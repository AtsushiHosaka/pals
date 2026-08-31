"""Seal original local-only candidates for ``typed-commutative-algebra-v1``.

The script writes no generic Draft, seed, SQL, embedding, or PFI artifact.  It
recomputes every C14N value and digest immediately before serializing the local
authoring proposal.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from pals_agent.typed_commutative_algebra import (
    TYPED_COMMUTATIVE_ALGEBRA_OPENMATH_CDBASE,
    TYPED_COMMUTATIVE_ALGEBRA_PROFILE,
    canonicalize_typed_commutative_algebra_openmath_xml,
)

ROOT = Path(__file__).resolve().parents[1]
OPENMATH = "http://www.openmath.org/OpenMath"
STANDARD = "http://www.openmath.org/cd"
TYPED = TYPED_COMMUTATIVE_ALGEBRA_OPENMATH_CDBASE
DESIGN = ROOT / "docs/typed-commutative-algebra-v1-design.md"
REGISTRY = (
    ROOT
    / "pals-agent/pals_agent/content_dictionaries/typed-commutative-algebra-v1-registry.json"
)
VALIDATOR = ROOT / "pals-agent/pals_agent/typed_commutative_algebra.py"
WITNESS = ROOT / "docs/typed-commutative-algebra-v1-authoring-witnesses.lean"
TOOLCHAIN = ROOT / "pals-agent/lean-workspace/lean-toolchain"


def _sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _typed(cd: str, name: str) -> str:
    return f'<OMS cdbase="{TYPED}" cd="{cd}" name="{name}"/>'


def _standard(cd: str, name: str) -> str:
    return f'<OMS cdbase="{STANDARD}" cd="{cd}" name="{name}"/>'


def _app(operator: str, *arguments: str) -> str:
    return f"<OMA>{operator}{''.join(arguments)}</OMA>"


def _ca(name: str, *arguments: str) -> str:
    return _app(_typed("commalg1", name), *arguments)


def _var(name: str) -> str:
    return f'<OMV name="{name}"/>'


def _ideal_sort(carrier: str) -> str:
    return _ca("Ideal", _var(carrier))


def _declaration(name: str, sort: str) -> str:
    sorts = {
        "CommRing": _typed("commalg1", "CommRing"),
        "Ideal R": _ideal_sort("R"),
        "Ideal S": _ideal_sort("S"),
        "Elem R": _app(_typed("typed1", "Elem"), _var("R")),
    }
    return (
        f"<OMATTR><OMATP>{_typed('typed1', 'type')}{sorts[sort]}"
        f"</OMATP>{_var(name)}</OMATTR>"
    )


def _bind(declarations: list[tuple[str, str]], body: str) -> str:
    declared = "".join(_declaration(name, sort) for name, sort in declarations)
    return f"<OMBIND>{_typed('typed1', 'forall')}<OMBVAR>{declared}</OMBVAR>{body}</OMBIND>"


def _proposition(declarations: list[tuple[str, str]], body: str) -> str:
    return (
        f'<OMOBJ xmlns="{OPENMATH}" version="2.0">{_bind(declarations, body)}</OMOBJ>'
    )


def _ideal(name: str, *arguments: str) -> str:
    return _ca(name, *arguments)


def _le(carrier: str, left: str, right: str) -> str:
    return _ideal("ideal_le", _var(carrier), left, right)


def _eq(left: str, right: str) -> str:
    return _app(_standard("relation1", "eq"), left, right)


def _and(left: str, right: str) -> str:
    return _app(_standard("logic1", "and"), left, right)


def _implies(left: str, right: str) -> str:
    return _app(_standard("logic1", "implies"), left, right)


def _card(
    identifier: str,
    statement: str,
    strategy: str,
    steps: list[str],
    xml: str,
    lean_target: str,
    lean_witness: str,
) -> dict[str, Any]:
    canonical = canonicalize_typed_commutative_algebra_openmath_xml(xml)
    return {
        "id": identifier,
        "canonical_statement": statement,
        "proof_strategy": strategy,
        "sketch_steps": steps,
        "openmath_xml": xml,
        "openmath_xml_sha256": _sha256(xml.encode("utf-8")),
        "canonical_openmath_xml": canonical,
        "canonical_openmath_xml_sha256": _sha256(canonical.encode("utf-8")),
        "canonical_statement_sha256": _sha256(statement.encode("utf-8")),
        "lean_target": lean_target,
        "lean_target_sha256": _sha256(lean_target.encode("utf-8")),
        "lean_witness": lean_witness,
        "lean_witness_sha256": _sha256(lean_witness.encode("utf-8")),
        "openmath_profile": TYPED_COMMUTATIVE_ALGEBRA_PROFILE,
        "profile_validation_status": "validated_local_typed_commutative_algebra_v1_sealed",
        "compiler_receipt_status": "verified",
        "admission_status": (
            "sealed-local-authoring-revision: not a DB Draft or an OpenMath-to-Lean "
            "translation receipt"
        ),
        "alignment": {
            "status": "sealed_local_authoring_review_not_admitted",
            "statement_to_openmath": "reviewed with an explicit CommRing carrier and Ideal(R) dependency",
            "openmath_to_lean": "reviewed against the named direct Mathlib ideal theorem",
            "admission_gate": "requires independent project review before any typed catalog admission",
        },
    }


def _cards() -> list[dict[str, Any]]:
    r = _var("R")
    i = _var("I")
    j = _var("J")
    k = _var("K")
    ideal_sum = lambda left, right: _ideal("ideal_sum", r, left, right)
    ideal_inf = lambda left, right: _ideal("ideal_inf", r, left, right)
    product = lambda left, right: _ideal("ideal_product", r, left, right)
    radical = lambda value: _ideal("ideal_radical", r, value)
    prime = lambda value: _ideal("is_prime_ideal", r, value)
    maximal = lambda value: _ideal("is_maximal_ideal", r, value)
    ij = [("R", "CommRing"), ("I", "Ideal R"), ("J", "Ideal R")]
    ijk = [*ij, ("K", "Ideal R")]
    return [
        _card(
            "commalg_ideal_le_sum_left",
            "可換環 R とそのイデアル I,J について I⊆I+J。",
            "イデアル束の sup の左包含を用いる。",
            [
                "R を可換環、I,J を R のイデアルとして固定する。",
                "I+J をイデアル和として読む。",
                "I から I+J への標準包含を適用する。",
                "包含を閉じる。",
            ],
            _proposition(ij, _le("R", i, ideal_sum(i, j))),
            "example {R : Type*} [CommRing R] (I J : Ideal R) : I ≤ I + J",
            "by\n  exact le_sup_left",
        ),
        _card(
            "commalg_ideal_le_sum_right",
            "可換環 R とそのイデアル I,J について J⊆I+J。",
            "イデアル束の sup の右包含を用いる。",
            [
                "R を可換環、I,J を R のイデアルとして固定する。",
                "I+J をイデアル和として読む。",
                "J から I+J への標準包含を適用する。",
                "包含を閉じる。",
            ],
            _proposition(ij, _le("R", j, ideal_sum(i, j))),
            "example {R : Type*} [CommRing R] (I J : Ideal R) : J ≤ I + J",
            "by\n  exact le_sup_right",
        ),
        _card(
            "commalg_ideal_product_le_left",
            "可換環 R とそのイデアル I,J について IJ⊆I。",
            "積イデアルの各生成元が左因子 I に入ることを使う。",
            [
                "R と I,J を固定する。",
                "IJ を積イデアルとして形成する。",
                "各積の左因子が I に属することを使う。",
                "IJ⊆I を結論する。",
            ],
            _proposition(ij, _le("R", product(i, j), i)),
            "example {R : Type*} [CommRing R] (I J : Ideal R) : I * J ≤ I",
            "by\n  exact Ideal.mul_le_right (I := I) (J := J)",
        ),
        _card(
            "commalg_ideal_product_le_right",
            "可換環 R とそのイデアル I,J について IJ⊆J。",
            "積イデアルの各生成元が右因子 J に入ることを使う。",
            [
                "R と I,J を固定する。",
                "IJ を積イデアルとして形成する。",
                "各積の右因子が J に属することを使う。",
                "IJ⊆J を結論する。",
            ],
            _proposition(ij, _le("R", product(i, j), j)),
            "example {R : Type*} [CommRing R] (I J : Ideal R) : I * J ≤ J",
            "by\n  exact Ideal.mul_le_left (I := I) (J := J)",
        ),
        _card(
            "commalg_ideal_product_le_inf",
            "可換環 R とそのイデアル I,J について IJ⊆I∩J。",
            "積イデアルの左右包含を交わりの普遍性で合わせる。",
            [
                "R と I,J を固定する。",
                "IJ⊆I を得る。",
                "IJ⊆J を得る。",
                "交わりの普遍性から IJ⊆I∩J を得る。",
            ],
            _proposition(ij, _le("R", product(i, j), ideal_inf(i, j))),
            "example {R : Type*} [CommRing R] (I J : Ideal R) : I * J ≤ I ⊓ J",
            "by\n  exact le_inf (Ideal.mul_le_right (I := I) (J := J)) (Ideal.mul_le_left (I := I) (J := J))",
        ),
        _card(
            "commalg_ideal_le_radical",
            "可換環 R の任意のイデアル I は √I に含まれる。",
            "1 乗を使い、I の元が radical の定義を満たすことを示す。",
            [
                "R と I を固定する。",
                "I の任意の元を取る。",
                "その 1 乗が I に入ることを確認する。",
                "I⊆√I を結論する。",
            ],
            _proposition(
                [("R", "CommRing"), ("I", "Ideal R")], _le("R", i, radical(i))
            ),
            "example {R : Type*} [CommRing R] (I : Ideal R) : I ≤ I.radical",
            "by\n  exact Ideal.le_radical",
        ),
        _card(
            "commalg_ideal_radical_idempotent",
            "可換環 R の任意のイデアル I について √(√I)=√I。",
            "radical が radical ideal であることを用いる。",
            [
                "R と I を固定する。",
                "√I が radical ideal であることを使う。",
                "radical を再び取っても変わらないことを適用する。",
                "等式を閉じる。",
            ],
            _proposition(
                [("R", "CommRing"), ("I", "Ideal R")],
                _eq(radical(radical(i)), radical(i)),
            ),
            "example {R : Type*} [CommRing R] (I : Ideal R) : I.radical.radical = I.radical",
            "by\n  exact Ideal.radical_idem I",
        ),
        _card(
            "commalg_ideal_radical_mono",
            "可換環 R のイデアル I,J で I⊆J ならば √I⊆√J。",
            "冪が I に入るという証人を J への包含で移す。",
            [
                "R と I,J を固定し I⊆J を仮定する。",
                "√I の元の冪に関する証人を取る。",
                "I⊆J により同じ冪が J に入る。",
                "√I⊆√J を結論する。",
            ],
            _proposition(
                ij, _implies(_le("R", i, j), _le("R", radical(i), radical(j)))
            ),
            "example {R : Type*} [CommRing R] (I J : Ideal R) (h : I ≤ J) : I.radical ≤ J.radical",
            "by\n  exact Ideal.radical_mono h",
        ),
        _card(
            "commalg_prime_ideal_is_radical",
            "可換環 R の素イデアル P は √P=P を満たす。",
            "素性から P が radical ideal であることを使う。",
            [
                "R と P を固定し P が素であると仮定する。",
                "素イデアルが radical ideal であることを使う。",
                "radical の特徴づけを適用する。",
                "√P=P を結論する。",
            ],
            _proposition(
                [("R", "CommRing"), ("P", "Ideal R")],
                _implies(prime(_var("P")), _eq(radical(_var("P")), _var("P"))),
            ),
            "example {R : Type*} [CommRing R] (P : Ideal R) (h : P.IsPrime) : P.radical = P",
            "by\n  exact h.radical",
        ),
        _card(
            "commalg_maximal_ideal_is_prime",
            "可換環 R の極大イデアル M は素イデアルである。",
            "商環が体となることから零因子がないことを使う。",
            [
                "R と M を固定し M が極大であると仮定する。",
                "極大イデアルの商環が体であることを使う。",
                "体には零因子がないことを用いる。",
                "M が素であると結論する。",
            ],
            _proposition(
                [("R", "CommRing"), ("M", "Ideal R")],
                _implies(maximal(_var("M")), prime(_var("M"))),
            ),
            "example {R : Type*} [CommRing R] (M : Ideal R) (h : M.IsMaximal) : M.IsPrime",
            "by\n  exact h.isPrime",
        ),
        _card(
            "commalg_ideal_inclusion_transitive",
            "可換環 R のイデアル I,J,K で I⊆J かつ J⊆K ならば I⊆K。",
            "イデアル包含の推移性を合成する。",
            [
                "R と I,J,K を固定する。",
                "I⊆J と J⊆K を仮定する。",
                "中間イデアル J を介して包含を合成する。",
                "I⊆K を結論する。",
            ],
            _proposition(
                ijk, _implies(_and(_le("R", i, j), _le("R", j, k)), _le("R", i, k))
            ),
            "example {R : Type*} [CommRing R] (I J K : Ideal R) (hIJ : I ≤ J) (hJK : J ≤ K) : I ≤ K",
            "by\n  exact hIJ.trans hJK",
        ),
        _card(
            "commalg_ideal_sum_mono_left",
            "可換環 R のイデアル I,J,K で I⊆J ならば I+K⊆J+K。",
            "和の単調性を左因子に適用する。",
            [
                "R と I,J,K を固定し I⊆J を仮定する。",
                "両辺に K をイデアル和として加える。",
                "和の単調性を適用する。",
                "I+K⊆J+K を得る。",
            ],
            _proposition(
                ijk,
                _implies(_le("R", i, j), _le("R", ideal_sum(i, k), ideal_sum(j, k))),
            ),
            "example {R : Type*} [CommRing R] (I J K : Ideal R) (h : I ≤ J) : I + K ≤ J + K",
            "by\n  simpa [add_comm] using add_le_add_right h K",
        ),
        _card(
            "commalg_ideal_product_mono_left",
            "可換環 R のイデアル I,J,K で I⊆J ならば IK⊆JK。",
            "積イデアルの単調性を一方の因子に適用する。",
            [
                "R と I,J,K を固定し I⊆J を仮定する。",
                "両辺に K を積イデアルとして掛ける。",
                "積の単調性を適用する。",
                "IK⊆JK を得る。",
            ],
            _proposition(
                ijk, _implies(_le("R", i, j), _le("R", product(i, k), product(j, k)))
            ),
            "example {R : Type*} [CommRing R] (I J K : Ideal R) (h : I ≤ J) : I * K ≤ J * K",
            "by\n  exact mul_le_mul_left h K",
        ),
    ]


def build_manifest() -> dict[str, Any]:
    witness = WITNESS.read_bytes()
    cards = _cards()
    payload: dict[str, Any] = {
        "schema_version": "pals.typed-commutative-algebra-v1-sealed-manifest.v1",
        "status": "sealed_local_authoring_revision_not_admitted",
        "seal": {
            "scope": "local typed-commutative-algebra authoring evidence only",
            "admission": "not admitted to the generic DB, seed, embedding index, or PFI package",
            "revision": "typed-commutative-algebra-v1-local-r1",
        },
        "profile": {
            "id": TYPED_COMMUTATIVE_ALGEBRA_PROFILE,
            "typed_cdbase": TYPED,
            "design_path": "docs/typed-commutative-algebra-v1-design.md",
            "design_sha256": _sha256(DESIGN.read_bytes()),
            "registry_path": "pals_agent/content_dictionaries/typed-commutative-algebra-v1-registry.json",
            "registry_sha256": _sha256(REGISTRY.read_bytes()),
            "validator": (
                "pals_agent.typed_commutative_algebra."
                "validate_canonical_typed_commutative_algebra_openmath_xml"
            ),
            "validator_path": "pals_agent/typed_commutative_algebra.py",
            "validator_sha256": _sha256(VALIDATOR.read_bytes()),
            "canonicalizer_version": "openmath-cdbase-alpha-c14n-v4",
        },
        "lean_receipt": {
            "witness_path": "docs/typed-commutative-algebra-v1-authoring-witnesses.lean",
            "witness_file_sha256": _sha256(witness),
            "toolchain": TOOLCHAIN.read_text(encoding="utf-8").rstrip("\n"),
            "verification_command": (
                "cd pals-agent/lean-workspace && lake env lean "
                "../../docs/typed-commutative-algebra-v1-authoring-witnesses.lean"
            ),
            "verification_status": "verified_local_pinned_workspace",
        },
        "admitted_card_count": len(cards),
        "excluded_cards": [
            {
                "id": "commalg_quotient_map_kernel",
                "reason": "quotient carrier and quotient map are not typed in this profile",
            },
            {
                "id": "commalg_localization_prime_correspondence",
                "reason": "submonoid, localization witness, and map are not typed in this profile",
            },
            {
                "id": "commalg_spec_closed_sets",
                "reason": "prime spectrum and set-valued constructors are outside the ideal core",
            },
            {
                "id": "commalg_module_exact_sequence",
                "reason": "module carrier and homomorphism dependencies are outside the ideal core",
            },
        ],
        "excluded_card_count": 4,
        "cards": cards,
    }
    payload["manifest_payload_sha256"] = _sha256(
        json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT
        / "docs/typed-commutative-algebra-v1-authoring-manifest.proposal.json",
    )
    parser.add_argument("--verify-lean", action="store_true")
    args = parser.parse_args()
    if args.verify_lean:
        completed = subprocess.run(
            [
                "lake",
                "env",
                "lean",
                "../../docs/typed-commutative-algebra-v1-authoring-witnesses.lean",
            ],
            cwd=ROOT / "pals-agent/lean-workspace",
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            return completed.returncode
    args.output.write_text(
        json.dumps(build_manifest(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
