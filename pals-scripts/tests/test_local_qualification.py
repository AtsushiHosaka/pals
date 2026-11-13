"""Contract/failure tests only. These never qualify a release or contact a provider."""

import ast
import importlib.util
import inspect
import io
import json
import os
import shutil
import ssl
import stat
import subprocess
import sys
import tarfile
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


proxy = load("local_budget_proxy", ROOT / "local-qualification/budget_proxy.py")
gate = load("local_qualification", ROOT / "local-qualification.py")
builder = load("local_web_build_test", ROOT / "local-web-build.py")
bootstrap = load(
    "local_bootstrap_contract", ROOT / "local-qualification/bootstrap_database.py"
)
prepare = load("local_prepare_contract", ROOT / "local-qualification-prepare.py")
rollover_tool = load(
    "local_budget_rollover_contract", ROOT / "local-qualification-budget-rollover.py"
)
sys.path.insert(0, str(ROOT / "local-qualification"))
readiness = load(
    "local_database_readiness_contract",
    ROOT / "local-qualification/database_readiness.py",
)
leftover_jobs = load(
    "local_leftover_jobs_contract", ROOT / "local-qualification/leftover_jobs.py"
)
provider_tls = load(
    "local_provider_tls_contract", ROOT / "bootstrap-local-provider-tls.py"
)
native = load("local_verifier_build_test", ROOT / "local-verifier-build.py")
archives = load("local_verifier_archives_test", ROOT / "local-verifier-archives.py")
INFRA = ROOT.parent / "pals-infra" / "scripts"
INFRA_REASON = (
    "pals-infra submodule is not initialised: the real release-plan validators were "
    "NOT exercised (the self-contained contract tests still pin key set and archives)"
)


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "ledger.json"
        self.b = proxy.Budget(self.path)

    def tearDown(self):
        self.temp.cleanup()

    def test_aggregate_reservation_stops_second_parallel_expensive_call(self):
        accepted = []

        def work():
            try:
                accepted.append(self.b.reserve("gpt-6.1-sol", 80000, 40000))
            except ValueError:
                pass

        threads = [threading.Thread(target=work) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(len(accepted), 1)
        self.assertLessEqual(self.b.held, 700000)

    def test_unknown_forward_never_releases_or_retries(self):
        i = self.b.reserve("gpt-6.1-terra", 1000, 12000)
        held = self.b.held
        self.b.uncertain(i)
        self.assertEqual(self.b.held, held)
        with self.assertRaises(ValueError):
            self.b.reserve("gpt-6-luna", 1, 1)

    def test_success_only_releases_known_unused_reserve(self):
        i = self.b.reserve("gpt-6.1-sol", 80000, 40000)
        self.b.complete(i, 1000, 100)
        self.assertEqual(self.b.actual, 3500)
        self.assertEqual(self.b.held, 3500)

    def test_unknown_model_boolean_tokens_and_excess_usage_fail_closed(self):
        for model, a, b in [
            ("unknown", 1, 1),
            ("gpt-6-luna", True, 1),
            ("gpt-6-luna", -1, 1),
        ]:
            with self.assertRaises(ValueError):
                self.b.reserve(model, a, b)
        i = self.b.reserve("gpt-6-luna", 1, 1)
        with self.assertRaises(ValueError):
            self.b.complete(i, 2, 1)
        self.assertTrue(self.b.blocked)

    def test_restart_cannot_erase_prior_paid_or_uncertain_ledger(self):
        with self.assertRaises(ValueError):
            proxy.Budget(self.path)

    def test_unpriced_priority_long_context_and_embedding_batches_block_prepaid(self):
        for tier in (None, "priority", "auto", "flex", "scale"):
            with self.assertRaises(ValueError):
                proxy.validate_paid_payload(
                    "/v1/responses",
                    {
                        "model": "gpt-6.1-terra",
                        "input": "proof",
                        "max_output_tokens": 12000,
                        "service_tier": tier,
                    },
                )
        with self.assertRaises(ValueError):
            self.b.reserve("gpt-6.1-terra", 272001, 1)
        for value in (["one", "two"], ["one"], "", {"text": "one"}):
            with self.assertRaises(ValueError):
                proxy.validate_paid_payload(
                    "/v1/embeddings",
                    {
                        "model": "text-embedding-3-small",
                        "input": value,
                        "dimensions": 384,
                    },
                )
        self.assertEqual(self.b.held, 0)
        self.assertEqual(self.b.calls, [])

    def test_explicit_hash_bound_lower_limit_resume_preserves_every_prior_charge(self):
        import hashlib

        i = self.b.reserve("gpt-6.1-terra", 1000, 1000)
        self.b.complete(i, 1000, 100)
        raw = self.path.read_bytes()
        resumed = proxy.Budget(self.path, resume_sha256=hashlib.sha256(raw).hexdigest())
        self.assertEqual(resumed.actual, 1750)
        self.assertEqual(resumed.held, 1750)
        self.assertEqual(len(resumed.calls), 1)
        with self.assertRaises(ValueError):
            proxy.Budget(self.path, resume_sha256="0" * 64)


class RuntimeTests(unittest.TestCase):
    def test_wrong_or_unhealthy_image_cannot_be_green(self):
        old = gate.command
        try:
            for image, health in [("wrong", "healthy"), ("expected", "unhealthy")]:
                gate.command = lambda _args, image=image, health=health: gate.stable(
                    [
                        {
                            "Config": {"Labels": {"codex.owner": gate.OWNER}},
                            "Image": image,
                            "State": {"Running": True, "Health": {"Status": health}},
                        }
                    ]
                )
                with self.assertRaises(gate.Refusal):
                    gate.runtime({"images": {"api": {"image_id": "expected"}}})
        finally:
            gate.command = old

    def test_unavailable_actual_compiler_blocks_before_any_browser_can_submit(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            subject = root / "subject.json"
            subject.write_text(
                json.dumps(
                    {
                        "schema_version": "pals.local-qualification-subject.v1",
                        "basis": "approved-local-real-db-lean-model",
                        "fixture": {
                            "paid_submissions": 1,
                            "maximum_approved_usd": 1,
                            "output_language": "en",
                        },
                        "local_profile": {},
                    }
                )
            )
            argv = [
                "gate",
                "--subject",
                str(subject),
                "--state-dir",
                str(root / "capture"),
                "--web-root",
                str(root),
                "--database-env",
                str(root / "private.env"),
            ]
            with (
                patch.object(sys, "argv", argv),
                patch.object(gate, "require_modules"),
                patch.object(gate, "provider_tls_status", return_value={}),
                patch.object(gate, "web_provenance", return_value={}),
                patch.object(gate, "verifier_provenance", return_value={}),
                patch.object(gate, "budget_status", return_value={}),
                patch.object(gate, "database_readiness", return_value={}),
                patch.object(gate, "runtime", return_value={}),
                patch.object(
                    gate,
                    "compiler_canary",
                    side_effect=gate.Refusal("actual_http_compiler_canary_unavailable"),
                ),
                patch.object(gate.subprocess, "Popen") as browser,
            ):
                self.assertEqual(gate.main(), 1)
                browser.assert_not_called()
            self.assertEqual(
                json.loads((root / "capture/latest.json").read_text())["state"],
                "failed",
            )
            self.assertFalse((root / "capture/submission.json").exists())


class LocalSetupBoundaryTests(unittest.TestCase):
    def test_private_file_dsn_rejects_query_fragment_remote_and_keyword_forms(self):
        with tempfile.TemporaryDirectory() as d:
            file = Path(d) / "local.env"
            valid = "postgresql://local_user:" + ("a" * 64) + "@127.0.0.1:55432/pals"
            file.write_text("PALS_HOST_DATABASE_URL=" + valid + "\n")
            file.chmod(0o600)
            self.assertEqual(
                bootstrap.validate_local_dsn(
                    gate.private_env(file)["PALS_HOST_DATABASE_URL"]
                ).hostname,
                "127.0.0.1",
            )
            for bad in (
                valid + "?host=remote.invalid",
                valid + "#host=remote.invalid",
                valid.replace("127.0.0.1", "remote.invalid"),
                valid.replace("postgresql:", "http:"),
                "host=remote.invalid dbname=pals",
            ):
                file.write_text("PALS_HOST_DATABASE_URL=" + bad + "\n")
                with self.assertRaises(ValueError):
                    bootstrap.validate_local_dsn(
                        gate.private_env(file)["PALS_HOST_DATABASE_URL"]
                    )
            selector = (
                "postgresql://pals_local_recipe_selector:"
                + ("b" * 64)
                + "@postgres:5432/pals"
            )
            self.assertEqual(
                bootstrap.validate_local_dsn(
                    bootstrap.runtime_login_url(selector)
                ).port,
                55432,
            )
            with self.assertRaises(ValueError):
                bootstrap.runtime_login_url(selector + "?host=remote.invalid")

    def test_actual_role_label_file_rejects_one_foreign_or_unknown_role(self):
        with tempfile.TemporaryDirectory() as d:
            file = Path(d) / "roles.json"
            owned = {
                "codex.owner": gate.OWNER,
                "com.docker.compose.project": prepare.PROJECT,
                "com.docker.compose.service": "api",
            }
            file.write_text(json.dumps([owned]))
            prepare.validate_existing_role_owners(json.loads(file.read_text()))
            for changed in (
                {"codex.owner": "foreign"},
                {"com.docker.compose.service": "unexpected"},
                {"com.docker.compose.project": "foreign"},
            ):
                file.write_text(json.dumps([owned, {**owned, **changed}]))
                with self.assertRaises(prepare.gate.Refusal):
                    prepare.validate_existing_role_owners(json.loads(file.read_text()))

    def test_missing_database_rowlock_privilege_blocks_before_browser(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            subject = root / "subject.json"
            subject.write_text(
                json.dumps(
                    {
                        "schema_version": "pals.local-qualification-subject.v1",
                        "basis": "approved-local-real-db-lean-model",
                        "fixture": {
                            "paid_submissions": 1,
                            "maximum_approved_usd": 1,
                            "output_language": "en",
                        },
                        "local_profile": {},
                    }
                )
            )
            argv = [
                "gate",
                "--subject",
                str(subject),
                "--state-dir",
                str(root / "capture"),
                "--web-root",
                str(root),
                "--database-env",
                str(root / "private.env"),
            ]
            with (
                patch.object(sys, "argv", argv),
                patch.object(gate, "require_modules"),
                patch.object(gate, "provider_tls_status", return_value={}),
                patch.object(gate, "web_provenance", return_value={}),
                patch.object(gate, "verifier_provenance", return_value={}),
                patch.object(gate, "budget_status", return_value={}),
                patch.object(gate, "runtime", return_value={}),
                patch.object(
                    gate,
                    "database_readiness",
                    side_effect=gate.Refusal("actual_local_rowlock_privilege_missing"),
                ),
                patch.object(gate.subprocess, "Popen") as browser,
            ):
                self.assertEqual(gate.main(), 1)
                browser.assert_not_called()
            self.assertEqual(
                json.loads((root / "capture/latest.json").read_text())["state"],
                "failed",
            )


class ProvenanceTests(unittest.TestCase):
    def test_replaced_source_bytes_cannot_match_a_real_archive(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            archive = root / "source.tar"
            context = root / "context"
            context.mkdir()
            with tarfile.open(archive, "w") as t:
                member = tarfile.TarInfo("Dockerfile")
                member.size = 8
                t.addfile(member, io.BytesIO(b"FROM old"))
            (context / "Dockerfile").write_bytes(b"FROM new")
            with self.assertRaises(ValueError):
                builder.context_tree(archive, context)

    def test_actual_build_args_or_output_must_match_not_claimed_receipt_flags(self):
        with tempfile.TemporaryDirectory() as d:
            context = Path(d)
            record = {
                "Status": "completed",
                "Context": str(context),
                "Dockerfile": "Dockerfile",
                "Platform": ["linux/arm64"],
                "BuildArgs": [
                    {"Name": k, "Value": v} for k, v in builder.LOCAL_ARGS.items()
                ],
                "Labels": [
                    {"Name": "org.opencontainers.image.revision", "Value": "a" * 40}
                ],
                "Attachments": [
                    {
                        "Digest": "sha256:" + "b" * 64,
                        "Type": "application/vnd.oci.image.manifest.v1+json",
                    }
                ],
            }
            old = builder.run
            try:
                record["BuildArgs"][0]["Value"] = "https://unapproved.invalid"
                builder.run = lambda _args: json.dumps(record).encode()
                with self.assertRaises(ValueError):
                    builder.observe_build(
                        "real-record", context, "a" * 40, "sha256:" + "b" * 64
                    )
                record["BuildArgs"] = [
                    {"Name": k, "Value": v} for k, v in builder.LOCAL_ARGS.items()
                ]
                with self.assertRaises(ValueError):
                    builder.observe_build(
                        "real-record", context, "a" * 40, "sha256:" + "c" * 64
                    )
            finally:
                builder.run = old


SUBJECT = {
    "schema_version": "pals.local-qualification-subject.v1",
    "basis": "approved-local-real-db-lean-model",
    "fixture": {
        "paid_submissions": 1,
        "maximum_approved_usd": 1,
        "output_language": "en",
    },
    "local_profile": {},
}


def gate_argv(root):
    (root / "subject.json").write_text(json.dumps(SUBJECT))
    return [
        "gate",
        "--subject",
        str(root / "subject.json"),
        "--state-dir",
        str(root / "capture"),
        "--web-root",
        str(root),
        "--database-env",
        str(root / "private.env"),
    ]


class DiagnosabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.previous = dict(gate._DIAGNOSTICS)
        self.secrets = set(gate._SECRET_VALUES)

    def tearDown(self):
        gate._DIAGNOSTICS.update(self.previous)
        gate._SECRET_VALUES.clear()
        gate._SECRET_VALUES.update(self.secrets)
        self.temp.cleanup()

    def failing(self, stderr, argument="--label=harmless"):
        program = "import sys;sys.stderr.write(sys.stdin.read());sys.exit(7)"
        script = self.root / "child-tool.py"
        script.write_text(program)
        old = gate.subprocess.run

        def run(args, **options):
            return old(args, input=stderr, **options)

        with patch.object(gate.subprocess, "run", run):
            with self.assertRaises(gate.Refusal) as caught:
                gate.command([sys.executable, str(script), argument])
        return caught.exception

    def test_failed_child_keeps_closed_code_and_names_private_bounded_file(self):
        gate.set_diagnostic_directory(self.root / "diagnostics")
        error = self.failing("ModuleNotFoundError: No module named 'absent'\n")
        self.assertEqual(str(error), "local_dependency_command_failed")
        file = Path(error.detail["diagnostic_file"])
        self.assertEqual(file.parent, self.root / "diagnostics")
        self.assertEqual(stat.S_IMODE(file.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(file.parent.stat().st_mode), 0o700)
        saved = json.loads(file.read_text())
        self.assertEqual(saved["returncode"], 7)
        self.assertIn("No module named 'absent'", saved["stderr_tail_redacted"])
        self.assertEqual(
            saved["failed_command"],
            Path(sys.executable).name + " child-tool.py",
        )
        self.assertEqual(error.detail["failed_command"], saved["failed_command"])
        lines = "".join("line %06d\n" % i for i in range(gate.DIAGNOSTIC_LIMIT))
        long = self.failing(lines + "END")
        saved = json.loads(Path(long.detail["diagnostic_file"]).read_text())
        self.assertTrue(saved["stderr_truncated"])
        tail = saved["stderr_tail_redacted"]
        self.assertLessEqual(len(tail), gate.DIAGNOSTIC_LIMIT)
        self.assertGreater(len(tail), gate.DIAGNOSTIC_LIMIT - 20)
        self.assertTrue(tail.endswith("END"))
        self.assertTrue(tail.startswith("line "))

    def test_secret_or_key_block_cut_by_the_size_limit_never_leaves_a_remainder(self):
        gate.set_diagnostic_directory(self.root / "diagnostics")
        limit = gate.DIAGNOSTIC_LIMIT
        # Neither value is caught by a generic rule once cut: only redacting BEFORE the
        # tail is taken (and dropping the partial first line) keeps the remainder out.
        registered = "R!" + "s!" * 30 + "Z!"
        gate.register_secrets({"PALS_WORKER_SHARED_SECRET": registered})
        body = "".join(chr(65 + i % 26) * 30 + "\n" for i in range(40))
        pem = (
            "-----BEGIN "
            + "PRIVATE KEY-----\n"
            + body
            + "-----END "
            + "PRIVATE KEY-----\n"
        )
        for secret, markers in (
            (registered + "\n", ("s!s!s!s!", "Z!")),
            (pem, tuple(chr(65 + i) * 30 for i in range(26))),
        ):
            # Every offset puts the 16 KiB boundary at a different place inside the secret.
            for inside in range(1, len(secret), max(1, len(secret) // 23)):
                filler = "f" * 30 + "\n"
                after = (filler * (limit // len(filler) + 2))[: limit - inside]
                stderr = "before\n" + secret + after
                self.assertGreater(len(stderr), limit)
                error = self.failing(stderr)
                raw = Path(error.detail["diagnostic_file"]).read_text()
                for marker in markers:
                    self.assertNotIn(marker, raw, (inside, marker[:8]))
        # The same holds for the bounded input scan in front of the redaction.
        with (
            patch.object(gate, "DIAGNOSTIC_SCAN_LIMIT", 2000),
            patch.object(gate, "DIAGNOSTIC_LIMIT", 4000),
        ):
            for inside in range(1, len(registered), 7):
                after = ("g" * 30 + "\n") * 80
                stderr = "before\n" + registered + "\n" + after[: 1999 - inside]
                error = self.failing(stderr)
                raw = Path(error.detail["diagnostic_file"]).read_text()
                self.assertNotIn("s!s!s!s!", raw, inside)
                self.assertNotIn(registered[-20:], raw, inside)

    def test_tail_never_starts_inside_a_line(self):
        self.assertEqual(gate._tail_from_line_start("abc", 10), ("abc", False))
        self.assertEqual(
            gate._tail_from_line_start("aaa\nbbb\nccc", 7), ("bbb\nccc", True)
        )
        self.assertEqual(gate._tail_from_line_start("aaa\nbbb\nccc", 5), ("ccc", True))
        self.assertEqual(gate._tail_from_line_start("aaaaaaaaaaaa", 5), ("", True))

    def test_quoted_pairs_uri_passwords_short_values_and_process_environment(self):
        gate.set_diagnostic_directory(self.root / "diagnostics")
        slash = "pa/ss:w@rd" + "x" * 6
        short = "s3cr"
        env_only = "envonly" + "7" * 9
        dsn_password = "d" * 5 + "/q"
        env_file = self.root / "local.env"
        env_file.write_text(
            "POSTGRES_PASSWORD="
            + short
            + "\nPALS_HOST_DATABASE_URL=postgresql://local_user:"
            + dsn_password
            + "@127.0.0.1:55432/pals\nPALS_ENV=local\n"
        )
        env_file.chmod(0o600)
        gate.register_private_env(env_file)
        gate.register_private_env(self.root / "absent.env")
        cases = {
            "json": '{"password": "' + "j" * 9 + ' with space", "user": "kept-user"}',
            "repr": "{'api_key': '" + "p" * 9 + "', 'port': 5432}",
            "upper": 'PALS_GUEST_HASH_KEY="' + "h" * 12 + '"',
            "colon": "client_secret : " + "c" * 10,
            "uri": "connect postgresql://user:"
            + slash
            + "@db.internal:5432/pals failed",
            "short": "role password was " + short + " today",
            "dsn": "could not use " + dsn_password + " for login",
            "environment": "upstream answered " + env_only,
            "basic": "Authorization: Basic " + "Zm9v" * 3,
        }
        with patch.dict(os.environ, {"UPSTREAM_ACCESS_TOKEN": env_only}):
            error = self.failing("\n".join(cases.values()) + "\nplain kept line\n")
        raw = json.loads(Path(error.detail["diagnostic_file"]).read_text())[
            "stderr_tail_redacted"
        ]
        for secret in (
            "j" * 9,
            "with space",
            "p" * 9,
            "h" * 12,
            "c" * 10,
            slash,
            "pa/ss",
            "w@rd",
            short,
            dsn_password,
            env_only,
            "Zm9v" * 3,
        ):
            self.assertNotIn(secret, raw, secret[:6])
        self.assertIn("plain kept line", raw)
        self.assertIn("db.internal:5432/pals failed", raw)
        self.assertIn("'port': 5432", raw)
        # Ordinary short settings stay readable; only secret-named short values are hidden.
        self.assertNotIn("local", gate._SECRET_VALUES)
        self.assertIn(short, gate._SECRET_VALUES)

    def test_environment_values_keys_tokens_and_arguments_never_reach_the_file(self):
        gate.set_diagnostic_directory(self.root / "diagnostics")
        registered = "r" * 40
        from_environment = "e" * 40
        password = "p" * 24
        token = "sk-" + "t" * 32
        account = "1" * 12
        argument = "--connection=" + "a" * 30
        env_file = self.root / "local.env"
        env_file.write_text("PALS_WORKER_SHARED_SECRET=" + registered + "\n")
        env_file.chmod(0o600)
        gate.private_env(env_file)
        pem = (
            "-----BEGIN " + "PRIVATE KEY-----\n" + "k" * 64 + "\n-----END "
            "PRIVATE KEY-----"
        )
        stderr = "\n".join(
            [
                "worker secret " + registered,
                "upstream " + from_environment,
                "dsn postgresql://local_user:" + password + "@127.0.0.1:55432/pals",
                "Authorization: Bearer " + "b" * 40,
                "key " + token,
                "registry " + account + ".example.invalid",
                "password=" + "q" * 20,
                pem,
                "kept line",
            ]
        )
        with patch.dict(os.environ, {"EXAMPLE_API_KEY": from_environment}):
            error = self.failing(stderr, argument)
        raw = Path(error.detail["diagnostic_file"]).read_text()
        for secret in (
            registered,
            from_environment,
            password,
            token,
            "b" * 40,
            account,
            "q" * 20,
            "k" * 64,
            "a" * 30,
        ):
            self.assertNotIn(secret, raw)
        self.assertIn("kept line", raw)
        self.assertNotIn("a" * 30, json.dumps(error.detail))

    def test_command_name_is_program_and_subcommand_only(self):
        for args, expected in (
            (["docker", "exec", "pals-reliability-local-reconciler-1"], "docker exec"),
            (
                ["docker", "compose", "--env-file", "/private/local.env"],
                "docker compose",
            ),
            (
                [
                    "/venv/bin/python",
                    "/src/bootstrap_database.py",
                    "--runtime-dir",
                    "/r",
                ],
                "python bootstrap_database.py",
            ),
            (["git", "-C", "/private/source", "rev-parse"], "git"),
            (["/venv/bin/python", "-c", "print('inline program')"], "python"),
        ):
            self.assertEqual(gate.command_name(args), expected)

    def test_without_a_private_directory_nothing_is_written(self):
        gate._DIAGNOSTICS["directory"] = None
        error = self.failing("anything")
        self.assertEqual(set(error.detail), {"failed_command"})
        self.assertFalse((self.root / "diagnostics").exists())

    def test_capture_record_names_the_diagnostic_of_its_failed_dependency(self):
        detail = {"failed_command": "docker buildx", "diagnostic_file": "/private/x"}
        with (
            patch.object(sys, "argv", gate_argv(self.root)),
            patch.object(gate, "require_modules"),
            patch.object(
                gate,
                "web_provenance",
                side_effect=gate.Refusal("local_dependency_command_failed", detail),
            ),
            patch.object(gate.subprocess, "Popen") as browser,
        ):
            self.assertEqual(gate.main(), 1)
            browser.assert_not_called()
        record = json.loads((self.root / "capture/latest.json").read_text())
        self.assertEqual(record["code"], "local_dependency_command_failed")
        self.assertEqual(record["diagnostic"], detail)
        self.assertEqual(
            stat.S_IMODE((self.root / "capture/diagnostics").stat().st_mode), 0o700
        )


class InterpreterTests(unittest.TestCase):
    def test_missing_driver_is_named_before_any_state_or_dependency(self):
        with self.assertRaises(gate.Refusal) as caught:
            gate.require_modules(("json", "pals_absent_driver_module"))
        self.assertEqual(
            str(caught.exception),
            "release_python_missing_module:pals_absent_driver_module",
        )
        gate.require_modules(("json", "hashlib"))
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with (
                patch.object(sys, "argv", gate_argv(root)),
                patch.object(gate, "REQUIRED_MODULES", ("pals_absent_driver_module",)),
                patch.object(
                    gate,
                    "require_modules",
                    lambda: gate.need(False, "release_python_missing_module:psycopg"),
                ),
                patch.object(gate, "web_provenance") as first_dependency,
            ):
                with self.assertRaises(gate.Refusal):
                    gate.main()
                first_dependency.assert_not_called()
            self.assertFalse((root / "capture").exists())

    def prepare_main(self, root):
        """Run the real preparation entry point against a recorded fake Docker."""
        runtime = root / "runtime"
        runtime.mkdir(mode=0o700)
        (runtime / "local.env").write_text("PALS_ENV=local\nPALS_ENVIRONMENT=local\n")
        (runtime / "local.env").chmod(0o600)
        commands = []

        def run(args, timeout=45):
            args = [str(x) for x in args]
            commands.append(args)
            if args[:3] == ["docker", "context", "inspect"]:
                return "unix:///var/run/docker.sock\n"
            if args[:2] == ["docker", "inspect"]:
                return json.dumps({"codex.owner": prepare.gate.OWNER})
            return ""

        argv = ["prepare"]
        for name in (
            "runtime-dir",
            "compose-root",
            "api-source",
            "base-subject",
            "web-build-receipt",
            "verifier-build-receipt",
            "api-python",
            "agent-python",
        ):
            argv += [
                "--" + name,
                str(runtime if name == "runtime-dir" else root / name),
            ]
        previous = dict(prepare.gate._DIAGNOSTICS)
        try:
            with (
                patch.object(sys, "argv", argv),
                patch.object(prepare, "run", run),
                patch.object(prepare, "require_child_modules", lambda *a, **k: None),
                patch.object(prepare.gate, "require_modules", lambda *a, **k: None),
            ):
                with self.assertRaises(prepare.gate.Refusal) as caught:
                    prepare.main()
        finally:
            prepare.gate._DIAGNOSTICS.update(previous)
        return str(caught.exception), commands

    def test_preparation_refuses_a_missing_driver_before_any_command(self):
        def missing(*_a, **_k):
            raise prepare.gate.Refusal("release_python_missing_module:psycopg")

        with tempfile.TemporaryDirectory() as d:
            previous = prepare.gate.require_modules
            prepare.gate.require_modules = missing
            try:
                with (
                    patch.object(
                        sys,
                        "argv",
                        ["prepare"]
                        + [
                            x
                            for name in (
                                "runtime-dir",
                                "compose-root",
                                "api-source",
                                "base-subject",
                                "web-build-receipt",
                                "verifier-build-receipt",
                                "api-python",
                                "agent-python",
                            )
                            for x in ("--" + name, d)
                        ],
                    ),
                    patch.object(prepare, "run") as run,
                ):
                    with self.assertRaises(prepare.gate.Refusal) as caught:
                        prepare.main()
                    run.assert_not_called()
            finally:
                prepare.gate.require_modules = previous
        self.assertEqual(str(caught.exception), "release_python_missing_module:psycopg")

    def test_preparation_refuses_dead_provider_tls_before_it_stops_anything(self):
        with tempfile.TemporaryDirectory() as d:
            code, commands = self.prepare_main(Path(d))
        # No material exists in the fake runtime: the real inspection refuses.
        self.assertEqual(code, "local_provider_tls_missing_or_invalid")
        self.assertTrue(commands)
        for command in commands:
            for word in ("stop", "up", "tag", "build", "buildx"):
                self.assertNotIn(word, command, command[:4])
        for state, expected in (
            ("expired", "local_provider_tls_expired"),
            (
                "expires_within_window",
                "local_provider_tls_expires_before_capture_window",
            ),
        ):
            with tempfile.TemporaryDirectory() as d:
                with patch.object(
                    prepare.provider_tls,
                    "inspect",
                    lambda *a, state=state, **k: {"state": state},
                ):
                    code, commands = self.prepare_main(Path(d))
            self.assertEqual(code, expected)
            self.assertFalse(any("stop" in c for c in commands))

    def test_child_interpreters_are_named_with_their_missing_module(self):
        calls = []

        def run(args):
            calls.append(args)
            return "psycopg_pool,other\n"

        with self.assertRaises(prepare.gate.Refusal) as caught:
            prepare.require_child_modules(
                "/venv/bin/python",
                ("psycopg", "psycopg_pool", "other"),
                "api_python",
                run_=run,
            )
        self.assertEqual(
            str(caught.exception), "api_python_missing_module:psycopg_pool"
        )
        self.assertEqual(calls[0][0], "/venv/bin/python")
        self.assertEqual(calls[0][3:], ["psycopg", "psycopg_pool", "other"])
        prepare.require_child_modules(
            "python", ("json",), "agent_python", run_=lambda _a: "\n"
        )
        prepare.require_child_modules(sys.executable, ("json",), "agent_python")
        with self.assertRaises(prepare.gate.Refusal) as caught:
            prepare.require_child_modules(
                sys.executable, ("pals_absent_driver_module",), "agent_python"
            )
        self.assertEqual(
            str(caught.exception),
            "agent_python_missing_module:pals_absent_driver_module",
        )
        with self.assertRaises(prepare.gate.Refusal) as caught:
            prepare.require_child_modules(
                "/nonexistent/python", ("json",), "api_python"
            )
        self.assertEqual(str(caught.exception), "api_python_unavailable")


@unittest.skipUnless(
    shutil.which("openssl"), "openssl CLI is required to issue material"
)
class ProviderTlsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name) / "provider-tls"

    def tearDown(self):
        self.temp.cleanup()

    def issue_expired(self, directory):
        from datetime import datetime, timedelta, timezone

        # Issuance refuses to install material that fails its own handshake, so the
        # self-check is bypassed here only to obtain genuinely expired local material.
        with patch.object(provider_tls, "inspect", return_value={"state": "valid"}):
            provider_tls.issue(
                directory,
                lifetime_hours=1,
                now=datetime.now(timezone.utc) - timedelta(days=2),
            )

    def test_issue_writes_private_short_lived_name_constrained_material(self):
        result = provider_tls.issue(self.directory, lifetime_hours=2)
        self.assertEqual(result["state"], "valid")
        self.assertTrue(7000 < result["remaining_seconds"] <= 7200)
        self.assertEqual(result["ca_bundle_certificates"], 1)
        self.assertEqual(stat.S_IMODE(self.directory.stat().st_mode), 0o700)
        self.assertEqual(
            sorted(x.name for x in self.directory.iterdir()), sorted(provider_tls.FILES)
        )
        modes = {
            x.name: stat.S_IMODE(x.stat().st_mode) for x in self.directory.iterdir()
        }
        self.assertEqual(
            modes,
            {"ca-bundle.pem": 0o644, "server.pem": 0o600, "server-key.pem": 0o600},
        )
        self.assertNotIn(
            b"PRIVATE KEY", (self.directory / "ca-bundle.pem").read_bytes()
        )
        self.assertNotIn(b"PRIVATE KEY", (self.directory / "server.pem").read_bytes())
        self.assertNotIn("PRIVATE", json.dumps(result))
        peer, _ = provider_tls.handshake(self.directory)
        self.assertEqual(peer["subjectAltName"], (("DNS", provider_tls.HOST),))
        # The local CA is constrained to the proxied host: trust cannot be widened.
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.load_verify_locations(cafile=self.directory / "ca-bundle.pem")
        self.assertEqual(len(context.get_ca_certs()), 1)
        again = provider_tls.issue(self.directory, lifetime_hours=2)
        self.assertNotEqual(
            again["server_certificate_sha256"], result["server_certificate_sha256"]
        )
        self.assertNotEqual(again["ca_bundle_sha256"], result["ca_bundle_sha256"])

    def test_window_expiry_and_real_expired_handshake_are_distinguished(self):
        import time

        provider_tls.issue(self.directory, lifetime_hours=1)
        self.assertEqual(
            provider_tls.inspect(self.directory, minimum_remaining_seconds=3500)[
                "state"
            ],
            "valid",
        )
        self.assertEqual(
            provider_tls.inspect(
                self.directory,
                minimum_remaining_seconds=prepare.PROVIDER_TLS_MINIMUM_SECONDS,
            )["state"],
            "expires_within_window",
        )
        self.assertEqual(
            provider_tls.inspect(
                self.directory, minimum_remaining_seconds=0, now=time.time() + 7200
            )["state"],
            "expired",
        )
        expired = Path(self.temp.name) / "expired"
        self.issue_expired(expired)
        self.assertEqual(
            provider_tls.inspect(expired, minimum_remaining_seconds=0),
            {
                "scope": "local_budget_proxy_transport_only",
                "host": provider_tls.HOST,
                "state": "expired",
            },
        )

    def test_failed_or_unsafe_issuance_leaves_previous_material_untouched(self):
        from datetime import datetime, timedelta, timezone

        first = provider_tls.issue(self.directory, lifetime_hours=2)
        before = {x.name: x.read_bytes() for x in self.directory.iterdir()}
        for options, code in (
            ({"lifetime_hours": 25}, "local_provider_tls_short_lifetime_required"),
            ({"lifetime_hours": 0}, "local_provider_tls_short_lifetime_required"),
            ({"openssl": "false"}, "local_provider_tls_issuer_tool_failed"),
            (
                {"now": datetime.now(timezone.utc) - timedelta(days=2)},
                "local_provider_tls_issued_material_invalid",
            ),
        ):
            with self.assertRaises(ValueError) as caught:
                provider_tls.issue(self.directory, **options)
            self.assertEqual(str(caught.exception), code)
        self.assertEqual(
            {x.name: x.read_bytes() for x in self.directory.iterdir()}, before
        )
        self.assertEqual(
            provider_tls.inspect(self.directory, minimum_remaining_seconds=0)[
                "server_certificate_sha256"
            ],
            first["server_certificate_sha256"],
        )
        open_directory = Path(self.temp.name) / "open"
        open_directory.mkdir(mode=0o755)
        with self.assertRaises(ValueError):
            provider_tls.issue(open_directory)

    def test_foreign_ca_mismatched_key_and_readable_key_are_invalid(self):
        provider_tls.issue(self.directory, lifetime_hours=1)
        other = Path(self.temp.name) / "other"
        provider_tls.issue(other, lifetime_hours=1)
        mixed = Path(self.temp.name) / "mixed"
        for replaced in provider_tls.FILES:
            shutil.rmtree(mixed, ignore_errors=True)
            shutil.copytree(self.directory, mixed)
            shutil.copy(other / replaced, mixed / replaced)
            self.assertEqual(
                provider_tls.inspect(mixed, minimum_remaining_seconds=0)["state"],
                "invalid",
                replaced,
            )
        (self.directory / "server-key.pem").chmod(0o644)
        self.assertEqual(
            provider_tls.inspect(self.directory, minimum_remaining_seconds=0)["state"],
            "invalid",
        )
        self.assertEqual(
            provider_tls.inspect(
                Path(self.temp.name) / "absent", minimum_remaining_seconds=0
            )["state"],
            "invalid",
        )

    def test_preparation_refuses_expired_or_short_material_with_closed_codes(self):
        self.assertGreaterEqual(prepare.PROVIDER_TLS_MINIMUM_SECONDS, 3600 + 600)
        for state, code in (
            ("expired", "local_provider_tls_expired"),
            (
                "expires_within_window",
                "local_provider_tls_expires_before_capture_window",
            ),
            ("invalid", "local_provider_tls_missing_or_invalid"),
            (None, "local_provider_tls_missing_or_invalid"),
        ):
            seen = []

            def observed(directory, *, minimum_remaining_seconds, state=state):
                seen.append(minimum_remaining_seconds)
                return {"state": state}

            with self.assertRaises(prepare.gate.Refusal) as caught:
                prepare.require_provider_tls(self.directory, inspect=observed)
            self.assertEqual(str(caught.exception), code)
            self.assertEqual(seen, [prepare.PROVIDER_TLS_MINIMUM_SECONDS])
        expired = Path(self.temp.name) / "expired"
        self.issue_expired(expired)
        with self.assertRaises(prepare.gate.Refusal) as caught:
            prepare.require_provider_tls(expired)
        self.assertEqual(str(caught.exception), "local_provider_tls_expired")
        provider_tls.issue(self.directory, lifetime_hours=1)
        with self.assertRaises(prepare.gate.Refusal) as caught:
            prepare.require_provider_tls(self.directory)
        self.assertEqual(
            str(caught.exception), "local_provider_tls_expires_before_capture_window"
        )
        provider_tls.issue(self.directory, lifetime_hours=12)
        self.assertEqual(prepare.require_provider_tls(self.directory)["state"], "valid")

    def test_preparation_only_checks_and_covers_its_own_duration(self):
        self.assertNotIn("provider_tls.issue", inspect.getsource(prepare))
        self.assertEqual(prepare.PROVIDER_TLS_SERVED_SECONDS, 3600 + 900)
        # The first check must cover every bounded step up to the served check, so
        # marginal material is refused before the stack is stopped and rebuilt.
        self.assertGreaterEqual(
            prepare.PREPARATION_BOUND_SECONDS, 600 + 120 + 120 + 60 + 60 + 55 + 45
        )
        self.assertEqual(
            prepare.PROVIDER_TLS_MINIMUM_SECONDS,
            prepare.PROVIDER_TLS_SERVED_SECONDS + prepare.PREPARATION_BOUND_SECONDS,
        )
        self.assertGreater(
            provider_tls.DEFAULT_LIFETIME_HOURS * 3600,
            prepare.PROVIDER_TLS_MINIMUM_SECONDS,
        )

    def test_replacement_never_follows_or_reuses_a_stale_temporary_file(self):
        provider_tls.issue(self.directory, lifetime_hours=1)
        outside = Path(self.temp.name) / "outside-target"
        outside.write_text("untouched")
        for name in provider_tls.FILES:
            (self.directory / ("." + name + ".new")).symlink_to(outside)
        result = provider_tls.issue(self.directory, lifetime_hours=1)
        self.assertEqual(result["state"], "valid")
        self.assertEqual(outside.read_text(), "untouched")
        self.assertEqual(
            sorted(x.name for x in self.directory.iterdir()), sorted(provider_tls.FILES)
        )
        for name in provider_tls.FILES:
            self.assertFalse((self.directory / name).is_symlink())
        source = inspect.getsource(provider_tls.write)
        self.assertIn("O_EXCL", source)
        self.assertIn("O_NOFOLLOW", source)


class ServedProviderTlsTests(unittest.TestCase):
    SHA = "a" * 64

    def subject(self, sha=SHA):
        return {"guard": {"provider_tls": {"server_certificate_sha256": sha}}}

    def status(self, answer, subject=None):
        old = gate.command
        try:
            gate.command = lambda _args, timeout=0: json.dumps(answer)
            return gate.provider_tls_status(subject or self.subject())
        finally:
            gate.command = old

    def test_running_proxy_certificate_must_be_trusted_bound_and_outlive_capture(self):
        good = {"state": "trusted", "sha256": self.SHA, "remaining_seconds": 5000}
        self.assertEqual(self.status(good)["remaining_seconds"], 5000)
        for answer, code in (
            ({"state": "expired"}, "local_provider_tls_expired"),
            ({"state": "untrusted"}, "local_provider_tls_unavailable_or_untrusted"),
            ({"state": "unavailable"}, "local_provider_tls_unavailable_or_untrusted"),
            ({}, "local_provider_tls_unavailable_or_untrusted"),
            ({**good, "sha256": "b" * 64}, "local_provider_tls_differs_from_subject"),
            (
                {**good, "remaining_seconds": gate.PROVIDER_TLS_CAPTURE_SECONDS - 1},
                "local_provider_tls_expires_before_capture_window",
            ),
            (
                {**good, "remaining_seconds": True},
                "local_provider_tls_expires_before_capture_window",
            ),
        ):
            with self.assertRaises(gate.Refusal) as caught:
                self.status(answer)
            self.assertEqual(str(caught.exception), code)
        for subject in ({"guard": {}}, self.subject("not-a-digest")):
            with self.assertRaises(gate.Refusal) as caught:
                self.status(good, subject)
            self.assertEqual(
                str(caught.exception), "local_provider_tls_subject_binding_required"
            )
        self.assertGreater(gate.PROVIDER_TLS_CAPTURE_SECONDS, 620)

    def test_probe_only_handshakes_with_the_task_ca_inside_the_guard(self):
        seen = []
        old = gate.command
        try:
            gate.command = lambda args, timeout=0: (
                seen.append(args)
                or json.dumps(
                    {"state": "trusted", "sha256": self.SHA, "remaining_seconds": 9000}
                )
            )
            gate.provider_tls_status(self.subject())
        finally:
            gate.command = old
        self.assertEqual(
            seen[0][:3],
            ["docker", "exec", "pals-reliability-local-worker-network-guard-1"],
        )
        program = seen[0][-1]
        compile(program, "probe", "exec")
        self.assertIn("cafile='/run/provider/ca-bundle.pem'", program)
        self.assertIn("('127.0.0.1',443)", program)
        # A clean TLS close: the guard's handler sees EOF instead of a broken pipe.
        self.assertIn("tls.unwrap()", program)
        for forbidden in (
            "POST",
            "GET ",
            "sendall",
            "Authorization",
            "check_hostname=False",
            "CERT_NONE",
        ):
            self.assertNotIn(forbidden, program)

    def test_dead_provider_transport_blocks_before_the_single_paid_submission(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with (
                patch.object(sys, "argv", gate_argv(root)),
                patch.object(gate, "require_modules"),
                patch.object(gate, "web_provenance", return_value={}),
                patch.object(gate, "verifier_provenance", return_value={}),
                patch.object(gate, "budget_status", return_value={}),
                patch.object(gate, "database_readiness", return_value={}),
                patch.object(gate, "runtime", return_value={}),
                patch.object(
                    gate,
                    "provider_tls_status",
                    side_effect=gate.Refusal("local_provider_tls_expired"),
                ),
                patch.object(gate, "compiler_canary") as canary,
                patch.object(gate.subprocess, "Popen") as browser,
            ):
                self.assertEqual(gate.main(), 1)
                browser.assert_not_called()
                canary.assert_not_called()
            record = json.loads((root / "capture/latest.json").read_text())
            self.assertEqual(record["code"], "local_provider_tls_expired")
            self.assertFalse((root / "capture/submission.json").exists())


class FakeLocalStack:
    """LocalStack keeps secrets in memory: recreating the container loses them."""

    def __init__(self, *, compose_root_changed):
        self.pending_recreation = compose_root_changed
        self.generation = 1
        self.secrets = set()
        self.log = []

    def run(self, args, timeout=45):
        args = [str(x) for x in args]
        if "up" in args:
            self.log.append(
                (
                    "up",
                    tuple(
                        x
                        for x in args[args.index("up") + 1 :]
                        if not x.startswith("-") and not x.isdigit()
                    ),
                )
            )
            if self.pending_recreation:
                # Any ``up`` converges changed dependencies, whichever roles were named.
                self.pending_recreation = False
                self.generation += 1
                self.secrets.clear()
        return ""

    def identity(self):
        return {"localstack": "container-%d" % self.generation, "cognito-local": "c"}

    def bootstrap(self):
        self.log.append(("bootstrap", self.generation))
        self.secrets.add("verifier-mtls")

    def start_application(self):
        self.run(["docker", "compose", "up", "-d", "--no-build", "verifier", "api"])


class DependencyOrderTests(unittest.TestCase):
    COMPOSE = ["docker", "compose", "--project-name", prepare.PROJECT]

    def test_first_preparation_after_a_compose_root_change_keeps_the_mtls_secret(self):
        for changed in (True, False):
            stack = FakeLocalStack(compose_root_changed=changed)
            before = prepare.bootstrap_on_stable_dependencies(
                self.COMPOSE, stack.bootstrap, run_=stack.run, identity=stack.identity
            )
            stack.start_application()
            prepare.require_dependencies_unchanged(before, identity=stack.identity)
            self.assertEqual(stack.secrets, {"verifier-mtls"})
            self.assertEqual(stack.log[0], ("up", prepare.STABLE_DEPENDENCIES))
            self.assertEqual(stack.log[1][0], "bootstrap")

    def test_previous_order_loses_the_secret_and_is_now_refused(self):
        stack = FakeLocalStack(compose_root_changed=True)
        before = stack.identity()
        stack.bootstrap()
        stack.start_application()
        self.assertEqual(stack.secrets, set())
        with self.assertRaises(prepare.gate.Refusal) as caught:
            prepare.require_dependencies_unchanged(before, identity=stack.identity)
        self.assertEqual(
            str(caught.exception),
            "local_dependency_recreated_after_verifier_tls_bootstrap",
        )

    def test_dependencies_are_waited_for_before_anything_is_written(self):
        seen = []
        prepare.bootstrap_on_stable_dependencies(
            self.COMPOSE,
            lambda: seen.append("bootstrap"),
            run_=lambda args, timeout=45: seen.append(args) or "",
            identity=lambda: seen.append("identity") or {},
        )
        self.assertEqual(seen[1:], ["identity", "bootstrap"])
        self.assertEqual(seen[0][: len(self.COMPOSE)], self.COMPOSE)
        self.assertIn("--wait", seen[0])
        self.assertIn("--no-build", seen[0])
        self.assertEqual(tuple(seen[0][-2:]), prepare.STABLE_DEPENDENCIES)

    def test_whole_start_keeps_the_secret_and_names_a_late_recreation(self):
        stack = FakeLocalStack(compose_root_changed=True)
        prepare.start_stack(
            self.COMPOSE, stack.bootstrap, run_=stack.run, identity=stack.identity
        )
        self.assertEqual(stack.secrets, {"verifier-mtls"})
        self.assertEqual([entry[0] for entry in stack.log], ["up", "bootstrap", "up"])
        self.assertEqual(stack.log[0][1], prepare.STABLE_DEPENDENCIES)
        self.assertEqual(stack.log[2][1], prepare.APPLICATION_ROLES)
        self.assertEqual(stack.generation, 2)

        class RecreatedByApplicationStart(FakeLocalStack):
            def run(self, args, timeout=45):
                if "up" in args and "api" in args:
                    self.pending_recreation = True
                return super().run(args, timeout)

        late = RecreatedByApplicationStart(compose_root_changed=False)
        with self.assertRaises(prepare.gate.Refusal) as caught:
            prepare.start_stack(
                self.COMPOSE, late.bootstrap, run_=late.run, identity=late.identity
            )
        # The specific code, immediately: not the generic readiness refusal 120 s later.
        self.assertEqual(
            str(caught.exception),
            "local_dependency_recreated_after_verifier_tls_bootstrap",
        )
        self.assertEqual(late.secrets, set())

    def test_preparation_main_runs_the_ordered_start(self):
        calls = []
        with (
            patch.object(
                prepare,
                "bootstrap_on_stable_dependencies",
                lambda *a, **k: calls.append("deps") or {"x": 1},
            ),
            patch.object(
                prepare,
                "run",
                lambda args, timeout=45: (
                    calls.append(tuple(args[-len(prepare.APPLICATION_ROLES) :])) or ""
                ),
            ),
            patch.object(
                prepare,
                "require_dependencies_unchanged",
                lambda before, **k: calls.append(("same", before)),
            ),
        ):
            prepare.start_stack(["docker", "compose"], lambda: None)
        self.assertEqual(calls, ["deps", prepare.APPLICATION_ROLES, ("same", {"x": 1})])
        body = inspect.getsource(prepare.main)
        self.assertEqual(body.count("start_stack(compose, bootstrap)"), 1)
        self.assertNotIn("stay in place", body)

    def test_dependency_identity_reads_the_actual_owned_containers(self):
        seen = []

        def run(args):
            seen.append(args[-1])
            return json.dumps("id-" + args[-1])

        self.assertEqual(
            prepare.dependency_identity(run_=run),
            {
                "localstack": "id-pals-reliability-local-localstack-1",
                "cognito-local": "id-pals-reliability-local-cognito-local-1",
            },
        )


class BuildRecordWorkingDirectoryTests(unittest.TestCase):
    REVISION = "a" * 40
    IMAGE = "sha256:" + "b" * 64

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.context = self.root / "out" / "context"
        self.context.mkdir(parents=True)
        self.elsewhere = self.root / "elsewhere"
        self.elsewhere.mkdir()
        self.cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self.cwd)
        self.temp.cleanup()

    def record(self, dockerfile, build_args):
        # ``docker buildx history inspect`` prints the context relative to the caller's
        # working directory when the context lies below it, otherwise absolute.
        cwd = Path(os.getcwd()).resolve()
        try:
            context = str(self.context.relative_to(cwd))
        except ValueError:
            context = str(self.context)
        return {
            "Status": "completed",
            "Context": context,
            "Dockerfile": dockerfile,
            "Platform": ["linux/arm64"],
            "BuildArgs": build_args,
            "Labels": [
                {"Name": "org.opencontainers.image.revision", "Value": self.REVISION}
            ],
            "Attachments": [
                {
                    "Digest": self.IMAGE,
                    "Type": "application/vnd.oci.image.manifest.v1+json",
                }
            ],
            "NumTotalSteps": 12,
        }

    def cases(self):
        web_args = [{"Name": k, "Value": v} for k, v in builder.LOCAL_ARGS.items()]
        return (
            (
                builder,
                builder.observe_build,
                "Dockerfile",
                web_args,
                "real_build_record_changed",
            ),
            (
                native,
                native.observe,
                "docker/lean-verifier.Dockerfile",
                [],
                "native_actual_build_record_changed",
            ),
        )

    def test_receipt_from_one_directory_verifies_from_any_other(self):
        for module, observe, dockerfile, args, code in self.cases():
            old = module.run
            module.run = lambda _args: json.dumps(
                self.record(dockerfile, args)
            ).encode()
            try:
                observed = {}
                for cwd in (self.root, self.root / "out", self.elsewhere, self.context):
                    os.chdir(cwd)
                    observed[cwd] = observe(
                        "ref", self.context, self.REVISION, self.IMAGE
                    )
                    self.assertEqual(observed[cwd]["Context"], str(self.context))
                self.assertEqual(
                    len({json.dumps(x, sort_keys=True) for x in observed.values()}), 1
                )
                # A legacy receipt froze the raw relative value of its build directory.
                os.chdir(self.root)
                legacy = self.record(dockerfile, args)
                self.assertEqual(legacy["Context"], "out/context")
                stored = self.root / "actual-build-record.json"
                stored.write_text(json.dumps(legacy))
                os.chdir(self.elsewhere)
                self.assertEqual(
                    builder.stored_build_record(stored, self.context, code),
                    observe("ref", self.context, self.REVISION, self.IMAGE),
                )
            finally:
                module.run = old

    def test_other_context_or_any_other_changed_field_is_still_refused(self):
        for module, observe, dockerfile, args, code in self.cases():
            old = module.run
            module.run = lambda _args: json.dumps(
                self.record(dockerfile, args)
            ).encode()
            try:
                os.chdir(self.root)
                good = observe("ref", self.context, self.REVISION, self.IMAGE)
                stored = self.root / "actual-build-record.json"
                for context in (
                    "other/context",
                    "context/../context",
                    "..",
                    ".",
                    "",
                    str(self.elsewhere),
                    "/out/context",
                ):
                    stored.write_text(json.dumps({**good, "Context": context}))
                    with self.assertRaises(ValueError) as caught:
                        builder.stored_build_record(stored, self.context, code)
                    self.assertEqual(str(caught.exception), code)
                stored.write_text(json.dumps({**good, "NumTotalSteps": 13}))
                self.assertNotEqual(
                    builder.stored_build_record(stored, self.context, code), good
                )
                # A record of a different build context is refused from every directory.
                with self.assertRaises(ValueError):
                    observe("ref", self.elsewhere, self.REVISION, self.IMAGE)
            finally:
                module.run = old


class VerifierVariantFixture(unittest.TestCase):
    """A real git repository with two commits whose compiler recipe files are identical."""

    IDENTITY = ["-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid"]
    PRODUCTION = "sha256:" + "9" * 64
    IMAGE = "sha256:" + "b" * 64
    LEAN = "leanprover/lean4:v4"

    def git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.repo), *self.IDENTITY, *args],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def raw_archive(self, commit, *paths):
        return subprocess.run(
            ["git", "-C", str(self.repo), "archive", "--format=tar", commit, *paths],
            check=True,
            capture_output=True,
        ).stdout

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.repo = self.root / "agent"
        files = {
            "docker/lean-verifier.Dockerfile": "FROM exact-compiler\nCOPY pyproject.toml README.md ./\n",
            "lean-workspace/lean-toolchain": self.LEAN + "\n",
            "lean-workspace/lake-manifest.json": "{}\n",
            "lean-workspace/Extra.lean": "one\n",
            "pals_agent/lean_child.py": "child = 1\n",
            "pyproject.toml": "[project]\nname='fixture'\n",
            "README.md": "fixture\n",
            "tests/test_other.py": "x = 1\n",
        }
        for name, text in files.items():
            (self.repo / name).parent.mkdir(parents=True, exist_ok=True)
            (self.repo / name).write_text(text)
        self.git("init", "-q")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "one")
        self.first = self.git("rev-parse", "HEAD")
        # Same Dockerfile, toolchain and manifest; other recipe and source files differ.
        (self.repo / "lean-workspace/Extra.lean").write_text("two\n")
        (self.repo / "pals_agent/lean_child.py").write_text("child = 2\n")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "two")
        self.second = self.git("rev-parse", "HEAD")

    def reference(self, path):
        return {"path": str(path), "sha256": gate.sha(Path(path).read_bytes())}

    def write(self, name, raw):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return path

    def build(self, commit, name="build"):
        """Everything the real builder records, without Docker: its own derivation code."""
        out = self.root / name
        out.mkdir()
        complete = self.write(name + "-complete.tar", self.raw_archive(commit))
        derived = archives.derive(self.repo, commit, complete, out)
        dockerfile, lean, lake = archives.recipe(derived["recipe_archive"])
        receipt = {
            "schema_version": native.SCHEMA,
            "source_root": str(self.repo),
            "source_revision": commit,
            "build_archive": self.reference(complete),
            "source_archive": self.reference(derived["source_archive"]),
            "recipe_archive": self.reference(derived["recipe_archive"]),
            "dockerfile_sha256": gate.sha(dockerfile),
            "lean_version": lean.decode().strip(),
            "lake_manifest_sha256": gate.sha(lake),
            "built_image_id": self.IMAGE,
            "platform": "linux/arm64",
            "difference_scope": "fixture",
        }
        return receipt

    def subject(self, receipt, name="provenance.json"):
        """The variant exactly as the preparation driver writes it."""
        file = self.write(name, json.dumps(receipt).encode())
        return {
            "images": {
                "verifier": {
                    "source_revision": receipt["source_revision"],
                    "image_id": self.IMAGE,
                    "platform": "linux/arm64",
                }
            },
            "verifier_variant": prepare.verifier_variant(
                self.PRODUCTION, receipt, self.reference(file)
            ),
        }

    def candidate(self, commit):
        return {
            "platforms": {"verifier": "linux/amd64"},
            "images": {"verifier": self.PRODUCTION},
            "recipe_active_lean_version": self.LEAN,
            "recipe_active_lake_manifest_sha256": gate.sha(b"{}\n"),
            "verifier_source": {
                "commit": commit,
                "source_archive_sha256": gate.sha(
                    self.raw_archive(commit, "pals_agent")
                ),
            },
        }


class VerifierVariantContractTests(VerifierVariantFixture):
    """Self-contained pin of what pals-infra's release plan requires (runs in every CI)."""

    def test_variant_has_exactly_the_plans_key_set_and_gits_own_archives(self):
        variant = self.subject(self.build(self.second))["verifier_variant"]
        # release-cycle.py `local_verifier_variant`: closed key set.
        self.assertEqual(
            set(variant),
            {
                "production_image_digest",
                "source_archive",
                "recipe_archive",
                "local_build_provenance",
                "dockerfile_sha256",
                "lean_version",
                "lake_manifest_sha256",
            },
        )
        # release_plan.py `VERIFIER_VARIANT_ARCHIVES`: path tuples in this exact order.
        self.assertEqual(
            archives.PROJECTIONS,
            {
                "source_archive": ("pals_agent",),
                "recipe_archive": ("docker/lean-verifier.Dockerfile", "lean-workspace"),
            },
        )
        for name, paths in archives.PROJECTIONS.items():
            expected = self.raw_archive(self.second, *paths)
            self.assertEqual(Path(variant[name]["path"]).read_bytes(), expected)
            self.assertEqual(variant[name]["sha256"], gate.sha(expected))
            self.assertEqual(set(variant[name]), {"path", "sha256"})
        # The reviewed manifest pin is the hash of the pals_agent archive.
        self.assertEqual(
            variant["source_archive"]["sha256"],
            self.candidate(self.second)["verifier_source"]["source_archive_sha256"],
        )
        self.assertNotEqual(
            variant["source_archive"]["sha256"], gate.sha(self.raw_archive(self.second))
        )
        self.assertEqual(variant["production_image_digest"], self.PRODUCTION)
        self.assertEqual(variant["lean_version"], self.LEAN)

    def test_git_command_form_and_environment_match_the_plan(self):
        seen = []
        real = archives.subprocess.run

        def run(argv, **options):
            seen.append((argv, options.get("env")))
            return real(argv, **options)

        with (
            patch.object(archives.subprocess, "run", run),
            patch.dict(os.environ, {"GIT_DIR": "/nonexistent", "GIT_WORK_TREE": "/x"}),
        ):
            raw = archives.git_archive(self.repo, self.second, ("pals_agent",))
        self.assertEqual(raw, self.raw_archive(self.second, "pals_agent"))
        argv, environment = seen[0]
        self.assertEqual(
            argv,
            [
                "git",
                "-C",
                str(self.repo),
                "archive",
                "--format=tar",
                self.second,
                "pals_agent",
            ],
        )
        self.assertFalse(
            [
                k
                for k in environment
                if k.startswith("GIT_")
                and k not in ("GIT_CONFIG_NOSYSTEM", "GIT_TERMINAL_PROMPT")
            ]
        )
        for bad in ("HEAD", "--output=/tmp/x", self.second[:12], self.second.upper()):
            with self.assertRaises(ValueError):
                archives.git_archive(self.repo, bad, ("pals_agent",))

    def test_runner_accepts_the_prepared_variant_and_reads_the_recipe_archive(self):
        subject = self.subject(self.build(self.second))
        calls = []
        old = gate.command
        gate.command = lambda args, timeout=0: calls.append(args) or ""
        try:
            result = gate.verifier_provenance(subject)
        finally:
            gate.command = old
        variant = subject["verifier_variant"]
        self.assertEqual(
            result["source_archive_sha256"], variant["source_archive"]["sha256"]
        )
        self.assertEqual(
            result["recipe_archive_sha256"], variant["recipe_archive"]["sha256"]
        )
        self.assertEqual(
            result["build_archive_sha256"], gate.sha(self.raw_archive(self.second))
        )
        # The receipt, and through it the built archive, stays hash-bound in the subject.
        self.assertEqual(
            result["build_provenance_sha256"],
            variant["local_build_provenance"]["sha256"],
        )
        self.assertEqual(
            calls[0][1:3], [str(ROOT / "local-verifier-build.py"), "--verify-receipt"]
        )

    def refused(self, subject, code):
        old = gate.command
        gate.command = lambda args, timeout=0: ""
        try:
            with self.assertRaises(gate.Refusal) as caught:
                gate.verifier_provenance(subject)
        finally:
            gate.command = old
        self.assertEqual(str(caught.exception), code)

    def test_runner_refuses_an_open_or_incomplete_variant(self):
        subject = self.subject(self.build(self.second))
        missing = json.loads(json.dumps(subject))
        del missing["verifier_variant"]["recipe_archive"]
        self.refused(missing, "closed_native_local_verifier_variant_required")
        extra = json.loads(json.dumps(subject))
        extra["verifier_variant"]["build_archive"] = extra["verifier_variant"][
            "source_archive"
        ]
        self.refused(extra, "closed_native_local_verifier_variant_required")

    def test_runner_refuses_archives_of_another_commit_or_an_old_receipt(self):
        good = self.build(self.second)
        other = self.build(self.first, "other")
        differs = "native_verifier_plan_archive_differs_from_the_built_commit"
        # A recipe archive of another commit has the SAME Dockerfile, toolchain and manifest.
        self.assertEqual(other["dockerfile_sha256"], good["dockerfile_sha256"])
        self.assertEqual(other["lake_manifest_sha256"], good["lake_manifest_sha256"])
        for name in ("recipe_archive", "source_archive"):
            self.assertNotEqual(other[name]["sha256"], good[name]["sha256"])
            self.refused(
                self.subject({**good, name: other[name]}, name + ".json"), differs
            )
        # The image built from another commit's complete archive.
        self.refused(
            self.subject(
                {**good, "build_archive": other["build_archive"]}, "built.json"
            ),
            differs,
        )
        # A consistent set, but git at the recorded commit produces other bytes.
        self.refused(
            self.subject({**other, "source_revision": self.second}, "commit.json"),
            differs,
        )
        # A changed frozen file.
        subject = self.subject(good, "frozen.json")
        Path(good["recipe_archive"]["path"]).write_bytes(
            Path(other["recipe_archive"]["path"]).read_bytes()
        )
        self.refused(subject, "frozen_provenance_file_changed")
        # Identical bytes at another path are still not what the receipt recorded.
        copied = self.build(self.second, "copied")
        subject = self.subject(copied, "copied.json")
        for name in ("recipe_archive", "source_archive"):
            moved = self.write(
                name + "-moved.tar", Path(copied[name]["path"]).read_bytes()
            )
            changed = json.loads(json.dumps(subject))
            changed["verifier_variant"][name] = self.reference(moved)
            self.refused(changed, "native_verifier_build_binding_changed")
        again = self.build(self.second, "again")
        self.refused(
            self.subject(
                {**again, "schema_version": "pals.local-verifier-build.v1"}, "v1.json"
            ),
            "native_verifier_build_binding_changed",
        )
        receipt = {**again, "dockerfile_sha256": "0" * 64}
        self.refused(
            self.subject(receipt, "docker.json"),
            "actual_native_verifier_toolchain_changed",
        )

    def test_projection_proof_compares_every_member_with_the_built_archive(self):
        complete = self.write("complete.tar", self.raw_archive(self.second))
        other = self.write("other-complete.tar", self.raw_archive(self.first))
        out = self.root / "derived"
        out.mkdir()
        derived = archives.derive(self.repo, self.second, complete, out)
        for name, paths in archives.PROJECTIONS.items():
            self.assertGreater(
                archives.require_projection(complete, derived[name], paths, "code"), 0
            )
            with self.assertRaises(ValueError) as caught:
                archives.require_projection(other, derived[name], paths, "code")
            self.assertEqual(str(caught.exception), "code")
        # Not a projection of the claimed paths: too few and too many members.
        with self.assertRaises(ValueError):
            archives.require_projection(
                complete, derived["recipe_archive"], ("lean-workspace",), "code"
            )
        with self.assertRaises(ValueError):
            archives.require_projection(
                complete, derived["source_archive"], ("pals_agent", "tests"), "code"
            )
        with self.assertRaises(ValueError):
            archives.require_projection(
                complete, derived["source_archive"], ("absent",), "code"
            )
        # Same content, changed mode.
        changed = self.root / "changed.tar"
        with (
            tarfile.open(derived["source_archive"]) as source,
            tarfile.open(changed, "w") as target,
        ):
            for member in source.getmembers():
                data = source.extractfile(member) if member.isfile() else None
                if member.isfile():
                    member.mode = 0o777
                target.addfile(member, data)
        with self.assertRaises(ValueError):
            archives.require_projection(complete, changed, ("pals_agent",), "code")
        # Building from another commit's complete archive is refused at build time.
        out2 = self.root / "derived-2"
        out2.mkdir()
        with self.assertRaises(ValueError) as caught:
            archives.derive(self.repo, self.second, other, out2)
        self.assertIn("not_of_the_built_commit", str(caught.exception))
        references = {name: self.reference(path) for name, path in derived.items()}
        archives.verify(self.repo, self.second, complete, references, "code")
        for broken in (
            {"source_archive": references["source_archive"]},
            {
                **references,
                "recipe_archive": {**references["recipe_archive"], "sha256": "0" * 64},
            },
            {**references, "recipe_archive": references["source_archive"]},
        ):
            with self.assertRaises(ValueError):
                archives.verify(self.repo, self.second, complete, broken, "code")
        with self.assertRaises(ValueError):
            archives.verify(self.repo, self.first, complete, references, "code")

    def test_builder_receipt_verification_requires_the_new_schema_and_proof(self):
        source = inspect.getsource(native.main)
        self.assertEqual(native.SCHEMA, "pals.local-verifier-build.v2")
        self.assertIn("archives.derive(", source)
        self.assertLess(source.index("archives.derive("), source.index('"buildx"'))
        self.assertIn("archives.verify(", source)


@unittest.skipUnless((INFRA / "release_plan.py").is_file(), INFRA_REASON)
class RealReleasePlanValidatorTests(VerifierVariantFixture):
    """The prepared variant is fed to pals-infra's own validators, unmodified."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(INFRA))
        try:
            import release_plan

            cls.plan = release_plan
            cls.cli = load("pals_release_plan_cli_contract", INFRA / "release-plan.py")
            cls.cycle = load("pals_release_cycle_contract", INFRA / "release-cycle.py")
        finally:
            sys.path.remove(str(INFRA))

    def context(self, commit):
        from types import SimpleNamespace

        return SimpleNamespace(
            manifest={"verifier_source": {"commit": commit}},
            git=self.cli.Git(root=self.root, agent_repo=self.repo),
            derived_files={},
        )

    def cycle_check(self, variant, candidate, frozen=None):
        from types import SimpleNamespace

        if frozen is None:
            frozen = {
                variant[name]["path"]: variant[name]["sha256"]
                for name in (
                    "source_archive",
                    "recipe_archive",
                    "local_build_provenance",
                )
            }
        self.cycle.Cycle.local_verifier_variant(
            SimpleNamespace(plan={"frozen_files": frozen}), variant, candidate
        )

    def test_release_plan_accepts_the_prepared_variant(self):
        subject = self.subject(self.build(self.second))
        self.assertTrue(
            self.plan.check_local_verifier_variant(self.context(self.second), subject)
        )
        self.cycle_check(subject["verifier_variant"], self.candidate(self.second))

    def test_release_plan_refuses_what_the_runner_refuses(self):
        good = self.build(self.second)
        other = self.build(self.first, "other")
        for name in ("recipe_archive", "source_archive"):
            subject = self.subject({**good, name: other[name]}, name + ".json")
            with self.assertRaises(self.plan.Refusal) as caught:
                self.plan.check_local_verifier_variant(
                    self.context(self.second), subject
                )
            self.assertEqual(
                str(caught.exception),
                "local_verifier_%s_differs_from_the_verifier_commit" % name,
            )
        variant = self.subject(good)["verifier_variant"]
        # The former shape: no recipe archive, complete archive as source archive.
        former = {k: v for k, v in variant.items() if k != "recipe_archive"}
        with self.assertRaises(self.cycle.Refusal) as caught:
            self.cycle_check(former, self.candidate(self.second), {})
        self.assertEqual(
            str(caught.exception), "closed_native_local_verifier_variant_required"
        )
        complete = {**variant, "source_archive": good["build_archive"]}
        with self.assertRaises(self.cycle.Refusal) as caught:
            self.cycle_check(complete, self.candidate(self.second))
        self.assertEqual(
            str(caught.exception), "native_local_verifier_source_archive_differs"
        )
        with self.assertRaises(self.cycle.Refusal) as caught:
            self.cycle_check(variant, self.candidate(self.second), {})
        self.assertEqual(
            str(caught.exception), "frozen_actual_local_verifier_provenance_required"
        )


class RuntimeDirectoryRelocationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def test_any_existing_private_plain_path_is_an_accepted_runtime_directory(self):
        persistent = (
            self.root / "pals-release-archive" / "pals-local-qualification-runtime"
        )
        persistent.mkdir(parents=True, mode=0o700)
        persistent.chmod(0o700)
        self.assertEqual(prepare.require_runtime_directory(persistent), persistent)
        for bad, mode in (
            (self.root / "open", 0o755),
            (self.root / "with space", 0o700),
        ):
            bad.mkdir(mode=mode)
            bad.chmod(mode)
            with self.assertRaises(prepare.gate.Refusal) as caught:
                prepare.require_runtime_directory(bad)
            self.assertEqual(
                str(caught.exception), "existing_private_runtime_directory_required"
            )
        with self.assertRaises((prepare.gate.Refusal, OSError)):
            prepare.require_runtime_directory(self.root / "absent")

    def test_every_bind_mount_follows_the_given_runtime_directory(self):
        template = (ROOT / "local-qualification/compose.override.yml.in").read_text()
        values = {
            "@@RUNTIME@@": "/Users/example/pals-local-qualification-runtime",
            "@@API_IMAGE@@": "api",
            "@@WORKER_IMAGE@@": "worker",
            "@@WEB_IMAGE@@": "web",
            "@@VERIFIER_IMAGE@@": "verifier",
            "@@GUARD_IMAGE@@": "guard",
        }
        rendered = prepare.render_profile(template, values)
        binds = [
            line.strip().lstrip("- ")
            for line in rendered.splitlines()
            if ":/run/" in line and line.strip().startswith("- ")
        ]
        self.assertGreaterEqual(len(binds), 5)
        for bind in binds:
            self.assertTrue(bind.startswith(values["@@RUNTIME@@"] + "/"), bind)
        with self.assertRaises(prepare.gate.Refusal):
            prepare.render_profile(template, {"@@RUNTIME@@": "/x"})

    def ledgers(self, extra_call_after_copy):
        import shutil as copier

        old = self.root / "serving" / "budget"
        old.mkdir(parents=True)
        budget = proxy.Budget(old / "ledger.json")
        budget.complete(budget.reserve("gpt-6.1-terra", 1000, 1000), 1000, 100)
        new = self.root / "persistent" / "budget"
        copier.copytree(old, new)
        if extra_call_after_copy:
            # A provider call the still-running guard records after the copy was taken.
            budget.complete(budget.reserve("gpt-6.1-terra", 2000, 1000), 2000, 100)
        return old, new

    def test_call_recorded_after_the_copy_is_detected_not_under_counted(self):
        old, new = self.ledgers(extra_call_after_copy=True)
        with self.assertRaises(prepare.gate.Refusal) as caught:
            prepare.require_ledger_continuity(new / "ledger.json", old)
        self.assertEqual(
            str(caught.exception),
            "relocated_budget_ledger_differs_from_the_serving_ledger",
        )
        # Re-copying the final ledger (producers are stopped by then) is accepted.
        (new / "ledger.json").write_bytes((old / "ledger.json").read_bytes())
        self.assertEqual(
            prepare.require_ledger_continuity(new / "ledger.json", old),
            "relocated_identical",
        )
        for field, value in (("actual_microusd", 1), ("blocked", True), ("calls", [])):
            changed = json.loads((old / "ledger.json").read_bytes())
            changed[field] = value
            (new / "ledger.json").write_text(json.dumps(changed))
            with self.assertRaises(prepare.gate.Refusal):
                prepare.require_ledger_continuity(new / "ledger.json", old)

    def test_unrelocated_and_fresh_stacks_and_a_lost_serving_ledger(self):
        old, new = self.ledgers(extra_call_after_copy=False)
        self.assertEqual(
            prepare.require_ledger_continuity(old / "ledger.json", old),
            "same_directory",
        )
        self.assertEqual(
            prepare.require_ledger_continuity(new / "ledger.json", None),
            "same_directory",
        )
        self.assertEqual(
            prepare.require_ledger_continuity(new / "ledger.json", old),
            "relocated_identical",
        )
        (old / "ledger.json").unlink()
        with self.assertRaises(prepare.gate.Refusal) as caught:
            prepare.require_ledger_continuity(new / "ledger.json", old)
        self.assertEqual(
            str(caught.exception), "relocated_budget_serving_ledger_required"
        )

    def test_serving_directory_is_read_from_the_actual_guard_container(self):
        name = "pals-reliability-local-worker-network-guard-1"
        mounts = [
            {"Destination": "/run/provider", "Source": "/old/provider-tls"},
            {"Destination": "/run/budget", "Source": "/old/budget"},
        ]

        def run(args):
            if args[:2] == ["docker", "ps"]:
                self.assertIn("name=^/" + name + "$", args)
                return "abc123\n"
            self.assertEqual(args[-1], name)
            return json.dumps(mounts)

        self.assertEqual(
            prepare.serving_budget_directory(run_=run), Path("/old/budget")
        )
        self.assertIsNone(prepare.serving_budget_directory(run_=lambda args: ""))
        mounts.pop()
        with self.assertRaises(prepare.gate.Refusal):
            prepare.serving_budget_directory(run_=run)

    def prepare_until_build(
        self, extra_call_after_copy, *, mutate=None, leftover=None, extra_argv=()
    ):
        """The real entry point against a fake Docker, up to the guard image build."""
        old, new = self.ledgers(extra_call_after_copy)
        if mutate:
            mutate(old)
            shutil.rmtree(new)
            shutil.copytree(old, new)
        runtime = new.parent
        runtime.chmod(0o700)
        (runtime / "local.env").write_text("PALS_ENV=local\nPALS_ENVIRONMENT=local\n")
        (runtime / "local.env").chmod(0o600)
        revision = "a" * 40
        subject = {
            "images": {
                role: {"source_revision": revision, "image_reference": role}
                for role in ("api", "worker", "web", "verifier")
            }
        }
        receipt = {"source_revision": revision, "built_image_id": "sha256:" + "b" * 64}
        files = {}
        for name, value in (
            ("base-subject", subject),
            ("web-build-receipt", receipt),
            ("verifier-build-receipt", receipt),
        ):
            files[name] = self.root / (name + ".json")
            files[name].write_text(json.dumps(value))
        commands = []

        def run(args, timeout=45):
            args = [str(x) for x in args]
            commands.append(args)
            if args[:3] == ["docker", "context", "inspect"]:
                return "unix:///var/run/docker.sock\n"
            if args[:2] == ["docker", "ps"] and any("network-guard" in x for x in args):
                return "abc123\n"
            if args[:2] == ["docker", "inspect"] and "{{json .Mounts}}" in args:
                return json.dumps([{"Destination": "/run/budget", "Source": str(old)}])
            if args[:2] == ["docker", "inspect"]:
                return json.dumps({"codex.owner": prepare.gate.OWNER})
            if "rev-parse" in args:
                return revision + "\n"
            if any(x.endswith("leftover_jobs.py") for x in args):
                return json.dumps(
                    leftover or {"state": "none", "requests": 0, "jobs": 0}
                )
            return ""

        def reached_build(*_args, **_kwargs):
            raise prepare.gate.Refusal("fixture_reached_the_guard_build")

        argv = ["prepare", "--runtime-dir", str(runtime), *extra_argv]
        for name in ("compose-root", "api-source", "api-python", "agent-python"):
            argv += ["--" + name, str(self.root / name)]
        for name, path in files.items():
            argv += ["--" + name, str(path)]
        previous = dict(prepare.gate._DIAGNOSTICS)
        try:
            with (
                patch.object(sys, "argv", argv),
                patch.object(prepare, "run", run),
                patch.object(prepare, "build", reached_build),
                patch.object(prepare, "require_child_modules", lambda *a, **k: None),
                patch.object(prepare, "require_provider_tls", lambda *a, **k: {}),
                patch.object(prepare.gate, "require_modules", lambda *a, **k: None),
            ):
                with self.assertRaises(prepare.gate.Refusal) as caught:
                    prepare.main()
        finally:
            prepare.gate._DIAGNOSTICS.update(previous)
        return str(caught.exception), commands, runtime

    def test_preparation_compares_ledgers_only_after_it_stopped_the_producers(self):
        code, commands, runtime = self.prepare_until_build(extra_call_after_copy=True)
        self.assertEqual(
            code, "relocated_budget_ledger_differs_from_the_serving_ledger"
        )
        words = [" ".join(c) for c in commands]
        mounts = next(i for i, c in enumerate(words) if "{{json .Mounts}}" in c)
        stop = next(i for i, c in enumerate(commands) if "stop" in c)
        self.assertLess(mounts, stop)
        self.assertEqual(stop, len(commands) - 1)
        for role in (
            "worker",
            "assessment-worker",
            "recipe-reviewer",
            "worker-network-guard",
        ):
            self.assertIn(role, commands[stop])
        # Refused before the copy was adopted: no resume binding, no backup written.
        self.assertNotIn(
            "PALS_BUDGET_RESUME_SHA256", (runtime / "local.env").read_text()
        )
        self.assertFalse(list(runtime.glob("budget-before-prepare-*")))
        code, commands, runtime = self.prepare_until_build_in_new_root(False)
        self.assertEqual(code, "fixture_reached_the_guard_build")
        self.assertIn("PALS_BUDGET_RESUME_SHA256", (runtime / "local.env").read_text())

    def test_preparation_main_accepts_only_the_proven_rolled_over_ledger(self):
        def roll(budget_directory, *, keep_archive=True):
            ledger = budget_directory / "ledger.json"
            budget = proxy.Budget(ledger, resume_sha256=sha256(ledger.read_bytes()))
            budget.uncertain(budget.reserve("gpt-6-luna", 1000, 1000), "timeout")
            approval = budget_directory.parent / "approval.json"
            approval.write_text(
                json.dumps(
                    {
                        "schema_version": proxy.APPROVAL_SCHEMA,
                        "approved_by": "repository owner",
                        "approved_at": "2026-11-13",
                        "approval_text": "approved",
                        "closed_ledger_sha256": sha256(ledger.read_bytes()),
                        "new_limit_microusd": 200000,
                    }
                )
            )
            rollover_tool.rollover(
                budget_directory.parent,
                approval,
                sha256(approval.read_bytes()),
                guard_running_=lambda: False,
            )
            if not keep_archive:
                for archive in budget_directory.glob("closed-*"):
                    shutil.rmtree(archive)

        code, _, runtime = self.prepare_until_build(False, mutate=roll)
        self.assertEqual(code, "fixture_reached_the_guard_build")
        ledger = runtime / "budget/ledger.json"
        self.assertEqual(json.loads(ledger.read_bytes())["calls"], [])
        self.assertIn(
            "PALS_BUDGET_RESUME_SHA256=" + sha256(ledger.read_bytes()),
            (runtime / "local.env").read_text(),
        )
        self.root = self.root / "blocked"
        self.root.mkdir()
        code, _, runtime = self.prepare_until_build(
            False, mutate=lambda d: roll(d, keep_archive=False)
        )
        self.assertEqual(code, "budget_rollover_not_proven:rollover_archive_missing")
        self.assertNotIn(
            "PALS_BUDGET_RESUME_SHA256", (runtime / "local.env").read_text()
        )

    def test_preparation_main_stops_on_leftover_jobs_before_anything_starts(self):
        leftover = {"state": "leftover", "requests": 1, "jobs": 1}
        code, commands, runtime = self.prepare_until_build(False, leftover=leftover)
        self.assertEqual(code, "leftover_non_terminal_local_jobs:requests=1,jobs=1")
        self.assertTrue(commands[-1][1].endswith("leftover_jobs.py"))
        self.assertNotIn("--fail", commands[-1])
        self.assertFalse(any("up" in c for c in commands))
        self.assertNotIn(
            "PALS_BUDGET_RESUME_SHA256", (runtime / "local.env").read_text()
        )
        self.root = self.root / "ended"
        self.root.mkdir()
        code, commands, _ = self.prepare_until_build(
            False,
            leftover={"state": "ended", "requests": 1, "jobs": 1},
            extra_argv=("--fail-leftover-local-jobs",),
        )
        self.assertEqual(code, "fixture_reached_the_guard_build")
        self.assertIn("--fail", next(c for c in commands if "leftover_jobs.py" in c[1]))

    def prepare_until_build_in_new_root(self, extra_call_after_copy):
        self.root = self.root / "second"
        self.root.mkdir()
        return self.prepare_until_build(extra_call_after_copy)

    def test_copied_ledger_continues_with_the_same_calls_and_spending(self):
        import hashlib
        import shutil as copier

        old = self.root / "old" / "budget"
        old.mkdir(parents=True)
        budget = proxy.Budget(old / "ledger.json")
        for tokens in (1000, 2000):
            budget.complete(budget.reserve("gpt-6.1-terra", tokens, 1000), tokens, 100)
        raw = (old / "ledger.json").read_bytes()
        new = self.root / "persistent" / "budget"
        copier.copytree(old, new)
        resumed = proxy.Budget(
            new / "ledger.json", resume_sha256=hashlib.sha256(raw).hexdigest()
        )
        self.assertEqual(len(resumed.calls), 2)
        self.assertEqual(resumed.actual, budget.actual)
        self.assertEqual(resumed.held, budget.held)
        self.assertEqual((old / "ledger.json").read_bytes(), raw)


def sha256(raw):
    import hashlib

    return hashlib.sha256(raw).hexdigest()


class BudgetRolloverFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.runtime = Path(self.temp.name).resolve() / "runtime"
        (self.runtime / "budget").mkdir(parents=True)
        self.ledger = self.runtime / "budget/ledger.json"

    def blocked_ledger(self):
        """One completed call, then a forward whose cost stayed unknown: blocked."""
        budget = proxy.Budget(self.ledger)
        budget.complete(budget.reserve("gpt-6.1-terra", 1000, 1000), 1000, 100)
        budget.uncertain(
            budget.reserve("gpt-6-luna", 1000, 1000), "upstream_status_429"
        )
        return self.ledger.read_bytes()

    def healthy_ledger(self):
        budget = proxy.Budget(self.ledger)
        budget.complete(budget.reserve("gpt-6.1-terra", 1000, 1000), 1000, 100)
        return self.ledger.read_bytes()

    def approval(self, closed_raw=None, **changed):
        record = {
            "schema_version": proxy.APPROVAL_SCHEMA,
            "approved_by": "repository owner",
            "approved_at": "2026-11-13",
            "approval_text": "Close the blocked local ledger and open a new one.",
            "closed_ledger_sha256": sha256(
                self.ledger.read_bytes() if closed_raw is None else closed_raw
            ),
            "new_limit_microusd": 300000,
        }
        record.update(changed)
        for name in [k for k, v in record.items() if v is ...]:
            del record[name]
        path = self.runtime / "approval.json"
        path.write_text(json.dumps(record, indent=1))
        return path, sha256(path.read_bytes())

    def roll(self, path, digest, guard=False):
        return rollover_tool.rollover(
            self.runtime, path, digest, guard_running_=lambda: guard
        )

    def refused(self, path, digest, guard=False):
        with self.assertRaises(rollover_tool.Refusal) as caught:
            self.roll(path, digest, guard)
        return str(caught.exception)


class BudgetRolloverRefusalTests(BudgetRolloverFixture):
    def assert_untouched(self, raw):
        self.assertEqual(self.ledger.read_bytes(), raw)
        self.assertFalse(list((self.runtime / "budget").glob("closed-*")))

    def test_healthy_ledger_cannot_be_rolled_over(self):
        raw = self.healthy_ledger()
        self.assertEqual(
            self.refused(*self.approval()), "rollover_healthy_ledger_refused"
        )
        self.assert_untouched(raw)
        # A ledger without any call is healthy too: no reset of an unused budget.
        self.ledger.unlink()
        raw = (proxy.Budget(self.ledger), self.ledger.read_bytes())[1]
        self.assertEqual(
            self.refused(*self.approval()), "rollover_healthy_ledger_refused"
        )
        self.assert_untouched(raw)

    def test_approval_hash_on_the_command_line_must_match_the_record(self):
        raw = self.blocked_ledger()
        path, digest = self.approval()
        self.assertEqual(
            self.refused(path, "0" * 64), "rollover_approval_sha256_mismatch"
        )
        # Editing the record after its hash was approved is the same refusal.
        path.write_text(path.read_text().replace("300000", "700000"))
        self.assertEqual(
            self.refused(path, digest), "rollover_approval_sha256_mismatch"
        )
        self.assert_untouched(raw)

    def test_approval_must_name_exactly_the_ledger_being_closed(self):
        raw = self.blocked_ledger()
        self.assertEqual(
            self.refused(*self.approval(closed_raw=b"another ledger")),
            "rollover_ledger_sha256_mismatch",
        )
        self.assert_untouched(raw)

    def test_call_still_in_flight_is_refused(self):
        budget = proxy.Budget(self.ledger)
        budget.uncertain(budget.reserve("gpt-6-luna", 1000, 1000), "timeout")
        raw = json.loads(self.ledger.read_bytes())
        raw["calls"].append(
            {
                "model": "gpt-6-luna",
                "input_bound": 1,
                "output_bound": 1,
                "reserved_microusd": 1,
                "state": "reserved",
            }
        )
        self.ledger.write_text(json.dumps(raw, sort_keys=True))
        before = self.ledger.read_bytes()
        self.assertEqual(
            self.refused(*self.approval()), "rollover_call_in_flight_refused"
        )
        self.assert_untouched(before)

    def test_running_guard_missing_record_and_links_are_refused(self):
        raw = self.blocked_ledger()
        path, digest = self.approval()
        self.assertEqual(
            self.refused(path, digest, guard=True), "rollover_requires_stopped_guard"
        )
        self.assertEqual(
            self.refused(self.runtime / "absent.json", digest),
            "rollover_approval_record_required",
        )
        link = self.runtime / "link.json"
        link.symlink_to(path)
        self.assertEqual(
            self.refused(link, digest), "rollover_approval_record_required"
        )
        self.assert_untouched(raw)

    def test_bound_above_the_limit_and_open_or_incomplete_records_are_refused(self):
        raw = self.blocked_ledger()
        for changed, code in (
            ({"new_limit_microusd": proxy.LIMIT + 1}, "rollover_new_limit_invalid"),
            ({"new_limit_microusd": 0}, "rollover_new_limit_invalid"),
            ({"new_limit_microusd": True}, "rollover_new_limit_invalid"),
            ({"new_limit_microusd": "300000"}, "rollover_new_limit_invalid"),
            ({"approval_text": " "}, "rollover_approval_record_invalid"),
            ({"approved_at": "yesterday"}, "rollover_approval_record_invalid"),
            ({"approved_by": ...}, "rollover_approval_record_invalid"),
            ({"extra": "field"}, "rollover_approval_record_invalid"),
            ({"schema_version": "v0"}, "rollover_approval_record_invalid"),
        ):
            self.assertEqual(self.refused(*self.approval(**changed)), code, changed)
        path = self.runtime / "approval.json"
        path.write_text("not json")
        self.assertEqual(
            self.refused(path, sha256(path.read_bytes())),
            "rollover_ledger_or_approval_unreadable",
        )
        self.assert_untouched(raw)

    def test_guard_state_is_read_from_docker_and_unknown_is_refused(self):
        calls = []

        def fake(returncode, stdout):
            def run(args, **_kwargs):
                calls.append(args)
                return subprocess.CompletedProcess(args, returncode, stdout, "")

            return run

        with patch.object(rollover_tool.subprocess, "run", fake(0, "abc\n")):
            self.assertTrue(rollover_tool.guard_running())
        with patch.object(rollover_tool.subprocess, "run", fake(0, "")):
            self.assertFalse(rollover_tool.guard_running())
        with patch.object(rollover_tool.subprocess, "run", fake(1, "")):
            with self.assertRaises(rollover_tool.Refusal):
                rollover_tool.guard_running()
        self.assertIn("name=^/" + rollover_tool.GUARD + "$", calls[0])
        self.assertIn("status=running", calls[0])


class BudgetRolloverAcceptanceTests(BudgetRolloverFixture):
    def rolled(self):
        closed = self.blocked_ledger()
        path, digest = self.approval()
        return closed, digest, self.roll(path, digest)

    def test_closed_ledger_is_archived_byte_identically_and_header_records_it(self):
        closed, digest, result = self.rolled()
        archive = self.runtime / "budget" / ("closed-" + sha256(closed))
        self.assertEqual((archive / "ledger.json").read_bytes(), closed)
        self.assertEqual(sha256((archive / "approval.json").read_bytes()), digest)
        self.assertEqual(stat.S_IMODE(archive.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((archive / "ledger.json").stat().st_mode), 0o400)
        opened = json.loads(self.ledger.read_bytes())
        self.assertEqual(
            (opened["calls"], opened["actual_microusd"], opened["reserved_microusd"]),
            ([], 0, 0),
        )
        self.assertFalse(opened["blocked"])
        self.assertEqual(opened["limit_microusd"], 300000)
        header = opened["rollover"]
        self.assertEqual(header["rolled_over_from_sha256"], sha256(closed))
        self.assertEqual(header["approval_sha256"], digest)
        self.assertEqual(
            header["closed_totals"],
            {
                "calls": 2,
                "actual_microusd": 1750,
                "reserved_microusd": 1750 + 625,
                "unknown_calls": 1,
                "unknown_reasons": {"upstream_status_429": 1},
                "limit_microusd": proxy.LIMIT,
                "blocked": True,
                "cumulative": {
                    "ledgers": 1,
                    "actual_microusd": 1750,
                    "reserved_microusd": 2375,
                },
            },
        )
        self.assertEqual(result["state"], "rolled_over_not_prepared")
        self.assertEqual(result["new_ledger_sha256"], sha256(self.ledger.read_bytes()))
        # Repeating the same command finds a healthy ledger: no second reset.
        path = self.runtime / "approval.json"
        self.assertEqual(self.refused(path, digest), "rollover_ledger_sha256_mismatch")
        self.assertEqual((archive / "ledger.json").read_bytes(), closed)

    def test_proxy_accepts_the_rolled_over_ledger_only_with_its_exact_hash(self):
        self.rolled()
        raw = self.ledger.read_bytes()
        # A restart without the hash prepare binds still cannot adopt it.
        for resume in (None, "0" * 64):
            with self.assertRaises(ValueError) as caught:
                proxy.Budget(self.ledger, resume_sha256=resume)
            self.assertEqual(
                str(caught.exception), "existing_budget_no_automatic_retry"
            )
        budget = proxy.Budget(self.ledger, resume_sha256=sha256(raw))
        self.assertEqual((budget.calls, budget.actual, budget.held), ([], 0, 0))
        self.assertEqual(budget.limit, 300000)
        # The approved bound, not the fixed one, limits the new ledger.
        with self.assertRaises(ValueError):
            budget.reserve("gpt-6.1-sol", 80000, 40000)
        budget.complete(budget.reserve("gpt-6.1-terra", 1000, 1000), 1000, 100)
        saved = json.loads(self.ledger.read_bytes())
        self.assertEqual(saved["limit_microusd"], 300000)
        self.assertEqual(saved["rollover"], json.loads(raw)["rollover"])
        # A later restart keeps the header, the bound and the new call.
        again = proxy.Budget(
            self.ledger, resume_sha256=sha256(self.ledger.read_bytes())
        )
        self.assertEqual(
            (again.limit, again.actual, len(again.calls)), (300000, 1750, 1)
        )
        self.assertEqual(again.rollover, saved["rollover"])

    def spend_once(self):
        budget = proxy.Budget(
            self.ledger, resume_sha256=sha256(self.ledger.read_bytes())
        )
        budget.complete(budget.reserve("gpt-6.1-terra", 1000, 1000), 1000, 100)
        return budget

    def assert_reset_refused(self):
        raw = self.ledger.read_bytes()
        with self.assertRaises(ValueError) as caught:
            proxy.Budget(self.ledger, resume_sha256=sha256(raw))
        self.assertEqual(str(caught.exception), "rollover_already_started_no_reset")
        with self.assertRaises(prepare.gate.Refusal) as caught:
            prepare.require_known_budget(self.ledger)
        self.assertEqual(
            str(caught.exception),
            "budget_rollover_not_proven:rollover_already_started_no_reset",
        )
        self.assertEqual(self.ledger.read_bytes(), raw)

    def test_restored_zero_call_ledger_cannot_reset_spending_after_first_use(self):
        closed, _, _ = self.rolled()
        archive = self.runtime / "budget" / ("closed-" + sha256(closed))
        opened = self.ledger.read_bytes()
        # The copy preparation itself keeps of the ledger it adopted.
        backup = self.runtime / ("budget-before-prepare-" + sha256(opened) + ".json")
        backup.write_bytes(opened)
        # Unused, the ledger may be started any number of times: nothing was spent.
        proxy.Budget(self.ledger, resume_sha256=sha256(opened))
        started_unused = self.ledger.read_bytes()
        proxy.Budget(self.ledger, resume_sha256=sha256(started_unused))
        prepare.require_known_budget(self.ledger)
        self.assertFalse((archive / proxy.STARTED_MARKER).exists())
        self.spend_once()
        spent = self.ledger.read_bytes()
        marker = archive / proxy.STARTED_MARKER
        self.assertTrue(marker.is_file())
        self.assertEqual(stat.S_IMODE(marker.stat().st_mode), 0o400)
        for restored in (backup.read_bytes(), opened, started_unused):
            self.ledger.write_bytes(restored)
            self.assert_reset_refused()
        # The ledger with its recorded call continues, and restores a removed marker.
        self.ledger.write_bytes(spent)
        marker.chmod(0o600)
        marker.unlink()
        again = proxy.Budget(self.ledger, resume_sha256=sha256(spent))
        self.assertEqual(again.actual, 1750)
        self.assertTrue(marker.is_file())
        self.ledger.write_bytes(opened)
        self.assert_reset_refused()

    def test_approval_and_closed_ledger_open_a_new_ledger_only_once(self):
        closed, digest, _ = self.rolled()
        path = self.runtime / "approval.json"
        # Unused: repeating the rollover yields the same zero state, never more budget.
        self.ledger.write_bytes(closed)
        self.roll(path, digest)
        self.spend_once()
        spent = self.ledger.read_bytes()
        self.ledger.write_bytes(closed)
        self.assertEqual(self.refused(path, digest), "rollover_already_used")
        # Another approval for the same closed ledger is refused as well.
        other, other_digest = self.approval(approval_text="approved once more")
        self.assertNotEqual(other_digest, digest)
        self.assertEqual(self.refused(other, other_digest), "rollover_already_used")
        self.assertEqual(self.ledger.read_bytes(), closed)
        self.assertEqual(len(list((self.runtime / "budget").glob("closed-*"))), 1)
        # Only the ledger that carries the spending continues.
        self.ledger.write_bytes(spent)
        self.assertEqual(
            prepare.require_known_budget(self.ledger)[1]["calls"][0]["state"],
            "completed",
        )

    def test_two_proxies_started_from_the_same_zero_call_ledger(self):
        self.rolled()
        opened = self.ledger.read_bytes()
        first = proxy.Budget(self.ledger, resume_sha256=sha256(opened))
        self.ledger.write_bytes(opened)
        second = proxy.Budget(self.ledger, resume_sha256=sha256(opened))
        first.reserve("gpt-6-luna", 1, 1)
        with self.assertRaises(ValueError) as caught:
            second.reserve("gpt-6-luna", 1, 1)
        self.assertEqual(str(caught.exception), "rollover_already_started_no_reset")
        self.assertEqual(second.calls, [])
        self.assertTrue(second.blocked)

    def test_prepare_accepts_it_and_binds_the_approved_bound(self):
        self.rolled()
        raw, previous, limit = prepare.require_known_budget(self.ledger)
        self.assertEqual(raw, self.ledger.read_bytes())
        self.assertEqual(limit, 300000)
        self.assertEqual(previous["calls"], [])

    def tampered(self):
        """Every way to present a zero-call ledger without the approved rollover."""
        closed, digest, _ = self.rolled()
        archive = self.runtime / "budget" / ("closed-" + sha256(closed))
        opened = self.ledger.read_bytes()

        def restore():
            shutil.rmtree(archive, ignore_errors=True)
            archive.mkdir(mode=0o700)
            (archive / "ledger.json").write_bytes(closed)
            (archive / "approval.json").write_bytes(
                (self.runtime / "approval.json").read_bytes()
            )
            self.ledger.write_bytes(opened)

        def edit_ledger(change):
            def apply():
                value = json.loads(opened)
                change(value)
                self.ledger.write_text(json.dumps(value, sort_keys=True))

            return apply

        def healthy_archive():
            value = json.loads(closed)
            value["blocked"] = False
            value["calls"] = value["calls"][:1]
            value["reserved_microusd"] = value["actual_microusd"]
            healthy = json.dumps(value, sort_keys=True).encode()
            other = archive.with_name("closed-" + sha256(healthy))
            other.mkdir()
            self.addCleanup(shutil.rmtree, other, True)
            (other / "ledger.json").write_bytes(healthy)
            approval = json.loads((self.runtime / "approval.json").read_bytes())
            approval["closed_ledger_sha256"] = sha256(healthy)
            approval_raw = json.dumps(approval).encode()
            (other / "approval.json").write_bytes(approval_raw)
            edit_ledger(
                lambda v: v["rollover"].update(
                    rolled_over_from_sha256=sha256(healthy),
                    approval_sha256=sha256(approval_raw),
                    closed_totals=proxy.closed_totals(value),
                )
            )()

        cases = {
            "archive removed": lambda: shutil.rmtree(archive),
            "closed ledger edited": lambda: (
                (archive / "ledger.json").chmod(0o600),
                (archive / "ledger.json").write_bytes(closed + b" "),
            ),
            "approval replaced": lambda: (
                (archive / "approval.json").chmod(0o600),
                (archive / "approval.json").write_bytes(b"{}"),
            ),
            "bound raised": edit_ledger(lambda v: v.update(limit_microusd=proxy.LIMIT)),
            "totals rewritten": edit_ledger(
                lambda v: v["rollover"]["closed_totals"].update(actual_microusd=0)
            ),
            "header removed": edit_ledger(lambda v: v.update(rollover=None)),
            "header open": edit_ledger(lambda v: v["rollover"].update(note="x")),
            "healthy ledger archived by hand": healthy_archive,
        }
        return cases, restore

    def test_proxy_and_prepare_refuse_every_unproven_zero_call_ledger(self):
        cases, restore = self.tampered()
        for name, tamper in cases.items():
            restore()
            tamper()
            raw = self.ledger.read_bytes()
            with self.assertRaises(ValueError, msg=name):
                proxy.Budget(self.ledger, resume_sha256=sha256(raw))
            with self.assertRaises(prepare.gate.Refusal, msg=name) as caught:
                prepare.require_known_budget(self.ledger)
            self.assertRegex(
                str(caught.exception),
                r"^(budget_rollover_not_proven:rollover_[a-z_]+"
                r"|known_existing_budget_required_no_reset)$",
                name,
            )
            # Refused ledgers are never rewritten by the refusal.
            self.assertEqual(self.ledger.read_bytes(), raw, name)
        restore()
        prepare.require_known_budget(self.ledger)

    def test_paths_without_an_approval_still_cannot_reset_spending(self):
        raw = self.blocked_ledger()
        for code, action in (
            ("known_existing_budget_required_no_reset", lambda: None),
            ("existing_budget_ledger_required_no_reset", self.ledger.unlink),
            (
                "known_existing_budget_required_no_reset",
                lambda: proxy.Budget(self.ledger),
            ),
        ):
            action()
            with self.assertRaises(prepare.gate.Refusal) as caught:
                prepare.require_known_budget(self.ledger)
            self.assertEqual(str(caught.exception), code)
        self.ledger.write_bytes(raw)
        with self.assertRaises(ValueError) as caught:
            proxy.Budget(self.ledger, resume_sha256=sha256(raw))
        self.assertEqual(str(caught.exception), "uncertain_budget_cannot_resume")

    def test_second_rollover_keeps_the_cumulative_closed_spending(self):
        self.rolled()
        budget = proxy.Budget(
            self.ledger, resume_sha256=sha256(self.ledger.read_bytes())
        )
        budget.uncertain(budget.reserve("gpt-6-luna", 1000, 1000), "timeout")
        path, digest = self.approval(new_limit_microusd=100000)
        self.roll(path, digest)
        totals = json.loads(self.ledger.read_bytes())["rollover"]["closed_totals"]
        self.assertEqual(totals["unknown_reasons"], {"timeout": 1})
        self.assertEqual(
            totals["cumulative"],
            {"ledgers": 2, "actual_microusd": 1750, "reserved_microusd": 3000},
        )
        self.assertEqual(len(list((self.runtime / "budget").glob("closed-*"))), 2)
        self.assertEqual(prepare.require_known_budget(self.ledger)[2], 100000)

    def test_capture_evidence_and_subject_record_the_rollover(self):
        self.rolled()
        ledger = json.loads(self.ledger.read_bytes())
        subject = {
            "guard": {
                "budget_limit_microusd": 300000,
                "budget_rollover": ledger["rollover"],
                "resumed_budget": {"path": "/private/backup", "sha256": "a" * 64},
            }
        }
        with patch.object(gate, "command", return_value=json.dumps(ledger)):
            self.assertEqual(gate.budget_status(subject), ledger)
            for changed in (
                {"budget_rollover": None},
                {
                    "budget_rollover": {
                        **ledger["rollover"],
                        "approval_sha256": "0" * 64,
                    }
                },
                {"budget_limit_microusd": 700000},
            ):
                with self.assertRaises(gate.Refusal):
                    gate.budget_status({"guard": {**subject["guard"], **changed}})
        # A continuous ledger must not claim a rollover, and keeps the fixed bound.
        plain = {**ledger, "rollover": None, "limit_microusd": 700000}
        with patch.object(gate, "command", return_value=json.dumps(plain)):
            with self.assertRaises(gate.Refusal) as caught:
                gate.budget_status(
                    {"guard": {**subject["guard"], "budget_limit_microusd": 700000}}
                )
            self.assertEqual(
                str(caught.exception), "budget_rollover_differs_from_subject"
            )
            gate.budget_status({"guard": {"budget_limit_microusd": 700000}})
        low = {**plain, "limit_microusd": 300000}
        with patch.object(gate, "command", return_value=json.dumps(low)):
            with self.assertRaises(gate.Refusal):
                gate.budget_status({"guard": {"budget_limit_microusd": 300000}})
        evidence = gate.budget_rollover_evidence(subject, ledger)
        self.assertEqual(evidence["state"], "owner_approved_rollover")
        self.assertEqual(evidence["closed_totals"]["unknown_calls"], 1)
        self.assertEqual(evidence["new_limit_microusd"], 300000)
        self.assertEqual(
            gate.budget_rollover_evidence(subject, plain),
            {"state": "none_continuous_ledger"},
        )

    def test_capture_record_carries_the_rollover_even_when_the_capture_fails(self):
        self.rolled()
        ledger = json.loads(self.ledger.read_bytes())
        root = self.runtime.parent
        subject = root / "subject.json"
        subject.write_text(
            json.dumps(
                {
                    "schema_version": "pals.local-qualification-subject.v1",
                    "basis": "approved-local-real-db-lean-model",
                    "fixture": {
                        "paid_submissions": 1,
                        "maximum_approved_usd": 1,
                        "output_language": "en",
                    },
                    "local_profile": {},
                    "guard": {
                        "budget_limit_microusd": 300000,
                        "budget_rollover": ledger["rollover"],
                    },
                }
            )
        )
        argv = ["gate", "--subject", str(subject), "--state-dir", str(root / "capture")]
        argv += ["--web-root", str(root), "--database-env", str(root / "private.env")]
        with (
            patch.object(sys, "argv", argv),
            patch.object(gate, "require_modules"),
            patch.object(gate, "web_provenance", return_value={}),
            patch.object(gate, "verifier_provenance", return_value={}),
            patch.object(gate, "runtime", return_value={}),
            patch.object(gate, "command", return_value=json.dumps(ledger)),
            patch.object(
                gate, "database_readiness", side_effect=gate.Refusal("stop_here")
            ),
            patch.object(gate.subprocess, "Popen") as browser,
        ):
            self.assertEqual(gate.main(), 1)
            browser.assert_not_called()
        record = json.loads((root / "capture/latest.json").read_text())
        self.assertEqual(record["budget_rollover"]["state"], "owner_approved_rollover")
        self.assertEqual(
            record["budget_rollover"]["rolled_over_from_sha256"],
            ledger["rollover"]["rolled_over_from_sha256"],
        )
        self.assertEqual(
            record["provider_budget_before"]["rollover"], ledger["rollover"]
        )


class UnknownReasonTests(unittest.TestCase):
    def test_every_condition_has_its_own_closed_code(self):
        import http.client

        for error, code in (
            (ValueError("upstream_status_429"), "upstream_status_429"),
            (ValueError("upstream_status_500"), "upstream_status_500"),
            (TimeoutError(), "timeout"),
            (ValueError("upstream_too_large"), "body_too_large"),
            (json.JSONDecodeError("x", "y", 0), "unparseable_body"),
            (KeyError("usage"), "unparseable_usage"),
            (TypeError(), "unparseable_usage"),
            (ValueError("unknown_price_or_usage"), "unparseable_usage"),
            (ValueError("upstream_model_changed"), "model_mismatch"),
            (ValueError("upstream_standard_tier_unconfirmed"), "service_tier"),
            (ValueError("usage_exceeds_reservation"), "usage_above_reservation"),
            (ssl.SSLCertVerificationError("secret host text"), "upstream_tls_error"),
            (ConnectionResetError("secret"), "upstream_transport_error"),
            (http.client.IncompleteRead(b"secret"), "upstream_protocol_error"),
            (ValueError("sk-secret provider text"), "internal_error"),
            (RuntimeError("secret"), "internal_error"),
        ):
            self.assertEqual(proxy.unknown_reason(error), code, repr(error))

    def test_reason_is_a_closed_code_and_never_free_text(self):
        with tempfile.TemporaryDirectory() as d:
            budget = proxy.Budget(Path(d) / "ledger.json")
            for reason, stored in (
                ("upstream_status_503", "upstream_status_503"),
                ("Bearer sk-secret", "internal_error"),
                (None, "internal_error"),
                ("x" * 49, "internal_error"),
            ):
                budget.blocked = False
                index = budget.reserve("gpt-6-luna", 1, 1)
                budget.uncertain(index, reason)
                row = json.loads((Path(d) / "ledger.json").read_bytes())["calls"][index]
                self.assertEqual(
                    (row["state"], row["unknown_reason"]), ("unknown", stored)
                )

    def forward(self, upstream):
        """One paid Responses call through the real handler with a scripted upstream."""
        with tempfile.TemporaryDirectory() as d:
            budget = proxy.Budget(Path(d) / "ledger.json")
            payload = json.dumps(
                {
                    "model": "gpt-6-luna",
                    "input": "prove it",
                    "max_output_tokens": 100,
                    "service_tier": "default",
                }
            ).encode()
            handler = proxy.Handler.__new__(proxy.Handler)
            handler.path = "/v1/responses"
            handler.headers = {"Content-Length": str(len(payload))}
            handler.rfile = io.BytesIO(payload)
            handler.server = type("Server", (), {"budget": budget})()
            answers = []
            handler.respond = lambda status, raw: answers.append(status)

            def scripted(path, _payload):
                if path.endswith("/input_tokens"):
                    return b'{"object":"response.input_tokens","input_tokens":10}'
                return upstream()

            with patch.object(proxy, "upstream", scripted):
                handler.do_POST()
            return answers[0], json.loads((Path(d) / "ledger.json").read_bytes())

    def test_handler_records_which_condition_fired_in_the_ledger_row(self):
        def raises(error):
            def call():
                raise error

            return call

        def body(**changed):
            value = {
                "model": "gpt-6-luna",
                "service_tier": "default",
                "usage": {"input_tokens": 10, "output_tokens": 5},
            }
            value.update(changed)
            return lambda: json.dumps(value).encode()

        for upstream, reason in (
            (raises(ValueError("upstream_status_429")), "upstream_status_429"),
            (raises(TimeoutError()), "timeout"),
            (raises(ValueError("upstream_too_large")), "body_too_large"),
            (lambda: b"<html>", "unparseable_body"),
            (body(usage=None), "unparseable_usage"),
            (
                body(usage={"input_tokens": "ten", "output_tokens": 5}),
                "unparseable_usage",
            ),
            (body(model="gpt-6.1-sol"), "model_mismatch"),
            (body(service_tier="priority"), "service_tier"),
            (
                body(usage={"input_tokens": 11, "output_tokens": 5}),
                "usage_above_reservation",
            ),
        ):
            status, ledger = self.forward(upstream)
            self.assertEqual(status, 402, reason)
            self.assertTrue(ledger["blocked"], reason)
            self.assertEqual(
                [(c["state"], c["unknown_reason"]) for c in ledger["calls"]],
                [("unknown", reason)],
            )
            self.assertEqual(
                set(ledger["calls"][0]) - {"unknown_reason"},
                {"model", "input_bound", "output_bound", "reserved_microusd", "state"},
            )
        status, ledger = self.forward(body())
        self.assertEqual(status, 200)
        self.assertEqual(ledger["calls"][0]["state"], "completed")
        self.assertNotIn("unknown_reason", ledger["calls"][0])

    def test_upstream_names_the_actual_status(self):
        class Connection:
            def __init__(self, *args, **kwargs):
                pass

            def request(self, *args, **kwargs):
                pass

            def getresponse(self):
                return type("Response", (), {"status": 429})()

            def close(self):
                pass

        environment = {"PALS_OPENAI_UPSTREAM_IP": "8.8.8.8", "OPENAI_API_KEY": "test"}
        with (
            patch.object(proxy, "HTTPSConnection", Connection),
            patch.dict(os.environ, environment),
        ):
            with self.assertRaises(ValueError) as caught:
                proxy.upstream("/v1/responses", {})
        self.assertEqual(str(caught.exception), "upstream_status_429")
        self.assertEqual(proxy.unknown_reason(caught.exception), "upstream_status_429")


class OperationalError(Exception):
    """Stands in for psycopg.OperationalError, which is matched by its name."""


class FakeConnection:
    """Records statements; answers privilege and catalog reads from a small state."""

    def __init__(self, state):
        self.state = state
        self.statements = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def cursor(self):
        return self

    def execute(self, statement, parameters=()):
        self.statements.append((statement, tuple(parameters)))
        state = self.state
        result = None
        if statement.startswith("GRANT UPDATE"):
            state.setdefault("column_update", set()).add(statement)
        elif "has_column_privilege" in statement:
            table, column = parameters[1].split(".")[1], parameters[2]
            held = any(
                '("%s") ON public."%s"' % (column, table) in grant
                for grant in state.get("column_update", ())
            )
            result = (
                held and not state.get("grant_ineffective"),
                table in state.get("table_update", ()),
            )
        elif "has_table_privilege" in statement:
            result = (parameters[1].split(".")[1] in state.get("table_update", ()),)
        elif "pg_database" in statement:
            result = (1,) if state.get("database") else None
        elif "FROM public.proof_explanations e" in statement:
            result = (state.get("explanations", 0),)
        elif "to_regclass" in statement and "AND to_regclass" in statement:
            result = (all(state.get("tables", (True, True))),)
        elif "to_regclass" in statement:
            result = state.get("tables", (True, True))
        elif "FROM public.proof_requests WHERE" in statement:
            return type("Rows", (), {"fetchall": lambda _s: list(state["requests"])})()
        elif "FROM public.proof_jobs" in statement:
            return type("Rows", (), {"fetchall": lambda _s: list(state["jobs"])})()
        return type("Row", (), {"fetchone": lambda _s: result})()


class EmptyServerBootstrapTests(unittest.TestCase):
    PARTS = bootstrap.validate_local_dsn(
        "postgresql://local_user:" + "a" * 64 + "@127.0.0.1:55432/pals"
    )

    def test_maintenance_connection_does_not_need_the_legacy_default_database(self):
        seen = []

        def server(existing):
            def connect(url, autocommit=False):
                name = url.rsplit("/", 1)[1]
                seen.append((name, autocommit))
                if name not in existing:
                    raise OperationalError("database does not exist")
                return name

            return connect

        # A freshly created server has ``postgres`` and nothing else.
        self.assertEqual(
            bootstrap.connect_maintenance(self.PARTS, connect=server({"postgres"})),
            "postgres",
        )
        self.assertEqual(seen, [("postgres", True)])
        # The container this stack was first created with keeps working either way.
        self.assertEqual(
            bootstrap.connect_maintenance(
                self.PARTS, connect=server({"pals_reliability_test"})
            ),
            "pals_reliability_test",
        )
        with self.assertRaises(ValueError) as caught:
            bootstrap.connect_maintenance(self.PARTS, connect=server(set()))
        self.assertEqual(
            str(caught.exception), "local_maintenance_database_unavailable"
        )

        def broken(url, autocommit=False):
            raise RuntimeError("not a missing database")

        with self.assertRaises(RuntimeError):
            bootstrap.connect_maintenance(self.PARTS, connect=broken)
        self.assertNotIn(
            "/pals_reliability_test",
            inspect.getsource(bootstrap.main),
            "the maintenance database is no longer hardcoded in the bootstrap",
        )

    def test_rowlock_grants_are_exactly_what_the_readiness_check_requires(self):
        self.assertEqual(
            bootstrap.ROWLOCK_COLUMNS,
            tuple((table, column) for _, table, column, _ in readiness.FUNCTIONS),
        )
        self.assertEqual(bootstrap.SCHEMA_OWNER, "pals_api_schema_owner")
        connection = FakeConnection({})
        self.assertEqual(
            bootstrap.grant_rowlock_privileges(connection),
            [
                "proof_verification_candidates.candidate_id",
                "proof_explanations.proof_job_id",
            ],
        )
        grants = [s for s, _ in connection.statements if not s.startswith("SELECT")]
        self.assertEqual(
            grants,
            [
                'GRANT UPDATE ("candidate_id") ON public."proof_verification_candidates" TO "pals_api_schema_owner"',
                'GRANT UPDATE ("proof_job_id") ON public."proof_explanations" TO "pals_api_schema_owner"',
            ],
        )
        # Idempotent: a second bootstrap issues the same two statements and nothing else.
        bootstrap.grant_rowlock_privileges(connection)
        again = [s for s, _ in connection.statements if not s.startswith("SELECT")]
        self.assertEqual(again, grants * 2)
        self.assertEqual(len(connection.state["column_update"]), 2)

    def test_table_level_update_or_an_ineffective_grant_is_refused(self):
        broad = FakeConnection({"table_update": {"proof_explanations"}})
        with self.assertRaises(ValueError) as caught:
            bootstrap.grant_rowlock_privileges(broad)
        self.assertEqual(
            str(caught.exception),
            "local_rowlock_table_update_too_broad:proof_explanations",
        )
        # Never widened and never revoked here: only the first, narrow grant was issued.
        self.assertEqual(
            [s for s, _ in broad.statements if not s.startswith("SELECT")],
            [
                'GRANT UPDATE ("candidate_id") ON public."proof_verification_candidates" TO "pals_api_schema_owner"'
            ],
        )
        with self.assertRaises(ValueError) as caught:
            bootstrap.grant_rowlock_privileges(
                FakeConnection({"grant_ineffective": True})
            )
        self.assertEqual(
            str(caught.exception),
            "local_rowlock_grant_failed:proof_verification_candidates",
        )
        with patch.object(bootstrap, "ROWLOCK_COLUMNS", (('x"; DROP', "y"),)):
            with self.assertRaises(ValueError):
                bootstrap.grant_rowlock_privileges(FakeConnection({}))


class ServingMigratorFixture(unittest.TestCase):
    """A miniature API source tree with the same shape as the candidate's."""

    SERVING = """from app.infrastructure.repositories.retry_schema import (
    preflight as retry_preflight,
)
from app.release.current_migration import preflight as current_preflight
from app.release.keyed_migration import preflight as keyed_preflight
from app.release.orphan_schema import preflight as orphan_preflight
from app.release.other import unrelated


def build():
    from app.release.late_migration import preflight
"""
    SCHEMA = """from pathlib import Path
STATE = Path(__file__).with_name("installed")


def preflight(database_url):
    if not STATE.exists() or "broken" in STATE.read_text():
        raise RuntimeError("Explanation retry migration is required before serving")
"""
    MIGRATION = """from app.infrastructure.repositories.retry_schema import STATE


def apply(database_url: str) -> str:
    STATE.write_text(database_url + MARK)
    return "installed"
"""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name).resolve()
        files = {
            "app/infrastructure/bootstrap.py": self.SERVING,
            "app/infrastructure/repositories/retry_schema.py": self.SCHEMA,
            "app/release/retry_migration.py": self.MIGRATION.replace("MARK", "''"),
            "app/release/current_migration.py": "CALLS = []\n\n\ndef preflight(database_url):\n    CALLS.append('preflight')\n\n\ndef apply(database_url):\n    CALLS.append('apply')\n",
            "app/release/keyed_migration.py": "def preflight(database_url, key):\n    raise RuntimeError\n",
            "app/release/orphan_schema.py": "def preflight(database_url):\n    raise RuntimeError\n",
            "app/release/other.py": "unrelated = 1\n",
        }
        for name, text in files.items():
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        for package in self.source.rglob("*"):
            if package.is_dir():
                (package / "__init__.py").write_text("")
        sys.path.insert(0, str(self.source))
        self.addCleanup(self.forget)

    def forget(self):
        sys.path.remove(str(self.source))
        for name in [n for n in sys.modules if n == "app" or n.startswith("app.")]:
            del sys.modules[name]

    def state(self):
        return self.source / "app/infrastructure/repositories/installed"


class ServingMigratorTests(ServingMigratorFixture):
    RETRY = "app.infrastructure.repositories.retry_schema"

    def test_required_preflights_are_read_from_the_serving_source(self):
        self.assertEqual(
            bootstrap.serving_preflight_modules(self.source),
            [
                self.RETRY,
                "app.release.current_migration",
                "app.release.keyed_migration",
                "app.release.orphan_schema",
            ],
        )

    def test_empty_database_gets_the_candidates_own_migrator_once(self):
        url = "postgresql://local/pals"
        report, not_applicable = bootstrap.apply_serving_migrators(self.source, url)
        # Named explicitly: what this bootstrap could never install, whatever its state.
        self.assertEqual(
            not_applicable,
            ["app.release.keyed_migration", "app.release.orphan_schema"],
        )
        self.assertEqual(
            report,
            {
                self.RETRY: "installed_by:app.release.retry_migration",
                "app.release.current_migration": "current",
                "app.release.keyed_migration": "not_checked_other_signature",
                # Never stricter than serving: reported, the API start stays the judge.
                "app.release.orphan_schema": "failing_no_discoverable_migrator",
            },
        )
        self.assertEqual(self.state().read_text(), url)
        import app.release.current_migration as current

        self.assertEqual(current.CALLS, ["preflight"])
        # Second bootstrap: already current, the migrator is not run again.
        self.state().write_text("kept")
        report, _ = bootstrap.apply_serving_migrators(self.source, url)
        self.assertEqual(report[self.RETRY], "current")
        self.assertEqual(self.state().read_text(), "kept")

    def test_migration_that_does_not_satisfy_serving_is_a_closed_refusal(self):
        (self.source / "app/release/retry_migration.py").write_text(
            self.MIGRATION.replace("MARK", "'broken'")
        )
        with self.assertRaises(ValueError) as caught:
            bootstrap.apply_serving_migrators(self.source, "postgresql://local/pals")
        self.assertEqual(
            str(caught.exception),
            "local_serving_migration_failed:app.release.retry_migration",
        )

    def test_two_possible_migrators_are_not_guessed(self):
        (self.source / "app/release/second_migration.py").write_text(
            self.MIGRATION.replace("MARK", "'second'")
        )
        self.assertEqual(
            bootstrap.migrator_candidates(self.source, self.RETRY),
            ["app.release.retry_migration", "app.release.second_migration"],
        )
        report, not_applicable = bootstrap.apply_serving_migrators(
            self.source, "postgresql://local/pals"
        )
        self.assertEqual(report[self.RETRY], "failing_no_discoverable_migrator")
        self.assertFalse(self.state().exists())
        self.assertIn(self.RETRY, not_applicable)

    @unittest.skipUnless(
        (ROOT.parent / "pals-api/app/infrastructure/bootstrap.py").is_file(),
        "pals-api submodule is not initialised: the real serving source was NOT read",
    )
    def test_pinned_api_source_yields_the_explanation_retry_migrator(self):
        api = ROOT.parent / "pals-api"
        modules = bootstrap.serving_preflight_modules(api)
        schema = "app.infrastructure.repositories.explanation_retry_schema"
        self.assertIn(schema, modules)
        self.assertEqual(
            bootstrap.migrator_candidates(api, schema),
            ["app.release.explanation_retry_migration"],
        )
        # Every other serving preflight has no module-level apply(database_url): the
        # bootstrap reports those by name and never installs them.
        for module in modules:
            if module == schema:
                continue
            file = api / (module.replace(".", "/") + ".py")
            functions = [
                node
                for node in ast.parse(file.read_text()).body
                if isinstance(node, ast.FunctionDef) and node.name == "apply"
            ]
            self.assertEqual(functions, [], module)


class LeftoverJobTests(unittest.TestCase):
    URL = "postgresql://local_user:" + "a" * 64 + "@127.0.0.1:55432/pals"
    TERMINAL = ["canceled", "failed", "verified"]

    def inspect(self, state, **kwargs):
        connections = []

        def connect(url, autocommit=False):
            connections.append(FakeConnection(state))
            return connections[-1]

        result = leftover_jobs.inspect(
            self.URL, connect=connect, terminal=self.TERMINAL, **kwargs
        )
        return result, connections

    def test_empty_server_and_finished_database_have_nothing_left_over(self):
        result, connections = self.inspect({"database": False})
        self.assertEqual(
            result, {"state": "no_local_database", "requests": 0, "jobs": 0}
        )
        self.assertEqual(len(connections), 1)
        result, _ = self.inspect({"database": True, "tables": (False, False)})
        self.assertEqual(
            (result["state"], result["requests"], result["jobs"]), ("none", 0, 0)
        )
        result, connections = self.inspect(
            {"database": True, "requests": [], "jobs": []}
        )
        self.assertEqual(result["state"], "none")
        statements = dict(connections[1].statements[1:])
        self.assertEqual(
            statements[leftover_jobs.REQUESTS], (["queued", "assessing", "verifying"],)
        )
        self.assertEqual(statements[leftover_jobs.JOBS], (self.TERMINAL,))

    def test_unfinished_work_is_reported_by_count_and_digest_never_by_identifier(self):
        state = {
            "database": True,
            "requests": [("request-identifier", "verifying")],
            "jobs": [("job-identifier", "repairing", "en")],
        }
        result, connections = self.inspect(state)
        self.assertEqual(result["state"], "leftover")
        self.assertEqual((result["requests"], result["jobs"]), (1, 1))
        self.assertEqual(result["request_statuses"], {"verifying": 1})
        self.assertEqual(result["job_states"], {"repairing": 1})
        self.assertEqual(result["job_sha256"], [sha256(b"job-identifier")])
        self.assertEqual(result["verified_jobs_with_unfinished_explanation"], 0)
        self.assertNotIn("identifier", json.dumps(result))
        # Read only unless asked: no statement but SET and SELECT was sent.
        for statement, _ in connections[1].statements:
            self.assertTrue(statement.startswith(("SET LOCAL", "SELECT")), statement)

    def test_ending_uses_the_candidates_calls_and_proves_nothing_is_left(self):
        state = {
            "database": True,
            "requests": [("r1", "verifying")],
            "jobs": [("j1", "repairing", "ja")],
        }
        ended = []

        def fail(connection, requests, jobs):
            ended.append((requests, jobs))
            state["requests"], state["jobs"] = [], []

        with patch.object(leftover_jobs, "fail_leftovers", fail):
            result, _ = self.inspect(state, fail=True)
        self.assertEqual(result["state"], "ended")
        self.assertEqual((result["requests"], result["jobs"]), (1, 1))
        self.assertEqual(ended, [([("r1", "verifying")], [("j1", "repairing", "ja")])])
        state.update(requests=[("r1", "verifying")], jobs=[])
        with patch.object(leftover_jobs, "fail_leftovers", lambda *a: None):
            with self.assertRaises(ValueError) as caught:
                self.inspect(state, fail=True)
        self.assertEqual(str(caught.exception), "leftover_local_jobs_not_ended")

    def test_verified_job_with_unfinished_explanation_is_reported_not_ended(self):
        state = {"database": True, "requests": [], "jobs": [], "explanations": 2}
        ended = []
        with patch.object(leftover_jobs, "fail_leftovers", lambda *a: ended.append(a)):
            for fail in (False, True):
                result, _ = self.inspect(state, fail=fail)
                # Not a refusal and nothing is written: the operator is told the count.
                self.assertEqual(result["state"], "none")
                self.assertEqual(result["verified_jobs_with_unfinished_explanation"], 2)
        self.assertEqual(ended, [])
        self.assertIn("j.state='verified'", leftover_jobs.EXPLANATIONS)
        self.assertIn("('queued','generating')", leftover_jobs.EXPLANATIONS)
        result, _ = self.run_prepare_check(
            {
                "state": "none",
                "requests": 0,
                "jobs": 0,
                "verified_jobs_with_unfinished_explanation": 2,
            }
        )
        self.assertEqual(result["verified_jobs_with_unfinished_explanation"], 2)
        self.assertIn(
            '"verified_jobs_with_unfinished_explanation": leftover_jobs.get(',
            inspect.getsource(prepare.main),
        )

    def test_only_the_closed_local_database_is_ever_read(self):
        for bad in (
            self.URL.replace("127.0.0.1", "db.example.invalid"),
            self.URL.replace("55432", "5432"),
            self.URL + "?host=remote.invalid",
        ):
            with self.assertRaises(ValueError):
                leftover_jobs.inspect(bad, connect=None, terminal=self.TERMINAL)

    def run_prepare_check(self, answer, fail=False):
        calls = []

        def run(args, timeout=45):
            calls.append([str(x) for x in args])
            return json.dumps(answer)

        result = prepare.require_no_leftover_jobs(
            Path("/runtime"), Path("/api"), Path("/python"), fail=fail, run_=run
        )
        return result, calls[0]

    def test_preparation_refuses_leftover_work_unless_told_to_end_it(self):
        with self.assertRaises(prepare.gate.Refusal) as caught:
            self.run_prepare_check({"state": "leftover", "requests": 1, "jobs": 2})
        self.assertEqual(
            str(caught.exception), "leftover_non_terminal_local_jobs:requests=1,jobs=2"
        )
        result, command = self.run_prepare_check(
            {"state": "none", "requests": 0, "jobs": 0}
        )
        self.assertEqual(result, {"state": "none", "requests": 0, "jobs": 0})
        self.assertNotIn("--fail", command)
        self.assertEqual(command[0], "/python")
        self.assertTrue(command[1].endswith("local-qualification/leftover_jobs.py"))
        result, command = self.run_prepare_check(
            {
                "state": "ended",
                "requests": 1,
                "jobs": 1,
                "job_states": {"repairing": 1},
            },
            fail=True,
        )
        self.assertEqual(command[-1], "--fail")
        self.assertEqual(result["state"], "ended")
        with self.assertRaises(prepare.gate.Refusal):
            self.run_prepare_check({"state": "unexpected"})


class ApiFreezeConvergenceTests(unittest.TestCase):
    def container(self, **host):
        return {
            "Image": "sha256:api",
            "Config": {"Env": ["A=1", "PALS_CLOUD_RESTORE_MANIFEST_SHA256=x"]},
            "HostConfig": {"NetworkMode": "database", **host},
        }

    def freeze(self, containers):
        first = containers[0]
        subject = {
            "runtime_config": {"api": prepare.runtime_config_entry(first)},
            "preparation": {},
        }
        written = []
        remaining = list(containers[1:])
        result = prepare.freeze_until_api_is_stable(
            subject,
            first,
            lambda: written.append(json.loads(json.dumps(subject))),
            lambda: remaining.pop(0),
        )
        return subject, written, result

    def test_rebuilt_stack_converges_in_one_run(self):
        created, recreated = self.container(), self.container(ShmSize=1)
        subject, written, result = self.freeze([created, recreated, recreated])
        # The written subject equals the API that serves after the last recreate.
        self.assertEqual(result, recreated)
        self.assertEqual(
            written[-1]["runtime_config"]["api"],
            prepare.runtime_config_entry(recreated),
        )
        self.assertEqual(len(written), 2)
        self.assertEqual(
            written[-1]["preparation"]["api_freeze_rounds"],
            [
                {
                    "changed": ["host_config_sha256"],
                    "changed_host_config_keys": ["ShmSize"],
                }
            ],
        )

    def test_unchanged_api_is_frozen_once_and_the_digest_variable_is_ignored(self):
        same = self.container()
        other_digest = self.container()
        other_digest["Config"]["Env"][1] = "PALS_CLOUD_RESTORE_MANIFEST_SHA256=y"
        subject, written, _ = self.freeze([same, other_digest])
        self.assertEqual(len(written), 1)
        self.assertEqual(subject["preparation"]["api_freeze_rounds"], [])

    def test_api_that_never_settles_is_refused(self):
        changing = [
            self.container(ShmSize=n) for n in range(prepare.API_FREEZE_ROUNDS + 1)
        ]
        with self.assertRaises(prepare.gate.Refusal) as caught:
            self.freeze(changing)
        self.assertEqual(
            str(caught.exception), "frozen_runtime_configuration_did_not_converge_api"
        )

    def test_preparation_main_freezes_through_the_convergence_loop(self):
        source = inspect.getsource(prepare.main)
        self.assertIn("freeze_until_api_is_stable(", source)
        self.assertLess(
            source.index("freeze_until_api_is_stable("),
            source.index("gate.runtime(subject)"),
        )
        self.assertLess(
            source.index("require_no_leftover_jobs("), source.index("start_stack(")
        )
        self.assertLess(
            source.index("require_known_budget("),
            source.index("require_no_leftover_jobs("),
        )


if __name__ == "__main__":
    unittest.main()
