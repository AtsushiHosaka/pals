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
            "id": "mv_line_supp_v5_" + identifier,
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


E = v("e")
curve_ds = N("n") + [
    decl("D", "ScalarDerivativeField", "n"),
    decl("c", "Curve", "n"),
    decl("u", "Curve", "n"),
    decl("a", "Real"),
    decl("b", "Real"),
]


def pull(field, curve, velocity):
    return a("pullback_one_form", n, field, curve, velocity)


def value(curve, point):
    return a("curve_apply", n, curve, point)


def derivative(curve, velocity, local=True):
    p = a("has_curve_deriv", n, curve, t, value(velocity, t))
    return bind([decl("t", "Real")], imp(a("in_uIcc", t, aa, bb), p) if local else p)


def integral(fun, left, right):
    return a("interval_integral", fun, left, right)


def integrable(fun, left, right):
    return a("interval_integrable", fun, left, right)


P = pull(D, c, u)

add(
    "orientation_law",
    curve_ds,
    imp(
        derivative(c, u),
        both(
            iff(integrable(P, aa, bb), integrable(P, bb, aa)),
            eq(integral(P, bb, aa), a("real_sub", Z, integral(P, aa, bb))),
        ),
    ),
    "For any actual curve c with velocity u on uIcc(a,b) and any scalar one-form field D, the pullback is interval-integrable from a to b if and only if it is integrable from b to a. Reversing the oriented parameter interval negates its integral. The total integral identity alone does not assert integrability.",
    "example (n : ℕ) (D : (Fin n → ℝ) → ((Fin n → ℝ) →L[ℝ] ℝ)) (c u : ℝ → (Fin n → ℝ)) (a b : ℝ) (hc : ∀ t ∈ Set.uIcc a b, HasDerivAt c (u t) t) : (IntervalIntegrable (fun t => D (c t) (u t)) MeasureTheory.volume a b ↔ IntervalIntegrable (fun t => D (c t) (u t)) MeasureTheory.volume b a) ∧ (∫ t in b..a, D (c t) (u t)) = -(∫ t in a..b, D (c t) (u t))",
    "  exact ⟨⟨fun h => h.symm, fun h => h.symm⟩, intervalIntegral.integral_symm a b⟩",
    [
        "Identify the pullback t↦D(c(t))(u(t)) using the stated actual velocity.",
        "The same unordered interval underlies both integration directions.",
        "Interval integrability is therefore unchanged by reversing endpoints.",
        "The oriented interval integral changes sign, including the zero-length case.",
    ],
)

add(
    "split_parameter_interval",
    curve_ds + [decl("e", "Real")],
    imp(
        derivative(c, u, False),
        integrable(P, aa, bb),
        integrable(P, bb, E),
        eq(a("real_add", integral(P, aa, bb), integral(P, bb, E)), integral(P, aa, E)),
    ),
    "For any differentiable curve c with velocity u and any one-form D, integrability of the pullback on a..b and b..e implies that the sum of these two oriented line integrals equals its integral on a..e. No ordering of a,b,e is required.",
    "example (n : ℕ) (D : (Fin n → ℝ) → ((Fin n → ℝ) →L[ℝ] ℝ)) (c u : ℝ → (Fin n → ℝ)) (a b e : ℝ) (hc : ∀ t, HasDerivAt c (u t) t) (hi : IntervalIntegrable (fun t => D (c t) (u t)) MeasureTheory.volume a b) (hj : IntervalIntegrable (fun t => D (c t) (u t)) MeasureTheory.volume b e) : (∫ t in a..b, D (c t) (u t)) + (∫ t in b..e, D (c t) (u t)) = ∫ t in a..e, D (c t) (u t)",
    "  exact intervalIntegral.integral_add_adjacent_intervals hi hj",
    [
        "Use the same parameterized curve and pullback on both intervals.",
        "Retain interval integrability separately on a..b and b..e.",
        "Apply additivity of interval integrals across the common parameter b.",
        "The oriented identity remains valid without assuming that b lies between a and e.",
    ],
)

