"""Offline source-bridge boundaries; no Docker, AWS, production SQL or source stops."""
import ast
import base64
import copy
import fcntl
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

FILE = Path(__file__).resolve().parents[1]/"aws-migration-source-final.py"
SPEC = importlib.util.spec_from_file_location("source_final", FILE)
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)
CANARY = "synthetic-private-value-do-not-print"


def envelope(raw):
    return m.encoded({"schema_version": m.ENVELOPE, "payload_b64": base64.b64encode(raw).decode(),
                      "signature_b64": base64.b64encode(b"synthetic-der").decode()})


def source_items(edge="pals-edge"):
    result = {}
    for index, name in enumerate([*m.ACTORS.values(), edge, m.DATABASE]):
        result[name] = {"Name": "/"+name, "Id": format(index+1, "064x"),
                        "Image": "sha256:"+format(index+20, "064x"), "Mounts": [],
                        "Config": {"Image": "pgvector/pgvector@sha256:"+"a"*64,
                                   "Env": ["PALS_ENV=prod", "PATH=/usr/bin:/bin"]},
                        "State": {"Running": True},
                        "HostConfig": {"RestartPolicy": {"Name": "unless-stopped", "MaximumRetryCount": 0}}}
    return result


class PrivateIOTests(unittest.TestCase):
    def test_private_read_rejects_alias_and_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve(); file = root/"input"
            m.write(file, CANARY.encode()); self.assertEqual(m.private(file), CANARY.encode())
            alias = root/"alias"; alias.symlink_to(file)
            with self.assertRaises(m.Refusal): m.private(alias)
            file.chmod(0o644)
            with self.assertRaises(m.Refusal): m.private(file)

    def test_atomic_metadata_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory).resolve()/"receipt"
            m.write(file, b"one")
            with self.assertRaises(FileExistsError): m.write(file, b"two")
            m.write(file, b"two", replace=True)
            self.assertEqual(file.read_bytes(), b"two")
            self.assertEqual(file.stat().st_mode & 0o777, 0o600)

    def test_python39_syntax_and_no_sdk_imports(self):
        source = FILE.read_text(); tree = ast.parse(source, feature_version=(3, 9))
        imported = {a.name.split('.')[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        self.assertFalse(imported & {"boto3", "botocore", "psycopg", "requests"})

    def test_failure_console_does_not_echo_unknown_arguments(self):
        child = subprocess.run([sys.executable, str(FILE), "--"+CANARY], capture_output=True,
                               timeout=5, check=False)
        self.assertEqual(child.returncode, 2)
        self.assertNotIn(CANARY.encode(), child.stdout+child.stderr)

    def test_real_pipe_output_limit_and_command_error_are_static(self):
        m.DEADLINE = time.monotonic()+5
        with patch.object(m, "MAX_METADATA", 1024), self.assertRaises(m.Refusal):
            m.run([sys.executable, "-c", "import sys;sys.stdout.write('x'*65536)"])
        with self.assertRaises(m.Refusal) as failure:
            m.run([sys.executable, "-c", "import sys;sys.stderr.write('"+CANARY+"');sys.exit(1)"])
        self.assertNotIn(CANARY, str(failure.exception))


class LockAndBindingsTests(unittest.TestCase):
    def setUp(self):
        m.DEADLINE=time.monotonic()+5

    def test_free_held_free_probe_exercises_real_native_child_exclusion(self):
        with tempfile.TemporaryDirectory() as directory:
            lock = Path(directory).resolve()/"deploy.lock"; m.write(lock, b"")
            statuses = []
            def native(_args, **_kwargs):
                # Replace only the VM command boundary. The actual fcntl probe
                # executes in a separate native Python process against the fixture.
                code = _args[-1].replace("'/lock'", repr(str(lock)))
                child = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True,
                                       timeout=5, check=False)
                statuses.append(child.returncode)
                return child.returncode, child.stdout, child.stderr
            with patch.object(m, "run", side_effect=native):
                m.probe_lock(["docker"], "sha256:"+"a"*64, lock)
            self.assertEqual(statuses, [0, 75, 0])

    def test_unrelated_existing_container_lock_cannot_fake_success(self):
        with tempfile.TemporaryDirectory() as directory:
            lock = Path(directory).resolve()/"deploy.lock"; m.write(lock, b"")
            with patch.object(m, "run", return_value=(75, b"native_lock_refused\n", b"")), \
                 self.assertRaises(m.Refusal):
                m.probe_lock(["docker"], "sha256:"+"a"*64, lock)

    def test_native_lock_metadata_and_competing_fd(self):
        with tempfile.TemporaryDirectory() as directory:
            lock = Path(directory).resolve()/"deploy.lock"; m.write(lock, b"")
            with m.existing_lock(lock) as verify:
                fd = os.open(lock, os.O_RDONLY)
                try:
                    with self.assertRaises(BlockingIOError): fcntl.flock(fd, fcntl.LOCK_EX|fcntl.LOCK_NB)
                    verify()
                finally: os.close(fd)

    def test_guest_fingerprint_is_of_decoded_key_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory).resolve()/"guest"; m.write(file, ("ab"*32+"\n").encode())
            env = {"PALS_GUEST_HASH_KEY": "AB"*32, "PALS_COGNITO_USER_POOL_ID": "ap-northeast-1_Test",
                   "PALS_COGNITO_APP_CLIENT_ID": "client123", "PALS_COGNITO_ISSUER": "https://cognito-idp.ap-northeast-1.amazonaws.com/ap-northeast-1_Test",
                   "PALS_S3_ARTIFACT_BUCKET": "fixture-artifacts", "PALS_SQS_PROOF_JOBS_QUEUE_URL":
                   "https://sqs.ap-northeast-1.amazonaws.com/828786775577/jobs",
                   "PALS_PROOF_REQUESTS_QUEUE_URL": "https://sqs.ap-northeast-1.amazonaws.com/828786775577/requests"}
            actor = {"Config": {"Env": [k+"="+v for k,v in env.items()]}}
            bindings = m.external_bindings({"guest_hash_key_file": str(file)}, actor)
            self.assertEqual(len(bindings), 7)
            self.assertEqual(bindings["guest_key_sha256"], hashlib.sha256(bytes.fromhex("ab"*32)).hexdigest())
            self.assertNotEqual(bindings["guest_key_sha256"], hashlib.sha256(("ab"*32).encode()).hexdigest())
            env["PALS_PROOF_REQUESTS_QUEUE_URL"] = env["PALS_SQS_PROOF_JOBS_QUEUE_URL"]
            with self.assertRaises(m.Refusal):
                m.external_bindings({"guest_hash_key_file": str(file)}, {"Config": {"Env": [k+"="+v for k,v in env.items()]}})


