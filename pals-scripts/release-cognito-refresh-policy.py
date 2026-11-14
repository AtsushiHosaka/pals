#!/usr/bin/env python3
"""Read-only AWS guard for a public Cognito client's nonrotating refresh policy.

Input is a bounded public descriptor, never session contents or tokens. Success
authorizes no AWS mutation and does not itself refresh a token. The caller must
enforce its own 20-second process deadline. Tests of this SDK boundary are not
live AWS acceptance.
"""
from __future__ import annotations

import contextlib
import json
import logging
import re
import sys

REGION = "ap-northeast-1"
PROFILE = "pals-prod-member"
MAX_INPUT_BYTES = 4096
FIELDS = frozenset({"region", "account_id", "user_pool_id", "client_id"})
CODES = frozenset({
    "invalid_descriptor", "aws_unavailable", "caller_account_mismatch",
    "client_response_invalid", "client_identity_mismatch", "client_secret_present",
    "refresh_rotation_not_disabled", "refresh_auth_flow_unavailable",
})


class Refusal(Exception):
    """Only fixed, non-sensitive codes may cross the CLI boundary."""


class _Discard:
    def write(self, value):
        return len(value)

    def flush(self):
        pass


@contextlib.contextmanager
def _quiet_sdk():
    previous = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    try:
        with contextlib.redirect_stdout(_Discard()), contextlib.redirect_stderr(_Discard()):
            yield
    finally:
        logging.disable(previous)


def validate_descriptor(value):
    if (type(value) is not dict or set(value) != FIELDS
            or any(type(item) is not str for item in value.values())
            or value["region"] != REGION
            or re.fullmatch(r"[0-9]{12}", value["account_id"]) is None
            or re.fullmatch(re.escape(REGION) + r"_[A-Za-z0-9]{1,64}", value["user_pool_id"]) is None
            or re.fullmatch(r"[A-Za-z0-9]{1,128}", value["client_id"]) is None):
        raise Refusal("invalid_descriptor")
    return value


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Refusal("invalid_descriptor")
        result[key] = value
    return result


def parse_descriptor(raw):
    if not isinstance(raw, (str, bytes)) or not 0 < len(raw) <= MAX_INPUT_BYTES:
        raise Refusal("invalid_descriptor")
    try:
        return validate_descriptor(json.loads(raw, object_pairs_hook=_unique_object))
    except (ValueError, UnicodeError):
        raise Refusal("invalid_descriptor") from None


def require_policy(descriptor, *, session_factory=None, config_factory=None):
    descriptor = validate_descriptor(descriptor)
    # Silence SDK debug output and credential-provider diagnostics. Exceptions are
    # converted to a fixed code without serializing their message or response.
    with _quiet_sdk():
        try:
            if session_factory is None:
                import boto3
                session_factory = boto3.Session
            if config_factory is None:
                from botocore.config import Config
                config_factory = Config
            config = config_factory(
                connect_timeout=5, read_timeout=10,
                retries={"total_max_attempts": 1, "mode": "standard"},
                ignore_configured_endpoint_urls=True,
            )
            session = session_factory(profile_name=PROFILE, region_name=REGION)
            identity = session.client("sts", config=config).get_caller_identity()
            if type(identity) is not dict or identity.get("Account") != descriptor["account_id"]:
                raise Refusal("caller_account_mismatch")
            response = session.client("cognito-idp", config=config).describe_user_pool_client(
                UserPoolId=descriptor["user_pool_id"], ClientId=descriptor["client_id"],
            )
            client = response.get("UserPoolClient") if type(response) is dict else None
            if type(client) is not dict:
                raise Refusal("client_response_invalid")
            if (client.get("UserPoolId") != descriptor["user_pool_id"]
                    or client.get("ClientId") != descriptor["client_id"]):
                raise Refusal("client_identity_mismatch")
            if "ClientSecret" in client:
                raise Refusal("client_secret_present")
            if "RefreshTokenRotation" in client:
                rotation = client["RefreshTokenRotation"]
                if (type(rotation) is not dict
                        or ("Feature" in rotation and rotation["Feature"] != "DISABLED")):
                    raise Refusal("refresh_rotation_not_disabled")
            flows = client.get("ExplicitAuthFlows")
            if (type(flows) is not list or any(type(flow) is not str for flow in flows)
                    or "ALLOW_REFRESH_TOKEN_AUTH" not in flows):
                raise Refusal("refresh_auth_flow_unavailable")
        except Refusal:
            raise
        except Exception:
            raise Refusal("aws_unavailable") from None


def main(stdin=None, stdout=None, *, session_factory=None, config_factory=None):
    source = stdin if stdin is not None else sys.stdin.buffer
    output = stdout if stdout is not None else sys.stdout
    try:
        descriptor = parse_descriptor(source.read(MAX_INPUT_BYTES + 1))
        require_policy(descriptor, session_factory=session_factory, config_factory=config_factory)
        result, status = {"allowed": True}, 0
    except Refusal as error:
        code = str(error)
        result, status = {"allowed": False, "code": code if code in CODES else "aws_unavailable"}, 2
    except Exception:
        result, status = {"allowed": False, "code": "aws_unavailable"}, 2
    output.write(json.dumps(result, separators=(",", ":")) + "\n")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
