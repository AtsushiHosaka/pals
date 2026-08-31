#!/usr/bin/env python3
"""Build high-school equation/inequality and trigonometry Draft candidates.

This is an ephemeral authoring aid.  Both groups use the current OpenMath
whitelist, including transc1:sin/cos/tan.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path


OPENMATH = "http://www.openmath.org/OpenMath"


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


def v(name: str) -> str:
    return f'<OMV name="{name}"/>'


def i(value: int) -> str:
    return f"<OMI>{value}</OMI>"


def app(op: str, *args: str) -> str:
    return tag("OMA", op + "".join(args))


def std(cd: str, name: str, *args: str) -> str:
    return app(oms(cd, name), *args)


def plus(*args: str) -> str:
    return std("arith1", "plus", *args)


def times(*args: str) -> str:
    return std("arith1", "times", *args)


def minus(a: str, b: str) -> str:
    return std("arith1", "minus", a, b)


def neg(a: str) -> str:
    return std("arith1", "unary_minus", a)


def divide(a: str, b: str) -> str:
    return std("arith1", "divide", a, b)


def power(a: str, n: int) -> str:
    return std("arith1", "power", a, i(n))


def absolute(a: str) -> str:
    return std("arith1", "abs", a)


def sin(a: str) -> str:
    return std("transc1", "sin", a)


def cos(a: str) -> str:
    return std("transc1", "cos", a)


def tan(a: str) -> str:
    return std("transc1", "tan", a)


def eq(a: str, b: str) -> str:
    return std("relation1", "eq", a, b)


def neq(a: str, b: str) -> str:
    return std("relation1", "neq", a, b)


def leq(a: str, b: str) -> str:
    return std("relation1", "leq", a, b)


def lt(a: str, b: str) -> str:
    return std("relation1", "lt", a, b)


def and_(*args: str) -> str:
    return std("logic1", "and", *args)


def or_(*args: str) -> str:
    return std("logic1", "or", *args)


def implies(a: str, b: str) -> str:
    return std("logic1", "implies", a, b)


def iff(a: str, b: str) -> str:
    return std("logic1", "equivalent", a, b)


def not_(a: str) -> str:
    return std("logic1", "not", a)


def bind(kind: str, names: tuple[str, ...], body: str) -> str:
    return tag("OMBIND", oms("quant1", kind) + tag("OMBVAR", "".join(v(name) for name in names)) + body)


def forall_r(names: tuple[str, ...], body: str) -> str:
    memberships = tuple(std("set1", "in", v(name), oms("setname1", "R")) for name in names)
    premise = memberships[0] if len(memberships) == 1 else and_(*memberships)
    return bind("forall", names, implies(premise, body))


def exists_r(name: str, body: str) -> str:
    return bind("exists", (name,), and_(std("set1", "in", v(name), oms("setname1", "R")), body))


def xml(body: str) -> str:
    return f'<OMOBJ xmlns="{OPENMATH}" version="2.0">{body}</OMOBJ>'


def card(
    identifier: str,
    profile: str,
    topic: str,
    difficulty: str,
    statement: str,
    proposition: str,
    strategy: str,
    steps: tuple[str, ...],
    witness: str,
) -> Card:
    return Card(
        id=identifier,
        profile=profile,
        domain="high_school_mathematics",
        level="high_school",
        topic=topic,
        difficulty=difficulty,
        canonical_statement=statement,
        openmath_xml=xml(proposition),
        proof_strategy=strategy,
        sketch_steps=steps,
        lean_witness=witness,
    )


def current_profile_cards() -> list[Card]:
    x, y, z, w = map(v, ("x", "y", "z", "w"))
    p = "current_openmath_profile"
    return [
        card("hs_linear_equation_2x_plus_3_solution", p, "linear_equations", "introductory", "For every real x, 2*x + 3 = 11 if and only if x = 4.", forall_r(("x",), iff(eq(plus(times(i(2), x), i(3)), i(11)), eq(x, i(4)))), "Isolate x by subtracting 3 and dividing by the nonzero coefficient 2.", ("setup: Introduce the real unknown x.", "forward: Assume 2*x + 3 = 11.", "solve: Subtract 3 and divide by 2.", "reverse: Substitute x = 4 into the original equation."), "example (x : ℝ) : 2*x + 3 = 11 ↔ x = 4 := by constructor <;> intro h <;> nlinarith"),
        card("hs_linear_inequality_2x_plus_3_solution", p, "linear_inequalities", "introductory", "For every real x, 2*x + 3 ≤ 11 if and only if x ≤ 4.", forall_r(("x",), iff(leq(plus(times(i(2), x), i(3)), i(11)), leq(x, i(4)))), "Use order-preserving subtraction and division by the positive coefficient 2.", ("setup: Introduce real x.", "forward: Subtract 3 from both sides.", "solve: Divide by the positive number 2.", "reverse: Multiply x ≤ 4 by 2 and add 3."), "example (x : ℝ) : 2*x + 3 ≤ 11 ↔ x ≤ 4 := by constructor <;> intro h <;> nlinarith"),
        card("hs_reverse_linear_inequality_solution", p, "linear_inequalities", "standard", "For every real x, -2*x + 5 < 1 if and only if 2 < x.", forall_r(("x",), iff(lt(plus(times(neg(i(2)), x), i(5)), i(1)), lt(i(2), x))), "After isolating the negative multiple of x, divide by -2 and reverse the inequality.", ("setup: Introduce real x.", "forward: Subtract 5 to isolate -2*x.", "order: Divide by -2 and reverse the strict inequality.", "reverse: Apply the same reversible transformations backward."), "example (x : ℝ) : -2*x + 5 < 1 ↔ 2 < x := by constructor <;> intro h <;> nlinarith"),
        card("hs_linear_system_sum_difference_unique", p, "simultaneous_linear_equations", "standard", "For all real x and y, if x + y = 7 and x - y = 1, then x = 4 and y = 3.", forall_r(("x", "y"), implies(and_(eq(plus(x, y), i(7)), eq(minus(x, y), i(1))), and_(eq(x, i(4)), eq(y, i(3))))), "Add the two equations to find x, then substitute back to find y.", ("setup: Record x + y = 7 and x - y = 1.", "eliminate: Add the equations to obtain 2*x = 8.", "solve_x: Conclude x = 4.", "solve_y: Substitute x = 4 into x + y = 7.", "conclude: Obtain y = 3."), "example (x y : ℝ) (h1 : x + y = 7) (h2 : x - y = 1) : x = 4 ∧ y = 3 := by constructor <;> linarith"),
        card("hs_quadratic_factor_roots", p, "quadratic_equations", "standard", "For every real x, (x - 2)*(x + 1) = 0 if and only if x = 2 or x = -1.", forall_r(("x",), iff(eq(times(minus(x, i(2)), plus(x, i(1))), i(0)), or_(eq(x, i(2)), eq(x, neg(i(1)))))), "Factor the quadratic and use the zero-product property.", ("setup: View the left side as a product of two linear factors.", "forward: Apply the zero-product property.", "case_1: Solve x - 2 = 0.", "case_2: Solve x + 1 = 0.", "reverse: Substitute either root into one factor."), """example (x : ℝ) : (x - 2)*(x + 1) = 0 ↔ x = 2 ∨ x = -1 := by
  constructor
  · intro h
    rcases mul_eq_zero.mp h with h | h
    · left; linarith
    · right; linarith
  · rintro (h | h)
    · nlinarith
    · nlinarith"""),
        card("hs_square_eq_four_roots", p, "quadratic_equations", "standard", "For every real x, x^2 = 4 if and only if x = 2 or x = -2.", forall_r(("x",), iff(eq(power(x, 2), i(4)), or_(eq(x, i(2)), eq(x, neg(i(2)))))), "Rewrite x^2 - 4 as (x - 2)(x + 2), then apply the zero-product property.", ("setup: Move 4 to the left side.", "factor: Factor x^2 - 4 as (x - 2)(x + 2).", "forward: Apply the zero-product property.", "cases: Solve the two linear factor equations.", "reverse: Check each proposed root."), """example (x : ℝ) : x^2 = 4 ↔ x = 2 ∨ x = -2 := by
  constructor
  · intro h
    have hp : (x - 2) * (x + 2) = 0 := by nlinarith
    rcases mul_eq_zero.mp hp with hp | hp
    · left; linarith
    · right; linarith
  · rintro (h | h)
    · nlinarith
    · nlinarith"""),
        card("hs_shifted_square_zero_characterization", p, "quadratic_equations", "standard", "For every real x, (x - 3)^2 = 0 if and only if x = 3.", forall_r(("x",), iff(eq(power(minus(x, i(3)), 2), i(0)), eq(x, i(3)))), "A square is zero precisely when its base is zero.", ("setup: Recognize a squared linear expression.", "forward: Use that a zero square has zero base.", "solve: Rearrange x - 3 = 0.", "reverse: Substitute x = 3 and evaluate the square."), """example (x : ℝ) : (x - 3)^2 = 0 ↔ x = 3 := by
  constructor
  · intro h
    have hz : x - 3 = 0 := sq_eq_zero_iff.mp h
    linarith
  · intro h
    subst x
    norm_num"""),
        card("hs_shifted_quadratic_has_no_real_root", p, "quadratic_equations", "standard", "For every real x, x^2 - 6*x + 10 is not equal to 0.", forall_r(("x",), not_(eq(plus(minus(power(x, 2), times(i(6), x)), i(10)), i(0)))), "Complete the square: x^2 - 6*x + 10 = (x - 3)^2 + 1, which is positive.", ("setup: Assume the quadratic equals zero for contradiction.", "rewrite: Complete the square around x = 3.", "bound: Use (x - 3)^2 ≥ 0.", "contradict: Deduce the expression is at least 1.", "conclude: No real root exists."), "example (x : ℝ) : ¬ (x^2 - 6*x + 10 = 0) := by intro h; nlinarith [sq_nonneg (x - 3)]"),
        card("hs_sum_of_squares_zero_characterization", p, "quadratic_equations", "advanced", "For all real x and y, x^2 + y^2 = 0 if and only if x = 0 and y = 0.", forall_r(("x", "y"), iff(eq(plus(power(x, 2), power(y, 2)), i(0)), and_(eq(x, i(0)), eq(y, i(0))))), "Both squares are nonnegative; a sum of two nonnegative values can be zero only when each is zero.", ("setup: Assume x^2 + y^2 = 0.", "bound: Record x^2 ≥ 0 and y^2 ≥ 0.", "separate: Deduce each square equals zero.", "solve: Infer x = 0 and y = 0.", "reverse: Substitute the zero pair."), """example (x y : ℝ) : x^2 + y^2 = 0 ↔ x = 0 ∧ y = 0 := by
  constructor
  · intro h
    have hx2 : x^2 = 0 := by nlinarith [sq_nonneg x, sq_nonneg y]
    have hy2 : y^2 = 0 := by nlinarith [sq_nonneg x, sq_nonneg y]
    constructor
    · exact sq_eq_zero_iff.mp hx2
    · exact sq_eq_zero_iff.mp hy2
  · rintro ⟨hx, hy⟩
    simp [hx, hy]"""),
        card("hs_square_plus_one_strictly_positive", p, "quadratic_inequalities", "introductory", "For every real x, 0 < x^2 + 1.", forall_r(("x",), lt(i(0), plus(power(x, 2), i(1)))), "Use nonnegativity of x^2 and add the positive constant 1.", ("setup: Introduce real x.", "bound: Establish x^2 ≥ 0.", "add: Add 1 to the lower bound.", "conclude: The resulting value is strictly positive."), "example (x : ℝ) : 0 < x^2 + 1 := by nlinarith [sq_nonneg x]"),
        card("hs_quadratic_tangent_lower_bound", p, "quadratic_inequalities", "standard", "For every real x, 2*x - 1 ≤ x^2.", forall_r(("x",), leq(minus(times(i(2), x), i(1)), power(x, 2))), "Rearrange to x^2 - 2*x + 1 = (x - 1)^2 and use square nonnegativity.", ("setup: Move the linear expression to the right-hand side.", "rewrite: Identify x^2 - 2*x + 1 as (x - 1)^2.", "bound: Use (x - 1)^2 ≥ 0.", "conclude: Rearrange to the claimed inequality."), "example (x : ℝ) : 2*x - 1 ≤ x^2 := by nlinarith [sq_nonneg (x - 1)]"),
        card("hs_two_variable_quadratic_inequality", p, "quadratic_inequalities", "standard", "For all real x and y, 2*x*y ≤ x^2 + y^2.", forall_r(("x", "y"), leq(times(i(2), x, y), plus(power(x, 2), power(y, 2)))), "Rearrange the difference as the nonnegative square (x - y)^2.", ("setup: Compare x^2 + y^2 with 2*x*y.", "rewrite: Form x^2 - 2*x*y + y^2.", "identify: Recognize (x - y)^2.", "bound: Use square nonnegativity.", "conclude: Rearrange the inequality."), "example (x y : ℝ) : 2*x*y ≤ x^2 + y^2 := by nlinarith [sq_nonneg (x - y)]"),
        card("hs_amgm_two_nonnegative", p, "quadratic_inequalities", "advanced", "For all real x and y, if 0 ≤ x and 0 ≤ y, then x*y ≤ ((x + y)/2)^2.", forall_r(("x", "y"), implies(and_(leq(i(0), x), leq(i(0), y)), leq(times(x, y), power(divide(plus(x, y), i(2)), 2)))), "Expand the gap between the square of the arithmetic mean and the product as (x - y)^2 / 4.", ("setup: Assume x and y are nonnegative.", "target: Move x*y to the right-hand side.", "rewrite: Expand the mean square and multiply by 4.", "bound: Use (x - y)^2 ≥ 0.", "conclude: Divide the nonnegative gap by 4."), "example (x y : ℝ) (hx : 0 ≤ x) (hy : 0 ≤ y) : x*y ≤ ((x + y)/2)^2 := by nlinarith [sq_nonneg (x - y)]"),
        card("hs_cauchy_schwarz_two_dimensions", p, "quadratic_inequalities", "advanced", "For all real x, y, z, and w, (x*y + z*w)^2 ≤ (x^2 + z^2)*(y^2 + w^2).", forall_r(("x", "y", "z", "w"), leq(power(plus(times(x, y), times(z, w)), 2), times(plus(power(x, 2), power(z, 2)), plus(power(y, 2), power(w, 2))))), "Subtract the dot-product square and recognize the remaining expression as (x*w - y*z)^2.", ("setup: Expand both sides of the desired inequality.", "rearrange: Move the left side to the right.", "factor: Recognize (x*w - y*z)^2.", "bound: Use nonnegativity of that square.", "conclude: Restore the original inequality."), "example (x y z w : ℝ) : (x*y + z*w)^2 ≤ (x^2 + z^2)*(y^2 + w^2) := by nlinarith [sq_nonneg (x*w - y*z)]"),
        card("hs_abs_shifted_closed_interval", p, "absolute_value_inequalities", "standard", "For every real x, |x - 3| ≤ 2 if and only if 1 ≤ x and x ≤ 5.", forall_r(("x",), iff(leq(absolute(minus(x, i(3))), i(2)), and_(leq(i(1), x), leq(x, i(5))))), "Use the characterization |u| ≤ a iff -a ≤ u and u ≤ a, then shift the interval by 3.", ("setup: Set u = x - 3.", "forward: Expand |u| ≤ 2 into two linear bounds.", "shift: Add 3 to both bounds.", "reverse: Start from 1 ≤ x ≤ 5.", "conclude: Shift back and apply the absolute-value characterization."), """example (x : ℝ) : |x - 3| ≤ 2 ↔ 1 ≤ x ∧ x ≤ 5 := by
  constructor
  · intro h
    rcases (abs_le.mp h) with ⟨h1, h2⟩
    constructor <;> linarith
  · rintro ⟨h1, h2⟩
    apply abs_le.mpr
    constructor <;> linarith"""),
        card("hs_abs_open_interval", p, "absolute_value_inequalities", "standard", "For every real x, |x| < 3 if and only if -3 < x and x < 3.", forall_r(("x",), iff(lt(absolute(x), i(3)), and_(lt(neg(i(3)), x), lt(x, i(3))))), "Apply the strict absolute-value interval characterization directly.", ("setup: Introduce real x.", "forward: Expand |x| < 3 into lower and upper bounds.", "identify: Read the two inequalities as -3 < x < 3.", "reverse: Combine the two interval bounds.", "conclude: Apply the strict absolute-value characterization."), """example (x : ℝ) : |x| < 3 ↔ -3 < x ∧ x < 3 := by
  constructor
  · intro h
    exact abs_lt.mp h
  · intro h
    exact abs_lt.mpr h"""),
        card("hs_rational_half_equation_solution", p, "rational_equations", "advanced", "For every real x, if x is not equal to -1 and x/(x + 1) = 1/2, then x = 1.", forall_r(("x",), implies(and_(neq(x, neg(i(1))), eq(divide(x, plus(x, i(1))), divide(i(1), i(2)))), eq(x, i(1)))), "Check the denominator, clear it safely, and solve the resulting linear equation.", ("setup: Assume x ≠ -1 so x + 1 is nonzero.", "clear_denominator: Multiply x/(x + 1) = 1/2 by x + 1.", "simplify: Normalize the constant fraction 1/2.", "solve: Rearrange the resulting linear equation.", "conclude: Obtain x = 1."), """example (x : ℝ) (hx : x ≠ -1) (h : x / (x + 1) = 1 / 2) : x = 1 := by
  have hden : x + 1 ≠ 0 := by
    intro hz
    apply hx
    linarith
  rw [div_eq_iff hden] at h
  norm_num at h
  linarith"""),
        card("hs_square_root_existence_nonnegative", p, "quadratic_equations", "advanced", "For every real y, if 0 ≤ y, then there exists real x such that x^2 = y.", forall_r(("y",), implies(leq(i(0), y), exists_r("x", eq(power(v("x"), 2), y)))), "Choose the nonnegative square root of y and use the square-root theorem.", ("setup: Assume the parameter y is nonnegative.", "construct: Choose x = sqrt(y).", "domain: The chosen square root is real.", "verify: Use (sqrt(y))^2 = y for y ≥ 0.", "conclude: Package the witness and equation."), "example (y : ℝ) (hy : 0 ≤ y) : ∃ x : ℝ, x^2 = y := ⟨Real.sqrt y, Real.sq_sqrt hy⟩"),
        card("hs_product_nonnegative_from_nonnegative", p, "inequality_reasoning", "introductory", "For all real x and y, if 0 ≤ x and 0 ≤ y, then 0 ≤ x*y.", forall_r(("x", "y"), implies(and_(leq(i(0), x), leq(i(0), y)), leq(i(0), times(x, y)))), "Apply the product rule for two nonnegative real factors.", ("setup: Assume x ≥ 0 and y ≥ 0.", "sign: Identify both factors as nonnegative.", "apply_theorem: Apply nonnegativity of a product.", "conclude: Obtain 0 ≤ x*y."), "example (x y : ℝ) (hx : 0 ≤ x) (hy : 0 ≤ y) : 0 ≤ x*y := mul_nonneg hx hy"),
        card("hs_square_sub_one_nonnegative_right", p, "quadratic_inequalities", "standard", "For every real x, if 1 ≤ x, then 0 ≤ x^2 - 1.", forall_r(("x",), implies(leq(i(1), x), leq(i(0), minus(power(x, 2), i(1))))), "Factor x^2 - 1 as (x - 1)(x + 1); both factors are nonnegative when x ≥ 1.", ("setup: Assume x ≥ 1.", "factor: Rewrite x^2 - 1 as (x - 1)(x + 1).", "sign_1: Deduce x - 1 ≥ 0.", "sign_2: Deduce x + 1 ≥ 0.", "conclude: The product of these factors is nonnegative."), "example (x : ℝ) (hx : 1 ≤ x) : 0 ≤ x^2 - 1 := by have hp : 0 ≤ (x - 1) * (x + 1) := mul_nonneg (by linarith) (by linarith); nlinarith"),
    ]


def trigonometry_cards() -> list[Card]:
    x, y = v("x"), v("y")
    p = "current_openmath_profile"
    return [
        card("trig_sin_range_closed", p, "trigonometric_inequalities", "introductory", "For every real x, -1 ≤ sin(x) and sin(x) ≤ 1.", forall_r(("x",), and_(leq(neg(i(1)), sin(x)), leq(sin(x), i(1)))), "Use the global lower and upper bounds of the sine function.", ("setup: Introduce an arbitrary real angle x.", "lower_bound: Apply the lower bound for sine.", "upper_bound: Apply the upper bound for sine.", "conclude: Combine the two inequalities into the range interval."), "example (x : ℝ) : -1 ≤ Real.sin x ∧ Real.sin x ≤ 1 := ⟨Real.neg_one_le_sin x, Real.sin_le_one x⟩"),
        card("trig_cos_range_closed", p, "trigonometric_inequalities", "introductory", "For every real x, -1 ≤ cos(x) and cos(x) ≤ 1.", forall_r(("x",), and_(leq(neg(i(1)), cos(x)), leq(cos(x), i(1)))), "Use the global lower and upper bounds of the cosine function.", ("setup: Introduce an arbitrary real angle x.", "lower_bound: Apply the lower bound for cosine.", "upper_bound: Apply the upper bound for cosine.", "conclude: Combine the two inequalities into the range interval."), "example (x : ℝ) : -1 ≤ Real.cos x ∧ Real.cos x ≤ 1 := ⟨Real.neg_one_le_cos x, Real.cos_le_one x⟩"),
        card("trig_pythagorean_identity", p, "trigonometric_equations", "standard", "For every real x, sin(x)^2 + cos(x)^2 = 1.", forall_r(("x",), eq(plus(power(sin(x), 2), power(cos(x), 2)), i(1))), "Apply the Pythagorean identity for sine and cosine.", ("setup: Introduce the real angle x.", "theorem: Invoke the sine-cosine Pythagorean identity.", "normalize: Match the standard squared-expression form.", "conclude: The sum of squares is one."), "example (x : ℝ) : Real.sin x ^ 2 + Real.cos x ^ 2 = 1 := Real.sin_sq_add_cos_sq x"),
        card("trig_sin_cos_product_upper_half", p, "trigonometric_inequalities", "advanced", "For every real x, sin(x)*cos(x) ≤ 1/2.", forall_r(("x",), leq(times(sin(x), cos(x)), divide(i(1), i(2)))), "Combine sin^2(x) + cos^2(x) = 1 with nonnegativity of (sin(x) - cos(x))^2.", ("setup: Introduce the real angle x.", "identity: Record sin(x)^2 + cos(x)^2 = 1.", "square: Use (sin(x) - cos(x))^2 ≥ 0.", "expand: Convert the square bound into 2*sin(x)*cos(x) ≤ 1.", "conclude: Divide by 2."), "example (x : ℝ) : Real.sin x * Real.cos x ≤ 1 / 2 := by nlinarith [Real.sin_sq_add_cos_sq x, sq_nonneg (Real.sin x - Real.cos x)]"),
        card("trig_sin_cos_product_lower_half", p, "trigonometric_inequalities", "advanced", "For every real x, -1/2 ≤ sin(x)*cos(x).", forall_r(("x",), leq(neg(divide(i(1), i(2))), times(sin(x), cos(x)))), "Combine sin^2(x) + cos^2(x) = 1 with nonnegativity of (sin(x) + cos(x))^2.", ("setup: Introduce the real angle x.", "identity: Record sin(x)^2 + cos(x)^2 = 1.", "square: Use (sin(x) + cos(x))^2 ≥ 0.", "expand: Convert the square bound into 1 + 2*sin(x)*cos(x) ≥ 0.", "conclude: Rearrange to the lower bound."), "example (x : ℝ) : -(1 / 2 : ℝ) ≤ Real.sin x * Real.cos x := by nlinarith [Real.sin_sq_add_cos_sq x, sq_nonneg (Real.sin x + Real.cos x)]"),
        card("trig_sin_double_angle", p, "trigonometric_equations", "standard", "For every real x, sin(2*x) = 2*sin(x)*cos(x).", forall_r(("x",), eq(sin(times(i(2), x)), times(i(2), sin(x), cos(x)))), "Apply the double-angle formula for sine.", ("setup: Introduce the real angle x.", "recognize: Identify 2*x as the doubled angle.", "theorem: Apply the sine double-angle formula.", "conclude: Rewrite the right side as 2*sin(x)*cos(x)."), "example (x : ℝ) : Real.sin (2*x) = 2 * Real.sin x * Real.cos x := Real.sin_two_mul x"),
        card("trig_cos_double_angle", p, "trigonometric_equations", "standard", "For every real x, cos(2*x) = 2*cos(x)^2 - 1.", forall_r(("x",), eq(cos(times(i(2), x)), minus(times(i(2), power(cos(x), 2)), i(1)))), "Apply the cosine double-angle formula in the 2*cos^2(x) - 1 form.", ("setup: Introduce the real angle x.", "recognize: Identify 2*x as the doubled angle.", "theorem: Apply the cosine double-angle formula.", "normalize: Use the form 2*cos(x)^2 - 1.", "conclude: Obtain the desired equality."), "example (x : ℝ) : Real.cos (2*x) = 2 * Real.cos x ^ 2 - 1 := Real.cos_two_mul x"),
        card("trig_fourth_power_lower_bound", p, "trigonometric_inequalities", "advanced", "For every real x, 1/2 ≤ sin(x)^4 + cos(x)^4.", forall_r(("x",), leq(divide(i(1), i(2)), plus(power(sin(x), 4), power(cos(x), 4)))), "Use the Pythagorean identity and nonnegativity of (sin^2(x) - cos^2(x))^2.", ("setup: Introduce the real angle x.", "identity: Record sin(x)^2 + cos(x)^2 = 1.", "square: Use (sin(x)^2 - cos(x)^2)^2 ≥ 0.", "expand: Derive sin(x)^4 + cos(x)^4 ≥ 1/2.", "conclude: State the fourth-power lower bound."), "example (x : ℝ) : (1 / 2 : ℝ) ≤ Real.sin x ^ 4 + Real.cos x ^ 4 := by nlinarith [Real.sin_sq_add_cos_sq x, sq_nonneg (Real.sin x ^ 2 - Real.cos x ^ 2)]"),
        card("trig_tan_as_sine_over_cosine", p, "trigonometric_equations", "standard", "For every real x, tan(x) = sin(x)/cos(x).", forall_r(("x",), eq(tan(x), divide(sin(x), cos(x)))), "Unfold tangent through its standard quotient definition.", ("setup: Introduce the real angle x.", "definition: Expand tangent as sine divided by cosine.", "normalize: Keep the quotient in the same argument order.", "conclude: The two expressions are equal."), "example (x : ℝ) : Real.tan x = Real.sin x / Real.cos x := Real.tan_eq_sin_div_cos x"),
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    current = current_profile_cards()
    trig = trigonometry_cards()
    assert len(current) == 20
    assert len(trig) == 9
    assert len({card.id for card in current + trig}) == 29
    args.output.write_text(json.dumps({"schema_version": "pals.high-school-draft-candidates.v1", "equation_and_inequality_cards": [asdict(card) for card in current], "trigonometry_cards": [asdict(card) for card in trig]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
