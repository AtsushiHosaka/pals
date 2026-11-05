"""Offline loader contracts; no AWS, Docker load or source operations."""
import ast
import importlib.util
import io
import json
import os
import tarfile
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

FILE = Path(__file__).resolve().parents[1]/"aws-migration-source-load-tool.py"
SPEC = importlib.util.spec_from_file_location("load_tool", FILE)
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def receipt():
    return {"schema_version":"pals.migration-tool-image.v1","admission_eligible":False,"bucket":m.b.BUCKET,
            "bytes":m.SIZE,"image_tag":m.TAG,"key":m.ARCHIVE_KEY,"platform":"linux/arm64",
            "source_commit":m.COMMIT,"sha256":m.ARCHIVE_SHA,"version_id":m.VERSION,
            "rootfs_diff_ids":["sha256:"+"a"*64],"docker_inspect_config_json_sha256":"b"*64}


class LoaderTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();m.b.DEADLINE=time.monotonic()+10

    def test_python39_syntax(self):
        ast.parse(FILE.read_text(),feature_version=(3,9))

    def test_failure_diagnostics_have_only_known_stage_code_and_field(self):
        m.STAGE='controller_read';secret='synthetic-private-value-never-print'
        for error in (KeyError(secret),RuntimeError(secret),m.b.Refusal(secret),ValueError(secret)):
            summary=m.failure(error)
            self.assertEqual(summary['stage'],'controller_read')
            self.assertNotIn(secret,json.dumps(summary));self.assertNotIn('known_field',summary)
        self.assertEqual(m.failure(KeyError('database_container'))['known_field'],'database_container')

    def test_public_inspection_redacts_all_unselected_config_values(self):
        state=self.root/'state';state.mkdir(mode=0o700)
        (self.root/'auto-recovery').mkdir(mode=0o700)
        secret='synthetic-private-value-never-print'
        policy={'database_container':m.b.DATABASE,'edge_container':'pals-edge','kms_public_key_sha256':'a'*64,
                'state_dir':str(state),'runtime_profile':'isolated-lean-v1','containers':m.b.ACTORS,
                'docker_binary':'/usr/bin/docker','docker_config':str(self.root/'docker'),'docker_context':'orbstack',
                'database_identity':{'private':secret},'unknown-secret':secret}
        m.b.write(self.root/'controller-policy.json',json.dumps(policy).encode())
        m.b.write(self.root/'deploy-config.json',json.dumps(policy).encode())
        m.b.write(self.root/'controller.py',b'# synthetic controller code')
        m.b.write(self.root/'auto-recovery/auto_recovery.py',b'# synthetic watchdog code')
        for name in ('host-update.lock','deploy.lock'):m.b.write(state/name,b'')
        report=m.public_inspection(self.root)
        self.assertNotIn(secret,json.dumps(report));self.assertNotIn('unknown-secret',json.dumps(report))
        self.assertTrue(report['policy_fields']['database_container']['matches_fixed_source'])
        self.assertEqual(report['locks']['deploy.lock']['mode'],'0o600')
        self.assertEqual(report['files']['watchdog']['sha256'],m.b.sha(b'# synthetic watchdog code'))

    def test_inspection_bypasses_controller_and_all_subprocesses(self):
        with patch.object(m.Path,'home',return_value=self.root),patch.object(m.b,'controller',side_effect=AssertionError('no validation')), \
             patch.object(m.b,'run',side_effect=AssertionError('no subprocess')),patch('sys.stdout',new_callable=io.StringIO) as out:
            self.assertEqual(m.main(['--inspect-controller']),0)
        self.assertEqual(json.loads(out.getvalue())['status'],'tool_loader_public_controller_inspection')

    def test_metadata_pin_closed_fields_and_fixed_destination(self):
        value=receipt();raw=json.dumps(value).encode();self.assertEqual(m.metadata(raw,m.b.sha(raw)),value)
        with self.assertRaises(m.b.Refusal):m.metadata(raw,'0'*64)
        for key,value in [('key','../foreign'),('bytes',True),('platform','linux/amd64'),('version_id','different'),('extra',True)]:
            changed=receipt();changed[key]=value;raw=json.dumps(changed).encode()
            with self.assertRaises(m.b.Refusal):m.metadata(raw,m.b.sha(raw))

    def test_default_plan_never_calls_aws_or_docker(self):
        with patch.object(m.b,'cli',side_effect=AssertionError('AWS forbidden')), \
             patch.object(m.b,'run',side_effect=AssertionError('Docker forbidden')):
            result=m.execute(self.root,SimpleNamespace(apply=False),{},[],(),lambda:None)
        self.assertEqual(result['status'],'tool_image_load_read_only_plan')

    def test_download_fixed_version_owner_range_private_and_reuse(self):
        content=b'fixture';digest=m.b.sha(content);calls=[]
        def aws(service,operation,payload,extra):
            calls.append((service,operation,payload))
            Path(extra[0]).write_bytes(content)
            return {'ContentLength':len(content),'ServerSideEncryption':'AES256','VersionId':'version'}
        with patch.object(m.b,'cli',side_effect=aws):
            path=m.download(self.root,'archive','fixed/key',len(content),digest,'version')
            self.assertEqual(m.download(self.root,'archive','fixed/key',len(content),digest,'version'),path)
        self.assertEqual(len(calls),1);self.assertEqual(path.stat().st_mode&0o777,0o600)
        self.assertEqual(calls[0][2],{'Bucket':m.b.BUCKET,'Key':'fixed/key','ExpectedBucketOwner':m.b.ACCOUNT,
                                    'Range':'bytes=0-6','VersionId':'version'})

    def test_existing_foreign_file_and_symlink_refused_without_network(self):
        m.b.write(self.root/'foreign',b'wrong');os.symlink(self.root/'foreign',self.root/'link')
        with patch.object(m.b,'cli',side_effect=AssertionError('network forbidden')):
            for name in ('foreign','link'):
                with self.assertRaises(m.b.Refusal):m.download(self.root,name,'key',5,'0'*64,'version')

    def test_inspect_content_not_docker_id_equals_config_hash(self):
        config={'Labels':{'org.opencontainers.image.revision':m.COMMIT}}
        expected=receipt();expected['docker_inspect_config_json_sha256']=m.b.sha(json.dumps(config,sort_keys=True,separators=(',',':')).encode())
        image={'Id':'sha256:'+'c'*64,'Os':'linux','Architecture':'arm64','Config':config,
               'RootFS':{'Layers':expected['rootfs_diff_ids']},'RepoTags':[m.TAG]}
        with patch.object(m.b,'result',return_value=[image]):
            self.assertEqual(m.verify_image(['docker'],expected),image['Id'])
            image['RootFS']['Layers']=['sha256:'+'d'*64]
            with self.assertRaises(m.b.Refusal):m.verify_image(['docker'],expected)

    def test_archive_rejects_additional_tag_and_traversal(self):
        for index,(tags,name) in enumerate([([m.TAG],'manifest.json'),([m.TAG,'foreign:tag'],'manifest.json'),([m.TAG],'../manifest.json')]):
            path=self.root/str(index)
            with tarfile.open(path,'w') as tar:
                raw=json.dumps([{'RepoTags':tags}]).encode();info=tarfile.TarInfo(name);info.size=len(raw)
                tar.addfile(info,io.BytesIO(raw))
            if index==0:m.archive_contract(path)
            else:
                with self.assertRaises(m.b.Refusal):m.archive_contract(path)


if __name__=='__main__':unittest.main()
