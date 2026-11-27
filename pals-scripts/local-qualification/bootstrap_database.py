"""Real local legacy fixture/migrations; never production admission or synthetic answers."""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib
import inspect
import json
import os
import re
import stat
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


LOCAL_HOST_PORT = {"singleton": 55432, "primary": 55434, "standby": 55433}


def validate_local_dsn(value, *, service=False, lane="singleton"):
    if lane not in LOCAL_HOST_PORT:
        raise ValueError("closed_local_database_lane_required")
    parts = urlsplit(value)
    hosts = ("postgres",) if service else ("127.0.0.1", "localhost")
    if (
        parts.scheme != "postgresql"
        or parts.hostname not in hosts
        or parts.port != (5432 if service else LOCAL_HOST_PORT[lane])
        or parts.path != "/pals"
        or parts.query
        or parts.fragment
        or not parts.username
        or not parts.password
    ):
        raise ValueError("closed_local_database_uri_required")
    return parts


def runtime_login_url(value, *, lane="singleton"):
    parts = validate_local_dsn(value, service=True, lane=lane)
    result = urlunsplit(
        parts._replace(netloc=f"{parts.netloc.rsplit('@', 1)[0]}@127.0.0.1:{LOCAL_HOST_PORT[lane]}")
    )
    validate_local_dsn(result, lane=lane)
    return result


def qualify_lane_postgres(runtime_directory, lane, binding_path, binding_sha256):
    """Bind migrations to the owned lane PostgreSQL before opening any connection."""
    from lane_topology import OWNER, PROJECT, SERVICE, active, docker_reader, inventory, port_map
    from lane_database import SCHEMA as DATABASE_LAYOUT, read_for_bootstrap, verify_databases

    layout = read_for_bootstrap(binding_path, binding_sha256)
    selected = layout["lanes"][lane]
    if Path(selected["runtime_directory"]) != runtime_directory.resolve():
        raise ValueError("local_lane_database_runtime_path_differs")
    database = selected["postgres"]
    run = docker_reader(layout["docker_socket"])
    rows = inventory(run)
    if layout["schema_version"] == DATABASE_LAYOUT:
        verify_databases(layout, run, rows)
        return selected["candidate_sha256"]
    actual = rows.get("/" + database["name"])
    if actual is None or actual["id"] != database["container_id"]:
        raise ValueError("local_lane_database_container_differs")
    labels = actual["labels"] or {}
    project = selected["compose_project"]
    if (
        labels.get(OWNER_LABEL) != OWNER or labels.get(PROJECT) != project
        or labels.get(SERVICE) != "postgres" or actual["privileged"] is not False
        or set(actual["networks"] or {}) != {project + "-database"}
    ):
        raise ValueError("owned_local_lane_database_required")
    active(actual, postgres=True)
    port_map(actual, {"5432/tcp": [{"HostIp": database["host"], "HostPort": str(database["host_port"])}]})
    idle_roles = {"api", "reconciler", "worker", "assessment-worker", "recipe-reviewer"}
    if any(
        row["running"] and (row["labels"] or {}).get(PROJECT) == project
        and (row["labels"] or {}).get(SERVICE) in idle_roles for row in rows.values()
    ):
        raise ValueError("local_lane_database_producers_must_be_stopped")
    peer = next(value for role, value in layout["lanes"].items() if role != lane)
    peer_actual = rows.get("/" + peer["postgres"]["name"])
    if peer_actual is None or peer_actual["id"] != peer["postgres"]["container_id"]:
        raise ValueError("local_lane_peer_database_container_differs")
    volumes = set()
    for row, compose_project in ((actual, project), (peer_actual, peer["compose_project"])):
        name = compose_project + "-postgres-data"
        data = [mount for mount in row["mounts"] or [] if mount["Destination"] == "/var/lib/postgresql/data"]
        if len(data) != 1 or data[0].get("Type") != "volume" or data[0].get("Name") != name or data[0].get("RW") is not True:
            raise ValueError("separate_owned_local_lane_database_volumes_required")
        volume = json.loads(run("volume", "inspect", name))
        if (
            len(volume) != 1 or volume[0].get("Name") != name or volume[0].get("Driver") != "local"
            or volume[0].get("Options") or volume[0].get("Mountpoint") != data[0].get("Source")
        ):
            raise ValueError("separate_owned_local_lane_database_volumes_required")
        volumes.add(volume[0]["Mountpoint"])
    if len(volumes) != 2:
        raise ValueError("separate_owned_local_lane_database_volumes_required")
    return selected["candidate_sha256"]


