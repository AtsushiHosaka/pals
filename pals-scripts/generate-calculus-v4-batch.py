"""Compile general multivariable witnesses before publishing a local authoring manifest."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pals-agent"))
from pals_agent.typed_calculus_v4 import (
    canonicalize_typed_calculus_v4_openmath_xml as canon,
)

BASE = "urn:pals:openmath:typed-calculus:v4"
WORKSPACE = ROOT / "pals-agent/lean-workspace"


def s(n, cd="calculus4"):
    return f'<OMS cdbase="{BASE if cd in ("typed4", "calculus4") else "http://www.openmath.org/cd"}" cd="{cd}" name="{n}"/>'


def v(n):
    return f'<OMV name="{n}"/>'


def a(n, *args):
    return "<OMA>" + s(n) + "".join(args) + "</OMA>"


def std(cd, n, *args):
    return "<OMA>" + s(n, cd) + "".join(args) + "</OMA>"


def eq(x, y):
    return std("relation1", "eq", x, y)


def neq(x, y):
    return std("relation1", "neq", x, y)


def le(x, y):
    return std("relation1", "leq", x, y)


def imp(x, y):
    return std("logic1", "implies", x, y)


def both(x, y):
    return std("logic1", "and", x, y)


def binder(ds, body):
    return (
        "<OMBIND>"
        + s("forall", "typed4")
        + "<OMBVAR>"
        + "".join(
            "<OMATTR><OMATP>"
            + s("type", "typed4")
            + t
            + "</OMATP>"
            + v(n)
            + "</OMATTR>"
            for n, t in ds
        )
        + "</OMBVAR>"
        + body
        + "</OMBIND>"
    )


def typ(n, *vs):
    return a(n, *map(v, vs)) if vs else s(n)


def real(n):
    return a("real_nat", f"<OMI>{n}</OMI>")


E, F, G, f, g, A, B, x, y, z, u, w, c, t, D, H, n = map(
    v,
    [
        "E",
        "F",
        "G",
        "f",
        "g",
        "A",
        "B",
        "x",
        "y",
        "z",
        "u",
        "w",
        "c",
        "t",
        "D",
        "H",
        "n",
    ],
)


def hd(E, F, f, x, A):
    return a("has_fderiv", E, F, f, x, A)


def hs(E, f, x, A):
    return a("has_scalar_fderiv", E, f, x, A)


def hg(E, f, x, u):
    return a("has_gradient", E, f, x, u)


def val(E, F, f, x):
    return a("apply", E, F, f, x)


def sv(E, f, x):
    return a("scalar_apply", E, f, x)


def norm(E, x):
    return a("norm", E, x)


BASELINE = lambda spaces: " ".join(
    "{"
    + q
    + " : Type*} [NormedAddCommGroup "
    + q
    + "] [InnerProductSpace ℝ "
    + q
    + "] [FiniteDimensional ℝ "
    + q
    + "]"
    for q in spaces.split()
)
cards = []


def add(key, spaces, ds, statement, body, params, target, proof, steps):
    raw = (
        '<OMOBJ xmlns="http://www.openmath.org/OpenMath" version="2.0">'
        + binder([(q, s("RealInnerProductSpace")) for q in spaces.split()] + ds, body)
        + "</OMOBJ>"
    )
    cards.append(
        {
            "id": "calculus_v4_" + key,
            "canonical_statement": "Let all vector spaces be finite-dimensional real inner product spaces. "
            + statement,
            "proof_strategy": steps[0],
            "sketch_steps": steps,
            "openmath_xml": canon(raw),
            "lean_target": "example "
            + BASELINE(spaces)
            + " "
            + params
            + " : "
            + target,
            "lean_witness": "by\n  " + proof.replace("\n", "\n  "),
        }
    )


V = lambda name, sp: (name, typ("Vector", sp))
Fn = lambda name, src, dst: (name, typ("Function", src, dst))
L = lambda name, src, dst: (name, typ("CLM", src, dst))
Sc = lambda name, src: (name, typ("ScalarFunction", src))
SL = lambda name, src: (name, typ("ScalarCLM", src))
R = lambda name: (name, typ("Real"))
common = [Fn("f", "E", "F"), L("A", "E", "F"), V("x", "E")]
pcommon = "(f : E → F) (A : E →L[ℝ] F) (x : E) (hf : HasFDerivAt f A x)"
add(
    "linear_map",
    "E F",
    [L("A", "E", "F"), V("x", "E")],
    "Every continuous linear map A has Fréchet derivative A at every x.",
    hd(E, F, a("linear_function", E, F, A), x, A),
    "(A : E →L[ℝ] F) (x : E)",
    "HasFDerivAt (fun y => A y) A x",
    "exact A.hasFDerivAt",
    [
        "Use linearity to expand A(x+h).",
        "Subtract A(x) and the candidate linear term A(h).",
        "The remainder is identically zero.",
        "Conclude Fréchet differentiability with derivative A.",
    ],
)
add(
    "affine_map",
    "E F",
    [L("A", "E", "F"), V("y", "F"), V("x", "E")],
    "The affine map z↦A z+y has derivative A at every x.",
    hd(E, F, a("affine_function", E, F, A, y), x, A),
    "(A : E →L[ℝ] F) (y : F) (x : E)",
    "HasFDerivAt (fun z => A z+y) A x",
    "exact HasFDerivAt.add_const y A.hasFDerivAt",
    [
        "Differentiate the continuous linear part.",
        "The fixed translation contributes no increment.",
        "Apply addition of a constant to the derivative witness.",
        "Keep the derivative map A at the same base point.",
    ],
)
for key, op, symbol, method in [
    ("sum", "function_add", "+", "add"),
    ("difference", "function_sub", "-", "sub"),
]:
    add(
        "frechet_" + key,
        "E F",
        [*common, Fn("g", "E", "F"), L("B", "E", "F")],
        f"If f and g have derivatives A and B at x, their {key} has derivative A{symbol}B.",
        imp(
            both(hd(E, F, f, x, A), hd(E, F, g, x, B)),
            hd(
                E,
                F,
                a(op, E, F, f, g),
                x,
                a("clm_" + ("add" if symbol == "+" else "sub"), E, F, A, B),
            ),
        ),
        pcommon + " (g : E → F) (B : E →L[ℝ] F) (hg : HasFDerivAt g B x)",
        f"HasFDerivAt (fun y => f y{symbol}g y) (A{symbol}B) x",
        f"exact hf.{method} hg",
        [
            "Write both first-order expansions at the same base point.",
            "Combine the continuous linear terms with the indicated sign.",
            "The corresponding sum or difference of little-o remainders is little-o.",
            "Conclude the displayed Fréchet derivative formula.",
        ],
    )
add(
    "constant_scalar",
    "E F",
    [*common, R("c")],
    "If Df(x)=A and c is fixed, the map y↦c•f(y) has derivative c•A.",
    imp(
        hd(E, F, f, x, A),
        hd(E, F, a("function_scale", E, F, c, f), x, a("clm_scale", E, F, c, A)),
    ),
    pcommon + " (c : ℝ)",
    "HasFDerivAt (fun y => c • f y) (c • A) x",
    "exact hf.const_smul c",
    [
        "Start with the Fréchet expansion of f.",
        "Multiply its linear part by the fixed scalar.",
        "Bounded scalar multiplication preserves a little-o remainder.",
        "Obtain the scaled derivative without requiring c to be nonzero.",
    ],
)
add(
    "chain_rule",
    "E F G",
    [*common, Fn("g", "F", "G"), L("B", "F", "G")],
    "If Df(x)=A and Dg(f(x))=B, then D(g∘f)(x)=B∘A.",
    imp(
        both(hd(E, F, f, x, A), hd(F, G, g, val(E, F, f, x), B)),
        hd(E, G, a("compose", E, F, G, g, f), x, a("clm_compose", E, F, G, B, A)),
    ),
    pcommon + " (g : F → G) (B : F →L[ℝ] G) (hg : HasFDerivAt g B (f x))",
    "HasFDerivAt (g ∘ f) (B.comp A) x",
    "exact hg.comp x hf",
    [
        "Differentiate the inner function at x.",
        "Evaluate the outer derivative at f(x).",
        "Compose the continuous linear maps in the order B after A.",
        "The Fréchet chain rule controls the composed remainder.",
    ],
)
add(
    "variable_scalar_product",
    "E F",
    [*common, Sc("g", "E"), SL("B", "E")],
    "If Df(x)=A and Dg(x)=B for real-valued g, D(g•f)(x)=g(x)•A+B.smulRight(f(x)).",
    imp(
        both(hd(E, F, f, x, A), hs(E, g, x, B)),
        hd(
            E,
            F,
            a("function_smul", E, F, g, f),
            x,
            a(
                "clm_add",
                E,
                F,
                a("clm_scale", E, F, sv(E, g, x), A),
                a("smul_right", E, F, B, val(E, F, f, x)),
            ),
        ),
    ),
    pcommon + " (g : E → ℝ) (B : E →L[ℝ] ℝ) (hg : HasFDerivAt g B x)",
    "HasFDerivAt (fun y => g y • f y) (g x • A + B.smulRight (f x)) x",
    "exact hg.smul hf",
    [
        "Treat scalar multiplication as a continuous bilinear operation.",
        "Vary f while fixing g(x), giving g(x)•A.",
        "Vary g while fixing f(x), giving B.smulRight(f(x)).",
        "Add both linear terms; their product remainder is higher order.",
    ],
)
add(
    "inner_product_rule",
    "E F",
    [*common, Fn("g", "E", "F"), L("B", "E", "F")],
    "For Df(x)=A,Dg(x)=B, the derivative of ⟨f,g⟩ sends h to ⟨A h,g(x)⟩+⟨f(x),B h⟩.",
    imp(
        both(hd(E, F, f, x, A), hd(E, F, g, x, B)),
        hs(
            E,
            a("inner_composition", E, F, f, g),
            x,
            a("inner_derivative", E, F, val(E, F, f, x), val(E, F, g, x), A, B),
        ),
    ),
    pcommon + " (g : E → F) (B : E →L[ℝ] F) (hg : HasFDerivAt g B x)",
    "HasFDerivAt (fun y => inner ℝ (f y) (g y)) ((fderivInnerCLM ℝ (f x,g x)).comp (A.prod B)) x",
    "exact hf.inner ℝ hg",
    [
        "Pair the two derivative witnesses.",
        "Differentiate the continuous bilinear real inner product.",
        "Its linear part varies each argument once.",
        "Compose with the paired derivative A.prod B.",
    ],
)
add(
    "norm_square_chain",
    "E F",
    common,
    "If Df(x)=A, the derivative of ‖f‖² is 2•(innerSL ℝ (f x)).comp A.",
    imp(
        hd(E, F, f, x, A),
        hs(
            E,
            a("norm_square_composition", E, F, f),
            x,
            a("norm_square_derivative", E, F, val(E, F, f, x), A),
        ),
    ),
    pcommon,
    "HasFDerivAt (fun y => ‖f y‖^2) (2 • (innerSL ℝ (f x)).comp A) x",
    "exact hf.norm_sq",
    [
        "Express the squared norm as a self inner product.",
        "Apply the inner-product differentiation rule.",
        "Symmetry over ℝ identifies the two linear terms.",
        "Compose the resulting factor 2 with A, including f(x)=0.",
    ],
)
add(
    "norm_away_zero",
    "E F",
    [Fn("f", "E", "F"), V("x", "E")],
    "Differentiability of f at x and f(x)≠0 imply differentiability of ‖f‖ at x.",
    imp(
        both(
            a("differentiable_at", E, F, f, x),
            neq(val(E, F, f, x), a("vector_zero", F)),
        ),
        a("scalar_differentiable_at", E, a("norm_composition", E, F, f), x),
    ),
    "(f : E → F) (x : E) (hf : DifferentiableAt ℝ f x) (hx : f x ≠ 0)",
    "DifferentiableAt ℝ (fun y => ‖f y‖) x",
    "exact hf.norm ℝ hx",
    [
        "The Hilbert norm is smooth away from zero.",
        "The value f(x) lies in that nonzero region.",
        "Compose its local differentiability with that of f.",
        "Retain the nonzero-value premise in the result.",
    ],
)
add(
    "distance_off_diagonal",
    "E F",
    [Fn("f", "E", "F"), Fn("g", "E", "F"), V("x", "E")],
    "If f,g are differentiable at x and f(x)≠g(x), their pointwise distance is differentiable at x.",
    imp(
        both(
            both(
                a("differentiable_at", E, F, f, x), a("differentiable_at", E, F, g, x)
            ),
            neq(val(E, F, f, x), val(E, F, g, x)),
        ),
        a("scalar_differentiable_at", E, a("distance_composition", E, F, f, g), x),
    ),
    "(f g : E → F) (x : E) (hf : DifferentiableAt ℝ f x) (hg : DifferentiableAt ℝ g x) (hx : f x ≠ g x)",
    "DifferentiableAt ℝ (fun y => dist (f y) (g y)) x",
    "exact hf.dist ℝ hg hx",
    [
        "Write distance as the norm of f-g.",
        "The difference is differentiable at x.",
        "The distinct-value premise makes this difference nonzero.",
        "Apply differentiability of the norm away from zero.",
    ],
)
add(
    "frechet_unique",
    "E F",
    [*common, L("B", "E", "F")],
    "Two Fréchet derivative witnesses A,B for the same f at x are equal.",
    imp(both(hd(E, F, f, x, A), hd(E, F, f, x, B)), eq(A, B)),
    pcommon + " (B : E →L[ℝ] F) (hb : HasFDerivAt f B x)",
    "A=B",
    "exact hf.unique hb",
    [
        "Subtract the two first-order expansions.",
        "Their continuous linear difference is little-o of the increment.",
        "Evaluate along scalar multiples of each direction.",
        "The difference vanishes on every vector, so the maps agree.",
    ],
)
add(
    "frechet_continuity",
    "E F",
    common,
    "A Fréchet derivative at x implies continuity at x.",
    imp(hd(E, F, f, x, A), a("continuous_at", E, F, f, x)),
    pcommon,
    "ContinuousAt f x",
    "exact hf.continuousAt",
    [
        "Use the derivative expansion at x.",
        "A continuous linear map sends small increments to small vectors.",
        "The little-o remainder also tends to zero.",
        "Thus f(y) tends to f(x) as y tends to x.",
    ],
)
add(
    "frechet_operator_value",
    "E F",
    common,
    "A derivative witness Df(x)=A identifies the totalized fderiv operator with A.",
    imp(hd(E, F, f, x, A), eq(a("fderiv", E, F, f, x), A)),
    pcommon,
    "fderiv ℝ f x=A",
    "exact hf.fderiv",
    [
        "The witness establishes actual differentiability.",
        "The chosen fderiv is a derivative under that premise.",
        "Apply uniqueness of the Fréchet derivative.",
        "Conclude the operator equality without asserting converse existence from a totalized value.",
    ],
)
sc = [Sc("f", "E"), V("x", "E"), V("u", "E")]
ps = "(f : E → ℝ) (x u : E) (hf : HasGradientAt f u x)"
add(
    "gradient_riesz_representation",
    "E",
    sc,
    "Having gradient u at x is equivalent to having Fréchet derivative h↦⟨u,h⟩ there.",
    both(
        imp(hg(E, f, x, u), hs(E, f, x, a("dual", E, u))),
        imp(hs(E, f, x, a("dual", E, u)), hg(E, f, x, u)),
    ),
    "(f : E → ℝ) (x u : E)",
    "HasGradientAt f u x ↔ HasFDerivAt f (InnerProductSpace.toDual ℝ E u) x",
    "exact hasGradientAt_iff_hasFDerivAt",
    [
        "Use the Riesz map from vectors to continuous real linear functionals.",
        "It sends u to the functional h↦⟨u,h⟩.",
        "Unfold the definition of a gradient derivative.",
        "Both implications retain the same point and represented functional.",
    ],
)
add(
    "gradient_unique",
    "E",
    [*sc, V("w", "E")],
    "Two gradients u,w of f at the same point x are equal.",
    imp(both(hg(E, f, x, u), hg(E, f, x, w)), eq(u, w)),
    ps + " (w : E) (hw : HasGradientAt f w x)",
    "u=w",
    "exact hf.unique hw",
    [
        "Represent both gradients by continuous linear functionals.",
        "Their derivative witnesses are unique.",
        "The Riesz map is injective.",
        "Therefore the gradient vectors coincide.",
    ],
)
add(
    "gradient_continuity",
    "E",
    sc,
    "A gradient witness for f at x implies continuity of f at x.",
    imp(hg(E, f, x, u), a("scalar_continuous_at", E, f, x)),
    ps,
    "ContinuousAt f x",
    "exact hf.continuousAt",
    [
        "Convert the gradient to its Fréchet derivative witness.",
        "The representing inner-product functional is continuous.",
        "The first-order remainder tends to zero.",
        "Deduce continuity of the scalar function.",
    ],
)
add(
    "gradient_linear_functional",
    "E",
    [V("u", "E"), V("x", "E")],
    "The gradient of the linear functional y↦⟨u,y⟩ is u at every x.",
    hg(E, a("inner_function", E, u), x, u),
    "(u x : E)",
    "HasGradientAt (fun y => inner ℝ u y) u x",
    "apply hasGradientAt_iff_hasFDerivAt.mpr\nexact (InnerProductSpace.toDual ℝ E u).hasFDerivAt",
    [
        "The inner-product functional is continuous and linear.",
        "Its derivative equals the functional itself.",
        "The Riesz map represents this functional by u.",
        "Use the gradient–Fréchet equivalence at the arbitrary point.",
    ],
)
add(
    "gradient_squared_norm",
    "E",
    [V("x", "E")],
    "The gradient of y↦‖y‖² at x is 2•x.",
    hg(E, a("norm_square", E), x, a("vector_scale", E, real(2), x)),
    "(x : E)",
    "HasGradientAt (fun y : E => ‖y‖^2) (2 • x) x",
    "apply hasGradientAt_iff_hasFDerivAt.mpr\nconvert! (hasStrictFDerivAt_norm_sq x).hasFDerivAt using 1\n  <;> ext y <;> simp [inner_smul_left]",
    [
        "Use the self-inner-product expression",
        "Split the derivative into two identical real inner-product terms",
        "Represent their sum by the vector 2•x",
        "This also holds at the zero vector.",
    ],
)
add(
    "minimum_gradient_zero",
    "E",
    sc,
    "At an unconstrained local minimum of differentiable scalar f, its gradient is zero.",
    imp(both(a("local_min", E, f, x), hg(E, f, x, u)), eq(u, a("vector_zero", E))),
    ps + " (hm : IsLocalMin f x)",
    "u=0",
    "have h := hm.hasFDerivAt_eq_zero hf.hasFDerivAt\nexact (InnerProductSpace.toDual ℝ E).injective (by simpa using h)",
    [
        "Represent the gradient as the Fréchet derivative.",
        "Fermat’s theorem makes that derivative zero at an unconstrained local minimum.",
        "The zero vector represents the zero functional.",
        "Injectivity of the Riesz map gives a zero gradient.",
    ],
)
add(
    "directional_from_frechet",
    "E F",
    [*common, V("u", "E")],
    "A Fréchet derivative A at x gives directional derivative A u along every direction u.",
    imp(
        hd(E, F, f, x, A),
        a("has_line_deriv", E, F, f, x, u, a("clm_apply", E, F, A, u)),
    ),
    pcommon + " (u : E)",
    "HasLineDerivAt ℝ f (A u) x u",
    "exact hf.hasLineDerivAt u",
    [
        "Restrict f to the affine line x+t•u.",
        "The line has velocity u at t=0.",
        "Apply the Fréchet chain rule along this curve.",
        "The resulting one-variable derivative is A(u).",
    ],
)
add(
    "curve_chain_rule",
    "E F",
    [
        Fn("f", "E", "F"),
        L("A", "E", "F"),
        ("c", typ("Curve", "E")),
        R("t"),
        V("u", "E"),
    ],
    "If c has velocity u at t and Df(c(t))=A, then f∘c has velocity A u at t.",
    imp(
        both(
            a("has_curve_deriv", E, c, t, u), hd(E, F, f, a("curve_apply", E, c, t), A)
        ),
        a(
            "has_curve_deriv",
            F,
            a("curve_compose", E, F, f, c),
            t,
            a("clm_apply", E, F, A, u),
        ),
    ),
    "(f : E → F) (A : E →L[ℝ] F) (c : ℝ → E) (t : ℝ) (u : E) (hc : HasDerivAt c u t) (hf : HasFDerivAt f A (c t))",
    "HasDerivAt (f ∘ c) (A u) t",
    "exact hf.comp_hasDerivAt t hc",
    [
        "Differentiate the curve at its parameter t.",
        "Evaluate the outer derivative at the curve point c(t).",
        "Apply that linear map to the velocity u.",
        "The one-dimensional composition rule yields the new velocity.",
    ],
)
add(
    "gradient_along_curve",
    "E",
    [Sc("f", "E"), ("c", typ("Curve", "E")), R("t"), V("u", "E"), V("w", "E")],
    "If c has velocity u at t and f has gradient w at c(t), then (f∘c)′(t)=⟨w,u⟩.",
    imp(
        both(a("has_curve_deriv", E, c, t, u), hg(E, f, a("curve_apply", E, c, t), w)),
        a("has_real_deriv", a("scalar_curve_compose", E, f, c), t, a("inner", E, w, u)),
    ),
    "(f : E → ℝ) (c : ℝ → E) (t : ℝ) (u w : E) (hc : HasDerivAt c u t) (hf : HasGradientAt f w (c t))",
    "HasDerivAt (f ∘ c) (inner ℝ w u) t",
    "exact hf.hasFDerivAt.comp_hasDerivAt t hc",
    [
        "Represent the gradient by its inner-product functional.",
        "Differentiate along c using its velocity u.",
        "The curve chain rule applies the functional to u.",
        "This evaluation is exactly ⟨w,u⟩.",
    ],
)
add(
    "gradient_direction_bound",
    "E",
    [*sc, V("w", "E")],
    "If f has gradient u at x, the absolute directional slope |Df(x)[w]| is at most ‖u‖‖w‖.",
    imp(
        hg(E, f, x, u),
        le(
            a("real_abs", a("scalar_line_deriv", E, f, x, w)),
            a("real_mul", norm(E, u), norm(E, w)),
        ),
    ),
    ps + " (w : E)",
    "|lineDeriv ℝ f x w| ≤ ‖u‖*‖w‖",
    "rw [(hf.hasFDerivAt.hasLineDerivAt w).lineDeriv]\nexact abs_real_inner_le_norm u w",
    [
        "The gradient represents the directional derivative as ⟨u,w⟩.",
        "Apply the real Cauchy–Schwarz inequality.",
        "Its two factors are the gradient norm and direction norm.",
        "Keep the absolute value; no unit-length direction is assumed.",
    ],
)
add(
    "zero_derivative_constant",
    "E F",
    [Fn("f", "E", "F"), V("x", "E"), V("y", "E")],
    "If f has zero Fréchet derivative at every point, f(x)=f(y) for every pair x,y.",
    imp(
        binder([V("z", "E")], hd(E, F, f, z, a("clm_zero", E, F))),
        eq(val(E, F, f, x), val(E, F, f, y)),
    ),
    "(f : E → F) (hf : ∀ z, HasFDerivAt f (0 : E →L[ℝ] F) z) (x y : E)",
    "f x=f y",
    "exact is_const_of_fderiv_eq_zero (𝕜 := ℝ) (fun z => (hf z).differentiableAt) (fun z => (hf z).fderiv) x y",
    [
        "Every derivative witness gives differentiability.",
        "The derivative field is zero on the entire vector space.",
        "The domain is convex, so the mean-value estimate along each segment applies.",
        "The image difference has norm zero and the values coincide.",
    ],
)
add(
    "bounded_derivative_lipschitz",
    "E F",
    [
        Fn("f", "E", "F"),
        ("D", typ("DerivativeField", "E", "F")),
        R("c"),
        V("x", "E"),
        V("y", "E"),
    ],
    "A globally valid derivative field D with ‖D(z)‖≤c everywhere gives ‖f(y)-f(x)‖≤c‖y-x‖.",
    imp(
        both(
            a("derivative_field", E, F, f, D),
            binder(
                [V("z", "E")], le(a("clm_norm", E, F, a("field_apply", E, F, D, z)), c)
            ),
        ),
        le(
            norm(F, a("vector_sub", F, val(E, F, f, y), val(E, F, f, x))),
            a("real_mul", c, norm(E, a("vector_sub", E, y, x))),
        ),
    ),
    "(f : E → F) (D : E → E →L[ℝ] F) (c : ℝ) (hf : ∀ z, HasFDerivAt f (D z) z) (hb : ∀ z, ‖D z‖ ≤ c) (x y : E)",
    "‖f y-f x‖ ≤ c*‖y-x‖",
    "exact (convex_univ : Convex ℝ (Set.univ : Set E)).norm_image_sub_le_of_norm_hasFDerivWithin_le (fun z _ => (hf z).hasFDerivWithinAt) (fun z _ => hb z) (Set.mem_univ x) (Set.mem_univ y)",
    [
        "Use the convexity of the full real vector space.",
        "Restrict the derivative witnesses to the segment between x and y.",
        "The same operator-norm bound controls every derivative on that segment.",
        "Apply the vector-valued mean-value inequality.",
    ],
)
add(
    "second_derivative_symmetry",
    "E F",
    [
        Fn("f", "E", "F"),
        ("D", typ("DerivativeField", "E", "F")),
        ("H", typ("Bilinear", "E", "F")),
        V("x", "E"),
        V("u", "E"),
        V("w", "E"),
    ],
    "If D is a derivative field of f everywhere and D has derivative H at x, then H(u)(w)=H(w)(u).",
    imp(
        both(a("derivative_field", E, F, f, D), a("has_second_deriv", E, F, D, x, H)),
        eq(a("bilinear_apply", E, F, H, u, w), a("bilinear_apply", E, F, H, w, u)),
    ),
    "(f : E → F) (D : E → E →L[ℝ] F) (H : E →L[ℝ] E →L[ℝ] F) (x u w : E) (hf : ∀ y, HasFDerivAt f (D y) y) (hD : HasFDerivAt D H x)",
    "H u w=H w u",
    "exact second_derivative_symmetric hf hD u w",
    [
        "Use D as the actual first derivative in a neighborhood of x.",
        "The derivative of D supplies the continuous bilinear second-order map H.",
        "Apply the symmetry theorem for second Fréchet derivatives over ℝ.",
        "Evaluate in the two arbitrary directions in either order.",
    ],
)
add(
    "smooth_composition",
    "E F G",
    [("n", typ("Nat")), Fn("f", "E", "F"), Fn("g", "F", "G")],
    "For every natural n, composing two C^n maps gives a C^n map.",
    imp(
        both(a("cont_diff", E, F, n, f), a("cont_diff", F, G, n, g)),
        a("cont_diff", E, G, n, a("compose", E, F, G, g, f)),
    ),
    "(n : ℕ) (f : E → F) (g : F → G) (hf : ContDiff ℝ n f) (hg : ContDiff ℝ n g)",
    "ContDiff ℝ n (g ∘ f)",
    "exact hg.comp hf",
    [
        "Use C^n regularity of the inner function.",
        "Use the same order of regularity for the outer function.",
        "Composition preserves each derivative order through n.",
        "The statement includes n=0, where it is continuity under composition.",
    ],
)
add(
    "smooth_squared_norm",
    "E F",
    [("n", typ("Nat")), Fn("f", "E", "F")],
    "For every natural n, a C^n map f has a C^n squared norm ‖f‖², including zeros of f.",
    imp(
        a("cont_diff", E, F, n, f),
        a("scalar_cont_diff", E, n, a("norm_square_composition", E, F, f)),
    ),
    "(n : ℕ) (f : E → F) (hf : ContDiff ℝ n f)",
    "ContDiff ℝ n (fun y => ‖f y‖^2)",
    "exact hf.norm_sq ℝ",
    [
        "Express squared norm as a continuous bilinear inner product on the diagonal.",
        "The inner product is smooth at zero as well as elsewhere.",
        "Compose it with the pair of C^n maps f,f.",
        "Conclude C^n regularity without a nonvanishing premise.",
    ],
)
add(
    "smooth_inner_product",
    "E F",
    [("n", typ("Nat")), Fn("f", "E", "F"), Fn("g", "E", "F")],
    "For every natural n, the inner product of two C^n maps is C^n.",
    imp(
        both(a("cont_diff", E, F, n, f), a("cont_diff", E, F, n, g)),
        a("scalar_cont_diff", E, n, a("inner_composition", E, F, f, g)),
    ),
    "(n : ℕ) (f g : E → F) (hf : ContDiff ℝ n f) (hg : ContDiff ℝ n g)",
    "ContDiff ℝ n (fun y => inner ℝ (f y) (g y))",
    "exact hf.inner ℝ hg",
    [
        "Pair the C^n maps f and g.",
        "The real inner product is a continuous bilinear operation.",
        "Continuous bilinear operations are smooth of every finite order.",
        "Compose to retain exactly the stated order n.",
    ],
)
add(
    "local_extremum_derivative_zero",
    "E",
    [Sc("f", "E"), SL("A", "E"), V("x", "E")],
    "At an unconstrained local extremum, a scalar function’s Fréchet derivative A is zero.",
    imp(
        both(a("local_extremum", E, f, x), hs(E, f, x, A)),
        eq(A, a("scalar_clm_zero", E)),
    ),
    "(f : E → ℝ) (A : E →L[ℝ] ℝ) (x : E) (hf : HasFDerivAt f A x) (he : IsLocalExtr f x)",
    "A=0",
    "exact he.hasFDerivAt_eq_zero hf",
    [
        "Restrict the scalar function to each line through the extremum.",
        "Each resulting real function has a local extremum at zero.",
        "Fermat’s theorem forces its directional derivative to vanish.",
        "The linear derivative is zero on every direction, hence is the zero map.",
    ],
)
add(
    "gradient_sum",
    "E",
    [*sc, Sc("g", "E"), V("w", "E")],
    "If f,g have gradients u,w at x, their sum has gradient u+w.",
    imp(
        both(hg(E, f, x, u), hg(E, g, x, w)),
        hg(E, a("scalar_add", E, f, g), x, a("vector_add", E, u, w)),
    ),
    ps + " (g : E → ℝ) (w : E) (hg : HasGradientAt g w x)",
    "HasGradientAt (fun y => f y+g y) (u+w) x",
    "apply hasGradientAt_iff_hasFDerivAt.mpr\nconvert! hf.hasFDerivAt.add hg.hasFDerivAt using 1 <;> simp",
    [
        "Represent each gradient as a real linear functional.",
        "Add the derivative witnesses at the common point.",
        "Linearity of the Riesz map identifies the sum functional with u+w.",
        "Convert that derivative witness back to a gradient.",
    ],
)
add(
    "gradient_scalar",
    "E",
    [*sc, R("c")],
    "For fixed real c, a gradient u for f gives gradient c•u for c*f.",
    imp(
        hg(E, f, x, u), hg(E, a("scalar_scale", E, c, f), x, a("vector_scale", E, c, u))
    ),
    ps + " (c : ℝ)",
    "HasGradientAt (fun y => c*f y) (c • u) x",
    "apply hasGradientAt_iff_hasFDerivAt.mpr\nconvert! hf.hasFDerivAt.const_smul c using 1 <;> simp",
    [
        "Represent u by its real inner-product functional.",
        "Scale the derivative by the fixed real c.",
        "The real Riesz representation respects this scalar multiplication.",
        "Conclude the gradient formula even when c=0.",
    ],
)
add(
    "gradient_adjoint_chain",
    "E F",
    [Fn("g", "E", "F"), Sc("f", "F"), L("A", "E", "F"), V("x", "E"), V("u", "F")],
    "If Dg(x)=A and f has gradient u at g(x), then f∘g has gradient A.adjoint(u) at x.",
    imp(
        both(hd(E, F, g, x, A), hg(F, f, val(E, F, g, x), u)),
        hg(E, a("scalar_compose", E, F, f, g), x, a("adjoint_apply", E, F, A, u)),
    ),
    "(g : E → F) (f : F → ℝ) (A : E →L[ℝ] F) (x : E) (u : F) (hg : HasFDerivAt g A x) (hf : HasGradientAt f u (g x))",
    "HasGradientAt (f ∘ g) (A.adjoint u) x",
    "apply hasGradientAt_iff_hasFDerivAt.mpr\nconvert! hf.hasFDerivAt.comp x hg using 1\next v\nexact A.adjoint_inner_left v u",
    [
        "Apply the Fréchet chain rule to the scalar outer function.",
        "Its derivative sends a direction h to ⟨u,A h⟩.",
        "The adjoint identity rewrites this as ⟨A.adjoint u,h⟩.",
        "Use Riesz representation to identify the composite gradient.",
    ],
)


def main():
    assert len(cards) >= 30 and len({c["openmath_xml"] for c in cards}) == len(cards)
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
    witness = ROOT / "docs/calculus-v4-batch.lean"
    witness.write_text(source)
    result = subprocess.run(
        ["lake", "env", "lean", str(witness)],
        cwd=WORKSPACE,
        text=True,
        capture_output=True,
        timeout=180,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    sha = lambda p: "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()
    packages = json.loads((WORKSPACE / "lake-manifest.json").read_text())["packages"]
    evidence = {
        "witness_path": str(witness.relative_to(ROOT)),
        "witness_sha256": sha(witness),
        "validator_sha256": sha(ROOT / "pals-agent/pals_agent/typed_calculus_v4.py"),
        "registry_sha256": sha(
            ROOT
            / "pals-agent/pals_agent/content_dictionaries/typed-calculus-v4-registry.json"
        ),
        "toolchain": (WORKSPACE / "lean-toolchain").read_text().strip(),
        "mathlib_revision": next(p["rev"] for p in packages if p["name"] == "mathlib"),
    }
    (ROOT / "docs/calculus-v4-batch.json").write_text(
        json.dumps(
            {
                "schema_version": "pals.typed-catalog-expansion-batch.v1",
                "profile_id": "typed-calculus-v4",
                "cards": cards,
                "evidence": evidence,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )
    print(f"PASS {len(cards)} canonical general multivariable cards compiled")


if __name__ == "__main__":
    main()
