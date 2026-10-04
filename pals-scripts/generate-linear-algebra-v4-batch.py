"""Compile arbitrary-size matrix Drafts before writing the authoring manifest."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from xml.sax.saxutils import quoteattr

from pals_agent.typed_linear_algebra_v4 import (
    canonicalize_typed_linear_algebra_v4_openmath_xml as canonicalize,
)
from pals_agent.typed_linear_algebra_v4 import (
    validate_canonical_typed_linear_algebra_v4_openmath_xml as validate,
)

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "pals-agent/lean-workspace"
PROFILE = "typed-linear-algebra-v4"
TYPED = "urn:pals:openmath:typed-linear-algebra:v4"


def sym(cd, name, base=TYPED):
    return f"<OMS cdbase={quoteattr(base)} cd={quoteattr(cd)} name={quoteattr(name)}/>"


def var(n):
    return f"<OMV name={quoteattr(n)}/>"


def app(h, *args):
    return "<OMA>" + h + "".join(args) + "</OMA>"


def op(name, *args):
    return app(sym("la4", name), *args)


def std(cd, name, *args):
    return app(sym(cd, name, "http://www.openmath.org/cd"), *args)


def eq(x, y):
    return std("relation1", "eq", x, y)


def ne(x, y):
    return std("relation1", "neq", x, y)


def le(x, y):
    return std("relation1", "leq", x, y)


def plus(x, y):
    return std("arith1", "plus", x, y)


def conj(x, y):
    return std("logic1", "and", x, y)


def imp(x, y):
    return std("logic1", "implies", x, y)


def iff(x, y):
    return conj(imp(x, y), imp(y, x))


def typ(name, *args):
    return op(name, *args) if args else sym("la4", name)


def quant(ds, body, kind="forall"):
    ds = "".join(
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
        + ds
        + "</OMBVAR>"
        + body
        + "</OMBIND>"
    )


K, m, n, p, k, A, B, C, P, d, x, y, t = map(
    var, ("K", "m", "n", "p", "k", "A", "B", "C", "P", "d", "x", "y", "t")
)


def nat(i):
    return f"<OMI>{i}</OMI>"


def sc(i):
    return op("scalar_nat", K, nat(i))


def mm(X, Y, r=n, s=n, t=n):
    return op("mul", K, r, s, t, X, Y)


def trans(X, r=n, s=n):
    return op("transpose", K, r, s, X)


def unary(name, X, size=n):
    return op(name, K, size, X)


def det(X, size=n):
    return unary("det", X, size)


def tr(X, size=n):
    return unary("trace", X, size)


def inv(X):
    return unary("inv", X)


def cp(X):
    return unary("charpoly", X)


def rank(X, r=n, s=n):
    return op("rank", K, r, s, X)


def ident(size=n):
    return op("identity", K, size)


def zero(r=n, s=n):
    return op("zero", K, r, s)


def mv(X, v, r=n, s=n):
    return op("mul_vec", K, r, s, X, v)


def mat(name, r=n, s=n):
    return (name, typ("Matrix", K, r, s))


def vec(name, size=n):
    return (name, typ("Vector", K, size))


BASE = [("K", typ("Field"))]
N = [("n", typ("Nat"))]
SQ = N + [mat("A")]
PAIR = SQ + [mat("B")]
LEAN = "example {K : Type*} [Field K] "
MATRIX = "Matrix (Fin n) (Fin n) K"


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
                "id": "la_v4_" + key,
                "canonical_statement": "Over any field K and for arbitrary natural matrix dimensions, "
                + statement,
                "proof_strategy": steps[0],
                "sketch_steps": steps,
                "openmath_xml": xml,
                "lean_target": LEAN + args + " : " + target,
                "lean_witness": "by\n  " + proof.replace("\n", "\n  "),
            }
        )

    sqargs = "{n : ℕ} (A : " + MATRIX + ")"
    pairargs = "{n : ℕ} (A B : " + MATRIX + ")"
    add(
        "det_transpose",
        "det(Aᵀ)=det A for every square A.",
        SQ,
        eq(det(trans(A)), det(A)),
        sqargs,
        "A.transpose.det = A.det",
        "exact Matrix.det_transpose A",
        [
            "Expand the determinant as a signed permutation sum.",
            "Replace each permutation by its inverse.",
            "The corresponding products of entries agree by commutativity.",
            "Inverse permutations have the same sign, proving the equality.",
        ],
    )
    diagonal = unary("diagonal", d)
    add(
        "det_diagonal",
        "det(diag d)=∏ᵢ dᵢ for every Fin n scalar family d.",
        N + [vec("d")],
        eq(det(diagonal), unary("vec_product", d)),
        "{n : ℕ} (d : Fin n → K)",
        "(Matrix.diagonal d).det = ∏ i, d i",
        "exact Matrix.det_diagonal",
        [
            "Use the permutation formula for the determinant.",
            "Every nonidentity permutation uses an off-diagonal zero entry.",
            "Only the identity permutation contributes.",
            "Its contribution is the product of diagonal entries, including the empty product when n=0.",
        ],
    )
    add(
        "det_upper_triangular",
        "An upper triangular square matrix has determinant equal to the product of its diagonal entries.",
        SQ,
        imp(
            unary("upper_triangular", A),
            eq(det(A), unary("vec_product", unary("diag_entries", A))),
        ),
        sqargs + " (h : A.BlockTriangular id)",
        "A.det = ∏ i, A i i",
        "exact Matrix.det_of_upperTriangular h",
        [
            "Use the ordering on Fin n and the vanishing entries below the diagonal.",
            "In the permutation determinant sum, a nonidentity permutation forces a zero factor.",
            "Thus only the diagonal product survives.",
            "This gives the determinant for every matrix size.",
        ],
    )
    adj = unary("adjugate", A)
    scaled = op("smul", K, n, n, det(A), ident())
    add(
        "adjugate_identity",
        "A adj(A)=det(A)I and adj(A) A=det(A)I, even for singular A.",
        SQ,
        conj(eq(mm(A, adj), scaled), eq(mm(adj, A), scaled)),
        sqargs,
        "A * A.adjugate = A.det • (1 : "
        + MATRIX
        + ") ∧ A.adjugate * A = A.det • (1 : "
        + MATRIX
        + ")",
        "exact ⟨Matrix.mul_adjugate A, Matrix.adjugate_mul A⟩",
        [
            "Compute an entry of A times its adjugate by cofactor expansion.",
            "A diagonal entry is det A; an off-diagonal entry is a determinant with repeated rows.",
            "The repeated-row determinant vanishes.",
            "The analogous column expansion proves the reverse product.",
        ],
    )
    add(
        "adjugate_product",
        "adj(AB)=adj(B)adj(A) for all square A,B.",
        PAIR,
        eq(unary("adjugate", mm(A, B)), mm(unary("adjugate", B), adj)),
        pairargs,
        "(A * B).adjugate = B.adjugate * A.adjugate",
        "exact Matrix.adjugate_mul_distrib A B",
        [
            "Apply the multiplicativity law for the adjugate.",
            "The order of the factors is reversed, as for inverses.",
            "The cofactor identity is polynomial and remains valid at singular matrices.",
            "Consequently no determinant nonvanishing assumption is needed.",
        ],
    )
    add(
        "inverse_adjugate",
        "The total nonsingular inverse satisfies A⁻¹=(det A)⁻¹•adj(A); singular matrices receive inverse zero.",
        SQ,
        eq(inv(A), op("smul", K, n, n, op("scalar_inv", K, det(A)), adj)),
        sqargs,
        "A⁻¹ = A.det⁻¹ • A.adjugate",
        "simpa only [Ring.inverse_eq_inv] using Matrix.inv_def A",
        [
            "Define the nonsingular inverse using the adjugate and scalar ring inverse.",
            "Over a field, the ring inverse is ordinary inverse with zero inverse equal to zero.",
            "Substitute that equality in the defining formula.",
            "When the determinant is zero the scalar factor and entire inverse are zero.",
        ],
    )
    add(
        "inverse_product",
        "(AB)⁻¹=B⁻¹A⁻¹ for the total nonsingular inverse of square matrices.",
        PAIR,
        eq(inv(mm(A, B)), mm(inv(B), inv(A))),
        pairargs,
        "(A * B)⁻¹ = B⁻¹ * A⁻¹",
        "exact Matrix.mul_inv_rev A B",
        [
            "When both determinants are nonzero, reverse the two ordinary inverse factors.",
            "If either determinant vanishes, multiplicativity makes AB singular.",
            "The total inverse of a singular matrix is zero.",
            "Both cases give the same reverse-product identity.",
        ],
    )
    add(
        "inverse_transpose",
        "(A⁻¹)ᵀ=(Aᵀ)⁻¹ for all square A.",
        SQ,
        eq(trans(inv(A)), inv(trans(A))),
        sqargs,
        "A⁻¹.transpose = A.transpose⁻¹",
        "exact Matrix.transpose_nonsing_inv A",
        [
            "Transpose the adjugate formula for the inverse.",
            "The determinant is unchanged by transpose.",
            "The adjugate commutes with transpose.",
            "Combine these identities without a nonsingularity assumption.",
        ],
    )
    add(
        "inverse_determinant",
        "det(A⁻¹)=(det A)⁻¹ for all square A, with total inverse.",
        SQ,
        eq(det(inv(A)), op("scalar_inv", K, det(A))),
        sqargs,
        "A⁻¹.det = A.det⁻¹",
        "simpa only [Ring.inverse_eq_inv] using Matrix.det_nonsing_inv A",
        [
            "If A is invertible, take determinants of the inverse identity.",
            "This makes the inverse determinant the reciprocal of det A.",
            "For singular A the inverse is zero, with the zero-dimensional case already invertible.",
            "Thus the field inverse convention covers all cases.",
        ],
    )
    add(
        "unit_iff_det_nonzero",
        "A square matrix is a unit exactly when its determinant is nonzero.",
        SQ,
        iff(unary("is_unit", A), ne(det(A), sc(0))),
        sqargs,
        "IsUnit A ↔ A.det ≠ 0",
        "rw [Matrix.isUnit_iff_isUnit_det, isUnit_iff_ne_zero]",
        [
            "Taking determinants maps matrix units to scalar units.",
            "Conversely an invertible determinant provides an inverse through the adjugate.",
            "A scalar in a field is a unit exactly when it is nonzero.",
            "Combine these two equivalences.",
        ],
    )
    add(
        "one_sided_inverse",
        "AB=I iff BA=I for square matrices of the same finite size.",
        PAIR,
        iff(eq(mm(A, B), ident()), eq(mm(B, A), ident())),
        pairargs,
        "A * B = 1 ↔ B * A = 1",
        "exact mul_eq_one_comm",
        [
            "A one-sided inverse forces the determinant of each matrix to be a unit.",
            "Use the adjugate to obtain a two-sided inverse.",
            "Uniqueness identifies the given one-sided inverse with it.",
            "Exchange A and B to obtain the reverse implication.",
        ],
    )
    add(
        "inverse_uniqueness",
        "If AB=I and CA=I, then B=C.",
        PAIR + [mat("C")],
        imp(conj(eq(mm(A, B), ident()), eq(mm(C, A), ident())), eq(B, C)),
        pairargs.replace("(A B :", "(A B C :") + " (h : A * B = 1) (g : C * A = 1)",
        "B = C",
        "exact Matrix.right_inv_eq_left_inv h g",
        [
            "Insert CA=I on the left of B.",
            "Reassociate C(AB).",
            "Use AB=I on the right of C.",
            "The resulting identity is B=C.",
        ],
    )
    sol = quant(
        [vec("x")],
        conj(
            eq(mv(A, x), y),
            quant([vec("y2")], imp(eq(mv(A, var("y2")), y), eq(var("y2"), x))),
        ),
        "exists",
    )
    add(
        "unique_linear_solution",
        "If det A≠0, then for every right-hand side y there is a unique vector x with Ax=y.",
        SQ + [vec("y")],
        imp(ne(det(A), sc(0)), sol),
        sqargs + " (h : A.det ≠ 0) (y : Fin n → K)",
        "∃ x : Fin n → K, A.mulVec x = y ∧ ∀ z, A.mulVec z = y → z = x",
        "have hu : IsUnit A := (Matrix.isUnit_iff_isUnit_det A).2 (isUnit_iff_ne_zero.mpr h)\nhave hs := Matrix.mulVec_surjective_iff_isUnit.mpr hu\nhave hi := Matrix.mulVec_injective_iff_isUnit.mpr hu\nobtain ⟨x, hx⟩ := hs y\nexact ⟨x, hx, fun z hz => hi (hz.trans hx.symm)⟩",
        [
            "Nonzero determinant makes A a matrix unit.",
            "The corresponding linear map on column vectors is surjective, giving a solution.",
            "It is also injective.",
            "Two solutions with the same right-hand side must therefore coincide.",
        ],
    )
    add(
        "cramer",
        "If det A≠0, then det(A)•(A⁻¹y)=cramer(A,y), where the ith Cramer entry replaces column i by y.",
        SQ + [vec("y")],
        imp(
            ne(det(A), sc(0)),
            eq(op("vec_smul", K, n, det(A), mv(inv(A), y)), op("cramer", K, n, A, y)),
        ),
        sqargs + " (y : Fin n → K) (h : A.det ≠ 0)",
        "A.det • (A⁻¹.mulVec y) = A.cramer y",
        "exact Matrix.det_smul_inv_mulVec_eq_cramer A y (isUnit_iff_ne_zero.mpr h)",
        [
            "Expand each replaced-column determinant by the replacement column.",
            "These entries form adj(A)y.",
            "Insert the adjugate formula for A⁻¹y.",
            "Multiply by det A and cancel its nonzero inverse factor.",
        ],
    )
    add(
        "det_power",
        "For every natural k, det(A^k)=(det A)^k.",
        SQ + [("k", typ("Nat"))],
        eq(det(op("pow", K, n, A, k)), op("scalar_pow", K, det(A), k)),
        sqargs + " (k : ℕ)",
        "(A ^ k).det = A.det ^ k",
        "exact Matrix.det_pow A k",
        [
            "At exponent zero both sides are one.",
            "Use induction on the arbitrary exponent.",
            "Determinant multiplicativity handles the induction step.",
            "The scalar power recursion gives the asserted equality.",
        ],
    )
    RECT = [("m", typ("Nat")), ("n", typ("Nat")), mat("A", m, n)]
    add(
        "rank_transpose",
        "Every rectangular matrix has the same rank as its transpose.",
        RECT,
        eq(rank(trans(A, m, n), n, m), rank(A, m, n)),
        "{m n : ℕ} (A : Matrix (Fin m) (Fin n) K)",
        "A.transpose.rank = A.rank",
        "exact Matrix.rank_transpose A",
        [
            "Rank is the dimension of the column span.",
            "Over a field it also equals the dimension of the row span.",
            "Transposition interchanges rows and columns.",
            "Hence the two ranks coincide, including rectangular matrices.",
        ],
    )
    PROD = [
        ("m", typ("Nat")),
        ("n", typ("Nat")),
        ("p", typ("Nat")),
        mat("A", m, n),
        mat("B", n, p),
    ]
    prod = mm(A, B, m, n, p)
    add(
        "rank_product_bounds",
        "For conformable rectangular A,B, rank(AB)≤rank A and rank(AB)≤rank B.",
        PROD,
        conj(le(rank(prod, m, p), rank(A, m, n)), le(rank(prod, m, p), rank(B, n, p))),
        "{m n p : ℕ} (A : Matrix (Fin m) (Fin n) K) (B : Matrix (Fin n) (Fin p) K)",
        "(A * B).rank ≤ A.rank ∧ (A * B).rank ≤ B.rank",
        "exact ⟨Matrix.rank_mul_le_left A B, Matrix.rank_mul_le_right A B⟩",
        [
            "View matrix multiplication as composition of linear maps.",
            "The image of the composite is contained in the image of the first matrix A.",
            "It is also a linear image of the range of B.",
            "Taking dimensions gives both bounds.",
        ],
    )
    add(
        "zero_product_rank_bound",
        "If AB=0 with A having n columns and B having n rows, then rank A+rank B≤n.",
        PROD,
        imp(eq(prod, zero(m, p)), le(plus(rank(A, m, n), rank(B, n, p)), n)),
        "{m n p : ℕ} (A : Matrix (Fin m) (Fin n) K) (B : Matrix (Fin n) (Fin p) K) (h : A * B = 0)",
        "A.rank + B.rank ≤ n",
        "simpa using Matrix.rank_add_rank_le_card_of_mul_eq_zero h",
        [
            "The equation AB=0 puts the range of B inside the kernel of A.",
            "Its dimension is at most the nullity of A.",
            "Rank-nullity for A adds this nullity to rank A to give n.",
            "Combine the inclusion bound with that equality.",
        ],
    )
    add(
        "rank_invertible_multipliers",
        "If square B is invertible, both AB and BA have the same rank as A.",
        PAIR,
        imp(
            unary("is_unit", B),
            conj(eq(rank(mm(A, B)), rank(A)), eq(rank(mm(B, A)), rank(A))),
        ),
        pairargs + " (h : IsUnit B)",
        "(A * B).rank = A.rank ∧ (B * A).rank = A.rank",
        "have hd := (Matrix.isUnit_iff_isUnit_det B).mp h\nexact ⟨Matrix.rank_mul_eq_left_of_isUnit_det B A hd, Matrix.rank_mul_eq_right_of_isUnit_det B A hd⟩",
        [
            "Multiplication by B is an isomorphism of the intermediate vector space.",
            "On the right it changes the parametrization of A’s image without changing that image.",
            "On the left it transports the image isomorphically.",
            "In both cases image dimension is preserved.",
        ],
    )
    add(
        "rank_diagonal",
        "The rank of diag d is the number of nonzero entries of d.",
        N + [vec("d")],
        eq(rank(diagonal), unary("count_nonzero", d)),
        "{n : ℕ} (d : Fin n → K)",
        "(Matrix.diagonal d).rank = Nat.card {i : Fin n // d i ≠ 0}",
        "classical\nsimpa only [Nat.card_eq_fintype_card] using Matrix.rank_diagonal d",
        [
            "Each nonzero diagonal entry contributes one nonzero coordinate-axis column.",
            "Those columns are linearly independent.",
            "Zero diagonal entries contribute zero columns.",
            "The column-span dimension is therefore the number of nonzero entries.",
        ],
    )
    add(
        "cayley_hamilton",
        "Every square matrix annihilates its characteristic polynomial: χ_A(A)=0.",
        SQ,
        eq(op("matrix_eval", K, n, A, cp(A)), zero()),
        sqargs,
        "Polynomial.aeval A A.charpoly = 0",
        "exact Matrix.aeval_self_charpoly A",
        [
            "Form the characteristic matrix XI-A over the polynomial ring.",
            "Multiply on the left by its adjugate to obtain adj(XI-A)(XI-A)=χ_A(X)I.",
            "View this as a polynomial with matrix coefficients and evaluate with powers on the right.",
            "Evaluation of the right factor XI-A telescopes term by term; no general multiplicativity of matrix-coefficient evaluation is assumed. The left side becomes zero and the right side χ_A(A).",
        ],
    )
    add(
        "charpoly_monic_degree",
        "The characteristic polynomial of an n×n matrix is monic and has natural degree n.",
        SQ,
        conj(op("poly_monic", K, cp(A)), eq(op("poly_degree", K, cp(A)), n)),
        sqargs,
        "A.charpoly.Monic ∧ A.charpoly.natDegree = n",
        "exact ⟨Matrix.charpoly_monic A, by simpa using Matrix.charpoly_natDegree_eq_dim A⟩",
        [
            "Expand det(XI-A) by permutations.",
            "The unique highest-degree contribution selects X from every diagonal factor.",
            "Its coefficient is one and its degree is n.",
            "This also covers n=0, when the polynomial is the constant one.",
        ],
    )
    scalarMat = op("smul", K, n, n, t, ident())
    negA = op("smul", K, n, n, op("scalar_neg", K, sc(1)), A)
    add(
        "charpoly_scalar_evaluation",
        "For every scalar t, χ_A(t)=det(tI-A).",
        SQ + [("t", typ("Scalar", K))],
        eq(op("poly_eval", K, cp(A), t), det(op("add", K, n, n, scalarMat, negA))),
        sqargs + " (t : K)",
        "A.charpoly.eval t = (Matrix.scalar (Fin n) t - A).det",
        "exact Matrix.eval_charpoly A t",
        [
            "Define χ_A(X) as det(XI-A).",
            "Scalar polynomial evaluation preserves sums and products.",
            "It therefore commutes with the determinant expression.",
            "Evaluating XI-A entrywise gives tI-A.",
        ],
    )
    add(
        "charpoly_transpose",
        "A and Aᵀ have identical characteristic polynomials.",
        SQ,
        eq(cp(trans(A)), cp(A)),
        sqargs,
        "A.transpose.charpoly = A.charpoly",
        "exact Matrix.charpoly_transpose A",
        [
            "Transpose the characteristic matrix XI-A.",
            "It becomes the characteristic matrix of Aᵀ.",
            "A determinant is unchanged under transposition.",
            "Thus the two characteristic polynomials agree.",
        ],
    )
    add(
        "charpoly_product_swap",
        "For square A,B of the same size, χ_(AB)=χ_(BA), even when either factor is singular.",
        PAIR,
        eq(cp(mm(A, B)), cp(mm(B, A))),
        pairargs,
        "(A * B).charpoly = (B * A).charpoly",
        "exact Matrix.charpoly_mul_comm A B",
        [
            "Apply the determinant identity comparing XI-AB and XI-BA.",
            "The two matrices have the same finite square size.",
            "The identity holds without choosing inverses.",
            "Consequently their characteristic polynomials agree also at singular factors.",
        ],
    )
    conjA = mm(mm(B, A), inv(B))
    add(
        "charpoly_similarity",
        "If B is invertible, χ_(BAB⁻¹)=χ_A.",
        PAIR,
        imp(unary("is_unit", B), eq(cp(conjA), cp(A))),
        pairargs + " (h : IsUnit B)",
        "(B * A * B⁻¹).charpoly = A.charpoly",
        "obtain ⟨u, rfl⟩ := h\nsimpa only [Matrix.coe_units_inv] using Matrix.charpoly_units_conj u A",
        [
            "The characteristic matrix of BAB⁻¹ is B(XI-A)B⁻¹.",
            "Take determinants in the polynomial matrix ring.",
            "The determinant factors for B and its inverse cancel.",
            "The remaining determinant is χ_A.",
        ],
    )
    add(
        "charpoly_diagonal",
        "The characteristic polynomial of diag d is ∏ᵢ(X-dᵢ).",
        N + [vec("d")],
        eq(cp(diagonal), unary("linear_factor_product", d)),
        "{n : ℕ} (d : Fin n → K)",
        "(Matrix.diagonal d).charpoly = ∏ i, (Polynomial.X - Polynomial.C (d i))",
        "exact Matrix.charpoly_diagonal d",
        [
            "The characteristic matrix of a diagonal matrix remains diagonal.",
            "Its ith diagonal entry is X-dᵢ.",
            "The determinant of a diagonal matrix is the product of its entries.",
            "This gives the claimed factorization, including the empty product.",
        ],
    )
    negone = op("scalar_neg", K, sc(1))
    add(
        "charpoly_recovers_det_trace",
        "det A=(-1)^n χ_A.coeff(0) and trace A=-χ_A.nextCoeff; nextCoeff is zero for constant polynomials.",
        SQ,
        conj(
            eq(
                det(A),
                op(
                    "scalar_mul",
                    K,
                    op("scalar_pow", K, negone, n),
                    op("poly_coeff", K, cp(A), nat(0)),
                ),
            ),
            eq(tr(A), op("scalar_neg", K, op("poly_next_coeff", K, cp(A)))),
        ),
        sqargs,
        "A.det = (-1 : K)^n * A.charpoly.coeff 0 ∧ A.trace = -A.charpoly.nextCoeff",
        "exact ⟨by simpa using Matrix.det_eq_sign_charpoly_coeff A, Matrix.trace_eq_neg_charpoly_nextCoeff A⟩",
        [
            "The constant coefficient comes from det(-A), giving the dimension-dependent sign.",
            "The coefficient just below the leading term selects one diagonal entry from -A.",
            "Summing these contributions gives minus the trace.",
            "Use nextCoeff’s zero convention to retain the trace identity at n=0.",
        ],
    )
    add(
        "nilpotent_charpoly",
        "If A is nilpotent, χ_A=X^n.",
        SQ,
        imp(unary("nilpotent", A), eq(cp(A), op("poly_pow", K, op("poly_X", K), n))),
        sqargs + " (h : IsNilpotent A)",
        "A.charpoly = Polynomial.X ^ n",
        "have hq := Matrix.isNilpotent_charpoly_sub_pow_of_isNilpotent h\nhave he := isNilpotent_iff_eq_zero.mp hq\nsimpa using sub_eq_zero.mp he",
        [
            "Nilpotence makes χ_A-X^n a nilpotent polynomial.",
            "A polynomial ring over a field has no nonzero nilpotents.",
            "Therefore that difference is zero.",
            "Rearrange to obtain χ_A=X^n.",
        ],
    )
    add(
        "nilpotent_trace",
        "Every nilpotent square matrix has trace zero over the field.",
        SQ,
        imp(unary("nilpotent", A), eq(tr(A), sc(0))),
        sqargs + " (h : IsNilpotent A)",
        "A.trace = 0",
        "exact isNilpotent_iff_eq_zero.mp (Matrix.isNilpotent_trace_of_isNilpotent h)",
        [
            "Nilpotence of A implies nilpotence of its trace.",
            "The trace lies in the scalar field.",
            "A field has no nonzero nilpotent scalar.",
            "Hence the trace vanishes in every characteristic.",
        ],
    )
    CYCL = [("m", typ("Nat")), ("n", typ("Nat")), mat("A", m, n), mat("B", n, m)]
    add(
        "trace_cyclic_rectangular",
        "For A of size m×n and B of size n×m, trace(AB)=trace(BA).",
        CYCL,
        eq(tr(mm(A, B, m, n, m), m), tr(mm(B, A, n, m, n), n)),
        "{m n : ℕ} (A : Matrix (Fin m) (Fin n) K) (B : Matrix (Fin n) (Fin m) K)",
        "(A * B).trace = (B * A).trace",
        "exact Matrix.trace_mul_comm A B",
        [
            "Expand the trace of AB as a double sum of entry products.",
            "Swap the finite summation order.",
            "Commute the scalar factors.",
            "The resulting double sum is the trace of BA, despite different outer dimensions.",
        ],
    )
    add(
        "similarity_det_trace",
        "Conjugation by an invertible B preserves both determinant and trace.",
        PAIR,
        imp(unary("is_unit", B), conj(eq(det(conjA), det(A)), eq(tr(conjA), tr(A)))),
        pairargs + " (h : IsUnit B)",
        "(B * A * B⁻¹).det = A.det ∧ (B * A * B⁻¹).trace = A.trace",
        "exact ⟨Matrix.det_conj h A, Matrix.trace_conj h A⟩",
        [
            "For the determinant, multiply the determinants of the three factors.",
            "Cancel the determinants of B and B⁻¹.",
            "For the trace, move the first factor to the end by cyclicity.",
            "Then cancel B⁻¹B to recover trace A.",
        ],
    )
    add(
        "transpose_product",
        "For conformable rectangular A,B, (AB)ᵀ=BᵀAᵀ.",
        PROD,
        eq(trans(prod, m, p), mm(trans(B, n, p), trans(A, m, n), p, n, m)),
        "{m n p : ℕ} (A : Matrix (Fin m) (Fin n) K) (B : Matrix (Fin n) (Fin p) K)",
        "(A * B).transpose = B.transpose * A.transpose",
        "exact Matrix.transpose_mul A B",
        [
            "Compare corresponding entries of the two matrices.",
            "Each entry of the transposed product is a sum over the common inner index.",
            "Commutativity reverses the scalar factors in each summand.",
            "The entry formulas identify the transpose with the reverse product.",
        ],
    )
    add(
        "matrix_action_composition",
        "For conformable rectangular A,B and a column vector x, (AB)x=A(Bx).",
        PROD + [vec("x", p)],
        eq(mv(prod, x, m, p), mv(A, mv(B, x, n, p), m, n)),
        "{m n p : ℕ} (A : Matrix (Fin m) (Fin n) K) (B : Matrix (Fin n) (Fin p) K) (x : Fin p → K)",
        "(A * B).mulVec x = A.mulVec (B.mulVec x)",
        "exact (Matrix.mulVec_mulVec x A B).symm",
        [
            "Expand both sides into finite sums of products of entries and coordinates.",
            "Reassociate each triple scalar product.",
            "Interchange the two finite summations.",
            "The equal coordinate formulas prove equality of vectors.",
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
    witness = ROOT / "docs/linear-algebra-v4-batch.lean"
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
                ROOT / "pals-agent/pals_agent/typed_linear_algebra_v4.py"
            ),
            "registry_sha256": sha(
                ROOT
                / "pals-agent/pals_agent/content_dictionaries/typed-linear-algebra-v4-registry.json"
            ),
            "toolchain": (WORKSPACE / "lean-toolchain").read_text().strip(),
            "mathlib_revision": next(p["rev"] for p in pkgs if p["name"] == "mathlib"),
        },
    }
    (ROOT / "docs/linear-algebra-v4-batch.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    )
    print(f"PASS: {len(cards)} arbitrary-size matrix cards compiled and canonicalized")


if __name__ == "__main__":
    main()
