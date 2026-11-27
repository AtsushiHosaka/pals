"""Render, but never apply, the two-lane local qualification Compose configuration."""

from __future__ import annotations

import hashlib
import itertools
import os
import stat
from pathlib import Path

from lane_compose import SOURCES, render_layout
from lane_topology import (
    OWNER,
    POLICY,
    PROVIDER_PROJECT,
    RELAY,
    RELAY_IMPORT,
    SHIM,
    SOCKET_MOUNT,
    SOCKET_VOLUME,
    WORKERS,
)
from lanes import ENDPOINTS, GUARD, PREFIX, absolute, fields, need, pin
from provider_relay import SESSION_SECONDS

SCHEMA = "pals.local-qualification-relay-compose.v1"
IMAGES = {"api", "worker", "web", "verifier", "postgres", "localstack", "cognito"}
BUILD_SOURCES = {"Dockerfile.lane", "lane_guard.py", "provider_relay.py"}
HEALTH = {"interval": "2s", "timeout": "3s", "retries": 15}
# `docker top` must see exactly one process in each guard, shim and relay container. A Python health probe
# is a second process while it runs (about 0.3 s under amd64 emulation), so a 2 s interval made the
# topology checks fail at random. Probe at 2 s only while starting, then every 30 s.
SPARSE_HEALTH = {
    "interval": "30s", "timeout": "3s", "retries": 3, "start_period": "60s", "start_interval": "2s",
}
PROVIDER_READY = "import socket; socket.create_connection(('127.0.0.1',443),2).close()"
# The lane relay runs as uid 65531, which its own egress policy rejects for any new connection, so it
# cannot probe itself by connecting. Read the kernel's listener table instead (127.0.0.1:443 LISTEN).
LISTENING = (
    "import sys;sys.exit(0 if any(r.split()[1]=='0100007F:01BB' and r.split()[3]=='0A' "
    "for r in open('/proc/net/tcp').read().splitlines()[1:]) else 1)"
)


class Override:
    def __init__(self, value):
        self.value = value


class Reset:
    pass


def yaml_text(value):
    import yaml

    class ComposeDumper(yaml.SafeDumper):
        pass

    def override(dumper, tagged):
        node = dumper.represent_data(tagged.value)
        node.tag = "!override"
        return node

    ComposeDumper.add_representer(Override, override)
    ComposeDumper.add_representer(
        Reset, lambda dumper, _: dumper.represent_scalar("!reset", "null")
    )
    return yaml.dump(value, Dumper=ComposeDumper, sort_keys=True)


def pinned_file(reference):
    fields(reference, {"path", "sha256"}, "exact_relay_compose_reference_required")
    path = absolute(reference["path"])
    need(
        path.resolve(strict=True) == path
        and path.is_file()
        and pin(reference["sha256"]),
        "exact_relay_compose_reference_required",
    )
    with path.open("rb") as stream:
        raw = stream.read(131_073)
    need(
        0 < len(raw) <= 131_072
        and hashlib.sha256(raw).hexdigest() == reference["sha256"],
        "relay_compose_reference_hash_changed",
    )
    return raw


def image_id(value):
    return isinstance(value, str) and value.startswith("sha256:") and pin(value[7:])


def validate(document):
    fields(
        document,
        {"schema_version", "build_sources", "provider", "lanes"},
        "relay_compose_input_invalid",
    )
    need(document["schema_version"] == SCHEMA, "relay_compose_input_invalid")
    fields(
        document["build_sources"], BUILD_SOURCES, "exact_relay_build_sources_required"
    )
    for name, reference in document["build_sources"].items():
        pinned_file(reference)
        need(Path(reference["path"]).name == name, "exact_relay_build_sources_required")
    provider = document["provider"]
    fields(
        provider,
        {"guard_image", "lane_image", "tls_directory", "budget_ledger"},
        "relay_compose_provider_invalid",
    )
    need(
        all(image_id(provider[key]) for key in ("guard_image", "lane_image"))
        and provider["guard_image"] != provider["lane_image"],
        "pinned_relay_images_required",
    )
    budget = provider["budget_ledger"]
    # The old guard's exact bytes are a preparation reference. Starting or testing a
    # second writer is deliberately outside this source-only renderer.
    fields(budget, {"path", "sha256"}, "exact_relay_compose_reference_required")
    info = absolute(budget["path"]).lstat()
    need(
        Path(budget["path"]).name == "ledger.json"
        and info.st_uid == os.geteuid()
        and stat.S_IMODE(info.st_mode) == 0o600
        and info.st_nlink == 1,
        "exact_relay_budget_ledger_required",
    )
    pinned_file(budget)
    directories = [
        Path(budget["path"]).parent.resolve(),
        absolute(provider["tls_directory"]).resolve(),
    ]
    fields(document["lanes"], ENDPOINTS, "exact_local_relay_lanes_required")
    candidates = set()
    for lane in document["lanes"].values():
        fields(
            lane,
            {"candidate_sha256", "images", "runtime_directory", "enable_plus_coupons"},
            "relay_compose_lane_invalid",
        )
        fields(lane["images"], IMAGES, "pinned_relay_images_required")
        need(
            pin(lane["candidate_sha256"])
            and type(lane["enable_plus_coupons"]) is bool
            and all(image_id(value) for value in lane["images"].values()),
            "relay_compose_lane_invalid",
        )
        candidates.add(lane["candidate_sha256"])
        directories.append(absolute(lane["runtime_directory"]).resolve())
    need(
        len(candidates) == 2
        and all(
            left != right and left not in right.parents and right not in left.parents
            for left, right in itertools.combinations(directories, 2)
        ),
        "relay_compose_lanes_overlap",
    )


