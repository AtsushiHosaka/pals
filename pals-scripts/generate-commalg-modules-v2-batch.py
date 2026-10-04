"""Build new module-v2 cards and compile their exact witnesses before JSON emission."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pals-agent"))
from pals_agent.typed_commalg_modules_v2 import (
    CDBASE,
    PROFILE_ID,
    canonicalize_typed_commalg_modules_v2_openmath_xml,
    validate_canonical_typed_commalg_modules_v2_openmath_xml,
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
    return app("module2", name, R, *args)


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
    declarations = [("R", sym("module2", "LocalRing" if local else "CommRing"))]
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
    xml = canonicalize_typed_commalg_modules_v2_openmath_xml(raw)
    validate_canonical_typed_commalg_modules_v2_openmath_xml(xml)
    lean = "example {R : Type*} [CommRing R] "
    if local:
        lean += "[IsLocalRing R] "
    for name in modules.split():
        lean += f"{{{name} : Type*}} [AddCommGroup {name}] [Module R {name}] "
    assert 4 <= len(steps) <= 10
    CARDS.append(
        {
            "id": "commalg_modules_v2_" + key,
            "canonical_statement": statement,
            "proof_strategy": strategy,
            "sketch_steps": steps,
            "openmath_xml": xml,
            "lean_target": lean + target,
            "lean_witness": "by\n" + proof,
        }
    )


add(
    "quotient_kernel",
    "M",
    [sub(M, "U")],
    [],
    eq(ker(M, q(M, U), mk(M, U)), U),
    "For any commutative ring R, R-module M and submodule U, the kernel of the canonical quotient map M → M/U is U.",
    "Use the criterion for a class in a module quotient to be zero.",
    [
        "Fix R, M and U without finiteness assumptions.",
        "An element lies in the kernel exactly when its quotient class is zero.",
        "The class is zero exactly when the element belongs to U.",
        "Identify the two submodules by this membership equivalence.",
    ],
    "(U : Submodule R M) : LinearMap.ker U.mkQ = U",
    "  exact U.ker_mkQ",
)

add(
    "quotient_surjective",
    "M",
    [sub(M, "U")],
    [],
    op("surjective", M, q(M, U), mk(M, U)),
    "Every canonical quotient map M → M/U of modules over a commutative ring is surjective.",
    "Every quotient class has a representative in M.",
    [
        "Fix a submodule U of M.",
        "Take an arbitrary element of M/U.",
        "Choose a representative x in M by quotient induction.",
        "The canonical projection sends x to the chosen class.",
    ],
    "(U : Submodule R M) : Function.Surjective U.mkQ",
    "  exact U.mkQ_surjective",
)

add(
    "quotient_exact_sequence",
    "M",
    [sub(M, "U")],
    [],
    op("exact", carrier(M, U), M, q(M, U), op("inclusion", M, U), mk(M, U)),
    "For an R-submodule U of M, the inclusion U → M followed by the quotient map M → M/U is exact at M.",
    "The image of inclusion and the kernel of projection are both U.",
    [
        "View U as an R-module with its induced structure.",
        "The inclusion has image U in M.",
        "The canonical quotient projection has kernel U.",
        "Their equality proves exactness at M.",
    ],
    "(U : Submodule R M) : Function.Exact U.subtype U.mkQ",
    "  exact LinearMap.exact_subtype_mkQ U",
)

add(
    "quotient_factorization",
    "M N",
    [sub(M, "U"), linear("f", M, N)],
    [op("submodule_le", M, U, ker(M, N, f))],
    bind("exists", [linear("g", q(M, U), N)], eq(comp(M, q(M, U), N, mk(M, U), g), f)),
    "If an R-linear map f:M→N vanishes on a submodule U, there exists an R-linear map g:M/U→N whose composite with the quotient projection is f.",
    "Descend f to quotient classes using U⊆ker(f) for representative independence.",
    [
        "Assume U is contained in the kernel of f.",
        "Define the image of a class [x] to be f(x).",
        "Changing x by an element of U does not change f(x).",
        "The descended map is linear and its composite with projection equals f.",
    ],
    "(U : Submodule R M) (f : M →ₗ[R] N) (hU : U ≤ LinearMap.ker f) : ∃ g : (M ⧸ U) →ₗ[R] N, g.comp U.mkQ = f",
    "  exact ⟨U.liftQ f hU, U.liftQ_mkQ f hU⟩",
)

add(
    "quotient_factorization_unique",
    "M N",
    [sub(M, "U"), linear("f", q(M, U), N), linear("g", q(M, U), N)],
    [eq(comp(M, q(M, U), N, mk(M, U), f), comp(M, q(M, U), N, mk(M, U), g))],
    eq(f, g),
    "Two R-linear maps M/U→N are equal if their composites with the canonical projection M→M/U are equal.",
    "Use surjectivity of the quotient projection to compare the maps on all classes.",
    [
        "Take a class in M/U.",
        "Choose a representative in M.",
        "Apply the equality of composites to this representative.",
        "Conclude the maps agree everywhere and use extensionality.",
    ],
    "(U : Submodule R M) (f g : (M ⧸ U) →ₗ[R] N) (h : f.comp U.mkQ = g.comp U.mkQ) : f = g",
    "  apply LinearMap.ext\n  intro x\n  obtain ⟨m, rfl⟩ := U.mkQ_surjective x\n  exact LinearMap.congr_fun h m",
)

add(
    "quotient_submodule_correspondence_pullback",
    "M",
    [sub(M, "U"), sub(M, "V")],
    [],
    eq(
        op("comap", M, q(M, U), mk(M, U), op("map", M, q(M, U), mk(M, U), V)),
        op("submodule_sup", M, U, V),
    ),
    "For submodules U,V of an R-module M, the inverse image of the image of V under M→M/U is U+V.",
    "Elements with the same quotient class differ by an element of U.",
    [
        "Project V to M/U and take its full inverse image.",
        "Any element in that inverse image differs from an element of V by an element of U.",
        "Thus it belongs to U+V.",
        "Conversely every sum from U+V projects to the image of V.",
    ],
    "(U V : Submodule R M) : (V.map U.mkQ).comap U.mkQ = U ⊔ V",
    "  exact U.comap_map_mkQ V",
)

add(
    "quotient_submodule_correspondence_pushforward",
    "M",
    [sub(M, "U"), sub(q(M, U), "W")],
    [],
    eq(op("map", M, q(M, U), mk(M, U), op("comap", M, q(M, U), mk(M, U), W)), W),
    "Every submodule W of M/U equals the image of its inverse image under the quotient projection M→M/U.",
    "Apply the image–inverse-image identity to the surjective quotient map.",
    [
        "Take the inverse image of W in M.",
        "Its image is contained in W by definition.",
        "Every element of W has a representative in M because projection is surjective.",
        "That representative belongs to the inverse image, proving the reverse inclusion.",
    ],
    "(U : Submodule R M) (W : Submodule R (M ⧸ U)) : (W.comap U.mkQ).map U.mkQ = W",
    "  exact Submodule.map_comap_eq_self (by simp [U.range_mkQ])",
)

add(
    "quotient_by_kernel_embedding",
    "M N",
    [linear("f", M, N)],
    [],
    bind(
        "exists",
        [linear("g", q(M, ker(M, N, f)), N)],
        logic(
            "and",
            eq(comp(M, q(M, ker(M, N, f)), N, mk(M, ker(M, N, f)), g), f),
            op("injective", q(M, ker(M, N, f)), N, g),
            eq(ran(q(M, ker(M, N, f)), N, g), ran(M, N, f)),
        ),
    ),
    "Every R-linear map f:M→N factors through an injective R-linear map M/ker(f)→N with image equal to the image of f.",
    "Descend f through its kernel; the descended kernel is zero and the image is unchanged.",
    [
        "Use ker(f)⊆ker(f) to construct the quotient lift g.",
        "The defining quotient-lift identity gives g∘π=f.",
        "The kernel of g is zero because the entire original kernel was quotiented out.",
        "Projection is surjective, so g and f have the same image.",
    ],
    "(f : M →ₗ[R] N) : ∃ g : (M ⧸ LinearMap.ker f) →ₗ[R] N, g.comp (LinearMap.ker f).mkQ = f ∧ Function.Injective g ∧ LinearMap.range g = LinearMap.range f",
    "  refine ⟨(LinearMap.ker f).liftQ f le_rfl, Submodule.liftQ_mkQ _ _ _, ?_, Submodule.range_liftQ _ _ _⟩\n  exact LinearMap.ker_eq_bot.mp (Submodule.ker_liftQ_eq_bot _ _ _ le_rfl)",
)

add(
    "finite_quotient",
    "M",
    [sub(M, "U")],
    [op("finite", M)],
    op("finite", q(M, U)),
    "Every quotient M/U of a finitely generated module M over a commutative ring is finitely generated.",
    "Project a finite generating family of M to the quotient.",
    [
        "Choose a finite generating family of M.",
        "Apply the quotient projection to each generator.",
        "Every quotient class has a representative in M.",
        "Express the representative using the original generators and project the expression.",
    ],
    "(U : Submodule R M) [Module.Finite R M] : Module.Finite R (M ⧸ U)",
    "  infer_instance",
)

add(
    "finite_surjective_image",
    "M N",
    [linear("f", M, N)],
    [op("finite", M), op("surjective", M, N, f)],
    op("finite", N),
    "A surjective R-linear image N of a finitely generated R-module M is finitely generated.",
    "Images of finitely many generators generate the codomain of a surjection.",
    [
        "Choose finitely many generators of M.",
        "Take their images under the surjective linear map.",
        "Lift an arbitrary element of N to M.",
        "Push down a generator expression for that lift.",
    ],
    "(f : M →ₗ[R] N) [Module.Finite R M] (hf : Function.Surjective f) : Module.Finite R N",
    "  exact Module.Finite.of_surjective f hf",
)

add(
    "finite_submodule_carrier_iff_fg",
    "M",
    [sub(M, "U")],
    [],
    iff(op("finite", carrier(M, U)), op("fg", M, U)),
    "A submodule U of an R-module M is finitely generated as a submodule exactly when its induced R-module is finitely generated.",
    "Transport finite generation along the inclusion of U into M.",
    [
        "The induced module on U uses the same addition and scalar multiplication.",
        "A finite family in U generates its whole induced module precisely when its images span U in M.",
        "Use the injectivity of the inclusion to compare these two spans.",
        "Conclude the equivalence of the two finite-generation statements.",
    ],
    "(U : Submodule R M) : Module.Finite R U ↔ U.FG",
    "  exact Module.Finite.iff_fg",
)

add(
    "finite_extension_quotient",
    "M",
    [sub(M, "U")],
    [op("fg", M, U), op("finite", q(M, U))],
    op("finite", M),
    "If U is a finitely generated submodule of M and M/U is finitely generated, then M is finitely generated over R.",
    "Lift finitely many quotient generators and adjoin finitely many generators of U.",
    [
        "Choose finite generators of U.",
        "Choose finite generators of M/U and lift them to M.",
        "Subtract a combination of the lifted generators from any element of M to obtain an element of U.",
        "The two finite families together generate M.",
    ],
    "(U : Submodule R M) (hU : U.FG) [Module.Finite R (M ⧸ U)] : Module.Finite R M",
    "  letI : Module.Finite R U := Module.Finite.of_fg hU\n  exact Module.Finite.of_submodule_quotient U",
)

add(
    "nakayama_jacobson_submodule",
    "M",
    [("I", op("Ideal")), sub(M, "U")],
    [
        op("fg", M, U),
        op("ideal_le", I, op("ideal_jacobson", op("ideal_bot"))),
        op("submodule_le", M, U, op("ideal_smul", M, I, U)),
    ],
    eq(U, bot(M)),
    "If U is a finitely generated submodule of an R-module, I is contained in the Jacobson radical of R, and U⊆IU, then U=0.",
    "Apply Nakayama's lemma in its Jacobson-radical form to the finitely generated submodule.",
    [
        "Retain the finite-generation hypothesis on U.",
        "Use U⊆IU and the automatic reverse inclusion IU⊆U to obtain U=IU.",
        "The determinant argument yields an element congruent to 1 modulo I that annihilates U.",
        "Every such element is a unit because I lies in the Jacobson radical, hence U=0.",
    ],
    "(I : Ideal R) (U : Submodule R M) (hU : U.FG) (hI : I ≤ Ideal.jacobson ⊥) (h : U ≤ I • U) : U = ⊥",
    "  exact Submodule.eq_bot_of_le_smul_of_le_jacobson_bot I U hU h hI",
)

add(
    "nakayama_local_finite_module",
    "M",
    [],
    [op("finite", M), eq(op("ideal_smul", M, op("maximal_ideal"), top(M)), top(M))],
    eq(top(M), bot(M)),
    "Let R be a commutative local ring with maximal ideal m and M a finitely generated R-module. If mM=M, then M=0.",
    "Use that the maximal ideal of a local ring is contained in its Jacobson radical, then apply Nakayama.",
    [
        "Use finite generation of M, with no freeness or Noetherian hypothesis.",
        "The maximal ideal m lies in the Jacobson radical of R.",
        "The equality mM=M gives the containment M⊆mM.",
        "Nakayama applied to the top submodule gives top=bottom, equivalently M=0.",
    ],
    "[Module.Finite R M] (h : IsLocalRing.maximalIdeal R • (⊤ : Submodule R M) = ⊤) : (⊤ : Submodule R M) = ⊥",
    "  exact Submodule.eq_bot_of_le_smul_of_le_jacobson_bot _ _ Module.Finite.fg_top h.ge (IsLocalRing.maximalIdeal_le_jacobson ⊥)",
    local=True,
)

add(
    "nakayama_local_generators",
    "M",
    [sub(M, "U")],
    [
        op("finite", M),
        eq(
            op("submodule_sup", M, U, op("ideal_smul", M, op("maximal_ideal"), top(M))),
            top(M),
        ),
    ],
    eq(U, top(M)),
    "For a finitely generated module M over a commutative local ring (R,m), if a submodule U satisfies U+mM=M, then U=M.",
    "Apply the generation form of Nakayama; no finite-generation assumption on U is required.",
    [
        "Assume M is finitely generated and U+mM=M.",
        "The maximal ideal m is contained in the Jacobson radical.",
        "Nakayama's containment form applied to the top submodule gives M⊆U.",
        "Together with U⊆M this proves U=M.",
    ],
    "(U : Submodule R M) [Module.Finite R M] (h : U ⊔ IsLocalRing.maximalIdeal R • (⊤ : Submodule R M) = ⊤) : U = ⊤",
    "  apply top_unique\n  exact Submodule.le_of_le_smul_of_le_jacobson_bot Module.Finite.fg_top (IsLocalRing.maximalIdeal_le_jacobson ⊥) h.ge",
    local=True,
)

add(
    "fg_submodule_sum",
    "M",
    [sub(M, "U"), sub(M, "V")],
    [op("fg", M, U), op("fg", M, V)],
    op("fg", M, op("submodule_sup", M, U, V)),
    "The sum of two finitely generated submodules of an R-module is finitely generated.",
    "Join finite generating families for the two submodules.",
    [
        "Choose a finite family spanning U.",
        "Choose a finite family spanning V.",
        "Their union is finite and lies in U+V.",
        "Every sum of elements from U and V is a combination of this union.",
    ],
    "(U V : Submodule R M) (hU : U.FG) (hV : V.FG) : (U ⊔ V).FG",
    "  exact hU.sup hV",
)

add(
    "finite_tensor_product",
    "M N",
    [],
    [op("finite", M), op("finite", N)],
    op("finite", tensor(M, N)),
    "The tensor product M⊗_R N of two finitely generated modules over a commutative ring is finitely generated.",
    "Tensor products of pairs of generators form a finite generating family.",
    [
        "Choose finite generating families for M and N.",
        "Form all pairwise pure tensors of these generators.",
        "Bilinearity expresses every pure tensor in their span.",
        "Every tensor is a finite sum of pure tensors, proving finite generation.",
    ],
    "[Module.Finite R M] [Module.Finite R N] : Module.Finite R (TensorProduct R M N)",
    "  infer_instance",
)

add(
    "tensor_preserves_surjections",
    "X M N",
    [linear("f", M, N)],
    [op("surjective", M, N, f)],
    op("surjective", tensor(X, M), tensor(X, N), lmap(X, M, N, f)),
    "For any R-module X, tensoring a surjective R-linear map f:M→N with the identity of X gives a surjection X⊗M→X⊗N.",
    "Lift the second factor of each pure tensor and use generation by pure tensors.",
    [
        "Take an arbitrary pure tensor x⊗n in X⊗N.",
        "Surjectivity of f supplies m with f(m)=n.",
        "The tensor x⊗m maps to x⊗n.",
        "Extend to sums of pure tensors; flatness is not needed.",
    ],
    "(f : M →ₗ[R] N) (hf : Function.Surjective f) : Function.Surjective (f.lTensor X)",
    "  exact LinearMap.lTensor_surjective X hf",
)

add(
    "flat_tensor_preserves_injections",
    "X M N",
    [linear("f", M, N)],
    [op("flat", X), op("injective", M, N, f)],
    op("injective", tensor(X, M), tensor(X, N), lmap(X, M, N, f)),
    "If X is a flat R-module and f:M→N is an injective R-linear map, then identity_X⊗f is injective.",
    "Apply preservation of injective linear maps by tensoring with a flat module.",
    [
        "Retain the hypothesis that X is flat.",
        "Take the injective map f:M→N.",
        "Flatness makes the functor X⊗_R− preserve this monomorphism.",
        "Conclude injectivity of the induced tensor map.",
    ],
    "[Module.Flat R X] (f : M →ₗ[R] N) (hf : Function.Injective f) : Function.Injective (f.lTensor X)",
    "  exact Module.Flat.lTensor_preserves_injective_linearMap f hf",
)

add(
    "flat_tensor_preserves_exactness",
    "X M N L",
    [linear("f", M, N), linear("g", N, L)],
    [op("flat", X), op("exact", M, N, L, f, g)],
    op(
        "exact",
        tensor(X, M),
        tensor(X, N),
        tensor(X, L),
        lmap(X, M, N, f),
        lmap(X, N, L, g),
    ),
    "Tensoring an exact pair of R-linear maps M→N→L with a flat R-module X preserves exactness at X⊗N.",
    "Use exactness of tensoring with a flat module, keeping both source and target maps.",
    [
        "Assume the image of f equals the kernel of g.",
        "Retain the flatness hypothesis on X.",
        "Apply the exact tensor functor X⊗_R− to both maps.",
        "The image of identity⊗f equals the kernel of identity⊗g.",
    ],
    "[Module.Flat R X] (f : M →ₗ[R] N) (g : N →ₗ[R] L) (h : Function.Exact f g) : Function.Exact (f.lTensor X) (g.lTensor X)",
    "  exact Module.Flat.lTensor_exact X h",
)

add(
    "finite_exact_extension",
    "M N L",
    [linear("f", M, N), linear("g", N, L)],
    [
        op("finite", M),
        op("finite", L),
        op("exact", M, N, L, f, g),
        op("surjective", N, L, g),
    ],
    op("finite", N),
    "If M→N→L→0 is an exact sequence of modules over a commutative ring and M,L are finitely generated, then N is finitely generated.",
    "Use the finitely generated image of M and lift finite generators of L.",
    [
        "Finite generation of M gives a finite generating family of the image of f.",
        "Surjectivity of g allows finite generators of L to be lifted to N.",
        "Subtract combinations of these lifts from an arbitrary element of N.",
        "Exactness places the difference in the image of f, so the combined finite family generates N.",
    ],
    "[Module.Finite R M] [Module.Finite R L] (f : M →ₗ[R] N) (g : N →ₗ[R] L) (h : Function.Exact f g) (hg : Function.Surjective g) : Module.Finite R N",
    "  exact Module.Finite.of_exact h hg",
)

add(
    "fg_image",
    "M N",
    [sub(M, "U"), linear("f", M, N)],
    [op("fg", M, U)],
    op("fg", N, op("map", M, N, f, U)),
    "The image of a finitely generated submodule U under an R-linear map f:M→N is finitely generated.",
    "Map a finite spanning family through the linear map.",
    [
        "Choose finitely many generators of U.",
        "Apply f to each of these generators.",
        "Linearity sends generator expressions in U to combinations of their images.",
        "Every element of the image has such an expression.",
    ],
    "(U : Submodule R M) (f : M →ₗ[R] N) (hU : U.FG) : (U.map f).FG",
    "  exact hU.map f",
)


def digest(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert len({c["id"] for c in CARDS}) == len(CARDS)
    assert len({c["openmath_xml"] for c in CARDS}) == len(CARDS)
    witness = ROOT / "docs/commalg-modules-v2-batch.lean"
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
        "validator_sha256": digest(
            ROOT / "pals-agent/pals_agent/typed_commalg_modules_v2.py"
        ),
        "registry_sha256": digest(
            ROOT
            / "pals-agent/pals_agent/content_dictionaries/typed-commalg-modules-v2-registry.json"
        ),
    }
    payload = {
        "schema_version": "pals.typed-catalog-expansion-batch.v1",
        "profile_id": PROFILE_ID,
        "cards": CARDS,
        "evidence": evidence,
    }
    (ROOT / "docs/commalg-modules-v2-batch.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    )
    print(f"Compiled and emitted {len(CARDS)} new module-v2 cards")


if __name__ == "__main__":
    main()
