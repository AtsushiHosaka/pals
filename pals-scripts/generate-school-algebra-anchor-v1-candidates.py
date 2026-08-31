#!/usr/bin/env python3
"""Generate the first 18 original school-algebra Draft authoring candidates."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
AGENT_ROOT = ROOT / "pals-agent"
SCHEMA_VERSION = "pals.school-algebra-anchor-v1-candidates.v1"
OUTPUT = ROOT / "docs/school-algebra-anchor-v1-candidates.json"
CARD_KEYS = frozenset(
    {"id", "canonical_statement", "openmath_xml", "proof_strategy", "sketch_steps"}
)


def oms(cd: str, name: str) -> str:
    return f'<OMS cd="{cd}" name="{name}"/>'


def omv(name: str) -> str:
    return f'<OMV name="{name}"/>'


def omi(value: int) -> str:
    return f"<OMI>{value}</OMI>"


def oma(cd: str, name: str, *arguments: str) -> str:
    return f"<OMA>{oms(cd, name)}{''.join(arguments)}</OMA>"


def forall(variables: Sequence[str], proposition: str) -> str:
    bound = "".join(omv(variable) for variable in variables)
    return f"<OMBIND>{oms('quant1', 'forall')}<OMBVAR>{bound}</OMBVAR>{proposition}</OMBIND>"


def openmath(expression: str) -> str:
    return f'<OMOBJ xmlns="http://www.openmath.org/OpenMath" version="2.0">{expression}</OMOBJ>'


def add(*values: str) -> str:
    return oma("arith1", "plus", *values)


def sub(left: str, right: str) -> str:
    return oma("arith1", "minus", left, right)


def mul(*values: str) -> str:
    return oma("arith1", "times", *values)


def div(left: str, right: str) -> str:
    return oma("arith1", "divide", left, right)


def power(base: str, exponent: int) -> str:
    return oma("arith1", "power", base, omi(exponent))


def neg(value: str) -> str:
    return oma("arith1", "unary_minus", value)


def eq(left: str, right: str) -> str:
    return oma("relation1", "eq", left, right)


def leq(left: str, right: str) -> str:
    return oma("relation1", "leq", left, right)


def lt(left: str, right: str) -> str:
    return oma("relation1", "lt", left, right)


def conjunction(*values: str) -> str:
    return oma("logic1", "and", *values)


def disjunction(*values: str) -> str:
    return oma("logic1", "or", *values)


def implies(premise: str, conclusion: str) -> str:
    return oma("logic1", "implies", premise, conclusion)


def equivalent(left: str, right: str) -> str:
    return oma("logic1", "equivalent", left, right)


def card(
    identifier: str,
    statement: str,
    expression: str,
    strategy: str,
    steps: Sequence[str],
) -> dict[str, Any]:
    return {
        "id": identifier,
        "canonical_statement": statement,
        "openmath_xml": openmath(expression),
        "proof_strategy": strategy,
        "sketch_steps": list(steps),
    }


def build_cards() -> list[dict[str, Any]]:
    x, y, a, b, d, p, n = (omv(name) for name in ("x", "y", "a", "b", "d", "p", "n"))
    return [
        card(
            "school_alg_e4_quantity_compute",
            "Six equal boxes containing eight pencils each contain forty-eight pencils in total.",
            eq(mul(omi(6), omi(8)), omi(48)),
            "Represent equal groups by multiplication and evaluate the product.",
            (
                "model: Treat the six boxes as six equal groups of eight.",
                "compute: Multiply 6 by 8.",
                "conclude: The total is 48 pencils.",
            ),
        ),
        card(
            "school_alg_e4_quantity_justify",
            "For all real a and b, four groups of a plus four groups of b equal four groups of a+b.",
            forall(
                ("a", "b"),
                eq(add(mul(omi(4), a), mul(omi(4), b)), mul(omi(4), add(a, b))),
            ),
            "Use the distributive law to justify combining two same-sized collections of groups.",
            (
                "setup: Regard a and b as the amounts in two parts of each group.",
                "apply_rule: Factor the common multiplier 4.",
                "conclude: 4a+4b=4(a+b).",
            ),
        ),
        card(
            "school_alg_e4_quantity_model",
            "If four equally priced notebooks cost 600 yen in total, then one notebook costs 150 yen.",
            forall(("p",), implies(eq(mul(omi(4), p), omi(600)), eq(p, omi(150)))),
            "Translate total cost as item count times unit price, then divide by four.",
            (
                "model: Let p be the price of one notebook and write 4p=600.",
                "solve: Divide both sides by 4.",
                "interpret: One notebook costs 150 yen.",
            ),
        ),
        card(
            "school_alg_e6_symbolic_compute",
            "Three fourths divided by two fifths equals fifteen eighths.",
            eq(div(div(omi(3), omi(4)), div(omi(2), omi(5))), div(omi(15), omi(8))),
            "Multiply by the reciprocal and reduce the resulting fraction.",
            (
                "rewrite: Replace division by 2/5 with multiplication by 5/2.",
                "compute: Multiply numerators and denominators.",
                "conclude: The value is 15/8.",
            ),
        ),
        card(
            "school_alg_e6_symbolic_justify",
            "For every real x, three fifths of x equals three times x divided by five.",
            forall(
                ("x",), eq(mul(div(omi(3), omi(5)), x), div(mul(omi(3), x), omi(5)))
            ),
            "Regroup multiplication and division to justify the equivalent symbolic forms.",
            (
                "rewrite: Express 3/5 as 3 divided by 5.",
                "reassociate: Move x into the numerator product.",
                "conclude: (3/5)x=(3x)/5.",
            ),
        ),
        card(
            "school_alg_e6_symbolic_model",
            "If three fourths of a real number x is 18, then x is 24.",
            forall(
                ("x",),
                implies(eq(mul(div(omi(3), omi(4)), x), omi(18)), eq(x, omi(24))),
            ),
            "Represent the stated fraction of the unknown, then multiply by the reciprocal.",
            (
                "model: Translate three fourths of x as (3/4)x.",
                "solve: Multiply both sides of (3/4)x=18 by 4/3.",
                "conclude: x=24.",
            ),
        ),
        card(
            "school_alg_g7_linear_compute",
            "For every real x, if 3x+5=20, then x=5.",
            forall(
                ("x",), implies(eq(add(mul(omi(3), x), omi(5)), omi(20)), eq(x, omi(5)))
            ),
            "Subtract five and divide by the nonzero coefficient three.",
            (
                "subtract: Obtain 3x=15.",
                "divide: Divide both sides by 3.",
                "conclude: x=5.",
            ),
        ),
        card(
            "school_alg_g7_linear_justify",
            "For every real x, 2x-6=10 if and only if x=8.",
            forall(
                ("x",),
                equivalent(eq(sub(mul(omi(2), x), omi(6)), omi(10)), eq(x, omi(8))),
            ),
            "Use reversible addition and division steps in both directions.",
            (
                "forward: Add 6 and divide by 2 to obtain x=8.",
                "reverse: Substitute x=8 into 2x-6.",
                "conclude: The equation and solution are equivalent.",
            ),
        ),
        card(
            "school_alg_g7_linear_model",
            "The fare with base charge 120 yen and rate 80 yen per kilometre totals 440 yen only when distance d is 4 kilometres.",
            forall(
                ("d",),
                implies(eq(add(omi(120), mul(omi(80), d)), omi(440)), eq(d, omi(4))),
            ),
            "Translate base charge plus rate times distance into a linear equation and solve it.",
            (
                "model: Write 120+80d=440.",
                "solve: Subtract 120 and divide by 80.",
                "interpret: The distance d is 4 kilometres.",
            ),
        ),
        card(
            "school_alg_g8_system_compute",
            "For all real x and y, if x+y=7 and x-y=1, then x=4 and y=3.",
            forall(
                ("x", "y"),
                implies(
                    conjunction(eq(add(x, y), omi(7)), eq(sub(x, y), omi(1))),
                    conjunction(eq(x, omi(4)), eq(y, omi(3))),
                ),
            ),
            "Add the equations to eliminate y, then substitute the resulting x-value.",
            (
                "eliminate: Add the two equations to obtain 2x=8.",
                "substitute: Use x=4 in x+y=7.",
                "conclude: x=4 and y=3.",
            ),
        ),
        card(
            "school_alg_g8_system_justify",
            "For all real x, y, a, and b, if x+y=a and x-y=b, then 2x=a+b.",
            forall(
                ("x", "y", "a", "b"),
                implies(
                    conjunction(eq(add(x, y), a), eq(sub(x, y), b)),
                    eq(mul(omi(2), x), add(a, b)),
                ),
            ),
            "Add the two equalities and justify cancellation of the opposite y-terms.",
            (
                "add: Add corresponding sides of both equations.",
                "cancel: Simplify y-y to zero.",
                "conclude: The remaining equality is 2x=a+b.",
            ),
        ),
        card(
            "school_alg_g8_system_model",
            "If 10 tickets consist of 500-yen adult tickets and 300-yen child tickets and cost 3800 yen, then there are 4 adult and 6 child tickets.",
            forall(
                ("a", "b"),
                implies(
                    conjunction(
                        eq(add(a, b), omi(10)),
                        eq(add(mul(omi(500), a), mul(omi(300), b)), omi(3800)),
                    ),
                    conjunction(eq(a, omi(4)), eq(b, omi(6))),
                ),
            ),
            "Model ticket count and total cost as a simultaneous linear system and eliminate one variable.",
            (
                "model: Write a+b=10 and 500a+300b=3800.",
                "eliminate: Subtract 300 times the count equation from the cost equation.",
                "interpret: a=4 adult tickets and b=6 child tickets.",
            ),
        ),
        card(
            "school_alg_g9_quadratic_compute",
            "For every real x, if x^2-5x+6=0, then x=2 or x=3.",
            forall(
                ("x",),
                implies(
                    eq(add(sub(power(x, 2), mul(omi(5), x)), omi(6)), omi(0)),
                    disjunction(eq(x, omi(2)), eq(x, omi(3))),
                ),
            ),
            "Factor the quadratic as (x-2)(x-3) and apply the zero-product property.",
            (
                "factor: Rewrite x^2-5x+6 as (x-2)(x-3).",
                "split: A zero product has at least one zero factor.",
                "conclude: x=2 or x=3.",
            ),
        ),
        card(
            "school_alg_g9_quadratic_justify",
            "For every real x, x^2=9 if and only if x=3 or x=-3.",
            forall(
                ("x",),
                equivalent(
                    eq(power(x, 2), omi(9)),
                    disjunction(eq(x, omi(3)), eq(x, neg(omi(3)))),
                ),
            ),
            "Use the difference-of-squares factorization and verify both roots for the reverse direction.",
            (
                "factor: Rewrite x^2-9 as (x-3)(x+3).",
                "forward: Apply the zero-product property.",
                "reverse: Square 3 and -3 to recover 9.",
            ),
        ),
        card(
            "school_alg_g9_quadratic_model",
            "If positive rectangle width x and length x+2 have area 48, then the width is 6.",
            forall(
                ("x",),
                implies(
                    conjunction(lt(omi(0), x), eq(mul(x, add(x, omi(2))), omi(48))),
                    eq(x, omi(6)),
                ),
            ),
            "Translate the area condition into a quadratic, solve both algebraic roots, and keep the positive length.",
            (
                "model: Write x(x+2)=48 with x>0.",
                "solve: Factor x^2+2x-48 as (x-6)(x+8).",
                "filter: Reject x=-8 because a width is positive; conclude x=6.",
            ),
        ),
        card(
            "school_alg_h1_inequality_compute",
            "For every real x, 3x-7≤5 if and only if x≤4.",
            forall(
                ("x",),
                equivalent(leq(sub(mul(omi(3), x), omi(7)), omi(5)), leq(x, omi(4))),
            ),
            "Add seven and divide by the positive coefficient three, preserving the inequality direction.",
            (
                "add: Obtain 3x≤12.",
                "divide: Divide by positive 3 without reversing the inequality.",
                "conclude: x≤4, with reversible steps.",
            ),
        ),
        card(
            "school_alg_h1_inequality_justify",
            "For all real x and y, x≤y if and only if -y≤-x.",
            forall(("x", "y"), equivalent(leq(x, y), leq(neg(y), neg(x)))),
            "Multiply both sides by -1 and justify reversal of the order relation in both directions.",
            (
                "forward: Multiply x≤y by -1 and reverse the inequality.",
                "reverse: Apply the same operation to -y≤-x.",
                "conclude: The two inequalities are equivalent.",
            ),
        ),
        card(
            "school_alg_h1_inequality_model",
            "If real ride count n is nonnegative and the 1200-yen pass plus 350 yen per ride costs at most 4000 yen, then n≤8.",
            forall(
                ("n",),
                implies(
                    conjunction(
                        leq(omi(0), n), leq(add(omi(1200), mul(omi(350), n)), omi(4000))
                    ),
                    leq(n, omi(8)),
                ),
            ),
            "Translate the budget cap into a linear inequality, isolate the ride count, and interpret the bound.",
            (
                "model: Write 1200+350n≤4000 with n≥0.",
                "solve: Subtract 1200 and divide by positive 350 to obtain n≤8.",
                "interpret: The budget permits at most eight rides.",
            ),
        ),
    ]


def build_manifest() -> dict[str, Any]:
    cards = build_cards()
    hard_negative_cases = [
        (
            "Six equal boxes containing eight pencils each contain fourteen pencils in total.",
            "Confuses multiplication of equal groups with addition of the two visible numbers.",
        ),
        (
            "For all real a and b, 4a+4b=8(a+b).",
            "Incorrectly adds the common coefficient while factoring it.",
        ),
        (
            "If four equally priced notebooks cost 600 yen, one notebook costs 2400 yen.",
            "Multiplies the total by the item count instead of dividing it.",
        ),
        (
            "Three fourths divided by two fifths equals six twentieths.",
            "Multiplies the fractions without taking the reciprocal of the divisor.",
        ),
        (
            "For every real x, (3/5)x=(3+x)/5.",
            "Replaces multiplication in the numerator with addition.",
        ),
        (
            "If three fourths of x is 18, then x is 27/2.",
            "Multiplies 18 by 3/4 instead of by the reciprocal 4/3.",
        ),
        (
            "For every real x, if 3x+5=20, then x=25/3.",
            "Adds five instead of subtracting five before division.",
        ),
        (
            "For every real x, 2x-6=10 if and only if x=2.",
            "Moves the constant with the wrong sign before dividing.",
        ),
        (
            "A fare with base charge 120 yen and rate 80 yen per kilometre is modeled by 120d+80=440.",
            "Swaps the fixed base charge and the per-kilometre coefficient.",
        ),
        (
            "The system x+y=7 and x-y=1 has solution x=3, y=4.",
            "The proposed pair satisfies the sum but violates the difference equation.",
        ),
        (
            "From x+y=a and x-y=b, conclude 2x=a-b.",
            "Uses subtraction on the right after adding the two equations.",
        ),
        (
            "Ten 500-yen adult and 300-yen child tickets costing 3800 yen consist of 6 adults and 4 children.",
            "Swaps the counts; the resulting total is 4200 yen.",
        ),
        (
            "If x^2-5x+6=0, then x=-2 or x=-3.",
            "Reads the signs of the roots directly from the factors.",
        ),
        (
            "For every real x, x^2=9 if and only if x=3.",
            "Drops the negative square root and therefore fails the characterization.",
        ),
        (
            "A positive rectangle width x with x(x+2)=48 may have width -8.",
            "Keeps an algebraic root that violates the positive-width premise.",
        ),
        (
            "For every real x, 3x-7≤5 if and only if x≤-2/3.",
            "Moves -7 in the wrong direction before dividing.",
        ),
        (
            "For all real x and y, x≤y if and only if -x≤-y.",
            "Negates both sides without reversing the order relation.",
        ),
        (
            "Under 1200+350n≤4000 with n≥0, the budget permits strictly fewer than eight rides.",
            "Changes the inclusive bound and incorrectly excludes the feasible endpoint n=8.",
        ),
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "source": {
            "kind": "independent_original_authoring",
            "coverage_matrix": "specs/draft-catalog-expansion/coverage-matrix.v1.json",
            "task": "DCE-T008",
        },
        "cards": cards,
        "hard_negatives": [
            {
                "target_draft_id": card["id"],
                "query": case[0],
                "reason": case[1],
            }
            for card, case in zip(cards, hard_negative_cases, strict=True)
        ],
    }


def validate_manifest(payload: dict[str, Any]) -> None:
    if set(payload) != {"schema_version", "source", "cards", "hard_negatives"}:
        raise ValueError("school algebra manifest has unknown or missing root keys")
    if payload["schema_version"] != SCHEMA_VERSION:
        raise ValueError("school algebra manifest schema version mismatch")
    cards = payload["cards"]
    if len(cards) != 18 or len(payload["hard_negatives"]) != 18:
        raise ValueError(
            "school algebra manifest must contain 18 cards and 18 hard negatives"
        )
    if any(set(candidate) != CARD_KEYS for candidate in cards):
        raise ValueError(
            "school algebra cards must contain only the five authoring fields"
        )
    if len({candidate["id"] for candidate in cards}) != 18:
        raise ValueError("school algebra card IDs must be unique")
    hard_negatives = payload["hard_negatives"]
    if any(
        set(candidate) != {"target_draft_id", "query", "reason"}
        for candidate in hard_negatives
    ):
        raise ValueError("school algebra hard negatives have invalid fields")
    if {candidate["target_draft_id"] for candidate in hard_negatives} != {
        candidate["id"] for candidate in cards
    }:
        raise ValueError(
            "school algebra hard negatives must cover every card exactly once"
        )
    if any(
        "nearby but invalid variant" in candidate["query"].lower()
        or not candidate["query"].strip()
        or not candidate["reason"].strip()
        for candidate in hard_negatives
    ):
        raise ValueError("school algebra hard negatives must be concrete")

    sys.path.insert(0, str(AGENT_ROOT))
    from pals_agent.openmath import (
        canonicalize_retrieval_openmath_xml,
        validate_openmath_statement_semantics,
    )

    canonical_xml: list[str] = []
    for candidate in cards:
        validate_openmath_statement_semantics(
            candidate["openmath_xml"], candidate["canonical_statement"]
        )
        canonical_xml.append(
            canonicalize_retrieval_openmath_xml(candidate["openmath_xml"])
        )
        if (
            not candidate["proof_strategy"].strip()
            or len(candidate["sketch_steps"]) < 3
        ):
            raise ValueError(f"{candidate['id']} has incomplete strategy or Sketch")
    if len(set(canonical_xml)) != len(canonical_xml):
        raise ValueError(
            "school algebra candidates contain canonical OpenMath collisions"
        )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_manifest()
    validate_manifest(payload)
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.check:
        if (
            not args.output.is_file()
            or args.output.read_text(encoding="utf-8") != rendered
        ):
            raise SystemExit("school algebra manifest is stale; rerun the generator")
        print("school algebra manifest is current and profile-valid")
        return 0
    args.output.write_text(rendered, encoding="utf-8")
    print(f"wrote {len(payload['cards'])} school algebra candidates to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
