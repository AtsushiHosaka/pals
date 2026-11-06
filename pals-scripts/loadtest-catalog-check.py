#!/usr/bin/env python3
"""Read-only: which toolchains do the published Recipe entries belong to? (counts only)

Reuses the tunnel and discovery of loadtest-pro-grant.py, connects as the RDS master user, and
runs aggregate SELECTs in a READ ONLY transaction. It creates no role, changes no grant and
prints no Recipe content: only counts per toolchain hash and per output language. If the master
user lacks a privilege the script reports that and stops; it never escalates.

  <repo>/pals-api/.venv/bin/python pals-scripts/loadtest-catalog-check.py                 # dry run
  <repo>/pals-api/.venv/bin/python pals-scripts/loadtest-catalog-check.py --execute --confirm-pool pals-mini-prod
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Any

_spec = importlib.util.spec_from_file_location("loadtest_pro_grant", Path(__file__).with_name("loadtest-pro-grant.py"))
grant = importlib.util.module_from_spec(_spec)
sys.modules["loadtest_pro_grant"] = grant
_spec.loader.exec_module(grant)

SEARCH = "pals_recipe_search"
CATALOG = "pals_local_lean_recipe_catalog"


def privileges(conn: Any) -> dict[str, bool]:
    row = conn.execute(
        "SELECT has_schema_privilege(current_user, %s, 'USAGE'), "
        "       has_schema_privilege(current_user, %s, 'USAGE')", (SEARCH, CATALOG)).fetchone()
    out = {f"usage on {SEARCH}": row[0], f"usage on {CATALOG}": row[1]}
    for table in (f"{SEARCH}.selectable_entries", f"{CATALOG}.toolchains"):
        try:
            ok = conn.execute("SELECT has_table_privilege(current_user, %s, 'SELECT')", (table,)).fetchone()[0]
        except Exception:  # noqa: BLE001 - the relation may not be visible at all
            ok = False
        out[f"select on {table}"] = bool(ok)
    return out


def report(conn: Any) -> list[str]:
    lines: list[str] = []
    have = privileges(conn)
    lines += [f"{name}: {value}" for name, value in have.items()]
    if have[f"select on {SEARCH}.selectable_entries"]:
        rows = conn.execute(
            f"SELECT toolchain_sha256, output_language, count(*) FROM {SEARCH}.selectable_entries "
            "GROUP BY 1,2 ORDER BY 3 DESC").fetchall()
        lines.append("selectable_entries by toolchain_sha256 / language:")
        lines += [f"  {sha}  {lang}  {count}" for sha, lang, count in rows] or ["  (no rows)"]
    else:
        lines.append("selectable_entries is not readable by the master user; stopped (no escalation).")
    if have[f"select on {CATALOG}.toolchains"]:
        rows = conn.execute(f"SELECT toolchain_id, toolchain_fingerprint_sha256, toolchain_fingerprint_jcs "
                            f"FROM {CATALOG}.toolchains ORDER BY 1").fetchall()
        lines.append("toolchains (id, fingerprint sha256, fingerprint: lean/lake/verifier versions only):")
        lines += [f"  {tid}  {sha}  {jcs}" for tid, sha, jcs in rows] or ["  (no rows)"]
    if have[f"select on {SEARCH}.selectable_entries"]:
        rows = conn.execute(f"SELECT toolchain_sha256, recipe_id, max(recipe_revision) FROM "
                            f"{SEARCH}.selectable_entries GROUP BY 1,2 ORDER BY 1,2").fetchall()
        lines.append("recipe ids (the catalog topic names, no content) per toolchain, highest revision:")
        lines += [f"  {sha[:8]}  {rid}  r{rev}" for sha, rid, rev in rows]
    return lines


def language_counts(conn: Any, start: str, end: str) -> list[str]:
    """Counts of proof requests per output_language in a UTC window (no request content)."""
    cols = {r[0] for r in conn.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_schema='public' "
        "AND table_name='proof_requests'").fetchall()}
    stamp = next((c for c in ("created_at", "submitted_at") if c in cols), None)
    if stamp is None or "output_language" not in cols:
        return ["proof_requests has no created_at/output_language visible to the master user"]
    try:
        rows = conn.execute(
            f"SELECT output_language, count(*) FROM public.proof_requests WHERE {stamp} >= %s::timestamptz "
            f"AND {stamp} < %s::timestamptz GROUP BY 1 ORDER BY 2 DESC", (start, end)).fetchall()
    except Exception as error:  # noqa: BLE001
        return [f"proof_requests not readable ({type(error).__name__})"]
    return [f"proof_requests {start}..{end} by output_language:"] + [f"  {lang}  {n}" for lang, n in rows]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profile", default="pals-prod-member")
    parser.add_argument("--region", default="ap-northeast-1")
    parser.add_argument("--state-dir", default="~/.pals-loadtest")
    parser.add_argument("--pool-name", default=grant.POOL_NAME)
    parser.add_argument("--cluster", default=grant.CLUSTER)
    parser.add_argument("--local-port", type=int, default=15432)
    parser.add_argument("--hours", type=int, default=1)
    parser.add_argument("--languages-between", nargs=2, metavar=("START_UTC", "END_UTC"),
                        help="also count proof requests per output_language in this UTC window")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm-pool", default="")
    args = parser.parse_args(argv)
    tool = grant.Tool(args)
    try:
        tool.guard()
        info = tool.discover()
        print(f"discovery ok: database {info['database']}, one control host")
        if not args.execute:
            print(f"DRY RUN: no tunnel or login. Add --execute --confirm-pool {args.pool_name}.")
            return 0
        tool.prerequisites()
        bundle = tool.ca_bundle()
        with tool._tunnel(info):
            user, password = tool.master_credentials(info)
            conn = tool.connect(info, user, password, bundle)
            del password
            try:
                conn.execute("SET default_transaction_read_only = on")
                print("\n".join(report(conn)))
                if args.languages_between:
                    print("\n".join(language_counts(conn, *args.languages_between)))
            finally:
                conn.close()
    except grant.Refusal as error:
        print(f"REFUSED: {error}", file=sys.stderr)
        return 2
    except Exception as error:  # noqa: BLE001 - never print anything that could hold a secret
        print(f"FAILED ({type(error).__name__}): {(str(error).splitlines() or [''])[0][:200]}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
