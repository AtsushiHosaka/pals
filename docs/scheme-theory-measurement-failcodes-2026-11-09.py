import json,glob,re,collections,sys
CLASSES=[("unknown identifier|unknown constant|Unknown identifier|unknown namespace","unknown_name"),("Type mismatch|type mismatch|has type|application type mismatch","type_mismatch"),("unsolved goals","unsolved_goals"),("failed to synthesize","instance_synth"),("sorry|axiom","policy"),("unexpected token|expected","parse"),("deterministic|timeout|maximum recursion","resource")]
def cls(m):
    for p,n in CLASSES:
        if re.search(p,m): return n
    return "other"
for arm,run in (("a","run-a"),("b","run-b"),("c","run-c")):
    for d in sorted(glob.glob(f"{run}/art/*-{arm}")):
        cid=d.split('/')[-1].rsplit('-',1)[0]
        codes=collections.Counter(); classes=collections.Counter(); n=0
        for f in sorted(glob.glob(f"{d}/*/attempts/*.json")):
            n+=1
            a=json.load(open(f))["attempt"]
            for x in a.get("diagnostics",[]):
                if x.get("severity")=="error":
                    codes[x["code"]]+=1
                    if x["code"]=="lean.error": classes[cls(x.get("message",""))]+=1
        res=json.load(open(glob.glob(f"{d}/*/result.json")[0])) if glob.glob(f"{d}/*/result.json") else {}
        print(arm,cid,"attempts",n,dict(codes),dict(classes))