def require_lane_migration_source(api_source, manifest, candidate_sha256, *, full_checkout=False):
    raw = manifest.read_bytes()
    if hashlib.sha256(raw).hexdigest() != candidate_sha256:
        raise ValueError("local_lane_migration_manifest_differs")
    revision = json.loads(raw)["source_commits"]["pals-api"]
    root = api_source.resolve(strict=True)
    prefix = ["git", "-C", str(root)]
    head = subprocess.run([*prefix, "rev-parse", "HEAD"], capture_output=True, text=True, check=True, timeout=10)
    dirty = subprocess.run(
        [*prefix, "status", "--porcelain", "--untracked-files=all", *([] if full_checkout else ["--", "app"])],
        capture_output=True, text=True, check=True, timeout=10,
    )
    if head.stdout.strip() != revision or dirty.stdout.strip():
        raise ValueError("exact_clean_lane_api_migration_source_required")


# ``postgres`` exists on every initialised server. The second name is the default
# database of the container this stack was first created with and is kept as a fallback.
MAINTENANCE_DATABASES = ("postgres", "pals_reliability_test")
OWNER_LABEL = "codex.owner"
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
    Returns the status per preflight module and the names of the modules this
    bootstrap can NOT install whatever their state, because no single module-level
    ``apply(database_url)`` exists for them.
    """
    report = {}
    not_applicable = []
    for module_name in serving_preflight_modules(api_source):
        preflight = getattr(import_module(module_name), "preflight", None)
        try:
            migrator = release_migrator(
                api_source, module_name, import_module=import_module
            )
        except Exception:  # noqa: BLE001 - An unimportable candidate is not a migrator.
            migrator = None
        if migrator is None:
            not_applicable.append(module_name)
        if not callable(preflight) or not _takes_only_database_url(preflight):
            report[module_name] = "not_checked_other_signature"
            continue
        try:
            preflight(url)
            report[module_name] = "current"
            continue
        except Exception:  # noqa: BLE001 - Any refusal of the read-only check means "not installed".
            pass
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
    return report, not_applicable


COUPON_MODULE = "app.release.plus_coupons_migration"
COUPON_HELPER = "app/release/plus_coupons_migration.py"
COUPON_SQL = "app/db/migrations/plus_coupons/001_plus_coupons.sql"
COUPON_MANIFEST = "app/db/migrations/plus_coupons/manifest.json"
COUPON_SQL_SHA256 = "b21487c769fcf31b6de656be4b0a9caf6c91d699dbbc2a4f9315bad84f62d078"
COUPON_SCHEMA_SHA256 = (
    "e79ae61f6d24c57c8a781116563c5fecde3cd1b2c16934438d2a47cdc3d08b43"
)


def coupon_source_contract(api_source):
    """Inspect only tracked source bytes; never import an API or touch a database."""
    root = Path(api_source).resolve()
    try:
        revision = (
            subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                capture_output=True,
                check=True,
                timeout=15,
            )
            .stdout.decode()
            .strip()
        )
        if not re.fullmatch(r"[a-f0-9]{40}", revision):
            raise ValueError
        files = {}
        raw = {}
        for name in (COUPON_HELPER, COUPON_SQL, COUPON_MANIFEST):
            path = root / name
            if path.is_symlink() or not path.is_file() or path.resolve() != path:
                raise ValueError
            raw[name] = path.read_bytes()
            tracked = subprocess.run(
                ["git", "-C", str(root), "show", revision + ":" + name],
                capture_output=True,
                check=True,
                timeout=15,
            ).stdout
            if tracked != raw[name]:
                raise ValueError
            files[name] = hashlib.sha256(raw[name]).hexdigest()
        if files[COUPON_SQL] != COUPON_SQL_SHA256:
            raise ValueError
        manifest = json.loads(raw[COUPON_MANIFEST])
        if manifest != {
            "schema_version": "pals.plus-coupons-migrations.v1",
            "postgresql_major": 16,
            "schema_sha256": COUPON_SCHEMA_SHA256,
            "files": [{"path": COUPON_SQL, "sha256": COUPON_SQL_SHA256}],
        }:
            raise ValueError
        tree = ast.parse(raw[COUPON_HELPER])
        functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
        for name, arguments in (
            ("canonical_sql", []),
            ("apply_local_storage", ["c"]),
            ("current", ["c"]),
        ):
            f = functions[name].args
            if (
                f.posonlyargs
                or [a.arg for a in f.args] != arguments
                or f.defaults
                or f.kwonlyargs
                or f.vararg
                or f.kwarg
            ):
                raise ValueError
    except (OSError, ValueError, KeyError, SyntaxError, subprocess.SubprocessError):
        raise ValueError("coupon_local_bootstrap_unsupported_api") from None
    return {
        "schema_version": "pals.local-plus-coupons-bootstrap.v1",
        "api_source_revision": revision,
        "files": files,
        "schema_sha256": COUPON_SCHEMA_SHA256,
    }


def coupon_bootstrap_plan(api_source, local, *, enabled):
    flag = local.get("PALS_PLUS_COUPONS_ENABLED")
    if flag not in (None, "false", "true"):
        raise ValueError("coupon_local_flag_invalid")
    if not enabled:
        if flag == "true":
            raise ValueError("coupon_local_explicit_opt_in_required")
        return None
    if local.get("PALS_ENV") != "local":
        raise ValueError("explicit_dedicated_local_database_required")
    return coupon_source_contract(api_source)


@contextmanager
def _local_coupon_environment():
    previous = os.environ.get("PALS_ENV")
    os.environ["PALS_ENV"] = "local"
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("PALS_ENV", None)
        else:
            os.environ["PALS_ENV"] = previous


def apply_coupon_storage(cursor, api_source, plan):
    """Use the candidate's own local installer in the caller's live transaction."""
    if plan is None:
        return None
    if coupon_source_contract(api_source) != plan:
        raise ValueError("coupon_local_source_changed_after_plan")
    if getattr(cursor.connection.info.transaction_status, "name", None) != "INTRANS":
        raise ValueError("coupon_local_transaction_required")
    module = importlib.import_module(COUPON_MODULE)
    if Path(module.__file__).resolve() != Path(api_source).resolve() / COUPON_HELPER:
        raise ValueError("coupon_local_module_source_mismatch")
    with _local_coupon_environment():
        changed = module.apply_local_storage(cursor)
        if type(changed) is not bool or module.current(cursor) is not True:
            raise ValueError("coupon_local_storage_not_current")
    return {**plan, "state": "installed" if changed else "current"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--runtime-dir", type=Path, required=True)
    p.add_argument("--api-source", type=Path, required=True)
    p.add_argument("--enable-plus-coupons", action="store_true")
    p.add_argument("--lane", choices=("primary", "standby"))
    p.add_argument("--lane-binding", type=Path)
    p.add_argument("--lane-binding-sha256")
    p.add_argument("--lane-candidate-manifest", type=Path)
    a = p.parse_args()
    lane_options = (a.lane, a.lane_binding, a.lane_binding_sha256, a.lane_candidate_manifest)
    if any(lane_options):
        if not all(lane_options):
            p.error("the lane, binding, binding SHA-256 and candidate manifest are required together")
        from lane_database import SCHEMA as DATABASE_LAYOUT, migration_state, read_for_bootstrap

        layout = read_for_bootstrap(a.lane_binding, a.lane_binding_sha256)
        if layout["schema_version"] == DATABASE_LAYOUT:
            from lane_bootstrap import local_environment_settings
            from lane_dependencies import runtime_directory

            selected = layout["lanes"][a.lane]
            runtime = runtime_directory(Path(selected["runtime_directory"]))
            if a.runtime_dir != runtime:
                raise ValueError("local_lane_database_runtime_path_differs")
            if any(name.startswith("PG") for name in os.environ):
                raise ValueError("lane_database_ambient_postgres_environment_refused")
            local = local_environment_settings(selected["local_env"], runtime, a.lane)
            with migration_state(runtime, selected) as begin:
                candidate = qualify_lane_postgres(runtime, a.lane, a.lane_binding, a.lane_binding_sha256)
                require_lane_migration_source(a.api_source, a.lane_candidate_manifest, candidate, full_checkout=True)
                result = migrate_database(a, a.lane, local=local, begin=begin)
            print(json.dumps(result))
            return
        candidate = qualify_lane_postgres(a.runtime_dir, a.lane, a.lane_binding, a.lane_binding_sha256)
        require_lane_migration_source(a.api_source, a.lane_candidate_manifest, candidate)
    print(json.dumps(migrate_database(a, a.lane or "singleton")))


def migrate_database(a, lane, *, local=None, begin=None):
    # Unsupported opt-in is refused before imports or any database operation.
    if a.enable_plus_coupons:
        coupon_source_contract(a.api_source)
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
        path = a.runtime_dir / name
        if begin is None:
            raw = path.read_text()
        else:
            with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as stream:
                info = os.fstat(stream.fileno())
                if (
                    not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
                    or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o600
                    or not 0 < info.st_size <= 16_384
                ):
                    raise ValueError("private_lane_database_recipe_environment_required")
                raw = stream.read(16_385).decode()
        pairs = [line.split("=", 1) for line in raw.splitlines() if line and not line.startswith("#")]
        values = dict(pairs)
        if begin is not None and len(values) != len(pairs):
            raise ValueError("private_lane_database_recipe_environment_required")
        return values

    if local is None:
        local = env("local.env")
    recipe = env("recipe.env")
    url = local["PALS_HOST_DATABASE_URL"]
    parts = validate_local_dsn(url, lane=lane)
    selector_url = runtime_login_url(
        recipe["PALS_RECIPE_CATALOG_SELECTOR_DATABASE_URL"], lane=lane,
    )
    reader_url = runtime_login_url(recipe["PALS_PFI_DRAFT_READER_DATABASE_URL"], lane=lane)
    if local.get("PALS_ENV") != "local":
        raise ValueError("explicit_dedicated_local_database_required")
    coupon_plan = coupon_bootstrap_plan(
        a.api_source, local, enabled=a.enable_plus_coupons
    )
    if coupon_plan and local.get("PALS_PLUS_COUPONS_ENABLED") != "true":
        raise ValueError("coupon_local_runtime_flag_required")
    if begin is not None:
        # A fresh dependency has already created /pals. Confirm the exact lane
        # identity through a read-only query before maintenance opens or writes.
        with psycopg.connect(url, connect_timeout=5,
                             options="-c default_transaction_read_only=on -c statement_timeout=5000") as c:
            identity = c.execute(
                "SELECT current_database(), current_user, "
                "current_setting('server_version_num')::int / 10000, "
                "inet_server_port(), pg_is_in_recovery()"
            ).fetchone()
            if identity != ("pals", f"pals_qual_{lane}", 16, 5432, False):
                raise ValueError("local_lane_database_connection_identity_differs")
            fresh = c.execute(
                "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'"
            ).fetchone() == (0,)
        begin(fresh)
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
    coupon_storage = None
    with psycopg.connect(url) as c, c.transaction(), c.cursor() as cursor:
        cursor.execute("SELECT 1")
        for module in (
            lean_generation_models_migration,
            proof_generation_settings_migration,
        ):
            module.apply_storage(cursor)
        guest_chat_migration.apply_storage(
            cursor, validate_key(local["PALS_GUEST_HASH_KEY"])
        )
        coupon_storage = apply_coupon_storage(cursor, a.api_source, coupon_plan)
    from app.release.typed_catalog import install

    install(url)
    serving, not_applicable = apply_serving_migrators(a.api_source.resolve(), url)
    if begin is not None and "failing_no_discoverable_migrator" in serving.values():
        raise ValueError("lane_database_serving_schema_requires_inspection")
    with psycopg.connect(url) as c:
        rowlocks = grant_rowlock_privileges(c)
    return {
        "state": "actual_local_schema_ready",
        "profile": "legacy-local-v1 + model/settings/guest/typed catalog",
        "preserved_existing_data": not empty,
        "serving_migrators": serving,
        "not_applicable_migrators": not_applicable,
        "rowlock_column_grants": rowlocks,
        **({"plus_coupons": coupon_storage} if coupon_plan else {}),
    }


if __name__ == "__main__":
    main()
