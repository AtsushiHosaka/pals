"""Validate the rendered local deployment's independent delivery paths."""

import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which("docker"), "Docker Compose is required")
class WorkerLanesComposeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        command = ["docker", "compose", "--project-name", "pals-local",
                   "--env-file", str(ROOT / ".env.example")]
        for path in ("docker-compose.yml", "pals-infra/docker-compose.localstack.yml",
                     "docker-compose.e2e.yml"):
            command.extend(["-f", str(ROOT / path)])
        result = subprocess.run(command + ["config", "--format", "json"],
                                cwd=ROOT, capture_output=True, text=True, check=True)
        cls.services = json.loads(result.stdout)["services"]

    def test_api_routes_to_the_queue_consumed_only_by_assessment_workers(self):
        api = self.services["api"]["environment"]
        assessment = self.services["assessment-worker"]
        proof = self.services["worker"]
        request_queue = api["PALS_SQS_PROOF_REQUESTS_QUEUE_URL"]
        self.assertNotEqual(request_queue, api["PALS_SQS_PROOF_JOBS_QUEUE_URL"])
        self.assertEqual(request_queue,
                         assessment["environment"]["PALS_SQS_PROOF_REQUESTS_QUEUE_URL"])
        self.assertIn("assessment", assessment["command"])
        self.assertIn("all", proof["command"])
        self.assertEqual(assessment["environment"]["PALS_PROOF_CAPABILITY"], "natural-only")
        self.assertNotIn("ipv4_address", assessment["networks"]["e2e"])
        self.assertEqual(assessment["image"], proof["image"])

    def test_assessment_replicas_have_resource_and_database_boundaries(self):
        assessment = self.services["assessment-worker"]
        self.assertGreater(int(assessment["mem_limit"]), 0)
        self.assertEqual(assessment["mem_limit"], assessment["memswap_limit"])
        self.assertGreater(float(assessment["cpus"]), 0)
        self.assertTrue(assessment["read_only"])
        self.assertEqual(set(assessment["networks"]), {"e2e"})
        self.assertEqual(assessment["entrypoint"],
                         ["python", "-m", "pals_agent.local_worker_boundary"])
        self.assertNotIn("verifier", assessment["depends_on"])
        self.assertNotIn("recipe-reviewer", assessment["depends_on"])


if __name__ == "__main__":
    unittest.main()
