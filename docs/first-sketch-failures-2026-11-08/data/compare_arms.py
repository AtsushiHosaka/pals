"""Paired comparison of baseline vs repair+template arms on the 24 held-out cards (no text stored)."""

from __future__ import annotations

import json
import random
import statistics
import sys
from pathlib import Path

OUT = Path(sys.argv[1])
BASE = ["base-held", "base-new"]
TREAT = ["ho-held", "ho-new"]
CAP = int(sys.argv[2]) if len(sys.argv) > 2 else 3


def load(labels):
    rows = {}
    for label in labels:
        for line in (OUT / f"{label}.jsonl").read_text().splitlines():
            d = json.loads(line)
            if "state" in d:
                rows[d["problem"]] = d
    return rows


def cost(d):
    return d.get("input_tokens", 0) * 1.25e-6 + d.get("output_tokens", 0) * 5e-6


def mismatches(d):
    return sum("lean.formal_harness_mismatch" in codes for codes in d.get("diagnostic_codes", []))


def first_sketch(d):
    checks = d.get("sketch_checks") or []
    return bool(checks and checks[0]["success"])


def ok(d):
    return d["state"] == "verified"


def at_cap(d, cap):
    """Desk estimate of success and seconds with the repair cap lowered to `cap`.

    Attempts = repairs_used + 1. A card that needed more than `cap` repairs (or failed after using
    its repairs) is a failure at the lower cap; its seconds are scaled by attempts kept / attempts
    used, which assumes equal time per attempt (Draft and first Sketch are in fact a fixed cost).
    """
    used = d["repairs_used"]
    attempts = used + 1
    if used <= cap:
        return ok(d), d["elapsed_seconds"]
    return False, d["elapsed_seconds"] * (cap + 1) / attempts


def boot(diffs, rng, n=10000):
    k = len(diffs)
    means = sorted(sum(rng.choice(diffs) for _ in range(k)) / k for _ in range(n))
    return means[int(0.025 * n)], means[int(0.975 * n)]


def main():
    base, treat = load(BASE), load(TREAT)
    cards = sorted(set(base) & set(treat))
    print(f"cards paired: {len(cards)} (base {len(base)}, treat {len(treat)})")
    rng = random.Random(20261109)
    metrics = {
        "success": lambda d: float(ok(d)),
        "first_sketch_pass": lambda d: float(first_sketch(d)),
        "mismatch_attempts": lambda d: float(mismatches(d)),
        "model_calls": lambda d: float(d["model_calls"]),
        "seconds": lambda d: d["elapsed_seconds"],
        "cost_usd": cost,
    }
    print("\n| metric | base | treat | diff (treat-base) | 95% CI |")
    print("|---|---:|---:|---:|---|")
    for name, fn in metrics.items():
        b = [fn(base[c]) for c in cards]
        t = [fn(treat[c]) for c in cards]
        diffs = [y - x for x, y in zip(b, t)]
        lo, hi = boot(diffs, rng)
        verdict = "" if lo > 0 or hi < 0 else " (0をまたぐ)"
        print(
            f"| {name} | {sum(b) / len(b):.3f} | {sum(t) / len(t):.3f} | "
            f"{sum(diffs) / len(diffs):+.3f} | [{lo:+.3f}, {hi:+.3f}]{verdict} |"
        )
    for label, rows in (("base", base), ("treat", treat)):
        secs = [rows[c]["elapsed_seconds"] for c in cards]
        top2 = sorted(secs, reverse=True)[:2]
        print(
            f"\n{label}: success {sum(ok(rows[c]) for c in cards)}/{len(cards)}, "
            f"first-Sketch {sum(first_sketch(rows[c]) for c in cards)}, "
            f"mismatch attempts {sum(mismatches(rows[c]) for c in cards)}, "
            f"calls {sum(rows[c]['model_calls'] for c in cards)}, "
            f"mean {statistics.mean(secs):.1f}s median {statistics.median(secs):.1f}s "
            f"slowest {top2[0]:.0f}/{top2[1]:.0f}s, cost ${sum(cost(rows[c]) for c in cards):.3f}"
        )
    print(f"\nDesk estimate with repair cap {CAP} (from cap-6 records)")
    print("| arm | success | mean s | median s |")
    print("|---|---:|---:|---:|")
    for label, rows in (("base", base), ("treat", treat)):
        est = [at_cap(rows[c], CAP) for c in cards]
        secs = [s for _, s in est]
        print(
            f"| {label} | {sum(o for o, _ in est)}/{len(cards)} | "
            f"{statistics.mean(secs):.1f} | {statistics.median(secs):.1f} |"
        )
    print("\nper-card seconds (base, treat, base state, treat state)")
    for c in cards:
        print(
            f"{c}: {base[c]['elapsed_seconds']:.0f} {treat[c]['elapsed_seconds']:.0f} "
            f"{base[c]['state']} {treat[c]['state']} repairs {base[c]['repairs_used']}/"
            f"{treat[c]['repairs_used']}"
        )


main()
