#!/usr/bin/env python3
"""Reject PALS application-network DB authentication without restarting PostgreSQL.

This is a local authentication guard, NOT a TCP isolation guarantee. Existing
HBA rules and live sessions remain intact. No database credentials are printed.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess

CONTAINER = "pals-local-postgres-1"
BEGIN = "# BEGIN PALS LOCAL APPLICATION NETWORK GUARD"
END = "# END PALS LOCAL APPLICATION NETWORK GUARD"
BLOCK = f"""{BEGIN}
# API, reconciler and schema-release use the separate database network.
# The worker/application network cannot authenticate, including replication.
host all all 172.30.0.0/24 reject
host replication all 172.30.0.0/24 reject
{END}
"""


def guarded_hba(source: str) -> str:
    if source.count(BEGIN) != source.count(END) or source.count(BEGIN) > 1:
        raise ValueError("Existing managed guard is malformed")
    if BEGIN in source:
        start = source.index(BEGIN)
        end = source.index(END, start) + len(END)
        source = source[:start] + source[end:].lstrip("\n")
    return BLOCK + source


def command(args: list[str], *, text: str | None = None) -> str:
    result = subprocess.run(
        args, input=text, text=True, capture_output=True, timeout=15, check=False
    )
    if result.returncode:
        # Docker/SQL errors can include secrets; never echo subprocess output.
        raise RuntimeError("Local PostgreSQL guard operation failed")
    return result.stdout


def sql(statement: str) -> str:
    return command(
        [
            "docker",
            "exec",
            "-i",
            CONTAINER,
            "sh",
            "-ec",
            'exec psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At',
        ],
        text=statement + ";\n",
    ).strip()


def write_hba(source: str) -> None:
    command(
        [
            "docker",
            "exec",
            "-i",
            CONTAINER,
            "sh",
            "-ec",
            (
                'umask 077; temporary=$(mktemp "$PGDATA/.pals-hba.XXXXXX"); '
                'trap \'rm -f "$temporary"\' EXIT; cat > "$temporary"; '
                'chown postgres:postgres "$temporary"; chmod 600 "$temporary"; '
                'mv "$temporary" "$PGDATA/pg_hba.conf"'
            ),
        ],
        text=source,
    )


def apply_guard() -> bool:
    if os.environ.get("DOCKER_HOST", "unix://").startswith(("tcp:", "ssh:")):
        raise ValueError("Only a local Docker socket is supported")
    endpoint = command(
        ["docker", "context", "inspect", "--format", "{{.Endpoints.docker.Host}}"]
    ).strip()
    if not endpoint.startswith("unix://"):
        raise ValueError("Only a local Docker socket is supported")
    labels = json.loads(
        command(["docker", "inspect", "--format", "{{json .Config.Labels}}", CONTAINER])
    )
    if (
        labels.get("com.docker.compose.project") != "pals-local"
        or labels.get("com.docker.compose.service") != "postgres"
    ):
        raise ValueError("Expected the existing pals-local PostgreSQL container")
    path = command(
        ["docker", "exec", CONTAINER, "sh", "-ec", 'printf "%s/pg_hba.conf" "$PGDATA"']
    ).strip()
    if sql("SHOW hba_file") != path:
        raise ValueError("Custom PostgreSQL HBA location is not supported")
    old = command(["docker", "exec", CONTAINER, "cat", path])
    new = guarded_hba(old)
    if new == old:
        return False
    try:
        write_hba(new)
        if sql("SELECT count(*) FROM pg_hba_file_rules WHERE error IS NOT NULL") != "0":
            raise RuntimeError("HBA validation failed")
        if sql("SELECT pg_reload_conf()") != "t":
            raise RuntimeError("HBA reload failed")
    except Exception:
        write_hba(old)
        sql("SELECT pg_reload_conf()")
        raise
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", required=True)
    parser.parse_args()
    try:
        changed = apply_guard()
    except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired):
        print(
            json.dumps(
                {"status": "failed", "detail": "Local PostgreSQL guard not applied"}
            )
        )
        return 1
    print(
        json.dumps(
            {"status": "applied" if changed else "current", "tcp_isolation": False}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
