"""Actual Make dispatch boundary only; the child sentinel proves no AWS behavior."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUARD = ROOT / "pals-scripts/require-release-cycle-v2.py"


class ReleaseCycleDispatchTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        shutil.copyfile(ROOT / "Makefile", self.root / "Makefile")
        scripts = self.root / "pals-scripts"
        scripts.mkdir()
        if GUARD.exists():
            shutil.copyfile(GUARD, scripts / GUARD.name)
        child = self.root / "pals-infra/scripts/release-cycle.py"
        child.parent.mkdir(parents=True)
        child.write_text("import json,pathlib,sys\n"
                         "pathlib.Path('child-dispatched.json').write_text(json.dumps(sys.argv[1:]))\n")
        self.sentinel = self.root / "child-dispatched.json"
        self.plan = self.root / "private-plan.json"

    def invoke(self, raw: bytes, *, reviewed_hash: str | None = None):
        self.plan.write_bytes(raw)
        self.plan.chmod(0o600)
        self.reviewed_hash = reviewed_hash or hashlib.sha256(raw).hexdigest()
        self.state = str(self.root / "private-state")
        return subprocess.run(["make", "--no-print-directory", "release-cycle",
            "RELEASE_PYTHON=" + sys.executable, "RELEASE_PLAN=" + str(self.plan),
            "RELEASE_PLAN_SHA256=" + self.reviewed_hash, "RELEASE_STATE_DIR=" + self.state,
            "RELEASE_APPLY=--apply"], cwd=self.root, capture_output=True, text=True, timeout=10, check=False)

    def assert_refused_before_child(self, raw: bytes, **options):
        result = self.invoke(raw, **options)
        self.assertFalse(self.sentinel.exists(), "invalid plan reached the external child dispatch")
        self.assertNotEqual(result.returncode, 0)

    def test_v1_plan_never_dispatches_child(self):
        self.assert_refused_before_child(b'{"schema_version":"pals.release-cycle.v1"}')

    def test_missing_release_alerts_never_dispatches_child(self):
        self.assert_refused_before_child(b'{"schema_version":"pals.release-cycle.v2"}')

    def test_non_object_release_alerts_never_dispatches_child(self):
        self.assert_refused_before_child(b'{"schema_version":"pals.release-cycle.v2","release_alerts":true}')

    def test_changed_raw_plan_hash_never_dispatches_child(self):
        self.assert_refused_before_child(b'{"schema_version":"pals.release-cycle.v2","release_alerts":{}}',
                                         reviewed_hash="f" * 64)

    def test_duplicate_key_never_dispatches_child(self):
        self.assert_refused_before_child(b'{"schema_version":"pals.release-cycle.v1",'
            b'"schema_version":"pals.release-cycle.v2","release_alerts":{}}')

    def test_nested_duplicate_key_never_dispatches_child(self):
        self.assert_refused_before_child(b'{"schema_version":"pals.release-cycle.v2",'
            b'"release_alerts":{"runner":"one","runner":"two"}}')

    def test_valid_v2_dispatches_original_child_with_unchanged_arguments(self):
        # This is deliberately only a parent shape check; full v2 validation is
        # the existing child controller's responsibility, not the sentinel's.
        result = self.invoke(b'{"schema_version":"pals.release-cycle.v2","release_alerts":{}}\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(self.sentinel.read_text()), ["--plan", str(self.plan),
            "--plan-sha256", self.reviewed_hash, "--state-dir", self.state, "--apply"])


if __name__ == "__main__":
    unittest.main()
