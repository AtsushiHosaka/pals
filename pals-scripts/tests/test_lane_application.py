"""The dedicated application launcher has no live Docker or provider tests."""

import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import Mock, patch

import test_lane_dependencies as dependency_tests
import lane_application as app
import lane_database
import lane_environment
import relay_compose


@unittest.skipUnless(importlib.util.find_spec("yaml"), "optional Compose rendering needs PyYAML")
class ApplicationLaneTests(unittest.TestCase):
    def setUp(self):
        fixture = dependency_tests.LaneDependencyTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture = fixture
        root = fixture.root
        self.provider_key = "fixture-provider-value"
        provider = fixture.write(root / "provider.env",
                                 f"OPENAI_API_KEY={self.provider_key}\nPALS_OPENAI_UPSTREAM_IP=1.1.1.1\n")
        state_root = root / "application"
        state_root.mkdir(mode=0o700)
        budget_ref = fixture.render_input["provider"]["budget_ledger"]
        before = fixture.write(state_root / "budget-before.json", Path(budget_ref["path"]).read_text())
        compose_input = fixture.write(root / "compose-input.json", json.dumps(fixture.render_input))
        bootstrap = {}
        layout = {"schema_version": lane_database.SCHEMA, "docker_socket": fixture.binding["docker_socket"],
                  "lanes": {}}
        self.rows = {}
        for digit, (role, ports) in enumerate(app.ENDPOINTS.items(), 1):
            lane = fixture.render_input["lanes"][role]
            runtime = Path(lane["runtime_directory"])
            env = lane_environment.lane_values(role, lane, {"PALS_ENV": "local", "PALS_ENVIRONMENT": "local"})
            local = fixture.write(runtime / "local.env", "".join(f"{k}={v}\n" for k, v in env.items()))
            fixture.binding["local_envs"][role] = local
            bootstrap[role] = {
                "release": fixture.write(runtime / "release.env", "PALS_VERIFIER_TEST=value\n"),
                "recipe": fixture.write(runtime / "recipe.env", "PALS_RECIPE_TEST=value\n"),
            }
            project = app.PREFIX + "-" + role
            database = project + "-postgres-1"
            selected = {
                "candidate_sha256": lane["candidate_sha256"], "compose_project": project,
                "runtime_directory": str(runtime), "local_env": local,
                "postgres": {"name": database, "container_id": str(digit) * 64,
                             "image_id": lane["images"]["postgres"], "host": "127.0.0.1",
                             "host_port": ports["postgres"], "database": "pals"},
            }
            layout["lanes"][role] = selected
            with lane_database.migration_state(runtime, selected) as begin:
                begin(True)
            for service, endpoint, target, network, image in (
                ("postgres", "postgres", 5432, "database", "postgres"),
                ("localstack", "localstack", 4566, "e2e", "localstack"),
                ("cognito-local", "cognito", 9229, "e2e", "cognito"),
            ):
                self.rows[f"/{project}-{service}-1"] = {
                    "id": str(digit) * 64 if service == "postgres" else f"{role}-{service}",
                    "image": lane["images"][image], "labels": {"codex.owner": app.OWNER, app.PROJECT: project,
                                                               app.SERVICE: service},
                    "privileged": False, "networks": {f"{project}-{network}": {}},
                    "ports": {f"{target}/tcp": [{"HostIp": "127.0.0.1", "HostPort": str(ports[endpoint])}]},
                    "running": True, "health": "healthy", "pid": 10 + digit, "started_at": "2026-11-27T10:00:00Z",
                }
        self.document = {
            "schema_version": app.SCHEMA,
            "dependency_binding": fixture.write(root / "dependency.json", json.dumps(fixture.binding)),
            "database_layout": fixture.write(root / "db-only.json", json.dumps(layout)),
            "compose_input": compose_input, "bootstrap_environments": bootstrap,
            "provider_env": provider, "budget_before": before,
            "handoff_output": str(state_root / "budget-handoff.json"),
        }
        self.budget = budget_ref

    def test_dry_derivation_does_not_launch_or_print_credentials(self):
        mocked = Mock()
        report = app.launch(self.document, run=mocked, read=mocked)
        mocked.assert_not_called()
        self.assertNotIn(self.provider_key, json.dumps(report))
        self.assertFalse(Path(self.document["handoff_output"]).exists())
        self.assertEqual(list(report["commands"]), ["provider", "primary", "standby"])
        for commands in report["commands"].values():
            for cmd in commands:
                index = cmd.index("up")
                self.assertEqual(cmd[index:index + 6], ["up", "--no-deps", "--wait", "--no-build", "--pull", "never"])
                self.assertFalse({"postgres", "localstack", "cognito-local", "schema-release"} & set(cmd[index + 6:]))

    def test_apply_seeds_only_candidate_through_compose_process_and_preserves_dependencies(self):
        original = {role: Path(ref["path"]).read_bytes() for role, ref in self.fixture.binding["local_envs"].items()}

        def runner(args, *, env, **kwargs):
            project = args[args.index("--project-name") + 1]
            if project == app.PROVIDER_PROJECT:
                self.assertEqual(env["OPENAI_API_KEY"], self.provider_key)
                self.assertNotIn("PALS_LOCAL_CANDIDATE_SHA256", env)
            else:
                role = project.rsplit("-", 1)[1]
                self.assertNotIn("OPENAI_API_KEY", env)
                self.assertEqual(env["PALS_LOCAL_CANDIDATE_SHA256"],
                                 self.fixture.render_input["lanes"][role]["candidate_sha256"])
            self.assertFalse({"AWS_PROFILE", "DOCKER_CONTEXT", "HTTP_PROXY"} & set(env))
            return subprocess.CompletedProcess(args, 0)

        receipt = {"status": "verified_read_only", "observed_stopped_container_ids": [], "ledger": self.budget}
        run = Mock(side_effect=runner)
        with (
            patch.object(app, "inventory", return_value=self.rows),
            patch.object(lane_database, "verify_databases"),
            patch.object(app, "verify_budget_handoff", return_value=receipt),
        ):
            report = app.launch(self.document, apply=True, run=run, read=Mock(return_value=""))
        self.assertEqual(report["status"], "lane_application_started")
        self.assertEqual(run.call_count, 2 + 2 * len(app.APPLICATION))
        self.assertFalse(self.provider_key in json.dumps(report))
        written = Path(report["handoff_receipt"])
        self.assertEqual(written.stat().st_mode & 0o777, 0o600)
        self.assertEqual(json.loads(written.read_bytes()), receipt)
        for role, ref in self.fixture.binding["local_envs"].items():
            self.assertEqual(Path(ref["path"]).read_bytes(), original[role])

    def test_replacement_dependency_refuses_before_next_role_launch(self):
        def replace(args, **kwargs):
            localstack = self.rows[f"/{app.PREFIX}-primary-localstack-1"]
            localstack["id"] = "replacement"
            return subprocess.CompletedProcess(args, 0)

        run = Mock(side_effect=replace)
        with (
            patch.object(app, "inventory", return_value=self.rows),
            patch.object(lane_database, "verify_databases"),
            patch.object(app, "verify_budget_handoff", return_value={"observed_stopped_container_ids": []}),
        ):
            with self.assertRaisesRegex(ValueError, "lane_application_existing_dependency_identity_changed"):
                app.launch(self.document, apply=True, run=run, read=Mock(return_value=""))
        run.assert_called_once()
        self.assertTrue(Path(self.document["handoff_output"]).exists())

    def test_dry_refuses_a_rewritten_overlay_even_when_new_bytes_are_hash_pinned(self):
        value = relay_compose.render(self.fixture.render_input, self.fixture.compose_root)
        value["provider_compose_yaml"] += "# unauthorized composition\n"
        path = Path(self.fixture.binding["rendered_compose"]["path"])
        self.fixture.binding["rendered_compose"] = self.fixture.write(path, json.dumps(value))
        binding = Path(self.document["dependency_binding"]["path"])
        self.document["dependency_binding"] = self.fixture.write(binding, json.dumps(self.fixture.binding))
        with self.assertRaisesRegex(ValueError, "lane_application_rendering_differs_from_frozen_inputs"):
            app.launch(self.document)

    def test_rejects_prior_dedicated_application_or_provider_volume(self):
        rows = {f"/{app.PREFIX}-primary-api-1": {"labels": {}}}
        with self.assertRaisesRegex(ValueError, "dedicated_application_scope_already_exists"):
            app.no_existing_application(rows, set(), Mock())
        with self.assertRaisesRegex(ValueError, "provider_application_resource_already_exists"):
            app.no_existing_application({}, set(), Mock(return_value=app.SOCKET_VOLUME))


if __name__ == "__main__":
    unittest.main()
