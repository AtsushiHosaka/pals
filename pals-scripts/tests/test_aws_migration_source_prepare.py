"""Preparation orchestration only; no AWS, Docker, source capture or secret reads."""
import ast
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import nullcontext, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

FILE=Path(__file__).resolve().parents[1]/'aws-migration-source-prepare.py'
SPEC=importlib.util.spec_from_file_location('source_prepare',FILE)
m=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(m)
SECRET='synthetic-private-token-never-print'


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.calls=[];self.reconciled='reconciled_absent';self.fail=None
        self.report={'status':'failed_closed','successful_child_stages':[]}

    def baseline(self,_root,report):
        report['source_baseline']={'policy_sha256':'a'*64}
        report['public_controller_inspection']={'status':'public'}

    def child(self,role,args):
        self.calls.append((role,args))
        if self.fail and self.fail in args:raise m.B.Refusal('child_failed')
        if role=='secrets':
            self.assertEqual(args[1:],['--sdk-tool-image','sha256:'+'b'*64,'--sdk-tool-api-commit',m.L.COMMIT])
            if args[0]=='--probe-sdk-transport':
                value={'status':'sdk_probe_verified','account_verified':True,'endpoint_verified':True,
                       'metadata_read_verified':True,'service_write_attempted':False}
            else:
                verified=args[0]=='--apply' or self.reconciled=='verified'
                value={'status':'verified' if verified else 'reconciled_absent',
                       'verified_parameter_count':5 if verified else 2,'admission_eligible':False}
        elif role=='inventory':
            return ('Inventory uploaded to existing private backup bucket.\nKey: aws-migration-20261030/source-inventory/inventory-'+
                    'a'*64+'.json\nSHA256: '+'a'*64+'\n').encode()
        elif role=='loader':value={'source_docker_image_id':'sha256:'+'b'*64,'admission_eligible':False}
        elif '--probe-lock-propagation' in args:
            value={'status':'independent_native_guest_lock_domains_observed','admission_eligible':False}
        else:value={'status':'smoke_uploaded_not_admissible','session':'c'*32,'admission_eligible':False}
        return json.dumps(value).encode()

    def sequence(self,apply=True,smoke=False):
        with patch.object(m,'baseline',side_effect=self.baseline),patch.object(m,'child',side_effect=self.child):
            m.sequence(SimpleNamespace(apply_runtime_secrets=apply,smoke=smoke),Path('/source'),self.report)

    def test_order_reconcile_before_apply_load_then_actual_lock_probe_never_final(self):
        self.sequence()
        self.assertEqual([args[:1] for role,args in self.calls if role=='secrets'],
                         [['--probe-sdk-transport'],['--reconcile'],['--apply']])
        self.assertEqual([role for role,_ in self.calls],['inventory','loader','secrets','secrets','secrets','final'])
        final=self.calls[-1][1]
        self.assertEqual(final,['--tool-image','sha256:'+'b'*64,'--tool-api-commit',m.L.COMMIT,'--host-native-locks','--probe-lock-propagation'])
        self.assertEqual(self.report['status'],'prepared_not_admitted')
        for forbidden in ('--final','--refresh-fence','--confirm-source-manifest','stop','kill'):
            self.assertFalse(any(forbidden in args for _,args in self.calls))

    def test_already_verified_skips_put_and_default_has_no_secret_transfer(self):
        self.reconciled='verified';self.sequence()
        self.assertFalse(any('--apply' in args for role,args in self.calls if role=='secrets'))
        self.calls.clear();self.sequence(apply=False)
        self.assertEqual([args[:1] for role,args in self.calls if role=='secrets'],[['--probe-sdk-transport']])

    def test_failure_stops_without_retry_or_later_actions(self):
        for flag in ('--probe-sdk-transport','--reconcile','--apply','--probe-lock-propagation'):
            self.calls.clear();self.fail=flag
            with self.assertRaises(m.B.Refusal):self.sequence(smoke=True)
            self.assertEqual(sum(flag in args for _,args in self.calls),1)
            self.assertFalse(any('--smoke' in args for _,args in self.calls))

    def test_optional_smoke_follows_successful_lock_probe(self):
        self.sequence(smoke=True)
        self.assertIn('--probe-lock-propagation',self.calls[-2][1]);self.assertIn('--smoke',self.calls[-1][1])
        self.assertEqual(self.report['smoke_session'],'c'*32)

    def test_untrusted_diagnostics_never_echo_arbitrary_fields_or_values(self):
        raw=json.dumps({'status':'runtime_secret_transfer_failed','code':'write_outcome_unverified',
                        'sdk_stage':'ssm_put','aws_error_code':'AccessDeniedException','Value':SECRET,
                        'phase':SECRET,'stderr':SECRET,'stdout_bytes':4,'stderr_bytes':10}).encode()
        safe=m.safe_diagnostic(raw)
        self.assertNotIn(SECRET,json.dumps(safe));self.assertNotIn('Value',safe)
        self.assertEqual(safe['aws_error_code'],'AccessDeniedException')

    def test_final_recheck_diagnostics_survive_exact_closed_filter(self):
        value={'status':'source_final_failed_closed','reason':'source_container_changed',
               'stage':'recheck_container_identity','phase':'source_final_operation','failed_check_line':482,
               'changed_fields':[{'container':m.B.DATABASE,'fields':['Mounts','Config']}], 'Env':SECRET}
        safe=m.safe_diagnostic(json.dumps(value).encode())
        self.assertEqual(safe,{key:item for key,item in value.items() if key!='Env'})
        control={'reason':'controller_changed','stage':'recheck_controller_binding',
                 'controller_changed_fields':['policy','current','config']}
        self.assertEqual(m.safe_diagnostic(json.dumps(control).encode()),control)

    def test_failed_check_line_is_strict_bounded_integer(self):
        for line in (True,False,0,-1,20001,1.5,'482',None):
            with self.subTest(line=line):
                self.assertNotIn('failed_check_line',m.safe_diagnostic(json.dumps({'failed_check_line':line}).encode()))
        for line in (1,20000):
            self.assertEqual(m.safe_diagnostic(json.dumps({'failed_check_line':line}).encode())['failed_check_line'],line)

    def test_tool_diagnostic_keeps_only_closed_names_and_bounded_location(self):
        value={'tool_module':'cloud_restore_preflight','tool_error':'FileNotFoundError',
               'tool_line':92,'exception_message':SECRET,'sql':SECRET}
        safe=m.safe_diagnostic(json.dumps(value).encode())
        self.assertEqual(safe,{key:item for key,item in value.items() if key.startswith('tool_')})
        self.assertNotIn(SECRET,json.dumps(safe))
        for field,item in [('tool_module',SECRET),('tool_error',SECRET),('tool_line',True),
                           ('tool_line',0),('tool_line',20001)]:
            bad={**value,field:item};filtered=m.safe_diagnostic(json.dumps(bad).encode())
            self.assertNotIn(field,filtered);self.assertNotIn(SECRET,json.dumps(filtered))

    def test_changed_fields_reject_unknown_names_values_duplicates_and_extra_keys(self):
        known={'container':m.B.DATABASE,'fields':['Config']}
        invalid=[[],[{'container':SECRET,'fields':['Config']}],
                 [{'container':m.B.DATABASE,'fields':['Env',SECRET]}],
                 [{'container':m.B.DATABASE,'fields':['Config','Config']}],
                 [{'container':m.B.DATABASE,'fields':['Config'],'value':SECRET}],
                 [{'container':m.B.DATABASE,'fields':[['Config']]}],[known,known]]
        for changes in invalid:
            safe=m.safe_diagnostic(json.dumps({'reason':'source_container_changed','changed_fields':changes}).encode())
            self.assertNotIn('changed_fields',safe);self.assertNotIn(SECRET,json.dumps(safe))
        for changes in ([],['current','current'],['current',SECRET],[['current']],['Env']):
            safe=m.safe_diagnostic(json.dumps({'reason':'controller_changed','controller_changed_fields':changes}).encode())
            self.assertNotIn('controller_changed_fields',safe);self.assertNotIn(SECRET,json.dumps(safe))

    def test_lsof_returns_only_command_pid_fd_without_paths_or_argv(self):
        raw=b'p123\ncPython\nf5\nlW\nn/private/secret-path\n'+SECRET.encode()+b'\n'
        with patch.object(m.B,'run',return_value=(0,raw,b'')) as call:
            result=m.holders(Path('/source/state'))
        self.assertEqual(result,[{'command':'Python','pid':123,'fd':'5'}])
        self.assertNotIn(SECRET,json.dumps(result));self.assertNotIn('secret-path',json.dumps(result))
        self.assertEqual(call.call_args.args[0][3],'-Fpcfl')

    def test_busy_baseline_is_reported_even_if_lsof_is_unavailable(self):
        inspection={'files':{name:{'sha256':pin} for name,pin in m.PINS.items()}}
        controller=({'state_dir':'/source/state'},None,None,(b'policy',b'current',b'config'))
        report={}
        with patch.object(m.L,'public_inspection',return_value=inspection),patch.object(m.B,'controller',return_value=controller), \
             patch.object(m.B,'existing_lock',side_effect=BlockingIOError),patch.object(m,'holders',side_effect=OSError), \
             self.assertRaisesRegex(m.B.Refusal,'source_lock_busy'):
            m.baseline(Path('/source'),report)
        self.assertEqual(report['lock_holders'],[])

    def test_process_metadata_closed_public_fields(self):
        raw=b'29456 1 501 Sat Oct 31 13:48:01 2026 01:00 0.0 Ss /usr/bin/Python\n'
        with patch.object(m.B,'run',return_value=(0,raw,b'')) as call:
            value=m.process_metadata(29456)
        self.assertEqual(value,{'pid':29456,'ppid':1,'uid':501,'started_local':'2026-10-31T13:48:01',
                               'elapsed':'01:00','cpu_percent':0.0,'state':'Ss','comm':'Python'})
        self.assertNotIn('command=',repr(call.call_args.args[0]))

    def test_script_classification_uses_actual_script_position_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();(root/'controller.py').write_text('# fixture')
            known=str(root/'controller.py')
            self.assertEqual(m.classify_command(('python3 -I -B '+known+' '+SECRET).encode(),root),'host_controller')
            for raw in ('python3 -c '+repr(known)+' '+SECRET,'/bin/echo '+known,'python3 /foreign/controller.py'):
                self.assertEqual(m.classify_command(raw.encode(),root),'unknown')

    def test_lock_owner_snapshot_rechecks_start_identity_fd_and_inode(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();state=root/'state';state.mkdir(mode=0o700)
            (root/'controller.py').write_text('# fixture')
            for name in ('host-update.lock','deploy.lock'):m.B.write(state/name,b'')
            inspection={'files':{name:{'sha256':pin} for name,pin in m.PINS.items()}}
            controller=({'state_dir':str(state)},None,None,(b'policy',b'current',b'config'))
            fds=[{'pid':29456,'command':'Python','fd':fd} for fd in ('4','5')]
            before={'pid':29456,'ppid':1,'uid':501,'started_local':'2026-10-31T13:48:01',
                    'elapsed':'01:00','cpu_percent':0.0,'state':'Ss','comm':'Python'}
            for changed in (False,True):
                after={**before,'started_local':'2026-10-31T13:49:01'} if changed else dict(before)
                report={}
                with patch.object(m.L,'public_inspection',return_value=inspection),patch.object(m.B,'controller',return_value=controller), \
                     patch.object(m,'holders',side_effect=[fds,fds]),patch.object(m,'process_metadata',side_effect=[before,after]), \
                     patch.object(m.B,'run',return_value=(0,('python3 '+str(root/'controller.py')+' '+SECRET).encode(),b'')):
                    m.inspect_lock_owners(root,report)
                self.assertNotIn(SECRET,json.dumps(report))
                observed=report['lock_owner_processes'][0]
                self.assertEqual(observed['identity_stable'],not changed)
                self.assertEqual(observed['script_classification'],'process_changed_or_exited' if changed else 'host_controller')
            report={}
            def replacement(_pid):
                fresh=state/'fresh';m.B.write(fresh,b'');os.replace(fresh,state/'deploy.lock')
                return dict(before)
            with patch.object(m.L,'public_inspection',return_value=inspection),patch.object(m.B,'controller',return_value=controller), \
                 patch.object(m,'holders',side_effect=[fds,fds]),patch.object(m,'process_metadata',side_effect=replacement), \
                 patch.object(m.B,'run',return_value=(0,b'python3 -c public',b'')):
                m.inspect_lock_owners(root,report)
            self.assertFalse(report['lock_inode_snapshot_stable'])
            self.assertFalse(report['lock_owner_processes'][0]['identity_stable'])

    def test_reports_are_private_versioned_checksummed_and_summary_binds_inspection(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary).resolve();stored={};calls=[]
            def aws(service,operation,payload=None,extra=()):
                calls.append((service,operation,payload))
                if service=='sts':return {'Account':m.B.ACCOUNT}
                self.assertEqual(payload['ExpectedBucketOwner'],m.B.ACCOUNT)
                if operation=='put-object':
                    raw=Path(extra[1]).read_bytes()
                    stored[payload['Key']]={'VersionId':'fixed-version','ContentLength':len(raw),'Metadata':payload['Metadata'],
                                           'ServerSideEncryption':'AES256','ChecksumSHA256':payload['ChecksumSHA256']}
                    return {'VersionId':'fixed-version'}
                self.assertEqual(payload['VersionId'],'fixed-version');return stored[payload['Key']]
            report={'status':'failed_closed','public_controller_inspection':{'status':'public'}}
            with patch.object(m.B,'cli',side_effect=aws):receipts=m.upload_reports(directory,report)
            self.assertEqual(set(receipts),{'controller-inspection.json','summary.json'})
            for filename in ('controller-inspection.json','summary.json','upload-receipt.json'):
                self.assertEqual((directory/filename).stat().st_mode&0o777,0o600)
            summary=json.loads((directory/'summary.json').read_bytes())
            self.assertEqual(summary['controller_inspection_sha256'],m.B.sha((directory/'controller-inspection.json').read_bytes()))
            self.assertEqual([operation for _,operation,_ in calls],
                             ['get-caller-identity','put-object','head-object','put-object','head-object'])

    def test_python39_syntax_and_invalid_cli_privacy(self):
        ast.parse(FILE.read_text(),feature_version=(3,9))
        result=subprocess.run([sys.executable,'-B',str(FILE),'--'+SECRET],capture_output=True,timeout=5,check=False)
        self.assertEqual(result.returncode,2);self.assertNotIn(SECRET.encode(),result.stdout+result.stderr)

    def test_missing_sibling_bootstrap_never_prints_exception_path(self):
        with tempfile.TemporaryDirectory(prefix=SECRET) as temporary:
            path=Path(temporary)/FILE.name;path.write_bytes(FILE.read_bytes())
            result=subprocess.run([sys.executable,'-B',str(path)],capture_output=True,timeout=5,check=False)
        self.assertEqual(result.returncode,2);self.assertNotIn(SECRET.encode(),result.stdout+result.stderr)
        self.assertEqual(json.loads(result.stderr)['code'],'helper_bootstrap_failed')

    def test_main_preserves_failure_and_uploads_closed_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            home=Path(temporary).resolve();(home/'pals-mini-deploy').mkdir(mode=0o700)
            def failed(_args,_root,report):
                report['stage']='sdk_read_only_probe'
                error=m.B.Refusal('child_failed');error.diagnostic={'code':'sdk_transport_failed','sdk_stage':'aws_identity'}
                raise error
            with patch.object(m.Path,'home',return_value=home),patch.object(m,'sequence',side_effect=failed), \
                 patch.object(m,'upload_reports',return_value={'summary.json':{'key':'fixed'}}) as upload,redirect_stdout(io.StringIO()) as out:
                self.assertEqual(m.main([]),2)
            self.assertEqual(json.loads(out.getvalue())['stage'],'sdk_read_only_probe')
            self.assertEqual(upload.call_args.args[1]['failure']['sdk_stage'],'aws_identity')
            self.assertFalse(upload.call_args.args[1]['source_stop_performed'])

    def final_sequence(self, failure=False, resume=False):
        binding=(b'policy',b'current',b'config')
        expected={key:m.B.sha(raw) for key,raw in zip(
            ('policy_sha256','current_sha256','config_sha256'),binding)}
        events=[]
        def base(_root,report):
            report['source_baseline']=expected
        def maintain(_root,report):
            events.append('maintenance');report['watchdog_maintenance']={'entered':True}
        def run(role,args,**kwargs):
            if '--final' in args or '--resume-final' in args:
                events.append('final')
                self.assertEqual('--resume-final' in args,resume)
                self.assertEqual(kwargs,{'timeout':1200})
                self.assertEqual(args[-2:],['--confirm-source-manifest','e'*64])
                if failure:raise m.B.Refusal('child_failed')
                return json.dumps({'status':'final_uploaded_source_fenced','session':'d'*32,
                                   'admission_eligible':False}).encode()
            events.append(args[0]);return self.child(role,args)
        with patch.object(m,'baseline',side_effect=base),patch.object(m,'enter_migration_maintenance',side_effect=maintain), \
             patch.object(m.B,'inspect_final_state',return_value=(
                 {'journal':{'exists':True,'read_status':'validated','phase':'failed_reconcile_required',
                             'capture_completed':False},
                  'containers':{name:{'running':name==m.B.DATABASE} for name in m.PUBLIC_CONTAINER_NAMES}}
                 if resume else {'journal':{'exists':False},'containers':{'fixture':{'running':True}}}),create=True), \
             patch.object(m,'child',side_effect=run),patch.object(m.B,'controller',return_value=(
                 {},{'manifest_sha256':'e'*64},None,binding)):
            if failure:
                with self.assertRaises(m.B.Refusal):
                    m.sequence(SimpleNamespace(apply_runtime_secrets=True,smoke=True,final_migration=True),Path('/source'),self.report)
            else:
                m.sequence(SimpleNamespace(apply_runtime_secrets=True,smoke=not resume,final_migration=not resume,
                                           resume_final_migration=resume),Path('/source'),self.report)
        return events

    def test_explicit_resume_uses_only_resume_mode_after_observed_stopped_source(self):
        events=self.final_sequence(resume=True)
        self.assertEqual(events[0],'maintenance');self.assertEqual(events[-1],'final')
        self.assertFalse(any('--smoke' in args or '--final' in args for _,args in self.calls))
        self.assertEqual(self.report['status'],'final_uploaded_source_fenced_not_admitted')

    def test_resume_refuses_wrong_source_state_before_any_preparation(self):
        state={'journal':{'exists':True,'read_status':'validated','phase':'failed_reconcile_required',
                          'capture_completed':False},
               'containers':{name:{'running':name==m.B.DATABASE} for name in m.PUBLIC_CONTAINER_NAMES}}
        for key in ('running_actor','database_stopped','capture_complete','journal_absent','journal_unvalidated'):
            bad=json.loads(json.dumps(state))
            if key=='running_actor':bad['containers'][next(iter(m.B.ACTORS.values()))]['running']=True
            if key=='database_stopped':bad['containers'][m.B.DATABASE]['running']=False
            if key=='capture_complete':bad['journal']['capture_completed']=True
            if key=='journal_absent':bad['journal']['exists']=False
            if key=='journal_unvalidated':bad['journal']['read_status']='unavailable'
            with self.subTest(key=key),patch.object(m,'baseline',side_effect=self.baseline), \
                 patch.object(m.B,'controller',return_value=({},None,[],None)), \
                 patch.object(m.B,'inspect_final_state',return_value=bad), \
                 patch.object(m,'enter_migration_maintenance') as maintain,patch.object(m,'child') as run, \
                 self.assertRaisesRegex(m.B.Refusal,'resume_source_state_not_eligible'):
                m.sequence(SimpleNamespace(apply_runtime_secrets=True,smoke=False,final_migration=False,
                                           resume_final_migration=True),Path('/source'),self.report)
            maintain.assert_not_called();run.assert_not_called()

    def test_final_migration_enters_maintenance_then_probe_smoke_and_exact_final(self):
        events=self.final_sequence()
        self.assertEqual(events[0],'maintenance');self.assertEqual(events[-1],'final')
        self.assertIn('--smoke',self.calls[-1][1])
        self.assertEqual(self.report['status'],'final_uploaded_source_fenced_not_admitted')
        self.assertTrue(self.report['source_stop_performed'])
        self.assertFalse(self.report['source_state_requires_reconciliation'])

    def test_final_failure_never_claims_source_unchanged_or_automatically_resumes(self):
        self.final_sequence(failure=True)
        self.assertIsNone(self.report['source_stop_performed'])
        self.assertIsNone(self.report['final_signing_performed'])
        self.assertTrue(self.report['source_state_requires_reconciliation'])

    def test_maintenance_creates_private_marker_and_preserves_existing_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();directory=root/'auto-recovery';directory.mkdir(mode=0o700)
            inspection={'files':{name:{'sha256':pin} for name,pin in m.PINS.items()}}
            observed=({'state_dir':str(root/'state')},{},None,(b'p',b'c',b'd'))
            with patch.object(m.L,'public_inspection',return_value=inspection), \
                 patch.object(m.B,'controller',return_value=observed),patch.object(m.B,'existing_lock',return_value=nullcontext()):
                report={'session':'a'*32};m.enter_migration_maintenance(root,report)
                marker=directory/'disabled.json';raw=marker.read_bytes()
                self.assertEqual(marker.stat().st_mode&0o777,0o600)
                self.assertFalse(report['watchdog_maintenance']['existing_marker_preserved'])
                report={'session':'b'*32};m.enter_migration_maintenance(root,report)
                self.assertEqual(marker.read_bytes(),raw)
                self.assertTrue(report['watchdog_maintenance']['existing_marker_preserved'])

    def test_final_reason_and_fixed_stage_survive_diagnostic_filter(self):
        value=m.safe_diagnostic(json.dumps({'status':'source_final_failed_closed',
            'reason':'actual_authority_drain_definition_changed','stage':'drain_definition_guard',
            'Value':SECRET}).encode())
        self.assertEqual(value['reason'],'actual_authority_drain_definition_changed')
        self.assertEqual(value['stage'],'drain_definition_guard')
        self.assertNotIn(SECRET,json.dumps(value))

    def test_existing_final_journal_prevents_maintenance_or_any_child_operation(self):
        with patch.object(m,'baseline',side_effect=self.baseline),patch.object(m.B,'controller',return_value=({},None,[],None)), \
             patch.object(m.B,'inspect_final_state',return_value={'journal':{'exists':True}}), \
             patch.object(m,'enter_migration_maintenance') as maintain,patch.object(m,'child') as run, \
             self.assertRaisesRegex(m.B.Refusal,'existing_final_journal_requires_reconcile'):
            m.sequence(SimpleNamespace(apply_runtime_secrets=True,smoke=False,final_migration=True),Path('/source'),self.report)
        maintain.assert_not_called();run.assert_not_called()
        self.assertTrue(self.report['source_state_requires_reconciliation'])

    def test_inspect_only_never_enters_preparation_or_takes_source_lock(self):
        with tempfile.TemporaryDirectory() as temporary:
            home=Path(temporary).resolve();(home/'pals-mini-deploy').mkdir(mode=0o700)
            def inspect(_root,report):report.update(status='lock_owner_inspection_complete',stage='complete')
            with patch.object(m.Path,'home',return_value=home),patch.object(m,'inspect_lock_owners',side_effect=inspect), \
                 patch.object(m,'sequence',side_effect=AssertionError('no preparation')), \
                 patch.object(m.B,'existing_lock',side_effect=AssertionError('no lock acquisition')), \
                 patch.object(m,'upload_reports',return_value={}),redirect_stdout(io.StringIO()):
                self.assertEqual(m.main(['--inspect-lock-owner-only']),0)
        with self.assertRaises(m.B.Refusal):m.main(['--inspect-lock-owner-only','--apply-runtime-secrets'])


if __name__=='__main__':unittest.main()
