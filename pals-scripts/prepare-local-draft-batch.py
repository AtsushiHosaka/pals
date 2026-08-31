"""Prepare a fail-closed SQL transaction for a locally authored Draft batch.

This script intentionally only prepares SQL.  The caller must execute that SQL
against the local legacy `dsp_drafts` table, after the transaction's own
preconditions have been rechecked by Postgres.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path
from typing import Any

EXPECTED_BINDING = {
    "provider": "openai",
    "model": "text-embedding-3-small",
    "dimension": 384,
    "canonicalizer": "openmath-cdbase-alpha-c14n-v2",
    "endpoint": "https://api.openai.com/v1",
    "deployment": "text-embedding-3-small",
    "revision": "openai-release-2024-01-25",
}


def _is_typed_authoring_manifest_schema(schema_version: object) -> bool:
    return (
        isinstance(schema_version, str)
        and schema_version.startswith("pals.typed-")
        and "-authoring-manifest" in schema_version
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument(
        "--cards-key",
        help="Optional top-level list key to load instead of the default cards selection.",
    )
    parser.add_argument("--expected-existing-count", type=int, required=True)
    parser.add_argument("--sql-output", type=Path, required=True)
    return parser.parse_args()


def dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key.strip()] = value
    return values


def cards_from_payload(payload: object, *, cards_key: str | None) -> list[dict[str, Any]]:
    required = {
        "id",
        "canonical_statement",
        "openmath_xml",
        "proof_strategy",
        "sketch_steps",
    }
    if not isinstance(payload, dict):
        raise TypeError("manifest root must be an object")
    if _is_typed_authoring_manifest_schema(payload.get("schema_version")):
        raise ValueError(
            "typed authoring manifests are forbidden in the generic local DB loader"
        )
    if cards_key is not None:
        cards = payload.get(cards_key)
        if not isinstance(cards, list):
            raise ValueError(f"manifest has no card list named `{cards_key}`")
    elif isinstance(payload.get("cards"), list):
        cards = payload["cards"]
    else:
        cards = [
            item
            for value in payload.values()
            if isinstance(value, list)
            for item in value
        ]
    if not cards or not all(isinstance(card, dict) and required <= set(card) for card in cards):
        raise ValueError("manifest contains an invalid Draft card")
    return cards


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def main() -> None:
    args = parse_args()
    if args.expected_existing_count < 0:
        raise ValueError("expected existing count must be non-negative")
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "pals-agent"))
    from pals_agent.draft_catalog import draft_embedding_text, validate_draft_collection
    from pals_agent.draft_embeddings import (
        OpenAIEmbeddingModel,
        embedding_to_pgvector_literal,
    )
    from pals_agent.models import ProofDraft

    cards = cards_from_payload(
        json.loads(args.manifest.read_text(encoding="utf-8")),
        cards_key=args.cards_key,
    )
    drafts = tuple(
        ProofDraft(
            id=card["id"],
            matched_prompt=card["canonical_statement"],
            openmath_xml=card["openmath_xml"],
            proof_strategy=card["proof_strategy"],
            sketch_steps=tuple(card["sketch_steps"]),
        )
        for card in cards
    )
    validate_draft_collection(drafts)
    canonical_texts = [draft_embedding_text(draft) for draft in drafts]
    if len({draft.id for draft in drafts}) != len(drafts):
        raise ValueError("manifest contains duplicate Draft IDs")
    if len(set(canonical_texts)) != len(canonical_texts):
        raise ValueError("manifest contains duplicate canonical OpenMath")

    env = dotenv(root / ".env.local")
    api_key = env.get("PALS_OPENAI_API_KEY") or env.get("OPENAI_API_KEY")
    revision = env.get("PALS_DRAFT_EMBEDDING_REVISION") or env.get(
        "PALS_DRAFT_EMBEDDING_DIGEST"
    )
    if not api_key or not revision:
        raise ValueError("local environment lacks the pinned OpenAI embedding binding")
    model = OpenAIEmbeddingModel(
        api_key=api_key,
        revision=revision,
        model=env.get("PALS_DRAFT_EMBEDDING_MODEL", EXPECTED_BINDING["model"]),
        dimension=int(env.get("PALS_DRAFT_EMBEDDING_DIM", EXPECTED_BINDING["dimension"])),
        base_url=env.get("PALS_OPENAI_BASE_URL", EXPECTED_BINDING["endpoint"]),
        timeout_seconds=float(env.get("PALS_DRAFT_EMBEDDING_TIMEOUT_SECONDS", "60")),
        endpoint_identity_override=env.get("PALS_DRAFT_EMBEDDING_ENDPOINT_IDENTITY"),
        deployment_identity_override=env.get("PALS_DRAFT_EMBEDDING_DEPLOYMENT_IDENTITY"),
    )
    actual_binding = {
        "provider": "openai",
        "model": model.model,
        "dimension": model.dimension,
        "canonicalizer": EXPECTED_BINDING["canonicalizer"],
        "endpoint": model.endpoint_identity,
        "deployment": model.deployment_identity,
        "revision": model.revision,
    }
    if actual_binding != EXPECTED_BINDING:
        raise ValueError("embedding binding differs from the local catalog")

    rows: list[tuple[str, str, str, str, str, str]] = []
    for draft, canonical_text in zip(drafts, canonical_texts, strict=True):
        embedding = model.embed(canonical_text)
        if len(embedding) != EXPECTED_BINDING["dimension"]:
            raise ValueError(f"{draft.id}: embedding dimension mismatch")
        rows.append(
            (
                draft.id,
                draft.matched_prompt,
                draft.proof_strategy,
                json.dumps(list(draft.sketch_steps), ensure_ascii=False, separators=(",", ":")),
                embedding_to_pgvector_literal(embedding),
                draft.openmath_xml,
            )
        )

    copy_data = io.StringIO()
    csv.writer(copy_data, lineterminator="\n").writerows(rows)
    ids = ", ".join(sql_literal(draft.id) for draft in drafts)
    binding = EXPECTED_BINDING
    sql = f'''BEGIN;
SELECT pg_advisory_xact_lock(hashtext('pals-local-draft-batch'));
DO $$
BEGIN
  IF (SELECT relkind FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = 'public' AND c.relname = 'dsp_drafts') <> 'r' THEN
    RAISE EXCEPTION 'dsp_drafts must be the local legacy table';
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'pfi_catalog_generations') THEN
    RAISE EXCEPTION 'PFI generation tables are present; legacy loader is forbidden';
  END IF;
  IF (SELECT count(*) FROM public.dsp_drafts) <> {args.expected_existing_count} THEN
    RAISE EXCEPTION 'unexpected existing draft count';
  END IF;
  IF (SELECT count(*) FROM public.pals_agent_draft_catalog_metadata WHERE catalog = 'dsp_drafts' AND embedding_provider = {sql_literal(binding['provider'])} AND embedding_model = {sql_literal(binding['model'])} AND embedding_dimension = {binding['dimension']} AND canonicalizer_version = {sql_literal(binding['canonicalizer'])} AND embedding_endpoint = {sql_literal(binding['endpoint'])} AND embedding_deployment = {sql_literal(binding['deployment'])} AND embedding_revision = {sql_literal(binding['revision'])}) <> 1 THEN
    RAISE EXCEPTION 'embedding metadata differs from the expected local catalog';
  END IF;
  IF EXISTS (SELECT 1 FROM public.dsp_drafts WHERE id IN ({ids})) THEN
    RAISE EXCEPTION 'one or more Draft IDs already exist';
  END IF;
END $$;
COPY public.dsp_drafts (id, canonical_statement, proof_strategy, sketch_steps, embedding, openmath_xml) FROM STDIN WITH (FORMAT csv);
{copy_data.getvalue()}\\.
DO $$
BEGIN
  IF (SELECT count(*) FROM public.dsp_drafts WHERE id IN ({ids})) <> {len(drafts)} THEN
    RAISE EXCEPTION 'not all batch rows were inserted';
  END IF;
  IF EXISTS (SELECT 1 FROM public.dsp_drafts WHERE id IN ({ids}) AND vector_dims(embedding) <> {binding['dimension']}) THEN
    RAISE EXCEPTION 'inserted embedding dimension mismatch';
  END IF;
END $$;
COMMIT;
'''
    args.sql_output.write_text(sql, encoding="utf-8")
    print(f"prepared_rows={len(rows)} embedding_dimension={binding['dimension']}")


if __name__ == "__main__":
    main()
