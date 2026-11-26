"""Read-only network rendering for the opt-in local qualification lanes."""

from __future__ import annotations

import hashlib
from ipaddress import IPv4Address, IPv4Network
from pathlib import Path

from lanes import ENDPOINTS, RELAY_REQUIRED, absolute, need, validate

SOURCES = (
    "docker-compose.yml",
    "docker-compose.e2e.yml",
    "pals-infra/docker-compose.localstack.yml",
    "pals-scripts/local-qualification/compose.override.yml.in",
)
BRIDGE_SUBNETS = {
    "primary": {"e2e": "172.30.0.0/24", "database": "172.30.1.0/24"},
    "standby": {"e2e": "172.30.2.0/24", "database": "172.30.3.0/24"},
}
PUBLISHED = {
    "api": ("api", 8000),
    "webfront": ("web", 3000),
    "localstack": ("localstack", 4566),
    "cognito-local": ("cognito", 9229),
    "postgres": ("postgres", 5432),
}
ATTACHMENTS = {
    "api": {"e2e", "database"},
    "reconciler": {"e2e", "database"},
    "schema-release": {"e2e", "database"},
    "postgres": {"database"},
    "webfront": {"e2e"},
    "localstack": {"e2e"},
    "cognito-local": {"e2e"},
    "verifier": {"e2e"},
}
STATE_VOLUMES = {
    "postgres-data": ("postgres", "/var/lib/postgresql/data"),
    "localstack-data": ("localstack", "/var/lib/localstack"),
    "cognito-local-data": ("cognito-local", "/app/.cognito"),
}


def read_yaml(raw):
    try:
        import yaml
    except ImportError:
        raise ValueError("compose_layout_requires_pyyaml") from None

    class ComposeLoader(yaml.SafeLoader):
        pass

    def compose_override(loader, node):
        # Preserve the structural value of the Compose tag for this offline projection.
        if isinstance(node, yaml.SequenceNode):
            return loader.construct_sequence(node)
        if isinstance(node, yaml.MappingNode):
            return loader.construct_mapping(node)
        return loader.construct_scalar(node)

    for tag in ("!override", "!reset"):
        ComposeLoader.add_constructor(tag, compose_override)
    try:
        result = yaml.load(raw, Loader=ComposeLoader)
    except yaml.YAMLError:
        raise ValueError("local_lane_compose_source_invalid") from None
    need(type(result) is dict, "local_lane_compose_source_invalid")
    return result


def source_documents(compose_root: Path):
    root = absolute(str(compose_root)).resolve(strict=True)
    raw = {}
    references = {}
    for name in SOURCES:
        path = root / name
        need(
            path.resolve(strict=True) == path and path.is_file(),
            "local_lane_compose_source_required",
        )
        with path.open("rb") as stream:
            value = stream.read(131_073)
        need(0 < len(value) <= 131_072, "local_lane_compose_source_invalid")
        raw[name] = value
        references[name] = {
            "path": str(path),
            "sha256": hashlib.sha256(value).hexdigest(),
        }
    base, e2e, infrastructure = (read_yaml(raw[name]) for name in SOURCES[:3])
    return base, e2e, infrastructure, references


def validate_sources(base, e2e, infrastructure):
    for service, (_endpoint, internal) in PUBLISHED.items():
        carrier = base if service == "postgres" else e2e
        ports = carrier["services"][service]["ports"]
        need(
            type(ports) is list
            and len(ports) == 1
            and isinstance(ports[0], str)
            and ports[0].endswith(f":{internal}"),
            "local_lane_compose_port_source_changed",
        )
    for volume, (service, target) in STATE_VOLUMES.items():
        carrier = base if service == "postgres" else infrastructure
        need(
            volume in carrier["volumes"]
            and f"{volume}:{target}" in carrier["services"][service]["volumes"],
            "local_lane_compose_volume_source_changed",
        )
    networks = e2e["networks"]
    need(
        set(networks) == {"e2e", "database"},
        "local_lane_compose_network_source_changed",
    )
    for key, subnet in BRIDGE_SUBNETS["primary"].items():
        value = networks[key]
        need(
            value["driver"] == "bridge"
            and value["ipam"]["config"] == [{"subnet": subnet}],
            "local_lane_compose_network_source_changed",
        )


def remap_attachments(e2e, role):
    result = {}
    addresses = set()
    for service, expected in sorted(ATTACHMENTS.items()):
        links = e2e["services"][service]["networks"]
        if isinstance(links, list):
            links = dict.fromkeys(links, {})
        need(
            type(links) is dict and set(links) == expected,
            "local_lane_compose_attachment_changed",
        )
        attachments = {}
        for network, config in links.items():
            need(
                type(config) is dict and set(config) <= {"ipv4_address", "aliases"},
                "local_lane_compose_attachment_changed",
            )
            item = config.copy()
            if "ipv4_address" in item:
                old = IPv4Network(BRIDGE_SUBNETS["primary"][network])
                new = IPv4Network(BRIDGE_SUBNETS[role][network])
                address = IPv4Address(item["ipv4_address"])
                need(
                    address in old
                    and address not in {old.network_address, old.broadcast_address}
                    and address not in addresses,
                    "local_lane_compose_address_source_changed",
                )
                addresses.add(address)
                item["ipv4_address"] = str(
                    new.network_address + (int(address) - int(old.network_address))
                )
            attachments[network] = item
        result[service] = {"networks": attachments}
    return result


def render(document, compose_root):
    validate(document)
    return render_layout(document["lanes"], compose_root)


def render_layout(lanes, compose_root):
    base, e2e, infrastructure, references = source_documents(compose_root)
    validate_sources(base, e2e, infrastructure)
    service_sources = e2e["services"]
    peer = service_sources["api"]["networks"]["e2e"]["ipv4_address"]
    setting = "PALS_RECONCILER_TRIGGER_ALLOWED_PEER_IP"
    need(
        service_sources["reconciler"]["environment"][setting] == peer,
        "local_lane_reconciler_peer_source_changed",
    )
    layouts = {}
    for role, lane in lanes.items():
        project = lane["compose_project"]
        services = remap_attachments(e2e, role)
        services["reconciler"]["environment"] = {
            setting: services["api"]["networks"]["e2e"]["ipv4_address"]
        }
        for service, (endpoint, target) in PUBLISHED.items():
            services[service]["ports"] = [
                {
                    "host_ip": "127.0.0.1",
                    "target": target,
                    "published": str(ENDPOINTS[role][endpoint]),
                    "protocol": "tcp",
                }
            ]
        layouts[role] = {
            "name": project,
            "networks": {
                name: {
                    "name": project + "-" + name,
                    "driver": "bridge",
                    "ipam": {"config": [{"subnet": subnet}]},
                }
                for name, subnet in BRIDGE_SUBNETS[role].items()
            },
            "volumes": {name: {"name": project + "-" + name} for name in STATE_VOLUMES},
            "services": services,
        }
    # An extension document rather than application services at its root. This result is
    # neither a Compose launch manifest nor evidence that either product ran.
    return {
        "status": "validated_network_layout",
        "launchable": False,
        "blocker": RELAY_REQUIRED,
        "compose_sources": references,
        "x-pals-network-layout": layouts,
    }
