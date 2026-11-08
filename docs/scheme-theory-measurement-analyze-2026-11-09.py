"""Aggregate ag_eval rows: python3 analyze.py run-a/rows.jsonl run-c/rows.jsonl ..."""
import json
import math
import statistics
import sys
from pathlib import Path


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def pct(xs, q):
    xs = sorted(xs)
    if not xs:
        return float("nan")
    k = (len(xs) - 1) * q
    f, c = math.floor(k), math.ceil(k)
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def success(r, cap):
    ok = r.get("state") == "verified" and r.get("review") == "approved" and not r.get("error")
    if not ok:
        return False
    used = r.get("repairs_used")
    return used is not None and used <= cap


rows = []
for path in sys.argv[1:]:
    for line in Path(path).read_text().splitlines():
        if line.strip():
            rows.append(json.loads(line))
# keep the last run per (id, arm)
last = {}
for r in rows:
    last[(r["id"], r["arm"])] = r
rows = list(last.values())
for arm in sorted({r["arm"] for r in rows}):
    rs = [r for r in rows if r["arm"] == arm and r["group"] != "T"]
    n = len(rs)
    if not n:
        continue
    for cap in (6, 3):
        k = sum(success(r, cap) for r in rs)
        lo, hi = wilson(k, n)
        print(f"arm {arm}  cap{cap}: {k}/{n} = {k/n:.3f}  Wilson95 [{lo:.2f}, {hi:.2f}]")
    wall = [r["wall_s"] for r in rs]
    ok = [r["wall_s"] for r in rs if success(r, 6)]
    print(f"  wall_s all: median {statistics.median(wall):.1f} p90 {pct(wall, .9):.1f} mean {statistics.mean(wall):.1f}")
    if ok:
        print(f"  wall_s successes: median {statistics.median(ok):.1f} p90 {pct(ok, .9):.1f} mean {statistics.mean(ok):.1f}")
    lean = [r["lean_s"] for r in rs]
    print(f"  lean_s total per card: median {statistics.median(lean):.1f}  share of wall {sum(lean)/sum(wall):.2f}")
    usd = [r["usd"] for r in rs]
    print(f"  usd: sum {sum(usd):.3f} median {statistics.median(usd):.3f} max {max(usd):.3f}; per success {sum(usd)/max(1,sum(success(r,6) for r in rs)):.3f}")
    print(f"  model_calls median {statistics.median([r['model_calls'] for r in rs])}; load_1m median {statistics.median([r['load_1m'] for r in rs]):.1f} max {max(r['load_1m'] for r in rs):.1f}")
    print("  id    state     review    rep  wall  lean  calls  usd   trust/notes")
    for r in sorted(rs, key=lambda r: r["id"]):
        trust = ",".join(sorted({m.get("trust_level", "?") for m in (r.get("trust") or [])})) or "-"
        print(
            f"  {r['id']:4} {str(r.get('state')):9} {str(r.get('review')):9} {str(r.get('repairs_used')):>3} "
            f"{r['wall_s']:6.1f} {r['lean_s']:5.1f} {r['model_calls']:4}  {r['usd']:.3f}  {trust} {r.get('error') or ''} {r.get('codes') if r.get('state')!='verified' else ''}"
        )
