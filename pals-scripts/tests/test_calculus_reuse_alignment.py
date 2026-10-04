"""Semantic regression for HasDerivAt's two same-sort Real arguments.

The sealed profile signature is has_deriv_at(f, point, derivative_value),
explicitly lowered to Lean HasDerivAt f derivative_value point by the original
generator alignment contract. Type validation alone cannot catch exchanging
the last two arguments because both are Real.
Expected roles below are independently stated mathematical formulas, not calls
to the authoring generator or its XML construction helpers.
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BATCH = ROOT / "docs/calculus-reuse-batch-20260930.json"

# Top-level variable names in each mathematical statement and every derivative
# occurrence in preorder (assumptions first, conclusion last).
CASES = [
    (
        "derivative_sum",
        "f g a u v",
        [
            ("f", "u", "a"),
            ("g", "v", "a"),
            ("lambda(x,plus(apply(f,x),apply(g,x)))", "plus(u,v)", "a"),
        ],
    ),
    (
        "derivative_difference",
        "f g a u v",
        [
            ("f", "u", "a"),
            ("g", "v", "a"),
            ("lambda(x,minus(apply(f,x),apply(g,x)))", "minus(u,v)", "a"),
        ],
    ),
    (
        "derivative_product",
        "f g a u v",
        [
            ("f", "u", "a"),
            ("g", "v", "a"),
            (
                "lambda(x,times(apply(f,x),apply(g,x)))",
                "plus(times(u,apply(g,a)),times(apply(f,a),v))",
                "a",
            ),
        ],
    ),
    (
        "derivative_quotient",
        "f g a u v",
        [
            ("f", "u", "a"),
            ("g", "v", "a"),
            (
                "lambda(x,divide(apply(f,x),apply(g,x)))",
                "divide(minus(times(u,apply(g,a)),times(apply(f,a),v)),power(apply(g,a),2))",
                "a",
            ),
        ],
    ),
    (
        "derivative_chain",
        "f g a u v",
        [
            ("f", "u", "apply(g,a)"),
            ("g", "v", "a"),
            ("lambda(x,apply(f,apply(g,x)))", "times(u,v)", "a"),
        ],
    ),
    (
        "derivative_scalar_multiple",
        "f a u c",
        [("f", "u", "a"), ("lambda(x,times(c,apply(f,x)))", "times(c,u)", "a")],
    ),
    ("derivative_unique", "f a u v", [("f", "u", "a"), ("f", "v", "a")]),
    ("derivative_implies_differentiable", "f a u", [("f", "u", "a")]),
    (
        "derivative_affine_parameters",
        "a b c",
        [("lambda(x,plus(times(b,x),c))", "b", "a")],
    ),
    (
        "derivative_reciprocal_function",
        "f a u",
        [
            ("f", "u", "a"),
            (
                "lambda(x,divide(of_int(1),apply(f,x)))",
                "divide(unary_minus(u),power(apply(f,a),2))",
                "a",
            ),
        ],
    ),
]


def local_tag(node):
    return node.tag.rsplit("}", 1)[-1]


def decode(node, names):
    tag = local_tag(node)
    if tag == "OMV":
        return names[node.attrib["name"]]
    if tag == "OMI":
        return node.text.strip()
    if tag == "OMA":
        return (
            node[0].attrib["name"]
            + "("
            + ",".join(decode(n, names) for n in node[1:])
            + ")"
        )
    if tag == "OMBIND" and node[0].attrib["name"] == "lambda":
        assert len(node[1]) == 1
        variable = node[1][0][-1].attrib["name"]
        return "lambda(x," + decode(node[2], dict(names, **{variable: "x"})) + ")"
    raise AssertionError(
        "unexpected expression: " + ET.tostring(node, encoding="unicode")
    )


@pytest.mark.parametrize("suffix,variables,expected", CASES, ids=[c[0] for c in CASES])
def test_xml_point_slope_lowers_to_lean_slope_point(suffix, variables, expected):
    cards = json.loads(BATCH.read_text())["cards"]
    card = next(c for c in cards if c["id"] == "calculus_reuse_" + suffix)
    root = ET.fromstring(card["openmath_xml"])
    binder = root[0]
    actual_variables = [entry[-1].attrib["name"] for entry in binder[1]]
    assert len(actual_variables) == len(variables.split())
    names = dict(zip(actual_variables, variables.split(), strict=True))
    actual = []
    for node in root.iter():
        if local_tag(node) == "OMA" and node[0].attrib.get("name") == "has_deriv_at":
            assert len(node) == 4
            # The profile orders point before slope; Lean orders slope before point.
            actual.append(
                (decode(node[1], names), decode(node[3], names), decode(node[2], names))
            )
    assert actual == expected


def test_runtime_guidance_preserves_sealed_openmath_argument_order():
    # Exercise the guidance actually emitted for query structuring, not a copy
    # of the generator helper. Same-sort slot drift would otherwise validate.
    import runpy

    guidance_module = runpy.run_path(
        str(ROOT / "pals-agent/pals_agent/typed_profile_guidance.py")
    )
    guidance = guidance_module["profile_guidance"]("typed-real-analysis-v1")
    assert "has_deriv_at(f,point,derivative_value)->Prop" in guidance
    assert "has_deriv_at(f,derivative_value,point)" not in guidance
    assert "Lean HasDerivAt f slope point" in guidance
