"""Prepare, but never execute, a typed local catalog SQL transaction.

Only sealed, isolated typed authoring manifests supported by
``pals_agent.typed_local_catalog`` are accepted.  The generic Draft loader,
legacy Draft table, PFI generation tables, and seed inputs are never read.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

EXPECTED_EMBEDDING: dict[str, str | int] = {
    "provider": "openai",
    "model": "text-embedding-3-small",
    "dimension": 384,
    "endpoint": "https://api.openai.com/v1",
    "deployment": "text-embedding-3-small",
    "revision": "openai-release-2024-01-25",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
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


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "pals-agent"))
    from pals_agent.draft_embeddings import OpenAIEmbeddingModel
    from pals_agent.typed_local_catalog import (
        TypedEmbeddingBinding,
        load_typed_local_catalog_manifest,
        prepare_typed_local_catalog_sql,
        typed_catalog_embedding_text,
    )

    catalog = load_typed_local_catalog_manifest(args.manifest, repository_root=root)
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
        model=env.get("PALS_DRAFT_EMBEDDING_MODEL", "text-embedding-3-small"),
        dimension=int(env.get("PALS_DRAFT_EMBEDDING_DIM", "384")),
        base_url=env.get("PALS_OPENAI_BASE_URL", "https://api.openai.com/v1"),
        timeout_seconds=float(env.get("PALS_DRAFT_EMBEDDING_TIMEOUT_SECONDS", "60")),
        endpoint_identity_override=env.get("PALS_DRAFT_EMBEDDING_ENDPOINT_IDENTITY"),
        deployment_identity_override=env.get(
            "PALS_DRAFT_EMBEDDING_DEPLOYMENT_IDENTITY"
        ),
    )
    binding = TypedEmbeddingBinding(
        provider="openai",
        model=model.model,
        dimension=model.dimension,
        endpoint=model.endpoint_identity,
        deployment=model.deployment_identity,
        revision=model.revision,
    )
    actual = {
        "provider": binding.provider,
        "model": binding.model,
        "dimension": binding.dimension,
        "endpoint": binding.endpoint,
        "deployment": binding.deployment,
        "revision": binding.revision,
    }
    if actual != EXPECTED_EMBEDDING:
        raise ValueError(
            "embedding binding differs from the typed local catalog binding"
        )
    embeddings = [
        model.embed(typed_catalog_embedding_text(card)) for card in catalog.cards
    ]
    sql = prepare_typed_local_catalog_sql(
        catalog,
        embedding_binding=binding,
        embeddings=embeddings,
    )
    args.sql_output.write_text(sql, encoding="utf-8")
    print(
        f"prepared_profile={catalog.profile.profile_id} "
        f"prepared_rows={len(catalog.cards)} embedding_dimension={binding.dimension}"
    )


if __name__ == "__main__":
    main()
