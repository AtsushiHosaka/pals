"""Contract/failure tests only. These never qualify a release or contact a provider."""

import importlib.util
import inspect
import io
import json
import os
import shutil
import ssl
import stat
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
provider_tls = load(
    "local_provider_tls_contract", ROOT / "bootstrap-local-provider-tls.py"
)
native = load("local_verifier_build_test", ROOT / "local-verifier-build.py")


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
        long = self.failing("x" * (gate.DIAGNOSTIC_LIMIT * 3) + "END")
        saved = json.loads(Path(long.detail["diagnostic_file"]).read_text())
        self.assertTrue(saved["stderr_truncated"])
        self.assertEqual(len(saved["stderr_tail_redacted"]), gate.DIAGNOSTIC_LIMIT)
        self.assertTrue(saved["stderr_tail_redacted"].endswith("END"))

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

    def test_runner_and_preparation_check_the_driver_first(self):
        for module in (gate, prepare):
            body = inspect.getsource(module.main)
            self.assertLess(
                body.index("require_modules()"),
                body.index("mkdir" if module is gate else "docker"),
            )

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

    def test_preparation_checks_material_before_it_quiesces_the_stack(self):
        body = inspect.getsource(prepare.main)
        self.assertLess(
            body.index('require_provider_tls(r / "provider-tls")'), body.index('"stop"')
        )
        self.assertNotIn("provider_tls.issue", inspect.getsource(prepare))


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

    def test_preparation_writes_dependency_state_only_inside_the_ordered_step(self):
        body = inspect.getsource(prepare.main)
        inner = body.index("def bootstrap():")
        ordered = body.index("bootstrap_on_stable_dependencies(compose, bootstrap)")
        application = body.index('"webfront",')
        unchanged = body.index("require_dependencies_unchanged(dependencies)")
        self.assertLess(inner, ordered)
        self.assertLess(ordered, application)
        self.assertLess(application, unchanged)
        for script in (
            "bootstrap-local-verifier-tls.py",
            "bootstrap-local-recipe-config.py",
            "bootstrap_database.py",
        ):
            self.assertEqual(body.count(script), 1 if "verifier" not in script else 2)
            self.assertTrue(inner < body.index(script) < ordered, script)
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


if __name__ == "__main__":
    unittest.main()
