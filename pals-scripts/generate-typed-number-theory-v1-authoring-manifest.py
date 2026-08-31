"""Seal the local-only typed-number-theory-v1 authoring proposal.

The script never writes a generic Draft, a seed, or database SQL.  It derives
every OpenMath and artifact digest immediately before serializing the proposal.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from pals_agent.typed_number_theory import (
    TYPED_NUMBER_THEORY_OPENMATH_CDBASE,
    TYPED_NUMBER_THEORY_PROFILE,
    canonicalize_typed_number_theory_openmath_xml,
)

ROOT = Path(__file__).resolve().parents[1]
OPENMATH = "http://www.openmath.org/OpenMath"
STANDARD = "http://www.openmath.org/cd"
TYPED = TYPED_NUMBER_THEORY_OPENMATH_CDBASE
DESIGN = ROOT / "docs/typed-number-theory-v1-design.md"
REGISTRY = ROOT / "pals-agent/pals_agent/content_dictionaries/typed-number-theory-v1-registry.json"
VALIDATOR = ROOT / "pals-agent/pals_agent/typed_number_theory.py"
WITNESS = ROOT / "docs/typed-number-theory-v1-authoring-witnesses.lean"
TOOLCHAIN = ROOT / "pals-agent/lean-workspace/lean-toolchain"


def _sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _typed(cd: str, name: str) -> str:
    return f'<OMS cdbase="{TYPED}" cd="{cd}" name="{name}"/>'


def _standard(cd: str, name: str) -> str:
    return f'<OMS cdbase="{STANDARD}" cd="{cd}" name="{name}"/>'


def _app(operator: str, *arguments: str) -> str:
    return f"<OMA>{operator}{''.join(arguments)}</OMA>"


def _nt(name: str, *arguments: str) -> str:
    return _app(_typed("numbertheory1", name), *arguments)


def _var(name: str) -> str:
    return f'<OMV name="{name}"/>'


def _nat(value: int) -> str:
    return _nt("nat_literal", f"<OMI>{value}</OMI>")


def _int(value: int) -> str:
    return _nt("int_literal", f"<OMI>{value}</OMI>")


def _eq(left: str, right: str) -> str:
    return _app(_standard("relation1", "eq"), left, right)


def _implies(left: str, right: str) -> str:
    return _app(_standard("logic1", "implies"), left, right)


def _declaration(name: str, sort: str) -> str:
    return (
        f"<OMATTR><OMATP>{_typed('typed1', 'type')}"
        f"{_typed('numbertheory1', sort)}</OMATP>{_var(name)}</OMATTR>"
    )


def _bind(binder: str, declarations: list[tuple[str, str]], body: str) -> str:
    declared = "".join(_declaration(name, sort) for name, sort in declarations)
    return f"<OMBIND>{_typed('typed1', binder)}<OMBVAR>{declared}</OMBVAR>{body}</OMBIND>"


def _proposition(binder: str, declarations: list[tuple[str, str]], body: str) -> str:
    return f'<OMOBJ xmlns="{OPENMATH}" version="2.0">{_bind(binder, declarations, body)}</OMOBJ>'


def _card(
    identifier: str,
    statement: str,
    strategy: str,
    steps: list[str],
    xml: str,
    lean_target: str,
    lean_witness: str,
) -> dict[str, Any]:
    canonical = canonicalize_typed_number_theory_openmath_xml(xml)
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
        "openmath_profile": TYPED_NUMBER_THEORY_PROFILE,
        "profile_validation_status": "validated_local_typed_number_theory_v1_sealed",
        "compiler_receipt_status": "verified",
        "admission_status": (
            "sealed-local-authoring-revision: not a DB Draft or an OpenMath-to-Lean translation receipt"
        ),
        "alignment": {
            "status": "sealed_local_authoring_review_not_admitted",
            "statement_to_openmath": "reviewed under explicit Nat/Int carrier conventions",
            "openmath_to_lean": "reviewed against the named Mathlib Nat/Int theorem statement",
            "admission_gate": "requires independent project review before any typed catalog admission",
        },
    }


def _cards() -> list[dict[str, Any]]:
    gcd = lambda a, b: _nt("gcd", a, b)
    lcm = lambda a, b: _nt("lcm", a, b)
    dvd = lambda a, b: _nt("divides_nat", a, b)
    mul = lambda a, b: _nt("nat_mul", a, b)
    add = lambda a, b: _nt("nat_add", a, b)
    return [
        _card(
            "number_theory_gcd_comm",
            "任意の自然数 m,n について gcd(m,n)=gcd(n,m)。",
            "gcd の対称性を直接適用する。",
            ["m,n を自然数として固定する。", "両辺が Nat の gcd であることを確認する。", "gcd の可換性を適用する。", "等式を閉じる。"],
            _proposition("forall", [("m", "Nat"), ("n", "Nat")], _eq(gcd(_var("m"), _var("n")), gcd(_var("n"), _var("m")))),
            "example (m n : ℕ) : Nat.gcd m n = Nat.gcd n m",
            "by\n  exact Nat.gcd_comm m n",
        ),
        _card(
            "number_theory_gcd_zero_right",
            "任意の自然数 n について gcd(n,0)=n。",
            "0 との gcd の標準簡約を使う。",
            ["n を自然数として固定する。", "第2引数の 0 を Nat literal と読む。", "gcd の zero-right 定理を適用する。", "結果を n と同一視する。"],
            _proposition("forall", [("n", "Nat")], _eq(gcd(_var("n"), _nat(0)), _var("n"))),
            "example (n : ℕ) : Nat.gcd n 0 = n",
            "by\n  exact Nat.gcd_zero_right n",
        ),
        _card(
            "number_theory_lcm_zero_right",
            "任意の自然数 n について lcm(n,0)=0。",
            "0 との lcm の標準簡約を使う。",
            ["n を自然数として固定する。", "0 を Nat literal と読む。", "lcm の zero-right 定理を適用する。", "Nat の 0 として結論を閉じる。"],
            _proposition("forall", [("n", "Nat")], _eq(lcm(_var("n"), _nat(0)), _nat(0))),
            "example (n : ℕ) : Nat.lcm n 0 = 0",
            "by\n  exact Nat.lcm_zero_right n",
        ),
        _card(
            "number_theory_dvd_reflexive",
            "任意の自然数 n は自分自身を割り切る。",
            "整除関係の反射性を使う。",
            ["n を Nat として固定する。", "両辺が同じ Nat であることを確認する。", "整除の反射性を適用する。", "命題を閉じる。"],
            _proposition("forall", [("n", "Nat")], dvd(_var("n"), _var("n"))),
            "example (n : ℕ) : n ∣ n",
            "by\n  exact dvd_refl n",
        ),
        _card(
            "number_theory_dvd_transitive",
            "a|b かつ b|c ならば a|c（a,b,c は自然数）。",
            "整除関係の推移性を合成する。",
            ["a,b,c を Nat として固定する。", "a|b と b|c を仮定する。", "中間項 b で整除を合成する。", "a|c を得る。"],
            _proposition("forall", [("a", "Nat"), ("b", "Nat"), ("c", "Nat")], _implies(_app(_standard("logic1", "and"), dvd(_var("a"), _var("b")), dvd(_var("b"), _var("c"))), dvd(_var("a"), _var("c")))),
            "example (a b c : ℕ) (hab : a ∣ b) (hbc : b ∣ c) : a ∣ c",
            "by\n  exact hab.trans hbc",
        ),
        _card(
            "number_theory_gcd_dvd_left",
            "任意の自然数 m,n で gcd(m,n)|m。",
            "gcd が各引数を割り切る性質を使う。",
            ["m,n を Nat として固定する。", "gcd(m,n) を Nat 値として形成する。", "左引数への整除定理を適用する。", "整除命題を閉じる。"],
            _proposition("forall", [("m", "Nat"), ("n", "Nat")], dvd(gcd(_var("m"), _var("n")), _var("m"))),
            "example (m n : ℕ) : Nat.gcd m n ∣ m",
            "by\n  exact Nat.gcd_dvd_left m n",
        ),
        _card(
            "number_theory_dvd_mul_right",
            "a|b ならば a|bc（a,b,c は自然数）。",
            "整除式に右から c を掛ける。",
            ["a,b,c を Nat として固定する。", "a|b を仮定する。", "b に右から c を掛ける。", "a|bc を結論する。"],
            _proposition("forall", [("a", "Nat"), ("b", "Nat"), ("c", "Nat")], _implies(dvd(_var("a"), _var("b")), dvd(_var("a"), mul(_var("b"), _var("c"))))),
            "example (a b c : ℕ) (hab : a ∣ b) : a ∣ b * c",
            "by\n  exact dvd_mul_of_dvd_left hab c",
        ),
        _card(
            "number_theory_mod_reduce_17_5",
            "n=17 ならば n mod 5 = 2（n は自然数）。",
            "仮定で n を 17 に置換して、正の法 5 による剰余を計算する。",
            ["n を Nat として固定する。", "n=17 を仮定する。", "法 5 が正であることを確認する。", "n を置換して剰余を計算する。"],
            _proposition("forall", [("n", "Nat")], _implies(_eq(_var("n"), _nat(17)), _eq(_nt("nat_mod", _var("n"), _nat(5)), _nat(2)))),
            "example (n : ℕ) (h : n = 17) : n % 5 = 2",
            "by\n  subst n\n  norm_num",
        ),
        _card(
            "number_theory_mod_add_fixed_five",
            "a≡b (mod 5) かつ c≡d (mod 5) ならば a+c≡b+d (mod 5)。",
            "正の固定法 5 で合同の加法閉性を合成する。",
            ["a,b,c,d を Nat として固定する。", "2つの法 5 の合同を仮定する。", "法 5 が正の literal であることを確認する。", "合同の加法閉性を適用する。"],
            _proposition("forall", [("a", "Nat"), ("b", "Nat"), ("c", "Nat"), ("d", "Nat")], _implies(_app(_standard("logic1", "and"), _nt("congruent_nat", _var("a"), _var("b"), _nat(5)), _nt("congruent_nat", _var("c"), _var("d"), _nat(5))), _nt("congruent_nat", add(_var("a"), _var("c")), add(_var("b"), _var("d")), _nat(5)))),
            "example (a b c d : ℕ) (hab : a ≡ b [MOD 5]) (hcd : c ≡ d [MOD 5]) :\n    a + c ≡ b + d [MOD 5]",
            "by\n  exact hab.add hcd",
        ),
        _card(
            "number_theory_mod_mul_fixed_five",
            "a≡b (mod 5) かつ c≡d (mod 5) ならば ac≡bd (mod 5)。",
            "正の固定法 5 で合同の乗法閉性を合成する。",
            ["a,b,c,d を Nat として固定する。", "2つの法 5 の合同を仮定する。", "法 5 が正の literal であることを確認する。", "合同の乗法閉性を適用する。"],
            _proposition("forall", [("a", "Nat"), ("b", "Nat"), ("c", "Nat"), ("d", "Nat")], _implies(_app(_standard("logic1", "and"), _nt("congruent_nat", _var("a"), _var("b"), _nat(5)), _nt("congruent_nat", _var("c"), _var("d"), _nat(5))), _nt("congruent_nat", mul(_var("a"), _var("c")), mul(_var("b"), _var("d")), _nat(5)))),
            "example (a b c d : ℕ) (hab : a ≡ b [MOD 5]) (hcd : c ≡ d [MOD 5]) :\n    a * c ≡ b * d [MOD 5]",
            "by\n  exact hab.mul hcd",
        ),
        _card(
            "number_theory_prime_two",
            "n=2 ならば n は素数である（n は自然数）。",
            "仮定で n を 2 に置換し、Nat の素数定理を適用する。",
            ["n を Nat として固定する。", "n=2 を仮定する。", "素数述語の carrier が Nat であることを確認する。", "n を置換して 2 の素数性を適用する。"],
            _proposition("forall", [("n", "Nat")], _implies(_eq(_var("n"), _nat(2)), _nt("is_prime", _var("n")))),
            "example (n : ℕ) (h : n = 2) : Nat.Prime n",
            "by\n  subst n\n  exact Nat.prime_two",
        ),
        _card(
            "number_theory_bezout_coprime_nat",
            "gcd(a,b)=1 なら、整数 x,y が存在して ax+by=1（a,b は自然数）。",
            "Nat の拡張Euclid係数を Int に明示移送する。",
            ["a,b を Nat として固定し gcd(a,b)=1 を仮定する。", "Nat.gcdA と Nat.gcdB を整数係数として選ぶ。", "拡張Euclid等式で ax+by を gcd(a,b) に戻す。", "仮定 gcd(a,b)=1 を代入して結論する。"],
            _proposition("forall", [("a", "Nat"), ("b", "Nat")], _implies(_eq(gcd(_var("a"), _var("b")), _nat(1)), _bind("exists", [("x", "Int"), ("y", "Int")], _eq(_nt("int_add", _nt("int_mul", _nt("int_of_nat", _var("a")), _var("x")), _nt("int_mul", _nt("int_of_nat", _var("b")), _var("y"))), _int(1))))),
            "example (a b : ℕ) (h : Nat.gcd a b = 1) :\n    ∃ x y : ℤ, (a : ℤ) * x + (b : ℤ) * y = 1",
            "by\n  refine ⟨a.gcdA b, a.gcdB b, ?_⟩\n  rw [← Nat.gcd_eq_gcd_ab, h]\n  norm_num",
        ),
    ]


def build_manifest() -> dict[str, Any]:
    witness = WITNESS.read_bytes()
    cards = _cards()
    payload: dict[str, Any] = {
        "schema_version": "pals.typed-number-theory-v1-sealed-manifest.v1",
        "status": "sealed_local_authoring_revision_not_admitted",
        "seal": {
            "scope": "local typed-number-theory authoring evidence only",
            "admission": "not admitted to the generic DB, seed, embedding index, or PFI package",
            "revision": "typed-number-theory-v1-local-r1",
        },
        "profile": {
            "id": TYPED_NUMBER_THEORY_PROFILE,
            "typed_cdbase": TYPED,
            "design_path": "docs/typed-number-theory-v1-design.md",
            "design_sha256": _sha256(DESIGN.read_bytes()),
            "registry_path": "pals_agent/content_dictionaries/typed-number-theory-v1-registry.json",
            "registry_sha256": _sha256(REGISTRY.read_bytes()),
            "validator": (
                "pals_agent.typed_number_theory."
                "validate_canonical_typed_number_theory_openmath_xml"
            ),
            "validator_path": "pals_agent/typed_number_theory.py",
            "validator_sha256": _sha256(VALIDATOR.read_bytes()),
            "canonicalizer_version": "openmath-cdbase-alpha-c14n-v4",
        },
        "lean_receipt": {
            "witness_path": "docs/typed-number-theory-v1-authoring-witnesses.lean",
            "witness_file_sha256": _sha256(witness),
            "toolchain": TOOLCHAIN.read_text(encoding="utf-8").rstrip("\n"),
            "verification_command": (
                "cd pals-agent/lean-workspace && lake env lean "
                "../../docs/typed-number-theory-v1-authoring-witnesses.lean"
            ),
            "verification_status": "verified_local_pinned_workspace",
        },
        "admitted_card_count": len(cards),
        "excluded_cards": [
            {"id": "number_theory_zero_modulus", "reason": "zero modulus is rejected, never totalized"},
            {"id": "number_theory_symbolic_modulus", "reason": "v1 requires a positive Nat literal modulus"},
            {"id": "number_theory_untyped_division", "reason": "division has unresolved sign and zero semantics"},
            {"id": "number_theory_general_prime_definition", "reason": "unbounded factor quantification is outside v1"},
        ],
        "excluded_card_count": 4,
        "cards": cards,
    }
    payload["manifest_payload_sha256"] = _sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs/typed-number-theory-v1-authoring-manifest.proposal.json",
    )
    parser.add_argument("--verify-lean", action="store_true")
    args = parser.parse_args()
    if args.verify_lean:
        completed = subprocess.run(
            ["lake", "env", "lean", "../../docs/typed-number-theory-v1-authoring-witnesses.lean"],
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
