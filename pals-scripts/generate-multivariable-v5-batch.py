"""Generate an isolated multivariable foundation batch only after actual Lean compilation."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pals-agent"))
from pals_agent.typed_multivariable_v5 import (
    canonicalize_typed_multivariable_v5_openmath_xml as canon,
)

BASE = "urn:pals:openmath:typed-multivariable:v5"
WORKSPACE = ROOT / "pals-agent/lean-workspace"


def s(name, cd="multivar5"):
    base = BASE if cd in {"multivar5", "typed5"} else "http://www.openmath.org/cd"
    return f'<OMS cdbase="{base}" cd="{cd}" name="{name}"/>'


def v(name):
    return f'<OMV name="{name}"/>'


def a(name, *args):
    return "<OMA>" + s(name) + "".join(args) + "</OMA>"


def st(cd, name, *args):
    return "<OMA>" + s(name, cd) + "".join(args) + "</OMA>"


def eq(x, y):
    return st("relation1", "eq", x, y)


def ne(x, y):
    return st("relation1", "neq", x, y)


def both(x, y):
    return st("logic1", "and", x, y)


def either(x, y):
    return st("logic1", "or", x, y)


def neg(x):
    return st("logic1", "not", x)


def iff(x, y):
    return st("logic1", "equivalent", x, y)


def imp(*terms):
    result = terms[-1]
    for premise in reversed(terms[:-1]):
        result = st("logic1", "implies", premise, result)
    return result


def bind(ds, body, kind="forall"):
    return (
        "<OMBIND>"
        + s(kind, "typed5")
        + "<OMBVAR>"
        + "".join(
            "<OMATTR><OMATP>"
            + s("type", "typed5")
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


def T(name, *dims):
    return a(name, *map(v, dims)) if dims else s(name)


def N(*names):
    return [(x, T("Nat")) for x in names]


def decl(name, ty, *dims):
    return (name, T(ty, *dims))


def real(n):
    return a("real_nat", f"<OMI>{n}</OMI>")


Z = real(0)
(
    M,
    n,
    p,
    k,
    x,
    y,
    h,
    i,
    j,
    f,
    g,
    A,
    B,
    D,
    H,
    u,
    w,
    c,
    d,
    q,
    b,
    t,
    aa,
    bb,
    L,
    lam,
    F,
    V,
) = map(
    v,
    [
        "m",
        "n",
        "p",
        "k",
        "x",
        "y",
        "h",
        "i",
        "j",
        "f",
        "g",
        "A",
        "B",
        "D",
        "H",
        "u",
        "w",
        "c",
        "d",
        "q",
        "b",
        "t",
        "a",
        "b",
        "L",
        "lambda",
        "F",
        "V",
    ],
)
cards = []


def add(identifier, ds, body, statement, target, proof, steps):
    cards.append(
        {
            "id": "mv_v5_" + identifier,
            "canonical_statement": statement,
            "proof_strategy": steps[0],
            "sketch_steps": steps,
            "openmath_xml": canon(
                '<OMOBJ xmlns="http://www.openmath.org/OpenMath" version="2.0">'
                + bind(ds, body)
                + "</OMOBJ>"
            ),
            "lean_target": target,
            "lean_witness": "by\n" + proof.rstrip(),
        }
    )


add(
    "coordinate_projection",
    N("n") + [decl("i", "Index", "n"), decl("x", "Vector", "n")],
    a("has_scalar_fderiv", n, a("projection", n, i), x, a("projection_clm", n, i)),
    "For every natural dimension n, coordinate i∈Fin n and point x∈ℝⁿ, coordinate projection y↦yᵢ has derivative the ith coordinate functional at x.",
    "example (n : ℕ) (i : Fin n) (x : Fin n → ℝ) : HasFDerivAt (fun y : Fin n → ℝ => y i) (ContinuousLinearMap.proj i : (Fin n → ℝ) →L[ℝ] ℝ) x",
    "  exact hasFDerivAt_apply (𝕜 := ℝ) i x",
    [
        "Identify coordinate projection as a continuous linear functional.",
        "Use the standard product norm on the finite coordinate space.",
        "The derivative of this projection is the projection itself at every point.",
        "Retain arbitrary n and the valid coordinate index i in the conclusion.",
    ],
)
add(
    "coordinate_update",
    N("n") + [decl("x", "Vector", "n"), decl("i", "Index", "n"), decl("t", "Real")],
    a("has_curve_deriv", n, a("update_curve", n, x, i), t, a("basis_vector", n, i)),
    "For every n, x∈ℝⁿ, i∈Fin n and t∈ℝ, the coordinate-update curve u↦update(x,i,u) has velocity eᵢ at t.",
    "example (n : ℕ) (x : Fin n → ℝ) (i : Fin n) (t : ℝ) : HasDerivAt (Function.update x i) (Pi.single i 1) t",
    "  exact hasDerivAt_update x i t",
    [
        "Regard the updated coordinate as the curve parameter.",
        "All coordinates except i are constant.",
        "The ith coordinate has derivative one, giving the standard basis vector.",
        "Apply the derivative-of-update theorem at the arbitrary parameter t.",
    ],
)
add(
    "coordinate_partial_from_total",
    N("n")
    + [
        decl("f", "ScalarFunction", "n"),
        decl("A", "ScalarCLM", "n"),
        decl("x", "Vector", "n"),
        decl("i", "Index", "n"),
    ],
    imp(
        a("has_scalar_fderiv", n, f, x, A),
        a(
            "has_deriv",
            a("coordinate_slice", n, f, x, i),
            a("coordinate", n, x, i),
            a("dual_apply", n, A, a("basis_vector", n, i)),
        ),
    ),
    "For a scalar f:ℝⁿ→ℝ with actual Fréchet derivative A at x, its ith coordinate slice has derivative A(eᵢ) at the coordinate value xᵢ.",
    "example (n : ℕ) (f : (Fin n → ℝ) → ℝ) (A : (Fin n → ℝ) →L[ℝ] ℝ) (x : Fin n → ℝ) (i : Fin n) (hf : HasFDerivAt f A x) : HasDerivAt (fun t => f (Function.update x i t)) (A (Pi.single i 1)) (x i)",
    "  have hh : HasFDerivAt f A (Function.update x i (x i)) := by simpa using hf\n  exact hh.comp_hasDerivAt (x i) (hasDerivAt_update x i (x i))",
    [
        "Use the actual total derivative hypothesis, not merely a totalized fderiv value.",
        "The coordinate-update curve returns x at parameter xᵢ.",
        "Its velocity is eᵢ.",
        "Compose the two derivative witnesses to obtain A(eᵢ).",
    ],
)
add(
    "component_derivative_assembly",
    N("m", "n")
    + [
        decl("f", "Function", "m", "n"),
        decl("A", "CLM", "m", "n"),
        decl("x", "Vector", "m"),
    ],
    iff(
        a("has_fderiv", M, n, f, x, A),
        bind(
            [decl("j", "Index", "n")],
            a(
                "has_scalar_fderiv",
                M,
                a("component", M, n, f, j),
                x,
                a("component_clm", M, n, A, j),
            ),
        ),
    ),
    "For arbitrary finite dimensions m,n, HasFDerivAt f A x is equivalent to every output component fⱼ having Fréchet derivative projⱼ∘A at x. These are total derivatives of components, not input partial derivatives alone.",
    "example (m n : ℕ) (f : (Fin m → ℝ) → (Fin n → ℝ)) (A : (Fin m → ℝ) →L[ℝ] (Fin n → ℝ)) (x : Fin m → ℝ) : HasFDerivAt f A x ↔ ∀ j : Fin n, HasFDerivAt (fun y => f y j) ((ContinuousLinearMap.proj j).comp A) x",
    "  exact hasFDerivAt_pi'",
    [
        "Distinguish output components from input-coordinate partial derivatives.",
        "Project a total derivative to each output coordinate for the forward implication.",
        "Assemble the finitely many component derivative estimates for the reverse implication.",
        "Identify the assembled derivative with the specified map A.",
    ],
)
add(
    "component_differentiability",
    N("m", "n") + [decl("f", "Function", "m", "n"), decl("x", "Vector", "m")],
    iff(
        a("differentiable_at", M, n, f, x),
        bind(
            [decl("j", "Index", "n")],
            a("scalar_differentiable_at", M, a("component", M, n, f, j), x),
        ),
    ),
    "A map f:ℝᵐ→ℝⁿ is Fréchet differentiable at x if and only if each scalar output component is Fréchet differentiable there; no assertion is made from the existence of input partials alone.",
    "example (m n : ℕ) (f : (Fin m → ℝ) → (Fin n → ℝ)) (x : Fin m → ℝ) : DifferentiableAt ℝ f x ↔ ∀ j : Fin n, DifferentiableAt ℝ (fun y => f y j) x",
    "  exact differentiableAt_pi",
    [
        "Extract differentiability of every coordinate by projection.",
        "For the converse, choose each component derivative.",
        "The finite product of these linear functionals is continuous.",
        "Apply differentiability of finite products to recover differentiability of f.",
    ],
)
J = a("jacobian", M, n, f, x)
add(
    "jacobian_entries",
    N("m", "n")
    + [
        decl("f", "Function", "m", "n"),
        decl("x", "Vector", "m"),
        decl("i", "Index", "m"),
        decl("j", "Index", "n"),
    ],
    imp(
        a("differentiable_at", M, n, f, x),
        a(
            "has_deriv",
            a("coordinate_slice", M, a("component", M, n, f, j), x, i),
            a("coordinate", M, x, i),
            a("matrix_entry", n, M, J, j, i),
        ),
    ),
    "If f:ℝᵐ→ℝⁿ is differentiable at x, the derivative of t↦f(update(x,i,t))ⱼ at xᵢ equals the (j,i) entry of its Jacobian, whose rows are output coordinates and columns are input coordinates.",
    "example (m n : ℕ) (f : (Fin m → ℝ) → (Fin n → ℝ)) (x : Fin m → ℝ) (i : Fin m) (j : Fin n) (hf : DifferentiableAt ℝ f x) : HasDerivAt (fun t => f (Function.update x i t) j) (LinearMap.toMatrix' (fderiv ℝ f x).toLinearMap j i) (x i)",
    "  have hc := (hasFDerivAt_pi'.mp hf.hasFDerivAt) j\n  have hh : HasFDerivAt (fun y => f y j) ((ContinuousLinearMap.proj j).comp (fderiv ℝ f x)) (Function.update x i (x i)) := by simpa using hc\n  simpa [Function.comp_def, LinearMap.toMatrix'_apply] using! hh.comp_hasDerivAt (x i) (hasDerivAt_update x i (x i))",
    [
        "Take the total derivative of the jth output component.",
        "Restrict that component along the ith coordinate-update curve.",
        "The derivative evaluates the total linear map on eᵢ and then projects to coordinate j.",
        "Use the standard-basis matrix entry formula to identify row j, column i.",
    ],
)
add(
    "jacobian_chain",
    N("m", "n", "p")
    + [
        decl("f", "Function", "m", "n"),
        decl("g", "Function", "n", "p"),
        decl("x", "Vector", "m"),
    ],
    imp(
        a("differentiable_at", M, n, f, x),
        a("differentiable_at", n, p, g, a("apply", M, n, f, x)),
        eq(
            a("jacobian", M, p, a("compose", M, n, p, g, f), x),
            a("matrix_mul", p, n, M, a("jacobian", n, p, g, a("apply", M, n, f, x)), J),
        ),
    ),
    "For differentiable f:ℝᵐ→ℝⁿ at x and g:ℝⁿ→ℝᵖ at f(x), J(g∘f)(x)=Jg(f(x)) Jf(x), in this matrix order and with arbitrary rectangular dimensions.",
    "example (m n p : ℕ) (f : (Fin m → ℝ) → (Fin n → ℝ)) (g : (Fin n → ℝ) → (Fin p → ℝ)) (x : Fin m → ℝ) (hf : DifferentiableAt ℝ f x) (hg : DifferentiableAt ℝ g (f x)) : LinearMap.toMatrix' (fderiv ℝ (g ∘ f) x).toLinearMap = LinearMap.toMatrix' (fderiv ℝ g (f x)).toLinearMap * LinearMap.toMatrix' (fderiv ℝ f x).toLinearMap",
    "  rw [fderiv_comp x hg hf, ContinuousLinearMap.toLinearMap_comp, LinearMap.toMatrix'_comp]",
    [
        "Apply the Fréchet chain rule at x and f(x), respectively.",
        "Pass the derivative composition to its underlying linear maps.",
        "Standard-coordinate matrices turn composition into matrix multiplication.",
        "Keep the outer Jacobian on the left and the inner Jacobian on the right.",
    ],
)
add(
    "jacobian_first_order_remainder",
    N("m", "n") + [decl("f", "Function", "m", "n"), decl("x", "Vector", "m")],
    imp(
        a("differentiable_at", M, n, f, x),
        a("little_o_displacement", M, n, a("linearization_remainder", M, n, f, x), x),
    ),
    "For differentiable f:ℝᵐ→ℝⁿ at x, the full coordinate linearization remainder f(y)−f(x)−Jf(x)(y−x) is little-o of y−x as y tends to x.",
    "example (m n : ℕ) (f : (Fin m → ℝ) → (Fin n → ℝ)) (x : Fin m → ℝ) (hf : DifferentiableAt ℝ f x) : Asymptotics.IsLittleO (nhds x) (fun y => f y - f x - (LinearMap.toMatrix' (fderiv ℝ f x).toLinearMap).mulVec (y - x)) (fun y => y - x)",
    "  simpa only [LinearMap.toMatrix'_mulVec, ContinuousLinearMap.coe_coe] using hf.hasFDerivAt.isLittleO",
    [
        "Start from the remainder characterization of an actual Fréchet derivative.",
        "Represent its continuous linear map in the standard coordinate bases.",
        "Matrix multiplication by y−x is exactly derivative application to y−x.",
        "Substitute this identity into the little-o estimate without assuming a quadratic error bound.",
    ],
)
# Two-block C1 criterion: global partial derivative witnesses and joint continuity at the point.
ds = N("m", "n", "p") + [
    decl("f", "ProductFunction", "m", "n", "p"),
    decl("A", "LeftField", "m", "n", "p"),
    decl("B", "RightField", "m", "n", "p"),
    decl("x", "Vector", "m"),
    decl("y", "Vector", "n"),
]
left = bind(
    [decl("u", "Vector", "m"), decl("w", "Vector", "n")],
    a(
        "has_fderiv",
        M,
        p,
        a("product_slice_left", M, n, p, f, w),
        u,
        a("left_field_apply", M, n, p, A, u, w),
    ),
)
right = bind(
    [decl("u", "Vector", "m"), decl("w", "Vector", "n")],
    a(
        "has_fderiv",
        n,
        p,
        a("product_slice_right", M, n, p, f, u),
        w,
        a("right_field_apply", M, n, p, B, u, w),
    ),
)
add(
    "continuous_block_partials",
    ds,
    imp(
        left,
        right,
        a("continuous_left_field_at", M, n, p, A, x, y),
        a("continuous_right_field_at", M, n, p, B, x, y),
        a(
            "has_product_strict_fderiv",
            M,
            n,
            p,
            f,
            x,
            y,
            a(
                "coprod",
                M,
                n,
                p,
                a("left_field_apply", M, n, p, A, x, y),
                a("right_field_apply", M, n, p, B, x, y),
            ),
        ),
    ),
    "Let f:ℝᵐ×ℝⁿ→ℝᵖ have actual first-block derivative A(u,v) and second-block derivative B(u,v) at every (u,v). If both derivative fields are jointly continuous at (x,y), then f is strictly differentiable there with derivative (h,k)↦A(x,y)h+B(x,y)k.",
    "example (m n p : ℕ) (f : ((Fin m → ℝ) × (Fin n → ℝ)) → (Fin p → ℝ)) (A : ((Fin m → ℝ) × (Fin n → ℝ)) → ((Fin m → ℝ) →L[ℝ] (Fin p → ℝ))) (B : ((Fin m → ℝ) × (Fin n → ℝ)) → ((Fin n → ℝ) →L[ℝ] (Fin p → ℝ))) (x : Fin m → ℝ) (y : Fin n → ℝ) (hA : ∀ u v, HasFDerivAt (fun z => f (z,v)) (A (u,v)) u) (hB : ∀ u v, HasFDerivAt (fun z => f (u,z)) (B (u,v)) v) (cA : ContinuousAt A (x,y)) (cB : ContinuousAt B (x,y)) : HasStrictFDerivAt f ((A (x,y)).coprod (B (x,y))) (x,y)",
    "  exact hasStrictFDerivAt_uncurry_coprod (𝕜 := ℝ) (u := (x,y)) (f := fun u v => f (u,v)) (f₁ := fun u v => A (u,v)) (f₂ := fun u v => B (u,v)) (Filter.Eventually.of_forall (fun z => hA z.1 z.2)) (Filter.Eventually.of_forall (fun z => hB z.1 z.2)) cA cB",
    [
        "Use the global partial derivative witnesses to obtain the required neighborhood witnesses.",
        "Keep joint continuity of both derivative fields at the target point.",
        "Apply the two-block strict differentiability criterion.",
        "The resulting derivative is the coproduct of the block derivatives, not a conclusion from isolated partials.",
    ],
)
add(
    "smooth_derivative_field",
    N("n", "k") + [decl("f", "ScalarFunction", "n")],
    imp(
        a("scalar_cont_diff", n, st("arith1", "plus", k, "<OMI>1</OMI>"), f),
        a("field_cont_diff", n, k, a("scalar_fderiv_field", n, f)),
    ),
    "For every natural k and dimension n, a globally C^(k+1) scalar function on ℝⁿ has a globally C^k total derivative field, including k=0.",
    "example (n k : ℕ) (f : (Fin n → ℝ) → ℝ) (hf : ContDiff ℝ (k+1) f) : ContDiff ℝ k (fderiv ℝ f)",
    "  exact hf.fderiv_right (by simp)",
    [
        "Interpret the natural regularity order k+1 with its exact coercion.",
        "A derivative consumes one order of regularity.",
        "Apply the regularity theorem for the Fréchet derivative field.",
        "Retain k=0, where the conclusion is continuity of the derivative field.",
    ],
)
add(
    "quadratic_derivative",
    N("n") + [decl("B", "Bilinear", "n"), decl("x", "Vector", "n")],
    a(
        "has_scalar_fderiv",
        n,
        a("quadratic", n, B),
        x,
        a("quadratic_derivative", n, B, x),
    ),
    "For any continuous real bilinear form B on ℝⁿ, the derivative of x↦B(x,x) at x is h↦B(x,h)+B(h,x); no symmetry assumption is required.",
    "example (n : ℕ) (B : (Fin n → ℝ) →L[ℝ] (Fin n → ℝ) →L[ℝ] ℝ) (x : Fin n → ℝ) : HasFDerivAt (fun y => B y y) (B x + B.flip x) x",
    "  convert! B.hasFDerivAt_of_bilinear (hasFDerivAt_id x) (hasFDerivAt_id x) using 1",
    [
        "Express the quadratic function as a bilinear form applied to two identity maps.",
        "Differentiate both occurrences of the input.",
        "The two terms are B(x,h) and B(h,x).",
        "Keep their sum; replacing it by 2B(x,h) would require symmetry.",
    ],
)
add(
    "quadratic_hessian",
    N("n") + [decl("B", "Bilinear", "n"), decl("x", "Vector", "n")],
    a("has_field_derivative", n, a("quadratic_field", n, B), x, a("symmetrize", n, B)),
    "For any continuous bilinear B on ℝⁿ, the derivative of the quadratic derivative field x↦B x+B.flip x is the constant bilinear form B+B.flip. Thus the quadratic Hessian is the symmetrization, without a factor of one half.",
    "example (n : ℕ) (B : (Fin n → ℝ) →L[ℝ] (Fin n → ℝ) →L[ℝ] ℝ) (x : Fin n → ℝ) : HasFDerivAt (fun y => B y + B.flip y) (B + B.flip) x",
    "  exact B.hasFDerivAt.add B.flip.hasFDerivAt",
    [
        "Use the explicit first derivative field of the quadratic form.",
        "Both x↦B x and x↦B.flip x are continuous linear maps.",
        "Differentiate their sum to obtain B+B.flip.",
        "This bilinear second derivative is constant and symmetric by construction.",
    ],
)
add(
    "quadratic_taylor_exact",
    N("n")
    + [decl("B", "Bilinear", "n"), decl("x", "Vector", "n"), decl("h", "Vector", "n")],
    eq(
        a("bilinear_apply", n, B, a("add", n, x, h), a("add", n, x, h)),
        a(
            "real_add",
            a(
                "real_add",
                a("bilinear_apply", n, B, x, x),
                a("dual_apply", n, a("quadratic_derivative", n, B, x), h),
            ),
            a("bilinear_apply", n, B, h, h),
        ),
    ),
    "For any continuous bilinear B, base point x and increment h in ℝⁿ, B(x+h,x+h)=B(x,x)+(B x+B.flip x)(h)+B(h,h). This is an exact second-order expansion for arbitrary quadratic forms, not a Taylor formula for arbitrary smooth functions.",
    "example (n : ℕ) (B : (Fin n → ℝ) →L[ℝ] (Fin n → ℝ) →L[ℝ] ℝ) (x h : Fin n → ℝ) : B (x+h) (x+h) = B x x + (B x + B.flip x) h + B h h",
    "  simp only [map_add, add_apply, ContinuousLinearMap.flip_apply]\n  ring",
    [
        "Expand in both slots using bilinearity.",
        "Collect the constant term B(x,x).",
        "Collect the two linear terms as the derivative applied to h.",
        "The remaining B(h,h) is exactly quadratic, so no higher remainder occurs.",
    ],
)
# Lagrange: weak multipliers do not secretly assume a regular constraint.
lds = N("n") + [
    decl("f", "ScalarFunction", "n"),
    decl("g", "ScalarFunction", "n"),
    decl("A", "ScalarCLM", "n"),
    decl("B", "ScalarCLM", "n"),
    decl("x", "Vector", "n"),
]
prem = [
    a("local_extr_fiber", n, g, f, x),
    a("has_scalar_strict_fderiv", n, f, x, A),
    a("has_scalar_strict_fderiv", n, g, x, B),
]
add(
    "lagrange_abnormal_allowed",
    lds,
    imp(
        *prem,
        bind(
            [decl("a", "Real"), decl("b", "Real")],
            both(
                either(ne(aa, Z), ne(bb, Z)),
                eq(
                    a(
                        "dual_add",
                        n,
                        a("dual_scale", n, aa, A),
                        a("dual_scale", n, bb, B),
                    ),
                    a("dual_zero", n),
                ),
            ),
            "exists",
        ),
    ),
    "If g has a local extremum at x on the level set f=f(x), and scalar f,g are strictly differentiable at x with derivatives A,B, then there exist real a,b, not both zero, with aA+bB=0. The objective multiplier b is allowed to be zero without constraint regularity.",
    "example (n : ℕ) (f g : (Fin n → ℝ) → ℝ) (A B : (Fin n → ℝ) →L[ℝ] ℝ) (x : Fin n → ℝ) (he : IsLocalExtrOn g {y | f y = f x} x) (hf : HasStrictFDerivAt f A x) (hg : HasStrictFDerivAt g B x) : ∃ a b : ℝ, (a ≠ 0 ∨ b ≠ 0) ∧ a • A + b • B = 0",
    "  obtain ⟨a,b,hne,heq⟩ := he.exists_multipliers_of_hasStrictFDerivAt_1d hf hg\n  exact ⟨a,b,by simpa only [ne_eq, Prod.mk_eq_zero, not_and_or] using hne,heq⟩",
    [
        "Use the local extremum only on the constraint level set.",
        "Apply the strict-differentiability Lagrange theorem.",
        "Translate the nonzero pair condition into a≠0 or b≠0.",
        "Retain the possible abnormal case b=0; normalization is not yet justified.",
    ],
)
add(
    "lagrange_regular_constraint",
    lds,
    imp(
        *prem,
        ne(A, a("dual_zero", n)),
        bind([decl("lambda", "Real")], eq(B, a("dual_scale", n, lam, A)), "exists"),
    ),
    "If g has a local extremum on f=f(x), both scalar functions are strictly differentiable at x, and the constraint derivative A is nonzero, then the objective derivative B equals λA for some real λ.",
    "example (n : ℕ) (f g : (Fin n → ℝ) → ℝ) (A B : (Fin n → ℝ) →L[ℝ] ℝ) (x : Fin n → ℝ) (he : IsLocalExtrOn g {y | f y = f x} x) (hf : HasStrictFDerivAt f A x) (hg : HasStrictFDerivAt g B x) (hA : A ≠ 0) : ∃ c : ℝ, B = c • A",
    "  obtain ⟨a,b,hne,heq⟩ := he.exists_multipliers_of_hasStrictFDerivAt_1d hf hg\n  have hb : b ≠ 0 := by\n    intro hb\n    have haz : a • A = 0 := by simpa [hb] using heq\n    have ha : a = 0 := (smul_eq_zero.mp haz).resolve_right hA\n    exact hne (by simp [ha,hb])\n  refine ⟨-a / b, ?_⟩\n  ext v\n  have hh := congrArg (fun C : (Fin n → ℝ) →L[ℝ] ℝ => C v) heq\n  simp only [add_apply, smul_apply, smul_eq_mul, zero_apply] at hh ⊢\n  field_simp\n  nlinarith [hh]",
    [
        "Obtain a nonzero pair of weak Lagrange multipliers.",
        "If the objective multiplier vanished, nonzero A would force the other multiplier to vanish too.",
        "Thus divide by the objective multiplier and set λ=−a/b.",
        "Evaluate the functional equality on arbitrary vectors to obtain B=λA.",
    ],
)
fds = N("k", "n") + [
    decl("F", "FunctionFamily", "k", "n"),
    decl("D", "DualFamily", "k", "n"),
    decl("g", "ScalarFunction", "n"),
    decl("B", "ScalarCLM", "n"),
    decl("x", "Vector", "n"),
]
add(
    "lagrange_finite_constraints",
    fds,
    imp(
        a("local_extr_fibers", k, n, g, F, x),
        bind(
            [decl("i", "Index", "k")],
            a(
                "has_scalar_strict_fderiv",
                n,
                a("family_at", k, n, F, i),
                x,
                a("dual_family_at", k, n, D, i),
            ),
        ),
        a("has_scalar_strict_fderiv", n, g, x, B),
        bind(
            [decl("L", "Vector", "k"), decl("b", "Real")],
            both(
                either(ne(L, a("zero", k)), ne(bb, Z)),
                eq(
                    a(
                        "dual_add",
                        n,
                        a("weighted_dual_sum", k, n, L, D),
                        a("dual_scale", n, bb, B),
                    ),
                    a("dual_zero", n),
                ),
            ),
            "exists",
        ),
    ),
    "For any finite number k of scalar constraints on ℝⁿ, a constrained local extremum of a strictly differentiable objective, with all constraints strictly differentiable, yields multipliers (λ∈ℝᵏ,b∈ℝ) not both zero satisfying Σᵢ λᵢ Dᵢ+bB=0; no constraint independence is assumed.",
    "example (k n : ℕ) (F : Fin k → (Fin n → ℝ) → ℝ) (D : Fin k → (Fin n → ℝ) →L[ℝ] ℝ) (g : (Fin n → ℝ) → ℝ) (B : (Fin n → ℝ) →L[ℝ] ℝ) (x : Fin n → ℝ) (he : IsLocalExtrOn g {y | ∀ i, F i y = F i x} x) (hF : ∀ i, HasStrictFDerivAt (F i) (D i) x) (hg : HasStrictFDerivAt g B x) : ∃ (L : Fin k → ℝ) (b : ℝ), (L ≠ 0 ∨ b ≠ 0) ∧ (∑ i, L i • D i) + b • B = 0",
    "  obtain ⟨L,b,hne,heq⟩ := he.exists_multipliers_of_hasStrictFDerivAt hF hg\n  exact ⟨L,b,by simpa only [ne_eq, Prod.mk_eq_zero, not_and_or] using hne,heq⟩",
    [
        "Keep the entire finite family of level-set constraints.",
        "Use strict differentiability of every constraint and of the objective.",
        "Apply finite-family Lagrange multipliers to their derivative functionals.",
        "The multiplier vector and objective multiplier are jointly nonzero, without claiming either one individually is nonzero.",
    ],
)
# Fubini and product integrability: Lebesgue volumes and arbitrary finite dimensions.
ip = N("m", "n") + [decl("f", "ProductScalarFunction", "m", "n")]
integ = a("product_integrable", M, n, f)
rightint = a("integral", M, a("inner_integral_right", M, n, f))
leftint = a("integral", n, a("inner_integral_left", M, n, f))
leanip = "example (m n : ℕ) (f : ((Fin m → ℝ) × (Fin n → ℝ)) → ℝ)"
add(
    "fubini",
    ip,
    imp(integ, eq(a("product_integral", M, n, f), rightint)),
    "For any absolutely integrable real f on ℝᵐ×ℝⁿ with product Lebesgue measure, its multiple integral equals the iterated integral with the right block integrated first.",
    leanip + " (hf : MeasureTheory.Integrable f) : (∫ z, f z) = ∫ x, ∫ y, f (x,y)",
    "  exact MeasureTheory.integral_prod f hf",
    [
        "Assume actual product-measure integrability of f.",
        "Finite-dimensional Lebesgue volumes are sigma-finite.",
        "Apply Fubini to integrate the right block first.",
        "Do not infer integrability merely from a totalized iterated integral value.",
    ],
)
add(
    "fubini_order_exchange",
    ip,
    imp(integ, eq(rightint, leftint)),
    "For an absolutely integrable real f on ℝᵐ×ℝⁿ, the two orders of iterated Lebesgue integration agree.",
    leanip
    + " (hf : MeasureTheory.Integrable f) : (∫ x, ∫ y, f (x,y)) = ∫ y, ∫ x, f (x,y)",
    "  exact MeasureTheory.integral_integral_swap hf",
    [
        "Retain absolute integrability on the product space.",
        "View f as the uncurrying of its two-variable form.",
        "Use Fubini in both orders.",
        "The common product integral identifies the two iterated integrals.",
    ],
)
sp = N("m", "n") + [decl("f", "ScalarFunction", "m"), decl("g", "ScalarFunction", "n")]
sep = a("product_separable", M, n, f, g)
add(
    "separable_product_integral",
    sp,
    imp(
        a("integrable", M, f),
        a("integrable", n, g),
        eq(
            a("product_integral", M, n, sep),
            a("real_mul", a("integral", M, f), a("integral", n, g)),
        ),
    ),
    "For integrable real f on ℝᵐ and g on ℝⁿ, the integral of (x,y)↦f(x)g(y) equals (∫f)(∫g).",
    "example (m n : ℕ) (f : (Fin m → ℝ) → ℝ) (g : (Fin n → ℝ) → ℝ) (_hf : MeasureTheory.Integrable f) (_hg : MeasureTheory.Integrable g) : (∫ z : (Fin m → ℝ) × (Fin n → ℝ), f z.1 * g z.2) = (∫ x, f x) * (∫ y, g y)",
    "  exact MeasureTheory.integral_prod_mul f g",
    [
        "Identify the integrand as a separated product.",
        "The hypotheses give genuine integrability of both factors.",
        "Use the product-integral factorization theorem.",
        "Keep both factor integrals with their own coordinate-space measures.",
    ],
)
add(
    "separable_product_integrable",
    sp,
    imp(
        a("integrable", M, f), a("integrable", n, g), a("product_integrable", M, n, sep)
    ),
    "The separated product (x,y)↦f(x)g(y) is integrable on ℝᵐ×ℝⁿ whenever both real factors are integrable on their respective spaces.",
    "example (m n : ℕ) (f : (Fin m → ℝ) → ℝ) (g : (Fin n → ℝ) → ℝ) (hf : MeasureTheory.Integrable f) (hg : MeasureTheory.Integrable g) : MeasureTheory.Integrable (fun z : (Fin m → ℝ) × (Fin n → ℝ) => f z.1 * g z.2)",
    "  exact hf.mul_prod hg",
    [
        "Use absolute integrability of each factor separately.",
        "The product-measure norm integral factors into their finite norm integrals.",
        "Apply integrability of separated products.",
        "This proves existence of the multiple integral, independently of its evaluation.",
    ],
)
add(
    "fubini_rectangular_domain",
    ip + [decl("s", "Set", "m"), decl("t", "Set", "n")],
    imp(
        a("product_integrable_on", M, n, f, v("s"), t),
        eq(
            a("product_set_integral", M, n, f, v("s"), t),
            a("set_integral", M, a("inner_set_integral_right", M, n, f, t), v("s")),
        ),
    ),
    "If f is integrable on a Cartesian domain s×t⊆ℝᵐ×ℝⁿ, its integral over that domain equals ∫ₛ∫ₜ f(x,y). The integrability hypothesis uses restricted Lebesgue measures.",
    leanip
    + " (s : Set (Fin m → ℝ)) (t : Set (Fin n → ℝ)) (hf : MeasureTheory.IntegrableOn f (s ×ˢ t)) : (∫ z in s ×ˢ t, f z) = ∫ x in s, ∫ y in t, f (x,y)",
    "  exact MeasureTheory.setIntegral_prod f hf",
    [
        "Restrict the two Lebesgue measures to the Cartesian factors.",
        "Use the assumed integrability on s×t.",
        "Apply the set-integral version of Fubini.",
        "Both iterated limits refer to their original domain factors.",
    ],
)
add(
    "almost_every_section_integrable",
    ip,
    imp(integ, a("ae_right_sections_integrable", M, n, f)),
    "An integrable real function on ℝᵐ×ℝⁿ has an integrable right-block section y↦f(x,y) for almost every x. This does not assert integrability for every x.",
    leanip
    + " (hf : MeasureTheory.Integrable f) : ∀ᵐ x, MeasureTheory.Integrable (fun y => f (x,y))",
    "  exact hf.prod_right_ae",
    [
        "Begin with integrability for product Lebesgue measure.",
        "Apply the almost-everywhere section theorem.",
        "Keep the exceptional null set in the conclusion.",
        "Do not replace the almost-everywhere quantifier by a universal one.",
    ],
)
add(
    "inner_integral_integrable",
    ip,
    imp(integ, a("integrable", M, a("inner_integral_right", M, n, f))),
    "For integrable f on ℝᵐ×ℝⁿ, the function x↦∫y f(x,y) is integrable on ℝᵐ.",
    leanip
    + " (hf : MeasureTheory.Integrable f) : MeasureTheory.Integrable (fun x => ∫ y, f (x,y))",
    "  exact hf.integral_prod_left",
    [
        "Use the product integrability hypothesis to control sections.",
        "The inner integral is measurable up to null sets.",
        "Its norm is bounded by the inner integral of the norm.",
        "Apply the integrable-inner-integral consequence of Fubini.",
    ],
)
add(
    "absolute_section_criterion",
    ip,
    imp(
        a("product_ae_strongly_measurable", M, n, f),
        iff(
            integ,
            both(
                a("ae_right_sections_integrable", M, n, f),
                a("integrable", M, a("inner_abs_integral", M, n, f)),
            ),
        ),
    ),
    "For product-a.e. strongly measurable real f on ℝᵐ×ℝⁿ, product integrability is equivalent to almost every right section being integrable and x↦∫y |f(x,y)| being integrable. Signed iterated integrals alone are insufficient.",
    leanip
    + " (hf : MeasureTheory.AEStronglyMeasurable f) : MeasureTheory.Integrable f ↔ (∀ᵐ x, MeasureTheory.Integrable (fun y => f (x,y))) ∧ MeasureTheory.Integrable (fun x => ∫ y, ‖f (x,y)‖)",
    "  exact MeasureTheory.integrable_prod_iff hf",
    [
        "Assume the required product a.e. strong measurability.",
        "Apply the product-integrability criterion.",
        "Retain both almost-everywhere section integrability and outer integrability of x ↦ ∫ y, |f(x,y)|.",
        "This avoids confusing cancellation in signed sections with absolute integrability.",
    ],
)
np = N("n") + [decl("F", "RealFunctionFamily", "n")]
nprem = bind(
    [decl("i", "Index", "n")], a("real_integrable", a("real_family_at", n, F, i))
)
add(
    "finite_separated_product_integral",
    np,
    imp(
        nprem,
        eq(
            a("integral", n, a("separable_n_product", n, F)),
            a("product_real_integrals", n, F),
        ),
    ),
    "For any natural n and integrable family fᵢ:ℝ→ℝ indexed by Fin n, ∫ℝⁿ Πᵢ fᵢ(xᵢ)=Πᵢ∫ℝ fᵢ. The zero-dimensional case uses the empty product 1 and the singleton product volume.",
    "example (n : ℕ) (F : Fin n → ℝ → ℝ) (_hF : ∀ i, MeasureTheory.Integrable (F i)) : (∫ x : Fin n → ℝ, ∏ i, F i (x i)) = ∏ i, ∫ t : ℝ, F i t",
    "  exact MeasureTheory.integral_fin_nat_prod_volume_eq_prod F",
    [
        "Use a finite family indexed by the arbitrary natural dimension.",
        "Iterate separated-product Fubini across the coordinates.",
        "Factor the n-dimensional integral into one-dimensional integrals.",
        "Include n=0 with the correct empty product and zero-dimensional measure.",
    ],
)
add(
    "finite_separated_product_integrable",
    np,
    imp(nprem, a("integrable", n, a("separable_n_product", n, F))),
    "For every natural n, integrability of each real one-variable factor fᵢ implies integrability of x↦Πᵢfᵢ(xᵢ) on ℝⁿ, including n=0.",
    "example (n : ℕ) (F : Fin n → ℝ → ℝ) (hF : ∀ i, MeasureTheory.Integrable (F i)) : MeasureTheory.Integrable (fun x : Fin n → ℝ => ∏ i, F i (x i))",
    "  exact MeasureTheory.Integrable.fintype_prod hF",
    [
        "Each factor has finite integral of its absolute value.",
        "Finite product Lebesgue measure is the coordinate product measure.",
        "Apply integrability of finite separated products.",
        "The empty finite product remains integrable in dimension zero.",
    ],
)
# Change of variables on arbitrary measurable domains, using within-set derivative witnesses.
cvds = N("n") + [
    decl("f", "Function", "n", "n"),
    decl("D", "DerivativeField", "n", "n"),
    decl("s", "Set", "n"),
]
cvprem = [
    a("measurable_set", n, v("s")),
    bind(
        [decl("x", "Vector", "n")],
        imp(
            a("member", n, x, v("s")),
            a("has_fderiv_within", n, f, x, v("s"), a("field_apply", n, n, D, x)),
        ),
    ),
    a("injective_on", n, f, v("s")),
]
img = a("image", n, f, v("s"))
weight = a("jacobian_weighted", n, f, D, g)
cvlean = "example (n : ℕ) (f : (Fin n → ℝ) → (Fin n → ℝ)) (D : (Fin n → ℝ) → ((Fin n → ℝ) →L[ℝ] (Fin n → ℝ))) (s : Set (Fin n → ℝ)) (hs : MeasurableSet s) (hD : ∀ x ∈ s, HasFDerivWithinAt f (D x) s x) (hi : Set.InjOn f s)"
add(
    "jacobian_change_variables",
    cvds + [decl("g", "ScalarFunction", "n")],
    imp(
        *cvprem,
        a("integrable_on", n, g, img),
        eq(a("set_integral", n, g, img), a("set_integral", n, weight, v("s"))),
    ),
    "Let f:ℝⁿ→ℝⁿ be injective on a measurable set s, with actual within-s derivatives D(x) for every x∈s. If real g is integrable on f(s), then ∫f(s) g = ∫s |det D(x)| g(f(x)). Neither openness of s nor everywhere nonzero determinant is assumed.",
    cvlean
    + " (g : (Fin n → ℝ) → ℝ) (_hg : MeasureTheory.IntegrableOn g (f '' s)) : (∫ y in f '' s, g y) = ∫ x in s, |(D x).det| * g (f x)",
    "  simpa only [smul_eq_mul] using MeasureTheory.integral_image_eq_integral_abs_det_fderiv_smul MeasureTheory.volume hs hD hi g",
    [
        "Keep measurability, within-set derivative witnesses, and injectivity on s.",
        "Use the image domain f(s) for the target integral.",
        "Apply the finite-dimensional Jacobian substitution theorem for Lebesgue volume.",
        "The measure scaling is the absolute determinant, preserving orientation-independent volume.",
    ],
)
add(
    "jacobian_integrability_equivalence",
    cvds + [decl("g", "ScalarFunction", "n")],
    imp(
        *cvprem,
        iff(a("integrable_on", n, g, img), a("integrable_on", n, weight, v("s"))),
    ),
    "Under measurable-domain, within-derivative and injectivity-on-domain hypotheses, real g is integrable on f(s) exactly when x↦|det D(x)|g(f(x)) is integrable on s.",
    cvlean
    + " (g : (Fin n → ℝ) → ℝ) : MeasureTheory.IntegrableOn g (f '' s) ↔ MeasureTheory.IntegrableOn (fun x => |(D x).det| * g (f x)) s",
    "  simpa only [smul_eq_mul] using MeasureTheory.integrableOn_image_iff_integrableOn_abs_det_fderiv_smul MeasureTheory.volume hs hD hi g",
    [
        "Use the same measurable injective transformation and actual derivative field.",
        "Transform the restricted volume using its absolute determinant density.",
        "Apply the integrability equivalence rather than reasoning from equal totalized integral values.",
        "Retain both directions of the existence criterion.",
    ],
)
add(
    "differentiable_injective_image_measurable",
    cvds,
    imp(*cvprem, a("measurable_set", n, img)),
    "The image f(s) of a measurable subset s⊆ℝⁿ is measurable when f is injective on s and has an actual Fréchet derivative within s at every point of s.",
    cvlean + " : MeasurableSet (f '' s)",
    "  exact MeasureTheory.measurable_image_of_fderivWithin hs hD hi",
    [
        "Retain the full within-set differentiability hypothesis on every domain point.",
        "Use injectivity only on the measurable domain.",
        "Apply the measurable-image theorem for differentiable injective maps.",
        "This supplies an essential domain fact for change of variables; arbitrary measurable images are not asserted.",
    ],
)
# Line integration of exact one-forms along arbitrary differentiable curves.
pathds = N("n") + [
    decl("f", "ScalarFunction", "n"),
    decl("D", "ScalarDerivativeField", "n"),
    decl("c", "Curve", "n"),
    decl("u", "Curve", "n"),
    decl("a", "Real"),
    decl("b", "Real"),
]
dfield = bind(
    [decl("x", "Vector", "n")],
    a("has_scalar_fderiv", n, f, x, a("scalar_field_apply", n, D, x)),
)


def curve_h(curve, vel):
    return bind(
        [decl("t", "Real")],
        imp(
            a("in_uIcc", t, aa, bb),
            a("has_curve_deriv", n, curve, t, a("curve_apply", n, vel, t)),
        ),
    )


def pull(curve, vel):
    return a("pullback_one_form", n, D, curve, vel)


pathprem = [dfield, curve_h(c, u), a("interval_integrable", pull(c, u), aa, bb)]
pathlean = "example (n : ℕ) (f : (Fin n → ℝ) → ℝ) (D : (Fin n → ℝ) → ((Fin n → ℝ) →L[ℝ] ℝ)) (c u : ℝ → (Fin n → ℝ)) (a b : ℝ) (hD : ∀ x, HasFDerivAt f (D x) x) (hc : ∀ t ∈ Set.uIcc a b, HasDerivAt c (u t) t) (hi : IntervalIntegrable (fun t => D (c t) (u t)) MeasureTheory.volume a b)"
add(
    "potential_line_integral",
    pathds,
    imp(
        *pathprem,
        eq(
            a("interval_integral", pull(c, u), aa, bb),
            a(
                "real_sub",
                a("scalar_apply", n, f, a("curve_apply", n, c, bb)),
                a("scalar_apply", n, f, a("curve_apply", n, c, aa)),
            ),
        ),
    ),
    "Let D be an actual derivative field of a scalar potential f on ℝⁿ. Along a curve c with velocity u on uIcc(a,b), if t↦D(c(t))u(t) is interval-integrable, its oriented integral from a to b equals f(c(b))−f(c(a)). Both orientations and equal endpoints are permitted.",
    pathlean + " : (∫ t in a..b, D (c t) (u t)) = f (c b) - f (c a)",
    "  apply intervalIntegral.integral_eq_sub_of_hasDerivAt _ hi\n  intro t ht\n  exact (hD (c t)).comp_hasDerivAt t (hc t ht)",
    [
        "Compose the actual derivative of f with the actual velocity of c.",
        "Obtain the derivative of the scalar function t↦f(c(t)) on the unordered closed interval.",
        "Use the stipulated interval integrability of the pullback one-form.",
        "Apply the oriented fundamental theorem of calculus to obtain the endpoint difference.",
    ],
)
add(
    "potential_path_independence",
    pathds + [decl("d", "Curve", "n"), decl("w", "Curve", "n")],
    imp(
        *pathprem,
        curve_h(d, w),
        a("interval_integrable", pull(d, w), aa, bb),
        eq(a("curve_apply", n, c, aa), a("curve_apply", n, d, aa)),
        eq(a("curve_apply", n, c, bb), a("curve_apply", n, d, bb)),
        eq(
            a("interval_integral", pull(c, u), aa, bb),
            a("interval_integral", pull(d, w), aa, bb),
        ),
    ),
    "Two differentiable curves in ℝⁿ with the same starting and ending points give the same line integral of an exact one-form D=df, provided both pullbacks are interval-integrable. No conclusion is asserted for an arbitrary non-exact field.",
    pathlean
    + " (d w : ℝ → (Fin n → ℝ)) (hd : ∀ t ∈ Set.uIcc a b, HasDerivAt d (w t) t) (hj : IntervalIntegrable (fun t => D (d t) (w t)) MeasureTheory.volume a b) (ha : c a = d a) (hb : c b = d b) : (∫ t in a..b, D (c t) (u t)) = ∫ t in a..b, D (d t) (w t)",
    "  have h1 : (∫ t in a..b, D (c t) (u t)) = f (c b) - f (c a) := intervalIntegral.integral_eq_sub_of_hasDerivAt (fun t ht => (hD (c t)).comp_hasDerivAt t (hc t ht)) hi\n  have h2 : (∫ t in a..b, D (d t) (w t)) = f (d b) - f (d a) := intervalIntegral.integral_eq_sub_of_hasDerivAt (fun t ht => (hD (d t)).comp_hasDerivAt t (hd t ht)) hj\n  rw [h1,h2,ha,hb]",
    [
        "The field is the derivative of one common globally defined potential.",
        "Apply the line-integral fundamental theorem to each curve.",
        "Both integrals become differences of potential values at their endpoints.",
        "Use the matching endpoint hypotheses to identify these differences.",
    ],
)

# An actual parameterized counterexample card, not just a hard-negative annotation.
jump = a("axis_jump", M, n, i, j, aa)
add(
    "partials_without_continuity",
    N("m", "n") + [decl("i", "Index", "m"), decl("j", "Index", "n"), decl("a", "Real")],
    imp(
        ne(aa, Z),
        both(
            a(
                "has_scalar_fderiv",
                M,
                a("product_scalar_slice_left", M, n, jump, a("zero", n)),
                a("zero", M),
                a("dual_zero", M),
            ),
            both(
                a(
                    "has_scalar_fderiv",
                    n,
                    a("product_scalar_slice_right", M, n, jump, a("zero", M)),
                    a("zero", n),
                    a("dual_zero", n),
                ),
                neg(a("product_continuous_at", M, n, jump, a("zero", M), a("zero", n))),
            ),
        ),
    ),
    "For all coordinate dimensions m,n with chosen coordinates i,j and every nonzero real a, define f(x,y)=0 when xᵢ=0 or yⱼ=0, and a otherwise. Both block partial derivatives at the origin exist and are zero, yet f is not continuous there. Thus isolated partial derivatives cannot establish total differentiability.",
    "example (m n : ℕ) (i : Fin m) (j : Fin n) (a : ℝ) (ha : a ≠ 0) :\n let f : ((Fin m → ℝ) × (Fin n → ℝ)) → ℝ := fun z => if z.1 i = 0 ∨ z.2 j = 0 then 0 else a\n HasFDerivAt (fun x => f (x, 0)) (0 : (Fin m → ℝ) →L[ℝ] ℝ) 0 ∧ HasFDerivAt (fun y => f (0, y)) (0 : (Fin n → ℝ) →L[ℝ] ℝ) 0 ∧ ¬ ContinuousAt f (0, 0)",
    " dsimp only\n constructor\n · simpa using (hasFDerivAt_const (𝕜 := ℝ) (0 : ℝ) (0 : Fin m → ℝ))\n constructor\n · simpa using (hasFDerivAt_const (𝕜 := ℝ) (0 : ℝ) (0 : Fin n → ℝ))\n intro hc\n have ha' : 0 < |a| := abs_pos.mpr ha\n obtain ⟨δ, hδ, hh⟩ := Metric.continuousAt_iff.mp hc (|a| / 2) (by positivity)\n let x : Fin m → ℝ := fun _ => δ / 2\n let y : Fin n → ℝ := fun _ => δ / 2\n have hxy : dist (x,y) (0,0) < δ := by\n   rw [Prod.dist_eq, max_lt_iff]\n   constructor <;> apply (dist_pi_lt_iff hδ).mpr <;> intro k <;> simp [x,y,abs_of_pos hδ] <;> linarith\n have hz := hh hxy\n simp only [x, y, Pi.zero_apply] at hz\n have hn : δ / 2 ≠ 0 := ne_of_gt (by positivity)\n simp only [hn, false_or, ↓reduceIte, true_or, dist_zero_right, Real.norm_eq_abs] at hz\n linarith",
    [
        "On each block axis the other selected coordinate is zero, so the restricted function is identically zero.",
        "Both block derivatives therefore exist and are zero.",
        "If the full function were continuous, values sufficiently close to the origin would have absolute value below |a|/2.",
        "Choose both coordinate blocks equal to a small nonzero constant vector: the point is arbitrarily close, but the function value is a, contradicting the bound.",
    ],
)


def main():
    witness_path = ROOT / "docs/multivariable-v5-batch.lean"
    witness = (
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
    witness_path.write_text(witness)
    result = subprocess.run(
        ["lake", "env", "lean", str(witness_path)],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    print(result.stdout + result.stderr, end="")
    if result.returncode:
        raise SystemExit(result.returncode)
    sha = lambda p: "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()
    mathlib = next(
        p["rev"]
        for p in json.loads((WORKSPACE / "lake-manifest.json").read_text())["packages"]
        if p["name"] == "mathlib"
    )
    evidence = {
        "witness_path": "docs/multivariable-v5-batch.lean",
        "witness_sha256": sha(witness_path),
        "validator_sha256": sha(
            ROOT / "pals-agent/pals_agent/typed_multivariable_v5.py"
        ),
        "registry_sha256": sha(
            ROOT
            / "pals-agent/pals_agent/content_dictionaries/typed-multivariable-v5-registry.json"
        ),
        "toolchain": (WORKSPACE / "lean-toolchain").read_text().strip(),
        "mathlib_revision": mathlib,
    }
    payload = {
        "schema_version": "pals.typed-catalog-expansion-batch.v1",
        "profile_id": "typed-multivariable-v5",
        "cards": cards,
        "evidence": evidence,
    }
    (ROOT / "docs/multivariable-v5-batch.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    )
    print(f"Compiled and emitted {len(cards)} general multivariable cards.")


if __name__ == "__main__":
    main()
