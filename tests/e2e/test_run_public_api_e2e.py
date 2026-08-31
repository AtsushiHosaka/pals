from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

_SCRIPT = Path(__file__).resolve().parent / "run_public_api_e2e.py"
_SPEC = importlib.util.spec_from_file_location("run_public_api_e2e", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
runner_module = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = runner_module
_SPEC.loader.exec_module(runner_module)


class FakeTransport:
    def __init__(self, scripted: list[tuple[str, str, int, dict[str, Any]]]) -> None:
        self.scripted = list(scripted)
        self.calls: list[dict[str, Any]] = []

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        json_body: Any | None,
        timeout_seconds: float,
    ) -> Any:
        path = urlsplit(url).path
        self.calls.append(
            {
                "method": method,
                "path": path,
                "headers": dict(headers),
                "json_body": json_body,
                "timeout_seconds": timeout_seconds,
            }
        )
        expected_method, expected_path, status, body = self.scripted.pop(0)
        if (method, path) != (expected_method, expected_path):
            raise AssertionError(
                f"expected {(expected_method, expected_path)}, got {(method, path)}"
            )
        return runner_module.HttpResponse(
            status=status,
            body=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        )


class FakeNotifier:
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def notify(self, *, job_id: str, chat_id: str, output_language: str) -> None:
        self.calls.append(
            {
                "job_id": job_id,
                "chat_id": chat_id,
                "output_language": output_language,
            }
        )


def _job(job_id: str, state: str, *, terminal: bool | None = None) -> dict[str, Any]:
    body = {
        "id": job_id,
        "job_id": job_id,
        "project_id": None,
        "chat_id": "11111111-1111-4111-8111-111111111111",
        "output_language": "ja",
        "theorem_statement": f"statement {job_id}",
        "state": state,
        "status": state,
        "stage": state,
        "sequence": 2,
        "diagnostics": [],
        "diagnostics_summary": None,
        "result_artifact_uri": None,
        "created_at": "2026-08-28T00:00:00+00:00",
        "updated_at": "2026-08-28T00:01:00+00:00",
    }
    if terminal is not None:
        body["is_terminal"] = terminal
    return body


