"""Pure policy/aggregation tests. No API import, database, or mock database PASS."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1] / "figure-readback.py"
SPEC = importlib.util.spec_from_file_location("figure_readback", PATH)
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


class FigureReadbackPolicyTests(unittest.TestCase):
    def setUp(self):
        self.registry = {"textbook.geometry.a": "a" * 64, "textbook.geometry.b": "b" * 64}

    def test_exact_single_variants_count_matches_without_exposing_digests(self):
        observed = probe.summarize_catalog(self.registry, list(self.registry.items()))
        self.assertEqual(observed["matching_recipe_count"], 2)
        self.assertEqual(observed["missing_recipe_ids"], [])
        self.assertNotIn("a" * 64, json.dumps(observed))
        self.assertNotIn("PASS", json.dumps(observed))

    def test_missing_and_mismatched_ids_are_distinct(self):
        result = probe.summarize_catalog(self.registry, [("textbook.geometry.a", "c" * 64)])
        self.assertEqual(result["matching_recipe_count"], 0)
        self.assertEqual(result["mismatched_recipe_ids"], ["textbook.geometry.a"])
        self.assertEqual(result["missing_recipe_ids"], ["textbook.geometry.b"])

    def test_multiple_variants_are_ambiguous_even_if_one_matches(self):
        result = probe.summarize_catalog(self.registry, [
            ("textbook.geometry.a", "a" * 64), ("textbook.geometry.a", "c" * 64)])
        self.assertEqual(result["ambiguous_recipe_ids"], ["textbook.geometry.a"])
        self.assertEqual(result["matching_recipe_count"], 0)

    def test_duplicate_equal_variants_are_also_ambiguous(self):
        result = probe.summarize_catalog(self.registry, [("textbook.geometry.a", "a" * 64)] * 2)
        self.assertEqual(result["ambiguous_recipe_ids"], ["textbook.geometry.a"])

    def test_unknown_ids_invalid_digests_and_extra_columns_are_refused(self):
        for row in [("private-user-id", "a" * 64), ("textbook.geometry.a", None),
                    ("textbook.geometry.a", "A" * 64), ("textbook.geometry.a", "x"),
                    ("textbook.geometry.a", "a" * 64, "secret")]:
            with self.subTest(row=row), self.assertRaises(probe.PolicyError):
                probe.summarize_catalog(self.registry, [row])

    def test_sentinel_overflow_is_refused_not_truncated(self):
        with self.assertRaisesRegex(probe.PolicyError, "catalog_row_limit"):
            probe.summarize_catalog(self.registry, [("textbook.geometry.a", "a" * 64)] * 351)

    def test_registry_tamper_is_rejected_before_reading_rows(self):
        for raw in [b"", b"{}", b'{"figures":[]}', b"postgresql://user:secret@private-host/db"]:
            with self.subTest(raw=raw), self.assertRaisesRegex(probe.PolicyError, "registry_hash_mismatch"):
                probe.registry_entries(raw)

    def test_answer_counts_require_nonnegative_ordered_int64_integers(self):
        self.assertEqual(probe.summarize_answers((10, 3))["object_visualization_answer_count"], 3)
        for row in [(3, 4), (-1, 0), (True, 0), (0, False), (2**63, 0), (1,), None, (1, "1")]:
            with self.subTest(row=row), self.assertRaises(probe.PolicyError):
                probe.summarize_answers(row)

    def test_canonical_module_counters_are_not_an_existing_pool(self):
        probe.require_fresh_pools({"module": {"nested_fallbacks": 0, "closed_fallbacks": 0, "exhausted": 0}})
        for stats in [{}, None, {"module": {}, "postgresql://user:secret@private/db": {}}]:
            with self.subTest(stats=stats), self.assertRaisesRegex(probe.PolicyError, "existing_process_pools_refused"):
                probe.require_fresh_pools(stats)

    def test_failure_output_is_closed_and_never_echoes_arbitrary_reason(self):
        secret = "postgresql://user:password@private-host/db"
        result = probe.unavailable(secret)
        self.assertEqual(result, {"status": "NOT_VERIFIED", "reason": "runtime_unavailable"})
        self.assertNotIn(secret, json.dumps(result))
        self.assertEqual(probe._reason(ValueError(secret), "catalog_read_unavailable"), "catalog_read_unavailable")

    def test_all_cli_arguments_are_rejected_without_importing_api_or_echoing_input(self):
        secret = "postgresql://user:password@private-host/db"
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = probe.main(["--url", secret])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(out.getvalue()), {"status": "NOT_VERIFIED", "reason": "arguments_refused"})
        self.assertNotIn(secret, out.getvalue())


if __name__ == "__main__":
    unittest.main()
