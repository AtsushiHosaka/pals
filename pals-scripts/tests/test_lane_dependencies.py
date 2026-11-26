"""Closed local dependency launch tests with a fake Compose process."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch

import test_relay_compose as render_tests

import lane_dependencies as deps
import lane_environment as environment
import relay_compose


@unittest.skipUnless(importlib.util.find_spec("yaml"), "optional Compose rendering needs PyYAML")
class LaneDependencyTests(unittest.TestCase):
    def setUp(self):
        fixture = render_tests.RelayComposeTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.root = fixture.root
        self.compose_root = fixture.compose_root
        self.render_input = fixture.document
        for name in deps.SUPPORT:
            path = self.compose_root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# reviewed fixture\n")
            path.chmod(0o700)
        infra = self.compose_root / deps.SOURCES[2]
        if "environment:" not in infra.read_text():
            infra.write_text("""services:
  localstack:
    environment: {AWS_ACCESS_KEY_ID: '${AWS_ACCESS_KEY_ID:-test}'}
    healthcheck: {test: [CMD, true]}
    volumes: [localstack-data:/var/lib/localstack]
  cognito-local:
    environment: {PORT: 9229}
    healthcheck: {test: [CMD, true]}
    volumes: [cognito-local-data:/app/.cognito]
volumes:
  localstack-data:
  cognito-local-data:
