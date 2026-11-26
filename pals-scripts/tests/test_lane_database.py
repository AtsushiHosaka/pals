"""Verify the pre-guard database binding without Docker or PostgreSQL."""

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "local-qualification"))

import lane_database as subject
from lanes import ENDPOINTS, PREFIX


class DatabaseLaneTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.descriptor = {
            "schema_version": subject.SCHEMA, "docker_socket": str(self.root / "fake.sock"),
            "lanes": {},
        }
        self.rows = {}
        self.volumes = {}
        for i, (role, ports) in enumerate(ENDPOINTS.items(), 1):
            runtime = self.root / role
            runtime.mkdir(mode=0o700)
            project = f"{PREFIX}-{role}"
            name = project + "-postgres-1"
            volume = project + "-postgres-data"
            image = "sha256:" + "a" * 64
            container_id = str(i) * 64
            self.descriptor["lanes"][role] = {
                "candidate_sha256": container_id,
                "compose_project": project,
                "runtime_directory": str(runtime),
                "local_env": {"path": str(runtime / "local.env"), "sha256": "3" * 64},
                "postgres": {"name": name, "container_id": container_id, "image_id": image,
                             "host": "127.0.0.1", "host_port": ports["postgres"], "database": "pals"},
            }
            self.rows["/" + name] = {
                "id": container_id, "image": image, "privileged": False, "networks": {project + "-database": {}},
                "labels": {"codex.owner": subject.OWNER, subject.PROJECT: project, subject.SERVICE: "postgres"},
                "ports": {"5432/tcp": [{"HostIp": "127.0.0.1", "HostPort": str(ports["postgres"])}]},
                "running": True, "pid": 100 + i, "started_at": "2026-11-27T10:00:00Z", "health": "healthy",
                "mounts": [{"Destination": "/var/lib/postgresql/data", "Type": "volume", "RW": True,
                            "Name": volume, "Source": f"/docker/{volume}"}],
            }
            self.volumes[volume] = {"Name": volume, "Options": None, "Driver": "local",
                                    "Mountpoint": f"/docker/{volume}",
                                    "Labels": {subject.PROJECT: project, "com.docker.compose.volume": "postgres-data"}}

    def inspect_volume(self, *args):
        assert args[:2] == ("volume", "inspect")
        return json.dumps([self.volumes[args[2]]])

    def test_freeze_uses_exact_dependency_input_and_no_guard(self):
        binding = {"local_envs": {role: item["local_env"] for role, item in self.descriptor["lanes"].items()},
                   "docker_socket": self.descriptor["docker_socket"], "rendered_compose": {}}
        rendered = {"lanes": self.descriptor["lanes"]}
        plans = {
            role: ([], json.dumps({"services": {"postgres": {"image": item["postgres"]["image_id"]}}}), {})
            for role, item in self.descriptor["lanes"].items()
        }
        with (
            patch("lane_dependencies.derive", return_value=(plans, None, None)),
            patch("lane_dependencies.checked_render", return_value=rendered),
            patch.object(subject, "docker_reader", return_value=self.inspect_volume),
            patch.object(subject, "inventory", return_value=self.rows),
        ):
            self.assertEqual(subject.freeze(binding), self.descriptor)
        self.assertNotIn("guard", self.descriptor)
        with self.assertRaisesRegex(ValueError, "lane_database_binding_invalid"):
            subject.validate_database_layout({**self.descriptor, "guard": {"container_id": "0" * 64}})

    def test_refuses_both_wrong_database_ports_and_images(self):
        standby = self.descriptor["lanes"]["standby"]
        row = self.rows["/" + standby["postgres"]["name"]]
        row["ports"]["5432/tcp"][0]["HostPort"] = "55432"
        with self.assertRaisesRegex(ValueError, "local_lane_loopback_binding_differs"):
            subject.verify_databases(self.descriptor, self.inspect_volume, self.rows)
        row["image"] = "sha256:" + "4" * 64
        with self.assertRaisesRegex(ValueError, "exact_lane_database_container_required"):
            subject.verify_databases(self.descriptor, self.inspect_volume, self.rows)

    def test_refuses_other_writers_and_wrong_volume_ownership(self):
        primary = self.descriptor["lanes"]["primary"]
        project = primary["compose_project"]
        foreign = {"id": "d" * 64, "running": True, "networks": {}, "labels": {
            subject.PROJECT: project, subject.SERVICE: "schema-release",
        }}
        with self.assertRaisesRegex(ValueError, "local_lane_database_producers_must_be_stopped"):
            subject.verify_databases(self.descriptor, self.inspect_volume, {**self.rows, "/schema-release": foreign})
        foreign["labels"] = {}
        foreign["networks"] = {project + "-database": {}}
        with self.assertRaisesRegex(ValueError, "local_lane_database_producers_must_be_stopped"):
            subject.verify_databases(self.descriptor, self.inspect_volume, {**self.rows, "/unlabelled-writer": foreign})
        del self.volumes[project + "-postgres-data"]["Labels"][subject.PROJECT]
        with self.assertRaisesRegex(ValueError, "owned_lane_database_volume_required"):
            subject.verify_databases(self.descriptor, self.inspect_volume, self.rows)

    def test_one_interrupted_lane_never_restarts_partially_written_schema_or_changes_peer(self):
        def state(role):
            selected = self.descriptor["lanes"][role]
            return subject.migration_state(Path(selected["runtime_directory"]), selected)

        with state("primary") as begin:
            begin(True)
        receipt = self.root / "primary/database-bootstrap.json"
        primary_before = receipt.read_bytes()
        self.assertEqual(receipt.stat().st_mode & 0o777, 0o600)
        with self.assertRaisesRegex(RuntimeError, "unexpected disconnect"):
            with state("standby") as begin:
                begin(True)
                raise RuntimeError("unexpected disconnect")
        self.assertEqual(receipt.read_bytes(), primary_before)
        self.assertEqual(json.loads((self.root / "standby/database-bootstrap.json").read_bytes())["state"], "incomplete")
        with self.assertRaisesRegex(ValueError, "lane_database_bootstrap_requires_inspection"):
            with state("standby"):
                self.fail("partial migration replayed")
        with state("primary") as begin:
            begin(False)
        self.assertEqual(receipt.read_bytes(), primary_before)

    def test_refuses_nonempty_untracked_database_before_mutation(self):
        primary = self.descriptor["lanes"]["primary"]
        with self.assertRaisesRegex(ValueError, "lane_database_bootstrap_requires_inspection"):
            with subject.migration_state(self.root / "primary", primary) as begin:
                begin(False)
        self.assertFalse((self.root / "primary/database-bootstrap.json").exists())


if __name__ == "__main__":
    unittest.main()
