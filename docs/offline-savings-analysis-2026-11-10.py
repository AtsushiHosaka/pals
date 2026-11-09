"""Desk analysis of time/cost savings from existing runs only (no model calls, cost 0).

Reads the committed rows under docs/first-sketch-failures-2026-11-08/data/ and
docs/scheme-theory-measurement-rows-*-2026-11-09.jsonl. Prints every number used in
docs/improvement-journal/entries/2026-11-10-offline-savings-analysis.md.

Usage: python3 -I docs/offline-savings-analysis-2026-11-10.py
Standard library only. Seeds are fixed. Intervals are 95% bootstrap over cards (10,000 resamples).
Time and cost of a run truncated by a lower repair cap or an early stop are ESTIMATES: the run's actual
value is scaled by fit(kept repairs) / fit(used repairs), where fit is a straight line in repairs fitted
on all Terra-medium rows (see q1_split). No per-attempt times are recorded, so this is the best available.
"""

from __future__ import annotations

import json
import math
import random
import statistics as st
from pathlib import Path

DOCS = Path(__file__).resolve().parent
DATA = DOCS / "first-sketch-failures-2026-11-08" / "data"
N_BOOT = 10000


def load(name):
    return [json.loads(line) for line in (DATA / f"{name}.jsonl").read_text().splitlines() if line.strip()]


def cost(r):  # Terra price per million tokens: input 1.25, output 5.00 (estimate)
    return r["input_tokens"] * 1.25e-6 + r["output_tokens"] * 5e-6


def ok(r):
    return r["state"] == "verified"


def mm(codes):
    return "lean.formal_harness_mismatch" in codes or "lean.statement_mismatch" in codes


def mm_only(codes):
    return bool(codes) and set(codes) <= {"lean.formal_harness_mismatch", "lean.statement_mismatch"}


def empty_first(r):
    return "pals.generation_empty" in r["diagnostic_codes"][0]


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - h) / d, (c + h) / d


def linfit(xs, ys):
    mx, my = st.mean(xs), st.mean(ys)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    a = my - b * mx
    ss_res = sum((y - a - b * x) ** 2 for x, y in zip(xs, ys))
    ss_tot = sum((y - my) ** 2 for y in ys)
    return a, b, 1 - ss_res / ss_tot


def boot_mean(vals, seed):
    rng = random.Random(seed)
    res = sorted(st.mean(rng.choice(vals) for _ in vals) for _ in range(N_BOOT))
    return st.mean(vals), res[int(0.025 * N_BOOT)], res[int(0.975 * N_BOOT)]


# Datasets: Terra medium, repair cap 6, each card once. Rows lost to API errors or the budget stop were
# replaced by the re-runs the original docs describe (docs/first-sketch-failures-2026-11-08/README.md).
def clean(rows):
    return [
        r
        for r in rows
        if not r["budget_stopped"] and r["model_calls"] > 0 and not any("openai.error" in c for c in r["diagnostic_codes"])
    ]


BASE_A = clean(load("pf-base-terra-med")) + clean(load("pf-base2-terra-med"))
BASE_B = load("base-held") + load("base-new")
REP = clean(load("full-repair-a")) + load("full-repair-b")
TPL_A = clean(load("tpl-9")) + load("tpl-1b") + load("tpl-3")
TPL_B = load("ho-held") + load("ho-new")
BASE, TPL = BASE_A + BASE_B, TPL_A + TPL_B
ALL = BASE + TPL + REP
for _name, _rows in (("BASE_A", BASE_A), ("BASE_B", BASE_B), ("REP", REP), ("TPL_A", TPL_A), ("TPL_B", TPL_B)):
    assert len({r["problem"] for r in _rows}) == len(_rows), _name
assert all(len(r["diagnostic_codes"]) == r["repairs_used"] + 1 for r in ALL)

TA, TB, TR2 = linfit([r["repairs_used"] for r in ALL], [r["elapsed_seconds"] for r in ALL])
CA, CB, CR2 = linfit([r["repairs_used"] for r in ALL], [cost(r) for r in ALL])


def t_fit(n_rep):
    return TA + TB * n_rep


def c_fit(n_rep):
    return CA + CB * n_rep


