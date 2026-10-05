#!/usr/bin/env python3
"""Prepare, kernel-check and append mathematics using existing production tables.

Run inventory/compile in the pinned verifier image with networking disabled.
Embedding uses the existing OpenAI binding. Applying needs an explicit DB identity
and --apply. Unsigned Draft generations remain inactive, with truthful review state;
this command cannot manufacture independent approval or activation evidence.
Artifacts are written only to the supplied ignored evidence directory.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import sys
import textwrap
from uuid import uuid4


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def save(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def closed_target(header: str, proof: str) -> tuple[str, str]:
    """Close an example telescope; never insert or delete a mathematical premise."""
    header = header.strip()
    if not header.startswith("example") or not proof.strip().startswith("by"):
        raise ValueError("not one tactic example")
    rest = header[len("example"):].strip()
    depth = 0
    boundary = None
    for i, ch in enumerate(rest):
        if ch in "({[":
            depth += 1
        elif ch in ")}]":
            depth -= 1
        elif ch == ":" and depth == 0:
            boundary = i
            break
    if boundary is None or depth != 0:
        raise ValueError("invalid example telescope")
    telescope = rest[:boundary].strip()
    proposition = rest[boundary+1:].strip()
    if not proposition or ":=" in proposition:
        raise ValueError("invalid proposition")
    names = []
    i = 0
    while i < len(telescope):
        if telescope[i].isspace():
            i += 1
            continue
        if telescope[i] not in "({[":
            raise ValueError("unsupported telescope")
        start = i
        stack = [telescope[i]]
        i += 1
        while i < len(telescope) and stack:
            if telescope[i] in "({[":
                stack.append(telescope[i])
            elif telescope[i] in ")}]":
                stack.pop()
            i += 1
        if stack:
            raise ValueError("unbalanced telescope")
        interior = telescope[start+1:i-1]
        if telescope[start] == "[" and ":" not in interior:
            names.append(f"catalog_inst_{len(names)}")
        else:
            binder_names = interior.split(":", 1)[0].strip().split()
            if not binder_names or any(not re.fullmatch(r"[A-Za-z_\u0080-\uffff][A-Za-z0-9_'\u0080-\uffff]*", n) for n in binder_names):
                raise ValueError("unsupported binder name")
            names.extend(binder_names)
    body = textwrap.dedent(proof.strip()[2:]).strip()
    if not body:
        raise ValueError("empty proof")
    if names:
        proposition = f"∀ {telescope}, {proposition}"
        body = "intro " + " ".join(names) + "\n" + body
    return re.sub(r"\s+", " ", proposition), "by\n" + textwrap.indent(body, "  ")


def inventory(args) -> None:
    from pals_agent.private_typed_candidates import profile_contract
    from pals_agent.private_draft_candidates import DraftCandidateCompatibilityError
    from app.schemas.typed_catalog import TypedDraft

    candidates, exclusions, seen, typed_seen = [], [], set(), set()
    source_files = []
    for path in sorted((args.root / "docs").glob("*.json")):
        try:
            payload = json.loads(path.read_text())
        except (ValueError, UnicodeError):
            continue
        if not isinstance(payload, dict) or not isinstance(payload.get("cards"), list):
            continue
        source_files.append((str(path.relative_to(args.root)), payload))
    spec = importlib.util.spec_from_file_location("school_math", args.root / "pals-scripts/math-catalog-school-20261005.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source_files.append(("pals-scripts/math-catalog-school-20261005.py", {"cards": module.cards()}))
    for source_path, payload in source_files:
        profile = payload.get("profile_id")
        if not profile and isinstance(payload.get("profile"), dict):
            profile = payload["profile"].get("id") or payload["profile"].get("profile_id")
        for raw in payload["cards"]:
            if not isinstance(raw, dict) or not raw.get("lean_witness"):
                continue
            identifier = str(raw.get("id", ""))
            try:
                witness = raw["lean_witness"].strip()
                header = raw.get("lean_target", "")
                if not header:
                    if ":=" not in witness:
                        raise ValueError("no exact target")
                    header, witness = witness.split(":=", 1)
                target, body = closed_target(header, witness)
                if re.search(r"\b(native_decide|ofReduceBool|sorryAx|sorry|admit|axiom|unsafe)\b", target + body):
                    raise ValueError("unchecked or additional trusted construct")
                identity = sha(re.sub(r"\s+", " ", target).encode())
                if identity in seen:
                    continue
                card_profile = raw.get("profile_id") or profile or raw.get("openmath_profile")
                typed = None
                if isinstance(card_profile, str) and card_profile.startswith("typed-"):
                    try:
                        contract, binding = profile_contract(card_profile)
                    except DraftCandidateCompatibilityError:
                        from pals_agent.typed_expansion_profiles import expansion_profile_spec
                        contract = expansion_profile_spec(card_profile)
                        if contract is None:
                            raise
                        binding = dict(
                            profile_id=card_profile,
                            validator_sha256=sha((args.root/contract.validator_module_path).read_bytes()),
                            registry_sha256=sha((args.root/contract.registry_path).read_bytes()),
                            canonicalizer_version="openmath-cdbase-alpha-c14n-v4",
                            embedding_provider="openai",embedding_model="text-embedding-3-small",
                            embedding_dimension=384,embedding_revision="openai-release-2024-01-25",
                            embedding_input_version="pals-typed-catalog-embedding-v1",
                        )
                    xml = contract.canonicalize(raw.get("canonical_openmath_xml") or raw["openmath_xml"])
                    contract.validate_canonical(xml)
                    draft_id = re.sub(r"[^a-z0-9_]", "_", identifier.lower())
                    if not draft_id or not draft_id[0].isalpha():
                        draft_id = "math_" + draft_id
                    if len(draft_id) > 64:
                        draft_id = draft_id[:51] + "_" + sha(identifier.encode())[:12]
                    typed = TypedDraft(
                        id=draft_id, canonical_statement=raw["canonical_statement"],
                        openmath_xml=xml, proof_strategy=raw["proof_strategy"],
                        sketch_steps=list(raw["sketch_steps"]),
                    ).model_dump()
                    xml_key = (card_profile, xml)
                    if xml_key in typed_seen:
                        typed = None
                    else:
                        typed_seen.add(xml_key)
                seen.add(identity)
                candidates.append(dict(
                    id="math26." + identity[:24], original_id=identifier,
                    source_path=source_path, source_file_sha256=sha((args.root/source_path).read_bytes()),
                    canonical_statement=raw.get("canonical_statement", ""),
                    proof_strategy=raw.get("proof_strategy", ""),
                    sketch_steps=raw.get("sketch_steps", []),
                    target_source=target, proof_body=body,
                    profile_id=card_profile if typed else None,
                    draft=typed, binding=binding if typed else None,
                    level=raw.get("level") or raw.get("domain") or "existing_authored_candidate",
                ))
            except (ValueError, KeyError, TypeError, DraftCandidateCompatibilityError) as error:
                exclusions.append(dict(id=identifier, source=source_path, reason=str(error)))
    save(args.evidence / "inventory.json", {"candidates": candidates, "exclusions": exclusions})
    print(json.dumps({"candidates":len(candidates), "typed_drafts":sum(bool(c['draft']) for c in candidates), "excluded_before_compile":len(exclusions)}),flush=True)


def compile_candidates(args) -> None:
    from pals_agent.lean_verifier.http_server import pinned_recipe_admission_context
    from app.domain.recipe_catalog_admission import (
        RecipeAuthoringManifestV1, RecipeMaterializerV1, canonical_json_bytes,
        validate_materialized_recipe,
    )
    engine_path=args.root/'pals-scripts/lean-catalog-batch.py'
    (args.evidence/'compiler-engine.py').write_bytes(engine_path.read_bytes())
    spec=importlib.util.spec_from_file_location('lean_catalog_batch',engine_path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    context=pinned_recipe_admission_context(project_dir=args.workspace,verifier_sha256=sha(engine_path.read_bytes()))
    save(args.evidence/'toolchain.json',{'fingerprint':context.toolchain_fingerprint,'method':'actual-cli-batch-compilation'})
    items=json.loads((args.evidence/'inventory.json').read_text())['candidates']
    principal='pals.principal.v1/author/math-catalog-20261005'
    toolchain_id='math26.'+context.toolchain_fingerprint_sha256[:24]
    values=[]
    for card in items:
        manifest=RecipeAuthoringManifestV1.parse(canonical_json_bytes(dict(
            schema_version='pals.recipe-authoring-manifest.v1',recipe_id=card['id'],revision=1,
            kind='exact_target_proof',source_author_principal=principal,
            author_profile={'schema_version':'pals.recipe-author-profile.v1','source_author_principal':principal},
            toolchain={'toolchain_id':toolchain_id,'fingerprint':context.toolchain_fingerprint},
            imports=['Mathlib'],environment={'namespace':None,'opens':[]},
            target_source=card['target_source'],proof_body=card['proof_body'],
        )))
        source=RecipeMaterializerV1.materialize(manifest)
        validate_materialized_recipe(manifest,source)
        values.append(dict(card=card,toolchain=context.toolchain_fingerprint,
            manifest=json.loads(manifest.canonical_bytes),materialized_source_sha256=sha(source)))
    passed,failed=module.verify(values,workspace=args.workspace,evidence=args.evidence)
    save(args.evidence/'compiled.json',{'verified':passed,'failed':failed})
    print(json.dumps({'verified':len(passed),'failed':len(failed)}),flush=True)


def embed(args) -> None:
    import urllib.request
    env={}
    for line in args.secret_file.read_text().splitlines():
        if line.strip() and not line.lstrip().startswith('#') and '=' in line:
            k,v=line.split('=',1);env[k.strip()]=v.strip().strip('"').strip("'")
    key=env.get('PALS_OPENAI_API_KEY') or env.get('OPENAI_API_KEY')
    if not key:
        raise ValueError("existing embedding credential unavailable")
    values=json.loads((args.evidence/'compiled.json').read_text())['verified']
    rows=[v for v in values if v['card']['draft']]
    vectors={}
    for offset in range(0,len(rows),32):
        group=rows[offset:offset+32]
        texts=[f"pals-typed-catalog-embedding-v1\nprofile_id={v['card']['profile_id']}\ncanonical_openmath_xml={v['card']['draft']['openmath_xml']}" for v in group]
        body=json.dumps({'model':'text-embedding-3-small','dimensions':384,'input':texts}).encode()
        request=urllib.request.Request('https://api.openai.com/v1/embeddings',data=body,headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
        with urllib.request.urlopen(request,timeout=90) as response:
            payload=json.load(response)
        if payload.get('model')!='text-embedding-3-small' or len(payload['data'])!=len(group):
            raise ValueError('embedding binding mismatch')
        by_index={x['index']:x['embedding'] for x in payload['data']}
        if set(by_index)!=set(range(len(group))):
            raise ValueError('embedding indices mismatch')
        for i,v in enumerate(group):
            vector=by_index[i]
            if len(vector)!=384 or not any(vector) or not all(type(x) in (int,float) and math.isfinite(x) for x in vector):
                raise ValueError('embedding vector invalid')
            vectors[v['card']['id']]=vector
        print(json.dumps({'embedded':len(vectors),'total':len(rows)}),flush=True)
    save(args.evidence/'embeddings.json',{'binding':{'provider':'openai','model':'text-embedding-3-small','dimensions':384,'revision':'openai-release-2024-01-25'},'vectors':vectors})


def verified_records(args) -> list[dict]:
    """Rebind every inserted proof to the actual successful compiler artifacts."""
    from app.domain.recipe_catalog_admission import RecipeAuthoringManifestV1, RecipeMaterializerV1, canonical_json_bytes, validate_materialized_recipe

    records = json.loads((args.evidence / 'compiled.json').read_text())['verified']
    if not records or len({v['card']['id'] for v in records}) != len(records):
        raise ValueError('empty or duplicate successful proof inventory')
    engine_path = args.evidence / 'compiler-engine.py'
    if sha(engine_path.read_bytes()) != records[0]['toolchain']['verifier_sha256']:
        raise ValueError('the executed compiler engine changed')
    spec = importlib.util.spec_from_file_location('batch_evidence_check', engine_path)
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    receipt = json.loads((args.evidence / 'accepted-batch-receipt.json').read_text())
    source, _, _ = engine.build(records, negative_control=False)
    output = (args.evidence / 'accepted-batch.log').read_text()
    if (receipt['exit_code'] != 0 or receipt['negative_control'] is not False
            or receipt['rejected_card_ids']
            or receipt['checked_card_ids'] != [v['card']['id'] for v in records]
            or receipt['source_sha256'] != sha(source.encode())
            or (args.evidence / 'accepted-batch.lean').read_text() != source
            or receipt['output_sha256'] != sha(output.encode())
            or re.search(r':\d+:\d+: error(?:\([^)]*\))?:', output)):
        raise ValueError('successful compiler artifact binding mismatch')
    exploratory = json.loads((args.evidence / 'exploratory-batch-receipt.json').read_text())
    exploratory_source = (args.evidence / 'exploratory-batch.lean').read_text()
    exploratory_output = (args.evidence / 'exploratory-batch.log').read_text()
    control_line = exploratory_source.rstrip('\n').count('\n') + 1
    if (exploratory['negative_control'] is not True or exploratory['exit_code'] == 0
            or not exploratory_source.endswith('example : (1:ℕ)+1=3 := by decide\n')
            or exploratory['source_sha256'] != sha(exploratory_source.encode())
            or exploratory['output_sha256'] != sha(exploratory_output.encode())
            or not re.search(rf':{control_line}:\d+: error(?:\([^)]*\))?:', exploratory_output)):
        raise ValueError('false-statement rejection control evidence mismatch')
    receipt_sha = sha(json.dumps(receipt, sort_keys=True, separators=(',', ':')).encode())
    for value in records:
        card = value['card']
        manifest = RecipeAuthoringManifestV1.parse(canonical_json_bytes(value['manifest']))
        materialized = RecipeMaterializerV1.materialize(manifest)
        validate_materialized_recipe(manifest, materialized)
        name = 'catalog_' + card['id'].split('.')[-1]
        printed = re.search(re.escape("'" + name + "'") + r" (?:depends on axioms: \[([^\]]*)\]|does not depend on any axioms)", output)
        if printed is None:
            raise ValueError('missing kernel axiom audit')
        axioms = sorted(x.strip() for x in (printed.group(1) or '').split(',') if x.strip())
        expected_result = {
            'schema_version': 'pals.math-catalog-batch-result.v1',
            'verification_succeeded': True,
            'method': 'independent-anonymous-examples-before-named-audits',
            'batch_source_sha256': receipt['source_sha256'],
            'batch_receipt_sha256': receipt_sha,
            'batch_exit_code': 0, 'individual_cli_run': False, 'axioms': axioms,
        }
        if (value.get('success') is not True or not set(axioms) <= engine.ALLOWED_AXIOMS
                or value['axioms'] != axioms or value['compiler_result'] != expected_result
                or value['materialized_source_sha256'] != sha(materialized)
                or manifest.recipe_id != card['id']
                or manifest.target_source != card['target_source']
                or manifest.proof_body != card['proof_body']
                or value['toolchain']['verifier_sha256'] != sha(engine_path.read_bytes())
                or card['source_file_sha256'] != sha((args.root / card['source_path']).read_bytes())):
            raise ValueError('proof, provenance or compiler receipt changed after verification')
    return records


def apply_database(args) -> None:
    if not args.apply or not args.expected_system_identifier:
        raise ValueError('explicit --apply and expected DB identity are required')
    import psycopg
    from psycopg.types.json import Jsonb
    import rfc8785
    from app.domain.recipe_catalog_admission import RecipeAuthoringManifestV1, RecipeAdmissionVerifierVerifiedV1, RecipeAdmissionVerifierRequestV1
    from app.release.lean_recipe_catalog_admission import _insert_all, _lookup, _is_exact_admitted_replay
    from app.schemas.typed_catalog import TypedLayout, digest
    from app.release.natural_sketch_catalog_migration import _validate_artifacts, _is_exact
    records=verified_records(args)
    embeddings={} if args.recipes_only else json.loads((args.evidence/'embeddings.json').read_text())['vectors']
    groups={}
    for value in records:
        card=value['card']
        if card['draft'] and not args.recipes_only:
            groups.setdefault(card['profile_id'],[]).append(value)
    layouts=[]
    prepared_path=args.evidence/'prepared-layouts.json'
    prepared={}
    if groups and prepared_path.exists():
        prepared_layouts=[TypedLayout.model_validate(x) for x in json.loads(prepared_path.read_text())]
        prepared={x.binding.profile_id:x for x in prepared_layouts}
        if len(prepared)!=len(prepared_layouts) or set(prepared)!=set(groups):
            raise ValueError('prepared Draft generation set changed')
    for profile,values in groups.items():
        generation=prepared[profile].generation_id if profile in prepared else str(uuid4())
        rows=[{**v['card']['draft'],'embedding':embeddings[v['card']['id']]} for v in values]
        layout=TypedLayout.model_validate(dict(schema_version='pals.typed-catalog-layout.v1',generation_id=generation,binding=values[0]['card']['binding'],author_id='pals.math-catalog-20261005',source_manifest_sha256=sha(rfc8785.dumps([v['card'] for v in values])),coverage_families=[profile+'.verified-20261005'],rows=rows))
        if profile in prepared and layout.model_dump()!=prepared[profile].model_dump():
            raise ValueError('prepared immutable Draft content changed')
        layouts.append(layout)
    if layouts and not prepared:
        # Freeze real v4 identities before DB mutation so retries cannot duplicate rows.
        save(prepared_path,[x.model_dump() for x in layouts])
    with psycopg.connect(host=args.db_host,dbname='pals',user='postgres',password=args.secret_file.read_text().strip(),connect_timeout=10) as connection:
        connection.execute("SET LOCAL lock_timeout='10s'")
        connection.execute("SET LOCAL statement_timeout='120s'")
        observed=str(connection.execute('SELECT system_identifier FROM pg_control_system()').fetchone()[0])
        if observed!=args.expected_system_identifier:
            raise ValueError('wrong production DB identity')
        connection.execute("SELECT pg_advisory_xact_lock(hashtextextended('pals.verified-math-20261005',0))")
        with connection.cursor() as cursor:
            if not _is_exact(cursor,_validate_artifacts()):
                raise ValueError('sealed natural catalog differs before append')
        natural_before=connection.execute('SELECT count(*) FROM public.dsp_drafts').fetchone()[0]
        recipes_before=connection.execute('SELECT count(*) FROM pals_local_lean_recipe_catalog.recipe_revisions').fetchone()[0]
        typed_before=connection.execute('SELECT count(*) FROM pals_typed_catalog.rows').fetchone()[0]
        inserted=0
        connection.execute('SET LOCAL ROLE pals_api_recipe_catalog_owner')
        for value in records:
            manifest=RecipeAuthoringManifestV1.parse(rfc8785.dumps(value['manifest']))
            request=RecipeAdmissionVerifierRequestV1.for_manifest(manifest,admission_id=uuid4())
            verified=RecipeAdmissionVerifierVerifiedV1(admission_id=request.admission_id,materialized_source_sha256=value['materialized_source_sha256'],toolchain_fingerprint=rfc8785.dumps(value['toolchain']),toolchain_fingerprint_sha256=manifest.toolchain.sha256,compiler_command_sha256=value['compiler_command_sha256'],compiler_result=value['compiler_result'])
            verified.validate_against(request)
            existing=_lookup(connection,manifest.recipe_id,1)
            if existing:
                if (not _is_exact_admitted_replay(existing,manifest)
                        or existing.compiler_command_sha256!=value['compiler_command_sha256']
                        or existing.compiler_result_jcs.encode()!=rfc8785.dumps(value['compiler_result'])):
                    raise ValueError('existing Recipe conflict')
            else:
                _insert_all(connection,manifest,verified)
                inserted+=1
                existing=_lookup(connection,manifest.recipe_id,1)
                if (not _is_exact_admitted_replay(existing,manifest)
                        or existing.compiler_command_sha256!=value['compiler_command_sha256']
                        or existing.compiler_result_jcs.encode()!=rfc8785.dumps(value['compiler_result'])):
                    raise ValueError('Recipe read-back failed')
        connection.execute('RESET ROLE')
        connection.execute('SET LOCAL ROLE pals_typed_catalog_owner')
        typed_inserted=0
        for layout in layouts:
            review={'status':'compiled_and_axiom_audited_not_admitted','independent_review':'pending','activation':'not_requested_by_this_runner','evidence_sha256':sha((args.evidence/'compiled.json').read_bytes()),'compiler_verification':True,'allowed_axioms':['propext','Classical.choice','Quot.sound']}
            review['authoring_witnesses']={v['card']['draft']['id']:{'recipe_id':v['card']['id'],'recipe_revision':1,'materialized_source_sha256':v['materialized_source_sha256'],'semantic_alignment_review':'pending'} for v in groups[layout.binding.profile_id]}
            previous=connection.execute('SELECT layout_sha256,binding,row_count,review,signature,coverage_families FROM pals_typed_catalog.generations WHERE profile_id=%s AND generation_id=%s',(layout.binding.profile_id,layout.generation_id)).fetchone()
            expected=(digest(layout.model_dump()),layout.binding.model_dump(),len(layout.rows),review,'',layout.coverage_families)
            if previous is not None and previous != expected:
                raise ValueError('existing immutable Draft generation conflict')
            if previous is None:
                connection.execute('INSERT INTO pals_typed_catalog.generations(profile_id,generation_id,layout_sha256,binding,row_count,review,signature,coverage_families) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)',(layout.binding.profile_id,layout.generation_id,digest(layout.model_dump()),Jsonb(layout.binding.model_dump()),len(layout.rows),Jsonb(review),'',Jsonb(layout.coverage_families)))
            for row in layout.rows:
                if previous is None:
                    connection.execute('INSERT INTO pals_typed_catalog.rows VALUES(%s,%s,%s,%s,%s)',(layout.binding.profile_id,layout.generation_id,row.id,Jsonb(row.model_dump(exclude={'embedding'})),row.embedding))
                    typed_inserted+=1
                actual=connection.execute('SELECT payload,embedding FROM pals_typed_catalog.rows WHERE profile_id=%s AND generation_id=%s AND draft_id=%s',(layout.binding.profile_id,layout.generation_id,row.id)).fetchone()
                if actual!=(row.model_dump(exclude={'embedding'}),row.embedding):
                    raise ValueError('Draft read-back failed')
        connection.execute('RESET ROLE')
        with connection.cursor() as cursor:
            if not _is_exact(cursor,_validate_artifacts()):
                raise ValueError('sealed natural catalog differs after append')
        report={'database_identity_verified':True,'recipes_before':recipes_before,'recipes_inserted':inserted,'recipes_after':connection.execute('SELECT count(*) FROM pals_local_lean_recipe_catalog.recipe_revisions').fetchone()[0],'typed_before':typed_before,'typed_inserted':typed_inserted,'typed_after':connection.execute('SELECT count(*) FROM pals_typed_catalog.rows').fetchone()[0],'natural_before':natural_before,'natural_after':connection.execute('SELECT count(*) FROM public.dsp_drafts').fetchone()[0],'active_typed_profiles':connection.execute('SELECT count(*) FROM pals_typed_catalog.active').fetchone()[0],'draft_publication_status':'unsigned_inactive_pending_independent_review','generations':[{'profile_id':x.binding.profile_id,'generation_id':x.generation_id,'count':len(x.rows),'layout_sha256':digest(x.model_dump())} for x in layouts]}
    if args.recipes_only:
        report['draft_publication_status']='prepared_locally_pending_embedding_authorization'
        report['typed_drafts_prepared']=sum(bool(v['card']['draft']) for v in records)
        save(args.evidence/'database-recipes-receipt.json',report)
    save(args.evidence/'database-receipt.json',report)
    save(args.evidence/'layouts.json',[x.model_dump() for x in layouts])
    print(json.dumps(report),flush=True)


def audit_evidence(args) -> None:
    records=verified_records(args)
    print(json.dumps({'verified_proofs':len(records),'typed_drafts':sum(bool(v['card']['draft']) for v in records),'evidence_binding':'exact'}),flush=True)


def readback_database(args) -> None:
    """Verify committed content through a fresh read-only production transaction."""
    import psycopg
    import rfc8785
    from app.domain.recipe_catalog_admission import RecipeAuthoringManifestV1
    from app.release.lean_recipe_catalog_admission import _lookup, _is_exact_admitted_replay
    from app.release.natural_sketch_catalog_migration import _validate_artifacts, _is_exact
    from app.schemas.typed_catalog import TypedLayout, digest

    if not args.expected_system_identifier:
        raise ValueError('expected DB identity is required')
    records=verified_records(args)
    layouts=[TypedLayout.model_validate(x) for x in json.loads((args.evidence/'layouts.json').read_text())]
    with psycopg.connect(host=args.db_host,dbname='pals',user='postgres',password=args.secret_file.read_text().strip(),connect_timeout=10) as connection:
        connection.execute('SET TRANSACTION READ ONLY')
        if str(connection.execute('SELECT system_identifier FROM pg_control_system()').fetchone()[0])!=args.expected_system_identifier:
            raise ValueError('wrong production DB identity')
        for value in records:
            manifest=RecipeAuthoringManifestV1.parse(rfc8785.dumps(value['manifest']))
            existing=_lookup(connection,manifest.recipe_id,1)
            if (existing is None or not _is_exact_admitted_replay(existing,manifest)
                    or existing.compiler_command_sha256!=value['compiler_command_sha256']
                    or existing.compiler_result_jcs.encode()!=rfc8785.dumps(value['compiler_result'])):
                raise ValueError('committed Recipe differs from verified manifest')
        drafts=0
        for layout in layouts:
            generation=connection.execute('SELECT layout_sha256,binding,row_count FROM pals_typed_catalog.generations WHERE profile_id=%s AND generation_id=%s',(layout.binding.profile_id,layout.generation_id)).fetchone()
            if generation!=(digest(layout.model_dump()),layout.binding.model_dump(),len(layout.rows)):
                raise ValueError('committed Draft generation differs from prepared layout')
            for row in layout.rows:
                actual=connection.execute('SELECT payload,embedding FROM pals_typed_catalog.rows WHERE profile_id=%s AND generation_id=%s AND draft_id=%s',(layout.binding.profile_id,layout.generation_id,row.id)).fetchone()
                if actual!=(row.model_dump(exclude={'embedding'}),row.embedding):
                    raise ValueError('committed Draft differs from prepared layout')
                drafts+=1
        if not _is_exact(connection.cursor(),_validate_artifacts()):
            raise ValueError('sealed natural catalog changed')
        report={'transaction':'read_only','database_identity_verified':True,'exact_recipes_read_back':len(records),'exact_typed_drafts_read_back':drafts,'sealed_natural_catalog_exact':True,'natural_count':connection.execute('SELECT count(*) FROM public.dsp_drafts').fetchone()[0]}
    save(args.evidence/'database-readback.json',report)
    print(json.dumps(report),flush=True)


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['inventory','compile','audit','embed','apply','readback'])
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--evidence',type=Path,required=True)
    parser.add_argument('--workspace',type=Path,default=Path('/app/lean-workspace'))
    parser.add_argument('--secret-file',type=Path)
    parser.add_argument('--db-host')
    parser.add_argument('--expected-system-identifier')
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--recipes-only',action='store_true',help='append verified Lean only, without an external embedding dependency')
    args=parser.parse_args()
    args.evidence.mkdir(parents=True,exist_ok=True)
    sys.path[:0]=[str(args.root/'pals-api'),str(args.root/'pals-agent')]
    {'inventory':inventory,'compile':compile_candidates,'audit':audit_evidence,'embed':embed,'apply':apply_database,'readback':readback_database}[args.operation](args)


if __name__=='__main__':
    main()
