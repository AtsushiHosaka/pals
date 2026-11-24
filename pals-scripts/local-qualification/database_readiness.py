"""Read actual local canonical definer/ACL/schema state; no grants, rows or attestations written."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
from pathlib import Path

import bootstrap_database
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


# The Plus coupon schema is a separate, optional contract. Its observation, and the key
# that freezes it, never enter ``inspect``: the Draft contract above keeps its bytes.
COUPON_SCHEMA = "pals_plus_coupons"
COUPON_OWNER = "pals_api_schema_owner"
COUPON_OPERATOR_ROLE = "pals_billing_test_admin"
COUPON_RUNTIME_ROLE = "pals_api_runtime"
COUPON_SEARCH_PATH = "search_path=pg_catalog,pals_plus_coupons"
# Function -> the only roles, besides the owner, that may execute it. Never PUBLIC.
COUPON_FUNCTIONS = (
    (
        "issue(uuid,text,integer,integer,integer,timestamptz,text)",
        True,
        COUPON_OPERATOR_ROLE,
    ),
    ("redeem(text,text,uuid)", True, COUPON_RUNTIME_ROLE),
    ("revoke_code(uuid,text)", True, COUPON_OPERATOR_ROLE),
    ("revoke_grant(uuid,text)", True, COUPON_OPERATOR_ROLE),
    ("access_end(timestamptz,integer,integer)", False, None),
    ("append_only()", False, None),
)
# Table -> the only roles, besides the owner, with SELECT. No other privilege is held.
COUPON_TABLES = (
    ("code_revocations", (COUPON_OPERATOR_ROLE,)),
    ("codes", (COUPON_OPERATOR_ROLE,)),
    ("grant_revocations", (COUPON_OPERATOR_ROLE, COUPON_RUNTIME_ROLE)),
    ("redemptions", (COUPON_OPERATOR_ROLE, COUPON_RUNTIME_ROLE)),
)
COUPON_TABLE_PRIVILEGES = ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE")


def coupon_helper(source):
    """The candidate's own readback helper, loaded from the bytes the plan verified."""
    path = Path(source).resolve() / bootstrap_database.COUPON_HELPER
    spec = importlib.util.spec_from_file_location("pals_plus_coupons_readback", path)
    if spec is None or spec.loader is None:
        raise ValueError("actual_local_plus_coupon_helper_unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if (
        type(getattr(module, "SCHEMA", None)) is not str
        or module.SCHEMA != COUPON_SCHEMA
        or not callable(getattr(module, "current", None))
        or not callable(getattr(module, "fingerprint", None))
    ):
        raise ValueError("actual_local_plus_coupon_helper_unavailable")
    return module


FUNCTION_ACL_SQL = (
    "SELECT COALESCE(r.rolname,'PUBLIC'),a.privilege_type FROM pg_proc p "
    "CROSS JOIN LATERAL aclexplode(COALESCE(p.proacl,acldefault('f',p.proowner))) a "
    "LEFT JOIN pg_roles r ON r.oid=a.grantee WHERE p.oid=to_regprocedure(%s)"
)
TABLE_ACL_SQL = (
    "SELECT COALESCE(r.rolname,'PUBLIC'),a.privilege_type FROM pg_class c "
    "CROSS JOIN LATERAL aclexplode(COALESCE(c.relacl,acldefault('r',c.relowner))) a "
    "LEFT JOIN pg_roles r ON r.oid=a.grantee WHERE c.oid=to_regclass(%s)"
)


def _grants(cursor, query, target):
    return sorted(
        (str(who), str(privilege))
        for who, privilege in cursor.execute(query, (target,)).fetchall()
    )