def outcome(r, cap=6, k=None, cum=None):
    """(success, seconds, usd) if the repair cap and an early-stop rule had been applied to this recorded run.

    k: stop after k consecutive attempts whose only error codes are statement/harness mismatch.
    cum: stop after cum attempts (not necessarily consecutive) that contain a mismatch.
    A stopped run is counted as a failure. Repairs after the stop are removed; earlier attempts are unchanged
    (no look-ahead: a repair prompt does not depend on the cap).
    """
    reps = r["repairs_used"]
    used, succ = reps, ok(r)
    run = cum_count = 0
    for i, codes in enumerate(r["diagnostic_codes"]):
        if i > cap:
            break
        run = run + 1 if (k and mm_only(codes)) else 0
        cum_count += 1 if (cum and mm(codes)) else 0
        if (k and run >= k) or (cum and cum_count >= cum):
            if i < reps:
                used, succ = i, False
            break
    if used > cap:
        used, succ = cap, False
    if used == reps:
        return succ, r["elapsed_seconds"], cost(r)
    return succ, r["elapsed_seconds"] * t_fit(used) / t_fit(reps), cost(r) * c_fit(used) / c_fit(reps)


def paired(rows, kw1, kw0, seed):
    o1 = [outcome(r, **kw1) for r in rows]
    o0 = [outcome(r, **kw0) for r in rows]
    d = [(a[0] - b[0], a[1] - b[1], a[2] - b[2]) for a, b in zip(o1, o0)]
    rng = random.Random(seed)
    res = []
    for _ in range(N_BOOT):
        s = [rng.choice(d) for _ in d]
        res.append(tuple(sum(x[j] for x in s) / len(s) for j in range(3)))
    out = []
    for j in range(3):
        v = sorted(x[j] for x in res)
        out.append((st.mean(x[j] for x in d), v[int(0.025 * N_BOOT)], v[int(0.975 * N_BOOT)]))
    return out  # [(d_success_per_card, lo, hi), (d_seconds, ...), (d_usd, ...)]


def median_ci(vals, seed):
    rng = random.Random(seed)
    res = sorted(st.median(rng.choice(vals) for _ in vals) for _ in range(N_BOOT))
    return res[int(0.025 * N_BOOT)], res[int(0.975 * N_BOOT)]


def section(title):
    print(f"\n=== {title} ===")


def q1_split():
    section("Q1a: success vs failure (Terra medium, cap 6, each card once)")
    for name, rows in (("BASE36 (no flags)", BASE), ("TPL36 (mechanical repair + statement pinning)", TPL), ("REP12 (mechanical repair only)", REP)):
        tt, tc = sum(r["elapsed_seconds"] for r in rows), sum(cost(r) for r in rows)
        print(f"{name}: n={len(rows)} success={sum(map(ok, rows))} total ${tc:.2f} {tt:.0f}s; per success ${tc / sum(map(ok, rows)):.3f}")
        for lab, sel in (("success", [r for r in rows if ok(r)]), ("failure", [r for r in rows if not ok(r)])):
            t = [r["elapsed_seconds"] for r in sel]
            c = [cost(r) for r in sel]
            print(
                f"  {lab}: n={len(sel)} time median {st.median(t):.0f}s mean {st.mean(t):.0f}s share {sum(t) / tt:.0%}"
                f" | cost median ${st.median(c):.3f} mean ${st.mean(c):.3f} share {sum(c) / tc:.0%}"
                f" | calls mean {st.mean(r['model_calls'] for r in sel):.1f} repairs mean {st.mean(r['repairs_used'] for r in sel):.1f}"
                f" | lean_seconds share of time {sum(r['lean_seconds'] for r in sel) / sum(t):.1%} (lower bound)"
            )
    print("BASE36 success by repairs used:")
    for n_rep in range(7):
        s = [r for r in BASE if ok(r) and r["repairs_used"] == n_rep]
        if s:
            print(f"  {n_rep}: n={len(s)} time median {st.median(r['elapsed_seconds'] for r in s):.0f}s cost median ${st.median(cost(r) for r in s):.3f}")
    print(f"line fit over {len(ALL)} runs: seconds = {TA:.1f} + {TB:.1f} x repairs (R2 {TR2:.2f}); usd = {CA:.4f} + {CB:.4f} x repairs (R2 {CR2:.2f})")
    print(f"  at cap 3 a failed run is estimated at {t_fit(3):.0f}s / ${c_fit(3):.3f}; at cap 6 {t_fit(6):.0f}s / ${c_fit(6):.3f}")

    section("Q1b: Draft / Sketch / sketch check (sketch-only runs, Terra medium)")
    rows = [r for f in ("diag1", "diag2", "diag3", "held1", "held2") for r in load(f)]
    good = [r for r in rows if r["model_calls"] == 2]
    for k in ("draft_seconds", "sketch_seconds", "lean_seconds", "elapsed_seconds"):
        v = sorted(r[k] for r in good)
        print(f"  {k}: median {st.median(v):.1f}s  p10 {v[int(0.1 * len(v))]:.1f}  p90 {v[int(0.9 * len(v)) - 1]:.1f}  (n={len(v)})")
    print(f"  Draft+Sketch cost median ${st.median(cost(r) for r in good):.4f} per run (n={len(good)})")
    for name, rs in (("BASE36", BASE), ("TPL36", TPL)):
        z = [r for r in rs if ok(r) and r["repairs_used"] == 0]
        print(f"  zero-repair successes {name}: n={len(z)} time median {st.median(r['elapsed_seconds'] for r in z):.0f}s cost median ${st.median(cost(r) for r in z):.3f}")


