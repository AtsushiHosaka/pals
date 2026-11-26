"""Validate the frozen layout of two local qualification lanes without starting either."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import re
import stat
import sys
from pathlib import Path

SCHEMA = "pals.local-qualification-lanes.v1"
HASH = re.compile(r"[a-f0-9]{64}\Z")
PREFIX = "pals-reliability-local"
GUARD = PREFIX + "-shared-guard-1"
ENDPOINTS = {
    "primary": {
        "api": 58000,
        "web": 53000,
        "localstack": 54566,
        "cognito": 59229,
        "postgres": 55432,
    },
    "standby": {
        "api": 58001,
        "web": 53001,
        "localstack": 54567,
        "cognito": 59230,
        "postgres": 55433,
    },
}


def need(value, code):
    if not value:
        raise ValueError(code)


def fields(value, keys, code):
    need(type(value) is dict and set(value) == set(keys), code)


def pin(value):
    return isinstance(value, str) and HASH.fullmatch(value) is not None


def absolute(value):
    need(
        isinstance(value, str) and re.fullmatch(r"/[a-zA-Z0-9_/.-]+", value),
        "local_lane_absolute_path_required",
    )
    path = Path(value)
    need(
        str(path) == value
        and not value.startswith("//")
        and ".." not in path.parts
        and path != Path("/"),
        "local_lane_absolute_path_required",
    )
    return path


def validate(document):
    fields(
        document,
        {"schema_version", "docker_socket", "guard", "lanes"},
        "local_lane_binding_invalid",
    )
    need(document["schema_version"] == SCHEMA, "local_lane_binding_invalid")
    absolute(document["docker_socket"])
    guard = document["guard"]
    fields(
        guard,
        {"name", "container_id", "image_id", "ledger_directory"},
        "local_lane_shared_guard_invalid",
    )
    image = guard["image_id"]
    need(
        guard["name"] == GUARD
        and pin(guard["container_id"])
        and isinstance(image, str)
        and image.startswith("sha256:")
        and pin(image[7:]),
        "local_lane_shared_guard_invalid",
    )
    directories = [absolute(guard["ledger_directory"])]
    container_ids = [guard["container_id"]]
    candidate_ids = []
    fields(document["lanes"], ENDPOINTS, "primary_and_standby_local_lanes_required")
    for role, ports in ENDPOINTS.items():
        lane = document["lanes"][role]
        fields(
            lane,
            {
                "candidate_sha256",
                "compose_project",
                "runtime_directory",
                "capture_directory",
                "http_ports",
                "postgres",
            },
            "local_lane_identity_invalid",
        )
        project = PREFIX + "-" + role
        need(
            pin(lane["candidate_sha256"]) and lane["compose_project"] == project,
            "local_lane_identity_invalid",
        )
        expected_http = {
            service: port for service, port in ports.items() if service != "postgres"
        }
        need(
            lane["http_ports"] == expected_http
            and all(type(port) is int for port in lane["http_ports"].values()),
            "local_lane_loopback_ports_differ",
        )
        database = lane["postgres"]
        fields(
            database,
            {"name", "container_id", "host", "host_port", "database"},
            "local_lane_postgres_invalid",
        )
        need(
            database["name"] == project + "-postgres-1"
            and pin(database["container_id"])
            and database["host"] == "127.0.0.1"
            and type(database["host_port"]) is int
            and database["host_port"] == ports["postgres"]
            and database["database"] == "pals",
            "local_lane_postgres_invalid",
        )
        directories.extend(
            absolute(lane[key]) for key in ("runtime_directory", "capture_directory")
        )
        candidate_ids.append(lane["candidate_sha256"])
        container_ids.append(database["container_id"])
    need(
        len(set(candidate_ids)) == 2 and len(set(container_ids)) == 3,
        "local_lane_identities_overlap",
    )
    need(
        all(
            left != right and left not in right.parents and right not in left.parents
            for left, right in itertools.combinations(directories, 2)
        ),
        "local_lane_directories_overlap",
    )
    return document


def unique_object(pairs):
    result = dict(pairs)
    need(len(result) == len(pairs), "local_lane_duplicate_key")
    return result


def read(path, sha256):
    path = absolute(str(path))
    need(pin(sha256), "local_lane_sha256_required")
    with os.fdopen(
        os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb"
    ) as stream:
        info = os.fstat(stream.fileno())
        need(
            stat.S_ISREG(info.st_mode)
            and info.st_uid == os.geteuid()
            and info.st_nlink == 1
            and stat.S_IMODE(info.st_mode) == 0o600
            and 0 < info.st_size <= 16_384,
            "private_local_lane_binding_required",
        )
        raw = stream.read(16_385)
    need(
        len(raw) == info.st_size and hashlib.sha256(raw).hexdigest() == sha256,
        "local_lane_binding_hash_changed",
    )
    return validate(json.loads(raw, object_pairs_hook=unique_object))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binding", type=Path, required=True)
    parser.add_argument("--binding-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        read(args.binding, args.binding_sha256)
    except (OSError, ValueError, RecursionError) as error:
        code = (
            str(error)
            if re.fullmatch(r"[a-z_]+", str(error))
            else "local_lane_binding_unreadable"
        )
        print(json.dumps({"status": "refused", "code": code}, sort_keys=True))
        return 2
    print(
        json.dumps(
            {
                "status": "validated_layout",
                "binding_sha256": args.binding_sha256,
                "runtime_verified": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
