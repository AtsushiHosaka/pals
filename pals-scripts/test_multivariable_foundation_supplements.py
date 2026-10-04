"""Artifact, dependent-type and semantic-slot checks for the targeted supplements."""

from __future__ import annotations

import copy
import hashlib
import json
import runpy
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pals-agent"))
from pals_agent.openmath import MathXMLValidationError
from pals_agent.typed_catalog_expansion import validate_expansion_batch
from pals_agent.typed_multivariable_v5 import (
    validate_canonical_typed_multivariable_v5_openmath_xml as valid5,
)

STEMS = ["multivariable-v5", "calculus-v4"]
DATA = {
    stem: json.loads((ROOT / f"docs/{stem}-foundation-supplement.json").read_text())
    for stem in STEMS
}
CARDS = {c["id"]: c for data in DATA.values() for c in data["cards"]}
NS = {"om": "http://www.openmath.org/OpenMath"}


def applications(key, symbol):
    node = ET.fromstring(CARDS["mv_foundation_" + key]["openmath_xml"])
    return [
        n for n in node.findall(".//om:OMA", NS) if n[0].attrib.get("name") == symbol
    ]


def variables(node):
    return [n.attrib["name"] for n in node.findall(".//om:OMV", NS)]


@pytest.mark.parametrize("stem", STEMS)
def test_original_and_supplement_same_profile_validate_independently(stem):
    for suffix in ["batch", "foundation-supplement"]:
        payload = json.loads((ROOT / f"docs/{stem}-{suffix}.json").read_text())
        validate_expansion_batch(payload, repository_root=ROOT)


@pytest.mark.parametrize("stem", STEMS)
def test_exact_witness_and_pins(stem):
    data = DATA[stem]
    expected = (
        "import Mathlib\n\n"
        + "\n\n".join(
            "-- manifest card: "
            + c["id"]
            + "\n"
            + c["lean_target"]
            + " := "
            + c["lean_witness"].rstrip()
            for c in data["cards"]
        )
        + "\n"
    )
    witness = (ROOT / data["evidence"]["witness_path"]).read_bytes()
    assert witness == expected.encode()
    assert (
        data["evidence"]["witness_sha256"]
        == "sha256:" + hashlib.sha256(witness).hexdigest()
    )
    for c in data["cards"]:
        assert 4 <= len(c["sketch_steps"]) <= 10
        assert not any(
            word in c["lean_witness"].split() for word in ["sorry", "admit", "axiom"]
        )


@pytest.mark.parametrize("stem", STEMS)
def test_every_card_has_exact_negative_pair(stem):
    negatives = json.loads(
        (ROOT / f"docs/{stem}-foundation-supplement-negatives.json").read_text()
    )
    assert negatives["profile_id"] == DATA[stem]["profile_id"]
    pairs = [i for case in negatives["cases"] for i in case["paired_card_ids"]]
    assert sorted(pairs) == sorted(c["id"] for c in DATA[stem]["cards"])
    assert all(
        c["mathematical_reason"] and c["candidate_question"] for c in negatives["cases"]
    )


def test_proposed_bindings_resolve_exact_manifests():
    bindings = json.loads(
        (ROOT / "docs/multivariable-foundation-supplement-bindings.json").read_text()
    )["bindings"]
    assert len(bindings) == 13
    assert {b["draft_id"] for b in bindings} == set(CARDS)
    assert len({b["family_id"] for b in bindings}) == 7
    for b in bindings:
        assert b["draft_id"] in {
            c["id"]
            for c in json.loads((ROOT / b["authoring_manifest"]).read_text())["cards"]
        }
        assert b["admission_manifest"] is None
        assert b["primary_mode"] in {
            "recognize",
            "compute_construct",
            "justify_prove",
            "counterexample_audit",
            "synthesize",
        }


def test_generator_matches_all_authored_bytes():
    generated = runpy.run_path(
        str(ROOT / "pals-scripts/generate-multivariable-foundation-supplements.py")
    )
    assert generated["BATCHES"][5] == DATA["multivariable-v5"]["cards"]
    assert generated["BATCHES"][4] == DATA["calculus-v4"]["cards"]


