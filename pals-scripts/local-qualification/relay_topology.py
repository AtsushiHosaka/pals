"""Frozen relay topology contract. Docker metadata readback only, no publication."""

from lane_topology import POLICY as POLICY
from lane_topology import PROVIDER_PROJECT as PROVIDER_PROJECT
from lane_topology import RELAY as RELAY
from lane_topology import RELAY_SCHEMA as SCHEMA
from lane_topology import SHIM as SHIM
from lane_topology import SOCKET_MOUNT as SOCKET_MOUNT
from lane_topology import SOCKET_VOLUME as SOCKET_VOLUME
from lane_topology import validate_relay, verify_relay
from lanes import fields, need, read_document
from lanes import read as read_layout

__all__ = [
    "SCHEMA",
    "POLICY",
    "RELAY",
    "SHIM",
    "PROVIDER_PROJECT",
    "SOCKET_VOLUME",
    "SOCKET_MOUNT",
    "read",
    "verify",
]


def layout(document):
    fields(
        document,
        {"schema_version", "layout", "authority_shim", "lanes"},
        "local_relay_binding_invalid",
    )
    reference = document["layout"]
    fields(reference, {"path", "sha256"}, "exact_local_relay_layout_ref_required")
    validated = read_layout(reference["path"], reference["sha256"])
    validate_relay(validated, document)
    return validated


def read(path, sha256):
    document = read_document(path, sha256)
    layout(document)
    return document


def verify(document, *, run=None):
    before = layout(document)
    result = verify_relay(before, document, run=run)
    need(layout(document) == before, "local_relay_binding_changed")
    return result
