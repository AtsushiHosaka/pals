#!/usr/bin/env python3
"""Apply audit patches to a COPY of the cards and validate them with the real catalog contract.

Stage 1 (contract): validate_card on every patched card with the full vocabulary, text lint,
canonical OpenMath collision check over the whole patched catalog.
Stage 2 (--compile): compile every card whose target/proof changed, axiom-audited.
"""

from __future__ import annotations

import argparse
import collections
import copy
import json
import re
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import catalog  # noqa: E402

FINDINGS = json.load(open(HERE.parent / "out" / "ALL_FINDINGS.json"))
CARD_FIELDS = {
    "statement", "statement_en", "assumptions", "quantifiers", "conclusion", "answer",
    "openmath", "hard_negative", "target", "proof", "level", "topic", "kind", "id",
}  # fmt: skip
SKIP = {"answer_note", "vocabulary_additions", "_vocabulary_to_add"}


def parse_vocab_additions(text: str) -> dict[str, dict]:
    added = {}
    for part in re.split(r";\s*(?=[a-z_]+:\s*\{)", text):
        added.update(yaml.safe_load(part))
    return added


def load_cards() -> dict[str, list[dict]]:
    out = {}
    for path in sorted(catalog.CARDS.glob("*.yaml")):
        if not path.stem.startswith("_"):
            out[path.stem] = yaml.safe_load(path.read_text())
    return out


OVERRIDES = json.load(open(HERE / "overrides.json")) if (HERE / "overrides.json").exists() else {}


def apply(cards: dict[str, list[dict]]):
    vocab_add: dict[str, dict] = {}
    applied, manual = {}, []
    for finding in FINDINGS:
        patch = finding.get("patch")
        if not patch:
            continue
        domain, cid = finding["domain"], finding["id"]
        card = next(c for c in cards[domain] if c["id"] == cid)
        for key, value in patch.items():
            if key in ("vocabulary_additions", "_vocabulary_to_add"):
                vocab_add.update(parse_vocab_additions(value))
            elif key in SKIP:
                manual.append((domain, cid, key, value))
            elif key in CARD_FIELDS:
                if key == "level" and str(value).isdigit():
                    value = int(value)
                if key == "openmath":
                    for old, new in OVERRIDES.get(f"{domain}.{cid}", []):
                        if old == "__replace__":
                            value = new
                            continue
                        assert old in value, (domain, cid, old)
                        value = value.replace(old, new)
                card[key] = value
            else:
                manual.append((domain, cid, key, value))
        applied[(domain, cid)] = {k: v for k, v in patch.items() if k in CARD_FIELDS}
    return applied, vocab_add, manual


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--compile", action="store_true")
    parser.add_argument("--out", default=str(HERE / "result.json"))
    parser.add_argument("--batch", type=int, default=12)
    args = parser.parse_args()

    cards = load_cards()
    patched_cards = copy.deepcopy(cards)
    applied, vocab_add, manual = apply(patched_cards)
    vocabulary = catalog.load_vocabulary()
    extra = HERE / "vocab_extra.yaml"
    if extra.exists():
        vocab_add.update(yaml.safe_load(extra.read_text()))
    for name, spec in vocab_add.items():
        if name in vocabulary and vocabulary[name] != spec:
            print("vocabulary addition conflicts with existing symbol:", name)
        vocabulary.setdefault(name, spec)

    result: dict = {"manual_items": manual, "vocab_added": sorted(vocab_add), "cards": {}}
    entries_by_label: dict[str, dict] = {}
    xml_owner: dict[str, list[str]] = collections.defaultdict(list)
    for domain, items in patched_cards.items():
        for card in items:
            label = f"textbook.{domain}.{card['id']}"
            try:
                entry = catalog.validate_card(card, domain, vocabulary)
                entries_by_label[label] = entry
                xml_owner[entry["xml"]].append(label)
            except Exception as error:  # noqa: BLE001
                if (domain, card["id"]) in applied or label.endswith("." + card["id"]):
                    result["cards"][label] = {"stage": "contract", "error": str(error)[:700]}
    patched_labels = {f"textbook.{d}.{patched_id(d, i, applied, patched_cards)}" for d, i in applied}
    for label in patched_labels:
        info = result["cards"].setdefault(label, {"stage": "contract", "error": None})
        card = None
        domain = label.split(".")[1]
        cid = label.split(".", 2)[2]
        card = next(c for c in patched_cards[domain] if c["id"] == cid)
        problems = []
        for key in sorted(catalog.TEXT_FIELDS):
            vals = card[key] if isinstance(card[key], list) else [card[key]]
            for value in vals:
                problems += [f"{key}: {p}" for p in catalog._text_problems(value)]
        if "概略" in card["answer"]:
            problems.append("answer: 概略")
        info["text_lint"] = problems
    collisions = [owners for owners in xml_owner.values() if len(owners) > 1]
    result["xml_collisions"] = collisions

    if args.compile:
        todo = []
        for (domain, cid), fields in applied.items():
            if "target" in fields or "proof" in fields:
                new_id = fields.get("id", cid)
                label = f"textbook.{domain}.{new_id}"
                if label in entries_by_label:
                    todo.append(entries_by_label[label])
        result["compile_total"] = len(todo)
        fails: dict[str, list[str]] = {}
        for start in range(0, len(todo), args.batch):
            chunk = todo[start : start + args.batch]
            print(f"compiling {start}-{start + len(chunk)} of {len(todo)}", flush=True)
            fails.update(catalog.compile_batch(chunk))
        for entry in todo:
            label = entry["recipe_id"]
            result["cards"].setdefault(label, {"stage": "compile", "error": None})["compile"] = (
                fails.get(label) or "ok"
            )
        if "<batch>" in fails:
            result["compile_batch_error"] = fails["<batch>"]

    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=1))
    contract_fail = [k for k, v in result["cards"].items() if v.get("error")]
    lint_fail = [k for k, v in result["cards"].items() if v.get("text_lint")]
    compile_fail = [k for k, v in result["cards"].items() if v.get("compile") not in (None, "ok")]
    print(
        json.dumps(
            {
                "patched_cards": len(applied),
                "contract_failed": len(contract_fail),
                "text_lint_flagged": len(lint_fail),
                "compile_failed": len(compile_fail),
                "xml_collisions": len(collisions),
                "vocab_added": len(vocab_add),
                "manual_items": len(manual),
            },
            ensure_ascii=False,
        )
    )
    diff = {}
    for domain, items in patched_cards.items():
        originals = {c["id"]: c for c in cards[domain]}
        for card in items:
            changed = {}
            for old_id, original in originals.items():
                pass
            base = originals.get(card["id"])
            if base is None:  # renamed card: find by position
                base = cards[domain][items.index(card)]
                changed["id"] = card["id"]
            for key, value in card.items():
                if base.get(key) != value:
                    changed[key] = value
            if changed:
                diff[f"{domain}.{base['id']}"] = changed
    (HERE / "validated_patches.json").write_text(json.dumps(diff, ensure_ascii=False, indent=1))
    # persist patched cards for later review
    outdir = HERE / "cards_patched"
    outdir.mkdir(exist_ok=True)
    for domain, items in patched_cards.items():
        (outdir / f"{domain}.yaml").write_text(
            yaml.dump(items, Dumper=catalog._LiteralDumper, allow_unicode=True, sort_keys=False, width=100000)
        )
    return 0


def patched_id(domain: str, cid: str, applied, patched_cards) -> str:
    return applied[(domain, cid)].get("id", cid)


if __name__ == "__main__":
    raise SystemExit(main())
