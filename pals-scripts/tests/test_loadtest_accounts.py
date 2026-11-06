import contextlib
import importlib.util
import io
import json
import re
import stat
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "loadtest-accounts.py"
spec = importlib.util.spec_from_file_location("loadtest_accounts", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FakeCognito:
    """Records every call; keeps just enough pool state for the script's checks."""

    def __init__(self, existing: set[str] | None = None, policy_min: int = 14) -> None:
        self.calls: list[tuple[list[str], dict | None]] = []
        self.users: dict[str, str] = {e: f"sub-existing-{i}" for i, e in enumerate(existing or [])}
        self.policy_min = policy_min
        self.counter = 0

    def __call__(self, command, payload):
        self.calls.append((command, payload))
        op = command[1]
        if op == "list-user-pools":
            return {"UserPools": [{"Id": "pool-1", "Name": "pals-mini-prod"}]}
        if op == "describe-user-pool":
            return {"UserPool": {"Id": "pool-1", "UsernameAttributes": ["email"],
                                 "EstimatedNumberOfUsers": 10,
                                 "Policies": {"PasswordPolicy": {"MinimumLength": self.policy_min}}}}
        if op == "list-user-pool-clients":
            return {"UserPoolClients": [{"ClientName": "pals-mini-web", "ClientId": "client-1"}]}
        if op == "list-users":
            email = command[command.index("--filter") + 1].split('"')[1]
            return {"Users": [{"Username": email}] if email in self.users else []}
        if op == "admin-create-user":
            self.counter += 1
            sub = f"sub-new-{self.counter}"
            self.users[payload["Username"]] = sub
            return {"User": {"Attributes": [{"Name": "sub", "Value": sub}]}}
        if op == "admin-set-user-password":
            return {}
        if op == "initiate-auth":
            return {"AuthenticationResult": {"IdToken": "secret-token"}}
        if op == "admin-get-user":
            username = command[command.index("--username") + 1]
            if username not in self.users:
                raise module.Refusal("UserNotFoundException")
            return {"UserAttributes": [{"Name": "sub", "Value": self.users[username]}]}
        if op == "admin-delete-user":
            self.users.pop(command[command.index("--username") + 1])
            return {}
        raise AssertionError(f"unexpected call {command}")

    def mutating(self) -> list[str]:
        write_ops = {"admin-create-user", "admin-set-user-password", "admin-delete-user"}
        return [c[1] for c, _ in self.calls if c[1] in write_ops]


class LoadtestAccountsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state = str(Path(self.tmp.name) / "state")

    def run_main(self, argv, fake):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = module.main(["--state-dir", self.state, *argv], runner=fake)
        return code, out.getvalue(), err.getvalue()

    def create_args(self, extra=()):
        return ["create", "--email-template", "lt+{n}@example.com", "--count", "3", *extra]

    def test_password_has_every_class_and_is_long(self):
        for _ in range(200):
            password = module.make_password(14)
            self.assertGreaterEqual(len(password), 24)
            for pattern in (r"[a-z]", r"[A-Z]", r"[0-9]", r"[!#%*+=?@_-]"):
                self.assertRegex(password, pattern)

    def test_dry_run_changes_nothing(self):
        fake = FakeCognito()
        code, out, _ = self.run_main(self.create_args(), fake)
        self.assertEqual(code, 0)
        self.assertEqual(fake.mutating(), [])
        self.assertIn("DRY RUN", out)
        self.assertFalse((Path(self.state) / "manifest.json").exists())

    def test_execute_needs_the_pool_confirmation(self):
        fake = FakeCognito()
        code, _, err = self.run_main(self.create_args(["--execute"]), fake)
        self.assertEqual(code, 2)
        self.assertIn("--confirm-pool", err)
        self.assertEqual(fake.mutating(), [])

    def test_refuses_when_any_address_already_exists(self):
        fake = FakeCognito(existing={"lt+02@example.com"})
        code, _, err = self.run_main(
            self.create_args(["--execute", "--confirm-pool", "pals-mini-prod"]), fake)
        self.assertEqual(code, 2)
        self.assertIn("already exist", err)
        self.assertEqual(fake.mutating(), [])

    def test_template_without_placeholder_or_with_bad_address_is_refused(self):
        for template in ("lt@example.com", "bad{n}"):
            fake = FakeCognito()
            code, _, _ = self.run_main(
                ["create", "--email-template", template, "--count", "2"], fake)
            self.assertEqual(code, 2)
            self.assertEqual(fake.calls, [])

    def test_email_option_builds_plus_addresses_from_one_real_address(self):
        fake = FakeCognito()
        code, out, err = self.run_main(
            ["create", "--email", "name@gmail.com", "--count", "10",
             "--execute", "--confirm-pool", "pals-mini-prod"], fake)
        self.assertEqual(code, 0, err)
        manifest = json.loads((Path(self.state) / "manifest.json").read_text())
        emails = [a["email"] for a in manifest["accounts"]]
        self.assertEqual(emails[0], "name+pals-lt01@gmail.com")
        self.assertEqual(emails[-1], "name+pals-lt10@gmail.com")
        self.assertEqual(len(set(emails)), 10)

    def test_email_option_refuses_placeholders_non_ascii_and_tagged_addresses(self):
        for bad in ("あなたのアドレス", "あなた@gmail.com", "name+tag@gmail.com", "name", "@gmail.com"):
            fake = FakeCognito()
            code, _, err = self.run_main(["create", "--email", bad], fake)
            self.assertEqual(code, 2, bad)
            self.assertEqual(fake.calls, [], bad)

    def test_exactly_one_of_email_and_template_is_required(self):
        for argv in (["create"],
                     ["create", "--email", "a@gmail.com", "--email-template", "lt+{n}@gmail.com"]):
            fake = FakeCognito()
            code, _, err = self.run_main(argv, fake)
            self.assertEqual(code, 2)
            self.assertIn("exactly one", err)
            self.assertEqual(fake.calls, [])

    def test_create_writes_private_manifest_and_never_prints_passwords(self):
        fake = FakeCognito()
        code, out, err = self.run_main(
            self.create_args(["--execute", "--confirm-pool", "pals-mini-prod"]), fake)
        self.assertEqual(code, 0, err)
        manifest_path = Path(self.state) / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        self.assertEqual(len(manifest["accounts"]), 3)
        self.assertEqual(stat.S_IMODE(manifest_path.stat().st_mode), 0o600)
        for account in manifest["accounts"]:
            self.assertNotIn(account["password"], out + err)
        grants = (Path(self.state) / "grant-commands.sh").read_text()
        self.assertEqual(grants.count("billing_test_entitlement grant"), 3)
        for account in manifest["accounts"]:
            self.assertNotIn(account["password"], grants)
        self.assertEqual(fake.mutating().count("admin-create-user"), 3)
        for command, payload in fake.calls:
            self.assertNotIn("--password", command)  # secrets never on the command line
            if payload and "Password" in payload:
                self.assertTrue(payload["Permanent"])

    def test_refuses_to_overwrite_an_existing_manifest(self):
        fake = FakeCognito()
        args = self.create_args(["--execute", "--confirm-pool", "pals-mini-prod"])
        self.assertEqual(self.run_main(args, fake)[0], 0)
        code, _, err = self.run_main(args, FakeCognito())
        self.assertEqual(code, 2)
        self.assertIn("already exists", err)

    def test_verify_reports_ok_without_printing_tokens(self):
        fake = FakeCognito()
        self.run_main(self.create_args(["--execute", "--confirm-pool", "pals-mini-prod"]), fake)
        code, out, _ = self.run_main(["verify", "--execute", "--confirm-pool", "pals-mini-prod"], fake)
        self.assertEqual(code, 0)
        self.assertEqual(out.count("ok  "), 3)
        self.assertNotIn("secret-token", out)

    def test_delete_removes_only_manifest_accounts_and_checks_the_subject(self):
        fake = FakeCognito(existing={"someone@real.example"})
        self.run_main(self.create_args(["--execute", "--confirm-pool", "pals-mini-prod"]), fake)
        fake.users["lt+01@example.com"] = "sub-hijacked"  # same address, different account
        code, _, err = self.run_main(["delete", "--execute", "--confirm-pool", "pals-mini-prod"], fake)
        self.assertEqual(code, 2)
        self.assertIn("no longer matches", err)
        self.assertIn("lt+01@example.com", fake.users)

    def test_delete_happy_path_leaves_other_users(self):
        fake = FakeCognito(existing={"someone@real.example"})
        self.run_main(self.create_args(["--execute", "--confirm-pool", "pals-mini-prod"]), fake)
        code, out, _ = self.run_main(["delete", "--execute", "--confirm-pool", "pals-mini-prod"], fake)
        self.assertEqual(code, 0)
        self.assertEqual(out.count("deleted "), 3)
        self.assertEqual(set(fake.users), {"someone@real.example"})

    def test_state_dir_inside_a_git_checkout_is_refused(self):
        repo = Path(self.tmp.name) / "repo"
        (repo / ".git").mkdir(parents=True)
        self.state = str(repo / "out")
        code, _, err = self.run_main(self.create_args(), FakeCognito())
        self.assertEqual(code, 2)
        self.assertIn("outside any git checkout", err)

    def test_refuses_a_pool_that_no_longer_uses_email_usernames(self):
        class Different(FakeCognito):
            def __call__(self, command, payload):
                result = super().__call__(command, payload)
                if command[1] == "describe-user-pool":
                    result["UserPool"]["UsernameAttributes"] = ["phone_number"]
                return result

        code, _, err = self.run_main(self.create_args(), Different())
        self.assertEqual(code, 2)
        self.assertIn("email as the username", err)


if __name__ == "__main__":
    unittest.main()
