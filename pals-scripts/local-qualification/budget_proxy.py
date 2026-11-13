"""Local-only real OpenAI forwarder. No synthetic output, cache, redirect, or retry."""

from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import re
import socket
import ssl
from fractions import Fraction
from http.client import HTTPException, HTTPSConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock

# Conservative cache-write input rates; USD per million tokens == microUSD per token.
RATES = {
    "gpt-6.1-terra": (Fraction(5, 4), Fraction(5)),
    "gpt-6.1-sol": (Fraction(5, 2), Fraction(10)),
    "gpt-6-luna": (Fraction(1, 8), Fraction(1, 2)),
    "text-embedding-3-small": (Fraction(1, 50), Fraction(0)),
}
LIMIT = (
    700_000  # Reserve a separate production test budget inside the thread's total $1.
)
ROLLOVER_SCHEMA = "pals.local-qualification-budget-rollover.v1"
APPROVAL_SCHEMA = "pals.local-qualification-budget-rollover-approval.v1"
APPROVAL_KEYS = {
    "schema_version",
    "approved_by",
    "approved_at",
    "approval_text",
    "closed_ledger_sha256",
    "new_limit_microusd",
}
ROLLOVER_KEYS = {
    "schema_version",
    "rolled_over_from_sha256",
    "closed_totals",
    "approval_sha256",
    "rolled_over_at",
}
_SHA256 = re.compile(r"[0-9a-f]{64}")
_REASON = re.compile(r"[a-z0-9_]{1,48}")
# Closed, non-sensitive codes for a forward whose cost stays unknown. Never response text.
_VALUE_REASONS = {
    "upstream_too_large": "body_too_large",
    "upstream_model_changed": "model_mismatch",
    "upstream_standard_tier_unconfirmed": "service_tier",
    "usage_exceeds_reservation": "usage_above_reservation",
    "long_context_price_not_admitted": "usage_above_reservation",
    "unknown_price_or_usage": "unparseable_usage",
    "upstream_ip_not_public": "upstream_ip_not_public",
}


def unknown_reason(error):
    """Which condition left a reserved call without a known cost."""
    if isinstance(error, (json.JSONDecodeError, UnicodeDecodeError)):
        return "unparseable_body"
    if isinstance(error, TimeoutError):
        return "timeout"
    # Before ValueError: a certificate verification failure is both.
    if isinstance(error, ssl.SSLError):
        return "upstream_tls_error"
    if isinstance(error, ValueError):
        code = str(error)
        if re.fullmatch(r"upstream_status_[0-9]{3}", code):
            return code
        return _VALUE_REASONS.get(code, "internal_error")
    if isinstance(error, OSError):
        return "upstream_transport_error"
    if isinstance(error, HTTPException):
        return "upstream_protocol_error"
    if isinstance(error, (KeyError, TypeError, AttributeError)):
        return "unparseable_usage"
    return "internal_error"


def validate_approval(approval):
    """The owner's record: who, when, in which words, which ledger, which new bound."""
    if (
        type(approval) is not dict
        or set(approval) != APPROVAL_KEYS
        or approval["schema_version"] != APPROVAL_SCHEMA
        or any(
            type(approval[name]) is not str or not approval[name].strip()
            for name in ("approved_by", "approved_at", "approval_text")
        )
        or not re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}(T[0-9:.+Z-]{1,24})?", approval["approved_at"]
        )
        or type(approval["closed_ledger_sha256"]) is not str
        or not _SHA256.fullmatch(approval["closed_ledger_sha256"])
    ):
        raise ValueError("rollover_approval_record_invalid")
    limit = approval["new_limit_microusd"]
    if type(limit) is not int or not 0 < limit <= LIMIT:
        raise ValueError("rollover_new_limit_invalid")
    return approval


