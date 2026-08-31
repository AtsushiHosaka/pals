#!/usr/bin/env python3
"""Generate safe current-generic OpenMath discrete-mathematics candidates.

The artifact is intentionally limited to concrete ordered-relation instances,
scalar map characterizations, closed finite-set calculations, and explicit
finite pigeonhole theorems.  It does not write to a Draft database.
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


def v(name: str) -> str:
    return f'<OMV name="{name}"/>'


def i(value: int) -> str:
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


def minus(left: str, right: str) -> str:
    return std("arith1", "minus", left, right)


def times(*arguments: str) -> str:
    return std("arith1", "times", *arguments)


def power(base: str, exponent: str | int) -> str:
    return std("arith1", "power", base, i(exponent) if isinstance(exponent, int) else exponent)


def and_(*arguments: str) -> str:
    return std("logic1", "and", *arguments)


def or_(*arguments: str) -> str:
    return std("logic1", "or", *arguments)


def implies(premise: str, conclusion: str) -> str:
    return std("logic1", "implies", premise, conclusion)


def iff(left: str, right: str) -> str:
    return std("logic1", "equivalent", left, right)


def member(element: str, set_: str) -> str:
    return std("set1", "in", element, set_)


def union(left: str, right: str) -> str:
    return std("set1", "union", left, right)


def intersection(left: str, right: str) -> str:
    return std("set1", "intersect", left, right)


def difference(left: str, right: str) -> str:
    return std("set1", "setdiff", left, right)


def product(left: str, right: str) -> str:
    return std("set1", "cartesian_product", left, right)


def set_literal(*elements: str) -> str:
    return std("set1", "set", *elements)


def size(set_: str) -> str:
    return std("set1", "size", set_)


def lambda_(name: str, body: str) -> str:
    return tag("OMBIND", oms("fns1", "lambda") + tag("OMBVAR", v(name)) + body)


def image(function: str, source: str) -> str:
    return std("set1", "map", function, source)


def bind(kind: str, names: tuple[str, ...], body: str) -> str:
    return tag("OMBIND", oms("quant1", kind) + tag("OMBVAR", "".join(v(name) for name in names)) + body)


def forall(names: tuple[str, ...], body: str) -> str:
    return bind("forall", names, body)


def exists(name: str, body: str) -> str:
    return bind("exists", (name,), body)


def typed_forall(names: tuple[str, ...], setname: str, body: str) -> str:
    premises = tuple(member(v(name), oms("setname1", setname)) for name in names)
    return forall(names, implies(premises[0] if len(premises) == 1 else and_(*premises), body))


def typed_exists(name: str, setname: str, body: str) -> str:
    return exists(name, and_(member(v(name), oms("setname1", setname)), body))


def xml(body: str) -> str:
    return f'<OMOBJ xmlns="{OPENMATH}" version="2.0">{body}</OMOBJ>'


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
    openmath_xml = xml(proposition)
    validate_openmath_statement_semantics(openmath_xml, statement)
    canonical = canonicalize_retrieval_openmath_xml(openmath_xml)
    validate_canonical_retrieval_openmath_xml(canonical)
    return Card(
        id=identifier,
        profile="current_openmath_profile",
        domain="discrete_mathematics",
        level="high_school_and_early_university",
        topic=topic,
        difficulty=difficulty,
        canonical_statement=statement,
        openmath_xml=openmath_xml,
        proof_strategy=strategy,
        sketch_steps=steps,
        lean_witness=witness,
    )


RELATION_STEPS = (
    "setup: Introduce the integer variables and the displayed order hypotheses.",
    "relation: Read the assumptions as statements about the concrete relation ≤ or <.",
    "derive: Apply transitivity, antisymmetry, or totality of integer order.",
    "conclude: State the requested relation among the original variables.",
)

MAP_STEPS = (
    "setup: Introduce source and target values in the stated scalar domain.",
    "expand: Write the displayed formula for the concrete map.",
    "solve: Cancel, rearrange, or choose the explicit preimage.",
    "verify: Substitute into the map equation or equality characterization.",
    "conclude: State the injectivity, collision, image, or preimage instance.",
)

FINITE_STEPS = (
    "setup: Write the finite sets and their distinct listed elements explicitly.",
    "operation: Form the displayed union, intersection, difference, product, or image.",
    "enumerate: Remove duplicate elements and list the resulting finite set.",
    "count: Count its elements or compare the two explicit finite sets.",
    "conclude: State the requested finite-set identity.",
)

PIGEONHOLE_STEPS = (
    "setup: Record that every listed integer lies in the displayed finite box set.",
    "cases: Split each value into the finitely many allowed box labels.",
    "compare: In every exhaustive branch, identify two equal labels.",
    "conclude: Assemble the resulting disjunction of pair equalities.",
)


def relation_cards() -> list[Card]:
    x, y, z = map(v, ("x", "y", "z"))
    int_xyz = lambda body: typed_forall(("x", "y", "z"), "Z", body)
    int_xy = lambda body: typed_forall(("x", "y"), "Z", body)
    return [
        make("disc_int_le_antisymmetric", "ordered_relation_instance", "introductory", "For all integers x and y, x ≤ y and y ≤ x imply x = y.", int_xy(implies(and_(leq(x, y), leq(y, x)), eq(x, y))), "Use antisymmetry of the integer order relation.", RELATION_STEPS, "example (x y : ℤ) : x ≤ y → y ≤ x → x = y := by omega"),
        make("disc_int_le_total", "ordered_relation_instance", "introductory", "For all integers x and y, either x ≤ y or y ≤ x.", int_xy(or_(leq(x, y), leq(y, x))), "Use totality of the linear order on integers.", RELATION_STEPS, "example (x y : ℤ) : x ≤ y ∨ y ≤ x := le_total x y"),
        make("disc_int_lt_transitive", "ordered_relation_instance", "standard", "For all integers x, y, and z, x < y and y < z imply x < z.", int_xyz(implies(and_(lt(x, y), lt(y, z)), lt(x, z))), "Chain the two strict inequalities by transitivity.", RELATION_STEPS, "example (x y z : ℤ) : x < y → y < z → x < z := by omega"),
        make("disc_int_lt_le_transitive", "ordered_relation_instance", "standard", "For all integers x, y, and z, x < y and y ≤ z imply x < z.", int_xyz(implies(and_(lt(x, y), leq(y, z)), lt(x, z))), "Combine a strict relation with a following weak relation.", RELATION_STEPS, "example (x y z : ℤ) : x < y → y ≤ z → x < z := by omega"),
        make("disc_int_le_lt_transitive", "ordered_relation_instance", "standard", "For all integers x, y, and z, x ≤ y and y < z imply x < z.", int_xyz(implies(and_(leq(x, y), lt(y, z)), lt(x, z))), "Combine a weak relation with a following strict relation.", RELATION_STEPS, "example (x y z : ℤ) : x ≤ y → y < z → x < z := by omega"),
    ]


def map_cards() -> list[Card]:
    x, y = map(v, ("x", "y"))
    real_xy = lambda body: typed_forall(("x", "y"), "R", body)
    real_y = lambda body: typed_forall(("y",), "R", body)
    shift_x, shift_y = plus(x, i(1)), plus(y, i(1))
    affine_x, affine_y = plus(times(i(2), x), i(3)), plus(times(i(2), y), i(3))
    return [
        make("disc_shift_one_equality_iff", "scalar_map_instance", "introductory", "For all real x and y, x + 1 = y + 1 if and only if x = y.", real_xy(iff(eq(shift_x, shift_y), eq(x, y))), "Cancel the common translation constant from both sides.", MAP_STEPS, "example (x y : ℝ) : x + 1 = y + 1 ↔ x = y := by constructor <;> intro h <;> linarith"),
        make("disc_double_equality_iff", "scalar_map_instance", "introductory", "For all real x and y, 2*x = 2*y if and only if x = y.", real_xy(iff(eq(times(i(2), x), times(i(2), y)), eq(x, y))), "Cancel the nonzero scalar factor two.", MAP_STEPS, "example (x y : ℝ) : 2*x = 2*y ↔ x = y := by constructor <;> intro h <;> linarith"),
        make("disc_affine_equality_iff", "scalar_map_instance", "standard", "For all real x and y, 2*x + 3 = 2*y + 3 if and only if x = y.", real_xy(iff(eq(affine_x, affine_y), eq(x, y))), "Cancel the common translation and then the nonzero scale factor.", MAP_STEPS, "example (x y : ℝ) : 2*x + 3 = 2*y + 3 ↔ x = y := by constructor <;> intro h <;> linarith"),
        make("disc_affine_has_real_preimage", "scalar_map_instance", "standard", "For every real y, there exists real x satisfying 2*x + 3 = y.", real_y(typed_exists("x", "R", eq(plus(times(i(2), x), i(3)), y))), "Choose x = (y - 3)/2 and verify the affine equation.", MAP_STEPS, "example (y : ℝ) : ∃ x : ℝ, 2*x + 3 = y := by refine ⟨(y - 3) / 2, by ring⟩"),
        make("disc_square_has_distinct_collision", "scalar_map_instance", "standard", "There exist real x and y with x ≠ y and x^2 = y^2.", typed_exists("x", "R", typed_exists("y", "R", and_(neq(x, y), eq(power(x, 2), power(y, 2))))), "Exhibit the distinct inputs 1 and -1, which have the same square.", MAP_STEPS, "example : ∃ x y : ℝ, x ≠ y ∧ x^2 = y^2 := by refine ⟨1, -1, by norm_num, by norm_num⟩"),
        make("disc_fixed_shift_image", "finite_set_image", "standard", "The image of {1,2,3} under x ↦ x + 1 equals {2,3,4}.", eq(image(lambda_("x", plus(v("x"), i(1))), set_literal(i(1), i(2), i(3))), set_literal(i(2), i(3), i(4))), "Evaluate the map on each listed element and remove no duplicates.", FINITE_STEPS, "example : ({1, 2, 3} : Finset ℤ).image (fun x => x + 1) = {2, 3, 4} := by norm_num"),
        make("disc_fixed_square_image", "finite_set_image", "standard", "The image of {-1,0,1} under x ↦ x^2 equals {0,1}.", eq(image(lambda_("x", power(v("x"), 2)), set_literal(i(-1), i(0), i(1))), set_literal(i(0), i(1))), "Evaluate the square map and identify the duplicate output one.", FINITE_STEPS, "example : ({-1, 0, 1} : Finset ℤ).image (fun x => x^2) = {0, 1} := by norm_num"),
    ]


def finite_cards() -> list[Card]:
    s12 = set_literal(i(1), i(2))
    s23 = set_literal(i(2), i(3))
    s123 = set_literal(i(1), i(2), i(3))
    s456 = set_literal(i(4), i(5), i(6))
    return [
        make("disc_size_empty_closed", "finite_set_cardinality_instance", "introductory", "The empty finite set has size 0.", eq(size(oms("set1", "emptyset")), i(0)), "Evaluate the cardinality of the empty finite set.", FINITE_STEPS, "example : (∅ : Finset ℤ).card = 0 := by norm_num"),
        make("disc_size_singleton_closed", "finite_set_cardinality_instance", "introductory", "The finite set {7} has size 1.", eq(size(set_literal(i(7))), i(1)), "List the unique element and count it.", FINITE_STEPS, "example : ({7} : Finset ℤ).card = 1 := by norm_num"),
        make("disc_size_union_two_overlap", "finite_set_cardinality_instance", "standard", "The finite set {1,2} ∪ {2,3} has size 3.", eq(size(union(s12, s23)), i(3)), "Form the union and discard the duplicated element 2.", FINITE_STEPS, "example : (({1, 2} : Finset ℤ) ∪ {2, 3}).card = 3 := by norm_num"),
        make("disc_size_intersection_two_overlap", "finite_set_cardinality_instance", "standard", "The finite set {1,2} ∩ {2,3} has size 1.", eq(size(intersection(s12, s23)), i(1)), "List the sole common element 2.", FINITE_STEPS, "example : (({1, 2} : Finset ℤ) ∩ {2, 3}).card = 1 := by norm_num"),
        make("disc_size_difference_closed", "finite_set_cardinality_instance", "standard", "The finite set {1,2,3} \\ {2} has size 2.", eq(size(difference(s123, set_literal(i(2)))), i(2)), "Remove the displayed element 2 and count the two remaining elements.", FINITE_STEPS, "example : (({1, 2, 3} : Finset ℤ) \\ {2}).card = 2 := by native_decide"),
        make("disc_size_cartesian_product_two_three", "finite_set_cardinality_instance", "standard", "The Cartesian product {1,2} × {4,5,6} has size 6.", eq(size(product(s12, s456)), i(6)), "Enumerate the two choices in the first coordinate and three in the second.", FINITE_STEPS, "example : (({1, 2} : Finset ℤ).product {4, 5, 6}).card = 6 := by norm_num"),
        make("disc_closed_inclusion_exclusion", "finite_set_cardinality_instance", "advanced", "For finite sets {1,2} and {2,3}, size of the union plus size of the intersection equals the sum of the two sizes.", eq(plus(size(union(s12, s23)), size(intersection(s12, s23))), plus(size(s12), size(s23))), "Count the union and intersection, then verify the closed inclusion-exclusion equation.", FINITE_STEPS, "example : (({1, 2} : Finset ℤ) ∪ {2, 3}).card + (({1, 2} : Finset ℤ) ∩ {2, 3}).card = ({1, 2} : Finset ℤ).card + ({2, 3} : Finset ℤ).card := by norm_num"),
    ]


def pigeonhole_cards() -> list[Card]:
    a, b, c, d = map(v, ("a", "b", "c", "d"))
    two_boxes = set_literal(i(0), i(1))
    three_boxes = set_literal(i(0), i(1), i(2))
    return [
        make("disc_pigeonhole_three_into_two", "explicit_pigeonhole_instance", "standard", "For all integers a, b, c in {0,1}, either a = b, a = c, or b = c.", typed_forall(("a", "b", "c"), "Z", implies(and_(member(a, two_boxes), member(b, two_boxes), member(c, two_boxes)), or_(eq(a, b), eq(a, c), eq(b, c)))), "Exhaust the two possible boxes for each of the three integers.", PIGEONHOLE_STEPS, """example (a b c : ℤ) (ha : a = 0 ∨ a = 1) (hb : b = 0 ∨ b = 1) (hc : c = 0 ∨ c = 1) : a = b ∨ a = c ∨ b = c := by
  rcases ha with ha | ha <;> rcases hb with hb | hb <;> rcases hc with hc | hc <;> omega"""),
        make("disc_pigeonhole_four_into_three", "explicit_pigeonhole_instance", "advanced", "For all integers a, b, c, d in {0,1,2}, some two among a, b, c, d are equal.", typed_forall(("a", "b", "c", "d"), "Z", implies(and_(member(a, three_boxes), member(b, three_boxes), member(c, three_boxes), member(d, three_boxes)), or_(eq(a, b), eq(a, c), eq(a, d), eq(b, c), eq(b, d), eq(c, d)))), "Exhaust the three possible boxes for four integers and select a repeated label.", PIGEONHOLE_STEPS, """example (a b c d : ℤ) (ha : a = 0 ∨ a = 1 ∨ a = 2) (hb : b = 0 ∨ b = 1 ∨ b = 2) (hc : c = 0 ∨ c = 1 ∨ c = 2) (hd : d = 0 ∨ d = 1 ∨ d = 2) : a = b ∨ a = c ∨ a = d ∨ b = c ∨ b = d ∨ c = d := by
  rcases ha with ha | ha | ha <;> rcases hb with hb | hb | hb <;> rcases hc with hc | hc | hc <;> rcases hd with hd | hd | hd <;> omega"""),
    ]


def cards() -> list[Card]:
    current = relation_cards() + map_cards() + finite_cards() + pigeonhole_cards()
    identifiers = [card.id for card in current]
    if len(current) != 21 or len(identifiers) != len(set(identifiers)):
        raise RuntimeError("expected exactly 21 uniquely identified cards")
    canonical = [canonicalize_retrieval_openmath_xml(card.openmath_xml) for card in current]
    if len(canonical) != len(set(canonical)):
        raise RuntimeError("candidate manifest contains duplicate canonical OpenMath")
    return current


def verify_lean(current: list[Card]) -> None:
    workspace = ROOT / "pals-agent" / "lean-workspace"
    source = "import Mathlib\n\n" + "\n\n".join(card.lean_witness for card in current) + "\n"
    with tempfile.NamedTemporaryFile("w", suffix=".lean", dir=workspace, delete=False, encoding="utf-8") as handle:
        handle.write(source)
        lean_file = Path(handle.name)
    try:
        completed = subprocess.run(["lake", "env", "lean", str(lean_file)], cwd=workspace, text=True, capture_output=True, check=False)
    finally:
        lean_file.unlink(missing_ok=True)
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
        identifier, separator, openmath_xml = line.partition("\t")
        if not separator or not identifier or not openmath_xml:
            raise RuntimeError("local Draft XML query returned a malformed row")
        existing[identifier] = openmath_xml
    if len(existing) != expected_count:
        raise RuntimeError("local Draft XML query count did not match Draft count")
    duplicate_ids = sorted(set(card.id for card in current) & set(existing))
    if duplicate_ids:
        raise RuntimeError(f"candidate IDs already exist in local DB: {duplicate_ids}")
    strict_existing: set[str] = set()
    legacy_fallback: list[str] = []
    for identifier, openmath_xml in existing.items():
        try:
            strict_existing.add(canonicalize_retrieval_openmath_xml(openmath_xml))
        except MathXMLValidationError:
            legacy_fallback.append(identifier)
    strict_candidates = {canonicalize_retrieval_openmath_xml(card.openmath_xml) for card in current}
    if strict_candidates & strict_existing:
        raise RuntimeError("candidate canonical OpenMath duplicates a strict current-profile local Draft")
    legacy_existing = {canonicalize_openmath_xml(openmath_xml) for openmath_xml in existing.values()}
    legacy_candidates = {canonicalize_openmath_xml(card.openmath_xml) for card in current}
    if legacy_candidates & legacy_existing:
        raise RuntimeError("candidate canonical OpenMath duplicates an existing local Draft")
    return tuple(sorted(legacy_fallback))


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
    payload = {
        "schema_version": "pals.discrete-relations-maps-combinatorics-candidates.v1",
        "source": "PALS first-party authored, generic-OpenMath and Lean-verified candidate set",
        "current_profile_card_count": len(current),
        "domain_counts": {
            "ordered_relation_instance": len(relation_cards()),
            "scalar_and_finite_set_map_instance": len(map_cards()),
            "finite_set_cardinality_instance": len(finite_cards()),
            "explicit_pigeonhole_instance": len(pigeonhole_cards()),
        },
        "scope_note": "Generic OpenMath has no type constructor for relations, functions, finite sets, or cardinal numbers. Relation cards are concrete integer-order instances; map cards use scalar equations or closed finite-set images; cardinality cards use only closed finite literals; pigeonhole cards are explicitly enumerated boxes rather than a general function theorem.",
        "typed_backlog": [
            {"topic": "equivalence relations and partial orders", "examples": ["R is reflexive, symmetric, and transitive on X", "R is a partial order on X"], "minimum_symbols": ["pals2:relation", "pals2:relation_apply", "pals2:reflexive_on", "pals2:symmetric_on", "pals2:transitive_on", "pals2:antisymmetric_on"], "why_current_profile_cannot_represent_it": "A bare generic term cannot be bound as a relation X × X → Prop, so relation properties cannot be linked to one carrier set."},
            {"topic": "injective and surjective maps", "examples": ["f:X→Y is injective", "f:X→Y is surjective"], "minimum_symbols": ["pals2:typed_function", "pals2:function_apply", "pals2:injective", "pals2:surjective"], "why_current_profile_cannot_represent_it": "The generic profile cannot bind a function together with coherent source and target sorts, nor state its universal mapping property."},
            {"topic": "general finite cardinality and binomial coefficients", "examples": ["|A∪B|+|A∩B|=|A|+|B|", "choose(n,k) Pascal identity"], "minimum_symbols": ["pals2:finite_set", "pals2:cardinality", "combinat1:binomial"], "why_current_profile_cannot_represent_it": "set1:size has no finite-set or natural-number dependent sort in the generic profile, and no supported binomial-coefficient symbol is registered."},
            {"topic": "general pigeonhole principle", "examples": ["Every f:{1,…,n+1}→{1,…,n} has a collision"], "minimum_symbols": ["pals2:finite_set", "pals2:typed_function", "pals2:injective", "pals2:cardinality", "pals2:cardinality_lt"], "why_current_profile_cannot_represent_it": "It quantifies a typed function and compares linked finite cardinalities; the explicitly enumerated instances above avoid that unsupported abstraction."},
        ],
        "validation_contract": {
            "generic_openmath": "All cards run statement-semantics validation, current retrieval C14N, and exact C14N validation during generation.",
            "lean": "Pass --verify-lean to compile one temporary file containing every witness in the pinned Lean workspace.",
            "local_db": "Pass --verify-db --expected-db-count 253 to perform read-only ID and C14N collision checks against the local legacy Draft DB.",
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
