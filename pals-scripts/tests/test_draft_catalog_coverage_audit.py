from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "pals-scripts/audit-draft-catalog-coverage.py"
MATRIX = ROOT / "specs/draft-catalog-expansion/coverage-matrix.v1.json"
SOURCES = ROOT / "specs/draft-catalog-expansion/inventory-sources.v1.json"
SPEC = importlib.util.spec_from_file_location("draft_catalog_coverage_audit", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class DraftCatalogCoverageAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
        self.sources = json.loads(SOURCES.read_text(encoding="utf-8"))

    def test_current_matrix_and_repository_inventory_are_distinguished(self) -> None:
        report = AUDIT.build_report(self.matrix, ROOT)
        scopes = {scope["id"]: scope for scope in report["coverage"]["scopes"]}

        self.assertEqual(scopes["school-japan-current"]["family_count"], 107)
        self.assertEqual(
            scopes["school-japan-current"]["required_distinct_patterns"], 321
        )
        self.assertEqual(scopes["school-japan-current"]["filled_distinct_patterns"], 36)
        self.assertEqual(
            scopes["school-japan-current"]["admitted_distinct_patterns"], 0
        )
        self.assertEqual(scopes["undergraduate-core-v1"]["family_count"], 101)
        self.assertEqual(
            scopes["undergraduate-core-v1"]["required_distinct_patterns"], 505
        )
        self.assertEqual(
            scopes["undergraduate-core-v1"]["filled_distinct_patterns"], 180
        )
        self.assertEqual(
            scopes["undergraduate-core-v1"]["admitted_distinct_patterns"], 0
        )
        for family in scopes["undergraduate-core-v1"]["families"][:5]:
            self.assertEqual(family["filled_distinct_patterns"], 5)
            self.assertEqual(family["mode_cells"], {"required": 5, "filled": 5})
            self.assertEqual(family["difficulty_cells"], {"required": 4, "filled": 4})
        self.assertEqual(
            scopes["advanced-commutative-algebra-v1"]["target_distinct_patterns"], 500
        )
        self.assertEqual(
            scopes["advanced-commutative-algebra-v1"]["refinement_status"], "required"
        )

        inventory = report["repository_inventory"]
        self.assertEqual(inventory["generic"]["packaged_seed"]["row_count"], 31)
        self.assertEqual(inventory["generic"]["authoring"]["unique_draft_count"], 422)
        self.assertFalse(
            inventory["generic"]["packaged_seed"]["runtime_publication_claim"]
        )
        self.assertEqual(inventory["typed"]["authoring"]["unique_draft_count"], 749)
        self.assertEqual(inventory["typed"]["authoring"]["profile_count"], 30)
        self.assertEqual(
            inventory["typed"]["loader_supported"]["unique_draft_count"], 749
        )
        self.assertEqual(inventory["typed"]["loader_supported"]["profile_count"], 30)
        self.assertEqual(inventory["database"]["status"], "not_checked")
        self.assertEqual(inventory["runtime"]["status"], "not_checked")
        self.assertFalse(report["overall_comprehensive"])
        self.assertEqual(
            len(report["findings"]["profiles_without_configured_limits"]), 38
        )

    def test_integral_extension_and_smooth_map_bindings_remain_authoring_only(self) -> None:
        families = {
            family["id"]: family
            for scope in self.matrix["scopes"]
            for family in scope.get("families", [])
        }
        integral = families["univ.algebra.integral-extension"]
        self.assertEqual(
            integral["prerequisites"],
            ["univ.algebra.rings-ideals", "univ.algebra.polynomials"],
        )
        self.assertEqual(integral["profile_requirement"], "typed_commalg_sealed")
        self.assertEqual(
            {binding["draft_id"] for binding in integral["draft_bindings"]},
            {
                "commalg_integral_add",
                "commalg_integral_base_map",
                "commalg_integral_extension_member",
                "commalg_integral_mul",
                "commalg_integral_neg",
                "commalg_integral_one",
                "commalg_integral_square",
                "commalg_integral_sub",
            },
        )
        smooth_ids = {
            "calculus_v4_norm_away_zero",
            "calculus_v4_norm_square_chain",
            "calculus_v4_smooth_composition",
            "calculus_v4_smooth_inner_product",
            "calculus_v4_smooth_squared_norm",
        }
        jacobian = families["univ.multivar.total-jacobian"]
        smooth = [
            binding
            for binding in jacobian["draft_bindings"]
            if binding["draft_id"] in smooth_ids
        ]
        self.assertEqual({binding["draft_id"] for binding in smooth}, smooth_ids)
        self.assertNotIn("univ.calculus.multivariable-jacobian", families)
        for binding in [*integral["draft_bindings"], *smooth]:
            self.assertEqual(binding["primary_mode"], "justify_prove")
            self.assertIsNone(binding["admission_manifest"])

        report = AUDIT.build_report(self.matrix, ROOT, self.sources)
        scope = next(
            scope
            for scope in report["coverage"]["scopes"]
            if scope["id"] == "undergraduate-core-v1"
        )
        family = next(
            family
            for family in scope["families"]
            if family["id"] == integral["id"]
        )
        self.assertEqual(family["mode_cells"], {"required": 5, "filled": 1})
        self.assertEqual(family["admitted_distinct_patterns"], 0)
        self.assertFalse(family["comprehensive"])
        self.assertEqual(report["findings"]["binding_source_mismatches"], [])

    def test_output_is_deterministic(self) -> None:
        first = AUDIT.build_report(self.matrix, ROOT)
        second = AUDIT.build_report(self.matrix, ROOT)
        self.assertEqual(
            json.dumps(first, ensure_ascii=False, sort_keys=True),
            json.dumps(second, ensure_ascii=False, sort_keys=True),
        )

    def test_closed_objects_and_unknown_references_fail(self) -> None:
        unknown_key = copy.deepcopy(self.matrix)
        unknown_key["unexpected"] = True
        with self.assertRaisesRegex(AUDIT.CoverageAuditError, "unknown keys"):
            AUDIT.validate_matrix(unknown_key)

        unknown_profile = copy.deepcopy(self.matrix)
        unknown_profile["scopes"][0]["families"][0]["profile_requirement"] = "missing"
        with self.assertRaisesRegex(AUDIT.CoverageAuditError, "references unknown"):
            AUDIT.validate_matrix(unknown_profile)

        duplicate_family = copy.deepcopy(self.matrix)
        duplicate_family["scopes"][0]["families"].append(
            copy.deepcopy(duplicate_family["scopes"][0]["families"][0])
        )
        with self.assertRaisesRegex(AUDIT.CoverageAuditError, "duplicate identifiers"):
            AUDIT.validate_matrix(duplicate_family)

    def test_binding_axes_and_duplicate_draft_ids_fail_closed(self) -> None:
        invalid_mode = copy.deepcopy(self.matrix)
        invalid_mode["scopes"][0]["families"][0]["draft_bindings"] = [
            {
                "draft_id": "draft.one",
                "primary_mode": "recognize",
                "difficulty": "introductory",
                "authoring_manifest": "docs/example.json",
                "admission_manifest": None,
            }
        ]
        with self.assertRaisesRegex(
            AUDIT.CoverageAuditError, "not required by its family"
        ):
            AUDIT.validate_matrix(invalid_mode)

        duplicate = copy.deepcopy(self.matrix)
        binding = {
            "draft_id": "draft.one",
            "primary_mode": "compute_construct",
            "difficulty": "introductory",
            "authoring_manifest": "docs/example.json",
            "admission_manifest": None,
        }
        duplicate["scopes"][0]["families"][0]["draft_bindings"] = [binding]
        duplicate["scopes"][0]["families"][1]["draft_bindings"] = [
            copy.deepcopy(binding)
        ]
        with self.assertRaisesRegex(AUDIT.CoverageAuditError, "duplicate identifiers"):
            AUDIT.validate_matrix(duplicate)

    def test_prerequisite_cycle_fails_closed(self) -> None:
        cyclic = copy.deepcopy(self.matrix)
        first, second = cyclic["scopes"][0]["families"][:2]
        first["prerequisites"] = [second["id"]]
        second["prerequisites"] = [first["id"]]
        with self.assertRaisesRegex(AUDIT.CoverageAuditError, "contain a cycle"):
            AUDIT.validate_matrix(cyclic)

    def test_duplicate_json_members_and_source_path_escape_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            duplicate_path = Path(directory) / "duplicate.json"
            duplicate_path.write_text('{"a":1,"a":2}', encoding="utf-8")
            with self.assertRaisesRegex(
                AUDIT.CoverageAuditError, "duplicate JSON member"
            ):
                AUDIT._read_json(duplicate_path)

        escaped = copy.deepcopy(self.sources)
        escaped["sources"][0]["path"] = "../outside.json"
        with self.assertRaisesRegex(
            AUDIT.CoverageAuditError, "escapes the repository root"
        ):
            AUDIT.validate_inventory_sources(escaped, ROOT)

    def test_profile_capacity_overflow_is_reported(self) -> None:
        constrained = copy.deepcopy(self.sources)
        constrained["profile_limits"][0]["configured_population_limit"] = 1
        constrained["profile_limits"][0]["available_population_limit"] = 1
        report = AUDIT.build_report(self.matrix, ROOT, constrained)
        self.assertEqual(
            [entry["profile_id"] for entry in report["findings"]["capacity_overflow"]],
            ["generic-v1"],
        )

    def test_database_reconciliation_keeps_authoring_and_runtime_separate(self) -> None:
        report = AUDIT.build_report(self.matrix, ROOT, self.sources)
        database = {
            "status": "checked",
            "adapter": "test-select-only",
            "legacy_generic": {
                "status": "checked",
                "relation_kind": "r",
                "row_count": 431,
            },
            "local_typed_authoring": {
                "status": "checked",
                "card_count": 163,
                "embedding_count": 163,
                "profile_count": 13,
                "manifest_count": 14,
                "authoring_statuses": {"not_admitted": 14},
            },
            "generic_runtime": {
                "status": "not_present",
                "active_generation_id": None,
                "active_row_count": None,
                "generation_count": None,
            },
            "typed_runtime": {
                "status": "not_present",
                "active_profile_count": None,
                "active_row_count": None,
            },
        }
        AUDIT.reconcile_database(report, database)
        self.assertEqual(
            report["repository_inventory"]["generic"]["observed_local_legacy"][
                "row_count"
            ],
            431,
        )
        self.assertFalse(
            report["repository_inventory"]["generic"]["observed_local_legacy"][
                "publication_claim"
            ]
        )
        self.assertEqual(report["findings"]["database_count_divergences"], [{
            "catalog": "local_typed_authoring",
            "repository_loader_supported": 749,
            "database_cards": 163,
        }])
        self.assertEqual(
            report["repository_inventory"]["database"]["generic_runtime"]["status"],
            "not_present",
        )

    def test_binding_must_match_its_declared_source_and_fills_one_pattern(self) -> None:
        bound = copy.deepcopy(self.matrix)
        family = bound["scopes"][0]["families"][0]
        family["draft_bindings"] = [
            {
                "draft_id": "coord_line_intersection_sum_difference",
                "primary_mode": "compute_construct",
                "difficulty": "introductory",
                "authoring_manifest": "docs/coordinate-geometry-candidates.json",
                "admission_manifest": None,
            }
        ]
        report = AUDIT.build_report(bound, ROOT, self.sources)
        family_report = report["coverage"]["scopes"][0]["families"][0]
        self.assertEqual(family_report["filled_distinct_patterns"], 1)
        self.assertEqual(family_report["admitted_distinct_patterns"], 0)
        self.assertEqual(report["findings"]["binding_source_mismatches"], [])

        family["draft_bindings"][0]["authoring_manifest"] = (
            "docs/local-university-math-draft-candidates.json"
        )
        mismatch = AUDIT.build_report(bound, ROOT, self.sources)
        self.assertEqual(
            mismatch["coverage"]["scopes"][0]["families"][0][
                "filled_distinct_patterns"
            ],
            0,
        )
        self.assertEqual(len(mismatch["findings"]["binding_source_mismatches"]), 1)

    def test_binding_profile_must_satisfy_family_requirement(self) -> None:
        bound = copy.deepcopy(self.matrix)
        family = bound["scopes"][0]["families"][1]
        self.assertEqual(family["profile_requirement"], "school_typed")
        family["draft_bindings"] = [
            {
                "draft_id": "coord_line_intersection_sum_difference",
                "primary_mode": "compute_construct",
                "difficulty": "introductory",
                "authoring_manifest": "docs/coordinate-geometry-candidates.json",
                "admission_manifest": None,
            }
        ]

        report = AUDIT.build_report(bound, ROOT, self.sources)

        family_report = report["coverage"]["scopes"][0]["families"][1]
        self.assertEqual(family_report["filled_distinct_patterns"], 0)
        self.assertEqual(
            report["findings"]["binding_profile_mismatches"],
            [
                {
                    "family_id": family["id"],
                    "draft_id": "coord_line_intersection_sum_difference",
                    "profile_id": "generic-v1",
                    "allowed_profile_ids": ["typed-school-math-v1"],
                }
            ],
        )

    def test_constant_and_alpha_variants_share_review_signature(self) -> None:
        first = (
            '<OMOBJ xmlns="http://www.openmath.org/OpenMath"><OMA>'
            '<OMS cd="arith1" name="plus"/><OMV name="x"/><OMI>1</OMI></OMA></OMOBJ>'
        )
        second = (
            '<OMOBJ xmlns="http://www.openmath.org/OpenMath"><OMA>'
            '<OMS cd="arith1" name="plus"/><OMV name="y"/><OMI>99</OMI></OMA></OMOBJ>'
        )
        self.assertEqual(
            AUDIT._structural_signature(first), AUDIT._structural_signature(second)
        )

    def test_json_cli_reports_same_contract(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--repository-root",
                str(ROOT),
                "--format",
                "json",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["schema_version"], AUDIT.REPORT_VERSION)
        self.assertEqual(
            payload["repository_inventory"]["database"]["status"], "not_checked"
        )

    def test_text_summary_reports_derived_coverage_counts(self) -> None:
        report = AUDIT.build_report(self.matrix, ROOT, self.sources)

        summary = AUDIT._summary(report)

        self.assertIn(
            "school-japan-current: target 321; filled 36; admitted 0", summary
        )


if __name__ == "__main__":
    unittest.main()
