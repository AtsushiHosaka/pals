"""Exercise local orchestration ordering without Docker, credentials, or services."""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


class LocalRunnerMigrationTest(unittest.TestCase):
    def run_runner(self, *, fail_migration, fail_guard=False, fail_queue=False):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runner = root / "tests/e2e/run-local.sh"
            runner.parent.mkdir(parents=True)
            shutil.copyfile(Path(__file__).with_name("run-local.sh"), runner)
            fake_python = root / "pals-agent/.venv/bin/python"
            fake_python.parent.mkdir(parents=True)
            fake_python.write_text('''#!/bin/sh
case "$*" in
 *"harden-local-postgres-access.py"*)
   printf 'database-authentication-guard\\n' >> "$CALL_LOG"
   exit "$GUARD_EXIT" ;;
esac
exit 0
''')
            fake_python.chmod(0o700)
            api_python = root / "pals-api/.venv/bin/python"
            api_python.parent.mkdir(parents=True)
            shutil.copyfile(fake_python, api_python)
            api_python.chmod(0o700)
            bootstrap = root / "pals-scripts/bootstrap-local-verifier-tls.py"
            bootstrap.parent.mkdir()
            bootstrap.touch()
            binary = root / "bin"
            binary.mkdir()
            docker = binary / "docker"
            docker.write_text("""#!/bin/sh
printf '%s\\n' "$*" >> "$CALL_LOG"
case "$*" in
 *"sh /etc/localstack/init/ready.d/10-pals-resources.sh"*) exit "$QUEUE_EXIT" ;;
 *"image inspect"*) printf 'sha256:%064d\\n' 0 ;;
 *"run --rm --no-deps schema-release"*) exit "$MIGRATION_EXIT" ;;
esac
""")
            docker.chmod(0o700)
            env_file = root / ".env.local"
            env_file.write_text(
                "\n".join(
                    f"{key}=fixture"
                    for key in (
                        "OPENAI_API_KEY",
                        "PALS_DATABASE_URL",
                        "PALS_COGNITO_USER_POOL_ID",
                        "PALS_COGNITO_APP_CLIENT_ID",
                        "PALS_COGNITO_ISSUER",
                        "PALS_WORKER_SHARED_SECRET",
                    )
                )
            )
            release = root / "release.env"
            release.write_text(
                "PALS_VERIFIER_IMAGE_DIGEST=sha256:"
                + "0" * 64
                + "\n"
                + "\n".join(
                    f"{prefix}_{suffix}=fixture"
                    for prefix in (
                        "PALS_VERIFIER_SERVER_CERTIFICATE",
                        "PALS_VERIFIER_SERVER_PRIVATE_KEY",
                        "PALS_VERIFIER_CA_CERTIFICATE",
                        "PALS_RECONCILER_CLIENT_CERTIFICATE",
                        "PALS_RECONCILER_CLIENT_PRIVATE_KEY",
                    )
                    for suffix in ("SECRET_ARN", "SECRET_VERSION_ID")
                )
            )
            log = root / "calls.log"
            environment = {
                **os.environ,
                "PATH": str(binary) + os.pathsep + os.environ["PATH"],
                "CALL_LOG": str(log),
                "MIGRATION_EXIT": "7" if fail_migration else "0",
                "GUARD_EXIT": "8" if fail_guard else "0",
                "QUEUE_EXIT": "9" if fail_queue else "0",
                "PALS_E2E_RELEASE_ENV_FILE": str(release),
                "PALS_E2E_REFRESH_RELEASE": "0",
            }
            result = subprocess.run(
                ["sh", str(runner), "--up-only"],
                env=environment,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            return result, log.read_text().splitlines()

    def test_migration_runs_after_database_before_serving_with_no_dependency_start(
        self,
    ):
        result, calls = self.run_runner(fail_migration=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        database = next(
            i
            for i, call in enumerate(calls)
            if call.endswith("up -d --wait postgres localstack cognito-local")
        )
        migrations = [i for i, call in enumerate(calls)
                      if call.endswith("run --rm --no-deps schema-release")]
        serving = next(
            i for i, call in enumerate(calls) if call.endswith("up -d --wait")
        )
        self.assertEqual(len(migrations), 1)
        self.assertLess(database, migrations[0])
        guard = calls.index("database-authentication-guard")
        provision = next(i for i, call in enumerate(calls)
                         if call.endswith("sh /etc/localstack/init/ready.d/10-pals-resources.sh"))
        self.assertLess(database, provision)
        self.assertLess(provision, guard)
        self.assertLess(database, guard)
        self.assertLess(guard, migrations[0])
        self.assertLess(migrations[0], serving)
        stopped = next(i for i, call in enumerate(calls)
                       if call.endswith("stop worker assessment-worker recipe-reviewer api reconciler"))
        self.assertLess(stopped, migrations[0])

    def test_migration_failure_prevents_serving(self):
        result, calls = self.run_runner(fail_migration=True)
        self.assertEqual(result.returncode, 7)
        self.assertFalse(any(call.endswith("up -d --wait") for call in calls))

    def test_queue_provision_failure_prevents_migration_and_serving(self):
        result, calls = self.run_runner(fail_migration=False, fail_queue=True)
        self.assertEqual(result.returncode, 9)
        self.assertFalse(any("schema-release" in call for call in calls))
        self.assertFalse(any(call.endswith("up -d --wait") for call in calls))

    def test_database_guard_failure_prevents_migration_and_serving(self):
        result, calls = self.run_runner(fail_migration=False, fail_guard=True)
        self.assertEqual(result.returncode, 8)
        self.assertFalse(any("schema-release" in call for call in calls))
        self.assertFalse(any(call.endswith("up -d --wait") for call in calls))


if __name__ == "__main__":
    unittest.main()
