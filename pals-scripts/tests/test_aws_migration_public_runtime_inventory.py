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

    def test_foreign_origin_or_secret_shaped_model_is_rejected(self):
        for entry in ('PALS_CORS_ALLOWED_ORIGINS=https://example.com',
                      'PALS_GUEST_ALLOWED_ORIGINS=not-json',
                      "PALS_DRAFT_EMBEDDING_MODEL=sk-private-canary"):
            with self.subTest(entry=entry), self.assertRaises(RuntimeError):
                MODULE.public_runtime_configuration([entry])


if __name__ == "__main__":
    unittest.main()
