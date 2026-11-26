"""Install the local-only firewall in one worker lane's network namespace."""

from __future__ import annotations

import argparse
import signal
import subprocess
from pathlib import Path

LANE_PREFIX = {"primary": "172.30.0", "standby": "172.30.2"}
READY = Path("/run/guard/ready")


def rules(lane):
    prefix = LANE_PREFIX[lane]
    return f"""table inet pals_qualification_lane {{
 chain output {{
  type filter hook output priority -150; policy accept;
  meta skuid {{ 65531, 65532 }} ct state established,related accept
  meta skuid 65532 ip daddr 127.0.0.11 udp dport 53 accept
  meta skuid 65532 ip daddr 127.0.0.11 tcp dport 53 accept
  meta skuid 65532 ip daddr 127.0.0.1 tcp dport 443 accept
  meta skuid 65532 ip daddr {prefix}.3 tcp dport 4566 accept
  meta skuid 65532 ip daddr {prefix}.20 tcp dport 8000 accept
  meta skuid 65532 ip daddr {prefix}.30 tcp dport 18119 accept
  meta skuid {{ 65531, 65532 }} reject
 }}
}}
"""


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lane", choices=LANE_PREFIX)
    args = parser.parse_args(argv)
    signals = {signal.SIGTERM, signal.SIGINT}
    signal.pthread_sigmask(signal.SIG_BLOCK, signals)
    subprocess.run(
        ["/usr/sbin/nft", "-f", "-"], input=rules(args.lane), text=True,
        check=True, timeout=10,
    )
    READY.write_text("ready\n", encoding="utf-8")
    signal.sigwait(signals)


if __name__ == "__main__":
    main()
