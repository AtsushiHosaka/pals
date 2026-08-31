from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "pals-scripts/bootstrap-local-cognito.py"


class CognitoState:
    def __init__(self) -> None:
        self.pool: dict[str, Any] | None = None
        self.app_client: dict[str, Any] | None = None
        self.user: dict[str, Any] | None = None
        self.operations: list[tuple[str, dict[str, Any]]] = []

    def dispatch(self, operation: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        self.operations.append((operation, payload))
        if operation == "ListUserPools":
            return 200, {"UserPools": [self.pool] if self.pool else []}
        if operation == "CreateUserPool":
            self.pool = {"Id": "local_pool123", "Name": payload["PoolName"]}
            return 200, {"UserPool": self.pool}
        if operation == "ListUserPoolClients":
            clients = [self.app_client] if self.app_client else []
            return 200, {"UserPoolClients": clients}
        if operation == "CreateUserPoolClient":
            self.app_client = {
                "ClientId": "client123",
                "ClientName": payload["ClientName"],
            }
            return 200, {"UserPoolClient": self.app_client}
        if operation == "AdminGetUser":
            if self.user is None:
                return 400, {"__type": "UserNotFoundException"}
            return 200, {"Username": self.user["Username"], "Enabled": self.user["Enabled"]}
        if operation == "AdminCreateUser":
            if self.user is not None:
                return 400, {"__type": "UsernameExistsException"}
            self.user = {
                "Enabled": True,
                "Password": None,
                "Username": payload["Username"],
            }
            return 200, {"User": {"Username": payload["Username"]}}
        if operation == "AdminEnableUser":
            assert self.user is not None
            self.user["Enabled"] = True
            return 200, {}
        if operation == "AdminUpdateUserAttributes":
            assert self.user is not None
            self.user["Attributes"] = payload["UserAttributes"]
            return 200, {}
        if operation == "AdminSetUserPassword":
            assert self.user is not None
            self.user["Password"] = payload["Password"]
            return 200, {}
        if operation == "InitiateAuth":
            assert self.user is not None
            parameters = payload["AuthParameters"]
            if (
                payload["ClientId"] != "client123"
                or parameters["USERNAME"] != self.user["Username"]
                or parameters["PASSWORD"] != self.user["Password"]
            ):
                return 400, {"__type": "NotAuthorizedException"}
            return 200, {"AuthenticationResult": {"AccessToken": "secret-access-token"}}
        return 400, {"__type": "UnsupportedOperationException"}


class Handler(BaseHTTPRequestHandler):
    server: CognitoServer

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length))
        target = self.headers.get("X-Amz-Target", "")
        operation = target.rsplit(".", 1)[-1]
        status, response = self.server.state.dispatch(operation, payload)
        encoded = json.dumps(response, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/x-amz-json-1.1")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, _format: str, *args: object) -> None:
        return


class CognitoServer(ThreadingHTTPServer):
    def __init__(self, state: CognitoState) -> None:
        super().__init__(("127.0.0.1", 0), Handler)
        self.state = state


class BootstrapLocalCognitoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = CognitoState()
        self.server = CognitoServer(self.state)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.env_file = Path(self.temporary.name) / ".env.local"
        self.password = "review-password-7"
        self.env_file.write_text(
            "# preserved comment\n"
            f"PALS_COGNITO_ENDPOINT_URL=http://127.0.0.1:{self.server.server_port}\n"
            "PALS_LOCAL_COGNITO_EMAIL=reviewer@example.test\n"
            f"PALS_LOCAL_COGNITO_PASSWORD={self.password}\n",
            encoding="utf-8",
        )

    def run_script(self, env_file: Path | None = None) -> subprocess.CompletedProcess[str]:
        clean_env = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--env-file", str(env_file or self.env_file)],
            cwd=ROOT,
            env=clean_env,
            capture_output=True,
            check=False,
            text=True,
        )

    def test_clean_bootstrap_creates_resources_authenticates_and_updates_env(self) -> None:
        result = self.run_script()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(result.stdout),
            {
                "account": "created",
                "app_client": "created",
                "environment_file": str(self.env_file.resolve()),
                "status": "ready",
                "user_pool": "created",
            },
        )
        self.assertNotIn(self.password, result.stdout + result.stderr)
        self.assertNotIn("secret-access-token", result.stdout + result.stderr)
        content = self.env_file.read_text(encoding="utf-8")
        self.assertIn("# preserved comment\n", content)
        self.assertIn("PALS_COGNITO_USER_POOL_ID=local_pool123\n", content)
        self.assertIn("PALS_COGNITO_APP_CLIENT_ID=client123\n", content)
        self.assertIn("NEXT_PUBLIC_COGNITO_CLIENT_ID=client123\n", content)
        self.assertIn(
            "PALS_COGNITO_ISSUER=http://localhost:9229/local_pool123\n",
            content,
        )
        self.assertEqual(self.env_file.stat().st_mode & 0o777, 0o600)
        self.assertEqual(
            [operation for operation, _ in self.state.operations],
            [
                "ListUserPools",
                "CreateUserPool",
                "ListUserPoolClients",
                "CreateUserPoolClient",
                "AdminGetUser",
                "AdminCreateUser",
                "AdminEnableUser",
                "AdminUpdateUserAttributes",
                "AdminSetUserPassword",
                "InitiateAuth",
            ],
        )

    def test_second_bootstrap_reuses_resources_and_updates_same_account(self) -> None:
        first = self.run_script()
        self.assertEqual(first.returncode, 0, first.stderr)
        self.state.operations.clear()

        second = self.run_script()

        self.assertEqual(second.returncode, 0, second.stderr)
        payload = json.loads(second.stdout)
        self.assertEqual(payload["user_pool"], "ready")
        self.assertEqual(payload["app_client"], "ready")
        self.assertEqual(payload["account"], "updated")
        self.assertEqual(
            [operation for operation, _ in self.state.operations],
            [
                "ListUserPools",
                "ListUserPoolClients",
                "AdminGetUser",
                "AdminEnableUser",
                "AdminUpdateUserAttributes",
                "AdminSetUserPassword",
                "InitiateAuth",
            ],
        )

    def test_missing_password_is_generated_and_never_printed(self) -> None:
        self.env_file.write_text(
            f"PALS_COGNITO_ENDPOINT_URL=http://127.0.0.1:{self.server.server_port}\n",
            encoding="utf-8",
        )

        result = self.run_script()

        self.assertEqual(result.returncode, 0, result.stderr)
        content = self.env_file.read_text(encoding="utf-8")
        password_line = next(
            line for line in content.splitlines() if line.startswith("PALS_LOCAL_COGNITO_PASSWORD=")
        )
        generated = password_line.split("=", 1)[1]
        self.assertGreaterEqual(len(generated), 8)
        self.assertNotIn(generated, result.stdout + result.stderr)

    def test_remote_endpoint_is_rejected_without_disclosing_credentials(self) -> None:
        remote = Path(self.temporary.name) / "remote.env"
        remote.write_text(
            "PALS_COGNITO_ENDPOINT_URL=https://cognito-idp.example.com\n"
            "PALS_LOCAL_COGNITO_EMAIL=private-reviewer@example.test\n"
            "PALS_LOCAL_COGNITO_PASSWORD=private-password-7\n",
            encoding="utf-8",
        )

        result = self.run_script(remote)

        self.assertEqual(result.returncode, 2)
        self.assertIn("loopback HTTP origin", result.stderr)
        self.assertNotIn("private-reviewer", result.stdout + result.stderr)
        self.assertNotIn("private-password", result.stdout + result.stderr)
        self.assertEqual(self.state.operations, [])

    def test_duplicate_resource_name_fails_closed(self) -> None:
        self.state.pool = {"Id": "local_pool123", "Name": "pals-local-users"}

        original_dispatch = self.state.dispatch

        def duplicate_dispatch(
            operation: str, payload: dict[str, Any]
        ) -> tuple[int, dict[str, Any]]:
            if operation == "ListUserPools":
                return 200, {
                    "UserPools": [
                        self.state.pool,
                        {"Id": "local_pool456", "Name": "pals-local-users"},
                    ]
                }
            return original_dispatch(operation, payload)

        self.state.dispatch = duplicate_dispatch  # type: ignore[method-assign]

        result = self.run_script()

        self.assertEqual(result.returncode, 2)
        self.assertIn("multiple local user pools", result.stderr)
        self.assertNotIn(self.password, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
