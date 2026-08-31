#!/usr/bin/env python3
"""Combine independently validated high-school and university Draft manifests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    ROOT / "docs/highschool-sequences-limits-calculus-candidates.json",
    ROOT / "docs/local-university-math-draft-candidates.json",
)
EXCLUDED_DUPLICATE_IDS = frozenset({"univ_analysis_inverse_successor_sequence"})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def cards_from_payload(payload: object) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("cards"), list):
        raise ValueError("source manifest must contain a cards list")
    cards = payload["cards"]
    if not all(isinstance(card, dict) for card in cards):
        raise ValueError("source manifest has a non-object card")
    return cards


def main() -> None:
    args = parse_args()
    cards = [
        card
        for source in SOURCES
        for card in cards_from_payload(json.loads(source.read_text(encoding="utf-8")))
        if card.get("id") not in EXCLUDED_DUPLICATE_IDS
    ]
    ids = [card.get("id") for card in cards]
    if len(cards) != 56 or len(set(ids)) != len(ids):
        raise ValueError("advanced batch must contain 56 cards with unique IDs")
    args.output.write_text(
        json.dumps(
            {
                "schema_version": "pals.local-advanced-math-batch.v1",
                "source": "PALS first-party authored high-school and university batch",
                "cards": cards,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
