"""Plan or start the dedicated relay authority and A/S application roles."""

from __future__ import annotations

import argparse
from contextlib import ExitStack, contextmanager
import fcntl
import hashlib
from ipaddress import IPv4Address
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile

from budget_handoff import verify_budget_handoff
import lane_database
import lane_dependencies as dependencies
from lane_bootstrap import local_environment_settings, reference
from lane_topology import (
    LEGACY_GUARD, OWNER, POLICY, PROJECT, PROVIDER_PROJECT, RELAY, SERVICE, SHIM,
    SOCKET_VOLUME, active, docker_reader, inventory, port_map,
)
from lanes import ENDPOINTS, GUARD, PREFIX, absolute, fields, need, read_document
from relay_compose import render

SCHEMA = "pals.local-qualification-lane-application.v1"
PROVIDER = (("worker-network-guard",), (SHIM,))
APPLICATION = (
    (POLICY,), (RELAY, "verifier"), ("reconciler",), ("api",),
    ("worker", "assessment-worker", "recipe-reviewer", "webfront"),
)


def private_bytes(ref):
    path = reference(ref)
    need(path.resolve(strict=True) == path, "canonical_lane_application_input_required")
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as stream:
        info = os.fstat(stream.fileno())
        need(
            stat.S_ISREG(info.st_mode) and stat.S_IMODE(info.st_mode) == 0o600
            and info.st_uid == os.geteuid() and info.st_nlink == 1
            and 0 < info.st_size <= 131_072,
            "private_lane_application_input_required",
        )
        raw = stream.read(131_073)
    need(len(raw) == info.st_size and hashlib.sha256(raw).hexdigest() == ref["sha256"],
         "lane_application_input_hash_changed")
    return raw


def environment(ref):
    entries = {}
    for line in private_bytes(ref).decode().splitlines():
        if not line or line.startswith("#"):
            continue
        key, equal, value = line.partition("=")
        need(
            equal and re.fullmatch(r"[A-Z_0-9]+", key) and key not in entries
            and not key.startswith(("COMPOSE_", "DOCKER_", "BUILDX_")),
            "unsafe_lane_application_environment",
        )
        entries[key] = value
    return entries


def lane_inputs(role, env_refs, scope):
    fields(env_refs, {"release", "recipe"}, "exact_lane_application_bootstrap_files_required")
    runtime = Path(scope["runtime_directory"])
    local = local_environment_settings(scope["local_env"], runtime, role)
    need("PALS_LOCAL_CANDIDATE_SHA256" not in local, "dedicated_lane_seed_must_stay_out_of_local_env")
    env_paths = [scope["local_env"]["path"]]
    environment(scope["local_env"])
    loaded = {}
    for name, ref in env_refs.items():
        path = reference(ref)
        need(path == runtime / f"{name}.env", "exact_lane_application_bootstrap_files_required")
        values = environment(ref)
        need(not set(values) & set(local) and not set(values) & set(loaded)
             and all(key.startswith("PALS_") and "OPENAI" not in key for key in values),
             "unsafe_lane_application_environment")
        loaded.update(values)
    env_paths.extend(str(runtime / f"{name}.env") for name in ("release", "recipe"))
    lane_database.require_completed_migration(runtime, scope)
    return env_paths


def provider_environment(ref):
    env = environment(ref)
    fields(env, {"OPENAI_API_KEY", "PALS_OPENAI_UPSTREAM_IP"}, "exact_provider_private_environment_required")
    need(
        re.fullmatch(r"[A-Za-z0-9_-]{12,512}", env["OPENAI_API_KEY"])
        and IPv4Address(env["PALS_OPENAI_UPSTREAM_IP"]).is_global,
        "exact_provider_private_environment_required",
    )
    return env


