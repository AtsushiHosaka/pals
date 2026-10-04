"""Compile general real inner-product-space Draft witnesses before emitting evidence."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from xml.sax.saxutils import quoteattr

from pals_agent.typed_linear_algebra_v3 import (
    canonicalize_typed_linear_algebra_v3_openmath_xml as canonicalize,
)
from pals_agent.typed_linear_algebra_v3 import (
    validate_canonical_typed_linear_algebra_v3_openmath_xml as validate,
)

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "pals-agent/lean-workspace"
TYPED = "urn:pals:openmath:typed-linear-algebra:v3"
PROFILE = "typed-linear-algebra-v3"


def sym(cd, name, base=TYPED):
    return f"<OMS cdbase={quoteattr(base)} cd={quoteattr(cd)} name={quoteattr(name)}/>"


def var(n):
    return f"<OMV name={quoteattr(n)}/>"


def app(h, *a):
    return "<OMA>" + h + "".join(a) + "</OMA>"


def op(n, *a):
    return app(sym("la3", n), *a)


def std(cd, n, *a):
    return app(sym(cd, n, "http://www.openmath.org/cd"), *a)


def eq(a, b):
    return std("relation1", "eq", a, b)


def le(a, b):
    return std("relation1", "leq", a, b)


def plus(a, b):
    return std("arith1", "plus", a, b)


def conj(a, b):
    return std("logic1", "and", a, b)


def disj(a, b):
    return std("logic1", "or", a, b)


def imp(a, b):
    return std("logic1", "implies", a, b)


def iff(a, b):
    return conj(imp(a, b), imp(b, a))


def typ(n, *a):
    return op(n, *a) if a else sym("la3", n)


def quant(ds, body, kind="forall"):
    decls = "".join(
        "<OMATTR><OMATP>"
        + sym("typed1", "type")
        + t
        + "</OMATP>"
        + var(n)
        + "</OMATTR>"
        for n, t in ds
    )
    return (
        "<OMBIND>"
        + sym("typed1", kind)
        + "<OMBVAR>"
        + decls
        + "</OMBVAR>"
        + body
        + "</OMBIND>"
    )


V, x, y, S, T, n, v, b, c, f, a = map(
    var, ("V", "x", "y", "S", "T", "n", "v", "b", "c", "f", "a")
)


def nat(i):
    return f"<OMI>{i}</OMI>"


def real(i):
    return op("real_nat", nat(i))


def norm(x):
    return op("norm", V, x)


def sq(x):
    return op("real_square", x)


def inner(x, y):
    return op("inner", V, x, y)


def va(x, y):
    return op("vector_add", V, x, y)


def vs(x, y):
    return op("vector_sub", V, x, y)


def orth(S):
    return op("orthogonal", V, S)


def proj(S, x):
    return op("projection", V, S, x)


def mem(x, S):
    return op("member", V, x, S)


def fam(name, v):
    return op(name, V, n, v)


def coeff(v, x):
    return op("coefficients", V, n, v, x)


def bv(b):
    return op("onbasis_vectors", V, n, b)


def span(v):
    return fam("family_span", v)


def coord(b, x):
    return op("coordinates", V, n, b, x)


SPACE = [("V", typ("RealInnerProductSpace"))]
XY = [("x", typ("Vector", V)), ("y", typ("Vector", V))]
SUB = [("S", typ("Subspace", V))]
SUBS = SUB + [("T", typ("Subspace", V))]
NF = [("n", typ("Nat")), ("v", typ("VectorFamily", V, n))]
NB = [("n", typ("Nat")), ("b", typ("OrthonormalBasis", V, n))]
LEAN = "example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] "


def build_cards():
    zero = op("vector_zero", V)
    opposite = vs(zero, x)
    neq = lambda a, b: std("relation1", "neq", a, b)
    body = imp(neq(x, zero), neq(norm(va(x, opposite)), plus(norm(x), norm(opposite))))
    xml = canonicalize(
        '<OMOBJ xmlns="http://www.openmath.org/OpenMath" version="2.0">'
        + quant([("V", typ("RealInnerProductSpace")), ("x", typ("Vector", V))], body)
        + "</OMOBJ>"
    )
    validate(xml)
    steps = [
        "Choose an arbitrary nonzero vector x and its opposite −x.",
        "Their sum is zero, so the norm of that sum is zero.",
        "Each separate norm equals the strictly positive norm of x.",
        "The sum of the norms is therefore positive, disproving universal norm additivity in every nonzero inner-product space.",
    ]
    return [
        {
            "id": "la_v3_nonadditive_norm_family",
            "canonical_statement": "In every finite-dimensional real inner-product space, for each nonzero x the vectors x and −x satisfy ‖x+(−x)‖≠‖x‖+‖−x‖. Norms are not additive in general.",
            "proof_strategy": steps[0],
            "sketch_steps": steps,
            "openmath_xml": xml,
            "lean_target": "example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] (x : V) (hx : x ≠ 0) : ‖x+(0-x)‖ ≠ ‖x‖+‖(0-x)‖",
            "lean_witness": "by\n  simp only [zero_sub, add_neg_cancel, norm_zero, norm_neg]\n  have hp : 0 < ‖x‖ := norm_pos_iff.mpr hx\n  linarith",
        }
    ]


def sha(p):
    return "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    cards = build_cards()
    assert len(cards) == 1 and len({c["openmath_xml"] for c in cards}) == len(cards)
    assert all(4 <= len(c["sketch_steps"]) <= 10 for c in cards)
    source = (
        "import Mathlib\n\n"
        + "\n\n".join(
            "-- manifest card: "
            + c["id"]
            + "\n"
            + c["lean_target"]
            + " := "
            + c["lean_witness"].rstrip()
            for c in cards
        )
        + "\n"
    )
    witness = ROOT / "docs/linear-algebra-v3-foundation-supplement.lean"
    witness.write_text(source)
    subprocess.run(
        ["lake", "env", "lean", str(witness)], cwd=WORKSPACE, check=True, timeout=180
    )
    packages = json.loads((WORKSPACE / "lake-manifest.json").read_text())["packages"]
    payload = {
        "schema_version": "pals.typed-catalog-expansion-batch.v1",
        "profile_id": PROFILE,
        "cards": cards,
        "evidence": {
            "witness_path": str(witness.relative_to(ROOT)),
            "witness_sha256": sha(witness),
            "toolchain": (WORKSPACE / "lean-toolchain").read_text().strip(),
            "mathlib_revision": next(
                p["rev"] for p in packages if p["name"] == "mathlib"
            ),
            "validator_sha256": sha(
                ROOT / "pals-agent/pals_agent/typed_linear_algebra_v3.py"
            ),
            "registry_sha256": sha(
                ROOT
                / "pals-agent/pals_agent/content_dictionaries/typed-linear-algebra-v3-registry.json"
            ),
        },
    }
    (ROOT / "docs/linear-algebra-v3-foundation-supplement.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    )
    print(
        f"PASS: {len(cards)} general inner-product-space cards compiled and canonicalized"
    )


if __name__ == "__main__":
    main()
