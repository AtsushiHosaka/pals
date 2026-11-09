"""Read actual local canonical definer/ACL/schema state; no grants, rows or attestations written."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess

from bootstrap_database import validate_local_dsn

DIRECTORY = "app/db/migrations/draft_addition_candidates"
FUNCTIONS = (
    (
        "record_verification(text,text)",
        "proof_verification_candidates",
        "candidate_id",
        True,
    ),
    ("capture_input(text)", "proof_explanations", "proof_job_id", False),
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def source_contract(source, revision):
    raw = (source / DIRECTORY / "001_candidates.sql").read_bytes()
    manifest = json.loads((source / DIRECTORY / "manifest.json").read_bytes())
    if manifest != {
        "schema_version": "pals.draft-addition-candidate-migrations.v1",
        "postgresql_major": 16,
        "files": [{"path": DIRECTORY + "/001_candidates.sql", "sha256": sha(raw)}],
    }:
        raise ValueError("local_database_migration_manifest_changed")
    exact = subprocess.run(
        [
            "git",
            "-C",
            str(source),
            "show",
            revision + ":" + DIRECTORY + "/001_candidates.sql",
        ],
        capture_output=True,
        timeout=15,
        check=False,
    )
    if exact.returncode or exact.stdout != raw:
        raise ValueError("local_database_exact_api_sql_changed")
    bodies = {}
    for signature, _, _, _ in FUNCTIONS:
        name = signature.split("(")[0]
        body_match = re.search(
            r"CREATE FUNCTION pals_draft_candidates\."
            + name
            + r"\([^;]+? AS \$\$(.*?)\$\$;",
            raw.decode(),
            re.DOTALL,
        )
        if body_match is None:
            raise ValueError("canonical_database_function_absent")
        bodies[signature] = body_match.group(1)
    return bodies, sha(raw)


def inspect(url, source, revision):
    import psycopg

    validate_local_dsn(url)
    bodies, sql_sha = source_contract(source, revision)
    observations = []
    with psycopg.connect(url) as c:
        c.execute("SET TRANSACTION READ ONLY")
        c.execute("SET LOCAL statement_timeout='5s'")
        migration = c.execute(
            "SELECT sql_sha256,schema_sha256 FROM pals_draft_candidates.schema_revision WHERE singleton"
        ).fetchone()
        if not migration or migration[0] != sql_sha:
            raise ValueError("actual_local_migration_revision_changed")
        for signature, table, column, requires_insert in FUNCTIONS:
            row = c.execute(
                "SELECT p.prosrc,p.prosecdef,pg_get_userbyid(p.proowner),p.proconfig,r.rolcanlogin,r.rolsuper,r.rolbypassrls FROM pg_proc p JOIN pg_roles r ON r.oid=p.proowner WHERE p.oid=to_regprocedure(%s)",
                ("pals_draft_candidates." + signature,),
            ).fetchone()
            if (
                not row
                or row[:3] != (bodies[signature], True, "pals_api_schema_owner")
                or ["".join(x.split()) for x in row[3]]
                != ["search_path=pg_catalog,public,pals_draft_candidates"]
                or row[4:] != (False, False, False)
            ):
                raise ValueError("actual_local_function_or_nologin_owner_changed")
            privileges = c.execute(
                "SELECT has_table_privilege(%s,%s,'SELECT'),has_table_privilege(%s,%s,'INSERT'),has_column_privilege(%s,%s,%s,'UPDATE'),has_table_privilege(%s,%s,'UPDATE')",
                (
                    row[2],
                    "public." + table,
                    row[2],
                    "public." + table,
                    row[2],
                    "public." + table,
                    column,
                    row[2],
                    "public." + table,
                ),
            ).fetchone()
            if (
                not privileges[0]
                or (requires_insert and not privileges[1])
                or not privileges[2]
                or privileges[3]
            ):
                raise ValueError(
                    "actual_local_rowlock_privilege_missing_or_broad:" + table
                )
            columns = c.execute(
                "SELECT attname,format_type(atttypid,atttypmod),attnotnull,attacl::text FROM pg_attribute WHERE attrelid=to_regclass(%s) AND attnum>0 AND NOT attisdropped ORDER BY attnum",
                ("public." + table,),
            ).fetchall()
            constraints = c.execute(
                "SELECT conname,pg_get_constraintdef(oid),convalidated FROM pg_constraint WHERE conrelid=to_regclass(%s) ORDER BY conname",
                ("public." + table,),
            ).fetchall()
            observations.append(
                {
                    "signature": signature,
                    "body_sha256": sha(row[0].encode()),
                    "owner": row[2],
                    "security_definer": row[1],
                    "owner_nologin": not row[4],
                    "table": table,
                    "column": column,
                    "privileges": privileges,
                    "columns": columns,
                    "constraints": constraints,
                }
            )
    result = {
        "scope": "local_record_and_capture_dependency_readiness_not_production_admission",
        "migration_sql_sha256": sql_sha,
        "migration_schema_sha256": migration[1],
        "functions": observations,
    }
    result["schema_fingerprint_sha256"] = sha(
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    )
    return result
