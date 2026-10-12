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
    def invoke(self, mode, subject='', grant_id=''):
        content = WORKFLOW.read_text()
        adapter = textwrap.dedent(content.split("<<'PY'\n", 1)[1].split('\n          PY', 1)[0])
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as temporary:
            event = Path(temporary) / 'event.json'
            event.write_text(json.dumps({'inputs': {'subject': subject, 'grant_id': grant_id}}))
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
