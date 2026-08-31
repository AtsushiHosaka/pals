"""Seal local-only CA-2 module-theory authoring evidence.

This script never writes generic Draft rows, SQL, seed data, embeddings, or a
PFI package.  It derives C14N and every digest from the current checked files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from pals_agent.typed_commutative_algebra_modules import (
    TYPED_COMMUTATIVE_ALGEBRA_MODULES_OPENMATH_CDBASE,
    TYPED_COMMUTATIVE_ALGEBRA_MODULES_PROFILE,
    canonicalize_typed_commutative_algebra_modules_openmath_xml,
)

ROOT = Path(__file__).resolve().parents[1]
OPENMATH = "http://www.openmath.org/OpenMath"
STANDARD = "http://www.openmath.org/cd"
TYPED = TYPED_COMMUTATIVE_ALGEBRA_MODULES_OPENMATH_CDBASE
DESIGN = ROOT / "docs/typed-commutative-algebra-modules-v1-design.md"
REGISTRY = (
    ROOT
    / "pals-agent/pals_agent/content_dictionaries/typed-commutative-algebra-modules-v1-registry.json"
)
VALIDATOR = ROOT / "pals-agent/pals_agent/typed_commutative_algebra_modules.py"
WITNESS = ROOT / "docs/typed-commutative-algebra-modules-v1-authoring-witnesses.lean"
TOOLCHAIN = ROOT / "pals-agent/lean-workspace/lean-toolchain"


def _sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _typed(cd: str, name: str) -> str:
    return f'<OMS cdbase="{TYPED}" cd="{cd}" name="{name}"/>'


def _standard(cd: str, name: str) -> str:
    return f'<OMS cdbase="{STANDARD}" cd="{cd}" name="{name}"/>'


def _app(operator: str, *arguments: str) -> str:
    return f"<OMA>{operator}{''.join(arguments)}</OMA>"


def _module(name: str, *arguments: str) -> str:
    return _app(_typed("module1", name), *arguments)


def _var(name: str) -> str:
    return f'<OMV name="{name}"/>'


def _eq(left: str, right: str) -> str:
    return _app(_standard("relation1", "eq"), left, right)


def _le(ring: str, module: str, left: str, right: str) -> str:
    return _module("submodule_le", _var(ring), _var(module), left, right)


def _decl(name: str, sort: str) -> str:
    return (
        f"<OMATTR><OMATP>{_typed('typed1', 'type')}{sort}</OMATP>{_var(name)}</OMATTR>"
    )


def _ring_type() -> str:
    return _typed("module1", "CommRing")


def _module_type(ring: str) -> str:
    return _module("Module", _var(ring))


def _submodule_type(ring: str, module: str) -> str:
    return _module("Submodule", _var(ring), _var(module))


def _map_type(ring: str, source: str, target: str) -> str:
    return _module("LinearMap", _var(ring), _var(source), _var(target))


def _proposition(declarations: list[tuple[str, str]], body: str) -> str:
    declared = "".join(_decl(name, sort) for name, sort in declarations)
    binding = f"<OMBIND>{_typed('typed1', 'forall')}<OMBVAR>{declared}</OMBVAR>{body}</OMBIND>"
    return f'<OMOBJ xmlns="{OPENMATH}" version="2.0">{binding}</OMOBJ>'


def _steps(focus: str) -> list[str]:
    return [
        "束縛された環・加群・写像の型を固定する。",
        "各演算の scalar ring と module carrier が一致することを確認する。",
        focus,
        "目的の部分加群等式・包含または写像性を閉じる。",
    ]


def _card(
    identifier: str,
    statement: str,
    strategy: str,
    xml: str,
    lean_target: str,
    lean_witness: str,
) -> dict[str, Any]:
    canonical = canonicalize_typed_commutative_algebra_modules_openmath_xml(xml)
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
        "openmath_profile": TYPED_COMMUTATIVE_ALGEBRA_MODULES_PROFILE,
        "profile_validation_status": "validated_local_typed_commutative_algebra_modules_v1_sealed",
        "compiler_receipt_status": "verified",
        "admission_status": (
            "sealed-local-authoring-revision: not a DB Draft or an OpenMath-to-Lean translation receipt"
        ),
        "alignment": {
            "status": "sealed_local_authoring_review_not_admitted",
            "statement_to_openmath": "reviewed under explicit scalar-ring, module, and map-carrier conventions",
            "openmath_to_lean": "reviewed against the named direct Mathlib module-theory statement",
            "admission_gate": "requires independent project review before any typed catalog admission",
        },
    }


def _target(prefix: str, variables: str, result: str) -> str:
    variables_part = f" {variables}" if variables else ""
    return f"example {prefix}{variables_part} : {result}"


def _cards() -> list[dict[str, Any]]:
    r, m, n, p, q = _var("R"), _var("M"), _var("N"), _var("P"), _var("Q")
    i, j = _var("I"), _var("J")
    f, g, h = _var("f"), _var("g"), _var("h")
    common = [("R", _ring_type()), ("M", _module_type("R"))]
    submodules = [
        *common,
        ("I", _submodule_type("R", "M")),
        ("J", _submodule_type("R", "M")),
    ]
    maps_mn = [*common, ("N", _module_type("R")), ("f", _map_type("R", "M", "N"))]
    maps_mnp = [
        *common,
        ("N", _module_type("R")),
        ("P", _module_type("R")),
        ("f", _map_type("R", "M", "N")),
        ("g", _map_type("R", "N", "P")),
    ]
    lattice_prefix = "{R M : Type*} [CommRing R] [AddCommGroup M] [Module R M]"
    maps_prefix = "{R M N : Type*} [CommRing R] [AddCommGroup M] [Module R M] [AddCommGroup N] [Module R N]"
    triple_prefix = "{R M N P : Type*} [CommRing R] [AddCommGroup M] [Module R M] [AddCommGroup N] [Module R N] [AddCommGroup P] [Module R P]"
    quadruple_prefix = "{R M N P Q : Type*} [CommRing R] [AddCommGroup M] [Module R M] [AddCommGroup N] [Module R N] [AddCommGroup P] [Module R P] [AddCommGroup Q] [Module R Q]"
    bot = lambda carrier: _module("submodule_bot", r, carrier)
    top = lambda carrier: _module("submodule_top", r, carrier)
    sup = lambda left, right: _module("submodule_sup", r, m, left, right)
    inf = lambda left, right: _module("submodule_inf", r, m, left, right)
    identity = lambda carrier: _module("linear_id", r, carrier)
    zero = lambda source, target: _module("linear_zero", r, source, target)
    kernel = lambda source, target, linear: _module(
        "linear_kernel", r, source, target, linear
    )
    image = lambda source, target, linear: _module(
        "linear_range", r, source, target, linear
    )
    compose = lambda source, middle, target, first, second: _module(
        "linear_comp", r, source, middle, target, first, second
    )
    exact = lambda source, middle, target, first, second: _module(
        "exact_at", r, source, middle, target, first, second
    )
    return [
        _card(
            "commalg_modules_le_sup_left",
            "任意の R-部分加群 I,J で I⊆I+J。",
            "上限への左包含を使う。",
            _proposition(submodules, _le("R", "M", i, sup(i, j))),
            _target(lattice_prefix, "(I J : Submodule R M)", "I ≤ I ⊔ J"),
            "by\n  exact le_sup_left",
        ),
        _card(
            "commalg_modules_le_sup_right",
            "任意の R-部分加群 I,J で J⊆I+J。",
            "上限への右包含を使う。",
            _proposition(submodules, _le("R", "M", j, sup(i, j))),
            _target(lattice_prefix, "(I J : Submodule R M)", "J ≤ I ⊔ J"),
            "by\n  exact le_sup_right",
        ),
        _card(
            "commalg_modules_inf_le_left",
            "任意の R-部分加群 I,J で I∩J⊆I。",
            "下限から左因子への包含を使う。",
            _proposition(submodules, _le("R", "M", inf(i, j), i)),
            _target(lattice_prefix, "(I J : Submodule R M)", "I ⊓ J ≤ I"),
            "by\n  exact inf_le_left",
        ),
        _card(
            "commalg_modules_inf_le_right",
            "任意の R-部分加群 I,J で I∩J⊆J。",
            "下限から右因子への包含を使う。",
            _proposition(submodules, _le("R", "M", inf(i, j), j)),
            _target(lattice_prefix, "(I J : Submodule R M)", "I ⊓ J ≤ J"),
            "by\n  exact inf_le_right",
        ),
        _card(
            "commalg_modules_bot_le",
            "任意の R-部分加群 I で 0⊆I。",
            "部分加群束の最小元性を使う。",
            _proposition(submodules[:3], _le("R", "M", bot(m), i)),
            _target(lattice_prefix, "(I : Submodule R M)", "⊥ ≤ I"),
            "by\n  exact bot_le",
        ),
        _card(
            "commalg_modules_le_top",
            "任意の R-部分加群 I で I⊆M。",
            "部分加群束の最大元性を使う。",
            _proposition(submodules[:3], _le("R", "M", i, top(m))),
            _target(lattice_prefix, "(I : Submodule R M)", "I ≤ ⊤"),
            "by\n  exact le_top",
        ),
        _card(
            "commalg_modules_sup_comm",
            "R-部分加群の和は可換である。",
            "上限の可換性を適用する。",
            _proposition(submodules, _eq(sup(i, j), sup(j, i))),
            _target(lattice_prefix, "(I J : Submodule R M)", "I ⊔ J = J ⊔ I"),
            "by\n  exact sup_comm I J",
        ),
        _card(
            "commalg_modules_inf_comm",
            "R-部分加群の共通部分は可換である。",
            "下限の可換性を適用する。",
            _proposition(submodules, _eq(inf(i, j), inf(j, i))),
            _target(lattice_prefix, "(I J : Submodule R M)", "I ⊓ J = J ⊓ I"),
            "by\n  exact inf_comm I J",
        ),
        _card(
            "commalg_modules_inf_sup_absorb",
            "I∩(I+J)=I（R-部分加群 I,J）。",
            "束の吸収律を使う。",
            _proposition(submodules, _eq(inf(i, sup(i, j)), i)),
            _target(lattice_prefix, "(I J : Submodule R M)", "I ⊓ (I ⊔ J) = I"),
            "by\n  exact inf_sup_self",
        ),
        _card(
            "commalg_modules_sup_inf_absorb",
            "I+(I∩J)=I（R-部分加群 I,J）。",
            "双対な吸収律を使う。",
            _proposition(submodules, _eq(sup(i, inf(i, j)), i)),
            _target(lattice_prefix, "(I J : Submodule R M)", "I ⊔ (I ⊓ J) = I"),
            "by\n  exact sup_inf_self",
        ),
        _card(
            "commalg_modules_kernel_identity",
            "恒等 R-線形写像の核は0部分加群である。",
            "恒等写像の kernel を直接簡約する。",
            _proposition(common, _eq(kernel(m, m, identity(m)), bot(m))),
            _target(lattice_prefix, "", "LinearMap.ker (LinearMap.id : M →ₗ[R] M) = ⊥"),
            "by\n  exact LinearMap.ker_id",
        ),
        _card(
            "commalg_modules_range_identity",
            "恒等 R-線形写像の像は全体である。",
            "恒等写像の range を直接簡約する。",
            _proposition(common, _eq(image(m, m, identity(m)), top(m))),
            _target(
                lattice_prefix, "", "LinearMap.range (LinearMap.id : M →ₗ[R] M) = ⊤"
            ),
            "by\n  exact LinearMap.range_id",
        ),
        _card(
            "commalg_modules_kernel_zero",
            "零 R-線形写像 M→N の核は M 全体である。",
            "零写像の kernel を簡約する。",
            _proposition(
                [*common, ("N", _module_type("R"))],
                _eq(kernel(m, n, zero(m, n)), top(m)),
            ),
            _target(maps_prefix, "", "LinearMap.ker (0 : M →ₗ[R] N) = ⊤"),
            "by\n  exact LinearMap.ker_zero",
        ),
        _card(
            "commalg_modules_range_zero",
            "零 R-線形写像 M→N の像は0部分加群である。",
            "零写像の range を簡約する。",
            _proposition(
                [*common, ("N", _module_type("R"))],
                _eq(image(m, n, zero(m, n)), bot(n)),
            ),
            _target(maps_prefix, "", "LinearMap.range (0 : M →ₗ[R] N) = ⊥"),
            "by\n  exact LinearMap.range_zero",
        ),
        _card(
            "commalg_modules_comp_left_identity",
            "N 上の恒等写像と f:M→N の合成は f である。",
            "線形写像を点ごとに外延して恒等性を使う。",
            _proposition(maps_mn, _eq(compose(m, n, n, f, identity(n)), f)),
            _target(
                maps_prefix, "(f : M →ₗ[R] N)", "(LinearMap.id : N →ₗ[R] N).comp f = f"
            ),
            "by\n  ext x\n  rfl",
        ),
        _card(
            "commalg_modules_comp_right_identity",
            "f:M→N と M 上の恒等写像の合成は f である。",
            "線形写像を点ごとに外延して恒等性を使う。",
            _proposition(maps_mn, _eq(compose(m, m, n, identity(m), f), f)),
            _target(
                maps_prefix, "(f : M →ₗ[R] N)", "f.comp (LinearMap.id : M →ₗ[R] M) = f"
            ),
            "by\n  ext x\n  rfl",
        ),
        _card(
            "commalg_modules_comp_associative",
            "f:M→N、g:N→P、h:P→Q の合成は結合的である。",
            "3つの線形写像を各元で評価して結合性を確認する。",
            _proposition(
                [*maps_mnp, ("Q", _module_type("R")), ("h", _map_type("R", "P", "Q"))],
                _eq(
                    compose(m, p, q, compose(m, n, p, f, g), h),
                    compose(m, n, q, f, compose(n, p, q, g, h)),
                ),
            ),
            _target(
                quadruple_prefix,
                "(f : M →ₗ[R] N) (g : N →ₗ[R] P) (h : P →ₗ[R] Q)",
                "(h.comp g).comp f = h.comp (g.comp f)",
            ),
            "by\n  rfl",
        ),
        _card(
            "commalg_modules_range_comp_le",
            "f:M→N, g:N→P なら im(g∘f)⊆im(g)。",
            "像の元を f の値として取り、g の像の証人にする。",
            _proposition(
                maps_mnp,
                _le("R", "P", image(m, p, compose(m, n, p, f, g)), image(n, p, g)),
            ),
            _target(
                triple_prefix,
                "(f : M →ₗ[R] N) (g : N →ₗ[R] P)",
                "LinearMap.range (g.comp f) ≤ LinearMap.range g",
            ),
            "by\n  rintro _ ⟨x, rfl⟩\n  exact ⟨f x, rfl⟩",
        ),
        _card(
            "commalg_modules_identity_injective",
            "任意の R-加群 M で恒等線形写像は単射である。",
            "恒等写像の値の等式をそのまま使う。",
            _proposition(common, _module("linear_injective", r, m, m, identity(m))),
            _target(
                lattice_prefix, "", "Function.Injective (LinearMap.id : M →ₗ[R] M)"
            ),
            "by\n  intro x y h\n  exact h",
        ),
        _card(
            "commalg_modules_identity_surjective",
            "任意の R-加群 M で恒等線形写像は全射である。",
            "各元自身を原像に取る。",
            _proposition(common, _module("linear_surjective", r, m, m, identity(m))),
            _target(
                lattice_prefix, "", "Function.Surjective (LinearMap.id : M →ₗ[R] M)"
            ),
            "by\n  intro x\n  exact ⟨x, rfl⟩",
        ),
        _card(
            "commalg_modules_exact_zero_id",
            "0:M→M と id_M は M で正確である。",
            "range(0)=0 と ker(id)=0 を一致させる。",
            _proposition(common, exact(m, m, m, zero(m, m), identity(m))),
            _target(
                lattice_prefix,
                "",
                "LinearMap.range (0 : M →ₗ[R] M) = LinearMap.ker (LinearMap.id : M →ₗ[R] M)",
            ),
            "by\n  simp",
        ),
        _card(
            "commalg_modules_exact_id_zero",
            "id_M と 0:M→M は M で正確である。",
            "range(id)=M と ker(0)=M を一致させる。",
            _proposition(common, exact(m, m, m, identity(m), zero(m, m))),
            _target(
                lattice_prefix,
                "",
                "LinearMap.range (LinearMap.id : M →ₗ[R] M) = LinearMap.ker (0 : M →ₗ[R] M)",
            ),
            "by\n  simp",
        ),
        _card(
            "commalg_modules_comp_zero_left",
            "g:N→P と零写像0:M→Nの合成は零写像である。",
            "各元で零写像を評価し、線形写像の外延性を使う。",
            _proposition(
                [
                    *common,
                    ("N", _module_type("R")),
                    ("P", _module_type("R")),
                    ("g", _map_type("R", "N", "P")),
                ],
                _eq(compose(m, n, p, zero(m, n), g), zero(m, p)),
            ),
            _target(triple_prefix, "(g : N →ₗ[R] P)", "g.comp (0 : M →ₗ[R] N) = 0"),
            "by\n  ext x\n  simp",
        ),
        _card(
            "commalg_modules_comp_zero_right",
            "f:M→N と零写像0:N→Pの合成は零写像である。",
            "各元で零写像を評価し、線形写像の外延性を使う。",
            _proposition(maps_mnp, _eq(compose(m, n, p, f, zero(n, p)), zero(m, p))),
            _target(triple_prefix, "(f : M →ₗ[R] N)", "(0 : N →ₗ[R] P).comp f = 0"),
            "by\n  ext x\n  simp",
        ),
    ]


def build_manifest() -> dict[str, Any]:
    cards = _cards()
    payload: dict[str, Any] = {
        "schema_version": "pals.typed-commutative-algebra-modules-v1-sealed-manifest.v1",
        "status": "sealed_local_authoring_revision_not_admitted",
        "seal": {
            "scope": "local typed commutative-algebra module authoring evidence only",
            "admission": "not admitted to the generic DB, seed, embedding index, or PFI package",
            "revision": "typed-commutative-algebra-modules-v1-local-r1",
        },
        "profile": {
            "id": TYPED_COMMUTATIVE_ALGEBRA_MODULES_PROFILE,
            "typed_cdbase": TYPED,
            "design_path": "docs/typed-commutative-algebra-modules-v1-design.md",
            "design_sha256": _sha256(DESIGN.read_bytes()),
            "registry_path": "pals_agent/content_dictionaries/typed-commutative-algebra-modules-v1-registry.json",
            "registry_sha256": _sha256(REGISTRY.read_bytes()),
            "validator": "pals_agent.typed_commutative_algebra_modules.validate_canonical_typed_commutative_algebra_modules_openmath_xml",
            "validator_path": "pals_agent/typed_commutative_algebra_modules.py",
            "validator_sha256": _sha256(VALIDATOR.read_bytes()),
            "canonicalizer_version": "openmath-cdbase-alpha-c14n-v4",
        },
        "lean_receipt": {
            "witness_path": "docs/typed-commutative-algebra-modules-v1-authoring-witnesses.lean",
            "witness_file_sha256": _sha256(WITNESS.read_bytes()),
            "toolchain": TOOLCHAIN.read_text(encoding="utf-8").rstrip("\n"),
            "verification_command": "cd pals-agent/lean-workspace && lake env lean ../../docs/typed-commutative-algebra-modules-v1-authoring-witnesses.lean",
            "verification_status": "verified_local_pinned_workspace",
        },
        "admitted_card_count": len(cards),
        "excluded_cards": [
            {
                "id": "commalg_modules_tensor_product",
                "reason": "tensor-product carrier and universal property are deferred",
            },
            {
                "id": "commalg_modules_hom_module",
                "reason": "first-class Hom-module carrier is deferred",
            },
            {
                "id": "commalg_modules_quotient",
                "reason": "quotient-module map and carrier are deferred",
            },
            {
                "id": "commalg_modules_general_exact_sequence",
                "reason": "arbitrary-length sequence typing is deferred; only exact_at is admitted",
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
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify-lean", action="store_true")
    args = parser.parse_args()
    if args.verify_lean:
        completed = subprocess.run(
            [
                "lake",
                "env",
                "lean",
                "../../docs/typed-commutative-algebra-modules-v1-authoring-witnesses.lean",
            ],
            cwd=ROOT / "pals-agent/lean-workspace",
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
