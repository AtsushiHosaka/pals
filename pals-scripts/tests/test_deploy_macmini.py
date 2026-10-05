"""Local boundary checks; these never deploy to or certify a live Mac mini."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

SPEC = importlib.util.spec_from_file_location(
    "deploy_macmini", Path(__file__).resolve().parents[1] / "deploy-macmini.py"
)
assert SPEC is not None and SPEC.loader is not None
deploy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(deploy)


def temporary_directory():
    # Canonical paths matter because macOS /tmp itself is a symlink.
    return tempfile.TemporaryDirectory(
        prefix="pals-deploy-test-", dir=Path(tempfile.gettempdir()).resolve()
    )


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        [
            "git",
            "-c",
            "protocol.file.allow=always",
            "-c",
            "user.name=PALS Test",
            "-c",
            "user.email=pals-test@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "core.hooksPath=/dev/null",
            "-C",
            str(root),
            *args,
        ],
        check=True,
        text=True,
        capture_output=True,
        timeout=30,
        env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0"},
    )
    return result.stdout.strip()


class SourceRevisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = temporary_directory()
        cls.root = Path(cls.workspace.name).resolve()
        cls.parent = cls.root / "parent"
        cls.parent.mkdir()
        git(cls.parent, "init", "-b", "main")
        for name in deploy.SOURCES:
            origin = cls.root / (name + "-origin")
            origin.mkdir()
            git(origin, "init", "-b", "main")
            (origin / "component.txt").write_text(name + "\n")
            git(origin, "add", "component.txt")
            git(origin, "commit", "-m", "Fixture component")
            git(cls.parent, "submodule", "add", str(origin), name)
        git(cls.parent, "commit", "-m", "Pin six local components")
        cls.sha = git(cls.parent, "rev-parse", "HEAD")

    @classmethod
    def tearDownClass(cls):
        cls.workspace.cleanup()

    def setUp(self):
        self.workspace = temporary_directory()
        self.addCleanup(self.workspace.cleanup)
        self.root = Path(self.workspace.name).resolve()
        self.checkout = self.root / "checkout"
        git(
            self.root,
            "clone",
            "--recurse-submodules",
            str(self.parent),
            str(self.checkout),
        )

    def test_exact_parent_and_six_submodule_pins(self):
        revisions = deploy.source_revisions(self.checkout, self.sha)
        self.assertEqual(set(revisions), {"pals", *deploy.SOURCES})
        for name in deploy.SOURCES:
            self.assertEqual(
                revisions[name], git(self.checkout / name, "rev-parse", "HEAD")
            )

    def test_wrong_parent_sha_rejected(self):
        with self.assertRaises(deploy.DeploymentError):
            deploy.source_revisions(self.checkout, "0" * 40)

    def test_dirty_parent_rejected(self):
        (self.checkout / "unexpected.txt").write_text("user work\n")
        with self.assertRaises(deploy.DeploymentError):
            deploy.source_revisions(self.checkout, self.sha)

    def test_dirty_submodule_rejected(self):
        (self.checkout / "pals-api" / "component.txt").write_text("changed\n")
        with self.assertRaises(deploy.DeploymentError):
            deploy.source_revisions(self.checkout, self.sha)

    def test_uninitialized_submodule_rejected(self):
        git(self.checkout, "submodule", "deinit", "--force", "pals-api")
        with self.assertRaises(deploy.DeploymentError):
            deploy.source_revisions(self.checkout, self.sha)

    def test_wrong_submodule_sha_rejected(self):
        component = self.checkout / "pals-agent"
        (component / "component.txt").write_text("new component commit\n")
        git(component, "add", "component.txt")
        git(component, "commit", "-m", "Unpinned candidate")
        with self.assertRaises(deploy.DeploymentError):
            deploy.source_revisions(self.checkout, self.sha)

    def test_deep_dirty_submodule_hidden_by_ignore_settings_rejected(self):
        component = self.checkout / "pals-api"
        git(
            component,
            "submodule",
            "add",
            str(self.parent.parent / "pals-webfront-origin"),
            "nested/one",
        )
        nested = component / "nested/one"
        git(
            nested,
            "submodule",
            "add",
            str(self.parent.parent / "pals-agent-origin"),
            "second",
        )
        git(nested, "commit", "-m", "Pin deeply nested component")
        git(component, "add", ".gitmodules", "nested/one")
        git(component, "commit", "-m", "Pin nested component")
        git(self.checkout, "add", "pals-api")
        git(self.checkout, "commit", "-m", "Pin nested test tree")
        revision = git(self.checkout, "rev-parse", "HEAD")
        deploy.source_revisions(self.checkout, revision)
        for repository, name in (
            (self.checkout, "pals-api"),
            (component, "nested/one"),
            (nested, "second"),
        ):
            git(repository, "config", "submodule." + name + ".ignore", "all")
        (nested / "second/component.txt").write_text("deep uncommitted user work\n")
        self.assertEqual(git(self.checkout, "status", "--porcelain=v1"), "")
        with self.assertRaises(deploy.DeploymentError):
            deploy.source_revisions(self.checkout, revision)


class HostBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.workspace = temporary_directory()
        self.addCleanup(self.workspace.cleanup)
        self.root = Path(self.workspace.name).resolve()
        self.source = self.root / "checkout"
        self.source.mkdir(mode=0o700)
        self.state = self.root / "state"
        self.state.mkdir(mode=0o700)
        self.controller = self.root / "controller"
        self.controller.write_text("#!/bin/sh\nexit 0\n")
        self.controller.chmod(0o700)
        self.config_path = self.root / "config.json"
        self.config = {
            "schema_version": "pals.macmini-deploy-config.v1",
            "state_dir": str(self.state),
            "controller": str(self.controller),
            "controller_sha256": hashlib.sha256(
                self.controller.read_bytes()
            ).hexdigest(),
            "docker_context": "desktop-linux",
            "containers": {
                "api": "pals-api-prod",
                "web": "pals-web-prod",
                "worker": "pals-worker-prod",
            },
            "database_identity": {
                "database_system_identifier": "123456789",
                "database_volume_id": "12345678-1234-4123-8123-123456789abc",
                "host_binding_sha256": "a" * 64,
            },
            "health_urls": {
                "api": "http://127.0.0.1:18000/health",
                "web": "http://127.0.0.1:13000/",
            },
            "controller_timeout_seconds": 30,
            "health_timeout_seconds": 1,
        }
        self.write_config()

    def write_config(self):
        self.config_path.write_text(json.dumps(self.config))
        self.config_path.chmod(0o600)

    def test_protected_config_accepted(self):
        self.assertEqual(deploy.read_config(self.config_path, self.source), self.config)

    def enable_assessment(self):
        self.config["schema_version"] = deploy.CONFIG_V2
        self.config["containers"]["assessment-worker"] = "pals-assessment-prod"
        self.write_config()

    def test_v2_requires_exact_four_distinct_containers(self):
        self.enable_assessment()
        self.assertEqual(deploy.read_config(self.config_path, self.source), self.config)
        valid = copy.deepcopy(self.config)
        for mutation in ("missing", "duplicate", "extra", "old-schema", "bad-schema"):
            with self.subTest(mutation=mutation):
                self.config = copy.deepcopy(valid)
                if mutation == "missing":
                    del self.config["containers"]["assessment-worker"]
                elif mutation == "duplicate":
                    self.config["containers"]["assessment-worker"] = self.config[
                        "containers"
                    ]["worker"]
                elif mutation == "extra":
                    self.config["containers"]["unexpected"] = "other"
                elif mutation == "old-schema":
                    self.config["schema_version"] = deploy.CONFIG_V1
                else:
                    self.config["schema_version"] = []
                self.write_config()
                with self.assertRaises(deploy.DeploymentError):
                    deploy.read_config(self.config_path, self.source)

    def assessment_fixture(self):
        revisions, receipt = self.release_fixture()
        observations = self.docker_observations(revisions, receipt)
        self.enable_assessment()
        receipt["schema_version"] = "pals.macmini-deploy-result.v2"
        prefix = ("docker", "--context", self.config["docker_context"], "inspect")
        observations[(*prefix, self.config["containers"]["assessment-worker"])] = [
            {"Image": receipt["images"]["worker"], "State": {"Running": True}}
        ]
        for service in ("worker", "assessment-worker"):
            observations[(*prefix, self.config["containers"][service])][0]["State"][
                "Health"
            ] = {"Status": "healthy"}
        return revisions, receipt, observations

    def test_v2_receipt_reuses_three_signed_images(self):
        revisions, receipt, _ = self.assessment_fixture()
        deploy.validate_receipt(receipt, revisions, self.config)
        for mutation in ("old-schema", "extra-image"):
            with self.subTest(mutation=mutation):
                invalid = copy.deepcopy(receipt)
                if mutation == "old-schema":
                    invalid["schema_version"] = "pals.macmini-deploy-result.v1"
                else:
                    invalid["images"]["assessment-worker"] = receipt["images"]["worker"]
                with self.assertRaises(deploy.DeploymentError):
                    deploy.validate_receipt(invalid, revisions, self.config)

    def test_v2_assessment_matches_signed_worker_and_both_are_ready(self):
        revisions, receipt, observations = self.assessment_fixture()
        capture = self.verify_docker_observations(revisions, receipt, observations)
        self.assertEqual(capture.call_count, 8)
        for service in ("worker", "assessment-worker"):
            for mutation in (
                "image",
                "stopped",
                "starting",
                "unhealthy",
                "missing-health",
            ):
                with self.subTest(service=service, mutation=mutation):
                    invalid = copy.deepcopy(observations)
                    item = invalid[
                        (
                            "docker",
                            "--context",
                            self.config["docker_context"],
                            "inspect",
                            self.config["containers"][service],
                        )
                    ][0]
                    if mutation == "image":
                        item["Image"] = "sha256:" + "f" * 64
                    elif mutation == "stopped":
                        item["State"]["Running"] = False
                    elif mutation == "missing-health":
                        del item["State"]["Health"]
                    else:
                        item["State"]["Health"]["Status"] = mutation
                    with self.assertRaises(deploy.DeploymentError):
                        self.verify_docker_observations(revisions, receipt, invalid)

    def test_config_permissions_rejected(self):
        self.config_path.chmod(0o644)
        with self.assertRaises(deploy.DeploymentError):
            deploy.read_config(self.config_path, self.source)

    def test_config_symlink_rejected(self):
        link = self.root / "config-link.json"
        link.symlink_to(self.config_path)
        with self.assertRaises(deploy.DeploymentError):
            deploy.read_config(link, self.source)

    def test_config_inside_checkout_rejected(self):
        destination = self.source / "config.json"
        destination.write_bytes(self.config_path.read_bytes())
        destination.chmod(0o600)
        with self.assertRaises(deploy.DeploymentError):
            deploy.read_config(destination, self.source)

    def test_state_and_controller_inside_checkout_rejected(self):
        for key in ("state_dir", "controller"):
            with self.subTest(key=key):
                invalid = copy.deepcopy(self.config)
                invalid[key] = str(self.source)
                self.config_path.write_text(json.dumps(invalid))
                with self.assertRaises(deploy.DeploymentError):
                    deploy.read_config(self.config_path, self.source)

    def test_modified_controller_hash_rejected(self):
        self.controller.write_text("#!/bin/sh\nexit 7\n")
        with self.assertRaises(deploy.DeploymentError):
            deploy.read_config(self.config_path, self.source)

    def test_controller_symlink_rejected(self):
        link = self.root / "controller-link"
        link.symlink_to(self.controller)
        self.config["controller"] = str(link)
        self.write_config()
        with self.assertRaises(deploy.DeploymentError):
            deploy.read_config(self.config_path, self.source)

    def test_loopback_url_boundary(self):
        for value in ("http://127.0.0.1:8000/health", "http://[::1]:8000/health"):
            self.assertEqual(deploy.loopback_url(value), value)
        for value in (
            "https://127.0.0.1:8000/health",
            "http://localhost:8000/health",
            "http://192.0.2.1:8000/health",
            "http://127.0.0.1/health",
            "http://user:password@127.0.0.1:8000/",
            "http://127.0.0.1:8000/?token=x",
            "http://127.0.0.1:8000/#fragment",
            "http://127.0.0.1:0/",
            None,
        ):
            with (
                self.subTest(value=value),
                self.assertRaises((deploy.DeploymentError, ValueError)),
            ):
                deploy.loopback_url(value)

    def test_real_lock_contention_and_retained_inode(self):
        with deploy.deployment_lock(self.state):
            original_inode = (self.state / "deploy.lock").stat().st_ino
            # A separate process must be rejected by the real OS lock.
            program = (
                "import fcntl,os,sys; fd=os.open(sys.argv[1],os.O_RDWR); "
                "fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)"
            )
            result = subprocess.run(
                [sys.executable, "-c", program, str(self.state / "deploy.lock")],
                capture_output=True,
                timeout=10,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            with (
                self.assertRaises(deploy.DeploymentError),
                deploy.deployment_lock(self.state),
            ):
                self.fail("Concurrent lock acquired")
        self.assertEqual((self.state / "deploy.lock").stat().st_ino, original_inode)
        with deploy.deployment_lock(self.state):
            self.assertEqual((self.state / "deploy.lock").stat().st_ino, original_inode)

    def test_receipt_requires_exact_revisions_database_and_images(self):
        revisions = {"pals": "a" * 40, **{name: "b" * 40 for name in deploy.SOURCES}}
        receipt = {
            "schema_version": "pals.macmini-deploy-result.v1",
            "status": "applied",
            "parent_sha": revisions["pals"],
            "source_commits": revisions,
            "manifest_sha256": "c" * 64,
            "images": {service: "sha256:" + "d" * 64 for service in deploy.SERVICES},
            "database_identity": self.config["database_identity"],
        }
        deploy.validate_receipt(receipt, revisions, self.config)
        mutations = (
            ("parent_sha", "e" * 40),
            ("source_commits", {**revisions, "pals-api": "e" * 40}),
            ("source_commits", {"pals": revisions["pals"]}),
            (
                "database_identity",
                {
                    **receipt["database_identity"],
                    "database_system_identifier": "987654321",
                },
            ),
            ("images", {**receipt["images"], "api": "latest"}),
            ("images", {"api": receipt["images"]["api"]}),
            ("manifest_sha256", ""),
            ("status", "healthy"),
        )
        for key, value in mutations:
            with (
                self.subTest(key=key, value=value),
                self.assertRaises(deploy.DeploymentError),
            ):
                deploy.validate_receipt({**receipt, key: value}, revisions, self.config)

    def test_nonzero_real_controller_rejected_and_private_log(self):
        config = {**self.config, "controller": "/usr/bin/false"}
        log = self.state / "controller.log"
        with self.assertRaises(deploy.DeploymentError):
            deploy.run_controller(
                config, self.source, "a" * 40, self.state / "receipt.json", log
            )
        self.assertEqual(log.stat().st_mode & 0o777, 0o600)
        self.assertFalse((self.state / "receipt.json").exists())

    def test_controller_timeout_reaps_process(self):
        # This isolated test executable records its PID; it never performs a deployment.
        self.controller.write_text(
            "#!" + sys.executable + "\nimport os,pathlib,sys,time\n"
            "pathlib.Path(sys.argv[-1] + '.pid').write_text(str(os.getpid()))\ntime.sleep(30)\n"
        )
        receipt = self.state / "receipt.json"
        config = {**self.config, "controller_timeout_seconds": 1}
        with self.assertRaises(subprocess.TimeoutExpired):
            deploy.run_controller(
                config, self.source, "a" * 40, receipt, self.state / "timeout.log"
            )
        pid = int(Path(str(receipt) + ".pid").read_text())
        with self.assertRaises(ProcessLookupError):
            os.kill(pid, 0)

    def test_successful_controller_cannot_leave_child_process(self):
        self.controller.write_text(
            "#!" + sys.executable + "\nimport pathlib,subprocess,sys\n"
            "child=subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])\n"
            "pathlib.Path(sys.argv[-1] + '.child-pid').write_text(str(child.pid))\n"
        )
        receipt = self.state / "receipt.json"
        try:
            with self.assertRaises(deploy.DeploymentError):
                deploy.run_controller(
                    self.config,
                    self.source,
                    "a" * 40,
                    receipt,
                    self.state / "child.log",
                )
            child_pid = int(Path(str(receipt) + ".child-pid").read_text())
            observed = subprocess.run(
                ["ps", "-p", str(child_pid), "-o", "stat="],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            self.assertTrue(
                observed.returncode != 0 or observed.stdout.strip().startswith("Z"),
                "Controller descendant remains active",
            )
        finally:
            pid_file = Path(str(receipt) + ".child-pid")
            if pid_file.exists():
                try:
                    os.kill(int(pid_file.read_text()), signal.SIGKILL)
                except ProcessLookupError:
                    pass

    def test_ambient_credentials_not_forwarded_to_controller(self):
        self.controller.write_text(
            "#!" + sys.executable + "\nimport os\n"
            "assert not any(k.startswith(('AWS_', 'PALS_', 'ACTIONS_')) or k == 'GITHUB_TOKEN' for k in os.environ)\n"
        )
        with mock.patch.dict(
            os.environ,
            {
                "AWS_SESSION_TOKEN": "test-only",
                "PALS_PRIVATE": "test-only",
                "ACTIONS_RUNTIME_TOKEN": "test-only",
                "GITHUB_TOKEN": "test-only",
            },
        ):
            deploy.run_controller(
                self.config,
                self.source,
                "a" * 40,
                self.state / "receipt.json",
                self.state / "environment.log",
            )

    def release_fixture(self):
        revisions = {"pals": "a" * 40}
        revisions.update(
            {
                name: format(index + 1, "x") * 40
                for index, name in enumerate(deploy.SOURCES)
            }
        )
        receipt = {
            "schema_version": "pals.macmini-deploy-result.v1",
            "status": "applied",
            "parent_sha": revisions["pals"],
            "source_commits": revisions,
            "manifest_sha256": "c" * 64,
            "images": {
                service: "sha256:" + str(index + 1) * 64
                for index, service in enumerate(self.config["containers"])
            },
            "database_identity": self.config["database_identity"],
        }
        return revisions, receipt

    def docker_observations(self, revisions, receipt):
        # Only this Docker boundary is isolated. These responses are not live deployment evidence.
        observations = {}
        prefix = ("docker", "--context", self.config["docker_context"])
        owners = {"api": "pals-api", "web": "pals-webfront", "worker": "pals-agent"}
        for service, container in self.config["containers"].items():
            image = receipt["images"][service]
            observations[(*prefix, "inspect", container)] = [
                {"Image": image, "State": {"Running": True}}
            ]
            observations[(*prefix, "image", "inspect", image)] = [
                {
                    "Config": {
                        "Labels": {
                            "org.opencontainers.image.revision": revisions[
                                owners[service]
                            ],
                            "site.pals.parent-sha": revisions["pals"],
                        }
                    }
                }
            ]
        return observations

    def verify_docker_observations(self, revisions, receipt, observations):
        with mock.patch.object(
            deploy,
            "capture",
            side_effect=lambda args: json.dumps(observations[tuple(args)]),
        ) as capture:
            deploy.verify_containers(self.config, receipt, revisions)
        return capture

    def test_three_container_images_and_provenance_accepted(self):
        revisions, receipt = self.release_fixture()
        observations = self.docker_observations(revisions, receipt)
        capture = self.verify_docker_observations(revisions, receipt, observations)
        self.assertEqual(capture.call_count, 6)
        self.assertEqual(
            {tuple(call.args[0]) for call in capture.call_args_list}, set(observations)
        )

    def test_container_actual_image_mismatch_rejected(self):
        revisions, receipt = self.release_fixture()
        for service in self.config["containers"]:
            with self.subTest(service=service):
                observations = self.docker_observations(revisions, receipt)
                container = self.config["containers"][service]
                observations[
                    (
                        "docker",
                        "--context",
                        self.config["docker_context"],
                        "inspect",
                        container,
                    )
                ][0]["Image"] = "sha256:" + "f" * 64
                with self.assertRaises(deploy.DeploymentError):
                    self.verify_docker_observations(revisions, receipt, observations)

    def test_stopped_container_rejected(self):
        revisions, receipt = self.release_fixture()
        for service in self.config["containers"]:
            with self.subTest(service=service):
                observations = self.docker_observations(revisions, receipt)
                container = self.config["containers"][service]
                observations[
                    (
                        "docker",
                        "--context",
                        self.config["docker_context"],
                        "inspect",
                        container,
                    )
                ][0]["State"]["Running"] = False
                with self.assertRaises(deploy.DeploymentError):
                    self.verify_docker_observations(revisions, receipt, observations)

    def test_wrong_component_image_provenance_rejected(self):
        self.assert_wrong_image_label_rejected("org.opencontainers.image.revision")

    def test_wrong_parent_image_provenance_rejected(self):
        self.assert_wrong_image_label_rejected("site.pals.parent-sha")

    def assert_wrong_image_label_rejected(self, label):
        revisions, receipt = self.release_fixture()
        for service in self.config["containers"]:
            with self.subTest(service=service):
                observations = self.docker_observations(revisions, receipt)
                image = receipt["images"][service]
                observations[
                    (
                        "docker",
                        "--context",
                        self.config["docker_context"],
                        "image",
                        "inspect",
                        image,
                    )
                ][0]["Config"]["Labels"][label] = "f" * 40
                with self.assertRaises(deploy.DeploymentError):
                    self.verify_docker_observations(revisions, receipt, observations)

    def test_preflight_never_runs_controller_or_writes_success(self):
        revisions, _ = self.release_fixture()
        current = self.state / "current.json"
        for existing in (False, True):
            with self.subTest(existing=existing):
                if existing:
                    current.write_bytes(b"previous healthy release\n")
                    current.chmod(0o600)
                with (
                    mock.patch.object(deploy.sys, "platform", "darwin"),
                    mock.patch.object(
                        deploy, "source_revisions", return_value=revisions
                    ),
                    mock.patch.object(
                        deploy, "capture", return_value="linux"
                    ) as docker,
                    mock.patch.object(deploy, "run_controller") as controller,
                    mock.patch.object(deploy, "verify_containers") as containers,
                    mock.patch.object(deploy, "verify_health") as health,
                ):
                    result = deploy.execute(
                        self.config_path, self.source, revisions["pals"], preflight=True
                    )
                self.assertEqual(result["status"], "preflight-passed")
                self.assertIs(result["deployed"], False)
                controller.assert_not_called()
                containers.assert_not_called()
                health.assert_not_called()
                docker.assert_called_once_with(
                    [
                        "docker",
                        "--context",
                        "desktop-linux",
                        "info",
                        "--format",
                        "{{.OSType}}",
                    ]
                )
                self.assertEqual(list(self.state.glob("receipt-*")), [])
                if existing:
                    self.assertEqual(
                        current.read_bytes(), b"previous healthy release\n"
                    )
                else:
                    self.assertFalse(current.exists())

    def test_invalid_receipt_never_updates_success_record(self):
        revisions, receipt = self.release_fixture()
        current = self.state / "current.json"
        current.write_bytes(b"previous healthy release\n")
        current.chmod(0o600)

        def controller(_config, _source, _revision, receipt_path, _log):
            # The real JSON reader and receipt validator inspect this isolated file.
            receipt_path.write_text(json.dumps({**receipt, "parent_sha": "0" * 40}))

        with (
            mock.patch.object(deploy.sys, "platform", "darwin"),
            mock.patch.object(deploy, "source_revisions", return_value=revisions),
            mock.patch.object(deploy, "capture", return_value="linux"),
            mock.patch.object(deploy, "run_controller", side_effect=controller) as run,
            mock.patch.object(deploy, "verify_containers") as containers,
            mock.patch.object(deploy, "verify_health") as health,
            self.assertRaises(deploy.DeploymentError),
        ):
            deploy.execute(self.config_path, self.source, revisions["pals"])
        run.assert_called_once()
        containers.assert_not_called()
        health.assert_not_called()
        self.assertEqual(current.read_bytes(), b"previous healthy release\n")
        self.assertEqual(list(self.state.glob("receipt-*.json")), [])

    def test_signal_permission_denied_ignored_only_for_observed_dead_group(self):
        for observation in ("123 Z\n456 S\n", "456 S\n"):
            with (
                self.subTest(observation=observation),
                mock.patch.object(
                    deploy.os, "killpg", side_effect=PermissionError(1, "test denial")
                ) as kill,
                mock.patch.object(
                    deploy, "capture", return_value=observation
                ) as capture,
            ):
                deploy.signal_controller_group(123, signal.SIGKILL)
                kill.assert_called_once_with(123, signal.SIGKILL)
                capture.assert_called_once_with(
                    ["ps", "-A", "-o", "pgid=", "-o", "stat="]
                )

    def test_signal_permission_denied_with_live_group_member_rejected(self):
        with (
            mock.patch.object(
                deploy.os, "killpg", side_effect=PermissionError(1, "test denial")
            ),
            mock.patch.object(deploy, "capture", return_value="123 Z\n123 S+\n456 Z\n"),
            self.assertRaises(PermissionError),
        ):
            deploy.signal_controller_group(123, signal.SIGKILL)

    def test_signal_permission_denied_with_failed_observation_rejected(self):
        for observation in (deploy.DeploymentError("Test ps unavailable"), "123\n"):
            with (
                self.subTest(observation=observation),
                mock.patch.object(
                    deploy.os, "killpg", side_effect=PermissionError(1, "test denial")
                ),
                mock.patch.object(deploy, "capture", side_effect=[observation]),
                self.assertRaises(deploy.DeploymentError),
            ):
                deploy.signal_controller_group(123, signal.SIGKILL)


class HealthBoundaryTests(unittest.TestCase):
    def start_server(self, status: int, location: str | None = None):
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                requests.append(self.path)
                self.send_response(status)
                if location:
                    self.send_header("Location", location)
                self.send_header("Content-Length", "0")
                self.end_headers()

            def log_message(self, *_):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        def cleanup():
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

        self.addCleanup(cleanup)
        return server, requests

    def config(self, server):
        base = "http://127.0.0.1:" + str(server.server_port)
        return {
            "health_timeout_seconds": 1,
            "health_urls": {"api": base + "/health", "web": base + "/"},
        }

    def test_real_loopback_200_ignores_proxy_environment(self):
        server, requests = self.start_server(200)
        with mock.patch.dict(
            os.environ,
            {
                "http_proxy": "http://127.0.0.1:1",
                "HTTP_PROXY": "http://127.0.0.1:1",
                "ALL_PROXY": "http://127.0.0.1:1",
                "NO_PROXY": "",
                "no_proxy": "",
            },
        ):
            deploy.verify_health(self.config(server))
        self.assertEqual(requests, ["/health", "/"])

    def test_real_loopback_failure_rejected(self):
        server, requests = self.start_server(503)
        with self.assertRaises(deploy.DeploymentError):
            deploy.verify_health(self.config(server))
        self.assertTrue(requests)

    def test_external_redirect_not_followed(self):
        server, requests = self.start_server(
            302, "https://example.invalid/never-follow"
        )
        # Observe every socket address requested by urllib, in addition to using real HTTP.
        import socket

        original = socket.create_connection
        addresses = []

        def observed_connection(address, *args, **kwargs):
            addresses.append(address)
            self.assertEqual(
                address[0], "127.0.0.1", "Redirect attempted an external connection"
            )
            return original(address, *args, **kwargs)

        with (
            mock.patch("socket.create_connection", side_effect=observed_connection),
            self.assertRaises(deploy.DeploymentError),
        ):
            deploy.verify_health(self.config(server))
        self.assertTrue(requests)
        self.assertTrue(addresses)


if __name__ == "__main__":
    unittest.main()
