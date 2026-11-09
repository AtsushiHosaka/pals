#!/usr/bin/env python3
"""Require actual GitHub Actions success for every changed release source."""
from __future__ import annotations

import argparse
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


def require_check(runs: list[dict], name: str, workflow: str = APPLICATION_WORKFLOW) -> None:
    candidates = [run for run in runs if run.get("name") == name
                  and run.get("app", {}).get("id") == GITHUB_ACTIONS_APP]
    if not candidates:
        raise ValueError("required_check_missing:" + name)
    # New queued checks have no started_at. Their newer monotonic run ID must
    # still supersede an older green run for this exact commit/context/app.
    latest = max(candidates, key=lambda run: run["id"])
    if latest.get("verified_workflow_path") != workflow:
        raise ValueError("required_workflow_identity_differs:" + name)
    if latest.get("status") != "completed" or latest.get("conclusion") != "success":
        raise ValueError("latest_required_check_not_successful:" + name)


def check_sources(candidate: dict, previous: dict, fetch) -> list[dict]:
    rows = []
    for repo, check in CHECKS.items():
        source = candidate["source_commits"].get(repo)
        if not isinstance(source, str) or not COMMIT.fullmatch(source):
            raise ValueError("exact_source_commit_required:" + repo)
        if source == previous["source_commits"].get(repo):
            rows.append({"repository": repo, "source": source, "status": "unchanged_from_predecessor"})
            continue
        runs = fetch(repo, source)
        for context in (check, *EXTRA_CHECKS.get(repo, ())):
            require_check(runs, context, WORKFLOWS.get(repo, APPLICATION_WORKFLOW))
        rows.append({"repository": repo, "source": source, "status": "actual_required_check_passed", "check": check})
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--predecessor", type=Path, required=True)
    args = parser.parse_args()
    try:
        candidate_bytes, previous_bytes = args.manifest.read_bytes(), args.predecessor.read_bytes()
        candidate, previous = json.loads(candidate_bytes), json.loads(previous_bytes)
        if candidate.get("previous_manifest_sha256") != hashlib.sha256(previous_bytes).hexdigest():
            raise ValueError("predecessor_bytes_not_linked_to_candidate")
        rows = check_sources(candidate, previous, fetch)
        print(json.dumps({"status": "source_checks_passed", "sources": rows}, sort_keys=True))
        return 0
    except (ValueError, KeyError, OSError, subprocess.TimeoutExpired) as error:
        reason = str(error) if type(error) is ValueError else type(error).__name__
        print(json.dumps({"status": "source_checks_blocked", "reason": reason}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
