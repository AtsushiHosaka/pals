"""Deterministic contracts for release-post-request.py with a fake transport. No network."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

HERE = Path(__file__).resolve().parents[1]


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = load("release_acceptance", "release-acceptance.py")
post = load("release_post_request", "release-post-request.py")
CAND = "a" * 64
SECRET_STATEMENT = "PRIVATE-STATEMENT-DO-NOT-LEAK"


class Fake:
    def __init__(self, replay_safe=True, statuses=("queued",)):
        self.replay_safe, self.statuses = replay_safe, list(statuses)
        self.calls, self.requests = [], {}
        self.chat = str(uuid4())
        self.crash_after_create = False

    def create_chat(self):
        self.calls.append("create_chat")
        return self.chat

    def create_request(self, chat_id, key, scenario):
        self.calls.append("create_request")
        if key not in self.requests:  # server-side Idempotency-Key replay
            self.requests[key] = str(uuid4())
        if self.crash_after_create:
            self.crash_after_create = False
            raise ConnectionError("lost reply")
        return self.requests[key]

    def observe(self, request_id):
        self.calls.append("observe")
        status = self.statuses.pop(0) if len(self.statuses) > 1 else self.statuses[0]
        return {"id": request_id, "chat_id": self.chat, "status": status}


def private(path, value):
    path.write_text(value if isinstance(value, str) else json.dumps(value))
    path.chmod(0o600)
    return path


def contract(**over):
    value = {
        "schema_version": gate.SCHEMA, "phase": "post_deployment", "target": "production",
        "manifest": {"path": "/m", "sha256": CAND, "signature_path": "/s", "public_key_path": "/k",
                     "public_key_spki_sha256": "2" * 64},
        "runtime": {role: {"ssm": {"profile": "pals-prod-member", "region": "ap-northeast-1",
                                    "account_id": "123456789012", "instance_id": "i-0123456789abcdef0"},
                           "container": "c-" + role, "config_sha256": "4" * 64,
                           "environment_sha256": "5" * 64} for role in gate.ROLES},
        "runner_sha256": gate.runner_fingerprint(), "web_root": "/w",
        "web_origin": "https://web.example.test", "api_origin": "https://api.example.test",
        "auth_origin": None,
        "request": {"id": None, "chat_id": None, "generation_model": "m", "reasoning_effort": "high",
                    "output_language": "ja", "required_conclusion_text": ["x"], "required_conclusion_math": []},
        "timeout_seconds": 60, "max_age_seconds": 600}
    value.update(over)
    return value


def scenario(**over):
    value = {"schema_version": post.SCENARIO_SCHEMA, "scenario_id": "s1", "statement": SECRET_STATEMENT,
             "generation_model": "m", "reasoning_effort": "high", "output_language": "ja"}
    value.update(over)
    return value


class Base(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.root = Path(self._dir.name).resolve()
        self.state = self.root / "state"
        self.key = post.idempotency_key(CAND, "s1")

    def journal(self):
        return post.Journal(self.state, self.key)

    def run_once(self, fake, **kw):
        journal = self.journal()
        try:
            return post.run(fake, journal, self.key, scenario(), wait_seconds=kw.get("wait", 10),
                            sleep=lambda _: None, clock=kw.get("clock", lambda: 0.0))
        finally:
            journal.stream.close()


class Tests(Base):
    def test_key_depends_on_candidate_and_scenario_and_fits_api_pattern(self):
        a = post.idempotency_key(CAND, "s1")
        self.assertRegex(a, r"^[A-Za-z0-9_-]{32,128}$")
        self.assertNotEqual(a, post.idempotency_key("b" * 64, "s1"))
        self.assertNotEqual(a, post.idempotency_key(CAND, "s2"))
        self.assertEqual(a, post.idempotency_key(CAND, "s1"))

    def test_first_run_creates_exactly_one_request_and_returns_contract(self):
        fake = Fake()
        result = self.run_once(fake)
        self.assertEqual(set(result), {"id", "chat_id"})
        self.assertEqual(fake.calls.count("create_request"), 1)

    def test_rerun_observes_existing_without_second_create(self):
        fake = Fake()
        first = self.run_once(fake)
        second = self.run_once(fake)
        self.assertEqual(first, second)
        self.assertEqual(fake.calls.count("create_request"), 1)
        self.assertEqual(fake.calls.count("create_chat"), 1)

    def test_crash_after_server_create_replays_same_key_not_new_job(self):
        fake = Fake()
        fake.crash_after_create = True
        with self.assertRaises(ConnectionError):
            self.run_once(fake)
        result = self.run_once(fake)
        self.assertEqual(len(fake.requests), 1)  # one paid job server-side
        self.assertEqual(result["id"], fake.requests[self.key])

    def test_ambiguous_create_without_server_replay_is_refused(self):
        fake = Fake(replay_safe=False)
        fake.crash_after_create = True
        with self.assertRaises(ConnectionError):
            self.run_once(fake)
        with self.assertRaisesRegex(post.Refusal, "ambiguous_create_requires_manual_reconciliation"):
            self.run_once(fake)
        self.assertEqual(fake.calls.count("create_request"), 1)

    def test_bounded_wait_and_resumable_observation(self):
        fake = Fake(statuses=("accepted",))
        ticks = iter(range(0, 1000, 5))
        with self.assertRaisesRegex(post.Refusal, "request_observation_deadline_exceeded"):
            self.run_once(fake, wait=12, clock=lambda: next(ticks))
        fake.statuses = ["queued"]
        self.run_once(fake)  # resumes observation; no second create
        self.assertEqual(fake.calls.count("create_request"), 1)

    def test_failed_or_foreign_requests_are_refused(self):
        with self.assertRaisesRegex(post.Refusal, "request_not_live"):
            self.run_once(Fake(statuses=("failed",)))

    def test_journal_for_another_key_and_concurrent_runs_are_refused(self):
        self.run_once(Fake())
        with self.assertRaisesRegex(post.Refusal, "journal_belongs_to_another_request"):
            post.Journal(self.state, post.idempotency_key(CAND, "other"))
        held = self.journal()
        self.addCleanup(held.stream.close)
        with self.assertRaisesRegex(post.Refusal, "post_request_already_running"):
            self.journal()

    def test_journal_has_no_user_content(self):
        self.run_once(Fake())
        self.assertNotIn(SECRET_STATEMENT, (self.state / "post-request.jsonl").read_text())


class CliTests(Base):
    def files(self, **scen):
        c = private(self.root / "contract.json", contract())
        s = private(self.root / "scenario.json", scenario(**scen))
        return c, s

    def invoke(self, c, s, factory, cand=CAND):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = post.main(["--contract", str(c), "--candidate-sha256", cand, "--scenario", str(s),
                              "--session", str(self.root / "session"), "--state-dir", str(self.state)],
                             transport_factory=factory)
        return code, out.getvalue(), err.getvalue()

    def test_stdout_is_exactly_the_release_cycle_contract_and_leaks_nothing(self):
        c, s = self.files()
        fake = Fake()
        code, out, err = self.invoke(c, s, lambda **kw: fake)
        self.assertEqual(code, 0)
        value = json.loads(out)
        self.assertEqual(set(value), {"id", "chat_id"})
        self.assertEqual(out.strip(), json.dumps(value, sort_keys=True))
        self.assertNotIn(SECRET_STATEMENT, out + err)

    def test_without_live_adapter_it_refuses_and_creates_nothing(self):
        c, s = self.files()
        code, out, err = self.invoke(c, s, None)
        self.assertEqual((code, out), (2, ""))
        self.assertIn("live_transport_adapter_not_supplied", err)

    def test_candidate_mismatch_pre_release_contract_and_scenario_drift_refused(self):
        c, s = self.files()
        self.assertEqual(self.invoke(c, s, lambda **kw: Fake(), cand="b" * 64)[0], 2)
        pre = contract(phase="pre_release", target="staging")
        pre["request"].update(id=str(uuid4()), chat_id=str(uuid4()))
        bad = private(self.root / "bad.json", pre)
        code, _, err = self.invoke(bad, s, lambda **kw: Fake())
        self.assertEqual(code, 2)
        self.assertIn("production_post_deployment_contract_required", err)
        s2 = private(self.root / "s2.json", scenario(generation_model="other"))
        code, _, err = self.invoke(c, s2, lambda **kw: Fake())
        self.assertEqual(code, 2)
        self.assertIn("scenario_differs_from_contract", err)

    def test_contract_hash_pin_is_enforced(self):
        c, s = self.files()
        with self.assertRaisesRegex(post.Refusal, "contract_hash_changed"):
            post.load_inputs(c, "0" * 64, CAND, s)


if __name__ == "__main__":
    unittest.main()
