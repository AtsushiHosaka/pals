"""Only validated public configuration may enter the inventory upload."""
import importlib.util
import unittest
from pathlib import Path

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

    def test_public_endpoints_reject_credentials_query_fragment_and_unsafe_paths(self):
        for value in ("http://example.com/v1", "https://user:synthetic-private-canary@example.com/v1",
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


if __name__ == "__main__":
    unittest.main()
