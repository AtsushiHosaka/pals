"""Deterministic gate contracts, not evidence of a production answer."""
from __future__ import annotations

import copy
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "release-acceptance.py"
spec = importlib.util.spec_from_file_location("release_acceptance", SCRIPT)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def contract():
    return {
        "schema_version": gate.SCHEMA, "phase": "pre_release", "target": "staging",
        "manifest": {"path": "/missing/manifest", "sha256": "1" * 64,
                     "signature_path": "/missing/signature", "public_key_path": "/missing/key",
                     "public_key_spki_sha256": "2" * 64},
        "runtime": {role: {"context": "pals-acceptance-missing-context", "endpoint_sha256": "3" * 64,
                           "container": "acceptance-" + role, "config_sha256": "4" * 64,
                           "environment_sha256": "5" * 64} for role in gate.ROLES},
        "runner_sha256": gate.runner_fingerprint(), "web_root": "/missing/web",
        "web_origin": "https://staging.example.test", "api_origin": "https://api.staging.example.test",
        "auth_origin": None,
        "request": {"id": "3a84ab28-808c-44ef-8404-f75716b5026b", "chat_id": "3dd7f299-dd37-4ac9-9e45-9bad2ae4dd12",
                    "generation_model": "gpt-6.1-terra", "reasoning_effort": "high", "output_language": "en",
                    "required_conclusion_text": ["The limit is zero."], "required_conclusion_math": []},
        "timeout_seconds": 30, "max_age_seconds": 600,
    }


def write_private(path, raw):
    path.write_bytes(raw)
    path.chmod(0o600)
    return path


