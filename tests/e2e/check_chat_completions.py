"""Read-only real local Cognito/API smoke for chat completion notifications."""
from datetime import datetime
import json

import httpx

from check_chat_sharing import local_values


def run():
    values = local_values()
    origin = "http://127.0.0.1:" + values.get("PALS_API_HOST_PORT", "8000")
    cognito = "http://127.0.0.1:" + values.get("COGNITO_LOCAL_HOST_PORT", "9229")
    with httpx.Client(timeout=20, trust_env=False) as client:
        auth = client.post(cognito, headers={
            "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
            "Content-Type": "application/x-amz-json-1.1",
        }, json={"AuthFlow": "USER_PASSWORD_AUTH", "ClientId": values["PALS_COGNITO_APP_CLIENT_ID"],
                 "AuthParameters": {"USERNAME": values["PALS_LOCAL_COGNITO_EMAIL"],
                                    "PASSWORD": values["PALS_LOCAL_COGNITO_PASSWORD"]}})
        assert auth.status_code == 200, "Cognito sign-in failed"
        headers = {"Authorization": "Bearer " + auth.json()["AuthenticationResult"]["AccessToken"]}
        path = origin + "/v1/chat-completions"
        responses = [client.get(path), client.get(path + "?access_token=invalid"),
                     client.get(path + "?owner=another", headers=headers), client.get(path, headers=headers)]
        assert [response.status_code for response in responses] == [401, 401, 422, 200]
        assert all("no-store" in response.headers.get("cache-control", "") for response in responses)
        payload = responses[-1].json()
        assert set(payload) == {"items"}
        ids = set()
        for item in payload["items"]:
            assert set(item) == {"chat_id", "completion_id", "completed_at"}
            assert item["chat_id"] not in ids
            ids.add(item["chat_id"])
            assert item["completion_id"].startswith(("modern:", "legacy:"))
            assert datetime.fromisoformat(item["completed_at"].replace("Z", "+00:00")).tzinfo
        return {"status": "PASS", "completed_chats": len(ids),
                "checks": ["real Cognito", "owner feed", "metadata only", "unique chats",
                           "anonymous rejected", "query credentials rejected", "closed query", "no-store"]}


if __name__ == "__main__":
    try:
        print(json.dumps(run()))
    except Exception as error:
        print(json.dumps({"status": "FAIL", "error_type": type(error).__name__}))
        raise SystemExit(1) from None
