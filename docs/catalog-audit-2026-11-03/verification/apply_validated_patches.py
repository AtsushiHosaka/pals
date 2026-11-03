#!/usr/bin/env python3
"""Apply validated_patches.json to a textbook-catalog-v1 checkout.

Usage: python apply_validated_patches.py <textbook-catalog-v1 dir> [--write]
Without --write it only reports which cards would change. The vocabulary additions in
vocab_extra.yaml must be copied into vocabulary/ by hand (they are new pals2 symbols).
Run `catalog.py check <domain>` afterwards; patches were validated against snapshot
cards/ SHA-256 a928e2cd216d501ca237c8605e5f6c3ac4a3c345407db14b700a53636021221c.
"""
import json
import sys
from pathlib import Path

import yaml

root = Path(sys.argv[1])
write = "--write" in sys.argv
patches = json.loads((Path(__file__).parent / "validated_patches.json").read_text())
sys.path.insert(0, str(root))
import catalog  # noqa: E402  (for the project's YAML dumper)

by_domain: dict[str, dict] = {}
for key, fields in patches.items():
    domain, card_id = key.split(".", 1)
    by_domain.setdefault(domain, {})[card_id] = fields
missing = []
for domain, items in by_domain.items():
    path = root / "cards" / f"{domain}.yaml"
    cards = yaml.safe_load(path.read_text())
    index = {card["id"]: card for card in cards}
    for card_id, fields in items.items():
        if card_id not in index:
            missing.append(f"{domain}.{card_id}")
            continue
        index[card_id].update(fields)
    print(f"{domain}: {len(items)} cards")
    if write:
        path.write_text(
            yaml.dump(cards, Dumper=catalog._LiteralDumper, allow_unicode=True,
                      sort_keys=False, width=100000)
        )
if missing:
    print("cards not found (the checkout moved on since the snapshot):", missing)
    sys.exit(1)
