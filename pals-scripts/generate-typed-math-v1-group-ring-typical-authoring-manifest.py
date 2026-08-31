"""Seal profile-faithful group and commutative-ring Draft proposals.

This is authoring evidence only.  It validates every XML proposition through
the isolated ``typed-math-v1`` validator and binds each statement to a Lean
witness.  It neither widens generic OpenMath nor writes to a Draft database.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import rfc8785

ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = ROOT / "pals-agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

from pals_agent.typed_draft_catalog import load_typed_authoring_manifest
from pals_agent.typed_math import canonicalize_typed_math_openmath_xml

TYPED = "urn:pals:openmath:typed-math:v1"
STANDARD = "http://www.openmath.org/cd"
OPENMATH = "http://www.openmath.org/OpenMath"
MANIFEST_DIGEST_INPUT = (
    "RFC 8785 canonical JSON serialization of this object with manifest_digest omitted"
)
CORE_MANIFEST = (
    AGENT_ROOT / "testdata/typed-math-v1/group-ring-core-authoring-manifest.proposal.json"
)
REGISTRY_PATH = AGENT_ROOT / "pals_agent/content_dictionaries/typed-math-v1-registry.json"
TOOLCHAIN_PATH = AGENT_ROOT / "lean-workspace/lean-toolchain"


def tag(name: str, *children: str, **attributes: str) -> str:
    attrs = "".join(f' {key}="{value}"' for key, value in attributes.items())
    return f"<{name}{attrs}>{''.join(children)}</{name}>"


def oms(cd: str, name: str, *, cdbase: str = TYPED) -> str:
    return f'<OMS cdbase="{cdbase}" cd="{cd}" name="{name}"/>'


def omv(name: str) -> str:
    return f'<OMV name="{name}"/>'


def app(operator: str, *arguments: str) -> str:
    return tag("OMA", operator, *arguments)


def algebra(name: str, structure: str, *arguments: str) -> str:
    return app(oms("algebra1", name), omv(structure), *arguments)


def eq(left: str, right: str) -> str:
    return app(oms("relation1", "eq", cdbase=STANDARD), left, right)


def equivalent(left: str, right: str) -> str:
    return app(oms("logic1", "equivalent", cdbase=STANDARD), left, right)


def implies(left: str, right: str) -> str:
    return app(oms("logic1", "implies", cdbase=STANDARD), left, right)


def disjunction(left: str, right: str) -> str:
    return app(oms("logic1", "or", cdbase=STANDARD), left, right)


def group_mul(structure: str, left: str, right: str) -> str:
    return algebra("mul", structure, left, right)


def group_inv(structure: str, value: str) -> str:
    return algebra("inv", structure, value)


def group_one(structure: str) -> str:
    return algebra("one", structure)


def ring_add(structure: str, left: str, right: str) -> str:
    return algebra("ring_add", structure, left, right)


def ring_mul(structure: str, left: str, right: str) -> str:
    return algebra("ring_mul", structure, left, right)


def ring_neg(structure: str, value: str) -> str:
    return algebra("ring_neg", structure, value)


def ring_zero(structure: str) -> str:
    return algebra("ring_zero", structure)


def typed_declaration(sort: str, variable: str) -> str:
    return tag("OMATTR", tag("OMATP", oms("typed1", "type"), sort), omv(variable))


def element_sort(structure: str) -> str:
    return app(oms("typed1", "Elem"), omv(structure))


def forall_structure(
    *,
    sort_name: str,
    structure: str,
    elements: tuple[str, ...],
    body: str,
) -> str:
    declarations = [typed_declaration(oms("algebra1", sort_name), structure)]
    declarations.extend(typed_declaration(element_sort(structure), element) for element in elements)
    return tag(
        "OMOBJ",
        tag("OMBIND", oms("typed1", "forall"), tag("OMBVAR", *declarations), body),
        xmlns=OPENMATH,
        version="2.0",
    )


def canonical(xml: str) -> str:
    return canonicalize_typed_math_openmath_xml(xml)


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def card(
    *,
    identifier: str,
    domain: str,
    difficulty: str,
    statement: str,
    sort_name: str,
    structure: str,
    elements: tuple[str, ...],
    body: str,
    strategy: str,
    steps: list[str],
    lean_target: str,
    lean_witness: str,
    statement_to_openmath: str,
    openmath_to_lean: str,
) -> dict[str, Any]:
    raw_xml = forall_structure(
        sort_name=sort_name,
        structure=structure,
        elements=elements,
        body=body,
    )
    canonical_xml = canonical(raw_xml)
    if not 4 <= len(steps) <= 8:
        raise ValueError(f"{identifier} needs 4..8 non-empty sketch steps")
    return {
        "id": identifier,
        "domain": domain,
        "difficulty": difficulty,
        "canonical_statement": statement,
        "openmath_xml": raw_xml,
        "canonical_openmath_xml": canonical_xml,
        "canonical_openmath_xml_sha256": sha256_text(canonical_xml),
        "proof_strategy": strategy,
        "sketch_steps": steps,
        "lean": {
            "target": lean_target,
            "target_sha256": sha256_text(lean_target),
            "witness": lean_witness,
            "witness_sha256": sha256_text(lean_witness),
        },
        "statement_openmath_lean_alignment_review": {
            "status": "reviewed_by_local_authoring_agent_not_admitted",
            "statement_to_openmath": statement_to_openmath,
            "openmath_to_lean": openmath_to_lean,
            "admission_gate": "An independent project reviewer must accept this record before any typed catalog or database admission.",
        },
    }


LEAN_WITNESSES: dict[str, tuple[str, str]] = {
    "typed_group_inverse_involution": (
        "∀ {G : Type*} [Group G] (a : G), a⁻¹⁻¹ = a",
        """example : ∀ {G : Type*} [Group G] (a : G), a⁻¹⁻¹ = a := by
  intro G _ a
  simp
