"""Generate an authoring-only expansion of real exponential/logarithm Drafts.

The generic retrieval profile represents only real scalar arithmetic and
``transc1:exp``/``transc1:ln``.  This generator therefore keeps each card in
that scope, explicitly records strict positivity for every variable logarithm
argument, and never writes to the local Draft database.
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
DEFAULT_DB_COUNT = 401
LEGACY_MANIFEST = ROOT / "docs" / "exponent-log-number-theory-candidates.json"


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


def power(value: str, exponent: int) -> str:
    return std("arith1", "power", value, integer(exponent))


def neg(value: str) -> str:
    return std("arith1", "unary_minus", value)


def exp(value: str) -> str:
    return std("transc1", "exp", value)


def log(value: str) -> str:
    return std("transc1", "ln", value)


def eq(left: str, right: str) -> str:
    return std("relation1", "eq", left, right)


def leq(left: str, right: str) -> str:
    return std("relation1", "leq", left, right)


def lt(left: str, right: str) -> str:
    return std("relation1", "lt", left, right)


def gt(left: str, right: str) -> str:
    return std("relation1", "gt", left, right)


def and_(*arguments: str) -> str:
    return std("logic1", "and", *arguments)


def implies(premise: str, conclusion: str) -> str:
    return std("logic1", "implies", premise, conclusion)


def iff(left: str, right: str) -> str:
    return std("logic1", "equivalent", left, right)


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
    source = openmath(proposition)
    validate_openmath_statement_semantics(source, statement)
    canonical = canonicalize_retrieval_openmath_xml(source)
    validate_canonical_retrieval_openmath_xml(canonical)
    return Card(
        id=identifier,
        profile="current_openmath_profile",
        domain="high_school_real_exponentials_and_logarithms",
        level="high_school",
        topic=topic,
        difficulty=difficulty,
        canonical_statement=statement,
        openmath_xml=source,
        proof_strategy=strategy,
        sketch_steps=steps,
        lean_witness=witness,
    )


EXP_IDENTITY_STEPS = (
    "setup: Bind the displayed real variables and identify the exponential arguments.",
    "rewrite: Apply the exponential addition, subtraction, or inverse identity.",
    "normalize: Simplify the real product, quotient, or integer multiple.",
    "domain: Use that every real exponential is strictly positive when cancellation is needed.",
    "conclude: State the resulting real exponential equality.",
)

EXP_ORDER_STEPS = (
    "setup: Bind the two real inputs or the displayed real input.",
    "monotonicity: Use strict monotonicity of the real exponential function.",
    "translate: Move the equality or order relation between the exponential values and exponents.",
    "conclude: State the requested equivalence over the real numbers.",
)

LOG_RULE_STEPS = (
    "setup: Bind the real variables and record strict positivity for each variable logarithm argument.",
    "domain: Derive positivity and nonzeroness of every product, quotient, or power used inside ln.",
    "rule: Apply the relevant logarithm or exponential inverse rule.",
    "normalize: Rearrange the resulting real sum, difference, or integer multiple.",
    "conclude: State the equality with its positive-domain hypotheses intact.",
)

LOG_ORDER_STEPS = (
    "setup: Bind the positive real variables and retain their strict positivity hypotheses.",
    "domain: Verify that both logarithm arguments lie in the positive real domain.",
    "monotonicity: Apply strict monotonicity of ln on the positive reals.",
    "translate: Transfer the displayed equality or order relation back to the original variables.",
    "conclude: State the positive-domain equivalence.",
)


def cards() -> list[Card]:
    x, y, z = var("x"), var("y"), var("z")
    rx = lambda body: real_forall(("x",), body)
    rxy = lambda body: real_forall(("x", "y"), body)
    rxyz = lambda body: real_forall(("x", "y", "z"), body)
    pos_x, pos_y, pos_z = gt(x, integer(0)), gt(y, integer(0)), gt(z, integer(0))

    current = [
        make(
            "exlog_expand_exp_sub",
            "exponential_laws",
            "standard",
            "For all real x and y, exp(x - y) = exp(x)/exp(y).",
            rxy(eq(exp(minus(x, y)), divide(exp(x), exp(y)))),
            "Rewrite subtraction as addition of an inverse in the exponent.",
            EXP_IDENTITY_STEPS,
            "example (x y : ℝ) : Real.exp (x - y) = Real.exp x / Real.exp y := Real.exp_sub x y",
        ),
        make(
            "exlog_expand_exp_double",
            "exponential_laws",
            "standard",
            "For every real x, exp(2x) = exp(x)^2.",
            rx(eq(exp(times(integer(2), x)), power(exp(x), 2))),
            "Use the natural-multiple exponential law with multiplier two.",
            EXP_IDENTITY_STEPS,
            "example (x : ℝ) : Real.exp (2*x) = Real.exp x ^ 2 := by simpa using Real.exp_nat_mul x 2",
        ),
        make(
            "exlog_expand_exp_neg_product",
            "exponential_laws",
            "standard",
            "For every real x, exp(x)*exp(-x) = 1.",
            rx(eq(times(exp(x), exp(neg(x))), integer(1))),
            "Replace exp(-x) by the reciprocal of exp(x), then cancel the nonzero exponential.",
            EXP_IDENTITY_STEPS,
            "example (x : ℝ) : Real.exp x * Real.exp (-x) = 1 := by rw [Real.exp_neg]; field_simp",
        ),
        make(
            "exlog_expand_exp_add_cancel_right",
            "exponential_laws",
            "advanced",
            "For all real x and y, exp(x + y)*exp(-y) = exp(x).",
            rxy(eq(times(exp(plus(x, y)), exp(neg(y))), exp(x))),
            "Expand exp(x+y), then cancel the exponential factor associated with y.",
            EXP_IDENTITY_STEPS,
            "example (x y : ℝ) : Real.exp (x + y) * Real.exp (-y) = Real.exp x := by rw [Real.exp_add, Real.exp_neg]; field_simp",
        ),
        make(
            "exlog_expand_exp_sub_recover",
            "exponential_laws",
            "advanced",
            "For all real x and y, exp(x - y)*exp(y) = exp(x).",
            rxy(eq(times(exp(minus(x, y)), exp(y)), exp(x))),
            "Use the exponential subtraction formula and cancel the certified nonzero denominator.",
            EXP_IDENTITY_STEPS,
            "example (x y : ℝ) : Real.exp (x - y) * Real.exp y = Real.exp x := by rw [Real.exp_sub]; field_simp",
        ),
        make(
            "exlog_expand_exp_eq_iff",
            "exponential_equations",
            "standard",
            "For all real x and y, exp(x) = exp(y) if and only if x = y.",
            rxy(iff(eq(exp(x), exp(y)), eq(x, y))),
            "Use injectivity of the strictly increasing real exponential function.",
            EXP_ORDER_STEPS,
            "example (x y : ℝ) : Real.exp x = Real.exp y ↔ x = y := Real.exp_eq_exp",
        ),
        make(
            "exlog_expand_exp_lt_iff",
            "exponential_inequalities",
            "standard",
            "For all real x and y, exp(x) < exp(y) if and only if x < y.",
            rxy(iff(lt(exp(x), exp(y)), lt(x, y))),
            "Use strict monotonicity of exp to compare exponents directly.",
            EXP_ORDER_STEPS,
            "example (x y : ℝ) : Real.exp x < Real.exp y ↔ x < y := Real.exp_lt_exp",
        ),
        make(
            "exlog_expand_exp_le_iff",
            "exponential_inequalities",
            "standard",
            "For all real x and y, exp(x) ≤ exp(y) if and only if x ≤ y.",
            rxy(iff(leq(exp(x), exp(y)), leq(x, y))),
            "Use monotonicity and injectivity of exp to compare non-strict inequalities.",
            EXP_ORDER_STEPS,
            "example (x y : ℝ) : Real.exp x ≤ Real.exp y ↔ x ≤ y := Real.exp_le_exp",
        ),
        make(
            "exlog_expand_one_lt_exp_iff",
            "exponential_inequalities",
            "introductory",
            "For every real x, 1 < exp(x) if and only if 0 < x.",
            rx(iff(lt(integer(1), exp(x)), lt(integer(0), x))),
            "Compare exp(x) to exp(0)=1 using strict monotonicity.",
            EXP_ORDER_STEPS,
            "example (x : ℝ) : 1 < Real.exp x ↔ 0 < x := Real.one_lt_exp_iff",
        ),
        make(
            "exlog_expand_exp_lt_one_iff",
            "exponential_inequalities",
            "introductory",
            "For every real x, exp(x) < 1 if and only if x < 0.",
            rx(iff(lt(exp(x), integer(1)), lt(x, integer(0)))),
            "Compare exp(x) to exp(0)=1 using strict monotonicity.",
            EXP_ORDER_STEPS,
            "example (x : ℝ) : Real.exp x < 1 ↔ x < 0 := Real.exp_lt_one_iff",
        ),
        make(
            "exlog_expand_one_le_exp_iff",
            "exponential_inequalities",
            "introductory",
            "For every real x, 1 ≤ exp(x) if and only if 0 ≤ x.",
            rx(iff(leq(integer(1), exp(x)), leq(integer(0), x))),
            "Compare exp(x) to exp(0)=1 using monotonicity.",
            EXP_ORDER_STEPS,
            "example (x : ℝ) : 1 ≤ Real.exp x ↔ 0 ≤ x := Real.one_le_exp_iff",
        ),
        make(
            "exlog_expand_exp_le_one_iff",
            "exponential_inequalities",
            "introductory",
            "For every real x, exp(x) ≤ 1 if and only if x ≤ 0.",
            rx(iff(leq(exp(x), integer(1)), leq(x, integer(0)))),
            "Compare exp(x) to exp(0)=1 using monotonicity.",
            EXP_ORDER_STEPS,
            "example (x : ℝ) : Real.exp x ≤ 1 ↔ x ≤ 0 := Real.exp_le_one_iff",
        ),
        make(
            "exlog_expand_log_cube_positive",
            "logarithm_laws",
            "standard",
            "For every real x, if x > 0 then ln(x^3) = 3ln(x).",
            rx(implies(pos_x, eq(log(power(x, 3)), times(integer(3), log(x))))),
            "Apply the logarithm power rule after retaining the positive argument condition.",
            LOG_RULE_STEPS,
            "example (x : ℝ) (_hx : 0 < x) : Real.log (x^3) = 3 * Real.log x := by simpa using Real.log_pow x 3",
        ),
        make(
            "exlog_expand_log_fourth_power_positive",
            "logarithm_laws",
            "standard",
            "For every real x, if x > 0 then ln(x^4) = 4ln(x).",
            rx(implies(pos_x, eq(log(power(x, 4)), times(integer(4), log(x))))),
            "Apply the logarithm power rule after retaining the positive argument condition.",
            LOG_RULE_STEPS,
            "example (x : ℝ) (_hx : 0 < x) : Real.log (x^4) = 4 * Real.log x := by simpa using Real.log_pow x 4",
        ),
        make(
            "exlog_expand_log_product_three_positive",
            "logarithm_laws",
            "advanced",
            "For all real x, y, and z, if x > 0, y > 0, and z > 0 then ln(xyz) = ln(x) + ln(y) + ln(z).",
            rxyz(implies(and_(pos_x, pos_y, pos_z), eq(log(times(x, y, z)), plus(log(x), log(y), log(z))))),
            "Apply the product rule twice, preserving positivity of all three factors.",
            LOG_RULE_STEPS,
            """example (x y z : ℝ) (hx : 0 < x) (hy : 0 < y) (hz : 0 < z) : Real.log (x*y*z) = Real.log x + Real.log y + Real.log z := by
  rw [Real.log_mul (mul_ne_zero (ne_of_gt hx) (ne_of_gt hy)) (ne_of_gt hz), Real.log_mul (ne_of_gt hx) (ne_of_gt hy)]""",
        ),
        make(
            "exlog_expand_log_quotient_product_positive",
            "logarithm_laws",
            "advanced",
            "For all real x, y, and z, if x > 0, y > 0, and z > 0 then ln(x/(yz)) = ln(x) - ln(y) - ln(z).",
            rxyz(implies(and_(pos_x, pos_y, pos_z), eq(log(divide(x, times(y, z))), minus(minus(log(x), log(y)), log(z))))),
            "Use the quotient rule, then split the denominator with the product rule.",
            LOG_RULE_STEPS,
            """example (x y z : ℝ) (hx : 0 < x) (hy : 0 < y) (hz : 0 < z) : Real.log (x / (y*z)) = Real.log x - Real.log y - Real.log z := by
  rw [Real.log_div (ne_of_gt hx) (mul_ne_zero (ne_of_gt hy) (ne_of_gt hz)), Real.log_mul (ne_of_gt hy) (ne_of_gt hz)]
  ring""",
        ),
        make(
            "exlog_expand_log_product_quotient_positive",
            "logarithm_laws",
            "advanced",
            "For all real x, y, and z, if x > 0, y > 0, and z > 0 then ln(xy/z) = ln(x) + ln(y) - ln(z).",
            rxyz(implies(and_(pos_x, pos_y, pos_z), eq(log(divide(times(x, y), z)), minus(plus(log(x), log(y)), log(z))))),
            "Apply the quotient rule after the product rule in the numerator.",
            LOG_RULE_STEPS,
            """example (x y z : ℝ) (hx : 0 < x) (hy : 0 < y) (hz : 0 < z) : Real.log (x*y / z) = Real.log x + Real.log y - Real.log z := by
  rw [Real.log_div (mul_ne_zero (ne_of_gt hx) (ne_of_gt hy)) (ne_of_gt hz), Real.log_mul (ne_of_gt hx) (ne_of_gt hy)]""",
        ),
        make(
            "exlog_expand_log_square_quotient_positive",
            "logarithm_laws",
            "advanced",
            "For all real x and y, if x > 0 and y > 0 then ln(x^2/y) = 2ln(x) - ln(y).",
            rxy(implies(and_(pos_x, pos_y), eq(log(divide(power(x, 2), y)), minus(times(integer(2), log(x)), log(y))))),
            "Combine the quotient rule with the square power rule.",
            LOG_RULE_STEPS,
            """example (x y : ℝ) (hx : 0 < x) (hy : 0 < y) : Real.log (x^2 / y) = 2 * Real.log x - Real.log y := by
  rw [Real.log_div (pow_ne_zero _ (ne_of_gt hx)) (ne_of_gt hy), Real.log_pow]
  norm_num""",
        ),
        make(
            "exlog_expand_log_quotient_square_positive",
            "logarithm_laws",
            "advanced",
            "For all real x and y, if x > 0 and y > 0 then ln(x/y^2) = ln(x) - 2ln(y).",
            rxy(implies(and_(pos_x, pos_y), eq(log(divide(x, power(y, 2))), minus(log(x), times(integer(2), log(y))))),),
            "Combine the quotient rule with the square power rule in the denominator.",
            LOG_RULE_STEPS,
            """example (x y : ℝ) (hx : 0 < x) (hy : 0 < y) : Real.log (x / y^2) = Real.log x - 2 * Real.log y := by
  rw [Real.log_div (ne_of_gt hx) (pow_ne_zero _ (ne_of_gt hy)), Real.log_pow]
  norm_num""",
        ),
        make(
            "exlog_expand_exp_log_product_positive",
            "logarithm_exponential_inverses",
            "standard",
            "For all real x and y, if x > 0 and y > 0 then exp(ln(x) + ln(y)) = xy.",
            rxy(implies(and_(pos_x, pos_y), eq(exp(plus(log(x), log(y))), times(x, y)))),
            "Use the exponential addition formula and cancel each logarithm on its positive domain.",
            LOG_RULE_STEPS,
            """example (x y : ℝ) (hx : 0 < x) (hy : 0 < y) : Real.exp (Real.log x + Real.log y) = x*y := by
  rw [Real.exp_add, Real.exp_log hx, Real.exp_log hy]""",
        ),
        make(
            "exlog_expand_exp_log_quotient_positive",
            "logarithm_exponential_inverses",
            "standard",
            "For all real x and y, if x > 0 and y > 0 then exp(ln(x) - ln(y)) = x/y.",
            rxy(implies(and_(pos_x, pos_y), eq(exp(minus(log(x), log(y))), divide(x, y)))),
            "Use the exponential subtraction formula and cancel each logarithm on its positive domain.",
            LOG_RULE_STEPS,
            """example (x y : ℝ) (hx : 0 < x) (hy : 0 < y) : Real.exp (Real.log x - Real.log y) = x/y := by
  rw [Real.exp_sub, Real.exp_log hx, Real.exp_log hy]""",
        ),
        make(
            "exlog_expand_log_exp_sum",
            "logarithm_exponential_inverses",
            "standard",
            "For all real x and y, if exp(x+y) > 0 then ln(exp(x+y)) = x+y.",
            rxy(implies(gt(exp(plus(x, y)), integer(0)), eq(log(exp(plus(x, y))), plus(x, y)))),
            "The explicit positive-domain premise certifies the logarithm input; then logarithm and exponential cancel.",
            LOG_RULE_STEPS,
            """example (x y : ℝ) (_h : 0 < Real.exp (x+y)) : Real.log (Real.exp (x+y)) = x+y := Real.log_exp _""",
        ),
        make(
            "exlog_expand_log_zero_iff_one_positive",
            "logarithmic_equations",
            "standard",
            "For every real x, if x > 0 then ln(x) = 0 if and only if x = 1.",
            rx(implies(pos_x, iff(eq(log(x), integer(0)), eq(x, integer(1))))),
            "On the positive real domain, logarithm is injective and ln(1)=0.",
            LOG_ORDER_STEPS,
            """example (x : ℝ) (hx : 0 < x) : Real.log x = 0 ↔ x = 1 := by
  constructor
  · exact Real.eq_one_of_pos_of_log_eq_zero hx
  · rintro rfl
    exact Real.log_one""",
        ),
        make(
            "exlog_expand_log_eq_iff_positive",
            "logarithmic_equations",
            "advanced",
            "For all real x and y, if x > 0 and y > 0 then ln(x) = ln(y) if and only if x = y.",
            rxy(implies(and_(pos_x, pos_y), iff(eq(log(x), log(y)), eq(x, y)))),
            "Exponentiate both sides on the positive real domain to use the inverse law.",
            LOG_ORDER_STEPS,
            """example (x y : ℝ) (hx : 0 < x) (hy : 0 < y) : Real.log x = Real.log y ↔ x = y := by
  constructor
  · intro h
    have h_exp := congrArg Real.exp h
    simpa only [Real.exp_log hx, Real.exp_log hy] using h_exp
  · intro h
    rw [h]""",
        ),
        make(
            "exlog_expand_log_lt_iff_positive",
            "logarithmic_inequalities",
            "standard",
            "For all real x and y, if x > 0 and y > 0 then ln(x) < ln(y) if and only if x < y.",
            rxy(implies(and_(pos_x, pos_y), iff(lt(log(x), log(y)), lt(x, y)))),
            "Use strict monotonicity of logarithm on positive real inputs.",
            LOG_ORDER_STEPS,
            "example (x y : ℝ) (hx : 0 < x) (hy : 0 < y) : Real.log x < Real.log y ↔ x < y := Real.log_lt_log_iff hx hy",
        ),
        make(
            "exlog_expand_log_le_iff_positive",
            "logarithmic_inequalities",
            "standard",
            "For all real x and y, if x > 0 and y > 0 then ln(x) ≤ ln(y) if and only if x ≤ y.",
            rxy(implies(and_(pos_x, pos_y), iff(leq(log(x), log(y)), leq(x, y)))),
            "Use monotonicity and injectivity of logarithm on positive real inputs.",
            LOG_ORDER_STEPS,
            "example (x y : ℝ) (hx : 0 < x) (hy : 0 < y) : Real.log x ≤ Real.log y ↔ x ≤ y := Real.log_le_log_iff hx hy",
        ),
        make(
            "exlog_expand_log_positive_iff",
            "logarithmic_inequalities",
            "introductory",
            "For every real x, if x > 0 then 0 < ln(x) if and only if 1 < x.",
            rx(implies(pos_x, iff(lt(integer(0), log(x)), lt(integer(1), x)))),
            "Compare ln(x) with ln(1)=0 on the positive real domain.",
            LOG_ORDER_STEPS,
            "example (x : ℝ) (hx : 0 < x) : 0 < Real.log x ↔ 1 < x := Real.log_pos_iff hx.le",
        ),
        make(
            "exlog_expand_log_negative_iff",
            "logarithmic_inequalities",
            "introductory",
            "For every real x, if x > 0 then ln(x) < 0 if and only if x < 1.",
            rx(implies(pos_x, iff(lt(log(x), integer(0)), lt(x, integer(1))))),
            "Compare ln(x) with ln(1)=0 on the positive real domain.",
            LOG_ORDER_STEPS,
            "example (x : ℝ) (hx : 0 < x) : Real.log x < 0 ↔ x < 1 := Real.log_neg_iff hx",
        ),
        make(
            "exlog_expand_log_nonnegative_iff",
            "logarithmic_inequalities",
            "introductory",
            "For every real x, if x > 0 then 0 ≤ ln(x) if and only if 1 ≤ x.",
            rx(implies(pos_x, iff(leq(integer(0), log(x)), leq(integer(1), x)))),
            "Use the positive-domain logarithm order equivalence against one.",
            LOG_ORDER_STEPS,
            "example (x : ℝ) (hx : 0 < x) : 0 ≤ Real.log x ↔ 1 ≤ x := Real.log_nonneg_iff hx",
        ),
        make(
            "exlog_expand_log_nonpositive_iff",
            "logarithmic_inequalities",
            "introductory",
            "For every real x, if x > 0 then ln(x) ≤ 0 if and only if x ≤ 1.",
            rx(implies(pos_x, iff(leq(log(x), integer(0)), leq(x, integer(1))))),
            "Use the positive-domain logarithm order equivalence against one.",
            LOG_ORDER_STEPS,
            "example (x : ℝ) (hx : 0 < x) : Real.log x ≤ 0 ↔ x ≤ 1 := Real.log_nonpos_iff hx.le",
        ),
    ]

    identifiers = [card.id for card in current]
    if len(current) != 30 or len(identifiers) != len(set(identifiers)):
        raise RuntimeError("expected exactly 30 uniquely identified exponent/logarithm cards")
    canonical = [canonicalize_retrieval_openmath_xml(card.openmath_xml) for card in current]
    if len(canonical) != len(set(canonical)):
        raise RuntimeError("candidate manifest contains duplicate canonical OpenMath")
    return current


def verify_legacy_manifest(current: list[Card]) -> None:
    payload = json.loads(LEGACY_MANIFEST.read_text(encoding="utf-8"))
    legacy = payload.get("cards")
    if not isinstance(legacy, list):
        raise TypeError("legacy exponent/log manifest has no cards array")
    legacy_ids = {item.get("id") for item in legacy if isinstance(item, dict)}
    if duplicate_ids := sorted({card.id for card in current} & legacy_ids):
        raise RuntimeError(f"candidate IDs already exist in legacy exponent/log manifest: {duplicate_ids}")
    legacy_canonical = {
        canonicalize_openmath_xml(item["openmath_xml"])
        for item in legacy
        if isinstance(item, dict) and isinstance(item.get("openmath_xml"), str)
    }
    current_canonical = {canonicalize_openmath_xml(card.openmath_xml) for card in current}
    if current_canonical & legacy_canonical:
        raise RuntimeError("candidate canonical OpenMath duplicates the legacy exponent/log manifest")


def verify_lean(current: list[Card]) -> None:
    workspace = ROOT / "pals-agent" / "lean-workspace"
    source = "import Mathlib\n\n" + "\n\n".join(card.lean_witness for card in current) + "\n"
    with tempfile.NamedTemporaryFile("w", suffix=".lean", dir=workspace, delete=False, encoding="utf-8") as handle:
        handle.write(source)
        witness_file = Path(handle.name)
    try:
        completed = subprocess.run(
            ["lake", "env", "lean", str(witness_file)],
            cwd=workspace,
            text=True,
            capture_output=True,
            check=False,
        )
    finally:
        witness_file.unlink(missing_ok=True)
    if completed.returncode:
        raise RuntimeError(f"Lean witness compilation failed:\n{completed.stdout}{completed.stderr}")


def verify_database(current: list[Card], expected_count: int) -> tuple[str, ...]:
    compose = ["docker", "compose", "--env-file", ".env.local", "exec", "-T", "postgres", "psql", "-U", "pals", "-d", "pals"]
    count = subprocess.run(
        [*compose, "-Atc", "SELECT count(*) FROM public.dsp_drafts;"],
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
        [*compose, "-At", "-F", "\t", "-c", "SELECT id, openmath_xml FROM public.dsp_drafts ORDER BY id;"],
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
    verify_legacy_manifest(current)
    if args.verify_lean:
        verify_lean(current)
    fallback: tuple[str, ...] = ()
    if args.verify_db:
        fallback = verify_database(current, args.expected_db_count)
    topic_counts = {
        topic: sum(card.topic == topic for card in current)
        for topic in sorted({card.topic for card in current})
    }
    payload = {
        "schema_version": "pals.high-school-real-exponent-logarithm-expansion-candidates.v1",
        "source": "PALS first-party authored, generic-OpenMath and Lean-verified candidate set",
        "current_profile_card_count": len(current),
        "topic_counts": topic_counts,
        "scope_note": "All cards use only real scalar arithmetic, transc1:exp, transc1:ln, relations, logic, and explicit real-membership premises. Every variable expression passed to ln has an explicit strict-positivity premise; the sole ln(exp(x+y)) card explicitly records positivity of that exponential argument.",
        "validation_contract": {
            "generic_openmath": "Every card runs statement-semantics validation, generic retrieval C14N, and exact-C14N validation while generated.",
            "legacy_manifest": "Generation rejects IDs and legacy C14N collisions against docs/exponent-log-number-theory-candidates.json.",
            "lean": "Pass --verify-lean to compile one temporary Lean file containing all 30 witnesses in pals-agent/lean-workspace.",
            "local_db": "Pass --verify-db --expected-db-count 401 to read-check local Draft IDs and strict/legacy C14N collisions. This command does not write the database.",
        },
        "excluded_backlog": [
            {"item": "General real-base expressions a^x and logarithms log_a(x)", "reason": "The current generic profile has no typed real-base exponentiation, a base-not-equal-to-one condition, or a base-order contract."},
            {"item": "Complex logarithms and branch-sensitive identities", "reason": "They require a complex carrier, branch data, and typed coercions; use a separate typed complex profile."},
            {"item": "Unqualified logarithm product or quotient laws", "reason": "The high-school real logarithm laws require positive arguments. Every included variable logarithm law retains strict positivity in its proposition."},
            {"item": "Numerical drill variants differing only by constants", "reason": "This expansion favors reusable identity, equation, inequality, and substitution patterns rather than constant substitutions."},
        ],
        "cards": [asdict(card) for card in current],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"cards={len(current)} generic_openmath=passed c14n_unique=passed legacy_collision_check=passed")
    if args.verify_lean:
        print("lean=passed")
    if args.verify_db:
        print(f"local_db={args.expected_db_count}_rows id_and_c14n_collision_check=passed")
        if fallback:
            print("local_db_retrieval_c14n_fallback=" + ",".join(fallback))


if __name__ == "__main__":
    main()
