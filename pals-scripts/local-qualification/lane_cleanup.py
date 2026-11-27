"""List or remove the dedicated lane containers, networks and volumes left by a stopped or failed run.

The next dependency launch refuses while any resource of the fixed lane names exists.
This is the one canonical way to clear them. It never touches the budget ledger, which is a host bind
mount, and it removes only resources of the exact lane compose projects and the two fixed names.
It refuses to remove anything while one of those containers is running: the shared guard is the
only writer of the budget ledger, and killing it during a provider call leaves an uncertain
budget that only an owner-approved rollover can continue. Stop the lanes first. The Docker CLI
and socket are named explicitly, like the dependency launch, so the same daemon is used.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

from lane_topology import PROJECT, PROVIDER_PROJECT, SOCKET_VOLUME
from lanes import ENDPOINTS, GUARD, PREFIX, need

SCOPES = (PROVIDER_PROJECT, *(f"{PREFIX}-{role}" for role in ENDPOINTS))
KINDS = (("container", "ls", "--all"), ("network", "ls"), ("volume", "ls"))
FIXED = {"container": GUARD, "volume": SOCKET_VOLUME}


def docker_runner(binary, socket, *, timeout=60):
    binary, socket = Path(binary), Path(socket)
    need(binary.is_absolute() and binary.name == "docker" and binary.is_file() and os.access(binary, os.X_OK),
         "exact_local_docker_cli_required")
    need(socket.is_absolute() and socket.is_socket() and socket == socket.resolve()
         and stat.S_ISSOCK(socket.lstat().st_mode),
         "exact_local_docker_socket_required")
    environment = {"PATH": "/usr/bin:/bin", "LANG": "C"}

    def run(argv):
        try:
            result = subprocess.run(
                [str(binary), "--host", "unix://" + str(socket), *argv], env=environment,
                stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout, check=False,
            )
        except (OSError, UnicodeError, subprocess.TimeoutExpired):
            raise ValueError("lane_cleanup_docker_unavailable") from None
        need(result.returncode == 0 and len(result.stdout) <= 2_000_000, "lane_cleanup_docker_failed")
        return result.stdout.splitlines()

    return run


def inventory(read, *, running=False):
    found = {}
    for kind, *listing in KINDS:
        if running:
            if kind != "container":
                continue
            listing = ["ls"]  # without --all: running containers only
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


def cleanup(*, read, run, apply=False):
    found = inventory(read)
    report = {"status": "lane_cleanup_preview", "resources": found}
    if not apply:
        return report
    need(not inventory(read, running=True)["container"], "lane_cleanup_running_containers")
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
    parser.add_argument("--docker", type=Path, required=True, help="absolute path of the same docker CLI the launch uses")
    parser.add_argument("--docker-socket", type=Path, required=True, help="the same Docker daemon socket the launch uses")
    parser.add_argument("--apply", action="store_true", help="remove the listed resources (default lists them)")
    args = parser.parse_args(argv)
    try:
        run = docker_runner(args.docker, args.docker_socket)
        result = cleanup(read=run, run=run, apply=args.apply)
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