""",
    ),
    "typed_group_inverse_one": (
        "∀ {G : Type*} [Group G], (1 : G)⁻¹ = 1",
        """example : ∀ {G : Type*} [Group G], (1 : G)⁻¹ = 1 := by
  intro G _
  simp
""",
    ),
    "typed_group_left_cancellation_iff": (
        "∀ {G : Type*} [Group G] (a b c : G), a * b = a * c ↔ b = c",
        """example : ∀ {G : Type*} [Group G] (a b c : G), a * b = a * c ↔ b = c := by
  intro G _ a b c
  constructor
  · exact mul_left_cancel
  · intro h
    simp [h]
""",
    ),
    "typed_group_right_cancellation_iff": (
        "∀ {G : Type*} [Group G] (a b c : G), b * a = c * a ↔ b = c",
        """example : ∀ {G : Type*} [Group G] (a b c : G), b * a = c * a ↔ b = c := by
  intro G _ a b c
  constructor
  · exact mul_right_cancel
  · intro h
    simp [h]
""",
    ),
    "typed_group_solve_left_multiplication": (
        "∀ {G : Type*} [Group G] (a x b : G), a * x = b ↔ x = a⁻¹ * b",
        """example : ∀ {G : Type*} [Group G] (a x b : G), a * x = b ↔ x = a⁻¹ * b := by
  intro G _ a x b
  constructor
  · intro h
    calc
      x = 1 * x := by simp
      _ = (a⁻¹ * a) * x := by simp
      _ = a⁻¹ * (a * x) := by rw [mul_assoc]
      _ = a⁻¹ * b := by rw [h]
  · intro h
    rw [h]
    simp
""",
    ),
    "typed_group_solve_right_multiplication": (
        "∀ {G : Type*} [Group G] (x a b : G), x * a = b ↔ x = b * a⁻¹",
        """example : ∀ {G : Type*} [Group G] (x a b : G), x * a = b ↔ x = b * a⁻¹ := by
  intro G _ x a b
  constructor
  · intro h
    calc
      x = x * 1 := by simp
      _ = x * (a * a⁻¹) := by simp
      _ = (x * a) * a⁻¹ := by rw [mul_assoc]
      _ = b * a⁻¹ := by rw [h]
  · intro h
    rw [h]
    simp [mul_assoc]
""",
    ),
    "typed_group_product_one_iff_right_inverse": (
        "∀ {G : Type*} [Group G] (a b : G), a * b = 1 ↔ b = a⁻¹",
        """example : ∀ {G : Type*} [Group G] (a b : G), a * b = 1 ↔ b = a⁻¹ := by
  intro G _ a b
  constructor
  · intro h
    calc
      b = 1 * b := by simp
      _ = (a⁻¹ * a) * b := by simp
      _ = a⁻¹ * (a * b) := by rw [mul_assoc]
      _ = a⁻¹ * 1 := by rw [h]
      _ = a⁻¹ := by simp
  · intro h
    rw [h]
    simp
""",
    ),
    "typed_group_cancel_right_inverse": (
        "∀ {G : Type*} [Group G] (a b : G), (a * b) * b⁻¹ = a",
        """example : ∀ {G : Type*} [Group G] (a b : G), (a * b) * b⁻¹ = a := by
  intro G _ a b
  simp [mul_assoc]
""",
    ),
    "typed_group_inverse_equality_iff": (
        "∀ {G : Type*} [Group G] (a b : G), a⁻¹ = b⁻¹ ↔ a = b",
        """example : ∀ {G : Type*} [Group G] (a b : G), a⁻¹ = b⁻¹ ↔ a = b := by
  intro G _ a b
  constructor
  · intro h
    have h' := congrArg Inv.inv h
    simpa using h'
  · intro h
    simp [h]
""",
    ),
    "typed_comm_ring_double_negation": (
        "∀ {R : Type*} [CommRing R] (x : R), - -x = x",
        """example : ∀ {R : Type*} [CommRing R] (x : R), - -x = x := by
  intro R _ x
  simp
""",
    ),
    "typed_comm_ring_neg_zero": (
        "∀ {R : Type*} [CommRing R], -(0 : R) = 0",
        """example : ∀ {R : Type*} [CommRing R], -(0 : R) = 0 := by
  intro R _
  simp
""",
    ),
    "typed_comm_ring_add_left_cancellation_iff": (
        "∀ {R : Type*} [CommRing R] (x y z : R), x + y = x + z ↔ y = z",
        """example : ∀ {R : Type*} [CommRing R] (x y z : R), x + y = x + z ↔ y = z := by
  intro R _ x y z
  constructor
  · exact add_left_cancel
  · intro h
    simp [h]
