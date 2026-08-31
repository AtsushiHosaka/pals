# ruff: noqa: E402, E741
"""Seal original CA-4 primary-decomposition authoring evidence locally.

This command only writes an immutable proposal manifest.  It does not touch a
generic Draft database, seed, loader, embedding index, SQL transaction, or PFI
package.
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path
from typing import Any

import rfc8785

ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = ROOT / "pals-agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from pals_agent.typed_commutative_algebra_decomposition import (
    TYPED_COMMUTATIVE_ALGEBRA_DECOMPOSITION_OPENMATH_CDBASE,
    TYPED_COMMUTATIVE_ALGEBRA_DECOMPOSITION_PROFILE,
    canonicalize_typed_commutative_algebra_decomposition_openmath_xml,
)

OPENMATH = "http://www.openmath.org/OpenMath"
STANDARD = "http://www.openmath.org/cd"
TYPED = TYPED_COMMUTATIVE_ALGEBRA_DECOMPOSITION_OPENMATH_CDBASE
DESIGN = ROOT / "docs/typed-commutative-algebra-decomposition-v1-design.md"
REGISTRY = (
    AGENT_ROOT
    / "pals_agent/content_dictionaries/typed-commutative-algebra-decomposition-v1-registry.json"
)
VALIDATOR = AGENT_ROOT / "pals_agent/typed_commutative_algebra_decomposition.py"
WITNESS = ROOT / "docs/typed-commutative-algebra-decomposition-v1-authoring-witnesses.lean"
TOOLCHAIN = AGENT_ROOT / "lean-workspace/lean-toolchain"
VERIFY = (
    "cd pals-agent/lean-workspace && lake env lean "
    "../../docs/typed-commutative-algebra-decomposition-v1-authoring-witnesses.lean"
)
HARD_REJECTS = [
    "associated_primes_requires_module_and_annihilator",
    "noetherian_primary_decomposition_existence",
    "arbitrary_finite_family_decomposition",
    "quotient_or_localized_primary_component",
]


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


def _op(name: str, *arguments: str) -> str:
    return _app(_typed("decomposition1", name), *arguments)


def _eq(left: str, right: str) -> str:
    return _app(_standard("relation1", "eq"), left, right)


def _neq(left: str, right: str) -> str:
    return _app(_standard("relation1", "neq"), left, right)


def _and(left: str, right: str) -> str:
    return _app(_standard("logic1", "and"), left, right)


def _implies(left: str, right: str) -> str:
    return _app(_standard("logic1", "implies"), left, right)


def _not(value: str) -> str:
    return _app(_standard("logic1", "not"), value)


def _sort(name: str, carrier: str | None = None) -> str:
    if carrier is None:
        return _typed("decomposition1", name)
    return _op(name, _var(carrier))


def _declaration(name: str, sort: str) -> str:
    return f"<OMATTR><OMATP>{_typed('typed1', 'type')}{sort}</OMATP>{_var(name)}</OMATTR>"


def _bind(declarations: list[tuple[str, str]], body: str) -> str:
    bound = "".join(_declaration(name, sort) for name, sort in declarations)
    return f"<OMBIND>{_typed('typed1', 'forall')}<OMBVAR>{bound}</OMBVAR>{body}</OMBIND>"


def _proposition(declarations: list[tuple[str, str]], body: str) -> str:
    return f'<OMOBJ xmlns="{OPENMATH}" version="2.0">{_bind(declarations, body)}</OMOBJ>'


R = _var("R")
I = _var("I")
J = _var("J")
K = _var("K")
P = _var("P")
Q = _var("Q")
Q1 = _var("Q1")
Q2 = _var("Q2")
Q3 = _var("Q3")
COMM_RING = _sort("CommRing")
IDEAL_R = _sort("Ideal", "R")
PRIMARY_R = _sort("PrimaryIdeal", "R")
PRIME_R = _sort("PrimeIdeal", "R")


def _ideal_top() -> str:
    return _op("ideal_top", R)


def _primary(value: str) -> str:
    return _op("primary_as_ideal", R, value)


def _prime(value: str) -> str:
    return _op("prime_as_ideal", R, value)


def _primary_radical_prime(value: str) -> str:
    return _op("primary_radical_prime", R, value)


def _radical(value: str) -> str:
    return _op("ideal_radical", R, value)


def _inf2(left: str, right: str) -> str:
    return _op("ideal_inf2", R, left, right)


def _inf3(first: str, second: str, third: str) -> str:
    return _op("ideal_inf3", R, first, second, third)


def _le(left: str, right: str) -> str:
    return _op("ideal_le", R, left, right)


def _is_primary(value: str) -> str:
    return _op("is_primary_ideal", R, value)


def _is_prime(value: str) -> str:
    return _op("is_prime_ideal", R, value)


def _is_radical(value: str) -> str:
    return _op("is_radical_ideal", R, value)


def _decomp2(ideal: str, first: str, second: str) -> str:
    return _op("primary_decomposition2", R, ideal, first, second)


def _decomp3(ideal: str, first: str, second: str, third: str) -> str:
    return _op("primary_decomposition3", R, ideal, first, second, third)


def _irredundant2(ideal: str, first: str, second: str) -> str:
    return _op("irredundant_decomposition2", R, ideal, first, second)


def _minimal_prime_over(prime: str, ideal: str) -> str:
    return _op("minimal_prime_over", R, prime, ideal)


def _base(*extra: tuple[str, str]) -> list[tuple[str, str]]:
    return [("R", COMM_RING), *extra]


def _steps(*steps: str) -> list[str]:
    values = list(steps)
    if not 4 <= len(values) <= 8:
        raise ValueError("every Sketch must have 4..8 steps")
    return values


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
    canonical = canonicalize_typed_commutative_algebra_decomposition_openmath_xml(raw)
    return {
        "id": identifier,
        "domain": "commutative_algebra.primary_decomposition",
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
        "openmath_profile": TYPED_COMMUTATIVE_ALGEBRA_DECOMPOSITION_PROFILE,
        "profile_validation_status": (
            "validated_local_typed_commutative_algebra_decomposition_v1_sealed"
        ),
        "compiler_receipt_status": "verified_local_pinned_workspace",
        "admission_status": (
            "sealed-local-authoring-revision: not a DB Draft or an OpenMath-to-Lean "
            "translation receipt"
        ),
        "alignment": {
            "status": "sealed_local_authoring_review_not_admitted",
            "statement_to_openmath": alignment,
            "openmath_to_lean": (
                "reviewed against the named direct Mathlib ideal theorem under the explicit "
                "PrimaryIdeal/PrimeIdeal witness convention"
            ),
            "admission_gate": (
                "requires independent project review before any typed catalog admission"
            ),
        },
    }


def _cards() -> list[dict[str, Any]]:
    return [
        _card(
            "commalg_decomp_ideal_le_radical",
            "可換環 R の任意の ideal I はその radical √I に含まれる。",
            "radical の定義で指数 1 を選ぶ。",
            _steps(
                "可換環 R と ideal I を固定する。",
                "I の任意の元を取る。",
                "その1乗が I に属することを使う。",
                "I⊆√I を結論する。",
            ),
            _base(("I", IDEAL_R)),
            _le(I, _radical(I)),
            "I ≤ I.radical",
            "by\n  exact Ideal.le_radical",
            "ideal_le(R,I,ideal_radical(R,I)) is exactly I⊆√I over one carrier R.",
        ),
        _card(
            "commalg_decomp_radical_idempotent",
            "任意の ideal I について √(√I)=√I。",
            "radical が radical ideal であることを用いる。",
            _steps(
                "R と I を固定する。",
                "√I が radical ideal であることを確認する。",
                "radical ideal に再度 radical を取る。",
                "等式を結論する。",
            ),
            _base(("I", IDEAL_R)),
            _eq(_radical(_radical(I)), _radical(I)),
            "I.radical.radical = I.radical",
            "by\n  exact (Ideal.radical_isRadical I).radical",
            "equality of ideal_radical(R,ideal_radical(R,I)) and ideal_radical(R,I).",
        ),
        _card(
            "commalg_decomp_radical_inf2",
            "二つの ideal I,J について √(I∩J)=√I∩√J。",
            "radical と二項交わりの可換性を用いる。",
            _steps(
                "R と I,J を固定する。",
                "I∩J を明示的な ideal_inf2 として形成する。",
                "radical_inf を適用する。",
                "両辺の ideal を同一 carrier R 上で結論する。",
            ),
            _base(("I", IDEAL_R), ("J", IDEAL_R)),
            _eq(_radical(_inf2(I, J)), _inf2(_radical(I), _radical(J))),
            "(I ⊓ J).radical = I.radical ⊓ J.radical",
            "by\n  exact Ideal.radical_inf I J",
            "ideal_inf2 and ideal_radical encode the two sides with explicit Ideal(R) inputs.",
        ),
        _card(
            "commalg_decomp_radical_inf3",
            "三つの ideal I,J,K について √(I∩J∩K)=√I∩√J∩√K。",
            "二項の radical-intersection 等式を二回使う。",
            _steps(
                "R と I,J,K を固定する。",
                "三項交わりを ideal_inf3 として固定する。",
                "最初の二項交わりに radical_inf を適用する。",
                "残る交わりにも同じ等式を適用する。",
                "三項の等式を閉じる。",
            ),
            _base(("I", IDEAL_R), ("J", IDEAL_R), ("K", IDEAL_R)),
            _eq(_radical(_inf3(I, J, K)), _inf3(_radical(I), _radical(J), _radical(K))),
            "(I ⊓ J ⊓ K).radical = I.radical ⊓ J.radical ⊓ K.radical",
            "by\n  rw [Ideal.radical_inf, Ideal.radical_inf]",
            "ideal_inf3 is the fixed left-associated three-component intersection over R.",
        ),
        _card(
            "commalg_decomp_prime_is_primary",
            "素 ideal P は primary ideal である。",
            "素性から primary 性を直接導く。",
            _steps(
                "R と PrimeIdeal(R) の witness P を固定する。",
                "P の基礎 ideal を primary_as_ideal で明示する。",
                "素 ideal が primary である定理を適用する。",
                "primary 性を結論する。",
            ),
            _base(("P", PRIME_R)),
            _is_primary(_prime(P)),
            "P.IsPrimary",
            "by\n  exact hP.isPrimary",
            "PrimeIdeal(R) is represented in Lean by P : Ideal R with hP : P.IsPrime.",
        ),
        _card(
            "commalg_decomp_primary_radical_prime",
            "primary ideal Q の radical √Q は素 ideal である。",
            "primary ideal の radical が素である定理を用いる。",
            _steps(
                "R と PrimaryIdeal(R) の witness Q を固定する。",
                "Q の underlying ideal を明示する。",
                "その radical に isPrime_radical を適用する。",
                "√Q が素 ideal であると結論する。",
            ),
            _base(("Q", PRIMARY_R)),
            _is_prime(_prime(_primary_radical_prime(Q))),
            "Q.radical.IsPrime",
            "by\n  exact Ideal.isPrime_radical hQ",
            "primary_radical_prime(R,Q) denotes the prime witness with underlying ideal √Q.",
        ),
        _card(
            "commalg_decomp_primary_ne_top",
            "primary ideal Q は全 ideal ではない。",
            "primary 性に含まれる properness を使う。",
            _steps(
                "R と Q を固定する。",
                "Q を PrimaryIdeal(R) として読む。",
                "primary ideal の properness を取り出す。",
                "Q≠⊤ を結論する。",
            ),
            _base(("Q", PRIMARY_R)),
            _neq(_primary(Q), _ideal_top()),
            "Q ≠ ⊤",
            "by\n  exact hQ.ne_top",
            "PrimaryIdeal(R) is explicitly converted before comparison with ideal_top(R).",
        ),
        _card(
            "commalg_decomp_radical_is_radical",
            "任意の ideal I の radical √I は radical ideal である。",
            "radical の閉包性を用いる。",
            _steps(
                "R と I を固定する。",
                "√I を ideal_radical として作る。",
                "radical_isRadical を適用する。",
                "√I が radical ideal であると結論する。",
            ),
            _base(("I", IDEAL_R)),
            _is_radical(_radical(I)),
            "I.radical.IsRadical",
            "by\n  exact Ideal.radical_isRadical I",
            "is_radical_ideal(R,ideal_radical(R,I)) names the same radical-ideal assertion.",
        ),
        _card(
            "commalg_decomp_primary_inf_common_radical",
            "同じ radical を持つ primary ideals Q₁,Q₂ の交わりは primary である。",
            "同 radical の primary ideals の交わりに関する定理を使う。",
            _steps(
                "R と Q₁,Q₂ を固定する。",
                "両者の radical が等しいと仮定する。",
                "underlying ideals の交わりを形成する。",
                "同 radical の交わりの primary 性を適用する。",
                "結論を閉じる。",
            ),
            _base(("Q1", PRIMARY_R), ("Q2", PRIMARY_R)),
            _implies(
                _eq(_radical(_primary(Q1)), _radical(_primary(Q2))),
                _is_primary(_inf2(_primary(Q1), _primary(Q2))),
            ),
            "(Q1 ⊓ Q2).IsPrimary",
            "by\n  exact hQ1.inf hQ2 hrad",
            (
                "the antecedent is Q1.radical=Q2.radical; each component has a "
                "PrimaryIdeal(R) witness."
            ),
        ),
        _card(
            "commalg_decomp_common_radical_inf_radical",
            "√Q₁=√Q₂ ならば √(Q₁∩Q₂)=√Q₁。",
            "radical of intersection を仮定の等式で簡約する。",
            _steps(
                "R と Q₁,Q₂ を固定する。",
                "二つの radical の等式を仮定する。",
                "交わりの radical を二項公式で展開する。",
                "仮定で右辺を同じ ideal に置換する。",
                "冪等な交わりを簡約する。",
            ),
            _base(("Q1", PRIMARY_R), ("Q2", PRIMARY_R)),
            _implies(
                _eq(_radical(_primary(Q1)), _radical(_primary(Q2))),
                _eq(_radical(_inf2(_primary(Q1), _primary(Q2))), _radical(_primary(Q1))),
            ),
            "(Q1 ⊓ Q2).radical = Q1.radical",
            "by\n  rw [Ideal.radical_inf, hrad, inf_idem]",
            "the equality is over the explicit underlying Ideal(R) values of Q1 and Q2.",
        ),
        _card(
            "commalg_decomp_primary_minimal_primes_singleton",
            "primary ideal Q の radical √Q は Q の上の極小素 ideal である。",
            "primary ideal の minimal-prime singleton 定理から要素を取る。",
            _steps(
                "R と primary component Q を固定する。",
                "Q の radical が素であることを使う。",
                "Q の極小素 ideal 全体が √Q の singleton になる定理を適用する。",
                "√Q が極小素 ideal であると結論する。",
            ),
            _base(("Q", PRIMARY_R)),
            _minimal_prime_over(_primary_radical_prime(Q), _primary(Q)),
            "Q.radical ∈ Q.minimalPrimes",
            "by\n  rw [Ideal.minimalPrimes_eq_subsingleton hQ]\n  simp",
            ("minimal_prime_over uses primary_radical_prime(R,Q) over Q's underlying ideal."),
        ),
        _card(
            "commalg_decomp_prime_minimal_primes_singleton",
            "素 ideal P は P 自身の上で極小素 ideal である。",
            "P の上の素 ideal の極小性を反射律で示す。",
            _steps(
                "R と prime witness P を固定する。",
                "P の underlying ideal を明示する。",
                "素 ideal の minimal-prime singleton 定理を使う。",
                "P が自分自身の上で極小であると結論する。",
            ),
            _base(("P", PRIME_R)),
            _minimal_prime_over(P, _prime(P)),
            "P ∈ P.minimalPrimes",
            "by\n  letI : P.IsPrime := hP\n  rw [Ideal.minimalPrimes_eq_subsingleton_self]\n  simp",
            "minimal_prime_over(R,P,prime_as_ideal(R,P)) retains the exact prime witness P.",
        ),
        _card(
            "commalg_decomp_primary_underlying_is_primary",
            "PrimaryIdeal(R) の underlying ideal は primary ideal として扱える。",
            "primary witness の型付け規約を展開する。",
            _steps(
                "R と PrimaryIdeal(R) の Q を固定する。",
                "primary_as_ideal により underlying ideal を取り出す。",
                "その型に付随する primary witness を読む。",
                "primary 性を結論する。",
            ),
            _base(("Q", PRIMARY_R)),
            _is_primary(_primary(Q)),
            "Q.IsPrimary",
            "by\n  exact hQ",
            "PrimaryIdeal(R) is a witness-bearing profile sort, not an implicit coercion.",
        ),
        _card(
            "commalg_decomp_two_component_reconstruct",
            "I=Q₁∩Q₂ という二成分 primary decomposition はその等式を再構成する。",
            "分解 witness の定義を展開する。",
            _steps(
                "R、I、二つの primary components を固定する。",
                "primary_decomposition2 witness を仮定する。",
                "witness に含まれる intersection 等式を取り出す。",
                "I=Q₁∩Q₂ を結論する。",
            ),
            _base(("I", IDEAL_R), ("Q1", PRIMARY_R), ("Q2", PRIMARY_R)),
            _implies(_decomp2(I, Q1, Q2), _eq(I, _inf2(_primary(Q1), _primary(Q2)))),
            "I = Q1 ⊓ Q2",
            "by\n  exact h",
            "primary_decomposition2(R,I,Q1,Q2) includes exactly I=underlying(Q1)∩underlying(Q2).",
        ),
        _card(
            "commalg_decomp_two_component_radical",
            "I=Q₁∩Q₂ ならば √I=√Q₁∩√Q₂。",
            "分解等式の後に radical-intersection 公式を適用する。",
            _steps(
                "二成分 primary decomposition witness を仮定する。",
                "I を Q₁∩Q₂ に置換する。",
                "radical_inf を適用する。",
                "各 component の radical の交わりとして結論する。",
            ),
            _base(("I", IDEAL_R), ("Q1", PRIMARY_R), ("Q2", PRIMARY_R)),
            _implies(
                _decomp2(I, Q1, Q2),
                _eq(
                    _radical(I),
                    _inf2(_radical(_primary(Q1)), _radical(_primary(Q2))),
                ),
            ),
            "I.radical = Q1.radical ⊓ Q2.radical",
            "by\n  rw [h]\n  exact Ideal.radical_inf Q1 Q2",
            "the decomposition witness is expanded in Lean as h : I=Q1⊓Q2 with primary hypotheses.",
        ),
        _card(
            "commalg_decomp_two_component_le_left",
            "I=Q₁∩Q₂ ならば I⊆Q₁。",
            "交わりの左射影を使う。",
            _steps(
                "二成分 decomposition witness を仮定する。",
                "I を Q₁∩Q₂ に書き換える。",
                "交わりから第一 component への包含を使う。",
                "I⊆Q₁ を結論する。",
            ),
            _base(("I", IDEAL_R), ("Q1", PRIMARY_R), ("Q2", PRIMARY_R)),
            _implies(_decomp2(I, Q1, Q2), _le(I, _primary(Q1))),
            "I ≤ Q1",
            "by\n  rw [h]\n  exact inf_le_left",
            "the target uses primary_as_ideal(R,Q1), so no component coercion is implicit.",
        ),
        _card(
            "commalg_decomp_two_component_le_right",
            "I=Q₁∩Q₂ ならば I⊆Q₂。",
            "交わりの右射影を使う。",
            _steps(
                "二成分 decomposition witness を仮定する。",
                "I を Q₁∩Q₂ に書き換える。",
                "交わりから第二 component への包含を使う。",
                "I⊆Q₂ を結論する。",
            ),
            _base(("I", IDEAL_R), ("Q1", PRIMARY_R), ("Q2", PRIMARY_R)),
            _implies(_decomp2(I, Q1, Q2), _le(I, _primary(Q2))),
            "I ≤ Q2",
            "by\n  rw [h]\n  exact inf_le_right",
            "the target uses primary_as_ideal(R,Q2), so no component coercion is implicit.",
        ),
        _card(
            "commalg_decomp_three_component_reconstruct",
            "I=Q₁∩Q₂∩Q₃ という三成分 primary decomposition はその等式を再構成する。",
            "三成分 decomposition witness の定義を展開する。",
            _steps(
                "R、I、三つの primary components を固定する。",
                "primary_decomposition3 witness を仮定する。",
                "witness に含まれる三項 intersection 等式を取り出す。",
                "I=Q₁∩Q₂∩Q₃ を結論する。",
            ),
            _base(("I", IDEAL_R), ("Q1", PRIMARY_R), ("Q2", PRIMARY_R), ("Q3", PRIMARY_R)),
            _implies(
                _decomp3(I, Q1, Q2, Q3),
                _eq(I, _inf3(_primary(Q1), _primary(Q2), _primary(Q3))),
            ),
            "I = Q1 ⊓ Q2 ⊓ Q3",
            "by\n  exact h",
            "primary_decomposition3 has only the explicit three components Q1,Q2,Q3 over R.",
        ),
        _card(
            "commalg_decomp_three_component_radical",
            "I=Q₁∩Q₂∩Q₃ ならば √I=√Q₁∩√Q₂∩√Q₃。",
            "三成分 decomposition 等式と二項 radical 公式を組み合わせる。",
            _steps(
                "三成分 decomposition witness を仮定する。",
                "I を三項交わりに置換する。",
                "最初の二項交わりに radical_inf を適用する。",
                "残る component にも radical_inf を適用する。",
                "三項 radical 等式を結論する。",
            ),
            _base(("I", IDEAL_R), ("Q1", PRIMARY_R), ("Q2", PRIMARY_R), ("Q3", PRIMARY_R)),
            _implies(
                _decomp3(I, Q1, Q2, Q3),
                _eq(
                    _radical(I),
                    _inf3(
                        _radical(_primary(Q1)),
                        _radical(_primary(Q2)),
                        _radical(_primary(Q3)),
                    ),
                ),
            ),
            "I.radical = Q1.radical ⊓ Q2.radical ⊓ Q3.radical",
            "by\n  rw [h, Ideal.radical_inf, Ideal.radical_inf]",
            "all three primary components are explicit and share the same ring carrier R.",
        ),
        _card(
            "commalg_decomp_three_component_le_first",
            "I=Q₁∩Q₂∩Q₃ ならば I⊆Q₁。",
            "二回の交わり射影を合成する。",
            _steps(
                "三成分 decomposition witness を仮定する。",
                "I を三項交わりに書き換える。",
                "外側の交わりから最初の二項交わりへ射影する。",
                "内側の交わりから Q₁ へ射影する。",
                "I⊆Q₁ を結論する。",
            ),
            _base(("I", IDEAL_R), ("Q1", PRIMARY_R), ("Q2", PRIMARY_R), ("Q3", PRIMARY_R)),
            _implies(_decomp3(I, Q1, Q2, Q3), _le(I, _primary(Q1))),
            "I ≤ Q1",
            "by\n  rw [h]\n  exact le_trans inf_le_left inf_le_left",
            "the first projection ends at primary_as_ideal(R,Q1).",
        ),
        _card(
            "commalg_decomp_irredundant2_omit_first_changes",
            "二成分分解が irredundant なら、第一成分を除いた Q₂ は I と一致しない。",
            "irredundance の Q₂⊄Q₁ 側と交わりの左射影を使う。",
            _steps(
                "R、I、Q₁,Q₂ を固定する。",
                "irredundant_decomposition2 witness を仮定する。",
                "I=Q₂ と仮定して分解等式へ戻す。",
                "Q₂⊆Q₁ が出て irredundance に矛盾する。",
                "I≠Q₂ を結論する。",
            ),
            _base(("I", IDEAL_R), ("Q1", PRIMARY_R), ("Q2", PRIMARY_R)),
            _implies(_irredundant2(I, Q1, Q2), _neq(I, _primary(Q2))),
            "I ≠ Q2",
            "by\n  intro hI\n  apply hnot\n  rw [← hI, h]\n  exact inf_le_left",
            "irredundant_decomposition2 expands to the decomposition equality and Q2⊄Q1.",
        ),
        _card(
            "commalg_decomp_irredundant2_omit_second_changes",
            "二成分分解が irredundant なら、第二成分を除いた Q₁ は I と一致しない。",
            "irredundance の Q₁⊄Q₂ 側と交わりの右射影を使う。",
            _steps(
                "R、I、Q₁,Q₂ を固定する。",
                "irredundant_decomposition2 witness を仮定する。",
                "I=Q₁ と仮定して分解等式へ戻す。",
                "Q₁⊆Q₂ が出て irredundance に矛盾する。",
                "I≠Q₁ を結論する。",
            ),
            _base(("I", IDEAL_R), ("Q1", PRIMARY_R), ("Q2", PRIMARY_R)),
            _implies(_irredundant2(I, Q1, Q2), _neq(I, _primary(Q1))),
            "I ≠ Q1",
            "by\n  intro hI\n  apply hnot\n  rw [← hI, h]\n  exact inf_le_right",
            "irredundant_decomposition2 expands to the decomposition equality and Q1⊄Q2.",
        ),
    ]


def _payload() -> dict[str, Any]:
    cards = _cards()
    if len(cards) != 22:
        raise ValueError("CA-4 core must seal exactly 22 original cards")
    profile = {
        "id": TYPED_COMMUTATIVE_ALGEBRA_DECOMPOSITION_PROFILE,
        "typed_cdbase": TYPED,
        "design_path": "docs/typed-commutative-algebra-decomposition-v1-design.md",
        "design_sha256": _sha256(DESIGN.read_bytes()),
        "registry_path": (
            "pals_agent/content_dictionaries/"
            "typed-commutative-algebra-decomposition-v1-registry.json"
        ),
        "registry_sha256": _sha256(REGISTRY.read_bytes()),
        "validator": (
            "pals_agent.typed_commutative_algebra_decomposition."
            "validate_canonical_typed_commutative_algebra_decomposition_openmath_xml"
        ),
        "validator_path": "pals_agent/typed_commutative_algebra_decomposition.py",
        "validator_sha256": _sha256(VALIDATOR.read_bytes()),
        "canonicalizer_version": "openmath-cdbase-alpha-c14n-v4",
    }
    receipt = {
        "witness_path": "docs/typed-commutative-algebra-decomposition-v1-authoring-witnesses.lean",
        "witness_file_sha256": _sha256(WITNESS.read_bytes()),
        "toolchain_path": "pals-agent/lean-workspace/lean-toolchain",
        "toolchain": TOOLCHAIN.read_text(encoding="utf-8").rstrip("\n"),
        "toolchain_sha256": _sha256(TOOLCHAIN.read_bytes()),
        "verification_command": VERIFY,
        "verification_status": "verified_local_pinned_workspace",
    }
    payload: dict[str, Any] = {
        "schema_version": "pals.typed-commutative-algebra-decomposition-v1-sealed-manifest.v1",
        "status": "sealed_local_authoring_revision_not_admitted",
        "seal": {
            "scope": (
                "local typed commutative-algebra primary-decomposition authoring evidence only"
            ),
            "admission": "not admitted to the generic DB, seed, embedding index, or PFI package",
            "revision": "typed-commutative-algebra-decomposition-v1-local-r1",
        },
        "profile": profile,
        "lean_receipt": receipt,
        "admitted_card_count": len(cards),
        "hard_rejects": HARD_REJECTS,
        "hard_reject_count": len(HARD_REJECTS),
        "cards": cards,
    }
    payload["manifest_payload_sha256"] = _sha256(rfc8785.dumps(payload))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT
        / "docs/typed-commutative-algebra-decomposition-v1-sealed-manifest.proposal.json",
    )
    parser.add_argument("--verify-lean", action="store_true")
    args = parser.parse_args()
    if args.verify_lean:
        result = subprocess.run(VERIFY, cwd=ROOT, shell=True, check=False)
        if result.returncode != 0:
            return result.returncode
    payload = _payload()
    args.output.write_bytes(rfc8785.dumps(payload) + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
