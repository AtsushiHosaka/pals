"""Build immutable typed-real-analysis authoring manifests.

The original four-card snapshot and the disjoint r2 expansion are generated
separately.  Neither manifest publishes a DB Draft or claims OpenMath-to-Lean
translation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pals-agent"))

from pals_agent.typed_real_analysis import (
    canonicalize_typed_real_analysis_openmath_xml,
    validate_canonical_typed_real_analysis_openmath_xml,
)

OPENMATH = "http://www.openmath.org/OpenMath"
TYPED_CDBASE = "urn:pals:openmath:typed-math:v1"
BASE_WITNESS_FILE = ROOT / "docs" / "typed-real-analysis-v1-authoring-witnesses.lean"
BASE_DESIGN_FILE = ROOT / "docs" / "typed-real-analysis-v1-design.md"
EXPANSION_WITNESS_FILE = (
    ROOT / "docs" / "typed-real-analysis-v1-expansion-r2-authoring-witnesses.lean"
)
EXPANSION_DESIGN_FILE = ROOT / "docs" / "typed-real-analysis-v1-expansion-r2-design.md"
REGISTRY_PATH = (
    ROOT
    / "pals-agent"
    / "pals_agent"
    / "content_dictionaries"
    / "typed-real-analysis-v1-registry.json"
)
_BASE_SCHEMA_VERSION = "pals.typed-real-analysis-v1-sealed-manifest.v1"
_EXPANSION_SCHEMA_VERSION = "pals.typed-real-analysis-v1-expansion-sealed-manifest.v1"
_SEALED_STATUS = "sealed_local_authoring_revision_not_admitted"


@dataclass(frozen=True)
class AdoptedCard:
    id: str
    canonical_statement: str
    proof_strategy: str
    sketch_steps: tuple[str, ...]
    openmath_xml: str
    signature_trace: tuple[str, ...]
    lean_target: str
    lean_witness: str
    source_witness_ids: tuple[str, ...]
    alignment: str


def sha256(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def tag(name: str, body: str) -> str:
    return f"<{name}>{body}</{name}>"


def oms(cd: str, name: str, *, cdbase: str | None = None) -> str:
    base = f' cdbase="{cdbase}"' if cdbase else ""
    return f'<OMS{base} cd="{cd}" name="{name}"/>'


def omv(name: str) -> str:
    return f'<OMV name="{name}"/>'


def omi(value: int) -> str:
    return f"<OMI>{value}</OMI>"


def app(operator: str, *arguments: str) -> str:
    return tag("OMA", operator + "".join(arguments))


def std(cd: str, name: str, *arguments: str) -> str:
    return app(oms(cd, name), *arguments)


def typed(name: str) -> str:
    return oms("typed1", name, cdbase=TYPED_CDBASE)


def ra(name: str) -> str:
    return oms("realanalysis1", name, cdbase=TYPED_CDBASE)


def typed_var(name: str, type_expression: str) -> str:
    return tag("OMATTR", tag("OMATP", typed("type") + type_expression) + omv(name))


def real_var(name: str) -> str:
    return typed_var(name, typed("Real"))


def typed_forall(names: tuple[tuple[str, str], ...], body: str) -> str:
    variables = "".join(
        typed_var(name, type_expression) for name, type_expression in names
    )
    return tag("OMBIND", typed("forall") + tag("OMBVAR", variables) + body)


def typed_exists(name: str, type_expression: str, body: str) -> str:
    return tag(
        "OMBIND",
        typed("exists") + tag("OMBVAR", typed_var(name, type_expression)) + body,
    )


def real_lambda(name: str, body: str) -> str:
    return tag("OMBIND", ra("lambda") + tag("OMBVAR", real_var(name)) + body)


def of_int(value: int) -> str:
    return app(ra("of_int"), omi(value))


def apply(function: str, point: str) -> str:
    return app(ra("apply"), function, point)


def eq(left: str, right: str) -> str:
    return std("relation1", "eq", left, right)


def neq(left: str, right: str) -> str:
    return std("relation1", "neq", left, right)


def lt(left: str, right: str) -> str:
    return std("relation1", "lt", left, right)


def plus(*arguments: str) -> str:
    return std("arith1", "plus", *arguments)


def times(*arguments: str) -> str:
    return std("arith1", "times", *arguments)


def minus(left: str, right: str) -> str:
    return std("arith1", "minus", left, right)


def power(base: str, exponent: int) -> str:
    return std("arith1", "power", base, omi(exponent))


def absolute(value: str) -> str:
    return std("arith1", "abs", value)


def and_(left: str, right: str) -> str:
    return std("logic1", "and", left, right)


def implies(left: str, right: str) -> str:
    return std("logic1", "implies", left, right)


def openmath(proposition: str) -> str:
    return f'<OMOBJ xmlns="{OPENMATH}" version="2.0">{proposition}</OMOBJ>'


def epsilon_delta_identity_xml() -> str:
    a, eps, delta, x = omv("a"), omv("eps"), omv("delta"), omv("x")
    displacement = absolute(minus(x, a))
    body = typed_forall(
        (("a", typed("Real")),),
        typed_forall(
            (("eps", typed("Real")),),
            implies(
                lt(of_int(0), eps),
                typed_exists(
                    "delta",
                    typed("Real"),
                    and_(
                        lt(of_int(0), delta),
                        typed_forall(
                            (("x", typed("Real")),),
                            implies(lt(displacement, delta), lt(displacement, eps)),
                        ),
                    ),
                ),
            ),
        ),
    )
    return openmath(body)


def has_deriv_square_xml() -> str:
    a, x = omv("a"), omv("x")
    square_function = real_lambda("x", power(x, 2))
    body = typed_forall(
        (("a", typed("Real")),),
        app(ra("has_deriv_at"), square_function, a, times(of_int(2), a)),
    )
    return openmath(body)


def differentiable_cubic_xml() -> str:
    a, x = omv("a"), omv("x")
    cubic_minus_linear = real_lambda("x", minus(power(x, 3), times(of_int(2), x)))
    body = typed_forall(
        (("a", typed("Real")),),
        app(ra("differentiable_at"), cubic_minus_linear, a),
    )
    return openmath(body)


def interval_integrable_square_xml() -> str:
    x = omv("x")
    square_function = real_lambda("x", power(x, 2))
    return openmath(
        app(ra("interval_integrable"), square_function, of_int(0), of_int(1))
    )


def epsilon_delta_affine_xml() -> str:
    a, eps, delta, x = omv("a"), omv("eps"), omv("delta"), omv("x")
    shifted_x = plus(x, of_int(3))
    shifted_a = plus(a, of_int(3))
    body = typed_forall(
        (("a", typed("Real")),),
        typed_forall(
            (("eps", typed("Real")),),
            implies(
                lt(of_int(0), eps),
                typed_exists(
                    "delta",
                    typed("Real"),
                    and_(
                        lt(of_int(0), delta),
                        typed_forall(
                            (("x", typed("Real")),),
                            implies(
                                lt(absolute(minus(x, a)), delta),
                                lt(absolute(minus(shifted_x, shifted_a)), eps),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )
    return openmath(body)


def epsilon_delta_continuous_square_xml() -> str:
    a, x = omv("a"), omv("x")
    return openmath(
        typed_forall(
            (("a", typed("Real")),),
            app(
                ra("epsilon_delta_continuous_at"),
                real_lambda("x", power(x, 2)),
                a,
            ),
        )
    )


def continuous_cubic_xml() -> str:
    a, x = omv("a"), omv("x")
    cubic_minus_linear = real_lambda("x", minus(power(x, 3), times(of_int(2), x)))
    return openmath(
        typed_forall(
            (("a", typed("Real")),), app(ra("continuous_at"), cubic_minus_linear, a)
        )
    )


def continuous_reciprocal_xml() -> str:
    a, x = omv("a"), omv("x")
    reciprocal = real_lambda("x", std("arith1", "divide", of_int(1), x))
    return openmath(
        typed_forall(
            (("a", typed("Real")),),
            implies(neq(a, of_int(0)), app(ra("continuous_at"), reciprocal, a)),
        )
    )


def has_deriv_affine_xml() -> str:
    a, x = omv("a"), omv("x")
    affine = real_lambda("x", plus(times(of_int(3), x), of_int(5)))
    return openmath(
        typed_forall(
            (("a", typed("Real")),), app(ra("has_deriv_at"), affine, a, of_int(3))
        )
    )


def has_deriv_sum_xml() -> str:
    a, x = omv("a"), omv("x")
    polynomial = real_lambda("x", plus(power(x, 2), times(of_int(3), x)))
    return openmath(
        typed_forall(
            (("a", typed("Real")),),
            app(
                ra("has_deriv_at"),
                polynomial,
                a,
                plus(times(of_int(2), a), of_int(3)),
            ),
        )
    )


def has_deriv_product_xml() -> str:
    a, x = omv("a"), omv("x")
    product = real_lambda("x", times(plus(x, of_int(1)), minus(x, of_int(1))))
    return openmath(
        typed_forall(
            (("a", typed("Real")),),
            app(ra("has_deriv_at"), product, a, times(of_int(2), a)),
        )
    )


def has_deriv_chain_xml() -> str:
    a, x = omv("a"), omv("x")
    inner_x = plus(power(x, 2), of_int(1))
    inner_a = plus(power(a, 2), of_int(1))
    chained = real_lambda("x", power(inner_x, 3))
    slope = times(of_int(3), power(inner_a, 2), times(of_int(2), a))
    return openmath(
        typed_forall(
            (("a", typed("Real")),), app(ra("has_deriv_at"), chained, a, slope)
        )
    )


def differentiable_affine_xml() -> str:
    a, x = omv("a"), omv("x")
    affine = real_lambda("x", plus(times(of_int(3), x), of_int(5)))
    return openmath(
        typed_forall(
            (("a", typed("Real")),), app(ra("differentiable_at"), affine, a)
        )
    )


def differentiable_product_xml() -> str:
    a, x = omv("a"), omv("x")
    product = real_lambda("x", times(plus(power(x, 2), of_int(1)), minus(x, of_int(1))))
    return openmath(
        typed_forall(
            (("a", typed("Real")),), app(ra("differentiable_at"), product, a)
        )
    )


def differentiable_reciprocal_xml() -> str:
    a, x = omv("a"), omv("x")
    reciprocal = real_lambda("x", std("arith1", "divide", of_int(1), x))
    return openmath(
        typed_forall(
            (("a", typed("Real")),),
            implies(neq(a, of_int(0)), app(ra("differentiable_at"), reciprocal, a)),
        )
    )


def interval_integrable_affine_xml() -> str:
    a, b, x = omv("a"), omv("b"), omv("x")
    affine = real_lambda("x", plus(times(of_int(3), x), of_int(5)))
    return openmath(
        typed_forall(
            (("a", typed("Real")), ("b", typed("Real"))),
            app(ra("interval_integrable"), affine, a, b),
        )
    )


def interval_integrable_cubic_xml() -> str:
    a, b, x = omv("a"), omv("b"), omv("x")
    cubic_minus_linear = real_lambda("x", minus(power(x, 3), times(of_int(2), x)))
    return openmath(
        typed_forall(
            (("a", typed("Real")), ("b", typed("Real"))),
            app(ra("interval_integrable"), cubic_minus_linear, a, b),
        )
    )


def interval_integrable_product_xml() -> str:
    a, b, x = omv("a"), omv("b"), omv("x")
    product = real_lambda("x", times(plus(power(x, 2), of_int(1)), minus(x, of_int(1))))
    return openmath(
        typed_forall(
            (("a", typed("Real")), ("b", typed("Real"))),
            app(ra("interval_integrable"), product, a, b),
        )
    )


def interval_integrable_reciprocal_quadratic_xml() -> str:
    a, b, x = omv("a"), omv("b"), omv("x")
    reciprocal_quadratic = real_lambda(
        "x", std("arith1", "divide", of_int(1), plus(power(x, 2), of_int(1)))
    )
    return openmath(
        typed_forall(
            (("a", typed("Real")), ("b", typed("Real"))),
            app(ra("interval_integrable"), reciprocal_quadratic, a, b),
        )
    )


EPSILON_TARGET = (
    "∀ (a ε : ℝ), 0 < ε → ∃ δ : ℝ, 0 < δ ∧ ∀ x : ℝ, |x - a| < δ → |x - a| < ε"
)
EPSILON_WITNESS = """example (a ε : ℝ) (hε : 0 < ε) :
    ∃ δ : ℝ, 0 < δ ∧ ∀ x : ℝ, |x - a| < δ → |x - a| < ε := by
  exact ⟨ε, hε, fun _ hx => hx⟩"""

DERIV_TARGET = "∀ a : ℝ, HasDerivAt (fun x : ℝ => x ^ 2) (2 * a) a"
DERIV_WITNESS = """example (a : ℝ) : HasDerivAt (fun x : ℝ => x ^ 2) (2 * a) a := by
  simpa [pow_two] using hasDerivAt_pow 2 a"""

DIFFERENTIABLE_TARGET = "∀ a : ℝ, DifferentiableAt ℝ (fun x : ℝ => x ^ 3 - 2 * x) a"
DIFFERENTIABLE_WITNESS = """example (a : ℝ) : DifferentiableAt ℝ (fun x : ℝ => x ^ 3 - 2 * x) a := by
  fun_prop"""

INTEGRABLE_TARGET = "IntervalIntegrable (fun x : ℝ => x ^ 2) (MeasureTheory.volume : MeasureTheory.Measure ℝ) 0 1"
INTEGRABLE_WITNESS = """example : IntervalIntegrable (fun x : ℝ => x ^ 2)
    (MeasureTheory.volume : MeasureTheory.Measure ℝ) 0 1 := by
  have hcont : Continuous (fun x : ℝ => x ^ 2) := by fun_prop
  exact hcont.intervalIntegrable (μ := (MeasureTheory.volume : MeasureTheory.Measure ℝ)) 0 1"""

EPSILON_AFFINE_TARGET = (
    "∀ (a ε : ℝ), 0 < ε → ∃ δ : ℝ, 0 < δ ∧ ∀ x : ℝ, "
    "|x - a| < δ → |(x + 3) - (a + 3)| < ε"
)
EPSILON_AFFINE_WITNESS = """example (a ε : ℝ) (hε : 0 < ε) :
    ∃ δ : ℝ, 0 < δ ∧ ∀ x : ℝ, |x - a| < δ → |(x + 3) - (a + 3)| < ε := by
  refine ⟨ε, hε, ?_⟩
  intro x hx
  simpa using hx"""

EPSILON_SQUARE_TARGET = "∀ a : ℝ, ContinuousAt (fun x : ℝ => x ^ 2) a"
EPSILON_SQUARE_WITNESS = """example (a : ℝ) : ContinuousAt (fun x : ℝ => x ^ 2) a := by
  fun_prop"""

CONTINUOUS_CUBIC_TARGET = "∀ a : ℝ, ContinuousAt (fun x : ℝ => x ^ 3 - 2 * x) a"
CONTINUOUS_CUBIC_WITNESS = """example (a : ℝ) : ContinuousAt (fun x : ℝ => x ^ 3 - 2 * x) a := by
  fun_prop"""

CONTINUOUS_RECIPROCAL_TARGET = "∀ a : ℝ, a ≠ 0 → ContinuousAt (fun x : ℝ => 1 / x) a"
CONTINUOUS_RECIPROCAL_WITNESS = """example (a : ℝ) (h : a ≠ 0) : ContinuousAt (fun x : ℝ => 1 / x) a := by
  simpa only [one_div] using continuousAt_inv₀ h"""

DERIV_AFFINE_TARGET = "∀ a : ℝ, HasDerivAt (fun x : ℝ => 3 * x + 5) 3 a"
DERIV_AFFINE_WITNESS = """example (a : ℝ) : HasDerivAt (fun x : ℝ => 3 * x + 5) 3 a := by
  simpa using ((hasDerivAt_id (x := a)).const_mul (3 : ℝ)).add_const (5 : ℝ)"""

DERIV_SUM_TARGET = "∀ a : ℝ, HasDerivAt (fun x : ℝ => x ^ 2 + 3 * x) (2 * a + 3) a"
DERIV_SUM_WITNESS = """example (a : ℝ) : HasDerivAt (fun x : ℝ => x ^ 2 + 3 * x) (2 * a + 3) a := by
  convert! (hasDerivAt_pow 2 a).add (hasDerivAt_const_mul 3) using 1
  all_goals ring"""

DERIV_PRODUCT_TARGET = "∀ a : ℝ, HasDerivAt (fun x : ℝ => (x + 1) * (x - 1)) (2 * a) a"
DERIV_PRODUCT_WITNESS = """example (a : ℝ) : HasDerivAt (fun x : ℝ => (x + 1) * (x - 1)) (2 * a) a := by
  convert! ((hasDerivAt_id (x := a)).add_const 1).mul ((hasDerivAt_id (x := a)).sub_const 1) using 1
  all_goals simp [id_eq]
  all_goals ring"""

DERIV_CHAIN_TARGET = (
    "∀ a : ℝ, HasDerivAt (fun x : ℝ => (x ^ 2 + 1) ^ 3) "
    "(3 * (a ^ 2 + 1) ^ 2 * (2 * a)) a"
)
DERIV_CHAIN_WITNESS = """example (a : ℝ) : HasDerivAt (fun x : ℝ => (x ^ 2 + 1) ^ 3) (3 * (a ^ 2 + 1) ^ 2 * (2 * a)) a := by
  convert! ((hasDerivAt_pow 2 a).add_const 1).pow 3 using 1
  all_goals ring"""

DIFFERENTIABLE_AFFINE_TARGET = "∀ a : ℝ, DifferentiableAt ℝ (fun x : ℝ => 3 * x + 5) a"
DIFFERENTIABLE_AFFINE_WITNESS = """example (a : ℝ) : DifferentiableAt ℝ (fun x : ℝ => 3 * x + 5) a := by
  fun_prop"""

DIFFERENTIABLE_PRODUCT_TARGET = (
    "∀ a : ℝ, DifferentiableAt ℝ (fun x : ℝ => (x ^ 2 + 1) * (x - 1)) a"
)
DIFFERENTIABLE_PRODUCT_WITNESS = """example (a : ℝ) : DifferentiableAt ℝ (fun x : ℝ => (x ^ 2 + 1) * (x - 1)) a := by
  fun_prop"""

DIFFERENTIABLE_RECIPROCAL_TARGET = (
    "∀ a : ℝ, a ≠ 0 → DifferentiableAt ℝ (fun x : ℝ => 1 / x) a"
)
DIFFERENTIABLE_RECIPROCAL_WITNESS = """example (a : ℝ) (h : a ≠ 0) : DifferentiableAt ℝ (fun x : ℝ => 1 / x) a := by
  simpa only [one_div] using differentiableAt_inv (𝕜 := ℝ) h"""

INTEGRABLE_AFFINE_TARGET = (
    "∀ a b : ℝ, IntervalIntegrable (fun x : ℝ => 3 * x + 5) "
    "(MeasureTheory.volume : MeasureTheory.Measure ℝ) a b"
)
INTEGRABLE_AFFINE_WITNESS = """example (a b : ℝ) : IntervalIntegrable (fun x : ℝ => 3 * x + 5)
    (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b := by
  exact (by fun_prop : Continuous (fun x : ℝ => 3 * x + 5)).intervalIntegrable (μ := (MeasureTheory.volume : MeasureTheory.Measure ℝ)) a b"""

INTEGRABLE_CUBIC_TARGET = (
    "∀ a b : ℝ, IntervalIntegrable (fun x : ℝ => x ^ 3 - 2 * x) "
    "(MeasureTheory.volume : MeasureTheory.Measure ℝ) a b"
)
INTEGRABLE_CUBIC_WITNESS = """example (a b : ℝ) : IntervalIntegrable (fun x : ℝ => x ^ 3 - 2 * x)
    (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b := by
  exact (by fun_prop : Continuous (fun x : ℝ => x ^ 3 - 2 * x)).intervalIntegrable (μ := (MeasureTheory.volume : MeasureTheory.Measure ℝ)) a b"""

INTEGRABLE_PRODUCT_TARGET = (
    "∀ a b : ℝ, IntervalIntegrable (fun x : ℝ => (x ^ 2 + 1) * (x - 1)) "
    "(MeasureTheory.volume : MeasureTheory.Measure ℝ) a b"
)
INTEGRABLE_PRODUCT_WITNESS = """example (a b : ℝ) : IntervalIntegrable (fun x : ℝ => (x ^ 2 + 1) * (x - 1))
    (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b := by
  exact (by fun_prop : Continuous (fun x : ℝ => (x ^ 2 + 1) * (x - 1))).intervalIntegrable (μ := (MeasureTheory.volume : MeasureTheory.Measure ℝ)) a b"""

INTEGRABLE_RECIPROCAL_QUADRATIC_TARGET = (
    "∀ a b : ℝ, IntervalIntegrable (fun x : ℝ => 1 / (x ^ 2 + 1)) "
    "(MeasureTheory.volume : MeasureTheory.Measure ℝ) a b"
)
INTEGRABLE_RECIPROCAL_QUADRATIC_WITNESS = """example (a b : ℝ) : IntervalIntegrable (fun x : ℝ => 1 / (x ^ 2 + 1))
    (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b := by
  have hcont : Continuous (fun x : ℝ => 1 / (x ^ 2 + 1)) := by
    apply continuous_const.div (by fun_prop)
    intro x
    nlinarith [sq_nonneg x]
  exact hcont.intervalIntegrable (μ := (MeasureTheory.volume : MeasureTheory.Measure ℝ)) a b"""


def adopted_cards() -> list[AdoptedCard]:
    return [
        AdoptedCard(
            "real_analysis_eps_delta_identity",
            "For every real a and every positive real ε, there is a positive real δ such that |x-a|<δ implies |x-a|<ε for every real x.",
            "Fix ε>0 and choose δ=ε; the two distance inequalities are identical.",
            (
                "Fix arbitrary real a and positive real ε.",
                "Choose δ=ε.",
                "The choice is positive because ε>0.",
                "Assume an arbitrary real x satisfies |x-a|<δ.",
                "Substitute δ=ε to obtain |x-a|<ε and close the quantifiers.",
            ),
            epsilon_delta_identity_xml(),
            (
                "typed1:forall",
                "typed1:exists",
                "typed1:Real",
                "realanalysis1:of_int",
                "arith1:minus",
                "arith1:abs",
                "relation1:lt",
                "logic1:and",
                "logic1:implies",
            ),
            EPSILON_TARGET,
            EPSILON_WITNESS,
            ("typed_real_analysis_witness_01_epsilon_delta_identity",),
            "The XML is the raw ε–δ formula for the identity function. Every scalar binder has sort Real; the Lean target has the same binder order, inequalities, and δ=ε witness.",
        ),
        AdoptedCard(
            "real_analysis_has_deriv_square",
            "For every real a, the derivative of x^2 at a is 2a.",
            "Use the power rule for x² and normalize the resulting slope at a.",
            (
                "Fix an arbitrary real a.",
                "View x² as a polynomial real function.",
                "Apply the derivative rule for the second power at a.",
                "Simplify the coefficient to 2·a.",
                "Record the result as HasDerivAt at the original point a.",
            ),
            has_deriv_square_xml(),
            (
                "typed1:forall",
                "typed1:Real",
                "realanalysis1:lambda",
                "realanalysis1:of_int",
                "realanalysis1:has_deriv_at",
                "arith1:power",
                "arith1:times",
            ),
            DERIV_TARGET,
            DERIV_WITNESS,
            ("typed_real_analysis_witness_02_has_deriv_square",),
            "realanalysis1:has_deriv_at(f,a,m) lowers directly to HasDerivAt f m a. The XML lambda is a Real→Real function and 2 is explicitly realanalysis1:of_int(2).",
        ),
        AdoptedCard(
            "real_analysis_differentiable_cubic_minus_linear",
            "For every real a, x^3 - 2x is differentiable at a.",
            "Use differentiability closure for polynomial powers, scalar multiplication, and subtraction.",
            (
                "Fix an arbitrary real a.",
                "The map x↦x³ is differentiable at a.",
                "The map x↦2x is differentiable at a.",
                "Apply closure of differentiability under subtraction.",
                "Conclude that x³-2x is differentiable at a.",
            ),
            differentiable_cubic_xml(),
            (
                "typed1:forall",
                "typed1:Real",
                "realanalysis1:lambda",
                "realanalysis1:of_int",
                "realanalysis1:differentiable_at",
                "arith1:power",
                "arith1:times",
                "arith1:minus",
            ),
            DIFFERENTIABLE_TARGET,
            DIFFERENTIABLE_WITNESS,
            ("typed_real_analysis_witness_03_differentiable_cubic_minus_linear",),
            "realanalysis1:differentiable_at(f,a) lowers directly to DifferentiableAt ℝ f a. The cubic and linear function body is identical after explicit integer-to-real lowering.",
        ),
        AdoptedCard(
            "real_analysis_interval_integrable_square_zero_one",
            "The real function x ↦ x^2 is interval-integrable from 0 to 1.",
            "Establish global continuity of x², then use continuity to obtain interval integrability.",
            (
                "Recognize x↦x² as a polynomial real function.",
                "Establish that this function is continuous on ℝ.",
                "Restrict the continuity statement to the interval from 0 to 1.",
                "Apply the continuity-implies-interval-integrable theorem for volume.",
                "Conclude interval integrability on the oriented interval 0..1.",
            ),
            interval_integrable_square_xml(),
            (
                "realanalysis1:lambda",
                "realanalysis1:of_int",
                "realanalysis1:interval_integrable",
                "arith1:power",
            ),
            INTEGRABLE_TARGET,
            INTEGRABLE_WITNESS,
            ("typed_real_analysis_witness_07_interval_integrable_square",),
            "realanalysis1:interval_integrable(f,a,b) lowers to IntervalIntegrable f volume a b. This admits the exact integration side condition, not an unsupported bare integral-value claim.",
        ),
        AdoptedCard(
            "real_analysis_eps_delta_affine_shift",
            "For every real a and every positive real ε, the affine function x ↦ x+3 has a positive δ such that |x-a|<δ implies |(x+3)-(a+3)|<ε.",
            "Choose δ=ε and cancel the common affine shift in the output distance.",
            (
                "Fix arbitrary real a and positive real ε.",
                "Choose δ=ε.",
                "The choice is positive by the hypothesis on ε.",
                "Let x satisfy |x-a|<δ.",
                "Cancel the shared constant 3 and conclude the required output bound.",
            ),
            epsilon_delta_affine_xml(),
            (
                "typed1:forall",
                "typed1:exists",
                "typed1:Real",
                "realanalysis1:of_int",
                "arith1:plus",
                "arith1:minus",
                "arith1:abs",
                "relation1:lt",
                "logic1:and",
                "logic1:implies",
            ),
            EPSILON_AFFINE_TARGET,
            EPSILON_AFFINE_WITNESS,
            ("typed_real_analysis_witness_09_epsilon_delta_affine_shift",),
            "The XML is a complete raw ε–δ formula for x↦x+3. The Lean witness has the same quantifiers and proves the target by δ=ε and cancellation of the shared shift.",
        ),
        AdoptedCard(
            "real_analysis_epsilon_delta_continuous_square",
            "For every real a, x ↦ x^2 is ε–δ continuous at a.",
            "Use the profile abbreviation whose fixed semantics is the raw ε–δ continuity predicate, then prove polynomial continuity.",
            (
                "Fix an arbitrary real a.",
                "Recognize x↦x² as a real polynomial.",
                "Use continuity of polynomial operations at a.",
                "Lower the abbreviation to ContinuousAt in the pinned Lean semantics.",
                "Conclude ε–δ continuity at a.",
            ),
            epsilon_delta_continuous_square_xml(),
            (
                "typed1:forall",
                "typed1:Real",
                "realanalysis1:lambda",
                "realanalysis1:epsilon_delta_continuous_at",
                "arith1:power",
            ),
            EPSILON_SQUARE_TARGET,
            EPSILON_SQUARE_WITNESS,
            ("typed_real_analysis_witness_10_epsilon_delta_continuous_square",),
            "realanalysis1:epsilon_delta_continuous_at has the profile-fixed raw ε–δ semantics; for this polynomial it lowers to the exact Lean ContinuousAt target.",
        ),
        AdoptedCard(
            "real_analysis_continuous_cubic_minus_linear",
            "For every real a, x ↦ x^3-2x is continuous at a.",
            "Build continuity from powers, scalar multiplication, and subtraction.",
            (
                "Fix an arbitrary real a.",
                "The cubic map is continuous at a.",
                "The linear map x↦2x is continuous at a.",
                "Use closure under subtraction.",
                "Conclude continuity of x³-2x at a.",
            ),
            continuous_cubic_xml(),
            (
                "typed1:forall",
                "typed1:Real",
                "realanalysis1:lambda",
                "realanalysis1:continuous_at",
                "realanalysis1:of_int",
                "arith1:power",
                "arith1:times",
                "arith1:minus",
            ),
            CONTINUOUS_CUBIC_TARGET,
            CONTINUOUS_CUBIC_WITNESS,
            ("typed_real_analysis_witness_11_continuous_cubic_minus_linear",),
            "realanalysis1:continuous_at(f,a) lowers directly to ContinuousAt f a; the OpenMath polynomial body matches the Lean function after explicit integer-to-real lowering.",
        ),
        AdoptedCard(
            "real_analysis_continuous_reciprocal_nonzero",
            "For every nonzero real a, x ↦ 1/x is continuous at a.",
            "Use continuity of inversion with the explicit nonzero denominator premise.",
            (
                "Fix a real a with a≠0.",
                "Represent the reciprocal as 1 divided by x.",
                "The denominator is nonzero at a by the premise.",
                "Apply continuity of inversion at a.",
                "Conclude continuity of x↦1/x at a.",
            ),
            continuous_reciprocal_xml(),
            (
                "typed1:forall",
                "typed1:Real",
                "realanalysis1:lambda",
                "realanalysis1:continuous_at",
                "realanalysis1:of_int",
                "arith1:divide",
                "relation1:neq",
                "logic1:implies",
            ),
            CONTINUOUS_RECIPROCAL_TARGET,
            CONTINUOUS_RECIPROCAL_WITNESS,
            ("typed_real_analysis_witness_12_continuous_reciprocal_nonzero",),
            "The XML carries a≠0 as a premise before continuous_at. It lowers exactly to the Lean inversion-continuity theorem; no denominator condition is inferred from prose.",
        ),
        AdoptedCard(
            "real_analysis_has_deriv_affine",
            "For every real a, the derivative of 3x+5 at a is 3.",
            "Combine the derivative of the identity with scalar multiplication and a constant shift.",
            (
                "Fix an arbitrary real a.",
                "Differentiate the identity map at a.",
                "Multiply the derivative by 3.",
                "Adding the constant 5 leaves the derivative unchanged.",
                "Record HasDerivAt with slope 3.",
            ),
            has_deriv_affine_xml(),
            (
                "typed1:forall",
                "typed1:Real",
                "realanalysis1:lambda",
                "realanalysis1:has_deriv_at",
                "realanalysis1:of_int",
                "arith1:times",
                "arith1:plus",
            ),
            DERIV_AFFINE_TARGET,
            DERIV_AFFINE_WITNESS,
            ("typed_real_analysis_witness_13_has_deriv_affine",),
            "The function, point, and slope occupy the exact has_deriv_at signature slots and lower directly to HasDerivAt.",
        ),
        AdoptedCard(
            "real_analysis_has_deriv_sum_square_linear",
            "For every real a, the derivative of x^2+3x at a is 2a+3.",
            "Apply the sum rule to the square and linear terms and normalize the slope.",
            (
                "Fix an arbitrary real a.",
                "Differentiate x² at a to obtain 2a.",
                "Differentiate 3x at a to obtain 3.",
                "Apply the derivative sum rule.",
                "Normalize the resulting slope to 2a+3.",
            ),
            has_deriv_sum_xml(),
            (
                "typed1:forall",
                "typed1:Real",
                "realanalysis1:lambda",
                "realanalysis1:has_deriv_at",
                "realanalysis1:of_int",
                "arith1:power",
                "arith1:times",
                "arith1:plus",
            ),
            DERIV_SUM_TARGET,
            DERIV_SUM_WITNESS,
            ("typed_real_analysis_witness_14_has_deriv_sum_square_linear",),
            "The XML is the same polynomial and slope as the Lean HasDerivAt target. The witness explicitly invokes the sum rule and normalizes algebraically.",
        ),
        AdoptedCard(
            "real_analysis_has_deriv_product_shifted_identity",
            "For every real a, the derivative of (x+1)(x-1) at a is 2a.",
            "Use the product rule after differentiating both shifted identity factors.",
            (
                "Fix an arbitrary real a.",
                "Differentiate x+1 and x-1 at a.",
                "Apply the product rule.",
                "Substitute the two function values at a.",
                "Simplify the slope to 2a.",
            ),
            has_deriv_product_xml(),
            (
                "typed1:forall",
                "typed1:Real",
                "realanalysis1:lambda",
                "realanalysis1:has_deriv_at",
                "realanalysis1:of_int",
                "arith1:plus",
                "arith1:minus",
                "arith1:times",
            ),
            DERIV_PRODUCT_TARGET,
            DERIV_PRODUCT_WITNESS,
            ("typed_real_analysis_witness_15_has_deriv_product_shifted_identity",),
            "The profile permits the product expression and an exact Real slope only. The Lean witness uses HasDerivAt.mul and no total derivative operator.",
        ),
        AdoptedCard(
            "real_analysis_has_deriv_chain_polynomial",
            "For every real a, the derivative of (x^2+1)^3 at a is 3(a^2+1)^2(2a).",
            "Apply the chain rule to the cube of the quadratic inner function.",
            (
                "Fix an arbitrary real a.",
                "Differentiate the inner function x²+1 at a.",
                "Apply the power rule to the outer third power.",
                "Multiply the outer and inner derivative factors.",
                "Record the exact HasDerivAt slope at a.",
            ),
            has_deriv_chain_xml(),
            (
                "typed1:forall",
                "typed1:Real",
                "realanalysis1:lambda",
                "realanalysis1:has_deriv_at",
                "realanalysis1:of_int",
                "arith1:power",
                "arith1:plus",
                "arith1:times",
            ),
            DERIV_CHAIN_TARGET,
            DERIV_CHAIN_WITNESS,
            ("typed_real_analysis_witness_16_has_deriv_chain_polynomial",),
            "The statement uses the predicate-valued has_deriv_at signature rather than a total derivative term. The Lean witness composes the exact polynomial derivative rules.",
        ),
        AdoptedCard(
            "real_analysis_differentiable_affine",
            "For every real a, 3x+5 is differentiable at a.",
            "Use differentiability closure for the identity, scalar multiplication, and constant addition.",
            (
                "Fix an arbitrary real a.",
                "The identity map is differentiable at a.",
                "Scale it by 3.",
                "Add the constant 5.",
                "Conclude differentiability at a.",
            ),
            differentiable_affine_xml(),
            (
                "typed1:forall",
                "typed1:Real",
                "realanalysis1:lambda",
                "realanalysis1:differentiable_at",
                "realanalysis1:of_int",
                "arith1:times",
                "arith1:plus",
            ),
            DIFFERENTIABLE_AFFINE_TARGET,
            DIFFERENTIABLE_AFFINE_WITNESS,
            ("typed_real_analysis_witness_17_differentiable_affine",),
            "The profile predicate lowers directly to DifferentiableAt ℝ. It records differentiability only, without assigning a total derivative value.",
        ),
        AdoptedCard(
            "real_analysis_differentiable_product_polynomial",
            "For every real a, (x^2+1)(x-1) is differentiable at a.",
            "Use closure of differentiability under powers, addition, subtraction, and multiplication.",
            (
                "Fix an arbitrary real a.",
                "Establish differentiability of x²+1 at a.",
                "Establish differentiability of x-1 at a.",
                "Apply closure under multiplication.",
                "Conclude differentiability of the product at a.",
            ),
            differentiable_product_xml(),
            (
                "typed1:forall",
                "typed1:Real",
                "realanalysis1:lambda",
                "realanalysis1:differentiable_at",
                "realanalysis1:of_int",
                "arith1:power",
                "arith1:plus",
                "arith1:minus",
                "arith1:times",
            ),
            DIFFERENTIABLE_PRODUCT_TARGET,
            DIFFERENTIABLE_PRODUCT_WITNESS,
            ("typed_real_analysis_witness_18_differentiable_product_polynomial",),
            "Each OpenMath operation has a fixed Real signature. The Lean target is the same product and uses only DifferentiableAt closure rules.",
        ),
        AdoptedCard(
            "real_analysis_differentiable_reciprocal_nonzero",
            "For every nonzero real a, x ↦ 1/x is differentiable at a.",
            "Apply differentiability of inversion after discharging the explicit nonzero denominator premise.",
            (
                "Fix a real a with a≠0.",
                "Express the function as reciprocal of x.",
                "Use the nonzero premise at the evaluation point.",
                "Apply differentiability of inversion.",
                "Conclude differentiability at a.",
            ),
            differentiable_reciprocal_xml(),
            (
                "typed1:forall",
                "typed1:Real",
                "realanalysis1:lambda",
                "realanalysis1:differentiable_at",
                "realanalysis1:of_int",
                "arith1:divide",
                "relation1:neq",
                "logic1:implies",
            ),
            DIFFERENTIABLE_RECIPROCAL_TARGET,
            DIFFERENTIABLE_RECIPROCAL_WITNESS,
            ("typed_real_analysis_witness_19_differentiable_reciprocal_nonzero",),
            "The nonzero denominator is an explicit typed premise. This card uses differentiable_at only and does not smuggle in a derivative value at the excluded point.",
        ),
        AdoptedCard(
            "real_analysis_interval_integrable_affine_all_endpoints",
            "For all real endpoints a and b, 3x+5 is interval-integrable from a to b.",
            "Prove global continuity of the affine function and restrict it to the requested oriented interval.",
            (
                "Fix arbitrary real endpoints a and b.",
                "Recognize 3x+5 as an affine continuous function.",
                "Establish continuity on all real numbers.",
                "Apply continuity-implies-interval-integrability for volume.",
                "Conclude interval integrability from a to b.",
            ),
            interval_integrable_affine_xml(),
            (
                "typed1:forall",
                "typed1:Real",
                "realanalysis1:lambda",
                "realanalysis1:interval_integrable",
                "realanalysis1:of_int",
                "arith1:times",
                "arith1:plus",
            ),
            INTEGRABLE_AFFINE_TARGET,
            INTEGRABLE_AFFINE_WITNESS,
            ("typed_real_analysis_witness_20_interval_integrable_affine_all_endpoints",),
            "The profile's only integration predicate lowers to IntervalIntegrable f volume a b. No integral value or linearity equality is asserted.",
        ),
        AdoptedCard(
            "real_analysis_interval_integrable_cubic_all_endpoints",
            "For all real endpoints a and b, x^3-2x is interval-integrable from a to b.",
            "Use global polynomial continuity to obtain interval integrability.",
            (
                "Fix arbitrary real endpoints a and b.",
                "Recognize x³-2x as a polynomial function.",
                "Establish its continuity on ℝ.",
                "Apply the interval-integrability consequence of continuity.",
                "Conclude interval integrability from a to b.",
            ),
            interval_integrable_cubic_xml(),
            (
                "typed1:forall",
                "typed1:Real",
                "realanalysis1:lambda",
                "realanalysis1:interval_integrable",
                "realanalysis1:of_int",
                "arith1:power",
                "arith1:times",
                "arith1:minus",
            ),
            INTEGRABLE_CUBIC_TARGET,
            INTEGRABLE_CUBIC_WITNESS,
            ("typed_real_analysis_witness_21_interval_integrable_cubic_all_endpoints",),
            "The Lean receipt proves the exact IntervalIntegrable target for arbitrary real endpoints, matching the profile's oriented-interval predicate.",
        ),
        AdoptedCard(
            "real_analysis_interval_integrable_product_all_endpoints",
            "For all real endpoints a and b, (x^2+1)(x-1) is interval-integrable from a to b.",
            "Use closure of continuous polynomials under products, then interval integrability.",
            (
                "Fix arbitrary real endpoints a and b.",
                "Establish continuity of x²+1.",
                "Establish continuity of x-1.",
                "Multiply the continuous factors.",
                "Apply continuity-implies-interval-integrability.",
                "Conclude interval integrability from a to b.",
            ),
            interval_integrable_product_xml(),
            (
                "typed1:forall",
                "typed1:Real",
                "realanalysis1:lambda",
                "realanalysis1:interval_integrable",
                "realanalysis1:of_int",
                "arith1:power",
                "arith1:plus",
                "arith1:minus",
                "arith1:times",
            ),
            INTEGRABLE_PRODUCT_TARGET,
            INTEGRABLE_PRODUCT_WITNESS,
            ("typed_real_analysis_witness_22_interval_integrable_product_all_endpoints",),
            "This is an integrability-only receipt. The profile does not contain an interval-integral value constructor, so no unsupported value claim is present.",
        ),
        AdoptedCard(
            "real_analysis_interval_integrable_reciprocal_quadratic",
            "For all real endpoints a and b, x ↦ 1/(x^2+1) is interval-integrable from a to b.",
            "Show the denominator is positive everywhere, obtain global continuity, then use interval integrability.",
            (
                "Fix arbitrary real endpoints a and b.",
                "Observe x²+1 is strictly positive for every real x.",
                "Use that fact to establish continuity of the reciprocal quotient.",
                "Apply continuity-implies-interval-integrability for volume.",
                "Conclude interval integrability from a to b.",
            ),
            interval_integrable_reciprocal_quadratic_xml(),
            (
                "typed1:forall",
                "typed1:Real",
                "realanalysis1:lambda",
                "realanalysis1:interval_integrable",
                "realanalysis1:of_int",
                "arith1:power",
                "arith1:plus",
                "arith1:divide",
            ),
            INTEGRABLE_RECIPROCAL_QUADRATIC_TARGET,
            INTEGRABLE_RECIPROCAL_QUADRATIC_WITNESS,
            ("typed_real_analysis_witness_23_interval_integrable_reciprocal_quadratic",),
            "The denominator safety is discharged in the Lean witness for every real x. The typed statement itself asserts only interval_integrable, never an integral value.",
        ),
    ]


def excluded_witnesses() -> list[dict[str, object]]:
    source = {
        "typed_real_analysis_witness_04_mvt_deriv_slope": """example {f : ℝ → ℝ} {a b : ℝ} (hab : a < b)
    (hcont : ContinuousOn f (Icc a b))
    (hdiff : DifferentiableOn ℝ f (Ioo a b)) :
    ∃ c ∈ Ioo a b, deriv f c = (f b - f a) / (b - a) := by
  exact exists_deriv_eq_slope f hab hcont hdiff""",
        "typed_real_analysis_witness_05_taylor2_exact_quadratic": """noncomputable def taylor2 (f0 f1 f2 x : ℝ) : ℝ := f0 + f1 * x + (f2 / 2) * x ^ 2

example (x : ℝ) : x ^ 2 = taylor2 0 0 2 x := by
  simp [taylor2]""",
        "typed_real_analysis_witness_06_interval_integral_square_value": """example : (∫ x : ℝ in 0..1, x ^ 2) = 1 / 3 := by
  norm_num [integral_pow]""",
        "typed_real_analysis_witness_08_improper_exp": """example : ∫ x : ℝ in Ioi 0, Real.exp (-x) = 1 := by
  simpa using integral_exp_neg_Ioi_zero""",
    }
    return [
        {
            "witness_id": "typed_real_analysis_witness_04_mvt_deriv_slope",
            "source_sha256": sha256(
                source["typed_real_analysis_witness_04_mvt_deriv_slope"]
            ),
            "disposition": "excluded",
            "reason": "The Lean conclusion is phrased with total `deriv f c`. The v1 profile intentionally has no `deriv`; its MVT form requires `has_deriv_at(f,c,m)` plus the scalar secant equation. This source witness is semantically adjacent but not a three-way exact alignment.",
            "next_receipt_requirement": "Create and compile a new exact HasDerivAt-based MVT witness before authoring a card.",
        },
        {
            "witness_id": "typed_real_analysis_witness_05_taylor2_exact_quadratic",
            "source_sha256": sha256(
                source["typed_real_analysis_witness_05_taylor2_exact_quadratic"]
            ),
            "disposition": "excluded",
            "reason": "The local Lean definition taylor2 has no v1 OpenMath denotation. General Taylor data needs degree, iterated derivative, factorial cast, smoothness, and remainder-point signatures reserved for typed-real-analysis-taylor-v1.",
            "next_receipt_requirement": "Wait for the separate Taylor profile and its registry digest.",
        },
        {
            "witness_id": "typed_real_analysis_witness_06_interval_integral_square_value",
            "source_sha256": sha256(
                source["typed_real_analysis_witness_06_interval_integral_square_value"]
            ),
            "disposition": "excluded",
            "reason": "Although interval_integral has a Real result sort, a v1 integral-value card must carry interval_integrable or a recognized continuity-to-integrability premise. This witness proves only the value; it cannot by itself meet the profile's admission template.",
            "next_receipt_requirement": "Fuse this value proof with witness_07 into one exact conjunctive Lean target and one XML card.",
        },
        {
            "witness_id": "typed_real_analysis_witness_08_improper_exp",
            "source_sha256": sha256(
                source["typed_real_analysis_witness_08_improper_exp"]
            ),
            "disposition": "excluded",
            "reason": "v1 has no improper-integral predicate. The Lean statement is a measure integral over Ioi 0, whereas the proposed future profile uses a finite-real limit predicate has_improper_integral_to_pos_inf.",
            "next_receipt_requirement": "Wait for typed-improper-integral-v1 and a limit-based exact witness.",
        },
    ]


def _validate_adopted_card_source(card: AdoptedCard, *, witness_file: str) -> None:
    if not card.id or not card.canonical_statement or not card.proof_strategy:
        raise ValueError("Sealed typed-real-analysis card has an empty required field.")
    if (
        not 4 <= len(card.sketch_steps) <= 8
        or any(not step.strip() for step in card.sketch_steps)
    ):
        raise ValueError("Sealed typed-real-analysis card requires 4..8 non-empty sketch steps.")
    if len(card.source_witness_ids) != 1 or not card.source_witness_ids[0]:
        raise ValueError("Sealed typed-real-analysis card must bind exactly one witness id.")
    if not card.lean_target or not card.lean_witness:
        raise ValueError("Sealed typed-real-analysis card has incomplete Lean evidence.")
    marker = f"-- manifest card: {card.id}\n{card.lean_witness}"
    if marker not in witness_file:
        raise ValueError(
            f"Sealed typed-real-analysis card `{card.id}` is not bound to the Lean witness file."
        )


def rendered_card(card: AdoptedCard, *, witness_file: str) -> dict[str, object]:
    _validate_adopted_card_source(card, witness_file=witness_file)
    canonical = canonicalize_typed_real_analysis_openmath_xml(card.openmath_xml)
    validate_canonical_typed_real_analysis_openmath_xml(canonical)
    source = asdict(card)
    source.update(
        {
            "openmath_xml_sha256": sha256(card.openmath_xml),
            "canonical_openmath_xml": canonical,
            "canonical_openmath_xml_sha256": sha256(canonical),
            "canonical_statement_sha256": sha256(card.canonical_statement),
            "lean_target_sha256": sha256(card.lean_target),
            "lean_witness_sha256": sha256(card.lean_witness),
            "source_witness_sha256": sha256(card.lean_witness),
            "profile_validation_status": "validated_local_typed_real_analysis_v1_sealed",
            "admission_status": "sealed-local-authoring-revision: not a DB Draft or a translation receipt",
        }
    )
    return source


def _validate_witness_audit(
    cards: list[dict[str, object]], witness_audit: list[dict[str, object]]
) -> None:
    adopted = {
        item["witness_id"]: item
        for item in witness_audit
        if item["disposition"] == "adopted"
    }
    if len(adopted) != len(cards):
        raise ValueError("Sealed typed-real-analysis witness audit does not cover every card.")
    for card in cards:
        source_ids = card["source_witness_ids"]
        if not isinstance(source_ids, (list, tuple)) or len(source_ids) != 1:
            raise ValueError("Sealed typed-real-analysis card has an invalid witness binding.")
        audit = adopted.get(source_ids[0])
        if audit is None or audit["card_id"] != card["id"]:
            raise ValueError("Sealed typed-real-analysis witness audit card mapping is invalid.")
        if audit["source_sha256"] != card["source_witness_sha256"]:
            raise ValueError("Sealed typed-real-analysis witness audit digest is stale.")


def verify_lean(witness_file: Path) -> None:
    workspace = ROOT / "pals-agent" / "lean-workspace"
    completed = subprocess.run(
        ["lake", "env", "lean", str(witness_file)],
        cwd=workspace,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(
            f"Lean compilation failed:\n{completed.stdout}{completed.stderr}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", choices=("base", "expansion"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify-lean", action="store_true")
    args = parser.parse_args()

    all_cards = adopted_cards()
    if args.scope == "base":
        cards_source = all_cards[:4]
        witness_path = BASE_WITNESS_FILE
        design_path = BASE_DESIGN_FILE
        schema_version = _BASE_SCHEMA_VERSION
        seal = {
            "scope": "local typed-real-analysis authoring evidence only",
            "admission": "not admitted to the generic DB, seed, embedding index, or PFI package",
            "revision": "typed-real-analysis-v1-local-r1",
        }
        excluded = excluded_witnesses()
    else:
        cards_source = all_cards[4:]
        witness_path = EXPANSION_WITNESS_FILE
        design_path = EXPANSION_DESIGN_FILE
        schema_version = _EXPANSION_SCHEMA_VERSION
        seal = {
            "scope": "local typed-real-analysis-v1 r2 expansion authoring evidence only",
            "admission": "not admitted to the generic DB, seed, embedding index, or PFI package",
            "revision": "typed-real-analysis-v1-expansion-r2",
        }
        excluded = []
    witness_file = witness_path.read_text(encoding="utf-8")
    cards = [rendered_card(card, witness_file=witness_file) for card in cards_source]
    witness_audit = [
        {
            "witness_id": card["source_witness_ids"][0],
            "source_sha256": card["source_witness_sha256"],
            "disposition": "adopted",
            "card_id": card["id"],
            "three_way_alignment": "statement, complete typed OpenMath, and Lean target/witness are manually reviewed as the same proposition",
        }
        for card in cards
    ] + [
        {
            "witness_id": item["witness_id"],
            "source_sha256": item["source_sha256"],
            "disposition": item["disposition"],
            "card_id": None,
            "three_way_alignment": "absent; see excluded_witnesses reason",
        }
        for item in excluded
    ]
    _validate_witness_audit(cards, witness_audit)
    manifest = {
        "schema_version": schema_version,
        "status": _SEALED_STATUS,
        "seal": seal,
        "immutability_contract": {
            "digest_algorithm": "sha256 over exact UTF-8 field bytes",
            "structural_openmath_c14n": "canonical_openmath_xml is produced only after typed-real-analysis-v1 validation and profile C14N; raw authoring XML remains separately hashed.",
            "profile_c14n": "Every card is revalidated from raw openmath_xml and compared with its profile-separated canonical bytes before this manifest digest is written.",
            "mutation_rule": "Any change to statement, proof strategy, sketch, XML, signature trace, Lean target, Lean proof, design digest, or profile registry creates a new sealed revision and manifest digest.",
        },
        "profile": {
            "id": "typed-real-analysis-v1",
            "typed_cdbase": TYPED_CDBASE,
            "profile_design_path": str(design_path.relative_to(ROOT)),
            "profile_design_sha256": sha256(design_path.read_text(encoding="utf-8")),
            "registry_path": "pals_agent/content_dictionaries/typed-real-analysis-v1-registry.json",
            "registry_digest": sha256(REGISTRY_PATH.read_text(encoding="utf-8")),
            "registry_status": "implemented isolated validator and registry; sealed local evidence only, no DB admission is implied",
        },
        "lean_receipt": {
            "witness_path": str(witness_path.relative_to(ROOT)),
            "witness_file_sha256": sha256(witness_file),
            "verification_status": "compiled when generator is run with --verify-lean; sealed evidence only, not an OpenMath-to-Lean translation receipt",
        },
        "adopted_card_count": len(cards),
        "excluded_witness_count": len(excluded),
        "witness_audit_count": len(witness_audit),
        "cards": cards,
        "witness_audit": witness_audit,
        "excluded_witnesses": excluded,
    }
    immutable_payload = json.dumps(
        manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    manifest["manifest_payload_sha256"] = sha256(immutable_payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if args.verify_lean:
        verify_lean(witness_path)
    print(
        f"scope={args.scope} sealed_cards={len(cards)} "
        f"excluded_witnesses={len(excluded)} profile_c14n=validated"
    )
    if args.verify_lean:
        print("lean=passed")


if __name__ == "__main__":
    main()
