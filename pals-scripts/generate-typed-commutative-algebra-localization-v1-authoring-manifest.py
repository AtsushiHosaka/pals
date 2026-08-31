"""Seal original, local-only localization Draft authoring evidence.

The command only writes a proposal manifest.  It neither touches the generic
Draft database nor creates SQL, embeddings, PFI packages, or seed data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import rfc8785

ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = ROOT / "pals-agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from pals_agent.typed_commutative_algebra_localization import (
    TYPED_COMMUTATIVE_ALGEBRA_LOCALIZATION_OPENMATH_CDBASE,
    TYPED_COMMUTATIVE_ALGEBRA_LOCALIZATION_PROFILE,
    canonicalize_typed_commutative_algebra_localization_openmath_xml,
)

OPENMATH = "http://www.openmath.org/OpenMath"
STANDARD = "http://www.openmath.org/cd"
TYPED = TYPED_COMMUTATIVE_ALGEBRA_LOCALIZATION_OPENMATH_CDBASE
DESIGN = ROOT / "docs/typed-commutative-algebra-localization-v1-design.md"
REGISTRY = (
    AGENT_ROOT
    / "pals_agent/content_dictionaries/typed-commutative-algebra-localization-v1-registry.json"
)
VALIDATOR = AGENT_ROOT / "pals_agent/typed_commutative_algebra_localization.py"
WITNESS = (
    ROOT / "docs/typed-commutative-algebra-localization-v1-authoring-witnesses.lean"
)
TOOLCHAIN = AGENT_ROOT / "lean-workspace/lean-toolchain"


def _sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _typed(cd: str, name: str) -> str:
    return f'<OMS cdbase="{TYPED}" cd="{cd}" name="{name}"/>'


def _standard(cd: str, name: str) -> str:
    return f'<OMS cdbase="{STANDARD}" cd="{cd}" name="{name}"/>'


def _app(operator: str, *arguments: str) -> str:
    return f"<OMA>{operator}{''.join(arguments)}</OMA>"


def _var(name: str) -> str:
    return f'<OMV name="{name}"/>'


def _eq(left: str, right: str) -> str:
    return _app(_standard("relation1", "eq"), left, right)


def _neq(left: str, right: str) -> str:
    return _app(_standard("relation1", "neq"), left, right)


def _and(left: str, right: str) -> str:
    return _app(_standard("logic1", "and"), left, right)


def _implies(left: str, right: str) -> str:
    return _app(_standard("logic1", "implies"), left, right)


def _equivalent(left: str, right: str) -> str:
    return _app(_standard("logic1", "equivalent"), left, right)


def _loc(name: str, *arguments: str) -> str:
    return _app(_typed("localization1", name), *arguments)


def _ideal(name: str, *arguments: str) -> str:
    return _app(_typed("commalg1", name), *arguments)


def _type(name: str, *arguments: str) -> str:
    if not arguments:
        return _typed("localization1", name)
    cd = (
        "typed1"
        if name == "Elem"
        else "localization1"
        if name != "Ideal"
        else "commalg1"
    )
    return _app(_typed(cd, name), *arguments)


def _declaration(name: str, sort: str) -> str:
    return (
        f"<OMATTR><OMATP>{_typed('typed1', 'type')}{sort}</OMATP>{_var(name)}</OMATTR>"
    )


def _bind(binder: str, declarations: list[tuple[str, str]], body: str) -> str:
    declared = "".join(_declaration(name, sort) for name, sort in declarations)
    return (
        f"<OMBIND>{_typed('typed1', binder)}<OMBVAR>{declared}</OMBVAR>{body}</OMBIND>"
    )


def _proposition(declarations: list[tuple[str, str]], body: str) -> str:
    return f'<OMOBJ xmlns="{OPENMATH}" version="2.0">{_bind("forall", declarations, body)}</OMOBJ>'


R = _var("R")
M = _var("M")
L = _var("L")
I = _var("I")
J = _var("J")
X = _var("x")
Y = _var("y")
D = _var("d")
T = _var("t")
RING_R = _type("CommRing")
MONOID_R = _type("Submonoid", R)
LOCALIZATION_RM = _type("Localization", R, M)
IDEAL_R = _type("Ideal", R)
IDEAL_L = _type("Ideal", L)
ELEM_R = _type("Elem", R)
SUBMONOID_ELEM_RM = _type("SubmonoidElem", R, M)


def _base_declarations(*extra: tuple[str, str]) -> list[tuple[str, str]]:
    return [("R", RING_R), ("M", MONOID_R), ("L", LOCALIZATION_RM), *extra]


def _extension(ideal: str) -> str:
    return _ideal("extend", R, M, L, ideal)


def _contraction(ideal: str) -> str:
    return _ideal("contract", R, M, L, ideal)


def _ideal_le(carrier: str, left: str, right: str) -> str:
    return _ideal("ideal_le", carrier, left, right)


def _ideal_mem(carrier: str, ideal: str, value: str) -> str:
    return _ideal("ideal_mem", carrier, ideal, value)


def _top(carrier: str) -> str:
    return _ideal("ideal_top", carrier)


def _map(value: str) -> str:
    return _loc("loc_map", R, M, L, value)


def _fraction(value: str, denominator: str) -> str:
    return _loc("loc_fraction", R, M, L, value, denominator)


def _monoid_value(value: str) -> str:
    return _loc("submonoid_value", R, M, value)


def _card(
    identifier: str,
    statement: str,
    strategy: str,
    steps: list[str],
    declarations: list[tuple[str, str]],
    body: str,
    lean_target: str,
    lean_witness: str,
    alignment: str,
) -> dict[str, Any]:
    raw = _proposition(declarations, body)
    canonical = canonicalize_typed_commutative_algebra_localization_openmath_xml(raw)
    if not 4 <= len(steps) <= 8:
        raise ValueError(f"{identifier} must have 4..8 sketch steps")
    return {
        "id": identifier,
        "domain": "commutative_algebra.localization",
        "difficulty": "undergraduate_year_2",
        "canonical_statement": statement,
        "canonical_statement_sha256": _sha256(statement.encode("utf-8")),
        "proof_strategy": strategy,
        "sketch_steps": steps,
        "openmath_xml": raw,
        "openmath_xml_sha256": _sha256(raw.encode("utf-8")),
        "canonical_openmath_xml": canonical,
        "canonical_openmath_xml_sha256": _sha256(canonical.encode("utf-8")),
        "lean_target": lean_target,
        "lean_target_sha256": _sha256(lean_target.encode("utf-8")),
        "lean_witness": lean_witness,
        "lean_witness_sha256": _sha256(lean_witness.encode("utf-8")),
        "openmath_profile": TYPED_COMMUTATIVE_ALGEBRA_LOCALIZATION_PROFILE,
        "profile_validation_status": "validated_local_typed_commutative_algebra_localization_v1_sealed",
        "compiler_receipt_status": "verified_local_pinned_workspace",
        "admission_status": "sealed-local-authoring-revision: not a DB Draft or an OpenMath-to-Lean translation receipt",
        "alignment": {
            "status": "sealed_local_authoring_review_not_admitted",
            "statement_to_openmath": alignment,
            "openmath_to_lean": "reviewed against the named IsLocalization/Ideal theorem under the explicit R, M, L convention",
            "admission_gate": "requires independent project review before any typed catalog admission",
        },
    }


def _steps(first: str, core: str, conclusion: str) -> list[str]:
    return [
        "可換環 R、部分モノイド M、局所化 L の carrier を固定する。",
        first,
        core,
        conclusion,
    ]


def _cards() -> list[dict[str, Any]]:
    return [
        _card(
            "commalg_localization_extend_mono",
            "I⊆J ならば、局所化 L における I の拡大は J の拡大に含まれる。",
            "ideal map の単調性を使う。",
            _steps(
                "I⊆J を仮定する。",
                "局所化写像による ideal map の単調性を適用する。",
                "拡大 ideal の包含を結論する。",
            ),
            _base_declarations(("I", IDEAL_R), ("J", IDEAL_R)),
            _implies(_ideal_le(R, I, J), _ideal_le(L, _extension(I), _extension(J))),
            "(I J : Ideal R) (h : I ≤ J) : I.map (algebraMap R S) ≤ J.map (algebraMap R S)",
            "example (I J : Ideal R) (h : I ≤ J) :\n    I.map (algebraMap R S) ≤ J.map (algebraMap R S) := by\n  exact Ideal.map_mono h",
            "ideal_le(R,I,J) is mapped to ideal_le(L,extend(I),extend(J)) with the same R,M,L.",
        ),
        _card(
            "commalg_localization_contract_mono",
            "L の ideal J₁⊆J₂ ならば、それらの R への縮約も包含関係を保つ。",
            "ideal comap の単調性を使う。",
            _steps(
                "局所化側の2つの ideal の包含を仮定する。",
                "algebraMap による comap を取る。",
                "comap の単調性を適用する。",
            ),
            _base_declarations(("I", IDEAL_L), ("J", IDEAL_L)),
            _implies(
                _ideal_le(L, I, J), _ideal_le(R, _contraction(I), _contraction(J))
            ),
            "(I J : Ideal S) (h : I ≤ J) : I.comap (algebraMap R S) ≤ J.comap (algebraMap R S)",
            "example (I J : Ideal S) (h : I ≤ J) :\n    I.comap (algebraMap R S) ≤ J.comap (algebraMap R S) := by\n  exact Ideal.comap_mono h",
            "ideal_le(L,I,J) contracts along the explicit algebraMap R L.",
        ),
        _card(
            "commalg_localization_le_contract_extend",
            "任意の R の ideal I は、拡大してから縮約した ideal に含まれる。",
            "map-comap の Galois 不等式を使う。",
            _steps(
                "R の ideal I を固定する。",
                "I を L へ拡大する。",
                "その縮約に対する標準不等式を適用する。",
            ),
            _base_declarations(("I", IDEAL_R)),
            _ideal_le(R, I, _contraction(_extension(I))),
            "(I : Ideal R) : I ≤ (I.map (algebraMap R S)).comap (algebraMap R S)",
            "example (I : Ideal R) : I ≤ (I.map (algebraMap R S)).comap (algebraMap R S) := by\n  exact Ideal.le_comap_map",
            "The OpenMath extension and contraction are Ideal.map and Ideal.comap along algebraMap R L.",
        ),
        _card(
            "commalg_localization_extend_contract_le",
            "L の ideal J について、縮約してから拡大した ideal は J に含まれる。",
            "map-comap の逆向き不等式を使う。",
            _steps(
                "L の ideal J を固定する。",
                "J を R へ縮約する。",
                "縮約の拡大が J に含まれることを適用する。",
            ),
            _base_declarations(("J", IDEAL_L)),
            _ideal_le(L, _extension(_contraction(J)), J),
            "(J : Ideal S) : (J.comap (algebraMap R S)).map (algebraMap R S) ≤ J",
            "example (J : Ideal S) : (J.comap (algebraMap R S)).map (algebraMap R S) ≤ J := by\n  exact Ideal.map_comap_le",
            "The same R,M,L binder order fixes the direction of map and comap.",
        ),
        _card(
            "commalg_localization_extend_contract_eq",
            "局所化 L の ideal J は、R への縮約の拡大と等しい。",
            "局所化における ideal の extension-contraction 等式を使う。",
            _steps(
                "局所化側の ideal J を固定する。",
                "J を R に縮約する。",
                "IsLocalization の map_under 等式を適用する。",
            ),
            _base_declarations(("J", IDEAL_L)),
            _eq(_extension(_contraction(J)), J),
            "(J : Ideal S) : (J.comap (algebraMap R S)).map (algebraMap R S) = J",
            "example (J : Ideal S) :\n    (J.comap (algebraMap R S)).map (algebraMap R S) = J := by\n  exact IsLocalization.map_under M S J",
            "The equality is only for an ideal already over the declared localization carrier L.",
        ),
        _card(
            "commalg_localization_contract_order_reflects",
            "局所化 L の ideal の包含は、R への縮約後の包含と同値である。",
            "局所化 ideal の order embedding を使う。",
            _steps(
                "局所化側の2つの ideal を固定する。",
                "両方を R に縮約する。",
                "縮約の順序反射同値を適用する。",
            ),
            _base_declarations(("I", IDEAL_L), ("J", IDEAL_L)),
            _equivalent(
                _ideal_le(R, _contraction(I), _contraction(J)), _ideal_le(L, I, J)
            ),
            "(I J : Ideal S) : I.comap (algebraMap R S) ≤ J.comap (algebraMap R S) ↔ I ≤ J",
            "example (I J : Ideal S) :\n    I.comap (algebraMap R S) ≤ J.comap (algebraMap R S) ↔ I ≤ J := by\n  exact IsLocalization.under_le_under_iff M S",
            "logic1:equivalent represents the Lean iff between the two explicit ideal orders.",
        ),
        _card(
            "commalg_localization_extend_inf",
            "R の2つの ideal の共通部分を拡大すると、各拡大 ideal の共通部分になる。",
            "局所化が ideal の有限 meet を保存することを使う。",
            _steps(
                "R の ideal I,J を固定する。",
                "I∩J を形成して局所化する。",
                "局所化に特有の map_inf 等式を適用する。",
            ),
            _base_declarations(("I", IDEAL_R), ("J", IDEAL_R)),
            _eq(
                _extension(_ideal("ideal_inf", R, I, J)),
                _ideal("ideal_inf", L, _extension(I), _extension(J)),
            ),
            "(I J : Ideal R) : (I ⊓ J).map (algebraMap R S) = I.map (algebraMap R S) ⊓ J.map (algebraMap R S)",
            "example (I J : Ideal R) :\n    (I ⊓ J).map (algebraMap R S) = I.map (algebraMap R S) ⊓ J.map (algebraMap R S) := by\n  exact IsLocalization.map_inf M S I J",
            "ideal_inf is interpreted over R on the left and over L on the right.",
        ),
        _card(
            "commalg_localization_extend_sup",
            "R の2つの ideal の和を拡大すると、各拡大 ideal の和になる。",
            "ideal map の sup 保存を使う。",
            _steps(
                "R の ideal I,J を固定する。",
                "I+J を形成して拡大する。",
                "ideal map の map_sup 等式を適用する。",
            ),
            _base_declarations(("I", IDEAL_R), ("J", IDEAL_R)),
            _eq(
                _extension(_ideal("ideal_sup", R, I, J)),
                _ideal("ideal_sup", L, _extension(I), _extension(J)),
            ),
            "(I J : Ideal R) : (I ⊔ J).map (algebraMap R S) = I.map (algebraMap R S) ⊔ J.map (algebraMap R S)",
            "example (I J : Ideal R) :\n    (I ⊔ J).map (algebraMap R S) = I.map (algebraMap R S) ⊔ J.map (algebraMap R S) := by\n  exact Ideal.map_sup (f := algebraMap R S) I J",
            "ideal_sup is represented as the ideal-lattice join, not elementwise union.",
        ),
        _card(
            "commalg_localization_contract_inf",
            "L の2つの ideal の共通部分を縮約すると、縮約 ideal の共通部分になる。",
            "ideal comap の inf 保存を使う。",
            _steps(
                "L の ideal I,J を固定する。",
                "I∩J を R に縮約する。",
                "comap_inf 等式を適用する。",
            ),
            _base_declarations(("I", IDEAL_L), ("J", IDEAL_L)),
            _eq(
                _contraction(_ideal("ideal_inf", L, I, J)),
                _ideal("ideal_inf", R, _contraction(I), _contraction(J)),
            ),
            "(I J : Ideal S) : (I ⊓ J).comap (algebraMap R S) =\n      I.comap (algebraMap R S) ⊓ J.comap (algebraMap R S)",
            "example (I J : Ideal S) :\n    (I ⊓ J).comap (algebraMap R S) =\n      I.comap (algebraMap R S) ⊓ J.comap (algebraMap R S) := by\n  exact Ideal.comap_inf (algebraMap R S) I J",
            "Both input ideals are forced to be over L before contraction.",
        ),
        _card(
            "commalg_localization_extend_top",
            "R の全 ideal を局所化しても、L の全 ideal である。",
            "ideal map が top を保存することを使う。",
            _steps(
                "R の top ideal を選ぶ。",
                "これを局所化写像で拡大する。",
                "map_top 等式を適用する。",
            ),
            _base_declarations(),
            _eq(_extension(_top(R)), _top(L)),
            ": (⊤ : Ideal R).map (algebraMap R S) = ⊤",
            "example : (⊤ : Ideal R).map (algebraMap R S) = ⊤ := by\n  exact Ideal.map_top (algebraMap R S)",
            "ideal_top carries its ring argument, so top ideals of R and L cannot be confused.",
        ),
        _card(
            "commalg_localization_contract_top",
            "L の全 ideal を縮約すると、R の全 ideal である。",
            "ideal comap が top を保存することを使う。",
            _steps(
                "L の top ideal を選ぶ。",
                "これを R に縮約する。",
                "comap_top 等式を適用する。",
            ),
            _base_declarations(),
            _eq(_contraction(_top(L)), _top(R)),
            ": (⊤ : Ideal S).comap (algebraMap R S) = ⊤",
            "example : (⊤ : Ideal S).comap (algebraMap R S) = ⊤ := by\n  exact Ideal.comap_top",
            "The contraction target is explicitly R, preventing a reversed-comap reading.",
        ),
        _card(
            "commalg_localization_extend_radical",
            "radical を取ってから拡大しても、拡大してから radical を取っても同じである。",
            "局所化と radical の可換性を使う。",
            _steps(
                "R の ideal I を固定する。",
                "I の radical と局所化を形成する。",
                "IsLocalization の map_radical 等式を適用する。",
            ),
            _base_declarations(("I", IDEAL_R)),
            _eq(
                _extension(_ideal("ideal_radical", R, I)),
                _ideal("ideal_radical", L, _extension(I)),
            ),
            "(I : Ideal R) : I.radical.map (algebraMap R S) = (I.map (algebraMap R S)).radical",
            "example (I : Ideal R) :\n    I.radical.map (algebraMap R S) = (I.map (algebraMap R S)).radical := by\n  exact IsLocalization.map_radical M S I",
            "ideal_radical retains the carrier; the right-hand radical is over L.",
        ),
        _card(
            "commalg_localization_extended_proper_iff_disjoint",
            "I の拡大が真 ideal であることは、I と分母モノイド M が交わらないことと同値である。",
            "局所化した ideal が top になる判定を使う。",
            _steps(
                "R の ideal I を固定する。",
                "拡大 ideal が top でない条件を読む。",
                "M と I の非交差判定へ変形する。",
            ),
            _base_declarations(("I", IDEAL_R)),
            _equivalent(
                _neq(_extension(I), _top(L)),
                _ideal("ideal_disjoint_submonoid", R, M, I),
            ),
            "(I : Ideal R) : I.map (algebraMap R S) ≠ ⊤ ↔ Disjoint (M : Set R) (I : Set R)",
            "example (I : Ideal R) :\n    I.map (algebraMap R S) ≠ ⊤ ↔ Disjoint (M : Set R) (I : Set R) := by\n  exact IsLocalization.map_algebraMap_ne_top_iff_disjoint M S I",
            "The disjointness predicate names both R and its declared submonoid M.",
        ),
        _card(
            "commalg_localization_prime_contract_iff",
            "L の ideal J が素であることは、縮約が素で M と交わらないことと同値である。",
            "局所化における素 ideal の対応を使う。",
            _steps(
                "L の ideal J を固定する。",
                "J を R に縮約する。",
                "prime-disjoint correspondence を適用する。",
            ),
            _base_declarations(("J", IDEAL_L)),
            _equivalent(
                _ideal("is_prime_ideal", L, J),
                _and(
                    _ideal("is_prime_ideal", R, _contraction(J)),
                    _ideal("ideal_disjoint_submonoid", R, M, _contraction(J)),
                ),
            ),
            "(J : Ideal S) : J.IsPrime ↔ (J.comap (algebraMap R S)).IsPrime ∧\n      Disjoint (M : Set R) ((J.comap (algebraMap R S) : Ideal R) : Set R)",
            "example (J : Ideal S) :\n    J.IsPrime ↔ (J.comap (algebraMap R S)).IsPrime ∧\n      Disjoint (M : Set R) ((J.comap (algebraMap R S) : Ideal R) : Set R) := by\n  exact IsLocalization.isPrime_iff_isPrime_disjoint M S J",
            "The conjunction retains both the prime condition and the denominator-disjoint side condition.",
        ),
        _card(
            "commalg_localization_extend_prime_of_disjoint",
            "R の素 ideal I が M と交わらなければ、I の拡大は L の素 ideal である。",
            "素 ideal の局所化定理を側条件付きで使う。",
            _steps(
                "R の ideal I が素であると仮定する。",
                "I と M の非交差を仮定する。",
                "局所化後の素性定理を適用する。",
            ),
            _base_declarations(("I", IDEAL_R)),
            _implies(
                _and(
                    _ideal("is_prime_ideal", R, I),
                    _ideal("ideal_disjoint_submonoid", R, M, I),
                ),
                _ideal("is_prime_ideal", L, _extension(I)),
            ),
            "(I : Ideal R) (hprime : I.IsPrime) (hdisjoint : Disjoint (M : Set R) (I : Set R)) :\n    (I.map (algebraMap R S)).IsPrime",
            "example (I : Ideal R) (hprime : I.IsPrime) (hdisjoint : Disjoint (M : Set R) (I : Set R)) :\n    (I.map (algebraMap R S)).IsPrime := by\n  exact IsLocalization.isPrime_of_isPrime_disjoint M S I hprime hdisjoint",
            "Both necessary premises are explicit; the profile never accepts an unguarded prime-extension claim.",
        ),
        _card(
            "commalg_localization_map_membership_iff",
            "algebraMap(x) が I の拡大に入ることは、ある分母 t∈M で tx∈I となることと同値である。",
            "局所化 ideal の分母を払う membership 判定を使う。",
            _steps(
                "R の ideal I と元 x を固定する。",
                "局所化写像の x の membership を考える。",
                "分母 t を掛ける存在条件へ展開する。",
            ),
            _base_declarations(("I", IDEAL_R), ("x", ELEM_R)),
            _equivalent(
                _ideal_mem(L, _extension(I), _map(X)),
                _bind(
                    "exists",
                    [("t", SUBMONOID_ELEM_RM)],
                    _ideal_mem(R, I, _loc("ring_mul", R, _monoid_value(T), X)),
                ),
            ),
            "(I : Ideal R) (x : R) :\n    algebraMap R S x ∈ I.map (algebraMap R S) ↔ ∃ m ∈ M, m * x ∈ I",
            "example (I : Ideal R) (x : R) :\n    algebraMap R S x ∈ I.map (algebraMap R S) ↔ ∃ m ∈ M, m * x ∈ I := by\n  exact IsLocalization.algebraMap_mem_map_algebraMap_iff M S I x",
            "The existential variable has sort SubmonoidElem(R,M), so M-membership is not an implicit premise.",
        ),
        _card(
            "commalg_localization_fraction_membership_iff",
            "分数 x/d が I の拡大に入ることは、ある t∈M で tx∈I となることと同値である。",
            "局所化した ideal の明示分数 membership 判定を使う。",
            _steps(
                "I、分子 x、分母 d を固定する。",
                "d が M の元である型注釈を確認する。",
                "mk' の membership 判定を適用する。",
            ),
            _base_declarations(("I", IDEAL_R), ("x", ELEM_R), ("d", SUBMONOID_ELEM_RM)),
            _equivalent(
                _ideal_mem(L, _extension(I), _fraction(X, D)),
                _bind(
                    "exists",
                    [("t", SUBMONOID_ELEM_RM)],
                    _ideal_mem(R, I, _loc("ring_mul", R, _monoid_value(T), X)),
                ),
            ),
            "{I : Ideal R} (x : R) (m : M) :\n    IsLocalization.mk' S x m ∈ I.map (algebraMap R S) ↔ ∃ s ∈ M, s * x ∈ I",
            "example {I : Ideal R} (x : R) (m : M) :\n    IsLocalization.mk' S x m ∈ I.map (algebraMap R S) ↔ ∃ s ∈ M, s * x ∈ I := by\n  exact IsLocalization.mk'_mem_map_algebraMap_iff M S I x m",
            "loc_fraction requires a SubmonoidElem(R,M) denominator and cannot be formed from an arbitrary element.",
        ),
        _card(
            "commalg_localization_fraction_membership_reduce",
            "L の ideal J に対し、分数 x/d が J に入ることは algebraMap(x) が J に入ることと同値である。",
            "分母が局所化で可逆であることによる membership 簡約を使う。",
            _steps(
                "L の ideal J、x、d を固定する。",
                "d が M に属することを型から得る。",
                "mk' の membership 同値を適用する。",
            ),
            _base_declarations(("J", IDEAL_L), ("x", ELEM_R), ("d", SUBMONOID_ELEM_RM)),
            _equivalent(_ideal_mem(L, J, _fraction(X, D)), _ideal_mem(L, J, _map(X))),
            "{I : Ideal S} (x : R) (m : M) :\n    IsLocalization.mk' S x m ∈ I ↔ algebraMap R S x ∈ I",
            "example {I : Ideal S} (x : R) (m : M) :\n    IsLocalization.mk' S x m ∈ I ↔ algebraMap R S x ∈ I := by\n  exact IsLocalization.mk'_mem_iff",
            "Both sides are membership in the same L-ideal J; only the represented element changes.",
        ),
        _card(
            "commalg_localization_denominator_is_unit",
            "M の任意の分母 d の局所化像は L で可逆である。",
            "局所化の defining unit property を使う。",
            _steps(
                "M の元 d を固定する。",
                "d を R の元として局所化写像で送る。",
                "IsLocalization.map_units を適用する。",
            ),
            _base_declarations(("d", SUBMONOID_ELEM_RM)),
            _loc("is_unit", L, _map(_monoid_value(D))),
            "(m : M) : IsUnit (algebraMap R S m)",
            "example (m : M) : IsUnit (algebraMap R S m) := by\n  exact IsLocalization.map_units S m",
            "The only inputs declared as denominators are values of SubmonoidElem(R,M).",
        ),
        _card(
            "commalg_localization_map_add",
            "局所化写像は加法を保存する。",
            "algebraMap の加法準同型性を使う。",
            _steps(
                "R の元 x,y を固定する。",
                "x+y を R で形成する。",
                "algebraMap の map_add を適用する。",
            ),
            _base_declarations(("x", ELEM_R), ("y", ELEM_R)),
            _eq(_map(_loc("ring_add", R, X, Y)), _loc("ring_add", L, _map(X), _map(Y))),
            "(x y : R) : algebraMap R S (x + y) = algebraMap R S x + algebraMap R S y",
            "example (x y : R) : algebraMap R S (x + y) = algebraMap R S x + algebraMap R S y := by\n  exact map_add (algebraMap R S) x y",
            "ring_add records its carrier explicitly on both the R and L sides.",
        ),
        _card(
            "commalg_localization_map_mul",
            "局所化写像は乗法を保存する。",
            "algebraMap の乗法準同型性を使う。",
            _steps(
                "R の元 x,y を固定する。",
                "xy を R で形成する。",
                "algebraMap の map_mul を適用する。",
            ),
            _base_declarations(("x", ELEM_R), ("y", ELEM_R)),
            _eq(_map(_loc("ring_mul", R, X, Y)), _loc("ring_mul", L, _map(X), _map(Y))),
            "(x y : R) : algebraMap R S (x * y) = algebraMap R S x * algebraMap R S y",
            "example (x y : R) : algebraMap R S (x * y) = algebraMap R S x * algebraMap R S y := by\n  exact map_mul (algebraMap R S) x y",
            "ring_mul records its carrier explicitly on both the R and L sides.",
        ),
        _card(
            "commalg_localization_map_zero",
            "局所化写像は R の0を L の0へ送る。",
            "algebraMap の zero 保存を使う。",
            _steps("R の0を選ぶ。", "局所化写像で0を送る。", "map_zero を適用する。"),
            _base_declarations(),
            _eq(_map(_loc("ring_zero", R)), _loc("ring_zero", L)),
            ": algebraMap R S (0 : R) = 0",
            "example : algebraMap R S (0 : R) = 0 := by\n  exact map_zero (algebraMap R S)",
            "The two zero symbols carry R and L separately.",
        ),
        _card(
            "commalg_localization_map_one",
            "局所化写像は R の1を L の1へ送る。",
            "algebraMap の one 保存を使う。",
            _steps("R の1を選ぶ。", "局所化写像で1を送る。", "map_one を適用する。"),
            _base_declarations(),
            _eq(_map(_loc("ring_one", R)), _loc("ring_one", L)),
            ": algebraMap R S (1 : R) = 1",
            "example : algebraMap R S (1 : R) = 1 := by\n  exact map_one (algebraMap R S)",
            "The two one symbols carry R and L separately.",
        ),
    ]


def build_manifest() -> dict[str, Any]:
    witness = WITNESS.read_bytes()
    cards = _cards()
    payload: dict[str, Any] = {
        "schema_version": "pals.typed-commutative-algebra-localization-v1-sealed-manifest.v1",
        "status": "sealed_local_authoring_revision_not_admitted",
        "seal": {
            "scope": "local typed commutative-algebra localization authoring evidence only",
            "admission": "not admitted to the generic DB, seed, embedding index, or PFI package",
            "revision": "typed-commutative-algebra-localization-v1-local-r1",
        },
        "profile": {
            "id": TYPED_COMMUTATIVE_ALGEBRA_LOCALIZATION_PROFILE,
            "typed_cdbase": TYPED,
            "design_path": "docs/typed-commutative-algebra-localization-v1-design.md",
            "design_sha256": _sha256(DESIGN.read_bytes()),
            "registry_path": "pals_agent/content_dictionaries/typed-commutative-algebra-localization-v1-registry.json",
            "registry_sha256": _sha256(REGISTRY.read_bytes()),
            "validator": "pals_agent.typed_commutative_algebra_localization.validate_canonical_typed_commutative_algebra_localization_openmath_xml",
            "validator_path": "pals_agent/typed_commutative_algebra_localization.py",
            "validator_sha256": _sha256(VALIDATOR.read_bytes()),
            "canonicalizer_version": "openmath-cdbase-alpha-c14n-v4",
        },
        "lean_receipt": {
            "witness_path": "docs/typed-commutative-algebra-localization-v1-authoring-witnesses.lean",
            "witness_file_sha256": _sha256(witness),
            "toolchain_path": "pals-agent/lean-workspace/lean-toolchain",
            "toolchain": TOOLCHAIN.read_text(encoding="utf-8").rstrip("\n"),
            "toolchain_sha256": _sha256(TOOLCHAIN.read_bytes()),
            "verification_command": "cd pals-agent/lean-workspace && lake env lean ../../docs/typed-commutative-algebra-localization-v1-authoring-witnesses.lean",
            "verification_status": "verified_local_pinned_workspace",
        },
        "admitted_card_count": len(cards),
        "hard_rejects": [
            "implicit_localization_carrier",
            "arbitrary_element_as_denominator",
            "quotient_ring",
            "localized_module",
            "fraction_field",
            "unproved_prime_extension_without_disjointness",
        ],
        "hard_reject_count": 6,
        "cards": cards,
    }
    payload["manifest_payload_sha256"] = _sha256(rfc8785.dumps(payload))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT
        / "docs/typed-commutative-algebra-localization-v1-authoring-manifest.proposal.json",
    )
    parser.add_argument("--verify-lean", action="store_true")
    args = parser.parse_args()
    if args.verify_lean:
        checked = subprocess.run(
            [
                "lake",
                "env",
                "lean",
                "../../docs/typed-commutative-algebra-localization-v1-authoring-witnesses.lean",
            ],
            cwd=AGENT_ROOT / "lean-workspace",
            check=False,
        )
        if checked.returncode != 0:
            return checked.returncode
    args.output.write_text(
        json.dumps(build_manifest(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
