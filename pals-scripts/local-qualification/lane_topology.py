"""Read-only Docker topology checks for the opt-in local qualification lanes."""

from __future__ import annotations

import hashlib
import itertools
import json
import os
import re
import shutil
import stat
import subprocess
from pathlib import Path

from lanes import ENDPOINTS, absolute, need, pin, validate

OWNER = "01a1bb4b-dec2-76f0-a6fe-32405e465d6e"
PROJECT = "com.docker.compose.project"
SERVICE = "com.docker.compose.service"
WORKERS = {"worker", "assessment-worker", "recipe-reviewer"}
PORTS = {
    "api": ("api", "8000/tcp"),
    "webfront": ("web", "3000/tcp"),
    "localstack": ("localstack", "4566/tcp"),
    "cognito-local": ("cognito", "9229/tcp"),
    "postgres": ("postgres", "5432/tcp"),
}
ROLES = WORKERS | set(PORTS) | {"reconciler", "verifier"}
INSPECT = (
    '{"id":{{json .Id}},"name":{{json .Name}},"image":{{json .Image}},'
    '"labels":{{json .Config.Labels}},"user":{{json .Config.User}},'
    '"entrypoint":{{json .Config.Entrypoint}},"cmd":{{json .Config.Cmd}},'
    '"running":{{json .State.Running}},"pid":{{json .State.Pid}},'
    '"started_at":{{json .State.StartedAt}},'
    '"health":{{if .State.Health}}{{json .State.Health.Status}}{{else}}null{{end}},'
    '"namespace":{{json .HostConfig.NetworkMode}},"privileged":{{json .HostConfig.Privileged}},'
    '"cap_drop":{{json .HostConfig.CapDrop}},"cap_add":{{json .HostConfig.CapAdd}},'
    '"read_only":{{json .HostConfig.ReadonlyRootfs}},"mounts":{{json .Mounts}},'
    '"ports":{{json .NetworkSettings.Ports}},"networks":{{json .NetworkSettings.Networks}}}'
)


