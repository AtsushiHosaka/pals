"""Execute the workflow argument adapter with an isolated event and no host calls."""

import contextlib
import io
import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / '.github/workflows/qa-pro-operator-macmini.yml'
SUBJECT = 'aaaaaaaa-bbbb-7ccc-8ddd-eeeeeeeeeeee'
GRANT = '11111111-2222-4333-8444-555555555555'


class OperatorWorkflowTests(unittest.TestCase):
    def invoke(self, mode, subject='', grant_id='', stage_plan='', runtime_plan='', verified_job='', edge_plan=''):
        content = WORKFLOW.read_text()
        adapter = textwrap.dedent(content.split("<<'PY'\n", 1)[1].split('\n          PY', 1)[0])
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as temporary:
            event = Path(temporary) / 'event.json'
            event.write_text(json.dumps({'inputs': {'subject': subject, 'grant_id': grant_id, 'stage_plan_sha256': stage_plan, 'runtime_plan_sha256': runtime_plan, 'verified_job_id': verified_job, 'edge_plan_sha256': edge_plan}}))
            environment = {
                'PALS_OPERATOR_MODE': mode,
                'PALS_DEPLOY_REVISION': 'a' * 40,
                'GITHUB_EVENT_PATH': str(event),
            }
            with mock.patch.dict(os.environ, environment, clear=True), \
                    mock.patch.object(subprocess, 'run', return_value=mock.Mock(returncode=0)) as run, \
                    contextlib.redirect_stdout(output), self.assertRaises(SystemExit) as result:
                exec(compile(adapter, str(WORKFLOW), 'exec'), {})
        return result.exception.code, run, output.getvalue()

    def test_grant_accepts_cognito_v7_without_shell_or_identifier_environment(self):
        code, run, output = self.invoke('grant', SUBJECT, GRANT)
        self.assertEqual(code, 0)
        args = run.call_args.args[0]
        self.assertEqual(args[args.index('--subject') + 1], SUBJECT)
        self.assertEqual(args[args.index('--grant-id') + 1], GRANT)
        self.assertEqual(args[args.index('--expected-parent') + 1], 'a' * 40)
        self.assertNotIn(SUBJECT, run.call_args.kwargs['env'].values())
        self.assertEqual(output, '::add-mask::' + SUBJECT + '\n')
        self.assertNotIn('shell', run.call_args.kwargs)

    def test_inspect_install_and_recovery_do_not_pass_an_account(self):
        for mode in ('inspect', 'inspect-edge', 'install-edge', 'install', 'install-chat', 'recover'):
            code, run, output = self.invoke(mode)
            self.assertEqual(code, 0)
            self.assertNotIn('--subject', run.call_args.args[0])
            self.assertEqual(output, '')

    def test_edge_modes_use_the_separate_edge_entrypoint(self):
        for mode in ('inspect-edge', 'install-edge'):
            code, run, output = self.invoke(mode)
            self.assertEqual(code, 0)
            self.assertTrue(run.call_args.args[0][2].endswith('/pals-infra/host/macmini-edge/chat_attachments_operator.py'))
            self.assertEqual(output, '')

    def test_lean_modes_use_guarded_entrypoint_and_exact_plan(self):
        for mode, expected, plan in (('inspect-lean', 'plan', ''),
                                      ('stage-lean-worker', 'stage-worker', 'b' * 64),
                                      ('inspect-lean-support', 'plan-support', ''),
                                      ('refresh-lean-support', 'refresh-support', 'c' * 64)):
            code, run, output = self.invoke(mode, stage_plan=plan)
            self.assertEqual(code, 0)
            args = run.call_args.args[0]
            self.assertTrue(args[2].endswith('/pals-infra/host/macmini-deploy/full_runtime_operator.py'))
            self.assertEqual(args[args.index('--mode') + 1], expected)
            self.assertEqual('--expected-stage-plan-sha256' in args, bool(plan))
            self.assertNotIn('--aws-profile', args)
            self.assertEqual(output, '')

    def test_materials_edge_apply_requires_its_own_exact_plan(self):
        for mode, plan in (('plan-materials-edge', ''), ('install-materials-edge', 'd' * 64)):
            code, run, output = self.invoke(mode, edge_plan=plan)
            self.assertEqual(code, 0)
            args = run.call_args.args[0]
            self.assertTrue(args[2].endswith('/project_materials_operator.py'))
            self.assertEqual(args[args.index('--mode') + 1], mode)
            self.assertEqual('--expected-plan-sha256' in args, bool(plan))
            if plan:
                self.assertEqual(args[args.index('--expected-plan-sha256') + 1], plan)
            self.assertEqual(output, '')
        for mode, plan in (('install-materials-edge', ''), ('install-materials-edge', 'D' * 64),
                           ('install-materials-edge', '$(id)'), ('plan-materials-edge', 'd' * 64),
                           ('install-edge', 'd' * 64), ('enable-lean-runtime', 'd' * 64)):
            code, run, _ = self.invoke(mode, edge_plan=plan)
            self.assertIsInstance(code, str)
            run.assert_not_called()

    def test_invalid_stage_plan_never_reaches_host(self):
        for mode, plan in (('stage-lean-worker', ''), ('stage-lean-worker', 'B' * 64),
                           ('stage-lean-worker', '$(id)'), ('inspect-lean', 'b' * 64),
                           ('refresh-lean-support', ''), ('refresh-lean-support', 'C' * 64),
                           ('refresh-lean-support', '$(id)'), ('inspect-lean-support', 'c' * 64),
                           ('grant', 'b' * 64)):
            code, run, output = self.invoke(mode, stage_plan=plan)
            self.assertIsInstance(code, str)
            run.assert_not_called()
            self.assertEqual(output, '')
            if plan:
                self.assertNotIn(plan, code)

    def test_initial_runtime_and_queue_modes_are_distinct_and_plan_bound(self):
        for mode, filename, command, plan in (
            ('inspect-lean-runtime', 'initial_full_runtime_operator.py', 'plan', ''),
            ('enable-lean-runtime', 'initial_full_runtime_operator.py', 'apply', 'b' * 64),
            ('recover-lean-runtime', 'initial_full_runtime_operator.py', 'recover', ''),
            ('inspect-lean-queue', 'assessment_queue_operator.py', 'plan', ''),
            ('prepare-lean-queue', 'assessment_queue_operator.py', 'apply', 'c' * 64),
        ):
            with self.subTest(mode=mode):
                code, run, output = self.invoke(mode, runtime_plan=plan)
                self.assertEqual(code, 0)
                args = run.call_args.args[0]
                self.assertTrue(args[2].endswith('/' + filename))
                self.assertEqual(args[args.index('--mode') + 1], command)
                self.assertEqual('--expected-plan-sha256' in args, bool(plan))
                self.assertEqual(output, '')

    def test_runtime_or_queue_hash_cannot_cross_operation_boundaries(self):
        for mode, plan in (('enable-lean-runtime', ''), ('prepare-lean-queue', ''),
                           ('enable-lean-runtime', '$(id)'), ('prepare-lean-queue', 'B' * 64),
                           ('recover-lean-runtime', 'b' * 64), ('inspect-lean-runtime', 'b' * 64),
                           ('inspect-lean-queue', 'b' * 64), ('stage-lean-worker', 'b' * 64)):
            with self.subTest(mode=mode):
                code, run, _ = self.invoke(mode, runtime_plan=plan)
                self.assertIsInstance(code, str)
                run.assert_not_called()

    def test_finalization_requires_canonical_job_and_never_crosses_modes(self):
        code, run, output = self.invoke('finalize-lean-runtime', verified_job=GRANT)
        self.assertEqual(code, 0)
        args = run.call_args.args[0]
        self.assertTrue(args[2].endswith('/initial_full_runtime_operator.py'))
        self.assertEqual(args[args.index('--mode') + 1], 'finalize')
        self.assertEqual(args[args.index('--verified-job-id') + 1], GRANT)
        self.assertEqual(output, '')
        for mode, job in (('finalize-lean-runtime', ''), ('finalize-lean-runtime', '$(id)'),
                          ('finalize-lean-runtime', SUBJECT), ('inspect-lean-runtime', GRANT),
                          ('enable-lean-runtime', GRANT), ('grant', GRANT)):
            with self.subTest(mode=mode, job=job):
                code, run, output = self.invoke(mode, verified_job=job)
                self.assertIsInstance(code, str)
                run.assert_not_called()
                self.assertEqual(output, '')

    def test_lock_diagnostics_run_after_a_failed_inspection_only(self):
        step = WORKFLOW.read_text().split('      - name: Inspect fixed host interpreter availability\n', 1)[1]
        self.assertIn("if: always() && inputs.mode == 'inspect' && steps.parent-checkout.outcome == 'success'", step)
        self.assertIn('      - name: Checkout the exact parent\n        id: parent-checkout\n', WORKFLOW.read_text())
        self.assertIn('/usr/bin/python3 -B macmini-deploy/pals-scripts/inspect-macmini-lock.py', step)

    def test_invalid_inputs_never_reach_host_or_render_identifier(self):
        for mode, subject, grant in (
            ('grant', '$(id)', GRANT),
            ('grant', SUBJECT.upper(), GRANT),
            ('grant', SUBJECT, SUBJECT),
            ('inspect', SUBJECT, ''),
            ('install', '', GRANT),
            ('install-chat', SUBJECT, ''),
            ('inspect-edge', '', GRANT),
            ('install-edge', SUBJECT, ''),
            ('recover', SUBJECT, ''),
            ('unrecognized', SUBJECT, GRANT),
        ):
            code, run, output = self.invoke(mode, subject, grant)
            self.assertIsInstance(code, str)
            run.assert_not_called()
            self.assertEqual(output, '')
            if subject:
                self.assertNotIn(subject, code)


if __name__ == '__main__':
    unittest.main()
