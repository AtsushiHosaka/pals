"""Local helper owns firewall/proxy; exact worker/reviewer images have UID65532 and no caps."""

import subprocess
from pathlib import Path

from budget_proxy import serve

rules = """table inet pals_worker {
 chain output {
  type filter hook output priority -150; policy accept;
  tcp dport { 5432, 55432 } reject with tcp reset
  ip daddr 169.254.169.254 reject
  ip6 daddr fd00:ec2::254 reject
  meta skuid 65532 ip daddr != 127.0.0.1 tcp dport 443 reject with tcp reset
  meta skuid 65532 ip6 daddr != ::1 tcp dport 443 reject with tcp reset
 }
}
"""
subprocess.run(
    ["/usr/sbin/nft", "-f", "-"], input=rules, text=True, check=True, timeout=10
)
Path("/run/guard/ready").write_text("ready")
serve(
    "/run/provider/server.pem",
    "/run/provider/server-key.pem",
    Path("/run/budget/ledger.json"),
)
