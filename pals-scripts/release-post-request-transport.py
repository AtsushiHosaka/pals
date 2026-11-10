#!/usr/bin/env python3
"""Live transport for release-post-request.py: one request, as the approved session account.

The credential never enters this process. `release-post-request-browser.cjs` seeds a browser
context from the private session file (the same seeding the acceptance observer uses), takes
the bearer the product itself sends to the API, and performs a closed list of HTTPS calls
against the contract's API origin. This module owns the policy around those calls:

* every response it relies on must carry the candidate's release manifest digest;
* the create is sent at most once per process, and only after the dedicated chat was
  observed to be empty; an existing request is adopted instead of created;
* a 4xx create reply is a definitive rejection (nothing was created); a lost reply, 5xx,
  3xx or timeout is unresolved and is settled by observing the chat, never by resubmitting;
* refusals are fixed codes, an HTTP status and at most the server's bounded error code.
  Statements, tokens, session contents and response text are never logged or raised.
"""
from __future__ import annotations

import json
import os
import queue
import re
import signal
import stat
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit

UUID4 = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\Z")
KEY = re.compile(r"[A-Za-z0-9_-]{32,128}\Z")
CODE = re.compile(r"[a-z0-9_]{1,64}\Z")
STATUSES = {"queued", "assessing", "needs_input", "verifying", "answered", "failed"}
# A 4xx that does not prove the server refused the command before creating anything.
AMBIGUOUS_4XX = {408, 421, 425, 499}
# Inherited settings that could weaken TLS verification or reroute the helper's traffic.
BLOCKED_ENVIRONMENT = {"NODE_OPTIONS", "NODE_EXTRA_CA_CERTS", "NODE_TLS_REJECT_UNAUTHORIZED",
                       "NODE_USE_ENV_PROXY", "SSL_CERT_FILE", "SSL_CERT_DIR", "HTTP_PROXY",
                       "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY"}


class _Lost(Exception):
    """No usable reply: the outcome of the call is unknown."""