add(
    "orientation_counterexample",
    N("n")
    + [
        decl("i", "Index", "n"),
        decl("x", "Vector", "n"),
        decl("u", "Curve", "n"),
        decl("a", "Real"),
        decl("b", "Real"),
    ],
    imp(
        bind([decl("t", "Real")], eq(value(u, t), a("basis_vector", n, i))),
        ne(aa, bb),
        both(
            bind(
                [decl("t", "Real")],
                a("has_curve_deriv", n, a("update_curve", n, x, i), t, value(u, t)),
            ),
            ne(
                integral(
                    pull(
                        a("scalar_fderiv_field", n, a("projection", n, i)),
                        a("update_curve", n, x, i),
                        u,
                    ),
                    aa,
                    bb,
                ),
                integral(
                    pull(
                        a("scalar_fderiv_field", n, a("projection", n, i)),
                        a("update_curve", n, x, i),
                        u,
                    ),
                    bb,
                    aa,
                ),
            ),
        ),
    ),
    "For every dimension n with coordinate i, base vector x, distinct real endpoints a,b, and constant velocity u(t)=e_i, the curve obtained by replacing coordinate i of x by t has actual velocity u. Integrating the exact coordinate form dx_i along this curve from a to b differs from integrating it from b to a.",
    "example (n : ℕ) (i : Fin n) (x : Fin n → ℝ) (u : ℝ → (Fin n → ℝ)) (a b : ℝ) (hu : ∀ t, u t = Pi.single i 1) (hab : a ≠ b) : (∀ t, HasDerivAt (fun s => Function.update x i s) (u t) t) ∧ (∫ t in a..b, fderiv ℝ (fun y : Fin n → ℝ => y i) (Function.update x i t) (u t)) ≠ (∫ t in b..a, fderiv ℝ (fun y : Fin n → ℝ => y i) (Function.update x i t) (u t))",
    "  constructor\n  · intro t\n    rw [hu t]\n    simpa using hasDerivAt_update x i t\n  · have hi : ∀ y : Fin n → ℝ, fderiv ℝ (fun y : Fin n → ℝ => y i) y = ContinuousLinearMap.proj i := fun y => (hasFDerivAt_apply (𝕜 := ℝ) i y).fderiv\n    simp_rw [hi, hu]\n    simp only [ContinuousLinearMap.proj_apply, Pi.single_eq_same, intervalIntegral.integral_const, smul_eq_mul, mul_one]\n    intro he\n    apply hab\n    linarith",
    [
        "The derivative of the coordinate-update curve is the chosen basis vector e_i.",
        "The derivative of the coordinate potential y↦y_i is coordinate projection.",
        "Applying this coordinate form to e_i gives the constant scalar pullback 1.",
        "The oriented integrals equal b-a and a-b; equality would force a=b, contrary to the hypothesis.",
    ],
)

add(
    "bilinear_curve_integration_by_parts",
    curve_ds
    + [decl("B", "Bilinear", "n"), decl("d", "Curve", "n"), decl("w", "Curve", "n")],
    imp(
        bind(
            [decl("x", "Vector", "n"), decl("y", "Vector", "n")],
            eq(
                a("dual_apply", n, a("scalar_field_apply", n, D, x), y),
                a("bilinear_apply", n, B, x, y),
            ),
        ),
        derivative(c, u),
        derivative(d, w),
        integrable(pull(D, c, w), aa, bb),
        integrable(pull(D, u, d), aa, bb),
        eq(
            a(
                "real_add",
                integral(pull(D, c, w), aa, bb),
                integral(pull(D, u, d), aa, bb),
            ),
            a(
                "real_sub",
                a("bilinear_apply", n, B, value(c, bb), value(d, bb)),
                a("bilinear_apply", n, B, value(c, aa), value(d, aa)),
            ),
        ),
    ),
    "Let B be any continuous bilinear real form on ℝⁿ, and let D(x)(y)=B(x,y). For curves c,d with actual velocities u,w on uIcc(a,b), if B(c(t),w(t)) and B(u(t),d(t)) are interval-integrable, the sum of their oriented integrals equals B(c(b),d(b))-B(c(a),d(a)). This is integration by parts for a pair of vector-valued curves; B need not be symmetric.",
    "example (n : ℕ) (B : (Fin n → ℝ) →L[ℝ] (Fin n → ℝ) →L[ℝ] ℝ) (D : (Fin n → ℝ) → ((Fin n → ℝ) →L[ℝ] ℝ)) (c d u w : ℝ → (Fin n → ℝ)) (a b : ℝ) (hD : ∀ x y, D x y = B x y) (hc : ∀ t ∈ Set.uIcc a b, HasDerivAt c (u t) t) (hd : ∀ t ∈ Set.uIcc a b, HasDerivAt d (w t) t) (hi : IntervalIntegrable (fun t => D (c t) (w t)) MeasureTheory.volume a b) (hj : IntervalIntegrable (fun t => D (u t) (d t)) MeasureTheory.volume a b) : (∫ t in a..b, D (c t) (w t)) + (∫ t in a..b, D (u t) (d t)) = B (c b) (d b) - B (c a) (d a)",
    "  simp_rw [hD] at *\n  rw [← intervalIntegral.integral_add hi hj]\n  apply intervalIntegral.integral_eq_sub_of_hasDerivAt _ (hi.add hj)\n  intro t ht\n  exact B.hasDerivAt_of_bilinear (fun _ => hc t ht) (fun _ => hd t ht)",
    [
        "Use the supplied pointwise equality D(x)(y)=B(x,y) to identify both scalar contractions.",
        "Differentiate t↦B(c(t),d(t)) by the bilinear product rule.",
        "The derivative is B(c(t),w(t))+B(u(t),d(t)), preserving the order of both slots.",
        "The separate integrability hypotheses justify adding the integrals and applying the fundamental theorem.",
        "Evaluate the bilinear primitive at the two oriented endpoints.",
    ],
)


def main():
    witness_path = ROOT / "docs/multivariable-v5-line-supplement-batch.lean"
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
        "witness_path": "docs/multivariable-v5-line-supplement-batch.lean",
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
    (ROOT / "docs/multivariable-v5-line-supplement-batch.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    )
    print(f"Compiled and emitted {len(cards)} general multivariable cards.")


if __name__ == "__main__":
    main()
