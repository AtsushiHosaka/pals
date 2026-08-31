#!/usr/bin/env python3
"""Generate the second first-party, local-only diversified Draft batch.

The generated manifest is an authoring artifact for the legacy local catalog.
It deliberately does not modify the packaged PFI seed or any shared database.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path


OPENMATH = "http://www.openmath.org/OpenMath"


@dataclass(frozen=True)
class Card:
    id: str
    domain: str
    canonical_statement: str
    openmath_xml: str
    proof_strategy: str
    sketch_steps: tuple[str, str, str]
    lean_witness: str


def tag(name: str, body: str) -> str:
    return f"<{name}>{body}</{name}>"


def oms(cd: str, name: str) -> str:
    return f'<OMS cd="{cd}" name="{name}"/>'


def var(name: str) -> str:
    return f'<OMV name="{name}"/>'


def integer(value: int) -> str:
    return f"<OMI>{value}</OMI>"


def application(operator: str, *arguments: str) -> str:
    return tag("OMA", operator + "".join(arguments))


def standard(cd: str, name: str, *arguments: str) -> str:
    return application(oms(cd, name), *arguments)


def pals(name: str, *arguments: str) -> str:
    return application(oms("pals1", name), *arguments)


def plus(*arguments: str) -> str:
    return standard("arith1", "plus", *arguments)


def times(*arguments: str) -> str:
    return standard("arith1", "times", *arguments)


def minus(left: str, right: str) -> str:
    return standard("arith1", "minus", left, right)


def neg(value: str) -> str:
    return standard("arith1", "unary_minus", value)


def power(base: str, exponent: str | int) -> str:
    encoded_exponent = integer(exponent) if isinstance(exponent, int) else exponent
    return standard("arith1", "power", base, encoded_exponent)


def absolute(value: str) -> str:
    return standard("arith1", "abs", value)


def gcd(left: str, right: str) -> str:
    return standard("arith1", "gcd", left, right)


def lcm(left: str, right: str) -> str:
    return standard("arith1", "lcm", left, right)


def equal(left: str, right: str) -> str:
    return standard("relation1", "eq", left, right)


def leq(left: str, right: str) -> str:
    return standard("relation1", "leq", left, right)


def lt(left: str, right: str) -> str:
    return standard("relation1", "lt", left, right)


def implies(left: str, right: str) -> str:
    return standard("logic1", "implies", left, right)


def equivalent(left: str, right: str) -> str:
    return standard("logic1", "equivalent", left, right)


def conjunction(*arguments: str) -> str:
    return standard("logic1", "and", *arguments)


def disjunction(*arguments: str) -> str:
    return standard("logic1", "or", *arguments)


def union(left: str, right: str) -> str:
    return standard("set1", "union", left, right)


def intersection(left: str, right: str) -> str:
    return standard("set1", "intersect", left, right)


def difference(left: str, right: str) -> str:
    return standard("set1", "setdiff", left, right)


def subset(left: str, right: str) -> str:
    return standard("set1", "subset", left, right)


def emptyset() -> str:
    return oms("set1", "emptyset")


def forall(names: tuple[str, ...], body: str) -> str:
    return tag(
        "OMBIND",
        oms("quant1", "forall")
        + tag("OMBVAR", "".join(var(name) for name in names))
        + body,
    )


def typed_forall(names: tuple[str, ...], set_name: str, body: str) -> str:
    assumptions = tuple(standard("set1", "in", var(name), oms("setname1", set_name)) for name in names)
    premise = assumptions[0] if len(assumptions) == 1 else conjunction(*assumptions)
    return forall(names, implies(premise, body))


def openmath(body: str) -> str:
    return f'<OMOBJ xmlns="{OPENMATH}" version="2.0">{body}</OMOBJ>'


def make_card(
    identifier: str,
    domain: str,
    statement: str,
    proposition: str,
    strategy: str,
    witness: str,
    steps: tuple[str, str, str],
) -> Card:
    return Card(
        id=identifier,
        domain=domain,
        canonical_statement=statement,
        openmath_xml=openmath(proposition),
        proof_strategy=strategy,
        sketch_steps=steps,
        lean_witness=witness,
    )


def algebra_cards() -> list[Card]:
    real = "elementary_algebra"
    x, y, z, w = map(var, ("x", "y", "z", "w"))
    return [
        make_card(
            "algebra_add_commutative_integer",
            real,
            "Show that for all integers a and b, a + b = b + a.",
            typed_forall(("a", "b"), "Z", equal(plus(var("a"), var("b")), plus(var("b"), var("a")))),
            "Use commutativity of integer addition to exchange the two summands.",
            "example (a b : ℤ) : a + b = b + a := by ring",
            ("setup: Introduce integers a and b.", "apply_theorem: Commute the addition.", "conclude: The two sides agree."),
        ),
        make_card(
            "algebra_mul_commutative_integer",
            real,
            "Show that for all integers a and b, a * b = b * a.",
            typed_forall(("a", "b"), "Z", equal(times(var("a"), var("b")), times(var("b"), var("a")))),
            "Use commutativity of integer multiplication to exchange the factors.",
            "example (a b : ℤ) : a * b = b * a := by ring",
            ("setup: Introduce integers a and b.", "apply_theorem: Commute the multiplication.", "conclude: The products agree."),
        ),
        make_card(
            "algebra_add_associative_real",
            real,
            "Show that for all real x, y, and z, (x + y) + z = x + (y + z).",
            typed_forall(("x", "y", "z"), "R", equal(plus(plus(x, y), z), plus(x, plus(y, z)))),
            "Reassociate the sum without changing the order of the three terms.",
            "example (x y z : ℝ) : (x + y) + z = x + (y + z) := by ring",
            ("setup: Introduce real x, y, z.", "calculation: Reassociate the sum.", "conclude: Both groupings have the same value."),
        ),
        make_card(
            "algebra_mul_associative_real",
            real,
            "Show that for all real x, y, and z, (x * y) * z = x * (y * z).",
            typed_forall(("x", "y", "z"), "R", equal(times(times(x, y), z), times(x, times(y, z)))),
            "Reassociate the product without changing the order of the three factors.",
            "example (x y z : ℝ) : (x * y) * z = x * (y * z) := by ring",
            ("setup: Introduce real x, y, z.", "calculation: Reassociate the product.", "conclude: Both groupings have the same value."),
        ),
        make_card(
            "algebra_left_distributive_real",
            real,
            "Show that for all real x, y, and z, x * (y + z) = x*y + x*z.",
            typed_forall(("x", "y", "z"), "R", equal(times(x, plus(y, z)), plus(times(x, y), times(x, z)))),
            "Distribute the common left factor x across the sum y + z.",
            "example (x y z : ℝ) : x * (y + z) = x*y + x*z := by ring",
            ("setup: Introduce real x, y, z.", "calculation: Distribute x across the sum.", "conclude: Collect the two resulting products."),
        ),
        make_card(
            "algebra_right_distributive_real",
            real,
            "Show that for all real x, y, and z, (x + y) * z = x*z + y*z.",
            typed_forall(("x", "y", "z"), "R", equal(times(plus(x, y), z), plus(times(x, z), times(y, z)))),
            "Distribute the common right factor z across the sum x + y.",
            "example (x y z : ℝ) : (x + y) * z = x*z + y*z := by ring",
            ("setup: Introduce real x, y, z.", "calculation: Distribute z across the sum.", "conclude: Collect the two resulting products."),
        ),
        make_card(
            "algebra_sub_self_real",
            real,
            "Show that for every real x, x - x = 0.",
            typed_forall(("x",), "R", equal(minus(x, x), integer(0))),
            "Subtracting a real number from itself leaves the additive identity.",
            "example (x : ℝ) : x - x = 0 := by ring",
            ("setup: Introduce a real x.", "calculation: Cancel x with its additive inverse.", "conclude: The result is zero."),
        ),
        make_card(
            "algebra_add_neg_cancel_real",
            real,
            "Show that for every real x, x + (-x) = 0.",
            typed_forall(("x",), "R", equal(plus(x, neg(x)), integer(0))),
            "Pair x with its additive inverse to obtain zero.",
            "example (x : ℝ) : x + (-x) = 0 := by ring",
            ("setup: Introduce a real x.", "apply_theorem: Use additive inverse cancellation.", "conclude: The sum is zero."),
        ),
        make_card(
            "algebra_sub_add_cancel_real",
            real,
            "Show that for all real x and y, x - y + y = x.",
            typed_forall(("x", "y"), "R", equal(plus(minus(x, y), y), x)),
            "Rewrite subtraction as addition of an inverse, then cancel -y with y.",
            "example (x y : ℝ) : x - y + y = x := by ring",
            ("setup: Introduce real x and y.", "calculation: Rewrite x - y as x + (-y).", "conclude: Cancel -y + y."),
        ),
        make_card(
            "algebra_add_sub_cancel_real",
            real,
            "Show that for all real x and y, x + y - y = x.",
            typed_forall(("x", "y"), "R", equal(minus(plus(x, y), y), x)),
            "Rewrite subtraction as addition of an inverse, then cancel y with -y.",
            "example (x y : ℝ) : x + y - y = x := by ring",
            ("setup: Introduce real x and y.", "calculation: Rewrite subtraction using -y.", "conclude: Cancel y + (-y)."),
        ),
        make_card(
            "algebra_neg_neg_real",
            real,
            "Show that for every real x, -(-x) = x.",
            typed_forall(("x",), "R", equal(neg(neg(x)), x)),
            "Taking the additive inverse twice restores the original value.",
            "example (x : ℝ) : -(-x) = x := by ring",
            ("setup: Introduce a real x.", "apply_theorem: Simplify the double inverse.", "conclude: The result is x."),
        ),
        make_card(
            "algebra_zero_mul_real",
            real,
            "Show that for every real x, 0 * x = 0.",
            typed_forall(("x",), "R", equal(times(integer(0), x), integer(0))),
            "Zero annihilates every real factor under multiplication.",
            "example (x : ℝ) : 0 * x = 0 := by ring",
            ("setup: Introduce a real x.", "apply_theorem: Use zero multiplication.", "conclude: The product is zero."),
        ),
        make_card(
            "algebra_square_difference_real",
            real,
            "Show that for all real x and y, (x - y)^2 = x^2 - 2*x*y + y^2.",
            typed_forall(("x", "y"), "R", equal(power(minus(x, y), 2), plus(minus(power(x, 2), times(integer(2), x, y)), power(y, 2)))),
            "Expand the square of a difference and combine the two mixed negative terms.",
            "example (x y : ℝ) : (x - y)^2 = x^2 - 2*x*y + y^2 := by ring",
            ("setup: Introduce real x and y.", "calculation: Expand (x - y)^2.", "conclude: Collect the mixed terms."),
        ),
        make_card(
            "algebra_sum_cubes_factor_real",
            real,
            "Show that for all real x and y, x^3 + y^3 = (x + y) * (x^2 - x*y + y^2).",
            typed_forall(("x", "y"), "R", equal(plus(power(x, 3), power(y, 3)), times(plus(x, y), plus(minus(power(x, 2), times(x, y)), power(y, 2))))),
            "Expand the proposed factorization and cancel the opposite cubic cross terms.",
            "example (x y : ℝ) : x^3 + y^3 = (x + y) * (x^2 - x*y + y^2) := by ring",
            ("setup: Introduce real x and y.", "calculation: Distribute the proposed factors.", "conclude: Cancel cross terms to recover the sum of cubes."),
        ),
        make_card(
            "algebra_difference_cubes_factor_real",
            real,
            "Show that for all real x and y, x^3 - y^3 = (x - y) * (x^2 + x*y + y^2).",
            typed_forall(("x", "y"), "R", equal(minus(power(x, 3), power(y, 3)), times(minus(x, y), plus(power(x, 2), times(x, y), power(y, 2))))),
            "Expand the proposed factorization and cancel the opposite cubic cross terms.",
            "example (x y : ℝ) : x^3 - y^3 = (x - y) * (x^2 + x*y + y^2) := by ring",
            ("setup: Introduce real x and y.", "calculation: Distribute the proposed factors.", "conclude: Cancel cross terms to recover the difference of cubes."),
        ),
    ]


def order_cards() -> list[Card]:
    domain = "order_and_absolute_value"
    x, y, z = map(var, ("x", "y", "z"))
    return [
        make_card("order_le_refl_real", domain, "Show that for every real x, x ≤ x.", typed_forall(("x",), "R", leq(x, x)), "Every ordered value is less than or equal to itself.", "example (x : ℝ) : x ≤ x := le_rfl", ("setup: Introduce x.", "apply_theorem: Use reflexivity of ≤.", "conclude: x ≤ x.")),
        make_card("order_lt_add_one_real", domain, "Show that for every real x, x < x + 1.", typed_forall(("x",), "R", lt(x, plus(x, integer(1)))), "Adding the positive number one strictly increases a real number.", "example (x : ℝ) : x < x + 1 := by linarith", ("setup: Introduce x.", "derive: Note that 0 < 1.", "conclude: Add x to the strict inequality.")),
        make_card("order_add_le_add_right_real", domain, "Show that for all real x, y, and z, if x ≤ y then x + z ≤ y + z.", typed_forall(("x", "y", "z"), "R", implies(leq(x, y), leq(plus(x, z), plus(y, z)))), "Add the same real z to both sides of the inequality.", "example (x y z : ℝ) (h : x ≤ y) : x + z ≤ y + z := by linarith", ("setup: Introduce x, y, z and x ≤ y.", "derive: Add z to both sides.", "conclude: Preserve the inequality order.")),
        make_card("order_add_le_add_left_real", domain, "Show that for all real x, y, and z, if y ≤ z then x + y ≤ x + z.", typed_forall(("x", "y", "z"), "R", implies(leq(y, z), leq(plus(x, y), plus(x, z)))), "Add the same real x to both sides of the inequality.", "example (x y z : ℝ) (h : y ≤ z) : x + y ≤ x + z := by linarith", ("setup: Introduce x, y, z and y ≤ z.", "derive: Add x to both sides.", "conclude: Preserve the inequality order.")),
        make_card("order_sub_le_sub_right_real", domain, "Show that for all real x, y, and z, if x ≤ y then x - z ≤ y - z.", typed_forall(("x", "y", "z"), "R", implies(leq(x, y), leq(minus(x, z), minus(y, z)))), "Subtract the same real z from both sides of the inequality.", "example (x y z : ℝ) (h : x ≤ y) : x - z ≤ y - z := by linarith", ("setup: Introduce x, y, z and x ≤ y.", "derive: Add -z to both sides.", "conclude: Rewrite the result as subtraction.")),
        make_card("order_neg_reverses_real", domain, "Show that for all real x and y, if x ≤ y then -y ≤ -x.", typed_forall(("x", "y"), "R", implies(leq(x, y), leq(neg(y), neg(x)))), "Multiply both sides of x ≤ y by the negative scalar -1, which reverses the order.", "example (x y : ℝ) (h : x ≤ y) : -y ≤ -x := by linarith", ("setup: Introduce x, y and x ≤ y.", "derive: Negate both sides.", "conclude: Reverse the inequality direction.")),
        make_card("order_neg_abs_le_real", domain, "Show that for every real x, -|x| ≤ x.", typed_forall(("x",), "R", leq(neg(absolute(x)), x)), "Absolute value bounds a real number below as well as above.", "example (x : ℝ) : -|x| ≤ x := neg_abs_le x", ("setup: Introduce x.", "apply_theorem: Use the lower absolute-value bound.", "conclude: -|x| ≤ x.")),
        make_card("order_le_abs_real", domain, "Show that for every real x, x ≤ |x|.", typed_forall(("x",), "R", leq(x, absolute(x))), "Absolute value is an upper bound for the underlying real number.", "example (x : ℝ) : x ≤ |x| := le_abs_self x", ("setup: Introduce x.", "apply_theorem: Use the upper absolute-value bound.", "conclude: x ≤ |x|.")),
        make_card("order_abs_neg_real", domain, "Show that for every real x, |-x| = |x|.", typed_forall(("x",), "R", equal(absolute(neg(x)), absolute(x))), "Negating a real number changes its sign but not its magnitude.", "example (x : ℝ) : |-x| = |x| := abs_neg x", ("setup: Introduce x.", "apply_theorem: Use invariance of absolute value under negation.", "conclude: The magnitudes agree.")),
        make_card("order_abs_mul_real", domain, "Show that for all real x and y, |x*y| = |x|*|y|.", typed_forall(("x", "y"), "R", equal(absolute(times(x, y)), times(absolute(x), absolute(y)))), "Absolute value is multiplicative over real products.", "example (x y : ℝ) : |x * y| = |x| * |y| := abs_mul x y", ("setup: Introduce x and y.", "apply_theorem: Use multiplicativity of absolute value.", "conclude: Split the magnitude across the product.")),
        make_card("order_abs_sub_comm_real", domain, "Show that for all real x and y, |x - y| = |y - x|.", typed_forall(("x", "y"), "R", equal(absolute(minus(x, y)), absolute(minus(y, x)))), "The two differences are negatives of one another, and absolute value removes the sign.", "example (x y : ℝ) : |x - y| = |y - x| := abs_sub_comm x y", ("setup: Introduce x and y.", "derive: Observe y - x = -(x - y).", "conclude: Apply absolute-value sign invariance.")),
        make_card("order_abs_eq_zero_real", domain, "Show that for every real x, |x| = 0 if and only if x = 0.", typed_forall(("x",), "R", equivalent(equal(absolute(x), integer(0)), equal(x, integer(0)))), "Use the zero characterization of absolute value.", "example (x : ℝ) : |x| = 0 ↔ x = 0 := abs_eq_zero", ("setup: Introduce x.", "apply_theorem: Characterize when absolute value vanishes.", "conclude: The two equalities are equivalent.")),
        make_card("order_abs_square_real", domain, "Show that for every real x, |x^2| = x^2.", typed_forall(("x",), "R", equal(absolute(power(x, 2)), power(x, 2))), "First prove x^2 is nonnegative, then remove absolute value using that bound.", "example (x : ℝ) : |x^2| = x^2 := abs_of_nonneg (sq_nonneg x)", ("setup: Introduce x.", "derive: Establish 0 ≤ x^2.", "conclude: Simplify the absolute value of a nonnegative term.")),
        make_card("order_add_nonnegative_left_real", domain, "Show that for all real x and y, if 0 ≤ x then y ≤ x + y.", typed_forall(("x", "y"), "R", implies(leq(integer(0), x), leq(y, plus(x, y)))), "A nonnegative summand cannot decrease a real number.", "example (x y : ℝ) (hx : 0 ≤ x) : y ≤ x + y := by linarith", ("setup: Introduce x, y and 0 ≤ x.", "derive: Add y to both sides of 0 ≤ x.", "conclude: Reorder the sum as y ≤ x + y.")),
        make_card("order_abs_triangle_real", domain, "Show that for all real x and y, |x + y| ≤ |x| + |y|.", typed_forall(("x", "y"), "R", leq(absolute(plus(x, y)), plus(absolute(x), absolute(y)))), "Apply the triangle inequality for absolute value.", "example (x y : ℝ) : |x + y| ≤ |x| + |y| := abs_add_le x y", ("setup: Introduce real x and y.", "apply_theorem: Use the absolute-value triangle inequality.", "conclude: Bound the sum by the sum of magnitudes.")),
    ]


def number_cards() -> list[Card]:
    domain = "elementary_number_theory"
    n, m, k = map(var, ("n", "m", "k"))
    return [
        make_card("nat_gcd_zero_left", domain, "Show that for every natural number n, gcd(0, n) = n.", typed_forall(("n",), "N", equal(gcd(integer(0), n), n)), "Use the zero identity for gcd on the left argument.", "example (n : ℕ) : Nat.gcd 0 n = n := by simp", ("setup: Introduce n.", "apply_theorem: Simplify gcd with zero on the left.", "conclude: The result is n.")),
        make_card("nat_gcd_self", domain, "Show that for every natural number n, gcd(n, n) = n.", typed_forall(("n",), "N", equal(gcd(n, n), n)), "A number is the greatest common divisor of itself and itself.", "example (n : ℕ) : Nat.gcd n n = n := Nat.gcd_self n", ("setup: Introduce n.", "apply_theorem: Use the self identity of gcd.", "conclude: gcd(n, n) is n.")),
        make_card("nat_gcd_one_right", domain, "Show that for every natural number n, gcd(n, 1) = 1.", typed_forall(("n",), "N", equal(gcd(n, integer(1)), integer(1))), "One is the only positive common divisor forced by a unit argument.", "example (n : ℕ) : Nat.gcd n 1 = 1 := Nat.gcd_one_right n", ("setup: Introduce n.", "apply_theorem: Use the gcd identity with one.", "conclude: The gcd is one.")),
        make_card("nat_gcd_one_left", domain, "Show that for every natural number n, gcd(1, n) = 1.", typed_forall(("n",), "N", equal(gcd(integer(1), n), integer(1))), "Swap the unit to the left argument of the gcd identity.", "example (n : ℕ) : Nat.gcd 1 n = 1 := Nat.gcd_one_left n", ("setup: Introduce n.", "apply_theorem: Use the gcd identity with one.", "conclude: The gcd is one.")),
        make_card("nat_gcd_associative", domain, "Show that for all natural numbers m, n, and k, gcd(gcd(m, n), k) = gcd(m, gcd(n, k)).", typed_forall(("m", "n", "k"), "N", equal(gcd(gcd(m, n), k), gcd(m, gcd(n, k)))), "Greatest common divisor is associative, so regroup the three arguments.", "example (m n k : ℕ) : Nat.gcd (Nat.gcd m n) k = Nat.gcd m (Nat.gcd n k) := Nat.gcd_assoc m n k", ("setup: Introduce m, n, k.", "apply_theorem: Reassociate gcd.", "conclude: The two groupings agree.")),
        make_card("nat_lcm_zero_right", domain, "Show that for every natural number n, lcm(n, 0) = 0.", typed_forall(("n",), "N", equal(lcm(n, integer(0)), integer(0))), "Zero is a common multiple of every natural number, and it is the least one in this convention.", "example (n : ℕ) : Nat.lcm n 0 = 0 := Nat.lcm_zero_right n", ("setup: Introduce n.", "apply_theorem: Simplify lcm with zero on the right.", "conclude: The lcm is zero.")),
        make_card("nat_lcm_zero_left", domain, "Show that for every natural number n, lcm(0, n) = 0.", typed_forall(("n",), "N", equal(lcm(integer(0), n), integer(0))), "Use the symmetric zero identity for lcm.", "example (n : ℕ) : Nat.lcm 0 n = 0 := Nat.lcm_zero_left n", ("setup: Introduce n.", "apply_theorem: Simplify lcm with zero on the left.", "conclude: The lcm is zero.")),
        make_card("nat_lcm_self", domain, "Show that for every natural number n, lcm(n, n) = n.", typed_forall(("n",), "N", equal(lcm(n, n), n)), "A number is the least common multiple of itself and itself.", "example (n : ℕ) : Nat.lcm n n = n := Nat.lcm_self n", ("setup: Introduce n.", "apply_theorem: Use the self identity of lcm.", "conclude: lcm(n, n) is n.")),
        make_card("nat_lcm_one_right", domain, "Show that for every natural number n, lcm(n, 1) = n.", typed_forall(("n",), "N", equal(lcm(n, integer(1)), n)), "Every number is already a multiple of one.", "example (n : ℕ) : Nat.lcm n 1 = n := Nat.lcm_one_right n", ("setup: Introduce n.", "apply_theorem: Use the lcm identity with one.", "conclude: The lcm is n.")),
        make_card("nat_lcm_one_left", domain, "Show that for every natural number n, lcm(1, n) = n.", typed_forall(("n",), "N", equal(lcm(integer(1), n), n)), "Swap the unit to the left argument of the lcm identity.", "example (n : ℕ) : Nat.lcm 1 n = n := Nat.lcm_one_left n", ("setup: Introduce n.", "apply_theorem: Use the lcm identity with one.", "conclude: The lcm is n.")),
        make_card("nat_lcm_associative", domain, "Show that for all natural numbers m, n, and k, lcm(lcm(m, n), k) = lcm(m, lcm(n, k)).", typed_forall(("m", "n", "k"), "N", equal(lcm(lcm(m, n), k), lcm(m, lcm(n, k)))), "Least common multiple is associative, so regroup the three arguments.", "example (m n k : ℕ) : Nat.lcm (Nat.lcm m n) k = Nat.lcm m (Nat.lcm n k) := Nat.lcm_assoc m n k", ("setup: Introduce m, n, k.", "apply_theorem: Reassociate lcm.", "conclude: The two groupings agree.")),
        make_card("nat_power_zero", domain, "Show that for every natural number n, n^0 = 1.", typed_forall(("n",), "N", equal(power(n, 0), integer(1))), "The zeroth power is the multiplicative identity.", "example (n : ℕ) : n^0 = 1 := by simp", ("setup: Introduce n.", "apply_theorem: Use the zeroth-power identity.", "conclude: The result is one.")),
        make_card("nat_one_power", domain, "Show that for every natural number n, 1^n = 1.", typed_forall(("n",), "N", equal(power(integer(1), n), integer(1))), "The multiplicative identity remains one under natural powers.", "example (n : ℕ) : 1^n = 1 := by simp", ("setup: Introduce n.", "apply_theorem: Use the one-power identity.", "conclude: The result is one.")),
        make_card("nat_power_one", domain, "Show that for every natural number n, n^1 = n.", typed_forall(("n",), "N", equal(power(n, 1), n)), "The first power leaves the base unchanged.", "example (n : ℕ) : n^1 = n := by simp", ("setup: Introduce n.", "apply_theorem: Use the first-power identity.", "conclude: The result is n.")),
        make_card("nat_zero_power_positive", domain, "Show that for every natural number n, if 0 < n then 0^n = 0.", typed_forall(("n",), "N", implies(lt(integer(0), n), equal(power(integer(0), n), integer(0)))), "A positive natural exponent leaves zero equal to zero.", "example (n : ℕ) (hn : 0 < n) : 0^n = 0 := zero_pow (Nat.ne_of_gt hn)", ("setup: Introduce n and 0 < n.", "apply_theorem: Use the positive-exponent zero-power law.", "conclude: The power is zero.")),
    ]


def set_cards() -> list[Card]:
    domain = "basic_set_theory"
    a, b, c = map(var, ("A", "B", "C"))
    return [
        make_card("set_union_commutative", domain, "Show that for all sets A and B, A ∪ B = B ∪ A.", forall(("A", "B"), equal(union(a, b), union(b, a))), "Prove extensional equality and commute the membership disjunction.", "example {α : Type} (A B : Set α) : A ∪ B = B ∪ A := by ext x; simp [or_comm]", ("setup: Apply set extensionality.", "derive: Rewrite union membership as a disjunction.", "conclude: Commute the disjunction.")),
        make_card("set_intersection_commutative", domain, "Show that for all sets A and B, A ∩ B = B ∩ A.", forall(("A", "B"), equal(intersection(a, b), intersection(b, a))), "Prove extensional equality and commute the membership conjunction.", "example {α : Type} (A B : Set α) : A ∩ B = B ∩ A := by ext x; simp [and_comm]", ("setup: Apply set extensionality.", "derive: Rewrite intersection membership as a conjunction.", "conclude: Commute the conjunction.")),
        make_card("set_union_associative", domain, "Show that for all sets A, B, and C, (A ∪ B) ∪ C = A ∪ (B ∪ C).", forall(("A", "B", "C"), equal(union(union(a, b), c), union(a, union(b, c)))), "Prove extensional equality and reassociate the membership disjunction.", "example {α : Type} (A B C : Set α) : (A ∪ B) ∪ C = A ∪ (B ∪ C) := by ext x; simp [or_assoc]", ("setup: Apply set extensionality.", "derive: Rewrite both unions as disjunctions.", "conclude: Reassociate the disjunction.")),
        make_card("set_intersection_associative", domain, "Show that for all sets A, B, and C, (A ∩ B) ∩ C = A ∩ (B ∩ C).", forall(("A", "B", "C"), equal(intersection(intersection(a, b), c), intersection(a, intersection(b, c)))), "Prove extensional equality and reassociate the membership conjunction.", "example {α : Type} (A B C : Set α) : (A ∩ B) ∩ C = A ∩ (B ∩ C) := by ext x; simp [and_assoc]", ("setup: Apply set extensionality.", "derive: Rewrite both intersections as conjunctions.", "conclude: Reassociate the conjunction.")),
        make_card("set_union_idempotent", domain, "Show that for every set A, A ∪ A = A.", forall(("A",), equal(union(a, a), a)), "Prove extensional equality and simplify the duplicated membership disjunction.", "example {α : Type} (A : Set α) : A ∪ A = A := by ext x; simp", ("setup: Apply set extensionality.", "derive: Rewrite membership in A ∪ A.", "conclude: Simplify P ∨ P to P.")),
        make_card("set_intersection_idempotent", domain, "Show that for every set A, A ∩ A = A.", forall(("A",), equal(intersection(a, a), a)), "Prove extensional equality and simplify the duplicated membership conjunction.", "example {α : Type} (A : Set α) : A ∩ A = A := by ext x; simp", ("setup: Apply set extensionality.", "derive: Rewrite membership in A ∩ A.", "conclude: Simplify P ∧ P to P.")),
        make_card("set_union_empty_right", domain, "Show that for every set A, A ∪ ∅ = A.", forall(("A",), equal(union(a, emptyset()), a)), "The empty set contributes no possible member to a union.", "example {α : Type} (A : Set α) : A ∪ ∅ = A := by ext x; simp", ("setup: Apply set extensionality.", "derive: Rewrite membership in the union with ∅.", "conclude: The false branch disappears.")),
        make_card("set_union_empty_left", domain, "Show that for every set A, ∅ ∪ A = A.", forall(("A",), equal(union(emptyset(), a), a)), "The empty set contributes no possible member to a union.", "example {α : Type} (A : Set α) : ∅ ∪ A = A := by ext x; simp", ("setup: Apply set extensionality.", "derive: Rewrite membership in the union with ∅.", "conclude: The false branch disappears.")),
        make_card("set_intersection_empty", domain, "Show that for every set A, A ∩ ∅ = ∅.", forall(("A",), equal(intersection(a, emptyset()), emptyset())), "No element can belong to the empty set, so no element belongs to the intersection.", "example {α : Type} (A : Set α) : A ∩ ∅ = ∅ := by ext x; simp", ("setup: Apply set extensionality.", "derive: Rewrite intersection membership with ∅.", "conclude: The membership condition is false.")),
        make_card("set_difference_empty", domain, "Show that for every set A, A \\ ∅ = A.", forall(("A",), equal(difference(a, emptyset()), a)), "Subtracting no elements leaves a set unchanged.", "example {α : Type} (A : Set α) : A \\ ∅ = A := by ext x; simp", ("setup: Apply set extensionality.", "derive: Rewrite difference membership with ∅.", "conclude: The nonmembership condition is automatic.")),
        make_card("set_empty_difference", domain, "Show that for every set A, ∅ \\ A = ∅.", forall(("A",), equal(difference(emptyset(), a), emptyset())), "There are no elements in the left set to retain after subtraction.", "example {α : Type} (A : Set α) : ∅ \\ A = ∅ := by ext x; simp", ("setup: Apply set extensionality.", "derive: Rewrite difference membership from ∅.", "conclude: The membership condition is false.")),
        make_card("set_difference_self", domain, "Show that for every set A, A \\ A = ∅.", forall(("A",), equal(difference(a, a), emptyset())), "No element can be both a member of A and not a member of A.", "example {α : Type} (A : Set α) : A \\ A = ∅ := by ext x; simp", ("setup: Apply set extensionality.", "derive: Rewrite A \\ A membership.", "conclude: The resulting contradiction yields false.")),
        make_card("set_subset_refl", domain, "Show that every set A is a subset of itself.", forall(("A",), subset(a, a)), "Subset inclusion is reflexive: retain the same membership proof.", "example {α : Type} (A : Set α) : A ⊆ A := fun _ hx => hx", ("setup: Fix a set A and an element of A.", "derive: Keep the membership proof unchanged.", "conclude: A is a subset of itself.")),
        make_card("set_intersection_subset_right", domain, "Show that for all sets A and B, A ∩ B is a subset of B.", forall(("A", "B"), subset(intersection(a, b), b)), "Unpack membership in an intersection and retain the B-membership component.", "example {α : Type} (A B : Set α) : A ∩ B ⊆ B := Set.inter_subset_right", ("setup: Fix A, B and an element in A ∩ B.", "derive: Unpack intersection membership.", "conclude: Keep the B-membership proof.")),
        make_card("set_union_subset_iff", domain, "For all sets A, B, C: A ∪ B ⊆ C iff A ⊆ C and B ⊆ C.", forall(("A", "B", "C"), equivalent(subset(union(a, b), c), conjunction(subset(a, c), subset(b, c)))), "Reduce subset statements to arbitrary memberships; then split and combine the union cases.", "example {α : Type} (A B C : Set α) : A ∪ B ⊆ C ↔ A ⊆ C ∧ B ⊆ C := by simp", ("setup: Expand both subset statements elementwise.", "derive: Split union membership into the A and B cases.", "conclude: Reassemble the two subset proofs.")),
    ]


def all_cards() -> list[Card]:
    cards = algebra_cards() + order_cards() + number_cards() + set_cards()
    if len(cards) != 60 or len({card.id for card in cards}) != 60:
        raise RuntimeError("batch must contain exactly 60 unique cards")
    return cards


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = {
        "schema_version": "pals.local-draft-diversification-batch.v1",
        "source": "PALS first-party authored batch",
        "cards": [asdict(card) for card in all_cards()],
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
