"""Exercise diagnostic capture with synthetic providers, without network access."""

import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1]
CASES = {
    "aws-cost": ([], ["aws-cost.json"]),
    "cloudwatch-logs": (["--trace-id", "fixture"], ["_api.json", "_agent.json"]),
    "langfuse-traces": (["--trace-id", "fixture"], ["langfuse-trace.json"]),
    "proof-job": (["--proof-job-id", "fixture"], ["proof-job.json"]),
}


class FetchExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="pals-fetch-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.scripts = self.root / "pals-scripts"
        for directory in ("lib", "fetch"):
            shutil.copytree(SCRIPTS / directory, self.scripts / directory)
        (self.scripts / ".env.local").write_text(
            "LANGFUSE_PUBLIC_KEY=fixture\nLANGFUSE_SECRET_KEY=fixture\n"
            "LANGFUSE_HOST=http://fixture.invalid\nPALS_ACCESS_TOKEN=fixture\n"
            "PALS_API_BASE_URL=http://fixture.invalid\n"
            "PALS_CLOUDWATCH_LOG_GROUP_API=/api\n"
            "PALS_CLOUDWATCH_LOG_GROUP_AGENT=/agent\n"
        )
        self.bin = self.root / "bin"
        self.bin.mkdir()
        provider = self.bin / "provider"
        provider.write_text(
            f"#!{sys.executable}\n" + r'''
import os
from pathlib import Path
import signal
import stat
import sys

root = Path(os.environ["FETCH_TEST_SCRIPTS"]) / "outputs" / "local"
mode = os.environ["FETCH_TEST_CASE"]
if mode == "missing-python":
    (Path(os.environ["FETCH_TEST_BIN"]) / "python3").unlink(missing_ok=True)
if mode == "invalid":
    sys.stdout.buffer.write(b"\xffaccess_token=raw-fixture-sentinel\n")
else:
    sys.stdout.write('{"access_token":"raw-fixture-sentinel","safe":"keep-me"}\n')
sys.stdout.flush()
if mode == "inspect":
    for directory in root.iterdir():
        assert stat.S_IMODE(directory.stat().st_mode) == 0o700
        for artifact in directory.iterdir():
            assert stat.S_IMODE(artifact.stat().st_mode) == 0o600
            assert b"raw-fixture-sentinel" not in artifact.read_bytes()
if mode == "fail":
    sys.exit(23)
if mode == "terminate":
    os.kill(os.getppid(), signal.SIGTERM)
'''
        )
        provider.chmod(0o755)
        for name in ("aws", "curl"):
            (self.bin / name).symlink_to(provider)
        # Explicit PATH also lets the missing-interpreter case avoid host fallbacks.
        for name in ("bash", "dirname", "date", "mkdir", "mktemp", "rm", "mv", "find", "tr", "cat"):
            executable = shutil.which(name)
            self.assertIsNotNone(executable, name)
            (self.bin / name).symlink_to(executable)
        (self.bin / "python3").symlink_to(sys.executable)
        self.env = dict(os.environ, PATH=str(self.bin), FETCH_TEST_SCRIPTS=str(self.scripts),
                        FETCH_TEST_BIN=str(self.bin), FETCH_TEST_CASE="inspect")

    def run_fetch(self, name, mode="inspect"):
        args, _ = CASES[name]
        return subprocess.run(
            [shutil.which("bash"), "-c", 'umask 022; exec bash "$@"', "fetch-test",
             str(self.scripts / "fetch" / f"{name}.sh"), "--env", "local", *args],
            env=dict(self.env, FETCH_TEST_CASE=mode), capture_output=True, text=True, timeout=15,
        )

    def assert_clean_failure(self, result):
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        root = self.scripts / "outputs"
        self.assertEqual([p for p in root.rglob("*") if p.is_file()], [])
        self.assertEqual(list(root.rglob(".fetch.*")), [])

    def test_private_capture_and_successful_manifest_for_every_fetcher(self):
        # Existing readable parents must not force readable run directories/files.
        parent = self.scripts / "outputs" / "local"
        parent.mkdir(parents=True)
        parent.chmod(0o755)
        for name, (_, filenames) in CASES.items():
            with self.subTest(name=name):
                result = self.run_fetch(name)
                self.assertEqual(result.returncode, 0, result.stderr)
                output = Path(result.stdout.strip())
                self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o700)
                self.assertEqual(sorted(p.name for p in output.iterdir()), sorted([*filenames, "manifest.json"]))
                self.assertEqual(stat.S_IMODE((output / "manifest.json").stat().st_mode), 0o600)
                for filename in filenames:
                    artifact = output / filename
                    self.assertEqual(stat.S_IMODE(artifact.stat().st_mode), 0o600)
                    self.assertEqual(json.loads(artifact.read_text()),
                                     {"access_token": "[REDACTED]", "safe": "keep-me"})
                self.assertTrue(json.loads((output / "manifest.json").read_text())["redacted"])

    def test_producer_failure_discards_partial_response(self):
        for name in CASES:
            with self.subTest(name=name):
                result = self.run_fetch(name, "fail")
                self.assertEqual(result.returncode, 23, result.stderr)
                self.assert_clean_failure(result)

    def test_invalid_utf8_discards_response(self):
        for name in CASES:
            with self.subTest(name=name):
                self.assert_clean_failure(self.run_fetch(name, "invalid"))

    def test_missing_python_discards_response(self):
        (self.bin / "python3").unlink()
        self.assert_clean_failure(self.run_fetch("proof-job", "missing-python"))

    def test_termination_discards_response(self):
        self.assert_clean_failure(self.run_fetch("proof-job", "terminate"))

    def test_publication_failure_discards_temporary_output(self):
        move = self.bin / "mv"
        move.unlink()
        move.write_text("#!/bin/bash\nexit 19\n")
        move.chmod(0o755)
        result = self.run_fetch("proof-job")
        self.assertEqual(result.returncode, 19, result.stderr)
        self.assert_clean_failure(result)

    def test_staging_creation_failure_does_not_fetch(self):
        # Allow directory allocation, then fail the staging-file allocation.
        temp = self.bin / "mktemp"
        executable = str(temp.resolve())
        temp.unlink()
        temp.write_text(f'#!/bin/bash\nif [[ "$1" == -d ]]; then exec "{executable}" "$@"; fi\nexit 17\n')
        temp.chmod(0o755)
        result = self.run_fetch("proof-job")
        self.assertEqual(result.returncode, 17, result.stderr)
        self.assert_clean_failure(result)

    def test_same_second_exports_are_unique(self):
        date = self.bin / "date"
        date.unlink()
        date.write_text("#!/bin/bash\nprintf '%s\\n' 20261008T000000Z\n")
        date.chmod(0o755)
        result = subprocess.run(
            [shutil.which("bash"), "-c", 'umask 022; source "$1/lib/common.sh"; '
             'PALS_ENV=local; make_output_dir proof-job; make_output_dir proof-job',
             "fetch-test", str(self.scripts)],
            env=self.env, capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        paths = result.stdout.splitlines()
        self.assertEqual(len(set(paths)), 2)
        self.assertTrue(all(Path(path).is_dir() for path in paths))

    def test_symlink_output_parent_is_rejected(self):
        external = self.root / "external"
        external.mkdir()
        (self.scripts / "outputs").symlink_to(external, target_is_directory=True)
        result = self.run_fetch("proof-job")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(external.iterdir()), [])

    def test_symlink_environment_parent_is_rejected(self):
        external = self.root / "external"
        external.mkdir()
        output = self.scripts / "outputs"
        output.mkdir()
        (output / "local").symlink_to(external, target_is_directory=True)
        result = self.run_fetch("proof-job")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(external.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
