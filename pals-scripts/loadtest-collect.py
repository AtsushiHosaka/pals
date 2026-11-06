#!/usr/bin/env python3
"""Read the AWS-side metrics for a load-test window (read-only CloudWatch and SQS calls).

  python3 pals-scripts/loadtest-collect.py                       # the latest run in ~/.pals-loadtest/runs
  python3 pals-scripts/loadtest-collect.py --start 2026-11-06T07:57:00Z --end 2026-11-06T08:20:00Z

It prints one table per resource and writes metrics.json next to the run's summary. It only
reads (cloudwatch get-metric-data, sqs get-queue-attributes); it changes nothing.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Callable

Runner = Callable[[list[str]], Any]

COMPUTE = {"InstanceId": "pals-prod-private-compute"}
CONTROL = {"InstanceId": "pals-prod-private-control"}


def aws(profile: str, region: str, command: list[str]) -> Any:
    done = subprocess.run(["aws", "--profile", profile, "--region", region, *command, "--output", "json"],
                          capture_output=True, text=True, check=False)
    if done.returncode != 0:
        raise RuntimeError(done.stderr.strip()[:300])
    return json.loads(done.stdout) if done.stdout.strip() else {}


def instance_ids(run: Runner) -> dict[str, str]:
    found = {}
    for name in (COMPUTE["InstanceId"], CONTROL["InstanceId"]):
        data = run(["ec2", "describe-instances", "--filters", f"Name=tag:Name,Values={name}",
                    "Name=instance-state-name,Values=running"])
        ids = [i["InstanceId"] for r in data["Reservations"] for i in r["Instances"]]
        if len(ids) != 1:
            raise RuntimeError(f"expected one running {name}")
        found[name] = ids[0]
    return found


def alb_dimension(run: Runner) -> str:
    data = run(["elbv2", "describe-load-balancers", "--names", "pals-prod-private-runtime"])
    return data["LoadBalancers"][0]["LoadBalancerArn"].split("loadbalancer/")[1]


def queries(ids: dict[str, str], alb: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []

    def add(label: str, namespace: str, metric: str, dims: dict[str, str], stat: str, period: int = 60) -> None:
        out.append({"Id": f"m{len(out)}", "Label": label, "MetricStat": {
            "Metric": {"Namespace": namespace, "MetricName": metric,
                       "Dimensions": [{"Name": k, "Value": v} for k, v in dims.items()]},
            "Period": period, "Stat": stat}})

    for key, name in (("compute", COMPUTE["InstanceId"]), ("control", CONTROL["InstanceId"])):
        dims = {"InstanceId": ids[name]}
        add(f"{key} CPU max %", "AWS/EC2", "CPUUtilization", dims, "Maximum", 300)
        add(f"{key} CPU avg %", "AWS/EC2", "CPUUtilization", dims, "Average", 300)
        add(f"{key} network in MB", "AWS/EC2", "NetworkIn", dims, "Sum", 300)
    for queue in ("proof-jobs", "proof-requests"):
        name = f"pals-mini-prod-{queue}"
        add(f"{queue} visible max", "AWS/SQS", "ApproximateNumberOfMessagesVisible", {"QueueName": name}, "Maximum")
        add(f"{queue} in-flight max", "AWS/SQS", "ApproximateNumberOfMessagesNotVisible", {"QueueName": name}, "Maximum")
        add(f"{queue} oldest age s", "AWS/SQS", "ApproximateAgeOfOldestMessage", {"QueueName": name}, "Maximum")
        for stat_name in ("Sent", "Received", "Deleted"):
            add(f"{queue} {stat_name.lower()}", "AWS/SQS", f"NumberOfMessages{stat_name}", {"QueueName": name}, "Sum", 300)
        add(f"{queue} DLQ visible max", "AWS/SQS", "ApproximateNumberOfMessagesVisible",
            {"QueueName": name + "-dlq"}, "Maximum")
    aurora = {"DBInstanceIdentifier": "pals-prod-aurora-1"}
    add("aurora ACU max", "AWS/RDS", "ServerlessDatabaseCapacity", aurora, "Maximum")
    add("aurora CPU max %", "AWS/RDS", "CPUUtilization", aurora, "Maximum")
    add("aurora connections max", "AWS/RDS", "DatabaseConnections", aurora, "Maximum")
    add("aurora freeable memory min MB", "AWS/RDS", "FreeableMemory", aurora, "Minimum")
    add("NAT bytes out MB", "AWS/NATGateway", "BytesOutToDestination", {"NatGatewayId": "__nat__"}, "Sum", 300)
    add("ALB requests", "AWS/ApplicationELB", "RequestCount", {"LoadBalancer": alb}, "Sum")
    add("ALB target 5xx", "AWS/ApplicationELB", "HTTPCode_Target_5XX_Count", {"LoadBalancer": alb}, "Sum")
    add("ALB ELB 5xx", "AWS/ApplicationELB", "HTTPCode_ELB_5XX_Count", {"LoadBalancer": alb}, "Sum")
    out.append({"Id": f"m{len(out)}", "Label": "ALB target response p90 s", "MetricStat": {
        "Metric": {"Namespace": "AWS/ApplicationELB", "MetricName": "TargetResponseTime",
                   "Dimensions": [{"Name": "LoadBalancer", "Value": alb}]}, "Period": 60, "Stat": "p90"}})
    return out


def collect(run: Runner, start: datetime, end: datetime) -> dict[str, Any]:
    ids = instance_ids(run)
    nat = run(["ec2", "describe-nat-gateways", "--filter", "Name=state,Values=available"])["NatGateways"]
    nat_id = nat[0]["NatGatewayId"] if len(nat) == 1 else None
    qs = queries(ids, alb_dimension(run))
    for q in qs:
        dims = q["MetricStat"]["Metric"]["Dimensions"]
        for d in dims:
            if d["Value"] == "__nat__":
                d["Value"] = nat_id or "none"
    path = Path(os.environ.get("TMPDIR", "/tmp")) / f"pals-collect-{os.getpid()}.json"
    path.write_text(json.dumps(qs))
    try:
        data = run(["cloudwatch", "get-metric-data", "--start-time", start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "--end-time", end.strftime("%Y-%m-%dT%H:%M:%SZ"), "--metric-data-queries", f"file://{path}",
                    "--max-datapoints", "100000"])
    finally:
        path.unlink(missing_ok=True)
    series = {}
    for result in data["MetricDataResults"]:
        points = sorted(zip(result["Timestamps"], result["Values"]))
        series[result["Label"]] = [(t, v) for t, v in points]
    return series


def reduce(label: str, points: list[tuple[str, float]]) -> dict[str, Any]:
    values = [v for _, v in points]
    if not values:
        return {"label": label, "n": 0}
    scale = 1e6 if label.endswith("MB") else 1.0
    peak = max(values) / scale
    low = min(values) / scale
    total = sum(values) / scale
    return {"label": label, "n": len(values), "max": round(peak, 3), "min": round(low, 3), "sum": round(total, 3)}


def render(rows: list[dict[str, Any]], start: datetime, end: datetime) -> str:
    lines = [f"CloudWatch window {start:%Y-%m-%d %H:%M}Z .. {end:%Y-%m-%d %H:%M}Z", "",
             f"{'metric':38} {'points':>6} {'max':>12} {'min':>12} {'sum':>12}"]
    for r in rows:
        if r["n"] == 0:
            lines.append(f"{r['label']:38} {'0':>6} {'-':>12} {'-':>12} {'-':>12}")
        else:
            lines.append(f"{r['label']:38} {r['n']:>6} {r['max']:>12} {r['min']:>12} {r['sum']:>12}")
    return "\n".join(lines) + "\n"


def latest_run_window(state: Path) -> tuple[datetime, datetime, Path]:
    runs = sorted((state / "runs").glob("*/summary.json"))
    if not runs:
        raise RuntimeError("no finished run with a summary.json")
    summary = json.loads(runs[-1].read_text())
    parse = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00"))
    return parse(summary["started_utc"]), parse(summary["finished_utc"]), runs[-1].parent


def main(argv: list[str] | None = None, runner: Runner | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profile", default=os.environ.get("AWS_PROFILE", "pals-prod-member"))
    parser.add_argument("--region", default="ap-northeast-1")
    parser.add_argument("--state-dir", default="~/.pals-loadtest")
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--margin-minutes", type=int, default=3)
    args = parser.parse_args(argv)
    run = runner or (lambda command: aws(args.profile, args.region, command))
    try:
        out_dir = None
        if args.start and args.end:
            start = datetime.fromisoformat(args.start.replace("Z", "+00:00"))
            end = datetime.fromisoformat(args.end.replace("Z", "+00:00"))
        else:
            start, end, out_dir = latest_run_window(Path(args.state_dir).expanduser())
        start -= timedelta(minutes=args.margin_minutes)
        end += timedelta(minutes=args.margin_minutes)
        series = collect(run, start.astimezone(UTC), end.astimezone(UTC))
    except RuntimeError as error:
        print(f"FAILED: {error}", file=sys.stderr)
        return 2
    rows = [reduce(label, points) for label, points in series.items()]
    print(render(rows, start, end))
    if out_dir is not None:
        (out_dir / "metrics.json").write_text(json.dumps(rows, indent=2))
        print(f"written: {out_dir / 'metrics.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
