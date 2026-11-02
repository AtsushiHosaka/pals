#!/usr/bin/env python3
"""Submit questions through the public API and time them as the web client sees them.

Polls GET /v1/proof-requests/{id} every 1.5 seconds like hooks/useProofRequests.ts and
prints one metadata-only JSON line per question, which pals_agent.latency_report reads
alongside the service logs. Statements and answers are never printed.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

POLL_SECONDS = 1.5
TERMINAL = {"answered", "needs_input", "failed"}


def request_json(
    method: str, url: str, *, body: Any = None, headers: dict[str, str] | None = None,
) -> tuple[int, Any]:
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(
        url, data=data, method=method,
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, json.loads(response.read() or b"null")
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read() or b"null")


def load_env(path: Path) -> dict[str, str]:
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        name, separator, value = line.partition("=")
        if separator and not name.startswith("#"):
            values[name.strip()] = value.strip().strip("'\"")
    return values


def sign_in(endpoint: str, env: dict[str, str]) -> str:
    status, payload = request_json(
        "POST", endpoint + "/",
        headers={
            "Content-Type": "application/x-amz-json-1.1",
            "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
        },
        body={
            "AuthFlow": "USER_PASSWORD_AUTH",
            "ClientId": env["PALS_COGNITO_APP_CLIENT_ID"],
            "AuthParameters": {
                "USERNAME": env["PALS_LOCAL_COGNITO_EMAIL"],
                "PASSWORD": env["PALS_LOCAL_COGNITO_PASSWORD"],
            },
        },
    )
    if status != 200:
        raise SystemExit(f"sign-in failed with HTTP {status}")
    return payload["AuthenticationResult"]["AccessToken"]


def probe(
    api: str, token: str, statement: str, model: str, effort: str, limit: float,
    quote_tokens: int | None,
) -> dict:
    auth = {"Authorization": f"Bearer {token}"}
    status, chat = request_json("POST", api + "/v1/chats", headers=auth)
    if status != 201:
        return {"event": "client_answer_timing", "stage": "chat", "http_status": status}
    body: dict[str, Any] = {
        "statement": statement,
        "generation_model": model,
        "generation_reasoning_effort": effort,
        "idempotency_key": secrets.token_urlsafe(32),
    }
    if quote_tokens is not None:
        status, quote = request_json(
            "POST", api + "/v1/billing/token-quotes", headers=auth,
            body={"action": "create", "chat_id": chat["id"], "request": body,
                  "max_utilization_tokens": quote_tokens},
        )
        if status not in {200, 201}:
            return {"event": "client_answer_timing", "stage": "quote", "http_status": status,
                    "error_code": quote.get("error", {}).get("code")}
        body["quote_id"] = quote["quote_id"]
    started = time.monotonic()
    status, created = request_json(
        "POST", f"{api}/v1/chats/{chat['id']}/proof-requests", headers=auth, body=body,
    )
    post_ms = (time.monotonic() - started) * 1000
    if status != 201:
        code = created.get("error", {}).get("code") if isinstance(created, dict) else None
        return {"event": "client_answer_timing", "stage": "create", "http_status": status,
                "error_code": code}
    polls = 0
    current = created
    seen: dict[str, float] = {created["status"]: 0.0}
    while current["status"] not in TERMINAL and time.monotonic() - started < limit:
        time.sleep(POLL_SECONDS)
        polls += 1
        status, payload = request_json(
            "GET", f"{api}/v1/proof-requests/{created['id']}", headers=auth,
        )
        if status == 200:
            current = payload
            seen.setdefault(current["status"], (time.monotonic() - started) * 1000)
    return {
        "event": "client_answer_timing",
        "status": current["status"],
        "error_code": current.get("error_code"),
        "post_ms": round(post_ms, 1),
        "total_ms": round((time.monotonic() - started) * 1000, 1),
        "polls": polls,
        "first_seen_ms": {name: round(value, 1) for name, value in seen.items()},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("statements", type=Path, help="file with one question per line")
    parser.add_argument("--env-file", type=Path, default=Path(".env.local"))
    parser.add_argument("--api-base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--cognito-endpoint", default="http://127.0.0.1:9229")
    parser.add_argument("--model", default="gpt-6.1-terra")
    parser.add_argument("--effort", default="medium")
    parser.add_argument("--limit-seconds", type=float, default=900.0)
    parser.add_argument(
        "--quote-tokens", type=int, help="take a token quote first, for a metered paid account",
    )
    args = parser.parse_args()
    env = {**load_env(args.env_file), **os.environ}
    token = sign_in(args.cognito_endpoint, env)
    for line in args.statements.read_text(encoding="utf-8").splitlines():
        if line.strip():
            result = probe(
                args.api_base_url, token, line.strip(), args.model, args.effort, args.limit_seconds,
                args.quote_tokens,
            )
            print(json.dumps(result, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
