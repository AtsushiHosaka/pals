"""Contract tests for the local Plus coupon readback and acceptance driver.

The real source inspector, readback function and acceptance flow run here. Only the
PostgreSQL, HTTP, Cognito and operator-CLI adapters are replaced by in-memory fakes, so
these tests never prove behaviour of a real database or server: that is what executing
``local-plus-coupon-acceptance.py`` against a real stack is for (see the recorded docs).
"""

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "local-qualification"))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


readiness = load(
    "plus_coupon_readback_contract", ROOT / "local-qualification/database_readiness.py"
)
acceptance = load(
    "plus_coupon_acceptance_contract", ROOT / "local-plus-coupon-acceptance.py"
)
prepare = load("plus_coupon_prepare_contract", ROOT / "local-qualification-prepare.py")
bootstrap = readiness.bootstrap_database
DSN = "postgresql://operator:fixture@127.0.0.1:55432/pals"
OWNER = readiness.COUPON_OWNER
HELPER = """SCHEMA = "pals_plus_coupons"

def canonical_sql():
    return b"fixture SQL"

def apply_local_storage(c):
    return False

def current(c):
    return c.state["current"]

def fingerprint(c):
    return c.state["fingerprint"]
"""


class FakeCoupons:
    """Answers the readback's catalog queries from one mutable state; records statements."""

    def __init__(self, state):
        self.state = state
        self.statements = []
        self.rows = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def cursor(self):
        return self

    def execute(self, statement, parameters=()):
        self.statements.append(statement)
        state = self.state
        rows = []
        if statement == readiness.FUNCTION_ACL_SQL:
            rows = state["function_acl"][parameters[0].split(".", 1)[1]]
        elif statement == readiness.TABLE_ACL_SQL:
            rows = state["table_acl"][parameters[0].split(".", 1)[1]]
        elif "obj_description" in statement:
            rows = [(state["comment"],)]
        elif "FROM pg_proc p JOIN pg_roles" in statement:
            signature = parameters[0].split(".", 1)[1]
            rows = (
                [state["functions"][signature]]
                if signature in state["functions"]
                else []
            )
        elif "pg_get_userbyid(c.relowner) FROM pg_class" in statement:
            rows = [(state["table_owner"][parameters[0].split(".", 1)[1]],)]
        elif "has_table_privilege" in statement:
            role, relation, privilege = parameters
            held = state["effective"][relation.split(".", 1)[1]][role]
            rows = [(privilege in held,)]
        self.rows = rows
        return self

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return list(self.rows)


def good_state():
    functions, function_acl = {}, {}
    for signature, definer, grantee in readiness.COUPON_FUNCTIONS:
        functions[signature] = (
            definer,
            OWNER,
            ["search_path=pg_catalog, pals_plus_coupons"] if definer else None,
            False,
            False,
            False,
            "md5-" + signature,
        )
        function_acl[signature] = [(OWNER, "EXECUTE")] + (
            [(grantee, "EXECUTE")] if grantee else []
        )
    table_acl, effective, owner = {}, {}, {}
    for table, readers in readiness.COUPON_TABLES:
        owner[table] = OWNER
        table_acl[table] = [
            (OWNER, privilege)
            for privilege in (
                "DELETE",
                "INSERT",
                "REFERENCES",
                "SELECT",
                "TRIGGER",
                "TRUNCATE",
                "UPDATE",
            )
        ] + [(role, "SELECT") for role in readers]
        effective[table] = {
            role: ["SELECT"] if role in readers else []
            for role in (readiness.COUPON_RUNTIME_ROLE, readiness.COUPON_OPERATOR_ROLE)
        }
    return {
        "current": True,
        "fingerprint": "a" * 64,
        "comment": "pals.plus-coupons.v1",
        "functions": functions,
        "function_acl": function_acl,
        "table_acl": table_acl,
        "table_owner": owner,
        "effective": effective,
    }


