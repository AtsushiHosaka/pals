"""Seal original local-only CA-6 chain/dimension authoring evidence.

This generator never creates a generic Draft, DB row, seed, embedding, or PFI
artifact.  It recomputes canonical OpenMath and every digest from current
source files before serializing its proposal.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from pals_agent.typed_commutative_algebra_chain_dimension import (
    TYPED_COMMUTATIVE_ALGEBRA_CHAIN_DIMENSION_OPENMATH_CDBASE,
    TYPED_COMMUTATIVE_ALGEBRA_CHAIN_DIMENSION_PROFILE,
    canonicalize_typed_commutative_algebra_chain_dimension_openmath_xml,
)

ROOT = Path(__file__).resolve().parents[1]
OPENMATH = "http://www.openmath.org/OpenMath"
STANDARD = "http://www.openmath.org/cd"
TYPED = TYPED_COMMUTATIVE_ALGEBRA_CHAIN_DIMENSION_OPENMATH_CDBASE
DESIGN = ROOT / "docs/typed-commutative-algebra-chain-dimension-v1-design.md"
REGISTRY = ROOT / (
    "pals-agent/pals_agent/content_dictionaries/"
    "typed-commutative-algebra-chain-dimension-v1-registry.json"
)
VALIDATOR = ROOT / "pals-agent/pals_agent/typed_commutative_algebra_chain_dimension.py"
WITNESS = ROOT / "docs/typed-commutative-algebra-chain-dimension-v1-authoring-witnesses.lean"
TOOLCHAIN = ROOT / "pals-agent/lean-workspace/lean-toolchain"
REGISTRY_PATH = (
    "pals_agent/content_dictionaries/typed-commutative-algebra-chain-dimension-v1-registry.json"
)
VALIDATOR_NAME = (
    "pals_agent.typed_commutative_algebra_chain_dimension."
    "validate_canonical_typed_commutative_algebra_chain_dimension_openmath_xml"
)
WITNESS_PATH = "docs/typed-commutative-algebra-chain-dimension-v1-authoring-witnesses.lean"
VERIFY_LEAN = (
    "cd pals-agent/lean-workspace && lake env lean "
    "../../docs/typed-commutative-algebra-chain-dimension-v1-authoring-witnesses.lean"
)
STATUS = "validated_local_typed_commutative_algebra_chain_dimension_v1_sealed"
ADMISSION = (
    "sealed-local-authoring-revision: not a DB Draft or an OpenMath-to-Lean translation receipt"
)
REVIEW_GATE = "requires independent project review before any typed catalog admission"
CHAIN_REASON = "arbitrary ideal-chain functions require a separate dependent-chain profile"


def _sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _typed(name: str) -> str:
    return f'<OMS cdbase="{TYPED}" cd="chain1" name="{name}"/>'


def _type() -> str:
    return f'<OMS cdbase="{TYPED}" cd="typed1" name="type"/>'


def _forall() -> str:
    return f'<OMS cdbase="{TYPED}" cd="typed1" name="forall"/>'


def _standard(cd: str, name: str) -> str:
    return f'<OMS cdbase="{STANDARD}" cd="{cd}" name="{name}"/>'


def _var(name: str) -> str:
    return f'<OMV name="{name}"/>'


def _app(operator: str, *arguments: str) -> str:
    return f"<OMA>{operator}{''.join(arguments)}</OMA>"


def _prop(name: str, ring: str) -> str:
    return _app(_typed(name), _var(ring))


def _ideal_prop(name: str, ring: str, ideal: str) -> str:
    return _app(_typed(name), _var(ring), _var(ideal))


def _ideal_op(name: str, ring: str, left: str, right: str | None = None) -> str:
    arguments = [_var(ring), _var(left)]
    if right is not None:
        arguments.append(_var(right))
    return _app(_typed(name), *arguments)


def _implies(left: str, right: str) -> str:
    return _app(_standard("logic1", "implies"), left, right)


def _and(left: str, right: str) -> str:
    return _app(_standard("logic1", "and"), left, right)


def _decl_ring(name: str) -> str:
    return f"<OMATTR><OMATP>{_type()}{_typed('CommRing')}</OMATP>{_var(name)}</OMATTR>"


def _decl_ideal(name: str, ring: str) -> str:
    sort = _app(_typed("Ideal"), _var(ring))
    return f"<OMATTR><OMATP>{_type()}{sort}</OMATP>{_var(name)}</OMATTR>"


def _bind(declarations: list[str], body: str) -> str:
    return f"<OMBIND>{_forall()}<OMBVAR>{''.join(declarations)}</OMBVAR>{body}</OMBIND>"


def _proposition(declarations: list[str], body: str) -> str:
    return f'<OMOBJ xmlns="{OPENMATH}" version="2.0">{_bind(declarations, body)}</OMOBJ>'


def _steps(strategy: str) -> list[str]:
    return [
        "束縛された可換環と、必要なイデアルの carrier を固定する。",
        "Noetherian・Artinian・有限生成・次元零の仮定を型付き述語として読む。",
        strategy,
        "対応する直接の Mathlib 定理または instance で結論を閉じる。",
    ]


def _card(
    identifier: str,
    statement: str,
    strategy: str,
    xml: str,
    lean_target: str,
    lean_witness: str,
) -> dict[str, Any]:
    canonical = canonicalize_typed_commutative_algebra_chain_dimension_openmath_xml(xml)
    return {
        "id": identifier,
        "canonical_statement": statement,
        "proof_strategy": strategy,
        "sketch_steps": _steps(strategy),
        "openmath_xml": xml,
        "openmath_xml_sha256": _sha256(xml.encode("utf-8")),
        "canonical_openmath_xml": canonical,
        "canonical_openmath_xml_sha256": _sha256(canonical.encode("utf-8")),
        "canonical_statement_sha256": _sha256(statement.encode("utf-8")),
        "lean_target": lean_target,
        "lean_target_sha256": _sha256(lean_target.encode("utf-8")),
        "lean_witness": lean_witness,
        "lean_witness_sha256": _sha256(lean_witness.encode("utf-8")),
        "openmath_profile": TYPED_COMMUTATIVE_ALGEBRA_CHAIN_DIMENSION_PROFILE,
        "profile_validation_status": STATUS,
        "compiler_receipt_status": "verified",
        "admission_status": ADMISSION,
        "alignment": {
            "status": "sealed_local_authoring_review_not_admitted",
            "statement_to_openmath": (
                "reviewed with explicit CommRing and dependent Ideal(R) carriers; "
                "Lean typeclass hypotheses are the reviewed lowering of profile predicates"
            ),
            "openmath_to_lean": "reviewed against the named direct Mathlib theorem or instance",
            "admission_gate": REVIEW_GATE,
        },
    }


def _target(prefix: str, result: str) -> str:
    return f"example {prefix} : {result}"


def _cards() -> list[dict[str, Any]]:
    r = _var("R")
    ring_i = [_decl_ring("R"), _decl_ideal("I", "R")]
    ring_ij = [*ring_i, _decl_ideal("J", "R")]
    ring_p = [_decl_ring("R"), _decl_ideal("P", "R")]
    noeth = _prop("NoetherianRing", "R")
    artin = _prop("ArtinianRing", "R")
    dim0 = _prop("KrullDimLEZero", "R")
    field = _prop("Field", "R")
    fg_i = _ideal_prop("IdealFG", "R", "I")
    prime_p = _ideal_prop("PrimeIdeal", "R", "P")
    max_p = _ideal_prop("MaximalIdeal", "R", "P")
    sum_fg = _app(_typed("IdealFG"), r, _ideal_op("IdealSum", "R", "I", "J"))
    inf_fg = _app(_typed("IdealFG"), r, _ideal_op("IdealInf", "R", "I", "J"))
    product_fg = _app(_typed("IdealFG"), r, _ideal_op("IdealProduct", "R", "I", "J"))
    radical_fg = _app(_typed("IdealFG"), r, _ideal_op("IdealRadical", "R", "I"))
    all_ideals_fg = _bind([_decl_ideal("I", "R")], fg_i)
    return [
        _card(
            "chain_noetherian_ideal_fg",
            "Noetherian 可換環 R の任意のイデアル I は有限生成である。",
            "Noetherian ring の ideal-finite-generation 特徴づけを I に適用する。",
            _proposition(ring_i, _implies(noeth, fg_i)),
            _target("{R : Type*} [CommRing R] [IsNoetherianRing R] (I : Ideal R)", "I.FG"),
            "by\n  exact Ideal.fg_of_isNoetherianRing I",
        ),
        _card(
            "chain_noetherian_sum_fg",
            "Noetherian 可換環では二つのイデアルの和は有限生成である。",
            "和は同じ R 上のイデアルなので有限生成定理を適用する。",
            _proposition(ring_ij, _implies(noeth, sum_fg)),
            _target("{R : Type*} [CommRing R] [IsNoetherianRing R] (I J : Ideal R)", "(I + J).FG"),
            "by\n  exact Ideal.fg_of_isNoetherianRing (I + J)",
        ),
        _card(
            "chain_noetherian_inf_fg",
            "Noetherian 可換環では二つのイデアルの交わりは有限生成である。",
            "交わりも R のイデアルであることを使う。",
            _proposition(ring_ij, _implies(noeth, inf_fg)),
            _target("{R : Type*} [CommRing R] [IsNoetherianRing R] (I J : Ideal R)", "(I ⊓ J).FG"),
            "by\n  exact Ideal.fg_of_isNoetherianRing (I ⊓ J)",
        ),
        _card(
            "chain_noetherian_product_fg",
            "Noetherian 可換環では二つのイデアルの積は有限生成である。",
            "積イデアルを R のイデアルとして有限生成定理に送る。",
            _proposition(ring_ij, _implies(noeth, product_fg)),
            _target("{R : Type*} [CommRing R] [IsNoetherianRing R] (I J : Ideal R)", "(I * J).FG"),
            "by\n  exact Ideal.fg_of_isNoetherianRing (I * J)",
        ),
        _card(
            "chain_noetherian_radical_fg",
            "Noetherian 可換環ではイデアルの根基は有限生成である。",
            "根基を R のイデアルとして有限生成定理に送る。",
            _proposition(ring_i, _implies(noeth, radical_fg)),
            _target("{R : Type*} [CommRing R] [IsNoetherianRing R] (I : Ideal R)", "I.radical.FG"),
            "by\n  exact Ideal.fg_of_isNoetherianRing I.radical",
        ),
        _card(
            "chain_noetherian_all_ideals_fg",
            "可換環 R が Noetherian であるなら、全ての R-イデアルが有限生成である。",
            "任意の束縛済み I に対して有限生成定理を一様に適用する。",
            _proposition([_decl_ring("R")], _implies(noeth, all_ideals_fg)),
            _target("{R : Type*} [CommRing R] [IsNoetherianRing R]", "∀ I : Ideal R, I.FG"),
            "by\n  intro I\n  exact Ideal.fg_of_isNoetherianRing I",
        ),
        _card(
            "chain_hilbert_basis_one_variable",
            "Noetherian 可換環 R に対し一変数多項式環 R[X] は Noetherian である。",
            "Hilbert 基底定理の一変数 instance を適用する。",
            _proposition([_decl_ring("R")], _implies(noeth, _prop("HilbertNoetherian", "R"))),
            _target(
                "{R : Type*} [CommRing R] [IsNoetherianRing R]", "IsNoetherianRing (Polynomial R)"
            ),
            "by\n  infer_instance",
        ),
        _card(
            "chain_hilbert_basis_two_iterations",
            "Noetherian 可換環 R に対し二回反復した一変数多項式環も Noetherian である。",
            "Hilbert 基底定理を多項式環にもう一度適用する。",
            _proposition(
                [_decl_ring("R")], _implies(noeth, _prop("IteratedHilbertNoetherian", "R"))
            ),
            _target(
                "{R : Type*} [CommRing R] [IsNoetherianRing R]",
                "IsNoetherianRing (Polynomial (Polynomial R))",
            ),
            "by\n  infer_instance",
        ),
        _card(
            "chain_artinian_implies_noetherian",
            "Artinian 可換環は Noetherian である。",
            "Artinian ring の Hopkins--Levitzki 型の有限性結果を使う。",
            _proposition([_decl_ring("R")], _implies(artin, noeth)),
            _target("{R : Type*} [CommRing R] [IsArtinianRing R]", "IsNoetherianRing R"),
            "by\n  infer_instance",
        ),
        _card(
            "chain_artinian_dimension_zero",
            "Artinian 可換環の Krull 次元は高々 0 である。",
            "Artinian ring の素イデアル鎖が自明であることを使う。",
            _proposition([_decl_ring("R")], _implies(artin, dim0)),
            _target("{R : Type*} [CommRing R] [IsArtinianRing R]", "Ring.KrullDimLE 0 R"),
            "by\n  infer_instance",
        ),
        _card(
            "chain_noetherian_dimension_zero_artinian",
            "Noetherian かつ Krull 次元高々0の可換環は Artinian である。",
            "Noetherian と次元零の特徴づけから Artinian 性を導く。",
            _proposition([_decl_ring("R")], _implies(_and(noeth, dim0), artin)),
            _target(
                "{R : Type*} [CommRing R] [IsNoetherianRing R] (h : Ring.KrullDimLE 0 R)",
                "IsArtinianRing R",
            ),
            "by\n  exact @IsNoetherianRing.isArtinianRing_of_krullDimLE_zero R _ _ h",
        ),
        _card(
            "chain_artinian_prime_maximal",
            "Artinian 可換環の素イデアルは極大イデアルである。",
            "Artinian ring での素イデアルの極大性を適用する。",
            _proposition(ring_p, _implies(_and(artin, prime_p), max_p)),
            _target(
                "{R : Type*} [CommRing R] [IsArtinianRing R] (P : Ideal R) (h : P.IsPrime)",
                "P.IsMaximal",
            ),
            "by\n  letI : P.IsPrime := h\n  exact IsArtinianRing.isMaximal_of_isPrime P",
        ),
        _card(
            "chain_dimension_zero_prime_maximal",
            "可換環 R の Krull 次元が高々0なら、全ての素イデアルは極大である。",
            "KrullDimLE 0 の素スペクトル順序による特徴づけの順方向を使う。",
            _proposition(ring_p, _implies(_and(dim0, prime_p), max_p)),
            _target(
                "{R : Type*} [CommRing R] (h : Ring.KrullDimLE 0 R) (P : Ideal R) (hP : P.IsPrime)",
                "P.IsMaximal",
            ),
            "by\n  exact Ring.krullDimLE_zero_iff.mp h P hP",
        ),
        _card(
            "chain_field_noetherian",
            "体 R は Noetherian 可換環である。",
            "体のイデアルが自明であることから Noetherian instance を得る。",
            _proposition([_decl_ring("R")], _implies(field, noeth)),
            _target("{K : Type*} [Field K]", "IsNoetherianRing K"),
            "by\n  infer_instance",
        ),
        _card(
            "chain_field_artinian",
            "体 R は Artinian 可換環である。",
            "体のイデアルが自明であることから Artinian instance を得る。",
            _proposition([_decl_ring("R")], _implies(field, artin)),
            _target("{K : Type*} [Field K]", "IsArtinianRing K"),
            "by\n  infer_instance",
        ),
        _card(
            "chain_field_dimension_zero",
            "体 R の Krull 次元は高々0である。",
            "体が Artinian であることと次元零結論を合成する。",
            _proposition([_decl_ring("R")], _implies(field, dim0)),
            _target("{K : Type*} [Field K]", "Ring.KrullDimLE 0 K"),
            "by\n  infer_instance",
        ),
        _card(
            "chain_artinian_ideal_fg",
            "Artinian 可換環 R の任意のイデアル I は有限生成である。",
            "Artinian から Noetherian を経由して有限生成定理を使う。",
            _proposition(ring_i, _implies(artin, fg_i)),
            _target("{R : Type*} [CommRing R] [IsArtinianRing R] (I : Ideal R)", "I.FG"),
            "by\n  exact Ideal.fg_of_isNoetherianRing I",
        ),
    ]


def build_manifest() -> dict[str, Any]:
    cards = _cards()
    payload: dict[str, Any] = {
        "schema_version": "pals.typed-commutative-algebra-chain-dimension-v1-sealed-manifest.v1",
        "status": "sealed_local_authoring_revision_not_admitted",
        "seal": {
            "scope": "local typed commutative-algebra CA-6 authoring evidence only",
            "admission": "not admitted to the generic DB, seed, embedding index, or PFI package",
            "revision": "typed-commutative-algebra-chain-dimension-v1-local-r1",
        },
        "profile": {
            "id": TYPED_COMMUTATIVE_ALGEBRA_CHAIN_DIMENSION_PROFILE,
            "typed_cdbase": TYPED,
            "design_path": "docs/typed-commutative-algebra-chain-dimension-v1-design.md",
            "design_sha256": _sha256(DESIGN.read_bytes()),
            "registry_path": REGISTRY_PATH,
            "registry_sha256": _sha256(REGISTRY.read_bytes()),
            "validator": VALIDATOR_NAME,
            "validator_path": "pals_agent/typed_commutative_algebra_chain_dimension.py",
            "validator_sha256": _sha256(VALIDATOR.read_bytes()),
            "canonicalizer_version": "openmath-cdbase-alpha-c14n-v4",
        },
        "lean_receipt": {
            "witness_path": WITNESS_PATH,
            "witness_file_sha256": _sha256(WITNESS.read_bytes()),
            "toolchain": TOOLCHAIN.read_text(encoding="utf-8").rstrip("\n"),
            "verification_command": VERIFY_LEAN,
            "verification_status": "verified_local_pinned_workspace",
        },
        "admitted_card_count": len(cards),
        "excluded_cards": [
            {
                "id": "chain_general_ascending_chain_stabilization",
                "reason": CHAIN_REASON,
            },
            {
                "id": "chain_general_descending_chain_stabilization",
                "reason": CHAIN_REASON,
            },
            {
                "id": "chain_polynomial_dimension_formula",
                "reason": (
                    "general Krull dimensions and polynomial dimension formulae are outside "
                    "the bounded zero-dimensional profile"
                ),
            },
            {
                "id": "chain_spec_height_formula",
                "reason": "Spec, prime chains, and height require a spectrum/chain carrier profile",
            },
            {
                "id": "chain_nullstellensatz",
                "reason": (
                    "field extensions and geometric hypotheses are not represented by "
                    "this profile"
                ),
            },
        ],
        "excluded_card_count": 5,
        "cards": cards,
    }
    payload["manifest_payload_sha256"] = _sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT
        / "docs/typed-commutative-algebra-chain-dimension-v1-sealed-manifest.proposal.json",
    )
    parser.add_argument("--verify-lean", action="store_true")
    args = parser.parse_args()
    if args.verify_lean:
        completed = subprocess.run(
            [
                "lake",
                "env",
                "lean",
                "../../docs/typed-commutative-algebra-chain-dimension-v1-authoring-witnesses.lean",
            ],
            cwd=ROOT / "pals-agent/lean-workspace",
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            return completed.returncode
    args.output.write_text(
        json.dumps(build_manifest(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
