"""Compile general basis/coordinate/eigenvalue Drafts before authoring manifest output."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from xml.sax.saxutils import quoteattr

from pals_agent.typed_linear_algebra_v5 import (
    canonicalize_typed_linear_algebra_v5_openmath_xml as canonicalize,
)
from pals_agent.typed_linear_algebra_v5 import (
    validate_canonical_typed_linear_algebra_v5_openmath_xml as validate,
)

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "pals-agent/lean-workspace"
PROFILE = "typed-linear-algebra-v5"
TYPED = "urn:pals:openmath:typed-linear-algebra:v5"


def sym(cd, name, base=TYPED):
    return f"<OMS cdbase={quoteattr(base)} cd={quoteattr(cd)} name={quoteattr(name)}/>"


def var(n):
    return f"<OMV name={quoteattr(n)}/>"


def app(h, *args):
    return "<OMA>" + h + "".join(args) + "</OMA>"


def op(name, *args):
    return app(sym("la5", name), *args)


def std(cd, name, *args):
    return app(sym(cd, name, "http://www.openmath.org/cd"), *args)


def eq(x, y):
    return std("relation1", "eq", x, y)


def conj(x, y):
    return std("logic1", "and", x, y)


def imp(x, y):
    return std("logic1", "implies", x, y)


def iff(x, y):
    return conj(imp(x, y), imp(y, x))


def typ(name, *args):
    return op(name, *args) if args else sym("la5", name)


def quant(ds, body, kind="forall"):
    attrs = "".join(
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
        + attrs
        + "</OMBVAR>"
        + body
        + "</OMBIND>"
    )


K, V, W, U, n, m, p, b, c, d, b2, c2, f, g, h, x, y, a, z, A, P, S, T, phi = map(
    var,
    (
        "K",
        "V",
        "W",
        "U",
        "n",
        "m",
        "p",
        "b",
        "c",
        "d",
        "b2",
        "c2",
        "f",
        "g",
        "h",
        "x",
        "y",
        "a",
        "z",
        "A",
        "P",
        "S",
        "T",
        "phi",
    ),
)


def sp(name):
    return (name, typ("FiniteDimensionalSpace", K))


def bs(name, space=V, size=n):
    return (name, typ("Basis", K, space, size))


def lm(name, source=V, target=W):
    return (name, typ("LinearMap", K, source, target))


def bv(B, space=V, size=n):
    return op("basis_vectors", K, space, size, B)


def coords(B, x, space=V, size=n):
    return op("coordinates", K, space, size, B, x)


def images(F, family, source=V, target=W, size=n):
    return op("family_images", K, source, target, size, F, family)


def apply(F, x, source=V, target=W):
    return op("apply", K, source, target, F, x)


def construct(B, family):
    return op("construct", K, V, W, n, B, family)


def matrix(F, B=b, C=c, source=V, target=W, ns=n, nt=m):
    return op("to_matrix", K, source, target, ns, nt, B, C, F)


def mm(A, B, r=n, s=n, t=n):
    return op("matrix_mul", K, r, s, t, A, B)


def transition(B, C, space=V, size=n):
    return op("transition", K, space, size, size, B, C)


def comp(F, G, source=V, middle=W, target=V):
    return op("compose", K, source, middle, target, F, G)


def poly(name, F=f):
    return op(name, K, V, F)


def eigenbasis(F, B, values):
    return op("eigenbasis", K, V, n, F, B, values)


def diagmap(B, values):
    return op("diagonal_map", K, V, n, B, values)


def funsum(terms, values):
    return op("functional_sum", K, V, n, terms, values)


BASE = [("K", typ("Field")), sp("V")]
BN = [("n", typ("Nat")), bs("b")]
BW = [sp("W"), ("m", typ("Nat")), bs("c", W, m)]
VX = [("x", typ("Vector", K, V))]
FA = [("a", typ("Coordinates", K, n))]
FV = [("y", typ("Family", K, W, n))]
LEAN = "example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] "


def ls(name):
    return (
        "{"
        + name
        + " : Type*} [AddCommGroup "
        + name
        + "] [Module K "
        + name
        + "] [FiniteDimensional K "
        + name
        + "] "
    )


def build_cards():
    cards = []

    def add(key, statement, ds, body, args, target, proof, steps):
        xml = canonicalize(
            '<OMOBJ xmlns="http://www.openmath.org/OpenMath" version="2.0">'
            + quant(BASE + ds, body)
            + "</OMOBJ>"
        )
        validate(xml)
        cards.append(
            {
                "id": "la_v5_" + key,
                "canonical_statement": "Over any field K and finite-dimensional K-vector spaces, "
                + statement,
                "proof_strategy": steps[0],
                "sketch_steps": steps,
                "openmath_xml": xml,
                "lean_target": LEAN + args + " : " + target,
                "lean_witness": "by\n  " + proof.replace("\n", "\n  "),
            }
        )

    bargs = "{n : ℕ} (b : Module.Basis (Fin n) K V) "
    bwargs = (
        ls("W")
        + "{n m : ℕ} (b : Module.Basis (Fin n) K V) (c : Module.Basis (Fin m) K W) "
    )
    add(
        "basis_reconstruction",
        "every vector x equals ∑ᵢ coord_b(x)ᵢ bᵢ for any Fin n basis b.",
        BN + VX,
        eq(op("sum_scaled", K, V, n, bv(b), coords(b, x)), x),
        bargs + "(x : V)",
        "∑ i, b.repr x i • b i = x",
        "exact b.sum_repr x",
        [
            "Use the basis coordinate equivalence between V and finite coefficient functions.",
            "Apply its inverse to the coordinates of x.",
            "The inverse is the finite linear combination of basis vectors.",
            "The inverse-composition identity gives x.",
        ],
    )
    add(
        "coordinates_of_combination",
        "the coordinates of ∑ᵢaᵢbᵢ are exactly the arbitrary coefficient family a.",
        BN + FA,
        eq(coords(b, op("sum_scaled", K, V, n, bv(b), a)), a),
        bargs + "(a : Fin n → K)",
        "(fun i => b.repr (∑ j, a j • b j) i) = a",
        "exact b.repr_sum_self a",
        [
            "A basis coordinate map is linear.",
            "Each basis vector has its corresponding unit coordinate.",
            "Apply the coordinate map to the finite combination.",
            "All coordinates reduce to the specified coefficients a.",
        ],
    )
    prescribed = quant(
        [lm("f")],
        conj(
            eq(images(f, bv(b)), y),
            quant([lm("g")], imp(eq(images(g, bv(b)), y), eq(g, f))),
        ),
        "exists",
    )
    add(
        "prescribed_basis_map",
        "any prescribed family y indexed by a basis b extends to a unique linear map f with f(bᵢ)=yᵢ.",
        BN + [sp("W")] + FV,
        prescribed,
        ls("W") + bargs + "(y : Fin n → W)",
        "∃ f : V →ₗ[K] W, (fun i => f (b i)) = y ∧ ∀ g : V →ₗ[K] W, (fun i => g (b i)) = y → g = f",
        "refine ⟨b.constr K y, ?_, ?_⟩\n· funext i; exact b.constr_basis K y i\n· intro g hg; apply b.ext; intro i; simpa using congrFun hg i",
        [
            "Send a vector to the same linear combination of the chosen images as its basis coordinates.",
            "Uniqueness of coordinates makes this assignment well defined and linear.",
            "On each basis vector the assignment returns the prescribed image.",
            "Any linear map with these values agrees on every basis expansion.",
        ],
    )
    add(
        "constructed_map_formula",
        "the map constructed from basis images y acts by f(x)=∑ᵢcoord_b(x)ᵢ yᵢ.",
        BN + [sp("W")] + FV + VX,
        eq(apply(construct(b, y), x), op("sum_scaled", K, W, n, y, coords(b, x))),
        ls("W") + bargs + "(y : Fin n → W) (x : V)",
        "b.constr K y x = ∑ i, b.equivFun x i • y i",
        "exact b.constr_apply_fintype K y x",
        [
            "Expand x in the basis b.",
            "Apply the constructed linear map to that finite sum.",
            "Its value on bᵢ is yᵢ.",
            "Linearity yields the displayed weighted sum.",
        ],
    )
    add(
        "constructed_map_range",
        "the range of the map with prescribed basis images y is span(y).",
        BN + [sp("W")] + FV,
        eq(op("range", K, V, W, construct(b, y)), op("span", K, W, n, y)),
        ls("W") + bargs + "(y : Fin n → W)",
        "LinearMap.range (b.constr K y) = Submodule.span K (Set.range y)",
        "exact b.constr_range K",
        [
            "Every output is a linear combination of the prescribed basis images.",
            "This gives inclusion of the range in span(y).",
            "Each yᵢ is the image of bᵢ, so it belongs to the range.",
            "The range is a subspace, giving the reverse span inclusion.",
        ],
    )
    add(
        "constructed_map_injective",
        "if the prescribed images y are linearly independent, their basis-constructed map is injective.",
        BN + [sp("W")] + FV,
        imp(op("independent", K, W, n, y), op("injective", K, V, W, construct(b, y))),
        ls("W") + bargs + "(y : Fin n → W) (hy : LinearIndependent K y)",
        "Function.Injective (b.constr K y)",
        "exact b.injective_constr_of_linearIndependent hy",
        [
            "Write a zero image as a relation among the vectors yᵢ.",
            "Their independence forces each basis coefficient to vanish.",
            "A vector with all zero basis coordinates is zero.",
            "Therefore the constructed map has trivial kernel and is injective.",
        ],
    )
    add(
        "constructed_map_surjective",
        "if the prescribed images y span W, their basis-constructed map is surjective.",
        BN + [sp("W")] + FV,
        imp(
            eq(op("span", K, W, n, y), op("sub_top", K, W)),
            op("surjective", K, V, W, construct(b, y)),
        ),
        ls("W") + bargs + "(y : Fin n → W) (hy : Submodule.span K (Set.range y) = ⊤)",
        "Function.Surjective (b.constr K y)",
        "apply LinearMap.range_eq_top.mp\nrw [b.constr_range K, hy]",
        [
            "The image of the constructed map is the span of its prescribed images.",
            "The hypothesis identifies that span with W.",
            "Consequently the range is the whole target.",
            "The range characterization of surjectivity completes the proof.",
        ],
    )
    add(
        "basis_determines_map",
        "two linear maps agreeing on all basis vectors are equal.",
        BN + [sp("W"), lm("f"), lm("g")],
        imp(eq(images(f, bv(b)), images(g, bv(b))), eq(f, g)),
        ls("W")
        + bargs
        + "(f g : V →ₗ[K] W) (h : (fun i => f (b i)) = (fun i => g (b i)))",
        "f = g",
        "apply b.ext\nintro i\nexact congrFun h i",
        [
            "Expand an arbitrary vector in the basis.",
            "Apply linearity to both maps on its expansion.",
            "The hypothesis identifies each corresponding basis image.",
            "The resulting values agree on every vector.",
        ],
    )
    add(
        "matrix_action_coordinates",
        "matrix representation sends input coordinates to output coordinates.",
        BN + BW + [lm("f")] + VX,
        eq(
            op("matrix_vec", K, m, n, matrix(f), coords(b, x)),
            coords(c, apply(f, x), W, m),
        ),
        bwargs + "(f : V →ₗ[K] W) (x : V)",
        "(LinearMap.toMatrix b c f).mulVec (b.repr x) = c.repr (f x)",
        "exact LinearMap.toMatrix_mulVec_repr b c f x",
        [
            "Expand the input vector in its source basis.",
            "The jth matrix column consists of the target coordinates of f(bⱼ).",
            "Linearity combines those columns with the input coefficients.",
            "This is precisely matrix-vector multiplication.",
        ],
    )
    matrixunique = quant(
        [lm("f")],
        conj(eq(matrix(f), A), quant([lm("g")], imp(eq(matrix(g), A), eq(g, f)))),
        "exists",
    )
    add(
        "matrix_representation_unique",
        "for chosen source and target bases, every m×n matrix represents exactly one linear map V→W.",
        BN + BW + [("A", typ("Matrix", K, m, n))],
        matrixunique,
        bwargs + "(A : Matrix (Fin m) (Fin n) K)",
        "∃ f : V →ₗ[K] W, LinearMap.toMatrix b c f = A ∧ ∀ g, LinearMap.toMatrix b c g = A → g = f",
        "refine ⟨Matrix.toLin b c A, LinearMap.toMatrix_toLin b c A, ?_⟩\nintro g hg\napply (LinearMap.toMatrix b c).injective\nsimpa using hg",
        [
            "Use A to map source coordinate columns to target coordinate columns.",
            "Translate the result back through the target basis to define a linear map.",
            "Converting this map to a matrix returns A.",
            "Injectivity of the coordinate equivalences proves uniqueness.",
        ],
    )
    ds = BN + BW + [sp("U"), ("p", typ("Nat")), bs("d", U, p), lm("f"), lm("g", W, U)]
    add(
        "matrix_of_composition",
        "the matrix of g∘f in three chosen bases is matrix(g)·matrix(f), with the intermediate basis shared.",
        ds,
        eq(
            matrix(comp(f, g, V, W, U), b, d, V, U, n, p),
            mm(matrix(g, c, d, W, U, m, p), matrix(f), p, m, n),
        ),
        ls("W")
        + ls("U")
        + "{n m p : ℕ} (b : Module.Basis (Fin n) K V) (c : Module.Basis (Fin m) K W) (d : Module.Basis (Fin p) K U) (f : V →ₗ[K] W) (g : W →ₗ[K] U)",
        "LinearMap.toMatrix b d (g.comp f) = LinearMap.toMatrix c d g * LinearMap.toMatrix b c f",
        "exact LinearMap.toMatrix_comp b c d g f",
        [
            "Apply f to a source basis vector and expand in the intermediate basis.",
            "Apply g to each term and take coordinates in the final basis.",
            "The resulting coefficient sums are the matrix product entries.",
            "The factor order is g’s matrix followed by f’s matrix.",
        ],
    )
    add(
        "matrix_representation_linear",
        "matrix representation preserves addition and scalar multiplication of linear maps.",
        BN + BW + [lm("f"), lm("g"), ("z", typ("Scalar", K))],
        conj(
            eq(
                matrix(op("map_add", K, V, W, f, g)),
                op("matrix_add", K, m, n, matrix(f), matrix(g)),
            ),
            eq(
                matrix(op("map_smul", K, V, W, z, f)),
                op("matrix_smul", K, m, n, z, matrix(f)),
            ),
        ),
        bwargs + "(f g : V →ₗ[K] W) (z : K)",
        "LinearMap.toMatrix b c (f+g) = LinearMap.toMatrix b c f + LinearMap.toMatrix b c g ∧ LinearMap.toMatrix b c (z • f) = z • LinearMap.toMatrix b c f",
        "exact ⟨(LinearMap.toMatrix b c).map_add f g, (LinearMap.toMatrix b c).map_smul z f⟩",
        [
            "Matrix columns are target coordinates of images of source basis vectors.",
            "Evaluation of a sum of maps adds these images.",
            "Evaluation of a scalar multiple scales these images.",
            "Linearity of target coordinates gives both matrix identities.",
        ],
    )
    add(
        "basis_change_coordinates",
        "for two bases b,c of V, the matrix of b in c-coordinates converts b-coordinates of x into c-coordinates.",
        BN + [bs("c")] + VX,
        eq(op("matrix_vec", K, n, n, transition(c, b), coords(b, x)), coords(c, x)),
        bargs + "(c : Module.Basis (Fin n) K V) (x : V)",
        "(c.toMatrix b).mulVec (b.repr x) = c.repr x",
        "exact Module.Basis.toMatrix_mulVec_repr b c x",
        [
            "Expand x using b and its coefficient vector.",
            "Write each b-vector in coordinates of c.",
            "Collect the coefficient of every c-vector.",
            "The coordinate change matrix has these b-coordinate columns in c.",
        ],
    )
    add(
        "basis_change_cocycle",
        "for bases b,c,d of V, C(b←c)C(c←d)=C(b←d).",
        BN + [bs("c"), bs("d")],
        eq(mm(transition(b, c), transition(c, d)), transition(b, d)),
        bargs + "(c d : Module.Basis (Fin n) K V)",
        "b.toMatrix c * c.toMatrix d = b.toMatrix d",
        "exact b.toMatrix_mul_toMatrix c d",
        [
            "Expand each d-vector first in c.",
            "Then expand each c-vector in b.",
            "Combining coefficients produces the product of the two transition matrices.",
            "Uniqueness of b-coordinates identifies it with the direct transition.",
        ],
    )
    add(
        "basis_change_inverse",
        "the transition matrices in opposite directions between two bases are two-sided inverses.",
        BN + [bs("c")],
        conj(
            eq(mm(transition(b, c), transition(c, b)), op("matrix_identity", K, n)),
            eq(mm(transition(c, b), transition(b, c)), op("matrix_identity", K, n)),
        ),
        bargs + "(c : Module.Basis (Fin n) K V)",
        "b.toMatrix c * c.toMatrix b = 1 ∧ c.toMatrix b * b.toMatrix c = 1",
        "exact ⟨b.toMatrix_mul_toMatrix_flip c, c.toMatrix_mul_toMatrix_flip b⟩",
        [
            "Composing coordinate changes in opposite directions leaves all coordinates unchanged.",
            "The transition cocycle expresses each composition as a self-transition.",
            "A basis has the identity as its self-transition matrix.",
            "Apply this in both orders.",
        ],
    )
    ds = BN + BW + [bs("b2"), bs("c2", W, m), lm("f")]
    add(
        "two_sided_basis_change",
        "changing both bases transforms a map matrix by C(c←c2)·M(b2,c2,f)·C(b2←b)=M(b,c,f).",
        ds,
        eq(
            mm(
                mm(transition(c, c2, W, m), matrix(f, b2, c2), m, m, n),
                transition(b2, b),
                m,
                n,
                n,
            ),
            matrix(f),
        ),
        bwargs
        + "(b2 : Module.Basis (Fin n) K V) (c2 : Module.Basis (Fin m) K W) (f : V →ₗ[K] W)",
        "c.toMatrix c2 * LinearMap.toMatrix b2 c2 f * b2.toMatrix b = LinearMap.toMatrix b c f",
        "exact basis_toMatrix_mul_linearMap_toMatrix_mul_basis_toMatrix b b2 c c2 f",
        [
            "Change the input coordinates from b to b2 on the right.",
            "Apply the matrix expressed in bases b2 and c2.",
            "Change output coordinates from c2 to c on the left.",
            "The composite performs f directly in bases b and c.",
        ],
    )
    ds = BN + [lm("f", V, V)] + FA
    add(
        "eigenbasis_diagonal_matrix",
        "a map f has f(bᵢ)=aᵢbᵢ on the basis b exactly when its matrix in b is diagonal with entries a.",
        ds,
        iff(
            eigenbasis(f, b, a),
            eq(matrix(f, b, b, V, V, n, n), op("diagonal", K, n, a)),
        ),
        bargs + "(f : V →ₗ[K] V) (a : Fin n → K)",
        "(∀ i, f (b i) = a i • b i) ↔ LinearMap.toMatrix b b f = Matrix.diagonal a",
        "constructor\n· intro h; ext i j; by_cases hij : i = j <;> simp [LinearMap.toMatrix_apply, h, hij]\n· intro h i\n  have hf : f = Matrix.toLin b b (Matrix.diagonal a) := by rw [← h, Matrix.toLin_toMatrix]\n  rw [hf]\n  exact (hasEigenvector_toLin_diagonal a i b).apply_eq_smul",
        [
            "A matrix column is the coordinate vector of the corresponding basis image.",
            "The eigenvector equation puts a single diagonal coefficient in that column.",
            "Conversely a diagonal column reconstructs exactly aᵢbᵢ.",
            "Applying this to all columns proves the equivalence.",
        ],
    )
    coordfamily = op("coordinate_functionals", K, V, n, b)
    add(
        "dual_basis_expansion",
        "every linear functional φ is ∑ᵢ φ(bᵢ) coord_b,i.",
        BN + [("phi", typ("Functional", K, V))],
        eq(funsum(coordfamily, op("functional_values", K, V, n, phi, bv(b))), phi),
        bargs + "(phi : V →ₗ[K] K)",
        "(∑ i, phi (b i) • b.coord i) = phi",
        "exact b.sum_dual_apply_smul_coord phi",
        [
            "Expand an arbitrary x in b.",
            "Apply the functional φ and distribute it over the finite sum.",
            "The coefficient of coord_b,i(x) is φ(bᵢ).",
            "Extensionality turns this identity of values into an identity of functionals.",
        ],
    )
    add(
        "dual_coordinates_independent",
        "the coordinate functionals of any basis are linearly independent.",
        BN,
        op("functional_independent", K, V, n, coordfamily),
        bargs,
        "LinearIndependent K b.coord",
        "exact b.linearIndependent_coord",
        [
            "Assume a linear combination of coordinate functionals vanishes.",
            "Evaluate it on each individual basis vector.",
            "The Kronecker coordinate values isolate the corresponding coefficient.",
            "Every coefficient is zero, proving independence.",
        ],
    )
    add(
        "subspace_has_complement",
        "every subspace S has a complementary subspace T.",
        [("S", typ("Subspace", K, V))],
        quant(
            [("T", typ("Subspace", K, V))], op("complementary", K, V, S, T), "exists"
        ),
        "(S : Submodule K V)",
        "∃ T : Submodule K V, IsCompl S T",
        "exact S.exists_isCompl",
        [
            "Choose a basis of S.",
            "Extend it to a basis of V.",
            "Let T be the span of the additional basis vectors.",
            "The full basis gives S+T=V, and independence gives S∩T=0.",
        ],
    )
    add(
        "injective_map_splits",
        "every injective linear map f:V→W has a linear left inverse.",
        [sp("W"), lm("f")],
        imp(
            op("injective", K, V, W, f),
            quant([lm("g", W, V)], eq(comp(f, g), op("identity", K, V)), "exists"),
        ),
        ls("W") + "(f : V →ₗ[K] W) (hf : Function.Injective f)",
        "∃ g : W →ₗ[K] V, g.comp f = LinearMap.id",
        "exact f.exists_leftInverse_of_injective (LinearMap.ker_eq_bot.mpr hf)",
        [
            "The images of a basis of V form an independent family in W.",
            "Extend that family to a basis of W.",
            "Send the image basis vectors back to their preimages and the added vectors to zero.",
            "The resulting linear map composes with f to the identity.",
        ],
    )
    add(
        "surjective_map_splits",
        "every surjective linear map f:V→W has a linear right inverse.",
        [sp("W"), lm("f")],
        imp(
            op("surjective", K, V, W, f),
            quant(
                [lm("g", W, V)], eq(comp(g, f, W, V, W), op("identity", K, W)), "exists"
            ),
        ),
        ls("W") + "(f : V →ₗ[K] W) (hf : Function.Surjective f)",
        "∃ g : W →ₗ[K] V, f.comp g = LinearMap.id",
        "exact f.exists_rightInverse_of_surjective (LinearMap.range_eq_top.mpr hf)",
        [
            "Choose a basis of W.",
            "Use surjectivity to choose a preimage of each basis vector.",
            "Extend those choices linearly to a map g:W→V.",
            "On the basis of W, f∘g is the identity, hence it is the identity everywhere.",
        ],
    )
    E = [lm("f", V, V), ("z", typ("Scalar", K))] + VX + [("P", typ("Polynomial", K))]
    add(
        "polynomial_on_eigenvector",
        "if x is a nonzero eigenvector of f with eigenvalue z, then P(f)x=P(z)x for every polynomial P.",
        E,
        imp(
            op("has_eigenvector", K, V, f, z, x),
            eq(
                apply(op("poly_aeval", K, V, f, P), x, V, V),
                op("vector_smul", K, V, op("poly_eval", K, P, z), x),
            ),
        ),
        "(f : V →ₗ[K] V) (z : K) (x : V) (P : Polynomial K) (hx : Module.End.HasEigenvector f z x)",
        "(Polynomial.aeval f P) x = P.eval z • x",
        "exact Module.End.aeval_apply_of_hasEigenvector hx",
        [
            "Repeated application of f multiplies x by corresponding powers of z.",
            "Constant polynomials act by scalar multiplication.",
            "Linearity combines the polynomial’s monomial actions.",
            "The scalar sum is precisely P evaluated at z.",
        ],
    )
    E = [lm("f", V, V), ("z", typ("Scalar", K))]
    for key, pname, label, proof in [
        (
            "eigenvalue_charpoly",
            "charpoly",
            "characteristic polynomial",
            "Module.End.hasEigenvalue_iff_isRoot_charpoly f z",
        ),
        (
            "eigenvalue_minpoly",
            "minpoly",
            "minimal polynomial",
            "Module.End.hasEigenvalue_iff_isRoot",
        ),
    ]:
        lp = "f.charpoly" if pname == "charpoly" else "minpoly K f"
        add(
            key,
            "z is an eigenvalue of f iff z is a root of its " + label + ".",
            E,
            iff(op("has_eigenvalue", K, V, f, z), op("poly_root", K, poly(pname), z)),
            "(f : V →ₗ[K] V) (z : K)",
            "Module.End.HasEigenvalue f z ↔ (" + lp + ").IsRoot z",
            "exact " + proof,
            [
                "An eigenvector turns polynomial evaluation at f into scalar evaluation at z.",
                "For the forward direction, apply the annihilating polynomial to that nonzero vector.",
                "For the converse, a root forces a nonzero kernel vector for f-zI, using the polynomial’s defining property.",
                "This gives a nonzero eigenvector and the claimed equivalence.",
            ],
        )
    add(
        "minpoly_divides_charpoly",
        "the minimal polynomial of f divides its characteristic polynomial.",
        [lm("f", V, V)],
        op("poly_divides", K, poly("minpoly"), poly("charpoly")),
        "(f : V →ₗ[K] V)",
        "minpoly K f ∣ f.charpoly",
        "exact LinearMap.minpoly_dvd_charpoly f",
        [
            "Cayley–Hamilton says the characteristic polynomial annihilates f.",
            "The minimal polynomial generates the ideal of annihilating scalar polynomials.",
            "Every annihilating polynomial is therefore its multiple.",
            "Apply that property to the characteristic polynomial.",
        ],
    )
    add(
        "annihilator_minpoly_divisibility",
        "P(f)=0 iff the minimal polynomial of f divides P.",
        [lm("f", V, V), ("P", typ("Polynomial", K))],
        iff(
            eq(op("poly_aeval", K, V, f, P), op("zero_map", K, V, V)),
            op("poly_divides", K, poly("minpoly"), P),
        ),
        "(f : V →ₗ[K] V) (P : Polynomial K)",
        "Polynomial.aeval f P = 0 ↔ minpoly K f ∣ P",
        "exact minpoly.dvd_iff.symm",
        [
            "Divide P by the monic minimal polynomial.",
            "Its evaluation at f equals the evaluation of the lower-degree remainder.",
            "Minimality forces an annihilating remainder to vanish.",
            "Conversely any multiple annihilates f by the evaluation homomorphism.",
        ],
    )
    ef = op("eigenspace", K, V, f, z)
    add(
        "commuting_preserves_eigenspace",
        "if f and g commute, g maps each eigenspace of f into itself.",
        [lm("f", V, V), lm("g", V, V), ("z", typ("Scalar", K))],
        imp(
            op("commute", K, V, f, g),
            op("sub_le", K, V, op("sub_map", K, V, V, g, ef), ef),
        ),
        "(f g : V →ₗ[K] V) (z : K) (h : Commute f g)",
        "(Module.End.eigenspace f z).map g ≤ Module.End.eigenspace f z",
        "rintro _ ⟨x, hx, rfl⟩\nchange x ∈ Module.End.eigenspace f z at hx\nrw [Module.End.mem_eigenspace_iff] at hx ⊢\nhave hh := congrArg (fun q : V →ₗ[K] V => q x) h.eq\nchange f (g x) = g (f x) at hh\nrw [hh, hx, map_smul]",
        [
            "Take x with f(x)=zx.",
            "Commutativity gives f(gx)=g(fx).",
            "Linearity of g changes g(zx) into z g(x).",
            "Thus gx remains in the z-eigenspace of f, even if gx=0.",
        ],
    )
    add(
        "common_eigenbasis_commutes",
        "two endomorphisms diagonal on the same basis commute.",
        BN + [lm("f", V, V), lm("g", V, V)] + FA + [("z", typ("Coordinates", K, n))],
        imp(conj(eigenbasis(f, b, a), eigenbasis(g, b, z)), op("commute", K, V, f, g)),
        bargs
        + "(f g : V →ₗ[K] V) (a z : Fin n → K) (hf : ∀ i, f (b i) = a i • b i) (hg : ∀ i, g (b i) = z i • b i)",
        "Commute f g",
        "show f * g = g * f\napply b.ext\nintro i\nsimp [Module.End.mul_apply, hf, hg, smul_smul, mul_comm]",
        [
            "Apply each composite to an arbitrary common basis vector.",
            "The two results multiply that vector by aᵢzᵢ and zᵢaᵢ.",
            "These scalars agree in the field.",
            "Equality on a basis gives equality of the composites.",
        ],
    )
    D = diagmap(b, a)
    add(
        "diagonal_operator_spectrum",
        "the eigenvalues of the operator diagonal with entries a in basis b are exactly the values occurring in a.",
        BN + FA + [("z", typ("Scalar", K))],
        iff(op("has_eigenvalue", K, V, D, z), op("coordinate_contains", K, n, a, z)),
        bargs + "(a : Fin n → K) (z : K)",
        "Module.End.HasEigenvalue (Matrix.toLin b b (Matrix.diagonal a)) z ↔ ∃ i, a i = z",
        "exact hasEigenvalue_toLin_diagonal_iff a b",
        [
            "Every diagonal basis vector is a nonzero eigenvector for its diagonal entry.",
            "Conversely express a nonzero eigenvector in the basis.",
            "Some coordinate is nonzero, and its eigenvector equation forces z to equal that diagonal entry.",
            "This proves both implications, including the empty-basis case.",
        ],
    )
    add(
        "diagonal_operator_eigenspaces_span",
        "the eigenspaces of an operator diagonal in a basis span the whole space.",
        BN + FA,
        eq(op("eigenspaces_sup", K, V, D), op("sub_top", K, V)),
        bargs + "(a : Fin n → K)",
        "(⨆ z : K, Module.End.eigenspace (Matrix.toLin b b (Matrix.diagonal a)) z) = ⊤",
        "exact Matrix.iSup_eigenspace_toLin_diagonal_eq_top a b",
        [
            "Each basis vector belongs to the eigenspace indexed by its diagonal entry.",
            "Therefore the supremum of eigenspaces contains every basis vector.",
            "It contains their span.",
            "The basis spans V, so the supremum is the whole space.",
        ],
    )
    i, j, t = map(var, ("i", "j", "t"))
    RI = [
        ("n", typ("Nat")),
        ("i", typ("Index", n)),
        ("j", typ("Index", n)),
        ("t", typ("Scalar", K)),
    ]
    ne = std("relation1", "neq", i, j)
    E = op("transvection", K, n, i, j, t)
    row = lambda M, q: op("row", K, n, n, M, q)
    plusrow = op(
        "coordinate_add", K, n, row(A, i), op("coordinate_smul", K, n, t, row(A, j))
    )
    det = lambda M: op("matrix_det", K, n, M)
    add(
        "row_addition_preserves_determinant",
        "adding t times row j to distinct row i preserves the determinant of every n×n matrix A.",
        RI + [("A", typ("Matrix", K, n, n))],
        imp(ne, eq(det(op("row_update", K, n, n, A, i, plusrow)), det(A))),
        "{n : ℕ} (A : Matrix (Fin n) (Fin n) K) (i j : Fin n) (t : K) (h : i ≠ j)",
        "(A.updateRow i (A i + t • A j)).det = A.det",
        "exact Matrix.det_updateRow_add_smul_self A h t",
        [
            "Expand the determinant linearly in its updated row.",
            "The original row contributes det(A).",
            "The extra summand has equal rows i and j, so it vanishes.",
            "The determinant is consequently unchanged for every scalar t.",
        ],
    )
    add(
        "row_scaling_determinant",
        "multiplying one row of A by t multiplies its determinant by t.",
        RI[:-2] + [("t", typ("Scalar", K)), ("A", typ("Matrix", K, n, n))],
        eq(
            det(
                op(
                    "row_update",
                    K,
                    n,
                    n,
                    A,
                    i,
                    op("coordinate_smul", K, n, t, row(A, i)),
                )
            ),
            op("scalar_mul", K, t, det(A)),
        ),
        "{n : ℕ} (A : Matrix (Fin n) (Fin n) K) (i : Fin n) (t : K)",
        "(A.updateRow i (t • A i)).det = t * A.det",
        "simpa using Matrix.det_updateRow_smul A i t (A i)",
        [
            "View the determinant as a linear function of row i.",
            "Pull the scalar t outside that row slot.",
            "Replacing row i by its original value recovers A.",
            "The determinant is t times det(A), including t=0.",
        ],
    )
    add(
        "row_addition_matrix_realization",
        "left multiplication by the elementary matrix Eᵢⱼ(t) replaces row i of any rectangular A by row i plus t times row j.",
        RI + [("m", typ("Nat")), ("A", typ("Matrix", K, n, m))],
        eq(
            mm(E, A, n, n, m),
            op(
                "row_update",
                K,
                n,
                m,
                A,
                i,
                op(
                    "coordinate_add",
                    K,
                    m,
                    op("row", K, n, m, A, i),
                    op("coordinate_smul", K, m, t, op("row", K, n, m, A, j)),
                ),
            ),
        ),
        "{n m : ℕ} (A : Matrix (Fin n) (Fin m) K) (i j : Fin n) (t : K)",
        "Matrix.transvection i j t * A = A.updateRow i (A i + t • A j)",
        "ext r c\nby_cases hr : r = i\n· subst r; simp [Matrix.transvection_mul_apply_same]\n· simp [Matrix.transvection_mul_apply_of_ne i j r c hr, Matrix.updateRow_ne hr]",
        [
            "Compare the product and the row-updated matrix entry by entry.",
            "At row i, the transvection contributes Aᵢ+tAⱼ.",
            "At every other row the off-diagonal correction is zero.",
            "The entry identities prove the complete rectangular matrix equality.",
        ],
    )
    En = op("transvection", K, n, i, j, op("scalar_neg", K, t))
    add(
        "row_addition_inverse",
        "adding t times row j to row i is undone by adding -t times that row, provided i≠j.",
        RI,
        imp(
            ne,
            conj(
                eq(mm(E, En), op("matrix_identity", K, n)),
                eq(mm(En, E), op("matrix_identity", K, n)),
            ),
        ),
        "{n : ℕ} (i j : Fin n) (t : K) (h : i ≠ j)",
        "Matrix.transvection i j t * Matrix.transvection i j (-t) = 1 ∧ Matrix.transvection i j (-t) * Matrix.transvection i j t = 1",
        "constructor <;> simp [Matrix.transvection_mul_transvection_same i j h]",
        [
            "The matrix units in distinct row and column positions square to zero.",
            "Multiplication of two such transvections adds their coefficients.",
            "The coefficients t and -t sum to zero in either order.",
            "The transvection with coefficient zero is the identity matrix.",
        ],
    )
    mv = lambda M, v: op("matrix_vec", K, n, m, M, v)
    ev = lambda v: op("matrix_vec", K, n, n, E, v)
    add(
        "row_operation_preserves_system",
        "simultaneously applying Eᵢⱼ(t), i≠j, to a rectangular system's coefficient matrix and right hand side preserves exactly its solutions.",
        RI
        + [
            ("m", typ("Nat")),
            ("A", typ("Matrix", K, n, m)),
            ("x", typ("Coordinates", K, m)),
            ("y", typ("Coordinates", K, n)),
        ],
        imp(ne, iff(eq(mv(mm(E, A, n, n, m), x), ev(y)), eq(mv(A, x), y))),
        "{n m : ℕ} (A : Matrix (Fin n) (Fin m) K) (i j : Fin n) (t : K) (h : i ≠ j) (x : Fin m → K) (y : Fin n → K)",
        "(Matrix.transvection i j t * A).mulVec x = (Matrix.transvection i j t).mulVec y ↔ A.mulVec x = y",
        "have he : IsUnit (Matrix.transvection i j t) := (Matrix.isUnit_iff_isUnit_det _).mpr (by rw [Matrix.det_transvection_of_ne i j h]; exact isUnit_one)\nhave hinj := Matrix.mulVec_injective_iff_isUnit.mpr he\nrw [← Matrix.mulVec_mulVec]\nexact hinj.eq_iff",
        [
            "The elementary matrix has determinant one because i and j are distinct.",
            "It is therefore invertible and its multiplication on vectors is injective.",
            "Associativity rewrites the transformed equation as E(Ax)=Ey.",
            "Injectivity cancels E, giving precisely Ax=y in both directions.",
        ],
    )
    N = op("matrix_single", K, n, n, i, j, t)
    nz = std("relation1", "neq", t, op("scalar_zero", K))
    zero = op("matrix_zero", K, n, n)
    add(
        "nonzero_square_zero_family",
        "for every pair of distinct indices i,j and nonzero scalar t, the matrix with t in entry (i,j) and zero elsewhere is nonzero but has square zero.",
        RI,
        imp(conj(ne, nz), conj(std("relation1", "neq", N, zero), eq(mm(N, N), zero))),
        "{n : ℕ} (i j : Fin n) (t : K) (h : i ≠ j) (ht : t ≠ 0)",
        "(Matrix.single i j t : Matrix (Fin n) (Fin n) K) ≠ 0 ∧ Matrix.single i j t * Matrix.single i j t = 0",
        "constructor\n· intro hz; apply ht; simpa using congrArg (fun M : Matrix (Fin n) (Fin n) K => M i j) hz\n· simp [Matrix.single_mul_single_of_ne, h.symm]",
        [
            "Inspect entry (i,j): it is t, so the matrix is nonzero.",
            "A nonzero term in its square would need j=i as an intermediate index.",
            "The distinct-index hypothesis excludes such a term.",
            "This gives a whole parameterized family disproving the inference A²=0 ⇒ A=0.",
        ],
    )
    add(
        "determinant_one_nonidentity_family",
        "for distinct i,j and nonzero t, the transvection Eᵢⱼ(t) has determinant one but is not the identity.",
        RI,
        imp(
            conj(ne, nz),
            conj(
                eq(op("matrix_det", K, n, E), op("scalar_one", K)),
                std("relation1", "neq", E, op("matrix_identity", K, n)),
            ),
        ),
        "{n : ℕ} (i j : Fin n) (t : K) (h : i ≠ j) (ht : t ≠ 0)",
        "(Matrix.transvection i j t).det = 1 ∧ Matrix.transvection i j t ≠ 1",
        "constructor\n· exact Matrix.det_transvection_of_ne i j h t\n· intro hz; apply ht; simpa [Matrix.transvection, h] using congrArg (fun M : Matrix (Fin n) (Fin n) K => M i j) hz",
        [
            "A row addition to the identity preserves its determinant one.",
            "The off-diagonal entry (i,j) in this transvection equals t.",
            "That entry is zero in the identity, while t is nonzero.",
            "Hence determinant one is insufficient to recognize the identity matrix.",
        ],
    )
    zm = op("zero_map", K, V, V)
    add(
        "square_zero_obstructs_eigenbasis",
        "a nonzero endomorphism f with f∘f=0 cannot have a basis of eigenvectors, over any field.",
        [lm("f", V, V)] + BN + FA,
        imp(
            conj(std("relation1", "neq", f, zm), eq(comp(f, f, V, V, V), zm)),
            std("logic1", "not", eigenbasis(f, b, a)),
        ),
        "(f : V →ₗ[K] V) (hf : f ≠ 0) (hs : f.comp f = 0) " + bargs + "(a : Fin n → K)",
        "¬ (∀ i, f (b i) = a i • b i)",
        "intro he\napply hf\napply b.ext\nintro i\nhave hz := congrArg (fun q : V →ₗ[K] V => q (b i)) hs\nhave heq : (a i * a i) • b i = 0 := by simpa [LinearMap.comp_apply, he, smul_smul] using hz\nhave ha : a i = 0 := by\n  have hp := (smul_eq_zero.mp heq).resolve_right (b.ne_zero i)\n  exact mul_self_eq_zero.mp hp\nsimp [he, ha]",
        [
            "Assume f is diagonal on some basis with entries aᵢ.",
            "The square-zero equation implies aᵢ²bᵢ=0.",
            "Basis vectors are nonzero and a field has no nonzero square-zero scalar, so aᵢ=0.",
            "The map then vanishes on every basis vector and hence everywhere, contradicting f≠0.",
        ],
    )
    return cards


def sha(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    cards = build_cards()
    assert len(cards) >= 30
    assert len({c["openmath_xml"] for c in cards}) == len(cards)
    assert all(4 <= len(c["sketch_steps"]) <= 10 for c in cards)
    witness = ROOT / "docs/linear-algebra-v5-batch.lean"
    witness.write_text(
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
    subprocess.run(
        ["lake", "env", "lean", str(witness)], cwd=WORKSPACE, check=True, timeout=180
    )
    pkgs = json.loads((WORKSPACE / "lake-manifest.json").read_text())["packages"]
    payload = {
        "schema_version": "pals.typed-catalog-expansion-batch.v1",
        "profile_id": PROFILE,
        "cards": cards,
        "evidence": {
            "witness_path": str(witness.relative_to(ROOT)),
            "witness_sha256": sha(witness),
            "validator_sha256": sha(
                ROOT / "pals-agent/pals_agent/typed_linear_algebra_v5.py"
            ),
            "registry_sha256": sha(
                ROOT
                / "pals-agent/pals_agent/content_dictionaries/typed-linear-algebra-v5-registry.json"
            ),
            "toolchain": (WORKSPACE / "lean-toolchain").read_text().strip(),
            "mathlib_revision": next(p["rev"] for p in pkgs if p["name"] == "mathlib"),
        },
    }
    (ROOT / "docs/linear-algebra-v5-batch.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    )
    print(
        f"PASS: {len(cards)} basis/coordinate/eigenvalue cards compiled and canonicalized"
    )


if __name__ == "__main__":
    main()
