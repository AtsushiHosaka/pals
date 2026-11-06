#!/usr/bin/env python3
"""Create, check and delete throwaway Cognito accounts for the 10-user load test.

Every subcommand is a dry run unless --execute is given, and --execute also needs
--confirm-pool <pool name>. Nothing here touches the database: the free Pro grants for
the new accounts are only written out as commands for the operator to run.

Passwords and subject ids live in a 0600 manifest under --state-dir (default
~/.pals-loadtest), never in the repository. Passwords are never printed and are passed
to the AWS CLI through a 0600 temporary file, not on the command line.

Usage (run from anywhere; needs the AWS CLI and credentials for the PALS account):
  python3 pals-scripts/loadtest-accounts.py create --email name@gmail.com
  python3 pals-scripts/loadtest-accounts.py create --email name@gmail.com --execute --confirm-pool pals-mini-prod
  python3 pals-scripts/loadtest-accounts.py verify --execute --confirm-pool pals-mini-prod
  python3 pals-scripts/loadtest-accounts.py delete --execute --confirm-pool pals-mini-prod
"""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import stat
import subprocess
import sys
import tempfile
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Callable

Runner = Callable[[list[str], dict[str, Any] | None], Any]

DEFAULT_POOL = "pals-mini-prod"
DEFAULT_CLIENT = "pals-mini-web"
DEFAULT_REGION = "ap-northeast-1"
SYMBOLS = "!#%*+-=?@_"
EMAIL = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
MAX_COUNT = 30


class Refusal(RuntimeError):
    """The request is unsafe or does not match the live pool; nothing was changed."""


