#!/usr/bin/env python3
"""Closed, aggregate-only figure readback inside an existing API image.

No URL, SQL, path, ID or role overrides are accepted. This reports database
observations, never rendered-answer or production-release acceptance.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import logging
import os
import re
import signal
import sys
import warnings
from typing import Any

REGISTRY_SHA256 = "16e8d4b6d104489b9373ccbbedae6b09950068f8b1ae836195bfb93a9fffcdc7"
REGISTRY_COUNT = 35
MAX_CATALOG_ROWS = 350
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_RECIPE = re.compile(r"textbook\.[a-z0-9_]+\.[a-z0-9_]+\Z")
CATALOG_QUERY = """SELECT recipe_id, entry_jcs::jsonb->>'answer_sha256'
FROM pals_recipe_search.selectable_entries
WHERE output_language='ja' AND toolchain_sha256=%s AND recipe_id=ANY(%s)
ORDER BY recipe_id COLLATE "C", entry_jcs::jsonb->>'answer_sha256'
LIMIT 351"""
ANSWER_QUERY = """SELECT count(answer),
count(*) FILTER (WHERE jsonb_typeof(answer->'visualization')='object')
FROM public.proof_requests"""
_REASONS = frozenset({
    "arguments_refused", "registry_hash_mismatch", "registry_invalid",
    "active_toolchain_unavailable", "database_configuration_unavailable",
    "existing_process_pools_refused", "readonly_not_confirmed",
    "catalog_row_limit", "catalog_row_invalid", "answer_counts_invalid",
    "runtime_unavailable", "catalog_read_unavailable", "answer_read_unavailable",
    "deadline_exceeded", "pool_cleanup_unavailable",
})


class PolicyError(Exception):
    pass


class DeadlineExceeded(Exception):
    pass


def unavailable(reason: str) -> dict[str, str]:
    # Never stringify exceptions, SQLSTATEs, URLs or arbitrary caller input.
    return {"status": "NOT_VERIFIED", "reason": reason if reason in _REASONS else "runtime_unavailable"}


def registry_entries(raw: bytes) -> dict[str, str]:
    if hashlib.sha256(raw).hexdigest() != REGISTRY_SHA256:
        raise PolicyError("registry_hash_mismatch")
    try:
        value = json.loads(raw)
        rows = value["figures"]
        if value["schema_version"] != "pals.recipe-figures.v1" or len(rows) != REGISTRY_COUNT:
            raise ValueError
        result: dict[str, str] = {}
        for row in rows:
            recipe_id, digest = row["recipe_id"], row["answer_sha256"]
            if not isinstance(recipe_id, str) or not _RECIPE.fullmatch(recipe_id):
                raise ValueError
            if not isinstance(digest, str) or not _SHA.fullmatch(digest) or recipe_id in result:
                raise ValueError
            result[recipe_id] = digest
        return result
    except (TypeError, ValueError, KeyError) as exc:
        raise PolicyError("registry_invalid") from exc


def summarize_catalog(registry: dict[str, str], rows: list[Any]) -> dict[str, Any]:
    if len(rows) > MAX_CATALOG_ROWS:
        raise PolicyError("catalog_row_limit")
    seen: dict[str, list[str]] = {}
    for row in rows:
        if not isinstance(row, (tuple, list)) or len(row) != 2:
            raise PolicyError("catalog_row_invalid")
        recipe_id, digest = row
        if (not isinstance(recipe_id, str) or recipe_id not in registry
                or not isinstance(digest, str) or not _SHA.fullmatch(digest)):
            raise PolicyError("catalog_row_invalid")
        seen.setdefault(recipe_id, []).append(digest)
    ambiguous = sorted(key for key, digests in seen.items() if len(digests) != 1)
    mismatched = sorted(key for key, digests in seen.items()
                        if len(digests) == 1 and digests[0] != registry[key])
    missing = sorted(registry.keys() - seen.keys())
    return {
        "status": "READ_ONLY_OBSERVED", "registry_recipe_count": len(registry),
        "eligible_variant_count": len(rows),
        "matching_recipe_count": len(registry) - len(missing) - len(mismatched) - len(ambiguous),
        "missing_recipe_ids": missing, "mismatched_recipe_ids": mismatched,
        "ambiguous_recipe_ids": ambiguous,
    }


def summarize_answers(row: Any) -> dict[str, Any]:
    if (not isinstance(row, (tuple, list)) or len(row) != 2
            or any(type(count) is not int or not 0 <= count <= 2**63 - 1 for count in row)
            or row[1] > row[0]):
        raise PolicyError("answer_counts_invalid")
    return {"status": "READ_ONLY_OBSERVED", "answer_count": row[0],
            "object_visualization_answer_count": row[1]}


def require_fresh_pools(stats: Any) -> None:
    # Canonical pool_stats always includes the non-pool module counters, even
    # before a connection has been created. Every other key denotes a pool.
    if not isinstance(stats, dict) or set(stats) != {"module"}:
        raise PolicyError("existing_process_pools_refused")


def _readonly(connection: Any) -> None:
    connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
    connection.execute("SET LOCAL statement_timeout='5s'")
    connection.execute("SET LOCAL lock_timeout='1s'")
    if connection.execute("SHOW transaction_read_only").fetchone() != ("on",):
        raise PolicyError("readonly_not_confirmed")


def _reason(error: Exception, default: str) -> str:
    if isinstance(error, DeadlineExceeded):
        return "deadline_exceeded"
    if (isinstance(error, PolicyError) and error.args and isinstance(error.args[0], str)
            and error.args[0] in _REASONS):
        return error.args[0]
    return default


def observe() -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema_version": "pals.figure-aggregate-readback.v1",
        "status": "NOT_VERIFIED", "expected_registry_sha256": REGISTRY_SHA256,
        "boundary": "read-only database aggregates; no rendering or release acceptance",
        "catalog": unavailable("runtime_unavailable"),
        "answers": unavailable("runtime_unavailable"),
    }
    pool_module = None
    owns_pools = False
    try:
        # These imports may validate environment or initialize loggers. The CLI
        # suppresses stdout, stderr, logging and warnings before entering here.
        from app.core.config import Settings
        from app.infrastructure.bootstrap import _configured_active_recipe_toolchain
        from app.infrastructure import db_pool
        from app.domain import recipe_figures

        settings = Settings()
        registry = registry_entries(recipe_figures._PATH.read_bytes())
        report["registry_sha256"] = REGISTRY_SHA256
        active = _configured_active_recipe_toolchain(settings)
        if active is None or not isinstance(active.sha256, str) or not _SHA.fullmatch(active.sha256):
            raise PolicyError("active_toolchain_unavailable")
        report["active_toolchain_sha256"] = active.sha256
        if not settings.database_url:
            raise PolicyError("database_configuration_unavailable")
        require_fresh_pools(db_pool.pool_stats())
        pool_module, owns_pools = db_pool, True
        base_url = settings.database_url.replace("postgresql+psycopg://", "postgresql://", 1)
        selector_url = (settings.recipe_catalog_selector_database_url or settings.database_url).replace(
            "postgresql+psycopg://", "postgresql://", 1)
        try:
            with db_pool.connect(selector_url, connect_timeout=5) as connection:
                _readonly(connection)
                connection.execute("SET LOCAL ROLE pals_api_recipe_catalog_selector")
                rows = connection.execute(CATALOG_QUERY, (active.sha256, sorted(registry))).fetchall()
                report["catalog"] = summarize_catalog(registry, rows)
        except Exception as error:
            report["catalog"] = unavailable(_reason(error, "catalog_read_unavailable"))
            if isinstance(error, DeadlineExceeded):
                raise
        try:
            # Separate connection/transaction: no selector role carries into this read.
            with db_pool.connect(base_url, connect_timeout=5) as connection:
                _readonly(connection)
                report["answers"] = summarize_answers(connection.execute(ANSWER_QUERY).fetchone())
        except Exception as error:
            report["answers"] = unavailable(_reason(error, "answer_read_unavailable"))
    except Exception as error:
        reason = _reason(error, "runtime_unavailable")
        for section in ("catalog", "answers"):
            if report[section]["status"] == "NOT_VERIFIED":
                report[section] = unavailable(reason)
    finally:
        if owns_pools and pool_module is not None:
            try:
                # At most two fresh pools in this standalone process; never a serving process.
                pool_module.close_all(timeout=0.25)
            except Exception:
                report["cleanup"] = unavailable("pool_cleanup_unavailable")
    if (all(report[key]["status"] == "READ_ONLY_OBSERVED" for key in ("catalog", "answers"))
            and "cleanup" not in report):
        report["status"] = "READ_ONLY_OBSERVED"
    return report


def main(argv: list[str] | None = None) -> int:
    if (sys.argv[1:] if argv is None else argv):
        print(json.dumps(unavailable("arguments_refused"), sort_keys=True))
        return 2
    logging.disable(logging.CRITICAL)
    warnings.filterwarnings("ignore")
    previous_handler = None
    if hasattr(signal, "SIGALRM"):
        def expired(_signum: int, _frame: Any) -> None:
            raise DeadlineExceeded
        previous_handler = signal.signal(signal.SIGALRM, expired)
        # Leave one second of the 30-second process budget for bounded pool cleanup.
        signal.alarm(29)
    try:
        with open(os.devnull, "w") as sink, contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            report = observe()
    except Exception as error:
        report = unavailable(_reason(error, "runtime_unavailable"))
    finally:
        if previous_handler is not None:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, previous_handler)
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "READ_ONLY_OBSERVED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