def derivation(document):
    fields(
        document, {"schema_version", "dependency_binding", "database_layout", "compose_input",
                   "bootstrap_environments", "provider_env", "budget_before", "handoff_output"},
        "lane_application_binding_invalid",
    )
    need(document["schema_version"] == SCHEMA, "lane_application_binding_invalid")
    dep_ref = document["dependency_binding"]
    dep = read_document(reference(dep_ref), dep_ref["sha256"])
    dep_plan = dependencies.derive(dep)
    layout_ref = document["database_layout"]
    layout = lane_database.read_for_bootstrap(reference(layout_ref), layout_ref["sha256"])
    need(layout["schema_version"] == lane_database.SCHEMA and layout["docker_socket"] == dep["docker_socket"],
         "exact_lane_application_database_scope_required")
    render_ref = document["compose_input"]
    render_input = read_document(reference(render_ref), render_ref["sha256"])
    root = Path(dep["compose_root"])
    rendered = dependencies.checked_render(dep["rendered_compose"])
    expected = render(render_input, root)
    if "binding_sha256" in rendered:
        expected["binding_sha256"] = render_ref["sha256"]
    need(rendered == expected, "lane_application_rendering_differs_from_frozen_inputs")
    before = document["budget_before"]
    ledger = rendered["budget_continuity"]
    before_path = reference(before)
    original = reference(ledger)
    need(before_path != original and original.parent not in before_path.parents
         and before["sha256"] == ledger["sha256"], "independent_authoritative_budget_snapshot_required")
    private_bytes(before)
    output = absolute(document["handoff_output"])
    output_dir = dependencies.runtime_directory(output.parent)
    tls_directory = absolute(render_input["provider"]["tls_directory"])
    need(output.name == "budget-handoff.json" and all(base != output_dir and base not in output_dir.parents
                                                      for base in (original.parent, tls_directory))
         and not os.path.lexists(output),
         "new_private_budget_handoff_output_required")
    fields(document["bootstrap_environments"], ENDPOINTS, "primary_and_standby_local_lanes_required")

    base = [dep["docker"], "--config", "<private-docker-config>", "--host", "unix://" + dep["docker_socket"],
            "compose", "--project-directory", str(root)]
    provider = {
        "argv": [*base, "--project-name", PROVIDER_PROJECT, "--env-file", "/dev/null",
                 "-f", "<provider-compose>"],
        "yaml": [rendered["provider_compose_yaml"]],
        "env": provider_environment(document["provider_env"]),
        "steps": PROVIDER,
    }
    lanes = {}
    for role in ENDPOINTS:
        row = layout["lanes"][role]
        frozen = rendered["lanes"][role]
        need(
            row["candidate_sha256"] == frozen["candidate_sha256"] and row["compose_project"] == frozen["compose_project"]
            and row["local_env"] == dep["local_envs"][role],
            "exact_lane_application_database_scope_required",
        )
        env_files = lane_inputs(role, document["bootstrap_environments"][role], row)
        argv = [*base, "--project-name", row["compose_project"]]
        for env_file in env_files:
            argv += ["--env-file", env_file]
        for file in frozen["base_files"]:
            argv += ["-f", file["path"]]
        argv += ["-f", f"<{role}-profile-compose>", "-f", f"<{role}-relay-compose>"]
        lanes[role] = {
            "argv": argv, "yaml": [frozen["profile_overlay_yaml"], frozen["relay_overlay_yaml"]],
            "steps": APPLICATION, "env": {"PALS_LOCAL_CANDIDATE_SHA256": row["candidate_sha256"]},
        }
    # Keep the full render-specific topology exact before any authority writer runs.
    return provider, lanes, dep_plan, layout, original, output


def dependency_identity(rows, layout, dep_plan):
    result = {}
    for role, (_, payload, _) in dep_plan[0].items():
        project = layout["lanes"][role]["compose_project"]
        services = json.loads(payload)["services"]
        for service, service_config in services.items():
            name = f"/{project}-{service}-1"
            row = rows.get(name)
            need(row is not None and row["image"] == service_config["image"], "exact_lane_dependency_container_required")
            labels = row["labels"] or {}
            need(
                labels.get("codex.owner") == OWNER and labels.get(PROJECT) == project
                and labels.get(SERVICE) == service and row["privileged"] is False
                and set(row["networks"] or {}) == {project + "-" + next(iter(service_config["networks"]))},
                "owned_lane_dependency_container_required",
            )
            port = service_config["ports"][0]
            port_map(row, {f'{port["target"]}/tcp': [{"HostIp": "127.0.0.1", "HostPort": port["published"]}]})
            result[name] = active(row)
            if service == "postgres":
                need(row["id"] == layout["lanes"][role]["postgres"]["container_id"],
                     "exact_lane_dependency_container_required")
    return result


def no_existing_application(rows, dependency_names, read):
    scopes = {PROVIDER_PROJECT, *(f"{PREFIX}-{role}" for role in ENDPOINTS)}
    for name, row in rows.items():
        labels = row["labels"] or {}
        if labels.get(PROJECT) in scopes or any(name.startswith(f"/{scope}-") for scope in scopes) or name == "/" + GUARD:
            need(name in dependency_names, "dedicated_application_scope_already_exists")
        if name == LEGACY_GUARD:
            # The final topology only recognizes the exact retired empty writer.
            need(row["status"] == "exited" and row["restart_policy"] in {"no", "unless-stopped"},
                 "retired_legacy_guard_required")
    for kind, reserved in (("volume", SOCKET_VOLUME), ("network", PROVIDER_PROJECT)):
        names = read(kind, "ls", "--format", "{{.Name}}").splitlines()
        need(reserved not in names, "provider_application_resource_already_exists")