def inspect_plus_coupons(url, source, revision, *, connect=None):
    """Read the installed Plus coupon schema, ACL and definers of a started local API.

    Read only. The candidate's own ``fingerprint`` must equal the signed manifest hash;
    every function owner/definer/search path/EXECUTE grant and every table privilege is
    observed again here so a legible, separate fact is frozen. Writes nothing.
    """
    validate_local_dsn(url)
    plan = bootstrap_database.coupon_source_contract(source)
    if plan["api_source_revision"] != revision:
        raise ValueError("actual_local_plus_coupon_source_revision_changed")
    helper = coupon_helper(source)
    if connect is None:
        import psycopg

        connect = psycopg.connect
    functions = []
    tables = []
    with connect(url) as connection:
        connection.execute("SET TRANSACTION READ ONLY")
        connection.execute("SET LOCAL statement_timeout='5s'")
        cursor = connection.cursor()
        if helper.current(cursor) is not True:
            raise ValueError("actual_local_plus_coupon_schema_not_current")
        observed = helper.fingerprint(cursor)
        if observed != plan["schema_sha256"]:
            raise ValueError("actual_local_plus_coupon_schema_changed")
        comment = cursor.execute(
            "SELECT obj_description(oid,'pg_namespace') FROM pg_namespace WHERE nspname=%s",
            (COUPON_SCHEMA,),
        ).fetchone()
        if comment != ("pals.plus-coupons.v1",):
            raise ValueError("actual_local_plus_coupon_schema_changed")
        for signature, definer, grantee in COUPON_FUNCTIONS:
            row = cursor.execute(
                "SELECT p.prosecdef,pg_get_userbyid(p.proowner),p.proconfig,"
                "r.rolcanlogin,r.rolsuper,r.rolbypassrls,md5(p.prosrc) "
                "FROM pg_proc p JOIN pg_roles r ON r.oid=p.proowner "
                "WHERE p.oid=to_regprocedure(%s)",
                (COUPON_SCHEMA + "." + signature,),
            ).fetchone()
            if row is None:
                raise ValueError("actual_local_plus_coupon_function_absent")
            expected_acl = sorted(
                [(COUPON_OWNER, "EXECUTE")]
                + ([(grantee, "EXECUTE")] if grantee else [])
            )
            acl = _grants(cursor, FUNCTION_ACL_SQL, COUPON_SCHEMA + "." + signature)
            config = ["".join(x.split()) for x in (row[2] or [])]
            if (
                row[0] != definer
                or row[1] != COUPON_OWNER
                or row[3:6] != (False, False, False)
                or (definer and config != [COUPON_SEARCH_PATH])
                or acl != expected_acl
            ):
                raise ValueError("actual_local_plus_coupon_function_acl_changed")
            functions.append(
                {
                    "signature": signature,
                    "security_definer": row[0],
                    "owner": row[1],
                    "owner_nologin": not row[3],
                    "search_path": config,
                    "body_md5": row[6],
                    "execute": acl,
                }
            )
        for table, readers in COUPON_TABLES:
            relation = COUPON_SCHEMA + "." + table
            row = cursor.execute(
                "SELECT pg_get_userbyid(c.relowner) FROM pg_class c "
                "WHERE c.oid=to_regclass(%s)",
                (relation,),
            ).fetchone()
            if row != (COUPON_OWNER,):
                raise ValueError("actual_local_plus_coupon_table_acl_changed")
            grants = _grants(cursor, TABLE_ACL_SQL, relation)
            owner_grants = sorted(
                (COUPON_OWNER, privilege)
                for privilege in (
                    "DELETE",
                    "INSERT",
                    "REFERENCES",
                    "SELECT",
                    "TRIGGER",
                    "TRUNCATE",
                    "UPDATE",
                )
            )
            expected = sorted(owner_grants + [(role, "SELECT") for role in readers])
            if grants != expected:
                raise ValueError("actual_local_plus_coupon_table_acl_changed")
            effective = {}
            for role in (COUPON_RUNTIME_ROLE, COUPON_OPERATOR_ROLE):
                effective[role] = [
                    privilege
                    for privilege in COUPON_TABLE_PRIVILEGES
                    if cursor.execute(
                        "SELECT has_table_privilege(%s,%s,%s)",
                        (role, relation, privilege),
                    ).fetchone()
                    == (True,)
                ]
                if effective[role] != (["SELECT"] if role in readers else []):
                    raise ValueError("actual_local_plus_coupon_table_acl_changed")
            tables.append({"table": table, "acl": grants, "effective": effective})
    result = {
        "scope": "local_plus_coupon_schema_acl_readback_not_production_admission",
        "api_source_revision": plan["api_source_revision"],
        "source_files": plan["files"],
        "schema_sha256": observed,
        "functions": functions,
        "tables": tables,
    }
    result["plus_coupons_schema_fingerprint_sha256"] = sha(
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    )
    return result
