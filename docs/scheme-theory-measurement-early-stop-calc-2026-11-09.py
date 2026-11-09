"""Desk calculation: what would stop_on_repeated_harness_mismatch (existing rule) and a widened variant cut on the 11 recorded failures?
Rule E1 (existing, pipeline._harness_mismatch_repeated): stop when the last two attempts each had ONLY lean.formal_harness_mismatch as error codes.
Rule E2 (widened): same, but codes in {lean.formal_harness_mismatch, lean.statement_mismatch}.
Also report: did any run whose history matched later succeed (for successes too: scan all 27 runs)."""
import glob, json
H = {"lean.formal_harness_mismatch"}
H2 = H | {"lean.statement_mismatch"}
def attempts(d):
    out = []
    for f in sorted(glob.glob(f"{d}/*/attempts/*.json")):
        a = json.load(open(f))["attempt"]
        codes = {x["code"] for x in a.get("diagnostics", []) if x.get("severity") == "error"}
        out.append((a["attempt"], codes))
    return out
rows = {}
for arm, run in (("a","run-a"),("b","run-b"),("c","run-c")):
    for line in open(f"{run}/rows.jsonl"):
        r = json.loads(line); rows[(r["id"], r["arm"])] = r
def stop_at(att, allowed):
    # history[-2:] both exactly allowed-only (E1: exactly {harness}; E2: subset of allowed and non-empty)
    for i in range(1, len(att)):
        pair = [att[i-1][1], att[i][1]]
        if allowed is H:
            ok = all(c == H for c in pair)
        else:
            ok = all(c and c <= allowed for c in pair)
        if ok:
            return att[i][0]  # stop after this attempt (no further repair)
    return None
print("id arm outcome attempts model_calls usd | E1 stop_after | E2 stop_after | later-success?")
tot = {"E1":0,"E2":0}
for (cid, arm), r in sorted(rows.items()):
    if r["group"] == "T": continue
    att = attempts(f"run-{arm}/art/{cid}-{arm}")
    ok = r.get("state") == "verified" and r.get("review") == "approved"
    e1, e2 = stop_at(att, H), stop_at(att, H2)
    seq = " ".join("+".join(sorted(c)).replace("lean.","")[:22] or "-" for _, c in att)
    print(cid, arm, "OK " if ok else "FAIL", len(att), r["model_calls"], r["usd"], "|", e1, "|", e2, "|", seq)

# ---- cost/time per attempt (estimates) -------------------------------------------------
R_IN, R_OUT = 2.5/1e6, 12.0/1e6
def per_attempt(d):
    out = []
    for f in sorted(glob.glob(f"{d}/*/attempts/*.json")):
        a = json.load(open(f))["attempt"]
        g = a.get("generated") or {}
        usd = ms = 0.0
        def stage(s):
            nonlocal usd, ms
            if not isinstance(s, dict): return
            usd += len(s.get("prompt") or "")/3*R_IN + len(s.get("raw_model_output") or "")/3*R_OUT
            ms += s.get("elapsed_ms") or 0
        for k in ("draft","sketch"): stage(g.get(k))
        stage(g)  # prove stage lives on the generated object itself
        stage(a.get("repair_route"))
        codes = {x["code"] for x in a.get("diagnostics", []) if x.get("severity") == "error"}
        out.append({"n": a["attempt"], "usd": usd, "s": ms/1000, "codes": codes})
    return out
print()
for cap in (6, 3):
    for name, allowed in (("E1", H), ("E2", H2)):
        stopped = saved_usd = saved_s = 0; lost = []; fail_stopped = []
        base_usd = base_s = 0
        for (cid, arm), r in sorted(rows.items()):
            if r["group"] == "T": continue
            att = per_attempt(f"run-{arm}/art/{cid}-{arm}")
            est = sum(x["usd"] for x in att)
            scale = r["gen_usd"]/est if est else 1.0   # calibrate char-based estimate to the recorded cost
            ok = r.get("state") == "verified" and r.get("review") == "approved" and (r["repairs_used"] or 0) <= cap
            att_cap = att[:cap+1]
            codes_only = [(x["n"], x["codes"]) for x in att_cap]
            s = stop_at(codes_only, allowed)
            # cost without the rule (what a cap-limited run costs)
            base = sum(x["usd"] for x in att_cap)*scale; base_t = sum(x["s"] for x in att_cap)
            base_usd += base; base_s += base_t
            if s is not None and s < len(att_cap):
                stopped += 1
                sv = sum(x["usd"] for x in att_cap if x["n"] > s)*scale
                saved_usd += sv; saved_s += sum(x["s"] for x in att_cap if x["n"] > s)
                if ok: lost.append((cid, arm, s, r["repairs_used"]))
                else: fail_stopped.append(cid+arm)
        print(f"cap{cap} {name}: stopped {stopped} runs (failures {len(fail_stopped)}: {' '.join(fail_stopped)}); lost successes {lost}; "
              f"saved ~${saved_usd:.2f} of ${base_usd:.2f} ({saved_usd/base_usd:.0%}), model-time {saved_s:.0f}s of {base_s:.0f}s ({saved_s/base_s:.0%})")
