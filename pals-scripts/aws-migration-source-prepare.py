#!/usr/bin/env python3
"""Mini preparation only: never final capture, drain, stop or maintenance changes.

Default performs the SDK read-only probe, public inventory upload, fixed tool load
and real native/container lock probe. --apply-runtime-secrets explicitly reconciles
then creates only missing authorized SecureStrings. --smoke is a separate opt-in.
Every child owns its existing lock. No retries, journal deletion or service restart.
--inspect-lock-owner-only runs only public file/lsof/ps inspection and report upload.
"""
import base64
import importlib.util
import json
import os
import re
import shlex
import sys
import time
from datetime import datetime
from pathlib import Path
from uuid import uuid4

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parent


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS/filename)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


try:
    L = module('preparation_loader', 'aws-migration-source-load-tool.py')
    R = module('preparation_secrets', 'aws-migration-source-runtime-secrets.py')
except BaseException:  # noqa: BLE001 -- bootstrap errors must not dump diagnostics
    print('{"status":"source_preparation_failed_closed","code":"helper_bootstrap_failed"}',file=sys.stderr)
    sys.exit(2)
B = L.b
MANIFEST = '256065f70ab6b6d383ba9953b68c0c81e0ed2f44ce4db1e7cb0844adff79eda5'
PINS = {'watchdog':'3b4ed85f09aed5212e0e7b352e83ecd7990ad34ea517b7766f3060020b70f23f',
        'controller':'b2855d4bff4ab850206dd2c35b1f1495c06a8e188d288d915816efe9b946d159'}
FILES = {'secrets':'aws-migration-source-runtime-secrets.py', 'inventory':'aws-migration-source-inventory.py',
         'loader':'aws-migration-source-load-tool.py', 'final':'aws-migration-source-final.py'}


def safe_diagnostic(raw):
    try:
        value = B.document(raw)
    except (ValueError, B.Refusal):
        return {'code':'child_output_unclassified'}
    allowed = R.SAFE_FAILURE_CODES | R.AWS_ERROR_CODES | {
        'unclassified','multiple_known_codes','source_lock_busy','required_path_absent','permission_denied',
        'required_field_absent','invalid_json','unexpected_failure','runtime_secret_transfer_failed',
        'tool_load_failed_closed','source_final_failed_closed','source_inventory_failed','read_only_inventory_failed',
        'inventory_command_failed','public_configuration_invalid','ssm_transfer','ssm_reconciliation','source_preflight',
        'sdk_transport_probe','sdk_import','sdk_config','sdk_construction','input_validation','aws_identity',
        'ssm_metadata','ssm_put','controller_read','source_lock','aws_cli_config','metadata_download',
        'metadata_validation','existing_image','archive_download','archive_contract','image_load',
        'loaded_image_validation','receipt_write','source_final_operation','final_maintenance_prerequisite',
        'native_container_lock_domain_not_proven','docker','aws'}
    result = {}
    for key in ('status','code','reason','phase','stage','program','sdk_stage','aws_error_code'):
        item = value.get(key)
        if isinstance(item,str) and item in allowed:
            result[key] = item
    for key in ('exit_code','aws_exit_code','stdout_bytes','stderr_bytes'):
        item=value.get(key)
        if type(item) is int and 0<=item<=B.MAX_METADATA+65536:
            result[key]=item
    for key in ('stdin_device_unavailable','parameter_file_error'):
        if type(value.get(key)) is bool:
            result[key]=value[key]
    return result or {'code':'child_output_unclassified'}


def child(role, arguments, timeout=450):
    code,out,err=B.run([sys.executable,'-B',str(SCRIPTS/FILES[role]),*arguments],
                       timeout=timeout,accepted=(0,1,2))
    if code:
        failure=B.Refusal('child_failed')
        failure.diagnostic=safe_diagnostic(err or out)
        raise failure
    return out


def holders(state):
    code,out,_err=B.run(['/usr/sbin/lsof','-n','-P','-Fpcfl','--',str(state/'host-update.lock'),
                        str(state/'deploy.lock')],timeout=5,accepted=(0,1))
    result=[];pid=None;command=None
    for line in out.decode('ascii',errors='replace').splitlines():
        if re.fullmatch(r'p[0-9]{1,10}',line):pid=int(line[1:]);command=None
        elif re.fullmatch(r'c[A-Za-z0-9_.+-]{1,32}',line):command=line[1:]
        elif pid and command and re.fullmatch(r'f[0-9]{1,6}[rwu]?',line):
            result.append({'command':command,'pid':pid,'fd':line[1:]})
    B.require(code in (0,1) and len(result)<=64)
    return result


