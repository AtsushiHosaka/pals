#!/usr/bin/env python3
"""Close a blocked local budget ledger and open a new one. Owner approval only, never a reset."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
GUARD = "pals-reliability-local-worker-network-guard-1"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


proxy = load(
    "local_qualification_rollover_proxy", HERE / "local-qualification/budget_proxy.py"
)


class Refusal(Exception):
    pass


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def guard_running():
    """True while the guard container runs: it would overwrite the ledger from memory."""
    result = subprocess.run(
        [
            "docker",
            "ps",
            "-q",
            "--filter",
            "name=^/" + GUARD + "$",
            "--filter",
            "status=running",
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        raise Refusal("rollover_guard_state_unknown")
    return bool(result.stdout.strip())


def private_file(path, code):
    if path.is_symlink() or not path.is_file():
        raise Refusal(code)
    return path.read_bytes()


def write_exclusive(path, raw, mode):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    with os.fdopen(descriptor, "wb") as output:
        output.write(raw)
        output.flush()
        os.fsync(output.fileno())
    path.chmod(mode)


def rollover(runtime, approval_path, approval_sha256, *, guard_running_=None, now=None):
    """Archive the closed ledger byte-identically, then start the approved new one."""
    budget = Path(runtime).resolve() / "budget"
    ledger = budget / "ledger.json"
    if (guard_running_ or guard_running)():
        # A running guard holds the ledger in memory and writes it back on its next call.
        raise Refusal("rollover_requires_stopped_guard")
    approval_raw = private_file(
        Path(approval_path), "rollover_approval_record_required"
    )
    if sha(approval_raw) != approval_sha256:
        raise Refusal("rollover_approval_sha256_mismatch")
    closed_raw = private_file(ledger, "rollover_ledger_required")
    try:
        approval = json.loads(approval_raw)
        proxy.validate_approval(approval)
        closed_sha256 = sha(closed_raw)
        if approval["closed_ledger_sha256"] != closed_sha256:
            raise Refusal("rollover_ledger_sha256_mismatch")
        closed = json.loads(closed_raw)
        proxy.require_rollover_eligible(closed)
        totals = proxy.closed_totals(closed)
    except (KeyError, TypeError, AttributeError, json.JSONDecodeError):
        raise Refusal("rollover_ledger_or_approval_unreadable") from None
    except ValueError as error:
        raise Refusal(str(error)) from None
    archive = budget / ("closed-" + closed_sha256)
    if archive.exists() or archive.is_symlink():
        # Never written twice and never edited: an existing archive must already be exact.
        if (
            archive.is_symlink()
            or not archive.is_dir()
            or private_file(archive / "ledger.json", "rollover_archive_differs")
            != closed_raw
            or private_file(archive / "approval.json", "rollover_archive_differs")
            != approval_raw
        ):
            raise Refusal("rollover_archive_differs")
    else:
        archive.mkdir(mode=0o700)
        archive.chmod(0o700)
        write_exclusive(archive / "ledger.json", closed_raw, 0o400)
        write_exclusive(archive / "approval.json", approval_raw, 0o400)
    if sha((archive / "ledger.json").read_bytes()) != closed_sha256:
        raise Refusal("rollover_archive_differs")
    opened = {
        "limit_microusd": approval["new_limit_microusd"],
        "reserved_microusd": 0,
        "actual_microusd": 0,
        "blocked": False,
        "calls": [],
        "resumed_from_sha256": None,
        "rollover": {
            "schema_version": proxy.ROLLOVER_SCHEMA,
            "rolled_over_from_sha256": closed_sha256,
            "closed_totals": totals,
            "approval_sha256": approval_sha256,
            "rolled_over_at": (now or datetime.now(timezone.utc)).isoformat(),
        },
    }
    try:
        # The same proof prepare and the proxy repeat before they accept this ledger.
        proxy.validate_rollover(opened, budget)
    except ValueError as error:
        raise Refusal(str(error)) from None
    raw = json.dumps(opened, sort_keys=True).encode()
    temporary = budget / ("ledger.json.rollover-" + closed_sha256[:16])
    temporary.unlink(missing_ok=True)
    write_exclusive(temporary, raw, 0o600)
    # The closed ledger is replaced only after its exact archive exists.
    if ledger.read_bytes() != closed_raw:
        temporary.unlink()
        raise Refusal("rollover_ledger_changed_during_rollover")
    os.replace(temporary, ledger)
    return {
        "state": "rolled_over_not_prepared",
        "closed_ledger": {
            "path": str(archive / "ledger.json"),
            "sha256": closed_sha256,
        },
        "approval": {"path": str(archive / "approval.json"), "sha256": approval_sha256},
        "closed_totals": totals,
        "new_ledger_sha256": sha(raw),
        "new_limit_microusd": approval["new_limit_microusd"],
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--runtime-dir", type=Path, required=True)
    p.add_argument("--approval", type=Path, required=True)
    p.add_argument("--approval-sha256", required=True)
    a = p.parse_args()
    try:
        result = rollover(a.runtime_dir, a.approval, a.approval_sha256)
    except Refusal as error:
        print(json.dumps({"state": "refused", "code": str(error)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
