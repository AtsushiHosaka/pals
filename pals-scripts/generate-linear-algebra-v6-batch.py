"""Compile general basis/coordinate/eigenvalue Drafts before authoring manifest output."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from xml.sax.saxutils import quoteattr

from pals_agent.typed_linear_algebra_v6 import (
    canonicalize_typed_linear_algebra_v6_openmath_xml as canonicalize,
)
from pals_agent.typed_linear_algebra_v6 import (
    validate_canonical_typed_linear_algebra_v6_openmath_xml as validate,
)

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / "pals-agent/lean-workspace"
PROFILE = "typed-linear-algebra-v6"
TYPED = "urn:pals:openmath:typed-linear-algebra:v6"


def sym(cd, name, base=TYPED):
    return f"<OMS cdbase={quoteattr(base)} cd={quoteattr(cd)} name={quoteattr(name)}/>"


def var(n):
    return f"<OMV name={quoteattr(n)}/>"


def app(h, *args):
    return "<OMA>" + h + "".join(args) + "</OMA>"


def op(name, *args):
    return app(sym("la6", name), *args)


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
    return op(name, *args) if args else sym("la6", name)


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
                "id": "la_v6_" + key,
                "canonical_statement": "Over any field K and finite-dimensional K-vector spaces, "
                + statement,
                "proof_strategy": steps[0],
                "sketch_steps": steps,
                "openmath_xml": xml,
                "lean_target": LEAN + args + " : " + target,
                "lean_witness": "by\n  " + proof.replace("\n", "\n  "),
            }
        )

    ne = lambda a, b: std("relation1", "neq", a, b)
    neg = lambda a: std("logic1", "not", a)
    lambda a, b: std("logic1", "or", a, b)
    vz = lambda Q=V: op("vector_zero", K, Q)
    plus = lambda a, b: op("vector_add", K, V, a, b)
    mem = lambda x, S, Q=V: op("member", K, Q, x, S)
    ker = lambda f, dom=V, cod=W: op("kernel", K, dom, cod, f)
    rng = lambda f, dom=V, cod=W: op("range", K, dom, cod, f)
    inf = lambda S, T: op("sub_inf", K, V, S, T)
    sup = lambda S, T: op("sub_sup", K, V, S, T)
    span = lambda v: op("span", K, V, n, v)
    summ = lambda v, a: op("sum_scaled", K, V, n, v, a)
    bargs = "{n : ℕ} (b : Module.Basis (Fin n) K V) "
    vf, u, i, j, t, B = map(var, ("v", "u", "i", "j", "t", "B"))
    sd = [("S", typ("Subspace", K, V)), ("T", typ("Subspace", K, V))]
    fd = [("n", typ("Nat")), ("v", typ("Family", K, V, n))]
    # The dual certificate criterion is a genuinely stronger solvability recognition result.
    ann = quant(
        [("u", typ("Vector", K, V))],
        eq(op("functional_apply", K, W, phi, apply(f, u)), op("scalar_zero", K)),
    )
    dualtest = quant(
        [("phi", typ("Functional", K, W))],
        imp(ann, eq(op("functional_apply", K, W, phi, y), op("scalar_zero", K))),
    )
    add(
        "fredholm_solvability",
        "f(x)=y is solvable exactly when every linear functional on W annihilating all outputs of f also annihilates y.",
        [sp("W"), lm("f"), ("y", typ("Vector", K, W))],
        iff(
            quant([("x", typ("Vector", K, V))], eq(apply(f, x), y), "exists"), dualtest
        ),
        ls("W") + "(f : V →ₗ[K] W) (y : W)",
        "(∃ x, f x = y) ↔ ∀ phi : W →ₗ[K] K, (∀ x, phi (f x) = 0) → phi y = 0",
        r"""change y ∈ LinearMap.range f ↔ _
  rw [← Subspace.forall_mem_dualAnnihilator_apply_eq_zero_iff (LinearMap.range f) y]
  simp only [Submodule.mem_dualAnnihilator]
  constructor
  · intro h phi hp
    apply h phi
    rintro _ ⟨x,rfl⟩
    exact hp x
  · intro h phi hp
    apply h phi
    intro x
    exact hp (f x) ⟨x,rfl⟩""".replace("\n  ", "\n"),
        [
            "A solution makes every annihilating functional vanish on y by direct substitution.",
            "Conversely these tests put y in the double annihilator of range f.",
            "A subspace over a field equals its double annihilator; the separation argument uses the quotient by that subspace.",
            "Membership in the range supplies the desired solution, giving the finite-dimensional Fredholm alternative.",
        ],
    )
    add(
        "kernel_causes_nonunique_solutions",
        "if a nonzero u lies in ker f, then for every x the distinct vector x+u has the same image as x. Thus any soluble right-hand side is nonunique.",
        [sp("W"), lm("f"), ("u", typ("Vector", K, V)), ("x", typ("Vector", K, V))],
        imp(
            conj(ne(u, vz()), eq(apply(f, u), vz(W))),
            conj(ne(plus(x, u), x), eq(apply(f, plus(x, u)), apply(f, x))),
        ),
        ls("W") + "(f : V →ₗ[K] W) (u x : V) (hu : u ≠ 0) (hk : f u = 0)",
        "x+u ≠ x ∧ f (x+u) = f x",
        "constructor\n· intro h; apply hu; exact add_left_cancel (show x+u=x+0 by simpa using h)\n· simp [map_add,hk]",
        [
            "Choose an arbitrary solution vector x.",
            "Adding a kernel vector leaves its image unchanged by linearity.",
            "If x+u=x, additive cancellation would force u=0.",
            "The assumed nonzero kernel vector therefore constructs a distinct solution for every soluble right-hand side.",
        ],
    )
    md = [
        ("n", typ("Nat")),
        ("m", typ("Nat")),
        ("A", typ("Matrix", K, n, m)),
        ("B", typ("Matrix", K, m, n)),
    ]
    matvec = lambda M, v, r, s: op("matrix_vec", K, r, s, M, v)
    ident = lambda n: op("matrix_identity", K, n)
    add(
        "left_inverse_detects_injective_action",
        "if A B=I on Kⁿ for rectangular A:n×m and B:m×n, then Bx=By forces x=y; a left inverse certifies uniqueness of input coordinates.",
        md,
        imp(
            eq(mm(A, B, n, m, n), ident(n)),
            quant(
                [("x", typ("Coordinates", K, n)), ("y", typ("Coordinates", K, n))],
                imp(eq(matvec(B, x, m, n), matvec(B, y, m, n)), eq(x, y)),
            ),
        ),
        "{n m : ℕ} (A : Matrix (Fin n) (Fin m) K) (B : Matrix (Fin m) (Fin n) K) (h : A*B=1)",
        "Function.Injective B.mulVec",
        "intro x y hxy\nhave he := congrArg A.mulVec hxy\nsimpa only [Matrix.mulVec_mulVec, h, Matrix.one_mulVec] using he",
        [
            "Start from an equality of two outputs of B.",
            "Apply the known left inverse A to that equality.",
            "Associativity combines the two matrix actions as AB.",
            "The identity action recovers equality of the input vectors.",
        ],
    )
    ri = [
        ("n", typ("Nat")),
        ("i", typ("Index", n)),
        ("j", typ("Index", n)),
        ("t", typ("Scalar", K)),
    ]
    E = op("matrix_single", K, n, n, i, j, t)
    F = op("matrix_single", K, n, n, j, i, op("scalar_one", K))
    add(
        "matrix_units_noncommute",
        "for distinct i,j and nonzero t, the matrices tEᵢⱼ and Eⱼᵢ have unequal products in opposite orders, in every size admitting those indices.",
        ri,
        imp(conj(ne(i, j), ne(t, op("scalar_zero", K))), ne(mm(E, F), mm(F, E))),
        "{n : ℕ} (i j : Fin n) (t : K) (h : i ≠ j) (ht : t ≠ 0)",
        "(Matrix.single i j t : Matrix (Fin n) (Fin n) K) * Matrix.single j i 1 ≠ Matrix.single j i 1 * Matrix.single i j t",
        "intro he\nhave hh := congrArg (fun M : Matrix (Fin n) (Fin n) K => M i i) he\napply ht\nsimpa [Matrix.single_mul_single_same, h, h.symm] using hh",
        [
            "Multiplying the matrix units in the first order places t in diagonal entry i.",
            "Multiplying in the reverse order places t in diagonal entry j.",
            "These indices are distinct, so the reverse product has zero at (i,i).",
            "The nonzero coefficient witnesses failure of commutativity.",
        ],
    )
    k = var("k")
    N = var("N")
    I = ident(n)
    Z = op("matrix_zero", K, n, n)
    G = op("matrix_geom_sum", K, n, N, k)
    IN = op("matrix_sub", K, n, n, I, N)
    add(
        "nilpotent_geometric_inverse",
        "if N^k=0, the finite geometric sum I+N+⋯+N^(k−1) is a two-sided inverse of I−N. This works for arbitrary natural k without a commutativity assumption on matrices.",
        [("n", typ("Nat")), ("k", typ("Nat")), ("N", typ("Matrix", K, n, n))],
        imp(
            eq(op("matrix_pow", K, n, N, k), Z),
            conj(eq(mm(IN, G), I), eq(mm(G, IN), I)),
        ),
        "{n k : ℕ} (N : Matrix (Fin n) (Fin n) K) (h : N^k=0)",
        "(1-N)*(∑ j ∈ Finset.range k, N^j)=1 ∧ (∑ j ∈ Finset.range k, N^j)*(1-N)=1",
        "constructor\n· simpa [h] using mul_neg_geom_sum N k\n· simpa [h] using geom_sum_mul_neg N k",
        [
            "Expand the product of I−N with the finite geometric sum.",
            "Successive powers cancel telescopically, leaving I−N^k.",
            "Nilpotency changes this remainder into I.",
            "The same telescoping in reverse multiplication order proves both inverse identities, including the degenerate k=0 case under its premise.",
        ],
    )
    add(
        "subspace_sum_membership",
        "x lies in S+T exactly when x=s+t for some s∈S and t∈T.",
        sd + [("x", typ("Vector", K, V))],
        iff(
            mem(x, sup(S, T)),
            quant(
                [("u", typ("Vector", K, V)), ("y", typ("Vector", K, V))],
                conj(mem(u, S), conj(mem(y, T), eq(plus(u, y), x))),
                "exists",
            ),
        ),
        "(S T : Submodule K V) (x : V)",
        "x ∈ S ⊔ T ↔ ∃ u ∈ S, ∃ y ∈ T, u+y=x",
        "exact Submodule.mem_sup",
        [
            "The set of all sums of a vector in S and one in T is a subspace.",
            "It contains both S and T by adding zero.",
            "Every subspace containing S and T contains all these sums.",
            "The least such subspace is S+T, yielding the membership criterion.",
        ],
    )
    add(
        "incomparable_union_not_closed",
        "if neither S⊆T nor T⊆S, there are u∈S and y∈T whose sum belongs to neither S nor T; their union fails closure under addition.",
        sd,
        imp(
            conj(neg(op("sub_le", K, V, S, T)), neg(op("sub_le", K, V, T, S))),
            quant(
                [("u", typ("Vector", K, V)), ("y", typ("Vector", K, V))],
                conj(
                    mem(u, S),
                    conj(
                        mem(y, T),
                        conj(neg(mem(plus(u, y), S)), neg(mem(plus(u, y), T))),
                    ),
                ),
                "exists",
            ),
        ),
        "(S T : Submodule K V) (hST : ¬ S ≤ T) (hTS : ¬ T ≤ S)",
        "∃ u ∈ S, ∃ y ∈ T, u+y ∉ S ∧ u+y ∉ T",
        "obtain ⟨u,hu,huT⟩ := SetLike.not_le_iff_exists.mp hST\nobtain ⟨y,hy,hyS⟩ := SetLike.not_le_iff_exists.mp hTS\nrefine ⟨u,hu,y,hy,?_,?_⟩\n· intro h; apply hyS; simpa using S.sub_mem h hu\n· intro h; apply huT; simpa using T.sub_mem h hy",
        [
            "Choose u in S but outside T, and y in T but outside S.",
            "If u+y lay in S, subtracting u would put y in S, a contradiction.",
            "If u+y lay in T, subtracting y would put u in T, also a contradiction.",
            "Both summands lie in the union but their sum does not.",
        ],
    )
    image = lambda S: op("sub_map", K, V, W, f, S)
    add(
        "injective_images_preserve_intersection",
        "an injective linear map takes intersections of subspaces to intersections of their images.",
        [sp("W"), lm("f")] + sd,
        imp(
            op("injective", K, V, W, f),
            eq(image(inf(S, T)), op("sub_inf", K, W, image(S), image(T))),
        ),
        ls("W") + "(f : V →ₗ[K] W) (hf : Function.Injective f) (S T : Submodule K V)",
        "(S ⊓ T).map f = S.map f ⊓ T.map f",
        "exact Submodule.map_inf f hf",
        [
            "An image of a vector in both subspaces lies in both images.",
            "Conversely choose preimages in S and T of a common image vector.",
            "Injectivity identifies these two preimages.",
            "The common preimage lies in S∩T and produces the reverse inclusion.",
        ],
    )
    independent = op("independent", K, V, n, vf)
    rel = quant(
        [("a", typ("Coordinates", K, n))],
        imp(eq(summ(vf, a), vz()), eq(a, op("coordinate_zero", K, n))),
    )
    add(
        "independence_zero_coefficients",
        "a finite family is linearly independent exactly when every zero linear combination has every coefficient zero.",
        fd,
        iff(independent, rel),
        "{n : ℕ} (v : Fin n → V)",
        "LinearIndependent K v ↔ ∀ a : Fin n → K, (∑ i, a i • v i)=0 → a=0",
        "rw [Fintype.linearIndependent_iff]\nsimp only [funext_iff, Pi.zero_apply]",
        [
            "Translate the finite family into its coefficient-to-vector linear map.",
            "Independence says the kernel of that map is zero.",
            "A coefficient family is in this kernel exactly when its linear combination vanishes.",
            "Thus the only zero combination has the zero coefficient function.",
        ],
    )
    add(
        "span_construct_coefficients",
        "a vector in the span of a finite family has coefficients giving it as a finite linear combination, and conversely.",
        fd + [("x", typ("Vector", K, V))],
        iff(
            mem(x, span(vf)),
            quant([("a", typ("Coordinates", K, n))], eq(summ(vf, a), x), "exists"),
        ),
        "{n : ℕ} (v : Fin n → V) (x : V)",
        "x ∈ Submodule.span K (Set.range v) ↔ ∃ a : Fin n → K, ∑ i, a i • v i = x",
        "exact Submodule.mem_span_range_iff_exists_fun K",
        [
            "The coefficient-to-vector map sends a to its finite combination.",
            "Its range is the span of the family.",
            "A span member therefore has a preimage coefficient function.",
            "Conversely every such finite combination lies in the span.",
        ],
    )
    at = lambda v, i: op("family_at", K, V, n, v, i)
    add(
        "repeated_vector_dependence",
        "a finite vector family with equal entries at two distinct indices is not linearly independent; pairwise nonzero vectors alone do not prevent this defect.",
        fd + [("i", typ("Index", n)), ("j", typ("Index", n))],
        imp(conj(ne(i, j), eq(at(vf, i), at(vf, j))), neg(independent)),
        "{n : ℕ} (v : Fin n → V) (i j : Fin n) (hij : i ≠ j) (hv : v i = v j)",
        "¬ LinearIndependent K v",
        "intro h\nexact hij (h.injective hv)",
        [
            "Select the two equal vectors at different indices.",
            "Independence over a field makes the family indexing function injective.",
            "Their equality would force the two indices to coincide.",
            "This contradicts distinctness and detects the repeated-vector dependence.",
        ],
    )
    add(
        "independence_under_restricted_injection",
        "if span(v) meets ker f only at zero, the image family f(vᵢ) is linearly independent exactly when v is; global injectivity of f is unnecessary.",
        fd + [sp("W"), lm("f")],
        imp(
            op("disjoint", K, V, span(vf), ker(f)),
            iff(op("independent", K, W, n, images(f, vf)), independent),
        ),
        ls("W")
        + "{n : ℕ} (v : Fin n → V) (f : V →ₗ[K] W) (h : Disjoint (Submodule.span K (Set.range v)) (LinearMap.ker f))",
        "LinearIndependent K (fun i => f (v i)) ↔ LinearIndependent K v",
        "exact f.linearIndependent_iff_of_disjoint h",
        [
            "A relation among image vectors is the image of a relation among the original vectors.",
            "The latter sum lies both in span(v) and in ker f.",
            "Their trivial intersection forces that sum to be zero, so original independence kills its coefficients.",
            "For the converse any original zero relation maps to an image relation; no control of f away from span(v) is needed.",
        ],
    )
    existence = quant([bs("b")], eq(bv(b), vf), "exists")
    add(
        "basis_recognition",
        "a Fin n family is the vector family of some basis exactly when it is independent and spans the whole space.",
        fd,
        iff(existence, conj(independent, eq(span(vf), op("sub_top", K, V)))),
        "{n : ℕ} (v : Fin n → V)",
        "(∃ b : Module.Basis (Fin n) K V, (fun i => b i)=v) ↔ LinearIndependent K v ∧ Submodule.span K (Set.range v)=⊤",
        "constructor\n· rintro ⟨b,rfl⟩; exact ⟨b.linearIndependent,b.span_eq⟩\n· rintro ⟨hi,hs⟩\n  exact ⟨Module.Basis.mk hi hs.ge, by simp⟩",
        [
            "A basis provides both independent vectors and a spanning family.",
            "Conversely spanning gives a representation of each vector.",
            "Independence makes that representation unique.",
            "The representation equivalence constructs a basis with exactly the supplied vectors.",
        ],
    )
    upd = op("family_update", K, V, n, bv(b), i, vz())
    add(
        "zeroing_basis_vector_loses_span",
        "replacing any one vector of a basis by zero produces a same-length family whose span omits the replaced vector; having the right number of vectors is not sufficient for a basis.",
        BN + [("i", typ("Index", n))],
        neg(mem(at(bv(b), i), span(upd))),
        bargs + "(i : Fin n)",
        "b i ∉ Submodule.span K (Set.range (Function.update (fun j => b j) i 0))",
        "intro hm\nhave hs : Submodule.span K (Set.range (Function.update (fun j => b j) i 0)) ≤ LinearMap.ker (b.coord i) := by\n  apply Submodule.span_le.mpr\n  rintro _ ⟨j,rfl⟩\n  by_cases hj : j=i\n  · subst j; simp\n  · simp [LinearMap.mem_ker, Function.update_of_ne hj, Ne.symm hj]\nhave hh := hs hm\nsimp [LinearMap.mem_ker] at hh",
        [
            "Use the ith coordinate functional of the original basis.",
            "It annihilates every vector in the modified family: the ith is zero, all other basis vectors have ith coordinate zero.",
            "Therefore it annihilates the whole modified span.",
            "Its value on the removed basis vector is one, so that vector cannot belong to the new span.",
        ],
    )
    add(
        "nonzero_translation_not_linear",
        "translation by any nonzero vector u cannot agree with a linear endomorphism on all vectors.",
        [("u", typ("Vector", K, V))],
        imp(
            ne(u, vz()),
            neg(
                quant(
                    [lm("f", V, V)],
                    quant(
                        [("x", typ("Vector", K, V))], eq(apply(f, x, V, V), plus(x, u))
                    ),
                    "exists",
                )
            ),
        ),
        "(u : V) (hu : u ≠ 0)",
        "¬ ∃ f : V →ₗ[K] V, ∀ x, f x = x+u",
        "rintro ⟨f,hf⟩\napply hu\nsimpa using (hf 0).symm",
        [
            "Every linear map sends the zero vector to zero.",
            "A translation sends zero to its translation vector u.",
            "Agreement with a linear map would force u=0.",
            "The nonzero hypothesis therefore gives a general family of nonlinear affine maps.",
        ],
    )
    proj = lambda i: op("basis_projection", K, V, n, b, i)
    fi, gj = proj(i), proj(j)
    zm = op("zero_map", K, V, V)
    add(
        "nonzero_maps_zero_composite",
        "coordinate projections onto two distinct vectors of a basis are both nonzero but their composite is zero; a zero composite does not force either factor to vanish.",
        BN + [("i", typ("Index", n)), ("j", typ("Index", n))],
        imp(
            ne(i, j), conj(ne(fi, zm), conj(ne(gj, zm), eq(comp(gj, fi, V, V, V), zm)))
        ),
        bargs + "(i j : Fin n) (hij : i ≠ j)",
        "let p := (b.coord i).smulRight (b i); let q := (b.coord j).smulRight (b j); p ≠ 0 ∧ q ≠ 0 ∧ p.comp q = 0",
        "dsimp only\nconstructor\n· intro hp; have h := congrArg (fun f : V →ₗ[K] V => f (b i)) hp; exact b.ne_zero i (by simpa using h)\nconstructor\n· intro hq; have h := congrArg (fun f : V →ₗ[K] V => f (b j)) hq; exact b.ne_zero j (by simpa using h)\next x\nsimp [hij]",
        [
            "The ith projection fixes the ith basis vector, so it is nonzero.",
            "Likewise the jth projection is nonzero.",
            "The jth projection lands in the jth basis line, whose ith coordinate is zero.",
            "Their composite vanishes on every vector despite both factors being nonzero.",
        ],
    )
    add(
        "idempotent_kernel_range_decomposition",
        "an idempotent linear map splits the whole space as the direct sum of its range and kernel.",
        [lm("f", V, V)],
        imp(
            eq(comp(f, f, V, V, V), f),
            op("complementary", K, V, rng(f, V, V), ker(f, V, V)),
        ),
        "(f : V →ₗ[K] V) (hf : f.comp f=f)",
        "IsCompl (LinearMap.range f) (LinearMap.ker f)",
        "have h : IsIdempotentElem f := hf\nexact LinearMap.IsIdempotentElem.isCompl h",
        [
            "For every x, write x=f(x)+(x−f(x)).",
            "The first summand lies in the range, and idempotency puts the second in the kernel.",
            "A vector in both the range and the kernel is fixed by f and also sent to zero, hence is zero.",
            "These spanning and trivial-intersection statements give the direct-sum decomposition.",
        ],
    )
    BA = mm(B, A, m, n, m)
    AB = mm(A, B, n, m, n)
    IAB = op("matrix_add", K, n, n, ident(n), AB)
    IBA = op("matrix_add", K, m, m, ident(m), BA)
    add(
        "rectangular_determinant_transfer",
        "for rectangular A:n×m and B:m×n, det(Iₙ+AB)=det(Iₘ+BA); consequently one of these square systems is invertible exactly when the other is, even when m≠n.",
        md,
        conj(
            eq(op("matrix_det", K, n, IAB), op("matrix_det", K, m, IBA)),
            iff(op("matrix_isunit", K, n, IAB), op("matrix_isunit", K, m, IBA)),
        ),
        "{n m : ℕ} (A : Matrix (Fin n) (Fin m) K) (B : Matrix (Fin m) (Fin n) K)",
        "(1+A*B).det=(1+B*A).det ∧ (IsUnit (1+A*B) ↔ IsUnit (1+B*A))",
        "constructor\n· exact Matrix.det_one_add_mul_comm A B\n· rw [Matrix.isUnit_iff_isUnit_det, Matrix.isUnit_iff_isUnit_det, Matrix.det_one_add_mul_comm]",
        [
            "Form the block matrix with identity diagonal blocks and off-diagonal A and B.",
            "Eliminating one block or the other gives the rectangular Sylvester determinant identity.",
            "Over a field, each square matrix is invertible exactly when its determinant is nonzero.",
            "The equal determinants transfer solvability and uniqueness for all right-hand sides between the two different-sized systems.",
        ],
    )
    return cards


def sha(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    cards = build_cards()
    assert len(cards) >= 15
    assert len({c["openmath_xml"] for c in cards}) == len(cards)
    assert all(4 <= len(c["sketch_steps"]) <= 10 for c in cards)
    witness = ROOT / "docs/linear-algebra-v6-batch.lean"
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
                ROOT / "pals-agent/pals_agent/typed_linear_algebra_v6.py"
            ),
            "registry_sha256": sha(
                ROOT
                / "pals-agent/pals_agent/content_dictionaries/typed-linear-algebra-v6-registry.json"
            ),
            "toolchain": (WORKSPACE / "lean-toolchain").read_text().strip(),
            "mathlib_revision": next(p["rev"] for p in pkgs if p["name"] == "mathlib"),
        },
    }
    (ROOT / "docs/linear-algebra-v6-batch.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    )
    print(
        f"PASS: {len(cards)} basis/coordinate/eigenvalue cards compiled and canonicalized"
    )


if __name__ == "__main__":
    main()