def q2_cap():
    section("Q2a: repair cap (desk, paired bootstrap over cards, difference vs cap 6)")
    for name, rows in (("BASE36", BASE), ("TPL36", TPL)):
        n = len(rows)
        print(name)
        for cap in (6, 5, 4, 3, 2, 1):
            o = [outcome(r, cap=cap) for r in rows]
            (ds, dslo, dshi), (dt, dtlo, dthi), (dc, dclo, dchi) = paired(rows, dict(cap=cap), dict(cap=6), 11)
            tm = [x[1] for x in o]
            lo, hi = median_ci(tm, 12)
            print(
                f"  cap {cap}: success {sum(x[0] for x in o)}/{n}; time mean {st.mean(tm):.0f}s median {st.median(tm):.0f}s [{lo:.0f}, {hi:.0f}]; cost mean ${st.mean(x[2] for x in o):.3f}"
                f" total ${sum(x[2] for x in o):.2f} | vs cap 6: success {ds * n:+.0f} cards [{dslo * n:+.0f}, {dshi * n:+.0f}], time {dt:+.1f}s [{dtlo:+.1f}, {dthi:+.1f}], cost {dc:+.4f} [{dclo:+.4f}, {dchi:+.4f}]"
            )


def q2_early_stop():
    section("Q2b: early stop on repeated mismatch (BASE36 only; TPL36 has zero mismatch attempts)")
    rows = BASE
    n = len(rows)
    print(
        f"mismatch attempts in BASE36: {sum(mm(c) for r in rows for c in r['diagnostic_codes'])} in {sum(any(mm(c) for c in r['diagnostic_codes']) for r in rows)} runs "
        f"(successes with a mismatch: {sum(ok(r) and any(mm(c) for c in r['diagnostic_codes']) for r in rows)}); in TPL36: {sum(mm(c) for r in TPL for c in r['diagnostic_codes'])}"
    )
    for cap in (6, 3):
        base = [outcome(r, cap=cap) for r in rows]
        print(f"cap {cap}: no rule success {sum(x[0] for x in base)}/{n} mean {st.mean(x[1] for x in base):.0f}s median {st.median(x[1] for x in base):.0f}s cost mean ${st.mean(x[2] for x in base):.3f}")
        for lab, kw in (("k=1", dict(k=1)), ("k=2", dict(k=2)), ("k=3", dict(k=3)), ("cum=2 (not consecutive)", dict(cum=2)), ("cum=3 (not consecutive)", dict(cum=3))):
            kw = dict(kw, cap=cap)
            o = [outcome(r, **kw) for r in rows]
            (ds, dslo, dshi), (dt, dtlo, dthi), (dc, dclo, dchi) = paired(rows, kw, dict(cap=cap), 13)
            lost = [r["problem"][:30] for r, a, b in zip(rows, o, base) if b[0] and not a[0]]
            stopped_fail = sum(1 for a, b in zip(o, base) if (not b[0]) and a[1] < b[1] - 1e-6)
            print(
                f"  {lab}: success {sum(x[0] for x in o)}/{n} ({ds * n:+.0f} cards [{dslo * n:+.0f}, {dshi * n:+.0f}]); time mean {st.mean(x[1] for x in o):.0f}s ({dt:+.1f}s [{dtlo:+.1f}, {dthi:+.1f}]) median {st.median(x[1] for x in o):.0f}s;"
                f" cost mean ${st.mean(x[2] for x in o):.3f} ({dc:+.4f} [{dclo:+.4f}, {dchi:+.4f}]); failed runs cut short {stopped_fail}; successes lost {len(lost)}"
            )


