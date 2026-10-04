#!/usr/bin/env python3
"""Prepare release inputs from the reviewed square corpus and an observed verifier fingerprint.

Does not admit a recipe or invent compiler evidence. Run using pals-api/.venv/bin/python;
then use the existing release-owned Recipe and alignment admission commands.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pals-api"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toolchain-json", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    from app.domain.pfi_draft_catalog import (
        PFIDraftPayloadCanonicalizerV4,
        PFIDraftPayloadV1,
    )
    from app.domain.recipe_alignment_admission import AlignmentAuthoringManifestV1
    from app.domain.recipe_catalog_admission import (
        RecipeAuthoringManifestV1,
        RecipeMaterializerV1,
        canonical_json_bytes,
    )

    corpus = json.loads(
        (ROOT / "pals-scripts/fixtures/lean-recipe-corpus.v1.json").read_text()
    )
    square = corpus["square_recipe"]
    fingerprint = json.loads(args.toolchain_json.read_text())
    principal = square["source_author_principal"]
    authoring = {
        "schema_version": "pals.recipe-authoring-manifest.v1",
        "recipe_id": square["recipe_id"],
        "revision": square["revision"],
        "kind": "exact_target_proof",
        "source_author_principal": principal,
        "author_profile": {
            "schema_version": "pals.recipe-author-profile.v1",
            "source_author_principal": principal,
        },
        "toolchain": {
            "toolchain_id": "square.pinned."
            + hashlib.sha256(canonical_json_bytes(fingerprint)).hexdigest()[:16],
            "fingerprint": fingerprint,
        },
        "imports": ["Mathlib"],
        "environment": {"namespace": None, "opens": []},
        "target_source": square["target_source"],
        "proof_body": square["proof_body"],
    }
    manifest = RecipeAuthoringManifestV1.parse(canonical_json_bytes(authoring))
    draft_fields = {
        **square["draft"],
        "sketch_steps": tuple(square["draft"]["sketch_steps"]),
    }
    draft = PFIDraftPayloadCanonicalizerV4().canonicalize(
        PFIDraftPayloadV1(**draft_fields)
    )
    alignment = {
        "schema_version": "pals.alignment-authoring-manifest.v1",
        "alignment_id": "continuous_square.explicit-epsilon-delta",
        "revision": 1,
        "draft_revision": {
            "catalog_id": draft.reference.catalog_id,
            "draft_id": draft.reference.draft_id,
            "draft_payload_sha256": draft.reference.draft_payload_sha256,
            "canonicalizer_version": draft.reference.canonicalizer_version,
        },
        "recipe_id": manifest.recipe_id,
        "recipe_revision": manifest.revision,
        "relation": "exact_target",
        "required_proof_method_tag": square["proof_method_tag"],
        "review": square["alignment_review"],
    }
    alignment_bytes = canonical_json_bytes(alignment)
    AlignmentAuthoringManifestV1.parse(alignment_bytes)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, payload in {
        "square-authoring-manifest.json": manifest.canonical_bytes,
        "square-alignment-manifest.json": alignment_bytes,
        "square-materialized.lean": RecipeMaterializerV1.materialize(manifest),
    }.items():
        destination = args.output_dir / name
        if destination.exists() and destination.read_bytes() != payload:
            raise ValueError(
                f"Refusing to overwrite different release input: {destination.name}"
            )
    (args.output_dir / "square-authoring-manifest.json").write_bytes(
        manifest.canonical_bytes
    )
    (args.output_dir / "square-alignment-manifest.json").write_bytes(alignment_bytes)
    (args.output_dir / "square-materialized.lean").write_bytes(
        RecipeMaterializerV1.materialize(manifest)
    )
    print(
        json.dumps(
            {
                "status": "prepared_not_admitted",
                "manifest_sha256": manifest.manifest_sha256,
                "draft_payload_sha256": draft.reference.draft_payload_sha256,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
