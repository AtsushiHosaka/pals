"""GitHub check selection policy; transport is outside these unit tests."""
import importlib.util
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("source_checks", Path(__file__).resolve().parents[1] / "release-source-checks.py")
C = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(C)


def run(**changes):
    result = {"id": 1, "name": "api-regression", "app": {"id": 15368},
              "started_at": "2026-11-08T12:00:00Z", "status": "completed", "conclusion": "success",
              "verified_workflow_path": ".github/workflows/application-regression.yml"}
    result.update(changes)
    return result


class SourceChecksTest(unittest.TestCase):
    def test_actual_actions_success(self):
        C.require_check([run()], "api-regression")

    def test_skipped_or_missing_does_not_pass(self):
        for conclusion in ("skipped", "neutral", "failure", "cancelled", None):
            with self.assertRaises(ValueError):
                C.require_check([run(conclusion=conclusion)], "api-regression")
        with self.assertRaises(ValueError):
            C.require_check([], "api-regression")

    def test_same_name_from_another_app_cannot_satisfy_gate(self):
        with self.assertRaises(ValueError):
            C.require_check([run(app={"id": 1})], "api-regression")

    def test_failed_or_running_latest_attempt_blocks_old_green(self):
        for status in ("completed", "in_progress"):
            with self.assertRaises(ValueError):
                C.require_check([run(), run(id=2, status=status, conclusion="failure")], "api-regression")

    def test_queued_latest_attempt_cannot_reuse_old_green(self):
        with self.assertRaises(ValueError):
            C.require_check([run(), run(id=2, started_at=None, status="queued", conclusion=None)], "api-regression")

    def test_same_job_from_another_actions_workflow_cannot_satisfy_gate(self):
        with self.assertRaisesRegex(ValueError, "workflow_identity_differs"):
            C.require_check([run(verified_workflow_path=".github/workflows/unrelated.yml")], "api-regression")

    def test_changed_verifier_override_requires_its_own_actual_checks(self):
        old = {"source_commits": {name: "a" * 40 for name in C.CHECKS}, "verifier_source": {"commit": "a" * 40}}
        new = {"source_commits": dict(old["source_commits"]), "verifier_source": {"commit": "b" * 40}}
        calls = []
        def fetch(repo, source):
            calls.append((repo, source)); return [run(name="agent-regression")]
        rows = C.check_sources(new, old, fetch)
        self.assertEqual(calls, [("pals-agent", "b" * 40)])
        self.assertEqual(rows[-1]["role"], "verifier")

    def test_only_changed_sources_require_fresh_checks(self):
        old = {"source_commits": {name: "a" * 40 for name in C.CHECKS}}
        new = {"source_commits": {**old["source_commits"], "pals-api": "b" * 40}}
        calls = []
        def fetch(repo, source):
            calls.append((repo, source)); return [run()]
        rows = C.check_sources(new, old, fetch)
        self.assertEqual(calls, [("pals-api", "b" * 40)])
        self.assertEqual(sum(row["status"] == "actual_required_check_passed" for row in rows), 1)


if __name__ == "__main__":
    unittest.main()
