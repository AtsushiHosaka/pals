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

from lanes import ENDPOINTS, PREFIX, absolute, fields, need, pin, validate

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
RELAY_SCHEMA = "pals.local-qualification-relay-topology.v1"
PROVIDER_PROJECT = PREFIX + "-provider"
SOCKET_VOLUME = PREFIX + "-provider-socket"
SOCKET_MOUNT = "/run/pals-provider"
POLICY = "egress-policy"
RELAY = "provider-relay"
SHIM = "authority-shim"
AUTHORITY_ENV = (
    "OPENAI_API_KEY",
    "PALS_OPENAI_API_KEY",
    "PALS_BUDGET_RESUME_SHA256",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
)
ENV_PRESENT = "".join(
    '{{if and (eq (printf "%%.%ds" .) "%s=") (ne . "%s=")}}{{$present = true}}{{end}}'
    % (len(name) + 1, name, name)
    for name in AUTHORITY_ENV
)
INSPECT = (
    '{"id":{{json .Id}},"name":{{json .Name}},"image":{{json .Image}},'
    '"labels":{{json .Config.Labels}},"user":{{json .Config.User}},'
    '"entrypoint":{{json .Config.Entrypoint}},"cmd":{{json .Config.Cmd}},'
    '"running":{{json .State.Running}},"pid":{{json .State.Pid}},'
    '"started_at":{{json .State.StartedAt}},'
    '"health":{{if .State.Health}}{{json .State.Health.Status}}{{else}}null{{end}},'
    '"namespace":{{json .HostConfig.NetworkMode}},"privileged":{{json .HostConfig.Privileged}},'
    '"cap_drop":{{json .HostConfig.CapDrop}},"cap_add":{{json .HostConfig.CapAdd}},'
    '"security_opts":{{json .HostConfig.SecurityOpt}},'
    '"authority_env":{{$present := false}}{{range .Config.Env}}'
    + ENV_PRESENT
    + "{{end}}{{json $present}},"
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
        try:
            result = subprocess.run(
                [binary, "--host", "unix://" + str(socket), *args],
                env=environment,
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
        except subprocess.TimeoutExpired:
            raise ValueError("docker_topology_read_failed") from None
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


def digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def command_sha256(row):
    return digest({"entrypoint": row["entrypoint"], "cmd": row["cmd"]})


def validate_relay(document, relay):
    fields(
        relay,
        {"schema_version", "layout", "authority_shim", "lanes"},
        "local_relay_binding_invalid",
    )
    need(relay["schema_version"] == RELAY_SCHEMA, "local_relay_binding_invalid")
    fields(relay["layout"], {"path", "sha256"}, "exact_local_relay_layout_ref_required")
    absolute(relay["layout"]["path"])
    need(pin(relay["layout"]["sha256"]), "exact_local_relay_layout_ref_required")
    fields(relay["lanes"], ENDPOINTS, "exact_local_relay_lanes_required")
    expected = [relay["authority_shim"]]
    for lane in relay["lanes"].values():
        fields(lane, {"policy", "relay", "workers"}, "local_relay_lane_invalid")
        fields(lane["workers"], WORKERS, "exact_local_relay_worker_roles_required")
        expected.extend([lane["policy"], lane["relay"], *lane["workers"].values()])
    ids = {
        document["guard"]["container_id"],
        *(lane["postgres"]["container_id"] for lane in document["lanes"].values()),
    }
    for actor in expected:
        fields(
            actor,
            {"container_id", "image_id", "command_sha256"},
            "pinned_local_relay_actor_required",
        )
        image = actor["image_id"]
        need(
            pin(actor["container_id"])
            and pin(actor["command_sha256"])
            and isinstance(image, str)
            and image.startswith("sha256:")
            and pin(image[7:]),
            "pinned_local_relay_actor_required",
        )
        need(actor["container_id"] not in ids, "local_relay_actor_ids_overlap")
        ids.add(actor["container_id"])


def locked_actor(row, expected, user, caps, *, credential_free=False):
    options = row["security_opts"] or []
    need(
        row["id"] == expected["container_id"]
        and row["image"] == expected["image_id"]
        and command_sha256(row) == expected["command_sha256"]
        and row["user"] == user
        and row["privileged"] is False
        and row["read_only"] is True
        and row["cap_drop"] == ["ALL"]
        and capabilities(row) == caps
        and options in (["no-new-privileges"], ["no-new-privileges:true"]),
        "local_relay_actor_binding_differs",
    )
    if credential_free:
        need(
            row["authority_env"] is False,
            "local_relay_actor_authority_environment_present",
        )


def expect_namespace(row, owner, network_ids):
    need(
        row["namespace"] == "container:" + owner["id"],
        "local_relay_network_namespace_differs",
    )
    networks(row, set(), network_ids)


def socket_mount(row, *, writer):
    mounts = row["mounts"] or []
    need(len(mounts) == 1, "local_relay_socket_mount_differs")
    mount = mounts[0]
    need(
        mount.get("Type") == "volume"
        and mount.get("Name") == SOCKET_VOLUME
        and mount.get("Destination") == SOCKET_MOUNT
        and mount.get("RW") is writer,
        "local_relay_socket_mount_differs",
    )
    return absolute(mount.get("Source")).resolve()


def overlaps(left, right):
    return left == right or left in right.parents or right in left.parents


def verify_socket_scope(rows, source, readers, writer):
    expected = {writer: True, **dict.fromkeys(readers, False)}
    observed = {}
    for row in rows.values():
        for mount in row["mounts"] or []:
            value = mount.get("Source")
            if mount.get("Name") != SOCKET_VOLUME and (
                not value or not overlaps(Path(value).resolve(), source)
            ):
                continue
            identifier = row["id"]
            need(
                identifier in expected and identifier not in observed,
                "local_relay_socket_mount_exposed",
            )
            need(
                socket_mount(row, writer=expected[identifier]) == source,
                "local_relay_socket_mount_differs",
            )
            observed[identifier] = expected[identifier]
    need(observed == expected, "local_relay_socket_mount_scope_incomplete")


def authority(rows, guard, relay, network_ids):
    name = f"/{PROVIDER_PROJECT}-{SHIM}-1"
    shim = rows.get(name)
    need(shim is not None, "local_relay_authority_shim_required")
    for actor, service in ((guard, "worker-network-guard"), (shim, SHIM)):
        labels = actor["labels"] or {}
        need(
            labels.get("codex.owner") == OWNER
            and labels.get(PROJECT) == PROVIDER_PROJECT
            and labels.get(SERVICE) == service,
            "local_relay_authority_owner_differs",
        )
    need(
        {
            key
            for key, row in rows.items()
            if (row["labels"] or {}).get(PROJECT) == PROVIDER_PROJECT
        }
        == {guard["name"], shim["name"]},
        "local_relay_authority_scope_differs",
    )
    networks(guard, {PROVIDER_PROJECT}, network_ids)
    locked_actor(shim, relay["authority_shim"], "0:65531", set(), credential_free=True)
    expect_namespace(shim, guard, network_ids)
    port_map(shim, {})
    return shim, socket_mount(shim, writer=True)


def local_relay_scope(scoped, project, lane_name, expected, source, network_ids):
    policy = scoped[f"/{project}-{POLICY}-1"]
    forwarder = scoped[f"/{project}-{RELAY}-1"]
    locked_actor(policy, expected["policy"], "0:0", {"NET_ADMIN"}, credential_free=True)
    need(
        policy["entrypoint"] == ["python", "/opt/pals-local/lane_guard.py"]
        and policy["cmd"] == [lane_name]
        and not policy["mounts"]
        and policy["namespace"] in {"bridge", "default", project + "-e2e"},
        "local_lane_egress_policy_boundary_differs",
    )
    networks(policy, {project + "-e2e"}, network_ids)
    locked_actor(
        forwarder,
        expected["relay"],
        "65531:65531",
        {"NET_BIND_SERVICE"},
        credential_free=True,
    )
    expect_namespace(forwarder, policy, network_ids)
    need(
        socket_mount(forwarder, writer=False) == source,
        "local_relay_socket_mount_differs",
    )
    return policy, forwarder


def collect(document, run, relay=None):
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
    observed = {}
    owned = {guard["name"]}
    namespace_owners = [guard]
    pgdata = []
    if relay is None:
        networks(
            guard,
            {lane["compose_project"] + "-e2e" for lane in document["lanes"].values()},
            network_ids,
        )
    else:
        shim, socket_source = authority(rows, guard, relay, network_ids)
        owned.add(shim["name"])
        socket_readers = set()
    for name, lane in document["lanes"].items():
        project = lane["compose_project"]
        scoped = {
            key: row
            for key, row in rows.items()
            if key.startswith("/" + project + "-")
            or (row["labels"] or {}).get(PROJECT) == project
        }
        roles = ROLES if relay is None else ROLES | {POLICY, RELAY}
        need(
            set(scoped) == {f"/{project}-{role}-1" for role in roles},
            "exact_local_lane_roles_required",
        )
        owned.update(scoped)
        observed[name] = {}
        if relay is not None:
            lane_relay = relay["lanes"][name]
            policy, forwarder = local_relay_scope(
                scoped, project, name, lane_relay, socket_source, network_ids
            )
            namespace_owners.append(policy)
            socket_readers.add(forwarder["id"])
        for role in sorted(roles):
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
            if role in {POLICY, RELAY}:
                continue
            if role in WORKERS:
                if relay is not None:
                    locked_actor(row, lane_relay["workers"][role], "65532:65532", set())
                    expect_namespace(row, policy, network_ids)
                    continue
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
    expected_network_count = 4 if relay is None else 5
    need(
        len(set(network_ids.values())) == expected_network_count
        and len(network_ids) == expected_network_count,
        "local_lane_network_identities_overlap",
    )
    if relay is not None:
        verify_socket_scope(rows, socket_source, socket_readers, shim["id"])
        pgdata.append(socket_source)
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
                and any(
                    owner["id"].startswith(qualifier)
                    or qualifier.lstrip("/") == owner["name"].lstrip("/")
                    for owner in namespace_owners
                )
            ),
            "foreign_container_in_local_lane_boundary",
        )
    result = {"guard": observed_guard, "lanes": observed, "network_ids": network_ids}
    if relay is not None:
        result.update(
            authority_shim=active(shim), socket_mount_sha256=digest(str(socket_source))
        )
    return result


