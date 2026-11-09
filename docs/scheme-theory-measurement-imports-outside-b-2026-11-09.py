"""Post-hoc: which `import StacksFrontier...` modules of each final file lie outside the base range B?
(The harness did not record this field, see the results document 10.6.)

usage: python3 this.py BASE_BUILT.json ADDED.json RUNDIR[:ARM] ...   (BASE_BUILT = module list of B, ADDED = the 523 modules of B')
Reads RUNDIR/rows.jsonl and RUNDIR/<id>-<arm>.lean; prints JSON."""
import json, re, sys
from pathlib import Path

base = set(json.load(open(sys.argv[1], encoding="utf-8")))
added = set(json.load(open(sys.argv[2], encoding="utf-8")))
out = []
for run in sys.argv[3:]:
    for line in Path(run, "rows.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        f = Path(run, f"{r['id']}-{r['arm']}.lean")
        code = f.read_text(encoding="utf-8") if f.exists() else ""
        mods = re.findall(r"^import (StacksFrontier\S*)", code, re.M)
        out.append({"run": Path(run).name, "id": r["id"], "arm": r["arm"], "state": r.get("state"), "review": r.get("review"),
                    "imports_outside_B": sorted(m for m in mods if m not in base),
                    "of_which_in_B_prime_added": sorted(m for m in mods if m in added)})
print(json.dumps(out, ensure_ascii=False, indent=1))
