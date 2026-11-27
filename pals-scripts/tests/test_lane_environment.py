"""Private offline environment inputs, never Docker, database or paid calls."""

import hashlib
import io
import json
import os
import stat
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "local-qualification"))

import lane_environment as env  # noqa: E402
import test_relay_compose  # noqa: E402


class LaneEnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.fixture = test_relay_compose.RelayComposeTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.document = self.fixture.document
        self.seed = self.fixture.root / "seed.env"
        self.seed.write_text(
            "PALS_ENV=local\nPALS_ENVIRONMENT=local\nPALS_LLM_PROVIDER=openai\n"
            "PALS_LOCAL_RELEASE_CONTRACT=legacy-local-v1\nPALS_OPENAI_MODEL=gpt-5.4-mini\n"
            "PALS_OPENAI_MAX_OUTPUT_TOKENS=12000\nPALS_PROOF_WORKER_LANE=proof\n"
            "PALS_TOKEN_ACCOUNTING_ENABLED=false\nPALS_PROOF_JOBS_VISIBILITY_TIMEOUT=300\n"
            "OPENAI_API_KEY=forbidden-provider-fixture\nPALS_OPENAI_API_KEY=forbidden-second-provider-fixture\n"
            "AWS_SESSION_TOKEN=forbidden-aws-fixture\nPALS_RELEASE_ID=forbidden-release-fixture\n"
            "PALS_DATABASE_URL=postgresql://fixture:forbidden-db@elsewhere/pals\n"
        )
        self.seed.chmod(0o600)
        self.seed_sha = hashlib.sha256(self.seed.read_bytes()).hexdigest()

    def test_creates_private_exact_lane_inputs_without_copying_secrets_or_bootstrap_artifacts(
        self,
    ):
        seed = env.settings_from_seed(self.seed, self.seed_sha)
        binding = self.fixture.root / "compose-input.json"
        raw = json.dumps(self.document).encode()
        binding.write_bytes(raw)
        binding.chmod(0o600)
        with (
            patch.dict(
                os.environ, {"OPENAI_API_KEY": "extra-forbidden-process-fixture"}
            ),
            patch(
                "socket.create_connection",
                side_effect=AssertionError("offline input builder"),
            ),
            patch("sys.stdout", new_callable=io.StringIO) as output,
        ):
            self.assertEqual(
                env.main(
                    [
                        "--binding",
                        str(binding),
                        "--binding-sha256",
                        hashlib.sha256(raw).hexdigest(),
                        "--seed-env",
                        str(self.seed),
                        "--seed-sha256",
                        self.seed_sha,
                    ]
                ),
                0,
            )
        report = json.loads(output.getvalue())
        self.assertFalse(report["activation_authorized"])
        self.assertFalse(report["bootstrap_verified"])
        self.assertEqual(
            set(report["required_live_bootstrap"]),
            {"cognito", "verifier_mtls_release_env", "recipe_env", "database"},
        )
        credentials = []
        for role, ports in env.ENDPOINTS.items():
            item = report["lanes"][role]
            path = Path(item["path"])
            raw = path.read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), item["sha256"])
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode), 0o700)
            self.assertEqual(
                [entry.name for entry in path.parent.iterdir()], ["local.env"]
            )
            values = dict(line.split("=", 1) for line in raw.decode().splitlines())
            self.assertNotIn(b"forbidden", raw)
            self.assertEqual(values["AWS_ACCESS_KEY_ID"], "test")
            self.assertEqual(values["AWS_SECRET_ACCESS_KEY"], "test")
            self.assertEqual(values["OPENAI_API_KEY"], "local-provider-relay")
            self.assertNotIn("PALS_LOCAL_CANDIDATE_SHA256", values)
            self.assertNotIn("PALS_OPENAI_UPSTREAM_IP", values)
            self.assertEqual(values["PALS_OPENAI_MODEL"], "gpt-5.4-mini")
            self.assertEqual(
                values["NEXT_PUBLIC_PALS_API_BASE_URL"],
                f"http://localhost:{ports['api']}",
            )
            self.assertEqual(
                values["NEXT_PUBLIC_COGNITO_ENDPOINT"],
                f"http://localhost:{ports['cognito']}",
            )
            self.assertEqual(
                json.loads(values["PALS_GUEST_ALLOWED_ORIGINS"]),
                [f"http://localhost:{ports['web']}"],
            )
            pg_password = values["POSTGRES_PASSWORD"]
            self.assertEqual(
                values["PALS_DATABASE_URL"],
                f"postgresql://pals_qual_{role}:{pg_password}@postgres:5432/pals",
            )
            self.assertEqual(
                values["PALS_HOST_DATABASE_URL"],
                f"postgresql://pals_qual_{role}:{pg_password}@127.0.0.1:{ports['postgres']}/pals",
            )
            self.assertEqual(
                values["PALS_HOST_AWS_ENDPOINT_URL"],
                f"http://127.0.0.1:{ports['localstack']}",
            )
            self.assertIn(
                f"pals-local-{role}-proof-jobs", values["PALS_PROOF_JOBS_QUEUE_URL"]
            )
            credentials.extend(
                values[key]
                for key in (
                    "POSTGRES_PASSWORD",
                    "PALS_GUEST_HASH_KEY",
                    "PALS_WORKER_SHARED_SECRET",
                )
            )
        self.assertEqual(len(set(credentials)), 6)
        self.assertTrue(all(value not in json.dumps(report) for value in credentials))
        with self.assertRaisesRegex(
            ValueError, "local_lane_environment_already_initialized"
        ):
            env.publish(self.document, seed)

    def test_a_racing_second_writer_never_overwrites_and_rolls_back_first_file(self):
        original_link = os.link
        race = b"owned-other-process\n"
        calls = 0

        def link(source, target, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                with os.fdopen(
                    os.open(
                        target,
                        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                        0o600,
                        dir_fd=kwargs["dst_dir_fd"],
                    ),
                    "wb",
                ) as stream:
                    stream.write(race)
            return original_link(source, target, **kwargs)

        seed = env.settings_from_seed(self.seed, self.seed_sha)
        with (
            patch.object(os, "link", side_effect=link),
            self.assertRaises(FileExistsError),
        ):
            env.publish(self.document, seed)
        primary, standby = (
            Path(self.document["lanes"][role]["runtime_directory"])
            for role in ("primary", "standby")
        )
        self.assertEqual(list(primary.iterdir()), [])
        self.assertEqual(list(standby.iterdir()), [standby / "local.env"])
        self.assertEqual((standby / "local.env").read_bytes(), race)

    def test_refuses_bad_seed_or_foreign_bootstrap_files(self):
        with self.assertRaisesRegex(ValueError, "local_env_seed_hash_changed"):
            env.settings_from_seed(self.seed, "0" * 64)
        self.seed.write_text(self.seed.read_text() + "PALS_ENV=local\n")
        with self.assertRaisesRegex(ValueError, "local_env_seed_policy_differs"):
            env.settings_from_seed(
                self.seed, hashlib.sha256(self.seed.read_bytes()).hexdigest()
            )
        target = Path(self.document["lanes"]["standby"]["runtime_directory"])
        target.mkdir(mode=0o700)
        (target / "recipe.env").write_text("already owned")
        with self.assertRaisesRegex(
            ValueError, "local_lane_environment_already_initialized"
        ):
            env.publish(self.document, {})
        self.assertEqual((target / "recipe.env").read_text(), "already owned")


if __name__ == "__main__":
    unittest.main()
