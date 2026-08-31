#!/usr/bin/env python3
"""Run a reusable local proof E2E through the public PALS HTTP API."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

_TERMINAL_PROOF_STATES = frozenset({"verified", "failed", "canceled"})
_TERMINAL_EXPLANATION_STATES = frozenset({"completed", "failed"})
_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
_SCHEMA_VERSION = "pals.public-api-e2e-run.v1"


class E2EError(RuntimeError):
    """The real public-API run could not satisfy its contract."""


@dataclass(frozen=True, slots=True)
class HttpResponse:
    status: int
    body: bytes

    def json(self) -> Any:
        try:
            return json.loads(self.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise E2EError(f"HTTP {self.status} response was not UTF-8 JSON") from exc


class HttpTransport(Protocol):
    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        json_body: Any | None,
        timeout_seconds: float,
    ) -> HttpResponse: ...


class JobNotifier(Protocol):
    def notify(self, *, job_id: str, chat_id: str, output_language: str) -> None: ...


class SqsJobNotifier:
    """Wake the fixed local worker after durable state transitions."""

    def __init__(self, *, endpoint_url: str, queue_url: str, region: str) -> None:
        try:
            import boto3
        except ImportError as exc:
            raise E2EError("local SQS acceleration requires boto3") from exc
        self.client = boto3.client(
            "sqs",
            endpoint_url=endpoint_url,
            region_name=region,
            aws_access_key_id="test",
            aws_secret_access_key="test",
        )
        self.queue_url = queue_url

    def notify(self, *, job_id: str, chat_id: str, output_language: str) -> None:
        try:
            self.client.send_message(
                QueueUrl=self.queue_url,
                MessageBody=job_id,
                MessageAttributes={
                    "proof_job_id": {"DataType": "String", "StringValue": job_id},
                    "chat_id": {"DataType": "String", "StringValue": chat_id},
                    "output_language": {
                        "DataType": "String",
                        "StringValue": output_language,
                    },
                },
            )
        except Exception as exc:
            raise E2EError(f"local worker notification failed for {job_id}") from exc


class UrllibHttpTransport:
    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        json_body: Any | None,
        timeout_seconds: float,
    ) -> HttpResponse:
        body = None
        request_headers = dict(headers)
        if json_body is not None:
            body = json.dumps(
                json_body,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
            request_headers.setdefault("Content-Type", "application/json")
        request = Request(url, data=body, headers=request_headers, method=method)
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                return HttpResponse(status=response.status, body=response.read())
        except HTTPError as exc:
            return HttpResponse(status=exc.code, body=exc.read())
        except (TimeoutError, URLError, OSError) as exc:
            raise E2EError(f"HTTP transport failed for {method} {_safe_url(url)}") from exc


@dataclass(frozen=True, slots=True)
class FixtureProblem:
    fixture_id: str
    field: str | None
    statement: str
    formal_statement: str | None
    difficulty_hint: str | None
    target_style: str | None
    context: dict[str, Any]
    expected_answer_summary: str | None
    grading_points: tuple[str, ...]

    def request_payload(self, chat_id: str) -> dict[str, Any]:
        context = dict(self.context)
        existing_id = context.get("e2e_fixture_id")
        if existing_id is not None and existing_id != self.fixture_id:
            raise E2EError(f"fixture {self.fixture_id!r} has a conflicting e2e_fixture_id")
        context["e2e_fixture_id"] = self.fixture_id
        payload: dict[str, Any] = {
            "natural_language_statement": self.statement,
            "project_id": None,
            "chat_id": chat_id,
            "context": context,
        }
        if self.formal_statement is not None:
            payload["formal_statement"] = self.formal_statement
        if self.difficulty_hint is not None:
            payload["difficulty_hint"] = self.difficulty_hint
        if self.target_style is not None:
            payload["target_style"] = self.target_style
        return payload


@dataclass(frozen=True, slots=True)
class FixtureDocument:
    problems: list[FixtureProblem]
    sha256: str
    schema_version: str | None
    suite_id: str | None
    output_language: str


@dataclass(frozen=True, slots=True)
class RunConfig:
    run_id: str
    api_base_url: str
    cognito_endpoint: str
    cognito_client_id: str
    cognito_username: str
    cognito_password: str
    fixture_path: Path
    artifact_dir: Path
    request_timeout_seconds: float
    overall_timeout_seconds: float
    poll_interval_seconds: float


class PublicApiE2ERunner:
    def __init__(
        self,
        config: RunConfig,
        *,
        transport: HttpTransport,
        notifier: JobNotifier | None = None,
    ) -> None:
        self.config = config
        self.transport = transport
        self.notifier = notifier
        self.access_token: str | None = None
        self.started_at = _utc_now()
        self.raw: dict[str, Any] = {
            "schema_version": _SCHEMA_VERSION,
            "run_id": config.run_id,
            "started_at": self.started_at,
            "api_base_url": config.api_base_url,
            "fixture": {},
            "health": None,
            "chat": None,
            "jobs": [],
            "http_exchanges": [],
            "result": {"status": "running"},
        }

    def run(self) -> bool:
        fixture = load_fixture(self.config.fixture_path)
        problems = fixture.problems
        self.raw["fixture"] = {
            "path": str(self.config.fixture_path.resolve()),
            "sha256": fixture.sha256,
            "problem_count": len(problems),
            "schema_version": fixture.schema_version,
            "suite_id": fixture.suite_id,
            "output_language": fixture.output_language,
        }
        self.raw["health"] = self._health_check()
        self.access_token = self._authenticate()
        self._request_json("GET", "/v1/auth/me", expected_statuses={200})
        preferences = self._request_json(
            "PUT",
            "/v1/auth/me/preferences",
            json_body={"output_language": "ja"},
            expected_statuses={200},
        )[1]
        if not isinstance(preferences, dict) or preferences.get("output_language") != "ja":
            raise E2EError("account output_language did not become ja")
        chat = self._request_json("POST", "/v1/chats", expected_statuses={201})[1]
        chat_id = _required_string(chat, "id", "chat response")
        if chat.get("project_id") is not None or chat.get("output_language") != "ja":
            raise E2EError("new projectless chat did not snapshot output_language ja")
        self.raw["chat"] = chat

        jobs = self._create_all_jobs(problems, chat_id)
        self._wait_for_all_jobs(jobs)
        self._collect_outputs(jobs)
        passed = all(_job_passed(job) for job in jobs)
        self.raw["result"] = {
            "status": "passed" if passed else "failed",
            "verified_count": sum(job.get("terminal", {}).get("state") == "verified" for job in jobs),
            "problem_count": len(jobs),
        }
        return passed

    def resume(self, raw_path: Path) -> bool:
        """Re-authenticate and collect the current outputs of an interrupted run."""
        try:
            recovered = json.loads(raw_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise E2EError(f"resume artifact is not UTF-8 JSON: {raw_path}") from exc
        if not isinstance(recovered, dict) or not isinstance(recovered.get("jobs"), list):
            raise E2EError("resume artifact does not contain jobs")
        self.raw = recovered
        self.raw["recovered_from"] = str(raw_path.resolve())
        self.raw["run_id"] = self.config.run_id
        self.raw["started_at"] = self.started_at
        self.raw["finished_at"] = None
        self.raw["http_exchanges"] = []
        self.raw["result"] = {"status": "running"}
        self.raw["health"] = self._health_check()
        self.access_token = self._authenticate()
        self._request_json("GET", "/v1/auth/me", expected_statuses={200})
        jobs = self.raw["jobs"]
        for job in jobs:
            job_id = _required_string(job, "job_id", "resume job")
            _, status = self._request_json(
                "GET",
                f"/v1/proof-jobs/{job_id}/status",
                expected_statuses={200},
            )
            snapshot = {
                "sequence": status.get("sequence"),
                "state": status.get("state"),
                "updated_at": status.get("updated_at"),
            }
            history = job.setdefault("status_history", [])
            if not isinstance(history, list):
                raise E2EError(f"resume job {job_id} has invalid status history")
            if not history or history[-1] != snapshot:
                history.append(snapshot)
            if status.get("is_terminal") is True:
                job["terminal"] = status
            else:
                job.pop("terminal", None)
            if self.notifier is not None and status.get("state") == "verified":
                self.notifier.notify(
                    job_id=job_id,
                    chat_id=_required_string(status, "chat_id", "proof status"),
                    output_language="ja",
                )
        self._collect_outputs(jobs)
        passed = all(_job_passed(job) for job in jobs)
        self.raw["result"] = {
            "status": "passed" if passed else "failed",
            "verified_count": sum(
                job.get("terminal", {}).get("state") == "verified" for job in jobs
            ),
            "problem_count": len(jobs),
        }
        return passed

    def finish(self, *, failure: BaseException | None = None) -> None:
        self.access_token = None
        if failure is not None:
            self.raw["result"] = {
                "status": "failed",
                "error_type": type(failure).__name__,
                "error": str(failure),
            }
        self.raw["finished_at"] = _utc_now()
        _write_artifacts(self.config.artifact_dir, self.raw)

    def _health_check(self) -> dict[str, Any]:
        _, health = self._request_json("GET", "/health", expected_statuses={200}, authenticated=False)
        if not isinstance(health, dict) or health.get("status") != "ok":
            raise E2EError("PALS API health response was not ok")
        if health.get("environment") != "local":
            raise E2EError("public E2E runner requires PALS API environment=local")
        return health

    def _authenticate(self) -> str:
        payload = {
            "AuthFlow": "USER_PASSWORD_AUTH",
            "ClientId": self.config.cognito_client_id,
            "AuthParameters": {
                "USERNAME": self.config.cognito_username,
                "PASSWORD": self.config.cognito_password,
            },
        }
        response = self.transport.request(
            "POST",
            self.config.cognito_endpoint + "/",
            headers={
                "Content-Type": "application/x-amz-json-1.1",
                "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
            },
            json_body=payload,
            timeout_seconds=self.config.request_timeout_seconds,
        )
        if response.status != 200:
            raise E2EError(f"Cognito local authentication failed with HTTP {response.status}")
        body = response.json()
        if not isinstance(body, dict):
            raise E2EError("Cognito local authentication returned an invalid envelope")
        result = body.get("AuthenticationResult")
        if not isinstance(result, dict):
            raise E2EError("Cognito local authentication did not return tokens")
        token = result.get("AccessToken")
        if not isinstance(token, str) or not token.strip():
            raise E2EError("Cognito local authentication did not return an access token")
        return token

    def _create_all_jobs(
        self,
        problems: list[FixtureProblem],
        chat_id: str,
    ) -> list[dict[str, Any]]:
        jobs: list[dict[str, Any]] = []
        for problem in problems:
            payload = problem.request_payload(chat_id)
            _, created = self._request_json(
                "POST",
                "/v1/proof-jobs",
                json_body=payload,
                expected_statuses={201},
            )
            job_id = _required_string(created, "id", f"proof job {problem.fixture_id}")
            if created.get("chat_id") != chat_id or created.get("output_language") != "ja":
                raise E2EError(f"proof job {job_id} did not inherit the Japanese chat")
            jobs.append(
                {
                    "fixture_id": problem.fixture_id,
                    "field": problem.field,
                    "statement": problem.statement,
                    "expected_answer_summary": problem.expected_answer_summary,
                    "grading_points": list(problem.grading_points),
                    "job_id": job_id,
                    "created": created,
                    "status_history": [],
                }
            )
        self.raw["jobs"] = jobs
        return jobs

    def _wait_for_all_jobs(self, jobs: list[dict[str, Any]]) -> None:
        deadline = time.monotonic() + self.config.overall_timeout_seconds
        pending = {job["job_id"]: job for job in jobs}
        while pending:
            for job_id, job in tuple(pending.items()):
                _, status = self._request_json(
                    "GET",
                    f"/v1/proof-jobs/{job_id}/status",
                    expected_statuses={200},
                )
                if status.get("id") != job_id or status.get("output_language") != "ja":
                    raise E2EError(f"proof status identity mismatch for {job_id}")
                snapshot = {
                    "sequence": status.get("sequence"),
                    "state": status.get("state"),
                    "updated_at": status.get("updated_at"),
                }
                history = job["status_history"]
                if not history or history[-1] != snapshot:
                    history.append(snapshot)
                    state = status.get("state")
                    if self.notifier is not None and state in {
                        "compiling",
                        "semantic_review",
                        "verified",
                    }:
                        self.notifier.notify(
                            job_id=job_id,
                            chat_id=_required_string(status, "chat_id", "proof status"),
                            output_language="ja",
                        )
                if status.get("is_terminal") is True:
                    state = status.get("state")
                    if state not in _TERMINAL_PROOF_STATES:
                        raise E2EError(f"proof job {job_id} claimed an invalid terminal state")
                    job["terminal"] = status
                    pending.pop(job_id)
            if not pending:
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise E2EError(
                    "timed out waiting for proof jobs: " + ", ".join(sorted(pending))
                )
            time.sleep(min(self.config.poll_interval_seconds, remaining))

    def _collect_outputs(self, jobs: list[dict[str, Any]]) -> None:
        deadline = time.monotonic() + self.config.overall_timeout_seconds
        for job in jobs:
            job_id = job["job_id"]
            job["proof"] = self._request_json(
                "GET", f"/v1/proof-jobs/{job_id}", expected_statuses={200}
            )[1]
            source_status, source = self._request_json(
                "GET",
                f"/v1/proof-jobs/{job_id}/source",
                expected_statuses={200, 404},
            )
            job["source"] = {"http_status": source_status, "body": source}
            if job.get("terminal", {}).get("state") == "verified":
                job["explanation"] = self._wait_for_explanation(job_id, deadline)
            else:
                explanation_status, explanation = self._request_json(
                    "GET",
                    f"/v1/proof-jobs/{job_id}/explanation",
                    expected_statuses={200, 404},
                )
                job["explanation"] = {
                    "http_status": explanation_status,
                    "body": explanation,
                }

    def _wait_for_explanation(self, job_id: str, deadline: float) -> dict[str, Any]:
        while True:
            status, explanation = self._request_json(
                "GET",
                f"/v1/proof-jobs/{job_id}/explanation",
                expected_statuses={200, 404},
            )
            if status == 404:
                if time.monotonic() >= deadline:
                    return {"http_status": status, "body": explanation}
            elif explanation.get("state") in _TERMINAL_EXPLANATION_STATES:
                return {"http_status": status, "body": explanation}
            if time.monotonic() >= deadline:
                return {"http_status": status, "body": explanation}
            time.sleep(self.config.poll_interval_seconds)

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        json_body: Any | None = None,
        expected_statuses: set[int],
        authenticated: bool = True,
    ) -> tuple[int, Any]:
        headers = {"Accept": "application/json"}
        if authenticated:
            if self.access_token is None:
                raise E2EError("authenticated PALS request attempted before Cognito login")
            headers["Authorization"] = f"Bearer {self.access_token}"
        response = self.transport.request(
            method,
            self.config.api_base_url + path,
            headers=headers,
            json_body=json_body,
            timeout_seconds=self.config.request_timeout_seconds,
        )
        body = response.json()
        if authenticated and response.status == 401:
            self.access_token = self._authenticate()
            headers["Authorization"] = f"Bearer {self.access_token}"
            response = self.transport.request(
                method,
                self.config.api_base_url + path,
                headers=headers,
                json_body=json_body,
                timeout_seconds=self.config.request_timeout_seconds,
            )
            body = response.json()
        self.raw["http_exchanges"].append(
            {
                "at": _utc_now(),
                "method": method,
                "path": path,
                "request_json": json_body,
                "response_status": response.status,
                "response_json": body,
            }
        )
        if response.status not in expected_statuses:
            raise E2EError(f"{method} {path} returned unexpected HTTP {response.status}")
        if not isinstance(body, dict):
            raise E2EError(f"{method} {path} did not return a JSON object")
        return response.status, body


def load_fixture(path: Path) -> FixtureDocument:
    try:
        raw_bytes = path.read_bytes()
        document = json.loads(raw_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise E2EError(f"fixture could not be read as UTF-8 JSON: {path}") from exc
    schema_version: str | None = None
    suite_id: str | None = None
    output_language = "ja"
    strict_cases = False
    if isinstance(document, list):
        items = document
    elif isinstance(document, dict):
        if "cases" in document:
            strict_cases = True
            schema_version = document.get("schema_version")
            suite_id = document.get("suite_id")
            output_language = document.get("output_language")
            if schema_version != "pals.local-e2e-fixture.v1":
                raise E2EError("cases fixture requires schema_version pals.local-e2e-fixture.v1")
            if (
                not isinstance(suite_id, str)
                or not suite_id.strip()
                or len(suite_id) > 200
            ):
                raise E2EError("cases fixture requires a bounded nonblank suite_id")
            if output_language != "ja":
                raise E2EError("cases fixture output_language must be ja")
            items = document.get("cases")
        else:
            schema_value = document.get("schema_version")
            schema_version = schema_value if isinstance(schema_value, str) else None
            suite_value = document.get("suite_id")
            suite_id = suite_value if isinstance(suite_value, str) else None
            configured_language = document.get("output_language", "ja")
            if configured_language != "ja":
                raise E2EError("fixture output_language must be ja")
            items = document.get("problems", document.get("cards"))
    else:
        items = None
    if not isinstance(items, list) or not items:
        raise E2EError("fixture must contain a nonempty problems or cards array")
    if len(items) > 100:
        raise E2EError("fixture may contain at most 100 problems")
    problems: list[FixtureProblem] = []
    seen: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise E2EError(f"fixture item {index} must be an object")
        fixture_id = item.get("id")
        if not isinstance(fixture_id, str) or not fixture_id.strip() or len(fixture_id) > 200:
            raise E2EError(f"fixture item {index} has an invalid id")
        if fixture_id in seen:
            raise E2EError(f"fixture id is duplicated: {fixture_id}")
        seen.add(fixture_id)
        statement = next(
            (
                item.get(name)
                for name in (
                    "statement",
                    "canonical_statement",
                    "natural_language_statement",
                    "theorem_statement",
                )
                if isinstance(item.get(name), str) and item.get(name).strip()
            ),
            None,
        )
        if not isinstance(statement, str) or len(statement) > 20_000:
            raise E2EError(f"fixture {fixture_id!r} has no bounded statement")
        context = item.get("context", {})
        if not isinstance(context, dict):
            raise E2EError(f"fixture {fixture_id!r} context must be an object")
        problem = FixtureProblem(
            fixture_id=fixture_id,
            field=_optional_bounded_string(item, "field", 80),
            statement=statement,
            formal_statement=_optional_bounded_string(item, "formal_statement", 20_000),
            difficulty_hint=_optional_bounded_string(
                item, "difficulty_hint", 80, fallback_key="difficulty"
            ),
            target_style=_optional_bounded_string(item, "target_style", 80),
            context=context,
            expected_answer_summary=_optional_bounded_string(
                item, "expected_answer_summary", 2_000
            ),
            grading_points=_grading_points(item, fixture_id),
        )
        if strict_cases and (
            problem.field is None
            or problem.formal_statement is None
            or problem.expected_answer_summary is None
            or not problem.grading_points
        ):
            raise E2EError(
                f"case {fixture_id!r} requires field, formal_statement, "
                "expected_answer_summary, and grading_points"
            )
        problems.append(problem)
    return FixtureDocument(
        problems=problems,
        sha256=hashlib.sha256(raw_bytes).hexdigest(),
        schema_version=schema_version,
        suite_id=suite_id,
        output_language=output_language,
    )


def _grading_points(item: dict[str, Any], fixture_id: str) -> tuple[str, ...]:
    values = item.get("grading_points", [])
    if not isinstance(values, list) or len(values) > 20:
        raise E2EError(f"fixture {fixture_id!r} grading_points must be an array of at most 20")
    result: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value.strip() or len(value) > 500:
            raise E2EError(f"fixture {fixture_id!r} has an invalid grading point")
        result.append(value)
    return tuple(result)


def _optional_bounded_string(
    item: dict[str, Any],
    key: str,
    maximum: int,
    *,
    fallback_key: str | None = None,
) -> str | None:
    value = item.get(key)
    if value is None and fallback_key is not None:
        value = item.get(fallback_key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise E2EError(f"fixture field {key} must be a bounded nonblank string")
    return value


def _job_passed(job: dict[str, Any]) -> bool:
    source = job.get("source", {})
    explanation = job.get("explanation", {})
    explanation_body = explanation.get("body", {})
    return (
        job.get("terminal", {}).get("state") == "verified"
        and source.get("http_status") == 200
        and isinstance(source.get("body", {}).get("lean_code"), str)
        and explanation.get("http_status") == 200
        and explanation_body.get("state") == "completed"
        and isinstance(explanation_body.get("content"), dict)
    )


def _write_artifacts(directory: Path, raw: dict[str, Any]) -> None:
    directory.mkdir(parents=True, exist_ok=False, mode=0o700)
    raw_path = directory / "raw.json"
    report_path = directory / "report.md"
    raw_path.write_text(
        json.dumps(raw, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(_render_markdown(raw), encoding="utf-8")
    os.chmod(raw_path, 0o600)
    os.chmod(report_path, 0o600)


def _render_markdown(raw: dict[str, Any]) -> str:
    result = raw.get("result", {})
    lines = [
        "# PALS 公開API E2Eレポート",
        "",
        f"- run ID: `{raw.get('run_id', '')}`",
        f"- 結果: **{str(result.get('status', 'failed')).upper()}**",
        f"- 開始: `{raw.get('started_at', '')}`",
        f"- 終了: `{raw.get('finished_at', '')}`",
        f"- 問題数: {raw.get('fixture', {}).get('problem_count', 0)}",
        f"- 検証成功数: {result.get('verified_count', 0)}",
        "",
    ]
    if result.get("error"):
        lines.extend(["## 実行エラー", "", str(result["error"]), ""])
    for index, job in enumerate(raw.get("jobs", []), start=1):
        state = job.get("terminal", {}).get("state", "not_terminal")
        lines.extend(
            [
                f"## {index}. {job.get('fixture_id', '')}",
                "",
                str(job.get("statement", "")),
                "",
                f"- 分野: `{job.get('field') or 'unspecified'}`",
                f"- proof job: `{job.get('job_id', '')}`",
                f"- terminal state: `{state}`",
                "",
            ]
        )
        expected = job.get("expected_answer_summary")
        grading_points = job.get("grading_points", [])
        if isinstance(expected, str) or grading_points:
            lines.extend(["### 評価基準", ""])
            if isinstance(expected, str):
                lines.extend([f"期待される要点: {expected}", ""])
            if isinstance(grading_points, list):
                lines.extend(f"- {point}" for point in grading_points if isinstance(point, str))
                lines.append("")
        source_body = job.get("source", {}).get("body", {})
        lean_code = source_body.get("lean_code") if isinstance(source_body, dict) else None
        if isinstance(lean_code, str):
            lines.extend(["### Lean source", "", "```lean", lean_code, "```", ""])
        explanation_body = job.get("explanation", {}).get("body", {})
        content = explanation_body.get("content") if isinstance(explanation_body, dict) else None
        if isinstance(content, dict):
            paragraphs = [content.get("overview")]
            sections = content.get("sections", [])
            if isinstance(sections, list):
                paragraphs.extend(
                    section.get("summary")
                    for section in sections
                    if isinstance(section, dict)
                )
            paragraphs.append(content.get("conclusion"))
            text = "\n\n".join(value for value in paragraphs if isinstance(value, str))
            lines.extend(["### 自然言語解答", "", text, ""])
        else:
            diagnostics = job.get("proof", {}).get("diagnostics", [])
            lines.extend(
                [
                    "### 自然言語解答",
                    "",
                    "取得できませんでした。",
                    "",
                    "```json",
                    json.dumps(diagnostics, ensure_ascii=False, indent=2),
                    "```",
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"


def _required_string(value: Any, key: str, label: str) -> str:
    if not isinstance(value, dict):
        raise E2EError(f"{label} was not a JSON object")
    result = value.get(key)
    if not isinstance(result, str) or not result.strip():
        raise E2EError(f"{label} omitted {key}")
    return result


def _safe_url(url: str) -> str:
    parsed = urlsplit(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


def _canonical_origin(value: str, label: str) -> str:
    parsed = urlsplit(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise E2EError(f"{label} must be a canonical HTTP(S) origin")
    return f"{parsed.scheme}://{parsed.netloc}"


def _load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(name, value)


def _env(*names: str, default: str | None = None) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value is not None and value.strip():
            return value.strip()
    return default


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _default_run_id() -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{secrets.token_hex(4)}"


def _parse_args(argv: list[str]) -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--run-id", default=_default_run_id())
    parser.add_argument("--env-file", type=Path, default=repo_root / ".env.local")
    parser.add_argument("--api-base-url")
    parser.add_argument("--cognito-endpoint")
    parser.add_argument("--cognito-client-id")
    parser.add_argument("--cognito-username")
    parser.add_argument("--request-timeout-seconds", type=float, default=15.0)
    parser.add_argument("--overall-timeout-seconds", type=float, default=1800.0)
    parser.add_argument("--poll-interval-seconds", type=float, default=5.0)
    parser.add_argument("--sqs-endpoint-url")
    parser.add_argument("--sqs-queue-url")
    parser.add_argument("--aws-region", default="ap-northeast-1")
    parser.add_argument("--resume-raw", type=Path)
    return parser.parse_args(argv)


def _config(args: argparse.Namespace) -> RunConfig:
    _load_env_file(args.env_file)
    if _RUN_ID.fullmatch(args.run_id) is None:
        raise E2EError("run ID contains unsupported characters")
    for name in (
        "request_timeout_seconds",
        "overall_timeout_seconds",
        "poll_interval_seconds",
    ):
        value = getattr(args, name)
        if value <= 0 or value > 86_400:
            raise E2EError(f"{name} must be in (0, 86400]")
    api_base_url = args.api_base_url or _env(
        "PALS_API_BASE_URL", "PALS_AGENT_API_BASE_URL", default="http://127.0.0.1:8000"
    )
    cognito_endpoint = args.cognito_endpoint or _env(
        "PALS_COGNITO_ENDPOINT_URL",
        "NEXT_PUBLIC_COGNITO_ENDPOINT",
        default="http://127.0.0.1:9229",
    )
    client_id = args.cognito_client_id or _env(
        "PALS_COGNITO_APP_CLIENT_ID", "NEXT_PUBLIC_COGNITO_CLIENT_ID"
    )
    username = args.cognito_username or _env("PALS_LOCAL_COGNITO_EMAIL")
    password = _env("PALS_LOCAL_COGNITO_PASSWORD")
    if not client_id or not username or not password:
        raise E2EError("Cognito client ID, existing username, and password are required")
    assert api_base_url is not None and cognito_endpoint is not None
    artifact_root = Path(__file__).resolve().parents[2] / ".local/e2e-runs"
    return RunConfig(
        run_id=args.run_id,
        api_base_url=_canonical_origin(api_base_url, "API base URL"),
        cognito_endpoint=_canonical_origin(cognito_endpoint, "Cognito endpoint"),
        cognito_client_id=client_id,
        cognito_username=username,
        cognito_password=password,
        fixture_path=args.fixture.resolve(),
        artifact_dir=artifact_root / args.run_id,
        request_timeout_seconds=args.request_timeout_seconds,
        overall_timeout_seconds=args.overall_timeout_seconds,
        poll_interval_seconds=args.poll_interval_seconds,
    )


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        config = _config(args)
    except E2EError as exc:
        print(f"configuration failed: {exc}", file=sys.stderr)
        return 2
    notifier: JobNotifier | None = None
    if args.sqs_endpoint_url or args.sqs_queue_url:
        if not args.sqs_endpoint_url or not args.sqs_queue_url:
            print("configuration failed: local SQS options must be supplied together", file=sys.stderr)
            return 2
        try:
            notifier = SqsJobNotifier(
                endpoint_url=_canonical_origin(args.sqs_endpoint_url, "SQS endpoint URL"),
                queue_url=args.sqs_queue_url,
                region=args.aws_region,
            )
        except E2EError as exc:
            print(f"configuration failed: {exc}", file=sys.stderr)
            return 2
    runner = PublicApiE2ERunner(
        config,
        transport=UrllibHttpTransport(),
        notifier=notifier,
    )
    failure: BaseException | None = None
    passed = False
    try:
        passed = (
            runner.resume(args.resume_raw.resolve())
            if args.resume_raw is not None
            else runner.run()
        )
    except (E2EError, ValueError) as exc:
        failure = exc
    try:
        runner.finish(failure=failure)
    except OSError as exc:
        print(f"artifact write failed: {exc}", file=sys.stderr)
        return 2
    status = "passed" if passed and failure is None else "failed"
    print(json.dumps({"artifact_dir": str(config.artifact_dir), "status": status}))
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
