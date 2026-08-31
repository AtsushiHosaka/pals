#!/usr/bin/env python3
"""Generate Lean-verified exponent/log and elementary-number-theory Drafts.

Only `gcd` and `lcm` are used for variable natural-number theory.  Congruence,
divisibility, primality, and remainder are intentionally excluded because the
current retrieval profile has no semantics for them.
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


def neg(value: str) -> str:
    return standard("arith1", "unary_minus", value)


def exp(value: str) -> str:
    return standard("transc1", "exp", value)


def log(value: str) -> str:
    return standard("transc1", "ln", value)


def gcd(left: str, right: str) -> str:
    return standard("arith1", "gcd", left, right)


def lcm(left: str, right: str) -> str:
    return standard("arith1", "lcm", left, right)


def equal(left: str, right: str) -> str:
    return standard("relation1", "eq", left, right)


def gt(left: str, right: str) -> str:
    return standard("relation1", "gt", left, right)


def implies(left: str, right: str) -> str:
    return standard("logic1", "implies", left, right)


def conjunction(*args: str) -> str:
    return standard("logic1", "and", *args)


def forall(names: tuple[str, ...], body: str) -> str:
    return tag("OMBIND", oms("quant1", "forall") + tag("OMBVAR", "".join(var(name) for name in names)) + body)


def exists(names: tuple[str, ...], body: str) -> str:
    return tag("OMBIND", oms("quant1", "exists") + tag("OMBVAR", "".join(var(name) for name in names)) + body)


def typed_forall(names: tuple[str, ...], set_name: str, body: str) -> str:
    memberships = tuple(standard("set1", "in", var(name), oms("setname1", set_name)) for name in names)
    premise = memberships[0] if len(memberships) == 1 else conjunction(*memberships)
    return forall(names, implies(premise, body))


def typed_exists(names: tuple[str, ...], set_name: str, body: str) -> str:
    memberships = tuple(standard("set1", "in", var(name), oms("setname1", set_name)) for name in names)
    premise = memberships[0] if len(memberships) == 1 else conjunction(*memberships)
    return exists(names, conjunction(premise, body))


def openmath(body: str) -> str:
    return f'<OMOBJ xmlns="{OPENMATH}" version="2.0">{body}</OMOBJ>'


def make(identifier: str, domain: str, statement: str, proposition: str, strategy: str, steps: tuple[str, ...], witness: str, *, difficulty: str) -> Card:
    return Card(identifier, domain, "high_school_and_early_university", difficulty, "current_openmath_profile", statement, openmath(proposition), strategy, steps, witness)


EXP_LOG_STEPS = (
    "setup: Bind the real variables and record the required positivity hypotheses for every logarithm argument.",
    "domain: Verify that each logarithm is evaluated at a strictly positive real number.",
    "rule: Apply the matching exponential or logarithm identity.",
    "simplify: Normalize products, quotients, powers, or inverse expressions.",
    "conclude: State the resulting real equality or implication.",
)

NUMBER_STEPS = (
    "setup: Bind the natural or integer variables and write the arithmetic expression explicitly.",
    "structure: Apply the gcd/lcm identity or choose the integer coefficients required by the claim.",
    "calculate: Evaluate or simplify the two sides in the appropriate number system.",
    "verify: Check the stated equality or Bézout combination directly.",
    "conclude: State the number-theoretic result.",
)


def exponent_log_cards() -> list[Card]:
    x, y = var("x"), var("y")
    real_x = lambda body: typed_forall(("x",), "R", body)
    real_xy = lambda body: typed_forall(("x", "y"), "R", body)
    positive_x = gt(x, integer(0))
    positive_y = gt(y, integer(0))
    return [
        make("exlog_exp_zero", "exponentials_and_logarithms", "The real exponential satisfies exp(0) = 1.", equal(exp(integer(0)), integer(1)), "Evaluate the exponential at its additive identity.", EXP_LOG_STEPS, "example : Real.exp 0 = 1 := Real.exp_zero", difficulty="standard"),
        make("exlog_exp_add", "exponentials_and_logarithms", "For all real x and y, exp(x + y) = exp(x) * exp(y).", real_xy(equal(exp(plus(x, y)), times(exp(x), exp(y)))), "Apply the exponential addition formula.", EXP_LOG_STEPS, "example (x y : ℝ) : Real.exp (x + y) = Real.exp x * Real.exp y := Real.exp_add x y", difficulty="standard"),
        make("exlog_exp_neg", "exponentials_and_logarithms", "For every real x, exp(-x) = 1/exp(x).", real_x(equal(exp(neg(x)), divide(integer(1), exp(x)))), "Use the exponential inverse identity and rewrite the inverse as one divided by exp(x).", EXP_LOG_STEPS, "example (x : ℝ) : Real.exp (-x) = 1 / Real.exp x := by simpa [one_div] using Real.exp_neg x", difficulty="standard"),
        make("exlog_exp_strictly_positive", "exponentials_and_logarithms", "For every real x, exp(x) > 0.", real_x(gt(exp(x), integer(0))), "Use positivity of the real exponential function.", EXP_LOG_STEPS, "example (x : ℝ) : 0 < Real.exp x := Real.exp_pos x", difficulty="standard"),
        make("exlog_log_one", "exponentials_and_logarithms", "The real logarithm satisfies ln(1) = 0.", equal(log(integer(1)), integer(0)), "Evaluate the logarithm at the positive multiplicative identity.", EXP_LOG_STEPS, "example : Real.log 1 = 0 := Real.log_one", difficulty="standard"),
        make("exlog_log_exp", "exponentials_and_logarithms", "For every real x, ln(exp(x)) = x.", real_x(equal(log(exp(x)), x)), "The exponential is always positive, so logarithm and exponential cancel.", EXP_LOG_STEPS, "example (x : ℝ) : Real.log (Real.exp x) = x := Real.log_exp x", difficulty="standard"),
        make("exlog_exp_log_positive", "exponentials_and_logarithms", "For every real x, if x > 0 then exp(ln(x)) = x.", real_x(implies(positive_x, equal(exp(log(x)), x))), "Use the inverse identity on the explicit positive-domain hypothesis.", EXP_LOG_STEPS, "example (x : ℝ) (hx : 0 < x) : Real.exp (Real.log x) = x := Real.exp_log hx", difficulty="standard"),
        make("exlog_log_mul_positive", "exponentials_and_logarithms", "For all real x and y, if x > 0 and y > 0 then ln(x*y) = ln(x) + ln(y).", real_xy(implies(conjunction(positive_x, positive_y), equal(log(times(x, y)), plus(log(x), log(y))))), "Use the product rule after deriving nonzeroness from positivity.", EXP_LOG_STEPS, "example (x y : ℝ) (hx : 0 < x) (hy : 0 < y) : Real.log (x*y) = Real.log x + Real.log y := Real.log_mul (ne_of_gt hx) (ne_of_gt hy)", difficulty="standard"),
        make("exlog_log_div_positive", "exponentials_and_logarithms", "For all real x and y, if x > 0 and y > 0 then ln(x/y) = ln(x) - ln(y).", real_xy(implies(conjunction(positive_x, positive_y), equal(log(divide(x, y)), minus(log(x), log(y))))), "Use the quotient rule after deriving that both arguments are nonzero.", EXP_LOG_STEPS, "example (x y : ℝ) (hx : 0 < x) (hy : 0 < y) : Real.log (x/y) = Real.log x - Real.log y := Real.log_div (ne_of_gt hx) (ne_of_gt hy)", difficulty="standard"),
        make("exlog_log_inv_positive", "exponentials_and_logarithms", "For every real x, if x > 0 then ln(1/x) = -ln(x).", real_x(implies(positive_x, equal(log(divide(integer(1), x)), neg(log(x))))), "Use the inverse rule for logarithms; positivity makes the reciprocal a valid positive argument.", EXP_LOG_STEPS, "example (x : ℝ) (_hx : 0 < x) : Real.log (1/x) = -Real.log x := by simpa [one_div] using Real.log_inv x", difficulty="standard"),
        make("exlog_log_square_positive", "exponentials_and_logarithms", "For every real x, if x > 0 then ln(x^2) = 2ln(x).", real_x(implies(positive_x, equal(log(power(x, 2)), times(integer(2), log(x))))), "Apply the logarithm power rule on the positive-domain hypothesis.", EXP_LOG_STEPS, "example (x : ℝ) (_hx : 0 < x) : Real.log (x^2) = 2 * Real.log x := by simpa using Real.log_pow x 2", difficulty="standard"),
        make("exlog_exp_eq_one_solution", "exponentials_and_logarithms", "For every real x, if exp(x) = 1 then x = 0.", real_x(implies(equal(exp(x), integer(1)), equal(x, integer(0)))), "Use injectivity of the exponential at the value one.", EXP_LOG_STEPS, "example (x : ℝ) : Real.exp x = 1 → x = 0 := by intro h; exact (Real.exp_eq_one_iff x).mp h", difficulty="advanced"),
        make("exlog_exp_injective", "exponentials_and_logarithms", "For all real x and y, if exp(x) = exp(y) then x = y.", real_xy(implies(equal(exp(x), exp(y)), equal(x, y))), "Apply injectivity of the real exponential function.", EXP_LOG_STEPS, "example (x y : ℝ) : Real.exp x = Real.exp y → x = y := by intro h; exact Real.exp_injective h", difficulty="advanced"),
        make("exlog_log_injective_positive", "exponentials_and_logarithms", "For all real x and y, if x > 0, y > 0, and ln(x) = ln(y), then x = y.", real_xy(implies(conjunction(positive_x, positive_y, equal(log(x), log(y))), equal(x, y))), "Restrict logarithm to positive reals, where it is strictly monotone and hence injective.", EXP_LOG_STEPS, "example (x y : ℝ) (hx : 0 < x) (hy : 0 < y) : Real.log x = Real.log y → x = y := by intro h; exact Real.strictMonoOn_log.injOn hx hy h", difficulty="advanced"),
    ]


def elementary_number_theory_cards() -> list[Card]:
    m, n, k = map(var, ("m", "n", "k"))
    natural_mn = lambda body: typed_forall(("m", "n"), "N", body)
    natural_mnk = lambda body: typed_forall(("m", "n", "k"), "N", body)
    def bezout(identifier: str, statement: str, a_value: int, b_value: int, left: int, right: int, target: int) -> Card:
        a, b = var("a"), var("b")
        return make(identifier, "elementary_number_theory", statement, typed_exists(("a", "b"), "Z", equal(plus(times(integer(left), a), times(integer(right), b)), integer(target))), "Provide explicit integer coefficients and verify their linear combination.", NUMBER_STEPS, f"example : ∃ a b : ℤ, {left}*a + {right}*b = {target} := by\n  refine ⟨{a_value}, {b_value}, by norm_num⟩", difficulty="standard")
    return [
        make("nt_gcd_lcm_product_identity", "elementary_number_theory", "For all natural m and n, gcd(m,n) * lcm(m,n) = m*n.", natural_mn(equal(times(gcd(m, n), lcm(m, n)), times(m, n))), "Apply the standard gcd-lcm product identity.", NUMBER_STEPS, "example (m n : ℕ) : Nat.gcd m n * Nat.lcm m n = m*n := Nat.gcd_mul_lcm m n", difficulty="advanced"),
        make("nt_gcd_common_factor_left", "elementary_number_theory", "For all natural m, n, and k, gcd(m*n,m*k) = m*gcd(n,k).", natural_mnk(equal(gcd(times(m, n), times(m, k)), times(m, gcd(n, k)))), "Factor the common left multiplier from both gcd arguments.", NUMBER_STEPS, "example (m n k : ℕ) : Nat.gcd (m*n) (m*k) = m * Nat.gcd n k := Nat.gcd_mul_left m n k", difficulty="advanced"),
        make("nt_lcm_common_factor_left", "elementary_number_theory", "For all natural m, n, and k, lcm(m*n,m*k) = m*lcm(n,k).", natural_mnk(equal(lcm(times(m, n), times(m, k)), times(m, lcm(n, k)))), "Factor the common left multiplier from both lcm arguments.", NUMBER_STEPS, "example (m n k : ℕ) : Nat.lcm (m*n) (m*k) = m * Nat.lcm n k := Nat.lcm_mul_left m n k", difficulty="advanced"),
        make("nt_gcd_common_factor_right", "elementary_number_theory", "For all natural m, n, and k, gcd(m*n,k*n) = gcd(m,k)*n.", natural_mnk(equal(gcd(times(m, n), times(k, n)), times(gcd(m, k), n))), "Factor the common right multiplier from both gcd arguments.", NUMBER_STEPS, "example (m n k : ℕ) : Nat.gcd (m*n) (k*n) = Nat.gcd m k * n := Nat.gcd_mul_right m n k", difficulty="advanced"),
        make("nt_lcm_common_factor_right", "elementary_number_theory", "For all natural m, n, and k, lcm(m*n,k*n) = lcm(m,k)*n.", natural_mnk(equal(lcm(times(m, n), times(k, n)), times(lcm(m, k), n))), "Factor the common right multiplier from both lcm arguments.", NUMBER_STEPS, "example (m n k : ℕ) : Nat.lcm (m*n) (k*n) = Nat.lcm m k * n := Nat.lcm_mul_right m n k", difficulty="advanced"),
        bezout("nt_bezout_21_15", "There exist integers a and b such that 21a + 15b = 3.", -2, 3, 21, 15, 3),
        bezout("nt_bezout_35_12", "There exist integers a and b such that 35a + 12b = 1.", -1, 3, 35, 12, 1),
        bezout("nt_bezout_30_18", "There exist integers a and b such that 30a + 18b = 6.", -1, 2, 30, 18, 6),
        bezout("nt_bezout_14_21", "There exist integers a and b such that 14a + 21b = 7.", -1, 1, 14, 21, 7),
        bezout("nt_bezout_101_37", "There exist integers a and b such that 101a + 37b = 1.", 11, -30, 101, 37, 1),
        make("nt_gcd_84_30", "elementary_number_theory", "The greatest common divisor gcd(84,30) equals 6.", equal(gcd(integer(84), integer(30)), integer(6)), "Evaluate the Euclidean algorithm on the fixed pair 84 and 30.", NUMBER_STEPS, "example : Nat.gcd 84 30 = 6 := by norm_num [Nat.gcd]", difficulty="standard"),
        make("nt_lcm_15_20", "elementary_number_theory", "The least common multiple lcm(15,20) equals 60.", equal(lcm(integer(15), integer(20)), integer(60)), "Evaluate the least common multiple of the two fixed natural numbers.", NUMBER_STEPS, "example : Nat.lcm 15 20 = 60 := by norm_num [Nat.lcm]", difficulty="standard"),
    ]


def backlog() -> list[dict[str, object]]:
    return [
        {"topic": "divisibility", "examples": ["if d divides m and n then d divides gcd(m,n)", "Euclidean division"], "minimum_symbols": ["relation1:divides or number_theory1:divides", "number_theory1:quotient", "number_theory1:remainder"], "why_current_profile_cannot_represent_it": "No supported predicate specifies divisibility or a quotient-remainder relation."},
        {"topic": "modular arithmetic", "examples": ["a congruent to b modulo n", "linear congruence", "Fermat's little theorem"], "minimum_symbols": ["number_theory1:congruent_mod"], "why_current_profile_cannot_represent_it": "The current profile has no congruence predicate, so equality of residues cannot be distinguished from ordinary equality."},
        {"topic": "primality and factorization", "examples": ["a prime has no positive divisors other than one and itself", "unique prime factorization"], "minimum_symbols": ["number_theory1:prime", "number_theory1:factorization"], "why_current_profile_cannot_represent_it": "The profile has neither primality nor factorization predicates/functions."},
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    current = exponent_log_cards() + elementary_number_theory_cards()
    for card in current:
        validate_openmath_statement_semantics(card.openmath_xml, card.canonical_statement)
    if len(current) != 26 or len({card.id for card in current}) != 26:
        raise RuntimeError("expected 26 unique current-profile cards")
    if not all(4 <= len(card.sketch_steps) <= 8 for card in current):
        raise RuntimeError("every current-profile card needs four to eight sketch steps")
    payload = {
        "schema_version": "pals.exponent-log-and-elementary-number-theory-candidates.v1",
        "source": "PALS first-party authored, Lean-verified candidate set",
        "current_profile_card_count": len(current),
        "domain_counts": {"exponentials_and_logarithms": len(exponent_log_cards()), "elementary_number_theory": len(elementary_number_theory_cards())},
        "cards": [asdict(card) for card in current],
        "backlog": backlog(),
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
