"""Offline renewal tests. Every CA/key is generated in a temporary directory."""
from datetime import UTC, datetime, timedelta
import json
import io
from contextlib import redirect_stdout
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import broker


class RenewalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.authority = self.root / 'machine-auth'
        self.authority.mkdir(mode=0o700)
        (self.root / 'runtime-sessions').mkdir(mode=0o700)
        self.ca(days=365)
        self.leaf('api', days=30)
        self.config = {'helper': '/synthetic/helper', 'trust_anchor_arn': 'synthetic-anchor',
                       'profile_arn': 'synthetic-profile'}
        self.real_run = subprocess.run
        self.helper_calls = []
        self.identity = {'Account': broker.ACCOUNT,
            'Arn': f'arn:aws:sts::{broker.ACCOUNT}:assumed-role/pals-geekten-api/pals-geekten-api'}

    def ca(self, *, days):
        ca, key = self.authority / 'ca.crt', self.authority / 'ca.key'
        broker.openssl('ecparam', '-name', 'prime256v1', '-genkey', '-noout', '-out', key)
        cnf = self.authority / 'ca.cnf'
        cnf.write_text('[req]\ndistinguished_name=dn\nx509_extensions=ca\nprompt=no\n'
                       '[dn]\nCN=pals-geekten-20261026-ca\n[ca]\n'
                       'basicConstraints=critical,CA:true,pathlen:0\nkeyUsage=critical,keyCertSign,cRLSign\n')
        broker.openssl('req', '-new', '-x509', '-sha256', '-days', str(days), '-key', key,
                       '-out', ca, '-config', cnf)
        for p in (ca, key):
            p.chmod(0o600)

    def leaf(self, purpose, *, days):
        key = self.authority / (purpose + '.key')
        cert = self.authority / (purpose + '.crt')
        csr = self.authority / (purpose + '.csr')
        broker.openssl('ecparam', '-name', 'prime256v1', '-genkey', '-noout', '-out', key)
        broker.openssl('req', '-new', '-key', key, '-out', csr,
                       '-subj', '/CN=pals-geekten-20261026-' + purpose)
        broker.openssl('x509', '-req', '-days', str(days), '-in', csr,
                       '-CA', self.authority / 'ca.crt', '-CAkey', self.authority / 'ca.key',
                       '-set_serial', '1', '-out', cert)
        for p in (key, cert):
            p.chmod(0o600)
        out = self.root / 'runtime-sessions' / purpose
        out.mkdir(mode=0o700, exist_ok=True)

    def helper(self, args, **kwargs):
        if args[0] != self.config['helper']:
            return self.real_run(args, **kwargs)
        cert = Path(args[args.index('--certificate') + 1])
        self.helper_calls.append(cert)
        self.assertEqual(kwargs['env']['AWS_CONFIG_FILE'], '/dev/null')
        self.assertEqual(kwargs['env']['AWS_SHARED_CREDENTIALS_FILE'], '/dev/null')
        self.assertEqual(kwargs['timeout'], 45)
        # Candidate must be usable while the installed cert is still the original.
        if cert.name == 'candidate.crt':
            self.assertEqual((self.authority / 'api.crt').read_bytes(), self.before)
        record = {'Version': 1, 'AccessKeyId': 'synthetic-access', 'SecretAccessKey': 'synthetic-secret',
                  'SessionToken': 'synthetic-token',
                  'Expiration': (datetime.now(UTC) + timedelta(hours=1)).isoformat()}
        return SimpleNamespace(stdout=json.dumps(record).encode())

    def run_broker(self, *, force=False):
        self.before = (self.authority / 'api.crt').read_bytes()
        boto = SimpleNamespace(client=lambda *a, **kw:
            SimpleNamespace(get_caller_identity=lambda: self.identity))
        with patch.dict(sys.modules, {'boto3': boto}), patch.object(broker.subprocess, 'run', self.helper):
            broker.renew('api', self.config, root=self.root, force_certificate_renewal=force)

    def test_unexpired_leaf_is_not_rotated_and_session_is_published(self):
        before = (self.authority / 'api.crt').read_bytes()
        self.run_broker()
        self.assertEqual((self.authority / 'api.crt').read_bytes(), before)
        self.assertEqual(self.helper_calls, [self.authority / 'api.crt'])
        state = json.loads((self.root / 'runtime-sessions/api/state.json').read_text())
        self.assertTrue(state['ready'])
        self.assertEqual(state['session_name'], 'pals-geekten-api')

    def test_due_certificate_authenticates_candidate_before_atomic_replacement(self):
        self.leaf('api', days=2)
        before = (self.authority / 'api.crt').read_bytes()
        preserved = {name: (self.authority / name).read_bytes() for name in ['api.key', 'ca.key', 'ca.crt']}
        inode = (self.authority / 'api.crt').stat().st_ino
        self.run_broker()
        cert = self.authority / 'api.crt'
        self.assertNotEqual(cert.read_bytes(), before)
        self.assertNotEqual(cert.stat().st_ino, inode)
        self.assertEqual(cert.stat().st_mode & 0o777, 0o600)
        self.assertEqual(len(self.helper_calls), 1)
        self.assertEqual(self.helper_calls[0].name, 'candidate.crt')
        self.assertGreater(broker.certificate_dates(cert)[1], datetime.now(UTC) + timedelta(days=29))
        for name, data in preserved.items():
            self.assertEqual((self.authority / name).read_bytes(), data)
        self.assertEqual(list(self.authority.glob('.api-renew-*')), [])

    def test_forced_rotation_and_repeat_skip(self):
        before = (self.authority / 'api.crt').read_bytes()
        self.run_broker(force=True)
        self.assertNotEqual((self.authority / 'api.crt').read_bytes(), before)
        self.run_broker()
        self.assertEqual(self.helper_calls[-1], self.authority / 'api.crt')

    def test_wrong_sts_identity_preserves_cert_and_previous_sessions(self):
        self.run_broker()
        creds = self.root / 'runtime-sessions/api/credentials.json'
        previous_creds = creds.read_bytes()
        before = (self.authority / 'api.crt').read_bytes()
        self.identity['Arn'] = f'arn:aws:sts::{broker.ACCOUNT}:assumed-role/wrong/session'
        with self.assertRaisesRegex(ValueError, 'identity mismatch'):
            self.run_broker(force=True)
        self.assertEqual((self.authority / 'api.crt').read_bytes(), before)
        self.assertEqual(creds.read_bytes(), previous_creds)
        self.assertEqual(list(self.authority.glob('.api-renew-*')), [])

    def test_helper_failure_preserves_current_certificate(self):
        before = (self.authority / 'api.crt').read_bytes()
        def fail(*args, **kwargs):
            raise RuntimeError('synthetic helper failure')
        with self.assertRaises(RuntimeError):
            broker.with_certificate('api', self.authority, fail, now=datetime.now(UTC), force=True)
        self.assertEqual((self.authority / 'api.crt').read_bytes(), before)
        self.assertEqual(list(self.authority.glob('.api-renew-*')), [])

    def test_short_lived_ca_refuses_issuance_and_authenticates_existing_leaf(self):
        self.ca(days=20)
        before = (self.authority / 'api.crt').read_bytes()
        with redirect_stdout(io.StringIO()) as output:
            self.run_broker(force=True)
        self.assertIn('certificate renewal failed', output.getvalue())
        self.assertEqual(self.helper_calls, [self.authority / 'api.crt'])
        self.assertEqual((self.authority / 'api.crt').read_bytes(), before)

    def test_mismatched_leaf_key_rejected(self):
        self.leaf('worker', days=30)
        (self.authority / 'api.key').write_bytes((self.authority / 'worker.key').read_bytes())
        with self.assertRaisesRegex(ValueError, 'key mismatch'):
            self.run_broker(force=True)
        self.assertEqual(self.helper_calls, [])

    def test_candidate_chain_failure_preserves_certificate(self):
        before = (self.authority / 'api.crt').read_bytes()
        # CA/key mismatch makes signing or chain verification fail.
        self.leaf('worker', days=30)
        (self.authority / 'ca.key').write_bytes((self.authority / 'worker.key').read_bytes())
        with redirect_stdout(io.StringIO()) as output:
            self.run_broker(force=True)
        self.assertIn('certificate renewal failed', output.getvalue())
        self.assertEqual((self.authority / 'api.crt').read_bytes(), before)
        self.assertEqual(self.helper_calls, [self.authority / 'api.crt'])

    def test_candidate_auth_failure_keeps_valid_original_ready_with_failure_log(self):
        before = (self.authority / 'api.crt').read_bytes()
        calls = []
        def authenticate(path):
            calls.append(path)
            if path.name == 'candidate.crt':
                raise RuntimeError('synthetic candidate unavailable')
            return 'authenticated old cert'
        with redirect_stdout(io.StringIO()) as output:
            result = broker.with_certificate('api', self.authority, authenticate,
                now=datetime.now(UTC), force=True)
        self.assertEqual(result, 'authenticated old cert')
        self.assertEqual([p.name for p in calls], ['candidate.crt', 'api.crt'])
        self.assertIn('certificate renewal failed; current certificate authenticated', output.getvalue())
        self.assertEqual((self.authority / 'api.crt').read_bytes(), before)

    def test_expired_original_never_used_as_fallback(self):
        now = datetime.now(UTC)
        real_dates = broker.certificate_dates
        def dates(path):
            if path.name == 'api.crt':
                return now - timedelta(days=31), now - timedelta(seconds=1)
            return real_dates(path)
        calls = []
        def unavailable(path):
            calls.append(path)
            raise RuntimeError('synthetic unavailable')
        with patch.object(broker, 'certificate_dates', dates), self.assertRaises(RuntimeError):
            broker.with_certificate('api', self.authority, unavailable, now=now)
        self.assertEqual([p.name for p in calls], ['candidate.crt'])

    def test_failed_atomic_replace_preserves_original_and_authenticates_fallback(self):
        before = (self.authority / 'api.crt').read_bytes()
        calls = []
        with patch.object(broker.os, 'replace', side_effect=OSError('synthetic disk failure')):
            with redirect_stdout(io.StringIO()):
                broker.with_certificate('api', self.authority, lambda p: calls.append(p),
                    now=datetime.now(UTC), force=True)
        self.assertEqual((self.authority / 'api.crt').read_bytes(), before)
        self.assertEqual([p.name for p in calls], ['candidate.crt', 'api.crt'])

    def test_postpublication_durability_error_never_runs_fallback(self):
        before = (self.authority / 'api.crt').read_bytes()
        calls = []
        with patch.object(broker.os, 'fsync', side_effect=[None, OSError('synthetic directory fsync failure')]):
            with self.assertRaises(broker.CertificatePublishedError):
                broker.with_certificate('api', self.authority, lambda p: calls.append(p),
                    now=datetime.now(UTC), force=True)
        self.assertNotEqual((self.authority / 'api.crt').read_bytes(), before)
        self.assertEqual([p.name for p in calls], ['candidate.crt'])

    def test_symlink_certificate_rejected(self):
        cert = self.authority / 'api.crt'
        target = self.authority / 'original.crt'
        cert.rename(target)
        cert.symlink_to(target)
        with self.assertRaisesRegex(ValueError, 'Private regular'):
            self.run_broker(force=True)

    def test_every_purpose_keeps_its_exact_expected_cn_and_key(self):
        for purpose in broker.ROLES:
            with self.subTest(purpose=purpose):
                if purpose != 'api':
                    self.leaf(purpose, days=2)
                key = (self.authority / (purpose + '.key')).read_bytes()
                calls = []
                result = broker.with_certificate(purpose, self.authority, lambda path: calls.append(path) or 'ok',
                                                  now=datetime.now(UTC), force=True)
                self.assertEqual(result, 'ok')
                self.assertEqual(len(calls), 1)
                broker.validate_leaf(self.authority / (purpose + '.crt'), self.authority / (purpose + '.key'), purpose)
                self.assertEqual((self.authority / (purpose + '.key')).read_bytes(), key)


if __name__ == '__main__':
    unittest.main()
