"""Main supersession and actual workflow-shell failure/skip contracts."""

from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "check_macmini_main", ROOT / "pals-scripts/check-macmini-main.py"
)
assert SPEC is not None and SPEC.loader is not None
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)
REQUESTED = "a" * 40
NEWER = "b" * 40


def response(sha=REQUESTED):
    return json.dumps(
        {"ref": "refs/heads/main", "object": {"type": "commit", "sha": sha}}
    )


class MainGuardTests(unittest.TestCase):
    def test_current_and_superseded_never_substitute_the_requested_sha(self):
        for observed, expected in ((REQUESTED, "current"), (NEWER, "superseded")):
            with (
                self.subTest(expected=expected),
                mock.patch.object(
                    guard.checkout, "capture", return_value=response(observed)
                ),
            ):
                self.assertEqual(
                    guard.check_main(REQUESTED, {}, auth="host-gh"), expected
                )

    def test_fixed_host_repo_ref_and_saved_login_environment(self):
        environment = {
            "HOME": "/fixture/host-home",
            "GH_TOKEN": "private-gh-token",
            "GITHUB_TOKEN": "private-runner-token",
            "GH_HOST": "attacker.invalid",
            "GH_DEBUG": "api",
            "HTTPS_PROXY": "https://attacker.invalid",
            "GIT_TRACE": "1",
            "PATH": "/untrusted/bin",
        }
        with mock.patch.object(
            guard.checkout, "capture", return_value=response()
        ) as capture:
            self.assertEqual(
                guard.check_main(REQUESTED, environment, auth="host-gh"), "current"
            )
        arguments, passed_environment = capture.call_args.args
        self.assertEqual(
            arguments,
            [
                guard.checkout.GH,
                "api",
                "--hostname",
                "github.com",
                "--method",
                "GET",
                "repos/AtsushiHosaka/pals/git/ref/heads/main",
            ],
        )
        self.assertEqual(passed_environment["HOME"], environment["HOME"])
        self.assertEqual(passed_environment["PATH"], guard.checkout.NATIVE_PATH)
        for key in (
            "GH_TOKEN",
            "GITHUB_TOKEN",
            "GH_HOST",
            "GH_DEBUG",
            "HTTPS_PROXY",
            "GIT_TRACE",
        ):
            self.assertNotIn(key, passed_environment)
        self.assertEqual(capture.call_args.kwargs, {"timeout": 30})

    def test_invalid_requested_sha_fails_before_api_access(self):
        with mock.patch.object(guard.checkout, "capture") as capture:
            for revision in ("main", "", REQUESTED + "\n", "A" * 40, "a" * 39):
                with (
                    self.subTest(revision=revision),
                    self.assertRaises(guard.MainCheckError),
                ):
                    guard.check_main(revision, {}, auth="host-gh")
            capture.assert_not_called()

    def test_bad_ref_type_sha_missing_duplicate_and_non_json_fail_closed(self):
        values = [
            "",
            "not json: private-token",
            "[]",
            "{}",
            response().replace("refs/heads/main", "refs/heads/other"),
            response().replace('"commit"', '"tag"'),
            response("A" * 40),
            response("main"),
            json.dumps({"ref": "refs/heads/main", "object": None}),
            '{"ref":"refs/heads/main","ref":"refs/heads/main","object":{}}',
            '{"ref":"refs/heads/main","object":{"type":"commit","sha":"'
            + REQUESTED
            + '","sha":"'
            + NEWER
            + '"}}',
            " " * 65537,
        ]
        for value in values:
            with (
                self.subTest(value=value[:40]),
                mock.patch.object(guard.checkout, "capture", return_value=value),
                self.assertRaises(guard.MainCheckError),
            ):
                guard.check_main(REQUESTED, {}, auth="host-gh")

    def test_api_failures_and_private_response_never_reach_cli_outputs(self):
        failures = [
            guard.checkout.CheckoutError("private token in subprocess failure"),
            OSError("private path"),
            UnicodeDecodeError("utf-8", b"private\xffresponse", 7, 8, "private reason"),
            subprocess.TimeoutExpired(
                "gh", 30, output="private stdout", stderr="private stderr"
            ),
        ]
        for failure in failures:
            with (
                self.subTest(failure=type(failure).__name__),
                mock.patch.object(guard.checkout, "capture", side_effect=failure),
            ):
                stdout, stderr = io.StringIO(), io.StringIO()
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    result = guard.main(["--revision", REQUESTED, "--auth", "host-gh"])
                self.assertEqual(result, 1)
                self.assertEqual(stdout.getvalue(), "")
                self.assertEqual(
                    stderr.getvalue(),
                    "Mac mini main check failed; deployment is blocked.\n",
                )
        with mock.patch.object(
            guard.checkout, "capture", return_value="private non-JSON response"
        ):
            stdout, stderr = io.StringIO(), io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                self.assertEqual(
                    guard.main(["--revision", REQUESTED, "--auth", "host-gh"]), 1
                )
            self.assertNotIn("private", stdout.getvalue() + stderr.getvalue())