class ContractTests(unittest.TestCase):
    def test_all_roles_and_real_conclusion_oracle_are_required(self):
        gate.validate_contract(contract())
        for role in gate.ROLES:
            bad = contract(); del bad["runtime"][role]
            with self.assertRaisesRegex(gate.Refusal, "all_runtime_roles_required"):
                gate.validate_contract(bad)
        bad = contract(); bad["request"]["required_conclusion_text"] = []
        with self.assertRaisesRegex(gate.Refusal, "conclusion_oracle_required"):
            gate.validate_contract(bad)

    def test_caller_cannot_supply_pass_booleans_or_relabel_production_as_staging(self):
        bad = contract(); bad["passed"] = True
        with self.assertRaisesRegex(gate.Refusal, "contract_members_differ"):
            gate.validate_contract(bad)
        bad = contract(); bad["target"] = "production"
        with self.assertRaisesRegex(gate.Refusal, "pre_release_requires_staging"):
            gate.validate_contract(bad)

    def test_revisions_and_credential_bearing_or_insecure_origins_fail(self):
        bad = contract(); bad["runner_sha256"] = "9" * 64
        with self.assertRaisesRegex(gate.Refusal, "executing_runner_changed"):
            gate.validate_contract(bad)
        for origin in ("https://user:secret@staging.example.test", "https://example.test/?token=secret", "http://example.test"):
            bad = contract(); bad["web_origin"] = origin
            with self.assertRaisesRegex(gate.Refusal, "unsafe_acceptance_origin"):
                gate.validate_contract(bad)

    def test_duplicate_json_and_public_or_symlinked_session_files_fail(self):
        with self.assertRaisesRegex(gate.Refusal, "duplicate_json_member"):
            gate.document(b'{"pass":false,"pass":true}')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            secret = write_private(root / "session", b"not-a-real-session")
            link = root / "link"; link.symlink_to(secret)
            with self.assertRaises(gate.Refusal): gate.private_file(link)
            secret.chmod(0o644)
            with self.assertRaises(gate.Refusal): gate.private_file(secret)

    def test_latest_failure_or_interrupted_run_blocks_earlier_success(self):
        now = datetime.now(UTC)
        good = {"state": "accepted", "contract_sha256": "1" * 64, "runner_sha256": "2" * 64,
                "finished_at": now.isoformat()}
        self.assertEqual(gate.latest_status([good], "1" * 64, "2" * 64, now, 60), good)
        for state in ("failed", "running", "blocked"):
            with self.assertRaisesRegex(gate.Refusal, "latest_acceptance_not_green"):
                gate.latest_status([good, {"state": state}], "1" * 64, "2" * 64, now, 60)

    def test_stale_future_or_wrong_candidate_evidence_cannot_promote(self):
        now = datetime.now(UTC)
        record = {"state": "accepted", "contract_sha256": "1" * 64, "runner_sha256": "2" * 64}
        for age in (61, -1):
            record["finished_at"] = (now - timedelta(seconds=age)).isoformat()
            with self.assertRaisesRegex(gate.Refusal, "acceptance_stale"):
                gate.latest_status([record], "1" * 64, "2" * 64, now, 60)
        record["finished_at"] = now.isoformat()
        with self.assertRaisesRegex(gate.Refusal, "latest_acceptance_not_green"):
            gate.latest_status([record], "3" * 64, "2" * 64, now, 60)

    def test_deferred_postdeployment_ids_are_bound_without_changing_frozen_scenario(self):
        fixed = contract(); fixed.update(phase="post_deployment", target="production")
        fixed["request"].update(id=None, chat_id=None)
        gate.validate_contract(fixed)
        ids = contract()["request"]
        captured = gate.effective_contract(fixed, ids["id"], ids["chat_id"])
        self.assertIsNone(fixed["request"]["id"])
        self.assertEqual(captured["request"]["required_conclusion_text"], fixed["request"]["required_conclusion_text"])
        self.assertEqual(captured["request"]["id"], ids["id"])
        with self.assertRaisesRegex(gate.Refusal, "post_deployment_request_identity_required"):
            gate.effective_contract(fixed, None, None)
        with self.assertRaisesRegex(gate.Refusal, "both_request_identity_overrides_required"):
            gate.effective_contract(fixed, ids["id"], None)
        with self.assertRaisesRegex(gate.Refusal, "identity_override_only_after_deployment"):
            gate.effective_contract(contract(), ids["id"], ids["chat_id"])
        now = datetime.now(UTC)
        record = {"state": "accepted", "contract_sha256": "1" * 64, "runner_sha256": "2" * 64,
                  "effective_contract_sha256": gate.digest(gate.encoded(captured)), "finished_at": now.isoformat()}
        with self.assertRaisesRegex(gate.Refusal, "acceptance_request_binding_changed"):
            gate.latest_status([record], "1" * 64, "2" * 64, now, 60, "3" * 64)


