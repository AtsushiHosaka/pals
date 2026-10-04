#!/usr/bin/env python3
"""Audit explicitly bound foundation chapters/forms; never infer coverage from card counts.

Run with pals-agent/.venv/bin/python. No database, network, or publication operations.
Artifact-bound evidence is NOT a compiler receipt or a successful problem execution.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = "docs/foundation-curriculum-contract.v1.json"
INVENTORY = "specs/draft-catalog-expansion/inventory-sources.v1.json"
LEVELS = ("authored", "artifact_bound", "lean_replayed")


def read(path: Path) -> Any:
    return json.loads(path.read_text())


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def safe_path(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    path.relative_to(root.resolve())
    if not path.is_file():
        raise ValueError(f"Missing input: {relative}")
    return path


def load_inventory_auditor(root: Path) -> Any:
    spec = importlib.util.spec_from_file_location(
        "foundation_inventory_auditor",
        root / "pals-scripts/audit-draft-catalog-coverage.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_contract(
    contract: dict[str, Any], matrix: dict[str, Any]
) -> list[dict[str, Any]]:
    if set(contract) != {
        "schema_version",
        "scope_id",
        "matrix_path",
        "description",
        "chapters",
        "stage_chapter_counts",
        "required_modes",
        "required_difficulties",
    }:
        raise ValueError("Unexpected curriculum contract fields")
    if contract["schema_version"] != "pals.foundation-curriculum-contract.v1":
        raise ValueError("Unsupported curriculum contract")
    scope = next(s for s in matrix["scopes"] if s["id"] == contract["scope_id"])
    if scope["kind"] != "undergraduate_core":
        raise ValueError("The curriculum requires an undergraduate_core scope")
    # Version 1 fixes the denominators, independently of mutable matrix defaults.
    fixed_axes = {
        "required_modes": {
            "recognize": 1,
            "compute_construct": 1,
            "justify_prove": 1,
            "counterexample_audit": 1,
            "synthesize": 1,
        },
        "required_difficulties": {"introductory": 1, "standard": 2, "advanced": 1},
    }
    fixed_stages = {"univ.linear": 10, "univ.calculus": 10, "univ.multivar": 10}
    if contract["stage_chapter_counts"] != fixed_stages or any(
        type(n) is not int for n in contract["stage_chapter_counts"].values()
    ):
        raise ValueError("Version 1 requires exactly ten chapters in each fixed stage")

    def axis_counts(axis: Any) -> dict[str, int]:
        if not isinstance(axis, list) or not axis:
            raise ValueError("Fixed curriculum requirements must be nonempty arrays")
        result = {}
        for item in axis:
            if (
                not isinstance(item, dict)
                or set(item) != {"id", "minimum_distinct_patterns"}
                or not isinstance(item["id"], str)
                or type(item["minimum_distinct_patterns"]) is not int
                or item["id"] in result
            ):
                raise ValueError("Malformed or repeated fixed curriculum requirement")
            result[item["id"]] = item["minimum_distinct_patterns"]
        return result

    for axis, fixed in fixed_axes.items():
        if axis_counts(contract[axis]) != fixed:
            raise ValueError("Version 1 fixed curriculum denominator cannot change")
        if axis_counts(scope["defaults"][axis]) != fixed:
            raise ValueError(
                "Matrix defaults differ from the fixed curriculum denominator"
            )
    families = {f["id"]: f for f in scope["families"]}
    expected = {
        k
        for k, f in families.items()
        if f["stage"] in {"univ.linear", "univ.calculus", "univ.multivar"}
    }
    for stage, count in fixed_stages.items():
        if sum(f["stage"] == stage for f in families.values()) != count:
            raise ValueError(
                "Matrix chapter counts differ from the fixed curriculum denominator"
            )
    seen: set[str] = set()
    for chapter in contract["chapters"]:
        if set(chapter) != {"family_id", "problem_forms"}:
            raise ValueError("Unexpected chapter fields")
        key = chapter["family_id"]
        if key in seen or key not in expected:
            raise ValueError("Duplicate or outside-scope chapter")
        seen.add(key)
        for axis, fixed in fixed_axes.items():
            effective = families[key].get(axis, scope["defaults"][axis])
            if axis_counts(effective) != fixed:
                raise ValueError(
                    "Family requirements differ from the fixed curriculum denominator"
                )
        modes = contract["required_modes"]
        if set(chapter["problem_forms"]) != {m["id"] for m in modes}:
            raise ValueError("Problem forms must match required modes exactly")
        if any(
            not isinstance(v, str) or not v.strip()
            for v in chapter["problem_forms"].values()
        ):
            raise ValueError("Problem descriptions must be nonempty")
    if seen != expected:
        raise ValueError(
            "Contract must include every target chapter; denominator cannot shrink"
        )
    return [
        dict(families[c["family_id"]], problem_forms=c["problem_forms"])
        for c in contract["chapters"]
    ]


def structural_signature(xml: str) -> str | None:
    """Fingerprint XML structure, ignoring formatting, names and literal values.

    Expanded tag names preserve namespace distinctions. Attribute ordering and
    whitespace-only formatting have no mathematical role. Meaningful nonliteral
    text is retained; this remains a conservative syntactic heuristic, not a
    decision procedure for equivalence of propositions.
    """
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return None

    def structure(node: ET.Element) -> tuple[Any, ...]:
        local = node.tag.rsplit("}", 1)[-1]
        attributes = dict(node.attrib)
        text = node.text or ""
        tail = node.tail or ""
        if local == "OMV" and "name" in attributes:
            attributes["name"] = "v"
        if local in {"OMI", "OMF"}:
            text = "#"
            for key in ("dec", "hex"):
                if key in attributes:
                    attributes[key] = "#"
        if local == "OMOBJ":
            attributes = {}
        return (
            node.tag,
            tuple(sorted(attributes.items())),
            text if text.strip() else "",
            tail if tail.strip() else "",
            tuple(structure(child) for child in node),
        )

    encoded = json.dumps(structure(root), ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def normalized_inventory_records(
    root: Path, inventory: dict[str, Any], audit: Any
) -> list[dict[str, Any]]:
    """Reuse inventory identity checks while keeping the new fingerprint isolated."""
    records = audit.inventory_repository(root, inventory)["identities"]["records"]
    xmls = {}
    for source in inventory["sources"]:
        if source["kind"] == "packaged_seed":
            continue
        manifest = source["path"]
        payload = read(safe_path(root, manifest))
        for card in audit._draft_cards(payload, source["card_keys"], manifest):
            identifier, xml = audit._card_identity(card, manifest)
            key = (identifier, manifest)
            if key in xmls:
                raise ValueError("Duplicate card identity in an authoring manifest")
            xmls[key] = xml
    return [
        dict(
            record,
            structural_signature=structural_signature(
                xmls[(record["id"], record["manifest"])]
            )
            or "",
        )
        for record in records
    ]


def artifact_evidence(root: Path, manifest: str, replay: bool) -> dict[str, Any]:
    path = safe_path(root, manifest)
    payload = read(path)
    result: dict[str, Any] = {
        "manifest": manifest,
        "manifest_sha256": digest(path),
        "artifact_bound": False,
        "lean_replayed": False,
        "runtime_problem_execution": "not_checked",
    }
    if payload.get("schema_version") != "pals.typed-catalog-expansion-batch.v1":
        result["artifact_status"] = "unsupported_evidence_schema_no_credit"
        return result
    sys.path.insert(0, str(root / "pals-agent"))
    try:
        from pals_agent.typed_catalog_expansion import validate_expansion_batch

        validated = validate_expansion_batch(payload, repository_root=root)
        result["artifact_bound"] = True
        result["artifact_status"] = (
            "canonical_profile_and_exact_pinned_bundle_validated"
        )
        result["witness_path"] = payload["evidence"]["witness_path"]
        result["evidence"] = payload["evidence"]
        result["validated_card_ids"] = [c.card_id for c in validated.cards]
    except (ValueError, ImportError, OSError, KeyError, TypeError) as exc:
        result["artifact_status"] = "invalid_or_unavailable"
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result
    finally:
        sys.path.pop(0)
    if replay:
        witness = safe_path(root, result["witness_path"])
        command = ["lake", "env", "lean", str(witness)]
        try:
            completed = subprocess.run(
                command,
                cwd=root / "pals-agent/lean-workspace",
                capture_output=True,
                text=True,
                timeout=180,
                check=False,
            )
            # The loader already rejects sorry/admit/axiom/unsafe in every card.
            result["lean_replayed"] = completed.returncode == 0
            result["compiler"] = {
                "command": command,
                "exit_code": completed.returncode,
                "output": (completed.stdout + completed.stderr)[-12000:],
            }
        except (OSError, subprocess.TimeoutExpired) as exc:
            result["compiler"] = {"error": str(exc)}
    return result


def axis_summary(rows: list[dict[str, Any]], field: str, level: str) -> dict[str, Any]:
    required = sum(c["required"] for row in rows for c in row[field])
    filled = sum(c["evidence"][level]["filled"] for row in rows for c in row[field])
    return {
        "filled": filled,
        "required": required,
        "percent": round(100 * filled / required, 2) if required else None,
    }


def build_report(
    root: Path,
    contract: dict[str, Any],
    matrix: dict[str, Any],
    inventory: dict[str, Any],
    *,
    replay: bool = False,
) -> dict[str, Any]:
    audit = load_inventory_auditor(root)
    audit.validate_matrix(matrix)
    chapters = validate_contract(contract, matrix)
    scope = next(s for s in matrix["scopes"] if s["id"] == contract["scope_id"])
    records = normalized_inventory_records(root, inventory, audit)
    lookup = {(r["id"], r["manifest"]): r for r in records}
    profiles = {p["id"]: set(p["profile_ids"]) for p in matrix["profile_requirements"]}
    evidence: dict[str, dict[str, Any]] = {}
    invalid: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    rows = []
    for family in chapters:
        bindings = []
        seen: set[str] = set()
        for binding in sorted(
            family.get("draft_bindings", []),
            key=lambda b: (b["draft_id"], b["authoring_manifest"]),
        ):
            key = (binding["draft_id"], binding["authoring_manifest"])
            record = lookup.get(key)
            reason = None
            if record is None:
                reason = "card_id_not_found_in_declared_manifest"
            elif record["profile_id"] not in profiles[family["profile_requirement"]]:
                reason = "profile_not_allowed_for_family"
            elif not record["structural_signature"]:
                reason = "invalid_openmath"
            if reason:
                invalid.append({"family_id": family["id"], **binding, "reason": reason})
                continue
            assert record is not None
            signature = record["structural_signature"]
            if signature in seen:
                duplicates.append(
                    {
                        "family_id": family["id"],
                        **binding,
                        "structural_signature": signature,
                    }
                )
                continue
            seen.add(signature)
            manifest = binding["authoring_manifest"]
            if manifest not in evidence:
                evidence[manifest] = artifact_evidence(root, manifest, replay)
            ev = evidence[manifest]
            bindings.append(
                {
                    **binding,
                    "profile_id": record["profile_id"],
                    "structural_signature": signature,
                    "openmath_sha256": record["openmath_sha256"],
                    "evidence": {
                        "authored": True,
                        "artifact_bound": ev["artifact_bound"],
                        "lean_replayed": ev["lean_replayed"],
                    },
                }
            )
        mode_requirements = family.get(
            "required_modes", scope["defaults"]["required_modes"]
        )
        diff_requirements = family.get(
            "required_difficulties", scope["defaults"]["required_difficulties"]
        )

        def cells(
            requirements: list[dict[str, Any]],
            field: str,
            members_source: list[dict[str, Any]],
        ) -> list[dict[str, Any]]:
            result = []
            for requirement in requirements:
                members = [b for b in members_source if b[field] == requirement["id"]]
                count = requirement["minimum_distinct_patterns"]
                result.append(
                    {
                        "id": requirement["id"],
                        "required": count,
                        "evidence": {
                            level: {
                                "filled": min(
                                    count, sum(b["evidence"][level] for b in members)
                                ),
                                "card_refs": [
                                    {
                                        "id": b["draft_id"],
                                        "manifest": b["authoring_manifest"],
                                    }
                                    for b in members
                                    if b["evidence"][level]
                                ],
                            }
                            for level in LEVELS
                        },
                    }
                )
            return result

        mode_cells = cells(mode_requirements, "primary_mode", bindings)
        for cell in mode_cells:
            cell["problem_form"] = family["problem_forms"][cell["id"]]
        difficulty_cells = cells(diff_requirements, "difficulty", bindings)
        joint = [
            {
                "mode": m["id"],
                "difficulty": d["id"],
                "card_refs": [
                    {"id": b["draft_id"], "manifest": b["authoring_manifest"]}
                    for b in bindings
                    if b["primary_mode"] == m["id"] and b["difficulty"] == d["id"]
                ],
            }
            for m in mode_requirements
            for d in diff_requirements
        ]
        rows.append(
            {
                "family_id": family["id"],
                "title": family["title"],
                "stage": family["stage"],
                "bindings": bindings,
                "mode_cells": mode_cells,
                "difficulty_cells": difficulty_cells,
                "joint_cells_diagnostic_only": joint,
                "chapter_contract_met": {
                    level: all(
                        c["evidence"][level]["filled"] == c["required"]
                        for c in mode_cells + difficulty_cells
                    )
                    for level in LEVELS
                },
            }
        )
    summaries = {}
    for stage in ["all", "univ.linear", "univ.calculus", "univ.multivar"]:
        subset = rows if stage == "all" else [r for r in rows if r["stage"] == stage]
        summaries[stage] = {
            level: {
                "mode_slots": axis_summary(subset, "mode_cells", level),
                "difficulty_slots": axis_summary(subset, "difficulty_cells", level),
                "chapters_contract_met": sum(
                    r["chapter_contract_met"][level] for r in subset
                ),
                "chapters_required": len(subset),
            }
            for level in LEVELS
        }
    if not replay:
        for summary in summaries.values():
            summary["lean_replayed"]["measurement_status"] = "not_run"
            summary["lean_replayed"]["chapters_contract_met"] = None
            for axis in ("mode_slots", "difficulty_slots"):
                summary["lean_replayed"][axis]["filled"] = None
                summary["lean_replayed"][axis]["percent"] = None
    return {
        "schema_version": "pals.foundation-curriculum-audit.v1",
        "scope_id": scope["id"],
        "evidence_levels": {
            "authored": "Explicit matrix binding resolves to a source card with allowed profile and parsed XML.",
            "artifact_bound": "Expansion loader validates canonical XML, profile pins, environment pins and exact Lean bundle; no compiler or semantic-review inference.",
            "lean_replayed": "This invocation ran lake env lean on the validated exact witness bundle with exit code 0; no problem-execution inference.",
            "runtime_problem_execution": "not_checked; neither retrieval, instantiation, nor solving is tested by this audit.",
        },
        "runtime_problem_execution": {
            "status": "not_checked",
            "coverage_percent": None,
        },
        "replay_requested": replay,
        "summary": summaries,
        "chapters": rows,
        "manifest_evidence": list(evidence.values()),
        "invalid_bindings": invalid,
        "structural_duplicate_bindings_excluded": duplicates,
        "all_catalog_records_not_credited_to_target_scope": len(records)
        - len(
            {
                (b["draft_id"], b["authoring_manifest"])
                for r in rows
                for b in r["bindings"]
            }
        ),
        "catalog_population_note": "The outside-credit count includes all repository subjects and unbound records. It is not a foundation denominator or a measure of missing foundation mathematics.",
        "missing_difficulty_slots": [
            {
                "family_id": row["family_id"],
                "difficulty": cell["id"],
                "required": cell["required"],
                "filled": cell["evidence"]["authored"]["filled"],
                "missing": cell["required"] - cell["evidence"]["authored"]["filled"],
                "card_refs": cell["evidence"]["authored"]["card_refs"],
            }
            for row in rows
            for cell in row["difficulty_cells"]
            if cell["evidence"]["authored"]["filled"] < cell["required"]
        ],
        "joint_grid_policy": "Mode × difficulty cells are diagnostic only. The existing matrix requires separate marginals, not every Cartesian pair.",
        "pattern_policy": "Isolated XML structure-tuple fingerprint normalizes insignificant whitespace, attribute order, variable names and literals. Distinct fingerprints do not prove semantic independence.",
        "missing_mode_cells": [
            {
                "family_id": r["family_id"],
                "mode": c["id"],
                "problem_form": c["problem_form"],
            }
            for r in rows
            for c in r["mode_cells"]
            if not c["evidence"]["authored"]["filled"]
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--replay-lean",
        action="store_true",
        help="Compile each bound supported expansion witness once; up to 180 seconds per bundle",
    )
    args = parser.parse_args()
    contract = read(ROOT / CONTRACT)
    matrix = read(ROOT / contract["matrix_path"])
    inventory = read(ROOT / INVENTORY)
    report = build_report(ROOT, contract, matrix, inventory, replay=args.replay_lean)
    report["input_sha256"] = {
        p: digest(ROOT / p)
        for p in [
            CONTRACT,
            contract["matrix_path"],
            INVENTORY,
            "pals-scripts/audit-draft-catalog-coverage.py",
            "pals-scripts/audit-foundation-curriculum.py",
        ]
    }
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded)
    print(
        json.dumps(
            {
                "summary": report["summary"],
                "invalid_bindings": len(report["invalid_bindings"]),
                "runtime_problem_execution": report["runtime_problem_execution"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    failed_artifacts = any(
        evidence["artifact_status"] == "invalid_or_unavailable"
        or (
            args.replay_lean
            and evidence["artifact_bound"]
            and not evidence["lean_replayed"]
        )
        for evidence in report["manifest_evidence"]
    )
    return 1 if report["invalid_bindings"] or failed_artifacts else 0


if __name__ == "__main__":
    raise SystemExit(main())
