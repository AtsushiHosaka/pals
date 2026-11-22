"""Simulated SDK trust-boundary checks, not live AWS or refresh acceptance."""
import contextlib
import importlib.util
import io
import json
import logging
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location(
    "cognito_refresh_policy", Path(__file__).resolve().parents[1] / "release-cognito-refresh-policy.py",
)
P = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)

DESCRIPTOR = {
    "region": "ap-northeast-1", "account_id": "123456789012",
    "user_pool_id": "ap-northeast-1_Example", "client_id": "exampleClient123",
}


class SDK:
    def __init__(self):
        self.identity = {"Account": DESCRIPTOR["account_id"]}
        self.response = {"UserPoolClient": {
            "UserPoolId": DESCRIPTOR["user_pool_id"], "ClientId": DESCRIPTOR["client_id"],
            "ExplicitAuthFlows": ["ALLOW_USER_SRP_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"],
        }}
        self.calls = []
        self.fail = None
        self.noisy = False

    def config(self, **options):
        self.calls.append(("config", options))
        return options

    def session(self, **options):
        self.calls.append(("session", options))
        if self.fail == "session":
            raise RuntimeError("private SDK exception")
        return self

    def client(self, name, *, config):
        self.calls.append(("client", name, config))
        if self.fail == name:
            raise RuntimeError("private SDK exception")
        return self

    def get_caller_identity(self):
        self.calls.append(("get_caller_identity",))
        if self.fail == "identity":
            raise RuntimeError("private SDK exception")
        return self.identity

    def describe_user_pool_client(self, **options):
        self.calls.append(("describe_user_pool_client", options))
        if self.noisy:
            print("private stdout")
            print("private stderr", file=__import__("sys").stderr)
            logging.getLogger("botocore.test").critical("private logging")
        if self.fail == "describe":
            raise RuntimeError("private SDK exception")
        return self.response


