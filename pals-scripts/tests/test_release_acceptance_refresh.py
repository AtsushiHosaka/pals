"""Production refresh authority/fingerprint tests; no browser, credentials or AWS calls."""
import importlib.util
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('acceptance_refresh_gate', HERE / 'release-acceptance.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def contract():
    return {'target': 'production', 'runtime': {
        role: {'ssm': {'profile': 'pals-prod-member', 'region': 'ap-northeast-1',
                       'account_id': '123456789012', 'instance_id': 'not-used'}}
        for role in gate.ROLES}}


class AcceptanceRefreshTests(unittest.TestCase):
    def test_only_consistent_production_remote_contract_supplies_fixed_guard(self):
        result = gate.browser_refresh_policy(contract())
        self.assertEqual(result, {'python': sys.executable,
            'guard': str(HERE / 'release-cognito-refresh-policy.py'),
            'region': 'ap-northeast-1', 'account_id': '123456789012'})
        staging = contract(); staging['target'] = 'staging'
        self.assertIsNone(gate.browser_refresh_policy(staging))
        local = contract(); local['runtime'] = {role: {'context': 'local'} for role in gate.ROLES}
        self.assertIsNone(gate.browser_refresh_policy(local))

    def test_mixed_or_conflicting_remote_authority_refuses(self):
        for change in ({'context': 'local'}, {'ssm': {'profile': 'pals-prod-member',
                'region': 'ap-northeast-1', 'account_id': '999999999999'}}):
            value = contract(); value['runtime']['web'] = change
            with self.assertRaisesRegex(gate.Refusal, 'refresh_remote_identity_inconsistent'):
                gate.browser_refresh_policy(value)
        value = contract()
        for binding in value['runtime'].values(): binding['ssm']['profile'] = 'other'
        with self.assertRaisesRegex(gate.Refusal, 'refresh_remote_identity_invalid'):
            gate.browser_refresh_policy(value)

    def test_fingerprint_binds_guard_and_shared_credential_holder(self):
        files = (HERE / 'release-acceptance.py', HERE / 'release-acceptance-browser.cjs',
                 HERE / 'release-post-request-browser.cjs', HERE / 'release-cognito-refresh-policy.py')
        expected = gate.digest(b''.join(p.name.encode() + b'\0' + p.read_bytes() + b'\0' for p in files))
        self.assertEqual(gate.runner_fingerprint(), expected)


if __name__ == '__main__': unittest.main()
