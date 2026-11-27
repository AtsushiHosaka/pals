"""Read-only pre-activation proof for the existing local provider budget."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path

from budget_proxy import LIMIT, cost, validate_rollover
from lane_topology import OWNER, PROJECT, SERVICE, docker_reader
from lanes import PREFIX, absolute, fields, need, pin

GUARD = "worker-network-guard"
GUARD_ENTRYPOINT = ["python", "/opt/pals-local/guard.py"]
LEGACY_GUARD = f"/{PREFIX}-{GUARD}-1"
PASSIVE_LEGACY_ROLES = {"cognito-local", "localstack", "postgres"}
PRODUCERS = {"api", "worker", "assessment-worker", "recipe-reviewer", "reconciler"}
INSPECT = (
    '{"id":{{json .Id}},"name":{{json .Name}},"labels":{{json .Config.Labels}},'
    '"entrypoint":{{json .Config.Entrypoint}},'
    '"status":{{json .State.Status}},"running":{{json .State.Running}},'
    '"pid":{{json .State.Pid}},"started_at":{{json .State.StartedAt}},'
    '"finished_at":{{json .State.FinishedAt}},"mounts":{{json .Mounts}}}'
)


def overlaps_ledger(mount, directory):
    source = mount.get("Source")
    if (mount.get("Type") != "bind" or mount.get("RW") is not True
            or not isinstance(source, str) or not Path(source).is_absolute()):
        return False
    path = Path(source).resolve()
    return path == directory or path in directory.parents or directory in path.parents


def observed_handoff(run, original):
    ids = run("ps", "--all", "--quiet", "--no-trunc").split()
    need(len(ids) <= 256 and len(set(ids)) == len(ids) and all(map(pin, ids)),
         "bounded_budget_handoff_inventory_required")
    if not ids:
        return {}
    rows = [json.loads(line) for line in run(
        "inspect", "--type", "container", "--format", INSPECT, *ids
    ).splitlines()]
    need(len(rows) == len(ids) and {row["id"] for row in rows} == set(ids)
         and len({row["name"] for row in rows}) == len(ids), "budget_handoff_inventory_changed")
    relevant = {}
    for row in rows:
        name, labels = row["name"], row["labels"] or {}
        project, service = labels.get(PROJECT), labels.get(SERVICE)
        owned = labels.get("codex.owner") == OWNER
        legacy = project == PREFIX or name == LEGACY_GUARD
        need(not legacy or (owned and project == PREFIX and isinstance(service, str)
                            and (name != LEGACY_GUARD or service == GUARD)),
             "foreign_legacy_budget_container_refused")
        all_mounts = row["mounts"] or []
        mounts = [mount for mount in all_mounts if mount.get("Destination") == "/run/budget"]
        guard = service == GUARD or bool(mounts) or row["entrypoint"] == GUARD_ENTRYPOINT
        writer = any(overlaps_ledger(mount, original) for mount in all_mounts)
        if not (legacy or writer or (owned and (guard or service in PRODUCERS))):
            continue
        if legacy and service == GUARD:
            need(len(mounts) == 1 and mounts[0].get("Type") == "bind" and mounts[0].get("RW") is True
                 and isinstance(mounts[0].get("Source"), str) and Path(mounts[0]["Source"]).is_absolute()
                 and Path(mounts[0]["Source"]).resolve() == original,
                 "legacy_provider_guard_did_not_mount_original_ledger")
        if guard or writer or service not in PASSIVE_LEGACY_ROLES:
            need(row["status"] in {"exited", "created"} and row["running"] is False and row["pid"] == 0,
                 "provider_guard_or_producer_not_stopped")
            relevant[row["id"]] = row
    need(sum((row["labels"] or {}).get(PROJECT) == PREFIX
             and (row["labels"] or {}).get(SERVICE) == GUARD for row in relevant.values()) <= 1,
         "legacy_provider_guard_identity_ambiguous")
    return relevant


def read_ledger(path, expected):
    try:
        with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as stream:
            info = os.fstat(stream.fileno())
            need(stat.S_ISREG(info.st_mode) and stat.S_IMODE(info.st_mode) == 0o600
                 and info.st_uid == os.geteuid() and info.st_nlink == 1,
                 "private_original_budget_ledger_required")
            raw = stream.read()
        need(hashlib.sha256(raw).hexdigest() == expected, "archived_budget_ledger_hash_differs")
        value = json.loads(raw)
        rolled = value.get("rollover") is not None
        limit = validate_rollover(value, path.parent) if rolled else LIMIT
        actual, reserved, calls = value["actual_microusd"], value["reserved_microusd"], value["calls"]
        need(value["blocked"] is False and isinstance(calls, list) and (calls or rolled)
             and all(call["state"] == "completed" for call in calls)
             and type(actual) is int and type(reserved) is int and 0 <= actual == reserved <= limit
             and (rolled or value["limit_microusd"] >= LIMIT), "known_existing_budget_required_no_reset")
        amounts = [cost(call["model"], call["input_tokens"], call["output_tokens"]) for call in calls]
        need(all(amount == call["actual_microusd"] for amount, call in zip(amounts, calls))
             and sum(amounts) == actual, "previous_budget_usage_changed")
    except OSError:
        raise ValueError("existing_budget_ledger_required_no_reset") from None
    except (AttributeError, KeyError, TypeError, json.JSONDecodeError, UnicodeDecodeError):
        raise ValueError("known_existing_budget_required_no_reset") from None
    return (info.st_dev, info.st_ino), actual


def verify_budget_handoff(docker_socket, ledger_reference, original_directory, archived_ledger_sha256, *, run=None):
    """Compare a proposed bind to an independently archived original, observing Docker only.

    The caller supplies the original directory and SHA from the previously owned budget
    record independently of the proposed renderer input. The receipt proves an observed
    interval only. It reserves no resources and does not authorize starting a guard.
    """
    original = absolute(original_directory)
    path = original / "ledger.json"
    fields(ledger_reference, {"path", "sha256"}, "exact_handoff_budget_reference_required")
    need(pin(archived_ledger_sha256) and ledger_reference == {"path": str(path), "sha256": archived_ledger_sha256},
         "handoff_budget_reference_must_match_original_archive")
    need(original.is_dir() and original.resolve() == original, "original_budget_directory_required")
    run = docker_reader(docker_socket) if run is None else run
    before = observed_handoff(run, original)
    ledger = read_ledger(path, archived_ledger_sha256)
    after = observed_handoff(run, original)
    need(before == after and ledger == read_ledger(path, archived_ledger_sha256),
         "budget_handoff_changed_during_observation")
    legacy_present = any(row["labels"].get(PROJECT) == PREFIX and row["labels"].get(SERVICE) == GUARD
                         for row in after.values())
    return {
        "status": "verified_read_only",
        "ledger": ledger_reference.copy(),
        "legacy_guard": "stopped" if legacy_present else "absent",
        "actual_microusd": ledger[1],
        "observed_stopped_container_ids": sorted(after),
    }
