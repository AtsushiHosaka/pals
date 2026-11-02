#!/usr/bin/env python3
"""Reseal the additive pals2 registry and every digest bound to the OpenMath v4 contract.

Run from the parent repository after the catalog vocabulary changes. The registry only grows:
removing or re-signing a symbol would invalidate rows that are already stored. Nothing here calls
a service; commit and deploy the worker and API together with the resulting files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VOCABULARY = ROOT / "pals-agent/testdata/textbook-catalog-v1/generated/vocabulary.json"
AGENT_REGISTRY = ROOT / "pals-agent/pals_agent/contracts/openmath-pals2-symbols-v1.json"
API_REGISTRY = ROOT / "pals-api/app/domain/openmath_pals2_symbols_v1.json"
AGENT_OPENMATH = ROOT / "pals-agent/pals_agent/openmath.py"
AGENT_CONTRACT = ROOT / "pals-agent/pals_agent/openmath_v4_contract.py"
API_OPENMATH = ROOT / "pals-api/app/domain/openmath_v4.py"
AGENT_VECTORS = ROOT / "pals-agent/pals_agent/contracts/openmath-cdbase-alpha-c14n-v4-vectors.json"
VECTOR_COPIES = (
    ROOT / "pals-api/app/domain/openmath_c14n_v4_vectors.json",
    ROOT / "specs/lean-recipe-catalog/openmath-cdbase-alpha-c14n-v4-vectors.json",
)
_HEX = "[0-9a-f]{64}"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def registry_bytes(existing: bytes | None, vocabulary: dict[str, dict]) -> bytes:
    symbols = dict(json.loads(existing)["symbols"]) if existing else {}
    for name, spec in vocabulary.items():
        signature = {"args": spec["args"], "returns": spec["returns"]}
        if symbols.setdefault(name, signature) != signature:
            raise SystemExit(f"pals2 symbol {name} changed signature; register a new name instead")
    document = {
        "schema_version": "pals.openmath-pals2-symbols.v1",
        "cdbase": "urn:pals:openmath:cd:v1",
        "cd": "pals2",
        "symbols": dict(sorted(symbols.items())),
    }
    return (json.dumps(document, indent=1, ensure_ascii=False) + "\n").encode()


def _replace_pin(path: Path, pattern: str, digest: str) -> None:
    text, count = re.subn(pattern, lambda match: match.group(1) + digest, path.read_text())
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one pin for {pattern}")
    path.write_text(text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keep-registry", action="store_true",
                        help="keep the registry as it is and reseal only the digests")
    args = parser.parse_args()
    existing = AGENT_REGISTRY.read_bytes() if AGENT_REGISTRY.exists() else None
    if args.keep_registry:
        if existing is None:
            raise SystemExit("no registry to keep")
        registry = existing
    else:
        registry = registry_bytes(existing, json.loads(VOCABULARY.read_text())["symbols"])
    AGENT_REGISTRY.write_bytes(registry)
    API_REGISTRY.write_bytes(registry)

    registry_sha = _sha256(registry)
    _replace_pin(AGENT_OPENMATH, rf'(_PALS2_SYMBOLS_SHA256 = "){_HEX}', registry_sha)
    _replace_pin(API_OPENMATH, rf'(_PALS2_SYMBOLS_SHA256 = "){_HEX}', registry_sha)

    source_sha = _sha256(AGENT_OPENMATH.read_bytes())
    _replace_pin(AGENT_VECTORS, rf'("source_sha256": "){_HEX}', source_sha)
    vectors = AGENT_VECTORS.read_bytes()
    for copy in VECTOR_COPIES:
        copy.write_bytes(vectors)
    vectors_sha = _sha256(vectors)
    _replace_pin(AGENT_CONTRACT, rf'(_ARTIFACT_SHA256 = "){_HEX}', vectors_sha)
    _replace_pin(
        API_OPENMATH, rf'(OPENMATH_V4_VECTOR_ARTIFACT_SHA256 = \(\s*"){_HEX}', vectors_sha
    )
    _replace_pin(
        API_OPENMATH, rf'(OPENMATH_V4_REFERENCE_SOURCE_SHA256 = \(\s*"){_HEX}', source_sha
    )
    print(
        json.dumps(
            {
                "symbols": len(json.loads(registry)["symbols"]),
                "registry_sha256": registry_sha,
                "source_sha256": source_sha,
                "vectors_sha256": vectors_sha,
            },
            indent=1,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
