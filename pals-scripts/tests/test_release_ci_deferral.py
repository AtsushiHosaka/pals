"""Owner-authorized pending CI remains distinguishable from successful CI."""
import copy
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('ci_deferral', Path(__file__).resolve().parents[1] / 'release-source-checks.py')
C = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(C)
NOW = dt.datetime(2026, 11, 19, 6, tzinfo=dt.timezone.utc)


def run(**changes):
    value = {'id': 2, 'name': 'release-cycle-regression', 'app': {'id': 15368},
             'status': 'queued', 'conclusion': None,
             'verified_workflow_path': C.WORKFLOWS['pals-infra']}
    value.update(changes)
    return value


class OwnerCITest(unittest.TestCase):
    def setUp(self):
        self.candidate = {'source_commits': {repo: 'b' * 40 for repo in C.CHECKS}}
        self.raw = json.dumps(self.candidate).encode()
        self.record = {'version': 1, 'purpose': 'release-ci-wait-deferral', 'owner': 'AtsushiHosaka',
                       'decision_url': 'https://github.com/AtsushiHosaka/pals/issues/422',
                       'decision': 'ciまたなくていい、すぐリリース！',
                       'candidate_manifest_sha256': hashlib.sha256(self.raw).hexdigest(),
                       'source_commits': copy.deepcopy(self.candidate['source_commits']),
                       'repositories': ['pals-infra'], 'created_at_utc': '2026-11-19T05:40:00Z',
                       'expires_at_utc': '2026-11-19T08:00:00Z',
                       'resume_condition': 'recheck_latest_exact_ci_before_issue_close'}

    def read(self, value=None, raw=None, expected=None):
        encoded = json.dumps(self.record if value is None else value).encode() if raw is None else raw
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'decision.json'
            path.write_bytes(encoded)
            return C.read_owner_deferral(path, expected or hashlib.sha256(encoded).hexdigest(), self.raw, self.candidate, now=NOW)

    def test_frozen_exact_record_allows_only_named_repository(self):
        self.assertEqual(self.read(), frozenset({'pals-infra'}))

    def test_wrong_hash_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'hash_differs'):
            self.read(expected='0' * 64)

    def test_decision_candidate_sources_and_scope_are_exact(self):
        changes = {'version': True, 'purpose': 'generic', 'owner': 'someone',
                   'decision_url': 'https://example.com', 'decision': 'release',
                   'candidate_manifest_sha256': '0' * 64, 'source_commits': {},
                   'repositories': ['pals-api'], 'resume_condition': 'never'}
        for key, value in changes.items():
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'binding_invalid'):
                self.read({**self.record, key: value})
        for repositories in ([], ['pals-infra', 'pals-infra'], [None]):
            with self.subTest(repositories=repositories), self.assertRaises(ValueError):
                self.read({**self.record, 'repositories': repositories})

    def test_duplicate_or_unknown_fields_are_refused(self):
        with self.assertRaisesRegex(ValueError, 'duplicate_key'):
            self.read(raw=b'{"version":1,"version":1}')
        with self.assertRaises(ValueError):
            self.read({**self.record, 'extra': 'ignored'})

    def test_expired_future_long_and_offset_windows_are_refused(self):
        for change in ({'expires_at_utc': '2026-11-19T06:00:00Z'},
                       {'created_at_utc': '2026-11-19T06:00:01Z'},
                       {'expires_at_utc': '2026-11-20T06:00:00Z'},
                       {'expires_at_utc': '2026-11-19T08:00:00+00:00'}):
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, 'window'):
                self.read({**self.record, **change})

    def test_pending_deferral_never_uses_old_green(self):
        old = run(id=1, status='completed', conclusion='success')
        for status in ('queued', 'in_progress'):
            self.assertEqual(C.require_check([old, run(status=status)], 'release-cycle-regression', C.WORKFLOWS['pals-infra'], defer_pending=True), 'pending_deferred_by_owner')
            with self.assertRaises(ValueError):
                C.require_check([old, run(status=status)], 'release-cycle-regression', C.WORKFLOWS['pals-infra'])

    def test_failed_cancelled_skipped_missing_foreign_checks_cannot_be_deferred(self):
        for conclusion in ('failure', 'cancelled', 'skipped', 'neutral', 'timed_out', None):
            with self.subTest(conclusion=conclusion), self.assertRaises(ValueError):
                C.require_check([run(status='completed', conclusion=conclusion)], 'release-cycle-regression', C.WORKFLOWS['pals-infra'], defer_pending=True)
        for runs in ([], [run(app={'id': 1})], [run(verified_workflow_path='other.yml')]):
            with self.subTest(runs=runs), self.assertRaises(ValueError):
                C.require_check(runs, 'release-cycle-regression', C.WORKFLOWS['pals-infra'], defer_pending=True)

    def test_rows_and_real_success_remain_distinct(self):
        old = {'source_commits': {repo: 'a' * 40 for repo in C.CHECKS}}
        candidate = {'source_commits': {**old['source_commits'], 'pals-infra': 'b' * 40}}
        rows = C.check_sources(candidate, old, lambda *args: [run()], deferred_repositories=self.read())
        self.assertEqual([row['status'] for row in rows if row['repository'] == 'pals-infra'], ['pending_deferred_by_owner'])
        rows = C.check_sources(candidate, old, lambda *args: [run(status='completed', conclusion='success')], deferred_repositories=self.read())
        self.assertEqual([row['status'] for row in rows if row['repository'] == 'pals-infra'], ['actual_required_check_passed'])

    def test_parent_contract_check_cannot_be_missing_under_deferral(self):
        old = {'source_commits': {repo: 'a' * 40 for repo in C.CHECKS}}
        candidate = {'source_commits': {**old['source_commits'], 'pals': 'b' * 40}}
        with self.assertRaisesRegex(ValueError, 'required_check_missing:release-acceptance-contracts'):
            C.check_sources(candidate, old, lambda *args: [run(name='repository-safety', verified_workflow_path=C.WORKFLOWS['pals'])], deferred_repositories=frozenset({'pals'}))


if __name__ == '__main__':
    unittest.main()