def docker_reader(path):
    socket = absolute(path)
    need(
        socket == socket.resolve(strict=True) and stat.S_ISSOCK(socket.lstat().st_mode),
        "exact_local_docker_socket_required",
    )
    binary = shutil.which("docker")
    need(binary is not None, "docker_cli_required")
    environment = {
        name: value
        for name, value in os.environ.items()
        if not name.startswith("DOCKER_")
    }

    def run(*args):
        result = subprocess.run(
            [binary, "--host", "unix://" + str(socket), *args],
            env=environment,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        need(
            result.returncode == 0 and len(result.stdout) <= 2_000_000,
            "docker_topology_read_failed",
        )
        return result.stdout

    return run


def inventory(run):
    ids = run("ps", "--all", "--quiet", "--no-trunc").split()
    need(
        0 < len(ids) <= 256
        and len(set(ids)) == len(ids)
        and all(pin(value) for value in ids),
        "bounded_docker_inventory_required",
    )
    raw = run("inspect", "--type", "container", "--format", INSPECT, *ids)
    rows = [json.loads(line) for line in raw.splitlines()]
    need(
        len(rows) == len(ids)
        and {row["id"] for row in rows} == set(ids)
        and len({row["name"] for row in rows}) == len(ids),
        "docker_container_inventory_changed",
    )
    return {row["name"]: row for row in rows}


def active(row, *, postgres=False):
    need(
        row["running"] is True
        and type(row["pid"]) is int
        and row["pid"] > 0
        and isinstance(row["started_at"], str)
        and re.fullmatch(r"20\d\d-\d\d-\d\dT[0-9:.]+Z", row["started_at"])
        and (row["health"] == "healthy" or (postgres and row["health"] is None)),
        "owned_local_container_not_live",
    )
    return {key: row[key] for key in ("id", "image", "pid", "started_at")}


def port_map(row, expected):
    published = {
        port: targets for port, targets in (row["ports"] or {}).items() if targets
    }
    need(published == expected, "local_lane_loopback_binding_differs")


def networks(row, expected, network_ids):
    attached = row["networks"] or {}
    need(set(attached) == set(expected), "local_lane_network_membership_differs")
    for name, connection in attached.items():
        network_id = connection["NetworkID"]
        need(
            pin(network_id) and network_ids.setdefault(name, network_id) == network_id,
            "local_lane_network_identity_differs",
        )


def capabilities(row):
    return {value.removeprefix("CAP_") for value in row["cap_add"] or []}


def collect(document, run):
    rows = inventory(run)
    expected_guard = document["guard"]
    guard = rows.get("/" + expected_guard["name"])
    need(
        guard is not None
        and guard["id"] == expected_guard["container_id"]
        and guard["image"] == expected_guard["image_id"]
        and guard["labels"].get("codex.owner") == OWNER
        and guard["entrypoint"] == ["python", "/opt/pals-local/guard.py"]
        and not guard["cmd"]
        and guard["user"] == "0:0"
        and guard["read_only"] is True
        and guard["privileged"] is False
        and guard["cap_drop"] == ["ALL"]
        and capabilities(guard) == {"NET_ADMIN", "NET_BIND_SERVICE"},
        "pinned_shared_guard_required",
    )
    observed_guard = active(guard)
    port_map(guard, {})
    ledger = absolute(expected_guard["ledger_directory"]).resolve()
    writers = []
    for row in rows.values():
        for mount in row["mounts"] or []:
            source = mount.get("Source")
            if not source or mount.get("RW") is not True:
                continue
            path = Path(source).resolve()
            if path == ledger or path in ledger.parents or ledger in path.parents:
                writers.append((row["id"], mount["Type"], path, mount["Destination"]))
    need(
        writers == [(guard["id"], "bind", ledger, "/run/budget")],
        "shared_budget_writer_mount_differs",
    )

    network_ids = {}
    networks(
        guard,
        {lane["compose_project"] + "-e2e" for lane in document["lanes"].values()},
        network_ids,
    )
    observed = {}
    owned = {guard["name"]}
    pgdata = []
    for name, lane in document["lanes"].items():
        project = lane["compose_project"]
        scoped = {
            key: row
            for key, row in rows.items()
            if key.startswith("/" + project + "-")
            or (row["labels"] or {}).get(PROJECT) == project
        }
        need(
            set(scoped) == {f"/{project}-{role}-1" for role in ROLES},
            "exact_local_lane_roles_required",
        )
        owned.update(scoped)
        observed[name] = {}
        for role in sorted(ROLES):
            row = scoped[f"/{project}-{role}-1"]
            labels = row["labels"] or {}
            need(
                labels.get("codex.owner") == OWNER
                and labels.get(PROJECT) == project
                and labels.get(SERVICE) == role
                and row["privileged"] is False,
                "local_lane_owner_or_role_differs",
            )
            observed[name][role] = active(row, postgres=role == "postgres")
            expected = {}
            if role in PORTS:
                key, internal = PORTS[role]
                expected = {
                    internal: [
                        {"HostIp": "127.0.0.1", "HostPort": str(ENDPOINTS[name][key])}
                    ]
                }
            port_map(row, expected)
            if role in WORKERS:
                need(
                    row["namespace"] == "container:" + guard["id"]
                    and row["user"] == "65532:65532"
                    and row["privileged"] is False
                    and row["cap_drop"] == ["ALL"]
                    and not capabilities(row),
                    "worker_shared_guard_namespace_required",
                )
                networks(row, set(), network_ids)
                continue
            expected_networks = {project + "-e2e"} if role != "postgres" else set()
            if role in {"api", "reconciler", "postgres"}:
                expected_networks.add(project + "-database")
            networks(row, expected_networks, network_ids)
            if role == "postgres":
                need(
                    row["id"] == lane["postgres"]["container_id"],
                    "local_lane_postgres_identity_differs",
                )
                data = [
                    mount
                    for mount in row["mounts"] or []
                    if mount["Destination"] == "/var/lib/postgresql/data"
                ]
                need(
                    len(data) == 1
                    and data[0]["Type"] in {"volume", "bind"}
                    and data[0]["RW"] is True,
                    "local_lane_postgres_data_mount_required",
                )
                source = absolute(data[0]["Source"]).resolve()
                pgdata.append(source)
                observed[name][role]["data_mount_sha256"] = hashlib.sha256(
                    str(source).encode()
                ).hexdigest()
    need(
        len(set(network_ids.values())) == 4 and len(network_ids) == 4,
        "local_lane_network_identities_overlap",
    )
    need(
        all(
            left != right and left not in right.parents and right not in left.parents
            for left, right in itertools.combinations([ledger, *pgdata], 2)
        ),
        "local_lane_data_mounts_overlap",
    )
    for name, row in rows.items():
        if name in owned:
            continue
        namespace = row["namespace"] or ""
        qualifier = (
            namespace.removeprefix("container:")
            if namespace.startswith("container:")
            else ""
        )
        need(
            not (set(row["networks"] or {}) & network_ids.keys())
            and not (
                qualifier
                and (
                    guard["id"].startswith(qualifier)
                    or qualifier.lstrip("/") == expected_guard["name"]
                )
            ),
            "foreign_container_in_local_lane_boundary",
        )
    return {"guard": observed_guard, "lanes": observed, "network_ids": network_ids}


def verify(document, *, run=None):
    validate(document)
    run = run or docker_reader(document["docker_socket"])
    before = collect(document, run)
    pid = before["guard"]["pid"]
    lines = [
        line.split()
        for line in run("top", before["guard"]["id"], "-eo", "pid,comm").splitlines()
    ]
    need(
        len(lines) == 2
        and lines[0] == ["PID", "COMMAND"]
        and len(lines[1]) == 2
        and lines[1][0] == str(pid)
        and re.fullmatch(r"python(?:3(?:\.\d+)?)?", lines[1][1]),
        "one_shared_guard_process_required",
    )
    need(collect(document, run) == before, "local_lane_topology_changed_during_read")
    raw = json.dumps(before, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()