def process_metadata(pid):
    code,out,_err=B.run(['/bin/ps','-p',str(pid),'-o','pid=,ppid=,uid=,lstart=,etime=,pcpu=,stat=,comm='],
                       timeout=5,accepted=(0,1))
    if code:return None
    values=out.decode('ascii').strip().split(None,11)
    B.require(len(values)==12 and all(re.fullmatch(r'[0-9]{1,10}',value) for value in values[:3]))
    B.require(int(values[0])==pid and re.fullmatch(r'[0-9:-]{1,20}',values[8])
              and re.fullmatch(r'[0-9]{1,4}(?:\.[0-9]{1,2})?',values[9])
              and re.fullmatch(r'[A-Za-z+<>-]{1,16}',values[10]))
    started=datetime.strptime(' '.join(values[3:8]),'%a %b %d %H:%M:%S %Y').isoformat()  # noqa: DTZ007 -- ps reports local time, explicitly labeled below
    comm=Path(values[11]).name
    return {'pid':pid,'ppid':int(values[1]),'uid':int(values[2]),'started_local':started,
            'elapsed':values[8],'cpu_percent':float(values[9]),'state':values[10],
            'comm':comm if re.fullmatch(r'[A-Za-z0-9_.+-]{1,64}',comm) else 'unclassified'}


def classify_command(raw,root):
    # Inspect only the executable/script position; a string occurring in -c or
    # another argument cannot impersonate an allowlisted installed script.
    try:
        tokens=shlex.split(raw.decode())
        if not tokens:return 'unknown'
        index=0
        if re.fullmatch(r'(?:Python|python(?:[0-9]+(?:\.[0-9]+)*)?)',Path(tokens[0]).name):
            index=1
            while index<len(tokens) and tokens[index] in {'-I','-B','-u','-s','-S','-E'}:index+=1
        if index>=len(tokens) or tokens[index].startswith('-'):return 'unknown'
        selected=Path(tokens[index]).resolve(strict=True)
        known={root/'controller.py':'host_controller',root/'auto-recovery/auto_recovery.py':'auto_recovery',
               SCRIPTS/'aws-migration-source-prepare.py':'source_preparation',
               **{SCRIPTS/filename:'source_'+name for name,filename in FILES.items()}}
        return known.get(selected,'unknown')
    except (OSError,ValueError):return 'unknown'


def inspect_lock_owners(root,report):
    report['stage']='lock_owner_inspection'
    inspection=L.public_inspection(root);report['public_controller_inspection']=inspection
    B.require(all(inspection['files'][name].get('sha256')==pin for name,pin in PINS.items()),
              'installed_controller_baseline_changed')
    policy,_current,_docker,binding=B.controller(root);state=Path(policy['state_dir'])
    report['source_baseline']={name:B.sha(raw) for name,raw in zip(('policy_sha256','current_sha256','config_sha256'),binding)}
    def inodes():return [(path.stat().st_dev,path.stat().st_ino) for path in
                         (state/'host-update.lock',state/'deploy.lock')]
    initial_inodes=inodes();initial=holders(state);observed=[]
    for pid in sorted({item['pid'] for item in initial}):
        try:
            first=process_metadata(pid)
            code,command,_err=B.run(['/bin/ps','-p',str(pid),'-o','command='],timeout=5,accepted=(0,1))
            classification=classify_command(command,root) if code==0 else 'unknown'
            del command  # Raw arguments are never part of report/file/stdout.
            last=process_metadata(pid)
            stable=first is not None and last is not None and all(first[key]==last[key]
                     for key in ('pid','ppid','uid','started_local','comm'))
            observed.append({**(last or {'pid':pid}),'identity_stable':stable,
                             'script_classification':classification if stable else 'process_changed_or_exited'})
        except (OSError,ValueError,B.Refusal):
            observed.append({'pid':pid,'identity_stable':False,'script_classification':'metadata_unavailable'})
    final=holders(state);inode_stable=initial_inodes==inodes()
    for item in observed:
        before=sorted(value['fd'] for value in initial if value['pid']==item['pid'])
        after=sorted(value['fd'] for value in final if value['pid']==item['pid'])
        if not inode_stable or before!=after or not after:
            item.update(identity_stable=False,script_classification='process_changed_or_exited')
        item['lock_fds_observed']=after
    report.update(status='lock_owner_inspection_complete',lock_holders=final,lock_owner_processes=observed,
                  lock_inode_snapshot_stable=inode_stable,stage='complete')


