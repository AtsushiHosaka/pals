#!/usr/bin/env python3
"""Provision the local Cognito pool, web client, and reviewer account.

This helper is deliberately restricted to the loopback-only Cognito emulator. It
never accepts a remote Cognito endpoint and never prints the reviewer password or
the access token used for its final authentication check.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from uuid import uuid4

_ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_ENV_SAFE_PASSWORD = re.compile(r"^[A-Za-z0-9._!@%+=:,/-]+$")
_LOCAL_EMAIL = re.compile(r"^[A-Za-z0-9._+-]+@[A-Za-z0-9.-]+$")
_RESOURCE_ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
_LOCAL_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})
_MAX_ENV_BYTES = 1024 * 1024
_MAX_RESPONSE_BYTES = 1024 * 1024
_TARGET_PREFIX = "AWSCognitoIdentityProviderService."
_TOKEN_ISSUER_ORIGIN = "http://localhost:9229"


class BootstrapError(RuntimeError):
    """A safe, user-facing bootstrap failure."""


class CognitoError(BootstrapError):
    """An error returned by the local Cognito JSON API."""

    def __init__(self, code: str, status: int) -> None:
        super().__init__(f"local Cognito returned {code} (HTTP {status})")
        self.code = code
        self.status = status


@dataclass(frozen=True)
class Settings:
    endpoint: str
    pool_name: str
    client_name: str
    configured_pool_id: str | None
    configured_client_id: str | None
    reviewer_email: str
    reviewer_name: str
    reviewer_password: str


@dataclass(frozen=True)
class EnvironmentFile:
    path: Path
    lines: tuple[str, ...]
    values: dict[str, str]


class CognitoClient:
    def __init__(self, endpoint: str, *, timeout_seconds: float = 10.0) -> None:
        self.endpoint = endpoint.rstrip("/") + "/"
        self.timeout_seconds = timeout_seconds

    def call(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("ascii")
        request = Request(
            self.endpoint,
            data=body,
            headers={
                "Content-Type": "application/x-amz-json-1.1",
                "X-Amz-Target": _TARGET_PREFIX + operation,
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read(_MAX_RESPONSE_BYTES + 1)
                if len(raw) > _MAX_RESPONSE_BYTES:
                    raise BootstrapError("local Cognito response exceeded the size limit")
        except HTTPError as error:
            raw = error.read(_MAX_RESPONSE_BYTES + 1)
            code = _error_code(raw)
            raise CognitoError(code, error.code) from None
        except (TimeoutError, URLError) as error:
            raise BootstrapError("could not reach the local Cognito emulator") from error

        try:
            decoded = json.loads(raw or b"{}")
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise BootstrapError("local Cognito returned invalid JSON") from error
        if not isinstance(decoded, dict):
            raise BootstrapError("local Cognito returned a non-object response")
        return decoded


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=Path(".env.local"))
    args = parser.parse_args(argv)

    try:
        environment = _read_environment(args.env_file)
        settings = _settings(environment.values)
        client = CognitoClient(settings.endpoint)
        pool_id, pool_state = _ensure_pool(client, settings)
        client_id, client_state = _ensure_client(client, settings, pool_id)
        account_state = _ensure_reviewer(client, settings, pool_id, client_id)
        _write_environment(
            environment,
            {
                "NEXT_PUBLIC_COGNITO_CLIENT_ID": client_id,
                "NEXT_PUBLIC_COGNITO_ENDPOINT": settings.endpoint,
                "NEXT_PUBLIC_COGNITO_USER_POOL_ID": pool_id,
                "PALS_COGNITO_APP_CLIENT_ID": client_id,
                # The pinned cognito-local config fixes the token issuer independently
                # of the host port used to reach its JSON API.
                "PALS_COGNITO_ISSUER": f"{_TOKEN_ISSUER_ORIGIN}/{pool_id}",
                "PALS_COGNITO_USER_POOL_ID": pool_id,
                "PALS_LOCAL_COGNITO_EMAIL": settings.reviewer_email,
                "PALS_LOCAL_COGNITO_PASSWORD": settings.reviewer_password,
            },
        )
    except BootstrapError as error:
        print(f"local Cognito bootstrap failed: {error}", file=sys.stderr)
        return 2
    except OSError:
        print("local Cognito bootstrap failed: local filesystem operation failed", file=sys.stderr)
        return 2

    print(
        json.dumps(
            {
                "account": account_state,
                "app_client": client_state,
                "environment_file": str(environment.path),
                "status": "ready",
                "user_pool": pool_state,
            },
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0


def _settings(values: dict[str, str]) -> Settings:
    host_port = _value(values, "COGNITO_LOCAL_HOST_PORT") or "9229"
    endpoint = (
        _value(values, "PALS_COGNITO_ENDPOINT_URL")
        or _value(values, "NEXT_PUBLIC_COGNITO_ENDPOINT")
        or f"http://localhost:{host_port}"
    ).rstrip("/")
    _require_local_endpoint(endpoint)

    reviewer_email = _value(values, "PALS_LOCAL_COGNITO_EMAIL") or "reviewer@example.test"
    if len(reviewer_email) > 320 or _LOCAL_EMAIL.fullmatch(reviewer_email) is None:
        raise BootstrapError("PALS_LOCAL_COGNITO_EMAIL must be a valid email-shaped value")

    reviewer_name = _value(values, "PALS_LOCAL_COGNITO_NAME") or "U-22 Reviewer"
    _require_plain_value(reviewer_name, "PALS_LOCAL_COGNITO_NAME", maximum=256)
    reviewer_password = _value(values, "PALS_LOCAL_COGNITO_PASSWORD") or _new_password()
    _require_password(reviewer_password)

    pool_name = _value(values, "PALS_COGNITO_USER_POOL_NAME") or "pals-local-users"
    client_name = _value(values, "PALS_COGNITO_APP_CLIENT_NAME") or "pals-local-web"
    _require_plain_value(pool_name, "PALS_COGNITO_USER_POOL_NAME", maximum=128)
    _require_plain_value(client_name, "PALS_COGNITO_APP_CLIENT_NAME", maximum=128)

    return Settings(
        endpoint=endpoint,
        pool_name=pool_name,
        client_name=client_name,
        configured_pool_id=_value(values, "PALS_COGNITO_USER_POOL_ID"),
        configured_client_id=_value(values, "PALS_COGNITO_APP_CLIENT_ID"),
        reviewer_email=reviewer_email,
        reviewer_name=reviewer_name,
        reviewer_password=reviewer_password,
    )


def _ensure_pool(client: CognitoClient, settings: Settings) -> tuple[str, str]:
    pools = _list_all(client, "ListUserPools", "UserPools", "MaxResults")
    selected = _select_named_resource(
        pools,
        id_key="Id",
        name_key="Name",
        configured_id=settings.configured_pool_id,
        expected_name=settings.pool_name,
        label="user pool",
    )
    if selected is not None:
        return selected, "ready"

    response = client.call(
        "CreateUserPool",
        {
            "AdminCreateUserConfig": {"AllowAdminCreateUserOnly": False},
            "AutoVerifiedAttributes": ["email"],
            "PoolName": settings.pool_name,
            "Policies": {
                "PasswordPolicy": {
                    "MinimumLength": 8,
                    "RequireLowercase": True,
                    "RequireNumbers": True,
                    "RequireSymbols": False,
                    "RequireUppercase": False,
                    "TemporaryPasswordValidityDays": 7,
                }
            },
            "UsernameAttributes": ["email"],
        },
    )
    pool = response.get("UserPool")
    pool_id = pool.get("Id") if isinstance(pool, dict) else None
    if not isinstance(pool_id, str) or not pool_id:
        raise BootstrapError("CreateUserPool omitted the user pool ID")
    _require_resource_id(pool_id, "user pool ID")
    return pool_id, "created"


def _ensure_client(
    client: CognitoClient,
    settings: Settings,
    pool_id: str,
) -> tuple[str, str]:
    clients = _list_all(
        client,
        "ListUserPoolClients",
        "UserPoolClients",
        "MaxResults",
        fixed_payload={"UserPoolId": pool_id},
    )
    selected = _select_named_resource(
        clients,
        id_key="ClientId",
        name_key="ClientName",
        configured_id=settings.configured_client_id,
        expected_name=settings.client_name,
        label="app client",
    )
    if selected is not None:
        return selected, "ready"

    response = client.call(
        "CreateUserPoolClient",
        {
            "ClientName": settings.client_name,
            "ExplicitAuthFlows": [
                "ALLOW_REFRESH_TOKEN_AUTH",
                "ALLOW_USER_PASSWORD_AUTH",
                "ALLOW_USER_SRP_AUTH",
            ],
            "GenerateSecret": False,
            "PreventUserExistenceErrors": "ENABLED",
            "UserPoolId": pool_id,
        },
    )
    app_client = response.get("UserPoolClient")
    client_id = app_client.get("ClientId") if isinstance(app_client, dict) else None
    if not isinstance(client_id, str) or not client_id:
        raise BootstrapError("CreateUserPoolClient omitted the app client ID")
    _require_resource_id(client_id, "app client ID")
    return client_id, "created"


def _ensure_reviewer(
    client: CognitoClient,
    settings: Settings,
    pool_id: str,
    client_id: str,
) -> str:
    created = False
    try:
        client.call(
            "AdminGetUser",
            {"UserPoolId": pool_id, "Username": settings.reviewer_email},
        )
    except CognitoError as error:
        if error.code != "UserNotFoundException":
            raise
        try:
            client.call(
                "AdminCreateUser",
                {
                    "MessageAction": "SUPPRESS",
                    "UserAttributes": [
                        {"Name": "email", "Value": settings.reviewer_email},
                        {"Name": "email_verified", "Value": "true"},
                        {"Name": "name", "Value": settings.reviewer_name},
                    ],
                    "UserPoolId": pool_id,
                    "Username": settings.reviewer_email,
                },
            )
            created = True
        except CognitoError as race_error:
            if race_error.code != "UsernameExistsException":
                raise

    client.call(
        "AdminEnableUser",
        {"UserPoolId": pool_id, "Username": settings.reviewer_email},
    )
    client.call(
        "AdminUpdateUserAttributes",
        {
            "UserAttributes": [
                {"Name": "email", "Value": settings.reviewer_email},
                {"Name": "email_verified", "Value": "true"},
                {"Name": "name", "Value": settings.reviewer_name},
            ],
            "UserPoolId": pool_id,
            "Username": settings.reviewer_email,
        },
    )
    client.call(
        "AdminSetUserPassword",
        {
            "Password": settings.reviewer_password,
            "Permanent": True,
            "UserPoolId": pool_id,
            "Username": settings.reviewer_email,
        },
    )
    response = client.call(
        "InitiateAuth",
        {
            "AuthFlow": "USER_PASSWORD_AUTH",
            "AuthParameters": {
                "PASSWORD": settings.reviewer_password,
                "USERNAME": settings.reviewer_email,
            },
            "ClientId": client_id,
        },
    )
    authentication = response.get("AuthenticationResult")
    token = authentication.get("AccessToken") if isinstance(authentication, dict) else None
    if not isinstance(token, str) or not token:
        raise BootstrapError("reviewer authentication did not return an access token")
    return "created" if created else "updated"


def _list_all(
    client: CognitoClient,
    operation: str,
    collection_key: str,
    limit_key: str,
    *,
    fixed_payload: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    next_token: str | None = None
    for _ in range(100):
        payload = dict(fixed_payload or {})
        payload[limit_key] = 60
        if next_token:
            payload["NextToken"] = next_token
        response = client.call(operation, payload)
        page = response.get(collection_key)
        if not isinstance(page, list) or not all(isinstance(item, dict) for item in page):
            raise BootstrapError(f"{operation} returned an invalid {collection_key} list")
        items.extend(page)
        candidate = response.get("NextToken")
        if candidate is None:
            return items
        if not isinstance(candidate, str) or not candidate or candidate == next_token:
            raise BootstrapError(f"{operation} returned an invalid pagination token")
        next_token = candidate
    raise BootstrapError(f"{operation} exceeded the pagination limit")


def _select_named_resource(
    resources: list[dict[str, Any]],
    *,
    id_key: str,
    name_key: str,
    configured_id: str | None,
    expected_name: str,
    label: str,
) -> str | None:
    normalized: list[tuple[str, str]] = []
    for resource in resources:
        identifier = resource.get(id_key)
        name = resource.get(name_key)
        if isinstance(identifier, str) and identifier and isinstance(name, str) and name:
            normalized.append((identifier, name))

    if configured_id:
        configured = [item for item in normalized if item[0] == configured_id]
        if configured and configured[0][1] != expected_name:
            raise BootstrapError(f"configured {label} ID belongs to a different name")
        if configured:
            _require_resource_id(configured_id, f"{label} ID")
            return configured_id

    named = [identifier for identifier, name in normalized if name == expected_name]
    if len(named) > 1:
        raise BootstrapError(f"multiple local {label}s use the expected name")
    if not named:
        return None
    _require_resource_id(named[0], f"{label} ID")
    return named[0]


def _read_environment(path: Path) -> EnvironmentFile:
    resolved = path.resolve(strict=False)
    if path.is_symlink():
        raise BootstrapError("environment file must not be a symbolic link")
    if not path.is_file():
        raise BootstrapError(f"environment file is missing: {path}")
    raw = path.read_bytes()
    if len(raw) > _MAX_ENV_BYTES:
        raise BootstrapError("environment file exceeded the size limit")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise BootstrapError("environment file must be UTF-8") from error

    lines = tuple(text.splitlines(keepends=True))
    values: dict[str, str] = {}
    for number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in line:
            raise BootstrapError(f"environment file line {number} is not NAME=VALUE")
        name, value = line.rstrip("\r\n").split("=", 1)
        name = name.strip()
        if _ENV_NAME.fullmatch(name) is None:
            raise BootstrapError(f"environment file line {number} has an invalid name")
        if name in values:
            raise BootstrapError(f"environment file contains duplicate {name}")
        values[name] = _unquote(value.strip())
    return EnvironmentFile(path=resolved, lines=lines, values=values)


def _write_environment(environment: EnvironmentFile, updates: dict[str, str]) -> None:
    for name, value in updates.items():
        if _ENV_NAME.fullmatch(name) is None or "\n" in value or "\r" in value:
            raise BootstrapError("refusing to write an invalid environment value")

    remaining = dict(updates)
    rendered: list[str] = []
    for line in environment.lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in line:
            name = line.split("=", 1)[0].strip()
            if name in remaining:
                rendered.append(f"{name}={remaining.pop(name)}\n")
                continue
        rendered.append(line)
    if rendered and not rendered[-1].endswith(("\n", "\r")):
        rendered[-1] += "\n"
    if remaining:
        if rendered and rendered[-1].strip():
            rendered.append("\n")
        rendered.append("# Generated by pals-scripts/bootstrap-local-cognito.py.\n")
        rendered.extend(f"{name}={remaining[name]}\n" for name in sorted(remaining))

    payload = "".join(rendered).encode("utf-8")
    temporary = environment.path.with_name(f".{environment.path.name}.{uuid4().hex}.tmp")
    try:
        descriptor = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            stat.S_IRUSR | stat.S_IWUSR,
        )
        try:
            os.write(descriptor, payload)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.replace(temporary, environment.path)
        os.chmod(environment.path, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        temporary.unlink(missing_ok=True)
        raise


def _value(values: dict[str, str], name: str) -> str | None:
    value = os.environ.get(name, values.get(name, "")).strip()
    return value or None


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _require_local_endpoint(value: str) -> None:
    parsed = urlparse(value)
    try:
        port = parsed.port
    except ValueError as error:
        raise BootstrapError("Cognito endpoint must be an explicit loopback HTTP origin") from error
    if (
        parsed.scheme != "http"
        or parsed.hostname not in _LOCAL_HOSTS
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in ("", "/")
        or port is None
    ):
        raise BootstrapError("Cognito endpoint must be an explicit loopback HTTP origin")


def _require_plain_value(value: str, name: str, *, maximum: int) -> None:
    if not value or len(value) > maximum or any(ord(character) < 32 for character in value):
        raise BootstrapError(f"{name} is invalid")


def _require_password(value: str) -> None:
    if (
        len(value) < 8
        or len(value) > 256
        or not any(character.islower() for character in value)
        or not any(character.isdigit() for character in value)
        or any(character in "\r\n\0" for character in value)
        or _ENV_SAFE_PASSWORD.fullmatch(value) is None
    ):
        raise BootstrapError(
            "PALS_LOCAL_COGNITO_PASSWORD must be 8-256 env-safe characters with a lowercase letter and digit"
        )


def _new_password() -> str:
    return f"PalsReview-{secrets.token_hex(16)}-7"


def _require_resource_id(value: str, label: str) -> None:
    if _RESOURCE_ID.fullmatch(value) is None:
        raise BootstrapError(f"local Cognito returned an invalid {label}")


def _error_code(raw: bytes) -> str:
    try:
        payload = json.loads(raw[:_MAX_RESPONSE_BYTES] or b"{}")
    except (UnicodeDecodeError, json.JSONDecodeError):
        return "UnknownError"
    if not isinstance(payload, dict):
        return "UnknownError"
    value = payload.get("__type") or payload.get("code") or payload.get("Code")
    if not isinstance(value, str) or not value:
        return "UnknownError"
    return value.rsplit("#", 1)[-1].rsplit(":", 1)[-1]


if __name__ == "__main__":
    raise SystemExit(main())
