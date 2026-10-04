"""Independent audit regressions; uses only in-memory matrix copies and read-only sources."""

from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "foundation_audit", ROOT / "pals-scripts/audit-foundation-curriculum.py"
)
assert spec and spec.loader
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class FoundationCoverageTests(unittest.TestCase):
    def setUp(self):
        self.contract = audit.read(ROOT / audit.CONTRACT)
        self.matrix = audit.read(ROOT / self.contract["matrix_path"])
        self.inventory = audit.read(ROOT / audit.INVENTORY)
        self.scope = next(
            s for s in self.matrix["scopes"] if s["id"] == self.contract["scope_id"]
        )
        for family in self.scope["families"]:
            if family["stage"] in {"univ.linear", "univ.calculus", "univ.multivar"}:
                family["draft_bindings"] = []
        self.family = next(
            f for f in self.scope["families"] if f["id"] == "univ.linear.determinant"
        )
        self.binding = {
            "draft_id": "la_v4_det_transpose",
            "primary_mode": "justify_prove",
            "difficulty": "standard",
            "authoring_manifest": "docs/linear-algebra-v4-batch.json",
            "admission_manifest": None,
        }

    def report(self):
        return audit.build_report(ROOT, self.contract, self.matrix, self.inventory)

    def test_empty_bindings_credit_no_catalog_population(self):
        r = self.report()
        self.assertEqual(
            r["summary"]["all"]["authored"]["mode_slots"],
            {"filled": 0, "required": 150, "percent": 0.0},
        )
        self.assertEqual(
            r["summary"]["all"]["authored"]["difficulty_slots"]["required"], 120
        )
        self.assertGreater(r["all_catalog_records_not_credited_to_target_scope"], 300)

    def test_explicit_binding_credits_only_its_mode_and_difficulty(self):
        self.family["draft_bindings"] = [self.binding]
        r = self.report()
        self.assertEqual(r["summary"]["all"]["authored"]["mode_slots"]["filled"], 1)
        self.assertEqual(
            r["summary"]["all"]["authored"]["difficulty_slots"]["filled"], 1
        )
        self.assertEqual(
            r["summary"]["all"]["artifact_bound"]["mode_slots"]["filled"], 1
        )
        self.assertEqual(r["summary"]["all"]["authored"]["chapters_contract_met"], 0)

    def test_exact_missing_id_never_gets_credit(self):
        self.family["draft_bindings"] = [dict(self.binding, draft_id="not_a_real_card")]
        r = self.report()
        self.assertEqual(len(r["invalid_bindings"]), 1)
        self.assertEqual(r["summary"]["all"]["authored"]["mode_slots"]["filled"], 0)

    def test_id_in_wrong_manifest_never_gets_credit(self):
        self.family["draft_bindings"] = [
            dict(self.binding, authoring_manifest="docs/calculus-v4-batch.json")
        ]
        self.assertEqual(len(self.report()["invalid_bindings"]), 1)

    def test_wrong_profile_never_gets_credit(self):
        self.family["profile_requirement"] = "typed_real_analysis"
        self.family["draft_bindings"] = [self.binding]
        self.assertEqual(
            self.report()["invalid_bindings"][0]["reason"],
            "profile_not_allowed_for_family",
        )

    def test_no_invented_runtime_or_compile_receipt(self):
        self.family["draft_bindings"] = [self.binding]
        r = self.report()
        self.assertEqual(
            r["runtime_problem_execution"],
            {"status": "not_checked", "coverage_percent": None},
        )
        self.assertFalse(r["manifest_evidence"][0]["lean_replayed"])
        self.assertNotIn("compiler", r["manifest_evidence"][0])

    def test_failed_artifact_does_not_get_lean_credit(self):
        self.family["draft_bindings"] = [self.binding]
        with patch.object(
            audit,
            "artifact_evidence",
            return_value={"artifact_bound": False, "lean_replayed": False},
        ):
            r = self.report()
        self.assertEqual(r["summary"]["all"]["authored"]["mode_slots"]["filled"], 1)
        self.assertEqual(
            r["summary"]["all"]["artifact_bound"]["mode_slots"]["filled"], 0
        )

    def test_unknown_mode_fails(self):
        self.family["draft_bindings"] = [dict(self.binding, primary_mode="invented")]
        with self.assertRaises(ValueError):
            self.report()

    def test_unknown_difficulty_fails(self):
        self.family["draft_bindings"] = [dict(self.binding, difficulty="easy")]
        with self.assertRaises(ValueError):
            self.report()

    def test_denominator_cannot_be_reduced(self):
        self.contract["chapters"].pop()
        with self.assertRaisesRegex(ValueError, "denominator"):
            self.report()

    def test_duplicate_chapter_fails(self):
        self.contract["chapters"].append(copy.deepcopy(self.contract["chapters"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.report()

    def test_missing_form_fails(self):
        del self.contract["chapters"][0]["problem_forms"]["recognize"]
        with self.assertRaisesRegex(ValueError, "exactly"):
            self.report()

    def test_joint_cells_are_diagnostic_not_invented_requirements(self):
        self.family["draft_bindings"] = [self.binding]
        r = self.report()
        joint = [c for f in r["chapters"] for c in f["joint_cells_diagnostic_only"]]
        self.assertEqual(len(joint), 450)
        self.assertEqual(sum(bool(c["card_refs"]) for c in joint), 1)
        self.assertNotIn("required", joint[0])

    def test_path_escape_fails(self):
        with self.assertRaises(ValueError):
            audit.safe_path(ROOT, "../outside.json")

    def test_report_deterministic(self):
        self.family["draft_bindings"] = [self.binding]
        self.assertEqual(self.report(), self.report())

    def test_numeric_variable_variants_collapse(self):
        a = '<OMOBJ><OMA><OMS cd="relation1" name="eq"/><OMV name="x"/><OMI>2</OMI></OMA></OMOBJ>'
        b = '<OMOBJ><OMA><OMS cd="relation1" name="eq"/><OMV name="y"/><OMI>3</OMI></OMA></OMOBJ>'
        self.assertEqual(audit.structural_signature(a), audit.structural_signature(b))

    def test_stale_hash_cannot_get_artifact_credit(self):
        payload = audit.read(ROOT / self.binding["authoring_manifest"])
        payload["evidence"]["validator_sha256"] = "sha256:" + "0" * 64
        with patch.object(audit, "read", return_value=payload):
            evidence = audit.artifact_evidence(
                ROOT, self.binding["authoring_manifest"], False
            )
        self.assertFalse(evidence["artifact_bound"])
        self.assertIn("stale", evidence["error"])

    def test_changed_target_cannot_reuse_old_witness(self):
        payload = audit.read(ROOT / self.binding["authoring_manifest"])
        payload["cards"][0]["lean_target"] += " "
        with patch.object(audit, "read", return_value=payload):
            evidence = audit.artifact_evidence(
                ROOT, self.binding["authoring_manifest"], False
            )
        self.assertFalse(evidence["artifact_bound"])
        self.assertIn("witness bytes", evidence["error"])

    def test_structural_duplicate_does_not_fill_two_modes(self):
        second = dict(
            self.binding,
            draft_id="la_v4_det_diagonal",
            primary_mode="compute_construct",
        )
        self.family["draft_bindings"] = [self.binding, second]
        manifest = self.binding["authoring_manifest"]
        payload = audit.read(ROOT / manifest)
        first = next(c for c in payload["cards"] if c["id"] == self.binding["draft_id"])
        duplicate = next(c for c in payload["cards"] if c["id"] == second["draft_id"])
        duplicate["openmath_xml"] = first["openmath_xml"].replace("><", ">\n  <")
        original_read = audit.read
        with patch.object(
            audit,
            "read",
            side_effect=lambda p: payload if p == ROOT / manifest else original_read(p),
        ):
            report = self.report()
        self.assertEqual(len(report["structural_duplicate_bindings_excluded"]), 1)
        self.assertEqual(
            report["summary"]["all"]["authored"]["mode_slots"]["filled"], 1
        )

    def test_simulated_compiler_failure_gets_no_replay_credit(self):
        completed = audit.subprocess.CompletedProcess([], 1, "failure", "")
        with patch.object(audit.subprocess, "run", return_value=completed):
            evidence = audit.artifact_evidence(
                ROOT, self.binding["authoring_manifest"], True
            )
        self.assertTrue(evidence["artifact_bound"])
        self.assertFalse(evidence["lean_replayed"])

    def test_simulated_compiler_success_never_implies_runtime(self):
        completed = audit.subprocess.CompletedProcess([], 0, "", "")
        with patch.object(audit.subprocess, "run", return_value=completed):
            evidence = audit.artifact_evidence(
                ROOT, self.binding["authoring_manifest"], True
            )
        self.assertTrue(evidence["lean_replayed"])
        self.assertEqual(evidence["runtime_problem_execution"], "not_checked")

    def test_unrun_lean_coverage_is_unknown_not_zero(self):
        report = self.report()
        self.assertIsNone(
            report["summary"]["all"]["lean_replayed"]["mode_slots"]["percent"]
        )
        self.assertEqual(
            report["summary"]["all"]["lean_replayed"]["measurement_status"], "not_run"
        )

    def test_standard_difficulty_reports_the_two_required_slots(self):
        self.family["draft_bindings"] = [self.binding]
        report = self.report()
        gap = next(
            g
            for g in report["missing_difficulty_slots"]
            if g["family_id"] == self.family["id"] and g["difficulty"] == "standard"
        )
        self.assertEqual((gap["required"], gap["filled"], gap["missing"]), (2, 1, 1))

    def test_matrix_default_standard_count_cannot_shrink_denominator(self):
        for requirement in self.scope["defaults"]["required_difficulties"]:
            if requirement["id"] == "standard":
                requirement["minimum_distinct_patterns"] = 1
        with self.assertRaisesRegex(ValueError, "fixed curriculum denominator"):
            self.report()

    def test_family_override_cannot_shrink_or_increase_axes(self):
        for axis in ("required_modes", "required_difficulties"):
            with self.subTest(axis=axis):
                self.family[axis] = copy.deepcopy(self.scope["defaults"][axis])
                self.family[axis][0]["minimum_distinct_patterns"] += 1
                with self.assertRaisesRegex(ValueError, "Family requirements"):
                    self.report()
                del self.family[axis]

    def test_explicit_equal_family_overrides_preserve_fixed_denominators(self):
        for axis in ("required_modes", "required_difficulties"):
            self.family[axis] = list(reversed(self.contract[axis]))
        summary = self.report()["summary"]["all"]["authored"]
        self.assertEqual(summary["mode_slots"]["required"], 150)
        self.assertEqual(summary["difficulty_slots"]["required"], 120)

    def test_contract_axes_and_stage_counts_are_fixed_for_v1(self):
        original = copy.deepcopy(self.contract)
        for key in ("required_modes", "required_difficulties", "stage_chapter_counts"):
            with self.subTest(key=key):
                self.contract = copy.deepcopy(original)
                if key == "stage_chapter_counts":
                    self.contract[key]["univ.linear"] = 9
                else:
                    self.contract[key][0]["minimum_distinct_patterns"] += 1
                with self.assertRaises(ValueError):
                    self.report()

    def test_matrix_stage_count_cannot_be_reassigned(self):
        self.family["stage"] = "univ.calculus"
        with self.assertRaisesRegex(ValueError, "chapter counts"):
            self.report()

    def test_formatting_attribute_order_and_numeric_variants_collapse(self):
        x = '<OMOBJ><OMA><OMS cd="relation1" name="eq"/><OMV name="x"/><OMI>2</OMI></OMA></OMOBJ>'
        y = '<OMOBJ>\n <OMA><OMS name="eq" cd="relation1"/><OMV name="y"/><OMI>3</OMI></OMA>\n</OMOBJ>'
        self.assertEqual(audit.structural_signature(x), audit.structural_signature(y))
        self.assertNotEqual(
            audit.structural_signature(x),
            audit.structural_signature(y.replace('name="eq"', 'name="neq"')),
        )
        self.assertIsNone(audit.structural_signature("<invalid"))

    def test_fixed_contract_rejects_missing_or_duplicate_axis_id(self):
        original = copy.deepcopy(self.contract)
        for replacement in (
            self.contract["required_modes"][:-1],
            self.contract["required_modes"] + self.contract["required_modes"][:1],
        ):
            with self.subTest(replacement=replacement):
                self.contract = copy.deepcopy(original)
                self.contract["required_modes"] = replacement
                with self.assertRaises(ValueError):
                    self.report()


if __name__ == "__main__":
    unittest.main()
