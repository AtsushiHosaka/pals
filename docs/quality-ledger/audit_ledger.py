#!/usr/bin/env python3
"""Validate the quality ledger and report evidence coverage without optional packages.

Reads local files only. Does not change the ledger, call a model, or send events.
Coverage is metadata availability, not model accuracy or proof of provenance.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIELDS = (
    "id", "date", "family", "experiment", "model_config", "dataset", "n", "successes",
    "success_rate", "failures_json", "failures_raw_json", "cost_usd", "latency_p50_s",
    "latency_p95_s", "latency_other", "environment", "source", "source_type", "overlap_with", "notes",
)
FAMILIES = {
    "answer_latency", "recipe_retrieval", "exact_precheck", "statement_index", "lean_runtime",
    "proof_generation", "guest_quality", "catalog_audit", "load_test", "feature_audit",
    "availability", "other",
}
ENVIRONMENTS = {"", "local macOS", "AWS", "CI", "other"}
SOURCE_TYPES = {"doc", "spec", "pr_pals", "pr_agent", "issue"}
NUMBERS = ("n", "successes", "success_rate", "cost_usd", "latency_p50_s", "latency_p95_s")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError("non-finite JSON constant")


def audit(path: Path = HERE / "ledger.csv", taxonomy: Path = HERE / "taxonomy.md") -> dict:
    """Return errors plus counts. Unknown measurements remain empty, never zero-filled."""
    errors: list[str] = []
    codes = set(re.findall(
        r"^\| `([a-z]+\.[a-z_0-9]+|unclassified)`", taxonomy.read_text(encoding="utf-8"), re.M,
    ))
    with path.open(encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source, strict=True)
        if reader.fieldnames != list(FIELDS):
            return {"errors": ["CSV header must match ledger.schema.md exactly"], "rows": 0}
        rows = list(reader)
    seen: set[str] = set()
    dates: list[str] = []
    for line, row in enumerate(rows, 2):
        label = f"CSV line {line}"
        if None in row or any(value is None for value in row.values()):
            errors.append(f"{label}: wrong number of columns")
            continue
        rid = row["id"]
        if not rid.strip() or rid in seen:
            errors.append(f"{label}: empty or duplicate id")
        seen.add(rid)
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", row["date"]):
            try:
                dt.date.fromisoformat(row["date"])
                dates.append(row["date"])
            except ValueError:
                errors.append(f"{label}: invalid date")
        else:
            errors.append(f"{label}: date must be YYYY-MM-DD")
        for field in ("experiment", "source"):
            if not row[field].strip():
                errors.append(f"{label}: {field} is empty")
        for field, allowed in (
            ("family", FAMILIES), ("environment", ENVIRONMENTS), ("source_type", SOURCE_TYPES),
        ):
            if row[field] not in allowed:
                errors.append(f"{label}: invalid {field}")
        numeric: dict[str, Decimal] = {}
        for field in NUMBERS:
            if not row[field]:
                continue
            try:
                value = Decimal(row[field])
                if not value.is_finite() or value < 0:
                    raise ValueError
                if field in {"n", "successes"} and value != value.to_integral_value():
                    raise ValueError
                numeric[field] = value
            except (InvalidOperation, ValueError):
                errors.append(f"{label}: {field} must be a finite nonnegative "
                              + ("integer" if field in {"n", "successes"} else "number"))
        if numeric.get("success_rate", 0) > 1:
            errors.append(f"{label}: success_rate is outside 0..1")
        if "n" in numeric and "successes" in numeric:
            if numeric["successes"] > numeric["n"]:
                errors.append(f"{label}: successes exceeds n")
            if "success_rate" in numeric:
                # Historical rates are rounded to four decimal places.
                if not numeric["n"] or abs(
                    numeric["success_rate"] - numeric["successes"] / numeric["n"]
                ) > Decimal("0.00005"):
                    errors.append(f"{label}: success_rate disagrees with successes / n")
        if ("latency_p50_s" in numeric and "latency_p95_s" in numeric
                and numeric["latency_p50_s"] > numeric["latency_p95_s"]):
            errors.append(f"{label}: latency_p50_s exceeds latency_p95_s")
        for field in ("failures_json", "failures_raw_json"):
            if not row[field]:
                continue
            try:
                parsed = json.loads(row[field], object_pairs_hook=_unique_object,
                                    parse_constant=_reject_constant)
                if not isinstance(parsed, dict):
                    raise ValueError
                if field == "failures_json":
                    if any(code not in codes for code in parsed):
                        errors.append(f"{label}: failure code is absent from taxonomy.md")
                    if any(type(count) is not int or count < 0 for count in parsed.values()):
                        errors.append(f"{label}: failure counts must be nonnegative integers")
                # Raw source annotations may contain unknown counts or ratios. Preserve them.
            except (ValueError, TypeError):
                errors.append(f"{label}: {field} must be a JSON object without duplicate keys")
    for line, row in enumerate(rows, 2):
        if None in row or any(value is None for value in row.values()):
            continue
        for other in filter(None, row["overlap_with"].split(";")):
            if other not in seen or other == row["id"]:
                errors.append(f"CSV line {line}: overlap_with is unknown or self-referential")
    valid_shape = [r for r in rows if None not in r and all(v is not None for v in r.values())]
    return {
        "errors": errors,
        "rows": len(rows),
        "date_min": min(dates) if dates else None,
        "date_max": max(dates) if dates else None,
        "source_types": dict(sorted(Counter(r["source_type"] for r in valid_shape).items())),
        "families": dict(sorted(Counter(r["family"] for r in valid_shape).items())),
        "missing_fields": {field: sum(not r[field].strip() for r in valid_shape) for field in FIELDS},
        "overlapping_rows": sum(bool(r["overlap_with"]) for r in valid_shape),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=HERE / "ledger.csv")
    parser.add_argument("--json", action="store_true", help="Print only counts and validation errors as JSON")
    args = parser.parse_args()
    try:
        report = audit(args.ledger)
    except (OSError, csv.Error, UnicodeError) as error:
        report = {"errors": [f"Cannot read ledger: {type(error).__name__}"], "rows": 0}
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))
    else:
        print(f"{report['rows']} ledger rows; {len(report['errors'])} validation errors")
        for error in report["errors"]:
            print(f"  - {error}")
    return int(bool(report["errors"]))


if __name__ == "__main__":
    raise SystemExit(main())
