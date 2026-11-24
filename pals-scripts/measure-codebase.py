#!/usr/bin/env python3
"""Measure code size, change frequency and CI time for the rearchitecture (pals#493, stage 1 pals#485).

Read only. It reads local git clones and the GitHub Actions / pull request APIs through `gh`; it never starts a workflow, pushes, or comments.
The output is one JSON document, so a stage can record the same numbers before and after its change.

Definitions (docs/rearchitecture-plan-2026-11-24.md, appendix A):
- lines: `wc -l` of tracked *.py *.ts *.tsx *.css *.sh *.sql files.
- churn: non-merge commits on the measured ref since --since that touch the file; co-change: other files in those commits.
- ci wall: run created_at -> updated_at of successful runs created in the window; job time: job started_at -> completed_at.
- runner occupancy: for every job that a runner picked up (runner_name set), first step start -> last step end. A job's own
  started_at -> completed_at includes queueing for cancelled jobs, so it is not used for occupancy.
- elapsed: run_started_at -> updated_at (includes queueing).
- pr lead time: createdAt -> mergedAt of pull requests merged in the window.

Usage:
  python3 pals-scripts/measure-codebase.py --workspace DIR [--clone] --since 2026-10-01 \
      --window 2026-11-18..2026-11-24 > baseline.json
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import subprocess
import sys
import tempfile
from pathlib import Path

OWNER = "AtsushiHosaka"
REPOS = ("pals", "pals-api", "pals-agent", "pals-webfront", "pals-infra")
CODE_PATTERNS = ("*.py", "*.ts", "*.tsx", "*.css", "*.sh", "*.sql")
LARGE = 1000
HEAVY_WORKFLOWS = {
    "pals": "PALS parent checks",
    "pals-api": "API application regression",
    "pals-agent": "Agent application regression",
    "pals-webfront": "Application regression",
    "pals-infra": "Release cycle regression",
}


# ---------- pure helpers (unit tested) ----------

def parse_time(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def minutes(start: str, end: str) -> float:
    return (parse_time(end) - parse_time(start)).total_seconds() / 60


def percentile(values: list[float], q: float) -> float | None:
    """Nearest-rank on the sorted values (the same rule the plan used: index int(n*q), median at n//2)."""
    if not values:
        return None
    ordered = sorted(values)
    index = len(ordered) // 2 if q == 0.5 else min(len(ordered) - 1, int(len(ordered) * q))
    return round(ordered[index], 1)


def summary(values: list[float]) -> dict:
    return {"n": len(values), "p50": percentile(values, 0.5), "p90": percentile(values, 0.9),
            "max": round(max(values), 1) if values else None}


def count_lines(path: Path) -> int:
    """The number `wc -l` prints: newline bytes."""
    return path.read_bytes().count(b"\n")


def parse_log(text: str) -> list[tuple[str, set[str]]]:
    """`git log --format=@%cs --name-only` -> [(date, files)]."""
    commits: list[tuple[str, set[str]]] = []
    for line in text.splitlines():
        if line.startswith("@"):
            commits.append((line[1:].strip(), set()))
        elif line.strip() and commits:
            commits[-1][1].add(line.strip())
    return commits


def churn(commits: list[tuple[str, set[str]]], path: str, recent_from: str, top: int = 4) -> dict:
    touching = [c for c in commits if path in c[1]]
    co = collections.Counter(f for _, files in touching for f in files if f != path)
    return {"commits": len(touching), "commits_recent": sum(1 for d, _ in touching if d >= recent_from),
            "co_changed": [[f, k] for f, k in co.most_common(top)]}


def job_occupancy(job: dict) -> float:
    """Minutes a runner spent on the job: first step start -> last step end; 0 if no runner picked it up."""
    if not job.get("runner_name") or job.get("conclusion") == "skipped":
        return 0.0
    steps = [s for s in job.get("steps") or [] if s.get("started_at") and s.get("completed_at")]
    if not steps:
        return 0.0
    first = min(parse_time(s["started_at"]) for s in steps)
    last = max(parse_time(s["completed_at"]) for s in steps)
    return max(0.0, (last - first).total_seconds() / 60)


def outcome(run: dict) -> str:
    return {"cancelled": "cancelled", "skipped": "skipped", "success": "success"}.get(run.get("conclusion"), "other")


def ci_summary(runs: list[dict], jobs_by_run: dict[int, list[dict]]) -> dict:
    """Wall, job time, queue and occupancy of one workflow's completed runs."""
    wall, queue = [], []
    job_minutes: dict[str, list[float]] = collections.defaultdict(list)
    occupancy = collections.Counter()
    elapsed = collections.Counter()
    count = collections.Counter()
    for run in runs:
        kind = outcome(run)
        count[kind] += 1
        if run.get("run_started_at") and kind != "skipped":
            elapsed[kind] += minutes(run["run_started_at"], run["updated_at"])
        for job in jobs_by_run.get(run["id"], []):
            occupancy[kind] += job_occupancy(job)
            if kind == "success" and job.get("started_at") and job.get("completed_at") and job.get("conclusion") != "skipped":
                job_minutes[job["name"]].append(minutes(job["started_at"], job["completed_at"]))
                queue.append(minutes(job["created_at"], job["started_at"]))
        if kind == "success":
            wall.append(minutes(run["created_at"], run["updated_at"]))
    used = occupancy["success"] + occupancy["cancelled"] + occupancy["other"]
    total_elapsed = elapsed["success"] + elapsed["cancelled"] + elapsed["other"]
    return {
        "runs": dict(count),
        "wall_success_min": summary(wall),
        "job_queue_min": summary(queue),
        "jobs_success_min": {name: summary(v) for name, v in sorted(job_minutes.items())},
        "runner_occupancy_min": {k: round(v) for k, v in occupancy.items()},
        "elapsed_min": {k: round(v) for k, v in elapsed.items()},
        "cancelled_share_of_occupancy": round(occupancy["cancelled"] / used, 3) if used else None,
        "cancelled_share_of_elapsed": round(elapsed["cancelled"] / total_elapsed, 3) if total_elapsed else None,
    }


def lead_times(prs: list[dict]) -> dict:
    hours = [(parse_time(p["mergedAt"]) - parse_time(p["createdAt"])).total_seconds() / 3600 for p in prs]
    files = [p["changedFiles"] for p in prs]
    lines = [p["additions"] + p["deletions"] for p in prs]
    return {"merged": len(prs), "open_to_merge_h": summary(hours), "changed_files": summary(files), "changed_lines": summary(lines)}


# ---------- adapters (git, gh) ----------

def run(cmd: list[str], cwd: Path | None = None) -> str:
    done = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if done.returncode != 0:
        raise SystemExit(f"{' '.join(cmd[:4])} failed: {done.stderr.strip()[:300]}")
    return done.stdout


def gh_pages(path: str, key: str) -> list[dict]:
    """All items of a paginated REST list (`key` is the array field, e.g. workflow_runs)."""
    out = run(["gh", "api", "--paginate", path, "--jq", f".{key}[]"])
    return [json.loads(line) for line in out.splitlines() if line.strip()]


def ensure_clone(workspace: Path, repo: str, clone: bool) -> Path:
    path = workspace / repo
    if not path.exists():
        if not clone:
            raise SystemExit(f"{path} is missing; pass --clone to make a blobless clone")
        run(["git", "clone", "-q", "--filter=blob:none", f"https://github.com/{OWNER}/{repo}.git", str(path)])
    else:
        run(["git", "fetch", "-q", "origin"], cwd=path)
    return path


def measure_repo(path: Path, ref: str, since: str, recent_from: str, hot: int) -> dict:
    head = run(["git", "rev-parse", "--short", ref], cwd=path).strip()
    files = [f for f in run(["git", "ls-tree", "-r", "--name-only", ref], cwd=path).splitlines()
             if any(Path(f).match(p) for p in CODE_PATTERNS)]
    # A detached temporary worktree checks the ref out in one batch (a blobless clone would otherwise fetch blob by blob)
    # and leaves the clone's own work tree untouched.
    with tempfile.TemporaryDirectory(prefix="measure-") as tmp:
        tree = Path(tmp) / "tree"
        run(["git", "worktree", "add", "-q", "--detach", str(tree), ref], cwd=path)
        try:
            counts = {f: count_lines(tree / f) for f in files if (tree / f).is_file()}
        finally:
            run(["git", "worktree", "remove", "--force", str(tree)], cwd=path)
    commits = parse_log(run(["git", "log", "--no-merges", f"--since={since}", "--format=@%cs", "--name-only", ref], cwd=path))
    large = sorted(((n, f) for f, n in counts.items() if n >= LARGE), reverse=True)
    by_churn = collections.Counter(f for _, fs in commits for f in fs)
    return {
        "ref": ref, "head": head,
        "code_files": len(counts), "code_lines": sum(counts.values()),
        "large_files": len(large), "large_lines": sum(n for n, _ in large),
        "large": [{"path": f, "lines": n, **churn(commits, f, recent_from)} for n, f in large],
        "commits_since": len(commits),
        "hot_files": [[f, k] for f, k in by_churn.most_common(hot)],
    }


def measure_ci(repo: str, window: str, with_jobs: bool) -> dict:
    name = HEAVY_WORKFLOWS[repo]
    runs = [r for r in gh_pages(f"repos/{OWNER}/{repo}/actions/runs?per_page=100&created={window}", "workflow_runs")
            if r["name"] == name and r["status"] == "completed"]
    jobs = {}
    if with_jobs:
        for r in runs:
            jobs[r["id"]] = gh_pages(f"repos/{OWNER}/{repo}/actions/runs/{r['id']}/jobs?per_page=100", "jobs")
    return {"workflow": name, **ci_summary(runs, jobs)}


def measure_prs(repo: str, window: str) -> dict:
    start, end = window.split("..")
    out = run(["gh", "pr", "list", "-R", f"{OWNER}/{repo}", "--state", "merged", "--limit", "500",
               "--search", f"merged:{start}..{end}", "--json", "createdAt,mergedAt,additions,deletions,changedFiles"])
    return lead_times(json.loads(out or "[]"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--workspace", type=Path, required=True, help="directory holding (or receiving) the clones")
    ap.add_argument("--clone", action="store_true", help="make missing blobless clones")
    ap.add_argument("--ref", default="origin/main")
    ap.add_argument("--since", default="2026-10-01", help="churn start date")
    ap.add_argument("--recent-from", default=None, help="date that starts the 'recent' churn count (default: 30 days before the window end)")
    ap.add_argument("--window", required=True, help="CI and PR window, YYYY-MM-DD..YYYY-MM-DD (inclusive)")
    ap.add_argument("--repo", action="append", choices=REPOS, help="limit to these repos (repeatable)")
    ap.add_argument("--no-jobs", action="store_true", help="skip per-job API calls (no occupancy, no job times)")
    ap.add_argument("--hot", type=int, default=8)
    args = ap.parse_args(argv)
    end = dt.date.fromisoformat(args.window.split("..")[1])
    recent_from = args.recent_from or (end - dt.timedelta(days=30)).isoformat()
    args.workspace.mkdir(parents=True, exist_ok=True)
    result = {"window": args.window, "since": args.since, "recent_from": recent_from, "repos": {}}
    for repo in args.repo or REPOS:
        path = ensure_clone(args.workspace, repo, args.clone)
        result["repos"][repo] = {
            "code": measure_repo(path, args.ref, args.since, recent_from, args.hot),
            "ci": measure_ci(repo, args.window, not args.no_jobs),
            "prs": measure_prs(repo, args.window),
        }
        print(f"measured {repo}", file=sys.stderr)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=1, sort_keys=True)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