def baseline(root,report):
    inspection=L.public_inspection(root)
    report['public_controller_inspection']=inspection
    B.require(all(inspection['files'][name].get('sha256')==pin for name,pin in PINS.items()),
              'installed_controller_baseline_changed')
    policy,_current,_docker,binding=B.controller(root)
    report['source_baseline']={name:B.sha(raw) for name,raw in zip(('policy_sha256','current_sha256','config_sha256'),binding)}
    state=Path(policy['state_dir'])
    try:
        with B.existing_lock(state/'host-update.lock'):
            pass
    except BlockingIOError:
        try:report['lock_holders']=holders(state)
        except (OSError,ValueError,B.Refusal):report['lock_holders']=[]
        raise B.Refusal('source_lock_busy') from None


def sequence(args,root,report):
    def step(name,role,arguments):
        report['stage']=name
        raw=child(role,arguments)
        report['successful_child_stages'].append(name)
        return raw
    report['stage']='controller_preflight';baseline(root,report)
    sdk=B.document(step('sdk_read_only_probe','secrets',['--probe-sdk-transport']))
    B.require(sdk=={'status':'sdk_probe_verified','account_verified':True,'endpoint_verified':True,
                   'metadata_read_verified':True,'service_write_attempted':False})
    report['sdk_probe_verified']=True
    if args.apply_runtime_secrets:
        result=B.document(step('runtime_secrets_reconcile','secrets',['--reconcile']))
        B.require(set(result)=={'status','verified_parameter_count','admission_eligible'}
                  and result['admission_eligible'] is False and type(result['verified_parameter_count']) is int
                  and 0<=result['verified_parameter_count']<=5)
        if result['status']=='reconciled_absent' and result['verified_parameter_count']<5:
            result=B.document(step('runtime_secrets_apply','secrets',['--apply']))
        B.require(result=={'status':'verified','verified_parameter_count':5,'admission_eligible':False})
        report['verified_runtime_parameter_count']=5
    raw=step('public_inventory_upload','inventory',['upload-inventory'])
    lines=raw.decode('ascii').splitlines()
    B.require(len(lines)==3 and lines[0]=='Inventory uploaded to existing private backup bucket.')
    match=re.fullmatch(r'Key: (aws-migration-20261030/source-inventory/inventory-([0-9a-f]{64})\.json)',lines[1])
    B.require(match and lines[2]=='SHA256: '+match[2])
    report['inventory']={'key':match[1],'sha256':match[2]}
    loaded=B.document(step('fixed_tool_load','loader',['--manifest-sha256',MANIFEST,'--apply']))
    B.require(set(loaded)=={'source_docker_image_id','admission_eligible'} and loaded['admission_eligible'] is False
              and isinstance(loaded['source_docker_image_id'],str) and B.IMAGE.fullmatch(loaded['source_docker_image_id']))
    report['source_tool_docker_image_id']=loaded['source_docker_image_id']
    common=['--tool-image',loaded['source_docker_image_id'],'--tool-api-commit',L.COMMIT]
    observed=B.document(step('native_container_lock_probe','final',common+['--probe-lock-propagation']))
    B.require(observed=={'status':'native_container_lock_exclusion_observed','admission_eligible':False})
    if args.smoke:
        observed=B.document(step('unsigned_smoke_capture','final',common+['--smoke']))
        B.require(set(observed)=={'status','session','admission_eligible'} and observed['status']=='smoke_uploaded_not_admissible'
                  and observed['admission_eligible'] is False and re.fullmatch(r'[0-9a-f]{32}',observed['session']))
        report['smoke_session']=observed['session']
    final={};baseline(root,final)
    B.require(final['source_baseline']==report['source_baseline'],'controller_changed')
    report['status']='prepared_not_admitted';report['stage']='complete'


def upload_reports(directory,report):
    prefix='aws-migration-20261030/source-preparation/'+directory.name+'/'
    inspection=report.pop('public_controller_inspection',{})
    report['controller_inspection_sha256']=B.sha(B.encoded(inspection))
    artifacts=[('controller-inspection.json',B.encoded(inspection)),('summary.json',B.encoded(report))]
    for name,raw in artifacts:B.write(directory/name,raw)
    B.require(B.cli('sts','get-caller-identity')['Account']==B.ACCOUNT)
    result={}
    for name,raw in artifacts:
        path=directory/name
        digest=B.sha(raw);checksum=base64.b64encode(bytes.fromhex(digest)).decode();key=prefix+name
        response=B.cli('s3api','put-object',{'Bucket':B.BUCKET,'ExpectedBucketOwner':B.ACCOUNT,'Key':key,
                       'ServerSideEncryption':'AES256','Metadata':{'sha256':digest},'ChecksumSHA256':checksum},['--body',str(path)])
        version=response.get('VersionId');B.require(isinstance(version,str) and version not in ('','null'))
        head=B.cli('s3api','head-object',{'Bucket':B.BUCKET,'ExpectedBucketOwner':B.ACCOUNT,'Key':key,
                   'VersionId':version,'ChecksumMode':'ENABLED'})
        B.require(head.get('VersionId')==version and head['ContentLength']==len(raw) and head['Metadata'].get('sha256')==digest
                  and head['ServerSideEncryption']=='AES256' and head['ChecksumSHA256']==checksum)
        result[name]={'key':key,'version_id':version,'sha256':digest}
    B.write(directory/'upload-receipt.json',B.encoded(result))
    return result


