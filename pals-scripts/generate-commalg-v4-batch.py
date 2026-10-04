"""Author general prime-spectrum/extension cards; compile exact witnesses before JSON."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pals-agent"))
from pals_agent.typed_commalg_v4 import (
    CDBASE,
    PROFILE_ID,
    canonicalize_typed_commalg_v4_openmath_xml,
    validate_canonical_typed_commalg_v4_openmath_xml,
)


def sym(cd, name):
    base = "http://www.openmath.org/cd" if cd in {"logic1", "relation1"} else CDBASE
    return f'<OMS cdbase="{base}" cd="{cd}" name="{name}"/>'


def v(name):
    return f'<OMV name="{name}"/>'


def app(cd, name, *args):
    return "<OMA>" + sym(cd, name) + "".join(args) + "</OMA>"


def op(name, *args):
    return app("spectrum4", name, *args)


def eq(a, b):
    return app("relation1", "eq", a, b)


def log(name, *args):
    return app("logic1", name, *args)


def And(*args):
    return log("and", *args)


def iff(a, b):
    return And(log("implies", a, b), log("implies", b, a))


def bind(kind, ds, body):
    return (
        "<OMBIND>"
        + sym("typed1", kind)
        + "<OMBVAR>"
        + "".join(
            "<OMATTR><OMATP>"
            + sym("typed1", "type")
            + sort
            + "</OMATP>"
            + v(name)
            + "</OMATTR>"
            for name, sort in ds
        )
        + "</OMBVAR>"
        + body
        + "</OMBIND>"
    )


def ideal(r, name):
    return name, op("Ideal", r)


def elem(r, name):
    return name, op("Element", r)


def point(r, name):
    return name, op("Prime", r)


def subset(r, name):
    return name, op("SpecSet", r)


def morph(r, s, name):
    return name, op("RingHom", r, s)


R, S, I, J, T, U, p, q, x, y, f, A, B, M = map(
    v, ["R", "S", "I", "J", "T", "U", "p", "q", "x", "y", "f", "A", "B", "M"]
)


def V(r, i):
    return op("zero_locus", r, i)


def D(r, x):
    return op("basic_open", r, x)


def rad(r, i):
    return op("ideal_radical", r, i)


def idealof(r, p):
    return op("prime_ideal", r, p)


def comap(r, s, f, i):
    return op("comap_ideal", r, s, f, i)


def smap(r, s, f):
    return op("spec_comap", r, s, f)


def amap(r, s):
    return op("algebra_map", r, s)


def le(r, i, j):
    return op("ideal_le", r, i, j)


def prime(r, i):
    return op("is_prime", r, i)


def dim(r):
    return op("dimension", r)


def specprop(name, r, s, fn):
    return op(name, s, r, smap(r, s, fn))


CARDS = []


def card(
    key, rings, extra, premises, result, statement, steps, target, proof, algebra=False
):
    ds = [("R", sym("spectrum4", "CommRing"))]
    if "S" in rings:
        ds += [("S", op("Algebra", R) if algebra else sym("spectrum4", "CommRing"))]
    ds += extra
    for premise in reversed(premises):
        result = log("implies", premise, result)
    raw = (
        '<OMOBJ xmlns="http://www.openmath.org/OpenMath" version="2.0">'
        + bind("forall", ds, result)
        + "</OMOBJ>"
    )
    xml = canonicalize_typed_commalg_v4_openmath_xml(raw)
    validate_canonical_typed_commalg_v4_openmath_xml(xml)
    lean = "example {R : Type*} [CommRing R] "
    if "S" in rings:
        lean += "{S : Type*} [CommRing S] " + ("[Algebra R S] " if algebra else "")
    assert 4 <= len(steps) <= 10
    CARDS.append(
        {
            "id": "commalg_v4_" + key,
            "canonical_statement": statement,
            "proof_strategy": steps[1],
            "sketch_steps": steps,
            "openmath_xml": xml,
            "lean_target": lean + target,
            "lean_witness": "by\n" + proof,
        }
    )


card(
    "vanishing_galois",
    "R",
    [ideal(R, "I"), subset(R, "T")],
    [],
    iff(op("set_subset", R, T, V(R, I)), le(R, I, op("vanishing_ideal", R, T))),
    "For any commutative ring R, ideal I and subset T of Spec R, T⊆V(I) if and only if I is contained in the ideal of elements vanishing on all primes in T.",
    [
        "Fix I and T.",
        "Expand vanishing as membership in each prime ideal in T.",
        "Both containments assert that each element of I lies in each prime of T.",
        "Reorder the universal quantifiers to obtain the equivalence.",
    ],
    "(I : Ideal R) (T : Set (PrimeSpectrum R)) : T ⊆ PrimeSpectrum.zeroLocus I ↔ I ≤ PrimeSpectrum.vanishingIdeal T",
    "  exact PrimeSpectrum.subset_zeroLocus_iff_le_vanishingIdeal T I",
)
card(
    "zero_locus_vanishing_closure",
    "R",
    [subset(R, "T")],
    [],
    eq(V(R, op("vanishing_ideal", R, T)), op("closure", R, T)),
    "For any commutative ring R and subset T of Spec R, V of the vanishing ideal of T is exactly the Zariski closure of T.",
    [
        "Fix an arbitrary subset T, not necessarily closed.",
        "Closed sets of Spec R are zero loci.",
        "The vanishing ideal determines the smallest zero locus containing T.",
        "This smallest closed superset is the closure of T.",
    ],
    "(T : Set (PrimeSpectrum R)) : PrimeSpectrum.zeroLocus (PrimeSpectrum.vanishingIdeal T) = closure T",
    "  exact PrimeSpectrum.zeroLocus_vanishingIdeal_eq_closure T",
)
card(
    "vanishing_zero_locus_radical",
    "R",
    [ideal(R, "I")],
    [],
    eq(op("vanishing_ideal", R, V(R, I)), rad(R, I)),
    "For any commutative ring R and ideal I, the ideal vanishing on V(I) is the radical of I.",
    [
        "Take the intersection of all primes containing I.",
        "Every prime containing I contains its radical.",
        "Prime ideal separation detects any element outside the radical.",
        "The intersection is therefore exactly the radical.",
    ],
    "(I : Ideal R) : PrimeSpectrum.vanishingIdeal (PrimeSpectrum.zeroLocus I) = I.radical",
    "  exact PrimeSpectrum.vanishingIdeal_zeroLocus_eq_radical I",
)
for key, idealop, setop, ln in [
    ("zero_locus_sum", "ideal_sum", "set_intersection", "sup"),
    ("zero_locus_product", "ideal_product", "set_union", "mul"),
]:
    card(
        key,
        "R",
        [ideal(R, "I"), ideal(R, "J")],
        [],
        eq(V(R, op(idealop, R, I, J)), op(setop, R, V(R, I), V(R, J))),
        (
            "For ideals I,J of any commutative ring, V(I+J)=V(I)∩V(J)."
            if ln == "sup"
            else "For ideals I,J of any commutative ring, V(IJ)=V(I)∪V(J)."
        ),
        [
            "Fix two ideals and test membership at an arbitrary prime.",
            "Use the defining containment condition of a zero locus.",
            (
                "Containing I+J means containing both I and J."
                if ln == "sup"
                else "Primality implies that a prime containing IJ contains at least one of I,J."
            ),
            "Translate the pointwise condition into equality of subsets of Spec R.",
        ],
        f"(I J : Ideal R) : PrimeSpectrum.zeroLocus ((I {'⊔' if ln == 'sup' else '*'} J : Ideal R) : Set R) = PrimeSpectrum.zeroLocus I {'∩' if ln == 'sup' else '∪'} PrimeSpectrum.zeroLocus J",
        f"  exact PrimeSpectrum.zeroLocus_{ln} I J",
    )
card(
    "closed_sets_zero_loci",
    "R",
    [subset(R, "T")],
    [],
    iff(op("is_closed", R, T), bind("exists", [ideal(R, "I")], eq(T, V(R, I)))),
    "For any commutative ring R, a subset T of Spec R is Zariski closed if and only if T=V(I) for some ideal I of R.",
    [
        "Use the definition of the Zariski closed sets by vanishing of ring elements.",
        "Replace any set of equations by the ideal it generates.",
        "The zero locus is unchanged by taking this generated ideal.",
        "Conversely every ideal zero locus is closed.",
    ],
    "(T : Set (PrimeSpectrum R)) : IsClosed T ↔ ∃ I : Ideal R, T = PrimeSpectrum.zeroLocus I",
    "  exact PrimeSpectrum.isClosed_iff_zeroLocus_ideal T",
)
card(
    "closure_prime_point",
    "R",
    [point(R, "p")],
    [],
    eq(op("closure", R, op("singleton", R, p)), V(R, idealof(R, p))),
    "For any prime p in Spec R, the closure of {p} is V(p), the primes containing p.",
    [
        "View the point p as its underlying prime ideal.",
        "The vanishing ideal of a singleton point is that prime ideal.",
        "The general closure formula applies to the singleton.",
        "Thus its specializations are exactly the primes containing p.",
    ],
    "(p : PrimeSpectrum R) : closure ({p} : Set (PrimeSpectrum R)) = PrimeSpectrum.zeroLocus p.asIdeal",
    "  exact PrimeSpectrum.closure_singleton p",
)
card(
    "closed_point_maximal",
    "R",
    [point(R, "p")],
    [],
    iff(op("is_closed", R, op("singleton", R, p)), op("is_maximal", R, idealof(R, p))),
    "A point of Spec R is closed if and only if its underlying prime ideal is maximal.",
    [
        "The closure of a prime point is the set of primes above it.",
        "A maximal ideal has no strictly larger prime ideal.",
        "Conversely every proper ideal lies below a maximal ideal.",
        "The singleton is closed precisely when the prime is maximal.",
    ],
    "(p : PrimeSpectrum R) : IsClosed ({p} : Set (PrimeSpectrum R)) ↔ p.asIdeal.IsMaximal",
    "  exact PrimeSpectrum.isClosed_singleton_iff_isMaximal p",
)
card(
    "irreducible_zero_locus",
    "R",
    [ideal(R, "I")],
    [],
    iff(op("is_irreducible", R, V(R, I)), prime(R, rad(R, I))),
    "For any ideal I of a commutative ring R, V(I) is nonempty and irreducible if and only if the radical of I is prime.",
    [
        "Replace I by its radical without changing its zero locus.",
        "A union decomposition of a zero locus corresponds to a product condition on ideals.",
        "Primality excludes nontrivial such decompositions and ensures nonemptiness.",
        "Conversely irreducibility forces the radical to satisfy the prime product condition.",
    ],
    "(I : Ideal R) : IsIrreducible (PrimeSpectrum.zeroLocus (I : Set R)) ↔ I.radical.IsPrime",
    "  exact PrimeSpectrum.isIrreducible_zeroLocus_iff I",
)
card(
    "basic_open_quasicompact",
    "R",
    [elem(R, "x")],
    [],
    op("is_compact", R, D(R, x)),
    "For any commutative ring R and x∈R, the basic open D(x) in Spec R is quasi-compact.",
    [
        "Identify D(x) with the spectrum of the localization at powers of x.",
        "The spectrum of a ring is quasi-compact.",
        "The canonical localization map is continuous with image D(x).",
        "Its image is therefore quasi-compact, without requiring a Hausdorff topology.",
    ],
    "(x : R) : IsCompact (PrimeSpectrum.basicOpen x : Set (PrimeSpectrum R))",
    "  exact PrimeSpectrum.isCompact_basicOpen x",
)
card(
    "basic_open_empty_nilpotent",
    "R",
    [elem(R, "x")],
    [],
    iff(eq(D(R, x), op("empty", R)), op("nilpotent", R, x)),
    "For any commutative ring R, D(x) is empty if and only if x is nilpotent.",
    [
        "D(x) is empty exactly when x lies in every prime ideal.",
        "The intersection of all prime ideals is the nilradical.",
        "Membership in the nilradical is equivalent to nilpotence.",
        "Combine the two equivalences.",
    ],
    "(x : R) : (PrimeSpectrum.basicOpen x : Set (PrimeSpectrum R)) = ∅ ↔ IsNilpotent x",
    "  simpa only [← TopologicalSpace.Opens.coe_bot, TopologicalSpace.Opens.coe_inj] using PrimeSpectrum.basicOpen_eq_bot_iff x",
)
card(
    "basic_open_inclusion_radical",
    "R",
    [elem(R, "x"), elem(R, "y")],
    [],
    iff(
        op("set_subset", R, D(R, x), D(R, y)),
        op("ideal_member", R, x, rad(R, op("principal", R, y))),
    ),
    "For x,y in any commutative ring R, D(x)⊆D(y) if and only if x belongs to the radical of the principal ideal (y).",
    [
        "Take complements of the two basic opens.",
        "Their reversed inclusion is an inclusion of principal zero loci.",
        "Zero-locus containment is detected by radical containment.",
        "For the principal ideal generated by x this is membership of x in √(y).",
    ],
    "(x y : R) : (PrimeSpectrum.basicOpen x : Set (PrimeSpectrum R)) ⊆ PrimeSpectrum.basicOpen y ↔ x ∈ (Ideal.span ({y} : Set R)).radical",
    "  exact PrimeSpectrum.basicOpen_le_basicOpen_iff x y",
)
card(
    "clopen_unique_idempotent",
    "R",
    [subset(R, "T")],
    [op("is_clopen", R, T)],
    bind(
        "exists",
        [elem(R, "x")],
        And(
            op("idempotent", R, x),
            eq(T, D(R, x)),
            bind(
                "forall",
                [elem(R, "y")],
                log("implies", And(op("idempotent", R, y), eq(T, D(R, y))), eq(y, x)),
            ),
        ),
    ),
    "For any commutative ring R, every clopen subset T of Spec R is D(e) for a unique idempotent e∈R.",
    [
        "Use quasi-compactness on the complementary open and closed pieces.",
        "Construct complementary ring elements with product zero and sum one.",
        "Their product and sum identities make the element defining T idempotent.",
        "Equality of basic opens for idempotents forces equality of their defining elements.",
    ],
    "(T : Set (PrimeSpectrum R)) (hT : IsClopen T) : ∃ x : R, IsIdempotentElem x ∧ T = PrimeSpectrum.basicOpen x ∧ ∀ y : R, IsIdempotentElem y ∧ T = PrimeSpectrum.basicOpen y → y = x",
    "  obtain ⟨x, hx, huniq⟩ := PrimeSpectrum.existsUnique_idempotent_basicOpen_eq_of_isClopen hT\n  exact ⟨x, hx.1, hx.2, huniq⟩",
)
card(
    "spectrum_t0",
    "R",
    [],
    [],
    op("spec_t0", R),
    "The Zariski spectrum of every commutative ring is a T0 topological space.",
    [
        "Two distinct spectrum points are distinct prime ideals.",
        "Choose an element belonging to exactly one of those ideals.",
        "Its basic open contains exactly one of the points.",
        "This separates distinct points in the T0 sense.",
    ],
    ": T0Space (PrimeSpectrum R)",
    "  infer_instance",
)
card(
    "spectrum_nonempty_nontrivial",
    "R",
    [],
    [],
    iff(op("spec_nonempty", R), op("nontrivial", R)),
    "For any commutative ring R, Spec R is nonempty if and only if R is nontrivial.",
    [
        "A prime ideal is proper, so its existence excludes the zero ring.",
        "In a nontrivial unital ring the zero ideal is proper.",
        "A maximal ideal above it exists and is prime.",
        "These implications give the equivalence.",
    ],
    ": Nonempty (PrimeSpectrum R) ↔ Nontrivial R",
    "  exact PrimeSpectrum.nonempty_iff_nontrivial",
)

card(
    "spectrum_comap_continuous",
    "RS",
    [morph(R, S, "f")],
    [],
    specprop("continuous", R, S, f),
    "Every unital ring homomorphism f:R→S induces a continuous contraction map Spec S→Spec R.",
    [
        "The induced map contracts a prime ideal along f.",
        "The preimage of a zero locus is the zero locus of the extended equations.",
        "Zero loci are closed in the Zariski topology.",
        "Preimages of closed sets are closed, proving continuity.",
    ],
    "(f : R →+* S) : Continuous (PrimeSpectrum.comap f)",
    "  exact PrimeSpectrum.continuous_comap f",
)
card(
    "spectrum_preimage_zero_locus",
    "RS",
    [morph(R, S, "f"), ideal(R, "I")],
    [],
    eq(op("spec_preimage", R, S, f, V(R, I)), V(S, op("map_ideal", R, S, f, I))),
    "For any unital ring homomorphism f:R→S and ideal I of R, the inverse image of V(I) under Spec S→Spec R is V(IS), where IS is ideal extension along f.",
    [
        "A prime of S lies in the inverse image exactly when its contraction contains I.",
        "By extension-contraction adjunction this means it contains the ideal generated by f(I).",
        "That extended ideal is I.map f.",
        "Apply the zero-locus membership definition pointwise.",
    ],
    "(f : R →+* S) (I : Ideal R) : (PrimeSpectrum.comap f) ⁻¹' PrimeSpectrum.zeroLocus I = PrimeSpectrum.zeroLocus (I.map f)",
    "  ext p\n  change I ≤ p.asIdeal.comap f ↔ I.map f ≤ p.asIdeal\n  exact Ideal.map_le_iff_le_comap.symm",
)
card(
    "surjective_map_closed_embedding",
    "RS",
    [morph(R, S, "f")],
    [op("ring_surjective", R, S, f)],
    specprop("closed_embedding", R, S, f),
    "A surjective unital ring homomorphism R→S induces a closed topological embedding Spec S→Spec R.",
    [
        "Surjectivity makes contraction injective on prime ideals.",
        "It also identifies the induced topology with the topology on Spec S.",
        "The image is the closed set cut out by the kernel.",
        "Together these properties give a closed embedding.",
    ],
    "(f : R →+* S) (hf : Function.Surjective f) : Topology.IsClosedEmbedding (PrimeSpectrum.comap f)",
    "  exact PrimeSpectrum.isClosedEmbedding_comap_of_surjective S f hf",
)
card(
    "spectrum_range_closure",
    "RS",
    [morph(R, S, "f")],
    [],
    eq(op("closure", R, op("spec_range", R, S, f)), V(R, op("ring_kernel", R, S, f))),
    "For every unital ring homomorphism f:R→S, the closure of the image of Spec S→Spec R is V(ker f); surjectivity and integrality are not required.",
    [
        "Compute the ideal vanishing on the contracted prime ideals of S.",
        "That ideal is the radical of the kernel of f.",
        "Apply the formula expressing closure as a zero locus of the vanishing ideal.",
        "Taking a radical does not change the zero locus, so the answer is V(ker f).",
    ],
    "(f : R →+* S) : closure (Set.range (PrimeSpectrum.comap f)) = PrimeSpectrum.zeroLocus (RingHom.ker f)",
    "  exact PrimeSpectrum.closure_range_comap f",
)
L = op("localization", R, M)
lm = op("localization_map", R, M)
card(
    "localization_spectrum_embedding",
    "R",
    [("M", op("Submonoid", R))],
    [],
    specprop("embedding", R, L, lm),
    "For any multiplicative submonoid M of a commutative ring R, the canonical map Spec(M⁻¹R)→Spec R is a topological embedding.",
    [
        "The canonical ring homomorphism contracts prime ideals to R.",
        "Extension and contraction show injectivity on spectrum points.",
        "Zero-locus preimages determine the induced topology.",
        "Thus the spectrum of the localization has the subspace topology on its image.",
    ],
    "(M : Submonoid R) : Topology.IsEmbedding (PrimeSpectrum.comap (algebraMap R (Localization M)))",
    "  exact PrimeSpectrum.localization_comap_isEmbedding (Localization M) M",
)
Lx = op("away", R, x)
lx = op("away_map", R, x)
card(
    "localization_away_basic_open",
    "R",
    [elem(R, "x")],
    [],
    And(
        specprop("open_embedding", R, Lx, lx), eq(op("spec_range", R, Lx, lx), D(R, x))
    ),
    "For any x in a commutative ring R, Spec(R[1/x])→Spec R is an open embedding with image D(x).",
    [
        "The localized spectrum embeds into Spec R.",
        "A prime occurs in its image exactly when it avoids all powers of x.",
        "Primality makes this equivalent to not containing x, which defines D(x).",
        "Since D(x) is open, this embedding is an open embedding.",
    ],
    "(x : R) : Topology.IsOpenEmbedding (PrimeSpectrum.comap (algebraMap R (Localization.Away x))) ∧ Set.range (PrimeSpectrum.comap (algebraMap R (Localization.Away x))) = PrimeSpectrum.basicOpen x",
    "  exact ⟨PrimeSpectrum.localization_away_isOpenEmbedding (Localization.Away x) x, PrimeSpectrum.localization_away_comap_range (Localization.Away x) x⟩",
)
QI = op("quotient", R, I)
qm = op("quotient_map", R, I)
card(
    "nil_quotient_spectrum_homeomorphism",
    "R",
    [ideal(R, "I")],
    [le(R, I, op("nilradical", R))],
    specprop("homeomorphism", R, QI, qm),
    "For any ideal I contained in the nilradical of a commutative ring R, the quotient map induces a homeomorphism Spec(R/I)→Spec R.",
    [
        "Every prime ideal contains I by the nilradical assumption.",
        "The quotient contraction map is therefore surjective as well as injective.",
        "Surjectivity of the ring quotient makes this map a closed embedding.",
        "A bijective closed embedding is a homeomorphism.",
    ],
    "(I : Ideal R) (hI : I ≤ nilradical R) : IsHomeomorph (PrimeSpectrum.comap (Ideal.Quotient.mk I))",
    "  exact isHomeomorph_iff_isEmbedding_surjective.mpr ⟨(PrimeSpectrum.isClosedEmbedding_comap_of_surjective (R ⧸ I) (Ideal.Quotient.mk I) Ideal.Quotient.mk_surjective).isEmbedding, (PrimeSpectrum.comap_quotientMk_bijective_of_le_nilradical hI).2⟩",
)

card(
    "integral_spectrum_closed_map",
    "RS",
    [morph(R, S, "f")],
    [op("ring_integral", R, S, f)],
    specprop("closed_map", R, S, f),
    "Every integral unital ring homomorphism f:R→S induces a closed map Spec S→Spec R, without an injectivity assumption.",
    [
        "Represent a closed subset of Spec S by a zero locus.",
        "Integrality persists after passing to the relevant quotients.",
        "The lying-over theorem identifies its image as a zero locus of a contracted ideal.",
        "Hence every closed subset has closed image.",
    ],
    "(f : R →+* S) (hf : f.IsIntegral) : IsClosedMap (PrimeSpectrum.comap f)",
    "  exact PrimeSpectrum.isClosedMap_comap_of_isIntegral f hf",
)
card(
    "integral_lying_over",
    "RS",
    [morph(R, S, "f")],
    [op("ring_integral", R, S, f), op("ring_injective", R, S, f)],
    specprop("spec_surjective", R, S, f),
    "For every injective integral unital ring homomorphism f:R→S, every prime ideal of R is the contraction of a prime ideal of S.",
    [
        "Fix an arbitrary prime of R.",
        "Injectivity ensures that the kernel obstruction to lying over vanishes.",
        "Apply lying over for the integral extension.",
        "The resulting prime of S maps to the chosen prime of R.",
    ],
    "(f : R →+* S) (hf : f.IsIntegral) (hinj : Function.Injective f) : Function.Surjective (PrimeSpectrum.comap f)",
    "  exact hf.comap_surjective hinj",
)
AM = amap(R, S)
card(
    "integral_going_up",
    "RS",
    [ideal(R, "I"), ideal(S, "J")],
    [op("integral", R, S), prime(R, I), prime(S, J), le(R, comap(R, S, AM, J), I)],
    bind(
        "exists",
        [ideal(S, "U")],
        And(le(S, J, U), prime(S, U), eq(comap(R, S, AM, U), I)),
    ),
    "For an integral commutative R-algebra S, a prime I of R and a prime J of S with contraction(J)⊆I, there exists a prime U⊇J of S whose contraction equals I (going up).",
    [
        "Retain integrality and primality of the two given ideals.",
        "Pass to the quotient by J and its contracted ideal.",
        "Apply lying over to the resulting integral extension and target prime.",
        "Pull the resulting prime back to S to obtain U containing J.",
    ],
    "[Algebra.IsIntegral R S] (I : Ideal R) (J : Ideal S) [I.IsPrime] [J.IsPrime] (h : J.comap (algebraMap R S) ≤ I) : ∃ U : Ideal S, J ≤ U ∧ U.IsPrime ∧ U.comap (algebraMap R S) = I",
    "  exact Ideal.exists_ideal_over_prime_of_isIntegral_of_isPrime I J h",
    algebra=True,
)
card(
    "integral_incomparability",
    "RS",
    [ideal(S, "I"), ideal(S, "J")],
    [op("integral", R, S), prime(S, I), op("ideal_lt", S, I, J)],
    op("ideal_lt", R, comap(R, S, AM, I), comap(R, S, AM, J)),
    "For an integral commutative R-algebra S, if I is a prime ideal of S and I⊊J for an ideal J, then contraction(I)⊊contraction(J); in particular distinct comparable primes cannot have the same contraction.",
    [
        "Choose an element of J outside the prime I.",
        "Its integral equation descends to the domain S/I.",
        "The equation supplies a coefficient in the contraction of J outside the contraction of I.",
        "Thus the contraction inclusion is strict.",
    ],
    "[Algebra.IsIntegral R S] (I J : Ideal S) [I.IsPrime] (h : I < J) : I.comap (algebraMap R S) < J.comap (algebraMap R S)",
    "  exact Ideal.IsIntegral.comap_lt_comap h",
    algebra=True,
)
card(
    "integral_maximal_equivalence",
    "RS",
    [morph(R, S, "f"), ideal(S, "I")],
    [op("ring_integral", R, S, f), prime(S, I)],
    iff(op("is_maximal", S, I), op("is_maximal", R, comap(R, S, f, I))),
    "For an integral ring homomorphism f:R→S and a prime ideal I of S, I is maximal if and only if its contraction is maximal.",
    [
        "Contracting a maximal ideal under an integral map gives a maximal ideal.",
        "For the converse, keep primality of I as an explicit assumption.",
        "Integrality forces strict ideal extension above I to give strict contraction.",
        "Maximality of the contracted ideal then makes I maximal.",
    ],
    "(f : R →+* S) (hf : f.IsIntegral) (I : Ideal S) [I.IsPrime] : I.IsMaximal ↔ (I.comap f).IsMaximal",
    "  constructor\n  · intro hI\n    letI := hI\n    exact Ideal.isMaximal_comap_of_isIntegral_of_isMaximal' f hf I\n  · exact Ideal.isMaximal_of_isIntegral_of_isMaximal_comap' f hf I",
)
card(
    "integral_extension_proper",
    "RS",
    [morph(R, S, "f"), ideal(R, "I")],
    [op("ring_integral", R, S, f), le(R, op("ring_kernel", R, S, f), I)],
    iff(eq(op("map_ideal", R, S, f, I), op("ideal_top", S)), eq(I, op("ideal_top", R))),
    "For an integral ring homomorphism f:R→S and ideal I containing ker f, its extension equals S if and only if I=R; thus proper such ideals stay proper.",
    [
        "The whole ideal certainly extends to the whole ideal.",
        "A proper I lies in a maximal ideal of R.",
        "The kernel assumption and integrality provide a maximal ideal of S lying above it.",
        "This maximal ideal contains the extension of I, so the extension is proper.",
    ],
    "(f : R →+* S) (hf : f.IsIntegral) (I : Ideal R) (hI : RingHom.ker f ≤ I) : I.map f = ⊤ ↔ I = ⊤",
    "  exact Ideal.map_eq_top_iff_of_ker_le f hI hf",
)
for key, assumptions, leanassumptions, statement, setup in [
    (
        "going_down_normal_domain",
        [
            op("domain", R),
            op("domain", S),
            op("integrally_closed", R),
            op("integral", R, S),
            op("ring_injective", R, S, AM),
        ],
        "[IsDomain R] [IsDomain S] [IsIntegrallyClosed R] [Algebra.IsIntegral R S] (hinj : Function.Injective (algebraMap R S))",
        "For an injective integral extension of commutative domains R→S with R integrally closed, primes p⊆q of R and a prime Q of S contracting to q admit a prime P⊆Q contracting to p (going down).",
        "  letI : FaithfulSMul R S := (faithfulSMul_iff_algebraMap_injective R S).mpr hinj\n",
    ),
    (
        "going_down_flat",
        [op("flat", R, S)],
        "[Module.Flat R S]",
        "For any flat commutative R-algebra S, primes p⊆q of R and a prime Q of S contracting to q admit a prime P⊆Q contracting to p (going down); integrality is not assumed.",
        "",
    ),
]:
    card(
        key,
        "RS",
        [ideal(R, "I"), ideal(R, "J"), ideal(S, "U")],
        assumptions
        + [
            prime(R, I),
            prime(R, J),
            prime(S, U),
            eq(comap(R, S, AM, U), J),
            le(R, I, J),
        ],
        bind(
            "exists",
            [ideal(S, "T")],
            And(le(S, T, U), prime(S, T), eq(comap(R, S, AM, T), I)),
        ),
        statement,
        [
            "Fix the lower and upper primes and a prime over the upper one.",
            "Use the stated ring-theoretic hypotheses to obtain the going-down property.",
            "Apply going down to the prime containment in the base ring.",
            "Read the resulting prime containment and contraction equality in S.",
        ],
        leanassumptions
        + " (I J : Ideal R) (U : Ideal S) [I.IsPrime] [J.IsPrime] [U.IsPrime] (hU : U.comap (algebraMap R S) = J) (hIJ : I ≤ J) : ∃ T : Ideal S, T ≤ U ∧ T.IsPrime ∧ T.comap (algebraMap R S) = I",
        setup
        + "  letI : U.LiesOver J := (Ideal.liesOver_iff U J).mpr hU.symm\n  obtain ⟨T, hTU, hT, hTI⟩ := Ideal.exists_ideal_le_liesOver_of_le U hIJ\n  exact ⟨T, hTU, hT, (Ideal.liesOver_iff T I).mp hTI |>.symm⟩",
        algebra=True,
    )
card(
    "dimension_surjective_map",
    "RS",
    [morph(R, S, "f")],
    [op("ring_surjective", R, S, f)],
    op("dimension_le", dim(S), dim(R)),
    "For any surjective ring homomorphism R→S, the Krull dimension of S is at most the Krull dimension of R, including infinite dimensions and the zero ring convention.",
    [
        "Contract a strict chain of prime ideals in S to R.",
        "Surjectivity ensures distinct primes have distinct contractions.",
        "Thus contraction preserves strictness and chain length.",
        "Taking the supremum of all chain lengths gives the dimension inequality.",
    ],
    "(f : R →+* S) (hf : Function.Surjective f) : ringKrullDim S ≤ ringKrullDim R",
    "  exact ringKrullDim_le_of_surjective f hf",
)
card(
    "dimension_polynomial_noetherian",
    "R",
    [],
    [op("noetherian", R)],
    eq(dim(op("polynomial", R)), op("dimension_successor", dim(R))),
    "For any commutative Noetherian ring R, dim R[X]=dim R+1, with dimension taken in WithBot ℕ∞ so that zero and infinite-dimensional cases use the same formula.",
    [
        "Retain the Noetherian hypothesis on R.",
        "Prime-chain arguments give the lower bound from adjoining one indeterminate.",
        "The Noetherian height theorem supplies the matching upper bound.",
        "The two bounds establish equality in the extended dimension order.",
    ],
    "[IsNoetherianRing R] : ringKrullDim (Polynomial R) = ringKrullDim R + 1",
    "  exact Polynomial.ringKrullDim_of_isNoetherianRing",
)
card(
    "dimension_localization_height",
    "R",
    [point(R, "p")],
    [],
    eq(dim(op("at_prime", R, p)), op("height", R, idealof(R, p))),
    "For every prime ideal p of a commutative ring R, the Krull dimension of the local ring R_p equals the height of p, allowing infinite height.",
    [
        "The prime ideals of R_p correspond to primes of R contained in p.",
        "This correspondence preserves and reflects strict chains.",
        "The maximal ideal of R_p corresponds to p itself.",
        "The supremum of the chain lengths is both dim R_p and the height of p.",
    ],
    "(p : PrimeSpectrum R) : ringKrullDim (Localization.AtPrime p.asIdeal) = p.asIdeal.height",
    "  exact IsLocalization.AtPrime.ringKrullDim_eq_height p.asIdeal (Localization.AtPrime p.asIdeal)",
)


def digest(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert len(CARDS) >= 30
    assert len({c["id"] for c in CARDS}) == len(CARDS)
    assert len({c["openmath_xml"] for c in CARDS}) == len(CARDS)
    witness = ROOT / "docs/commalg-v4-batch.lean"
    witness.write_text(
        "import Mathlib\n\n"
        + "\n\n".join(
            "-- manifest card: "
            + c["id"]
            + "\n"
            + c["lean_target"]
            + " := "
            + c["lean_witness"].rstrip()
            for c in CARDS
        )
        + "\n"
    )
    workspace = ROOT / "pals-agent/lean-workspace"
    subprocess.run(
        [str(Path.home() / ".elan/bin/lake"), "env", "lean", str(witness)],
        cwd=workspace,
        check=True,
        timeout=180,
    )
    revision = next(
        p["rev"]
        for p in json.loads((workspace / "lake-manifest.json").read_text())["packages"]
        if p["name"] == "mathlib"
    )
    evidence = {
        "witness_path": str(witness.relative_to(ROOT)),
        "witness_sha256": digest(witness),
        "toolchain": (workspace / "lean-toolchain").read_text().strip(),
        "mathlib_revision": revision,
        "validator_sha256": digest(ROOT / "pals-agent/pals_agent/typed_commalg_v4.py"),
        "registry_sha256": digest(
            ROOT
            / "pals-agent/pals_agent/content_dictionaries/typed-commalg-v4-registry.json"
        ),
    }
    (ROOT / "docs/commalg-v4-batch.json").write_text(
        json.dumps(
            {
                "schema_version": "pals.typed-catalog-expansion-batch.v1",
                "profile_id": PROFILE_ID,
                "cards": CARDS,
                "evidence": evidence,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    print("compiled cards", len(CARDS))


if __name__ == "__main__":
    main()
