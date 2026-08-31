#!/usr/bin/env python3
"""Generate six missing model/construct Drafts for the second school algebra slice."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
AGENT_ROOT = ROOT / "pals-agent"
ANCHOR_GENERATOR = ROOT / "pals-scripts/generate-school-algebra-anchor-v1-candidates.py"
OUTPUT = ROOT / "docs/school-algebra-precursor-v1-candidates.json"
SCHEMA_VERSION = "pals.school-algebra-precursor-v1-candidates.v1"
CARD_KEYS = frozenset(
    {"id", "canonical_statement", "openmath_xml", "proof_strategy", "sketch_steps"}
)


def _load_openmath_helpers() -> Any:
    spec = importlib.util.spec_from_file_location(
        "school_algebra_anchor_generator", ANCHOR_GENERATOR
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load the school algebra OpenMath helpers")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_cards() -> list[dict[str, Any]]:
    om = _load_openmath_helpers()
    x, area, length, width, diagonal = (
        om.omv(name) for name in ("x", "A", "l", "w", "d")
    )
    neq_width_zero = om.oma("relation1", "neq", width, om.omi(0))
    return [
        om.card(
            "school_alg_g7_signed_model",
            "Starting at -3 degrees and falling 5 degrees gives -8 degrees.",
            om.eq(om.sub(om.neg(om.omi(3)), om.omi(5)), om.neg(om.omi(8))),
            "Represent the starting temperature and the decrease as signed numbers, then subtract.",
            (
                "model: Represent three degrees below zero by -3.",
                "change: Subtract 5 for the temperature fall.",
                "conclude: -3-5=-8 degrees.",
            ),
        ),
        om.card(
            "school_alg_g7_symbolic_model",
            "For nonnegative real x, the rectangle with side lengths x and 3 has perimeter 2x+6.",
            om.forall(
                ("x",),
                om.implies(
                    om.leq(om.omi(0), x),
                    om.eq(
                        om.mul(om.omi(2), om.add(x, om.omi(3))),
                        om.add(om.mul(om.omi(2), x), om.omi(6)),
                    ),
                ),
            ),
            "Translate perimeter as twice the sum of adjacent sides and distribute the factor two.",
            (
                "model: Write the perimeter as 2(x+3).",
                "expand: Apply the distributive law.",
                "conclude: The perimeter is 2x+6.",
            ),
        ),
        om.card(
            "school_alg_g8_expression_model",
            "For real A, l, and nonzero w, if A=lw then l=A/w.",
            om.forall(
                ("A", "l", "w"),
                om.implies(
                    om.conjunction(om.eq(area, om.mul(length, width)), neq_width_zero),
                    om.eq(length, om.div(area, width)),
                ),
            ),
            "Treat A=lw as an area formula and divide by the nonzero width to isolate the length.",
            (
                "premise: Use A=lw and record w≠0.",
                "transform: Divide both sides by w.",
                "conclude: l=A/w.",
            ),
        ),
        om.card(
            "school_alg_g9_square_root_compute",
            "For every nonnegative real x, if x squared is 144 then x is 12.",
            om.forall(
                ("x",),
                om.implies(
                    om.conjunction(
                        om.leq(om.omi(0), x), om.eq(om.power(x, 2), om.omi(144))
                    ),
                    om.eq(x, om.omi(12)),
                ),
            ),
            "Use the nonnegative square-root convention and verify that 12 squared is 144.",
            (
                "factor: Rewrite x²-144 as (x-12)(x+12).",
                "solve: The algebraic roots are 12 and -12.",
                "filter: Nonnegativity leaves x=12.",
            ),
        ),
        om.card(
            "school_alg_g9_square_root_model",
            "The nonnegative diagonal d whose square equals 3 squared plus 4 squared has length 5.",
            om.forall(
                ("d",),
                om.implies(
                    om.conjunction(
                        om.leq(om.omi(0), diagonal),
                        om.eq(
                            om.power(diagonal, 2),
                            om.add(om.power(om.omi(3), 2), om.power(om.omi(4), 2)),
                        ),
                    ),
                    om.eq(diagonal, om.omi(5)),
                ),
            ),
            "Model a right-triangle diagonal with the Pythagorean relation and take the nonnegative root.",
            (
                "model: Write d²=3²+4² with d≥0.",
                "compute: Simplify the right side to 25.",
                "interpret: The nonnegative solution is d=5.",
            ),
        ),
        om.card(
            "school_alg_g9_polynomial_model",
            "For nonnegative real x, the rectangle with sides x+2 and x+3 has area x squared plus 5x plus 6.",
            om.forall(
                ("x",),
                om.implies(
                    om.leq(om.omi(0), x),
                    om.eq(
                        om.mul(om.add(x, om.omi(2)), om.add(x, om.omi(3))),
                        om.add(om.power(x, 2), om.mul(om.omi(5), x), om.omi(6)),
                    ),
                ),
            ),
            "Translate rectangle area as a product of side expressions and expand the product.",
            (
                "model: Write the area as (x+2)(x+3).",
                "expand: Multiply each term and combine the two linear terms.",
                "conclude: The area is x²+5x+6.",
            ),
        ),
    ]


def build_manifest() -> dict[str, Any]:
    cards = build_cards()
    hard_negative_cases = [
        (
            "A temperature of -3 degrees that falls by 5 degrees becomes 2 degrees.",
            "Subtracts magnitudes without preserving the signed direction.",
        ),
        (
            "A rectangle with sides x and 3 has perimeter 2x+3.",
            "Distributes the perimeter factor to only one side length.",
        ),
        (
            "From A=lw conclude l=A-w.",
            "Uses subtraction instead of division when rearranging the formula.",
        ),
        (
            "If x²=144 then the only real solution is x=12.",
            "Drops the negative root without the nonnegative premise.",
        ),
        (
            "A right triangle with legs 3 and 4 has diagonal 7.",
            "Adds the leg lengths instead of applying the Pythagorean relation.",
        ),
        ("(x+2)(x+3)=x²+6.", "Omits both cross terms in the polynomial expansion."),
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "source": {
            "kind": "independent_original_authoring",
            "coverage_matrix": "specs/draft-catalog-expansion/coverage-matrix.v1.json",
            "followup_to": "DCE-T008",
        },
        "cards": cards,
        "hard_negatives": [
            {"target_draft_id": card["id"], "query": case[0], "reason": case[1]}
            for card, case in zip(cards, hard_negative_cases, strict=True)
        ],
    }


def validate_manifest(payload: dict[str, Any]) -> None:
    cards = payload.get("cards")
    hard_negatives = payload.get("hard_negatives")
    if set(payload) != {"schema_version", "source", "cards", "hard_negatives"}:
        raise ValueError("school precursor manifest has invalid root fields")
    if payload["schema_version"] != SCHEMA_VERSION:
        raise ValueError("school precursor manifest schema version mismatch")
    if not isinstance(cards, list) or len(cards) != 6:
        raise ValueError("school precursor manifest must contain six cards")
    if not isinstance(hard_negatives, list) or len(hard_negatives) != 6:
        raise ValueError("school precursor manifest must contain six hard negatives")
    if any(set(card) != CARD_KEYS for card in cards):
        raise ValueError(
            "school precursor cards must contain only Draft authoring fields"
        )
    if len({card["id"] for card in cards}) != 6:
        raise ValueError("school precursor card IDs must be unique")
    if {item["target_draft_id"] for item in hard_negatives} != {
        card["id"] for card in cards
    }:
        raise ValueError("school precursor hard negatives must cover every card")

    sys.path.insert(0, str(AGENT_ROOT))
    from pals_agent.openmath import (
        canonicalize_retrieval_openmath_xml,
        validate_openmath_statement_semantics,
    )

    canonical_xml: list[str] = []
    for card in cards:
        validate_openmath_statement_semantics(
            card["openmath_xml"], card["canonical_statement"]
        )
        canonical_xml.append(canonicalize_retrieval_openmath_xml(card["openmath_xml"]))
        if not card["proof_strategy"].strip() or len(card["sketch_steps"]) < 3:
            raise ValueError(f"{card['id']} has incomplete strategy or Sketch")
    if len(set(canonical_xml)) != len(canonical_xml):
        raise ValueError("school precursor candidates contain OpenMath collisions")


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
            raise SystemExit("school precursor manifest is stale; rerun the generator")
        print("school precursor manifest is current and profile-valid")
        return 0
    args.output.write_text(rendered, encoding="utf-8")
    print(f"wrote {len(payload['cards'])} school precursor candidates to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
