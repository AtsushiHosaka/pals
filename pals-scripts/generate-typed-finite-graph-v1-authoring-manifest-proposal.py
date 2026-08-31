"""Build the sealed local authoring manifest for typed finite graphs.

The seal binds cards validated by the isolated graph profile.  It is local
authoring evidence only: it is not a generic-DB, seed, embedding, or PFI
publication receipt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AGENT_ROOT = ROOT / "pals-agent"
if str(AGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(AGENT_ROOT))

import rfc8785
from pals_agent.typed_finite_graph import (  # type: ignore[import-untyped]
    canonicalize_typed_finite_graph_openmath_xml,
    validate_canonical_typed_finite_graph_openmath_xml,
)

OPENMATH = "http://www.openmath.org/OpenMath"
STANDARD_CDBASE = "http://www.openmath.org/cd"
TYPED_CDBASE = "urn:pals:openmath:typed-finite-graph:v1"
DESIGN_PATH = ROOT / "docs/typed-finite-graph-profile-v1-design.md"
WITNESS_PATH = ROOT / "docs/typed-finite-graph-v1-authoring-witnesses.proposal.lean"
REGISTRY_PATH = (
    AGENT_ROOT
    / "pals_agent"
    / "content_dictionaries"
    / "typed-finite-graph-v1-registry.json"
)
MANIFEST_DIGEST_INPUT = (
    "RFC 8785 canonical JSON serialization of this object with manifest_digest omitted"
)


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def tag(name: str, *children: str, **attributes: str) -> str:
    attrs = "".join(f' {key}="{value}"' for key, value in attributes.items())
    return f"<{name}{attrs}>{''.join(children)}</{name}>"


def oms(cd: str, name: str, *, cdbase: str) -> str:
    return f'<OMS cdbase="{cdbase}" cd="{cd}" name="{name}"/>'


def graph(name: str) -> str:
    return oms("pals_typed_graph", name, cdbase=TYPED_CDBASE)


def standard(cd: str, name: str) -> str:
    return oms(cd, name, cdbase=STANDARD_CDBASE)


def omv(name: str) -> str:
    return f'<OMV name="{name}"/>'


def omi(value: int) -> str:
    if value < 0:
        raise ValueError("typed-finite-graph-v1 Nat literals must be nonnegative")
    return f"<OMI>{value}</OMI>"


def app(operator: str, *arguments: str) -> str:
    return tag("OMA", operator, *arguments)


def graph_app(name: str, *arguments: str) -> str:
    return app(graph(name), *arguments)


def relation_eq(left: str, right: str) -> str:
    return app(standard("relation1", "eq"), left, right)


def logical(name: str, *arguments: str) -> str:
    return app(standard("logic1", name), *arguments)


def type_annotation(name: str, sort_expression: str) -> str:
    return tag("OMATTR", tag("OMATP", graph("type"), sort_expression), omv(name))


def typed_forall(name: str, sort_expression: str, body: str) -> str:
    return tag(
        "OMBIND",
        graph("forall"),
        tag("OMBVAR", type_annotation(name, sort_expression)),
        body,
    )


def fin_simple_graph_sort() -> str:
    return graph("FinSimpleGraph")


def trail_sort(graph_value: str) -> str:
    return graph_app("Trail", graph_value)


def openmath(proposition: str) -> str:
    return f'<OMOBJ xmlns="{OPENMATH}" version="2.0">{proposition}</OMOBJ>'


def handshaking_xml() -> str:
    g = omv("G")
    return openmath(
        typed_forall(
            "G",
            fin_simple_graph_sort(),
            relation_eq(
                graph_app("degree_sum", g),
                graph_app("nat_mul", omi(2), graph_app("edge_count", g)),
            ),
        )
    )


def tree_edge_count_xml() -> str:
    g = omv("G")
    return openmath(
        typed_forall(
            "G",
            fin_simple_graph_sort(),
            logical(
                "implies",
                graph_app("tree", g),
                relation_eq(
                    graph_app("nat_add", graph_app("edge_count", g), omi(1)),
                    graph_app("vertex_count", g),
                ),
            ),
        )
    )


def tree_connected_xml() -> str:
    g = omv("G")
    return openmath(
        typed_forall(
            "G",
            fin_simple_graph_sort(),
            logical("implies", graph_app("tree", g), graph_app("connected", g)),
        )
    )


def tree_bipartite_xml() -> str:
    g = omv("G")
    return openmath(
        typed_forall(
            "G",
            fin_simple_graph_sort(),
            logical("implies", graph_app("tree", g), graph_app("bipartite", g)),
        )
    )


def euler_trail_odd_degree_xml() -> str:
    g = omv("G")
    odd_count = graph_app("odd_degree_count", g)
    proposition = logical(
        "implies",
        graph_app("is_euler_trail", g, omv("t")),
        logical("or", relation_eq(odd_count, omi(0)), relation_eq(odd_count, omi(2))),
    )
    return openmath(
        typed_forall(
            "G",
            fin_simple_graph_sort(),
            typed_forall("t", trail_sort(g), proposition),
        )
    )


HANDSHAKING_TARGET = """∀ {V : Type*} [Fintype V] (G : SimpleGraph V) [DecidableRel G.Adj],
    (∑ v, G.degree v) = 2 * G.edgeFinset.card"""
TREE_EDGE_COUNT_TARGET = """∀ {V : Type*} [Fintype V] [DecidableEq V] (G : SimpleGraph V) [DecidableRel G.Adj],
    G.IsTree → G.edgeFinset.card + 1 = Fintype.card V"""
TREE_CONNECTED_TARGET = "∀ {V : Type*} (G : SimpleGraph V), G.IsTree → G.Connected"
TREE_BIPARTITE_TARGET = "∀ {V : Type*} (G : SimpleGraph V), G.IsTree → G.IsBipartite"
EULER_ODD_DEGREE_TARGET = """∀ {V : Type*} [Fintype V] [DecidableEq V] (G : SimpleGraph V) [DecidableRel G.Adj]
    {u v : V} (p : G.Walk u v), p.IsEulerian →
      Fintype.card {w | Odd (G.degree w)} = 0 ∨ Fintype.card {w | Odd (G.degree w)} = 2"""


HANDSHAKING_WITNESS = f"""example : {HANDSHAKING_TARGET} := by
  intro V _ G _
  exact G.sum_degrees_eq_twice_card_edges
