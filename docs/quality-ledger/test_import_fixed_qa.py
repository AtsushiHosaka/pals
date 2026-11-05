"""Synthetic private evidence exercises the real importer, without models or a database."""

from __future__ import annotations

import base64
import contextlib
import csv
import datetime as dt
import io
import json
import tempfile
import unittest
from pathlib import Path

import import_fixed_qa as qa


class FixedQaImportTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.evidence = self.root / "private"
        self.evidence.mkdir(mode=0o700)
        self.build(modern=True)

    def write(self, name, value):
        raw = json.dumps(value, ensure_ascii=False).encode()
        p = self.evidence / name
        p.write_bytes(raw)
        p.chmod(0o600)
        return qa.digest(raw)

    def read(self, name):
        return json.loads((self.evidence / name).read_bytes())

    def build(self, modern):
        self.modern = modern
        source = b'raise AssertionError("Importer must never execute private Python")\n'
        for name in ["baseline.py", "candidate.py", "benchmark.py"]:
            p = self.evidence / name
            p.write_bytes(source)
            p.chmod(0o600)
        schema = (
            "pals.semantic-priority-qa-repeat.v1"
            if modern
            else "pals.grounded-rationale-qa-repeat.v1"
        )
        inputs = []
        for name in qa.INPUTS:
            saved = self.write(name + ".json", {"private_input": "DO_NOT_EXPORT_INPUT"})
            inputs.append(
                {
                    "id": name,
                    "saved_sha256": saved,
                    "question_sha256": "a" * 64,
                    "lean_sha256": "b" * 64,
                    "prompt_sha256": {a: "c" * 64 for a in qa.ARMS},
                }
            )
        order = [
            {"input_id": name, "arm": arm, "repeat": repeat}
            for name in qa.INPUTS
            for arm in qa.ARMS
            for repeat in (1, 2, 3)
        ]
        pre = {
            "schema_version": schema,
            "created_at_utc": "2026-11-05T00:00:00+00:00",
            "provider": "openai",
            "model": "gpt-6-luna",
            "reasoning_effort": "low",
            "max_output_tokens": 6000,
            "max_input_bytes": 80000,
            "timeout_seconds": 55,
            "max_attempts": 1,
            "planned_calls": 24,
            "hard_call_cap": 24,
            "cost_cap_usd": 1,
            "price_usd_per_million": {"all_input": 0.25, "output": 0.5},
            "baseline_commit": "1" * 40,
            "candidate_commit": "2" * 40,
            "source_sha256": {a: qa.digest(source) for a in qa.ARMS},
            "harness_sha256": qa.digest(source),
            "corpus_sha256": "d" * 64,
            "inputs": inputs,
            "order": order,
        }
        self.write("predeclaration.json", pre)
        outcomes, scores = [], []
        for index, task in enumerate(order):
            positive = task["input_id"].endswith("positive")
            decision = "approved" if positive else "rejected"
            rationale = "DO_NOT_EXPORT_RESPONSE"
            usage = {
                "schema_version": "pals.proof-job-usage.v1",
                "call_id": f"secret-call-{index}",
                "provider": "openai",
                "model": "gpt-6-luna",
                "input_tokens": 100,
                "output_tokens": 20,
                "cached_input_tokens": 20,
                "reasoning_output_tokens": 2,
                "price_snapshot_id": "fixture-snapshot",
                "provider_request_id": f"secret-resp-{index}",
            }
            started = dt.datetime(2026, 11, 5, 0, 1, index, tzinfo=dt.UTC)
            outcomes.append(
                dict(
                    task,
                    started_at_utc=started.isoformat(),
                    finished_at_utc=(started + dt.timedelta(seconds=0.5)).isoformat(),
                    elapsed_seconds=0.5,
                    decision=decision,
                    usage=[usage],
                    provider_calls=1,
                    usage_missing=False,
                    conservative_cost_usd=0.000035,
                )
            )
            response = {
                "id": usage["provider_request_id"],
                "status": "completed",
                "model": "gpt-6-luna",
                "reasoning": {"effort": "low"},
                "max_output_tokens": 6000,
                "service_tier": "default",
                "store": False,
                "usage": {
                    "input_tokens": 100,
                    "output_tokens": 20,
                    "input_tokens_details": {
                        "cached_tokens": 20,
                        "cache_write_tokens": 30,
                    },
                    "output_tokens_details": {"reasoning_tokens": 2},
                },
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": json.dumps(
                                    {"approved": positive, "rationale": rationale}
                                ),
                            }
                        ],
                    }
                ],
            }
            self.write_response(index, response)
            review_sha = self.write(f"review-{index}.json", {"rationale": rationale})
            score = dict(
                outcome_index=index,
                **task,
                expected_decision=decision,
                actual_decision=decision,
                strict_semantic_success=True,
                semantic_reason="correct_positive_approval"
                if positive
                else "correct_intended_defect_rejection",
                criticism_present=not positive,
                rationale_source=f"review-{index}.json",
            )
            if modern:
                score.update(
                    criticism_evidence_form_complete=None if positive else True,
                    all_verdict_conclusion_evidence_complete=True,
                    rationale_sha256=review_sha,
                    provider_response_verdict_rationale_roundtrip=True,
                )
            else:
                score["evidence_form_complete"] = None if positive else True
            scores.append(score)
        self.write("outcomes.json", outcomes)
        adj = {
            "basis": "Explicitly human adjudicated synthetic fixture; not a model evaluation",
            "scores": scores,
        }
        if modern:
            adj.update(schema_version="pals.qa-semantic-priority-adjudication.v1")
        self.write("adjudication.json", adj)
        self.refresh_bindings()

    def write_response(self, index, response):
        envelope = {
            "http_status": 200,
            "elapsed_seconds": 0.125,
            "body_base64": base64.b64encode(json.dumps(response).encode()).decode(),
        }
        raw_sha = self.write(f"provider-{index + 1}-raw.json", envelope)
        self.write(
            f"provider-{index + 1}.json",
            dict(
                envelope,
                parse_status="json",
                response=response,
                raw_envelope_sha256=raw_sha,
            ),
        )

    def refresh_bindings(self):
        if self.modern:
            adj = self.read("adjudication.json")
            adj.update(
                prereg_sha256=qa.digest(
                    (self.evidence / "predeclaration.json").read_bytes()
                ),
                outcomes_sha256=qa.digest(
                    (self.evidence / "outcomes.json").read_bytes()
                ),
            )
            self.write("adjudication.json", adj)

    def options(self):
        self.refresh_bindings()
        cohort = qa.PROFILES[self.read("predeclaration.json")["schema_version"]][0]
        return {
            "prereg_sha256": qa.digest(
                (self.evidence / "predeclaration.json").read_bytes()
            ),
            "outcomes_sha256": qa.digest(
                (self.evidence / "outcomes.json").read_bytes()
            ),
            "adjudication_sha256": qa.digest(
                (self.evidence / "adjudication.json").read_bytes()
            ),
            "human_confirmed": True,
            "environment": "local macOS",
            "report_url": f"https://github.com/AtsushiHosaka/pals-agent/blob/{'1' * 40}/testdata/{cohort}/README.md",
            "pr_url": "https://github.com/AtsushiHosaka/pals-agent/pull/53",
        }

    def rows(self):
        return qa.generate(self.evidence, **self.options())

    def argv(self):
        options = self.options()
        result = [
            "--private-dir",
            str(self.evidence),
            "--confirm-human-adjudication",
            "--environment",
            "local macOS",
            "--source-report",
            options["report_url"],
            "--source-pr",
            options["pr_url"],
        ]
        for name in ("prereg", "outcomes", "adjudication"):
            result += [f"--{name}-sha256", options[name + "_sha256"]]
        return result

    def test_both_schemas_generate_eight_rows_without_private_text_or_ids(self):
        for modern in (False, True):
            self.build(modern)
            rows = self.rows()
            self.assertEqual(len(rows), 8)
            self.assertEqual(len({r["id"] for r in rows}), 8)
            self.assertEqual(list(rows[0]), list(qa.FIELDS))
            self.assertEqual(rows[0]["n"], "3")
            self.assertEqual(rows[0]["cost_usd"], "0.00010500")
            self.assertEqual(rows[0]["latency_p50_s"], "")
            for canary in ("DO_NOT_EXPORT", "secret-call", "secret-resp"):
                self.assertNotIn(canary, qa.csv_bytes(rows).decode())

    def test_input_and_source_tampering_fail_even_with_other_files_valid(self):
        for name in (qa.INPUTS[0] + ".json", "candidate.py", "benchmark.py"):
            with self.subTest(name=name):
                raw = (self.evidence / name).read_bytes()
                (self.evidence / name).write_bytes(raw + b" ")
                with self.assertRaises(qa.EvidenceError):
                    self.rows()
                (self.evidence / name).write_bytes(raw)

    def test_bad_manual_scoring_and_missing_human_confirmation_fail(self):
        with self.assertRaisesRegex(qa.EvidenceError, "human_adjudication"):
            qa.generate(self.evidence, **(self.options() | {"human_confirmed": False}))
        adj = self.read("adjudication.json")
        adj["scores"][0]["strict_semantic_success"] = "true"
        self.write("adjudication.json", adj)
        with self.assertRaisesRegex(qa.EvidenceError, "manual_score"):
            self.rows()

    def test_unknown_reason_and_wrong_verdict_are_not_automatically_rescored(self):
        adj = self.read("adjudication.json")
        adj["scores"][0]["semantic_reason"] = "novel_human_category"
        self.write("adjudication.json", adj)
        with self.assertRaisesRegex(qa.EvidenceError, "manual_score_reason"):
            self.rows()

    def test_missing_usage_is_rejected_and_not_zero_filled(self):
        outcomes = self.read("outcomes.json")
        outcomes[0].update(usage=[], usage_missing=True)
        self.write("outcomes.json", outcomes)
        with self.assertRaisesRegex(qa.EvidenceError, "missing_usage"):
            self.rows()

    def test_duplicate_calls_schedule_and_excess_provider_file_are_rejected(self):
        outcomes = self.read("outcomes.json")
        outcomes[1]["usage"][0]["call_id"] = outcomes[0]["usage"][0]["call_id"]
        self.write("outcomes.json", outcomes)
        with self.assertRaisesRegex(qa.EvidenceError, "duplicate_or_missing_call"):
            self.rows()
        self.build(True)
        self.write("provider-25-raw.json", {})
        with self.assertRaisesRegex(qa.EvidenceError, "unexpected_provider_call"):
            self.rows()

    def test_missing_raw_usage_and_wrong_provider_settings_fail_without_disclosure(
        self,
    ):
        response = self.read("provider-1.json")["response"]
        del response["usage"]["input_tokens_details"]["cache_write_tokens"]
        self.write_response(0, response)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = qa.main(self.argv() + ["--dry-run"])
        self.assertEqual(code, 2)
        self.assertNotIn("DO_NOT_EXPORT", output.getvalue())
        self.build(True)
        response = self.read("provider-1.json")["response"]
        response["reasoning"]["effort"] = "high"
        self.write_response(0, response)
        with self.assertRaisesRegex(qa.EvidenceError, "response_settings"):
            self.rows()

    def test_all_fields_comparison_and_existing_id_dedup_are_distinct(self):
        rows = self.rows()
        reference = self.root / "reference.csv"
        reference.write_bytes(qa.csv_bytes(rows))
        qa.compare(rows, reference)
        with self.assertRaisesRegex(qa.EvidenceError, "duplicate_existing_ledger_id"):
            qa.compare(rows, reference, dedupe=True)
        changed = [r.copy() for r in rows]
        changed[0]["notes"] += " different"
        reference.write_bytes(qa.csv_bytes(changed))
        with self.assertRaisesRegex(qa.EvidenceError, "ledger_field_mismatch"):
            qa.compare(rows, reference)

    def test_dry_run_output_exclusive_and_symlink_never_append_or_overwrite(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(qa.main(self.argv() + ["--dry-run"]), 0)
        proposal = self.root / "proposal.csv"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(qa.main(self.argv() + ["--output", str(proposal)]), 0)
        with proposal.open(newline="") as stream:
            self.assertEqual(len(list(csv.DictReader(stream))), 8)
        before = proposal.read_bytes()
        for path in (proposal, self.root / "link.csv"):
            if path != proposal:
                path.symlink_to(proposal)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(qa.main(self.argv() + ["--output", str(path)]), 2)
            self.assertEqual(proposal.read_bytes(), before)

    def test_cap_schedule_and_manual_identity_tampering_are_rejected(self):
        pre = self.read("predeclaration.json")
        pre["hard_call_cap"] = 25
        self.write("predeclaration.json", pre)
        with self.assertRaisesRegex(qa.EvidenceError, "call_cap"):
            self.rows()
        self.build(True)
        pre = self.read("predeclaration.json")
        pre["order"][1] = pre["order"][0]
        self.write("predeclaration.json", pre)
        with self.assertRaisesRegex(qa.EvidenceError, "schedule"):
            self.rows()
        self.build(True)
        adj = self.read("adjudication.json")
        adj["scores"][0]["arm"] = "candidate"
        self.write("adjudication.json", adj)
        with self.assertRaisesRegex(qa.EvidenceError, "manual_score_binding"):
            self.rows()

    def test_unknown_schema_source_controls_and_public_private_files_fail(self):
        options = self.options()
        pre = self.read("predeclaration.json")
        pre["schema_version"] = "unknown.schema"
        options["prereg_sha256"] = self.write("predeclaration.json", pre)
        with self.assertRaisesRegex(qa.EvidenceError, "unsupported_preregistration"):
            qa.generate(self.evidence, **options)
        self.build(True)
        options = self.options()
        options["report_url"] = "\n" + options["report_url"]
        with self.assertRaisesRegex(qa.EvidenceError, "noncanonical_public_source"):
            qa.generate(self.evidence, **options)
        (self.evidence / "baseline.py").chmod(0o644)
        with self.assertRaisesRegex(qa.EvidenceError, "evidence_not_private"):
            self.rows()

    def test_boolean_provider_usage_and_duplicate_json_are_rejected(self):
        outcomes = self.read("outcomes.json")
        outcomes[0]["usage"][0]["cached_input_tokens"] = 0
        self.write("outcomes.json", outcomes)
        response = self.read("provider-1.json")["response"]
        response["usage"]["input_tokens_details"]["cached_tokens"] = False
        self.write_response(0, response)
        with self.assertRaisesRegex(qa.EvidenceError, "invalid_usage_integer"):
            self.rows()
        with self.assertRaisesRegex(qa.EvidenceError, "duplicate_json_key"):
            qa.decode(b'{"success":true,"success":false}')


if __name__ == "__main__":
    unittest.main()