class CognitoRefreshPolicyTest(unittest.TestCase):
    def invoke(self, descriptor=DESCRIPTOR, sdk=None, raw=None):
        sdk = sdk or SDK()
        output = io.StringIO()
        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            status = P.main(io.StringIO(raw if raw is not None else json.dumps(descriptor)), output,
                            session_factory=sdk.session, config_factory=sdk.config)
        self.assertEqual(error.getvalue(), "")
        value = json.loads(output.getvalue())
        self.assertEqual(set(value), {"allowed"} if value["allowed"] else {"allowed", "code"})
        self.assertEqual(status, 0 if value["allowed"] else 2)
        return value, sdk

    def refused(self, sdk, code):
        self.assertEqual(self.invoke(sdk=sdk)[0], {"allowed": False, "code": code})

    def test_absent_rotation_is_allowed_and_exact_read_only_sdk_calls_are_bound(self):
        value, sdk = self.invoke()
        self.assertEqual(value, {"allowed": True})
        self.assertEqual(sdk.calls[0], ("config", {
            "connect_timeout": 5, "read_timeout": 10,
            "retries": {"total_max_attempts": 1, "mode": "standard"},
            "ignore_configured_endpoint_urls": True,
        }))
        self.assertIn(("session", {"profile_name": "pals-prod-member", "region_name": "ap-northeast-1"}), sdk.calls)
        self.assertEqual([row[1] for row in sdk.calls if row[0] == "client"], ["sts", "cognito-idp"])
        self.assertEqual(sdk.calls[-1], ("describe_user_pool_client", {
            "UserPoolId": DESCRIPTOR["user_pool_id"], "ClientId": DESCRIPTOR["client_id"],
        }))

    def test_disabled_or_absent_feature_is_allowed(self):
        for rotation in ({"Feature": "DISABLED"}, {}):
            with self.subTest(rotation=rotation):
                sdk = SDK()
                sdk.response["UserPoolClient"]["RefreshTokenRotation"] = rotation
                self.assertTrue(self.invoke(sdk=sdk)[0]["allowed"])

    def test_enabled_unknown_or_malformed_rotation_is_refused(self):
        for rotation in ({"Feature": "ENABLED"}, {"Feature": "unknown"}, {"Feature": None},
                         {"Feature": False}, None, "DISABLED", []):
            with self.subTest(rotation=rotation):
                sdk = SDK()
                sdk.response["UserPoolClient"]["RefreshTokenRotation"] = rotation
                self.refused(sdk, "refresh_rotation_not_disabled")

    def test_secret_presence_is_refused_even_if_empty(self):
        for secret in ("private", "", None):
            sdk = SDK()
            sdk.response["UserPoolClient"]["ClientSecret"] = secret
            self.refused(sdk, "client_secret_present")

    def test_refresh_flow_must_be_explicitly_enabled(self):
        for flows in (None, [], ["ALLOW_USER_SRP_AUTH"], "ALLOW_REFRESH_TOKEN_AUTH",
                      ["ALLOW_REFRESH_TOKEN_AUTH", None]):
            sdk = SDK()
            sdk.response["UserPoolClient"]["ExplicitAuthFlows"] = flows
            self.refused(sdk, "refresh_auth_flow_unavailable")
        sdk = SDK()
        del sdk.response["UserPoolClient"]["ExplicitAuthFlows"]
        self.refused(sdk, "refresh_auth_flow_unavailable")

    def test_sts_account_mismatch_or_missing_stops_before_cognito(self):
        for identity in ({"Account": "999999999999"}, {}, None, []):
            sdk = SDK()
            sdk.identity = identity
            self.refused(sdk, "caller_account_mismatch")
            self.assertFalse(any(row[0] == "describe_user_pool_client" for row in sdk.calls))

    def test_response_pool_and_client_identity_must_match(self):
        for key in ("UserPoolId", "ClientId"):
            for value in ("different", None):
                sdk = SDK()
                sdk.response["UserPoolClient"][key] = value
                self.refused(sdk, "client_identity_mismatch")

    def test_missing_or_malformed_client_response_is_refused(self):
        for response in ({}, None, [], {"UserPoolClient": None}, {"UserPoolClient": []}):
            sdk = SDK()
            sdk.response = response
            self.refused(sdk, "client_response_invalid")

    def test_sdk_unavailability_is_closed_and_does_not_expose_exception_text(self):
        for failure in ("session", "sts", "identity", "cognito-idp", "describe"):
            sdk = SDK()
            sdk.fail = failure
            self.refused(sdk, "aws_unavailable")

    def test_descriptor_rejected_before_any_sdk_call(self):
        cases = [None, [], {}, {**DESCRIPTOR, "extra": "no"}]
        for key, values in {
            "region": ["us-east-1", None, "ap-northeast-1\n"],
            "account_id": ["123", 123456789012, "123456789012\n"],
            "user_pool_id": ["us-east-1_Example", "ap-northeast-1_", "ap-northeast-1_bad/path"],
            "client_id": ["", "a" * 129, "client-with-dash", "client\n"],
        }.items():
            cases.extend({**DESCRIPTOR, key: value} for value in values)
        for descriptor in cases:
            with self.subTest(descriptor=descriptor):
                value, sdk = self.invoke(descriptor)
                self.assertEqual(value, {"allowed": False, "code": "invalid_descriptor"})
                self.assertEqual(sdk.calls, [])

    def test_invalid_duplicate_oversized_or_extra_json_is_refused(self):
        raws = ["", "{", "{}{}", " " * (P.MAX_INPUT_BYTES + 1),
                json.dumps(DESCRIPTOR)[:-1] + ',"region":"ap-northeast-1"}',
                '{"region":NaN}']
        for raw in raws:
            self.assertEqual(self.invoke(raw=raw)[0], {"allowed": False, "code": "invalid_descriptor"})

    def test_sdk_stdout_stderr_and_logging_are_suppressed(self):
        sdk = SDK()
        sdk.noisy = True
        previous = logging.root.manager.disable
        ambient = io.StringIO()
        with contextlib.redirect_stdout(ambient):
            value, _ = self.invoke(sdk=sdk)
        self.assertEqual(ambient.getvalue(), "")
        self.assertEqual(value, {"allowed": True})
        self.assertEqual(logging.root.manager.disable, previous)

    def test_read_failure_is_closed(self):
        class BrokenInput:
            def read(self, _bound):
                raise OSError("private stream failure")
        output = io.StringIO()
        self.assertEqual(P.main(BrokenInput(), output), 2)
        self.assertEqual(json.loads(output.getvalue()), {"allowed": False, "code": "aws_unavailable"})

    def test_nonstandard_exception_cannot_supply_an_output_code(self):
        def broken_session(**_options):
            raise P.Refusal("private SDK text")
        output = io.StringIO()
        self.assertEqual(P.main(io.StringIO(json.dumps(DESCRIPTOR)), output,
                                session_factory=broken_session, config_factory=SDK().config), 2)
        self.assertEqual(json.loads(output.getvalue()), {"allowed": False, "code": "aws_unavailable"})


if __name__ == "__main__":
    unittest.main()
