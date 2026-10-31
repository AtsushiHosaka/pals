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


class FailureDiagnosticTests(unittest.TestCase):
    def test_active_source_lock_is_distinguished_without_raw_error(self):
        result = m.failure_summary(BlockingIOError(SECRET))
        self.assertEqual(result["code"], "source_lock_busy")
        self.assertNotIn(SECRET, json.dumps(result))

    def test_fixed_guard_label_is_actionable_without_exception_text(self):
        self.assertEqual(m.failure_summary(m.GuardError("not_private"))["code"],
                         "not_private")

    def test_unknown_guard_text_is_not_emitted(self):
        output = json.dumps(m.failure_summary(m.GuardError(SECRET)))
        self.assertNotIn(SECRET, output)
        self.assertEqual(json.loads(output)["code"], "guard_rejected")

    def test_missing_path_does_not_emit_path(self):
        output = json.dumps(m.failure_summary(FileNotFoundError(2, SECRET, SECRET)))
        self.assertNotIn(SECRET, output)
        self.assertEqual(json.loads(output)["code"], "required_path_absent")

    def test_raw_command_error_is_not_emitted(self):
        output = json.dumps(m.failure_summary(RuntimeError(SECRET)))
        self.assertNotIn(SECRET, output)
        self.assertEqual(json.loads(output)["code"], "unexpected_failure")

    def test_json_decode_error_does_not_emit_document(self):
        output = json.dumps(m.failure_summary(json.JSONDecodeError(SECRET, SECRET, 0)))
        self.assertNotIn(SECRET, output)
        self.assertEqual(json.loads(output)["code"], "invalid_json")


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
    def test_structured_missing_with_cli_warning_uses_one_fixed_batch_read(self):
        name=next(iter(values()))
        out=json.dumps({'Parameters':[],'InvalidParameters':[name]}).encode()
        with patch.object(m,'command',return_value=(0,out,b'CLI warning format is irrelevant')) as call:
            self.assertIsNone(m.Parameters().get(name))
        self.assertEqual(call.call_count,1)
        args=call.call_args.args[0]
        self.assertIn('get-parameters',args);self.assertNotIn('get-parameter',args)
        self.assertEqual(args[args.index('--names')+1],name)
        self.assertEqual(args[args.index('--profile')+1],m.PROFILE)
        self.assertEqual(args[args.index('--region')+1],m.REGION)
        self.assertIn('https://ssm.ap-northeast-1.amazonaws.com',args)

    def test_failed_read_exposes_only_bounded_exit_and_format_metadata(self):
        with patch.object(m, "command", return_value=(255, SECRET.encode(), b"ParameterNotFound\x1b[0m")), self.assertRaises(m.GuardError) as caught:
            m.Parameters().get(next(iter(values())))
        summary = m.failure_summary(caught.exception)
        self.assertEqual(summary["aws_exit_code"], 255)
        self.assertIs(summary["parameter_not_found_label"], False)
        self.assertIs(summary["ansi_formatting_present"], False)
        self.assertNotIn(SECRET, json.dumps(summary))

    def test_structured_existing_parameter_validates_actual_value(self):
        name=next(iter(values()));existing=parameter(name)
        out=json.dumps({'Parameters':[existing],'InvalidParameters':[]}).encode()
        with patch.object(m,'command',return_value=(0,out,b'')):
            self.assertEqual(m.Parameters().get(name),existing)

    def test_put_uses_fifo_and_no_secret_argv(self):
        name = next(iter(values()))
        with patch.object(m, "fifo_json", return_value=(0, b'{"Version":1}', b"")) as call:
            m.Parameters().put(name, SECRET)
        args, data, _directory = call.call_args.args
        self.assertNotIn(SECRET, repr(args))
        self.assertEqual(args[-1], "put-parameter")
        payload = json.loads(data)
        self.assertEqual(payload["Value"], SECRET)
        self.assertIs(payload["Overwrite"], False)
        self.assertEqual(payload["Type"], "SecureString")
        self.assertIn("https://ssm.ap-northeast-1.amazonaws.com", args)

    def test_fifo_real_reader_private_kernel_transport_and_cleanup(self):
        m.DEADLINE=time.monotonic()+5
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary).resolve()
            payload=json.dumps({'Value':SECRET*500}).encode()
            child="import sys,json,stat,os; p=sys.argv[-1][7:]; s=os.lstat(p); assert stat.S_ISFIFO(s.st_mode) and stat.S_IMODE(s.st_mode)==0o600; v=json.load(open(p)); assert len(v['Value'])>1000; print('{\"Version\":1}')"
            code,out,err=m.fifo_json([sys.executable,'-c',child],payload,directory)
            self.assertEqual((code,json.loads(out),err),(0,{'Version':1},b''))
            self.assertEqual(list(directory.iterdir()),[]);self.assertNotIn(SECRET,out.decode())

    def test_fifo_reader_exit_and_expired_budget_cleanup_without_retry(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary).resolve();m.DEADLINE=time.monotonic()+5
            code,_out,_err=m.fifo_json([sys.executable,'-c','import sys;sys.exit(2)'],SECRET.encode(),directory)
            self.assertEqual(code,2);self.assertEqual(list(directory.iterdir()),[])
            m.DEADLINE=time.monotonic()-1
            with self.assertRaises(m.GuardError):m.fifo_json([sys.executable,'-c','pass'],SECRET.encode(),directory)
            self.assertEqual(list(directory.iterdir()),[])
            with patch.object(m,'command',side_effect=AssertionError('oversized payload never starts command')), \
                 self.assertRaises(m.GuardError):m.fifo_json([],b'x'*(m.MAX_OUTPUT+1),directory)
            self.assertEqual(list(directory.iterdir()),[])

    def test_put_error_reports_only_fixed_paramfile_diagnostics(self):
        err=SECRET.encode()+b' [Errno 6] Device not configured: paramfile'
        with patch.object(m,'fifo_json',return_value=(255,b'',err)),self.assertRaises(m.GuardError) as caught:
            m.Parameters().put(next(iter(values())),SECRET)
        summary=m.failure_summary(caught.exception)
        self.assertTrue(summary['stdin_device_unavailable']);self.assertTrue(summary['parameter_file_error'])
        self.assertNotIn(SECRET,json.dumps(summary))

    def test_probe_is_synthetic_offline_skeleton_for_both_transports(self):
        with patch.object(m,'command',return_value=(255,b'',b'[Errno 6] paramfile')) as pipe, \
             patch.object(m,'fifo_json',return_value=(0,b'{"Version":0}',b'')) as fifo:
            observed=m.Parameters().probe_transport()
        self.assertIs(observed['service_write_attempted'],False)
        self.assertFalse(observed['stdin']['input_loaded']);self.assertTrue(observed['fifo']['input_loaded'])
        for call in (pipe,fifo):
            args,payload=call.call_args.args[:2]
            self.assertEqual(args[args.index('--generate-cli-skeleton')+1],'output')
            self.assertNotIn(SECRET,repr(args));self.assertNotIn(SECRET,payload.decode())

    def test_probe_selects_one_transport_and_timeout_has_specific_phase(self):
        for selected in ('stdin','fifo'):
            with patch.object(m,'command',side_effect=m.GuardError('command_timeout')) as pipe, \
                 patch.object(m,'fifo_json',side_effect=m.GuardError('command_timeout')) as fifo:
                report=m.Parameters().probe_transport(selected)
            self.assertEqual(set(report),{'status','service_write_attempted',selected})
            self.assertEqual(report[selected]['phase'],'cli_transport_probe_'+selected)
            self.assertEqual(report[selected]['failure_code'],'command_timeout')
            self.assertEqual(pipe.call_count,1 if selected=='stdin' else 0)
            self.assertEqual(fifo.call_count,1 if selected=='fifo' else 0)

    def test_known_aws_codes_are_diagnostics_only_and_no_unknown_text(self):
        for code in ('AccessDeniedException','InvalidKeyId','ValidationException','ParameterAlreadyExists',
                     'ParameterLimitExceeded','UnsupportedParameterType','ThrottlingException'):
            err=SECRET.encode()+b' ('+code.encode()+b') '+SECRET.encode()
            with patch.object(m,'fifo_json',return_value=(254,SECRET.encode(),err)),self.assertRaises(m.GuardError) as caught:
                m.Parameters().put(next(iter(values())),SECRET)
            summary=m.failure_summary(caught.exception)
            self.assertEqual(summary['code'],'write_outcome_unverified')
            self.assertEqual(summary['aws_error_code'],code)
            self.assertEqual(summary['stdout_bytes'],len(SECRET.encode()))
            self.assertEqual(summary['stderr_bytes'],len(err))
            self.assertNotIn(SECRET,json.dumps(summary))
        error=m.GuardError('write_outcome_unverified')
        m.diagnose(error,b'',b'UnknownCode '+SECRET.encode())
        self.assertEqual(m.failure_summary(error)['aws_error_code'],'unclassified')

    def test_actual_timeout_reports_only_bounded_output_counts_and_labels(self):
        m.DEADLINE=time.monotonic()+0.15
        child="import sys,time;sys.stderr.write('AccessDeniedException synthetic-private-value');sys.stderr.flush();time.sleep(5)"
        with self.assertRaises(m.GuardError) as caught:m.command([sys.executable,'-c',child])
        summary=m.failure_summary(caught.exception)
        self.assertEqual(summary['aws_error_code'],'AccessDeniedException')
        self.assertGreater(summary['stderr_bytes'],0);self.assertEqual(summary['stdout_bytes'],0)
        self.assertNotIn('synthetic-private-value',json.dumps(summary))

    def test_get_type_arn_version_and_error_guards(self):
        name = next(iter(values()))
        for key, value in (("Type", "String"), ("ARN", "foreign"), ("Version", True),
                           ("Name", "/foreign")):
            p = parameter(name)
            p[key] = value
            with patch.object(m, "command", return_value=(0, json.dumps({"Parameters": [p], "InvalidParameters": []}).encode(), b"")), \
                 self.assertRaises(m.GuardError):
                m.Parameters().get(name)
        with patch.object(m, "command", return_value=(1, SECRET.encode(), SECRET.encode())), \
             self.assertRaises(m.GuardError) as error:
            m.Parameters().get(name)
        self.assertNotIn(SECRET, str(error.exception))

    def test_batch_wrong_multiple_missing_and_unknown_members_refused(self):
        name=next(iter(values()))
        for metadata in ({'Parameters':[],'InvalidParameters':['/foreign']},
                         {'Parameters':[],'InvalidParameters':[]},
                         {'Parameters':[],'InvalidParameters':[name,name]},
                         {'Parameters':[parameter(name),parameter(name)],'InvalidParameters':[]},
                         {'Parameters':[parameter(name)],'InvalidParameters':[name]},
                         {'Parameters':[None],'InvalidParameters':[]},
                         {'Parameters':[],'InvalidParameters':[name],'NextToken':'unknown'},
                         {'Parameters':None,'InvalidParameters':[name]}, {'Parameters':[]},{},[]):
            with patch.object(m,'command',return_value=(0,json.dumps(metadata).encode(),b'')), \
                 self.assertRaises(m.GuardError) as caught:
                m.Parameters().get(name)
            self.assertEqual(str(caught.exception),'parameter_batch_response_invalid')

    def test_batch_errors_and_malformed_json_never_fall_back_or_leak(self):
        for error in [(254,b'',b'AccessDeniedException'),(255,b'',b'ParameterNotFound'),
                      (254,SECRET.encode(),b'ParameterNotFound')]:
            with patch.object(m,'command',return_value=error) as call,self.assertRaises(m.GuardError) as caught:
                m.Parameters().get(next(iter(values())))
            self.assertEqual(call.call_count,1)
            self.assertEqual(str(caught.exception),'parameter_read_failed')
            self.assertNotIn(SECRET,json.dumps(m.failure_summary(caught.exception)))
        for raw in (SECRET.encode(),b'{"Parameters":[],"Parameters":[],"InvalidParameters":[]}',b'\xff'):
            with patch.object(m,'command',return_value=(0,raw,b'')),self.assertRaises(m.GuardError) as caught:
                m.Parameters().get(next(iter(values())))
            self.assertEqual(str(caught.exception),'parameter_batch_response_invalid')
            self.assertNotIn(SECRET,json.dumps(m.failure_summary(caught.exception)))

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
