"""Offline re-computation restricted to the 12 cards whose Luna time comes from the
same-day sequential run (the "Terra side": s1a-luna-on-terra12.jsonl).

Added on 2026-11-09 after review: the 24-card interval in sim.py mixes Luna times from the
2026-11-03 parallel run (the "Luna side" 12 cards) with times from sequential runs, so it cannot
isolate the policy difference. This script reuses sim.py's definitions unchanged and only
changes which cards enter the paired bootstrap. No model calls. Data paths are relative.
"""
import json
import os
import random
import re

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "sim.py")).read()
# Reuse sim.py's tables and policies verbatim; only the data directory is rebound.
src = re.sub(r'^S = ".*"$', f'S = {HERE!r} + "/"', src, flags=re.M)
# Drop the 24-card report at the end (everything from `policies =` on) and rerun it below.
head = src.split("\npolicies = ")[0]
ns = {}
exec(compile(head, "sim_head", "exec"), ns)
cards, policy_A, policy_B = ns["cards"], ns["policy_A"], ns["policy_B"]

matched = [c for c in cards if c[0] in ns["terra_t"]]
assert len(matched) == 12
random.seed(0)
print("matched-condition subset: 12 cards (Luna time from the same-day sequential run)")
for k in (2, 3):
    a = [policy_A(l, t)[0] for _, l, t in matched]
    b = [policy_B(k)(l, t)[0] for _, l, t in matched]
    diffs = [x - y for x, y in zip(a, b)]  # >0 means B is faster
    boots = sorted(sum(random.choice(diffs) for _ in diffs) / len(diffs) for _ in range(10000))
    print(f"time/card A {sum(a)/12:6.1f}s  B(k={k}) {sum(b)/12:6.1f}s  "
          f"A - B(k={k}): mean {sum(diffs)/12:6.1f}s  95% CI [{boots[250]:.1f}, {boots[9750]:.1f}]")
