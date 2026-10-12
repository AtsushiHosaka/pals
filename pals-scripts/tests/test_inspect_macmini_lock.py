import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

spec = importlib.util.spec_from_file_location('lock_probe', Path(__file__).parents[1] / 'inspect-macmini-lock.py')
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class LockInspectionTests(unittest.TestCase):
    def test_reports_known_deployer_without_private_command(self):
        raw = '1 123 2-03:04:05 /private/python pals-scripts/deploy-macmini.py --revision ' + 'a' * 40 + ' --config /private/secret-url --password hidden'
        result = probe.owner_summary(123, raw)
        self.assertTrue(result['command_mentions_deployer'])
        self.assertEqual(result['elapsed_seconds'], 2 * 86400 + 3 * 3600 + 4 * 60 + 5)
        self.assertEqual(result['claimed_revision'], 'a' * 40)
        self.assertNotIn('secret', json.dumps(result))
        self.assertNotIn('hidden', json.dumps(result))

    def test_other_process_does_not_expose_arguments_or_revision(self):
        result = probe.owner_summary(9, '1 9 01:02 /private/unknown --revision ' + 'a' * 40 + ' --secret private')
        self.assertFalse(result['command_mentions_deployer'])
        self.assertIsNone(result['claimed_revision'])
        self.assertEqual(result['elapsed_seconds'], 62)
        self.assertNotIn('private', json.dumps(result))

    def test_argument_mentions_are_reported_without_claiming_process_identity(self):
        result = probe.owner_summary(9, '1 9 01:02 /bin/cat pals-scripts/deploy-macmini.py')
        self.assertTrue(result['command_mentions_deployer'])
        self.assertNotIn('recognized_deployer', result)

    def test_malformed_metadata_returns_only_closed_status(self):
        for raw in ('secret-value', '1 nope 00:03 private', '1 2 secret private'):
            self.assertEqual(probe.owner_summary(7, raw), {'pid': 7, 'status': 'unavailable'})

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.state = self.root / 'state'
        self.state.mkdir()
        for name in ('deploy.lock', 'host-update.lock'):
            (self.state / name).touch(mode=0o600)
        for name in ('deploy-config.json', 'controller-policy.json'):
            (self.root / name).write_text(json.dumps({'state_dir': str(self.state)}))

    def result(self, returncode=1, stdout=b'', stderr=b''):
        return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)

    def test_main_observes_both_fixed_locks_and_pending_flag(self):
        (self.state / 'normal-update-pending.json').touch()
        with mock.patch.object(probe, 'ROOT', self.root), mock.patch.object(probe.sys, 'platform', 'darwin'), mock.patch.object(probe.subprocess, 'run', return_value=self.result()) as run:
            result = probe.main()
        self.assertTrue(result['pending_update_present'])
        self.assertEqual(set(result['locks']), {'deploy.lock', 'host-update.lock'})
        for name, observed in result['locks'].items():
            self.assertEqual(observed['status'], 'observed-lock-openers')
            self.assertTrue(observed['empty_openers_observed'])
            self.assertEqual(observed['processes'], [])
        self.assertEqual([call.args[0] for call in run.call_args_list], [
            ['/usr/sbin/lsof', '-t', '--', str(self.state / 'deploy.lock')],
            ['/usr/sbin/lsof', '-t', '--', str(self.state / 'host-update.lock')]])
        self.assertNotIn(str(self.state), json.dumps(result))

    def test_missing_lock_is_not_empty_openers_or_lsof(self):
        (self.state / 'host-update.lock').unlink()
        with mock.patch.object(probe.subprocess, 'run') as run:
            result = probe.inspect_lock(self.state, 'host-update.lock')
        self.assertEqual(result, {'status': 'missing', 'code': 'lock_file_missing'})
        run.assert_not_called()

    def test_lsof_rc1_stderr_is_error_not_empty_observation(self):
        for code in (0, 1, 2):
            with self.subTest(code=code), mock.patch.object(probe.subprocess, 'run', return_value=self.result(code, stderr=b'private path permission denied')):
                result = probe.inspect_lock(self.state, 'deploy.lock')
            self.assertEqual(result, {'status': 'unavailable', 'code': 'lsof_stderr_present'})
            self.assertNotIn('private', json.dumps(result))

    def test_lsof_failure_timeout_invalid_output_are_closed(self):
        cases = [(self.result(2), 'lsof_failed'),
                 (self.result(1, stdout=b'123'), 'lsof_inconsistent_result'),
                 (self.result(0, stdout=b'private credentials'), 'lsof_invalid_pids'),
                 (self.result(0, stdout=b'\xff'), 'lsof_invalid_pids'),
                 (self.result(0, stdout=b'x' * 65537), 'lsof_output_limit')]
        for response, code in cases:
            with self.subTest(code=code), mock.patch.object(probe.subprocess, 'run', return_value=response):
                self.assertEqual(probe.inspect_lock(self.state, 'deploy.lock'), {'status': 'unavailable', 'code': code})
        with mock.patch.object(probe.subprocess, 'run', side_effect=subprocess.TimeoutExpired('private argv', 5)):
            self.assertEqual(probe.inspect_lock(self.state, 'deploy.lock'), {'status': 'unavailable', 'code': 'lsof_unavailable'})

    def test_main_closes_error_for_one_lock_without_losing_other(self):
        with mock.patch.object(probe, 'ROOT', self.root), mock.patch.object(probe.sys, 'platform', 'darwin'), mock.patch.object(probe.subprocess, 'run', side_effect=[self.result(1, stderr=b'private error'), self.result(1)]):
            result = probe.main()
        self.assertEqual(result['locks']['deploy.lock']['code'], 'lsof_stderr_present')
        self.assertTrue(result['locks']['host-update.lock']['empty_openers_observed'])

    def test_holder_metadata_stays_closed_and_ps_errors_are_unavailable(self):
        calls = [self.result(0, stdout=b'123\n123\n456\n'),
                 self.result(0, stdout=b'1 123 00:30 /private/python pals-scripts/deploy-macmini.py --password hidden'),
                 self.result(0, stdout=b'1 456 00:30 private command', stderr=b'private warning')]
        with mock.patch.object(probe.subprocess, 'run', side_effect=calls) as run:
            result = probe.inspect_lock(self.state, 'host-update.lock')
        self.assertFalse(result['empty_openers_observed'])
        self.assertEqual([row['pid'] for row in result['processes']], [123, 456])
        self.assertEqual(result['processes'][1], {'pid': 456, 'status': 'unavailable'})
        for forbidden in ('private', 'hidden', 'password', 'flock', 'kill'):
            self.assertNotIn(forbidden, json.dumps(result))
        self.assertEqual(len(run.call_args_list), 3)

    def test_link_or_insecure_file_does_not_trigger_lsof(self):
        path = self.state / 'deploy.lock'
        path.unlink()
        path.symlink_to(self.state / 'host-update.lock')
        with mock.patch.object(probe.subprocess, 'run') as run:
            self.assertEqual(probe.inspect_lock(self.state, 'deploy.lock')['code'], 'lock_metadata_invalid')
        run.assert_not_called()
        path.unlink()
        path.touch(mode=0o644)
        with mock.patch.object(probe.subprocess, 'run') as run:
            self.assertEqual(probe.inspect_lock(self.state, 'deploy.lock')['code'], 'lock_metadata_invalid')
        run.assert_not_called()

    def test_state_mismatch_stops_before_lsof(self):
        (self.root / 'controller-policy.json').write_text(json.dumps({'state_dir': '/different/private/state'}))
        with mock.patch.object(probe, 'ROOT', self.root), mock.patch.object(probe.sys, 'platform', 'darwin'), mock.patch.object(probe.subprocess, 'run') as run:
            self.assertEqual(probe.main(), {'status': 'unavailable', 'code': 'state_directory_mismatch'})
        run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
