"""Contract/failure tests only. These never qualify a release or contact a provider."""

import importlib.util
import io
import json
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
                patch.object(gate, "web_provenance", return_value={}),
                patch.object(gate, "verifier_provenance", return_value={}),
                patch.object(gate, "budget_status", return_value={}),
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


if __name__ == "__main__":
    unittest.main()
