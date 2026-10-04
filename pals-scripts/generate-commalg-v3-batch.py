"""Build new commalg-v3 cards and compile their exact witnesses before JSON emission."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pals-agent"))
from pals_agent.typed_commalg_v3 import (
    CDBASE,
    PROFILE_ID,
    canonicalize_typed_commalg_v3_openmath_xml,
    validate_canonical_typed_commalg_v3_openmath_xml,
)


def sym(cd, name):
    base = "http://www.openmath.org/cd" if cd in {"logic1", "relation1"} else CDBASE
    return f'<OMS cdbase="{base}" cd="{cd}" name="{name}"/>'


def var(n):
    return f'<OMV name="{n}"/>'


def app(cd, name, *args):
    return "<OMA>" + sym(cd, name) + "".join(args) + "</OMA>"


R, M, N, L, X, U, V, W, I, f, g, h = map(
    var, ["R", "M", "N", "L", "X", "U", "V", "W", "I", "f", "g", "h"]
)


def op(name, *args):
    return app("module3", name, R, *args)


def eq(a, b):
    return app("relation1", "eq", a, b)


def logic(name, *args):
    return app("logic1", name, *args)


def iff(a, b):
    return logic("and", logic("implies", a, b), logic("implies", b, a))


def bind(kind, declarations, body):
    return (
        "<OMBIND>"
        + sym("typed1", kind)
        + "<OMBVAR>"
        + "".join(
            "<OMATTR><OMATP>"
            + sym("typed1", "type")
            + sort
            + "</OMATP>"
            + var(name)
            + "</OMATTR>"
            for name, sort in declarations
        )
        + "</OMBVAR>"
        + body
        + "</OMBIND>"
    )


def sub(module, name):
    return name, op("Submodule", module)


def linear(name, source, target):
    return name, op("LinearMap", source, target)


def top(module):
    return op("submodule_top", module)


def bot(module):
    return op("submodule_bot", module)


def q(module, submodule):
    return op("quotient", module, submodule)


def mk(module, submodule):
    return op("quotient_map", module, submodule)


def carrier(module, submodule):
    return op("submodule_carrier", module, submodule)


def ker(source, target, fn):
    return op("kernel", source, target, fn)


def ran(source, target, fn):
    return op("range", source, target, fn)


def comp(source, middle, target, first, second):
    return op("compose", source, middle, target, first, second)


def tensor(a, b):
    return op("tensor", a, b)


def lmap(factor, source, target, fn):
    return op("tensor_map_left", factor, source, target, fn)


CARDS = []


def add(
    key,
    modules,
    extra,
    premises,
    conclusion,
    statement,
    strategy,
    steps,
    target,
    proof,
    local=False,
):
    declarations = [("R", sym("module3", "LocalRing" if local else "CommRing"))]
    declarations += [(name, op("Module")) for name in modules.split()]
    declarations += extra
    body = conclusion
    for p in reversed(premises):
        body = logic("implies", p, body)
    raw = (
        '<OMOBJ xmlns="http://www.openmath.org/OpenMath" version="2.0">'
        + bind("forall", declarations, body)
        + "</OMOBJ>"
    )
    xml = canonicalize_typed_commalg_v3_openmath_xml(raw)
    validate_canonical_typed_commalg_v3_openmath_xml(xml)
    lean = "example {R : Type*} [CommRing R] "
    if local:
        lean += "[IsLocalRing R] "
    for name in modules.split():
        lean += f"{{{name} : Type*}} [AddCommGroup {name}] [Module R {name}] "
    assert 4 <= len(steps) <= 10
    CARDS.append(
        {
            "id": "commalg_v3_" + key,
            "canonical_statement": statement,
            "proof_strategy": strategy,
            "sketch_steps": steps,
            "openmath_xml": xml,
            "lean_target": lean + target,
            "lean_witness": "by\n" + proof,
        }
    )


P, Q, S, b, k = map(var, ["P", "Q", "S", "b", "k"])


def hom(a, c):
    return op("hom", a, c)


def prod(a, c):
    return op("product", a, c)


def loc(a):
    return op("localized_module", a, S)


def lm(a):
    return op("localization_map", a, S)


def lf(a, c, fn):
    return op("localized_map", a, c, S, fn)


def lu(a, u):
    return op("localized_submodule", a, S, u)


def pre(a, c, d, fn):
    return op("hom_precompose", a, c, d, fn)


def post(a, c, d, fn):
    return op("hom_postcompose", a, c, d, fn)


def curry(a, c, d, fn):
    return op("tensor_curry", a, c, d, fn)


def lift(a, c, d, fn):
    return op("tensor_lift", a, c, d, fn)


def inj(a, c, fn):
    return op("injective", a, c, fn)


def surj(a, c, fn):
    return op("surjective", a, c, fn)


def exact(a, c, d, fn, gn):
    return op("exact", a, c, d, fn, gn)


def both(a, c):
    return logic("and", a, c)


def card(key, modules, extra, assumptions, result, statement, steps, target, proof):
    add(
        key,
        modules,
        extra,
        assumptions,
        result,
        statement,
        steps[1],
        steps,
        target,
        proof,
    )


card(
    "noetherian_iff_fg",
    "M",
    [],
    [],
    iff(op("noetherian", M), bind("forall", [sub(M, "U")], op("fg", M, U))),
    "For any commutative ring R and R-module M, M is Noetherian if and only if every submodule of M is finitely generated.",
    [
        "Fix the ring and module without any finiteness assumption.",
        "Use the equivalence between the ascending chain condition and finite generation of all submodules.",
        "The forward direction applies Noetherianity to an arbitrary submodule.",
        "The reverse direction reconstructs Noetherianity from this universal finite-generation condition.",
    ],
    ": IsNoetherian R M ↔ ∀ U : Submodule R M, U.FG",
    "  exact isNoetherian_def",
)
for kind, lean in [("noetherian", "IsNoetherian"), ("artinian", "IsArtinian")]:
    card(
        kind + "_submodule_quotient",
        "M",
        [sub(M, "U")],
        [],
        iff(op(kind, M), both(op(kind, carrier(M, U)), op(kind, q(M, U)))),
        f"For any commutative ring R, R-module M and submodule U, M is {kind.title()} if and only if both U and M/U are {kind.title()}.",
        [
            "Fix an arbitrary submodule U of M.",
            f"{kind.title()} modules pass the chain condition to submodules and quotients.",
            "For the converse, use the exact sequence U → M → M/U.",
            "Combine the two chain conditions to obtain the condition on the middle module.",
        ],
        f"(U : Submodule R M) : {lean} R M ↔ {lean} R U ∧ {lean} R (M ⧸ U)",
        f"  exact is{kind.title()}_iff_submodule_quotient U",
    )
    card(
        kind + "_exact_extension",
        "M N P",
        [linear("f", M, N), linear("g", N, P)],
        [op(kind, M), op(kind, P), exact(M, N, P, f, g)],
        op(kind, N),
        f"For any commutative ring R and exact pair M → N → P of R-linear maps, if M and P are {kind.title()}, then N is {kind.title()}; neither endpoint map is required to be injective or surjective.",
        [
            "Fix the exact pair f and g.",
            "Exactness identifies the image of f with the kernel of g.",
            f"The end modules supply {kind.title()} chain conditions on the image and quotient portions.",
            "Apply closure of the chain condition under extensions.",
        ],
        f"[ {lean} R M] [{lean} R P] (f : M →ₗ[R] N) (g : N →ₗ[R] P) (h : Function.Exact f g) : {lean} R N",
        f"  exact is{kind.title()}_of_range_eq_ker f g h.linearMap_ker_eq.symm",
    )
    card(
        kind + "_product",
        "M N",
        [],
        [op(kind, M), op(kind, N)],
        op(kind, prod(M, N)),
        f"For any commutative ring R, the product of two {kind.title()} R-modules is {kind.title()}.",
        [
            "Fix the two modules with their chain conditions.",
            "Embed the first factor and project onto the second.",
            "This produces an exact sequence with the two factors as endpoints.",
            "Closure under extensions gives the chain condition on their product.",
        ],
        f"[{lean} R M] [{lean} R N] : {lean} R (M × N)",
        "  infer_instance",
    )
card(
    "noetherian_surjective_endomorphism",
    "M",
    [linear("f", M, M)],
    [op("noetherian", M), surj(M, M, f)],
    inj(M, M, f),
    "Every surjective linear endomorphism of a Noetherian module over a commutative ring is injective.",
    [
        "Fix a surjective endomorphism of a Noetherian module.",
        "Ascending kernels of the iterates eventually stabilize.",
        "Use surjectivity to lift an element of the kernel through a sufficiently high iterate.",
        "Stabilization forces that element to be zero, proving injectivity.",
    ],
    "[IsNoetherian R M] (f : M →ₗ[R] M) (hf : Function.Surjective f) : Function.Injective f",
    "  exact IsNoetherian.injective_of_surjective_endomorphism f hf",
)
card(
    "artinian_injective_endomorphism",
    "M",
    [linear("f", M, M)],
    [op("artinian", M), inj(M, M, f)],
    surj(M, M, f),
    "Every injective linear endomorphism of an Artinian module over a commutative ring is surjective.",
    [
        "Fix an injective endomorphism of an Artinian module.",
        "Descending ranges of its iterates eventually stabilize.",
        "Injectivity allows cancellation of the stabilized iterate.",
        "The range of the original map must equal the whole module.",
    ],
    "[IsArtinian R M] (f : M →ₗ[R] M) (hf : Function.Injective f) : Function.Surjective f",
    "  exact IsArtinian.surjective_of_injective_endomorphism f hf",
)
card(
    "noetherian_hom",
    "M N",
    [],
    [op("finite", M), op("noetherian", N)],
    op("noetherian", hom(M, N)),
    "For any commutative ring R, if M is finitely generated and N is Noetherian, then Hom_R(M,N) is Noetherian.",
    [
        "Choose a finite generating family of M.",
        "Evaluation on these generators embeds Hom_R(M,N) into a finite product of copies of N.",
        "That finite product is Noetherian.",
        "Its embedded submodule Hom_R(M,N) is therefore Noetherian.",
    ],
    "[Module.Finite R M] [IsNoetherian R N] : IsNoetherian R (M →ₗ[R] N)",
    "  infer_instance",
)
card(
    "noetherian_ring_finite_module",
    "M",
    [],
    [op("noetherian", op("scalar_module")), op("finite", M)],
    op("noetherian", M),
    "For any commutative Noetherian ring R, every finitely generated R-module M is Noetherian.",
    [
        "Choose a finite generating set of M.",
        "Obtain a surjective linear map from a finite free R-module onto M.",
        "Finite free modules over a Noetherian ring are Noetherian.",
        "Pass the ascending chain condition through the surjection.",
    ],
    "[IsNoetherianRing R] [Module.Finite R M] : IsNoetherian R M",
    "  infer_instance",
)
card(
    "finite_length_iff_chain_conditions",
    "M",
    [],
    [],
    iff(op("finite_length", M), both(op("noetherian", M), op("artinian", M))),
    "For any commutative ring R and R-module M, M has finite composition length if and only if M is both Noetherian and Artinian.",
    [
        "Interpret finite length as the existence of a finite composition series.",
        "A finite composition series forces ascending and descending chains to stabilize.",
        "Conversely, use both chain conditions to build and terminate a composition series.",
        "Combine these implications into the equivalence.",
    ],
    ": IsFiniteLength R M ↔ IsNoetherian R M ∧ IsArtinian R M",
    "  exact isFiniteLength_iff_isNoetherian_isArtinian",
)

SD = [("S", op("Submonoid"))]
LMS = lambda name: f"(LocalizedModule.mkLinearMap S {name})"
LF = lambda a, c, fn: f"(IsLocalizedModule.map S {LMS(a)} {LMS(c)} {fn})"
for name, lean in [("injective", "Injective"), ("surjective", "Surjective")]:
    card(
        "localization_preserves_" + name,
        "M N",
        SD + [linear("f", M, N)],
        [op(name, M, N, f)],
        op(name, loc(M), loc(N), lf(M, N, f)),
        f"For any commutative ring R and multiplicative submonoid S, localization at S preserves {name} R-linear maps of modules.",
        [
            "Use the canonical localization maps into fractions.",
            "The induced map sends x/s to f(x)/s.",
            (
                "Clear denominators and apply injectivity to an equality of fractions."
                if name == "injective"
                else "Lift the numerator of an arbitrary target fraction using surjectivity."
            ),
            "This proves the required property of the induced localized map.",
        ],
        f"(S : Submonoid R) (f : M →ₗ[R] N) (hf : Function.{lean} f) : Function.{lean} {LF('M', 'N', 'f')}",
        f"  exact IsLocalizedModule.map_{name} S {LMS('M')} {LMS('N')} f hf",
    )
card(
    "localization_exact",
    "M N P",
    SD + [linear("f", M, N), linear("g", N, P)],
    [exact(M, N, P, f, g)],
    exact(loc(M), loc(N), loc(P), lf(M, N, f), lf(N, P, g)),
    "For any commutative ring R and multiplicative submonoid S, localizing any exact pair M → N → P yields an exact pair S⁻¹M → S⁻¹N → S⁻¹P.",
    [
        "Fix the exact pair and a common multiplicative subset.",
        "A localized element in the kernel becomes a kernel element after multiplication by a denominator.",
        "Exactness before localization provides a preimage numerator.",
        "The resulting fraction identifies the localized kernel with the localized image.",
    ],
    f"(S : Submonoid R) (f : M →ₗ[R] N) (g : N →ₗ[R] P) (h : Function.Exact f g) : Function.Exact {LF('M', 'N', 'f')} {LF('N', 'P', 'g')}",
    "  exact LocalizedModule.map_exact S f g h",
)
for name in ["kernel", "range"]:
    a = M if name == "kernel" else N
    kxml = ker(M, N, f) if name == "kernel" else ran(M, N, f)
    result = (ker if name == "kernel" else ran)(loc(M), loc(N), lf(M, N, f))
    ln = "ker" if name == "kernel" else "range"
    card(
        "localization_" + name,
        "M N",
        SD + [linear("f", M, N)],
        [],
        eq(result, lu(a, kxml)),
        f"For any commutative ring R, multiplicative submonoid S and linear map f:M→N, the {name} of the localized map equals the localization of the {name} of f, as an R-submodule of the corresponding localized module.",
        [
            "Fix f and the same multiplicative submonoid on both modules.",
            "Describe the localized submodule by fractions with numerators in the original submodule.",
            (
                "Clear denominators when the image of a fraction is zero."
                if name == "kernel"
                else "A fraction in the image has a numerator in the original range, and conversely."
            ),
            "Use equality of membership conditions to identify the two submodules.",
        ],
        f"(S : Submonoid R) (f : M →ₗ[R] N) : LinearMap.{ln} {LF('M', 'N', 'f')} = (LinearMap.{ln} f).localized₀ S {LMS('M' if name == 'kernel' else 'N')}",
        f"  exact LinearMap.{ln}_localizedMap_eq_localized₀_{ln} S {LMS('M')} {LMS('N')} f",
    )
card(
    "localization_composition",
    "M N P",
    SD + [linear("f", M, N), linear("g", N, P)],
    [],
    eq(
        lf(M, P, comp(M, N, P, f, g)),
        comp(loc(M), loc(N), loc(P), lf(M, N, f), lf(N, P, g)),
    ),
    "For any commutative ring R and multiplicative submonoid S, localizing the composition g∘f of linear maps equals composing their localizations.",
    [
        "Fix composable maps and the canonical module localizations.",
        "Represent an arbitrary localized element as x/s.",
        "Both composites send that fraction to g(f(x))/s.",
        "Extensionality of linear maps gives equality.",
    ],
    f"(S : Submonoid R) (f : M →ₗ[R] N) (g : N →ₗ[R] P) : {LF('M', 'P', '(g.comp f)')} = {LF('N', 'P', 'g')}.comp {LF('M', 'N', 'f')}",
    f"  exact IsLocalizedModule.map_comp' S {LMS('M')} {LMS('N')} {LMS('P')} f g",
)
card(
    "localization_naturality",
    "M N",
    SD + [linear("f", M, N)],
    [],
    eq(comp(M, loc(M), loc(N), lm(M), lf(M, N, f)), comp(M, N, loc(N), f, lm(N))),
    "For any commutative ring R, multiplicative submonoid S and R-linear f:M→N, the canonical maps x↦x/1 commute with f and its localization.",
    [
        "Fix the canonical maps from the two modules to their localizations.",
        "The induced map sends each fraction x/s to f(x)/s.",
        "On x/1 this is precisely the canonical image of f(x).",
        "Equality on all elements gives the commutative square of linear maps.",
    ],
    f"(S : Submonoid R) (f : M →ₗ[R] N) : {LF('M', 'N', 'f')}.comp {LMS('M')} = {LMS('N')}.comp f",
    f"  exact IsLocalizedModule.map_comp S {LMS('M')} {LMS('N')} f",
)
card(
    "localization_intersection",
    "M",
    SD + [sub(M, "U"), sub(M, "V")],
    [],
    eq(
        lu(M, op("submodule_inf", M, U, V)),
        op("submodule_inf", loc(M), lu(M, U), lu(M, V)),
    ),
    "For any commutative ring R, multiplicative submonoid S and submodules U,V of M, localization preserves the intersection U∩V, viewed as an R-submodule of S⁻¹M.",
    [
        "One inclusion follows directly from numerators in the intersection.",
        "For the reverse inclusion, represent the same fraction by numerators in U and V.",
        "Clear their denominators and the resulting equality denominator to get a numerator in both.",
        "This common numerator proves equality with the intersection of localized submodules.",
    ],
    f"(S : Submonoid R) (U V : Submodule R M) : (U ⊓ V).localized₀ S {LMS('M')} = U.localized₀ S {LMS('M')} ⊓ V.localized₀ S {LMS('M')}",
    f"  exact Submodule.localized₀_inf S {LMS('M')} U V",
)
card(
    "localization_ideal_action",
    "M",
    SD + [("I", op("Ideal")), sub(M, "U")],
    [],
    eq(lu(M, op("ideal_smul", M, I, U)), op("ideal_smul", loc(M), I, lu(M, U))),
    "For any commutative ring R, multiplicative submonoid S, ideal I and submodule U of M, localizing I•U equals I•(S⁻¹U), with the ideal action over the original ring R.",
    [
        "Interpret I•U as finite sums of scalar products, not as a pointwise product set.",
        "Localization transports each scalar product to the corresponding product with a fraction.",
        "Induction over sums gives one inclusion; represent fractions to obtain the reverse inclusion.",
        "Conclude equality of R-submodules, without replacing I by an unspecified localized ideal.",
    ],
    f"(S : Submonoid R) (I : Ideal R) (U : Submodule R M) : (I • U).localized₀ S {LMS('M')} = I • U.localized₀ S {LMS('M')}",
    f"  exact Submodule.localized₀_smul S {LMS('M')} U I",
)
card(
    "localization_extreme_submodules",
    "M",
    SD,
    [],
    both(eq(lu(M, bot(M)), bot(loc(M))), eq(lu(M, top(M)), top(loc(M)))),
    "For any commutative ring R, multiplicative submonoid S and R-module M, the localizations of the zero and whole submodules are respectively the zero and whole submodules of S⁻¹M.",
    [
        "A fraction with zero numerator is zero.",
        "Thus localization of the zero submodule contains only zero.",
        "Every localized element has a numerator in M.",
        "Hence localization of the whole submodule is the whole localized module.",
    ],
    f"(S : Submonoid R) : (⊥ : Submodule R M).localized₀ S {LMS('M')} = ⊥ ∧ (⊤ : Submodule R M).localized₀ S {LMS('M')} = ⊤",
    "  exact ⟨Submodule.localized₀_bot _ _, Submodule.localized₀_top _ _⟩",
)
card(
    "localization_contains_image",
    "M",
    SD + [sub(M, "U")],
    [],
    op("submodule_le", loc(M), op("map", M, loc(M), lm(M), U), lu(M, U)),
    "For any commutative ring R, multiplicative submonoid S and submodule U of M, the image of U under x↦x/1 is contained in its localized submodule inside S⁻¹M.",
    [
        "Take an element in the image of U under the canonical localization map.",
        "Choose its representative x in U.",
        "The fraction x/1 belongs to the localized submodule by its defining membership condition.",
        "This proves inclusion; equality is not asserted.",
    ],
    f"(S : Submonoid R) (U : Submodule R M) : U.map {LMS('M')} ≤ U.localized₀ S {LMS('M')}",
    f"  exact Submodule.map_le_localized₀ S {LMS('M')} U",
)

card(
    "tensor_universal_property",
    "M N P",
    [linear("b", M, hom(N, P))],
    [],
    bind(
        "exists",
        [linear("f", tensor(M, N), P)],
        both(
            eq(curry(M, N, P, f), b),
            bind(
                "forall",
                [linear("g", tensor(M, N), P)],
                logic("implies", eq(curry(M, N, P, g), b), eq(g, f)),
            ),
        ),
    ),
    "For any commutative ring R and R-modules M,N,P, every bilinear map b:M→Hom_R(N,P) factors uniquely through a linear map M⊗_R N→P; factoring means curry(f)=b.",
    [
        "Construct the factor map using TensorProduct.lift b.",
        "On a pure tensor x⊗y this map evaluates to b(x)(y).",
        "Its curried map therefore equals b.",
        "Any other factor map agrees on every pure tensor, so tensor extensionality makes it equal to this lift.",
    ],
    "(b : M →ₗ[R] N →ₗ[R] P) : ∃ f : TensorProduct R M N →ₗ[R] P, TensorProduct.curry f = b ∧ ∀ g : TensorProduct R M N →ₗ[R] P, TensorProduct.curry g = b → g = f",
    "  refine ⟨TensorProduct.lift b, ?_, ?_⟩\n  · rfl\n  · intro g hg\n    apply TensorProduct.curry_injective\n    exact hg",
)
card(
    "tensor_lift_naturality",
    "M N P Q",
    [linear("b", M, hom(N, P)), linear("g", P, Q)],
    [],
    eq(
        lift(M, N, Q, op("bilinear_postcompose", M, N, P, Q, b, g)),
        comp(tensor(M, N), P, Q, lift(M, N, P, b), g),
    ),
    "For any commutative ring R, bilinear map b:M×N→P and linear map g:P→Q, lifting the bilinear composite g∘b equals composing g with the tensor lift of b.",
    [
        "Form the bilinear composite by applying g to b(x,y).",
        "Its tensor lift sends x⊗y to g(b(x,y)).",
        "The composite of g with the original lift has the same value on pure tensors.",
        "Tensor extensionality identifies the two linear maps.",
    ],
    "(b : M →ₗ[R] N →ₗ[R] P) (g : P →ₗ[R] Q) : TensorProduct.lift (b.compr₂ g) = g.comp (TensorProduct.lift b)",
    "  exact TensorProduct.lift_compr₂ g",
)
card(
    "tensor_right_exact",
    "X M N P",
    [linear("f", M, N), linear("g", N, P)],
    [exact(M, N, P, f, g), surj(N, P, g)],
    exact(tensor(X, M), tensor(X, N), tensor(X, P), lmap(X, M, N, f), lmap(X, N, P, g)),
    "For any commutative ring R and R-module X, tensoring an exact pair M→N→P with surjective N→P on the left by X preserves exactness; X need not be flat.",
    [
        "Fix the exact pair with its explicitly surjective second map.",
        "Identify P with the quotient of N by the image of the first map.",
        "Tensor product respects this cokernel presentation.",
        "Consequently the new kernel equals the image of the first tensor map.",
    ],
    "(f : M →ₗ[R] N) (g : N →ₗ[R] P) (h : Function.Exact f g) (hg : Function.Surjective g) : Function.Exact (f.lTensor X) (g.lTensor X)",
    "  exact lTensor_exact X h hg",
)
for key, mods, a, c, fn, ln in [
    (
        "tensor_symmetry",
        "M N",
        tensor(M, N),
        tensor(N, M),
        op("tensor_comm", M, N),
        "(TensorProduct.comm R M N)",
    ),
    (
        "tensor_associativity",
        "M N P",
        tensor(tensor(M, N), P),
        tensor(M, tensor(N, P)),
        op("tensor_assoc", M, N, P),
        "(TensorProduct.assoc R M N P)",
    ),
]:
    card(
        key,
        mods,
        [],
        [],
        both(inj(a, c, fn), surj(a, c, fn)),
        (
            "For any commutative ring R and R-modules M,N, the canonical map M⊗N→N⊗M sending x⊗y to y⊗x is bijective."
            if key == "tensor_symmetry"
            else "For any commutative ring R and R-modules M,N,P, the canonical associativity map (M⊗N)⊗P→M⊗(N⊗P) is bijective."
        ),
        [
            "Construct the canonical map on pure tensors.",
            "Construct its inverse by reversing the same rearrangement of factors.",
            "Tensor extensionality verifies that each composite is the identity.",
            "The inverse identities prove injectivity and surjectivity.",
        ],
        f": Function.Injective {ln}.toLinearMap ∧ Function.Surjective {ln}.toLinearMap",
        f"  exact {ln}.bijective",
    )
card(
    "hom_contravariant_left_exact",
    "M N P X",
    [linear("f", M, N), linear("g", N, P)],
    [exact(M, N, P, f, g), surj(N, P, g)],
    exact(hom(P, X), hom(N, X), hom(M, X), pre(N, P, X, g), pre(M, N, X, f)),
    "For any commutative ring R, any R-module X and an exact pair M→N→P whose second map is surjective, precomposition gives an exact pair Hom_R(P,X)→Hom_R(N,X)→Hom_R(M,X).",
    [
        "An element of the new kernel is a map N→X vanishing on the image of M.",
        "Exactness identifies that image with the kernel of N→P.",
        "The quotient universal property factors this map through P because N→P is surjective.",
        "This identifies the kernel of precomposition with the image of precomposition.",
    ],
    "(f : M →ₗ[R] N) (g : N →ₗ[R] P) (h : Function.Exact f g) (hg : Function.Surjective g) : Function.Exact (LinearMap.lcomp R X g) (LinearMap.lcomp R X f)",
    "  exact LinearMap.exact_lcomp_of_exact_of_surjective X h hg",
)
card(
    "hom_precomposition_injective",
    "M N X",
    [linear("f", M, N)],
    [surj(M, N, f)],
    inj(hom(N, X), hom(M, X), pre(M, N, X, f)),
    "For any commutative ring R and surjective R-linear f:M→N, precomposition with f is an injection Hom_R(N,X)→Hom_R(M,X) for every R-module X.",
    [
        "Take two maps N→X whose composites with f agree.",
        "Choose a preimage under f for each element of N.",
        "Evaluate the composite equality at that preimage.",
        "The maps agree on all elements, proving injectivity of precomposition.",
    ],
    "(f : M →ₗ[R] N) (hf : Function.Surjective f) : Function.Injective (LinearMap.lcomp R X f)",
    "  exact LinearMap.lcomp_injective_of_surjective f hf",
)
card(
    "hom_postcomposition_injective",
    "X M N",
    [linear("f", M, N)],
    [inj(M, N, f)],
    inj(hom(X, M), hom(X, N), post(X, M, N, f)),
    "For any commutative ring R and injective R-linear f:M→N, postcomposition with f is an injection Hom_R(X,M)→Hom_R(X,N) for every R-module X.",
    [
        "Take two maps X→M with equal composites into N.",
        "Evaluate their composite equality at an arbitrary element of X.",
        "Cancel f by injectivity to recover equality in M.",
        "Extensionality gives equality of the maps X→M.",
    ],
    "(f : M →ₗ[R] N) (hf : Function.Injective f) : Function.Injective ((LinearMap.llcomp R X M N f) : (X →ₗ[R] M) →ₗ[R] (X →ₗ[R] N))",
    "  intro u v huv\n  ext x\n  apply hf\n  exact LinearMap.congr_fun huv x",
)


def digest(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert len({c["id"] for c in CARDS}) == len(CARDS)
    assert len({c["openmath_xml"] for c in CARDS}) == len(CARDS)
    witness = ROOT / "docs/commalg-v3-batch.lean"
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
        "validator_sha256": digest(ROOT / "pals-agent/pals_agent/typed_commalg_v3.py"),
        "registry_sha256": digest(
            ROOT
            / "pals-agent/pals_agent/content_dictionaries/typed-commalg-v3-registry.json"
        ),
    }
    payload = {
        "schema_version": "pals.typed-catalog-expansion-batch.v1",
        "profile_id": PROFILE_ID,
        "cards": CARDS,
        "evidence": evidence,
    }
    (ROOT / "docs/commalg-v3-batch.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    )
    print(f"Compiled and emitted {len(CARDS)} new commalg-v3 cards")


if __name__ == "__main__":
    main()
