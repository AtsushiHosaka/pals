"""Seal local authoring evidence for the isolated ``typed-ode-v1`` profile."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import rfc8785

ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = ROOT / "pals-agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from pals_agent.typed_ode import (
    TYPED_ODE_OPENMATH_CDBASE,
    TYPED_ODE_PROFILE,
    canonicalize_typed_ode_openmath_xml,
)

SOURCE = ROOT / "docs" / "probability-ode-draft-candidates.json"
DESIGN = ROOT / "docs" / "typed-ode-v1-design.md"
WITNESS = ROOT / "docs" / "typed-ode-v1-authoring-witnesses.lean"
REGISTRY = AGENT_ROOT / "pals_agent" / "content_dictionaries" / "typed-ode-v1-registry.json"
TOOLCHAIN = AGENT_ROOT / "lean-workspace" / "lean-toolchain"
SCHEMA = "pals.typed-ode-v1-sealed-manifest.v1"
STATUS = "sealed_local_authoring_revision_not_admitted"


def _sha(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _typed(cd: str, name: str) -> str:
    return f'<OMS cdbase="{TYPED_ODE_OPENMATH_CDBASE}" cd="{cd}" name="{name}"/>'


def _standard(cd: str, name: str) -> str:
    return f'<OMS cd="{cd}" name="{name}"/>'


def _app(head: str, *arguments: str) -> str:
    return f"<OMA>{head}{''.join(arguments)}</OMA>"


def _ode(name: str, *arguments: str) -> str:
    return _app(_typed("ode1", name), *arguments)


def _arith(name: str, *arguments: str) -> str:
    return _app(_standard("arith1", name), *arguments)


def _trans(name: str, argument: str) -> str:
    return _app(_standard("transc1", name), argument)


def _real(integer: int) -> str:
    return _ode("of_int", f"<OMI>{integer}</OMI>")


def _decl(name: str) -> str:
    return (
        f"<OMATTR><OMATP>{_typed('typed1', 'type')}{_typed('typed1', 'Real')}</OMATP>"
        f'<OMV name="{name}"/></OMATTR>'
    )


def _forall(names: tuple[str, ...], body: str) -> str:
    return (
        f"<OMBIND>{_typed('typed1', 'forall')}<OMBVAR>"
        f"{''.join(_decl(name) for name in names)}</OMBVAR>{body}</OMBIND>"
    )


def _function(body: str, *, name: str = "t") -> str:
    return (
        f"<OMBIND>{_typed('ode1', 'lambda')}<OMBVAR>{_decl(name)}</OMBVAR>"
        f"{body}</OMBIND>"
    )


def _eq(left: str, right: str) -> str:
    return _app(_standard("relation1", "eq"), left, right)


def _certificate(
    parameters: tuple[str, ...], function: str, initial_value: str, equality: str
) -> str:
    initial = _ode("initial_value", function, _real(0), initial_value)
    all_real = _forall(("x",), equality)
    body = _app(_standard("logic1", "and"), initial, all_real)
    if parameters:
        body = _forall(parameters, body)
    return f'<OMOBJ xmlns="http://www.openmath.org/OpenMath" version="2.0">{body}</OMOBJ>'


@dataclass(frozen=True, slots=True)
class _Card:
    card_id: str
    topic: str
    difficulty: str
    statement: str
    strategy: str
    steps: tuple[str, ...]
    parameters: tuple[str, ...]
    function: str
    initial_value: str
    equality: str
    lean_target: str
    lean_witness: str


def _cards() -> tuple[_Card, ...]:
    growth = _function(_arith("times", '<OMV name="C"/>', _trans("exp", _arith("times", '<OMV name="k"/>', '<OMV name="t"/>'))))
    decay = _function(_arith("times", '<OMV name="C"/>', _trans("exp", _arith("times", _arith("unary_minus", '<OMV name="k"/>'), '<OMV name="t"/>'))))
    zero = _function(_real(0))
    homogeneous = _function(_arith("times", '<OMV name="C"/>', _trans("exp", _arith("unary_minus", '<OMV name="t"/>'))))
    affine = _function(_arith("minus", '<OMV name="t"/>', _real(1)))
    polynomial = _function(_arith("times", _real(2), '<OMV name="t"/>'))
    sine = _function(_trans("sin", '<OMV name="t"/>'))
    cosine = _function(_trans("cos", '<OMV name="t"/>'))
    exponential = _function(_trans("exp", '<OMV name="t"/>'))
    identity = _function('<OMV name="t"/>')
    x = '<OMV name="x"/>'

    return (
        _Card(
            "ode_separable_exponential_growth", "separable_equations", "standard",
            "For real C and k, f(t)=C exp(k t) has f(0)=C and satisfies f'(x)=k f(x) for every real x.",
            "Differentiate the explicit exponential solution and check its initial value at zero.",
            ("Name the proposed real function.", "Evaluate it at zero.", "Differentiate the exponential composition.", "Factor the derivative as k times the function value.", "Conclude the all-real ODE certificate."),
            ("C", "k"), growth, '<OMV name="C"/>',
            _eq(_ode("deriv_at", growth, x), _arith("times", '<OMV name="k"/>', _ode("apply", growth, x))),
            "((fun t : ℝ => C * Real.exp (k * t)) 0 = C) ∧ ∀ x : ℝ, deriv (fun t : ℝ => C * Real.exp (k * t)) x = k * (C * Real.exp (k * x))",
            "by\n  constructor\n  · simp\n  · intro x\n    have hd := ((Real.hasDerivAt_exp (k * x)).comp x (hasDerivAt_const_mul k)).const_mul C\n    calc\n      deriv (fun t : ℝ => C * Real.exp (k * t)) x = C * (Real.exp (k * x) * k) := by\n        simpa [Function.comp_apply] using hd.deriv\n      _ = k * (C * Real.exp (k * x)) := by ring",
        ),
        _Card(
            "ode_separable_exponential_decay", "separable_equations", "standard",
            "For real C and k, f(t)=C exp(-k t) has f(0)=C and satisfies f'(x)=-k f(x) for every real x.",
            "Differentiate the decaying exponential and retain the negative rate factor.",
            ("Name the proposed real function.", "Evaluate it at zero.", "Differentiate the affine exponent.", "Apply the chain rule to the exponential.", "Rewrite the result as -k times the function value."),
            ("C", "k"), decay, '<OMV name="C"/>',
            _eq(_ode("deriv_at", decay, x), _arith("times", _arith("unary_minus", '<OMV name="k"/>'), _ode("apply", decay, x))),
            "((fun t : ℝ => C * Real.exp (-k * t)) 0 = C) ∧ ∀ x : ℝ, deriv (fun t : ℝ => C * Real.exp (-k * t)) x = -k * (C * Real.exp (-k * x))",
            "by\n  constructor\n  · simp\n  · intro x\n    have hd := ((Real.hasDerivAt_exp (-k * x)).comp x (hasDerivAt_const_mul (-k))).const_mul C\n    calc\n      deriv (fun t : ℝ => C * Real.exp (-k * t)) x = C * (Real.exp (-k * x) * (-k)) := by\n        simpa [Function.comp_apply] using hd.deriv\n      _ = -k * (C * Real.exp (-k * x)) := by ring",
        ),
        _Card(
            "ode_separable_zero_solution", "separable_equations", "introductory",
            "The zero function has f(0)=0 and satisfies f'(x)=f(x)^2 for every real x.",
            "Check the zero initial value and simplify both sides of the separable equation.",
            ("Name the constant zero function.", "Evaluate it at the initial time zero.", "Differentiate the constant function.", "Square the function value.", "Compare the two zero expressions for every real x."),
            (), zero, _real(0),
            _eq(_ode("deriv_at", zero, x), _arith("power", _ode("apply", zero, x), "<OMI>2</OMI>")),
            "((fun _ : ℝ => (0 : ℝ)) 0 = 0) ∧ ∀ x : ℝ, deriv (fun _ : ℝ => (0 : ℝ)) x = (0 : ℝ) ^ 2",
            "by\n  constructor\n  · simp\n  · intro x\n    simp",
        ),
        _Card(
            "ode_first_linear_homogeneous_unit", "first_order_linear", "standard",
            "For real C, f(t)=C exp(-t) has f(0)=C and satisfies f'(x)+f(x)=0 for every real x.",
            "Use the derivative of exp(-t) to cancel the homogeneous linear operator.",
            ("Name the proposed homogeneous solution.", "Evaluate it at zero.", "Differentiate the negative exponent.", "Substitute f and f' into f'+f.", "Cancel the two terms."),
            ("C",), homogeneous, '<OMV name="C"/>',
            _eq(_arith("plus", _ode("deriv_at", homogeneous, x), _ode("apply", homogeneous, x)), _real(0)),
            "((fun t : ℝ => C * Real.exp (-t)) 0 = C) ∧ ∀ x : ℝ, deriv (fun t : ℝ => C * Real.exp (-t)) x + C * Real.exp (-x) = 0",
            "by\n  constructor\n  · simp\n  · intro x\n    have hd := ((Real.hasDerivAt_exp (-x)).comp x (hasDerivAt_neg x)).const_mul C\n    rw [show deriv (fun t : ℝ => C * Real.exp (-t)) x = C * (Real.exp (-x) * (-1)) by simpa [Function.comp_apply] using hd.deriv]\n    ring",
        ),
        _Card(
            "ode_first_linear_affine_particular", "first_order_linear", "standard",
            "The function f(t)=t-1 has f(0)=-1 and satisfies f'(x)+f(x)=x for every real x.",
            "Differentiate the affine particular solution and simplify the linear operator.",
            ("Name the affine function.", "Evaluate it at zero.", "Differentiate the identity minus a constant.", "Substitute into f'+f.", "Simplify to x."),
            (), affine, _real(-1),
            _eq(_arith("plus", _ode("deriv_at", affine, x), _ode("apply", affine, x)), x),
            "((fun t : ℝ => t - 1) 0 = -1) ∧ ∀ x : ℝ, deriv (fun t : ℝ => t - 1) x + (x - 1) = x",
            "by\n  constructor\n  · norm_num\n  · intro x\n    have hd : HasDerivAt (fun t : ℝ => t - 1) 1 x := (hasDerivAt_id x).sub_const 1\n    rw [hd.deriv]\n    ring",
        ),
        _Card(
            "ode_first_linear_polynomial_forcing", "first_order_linear", "standard",
            "The function f(t)=2t has f(0)=0 and satisfies f'(x)+2x=2x+2 for every real x.",
            "Differentiate the linear polynomial and simplify the forcing equation.",
            ("Name the polynomial particular solution.", "Evaluate it at zero.", "Differentiate 2t.", "Substitute the derivative.", "Collect the two constant terms."),
            (), polynomial, _real(0),
            _eq(_arith("plus", _ode("deriv_at", polynomial, x), _arith("times", _real(2), x)), _arith("plus", _arith("times", _real(2), x), _real(2))),
            "((fun t : ℝ => 2 * t) 0 = 0) ∧ ∀ x : ℝ, deriv (fun t : ℝ => 2 * t) x + 2 * x = 2 * x + 2",
            "by\n  constructor\n  · norm_num\n  · intro x\n    have hd : HasDerivAt (fun t : ℝ => 2 * t) 2 x := by\n      simpa using (hasDerivAt_id x).const_mul 2\n    rw [hd.deriv]\n    ring",
        ),
        _Card(
            "ode_second_harmonic_sine", "second_order_constant_coefficient", "standard",
            "The function f(t)=sin t has f(0)=0 and satisfies f''(x)+f(x)=0 for every real x.",
            "Differentiate sine twice and use the harmonic-oscillator cancellation.",
            ("Name the sine function.", "Evaluate it at zero.", "Differentiate once to cosine.", "Differentiate again to negative sine.", "Substitute into f''+f and cancel."),
            (), sine, _real(0),
            _eq(_arith("plus", _ode("second_deriv_at", sine, x), _ode("apply", sine, x)), _real(0)),
            "((fun t : ℝ => Real.sin t) 0 = 0) ∧ ∀ x : ℝ, deriv (fun t : ℝ => deriv (fun s : ℝ => Real.sin s) t) x + Real.sin x = 0",
            "by\n  constructor\n  · simp\n  · intro x\n    rw [show (fun t : ℝ => deriv (fun s : ℝ => Real.sin s) t) = Real.cos by\n      ext t\n      exact (Real.hasDerivAt_sin t).deriv]\n    rw [(Real.hasDerivAt_cos x).deriv]\n    ring",
        ),
        _Card(
            "ode_second_harmonic_cosine", "second_order_constant_coefficient", "standard",
            "The function f(t)=cos t has f(0)=1 and satisfies f''(x)+f(x)=0 for every real x.",
            "Differentiate cosine twice and cancel the harmonic terms.",
            ("Name the cosine function.", "Evaluate it at zero.", "Differentiate once to negative sine.", "Differentiate again to negative cosine.", "Substitute into f''+f and cancel."),
            (), cosine, _real(1),
            _eq(_arith("plus", _ode("second_deriv_at", cosine, x), _ode("apply", cosine, x)), _real(0)),
            "((fun t : ℝ => Real.cos t) 0 = 1) ∧ ∀ x : ℝ, deriv (fun t : ℝ => deriv (fun s : ℝ => Real.cos s) t) x + Real.cos x = 0",
            "by\n  constructor\n  · simp\n  · intro x\n    rw [show (fun t : ℝ => deriv (fun s : ℝ => Real.cos s) t) = fun t : ℝ => -Real.sin t by\n      ext t\n      exact (Real.hasDerivAt_cos t).deriv]\n    rw [show deriv (fun t : ℝ => -Real.sin t) x = -Real.cos x by\n      rw [show (fun t : ℝ => -Real.sin t) = fun t : ℝ => (-1 : ℝ) * Real.sin t by\n        ext t\n        ring]\n      rw [deriv_const_mul]\n      · rw [(Real.hasDerivAt_sin x).deriv]\n        ring\n      · fun_prop]\n    ring",
        ),
        _Card(
            "ode_second_exponential_positive_root", "second_order_constant_coefficient", "standard",
            "The function f(t)=exp t has f(0)=1 and satisfies f''(x)-f(x)=0 for every real x.",
            "Use that the exponential is unchanged by each differentiation.",
            ("Name the exponential function.", "Evaluate it at zero.", "Differentiate once.", "Differentiate the same function again.", "Subtract f from f'' and simplify."),
            (), exponential, _real(1),
            _eq(_arith("minus", _ode("second_deriv_at", exponential, x), _ode("apply", exponential, x)), _real(0)),
            "((fun t : ℝ => Real.exp t) 0 = 1) ∧ ∀ x : ℝ, deriv (fun t : ℝ => deriv (fun s : ℝ => Real.exp s) t) x - Real.exp x = 0",
            "by\n  constructor\n  · simp\n  · intro x\n    rw [show (fun t : ℝ => deriv (fun s : ℝ => Real.exp s) t) = Real.exp by\n      ext t\n      exact (Real.hasDerivAt_exp t).deriv]\n    rw [(Real.hasDerivAt_exp x).deriv]\n    ring",
        ),
        _Card(
            "ode_second_zero_characteristic_identity", "second_order_constant_coefficient", "introductory",
            "The identity function has f(0)=0 and satisfies f''(x)=0 for every real x.",
            "Differentiate the identity twice and retain the initial value at zero.",
            ("Name the identity function.", "Evaluate it at zero.", "Differentiate once to the constant one.", "Differentiate once more to zero.", "Conclude the all-real second-order equation."),
            (), identity, _real(0),
            _eq(_ode("second_deriv_at", identity, x), _real(0)),
            "((fun t : ℝ => t) 0 = 0) ∧ ∀ x : ℝ, deriv (fun t : ℝ => deriv (fun s : ℝ => s) t) x = 0",
            "by\n  constructor\n  · simp\n  · intro x\n    rw [show (fun t : ℝ => deriv (fun s : ℝ => s) t) = fun _ : ℝ => 1 by\n      ext t\n      exact (hasDerivAt_id t).deriv]\n    simp",
        ),
    )


def _source_candidates() -> dict[str, dict[str, object]]:
    payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    cards = payload.get("current_openmath_cards")
    if not isinstance(cards, list):
        raise TypeError("ODE source catalog has no current_openmath_cards list")
    result: dict[str, dict[str, object]] = {}
    for card in cards:
        if not isinstance(card, dict) or card.get("domain") != "ordinary_differential_equations":
            continue
        card_id = card.get("id")
        if not isinstance(card_id, str):
            raise TypeError("ODE source card id is invalid")
        result[card_id] = card
    return result


def _card_payload(card: _Card, source: dict[str, object]) -> dict[str, object]:
    raw = _certificate(card.parameters, card.function, card.initial_value, card.equality)
    canonical = canonicalize_typed_ode_openmath_xml(raw)
    source_statement = source.get("canonical_statement")
    if not isinstance(source_statement, str) or not source_statement:
        raise ValueError(f"source candidate `{card.card_id}` has no statement")
    return {
        "id": card.card_id,
        "source_candidate_id": card.card_id,
        "source_candidate_statement_sha256": _sha(source_statement.encode("utf-8")),
        "openmath_profile": TYPED_ODE_PROFILE,
        "domain": "ordinary_differential_equations",
        "level": "undergraduate_year_2",
        "topic": card.topic,
        "difficulty": card.difficulty,
        "canonical_statement": card.statement,
        "proof_strategy": card.strategy,
        "sketch_steps": list(card.steps),
        "openmath_xml": raw,
        "openmath_xml_sha256": _sha(raw.encode("utf-8")),
        "canonical_openmath_xml": canonical,
        "canonical_openmath_xml_sha256": _sha(canonical.encode("utf-8")),
        "lean_target": card.lean_target,
        "lean_target_sha256": _sha(card.lean_target.encode("utf-8")),
        "lean_witness": card.lean_witness,
        "lean_witness_sha256": _sha(card.lean_witness.encode("utf-8")),
        "openmath_to_lean_alignment": (
            "ode1:lambda is a Lean `fun t : ℝ => ...`; ode1:initial_value(f,0,y0) "
            "lowers to `f 0 = y0`; deriv_at and second_deriv_at lower to the displayed "
            "first and iterated Lean `deriv` expressions."
        ),
        "profile_validation_status": "validated_local_typed_ode_v1_sealed",
        "compiler_receipt_status": "verified_local_pinned_workspace",
    }


def build_manifest() -> dict[str, object]:
    source = _source_candidates()
    cards = _cards()
    if len(cards) != 10 or set(source) != {card.card_id for card in cards}:
        raise ValueError("typed-ode-v1 must bind exactly the ten existing ODE source cards")
    source_bytes = SOURCE.read_bytes()
    registry_bytes = REGISTRY.read_bytes()
    design_bytes = DESIGN.read_bytes()
    witness_bytes = WITNESS.read_bytes()
    toolchain_bytes = TOOLCHAIN.read_bytes()
    payload: dict[str, object] = {
        "schema_version": SCHEMA,
        "status": STATUS,
        "seal": {
            "scope": "local typed-ode authoring evidence only",
            "admission": "not admitted to the generic DB, seed, embedding index, or PFI package",
            "revision": "typed-ode-v1-local-r1",
        },
        "immutability_contract": {
            "digest_algorithm": "sha256",
            "canonical_json": "RFC 8785 canonical JSON serialization of this object with manifest_digest omitted",
            "profile_c14n": "Every card is validated by typed-ode-v1 and then canonicalized before sealing.",
            "mutation_rule": "Any source, design, registry, Lean witness, statement, proof strategy, sketch, XML, or Lean target/proof change creates a new sealed revision.",
        },
        "profile": {
            "id": TYPED_ODE_PROFILE,
            "typed_cdbase": TYPED_ODE_OPENMATH_CDBASE,
            "validator": "pals_agent.typed_ode.validate_canonical_typed_ode_openmath_xml",
            "validator_status": "implemented_isolated_profile",
            "registry_path": "pals_agent/content_dictionaries/typed-ode-v1-registry.json",
            "registry_sha256": _sha(registry_bytes),
            "design_path": "docs/typed-ode-v1-design.md",
            "design_sha256": _sha(design_bytes),
            "lean_toolchain": {
                "path": "pals-agent/lean-workspace/lean-toolchain",
                "value": toolchain_bytes.decode("utf-8").rstrip("\n"),
                "sha256": _sha(toolchain_bytes),
            },
        },
        "source_catalog": {
            "path": "docs/probability-ode-draft-candidates.json",
            "sha256": _sha(source_bytes),
            "selection": "all ten current_openmath_cards with domain ordinary_differential_equations",
        },
        "lean_witness_bundle": {
            "path": "docs/typed-ode-v1-authoring-witnesses.lean",
            "sha256": _sha(witness_bytes),
            "verification_command": "cd pals-agent/lean-workspace && lake env lean ../../docs/typed-ode-v1-authoring-witnesses.lean",
            "verification_status": "verified_local_pinned_workspace",
        },
        "admitted_card_count": len(cards),
        "excluded_source_card_count": 0,
        "cards": [_card_payload(card, source[card.card_id]) for card in cards],
    }
    payload["manifest_digest"] = {
        "algorithm": "sha256",
        "input": "RFC 8785 canonical JSON serialization of this object with manifest_digest omitted",
        "sha256": _sha(rfc8785.dumps(payload)),
    }
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs" / "typed-ode-v1-authoring-manifest.proposal.json",
    )
    args = parser.parse_args()
    output = args.output.resolve()
    output.write_text(json.dumps(build_manifest(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
