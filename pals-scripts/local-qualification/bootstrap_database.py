"""Real local legacy fixture/migrations; never production admission or synthetic answers."""

from __future__ import annotations

import argparse
import ast
import importlib
import inspect
import json
import re
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


# ``postgres`` exists on every initialised server. The second name is the default
# database of the container this stack was first created with and is kept as a fallback.
MAINTENANCE_DATABASES = ("postgres", "pals_reliability_test")
SCHEMA_OWNER = "pals_api_schema_owner"
# The row locks the candidate's definer functions take (database_readiness.FUNCTIONS).
# PostgreSQL requires UPDATE on a column for a locking read, including FOR SHARE.
ROWLOCK_COLUMNS = (
    ("proof_verification_candidates", "candidate_id"),
    ("proof_explanations", "proof_job_id"),
)
SERVING_BOOTSTRAP = "app/infrastructure/bootstrap.py"


def connect_maintenance(parts, *, connect):
    """Autocommit connection to a maintenance database of the dedicated local server."""
    for name in MAINTENANCE_DATABASES:
        try:
            return connect(urlunsplit(parts._replace(path="/" + name)), autocommit=True)
        except Exception as error:  # noqa: BLE001 - psycopg is imported by the caller only.
            if type(error).__name__ != "OperationalError":
                raise
    raise ValueError("local_maintenance_database_unavailable")


def grant_rowlock_privileges(connection):
    """Exactly the column privileges the readiness check requires; never the table.

    Local database only (the caller validated the closed local DSN). Idempotent: GRANT
    of a held privilege changes nothing. A table-level UPDATE is refused, not revoked.
    """
    granted = []
    for table, column in ROWLOCK_COLUMNS:
        # Closed constants above, checked anyway before they are placed in a statement.
        if not all(re.fullmatch(r"[a-z][a-z_]{0,62}", x) for x in (table, column)):
            raise ValueError("closed_rowlock_identifier_required")
        relation = "public." + table
        if connection.execute(
            "SELECT has_table_privilege(%s,%s,'UPDATE')", (SCHEMA_OWNER, relation)
        ).fetchone() != (False,):
            raise ValueError("local_rowlock_table_update_too_broad:" + table)
        connection.execute(
            'GRANT UPDATE ("%s") ON public."%s" TO "%s"' % (column, table, SCHEMA_OWNER)
        )
        if connection.execute(
            "SELECT has_column_privilege(%s,%s,%s,'UPDATE'),has_table_privilege(%s,%s,'UPDATE')",
            (SCHEMA_OWNER, relation, column, SCHEMA_OWNER, relation),
        ).fetchone() != (True, False):
            raise ValueError("local_rowlock_grant_failed:" + table)
        granted.append(table + "." + column)
    return granted


def serving_preflight_modules(api_source):
    """Modules whose ``preflight`` the candidate's serving start imports, in source order.

    Read from the candidate's own serving bootstrap, so a release that adds a required
    migration is noticed here without this file naming it.
    """
    tree = ast.parse((Path(api_source) / SERVING_BOOTSTRAP).read_text())
    modules = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            if any(alias.name == "preflight" for alias in node.names):
                modules.append(node.module)
    return modules


def _takes_only_database_url(function):
    try:
        parameters = list(inspect.signature(function).parameters.values())
    except (TypeError, ValueError):
        return False
    return (
        len(parameters) == 1
        and parameters[0].name == "database_url"
        and parameters[0].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    )


def migrator_candidates(api_source, module_name):
    """Release modules that can install what ``module_name``'s preflight checks.

    The preflight's own module when it is a release module, and every
    ``app/release/*_migration.py`` importing from it. Source text only; nothing is run.
    """
    candidates = []
    if module_name.startswith("app.release."):
        candidates.append(module_name)
    for file in sorted((Path(api_source) / "app/release").glob("*_migration.py")):
        tree = ast.parse(file.read_text())
        if any(
            isinstance(node, ast.ImportFrom)
            and node.level == 0
            and node.module == module_name
            for node in ast.walk(tree)
        ):
            candidates.append("app.release." + file.stem)
    return list(dict.fromkeys(candidates))


def release_migrator(api_source, module_name, *, import_module=importlib.import_module):
    """The candidate's own single ``apply(database_url)``; anything else is not guessed."""
    found = []
    for name in migrator_candidates(api_source, module_name):
        function = getattr(import_module(name), "apply", None)
        if callable(function) and _takes_only_database_url(function):
            found.append((name, function))
    return found[0] if len(found) == 1 else None


def apply_serving_migrators(api_source, url, *, import_module=importlib.import_module):
    """Run every serving preflight; install only what fails, with the candidate's code.

    Never stricter than serving itself: a failing preflight without exactly one
    discoverable migrator is reported, and the API's own start remains the judge.
    """
    report = {}
    for module_name in serving_preflight_modules(api_source):
        preflight = getattr(import_module(module_name), "preflight", None)
        if not callable(preflight) or not _takes_only_database_url(preflight):
            report[module_name] = "not_checked_other_signature"
            continue
        try:
            preflight(url)
            report[module_name] = "current"
            continue
        except Exception:  # noqa: BLE001 - Any refusal of the read-only check means "not installed".
            pass
        migrator = release_migrator(
            api_source, module_name, import_module=import_module
        )
        if migrator is None:
            report[module_name] = "failing_no_discoverable_migrator"
            continue
        name, function = migrator
        function(url)
        try:
            preflight(url)
        except Exception:  # noqa: BLE001 - Closed code; the cause is the candidate's own.
            raise ValueError("local_serving_migration_failed:" + name) from None
        report[module_name] = "installed_by:" + name
    return report


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
    with connect_maintenance(parts, connect=psycopg.connect) as c:
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
    serving = apply_serving_migrators(a.api_source.resolve(), url)
    with psycopg.connect(url) as c:
        rowlocks = grant_rowlock_privileges(c)
    print(
        json.dumps(
            {
                "state": "actual_local_schema_ready",
                "profile": "legacy-local-v1 + model/settings/guest/typed catalog",
                "preserved_existing_data": not empty,
                "serving_migrators": serving,
                "rowlock_column_grants": rowlocks,
            }
        )
    )


if __name__ == "__main__":
    main()