def socket_mount(*, read_only):
    return {
        "type": "volume",
        "source": "provider-socket",
        "target": SOCKET_MOUNT,
        "read_only": read_only,
        "volume": {"nocopy": True},
    }


def actor(image, user, caps):
    return {
        "image": image,
        "pull_policy": "never",
        "platform": "linux/amd64",
        "user": user,
        "read_only": True,
        "cap_drop": ["ALL"],
        "cap_add": caps,
        "security_opt": ["no-new-privileges:true"],
        "labels": {"codex.owner": OWNER},
    }


def relay_service(image, *, authority=False):
    operation = "serve_authority_socket" if authority else "serve_lane"
    result = actor(
        image,
        "0:65531" if authority else "65531:65531",
        [] if authority else ["NET_BIND_SERVICE"],
    )
    program = RELAY_IMPORT + "p." + operation + "()"
    health = (
        RELAY_IMPORT
        + "p.private_socket_directory(p.AUTHORITY_SOCKET);p.socket_identity(p.AUTHORITY_SOCKET)"
        if authority
        else LISTENING
    )
    result.update(
        entrypoint=["python", "-I", "-c", program],
        command=[],
        stop_grace_period=f"{SESSION_SECONDS + 10}s",
        volumes=[socket_mount(read_only=not authority)],
        healthcheck={**SPARSE_HEALTH, "test": ["CMD", "python", "-I", "-c", health]},
    )
    return result


def provider_compose(provider):
    guard = actor(provider["guard_image"], "0:0", ["NET_ADMIN", "NET_BIND_SERVICE"])
    guard.update(
        container_name=GUARD,
        entrypoint=["python", "/opt/pals-local/guard.py"],
        command=[],
        networks=["provider"],
        tmpfs=["/run/guard:rw,noexec,nosuid,size=1m"],
        environment={
            "OPENAI_API_KEY": "${OPENAI_API_KEY:?provider-only private env required}",
            "PALS_OPENAI_UPSTREAM_IP": "${PALS_OPENAI_UPSTREAM_IP:?provider-only private env required}",
            "PALS_BUDGET_RESUME_SHA256": provider["budget_ledger"]["sha256"],
        },
        healthcheck={**SPARSE_HEALTH, "test": ["CMD", "python", "-c", PROVIDER_READY]},
        volumes=[
            {
                "type": "bind",
                "source": provider["tls_directory"],
                "target": "/run/provider",
                "read_only": True,
            },
            {
                "type": "bind",
                "source": str(Path(provider["budget_ledger"]["path"]).parent),
                "target": "/run/budget",
            },
        ],
    )
    shim = relay_service(provider["lane_image"], authority=True)
    shim.update(
        network_mode="service:worker-network-guard",
        depends_on={"worker-network-guard": {"condition": "service_healthy"}},
    )
    return {
        "name": PROVIDER_PROJECT,
        "services": {"worker-network-guard": guard, SHIM: shim},
        "networks": {"provider": {"name": PROVIDER_PROJECT, "driver": "bridge"}},
        "volumes": {
            "provider-socket": {
                "name": SOCKET_VOLUME,
                "driver": "local",
                "driver_opts": {
                    "type": "tmpfs",
                    "device": "tmpfs",
                    "o": "size=1048576,mode=0750,uid=0,gid=65531,nosuid,nodev,noexec",
                },
            }
        },
    }


