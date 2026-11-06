#!/usr/bin/env python3
"""Drive 10 test accounts through the real production API and measure the wait for the final answer.

Each virtual user signs in with the Cognito app client (access token), opens one projectless chat
and submits proof requests one at a time with a think-time pause between them, polling until the
request is answered, failed or needs input. Everything goes through the public API the web app uses
(https://api.palschat.site), so Cloudflare, the ALB, the queues, the workers and Lean are all in the
path. Without --execute nothing is submitted: it prints the plan and checks that the API answers.

Results (no question text, no tokens, no passwords) go to <state-dir>/runs/<run-id>/:
results.jsonl, summary.json and summary.md.

  python3 pals-scripts/loadtest-run.py                      # plan only
  python3 pals-scripts/loadtest-run.py --execute --approve-max-usd 1.5
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import secrets
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

API_BASE = "https://api.palschat.site"
TERMINAL = {"answered", "failed", "needs_input"}
# Per request in USD as (typical, upper bound). New proofs measured 0.044-0.062 (exact-precheck);
# simple ones should be cheaper; a reuse is a few tenths of a cent to a few cents.
COST = {"A": (0.03, 0.10), "B": (0.003, 0.02), "C": (0.062, 0.10)}
GOAL_SECONDS = 60.0


class Refusal(RuntimeError):
    pass


# ---- http ---------------------------------------------------------------------------------
class Http:
    """urllib with explicit timeouts; returns (status, parsed json or None). Never raises on HTTP errors."""

    def __init__(self, user_agent: str = "pals-loadtest/1.0 (owner-run)") -> None:
        self.user_agent = user_agent

    def __call__(self, method: str, url: str, headers: dict[str, str] | None = None,
                 body: dict[str, Any] | None = None, timeout: float = 30.0) -> tuple[int, Any]:
        data = None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(url, data=data, method=method, headers={
            "User-Agent": self.user_agent, "Accept": "application/json",
            **({"Content-Type": "application/json"} if body is not None else {}), **(headers or {})})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read(2_000_000)
                return response.status, (json.loads(raw) if raw.strip() else None)
        except urllib.error.HTTPError as error:
            raw = error.read(200_000)
            try:
                return error.code, json.loads(raw)
            except ValueError:
                return error.code, None
        except (urllib.error.URLError, TimeoutError, OSError):
            return 0, None


def percentile(values: list[float], fraction: float) -> float | None:
    """Nearest rank."""
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(fraction * len(ordered)) - 1)]


# ---- one virtual user -----------------------------------------------------------------------
class Session:
    def __init__(self, http: Http, region: str, client_id: str, email: str, password: str) -> None:
        self.http, self.region, self.client_id = http, region, client_id
        self.email, self.password = email, password
        self.access = self.refresh = ""
        self.expires = 0.0

    def _auth(self, flow: str, parameters: dict[str, str]) -> bool:
        status, body = self.http(
            "POST", f"https://cognito-idp.{self.region}.amazonaws.com/",
            headers={"X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
                     "Content-Type": "application/x-amz-json-1.1"},
            body={"AuthFlow": flow, "ClientId": self.client_id, "AuthParameters": parameters})
        result = (body or {}).get("AuthenticationResult") if status == 200 else None
        if not result:
            return False
        self.access = result["AccessToken"]
        self.refresh = result.get("RefreshToken", self.refresh)
        self.expires = time.monotonic() + int(result.get("ExpiresIn", 900))
        return True

    def login(self) -> bool:
        return self._auth("USER_PASSWORD_AUTH", {"USERNAME": self.email, "PASSWORD": self.password})

    def headers(self) -> dict[str, str]:
        if time.monotonic() > self.expires - 90:  # access tokens last 15 minutes
            if not (self.refresh and self._auth("REFRESH_TOKEN_AUTH", {"REFRESH_TOKEN": self.refresh})):
                self.login()
        return {"Authorization": f"Bearer {self.access}"}


class Runner:
    def __init__(self, args: argparse.Namespace, accounts: list[dict[str, Any]], problems: list[dict[str, Any]],
                 client_id: str, http: Http, run_dir: Path) -> None:
        self.args, self.http, self.client_id, self.run_dir = args, http, client_id, run_dir
        self.accounts = accounts[: args.users]
        self.lock = threading.Lock()
        self.results: list[dict[str, Any]] = []
        self.stop = threading.Event()
        self.failures = 0
        self.rng = random.Random(args.seed)
        self.plans = self.assign(problems)
        self.barrier = threading.Barrier(len(self.accounts))

    def assign(self, problems: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
        by_class = {c: [p for p in problems if p["class"] == c] for c in "ABC"}
        plans = []
        for i in range(len(self.accounts)):
            picks = [by_class[c][i % len(by_class[c])] for c in "ABC" if by_class[c]]
            self.rng.shuffle(picks)
            plans.append(picks)
        return plans

    def record(self, row: dict[str, Any]) -> None:
        with self.lock:
            self.results.append(row)
            with (self.run_dir / "results.jsonl").open("a") as stream:
                stream.write(json.dumps(row) + "\n")
            if row["status"] in {"failed", "timeout", "http_error"}:
                self.failures += 1
                if self.failures >= self.args.stop_after_failures:
                    self.stop.set()

    def user(self, index: int) -> None:
        account = self.accounts[index]
        session = Session(self.http, self.args.region, self.client_id, account["email"], account["password"])
        chat = None
        if session.login():
            status, body = self.http("POST", f"{self.args.api}/v1/chats", session.headers(), None)
            chat = (body or {}).get("id") if status == 201 else None
        try:
            self.barrier.wait(timeout=180)  # start everyone together: the worst-case burst
        except threading.BrokenBarrierError:
            pass
        if chat is None:
            self.record({"user": index, "problem": None, "class": None, "status": "setup_failed"})
            self.barrier.abort()
            return
        think = random.Random(self.args.seed * 1000 + index)
        for position, problem in enumerate(self.plans[index]):
            if self.stop.is_set():
                break
            if position:
                time.sleep(think.uniform(self.args.think_min, self.args.think_max))
            self.record(self.one_request(index, session, chat, problem))

    def one_request(self, index: int, session: Session, chat: str, problem: dict[str, Any]) -> dict[str, Any]:
        row: dict[str, Any] = {"user": index, "problem": problem["id"], "class": problem["class"],
                               "submitted_utc": datetime.now(UTC).isoformat(timespec="seconds"),
                               "http_errors": 0}
        started = time.monotonic()
        status, body = self.http("POST", f"{self.args.api}/v1/chats/{chat}/proof-requests", session.headers(),
                                 {"statement": problem["statement"], "idempotency_key": secrets.token_urlsafe(32)})
        if status != 201 or not body:
            row.update(status="http_error", http_status=status, error_code=(body or {}).get("code"))
            return row
        row["request_id"] = body["id"]
        progress = None
        while time.monotonic() - started < self.args.timeout:
            status, current = self.http("GET", f"{self.args.api}/v1/proof-requests/{body['id']}", session.headers())
            if status != 200 or not current:
                row["http_errors"] += 1
            else:
                if progress is None and current["status"] != "queued":
                    progress = time.monotonic() - started
                if current["status"] in TERMINAL:
                    answer = current.get("answer") or {}
                    row.update(status=current["status"], error_code=current.get("error_code"),
                               evidence_kind=answer.get("evidence_kind"),
                               seconds_to_terminal=round(time.monotonic() - started, 2))
                    break
            time.sleep(self.args.poll)
        else:
            row["status"] = "timeout"
        if progress is not None:
            row["seconds_to_progress"] = round(progress, 2)
        return row

    def run(self) -> None:
        threads = [threading.Thread(target=self.user, args=(i,), name=f"user-{i}") for i in range(len(self.accounts))]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()


# ---- summary --------------------------------------------------------------------------------
def summarize(results: list[dict[str, Any]], started: str, finished: str) -> dict[str, Any]:
    classes: dict[str, Any] = {}
    for cls in "ABC":
        rows = [r for r in results if r.get("class") == cls]
        done = [r["seconds_to_terminal"] for r in rows if r["status"] == "answered"]
        progress = [r["seconds_to_progress"] for r in rows if "seconds_to_progress" in r]
        kinds: dict[str, int] = {}
        for r in rows:
            if r.get("evidence_kind"):
                kinds[r["evidence_kind"]] = kinds.get(r["evidence_kind"], 0) + 1
        classes[cls] = {
            "requests": len(rows),
            "answered": len(done),
            "failed": sum(r["status"] == "failed" for r in rows),
            "needs_input": sum(r["status"] == "needs_input" for r in rows),
            "timeout": sum(r["status"] == "timeout" for r in rows),
            "http_error": sum(r["status"] == "http_error" for r in rows),
            "answer_p50": percentile(done, 0.5), "answer_p90": percentile(done, 0.9),
            "answer_max": max(done) if done else None,
            "progress_p50": percentile(progress, 0.5), "progress_p90": percentile(progress, 0.9),
            "within_goal": sum(v <= GOAL_SECONDS for v in done),
            "evidence_kinds": kinds,
            "failure_codes": sorted({r.get("error_code") or "none" for r in rows if r["status"] == "failed"}),
        }
    return {"started_utc": started, "finished_utc": finished, "goal_seconds": GOAL_SECONDS,
            "setup_failed": sum(r["status"] == "setup_failed" for r in results), "classes": classes}


def render(summary: dict[str, Any]) -> str:
    def fmt(value: float | None) -> str:
        return "-" if value is None else f"{value:.1f}"

    names = {"A": "A 簡単な新規", "B": "B 再利用", "C": "C 中程度の新規"}
    lines = [f"# 10人同時利用の負荷試験の結果 ({summary['started_utc']} から {summary['finished_utc']})", "",
             f"目標: 最終回答まで{summary['goal_seconds']:.0f}秒以内。準備に失敗したユーザー: {summary['setup_failed']}", "",
             "| 区分 | 件数 | 回答 | 失敗 | 入力待ち | タイムアウト | 回答p50(秒) | 回答p90(秒) | 最大(秒) | 目標内 | 進捗p50(秒) |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for cls, c in summary["classes"].items():
        lines.append(f"| {names[cls]} | {c['requests']} | {c['answered']} | {c['failed']} | {c['needs_input']} | "
                     f"{c['timeout'] + c['http_error']} | {fmt(c['answer_p50'])} | {fmt(c['answer_p90'])} | "
                     f"{fmt(c['answer_max'])} | {c['within_goal']}/{c['answered']} | {fmt(c['progress_p50'])} |")
    lines += ["", "経路(evidence_kind): " + "; ".join(
        f"{cls}: {c['evidence_kinds'] or '-'}" for cls, c in summary["classes"].items()),
        "", "CloudWatch等の照合には、上の開始と終了の時刻（UTC）を使います。"]
    return "\n".join(lines) + "\n"


# ---- cli ------------------------------------------------------------------------------------
def estimate(problems_per_class: dict[str, int]) -> tuple[float, float]:
    """(typical, upper bound) total model cost in USD."""
    typical = sum(COST[c][0] * n for c, n in problems_per_class.items())
    upper = sum(COST[c][1] * n for c, n in problems_per_class.items())
    return typical, upper


def resolve_client_id(args: argparse.Namespace, pool_id: str, runner: Callable[..., Any] | None = None) -> str:
    argv = ["aws", "--profile", args.profile, "--region", args.region, "cognito-idp", "list-user-pool-clients",
            "--user-pool-id", pool_id, "--max-results", "60", "--output", "json"]
    done = (runner or subprocess.run)(argv, capture_output=True, text=True, check=False)
    if done.returncode != 0:
        raise Refusal("could not list the Cognito app clients: " + done.stderr.strip()[:200])
    found = [c for c in json.loads(done.stdout)["UserPoolClients"] if c["ClientName"] == args.client_name]
    if len(found) != 1:
        raise Refusal(f"expected exactly one app client named {args.client_name}")
    return found[0]["ClientId"]


def load_private(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise Refusal(f"missing {path}")
    if path.stat().st_mode & 0o077:
        raise Refusal(f"{path} must be private (0600)")
    return json.loads(path.read_text())


def inside_git_checkout(path: Path) -> bool:
    path = path.expanduser().resolve()
    return any((parent / ".git").exists() for parent in (path, *path.parents))


def main(argv: list[str] | None = None, http: Http | None = None, client_id: str | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--api", default=API_BASE)
    parser.add_argument("--profile", default=os.environ.get("AWS_PROFILE", "pals-prod-member"))
    parser.add_argument("--region", default="ap-northeast-1")
    parser.add_argument("--client-name", default="pals-mini-web")
    parser.add_argument("--state-dir", default="~/.pals-loadtest")
    parser.add_argument("--problems", default=str(Path(__file__).with_name("loadtest-problems.v1.json")))
    parser.add_argument("--users", type=int, default=10)
    parser.add_argument("--think-min", type=float, default=20.0)
    parser.add_argument("--think-max", type=float, default=60.0)
    parser.add_argument("--poll", type=float, default=2.0)
    parser.add_argument("--timeout", type=float, default=900.0)
    parser.add_argument("--stop-after-failures", type=int, default=4)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--approve-max-usd", type=float, default=0.0)
    args = parser.parse_args(argv)
    http = http or Http()
    state = Path(args.state_dir).expanduser()
    try:
        if inside_git_checkout(state):
            raise Refusal("--state-dir must be outside any git checkout")
        manifest = load_private(state / "manifest.json")
        accounts = manifest["accounts"]
        if not 1 <= args.users <= len(accounts):
            raise Refusal(f"--users must be between 1 and {len(accounts)}")
        problems_doc = json.loads(Path(args.problems).read_text())
        problems = problems_doc["problems"]
        per_class = {c: min(args.users, sum(p["class"] == c for p in problems)) for c in "ABC"}
        typical, upper = estimate(per_class)
        needed = round(typical * 1.25, 2)  # headroom for repairs and failed attempts
        total = sum(per_class.values())
        print(f"{args.users} users, {total} requests ({per_class}); think time {args.think_min:.0f}-{args.think_max:.0f}s; "
              f"timeout {args.timeout:.0f}s each; stop after {args.stop_after_failures} failures")
        print(f"model cost: typically {typical:.2f} USD, upper bound {upper:.2f} USD; "
              f"--approve-max-usd must be at least {needed:.2f} (problem list status: {problems_doc.get('status')})")
        health, _ = http("GET", f"{args.api}/health")
        print(f"API health: HTTP {health}")
        if health != 200:
            raise Refusal("the API did not answer /health with 200")
        if not args.execute:
            print(f"PLAN ONLY: nothing was submitted. To run: --execute --approve-max-usd {needed:.2f} or more.")
            return 0
        if args.approve_max_usd < needed:
            raise Refusal(f"--approve-max-usd must be at least {needed:.2f} (typical cost plus 25% headroom)")
        if "draft" in str(problems_doc.get("status", "")):
            raise Refusal("the problem list is still a draft; the owner must approve it (edit its status)")
        client = client_id or resolve_client_id(args, manifest["pool_id"])
        run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        run_dir = state / "runs" / run_id
        run_dir.mkdir(mode=0o700, parents=True)
        started = datetime.now(UTC).isoformat(timespec="seconds")
        runner = Runner(args, accounts, problems, client, http, run_dir)
        runner.run()
        finished = datetime.now(UTC).isoformat(timespec="seconds")
        summary = summarize(runner.results, started, finished)
        (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))
        (run_dir / "summary.md").write_text(render(summary))
        print(render(summary))
        print(f"results: {run_dir}")
        return 0
    except Refusal as refusal:
        print(f"REFUSED: {refusal}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
