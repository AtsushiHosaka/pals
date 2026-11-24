"""Pure tests of the rearchitecture measurements (pals#485). No git, no network."""

import importlib.util
from pathlib import Path
import tempfile
import unittest

PATH = Path(__file__).resolve().parents[1] / "measure-codebase.py"
SPEC = importlib.util.spec_from_file_location("measure_codebase", PATH)
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def step(start, end):
    return {"started_at": start, "completed_at": end}


class Percentiles(unittest.TestCase):
    def test_median_and_tail_use_the_plan_rule(self):
        values = [5.0, 1.0, 3.0, 2.0, 4.0]
        self.assertEqual(m.percentile(values, 0.5), 3.0)
        self.assertEqual(m.percentile(values, 0.9), 5.0)
        self.assertIsNone(m.percentile([], 0.5))
        self.assertEqual(m.summary([]), {"n": 0, "p50": None, "p90": None, "max": None})


class Churn(unittest.TestCase):
    LOG = "@2026-11-20\na.py\ntest_a.py\n\n@2026-10-02\na.py\nb.py\n\n@2026-11-21\nb.py\n"

    def test_commits_recent_and_co_change(self):
        commits = m.parse_log(self.LOG)
        self.assertEqual(len(commits), 3)
        result = m.churn(commits, "a.py", "2026-10-25")
        self.assertEqual(result["commits"], 2)
        self.assertEqual(result["commits_recent"], 1)
        self.assertEqual(sorted(result["co_changed"]), [["b.py", 1], ["test_a.py", 1]])

    def test_lines_count_newline_bytes_like_wc(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "f.py"
            path.write_bytes(b"a\nb\nc")
            self.assertEqual(m.count_lines(path), 2)


class Occupancy(unittest.TestCase):
    def test_queued_time_of_a_cancelled_job_is_not_occupancy(self):
        job = {"runner_name": "r1", "conclusion": "cancelled",
               "started_at": "2026-11-18T00:00:00Z", "completed_at": "2026-11-18T01:00:00Z",
               "steps": [step("2026-11-18T00:50:00Z", "2026-11-18T00:52:00Z"), step("2026-11-18T00:52:00Z", "2026-11-18T00:55:00Z")]}
        self.assertAlmostEqual(m.job_occupancy(job), 5.0)

    def test_a_job_no_runner_picked_up_occupies_nothing(self):
        self.assertEqual(m.job_occupancy({"runner_name": None, "steps": [step("2026-11-18T00:00:00Z", "2026-11-18T00:10:00Z")]}), 0.0)
        self.assertEqual(m.job_occupancy({"runner_name": "r1", "conclusion": "skipped", "steps": []}), 0.0)

    def test_ci_summary_separates_occupancy_from_elapsed(self):
        runs = [
            {"id": 1, "conclusion": "success", "created_at": "2026-11-18T00:00:00Z", "run_started_at": "2026-11-18T00:00:00Z", "updated_at": "2026-11-18T00:20:00Z"},
            {"id": 2, "conclusion": "cancelled", "created_at": "2026-11-18T00:00:00Z", "run_started_at": "2026-11-18T00:00:00Z", "updated_at": "2026-11-18T00:30:00Z"},
        ]
        jobs = {
            1: [{"name": "j", "runner_name": "r", "conclusion": "success", "created_at": "2026-11-18T00:00:00Z",
                 "started_at": "2026-11-18T00:02:00Z", "completed_at": "2026-11-18T00:20:00Z",
                 "steps": [step("2026-11-18T00:02:00Z", "2026-11-18T00:20:00Z")]}],
            2: [{"name": "j", "runner_name": "r", "conclusion": "cancelled", "created_at": "2026-11-18T00:00:00Z",
                 "started_at": "2026-11-18T00:00:00Z", "completed_at": "2026-11-18T00:30:00Z",
                 "steps": [step("2026-11-18T00:28:00Z", "2026-11-18T00:30:00Z")]}],
        }
        result = m.ci_summary(runs, jobs)
        self.assertEqual(result["runs"], {"success": 1, "cancelled": 1})
        self.assertEqual(result["runner_occupancy_min"], {"success": 18, "cancelled": 2})
        self.assertEqual(result["elapsed_min"], {"success": 20, "cancelled": 30})
        self.assertEqual(result["cancelled_share_of_occupancy"], 0.1)
        self.assertEqual(result["cancelled_share_of_elapsed"], 0.6)
        self.assertEqual(result["wall_success_min"]["p50"], 20.0)
        self.assertEqual(result["job_queue_min"]["p50"], 2.0)


class LeadTime(unittest.TestCase):
    def test_open_to_merge_hours(self):
        prs = [{"createdAt": "2026-11-18T00:00:00Z", "mergedAt": "2026-11-18T02:00:00Z", "changedFiles": 3, "additions": 10, "deletions": 5}]
        result = m.lead_times(prs)
        self.assertEqual(result["merged"], 1)
        self.assertEqual(result["open_to_merge_h"]["p50"], 2.0)
        self.assertEqual(result["changed_lines"]["p50"], 15)


if __name__ == "__main__":
    unittest.main()
