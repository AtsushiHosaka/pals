#!/usr/bin/env python3
"""Validate private fixed-QA evidence and propose eight public ledger rows. Never append."""

from __future__ import annotations

import argparse
import base64
import csv
import datetime as dt
import hashlib
import io
import json
import math
import os
import re
import stat
import tempfile
from collections import Counter
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from audit_ledger import FIELDS, audit

INPUTS = (
    "coprime-positive",
    "energy-positive",
    "coprime-missing-result",
    "energy-unsupported-bridge",
)
ARMS = ("baseline", "candidate")
PROFILES = {
    "pals.grounded-rationale-qa-repeat.v1": (
        "qa-grounded-rationale-v1",
        "Grounded QA rationale comparison",
        False,
    ),
    "pals.semantic-priority-qa-repeat.v1": (
        "qa-semantic-priority-v1",
        "Semantic-priority QA comparison",
        True,
    ),
}
SUCCESS_REASONS = {
    "correct_positive_approval",
    "correct_intended_defect_rejection",
    "correct_missing_result_rejection",
    "correct_unsupported_bridge_rejection",
}
FAILURE_REASONS = {
    "approved_missing_conclusion": "review.explanation_false_accept",
    "invented_missing_source_lines": "review.unsupported_rationale",
    "misapplied_squaring_vs_distributivity_objection": "review.unsupported_rationale",
    "unfounded_dependency_as_duplication": "review.unsupported_rationale",
    "unsupported_missing_header_accusation": "review.unsupported_rationale",
    "over_rejection": "review.rejected",
}


class EvidenceError(ValueError):
    """Messages are fixed codes; never include private evidence values."""


def require(ok: bool, code: str) -> None:
    if not ok:
        raise EvidenceError(code)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def integer(value: Any) -> int:
    require(
        type(value) is int and 0 <= value <= 9_007_199_254_740_991,
        "invalid_usage_integer",
    )
    return value


def number(value: Any) -> float:
    require(
        type(value) in (int, float) and math.isfinite(value) and value >= 0,
        "invalid_finite_measurement",
    )
    return float(value)


def moment(value: Any) -> dt.datetime:
    require(isinstance(value, str), "invalid_timestamp")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EvidenceError("invalid_timestamp") from exc
    require(parsed.utcoffset() == dt.timedelta(0), "timestamp_requires_utc")
    return parsed


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, "duplicate_json_key")
        result[key] = value
    return result


def decode(raw: bytes) -> Any:
    def invalid(_: str) -> None:
        raise EvidenceError("nonfinite_json")

    return json.loads(raw, object_pairs_hook=unique_object, parse_constant=invalid)


def private_bytes(directory: Path, name: str) -> bytes:
    require(re.fullmatch(r"[A-Za-z0-9_.-]+", name) is not None, "unsafe_evidence_name")
    p = directory / name
    info = p.lstat()
    require(
        stat.S_ISREG(info.st_mode) and not p.is_symlink(), "nonregular_private_evidence"
    )
    require(
        info.st_mode & 0o077 == 0 and info.st_uid == os.getuid(), "evidence_not_private"
    )
    require(info.st_size <= 2_000_000, "evidence_too_large")
    return p.read_bytes()


def source_urls(report: str, pr: str, cohort: str) -> str:
    r, p = urlsplit(report), urlsplit(pr)
    require(report == r.geturl() and pr == p.geturl(), "noncanonical_public_source")
    require(
        r.scheme == p.scheme == "https"
        and r.netloc == p.netloc == "github.com"
        and not any((r.query, r.fragment, p.query, p.fragment)),
        "invalid_public_source",
    )
    require(
        re.fullmatch(
            rf"/AtsushiHosaka/pals-agent/blob/[0-9a-f]{{40}}/testdata/"
            rf"{re.escape(cohort)}/README\.md",
            r.path,
        )
        is not None
        and re.fullmatch(r"/AtsushiHosaka/pals-agent/pull/[1-9][0-9]*", p.path)
        is not None,
        "source_requires_immutable_report_and_pr",
    )
    return pr + ";" + report


