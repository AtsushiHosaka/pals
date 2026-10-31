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
