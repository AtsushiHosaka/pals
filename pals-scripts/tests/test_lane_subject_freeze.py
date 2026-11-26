"""Local subject binding regressions that do not start services or spend budget."""

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

SCRIPTS = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("lane_freezer", SCRIPTS / "local-qualification-freeze-lane.py")
freezer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(freezer)


class LaneSubjectFreezeTests(unittest.TestCase):
    def test_subject_publication_is_private_exclusive_and_byte_bound(self):
        with tempfile.TemporaryDirectory() as root:
            subject = {"local_lane": {"role": "standby"}}
            out = Path(root) / "subject-native.json"
            freezer.publish_subject(out, subject)
            self.assertEqual(out.read_bytes(), freezer.subject_bytes(subject))
            self.assertEqual(out.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                freezer.publish_subject(out, {"other": True})
            self.assertEqual(out.read_bytes(), freezer.subject_bytes(subject))

    def test_live_header_mismatch_restores_only_the_selected_api_and_private_environment(self):
        self.exercise_binding()

    def test_explicit_initial_candidate_seed_is_bound_without_rewriting_local_env(self):
        self.exercise_binding(initial_seed="b" * 64, failed=False)

    def test_explicit_initial_candidate_seed_is_restored_without_rewriting_local_env(self):
        self.exercise_binding(initial_seed="b" * 64)

    def test_explicit_seed_cannot_override_a_different_frozen_candidate(self):
        self.exercise_binding(initial_seed="d" * 64)

    def exercise_binding(self, *, initial_seed=None, failed=True):
        with tempfile.TemporaryDirectory() as root:
            runtime = Path(root).resolve()
            subject_dir = runtime / "captures"
            subject_dir.mkdir()
            out = runtime / "subject-native.json"
            env = runtime / "local.env"
            original = b"PALS_ENV=local\n"
            if initial_seed is None:
                original += b"PALS_LOCAL_CANDIDATE_SHA256=" + b"a" * 64 + b"\n"
            env.write_bytes(original)
            for name in ("local.env", "release.env", "recipe.env"):
                path = runtime / name
                path.touch()
                path.chmod(0o600)
            lane = {
                "compose_project": "pals-reliability-local-standby", "candidate_sha256": "b" * 64,
                "environment_files": [str(runtime / name) for name in ("local.env", "release.env", "recipe.env")],
                "base_files": [], "profile_overlay_yaml": "services: {}", "relay_overlay_yaml": "services: {}",
            }
            scope = {"docker_socket": "/private/socket", "lane": {**lane, "http_ports": {"api": 58001}}}
            value = {"local_lane": {"candidate_sha256": "b" * 64}, "preparation": {},
                     "guard": {"resumed_budget": {"sha256": "c" * 64}}}
            rendered = runtime / "compose.json"
            rendered.write_text(json.dumps({"status": "rendered_relay_compose", "activation_authorized": False,
                                            "budget_continuity": {"sha256": "c" * 64}, "lanes": {"standby": lane}}))
            args = SimpleNamespace(role="standby", state_dir=subject_dir, rendered_compose=rendered,
                                   rendered_compose_sha256=freezer.gate.sha(rendered.read_bytes()), compose_root=runtime,
                                   initial_candidate_sha256=initial_seed)
            recreations = []
            config_headers = []

            def command(argv, **options):
                if argv[-3:] == ["config", "--hash", "api"]:
                    config_headers.append(options["env"].get("PALS_LOCAL_CANDIDATE_SHA256"))
                    return "api initial-config-hash\n"
                recreations.append((argv, dict(options["env"]), env.read_bytes()))

            def round_once(_subject, _api, write, _inspect):
                write()

            health = Mock(side_effect=[None, freezer.gate.Refusal("bad_header"), None] if failed else None)
            with patch.dict(os.environ, {"OPENAI_API_KEY": "forbidden-fixture", "PALS_API_HOST_PORT": "9999"}), patch.object(
                freezer.gate, "lane_runtime", return_value=scope
            ), patch.object(freezer.gate, "scoped_docker", return_value=json.dumps([
                {"Config": {"Labels": {"com.docker.compose.config-hash": "initial-config-hash"}}}
            ])), patch.object(
                freezer.gate, "command", side_effect=command
            ), patch.object(freezer.gate, "runtime"), patch.object(
                freezer.prepare, "freeze_until_api_is_stable", side_effect=round_once
            ), patch.object(freezer, "api_header", health):
                if initial_seed == "d" * 64:
                    with self.assertRaisesRegex(freezer.gate.Refusal, "initial_lane_api_header_differs_from_candidate"):
                        freezer.bind_api(args, value, out)
                    health.assert_not_called()
                    self.assertFalse(recreations)
                    return
                if failed:
                    with self.assertRaisesRegex(freezer.gate.Refusal, "bad_header"):
                        freezer.bind_api(args, value, out)
                else:
                    freezer.bind_api(args, value, out)
            self.assertEqual(out.exists(), not failed)
            self.assertFalse((runtime / "api-binding-recovery").exists())
            self.assertEqual(env.read_bytes(), original)
            self.assertEqual(len(recreations), 2 if failed else 1)
            self.assertEqual(config_headers, [initial_seed])
            for argv, environment, _ in recreations:
                self.assertEqual(argv[:4], ["docker", "--host", "unix:///private/socket", "compose"])
                self.assertIn(lane["compose_project"], argv)
                self.assertEqual(argv[-8:], ["up", "-d", "--no-deps", "--no-build", "--wait", "--wait-timeout", "45", "api"])
                self.assertNotIn("OPENAI_API_KEY", environment)
                self.assertNotIn("PALS_API_HOST_PORT", environment)
            final_digest = freezer.gate.sha(freezer.subject_bytes(value))
            if initial_seed is None:
                self.assertIn(final_digest.encode(), recreations[0][2])
                self.assertEqual(recreations[1][2], original)
            else:
                self.assertEqual(recreations[0][1]["PALS_LOCAL_CANDIDATE_SHA256"], final_digest)
                self.assertTrue(all(raw == original for _, _, raw in recreations))
                if failed:
                    self.assertEqual(recreations[1][1]["PALS_LOCAL_CANDIDATE_SHA256"], initial_seed)