class LiveTransport:
    replay_safe = True  # the API replays a create for the same owner, key and body

    def __init__(self, *, api_origin: str, session: Path, contract: dict[str, Any],
                 refusal: type[Exception], helper: Path, extra_ca: Path | None = None,
                 call_seconds: float = 30.0, start_seconds: float = 90.0,
                 settle_seconds: tuple[float, ...] = (1.0, 2.0, 4.0),
                 sleep: Callable[[float], None] = time.sleep):
        self._refusal = refusal
        self._need(api_origin == contract["api_origin"], "api_origin_differs_from_contract")
        for name in ("api_origin", "web_origin"):
            url = urlsplit(contract[name])
            self._need(url.scheme == "https" and url.hostname and url.username is None
                       and url.password is None and url.path == "" and not url.query
                       and not url.fragment, f"https_{name}_required")
        self._need(contract["phase"] == "post_deployment" and contract["target"] == "production",
                   "production_post_deployment_contract_required")
        self._manifest = contract["manifest"]["sha256"]
        self._session = self._private_session(Path(session))
        self._init = {"api_origin": contract["api_origin"], "web_origin": contract["web_origin"],
                      "auth_origin": contract["auth_origin"], "web_root": contract["web_root"],
                      "session_path": str(self._session), "start_ms": int(start_seconds * 1000),
                      "call_ms": int(call_seconds * 1000)}
        self._helper, self._extra_ca = Path(helper), extra_ca
        self._call_seconds, self._start_seconds = call_seconds, start_seconds
        self._settle, self._sleep = settle_seconds, sleep
        self._process: subprocess.Popen[bytes] | None = None
        self._replies: queue.Queue[bytes | None] = queue.Queue()
        self._sequence = 0
        self._submitted = False

    # -- refusals ---------------------------------------------------------------------

    def _need(self, value: Any, code: str) -> None:
        if not value:
            raise self._refusal(code)

    def _private_session(self, path: Path) -> Path:
        """Check the session file's metadata only; its contents are read by the helper alone."""
        try:
            ok = path.is_absolute() and path.resolve(strict=True) == path
            if ok:
                fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                try:
                    info = os.fstat(fd)
                finally:
                    os.close(fd)
                ok = (stat.S_ISREG(info.st_mode) and info.st_uid == os.geteuid()
                      and stat.S_IMODE(info.st_mode) == 0o600 and info.st_nlink == 1
                      and 0 < info.st_size <= 2**20)
        except OSError:
            ok = False
        self._need(ok, "private_session_required")
        return path

    # -- helper process ---------------------------------------------------------------

    def _start(self) -> None:
        environment = {name: value for name, value in os.environ.items()
                       if name.upper() not in BLOCKED_ENVIRONMENT}
        if self._extra_ca is not None:  # tests only: trust anchor of a loopback server
            environment["NODE_EXTRA_CA_CERTS"] = str(self._extra_ca)
        try:
            self._process = subprocess.Popen(
                ["node", str(self._helper)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, env=environment, start_new_session=True)
        except OSError:
            raise self._refusal("live_session_helper_unavailable") from None
        threading.Thread(target=self._pump, args=(self._process.stdout, self._replies), daemon=True).start()
        try:
            ready = self._exchange(self._init, self._start_seconds + 15)
        except _Lost:
            raise self._refusal("live_session_helper_unavailable") from None
        if ready.get("ready") is not True:
            self.close()
            code = ready.get("code")
            raise self._refusal(code if isinstance(code, str) and CODE.fullmatch(code)
                                else "live_session_helper_unavailable")

    @staticmethod
    def _pump(stream: Any, replies: "queue.Queue[bytes | None]") -> None:
        try:
            for line in stream:
                replies.put(line)
        except (OSError, ValueError):
            pass
        replies.put(None)

    def _exchange(self, message: dict[str, Any], seconds: float) -> dict[str, Any]:
        process = self._process
        try:
            assert process is not None and process.stdin is not None
            process.stdin.write(json.dumps(message, ensure_ascii=False).encode() + b"\n")
            process.stdin.flush()
            line = self._replies.get(timeout=seconds)
            reply = json.loads(line) if line and len(line) <= 2**21 else None
        except (OSError, ValueError, queue.Empty, AssertionError):
            reply = None
        if not isinstance(reply, dict):
            self.close()  # the protocol is out of step; never reuse this helper
            raise _Lost
        return reply

    def close(self) -> None:
        process, self._process = self._process, None
        if process is None:
            return
        for sig in (signal.SIGTERM, signal.SIGKILL):
            if process.poll() is not None:
                break
            try:
                os.killpg(process.pid, sig)
                process.wait(timeout=5)
            except (OSError, subprocess.TimeoutExpired):
                continue
        for stream in (process.stdin, process.stdout):
            try:
                if stream is not None:
                    stream.close()
            except OSError:
                pass

    def _wire(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        """One allow-listed HTTPS call. Returns {"status", "release", "body"} or raises _Lost."""
        if self._process is None:
            self._start()
        self._sequence += 1
        message: dict[str, Any] = {"id": self._sequence, "method": method, "path": path}
        if body is not None:
            message["body"] = body
        reply = self._exchange(message, self._call_seconds + 15)
        if reply.get("id") != self._sequence:
            self.close()
            raise _Lost
        if reply.get("ok") is not True:
            self._need(reply.get("error") != "route_not_allowed", "route_not_allowed")
            raise _Lost
        self._need(type(reply.get("status")) is int, "live_session_helper_unavailable")
        return reply

    # -- response policy --------------------------------------------------------------

    def _bound(self, reply: dict[str, Any]) -> None:
        self._need(reply.get("release") == self._manifest, "public_api_not_candidate")

    def _read(self, path: str, failure: str) -> dict[str, Any]:
        """A GET that must succeed, as the session account, on the candidate."""
        try:
            reply = self._wire("GET", path)
        except _Lost:
            raise self._refusal(failure + "_unresolved") from None
        self._need(reply["status"] not in {401, 403}, "session_not_authorized")
        self._need(reply["status"] == 200, f"{failure}_failed_http_{reply['status']}")
        self._bound(reply)
        self._need(isinstance(reply.get("body"), dict), f"{failure}_response_invalid")
        return reply["body"]

    def _uuid(self, value: Any, code: str) -> str:
        self._need(isinstance(value, str) and UUID4.fullmatch(value), code)
        return value

    def _existing(self, chat_id: str, statement: str) -> str | None:
        """The request already in this run's dedicated chat, if any. Anything else is foreign."""
        items = self._read(f"/v1/chats/{chat_id}/proof-requests", "observe_chat").get("items")
        self._need(isinstance(items, list), "observe_chat_response_invalid")
        if not items:
            return None
        only = items[0]
        self._need(len(items) == 1 and isinstance(only, dict) and only.get("chat_id") == chat_id
                   and only.get("statement") == statement, "chat_contains_unexpected_requests")
        return self._uuid(only.get("id"), "observe_chat_response_invalid")

    # -- Transport surface ------------------------------------------------------------

    def create_chat(self) -> str:
        try:
            reply = self._wire("POST", "/v1/chats")
        except _Lost:
            raise self._refusal("create_chat_unresolved") from None
        self._need(reply["status"] not in {401, 403}, "session_not_authorized")
        self._need(reply["status"] == 201, f"create_chat_failed_http_{reply['status']}")
        self._bound(reply)
        body = reply.get("body")
        return self._uuid(body.get("id") if isinstance(body, dict) else None, "create_chat_response_invalid")

    def create_request(self, chat_id: str, key: str, scenario: dict[str, Any]) -> str:
        self._uuid(chat_id, "canonical_uuid_required")
        self._need(isinstance(key, str) and KEY.fullmatch(key), "idempotency_key_invalid")
        statement = scenario["statement"]
        # Free reads first: they prove the account, the chat and the candidate before any charge.
        owned = self._read(f"/v1/chats/{chat_id}", "preflight")
        self._need(owned.get("id") == chat_id, "preflight_response_invalid")
        found = self._existing(chat_id, statement)
        if found is not None:
            return found
        self._need(not self._submitted, "create_already_attempted")
        self._submitted = True
        body = {"statement": statement, "idempotency_key": key,
                "generation_model": scenario["generation_model"]}
        if scenario["reasoning_effort"] is not None:
            body["generation_reasoning_effort"] = scenario["reasoning_effort"]
        try:
            reply = self._wire("POST", f"/v1/chats/{chat_id}/proof-requests", body)
        except _Lost:
            reply = None
        if reply is not None:
            status, payload = reply["status"], reply.get("body")
            if status in {200, 201}:
                self._bound(reply)
                if (isinstance(payload, dict) and payload.get("chat_id") == chat_id
                        and isinstance(payload.get("id"), str) and UUID4.fullmatch(payload["id"])):
                    return payload["id"]
            elif 400 <= status < 500 and status not in AMBIGUOUS_4XX:
                error = payload.get("error") if isinstance(payload, dict) else None
                code = error.get("code") if isinstance(error, dict) else None
                suffix = ":" + code if isinstance(code, str) and CODE.fullmatch(code) else ""
                raise self._refusal(f"create_rejected_http_{status}{suffix}")
        # Unresolved: the create may or may not exist. Observe only; never send it again.
        for delay in self._settle:
            self._sleep(delay)
            try:
                found = self._existing(chat_id, statement)
            except self._refusal as error:
                if str(error) in {"chat_contains_unexpected_requests", "public_api_not_candidate"}:
                    raise
                continue
            if found is not None:
                return found
        raise self._refusal("create_unresolved_not_observed")

    def observe(self, request_id: str) -> dict[str, Any]:
        self._uuid(request_id, "canonical_uuid_required")
        body = self._read(f"/v1/proof-requests/{request_id}", "observe")
        self._need(body.get("id") == request_id and isinstance(body.get("chat_id"), str)
                   and UUID4.fullmatch(body["chat_id"]) and body.get("status") in STATUSES,
                   "observed_request_invalid")
        return {"id": body["id"], "chat_id": body["chat_id"], "status": body["status"]}
