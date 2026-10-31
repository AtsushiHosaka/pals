"""Preparation orchestration only; no AWS, Docker, source capture or secret reads."""
import ast
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
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
            if args==['--probe-sdk-transport']:
                value={'status':'sdk_probe_verified','account_verified':True,'endpoint_verified':True,
                       'metadata_read_verified':True,'service_write_attempted':False}
            else:
                verified=args==['--apply'] or self.reconciled=='verified'
                value={'status':'verified' if verified else 'reconciled_absent',
                       'verified_parameter_count':5 if verified else 2,'admission_eligible':False}
        elif role=='inventory':
            return ('Inventory uploaded to existing private backup bucket.\nKey: aws-migration-20261030/source-inventory/inventory-'+
                    'a'*64+'.json\nSHA256: '+'a'*64+'\n').encode()
        elif role=='loader':value={'source_docker_image_id':'sha256:'+'b'*64,'admission_eligible':False}
        elif '--probe-lock-propagation' in args:
            value={'status':'native_container_lock_exclusion_observed','admission_eligible':False}
        else:value={'status':'smoke_uploaded_not_admissible','session':'c'*32,'admission_eligible':False}
        return json.dumps(value).encode()

    def sequence(self,apply=True,smoke=False):
        with patch.object(m,'baseline',side_effect=self.baseline),patch.object(m,'child',side_effect=self.child):
            m.sequence(SimpleNamespace(apply_runtime_secrets=apply,smoke=smoke),Path('/source'),self.report)

    def test_order_reconcile_before_apply_load_then_actual_lock_probe_never_final(self):
        self.sequence()
        self.assertEqual([args for role,args in self.calls if role=='secrets'],
                         [['--probe-sdk-transport'],['--reconcile'],['--apply']])
        self.assertEqual([role for role,_ in self.calls],['secrets','secrets','secrets','inventory','loader','final'])
        final=self.calls[-1][1]
        self.assertEqual(final,['--tool-image','sha256:'+'b'*64,'--tool-api-commit',m.L.COMMIT,'--probe-lock-propagation'])
        self.assertEqual(self.report['status'],'prepared_not_admitted')
        for forbidden in ('--final','--refresh-fence','--confirm-source-manifest','stop','kill'):
            self.assertFalse(any(forbidden in args for _,args in self.calls))

    def test_already_verified_skips_put_and_default_has_no_secret_transfer(self):
        self.reconciled='verified';self.sequence()
        self.assertFalse(any('--apply' in args for role,args in self.calls if role=='secrets'))
        self.calls.clear();self.sequence(apply=False)
        self.assertEqual([args for role,args in self.calls if role=='secrets'],[['--probe-sdk-transport']])

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


if __name__=='__main__':unittest.main()