class RepositoryTokenTests(unittest.TestCase):
    def api_response(self, content, *, status=200, url=guard.MAIN_API_URL):
        result = mock.MagicMock()
        result.__enter__.return_value = result
        result.getcode.return_value = status
        result.geturl.return_value = url
        result.read.return_value = content
        return result

    def test_step_token_uses_fixed_https_get_and_never_saved_login(self):
        for observed, expected in ((REQUESTED, "current"), (NEWER, "superseded")):
            opener = mock.Mock()
            remote = self.api_response(response(observed).encode())
            opener.open.return_value = remote
            with (
                self.subTest(status=expected),
                mock.patch.object(
                    guard.urllib.request, "build_opener", return_value=opener
                ) as build,
                mock.patch.object(guard.checkout, "capture") as capture,
            ):
                self.assertEqual(
                    guard.check_main(
                        REQUESTED,
                        {
                            "PALS_MAIN_READ_TOKEN": "explicit-step-token",
                            "GH_TOKEN": "ambient-token",
                        },
                        auth="repository-token",
                    ),
                    expected,
                )
                capture.assert_not_called()
            proxy, redirects = build.call_args.args
            self.assertEqual(proxy.proxies, {})
            self.assertIsInstance(redirects, guard.NoRedirect)
            request = opener.open.call_args.args[0]
            self.assertEqual(
                request.full_url,
                "https://api.github.com/repos/AtsushiHosaka/pals/git/ref/heads/main",
            )
            self.assertEqual(request.get_method(), "GET")
            self.assertEqual(
                request.get_header("Authorization"), "Bearer explicit-step-token"
            )
            self.assertEqual(opener.open.call_args.kwargs, {"timeout": 30})
            remote.read.assert_called_once_with(65537)

    def test_missing_or_invalid_explicit_token_cannot_fallback_to_ambient_login(self):
        with (
            mock.patch.object(guard.urllib.request, "build_opener") as build,
            mock.patch.object(guard.checkout, "capture") as capture,
        ):
            for token in (None, "", " ", "token\r\ninjection", "x" * 4097):
                environment = {
                    "GH_TOKEN": "ambient-gh",
                    "GITHUB_TOKEN": "ambient-runner",
                }
                if token is not None:
                    environment["PALS_MAIN_READ_TOKEN"] = token
                with self.subTest(token=token), self.assertRaises(guard.MainCheckError):
                    guard.check_main(REQUESTED, environment, auth="repository-token")
            build.assert_not_called()
            capture.assert_not_called()

    def test_host_login_drops_explicit_step_token_and_invalid_auth_fails_closed(self):
        with (
            mock.patch.object(
                guard.checkout, "capture", return_value=response()
            ) as capture,
            mock.patch.object(guard.urllib.request, "build_opener") as build,
        ):
            self.assertEqual(
                guard.check_main(
                    REQUESTED, {"PALS_MAIN_READ_TOKEN": "unused-token"}, auth="host-gh"
                ),
                "current",
            )
            self.assertNotIn("PALS_MAIN_READ_TOKEN", capture.call_args.args[1])
            with self.assertRaises(guard.MainCheckError):
                guard.check_main(REQUESTED, {}, auth="ambient-fallback")
            build.assert_not_called()
            self.assertEqual(capture.call_count, 1)

    def test_redirect_http_failure_oversize_and_bad_body_never_authorize(self):
        cases = [
            self.api_response(response().encode(), status=401),
            self.api_response(response().encode(), url="https://attacker.invalid/main"),
            self.api_response(b"x" * 65537),
            self.api_response(b"private non-JSON response"),
        ]
        for remote in cases:
            opener = mock.Mock()
            opener.open.return_value = remote
            with (
                mock.patch.object(
                    guard.urllib.request, "build_opener", return_value=opener
                ),
                self.assertRaises(guard.MainCheckError),
            ):
                guard.check_main(
                    REQUESTED,
                    {"PALS_MAIN_READ_TOKEN": "explicit-token"},
                    auth="repository-token",
                )
        self.assertIsNone(
            guard.NoRedirect().redirect_request(
                None, None, 302, "Found", {}, "https://attacker.invalid"
            )
        )

    def test_http_exception_and_invalid_utf8_cli_only_print_fixed_error(self):
        for outcome in (
            guard.http.client.IncompleteRead(b"private partial body", 100),
            urllib.error.HTTPError(
                guard.MAIN_API_URL,
                401,
                "private failure",
                {},
                io.BytesIO(b"private body"),
            ),
            urllib.error.URLError("private network failure"),
            self.api_response(b"private\xffresponse"),
        ):
            opener = mock.Mock()
            if isinstance(outcome, Exception):
                opener.open.side_effect = outcome
            else:
                opener.open.return_value = outcome
            with (
                mock.patch.object(
                    guard.urllib.request, "build_opener", return_value=opener
                ),
                mock.patch.dict(
                    guard.os.environ,
                    {"PALS_MAIN_READ_TOKEN": "explicit-token"},
                    clear=True,
                ),
            ):
                stdout, stderr = io.StringIO(), io.StringIO()
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    self.assertEqual(
                        guard.main(
                            ["--revision", REQUESTED, "--auth", "repository-token"]
                        ),
                        1,
                    )
                self.assertEqual(stdout.getvalue(), "")
                self.assertEqual(
                    stderr.getvalue(),
                    "Mac mini main check failed; deployment is blocked.\n",
                )


class WorkflowShellGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        workflow = (ROOT / ".github/workflows/deploy-macmini.yml").read_text()
        step = workflow.split(
            "      - name: Skip a parent revision superseded by main\n", 1
        )[1]
        step, controller = step.split(
            "      - name: Run the host deployment controller contract\n", 1
        )
        cls.shell = "\n".join(
            line[10:] for line in step.split("        run: |\n", 1)[1].splitlines()
        )
        # GitHub evaluates this expression before running the controller/receipt code.
        if (
            "if: env.PALS_MACMINI_MODE != 'deploy' || steps.main-head.outputs.deploy == 'true'"
            not in controller
        ):
            raise AssertionError("Superseded results must gate the controller step")

    def run_workflow_guard(self, program):
        with tempfile.TemporaryDirectory(prefix="pals-main-guard-test-") as temporary:
            root = Path(temporary)
            (root / "pals-scripts").mkdir()
            (root / "pals-scripts/check-macmini-main.py").write_text(program)
            output, summary = root / "output", root / "summary"
            process = subprocess.run(
                ["/bin/bash", "-c", self.shell],
                cwd=root,
                env={
                    "PATH": "/usr/bin:/bin",
                    "PALS_DEPLOY_REVISION": REQUESTED,
                    "PALS_MACMINI_CHECKOUT_AUTH": "host-gh",
                    "GITHUB_OUTPUT": str(output),
                    "GITHUB_STEP_SUMMARY": str(summary),
                },
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            return (
                process,
                output.read_text() if output.exists() else "",
                summary.read_text() if summary.exists() else "",
            )

    def test_current_permits_controller_and_superseded_is_explicit_skip(self):
        process, output, summary = self.run_workflow_guard('print("current")\n')
        self.assertEqual(process.returncode, 0)
        self.assertEqual(output, "deploy=true\n")
        self.assertEqual(summary, "")
        process, output, summary = self.run_workflow_guard('print("superseded")\n')
        self.assertEqual(process.returncode, 0)
        self.assertEqual(output, "deploy=false\n")
        self.assertIn("No controller was started", summary)
        self.assertIn("Deployment skipped", process.stdout)

    def test_api_failure_or_unknown_status_cannot_authorize_controller(self):
        for program in ("raise SystemExit(1)\n", 'print("unknown")\n'):
            process, output, summary = self.run_workflow_guard(program)
            self.assertNotEqual(process.returncode, 0)
            self.assertEqual(output, "")
            self.assertEqual(summary, "")


if __name__ == "__main__":
    unittest.main()
