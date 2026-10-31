"""Only validated public configuration may enter the inventory upload."""
import contextlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

FILE = Path(__file__).resolve().parents[1] / "aws-migration-source-inventory.py"
SPEC = importlib.util.spec_from_file_location("public_migration_inventory", FILE)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PublicRuntimeInventoryTests(unittest.TestCase):
    def test_credentials_urls_and_unknown_flags_are_not_serialized(self):
        result = MODULE.public_runtime_configuration([
            "PALS_OPENAI_API_KEY=synthetic-private-canary",
            "PALS_DATABASE_URL=synthetic-private-canary",
            "PALS_GUEST_HASH_KEY=synthetic-private-canary",
            "PALS_GUEST_CHAT_ENABLED=true",
            "UNREVIEWED_FLAG=synthetic-private-canary",
        ])
        self.assertEqual(result, {"PALS_GUEST_CHAT_ENABLED": "true"})

    def test_public_flags_models_and_origins_are_preserved_exactly(self):
        values = ["PALS_TOKEN_ACCOUNTING_ENABLED=true",
                  "PALS_DRAFT_EMBEDDING_MODEL=text-embedding-3-small",
                  'PALS_CORS_ALLOWED_ORIGINS=https://palschat.site,https://app.palschat.site',
                  'PALS_GUEST_ALLOWED_ORIGINS=["https://palschat.site"]']
        self.assertEqual(MODULE.public_runtime_configuration(values),
                         dict(value.split("=", 1) for value in values))

    def test_invalid_bool_is_rejected_without_echoing_its_value(self):
        with self.assertRaisesRegex(RuntimeError, "^Public runtime metadata is invalid$"):
            MODULE.public_runtime_configuration(["PALS_GUEST_CHAT_ENABLED=private-canary"])

    def test_duplicate_selected_key_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "ambiguous"):
            MODULE.public_runtime_configuration(["PALS_GUEST_CHAT_ENABLED=true"] * 2)

    def test_credential_bearing_origin_or_secret_shaped_model_is_rejected(self):
        for entry in ('PALS_CORS_ALLOWED_ORIGINS=https://user:private-canary@example.com',
                      'PALS_CORS_ALLOWED_ORIGINS=https://example.com/private-canary',
                      'PALS_CORS_ALLOWED_ORIGINS=https://example.com?private-canary',
                      'PALS_GUEST_ALLOWED_ORIGINS=not-json',
                      "PALS_DRAFT_EMBEDDING_MODEL=sk-private-canary"):
            with self.subTest(entry=entry), self.assertRaises(RuntimeError):
                MODULE.public_runtime_configuration([entry])

    def test_existing_public_origins_are_observed_without_inventing_a_domain_allowlist(self):
        for value in ('https://api.palschat.site,http://localhost:3000', '*'):
            self.assertEqual(MODULE.public_runtime_configuration(['PALS_CORS_ALLOWED_ORIGINS='+value]),
                             {'PALS_CORS_ALLOWED_ORIGINS': value})


    def test_observed_optional_capabilities_are_preserved_without_defaults(self):
        fields = {"PALS_TYPED_CATALOG_ENABLED": "false",
                  "PALS_PFI_PROVENANCE_SHA256": "a" * 64,
                  "PALS_DRAFT_EMBEDDING_ENDPOINT_IDENTITY": "https://api.openai.com/v1",
                  "PALS_DRAFT_EMBEDDING_DEPLOYMENT_IDENTITY": "text-embedding-3-small",
                  "PALS_RECIPE_REVIEWER_URL": "http://pals-recipe-reviewer:18119"}
        self.assertEqual(MODULE.public_runtime_configuration(
            [key + "=" + value for key, value in fields.items()]), fields)
        self.assertEqual(MODULE.public_runtime_configuration([]), {})
        for value in ("true", "false"):
            self.assertEqual(MODULE.public_runtime_configuration([
                "PALS_TYPED_CATALOG_ENABLED=" + value]), {"PALS_TYPED_CATALOG_ENABLED": value})

    def test_typed_opt_in_matches_strict_agent_bool_without_coercion(self):
        for value in ("1", "0", "on", "off", "TRUE", " false", "synthetic-private-canary"):
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                MODULE.public_runtime_configuration(["PALS_TYPED_CATALOG_ENABLED=" + value])

    def test_provenance_requires_exact_lowercase_sha256(self):
        for value in ("a" * 63, "a" * 65, "A" * 64, "synthetic-private-canary"):
            with self.subTest(length=len(value)), self.assertRaises(RuntimeError) as caught:
                MODULE.public_runtime_configuration(["PALS_PFI_PROVENANCE_SHA256=" + value])
            self.assertNotIn(value, str(caught.exception))

    def test_embedding_endpoint_identity_supports_public_labels_and_http_without_normalizing(self):
        for value in ("deployment-east-1", "local_embedding:v1", "models/snapshot-2026",
                      "http://localhost:11434", "http://ollama:11434/api/", "https://api.openai.com/v1"):
            self.assertEqual(MODULE.public_runtime_configuration([
                "PALS_DRAFT_EMBEDDING_ENDPOINT_IDENTITY=" + value]),
                {"PALS_DRAFT_EMBEDDING_ENDPOINT_IDENTITY": value})

    def test_embedding_endpoint_identity_label_cannot_bypass_url_credential_checks(self):
        for value in ("sk-" + "synthetic-private-canary", "AKIAcanary", "ASIAcanary", "private canary",
                      "https://user:canary@example.com", "http://user:canary@ollama:11434",
                      "http://ollama:11434?canary", "http://ollama:11434#canary", "http://ollama:11434?",
                      "a" * 129):
            with self.subTest(value=value), self.assertRaises(RuntimeError) as caught:
                MODULE.public_runtime_configuration(["PALS_DRAFT_EMBEDDING_ENDPOINT_IDENTITY=" + value])
            self.assertNotIn(value, str(caught.exception))

    def test_public_endpoints_reject_credentials_query_fragment_and_unsafe_paths(self):
        for value in ("ftp://example.com/v1", "https://user:synthetic-private-canary@example.com/v1",
                      "https://example.com/v1?synthetic-private-canary", "https://example.com/#canary",
                      "https://example.com/?", "https://example.com/#", "https://example.com/sk-canary",
                      "https://example.com/percent%20canary", "https://example.com:99999/v1",
                      "https://example.com/\\canary", "https://example.com/\ncanary"):
            with self.subTest(value=value), self.assertRaises(RuntimeError) as caught:
                MODULE.public_runtime_configuration(["PALS_DRAFT_EMBEDDING_ENDPOINT_IDENTITY=" + value])
            self.assertNotIn(value, str(caught.exception))

    def test_reviewer_matches_owning_origin_boundary(self):
        for value in ("http://pals-recipe-reviewer:18119", "http://recipe-reviewer:18119/",
                      "http://127.0.0.1:18119", "https://review.example.com"):
            self.assertEqual(MODULE.public_runtime_configuration(["PALS_RECIPE_REVIEWER_URL=" + value]),
                             {"PALS_RECIPE_REVIEWER_URL": value})
        for value in ("http://foreign.example.com", "https://review.example.com/v1",
                      "https://user:canary@review.example.com", "https://review.example.com?canary"):
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                MODULE.public_runtime_configuration(["PALS_RECIPE_REVIEWER_URL=" + value])

    def test_optional_deployment_rejects_secret_shaped_values_and_unknown_enable_flags(self):
        for value in ("sk-" + "synthetic-private-canary", "ASIAcanary", "AKIAcanary", "a b", ""):
            with self.subTest(value=value), self.assertRaises(RuntimeError) as caught:
                MODULE.public_runtime_configuration(["PALS_DRAFT_EMBEDDING_DEPLOYMENT_IDENTITY=" + value])
            self.assertNotIn("synthetic-private-canary", str(caught.exception))
        self.assertEqual(MODULE.public_runtime_configuration([
            "PALS_OCR_ENABLED=synthetic-private-canary", "PALS_DIAGRAM_ENABLED=synthetic-private-canary",
            "PALS_RECIPE_REVIEW_REQUESTER_SECRET=synthetic-private-canary"]), {})

    def test_new_public_keys_still_reject_duplicate_observations(self):
        for entry in ("PALS_TYPED_CATALOG_ENABLED=true", "PALS_PFI_PROVENANCE_SHA256=" + "b" * 64,
                      "PALS_RECIPE_REVIEWER_URL=https://review.example.com"):
            with self.subTest(key=entry.split("=", 1)[0]), self.assertRaises(RuntimeError):
                MODULE.public_runtime_configuration([entry, entry])


    def test_additional_code_backed_public_values_are_preserved(self):
        fields = {"PALS_PUBLIC_SUPPORT_EMAIL": "support@example.com", "PALS_OPENAI_MODEL": "gpt-5-mini",
                  "OPENAI_MODEL": "gpt-5-mini", "PALS_OPENAI_BASE_URL": "http://localhost:11434/v1",
                  "PALS_OPENAI_MAX_OUTPUT_TOKENS": "12000", "PALS_MAX_REPAIR_ATTEMPTS": "4",
                  "PALS_AGENT_WORKER_IDLE_SLEEP_SECONDS": "2.0", "PALS_EXPLANATION_MODEL_TIMEOUT_SECONDS": "90",
                  "PALS_LEAN_TIMEOUT_SECONDS": "3e2", "PALS_LEAN_REUSE_LAKE_ENVIRONMENT": "false"}
        self.assertEqual(MODULE.public_runtime_configuration([k+"="+v for k,v in fields.items()]), fields)
        self.assertEqual(MODULE.public_runtime_configuration([]), {})

    def test_additional_public_fields_fail_closed_without_values(self):
        for key,value in (("PALS_PUBLIC_SUPPORT_EMAIL", "bad<@example.com"),
                          ("PALS_OPENAI_BASE_URL", "plain-label"),
                          ("PALS_OPENAI_BASE_URL", "https://user:canary@example.com"),
                          ("PALS_OPENAI_BASE_URL", "https://example.com?canary"),
                          ("PALS_MAX_REPAIR_ATTEMPTS", "65"),
                          ("PALS_EXPLANATION_MODEL_TIMEOUT_SECONDS", "301"),
                          ("PALS_AGENT_WORKER_IDLE_SLEEP_SECONDS", "nan"),
                          ("PALS_AGENT_WORKER_IDLE_SLEEP_SECONDS", "0"),
                          ("PALS_OPENAI_MAX_OUTPUT_TOKENS", "0"),
                          ("PALS_LEAN_TIMEOUT_SECONDS", "301"),
                          ("PALS_LEAN_REUSE_LAKE_ENVIRONMENT", "on")):
            with self.subTest(key=key), self.assertRaises(RuntimeError) as caught:
                MODULE.public_runtime_configuration([key+"="+value])
            self.assertNotIn(value, str(caught.exception))

    def test_upload_file_reuse_is_exact_private_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"inventory.json";data=b'{"public":"fixture"}'
            MODULE.persist_inventory(path,data);before=path.stat()
            MODULE.persist_inventory(path,data)
            self.assertEqual(path.stat().st_ino,before.st_ino)
            self.assertEqual(path.read_bytes(),data)
            with self.assertRaises(RuntimeError):MODULE.persist_inventory(path,b"different")
            path.chmod(0o644)
            with self.assertRaises(RuntimeError):MODULE.persist_inventory(path,data)
            path.chmod(0o600)
            alias=Path(directory)/"alias";alias.symlink_to(path)
            with self.assertRaises(OSError):MODULE.persist_inventory(alias,data)
            link=Path(directory)/"link";os.link(path,link)
            with self.assertRaises(RuntimeError):MODULE.persist_inventory(path,data)
            self.assertEqual(path.read_bytes(),data)

    def test_stopped_configured_database_is_inspected_without_exec_or_sql(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory);root=home/"pals-mini-deploy";root.mkdir();(root/"state").mkdir()
            actors={"api":"pals-api"};policy={"containers":actors,"database_container":"pals-source-db"}
            (root/"deploy-config.json").write_text(json.dumps({"containers":actors}))
            (root/"controller-policy.json").write_text(json.dumps(policy))
            (root/"state/current.json").write_text('{}')
            calls=[]
            def command(args):
                calls.append(args)
                self.assertEqual(args,["docker","inspect","pals-api","pals-source-db"])
                return json.dumps([{"Name":"/"+name,"Image":"fixture-image","State":{"Status":"exited","Running":False},"Config":{"Env":["PALS_OPENAI_API_KEY=synthetic-private-canary"]},"Mounts":[]} for name in ("pals-api","pals-source-db")])
            output=io.StringIO()
            with patch.object(MODULE.pathlib.Path,"home",return_value=home),patch.object(MODULE.sys,"argv",["inventory"]),patch.object(MODULE,"command",side_effect=command),contextlib.redirect_stdout(output):
                MODULE.main()
            report=json.loads(output.getvalue());self.assertEqual(len(calls),1)
            self.assertEqual(report["report_kind"],"read_only_inventory_not_backup")
            self.assertEqual(report["containers"][1]["database_probe_skipped"],"container_not_running")
            self.assertNotIn("synthetic-private-canary",output.getvalue())


if __name__ == "__main__":
    unittest.main()
