#!/usr/bin/env python3
"""Require actual GitHub Actions success for every changed release source."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
from pathlib import Path

CHECKS = {"pals": "repository-safety", "pals-api": "api-regression",
          "pals-webfront": "web-regression", "pals-infra": "release-cycle-regression",
          "pals-agent": "agent-regression"}
WORKFLOWS = {"pals": ".github/workflows/pals-scripts-pr.yml",
             "pals-infra": ".github/workflows/release-cycle-regression.yml"}
APPLICATION_WORKFLOW = ".github/workflows/application-regression.yml"
EXTRA_CHECKS = {"pals": ("release-acceptance-contracts",)}
COMMIT = re.compile(r"[a-f0-9]{40}\Z")
GITHUB_ACTIONS_APP = 15368


def require_check(runs: list[dict], name: str, workflow: str = APPLICATION_WORKFLOW, *, defer_pending: bool = False) -> str:
    candidates = [run for run in runs if run.get("name") == name
                  and run.get("app", {}).get("id") == GITHUB_ACTIONS_APP]
    if not candidates:
        raise ValueError("required_check_missing:" + name)
    # New queued checks have no started_at. Their newer monotonic run ID must
    # still supersede an older green run for this exact commit/context/app.
    latest = max(candidates, key=lambda run: run["id"])
    if latest.get("verified_workflow_path") != workflow:
        raise ValueError("required_workflow_identity_differs:" + name)
    if (defer_pending and latest.get("status") in {"queued", "in_progress"}
            and latest.get("conclusion") is None):
        return "pending_deferred_by_owner"
    if latest.get("status") != "completed" or latest.get("conclusion") != "success":
        raise ValueError("latest_required_check_not_successful:" + name)
    return "actual_required_check_passed"


def check_sources(candidate: dict, previous: dict, fetch, *, deferred_repositories: frozenset[str] = frozenset()) -> list[dict]:
    rows = []
    for repo, check in CHECKS.items():
        source = candidate["source_commits"].get(repo)
        if not isinstance(source, str) or not COMMIT.fullmatch(source):
            raise ValueError("exact_source_commit_required:" + repo)
        if source == previous["source_commits"].get(repo):
            rows.append({"repository": repo, "source": source, "status": "unchanged_from_predecessor"})
            continue
        runs = fetch(repo, source)
        observed = []
        for context in (check, *EXTRA_CHECKS.get(repo, ())):
            status = require_check(runs, context, WORKFLOWS.get(repo, APPLICATION_WORKFLOW),
                                   defer_pending=repo in deferred_repositories)
            observed.append({"check": context, "status": status})
        row = {"repository": repo, "source": source, "status": "actual_required_check_passed", "check": check}
        if any(item["status"] == "pending_deferred_by_owner" for item in observed):
            row.update(status="pending_deferred_by_owner", checks=observed)
        rows.append(row)
    # The verifier can deliberately retain an older agent revision while the
    # worker moves forward. Its independent override must never evade CI.
    source = candidate.get("verifier_source", {}).get("commit", candidate["source_commits"]["pals-agent"])
    before = previous.get("verifier_source", {}).get("commit", previous["source_commits"]["pals-agent"])
    if not isinstance(source, str) or not COMMIT.fullmatch(source):
        raise ValueError("exact_verifier_source_commit_required")
    if source != before:
        require_check(fetch("pals-agent", source), CHECKS["pals-agent"])
        rows.append({"repository": "pals-agent", "role": "verifier", "source": source,
                     "status": "actual_required_check_passed", "check": CHECKS["pals-agent"]})
    return rows


def fetch(repo: str, source: str) -> list[dict]:
    # Fixed owner/repository map and immutable SHA; never follow caller URLs.
    result = subprocess.run(["gh", "api", "--paginate", "--slurp",
        f"repos/AtsushiHosaka/{repo}/commits/{source}/check-runs"],
        capture_output=True, timeout=45, check=False)
    if result.returncode or len(result.stdout) > 4 * 1024**2:
        raise ValueError("github_check_read_unavailable:" + repo)
    pages = json.loads(result.stdout)
    if not isinstance(pages, list) or not 1 <= len(pages) <= 100:
        raise ValueError("github_check_pages_invalid")
    runs = [run for page in pages for run in page["check_runs"]]
    for run in runs:
        if run.get("name") not in (CHECKS[repo], *EXTRA_CHECKS.get(repo, ())) or run.get("app", {}).get("id") != GITHUB_ACTIONS_APP:
            continue
        url = run.get("details_url", "")
        match = re.fullmatch(r"https://github[.]com/AtsushiHosaka/" + re.escape(repo)
                             + r"/actions/runs/([0-9]+)/job/[0-9]+", url)
        if not match or run.get("head_sha") != source:
            raise ValueError("check_run_commit_or_origin_differs:" + repo)
        observed = subprocess.run(["gh", "api", f"repos/AtsushiHosaka/{repo}/actions/runs/{match[1]}"],
                                  capture_output=True, timeout=30, check=False)
        if observed.returncode or len(observed.stdout) > 1024**2:
            raise ValueError("workflow_identity_unavailable:" + repo)
        workflow = json.loads(observed.stdout)
        if (workflow.get("head_sha") != source
                or workflow.get("repository", {}).get("full_name") != f"AtsushiHosaka/{repo}"):
            raise ValueError("workflow_commit_or_repository_differs:" + repo)
        run["verified_workflow_path"] = workflow.get("path", "").split("@")[0]
    return runs


def read_owner_deferral(path: Path, expected_sha256: str, candidate_bytes: bytes,
                        candidate: dict, *, now: dt.datetime | None = None) -> frozenset[str]:
    """A frozen record of this release owner's explicit pending-CI decision.

    It permits waiting deferral only; it cannot turn missing, failed, cancelled,
    skipped or foreign-workflow checks into a successful result.
    """
    raw = path.read_bytes()
    if (len(raw) > 16384 or not re.fullmatch(r"[a-f0-9]{64}", expected_sha256 or "")
            or hashlib.sha256(raw).hexdigest() != expected_sha256):
        raise ValueError("owner_ci_deferral_hash_differs")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("owner_ci_deferral_duplicate_key")
            result[key] = value
        return result
    value = json.loads(raw, object_pairs_hook=unique)
    required = {"version", "purpose", "owner", "decision_url", "decision", "candidate_manifest_sha256",
                "source_commits", "repositories", "created_at_utc", "expires_at_utc", "resume_condition"}
    if (type(value) is not dict or set(value) != required or type(value["version"]) is not int
            or value["version"] != 1 or value["purpose"] != "release-ci-wait-deferral"
            or value["owner"] != "AtsushiHosaka"
            or value["decision_url"] != "https://github.com/AtsushiHosaka/pals/issues/422"
            or value["decision"] != "ciまたなくていい、すぐリリース！"
            or value["resume_condition"] != "recheck_latest_exact_ci_before_issue_close"
            or value["candidate_manifest_sha256"] != hashlib.sha256(candidate_bytes).hexdigest()
            or value["source_commits"] != candidate["source_commits"]
            or type(value["repositories"]) is not list or not value["repositories"]
            or any(type(repo) is not str for repo in value["repositories"])
            or len(set(value["repositories"])) != len(value["repositories"])
            or not set(value["repositories"]) <= {"pals", "pals-infra"}):
        raise ValueError("owner_ci_deferral_binding_invalid")
    try:
        times = []
        for key in ("created_at_utc", "expires_at_utc"):
            stamp = value[key]
            if not isinstance(stamp, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", stamp):
                raise ValueError()
            times.append(dt.datetime.fromisoformat(stamp.replace("Z", "+00:00")))
        created, expires = times
        current = now if now is not None else dt.datetime.now(dt.timezone.utc)
        if not created <= current < expires or not dt.timedelta(0) < expires - created <= dt.timedelta(hours=4):
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError("owner_ci_deferral_expired_or_invalid_window") from None
    return frozenset(value["repositories"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--predecessor", type=Path, required=True)
    parser.add_argument("--owner-ci-deferral", type=Path)
    parser.add_argument("--owner-ci-deferral-sha256")
    args = parser.parse_args()
    try:
        candidate_bytes, previous_bytes = args.manifest.read_bytes(), args.predecessor.read_bytes()
        candidate, previous = json.loads(candidate_bytes), json.loads(previous_bytes)
        if candidate.get("previous_manifest_sha256") != hashlib.sha256(previous_bytes).hexdigest():
            raise ValueError("predecessor_bytes_not_linked_to_candidate")
        if bool(args.owner_ci_deferral) != bool(args.owner_ci_deferral_sha256):
            raise ValueError("owner_ci_deferral_requires_pinned_file")
        deferred = (read_owner_deferral(args.owner_ci_deferral, args.owner_ci_deferral_sha256,
                                       candidate_bytes, candidate) if args.owner_ci_deferral else frozenset())
        rows = check_sources(candidate, previous, fetch, deferred_repositories=deferred)
        result = {"status": "source_checks_passed", "sources": rows}
        if any(row["status"] == "pending_deferred_by_owner" for row in rows):
            result.update(status="source_checks_owner_deferred", acceptance="NOT_VERIFIED",
                          owner_ci_deferral_sha256=args.owner_ci_deferral_sha256)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (ValueError, KeyError, OSError, subprocess.TimeoutExpired) as error:
        reason = str(error) if type(error) is ValueError else type(error).__name__
        print(json.dumps({"status": "source_checks_blocked", "reason": reason}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