class PublicApiE2ERunnerTest(unittest.TestCase):
    def test_public_flow_posts_all_jobs_before_polling_and_never_persists_token(self) -> None:
        token = "access-token-must-never-be-persisted"
        chat_id = "11111111-1111-4111-8111-111111111111"
        explanation = {
            "proof_job_id": "job-1",
            "state": "completed",
            "content": {
                "overview": "概要です。",
                "sections": [
                    {
                        "id": "s1",
                        "title": "内部見出し",
                        "summary": "証明の本文です。",
                        "references": [{"start_line": 1, "end_line": 1, "excerpt": "example"}],
                    }
                ],
                "conclusion": "以上で示されました。",
                "model": "fixed-model",
                "provider": "openai",
                "elapsed_ms": 1,
            },
            "created_at": "2026-08-28T00:00:00+00:00",
            "updated_at": "2026-08-28T00:01:00+00:00",
        }
        explanation_2 = json.loads(json.dumps(explanation))
        explanation_2["proof_job_id"] = "job-2"
        scripted = [
            ("GET", "/health", 200, {"status": "ok", "service": "pals-api", "environment": "local"}),
            ("POST", "/", 200, {"AuthenticationResult": {"AccessToken": token}}),
            ("GET", "/v1/auth/me", 200, {"user_id": "user", "email": None, "name": None, "groups": [], "token_use": "access"}),
            ("PUT", "/v1/auth/me/preferences", 200, {"output_language": "ja"}),
            ("POST", "/v1/chats", 201, {"id": chat_id, "project_id": None, "output_language": "ja", "created_at": "2026-08-28T00:00:00+00:00"}),
            ("POST", "/v1/proof-jobs", 201, _job("job-1", "queued")),
            ("POST", "/v1/proof-jobs", 201, _job("job-2", "queued")),
            ("GET", "/v1/proof-jobs/job-1/status", 200, _job("job-1", "verified", terminal=True)),
            ("GET", "/v1/proof-jobs/job-2/status", 200, _job("job-2", "verified", terminal=True)),
            ("GET", "/v1/proof-jobs/job-1", 200, _job("job-1", "verified")),
            ("GET", "/v1/proof-jobs/job-1/source", 200, {"job_id": "job-1", "project_id": None, "chat_id": chat_id, "lean_code": "example : True := by trivial"}),
            ("GET", "/v1/proof-jobs/job-1/explanation", 200, explanation),
            ("GET", "/v1/proof-jobs/job-2", 200, _job("job-2", "verified")),
            ("GET", "/v1/proof-jobs/job-2/source", 200, {"job_id": "job-2", "project_id": None, "chat_id": chat_id, "lean_code": "example : True := by trivial"}),
            ("GET", "/v1/proof-jobs/job-2/explanation", 200, explanation_2),
        ]
        transport = FakeTransport(scripted)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = root / "fixture.json"
            fixture.write_text(
                json.dumps(
                    {
                        "schema_version": "pals.local-e2e-fixture.v1",
                        "suite_id": "unit-suite",
                        "output_language": "ja",
                        "cases": [
                            {
                                "id": "one",
                                "field": "algebra",
                                "natural_language_statement": "問題一",
                                "formal_statement": "theorem one : True := by",
                                "expected_answer_summary": "真であることを示す。",
                                "grading_points": ["結論まで示す"],
                            },
                            {
                                "id": "two",
                                "field": "analysis",
                                "natural_language_statement": "問題二",
                                "formal_statement": "theorem two : True := by",
                                "expected_answer_summary": "仮定を使う。",
                                "grading_points": ["仮定を明示する"],
                            },
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            artifact_dir = root / "artifacts" / "run-1"
            config = runner_module.RunConfig(
                run_id="run-1",
                api_base_url="http://api.local",
                cognito_endpoint="http://cognito.local",
                cognito_client_id="client-id",
                cognito_username="existing@example.test",
                cognito_password="password-must-never-be-persisted",
                fixture_path=fixture,
                artifact_dir=artifact_dir,
                request_timeout_seconds=1,
                overall_timeout_seconds=1,
                poll_interval_seconds=0.001,
            )
            notifier = FakeNotifier()
            runner = runner_module.PublicApiE2ERunner(
                config,
                transport=transport,
                notifier=notifier,
            )
            self.assertTrue(runner.run())
            runner.finish()

            raw_text = (artifact_dir / "raw.json").read_text(encoding="utf-8")
            report_text = (artifact_dir / "report.md").read_text(encoding="utf-8")
            self.assertNotIn(token, raw_text)
            self.assertNotIn(token, report_text)
            self.assertNotIn(config.cognito_password, raw_text)
            self.assertNotIn(config.cognito_password, report_text)
            self.assertNotIn('"Authorization"', raw_text)
            self.assertIn("自然言語解答", report_text)
            self.assertIn("証明の本文です。", report_text)
            post_indices = [
                index
                for index, call in enumerate(transport.calls)
                if call["method"] == "POST" and call["path"] == "/v1/proof-jobs"
            ]
            first_poll = next(
                index
                for index, call in enumerate(transport.calls)
                if call["path"].endswith("/status")
            )
            self.assertEqual(len(post_indices), 2)
            self.assertLess(max(post_indices), first_poll)
            first_job_payload = transport.calls[post_indices[0]]["json_body"]
            self.assertNotIn("expected_answer_summary", first_job_payload)
            self.assertNotIn("grading_points", first_job_payload)
            self.assertNotIn("field", first_job_payload)
            cognito_call = transport.calls[1]
            self.assertEqual(
                cognito_call["headers"]["X-Amz-Target"],
                "AWSCognitoIdentityProviderService.InitiateAuth",
            )
            self.assertEqual(
                notifier.calls,
                [
                    {
                        "job_id": "job-1",
                        "chat_id": chat_id,
                        "output_language": "ja",
                    },
                    {
                        "job_id": "job-2",
                        "chat_id": chat_id,
                        "output_language": "ja",
                    },
                ],
            )
            self.assertEqual(transport.scripted, [])

    def test_loads_the_real_ten_case_fixture(self) -> None:
        fixture_path = Path(__file__).resolve().parent / "fixtures/university-math-v1.json"
        fixture = runner_module.load_fixture(fixture_path)
        self.assertEqual(fixture.schema_version, "pals.local-e2e-fixture.v1")
        self.assertEqual(fixture.suite_id, "university-math-v1")
        self.assertEqual(fixture.output_language, "ja")
        self.assertEqual(len(fixture.problems), 10)
        self.assertEqual(fixture.problems[0].field, "linear-algebra")
        self.assertTrue(fixture.problems[0].expected_answer_summary)
        self.assertGreaterEqual(len(fixture.problems[0].grading_points), 1)

    def test_rejects_a_cases_fixture_with_non_japanese_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture_path = Path(temporary) / "fixture.json"
            fixture_path.write_text(
                json.dumps(
                    {
                        "schema_version": "pals.local-e2e-fixture.v1",
                        "suite_id": "wrong-language",
                        "output_language": "en",
                        "cases": [],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(runner_module.E2EError, "output_language"):
                runner_module.load_fixture(fixture_path)

    def test_health_failure_is_fail_fast_before_authentication(self) -> None:
        transport = FakeTransport(
            [("GET", "/health", 503, {"detail": "not ready"})]
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = root / "fixture.json"
            fixture.write_text(
                json.dumps([{"id": "one", "statement": "問題"}]),
                encoding="utf-8",
            )
            config = runner_module.RunConfig(
                run_id="run-2",
                api_base_url="http://api.local",
                cognito_endpoint="http://cognito.local",
                cognito_client_id="client-id",
                cognito_username="existing@example.test",
                cognito_password="password",
                fixture_path=fixture,
                artifact_dir=root / "artifacts" / "run-2",
                request_timeout_seconds=1,
                overall_timeout_seconds=1,
                poll_interval_seconds=0.001,
            )
            runner = runner_module.PublicApiE2ERunner(config, transport=transport)
            with self.assertRaises(runner_module.E2EError):
                runner.run()
            self.assertEqual(len(transport.calls), 1)
            self.assertEqual(transport.scripted, [])


if __name__ == "__main__":
    unittest.main()
