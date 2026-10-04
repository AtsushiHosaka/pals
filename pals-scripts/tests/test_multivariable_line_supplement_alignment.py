"""Source binding and cross-slot semantic checks for parameterized line integrals."""

from __future__ import annotations

import hashlib
import json
import runpy
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pals-agent"))
from pals_agent.typed_catalog_expansion import witness_source
from pals_agent.typed_local_catalog import load_typed_local_catalog_manifest

PATH = ROOT / "docs/multivariable-v5-line-supplement-batch.json"


def payload():
    return json.loads(PATH.read_text())


def card(suffix):
    return next(c for c in payload()["cards"] if c["id"].endswith("_" + suffix))


def names(c, roles):
    binder = ET.fromstring(c["openmath_xml"])[0]
    return dict(
        zip([d[-1].attrib["name"] for d in binder[1]], roles.split(), strict=True)
    )


def apps(c, operation):
    return [
        node
        for node in ET.fromstring(c["openmath_xml"]).iter()
        if node.tag.endswith("}OMA") and node[0].attrib.get("name") == operation
    ]


def decode(node, mapping):
    if node.tag.endswith("}OMV"):
        return mapping[node.attrib["name"]]
    if node.tag.endswith("}OMI"):
        return int(node.text)
    if node.tag.endswith("}OMA"):
        return (node[0].attrib["name"], *(decode(n, mapping) for n in node[1:]))
    raise AssertionError(node.tag)


def test_original_and_supplement_share_exact_unchanged_profile_and_load_separately():
    original_path = ROOT / "docs/multivariable-v5-batch.json"
    original = load_typed_local_catalog_manifest(original_path, repository_root=ROOT)
    supplement = load_typed_local_catalog_manifest(PATH, repository_root=ROOT)
    assert len(supplement.cards) == 4
    assert original.profile == supplement.profile
    assert supplement.authoring_status == "local_authoring_evidence_bound_not_admitted"
    old = json.loads(original_path.read_text())
    new = payload()
    for key in ("validator_sha256", "registry_sha256", "toolchain", "mathlib_revision"):
        assert old["evidence"][key] == new["evidence"][key]
    for key in ("id", "openmath_xml", "lean_target"):
        assert not ({c[key] for c in old["cards"]} & {c[key] for c in new["cards"]})
    source = ROOT / new["evidence"]["witness_path"]
    assert source.read_text() == witness_source(new["cards"])
    assert (
        "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest()
        == new["evidence"]["witness_sha256"]
    )
    generated = runpy.run_path(
        str(ROOT / "pals-scripts/generate-multivariable-v5-line-supplement-batch.py")
    )
    assert generated["cards"] == new["cards"]


def test_orientation_sign_is_negation_and_velocity_order_is_unchanged():
    c = card("orientation_law")
    mapping = names(c, "n D c u a b")
    integral_nodes = apps(c, "interval_integral")
    assert [tuple(decode(e, mapping) for e in n[2:]) for n in integral_nodes] == [
        ("b", "a"),
        ("a", "b"),
    ]
    minus = apps(c, "real_sub")[0]
    assert decode(minus[1], mapping) == ("real_nat", 0)
    for node in apps(c, "pullback_one_form"):
        assert tuple(decode(e, mapping) for e in node[1:]) == ("n", "D", "c", "u")


def test_bilinear_parts_uses_two_actual_velocities_in_the_correct_distinct_slots():
    c = card("bilinear_curve_integration_by_parts")
    mapping = names(c, "n D c u a b B d w")
    pulls = [
        tuple(decode(e, mapping) for e in n[1:]) for n in apps(c, "pullback_one_form")
    ]
    assert set(pulls) == {("n", "D", "c", "w"), ("n", "D", "u", "d")}
    assert len(apps(c, "interval_integrable")) == 2
    assert "HasDerivAt c (u t) t" in c["lean_target"]
    assert "HasDerivAt d (w t) t" in c["lean_target"]
    assert "B (c b) (d b) - B (c a) (d a)" in c["lean_target"]


def test_orientation_counterexample_has_actual_velocity_and_unequal_endpoints():
    c = card("orientation_counterexample")
    assert apps(c, "has_curve_deriv")
    assert apps(c, "basis_vector")
    assert apps(c, "scalar_fderiv_field")
    mapping = names(c, "n i x u a b")
    inequalities = apps(c, "neq")
    assert tuple(decode(e, mapping) for e in inequalities[0][1:]) == ("a", "b")
    assert len(inequalities) == 2
    assert "(i : Fin n)" in c["lean_target"]


def test_negative_and_proposed_bindings_are_total_without_advanced_inflation():
    ids = {c["id"] for c in payload()["cards"]}
    ns = json.loads(
        (ROOT / "docs/multivariable-v5-line-supplement-negatives.json").read_text()
    )["cases"]
    bs = json.loads(
        (
            ROOT / "docs/multivariable-v5-line-supplement-proposed-bindings.json"
        ).read_text()
    )
    assert {n["positive_card_id"] for n in ns} == ids
    assert {b["draft_id"] for b in bs} == ids
    assert len(ns) == len(bs) == len(ids) == 4
    assert all(b["difficulty"] != "advanced" for b in bs)
    assert {b["primary_mode"] for b in bs} == {
        "recognize",
        "justify_prove",
        "counterexample_audit",
        "synthesize",
    }


@pytest.mark.parametrize(
    "suffix",
    [
        "orientation_law",
        "split_parameter_interval",
        "orientation_counterexample",
        "bilinear_curve_integration_by_parts",
    ],
)
def test_sketches_are_substantive_and_no_unsafe_admissions(suffix):
    c = card(suffix)
    assert 4 <= len(c["sketch_steps"]) <= 10
    assert "sorry" not in c["lean_witness"]
    assert "admit" not in c["lean_witness"]
    assert "axiom" not in c["lean_witness"]
