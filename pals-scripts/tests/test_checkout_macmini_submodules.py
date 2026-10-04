"""Real local Git/process checks; these do not certify a live GitHub/Keychain login."""

from __future__ import annotations

import importlib.util
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "checkout-macmini-submodules.py"
SPEC = importlib.util.spec_from_file_location("checkout_macmini", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
checkout = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checkout)


def git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        [
            "/usr/bin/git",
            "-c",
            "protocol.file.allow=always",
            "-c",
            "user.name=PALS Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "core.hooksPath=/dev/null",
            "-C",
            str(root),
            *arguments,
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
        env={
            **os.environ,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null",
        },
    )
    return result.stdout.strip()


def temporary_directory():
    return tempfile.TemporaryDirectory(
        prefix="pals-checkout-test-", dir=Path(tempfile.gettempdir()).resolve()
    )


class CheckoutGitBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = temporary_directory()
        cls.root = Path(cls.workspace.name)
        cls.origins = cls.root / "origins"
        cls.origins.mkdir()
        cls.parent = cls.root / "parent"
        cls.parent.mkdir()
        git(cls.parent, "init", "-b", "main")
        for name in (*checkout.deployment.SOURCES, "pals-nested"):
            origin = cls.origins / (name + ".git")
            origin.mkdir()
            git(origin, "init", "-b", "main")
            (origin / "component.txt").write_text(name + "\n")
            git(origin, "add", "component.txt")
            git(origin, "commit", "-m", "Fixture source")
        api = cls.origins / "pals-api.git"
        git(
            api,
            "submodule",
            "add",
            str(cls.origins / "pals-nested.git"),
            "nested/library",
        )
        git(
            api,
            "config",
            "-f",
            ".gitmodules",
            "submodule.nested/library.url",
            "https://github.com/AtsushiHosaka/pals-nested.git",
        )
        git(api, "add", ".gitmodules", "nested/library")
        git(api, "commit", "-m", "Pin nested fixture")
        for name in checkout.deployment.SOURCES:
            git(
                cls.parent, "submodule", "add", str(cls.origins / (name + ".git")), name
            )
            git(
                cls.parent,
                "config",
                "-f",
                ".gitmodules",
                f"submodule.{name}.url",
                f"git@github.com:AtsushiHosaka/{name}.git",
            )
        git(cls.parent, "add", ".gitmodules")
        git(cls.parent, "commit", "-m", "Pin approved fixture sources")
        cls.sha = git(cls.parent, "rev-parse", "HEAD")

    @classmethod
    def tearDownClass(cls):
        cls.workspace.cleanup()

    def setUp(self):
        self.workspace = temporary_directory()
        self.addCleanup(self.workspace.cleanup)
        self.root = Path(self.workspace.name)
        work = self.root / "_work"
        work.mkdir()
        temporary = work / "_temp"
        temporary.mkdir(mode=0o700)
        repository = work / "pals"
        repository.mkdir()
        self.source = repository / "pals"
        git(self.root, "clone", str(self.parent), str(self.source))
        self.gh = self.root / "gh-fixture"
        self.gh.write_text("#!/bin/sh\nexit 99\n")
        self.gh.chmod(0o700)
        self.environment = {
            **os.environ,
            "GITHUB_ACTIONS": "true",
            "RUNNER_ENVIRONMENT": "self-hosted",
            "GITHUB_WORKSPACE": str(self.source),
            "RUNNER_TEMP": str(temporary),
        }
        production_arguments = checkout.authenticated_git

        def local_mirrors(source):
            # Replace only the external GitHub transport with isolated file
            # mirrors. All pins, dirty checks, recursion and Git commands are real.
            return [
                *production_arguments(source),
                "-c",
                "protocol.file.allow=always",
                "-c",
                f"url.{self.origins.as_uri()}/.insteadOf=git@github.com:AtsushiHosaka/",
                "-c",
                f"url.{self.origins.as_uri()}/.insteadOf=https://github.com/AtsushiHosaka/",
            ]

        self.enterContext(mock.patch.dict(os.environ, self.environment, clear=True))
        self.enterContext(mock.patch.object(checkout.sys, "platform", "darwin"))
        self.enterContext(mock.patch.object(checkout, "GH", str(self.gh)))
        self.enterContext(
            mock.patch.object(checkout, "authenticated_git", side_effect=local_mirrors)
        )

    def test_real_git_checkout_preserves_exact_recursive_pins_and_reuses_workspace(
        self,
    ):
        result = checkout.execute(self.source, self.sha)
        self.assertEqual(result["status"], "checkout-passed")
        self.assertFalse(result["deployed"])
        self.assertEqual(
            set(result["source_commits"]), {"pals", *checkout.deployment.SOURCES}
        )
        self.assertEqual(git(self.source, "status", "--porcelain=v1"), "")
        nested = self.source / "pals-api/nested/library"
        self.assertEqual(
            git(nested, "rev-parse", "HEAD"),
            git(self.origins / "pals-nested.git", "rev-parse", "HEAD"),
        )
        self.assertEqual(checkout.execute(self.source, self.sha), result)

    def test_dirty_nested_checkout_rejected_without_discarding_changes(self):
        checkout.execute(self.source, self.sha)
        marker = self.source / "pals-api/nested/library/component.txt"
        marker.write_text("preserve local changes\n")
        with self.assertRaises(checkout.CheckoutError):
            checkout.execute(self.source, self.sha)
        self.assertEqual(marker.read_text(), "preserve local changes\n")

    def test_untracked_child_file_rejected(self):
        checkout.execute(self.source, self.sha)
        marker = self.source / "pals-agent/untracked.txt"
        marker.write_text("preserve user fixture\n")
        with self.assertRaises(checkout.CheckoutError):
            checkout.execute(self.source, self.sha)
        self.assertTrue(marker.exists())

    def test_wrong_parent_revision_rejected_before_fetch(self):
        with self.assertRaises(checkout.CheckoutError):
            checkout.execute(self.source, "a" * 40)
        self.assertFalse((self.source / "pals-api/.git").exists())

    def test_parent_dirty_checkout_rejected(self):
        (self.source / "user.txt").write_text("preserve\n")
        with self.assertRaises(checkout.CheckoutError):
            checkout.execute(self.source, self.sha)

    def test_unapproved_repository_url_rejected_before_fetch(self):
        git(
            self.source,
            "config",
            "-f",
            ".gitmodules",
            "submodule.pals-api.url",
            "https://github.com/unapproved/pals-api.git",
        )
        git(self.source, "add", ".gitmodules")
        git(self.source, "commit", "-m", "Unapproved fixture URL")
        with self.assertRaises(checkout.CheckoutError):
            checkout.execute(self.source, git(self.source, "rev-parse", "HEAD"))
        self.assertFalse((self.source / "pals-api/.git").exists())

    def test_extra_submodule_metadata_rejected(self):
        git(
            self.source,
            "config",
            "-f",
            ".gitmodules",
            "submodule.pals-api.update",
            "rebase",
        )
        git(self.source, "add", ".gitmodules")
        git(self.source, "commit", "-m", "Unexpected fixture strategy")
        with self.assertRaises(checkout.CheckoutError):
            checkout.execute(self.source, git(self.source, "rev-parse", "HEAD"))

    def test_non_runner_source_and_symlink_paths_rejected(self):
        with (
            mock.patch.dict(os.environ, {"GITHUB_WORKSPACE": str(self.parent)}),
            self.assertRaises(checkout.CheckoutError),
        ):
            checkout.execute(self.parent, self.sha)
        alias = self.source.parent / "alias"
        alias.symlink_to(self.source)
        with (
            mock.patch.dict(os.environ, {"GITHUB_WORKSPACE": str(alias)}),
            self.assertRaises(checkout.CheckoutError),
        ):
            checkout.execute(alias, self.sha)

    def test_dedicated_checkout_preserves_old_staged_submodule_deletions(self):
        checkout.execute(self.source, self.sha)
        old_module = self.source / "pals-agent"
        tracked = git(old_module, "ls-files").splitlines()[0]
        git(old_module, "rm", "--", tracked)
        staged = git(old_module, "diff", "--cached", "--name-status")
        dedicated = self.source / "macmini-deploy"
        git(self.root, "clone", str(self.parent), str(dedicated))

        result = checkout.execute(dedicated, self.sha)
        self.assertEqual(result["status"], "checkout-passed")
        self.assertEqual(git(old_module, "diff", "--cached", "--name-status"), staged)
        self.assertFalse((old_module / tracked).exists())

    def test_arbitrary_checkout_child_is_rejected(self):
        other = self.source / "other-checkout"
        git(self.root, "clone", str(self.parent), str(other))
        with self.assertRaises(checkout.CheckoutError):
            checkout.execute(other, self.sha)

    def test_url_specific_tls_bypass_or_headers_in_reused_checkout_rejected(self):
        checkout.execute(self.source, self.sha)
        nested = self.source / "pals-api/nested/library"
        for root, key, value in (
            (nested, "http.https://github.com/AtsushiHosaka/.sslVerify", "false"),
            (
                self.source,
                "http.https://github.com/.extraheader",
                "fixture-only-header",
            ),
        ):
            with self.subTest(root=root, key=key):
                git(root, "config", "--local", key, value)
                try:
                    with self.assertRaises(checkout.CheckoutError):
                        checkout.execute(self.source, self.sha)
                finally:
                    git(root, "config", "--local", "--unset", key)


class CredentialAndProcessBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.workspace = temporary_directory()
        self.addCleanup(self.workspace.cleanup)
        self.root = Path(self.workspace.name)
        self.environment = checkout.checkout_environment(dict(os.environ))

    def test_environment_removes_shadow_credentials_and_every_trace(self):
        unsafe = {
            "GH_TOKEN": "fixture",
            "GITHUB_TOKEN": "fixture",
            "GH_DEBUG": "api",
            "DEBUG": "1",
            "GIT_TRACE": "1",
            "GIT_TRACE_CURL": "1",
            "GIT_CURL_VERBOSE": "1",
            "GIT_ASKPASS": "unapproved-command",
            "GIT_CONFIG_COUNT": "1",
            "AWS_SESSION_TOKEN": "fixture",
        }
        result = checkout.checkout_environment({**os.environ, **unsafe})
        self.assertTrue(set(result).isdisjoint(unsafe))
        self.assertEqual(result["GIT_TERMINAL_PROMPT"], "0")
        self.assertEqual(result["PATH"].split(":")[0], "/usr/bin")

    def test_real_git_credential_protocol_uses_internal_helper_pipe_without_config_write(
        self,
    ):
        helper = self.root / "helper"
        helper.write_text(
            "#!/bin/sh\n"
            'test -z "${GH_TOKEN:-}${GITHUB_TOKEN:-}${GH_DEBUG:-}${GIT_TRACE:-}" || exit 9\n'
            'test "$1" = auth && test "$2" = git-credential && test "$3" = get || exit 8\n'
            "printf '%s\\n' 'username=fixture-user' 'password=fixture-only-value'\n"
        )
        helper.chmod(0o700)
        git(self.root, "init")
        config = self.root / ".git/config"
        before = config.read_bytes()
        with mock.patch.object(checkout, "GH", str(helper)):
            output = checkout.capture(
                [*checkout.authenticated_git(self.root), "credential", "fill"],
                checkout.checkout_environment(
                    {**os.environ, "GITHUB_TOKEN": "shadow-fixture"}
                ),
                input_text="protocol=https\nhost=github.com\n\n",
            )
        self.assertIn("password=fixture-only-value", output)
        self.assertEqual(config.read_bytes(), before)

    def assert_process_dead(self, pid):
        observed = subprocess.run(
            ["/bin/ps", "-p", str(pid), "-o", "stat="],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        self.assertTrue(
            observed.returncode != 0 or observed.stdout.strip().startswith("Z")
        )

    def create_process_tree(self):
        program = self.root / "process-tree.py"
        program.write_text(
            "import os,pathlib,subprocess,sys,time\n"
            "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'])\n"
            "pathlib.Path(sys.argv[1]).write_text(str(os.getpid())+' '+str(child.pid))\n"
            "time.sleep(30)\n"
        )
        return program

    def test_real_timeout_stops_parent_and_child_processes(self):
        marker = self.root / "pids"
        with self.assertRaises(subprocess.TimeoutExpired):
            checkout.capture(
                [sys.executable, str(self.create_process_tree()), str(marker)],
                self.environment,
                timeout=1,
            )
        for pid in map(int, marker.read_text().split()):
            self.assert_process_dead(pid)

    def test_real_cancellation_stops_parent_and_child_processes(self):
        marker = self.root / "pids"
        wrapper = (
            "import importlib.util,signal,sys\n"
            "spec=importlib.util.spec_from_file_location('fixture',sys.argv[1])\n"
            "module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)\n"
            "signal.signal(signal.SIGTERM,lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))\n"
            "try:\n"
            " module.capture([sys.executable,sys.argv[2],sys.argv[3]],module.checkout_environment({}),30)\n"
            "except KeyboardInterrupt:\n"
            " raise SystemExit(130)\n"
        )
        process = subprocess.Popen(
            [
                sys.executable,
                "-c",
                wrapper,
                str(SCRIPT),
                str(self.create_process_tree()),
                str(marker),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            deadline = time.monotonic() + 5
            while not marker.exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertTrue(marker.exists())
            process.send_signal(signal.SIGTERM)
            stdout, stderr = process.communicate(timeout=5)
            self.assertEqual(process.returncode, 130, (stdout, stderr))
            for pid in map(int, marker.read_text().split()):
                self.assert_process_dead(pid)
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=5)
            if marker.exists():
                for pid in map(int, marker.read_text().split()):
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass

    def test_failed_command_does_not_expose_captured_output(self):
        with self.assertRaises(checkout.CheckoutError) as observed:
            checkout.capture(
                [
                    sys.executable,
                    "-c",
                    "import sys; print('private-fixture-value'); sys.exit(1)",
                ],
                self.environment,
            )
        self.assertNotIn("private-fixture-value", str(observed.exception))


if __name__ == "__main__":
    unittest.main()
