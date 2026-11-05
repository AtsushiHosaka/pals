"""Regression checks for corrupt evidence entering charts; no model or network calls."""
from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from audit_ledger import FIELDS, audit


class LedgerAuditTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "ledger.csv"
        self.row = dict.fromkeys(FIELDS, "")
        self.row.update(id="2026-11-04-check", date="2026-11-04", family="proof_generation",
                        experiment="fixed-suite", n="3", successes="2", success_rate="0.6667",
                        source="docs/measurement.md@0123456", source_type="doc")

    def check_rows(self, *rows):
        with self.path.open("w", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(target, FIELDS)
            writer.writeheader()
            writer.writerows(rows or [self.row])
        return audit(self.path)

    def test_repository_ledger_passes_and_unknowns_are_not_zero_filled(self):
        result = audit()
        self.assertEqual(result["errors"], [])
        self.assertGreater(result["missing_fields"]["cost_usd"], 0)

    def test_source_annotations_and_rounded_rate_are_preserved(self):
        self.row.update(failures_raw_json='{"unmeasured":null,"ratio":"2/3"}')
        result = self.check_rows()
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["missing_fields"]["cost_usd"], 1)

    def test_negative_fractional_and_nonfinite_values_are_rejected(self):
        for field, value in [("n", "-1"), ("successes", "0.5"), ("cost_usd", "Infinity"),
                             ("latency_p50_s", "NaN"), ("success_rate", "1.1")]:
            with self.subTest(field=field, value=value):
                row = self.row | {field: value}
                self.assertTrue(self.check_rows(row)["errors"])

    def test_successes_denominator_and_percentiles_are_checked(self):
        for delta in [{"successes": "4"}, {"success_rate": "0.5"},
                      {"latency_p50_s": "10", "latency_p95_s": "9"}]:
            with self.subTest(delta=delta):
                self.assertTrue(self.check_rows(self.row | delta)["errors"])

    def test_normalized_failures_require_integer_counts_and_known_codes(self):
        for value in ['{"model.could_not_prove":-1}', '{"model.could_not_prove":true}',
                      '{"model.could_not_prove":0.5}', '{"unknown.code":1}', '[]',
                      '{"model.could_not_prove":1,"model.could_not_prove":2}',
                      '{"model.could_not_prove":NaN}', '{not JSON}']:
            with self.subTest(value=value):
                self.assertTrue(self.check_rows(self.row | {"failures_json": value})["errors"])

    def test_missing_source_duplicate_id_and_bad_overlap_are_rejected(self):
        self.assertTrue(self.check_rows(self.row | {"source": " "})["errors"])
        self.assertTrue(self.check_rows(self.row, self.row)["errors"])
        for overlap in ["absent", self.row["id"]]:
            self.assertTrue(self.check_rows(self.row | {"overlap_with": overlap})["errors"])

    def test_date_and_enumerations_are_checked(self):
        for field, value in [("date", "2026-02-30"), ("family", "accuracy"),
                             ("source_type", "email"), ("environment", "production")]:
            with self.subTest(field=field):
                self.assertTrue(self.check_rows(self.row | {field: value})["errors"])

    def test_truncated_row_and_duplicate_header_are_rejected(self):
        self.path.write_text(",".join(FIELDS) + "\n2026-11-04-short\n", encoding="utf-8")
        self.assertTrue(audit(self.path)["errors"])
        self.path.write_text(",".join(FIELDS + ("id",)) + "\n", encoding="utf-8")
        self.assertTrue(audit(self.path)["errors"])


if __name__ == "__main__":
    unittest.main()
