"""Seal the local, non-published multivariable-calculus authoring manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pals-agent"))

from pals_agent.typed_multivariable_calculus import (
    canonicalize_typed_multivariable_calculus_openmath_xml,
    validate_canonical_typed_multivariable_calculus_openmath_xml,
)

OPENMATH = "http://www.openmath.org/OpenMath"
TYPED_CDBASE = "urn:pals:openmath:typed-multivariable-calculus:v1"
DESIGN = ROOT / "docs" / "typed-multivariable-calculus-v1-design.md"
WITNESS = ROOT / "docs" / "typed-multivariable-calculus-v1-authoring-witnesses.lean"
REGISTRY = (
    ROOT
    / "pals-agent"
    / "pals_agent"
    / "content_dictionaries"
    / "typed-multivariable-calculus-v1-registry.json"
)
TOOLCHAIN = ROOT / "pals-agent" / "lean-workspace" / "lean-toolchain"


@dataclass(frozen=True)
class Card:
    id: str
    canonical_statement: str
    proof_strategy: str
    sketch_steps: tuple[str, ...]
    openmath_xml: str
    signature_trace: tuple[str, ...]
    lean_target: str
    lean_witness: str
    alignment: str


def sha256(value: str | bytes) -> str:
    data = value if isinstance(value, bytes) else value.encode("utf-8")
    return "sha256:" + hashlib.sha256(data).hexdigest()


def tag(name: str, body: str) -> str:
    return f"<{name}>{body}</{name}>"


def oms(cd: str, name: str, *, typed: bool = False) -> str:
    cdbase = f' cdbase="{TYPED_CDBASE}"' if typed else ""
    return f'<OMS{cdbase} cd="{cd}" name="{name}"/>'


def omv(name: str) -> str:
    return f'<OMV name="{name}"/>'


def app(operator: str, *arguments: str) -> str:
    return tag("OMA", operator + "".join(arguments))


def typed(name: str) -> str:
    return oms("typed1", name, typed=True)


def mc(name: str) -> str:
    return oms("multicalc1", name, typed=True)


def std(cd: str, name: str, *arguments: str) -> str:
    return app(oms(cd, name), *arguments)


def declaration(name: str, sort: str) -> str:
    return tag("OMATTR", tag("OMATP", typed("type") + sort) + omv(name))


def forall(declarations: tuple[tuple[str, str], ...], body: str) -> str:
    return tag(
        "OMBIND",
        typed("forall")
        + tag("OMBVAR", "".join(declaration(name, sort) for name, sort in declarations))
        + body,
    )


def lambda2(name: str, body: str) -> str:
    return tag(
        "OMBIND",
        mc("lambda2") + tag("OMBVAR", declaration(name, mc("Real2"))) + body,
    )


def of_int(value: int) -> str:
    return app(mc("of_int"), f"<OMI>{value}</OMI>")


def pair(left: str, right: str) -> str:
    return app(mc("pair"), left, right)


def fst(point: str) -> str:
    return app(mc("fst"), point)


def snd(point: str) -> str:
    return app(mc("snd"), point)


def power(base: str, exponent: int) -> str:
    return std("arith1", "power", base, f"<OMI>{exponent}</OMI>")


def plus(left: str, right: str) -> str:
    return std("arith1", "plus", left, right)


def times(left: str, right: str) -> str:
    return std("arith1", "times", left, right)


def proposition(name: str, *arguments: str) -> str:
    return app(mc(name), *arguments)


def openmath(body: str) -> str:
    return f'<OMOBJ xmlns="{OPENMATH}" version="2.0">{body}</OMOBJ>'


def quadratic() -> str:
    point = omv("p")
    return lambda2("p", plus(power(fst(point), 2), power(snd(point), 2)))


def product() -> str:
    point = omv("p")
    return lambda2("p", times(fst(point), snd(point)))


def partial_x_quadratic_xml() -> str:
    a, b = omv("a"), omv("b")
    return openmath(
        forall(
            (("a", typed("Real")), ("b", typed("Real"))),
            proposition("partial_x_at", quadratic(), pair(a, b), times(of_int(2), a)),
        )
    )


def partial_y_quadratic_xml() -> str:
    a, b = omv("a"), omv("b")
    return openmath(
        forall(
            (("a", typed("Real")), ("b", typed("Real"))),
            proposition("partial_y_at", quadratic(), pair(a, b), times(of_int(2), b)),
        )
    )


def partial_x_product_xml() -> str:
    a, b = omv("a"), omv("b")
    return openmath(
        forall(
            (("a", typed("Real")), ("b", typed("Real"))),
            proposition("partial_x_at", product(), pair(a, b), b),
        )
    )


def partial_y_product_xml() -> str:
    a, b = omv("a"), omv("b")
    return openmath(
        forall(
            (("a", typed("Real")), ("b", typed("Real"))),
            proposition("partial_y_at", product(), pair(a, b), a),
        )
    )


def differentiable_quadratic_xml() -> str:
    point = omv("point")
    return openmath(
        forall(
            (("point", mc("Real2")),),
            proposition("differentiable_at", quadratic(), point),
        )
    )


def differentiable_product_xml() -> str:
    point = omv("point")
    return openmath(
        forall(
            (("point", mc("Real2")),),
            proposition("differentiable_at", product(), point),
        )
    )


def cards() -> tuple[Card, ...]:
    return (
        Card(
            "multivar_partial_x_quadratic",
            "For f(x,y)=x²+y², the first coordinate partial derivative at (a,b) is 2a.",
            "Freeze the second coordinate and apply the one-variable square rule.",
            (
                "setup: Fix the point (a,b).",
                "restrict: Hold y=b and view f(x,b) as x²+b².",
                "differentiate: Apply the square rule to x².",
                "constant: The b² term has derivative zero.",
                "conclude: The x-partial slope is 2a.",
            ),
            partial_x_quadratic_xml(),
            ("Real2Function", "partial_x_at: Real2Function × Real2 × Real → Prop"),
            "∀ a b : ℝ, HasPartialXAt (fun p : ℝ × ℝ => p.1 ^ 2 + p.2 ^ 2) (2 * a) (a, b)",
            "example (a b : ℝ) :\n    HasPartialXAt (fun p : ℝ × ℝ => p.1 ^ 2 + p.2 ^ 2) (2 * a) (a, b) := by\n  simpa [HasPartialXAt, pow_two] using (hasDerivAt_pow 2 a).add_const (b ^ 2)",
            "partial_x_at lowers to HasDerivAt (fun x => f (x,b)) at a; the XML lambda is exactly x²+y².",
        ),
        Card(
            "multivar_partial_y_quadratic",
            "For f(x,y)=x²+y², the second coordinate partial derivative at (a,b) is 2b.",
            "Freeze the first coordinate and apply the one-variable square rule.",
            (
                "setup: Fix the point (a,b).",
                "restrict: Hold x=a and view f(a,y) as a²+y².",
                "differentiate: Apply the square rule to y².",
                "constant: The a² term has derivative zero.",
                "conclude: The y-partial slope is 2b.",
            ),
            partial_y_quadratic_xml(),
            ("Real2Function", "partial_y_at: Real2Function × Real2 × Real → Prop"),
            "∀ a b : ℝ, HasPartialYAt (fun p : ℝ × ℝ => p.1 ^ 2 + p.2 ^ 2) (2 * b) (a, b)",
            "example (a b : ℝ) :\n    HasPartialYAt (fun p : ℝ × ℝ => p.1 ^ 2 + p.2 ^ 2) (2 * b) (a, b) := by\n  simpa [HasPartialYAt, pow_two] using (hasDerivAt_pow 2 b).const_add (a ^ 2)",
            "partial_y_at lowers to HasDerivAt (fun y => f (a,y)) at b; the XML lambda is exactly x²+y².",
        ),
        Card(
            "multivar_partial_x_product",
            "For f(x,y)=xy, the first coordinate partial derivative at (a,b) is b.",
            "Freeze y=b and differentiate the linear function x ↦ xb.",
            (
                "setup: Fix the point (a,b).",
                "restrict: Hold y=b to obtain x ↦ xb.",
                "linear: Use the derivative of the identity function.",
                "scale: Multiply its slope by the constant b.",
                "conclude: The x-partial slope is b.",
            ),
            partial_x_product_xml(),
            ("Real2Function", "partial_x_at: Real2Function × Real2 × Real → Prop"),
            "∀ a b : ℝ, HasPartialXAt (fun p : ℝ × ℝ => p.1 * p.2) b (a, b)",
            "example (a b : ℝ) :\n    HasPartialXAt (fun p : ℝ × ℝ => p.1 * p.2) b (a, b) := by\n  simpa [HasPartialXAt] using (hasDerivAt_id a).mul_const b",
            "The coordinate restriction preserves the product order x*b, and Lean witnesses its slope b.",
        ),
        Card(
            "multivar_partial_y_product",
            "For f(x,y)=xy, the second coordinate partial derivative at (a,b) is a.",
            "Freeze x=a and differentiate the linear function y ↦ ay.",
            (
                "setup: Fix the point (a,b).",
                "restrict: Hold x=a to obtain y ↦ ay.",
                "linear: Use the derivative of the identity function.",
                "scale: Multiply its slope by the constant a.",
                "conclude: The y-partial slope is a.",
            ),
            partial_y_product_xml(),
            ("Real2Function", "partial_y_at: Real2Function × Real2 × Real → Prop"),
            "∀ a b : ℝ, HasPartialYAt (fun p : ℝ × ℝ => p.1 * p.2) a (a, b)",
            "example (a b : ℝ) :\n    HasPartialYAt (fun p : ℝ × ℝ => p.1 * p.2) a (a, b) := by\n  simpa [HasPartialYAt] using (hasDerivAt_id b).const_mul a",
            "The coordinate restriction is y ↦ a*y, represented by Lean's constant-left multiplication derivative rule.",
        ),
        Card(
            "multivar_differentiable_quadratic",
            "The bivariate quadratic (x,y) ↦ x²+y² is differentiable at every point of ℝ².",
            "Use closure of differentiable functions under coordinate projections, powers, and addition.",
            (
                "setup: Fix an arbitrary point p in ℝ².",
                "coordinates: Both coordinate projections are differentiable.",
                "powers: Square each projection.",
                "sum: Add the two differentiable terms.",
                "conclude: The quadratic is differentiable at p.",
            ),
            differentiable_quadratic_xml(),
            ("Real2Function", "differentiable_at: Real2Function × Real2 → Prop"),
            "∀ p : ℝ × ℝ, DifferentiableAt ℝ (fun q : ℝ × ℝ => q.1 ^ 2 + q.2 ^ 2) p",
            "example (p : ℝ × ℝ) : DifferentiableAt ℝ (fun q : ℝ × ℝ => q.1 ^ 2 + q.2 ^ 2) p := by\n  fun_prop",
            "differentiable_at lowers directly to Mathlib DifferentiableAt over ℝ for the same product-space lambda.",
        ),
        Card(
            "multivar_differentiable_product",
            "The bivariate product (x,y) ↦ xy is differentiable at every point of ℝ².",
            "Use closure of differentiable functions under coordinate projections and multiplication.",
            (
                "setup: Fix an arbitrary point p in ℝ².",
                "coordinates: Both coordinate projections are differentiable.",
                "product: Multiply the two differentiable scalar functions.",
                "locality: The construction applies at the chosen p.",
                "conclude: The product is differentiable at p.",
            ),
            differentiable_product_xml(),
            ("Real2Function", "differentiable_at: Real2Function × Real2 → Prop"),
            "∀ p : ℝ × ℝ, DifferentiableAt ℝ (fun q : ℝ × ℝ => q.1 * q.2) p",
            "example (p : ℝ × ℝ) : DifferentiableAt ℝ (fun q : ℝ × ℝ => q.1 * q.2) p := by\n  fun_prop",
            "differentiable_at lowers directly to Mathlib DifferentiableAt over ℝ for the same product-space lambda.",
        ),
    )


def build_manifest() -> dict[str, object]:
    witness = WITNESS.read_text(encoding="utf-8")
    cards_payload: list[dict[str, object]] = []
    for card in cards():
        canonical = canonicalize_typed_multivariable_calculus_openmath_xml(card.openmath_xml)
        validate_canonical_typed_multivariable_calculus_openmath_xml(canonical)
        if f"-- manifest card: {card.id}\n{card.lean_witness}" not in witness:
            raise ValueError(f"Lean witness bundle lacks exact witness for `{card.id}`.")
        cards_payload.append(
            {
                **asdict(card),
                "sketch_steps": list(card.sketch_steps),
                "signature_trace": list(card.signature_trace),
                "openmath_xml_sha256": sha256(card.openmath_xml),
                "canonical_openmath_xml": canonical,
                "canonical_openmath_xml_sha256": sha256(canonical),
                "canonical_statement_sha256": sha256(card.canonical_statement),
                "lean_target_sha256": sha256(card.lean_target),
                "lean_witness_sha256": sha256(card.lean_witness),
                "source_witness_sha256": sha256(card.lean_witness),
                "profile_validation_status": "validated_local_typed_multivariable_calculus_v1_sealed",
                "statement_openmath_lean_alignment_review": {
                    "status": "reviewed_by_local_authoring_agent_not_admitted",
                    "statement_to_openmath": "The natural-language statement is represented only by the listed profile-local typed signature.",
                    "openmath_to_lean": card.alignment,
                    "admission_gate": "Canonical XML, direct Lean witness, and manifest digest are required; this remains non-published.",
                },
            }
        )
    toolchain = TOOLCHAIN.read_text(encoding="utf-8")
    payload: dict[str, object] = {
        "schema_version": "pals.typed-multivariable-calculus-v1-sealed-manifest.v1",
        "status": "sealed_local_authoring_revision_not_admitted",
        "seal": {
            "scope": "local typed multivariable-calculus authoring evidence only",
            "admission": "not admitted to the generic DB, seed, embedding index, or PFI package",
            "revision": "typed-multivariable-calculus-v1-local-r1",
        },
        "profile": {
            "id": "typed-multivariable-calculus-v1",
            "validator": "pals_agent.typed_multivariable_calculus.validate_canonical_typed_multivariable_calculus_openmath_xml",
            "canonicalizer": "openmath-cdbase-alpha-c14n-v4",
            "profile_design_path": "docs/typed-multivariable-calculus-v1-design.md",
            "profile_design_sha256": sha256(DESIGN.read_bytes()),
            "registry_path": "pals_agent/content_dictionaries/typed-multivariable-calculus-v1-registry.json",
            "registry_digest": sha256(REGISTRY.read_bytes()),
            "lean_toolchain": {
                "path": "pals-agent/lean-workspace/lean-toolchain",
                "value": toolchain.rstrip("\n"),
                "sha256": sha256(toolchain.encode("utf-8")),
                "digest_input": "exact UTF-8 bytes of the named lean-toolchain file",
            },
        },
        "lean_receipt": {
            "witness_path": "docs/typed-multivariable-calculus-v1-authoring-witnesses.lean",
            "witness_file_sha256": sha256(witness),
            "verification_command": "cd pals-agent/lean-workspace && lake env lean ../../docs/typed-multivariable-calculus-v1-authoring-witnesses.lean",
            "verification_status": "verified_local_pinned_workspace",
            "scope": "manual statement-to-OpenMath-to-Lean alignment; no automatic translator claim",
        },
        "hard_rejects": [
            "gradient", "hessian", "local_extremum", "partial_xy_at", "double_integral", "iterated_integral", "fubini", "change_of_variables"
        ],
        "cards": cards_payload,
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    payload["manifest_payload_sha256"] = sha256(serialized)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(
        json.dumps(build_manifest(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
