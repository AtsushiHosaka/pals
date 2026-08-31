#!/usr/bin/env python3
"""Generate current-profile Draft candidates for logic and set foundations.

This authoring tool writes a manifest only.  It never writes to the Draft DB.
When explicitly requested, it validates the generated cards against the local
legacy catalog and compiles every Lean witness in the pinned Lean workspace.

The generic OpenMath profile has no `Prop` sort or predicate-variable binder.
Therefore every logical law below is anchored to a concrete atomic predicate
(equality, order, membership, or inclusion), rather than pretending that a
bare `OMV` is a proposition.
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
DEFAULT_DB_COUNT = 253


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


def neq(left: str, right: str) -> str:
    return std("relation1", "neq", left, right)


def lt(left: str, right: str) -> str:
    return std("relation1", "lt", left, right)


def leq(left: str, right: str) -> str:
    return std("relation1", "leq", left, right)


def plus(*arguments: str) -> str:
    return std("arith1", "plus", *arguments)


def times(*arguments: str) -> str:
    return std("arith1", "times", *arguments)


def power(base: str, exponent: str) -> str:
    return std("arith1", "power", base, exponent)


def and_(*arguments: str) -> str:
    return std("logic1", "and", *arguments)


def or_(*arguments: str) -> str:
    return std("logic1", "or", *arguments)


def not_(argument: str) -> str:
    return std("logic1", "not", argument)


def implies(premise: str, conclusion: str) -> str:
    return std("logic1", "implies", premise, conclusion)


def iff(left: str, right: str) -> str:
    return std("logic1", "equivalent", left, right)


def member(element: str, set_: str) -> str:
    return std("set1", "in", element, set_)


def not_member(element: str, set_: str) -> str:
    return std("set1", "notin", element, set_)


def subset(left: str, right: str) -> str:
    return std("set1", "subset", left, right)


def union(left: str, right: str) -> str:
    return std("set1", "union", left, right)


def intersection(left: str, right: str) -> str:
    return std("set1", "intersect", left, right)


def difference(left: str, right: str) -> str:
    return std("set1", "setdiff", left, right)


def emptyset() -> str:
    return oms("set1", "emptyset")


def bind(kind: str, names: tuple[str, ...], body: str) -> str:
    return tag("OMBIND", oms("quant1", kind) + tag("OMBVAR", "".join(var(name) for name in names)) + body)


def forall(names: tuple[str, ...], body: str) -> str:
    return bind("forall", names, body)


def exists(name: str, body: str) -> str:
    return bind("exists", (name,), body)


def typed_forall(names: tuple[str, ...], set_name: str, body: str) -> str:
    premises = tuple(member(var(name), oms("setname1", set_name)) for name in names)
    premise = premises[0] if len(premises) == 1 else and_(*premises)
    return forall(names, implies(premise, body))


def typed_exists(name: str, set_name: str, body: str) -> str:
    return exists(name, and_(member(var(name), oms("setname1", set_name)), body))


def openmath(body: str) -> str:
    return f'<OMOBJ xmlns="{OPENMATH}" version="2.0">{body}</OMOBJ>'


def make(
    identifier: str,
    domain: str,
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
        domain=domain,
        level="high_school_and_early_university",
        topic=topic,
        difficulty=difficulty,
        canonical_statement=statement,
        openmath_xml=xml,
        proof_strategy=strategy,
        sketch_steps=steps,
        lean_witness=witness,
    )


LOGIC_STEPS = (
    "setup: Introduce the variables together with the stated atomic hypotheses.",
    "translate: Read the hypotheses as the corresponding logical assertions.",
    "derive: Apply the indicated logical rule or its order/equality instance.",
    "conclude: State the required proposition with its original quantifiers.",
)

SET_MEMBERSHIP_STEPS = (
    "setup: Fix an arbitrary element and the displayed sets.",
    "unfold: Translate the set operation into its membership condition.",
    "logic: Apply the required conjunction, disjunction, or negation rule.",
    "conclude: Reassemble the target membership proposition.",
)

SET_INCLUSION_STEPS = (
    "setup: Fix an arbitrary candidate element of the source set.",
    "unpack: Use the given subset or membership hypotheses.",
    "derive: Apply the relevant inclusion rule to the element.",
    "conclude: Since the element was arbitrary, establish the target subset or equality.",
)

QUANTIFIER_STEPS = (
    "setup: Introduce the universally quantified variable and its domain premise.",
    "choose: Construct the required witness explicitly.",
    "domain: Verify that the witness lies in the requested domain.",
    "verify: Substitute the witness into the target relation.",
    "conclude: Package the witness under the existential quantifier.",
)

INDUCTION_STEPS = (
    "setup: State the proposition for an arbitrary natural number n.",
    "base_case: Verify the claim at n = 0.",
    "inductive_step: Assume the claim for n and rewrite the n + 1 case.",
    "close_step: Apply the induction hypothesis and normalize the natural-number arithmetic.",
    "conclude: Invoke induction to obtain the result for every natural number.",
)


def logic_cards() -> list[Card]:
    x, y, z = map(var, ("x", "y", "z"))
    real_xyz = lambda body: typed_forall(("x", "y", "z"), "R", body)
    real_xy = lambda body: typed_forall(("x", "y"), "R", body)
    real_x = lambda body: typed_forall(("x",), "R", body)
    return [
        make("logic_eq_symmetry_real", "logic_and_proof_methods", "equality_reasoning", "introductory", "For all real x and y, if x = y then y = x.", real_xy(implies(eq(x, y), eq(y, x))), "Use symmetry of equality as a direct proof.", LOGIC_STEPS, "example (x y : ℝ) : x = y → y = x := by intro h; exact h.symm"),
        make("logic_eq_transitivity_real", "logic_and_proof_methods", "equality_reasoning", "introductory", "For all real x, y, and z, if x = y and y = z then x = z.", real_xyz(implies(and_(eq(x, y), eq(y, z)), eq(x, z))), "Chain the two equality hypotheses by transitivity.", LOGIC_STEPS, "example (x y z : ℝ) : x = y ∧ y = z → x = z := by rintro ⟨hxy, hyz⟩; exact hxy.trans hyz"),
        make("logic_eq_add_congruence_real", "logic_and_proof_methods", "equality_substitution", "standard", "For all real x, y, and z, if x = y then x + z = y + z.", real_xyz(implies(eq(x, y), eq(plus(x, z), plus(y, z)))), "Substitute equals for equals inside addition.", LOGIC_STEPS, "example (x y z : ℝ) : x = y → x + z = y + z := by intro h; rw [h]"),
        make("logic_lt_implies_not_ge_real", "logic_and_proof_methods", "proof_by_contradiction", "standard", "For all real x and y, if x < y then it is not the case that y ≤ x.", real_xy(implies(lt(x, y), not_(leq(y, x)))), "Assume the opposite weak inequality and contradict strict order.", LOGIC_STEPS, "example (x y : ℝ) : x < y → ¬ y ≤ x := by intro hlt hle; exact (not_le_of_gt hlt) hle"),
        make("logic_lt_implies_neq_real", "logic_and_proof_methods", "proof_by_contradiction", "standard", "For all real x and y, if x < y then x is not equal to y.", real_xy(implies(lt(x, y), neq(x, y))), "Assume equality and rewrite the strict inequality into an irreflexive one.", LOGIC_STEPS, "example (x y : ℝ) : x < y → x ≠ y := by intro hlt heq; subst y; exact (lt_irrefl x) hlt"),
        make("logic_not_lt_self_real", "logic_and_proof_methods", "proof_by_contradiction", "introductory", "For every real x, it is not the case that x < x.", real_x(not_(lt(x, x))), "Assume x < x and use irreflexivity of strict order.", LOGIC_STEPS, "example (x : ℝ) : ¬ x < x := lt_irrefl x"),
        make("logic_eq_or_neq_real", "logic_and_proof_methods", "excluded_middle_instance", "standard", "For all real x and y, either x = y or x is not equal to y.", real_xy(or_(eq(x, y), neq(x, y))), "Apply decidability of equality to this concrete equality proposition.", LOGIC_STEPS, "example (x y : ℝ) : x = y ∨ x ≠ y := eq_or_ne x y"),
        make("logic_not_neq_iff_eq_real", "logic_and_proof_methods", "double_negation_instance", "standard", "For all real x and y, not (x ≠ y) if and only if x = y.", real_xy(iff(not_(neq(x, y)), eq(x, y))), "Prove each direction using equality reflexivity and a contradiction argument.", LOGIC_STEPS, """example (x y : ℝ) : (¬ x ≠ y) ↔ x = y := by
  constructor
  · intro h
    exact by_contra fun hxy => h hxy
  · intro h hxy
    exact hxy h"""),
        make("logic_not_lt_and_le_real", "logic_and_proof_methods", "proof_by_contradiction", "standard", "For all real x and y, it is not the case that x < y and y ≤ x.", real_xy(not_(and_(lt(x, y), leq(y, x)))), "Assume both order statements and derive the contradiction x < x.", LOGIC_STEPS, "example (x y : ℝ) : ¬ (x < y ∧ y ≤ x) := by rintro ⟨hlt, hle⟩; exact (not_le_of_gt hlt) hle"),
        make("logic_add_neq_contrapositive_real", "logic_and_proof_methods", "contrapositive", "advanced", "For all real x, y, and z, if x + z ≠ y + z then x ≠ y.", real_xyz(implies(neq(plus(x, z), plus(y, z)), neq(x, y))), "Use the contrapositive: equal inputs yield equal sums after adding z.", LOGIC_STEPS, "example (x y z : ℝ) : x + z ≠ y + z → x ≠ y := by intro hsum hxy; apply hsum; rw [hxy]"),
    ]


def set_cards() -> list[Card]:
    a, b, c, x = map(var, ("A", "B", "C", "x"))
    return [
        make("logic_set_membership_union_iff", "set_foundations", "membership_characterization", "introductory", "For every element x and sets A, B, x belongs to A ∪ B if and only if x belongs to A or x belongs to B.", forall(("x", "A", "B"), iff(member(x, union(a, b)), or_(member(x, a), member(x, b)))), "Unfold union membership into a disjunction.", SET_MEMBERSHIP_STEPS, "example {α : Type} (x : α) (A B : Set α) : x ∈ A ∪ B ↔ x ∈ A ∨ x ∈ B := by simp"),
        make("logic_set_membership_intersection_iff", "set_foundations", "membership_characterization", "introductory", "For every element x and sets A, B, x belongs to A ∩ B if and only if x belongs to A and x belongs to B.", forall(("x", "A", "B"), iff(member(x, intersection(a, b)), and_(member(x, a), member(x, b)))), "Unfold intersection membership into a conjunction.", SET_MEMBERSHIP_STEPS, "example {α : Type} (x : α) (A B : Set α) : x ∈ A ∩ B ↔ x ∈ A ∧ x ∈ B := by simp"),
        make("logic_set_membership_difference_iff", "set_foundations", "membership_characterization", "standard", "For every element x and sets A, B, x belongs to A \\ B if and only if x belongs to A and x does not belong to B.", forall(("x", "A", "B"), iff(member(x, difference(a, b)), and_(member(x, a), not_(member(x, b))))), "Unfold set difference membership into membership and nonmembership.", SET_MEMBERSHIP_STEPS, "example {α : Type} (x : α) (A B : Set α) : x ∈ A \\ B ↔ x ∈ A ∧ x ∉ B := by simp"),
        make("logic_set_not_member_empty", "set_foundations", "empty_set", "introductory", "For every element x, x does not belong to the empty set.", forall(("x",), not_member(x, emptyset())), "Assume membership in the empty set and eliminate the impossible hypothesis.", SET_MEMBERSHIP_STEPS, "example {α : Type} (x : α) : x ∉ (∅ : Set α) := by simp"),
        make("logic_set_subset_member_elim", "set_foundations", "subset_reasoning", "introductory", "For every element x and sets A, B, if A is a subset of B and x belongs to A, then x belongs to B.", forall(("x", "A", "B"), implies(and_(subset(a, b), member(x, a)), member(x, b))), "Apply the subset hypothesis to the displayed membership proof.", SET_INCLUSION_STEPS, "example {α : Type} (x : α) (A B : Set α) : A ⊆ B → x ∈ A → x ∈ B := by intro h hx; exact h hx"),
        make("logic_set_subset_transitive", "set_foundations", "subset_reasoning", "standard", "For all sets A, B, C, if A ⊆ B and B ⊆ C then A ⊆ C.", forall(("A", "B", "C"), implies(and_(subset(a, b), subset(b, c)), subset(a, c))), "Apply the two inclusion maps successively to an arbitrary element.", SET_INCLUSION_STEPS, "example {α : Type} (A B C : Set α) : A ⊆ B → B ⊆ C → A ⊆ C := by intro hAB hBC x hx; exact hBC (hAB hx)"),
        make("logic_set_union_subset_elim", "set_foundations", "subset_reasoning", "standard", "For all sets A, B, C, if A ⊆ C and B ⊆ C then A ∪ B ⊆ C.", forall(("A", "B", "C"), implies(and_(subset(a, c), subset(b, c)), subset(union(a, b), c))), "Split membership in the union and use the corresponding inclusion hypothesis.", SET_INCLUSION_STEPS, """example {α : Type} (A B C : Set α) : A ⊆ C → B ⊆ C → A ∪ B ⊆ C := by
  intro hAC hBC x hx
  rcases hx with hx | hx
  · exact hAC hx
  · exact hBC hx"""),
        make("logic_set_subset_intersection_intro", "set_foundations", "subset_reasoning", "standard", "For all sets A, B, C, if C ⊆ A and C ⊆ B then C ⊆ A ∩ B.", forall(("A", "B", "C"), implies(and_(subset(c, a), subset(c, b)), subset(c, intersection(a, b)))), "Use both inclusion hypotheses to build intersection membership.", SET_INCLUSION_STEPS, "example {α : Type} (A B C : Set α) : C ⊆ A → C ⊆ B → C ⊆ A ∩ B := by intro hCA hCB x hx; exact ⟨hCA hx, hCB hx⟩"),
        make("logic_set_difference_subset_left", "set_foundations", "subset_reasoning", "introductory", "For all sets A and B, A \\ B is a subset of A.", forall(("A", "B"), subset(difference(a, b), a)), "Unpack difference membership and retain its A-membership component.", SET_INCLUSION_STEPS, "example {α : Type} (A B : Set α) : A \\ B ⊆ A := by intro x hx; exact hx.1"),
        make("logic_set_union_absorption", "set_foundations", "set_algebra", "standard", "For all sets A and B, A ∪ (A ∩ B) = A.", forall(("A", "B"), eq(union(a, intersection(a, b)), a)), "Use extensionality; the extra intersection branch already implies membership in A.", SET_INCLUSION_STEPS, """example {α : Type} (A B : Set α) : A ∪ (A ∩ B) = A := by
  ext x
  constructor
  · intro hx
    exact hx.elim (fun hA => hA) (fun hAB => hAB.1)
  · intro hx
    exact Or.inl hx"""),
        make("logic_set_intersection_absorption", "set_foundations", "set_algebra", "standard", "For all sets A and B, A ∩ (A ∪ B) = A.", forall(("A", "B"), eq(intersection(a, union(a, b)), a)), "Use extensionality; membership in A supplies the required union branch.", SET_INCLUSION_STEPS, """example {α : Type} (A B : Set α) : A ∩ (A ∪ B) = A := by
  ext x
  constructor
  · intro hx
    exact hx.1
  · intro hx
    exact ⟨hx, Or.inl hx⟩"""),
        make("logic_set_difference_intersection_demorgan", "set_foundations", "set_algebra", "advanced", "For all sets A, B, C, A \\ (B ∩ C) = (A \\ B) ∪ (A \\ C).", forall(("A", "B", "C"), eq(difference(a, intersection(b, c)), union(difference(a, b), difference(a, c)))), "Apply extensionality and distribute a negated conjunction under the shared A-membership condition.", SET_INCLUSION_STEPS, """example {α : Type} (A B C : Set α) : A \\ (B ∩ C) = (A \\ B) ∪ (A \\ C) := by
  classical
  ext x
  constructor
  · rintro ⟨hA, hnot⟩
    by_cases hB : x ∈ B
    · right
      exact ⟨hA, fun hC => hnot ⟨hB, hC⟩⟩
    · left
      exact ⟨hA, hB⟩
  · intro hx
    rcases hx with hx | hx
    · exact ⟨hx.1, fun hBC => hx.2 hBC.1⟩
    · exact ⟨hx.1, fun hBC => hx.2 hBC.2⟩"""),
        make("logic_set_extensionality_subset_antisymm", "set_foundations", "set_extensionality", "standard", "For all sets A and B, if A ⊆ B and B ⊆ A then A = B.", forall(("A", "B"), implies(and_(subset(a, b), subset(b, a)), eq(a, b))), "Use antisymmetry of subset inclusion.", SET_INCLUSION_STEPS, "example {α : Type} (A B : Set α) : A ⊆ B → B ⊆ A → A = B := by intro hAB hBA; exact Set.Subset.antisymm hAB hBA"),
        make("logic_set_subset_union_left", "set_foundations", "subset_reasoning", "introductory", "For all sets A and B, A is a subset of A ∪ B.", forall(("A", "B"), subset(a, union(a, b))), "Map an arbitrary A-member into the left branch of the union.", SET_INCLUSION_STEPS, "example {α : Type} (A B : Set α) : A ⊆ A ∪ B := by intro x hx; exact Or.inl hx"),
        make("logic_set_subset_union_right", "set_foundations", "subset_reasoning", "introductory", "For all sets A and B, B is a subset of A ∪ B.", forall(("A", "B"), subset(b, union(a, b))), "Map an arbitrary B-member into the right branch of the union.", SET_INCLUSION_STEPS, "example {α : Type} (A B : Set α) : B ⊆ A ∪ B := by intro x hx; exact Or.inr hx"),
    ]


def quantifier_and_induction_cards() -> list[Card]:
    x, y, n, m = map(var, ("x", "y", "n", "m"))
    return [
        make("logic_forall_real_exists_add_inverse", "logic_and_proof_methods", "quantifiers_and_witnesses", "introductory", "For every real x, there exists real y such that x + y = 0.", typed_forall(("x",), "R", typed_exists("y", "R", eq(plus(x, y), integer(0)))), "Construct the additive inverse as the existential witness.", QUANTIFIER_STEPS, "example (x : ℝ) : ∃ y : ℝ, x + y = 0 := by refine ⟨-x, by ring⟩"),
        make("logic_forall_real_nonzero_exists_inverse", "logic_and_proof_methods", "quantifiers_and_witnesses", "standard", "For every nonzero real x, there exists real y such that x*y = 1.", typed_forall(("x",), "R", implies(neq(x, integer(0)), typed_exists("y", "R", eq(times(x, y), integer(1))))), "Use the reciprocal x⁻¹ as the witness after checking x is nonzero.", QUANTIFIER_STEPS, "example (x : ℝ) (hx : x ≠ 0) : ∃ y : ℝ, x*y = 1 := by exact ⟨x⁻¹, mul_inv_cancel₀ hx⟩"),
        make("logic_forall_natural_exists_larger", "logic_and_proof_methods", "quantifiers_and_witnesses", "introductory", "For every natural number n, there exists natural number m with n < m.", typed_forall(("n",), "N", typed_exists("m", "N", lt(n, m))), "Choose the successor n + 1 and use the strict successor inequality.", QUANTIFIER_STEPS, "example (n : ℕ) : ∃ m : ℕ, n < m := ⟨n + 1, Nat.lt_succ_self n⟩"),
        make("logic_no_negative_natural", "logic_and_proof_methods", "quantified_negation", "introductory", "No natural number n satisfies n < 0.", not_(typed_exists("n", "N", lt(n, integer(0)))), "Assume an existential witness and contradict nonnegativity of natural numbers.", LOGIC_STEPS, "example : ¬ ∃ n : ℕ, n < 0 := by rintro ⟨n, hn⟩; exact (Nat.not_lt_zero n) hn"),
        make("logic_natural_nonzero_positive", "logic_and_proof_methods", "quantified_implication", "standard", "Every nonzero natural number n is positive.", typed_forall(("n",), "N", implies(neq(n, integer(0)), lt(integer(0), n))), "Use the natural-number dichotomy between zero and positive values.", LOGIC_STEPS, "example (n : ℕ) : n ≠ 0 → 0 < n := by intro hn; exact Nat.pos_of_ne_zero hn"),
        make("logic_natural_le_zero_eq_zero", "logic_and_proof_methods", "quantified_implication", "standard", "Every natural number n at most zero equals zero.", typed_forall(("n",), "N", implies(leq(n, integer(0)), eq(n, integer(0)))), "Use the least-element property of zero in the natural-number order.", LOGIC_STEPS, "example (n : ℕ) : n ≤ 0 → n = 0 := by intro hn; exact Nat.eq_zero_of_le_zero hn"),
        make("induction_nat_add_zero", "logic_and_proof_methods", "mathematical_induction_instance", "introductory", "For every natural number n, n + 0 = n.", typed_forall(("n",), "N", eq(plus(n, integer(0)), n)), "Prove the concrete natural-number identity by induction on n.", INDUCTION_STEPS, "example (n : ℕ) : n + 0 = n := by induction n with | zero => norm_num | succ n ih => omega"),
        make("induction_nat_mul_one", "logic_and_proof_methods", "mathematical_induction_instance", "introductory", "For every natural number n, n*1 = n.", typed_forall(("n",), "N", eq(times(n, integer(1)), n)), "Prove the concrete multiplicative identity by induction on n.", INDUCTION_STEPS, "example (n : ℕ) : n * 1 = n := by induction n with | zero => norm_num | succ n ih => omega"),
        make("induction_nat_power_two_bound", "logic_and_proof_methods", "mathematical_induction_instance", "advanced", "For every natural number n, n + 1 ≤ 2^n.", typed_forall(("n",), "N", leq(plus(n, integer(1)), power(integer(2), n))), "Use induction and double the induction bound in the successor step.", INDUCTION_STEPS, "example (n : ℕ) : n + 1 ≤ 2^n := by induction n with | zero => norm_num | succ n ih => rw [pow_succ]; omega"),
    ]


def cards() -> list[Card]:
    current = logic_cards() + set_cards() + quantifier_and_induction_cards()
    identifiers = [card.id for card in current]
    if len(current) != 34 or len(identifiers) != len(set(identifiers)):
        raise RuntimeError("expected exactly 34 uniquely identified cards")
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
    count_result = subprocess.run(
        ["docker", "compose", "exec", "-T", "postgres", "psql", "-U", "pals", "-d", "pals", "-Atc", "SELECT count(*) FROM public.dsp_drafts;"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if count_result.returncode:
        raise RuntimeError(f"could not query local Draft count:\n{count_result.stderr}")
    actual_count = int(count_result.stdout.strip())
    if actual_count != expected_count:
        raise RuntimeError(f"expected {expected_count} local Drafts, found {actual_count}")

    rows_result = subprocess.run(
        ["docker", "compose", "exec", "-T", "postgres", "psql", "-U", "pals", "-d", "pals", "-At", "-F", "\t", "-c", "SELECT id, openmath_xml FROM public.dsp_drafts ORDER BY id;"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if rows_result.returncode:
        raise RuntimeError(f"could not query local Draft XML:\n{rows_result.stderr}")
    existing: dict[str, str] = {}
    for line in rows_result.stdout.splitlines():
        identifier, separator, xml = line.partition("\t")
        if not separator or not identifier or not xml:
            raise RuntimeError("local Draft XML query returned a malformed row")
        existing[identifier] = xml
    if len(existing) != expected_count:
        raise RuntimeError("local Draft XML query count did not match Draft count")

    candidate_ids = {card.id for card in current}
    duplicate_ids = sorted(candidate_ids & set(existing))
    if duplicate_ids:
        raise RuntimeError(f"candidate IDs already exist in the local DB: {duplicate_ids}")
    # The current generic-retrieval C14N is authoritative for every candidate.
    # Some legacy database rows predate the typed continuity validator and are
    # valid OpenMath but cannot be revalidated by the newer retrieval profile.
    # Scan the compatible DB subset with the authoritative C14N and scan all
    # DB rows with the older structural alpha-C14N.  The latter is a complete
    # collision guard for legacy rows, while retaining the strict check where
    # the current profile permits it.
    strict_existing: set[str] = set()
    legacy_fallback_ids: list[str] = []
    for identifier, xml in existing.items():
        try:
            strict_existing.add(canonicalize_retrieval_openmath_xml(xml))
        except MathXMLValidationError:
            legacy_fallback_ids.append(identifier)
    candidate_strict = {canonicalize_retrieval_openmath_xml(card.openmath_xml) for card in current}
    if duplicate_strict := candidate_strict & strict_existing:
        raise RuntimeError("candidate canonical OpenMath duplicates a current-profile local Draft")

    existing_legacy = {canonicalize_openmath_xml(xml) for xml in existing.values()}
    candidate_legacy = {canonicalize_openmath_xml(card.openmath_xml) for card in current}
    if duplicate_legacy := candidate_legacy & existing_legacy:
        raise RuntimeError("candidate canonical OpenMath duplicates an existing local Draft")
    return tuple(sorted(legacy_fallback_ids))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--verify-lean", action="store_true", help="Compile all Lean witnesses in the pinned workspace.")
    parser.add_argument("--verify-db", action="store_true", help="Read the local Draft DB and reject ID/C14N collisions; does not write to it.")
    parser.add_argument("--expected-db-count", type=int, default=DEFAULT_DB_COUNT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    current = cards()
    if args.verify_lean:
        verify_lean(current)
    legacy_fallback_ids: tuple[str, ...] = ()
    if args.verify_db:
        legacy_fallback_ids = verify_database(current, args.expected_db_count)
    payload = {
        "schema_version": "pals.logic-proof-methods-set-foundations-candidates.v1",
        "source": "PALS first-party authored, generic-OpenMath and Lean-verified candidate set",
        "current_profile_card_count": len(current),
        "validation_contract": {
            "generic_openmath": "Every card is validated by statement-semantics validation plus retrieval C14N validation while the manifest is generated.",
            "lean": "Run with --verify-lean to compile the full witness batch in pals-agent/lean-workspace.",
            "local_db": "Run with --verify-db --expected-db-count 253 to read-check local Draft ID and canonical-OpenMath collisions; no database write is performed.",
        },
        "scope_note": "Bare proposition variables are not representable in the generic profile, so logic cards use concrete equality, order, membership, and subset atoms. Set variables remain untyped generic terms; cards avoid mixing carriers and make no typed-set claim beyond the ordinary single-carrier Lean witness.",
        "induction_boundary": [
            {
                "excluded": "The general mathematical-induction schema: from P(0) and forall n, P(n) implies P(n+1), infer forall n, P(n).",
                "why_current_profile_cannot_represent_it": "The generic profile has neither a Prop sort nor a binder for a predicate P : Nat -> Prop, and it has no induction or natural-recursion operator. Encoding P as a bare OMV would fail proposition validation.",
            },
            {
                "included": "A concrete theorem whose Lean witness uses induction, such as n + 1 <= 2^n.",
                "why_safe": "Its statement is an ordinary quantified natural-number proposition using current quant1, setname1:N, arith1, relation1, and logic1 symbols; induction is retained as proof strategy rather than inserted into the theorem proposition.",
            },
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
        if legacy_fallback_ids:
            print("local_db_retrieval_c14n_fallback=" + ",".join(legacy_fallback_ids))


if __name__ == "__main__":
    main()
