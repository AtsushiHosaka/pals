#!/usr/bin/env python3
"""Prepare exact-source Recipe inputs and unsealed question metadata, never publish.

Run with the existing API Python environment. External review evidence must bind
the complete runtime JSON, source, target, explanation, and exact metadata bytes.
This preparation review is not an admission receipt or a signed search-entry review.
The explicit materialized policy accepts only already compiled and reviewed exact
RecipeMaterializerV1 output. Transformations must be reverified before preparation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pals-api"))


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def prepare(
    result_bytes,
    review,
    metadata,
    *,
    recipe_id,
    revision,
    author,
    toolchain_id,
    fingerprint,
    admission_policy="raw",
):
    import rfc8785
    from app.core.duplicate_json import decode_json_object
    from app.domain.lean_target import extract_single_target_declaration
    from app.domain.recipe_catalog_admission import (
        RecipeAuthoringManifestV1,
        RecipeMaterializerV1,
    )
    from app.release.draft_candidate_recipe_admit import parse_manifest

    result = decode_json_object(result_bytes)
    if result.get("passed") is not True or result.get("lean_verified") is not True:
        raise ValueError("runtime result is not successful")
    if result.get("verification", {}).get("success") is not True:
        raise ValueError("runtime compiler approval is missing")
    semantic = result.get("semantic_review", {})
    output = result.get("answer_review", {})
    if semantic.get("decision") != "approved" or not semantic.get("session_id"):
        raise ValueError("runtime semantic approval is missing")
    # Older runner records only a successful output-review object, not its decision.
    # An external exact-artifact review below is therefore mandatory in all cases.
    if not output.get("session_id") or output.get("decision", "approved") != "approved":
        raise ValueError("runtime output review is missing or rejected")
    if semantic["session_id"] == output["session_id"]:
        raise ValueError("semantic and output review sessions must be distinct")
    source = result.get("lean_source")
    if not isinstance(source, str):
        raise TypeError("runtime Lean source is missing")
    target = extract_single_target_declaration(source)
    if admission_policy not in {"raw", "materialized"}:
        raise ValueError("unsupported admission policy")
    if target is None or (admission_policy == "raw" and target.name is None):
        raise ValueError("one named Lean target is required")
    if result.get("target") != target.as_dict():
        raise ValueError("recorded target differs from actual Lean source")
    if not isinstance(result.get("explanation"), dict):
        raise TypeError("reviewed explanation is missing")
    required_metadata = {
        "statement",
        "domain",
        "assumptions",
        "quantifiers",
        "conclusion",
        "search_text",
        "output_language",
        "question_variants",
    }
    if set(metadata) != required_metadata:
        raise ValueError("metadata fields differ from the closed proposal contract")
    for key in ("statement", "domain", "conclusion", "search_text"):
        if not isinstance(metadata[key], str) or not metadata[key].strip():
            raise ValueError("metadata text is empty")
    for key in ("assumptions", "quantifiers", "question_variants"):
        if not isinstance(metadata[key], list) or any(
            not isinstance(x, str) or not x.strip() for x in metadata[key]
        ):
            raise ValueError("metadata list is invalid")
    if metadata["output_language"] not in {"en", "ja", "zh-Hans", "zh-Hant"}:
        raise ValueError("unsupported output language")
    bindings = {
        "runtime_result_sha256": digest(result_bytes),
        "lean_sha256": digest(source.encode()),
        "target_sha256": digest(target.proposition.encode()),
        "explanation_sha256": digest(rfc8785.dumps(result["explanation"])),
        "metadata_sha256": digest(rfc8785.dumps(metadata)),
    }
    if any(review.get(k) != v for k, v in bindings.items()):
        raise ValueError("external review artifact hash mismatch")
    if review.get("schema_version") != "pals.math-question-preparation-review.v1":
        raise ValueError("unsupported preparation review")
    principal = review.get("reviewer_principal", "")
    if (
        not isinstance(principal, str)
        or not principal.startswith("pals.principal.v1/")
        or principal == author
    ):
        raise ValueError("independent reviewer principal required")
    if (
        review.get("semantic_approved") is not True
        or review.get("output_approved") is not True
        or review.get("question_variants_equivalent") is not True
        or not review.get("rationale")
    ):
        raise ValueError(
            "external semantic, output and question equivalence approvals required"
        )
    manifest = {
        "schema_version": "pals.raw-recipe-authoring.v1",
        "recipe_id": recipe_id,
        "recipe_revision": revision,
        "source_author_principal": author,
        "toolchain_id": toolchain_id,
        "toolchain_fingerprint": fingerprint,
        "lean_code": source,
        "lean_sha256": bindings["lean_sha256"],
        "target_source": target.proposition,
        "target_sha256": bindings["target_sha256"],
    }
    if admission_policy == "materialized":
        prefix = "import Mathlib\n\nexample : " + target.proposition + " := "
        if (
            target.kind != "example"
            or not source.startswith(prefix)
            or not source.endswith("\n")
        ):
            raise ValueError(
                "materialized policy requires exact previously reverified RecipeMaterializerV1 source"
            )
        manifest = {
            "schema_version": "pals.recipe-authoring-manifest.v1",
            "recipe_id": recipe_id,
            "revision": revision,
            "kind": "exact_target_proof",
            "source_author_principal": author,
            "author_profile": {
                "schema_version": "pals.recipe-author-profile.v1",
                "source_author_principal": author,
            },
            "toolchain": {"toolchain_id": toolchain_id, "fingerprint": fingerprint},
            "imports": ["Mathlib"],
            "environment": {"namespace": None, "opens": []},
            "target_source": target.proposition,
            "proof_body": source[len(prefix) : -1],
        }
        raw = rfc8785.dumps(manifest)
        checked = RecipeAuthoringManifestV1.parse(raw)
        if RecipeMaterializerV1.materialize(checked) != source.encode():
            raise ValueError(
                "materialized source bytes differ from reviewed runtime source"
            )
    else:
        raw = rfc8785.dumps(manifest)
        parse_manifest(raw)  # Existing release policy; do not repair or rewrite source.
    proposal = {
        "schema_version": "pals.math-question-search-proposal.v1",
        "status": "prepared_not_admitted",
        "admission_policy": admission_policy,
        "recipe_id": recipe_id,
        "recipe_revision": revision,
        "target": target.as_dict(),
        **bindings,
        "metadata": metadata,
        "reviewed_explanation": result["explanation"],
        "preparation_review": review,
        "remaining_requirements": [
            "production pinned verifier admission",
            "actual compiler receipt",
            "independently signed Recipe search entry review",
            "release-owned search entry admission",
        ],
    }
    return {
        "authoring-manifest.json": raw,
        "source.lean": source.encode(),
        "search-proposal.json": rfc8785.dumps(proposal),
    }


def write_outputs(directory: Path, files: dict[str, bytes]) -> None:
    if directory.resolve().is_relative_to(ROOT):
        raise ValueError("output directory must be outside the repository")
    directory.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        path = directory / name
        if path.exists() and path.read_bytes() != data:
            raise ValueError("refusing to overwrite different prepared output")
    for name, data in files.items():
        path = directory / name
        if not path.exists():
            with path.open("xb") as handle:
                handle.write(data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "runtime-result",
        "review-evidence",
        "metadata",
        "toolchain-json",
        "output-dir",
    ):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("recipe-id", "author", "toolchain-id"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--revision", type=int, default=1)
    parser.add_argument(
        "--admission-policy", choices=("raw", "materialized"), default="raw"
    )
    args = parser.parse_args()
    from app.core.duplicate_json import decode_json_object

    files = prepare(
        args.runtime_result.read_bytes(),
        decode_json_object(args.review_evidence.read_bytes()),
        decode_json_object(args.metadata.read_bytes()),
        recipe_id=args.recipe_id,
        revision=args.revision,
        author=args.author,
        toolchain_id=args.toolchain_id,
        fingerprint=decode_json_object(args.toolchain_json.read_bytes()),
        admission_policy=args.admission_policy,
    )
    write_outputs(args.output_dir, files)
    print(json.dumps({"status": "prepared_not_admitted", "files": sorted(files)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
