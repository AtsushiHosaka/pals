from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

PATH = (
    Path(__file__).resolve().parents[1] / "pals-scripts/harden-local-postgres-access.py"
)
SPEC = importlib.util.spec_from_file_location("local_pg_guard", PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_guard_precedes_broad_rule_preserves_existing_rules_and_is_idempotent():
    existing = "local all all trust\nhost all all all scram-sha-256\n"
    guarded = MODULE.guarded_hba(existing)
    assert guarded.endswith(existing)
    assert guarded.index("host all all 172.30.0.0/24 reject") < guarded.index(
        "host all all all"
    )
    assert "host replication all 172.30.0.0/24 reject" in guarded
    assert MODULE.guarded_hba(guarded) == guarded


@pytest.mark.parametrize("existing", [MODULE.BEGIN, MODULE.END, MODULE.BLOCK * 2])
def test_malformed_managed_block_is_rejected(existing):
    with pytest.raises(ValueError):
        MODULE.guarded_hba(existing)
