"""Aggregate per-stage model time from eval ``*/result.json`` files.

Usage: python3 -I stage_breakdown.py <dir containing <run>/result.json>

Two things are easy to get wrong, so they are handled explicitly:

* A repair route decided by ``deterministic_repair_route`` has no model call. Its
  ``attempt_outputs`` is empty and ``elapsed_ms`` is 0, so the stage to re-run is
  read from the recorded ``route`` and the decision is counted separately from
  the model route-selection timings (``provider`` marks it).
* When Draft or Sketch fails, the pipeline stores a GeneratedProof with an empty
  ``lean_code`` whose ``elapsed_ms`` is copied from the failed stage. Prove did
  not run, so it must not be counted as a Prove sample.
"""

from __future__ import annotations

import collections
import glob
import json
import statistics as st
import sys

DETERMINISTIC_PROVIDER = "pals-deterministic-policy"
STAGES_BY_ROUTE = {
    "initial": ("draft", "sketch", "prove"),
    "draft": ("draft", "sketch", "prove"),
    "sketch": ("sketch", "prove"),
    "prove": ("prove",),
}


def recorded_route(rr: dict) -> str:
    route = rr.get("route")
    if route in STAGES_BY_ROUTE:
        return route
    try:  # older records without a top-level route
        return json.loads(rr["attempt_outputs"][-1])["route"]
    except (KeyError, IndexError, TypeError, ValueError):
        return "?"


def prove_ran(generated: dict) -> bool:
    return bool((generated.get("lean_code") or "").strip())


def collect(root: str):
    samples = collections.defaultdict(list)  # stage -> [(seconds, chars)]
    routes = collections.Counter()
    deterministic = collections.Counter()
    skipped_prove = 0
    for path in sorted(glob.glob(root + "/*/result.json")):
        if path.split("/")[-2].startswith("dry"):
            continue
        with open(path) as handle:
            data = json.load(handle)
        for attempt in data.get("attempts", []):
            generated = attempt.get("generated") or {}
            rr = attempt.get("repair_route")
            if rr is None:
                route = "initial"
            else:
                route = recorded_route(rr)
                if rr.get("provider") == DETERMINISTIC_PROVIDER:
                    deterministic[route] += 1
                else:
                    chars = sum(len(x) for x in rr.get("attempt_outputs", []))
                    samples["route"].append((rr["elapsed_ms"] / 1000, chars))
                    routes[route] += 1
            if route not in STAGES_BY_ROUTE:
                raise ValueError(f"unrecognised repair route {route!r} in {path}")
            for stage in STAGES_BY_ROUTE[route]:
                if stage == "prove":
                    if not prove_ran(generated):
                        skipped_prove += 1
                        continue
                    key = "prove_init" if rr is None else "prove_rep"
                    elapsed = generated.get("elapsed_ms", 0)
                    chars = len(generated.get("raw_model_output", ""))
                else:
                    record = generated.get(stage)
                    if not record:
                        continue
                    key = stage
                    elapsed = record.get("elapsed_ms", 0)
                    chars = len(record.get("raw_model_output", ""))
                samples[key].append((elapsed / 1000, chars))
            verification = attempt.get("verification", {})
            samples["lean"].append((verification.get("elapsed_ms", 0) / 1000, 0))
    return samples, routes, deterministic, skipped_prove


def main() -> None:
    samples, routes, deterministic, skipped_prove = collect(sys.argv[1])
    for key, rows in samples.items():
        times = [x[0] for x in rows]
        chars = [x[1] for x in rows]
        print(
            f"{key:12s} n={len(rows):3d} total={sum(times):7.0f}s "
            f"mean={st.mean(times):5.1f}s median={st.median(times):5.1f}s "
            f"mean_chars_out={st.mean(chars):6.0f}"
        )
    print("model routes:", dict(routes))
    print("deterministic routes (no model call):", dict(deterministic))
    print("attempts without a Prove call (not counted):", skipped_prove)


if __name__ == "__main__":
    main()
