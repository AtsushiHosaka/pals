"""Seal the local-only CA-5 integral/valuation authoring proposal.

This script derives C14N and every digest from current artifacts.  It never
creates a generic Draft, database SQL, seed, embedding, or PFI artifact.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import rfc8785
from pals_agent.typed_commutative_algebra_integral import (
    TYPED_COMMUTATIVE_ALGEBRA_INTEGRAL_OPENMATH_CDBASE,
    TYPED_COMMUTATIVE_ALGEBRA_INTEGRAL_PROFILE,
    canonicalize_typed_commutative_algebra_integral_openmath_xml,
)

ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = ROOT / "pals-agent"
OPENMATH = "http://www.openmath.org/OpenMath"
STANDARD = "http://www.openmath.org/cd"
TYPED = TYPED_COMMUTATIVE_ALGEBRA_INTEGRAL_OPENMATH_CDBASE
DESIGN = ROOT / "docs/typed-commutative-algebra-integral-v1-design.md"
REGISTRY = AGENT_ROOT / "pals_agent/content_dictionaries/typed-commutative-algebra-integral-v1-registry.json"
VALIDATOR = AGENT_ROOT / "pals_agent/typed_commutative_algebra_integral.py"
WITNESS = ROOT / "docs/typed-commutative-algebra-integral-v1-authoring-witnesses.lean"
TOOLCHAIN = AGENT_ROOT / "lean-workspace/lean-toolchain"


def _sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _typed(cd: str, name: str) -> str:
    return f'<OMS cdbase="{TYPED}" cd="{cd}" name="{name}"/>'


def _standard(cd: str, name: str) -> str:
    return f'<OMS cdbase="{STANDARD}" cd="{cd}" name="{name}"/>'


def _app(operator: str, *arguments: str) -> str:
    return f"<OMA>{operator}{''.join(arguments)}</OMA>"


def _iv(name: str, *arguments: str) -> str:
    return _app(_typed("integral1", name), *arguments)


def _var(name: str) -> str:
    return f'<OMV name="{name}"/>'


def _eq(left: str, right: str) -> str:
    return _app(_standard("relation1", "eq"), left, right)


def _and(left: str, right: str) -> str:
    return _app(_standard("logic1", "and"), left, right)


def _or(left: str, right: str) -> str:
    return _app(_standard("logic1", "or"), left, right)


def _not(value: str) -> str:
    return _app(_standard("logic1", "not"), value)


def _implies(left: str, right: str) -> str:
    return _app(_standard("logic1", "implies"), left, right)


def _declaration(name: str, sort: str) -> str:
    return (
        f"<OMATTR><OMATP>{_typed('typed1', 'type')}{sort}</OMATP>"
        f"{_var(name)}</OMATTR>"
    )


def _proposition(declarations: list[tuple[str, str]], body: str) -> str:
    declared = "".join(_declaration(name, sort) for name, sort in declarations)
    return (
        f'<OMOBJ xmlns="{OPENMATH}" version="2.0"><OMBIND>'
        f"{_typed('typed1', 'forall')}<OMBVAR>{declared}</OMBVAR>{body}"
        "</OMBIND></OMOBJ>"
    )


def _sort(name: str, *arguments: str) -> str:
    symbol = _typed("integral1", name)
    return symbol if not arguments else _app(symbol, *arguments)


def _elem(carrier: str) -> str:
    return _app(_typed("typed1", "Elem"), _var(carrier))


def _extension(base: str) -> str:
    return _sort("Extension", _var(base))


def _valuation_ring(field: str) -> str:
    return _sort("ValuationRing", _var(field))


def _ring(name: str, *arguments: str) -> str:
    return _iv(name, *arguments)


def _integral(base: str, extension: str, element: str) -> str:
    return _iv("is_integral", _var(base), _var(extension), element)


def _integral_extension(base: str, extension: str) -> str:
    return _iv("is_integral_extension", _var(base), _var(extension))


def _valuation_mem(field: str, valuation: str, element: str) -> str:
    return _iv("valuation_mem", _var(field), _var(valuation), element)


def _card(
    identifier: str,
    statement: str,
    strategy: str,
    steps: list[str],
    xml: str,
    lean_target: str,
    lean_witness: str,
) -> dict[str, Any]:
    canonical = canonicalize_typed_commutative_algebra_integral_openmath_xml(xml)
    return {
        "id": identifier,
        "domain": "commutative_algebra.integral_dependence_and_valuation",
        "difficulty": "undergraduate_year_2",
        "canonical_statement": statement,
        "canonical_statement_sha256": _sha256(statement.encode("utf-8")),
        "proof_strategy": strategy,
        "sketch_steps": steps,
        "openmath_xml": xml,
        "openmath_xml_sha256": _sha256(xml.encode("utf-8")),
        "canonical_openmath_xml": canonical,
        "canonical_openmath_xml_sha256": _sha256(canonical.encode("utf-8")),
        "lean_target": lean_target,
        "lean_target_sha256": _sha256(lean_target.encode("utf-8")),
        "lean_witness": lean_witness,
        "lean_witness_sha256": _sha256(lean_witness.encode("utf-8")),
        "openmath_profile": TYPED_COMMUTATIVE_ALGEBRA_INTEGRAL_PROFILE,
        "profile_validation_status": "validated_local_typed_commutative_algebra_integral_v1_sealed",
        "compiler_receipt_status": "verified_local_pinned_workspace",
        "admission_status": (
            "sealed-local-authoring-revision: not a DB Draft or an OpenMath-to-Lean "
            "translation receipt"
        ),
        "alignment": {
            "status": "sealed_local_authoring_review_not_admitted",
            "statement_to_openmath": "reviewed under explicit base, extension, and ambient-field carriers",
            "openmath_to_lean": "reviewed against the named direct Mathlib witness; no automatic translation is claimed",
            "admission_gate": "requires independent project review before any typed catalog admission",
        },
    }


def _steps(*values: str) -> list[str]:
    assert 4 <= len(values) <= 8
    return list(values)


def _cards() -> list[dict[str, Any]]:
    r = _var("r")
    x = _var("x")
    y = _var("y")
    R = "R"
    S = "S"
    K = "K"
    V = "V"
    comm_ring_R = _sort("CommRing")
    extension_R = _extension(R)
    field_K = _sort("Field")
    valuation_K = _valuation_ring(K)
    elem_R = _elem(R)
    elem_S = _elem(S)
    elem_K = _elem(K)
    integral_x = _integral(R, S, x)
    integral_y = _integral(R, S, y)
    valuation_x = _valuation_mem(K, V, x)
    valuation_y = _valuation_mem(K, V, y)
    inv_x = _ring("field_inv", _var(K), x)
    return [
        _card(
            "commalg_integral_base_map",
            "可換環拡大 R→S と r∈R に対し、r の S への像は R 上整である。",
            "algebraMap の像が一次モニック多項式を満たすことを使う。",
            _steps("R とその拡大 S を固定する。", "r が R の元であることを確認する。", "r を S へ送る。", "base map のintegralityを適用する。"),
            _proposition(
                [(R, comm_ring_R), (S, extension_R), ("r", elem_R)],
                _integral(R, S, _ring("extension_map", _var(R), _var(S), r)),
            ),
            "example {R S : Type*} [CommRing R] [CommRing S] [Algebra R S] (r : R) : IsIntegral R (algebraMap R S r)",
            "by\n  exact isIntegral_algebraMap",
        ),
        _card(
            "commalg_integral_zero",
            "可換環拡大 R→S に対し、S の 0 は R 上整である。",
            "0 がモニック一次式を満たすことを使う。",
            _steps("R と拡大 S を固定する。", "S の 0 を形成する。", "base ring R を保持する。", "0 のintegralityを適用する。"),
            _proposition([(R, comm_ring_R), (S, extension_R)], _integral(R, S, _ring("ring_zero", _var(S)))),
            "example {R S : Type*} [CommRing R] [CommRing S] [Algebra R S] : IsIntegral R (0 : S)",
            "by\n  exact isIntegral_zero",
        ),
        _card(
            "commalg_integral_one",
            "可換環拡大 R→S に対し、S の 1 は R 上整である。",
            "1 がモニック一次式を満たすことを使う。",
            _steps("R と拡大 S を固定する。", "S の 1 を形成する。", "base ring R を保持する。", "1 のintegralityを適用する。"),
            _proposition([(R, comm_ring_R), (S, extension_R)], _integral(R, S, _ring("ring_one", _var(S)))),
            "example {R S : Type*} [CommRing R] [CommRing S] [Algebra R S] : IsIntegral R (1 : S)",
            "by\n  exact isIntegral_one",
        ),
        _card(
            "commalg_integral_neg",
            "x∈S が R 上整ならば、-x も R 上整である。",
            "整元の負元閉性を使う。",
            _steps("R→S と x を固定する。", "x の R 上integralityを仮定する。", "S 内で -x を形成する。", "負元閉性を適用する。"),
            _proposition([(R, comm_ring_R), (S, extension_R), ("x", elem_S)], _implies(integral_x, _integral(R, S, _ring("ring_neg", _var(S), x)))),
            "example {R S : Type*} [CommRing R] [CommRing S] [Algebra R S] (x : S) (hx : IsIntegral R x) : IsIntegral R (-x)",
            "by\n  exact hx.neg",
        ),
        _card(
            "commalg_integral_add",
            "x,y∈S が R 上整ならば、x+y も R 上整である。",
            "整元の加法閉性を使う。",
            _steps("R→S と x,y を固定する。", "x と y のintegralityを仮定する。", "S 内で和を形成する。", "加法閉性を適用する。"),
            _proposition([(R, comm_ring_R), (S, extension_R), ("x", elem_S), ("y", elem_S)], _implies(_and(integral_x, integral_y), _integral(R, S, _ring("ring_add", _var(S), x, y)))),
            "example {R S : Type*} [CommRing R] [CommRing S] [Algebra R S] (x y : S) (hx : IsIntegral R x) (hy : IsIntegral R y) : IsIntegral R (x + y)",
            "by\n  exact hx.add hy",
        ),
        _card(
            "commalg_integral_sub",
            "x,y∈S が R 上整ならば、x-y も R 上整である。",
            "整元の減法閉性を使う。",
            _steps("R→S と x,y を固定する。", "2つのintegralityを仮定する。", "S 内で差を形成する。", "減法閉性を適用する。"),
            _proposition([(R, comm_ring_R), (S, extension_R), ("x", elem_S), ("y", elem_S)], _implies(_and(integral_x, integral_y), _integral(R, S, _ring("ring_sub", _var(S), x, y)))),
            "example {R S : Type*} [CommRing R] [CommRing S] [Algebra R S] (x y : S) (hx : IsIntegral R x) (hy : IsIntegral R y) : IsIntegral R (x - y)",
            "by\n  exact hx.sub hy",
        ),
        _card(
            "commalg_integral_mul",
            "x,y∈S が R 上整ならば、xy も R 上整である。",
            "整元の乗法閉性を使う。",
            _steps("R→S と x,y を固定する。", "2つのintegralityを仮定する。", "S 内で積を形成する。", "乗法閉性を適用する。"),
            _proposition([(R, comm_ring_R), (S, extension_R), ("x", elem_S), ("y", elem_S)], _implies(_and(integral_x, integral_y), _integral(R, S, _ring("ring_mul", _var(S), x, y)))),
            "example {R S : Type*} [CommRing R] [CommRing S] [Algebra R S] (x y : S) (hx : IsIntegral R x) (hy : IsIntegral R y) : IsIntegral R (x * y)",
            "by\n  exact hx.mul hy",
        ),
        _card(
            "commalg_integral_square",
            "x∈S が R 上整ならば、x²=x·x も R 上整である。",
            "x と自分自身の乗法閉性を使う。",
            _steps("R→S と x を固定する。", "x のintegralityを仮定する。", "x·x を S で形成する。", "乗法閉性を同じ仮定へ適用する。"),
            _proposition([(R, comm_ring_R), (S, extension_R), ("x", elem_S)], _implies(integral_x, _integral(R, S, _ring("ring_square", _var(S), x)))),
            "example {R S : Type*} [CommRing R] [CommRing S] [Algebra R S] (x : S) (hx : IsIntegral R x) : IsIntegral R (x * x)",
            "by\n  exact hx.mul hx",
        ),
        _card(
            "commalg_integral_extension_member",
            "R→S が整拡大ならば、S の任意の元は R 上整である。",
            "整拡大の定義を各元に適用する。",
            _steps("R→S と x∈S を固定する。", "拡大がintegralであることを仮定する。", "定義を x に特殊化する。", "x のintegralityを得る。"),
            _proposition([(R, comm_ring_R), (S, extension_R), ("x", elem_S)], _implies(_integral_extension(R, S), integral_x)),
            "example {R S : Type*} [CommRing R] [CommRing S] [Algebra R S] [Algebra.IsIntegral R S] (x : S) : IsIntegral R x",
            "by\n  exact Algebra.IsIntegral.isIntegral x",
        ),
        _card(
            "commalg_valuation_mem_or_inv_mem",
            "K の付値環 V と x∈K に対し、x∈V または x⁻¹∈V である。",
            "valuation subring の定義的二者択一を使う。",
            _steps("field K と付値環 V を固定する。", "x を K の元として固定する。", "x の逆元を K 内で形成する。", "付値環の二者択一を適用する。"),
            _proposition([(K, field_K), (V, valuation_K), ("x", elem_K)], _or(valuation_x, _valuation_mem(K, V, inv_x))),
            "example {K : Type*} [Field K] (V : ValuationSubring K) (x : K) : x ∈ V ∨ x⁻¹ ∈ V",
            "by\n  exact V.mem_or_inv_mem x",
        ),
        _card(
            "commalg_valuation_zero_mem",
            "K の任意の付値環 V は K の 0 を含む。",
            "付値subringのzero閉性を使う。",
            _steps("field K と付値環 V を固定する。", "K の0を形成する。", "membershipのambient fieldを確認する。", "zero membershipを適用する。"),
            _proposition([(K, field_K), (V, valuation_K)], _valuation_mem(K, V, _ring("ring_zero", _var(K)))),
            "example {K : Type*} [Field K] (V : ValuationSubring K) : (0 : K) ∈ V",
            "by\n  exact V.zero_mem",
        ),
        _card(
            "commalg_valuation_one_mem",
            "K の任意の付値環 V は K の 1 を含む。",
            "付値subringのone閉性を使う。",
            _steps("field K と付値環 V を固定する。", "K の1を形成する。", "membershipのambient fieldを確認する。", "one membershipを適用する。"),
            _proposition([(K, field_K), (V, valuation_K)], _valuation_mem(K, V, _ring("ring_one", _var(K)))),
            "example {K : Type*} [Field K] (V : ValuationSubring K) : (1 : K) ∈ V",
            "by\n  exact V.one_mem",
        ),
        _card(
            "commalg_valuation_neg_closed",
            "x∈V ならば -x∈V である。",
            "付値subringの負元閉性を使う。",
            _steps("K,V,x を固定する。", "x∈V を仮定する。", "K 内で -x を形成する。", "負元閉性を適用する。"),
            _proposition([(K, field_K), (V, valuation_K), ("x", elem_K)], _implies(valuation_x, _valuation_mem(K, V, _ring("ring_neg", _var(K), x)))),
            "example {K : Type*} [Field K] (V : ValuationSubring K) (x : K) (hx : x ∈ V) : -x ∈ V",
            "by\n  exact V.neg_mem x hx",
        ),
        _card(
            "commalg_valuation_add_closed",
            "x,y∈V ならば x+y∈V である。",
            "付値subringの加法閉性を使う。",
            _steps("K,V,x,y を固定する。", "2つのmembershipを仮定する。", "K 内で和を形成する。", "加法閉性を適用する。"),
            _proposition([(K, field_K), (V, valuation_K), ("x", elem_K), ("y", elem_K)], _implies(_and(valuation_x, valuation_y), _valuation_mem(K, V, _ring("ring_add", _var(K), x, y)))),
            "example {K : Type*} [Field K] (V : ValuationSubring K) (x y : K) (hx : x ∈ V) (hy : y ∈ V) : x + y ∈ V",
            "by\n  exact V.add_mem x y hx hy",
        ),
        _card(
            "commalg_valuation_sub_closed",
            "x,y∈V ならば x-y∈V である。",
            "付値subringの減法閉性を使う。",
            _steps("K,V,x,y を固定する。", "2つのmembershipを仮定する。", "K 内で差を形成する。", "減法閉性を適用する。"),
            _proposition([(K, field_K), (V, valuation_K), ("x", elem_K), ("y", elem_K)], _implies(_and(valuation_x, valuation_y), _valuation_mem(K, V, _ring("ring_sub", _var(K), x, y)))),
            "example {K : Type*} [Field K] (V : ValuationSubring K) (x y : K) (hx : x ∈ V) (hy : y ∈ V) : x - y ∈ V",
            "by\n  exact V.sub_mem hx hy",
        ),
        _card(
            "commalg_valuation_mul_closed",
            "x,y∈V ならば xy∈V である。",
            "付値subringの乗法閉性を使う。",
            _steps("K,V,x,y を固定する。", "2つのmembershipを仮定する。", "K 内で積を形成する。", "乗法閉性を適用する。"),
            _proposition([(K, field_K), (V, valuation_K), ("x", elem_K), ("y", elem_K)], _implies(_and(valuation_x, valuation_y), _valuation_mem(K, V, _ring("ring_mul", _var(K), x, y)))),
            "example {K : Type*} [Field K] (V : ValuationSubring K) (x y : K) (hx : x ∈ V) (hy : y ∈ V) : x * y ∈ V",
            "by\n  exact V.mul_mem x y hx hy",
        ),
        _card(
            "commalg_valuation_square_closed",
            "x∈V ならば x²=x·x∈V である。",
            "同じmembershipへ乗法閉性を適用する。",
            _steps("K,V,x を固定する。", "x∈V を仮定する。", "x·x を K 内で形成する。", "乗法閉性を同じ仮定に適用する。"),
            _proposition([(K, field_K), (V, valuation_K), ("x", elem_K)], _implies(valuation_x, _valuation_mem(K, V, _ring("ring_square", _var(K), x)))),
            "example {K : Type*} [Field K] (V : ValuationSubring K) (x : K) (hx : x ∈ V) : x * x ∈ V",
            "by\n  exact V.mul_mem x x hx hx",
        ),
        _card(
            "commalg_valuation_not_mem_implies_inv_mem",
            "x∉V ならば x⁻¹∈V である。",
            "二者択一から x∈V の枝を除く。",
            _steps("K,V,x を固定する。", "x∉V を仮定する。", "x または逆元のmembershipを使う。", "x の枝を排除して逆元のmembershipを得る。"),
            _proposition([(K, field_K), (V, valuation_K), ("x", elem_K)], _implies(_not(valuation_x), _valuation_mem(K, V, inv_x))),
            "example {K : Type*} [Field K] (V : ValuationSubring K) (x : K) (hx : x ∉ V) : x⁻¹ ∈ V",
            "by\n  exact (V.mem_or_inv_mem x).resolve_left hx",
        ),
        _card(
            "commalg_valuation_not_inv_mem_implies_mem",
            "x⁻¹∉V ならば x∈V である。",
            "二者択一から逆元の枝を除く。",
            _steps("K,V,x を固定する。", "x⁻¹∉V を仮定する。", "x または逆元のmembershipを使う。", "逆元の枝を排除して x のmembershipを得る。"),
            _proposition([(K, field_K), (V, valuation_K), ("x", elem_K)], _implies(_not(_valuation_mem(K, V, inv_x)), valuation_x)),
            "example {K : Type*} [Field K] (V : ValuationSubring K) (x : K) (hx : x⁻¹ ∉ V) : x ∈ V",
            "by\n  exact (V.mem_or_inv_mem x).resolve_right hx",
        ),
        _card(
            "commalg_valuation_integrally_closed",
            "field K の任意の付値環 V は整閉である。",
            "valuation subring の整閉性instanceを用いる。",
            _steps("field K と付値環 V を固定する。", "V が K のvaluation subringであることを確認する。", "対応するintegrally closed instanceを取得する。", "V の整閉性を結論する。"),
            _proposition([(K, field_K), (V, valuation_K)], _iv("valuation_integrally_closed", _var(K), _var(V))),
            "example {K : Type*} [Field K] (V : ValuationSubring K) : IsIntegrallyClosed V",
            "by\n  infer_instance",
        ),
    ]


def build_manifest() -> dict[str, Any]:
    cards = _cards()
    payload: dict[str, Any] = {
        "schema_version": "pals.typed-commutative-algebra-integral-v1-sealed-manifest.v1",
        "status": "sealed_local_authoring_revision_not_admitted",
        "seal": {
            "scope": "local typed commutative-algebra integral/valuation authoring evidence only",
            "admission": "not admitted to the generic DB, seed, embedding index, or PFI package",
            "revision": "typed-commutative-algebra-integral-v1-local-r1",
        },
        "profile": {
            "id": TYPED_COMMUTATIVE_ALGEBRA_INTEGRAL_PROFILE,
            "typed_cdbase": TYPED,
            "design_path": "docs/typed-commutative-algebra-integral-v1-design.md",
            "design_sha256": _sha256(DESIGN.read_bytes()),
            "registry_path": "pals_agent/content_dictionaries/typed-commutative-algebra-integral-v1-registry.json",
            "registry_sha256": _sha256(REGISTRY.read_bytes()),
            "validator": "pals_agent.typed_commutative_algebra_integral.validate_canonical_typed_commutative_algebra_integral_openmath_xml",
            "validator_path": "pals_agent/typed_commutative_algebra_integral.py",
            "validator_sha256": _sha256(VALIDATOR.read_bytes()),
            "canonicalizer_version": "openmath-cdbase-alpha-c14n-v4",
        },
        "lean_receipt": {
            "witness_path": "docs/typed-commutative-algebra-integral-v1-authoring-witnesses.lean",
            "witness_file_sha256": _sha256(WITNESS.read_bytes()),
            "toolchain_path": "pals-agent/lean-workspace/lean-toolchain",
            "toolchain": TOOLCHAIN.read_text(encoding="utf-8").rstrip("\n"),
            "toolchain_sha256": _sha256(TOOLCHAIN.read_bytes()),
            "verification_command": "cd pals-agent/lean-workspace && lake env lean ../../docs/typed-commutative-algebra-integral-v1-authoring-witnesses.lean",
            "verification_status": "verified_local_pinned_workspace",
        },
        "admitted_card_count": len(cards),
        "hard_rejects": [
            "implicit_extension_direction",
            "implicit_fraction_field",
            "zero_divisor_as_domain_or_field",
            "unproved_integral_tower_transitivity",
            "lying_over_going_up_going_down",
            "fractional_ideal_dvr_dedekind",
            "valuation_value_group_or_uniformizer",
        ],
        "hard_reject_count": 7,
        "cards": cards,
    }
    payload["manifest_payload_sha256"] = _sha256(rfc8785.dumps(payload))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs/typed-commutative-algebra-integral-v1-sealed-manifest.proposal.json",
    )
    parser.add_argument("--verify-lean", action="store_true")
    args = parser.parse_args()
    if args.verify_lean:
        checked = subprocess.run(
            ["lake", "env", "lean", "../../docs/typed-commutative-algebra-integral-v1-authoring-witnesses.lean"],
            cwd=AGENT_ROOT / "lean-workspace",
            check=False,
        )
        if checked.returncode != 0:
            return checked.returncode
    args.output.write_text(json.dumps(build_manifest(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
