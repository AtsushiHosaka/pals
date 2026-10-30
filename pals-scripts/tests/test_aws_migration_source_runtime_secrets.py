"""Offline command-boundary tests; no Docker, AWS, or live source access."""
import ast
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

FILE = Path(__file__).resolve().parents[1] / "aws-migration-source-runtime-secrets.py"
spec = importlib.util.spec_from_file_location("runtime_secret_transfer", FILE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
SECRET = "synthetic-runtime-canary-do-not-emit"


def values():
    return {"/pals/prod/" + suffix: SECRET for suffix, _roles in m.SPEC.values()}


def parameter(name, value=SECRET, version=1):
    return {"Name": name, "ARN": m.arn(name), "Type": "SecureString",
            "Version": version, "Value": value, "DataType": "text"}


class Store:
    def __init__(self, existing=None):
        self.existing = existing or {}
        self.writes = []

    def identity(self):
        pass

    def get(self, name):
        return self.existing.get(name)

    def put(self, name, value):
        self.writes.append(name)
        self.existing[name] = parameter(name, value)
        return 1


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.directory = self.root / "migration"
        self.directory.mkdir(mode=0o700)

    def transfer(self, store, apply=True, reconcile=False):
        return m.transfer(store, values(), apply, reconcile, self.directory, lambda: None)

    def test_creates_five_and_receipt_has_no_value_or_value_hash(self):
        store = Store()
        result = self.transfer(store)
        self.assertEqual(len(store.writes), 5)
        self.assertEqual(result["status"], "verified")
        raw = (self.directory / m.JOURNAL).read_text()
        self.assertNotIn(SECRET, raw)
        self.assertNotIn("sha256", raw)
        self.assertNotIn("fingerprint", raw)
        self.assertEqual((self.directory / m.JOURNAL).stat().st_mode & 0o777, 0o600)

    def test_reuses_exact_existing_without_put(self):
        store = Store({n: parameter(n, version=7) for n in values()})
        result = self.transfer(store)
        self.assertEqual(store.writes, [])
        self.assertTrue(all(p["version"] == 7 for p in result["parameters"]))

    def test_last_existing_difference_prevents_all_puts(self):
        name = list(values())[-1]
        store = Store({name: parameter(name, "different-synthetic-value")})
        with self.assertRaises(m.GuardError):
            self.transfer(store)
        self.assertEqual(store.writes, [])

    def test_uncertain_write_blocks_apply_until_explicit_reconcile(self):
        store = Store()
        def uncertain(name, value):
            store.writes.append(name)
            store.existing[name] = parameter(name, value)
            raise m.GuardError("write_outcome_unverified")
        store.put = uncertain
        with self.assertRaises(m.GuardError):
            self.transfer(store)
        journal = json.loads((self.directory / m.JOURNAL).read_text())
        self.assertEqual(journal["status"], "reconcile_required")
        self.assertIsNotNone(journal["pending_parameter"])
        with self.assertRaises(m.GuardError):
            self.transfer(store)
        self.assertEqual(len(store.writes), 1)
        result = self.transfer(store, apply=False, reconcile=True)
        self.assertEqual(result["status"], "reconciled_absent")
        self.assertEqual(len(result["missing_parameters"]), 4)
        self.assertEqual(len(store.writes), 1)

    def test_readback_difference_retains_pending_receipt(self):
        store = Store()
        def wrong_readback(name, value):
            store.existing[name] = parameter(name, "different")
            return 1
        store.put = wrong_readback
        with self.assertRaises(m.GuardError):
            self.transfer(store)
        self.assertEqual(json.loads((self.directory / m.JOURNAL).read_text())["status"],
                         "reconcile_required")

    def test_explicit_mode_required(self):
        store = Store()
        with self.assertRaises(m.GuardError):
            self.transfer(store, apply=False)
        self.assertEqual(store.writes, [])

    def test_symlink_receipt_rejected(self):
        target = self.root / "foreign"
        target.write_text("{}")
        (self.directory / m.JOURNAL).symlink_to(target)
        with self.assertRaises(m.GuardError):
            self.transfer(Store())


class SourceTests(unittest.TestCase):
    def fixture(self):
        items = []
        for role, name in m.ACTORS.items():
            env = ["PALS_ENV=prod", "PALS_DATABASE_URL=forbidden-database-canary"]
            env += [key + "=" + SECRET for key, (_suffix, roles) in m.SPEC.items()
                    if role in roles]
            items.append({"Name": "/" + name, "Id": "a" * 64,
                          "Image": "sha256:" + "b" * 64,
                          "State": {"Running": True}, "Config": {"Env": env}})
        current = {"images": {"api": "sha256:" + "b" * 64,
                              "worker": "sha256:" + "b" * 64}}
        return current, items

    def test_only_fixed_five_selected(self):
        current, items = self.fixture()
        with patch.object(m, "successful", return_value=items):
            actual, _ids = m.source(current, ["docker"])
        self.assertEqual(actual, values())
        self.assertNotIn("forbidden-database-canary", repr(actual))

    def test_alias_mismatch_and_missing_actor_value_rejected(self):
        for mutation in ("alias", "missing", "duplicate", "name", "image"):
            with self.subTest(mutation=mutation):
                current, items = self.fixture()
                if mutation == "alias":
                    items[1]["Config"]["Env"].append("OPENAI_API_KEY=different")
                elif mutation == "missing":
                    items[2]["Config"]["Env"] = [x for x in items[2]["Config"]["Env"]
                                                if not x.startswith("PALS_OPENAI_API_KEY=")]
                elif mutation == "duplicate":
                    items[0]["Config"]["Env"].append("PALS_GUEST_HASH_KEY=" + SECRET)
                elif mutation == "name":
                    items[1]["Name"] = "/foreign"
                else:
                    items[1]["Image"] = "sha256:" + "c" * 64
                with patch.object(m, "successful", return_value=items), self.assertRaises(m.GuardError):
                    m.source(current, ["docker"])

    def test_plan_never_constructs_aws_store_or_receipt(self):
        root = Path("/protected/pals-mini-deploy")
        binding = (b"policy", b"config", b"current")
        observed = (root / "state", {}, ["docker"], binding)
        from contextlib import contextmanager
        @contextmanager
        def locked(_path):
            yield lambda: None
        with patch.object(m.Path, "home", return_value=root.parent), \
             patch.object(m, "protected", side_effect=lambda *a, **k: os.open(os.devnull, os.O_RDONLY)), \
             patch.object(m, "controller", return_value=observed), \
             patch.object(m, "lock", locked), \
             patch.object(m, "source", return_value=(values(), {})), \
             patch.object(m, "Parameters") as aws, patch.object(m, "receipt") as receipt, \
             redirect_stdout(io.StringIO()) as output:
            self.assertEqual(m.main([]), 0)
        aws.assert_not_called()
        receipt.assert_not_called()
        self.assertNotIn(SECRET, output.getvalue())
        self.assertEqual(json.loads(output.getvalue())["status"], "plan_only_no_AWS_calls")


class CommandTests(unittest.TestCase):
    def test_put_uses_stdin_and_no_secret_argv(self):
        name = next(iter(values()))
        with patch.object(m, "command", return_value=(0, b'{"Version":1}', b"")) as call:
            m.Parameters().put(name, SECRET)
        args, data = call.call_args.args
        self.assertNotIn(SECRET, repr(args))
        self.assertEqual(args[-1], "file:///dev/stdin")
        payload = json.loads(data)
        self.assertEqual(payload["Value"], SECRET)
        self.assertIs(payload["Overwrite"], False)
        self.assertEqual(payload["Type"], "SecureString")
        self.assertIn("https://ssm.ap-northeast-1.amazonaws.com", args)

    def test_get_type_arn_version_and_error_guards(self):
        name = next(iter(values()))
        for key, value in (("Type", "String"), ("ARN", "foreign"), ("Version", True),
                           ("Name", "/foreign")):
            p = parameter(name)
            p[key] = value
            with patch.object(m, "command", return_value=(0, json.dumps({"Parameter": p}).encode(), b"")), \
                 self.assertRaises(m.GuardError):
                m.Parameters().get(name)
        with patch.object(m, "command", return_value=(254, b"", b"An error occurred (ParameterNotFound) when calling the GetParameter operation: absent")):
            self.assertIsNone(m.Parameters().get(name))
        with patch.object(m, "command", return_value=(1, SECRET.encode(), SECRET.encode())), \
             self.assertRaises(m.GuardError) as error:
            m.Parameters().get(name)
        self.assertNotIn(SECRET, str(error.exception))

    def test_real_subprocess_stdin_bounded_and_environment_closed(self):
        m.DEADLINE = time.monotonic() + 5
        with patch.dict(os.environ, {"AWS_ENDPOINT_URL": "https://foreign.invalid",
                                     "AWS_CA_BUNDLE": "/foreign", "UNRELATED_SECRET": SECRET}):
            code, out, err = m.command([sys.executable, "-c",
                "import os,sys; d=sys.stdin.buffer.read(); assert not any(k in os.environ for k in ('AWS_ENDPOINT_URL','AWS_CA_BUNDLE','UNRELATED_SECRET')); sys.stdout.buffer.write(d)"], b"synthetic-pipe-payload")
        self.assertEqual((code, out, err), (0, b"synthetic-pipe-payload", b""))

    def test_python39_syntax(self):
        ast.parse(FILE.read_text(), feature_version=(3, 9))

    def test_cli_history_custom_CA_and_plugins_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary).resolve()
            directory = home / ".aws"
            directory.mkdir(mode=0o700)
            config = directory / "config"
            base = "[profile pals-migration-operator]\nregion=ap-northeast-1\n"
            for extra in ("", "cli_history=enabled\n", "ca_bundle=/foreign\n",
                          "\n[plugins]\nsteal=foreign.plugin\n"):
                config.write_text(base + extra)
                config.chmod(0o600)
                with patch.object(m.Path, "home", return_value=home):
                    if extra:
                        with self.assertRaises(m.GuardError):
                            m.aws_cli_privacy()
                    else:
                        m.aws_cli_privacy()

    def test_real_failure_console_never_displays_exception_payload(self):
        result = subprocess.run([sys.executable, str(FILE)], env={"HOME": "/nonexistent/" + SECRET},
                                capture_output=True, timeout=5, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(SECRET.encode(), result.stdout + result.stderr)

    def test_invalid_arguments_never_echo_payload(self):
        result = subprocess.run([sys.executable, str(FILE), "--" + SECRET],
                                capture_output=True, timeout=5, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(SECRET.encode(), result.stdout + result.stderr)

    def test_output_limit_and_timeout_are_actual_subprocess_bounds(self):
        m.DEADLINE = time.monotonic() + 5
        with patch.object(m, "MAX_OUTPUT", 1024), self.assertRaises(m.GuardError):
            m.command([sys.executable, "-c", "import sys; sys.stdout.write('x'*65536)"])
        m.DEADLINE = time.monotonic() + 0.1
        began = time.monotonic()
        with self.assertRaises(m.GuardError):
            m.command([sys.executable, "-c", "import time; time.sleep(5)"])
        self.assertLess(time.monotonic()-began, 2)


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "pals-mini-deploy"
        self.root.mkdir(mode=0o700)
        self.state = self.root / "state"
        self.state.mkdir(mode=0o700)
        self.containers = {**m.ACTORS, "web": "pals-web", "verifier": "pals-verifier",
                           "reconciler": "pals-reconciler"}
        self.policy = {"schema_version": "pals.macmini-host-controller.v1",
                       "runtime_profile": "isolated-lean-v1", "containers": self.containers,
                       "state_dir": str(self.state), "docker_context": "existing-mini",
                       "docker_binary": "/usr/local/bin/docker", "docker_config": "/protected/.docker",
                       "database_identity": {"database_system_identifier": "fixture-only"}}
        self.config = {k: self.policy[k] for k in ("containers", "state_dir", "docker_context",
                                                  "database_identity")}
        self.current = {"status": "healthy", "manifest_sha256": "a" * 64,
                        "database_identity": self.policy["database_identity"],
                        "images": {"api": "sha256:" + "b" * 64,
                                   "worker": "sha256:" + "c" * 64}}
        self.write(self.root / "controller-policy.json", self.policy)
        self.write(self.root / "deploy-config.json", self.config)
        self.write(self.state / "current.json", self.current)
        self.write(self.state / "host-update.lock", {})

    def write(self, path, value):
        path.write_text(json.dumps(value))
        path.chmod(0o600)

    def test_actual_protected_controller_paths_and_docker_prefix(self):
        state, current, docker, _binding = m.controller(self.root)
        self.assertEqual(state, self.state)
        self.assertEqual(current, self.current)
        self.assertEqual(docker, ["/usr/local/bin/docker", "--config", "/protected/.docker",
                                  "--context", "existing-mini"])
        with m.lock(self.state / "host-update.lock") as verify:
            verify()

    def test_controller_actor_alias_current_and_pending_mismatch(self):
        for mutation in ("alias", "database", "unhealthy", "pending"):
            with self.subTest(mutation=mutation):
                if mutation == "alias":
                    self.config["containers"] = {**self.containers, "worker": "foreign"}
                    self.write(self.root / "deploy-config.json", self.config)
                elif mutation == "database":
                    self.current["database_identity"] = {"foreign": True}
                    self.write(self.state / "current.json", self.current)
                elif mutation == "unhealthy":
                    self.current["status"] = "failed"
                    self.write(self.state / "current.json", self.current)
                else:
                    self.write(self.state / "normal-update-pending.json", {})
                with self.assertRaises(m.GuardError):
                    m.controller(self.root)
                self.config["containers"] = self.containers
                self.current.update(status="healthy", database_identity=self.policy["database_identity"])
                self.write(self.root / "deploy-config.json", self.config)
                self.write(self.state / "current.json", self.current)

    def test_lock_replacement_and_duplicate_json_rejected(self):
        with self.assertRaises(m.GuardError), m.lock(self.state / "host-update.lock") as verify:
            replacement = self.state / "replacement"
            self.write(replacement, {})
            os.replace(replacement, self.state / "host-update.lock")
            verify()
        path = self.state / "current.json"
        path.write_text('{"duplicate":1,"duplicate":2}')
        with self.assertRaises(m.GuardError):
            m.read_json(path)

    def test_world_readable_and_symlink_inputs_rejected(self):
        path = self.root / "controller-policy.json"
        path.chmod(0o644)
        with self.assertRaises(m.GuardError):
            m.controller(self.root)
        path.chmod(0o600)
        alias = self.root / "policy-alias"
        alias.symlink_to(path)
        with self.assertRaises(m.GuardError):
            m.read_json(alias)


if __name__ == "__main__":
    unittest.main()
