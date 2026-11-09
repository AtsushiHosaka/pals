"""Real local legacy fixture/migrations; never production admission or synthetic answers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


def validate_local_dsn(value, *, service=False):
    parts = urlsplit(value)
    hosts = ("postgres",) if service else ("127.0.0.1", "localhost")
    if (
        parts.scheme != "postgresql"
        or parts.hostname not in hosts
        or parts.port != (5432 if service else 55432)
        or parts.path != "/pals"
        or parts.query
        or parts.fragment
        or not parts.username
        or not parts.password
    ):
        raise ValueError("closed_local_database_uri_required")
    return parts


def runtime_login_url(value):
    parts = validate_local_dsn(value, service=True)
    result = urlunsplit(
        parts._replace(netloc=parts.netloc.rsplit("@", 1)[0] + "@127.0.0.1:55432")
    )
    validate_local_dsn(result)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--runtime-dir", type=Path, required=True)
    p.add_argument("--api-source", type=Path, required=True)
    a = p.parse_args()
    sys.path.insert(0, str(a.api_source.resolve()))
    import psycopg
    from app.core.guest_chat import validate_key
    from app.infrastructure.repositories.postgres import PostgresDatabase
    from app.release import (
        guest_chat_migration,
        lean_generation_models_migration,
        proof_generation_settings_migration,
    )
    from app.release.chat_migration import ChatMigrator
    from app.release.local_legacy_database_release import LocalLegacyDatabaseRelease
    from app.release.natural_sketch_catalog_migration import _validate_artifacts
    from app.release.recipe_proof_candidate_source_migration import (
        RecipeProofCandidateSourceMigrator,
    )
    from app.release.semantic_review_migration import SemanticReviewMigrator
    from psycopg import sql
    from psycopg.types.json import Jsonb

    def env(name):
        return dict(
            line.split("=", 1)
            for line in (a.runtime_dir / name).read_text().splitlines()
            if line and not line.startswith("#")
        )

    local, recipe = env("local.env"), env("recipe.env")
    url = local["PALS_HOST_DATABASE_URL"]
    parts = validate_local_dsn(url)
    selector_url = runtime_login_url(
        recipe["PALS_RECIPE_CATALOG_SELECTOR_DATABASE_URL"]
    )
    reader_url = runtime_login_url(recipe["PALS_PFI_DRAFT_READER_DATABASE_URL"])
    if local.get("PALS_ENV") != "local":
        raise ValueError("explicit_dedicated_local_database_required")
    base = urlunsplit(parts._replace(path="/pals_reliability_test"))
    with psycopg.connect(base, autocommit=True) as c:
        if not c.execute("SELECT 1 FROM pg_database WHERE datname='pals'").fetchone():
            c.execute("CREATE DATABASE pals")
        for role in (
            "pals_api_schema_owner",
            "pals_api_runtime",
            "pals_draft_reader",
            "pals_natural_draft_reader",
        ):
            row = c.execute(
                "SELECT rolcanlogin,rolsuper,rolcreaterole,rolcreatedb,rolreplication,rolbypassrls FROM pg_roles WHERE rolname=%s",
                (role,),
            ).fetchone()
            if row is None:
                c.execute(
                    sql.SQL(
                        "CREATE ROLE {} NOLOGIN NOINHERIT NOSUPERUSER NOCREATEROLE NOCREATEDB NOREPLICATION NOBYPASSRLS"
                    ).format(sql.Identifier(role))
                )
            elif row != (False,) * 6:
                raise ValueError("incompatible_existing_local_role")
    with psycopg.connect(url) as c:
        empty = c.execute(
            "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'"
        ).fetchone() == (0,)
    if empty:
        with psycopg.connect(url) as c:
            c.execute("CREATE EXTENSION IF NOT EXISTS vector")
            c.execute("GRANT USAGE,CREATE ON SCHEMA public TO pals_api_schema_owner")
            c.execute("SET LOCAL ROLE pals_api_schema_owner")
            artifacts = _validate_artifacts()
            c.execute(artifacts.sql_bytes.decode())
            for d in artifacts.rows:
                c.execute(
                    "INSERT INTO public.dsp_drafts VALUES(%s,%s,%s,%s,%s,%s::public.vector)",
                    (
                        d.id,
                        d.canonical_statement,
                        d.openmath_xml,
                        d.proof_strategy,
                        Jsonb(list(d.sketch_steps)),
                        d.embedding_text,
                    ),
                )
            c.execute(
                "INSERT INTO public.pals_agent_draft_catalog_metadata VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                ("dsp_drafts", *artifacts.binding),
            )
            c.execute(
                "INSERT INTO public.pals_natural_sketch_catalog_import VALUES(true,%s,%s,%s,%s,%s)",
                (
                    artifacts.manifest_sha256,
                    artifacts.data_sha256,
                    artifacts.sql_sha256,
                    artifacts.content_sha256,
                    len(artifacts.rows),
                ),
            )
        db = PostgresDatabase(url)
        db.initialize()
        db.initialize_target_schema()
        canonical = (
            a.api_source / "app/db/migrations/canonical/001_proof_job_runtime.sql"
        ).read_text()
        predicate = (
            "CREATE FUNCTION public.pals_verifier_attestation_is_bound("
            + canonical.split(
                "CREATE FUNCTION public.pals_verifier_attestation_is_bound(", 1
            )[1].split("$$;", 1)[0]
            + "$$;"
        )
        with psycopg.connect(url) as c:
            c.execute(predicate)
        for cls in (
            ChatMigrator,
            SemanticReviewMigrator,
            RecipeProofCandidateSourceMigrator,
        ):
            if cls(url).apply().status != "installed":
                raise ValueError("local_foundation_migration_failed")

    result = LocalLegacyDatabaseRelease(
        url,
        environment="local",
        contract="legacy-local-v1",
        selector_database_url=selector_url,
        draft_reader_database_url=reader_url,
    ).apply()
    if result.status != "current":
        raise ValueError("actual_local_legacy_release_failed")
    with psycopg.connect(url) as c, c.cursor() as cursor:
        cursor.execute("SELECT 1")
        for module in (
            lean_generation_models_migration,
            proof_generation_settings_migration,
        ):
            module.apply_storage(cursor)
        guest_chat_migration.apply_storage(
            cursor, validate_key(local["PALS_GUEST_HASH_KEY"])
        )
    from app.release.typed_catalog import install

    install(url)
    print(
        json.dumps(
            {
                "state": "actual_local_schema_ready",
                "profile": "legacy-local-v1 + model/settings/guest/typed catalog",
                "preserved_existing_data": not empty,
            }
        )
    )


if __name__ == "__main__":
    main()
