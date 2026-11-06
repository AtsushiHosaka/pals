"""Regression checks for the PQO state/series contradiction and source-copy drift."""

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "pals-scripts/validate-proof-quality-completion-contract.py"
loader = importlib.util.spec_from_file_location("completion_contract_check", MODULE_PATH)
assert loader is not None and loader.loader is not None
module = importlib.util.module_from_spec(loader)
loader.loader.exec_module(module)
CANONICAL = ROOT / "specs/proof-quality-observability"


class CompletionContractTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.spec = Path(self.directory.name)
        for name in ("requirements.md", "design.md", "tasks.md", "completion-metrics.v1.json"):
            (self.spec / name).write_bytes((CANONICAL / name).read_bytes())

    def test_current_contract_matches_readable_specs(self):
        self.assertEqual(module.validate(self.spec), [])

    def test_original_missing_state_permission_is_rejected(self):
        path = self.spec / "requirements.md"
        text = path.read_text()
        old = next(line for line in text.splitlines() if line.startswith("| PQO-005 |"))
        path.write_text(text.replace(old, "| PQO-005 | `Environment`、`Route`だけを許可する。 |"))
        self.assertIn("requirement_state_allowlist", module.validate(self.spec))

    def test_route_cannot_replace_the_state_dimension(self):
        path = self.spec / "design.md"
        path.write_text(path.read_text().replace("`[Environment, State]`", "`[Environment, Route]`"))
        self.assertIn("metric_unit_or_dimensions", module.validate(self.spec))

    def test_missing_metric_and_wrong_unit_are_rejected(self):
        path = self.spec / "design.md"
        text = path.read_text().replace("| `ProofRequestsAccepted` | Count", "| `ProofRequestsAccepted` | Seconds")
        text = "\n".join(line for line in text.splitlines() if not line.startswith("| `LeanJobsUnreconciled` |"))
        path.write_text(text)
        errors = module.validate(self.spec)
        self.assertIn("metric_unit_or_dimensions", errors)
        self.assertIn("metric_missing_from_design", errors)

    def test_child_copy_requires_exact_bytes(self):
        copy = self.spec / "child.json"
        raw = (self.spec / "completion-metrics.v1.json").read_bytes()
        copy.write_bytes(raw)
        self.assertEqual(module.validate(self.spec, [copy]), [])
        copy.write_bytes(raw + b"\n")
        self.assertIn("child_contract_bytes_differ", module.validate(self.spec, [copy]))


if __name__ == "__main__":
    unittest.main()
