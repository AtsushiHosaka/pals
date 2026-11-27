"""Lane cleanup lists by default, removes only exact lane resources and proves the result."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "local-qualification"))

import lane_cleanup as cleanup  # noqa: E402
from lane_topology import PROJECT  # noqa: E402


class Docker:
    def __init__(self, present):
        self.present = {kind: set(names) for kind, names in present.items()}
        self.calls = []

    def read(self, argv):
        kind, *rest = argv
        label = next((item for item in rest if item.startswith("label=")), None)
        name = next((item for item in rest if item.startswith("name=")), None)
        self.calls.append(argv)
        rows = self.present.get(kind, set())
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
