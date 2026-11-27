"""Authoritative ledger transfer observations using fake Docker inventory only."""

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "local-qualification"))

from budget_handoff import GUARD, OWNER, PREFIX, PROJECT, SERVICE, verify_budget_handoff
from budget_proxy import LIMIT


def container(identifier, project, service, *, owner=OWNER, active=False, source=None, entrypoint=None):
    return {
        "id": identifier * 64, "name": f"/{project}-{service}-1",
        "labels": {PROJECT: project, SERVICE: service, "codex.owner": owner},
        "entrypoint": entrypoint,
        "status": "running" if active else "exited", "running": active, "pid": 123 if active else 0,
        "started_at": "2026-11-27T00:00:00Z", "finished_at": "2026-11-27T01:00:00Z",
        "mounts": [] if source is None else [{"Type": "bind", "Source": str(source),
                                               "Destination": "/run/budget", "RW": True}],
    }


class BudgetHandoffTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.original = Path(directory.name).resolve()
        self.path = self.original / "ledger.json"
        self.value = {"actual_microusd": 10, "reserved_microusd": 10, "limit_microusd": LIMIT,
                      "calls": [{"state": "completed", "model": "gpt-6.1-terra", "input_tokens": 0,
                                 "output_tokens": 2, "actual_microusd": 10}], "blocked": False}
        self.write_ledger()

    def write_ledger(self):
        raw = json.dumps(self.value).encode()
        self.path.write_bytes(raw)
        self.path.chmod(0o600)
        self.digest = hashlib.sha256(raw).hexdigest()
        self.reference = {"path": str(self.path), "sha256": self.digest}

    def verify(self, first, second=None, *, reference=None, expected=None):
        inventories = iter((first, first if second is None else second))
        by_id = {}

        def run(*args):
            if args == ("ps", "--all", "--quiet", "--no-trunc"):
                by_id.clear()
                by_id.update((row["id"], row) for row in next(inventories))
                return "\n".join(by_id)
            self.assertEqual(args[:4], ("inspect", "--type", "container", "--format"))
            return "\n".join(json.dumps(by_id[key]) for key in args[5:])

        return verify_budget_handoff("/unused.sock", reference or self.reference, str(self.original),
                                     expected or self.digest, run=run)

    def test_stopped_exact_guard_preserves_ledger_and_allows_passive_database(self):
        guard = container("a", PREFIX, GUARD, source=self.original)
        producer = container("b", PREFIX, "worker")
        dependency = container("c", PREFIX, "postgres", active=True)
        before = self.path.read_bytes()
        result = self.verify([guard, producer, dependency])
        self.assertEqual(result["status"], "verified_read_only")
        self.assertEqual(result["legacy_guard"], "stopped")
        self.assertEqual(result["observed_stopped_container_ids"], [guard["id"], producer["id"]])
        self.assertEqual(result["actual_microusd"], 10)
        self.assertEqual(self.path.read_bytes(), before)

    def test_absent_guard_requires_exact_archived_identity_and_hash(self):
        self.assertEqual(self.verify([])["legacy_guard"], "absent")
        for reference, expected, refusal in (
            ({**self.reference, "path": str(self.original / "copy" / "ledger.json")}, None,
             "must_match_original_archive"),
            (None, "f" * 64, "must_match_original_archive"),
            ({**self.reference, "sha256": "f" * 64}, "f" * 64, "archived_budget_ledger_hash_differs"),
        ):
            with self.subTest(refusal=refusal), self.assertRaisesRegex(ValueError, refusal):
                self.verify([], reference=reference, expected=expected)

    def test_unsettled_calls_are_refused_even_with_an_exact_archive_match(self):
        self.value["calls"][0]["state"] = "in_flight"
        self.write_ledger()
        with self.assertRaisesRegex(ValueError, "known_existing_budget_required_no_reset"):
            self.verify([])

    def test_reprices_completed_rows_using_the_guard_rate_table(self):
        self.value["calls"][0]["output_tokens"] = 3
        self.write_ledger()
        with self.assertRaisesRegex(ValueError, "previous_budget_usage_changed"):
            self.verify([])

    def test_refuses_active_legacy_producers_and_another_guard_on_a_different_mount(self):
        for actor in (container("a", PREFIX, "worker", active=True),
                      container("b", "alternate-project", GUARD, active=True, source="/different"),
                      container("c", "alternate-project", "unexpected-role", active=True, source="/different"),
                      container("d", "alternate-project", "unexpected-role", active=True,
                                entrypoint=["python", "/opt/pals-local/guard.py"])):
            with self.subTest(actor=actor["name"]), self.assertRaisesRegex(ValueError, "not_stopped"):
                self.verify([actor])

    def test_foreign_active_bind_over_original_ledger_is_refused(self):
        actor = container("a", "foreign-project", "worker", owner="other", active=True, source=self.original)
        actor["mounts"][0]["Destination"] = "/other-path"
        with self.assertRaisesRegex(ValueError, "not_stopped"):
            self.verify([actor])

    def test_refuses_legacy_guard_on_another_mount_or_with_foreign_ownership(self):
        with self.assertRaisesRegex(ValueError, "did_not_mount_original_ledger"):
            self.verify([container("a", PREFIX, GUARD, source="/different")])
        with self.assertRaisesRegex(ValueError, "foreign_legacy_budget_container_refused"):
            self.verify([container("a", PREFIX, GUARD, source=self.original, owner="other")])

    def test_refuses_changed_legacy_inventory(self):
        with self.assertRaisesRegex(ValueError, "changed_during_observation"):
            self.verify([], [container("a", PREFIX, GUARD, source=self.original)])


if __name__ == "__main__":
    unittest.main()
