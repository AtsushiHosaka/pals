"""Local-only real OpenAI forwarder. No synthetic output, cache, redirect, or retry."""

from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import socket
import ssl
from fractions import Fraction
from http.client import HTTPSConnection
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
        if path.exists():
            raw = path.read_bytes()
            if (
                resume_sha256 is None
                or hashlib.sha256(raw).hexdigest() != resume_sha256
            ):
                raise ValueError("existing_budget_no_automatic_retry")
            old = json.loads(raw)
            if (
                old["blocked"]
                or not old["calls"]
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
                or total > LIMIT
                or old["limit_microusd"] < LIMIT
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
                    "limit_microusd": LIMIT,
                    "reserved_microusd": self.held,
                    "actual_microusd": self.actual,
                    "blocked": self.blocked,
                    "calls": self.calls,
                    "resumed_from_sha256": self.resumed_from_sha256,
                },
                sort_keys=True,
            )
        )
        self.path.chmod(0o600)

    def reserve(self, model, inputs, outputs):
        amount = cost(model, inputs, outputs)
        with self.lock:
            if self.blocked or self.held + amount > LIMIT:
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

    def uncertain(self, index):
        with self.lock:
            self.blocked = True
            self.calls[index]["state"] = "unknown"
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
            raise ValueError("upstream_not_exact")
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
        except Exception:  # noqa: BLE001 - Every ambiguous paid forward must retain its reservation.
            if index is not None:
                self.server.budget.uncertain(index)
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
