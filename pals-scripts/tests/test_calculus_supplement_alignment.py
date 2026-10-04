"""Independent source, role, and closed-profile checks for curriculum supplements."""

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
from pals_agent.typed_local_catalog import (
    TypedLocalCatalogError,
    load_typed_local_catalog_manifest,
    validate_typed_local_catalog_manifest,
)


def payload(version):
    return json.loads(
        (ROOT / f"docs/calculus-v{version}-supplement-batch.json").read_text()
    )


def card(version, suffix):
    return next(c for c in payload(version)["cards"] if c["id"].endswith("_" + suffix))


def applications(c, operator):
    return [
        n
        for n in ET.fromstring(c["openmath_xml"]).iter()
        if n.tag.endswith("}OMA") and n[0].attrib.get("name") == operator
    ]


def decode(node, names):
    tag = node.tag.rsplit("}", 1)[-1]
    if tag == "OMV":
        return names[node.attrib["name"]]
    if tag == "OMI":
        return int(node.text)
    if tag == "OMA":
        return (node[0].attrib["name"], *(decode(c, names) for c in node[1:]))
    raise AssertionError(tag)


def outer_names(c, roles):
    binder = ET.fromstring(c["openmath_xml"])[0]
    return dict(
        zip([e[-1].attrib["name"] for e in binder[1]], roles.split(), strict=True)
    )


@pytest.mark.parametrize("version,count", [(5, 15), (3, 9)])
def test_distinct_source_bound_supplement_and_original_share_profile(version, count):
    p = payload(version)
    supplement = load_typed_local_catalog_manifest(
        ROOT / f"docs/calculus-v{version}-supplement-batch.json", repository_root=ROOT
    )
    original = load_typed_local_catalog_manifest(
        ROOT / f"docs/calculus-v{version}-batch.json", repository_root=ROOT
    )
    assert len(supplement.cards) == count
    assert supplement.profile == original.profile
    assert supplement.authoring_status == "local_authoring_evidence_bound_not_admitted"
    old = json.loads((ROOT / f"docs/calculus-v{version}-batch.json").read_text())
    assert not ({c["id"] for c in p["cards"]} & {c["id"] for c in old["cards"]})
    assert not (
        {c["openmath_xml"] for c in p["cards"]}
        & {c["openmath_xml"] for c in old["cards"]}
    )
    assert not (
        {c["lean_target"] for c in p["cards"]}
        & {c["lean_target"] for c in old["cards"]}
    )
    source = ROOT / p["evidence"]["witness_path"]
    assert source.read_text() == witness_source(p["cards"])
    assert (
        "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest()
        == p["evidence"]["witness_sha256"]
    )
    assert p["evidence"]["validator_sha256"] == old["evidence"]["validator_sha256"]
    assert p["evidence"]["registry_sha256"] == old["evidence"]["registry_sha256"]
    assert all(4 <= len(c["sketch_steps"]) <= 10 for c in p["cards"])
    ns = runpy.run_path(
        str(ROOT / f"pals-scripts/generate-calculus-v{version}-supplement-batch.py")
    )
    assert ns["cards"] == p["cards"]


@pytest.mark.parametrize("version", [3, 5])
def test_negative_pairing_covers_each_new_card_once(version):
    p = payload(version)
    ns = json.loads(
        (ROOT / f"docs/calculus-v{version}-supplement-negatives.json").read_text()
    )["cases"]
    assert {n["positive_card_id"] for n in ns} == {c["id"] for c in p["cards"]}
    assert len(ns) == len(p["cards"])
    assert len({n["candidate_question"] for n in ns}) == len(ns)
    assert all(len(n["why_invalid"]) > 40 for n in ns)


def test_difference_quotient_derivative_order_is_point_then_slope():
    c = card(5, "difference_quotient_extension")
    names = outer_names(c, "f a u")
    d = applications(c, "has_deriv_at")[0]
    assert tuple(decode(a, names) for a in d[1:]) == ("f", "a", "u")
    update = applications(c, "update_value")[0]
    assert decode(update[2], names) == ("of_int", 0)
    assert decode(update[3], names) == "u"
    assert "HasDerivAt f u a" in c["lean_target"]


def test_taylor_bound_is_n_factorial_not_successor_factorial():
    c = card(3, "taylor_uniform_remainder_bound")
    names = outer_names(c, "f n a b c x")
    fact = applications(c, "nat_factorial")
    assert len(fact) == 1 and decode(fact[0][1], names) == "n"
    powers = applications(c, "power")
    assert any(decode(n[-1], names) == ("nat_succ", "n") for n in powers)
    assert "/(n.factorial : ℝ)" in c["lean_target"]


def test_power_series_boundary_hypothesis_is_ordered_convergence_not_has_sum():
    c = card(3, "power_series_interior_convergence")
    assert len(applications(c, "sequence_limit")) == 1
    assert not applications(c, "has_sum")
    assert len(applications(c, "summable")) == 1
    names = outer_names(c, "u a b c")
    strict = applications(c, "lt")[0]
    assert tuple(decode(n, names) for n in strict[1:]) == (("abs", "b"), ("abs", "a"))
    assert "Filter.Tendsto" in c["lean_target"] and "Summable" in c["lean_target"]


def test_geometric_error_contains_summability_and_correct_tail_factor():
    c = card(3, "geometric_majorant_error")
    assert len(applications(c, "summable")) == 1
    names = outer_names(c, "u c q")
    quotient = applications(c, "divide")[0]
    assert decode(quotient[-1], names) == ("minus", ("of_int", 1), "q")
    assert "Summable u ∧ ∀ n" in c["lean_target"]


@pytest.mark.parametrize("version", [3, 5])
def test_evidence_and_statement_mutation_fail_closed(version):
    p = payload(version)
    p["cards"][0]["lean_target"] += " "
    with pytest.raises(TypedLocalCatalogError):
        validate_typed_local_catalog_manifest(p, repository_root=ROOT)
    p = payload(version)
    p["evidence"]["registry_sha256"] = "sha256:" + "0" * 64
    with pytest.raises(TypedLocalCatalogError):
        validate_typed_local_catalog_manifest(p, repository_root=ROOT)


def test_proposed_curriculum_bindings_are_exact_new_ids_with_conservative_counts():
    bindings = json.loads(
        (ROOT / "docs/calculus-supplement-proposed-bindings.json").read_text()
    )
    newids = {c["id"] for v in [3, 5] for c in payload(v)["cards"]}
    assert {b["draft_id"] for b in bindings} == newids
    assert len(bindings) == len(newids) == 24
    advanced = {b["draft_id"] for b in bindings if b["difficulty"] == "advanced"}
    assert advanced == {
        "calculus_supp_v5_strong_derivative_growth_minimum",
        "calculus_supp_v3_geometric_majorant_error",
        "calculus_supp_v3_power_series_interior_convergence",
        "calculus_supp_v3_geometric_sum_derivative",
    }
