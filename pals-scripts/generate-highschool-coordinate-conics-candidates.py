#!/usr/bin/env python3
"""Generate generic-OpenMath scalar-coordinate conic candidates.

This is an authoring-only tool.  It deliberately treats a point as its two
scalar coordinates in each *closed* exercise.  It does not add point, line,
vector, affine, or complex objects to generic OpenMath, and it never writes
to the local Draft database.
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

from pals_agent.openmath import (  # noqa: E402
    MathXMLValidationError,
    canonicalize_openmath_xml,
    canonicalize_retrieval_openmath_xml,
    validate_canonical_retrieval_openmath_xml,
    validate_openmath_statement_semantics,
)


OPENMATH = "http://www.openmath.org/OpenMath"
DEFAULT_DB_COUNT = 308


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


def app(operator: str, *arguments: str) -> str:
    return tag("OMA", operator + "".join(arguments))


def std(cd: str, name: str, *arguments: str) -> str:
    return app(oms(cd, name), *arguments)


def eq(left: str, right: str) -> str:
    return std("relation1", "eq", left, right)


def leq(left: str, right: str) -> str:
    return std("relation1", "leq", left, right)


def plus(*arguments: str) -> str:
    return std("arith1", "plus", *arguments)


def times(*arguments: str) -> str:
    return std("arith1", "times", *arguments)


def minus(left: str, right: str) -> str:
    return std("arith1", "minus", left, right)


def divide(left: str, right: str) -> str:
    return std("arith1", "divide", left, right)


def square(value: str) -> str:
    return std("arith1", "power", value, integer(2))


def and_(*arguments: str) -> str:
    return std("logic1", "and", *arguments)


def or_(*arguments: str) -> str:
    return std("logic1", "or", *arguments)


def implies(premise: str, conclusion: str) -> str:
    return std("logic1", "implies", premise, conclusion)


def falsehood() -> str:
    return oms("logic1", "false")


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
        domain="high_school_coordinate_geometry_conic_sections",
        level="high_school",
        topic=topic,
        difficulty=difficulty,
        canonical_statement=statement,
        openmath_xml=xml,
        proof_strategy=strategy,
        sketch_steps=steps,
        lean_witness=witness,
    )


ROOT_STEPS = (
    "setup: Record the two scalar coordinate equations and their real-domain premises.",
    "eliminate: Substitute the line or fixed-coordinate equation into the conic equation.",
    "factor: Rewrite the resulting univariate quadratic as a product or a zero square.",
    "cases: Apply the zero-product or zero-square rule to obtain every real root.",
    "recover: Substitute each root into the remaining scalar equation.",
    "conclude: State exactly the listed coordinate alternatives.",
)

TANGENT_STEPS = (
    "setup: Record the conic equation and the proposed tangent-line scalar equation.",
    "substitute: Eliminate the shared coordinate using the line equation.",
    "double_root: Reduce the contact equation to a square equal to zero.",
    "zero_square: Use that a real square vanishes only at zero.",
    "recover: Compute the remaining coordinate at the contact value.",
    "conclude: The scalar system has one real contact coordinate.",
)

LOCUS_STEPS = (
    "setup: Fix real scalar coordinates satisfying the displayed locus equation.",
    "expand: Expand the translated squares or difference of squares.",
    "cancel: Cancel the common scalar terms on both sides.",
    "rearrange: Put the remaining expression into a square, product, or inequality form.",
    "conclude: Read off the stated scalar locus consequence.",
)

DISCRIMINANT_STEPS = (
    "setup: Move the displayed quadratic equation to one side.",
    "classify: Identify the positive, zero, or negative discriminant case through its factorization or completed square.",
    "reduce: Express the equation as a product equal to zero, a zero square, or a positive square sum.",
    "roots: Apply the appropriate real-root rule.",
    "conclude: State the exact real-root alternative or contradiction.",
)


def cards() -> list[Card]:
    x, y = var("x"), var("y")
    xy = lambda body: real_forall(("x", "y"), body)
    x_only = lambda body: real_forall(("x",), body)

    parabola = eq(y, square(x))
    circle5 = eq(plus(square(x), square(y)), integer(5))
    ellipse = eq(plus(times(integer(9), square(x)), times(integer(4), square(y))), integer(36))
    hyperbola1 = eq(minus(square(x), square(y)), integer(1))

    current = [
        make(
            "conic_parabola_horizontal_secant_y_four",
            "parabola_intersections",
            "standard",
            "For all real x and y, if y = x^2 and y = 4, then (x, y) is either (2, 4) or (-2, 4).",
            xy(implies(and_(parabola, eq(y, integer(4))), or_(and_(eq(x, integer(2)), eq(y, integer(4))), and_(eq(x, integer(-2)), eq(y, integer(4)))))),
            "Substitute y = 4 into y = x^2 and factor x^2 - 4.",
            ROOT_STEPS,
            """example (x y : ℝ) : y = x^2 → y = 4 → (x = 2 ∧ y = 4) ∨ (x = -2 ∧ y = 4) := by
  intro hp hy
  have hfac : (x - 2) * (x + 2) = 0 := by nlinarith
  rcases mul_eq_zero.mp hfac with hx | hx
  · left; constructor <;> linarith
  · right; constructor <;> linarith""",
        ),
        make(
            "conic_parabola_tangent_at_one",
            "parabola_tangents",
            "advanced",
            "For all real x and y, if y = x^2 and y = 2x - 1, then x = 1 and y = 1.",
            xy(implies(and_(parabola, eq(y, minus(times(integer(2), x), integer(1)))), and_(eq(x, integer(1)), eq(y, integer(1))))),
            "Equate the parabola with y = 2x - 1 and recognize the double root (x - 1)^2 = 0.",
            TANGENT_STEPS,
            """example (x y : ℝ) : y = x^2 → y = 2*x - 1 → x = 1 ∧ y = 1 := by
  intro hp hl
  have hsq : (x - 1)^2 = 0 := by nlinarith
  have hx : x - 1 = 0 := sq_eq_zero_iff.mp hsq
  constructor <;> nlinarith""",
        ),
        make(
            "conic_parabola_line_secant_y_three_x",
            "parabola_intersections",
            "standard",
            "For all real x and y, if y = x^2 and y = 3x, then (x, y) is either (0, 0) or (3, 9).",
            xy(implies(and_(parabola, eq(y, times(integer(3), x))), or_(and_(eq(x, integer(0)), eq(y, integer(0))), and_(eq(x, integer(3)), eq(y, integer(9)))))),
            "Equate x^2 and 3x, factor x(x - 3), then recover y from y = 3x.",
            ROOT_STEPS,
            """example (x y : ℝ) : y = x^2 → y = 3*x → (x = 0 ∧ y = 0) ∨ (x = 3 ∧ y = 9) := by
  intro hp hl
  have hfac : x * (x - 3) = 0 := by nlinarith
  rcases mul_eq_zero.mp hfac with hx | hx
  · left; constructor <;> nlinarith
  · right; constructor <;> nlinarith""",
        ),
        make(
            "conic_parabola_horizontal_line_no_intersection",
            "parabola_intersections",
            "standard",
            "For all real x and y, the equations y = x^2 and y = -1 cannot both hold.",
            xy(implies(and_(parabola, eq(y, integer(-1))), falsehood())),
            "A square is nonnegative, so y = x^2 cannot equal -1 over the reals.",
            LOCUS_STEPS,
            """example (x y : ℝ) : y = x^2 → y = -1 → False := by
  intro hp hy
  nlinarith [sq_nonneg x]""",
        ),
        make(
            "conic_parabola_circle_two_intersections",
            "parabola_circle_intersections",
            "advanced",
            "For all real x and y, if y = x^2 and x^2 + y^2 = 2, then (x, y) is either (1, 1) or (-1, 1).",
            xy(implies(and_(parabola, eq(plus(square(x), square(y)), integer(2))), or_(and_(eq(x, integer(1)), eq(y, integer(1))), and_(eq(x, integer(-1)), eq(y, integer(1)))))),
            "Use y = x^2 to first solve y^2 + y = 2, then solve x^2 = 1.",
            ROOT_STEPS,
            """example (x y : ℝ) : y = x^2 → x^2 + y^2 = 2 → (x = 1 ∧ y = 1) ∨ (x = -1 ∧ y = 1) := by
  intro hp hc
  have hyfac : (y - 1) * (y + 2) = 0 := by nlinarith
  rcases mul_eq_zero.mp hyfac with hy | hy
  · have hy1 : y = 1 := by linarith
    have hxfac : (x - 1) * (x + 1) = 0 := by nlinarith
    rcases mul_eq_zero.mp hxfac with hx | hx
    · left; constructor <;> linarith
    · right; constructor <;> linarith
  · exfalso
    nlinarith [sq_nonneg x]""",
        ),
        make(
            "conic_parabola_vertex_lower_bound",
            "parabola_loci",
            "introductory",
            "For all real x and y, if y = x^2 + 2x + 1, then 0 ≤ y.",
            xy(implies(eq(y, plus(square(x), times(integer(2), x), integer(1))), leq(integer(0), y))),
            "Complete the square to y = (x + 1)^2 and use nonnegativity.",
            LOCUS_STEPS,
            """example (x y : ℝ) : y = x^2 + 2*x + 1 → 0 ≤ y := by
  intro h
  nlinarith [sq_nonneg (x + 1)]""",
        ),
        make(
            "conic_circle_line_secant_y_one",
            "circle_intersections",
            "standard",
            "For all real x and y, if x^2 + y^2 = 5 and y = 1, then (x, y) is either (2, 1) or (-2, 1).",
            xy(implies(and_(circle5, eq(y, integer(1))), or_(and_(eq(x, integer(2)), eq(y, integer(1))), and_(eq(x, integer(-2)), eq(y, integer(1)))))),
            "Substitute y = 1 into the circle equation and factor x^2 - 4.",
            ROOT_STEPS,
            """example (x y : ℝ) : x^2 + y^2 = 5 → y = 1 → (x = 2 ∧ y = 1) ∨ (x = -2 ∧ y = 1) := by
  intro hc hy
  have hfac : (x - 2) * (x + 2) = 0 := by nlinarith
  rcases mul_eq_zero.mp hfac with hx | hx
  · left; constructor <;> linarith
  · right; constructor <;> linarith""",
        ),
        make(
            "conic_circle_vertical_tangent_x_three",
            "circle_tangents",
            "advanced",
            "For all real x and y, if x^2 + y^2 = 9 and x = 3, then x = 3 and y = 0.",
            xy(implies(and_(eq(plus(square(x), square(y)), integer(9)), eq(x, integer(3))), and_(eq(x, integer(3)), eq(y, integer(0))))),
            "Substitute x = 3; the remaining equation is y^2 = 0, showing one contact coordinate.",
            TANGENT_STEPS,
            """example (x y : ℝ) : x^2 + y^2 = 9 → x = 3 → x = 3 ∧ y = 0 := by
  intro hc hx
  have hsq : y^2 = 0 := by nlinarith
  constructor
  · exact hx
  · exact sq_eq_zero_iff.mp hsq""",
        ),
        make(
            "conic_circle_translated_vertical_secant",
            "circle_intersections",
            "advanced",
            "For all real x and y, if (x - 1)^2 + (y + 2)^2 = 25 and x = 4, then (x, y) is either (4, 2) or (4, -6).",
            xy(implies(and_(eq(plus(square(minus(x, integer(1))), square(plus(y, integer(2)))), integer(25)), eq(x, integer(4))), or_(and_(eq(x, integer(4)), eq(y, integer(2))), and_(eq(x, integer(4)), eq(y, integer(-6)))))),
            "Fix x = 4, obtain (y + 2)^2 = 16, and factor the difference of squares.",
            ROOT_STEPS,
            """example (x y : ℝ) : (x - 1)^2 + (y + 2)^2 = 25 → x = 4 → (x = 4 ∧ y = 2) ∨ (x = 4 ∧ y = -6) := by
  intro hc hx
  have hfac : (y - 2) * (y + 6) = 0 := by nlinarith
  rcases mul_eq_zero.mp hfac with hy | hy
  · left; constructor <;> linarith
  · right; constructor <;> linarith""",
        ),
        make(
            "conic_circle_common_chord_scalar_y_one",
            "circle_intersections",
            "standard",
            "For all real x and y, if x^2 + y^2 = 5 and x^2 + (y - 2)^2 = 5, then y = 1.",
            xy(implies(and_(circle5, eq(plus(square(x), square(minus(y, integer(2)))), integer(5))), eq(y, integer(1)))),
            "Subtract the two circle equations so that x^2 cancels, leaving a linear equation in y.",
            LOCUS_STEPS,
            """example (x y : ℝ) : x^2 + y^2 = 5 → x^2 + (y - 2)^2 = 5 → y = 1 := by
  intro h1 h2
  nlinarith""",
        ),
        make(
            "conic_circle_equal_distance_locus_y_axis",
            "circle_loci",
            "standard",
            "For all real x and y, if (x - 1)^2 + y^2 = (x + 1)^2 + y^2, then x = 0.",
            xy(implies(eq(plus(square(minus(x, integer(1))), square(y)), plus(square(plus(x, integer(1))), square(y))), eq(x, integer(0)))),
            "Expand the two squared distances and cancel y^2 to obtain the perpendicular-bisector scalar equation x = 0.",
            LOCUS_STEPS,
            """example (x y : ℝ) : (x - 1)^2 + y^2 = (x + 1)^2 + y^2 → x = 0 := by
  intro h
  nlinarith""",
        ),
        make(
            "conic_circle_fixed_x_radius_locus",
            "circle_loci",
            "standard",
            "For all real x and y, if x^2 + y^2 = 25 and x = 3, then y = 4 or y = -4.",
            xy(implies(and_(eq(plus(square(x), square(y)), integer(25)), eq(x, integer(3))), or_(eq(y, integer(4)), eq(y, integer(-4))))),
            "Fix x = 3, reduce to y^2 = 16, and apply the difference-of-squares factorization.",
            ROOT_STEPS,
            """example (x y : ℝ) : x^2 + y^2 = 25 → x = 3 → y = 4 ∨ y = -4 := by
  intro hc hx
  have hfac : (y - 4) * (y + 4) = 0 := by nlinarith
  rcases mul_eq_zero.mp hfac with hy | hy
  · left; linarith
  · right; linarith""",
        ),
        make(
            "conic_ellipse_major_axis_intersections",
            "ellipse_intersections",
            "standard",
            "For all real x and y, if 9x^2 + 4y^2 = 36 and y = 0, then (x, y) is either (2, 0) or (-2, 0).",
            xy(implies(and_(ellipse, eq(y, integer(0))), or_(and_(eq(x, integer(2)), eq(y, integer(0))), and_(eq(x, integer(-2)), eq(y, integer(0)))))),
            "Set y = 0 in the scaled ellipse equation and solve x^2 = 4.",
            ROOT_STEPS,
            """example (x y : ℝ) : 9*x^2 + 4*y^2 = 36 → y = 0 → (x = 2 ∧ y = 0) ∨ (x = -2 ∧ y = 0) := by
  intro he hy
  have hfac : (x - 2) * (x + 2) = 0 := by nlinarith
  rcases mul_eq_zero.mp hfac with hx | hx
  · left; constructor <;> linarith
  · right; constructor <;> linarith""",
        ),
        make(
            "conic_ellipse_minor_axis_intersections",
            "ellipse_intersections",
            "standard",
            "For all real x and y, if 9x^2 + 4y^2 = 36 and x = 0, then (x, y) is either (0, 3) or (0, -3).",
            xy(implies(and_(ellipse, eq(x, integer(0))), or_(and_(eq(x, integer(0)), eq(y, integer(3))), and_(eq(x, integer(0)), eq(y, integer(-3)))))),
            "Set x = 0 in the scaled ellipse equation and solve y^2 = 9.",
            ROOT_STEPS,
            """example (x y : ℝ) : 9*x^2 + 4*y^2 = 36 → x = 0 → (x = 0 ∧ y = 3) ∨ (x = 0 ∧ y = -3) := by
  intro he hx
  have hfac : (y - 3) * (y + 3) = 0 := by nlinarith
  rcases mul_eq_zero.mp hfac with hy | hy
  · left; constructor <;> linarith
  · right; constructor <;> linarith""",
        ),
        make(
            "conic_ellipse_top_horizontal_tangent",
            "ellipse_tangents",
            "advanced",
            "For all real x and y, if 9x^2 + 4y^2 = 36 and y = 3, then x = 0 and y = 3.",
            xy(implies(and_(ellipse, eq(y, integer(3))), and_(eq(x, integer(0)), eq(y, integer(3))))),
            "Substitute y = 3 and reduce the contact equation to x^2 = 0.",
            TANGENT_STEPS,
            """example (x y : ℝ) : 9*x^2 + 4*y^2 = 36 → y = 3 → x = 0 ∧ y = 3 := by
  intro he hy
  have hsq : x^2 = 0 := by nlinarith
  constructor
  · exact sq_eq_zero_iff.mp hsq
  · exact hy""",
        ),
        make(
            "conic_ellipse_fractional_horizontal_secant",
            "ellipse_intersections",
            "advanced",
            "For all real x and y, if 9x^2 + 4y^2 = 36 and y = 12/5, then x = 6/5 or x = -6/5.",
            xy(implies(and_(ellipse, eq(y, divide(integer(12), integer(5)))), or_(eq(x, divide(integer(6), integer(5))), eq(x, divide(integer(-6), integer(5)))))),
            "Substitute y = 12/5 into the scaled ellipse equation and factor (5x - 6)(5x + 6).",
            ROOT_STEPS,
            """example (x y : ℝ) : 9*x^2 + 4*y^2 = 36 → y = (12 : ℝ)/5 → x = (6 : ℝ)/5 ∨ x = (-6 : ℝ)/5 := by
  intro he hy
  have hfac : (5*x - 6) * (5*x + 6) = 0 := by nlinarith
  rcases mul_eq_zero.mp hfac with hx | hx
  · left; linarith
  · right; linarith""",
        ),
        make(
            "conic_ellipse_coordinate_bounds",
            "ellipse_loci",
            "standard",
            "For all real x and y, if 9x^2 + 4y^2 = 36, then x^2 ≤ 4 and y^2 ≤ 9.",
            xy(implies(ellipse, and_(leq(square(x), integer(4)), leq(square(y), integer(9))))),
            "Use nonnegativity of the other squared coordinate term to bound each coordinate separately.",
            LOCUS_STEPS,
            """example (x y : ℝ) : 9*x^2 + 4*y^2 = 36 → x^2 ≤ 4 ∧ y^2 ≤ 9 := by
  intro he
  constructor <;> nlinarith [sq_nonneg x, sq_nonneg y]""",
        ),
        make(
            "conic_hyperbola_transverse_axis_intersections",
            "hyperbola_intersections",
            "standard",
            "For all real x and y, if x^2 - y^2 = 1 and y = 0, then (x, y) is either (1, 0) or (-1, 0).",
            xy(implies(and_(hyperbola1, eq(y, integer(0))), or_(and_(eq(x, integer(1)), eq(y, integer(0))), and_(eq(x, integer(-1)), eq(y, integer(0)))))),
            "Set y = 0 and factor x^2 - 1 into its two transverse-axis intersections.",
            ROOT_STEPS,
            """example (x y : ℝ) : x^2 - y^2 = 1 → y = 0 → (x = 1 ∧ y = 0) ∨ (x = -1 ∧ y = 0) := by
  intro hh hy
  have hfac : (x - 1) * (x + 1) = 0 := by nlinarith
  rcases mul_eq_zero.mp hfac with hx | hx
  · left; constructor <;> linarith
  · right; constructor <;> linarith""",
        ),
        make(
            "conic_hyperbola_vertical_tangent_at_one_zero",
            "hyperbola_tangents",
            "advanced",
            "For all real x and y, if x^2 - y^2 = 1 and x = 1, then x = 1 and y = 0.",
            xy(implies(and_(hyperbola1, eq(x, integer(1))), and_(eq(x, integer(1)), eq(y, integer(0))))),
            "Set x = 1; the remaining equation y^2 = 0 gives the single vertical contact coordinate.",
            TANGENT_STEPS,
            """example (x y : ℝ) : x^2 - y^2 = 1 → x = 1 → x = 1 ∧ y = 0 := by
  intro hh hx
  have hsq : y^2 = 0 := by nlinarith
  constructor
  · exact hx
  · exact sq_eq_zero_iff.mp hsq""",
        ),
        make(
            "conic_hyperbola_line_intersection",
            "hyperbola_intersections",
            "standard",
            "For all real x and y, if x^2 - y^2 = 3 and y = x - 1, then x = 2 and y = 1.",
            xy(implies(and_(eq(minus(square(x), square(y)), integer(3)), eq(y, minus(x, integer(1)))), and_(eq(x, integer(2)), eq(y, integer(1))))),
            "Substitute y = x - 1; the quadratic terms cancel and leave a linear equation for x.",
            LOCUS_STEPS,
            """example (x y : ℝ) : x^2 - y^2 = 3 → y = x - 1 → x = 2 ∧ y = 1 := by
  intro hh hl
  constructor <;> nlinarith""",
        ),
        make(
            "conic_hyperbola_no_y_axis_intersection",
            "hyperbola_intersections",
            "standard",
            "For all real x and y, the equations x^2 - y^2 = 1 and x = 0 cannot both hold.",
            xy(implies(and_(hyperbola1, eq(x, integer(0))), falsehood())),
            "Substituting x = 0 would require -y^2 = 1, impossible over the reals.",
            LOCUS_STEPS,
            """example (x y : ℝ) : x^2 - y^2 = 1 → x = 0 → False := by
  intro hh hx
  nlinarith [sq_nonneg y]""",
        ),
        make(
            "conic_hyperbola_asymptote_no_intersection",
            "hyperbola_asymptotes",
            "standard",
            "For all real x and y, the equations x^2 - y^2 = 1 and y = x cannot both hold.",
            xy(implies(and_(hyperbola1, eq(y, x)), falsehood())),
            "Substituting y = x cancels the difference of squares to 0 = 1.",
            LOCUS_STEPS,
            """example (x y : ℝ) : x^2 - y^2 = 1 → y = x → False := by
  intro hh hl
  subst y
  nlinarith""",
        ),
        make(
            "conic_hyperbola_reflection_scalar_symmetry",
            "hyperbola_loci",
            "introductory",
            "For all real x and y, if x^2 - y^2 = 1, then (-x)^2 - y^2 = 1.",
            xy(implies(hyperbola1, eq(minus(square(minus(integer(0), x)), square(y)), integer(1)))),
            "Square the reflected x-coordinate and observe that the scalar equation is unchanged.",
            LOCUS_STEPS,
            """example (x y : ℝ) : x^2 - y^2 = 1 → (-x)^2 - y^2 = 1 := by
  intro h
  convert h using 1 <;> ring""",
        ),
        make(
            "conic_quadratic_two_distinct_real_roots",
            "discriminants_and_roots",
            "standard",
            "For every real x, if x^2 - 5x + 6 = 0, then x = 2 or x = 3.",
            x_only(implies(eq(plus(minus(square(x), times(integer(5), x)), integer(6)), integer(0)), or_(eq(x, integer(2)), eq(x, integer(3))))),
            "Factor x^2 - 5x + 6 as (x - 2)(x - 3), the positive-discriminant case.",
            DISCRIMINANT_STEPS,
            """example (x : ℝ) : x^2 - 5*x + 6 = 0 → x = 2 ∨ x = 3 := by
  intro h
  have hfac : (x - 2) * (x - 3) = 0 := by nlinarith
  rcases mul_eq_zero.mp hfac with hx | hx
  · left; linarith
  · right; linarith""",
        ),
        make(
            "conic_quadratic_double_root",
            "discriminants_and_roots",
            "standard",
            "For every real x, if x^2 - 4x + 4 = 0, then x = 2.",
            x_only(implies(eq(plus(minus(square(x), times(integer(4), x)), integer(4)), integer(0)), eq(x, integer(2)))),
            "Complete the square to (x - 2)^2 = 0, the zero-discriminant case.",
            DISCRIMINANT_STEPS,
            """example (x : ℝ) : x^2 - 4*x + 4 = 0 → x = 2 := by
  intro h
  have hsq : (x - 2)^2 = 0 := by nlinarith
  exact by linarith [sq_eq_zero_iff.mp hsq]""",
        ),
        make(
            "conic_quadratic_no_real_root",
            "discriminants_and_roots",
            "standard",
            "For every real x, the equation x^2 + 2x + 2 = 0 cannot hold.",
            x_only(implies(eq(plus(square(x), times(integer(2), x), integer(2)), integer(0)), falsehood())),
            "Complete the square to (x + 1)^2 + 1 = 0, the negative-discriminant case.",
            DISCRIMINANT_STEPS,
            """example (x : ℝ) : x^2 + 2*x + 2 = 0 → False := by
  intro h
  nlinarith [sq_nonneg (x + 1)]""",
        ),
        make(
            "conic_difference_of_squares_locus_lines",
            "quadratic_loci",
            "advanced",
            "For all real x and y, if x^2 - y^2 = 0, then x = y or x = -y.",
            xy(implies(eq(minus(square(x), square(y)), integer(0)), or_(eq(x, y), eq(x, minus(integer(0), y))))),
            "Factor the degenerate quadratic locus as (x - y)(x + y) = 0.",
            DISCRIMINANT_STEPS,
            """example (x y : ℝ) : x^2 - y^2 = 0 → x = y ∨ x = -y := by
  intro h
  have hfac : (x - y) * (x + y) = 0 := by nlinarith
  rcases mul_eq_zero.mp hfac with hxy | hsum
  · left; linarith
  · right; linarith""",
        ),
    ]

    identifiers = [card.id for card in current]
    if len(current) != 27 or len(identifiers) != len(set(identifiers)):
        raise RuntimeError("expected exactly 27 uniquely identified conic cards")
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
    duplicate_ids = sorted(set(card.id for card in current) & set(existing))
    if duplicate_ids:
        raise RuntimeError(f"candidate IDs already exist in local DB: {duplicate_ids}")

    strict_existing: set[str] = set()
    fallback: list[str] = []
    for identifier, xml in existing.items():
        try:
            strict_existing.add(canonicalize_retrieval_openmath_xml(xml))
        except MathXMLValidationError:
            fallback.append(identifier)
    strict_candidates = {canonicalize_retrieval_openmath_xml(card.openmath_xml) for card in current}
    if strict_candidates & strict_existing:
        raise RuntimeError("candidate canonical OpenMath duplicates a strict current-profile local Draft")
    legacy_existing = {canonicalize_openmath_xml(xml) for xml in existing.values()}
    legacy_candidates = {canonicalize_openmath_xml(card.openmath_xml) for card in current}
    if legacy_candidates & legacy_existing:
        raise RuntimeError("candidate canonical OpenMath duplicates an existing local Draft")
    return tuple(sorted(fallback))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify-lean", action="store_true", help="Compile all witnesses in the pinned Lean workspace.")
    parser.add_argument("--verify-db", action="store_true", help="Read-check local Draft IDs/C14N only; never writes the DB.")
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
        "schema_version": "pals.high-school-coordinate-conics-candidates.v1",
        "source": "PALS first-party authored, generic-OpenMath and Lean-verified candidate set",
        "current_profile_card_count": len(current),
        "topic_counts": topic_counts,
        "scope_note": "Every included problem is a closed real scalar-coordinate equation. The manifest does not bind native points, lines, conics, vectors, affine transformations, or complex values. A tangent label means only that the displayed line/conic scalar system has one real contact coordinate; intersection and locus labels are likewise scalar-system claims, not geometric-object predicates.",
        "validation_contract": {
            "generic_openmath": "Every card runs statement-semantics validation, generic retrieval C14N, and exact-C14N validation while generated.",
            "lean": "Pass --verify-lean to compile one temporary Lean file containing all 27 witnesses in pals-agent/lean-workspace.",
            "local_db": "Pass --verify-db --expected-db-count 308 to read-check local Draft ID and strict/legacy C14N collisions. This command does not write the DB.",
        },
        "excluded_native_geometry": {
            "examples": ["a quantified point lies on a line", "the tangent object to a conic at a bound point", "affine reflection", "vector normal", "complex-plane conic parametrization"],
            "why": "The current generic profile has only coarse term/proposition/function sorts. These need a typed affine/geometry profile and are intentionally not simulated by unlinked generic variables.",
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
