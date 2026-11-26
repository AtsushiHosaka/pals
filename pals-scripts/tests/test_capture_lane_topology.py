"""Capture fixtures through the real read-only topology checks, without Docker."""

import json
import unittest
from pathlib import Path
from unittest.mock import patch

import test_local_qualification as fixture

import capture_lane_topology as capture
import lane_database
import relay_topology


class CaptureLaneTopologyTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture.QualificationLaneLayoutTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root.resolve()
        self.fixture.root = self.root
        layout = self.fixture.document
        self.rows, self.relay = self.fixture.relay_rows()
        self.resume = "c" * 64
        self.ledger = self.root / "original-runtime" / "budget"
        self.ledger.mkdir(parents=True)
        self.rows[0]["budget_resume_sha256"] = self.resume
        self.rows[0]["mounts"][0]["Source"] = str(self.ledger)
        self.output = self.root / "new-topology"
        self.database = self.root / "database.json"
        self.captures = {}
        self.volumes = {}
        document = {"schema_version": lane_database.SCHEMA, "docker_socket": layout["docker_socket"], "lanes": {}}
        for role, lane in layout["lanes"].items():
            runtime = Path(lane["runtime_directory"]).resolve()
            self.captures[role] = Path(lane["capture_directory"]).resolve()
            postgres = next(row for row in self.rows if row["name"] == "/" + lane["postgres"]["name"])
            postgres["health"] = "healthy"
            project = lane["compose_project"]
            volume = f"{project}-postgres-data"
            postgres["mounts"][0]["Name"] = volume
            self.volumes[volume] = {"Name": volume, "Driver": "local", "Options": None,
                                    "Mountpoint": postgres["mounts"][0]["Source"],
                                    "Labels": {"com.docker.compose.project": project, "com.docker.compose.volume": "postgres-data"}}
            document["lanes"][role] = {
                "candidate_sha256": lane["candidate_sha256"], "compose_project": lane["compose_project"],
                "runtime_directory": str(runtime), "local_env": {"path": str(runtime / "local.env"), "sha256": "1" * 64},
                "postgres": {**lane["postgres"], "image_id": postgres["image"]},
            }
        raw = capture.encode(document)
        self.database.write_bytes(raw)
        self.database.chmod(0o600)
        self.database_sha256 = fixture.sha256(raw)

    def capture(self, **harness):
        calls, fixture_run = self.fixture.fixture_docker(self.rows, **harness)

        def run(*args):
            if args[:2] == ("volume", "inspect"):
                calls.append("volume")
                return json.dumps([self.volumes[args[2]]])
            return fixture_run(*args)

        with patch.object(capture, "socket_identity", return_value=(1, 2)):
            result = capture.capture(self.database, self.database_sha256, self.captures, self.ledger,
                                     self.resume, self.output, run=run)
        return calls, run, result

    def test_emits_pair_that_the_existing_verifier_reads_back(self):
        calls, run, result = self.capture()
        self.assertEqual(calls, ["ps", "inspect", "volume", "volume", "ps", "inspect", "top", "top", "top", "top",
                                 "ps", "inspect", "ps", "inspect", "volume", "volume"])
        topology = relay_topology.read(**result["topology"])
        self.assertEqual(topology["layout"], result["layout"])
        self.assertEqual(topology["authority_shim"], self.relay["authority_shim"])
        self.assertEqual(topology["lanes"], self.relay["lanes"])
        self.assertEqual(relay_topology.verify(topology, run=run), result["topology_sha256"])
        self.assertEqual(self.output.stat().st_mode & 0o777, 0o700)
        for path in self.output.iterdir():
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_refuses_foreign_actor_namespace_and_does_not_publish(self):
        forwarder = next(row for row in self.rows if row["name"].endswith("-standby-provider-relay-1"))
        forwarder["namespace"] = "container:" + self.relay["lanes"]["primary"]["policy"]["container_id"]
        with self.assertRaisesRegex(ValueError, "local_relay_network_namespace_differs"):
            self.capture()
        self.assertFalse(self.output.exists())

    def test_refuses_database_volume_attached_to_a_stopped_foreign_container(self):
        postgres = next(row for row in self.rows if row["name"].endswith("-standby-postgres-1"))
        self.rows.append({**postgres, "id": "e" * 64, "name": "/foreign", "running": False, "networks": {}})
        with self.assertRaisesRegex(ValueError, "lane_database_volume_in_use_elsewhere"):
            self.capture()
        self.assertFalse(self.output.exists())

    def test_cannot_replace_the_pinned_database_or_budget_authority(self):
        postgres = next(row for row in self.rows if row["name"].endswith("-standby-postgres-1"))
        image = postgres["image"]
        postgres["image"] = "sha256:" + "2" * 64
        with self.assertRaisesRegex(ValueError, "exact_lane_database_container_required"):
            self.capture()
        postgres["image"] = image
        self.rows[0]["budget_resume_sha256"] = "d" * 64
        with self.assertRaisesRegex(ValueError, "shared_guard_budget_startup_pin_differs"):
            self.capture()
        self.assertFalse(self.output.exists())

    def test_proof_is_closed_on_live_drift_or_output_reuse(self):
        with self.assertRaisesRegex(ValueError, "local_lane_topology_changed_during_read"):
            self.capture(changed_after_top=True)
        self.assertFalse(self.output.exists())
        self.output.mkdir(mode=0o700)
        marker = self.output / "existing.json"
        marker.write_text(json.dumps({"existing": True}))
        with self.assertRaisesRegex(ValueError, "unused_lane_topology_output_required"):
            self.capture()
        self.assertEqual(list(self.output.iterdir()), [marker])


if __name__ == "__main__":
    unittest.main()