""",
    ),
    "typed_comm_ring_solve_left_addition": (
        "∀ {R : Type*} [CommRing R] (x y z : R), x + y = z ↔ y = z + -x",
        """example : ∀ {R : Type*} [CommRing R] (x y z : R), x + y = z ↔ y = z + -x := by
  intro R _ x y z
  constructor
  · intro h
    calc
      y = 0 + y := by simp
      _ = (-x + x) + y := by simp
      _ = -x + (x + y) := by rw [add_assoc]
      _ = -x + z := by rw [h]
      _ = z + -x := by rw [add_comm]
  · intro h
    calc
      x + y = x + (z + -x) := by rw [h]
      _ = (x + -x) + z := by ac_rfl
      _ = 0 + z := by simp
      _ = z := by simp
""",
    ),
    "typed_comm_ring_zero_sum_iff_neg": (
        "∀ {R : Type*} [CommRing R] (x y : R), x + y = 0 ↔ x = -y",
        """example : ∀ {R : Type*} [CommRing R] (x y : R), x + y = 0 ↔ x = -y := by
  intro R _ x y
  constructor
  · intro h
    calc
      x = x + 0 := by simp
      _ = x + (y + -y) := by simp
      _ = (x + y) + -y := by rw [add_assoc]
      _ = 0 + -y := by rw [h]
      _ = -y := by simp
  · intro h
    rw [h]
    simp
""",
    ),
    "typed_comm_ring_neg_add": (
        "∀ {R : Type*} [CommRing R] (x y : R), -(x + y) = -x + -y",
        """example : ∀ {R : Type*} [CommRing R] (x y : R), -(x + y) = -x + -y := by
  intro R _ x y
  simp [add_comm]
""",
    ),
    "typed_comm_ring_neg_mul_left": (
        "∀ {R : Type*} [CommRing R] (x y : R), (-x) * y = -(x * y)",
        """example : ∀ {R : Type*} [CommRing R] (x y : R), (-x) * y = -(x * y) := by
  intro R _ x y
  simp
""",
    ),
    "typed_comm_ring_neg_mul_neg": (
        "∀ {R : Type*} [CommRing R] (x y : R), (-x) * (-y) = x * y",
        """example : ∀ {R : Type*} [CommRing R] (x y : R), (-x) * (-y) = x * y := by
  intro R _ x y
  simp
""",
    ),
    "typed_comm_ring_mul_zero_right": (
        "∀ {R : Type*} [CommRing R] (x : R), x * 0 = 0",
        """example : ∀ {R : Type*} [CommRing R] (x : R), x * 0 = 0 := by
  intro R _ x
  simp
""",
    ),
    "typed_comm_ring_square_expansion": (
        "∀ {R : Type*} [CommRing R] (x y : R), (x + y) * (x + y) = x * x + (x * y + (y * x + y * y))",
        """example : ∀ {R : Type*} [CommRing R] (x y : R), (x + y) * (x + y) = x * x + (x * y + (y * x + y * y)) := by
  intro R _ x y
  ring
""",
    ),
    "typed_comm_ring_difference_of_squares": (
        "∀ {R : Type*} [CommRing R] (x y : R), (x + y) * (x + -y) = x * x + -(y * y)",
        """example : ∀ {R : Type*} [CommRing R] (x y : R), (x + y) * (x + -y) = x * x + -(y * y) := by
  intro R _ x y
  ring
""",
    ),
    "typed_integral_domain_zero_product": (
        "∀ {R : Type*} [CommRing R] [IsDomain R] (x y : R), x * y = 0 → x = 0 ∨ y = 0",
        """example : ∀ {R : Type*} [CommRing R] [IsDomain R] (x y : R), x * y = 0 → x = 0 ∨ y = 0 := by
  intro R _ _ x y h
  exact eq_zero_or_eq_zero_of_mul_eq_zero h
""",
    ),
    "typed_integral_domain_square_zero": (
        "∀ {R : Type*} [CommRing R] [IsDomain R] (x : R), x * x = 0 → x = 0",
        """example : ∀ {R : Type*} [CommRing R] [IsDomain R] (x : R), x * x = 0 → x = 0 := by
  intro R _ _ x h
  exact mul_self_eq_zero.mp h
