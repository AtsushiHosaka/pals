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


sset, z, z2, y2 = v("s"), v("z"), v("z2"), v("y2")
member = lambda point: a("member", n, point, sset)
add(
    "constant_map_not_coordinate_change",
    N("n")
    + [
        decl("s", "Set", "n"),
        decl("x", "Vector", "n"),
        decl("y", "Vector", "n"),
        decl("c", "Vector", "n"),
    ],
    imp(
        a("measurable_set", n, sset),
        member(x),
        member(y),
        ne(x, y),
        bind(
            [decl("f", "Function", "n", "n"), decl("D", "DerivativeField", "n", "n")],
            both(
                bind([decl("z", "Vector", "n")], eq(a("apply", n, n, f, z), c)),
                both(
                    bind(
                        [decl("z", "Vector", "n")],
                        a("has_fderiv", n, n, f, z, a("field_apply", n, n, D, z)),
                    ),
                    neg(a("injective_on", n, f, sset)),
                ),
            ),
            "exists",
        ),
    ),
    "For every coordinate dimension n, measurable region s containing distinct points x,y, and vector c, there exists an everywhere Fréchet-differentiable map constantly equal to c which is not injective on s. Differentiability alone therefore does not establish the injectivity hypothesis of a coordinate change.",
    "example (n : ℕ) (s : Set (Fin n → ℝ)) (_hs : MeasurableSet s) (x y c : Fin n → ℝ) (hx : x ∈ s) (hy : y ∈ s) (hxy : x ≠ y) : ∃ f : (Fin n → ℝ) → (Fin n → ℝ), ∃ D : (Fin n → ℝ) → ((Fin n → ℝ) →L[ℝ] (Fin n → ℝ)), (∀ z, f z = c) ∧ (∀ z, HasFDerivAt f (D z) z) ∧ ¬ Set.InjOn f s",
    "  refine ⟨fun _ => c, fun _ => 0, fun _ => rfl, ?_, ?_⟩\n  · intro z; exact hasFDerivAt_const c z\n  · intro hi; exact hxy (hi hx hy rfl)",
    [
        "Choose the constant map with arbitrary value c.",
        "Its Fréchet derivative exists everywhere and is the zero continuous linear map.",
        "The two distinct domain points x and y have the same image c.",
        "Thus the map fails injectivity on the region despite differentiability; the substitution theorem needs its separate injectivity premise.",
    ],
)
# Two successive valid substitutions; no determinant-of-a-composition shortcut.
Ds, Es, F = v("D"), v("E"), v("F")
image1 = a("image", n, f, sset)
image2 = a("image", n, g, image1)
weight2 = a("jacobian_weighted", n, g, Es, F)
weight12 = a("jacobian_weighted", n, f, Ds, weight2)


def derivative_on(fun, field, domain):
    return bind(
        [decl("z", "Vector", "n")],
        imp(
            a("member", n, z, domain),
            a("has_fderiv_within", n, fun, z, domain, a("field_apply", n, n, field, z)),
        ),
    )


add(
    "successive_coordinate_changes",
    N("n")
    + [
        decl("s", "Set", "n"),
        decl("f", "Function", "n", "n"),
        decl("g", "Function", "n", "n"),
        decl("D", "DerivativeField", "n", "n"),
        decl("E", "DerivativeField", "n", "n"),
        decl("F", "ScalarFunction", "n"),
    ],
    imp(
        a("measurable_set", n, sset),
        derivative_on(f, Ds, sset),
        a("injective_on", n, f, sset),
        derivative_on(g, Es, image1),
        a("injective_on", n, g, image1),
        a("integrable_on", n, F, image2),
        both(
            a("integrable_on", n, weight12, sset),
            eq(a("set_integral", n, F, image2), a("set_integral", n, weight12, sset)),
        ),
    ),
    "For arbitrary n, let f be injective on a measurable region s with within-s derivative D, and let g be injective on f(s) with within-f(s) derivative E. For every real F integrable on g(f(s)), the twice-pulled-back density |det D(x)| (|det E(f(x))| F(g(f(x)))) is integrable on s, and its integral equals the integral of F on g(f(s)). The second derivative is evaluated at the intermediate point f(x).",
    "example (n : ℕ) (s : Set (Fin n → ℝ)) (f g : (Fin n → ℝ) → (Fin n → ℝ)) (D E : (Fin n → ℝ) → ((Fin n → ℝ) →L[ℝ] (Fin n → ℝ))) (F : (Fin n → ℝ) → ℝ) (hs : MeasurableSet s) (hD : ∀ x ∈ s, HasFDerivWithinAt f (D x) s x) (hf : Set.InjOn f s) (hE : ∀ y ∈ f '' s, HasFDerivWithinAt g (E y) (f '' s) y) (hg : Set.InjOn g (f '' s)) (hF : MeasureTheory.IntegrableOn F (g '' (f '' s))) : MeasureTheory.IntegrableOn (fun x => |(D x).det| * (|(E (f x)).det| * F (g (f x)))) s ∧ (∫ z in g '' (f '' s), F z) = ∫ x in s, |(D x).det| * (|(E (f x)).det| * F (g (f x)))",
    """  have hm : MeasurableSet (f '' s) := MeasureTheory.measurable_image_of_fderivWithin hs hD hf
  have h1 : MeasureTheory.IntegrableOn (fun y => |(E y).det| * F (g y)) (f '' s) := by
    simpa only [smul_eq_mul] using (MeasureTheory.integrableOn_image_iff_integrableOn_abs_det_fderiv_smul MeasureTheory.volume hm hE hg F).mp hF
  constructor
  · simpa only [smul_eq_mul] using (MeasureTheory.integrableOn_image_iff_integrableOn_abs_det_fderiv_smul MeasureTheory.volume hs hD hf (fun y => |(E y).det| * F (g y))).mp h1
  · calc
      (∫ z in g '' (f '' s), F z) = ∫ y in f '' s, |(E y).det| * F (g y) := by
        simpa only [smul_eq_mul] using MeasureTheory.integral_image_eq_integral_abs_det_fderiv_smul MeasureTheory.volume hm hE hg F
      _ = ∫ x in s, |(D x).det| * (|(E (f x)).det| * F (g (f x))) := by
        simpa only [smul_eq_mul] using MeasureTheory.integral_image_eq_integral_abs_det_fderiv_smul MeasureTheory.volume hs hD hf (fun y => |(E y).det| * F (g y))""",
    [
        "The first injective differentiable substitution takes the measurable region s to a measurable intermediate image f(s).",
        "Apply integrability transport to g on this intermediate domain, obtaining the inner weighted density.",
        "Transport its integrability through f to establish integrability of the twice-weighted density on s.",
        "Apply the Jacobian integral formula first to g and then to f.",
        "The second substitution evaluates both the intermediate density and E at f(x), and multiplies the two absolute determinant factors.",
        "Combine the equalities while retaining both region-specific injectivity and within-derivative assumptions.",
    ],
)


def main():
    witness_path = ROOT / "docs/multivariable-v5-change-variables-supplement.lean"
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
        "witness_path": "docs/multivariable-v5-change-variables-supplement.lean",
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
    (ROOT / "docs/multivariable-v5-change-variables-supplement.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    )
    print(f"Compiled and emitted {len(cards)} general multivariable cards.")


if __name__ == "__main__":
    main()
