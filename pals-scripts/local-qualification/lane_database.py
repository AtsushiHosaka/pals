"""Freeze only the two disposable database identities needed before provider start."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
import re
import stat
from pathlib import Path
import sys
import tempfile

from lanes import ENDPOINTS, PREFIX, absolute, fields, need, pin, read_document, validate
from lane_topology import OWNER, PROJECT, SERVICE, active, docker_reader, inventory, port_map

SCHEMA = "pals.local-qualification-lane-databases.v1"
PRODUCERS = {"api", "reconciler", "worker", "assessment-worker", "recipe-reviewer", "schema-release"}


def validate_database_layout(document):
    fields(document, {"schema_version", "docker_socket", "lanes"}, "lane_database_binding_invalid")
    need(document["schema_version"] == SCHEMA, "lane_database_binding_invalid")
    absolute(document["docker_socket"])
    fields(document["lanes"], ENDPOINTS, "primary_and_standby_local_lanes_required")
    runtimes, candidates, container_ids = [], set(), set()
    for role, selected in document["lanes"].items():
        fields(
            selected, {"candidate_sha256", "compose_project", "runtime_directory", "local_env", "postgres"},
            "lane_database_member_invalid",
        )
        runtime = absolute(selected["runtime_directory"])
        env = selected["local_env"]
        fields(env, {"path", "sha256"}, "lane_database_environment_reference_invalid")
        need(absolute(env["path"]) == runtime / "local.env" and pin(env["sha256"]),
             "lane_database_environment_reference_invalid")
        project = f"{PREFIX}-{role}"
        database = selected["postgres"]
        fields(
            database, {"name", "container_id", "image_id", "host", "host_port", "database"},
            "lane_database_member_invalid",
        )
        need(
            selected["compose_project"] == project and pin(selected["candidate_sha256"])
            and database["name"] == f"{project}-postgres-1"
            and pin(database["container_id"]) and isinstance(database["image_id"], str)
            and database["image_id"].startswith("sha256:") and pin(database["image_id"][7:])
            and database["host"] == "127.0.0.1" and type(database["host_port"]) is int
            and database["host_port"] == ENDPOINTS[role]["postgres"] and database["database"] == "pals",
            "lane_database_member_invalid",
        )
        runtimes.append(runtime)
        candidates.add(selected["candidate_sha256"])
        container_ids.add(database["container_id"])
    primary, standby = runtimes
    need(
        len(candidates) == len(container_ids) == 2 and primary != standby
        and primary not in standby.parents and standby not in primary.parents,
        "lane_database_identities_overlap",
    )
    return document


def read_for_bootstrap(path, sha256):
    document = read_document(path, sha256)
    if document.get("schema_version") == SCHEMA:
        return validate_database_layout(document)
    # The existing full layout remains accepted here and is still required by the
    # qualification capture and its topology verifier.
    return validate(document)


def verify_databases(document, run, rows):
    validate_database_layout(document)
    volumes = set()
    for selected in document["lanes"].values():
        project = selected["compose_project"]
        database = selected["postgres"]
        actual = rows.get("/" + database["name"])
        need(actual is not None and actual["id"] == database["container_id"]
             and actual["image"] == database["image_id"], "exact_lane_database_container_required")
        labels = actual["labels"] or {}
        network = f"{project}-database"
        need(
            labels.get("codex.owner") == OWNER and labels.get(PROJECT) == project
            and labels.get(SERVICE) == "postgres" and actual["privileged"] is False
            and set(actual["networks"] or {}) == {network},
            "owned_local_lane_database_required",
        )
        active(actual, postgres=True)
        need(actual["health"] == "healthy", "healthy_lane_database_required")
        port_map(actual, {"5432/tcp": [{"HostIp": database["host"], "HostPort": str(database["host_port"])}]})
        name = f"{project}-postgres-data"
        for row in rows.values():
            if row["id"] == actual["id"]:
                continue
            need(not any(mount.get("Name") == name for mount in row.get("mounts") or []),
                 "lane_database_volume_in_use_elsewhere")
            if not row["running"]:
                continue
            labels = row["labels"] or {}
            need(
                network not in (row["networks"] or {})
                and (labels.get(PROJECT) != project or labels.get(SERVICE) not in PRODUCERS),
                "local_lane_database_producers_must_be_stopped",
            )
        data = [mount for mount in actual["mounts"] or []
                if mount["Destination"] == "/var/lib/postgresql/data"]
        need(
            len(data) == 1 and data[0].get("Type") == "volume"
            and data[0].get("Name") == name and data[0].get("RW") is True,
            "owned_lane_database_volume_required",
        )
        inspected = json.loads(run("volume", "inspect", name))
        need(type(inspected) is list and len(inspected) == 1, "owned_lane_database_volume_required")
        volume = inspected[0]
        labels = volume.get("Labels") or {}
        need(
            volume.get("Name") == name and volume.get("Driver") == "local"
            and not volume.get("Options") and volume.get("Mountpoint") == data[0].get("Source")
            and bool(volume["Mountpoint"]) and labels.get(PROJECT) == project
            and labels.get("com.docker.compose.volume") == "postgres-data",
            "owned_lane_database_volume_required",
        )
        volumes.add(volume["Mountpoint"])
    need(len(volumes) == 2, "lane_database_volumes_overlap")


def freeze(dependency_binding):
    from lane_dependencies import checked_render, derive

    derivation = derive(dependency_binding)
    plans, _, _ = derivation
    rendered = checked_render(dependency_binding["rendered_compose"])
    socket = dependency_binding["docker_socket"]
    run = docker_reader(socket)
    rows = inventory(run)
    document = {"schema_version": SCHEMA, "docker_socket": socket, "lanes": {}}
    for role, (_, payload, _) in plans.items():
        env = dependency_binding["local_envs"][role]
        project = f"{PREFIX}-{role}"
        name = project + "-postgres-1"
        actual = rows.get("/" + name)
        need(actual is not None, "exact_lane_database_container_required")
        document["lanes"][role] = {
            "candidate_sha256": rendered["lanes"][role]["candidate_sha256"],
            "compose_project": project,
            "runtime_directory": str(absolute(env["path"]).parent),
            "local_env": env,
            "postgres": {
                "name": name,
                "container_id": actual["id"],
                "image_id": json.loads(payload)["services"]["postgres"]["image"],
                "host": "127.0.0.1",
                "host_port": ENDPOINTS[role]["postgres"],
                "database": "pals",
            },
        }
    verify_databases(document, run, rows)
    # Catch changes to a pinned input before writing a usable descriptor.
    need(derive(dependency_binding) == derivation, "lane_database_dependency_input_changed")
    return document


def migration_receipt_bytes(selected, value):
    return json.dumps({
        "candidate_sha256": selected["candidate_sha256"],
        "container_id": selected["postgres"]["container_id"],
        "local_env_sha256": selected["local_env"]["sha256"],
        "state": value,
    }, sort_keys=True).encode() + b"\n"


def require_completed_migration(runtime, selected):
    receipt = runtime / "database-bootstrap.json"
    with os.fdopen(os.open(receipt, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as prior:
        info = os.fstat(prior.fileno())
        need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_uid == os.geteuid()
             and stat.S_IMODE(info.st_mode) == 0o600, "private_lane_database_receipt_required")
        need(prior.read(1025) == migration_receipt_bytes(selected, "complete"),
             "lane_database_bootstrap_requires_inspection")


@contextmanager
def migration_state(runtime, selected):
    # Per-lane guard: failure on one database never resets or disqualifies the
    # healthy peer. A partial foundation requires explicit inspection.
    lock = runtime / ".database-bootstrap.lock"
    receipt = runtime / "database-bootstrap.json"
    fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    with os.fdopen(fd, "wb") as stream:
        info = os.fstat(stream.fileno())
        need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_uid == os.geteuid()
             and stat.S_IMODE(info.st_mode) == 0o600, "private_lane_database_lock_required")
        try:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("lane_database_bootstrap_busy") from None
        previously_completed = os.path.lexists(receipt)
        if previously_completed:
            require_completed_migration(runtime, selected)

        def store(value):
            temporary_fd, temporary = tempfile.mkstemp(dir=runtime, prefix=".database-bootstrap-")
            try:
                with os.fdopen(temporary_fd, "wb") as output:
                    output.write(migration_receipt_bytes(selected, value))
                    output.flush()
                    os.fsync(output.fileno())
                os.replace(temporary, receipt)
                directory = os.open(runtime, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
            finally:
                Path(temporary).unlink(missing_ok=True)

        begun = False

        def begin(empty):
            nonlocal begun
            need(empty or previously_completed, "lane_database_bootstrap_requires_inspection")
            store("incomplete")
            begun = True

        yield begin
        need(begun, "lane_database_bootstrap_did_not_start")
        store("complete")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dependency-binding", required=True, type=Path)
    parser.add_argument("--dependency-binding-sha256", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        output = absolute(str(args.output))
        need(output.parent.resolve(strict=True) == output.parent, "canonical_lane_database_output_required")
        document = freeze(read_document(args.dependency_binding, args.dependency_binding_sha256))
        raw = (json.dumps(document, sort_keys=True) + "\n").encode()
        with os.fdopen(os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600), "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RecursionError) as error:
        code = str(error)
        if not re.fullmatch(r"[a-z_]+", code):
            code = "lane_database_binding_refused"
        print(json.dumps({"status": "refused", "code": code}))
        return 2
    print(json.dumps({"status": "lane_database_binding_frozen", "sha256": hashlib.sha256(raw).hexdigest()}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