class ImageAndSignatureTests(unittest.TestCase):
    def test_actual_saved_config_bytes_are_hashed_not_docker_image_id(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory).resolve()
            image = "sha256:"+"a"*64; layers = ["sha256:"+"b"*64]
            raw = json.dumps({"architecture": "arm64", "os": "linux", "rootfs": {"type": "layers", "diff_ids": layers}}).encode()
            item = {"Id": image, "Os": "linux", "Architecture": "arm64", "RootFS": {"Layers": layers}}
            database = {"Image": image, "Config": {"Image": "pgvector/pgvector@"+image}}
            def save(_args, **options):
                with tarfile.open(fileobj=options["output"], mode="w|") as archive:
                    for name, content in [("manifest.json", b'[{"Config":"config.json"}]'), ("config.json", raw)]:
                        member = tarfile.TarInfo(name); member.size = len(content)
                        archive.addfile(member, io.BytesIO(content))
                return 0, b"", b""
            with patch.object(m, "result", return_value=[item]), patch.object(m, "run", side_effect=save):
                identity = m.image_identity(["docker"], database, out)
            self.assertEqual(identity["source_docker_image_id"], image)
            self.assertEqual(identity["source_image_config_sha256"], hashlib.sha256(raw).hexdigest())
            self.assertNotEqual(identity["source_image_config_sha256"], image.split(':')[1])

    def test_kms_uses_32_raw_digest_bytes_and_actual_verify_command(self):
        signature = b"\x30"+b"x"*69
        calls = []
        temporary_files = []
        def aws(args, data=None, **_options):
            calls.append((args,data))
            self.assertIsNone(data)
            digest = Path(args[args.index('--message')+1].removeprefix('fileb://'))
            temporary_files.append(digest)
            self.assertEqual(digest.read_bytes(),hashlib.sha256(b'fixture-payload').digest())
            self.assertEqual(digest.stat().st_size,32)
            self.assertEqual(digest.stat().st_mode&0o777,0o600)
            self.assertEqual(digest.parent.stat().st_mode&0o777,0o700)
            self.assertEqual(args[args.index('--key-id')+1],m.KEY)
            self.assertEqual(args[args.index('--message-type')+1],'DIGEST')
            self.assertEqual(args[args.index('--signing-algorithm')+1],'ECDSA_SHA_256')
            self.assertNotIn('fixture-payload',repr(args))
            self.assertNotIn("--cli-input-json", args)
            if "sign" in args:
                response = {"KeyId": m.KEY, "SigningAlgorithm": "ECDSA_SHA_256",
                            "Signature": base64.b64encode(signature).decode()}
            else:
                path = args[args.index("--signature")+1].removeprefix("fileb://")
                self.assertEqual(Path(path).read_bytes(), signature)
                self.assertEqual(Path(path).stat().st_mode & 0o777, 0o600)
                response = {"KeyId": m.KEY, "SigningAlgorithm": "ECDSA_SHA_256", "SignatureValid": True}
            return 0, json.dumps(response).encode(), b""
        with patch.object(m, "run", side_effect=aws):
            observed = json.loads(m.signed(b"fixture-payload"))
        self.assertEqual([a[a.index("kms")+1] for a,_d in calls], ["sign", "verify"])
        self.assertEqual(base64.b64decode(observed["payload_b64"]), b"fixture-payload")
        self.assertTrue(all(not path.exists() and not path.parent.exists() for path in temporary_files))

    def test_public_aws_calls_use_closed_exact_argv_without_stdin(self):
        calls=[]
        def execute(args,data=None,**_options):
            self.assertIsNone(data);self.assertNotIn('--cli-input-json',args)
            self.assertEqual(args[args.index('--profile')+1],m.PROFILE)
            self.assertEqual(args[args.index('--region')+1],m.REGION)
            calls.append(args);return 0,b'{}',b''
        with tempfile.TemporaryDirectory() as temporary,patch.object(m,'run',side_effect=execute):
            root=Path(temporary).resolve();target=root/'download';m.write(target,b'')
            body=root/'body';m.write(body,CANARY.encode())
            base={'Bucket':m.BUCKET,'ExpectedBucketOwner':m.ACCOUNT}
            key='aws-migration-20261030/tools/api-7027478-arm64.tar.gz';version='1MfCzRK8zYelAFqgiGxO1fgChCMnHC8v'
            m.cli('sts','get-caller-identity')
            m.cli('kms','get-public-key',{'KeyId':m.KEY})
            for operation in ('get-public-access-block','get-bucket-acl','get-bucket-versioning'):
                m.cli('s3api',operation,base)
            m.cli('s3api','get-object',{**base,'Key':key,'VersionId':version,'Range':'bytes=0-149928496'},[str(target)])
            args=calls[-1]
            for flag,value in [('--bucket',m.BUCKET),('--expected-bucket-owner',m.ACCOUNT),('--key',key),
                               ('--version-id',version),('--range','bytes=0-149928496')]:
                self.assertEqual(args[args.index(flag)+1],value)
            self.assertEqual(args[-1],str(target))
            digest=m.sha(CANARY.encode());checksum=base64.b64encode(bytes.fromhex(digest)).decode()
            m.cli('s3api','put-object',{**base,'Key':key,'Metadata':{'sha256':digest},'ChecksumSHA256':checksum,
                                      'ServerSideEncryption':'AES256'},['--body',str(body)])
            self.assertNotIn(CANARY,repr(calls[-1]))
            self.assertEqual(calls[-1][calls[-1].index('--checksum-sha256')+1],checksum)
            m.cli('s3api','head-object',{**base,'Key':key,'VersionId':version,'ChecksumMode':'ENABLED'})
            self.assertEqual(calls[-1][-2:],['--checksum-mode','ENABLED'])

    def test_public_aws_unknown_calls_fields_and_foreign_pins_never_execute(self):
        base={'Bucket':m.BUCKET,'ExpectedBucketOwner':m.ACCOUNT}
        with patch.object(m,'run',side_effect=AssertionError('invalid request must not execute')):
            cases=[('ssm','put-parameter',{'Value':CANARY},()),('kms','decrypt',{},()),
                   ('kms','get-public-key',{'KeyId':'foreign'},()),
                   ('s3api','get-bucket-acl',{**base,'Bucket':'foreign'},()),
                   ('s3api','get-bucket-acl',{**base,'Value':CANARY},()),
                   ('s3api','get-bucket-versioning',base,['--endpoint-url','https://foreign.invalid']),
                   ('s3api','head-object',{**base,'Key':'aws-migration-20261030/../foreign','VersionId':'fixed','ChecksumMode':'ENABLED'},()),
                   ('s3api','head-object',{**base,'Key':'aws-migration-20261030/key','VersionId':'null','ChecksumMode':'ENABLED'},()),
                   ('s3api','get-object',{**base,'Key':'aws-migration-20261030/key','Range':'bytes=1-5'},()),
                   ('s3api','get-object',{**base,'Key':'aws-migration-20261030/key','Range':'bytes=0-9999999999'},())]
            for service,operation,payload,extra in cases:
                with self.subTest(operation=operation,payload=payload),self.assertRaises(m.Refusal):
                    m.cli(service,operation,payload,extra)

    def test_false_kms_verify_never_produces_envelope(self):
        with patch.object(m, "run", return_value=(0, json.dumps({"KeyId":m.KEY,
             "SigningAlgorithm":"ECDSA_SHA_256","SignatureValid":False}).encode(), b"")), \
             self.assertRaises(m.Refusal):
            m.verify_signature(b"payload", b"signature")

    def test_fence_requires_all_stopped_and_restart_no(self):
        items = source_items(); policy = {"kms_public_key_sha256":"c"*64}
        identity = {"image_uri":"pgvector/pgvector@sha256:"+"d"*64, "image_id":items[m.DATABASE]["Image"],
                    "source_docker_image_id":items[m.DATABASE]["Image"], "source_image_config_sha256":"e"*64,
                    "source_image_rootfs_diff_ids":["sha256:"+"f"*64]}
        raw = envelope(m.encoded({"predecessor_manifest_sha256":"a"*64,
              "source_identity":{"database_system_identifier":"123", "database_volume_id":"fixture-volume"}}))
        with self.assertRaises(m.Refusal):m.fence(items,identity,raw,"b"*64,policy,"stopped-after-final-capture")
        for item in items.values():item["State"]["Running"]=False;item["HostConfig"]["RestartPolicy"]["Name"]="no"
        observed=m.fence(items,identity,raw,"b"*64,policy,"stopped-before-target-admission")
        from datetime import datetime
        self.assertEqual((datetime.fromisoformat(observed["expires_at"].replace('Z','+00:00'))-
                          datetime.fromisoformat(observed["issued_at"].replace('Z','+00:00'))).total_seconds(),300)
        self.assertEqual(len(observed["writer_containers"]),7)


class NativeLockWaitTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name).resolve()/'host-update.lock';m.write(self.path,b'')
        m.DEADLINE=time.monotonic()+5

    def holder(self,seconds):
        code="import fcntl,sys,time; f=open(sys.argv[1],'rb');fcntl.flock(f,fcntl.LOCK_EX);print('held',flush=True);time.sleep(float(sys.argv[2]))"
        process=subprocess.Popen([sys.executable,'-I','-c',code,str(self.path),str(seconds)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        self.addCleanup(process.stderr.close);self.addCleanup(process.stdout.close)
        self.addCleanup(process.wait,timeout=2)
        self.assertEqual(process.stdout.readline(),b'held\n')
        return process

    def test_real_competing_process_release_then_parent_acquires_same_inode(self):
        inode=self.path.stat().st_ino;process=self.holder(0.25)
        with m.existing_lock(self.path) as verify:
            process.wait(timeout=2);verify()
            fd=os.open(self.path,os.O_RDONLY)
            try:
                with self.assertRaises(BlockingIOError):fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            finally:os.close(fd)
            self.assertIsNotNone(m.LOCK_FD)
        self.assertEqual(self.path.stat().st_ino,inode);self.assertIsNone(m.LOCK_FD)

    def test_real_persistent_contention_hits_wait_bound_without_mutating_lock(self):
        self.holder(0.35);inode=self.path.stat().st_ino;began=time.monotonic()
        with patch.object(m,'LOCK_WAIT_SECONDS',0.08),self.assertRaises(BlockingIOError),m.existing_lock(self.path):pass
        self.assertLess(time.monotonic()-began,0.3)
        self.assertEqual(self.path.stat().st_ino,inode);self.assertIsNone(m.LOCK_FD)

    def test_total_deadline_caps_real_contention_wait(self):
        self.holder(0.35);m.DEADLINE=time.monotonic()+0.08;began=time.monotonic()
        with self.assertRaisesRegex(m.Refusal,'total_timeout'),m.existing_lock(self.path):pass
        self.assertLess(time.monotonic()-began,0.3);self.assertIsNone(m.LOCK_FD)

    def test_inode_replacement_during_real_contention_is_rejected(self):
        self.holder(0.35)
        def replace():
            time.sleep(0.04);replacement=self.path.with_name('replacement');m.write(replacement,b'');os.replace(replacement,self.path)
        changed=threading.Thread(target=replace);changed.start();self.addCleanup(changed.join,1)
        with self.assertRaisesRegex(m.Refusal,'source_lock_changed'),m.existing_lock(self.path):pass
        self.assertIsNone(m.LOCK_FD)


class CaptureOrderingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();(self.root/"aws-migration-20261030").mkdir(mode=0o700)
        m.write(self.root/'deploy.lock',b'')
        (self.root/'auto-recovery').mkdir(mode=0o700)
        m.write(self.root/'auto-recovery/disabled.json',b'{"reason":"final-source-capture"}')
        self.previous=m.encoded({"kms_key_arn":m.KEY});self.previous_path=self.root/"previous"
        m.write(self.previous_path,self.previous);m.write(self.root/"signature",b"signature")
        self.policy={"state_dir":str(self.root),"edge_container":"pals-edge","signed_predecessor_manifest":str(self.previous_path),
                     "signed_predecessor_signature":str(self.root/"signature"),"kms_public_key_sha256":"e"*64}
        self.items=source_items();self.actual=copy.deepcopy(self.items);self.events=[]
        images={role:self.items[name]["Image"] for role,name in m.ACTORS.items() if role not in ['assessment-worker','reconciler']}
        images['worker']=self.items[m.ACTORS['worker']]['Image']
        for role,component in [('assessment-worker','worker'),('reconciler','api')]:
            self.items[m.ACTORS[role]]['Image']=images[component];self.actual[m.ACTORS[role]]['Image']=images[component]
        self.current={"manifest_sha256":m.sha(self.previous),"images":images}
        self.binding=(b"policy",b"current",b"config")
        self.identity={"image_uri":"pgvector/pgvector@sha256:"+"f"*64,"image_id":self.items[m.DATABASE]['Image'],
                       "source_docker_image_id":self.items[m.DATABASE]['Image'],"source_image_config_sha256":"d"*64,
                       "source_image_rootfs_diff_ids":["sha256:"+"c"*64]}
        self.args=SimpleNamespace(final=True,tool_image="sha256:"+"a"*64,tool_api_commit="b"*40,
                                  confirm_source_manifest=self.current['manifest_sha256'])
        self.fail_capture=False;self.fail_db_stop=False;m.DEADLINE=time.monotonic()+30

    def fake_run(self, args, **_kwargs):
        operation=args[1];self.events.append((operation,args[2:]))
        byid={v['Id']:v for v in self.actual.values()}
        if operation=='stop':
            if self.fail_db_stop and self.items[m.DATABASE]['Id'] in args:raise m.Refusal('command_failed')
            for value in args[2:]:
                if value in byid:byid[value]['State']['Running']=False
        elif operation=='update':
            for value in args[2:]:
                if value in byid:byid[value]['HostConfig']['RestartPolicy']['Name']='no'
        else:raise AssertionError(operation)
        return 0,b'',b''

    def prepare(self,_root,output,*_args):
        m.write(output/'inputs/historical-registry.json',b'{}')
        m.write(output/'inputs/master-url',CANARY.encode())

    def tool(self,*args):
        self.events.append(('capture',[]))
        if self.fail_capture:raise m.Refusal('tool_stdio_timeout')
        return m.encoded({'schema_version':'pals.cloud-restore.source-evidence.v1',
                         'predecessor_manifest_sha256':self.current['manifest_sha256'],
                         'source_identity':{'database_system_identifier':'123','database_volume_id':'fixture-volume'}})

    def signing(self,raw):
        self.assertTrue(m.stopped(self.actual))
        # Actual native lock remains held throughout signing, beyond tool exit.
        fd=os.open(self.root/'deploy.lock',os.O_RDONLY)
        try:
            with self.assertRaises(BlockingIOError):fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        finally:os.close(fd)
        self.events.append(('sign',[]));return envelope(raw)

    def execute(self):
        with patch.object(m,'require_drain_definition'),patch.object(m,'source_tools',return_value=({},'a'*64)), \
             patch.object(m,'probe_lock'),patch.object(m,'aws_preflight',return_value=b'public'), \
             patch.object(m,'prepare_inputs',side_effect=self.prepare),patch.object(m,'image_identity',return_value=self.identity), \
             patch.object(m,'controller',return_value=(None,None,None,self.binding)), \
             patch.object(m,'inspect_all',side_effect=lambda *_args:copy.deepcopy(self.actual)), \
             patch.object(m,'run',side_effect=self.fake_run),patch.object(m,'drained',return_value=True), \
             patch.object(m,'capture_tool',side_effect=self.tool),patch.object(m,'signed',side_effect=self.signing), \
             patch.object(m,'upload',side_effect=lambda *_a,**_k:self.assertTrue(m.stopped(self.actual))):
            return m.capture(self.root,self.args,self.policy,self.current,['docker'],self.binding,self.items,lambda:None)

    def test_final_capture_and_database_fence_precede_every_sign(self):
        result=self.execute();self.assertEqual(result['status'],'final_uploaded_source_fenced')
        labels=[x[0] for x in self.events];self.assertLess(labels.index('capture'),labels.index('sign'))
        dbstop=next(i for i,(op,argv) in enumerate(self.events) if op=='stop' and self.items[m.DATABASE]['Id'] in argv)
        self.assertLess(labels.index('capture'),dbstop);self.assertLess(dbstop,labels.index('sign'))
        journal=json.loads(m.private(m.journal_path(self.root)));self.assertEqual(journal['phase'],'uploaded_source_fenced')
        self.assertNotIn(CANARY,repr(journal));self.assertFalse((Path(journal['output_directory'])/'inputs/master-url').exists())

    def test_default_plan_has_no_aws_or_mutation_boundary(self):
        m.write(self.root/'host-update.lock',b'')
        args=['--tool-image',self.args.tool_image,'--tool-api-commit',self.args.tool_api_commit]
        with patch.object(m.Path,'home',return_value=self.root.parent), \
             patch.object(m,'controller',return_value=(self.policy,self.current,['docker'],self.binding)), \
             patch.object(m,'tool_image'),patch.object(m,'inspect_all',return_value=self.items), \
             patch.object(m,'require_drain_definition'),patch.object(m,'source_tools'), \
             patch.object(m,'cli',side_effect=AssertionError('AWS forbidden in default plan')), \
             patch.object(m,'capture',side_effect=AssertionError('capture forbidden in default plan')), \
             patch.object(m,'run',side_effect=AssertionError('unexpected subprocess')), \
             patch('sys.stdout',new_callable=io.StringIO) as output:
            self.assertEqual(m.main(args),0)
        self.assertEqual(json.loads(output.getvalue())['status'],'source_final_read_only_plan')

    def test_capture_failure_never_stops_database_or_signs_or_restarts_source(self):
        self.fail_capture=True
        with self.assertRaises(m.Refusal):self.execute()
        self.assertTrue(self.actual[m.DATABASE]['State']['Running'])
        self.assertNotIn('sign',[x[0] for x in self.events]);self.assertNotIn('start',[x[0] for x in self.events])
        journal=json.loads(m.private(m.journal_path(self.root)))
        self.assertEqual(journal['phase'],'failed_reconcile_required');self.assertIs(journal['capture_completed'],False)

    def test_missing_or_unsafe_maintenance_prevents_first_source_mutation(self):
        marker=self.root/'auto-recovery/disabled.json'
        marker.unlink()
        with self.assertRaisesRegex(m.Refusal,'source_recovery_maintenance_required'):self.execute()
        self.assertEqual(self.events,[])
        for raw,mode in [(b'[]',0o600),(b'{}',0o644),(b'not-json',0o600)]:
            m.write(marker,raw);marker.chmod(mode)
            with self.assertRaisesRegex(m.Refusal,'source_recovery_maintenance_required'):self.execute()
            self.assertEqual(self.events,[]);marker.unlink()

    def test_removed_maintenance_after_ingress_stop_blocks_further_mutation(self):
        original=self.fake_run
        def changed(args,**options):
            result=original(args,**options)
            (self.root/'auto-recovery/disabled.json').unlink()
            return result
        with patch.object(self,'fake_run',side_effect=changed),self.assertRaisesRegex(m.Refusal,'source_recovery_maintenance_required'):
            self.execute()
        self.assertEqual(len(self.events),1)
        self.assertTrue(self.actual[m.DATABASE]['State']['Running'])
        self.assertNotIn('sign',[x[0] for x in self.events])

    def test_ambiguous_database_stop_never_signs_or_retries(self):
        self.fail_db_stop=True
        with self.assertRaises(m.Refusal):self.execute()
        self.assertNotIn('sign',[x[0] for x in self.events])
        dbstops=[x for x in self.events if x[0]=='stop' and self.items[m.DATABASE]['Id'] in x[1]]
        self.assertEqual(len(dbstops),1)
        self.assertEqual(self.actual[m.DATABASE]['HostConfig']['RestartPolicy']['Name'],'no')
        self.assertEqual(json.loads(m.private(m.journal_path(self.root)))['phase'],'failed_reconcile_required')


class WireAndUploadTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();(self.root/'inputs').mkdir(mode=0o700)
        (self.root/'artifacts').mkdir(mode=0o700);m.write(self.root/'deploy.lock',b'')
        self.items=source_items();self.tools={'env':'/usr/bin/env','pg_dump':'/usr/bin/pg_dump'}
        self.dump_calls=[];m.DEADLINE=time.monotonic()+10

    def test_real_stdio_child_receives_handoff_only_after_both_snapshot_dumps(self):
        raw=m.encoded({'schema_version':'pals.cloud-restore.ec2-rehearsal-unsigned.v1','fixture':True})
        target=self.root/'artifacts/source-payload.jcs'
        child_code=("import sys,json,hashlib,os;print(json.dumps({'event':'snapshot_ready','snapshot':'00000003-00000001-1','admission_eligible':False}),flush=True);"
                    "assert sys.stdin.readline()=='{\"action\":\"dumps-complete\"}\\n';"
                    "raw="+repr(raw)+";p="+repr(str(target))+";f=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.write(f,raw);os.close(f);"
                    "print(json.dumps({'status':'smoke_unsigned_not_admissible','payload_sha256':hashlib.sha256(raw).hexdigest(),'table_count':0,'admission_eligible':False}),flush=True)")
        original=subprocess.Popen
        def popen(_args,**options):return original([sys.executable,'-c',child_code],**options)
        def dumps(args,**options):
            if 'ps' in args:return 0,b'',b''
            self.assertIn('--snapshot=00000003-00000001-1',args)
            self.dump_calls.append(args)
            options['output'].write(b'PGDMPfixture' if '--format=custom' in args else b'-- schema fixture')
            return 0,b'',b''
        with patch.object(m.subprocess,'Popen',side_effect=popen),patch.object(m,'run',side_effect=dumps):
            observed=m.capture_tool(self.root,self.root,{'state_dir':str(self.root)},['docker'],
                                    self.items,'sha256:'+'a'*64,self.tools,True)
        self.assertEqual(observed,raw);self.assertEqual(len(self.dump_calls),2)

    def test_expired_budget_still_invokes_owned_tool_cleanup(self):
        original=subprocess.Popen
        def popen(_args,**options):return original([sys.executable,'-c','import time;time.sleep(30)'],**options)
        image='sha256:'+'a'*64
        info=[{'Image':image,'Id':'a'*64,'Config':{'Labels':{'pals.migration.purpose':'ec2-source-capture'}}}]
        observed=[]
        def cleanup(args,**_options):
            observed.append(args)
            return SimpleNamespace(returncode=0,stdout=json.dumps(info).encode(),stderr=b'')
        m.DEADLINE=time.monotonic()-1
        with patch.object(m,'run',return_value=(0,b'',b'')),patch.object(m.subprocess,'Popen',side_effect=popen), \
             patch.object(m.subprocess,'run',side_effect=cleanup),self.assertRaises(m.Refusal):
            m.capture_tool(self.root,self.root,{'state_dir':str(self.root)},['docker'],self.items,image,self.tools,True)
        self.assertEqual(len(observed),2)
        self.assertIn('inspect',observed[0]);self.assertIn('stop',observed[1]);self.assertIn('a'*64,observed[1])

    def test_manifest_is_last_after_every_artifact_readback(self):
        output=self.root/'artifacts';m.write(output/'one',CANARY.encode());m.write(output/'two',b'fixture')
        calls=[];stored={}
        def aws(service,operation,payload=None,extra=()):
            self.assertEqual(service,'s3api');calls.append((operation,payload['Key']))
            self.assertEqual(payload['ExpectedBucketOwner'],m.ACCOUNT)
            if operation=='put-object':
                body=Path(extra[1]).read_bytes()
                stored[payload['Key']]={'ContentLength':len(body),'Metadata':payload['Metadata'],
                                        'ServerSideEncryption':payload['ServerSideEncryption'],
                                        'ChecksumSHA256':payload['ChecksumSHA256']}
                return {'VersionId':'version1'}
            return stored[payload['Key']]
        with patch.object(m,'cli',side_effect=aws):m.upload(output,['one','two'],'fixture/',smoke=True)
        self.assertEqual(calls, [('put-object','fixture/one'),('head-object','fixture/one'),
                                 ('put-object','fixture/two'),('head-object','fixture/two'),
                                 ('put-object','fixture/manifest.json'),('head-object','fixture/manifest.json')])
        receipt=json.loads((output/'upload-receipt.json').read_bytes());self.assertNotIn(CANARY,repr(receipt))

    def test_failed_artifact_readback_never_publishes_manifest(self):
        output=self.root/'artifacts';m.write(output/'one',b'fixture');calls=[]
        def aws(_service,operation,payload=None,extra=()):
            calls.append((operation,payload['Key']))
            if operation=='put-object':return {'VersionId':'version1'}
            return {'ContentLength':7,'Metadata':{'sha256':'0'*64},'ServerSideEncryption':'AES256','ChecksumSHA256':'wrong'}
        with patch.object(m,'cli',side_effect=aws),self.assertRaises(m.Refusal):m.upload(output,['one'],'fixture/')
        self.assertEqual(len(calls),2);self.assertFalse((output/'upload-manifest.json').exists())

    def test_prepared_config_matches_exact_api_keys_and_url_never_enters_argv(self):
        policy={'state_dir':str(self.root),'database_identity':{'database_volume_id':'fixture-volume'},
                'identity_volume':'fixture-volume-name','kms_public_key_sha256':'a'*64,
                'database_urls':{'master_database_url':str(self.root/'original-url')}}
        for name,filename,content in [('signed_predecessor_manifest','previous',b'{}'),
                ('signed_predecessor_signature','previous-signature',b'signature'),
                ('previous_production_registry','registry',b'{}'),('host_marker','host',b'host')]:
            policy[name]=str(self.root/filename);m.write(self.root/filename,content)
        m.write(self.root/'original-url',('postgresql+psycopg://postgres:'+CANARY+'@original-host:35432/pals').encode())
        self.items[m.DATABASE]['Mounts']=[{'Type':'volume','Name':'fixture-volume-name','Destination':'/var/lib/postgresql/data'}]
        calls=[]
        def cat(args,**_options):calls.append(args);return 0,b'fixture-volume\n',b''
        bindings={'cognito_user_pool_id':'fixture','cognito_app_client_id':'fixture','cognito_issuer':'fixture',
                  'artifact_bucket':'fixture','proof_jobs_queue_arn':'fixture1','proof_requests_queue_arn':'fixture2','guest_key_sha256':'a'*64}
        with patch.object(m,'external_bindings',return_value=bindings),patch.object(m,'run',side_effect=cat):
            m.prepare_inputs(self.root,self.root,policy,{'manifest_sha256':m.sha(b'{}')},['docker'],self.items,b'public','b'*64)
        config=json.loads((self.root/'inputs/capture-config.json').read_bytes())
        owning=FILE.parents[1]/'pals-api/app/release/cloud_restore_ec2_source.py'
        tree=ast.parse(owning.read_text())
        assignment=next(n for n in tree.body if isinstance(n,ast.Assign) and any(
                        isinstance(t,ast.Name) and t.id=='KEYS' for t in n.targets))
        self.assertEqual(set(config),ast.literal_eval(assignment.value.args[0]))
        self.assertEqual(config['deployment_lock_file'],'/deployment-lock')
        self.assertEqual((self.root/'inputs/master-url').read_text(),
                         'postgresql://postgres:'+CANARY+'@127.0.0.1:5432/pals')
        self.assertNotIn(CANARY,repr(calls))


if __name__=='__main__':unittest.main()