class SourceFixture(unittest.TestCase):
    """A tracked git source whose coupon files satisfy the real source inspector."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name).resolve() / "api"
        self.sql = b"-- isolated source fixture; never executed\n"
        self.patches = [
            patch.object(bootstrap, "COUPON_SQL_SHA256", sha256(self.sql).hexdigest()),
            patch.object(bootstrap, "COUPON_SCHEMA_SHA256", "a" * 64),
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)
        files = {
            bootstrap.COUPON_HELPER: HELPER.encode(),
            bootstrap.COUPON_SQL: self.sql,
            bootstrap.COUPON_MANIFEST: json.dumps(
                {
                    "schema_version": "pals.plus-coupons-migrations.v1",
                    "postgresql_major": 16,
                    "schema_sha256": "a" * 64,
                    "files": [
                        {
                            "path": bootstrap.COUPON_SQL,
                            "sha256": sha256(self.sql).hexdigest(),
                        }
                    ],
                }
            ).encode(),
        }
        for name, raw in files.items():
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        self.git("init", "-q")
        self.git("add", ".")
        self.git(
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-qm",
            "fixture",
        )
        self.revision = self.git("rev-parse", "HEAD")

    def git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.source), *args],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()


class ReadbackTests(SourceFixture):
    def read(self, state=None, url=DSN, revision=None):
        self.connection = FakeCoupons(state or good_state())
        return readiness.inspect_plus_coupons(
            url,
            self.source,
            revision or self.revision,
            connect=lambda _url: self.connection,
        )

    def refused(self, state, code, **kwargs):
        with self.assertRaises(ValueError) as caught:
            self.read(state, **kwargs)
        self.assertEqual(str(caught.exception), code)

    def test_observation_is_read_only_and_frozen_under_its_own_key(self):
        result = self.read()
        self.assertEqual(self.connection.statements[0], "SET TRANSACTION READ ONLY")
        write = re.compile(
            r"^\s*(INSERT|UPDATE|DELETE|GRANT|REVOKE|CREATE|ALTER|DROP)\b", re.I
        )
        self.assertFalse([s for s in self.connection.statements if write.match(s)])
        self.assertNotIn("schema_fingerprint_sha256", result)
        self.assertEqual(len(result["plus_coupons_schema_fingerprint_sha256"]), 64)
        self.assertEqual(result["api_source_revision"], self.revision)
        self.assertEqual(result["schema_sha256"], "a" * 64)
        self.assertEqual(
            (len(result["functions"]), len(result["tables"])),
            (len(readiness.COUPON_FUNCTIONS), len(readiness.COUPON_TABLES)),
        )
        self.assertEqual(result, self.read())

    def test_fingerprint_follows_every_observed_fact(self):
        base = self.read()["plus_coupons_schema_fingerprint_sha256"]
        state = good_state()
        signature = readiness.COUPON_FUNCTIONS[0][0]
        row = list(state["functions"][signature])
        row[6] = "another-body"
        state["functions"][signature] = tuple(row)
        self.assertNotEqual(
            self.read(state)["plus_coupons_schema_fingerprint_sha256"], base
        )

    def test_draft_contract_is_untouched(self):
        self.assertEqual(
            [signature for signature, *_ in readiness.FUNCTIONS],
            ["record_verification(text,text)", "capture_input(text)"],
        )
        source = Path(readiness.__file__).read_text()
        draft = source[
            source.index("def inspect(") : source.index("# The Plus coupon schema")
        ]
        self.assertNotIn("coupon", draft.lower())

    def test_source_and_identity_refusals(self):
        self.refused(
            good_state(),
            "closed_local_database_uri_required",
            url="postgresql://u:p@db.example:5432/pals",
        )
        self.refused(
            good_state(),
            "actual_local_plus_coupon_source_revision_changed",
            revision="0" * 40,
        )
        (self.source / bootstrap.COUPON_HELPER).write_text(HELPER + "# drift\n")
        self.refused(good_state(), "coupon_local_bootstrap_unsupported_api")

    def test_schema_state_refusals(self):
        for change, code in (
            ({"current": False}, "actual_local_plus_coupon_schema_not_current"),
            ({"fingerprint": "b" * 64}, "actual_local_plus_coupon_schema_changed"),
            ({"comment": "other"}, "actual_local_plus_coupon_schema_changed"),
        ):
            state = {**good_state(), **change}
            with self.subTest(code=code, change=sorted(change)):
                self.refused(state, code)

    def test_function_definer_owner_search_path_and_execute_refusals(self):
        signature = "redeem(text,text,uuid)"

        def mutate(index, value):
            state = good_state()
            row = list(state["functions"][signature])
            row[index] = value
            state["functions"][signature] = tuple(row)
            return state

        wrong_acl = good_state()
        wrong_acl["function_acl"][signature].append(("PUBLIC", "EXECUTE"))
        operator_acl = good_state()
        operator_acl["function_acl"][signature].append(
            (readiness.COUPON_OPERATOR_ROLE, "EXECUTE")
        )
        absent = good_state()
        del absent["functions"][signature]
        cases = {
            "invoker": mutate(0, False),
            "owner": mutate(1, "someone_else"),
            "search_path": mutate(2, ["search_path=public"]),
            "no_search_path": mutate(2, None),
            "login_owner": mutate(3, True),
            "superuser_owner": mutate(4, True),
            "bypass_rls_owner": mutate(5, True),
            "public_execute": wrong_acl,
            "operator_execute_redeem": operator_acl,
        }
        for name, state in cases.items():
            with self.subTest(name):
                self.refused(state, "actual_local_plus_coupon_function_acl_changed")
        self.refused(absent, "actual_local_plus_coupon_function_absent")

    def test_table_owner_acl_and_effective_privilege_refusals(self):
        public = good_state()
        public["table_acl"]["codes"].append(("PUBLIC", "SELECT"))
        runtime_write = good_state()
        runtime_write["effective"]["redemptions"][readiness.COUPON_RUNTIME_ROLE].append(
            "INSERT"
        )
        runtime_reads_codes = good_state()
        runtime_reads_codes["table_acl"]["codes"].append(
            (readiness.COUPON_RUNTIME_ROLE, "SELECT")
        )
        owner = good_state()
        owner["table_owner"]["codes"] = "postgres"
        for name, state in {
            "public": public,
            "runtime_write": runtime_write,
            "runtime_reads_codes": runtime_reads_codes,
            "owner": owner,
        }.items():
            with self.subTest(name):
                self.refused(state, "actual_local_plus_coupon_table_acl_changed")


class PrepareFreezeTests(unittest.TestCase):
    def subject(self):
        return {
            "database_contract": {
                "api_source_root": "/api",
                "api_source_revision": "r" * 40,
                "schema_fingerprint_sha256": "d" * 64,
            }
        }

    def observation(self, fingerprint="f" * 64, revision="r" * 40, schema="s" * 64):
        return {
            "api_source_revision": revision,
            "schema_sha256": schema,
            "plus_coupons_schema_fingerprint_sha256": fingerprint,
        }

    def plan(self):
        return {"api_source_revision": "r" * 40, "schema_sha256": "s" * 64}

    def test_default_profile_leaves_the_contract_byte_identical(self):
        subject = self.subject()
        before = json.dumps(subject, sort_keys=True)
        calls = []
        self.assertIsNone(
            prepare.freeze_plus_coupons(
                subject, Path("/e"), None, observe=lambda *a: calls.append(a)
            )
        )
        prepare.require_plus_coupons_unchanged(
            subject, Path("/e"), None, observe=lambda *a: calls.append(a)
        )
        self.assertEqual((json.dumps(subject, sort_keys=True), calls), (before, []))

    def test_opt_in_adds_only_the_independent_key_and_detects_drift(self):
        subject = self.subject()
        keys = set(subject["database_contract"])
        value = prepare.freeze_plus_coupons(
            subject, Path("/e"), self.plan(), observe=lambda *_: self.observation()
        )
        contract = subject["database_contract"]
        self.assertEqual(value, "f" * 64)
        self.assertEqual(
            set(contract) - keys, {"plus_coupons_schema_fingerprint_sha256"}
        )
        self.assertEqual(contract["schema_fingerprint_sha256"], "d" * 64)
        prepare.require_plus_coupons_unchanged(
            subject, Path("/e"), self.plan(), observe=lambda *_: self.observation()
        )
        with self.assertRaisesRegex(prepare.gate.Refusal, "differ_from_subject"):
            prepare.require_plus_coupons_unchanged(
                subject,
                Path("/e"),
                self.plan(),
                observe=lambda *_: self.observation("0" * 64),
            )

    def test_readback_must_match_the_bootstrap_plan(self):
        for observation in (
            self.observation(revision="x" * 40),
            self.observation(schema="x" * 64),
        ):
            subject = self.subject()
            with self.assertRaisesRegex(
                prepare.gate.Refusal, "differs_from_bootstrap_plan"
            ):
                prepare.freeze_plus_coupons(
                    subject, Path("/e"), self.plan(), observe=lambda *_: observation
                )
            self.assertNotIn(
                "plus_coupons_schema_fingerprint_sha256", subject["database_contract"]
            )

    def test_unavailable_readback_is_a_closed_refusal_without_content(self):
        def run(_args):
            return json.dumps({"state": "unavailable", "code": "actual_x"})

        with self.assertRaisesRegex(
            prepare.gate.Refusal, "actual_local_plus_coupon_readiness_failed:actual_x"
        ):
            prepare.observe_plus_coupons(self.subject(), Path("/e"), run_=run)

    def test_freeze_runs_after_the_api_is_started_and_again_after_the_freeze(self):
        source = Path(prepare.__file__).read_text()
        main = source[source.index("def main():") :]
        self.assertLess(
            main.index("freeze_plus_coupons(subject"),
            main.index("freeze_until_api_is_stable("),
        )
        self.assertLess(
            main.index("freeze_until_api_is_stable("),
            main.index("require_plus_coupons_unchanged(subject"),
        )


class PureTests(unittest.TestCase):
    def test_one_utc_calendar_month_matches_postgresql_interval_addition(self):
        zone = timezone(timedelta(hours=9))
        for start, expected in (
            ("2026-11-24T22:10:11.123456+09:00", "2026-12-24T13:10:11.123456+00:00"),
            ("2026-01-31T10:00:00+00:00", "2026-02-28T10:00:00+00:00"),
            ("2028-01-31T10:00:00+00:00", "2028-02-29T10:00:00+00:00"),
            ("2026-03-31T00:00:00+00:00", "2026-04-30T00:00:00+00:00"),
            ("2026-12-15T23:59:59.999999+00:00", "2027-01-15T23:59:59.999999+00:00"),
        ):
            with self.subTest(start=start):
                moment = datetime.fromisoformat(start)
                self.assertEqual(
                    acceptance.add_one_utc_month(moment).isoformat(), expected
                )
        # A zone shift near the month end moves the UTC day, not the wall time of the zone.
        moment = datetime(2026, 1, 31, 8, 0, tzinfo=zone)
        self.assertEqual(
            acceptance.add_one_utc_month(moment).isoformat(),
            "2026-02-28T23:00:00+00:00",
        )

    def test_only_explicit_loopback_http_origins_are_accepted(self):
        for value in ("http://127.0.0.1:8000", "http://localhost:9229/"):
            self.assertTrue(acceptance.loopback_origin(value, "refused"))
        for value in (
            "https://127.0.0.1:8000",
            "http://example.com:8000",
            "http://127.0.0.1",
            "http://user:pw@127.0.0.1:8000",
            "http://127.0.0.1:8000/v1",
            "http://127.0.0.1:8000?x=1",
            "http://0.0.0.0:8000",
        ):
            with self.subTest(value), self.assertRaises(acceptance.Failure):
                acceptance.loopback_origin(value, "refused")

    def test_issue_command_environment_and_output_hygiene(self):
        seen = {}

        def runner(args, **kwargs):
            seen.update(args=args, **kwargs)
            coupon = args[args.index("--coupon-id") + 1]
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps({"coupon_id": coupon, "code": "SECRET-1"}),
            )

        with patch.dict(
            "os.environ", {"AWS_SECRET_ACCESS_KEY": "ambient", "PATH": "/bin"}
        ):
            coupon, code = acceptance.issue_with_cli(
                "/usr/bin/python3",
                "/api",
                "postgresql://op:pw@127.0.0.1:55432/pals",
                runner=runner,
            )
        self.assertEqual(code, "SECRET-1")
        self.assertEqual(
            seen["args"][1:4],
            ["-m", "app.release.plus_coupon_admin", "issue-initial-campaign"],
        )
        self.assertEqual(seen["args"][seen["args"].index("--max-redemptions") + 1], "1")
        self.assertEqual(
            set(seen["env"]),
            {
                "PATH",
                "PYTHONDONTWRITEBYTECODE",
                "PALS_ENV",
                "PALS_PLUS_COUPONS_ENABLED",
                "PALS_BILLING_OPERATOR_DATABASE_URL",
            },
        )
        self.assertTrue(seen["capture_output"])

    def test_issue_failures_are_closed_and_never_echo_output(self):
        for result, code in (
            (
                SimpleNamespace(returncode=1, stdout='{"code":"LEAKED"}'),
                "acceptance_coupon_issue_failed",
            ),
            (
                SimpleNamespace(returncode=0, stdout="not json LEAKED"),
                "acceptance_coupon_issue_output_invalid",
            ),
            (
                SimpleNamespace(
                    returncode=0, stdout='{"coupon_id":"x","code":"LEAKED"}'
                ),
                "acceptance_coupon_issue_output_invalid",
            ),
            (
                SimpleNamespace(
                    returncode=0, stdout='{"coupon_id":"x","code":"LEAKED","extra":1}'
                ),
                "acceptance_coupon_issue_output_invalid",
            ),
        ):
            with (
                self.subTest(code=code),
                self.assertRaises(acceptance.Failure) as caught,
            ):
                acceptance.issue_with_cli(
                    "py",
                    "/api",
                    "postgresql://u:p@127.0.0.1:55432/pals",
                    runner=lambda *_a, **_k: result,
                )
            self.assertEqual(str(caught.exception), code)
            self.assertNotIn(
                "LEAKED", repr(caught.exception.__dict__) + str(caught.exception)
            )


class World:
    """An in-memory API, Cognito and coupon store with the contract the driver expects."""

    def __init__(self, *, refuse_second=True, project=True, drop_fails=False):
        self.refuse_second, self.project, self.drop_fails = (
            refuse_second,
            project,
            drop_fails,
        )
        self.users, self.tokens, self.redemptions, self.coupons = {}, {}, [], {}
        self.events = []
        self.next_code = 0

    # Cognito
    def call(self, operation, payload):
        self.events.append(operation)
        if operation == "AdminCreateUser":
            email = payload["Username"]
            self.users[email] = {"password": None, "id": "user-" + str(len(self.users))}
        elif operation == "AdminSetUserPassword":
            self.users[payload["Username"]]["password"] = payload["Password"]
        elif operation == "InitiateAuth":
            name = payload["AuthParameters"]["USERNAME"]
            assert self.users[name]["password"] == payload["AuthParameters"]["PASSWORD"]
            token = "TOKEN-" + name + str(len(self.tokens))
            self.tokens[token] = self.users[name]["id"]
            return {"AuthenticationResult": {"AccessToken": token}}
        elif operation == "AdminDeleteUser":
            del self.users[payload["Username"]]
        return {}

    # HTTP
    def request(self, method, url, body=None, headers=None):
        path = url.split(":8000", 1)[1] if ":8000" in url else url
        token = (headers or {}).get("Authorization", "")[7:]
        user = self.tokens.get(token)
        if path == "/health":
            return 200, {"status": "ok"}
        if user is None:
            return 401, {"error": {"code": "auth_token_invalid"}}
        if path == "/v1/auth/me":
            return 200, {"user_id": user}
        has = [r for r in self.redemptions if r["owner"] == user]
        if path == "/v1/billing/plus-coupons/status":
            return 200, {"enabled": True}
        if path == "/v1/billing/summary":
            return 200, {
                "billing_product_id": "plus" if has else "free",
                "billing_source": "complimentary" if has else "free",
                "entitlement_state": "active",
                "price": None,
                "period_end": has[0]["expires"].isoformat() if has else None,
            }
        if path == "/v1/projects":
            if has and self.project:
                return 201, {"id": "p"}
            return 403, {"error": {"code": "project_plan_required"}}
        assert path == "/v1/billing/plus-coupons/redeem"
        # The route refuses an account that already holds Plus before any code is consumed.
        if has and self.refuse_second:
            return 409, {"error": {"code": "plus_coupon_existing_entitlement"}}
        coupon = self.coupons.get(body["code"])
        if coupon is None or any(r["coupon"] == coupon for r in self.redemptions):
            return 422, {"error": {"code": "plus_coupon_invalid"}}
        start = datetime(2026, 11, 24, 13, 0, 0, 123456, tzinfo=timezone.utc)
        end = acceptance.add_one_utc_month(start)
        self.redemptions.append(
            {
                "owner": user,
                "coupon": coupon,
                "start": start,
                "expires": end,
                "grant": "g%d" % len(self.redemptions),
            }
        )
        return 200, {
            "billing_product_id": "plus",
            "billing_source": "complimentary",
            "grant_id": self.redemptions[-1]["grant"],
            "starts_at": start.isoformat(),
            "expires_at": end.isoformat(),
        }

    # coupons and SQL
    def issue(self, _python, _source, _operator_url):
        self.next_code += 1
        coupon, code = "coupon-%d" % self.next_code, "CODE-SECRET-%d" % self.next_code
        self.coupons[code] = coupon
        return coupon, code

    def rows(self, query, parameters=()):
        if "FROM pals_plus_coupons.codes" in query:
            return [(c, 1, None, 1) for c in parameters[0]]
        if "count(DISTINCT" in query:
            members = [r for r in self.redemptions if r["coupon"] in parameters[0]]
            return [
                (
                    len(members),
                    len({r["owner"] for r in members}),
                    len({r["coupon"] for r in members}),
                )
            ]
        if "GROUP BY 1" in query:
            names = sorted(
                {r["coupon"] for r in self.redemptions if r["coupon"] in parameters[0]}
            )
            return [(n, sum(r["coupon"] == n for r in self.redemptions)) for n in names]
        owned = [r for r in self.redemptions if r["owner"] == parameters[0]]
        if "count(*)" in query:
            return [(len(owned),)]
        if "SELECT grant_id::text FROM" in query:
            return [(r["grant"],) for r in owned]
        return [(r["grant"], r["coupon"], r["start"], r["expires"]) for r in owned]


class AcceptanceFlowTests(unittest.TestCase):
    ENVIRONMENT = {
        "PALS_ENV": "local",
        "PALS_PLUS_COUPONS_ENABLED": "true",
        "PALS_HOST_DATABASE_URL": DSN,
        "PALS_COGNITO_APP_CLIENT_ID": "client",
        "PALS_COGNITO_USER_POOL_ID": "pool",
    }

    def config(self, **changes):
        base = {
            "environment": dict(self.ENVIRONMENT),
            "api_source": Path("/api"),
            "api_python": "python",
            "api_base_url": "http://127.0.0.1:8000",
            "cognito_endpoint": "http://localhost:9229",
            "frozen_fingerprint": None,
            "project_access": True,
        }
        return {**base, **changes}

    def run_flow(self, world, config=None):
        dropped = []

        class Database:
            def __init__(self, url, connect=None):
                self.operator_role = None

            def create_operator(self):
                self.operator_role = "operator"
                return "postgresql://op:pw@127.0.0.1:55432/pals"

            def drop_operator(self):
                if world.drop_fails:
                    raise RuntimeError("secret detail")
                dropped.append(self.operator_role)
                self.operator_role = None

            rows = staticmethod(world.rows)

        observation = {
            "schema_sha256": "a" * 64,
            "functions": [1] * 6,
            "tables": [1] * 4,
            "plus_coupons_schema_fingerprint_sha256": "f" * 64,
        }
        with (
            patch.object(acceptance, "Database", Database),
            patch.object(
                acceptance.bootstrap,
                "coupon_source_contract",
                return_value={"api_source_revision": "r" * 40},
            ),
            patch.object(
                acceptance.readiness, "inspect_plus_coupons", return_value=observation
            ),
        ):
            result = acceptance.run(
                config or self.config(),
                http=world,
                issue=world.issue,
                cognito=world,
            )
        return result, dropped

    def test_full_flow_passes_and_prints_no_secret_value(self):
        world = World()
        result, dropped = self.run_flow(world)
        text = acceptance.gate.stable(result)
        self.assertEqual(result["state"], "local_plus_coupon_acceptance_passed")
        self.assertEqual(
            (
                result["coupons_issued"],
                result["redemptions_succeeded"],
                result["redemptions_refused"],
                result["failures"],
            ),
            (2, 2, 3, 0),
        )
        self.assertEqual(len(result["checks"]), 9)
        self.assertTrue(all(check["ok"] for check in result["checks"]))
        self.assertFalse(
            re.search(r"CODE-SECRET|TOKEN-|example\.test|password", text, re.I)
        )
        self.assertEqual((dropped, world.users), (["operator"], {}))
        self.assertEqual(len(world.redemptions), 2)

    def test_project_access_check_can_be_turned_off(self):
        world = World(project=False)
        result, _ = self.run_flow(world, self.config(project_access=False))
        self.assertIsNone(result["checks"][2]["project_create_status"])
        with self.assertRaisesRegex(acceptance.Failure, "project_not_allowed_after"):
            self.run_flow(World(project=False))

    def test_second_redemption_that_is_accepted_fails_and_still_cleans_up(self):
        world = World(refuse_second=False)
        with self.assertRaisesRegex(
            acceptance.Failure, "second_redemption_not_refused:second_coupon"
        ):
            self.run_flow(world)
        self.assertEqual(world.users, {})

    def test_cleanup_failure_is_named_without_the_cause(self):
        world = World(drop_fails=True)
        with self.assertRaises(acceptance.Failure) as caught:
            self.run_flow(world)
        self.assertEqual(
            str(caught.exception), "acceptance_cleanup_failed:operator_role"
        )
        self.assertNotIn("secret detail", str(caught.exception))

    def test_frozen_fingerprint_mismatch_stops_before_any_account_exists(self):
        world = World()
        with self.assertRaisesRegex(
            acceptance.Failure, "schema_differs_from_subject_freeze"
        ):
            self.run_flow(world, self.config(frozen_fingerprint="0" * 64))
        self.assertEqual(world.events, [])

    def test_environment_refusals_touch_nothing(self):
        world = World()
        for changes, code in (
            (
                {"environment": {**self.ENVIRONMENT, "PALS_ENV": "prod"}},
                "acceptance_local_coupon_environment_required",
            ),
            (
                {
                    "environment": {
                        **self.ENVIRONMENT,
                        "PALS_PLUS_COUPONS_ENABLED": "false",
                    }
                },
                "acceptance_local_coupon_environment_required",
            ),
            (
                {"api_base_url": "http://api.example.com:8000"},
                "acceptance_loopback_api_required",
            ),
            (
                {"cognito_endpoint": "https://cognito.example.com:443"},
                "acceptance_loopback_cognito_required",
            ),
        ):
            with (
                self.subTest(code=code),
                self.assertRaises(acceptance.Failure) as caught,
            ):
                self.run_flow(world, self.config(**changes))
            self.assertEqual(str(caught.exception), code)
        self.assertEqual(world.events, [])


if __name__ == "__main__":
    unittest.main()
