#!/usr/bin/env python3
"""Read-only Recipe candidate inventory. Offline artifacts never establish usability.

Uses the owning API's real manifest parser, materializer and source validator. This
first #193 slice deliberately has no database, network, signature or model adapter.
It reports unknown publication/runtime counts, rather than accepting self-asserted
``admitted`` or ``runtime_verified`` flags from authoring data.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCHEMA = "pals.usable-catalog-inventory.v1"
MAX_FILES = 10_000
MAX_FILE_BYTES = 2 * 1024 * 1024
PROFILE = "lean-proposition-v1"
_API_IMPORT_PINS: dict[Path, dict[str, str]] = {}


class InventoryError(ValueError):
    """A source or inventory cannot be inspected without weakening its contract."""


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def api_source_pin(repository: Path) -> dict[str, str]:
    """Observe clean checker provenance before loading code and after the audit."""
    root = repository.resolve(strict=True)
    if not (root / "app/domain/recipe_catalog_admission.py").is_file():
        raise InventoryError("owning API repository is missing the admission parser")
    dirty = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain", "--", "app"],
        check=True, capture_output=True, text=True, timeout=5,
    ).stdout
    if dirty:
        raise InventoryError("owning API app sources must be clean for a pinned audit")
    revision = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True, timeout=5,
    ).stdout.strip()
    return {"revision": revision, "parser_sha256": sha256(
        (root / "app/domain/recipe_catalog_admission.py").read_bytes()
    )}


def require_api_pin(repository: Path, expected: dict[str, str]) -> None:
    if api_source_pin(repository) != expected:
        raise InventoryError("owning API revision or parser changed during audit")


def api_adapter(repository: Path, *, pin: dict[str, str] | None = None) -> Any:
    """Load clean owning code once; never relabel cached code after a checkout."""
    root = repository.resolve(strict=True)
    pin = api_source_pin(root) if pin is None else pin
    name = "app.domain.recipe_catalog_admission"
    if name in sys.modules and _API_IMPORT_PINS.get(root) != pin:
        raise InventoryError("cached API parser lacks the matching import-time provenance")
    require_api_pin(root, pin)
    sys.path.insert(0, str(root))
    module = importlib.import_module(name)
    if Path(module.__file__).resolve() != root / "app/domain/recipe_catalog_admission.py":
        raise InventoryError("a different API package is already imported")
    require_api_pin(root, pin)
    _API_IMPORT_PINS[root] = dict(pin)
    return module


def classify_candidates(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate exact-byte targets without claiming semantic equivalence."""
    latest: dict[str, int] = {}
    content_by_identity: dict[tuple[str, int], tuple[str, ...]] = {}
    for item in records:
        identity = (item["recipe_id"], item["revision"])
        content = tuple(item[key] for key in (
            "file_sha256", "source_sha256", "target_sha256", "toolchain_sha256"
        ))
        if identity in content_by_identity and content_by_identity[identity] != content:
            raise InventoryError("conflicting contents for the same Recipe candidate revision")
        content_by_identity[identity] = content
        latest[item["recipe_id"]] = max(latest.get(item["recipe_id"], 0), item["revision"])
    seen: dict[str, str] = {}
    identities: set[tuple[str, int]] = set()
    result = []
    for item in sorted(records, key=lambda row: (row["recipe_id"], -row["revision"], row["path"])):
        row = dict(item)
        reasons = ["no_authenticated_publication_evidence", "no_runtime_retrieval_evidence"]
        identity = (row["recipe_id"], row["revision"])
        duplicate_revision = identity in identities
        if duplicate_revision:
            reasons.append("duplicate_candidate_revision")
        identities.add(identity)
        current = row["revision"] == latest[row["recipe_id"]] and not duplicate_revision
        if row["revision"] != latest[row["recipe_id"]]:
            reasons.append("superseded_candidate_revision")
        key = row["operational_key"]
        if current:
            if key in seen:
                reasons.append("duplicate_current_operational_target")
                row["same_current_operational_target_as"] = seen[key]
            else:
                seen[key] = row["recipe_id"]
        # Parser/materializer success is authoring evidence only. There is no
        # caller-controlled lifecycle boolean which can promote this record.
        row.update(current_candidate=current, counted_usable=False, publication_state="not_checked",
                   runtime_state="not_checked", exclusions=reasons)
        result.append(row)
    return result