def app_overlay(template, lane, provider):
    before, separator, after = template.partition("  worker-network-guard:\n")
    _guard, next_service, workers = after.partition("  worker:\n")
    need(separator and next_service, "relay_compose_legacy_guard_template_changed")
    raw = before + next_service + workers
    mappings = {
        "@@API_IMAGE@@": lane["images"]["api"],
        "@@WORKER_IMAGE@@": lane["images"]["worker"],
        "@@WEB_IMAGE@@": lane["images"]["web"],
        "@@VERIFIER_IMAGE@@": lane["images"]["verifier"],
        "@@RUNTIME@@/provider-tls/ca-bundle.pem": provider["tls_directory"]
        + "/ca-bundle.pem",
        "@@PLUS_COUPONS_ENV@@": '      PALS_PLUS_COUPONS_ENABLED: "true"\n'
        if lane["enable_plus_coupons"]
        else "",
    }
    for key, value in mappings.items():
        raw = raw.replace(key, value)
    for old, new in (
        (
            "network_mode: service:worker-network-guard",
            "network_mode: service:" + POLICY,
        ),
        (
            "worker-network-guard: {condition: service_healthy}",
            RELAY + ": {condition: service_healthy}",
        ),
    ):
        need(raw.count(old) == 3, "relay_compose_legacy_worker_template_changed")
        raw = raw.replace(old, new)
    need(
        "@@" not in raw and "worker-network-guard" not in raw,
        "relay_compose_legacy_guard_template_changed",
    )
    return raw


def lane_compose(layout, role, lane, provider):
    services = layout["services"]
    guard_network = layout["networks"]["e2e"]["ipam"]["config"][0]["subnet"].rsplit(
        ".", 1
    )[0]
    policy = actor(provider["lane_image"], "0:0", ["NET_ADMIN"])
    policy.update(
        entrypoint=["python", "/opt/pals-local/lane_guard.py"],
        command=[role],
        networks={
            "e2e": {
                "ipv4_address": guard_network + ".30",
                "aliases": ["pals-recipe-reviewer"],
            }
        },
        extra_hosts=["api.openai.com:127.0.0.1"],
        tmpfs=["/run/guard:rw,noexec,nosuid,size=1m"],
        healthcheck={**HEALTH, "test": ["CMD", "test", "-s", "/run/guard/ready"]},
    )
    forwarder = relay_service(provider["lane_image"])
    forwarder.update(
        network_mode="service:" + POLICY,
        depends_on={POLICY: {"condition": "service_healthy"}},
    )
    role_images = {
        "api": "api",
        "reconciler": "api",
        "schema-release": "api",
        "verifier": "verifier",
        "webfront": "web",
        "localstack": "localstack",
        "cognito-local": "cognito",
        "postgres": "postgres",
        **dict.fromkeys(WORKERS, "worker"),
    }
    for service, image in role_images.items():
        value = services.setdefault(service, {})
        value.update(
            image=lane["images"][image],
            pull_policy="never",
            build=Reset(),
            labels={"codex.owner": OWNER},
        )
        for field in ("networks", "ports"):
            if field in value:
                value[field] = Override(value[field])
        if service in WORKERS:
            # The provider authority authenticates to its upstream itself. No real key is
            # needed in an application worker to establish the local relay TLS session.
            value["environment"] = {
                "OPENAI_API_KEY": "local-provider-relay",
                "PALS_OPENAI_API_KEY": "",
            }
    # The reviewer shares the egress-policy namespace as uid 65532, which that policy lets reach only
    # the lane's own .30 address on 18119, not loopback. The inherited loopback probe is rejected.
    services["recipe-reviewer"]["healthcheck"] = {
        "test": Override(
            ["CMD", "python", "-c",
             f"import socket; socket.create_connection(('{guard_network}.30',18119),2).close()"]
        )
    }
    services["postgres"]["profiles"] = Override([])
    services.update({POLICY: policy, RELAY: forwarder})
    layout["networks"] = Override(layout["networks"])
    layout["volumes"]["provider-socket"] = {"external": True, "name": SOCKET_VOLUME}
    return layout


def render(document, compose_root):
    validate(document)
    projects = {role: {"compose_project": f"{PREFIX}-{role}"} for role in ENDPOINTS}
    layout = render_layout(projects, compose_root)
    sources = layout["compose_sources"]
    template = pinned_file(sources[SOURCES[-1]]).decode()
    provider = document["provider"]
    lane_output = {}
    for role, lane in document["lanes"].items():
        network_layout = layout["x-pals-network-layout"][role]
        lane_output[role] = {
            "compose_project": projects[role]["compose_project"],
            "candidate_sha256": lane["candidate_sha256"],
            "environment_files": [
                str(Path(lane["runtime_directory"]) / name)
                for name in ("local.env", "release.env", "recipe.env")
            ],
            "base_files": [
                sources[name] for name in (SOURCES[0], SOURCES[2], SOURCES[1])
            ],
            "profile_overlay_yaml": app_overlay(template, lane, provider),
            "relay_overlay_yaml": yaml_text(
                lane_compose(network_layout, role, lane, provider)
            ),
        }
    provider_yaml = yaml_text(provider_compose(provider))
    pinned_file(provider["budget_ledger"])
    return {
        "status": "rendered_relay_compose",
        "activation_authorized": False,
        "runtime_verified": False,
        "compose_sources": sources,
        "lane_build_sources": document["build_sources"],
        "budget_continuity": provider["budget_ledger"],
        "single_ledger_writer": GUARD,
        "writer_handoff_verified": False,
        "provider_compose_yaml": provider_yaml,
        "lanes": lane_output,
    }
