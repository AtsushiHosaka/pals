#!/usr/bin/env python3
"""Check the completion contract against readable specs and exact child copies.

This is an offline source-contract check, not metric extraction or alarm execution.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

SPEC_PATH = Path("specs/proof-quality-observability")


def validate(spec: Path, copies: list[Path] | None = None) -> list[str]:
    errors: list[str] = []
    raw = (spec / "completion-metrics.v1.json").read_bytes()
    contract = json.loads(raw)
    requirements = (spec / "requirements.md").read_text()
    design = (spec / "design.md").read_text()
    tasks = (spec / "tasks.md").read_text()
    states = contract["states"]
    if len(states) != 5 or len(set(states)) != 5:
        errors.append("state_count")
    requirement = next(line for line in requirements.splitlines() if line.startswith("| PQO-005 |"))
    if "`State`" not in requirement or any(f"`{state}`" not in requirement for state in states):
        errors.append("requirement_state_allowlist")
    d4 = design.split("### D4 ", 1)[1].split("### D5 ", 1)[0]
    rows: dict[str, list[str]] = {}
    for line in d4.splitlines():
        if not line.startswith("|"):
            continue
        cells = [part.strip() for part in line.split("|")[1:-1]]
        if cells and cells[0].startswith("`"):
            rows[cells[0].strip("`")] = cells
    for name, metric in contract["metrics"].items():
        row = rows.get(name)
        if row is None or len(row) < 3:
            errors.append("metric_missing_from_design")
            continue
        dimensions = re.findall(r"\[([A-Za-z, ]+)\]", row[2])
        expected = ", ".join(metric["dimensions"])
        if row[1] != metric["unit"] or dimensions != [expected]:
            errors.append("metric_unit_or_dimensions")
    if any(state not in rows for state in states):
        errors.append("design_state_allowlist")
    for alarm in contract["alarms"].values():
        if (alarm["unit"] != "Seconds" or alarm["statistic"] != "Maximum"
                or alarm["period_seconds"] != 300 or alarm["evaluation_periods"] != 1
                or alarm["datapoints_to_alarm"] != 1
                or alarm["comparison_operator"] != "GreaterThanThreshold"
                or alarm["treat_missing_data"] != "breaching"):
            errors.append("alarm_contract")
    if "completion-metrics.v1.json" not in tasks:
        errors.append("tasks_contract_reference")
    for copy in copies or []:
        if copy.read_bytes() != raw:
            errors.append("child_contract_bytes_differ")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec-dir", type=Path, default=Path(__file__).resolve().parents[1] / SPEC_PATH)
    parser.add_argument("--copy", type=Path, action="append", default=[])
    args = parser.parse_args()
    try:
        errors = validate(args.spec_dir, args.copy)
        digest = hashlib.sha256((args.spec_dir / "completion-metrics.v1.json").read_bytes()).hexdigest()
    except (OSError, ValueError, KeyError, TypeError, StopIteration, IndexError):
        errors, digest = ["contract_or_spec_unreadable"], None
    print(json.dumps({"errors": errors, "contract_sha256": digest, "child_copies": len(args.copy)}))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
