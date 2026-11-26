"""Tests derive commands and read private disposable files, without subprocesses."""

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "local-qualification"))

import lane_bootstrap as boot  # noqa: E402
import lane_environment as env  # noqa: E402
import lanes  # noqa: E402


class LaneBootstrapTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.parent = self.root / "reviewed-parent"
        self.interpreter = self.root / "python"
        self.interpreter.symlink_to(sys.executable)
        # Only the static canonical CLI surface is read in this fixture; no executable is run.
        for name, (relative, flags) in boot.CANONICAL_SCRIPTS.items():
            script = self.parent / "pals-scripts" / relative
            script.parent.mkdir(parents=True, exist_ok=True)
            lines = [f"p.add_argument({flag!r})" for flag in sorted(flags)]
            if name == "database":
                lines.append(
                    "def qualify_lane_postgres(runtime_directory, lane, binding_path, binding_sha256): pass"
                )
            script.write_text("\n".join(lines) + "\n")
        workspace = self.root / "verifier-context/lean-workspace"
        workspace.mkdir(parents=True)
        toolchain = "leanprover/lean4:v4.32.0-rc1"
        lake = b'{"test":"fixture-only"}\n'
        (workspace / "lean-toolchain").write_text(toolchain + "\n")
        (workspace / "lake-manifest.json").write_bytes(lake)
        self.verifier = {
            "schema_version": boot.VERIFIER_RECEIPT,
            "platform": "linux/arm64",
            "source_revision": "8" * 40,
            "built_image_id": "sha256:" + "7" * 64,
            "build_context": str(workspace.parent),
            "lean_version": toolchain,
            "lake_manifest_sha256": boot.sha(lake),
        }
        self.verifier_ref = self.write_private(
            self.root / "native-build-receipt.json", self.verifier
        )
        self.layout = {
            "schema_version": lanes.SCHEMA,
            "docker_socket": str(self.root / "docker.sock"),
            "guard": {
                "name": lanes.GUARD,
                "container_id": "6" * 64,
                "image_id": "sha256:" + "9" * 64,
                "ledger_directory": str(self.root / "budget"),
            },
            "lanes": {},
        }
        self.bindings = {}
        for index, role in enumerate(boot.ENDPOINTS, start=1):
            manifest = {
                "source_commits": {"pals-api": str(index) * 40},
                "verifier_source": {"commit": "8" * 40},
                "recipe_active_lean_version": toolchain,
                "recipe_active_lake_manifest_sha256": boot.sha(lake),
            }
            manifest_ref = self.write_private(
                self.root / f"{role}-manifest.json", manifest
            )
            runtime = self.root / f"runtime-{role}"
            runtime.mkdir(mode=0o700)
            api = self.root / f"api-{role}"
            api.mkdir()
            project = f"{lanes.PREFIX}-{role}"
            ports = boot.ENDPOINTS[role]
            self.layout["lanes"][role] = {
                "compose_project": project,
                "candidate_sha256": manifest_ref["sha256"],
                "runtime_directory": str(runtime),
                "capture_directory": str(self.root / f"capture-{role}"),
                "http_ports": {
                    key: value for key, value in ports.items() if key != "postgres"
                },
                "postgres": {
                    "name": f"{project}-postgres-1",
                    "container_id": str(index) * 64,
                    "host": "127.0.0.1",
                    "host_port": ports["postgres"],
                    "database": "pals",
                },
            }
            self.bindings[role] = {
                "schema_version": boot.SCHEMA,
                "lane": role,
                "local_env": self.write_env(runtime, role),
                "candidate_manifest": manifest_ref,
                "native_verifier_receipt": self.verifier_ref,
                "api_source": str(api),
                "interpreters": dict.fromkeys(("agent", "api"), str(self.interpreter)),
            }
        layout_ref = self.write_private(self.root / "lane-layout.json", self.layout)
        for binding in self.bindings.values():
            binding["layout"] = layout_ref

    @staticmethod
    def write_private(path, value):
        raw = value if isinstance(value, bytes) else json.dumps(value).encode()
        path.write_bytes(raw)
        path.chmod(0o600)
        return {"path": str(path), "sha256": boot.sha(raw)}

    def write_env(self, runtime, lane, **overrides):
        settings = env.lane_values(
            lane,
            {"enable_plus_coupons": lane == "primary"},
            {"PALS_ENV": "local", "PALS_ENVIRONMENT": "local"},
        )
        settings.update(overrides)
        raw = "".join(
            f"{key}={value}\n" for key, value in sorted(settings.items())
        ).encode()
        return self.write_private(runtime / "local.env", raw)

    def test_both_lanes_derive_only_canonical_closed_commands(self):
        for role, binding in self.bindings.items():
            with (
                self.subTest(role=role),
                patch(
                    "subprocess.run",
                    side_effect=AssertionError("dry derivation cannot run commands"),
                ),
            ):
                result = boot.derive(binding, self.parent)
            self.assertFalse(result["activation_authorized"])
            self.assertFalse(result["live_checks_verified"])
            self.assertEqual(
                result["expected_postgres"]["host_port"],
                boot.ENDPOINTS[role]["postgres"],
            )
            commands = {entry["step"]: entry for entry in result["commands"]}
            self.assertEqual(
                list(commands),
                ["verify_native_build", "verifier_tls", "recipe", "database"],
            )
            self.assertIn(
                f"http://127.0.0.1:{boot.ENDPOINTS[role]['localstack']}",
                commands["verifier_tls"]["argv"],
            )
            self.assertEqual(
                commands["verifier_tls"]["environment_overrides"]["AWS_ACCESS_KEY_ID"],
                "test",
            )
            self.assertEqual(
                "--enable-plus-coupons" in commands["database"]["argv"],
                role == "primary",
            )
            self.assertIn(
                binding["candidate_manifest"]["path"], commands["database"]["argv"]
            )
            self.assertEqual(result["postgres_preflight"]["arguments"]["lane"], role)
            self.assertEqual(
                result["postgres_preflight"]["call"], "qualify_lane_postgres"
            )
            runtime = Path(binding["local_env"]["path"]).parent
            self.assertEqual([item.name for item in runtime.iterdir()], ["local.env"])
            self.assertNotIn("POSTGRES_PASSWORD", json.dumps(result))

    def test_refuses_cross_lane_environment_and_manifest(self):
        primary, standby = (self.bindings[role] for role in ("primary", "standby"))
        with self.assertRaisesRegex(
            ValueError, "exact_lane_bootstrap_environment_required"
        ):
            boot.derive({**primary, "local_env": standby["local_env"]}, self.parent)
        with self.assertRaisesRegex(ValueError, "lane_bootstrap_candidate_differs"):
            boot.derive(
                {**primary, "candidate_manifest": standby["candidate_manifest"]},
                self.parent,
            )
        wrong = self.write_env(
            Path(primary["local_env"]["path"]).parent,
            "primary",
            PALS_HOST_AWS_ENDPOINT_URL=f"http://127.0.0.1:{boot.ENDPOINTS['standby']['localstack']}",
        )
        with self.assertRaisesRegex(
            ValueError, "lane_bootstrap_environment_identity_differs"
        ):
            boot.derive({**primary, "local_env": wrong}, self.parent)

    def test_cli_pins_dry_input_and_never_advertises_activation(self):
        ref = self.write_private(
            self.root / "bootstrap-binding.json", self.bindings["standby"]
        )
        with patch("sys.stdout", new_callable=io.StringIO) as output:
            self.assertEqual(
                boot.main(
                    [
                        "--binding",
                        ref["path"],
                        "--binding-sha256",
                        ref["sha256"],
                        "--source-root",
                        str(self.parent),
                    ]
                ),
                0,
            )
        result = json.loads(output.getvalue())
        self.assertEqual(result["binding_sha256"], ref["sha256"])
        self.assertFalse(result["activation_authorized"])
        self.assertFalse(result["live_checks_verified"])

    def test_refuses_changed_lean_sources_or_missing_canonical_db_entry(self):
        primary = self.bindings["primary"]
        selected = self.write_private(
            self.root / "wrong-lean.json",
            {**self.verifier, "lake_manifest_sha256": "4" * 64},
        )
        with self.assertRaisesRegex(
            ValueError, "lane_bootstrap_native_lean_files_differ"
        ):
            boot.derive({**primary, "native_verifier_receipt": selected}, self.parent)
        source = self.parent / "pals-scripts/local-qualification/bootstrap_database.py"
        source.write_text(
            source.read_text().replace(
                "--lane-binding-sha256", "--wrong-binding-sha256"
            )
        )
        with self.assertRaisesRegex(ValueError, "canonical_lane_bootstrap_cli_differs"):
            boot.derive(primary, self.parent)


if __name__ == "__main__":
    unittest.main()