""")
        self.rendered = relay_compose.render(self.render_input, self.compose_root)
        socket_path = self.root / "d.sock"
        socket_path.touch(mode=0o600)
        socket_check = patch.object(deps.stat, "S_ISSOCK", return_value=True)
        socket_check.start()
        self.addCleanup(socket_check.stop)
        local_envs = {}
        self.passwords = {}
        for role, lane in self.render_input["lanes"].items():
            runtime = Path(lane["runtime_directory"])
            runtime.mkdir(mode=0o700)
            values = environment.lane_values(role, lane, {"PALS_ENV": "local", "PALS_ENVIRONMENT": "local"})
            # Deliberately include ambient-like inputs. The child must not forward them.
            values.update(COMPOSE_PROFILES="all", DOCKER_CONTEXT="production", HTTPS_PROXY="https://forbidden.test")
            self.passwords[role] = values["POSTGRES_PASSWORD"]
            local_envs[role] = self.write(runtime / "local.env", "".join(f"{k}={v}\n" for k, v in values.items()))
        self.docker = self.root / "docker"
        self.docker.symlink_to(Path(sys.executable).resolve())
        self.binding = {
            "schema_version": deps.SCHEMA,
            "compose_root": str(self.compose_root),
            "rendered_compose": self.write(self.root / "rendered.json", json.dumps(self.rendered)),
            "docker": str(self.docker),
            "compose_plugin": str(Path(sys.executable).resolve()),
            "docker_socket": str(socket_path),
            "local_envs": local_envs,
            "support": {
                name: self.ref(self.compose_root / name) for name in deps.SUPPORT
            },
        }

    @staticmethod
    def ref(path):
        return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    def write(self, path, text):
        path.write_text(text)
        path.chmod(0o600)
        return self.ref(path)

    def test_dry_mode_derives_both_exact_projects_without_running_commands(self):
        run = Mock()
        result = deps.launch(self.binding, run=run, read=run)
        run.assert_not_called()
        self.assertEqual(result["status"], "lane_dependencies_preview")
        for role, entry in result["lanes"].items():
            argv = entry["command"]
            self.assertEqual(argv[0], str(self.docker))
            self.assertIn(f"pals-reliability-local-{role}", argv)
            self.assertEqual(argv[-9:], ["up", "--wait", "--no-recreate", "--no-build", "--pull", "never",
                                        "postgres", "localstack", "cognito-local"])
        for password in self.passwords.values():
            self.assertNotIn(password, json.dumps(result))

    def test_apply_only_invokes_dependency_compose_with_scrubbed_environment(self):
        def run(argv, **kwargs):
            role = argv[argv.index("--project-name") + 1].rsplit("-", 1)[1]
            config_directory = Path(argv[argv.index("--config") + 1])
            self.assertEqual(config_directory.stat().st_mode & 0o777, 0o700)
            self.assertTrue((config_directory / "cli-plugins/docker-compose").is_symlink())
            model = json.loads(kwargs["input"])
            self.assertEqual(set(model["services"]), {"postgres", "localstack", "cognito-local"})
            self.assertEqual(model["services"]["postgres"]["ports"][0]["published"],
                             {"primary": "55434", "standby": "55433"}[role])
            for service in model["services"].values():
                self.assertEqual(service["ports"][0]["host_ip"], "127.0.0.1")
                self.assertEqual(service["pull_policy"], "never")
                self.assertNotIn("build", service)
                self.assertNotIn("depends_on", service)
            self.assertNotIn("provider-socket", model["volumes"])
            self.assertIn("--no-recreate", argv)
            env = kwargs["env"]
            self.assertEqual(env["POSTGRES_PASSWORD"], self.passwords[role])
            self.assertEqual(env["AWS_ACCESS_KEY_ID"], "test")
            self.assertFalse({"AWS_PROFILE", "COMPOSE_PROFILES", "DOCKER_CONTEXT", "HTTPS_PROXY", "HOME",
                              "OPENAI_API_KEY", "PALS_OPENAI_API_KEY"} & env.keys())
            return subprocess.CompletedProcess(argv, 0, "", "")

        fake = Mock(side_effect=run)
        with patch.dict(os.environ, AWS_PROFILE="live", OPENAI_API_KEY="live"):
            result = deps.launch(self.binding, apply=True, run=fake, read=Mock(return_value=[]))
        self.assertEqual(result["status"], "lane_dependencies_started")
        self.assertEqual(fake.call_count, 2)

    def test_refuses_any_existing_target_resource_before_starting_either_lane(self):
        standby = "pals-reliability-local-standby"
        for kind, args in (("container", ["--all"]), ("network", []), ("volume", [])):
            with self.subTest(kind=kind):
                def read(argv):
                    self.assertEqual(argv[0], str(self.docker))
                    self.assertEqual(argv[3:5], ["--host", "unix://" + self.binding["docker_socket"]])
                    self.assertNotIn("pals-reliability-local", argv)
                    if argv[5:7 + len(args)] == [kind, "ls", *args] and "--format" in argv:
                        return [standby + "_custom"]
                    return []

                run = Mock()
                with self.assertRaisesRegex(ValueError, "lane_dependency_resources_already_exist_standby"):
                    deps.launch(self.binding, apply=True, run=run, read=read)
                run.assert_not_called()

    def test_refuses_a_custom_named_resource_by_exact_project_label(self):
        selected = "label=com.docker.compose.project=pals-reliability-local-primary"
        calls = []

        def read(argv):
            calls.append(argv)
            if argv[5:7] == ["volume", "ls"] and selected in argv:
                return ["custom-owned-volume"]
            return ["pals-reliability-local-postgres-1"] if "--format" in argv else []

        run = Mock()
        with self.assertRaisesRegex(ValueError, "lane_dependency_resources_already_exist_primary"):
            deps.launch(self.binding, apply=True, run=run, read=read)
        run.assert_not_called()
        self.assertTrue(any(selected in call for call in calls))

    def test_rechecks_standby_after_primary_and_ignores_legacy_project(self):
        started = []

        def run(argv, **kwargs):
            project = argv[argv.index("--project-name") + 1]
            started.append(project)
            return subprocess.CompletedProcess(argv, 0)

        def read(argv):
            if "--format" in argv:
                return ["pals-reliability-local-postgres-1", "pals-reliability-local-standbyish-net"]
            standby_filter = "label=com.docker.compose.project=pals-reliability-local-standby"
            if argv[5:7] == ["network", "ls"] and standby_filter in argv and started:
                return ["raced-network"]
            return []

        with self.assertRaisesRegex(ValueError, "lane_dependency_resources_already_exist_standby"):
            deps.launch(self.binding, apply=True, run=run, read=read)
        self.assertEqual(started, ["pals-reliability-local-primary"])

    def test_inventory_failure_cannot_be_accepted_as_empty(self):
        with patch.object(deps.subprocess, "run", return_value=subprocess.CompletedProcess([], 1, "", "error")):
            with self.assertRaisesRegex(ValueError, "lane_dependency_resource_inventory_unverified"):
                deps.read_docker(["docker", "network", "ls"])

    def test_refuses_legacy_project_before_any_launch(self):
        lane = self.rendered["lanes"]["primary"]
        lane["compose_project"] = "pals-reliability-local"
        self.binding["rendered_compose"] = self.write(self.root / "rendered.json", json.dumps(self.rendered))
        run = Mock()
        with self.assertRaisesRegex(ValueError, "rendered_lane_dependency_identity_differs"):
            deps.launch(self.binding, apply=True, run=run)
        run.assert_not_called()

    def test_refuses_legacy_postgres_port_even_in_hash_pinned_overlay(self):
        lane = self.rendered["lanes"]["primary"]
        overlay = lane["relay_overlay_yaml"]
        self.assertIn("55434", overlay)
        lane["relay_overlay_yaml"] = overlay.replace("55434", "55432")
        self.binding["rendered_compose"] = self.write(self.root / "rendered.json", json.dumps(self.rendered))
        run = Mock()
        with self.assertRaisesRegex(ValueError, "rendered_lane_dependency_service_differs"):
            deps.launch(self.binding, apply=True, run=run)
        run.assert_not_called()

    def test_does_not_start_second_lane_after_frozen_input_changes(self):
        def run(argv, **kwargs):
            path = Path(self.binding["local_envs"]["standby"]["path"])
            path.write_text(path.read_text() + "# changed\n")
            return subprocess.CompletedProcess(argv, 0, "", "")

        fake = Mock(side_effect=run)
        with self.assertRaisesRegex(ValueError, "lane_bootstrap_environment_hash_changed"):
            deps.launch(self.binding, apply=True, run=fake, read=Mock(return_value=[]))
        fake.assert_called_once()

    def test_does_not_start_second_lane_after_docker_symlink_changes(self):
        changed = self.root / "other-executable"
        changed.touch(mode=0o700)

        def run(argv, **kwargs):
            self.docker.unlink()
            self.docker.symlink_to(changed)
            return subprocess.CompletedProcess(argv, 0, "", "")

        fake = Mock(side_effect=run)
        with self.assertRaisesRegex(ValueError, "lane_dependency_inputs_changed_before_start"):
            deps.launch(self.binding, apply=True, run=fake, read=Mock(return_value=[]))
        fake.assert_called_once()

    def test_timeout_stops_compose_and_docker_in_one_process_group(self):
        child = Mock(pid=321)
        child.communicate.side_effect = subprocess.TimeoutExpired(["docker"], 240)
        with patch.object(deps.subprocess, "Popen") as popen, patch.object(deps.os, "killpg") as kill:
            popen.return_value.__enter__.return_value = child
            with self.assertRaises(subprocess.TimeoutExpired):
                deps.run_compose(["docker"], input="{}", env={}, timeout=240)
        self.assertTrue(popen.call_args.kwargs["start_new_session"])
        kill.assert_called_once_with(321, deps.signal.SIGKILL)

    def test_refuses_alias_socket_and_changes_to_frozen_inputs(self):
        alias = self.root / "alias.sock"
        alias.symlink_to(self.binding["docker_socket"])
        with self.assertRaisesRegex(ValueError, "exact_owned_local_docker_socket_required"):
            deps.launch({**self.binding, "docker_socket": str(alias)})
        path = Path(self.binding["local_envs"]["standby"]["path"])
        path.write_text(path.read_text().replace("POSTGRES_HOST_PORT=55433", "POSTGRES_HOST_PORT=55432"))
        run = Mock()
        with self.assertRaisesRegex(ValueError, "lane_bootstrap_environment_hash_changed"):
            deps.launch(self.binding, apply=True, run=run)
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
