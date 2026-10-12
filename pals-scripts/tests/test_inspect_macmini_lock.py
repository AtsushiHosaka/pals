import importlib.util
import json
import unittest
from pathlib import Path

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


if __name__ == '__main__':
    unittest.main()
