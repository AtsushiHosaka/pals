#!/usr/bin/env python3
"""Generate current-profile coordinate-geometry Draft candidates.

These cards intentionally cover coordinate equations only.  They do not claim to
encode points, vectors, or complex numbers, which need additional typed symbols.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pals-agent"))

from pals_agent.openmath import validate_openmath_statement_semantics

OPENMATH = "http://www.openmath.org/OpenMath"


@dataclass(frozen=True)
class Card:
    id: str
    domain: str
    level: str
    difficulty: str
    profile: str
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


def standard(cd: str, name: str, *args: str) -> str:
    return app(oms(cd, name), *args)


def plus(*args: str) -> str:
    return standard("arith1", "plus", *args)


def times(*args: str) -> str:
    return standard("arith1", "times", *args)


def minus(left: str, right: str) -> str:
    return standard("arith1", "minus", left, right)


def divide(left: str, right: str) -> str:
    return standard("arith1", "divide", left, right)


def power(base: str, exponent: int) -> str:
    return standard("arith1", "power", base, integer(exponent))


def equal(left: str, right: str) -> str:
    return standard("relation1", "eq", left, right)


def implies(left: str, right: str) -> str:
    return standard("logic1", "implies", left, right)


def conjunction(*args: str) -> str:
    return standard("logic1", "and", *args)


def disjunction(*args: str) -> str:
    return standard("logic1", "or", *args)


def falsehood() -> str:
    return oms("logic1", "false")


def forall(names: tuple[str, ...], body: str) -> str:
    return tag("OMBIND", oms("quant1", "forall") + tag("OMBVAR", "".join(var(name) for name in names)) + body)


def typed_forall(names: tuple[str, ...], body: str) -> str:
    memberships = tuple(standard("set1", "in", var(name), oms("setname1", "R")) for name in names)
    premise = memberships[0] if len(memberships) == 1 else conjunction(*memberships)
    return forall(names, implies(premise, body))


def openmath(body: str) -> str:
    return f'<OMOBJ xmlns="{OPENMATH}" version="2.0">{body}</OMOBJ>'


def make(
    identifier: str,
    statement: str,
    proposition: str,
    strategy: str,
    steps: tuple[str, ...],
    witness: str,
    *,
    difficulty: str,
) -> Card:
    return Card(
        id=identifier,
        domain="coordinate_geometry_and_equations",
        level="high_school",
        difficulty=difficulty,
        profile="current_openmath_profile",
        canonical_statement=statement,
        openmath_xml=openmath(proposition),
        proof_strategy=strategy,
        sketch_steps=steps,
        lean_witness=witness,
    )


SYSTEM_STEPS = (
    "setup: Introduce the real coordinate variables and record the displayed equations.",
    "eliminate: Add, subtract, or substitute the equations to isolate one coordinate.",
    "solve: Determine the remaining coordinate from either original equation.",
    "verify: Substitute both values back into the defining equations.",
    "conclude: State the unique coordinate conclusion.",
)

SUBSTITUTION_STEPS = (
    "setup: Write the supplied coordinate parametrization.",
    "substitute: Replace x and y in the target coordinate equation.",
    "expand: Distribute scalar factors and collect the parameter terms.",
    "cancel: Cancel opposite parameter contributions when they occur.",
    "conclude: Obtain the required constant equation.",
)

DISTANCE_STEPS = (
    "setup: Form the horizontal and vertical coordinate differences.",
    "square: Square both coordinate differences.",
    "add: Sum the two squared contributions.",
    "simplify: Evaluate the resulting squared distance.",
    "conclude: State the coordinate distance-squared identity.",
)


def cards() -> list[Card]:
    x, y, t, m1, m2 = map(var, ("x", "y", "t", "m1", "m2"))
    return [
        make(
            "coord_line_intersection_sum_difference",
            "For all real x and y, if x + y = 5 and x - y = 1, then x = 3 and y = 2.",
            typed_forall(("x", "y"), implies(conjunction(equal(plus(x, y), integer(5)), equal(minus(x, y), integer(1))), conjunction(equal(x, integer(3)), equal(y, integer(2))))),
            "Add the two line equations to solve x, then substitute into either equation to solve y.",
            SYSTEM_STEPS,
            "example (x y : ℝ) : x + y = 5 → x - y = 1 → x = 3 ∧ y = 2 := by\n  intro h1 h2\n  constructor <;> linarith",
            difficulty="standard",
        ),
        make(
            "coord_line_intersection_two_affines",
            "For all real x and y, if x + 2y = 8 and 3x - y = 3, then x = 2 and y = 3.",
            typed_forall(("x", "y"), implies(conjunction(equal(plus(x, times(integer(2), y)), integer(8)), equal(minus(times(integer(3), x), y), integer(3))), conjunction(equal(x, integer(2)), equal(y, integer(3))))),
            "Eliminate y by combining a suitable multiple of the first equation with the second.",
            SYSTEM_STEPS,
            "example (x y : ℝ) : x + 2*y = 8 → 3*x - y = 3 → x = 2 ∧ y = 3 := by\n  intro h1 h2\n  constructor <;> linarith",
            difficulty="standard",
        ),
        make(
            "coord_parallel_lines_inconsistent_system",
            "For all real x and y, the equations x + 2y = 1 and 2x + 4y = 3 cannot both hold.",
            typed_forall(("x", "y"), implies(conjunction(equal(plus(x, times(integer(2), y)), integer(1)), equal(plus(times(integer(2), x), times(integer(4), y)), integer(3))), falsehood())),
            "Double the first equation and compare it with the second equation to obtain a contradiction.",
            SYSTEM_STEPS,
            "example (x y : ℝ) : x + 2*y = 1 → 2*x + 4*y = 3 → False := by\n  intro h1 h2\n  linarith",
            difficulty="standard",
        ),
        make(
            "coord_parametric_line_substitution_one",
            "For every real t, (1 + 2t) + 2(3 - t) = 7.",
            typed_forall(("t",), equal(plus(plus(integer(1), times(integer(2), t)), times(integer(2), minus(integer(3), t))), integer(7))),
            "Substitute the parametrized coordinates and cancel the t terms.",
            SUBSTITUTION_STEPS,
            "example (t : ℝ) : (1 + 2*t) + 2*(3 - t) = 7 := by ring",
            difficulty="standard",
        ),
        make(
            "coord_parametric_line_substitution_two",
            "For every real t, 2(-1 + 3t) - 3(4 + 2t) = -14.",
            typed_forall(("t",), equal(minus(times(integer(2), plus(integer(-1), times(integer(3), t))), times(integer(3), plus(integer(4), times(integer(2), t)))), integer(-14))),
            "Substitute the parametrized coordinates, expand, and cancel the t terms.",
            SUBSTITUTION_STEPS,
            "example (t : ℝ) : 2*(-1 + 3*t) - 3*(4 + 2*t) = -14 := by ring",
            difficulty="standard",
        ),
        make(
            "coord_origin_distance_three_four",
            "The coordinate pair (3, 4) has squared distance 25 from the origin.",
            equal(plus(power(minus(integer(3), integer(0)), 2), power(minus(integer(4), integer(0)), 2)), integer(25)),
            "Apply the squared-distance formula and evaluate 3^2 + 4^2.",
            DISTANCE_STEPS,
            "example : (3 : ℝ)^2 + 4^2 = 25 := by norm_num",
            difficulty="standard",
        ),
        make(
            "coord_squared_distance_between_two_points",
            "The coordinate pairs (2, -1) and (-1, 3) have squared distance 25.",
            equal(plus(power(minus(integer(2), integer(-1)), 2), power(minus(integer(-1), integer(3)), 2)), integer(25)),
            "Take the coordinate differences 3 and -4, square them, and add.",
            DISTANCE_STEPS,
            "example : ((2 : ℝ) - (-1))^2 + ((-1) - 3)^2 = 25 := by norm_num",
            difficulty="standard",
        ),
        make(
            "coord_midpoint_fixed_average",
            "The coordinatewise average of (1, 2) and (5, 8) is (3, 5).",
            conjunction(equal(divide(plus(integer(1), integer(5)), integer(2)), integer(3)), equal(divide(plus(integer(2), integer(8)), integer(2)), integer(5))),
            "Average the two x-coordinates and separately average the two y-coordinates.",
            DISTANCE_STEPS,
            "example : ((1 : ℝ) + 5) / 2 = 3 ∧ ((2 : ℝ) + 8) / 2 = 5 := by norm_num",
            difficulty="standard",
        ),
        make(
            "coord_internal_section_ratio_one_two",
            "The point that divides (1, 2) to (7, 8) internally in the ratio 1:2 has coordinate pair (3, 4).",
            conjunction(equal(divide(plus(times(integer(2), integer(1)), times(integer(1), integer(7))), integer(3)), integer(3)), equal(divide(plus(times(integer(2), integer(2)), times(integer(1), integer(8))), integer(3)), integer(4))),
            "Use the internal-section formula with weights 2 and 1, then simplify both coordinates.",
            DISTANCE_STEPS,
            "example : ((2 : ℝ)*1 + 1*7) / 3 = 3 ∧ ((2 : ℝ)*2 + 1*8) / 3 = 4 := by norm_num",
            difficulty="advanced",
        ),
        make(
            "coord_three_fixed_points_collinear",
            "The three displayed coordinate substitutions yield the constant equations 1 = 2·0 + 1, 5 = 2·2 + 1, and 7 = 2·3 + 1.",
            conjunction(equal(integer(1), plus(times(integer(2), integer(0)), integer(1))), equal(integer(5), plus(times(integer(2), integer(2)), integer(1))), equal(integer(7), plus(times(integer(2), integer(3)), integer(1)))),
            "Verify the same line equation independently at each coordinate pair.",
            SUBSTITUTION_STEPS,
            "example : (1 : ℝ) = 2*0 + 1 ∧ 5 = 2*2 + 1 ∧ 7 = 2*3 + 1 := by norm_num",
            difficulty="standard",
        ),
        make(
            "coord_line_circle_unit_intersections",
            "For all real x and y, if x + y = 1 and x^2 + y^2 = 1, then (x, y) is either (0, 1) or (1, 0).",
            typed_forall(("x", "y"), implies(conjunction(equal(plus(x, y), integer(1)), equal(plus(power(x, 2), power(y, 2)), integer(1))), disjunction(conjunction(equal(x, integer(0)), equal(y, integer(1))), conjunction(equal(x, integer(1)), equal(y, integer(0)))))),
            "Substitute y = 1 - x into the circle equation and factor the resulting quadratic.",
            (
                "setup: Record the line and unit-circle equations.",
                "substitute: Replace y by 1 - x using the line equation.",
                "factor: Reduce the circle equation to x(x - 1) = 0.",
                "cases: Split into x = 0 and x = 1.",
                "recover: Use x + y = 1 to obtain the corresponding y-coordinate.",
                "conclude: List the two intersection points.",
            ),
            "example (x y : ℝ) : x + y = 1 → x^2 + y^2 = 1 → (x = 0 ∧ y = 1) ∨ (x = 1 ∧ y = 0) := by\n  intro h1 h2\n  have hx : x * (x - 1) = 0 := by nlinarith\n  rcases mul_eq_zero.mp hx with hx | hx\n  · left; constructor <;> linarith\n  · right; constructor <;> linarith",
            difficulty="advanced",
        ),
        make(
            "coord_unit_circle_top_tangent",
            "For all real x and y, if x^2 + y^2 = 1 and y = 1, then x = 0.",
            typed_forall(("x", "y"), implies(conjunction(equal(plus(power(x, 2), power(y, 2)), integer(1)), equal(y, integer(1))), equal(x, integer(0)))),
            "Substitute y = 1 into the unit-circle equation and use that a square is zero only at zero.",
            (
                "setup: Record the unit-circle equation and y = 1.",
                "substitute: Replace y^2 by 1.",
                "reduce: Deduce x^2 = 0.",
                "zero_square: Use the zero-square characterization.",
                "conclude: Obtain x = 0.",
            ),
            "example (x y : ℝ) : x^2 + y^2 = 1 → y = 1 → x = 0 := by\n  intro h1 h2\n  have hx : x^2 = 0 := by nlinarith\n  exact sq_eq_zero_iff.mp hx",
            difficulty="advanced",
        ),
        make(
            "coord_sum_of_squares_origin",
            "For all real x and y, if x^2 + y^2 = 0, then x = 0 and y = 0.",
            typed_forall(("x", "y"), implies(equal(plus(power(x, 2), power(y, 2)), integer(0)), conjunction(equal(x, integer(0)), equal(y, integer(0))))),
            "Use nonnegativity of both squares to show that each square must vanish.",
            (
                "setup: Record the sum-of-squares equation.",
                "nonnegative: Establish x^2 ≥ 0 and y^2 ≥ 0.",
                "separate: Deduce x^2 = 0 and y^2 = 0.",
                "zero_square: Convert each zero square into a zero coordinate.",
                "conclude: Obtain the origin coordinates.",
            ),
            "example (x y : ℝ) : x^2 + y^2 = 0 → x = 0 ∧ y = 0 := by\n  intro h\n  constructor\n  · nlinarith [sq_nonneg y, sq_nonneg (x - 1)]\n  · nlinarith [sq_nonneg x, sq_nonneg (y - 1)]",
            difficulty="advanced",
        ),
        make(
            "coord_quarter_turn_preserves_squared_radius",
            "For all real x and y, the coordinate transformation (x, y) ↦ (-y, x) preserves squared radius.",
            typed_forall(("x", "y"), equal(plus(power(minus(integer(0), y), 2), power(x, 2)), plus(power(x, 2), power(y, 2)))),
            "Expand the square of -y and use commutativity of addition.",
            SUBSTITUTION_STEPS,
            "example (x y : ℝ) : (-y)^2 + x^2 = x^2 + y^2 := by ring",
            difficulty="standard",
        ),
        make(
            "coord_quarter_turn_orthogonal_components",
            "For all real x and y, the coordinate dot expression x(-y) + yx equals 0.",
            typed_forall(("x", "y"), equal(plus(times(x, minus(integer(0), y)), times(y, x)), integer(0))),
            "Expand x(-y), commute yx, and cancel the opposite terms.",
            SUBSTITUTION_STEPS,
            "example (x y : ℝ) : x*(-y) + y*x = 0 := by ring",
            difficulty="standard",
        ),
        make(
            "coord_reflection_y_axis_preserves_squared_radius",
            "For all real x and y, reflection (x, y) ↦ (-x, y) preserves squared radius.",
            typed_forall(("x", "y"), equal(plus(power(minus(integer(0), x), 2), power(y, 2)), plus(power(x, 2), power(y, 2)))),
            "Square the negated x-coordinate and observe that its square is unchanged.",
            SUBSTITUTION_STEPS,
            "example (x y : ℝ) : (-x)^2 + y^2 = x^2 + y^2 := by ring",
            difficulty="standard",
        ),
        make(
            "coord_perpendicular_slope_solution",
            "For all real m1 and m2, if m1*m2 = -1 and m1 = 2, then m2 = -1/2.",
            typed_forall(("m1", "m2"), implies(conjunction(equal(times(m1, m2), integer(-1)), equal(m1, integer(2))), equal(m2, divide(integer(-1), integer(2))))),
            "Substitute m1 = 2 into the perpendicular-slope product and solve the remaining linear equation.",
            SYSTEM_STEPS,
            "example (m1 m2 : ℝ) : m1*m2 = -1 → m1 = 2 → m2 = -(1:ℝ)/2 := by\n  intro h1 h2\n  nlinarith",
            difficulty="standard",
        ),
        make(
            "coord_circle_center_radius_substitution",
            "The displayed coordinate substitution gives (1 - 1)^2 + (-2 - 1)^2 = 9.",
            equal(plus(power(minus(integer(1), integer(1)), 2), power(minus(integer(-2), integer(1)), 2)), integer(9)),
            "Substitute the two coordinates into the translated-circle equation and simplify.",
            DISTANCE_STEPS,
            "example : ((1 : ℝ) - 1)^2 + ((-2) - 1)^2 = 9 := by norm_num",
            difficulty="standard",
        ),
        make(
            "coord_parabola_line_intersections",
            "For every real x, if x^2 = 2x, then x = 0 or x = 2.",
            typed_forall(("x",), implies(equal(power(x, 2), times(integer(2), x)), disjunction(equal(x, integer(0)), equal(x, integer(2))))),
            "Move all terms to one side, factor x(x - 2), and split into its two roots.",
            (
                "setup: Record the equality x^2 = 2x.",
                "rearrange: Move all terms to the left side.",
                "factor: Write the equation as x(x - 2) = 0.",
                "cases: Apply the zero-product rule.",
                "conclude: Obtain x = 0 or x = 2.",
            ),
            "example (x : ℝ) : x^2 = 2*x → x = 0 ∨ x = 2 := by\n  intro h\n  have hx : x * (x - 2) = 0 := by nlinarith\n  rcases mul_eq_zero.mp hx with hx | hx\n  · exact Or.inl hx\n  · right; linarith",
            difficulty="standard",
        ),
        make(
            "coord_triangle_centroid_fixed",
            "The coordinatewise average of (0, 0), (3, 0), and (0, 6) is (1, 2).",
            conjunction(equal(divide(plus(integer(0), integer(3), integer(0)), integer(3)), integer(1)), equal(divide(plus(integer(0), integer(0), integer(6)), integer(3)), integer(2))),
            "Average the three x-coordinates and separately average the three y-coordinates.",
            DISTANCE_STEPS,
            "example : ((0 : ℝ) + 3 + 0) / 3 = 1 ∧ ((0 : ℝ) + 0 + 6) / 3 = 2 := by norm_num",
            difficulty="standard",
        ),
    ]


def extension_backlog() -> list[dict[str, object]]:
    geometry = ("linalg2:vector", "linalg1:vector_selector", "pals2:point2", "pals2:line2", "pals2:circle2", "pals2:incident")
    vector = ("linalg2:vector", "linalg1:vector_selector", "linalg1:scalarproduct", "linalg1:determinant", "pals2:vector_add", "pals2:vector_scale")
    complex_plane = ("complex1:complex_cartesian", "complex1:conjugate", "complex1:real", "complex1:imaginary", "complex1:argument", "nums1:i", "pals2:complex_modulus")
    return [
        {"id": "geometry_line_through_two_points", "topic": "geometry", "canonical_statement": "Find the line through two distinct points.", "minimum_symbols": geometry, "why_current_profile_cannot_represent_it": "It has no point or line sort, nor an incidence predicate."},
        {"id": "geometry_circle_through_three_points", "topic": "geometry", "canonical_statement": "Determine the circle through three non-collinear points.", "minimum_symbols": geometry, "why_current_profile_cannot_represent_it": "Three points and their common circle cannot be represented as linked geometric objects."},
        {"id": "geometry_perpendicular_bisector_locus", "topic": "geometry", "canonical_statement": "Prove that points equidistant from two fixed points lie on their perpendicular bisector.", "minimum_symbols": geometry + ("pals2:distance_sq", "pals2:perpendicular", "pals2:midpoint"), "why_current_profile_cannot_represent_it": "The scalar profile lacks distance, midpoint, and perpendicular-line relations."},
        {"id": "geometry_reflection_in_line", "topic": "geometry", "canonical_statement": "Reflect a point in a non-axis-aligned line and verify distance preservation.", "minimum_symbols": geometry + ("pals2:reflect", "pals2:distance_sq"), "why_current_profile_cannot_represent_it": "A general reflection is not a scalar algebraic operation without a bound line and point objects."},
        {"id": "vector_component_addition", "topic": "vectors", "canonical_statement": "Add two planar vectors from their components.", "minimum_symbols": vector, "why_current_profile_cannot_represent_it": "Independent scalar equalities do not preserve that two coordinates denote a single vector."},
        {"id": "vector_scalar_multiple", "topic": "vectors", "canonical_statement": "Compute a scalar multiple of a planar vector and its endpoint.", "minimum_symbols": vector, "why_current_profile_cannot_represent_it": "The profile has no typed vector constructor or scalar-action operation."},
        {"id": "vector_dot_product_orthogonality", "topic": "vectors", "canonical_statement": "Show that two planar vectors are perpendicular exactly when their dot product is zero.", "minimum_symbols": vector, "why_current_profile_cannot_represent_it": "The dot product and vector-valued quantification are absent."},
        {"id": "vector_triangle_area_determinant", "topic": "vectors", "canonical_statement": "Compute a triangle area from the determinant of two side vectors.", "minimum_symbols": vector + ("arith1:abs", "arith1:divide"), "why_current_profile_cannot_represent_it": "A determinant must operate on typed vectors, not unrelated scalar coordinates."},
        {"id": "complex_cartesian_multiplication", "topic": "complex_plane", "canonical_statement": "Multiply two complex numbers given in Cartesian form.", "minimum_symbols": complex_plane, "why_current_profile_cannot_represent_it": "There is no complex constructor, real/imaginary projection, or complex sort."},
        {"id": "complex_conjugate_modulus_square", "topic": "complex_plane", "canonical_statement": "Show that z times its conjugate equals the squared modulus of z.", "minimum_symbols": complex_plane, "why_current_profile_cannot_represent_it": "Conjugation and modulus have no current semantic representation."},
        {"id": "complex_multiply_i_quarter_turn", "topic": "complex_plane", "canonical_statement": "Show that multiplication by i is a quarter-turn rotation in the complex plane.", "minimum_symbols": complex_plane, "why_current_profile_cannot_represent_it": "The imaginary unit, complex multiplication, and complex-plane interpretation are all absent."},
        {"id": "complex_argument_quadrant", "topic": "complex_plane", "canonical_statement": "Determine the argument of a nonzero Cartesian complex number in a specified quadrant.", "minimum_symbols": complex_plane + ("transc2:arctan",), "why_current_profile_cannot_represent_it": "The profile lacks complex argument and the two-argument arctangent needed to retain quadrant information."},
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    current = cards()
    for card in current:
        validate_openmath_statement_semantics(card.openmath_xml, card.canonical_statement)
    if len(current) != 20 or len({card.id for card in current}) != 20:
        raise RuntimeError("expected 20 unique current-profile cards")
    if not all(4 <= len(card.sketch_steps) <= 8 for card in current):
        raise RuntimeError("every current-profile card requires four to eight sketch steps")
    payload = {
        "schema_version": "pals.coordinate-geometry-candidates.v1",
        "source": "PALS first-party authored, Lean-verified candidate set",
        "current_profile_card_count": len(current),
        "scope_note": "Current-profile cards are rigorously scalar coordinate-equation problems, not a claim of native point/vector/complex semantics.",
        "extension_backlog_note": "Symbols in linalg1, linalg2, complex1, nums1, and transc2 are official OpenMath CDs. Every pals2:* name in this backlog is a proposed PALS semantic-profile extension, not an existing vocabulary item.",
        "cards": [asdict(card) for card in current],
        "extension_backlog": extension_backlog(),
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