@pytest.mark.parametrize("stem", STEMS)
def test_no_literal_xml_duplicate_against_original_or_within_batch(stem):
    original = json.loads((ROOT / f"docs/{stem}-batch.json").read_text())
    old = {c["openmath_xml"] for c in original["cards"]}
    new = [c["openmath_xml"] for c in DATA[stem]["cards"]]
    assert not old.intersection(new)
    assert len(set(new)) == len(new)


def test_jacobian_rows_outputs_columns_inputs_and_velocity_point():
    entries = applications("zero_totalized_jacobian_counterexample", "matrix_entry")
    assert variables(entries[0]) == ["v2", "v1", "v1", "v2", "v5", "v1", "v6", "v7"]
    action = applications("jacobian_curve_velocity", "matrix_action")[0]
    assert variables(action) == ["v2", "v1", "v1", "v2", "v3", "v1", "v4", "v6", "v5"]
    derivative = applications("jacobian_curve_velocity", "has_curve_deriv")[-1]
    assert derivative[2].attrib["name"] == "v7"
    assert derivative[3].attrib["name"] == "v6"


def test_hessian_candidate_and_transpose_are_explicit():
    hs = applications("quadratic_hessian_criterion", "has_field_derivative")
    assert all(n[-1].attrib["name"] == "v3" for n in hs)
    assert applications("quadratic_hessian_criterion", "symmetrize")
    assert applications(
        "quadratic_hessian_missing_flip_counterexample", "bilinear_apply"
    )


def test_lagrange_function_order_constraint_regular_direction():
    p = applications("lagrange_multiplier_from_direction", "local_extr_fiber")[0]
    assert variables(p) == ["v1", "v3", "v2", "v6"]
    assert (
        "hu : A u ≠ 0"
        in CARDS["mv_foundation_lagrange_multiplier_from_direction"]["lean_target"]
    )
    assert (
        "∀ t : ℝ"
        in CARDS["mv_foundation_lagrange_multiplier_from_direction"]["lean_target"]
    )


def test_section_counterexample_is_product_integrable_not_all_sections():
    assert applications("exceptional_section_counterexample", "product_integrable")
    section = applications(
        "exceptional_section_counterexample", "product_scalar_slice_right"
    )[0]
    assert variables(section) == ["v1", "v2", "v6", "v1"]
    assert section[-1][0].attrib["name"] == "zero"
    assert applications("exceptional_section_counterexample", "not")


def test_gradient_slot_is_point_then_vector_and_exact_residual_hypothesis():
    g = applications("exact_residual_minimum", "has_gradient")[0]
    assert g[-2].attrib["name"] == "v5"
    assert g[-1][0].attrib["name"] == "vector_zero"
    assert (
        "hx : A x = b" in CARDS["mv_foundation_exact_residual_minimum"]["lean_target"]
    )


@pytest.mark.parametrize("mutation", ["dimension", "unbound", "missing_argument"])
def test_jacobian_dimension_and_binding_fail_closed(mutation):
    node = ET.fromstring(CARDS["mv_foundation_jacobian_curve_velocity"]["openmath_xml"])
    action = next(
        n
        for n in node.findall(".//om:OMA", NS)
        if n[0].attrib.get("name") == "matrix_action"
    )
    if mutation == "dimension":
        action[1].set("name", "v1")
    elif mutation == "unbound":
        action[-1].set("name", "unbound_velocity")
    else:
        action.remove(action[-1])
    with pytest.raises(MathXMLValidationError):
        valid5(ET.tostring(node, encoding="unicode"))


def test_semantic_witness_tampering_rejected():
    data = copy.deepcopy(DATA["multivariable-v5"])
    data["cards"][0]["lean_target"] = data["cards"][0]["lean_target"].replace(
        "A (Pi.single i 1)", "A x"
    )
    with pytest.raises(ValueError):
        validate_expansion_batch(data, repository_root=ROOT)
