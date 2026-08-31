#!/usr/bin/env python3
"""Generate probability/statistics and ODE Draft candidates; no database writes."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


OM = "http://www.openmath.org/OpenMath"
PALS = "urn:pals:openmath:cd:v1"


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


def tag(name: str, body: str) -> str: return f"<{name}>{body}</{name}>"
def oms(cd: str, name: str) -> str: return f'<OMS cd="{cd}" name="{name}"/>'
def v(name: str) -> str: return f'<OMV name="{name}"/>'
def i(value: int) -> str: return f"<OMI>{value}</OMI>"
def app(op: str, *args: str) -> str: return tag("OMA", op + "".join(args))
def std(cd: str, name: str, *args: str) -> str: return app(oms(cd, name), *args)
def pals(name: str, *args: str) -> str: return app(f'<OMS cdbase="{PALS}" cd="pals1" name="{name}"/>', *args)
def plus(*args: str) -> str: return std("arith1", "plus", *args)
def times(*args: str) -> str: return std("arith1", "times", *args)
def minus(a: str, b: str) -> str: return std("arith1", "minus", a, b)
def neg(a: str) -> str: return std("arith1", "unary_minus", a)
def divide(a: str, b: str) -> str: return std("arith1", "divide", a, b)
def power(a: str, n: int) -> str: return std("arith1", "power", a, i(n))
def power_term(a: str, b: str) -> str: return std("arith1", "power", a, b)
def eq(a: str, b: str) -> str: return std("relation1", "eq", a, b)
def leq(a: str, b: str) -> str: return std("relation1", "leq", a, b)
def neq(a: str, b: str) -> str: return std("relation1", "neq", a, b)
def and_(*args: str) -> str: return std("logic1", "and", *args)
def implies(a: str, b: str) -> str: return std("logic1", "implies", a, b)
def inter(a: str, b: str) -> str: return std("set1", "intersect", a, b)
def binder(kind: str, names: tuple[str, ...], body: str) -> str:
    return tag("OMBIND", oms("quant1", kind) + tag("OMBVAR", "".join(v(name) for name in names)) + body)
def forall(names: tuple[str, ...], body: str) -> str: return binder("forall", names, body)
def typed_forall(names: tuple[str, ...], set_name: str, body: str) -> str:
    membership = tuple(std("set1", "in", v(name), oms("setname1", set_name)) for name in names)
    premise = membership[0] if len(membership) == 1 else and_(*membership)
    return forall(names, implies(premise, body))
def mixed_forall(names: tuple[str, ...], premise: str, body: str) -> str: return forall(names, implies(premise, body))
def lam(name: str, body: str) -> str: return tag("OMBIND", oms("fns1", "lambda") + tag("OMBVAR", v(name)) + body)
def deriv_at(parameter: str, body: str, point: str) -> str:
    return pals("apply", std("calculus1", "diff", lam(parameter, body)), point)
def xml(body: str) -> str: return f'<OMOBJ xmlns="{OM}" version="2.0">{body}</OMOBJ>'


def examples(path: str) -> list[str]:
    source = Path(path).read_text(encoding="utf-8")
    return [chunk.strip() for chunk in re.split(r"(?m)(?=^example )", source) if chunk.strip().startswith("example ")]


ODE_EXP_STEPS = (
    "setup: Define the proposed solution as a function of the independent variable.",
    "differentiate: Apply the chain rule to the exponential factor.",
    "substitute: Replace the derivative in the differential equation.",
    "simplify: Factor the common exponential term.",
    "conclude: Verify that the equation holds for every real point.",
)
ODE_LINEAR_STEPS = (
    "setup: Write the proposed function and its first derivative.",
    "differentiate: Use the derivative rule for the relevant elementary function.",
    "substitute: Insert both expressions into the first-order linear equation.",
    "cancel: Combine the homogeneous terms.",
    "conclude: Recover the stated forcing term.",
)
ODE_SECOND_STEPS = (
    "setup: Differentiate the proposed solution once.",
    "differentiate_again: Differentiate the first derivative.",
    "substitute: Insert the function and second derivative into the ODE.",
    "simplify: Cancel terms using the derivative identities.",
    "conclude: The constant-coefficient equation is satisfied.",
)
COMB_STEPS = (
    "setup: Interpret the binomial coefficient as a selection count.",
    "recurrence: Apply the relevant counting identity or boundary rule.",
    "simplify: Reduce the resulting natural-number expression.",
    "conclude: Obtain the claimed combinatorial count.",
)
COND_STEPS = (
    "setup: Record the measure and the measurable conditioning event.",
    "definition: Expand conditional probability through restriction and normalization.",
    "rewrite: Express the relevant intersection event.",
    "algebra: Rearrange the measure factors safely.",
    "conclude: Obtain the conditional-probability relation.",
)
MOMENT_STEPS = (
    "setup: State the random variable and probability measure assumptions.",
    "definition: Expand the expectation or variance expression.",
    "transform: Apply the corresponding linearity or scaling theorem.",
    "simplify: Normalize the real scalar expression.",
    "conclude: Obtain the stated moment identity or bound.",
)
BINOMIAL_STEPS = (
    "setup: Fix the trial count, success probability, and outcome count.",
    "model: Use the binomial probability-mass function.",
    "count: Insert the selection coefficient and success/failure powers.",
    "simplify: Evaluate the boundary or general mass expression.",
    "conclude: State the requested binomial probability.",
)


def make(identifier: str, profile: str, domain: str, topic: str, difficulty: str, statement: str, proposition: str, strategy: str, steps: tuple[str, ...], witness: str) -> Card:
    return Card(identifier, profile, domain, "undergraduate_year_2", topic, difficulty, statement, xml(proposition), strategy, steps, witness)


def ode_cards(witnesses: list[str]) -> list[Card]:
    x, c, k = v("x"), v("C"), v("k")
    e_growth = times(c, std("transc1", "exp", times(k, x)))
    e_decay = times(c, std("transc1", "exp", times(neg(k), x)))
    identity_minus_one = minus(x, i(1))
    two_x = times(i(2), x)
    sin_x, cos_x, exp_x = std("transc1", "sin", x), std("transc1", "cos", x), std("transc1", "exp", x)
    cards = [
        make("ode_separable_exponential_growth", "current_openmath_profile", "ordinary_differential_equations", "separable_equations", "standard", "For all real C, k, and x, the derivative at x of C*exp(k*x) equals k times C*exp(k*x).", typed_forall(("C", "k", "x"), "R", eq(deriv_at("t", times(v("C"), std("transc1", "exp", times(v("k"), v("t")))), x), times(k, e_growth))), "Verify the separated exponential family directly with the chain rule.", ODE_EXP_STEPS, witnesses[0]),
        make("ode_separable_exponential_decay", "current_openmath_profile", "ordinary_differential_equations", "separable_equations", "standard", "For all real C, k, and x, the derivative at x of C*exp(-k*x) equals -k times C*exp(-k*x).", typed_forall(("C", "k", "x"), "R", eq(deriv_at("t", times(v("C"), std("transc1", "exp", times(neg(v("k")), v("t")))), x), times(neg(k), e_decay))), "Verify a decaying separated solution using the exponential chain rule.", ODE_EXP_STEPS, witnesses[1]),
        make("ode_separable_zero_solution", "current_openmath_profile", "ordinary_differential_equations", "separable_equations", "introductory", "For every real x, the derivative at x of the zero function equals its square.", typed_forall(("x",), "R", eq(deriv_at("t", i(0), x), power(i(0), 2))), "Check the equilibrium solution of the nonlinear separable equation.", ODE_LINEAR_STEPS, witnesses[2]),
        make("ode_first_linear_homogeneous_unit", "current_openmath_profile", "ordinary_differential_equations", "first_order_linear", "standard", "For all real C and x, the derivative at x of C*exp(-x), plus C*exp(-x), equals 0.", typed_forall(("C", "x"), "R", eq(plus(deriv_at("t", times(v("C"), std("transc1", "exp", neg(v("t")))), x), times(c, std("transc1", "exp", neg(x)))), i(0))), "Substitute the exponential homogeneous solution into the linear equation.", ODE_LINEAR_STEPS, witnesses[3]),
        make("ode_first_linear_affine_particular", "current_openmath_profile", "ordinary_differential_equations", "first_order_linear", "standard", "For every real x, the derivative at x of x - 1, plus x - 1, equals x.", typed_forall(("x",), "R", eq(plus(deriv_at("t", minus(v("t"), i(1)), x), identity_minus_one), x)), "Differentiate the affine particular solution and simplify the linear operator.", ODE_LINEAR_STEPS, witnesses[4]),
        make("ode_first_linear_polynomial_forcing", "current_openmath_profile", "ordinary_differential_equations", "first_order_linear", "standard", "For every real x, the derivative at x of 2*x, plus 2*x, equals 2*x + 2.", typed_forall(("x",), "R", eq(plus(deriv_at("t", times(i(2), v("t")), x), two_x), plus(two_x, i(2)))), "Apply the first-order linear operator to a polynomial particular solution.", ODE_LINEAR_STEPS, witnesses[5]),
        make("ode_second_harmonic_sine", "current_openmath_profile", "ordinary_differential_equations", "second_order_constant_coefficient", "standard", "For every real x, the second derivative at x of sin(x), plus sin(x), equals 0.", typed_forall(("x",), "R", eq(plus(deriv_at("t", deriv_at("s", std("transc1", "sin", v("s")), v("t")), x), sin_x), i(0))), "Differentiate sine twice and use the harmonic-oscillator relation.", ODE_SECOND_STEPS, witnesses[6]),
        make("ode_second_harmonic_cosine", "current_openmath_profile", "ordinary_differential_equations", "second_order_constant_coefficient", "standard", "For every real x, the second derivative at x of cos(x), plus cos(x), equals 0.", typed_forall(("x",), "R", eq(plus(deriv_at("t", deriv_at("s", std("transc1", "cos", v("s")), v("t")), x), cos_x), i(0))), "Differentiate cosine twice and use the harmonic-oscillator relation.", ODE_SECOND_STEPS, witnesses[7]),
        make("ode_second_exponential_positive_root", "current_openmath_profile", "ordinary_differential_equations", "second_order_constant_coefficient", "standard", "For every real x, the second derivative at x of exp(x), minus exp(x), equals 0.", typed_forall(("x",), "R", eq(minus(deriv_at("t", deriv_at("s", std("transc1", "exp", v("s")), v("t")), x), exp_x), i(0))), "Use that the exponential is unchanged by either differentiation.", ODE_SECOND_STEPS, witnesses[8]),
        make("ode_second_zero_characteristic_identity", "current_openmath_profile", "ordinary_differential_equations", "second_order_constant_coefficient", "introductory", "For every real x, the second derivative at x of the identity function equals 0.", typed_forall(("x",), "R", eq(deriv_at("t", deriv_at("s", v("s"), v("t")), x), i(0))), "Differentiate the identity twice to obtain the zero characteristic-root solution.", ODE_SECOND_STEPS, witnesses[9]),
    ]
    assert len(cards) == len(witnesses) == 10
    return cards


def statistics_cards(witnesses: list[str]) -> list[Card]:
    profile = "requires_pals_probability_profile_v1"
    n, k, m, s, t, x, c, p = map(v, ("n", "k", "M", "S", "T", "X", "c", "p"))
    choose = lambda a, b: pals("choose", a, b)
    probability = lambda measure, event: pals("probability", measure, event)
    conditional = lambda measure, event, given: pals("conditional_probability", measure, event, given)
    variance = lambda rv, measure: pals("variance", rv, measure)
    expectation = lambda rv, measure: pals("expectation", rv, measure)
    binomial = lambda trials, prob, successes: pals("binomial_pmf", trials, prob, successes)
    finite = lambda measure: pals("finite_measure", measure)
    measurable = lambda event: pals("measurable_event", event)
    event = lambda value: pals("event", value)
    random_variable = lambda value: pals("random_variable", value)
    probability_measure = lambda measure: pals("probability_measure", measure)
    cards = [
        make("prob_choose_zero", profile, "probability_and_statistics", "combinatorics", "introductory", "For every natural number n, choose(n, 0) = 1.", typed_forall(("n",), "N", eq(choose(n, i(0)), i(1))), "Use the empty-selection boundary case.", COMB_STEPS, witnesses[0]),
        make("prob_choose_self", profile, "probability_and_statistics", "combinatorics", "introductory", "For every natural number n, choose(n, n) = 1.", typed_forall(("n",), "N", eq(choose(n, n), i(1))), "Use the all-elements selection boundary case.", COMB_STEPS, witnesses[1]),
        make("prob_choose_one", profile, "probability_and_statistics", "combinatorics", "introductory", "For every natural number n, choose(n, 1) = n.", typed_forall(("n",), "N", eq(choose(n, i(1)), n)), "Choose one item by specifying which of the n items is selected.", COMB_STEPS, witnesses[2]),
        make("prob_choose_pascal", profile, "probability_and_statistics", "combinatorics", "standard", "For natural n and k, choose(n + 1, k + 1) = choose(n, k) + choose(n, k + 1).", typed_forall(("n", "k"), "N", eq(choose(plus(n, i(1)), plus(k, i(1))), plus(choose(n, k), choose(n, plus(k, i(1)))))), "Partition selections by whether a distinguished element is chosen.", COMB_STEPS, witnesses[3]),
        make("prob_choose_symmetry", profile, "probability_and_statistics", "combinatorics", "standard", "For natural n and k with k ≤ n, choose(n, n - k) = choose(n, k).", typed_forall(("n", "k"), "N", implies(leq(k, n), eq(choose(n, minus(n, k)), choose(n, k)))), "Map each chosen subset to its complement.", COMB_STEPS, witnesses[4]),
        make("prob_choose_two", profile, "probability_and_statistics", "combinatorics", "standard", "For every natural number n, choose(n, 2) = n*(n - 1)/2.", typed_forall(("n",), "N", eq(choose(n, i(2)), divide(times(n, minus(n, i(1))), i(2)))), "Count ordered pairs of distinct elements, then divide by the two orders.", COMB_STEPS, witnesses[5]),
        make("prob_conditional_definition", profile, "probability_and_statistics", "conditional_probability", "standard", "For finite measure M and measurable events S and T, conditional_probability(M, T, S) = probability(M, S intersect T) / probability(M, S).", forall(("M", "S", "T"), implies(and_(finite(m), measurable(s), measurable(t)), eq(conditional(m, t, s), divide(probability(m, inter(s, t)), probability(m, s))))), "Expand the normalized restricted measure defining conditional probability.", COND_STEPS, witnesses[6]),
        make("prob_conditional_self", profile, "probability_and_statistics", "conditional_probability", "standard", "For finite measure M and measurable event S with positive finite probability, conditional_probability(M, S, S) = 1.", forall(("M", "S"), implies(and_(finite(m), measurable(s), neq(probability(m, s), i(0))), eq(conditional(m, s, s), i(1)))), "Apply the conditional-probability definition to the same event and cancel its nonzero mass.", COND_STEPS, witnesses[7]),
        make("prob_conditional_multiplication_rule", profile, "probability_and_statistics", "conditional_probability", "standard", "For finite measure M and measurable events S and T, conditional_probability(M, T, S)*probability(M, S) = probability(M, S intersect T).", forall(("M", "S", "T"), implies(and_(finite(m), measurable(s), measurable(t)), eq(times(conditional(m, t, s), probability(m, s)), probability(m, inter(s, t))))), "Multiply the conditional formula by the conditioning probability.", COND_STEPS, witnesses[8]),
        make("prob_bayes_formula", profile, "probability_and_statistics", "conditional_probability", "advanced", "For finite measure M and measurable events S and T, conditional_probability(M, T, S) = conditional_probability(M, S, T)*probability(M, T)/probability(M, S).", forall(("M", "S", "T"), implies(and_(finite(m), measurable(s), measurable(t)), eq(conditional(m, t, s), divide(times(conditional(m, s, t), probability(m, t)), probability(m, s))))), "Equate the two intersection probabilities and solve for the requested conditional probability.", COND_STEPS, witnesses[9]),
        make("prob_variance_nonnegative", profile, "probability_and_statistics", "variance", "introductory", "For random variable X under measure M, 0 ≤ Var(X; M).", forall(("M", "X"), implies(and_(finite(m), random_variable(x)), leq(i(0), variance(x, m)))), "Use the squared-deviation definition of variance.", MOMENT_STEPS, witnesses[10]),
        make("prob_variance_scaling", profile, "probability_and_statistics", "variance", "standard", "For real c and random variable X, Var(c*X; M) = c^2*Var(X; M).", forall(("M", "X", "c"), implies(and_(finite(m), random_variable(x)), eq(variance(pals("scalar_multiply_random_variable", c, x), m), times(power(c, 2), variance(x, m))))), "Factor the scalar out of the centered random variable and square it.", MOMENT_STEPS, witnesses[11]),
        make("prob_variance_translation", profile, "probability_and_statistics", "variance", "standard", "For probability measure M, random variable X, and real c, Var(X + c; M) = Var(X; M).", forall(("M", "X", "c"), implies(and_(probability_measure(m), random_variable(x)), eq(variance(pals("add_constant_random_variable", x, c), m), variance(x, m)))), "Centering removes an additive constant before squaring deviations.", MOMENT_STEPS, witnesses[12]),
        make("prob_expectation_constant", profile, "probability_and_statistics", "expectation", "introductory", "For probability measure M and real c, expectation(constant(c), M) = c.", forall(("M", "c"), implies(probability_measure(m), eq(expectation(pals("constant_random_variable", c), m), c))), "Integrate a constant against a probability measure of total mass one.", MOMENT_STEPS, witnesses[13]),
        make("prob_binomial_pmf", profile, "probability_and_statistics", "binomial_distribution", "advanced", "For natural n and k and real p with 0 ≤ p ≤ 1, BinomialPMF(n, p, k) = choose(n, k)*p^k*(1 - p)^(n - k).", mixed_forall(("n", "k", "p"), and_(std("set1", "in", n, oms("setname1", "N")), std("set1", "in", k, oms("setname1", "N")), std("set1", "in", p, oms("setname1", "R")), leq(i(0), p), leq(p, i(1))), eq(binomial(n, p, k), times(choose(n, k), power_term(p, k), power_term(minus(i(1), p), minus(n, k))))), "Use the binomial mass formula with the typed trial, outcome, and probability parameters.", BINOMIAL_STEPS, witnesses[14]),
        make("prob_binomial_zero_success", profile, "probability_and_statistics", "binomial_distribution", "standard", "For natural n and real p with 0 ≤ p ≤ 1, BinomialPMF(n, p, 0) = (1 - p)^n.", mixed_forall(("n", "p"), and_(std("set1", "in", n, oms("setname1", "N")), std("set1", "in", p, oms("setname1", "R")), leq(i(0), p), leq(p, i(1))), eq(binomial(n, p, i(0)), power_term(minus(i(1), p), n))), "Specialize the binomial mass formula to zero successes.", BINOMIAL_STEPS, witnesses[15]),
        make("prob_binomial_all_success", profile, "probability_and_statistics", "binomial_distribution", "standard", "For natural n and real p with 0 ≤ p ≤ 1, BinomialPMF(n, p, n) = p^n.", mixed_forall(("n", "p"), and_(std("set1", "in", n, oms("setname1", "N")), std("set1", "in", p, oms("setname1", "R")), leq(i(0), p), leq(p, i(1))), eq(binomial(n, p, n), power_term(p, n))), "Specialize the binomial mass formula to all successes.", BINOMIAL_STEPS, witnesses[16]),
    ]
    assert len(cards) == len(witnesses) == 17
    return cards


PROPOSED_PALS_PROBABILITY_PROFILE_V1 = {
    "terms": {
        "choose": ["Nat", "Nat"],
        "probability": ["Measure", "Event"],
        "conditional_probability": ["Measure", "Event", "Event"],
        "expectation": ["RandomVariable", "Measure"],
        "variance": ["RandomVariable", "Measure"],
        "binomial_pmf": ["Nat", "Probability", "Nat"],
        "constant_random_variable": ["Real"],
        "scalar_multiply_random_variable": ["Real", "RandomVariable"],
        "add_constant_random_variable": ["RandomVariable", "Real"],
    },
    "predicates": {"finite_measure": ["Measure"], "probability_measure": ["Measure"], "measurable_event": ["Event"], "event": ["Event"], "random_variable": ["RandomVariable"]},
    "note": "The current generic OpenMath profile does not contain these probability/data types. This profile is a minimal PALS extension proposal, not enabled production vocabulary.",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cards = ode_cards(examples("/private/tmp/test_ode_witnesses.lean")) + statistics_cards(examples("/private/tmp/test_probability_witnesses.lean"))
    assert len(cards) == 27 and len({card.id for card in cards}) == 27
    args.output.write_text(json.dumps({"schema_version": "pals.probability-ode-draft-candidates.v1", "current_openmath_cards": [asdict(card) for card in cards if card.profile == "current_openmath_profile"], "requires_probability_profile_cards": [asdict(card) for card in cards if card.profile != "current_openmath_profile"], "proposed_pals_probability_profile_v1": PROPOSED_PALS_PROBABILITY_PROFILE_V1}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