def generate(
    directory: Path,
    *,
    prereg_sha256: str,
    outcomes_sha256: str,
    adjudication_sha256: str,
    human_confirmed: bool,
    report_url: str,
    pr_url: str,
    environment: str,
) -> list[dict[str, str]]:
    require(human_confirmed, "human_adjudication_confirmation_required")
    require(environment == "local macOS", "unsupported_environment")
    info = directory.lstat()
    require(
        stat.S_ISDIR(info.st_mode)
        and not directory.is_symlink()
        and info.st_mode & 0o077 == 0
        and info.st_uid == os.getuid(),
        "directory_not_private",
    )
    values = []
    for name, expected in (
        ("predeclaration.json", prereg_sha256),
        ("outcomes.json", outcomes_sha256),
        ("adjudication.json", adjudication_sha256),
    ):
        raw = private_bytes(directory, name)
        require(sha(expected) and digest(raw) == expected, "evidence_hash_mismatch")
        values.append(decode(raw))
    pre, outcomes, adjudication = values
    require(
        isinstance(pre, dict) and pre.get("schema_version") in PROFILES,
        "unsupported_preregistration_schema",
    )
    cohort, title, modern = PROFILES[pre["schema_version"]]
    source = source_urls(report_url, pr_url, cohort)
    require(
        pre["provider"] == "openai"
        and pre["model"] == "gpt-6-luna"
        and pre["reasoning_effort"] == "low"
        and pre["max_output_tokens"] == 6000
        and pre["max_attempts"] == 1
        and type(pre["max_attempts"]) is int
        and pre["max_input_bytes"] == 80000
        and pre["timeout_seconds"] == 55
        and pre["planned_calls"] == pre["hard_call_cap"] == 24
        and pre["price_usd_per_million"] == {"all_input": 0.25, "output": 0.5},
        "unsupported_settings_or_call_cap",
    )
    require(
        sha(pre["harness_sha256"])
        and digest(private_bytes(directory, "benchmark.py")) == pre["harness_sha256"],
        "harness_hash_mismatch",
    )
    for arm in ARMS:
        require(
            sha(pre["source_sha256"][arm])
            and digest(private_bytes(directory, arm + ".py"))
            == pre["source_sha256"][arm]
            and re.fullmatch(r"[0-9a-f]{40}", pre[arm + "_commit"]) is not None,
            "source_hash_mismatch",
        )
    require(
        sha(pre["corpus_sha256"]) and len(pre["inputs"]) == 4, "invalid_fixed_inputs"
    )
    require([x["id"] for x in pre["inputs"]] == list(INPUTS), "unexpected_input_matrix")
    for item in pre["inputs"]:
        require(
            digest(private_bytes(directory, item["id"] + ".json"))
            == item["saved_sha256"],
            "fixed_input_hash_mismatch",
        )
        require(
            all(
                sha(item[k]) for k in ("saved_sha256", "question_sha256", "lean_sha256")
            )
            and set(item["prompt_sha256"]) == set(ARMS)
            and all(sha(v) for v in item["prompt_sha256"].values()),
            "invalid_input_pins",
        )
    require(
        isinstance(outcomes, list) and len(outcomes) == len(pre["order"]) == 24,
        "incomplete_or_excess_calls",
    )
    schedule = [(r["input_id"], r["arm"], r["repeat"]) for r in pre["order"]]
    require(
        set(schedule) == {(i, a, n) for i in INPUTS for a in ARMS for n in (1, 2, 3)}
        and len(set(schedule)) == 24,
        "duplicate_or_invalid_schedule",
    )
    require(
        isinstance(adjudication, dict)
        and isinstance(adjudication.get("basis"), str)
        and bool(adjudication["basis"].strip())
        and len(adjudication["scores"]) == 24,
        "incomplete_manual_adjudication",
    )
    if modern:
        require(
            adjudication["schema_version"]
            == "pals.qa-semantic-priority-adjudication.v1"
            and adjudication["prereg_sha256"] == prereg_sha256
            and adjudication["outcomes_sha256"] == outcomes_sha256,
            "adjudication_binding_mismatch",
        )
    expected_files = set(range(1, 25))
    reserved = {
        int(m[1])
        for p in directory.iterdir()
        if (m := re.fullmatch(r"call-([0-9]+)-reserved\.json", p.name))
    }
    require(reserved == expected_files, "unexpected_attempt_reservations")
    for suffix in ("-raw.json", ".json"):
        found = {
            int(m[1])
            for p in directory.iterdir()
            if (m := re.fullmatch(r"provider-([0-9]+)" + re.escape(suffix), p.name))
        }
        require(found == expected_files, "unexpected_provider_call_files")
    seen_calls: set[str] = set()
    seen_responses: set[str] = set()
    price_snapshots: set[str] = set()
    cells: dict[tuple[str, str], list[dict[str, Any]]] = {}
    created = moment(pre["created_at_utc"])
    dates: set[str] = set()
    for index, (row, score) in enumerate(
        zip(outcomes, adjudication["scores"], strict=True)
    ):
        identity = (row["input_id"], row["arm"], row["repeat"])
        require(
            identity == schedule[index] and type(row["repeat"]) is int,
            "outcome_order_or_identity_mismatch",
        )
        start, finish = moment(row["started_at_utc"]), moment(row["finished_at_utc"])
        require(created <= start <= finish, "invalid_call_chronology")
        reservation = decode(
            private_bytes(directory, f"call-{index + 1}-reserved.json")
        )
        require(
            sha(reservation["payload_sha256"])
            and start <= moment(reservation["utc"]) <= finish,
            "invalid_attempt_reservation",
        )
        dates.add(start.date().isoformat())
        wall = number(row["elapsed_seconds"])
        require(
            row["provider_calls"] == 1
            and type(row["provider_calls"]) is int
            and row["usage_missing"] is False
            and len(row["usage"]) == 1,
            "missing_usage_or_retry",
        )
        usage = row["usage"][0]
        require(
            usage["schema_version"] == "pals.proof-job-usage.v1"
            and usage["provider"] == pre["provider"]
            and usage["model"] == pre["model"],
            "usage_settings_mismatch",
        )
        for k, seen in (
            ("call_id", seen_calls),
            ("provider_request_id", seen_responses),
        ):
            require(
                isinstance(usage[k], str) and bool(usage[k]) and usage[k] not in seen,
                "duplicate_or_missing_call_identity",
            )
            seen.add(usage[k])
        require(
            isinstance(usage["price_snapshot_id"], str)
            and bool(usage["price_snapshot_id"]),
            "missing_price_snapshot",
        )
        price_snapshots.add(usage["price_snapshot_id"])
        raw_bytes = private_bytes(directory, f"provider-{index + 1}-raw.json")
        envelope = decode(raw_bytes)
        require(envelope["http_status"] == 200, "provider_http_failure")
        response = decode(base64.b64decode(envelope["body_base64"], validate=True))
        parsed = decode(private_bytes(directory, f"provider-{index + 1}.json"))
        require(
            parsed["raw_envelope_sha256"] == digest(raw_bytes)
            and parsed["response"] == response
            and parsed["parse_status"] == "json"
            and parsed["body_base64"] == envelope["body_base64"],
            "raw_response_mismatch",
        )
        require(
            response["id"] == usage["provider_request_id"]
            and response["status"] == "completed"
            and response["model"] == pre["model"]
            and response["reasoning"]["effort"] == pre["reasoning_effort"]
            and response["max_output_tokens"] == pre["max_output_tokens"]
            and response["service_tier"] == "default"
            and response.get("prompt_cache_retention") == "24h"
            and response["store"] is False,
            "response_settings_mismatch",
        )
        actual = response["usage"]
        counts = {
            k: integer(usage[k])
            for k in (
                "input_tokens",
                "output_tokens",
                "cached_input_tokens",
                "reasoning_output_tokens",
            )
        }
        require(
            tuple(
                integer(v)
                for v in (
                    actual["input_tokens"],
                    actual["output_tokens"],
                    actual["input_tokens_details"]["cached_tokens"],
                    actual["output_tokens_details"]["reasoning_tokens"],
                )
            )
            == tuple(counts.values()),
            "response_usage_mismatch",
        )
        writes = integer(actual["input_tokens_details"]["cache_write_tokens"])
        require(
            counts["cached_input_tokens"] + writes <= counts["input_tokens"]
            and counts["reasoning_output_tokens"] <= counts["output_tokens"]
            and counts["output_tokens"] <= pre["max_output_tokens"],
            "usage_components_exceed_total",
        )
        reserve = (
            Decimal(counts["input_tokens"]) * Decimal(".25")
            + Decimal(counts["output_tokens"]) * Decimal(".5")
        ) / 1_000_000
        require(
            abs(Decimal(str(number(row["conservative_cost_usd"]))) - reserve)
            <= Decimal("1e-12"),
            "reserve_estimate_mismatch",
        )
        expected = "approved" if identity[0].endswith("positive") else "rejected"
        require(
            row["decision"] in {"approved", "rejected"}
            and score["outcome_index"] == index
            and type(score["outcome_index"]) is int
            and (score["input_id"], score["arm"], score["repeat"]) == identity
            and score["actual_decision"] == row["decision"]
            and score["expected_decision"] == expected
            and type(score["strict_semantic_success"]) is bool,
            "invalid_manual_score_binding",
        )
        reason, success = score["semantic_reason"], score["strict_semantic_success"]
        require(
            (success and reason in SUCCESS_REASONS and row["decision"] == expected)
            or (not success and reason in FAILURE_REASONS),
            "invalid_manual_score_reason",
        )
        require(
            not success
            or (reason == "correct_positive_approval") == (expected == "approved"),
            "manual_reason_verdict_conflict",
        )
        require(
            reason != "approved_missing_conclusion"
            or (expected == "rejected" and row["decision"] == "approved"),
            "manual_reason_verdict_conflict",
        )
        require(
            reason != "over_rejection"
            or (expected == "approved" and row["decision"] == "rejected"),
            "manual_reason_verdict_conflict",
        )
        require(
            success
            or reason in {"approved_missing_conclusion", "over_rejection"}
            or row["decision"] == "rejected",
            "manual_reason_verdict_conflict",
        )
        criticism = row["decision"] == "rejected"
        require(
            score["criticism_present"] is criticism, "invalid_criticism_denominator"
        )
        form = score[
            "criticism_evidence_form_complete" if modern else "evidence_form_complete"
        ]
        require(
            type(form) is bool if criticism else form is None, "invalid_evidence_na"
        )
        if modern:
            require(
                type(score["all_verdict_conclusion_evidence_complete"]) is bool
                and score["provider_response_verdict_rationale_roundtrip"] is True,
                "invalid_manual_evidence_score",
            )
        require(
            score["rationale_source"] == f"review-{index}.json",
            "invalid_rationale_binding",
        )
        review_bytes = private_bytes(directory, f"review-{index}.json")
        review = decode(review_bytes)
        texts = [
            c["text"]
            for m in response["output"]
            if m.get("type") == "message"
            for c in m.get("content", [])
            if c.get("type") == "output_text"
        ]
        require(len(texts) == 1, "ambiguous_provider_verdict")
        fact = decode(texts[0].encode())
        require(
            fact["approved"] is (row["decision"] == "approved")
            and isinstance(review["rationale"], str)
            and fact["rationale"] == review["rationale"],
            "provider_verdict_roundtrip_mismatch",
        )
        if modern:
            require(
                score["rationale_sha256"] == digest(review_bytes),
                "rationale_hash_mismatch",
            )
        cells.setdefault(identity[:2], []).append(
            {
                "score": score,
                "counts": counts,
                "writes": writes,
                "wall": wall,
                "http": number(envelope["elapsed_seconds"]),
                "reserve": reserve,
            }
        )
    require(len(price_snapshots) == len(dates) == 1, "mixed_snapshot_or_execution_date")
    require(
        sum(x["reserve"] for c in cells.values() for x in c)
        <= Decimal(str(number(pre["cost_cap_usd"]))),
        "recorded_cost_exceeds_cap",
    )
    result = []
    for input_id in INPUTS:
        for arm in ARMS:
            selected = cells[(input_id, arm)]
            require(len(selected) == 3, "incomplete_cell")
            scores = [x["score"] for x in selected]
            successes = sum(s["strict_semantic_success"] for s in scores)
            raw_failures = Counter(
                s["semantic_reason"] for s in scores if not s["strict_semantic_success"]
            )
            failures = Counter()
            for reason, count in raw_failures.items():
                failures[FAILURE_REASONS[reason]] += count
            approvals = sum(s["actual_decision"] == "approved" for s in scores)
            criticisms = sum(s["criticism_present"] for s in scores)
            complete = sum(
                s[
                    "criticism_evidence_form_complete"
                    if modern
                    else "evidence_form_complete"
                ]
                is True
                for s in scores
            )
            form_text = (
                f"{complete}/{criticisms}"
                if criticisms
                else ("NA(no criticism)" if modern else "NA(no rejection)")
            )
            totals = {
                k: sum(x["counts"][k] for x in selected) for k in selected[0]["counts"]
            }
            row = dict.fromkeys(FIELDS, "")
            row.update(
                id=f"{next(iter(dates))}-{cohort.removesuffix('-v1')}-{input_id}-{arm}",
                date=next(iter(dates)),
                family="other",
                experiment=f"{title}: {input_id}",
                model_config=f"{pre['model']} / low / max_output=6000 / sha256:"
                + pre["source_sha256"][arm][:8],
                dataset=f"{cohort}; {input_id}; one fixed explanation x3",
                n="3",
                successes=str(successes),
                success_rate=str(successes / 3),
                failures_json=json.dumps(failures) if failures else "",
                failures_raw_json=json.dumps(raw_failures) if raw_failures else "",
                cost_usd=f"{sum(x['reserve'] for x in selected):.8f}",
                latency_other=f"QA wall sum={sum(x['wall'] for x in selected):.9f}s; "
                f"HTTP sum={sum(x['http'] for x in selected):.9f}s",
                environment=environment,
                source=source,
                source_type="pr_agent",
            )
            common = "3 QA requests on ONE identical fixed saved explanation; not 3 problems/generation pipelines. "
            if modern:
                evidence = sum(
                    s["all_verdict_conclusion_evidence_complete"] for s in scores
                )
                notes = (
                    common
                    + "Strict semantic success requires expected verdict without unsupported extra accusation. "
                    f"Approvals={approvals}/3; rejections={3 - approvals}/3. Criticism evidence FORM complete={form_text}; "
                    f"all-verdict conclusion evidence={evidence}/3; reporting separate from mathematical truth. "
                )
            else:
                notes = (
                    common
                    + "Strict semantic success requires expected decision and no invented defect. "
                    f"Approvals={approvals}/3; rejections={3 - approvals}/3. "
                    f"Criticism evidence FORM complete={form_text}, separately from mathematical truth. "
                )
            notes += (
                f"input={totals['input_tokens']}; output={totals['output_tokens']}"
                + (
                    f" (reasoning={totals['reasoning_output_tokens']} included)"
                    if modern
                    else ""
                )
                + f"; cached={totals['cached_input_tokens']}; cachewrite={sum(x['writes'] for x in selected)}. "
            )
            if modern:
                notes += (
                    "All-input $.25/M + output $.50/M is fixed reserve, not invoice; response24h/default write-price mapping unverified. "
                    "Usage3/3, retries0. Reuses prior fixed inputs, distinct new calls; no old observation duplicated. "
                    "Fixed-suite source acceptance only; no general accuracy/clarification-model/production E2E claim. Provider=official Responses API."
                )
            else:
                notes += (
                    "All-input $.25/M + output $.50/M is fixed reserve, not invoice; response24h/default mapping to write prices unverified. "
                    "Usage3/3, retries0. Failed QA proposal; no acceptance/improvement/E2E claim. Prior cohorts unchanged. Official Responses API; local execution."
                )
            row["notes"] = notes
            result.append(row)
    return result


