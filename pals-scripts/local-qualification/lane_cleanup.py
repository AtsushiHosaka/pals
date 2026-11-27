"""List or remove the dedicated lane containers, networks and volumes left by a stopped or failed run.

The next dependency launch refuses while any resource of the fixed lane names exists.
This is the one canonical way to clear them. It never touches the budget ledger, which is a host bind
mount, and it removes only resources of the exact lane compose projects and the two fixed names.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

from lane_topology import PROJECT, PROVIDER_PROJECT, SOCKET_VOLUME
from lanes import ENDPOINTS, GUARD, PREFIX, need

SCOPES = (PROVIDER_PROJECT, *(f"{PREFIX}-{role}" for role in ENDPOINTS))
KINDS = (("container", "ls", "--all"), ("network", "ls"), ("volume", "ls"))
FIXED = {"container": GUARD, "volume": SOCKET_VOLUME}


def docker(argv, *, timeout=60):
    try:
        result = subprocess.run(
            ["docker", *argv], env={"PATH": "/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin", "LANG": "C"},
            stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout, check=False,
        )
    except (OSError, UnicodeError, subprocess.TimeoutExpired):
        raise ValueError("lane_cleanup_docker_unavailable") from None
    need(result.returncode == 0 and len(result.stdout) <= 2_000_000, "lane_cleanup_docker_failed")
    return result.stdout.splitlines()


def inventory(read=docker):
    found = {}
    for kind, *listing in KINDS:
        names = set()
        for scope in SCOPES:
            names.update(
                name.strip() for name in read([kind, *listing, "--filter", f"label={PROJECT}={scope}",
                                                "--format", "{{.Names}}" if kind == "container" else "{{.Name}}"])
                if name.strip()
            )
        fixed = FIXED.get(kind)
        if fixed:
            names.update(
                name.strip() for name in read([kind, *listing, "--filter", f"name=^{re.escape(fixed)}$",
                                                "--format", "{{.Names}}" if kind == "container" else "{{.Name}}"])
                if name.strip()
            )
        found[kind] = sorted(names)
    return found


def cleanup(*, apply=False, read=docker, run=docker):
    found = inventory(read)
    report = {"status": "lane_cleanup_preview", "resources": found}
    if not apply:
        return report
    # Containers first, so the networks and volumes they hold can be removed.
    if found["container"]:
        run(["container", "rm", "--force", *found["container"]])
    for kind in ("network", "volume"):
        if found[kind]:
            run([kind, "rm", *found[kind]])
    after = inventory(read)
    need(not any(after.values()), "lane_cleanup_incomplete")
    report["status"] = "lane_cleanup_done"
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="remove the listed resources (default lists them)")
    args = parser.parse_args(argv)
    try:
        result = cleanup(apply=args.apply)
    except (OSError, ValueError) as error:
        code = str(error)
        if not re.fullmatch(r"[a-z_]+", code):
            code = "lane_cleanup_refused"
        print(json.dumps({"status": "refused", "code": code}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
