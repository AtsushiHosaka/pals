import json,glob,sys,collections,statistics as st
root=sys.argv[1]
# stage -> list of (seconds, chars)
T=collections.defaultdict(list)
routes=collections.Counter()
cards=0; lean=0; tot=0; calls=0
per_card=[]
byrun=collections.defaultdict(lambda:collections.defaultdict(float))
for f in sorted(glob.glob(root+'/*/result.json')):
    name=f.split('/')[-2]
    if name.startswith('dry'): continue
    run=name.split('-baseline-')[0]
    d=json.load(open(f))
    prev=None
    for a in d.get('attempts',[]):
        g=a.get('generated') or {}
        rr=a.get('repair_route')
        route='initial' if rr is None else None
        if rr:
            T['route'].append((rr['elapsed_ms']/1000,sum(len(x) for x in rr.get('attempt_outputs',[]))))
            try: route=json.loads(rr['attempt_outputs'][-1])['route']
            except Exception: route='?'
            routes[route]+=1
        stages={'initial':['draft','sketch','prove'],'draft':['draft','sketch','prove'],'sketch':['sketch','prove'],'prove':['prove'],'?':['prove']}[route]
        for s in stages:
            if s=='prove':
                if g.get('lean_code') is not None: T['prove'+('_init' if rr is None else '_rep')].append((g.get('elapsed_ms',0)/1000,len(g.get('raw_model_output',''))))
            else:
                x=g.get(s)
                if x: T[s].append((x.get('elapsed_ms',0)/1000,len(x.get('raw_model_output',''))))
        v=a.get('verification',{})
        T['lean'].append((v.get('elapsed_ms',0)/1000,0))
for k,v in T.items():
    n=len(v); ts=[x[0] for x in v]; cs=[x[1] for x in v]
    print(f"{k:12s} n={n:3d} total={sum(ts):7.0f}s mean={st.mean(ts):5.1f}s median={st.median(ts):5.1f}s  mean_chars_out={st.mean(cs):6.0f}")
print(routes)