def main(arguments=None):
    B.DEADLINE=time.monotonic()+1200
    parser=B.Parser(description=__doc__)
    parser.add_argument('--apply-runtime-secrets',action='store_true')
    parser.add_argument('--smoke',action='store_true')
    parser.add_argument('--inspect-lock-owner-only',action='store_true')
    args=parser.parse_args(arguments)
    B.require(not args.inspect_lock_owner_only or not (args.apply_runtime_secrets or args.smoke),'invalid_arguments')
    root=Path.home()/'pals-mini-deploy';parent=root/'aws-migration-20261030/source-preparation'
    for path in (parent.parent,parent):
        if not path.exists():path.mkdir(mode=0o700)
        B.require(path.resolve(strict=True)==path and path.is_dir() and path.stat().st_uid==os.geteuid()
                  and path.stat().st_mode&0o777==0o700)
    directory=parent/uuid4().hex;directory.mkdir(mode=0o700)
    report={'schema_version':'pals.source-preparation.v1','status':'failed_closed','stage':'initialization',
            'session':directory.name,'successful_child_stages':[],'admission_eligible':False,'source_stop_performed':False,
            'final_signing_performed':False,'runtime_secret_transfer_requested':args.apply_runtime_secrets,
            'helper_sha256':{name:B.sha(B.private(SCRIPTS/filename,private_mode=False))
                             for name,filename in (FILES|{'prepare':Path(__file__).name}).items()}}
    try:
        if args.inspect_lock_owner_only:inspect_lock_owners(root,report)
        else:sequence(args,root,report)
    except (OSError,ValueError,KeyError,TypeError,B.Refusal,KeyboardInterrupt) as error:
        report['failure']=getattr(error,'diagnostic',{'code':'preparation_guard_rejected'})
        if isinstance(error,BlockingIOError):report['failure']={'code':'source_lock_busy'}
        if isinstance(error,KeyboardInterrupt):report['failure']={'code':'operator_interrupted'}
        if isinstance(error,B.Refusal) and len(error.args)==1 and error.args[0] in R.SAFE_FAILURE_CODES | {
                'installed_controller_baseline_changed','source_lock_busy','controller_changed'}:
            report['failure']={'code':error.args[0]}
        if report['failure'].get('code')=='source_lock_busy' and report.get('public_controller_inspection',{}).get('locks'):
            try:
                state=Path(report['public_controller_inspection']['locks']['host-update.lock']['path']).parent
                report['lock_holders']=holders(state)
            except (OSError,ValueError,KeyError,B.Refusal):
                report['lock_holders']=[]
    B.write(directory/'aggregate-private.json',B.encoded(report))
    B.DEADLINE=time.monotonic()+180  # Reporting must survive an exhausted preparation budget.
    try:
        receipts=upload_reports(directory,report)
    except (OSError,ValueError,KeyError,TypeError,B.Refusal):
        expired=report.get('failure',{}).get('aws_error_code') in {'ExpiredTokenException','UnrecognizedClientException'}
        print(json.dumps({'status':'source_preparation_failed_closed','stage':report['stage'],
                          'code':'operator_authentication_required' if expired else 'report_upload_failed','session':directory.name,
                          'failure':report.get('failure',{}),'action':'check_existing_operator_sso_and_protected_receipt'},sort_keys=True))
        return 2
    print(json.dumps({'status':report['status'],'stage':report['stage'],'reports':receipts,'admission_eligible':False},sort_keys=True))
    return 0 if report['status'] in {'prepared_not_admitted','lock_owner_inspection_complete'} else 2


if __name__=='__main__':
    try:sys.exit(main())
    except SystemExit:raise
    except BaseException:  # noqa: BLE001 -- no raw child output/exception disclosure
        print('{"status":"source_preparation_failed_closed","code":"report_or_preflight_failed","action":"inspect_protected_source_preparation_receipt"}',file=sys.stderr)
        sys.exit(2)
