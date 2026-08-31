#!/usr/bin/env python3
"""Generate Lean-verified high-school polynomial and rational-expression Drafts.

The generic OpenMath profile has no polynomial, rational-function, or ordered
field *types*.  Every card therefore quantifies only real scalar variables and
spells out each denominator nonzero premise.  This authoring-only utility
never writes the local Draft database.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pals-agent"))

from pals_agent.openmath import (
    MathXMLValidationError,
    canonicalize_openmath_xml,
    canonicalize_retrieval_openmath_xml,
    validate_canonical_retrieval_openmath_xml,
    validate_openmath_statement_semantics,
)

OPENMATH = "http://www.openmath.org/OpenMath"
DEFAULT_DB_COUNT = 335


@dataclass(frozen=True)
class Card:
    id: str
    profile: str
    domain: str
    level: str
    topic: str
    difficulty: str
    canonical_statement: str
    openmath_xml: str
    proof_strategy: str
    sketch_steps: tuple[str, ...]
    lean_witness: str


def tag(name: str, body: str) -> str:
    return f"<{name}>{body}</{name}>"


def oms(cd: str, name: str) -> str:
    return f'<OMS cd="{cd}" name="{name}"/>'


def var(name: str) -> str:
    return f'<OMV name="{name}"/>'


def integer(value: int) -> str:
    return f"<OMI>{value}</OMI>"


def app(head: str, *args: str) -> str:
    return tag("OMA", head + "".join(args))


def std(cd: str, name: str, *args: str) -> str:
    return app(oms(cd, name), *args)


def eq(left: str, right: str) -> str:
    return std("relation1", "eq", left, right)


def neq(left: str, right: str) -> str:
    return std("relation1", "neq", left, right)


def leq(left: str, right: str) -> str:
    return std("relation1", "leq", left, right)


def geq(left: str, right: str) -> str:
    return std("relation1", "geq", left, right)


def lt(left: str, right: str) -> str:
    return std("relation1", "lt", left, right)


def gt(left: str, right: str) -> str:
    return std("relation1", "gt", left, right)


def plus(*args: str) -> str:
    return std("arith1", "plus", *args)


def times(*args: str) -> str:
    return std("arith1", "times", *args)


def minus(left: str, right: str) -> str:
    return std("arith1", "minus", left, right)


def divide(left: str, right: str) -> str:
    return std("arith1", "divide", left, right)


def neg(value: str) -> str:
    return std("arith1", "unary_minus", value)


def power(base: str, exponent: int) -> str:
    return std("arith1", "power", base, integer(exponent))


def and_(*args: str) -> str:
    return std("logic1", "and", *args)


def or_(*args: str) -> str:
    return std("logic1", "or", *args)


def implies(premise: str, conclusion: str) -> str:
    return std("logic1", "implies", premise, conclusion)


def forall(names: tuple[str, ...], body: str) -> str:
    return tag("OMBIND", oms("quant1", "forall") + tag("OMBVAR", "".join(var(name) for name in names)) + body)


def real_forall(names: tuple[str, ...], body: str) -> str:
    memberships = tuple(std("set1", "in", var(name), oms("setname1", "R")) for name in names)
    premise = memberships[0] if len(memberships) == 1 else and_(*memberships)
    return forall(names, implies(premise, body))


def openmath(proposition: str) -> str:
    return f'<OMOBJ xmlns="{OPENMATH}" version="2.0">{proposition}</OMOBJ>'


def make(
    identifier: str,
    topic: str,
    difficulty: str,
    statement: str,
    proposition: str,
    strategy: str,
    steps: tuple[str, ...],
    witness: str,
) -> Card:
    if not 4 <= len(steps) <= 8:
        raise ValueError(f"{identifier}: sketch_steps must contain 4..8 entries")
    xml = openmath(proposition)
    validate_openmath_statement_semantics(xml, statement)
    canonical = canonicalize_retrieval_openmath_xml(xml)
    validate_canonical_retrieval_openmath_xml(canonical)
    return Card(
        id=identifier,
        profile="current_openmath_profile",
        domain="high_school_polynomials_rational_expressions_equations_inequalities",
        level="high_school",
        topic=topic,
        difficulty=difficulty,
        canonical_statement=statement,
        openmath_xml=xml,
        proof_strategy=strategy,
        sketch_steps=steps,
        lean_witness=witness,
    )


POLYNOMIAL_IDENTITY_STEPS = (
    "setup: Bind the real scalar variables and write both polynomial expressions without suppressing factors.",
    "expand: Expand the displayed powers and products in the real polynomial ring.",
    "collect: Collect like terms with the same monomial part.",
    "compare: Match the normalized left and right polynomial expressions.",
    "conclude: State the resulting real polynomial identity.",
)

POLYNOMIAL_ROOT_STEPS = (
    "setup: Bind the real unknown and move the equation to a zero-polynomial form.",
    "factor: Factor the polynomial, or complete the square, using the displayed coefficients.",
    "zero_product: Apply the zero-product rule or the zero-square rule over the reals.",
    "solve: Solve each resulting linear real equation.",
    "conclude: List exactly the permitted real root alternatives.",
)

POLYNOMIAL_INEQUALITY_STEPS = (
    "setup: Bind the real variable and record the stated interval or sign hypotheses.",
    "rewrite: Rewrite the expression as a square or a product of explicit real factors.",
    "sign: Determine the sign of every factor from the hypotheses.",
    "combine: Use square nonnegativity or the product sign rule.",
    "conclude: State the requested ordered-real inequality.",
)

RATIONAL_IDENTITY_STEPS = (
    "setup: Bind the real variables and record every displayed nonzero denominator premise.",
    "factor: Factor the numerator or place both sides over the common denominator.",
    "cancel: Cancel only factors certified nonzero by the premise.",
    "simplify: Normalize the resulting real rational expression.",
    "conclude: State the equality with its denominator domain retained.",
)

RATIONAL_EQUATION_STEPS = (
    "setup: Bind the real unknown and preserve the stated denominator exclusion.",
    "clear_denominators: Multiply by the explicitly nonzero denominator.",
    "solve: Reduce the equation to a linear polynomial equation and solve it.",
    "check_domain: Verify that the displayed solution is not an excluded denominator value.",
    "conclude: State the real solution implication.",
)

RATIONAL_INEQUALITY_STEPS = (
    "setup: Bind the real variable and translate the interval hypothesis into signs of numerator and denominator.",
    "numerator: Determine the strict sign of the numerator factor.",
    "denominator: Determine the strict sign of the denominator factor.",
    "quotient_sign: Apply the ordered-field quotient sign rule.",
    "conclude: State the resulting strict rational inequality.",
)


def cards() -> list[Card]:
    x, y, a, b = map(var, ("x", "y", "a", "b"))
    real_x = lambda body: real_forall(("x",), body)
    real_xy = lambda body: real_forall(("x", "y"), body)
    real_abx = lambda body: real_forall(("a", "b", "x"), body)

    current = [
        make(
            "poly_square_binomial_expansion",
            "polynomial_identities",
            "introductory",
            "For all real x and y, (x + y)^2 = x^2 + 2xy + y^2.",
            real_xy(eq(power(plus(x, y), 2), plus(power(x, 2), times(integer(2), x, y), power(y, 2)))),
            "Expand the square of a binomial and collect the cross term.",
            POLYNOMIAL_IDENTITY_STEPS,
            "example (x y : ℝ) : (x + y)^2 = x^2 + 2*x*y + y^2 := by ring",
        ),
        make(
            "poly_monic_quadratic_vieta_factorization",
            "polynomial_identities",
            "standard",
            "For all real a, b, and x, x^2 - (a+b)x + ab = (x-a)(x-b).",
            real_abx(eq(plus(minus(power(x, 2), times(plus(a, b), x)), times(a, b)), times(minus(x, a), minus(x, b)))),
            "Expand the root-form product to recover the monic quadratic coefficients.",
            POLYNOMIAL_IDENTITY_STEPS,
            "example (a b x : ℝ) : x^2 - (a+b)*x + a*b = (x-a)*(x-b) := by ring",
        ),
        make(
            "poly_complete_square_x2_minus_6x",
            "polynomial_identities",
            "standard",
            "For every real x, x^2 - 6x + 9 = (x - 3)^2.",
            real_x(eq(plus(minus(power(x, 2), times(integer(6), x)), integer(9)), power(minus(x, integer(3)), 2))),
            "Complete the square by adding and subtracting the square of half the linear coefficient.",
            POLYNOMIAL_IDENTITY_STEPS,
            "example (x : ℝ) : x^2 - 6*x + 9 = (x - 3)^2 := by ring",
        ),
        make(
            "poly_square_equals_nine_roots",
            "polynomial_equations",
            "introductory",
            "For every real x, if x^2 = 9 then x = 3 or x = -3.",
            real_x(implies(eq(power(x, 2), integer(9)), or_(eq(x, integer(3)), eq(x, integer(-3))))),
            "Factor x^2 - 9 and use the zero-product rule.",
            POLYNOMIAL_ROOT_STEPS,
            """example (x : ℝ) : x^2 = 9 → x = 3 ∨ x = -3 := by
  intro h
  have hfac : (x - 3) * (x + 3) = 0 := by nlinarith
  rcases mul_eq_zero.mp hfac with hleft | hright
  · left; linarith
  · right; linarith""",
        ),
        make(
            "poly_square_equals_sixteen_roots",
            "polynomial_equations",
            "introductory",
            "For every real x, if x^2 = 16 then x = 4 or x = -4.",
            real_x(implies(eq(power(x, 2), integer(16)), or_(eq(x, integer(4)), eq(x, integer(-4))))),
            "Factor x^2 - 16 and use the zero-product rule.",
            POLYNOMIAL_ROOT_STEPS,
            """example (x : ℝ) : x^2 = 16 → x = 4 ∨ x = -4 := by
  intro h
  have hfac : (x - 4) * (x + 4) = 0 := by nlinarith
  rcases mul_eq_zero.mp hfac with hleft | hright
  · left; linarith
  · right; linarith""",
        ),
        make(
            "poly_factored_linear_roots",
            "polynomial_equations",
            "introductory",
            "For every real x, if (x-1)(x+2) = 0 then x = 1 or x = -2.",
            real_x(implies(eq(times(minus(x, integer(1)), plus(x, integer(2))), integer(0)), or_(eq(x, integer(1)), eq(x, integer(-2))))),
            "Apply the zero-product rule directly to the displayed factors.",
            POLYNOMIAL_ROOT_STEPS,
            """example (x : ℝ) : (x - 1) * (x + 2) = 0 → x = 1 ∨ x = -2 := by
  intro h
  rcases mul_eq_zero.mp h with hleft | hright
  · left; linarith
  · right; linarith""",
        ),
        make(
            "poly_monic_quadratic_given_roots",
            "polynomial_equations",
            "advanced",
            "For all real a, b, and x, if x^2 - (a+b)x + ab = 0 then x = a or x = b.",
            real_abx(implies(eq(plus(minus(power(x, 2), times(plus(a, b), x)), times(a, b)), integer(0)), or_(eq(x, a), eq(x, b)))),
            "Rewrite the equation in factored root form and apply the zero-product rule.",
            POLYNOMIAL_ROOT_STEPS,
            """example (a b x : ℝ) : x^2 - (a+b)*x + a*b = 0 → x = a ∨ x = b := by
  intro h
  have hfac : (x - a) * (x - b) = 0 := by
    calc
      (x - a) * (x - b) = x^2 - (a+b)*x + a*b := by ring
      _ = 0 := h
  rcases mul_eq_zero.mp hfac with hleft | hright
  · left; linarith
  · right; linarith""",
        ),
        make(
            "poly_cubic_equals_eight_root",
            "polynomial_equations",
            "standard",
            "For every real x, if x^3 = 8 then x = 2.",
            real_x(implies(eq(power(x, 3), integer(8)), eq(x, integer(2)))),
            "Factor x^3 - 8 and show its quadratic cofactor is strictly positive.",
            POLYNOMIAL_ROOT_STEPS,
            """example (x : ℝ) : x^3 = 8 → x = 2 := by
  intro h
  have hfac : (x - 2) * (x^2 + 2*x + 4) = 0 := by
    calc
      (x - 2) * (x^2 + 2*x + 4) = x^3 - 8 := by ring
      _ = 0 := by nlinarith
  rcases mul_eq_zero.mp hfac with hleft | hright
  · linarith
  · have hpos : 0 < x^2 + 2*x + 4 := by nlinarith [sq_nonneg (x + 1)]
    linarith""",
        ),
        make(
            "poly_biquadratic_four_roots",
            "polynomial_equations",
            "advanced",
            "For every real x, if x^4 - 5x^2 + 4 = 0 then x = -2, x = -1, x = 1, or x = 2.",
            real_x(implies(eq(plus(minus(power(x, 4), times(integer(5), power(x, 2))), integer(4)), integer(0)), or_(eq(x, integer(-2)), eq(x, integer(-1)), eq(x, integer(1)), eq(x, integer(2))))),
            "Regard the equation as quadratic in x^2, factor, and then solve the two square equations.",
            POLYNOMIAL_ROOT_STEPS,
            """example (x : ℝ) : x^4 - 5*x^2 + 4 = 0 → x = -2 ∨ x = -1 ∨ x = 1 ∨ x = 2 := by
  intro h
  have hfac : (x^2 - 1) * (x^2 - 4) = 0 := by
    calc
      (x^2 - 1) * (x^2 - 4) = x^4 - 5*x^2 + 4 := by ring
      _ = 0 := h
  rcases mul_eq_zero.mp hfac with hfirst | hsecond
  · have hsq : (x - 1) * (x + 1) = 0 := by nlinarith
    rcases mul_eq_zero.mp hsq with hleft | hright
    · exact Or.inr (Or.inr (Or.inl (by linarith)))
    · exact Or.inr (Or.inl (by linarith))
  · have hsq : (x - 2) * (x + 2) = 0 := by nlinarith
    rcases mul_eq_zero.mp hsq with hleft | hright
    · exact Or.inr (Or.inr (Or.inr (by linarith)))
    · exact Or.inl (by linarith)""",
        ),
        make(
            "poly_square_nonnegative",
            "polynomial_inequalities",
            "introductory",
            "For every real x, x^2 is nonnegative.",
            real_x(geq(power(x, 2), integer(0))),
            "Use nonnegativity of a real square.",
            POLYNOMIAL_INEQUALITY_STEPS,
            "example (x : ℝ) : 0 ≤ x^2 := sq_nonneg x",
        ),
        make(
            "poly_square_linear_bound",
            "polynomial_inequalities",
            "standard",
            "For every real x, 2x is at most x^2 + 1.",
            real_x(leq(times(integer(2), x), plus(power(x, 2), integer(1)))),
            "Rewrite x^2 - 2x + 1 as the nonnegative square (x-1)^2.",
            POLYNOMIAL_INEQUALITY_STEPS,
            "example (x : ℝ) : 2*x ≤ x^2 + 1 := by nlinarith [sq_nonneg (x - 1)]",
        ),
        make(
            "poly_shifted_square_minimum",
            "polynomial_inequalities",
            "standard",
            "For every real x, (x-2)^2 + 3 is at least 3.",
            real_x(geq(plus(power(minus(x, integer(2)), 2), integer(3)), integer(3))),
            "Use nonnegativity of the translated square.",
            POLYNOMIAL_INEQUALITY_STEPS,
            "example (x : ℝ) : 3 ≤ (x - 2)^2 + 3 := by nlinarith [sq_nonneg (x - 2)]",
        ),
        make(
            "poly_square_upper_bound_interval",
            "polynomial_inequalities",
            "standard",
            "For every real x, if x^2 is at most 4 then -2 ≤ x and x ≤ 2.",
            real_x(implies(leq(power(x, 2), integer(4)), and_(leq(integer(-2), x), leq(x, integer(2))))),
            "Use contradiction with the square lower bounds outside [-2,2].",
            POLYNOMIAL_INEQUALITY_STEPS,
            """example (x : ℝ) : x^2 ≤ 4 → -2 ≤ x ∧ x ≤ 2 := by
  intro h
  constructor <;> nlinarith [sq_nonneg (x + 2), sq_nonneg (x - 2)]""",
        ),
        make(
            "poly_product_nonpositive_inside_interval",
            "polynomial_inequalities",
            "standard",
            "For every real x, if -3 ≤ x and x ≤ 1 then (x-1)(x+3) ≤ 0.",
            real_x(implies(and_(leq(integer(-3), x), leq(x, integer(1))), leq(times(minus(x, integer(1)), plus(x, integer(3))), integer(0)))),
            "The first factor is nonpositive and the second is nonnegative on the interval.",
            POLYNOMIAL_INEQUALITY_STEPS,
            """example (x : ℝ) : -3 ≤ x → x ≤ 1 → (x - 1) * (x + 3) ≤ 0 := by
  intro hleft hright
  exact mul_nonpos_of_nonpos_of_nonneg (by linarith) (by linarith)""",
        ),
        make(
            "poly_product_nonnegative_right_of_root",
            "polynomial_inequalities",
            "standard",
            "For every real x, if x ≥ 1 then (x-1)(x+3) is nonnegative.",
            real_x(implies(geq(x, integer(1)), geq(times(minus(x, integer(1)), plus(x, integer(3))), integer(0)))),
            "Both factors are nonnegative to the right of the larger root.",
            POLYNOMIAL_INEQUALITY_STEPS,
            """example (x : ℝ) : 1 ≤ x → 0 ≤ (x - 1) * (x + 3) := by
  intro h
  exact mul_nonneg (by linarith) (by linarith)""",
        ),
        make(
            "poly_product_nonnegative_left_of_root",
            "polynomial_inequalities",
            "standard",
            "For every real x, if x ≤ -3 then (x-1)(x+3) is nonnegative.",
            real_x(implies(leq(x, integer(-3)), geq(times(minus(x, integer(1)), plus(x, integer(3))), integer(0)))),
            "Both factors are nonpositive to the left of the smaller root.",
            POLYNOMIAL_INEQUALITY_STEPS,
            """example (x : ℝ) : x ≤ -3 → 0 ≤ (x - 1) * (x + 3) := by
  intro h
  exact mul_nonneg_of_nonpos_of_nonpos (by linarith) (by linarith)""",
        ),
        make(
            "poly_product_strictly_negative_between_roots",
            "polynomial_inequalities",
            "standard",
            "For every real x, if -3 < x and x < 1 then (x-1)(x+3) is negative.",
            real_x(implies(and_(lt(integer(-3), x), lt(x, integer(1))), lt(times(minus(x, integer(1)), plus(x, integer(3))), integer(0)))),
            "Between the roots the first factor is negative and the second is positive.",
            POLYNOMIAL_INEQUALITY_STEPS,
            """example (x : ℝ) : -3 < x → x < 1 → (x - 1) * (x + 3) < 0 := by
  intro hleft hright
  exact mul_neg_of_neg_of_pos (by linarith) (by linarith)""",
        ),
        make(
            "poly_cubic_strictly_increasing",
            "polynomial_inequalities",
            "advanced",
            "For all real x and y, if x < y then x^3 < y^3.",
            real_xy(implies(lt(x, y), lt(power(x, 3), power(y, 3)))),
            "Factor y^3-x^3; its linear factor and quadratic cofactor are positive when x<y.",
            POLYNOMIAL_INEQUALITY_STEPS,
            """example (x y : ℝ) : x < y → x^3 < y^3 := by
  intro h
  have hcofactor : 0 < y^2 + x*y + x^2 := by
    nlinarith [sq_nonneg (x + y), sq_nonneg (x - y)]
  have hprod : 0 < (y - x) * (y^2 + x*y + x^2) := mul_pos (by linarith) hcofactor
  nlinarith""",
        ),
        make(
            "rat_difference_squares_cancellation",
            "rational_expression_identities",
            "standard",
            "For every real x with x ≠ 1, (x^2-1)/(x-1) = x+1.",
            real_x(implies(neq(x, integer(1)), eq(divide(minus(power(x, 2), integer(1)), minus(x, integer(1))), plus(x, integer(1))))),
            "Factor the numerator as (x-1)(x+1) and cancel the certified nonzero factor.",
            RATIONAL_IDENTITY_STEPS,
            """example (x : ℝ) (hx : x ≠ 1) : (x^2 - 1) / (x - 1) = x + 1 := by
  field_simp
  ring""",
        ),
        make(
            "rat_difference_squares_cancellation_shifted",
            "rational_expression_identities",
            "standard",
            "For every real x with x ≠ 2, (x^2-4)/(x-2) = x+2.",
            real_x(implies(neq(x, integer(2)), eq(divide(minus(power(x, 2), integer(4)), minus(x, integer(2))), plus(x, integer(2))))),
            "Factor the numerator as (x-2)(x+2) and retain the denominator exclusion.",
            RATIONAL_IDENTITY_STEPS,
            """example (x : ℝ) (hx : x ≠ 2) : (x^2 - 4) / (x - 2) = x + 2 := by
  field_simp
  ring""",
        ),
        make(
            "rat_difference_squares_cancellation_negative_shift",
            "rational_expression_identities",
            "standard",
            "For every real x with x ≠ -3, (x^2-9)/(x+3) = x-3.",
            real_x(implies(neq(x, integer(-3)), eq(divide(minus(power(x, 2), integer(9)), plus(x, integer(3))), minus(x, integer(3))))),
            "Factor the numerator as (x-3)(x+3) and retain the denominator exclusion.",
            RATIONAL_IDENTITY_STEPS,
            """example (x : ℝ) (hx : x ≠ -3) : (x^2 - 9) / (x + 3) = x - 3 := by
  have hden : x + 3 ≠ 0 := by
    intro hzero
    apply hx
    linarith
  field_simp [hden] <;> ring""",
        ),
        make(
            "rat_sum_two_reciprocals",
            "rational_expression_identities",
            "standard",
            "For all real x and y with x ≠ 0 and y ≠ 0, 1/x + 1/y = (x+y)/(xy).",
            real_xy(implies(and_(neq(x, integer(0)), neq(y, integer(0))), eq(plus(divide(integer(1), x), divide(integer(1), y)), divide(plus(x, y), times(x, y))))),
            "Use the common denominator xy after recording both nonzero factors.",
            RATIONAL_IDENTITY_STEPS,
            """example (x y : ℝ) (hx : x ≠ 0) (hy : y ≠ 0) : 1/x + 1/y = (x+y)/(x*y) := by
  field_simp
  ring""",
        ),
        make(
            "rat_difference_two_reciprocals",
            "rational_expression_identities",
            "standard",
            "For all real x and y with x ≠ 0 and y ≠ 0, 1/x - 1/y = (y-x)/(xy).",
            real_xy(implies(and_(neq(x, integer(0)), neq(y, integer(0))), eq(minus(divide(integer(1), x), divide(integer(1), y)), divide(minus(y, x), times(x, y))))),
            "Use the common denominator xy and subtract the numerators in order.",
            RATIONAL_IDENTITY_STEPS,
            """example (x y : ℝ) (hx : x ≠ 0) (hy : y ≠ 0) : 1/x - 1/y = (y-x)/(x*y) := by
  field_simp [hx, hy] <;> ring""",
        ),
        make(
            "rat_adjacent_partial_fractions",
            "rational_expression_identities",
            "advanced",
            "For every real x with x ≠ -1 and x ≠ -2, (2x+3)/((x+1)(x+2)) = 1/(x+1) + 1/(x+2).",
            real_x(implies(and_(neq(x, integer(-1)), neq(x, integer(-2))), eq(divide(plus(times(integer(2), x), integer(3)), times(plus(x, integer(1)), plus(x, integer(2)))), plus(divide(integer(1), plus(x, integer(1))), divide(integer(1), plus(x, integer(2))))))),
            "Decompose the numerator using the two adjacent linear denominator factors.",
            RATIONAL_IDENTITY_STEPS,
            """example (x : ℝ) (h1 : x ≠ -1) (h2 : x ≠ -2) : (2*x + 3) / ((x+1)*(x+2)) = 1/(x+1) + 1/(x+2) := by
  have hden1 : x + 1 ≠ 0 := by
    intro hzero
    apply h1
    linarith
  have hden2 : x + 2 ≠ 0 := by
    intro hzero
    apply h2
    linarith
  field_simp [hden1, hden2] <;> ring""",
        ),
        make(
            "rat_linear_fraction_minus_one",
            "rational_expression_identities",
            "standard",
            "For every real x with x ≠ 1, (x+1)/(x-1) - 1 = 2/(x-1).",
            real_x(implies(neq(x, integer(1)), eq(minus(divide(plus(x, integer(1)), minus(x, integer(1))), integer(1)), divide(integer(2), minus(x, integer(1)))))),
            "Put the constant one over x-1 and subtract numerators.",
            RATIONAL_IDENTITY_STEPS,
            """example (x : ℝ) (hx : x ≠ 1) : (x+1)/(x-1) - 1 = 2/(x-1) := by
  field_simp
  ring""",
        ),
        make(
            "rat_square_over_square_plus_one_bound",
            "rational_expression_identities",
            "advanced",
            "For every real x, x^2/(x^2+1) is at most 1.",
            real_x(leq(divide(power(x, 2), plus(power(x, 2), integer(1))), integer(1))),
            "The denominator x^2+1 is positive; compare the numerator to it before division.",
            RATIONAL_INEQUALITY_STEPS,
            """example (x : ℝ) : x^2 / (x^2 + 1) ≤ 1 := by
  have hpos : 0 < x^2 + 1 := by nlinarith [sq_nonneg x]
  apply (div_le_iff₀ hpos).mpr
  nlinarith""",
        ),
        make(
            "rat_fraction_equals_two_solution",
            "rational_equations",
            "standard",
            "For every real x with x ≠ 2, if (x+1)/(x-2) = 2 then x = 5.",
            real_x(implies(and_(neq(x, integer(2)), eq(divide(plus(x, integer(1)), minus(x, integer(2))), integer(2))), eq(x, integer(5)))),
            "Clear the nonzero denominator x-2 and solve the resulting linear equation.",
            RATIONAL_EQUATION_STEPS,
            """example (x : ℝ) (hx : x ≠ 2) : (x+1)/(x-2) = 2 → x = 5 := by
  intro h
  have hden : x - 2 ≠ 0 := by
    intro hzero
    apply hx
    linarith
  field_simp [hden] at h
  linarith""",
        ),
        make(
            "rat_fraction_equals_half_solution",
            "rational_equations",
            "standard",
            "For every real x with x ≠ -1, if x/(x+1) = 1/2 then x = 1.",
            real_x(implies(and_(neq(x, integer(-1)), eq(divide(x, plus(x, integer(1))), divide(integer(1), integer(2)))), eq(x, integer(1)))),
            "Clear the nonzero denominator x+1 and solve the resulting linear equation.",
            RATIONAL_EQUATION_STEPS,
            """example (x : ℝ) (hx : x ≠ -1) : x/(x+1) = 1/2 → x = 1 := by
  intro h
  have hden : x + 1 ≠ 0 := by
    intro hzero
    apply hx
    linarith
  field_simp [hden] at h
  linarith""",
        ),
        make(
            "rat_reciprocal_equals_two_solution",
            "rational_equations",
            "standard",
            "For every real x with x ≠ 1, if 1/(x-1) = 2 then x = 3/2.",
            real_x(implies(and_(neq(x, integer(1)), eq(divide(integer(1), minus(x, integer(1))), integer(2))), eq(x, divide(integer(3), integer(2))))),
            "Clear the nonzero denominator x-1 and solve the resulting linear equation.",
            RATIONAL_EQUATION_STEPS,
            """example (x : ℝ) (hx : x ≠ 1) : 1/(x-1) = 2 → x = 3/2 := by
  intro h
  have hden : x - 1 ≠ 0 := by
    intro hzero
    apply hx
    linarith
  field_simp [hden] at h
  linarith""",
        ),
        make(
            "rat_three_over_shift_equals_one_solution",
            "rational_equations",
            "standard",
            "For every real x with x ≠ -2, if 3/(x+2) = 1 then x = 1.",
            real_x(implies(and_(neq(x, integer(-2)), eq(divide(integer(3), plus(x, integer(2))), integer(1))), eq(x, integer(1)))),
            "Clear the nonzero denominator x+2 and solve the resulting linear equation.",
            RATIONAL_EQUATION_STEPS,
            """example (x : ℝ) (hx : x ≠ -2) : 3/(x+2) = 1 → x = 1 := by
  intro h
  have hden : x + 2 ≠ 0 := by
    intro hzero
    apply hx
    linarith
  field_simp [hden] at h
  linarith""",
        ),
        make(
            "rat_product_fraction_equals_one_solution",
            "rational_equations",
            "advanced",
            "For every real x with x ≠ -1, if (x-2)/(x+1) = 1 then x = 3/2.",
            real_x(implies(and_(neq(x, integer(-1)), eq(divide(minus(x, integer(2)), plus(x, integer(1))), integer(1))), eq(x, divide(integer(3), integer(2))))),
            "Clear x+1, solve x-2=x+1, and retain the sole denominator exclusion.",
            RATIONAL_EQUATION_STEPS,
            """example (x : ℝ) (hx : x ≠ -1) : (x-2)/(x+1) = 1 → x = 3/2 := by
  intro h
  have hden : x + 1 ≠ 0 := by
    intro hzero
    apply hx
    linarith
  field_simp [hden] at h
  linarith""",
        ),
        make(
            "rat_two_over_shift_equals_four_solution",
            "rational_equations",
            "standard",
            "For every real x with x ≠ -1, if 2/(x+1) = 4 then x = -1/2.",
            real_x(implies(and_(neq(x, integer(-1)), eq(divide(integer(2), plus(x, integer(1))), integer(4))), eq(x, divide(integer(-1), integer(2))))),
            "Clear the nonzero denominator x+1 and solve the resulting linear equation.",
            RATIONAL_EQUATION_STEPS,
            """example (x : ℝ) (hx : x ≠ -1) : 2/(x+1) = 4 → x = -1/2 := by
  intro h
  have hden : x + 1 ≠ 0 := by
    intro hzero
    apply hx
    linarith
  field_simp [hden] at h
  linarith""",
        ),
        make(
            "rat_positive_right_of_two",
            "rational_inequalities",
            "standard",
            "For every real x, if x > 2 then (x-2)/(x+1) is positive.",
            real_x(implies(gt(x, integer(2)), gt(divide(minus(x, integer(2)), plus(x, integer(1))), integer(0)))),
            "Both numerator and denominator are positive when x>2.",
            RATIONAL_INEQUALITY_STEPS,
            """example (x : ℝ) : x > 2 → 0 < (x-2)/(x+1) := by
  intro h
  exact div_pos (by linarith) (by linarith)""",
        ),
        make(
            "rat_positive_left_of_negative_one",
            "rational_inequalities",
            "standard",
            "For every real x, if x < -1 then (x-2)/(x+1) is positive.",
            real_x(implies(lt(x, integer(-1)), gt(divide(minus(x, integer(2)), plus(x, integer(1))), integer(0)))),
            "Both numerator and denominator are negative when x<-1.",
            RATIONAL_INEQUALITY_STEPS,
            """example (x : ℝ) : x < -1 → 0 < (x-2)/(x+1) := by
  intro h
  exact div_pos_of_neg_of_neg (by linarith) (by linarith)""",
        ),
        make(
            "rat_negative_between_negative_one_and_two",
            "rational_inequalities",
            "standard",
            "For every real x, if -1 < x and x < 2 then (x-2)/(x+1) is negative.",
            real_x(implies(and_(lt(integer(-1), x), lt(x, integer(2))), lt(divide(minus(x, integer(2)), plus(x, integer(1))), integer(0)))),
            "The numerator is negative and the denominator is positive between the excluded value and the root.",
            RATIONAL_INEQUALITY_STEPS,
            """example (x : ℝ) : -1 < x → x < 2 → (x-2)/(x+1) < 0 := by
  intro hleft hright
  exact div_neg_of_neg_of_pos (by linarith) (by linarith)""",
        ),
        make(
            "rat_reciprocal_positive_right_of_negative_one",
            "rational_inequalities",
            "introductory",
            "For every real x, if x > -1 then 1/(x+1) is positive.",
            real_x(implies(gt(x, integer(-1)), gt(divide(integer(1), plus(x, integer(1))), integer(0)))),
            "The denominator x+1 is positive, so its positive reciprocal is positive.",
            RATIONAL_INEQUALITY_STEPS,
            """example (x : ℝ) : x > -1 → 0 < 1/(x+1) := by
  intro h
  exact one_div_pos.mpr (by linarith)""",
        ),
    ]

    identifiers = [card.id for card in current]
    if len(current) != 36 or len(identifiers) != len(set(identifiers)):
        raise RuntimeError("expected exactly 36 uniquely identified polynomial/rational cards")
    canonical = [canonicalize_retrieval_openmath_xml(card.openmath_xml) for card in current]
    if len(canonical) != len(set(canonical)):
        raise RuntimeError("candidate manifest contains duplicate canonical OpenMath")
    return current


def verify_lean(current: list[Card]) -> None:
    workspace = ROOT / "pals-agent" / "lean-workspace"
    if not workspace.is_dir():
        raise RuntimeError(f"pinned Lean workspace is missing: {workspace}")
    source = "import Mathlib\n\n" + "\n\n".join(card.lean_witness for card in current) + "\n"
    with tempfile.NamedTemporaryFile("w", suffix=".lean", dir=workspace, delete=False, encoding="utf-8") as handle:
        handle.write(source)
        witness_file = Path(handle.name)
    try:
        completed = subprocess.run(["lake", "env", "lean", str(witness_file)], cwd=workspace, text=True, capture_output=True, check=False)
    finally:
        witness_file.unlink(missing_ok=True)
    if completed.returncode:
        raise RuntimeError(f"Lean witness compilation failed:\n{completed.stdout}{completed.stderr}")


def verify_database(current: list[Card], expected_count: int) -> tuple[str, ...]:
    count = subprocess.run(
        ["docker", "compose", "exec", "-T", "postgres", "psql", "-U", "pals", "-d", "pals", "-Atc", "SELECT count(*) FROM public.dsp_drafts;"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if count.returncode:
        raise RuntimeError(f"could not query local Draft count:\n{count.stderr}")
    if int(count.stdout.strip()) != expected_count:
        raise RuntimeError(f"expected {expected_count} local Drafts, found {count.stdout.strip()}")
    rows = subprocess.run(
        ["docker", "compose", "exec", "-T", "postgres", "psql", "-U", "pals", "-d", "pals", "-At", "-F", "\t", "-c", "SELECT id, openmath_xml FROM public.dsp_drafts ORDER BY id;"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if rows.returncode:
        raise RuntimeError(f"could not query local Draft XML:\n{rows.stderr}")
    existing: dict[str, str] = {}
    for line in rows.stdout.splitlines():
        identifier, separator, xml = line.partition("\t")
        if not separator or not identifier or not xml:
            raise RuntimeError("local Draft XML query returned a malformed row")
        existing[identifier] = xml
    if len(existing) != expected_count:
        raise RuntimeError("local Draft XML query count did not match Draft count")
    duplicate_ids = sorted({card.id for card in current} & set(existing))
    if duplicate_ids:
        raise RuntimeError(f"candidate IDs already exist in local DB: {duplicate_ids}")

    strict_existing: dict[str, str] = {}
    fallback: list[str] = []
    for identifier, xml in existing.items():
        try:
            strict_existing[canonicalize_retrieval_openmath_xml(xml)] = identifier
        except MathXMLValidationError:
            fallback.append(identifier)
    candidate_by_strict = {canonicalize_retrieval_openmath_xml(card.openmath_xml): card.id for card in current}
    strict_duplicates = sorted(
        (candidate_by_strict[canonical], strict_existing[canonical])
        for canonical in candidate_by_strict.keys() & strict_existing.keys()
    )
    if strict_duplicates:
        raise RuntimeError(f"candidate canonical OpenMath duplicates strict local Drafts: {strict_duplicates}")
    legacy_existing = {canonicalize_openmath_xml(xml): identifier for identifier, xml in existing.items()}
    candidate_by_legacy = {canonicalize_openmath_xml(card.openmath_xml): card.id for card in current}
    legacy_duplicates = sorted(
        (candidate_by_legacy[canonical], legacy_existing[canonical])
        for canonical in candidate_by_legacy.keys() & legacy_existing.keys()
    )
    if legacy_duplicates:
        raise RuntimeError(f"candidate canonical OpenMath duplicates existing local Drafts: {legacy_duplicates}")
    return tuple(sorted(fallback))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify-lean", action="store_true", help="Compile all witnesses in the pinned Lean workspace.")
    parser.add_argument("--verify-db", action="store_true", help="Read-check local Draft ID/C14N only; never writes the DB.")
    parser.add_argument("--expected-db-count", type=int, default=DEFAULT_DB_COUNT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    current = cards()
    if args.verify_lean:
        verify_lean(current)
    fallback: tuple[str, ...] = ()
    if args.verify_db:
        fallback = verify_database(current, args.expected_db_count)
    topic_counts = {topic: sum(card.topic == topic for card in current) for topic in sorted({card.topic for card in current})}
    payload = {
        "schema_version": "pals.high-school-polynomial-rational-expansion-candidates.v1",
        "source": "PALS first-party authored, generic-OpenMath and Lean-verified candidate set",
        "current_profile_card_count": len(current),
        "topic_counts": topic_counts,
        "scope_note": "Every included card is an explicitly real scalar polynomial or rational-expression theorem. A rational card retains every denominator exclusion in its OpenMath premise; no native polynomial, rational-function, ordered-field, or solution-set object is bound by the generic profile.",
        "validation_contract": {
            "generic_openmath": "Every card runs statement-semantics validation, generic retrieval C14N, and exact-C14N validation while generated.",
            "lean": "Pass --verify-lean to compile one temporary Lean file containing all 36 witnesses in pals-agent/lean-workspace.",
            "local_db": "Pass --verify-db --expected-db-count 335 to read-check local Draft ID and strict/legacy C14N collisions. This command does not write the DB.",
        },
        "excluded_unsupported_abstractions": {
            "examples": ["quantified polynomial coefficients as a typed polynomial object", "a rational function as a bound function object", "a general solution set expressed as a typed subset of R", "division without a nonzero denominator premise"],
            "why": "Current generic OpenMath provides only coarse term/proposition/function sorts. The included cards stay in explicitly quantified real scalar arithmetic and preserve denominator hypotheses rather than pretending these richer objects are typed.",
        },
        "cards": [asdict(card) for card in current],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"cards={len(current)} generic_openmath=passed c14n_unique=passed")
    if args.verify_lean:
        print("lean=passed")
    if args.verify_db:
        print(f"local_db={args.expected_db_count}_rows id_and_c14n_collision_check=passed")
        if fallback:
            print("local_db_retrieval_c14n_fallback=" + ",".join(fallback))


if __name__ == "__main__":
    main()