"""
TREE_EDGE_COUNT_WITNESS = f"""example : {TREE_EDGE_COUNT_TARGET} := by
  intro V _ _ G _ hG
  exact hG.card_edgeFinset
"""
TREE_CONNECTED_WITNESS = f"""example : {TREE_CONNECTED_TARGET} := by
  intro V G hG
  exact hG.connected
"""
TREE_BIPARTITE_WITNESS = f"""example : {TREE_BIPARTITE_TARGET} := by
  intro V G hG
  exact hG.isBipartite
"""
EULER_ODD_DEGREE_WITNESS = f"""example : {EULER_ODD_DEGREE_TARGET} := by
  intro V _ _ G _ u v p hp
  exact hp.card_odd_degree
"""


WITNESS_CARDS = (
    ("typed_finite_graph_v1_handshaking", HANDSHAKING_WITNESS),
    ("typed_finite_graph_v1_tree_edge_count", TREE_EDGE_COUNT_WITNESS),
    ("typed_finite_graph_v1_tree_connected", TREE_CONNECTED_WITNESS),
    ("typed_finite_graph_v1_tree_bipartite", TREE_BIPARTITE_WITNESS),
    (
        "typed_finite_graph_v1_euler_trail_odd_degree_necessity",
        EULER_ODD_DEGREE_WITNESS,
    ),
)
WITNESS_TEXT = (
    "import Mathlib\n\nopen scoped BigOperators\n\n"
    + "\n\n".join(
        f"-- manifest card: {identifier}\n{witness.rstrip()}"
        for identifier, witness in WITNESS_CARDS
    )
    + "\n"
)


def profile_c14n(raw_xml: str) -> str:
    canonical = canonicalize_typed_finite_graph_openmath_xml(raw_xml)
    validate_canonical_typed_finite_graph_openmath_xml(canonical)
    return canonical


def assert_exact_cdbases(raw_xml: str) -> None:
    root = ET.fromstring(raw_xml)
    oms_tag = f"{{{OPENMATH}}}OMS"
    seen = 0
    for element in root.iter(oms_tag):
        seen += 1
        cd = element.attrib["cd"]
        expected = TYPED_CDBASE if cd == "pals_typed_graph" else STANDARD_CDBASE
        if cd not in {"pals_typed_graph", "logic1", "relation1"}:
            raise ValueError(f"unsupported graph profile CD: {cd}")
        if element.attrib.get("cdbase") != expected:
            raise ValueError(
                f"{cd}:{element.attrib.get('name')} lacks its exact direct cdbase"
            )
    if seen == 0:
        raise ValueError("OpenMath candidate has no symbols")


def card(
    *,
    identifier: str,
    difficulty: str,
    statement: str,
    xml: str,
    signature_trace: list[str],
    proof_strategy: str,
    steps: list[str],
    lean_target: str,
    lean_witness: str,
    statement_to_openmath: str,
    openmath_to_lean: str,
) -> dict[str, Any]:
    if not 4 <= len(steps) <= 8:
        raise ValueError(f"{identifier} has {len(steps)} sketch steps; expected 4..8")
    assert_exact_cdbases(xml)
    canonical = profile_c14n(xml)
    if lean_target not in lean_witness or lean_witness not in WITNESS_TEXT:
        raise ValueError(
            f"Lean witness for {identifier} is not bound to the exact witness file"
        )
    return {
        "id": identifier,
        "domain": "discrete_mathematics_finite_graphs",
        "difficulty": difficulty,
        "authoring_status": "sealed_local_profile_validated_not_admitted",
        "canonical_statement": statement,
        "canonical_statement_sha256": sha256_text(statement),
        "openmath_xml": xml,
        "openmath_xml_sha256": sha256_text(xml),
        "canonical_openmath_xml": canonical,
        "canonical_openmath_xml_sha256": sha256_text(canonical),
        "profile_c14n": {
            "algorithm": "openmath-cdbase-alpha-c14n-v4",
            "scope": "typed-finite-graph-v1 validation followed by profile-separated canonicalization",
            "xml": canonical,
            "sha256": sha256_text(canonical),
        },
        "signature_trace": signature_trace,
        "signature_trace_sha256": sha256_bytes(rfc8785.dumps(signature_trace)),
        "proof_strategy": proof_strategy,
        "proof_strategy_sha256": sha256_text(proof_strategy),
        "sketch_steps": steps,
        "sketch_steps_sha256": sha256_bytes(rfc8785.dumps(steps)),
        "lean": {
            "target": lean_target,
            "target_sha256": sha256_text(lean_target),
            "witness": lean_witness,
            "witness_sha256": sha256_text(lean_witness),
        },
        "statement_openmath_lean_alignment_review": {
            "status": "sealed_local_authoring_review_not_admitted",
            "statement_to_openmath": statement_to_openmath,
            "openmath_to_lean": openmath_to_lean,
            "admission_gate": "Obtain independent project review before any catalog or DB admission.",
        },
    }


def profile_signature_contract() -> dict[str, Any]:
    return {
        "source": "docs/typed-finite-graph-profile-v1-design.md#exact-typed-signature",
        "status": "implemented_isolated_profile_not_admitted",
        "sorts": {
            "FinSimpleGraph": "finite, undirected, loopless, simple graph value",
            "Vertex(G)": "vertex carrier indexed by the exact graph binder G",
            "VertexClass(G)": "opaque vertex subset indexed by G",
            "Trail(G)": "opaque finite trail witness indexed by G",
            "Nat": "nonnegative OMI only",
        },
        "symbols_used_by_admitted_candidates": {
            "pals_typed_graph:forall": "typed binder; every OMBVAR has exactly one type annotation",
            "pals_typed_graph:type": "OMATTR key permitted only in OMBVAR declarations",
            "pals_typed_graph:FinSimpleGraph": "sort constant",
            "pals_typed_graph:Trail": "(G : FinSimpleGraph) -> Sort",
            "pals_typed_graph:degree_sum": "FinSimpleGraph -> Nat",
            "pals_typed_graph:edge_count": "FinSimpleGraph -> Nat",
            "pals_typed_graph:vertex_count": "FinSimpleGraph -> Nat",
            "pals_typed_graph:odd_degree_count": "FinSimpleGraph -> Nat",
            "pals_typed_graph:nat_add": "Nat x Nat -> Nat",
            "pals_typed_graph:nat_mul": "Nat x Nat -> Nat",
            "pals_typed_graph:tree": "FinSimpleGraph -> Prop",
            "pals_typed_graph:connected": "FinSimpleGraph -> Prop",
            "pals_typed_graph:bipartite": "FinSimpleGraph -> Prop",
            "pals_typed_graph:is_euler_trail": "(G, Trail(G)) -> Prop",
            "logic1:implies": "Prop x Prop -> Prop",
            "logic1:or": "Prop x Prop -> Prop",
            "relation1:eq": "equal inferred sorts -> Prop",
        },
        "intentional_absences": [
            "No public graph1/graph2/graph3 constructor or inherited cdbase is accepted.",
            "No Euler existence converse is admitted without a pinned constructive bridge witness.",
            "No proper_bipartition iff bipartite card is admitted until the full-vertex-coverage bridge is proved.",
        ],
    }


def build_manifest() -> dict[str, Any]:
    contract = profile_signature_contract()
    cards = [
        card(
            identifier="typed_finite_graph_v1_handshaking",
            difficulty="standard",
            statement="For every finite simple undirected graph G, the sum of all vertex degrees equals twice the number of edges of G.",
            xml=handshaking_xml(),
            signature_trace=[
                "pals_typed_graph:forall",
                "pals_typed_graph:FinSimpleGraph",
                "pals_typed_graph:degree_sum",
                "pals_typed_graph:nat_mul",
                "pals_typed_graph:edge_count",
                "relation1:eq",
            ],
            proof_strategy="Count incident edge-ends: every edge contributes exactly two ends in a loopless undirected simple graph.",
            steps=[
                "setup: Fix a finite simple undirected graph G.",
                "incidence: Count all incidences by summing degree(G,v) over vertices.",
                "edge-view: Each edge supplies exactly two incidences because G is loopless and undirected.",
                "equate: The two finite counts are equal.",
                "conclude: degree_sum(G) = nat_mul(2, edge_count(G)).",
            ],
            lean_target=HANDSHAKING_TARGET,
            lean_witness=HANDSHAKING_WITNESS,
            statement_to_openmath="exact: degree_sum, edge_count, natural multiplication, and the single graph binder G are all explicit; no graph representation is inferred from generic graph1 syntax.",
            openmath_to_lean="exact under the declared bridge: FinSimpleGraph lowers to SimpleGraph V with finite vertex and decidable adjacency instances; degree_sum and edge_count lower to `∑ v, G.degree v` and `G.edgeFinset.card`.",
        ),
        card(
            identifier="typed_finite_graph_v1_tree_edge_count",
            difficulty="standard",
            statement="For every finite simple undirected graph G, if G is a tree, then its number of edges plus one equals its number of vertices.",
            xml=tree_edge_count_xml(),
            signature_trace=[
                "pals_typed_graph:forall",
                "pals_typed_graph:FinSimpleGraph",
                "pals_typed_graph:tree",
                "pals_typed_graph:edge_count",
                "pals_typed_graph:nat_add",
                "pals_typed_graph:vertex_count",
                "logic1:implies",
                "relation1:eq",
            ],
            proof_strategy="Use the finite-tree cardinality theorem after fixing the profile convention that tree means connected and acyclic.",
            steps=[
                "setup: Fix G and assume tree(G).",
                "model: Unpack tree as connected and acyclic in the finite simple graph model.",
                "finite-count: Apply the finite-tree edge-cardinality theorem.",
                "normalize: Identify edge_count(G) and vertex_count(G) with the two finite cardinalities.",
                "conclude: nat_add(edge_count(G),1) = vertex_count(G).",
            ],
            lean_target=TREE_EDGE_COUNT_TARGET,
            lean_witness=TREE_EDGE_COUNT_WITNESS,
            statement_to_openmath="exact: the antecedent is tree(G), and both sides remain Nat terms; the formula does not encode tree by a hidden cardinality convention.",
            openmath_to_lean="exact under the bridge: `tree(G)` lowers to `G.IsTree`, `edge_count` to `G.edgeFinset.card`, and `vertex_count` to `Fintype.card V`; the witness is `SimpleGraph.IsTree.card_edgeFinset`.",
        ),
        card(
            identifier="typed_finite_graph_v1_tree_connected",
            difficulty="introductory",
            statement="For every finite simple undirected graph G, if G is a tree, then G is connected.",
            xml=tree_connected_xml(),
            signature_trace=[
                "pals_typed_graph:forall",
                "pals_typed_graph:FinSimpleGraph",
                "pals_typed_graph:tree",
                "pals_typed_graph:connected",
                "logic1:implies",
            ],
            proof_strategy="Unfold the profile definition of tree, whose first component is connectedness.",
            steps=[
                "setup: Fix G and assume tree(G).",
                "definition: A profile tree is connected and acyclic.",
                "project: Take the connected component of the tree witness.",
                "conclude: connected(G).",
            ],
            lean_target=TREE_CONNECTED_TARGET,
            lean_witness=TREE_CONNECTED_WITNESS,
            statement_to_openmath="exact: the XML uses the profile predicates tree and connected on the same graph binder G.",
            openmath_to_lean="exact under the bridge: `tree(G)` and `connected(G)` lower to `G.IsTree` and `G.Connected`, and the Lean witness projects `IsTree.connected`.",
        ),
        card(
            identifier="typed_finite_graph_v1_tree_bipartite",
            difficulty="standard",
            statement="For every finite simple undirected graph G, if G is a tree, then G is bipartite.",
            xml=tree_bipartite_xml(),
            signature_trace=[
                "pals_typed_graph:forall",
                "pals_typed_graph:FinSimpleGraph",
                "pals_typed_graph:tree",
                "pals_typed_graph:bipartite",
                "logic1:implies",
            ],
            proof_strategy="Two-color vertices by parity of distance from a fixed root; acyclicity ensures adjacent vertices receive opposite colors.",
            steps=[
                "setup: Fix G and assume tree(G).",
                "root: Choose a root using connectedness.",
                "color: Color each vertex by the parity of its graph distance from the root.",
                "separate: Adjacent vertices have distances differing by one in a tree.",
                "conclude: The parity coloring witnesses bipartite(G).",
            ],
            lean_target=TREE_BIPARTITE_TARGET,
            lean_witness=TREE_BIPARTITE_WITNESS,
            statement_to_openmath="exact: this is only the one-way tree-to-bipartite theorem; it does not assert an unsupported full-coverage bipartition equivalence.",
            openmath_to_lean="exact under the bridge: `tree(G)` and `bipartite(G)` lower to `G.IsTree` and `G.IsBipartite`; mathlib's `IsTree.isBipartite` supplies the witness.",
        ),
        card(
            identifier="typed_finite_graph_v1_euler_trail_odd_degree_necessity",
            difficulty="advanced",
            statement="For every finite simple undirected graph G and trail t in G, if t uses every edge of G exactly once, then G has either zero or two odd-degree vertices.",
            xml=euler_trail_odd_degree_xml(),
            signature_trace=[
                "pals_typed_graph:forall",
                "pals_typed_graph:FinSimpleGraph",
                "pals_typed_graph:Trail",
                "pals_typed_graph:is_euler_trail",
                "pals_typed_graph:odd_degree_count",
                "logic1:implies",
                "logic1:or",
                "relation1:eq",
            ],
            proof_strategy="Pair entrance and exit incidences along an Euler trail; only its endpoints can contribute unpaired incidences.",
            steps=[
                "setup: Fix G and a trail t with is_euler_trail(G,t).",
                "coverage: Every edge occurs exactly once in t.",
                "internal-pairing: Each internal visit pairs one entering and one leaving incidence.",
                "endpoints: Only the two trail endpoints may have unpaired incidences.",
                "parity: Therefore all degrees are even except possibly two endpoint degrees.",
                "conclude: odd_degree_count(G) is 0 or 2.",
            ],
            lean_target=EULER_ODD_DEGREE_TARGET,
            lean_witness=EULER_ODD_DEGREE_WITNESS,
            statement_to_openmath="exact under the profile's opaque Trail(G) contract: the XML quantifies one trail of the same graph G and asserts only the necessary odd-degree conclusion, not Euler-trail existence.",
            openmath_to_lean="exact under the declared trail bridge: Trail(G) lowers to an endpoint-indexed `SimpleGraph.Walk G u v`, `is_euler_trail` lowers to `Walk.IsEulerian`, and `odd_degree_count` lowers to the cardinality of odd-degree vertices.",
        ),
    ]
    excluded = [
        {
            "id": "typed_finite_graph_v1_euler_trail_existence_converse",
            "canonical_statement": "A finite graph has an Euler trail if and only if its non-isolated vertices are connected and it has zero or two odd-degree vertices.",
            "status": "excluded_no_constructive_existence_bridge",
            "reason": "The pinned Trails module supplies the necessary `Walk.IsEulerian.card_odd_degree` theorem but leaves the relevant existence direction as TODO. The design therefore marks GRAF-006 blocked; no proof receipt or XML card may claim the converse.",
            "required_evidence": "Compile a constructive existence theorem against the exact nonisolated_connected convention, including the zero-edge case, then add an independently reviewed Trail(G) lowering receipt.",
        },
        {
            "id": "typed_finite_graph_v1_bipartite_full_partition_iff",
            "canonical_statement": "A finite graph is bipartite if and only if it has a proper bipartition L,R covering every vertex.",
            "status": "excluded_coverage_bridge_not_exact",
            "reason": "`SimpleGraph.isBipartite_iff_exists_isBipartiteWith` is close, but its sets need not cover isolated vertices. The profile predicate proper_bipartition requires total coverage, so this is not a three-way exact statement yet.",
            "required_evidence": "Prove and compile a bridge that extends a mathlib bipartition over isolated vertices while preserving the exact VertexClass(G) semantics, then obtain independent review.",
        },
    ]
    identifiers = [entry["id"] for entry in cards]
    statements = [entry["canonical_statement"] for entry in cards]
    xmls = [entry["canonical_openmath_xml"] for entry in cards]
    if len(cards) != 5 or len(excluded) != 2:
        raise ValueError("expected exactly five safe cards and two blocked exclusions")
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("candidate IDs must be unique")
    if len(statements) != len(set(statements)):
        raise ValueError("candidate statements must be unique")
    if len(xmls) != len(set(xmls)):
        raise ValueError("canonical OpenMath statements must be unique")
    return {
        "schema_version": "pals.typed-finite-graph-v1-sealed-manifest.v1",
        "status": "sealed_local_authoring_revision_not_admitted",
        "seal": {
            "scope": "local typed-finite-graph authoring evidence only",
            "admission": "not admitted to the generic DB, seed, embedding index, or PFI package",
            "revision": "typed-finite-graph-v1-local-r1",
        },
        "immutability_contract": {
            "digest_algorithm": "sha256 over exact UTF-8 bytes of the named field or artifact",
            "canonical_json": MANIFEST_DIGEST_INPUT,
            "profile_c14n": "Every card is validated by typed-finite-graph-v1 before exact canonical bytes are sealed.",
            "mutation_rule": "Changing a statement, strategy, sketch, XML, signature trace, Lean target/witness, design, or registry requires a new sealed revision and manifest digest.",
        },
        "profile": {
            "id": "typed-finite-graph-v1",
            "typed_cdbase": TYPED_CDBASE,
            "validator": "pals_agent.typed_finite_graph.validate_canonical_typed_finite_graph_openmath_xml",
            "validator_status": "implemented_isolated_profile",
            "registry_status": "implemented_isolated_profile",
            "canonicalization_scope": "typed-finite-graph-v1 validation followed by profile-separated XML C14N",
            "content_dictionary_bundle": {
                "relative_path": "pals-agent/pals_agent/content_dictionaries/typed-finite-graph-v1-registry.json",
                "sha256": sha256_bytes(REGISTRY_PATH.read_bytes()),
                "digest_input": "exact UTF-8 bytes of the named registry/CD bundle",
            },
            "profile_design": {
                "path": "docs/typed-finite-graph-profile-v1-design.md",
                "sha256": sha256_bytes(DESIGN_PATH.read_bytes()),
            },
            "signature_contract": contract,
            "signature_contract_sha256": "sha256:"
            + hashlib.sha256(rfc8785.dumps(contract)).hexdigest(),
            "lean_bridge": {
                "FinSimpleGraph": "a Lean `SimpleGraph V` with finite vertex carrier and required decidability instances",
                "Vertex(G)": "the same Lean carrier `V` associated with G",
                "Trail(G)": "an endpoint-indexed `SimpleGraph.Walk G u v`, packaged behind the profile's opaque trail sort",
                "is_euler_trail(G,t)": "`SimpleGraph.Walk.IsEulerian` after unpacking the endpoint-indexed trail",
            },
        },
        "lean_witness_bundle": {
            "path": "docs/typed-finite-graph-v1-authoring-witnesses.proposal.lean",
            "sha256": sha256_text(WITNESS_TEXT),
            "digest_input": "exact UTF-8 bytes of the named Lean file, including import and final newline",
            "verification_command": "cd pals-agent/lean-workspace && lake env lean ../../docs/typed-finite-graph-v1-authoring-witnesses.proposal.lean",
            "verification_status": "compiled when generator is run with --verify-lean; sealed evidence only, not an OpenMath-to-Lean translation receipt",
            "scope": "the five profile-faithful candidates only; blocked theorem families are recorded as exclusions",
        },
        "admitted_candidate_cards": cards,
        "excluded_witnesses": excluded,
        "manifest_digest": {},
    }


def seal(manifest: dict[str, Any]) -> dict[str, Any]:
    unsigned = dict(manifest)
    unsigned.pop("manifest_digest", None)
    manifest["manifest_digest"] = {
        "algorithm": "sha256",
        "input": MANIFEST_DIGEST_INPUT,
        "sha256": "sha256:" + hashlib.sha256(rfc8785.dumps(unsigned)).hexdigest(),
    }
    return manifest


def verify_lean() -> None:
    completed = subprocess.run(
        ["lake", "env", "lean", str(WITNESS_PATH)],
        cwd=AGENT_ROOT / "lean-workspace",
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(
            f"Lean compilation failed:\n{completed.stdout}{completed.stderr}"
        )


def write_if_changed(path: Path, text: str) -> None:
    if not path.exists() or path.read_text(encoding="utf-8") != text:
        path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs/typed-finite-graph-v1-authoring-manifest.proposal.json",
    )
    parser.add_argument("--lean-output", type=Path, default=WITNESS_PATH)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--verify-lean", action="store_true")
    args = parser.parse_args()

    manifest = seal(build_manifest())
    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    if not WITNESS_TEXT.endswith("\n"):
        raise AssertionError("Lean witness bundle must end in a newline")
    if args.check:
        if args.output.read_text(encoding="utf-8") != manifest_text:
            raise SystemExit(
                "finite-graph authoring manifest is stale; rerun this generator"
            )
        if args.lean_output.read_text(encoding="utf-8") != WITNESS_TEXT:
            raise SystemExit(
                "finite-graph Lean witness bundle is stale; rerun this generator"
            )
        if args.verify_lean:
            verify_lean()
        print("finite-graph authoring manifest and Lean bundle are current")
        return
    write_if_changed(args.output, manifest_text)
    write_if_changed(args.lean_output, WITNESS_TEXT)
    if args.verify_lean:
        verify_lean()
    print("sealed_cards=5 excluded_witnesses=2 profile_c14n=validated")
    if args.verify_lean:
        print("lean=passed")


if __name__ == "__main__":
    main()
