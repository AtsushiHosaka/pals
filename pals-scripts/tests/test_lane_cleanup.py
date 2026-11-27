"""Lane cleanup lists by default, removes only exact lane resources and proves the result."""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "local-qualification"))

import lane_cleanup as cleanup  # noqa: E402
from lane_topology import PROJECT  # noqa: E402


class Docker:
    def __init__(self, present, running=()):
        self.present = {kind: set(names) for kind, names in present.items()}
        self.running = set(running)
        self.calls = []

    def read(self, argv):
        kind, *rest = argv
        label = next((item for item in rest if item.startswith("label=")), None)
        name = next((item for item in rest if item.startswith("name=")), None)
        self.calls.append(argv)
        rows = self.present.get(kind, set())
        if kind == "container" and "--all" not in rest:
            rows = rows & self.running
        if label:
            scope = label.split("=", 2)[2]
            return sorted(row for row in rows if row.startswith(scope))
        if name:
            exact = name.split("=", 1)[1].lstrip("^").rstrip("$").replace("\\", "")
            return sorted(row for row in rows if row == exact)
        raise AssertionError(argv)

    def run(self, argv):
        kind, verb, *names = argv
        self.calls.append(argv)
        assert verb == "rm"
        self.present[kind] -= {name for name in names if not name.startswith("--")}
        self.running -= {name for name in names if not name.startswith("--")}
        return []


LEFT = {
    "container": {"pals-reliability-local-primary-api-1", "pals-reliability-local-shared-guard-1",
                  "unrelated-api-1"},
    "network": {"pals-reliability-local-standby_default"},
    "volume": {"pals-reliability-local-primary-pgdata", "pals-reliability-local-provider-socket", "other-volume"},
}


class LaneCleanupTests(unittest.TestCase):
    def test_default_only_lists_and_never_removes(self):
        docker = Docker(LEFT)
        report = cleanup.cleanup(read=docker.read, run=docker.run)
        self.assertEqual(report["status"], "lane_cleanup_preview")
        self.assertEqual(docker.present, {kind: set(names) for kind, names in LEFT.items()})
        self.assertIn("pals-reliability-local-shared-guard-1", report["resources"]["container"])
        self.assertNotIn("unrelated-api-1", report["resources"]["container"])
        self.assertNotIn("other-volume", report["resources"]["volume"])

    def test_apply_removes_exactly_the_lane_resources_containers_first(self):
        docker = Docker(LEFT)
        report = cleanup.cleanup(apply=True, read=docker.read, run=docker.run)
        self.assertEqual(report["status"], "lane_cleanup_done")
        self.assertEqual(docker.present["container"], {"unrelated-api-1"})
        self.assertEqual(docker.present["volume"], {"other-volume"})
        self.assertEqual(docker.present["network"], set())
        removals = [argv[0] for argv in docker.calls if argv[1] == "rm"]
        self.assertEqual(removals, ["container", "network", "volume"])

    def test_running_lane_container_refuses_everything_but_still_previews(self):
        docker = Docker(LEFT, running={"pals-reliability-local-shared-guard-1"})
        self.assertEqual(cleanup.cleanup(read=docker.read, run=docker.run)["status"], "lane_cleanup_preview")
        with self.assertRaisesRegex(ValueError, "lane_cleanup_running_containers"):
            cleanup.cleanup(apply=True, read=docker.read, run=docker.run)
        self.assertEqual(docker.present, {kind: set(names) for kind, names in LEFT.items()})
        self.assertEqual([a for a in docker.calls if a[1] == "rm"], [])

    def test_running_lane_api_container_is_refused(self):
        docker = Docker(LEFT, running={"pals-reliability-local-primary-api-1"})
        with self.assertRaisesRegex(ValueError, "lane_cleanup_running_containers"):
            cleanup.cleanup(apply=True, read=docker.read, run=docker.run)
        self.assertEqual([a for a in docker.calls if a[1] == "rm"], [])

    def test_removal_never_forces_a_running_container(self):
        docker = Docker(LEFT)
        cleanup.cleanup(apply=True, read=docker.read, run=docker.run)
        removals = [a for a in docker.calls if a[1] == "rm"]
        self.assertTrue(removals and all("--force" not in a and "-f" not in a for a in removals))

    def test_main_exits_2_with_the_refusal_code_and_removes_nothing(self):
        docker = Docker(LEFT, running={"pals-reliability-local-primary-api-1"})
        out = io.StringIO()
        with mock.patch.object(cleanup, "docker_runner", return_value=docker.read), \
                contextlib.redirect_stdout(out):
            code = cleanup.main(["--docker", "/x/docker", "--docker-socket", "/x/sock", "--apply"])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(out.getvalue()), {"status": "refused", "code": "lane_cleanup_running_containers"})
        self.assertEqual([a for a in docker.calls if a[1] == "rm"], [])

    def test_unrelated_running_container_does_not_block(self):
        docker = Docker(LEFT, running={"unrelated-api-1"})
        self.assertEqual(cleanup.cleanup(apply=True, read=docker.read, run=docker.run)["status"], "lane_cleanup_done")

    def test_cli_and_socket_must_be_explicit_and_exact(self):
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "docker"
            binary.write_text("#!/bin/sh\n")
            binary.chmod(0o700)
            with self.assertRaisesRegex(ValueError, "exact_local_docker_cli_required"):
                cleanup.docker_runner("docker", "/var/run/docker.sock")
            with self.assertRaisesRegex(ValueError, "exact_local_docker_cli_required"):
                cleanup.docker_runner(Path(directory) / "other", "/var/run/docker.sock")
            with self.assertRaisesRegex(ValueError, "exact_local_docker_socket_required"):
                cleanup.docker_runner(binary, Path(directory) / "missing.sock")
            with self.assertRaisesRegex(ValueError, "exact_local_docker_socket_required"):
                cleanup.docker_runner(binary, binary)  # a regular file is not a socket

    def test_incomplete_removal_is_refused(self):
        docker = Docker(LEFT)
        docker.run = lambda argv: []
        with self.assertRaisesRegex(ValueError, "lane_cleanup_incomplete"):
            cleanup.cleanup(apply=True, read=docker.read, run=docker.run)

    def test_nothing_left_is_a_clean_preview(self):
        docker = Docker({})
        report = cleanup.cleanup(apply=True, read=docker.read, run=docker.run)
        self.assertEqual(report["resources"], {"container": [], "network": [], "volume": []})
        self.assertEqual([a for a in docker.calls if a[1] == "rm"], [])

    def test_selection_uses_the_exact_compose_project_label(self):
        docker = Docker(LEFT)
        cleanup.inventory(docker.read)
        labels = {argv[-3] for argv in docker.calls if argv[-3].startswith("label=")}
        self.assertTrue(labels and all(label.startswith(f"label={PROJECT}=pals-reliability-local-") for label in labels))


if __name__ == "__main__":
    unittest.main()
