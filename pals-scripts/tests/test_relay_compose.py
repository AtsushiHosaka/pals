"""Compose rendering tests that do not start Docker or read real credentials."""

import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pals-scripts/local-qualification"))

import lane_compose  # noqa: E402
import relay_compose as relay  # noqa: E402


@unittest.skipUnless(
    importlib.util.find_spec("yaml"), "optional Compose rendering needs PyYAML"
)
class RelayComposeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.compose_root = self.root / "checkout"
        for relative in lane_compose.SOURCES:
            target = self.compose_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            source = ROOT / relative
            if source.is_file():
                shutil.copyfile(source, target)
            else:
                target.write_text("""services:
  localstack:
    volumes: [localstack-data:/var/lib/localstack]
  cognito-local:
    volumes: [cognito-local-data:/app/.cognito]
volumes:
  localstack-data:
  cognito-local-data:
""")

        def reference(path, text):
            path.parent.mkdir(parents=True, exist_ok=True)
            raw = text.encode()
            path.write_bytes(raw)
            path.chmod(0o600)
            return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()}

        self.document = {
            "schema_version": relay.SCHEMA,
            "build_sources": {
                name: reference(self.root / name, "source-only fixture\n")
                for name in relay.BUILD_SOURCES
            },
            "provider": {
                "guard_image": "sha256:" + "1" * 64,
                "lane_image": "sha256:" + "2" * 64,
                "tls_directory": str(self.root / "provider-tls"),
                "budget_ledger": reference(
                    self.root / "budget/ledger.json", '{"budget":"fixture"}'
                ),
            },
            "lanes": {
                role: {
                    "candidate_sha256": letter * 64,
                    "runtime_directory": str(self.root / role),
                    "enable_plus_coupons": False,
                    "images": {
                        image: "sha256:" + letter * 64 for image in relay.IMAGES
                    },
                }
                for role, letter in (("primary", "a"), ("standby", "b"))
            },
        }

    def test_three_projects_have_one_writer_and_separate_policy_namespaces(self):
        manifest = relay.render(self.document, self.compose_root)
        self.assertFalse(manifest["activation_authorized"])
        self.assertFalse(manifest["runtime_verified"])
        provider = lane_compose.read_yaml(manifest["provider_compose_yaml"])
        guard = provider["services"]["worker-network-guard"]
        shim = provider["services"][relay.SHIM]
        self.assertEqual(shim["network_mode"], "service:worker-network-guard")
        self.assertEqual(shim["user"], "0:65531")
        self.assertFalse(shim["volumes"][0]["read_only"])
        self.assertEqual(
            provider["volumes"]["provider-socket"]["name"], relay.SOCKET_VOLUME
        )
        self.assertIn(
            "mode=0750,uid=0,gid=65531",
            provider["volumes"]["provider-socket"]["driver_opts"]["o"],
        )
        self.assertEqual(
            guard["environment"]["PALS_BUDGET_RESUME_SHA256"],
            manifest["budget_continuity"]["sha256"],
        )
        self.assertIn("${OPENAI_API_KEY:", guard["environment"]["OPENAI_API_KEY"])
        for role, lane in manifest["lanes"].items():
            profile = lane_compose.read_yaml(lane["profile_overlay_yaml"])
            overlay = lane_compose.read_yaml(lane["relay_overlay_yaml"])
            self.assertNotIn("worker-network-guard", profile["services"])
            self.assertEqual(
                profile["services"]["api"]["environment"][
                    "PALS_CLOUD_RESTORE_MANIFEST_SHA256"
                ],
                "${PALS_LOCAL_CANDIDATE_SHA256}",
            )
            policy, forwarder = (
                overlay["services"][name] for name in (relay.POLICY, relay.RELAY)
            )
            self.assertEqual(policy["command"], [role])
            self.assertEqual(policy["cap_add"], ["NET_ADMIN"])
            self.assertEqual(forwarder["network_mode"], "service:egress-policy")
            self.assertEqual(forwarder["volumes"], [relay.socket_mount(read_only=True)])
            self.assertTrue(overlay["volumes"]["provider-socket"]["external"])
            for worker in relay.WORKERS:
                self.assertEqual(
                    profile["services"][worker]["network_mode"], "service:egress-policy"
                )
                self.assertEqual(
                    profile["services"][worker]["volumes"],
                    [
                        self.document["provider"]["tls_directory"]
                        + "/ca-bundle.pem:/run/local-provider-ca.pem:ro"
                    ],
                )
                self.assertEqual(
                    overlay["services"][worker]["environment"]["OPENAI_API_KEY"],
                    "local-provider-relay",
                )
            self.assertEqual(overlay["services"]["postgres"]["profiles"], [])
        self.assertEqual(json.dumps(manifest).count("/run/budget"), 1)
        self.assertFalse(manifest["writer_handoff_verified"])

    def test_refuses_losing_frozen_ledger_continuity_during_render(self):
        original = relay.provider_compose

        def changed(provider):
            Path(provider["budget_ledger"]["path"]).write_text("changed")
            return original(provider)

        with (
            patch.object(relay, "provider_compose", side_effect=changed),
            self.assertRaisesRegex(ValueError, "relay_compose_reference_hash_changed"),
        ):
            relay.render(self.document, self.compose_root)

    def test_health_probes_obey_the_lane_egress_policy_and_stay_sparse(self):
        """Each probe ran as a uid that lane_guard rejects, so no lane could ever become healthy."""
        manifest = relay.render(self.document, self.compose_root)
        provider = lane_compose.read_yaml(manifest["provider_compose_yaml"])
        for service in provider["services"].values():
            # Guard and shim: one python probe process every 30 s at most, once started.
            self.assertEqual(service["healthcheck"]["interval"], "30s")
        for role, lane in manifest["lanes"].items():
            overlay = lane_compose.read_yaml(lane["relay_overlay_yaml"])
            forwarder = overlay["services"][relay.RELAY]
            probe = " ".join(forwarder["healthcheck"]["test"])
            # lane_guard rejects every new connection by uid 65531, so the relay must not connect.
            self.assertNotIn("create_connection", probe)
            self.assertIn("/proc/net/tcp", probe)
            self.assertEqual(forwarder["healthcheck"]["interval"], "30s")
            reviewer = " ".join(overlay["services"]["recipe-reviewer"]["healthcheck"]["test"])
            prefix = lane_compose.BRIDGE_SUBNETS[role]["e2e"].rsplit(".", 1)[0]
            # uid 65532 may reach 127.0.0.1:443 and the lane's own .30:18119 only.
            self.assertIn(f"('{prefix}.30',18119)", reviewer)
            self.assertNotIn("127.0.0.1", reviewer)
