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
    cards = []

    def add(key, statement, ds, body, args, target, proof, steps):
        xml = canonicalize(
            '<OMOBJ xmlns="http://www.openmath.org/OpenMath" version="2.0">'
            + quant(SPACE + ds, body)
            + "</OMOBJ>"
        )
        validate(xml)
        cards.append(
            {
                "id": "la_v3_" + key,
                "canonical_statement": "Let V be any finite-dimensional real inner product space. "
                + statement,
                "proof_strategy": steps[0],
                "sketch_steps": steps,
                "openmath_xml": xml,
                "lean_target": LEAN + args + " : " + target,
                "lean_witness": "by\n  " + proof.replace("\n", "\n  "),
            }
        )

    add(
        "inner_self",
        "For every x, ⟨x,x⟩ = ‖x‖².",
        XY[:1],
        eq(inner(x, x), sq(norm(x))),
        "(x : V)",
        "inner ℝ x x = ‖x‖ ^ 2",
        "exact real_inner_self_eq_norm_sq x",
        [
            "Use compatibility of the norm and inner product.",
            "The real part of a real inner product is itself.",
            "Replace the product of the two equal norms by its square.",
            "Conclude the identity for every vector, including zero.",
        ],
    )
    add(
        "cauchy_schwarz",
        "For all x,y, |⟨x,y⟩| ≤ ‖x‖‖y‖.",
        XY,
        le(op("real_abs", inner(x, y)), op("real_mul", norm(x), norm(y))),
        "(x y : V)",
        "|inner ℝ x y| ≤ ‖x‖ * ‖y‖",
        "exact abs_real_inner_le_norm x y",
        [
            "Use the inner-product Cauchy–Schwarz inequality.",
            "Identify the scalar norm on ℝ with absolute value.",
            "Keep both vector norms as nonnegative real factors.",
            "The resulting inequality applies without a nonzero hypothesis.",
        ],
    )
    add(
        "pythagorean_iff",
        "For all x,y, ‖x+y‖² = ‖x‖²+‖y‖² iff ⟨x,y⟩=0.",
        XY,
        iff(
            eq(sq(norm(va(x, y))), plus(sq(norm(x)), sq(norm(y)))),
            eq(inner(x, y), real(0)),
        ),
        "(x y : V)",
        "‖x + y‖ ^ 2 = ‖x‖ ^ 2 + ‖y‖ ^ 2 ↔ inner ℝ x y = 0",
        "simpa only [pow_two] using norm_add_sq_eq_norm_sq_add_norm_sq_iff_real_inner_eq_zero x y",
        [
            "Expand the squared norm of a sum.",
            "The additional term is twice the real inner product.",
            "Equality of the squared norms forces that cross term to vanish.",
            "Conversely, orthogonality removes the cross term.",
        ],
    )
    add(
        "parallelogram",
        "For all x,y, ‖x+y‖²+‖x-y‖² = 2(‖x‖²+‖y‖²).",
        XY,
        eq(
            plus(sq(norm(va(x, y))), sq(norm(vs(x, y)))),
            op("real_mul", real(2), plus(sq(norm(x)), sq(norm(y)))),
        ),
        "(x y : V)",
        "‖x + y‖ ^ 2 + ‖x - y‖ ^ 2 = 2 * (‖x‖ ^ 2 + ‖y‖ ^ 2)",
        "exact parallelogram_law_with_norm ℝ x y",
        [
            "Expand the squared norm of the sum.",
            "Expand the squared norm of the difference.",
            "Add the expansions so the inner-product terms cancel.",
            "Collect two copies of each squared norm.",
        ],
    )
    add(
        "polarization",
        "For all x,y, 4⟨x,y⟩ = ‖x+y‖²-‖x-y‖².",
        XY,
        eq(
            op("real_mul", real(4), inner(x, y)),
            op("real_sub", sq(norm(va(x, y))), sq(norm(vs(x, y)))),
        ),
        "(x y : V)",
        "4 * inner ℝ x y = ‖x + y‖ ^ 2 - ‖x - y‖ ^ 2",
        "nlinarith [norm_add_sq_real x y, norm_sub_sq_real x y]",
        [
            "Expand both squared norms over ℝ.",
            "Subtract the difference expansion from the sum expansion.",
            "Cancel the squared norms of x and y.",
            "The remaining cross terms give four times the inner product.",
        ],
    )
    add(
        "orthogonal_independent",
        "Every pairwise orthogonal family v indexed by Fin n whose vectors are all nonzero is linearly independent.",
        NF,
        imp(
            conj(fam("family_nonzero", v), fam("orthogonal_family", v)),
            fam("independent", v),
        ),
        "{n : ℕ} (v : Fin n → V) (hz : ∀ i, v i ≠ 0) (ho : Pairwise (fun i j => inner ℝ (v i) (v j) = 0))",
        "LinearIndependent ℝ v",
        "exact linearIndependent_of_ne_zero_of_inner_eq_zero hz ho",
        [
            "Take a finite linear relation among the family.",
            "Pair the relation with each chosen family vector.",
            "Orthogonality kills all terms except its own coefficient times its positive squared norm.",
            "Nonzero norms force every coefficient to be zero.",
        ],
    )
    add(
        "bessel",
        "For every orthonormal Fin n family v and every x, ∑ᵢ⟨vᵢ,x⟩² ≤ ‖x‖².",
        NF + XY[:1],
        imp(fam("orthonormal", v), le(op("sum_squares", n, coeff(v, x)), sq(norm(x)))),
        "{n : ℕ} (v : Fin n → V) (hv : Orthonormal ℝ v) (x : V)",
        "∑ i, (inner ℝ (v i) x) ^ 2 ≤ ‖x‖ ^ 2",
        "simpa using hv.sum_inner_products_le (s := Finset.univ) x",
        [
            "Subtract the finite sum of orthonormal coefficients from x.",
            "Expand the squared norm of this residual.",
            "Orthonormality identifies it with ‖x‖² minus the sum of coefficient squares.",
            "Use nonnegativity of the residual squared norm.",
        ],
    )
    add(
        "complement_antitone",
        "If S ≤ T, then T⊥ ≤ S⊥.",
        SUBS,
        imp(op("sub_le", V, S, T), op("sub_le", V, orth(T), orth(S))),
        "(S T : Submodule ℝ V) (h : S ≤ T)",
        "Tᗮ ≤ Sᗮ",
        "exact Submodule.orthogonal_le h",
        [
            "Take a vector orthogonal to T.",
            "Every vector of S belongs to T by the inclusion.",
            "Its inner product with every vector of S therefore vanishes.",
            "This is membership in S⊥.",
        ],
    )
    add(
        "double_complement",
        "For every subspace S, (S⊥)⊥ = S.",
        SUB,
        eq(orth(orth(S)), S),
        "(S : Submodule ℝ V)",
        "Sᗮᗮ = S",
        "exact S.orthogonal_orthogonal",
        [
            "Finite dimension ensures that S admits an orthogonal projection.",
            "Decompose an arbitrary vector into its S and S⊥ components.",
            "For a vector in (S⊥)⊥, its S⊥ component must vanish.",
            "Combine this inclusion with S ≤ (S⊥)⊥.",
        ],
    )
    add(
        "complement_sum",
        "For all subspaces S,T, (S+T)⊥ = S⊥ ∩ T⊥.",
        SUBS,
        eq(orth(op("sub_sup", V, S, T)), op("sub_inf", V, orth(S), orth(T))),
        "(S T : Submodule ℝ V)",
        "(S ⊔ T)ᗮ = Sᗮ ⊓ Tᗮ",
        "exact (Submodule.inf_orthogonal S T).symm",
        [
            "Orthogonality to the sum implies orthogonality to each summand.",
            "Conversely take a vector orthogonal to both summands.",
            "Linearity makes its inner product vanish on sums of vectors from S and T.",
            "The two membership implications identify the subspaces.",
        ],
    )
    add(
        "complement_dimension",
        "For every S, dim S + dim S⊥ = dim V.",
        SUB,
        eq(plus(op("sub_dim", V, S), op("sub_dim", V, orth(S))), op("dim", V)),
        "(S : Submodule ℝ V)",
        "Module.finrank ℝ S + Module.finrank ℝ Sᗮ = Module.finrank ℝ V",
        "exact S.finrank_add_finrank_orthogonal",
        [
            "Use the orthogonal decomposition V = S ⊕ S⊥.",
            "Both summands are finite-dimensional.",
            "Apply dimension additivity to the direct sum.",
            "Identify the dimension of the sum with dim V.",
        ],
    )
    add(
        "orthogonal_direct_sum",
        "Every S satisfies S+S⊥=V and S∩S⊥={0}.",
        SUB,
        conj(
            eq(op("sub_sup", V, S, orth(S)), op("sub_top", V)),
            eq(op("sub_inf", V, S, orth(S)), op("sub_bot", V)),
        ),
        "(S : Submodule ℝ V)",
        "S ⊔ Sᗮ = ⊤ ∧ S ⊓ Sᗮ = ⊥",
        "exact ⟨S.sup_orthogonal_of_hasOrthogonalProjection, S.inf_orthogonal_eq_bot⟩",
        [
            "Split each vector using its orthogonal projection onto S.",
            "The residual lies in S⊥, proving the sum is all of V.",
            "A vector in the intersection is orthogonal to itself.",
            "Its squared norm is zero, so the intersection is the zero subspace.",
        ],
    )
    add(
        "projection_decomposition",
        "For every S,x, P_S x ∈ S and x-P_S x ∈ S⊥.",
        SUB + XY[:1],
        conj(mem(proj(S, x), S), mem(vs(x, proj(S, x)), orth(S))),
        "(S : Submodule ℝ V) (x : V)",
        "S.starProjection x ∈ S ∧ x - S.starProjection x ∈ Sᗮ",
        "exact ⟨S.starProjection_apply_mem x, S.sub_starProjection_mem_orthogonal x⟩",
        [
            "Construct the orthogonal projection using finite-dimensional completeness.",
            "Its image is a vector of S.",
            "The defining orthogonality condition makes the residual orthogonal to every vector of S.",
            "Package image membership and residual membership together.",
        ],
    )
    add(
        "projection_unique",
        "If y∈S and x-y∈S⊥, then P_S x=y.",
        SUB + XY,
        imp(conj(mem(y, S), mem(vs(x, y), orth(S))), eq(proj(S, x), y)),
        "(S : Submodule ℝ V) (x y : V) (hy : y ∈ S) (ho : x-y ∈ Sᗮ)",
        "S.starProjection x = y",
        "exact S.eq_starProjection_of_mem_orthogonal hy ho",
        [
            "Compare y with the orthogonal projection of x.",
            "Their difference lies in S because both points lie in S.",
            "The difference also lies in S⊥ by subtracting the residuals.",
            "The orthogonal intersection is zero, so the two points coincide.",
        ],
    )
    add(
        "projection_fixed_iff",
        "For every S,x, P_S x=x iff x∈S.",
        SUB + XY[:1],
        iff(eq(proj(S, x), x), mem(x, S)),
        "(S : Submodule ℝ V) (x : V)",
        "S.starProjection x = x ↔ x ∈ S",
        "exact S.starProjection_eq_self_iff",
        [
            "A fixed vector lies in the range of the projection, hence in S.",
            "For x∈S, choose x as its own projected point.",
            "Its residual is zero, which belongs to S⊥.",
            "Uniqueness gives P_S x=x and completes the converse.",
        ],
    )
    add(
        "projection_idempotent",
        "For every S,x, P_S(P_S x)=P_S x.",
        SUB + XY[:1],
        eq(proj(S, proj(S, x)), proj(S, x)),
        "(S : Submodule ℝ V) (x : V)",
        "S.starProjection (S.starProjection x) = S.starProjection x",
        "exact S.starProjection_eq_self_iff.mpr (S.starProjection_apply_mem x)",
        [
            "The first projection lands in S.",
            "Every vector in S is fixed by projection onto S.",
            "Apply that fixed-vector characterization to P_S x.",
            "This gives idempotence pointwise.",
        ],
    )
    add(
        "projection_zero_iff",
        "For every S,x, P_S x=0 iff x∈S⊥.",
        SUB + XY[:1],
        iff(eq(proj(S, x), op("vector_zero", V)), mem(x, orth(S))),
        "(S : Submodule ℝ V) (x : V)",
        "S.starProjection x = 0 ↔ x ∈ Sᗮ",
        "change x ∈ S.starProjection.ker ↔ x ∈ Sᗮ\nrw [Submodule.ker_starProjection]",
        [
            "The kernel consists exactly of vectors whose projection vanishes.",
            "A vector orthogonal to S has zero as its unique projected point.",
            "Conversely a zero projection makes x equal to its orthogonal residual.",
            "Identify kernel membership with membership in S⊥.",
        ],
    )
    add(
        "projection_contractive",
        "For every S,x, ‖P_S x‖ ≤ ‖x‖.",
        SUB + XY[:1],
        le(norm(proj(S, x)), norm(x)),
        "(S : Submodule ℝ V) (x : V)",
        "‖S.starProjection x‖ ≤ ‖x‖",
        "exact S.norm_starProjection_apply_le x",
        [
            "Decompose x into its projected part and orthogonal residual.",
            "The Pythagorean identity adds their squared norms.",
            "Discard the nonnegative squared residual norm.",
            "Nonnegativity of norms converts the squared inequality into the norm inequality.",
        ],
    )
    add(
        "projection_complement",
        "For every S,x, P_(S⊥) x=x-P_S x.",
        SUB + XY[:1],
        eq(proj(orth(S), x), vs(x, proj(S, x))),
        "(S : Submodule ℝ V) (x : V)",
        "Sᗮ.starProjection x = x - S.starProjection x",
        "exact S.starProjection_orthogonal_val x",
        [
            "The residual from projecting onto S lies in S⊥.",
            "The complementary residual is P_S x, which lies in (S⊥)⊥.",
            "Apply the uniqueness characterization of projection onto S⊥.",
            "Obtain the complementary projection formula.",
        ],
    )
    add(
        "projection_nested",
        "If S≤T then for every x, P_S(P_T x)=P_S x.",
        SUBS + XY[:1],
        imp(op("sub_le", V, S, T), eq(proj(S, proj(T, x)), proj(S, x))),
        "(S T : Submodule ℝ V) (h : S ≤ T) (x : V)",
        "S.starProjection (T.starProjection x) = S.starProjection x",
        "exact congrArg (fun q : V →L[ℝ] V => q x) (Submodule.starProjection_comp_starProjection_of_le h)",
        [
            "The residual x-P_T x lies in T⊥.",
            "The inclusion S≤T implies T⊥≤S⊥.",
            "Projection onto S kills this residual.",
            "Linearity yields P_S(P_T x)=P_S x.",
        ],
    )
    add(
        "projection_symmetric",
        "For every S,x,y, ⟨P_S x,y⟩=⟨x,P_S y⟩.",
        SUB + XY,
        eq(inner(proj(S, x), y), inner(x, proj(S, y))),
        "(S : Submodule ℝ V) (x y : V)",
        "inner ℝ (S.starProjection x) y = inner ℝ x (S.starProjection y)",
        "exact S.inner_starProjection_left_eq_right x y",
        [
            "Split y into its projection and orthogonal residual.",
            "The residual is orthogonal to P_S x.",
            "Split x similarly and eliminate its residual paired with P_S y.",
            "Both inner products equal ⟨P_S x,P_S y⟩.",
        ],
    )
    add(
        "projection_pythagoras",
        "For every S,x, ‖x‖²=‖P_S x‖²+‖P_(S⊥) x‖².",
        SUB + XY[:1],
        eq(sq(norm(x)), plus(sq(norm(proj(S, x))), sq(norm(proj(orth(S), x))))),
        "(S : Submodule ℝ V) (x : V)",
        "‖x‖ ^ 2 = ‖S.starProjection x‖ ^ 2 + ‖Sᗮ.starProjection x‖ ^ 2",
        "exact S.norm_sq_eq_add_norm_sq_starProjection x",
        [
            "The two projections sum to x.",
            "They lie in mutually orthogonal subspaces S and S⊥.",
            "Their inner product therefore vanishes.",
            "Apply the Pythagorean identity to their sum.",
        ],
    )
    add(
        "projection_norm_equality",
        "For every S,x, x∈S iff ‖P_S x‖=‖x‖.",
        SUB + XY[:1],
        iff(mem(x, S), eq(norm(proj(S, x)), norm(x))),
        "(S : Submodule ℝ V) (x : V)",
        "x ∈ S ↔ ‖S.starProjection x‖ = ‖x‖",
        "exact S.mem_iff_norm_starProjection x",
        [
            "A vector of S is fixed, so its norm is preserved.",
            "Conversely assume the projected norm equals the original norm.",
            "The Pythagorean identity forces the complementary component to have zero norm.",
            "Thus x equals its projection and belongs to S.",
        ],
    )
    add(
        "projection_best_approximation",
        "For every S,x and every y∈S, ‖x-P_S x‖≤‖x-y‖.",
        SUB + XY,
        imp(mem(y, S), le(norm(vs(x, proj(S, x))), norm(vs(x, y)))),
        "(S : Submodule ℝ V) (x y : V) (hy : y ∈ S)",
        "‖x - S.starProjection x‖ ≤ ‖x - y‖",
        "have h := Sᗮ.norm_starProjection_apply_le (x-y)\n"
        "rw [map_sub, S.starProjection_orthogonal_apply_eq_zero hy, sub_zero, "
        "S.starProjection_orthogonal_val] at h\nexact h",
        [
            "Project the error x-y onto S⊥.",
            "The component of y vanishes because y belongs to S.",
            "The projected error is x-P_S x by complementary projection.",
            "Contractivity bounds its norm by the norm of x-y.",
        ],
    )
    gs = fam("gram_schmidt", v)
    gn = fam("gram_schmidt_normed", v)
    add(
        "gram_schmidt_orthogonal",
        "For every finite family v, GramSchmidt(v) is pairwise orthogonal.",
        NF,
        fam("orthogonal_family", gs),
        "{n : ℕ} (v : Fin n → V)",
        "Pairwise (fun i j => inner ℝ (InnerProductSpace.gramSchmidt ℝ v i) (InnerProductSpace.gramSchmidt ℝ v j) = 0)",
        "exact InnerProductSpace.gramSchmidt_pairwise_orthogonal ℝ v",
        [
            "Process the finite ordered index set by induction.",
            "At each stage subtract components along earlier orthogonalized vectors.",
            "Each subtraction cancels the relevant inner product.",
            "Use inner-product symmetry to cover either ordering of distinct indices.",
        ],
    )
    add(
        "gram_schmidt_span",
        "For every finite family v, span GramSchmidt(v)=span v.",
        NF,
        eq(span(gs), span(v)),
        "{n : ℕ} (v : Fin n → V)",
        "Submodule.span ℝ (Set.range (InnerProductSpace.gramSchmidt ℝ v)) = Submodule.span ℝ (Set.range v)",
        "exact InnerProductSpace.span_gramSchmidt ℝ v",
        [
            "Each orthogonalized vector is its input minus a combination of earlier vectors.",
            "Inductively it belongs to the span of the original family.",
            "Rearrange the same recursion to express each input using orthogonalized vectors.",
            "The two span inclusions prove equality.",
        ],
    )
    add(
        "gram_schmidt_independent",
        "If v is linearly independent, GramSchmidt(v) is linearly independent.",
        NF,
        imp(fam("independent", v), fam("independent", gs)),
        "{n : ℕ} (v : Fin n → V) (hv : LinearIndependent ℝ v)",
        "LinearIndependent ℝ (InnerProductSpace.gramSchmidt ℝ v)",
        "exact InnerProductSpace.gramSchmidt_linearIndependent hv",
        [
            "Independence prevents an input from lying in the span of its predecessors.",
            "Hence no orthogonalized vector vanishes.",
            "Gram–Schmidt gives pairwise orthogonality.",
            "A nonzero orthogonal family is linearly independent.",
        ],
    )
    add(
        "gram_schmidt_normalization",
        "If v is linearly independent, normalized GramSchmidt(v) is orthonormal.",
        NF,
        imp(fam("independent", v), fam("orthonormal", gn)),
        "{n : ℕ} (v : Fin n → V) (hv : LinearIndependent ℝ v)",
        "Orthonormal ℝ (InnerProductSpace.gramSchmidtNormed ℝ v)",
        "exact InnerProductSpace.gramSchmidtNormed_orthonormal hv",
        [
            "Independence makes every Gram–Schmidt vector nonzero.",
            "Divide each such vector by its norm.",
            "Normalization preserves pairwise orthogonality.",
            "Each normalized vector has unit norm, giving orthonormality.",
        ],
    )
    add(
        "normalized_span",
        "For every finite family v, span normalized GramSchmidt(v)=span v.",
        NF,
        eq(span(gn), span(v)),
        "{n : ℕ} (v : Fin n → V)",
        "Submodule.span ℝ (Set.range (InnerProductSpace.gramSchmidtNormed ℝ v)) = Submodule.span ℝ (Set.range v)",
        "exact (InnerProductSpace.span_gramSchmidtNormed_range v).trans (InnerProductSpace.span_gramSchmidt ℝ v)",
        [
            "Normalization rescales each nonzero orthogonalized vector by an invertible real scalar.",
            "Zero orthogonalized vectors remain zero and contribute nothing to the span.",
            "Therefore normalized and unnormalized orthogonalized families have the same span.",
            "Use Gram–Schmidt span preservation to identify this with the original span.",
        ],
    )
    add(
        "gram_schmidt_fixed",
        "A pairwise orthogonal family is unchanged by GramSchmidt.",
        NF,
        imp(fam("orthogonal_family", v), eq(gs, v)),
        "{n : ℕ} (v : Fin n → V) (hv : Pairwise (fun i j => inner ℝ (v i) (v j) = 0))",
        "InnerProductSpace.gramSchmidt ℝ v = v",
        "exact InnerProductSpace.gramSchmidt_of_orthogonal ℝ hv",
        [
            "Use induction on the ordered finite index.",
            "Earlier orthogonalized vectors equal their original inputs.",
            "All coefficients subtracted at the next step are zero by orthogonality.",
            "Each output equals its input, proving equality of families.",
        ],
    )
    add(
        "onbasis_expansion",
        "For every orthonormal basis b indexed by Fin n and every x, ∑ᵢ⟨bᵢ,x⟩bᵢ=x.",
        NB + XY[:1],
        eq(op("sum_scaled", V, n, bv(b), coeff(bv(b), x)), x),
        "{n : ℕ} (b : OrthonormalBasis (Fin n) ℝ V) (x : V)",
        "∑ i, (inner ℝ (b i) x) • b i = x",
        "exact b.sum_repr' x",
        [
            "A basis expands x in its unique coordinate coefficients.",
            "Orthonormality identifies each coefficient with ⟨bᵢ,x⟩.",
            "Substitute these inner products into the finite basis expansion.",
            "The reconstructed vector is x.",
        ],
    )
    add(
        "parseval",
        "For every orthonormal basis b and every x, ∑ᵢ⟨bᵢ,x⟩²=‖x‖².",
        NB + XY[:1],
        eq(op("sum_squares", n, coeff(bv(b), x)), sq(norm(x))),
        "{n : ℕ} (b : OrthonormalBasis (Fin n) ℝ V) (x : V)",
        "∑ i, (inner ℝ (b i) x) ^ 2 = ‖x‖ ^ 2",
        "exact b.sum_sq_inner_right x",
        [
            "Expand x in the orthonormal basis.",
            "Compute the inner product of the expansion with itself.",
            "Orthonormality removes cross terms and leaves the squares of coefficients.",
            "Identify the self inner product with ‖x‖².",
        ],
    )
    add(
        "onbasis_inner",
        "For every orthonormal basis b and all x,y, ∑ᵢ⟨bᵢ,x⟩⟨bᵢ,y⟩=⟨x,y⟩.",
        NB + XY,
        eq(op("dot", n, coeff(bv(b), x), coeff(bv(b), y)), inner(x, y)),
        "{n : ℕ} (b : OrthonormalBasis (Fin n) ℝ V) (x y : V)",
        "∑ i, (inner ℝ (b i) x) * inner ℝ (b i) y = inner ℝ x y",
        "simpa only [real_inner_comm (b _) x] using b.sum_inner_mul_inner x y",
        [
            "Expand y in the orthonormal basis.",
            "Pair the expansion with x and distribute the inner product over the sum.",
            "Use symmetry of the real inner product to orient the first coefficient.",
            "The resulting sum is the dot product of coefficient families.",
        ],
    )
    add(
        "onbasis_coordinates",
        "For every orthonormal basis b and every x, its coordinate function is i↦⟨bᵢ,x⟩.",
        NB + XY[:1],
        eq(coord(b, x), coeff(bv(b), x)),
        "{n : ℕ} (b : OrthonormalBasis (Fin n) ℝ V) (x : V)",
        "(fun i => b.repr x i) = (fun i => inner ℝ (b i) x)",
        "funext i\nexact b.repr_apply_apply x i",
        [
            "Write the unique basis expansion of x.",
            "Pair with the ith orthonormal basis vector.",
            "All coefficients except the ith vanish under orthogonality.",
            "Function extensionality gives equality of the complete coordinate functions.",
        ],
    )
    add(
        "orthonormal_transition_det",
        "The determinant of the coordinate change between any two Fin n orthonormal bases is 1 or -1.",
        NB + [("c", typ("OrthonormalBasis", V, n))],
        disj(
            eq(op("transition_det", V, n, b, c), real(1)),
            eq(op("transition_det", V, n, b, c), op("real_neg", real(1))),
        ),
        "{n : ℕ} (b c : OrthonormalBasis (Fin n) ℝ V)",
        "b.toBasis.det c = 1 ∨ b.toBasis.det c = -1",
        "exact b.det_to_matrix_orthonormalBasis_real c",
        [
            "The transition matrix preserves the real inner product.",
            "Its transpose multiplied by itself is the identity.",
            "Taking determinants gives the square of its determinant equal to one.",
            "A real number with square one is 1 or -1.",
        ],
    )
    spectral = quant(
        [("b", typ("OrthonormalBasis", V, n)), ("a", typ("ScalarFamily", n))],
        op("eigenfamily", V, n, f, a, bv(b)),
        "exists",
    )
    add(
        "spectral_orthonormal_basis",
        "For every n=dim V and symmetric endomorphism f, there are a Fin n orthonormal basis b and real eigenvalues a with f(bᵢ)=aᵢbᵢ and bᵢ≠0 for every i.",
        [("n", typ("Nat")), ("f", typ("End", V))],
        imp(conj(eq(op("dim", V), n), op("symmetric", V, f)), spectral),
        "(n : ℕ) (f : V →ₗ[ℝ] V) (hn : Module.finrank ℝ V = n) (hf : f.IsSymmetric)",
        "∃ b : OrthonormalBasis (Fin n) ℝ V, ∃ a : Fin n → ℝ, ∀ i, Module.End.HasEigenvector f (a i) (b i)",
        "refine ⟨hf.eigenvectorBasis hn, hf.eigenvalues hn, ?_⟩\nintro i\nexact hf.hasEigenvector_eigenvectorBasis hn i",
        [
            "A real symmetric endomorphism has mutually orthogonal eigenspaces.",
            "Finite-dimensional spectral decomposition spans the entire space by these eigenspaces.",
            "Choose orthonormal bases inside the eigenspaces and combine them.",
            "Index the resulting basis by Fin n using the dimension equality.",
            "Each basis vector is nonzero and satisfies its eigenvalue equation.",
        ],
    )
    return cards


def sha(p):
    return "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    cards = build_cards()
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
    witness = ROOT / "docs/linear-algebra-v3-batch.lean"
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
    (ROOT / "docs/linear-algebra-v3-batch.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    )
    print(
        f"PASS: {len(cards)} general inner-product-space cards compiled and canonicalized"
    )


if __name__ == "__main__":
    main()