def closed_totals(ledger):
    """What a closed ledger leaves behind, including everything closed before it."""
    calls = ledger["calls"]
    reasons = {}
    for row in calls:
        if row["state"] == "unknown":
            reason = row.get("unknown_reason", "not_recorded")
            reasons[reason] = reasons.get(reason, 0) + 1
    totals = {
        "calls": len(calls),
        "actual_microusd": ledger["actual_microusd"],
        "reserved_microusd": ledger["reserved_microusd"],
        "unknown_calls": sum(reasons.values()),
        "unknown_reasons": reasons,
        "limit_microusd": ledger["limit_microusd"],
        "blocked": ledger["blocked"],
    }
    if (
        any(
            type(totals[name]) is not int or totals[name] < 0
            for name in ("actual_microusd", "reserved_microusd", "limit_microusd")
        )
        or type(totals["blocked"]) is not bool
    ):
        raise ValueError("rollover_closed_ledger_invalid")
    before = (ledger.get("rollover") or {}).get("closed_totals", {}).get("cumulative")
    before = before or {"ledgers": 0, "actual_microusd": 0, "reserved_microusd": 0}
    totals["cumulative"] = {
        "ledgers": before["ledgers"] + 1,
        "actual_microusd": before["actual_microusd"] + totals["actual_microusd"],
        "reserved_microusd": before["reserved_microusd"] + totals["reserved_microusd"],
    }
    return totals


def require_rollover_eligible(ledger):
    """Only a ledger that can never be resumed may be closed; a healthy one continues."""
    states = [row["state"] for row in ledger["calls"]]
    if "reserved" in states:
        # The outcome of that call was never recorded. It is not this tool's to guess.
        raise ValueError("rollover_call_in_flight_refused")
    if not (
        ledger["blocked"]
        or any(state != "completed" for state in states)
        or ledger["reserved_microusd"] != ledger["actual_microusd"]
    ):
        raise ValueError("rollover_healthy_ledger_refused")