""",
    ),
}


def lean_target(identifier: str) -> str:
    return LEAN_WITNESSES[identifier][0]


def lean_witness(identifier: str) -> str:
    return LEAN_WITNESSES[identifier][1]


def build_manifest() -> dict[str, Any]:
    g = "G"
    r = "R"
    a, b, c = omv("a"), omv("b"), omv("c")
    x, y, z = omv("x"), omv("y"), omv("z")
    group_alignment = (
        "exact: the Group carrier and every element operand are explicitly bound, and each group operation is indexed by that same carrier.",
        "exact under the profile's carrier-indexed Group lowering: algebra1:mul, inv, and one map to Lean multiplication, inversion, and identity.",
    )
    ring_alignment = (
        "exact: the CommRing carrier and every element operand are explicitly bound, and each ring operation is indexed by that same carrier.",
        "exact under the profile's carrier-indexed CommRing lowering: ring_add, ring_mul, ring_neg, and ring_zero map to Lean's corresponding ring operations.",
    )
    domain_alignment = (
        "exact: the IntegralDomain carrier and both element operands are explicitly bound; the premise and disjunction remain propositions over that same carrier.",
        "exact under the recorded lowering: algebra1:IntegralDomain maps to the Lean assumptions [CommRing R] [IsDomain R]; ring multiplication/zero and logic1:implies/or map to their corresponding Lean operations.",
    )
    cards = [
        card(
            identifier="typed_group_inverse_involution", domain="abstract_algebra_groups", difficulty="introductory",
            statement="For every element a of a group G, the inverse of a⁻¹ is a.", sort_name="Group", structure=g, elements=("a",),
            body=eq(group_inv(g, group_inv(g, a)), a),
            strategy="Use uniqueness of the inverse after observing that a is an inverse of a⁻¹.",
            steps=["setup: Fix a in the carrier of G.", "inverse: Form a⁻¹ using the group inverse operation.", "candidate: Observe that a is a two-sided inverse candidate for a⁻¹.", "uniqueness: Apply uniqueness of inverses in a group.", "conclude: The inverse of a⁻¹ is a."],
            lean_target=lean_target("typed_group_inverse_involution"), lean_witness=lean_witness("typed_group_inverse_involution"), statement_to_openmath=group_alignment[0], openmath_to_lean=group_alignment[1],
        ),
        card(
            identifier="typed_group_inverse_one", domain="abstract_algebra_groups", difficulty="introductory",
            statement="In every group G, the inverse of the identity element is the identity element.", sort_name="Group", structure=g, elements=(),
            body=eq(group_inv(g, group_one(g)), group_one(g)),
            strategy="Show that the identity is its own two-sided inverse.",
            steps=["setup: Fix the group G and its identity 1.", "candidate: Use 1 itself as an inverse candidate for 1.", "left-product: Simplify 1*1 to 1.", "right-product: Simplify the reverse product in the same way.", "conclude: Inverse uniqueness gives 1⁻¹ = 1."],
            lean_target=lean_target("typed_group_inverse_one"), lean_witness=lean_witness("typed_group_inverse_one"), statement_to_openmath=group_alignment[0], openmath_to_lean=group_alignment[1],
        ),
        card(
            identifier="typed_group_left_cancellation_iff", domain="abstract_algebra_groups", difficulty="standard",
            statement="For a, b, c in a group G, a*b = a*c if and only if b = c.", sort_name="Group", structure=g, elements=("a", "b", "c"),
            body=equivalent(eq(group_mul(g, a, b), group_mul(g, a, c)), eq(b, c)),
            strategy="Multiply an equality on the left by a⁻¹, and use congruence for the converse.",
            steps=["setup: Fix a, b, c in G.", "forward: Assume a*b = a*c.", "cancel: Multiply both sides on the left by a⁻¹ and reassociate.", "simplify: Reduce a⁻¹*a to 1.", "reverse: Substitute b = c to recover the product equality."],
            lean_target=lean_target("typed_group_left_cancellation_iff"), lean_witness=lean_witness("typed_group_left_cancellation_iff"), statement_to_openmath=group_alignment[0], openmath_to_lean=group_alignment[1],
        ),
        card(
            identifier="typed_group_right_cancellation_iff", domain="abstract_algebra_groups", difficulty="standard",
            statement="For a, b, c in a group G, b*a = c*a if and only if b = c.", sort_name="Group", structure=g, elements=("a", "b", "c"),
            body=equivalent(eq(group_mul(g, b, a), group_mul(g, c, a)), eq(b, c)),
            strategy="Multiply an equality on the right by a⁻¹, and use congruence for the converse.",
            steps=["setup: Fix a, b, c in G.", "forward: Assume b*a = c*a.", "cancel: Multiply both sides on the right by a⁻¹.", "simplify: Reduce a*a⁻¹ to 1.", "reverse: Substitute b = c to recover the original equality."],
            lean_target=lean_target("typed_group_right_cancellation_iff"), lean_witness=lean_witness("typed_group_right_cancellation_iff"), statement_to_openmath=group_alignment[0], openmath_to_lean=group_alignment[1],
        ),
        card(
            identifier="typed_group_solve_left_multiplication", domain="abstract_algebra_groups", difficulty="standard",
            statement="For a, x, b in a group G, a*x = b if and only if x = a⁻¹*b.", sort_name="Group", structure=g, elements=("a", "x", "b"),
            body=equivalent(eq(group_mul(g, a, x), b), eq(x, group_mul(g, group_inv(g, a), b))),
            strategy="Undo left multiplication by multiplying with a⁻¹, then verify the proposed solution.",
            steps=["setup: Fix a, x, b in G.", "forward: Start from a*x = b.", "undo: Multiply on the left by a⁻¹ and reassociate.", "simplify: Replace a⁻¹*a by 1 to isolate x.", "reverse: Substitute x = a⁻¹*b and simplify a*a⁻¹."],
            lean_target=lean_target("typed_group_solve_left_multiplication"), lean_witness=lean_witness("typed_group_solve_left_multiplication"), statement_to_openmath=group_alignment[0], openmath_to_lean=group_alignment[1],
        ),
        card(
            identifier="typed_group_solve_right_multiplication", domain="abstract_algebra_groups", difficulty="standard",
            statement="For x, a, b in a group G, x*a = b if and only if x = b*a⁻¹.", sort_name="Group", structure=g, elements=("x", "a", "b"),
            body=equivalent(eq(group_mul(g, x, a), b), eq(x, group_mul(g, b, group_inv(g, a)))),
            strategy="Undo right multiplication by multiplying with a⁻¹, then verify the proposed solution.",
            steps=["setup: Fix x, a, b in G.", "forward: Start from x*a = b.", "undo: Multiply on the right by a⁻¹ and reassociate.", "simplify: Replace a*a⁻¹ by 1 to isolate x.", "reverse: Substitute x = b*a⁻¹ and simplify."],
            lean_target=lean_target("typed_group_solve_right_multiplication"), lean_witness=lean_witness("typed_group_solve_right_multiplication"), statement_to_openmath=group_alignment[0], openmath_to_lean=group_alignment[1],
        ),
        card(
            identifier="typed_group_product_one_iff_right_inverse", domain="abstract_algebra_groups", difficulty="standard",
            statement="For a and b in a group G, a*b = 1 if and only if b = a⁻¹.", sort_name="Group", structure=g, elements=("a", "b"),
            body=equivalent(eq(group_mul(g, a, b), group_one(g)), eq(b, group_inv(g, a))),
            strategy="Treat b as the solution of the equation a*b = 1.",
            steps=["setup: Fix a and b in G.", "forward: Assume a*b is the identity.", "isolate: Multiply on the left by a⁻¹.", "simplify: Reassociate and reduce a⁻¹*a and 1*b.", "reverse: Substitute b = a⁻¹ and simplify a*a⁻¹."],
            lean_target=lean_target("typed_group_product_one_iff_right_inverse"), lean_witness=lean_witness("typed_group_product_one_iff_right_inverse"), statement_to_openmath=group_alignment[0], openmath_to_lean=group_alignment[1],
        ),
        card(
            identifier="typed_group_cancel_right_inverse", domain="abstract_algebra_groups", difficulty="introductory",
            statement="For a and b in a group G, (a*b)*b⁻¹ = a.", sort_name="Group", structure=g, elements=("a", "b"),
            body=eq(group_mul(g, group_mul(g, a, b), group_inv(g, b)), a),
            strategy="Reassociate the product and cancel b with its right inverse.",
            steps=["setup: Fix a and b in G.", "associate: Rewrite (a*b)*b⁻¹ as a*(b*b⁻¹).", "inverse: Apply the right-inverse law to b.", "identity: Simplify a*1.", "conclude: The result is a."],
            lean_target=lean_target("typed_group_cancel_right_inverse"), lean_witness=lean_witness("typed_group_cancel_right_inverse"), statement_to_openmath=group_alignment[0], openmath_to_lean=group_alignment[1],
        ),
        card(
            identifier="typed_group_inverse_equality_iff", domain="abstract_algebra_groups", difficulty="standard",
            statement="For a and b in a group G, a⁻¹ = b⁻¹ if and only if a = b.", sort_name="Group", structure=g, elements=("a", "b"),
            body=equivalent(eq(group_inv(g, a), group_inv(g, b)), eq(a, b)),
            strategy="Take inverses on both sides, using inverse involution; use substitution in the converse.",
            steps=["setup: Fix a and b in G.", "forward: Assume their inverses are equal.", "invert: Apply the inverse operation to both sides.", "simplify: Use (u⁻¹)⁻¹ = u.", "reverse: Substitute a = b before taking inverses."],
            lean_target=lean_target("typed_group_inverse_equality_iff"), lean_witness=lean_witness("typed_group_inverse_equality_iff"), statement_to_openmath=group_alignment[0], openmath_to_lean=group_alignment[1],
        ),
        card(
            identifier="typed_comm_ring_double_negation", domain="abstract_algebra_rings", difficulty="introductory",
            statement="For every x in a commutative ring R, -(-x) = x.", sort_name="CommRing", structure=r, elements=("x",),
            body=eq(ring_neg(r, ring_neg(r, x)), x),
            strategy="Use uniqueness of the additive inverse of x.",
            steps=["setup: Fix x in R.", "inverse: The element -x is an additive inverse of x.", "candidate: Observe that x is an additive inverse of -x.", "uniqueness: Apply uniqueness of additive inverses.", "conclude: -(-x) equals x."],
            lean_target=lean_target("typed_comm_ring_double_negation"), lean_witness=lean_witness("typed_comm_ring_double_negation"), statement_to_openmath=ring_alignment[0], openmath_to_lean=ring_alignment[1],
        ),
        card(
            identifier="typed_comm_ring_neg_zero", domain="abstract_algebra_rings", difficulty="introductory",
            statement="In every commutative ring R, the additive inverse of zero is zero.", sort_name="CommRing", structure=r, elements=(),
            body=eq(ring_neg(r, ring_zero(r)), ring_zero(r)),
            strategy="Use that zero is its own additive inverse.",
            steps=["setup: Fix the commutative ring R and its additive zero.", "candidate: Use zero as an inverse candidate for zero.", "sum: Verify 0+0=0.", "uniqueness: Use uniqueness of additive inverses.", "conclude: -0=0."],
            lean_target=lean_target("typed_comm_ring_neg_zero"), lean_witness=lean_witness("typed_comm_ring_neg_zero"), statement_to_openmath=ring_alignment[0], openmath_to_lean=ring_alignment[1],
        ),
        card(
            identifier="typed_comm_ring_add_left_cancellation_iff", domain="abstract_algebra_rings", difficulty="standard",
            statement="For x, y, z in a commutative ring R, x+y = x+z if and only if y = z.", sort_name="CommRing", structure=r, elements=("x", "y", "z"),
            body=equivalent(eq(ring_add(r, x, y), ring_add(r, x, z)), eq(y, z)),
            strategy="Add -x to both sides for cancellation; use substitution for the converse.",
            steps=["setup: Fix x, y, z in R.", "forward: Assume x+y=x+z.", "cancel: Add -x to both sides and reassociate.", "simplify: Reduce -x+x to zero.", "reverse: Substitute y=z to recover the original equality."],
            lean_target=lean_target("typed_comm_ring_add_left_cancellation_iff"), lean_witness=lean_witness("typed_comm_ring_add_left_cancellation_iff"), statement_to_openmath=ring_alignment[0], openmath_to_lean=ring_alignment[1],
        ),
        card(
            identifier="typed_comm_ring_solve_left_addition", domain="abstract_algebra_rings", difficulty="standard",
            statement="For x, y, z in a commutative ring R, x+y = z if and only if y = z+(-x).", sort_name="CommRing", structure=r, elements=("x", "y", "z"),
            body=equivalent(eq(ring_add(r, x, y), z), eq(y, ring_add(r, z, ring_neg(r, x)))),
            strategy="Add the additive inverse of x to isolate y, then substitute back.",
            steps=["setup: Fix x, y, z in R.", "forward: Assume x+y=z.", "isolate: Add -x and reassociate the left-hand side.", "simplify: Reduce -x+x to zero and commute the resulting sum.", "reverse: Substitute y=z+(-x) and cancel x with -x."],
            lean_target=lean_target("typed_comm_ring_solve_left_addition"), lean_witness=lean_witness("typed_comm_ring_solve_left_addition"), statement_to_openmath=ring_alignment[0], openmath_to_lean=ring_alignment[1],
        ),
        card(
            identifier="typed_comm_ring_zero_sum_iff_neg", domain="abstract_algebra_rings", difficulty="standard",
            statement="For x and y in a commutative ring R, x+y=0 if and only if x=-y.", sort_name="CommRing", structure=r, elements=("x", "y"),
            body=equivalent(eq(ring_add(r, x, y), ring_zero(r)), eq(x, ring_neg(r, y))),
            strategy="Move y across the equation using its additive inverse.",
            steps=["setup: Fix x and y in R.", "forward: Assume x+y=0.", "isolate: Add -y and reassociate.", "simplify: Replace y+(-y) by zero.", "reverse: Substitute x=-y and simplify the sum."],
            lean_target=lean_target("typed_comm_ring_zero_sum_iff_neg"), lean_witness=lean_witness("typed_comm_ring_zero_sum_iff_neg"), statement_to_openmath=ring_alignment[0], openmath_to_lean=ring_alignment[1],
        ),
        card(
            identifier="typed_comm_ring_neg_add", domain="abstract_algebra_rings", difficulty="standard",
            statement="For x and y in a commutative ring R, -(x+y)=(-x)+(-y).", sort_name="CommRing", structure=r, elements=("x", "y"),
            body=eq(ring_neg(r, ring_add(r, x, y)), ring_add(r, ring_neg(r, x), ring_neg(r, y))),
            strategy="Show that (-x)+(-y) is the additive inverse of x+y.",
            steps=["setup: Fix x and y in R.", "candidate: Propose (-x)+(-y) as the inverse of x+y.", "expand: Add the two expressions and reassociate.", "cancel: Pair x with -x and y with -y.", "conclude: Inverse uniqueness gives the formula."],
            lean_target=lean_target("typed_comm_ring_neg_add"), lean_witness=lean_witness("typed_comm_ring_neg_add"), statement_to_openmath=ring_alignment[0], openmath_to_lean=ring_alignment[1],
        ),
        card(
            identifier="typed_comm_ring_neg_mul_left", domain="abstract_algebra_rings", difficulty="standard",
            statement="For x and y in a commutative ring R, (-x)*y = -(x*y).", sort_name="CommRing", structure=r, elements=("x", "y"),
            body=eq(ring_mul(r, ring_neg(r, x), y), ring_neg(r, ring_mul(r, x, y))),
            strategy="Use distributivity to show that (-x)*y is the additive inverse of x*y.",
            steps=["setup: Fix x and y in R.", "candidate: Consider (-x)*y.", "add: Add x*y to that candidate.", "factor: Use distributivity to factor (-x+x)*y.", "conclude: The product is zero, so the candidate is -(x*y)."],
            lean_target=lean_target("typed_comm_ring_neg_mul_left"), lean_witness=lean_witness("typed_comm_ring_neg_mul_left"), statement_to_openmath=ring_alignment[0], openmath_to_lean=ring_alignment[1],
        ),
        card(
            identifier="typed_comm_ring_neg_mul_neg", domain="abstract_algebra_rings", difficulty="standard",
            statement="For x and y in a commutative ring R, (-x)*(-y)=x*y.", sort_name="CommRing", structure=r, elements=("x", "y"),
            body=eq(ring_mul(r, ring_neg(r, x), ring_neg(r, y)), ring_mul(r, x, y)),
            strategy="Apply the one-negative product rule twice and use double negation.",
            steps=["setup: Fix x and y in R.", "first-sign: Move the negation on the left factor outside the product.", "second-sign: Apply the same rule to the remaining negated factor.", "double-negation: Simplify the double additive inverse of x*y.", "conclude: The product equals x*y."],
            lean_target=lean_target("typed_comm_ring_neg_mul_neg"), lean_witness=lean_witness("typed_comm_ring_neg_mul_neg"), statement_to_openmath=ring_alignment[0], openmath_to_lean=ring_alignment[1],
        ),
        card(
            identifier="typed_comm_ring_mul_zero_right", domain="abstract_algebra_rings", difficulty="introductory",
            statement="For every x in a commutative ring R, x*0=0.", sort_name="CommRing", structure=r, elements=("x",),
            body=eq(ring_mul(r, x, ring_zero(r)), ring_zero(r)),
            strategy="Use distributivity and additive cancellation to identify x*0 with zero.",
            steps=["setup: Fix x in R.", "duplicate: Rewrite 0 as 0+0.", "distribute: Expand x*(0+0) into x*0+x*0.", "cancel: Cancel one x*0 from both sides.", "conclude: x*0=0."],
            lean_target=lean_target("typed_comm_ring_mul_zero_right"), lean_witness=lean_witness("typed_comm_ring_mul_zero_right"), statement_to_openmath=ring_alignment[0], openmath_to_lean=ring_alignment[1],
        ),
        card(
            identifier="typed_comm_ring_square_expansion", domain="abstract_algebra_rings", difficulty="intermediate",
            statement="For x and y in a commutative ring R, (x+y)(x+y)=x*x+(x*y+(y*x+y*y)).", sort_name="CommRing", structure=r, elements=("x", "y"),
            body=eq(ring_mul(r, ring_add(r, x, y), ring_add(r, x, y)), ring_add(r, ring_mul(r, x, x), ring_add(r, ring_mul(r, x, y), ring_add(r, ring_mul(r, y, x), ring_mul(r, y, y))))),
            strategy="Distribute each sum and collect the four products without collapsing the two cross terms.",
            steps=["setup: Fix x and y in R.", "outer-distribution: Expand the left factor across x+y.", "inner-distribution: Expand both resulting products.", "associate: Reassociate the four summands in the displayed order.", "conclude: Both sides are the same four-term sum."],
            lean_target=lean_target("typed_comm_ring_square_expansion"), lean_witness=lean_witness("typed_comm_ring_square_expansion"), statement_to_openmath=ring_alignment[0], openmath_to_lean=ring_alignment[1],
        ),
        card(
            identifier="typed_comm_ring_difference_of_squares", domain="abstract_algebra_rings", difficulty="intermediate",
            statement="For x and y in a commutative ring R, (x+y)(x+(-y))=x*x+(-(y*y)).", sort_name="CommRing", structure=r, elements=("x", "y"),
            body=eq(ring_mul(r, ring_add(r, x, y), ring_add(r, x, ring_neg(r, y))), ring_add(r, ring_mul(r, x, x), ring_neg(r, ring_mul(r, y, y)))),
            strategy="Expand both products, cancel the two cross terms, then simplify the double negative.",
            steps=["setup: Fix x and y in R.", "expand: Distribute both factors into four products.", "signs: Rewrite products containing -y as additive negatives.", "cancel: Pair x*y with its additive inverse.", "conclude: The remaining terms are x*x and -(y*y)."],
            lean_target=lean_target("typed_comm_ring_difference_of_squares"), lean_witness=lean_witness("typed_comm_ring_difference_of_squares"), statement_to_openmath=ring_alignment[0], openmath_to_lean=ring_alignment[1],
        ),
        card(
            identifier="typed_integral_domain_zero_product", domain="abstract_algebra_integral_domains", difficulty="standard",
            statement="For x and y in an integral domain R, x*y=0 implies x=0 or y=0.", sort_name="IntegralDomain", structure=r, elements=("x", "y"),
            body=implies(eq(ring_mul(r, x, y), ring_zero(r)), disjunction(eq(x, ring_zero(r)), eq(y, ring_zero(r)))),
            strategy="Apply the no-zero-divisors property of an integral domain.",
            steps=["setup: Fix x and y in the integral domain R.", "premise: Assume x*y=0.", "domain-property: Invoke that R has no zero divisors.", "split: Obtain x=0 or y=0.", "conclude: This is the stated disjunction."],
            lean_target=lean_target("typed_integral_domain_zero_product"), lean_witness=lean_witness("typed_integral_domain_zero_product"), statement_to_openmath=domain_alignment[0], openmath_to_lean=domain_alignment[1],
        ),
        card(
            identifier="typed_integral_domain_square_zero", domain="abstract_algebra_integral_domains", difficulty="standard",
            statement="For x in an integral domain R, x*x=0 implies x=0.", sort_name="IntegralDomain", structure=r, elements=("x",),
            body=implies(eq(ring_mul(r, x, x), ring_zero(r)), eq(x, ring_zero(r))),
            strategy="Specialize the zero-product property to the same factor twice.",
            steps=["setup: Fix x in the integral domain R.", "premise: Assume x*x=0.", "zero-product: Apply the no-zero-divisors conclusion to x and x.", "cases: Both alternatives are the same assertion x=0.", "conclude: x=0."],
            lean_target=lean_target("typed_integral_domain_square_zero"), lean_witness=lean_witness("typed_integral_domain_square_zero"), statement_to_openmath=domain_alignment[0], openmath_to_lean=domain_alignment[1],
        ),
    ]
    if len(cards) != 22:
        raise AssertionError("expected 22 distinct group/ring derived-theorem cards")
    witness_text = witness_bundle()
    for entry in cards:
        target = entry["lean"]["target"]
        witness = entry["lean"]["witness"]
        if target not in witness or witness not in witness_text:
            raise ValueError(f"Lean evidence for {entry['id']} is not bundle-bound")
    _assert_no_overlap_with_core(cards)
    return {
        "schema_version": "pals.typed-math-v1-authoring-manifest.v1",
        "proposal_status": "not_admitted_requires_independent_project_review",
        "profile": {
            "id": "typed-math-v1",
            "validator": "pals_agent.typed_math.validate_canonical_typed_math_openmath_xml",
            "canonicalizer": "openmath-cdbase-alpha-c14n-v4",
            "admission_openmath_field": "canonical_openmath_xml",
            "cd_bundle": {
                "registry_path": "pals_agent/content_dictionaries/typed-math-v1-registry.json",
                "sha256": sha256_bytes(REGISTRY_PATH.read_bytes()),
                "digest_input": "exact UTF-8 bytes of the named registry file",
            },
            "lean_toolchain": {
                "path": "lean-workspace/lean-toolchain",
                "value": TOOLCHAIN_PATH.read_text(encoding="utf-8").rstrip("\n"),
                "sha256": sha256_bytes(TOOLCHAIN_PATH.read_bytes()),
                "digest_input": "exact UTF-8 bytes of the named lean-toolchain file",
            },
        },
        "lean_witness_bundle": {
            "path": "testdata/typed-math-v1/group-ring-typical-theorems-authoring-witnesses.lean",
            "sha256": sha256_text(witness_text),
            "digest_input": "exact UTF-8 bytes of the named Lean file, including import and final newline",
            "verification_command": "cd pals-agent/lean-workspace && lake env lean ../testdata/typed-math-v1/group-ring-typical-theorems-authoring-witnesses.lean",
            "verification_status": "verified_local_pinned_workspace",
        },
        "cards": cards,
        "manifest_digest": {},
    }


def witness_bundle() -> str:
    return "import Mathlib\n\n" + "\n".join(witness for _target, witness in LEAN_WITNESSES.values())


def _assert_no_overlap_with_core(cards: list[dict[str, Any]]) -> None:
    core = load_typed_authoring_manifest(CORE_MANIFEST)
    existing_ids = {entry["id"] for entry in core["cards"]}
    existing_xml = {entry["canonical_openmath_xml"] for entry in core["cards"]}
    for entry in cards:
        if entry["id"] in existing_ids:
            raise ValueError(f"card id overlaps core manifest: {entry['id']}")
        if entry["canonical_openmath_xml"] in existing_xml:
            raise ValueError(f"canonical OpenMath overlaps core manifest: {entry['id']}")


def seal(manifest: dict[str, Any]) -> dict[str, Any]:
    unsigned = dict(manifest)
    unsigned.pop("manifest_digest", None)
    manifest["manifest_digest"] = {
        "algorithm": "sha256",
        "input": MANIFEST_DIGEST_INPUT,
        "sha256": "sha256:" + hashlib.sha256(rfc8785.dumps(unsigned)).hexdigest(),
    }
    return manifest


def write_if_changed(path: Path, text: str) -> None:
    if not path.exists() or path.read_text(encoding="utf-8") != text:
        path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=AGENT_ROOT / "testdata/typed-math-v1/group-ring-typical-theorems-authoring-manifest.proposal.json",
    )
    parser.add_argument(
        "--lean-output",
        type=Path,
        default=AGENT_ROOT / "testdata/typed-math-v1/group-ring-typical-theorems-authoring-witnesses.lean",
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    manifest = seal(build_manifest())
    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    lean_text = witness_bundle()
    if not lean_text.endswith("\n"):
        raise AssertionError("Lean witness bundle must end in a newline")
    if args.check:
        if args.output.read_text(encoding="utf-8") != manifest_text:
            raise SystemExit("group/ring typical-theorems manifest is stale; rerun this generator")
        if args.lean_output.read_text(encoding="utf-8") != lean_text:
            raise SystemExit("group/ring typical-theorems Lean bundle is stale; rerun this generator")
        load_typed_authoring_manifest(args.output)
        print("group/ring typical-theorems manifest and Lean bundle are current")
        return
    write_if_changed(args.output, manifest_text)
    write_if_changed(args.lean_output, lean_text)
    load_typed_authoring_manifest(args.output)


if __name__ == "__main__":
    main()
