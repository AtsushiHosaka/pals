"""Derive and optionally start just the local dependencies of both relay lanes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile

from lane_bootstrap import local_environment_settings, reference
from lane_topology import OWNER
from lane_compose import (
    PUBLISHED, SOURCES, STATE_VOLUMES, read_yaml, render_layout, source_documents,
)
from lanes import ENDPOINTS, PREFIX, absolute, fields, need, read_document, unique_object
from relay_compose import image_id, pinned_file

SCHEMA = "pals.local-qualification-lane-dependencies.v1"
IMAGES = {"postgres": "postgres", "localstack": "localstack", "cognito-local": "cognito"}
BINDINGS = {
    "localstack": {
        "pals-infra/localstack/init/ready.d": "/etc/localstack/init/ready.d",
    },
    "cognito-local": {
        "pals-infra/cognito-local/config.json": "/config/config.json",
        "pals-infra/cognito-local/entrypoint.sh": "/config/entrypoint.sh",
    },
}
SUPPORT = {
    "pals-infra/localstack/init/ready.d/10-pals-resources.sh",
    *BINDINGS["cognito-local"],
}
ENV_VARIABLE = re.compile(r"\$\{([A-Z][A-Z_0-9]*)(?::-[^$`{}]*)?\}\Z")
ENV_PREFIXES = ("POSTGRES_", "PALS_PROOF_", "PALS_ARTIFACTS_", "PALS_LOCAL_DATABASE_")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def checked_render(ref):
    path = reference(ref)
    need(path.resolve(strict=True) == path, "canonical_rendered_lane_compose_required")
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as stream:
        info = os.fstat(stream.fileno())
        need(
            stat.S_ISREG(info.st_mode) and stat.S_IMODE(info.st_mode) == 0o600
            and info.st_uid == os.geteuid() and info.st_nlink == 1
            and 0 < info.st_size <= 131_072,
            "private_rendered_lane_compose_required",
        )
        raw = stream.read(131_073)
    need(
        len(raw) == info.st_size and digest(raw) == ref["sha256"],
        "rendered_lane_compose_hash_changed",
    )
    return json.loads(raw, object_pairs_hook=unique_object)


def socket_identity(path):
    info = path.lstat()
    need(
        path.resolve(strict=True) == path and stat.S_ISSOCK(info.st_mode)
        and info.st_uid == os.geteuid(),
        "exact_owned_local_docker_socket_required",
    )
    return (info.st_dev, info.st_ino)


def checked_executable(value, code):
    path = absolute(value)
    need(path.resolve(strict=True) == path and path.is_file() and os.access(path, os.X_OK), code)
    return path


def runtime_directory(path):
    info = path.lstat()
    need(
        path.resolve(strict=True) == path and stat.S_ISDIR(info.st_mode)
        and info.st_uid == os.geteuid() and stat.S_IMODE(info.st_mode) == 0o700,
        "private_lane_dependency_runtime_required",
    )
    return path


def validate_support(root, refs):
    fields(refs, SUPPORT, "exact_lane_dependency_support_files_required")
    for name, ref in refs.items():
        need(reference(ref) == root / name, "exact_lane_dependency_support_files_required")
        pinned_file(ref)
    init = root / "pals-infra/localstack/init/ready.d"
    need(
        {entry.name for entry in init.iterdir()} == {"10-pals-resources.sh"}
        and os.access(init / "10-pals-resources.sh", os.X_OK),
        "exact_localstack_init_directory_required",
    )


def service_environment(kind, settings):
    result = {}
    for value in kind["environment"].values():
        if not isinstance(value, str) or "$" not in value:
            continue
        match = ENV_VARIABLE.fullmatch(value)
        need(match, "lane_dependency_environment_source_changed")
        variable = match[1]
        need(
            variable in {"AWS_REGION", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY",
                         "PALS_LOCAL_COGNITO_CONFIRMATION_CODE", "PALS_DATABASE_SECRET_ID"}
            or variable.startswith(ENV_PREFIXES),
            "lane_dependency_environment_source_changed",
        )
        if variable in settings:
            candidate = settings[variable]
            need(
                re.fullmatch(r"[A-Za-z0-9_./-]+", candidate),
                "lane_dependency_environment_value_invalid",
            )
            result[variable] = candidate
    return result


def projection(role, root, lane, expected, base, infrastructure):
    overlay = read_yaml(lane["relay_overlay_yaml"])
    need(
        overlay["name"] == expected["name"] and overlay["networks"] == expected["networks"],
        "rendered_lane_dependency_networks_differ",
    )
    services = {}
    for name in IMAGES:
        settings = overlay["services"][name]
        wanted = expected["services"][name]
        need(
            settings["ports"] == wanted["ports"] and settings["networks"] == wanted["networks"]
            and (name != "postgres" or settings["profiles"] == [])
            and settings["pull_policy"] == "never" and image_id(settings["image"])
            and settings["labels"] == {"codex.owner": OWNER},
            "rendered_lane_dependency_service_differs",
        )
        original = (base if name == "postgres" else infrastructure)["services"][name]
        for key in ("environment", "healthcheck"):
            need(type(original[key]) is dict, "lane_dependency_source_service_changed")
        service = {
            key: original[key]
            for key in ("environment", "healthcheck", "entrypoint", "restart")
            if key in original
        }
        service.update(
            image=settings["image"], pull_policy="never", ports=wanted["ports"],
            networks=wanted["networks"], labels=settings["labels"],
            volumes=[f"{volume}:{target}" for volume, (owner, target) in STATE_VOLUMES.items() if name == owner],
        )
        service["volumes"] += [
            f"{root / source}:{target}:ro"
            for source, target in BINDINGS.get(name, {}).items()
        ]
        services[name] = service
        endpoint, _ = PUBLISHED[name]
        need(
            service["ports"][0]["published"] == str(ENDPOINTS[role][endpoint]),
            "rendered_lane_dependency_service_differs",
        )

    volumes = {name: overlay["volumes"][name] for name in STATE_VOLUMES}
    need(volumes == expected["volumes"], "rendered_lane_dependency_volumes_differ")
    return {"name": expected["name"], "services": services,
            "networks": expected["networks"], "volumes": volumes}


def derive(document):
    fields(document, {"schema_version", "compose_root", "rendered_compose", "docker_socket",
                      "docker", "compose_plugin", "support", "local_envs"},
           "lane_dependency_binding_invalid")
    need(document["schema_version"] == SCHEMA, "lane_dependency_binding_invalid")
    socket = absolute(document["docker_socket"])
    identity = socket_identity(socket)
    docker = checked_executable(document["docker"], "exact_local_docker_cli_required")
    plugin = checked_executable(document["compose_plugin"], "exact_local_compose_plugin_required")
    root = absolute(document["compose_root"])
    need(root.resolve(strict=True) == root, "canonical_lane_compose_checkout_required")

    rendered = checked_render(document["rendered_compose"])
    need(rendered["status"] == "rendered_relay_compose", "rendered_lane_compose_required")
    base, _, infrastructure, source_refs = source_documents(root)
    need(source_refs == rendered["compose_sources"], "rendered_lane_compose_sources_differ")
    validate_support(root, document["support"])
    fields(rendered["lanes"], ENDPOINTS, "exact_local_relay_lanes_required")
    fields(document["local_envs"], ENDPOINTS, "exact_local_relay_lanes_required")

    projects = {role: {"compose_project": f"{PREFIX}-{role}"} for role in ENDPOINTS}
    layouts = render_layout(projects, root)["x-pals-network-layout"]
    plans = {}
    runtimes = []
    passwords = set()
    for role, ref in document["local_envs"].items():
        lane = rendered["lanes"][role]
        runtime = runtime_directory(reference(ref).parent)
        runtimes.append(runtime)
        need(
            lane["compose_project"] == projects[role]["compose_project"]
            and lane["environment_files"] == [str(runtime / name) for name in
                                                ("local.env", "release.env", "recipe.env")]
            and lane["base_files"] == [source_refs[SOURCES[index]] for index in (0, 2, 1)],
            "rendered_lane_dependency_identity_differs",
        )
        settings = local_environment_settings(ref, runtime, role)
        queue = f"pals-local-{role}-proof-jobs"
        requests = f"pals-local-{role}-proof-requests"
        required = {
            "POSTGRES_USER": f"pals_qual_{role}",
            "PALS_LOCAL_DATABASE_HOST": "postgres",
            "PALS_LOCAL_DATABASE_PORT": "5432",
            "PALS_LOCAL_DATABASE_NAME": "pals",
            "PALS_LOCAL_DATABASE_USERNAME": f"pals_qual_{role}",
            "PALS_LOCAL_DATABASE_PASSWORD": settings["POSTGRES_PASSWORD"],
            "PALS_PROOF_JOBS_QUEUE_NAME": queue,
            "PALS_PROOF_JOBS_DLQ_NAME": queue + "-dlq",
            "PALS_PROOF_REQUESTS_QUEUE_NAME": requests,
            "PALS_PROOF_REQUESTS_DLQ_NAME": requests + "-dlq",
            "PALS_ARTIFACTS_BUCKET": f"pals-local-{role}-artifacts",
        }
        need(all(settings.get(key) == value for key, value in required.items()),
             "lane_dependency_local_identity_differs")
        passwords.add(settings["POSTGRES_PASSWORD"])
        model = projection(role, root, lane, layouts[role], base, infrastructure)
        child = {"PATH": "/usr/bin:/bin", "LANG": "C", "COMPOSE_DISABLE_ENV_FILE": "1",
                 "COMPOSE_IGNORE_ORPHANS": "1"}
        for service in model["services"].values():
            child.update(service_environment(service, settings))
        stdin = json.dumps(model, sort_keys=True)
        argv = [
            str(docker), "--config", "<private-docker-config>", "--host", "unix://" + str(socket),
            "compose", "--project-name", lane["compose_project"], "--project-directory", str(root),
            "--env-file", "/dev/null", "--file", "-", "up", "--wait", "--no-build", "--pull", "never",
            *IMAGES,
        ]
        plans[role] = (argv, stdin, child)
    first, second = runtimes
    need(first != second and first not in second.parents and second not in first.parents,
         "lane_dependency_runtime_directories_overlap")
    need(len(passwords) == 2, "lane_dependency_database_passwords_overlap")
    return plans, plugin, identity


def launch(document, *, apply=False, run=subprocess.run):
    plans, plugin, identity = derive(document)
    report = {
        "status": "lane_dependencies_preview",
        "rendered_compose_sha256": document["rendered_compose"]["sha256"],
        "lanes": {},
    }
    for role, (argv, stdin, _) in plans.items():
        report["lanes"][role] = {
            "command": argv,
            "compose_sha256": digest(stdin.encode()),
            "local_env_sha256": document["local_envs"][role]["sha256"],
        }
    if not apply:
        return report
    with tempfile.TemporaryDirectory(prefix="pals-dependency-docker-") as config:
        plugins = Path(config) / "cli-plugins"
        plugins.mkdir(mode=0o700)
        (plugins / "docker-compose").symlink_to(plugin)
        for role in ENDPOINTS:
            current, current_plugin, current_identity = derive(document)
            need(
                (current, current_plugin, current_identity) == (plans, plugin, identity),
                "lane_dependency_inputs_changed_before_start",
            )
            argv, stdin, environment = plans[role]
            command = argv.copy()
            command[2] = config
            try:
                result = run(command, input=stdin, env={**environment, "HOME": config}, text=True,
                             capture_output=True, timeout=240, check=False)
            except subprocess.TimeoutExpired:
                raise ValueError(f"lane_dependency_start_timed_out_{role}") from None
            need(result.returncode == 0, f"lane_dependency_start_failed_{role}")
    report["status"] = "lane_dependencies_started"
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binding", type=Path, required=True)
    parser.add_argument("--binding-sha256", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = launch(read_document(args.binding, args.binding_sha256), apply=args.apply)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RecursionError) as error:
        code = str(error)
        if not re.fullmatch(r"[a-z_]+", code):
            code = "lane_dependency_launch_refused"
        print(json.dumps({"status": "refused", "code": code}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
