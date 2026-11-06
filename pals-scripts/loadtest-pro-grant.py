#!/usr/bin/env python3
"""Grant (and later revoke) complimentary Pro to the load-test accounts in production.

The operator role pals_billing_test_admin is NOLOGIN, so this opens an SSM port-forward to the
private Aurora through the control host, reads the RDS master secret in memory, creates a
short-lived operator login (10 minutes), runs pals_billing.grant_complimentary_pro for each
account recorded by loadtest-accounts.py, and drops the login again. It never prints the
master secret or any password, and nothing goes on a command line except the tunnel target.

Every subcommand is a dry run unless --execute is given with --confirm-pool. `check --execute`
opens the tunnel, connects as the master user and runs only read-only checks; use it first.
Needs: the AWS CLI + SSO credentials for the PALS account, the Session Manager plugin
(brew install --cask session-manager-plugin) and psycopg. Use the pals-api virtualenv:
  <repo>/pals-api/.venv/bin/python pals-scripts/loadtest-pro-grant.py check --execute --confirm-pool pals-mini-prod
  <repo>/pals-api/.venv/bin/python pals-scripts/loadtest-pro-grant.py grant
  <repo>/pals-api/.venv/bin/python pals-scripts/loadtest-pro-grant.py grant --execute --confirm-pool pals-mini-prod
  <repo>/pals-api/.venv/bin/python pals-scripts/loadtest-pro-grant.py revoke --execute --confirm-pool pals-mini-prod
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import secrets
import shutil
import socket
import ssl
import stat
import subprocess
import sys
import time
import urllib.request
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Iterator

Runner = Callable[[list[str]], Any]
Connect = Callable[..., Any]

ROLE = "pals_billing_test_admin"
CONTROL_NAME = "pals-prod-private-control"
CLUSTER = "pals-prod-aurora"
POOL_NAME = "pals-mini-prod"
CA_URL = "https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem"
LOGIN_MINUTES = 10
MAX_HOURS = 168


class Refusal(RuntimeError):
    """Unsafe or inconsistent; stop before changing anything (or after cleaning up)."""


_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,62}$")
_LITERAL = re.compile(r"^[A-Za-z0-9_:+. -]{1,128}$")


def ident(name: str) -> str:
    """A plain SQL identifier; anything unusual is refused rather than quoted."""
    if not _IDENT.match(name):
        raise Refusal("unexpected characters in a SQL identifier")
    return f'"{name}"'


def lit(value: str) -> str:
    """A string literal for values this script generates itself (token, timestamp)."""
    if not _LITERAL.match(value):
        raise Refusal("unexpected characters in a SQL literal")
    return f"'{value}'"


def inside_git_checkout(path: Path) -> bool:
    path = path.expanduser().resolve()
    return any((parent / ".git").exists() for parent in (path, *path.parents))


class Tool:
    def __init__(self, args: argparse.Namespace, runner: Runner | None = None,
                 connect: Connect | None = None, tunnel: Callable[..., Any] | None = None) -> None:
        self.args = args
        self.runner = runner or self._aws
        self._connect = connect
        self._tunnel = tunnel or self._open_tunnel
        self.state_dir = Path(args.state_dir).expanduser()
        self.manifest_path = self.state_dir / "manifest.json"
        self.grants_path = self.state_dir / "grants.json"

    # ---- aws ---------------------------------------------------------------
    def _aws(self, command: list[str]) -> Any:
        argv = ["aws", "--profile", self.args.profile, "--region", self.args.region,
                *command, "--output", "json"]
        done = subprocess.run(argv, capture_output=True, text=True, check=False)
        if done.returncode != 0:
            raise Refusal(f"aws {' '.join(command[:2])} failed: {done.stderr.strip()[:300]}")
        return json.loads(done.stdout) if done.stdout.strip() else {}

    # ---- state files -------------------------------------------------------
    def read_private(self, path: Path) -> dict[str, Any]:
        if not path.is_file():
            raise Refusal(f"missing {path}")
        if stat.S_IMODE(path.stat().st_mode) & 0o077:
            raise Refusal(f"{path} must be private (0600)")
        return json.loads(path.read_text())

    def write_private(self, path: Path, value: dict[str, Any]) -> None:
        self.state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        temp = path.with_suffix(".tmp")
        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as stream:
            json.dump(value, stream, indent=2)
        os.replace(temp, path)

    # ---- read-only discovery ----------------------------------------------
    def discover(self) -> dict[str, Any]:
        manifest = self.read_private(self.manifest_path)
        pools = self.runner(["cognito-idp", "list-user-pools", "--max-results", "60"])["UserPools"]
        pool = [p for p in pools if p["Name"] == self.args.pool_name]
        if len(pool) != 1 or pool[0]["Id"] != manifest["pool_id"]:
            raise Refusal("the manifest does not belong to the current Cognito pool")
        cluster = self.runner(["rds", "describe-db-clusters", "--db-cluster-identifier", self.args.cluster]
                              )["DBClusters"][0]
        secret = (cluster.get("MasterUserSecret") or {}).get("SecretArn")
        if not secret or not cluster.get("Endpoint") or not cluster.get("DatabaseName"):
            raise Refusal("the Aurora cluster does not expose an endpoint, database and master secret")
        hosts = self.runner(["ec2", "describe-instances", "--filters", f"Name=tag:Name,Values={CONTROL_NAME}",
                             "Name=instance-state-name,Values=running"])
        instances = [i["InstanceId"] for r in hosts["Reservations"] for i in r["Instances"]]
        if len(instances) != 1:
            raise Refusal(f"expected exactly one running {CONTROL_NAME}, found {len(instances)}")
        return {"manifest": manifest, "pool_id": pool[0]["Id"], "endpoint": cluster["Endpoint"],
                "port": cluster.get("Port", 5432), "database": cluster["DatabaseName"],
                "secret": secret, "control": instances[0]}

    def check_subjects(self, info: dict[str, Any]) -> None:
        for account in info["manifest"]["accounts"]:
            found = self.runner(["cognito-idp", "list-users", "--user-pool-id", info["pool_id"],
                                 "--filter", f'sub = "{account["sub"]}"'])["Users"]
            if len(found) != 1 or found[0].get("Enabled") is not True:
                raise Refusal(f"{account['email']} is not a single enabled Cognito user")

    # ---- tunnel + database -------------------------------------------------
    def _open_tunnel(self, info: dict[str, Any]) -> contextlib.AbstractContextManager[None]:
        @contextlib.contextmanager
        def tunnel() -> Iterator[None]:
            port = self.args.local_port
            with socket.socket() as probe:
                if probe.connect_ex(("127.0.0.1", port)) == 0:
                    raise Refusal(f"local port {port} is already in use; pass --local-port")
            parameters = json.dumps({"host": [info["endpoint"]], "portNumber": [str(info["port"])],
                                     "localPortNumber": [str(port)]})
            process = subprocess.Popen(
                ["aws", "--profile", self.args.profile, "--region", self.args.region, "ssm", "start-session",
                 "--target", info["control"], "--document-name", "AWS-StartPortForwardingSessionToRemoteHost",
                 "--parameters", parameters], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            try:
                deadline = time.monotonic() + 45
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        raise Refusal("the SSM port-forward ended: " + (process.stderr.read() or "")[-300:])
                    with socket.socket() as probe:
                        if probe.connect_ex(("127.0.0.1", port)) == 0:
                            break
                    time.sleep(0.5)
                else:
                    raise Refusal("the SSM port-forward did not open in time")
                yield
            finally:
                process.terminate()
                with contextlib.suppress(Exception):
                    process.wait(timeout=10)
        return tunnel()

    def ca_bundle(self) -> Path:
        path = self.state_dir / "rds-global-bundle.pem"
        if not path.exists():
            self.state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
            with urllib.request.urlopen(CA_URL, timeout=30, context=ssl.create_default_context()) as response:
                body = response.read(3_000_000)
            if body.count(b"BEGIN CERTIFICATE") < 3 or len(body) >= 3_000_000:
                raise Refusal("the downloaded RDS CA bundle looks wrong")
            path.write_bytes(body)
        return path

    def connect(self, info: dict[str, Any], user: str, password: str, bundle: Path) -> Any:
        if self._connect is not None:
            return self._connect(user=user, password=password, info=info)
        try:
            import psycopg
        except ImportError:
            raise Refusal("psycopg is missing; run with <repo>/pals-api/.venv/bin/python") from None
        # The hostname is 127.0.0.1 because of the tunnel, so verify the chain (verify-ca).
        return psycopg.connect(host="127.0.0.1", port=self.args.local_port, dbname=info["database"],
                               user=user, password=password, sslmode="verify-ca",
                               sslrootcert=str(bundle), connect_timeout=15, autocommit=True)

    def master_credentials(self, info: dict[str, Any]) -> tuple[str, str]:
        raw = self.runner(["secretsmanager", "get-secret-value", "--secret-id", info["secret"]])
        value = json.loads(raw["SecretString"])
        return value["username"], value["password"]

    # ---- guards ------------------------------------------------------------
    def guard(self) -> None:
        if inside_git_checkout(self.state_dir):
            raise Refusal("--state-dir must be outside any git checkout")
        if self.args.execute and self.args.confirm_pool != self.args.pool_name:
            raise Refusal(f"--execute also needs --confirm-pool {self.args.pool_name}")
        if not 1 <= self.args.hours <= MAX_HOURS:
            raise Refusal(f"--hours must be between 1 and {MAX_HOURS}")

    def prerequisites(self) -> None:
        if self._connect is None and shutil.which("session-manager-plugin") is None:
            raise Refusal("session-manager-plugin is missing: brew install --cask session-manager-plugin")
        if self._connect is None:
            try:
                import psycopg  # noqa: F401
            except ImportError:
                raise Refusal("psycopg is missing; run with <repo>/pals-api/.venv/bin/python") from None

    # ---- subcommands -------------------------------------------------------
    def check(self) -> int:
        """Tunnel + TLS + master login + the read-only preflight; creates nothing."""
        info = self.discover()
        self.check_subjects(info)
        print(f"discovery ok: database {info['database']}, one control host, "
              f"{len(info['manifest']['accounts'])} enabled Cognito users")
        if not self.args.execute:
            print("DRY RUN: no tunnel or login. Add --execute --confirm-pool %s for the connection check."
                  % self.args.pool_name)
            return 0
        self.prerequisites()
        bundle = self.ca_bundle() if self._connect is None else Path("unused")
        with self._tunnel(info):
            user, password = self.master_credentials(info)
            master = self.connect(info, user, password, bundle)
            del password
            try:
                self.preflight(master, info)
            finally:
                master.close()
        print("connection check ok: tunnel, TLS, master login and the billing preflight all pass")
        return 0

    def grant(self) -> int:
        info = self.discover()
        self.check_subjects(info)
        accounts = info["manifest"]["accounts"]
        hours = self.args.hours
        print(f"pool {self.args.pool_name}; database {info['database']} via the control host; "
              f"{len(accounts)} accounts; Pro until now+{hours}h")
        print("a temporary operator login (10 minutes) is created, used, and dropped")
        if self.grants_path.exists():
            raise Refusal(f"{self.grants_path} already exists; revoke or move it first")
        if not self.args.execute:
            print("DRY RUN: nothing changed. Add --execute --confirm-pool %s to grant." % self.args.pool_name)
            return 0
        self.prerequisites()
        expires = datetime.now(UTC) + timedelta(hours=hours)
        run_id = info["manifest"]["run_id"]
        reason = f"load test {run_id}"
        grants = {"run_id": run_id, "pool_id": info["pool_id"], "expires_at": expires.isoformat(),
                  "reason": reason, "grants": []}
        bundle = self.ca_bundle() if self._connect is None else Path("unused")
        with self._tunnel(info):
            self.with_operator(info, bundle, lambda conn: self._do_grants(conn, info, accounts, expires, reason, grants))
        print(f"done: {len(grants['grants'])} grants recorded in {self.grants_path}")
        return 0

    def _do_grants(self, conn: Any, info: dict[str, Any], accounts: list[dict[str, Any]],
                   expires: datetime, reason: str, grants: dict[str, Any]) -> None:
        for account in accounts:
            grant_id = str(uuid.uuid4())
            with conn.transaction():
                conn.execute(f"SET LOCAL ROLE {ident(ROLE)}")
                conn.execute("SELECT pals_billing.grant_complimentary_pro(%s::uuid,%s,%s,%s::timestamptz,%s)",
                             (grant_id, account["sub"], info["pool_id"], expires, reason))
            grants["grants"].append({"email": account["email"], "sub": account["sub"], "grant_id": grant_id})
            self.write_private(self.grants_path, grants)  # record before the next one
            print(f"granted {account['email']}")
        ids = [g["grant_id"] for g in grants["grants"]]
        with conn.transaction():
            conn.execute(f"SET LOCAL ROLE {ident(ROLE)}")
            active = conn.execute(
                "SELECT count(*) FROM pals_billing.complimentary_pro_grants g WHERE g.grant_id = ANY(%s::uuid[]) "
                "AND g.expires_at > clock_timestamp() AND NOT EXISTS (SELECT 1 FROM "
                "pals_billing.complimentary_pro_revocations r WHERE r.grant_id=g.grant_id)", (ids,)).fetchone()[0]
        if active != len(ids):
            raise Refusal(f"read-back shows {active} active grants for {len(ids)} recorded")
        print(f"read-back: {active} active grants")

    def revoke(self) -> int:
        info = self.discover()
        grants = self.read_private(self.grants_path)
        print(f"will revoke {len(grants['grants'])} grants recorded in {self.grants_path}")
        if not self.args.execute:
            print("DRY RUN: nothing changed. Add --execute --confirm-pool %s to revoke." % self.args.pool_name)
            return 0
        self.prerequisites()
        bundle = self.ca_bundle() if self._connect is None else Path("unused")

        def work(conn: Any) -> None:
            for item in grants["grants"]:
                with conn.transaction():
                    conn.execute(f"SET LOCAL ROLE {ident(ROLE)}")
                    conn.execute("SELECT pals_billing.revoke_complimentary_pro(%s::uuid,%s)",
                                 (item["grant_id"], f"load test finished {grants['run_id']}"))
                print(f"revoked {item['email']}")
        with self._tunnel(info):
            self.with_operator(info, bundle, work)
        self.grants_path.rename(self.grants_path.with_name(f"grants.revoked-{grants['run_id']}.json"))
        return 0

    # ---- temporary operator login -----------------------------------------
    def with_operator(self, info: dict[str, Any], bundle: Path, work: Callable[[Any], None]) -> None:
        master_user, master_password = self.master_credentials(info)
        login = f"pals_op_lt_{secrets.token_hex(6)}"
        password = secrets.token_urlsafe(32)
        master = self.connect(info, master_user, master_password, bundle)
        del master_password
        database = info["database"]
        created = False
        try:
            self.preflight(master, info)
            until = (datetime.now(UTC) + timedelta(minutes=LOGIN_MINUTES)).strftime("%Y-%m-%d %H:%M:%S+00")
            master.execute(
                f"CREATE ROLE {ident(login)} LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE "
                f"NOREPLICATION NOBYPASSRLS PASSWORD {lit(password)} VALID UNTIL {lit(until)}")
            created = True
            master.execute(f"GRANT {ident(ROLE)} TO {ident(login)} WITH INHERIT FALSE, SET TRUE")
            master.execute(f"GRANT CONNECT ON DATABASE {ident(database)} TO {ident(login)}")
            operator = self.connect(info, login, password, bundle)
            try:
                work(operator)
            finally:
                operator.close()
        finally:
            if created:
                with contextlib.suppress(Exception):  # best effort: the operator session is already closed
                    master.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE usename=%s",
                                   (login,))
                try:
                    master.execute(f"REVOKE CONNECT ON DATABASE {ident(database)} FROM {ident(login)}")
                    master.execute(f"REVOKE {ident(ROLE)} FROM {ident(login)}")
                    master.execute(f"DROP ROLE {ident(login)}")
                    print("temporary operator login dropped")
                except Exception:  # noqa: BLE001 - never echo a database error that might hold a secret
                    print(f"WARNING: could not drop the temporary login {login}; drop it by hand "
                          "(it expires in 10 minutes and its password was never shown)", file=sys.stderr)
            master.close()

    def preflight(self, master: Any, info: dict[str, Any]) -> None:
        cur = master.execute(
            "SELECT rolcanlogin, rolinherit, rolsuper FROM pg_roles WHERE rolname=%s", (ROLE,))
        row = cur.fetchone()
        if row != (False, False, False):
            raise Refusal(f"role {ROLE} is missing or differs from the expected NOLOGIN NOINHERIT NOSUPERUSER")
        # Read pg_proc directly: the master user has no USAGE on the pals_billing schema, so a
        # schema-qualified lookup (to_regprocedure) would fail with a permission error.
        for name, arguments in (("grant_complimentary_pro", 5), ("revoke_complimentary_pro", 2)):
            found = master.execute(
                "SELECT EXISTS (SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace "
                "WHERE n.nspname='pals_billing' AND p.proname=%s AND p.pronargs=%s AND p.prosecdef)",
                (name, arguments)).fetchone()
            if found != (True,):
                raise Refusal(f"pals_billing.{name} does not exist in this database; billing migration missing?")
        self.prove_grant_works(master)
        stale = master.execute("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'pals\\_op\\_lt\\_%'").fetchone()
        if stale and stale[0]:
            raise Refusal("a previous temporary login still exists; drop it first")


    def prove_grant_works(self, master: Any) -> None:
        """Do the real create-and-grant inside a transaction, then roll it back.

        Reading pg_auth_members would only guess whether the master may grant the role; this asks
        the server itself and leaves nothing behind (role creation and GRANT are transactional).
        """
        probe = f"pals_op_lt_probe_{secrets.token_hex(4)}"
        try:
            with master.transaction():
                master.execute(f"CREATE ROLE {ident(probe)} NOLOGIN")
                master.execute(f"GRANT {ident(ROLE)} TO {ident(probe)} WITH INHERIT FALSE, SET TRUE")
                raise _RollBack
        except _RollBack:
            return
        except Exception as error:  # noqa: BLE001
            first = (str(error).splitlines() or [""])[0][:160]
            raise Refusal(f"the master user cannot create a login and grant {ROLE} ({first}). "
                          f"{self.describe_membership(master)}") from None

    def describe_membership(self, master: Any) -> str:
        """Role names and flags only (no secrets): who can administer the operator role."""
        try:
            who = master.execute(
                "SELECT current_user, rolcreaterole, rolsuper, EXISTS (SELECT 1 FROM pg_roles g WHERE "
                "g.rolname='rds_superuser' AND pg_has_role(current_user, g.oid, 'MEMBER')) "
                "FROM pg_roles WHERE rolname=current_user"
            ).fetchone()
            rows = master.execute(
                "SELECT pg_get_userbyid(m.member), pg_get_userbyid(m.grantor), m.admin_option, "
                "m.inherit_option, m.set_option FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.roleid "
                "WHERE r.rolname=%s ORDER BY 1", (ROLE,)).fetchall()
        except Exception:  # noqa: BLE001
            return "membership could not be read"
        edges = "; ".join(f"{m}<-{g} admin={a} inherit={i} set={t}" for m, g, a, i, t in rows) or "none"
        return (f"connected as {who[0]} (createrole={who[1]}, superuser={who[2]}, rds_superuser={who[3]}); "
                f"edges on {ROLE}: {edges}")


class _RollBack(Exception):
    """Raised on purpose to roll the probe transaction back."""


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("command", choices=["check", "grant", "revoke"])
    p.add_argument("--profile", default=os.environ.get("AWS_PROFILE", "pals-prod-member"))
    p.add_argument("--region", default="ap-northeast-1")
    p.add_argument("--pool-name", default=POOL_NAME)
    p.add_argument("--cluster", default=CLUSTER)
    p.add_argument("--hours", type=int, default=72)
    p.add_argument("--local-port", type=int, default=15432)
    p.add_argument("--state-dir", default="~/.pals-loadtest")
    p.add_argument("--execute", action="store_true")
    p.add_argument("--confirm-pool")
    return p


def main(argv: list[str] | None = None, **injected: Any) -> int:
    args = parser().parse_args(argv)
    tool = Tool(args, **injected)
    try:
        tool.guard()
        return {"check": tool.check, "grant": tool.grant, "revoke": tool.revoke}[args.command]()
    except Refusal as refusal:
        print(f"REFUSED: {refusal}", file=sys.stderr)
        return 2
    except Exception as error:  # noqa: BLE001 - cleanup already ran in with_operator's finally
        first = (str(error).splitlines() or [""])[0][:200]
        print(f"FAILED ({type(error).__name__}): {first}", file=sys.stderr)
        if tool.grants_path.exists():
            print(f"some grants were recorded in {tool.grants_path}; run revoke to undo them", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
