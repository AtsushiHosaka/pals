"""Unit tests with fakes, plus a real-PostgreSQL test of the privilege flow.

The real test runs only when PALS_LOADTEST_TEST_PG_PORT points at a throwaway PostgreSQL 16
server whose superuser is reachable as `postgres` (see _FIXTURE for what it creates) and
psycopg is importable. It copies the grant/revoke functions from the billing migration, so it
checks what matters: a NOINHERIT login can reach them only through SET ROLE, session_user is
the audit identity, and the temporary login is gone afterwards.
"""

import contextlib
import importlib.util
import io
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "loadtest-pro-grant.py"
spec = importlib.util.spec_from_file_location("loadtest_pro_grant", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

SUBS = [f"00000000-0000-4000-8000-{i:012d}" for i in range(1, 4)]
POOL_ID = "ap-northeast-1_TESTPOOL"


def manifest(state: Path, run_id="20261106T000000Z") -> None:
    state.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = state / "manifest.json"
    path.write_text(json.dumps({
        "run_id": run_id, "pool_name": "pals-mini-prod", "pool_id": POOL_ID,
        "accounts": [{"email": f"lt+{i + 1:02d}@example.com", "sub": sub, "password": "never-printed"}
                     for i, sub in enumerate(SUBS)]}))
    os.chmod(path, 0o600)


def fake_aws(master=("palsadmin", "master-secret-value"), enabled=True, instances=1):
    calls = []

    def run(command):
        calls.append(command)
        op = command[1]
        if op == "list-user-pools":
            return {"UserPools": [{"Id": POOL_ID, "Name": "pals-mini-prod"}]}
        if op == "describe-db-clusters":
            return {"DBClusters": [{"Endpoint": "db.example.internal", "Port": 5432, "DatabaseName": "pals",
                                    "MasterUserSecret": {"SecretArn": "arn:secret"}}]}
        if op == "describe-instances":
            return {"Reservations": [{"Instances": [{"InstanceId": f"i-{n}"} for n in range(instances)]}]}
        if op == "list-users":
            return {"Users": [{"Enabled": enabled}]}
        if op == "get-secret-value":
            return {"SecretString": json.dumps({"username": master[0], "password": master[1]})}
        raise AssertionError(command)
    run.calls = calls
    return run


@contextlib.contextmanager
def no_tunnel(info):
    yield


class FakeConn:
    """Records statements; answers the preflight and read-back queries."""

    def __init__(self, log, role_row=(False, False, False), admin=True, procs=True, stale=0, user="palsadmin"):
        self.log, self.user = log, user
        self.role_row, self.admin, self.procs, self.stale = role_row, admin, procs, stale
        self.last = None
        self.closed = False

    def execute(self, query, params=None):
        text = " ".join(str(query).split())
        self.log.append((self.user, text, params))
        low = text.lower()
        if "from pg_roles where rolname=%s" in low and "rolcanlogin" in low:
            self.last = self.role_row
        elif "from pg_proc" in low:
            self.last = (self.procs,)
        elif "admin_option" in low:
            self.last = (self.admin,)
        elif "like 'pals" in low:
            self.last = (self.stale,)
        elif "select count(*)" in low:
            self.last = (len(SUBS),)
        else:
            self.last = None
        return self

    def fetchone(self):
        return self.last

    @contextlib.contextmanager
    def transaction(self):
        self.log.append((self.user, "BEGIN", None))
        yield
        self.log.append((self.user, "COMMIT", None))

    def close(self):
        self.closed = True


class GrantTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state = Path(self.tmp.name) / "state"
        manifest(self.state)

    def run_main(self, argv, **injected):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = module.main(["--state-dir", str(self.state), *argv], **injected)
        return code, out.getvalue(), err.getvalue()

    def connect_factory(self, log, **kwargs):
        def connect(user, password, info):
            return FakeConn(log, user=user, **kwargs)
        return connect

    def execute_args(self, *extra):
        return ["grant", "--execute", "--confirm-pool", "pals-mini-prod", *extra]

    def test_dry_run_reads_metadata_only_and_changes_nothing(self):
        runner = fake_aws()
        log = []
        code, out, _ = self.run_main(["grant"], runner=runner, connect=self.connect_factory(log), tunnel=no_tunnel)
        self.assertEqual(code, 0)
        self.assertIn("DRY RUN", out)
        self.assertEqual(log, [])  # no database connection at all
        self.assertFalse(any(c[1] == "get-secret-value" for c in runner.calls))  # secret never read
        self.assertFalse((self.state / "grants.json").exists())

    def test_check_connects_and_runs_the_preflight_but_creates_nothing(self):
        log = []
        code, out, err = self.run_main(["check", "--execute", "--confirm-pool", "pals-mini-prod"],
                                       runner=fake_aws(), connect=self.connect_factory(log), tunnel=no_tunnel)
        self.assertEqual(code, 0, err)
        self.assertIn("connection check ok", out)
        self.assertTrue(log)
        self.assertFalse(any(s.startswith(("CREATE", "GRANT", "DROP")) for _, s, _ in log))
        self.assertFalse((self.state / "grants.json").exists())

    def test_check_without_execute_never_connects_or_reads_the_secret(self):
        runner, log = fake_aws(), []
        code, out, _ = self.run_main(["check"], runner=runner, connect=self.connect_factory(log), tunnel=no_tunnel)
        self.assertEqual(code, 0)
        self.assertEqual(log, [])
        self.assertFalse(any(c[1] == "get-secret-value" for c in runner.calls))

    def test_check_reports_a_failed_preflight(self):
        code, _, err = self.run_main(["check", "--execute", "--confirm-pool", "pals-mini-prod"], runner=fake_aws(),
                                     connect=self.connect_factory([], admin=False), tunnel=no_tunnel)
        self.assertEqual(code, 2)
        self.assertIn("ADMIN OPTION", err)

    def test_execute_requires_pool_confirmation(self):
        code, _, err = self.run_main(["grant", "--execute"], runner=fake_aws(), connect=self.connect_factory([]))
        self.assertEqual(code, 2)
        self.assertIn("--confirm-pool", err)

    def test_refuses_a_disabled_or_missing_cognito_user(self):
        log = []
        code, _, err = self.run_main(self.execute_args(), runner=fake_aws(enabled=False),
                                     connect=self.connect_factory(log), tunnel=no_tunnel)
        self.assertEqual(code, 2)
        self.assertIn("enabled Cognito user", err)
        self.assertEqual(log, [])

    def test_refuses_when_there_is_not_exactly_one_control_host(self):
        code, _, err = self.run_main(["grant"], runner=fake_aws(instances=2))
        self.assertEqual(code, 2)
        self.assertIn("exactly one running", err)

    def test_state_dir_must_be_private_and_outside_git(self):
        os.chmod(self.state / "manifest.json", 0o644)
        code, _, err = self.run_main(["grant"], runner=fake_aws())
        self.assertEqual(code, 2)
        self.assertIn("0600", err)

    def test_full_flow_creates_uses_and_drops_the_login_and_records_grants(self):
        log = []
        code, out, err = self.run_main(self.execute_args(), runner=fake_aws(),
                                       connect=self.connect_factory(log), tunnel=no_tunnel)
        self.assertEqual(code, 0, err)
        statements = [(u, s) for u, s, _ in log]
        creates = [s for u, s in statements if s.startswith("CREATE ROLE")]
        self.assertEqual(len(creates), 1)
        self.assertIn("NOINHERIT", creates[0])
        self.assertIn("VALID UNTIL", creates[0])
        login = creates[0].split('"')[1]
        self.assertTrue(login.startswith("pals_op_lt_"))
        grant_calls = [(u, s) for u, s in statements if "grant_complimentary_pro" in s]
        self.assertEqual(len(grant_calls), 3)
        self.assertTrue(all(u == login for u, _ in grant_calls))  # the audit identity is the temp login
        order = [s.split()[0] + " " + s.split()[1] for _, s in statements if s.startswith(("CREATE ROLE", "DROP ROLE"))]
        self.assertEqual(order, ["CREATE ROLE", "DROP ROLE"])
        self.assertIn("temporary operator login dropped", out)
        grants = json.loads((self.state / "grants.json").read_text())
        self.assertEqual(len(grants["grants"]), 3)
        self.assertEqual(stat.S_IMODE((self.state / "grants.json").stat().st_mode), 0o600)
        everything = out + err + json.dumps(log, default=str).replace("master-secret-value", "<SECRET>", 0)
        self.assertNotIn("master-secret-value", out + err)

    def test_secrets_are_never_printed(self):
        log = []
        _, out, err = self.run_main(self.execute_args(), runner=fake_aws(), connect=self.connect_factory(log),
                                    tunnel=no_tunnel)
        creates = [s for _, s, _ in log if s.startswith("CREATE ROLE")]
        password = creates[0].split("PASSWORD '")[1].split("'")[0]
        for secret in ("master-secret-value", password, "never-printed"):
            self.assertNotIn(secret, out + err)

    def test_preflight_failures_stop_before_creating_any_login(self):
        for kwargs, expected in (({"role_row": (True, False, False)}, "NOLOGIN"),
                                 ({"procs": False}, "does not exist"),
                                 ({"admin": False}, "ADMIN OPTION"),
                                 ({"stale": 1}, "previous temporary login")):
            log = []
            code, _, err = self.run_main(self.execute_args(), runner=fake_aws(),
                                         connect=self.connect_factory(log, **kwargs), tunnel=no_tunnel)
            self.assertEqual(code, 2, kwargs)
            self.assertIn(expected, err)
            self.assertFalse(any(s.startswith("CREATE ROLE") for _, s, _ in log), kwargs)
            (self.state / "grants.json").unlink(missing_ok=True)

    def test_a_failure_while_granting_still_drops_the_login(self):
        log = []

        class Boom(FakeConn):
            def execute(self, query, params=None):
                if "grant_complimentary_pro" in str(query):
                    raise RuntimeError("grant_overlap")
                return super().execute(query, params)

        def connect(user, password, info):
            return Boom(log, user=user)

        code, _, err = self.run_main(self.execute_args(), runner=fake_aws(), connect=connect, tunnel=no_tunnel)
        self.assertEqual(code, 3)
        self.assertIn("grant_overlap", err)
        self.assertNotIn("Traceback", err)
        self.assertTrue(any(s.startswith("DROP ROLE") for _, s, _ in log))

    def test_revoke_uses_the_recorded_grants_and_archives_the_record(self):
        log = []
        self.run_main(self.execute_args(), runner=fake_aws(), connect=self.connect_factory(log), tunnel=no_tunnel)
        log.clear()
        code, out, err = self.run_main(["revoke", "--execute", "--confirm-pool", "pals-mini-prod"],
                                       runner=fake_aws(), connect=self.connect_factory(log), tunnel=no_tunnel)
        self.assertEqual(code, 0, err)
        self.assertEqual(sum("revoke_complimentary_pro" in s for _, s, _ in log), 3)
        self.assertFalse((self.state / "grants.json").exists())
        self.assertTrue(any(p.name.startswith("grants.revoked-") for p in self.state.iterdir()))

    def test_grant_refuses_when_a_grants_record_already_exists(self):
        self.run_main(self.execute_args(), runner=fake_aws(), connect=self.connect_factory([]), tunnel=no_tunnel)
        code, _, err = self.run_main(self.execute_args(), runner=fake_aws(),
                                     connect=self.connect_factory([]), tunnel=no_tunnel)
        self.assertEqual(code, 2)
        self.assertIn("already exists", err)

    def test_identifier_and_literal_helpers_refuse_odd_input(self):
        self.assertEqual(module.ident("pals_op_lt_ab12"), '"pals_op_lt_ab12"')
        for bad in ('a"b', "a b", "x;drop", "1abc", ""):
            with self.assertRaises(module.Refusal):
                module.ident(bad)
        with self.assertRaises(module.Refusal):
            module.lit("it's")
        self.assertEqual(module.lit("abc_-123"), "'abc_-123'")


_FIXTURE = """
CREATE ROLE palsadmin LOGIN CREATEROLE CREATEDB PASSWORD 'masterpw';
GRANT pg_signal_backend TO palsadmin;
CREATE DATABASE pals OWNER palsadmin;
"""

_SCHEMA = """
SET ROLE palsadmin;
CREATE ROLE pals_billing_test_admin NOLOGIN NOINHERIT;
CREATE ROLE pals_api_billing_runtime NOLOGIN;
RESET ROLE;
CREATE SCHEMA pals_billing;
CREATE TABLE pals_billing.complimentary_pro_grants (
  grant_id UUID PRIMARY KEY, owner_user_id TEXT NOT NULL, cognito_pool_id TEXT NOT NULL,
  starts_at TIMESTAMPTZ NOT NULL, expires_at TIMESTAMPTZ NOT NULL, operator_identity TEXT NOT NULL,
  reason TEXT NOT NULL, CHECK (starts_at < expires_at));
CREATE TABLE pals_billing.complimentary_pro_revocations (
  grant_id UUID PRIMARY KEY REFERENCES pals_billing.complimentary_pro_grants(grant_id),
  revoked_at TIMESTAMPTZ NOT NULL, operator_identity TEXT NOT NULL, reason TEXT NOT NULL);
"""


def migration_functions() -> str:
    """The exact function bodies and grants from the billing migration, when the API source is at hand."""
    here = Path(__file__).resolve()
    candidates = [Path(os.environ.get("PALS_API_MIGRATION", "")),
                  here.parents[2] / "pals-api/app/db/migrations/billing/004_complimentary_pro.sql"]
    for path in candidates:
        if path.is_file():
            text = path.read_text()
            start = text.index("CREATE FUNCTION pals_billing.grant_complimentary_pro")
            end = text.index("COMMENT ON SCHEMA")
            return text[start:end]
    raise unittest.SkipTest("billing migration 004_complimentary_pro.sql not found (set PALS_API_MIGRATION)")


@unittest.skipUnless(os.environ.get("PALS_LOADTEST_TEST_PG_PORT"), "needs a throwaway PostgreSQL 16 server")
class RealPostgresTest(unittest.TestCase):
    """Runs the script's real SQL against PostgreSQL with the migration's functions."""

    def setUp(self):
        import psycopg

        self.psycopg = psycopg
        self.port = int(os.environ["PALS_LOADTEST_TEST_PG_PORT"])
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state = Path(self.tmp.name) / "state"
        manifest(self.state)
        su = psycopg.connect(host="127.0.0.1", port=self.port, dbname="postgres", user="postgres", autocommit=True)
        self.addCleanup(su.close)
        with contextlib.suppress(Exception):
            su.execute("DROP DATABASE IF EXISTS pals WITH (FORCE)")
        for role in ("probe", "pals_billing_test_admin", "pals_api_billing_runtime", "palsadmin"):
            su.execute(f"DROP ROLE IF EXISTS {role}")
        for (left,) in su.execute("SELECT rolname FROM pg_roles WHERE rolname LIKE 'pals\\_op\\_lt\\_%'").fetchall():
            su.execute(f'DROP ROLE "{left}"')
        for statement in _FIXTURE.strip().split(";\n"):
            if statement.strip():
                su.execute(statement)
        admin = psycopg.connect(host="127.0.0.1", port=self.port, dbname="pals", user="postgres", autocommit=True)
        self.addCleanup(admin.close)
        admin.execute("GRANT ALL ON SCHEMA public TO palsadmin")
        for statement in _SCHEMA.strip().split(";\n"):
            if statement.strip():
                admin.execute(statement)
        admin.execute(migration_functions().replace("RESET ROLE;", ""))
        self.admin = admin

    def connect(self, user, password, info):
        return self.psycopg.connect(host="127.0.0.1", port=self.port, dbname="pals", user=user,
                                    password=password, autocommit=True)

    def run_main(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = module.main(["--state-dir", str(self.state), *argv], runner=fake_aws(master=("palsadmin", "masterpw")),
                               connect=self.connect, tunnel=no_tunnel)
        return code, out.getvalue(), err.getvalue()

    def logins(self):
        return self.admin.execute("SELECT rolname FROM pg_roles WHERE rolname LIKE 'pals\\_op\\_lt\\_%'").fetchall()

    def test_grant_then_revoke_against_real_postgres(self):
        code, out, err = self.run_main(["grant", "--execute", "--confirm-pool", "pals-mini-prod"])
        self.assertEqual(code, 0, err + out)
        self.assertEqual(self.logins(), [])  # temporary login dropped
        rows = self.admin.execute(
            "SELECT owner_user_id, cognito_pool_id, operator_identity FROM pals_billing.complimentary_pro_grants "
            "ORDER BY owner_user_id").fetchall()
        self.assertEqual([r[0] for r in rows], SUBS)
        self.assertTrue(all(r[1] == POOL_ID for r in rows))
        self.assertTrue(all(r[2].startswith("pals_op_lt_") for r in rows))  # session_user, never the master
        code, out, err = self.run_main(["revoke", "--execute", "--confirm-pool", "pals-mini-prod"])
        self.assertEqual(code, 0, err + out)
        revoked = self.admin.execute("SELECT count(*) FROM pals_billing.complimentary_pro_revocations").fetchone()
        self.assertEqual(revoked, (3,))
        self.assertEqual(self.logins(), [])

    def test_the_login_needs_set_role_and_cannot_call_the_function_directly(self):
        self.admin.execute("CREATE ROLE probe LOGIN NOINHERIT PASSWORD 'probepw'")
        self.admin.execute("GRANT pals_billing_test_admin TO probe WITH INHERIT FALSE, SET TRUE")
        self.admin.execute("GRANT CONNECT ON DATABASE pals TO probe")
        probe = self.psycopg.connect(host="127.0.0.1", port=self.port, dbname="pals", user="probe",
                                     password="probepw", autocommit=True)
        with self.assertRaises(self.psycopg.errors.InsufficientPrivilege):
            probe.execute("SELECT pals_billing.grant_complimentary_pro(gen_random_uuid(),'x','p',now()+interval '1 h','r')")
        probe.close()

    def test_an_existing_active_grant_makes_the_run_fail_and_still_drops_the_login(self):
        self.run_main(["grant", "--execute", "--confirm-pool", "pals-mini-prod"])
        (self.state / "grants.json").unlink()
        code, _, err = self.run_main(["grant", "--execute", "--confirm-pool", "pals-mini-prod"])
        self.assertEqual(code, 3)
        self.assertIn("grant_overlap", err)
        self.assertEqual(self.logins(), [])


if __name__ == "__main__":
    unittest.main()