def require_single_process(run, process, code="one_shared_guard_process_required"):
    lines = [
        line.split()
        for line in run("top", process["id"], "-eo", "pid,comm").splitlines()
    ]
    need(
        len(lines) == 2
        and lines[0] == ["PID", "COMMAND"]
        and len(lines[1]) == 2
        and lines[1][0] == str(process["pid"])
        and re.fullmatch(r"python(?:3(?:\.\d+)?)?", lines[1][1]),
        code,
    )


def verify(document, *, run=None):
    """Legacy same-namespace diagnostic retained for fixture checks."""
    validate(document)
    run = run or docker_reader(document["docker_socket"])
    before = collect(document, run)
    require_single_process(run, before["guard"])
    need(collect(document, run) == before, "local_lane_topology_changed_during_read")
    return digest(before)


def verify_relay(document, relay, *, run=None):
    """Verify Docker placement, process and mount metadata. No TLS/DB/product verdict."""
    validate(document)
    validate_relay(document, relay)
    run = run or docker_reader(document["docker_socket"])
    before = collect(document, run, relay)
    require_single_process(run, before["guard"])
    require_single_process(
        run, before["authority_shim"], "single_local_relay_process_required"
    )
    for lane in before["lanes"].values():
        require_single_process(run, lane[RELAY], "single_local_relay_process_required")
    need(
        collect(document, run, relay) == before,
        "local_lane_topology_changed_during_read",
    )
    return digest(before)