def q2_pinning_and_sketch():
    section("Q2c: statement pinning (observed pairs, same 36 cards; NOT a counterfactual)")
    b = {r["problem"]: r for r in BASE}
    t = {r["problem"]: r for r in TPL}
    assert set(b) == set(t)
    cards = sorted(b)
    groups = {
        "all 36": cards,
        "8 cards with a mismatch in the base run": [c for c in cards if any(mm(x) for x in b[c]["diagnostic_codes"])],
        "5 successes with a mismatch": [c for c in cards if ok(b[c]) and any(mm(x) for x in b[c]["diagnostic_codes"])],
        "28 cards with no mismatch": [c for c in cards if not any(mm(x) for x in b[c]["diagnostic_codes"])],
    }
    for lab, sel in groups.items():
        dt = [t[c]["elapsed_seconds"] - b[c]["elapsed_seconds"] for c in sel]
        dr = [t[c]["repairs_used"] - b[c]["repairs_used"] for c in sel]
        dc = [cost(t[c]) - cost(b[c]) for c in sel]
        m, lo, hi = boot_mean(dt, 21)
        print(f"  {lab} (n={len(sel)}): time {m:+.1f}s [{lo:+.1f}, {hi:+.1f}]; repairs {st.mean(dr):+.2f}; cost {st.mean(dc):+.4f}")
    sd = st.stdev([t[c]["elapsed_seconds"] - b[c]["elapsed_seconds"] for c in cards])
    print(f"  success base {sum(map(ok, BASE))}/36, pinned {sum(map(ok, TPL))}/36; paired time SD {sd:.0f}s")
    for d in (35, 25, 9):
        print(f"  pairs needed to detect a {d}s mean difference (80% power, alpha 0.05, same SD): {(2.8 * sd / d) ** 2:.0f}")
    succ_mm = [r for r in BASE if ok(r) and any(mm(c) for c in r["diagnostic_codes"])]
    ub_t = sum(t_fit(r["repairs_used"]) - t_fit(max(r["repairs_used"] - 1, 0)) for r in succ_mm) / 36
    ub_c = sum(c_fit(r["repairs_used"]) - c_fit(max(r["repairs_used"] - 1, 0)) for r in succ_mm) / 36
    print(f"  desk ceiling (one attempt saved in each of the {len(succ_mm)} successful runs that had a mismatch): {ub_t:.1f}s per card, ${ub_c:.4f} per card")
    for lab, A, B in (("design 12", BASE_A, TPL_A), ("held-out 24", BASE_B, TPL_B)):
        bb = {r["problem"]: r for r in A}
        tt = {r["problem"]: r for r in B}
        m, lo, hi = boot_mean([tt[c]["elapsed_seconds"] - bb[c]["elapsed_seconds"] for c in bb], 22)
        print(f"  {lab}: time {m:+.1f}s [{lo:+.1f}, {hi:+.1f}]; success {sum(map(ok, A))} vs {sum(map(ok, B))}")

    section("Q2d: mechanical Sketch repair (desk ceiling vs observed)")
    e = [r for r in BASE if empty_first(r)]
    ne = [r for r in BASE if not empty_first(r)]
    w = wilson(len(e), 36)
    print(f"  BASE36 first attempt had an empty Sketch: {len(e)}/36 (Wilson {w[0]:.2f}-{w[1]:.2f})")
    print(
        f"  empty-first vs not: time {st.mean(r['elapsed_seconds'] for r in e):.0f}s vs {st.mean(r['elapsed_seconds'] for r in ne):.0f}s,"
        f" repairs {st.mean(r['repairs_used'] for r in e):.2f} vs {st.mean(r['repairs_used'] for r in ne):.2f},"
        f" cost ${st.mean(cost(r) for r in e):.3f} vs ${st.mean(cost(r) for r in ne):.3f}"
    )
    w = wilson(15, 23)
    print(f"  offline fix rate 15/23 (design 10/14 + held-out 5/9): Wilson {w[0]:.2f}-{w[1]:.2f}")
    rng = random.Random(5)
    res = []
    for _ in range(N_BOOT):
        s = [rng.choice(BASE) for _ in BASE]
        ee = [r for r in s if empty_first(r)]
        nn = [r for r in s if not empty_first(r)]
        if not ee or not nn:
            continue
        share = len(ee) / len(s)
        p = rng.betavariate(15.5, 8.5)
        res.append(
            (
                share * p * (st.mean(r["elapsed_seconds"] for r in ee) - st.mean(r["elapsed_seconds"] for r in nn)),
                share * p * (st.mean(cost(r) for r in ee) - st.mean(cost(r) for r in nn)),
            )
        )
    for j, lab in ((0, "SAVING seconds per card (positive = faster; the entry reports it as a negative delta)"), (1, "SAVING usd per card (positive = cheaper)")):
        v = sorted(x[j] for x in res)
        print(f"  desk ceiling {lab}: {st.mean(v):.3f} [{v[int(0.025 * len(v))]:.3f}, {v[int(0.975 * len(v))]:.3f}] (assumes the whole excess of empty-first runs is removed in the fixed share)")
    bb = {r["problem"]: r for r in BASE_A}
    rr = {r["problem"]: r for r in REP}
    d = [rr[c]["elapsed_seconds"] - bb[c]["elapsed_seconds"] for c in bb]
    m, lo, hi = boot_mean(d, 23)
    print(
        f"  observed (12 design cards, repair only vs base): time {m:+.1f}s [{lo:+.1f}, {hi:+.1f}], repairs {sum(rr[c]['repairs_used'] - bb[c]['repairs_used'] for c in bb):+d},"
        f" success {sum(map(ok, BASE_A))} vs {sum(map(ok, REP))}; SD {st.stdev(d):.0f}s -> pairs for a 16s difference: {(2.8 * st.stdev(d) / 16) ** 2:.0f}"
    )