class SSMTransportContracts(unittest.TestCase):
    """AWS is an isolated unit boundary here; only a real runner can qualify a target."""
    def binding(self):
        return {"ssm": {"profile": "pals-prod-member", "region": "ap-northeast-1",
                         "account_id": "000000000001", "instance_id": "i-0123456789abcdef0"},
                "container": "acceptance-api", "config_sha256": "4" * 64, "environment_sha256": "5" * 64}

    def metadata(self):
        uri = "000000000001.dkr.ecr.ap-northeast-1.amazonaws.com/pals-prod-api@sha256:" + "a" * 64
        image_id = "sha256:" + "b" * 64
        container = {"Id": "c" * 64, "Image": image_id,
                     "Config": {"Image": uri, "Env": ["PALS_DATABASE_URL=SECRET_DATABASE_VALUE", "API_KEY=SECRET_PROVIDER_VALUE",
                                                        "PALS_CLOUD_RESTORE_MANIFEST_SHA256=" + "1" * 64],
                                "Labels": {"com.pals.private-control": "4" * 64, "unexpected": "SECRET_LABEL_VALUE"}},
                     "State": {"Running": True, "StartedAt": "2026-11-08T10:00:00Z", "Error": "SECRET_ERROR_VALUE"}}
        image = {"Id": image_id, "RepoDigests": [uri], "Os": "linux", "Architecture": "arm64",
                 "Config": {"Labels": {"org.opencontainers.image.revision": "d" * 40, "extra": "SECRET_IMAGE_LABEL"}}}
        return container, image

    def test_fixed_transport_allows_only_approved_profile_region_and_exact_instance(self):
        value = contract(); value["runtime"]["api"] = self.binding()
        gate.validate_contract(value)
        for key, bad in (("profile", "another-profile"), ("region", "another-region"), ("instance_id", "*")):
            modified = copy.deepcopy(value); modified["runtime"]["api"]["ssm"][key] = bad
            with self.assertRaisesRegex(gate.Refusal, "ssm_target_invalid"): gate.validate_contract(modified)
        with self.assertRaisesRegex(gate.Refusal, "ssm_manifest_account_differs"):
            gate.ssm_observe(self.binding(), account_id="000000000002")

    def test_remote_sanitizer_never_returns_secrets_full_env_config_or_errors(self):
        container, image = self.metadata()
        observed = gate.sanitize_runtime(container, image)
        raw = gate.encoded(observed)
        self.assertNotIn(b"SECRET", raw)
        self.assertNotIn(b"PALS_DATABASE_URL", raw)
        self.assertNotIn(b'"Env"', raw)
        self.assertNotIn(b'"Config"', raw)
        self.assertEqual(observed["api_manifest_sha256"], "1" * 64)
        self.assertEqual(observed["environment_sha256"], gate.digest(gate.encoded(sorted(container["Config"]["Env"]))))
        image["Config"]["Labels"]["org.opencontainers.image.revision"] = "SECRET_WRONGLY_LABELLED_VALUE"
        self.assertNotIn(b"SECRET", gate.encoded(gate.sanitize_runtime(container, image)))
        container["State"]["Health"] = {"Status": "UNKNOWN_OR_SECRET_VALUE"}
        self.assertEqual(gate.sanitize_runtime(container, image)["state"]["health"], "invalid")

    def test_remote_program_is_fixed_read_only_and_rejects_command_or_path_injection(self):
        program = gate.remote_program("acceptance-api")
        compile(program, "observer", "exec")
        self.assertIn("capture_output=True", program)
        self.assertIn("result = sanitize_runtime(container, image)", program)
        self.assertNotIn("SECRET_DATABASE_VALUE", program)
        self.assertNotIn("print(container)", program)
        compile(gate.remote_program("acceptance-web", "/_next/static/chunks/[runtime].js"), "asset", "exec")
        for bad in ("api;id", "api\nwhoami"):
            with self.assertRaisesRegex(gate.Refusal, "remote_container_invalid"): gate.remote_program(bad)
        with self.assertRaisesRegex(gate.Refusal, "remote_asset_path_invalid"):
            gate.remote_program("web", "/_next/static/../../credentials.js")

    def test_only_exact_successful_ssm_invocation_is_consumed(self):
        binding = self.binding(); identifier = "c7512219-d918-4a67-b823-a78ac71e7bb8"
        observed = gate.sanitize_runtime(*self.metadata())
        response = {"Status": "Success", "ResponseCode": 0, "CommandId": identifier,
                    "InstanceId": binding["ssm"]["instance_id"], "StandardErrorContent": "",
                    "StandardOutputContent": json.dumps(observed)}
        prefix = [{"Account": "000000000001"}, {"Command": {"CommandId": identifier}}]
        with patch.object(gate, "aws_read", side_effect=prefix + [gate.SSMNotReady(), response]), patch.object(gate.time, "sleep"):
            self.assertEqual(gate.ssm_observe(binding, account_id="000000000001"), observed)
        for field, bad in (("InstanceId", "i-00000000000000000"), ("ResponseCode", 1), ("Status", "Failed")):
            rejected = dict(response); rejected[field] = bad
            with patch.object(gate, "aws_read", side_effect=prefix + [rejected]), patch.object(gate.time, "sleep"):
                with self.assertRaisesRegex(gate.Refusal, "ssm_runtime_observation_failed"):
                    gate.ssm_observe(binding, account_id="000000000001")
        with patch.object(gate, "aws_read", return_value={"Account": "000000000002"}) as request:
            with self.assertRaisesRegex(gate.Refusal, "ssm_caller_account_differs"):
                gate.ssm_observe(binding, account_id="000000000001")
            self.assertEqual(request.call_count, 1)


class SignatureAndFailClosedTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.contract = contract()
        private = self.root / "private.pem"
        subprocess.run(["openssl", "genpkey", "-algorithm", "EC", "-pkeyopt", "ec_paramgen_curve:P-256", "-out", str(private)], check=True, capture_output=True)
        public = self.root / "public.der"
        subprocess.run(["openssl", "pkey", "-in", str(private), "-pubout", "-outform", "DER", "-out", str(public)], check=True, capture_output=True)
        public.chmod(0o600)
        now = datetime.now(UTC)
        manifest = {"images": {role: "sha256:" + "a" * 64 for role in ("api", "web", "worker", "verifier")},
                    "source_commits": {name: "b" * 40 for name in ("pals", "pals-api", "pals-infra", "pals-agent", "pals-webfront")},
                    "issued_at": (now - timedelta(minutes=1)).isoformat(), "expires_at": (now + timedelta(minutes=10)).isoformat()}
        path = write_private(self.root / "manifest", gate.encoded(manifest))
        signature = self.root / "signature"
        subprocess.run(["openssl", "dgst", "-sha256", "-sign", str(private), "-out", str(signature), str(path)], check=True, capture_output=True)
        signature.chmod(0o600)
        self.contract["manifest"] = {"path": str(path), "sha256": gate.digest(path.read_bytes()), "signature_path": str(signature),
                                     "public_key_path": str(public), "public_key_spki_sha256": gate.digest(public.read_bytes())}

    def tearDown(self): self.temp.cleanup()

    def test_real_signature_is_verified_and_changed_manifest_key_or_signature_fails(self):
        result = gate.verify_manifest(self.contract)
        self.assertEqual(result["source_commits"]["pals"], "b" * 40)
        bad = copy.deepcopy(self.contract); bad["manifest"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(gate.Refusal, "candidate_manifest_changed"): gate.verify_manifest(bad)
        bad = copy.deepcopy(self.contract); bad["manifest"]["public_key_spki_sha256"] = "0" * 64
        with self.assertRaisesRegex(gate.Refusal, "independent_signing_key_changed"): gate.verify_manifest(bad)
        Path(self.contract["manifest"]["signature_path"]).write_bytes(b"invalid-signature")
        with self.assertRaisesRegex(gate.Refusal, "required_command_failed"): gate.verify_manifest(self.contract)

    def test_missing_live_dependencies_fail_and_journal_blocks_prior_green(self):
        config = write_private(self.root / "contract.json", gate.encoded(self.contract))
        session = write_private(self.root / "session.json", b"{}")
        state = self.root / "state"; state.mkdir(mode=0o700)
        command = [sys.executable, str(SCRIPT), "run", "--contract", str(config), "--session", str(session), "--state-dir", str(state)]
        run = subprocess.run(command, capture_output=True, timeout=60)
        self.assertEqual(run.returncode, 1)
        records = [json.loads(line) for line in (state / "attempts.jsonl").read_bytes().splitlines()]
        self.assertEqual([row["state"] for row in records], ["running", "failed"])
        status = subprocess.run([sys.executable, str(SCRIPT), "status", "--contract", str(config), "--state-dir", str(state)], capture_output=True, timeout=10)
        self.assertEqual(status.returncode, 1)
        self.assertNotIn(b"accepted", status.stdout)


if __name__ == "__main__":
    unittest.main()
