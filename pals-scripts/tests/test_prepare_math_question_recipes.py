"""Preparation keeps source immutable and refuses missing or stale review evidence."""

import importlib.util
import json
from pathlib import Path

import pytest
import rfc8785

spec = importlib.util.spec_from_file_location(
    "prepare_math_question_recipes",
    Path(__file__).resolve().parents[1] / "prepare-math-question-recipes.py",
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def inputs():
    source = "import Mathlib\n\ntheorem prepared_example : ∀ x : ℝ, 0 ≤ x ^ 2 := by\n  intro x\n  positivity\n"
    from app.domain.lean_target import extract_single_target_declaration

    target = extract_single_target_declaration(source)
    result = {
        "passed": True,
        "lean_verified": True,
        "verification": {"success": True},
        "lean_source": source,
        "target": target.as_dict(),
        "semantic_review": {"decision": "approved", "session_id": "semantic"},
        "answer_review": {"session_id": "output"},
        "explanation": {"overview": "Squares are nonnegative."},
    }
    metadata = {
        "statement": "Are real squares nonnegative?",
        "domain": "real numbers",
        "assumptions": [],
        "quantifiers": ["all real x"],
        "conclusion": "0 ≤ x²",
        "search_text": "real square nonnegativity",
        "output_language": "en",
        "question_variants": ["Determine whether every real square is nonnegative."],
    }
    author = "pals.principal.v1/author/preparation-tests"
    review = {
        "schema_version": "pals.math-question-preparation-review.v1",
        "reviewer_principal": "pals.principal.v1/reviewer/preparation-tests",
        "semantic_approved": True,
        "output_approved": True,
        "question_variants_equivalent": True,
        "rationale": "Exact artifact review.",
    }
    kwargs = {
        "recipe_id": "math.question.preparation",
        "revision": 1,
        "author": author,
        "toolchain_id": "preparation.test.v1",
        "fingerprint": {
            "schema_version": "pals.lean-toolchain-fingerprint.v1",
            "lean_version": "leanprover/lean4:v4.32.0-rc1",
            "lake_manifest_sha256": "a" * 64,
            "verifier_sha256": "b" * 64,
            "materializer_version": "pals.recipe-materializer.v1",
        },
    }
    return result, review, metadata, kwargs


def bind(result, review, metadata):
    payload = json.dumps(result).encode()
    review.update(
        {
            "runtime_result_sha256": module.digest(payload),
            "lean_sha256": module.digest(result["lean_source"].encode()),
            "target_sha256": module.digest(result["target"]["proposition"].encode()),
            "explanation_sha256": module.digest(rfc8785.dumps(result["explanation"])),
            "metadata_sha256": module.digest(rfc8785.dumps(metadata)),
        }
    )
    return payload


def test_exact_source_and_question_variants_remain_unsealed():
    result, review, metadata, kwargs = inputs()
    files = module.prepare(bind(result, review, metadata), review, metadata, **kwargs)
    assert files["source.lean"] == result["lean_source"].encode()
    manifest = json.loads(files["authoring-manifest.json"])
    assert manifest["lean_code"] == result["lean_source"]
    proposal = json.loads(files["search-proposal.json"])
    assert proposal["metadata"]["question_variants"] == metadata["question_variants"]
    assert proposal["status"] == "prepared_not_admitted"
    assert "compiler_receipt_sha256" not in proposal
    assert "review_signature" not in proposal


@pytest.mark.parametrize("field", ["passed", "lean_verified"])
def test_failed_runtime_is_rejected(field):
    result, review, metadata, kwargs = inputs()
    result[field] = False
    with pytest.raises(ValueError, match="not successful"):
        module.prepare(bind(result, review, metadata), review, metadata, **kwargs)


def test_source_hash_or_changed_question_invalidates_review():
    result, review, metadata, kwargs = inputs()
    payload = bind(result, review, metadata)
    review["lean_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="hash mismatch"):
        module.prepare(payload, review, metadata, **kwargs)
    bind(result, review, metadata)
    metadata["question_variants"] = ["Are all real numbers nonnegative?"]
    with pytest.raises(ValueError, match="hash mismatch"):
        module.prepare(payload, review, metadata, **kwargs)


@pytest.mark.parametrize(
    "field", ["semantic_approved", "output_approved", "question_variants_equivalent"]
)
def test_no_external_approval_is_rejected(field):
    result, review, metadata, kwargs = inputs()
    payload = bind(result, review, metadata)
    review[field] = False
    with pytest.raises(ValueError, match="approvals required"):
        module.prepare(payload, review, metadata, **kwargs)


def test_missing_runtime_reviews_and_wrong_target_fail():
    result, review, metadata, kwargs = inputs()
    result["semantic_review"]["decision"] = "rejected"
    with pytest.raises(ValueError, match="semantic approval"):
        module.prepare(bind(result, review, metadata), review, metadata, **kwargs)
    result["semantic_review"]["decision"] = "approved"
    result["target"]["proposition"] = "False"
    with pytest.raises(ValueError, match="target differs"):
        module.prepare(bind(result, review, metadata), review, metadata, **kwargs)


def test_raw_policy_rejects_source_rewrite_requirements():
    result, review, metadata, kwargs = inputs()
    result["lean_source"] = result["lean_source"].replace(
        "import Mathlib", "import Mathlib.Data.Real.Basic"
    )
    with pytest.raises(ValueError, match="environment"):
        module.prepare(bind(result, review, metadata), review, metadata, **kwargs)


def test_duplicate_json_and_malformed_toolchain_are_rejected():
    result, review, metadata, kwargs = inputs()
    with pytest.raises(ValueError):
        module.prepare(b'{"passed":true,"passed":false}', review, metadata, **kwargs)
    kwargs["fingerprint"]["verifier_sha256"] = "unobserved"
    with pytest.raises(ValueError):
        module.prepare(bind(result, review, metadata), review, metadata, **kwargs)


def test_outputs_refuse_repository_and_overwrite(tmp_path):
    with pytest.raises(ValueError, match="outside"):
        module.write_outputs(module.ROOT / "output", {"one": b"data"})
    module.write_outputs(tmp_path, {"one": b"original"})
    module.write_outputs(tmp_path, {"one": b"original"})
    with pytest.raises(ValueError, match="overwrite"):
        module.write_outputs(tmp_path, {"one": b"changed", "two": b"new"})
    assert (tmp_path / "one").read_bytes() == b"original"
    assert not (tmp_path / "two").exists()


def materialized_inputs():
    result, review, metadata, kwargs = inputs()
    result["lean_source"] = result["lean_source"].replace(
        "theorem prepared_example :", "example :"
    )
    from app.domain.lean_target import extract_single_target_declaration

    result["target"] = extract_single_target_declaration(
        result["lean_source"]
    ).as_dict()
    return result, review, metadata, kwargs


def test_materialized_requires_explicit_policy_and_preserves_reviewed_bytes():
    result, review, metadata, kwargs = materialized_inputs()
    payload = bind(result, review, metadata)
    with pytest.raises(ValueError, match="named"):
        module.prepare(payload, review, metadata, **kwargs)
    files = module.prepare(
        payload, review, metadata, admission_policy="materialized", **kwargs
    )
    from app.domain.recipe_catalog_admission import (
        RecipeAuthoringManifestV1,
        RecipeMaterializerV1,
    )

    parsed = RecipeAuthoringManifestV1.parse(files["authoring-manifest.json"])
    assert (
        RecipeMaterializerV1.materialize(parsed)
        == files["source.lean"]
        == result["lean_source"].encode()
    )
    assert (
        json.loads(files["search-proposal.json"])["admission_policy"] == "materialized"
    )


@pytest.mark.parametrize("change", ["name", "import", "spacing", "trailing"])
def test_materialized_policy_never_normalizes_generated_source(change):
    result, review, metadata, kwargs = materialized_inputs()
    edits = {
        "name": ("example :", "theorem named :"),
        "import": ("import Mathlib", "import Mathlib.Data.Real.Basic"),
        "spacing": ("example : ∀", "example :  ∀"),
        "trailing": ("  positivity\n", "  positivity"),
    }
    result["lean_source"] = result["lean_source"].replace(*edits[change])
    from app.domain.lean_target import extract_single_target_declaration

    result["target"] = extract_single_target_declaration(
        result["lean_source"]
    ).as_dict()
    with pytest.raises(ValueError, match="exact previously reverified"):
        module.prepare(
            bind(result, review, metadata),
            review,
            metadata,
            admission_policy="materialized",
            **kwargs,
        )


def test_changed_source_cannot_reuse_pretransformation_approvals():
    result, review, metadata, kwargs = inputs()
    bind(result, review, metadata)
    result["lean_source"] = result["lean_source"].replace(
        "theorem prepared_example :", "example :"
    )
    from app.domain.lean_target import extract_single_target_declaration

    result["target"] = extract_single_target_declaration(
        result["lean_source"]
    ).as_dict()
    with pytest.raises(ValueError, match="hash mismatch"):
        module.prepare(
            json.dumps(result).encode(),
            review,
            metadata,
            admission_policy="materialized",
            **kwargs,
        )