def make_password(minimum: int = 14) -> str:
    """A random password with every character class, longer than the pool minimum."""
    length = max(24, minimum + 8)
    pools = ["abcdefghijklmnopqrstuvwxyz", "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "0123456789", SYMBOLS]
    chars = [secrets.choice(pool) for pool in pools]
    allowed = "".join(pools)
    chars += [secrets.choice(allowed) for _ in range(length - len(chars))]
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


def inside_git_checkout(path: Path) -> bool:
    path = path.expanduser().resolve()
    return any((parent / ".git").exists() for parent in (path, *path.parents))


class Tool:
    def __init__(self, args: argparse.Namespace, runner: Runner | None = None) -> None:
        self.args = args
        self.runner = runner or self._aws
        self.state_dir = Path(args.state_dir).expanduser()
        self.manifest_path = self.state_dir / "manifest.json"

    def _aws(self, command: list[str], payload: dict[str, Any] | None) -> Any:
        base = ["aws", "--profile", self.args.profile, "--region", self.args.region]
        argv = [*base, *command, "--output", "json"]
        temp: Path | None = None
        try:
            if payload is not None:
                # Secrets go through a private file so they never appear in `ps`.
                self.state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
                handle, name = tempfile.mkstemp(dir=self.state_dir, prefix=".payload-", suffix=".json")
                temp = Path(name)
                with os.fdopen(handle, "w") as stream:
                    json.dump(payload, stream)
                argv += ["--cli-input-json", f"file://{temp}"]
            done = subprocess.run(argv, capture_output=True, text=True, check=False)
        finally:
            if temp is not None:
                temp.unlink(missing_ok=True)
        if done.returncode != 0:
            # The CLI error text never contains the payload, but trim it anyway.
            raise Refusal(f"aws {' '.join(command[:2])} failed: {done.stderr.strip()[:300]}")
        return json.loads(done.stdout) if done.stdout.strip() else {}

    # ---- read-only lookups -------------------------------------------------
    def pool(self) -> dict[str, Any]:
        pools = self.runner(["cognito-idp", "list-user-pools", "--max-results", "60"], None)
        found = [p for p in pools.get("UserPools", []) if p.get("Name") == self.args.pool_name]
        if len(found) != 1:
            raise Refusal(f"expected exactly one pool named {self.args.pool_name}, found {len(found)}")
        described = self.runner(
            ["cognito-idp", "describe-user-pool", "--user-pool-id", found[0]["Id"]], None
        )["UserPool"]
        if described.get("UsernameAttributes") != ["email"]:
            raise Refusal("the pool no longer uses email as the username; review this script")
        return described

    def client_id(self, pool_id: str) -> str:
        clients = self.runner(
            ["cognito-idp", "list-user-pool-clients", "--user-pool-id", pool_id, "--max-results", "60"],
            None,
        )["UserPoolClients"]
        found = [c for c in clients if c.get("ClientName") == self.args.client_name]
        if len(found) != 1:
            raise Refusal(f"expected exactly one client named {self.args.client_name}")
        return found[0]["ClientId"]

    def user_exists(self, pool_id: str, email: str) -> bool:
        listed = self.runner(
            ["cognito-idp", "list-users", "--user-pool-id", pool_id, "--filter", f'email = "{email}"'],
            None,
        )
        return bool(listed.get("Users"))

    # ---- manifest ----------------------------------------------------------
    def load(self) -> dict[str, Any]:
        if not self.manifest_path.is_file():
            raise Refusal(f"no manifest at {self.manifest_path}; run create first")
        mode = stat.S_IMODE(self.manifest_path.stat().st_mode)
        if mode & 0o077:
            raise Refusal("the manifest must be private (0600)")
        return json.loads(self.manifest_path.read_text())

    def save(self, manifest: dict[str, Any]) -> None:
        self.state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(self.state_dir, 0o700)
        temp = self.manifest_path.with_suffix(".tmp")
        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as stream:
            json.dump(manifest, stream, indent=2)
        os.replace(temp, self.manifest_path)

    # ---- guards ------------------------------------------------------------
    def guard(self) -> None:
        if inside_git_checkout(self.state_dir):
            raise Refusal("--state-dir must be outside any git checkout")
        if self.args.execute and self.args.confirm_pool != self.args.pool_name:
            raise Refusal(f"--execute also needs --confirm-pool {self.args.pool_name}")

    # ---- subcommands -------------------------------------------------------
    def template(self) -> str:
        """--email BASE (one real address) or --email-template with {n}."""
        base, template = self.args.email, self.args.email_template
        if bool(base) == bool(template):
            raise Refusal("give exactly one of --email (your address) or --email-template")
        if template:
            if "{n}" not in template:
                raise Refusal("--email-template must contain {n}")
            return template
        if not EMAIL.match(base) or "+" in base.split("@")[0]:
            raise Refusal(f"--email must be one plain address such as name@gmail.com (got {base!r})")
        local, domain = base.split("@")
        # Plus addressing: mail for name+tag@domain reaches name@domain, so the owner stays
        # in control of every test address, and the tag makes the accounts easy to spot.
        return f"{local}+pals-lt{{n}}@{domain}"

    def create(self) -> int:
        count = self.args.count
        if not 1 <= count <= MAX_COUNT:
            raise Refusal(f"--count must be between 1 and {MAX_COUNT}")
        template = self.template()
        emails = [template.format(n=f"{i:02d}") for i in range(1, count + 1)]
        bad = [e for e in emails if not EMAIL.match(e)]
        if bad or len(set(emails)) != count:
            raise Refusal(f"this would produce an invalid or repeated address, e.g. {(bad or emails)[0]!r}")
        if self.manifest_path.exists():
            raise Refusal(f"{self.manifest_path} already exists; delete or move it first")
        pool = self.pool()
        taken = [e for e in emails if self.user_exists(pool["Id"], e)]
        if taken:
            raise Refusal(f"{len(taken)} address(es) already exist in the pool; refusing to touch them")
        minimum = pool.get("Policies", {}).get("PasswordPolicy", {}).get("MinimumLength", 14)
        print(f"pool: {self.args.pool_name} ({pool.get('EstimatedNumberOfUsers')} users now)")
        print(f"accounts to create: {count}  ->  {emails[0]} ... {emails[-1]}")
        print(f"password: random, {max(24, minimum + 8)} chars; stored only in {self.manifest_path} (0600)")
        print("no mail is sent; addresses are marked verified; accounts are CONFIRMED with permanent passwords")
        if not self.args.execute:
            print("DRY RUN: nothing was changed. Add --execute --confirm-pool %s to create." % self.args.pool_name)
            return 0
        run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        manifest: dict[str, Any] = {"run_id": run_id, "pool_name": self.args.pool_name,
                                    "pool_id": pool["Id"], "accounts": []}
        for email in emails:
            password = make_password(minimum)
            created = self.runner(["cognito-idp", "admin-create-user"], {
                "UserPoolId": pool["Id"], "Username": email, "MessageAction": "SUPPRESS",
                "UserAttributes": [{"Name": "email", "Value": email},
                                   {"Name": "email_verified", "Value": "true"}]})
            sub = next(a["Value"] for a in created["User"]["Attributes"] if a["Name"] == "sub")
            # Record the account before the password step so a failure stays cleanable.
            manifest["accounts"].append({"email": email, "sub": sub, "password": password})
            self.save(manifest)
            self.runner(["cognito-idp", "admin-set-user-password"], {
                "UserPoolId": pool["Id"], "Username": email, "Password": password, "Permanent": True})
            print(f"created {email}  sub={sub}")
        self.write_grant_commands(manifest)
        print(f"done. manifest: {self.manifest_path}")
        return 0

    def write_grant_commands(self, manifest: dict[str, Any]) -> None:
        expires = (datetime.now(UTC) + timedelta(hours=self.args.entitlement_hours)).isoformat(timespec="seconds")
        lines = ["#!/bin/sh", "# Run from pals-api/ with PALS_BILLING_OPERATOR_DATABASE_URL and the Cognito",
                 "# PALS_COGNITO_USER_POOL_ID / PALS_COGNITO_ISSUER set. This script only prints; it changes nothing.", ""]
        for account in manifest["accounts"]:
            lines.append(
                "python -m app.release.billing_test_entitlement grant"
                f" --subject '{account['sub']}' --grant-id '{uuid.uuid4()}'"
                f" --expires-at '{expires}' --reason 'load test {manifest['run_id']}'")
        path = self.state_dir / "grant-commands.sh"
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as stream:
            stream.write("\n".join(lines) + "\n")
        print(f"entitlement grant commands (not run): {path}  expires {expires}")

    def verify(self) -> int:
        manifest = self.load()
        pool = self.pool()
        if pool["Id"] != manifest["pool_id"]:
            raise Refusal("the manifest belongs to a different pool")
        client = self.client_id(pool["Id"])
        print(f"will sign in {len(manifest['accounts'])} accounts through client {self.args.client_name}")
        if not self.args.execute:
            print("DRY RUN: no sign-in attempted. Add --execute --confirm-pool %s." % self.args.pool_name)
            return 0
        failed = 0
        for account in manifest["accounts"]:
            try:
                result = self.runner(["cognito-idp", "initiate-auth"], {
                    "AuthFlow": "USER_PASSWORD_AUTH", "ClientId": client,
                    "AuthParameters": {"USERNAME": account["email"], "PASSWORD": account["password"]}})
                ok = "AuthenticationResult" in result  # tokens are discarded, never printed
            except Refusal as error:
                ok, reason = False, str(error)[:120]
            print(f"{'ok  ' if ok else 'FAIL'} {account['email']}" + ("" if ok else f"  {reason if not ok else ''}"))
            failed += 0 if ok else 1
        return 1 if failed else 0

    def delete(self) -> int:
        manifest = self.load()
        pool = self.pool()
        if pool["Id"] != manifest["pool_id"]:
            raise Refusal("the manifest belongs to a different pool")
        print(f"will delete {len(manifest['accounts'])} accounts listed in {self.manifest_path} (nothing else)")
        if not self.args.execute:
            print("DRY RUN: nothing deleted. Add --execute --confirm-pool %s." % self.args.pool_name)
            return 0
        for account in manifest["accounts"]:
            try:
                found = self.runner(["cognito-idp", "admin-get-user", "--user-pool-id", pool["Id"],
                                     "--username", account["email"]], None)
            except Refusal:
                print(f"gone {account['email']}")
                continue
            sub = next((a["Value"] for a in found.get("UserAttributes", []) if a["Name"] == "sub"), None)
            if sub != account["sub"]:
                raise Refusal(f"{account['email']} no longer matches the recorded subject; not deleting")
            self.runner(["cognito-idp", "admin-delete-user", "--user-pool-id", pool["Id"],
                         "--username", account["email"]], None)
            print(f"deleted {account['email']}")
        self.manifest_path.rename(self.manifest_path.with_name(f"manifest.deleted-{manifest['run_id']}.json"))
        return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("command", choices=["create", "verify", "delete"])
    p.add_argument("--profile", default=os.environ.get("AWS_PROFILE", "pals-prod-member"))
    p.add_argument("--region", default=DEFAULT_REGION)
    p.add_argument("--pool-name", default=DEFAULT_POOL)
    p.add_argument("--client-name", default=DEFAULT_CLIENT)
    p.add_argument("--count", type=int, default=10)
    p.add_argument("--email", help="your own address, e.g. name@gmail.com; accounts become "
                   "name+pals-lt01@gmail.com ... (mail still reaches you; none is sent)")
    p.add_argument("--email-template", help="alternative to --email; must contain {n}")
    p.add_argument("--entitlement-hours", type=int, default=72)
    p.add_argument("--state-dir", default="~/.pals-loadtest")
    p.add_argument("--execute", action="store_true")
    p.add_argument("--confirm-pool")
    return p


def main(argv: list[str] | None = None, runner: Runner | None = None) -> int:
    args = parser().parse_args(argv)
    tool = Tool(args, runner)
    try:
        tool.guard()
        return {"create": tool.create, "verify": tool.verify, "delete": tool.delete}[args.command]()
    except Refusal as refusal:
        print(f"REFUSED: {refusal}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
