#!/usr/bin/env python3
"""Submit exactly one acceptance request to the newly activated release.

stdout contract (consumed by pals-infra release-cycle.py): one JSON object
{"id": <uuid>, "chat_id": <uuid>} and nothing else. Idempotency key =
sha256(candidate manifest sha256, scenario id, cycle id). The cycle id is a canonical
UUID minted once per release-cycle attempt (see docs/release-acceptance-credential.md);
a re-release of the same candidate is a new cycle and gets a new key, while a retry
inside one cycle observes the same request. A failed/needs_input request is observed
and reported, never resubmitted within its cycle. A durable private journal plus the
server-side Idempotency-Key replay guarantee make a retry or a crash observe the
existing request instead of creating a second paid job. User content (the scenario
statement), credentials and raw provider errors are never printed or journaled.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
import re
import stat
import sys
import time
from pathlib import Path
from typing import Any, Callable, Protocol
from uuid import UUID

HERE = Path(__file__).resolve().parent
SCENARIO_SCHEMA = "pals.post-request-scenario.v1"
JOURNAL_SCHEMA = "pals.post-request-journal.v1"
HEX = re.compile(r"[a-f0-9]{64}\Z")
LIVE_OK = {"queued", "assessing", "verifying", "answered"}
KEEP_WAITING = {"accepted"}
STATE_KEYS = {"chat_id", "request_id", "intent", "terminal_failure"}


class Refusal(RuntimeError):
    pass


def _load_acceptance():
    spec = importlib.util.spec_from_file_location("release_acceptance", HERE / "release-acceptance.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def need(value: Any, code: str) -> None:
    if not value:
        raise Refusal(code)


def idempotency_key(candidate_sha256: str, scenario_id: str, cycle_id: str) -> str:
    need(isinstance(candidate_sha256, str) and HEX.fullmatch(candidate_sha256), "candidate_sha256_required")
    need(isinstance(scenario_id, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", scenario_id),
         "scenario_id_invalid")
    canonical_uuid(cycle_id)
    # 64 hex chars satisfy the API's ^[A-Za-z0-9_-]{32,128}$ Idempotency-Key rule.
    return hashlib.sha256(b"pals.post-request.v2\0" + candidate_sha256.encode() + b"\0"
                          + scenario_id.encode() + b"\0" + cycle_id.encode()).hexdigest()


class Transport(Protocol):
    """Live adapter surface. Implementations must never log statements or tokens."""

    replay_safe: bool  # True only if create_request replays the same result for the same key

    def create_chat(self) -> str: ...

    def create_request(self, chat_id: str, key: str, scenario: dict[str, Any]) -> str:
        """Create the proof request with Idempotency-Key=key; a repeat with the same
        key/chat/body must return the SAME request id and never a new paid job."""

    def observe(self, request_id: str) -> dict[str, Any]:
        """Return {"id", "chat_id", "status"} for the request."""


class Journal:
    def __init__(self, state_dir: Path, key: str, payload: str):
        if not state_dir.exists():
            state_dir.mkdir(mode=0o700, parents=True)
        info = state_dir.lstat()
        need(stat.S_ISDIR(info.st_mode) and info.st_uid == os.geteuid()
             and stat.S_IMODE(info.st_mode) == 0o700, "private_state_directory_required")
        self.path = state_dir / "post-request.jsonl"
        self.key = key
        self.payload = payload
        fd = os.open(self.path, os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        self.stream = os.fdopen(fd, "a+b")
        meta = os.fstat(self.stream.fileno())
        need(stat.S_ISREG(meta.st_mode) and meta.st_uid == os.geteuid() and meta.st_nlink == 1
             and stat.S_IMODE(meta.st_mode) == 0o600, "protected_journal_required")
        try:
            fcntl.flock(self.stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise Refusal("post_request_already_running") from error
        self.state: dict[str, Any] = {}
        self.stream.seek(0)
        lines = self.stream.read().split(b"\n")
        torn = lines.pop()  # bytes after the last newline: empty, or a torn append
        offset = 0
        for line in lines:
            offset += len(line) + 1
            try:
                record = json.loads(line)
            except ValueError as error:
                raise Refusal("journal_corrupt") from error
            need(isinstance(record, dict) and record.get("schema_version") == JOURNAL_SCHEMA
                 and record.get("key") == key, "journal_belongs_to_another_request")
            need(record.get("payload_sha256") == payload, "scenario_payload_changed_since_journal")
            self.state.update({k: v for k, v in record.items() if k in STATE_KEYS})
        if torn:  # a crash mid-append: that record never completed, so discard it
            self.stream.truncate(offset)
            self.stream.flush()
            os.fsync(self.stream.fileno())

    def write(self, **fields: Any) -> None:
        record = {"schema_version": JOURNAL_SCHEMA, "key": self.key, "payload_sha256": self.payload, **fields}
        self.stream.write(json.dumps(record, sort_keys=True).encode() + b"\n")
        self.stream.flush()
        os.fsync(self.stream.fileno())
        self.state.update({k: v for k, v in fields.items() if k in STATE_KEYS})


def payload_sha256(scenario: dict[str, Any]) -> str:
    """Hash of the FULL scenario payload (statement included); the statement itself is never stored."""
    return hashlib.sha256(json.dumps(scenario, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode()).hexdigest()


def canonical_uuid(value: Any) -> str:
    try:
        ok = isinstance(value, str) and str(UUID(value)) == value
    except ValueError:
        ok = False
    need(ok, "canonical_uuid_required")
    return value


def load_inputs(contract_path: Path, contract_sha256: str | None, candidate_sha256: str,
                scenario_path: Path, scenario_sha256: str | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    acceptance = _load_acceptance()
    raw = acceptance.private_file(contract_path)
    if contract_sha256 is not None:
        need(acceptance.digest(raw) == contract_sha256, "contract_hash_changed")
    contract = acceptance.validate_contract(acceptance.document(raw))
    need(contract["phase"] == "post_deployment" and contract["target"] == "production",
         "production_post_deployment_contract_required")
    need(contract["manifest"]["sha256"] == candidate_sha256, "contract_not_for_candidate")
    scenario_raw = acceptance.private_file(scenario_path)
    if scenario_sha256 is not None:  # the plan pins the exact statement bytes
        need(HEX.fullmatch(scenario_sha256) and acceptance.digest(scenario_raw) == scenario_sha256,
             "scenario_hash_changed")
    scenario = acceptance.document(scenario_raw)
    need(set(scenario) == {"schema_version", "scenario_id", "statement", "generation_model",
                           "reasoning_effort", "output_language"}
         and scenario["schema_version"] == SCENARIO_SCHEMA
         and isinstance(scenario["statement"], str) and 0 < len(scenario["statement"].strip()) <= 20000,
         "scenario_shape_invalid")
    request = contract["request"]
    for name in ("generation_model", "reasoning_effort", "output_language"):
        need(scenario[name] == request[name], "scenario_differs_from_contract")
    return contract, scenario


def run(transport: Transport, journal: Journal, key: str, scenario: dict[str, Any], *,
        wait_seconds: float, poll_seconds: float = 2.0,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep) -> dict[str, str]:
    state = journal.state
    if "request_id" not in state:
        if "chat_id" not in state:
            # A crash right after this call leaves an empty orphan chat: free, harmless.
            journal.write(chat_id=canonical_uuid(transport.create_chat()))
        if state.get("intent") and not transport.replay_safe:
            # The create may already have reached the server; without server replay a
            # second call could be a second paid job. Refuse instead of guessing.
            raise Refusal("ambiguous_create_requires_manual_reconciliation")
        journal.write(intent="create_request")  # durable intent BEFORE the paid call
        journal.write(request_id=canonical_uuid(
            transport.create_request(state["chat_id"], key, scenario)))
    request_id, chat_id = state["request_id"], state["chat_id"]
    if state.get("terminal_failure"):
        raise Refusal("request_failed_not_resubmitted:" + state["terminal_failure"])
    deadline = clock() + wait_seconds
    while True:
        observed = transport.observe(request_id)
        need(isinstance(observed, dict) and observed.get("id") == request_id
             and observed.get("chat_id") == chat_id, "observed_request_identity_differs")
        status = observed.get("status")
        if status in {"failed", "needs_input"}:
            # Reported, never resubmitted in this cycle; a new cycle has a new key.
            journal.write(terminal_failure=status)
            raise Refusal("request_failed_not_resubmitted:" + status)
        need(status in LIVE_OK | KEEP_WAITING, "request_not_live")
        if status in LIVE_OK:
            journal.write(observed_status=status)
            return {"id": request_id, "chat_id": chat_id}
        need(clock() < deadline, "request_observation_deadline_exceeded")
        sleep(poll_seconds)


def main(argv: list[str] | None = None,
         transport_factory: Callable[..., Transport] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--contract-sha256")
    parser.add_argument("--candidate-sha256", required=True)
    parser.add_argument("--cycle-id", required=True)
    parser.add_argument("--scenario-sha256")
    parser.add_argument("--scenario", required=True, type=Path)
    parser.add_argument("--session", required=True, type=Path)
    parser.add_argument("--state-dir", required=True, type=Path)
    parser.add_argument("--wait-seconds", type=int, default=120)
    args = parser.parse_args(argv)
    try:
        os.umask(0o077)
        need(1 <= args.wait_seconds <= 900, "bounded_wait_required")
        contract, scenario = load_inputs(args.contract, args.contract_sha256,
                                         args.candidate_sha256, args.scenario, args.scenario_sha256)
        key = idempotency_key(args.candidate_sha256, scenario["scenario_id"], args.cycle_id)
        need(transport_factory is not None, "live_transport_adapter_not_supplied")
        transport = transport_factory(api_origin=contract["api_origin"], session=args.session)
        journal = Journal(args.state_dir, key, payload_sha256(scenario))
        try:
            result = run(transport, journal, key, scenario, wait_seconds=args.wait_seconds)
        finally:
            journal.stream.close()
        print(json.dumps(result, sort_keys=True))
        return 0
    except Exception as error:  # noqa: BLE001 -- never print provider text or user content.
        reason = str(error) if isinstance(error, Refusal) else "closed_failure"
        print(json.dumps({"status": "post_request_refused", "reason": reason}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