def audit(directory: Path, api_repository: Path, *, expected_snapshot: str | None = None) -> dict:
    root = directory.resolve(strict=True)
    if not root.is_dir():
        raise InventoryError("authoring directory required")
    paths = sorted(root.rglob("*.json"))
    if not paths or len(paths) > MAX_FILES:
        raise InventoryError("authoring directory must contain 1 to 10000 JSON manifests")
    checker_pin = api_source_pin(api_repository)
    api = api_adapter(api_repository, pin=checker_pin)
    records = []
    snapshot = []
    contents: dict[Path, str] = {}
    for path in paths:
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise InventoryError("manifest symlinks are not accepted")
        if path.stat().st_size > MAX_FILE_BYTES:
            raise InventoryError("manifest exceeds the bounded file size")
        raw = path.read_bytes()
        if not raw or len(raw) > MAX_FILE_BYTES:
            raise InventoryError("invalid manifest file size")
        digest = sha256(raw)
        manifest = api.RecipeAuthoringManifestV1.parse(raw)
        source = api.RecipeMaterializerV1.materialize(manifest)
        api.validate_materialized_recipe(manifest, source)
        relative = path.relative_to(root).as_posix()
        snapshot.append({"path": relative, "sha256": digest})
        contents[path] = digest
        target = manifest.target_c14n_sha256
        records.append({
            "path": relative, "file_sha256": digest,
            "recipe_id": manifest.recipe_id, "revision": manifest.revision,
            "profile": PROFILE, "target_sha256": target,
            "source_sha256": sha256(source), "toolchain_sha256": manifest.toolchain.sha256,
            "target_text_key": PROFILE + ":" + target,
            "operational_key": PROFILE + ":" + target + ":" + manifest.toolchain.sha256,
        })
    # Catch changes during traversal and include the complete path set, so a
    # simultaneous generator cannot silently produce a mixed inventory.
    if paths != sorted(root.rglob("*.json")) or any(
        sha256(path.read_bytes()) != digest for path, digest in contents.items()
    ):
        raise InventoryError("authoring snapshot changed during audit")
    snapshot_digest = sha256(api.canonical_json_bytes(snapshot))
    if expected_snapshot is not None and expected_snapshot != snapshot_digest:
        raise InventoryError("authoring snapshot differs from the expected pin")
    classified = classify_candidates(records)
    require_api_pin(api_repository, checker_pin)
    current_records = [row for row in classified if row["current_candidate"]]
    return {
        "schema_version": SCHEMA,
        "observed_at_utc": datetime.now(UTC).isoformat(),
        "snapshot_sha256": snapshot_digest,
        "api_revision": checker_pin["revision"],
        "admission_parser_sha256": checker_pin["parser_sha256"],
        "candidate_count": len(records),
        "candidate_exact_target_text_groups": len({r["target_text_key"] for r in records}),
        "candidate_operational_groups": len({r["operational_key"] for r in records}),
        "current_candidate_count": len(current_records),
        "current_candidate_exact_target_text_groups": len({
            r["target_text_key"] for r in current_records
        }),
        "current_candidate_operational_groups": len({
            r["operational_key"] for r in current_records
        }),
        "eligible_published_count": None,
        "verified_usable_count": None,
        "counted_usable_count": 0,
        "database_read": False,
        "exclusion_counts": dict(sorted(Counter(
            reason for row in classified for reason in row["exclusions"]
        ).items())),
        "limitations": [
            "Exact target text groups imply no semantic count or upper/lower bound; bindings vary.",
            "Offline authoring and source validation do not prove compilation or admission.",
            "No authenticated publication, active-generation, retrieval or runtime evidence read.",
            "Draft and typed catalogs are not covered by this Recipe-manifest slice.",
        ],
        "records": classified,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authoring-directory", type=Path, required=True)
    parser.add_argument("--api-repository", type=Path, required=True)
    parser.add_argument("--expected-snapshot-sha256")
    args = parser.parse_args(argv)
    if args.expected_snapshot_sha256 is not None and not re.fullmatch(
        "[0-9a-f]{64}", args.expected_snapshot_sha256
    ):
        parser.error("expected snapshot must be a lowercase SHA-256 digest")
    try:
        report = audit(args.authoring_directory, args.api_repository,
                       expected_snapshot=args.expected_snapshot_sha256)
    except (ValueError, OSError, ImportError, subprocess.SubprocessError) as error:
        # Admission parser errors may quote source content; no arbitrary error
        # string, environment value or database URL is printed.
        print(json.dumps({"status": "failed", "error_type": type(error).__name__}),
              file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
