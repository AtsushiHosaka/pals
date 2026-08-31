#!/usr/bin/env python3
"""Build a local, first-party candidate set for university-level Draft coverage.

This creates an authoring manifest only.  It intentionally performs no database
or packaged-seed mutation; its validation hooks make the artifact safe to review
before a separate publication decision.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pals-agent"))

from pals_agent.openmath import (  # noqa: E402
    PALS_OPENMATH_CDBASE,
    canonicalize_retrieval_openmath_xml,
    validate_canonical_retrieval_openmath_xml,
    validate_openmath_statement_semantics,
)


OPENMATH = "http://www.openmath.org/OpenMath"


@dataclass(frozen=True)
class Card:
    id: str
    domain: str
    difficulty: str
    canonical_statement: str
    openmath_xml: str
    proof_strategy: str
    sketch_steps: tuple[str, ...]
    lean_witness: str


def tag(name: str, body: str) -> str:
    return f"<{name}>{body}</{name}>"


def oms(cd: str, name: str, *, pals_symbol: bool = False) -> str:
    cdbase = f' cdbase="{PALS_OPENMATH_CDBASE}"' if pals_symbol else ""
    return f'<OMS{cdbase} cd="{cd}" name="{name}"/>'


def v(name: str) -> str:
    return f'<OMV name="{name}"/>'


def n(value: int) -> str:
    return f"<OMI>{value}</OMI>"


def app(operator: str, *arguments: str) -> str:
    return tag("OMA", operator + "".join(arguments))


def std(cd: str, name: str, *arguments: str) -> str:
    return app(oms(cd, name), *arguments)


def pals(name: str, *arguments: str) -> str:
    return app(oms("pals1", name, pals_symbol=True), *arguments)


def add(*values: str) -> str:
    return std("arith1", "plus", *values)


def mul(*values: str) -> str:
    return std("arith1", "times", *values)


def sub(left: str, right: str) -> str:
    return std("arith1", "minus", left, right)


def div(left: str, right: str) -> str:
    return std("arith1", "divide", left, right)


def pow_(base: str, exponent: str | int) -> str:
    return std("arith1", "power", base, n(exponent) if isinstance(exponent, int) else exponent)


def abs_(value: str) -> str:
    return std("arith1", "abs", value)


def eq(left: str, right: str) -> str:
    return std("relation1", "eq", left, right)


def le(left: str, right: str) -> str:
    return std("relation1", "leq", left, right)


def lt(left: str, right: str) -> str:
    return std("relation1", "lt", left, right)


def implies(premise: str, conclusion: str) -> str:
    return std("logic1", "implies", premise, conclusion)


def iff(left: str, right: str) -> str:
    return std("logic1", "equivalent", left, right)


def and_(*values: str) -> str:
    return std("logic1", "and", *values)


def union(*values: str) -> str:
    return std("set1", "union", *values)


def inter(*values: str) -> str:
    return std("set1", "intersect", *values)


def diff(left: str, right: str) -> str:
    return std("set1", "setdiff", left, right)


def subset(left: str, right: str) -> str:
    return std("set1", "subset", left, right)


def product(left: str, right: str) -> str:
    return std("set1", "cartesian_product", left, right)


def image(function: str, source: str) -> str:
    return std("set1", "map", function, source)


def lambda_(name: str, body: str) -> str:
    return tag("OMBIND", oms("fns1", "lambda") + tag("OMBVAR", v(name)) + body)


def forall(names: tuple[str, ...], body: str) -> str:
    return tag("OMBIND", oms("quant1", "forall") + tag("OMBVAR", "".join(v(name) for name in names)) + body)


def typed_forall(names: tuple[str, ...], set_name: str, body: str) -> str:
    memberships = tuple(std("set1", "in", v(name), oms("setname1", set_name)) for name in names)
    premise = memberships[0] if len(memberships) == 1 else and_(*memberships)
    return forall(names, implies(premise, body))


def omobj(body: str) -> str:
    return f'<OMOBJ xmlns="{OPENMATH}" version="2.0">{body}</OMOBJ>'


def card(
    identifier: str,
    domain: str,
    difficulty: str,
    statement: str,
    proposition: str,
    strategy: str,
    steps: tuple[str, ...],
    witness: str,
) -> Card:
    if not 4 <= len(steps) <= 8:
        raise ValueError(f"{identifier}: sketch_steps must have 4..8 entries")
    xml = omobj(proposition)
    # Statement-faithfulness intentionally runs before alpha-normalization: its
    # variable names are part of the author-facing canonical statement.  The
    # second check independently proves that the exact same proposition is
    # admissible as a closed retrieval artifact after PFI canonicalization.
    validate_openmath_statement_semantics(xml, statement)
    canonical = canonicalize_retrieval_openmath_xml(xml)
    validate_canonical_retrieval_openmath_xml(canonical)
    return Card(identifier, domain, difficulty, statement, xml, strategy, steps, witness)


def linear_cards() -> list[Card]:
    a = v("A")
    domain = pals("domain", a)
    rank = pals("rank", a)
    nullity = pals("nullity", a)
    dimension = pals("dimension", domain)
    assumptions = and_(pals("linear_map", a), pals("finite_dimensional", domain))
    prefix = "If A is a linear map and domain of A is finite-dimensional, "
    witness_prelude = (
        "{K V W : Type*} [Field K] [AddCommGroup V] [Module K V] "
        "[FiniteDimensional K V] [AddCommGroup W] [Module K W] "
        "(A : V →ₗ[K] W)"
    )
    return [
        card(
            "univ_linear_rank_le_domain_dimension",
            "university_linear_algebra",
            "intermediate",
            prefix + "rank(A) is at most dimension(domain(A)).",
            forall(("A",), implies(assumptions, le(rank, dimension))),
            "Apply the finite-dimensional range bound for a linear map.",
            (
                "setup: Fix a field and finite-dimensional domain V for the linear map A.",
                "translate: Read rank(A) as the dimension of range(A).",
                "apply_theorem: Apply the range-dimension bound for linear maps.",
                "conclude: The rank cannot exceed dimension(V).",
            ),
            f"example {witness_prelude} : Module.finrank K (LinearMap.range A) ≤ Module.finrank K V := LinearMap.finrank_range_le A",
        ),
        card(
            "univ_linear_nullity_le_domain_dimension",
            "university_linear_algebra",
            "intermediate",
            prefix + "nullity(A) is at most dimension(domain(A)).",
            forall(("A",), implies(assumptions, le(nullity, dimension))),
            "Combine rank-nullity with nonnegativity of the rank.",
            (
                "setup: Fix A with finite-dimensional domain V.",
                "apply_theorem: Write rank(A) + nullity(A) = dimension(V).",
                "derive: Use nonnegativity of rank(A).",
                "conclude: Nullity(A) is bounded by dimension(V).",
            ),
            f"example {witness_prelude} : Module.finrank K (LinearMap.ker A) ≤ Module.finrank K V := by\n  have h := LinearMap.finrank_range_add_finrank_ker A\n  omega",
        ),
        card(
            "univ_linear_rank_deficit_positive_nullity",
            "university_linear_algebra",
            "advanced",
            "For a linear map A with finite-dimensional domain, rank(A) < dimension(domain(A)) entails 0 < nullity(A).",
            forall(("A",), implies(and_(assumptions, lt(rank, dimension)), lt(n(0), nullity))),
            "Use rank-nullity to turn a strict rank deficit into a positive kernel dimension.",
            (
                "setup: Fix A and assume its rank is strictly below the domain dimension.",
                "apply_theorem: Expand dimension(V) using rank-nullity.",
                "derive: Rewrite the strict inequality as a positive natural-number remainder.",
                "interpret: Identify that remainder with nullity(A).",
                "conclude: The kernel has positive dimension.",
            ),
            f"example {witness_prelude} (hdeficit : Module.finrank K (LinearMap.range A) < Module.finrank K V) : 0 < Module.finrank K (LinearMap.ker A) := by\n  have h := LinearMap.finrank_range_add_finrank_ker A\n  omega",
        ),
        card(
            "univ_linear_full_rank_zero_nullity",
            "university_linear_algebra",
            "advanced",
            "For a linear map A with finite-dimensional domain, rank(A) = dimension(domain(A)) entails nullity(A) = 0.",
            forall(("A",), implies(and_(assumptions, eq(rank, dimension)), eq(nullity, n(0)))),
            "Substitute the full-rank hypothesis into rank-nullity and cancel the common term.",
            (
                "setup: Fix A and assume that its rank equals the domain dimension.",
                "apply_theorem: Write rank(A) + nullity(A) = dimension(V).",
                "substitute: Replace rank(A) by dimension(V).",
                "derive: Cancel the equal dimension terms in the natural-number equality.",
                "conclude: Nullity(A) is zero.",
            ),
            f"example {witness_prelude} (hfull : Module.finrank K (LinearMap.range A) = Module.finrank K V) : Module.finrank K (LinearMap.ker A) = 0 := by\n  have h := LinearMap.finrank_range_add_finrank_ker A\n  omega",
        ),
        card(
            "univ_linear_full_nullity_zero_rank",
            "university_linear_algebra",
            "advanced",
            "For a linear map A with finite-dimensional domain, nullity(A) = dimension(domain(A)) entails rank(A) = 0.",
            forall(("A",), implies(and_(assumptions, eq(nullity, dimension)), eq(rank, n(0)))),
            "Use rank-nullity with the maximal-nullity hypothesis.",
            (
                "setup: Fix A and assume its nullity equals the domain dimension.",
                "apply_theorem: Expand dimension(V) by rank-nullity.",
                "substitute: Replace nullity(A) by dimension(V).",
                "derive: The remaining rank term must vanish.",
                "conclude: A has rank zero.",
            ),
            f"example {witness_prelude} (hfull : Module.finrank K (LinearMap.ker A) = Module.finrank K V) : Module.finrank K (LinearMap.range A) = 0 := by\n  have h := LinearMap.finrank_range_add_finrank_ker A\n  omega",
        ),
    ]


def analysis_cards() -> list[Card]:
    x, a, index = v("x"), v("a"), v("n")
    parameterized_denominator = add(sub(pow_(x, 2), mul(n(2), a, x)), pow_(a, 2), n(1))
    parameterized_rational = div(sub(x, a), parameterized_denominator)
    polynomial = sub(add(pow_(x, 2), mul(n(3), x)), n(1))
    polynomial_at_a = sub(add(pow_(a, 2), mul(n(3), a)), n(1))
    removable = div(sub(pow_(x, 2), n(4)), sub(x, n(2)))
    inverse_successor = div(n(1), add(pals("index_to_real", index), n(1)))
    ratio = div(pals("index_to_real", index), add(pals("index_to_real", index), n(2)))
    return [
        card(
            "univ_analysis_parameterized_rational_continuity",
            "university_real_analysis",
            "advanced",
            "If a is real, then the function x ↦ (x-a)/(x^2-(2*a*x)+a^2+1) is continuous on the real line.",
            typed_forall(("a",), "R", pals("continuous_on", oms("setname1", "R"), lambda_("x", parameterized_rational))),
            "Prove the quadratic denominator is strictly positive, then apply quotient continuity.",
            (
                "setup: Fix a real parameter a and set q(x)=x²-2ax+a²+1.",
                "rewrite: Complete the square to obtain q(x)=(x-a)²+1.",
                "derive: Use square nonnegativity to prove q(x)>0 for every real x.",
                "apply_theorem: The numerator and denominator are polynomial functions, hence continuous.",
                "conclude: Apply the quotient-continuity theorem using q(x)≠0.",
            ),
            "example (a : ℝ) : Continuous (fun x : ℝ => (x - a) / (x^2 - 2*a*x + a^2 + 1)) := by\n  apply Continuous.div\n  · fun_prop\n  · fun_prop\n  · intro x\n    nlinarith [sq_nonneg (x - a)]",
        ),
        card(
            "univ_analysis_abs_rational_continuity",
            "university_real_analysis",
            "intermediate",
            "The function x ↦ |x|/(x^2+1) is continuous on the real line.",
            pals("continuous_on", oms("setname1", "R"), lambda_("x", div(abs_(x), add(pow_(x, 2), n(1))))),
            "Combine continuity of absolute value with a positive quadratic denominator.",
            (
                "setup: Let q(x)=x²+1.",
                "derive: Since x²≥0, q(x)>0 for all real x.",
                "apply_theorem: Absolute value and q are continuous functions.",
                "apply_theorem: Use quotient continuity with the nonvanishing denominator.",
                "conclude: The displayed rational absolute-value function is continuous everywhere.",
            ),
            "example : Continuous (fun x : ℝ => |x| / (x^2 + 1)) := by\n  apply Continuous.div\n  · fun_prop\n  · fun_prop\n  · intro x\n    nlinarith [sq_nonneg x]",
        ),
        card(
            "univ_analysis_polynomial_limit_at_parameter",
            "university_real_analysis",
            "intermediate",
            "If a is real, then the limit of x ↦ x^2+3*x-1 at a is a^2+3*a-1.",
            typed_forall(("a",), "R", pals("has_limit_at", lambda_("x", polynomial), a, polynomial_at_a)),
            "Use continuity of a polynomial to obtain its punctured-neighborhood limit.",
            (
                "setup: Fix a real point a.",
                "identify: The displayed expression is a polynomial in x.",
                "apply_theorem: Polynomials are continuous at a.",
                "derive: Continuity gives convergence on ordinary neighborhoods.",
                "restrict: Pass to the punctured neighborhood at a.",
                "conclude: Evaluate the polynomial at a to obtain the claimed limit.",
            ),
            "example (a : ℝ) : Filter.Tendsto (fun x : ℝ => x^2 + 3*x - 1) (nhdsWithin a ({a} : Set ℝ)ᶜ) (nhds (a^2 + 3*a - 1)) := by\n  have h : ContinuousAt (fun x : ℝ => x^2 + 3*x - 1) a := by fun_prop\n  exact h.tendsto.mono_left nhdsWithin_le_nhds",
        ),
        card(
            "univ_analysis_removable_singularity_limit",
            "university_real_analysis",
            "advanced",
            "The limit of x ↦ (x^2-4)/(x-2) at 2 is 4.",
            pals("has_limit_at", lambda_("x", removable), n(2), n(4)),
            "Factor the numerator away from the excluded point, then take the limit of the simplified affine function.",
            (
                "setup: Work in the punctured neighborhood of 2, where x-2 is nonzero.",
                "factor: Rewrite x²-4 as (x-2)(x+2).",
                "simplify: Cancel x-2 on the punctured neighborhood to get x+2.",
                "apply_theorem: The affine function x↦x+2 is continuous at 2.",
                "evaluate: Its value at 2 is 4.",
                "conclude: Transfer the limit through the eventual equality.",
            ),
            "example : Filter.Tendsto (fun x : ℝ => (x^2 - 4) / (x - 2)) (nhdsWithin (2 : ℝ) ({(2 : ℝ)} : Set ℝ)ᶜ) (nhds 4) := by\n  have hEq : (fun x : ℝ => (x^2 - 4) / (x - 2)) =ᶠ[nhdsWithin (2 : ℝ) ({(2 : ℝ)} : Set ℝ)ᶜ] fun x => x + 2 := by\n    filter_upwards [self_mem_nhdsWithin] with x hx\n    simp only [Set.mem_compl_iff, Set.mem_singleton_iff] at hx\n    have hx0 : x - 2 ≠ 0 := by\n      intro hzero\n      apply hx\n      linarith\n    field_simp [hx0]\n    ring\n  have h : Filter.Tendsto (fun x : ℝ => x + 2) (nhdsWithin (2 : ℝ) ({(2 : ℝ)} : Set ℝ)ᶜ) (nhds 4) := by\n    have hcont : ContinuousAt (fun x : ℝ => x + 2) (2 : ℝ) := by fun_prop\n    have hfilter : nhdsWithin (2 : ℝ) ({(2 : ℝ)} : Set ℝ)ᶜ ≤ nhds (2 : ℝ) := nhdsWithin_le_nhds\n    convert hcont.tendsto.mono_left hfilter using 1 <;> norm_num\n  exact h.congr' hEq.symm",
        ),
        card(
            "univ_analysis_inverse_successor_sequence",
            "university_real_analysis",
            "intermediate",
            "The real sequence n ↦ 1/(n+1) converges to 0.",
            pals("converges_to", tag("OMBIND", oms("pals1", "sequence_lambda", pals_symbol=True) + tag("OMBVAR", v("n")) + inverse_successor), n(0)),
            "Apply the standard reciprocal-of-a-diverging-natural-number limit theorem.",
            (
                "setup: View n↦n+1 as an unbounded positive real sequence.",
                "derive: Its reciprocal is defined for every natural index.",
                "apply_theorem: Use convergence of 1/(n+1) to zero.",
                "conclude: The specified real sequence converges to 0.",
            ),
            "example : Filter.Tendsto (fun n : ℕ => (1 : ℝ) / (n + 1)) Filter.atTop (𝓝 0) := by\n  simpa using (tendsto_one_div_add_atTop_nhds_zero_nat : Filter.Tendsto (fun n : ℕ => (1 : ℝ) / (↑n + 1)) Filter.atTop (𝓝 0))",
        ),
        card(
            "univ_analysis_linear_ratio_sequence",
            "university_real_analysis",
            "intermediate",
            "The real sequence n ↦ n/(n+2) converges to 1.",
            pals("converges_to", tag("OMBIND", oms("pals1", "sequence_lambda", pals_symbol=True) + tag("OMBVAR", v("n")) + ratio), n(1)),
            "Normalize numerator and denominator by their common leading growth rate.",
            (
                "setup: Consider the ratio n/(n+2) as n tends to infinity.",
                "normalize: Both numerator and denominator have leading coefficient 1.",
                "apply_theorem: Use the natural-cast ratio limit for n/(n+c).",
                "evaluate: The leading-coefficient ratio is 1/1.",
                "conclude: The sequence converges to 1.",
            ),
            "example : Filter.Tendsto (fun n : ℕ => (n : ℝ) / (n + 2)) Filter.atTop (nhds 1) := by\n  simpa using (tendsto_natCast_div_add_atTop (2 : ℝ))",
        ),
    ]


def discrete_cards() -> list[Card]:
    a, b, c = v("A"), v("B"), v("C")
    sq = lambda_("x", pow_(v("x"), 2))
    shift = lambda_("x", add(v("x"), n(1)))
    shifted_square = lambda_("x", add(pow_(v("x"), 2), n(1)))
    return [
        card(
            "univ_discrete_product_union_left",
            "university_discrete_mathematics",
            "intermediate",
            "For sets A, B, C, (A ∪ B) × C = (A × C) ∪ (B × C).",
            forall(("A", "B", "C"), eq(product(union(a, b), c), union(product(a, c), product(b, c)))),
            "Expand membership of an ordered pair and distribute the left disjunction.",
            (
                "setup: Take an arbitrary ordered pair (x,y).",
                "expand: Interpret membership in (A∪B)×C componentwise.",
                "split: Separate the cases x∈A and x∈B.",
                "reassemble: Recognize membership in (A×C)∪(B×C).",
                "conclude: Extensionality proves the set equality.",
            ),
            "example {α β : Type*} (A B : Set α) (C : Set β) : (A ∪ B) ×ˢ C = (A ×ˢ C) ∪ (B ×ˢ C) := by\n  ext p\n  simp [and_or_left]",
        ),
        card(
            "univ_discrete_product_union_right",
            "university_discrete_mathematics",
            "intermediate",
            "For sets A, B, C, A × (B ∪ C) = (A × B) ∪ (A × C).",
            forall(("A", "B", "C"), eq(product(a, union(b, c)), union(product(a, b), product(a, c)))),
            "Use componentwise product membership and distribute the right disjunction.",
            (
                "setup: Take an arbitrary ordered pair (x,y).",
                "expand: Interpret membership in A×(B∪C).",
                "split: Separate the cases y∈B and y∈C.",
                "reassemble: Obtain membership in (A×B)∪(A×C).",
                "conclude: Apply extensionality.",
            ),
            "example {α β : Type*} (A : Set α) (B C : Set β) : A ×ˢ (B ∪ C) = (A ×ˢ B) ∪ (A ×ˢ C) := by\n  ext p\n  simp [and_or_right]",
        ),
        card(
            "univ_discrete_product_intersection",
            "university_discrete_mathematics",
            "intermediate",
            "For sets A, B, C, (A ∩ B) × C = (A × C) ∩ (B × C).",
            forall(("A", "B", "C"), eq(product(inter(a, b), c), inter(product(a, c), product(b, c)))),
            "Use pair membership to move conjunctions between factors and products.",
            (
                "setup: Fix an ordered pair (x,y).",
                "expand: Write membership in (A∩B)×C as x∈A, x∈B, y∈C.",
                "rearrange: Group the conditions as membership in A×C and B×C.",
                "reassemble: Recognize their intersection.",
                "conclude: Use extensionality.",
            ),
            "example {α β : Type*} (A B : Set α) (C : Set β) : (A ∩ B) ×ˢ C = (A ×ˢ C) ∩ (B ×ˢ C) := by\n  ext p\n  simp [and_left_comm, and_assoc, and_comm]",
        ),
        card(
            "univ_discrete_product_set_difference",
            "university_discrete_mathematics",
            "advanced",
            "For sets A, B, C, (A \\ B) × C = (A × C) \\ (B × C).",
            forall(("A", "B", "C"), eq(product(diff(a, b), c), diff(product(a, c), product(b, c)))),
            "Use the shared second-coordinate condition to transport exclusion through the product.",
            (
                "setup: Fix an ordered pair (x,y).",
                "expand: Unfold membership in the left-hand product and set difference.",
                "derive: On both sides y∈C, so exclusion from B×C is exactly x∉B.",
                "reassemble: Match the condition x∈A\\B and y∈C.",
                "conclude: Apply extensionality.",
            ),
            "example {α β : Type*} (A B : Set α) (C : Set β) : (A \\ B) ×ˢ C = (A ×ˢ C) \\ (B ×ˢ C) := by\n  ext p\n  simp\n  tauto",
        ),
        card(
            "univ_discrete_difference_intersection",
            "university_discrete_mathematics",
            "intermediate",
            "For sets A, B, C, (A ∩ B) \\ C = (A \\ C) ∩ (B \\ C).",
            forall(("A", "B", "C"), eq(diff(inter(a, b), c), inter(diff(a, c), diff(b, c)))),
            "Distribute the common exclusion from C across the conjunction A∩B.",
            (
                "setup: Take an arbitrary element x.",
                "expand: Unfold x∈(A∩B)\\C.",
                "rearrange: Separate x∈A, x∈B, and x∉C.",
                "reassemble: Recognize x∈(A\\C)∩(B\\C).",
                "conclude: Use extensionality.",
            ),
            "example {α : Type*} (A B C : Set α) : (A ∩ B) \\ C = (A \\ C) ∩ (B \\ C) := by\n  ext x\n  simp\n  tauto",
        ),
        card(
            "univ_discrete_difference_of_difference",
            "university_discrete_mathematics",
            "advanced",
            "For sets A, B, C, A \\ (B \\ C) = (A \\ B) ∪ (A ∩ C).",
            forall(("A", "B", "C"), eq(diff(a, diff(b, c)), union(diff(a, b), inter(a, c)))),
            "Convert the nested exclusion to a propositional normal form.",
            (
                "setup: Fix an arbitrary element x.",
                "expand: Unfold x∈A\\(B\\C) into x∈A and not(x∈B and x∉C).",
                "normalize: Use De Morgan to obtain x∈A and (x∉B or x∈C).",
                "split: Distribute x∈A over the resulting disjunction.",
                "reassemble: Recognize (A\\B)∪(A∩C).",
                "conclude: Apply extensionality.",
            ),
            "example {α : Type*} (A B C : Set α) : A \\ (B \\ C) = (A \\ B) ∪ (A ∩ C) := by\n  ext x\n  simp\n  tauto",
        ),
        card(
            "univ_discrete_union_membership_partition",
            "university_discrete_mathematics",
            "advanced",
            "For sets A and B, A ∪ B = (A \\ B) ∪ (A ∩ B) ∪ (B \\ A).",
            forall(("A", "B"), eq(union(a, b), union(diff(a, b), inter(a, b), diff(b, a)))),
            "Partition a union into the A-only, shared, and B-only regions.",
            (
                "setup: Fix an arbitrary element x in A∪B.",
                "case_split: If x∈A, split further on whether x∈B.",
                "derive: The two A-cases give x∈A\\B or x∈A∩B.",
                "case_split: If x∉A, membership in A∪B forces x∈B\\A.",
                "reverse: Each of the three regions is contained in A∪B.",
                "conclude: Extensionality gives the partition equality.",
            ),
            "example {α : Type*} (A B : Set α) : A ∪ B = (A \\ B) ∪ (A ∩ B) ∪ (B \\ A) := by\n  ext x\n  simp",
        ),
        card(
            "univ_discrete_union_intersection_distributive",
            "university_discrete_mathematics",
            "intermediate",
            "For sets A, B, C, A ∪ (B ∩ C) = (A ∪ B) ∩ (A ∪ C).",
            forall(("A", "B", "C"), eq(union(a, inter(b, c)), inter(union(a, b), union(a, c)))),
            "Distribute the common membership alternative x∈A over an intersection.",
            (
                "setup: Fix an arbitrary element x.",
                "expand: Translate both sides into propositions about x.",
                "forward: From x∈A or (x∈B and x∈C), derive both union memberships.",
                "reverse: If x∉A, the two union memberships force x∈B and x∈C.",
                "reassemble: Obtain x∈A∪(B∩C).",
                "conclude: Use extensionality.",
            ),
            "example {α : Type*} (A B C : Set α) : A ∪ (B ∩ C) = (A ∪ B) ∩ (A ∪ C) := by\n  ext x\n  simp\n  tauto",
        ),
        card(
            "univ_discrete_difference_subset_iff",
            "university_discrete_mathematics",
            "advanced",
            "For sets A, B, C, A \\ B ⊆ C if and only if A ⊆ B ∪ C.",
            forall(("A", "B", "C"), iff(subset(diff(a, b), c), subset(a, union(b, c)))),
            "Prove both directions elementwise, splitting on membership in B.",
            (
                "setup: Expand both subset statements at an arbitrary element x.",
                "forward: Assume A\\B⊆C and take x∈A.",
                "case_split: If x∈B, place x in B∪C; otherwise use the difference inclusion.",
                "reverse: Assume A⊆B∪C and take x∈A\\B.",
                "derive: The B alternative is impossible, so x∈C.",
                "conclude: The two subset statements are equivalent.",
            ),
            "example {α : Type*} (A B C : Set α) : A \\ B ⊆ C ↔ A ⊆ B ∪ C := by\n  constructor\n  · intro h x hx\n    by_cases hB : x ∈ B\n    · exact Or.inl hB\n    · exact Or.inr (h ⟨hx, hB⟩)\n  · intro h x hx\n    rcases h hx.1 with hB | hC\n    · exact False.elim (hx.2 hB)\n    · exact hC",
        ),
        card(
            "univ_discrete_difference_monotone_left",
            "university_discrete_mathematics",
            "intermediate",
            "If A ⊆ C, then A \\ B ⊆ C \\ B for sets A, B, C.",
            forall(("A", "B", "C"), implies(subset(a, c), subset(diff(a, b), diff(c, b)))),
            "Transport the positive membership through A⊆C while retaining the exclusion from B.",
            (
                "setup: Assume A⊆C and take x∈A\\B.",
                "derive: The first component gives x∈A.",
                "apply_theorem: Use A⊆C to conclude x∈C.",
                "retain: Keep the second component x∉B unchanged.",
                "conclude: Assemble x∈C\\B.",
            ),
            "example {α : Type*} (A B C : Set α) (h : A ⊆ C) : A \\ B ⊆ C \\ B := fun x hx => ⟨h hx.1, hx.2⟩",
        ),
        card(
            "univ_discrete_square_image_union",
            "university_discrete_mathematics",
            "intermediate",
            "For real sets A and B, the image of A ∪ B under x ↦ x^2 equals the union of the two images.",
            forall(("A", "B"), implies(and_(subset(a, oms("setname1", "R")), subset(b, oms("setname1", "R"))), eq(image(sq, union(a, b)), union(image(sq, a), image(sq, b))))),
            "Use the general image-of-union theorem for the concrete squaring function.",
            (
                "setup: Regard x↦x² as a function from ℝ to ℝ.",
                "expand: An image witness comes from either A or B exactly when it comes from A∪B.",
                "forward: Split the source membership into the A and B cases.",
                "reverse: Reinsert either source witness into A∪B.",
                "conclude: Apply extensionality to the image sets.",
            ),
            "example (A B : Set ℝ) : (fun x : ℝ => x^2) '' (A ∪ B) = (fun x : ℝ => x^2) '' A ∪ (fun x : ℝ => x^2) '' B := Set.image_union _ _ _",
        ),
        card(
            "univ_discrete_square_image_intersection_subset",
            "university_discrete_mathematics",
            "advanced",
            "For real sets A and B, the image of A ∩ B under x ↦ x^2 is a subset of the intersection of the images.",
            forall(("A", "B"), implies(and_(subset(a, oms("setname1", "R")), subset(b, oms("setname1", "R"))), subset(image(sq, inter(a, b)), inter(image(sq, a), image(sq, b))))),
            "Track the same source witness into both images; do not claim equality because squaring is not injective.",
            (
                "setup: Take y in the image of A∩B under squaring.",
                "unpack: Obtain one witness x belonging to both A and B with y=x².",
                "derive: The same x witnesses y in the image of A.",
                "derive: The same x witnesses y in the image of B.",
                "conclude: y lies in the intersection of the two images.",
                "guardrail: Only prove subset; squaring can identify x and -x.",
            ),
            "example (A B : Set ℝ) : (fun x : ℝ => x^2) '' (A ∩ B) ⊆ (fun x : ℝ => x^2) '' A ∩ (fun x : ℝ => x^2) '' B := Set.image_inter_subset _ _ _",
        ),
        card(
            "univ_discrete_square_image_monotone",
            "university_discrete_mathematics",
            "intermediate",
            "The square-image map preserves subset inclusion for real sets A and B.",
            forall(("A", "B"), implies(and_(subset(a, oms("setname1", "R")), subset(b, oms("setname1", "R")), subset(a, b)), subset(image(sq, a), image(sq, b)))),
            "Reuse a source witness and transport its membership across the subset relation.",
            (
                "setup: Assume A⊆B and take y in the square image of A.",
                "unpack: Choose x∈A with y=x².",
                "apply_theorem: Use A⊆B to obtain x∈B.",
                "repack: The same x witnesses y in the square image of B.",
                "conclude: The square-image operation is monotone.",
            ),
            "example (A B : Set ℝ) (h : A ⊆ B) : (fun x : ℝ => x^2) '' A ⊆ (fun x : ℝ => x^2) '' B := Set.image_mono h",
        ),
        card(
            "univ_discrete_affine_image_composition",
            "university_discrete_mathematics",
            "advanced",
            "For every real set A, shifting the square image by 1 equals the image of A under x ↦ x^2+1.",
            forall(("A",), implies(subset(a, oms("setname1", "R")), eq(image(shift, image(sq, a)), image(shifted_square, a)))),
            "Compose explicit image witnesses and simplify the composed function.",
            (
                "setup: Let s(x)=x² and t(y)=y+1.",
                "expand: A member of t(s(A)) has witnesses x∈A and y=x².",
                "substitute: Replace y by x² in the outer equation.",
                "simplify: The composed value is x²+1.",
                "reverse: Any witness for x²+1 supplies the two-stage image witness.",
                "conclude: Extensionality proves the image-composition equality.",
            ),
            "example (A : Set ℝ) : (fun y : ℝ => y + 1) '' ((fun x : ℝ => x^2) '' A) = (fun x : ℝ => x^2 + 1) '' A := by\n  simpa [Function.comp_def] using (Set.image_comp (fun y : ℝ => y + 1) (fun x : ℝ => x^2) A).symm",
        ),
        card(
            "univ_discrete_translation_image_difference",
            "university_discrete_mathematics",
            "advanced",
            "For real sets A and B, translating A \\ B by 1 equals the difference of the translated images of A and B.",
            forall(("A", "B"), implies(and_(subset(a, oms("setname1", "R")), subset(b, oms("setname1", "R"))), eq(image(shift, diff(a, b)), diff(image(shift, a), image(shift, b))))),
            "Use injectivity of translation to show that image and set difference commute in this case.",
            (
                "setup: Let t(x)=x+1 and take an arbitrary target value y.",
                "forward: A witness x∈A\\B gives y=t(x) in t(A), and injectivity prevents y from being in t(B).",
                "reverse: From y∈t(A)\\t(B), choose x∈A with y=x+1.",
                "derive: If x were in B, then y would be in t(B), contradicting exclusion.",
                "repack: Obtain x∈A\\B with y=t(x).",
                "conclude: Extensionality proves equality of the two sets.",
            ),
            "example (A B : Set ℝ) : (fun x : ℝ => x + 1) '' (A \\ B) = ((fun x : ℝ => x + 1) '' A) \\ ((fun x : ℝ => x + 1) '' B) := by\n  ext y\n  constructor\n  · rintro ⟨x, hx, rfl⟩\n    constructor\n    · exact ⟨x, hx.1, rfl⟩\n    · rintro ⟨z, hz, hzy⟩\n      apply hx.2\n      have hzx : z = x := by linarith\n      simpa [hzx] using hz\n  · rintro ⟨⟨x, hx, rfl⟩, hnot⟩\n    refine ⟨x, ?_, rfl⟩\n    constructor\n    · exact hx\n    · intro hB\n      apply hnot\n      exact ⟨x, hB, rfl⟩",
        ),
    ]


def cards() -> tuple[Card, ...]:
    result = tuple(linear_cards() + analysis_cards() + discrete_cards())
    if len(result) != 26 or len({item.id for item in result}) != len(result):
        raise RuntimeError("expected exactly 26 uniquely identified university-mathematics cards")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "pals.local-university-math-draft-candidates.v1",
        "source": "PALS first-party authored candidate set; not yet published",
        "cards": [asdict(item) for item in cards()],
    }
    arguments.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
