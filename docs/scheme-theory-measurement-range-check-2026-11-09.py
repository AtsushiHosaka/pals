"""For every F card: the harness retrieval (same terms, k=80, RRF) WITHOUT the built-set filter; report the top NOTE_K
candidates and whether their module is inside the built set B (imp/s2_closure.json). Mechanical rule, no judgement."""
import json, sys
sys.path.append("/private/tmp/claude-501/-Users-atsushi-Desktop-projects-personal-pals--claude-worktrees-stacks-verifier-routing-312479/4c12f0f4-9f14-4f87-a355-2cddd28858fa/scratchpad/idx2")
from pathlib import Path
from tools.stacks_index.search import StacksIndex, lean_query_terms, natural_query_terms, reciprocal_rank_fusion
S = Path(__file__).resolve().parent
B = set(json.load(open(S / "imp/s2_closure.json")))
index = StacksIndex(S / "idx-out/index.sqlite")
cards = json.load(open(S.parent.parent.parent.parent.parent / "dev/null")) if False else None
cards = json.load(open("/Users/atsushi/Desktop/projects/personal/pals/.claude/worktrees/stacks-verifier-routing-312479/docs/scheme-theory-measurement-cards-2026-11-09.json"))["cards"]
out = {}
for card in cards:
    if card["group"] != "F": continue
    terms = natural_query_terms(card["nl"]) + lean_query_terms(card["formal"])
    fused = reciprocal_rank_fusion([index.text_search(terms, k=80, scope="all", include_upstream=False),
                                    index.symbol_search_lean(card["formal"], k=80, scope="all")], k=120)
    picked = []
    for cand in fused:
        row = index.describe([cand.name])
        if not row: continue
        row = row[0]
        if row["kind"] not in ("theorem","lemma","def","abbrev","instance","structure","class"): continue
        picked.append(row)
        if len(picked) >= 12: break
    out[card["id"]] = [{"name": r["name"], "module": r["module"], "trust": r["trust"], "in_B": r["module"] in B or r["trust"] != "frontier"} for r in picked]
    print(card["id"], "outside B:", sum(1 for r in out[card["id"]] if not r["in_B"]), "of", len(picked))
    for r in out[card["id"]]:
        print("   ", "IN " if r["in_B"] else "OUT", r["trust"], r["module"].replace("StacksFrontier.AlgebraicGeometry.","SF.AG."), "::", r["name"])
json.dump(out, open(S / "range_check.json", "w"), indent=1)