def scheme():
    section("Scheme-theory rows (different cards; per arm; success = verified and approved; cap 3 by a line fit over these rows)")

    def rows_of(*names):
        return [json.loads(line) for n in names for line in (DOCS / f"scheme-theory-measurement-rows-{n}-2026-11-09.jsonl").read_text().splitlines() if line.strip()]

    arms = {"a (Mathlib only, M01-M16 + C01,C02)": rows_of("arm-a", "run2-a"), "b": rows_of("arm-b"), "c (Frontier, first run)": rows_of("arm-c")}
    allr = [r for rs in arms.values() for r in rs]
    a, b, _ = linfit([r["repairs_used"] for r in allr], [r["wall_s"] for r in allr])
    ca, cb, _ = linfit([r["repairs_used"] for r in allr], [r["usd"] for r in allr])
    print(f"  line fit over {len(allr)} rows: seconds = {a:.0f} + {b:.0f} x repairs; usd = {ca:.3f} + {cb:.3f} x repairs")
    for name, rs in arms.items():
        succ = [r for r in rs if r.get("state") == "verified" and r.get("review") == "approved"]
        fail = [r for r in rs if r not in succ]
        tt, tc = sum(r["wall_s"] for r in rs), sum(r["usd"] for r in rs)
        c3 = sum(1 for r in succ if r["repairs_used"] <= 3)

        def cap3(r):
            if r["repairs_used"] <= 3:
                return r["wall_s"], r["usd"]
            return r["wall_s"] * (a + b * 3) / (a + b * r["repairs_used"]), r["usd"] * (ca + cb * 3) / (ca + cb * r["repairs_used"])

        o = [cap3(r) for r in rs]
        print(
            f"  {name}: n={len(rs)} success {len(succ)} (cap 3: {c3}); time median all {st.median(r['wall_s'] for r in rs):.0f}s success {st.median(r['wall_s'] for r in succ):.0f}s failure {st.median(r['wall_s'] for r in fail):.0f}s;"
            f" failure share of time {sum(r['wall_s'] for r in fail) / tt:.0%} of cost {sum(r['usd'] for r in fail) / tc:.0%}; total ${tc:.2f};"
            f" cap 3 estimate: mean {st.mean(x[0] for x in o):.0f}s vs {st.mean(r['wall_s'] for r in rs):.0f}s, cost ${sum(x[1] for x in o):.2f} vs ${tc:.2f}; lean share {sum(r['lean_s'] for r in rs) / tt:.1%}"
        )


def main():
    q1_split()
    q2_cap()
    q2_early_stop()
    q2_pinning_and_sketch()
    scheme()


if __name__ == "__main__":
    main()
