"""Policy shape and fail-closed startup tests, without modifying host rules."""

import importlib.util
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

source = Path(__file__).resolve().parents[1] / "local-qualification/lane_guard.py"
spec = importlib.util.spec_from_file_location("lane_guard", source)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class LaneGuardTests(unittest.TestCase):
    def test_worker_destinations_are_only_loopback_and_own_lane(self):
        for lane, prefix in guard.LANE_PREFIX.items():
            with self.subTest(lane=lane):
                document = guard.rules(lane)
                other_lanes = set(guard.LANE_PREFIX.values()) - {prefix}
                for other in other_lanes:
                    self.assertNotIn(other + ".", document)
                expected = {
                    "65532 ip daddr 127.0.0.11 udp dport 53 accept",
                    "65532 ip daddr 127.0.0.11 tcp dport 53 accept",
                    "65532 ip daddr 127.0.0.1 tcp dport 443 accept",
                    f"65532 ip daddr {prefix}.3 tcp dport 4566 accept",
                    f"65532 ip daddr {prefix}.20 tcp dport 8000 accept",
                    f"65532 ip daddr {prefix}.30 tcp dport 18119 accept",
                }
                lines = [line.strip().removeprefix("meta skuid ") for line in document.splitlines()]
                self.assertEqual({line for line in lines if line.startswith("65532 ip daddr ")}, expected)
                self.assertEqual(lines[-3], "{ 65531, 65532 } reject")

    def test_rule_installation_failure_never_marks_ready(self):
        with patch.object(guard, "READY") as ready, patch.object(guard, "signal"), patch.object(
            guard.subprocess, "run", side_effect=subprocess.CalledProcessError(1, "nft")
        ):
            with self.assertRaises(subprocess.CalledProcessError):
                guard.main(["primary"])
            ready.write_text.assert_not_called()
