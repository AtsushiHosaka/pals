#!/usr/bin/env python3
"""Generate Lean-verified high-school sequence/limit and proposed calculus Drafts.

The current-profile cards use only the existing PALS/OpenMath retrieval vocabulary.
The calculus cards are deliberately isolated behind the minimal proposed vocabulary
extension recorded in their `required_symbols` field.
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
PALS_CDBASE = "urn:pals:openmath:cd:v1"


@dataclass(frozen=True)
class Card:
    id: str
    domain: str
    level: str
    difficulty: str
    profile: str
    required_symbols: tuple[str, ...]
    canonical_statement: str
    openmath_xml: str
    proof_strategy: str
    sketch_steps: tuple[str, ...]
    lean_witness: str


def tag(name: str, body: str) -> str:
    return f"<{name}>{body}</{name}>"


def oms(cd: str, name: str, *, pals: bool = False) -> str:
    attrs = f' cd="{cd}" name="{name}"'
    if pals:
        attrs = f' cdbase="{PALS_CDBASE}"' + attrs
    return f"<OMS{attrs}/>"


def var(name: str) -> str:
    return f'<OMV name="{name}"/>'


def integer(value: int) -> str:
    return f"<OMI>{value}</OMI>"


def app(operator: str, *args: str) -> str:
    return tag("OMA", operator + "".join(args))


def standard(cd: str, name: str, *args: str) -> str:
    return app(oms(cd, name), *args)


def pals(name: str, *args: str) -> str:
    return app(oms("pals1", name, pals=True), *args)


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


def absolute(value: str) -> str:
    return standard("arith1", "abs", value)


def neg(value: str) -> str:
    return standard("arith1", "unary_minus", value)


def equal(left: str, right: str) -> str:
    return standard("relation1", "eq", left, right)


def neq(left: str, right: str) -> str:
    return standard("relation1", "neq", left, right)


def implies(left: str, right: str) -> str:
    return standard("logic1", "implies", left, right)


def conjunction(*args: str) -> str:
    return standard("logic1", "and", *args)


def binder(operator: str, names: tuple[str, ...], body: str, *, pals_binder: bool = False) -> str:
    return tag("OMBIND", oms("pals1" if pals_binder else "quant1", operator, pals=pals_binder) + tag("OMBVAR", "".join(var(name) for name in names)) + body)


def forall(names: tuple[str, ...], body: str) -> str:
    return binder("forall", names, body)


def forall_seq(names: tuple[str, ...], body: str) -> str:
    return binder("forall_real_sequence", names, body, pals_binder=True)


def lam(name: str, body: str) -> str:
    return tag("OMBIND", oms("fns1", "lambda") + tag("OMBVAR", var(name)) + body)


def sequence_lam(body: str) -> str:
    return binder("sequence_lambda", ("n",), body, pals_binder=True)


def index_real() -> str:
    return pals("index_to_real", var("n"))


def converges(sequence: str, limit: str) -> str:
    return pals("converges_to", sequence, limit)


def has_limit(function: str, point: str, limit: str) -> str:
    return pals("has_limit_at", function, point, limit)


def apply(function: str, value: str) -> str:
    return pals("apply", function, value)


def openmath(body: str) -> str:
    return f'<OMOBJ xmlns="{OPENMATH}" version="2.0">{body}</OMOBJ>'


def current_card(
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
        domain="high_school_sequences_and_limits",
        level="high_school",
        difficulty=difficulty,
        profile="current_openmath_profile",
        required_symbols=(),
        canonical_statement=statement,
        openmath_xml=openmath(proposition),
        proof_strategy=strategy,
        sketch_steps=steps,
        lean_witness=witness,
    )


def current_cards() -> list[Card]:
    n = index_real()
    one_over_n_plus_one = divide(integer(1), plus(n, integer(1)))
    n_over_n_plus_one = divide(n, plus(n, integer(1)))
    affine_ratio_a = divide(plus(integer(3), times(integer(2), n)), plus(integer(1), n))
    affine_ratio_b = divide(plus(integer(1), times(integer(3), n)), plus(integer(4), times(integer(2), n)))
    linear_over_quadratic = divide(power(n, 1), power(n, 2))
    quadratic_over_cubic = divide(power(n, 2), power(n, 3))
    four_over_n = divide(integer(4), n)
    sequence_steps = (
        "setup: State the sequence as a real-valued function of the natural index n.",
        "normalize: Rewrite its leading terms using the real embedding of n.",
        "bound_or_ratio: Compare numerator and denominator growth, or use a standard limit theorem.",
        "limit: Evaluate the resulting constant or vanishing factor.",
        "conclude: Translate the calculation back to convergence of the original sequence.",
    )
    result = [
        current_card(
            "hs_seq_reciprocal_n_plus_one_to_zero",
            "Show that the real sequence 1/(n + 1) converges to 0.",
            converges(sequence_lam(one_over_n_plus_one), integer(0)),
            "Apply the reciprocal-sequence limit after shifting the natural index by one.",
            sequence_steps,
            "example : Filter.Tendsto (fun n : ℕ => (1 : ℝ) / (n + 1)) Filter.atTop (nhds 0) := by\n  simpa using (tendsto_one_div_add_atTop_nhds_zero_nat : Filter.Tendsto (fun n : ℕ => (1 : ℝ) / ((n : ℝ) + 1)) Filter.atTop (nhds 0))",
            difficulty="standard",
        ),
        current_card(
            "hs_seq_ratio_n_over_n_plus_one_to_one",
            "Show that the real sequence n/(n + 1) converges to 1.",
            converges(sequence_lam(n_over_n_plus_one), integer(1)),
            "Divide numerator and denominator by the leading power of n, or invoke the standard affine-ratio limit.",
            sequence_steps,
            "example : Filter.Tendsto (fun n : ℕ => (n : ℝ) / (n + 1)) Filter.atTop (nhds 1) := by\n  simpa using (tendsto_natCast_div_add_atTop (1 : ℝ))",
            difficulty="standard",
        ),
        current_card(
            "hs_seq_affine_ratio_two_n_plus_three_to_two",
            "Show that the real sequence (2n + 3)/(n + 1) converges to 2.",
            converges(sequence_lam(affine_ratio_a), integer(2)),
            "Use the quotient of affine functions: the limit is the ratio of their leading coefficients.",
            sequence_steps,
            "example : Filter.Tendsto (fun n : ℕ => (3 + 2 * (n : ℝ)) / (1 + (n : ℝ))) Filter.atTop (nhds 2) := by\n  simpa using (tendsto_add_mul_div_add_mul_atTop_nhds (3 : ℝ) 1 2 (by norm_num : (1 : ℝ) ≠ 0))",
            difficulty="standard",
        ),
        current_card(
            "hs_seq_affine_ratio_three_n_plus_one_to_three_halves",
            "Show that the real sequence (3n + 1)/(2n + 4) converges to 3/2.",
            converges(sequence_lam(affine_ratio_b), divide(integer(3), integer(2))),
            "Use the quotient of affine functions and retain the leading coefficients 3 and 2.",
            sequence_steps,
            "example : Filter.Tendsto (fun n : ℕ => (1 + 3 * (n : ℝ)) / (4 + 2 * (n : ℝ))) Filter.atTop (nhds ((3 : ℝ) / 2)) := by\n  simpa [add_comm, add_left_comm, add_assoc] using (tendsto_add_mul_div_add_mul_atTop_nhds (1 : ℝ) 4 3 (by norm_num : (2 : ℝ) ≠ 0))",
            difficulty="advanced",
        ),
        current_card(
            "hs_seq_linear_over_quadratic_to_zero",
            "Show that the real sequence n/n^2 converges to 0.",
            converges(sequence_lam(linear_over_quadratic), integer(0)),
            "Compare the numerator degree one with the denominator degree two.",
            sequence_steps,
            "example : Filter.Tendsto (fun n : ℕ => ((n : ℝ)^1) / ((n : ℝ)^2)) Filter.atTop (nhds 0) := by\n  exact (tendsto_pow_div_pow_atTop_zero (by norm_num)).comp tendsto_natCast_atTop_atTop",
            difficulty="advanced",
        ),
        current_card(
            "hs_seq_quadratic_over_cubic_to_zero",
            "Show that the real sequence n^2/n^3 converges to 0.",
            converges(sequence_lam(quadratic_over_cubic), integer(0)),
            "Compare the numerator degree two with the denominator degree three.",
            sequence_steps,
            "example : Filter.Tendsto (fun n : ℕ => ((n : ℝ)^2) / ((n : ℝ)^3)) Filter.atTop (nhds 0) := by\n  exact (tendsto_pow_div_pow_atTop_zero (by norm_num)).comp tendsto_natCast_atTop_atTop",
            difficulty="advanced",
        ),
        current_card(
            "hs_seq_four_over_n_to_zero",
            "Show that the real sequence 4/n converges to 0.",
            converges(sequence_lam(four_over_n), integer(0)),
            "Use the fact that a fixed constant divided by an unbounded natural index tends to zero.",
            sequence_steps,
            "example : Filter.Tendsto (fun n : ℕ => (4 : ℝ) / n) Filter.atTop (nhds 0) := by\n  simpa using (tendsto_const_div_atTop_nhds_zero_nat (4 : ℝ))",
            difficulty="standard",
        ),
    ]
    u, v, L, M, c = map(var, ("u", "v", "L", "M", "c"))
    law_steps = (
        "setup: Bind the two convergent sequences and their proposed limits.",
        "hypotheses: Record the convergence hypotheses and any nonzero limit condition.",
        "closure: Apply continuity of the displayed arithmetic operation on real limits.",
        "target: Compute the operation on L and M.",
        "conclude: State convergence of the transformed sequence.",
    )
    def sequence_law(identifier: str, statement: str, conclusion: str, witness: str, strategy: str, *, nonzero: bool = False, unary: bool = False) -> Card:
        if unary:
            premise = converges(u, L)
            body = forall(("L",), implies(premise, conclusion))
            prop = forall_seq(("u",), forall(("L",), implies(premise, conclusion)))
        else:
            premises = [converges(u, L), converges(v, M)]
            if nonzero:
                premises.append(neq(M, integer(0)))
            prop = forall_seq(("u", "v"), forall(("L", "M"), implies(conjunction(*premises), conclusion)))
        return current_card(identifier, statement, prop, strategy, law_steps, witness, difficulty="advanced")
    result.extend([
        sequence_law("hs_seq_sum_limit_law", "Show that if real sequences u and v converge to L and M, then their termwise sum converges to L + M.", converges(pals("sequence_add", u, v), plus(L, M)), "example : ∀ (u v : ℕ → ℝ) (L M : ℝ), Filter.Tendsto u Filter.atTop (nhds L) → Filter.Tendsto v Filter.atTop (nhds M) → Filter.Tendsto (fun n => u n + v n) Filter.atTop (nhds (L + M)) := by\n  intro u v L M hu hv\n  exact hu.add hv", "Use continuity of addition at the pair of sequence limits."),
        sequence_law("hs_seq_difference_limit_law", "Show that if real sequences u and v converge to L and M, then their termwise difference converges to L - M.", converges(pals("sequence_sub", u, v), minus(L, M)), "example : ∀ (u v : ℕ → ℝ) (L M : ℝ), Filter.Tendsto u Filter.atTop (nhds L) → Filter.Tendsto v Filter.atTop (nhds M) → Filter.Tendsto (fun n => u n - v n) Filter.atTop (nhds (L - M)) := by\n  intro u v L M hu hv\n  exact hu.sub hv", "Use continuity of subtraction at the pair of sequence limits."),
        sequence_law("hs_seq_product_limit_law", "Show that if real sequences u and v converge to L and M, then their termwise product converges to L*M.", converges(pals("sequence_mul", u, v), times(L, M)), "example : ∀ (u v : ℕ → ℝ) (L M : ℝ), Filter.Tendsto u Filter.atTop (nhds L) → Filter.Tendsto v Filter.atTop (nhds M) → Filter.Tendsto (fun n => u n * v n) Filter.atTop (nhds (L * M)) := by\n  intro u v L M hu hv\n  exact hu.mul hv", "Use continuity of multiplication at the pair of sequence limits."),
        sequence_law("hs_seq_quotient_limit_law", "Show that if real sequences u and v converge to L and nonzero M, then their termwise quotient converges to L/M.", converges(pals("sequence_div", u, v), divide(L, M)), "example : ∀ (u v : ℕ → ℝ) (L M : ℝ), Filter.Tendsto u Filter.atTop (nhds L) → Filter.Tendsto v Filter.atTop (nhds M) → M ≠ 0 → Filter.Tendsto (fun n => u n / v n) Filter.atTop (nhds (L / M)) := by\n  intro u v L M hu hv hM\n  exact hu.div hv hM", "Use continuity of division away from a zero denominator limit.", nonzero=True),
        current_card("hs_seq_scalar_limit_law", "Show that if sequence u converges to L, then termwise scaling by real c converges to c*L.", forall_seq(("u",), forall(("L", "c"), implies(converges(u, L), converges(pals("sequence_scale", c, u), times(c, L))))), "Apply continuity of scalar multiplication by the fixed real c.", law_steps, "example : ∀ (u : ℕ → ℝ) (L c : ℝ), Filter.Tendsto u Filter.atTop (nhds L) → Filter.Tendsto (fun n => c * u n) Filter.atTop (nhds (c * L)) := by\n  intro u L c hu\n  exact hu.const_mul c", difficulty="advanced"),
        sequence_law("hs_seq_negative_limit_law", "Show that if sequence u converges to L, then termwise negation converges to -L.", converges(pals("sequence_neg", u), neg(L)), "example : ∀ (u : ℕ → ℝ) (L : ℝ), Filter.Tendsto u Filter.atTop (nhds L) → Filter.Tendsto (fun n => -u n) Filter.atTop (nhds (-L)) := by\n  intro u L hu\n  exact hu.neg", "Apply continuity of negation at the sequence limit.", unary=True),
    ])
    x, a = var("x"), var("a")
    limit_steps = (
        "setup: Fix the approach point a and write the displayed function as a real lambda term.",
        "continuity: Establish continuity of each polynomial, absolute-value, or rational component at a.",
        "denominator: For rational expressions, prove that the denominator at a is nonzero.",
        "transport: Restrict the neighborhood to the punctured neighborhood of a.",
        "evaluate: Evaluate the continuous expression at a.",
        "conclude: State the punctured-point limit.",
    )
    def limit_card(identifier: str, statement: str, function_body: str, value: str, witness: str, strategy: str, *, difficulty: str) -> Card:
        return current_card(identifier, statement, forall(("a",), has_limit(lam("x", function_body), a, value)), strategy, limit_steps, witness, difficulty=difficulty)
    result.extend([
        limit_card("hs_limit_square_at_a", "Show that for every real a, lim_{x→a} x^2 = a^2.", power(x, 2), power(a, 2), "example (a : ℝ) : Filter.Tendsto (fun x : ℝ => x^2) (nhdsWithin a {a}ᶜ) (nhds (a^2)) := by\n  exact ((continuousAt_id.pow 2).tendsto).mono_left inf_le_left", "Use continuity of the square function and restrict its neighborhood to the punctured neighborhood.", difficulty="standard"),
        limit_card("hs_limit_cube_at_a", "Show that for every real a, lim_{x→a} x^3 = a^3.", power(x, 3), power(a, 3), "example (a : ℝ) : Filter.Tendsto (fun x : ℝ => x^3) (nhdsWithin a {a}ᶜ) (nhds (a^3)) := by\n  exact ((continuousAt_id.pow 3).tendsto).mono_left inf_le_left", "Use continuity of the cubic polynomial.", difficulty="standard"),
        limit_card("hs_limit_quadratic_polynomial_at_a", "Show that for every real a, lim_{x→a} (2x^2 - 3x + 1) = 2a^2 - 3a + 1.", plus(minus(times(integer(2), power(x, 2)), times(integer(3), x)), integer(1)), plus(minus(times(integer(2), power(a, 2)), times(integer(3), a)), integer(1)), "example (a : ℝ) : Filter.Tendsto (fun x : ℝ => 2*x^2 - 3*x + 1) (nhdsWithin a {a}ᶜ) (nhds (2*a^2 - 3*a + 1)) := by\n  exact ((by fun_prop : ContinuousAt (fun x : ℝ => 2*x^2 - 3*x + 1) a).tendsto).mono_left inf_le_left", "Build the polynomial from continuous addition, multiplication, and powers.", difficulty="standard"),
        limit_card("hs_limit_abs_at_a", "Show that for every real a, lim_{x→a} |x| = |a|.", absolute(x), absolute(a), "example (a : ℝ) : Filter.Tendsto (fun x : ℝ => |x|) (nhdsWithin a {a}ᶜ) (nhds |a|) := by\n  exact (continuousAt_id.abs.tendsto).mono_left inf_le_left", "Use continuity of absolute value.", difficulty="standard"),
        limit_card("hs_limit_rational_square_minus_one_at_a", "Show that for every real a, lim_{x→a} (x^2 - 1)/(x^2 + 1) = (a^2 - 1)/(a^2 + 1).", divide(minus(power(x, 2), integer(1)), plus(power(x, 2), integer(1))), divide(minus(power(a, 2), integer(1)), plus(power(a, 2), integer(1))), "example (a : ℝ) : Filter.Tendsto (fun x : ℝ => (x^2 - 1) / (x^2 + 1)) (nhdsWithin a {a}ᶜ) (nhds ((a^2 - 1) / (a^2 + 1))) := by\n  have h_ne : a^2 + 1 ≠ 0 := by nlinarith [sq_nonneg a]\n  exact (((((continuousAt_id.pow 2).sub continuousAt_const).div ((continuousAt_id.pow 2).add continuousAt_const) h_ne).tendsto).mono_left inf_le_left)", "Show x^2 + 1 is positive, then apply the quotient limit rule.", difficulty="advanced"),
        limit_card("hs_limit_one_over_square_plus_one_at_a", "Show that for every real a, lim_{x→a} 1/(x^2 + 1) = 1/(a^2 + 1).", divide(integer(1), plus(power(x, 2), integer(1))), divide(integer(1), plus(power(a, 2), integer(1))), "example (a : ℝ) : Filter.Tendsto (fun x : ℝ => 1 / (x^2 + 1)) (nhdsWithin a {a}ᶜ) (nhds (1 / (a^2 + 1))) := by\n  have h_ne : a^2 + 1 ≠ 0 := by nlinarith [sq_nonneg a]\n  exact (((continuousAt_const.div ((continuousAt_id.pow 2).add continuousAt_const) h_ne).tendsto).mono_left inf_le_left)", "Use positivity of x^2 + 1 to justify the reciprocal limit rule.", difficulty="advanced"),
        limit_card("hs_limit_affine_over_square_plus_one_at_a", "Show that for every real a, lim_{x→a} (2x + 1)/(x^2 + 1) = (2a + 1)/(a^2 + 1).", divide(plus(times(integer(2), x), integer(1)), plus(power(x, 2), integer(1))), divide(plus(times(integer(2), a), integer(1)), plus(power(a, 2), integer(1))), "example (a : ℝ) : Filter.Tendsto (fun x : ℝ => (2*x + 1) / (x^2 + 1)) (nhdsWithin a {a}ᶜ) (nhds ((2*a + 1) / (a^2 + 1))) := by\n  have h_ne : a^2 + 1 ≠ 0 := by nlinarith [sq_nonneg a]\n  exact (((((continuousAt_const.mul continuousAt_id).add continuousAt_const).div ((continuousAt_id.pow 2).add continuousAt_const) h_ne).tendsto).mono_left inf_le_left)", "Combine an affine numerator with a strictly positive quadratic denominator.", difficulty="advanced"),
        limit_card("hs_limit_neighbor_product_at_a", "Show that for every real a, lim_{x→a} x(x + 1) = a(a + 1).", times(x, plus(x, integer(1))), times(a, plus(a, integer(1))), "example (a : ℝ) : Filter.Tendsto (fun x : ℝ => x * (x + 1)) (nhdsWithin a {a}ᶜ) (nhds (a * (a + 1))) := by\n  exact ((continuousAt_id.mul (continuousAt_id.add continuousAt_const)).tendsto).mono_left inf_le_left", "Apply the product law to the identity and shifted identity functions.", difficulty="standard"),
        limit_card("hs_limit_fourth_plus_square_at_a", "Show that for every real a, lim_{x→a} (x^4 + x^2) = a^4 + a^2.", plus(power(x, 4), power(x, 2)), plus(power(a, 4), power(a, 2)), "example (a : ℝ) : Filter.Tendsto (fun x : ℝ => x^4 + x^2) (nhdsWithin a {a}ᶜ) (nhds (a^4 + a^2)) := by\n  exact (((continuousAt_id.pow 4).add (continuousAt_id.pow 2)).tendsto).mono_left inf_le_left", "Use the sum law for continuous polynomial functions.", difficulty="standard"),
    ])
    return result


def calculus_card(identifier: str, statement: str, proposition: str, strategy: str, steps: tuple[str, ...], witness: str, *, difficulty: str, required_symbols: tuple[str, ...]) -> Card:
    return Card(identifier, "calculus", "high_school_and_early_university", difficulty, "proposed_calculus_extension", required_symbols, statement, openmath(proposition), strategy, steps, witness)


def calculus_cards() -> list[Card]:
    x, a = var("x"), var("a")
    diff_steps = (
        "setup: Fix the evaluation point a and write the function as a real lambda term.",
        "decompose: Identify the elementary polynomial, product, shift, or quotient components.",
        "differentiate: Apply the corresponding derivative rule.",
        "simplify: Substitute x = a and collect the algebraic terms.",
        "conclude: State the derivative value at a.",
    )
    integral_steps = (
        "setup: Record the oriented integration interval and the real integrand.",
        "antiderivative: Select a polynomial antiderivative or standard integral formula.",
        "endpoints: Evaluate the antiderivative at the upper and lower endpoints.",
        "subtract: Take the oriented upper-minus-lower difference.",
        "conclude: Simplify to the stated definite-integral value.",
    )
    def derivative(identifier: str, statement: str, body: str, rhs: str, witness: str, strategy: str, *, premise: str | None = None, difficulty: str = "standard") -> Card:
        proposition = equal(apply(app(oms("calculus1", "diff"), lam("x", body)), a), rhs)
        if premise is not None:
            proposition = implies(premise, proposition)
        return calculus_card(identifier, statement, forall(("a",), proposition), strategy, diff_steps, witness, difficulty=difficulty, required_symbols=("calculus1:diff",))
    cards = [
        derivative("calc_derivative_square", "Show that for every real a, the derivative of x^2 at a is 2a.", power(x, 2), times(integer(2), a), "example (a : ℝ) : deriv (fun x : ℝ => x^2) a = 2*a := by\n  simpa [mul_comm] using (hasDerivAt_pow 2 a).deriv", "Apply the power rule with exponent two."),
        derivative("calc_derivative_cubic_minus_linear", "Show that for every real a, the derivative of x^3 - 2x at a is 3a^2 - 2.", minus(power(x, 3), times(integer(2), x)), minus(times(integer(3), power(a, 2)), integer(2)), "example (a : ℝ) : deriv (fun x : ℝ => x^3 - 2*x) a = 3*a^2 - 2 := by\n  have h1 : HasDerivAt (fun x : ℝ => x^3) (3*a^2) a := by\n    simpa using (hasDerivAt_pow 3 a)\n  have h2 : HasDerivAt (fun x : ℝ => 2*x) 2 a := by\n    simpa [id] using (hasDerivAt_id a).const_mul (2 : ℝ)\n  exact (h1.sub h2).deriv", "Combine the power rule with linearity of differentiation.", difficulty="advanced"),
        derivative("calc_derivative_neighbor_product", "Show that for every real a, the derivative of x(x + 1) at a is 2a + 1.", times(x, plus(x, integer(1))), plus(times(integer(2), a), integer(1)), "example (a : ℝ) : deriv (fun x : ℝ => x * (x + 1)) a = 2*a + 1 := by\n  have h1 := hasDerivAt_id a\n  have h2 := h1.add_const (1 : ℝ)\n  convert (h1.mul h2).deriv using 1 <;> simp <;> ring", "Use the product rule for x and x + 1."),
        derivative("calc_derivative_shifted_square", "Show that for every real a, the derivative of (x + 1)^2 at a is 2(a + 1).", power(plus(x, integer(1)), 2), times(integer(2), plus(a, integer(1))), "example (a : ℝ) : deriv (fun x : ℝ => (x + 1)^2) a = 2*(a + 1) := by\n  have h : HasDerivAt (fun x : ℝ => x + 1) 1 a := (hasDerivAt_id a).add_const 1\n  convert (h.pow 2).deriv using 1 <;> simp [id] <;> ring", "Apply the chain rule to the shifted linear function.", difficulty="advanced"),
        derivative("calc_derivative_reciprocal", "Show that for every nonzero real a, the derivative of 1/x at a is -1/a^2.", divide(integer(1), x), neg(divide(integer(1), power(a, 2))), "example (a : ℝ) (ha : a ≠ 0) : deriv (fun x : ℝ => 1 / x) a = -(1 / a^2) := by\n  have h : HasDerivAt (fun x : ℝ => 1 / x) ((0 * a - 1 * 1) / a^2) a := (hasDerivAt_const a 1).div (hasDerivAt_id a) ha\n  convert h.deriv using 1 <;> simp [id] <;> ring", "Use the quotient rule and the nonzero-denominator hypothesis.", premise=neq(a, integer(0)), difficulty="advanced"),
    ]
    def integral(identifier: str, statement: str, lower: int, upper: int, body: str, value: str, witness: str, strategy: str, *, difficulty: str = "standard") -> Card:
        interval = app(oms("interval1", "oriented_interval"), integer(lower), integer(upper))
        prop = equal(app(oms("calculus1", "defint"), interval, lam("x", body)), value)
        return calculus_card(identifier, statement, prop, strategy, integral_steps, witness, difficulty=difficulty, required_symbols=("calculus1:defint", "interval1:oriented_interval"))
    cards.extend([
        integral("calc_integral_x_zero_one", "Show that the definite integral of x from 0 to 1 is 1/2.", 0, 1, x, divide(integer(1), integer(2)), "example : (∫ x : ℝ in 0..1, x) = 1/2 := by\n  norm_num [integral_id]", "Use the antiderivative x^2/2."),
        integral("calc_integral_square_zero_one", "Show that the definite integral of x^2 from 0 to 1 is 1/3.", 0, 1, power(x, 2), divide(integer(1), integer(3)), "example : (∫ x : ℝ in 0..1, x^2) = 1/3 := by\n  norm_num [integral_pow]", "Use the power-rule antiderivative x^3/3."),
        integral("calc_integral_cubic_zero_two", "Show that the definite integral of x^3 from 0 to 2 is 4.", 0, 2, power(x, 3), integer(4), "example : (∫ x : ℝ in 0..2, x^3) = 4 := by\n  norm_num [integral_pow]", "Use the power-rule antiderivative x^4/4."),
        integral("calc_integral_constant_two_five", "Show that the definite integral of 1 from 2 to 5 is 3.", 2, 5, integer(1), integer(3), "example : (∫ x : ℝ in 2..5, (1 : ℝ)) = 3 := by\n  norm_num [integral_one]", "Interpret the integral of one as the oriented interval length."),
    ])
    return cards


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    current = current_cards()
    for card in current:
        validate_openmath_statement_semantics(card.openmath_xml, card.canonical_statement)
    cards = current + calculus_cards()
    identifiers = [card.id for card in cards]
    if len(identifiers) != len(set(identifiers)):
        raise RuntimeError("duplicate candidate identifiers")
    if not all(4 <= len(card.sketch_steps) <= 8 for card in cards):
        raise RuntimeError("every card must contain four to eight meaningful sketch steps")
    payload = {
        "schema_version": "pals.high-school-sequences-limits-and-calculus-candidates.v1",
        "source": "PALS first-party authored, Lean-verified candidate set",
        "current_profile_card_count": len(current),
        "proposed_calculus_extension_card_count": len(cards) - len(current),
        "notes": {
            "current_profile": "Validated by the current generic OpenMath statement validator.",
            "proposed_calculus_extension": "Requires explicit registration of calculus1:diff, calculus1:defint, and interval1:oriented_interval before it can enter the generic validator.",
        },
        "cards": [asdict(card) for card in cards],
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