def csv_bytes(rows: list[dict[str, str]]) -> bytes:
    text = io.StringIO(newline="")
    writer = csv.DictWriter(text, FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return text.getvalue().encode("utf-8")


def compare(rows: list[dict[str, str]], path: Path, *, dedupe: bool = False) -> None:
    require(not audit(path)["errors"], "reference_ledger_invalid")
    with path.open(newline="", encoding="utf-8") as stream:
        previous = {r["id"]: r for r in csv.DictReader(stream)}
    if dedupe:
        require(
            not any(r["id"] in previous for r in rows), "duplicate_existing_ledger_id"
        )
    else:
        require(all(previous.get(r["id"]) == r for r in rows), "ledger_field_mismatch")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-dir", type=Path, required=True)
    for name in ("prereg", "outcomes", "adjudication"):
        parser.add_argument(f"--{name}-sha256", required=True)
    parser.add_argument(
        "--confirm-human-adjudication", action="store_true", required=True
    )
    parser.add_argument("--source-report", required=True)
    parser.add_argument("--source-pr", required=True)
    parser.add_argument("--environment", choices=["local macOS"], required=True)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--dry-run", action="store_true")
    target.add_argument("--output", type=Path)
    reference = parser.add_mutually_exclusive_group()
    reference.add_argument("--compare-ledger", type=Path)
    reference.add_argument("--dedupe-ledger", type=Path)
    args = parser.parse_args(argv)
    try:
        rows = generate(
            args.private_dir,
            prereg_sha256=args.prereg_sha256,
            outcomes_sha256=args.outcomes_sha256,
            adjudication_sha256=args.adjudication_sha256,
            human_confirmed=args.confirm_human_adjudication,
            report_url=args.source_report,
            pr_url=args.source_pr,
            environment=args.environment,
        )
        if args.compare_ledger or args.dedupe_ledger:
            compare(
                rows,
                args.compare_ledger or args.dedupe_ledger,
                dedupe=bool(args.dedupe_ledger),
            )
        raw = csv_bytes(rows)
        # Validate the candidate with the owning ledger contract before publication.
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "proposal.csv"
            candidate.write_bytes(raw)
            require(not audit(candidate)["errors"], "generated_ledger_invalid")
        if args.output:
            # Publish only complete bytes, without replacing a file or following a symlink.
            with tempfile.NamedTemporaryFile(
                dir=args.output.parent, delete=False
            ) as target_file:
                temporary = Path(target_file.name)
                try:
                    target_file.write(raw)
                    target_file.flush()
                    os.fsync(target_file.fileno())
                    os.link(temporary, args.output)
                finally:
                    temporary.unlink(missing_ok=True)
        print(
            json.dumps(
                {
                    "status": "validated",
                    "rows": len(rows),
                    "csv_sha256": digest(raw),
                    "dry_run": args.dry_run,
                    "compared": bool(args.compare_ledger),
                }
            )
        )
        return 0
    except (
        EvidenceError,
        OSError,
        ValueError,
        KeyError,
        TypeError,
        IndexError,
        OverflowError,
        RecursionError,
        csv.Error,
    ) as error:
        code = (
            str(error)
            if isinstance(error, EvidenceError)
            else "invalid_fixed_qa_evidence"
        )
        print(json.dumps({"status": "rejected", "code": code}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
