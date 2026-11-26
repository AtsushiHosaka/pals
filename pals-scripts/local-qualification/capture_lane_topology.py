#!/usr/bin/env python3
"""Freeze the running two-lane relay topology after read-only Docker verification."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
from pathlib import Path

import lane_database
import lane_topology as docker
import lanes
import relay_topology


def private_directory(path):
    info = path.lstat()
    lanes.need(
        path.resolve(strict=True) == path and stat.S_ISDIR(info.st_mode)
        and stat.S_IMODE(info.st_mode) == 0o700 and info.st_uid == os.geteuid(),
        "private_lane_topology_directory_required",
    )


def socket_identity(path):
    info = path.lstat()
    lanes.need(path.resolve(strict=True) == path and stat.S_ISSOCK(info.st_mode)
               and info.st_uid == os.geteuid(), "exact_owned_local_docker_socket_required")
    return info.st_dev, info.st_ino


def actor(rows, name):
    row = rows.get("/" + name)
    lanes.need(row is not None, "required_local_lane_actor_missing")
    return row


def actor_reference(row):
    return {"container_id": row["id"], "image_id": row["image"],
            "command_sha256": docker.command_sha256(row)}


def require_fixed_runtime(database, rows, ledger, resume_sha256, run):
    guard = actor(rows, lanes.GUARD)
    lanes.need(guard["budget_resume_sha256"] == resume_sha256, "shared_guard_budget_startup_pin_differs")
    mounts = [mount for mount in guard["mounts"] or [] if mount.get("Destination") == "/run/budget"]
    lanes.need(len(mounts) == 1 and mounts[0].get("Type") == "bind" and mounts[0].get("RW") is True
               and lanes.absolute(mounts[0]["Source"]).resolve(strict=True) == ledger,
               "shared_guard_original_budget_mount_differs")
    volumes = set()
    for lane in database["lanes"].values():
        pin = lane["postgres"]
        actual = actor(rows, pin["name"])
        lanes.need(actual["id"] == pin["container_id"] and actual["image"] == pin["image_id"]
                   and actual["health"] == "healthy", "exact_lane_database_container_required")
        volumes.add(lane_database.verify_database_volume(lane["compose_project"], actual, run, rows))
    lanes.need(len(volumes) == 2, "lane_database_volumes_overlap")
    return guard


def documents(database, rows, guard, captures, ledger, layout_path):
    layout = {
        "schema_version": lanes.SCHEMA,
        "docker_socket": database["docker_socket"],
        "guard": {"name": lanes.GUARD, "container_id": guard["id"], "image_id": guard["image"],
                  "ledger_directory": str(ledger)},
        "lanes": {},
    }
    bindings = {}
    for role, lane in database["lanes"].items():
        layout["lanes"][role] = {
            **{key: lane[key] for key in ("candidate_sha256", "compose_project", "runtime_directory")},
            "capture_directory": str(captures[role]),
            "http_ports": {key: port for key, port in lanes.ENDPOINTS[role].items() if key != "postgres"},
            "postgres": {key: val for key, val in lane["postgres"].items() if key != "image_id"},
        }
        project = lane["compose_project"]
        pinned = {service: actor_reference(actor(rows, f"{project}-{service}-1"))
                  for service in sorted(docker.WORKERS | {docker.POLICY, docker.RELAY})}
        bindings[role] = {"policy": pinned.pop(docker.POLICY), "relay": pinned.pop(docker.RELAY), "workers": pinned}
    layout_raw = encode(layout)
    relay = {
        "schema_version": relay_topology.SCHEMA,
        "layout": reference(layout_path, layout_raw),
        "authority_shim": actor_reference(actor(rows, f"{docker.PROVIDER_PROJECT}-{docker.SHIM}-1")),
        "lanes": bindings,
    }
    return layout, layout_raw, relay


def encode(document):
    raw = (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode()
    lanes.need(0 < len(raw) <= 16_384, "lane_topology_document_too_large")
    return raw


def reference(path, raw):
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()}


def publish(output, files):
    output.mkdir(mode=0o700)
    made = []
    try:
        for name, raw in files.items():
            path = output / name
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            made.append(path)
            with os.fdopen(fd, "wb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
    except BaseException:
        for path in made:
            path.unlink()
        output.rmdir()
        raise


def capture(database_path, database_sha256, captures, ledger, resume_sha256, output, *, run=None):
    """Use the already frozen dependency identities, then confirm a stable live topology."""
    database_path, ledger, output = (lanes.absolute(str(path)) for path in (database_path, ledger, output))
    lanes.need(database_path.resolve(strict=True) == database_path, "canonical_lane_database_binding_required")
    private_directory(output.parent)
    lanes.need(ledger.is_dir() and ledger.resolve(strict=True) == ledger, "original_budget_directory_required")
    lanes.need(not output.exists() and not output.is_symlink(), "unused_lane_topology_output_required")
    lanes.need(lanes.pin(resume_sha256), "exact_shared_guard_budget_startup_pin_required")
    lanes.fields(captures, lanes.ENDPOINTS, "primary_and_standby_local_lanes_required")
    captures = {role: lanes.absolute(str(path)) for role, path in captures.items()}
    database = lane_database.validate_database_layout(lanes.read_document(database_path, database_sha256))
    directories = [*captures.values(), *(Path(lane["runtime_directory"]) for lane in database["lanes"].values())]
    lanes.need(all(path.resolve() == path for path in directories), "canonical_lane_capture_or_runtime_required")
    for directory in [ledger.parent, *directories]:
        lanes.need(output != directory and output not in directory.parents and directory not in output.parents,
                   "lane_topology_output_overlaps_runtime")
    socket = Path(database["docker_socket"])
    identity = socket_identity(socket)
    run = docker.docker_reader(str(socket)) if run is None else run
    rows = docker.inventory(run)
    guard = require_fixed_runtime(database, rows, ledger, resume_sha256, run)
    layout, layout_raw, relay = documents(database, rows, guard, captures, ledger, output / "lane-layout.json")
    topology_sha256 = docker.verify_relay(layout, relay, run=run)
    guard = require_fixed_runtime(database, docker.inventory(run), ledger, resume_sha256, run)
    lanes.need(guard["id"] == layout["guard"]["container_id"] and socket_identity(socket) == identity
               and lanes.read_document(database_path, database_sha256) == database,
               "lane_topology_capture_inputs_changed")
    relay_raw = encode(relay)
    publish(output, {"lane-layout.json": layout_raw, "relay-topology.json": relay_raw})
    return {"status": "lane_topology_captured", "layout": relay["layout"],
            "topology": reference(output / "relay-topology.json", relay_raw), "topology_sha256": topology_sha256}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("database-binding", "primary-capture-directory", "standby-capture-directory", "ledger-directory", "output-directory"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--database-binding-sha256", required=True)
    parser.add_argument("--budget-resume-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        result = capture(args.database_binding, args.database_binding_sha256,
                         {"primary": args.primary_capture_directory, "standby": args.standby_capture_directory},
                         args.ledger_directory, args.budget_resume_sha256, args.output_directory)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        code = str(error)
        if not re.fullmatch(r"[a-z_]+", code):
            code = "lane_topology_capture_refused"
        print(json.dumps({"status": "refused", "code": code}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
