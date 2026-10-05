"""Real Lean CLI checks of independent anonymous examples and their kernel axioms.

Anonymous examples add no reusable declaration to the environment. All original
examples precede named audit copies, so the audit copies cannot help prove them.
A final compilation containing only accepted examples must exit zero. Receipts
bind the actual batch command and bytes; they do not claim individual CLI runs.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

ALLOWED_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build(values: list[dict], *, negative_control: bool) -> tuple[str, list, int | None]:
    source="import Mathlib\n\n"
    spans=[]
    for audit in [False,True]:
        for value in values:
            card=value['card']
            name='catalog_'+card['id'].split('.')[-1]
            header=f"theorem {name} : " if audit else "example : "
            start=source.count('\n')+1
            source+=header+card['target_source']+' := '+card['proof_body']+'\n\n'
            if audit:
                source+=f"#print axioms {name}\n\n"
            spans.append((start,source.count('\n'),card['id'],audit))
    control=None
    if negative_control:
        control=source.count('\n')+1
        source+='example : (1:ℕ)+1=3 := by decide\n'
    return source,spans,control


def execute(values: list[dict], *, workspace: Path, evidence: Path, name: str,
            negative_control: bool) -> tuple[dict,dict,set]:
    source,spans,control=build(values,negative_control=negative_control)
    path=evidence/(name+'.lean')
    path.write_text(source)
    command=['lake','env','lean','--threads=1',str(path)]
    print(json.dumps({'compiler_started':name,'examples':len(values),'source_sha256':digest(source.encode())}),flush=True)
    started=time.monotonic()
    completed=subprocess.run(command,cwd=workspace,text=True,capture_output=True,timeout=1800)
    output=completed.stdout+completed.stderr
    (evidence/(name+'.log')).write_text(output)
    errors=[int(match.group(1)) for match in re.finditer(r'^.*?:(\d+):\d+: error(?:\([^)]*\))?:',output,re.MULTILINE)]
    if negative_control and (completed.returncode==0 or control not in errors):
        raise ValueError('the intentionally false compiler control was not rejected')
    if any(line<3 for line in errors):
        raise ValueError('Mathlib import or batch header failed')
    rejected=set()
    for line in errors:
        matched=False
        for start,end,identifier,_ in spans:
            if start<=line<=end:
                rejected.add(identifier);matched=True
        if not matched and line!=control:
            raise ValueError('compiler error is not bound to a card')
    axioms={}
    for value in values:
        card=value['card'];theorem_name='catalog_'+card['id'].split('.')[-1]
        found=re.search(re.escape("'"+theorem_name+"'")+r" (?:depends on axioms: \[([^\]]*)\]|does not depend on any axioms)",output)
        if found is None:
            rejected.add(card['id']);continue
        dependencies=sorted(x.strip() for x in (found.group(1) or '').split(',') if x.strip())
        axioms[card['id']]=dependencies
        if not set(dependencies)<=ALLOWED_AXIOMS:
            rejected.add(card['id'])
    receipt={
        'schema_version':'pals.math-catalog-real-batch-compilation.v1',
        'argv':command,'source_sha256':digest(source.encode()),
        'output_sha256':digest(output.encode()),'exit_code':completed.returncode,
        'elapsed_ms':int((time.monotonic()-started)*1000),
        'negative_control':negative_control,'rejected_card_ids':sorted(rejected),
        'checked_card_ids':[v['card']['id'] for v in values],
    }
    (evidence/(name+'-receipt.json')).write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'compiler_finished':name,'exit_code':completed.returncode,'rejected':len(rejected),'elapsed_ms':receipt['elapsed_ms']}),flush=True)
    return receipt,axioms,rejected


def verify(values: list[dict], *, workspace: Path, evidence: Path) -> tuple[list,list]:
    exploratory,_,excluded=execute(values,workspace=workspace,evidence=evidence,
        name='exploratory-batch',negative_control=True)
    accepted=[v for v in values if v['card']['id'] not in excluded]
    failed=[v for v in values if v['card']['id'] in excluded]
    # The final file is independently compiled, without the negative control or failed code.
    receipt,axioms,rejected=execute(accepted,workspace=workspace,evidence=evidence,
        name='accepted-batch',negative_control=False)
    if receipt['exit_code']!=0 or rejected or len(axioms)!=len(accepted):
        raise ValueError('the final compilation is not fully successful')
    receipt_sha=digest(json.dumps(receipt,sort_keys=True,separators=(',',':')).encode())
    command_sha=digest(json.dumps({'argv':receipt['argv'],'workspace_lake_manifest_sha256':digest((workspace/'lake-manifest.json').read_bytes()),'workspace_lean_toolchain_sha256':digest((workspace/'lean-toolchain').read_bytes())},sort_keys=True,separators=(',',':')).encode())
    for value in accepted:
        identifier=value['card']['id']
        value.update(success=True,axioms=axioms[identifier],elapsed_ms=receipt['elapsed_ms'],
            compiler_command_sha256=command_sha,compiler_result={
                'schema_version':'pals.math-catalog-batch-result.v1',
                'verification_succeeded':True,'method':'independent-anonymous-examples-before-named-audits',
                'batch_source_sha256':receipt['source_sha256'],'batch_receipt_sha256':receipt_sha,
                'batch_exit_code':0,'individual_cli_run':False,'axioms':axioms[identifier],
            })
    for value in failed:
        value.update(success=False,compiler_result=None,
            failure='exploratory_compiler_error_or_unapproved_axiom',
            exploratory_receipt_sha256=digest(json.dumps(exploratory,sort_keys=True,separators=(',',':')).encode()))
    return accepted,failed
