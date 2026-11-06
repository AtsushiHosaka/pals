import importlib.util
import json
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "loadtest-collect.py"
spec = importlib.util.spec_from_file_location("loadtest_collect", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fake_run(calls):
    def run(command):
        calls.append(command)
        if command[:2] == ["ec2", "describe-instances"]:
            name = command[3].split("=")[-1]
            return {"Reservations": [{"Instances": [{"InstanceId": f"i-{name[-7:]}"}]}]}
        if command[:2] == ["elbv2", "describe-load-balancers"]:
            return {"LoadBalancers": [{"LoadBalancerArn": "arn:aws:elasticloadbalancing:r:1:loadbalancer/app/x/abc"}]}
        if command[:2] == ["ec2", "describe-nat-gateways"]:
            return {"NatGateways": [{"NatGatewayId": "nat-1"}]}
        if command[:2] == ["cloudwatch", "get-metric-data"]:
            queries = json.loads(Path(command[command.index("--metric-data-queries") + 1][7:]).read_text())
            now = datetime(2026, 11, 6, 8, 0, tzinfo=UTC)
            return {"MetricDataResults": [
                {"Label": q["Label"], "Timestamps": [(now + timedelta(minutes=i)).isoformat() for i in range(2)],
                 "Values": [1.5e6, 3.0e6]} for q in queries]}
        raise AssertionError(command)
    return run


class CollectTest(unittest.TestCase):
    def test_only_read_calls_are_made_and_units_are_scaled(self):
        calls = []
        start = datetime(2026, 11, 6, 7, 55, tzinfo=UTC)
        series = module.collect(fake_run(calls), start, start + timedelta(minutes=30))
        verbs = {tuple(c[:2]) for c in calls}
        self.assertEqual(verbs, {("ec2", "describe-instances"), ("elbv2", "describe-load-balancers"),
                                 ("ec2", "describe-nat-gateways"), ("cloudwatch", "get-metric-data")})
        rows = {r["label"]: r for r in (module.reduce(l, p) for l, p in series.items())}
        self.assertEqual(rows["compute network in MB"]["max"], 3.0)  # bytes -> MB
        self.assertEqual(rows["proof-jobs visible max"]["max"], 3.0e6)  # counts are not scaled
        self.assertIn("compute CPU max %", rows)
        self.assertIn("proof-jobs DLQ visible max", rows)

    def test_render_has_one_line_per_metric_and_marks_empty_series(self):
        rows = [module.reduce("x", [("t", 2.0)]), module.reduce("empty", [])]
        text = module.render(rows, datetime(2026, 11, 6, tzinfo=UTC), datetime(2026, 11, 6, 1, tzinfo=UTC))
        self.assertIn("empty", text)
        self.assertEqual(len([l for l in text.splitlines() if l.startswith(("x ", "empty"))]), 2)


if __name__ == "__main__":
    unittest.main()
