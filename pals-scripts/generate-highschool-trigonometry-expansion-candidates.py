"""Generate a safe generic-OpenMath expansion of high-school trigonometry.

The current retrieval profile has sin, cos, tan and ordinary real arithmetic,
but it deliberately has neither a pi constant nor typed partial functions.
This authoring-only generator therefore contains closed real identities and
inequalities only.  It never writes to the local Draft database.
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


def app(operator: str, *arguments: str) -> str:
    return tag("OMA", operator + "".join(arguments))


def std(cd: str, name: str, *arguments: str) -> str:
    return app(oms(cd, name), *arguments)


def plus(*arguments: str) -> str:
    return std("arith1", "plus", *arguments)


def times(*arguments: str) -> str:
    return std("arith1", "times", *arguments)


def minus(left: str, right: str) -> str:
    return std("arith1", "minus", left, right)


def divide(left: str, right: str) -> str:
    return std("arith1", "divide", left, right)


def neg(value: str) -> str:
    return std("arith1", "unary_minus", value)


def power(value: str, exponent: int) -> str:
    return std("arith1", "power", value, integer(exponent))


def sin(value: str) -> str:
    return std("transc1", "sin", value)


def cos(value: str) -> str:
    return std("transc1", "cos", value)


def tan(value: str) -> str:
    return std("transc1", "tan", value)


def eq(left: str, right: str) -> str:
    return std("relation1", "eq", left, right)


def neq(left: str, right: str) -> str:
    return std("relation1", "neq", left, right)


def leq(left: str, right: str) -> str:
    return std("relation1", "leq", left, right)


def implies(premise: str, conclusion: str) -> str:
    return std("logic1", "implies", premise, conclusion)


def forall(names: tuple[str, ...], body: str) -> str:
    return tag(
        "OMBIND",
        oms("quant1", "forall")
        + tag("OMBVAR", "".join(var(name) for name in names))
        + body,
    )


def real_forall(names: tuple[str, ...], body: str) -> str:
    memberships = tuple(
        std("set1", "in", var(name), oms("setname1", "R")) for name in names
    )
    premise = memberships[0] if len(memberships) == 1 else std("logic1", "and", *memberships)
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
    source = openmath(proposition)
    validate_openmath_statement_semantics(source, statement)
    canonical = canonicalize_retrieval_openmath_xml(source)
    validate_canonical_retrieval_openmath_xml(canonical)
    return Card(
        id=identifier,
        profile="current_openmath_profile",
        domain="high_school_trigonometry",
        level="high_school",
        topic=topic,
        difficulty=difficulty,
        canonical_statement=statement,
        openmath_xml=source,
        proof_strategy=strategy,
        sketch_steps=steps,
        lean_witness=witness,
    )


PARITY_STEPS = (
    "setup: Introduce an arbitrary real angle x.",
    "substitute: Replace the angle by its additive inverse.",
    "symmetry: Apply the parity theorem for the named trigonometric function.",
    "conclude: Normalize the resulting sign or unchanged value.",
)

ZERO_STEPS = (
    "setup: Evaluate the named trigonometric function at the real angle 0.",
    "definition: Use the zero-angle value theorem.",
    "normalize: Simplify the resulting real constant.",
    "conclude: State the exact zero-angle equality.",
)

ADDITION_STEPS = (
    "setup: Introduce arbitrary real angles x and y.",
    "decompose: Identify the displayed angle as a sum or difference.",
    "formula: Apply the corresponding addition or subtraction formula.",
    "normalize: Preserve the displayed order of the real products.",
    "conclude: Obtain the requested trigonometric identity.",
)

PRODUCT_SUM_STEPS = (
    "setup: Write the relevant addition and subtraction formulas at x and y.",
    "expand: Replace each trigonometric term by its sine or cosine expansion.",
    "cancel: Add or subtract the expansions to cancel the opposite terms.",
    "factor: Factor the common real product and the coefficient 2.",
    "conclude: State the product-to-sum identity.",
)

POWER_BOUND_STEPS = (
    "setup: Introduce an arbitrary real angle x.",
    "identity: Record sin(x)^2 + cos(x)^2 = 1.",
    "square: Use nonnegativity of the displayed square or product of squares.",
    "rearrange: Expand and isolate the requested trigonometric expression.",
    "conclude: Read off the claimed real inequality.",
)

TANGENT_DOMAIN_STEPS = (
    "setup: Introduce a real angle x and assume cos(x) is nonzero.",
    "definition: Replace tan(x) by sin(x)/cos(x).",
    "clear_denominator: Multiply only by the certified nonzero cosine factor.",
    "identity: Use sin(x)^2 + cos(x)^2 = 1 when needed.",
    "conclude: Simplify to the requested tangent equality.",
)


def cards() -> list[Card]:
    x, y = var("x"), var("y")
    rx = lambda body: real_forall(("x",), body)
    rxy = lambda body: real_forall(("x", "y"), body)
    sx, sy = sin(x), sin(y)
    cx, cy = cos(x), cos(y)
    tx = tan(x)
    sin_sq, cos_sq = power(sx, 2), power(cx, 2)
    product_sq = times(sin_sq, cos_sq)

    current = [
        make("trig_expand_sin_neg", "parity_and_zero_values", "introductory", "For every real x, sin(-x) = -sin(x).", rx(eq(sin(neg(x)), neg(sx))), "Use that sine is odd.", PARITY_STEPS, "example (x : ℝ) : Real.sin (-x) = -Real.sin x := Real.sin_neg x"),
        make("trig_expand_cos_neg", "parity_and_zero_values", "introductory", "For every real x, cos(-x) = cos(x).", rx(eq(cos(neg(x)), cx)), "Use that cosine is even.", PARITY_STEPS, "example (x : ℝ) : Real.cos (-x) = Real.cos x := Real.cos_neg x"),
        make("trig_expand_tan_neg", "parity_and_zero_values", "standard", "For every real x, tan(-x) = -tan(x).", rx(eq(tan(neg(x)), neg(tx))), "Use that tangent is odd.", PARITY_STEPS, "example (x : ℝ) : Real.tan (-x) = -Real.tan x := Real.tan_neg x"),
        make("trig_expand_sin_zero", "parity_and_zero_values", "introductory", "sin(0) = 0.", eq(sin(integer(0)), integer(0)), "Evaluate sine at zero.", ZERO_STEPS, "example : Real.sin 0 = 0 := Real.sin_zero"),
        make("trig_expand_cos_zero", "parity_and_zero_values", "introductory", "cos(0) = 1.", eq(cos(integer(0)), integer(1)), "Evaluate cosine at zero.", ZERO_STEPS, "example : Real.cos 0 = 1 := Real.cos_zero"),
        make("trig_expand_tan_zero", "parity_and_zero_values", "introductory", "tan(0) = 0.", eq(tan(integer(0)), integer(0)), "Evaluate tangent at zero.", ZERO_STEPS, "example : Real.tan 0 = 0 := Real.tan_zero"),
        make("trig_expand_sin_add", "addition_and_subtraction", "standard", "For all real x and y, sin(x + y) = sin(x)*cos(y) + cos(x)*sin(y).", rxy(eq(sin(plus(x, y)), plus(times(sx, cy), times(cx, sy)))), "Apply the sine addition formula.", ADDITION_STEPS, "example (x y : ℝ) : Real.sin (x + y) = Real.sin x * Real.cos y + Real.cos x * Real.sin y := Real.sin_add x y"),
        make("trig_expand_cos_add", "addition_and_subtraction", "standard", "For all real x and y, cos(x + y) = cos(x)*cos(y) - sin(x)*sin(y).", rxy(eq(cos(plus(x, y)), minus(times(cx, cy), times(sx, sy)))), "Apply the cosine addition formula.", ADDITION_STEPS, "example (x y : ℝ) : Real.cos (x + y) = Real.cos x * Real.cos y - Real.sin x * Real.sin y := Real.cos_add x y"),
        make("trig_expand_sin_sub", "addition_and_subtraction", "standard", "For all real x and y, sin(x - y) = sin(x)*cos(y) - cos(x)*sin(y).", rxy(eq(sin(minus(x, y)), minus(times(sx, cy), times(cx, sy)))), "Apply the sine subtraction formula.", ADDITION_STEPS, "example (x y : ℝ) : Real.sin (x - y) = Real.sin x * Real.cos y - Real.cos x * Real.sin y := Real.sin_sub x y"),
        make("trig_expand_cos_sub", "addition_and_subtraction", "standard", "For all real x and y, cos(x - y) = cos(x)*cos(y) + sin(x)*sin(y).", rxy(eq(cos(minus(x, y)), plus(times(cx, cy), times(sx, sy)))), "Apply the cosine subtraction formula.", ADDITION_STEPS, "example (x y : ℝ) : Real.cos (x - y) = Real.cos x * Real.cos y + Real.sin x * Real.sin y := Real.cos_sub x y"),
        make("trig_expand_sin_sum_product", "product_to_sum", "advanced", "For all real x and y, sin(x + y) + sin(x - y) = 2*sin(x)*cos(y).", rxy(eq(plus(sin(plus(x, y)), sin(minus(x, y))), times(integer(2), sx, cy))), "Add the sine addition and subtraction formulas.", PRODUCT_SUM_STEPS, "example (x y : ℝ) : Real.sin (x + y) + Real.sin (x - y) = 2 * Real.sin x * Real.cos y := by rw [Real.sin_add, Real.sin_sub]; ring"),
        make("trig_expand_sin_difference_product", "product_to_sum", "advanced", "For all real x and y, sin(x + y) - sin(x - y) = 2*cos(x)*sin(y).", rxy(eq(minus(sin(plus(x, y)), sin(minus(x, y))), times(integer(2), cx, sy))), "Subtract the sine subtraction formula from the sine addition formula.", PRODUCT_SUM_STEPS, "example (x y : ℝ) : Real.sin (x + y) - Real.sin (x - y) = 2 * Real.cos x * Real.sin y := by rw [Real.sin_add, Real.sin_sub]; ring"),
        make("trig_expand_cos_sum_product", "product_to_sum", "advanced", "For all real x and y, cos(x + y) + cos(x - y) = 2*cos(x)*cos(y).", rxy(eq(plus(cos(plus(x, y)), cos(minus(x, y))), times(integer(2), cx, cy))), "Add the cosine addition and subtraction formulas.", PRODUCT_SUM_STEPS, "example (x y : ℝ) : Real.cos (x + y) + Real.cos (x - y) = 2 * Real.cos x * Real.cos y := by rw [Real.cos_add, Real.cos_sub]; ring"),
        make("trig_expand_cos_difference_product", "product_to_sum", "advanced", "For all real x and y, cos(x - y) - cos(x + y) = 2*sin(x)*sin(y).", rxy(eq(minus(cos(minus(x, y)), cos(plus(x, y))), times(integer(2), sx, sy))), "Subtract the cosine addition formula from the cosine subtraction formula.", PRODUCT_SUM_STEPS, "example (x y : ℝ) : Real.cos (x - y) - Real.cos (x + y) = 2 * Real.sin x * Real.sin y := by rw [Real.cos_add, Real.cos_sub]; ring"),
        make("trig_expand_sin_triple_angle", "multiple_angle", "advanced", "For every real x, sin(3*x) = 3*sin(x) - 4*sin(x)^3.", rx(eq(sin(times(integer(3), x)), minus(times(integer(3), sx), times(integer(4), power(sx, 3))))), "Expand sin(2x + x), then use the double-angle and Pythagorean identities.", ADDITION_STEPS, """example (x : ℝ) : Real.sin (3*x) = 3 * Real.sin x - 4 * Real.sin x ^ 3 := by
  calc
    Real.sin (3*x) = Real.sin (2*x + x) := by congr 1 <;> ring
    _ = 3 * Real.sin x - 4 * Real.sin x ^ 3 := by
      rw [Real.sin_add, Real.sin_two_mul, Real.cos_two_mul]
      have h := Real.sin_sq_add_cos_sq x
      linear_combination 4 * Real.sin x * h"""),
        make("trig_expand_cos_triple_angle", "multiple_angle", "advanced", "For every real x, cos(3*x) = 4*cos(x)^3 - 3*cos(x).", rx(eq(cos(times(integer(3), x)), minus(times(integer(4), power(cx, 3)), times(integer(3), cx)))), "Expand cos(2x + x), then use the double-angle and Pythagorean identities.", ADDITION_STEPS, """example (x : ℝ) : Real.cos (3*x) = 4 * Real.cos x ^ 3 - 3 * Real.cos x := by
  calc
    Real.cos (3*x) = Real.cos (2*x + x) := by congr 1 <;> ring
    _ = 4 * Real.cos x ^ 3 - 3 * Real.cos x := by
      rw [Real.cos_add, Real.cos_two_mul, Real.sin_two_mul]
      have h := Real.sin_sq_add_cos_sq x
      linear_combination -2 * Real.cos x * h"""),
        make("trig_expand_sum_square_identity", "sine_cosine_algebra", "standard", "For every real x, (sin(x) + cos(x))^2 = 1 + 2*sin(x)*cos(x).", rx(eq(power(plus(sx, cx), 2), plus(integer(1), times(integer(2), sx, cx)))), "Expand the square and substitute the Pythagorean identity.", POWER_BOUND_STEPS, "example (x : ℝ) : (Real.sin x + Real.cos x)^2 = 1 + 2 * Real.sin x * Real.cos x := by nlinarith [Real.sin_sq_add_cos_sq x]"),
        make("trig_expand_difference_square_identity", "sine_cosine_algebra", "standard", "For every real x, (sin(x) - cos(x))^2 = 1 - 2*sin(x)*cos(x).", rx(eq(power(minus(sx, cx), 2), minus(integer(1), times(integer(2), sx, cx)))), "Expand the square and substitute the Pythagorean identity.", POWER_BOUND_STEPS, "example (x : ℝ) : (Real.sin x - Real.cos x)^2 = 1 - 2 * Real.sin x * Real.cos x := by nlinarith [Real.sin_sq_add_cos_sq x]"),
        make("trig_expand_sin_square_le_one", "sine_cosine_algebra", "introductory", "For every real x, sin(x)^2 ≤ 1.", rx(leq(sin_sq, integer(1))), "Use the standard squared-sine bound.", POWER_BOUND_STEPS, "example (x : ℝ) : Real.sin x ^ 2 ≤ 1 := Real.sin_sq_le_one x"),
        make("trig_expand_cos_square_le_one", "sine_cosine_algebra", "introductory", "For every real x, cos(x)^2 ≤ 1.", rx(leq(cos_sq, integer(1))), "Use the standard squared-cosine bound.", POWER_BOUND_STEPS, "example (x : ℝ) : Real.cos x ^ 2 ≤ 1 := Real.cos_sq_le_one x"),
        make("trig_expand_square_product_le_quarter", "sine_cosine_algebra", "advanced", "For every real x, sin(x)^2*cos(x)^2 ≤ 1/4.", rx(leq(product_sq, divide(integer(1), integer(4)))), "Apply nonnegativity of (sin(x)^2 - cos(x)^2)^2 together with the Pythagorean identity.", POWER_BOUND_STEPS, "example (x : ℝ) : Real.sin x ^ 2 * Real.cos x ^ 2 ≤ 1 / 4 := by nlinarith [Real.sin_sq_add_cos_sq x, sq_nonneg (Real.sin x ^ 2 - Real.cos x ^ 2)]"),
        make("trig_expand_fourth_power_upper_bound", "sine_cosine_algebra", "advanced", "For every real x, sin(x)^4 + cos(x)^4 ≤ 1.", rx(leq(plus(power(sx, 4), power(cx, 4)), integer(1))), "Expand the square of sin(x)^2 + cos(x)^2 and discard the nonnegative cross term.", POWER_BOUND_STEPS, "example (x : ℝ) : Real.sin x ^ 4 + Real.cos x ^ 4 ≤ 1 := by nlinarith [sq_nonneg (Real.sin x), sq_nonneg (Real.cos x), mul_nonneg (sq_nonneg (Real.sin x)) (sq_nonneg (Real.cos x)), Real.sin_sq_add_cos_sq x]"),
        make("trig_expand_fourth_power_product_identity", "sine_cosine_algebra", "advanced", "For every real x, sin(x)^4 + cos(x)^4 = 1 - 2*sin(x)^2*cos(x)^2.", rx(eq(plus(power(sx, 4), power(cx, 4)), minus(integer(1), times(integer(2), sin_sq, cos_sq)))), "Square the Pythagorean identity and rearrange its cross term.", POWER_BOUND_STEPS, "example (x : ℝ) : Real.sin x ^ 4 + Real.cos x ^ 4 = 1 - 2 * Real.sin x ^ 2 * Real.cos x ^ 2 := by have h := Real.sin_sq_add_cos_sq x; nlinarith [show (Real.sin x ^ 2 + Real.cos x ^ 2)^2 = 1 from by rw [h]; norm_num]"),
        make("trig_expand_square_difference_product_identity", "sine_cosine_algebra", "advanced", "For every real x, (sin(x)^2 - cos(x)^2)^2 = 1 - 4*sin(x)^2*cos(x)^2.", rx(eq(power(minus(sin_sq, cos_sq), 2), minus(integer(1), times(integer(4), sin_sq, cos_sq)))), "Expand the square difference and square the Pythagorean identity.", POWER_BOUND_STEPS, "example (x : ℝ) : (Real.sin x ^ 2 - Real.cos x ^ 2)^2 = 1 - 4 * Real.sin x ^ 2 * Real.cos x ^ 2 := by have h := Real.sin_sq_add_cos_sq x; nlinarith [show (Real.sin x ^ 2 + Real.cos x ^ 2)^2 = 1 from by rw [h]; norm_num]"),
        make("trig_expand_sum_square_le_two", "sine_cosine_algebra", "standard", "For every real x, (sin(x) + cos(x))^2 ≤ 2.", rx(leq(power(plus(sx, cx), 2), integer(2))), "Use nonnegativity of (sin(x) - cos(x))^2 with the Pythagorean identity.", POWER_BOUND_STEPS, "example (x : ℝ) : (Real.sin x + Real.cos x)^2 ≤ 2 := by nlinarith [Real.sin_sq_add_cos_sq x, sq_nonneg (Real.sin x - Real.cos x)]"),
        make("trig_expand_difference_square_le_two", "sine_cosine_algebra", "standard", "For every real x, (sin(x) - cos(x))^2 ≤ 2.", rx(leq(power(minus(sx, cx), 2), integer(2))), "Use nonnegativity of (sin(x) + cos(x))^2 with the Pythagorean identity.", POWER_BOUND_STEPS, "example (x : ℝ) : (Real.sin x - Real.cos x)^2 ≤ 2 := by nlinarith [Real.sin_sq_add_cos_sq x, sq_nonneg (Real.sin x + Real.cos x)]"),
        make("trig_expand_square_product_nonnegative", "sine_cosine_algebra", "standard", "For every real x, 0 ≤ sin(x)^2*cos(x)^2.", rx(leq(integer(0), product_sq)), "A product of two squares is nonnegative.", POWER_BOUND_STEPS, "example (x : ℝ) : 0 ≤ Real.sin x ^ 2 * Real.cos x ^ 2 := mul_nonneg (sq_nonneg _) (sq_nonneg _)"),
        make("trig_expand_tan_times_cos", "tangent_with_nonzero_denominator", "standard", "For every real x, if cos(x) is not equal to 0, then tan(x)*cos(x) = sin(x).", rx(implies(neq(cx, integer(0)), eq(times(tx, cx), sx))), "Use the quotient definition of tangent and cancel the certified nonzero cosine.", TANGENT_DOMAIN_STEPS, "example (x : ℝ) (h : Real.cos x ≠ 0) : Real.tan x * Real.cos x = Real.sin x := by rw [Real.tan_eq_sin_div_cos]; field_simp"),
        make("trig_expand_tan_square_plus_one", "tangent_with_nonzero_denominator", "advanced", "For every real x, if cos(x) is not equal to 0, then tan(x)^2 + 1 = 1/cos(x)^2.", rx(implies(neq(cx, integer(0)), eq(plus(power(tx, 2), integer(1)), divide(integer(1), power(cx, 2))))), "Replace tangent by a quotient, clear the nonzero denominator, and use the Pythagorean identity.", TANGENT_DOMAIN_STEPS, "example (x : ℝ) (h : Real.cos x ≠ 0) : Real.tan x ^ 2 + 1 = 1 / Real.cos x ^ 2 := by rw [Real.tan_eq_sin_div_cos, div_pow]; field_simp; nlinarith [Real.sin_sq_add_cos_sq x]"),
        make("trig_expand_tan_square_times_cos_square", "tangent_with_nonzero_denominator", "advanced", "For every real x, if cos(x) is not equal to 0, then tan(x)^2*cos(x)^2 = sin(x)^2.", rx(implies(neq(cx, integer(0)), eq(times(power(tx, 2), power(cx, 2)), sin_sq))), "Replace tangent by sin(x)/cos(x), then cancel the nonzero squared cosine.", TANGENT_DOMAIN_STEPS, "example (x : ℝ) (h : Real.cos x ≠ 0) : Real.tan x ^ 2 * Real.cos x ^ 2 = Real.sin x ^ 2 := by rw [Real.tan_eq_sin_div_cos, div_pow]; field_simp"),
    ]

    identifiers = [card.id for card in current]
    if len(current) != 30 or len(identifiers) != len(set(identifiers)):
        raise RuntimeError("expected exactly 30 uniquely identified trigonometry cards")
    canonical = [canonicalize_retrieval_openmath_xml(card.openmath_xml) for card in current]
    if len(canonical) != len(set(canonical)):
        raise RuntimeError("candidate manifest contains duplicate canonical OpenMath")
    return current


def verify_lean(current: list[Card]) -> None:
    workspace = ROOT / "pals-agent" / "lean-workspace"
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
    count = subprocess.run(["docker", "compose", "exec", "-T", "postgres", "psql", "-U", "pals", "-d", "pals", "-Atc", "SELECT count(*) FROM public.dsp_drafts;"], cwd=ROOT, text=True, capture_output=True, check=False)
    if count.returncode:
        raise RuntimeError(f"could not query local Draft count:\n{count.stderr}")
    if int(count.stdout.strip()) != expected_count:
        raise RuntimeError(f"expected {expected_count} local Drafts, found {count.stdout.strip()}")
    rows = subprocess.run(["docker", "compose", "exec", "-T", "postgres", "psql", "-U", "pals", "-d", "pals", "-At", "-F", "\t", "-c", "SELECT id, openmath_xml FROM public.dsp_drafts ORDER BY id;"], cwd=ROOT, text=True, capture_output=True, check=False)
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
    if duplicate_ids := sorted({card.id for card in current} & set(existing)):
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
    parser.add_argument("--verify-lean", action="store_true")
    parser.add_argument("--verify-db", action="store_true")
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
        "schema_version": "pals.high-school-trigonometry-expansion-candidates.v1",
        "source": "PALS first-party authored, generic-OpenMath and Lean-verified candidate set",
        "current_profile_card_count": len(current),
        "topic_counts": topic_counts,
        "scope_note": "All cards are closed real-valued identities or inequalities using only current generic transc1:sin/cos/tan, arithmetic, relations, logic, and real-membership premises. Tangent cancellation cards explicitly require cos(x) != 0.",
        "validation_contract": {
            "generic_openmath": "Every card runs statement-semantics validation, generic retrieval C14N, and exact-C14N validation while generated.",
            "lean": "Pass --verify-lean to compile one temporary Lean file containing all 30 witnesses in pals-agent/lean-workspace.",
            "local_db": "Pass --verify-db --expected-db-count 335 to read-check local Draft IDs and strict/legacy C14N collisions. This command does not write the database.",
        },
        "excluded_backlog": [
            {"item": "General-angle solution sets such as sin(x)=a", "reason": "They need pi and inverse-trigonometric values or a periodic solution-set object; neither is typed by the current generic profile."},
            {"item": "Inverse trigonometric functions and branch-sensitive identities", "reason": "The current profile has no asin/acos/atan symbols, interval/branch typing, or principal-value contract."},
            {"item": "Complex trigonometric identities", "reason": "They require a complex carrier and typed coercions; use the separate typed complex profile proposal instead."},
            {"item": "Unqualified tangent cancellation at cosine zeros", "reason": "Generic division is totalized, whereas the high-school tangent function is partial at those angles. Included cancellation claims state cos(x) != 0 explicitly."},
        ],
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
