import contextlib
import importlib.util
import io
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "loadtest-run.py"
PROBLEMS = Path(__file__).resolve().parents[1] / "loadtest-problems.v1.json"
spec = importlib.util.spec_from_file_location("loadtest_run", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

STATEMENTS = {p["statement"]: p for p in json.loads(PROBLEMS.read_text())["problems"]}


class FakeApi:
    """The slice of the production API the driver uses, answering after a few polls."""

    def __init__(self, behaviour=None, expires_in=900, bad_password_for=None):
        self.lock = threading.Lock()
        self.behaviour = behaviour or (lambda problem: ("answered", "lean_catalog" if problem["class"] == "B" else "lean_verified", None))
        self.expires_in, self.bad = expires_in, bad_password_for
        self.requests, self.posted, self.refreshes, self.logins = {}, 0, 0, 0
        self.chat_n = 0
        self.problem_text_seen = []

    def __call__(self, method, url, headers=None, body=None, timeout=30.0):
        with self.lock:
            return self.handle(method, url, headers or {}, body)

    def handle(self, method, url, headers, body):
        if url.endswith("/health"):
            return 200, {"status": "ok"}
        if "cognito-idp" in url:
            flow = body["AuthFlow"]
            if flow == "USER_PASSWORD_AUTH":
                if body["AuthParameters"]["USERNAME"] == self.bad:
                    return 400, {"__type": "NotAuthorizedException"}
                self.logins += 1
            else:
                self.refreshes += 1
            return 200, {"AuthenticationResult": {"AccessToken": "access-token-value", "RefreshToken": "refresh-token-value",
                                                  "ExpiresIn": self.expires_in}}
        if "Authorization" not in headers:
            return 401, {"code": "auth_token_missing"}
        if method == "PUT" and url.endswith("/v1/auth/me/preferences"):
            self.language = body["output_language"]
            return 200, {"output_language": body["output_language"]}
        if method == "POST" and url.endswith("/v1/chats"):
            self.chat_n += 1
            return 201, {"id": f"chat-{self.chat_n}"}
        if method == "POST" and url.endswith("/proof-requests"):
            self.posted += 1
            problem = STATEMENTS[body["statement"]]
            self.problem_text_seen.append(body["statement"])
            rid = f"req-{self.posted}"
            self.requests[rid] = {"polls": 0, "problem": problem}
            return 201, {"id": rid, "status": "queued"}
        if method == "GET" and "/proof-requests/" in url:
            entry = self.requests[url.rsplit("/", 1)[1]]
            entry["polls"] += 1
            outcome, kind, code = self.behaviour(entry["problem"])
            if entry["polls"] < 2:
                return 200, {"status": "queued"}
            if entry["polls"] < 4:
                return 200, {"status": "assessing"}
            answer = {"evidence_kind": kind, "text": "SECRET ANSWER TEXT"} if outcome == "answered" else None
            return 200, {"status": outcome, "error_code": code, "answer": answer}
        raise AssertionError((method, url))


class RunTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state = Path(self.tmp.name) / "state"
        self.state.mkdir(mode=0o700)
        accounts = [{"email": f"u{i}@example.com", "sub": f"sub-{i}", "password": f"pw-secret-{i}"} for i in range(3)]
        manifest = self.state / "manifest.json"
        manifest.write_text(json.dumps({"run_id": "t", "pool_id": "pool", "accounts": accounts}))
        os.chmod(manifest, 0o600)
        doc = json.loads(PROBLEMS.read_text())
        doc["status"] = "approved by the owner"
        self.approved = Path(self.tmp.name) / "problems.json"
        self.approved.write_text(json.dumps(doc))

    def run_main(self, argv, api):
        out, err = io.StringIO(), io.StringIO()
        base = ["--state-dir", str(self.state), "--users", "3", "--think-min", "0", "--think-max", "0",
                "--poll", "0.001", "--timeout", "10"]
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = module.main(base + argv, http=api, client_id="client-1")
        return code, out.getvalue(), err.getvalue()

    def test_plan_only_submits_nothing_and_reports_the_cost(self):
        api = FakeApi()
        code, out, _ = self.run_main(["--problems", str(self.approved)], api)
        self.assertEqual(code, 0)
        self.assertIn("PLAN ONLY", out)
        self.assertIn("typically", out)
        self.assertEqual(api.posted, 0)
        self.assertEqual(api.logins, 0)

    def test_execute_needs_an_approved_amount_and_an_approved_problem_list(self):
        api = FakeApi()
        code, _, err = self.run_main(["--problems", str(self.approved), "--execute"], api)
        self.assertEqual(code, 2)
        self.assertIn("--approve-max-usd", err)
        doc = json.loads(PROBLEMS.read_text())
        doc["status"] = "draft: not yet approved"
        drafted = Path(self.tmp.name) / "draft.json"
        drafted.write_text(json.dumps(doc))
        code, _, err = self.run_main(["--problems", str(drafted), "--execute", "--approve-max-usd", "5"], api)
        self.assertEqual(code, 2)
        self.assertIn("draft", err)
        self.assertEqual(api.posted, 0)

    def test_full_run_records_every_request_and_leaks_nothing_sensitive(self):
        api = FakeApi()
        code, out, err = self.run_main(["--problems", str(self.approved), "--execute", "--approve-max-usd", "5"], api)
        self.assertEqual(code, 0, err)
        runs = list((self.state / "runs").iterdir())
        self.assertEqual(len(runs), 1)
        rows = [json.loads(line) for line in (runs[0] / "results.jsonl").read_text().splitlines()]
        self.assertEqual(len(rows), 9)  # 3 users x (A, B, C)
        self.assertEqual({r["class"] for r in rows}, {"A", "B", "C"})
        self.assertTrue(all(r["status"] == "answered" for r in rows))
        self.assertTrue(all("seconds_to_progress" in r and "seconds_to_terminal" in r for r in rows))
        summary = json.loads((runs[0] / "summary.json").read_text())
        self.assertEqual(summary["classes"]["B"]["evidence_kinds"], {"lean_catalog": 3})
        self.assertEqual(summary["classes"]["A"]["answered"], 3)
        blob = out + err + "".join(p.read_text() for p in runs[0].iterdir())
        for secret in ("pw-secret-", "access-token-value", "refresh-token-value", "SECRET ANSWER TEXT",
                       *STATEMENTS.keys()):
            self.assertNotIn(secret, blob)
        self.assertEqual(oct(runs[0].stat().st_mode & 0o777), "0o700")

    def test_the_account_language_is_set_to_japanese_before_the_chat_is_created(self):
        api = FakeApi()
        self.run_main(["--problems", str(self.approved), "--execute", "--approve-max-usd", "5"], api)
        self.assertEqual(api.language, "ja")

    def test_each_user_gets_a_different_problem_of_each_class(self):
        api = FakeApi()
        self.run_main(["--problems", str(self.approved), "--execute", "--approve-max-usd", "5"], api)
        self.assertEqual(len(set(api.problem_text_seen)), 9)

    def test_failures_are_counted_and_stop_new_submissions(self):
        api = FakeApi(behaviour=lambda problem: ("failed", None, "pals.generation_failed"))
        code, _, err = self.run_main(["--problems", str(self.approved), "--execute", "--approve-max-usd", "5",
                                      "--stop-after-failures", "2"], api)
        self.assertEqual(code, 0, err)
        self.assertLess(api.posted, 9)  # the switch stopped later submissions
        run = next((self.state / "runs").iterdir())
        summary = json.loads((run / "summary.json").read_text())
        failed = sum(c["failed"] for c in summary["classes"].values())
        self.assertGreaterEqual(failed, 2)
        self.assertIn("pals.generation_failed", json.dumps(summary))

    def test_needs_input_is_recorded_separately(self):
        api = FakeApi(behaviour=lambda problem: ("needs_input", None, None) if problem["class"] == "C"
                      else ("answered", "lean_verified", None))
        self.run_main(["--problems", str(self.approved), "--execute", "--approve-max-usd", "5"], api)
        summary = json.loads((next((self.state / "runs").iterdir()) / "summary.json").read_text())
        self.assertEqual(summary["classes"]["C"]["needs_input"], 3)
        self.assertEqual(summary["classes"]["C"]["answered"], 0)

    def test_expiring_tokens_are_refreshed_without_failing(self):
        api = FakeApi(expires_in=30)  # inside the 90 s refresh margin: refresh on every call
        code, _, err = self.run_main(["--problems", str(self.approved), "--execute", "--approve-max-usd", "5"], api)
        self.assertEqual(code, 0, err)
        self.assertGreater(api.refreshes, 0)
        run = next((self.state / "runs").iterdir())
        rows = [json.loads(line) for line in (run / "results.jsonl").read_text().splitlines()]
        self.assertTrue(all(r["status"] == "answered" for r in rows))

    def test_a_user_who_cannot_sign_in_is_reported_and_does_not_hang_the_others(self):
        api = FakeApi(bad_password_for="u1@example.com")
        code, _, err = self.run_main(["--problems", str(self.approved), "--execute", "--approve-max-usd", "5"], api)
        self.assertEqual(code, 0, err)
        run = next((self.state / "runs").iterdir())
        rows = [json.loads(line) for line in (run / "results.jsonl").read_text().splitlines()]
        self.assertEqual(sum(r["status"] == "setup_failed" for r in rows), 1)
        self.assertEqual(sum(r["status"] == "answered" for r in rows), 6)

    def test_refuses_when_the_api_health_check_fails(self):
        def down(method, url, headers=None, body=None, timeout=30.0):
            return 503, None
        code, _, err = self.run_main(["--problems", str(self.approved)], down)
        self.assertEqual(code, 2)
        self.assertIn("/health", err)

    def test_manifest_must_be_private(self):
        os.chmod(self.state / "manifest.json", 0o644)
        code, _, err = self.run_main(["--problems", str(self.approved)], FakeApi())
        self.assertEqual(code, 2)
        self.assertIn("0600", err)

    def test_percentile_is_nearest_rank(self):
        values = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
        self.assertEqual(module.percentile(values, 0.5), 50.0)
        self.assertEqual(module.percentile(values, 0.9), 90.0)
        self.assertIsNone(module.percentile([], 0.9))

    def test_the_shipped_problem_list_has_ten_per_class_and_no_square_expansion(self):
        doc = json.loads(PROBLEMS.read_text())
        self.assertTrue(doc["status"])
        for cls in "ABC":
            self.assertEqual(sum(p["class"] == cls for p in doc["problems"]), 10)
        for problem in doc["problems"]:
            self.assertNotIn("(x + y)^2", problem["statement"])
            self.assertNotIn("(x+y)^2", problem["statement"])
        self.assertEqual(len({p["id"] for p in doc["problems"]}), 30)


if __name__ == "__main__":
    unittest.main()
