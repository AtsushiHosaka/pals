"""Real authoring parsers and filesystem checks; no publication/DB/model doubles."""

import hashlib
import importlib.util
import json
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "usable_catalog_audit", ROOT / "pals-scripts/audit-usable-catalog.py"
)
assert SPEC is not None and SPEC.loader is not None
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)
API = Path(os.environ.get("PALS_AUDIT_API_REPOSITORY", str(ROOT / "pals-api")))
AUTHORING = Path(__file__).resolve().parent / "fixtures/usable-catalog-authoring-v1"


def write_manifest(directory: Path, name: str, *, template="requested.rank_nullity", **updates) -> Path:
    """Modify an actual rank-nullity authoring input, not an evidence receipt."""
    value = json.loads((AUTHORING / (template + ".json")).read_bytes())
    value.update(updates)
    path = directory / name
    path.write_bytes(audit.api_adapter(API).canonical_json_bytes(value))
    return path


def test_repository_manifests_are_real_candidates_never_runtime_proof():
    expected_files = {
        "requested.rank_nullity.json":
            "153e60c5d31f1f8154bbe68361b7f35e6bd768d3126ae2790eddc2b5bd7050be",
        "requested.composite_injective_implies_first.json":
            "642b8563404ffb75fc6aa17872b3aee4852eefde365201b91bc6fcb82cc10df8",
    }
    assert {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in AUTHORING.glob("*.json")} == expected_files
    result = audit.audit(AUTHORING, API)
    assert result["candidate_count"] == 2
    assert result["candidate_exact_target_text_groups"] == 2
    assert {row["recipe_id"] for row in result["records"]} == {
        "requested.rank_nullity", "requested.composite_injective_implies_first"
    }
    assert result["verified_usable_count"] is None
    assert result["eligible_published_count"] is None
    assert result["counted_usable_count"] == 0
    assert result["database_read"] is False
    assert all(row["counted_usable"] is False for row in result["records"])
    assert all(row["publication_state"] == "not_checked" for row in result["records"])
    replay = audit.audit(AUTHORING, API, expected_snapshot=result["snapshot_sha256"])
    assert replay["snapshot_sha256"] == result["snapshot_sha256"]


def test_identical_targets_different_ids_do_not_increase_exact_problem_groups(tmp_path):
    write_manifest(tmp_path, "a.json")
    write_manifest(tmp_path, "b.json", recipe_id="review.other_rank_nullity")
    result = audit.audit(tmp_path, API)
    assert result["candidate_count"] == 2
    assert result["candidate_exact_target_text_groups"] == 1
    assert result["exclusion_counts"]["duplicate_current_operational_target"] == 1
    assert result["counted_usable_count"] == 0


def test_old_and_duplicate_revisions_cannot_inflate_counts(tmp_path):
    write_manifest(tmp_path, "a.json", revision=1)
    write_manifest(tmp_path, "b.json", revision=2)
    write_manifest(tmp_path, "c.json", revision=2)
    result = audit.audit(tmp_path, API)
    assert result["candidate_count"] == 3
    assert result["candidate_exact_target_text_groups"] == 1
    assert result["exclusion_counts"]["superseded_candidate_revision"] == 1
    assert result["exclusion_counts"]["duplicate_candidate_revision"] == 1
    assert result["counted_usable_count"] == 0
    assert result["current_candidate_count"] == 1


def test_conflicting_same_recipe_revision_fails_closed(tmp_path):
    write_manifest(tmp_path, "rank.json")
    write_manifest(tmp_path, "composite.json", template="requested.composite_injective_implies_first",
                   recipe_id="requested.rank_nullity")
    with pytest.raises(audit.InventoryError, match="conflicting contents"):
        audit.audit(tmp_path, API)


def test_old_target_cannot_shadow_another_current_candidate(tmp_path):
    write_manifest(tmp_path, "a-old.json", recipe_id="review.a", revision=1)
    write_manifest(tmp_path, "a-new.json", template="requested.composite_injective_implies_first",
                   recipe_id="review.a", revision=2)
    write_manifest(tmp_path, "b-current.json", recipe_id="review.b", revision=1)
    result = audit.audit(tmp_path, API)
    b = next(row for row in result["records"] if row["recipe_id"] == "review.b")
    assert b["current_candidate"] is True
    assert "duplicate_current_operational_target" not in b["exclusions"]
    assert result["current_candidate_count"] == 2
    assert result["current_candidate_operational_groups"] == 2
    assert result["candidate_count"] == 3