def _closed_file(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("rollover_archive_missing")
    return path.read_bytes()


def validate_rollover(ledger, directory):
    """Prove a rolled-over ledger against its archive; returns the approved bound.

    The ledger names the closed ledger and the approval by hash. Both are re-read from
    ``closed-<sha256>/`` next to it, so a header without its archive, an edited archive,
    another approval or another bound is refused everywhere a ledger is accepted.
    """
    header = ledger.get("rollover")
    if (
        type(header) is not dict
        or set(header) != ROLLOVER_KEYS
        or header["schema_version"] != ROLLOVER_SCHEMA
        or type(header["rolled_over_at"]) is not str
        or any(
            type(header[name]) is not str or not _SHA256.fullmatch(header[name])
            for name in ("rolled_over_from_sha256", "approval_sha256")
        )
    ):
        raise ValueError("rollover_header_invalid")
    archive = directory / ("closed-" + header["rolled_over_from_sha256"])
    if archive.is_symlink() or not archive.is_dir():
        raise ValueError("rollover_archive_missing")
    closed_raw = _closed_file(archive / "ledger.json")
    approval_raw = _closed_file(archive / "approval.json")
    if hashlib.sha256(closed_raw).hexdigest() != header["rolled_over_from_sha256"]:
        raise ValueError("rollover_closed_ledger_changed")
    if hashlib.sha256(approval_raw).hexdigest() != header["approval_sha256"]:
        raise ValueError("rollover_approval_changed")
    try:
        closed, approval = json.loads(closed_raw), json.loads(approval_raw)
        validate_approval(approval)
        require_rollover_eligible(closed)
        totals = closed_totals(closed)
    except (KeyError, TypeError, AttributeError, json.JSONDecodeError):
        raise ValueError("rollover_archive_invalid") from None
    if approval["closed_ledger_sha256"] != header["rolled_over_from_sha256"]:
        raise ValueError("rollover_approval_names_another_ledger")
    if ledger.get("limit_microusd") != approval["new_limit_microusd"]:
        raise ValueError("rollover_limit_differs_from_approval")
    if header["closed_totals"] != totals:
        raise ValueError("rollover_closed_totals_changed")
    return approval["new_limit_microusd"]


def cost(model, inputs, outputs):
    if (
        model not in RATES
        or type(inputs) is not int
        or type(outputs) is not int
        or min(inputs, outputs) < 0
    ):
        raise ValueError("unknown_price_or_usage")
    if inputs > 272000:
        raise ValueError("long_context_price_not_admitted")
    amount = RATES[model][0] * inputs + RATES[model][1] * outputs
    return (amount.numerator + amount.denominator - 1) // amount.denominator


def validate_paid_payload(path, payload):
    if type(payload) is not dict:
        raise ValueError("unsupported_provider_payload")
    if path == "/v1/embeddings":
        if (
            set(payload) != {"model", "input", "dimensions"}
            or payload.get("model") != "text-embedding-3-small"
            or type(payload.get("input")) is not str
            or not payload["input"]
            or payload.get("dimensions") != 384
        ):
            raise ValueError("unsupported_single_embedding_payload")
        return
    if path != "/v1/responses" or payload.get("service_tier") != "default":
        raise ValueError("standard_service_tier_required")
    if set(payload) - {
        "model",
        "input",
        "max_output_tokens",
        "text",
        "service_tier",
        "reasoning",
        "store",
    }:
        raise ValueError("unsupported_response_fields")


class Budget:
    def __init__(self, path, *, resume_sha256=None):
        self.path = path
        self.lock = Lock()
        self.held = 0
        self.actual = 0
        self.blocked = False
        self.calls = []
        self.resumed_from_sha256 = None
        self.limit = LIMIT
        self.rollover = None
        if path.exists():
            raw = path.read_bytes()
            if (
                resume_sha256 is None
                or hashlib.sha256(raw).hexdigest() != resume_sha256
            ):
                raise ValueError("existing_budget_no_automatic_retry")
            old = json.loads(raw)
            rolled = old.get("rollover") is not None
            if rolled:
                # Only the owner-approved rollover may start from zero calls, and only
                # with its archive and approval intact. Its bound is never raised.
                self.limit = validate_rollover(old, path.parent)
                self.rollover = old["rollover"]
            if (
                old["blocked"]
                or (not old["calls"] and not rolled)
                or old["reserved_microusd"] != old["actual_microusd"]
            ):
                raise ValueError("uncertain_budget_cannot_resume")
            total = 0
            for row in old["calls"]:
                if row["state"] != "completed":
                    raise ValueError("uncertain_budget_cannot_resume")
                value = cost(row["model"], row["input_tokens"], row["output_tokens"])
                if value != row["actual_microusd"]:
                    raise ValueError("previous_budget_usage_changed")
                total += value
            if (
                total != old["actual_microusd"]
                or total > self.limit
                or (not rolled and old["limit_microusd"] < LIMIT)
            ):
                raise ValueError("previous_budget_total_changed")
            self.actual = self.held = total
            self.calls = old["calls"]
            self.resumed_from_sha256 = resume_sha256
        self.save()

    def save(self):
        self.path.write_text(
            json.dumps(
                {
                    "limit_microusd": self.limit,
                    "reserved_microusd": self.held,
                    "actual_microusd": self.actual,
                    "blocked": self.blocked,
                    "calls": self.calls,
                    "resumed_from_sha256": self.resumed_from_sha256,
                    "rollover": self.rollover,
                },
                sort_keys=True,
            )
        )
        self.path.chmod(0o600)

    def reserve(self, model, inputs, outputs):
        amount = cost(model, inputs, outputs)
        with self.lock:
            if self.blocked or self.held + amount > self.limit:
                raise ValueError("aggregate_budget_exceeded")
            self.held += amount
            self.calls.append(
                {
                    "model": model,
                    "input_bound": inputs,
                    "output_bound": outputs,
                    "reserved_microusd": amount,
                    "state": "reserved",
                }
            )
            self.save()
            return len(self.calls) - 1

    def complete(self, index, inputs, outputs):
        with self.lock:
            row = self.calls[index]
            amount = cost(row["model"], inputs, outputs)
            if (
                inputs > row["input_bound"]
                or outputs > row["output_bound"]
                or amount > row["reserved_microusd"]
            ):
                self.blocked = True
                self.save()
                raise ValueError("usage_exceeds_reservation")
            self.held -= row["reserved_microusd"] - amount
            self.actual += amount
            row.update(
                state="completed",
                input_tokens=inputs,
                output_tokens=outputs,
                actual_microusd=amount,
            )
            self.save()

    def uncertain(self, index, reason="not_recorded"):
        with self.lock:
            self.blocked = True
            self.calls[index]["state"] = "unknown"
            # A closed code only: which condition fired, never provider or request text.
            self.calls[index]["unknown_reason"] = (
                reason
                if type(reason) is str and _REASON.fullmatch(reason)
                else "internal_error"
            )
            self.save()


def upstream(path, payload):
    address = os.environ["PALS_OPENAI_UPSTREAM_IP"]
    if not ipaddress.ip_address(address).is_global:
        raise ValueError("upstream_ip_not_public")
    # Apps share this helper's hosts file. Resolve once outside that local DNS mapping,
    # then retain real api.openai.com SNI + certificate validation on the fixed public IP.
    connection = HTTPSConnection(
        "api.openai.com", timeout=80, context=ssl.create_default_context()
    )
    connection._create_connection = lambda _address, timeout, *_args: (
        socket.create_connection((address, 443), timeout)
    )
    try:
        connection.request(
            "POST",
            path,
            body=json.dumps(payload).encode(),
            headers={
                "Authorization": "Bearer " + os.environ["OPENAI_API_KEY"],
                "Content-Type": "application/json",
            },
        )
        response = connection.getresponse()
        if response.status != 200:
            raise ValueError("upstream_status_%03d" % response.status)
        raw = response.read(8 * 1024 * 1024 + 1)
        if len(raw) > 8 * 1024 * 1024:
            raise ValueError("upstream_too_large")
        return raw
    finally:
        connection.close()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def respond(self, status, raw):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        index = None
        try:
            if self.path not in {
                "/v1/responses",
                "/v1/responses/input_tokens",
                "/v1/embeddings",
            }:
                raise ValueError("unsupported_provider_endpoint")
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 2 * 1024 * 1024:
                raise ValueError("unsupported_provider_payload")
            payload = json.loads(self.rfile.read(size))
            model = payload.get("model")
            if model not in RATES or payload.get("stream") is True:
                raise ValueError("unsupported_model_or_stream")
            if self.path.endswith("/input_tokens"):
                return self.respond(200, upstream(self.path, payload))
            validate_paid_payload(self.path, payload)
            if self.path.endswith("/embeddings"):
                if model != "text-embedding-3-small":
                    raise ValueError("unsupported_embedding")
                inputs, outputs = 8192, 0
            else:
                if set(payload) - {
                    "model",
                    "input",
                    "max_output_tokens",
                    "text",
                    "service_tier",
                    "reasoning",
                    "store",
                }:
                    raise ValueError("unsupported_response_fields")
                counted = json.loads(
                    upstream(
                        "/v1/responses/input_tokens",
                        {
                            k: payload[k]
                            for k in ("model", "input", "text", "reasoning")
                            if k in payload
                        },
                    )
                )
                if (
                    set(counted) != {"object", "input_tokens"}
                    or counted["object"] != "response.input_tokens"
                ):
                    raise ValueError("count_unavailable")
                inputs, outputs = counted["input_tokens"], payload["max_output_tokens"]
                if not 0 < outputs <= 32768:
                    raise ValueError("output_limit_invalid")
            index = self.server.budget.reserve(model, inputs, outputs)
            raw = upstream(self.path, payload)
            body = json.loads(raw)
            usage = body["usage"]
            if body.get("model") != model:
                raise ValueError("upstream_model_changed")
            if outputs and body.get("service_tier") != "default":
                raise ValueError("upstream_standard_tier_unconfirmed")
            actual_in = (
                usage["prompt_tokens"] if outputs == 0 else usage["input_tokens"]
            )
            actual_out = 0 if outputs == 0 else usage["output_tokens"]
            self.server.budget.complete(index, actual_in, actual_out)
            self.respond(200, raw)
        except Exception as error:  # noqa: BLE001 - Every ambiguous paid forward must retain its reservation.
            if index is not None:
                self.server.budget.uncertain(index, unknown_reason(error))
            self.respond(
                402,
                b'{"error":{"message":"local_provider_budget_or_dependency_failed","type":"local_budget"}}',
            )


def serve(cert, key, ledger):
    server = ThreadingHTTPServer(("127.0.0.1", 443), Handler)
    server.budget = Budget(
        ledger, resume_sha256=os.environ.get("PALS_BUDGET_RESUME_SHA256")
    )
    tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    tls.load_cert_chain(cert, key)
    server.socket = tls.wrap_socket(server.socket, server_side=True)
    server.serve_forever()