def write_receipt(path, receipt):
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600), "wb") as stream:
        stream.write((json.dumps(receipt, sort_keys=True) + "\n").encode())
        stream.flush()
        os.fsync(stream.fileno())


def compose_steps(plan):
    for roles in plan["steps"]:
        yield [*plan["argv"], "up", "--no-deps", "--wait", "--no-build", "--pull", "never", *roles]


@contextmanager
def locked_runtimes(layout):
    with ExitStack() as stack:
        for path in sorted(row["runtime_directory"] for row in layout["lanes"].values()):
            descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            stack.callback(os.close, descriptor)
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ValueError("lane_application_runtime_busy") from None
        yield


def check_stage_inputs(document, dep_plan, layout, role):
    # The live budget bytes are replaced during guard startup. All remaining source,
    # socket, executable and per-lane bootstrap pins are independently rechecked.
    dep_ref = document["dependency_binding"]
    dep = read_document(reference(dep_ref), dep_ref["sha256"])
    need(dependencies.derive(dep) == dep_plan, "lane_application_inputs_changed_before_start")
    if role != "provider":
        lane_inputs(role, document["bootstrap_environments"][role], layout["lanes"][role])


def launch(document, *, apply=False, run=dependencies.run_compose, read=None):
    provider, lanes, dep_plan, layout, original, output = derivation(document)
    projects = {"provider": provider, **lanes}
    report = {"status": "lane_application_preview",
              "commands": {name: list(compose_steps(plan)) for name, plan in projects.items()}}
    if not apply:
        return report
    with locked_runtimes(layout):
        apply_plan(document, (provider, lanes, dep_plan, layout, original, output), projects, run, read)
    report["status"] = "lane_application_started"
    report["handoff_receipt"] = str(output)
    return report


def apply_plan(document, inputs, projects, run, read):
    _, _, dep_plan, layout, original, output = inputs
    read = docker_reader(layout["docker_socket"]) if read is None else read
    rows = inventory(read)
    baseline = dependency_identity(rows, layout, dep_plan)
    lane_database.verify_databases(layout, read, rows)
    no_existing_application(rows, baseline, read)
    budget_ref = {"path": str(original), "sha256": document["budget_before"]["sha256"]}
    receipt = verify_budget_handoff(
        layout["docker_socket"], budget_ref, str(original.parent), budget_ref["sha256"], run=read,
    )
    for name, row in rows.items():
        if name == LEGACY_GUARD:
            need(row["id"] in receipt["observed_stopped_container_ids"]
                 and re.fullmatch(r"[a-f0-9]{64}", row.get("budget_resume_sha256") or "")
                 and row["budget_resume_sha256"] != budget_ref["sha256"],
                 "retired_legacy_guard_ledger_pin_required")
    latest = inventory(read)
    no_existing_application(latest, baseline, read)
    need(derivation(document) == inputs and dependency_identity(latest, layout, dep_plan) == baseline,
         "lane_application_inputs_changed_before_start")
    write_receipt(output, receipt)
    with tempfile.TemporaryDirectory(prefix="pals-lane-application-") as directory:
        scratch = Path(directory)
        plugins = scratch / "cli-plugins"
        plugins.mkdir(mode=0o700)
        (plugins / "docker-compose").symlink_to(dep_plan[1])
        child = {"PATH": "/usr/bin:/bin", "LANG": "C", "HOME": directory, "COMPOSE_DISABLE_ENV_FILE": "1",
                 "COMPOSE_IGNORE_ORPHANS": "1"}
        for role, plan in projects.items():
            check_stage_inputs(document, dep_plan, layout, role)
            files = {"<private-docker-config>": directory}
            placeholders = [item for item in plan["argv"] if item.endswith("-compose>")]
            for index, (placeholder, contents) in enumerate(zip(placeholders, plan["yaml"], strict=True)):
                path = scratch / f"{role}-{index}.yml"
                path.write_text(contents)
                path.chmod(0o600)
                files[placeholder] = str(path)
            for command in compose_steps(plan):
                args = [files.get(item, item) for item in command]
                try:
                    done = run(args, input="", env={**child, **plan["env"]}, timeout=240)
                except subprocess.TimeoutExpired:
                    raise ValueError(f"lane_application_start_timed_out_{role}") from None
                finally:
                    need(dependency_identity(inventory(read), layout, dep_plan) == baseline,
                         "lane_application_existing_dependency_identity_changed")
                need(done.returncode == 0, f"lane_application_start_failed_{role}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binding", required=True, type=Path)
    parser.add_argument("--binding-sha256", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = launch(read_document(args.binding, args.binding_sha256), apply=args.apply)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RecursionError) as error:
        code = str(error)
        if not re.fullmatch(r"[a-z_]+", code):
            code = "lane_application_launch_refused"
        print(json.dumps({"status": "refused", "code": code}))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