def test_same_target_text_different_toolchains_are_separate_operational_groups(tmp_path):
    write_manifest(tmp_path, "a.json", recipe_id="review.a")
    path = write_manifest(tmp_path, "b.json", recipe_id="review.b")
    value = json.loads(path.read_bytes())
    value["toolchain"]["fingerprint"]["verifier_sha256"] = "1" * 64
    path.write_bytes(audit.api_adapter(API).canonical_json_bytes(value))
    result = audit.audit(tmp_path, API)
    assert result["candidate_exact_target_text_groups"] == 1
    assert result["current_candidate_operational_groups"] == 2
    assert "duplicate_current_operational_target" not in result["exclusion_counts"]


def test_cached_parser_cannot_be_relabeled_with_another_pin():
    adapter = audit.api_adapter(API)
    root = API.resolve()
    actual = audit.api_source_pin(API)
    assert Path(adapter.__file__).resolve().is_relative_to(root)
    imported = audit._API_IMPORT_PINS[root]
    try:
        # This corrupts only provenance metadata, not a repository or model boundary.
        audit._API_IMPORT_PINS[root] = {**actual, "revision": "0" * 40}
        with pytest.raises(audit.InventoryError, match="import-time provenance"):
            audit.api_adapter(API)
    finally:
        audit._API_IMPORT_PINS[root] = imported


def test_changed_api_revision_pin_is_rejected():
    actual = audit.api_source_pin(API)
    with pytest.raises(audit.InventoryError, match="changed during audit"):
        audit.require_api_pin(API, {**actual, "revision": "0" * 40})


def test_dirty_owning_source_fails_before_import(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, timeout=5)
    path = tmp_path / "app/domain/recipe_catalog_admission.py"
    path.parent.mkdir(parents=True)
    path.write_bytes((API / "app/domain/recipe_catalog_admission.py").read_bytes())
    with pytest.raises(audit.InventoryError, match="must be clean"):
        audit.api_source_pin(tmp_path)


@pytest.mark.parametrize("field", ["active", "admitted", "retrievable", "runtime_verified"])
@pytest.mark.parametrize("value", [False, True])
def test_self_asserted_lifecycle_fields_are_rejected_not_promoted(tmp_path, field, value):
    write_manifest(tmp_path, "entry.json", **{field: value})
    with pytest.raises(ValueError):
        audit.audit(tmp_path, API)


def test_unreviewed_authoring_has_no_authenticated_publication_evidence(tmp_path):
    write_manifest(tmp_path, "entry.json")
    result = audit.audit(tmp_path, API)
    assert result["exclusion_counts"]["no_authenticated_publication_evidence"] == 1
    assert result["records"][0]["runtime_state"] == "not_checked"


def test_snapshot_pin_rejects_another_collection(tmp_path):
    write_manifest(tmp_path, "entry.json")
    with pytest.raises(audit.InventoryError, match="expected pin"):
        audit.audit(tmp_path, API, expected_snapshot="0" * 64)


def test_noncanonical_and_placeholder_source_is_rejected(tmp_path):
    path = write_manifest(tmp_path, "entry.json")
    path.write_text(json.dumps(json.loads(path.read_bytes()), indent=2))
    with pytest.raises(ValueError):
        audit.audit(tmp_path, API)
    write_manifest(tmp_path, "entry.json", proof_body="by sorry")
    with pytest.raises(ValueError):
        audit.audit(tmp_path, API)


def test_symlink_and_empty_input_fail_closed(tmp_path):
    with pytest.raises(audit.InventoryError, match="1 to 10000"):
        audit.audit(tmp_path, API)
    (tmp_path / "entry.json").symlink_to(AUTHORING / "requested.rank_nullity.json")
    with pytest.raises(audit.InventoryError, match="symlinks"):
        audit.audit(tmp_path, API)
