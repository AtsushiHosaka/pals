"""Find or end proof work a failed local capture left unfinished. Local database only."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from bootstrap_database import connect_maintenance, validate_local_dsn

# A request in one of these can still make a worker call the provider. ``needs_input``
# waits for a person and ``answered``/``failed`` are finished (the API has no enum).
OPEN_REQUEST_STATUSES = ("queued", "assessing", "verifying")
REQUESTS = "SELECT id::text,status FROM public.proof_requests WHERE status = ANY(%s) ORDER BY id"
JOBS = (
    "SELECT j.id::text,j.state,COALESCE(r.output_language,'en') FROM public.proof_jobs j "
    "LEFT JOIN public.proof_requests r ON r.formal_job_id=j.id "
    "WHERE NOT (j.state = ANY(%s)) ORDER BY j.id"
)


def terminal_job_states():
    # The candidate's own definition, so a new state is never treated as finished here.
    from app.domain.models.proof_job import TERMINAL_PROOF_JOB_STATES

    return sorted(state.value for state in TERMINAL_PROOF_JOB_STATES)


def leftovers(connection, terminal):
    present = connection.execute(
        "SELECT to_regclass('public.proof_requests') IS NOT NULL,"
        "to_regclass('public.proof_jobs') IS NOT NULL"
    ).fetchone()
    requests = (
        connection.execute(REQUESTS, (list(OPEN_REQUEST_STATUSES),)).fetchall()
        if present[0]
        else []
    )
    jobs = (
        connection.execute(JOBS, (list(terminal),)).fetchall()
        if present[0] and present[1]
        else []
    )
    return requests, jobs


def summary(requests, jobs):
    def count(rows):
        result = {}
        for row in rows:
            result[row[1]] = result.get(row[1], 0) + 1
        return result

    return {
        "requests": len(requests),
        "jobs": len(jobs),
        "request_statuses": count(requests),
        "job_states": count(jobs),
        # Identifiers stay in the database; a reviewer can match these digests there.
        "request_sha256": [hashlib.sha256(r[0].encode()).hexdigest() for r in requests],
        "job_sha256": [hashlib.sha256(j[0].encode()).hexdigest() for j in jobs],
    }


def fail_leftovers(connection, requests, jobs):
    """End them with the candidate's own code, in the caller's one transaction.

    The same two calls the API makes when it ends an overdue request: the job first, then
    the request (which also releases its token and quota holds and closes its outbox).
    A worker that still receives the queued message finds a failed job or a finished
    request and acknowledges it without a provider call.
    """
    from app.domain.proof_termination import REQUEST_DEADLINE_ERROR_CODE
    from app.infrastructure.repositories.proof_request_lean import fail_unfinished_job
    from app.infrastructure.repositories.proof_requests import (
        PostgresProofRequestRepository,
    )

    with connection.cursor() as cursor:
        for job_id, _state, language in jobs:
            fail_unfinished_job(cursor, job_id, language)
        for request_id, _status in requests:
            PostgresProofRequestRepository._fail(
                cursor, request_id, REQUEST_DEADLINE_ERROR_CODE
            )


def inspect(url, *, fail=False, connect=None, terminal=None):
    parts = validate_local_dsn(url)
    if connect is None:
        import psycopg

        connect = psycopg.connect
    terminal = terminal or terminal_job_states()
    with connect_maintenance(parts, connect=connect) as maintenance:
        if not maintenance.execute(
            "SELECT 1 FROM pg_database WHERE datname='pals'"
        ).fetchone():
            # An empty dedicated server: nothing can be left over.
            return {"state": "no_local_database", "requests": 0, "jobs": 0}
    with connect(url) as connection:
        connection.execute("SET LOCAL statement_timeout='20s'")
        requests, jobs = leftovers(connection, terminal)
        result = summary(requests, jobs)
        if not requests and not jobs:
            return {"state": "none", **result}
        if not fail:
            return {"state": "leftover", **result}
        fail_leftovers(connection, requests, jobs)
        after = leftovers(connection, terminal)
        if after[0] or after[1]:
            raise ValueError("leftover_local_jobs_not_ended")
    return {"state": "ended", **result}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--runtime-dir", type=Path, required=True)
    p.add_argument("--api-source", type=Path, required=True)
    p.add_argument("--fail", action="store_true")
    a = p.parse_args()
    sys.path.insert(0, str(a.api_source.resolve()))
    local = dict(
        line.split("=", 1)
        for line in (a.runtime_dir / "local.env").read_text().splitlines()
        if line and not line.startswith("#")
    )
    if local.get("PALS_ENV") != "local":
        raise ValueError("explicit_dedicated_local_database_required")
    print(json.dumps(inspect(local["PALS_HOST_DATABASE_URL"], fail=a.fail)))


if __name__ == "__main__":
    main()
