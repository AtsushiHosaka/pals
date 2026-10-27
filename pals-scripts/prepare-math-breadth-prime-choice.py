"""Prepare a Lean-checked ideal-theory proposal through the existing authoring adapter.

No embedding, signing, admission, activation, provider, or database operation occurs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from xml.sax.saxutils import quoteattr

from pals_agent.breadth_evaluation import environment_binding, load_corpus
from pals_agent.lean import LeanVerifier
from pals_agent.typed_catalog_expansion import witness_source
from pals_agent.typed_commutative_algebra import (
    canonicalize_typed_commutative_algebra_openmath_xml as canonicalize,
)
from pals_agent.typed_local_catalog import load_typed_local_catalog_manifest

ROOT = Path(__file__).resolve().parents[1]
PROFILE = "typed-commutative-algebra-v1"
TYPED = "urn:pals:openmath:typed-commutative-algebra:v1"


def digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def sym(cd: str, name: str, base: str = TYPED) -> str:
    return f"<OMS cdbase={quoteattr(base)} cd={quoteattr(cd)} name={quoteattr(name)}/>"


def var(name: str) -> str:
    return f"<OMV name={quoteattr(name)}/>"


def app(head: str, *args: str) -> str:
    return "<OMA>" + head + "".join(args) + "</OMA>"


def ideal(name: str, *args: str) -> str:
    return app(sym("commalg1", name), *args)


def logic(name: str, *args: str) -> str:
    return app(sym("logic1", name, "http://www.openmath.org/cd"), *args)


def statement_xml() -> str:
    r, i, j, p = map(var, ("R", "I", "J", "P"))
    declarations = [("R", sym("commalg1", "CommRing"))] + [
        (name, ideal("Ideal", r)) for name in ("I", "J", "P")
    ]
    binders = "".join(
        "<OMATTR><OMATP>"
        + sym("typed1", "type")
        + sort
        + "</OMATP>"
        + var(name)
        + "</OMATTR>"
        for name, sort in declarations
    )
    formula = logic(
        "implies",
        logic(
            "and",
            ideal("is_prime_ideal", r, p),
            ideal("ideal_le", r, ideal("ideal_inf", r, i, j), p),
        ),
        logic("or", ideal("ideal_le", r, i, p), ideal("ideal_le", r, j, p)),
    )
    return canonicalize(
        '<OMOBJ xmlns="http://www.openmath.org/OpenMath" version="2.0">'
        "<OMBIND>"
        + sym("typed1", "forall")
        + "<OMBVAR>"
        + binders
        + "</OMBVAR>"
        + formula
        + "</OMBIND></OMOBJ>"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lean-project", type=Path, required=True)
    parser.add_argument("--elan-home", type=Path, default=Path.home() / ".elan")
    args = parser.parse_args()
    corpus_dir = ROOT / "pals-agent/testdata/mathematical-breadth-v1"
    corpus_path = corpus_dir / "corpus.json"
    bound_corpus = load_corpus(corpus_path)
    corpus = json.loads(corpus_path.read_text())
    case = next(
        c for c in corpus["cases"] if c["id"] == "ug.commalg.prime_intersection"
    )
    lean = (corpus_dir / case["source_path"]).read_text()
    declaration = lean.split("theorem prime_intersection_choice", 1)[1]
    target, proof = declaration.split(":= by", 1)
    card = {
        "id": "mrd_t6_prime_intersection_choice",
        "canonical_statement": case["statement"],
        "proof_strategy": (
            "Choose elements outside the prime ideal "
            "and apply absorption and primality."
        ),
        "sketch_steps": case["proof_outline"],
        "openmath_xml": statement_xml(),
        "lean_target": "example " + target.strip(),
        "lean_witness": "by" + proof.rstrip(),
    }
    source = witness_source([card])
    project = args.lean_project.resolve(strict=True)
    pins = corpus["toolchain"]
    binding = environment_binding(bound_corpus, project)
    verifier = LeanVerifier(
        lean_binary=str(args.elan_home / "bin/lean"),
        lake_binary=str(args.elan_home / "bin/lake"),
        project_dir=project,
        timeout_seconds=45,
        elan_home=str(args.elan_home),
        child_path=f"{args.elan_home / 'bin'}:/usr/bin:/bin",
    )
    result = verifier.verify(source)
    if not result.success:
        raise RuntimeError("Actual Lean check failed: " + str(result.diagnostics))
    if (
        environment_binding(bound_corpus, project) != binding
        or load_corpus(corpus_path) != bound_corpus
    ):
        raise ValueError("Authoring inputs changed during verification")
    out = ROOT / "docs/mathematics-roadmap-2026-10-28"
    out.mkdir(parents=True, exist_ok=True)
    witness = out / "t6-prime-intersection-choice.lean"
    witness.write_text(source)
    agent = ROOT / "pals-agent/pals_agent"
    manifest = {
        "schema_version": "pals.typed-catalog-expansion-batch.v1",
        "profile_id": PROFILE,
        "cards": [card],
        "evidence": {
            "witness_path": str(witness.relative_to(ROOT)),
            "witness_sha256": digest(source.encode()),
            "toolchain": pins["lean_toolchain"],
            "mathlib_revision": pins["mathlib_revision"],
            "validator_sha256": digest(
                (agent / "typed_commutative_algebra.py").read_bytes()
            ),
            "registry_sha256": digest(
                (
                    agent / "content_dictionaries" / f"{PROFILE}-registry.json"
                ).read_bytes()
            ),
        },
    }
    path = out / "t6-prime-intersection-choice.proposal.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    loaded = load_typed_local_catalog_manifest(path, repository_root=ROOT)
    print(
        f"Compiled witness; loaded {loaded.manifest_digest}; status={loaded.authoring_status}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
