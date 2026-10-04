"""Real local Cognito + HTTP publication/revocation smoke for a saved chat.

Run with pals-api/.venv/bin/python tests/e2e/check_chat_sharing.py --chat-id UUID.
Only loopback services are used. Existing active shares are never revoked or replaced.
Credentials are read from .env.local, kept in memory, and never included in evidence.
"""

from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID

import httpx


def local_values() -> dict[str, str]:
    values: dict[str, str] = {}
    for line in (Path(__file__).resolve().parents[2] / ".env.local").read_text().splitlines():
        if not line.strip() or line.lstrip().startswith("#") or "=" not in line:
            continue
        name, raw = line.split("=", 1)
        parts = shlex.split(raw, comments=True)
        values[name.strip()] = parts[0] if parts else ""
    return values


def check_headers(response: httpx.Response) -> None:
    assert "no-store" in response.headers.get("cache-control", ""), "cache protection missing"
    assert "noindex" in response.headers.get("x-robots-tag", ""), "index protection missing"
    assert response.headers.get("referrer-policy") == "no-referrer", "referrer protection missing"


def check_snapshot(value: dict) -> None:
    assert set(value) == {"title", "output_language", "captured_at", "messages"}
    assert value["messages"], "fixture has no saved conversation"
    for message in value["messages"]:
        assert set(message) == {"role", "kind", "content", "status", "lean_source"}
        if message["lean_source"] is not None:
            assert message["status"] == "verified", "private intermediate source escaped"


def run(chat_id: str) -> dict:
    assert str(UUID(chat_id, version=4)) == chat_id
    values = local_values()
    api_origin = "http://127.0.0.1:" + values.get("PALS_API_HOST_PORT", "8000")
    cognito_origin = "http://127.0.0.1:" + values.get("COGNITO_LOCAL_HOST_PORT", "9229")
    assert urlsplit(api_origin).hostname == urlsplit(cognito_origin).hostname == "127.0.0.1"
    with httpx.Client(timeout=20, trust_env=False) as transport:
        auth = transport.post(cognito_origin, headers={
            "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
            "Content-Type": "application/x-amz-json-1.1",
        }, json={
            "AuthFlow": "USER_PASSWORD_AUTH",
            "ClientId": values["PALS_COGNITO_APP_CLIENT_ID"],
            "AuthParameters": {"USERNAME": values["PALS_LOCAL_COGNITO_EMAIL"],
                               "PASSWORD": values["PALS_LOCAL_COGNITO_PASSWORD"]},
        })
        assert auth.status_code == 200, "real Cognito sign-in failed"
        owner_headers = {"Authorization": "Bearer " + auth.json()["AuthenticationResult"]["AccessToken"]}
        owned = api_origin + f"/v1/chats/{chat_id}/share"
        initial = transport.get(owned, headers=owner_headers)
        assert initial.status_code == 200, "owner share inspection failed"
        assert initial.json() == {"share": None}, "fixture already has a share; refusing to alter it"
        preview = transport.get(owned + "-preview", headers=owner_headers)
        assert preview.status_code == 200, "preview failed"
        check_headers(preview)
        reviewed = preview.json()
        check_snapshot(reviewed["snapshot"])
        created_tokens: list[str] = []
        try:
            stale = transport.post(owned, headers=owner_headers, json={"snapshot_digest": "0" * 64})
            assert stale.status_code == 409, "stale preview unexpectedly published"
            assert transport.get(owned, headers=owner_headers).json() == {"share": None}
            for generation in range(2):
                result = transport.post(owned, headers=owner_headers,
                                        json={"snapshot_digest": reviewed["snapshot_digest"]})
                assert result.status_code == 201, "publication failed"
                share = result.json()
                created_tokens.append(share["token"])
                assert set(share) == {"token", "created_at", "snapshot"}
                check_headers(result)
                public_url = api_origin + "/v1/shared-chats/" + share["token"]
                public = transport.get(public_url)
                assert public.status_code == 200, "anonymous retrieval failed"
                check_headers(public)
                assert public.json() == share["snapshot"], "public snapshot differs from publication"
                for field in ("title", "output_language", "messages"):
                    assert public.json()[field] == reviewed["snapshot"][field], "preview content changed"
                check_snapshot(public.json())
                assert transport.get(public_url, headers={"Authorization": "Bearer invalid"}).status_code == 200
                assert transport.get(owned, headers=owner_headers).json()["share"] == share
                duplicate = transport.post(owned, headers=owner_headers,
                                           json={"snapshot_digest": reviewed["snapshot_digest"]})
                assert duplicate.status_code == 409, "duplicate active link created"
                assert transport.delete(owned).status_code == 401, "anonymous revocation allowed"
                assert transport.get(public_url).json() == share["snapshot"]
                revoked = transport.delete(owned, headers=owner_headers)
                assert revoked.status_code == 204, "revocation failed"
                assert transport.delete(owned, headers=owner_headers).status_code == 204
                missing = transport.get(public_url)
                assert missing.status_code == 404, "revoked link remains readable"
                check_headers(missing)
                never_existed = transport.get(api_origin + "/v1/shared-chats/" + "z" * 43)
                assert never_existed.status_code == 404
                # Request IDs may differ; compare the public error code and message.
                assert missing.json()["error"]["code"] == never_existed.json()["error"]["code"]
                assert transport.get(owned, headers=owner_headers).json() == {"share": None}
            assert created_tokens[0] != created_tokens[1], "revoked token was reused"
            return {"status": "PASS", "chat_id": chat_id,
                    "messages": len(reviewed["snapshot"]["messages"]),
                    "checks": ["real Cognito", "preview", "stale digest rejection", "anonymous read",
                               "public allowlist", "duplicate conflict", "anonymous revoke rejection",
                               "no-store/noindex/referrer", "revoke", "idempotent revoke", "fresh token"]}
        finally:
            current = transport.get(owned, headers=owner_headers)
            if current.status_code == 200:
                share = current.json().get("share")
                if share and share["token"] in created_tokens:
                    assert transport.delete(owned, headers=owner_headers).status_code == 204


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chat-id", required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(run(args.chat_id), ensure_ascii=False))
    except Exception as error:
        # Never print HTTP exception URLs/headers or credential-bearing response bodies.
        print(json.dumps({"status": "FAIL", "error_type": type(error).__name__,
                          "reason": str(error) if isinstance(error, AssertionError) else "Local smoke failed"}))
        raise SystemExit(1) from None
