"""Generate genuine planar Green/Gauss cards after compiling the exact Lean bundle."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pals-agent"))
from pals_agent.typed_vector_calculus_v6 import (
    canonicalize_typed_vector_calculus_v6_openmath_xml as canon,
)

WORKSPACE = ROOT / "pals-agent/lean-workspace"


class Grammar:
    def __init__(self, base, cd, typed, canon):
        self.base, self.cd, self.typed, self.canon = base, cd, typed, canon

    def s(self, name, cd=None):
        cd = cd or self.cd
        return f'<OMS cdbase="{self.base if cd in (self.cd, self.typed) else "http://www.openmath.org/cd"}" cd="{cd}" name="{name}"/>'

    def a(self, name, *args):
        return "<OMA>" + self.s(name) + "".join(args) + "</OMA>"

    def st(self, cd, name, *args):
        return "<OMA>" + self.s(name, cd) + "".join(args) + "</OMA>"

    def eq(self, x, y):
        return self.st("relation1", "eq", x, y)

    def ne(self, x, y):
        return self.st("relation1", "neq", x, y)

    def le(self, x, y):
        return self.st("relation1", "leq", x, y)

    def lt(self, x, y):
        return self.st("relation1", "lt", x, y)

    def neg(self, x):
        return self.st("logic1", "not", x)

    def both(self, *terms):
        out = terms[-1]
        for term in reversed(terms[:-1]):
            out = self.st("logic1", "and", term, out)
        return out

    def imp(self, *terms):
        out = terms[-1]
        for term in reversed(terms[:-1]):
            out = self.st("logic1", "implies", term, out)
        return out

    def iff(self, x, y):
        return self.both(self.imp(x, y), self.imp(y, x))

    def typ(self, name, *args):
        return self.a(name, *map(v, args)) if args else self.s(name)

    def d(self, name, ty, *args):
        return (name, self.typ(ty, *args))

    def bind(self, ds, body, kind="forall"):
        return (
            "<OMBIND>"
            + self.s(kind, self.typed)
            + "<OMBVAR>"
            + "".join(
                "<OMATTR><OMATP>"
                + self.s("type", self.typed)
                + ty
                + "</OMATP>"
                + v(name)
                + "</OMATTR>"
                for name, ty in ds
            )
            + "</OMBVAR>"
            + body
            + "</OMBIND>"
        )

    def real(self, n):
        return self.a("real_nat", f"<OMI>{n}</OMI>")


def v(name):
    return f'<OMV name="{name}"/>'


q = Grammar("urn:pals:openmath:typed-vector-calculus:v6", "vector6", "typed6", canon)
a = q.a
d = q.d
f, g, A, B, P, Q, x, y, z, s, lo, hi, c = map(v, ["f", "g", "A", "B", "P", "Q", "x", "y", "z", "s", "lo", "hi", "c"])
zero = q.real(0)
closed = a("closed_rectangle", lo, hi)
interior = a("open_rectangle", lo, hi)
order = q.both(q.le(a("fst", lo), a("fst", hi)), q.le(a("snd", lo), a("snd", hi)))
base = [d("lo", "Point"), d("hi", "Point")]
fd = [
    d("f", "ScalarFunction"),
    d("g", "ScalarFunction"),
    d("A", "DualField"),
    d("B", "DualField"),
] + base
pd = (
    [
        d("P", "ScalarFunction"),
        d("Q", "ScalarFunction"),
        d("A", "DualField"),
        d("B", "DualField"),
    ]
    + base
    + [d("s", "Set")]
)


def derivative_on(fn, field, domain):
    return q.bind(
        [d("z", "Point")],
        q.imp(
            a("member", z, domain), a("has_fderiv", fn, z, a("field_apply", field, z))
        ),
    )


cards = []
bindings = []


def add(key, ds, body, statement, target, proof, steps, mode, difficulty):
    cards.append(
        {
            "id": "vector_v6_" + key,
            "canonical_statement": statement,
            "proof_strategy": steps[0],
            "sketch_steps": steps,
            "openmath_xml": canon(
                '<OMOBJ xmlns="http://www.openmath.org/OpenMath" version="2.0">'
                + q.bind(ds, body)
                + "</OMOBJ>"
            ),
            "lean_target": target,
            "lean_witness": "by\n" + proof.rstrip(),
        }
    )
    bindings.append(
        {
            "family_id": "univ.multivar.integral-theorems",
            "draft_id": "vector_v6_" + key,
            "primary_mode": mode,
            "difficulty": difficulty,
            "authoring_manifest": "docs/vector-calculus-v6-batch.json",
            "admission_manifest": None,
        }
    )


add(
    "gauss_rectangle",
    fd,
    q.imp(
        order,
        a("continuous_on", f, closed),
        a("continuous_on", g, closed),
        derivative_on(f, A, interior),
        derivative_on(g, B, interior),
        a("integrable_on", a("divergence", A, B), closed),
        q.eq(
            a("set_integral", a("divergence", A, B), closed),
            a("boundary_flux", f, g, lo, hi),
        ),
    ),
    "For any ordered planar rectangle [a,b], let the vector-field components f,g be continuous on the closed rectangle, with actual derivative fields A,B throughout its open interior. If A(e₁)+B(e₂) is Lebesgue integrable on the rectangle, its area integral equals the outward boundary flux: top minus bottom plus right minus left.",
    "example (f g : ℝ × ℝ → ℝ) (A B : ℝ × ℝ → (ℝ × ℝ) →L[ℝ] ℝ) (a b : ℝ × ℝ) (hab : a ≤ b) (hf : ContinuousOn f (Set.Icc a b)) (hg : ContinuousOn g (Set.Icc a b)) (hA : ∀ z ∈ Set.Ioo a.1 b.1 ×ˢ Set.Ioo a.2 b.2, HasFDerivAt f (A z) z) (hB : ∀ z ∈ Set.Ioo a.1 b.1 ×ˢ Set.Ioo a.2 b.2, HasFDerivAt g (B z) z) (hi : MeasureTheory.IntegrableOn (fun z => A z (1,0) + B z (0,1)) (Set.Icc a b)) :\n (∫ z in Set.Icc a b, A z (1,0) + B z (0,1)) = (((∫ x in a.1..b.1, g (x,b.2)) - (∫ x in a.1..b.1, g (x,a.2))) + (∫ y in a.2..b.2, f (b.1,y))) - (∫ y in a.2..b.2, f (a.1,y))",
    " exact MeasureTheory.integral_divergence_prod_Icc_of_hasFDerivAt_of_le f g A B a b hab hf hg hA hB hi\n",
    [
        "Use the actual component derivatives to form the divergence.",
        "Continuity on the closed rectangle includes boundary continuity.",
        "Apply the planar rectangular Gauss theorem with the explicit divergence-integrability premise.",
        "Read the oriented boundary terms as top−bottom+right−left outward flux.",
    ],
    "justify_prove",
    "standard",
)

add(
    "green_countable_exceptions",
    pd,
    q.imp(
        order,
        a("countable", s),
        a("continuous_on", P, closed),
        a("continuous_on", Q, closed),
        derivative_on(P, A, a("set_difference", interior, s)),
        derivative_on(Q, B, a("set_difference", interior, s)),
        a("integrable_on", a("curl", A, B), closed),
        q.eq(
            a("set_integral", a("curl", A, B), closed),
            a("boundary_circulation", P, Q, lo, hi),
        ),
    ),
    "For any ordered planar rectangle, P,Q continuous on the closed rectangle may fail to have the specified derivatives A,B on a countable exceptional set in the interior. If the scalar curl B(e₁)−A(e₂) is integrable, its area integral equals the counterclockwise circulation of P dx+Q dy around the four sides. No differentiability is asserted on the exceptional set.",
    "example (P Q : ℝ × ℝ → ℝ) (A B : ℝ × ℝ → (ℝ × ℝ) →L[ℝ] ℝ) (a b : ℝ × ℝ) (hab : a ≤ b) (s : Set (ℝ × ℝ)) (hs : s.Countable) (hP : ContinuousOn P (Set.Icc a b)) (hQ : ContinuousOn Q (Set.Icc a b)) (hA : ∀ z ∈ (Set.Ioo a.1 b.1 ×ˢ Set.Ioo a.2 b.2) \\ s, HasFDerivAt P (A z) z) (hB : ∀ z ∈ (Set.Ioo a.1 b.1 ×ˢ Set.Ioo a.2 b.2) \\ s, HasFDerivAt Q (B z) z) (hi : MeasureTheory.IntegrableOn (fun z => B z (1,0) - A z (0,1)) (Set.Icc a b)) :\n (∫ z in Set.Icc a b, B z (1,0) - A z (0,1)) = (((∫ x in a.1..b.1, P (x,a.2)) + (∫ y in a.2..b.2, Q (b.1,y))) - (∫ x in a.1..b.1, P (x,b.2))) - (∫ y in a.2..b.2, Q (a.1,y))",
    " have h := MeasureTheory.integral_divergence_prod_Icc_of_hasFDerivAt_off_countable_of_le Q (fun z => -P z) B (fun z => -A z) a b hab s hs hQ hP.neg hB (fun z hz => (hA z hz).neg) (by simpa [sub_eq_add_neg] using hi)\n simp only [neg_apply,intervalIntegral.integral_neg] at h\n simpa only [sub_eq_add_neg] using h.trans (by ring)\n",
    [
        "Rotate the field to (Q,−P), whose divergence is the scalar curl.",
        "Retain closed-rectangle continuity and exclude only the supplied countable set from the interior derivative hypotheses.",
        "Apply Gauss with countable derivative exceptions and the stated curl-integrability premise.",
        "Negate the horizontal integrals and collect the bottom/right/top/left terms in counterclockwise order.",
    ],
    "justify_prove",
    "advanced",
)

add(
    "affine_flux",
    base + [d(k, "Real") for k in ["alpha", "beta", "gamma", "delta", "p", "q"]],
    q.eq(
        a(
            "boundary_flux",
            a("affine", v("alpha"), v("beta"), v("p")),
            a("affine", v("gamma"), v("delta"), v("q")),
            lo,
            hi,
        ),
        a(
            "real_mul",
            a(
                "real_mul",
                a("real_add", v("alpha"), v("delta")),
                a("real_sub", a("fst", hi), a("fst", lo)),
            ),
            a("real_sub", a("snd", hi), a("snd", lo)),
        ),
    ),
    "For the general affine planar field (αx+βy+p, γx+δy+q), the signed four-side flux formula is (α+δ)(b₁−a₁)(b₂−a₂). For ordered endpoints it is the outward flux through the rectangle; the algebraic identity also holds for reversed or degenerate endpoint choices.",
    "example (a b : ℝ × ℝ) (α β γ δ p q : ℝ) :\n (((∫ x in a.1..b.1, (γ*x+δ*b.2+q)) - (∫ x in a.1..b.1, (γ*x+δ*a.2+q))) + (∫ y in a.2..b.2, (α*b.1+β*y+p))) - (∫ y in a.2..b.2, (α*a.1+β*y+p)) = (α+δ)*(b.1-a.1)*(b.2-a.2)",
    " have h₁ : (∫ x in a.1..b.1, γ*x+δ*b.2+q) - (∫ x in a.1..b.1, γ*x+δ*a.2+q) = δ*(b.2-a.2)*(b.1-a.1) := by\n   rw [← intervalIntegral.integral_sub (Continuous.intervalIntegrable (by fun_prop) _ _) (Continuous.intervalIntegrable (by fun_prop) _ _)]\n   have he : (fun x : ℝ => (γ*x+δ*b.2+q)-(γ*x+δ*a.2+q)) = fun _ => δ*(b.2-a.2) := by funext x; ring\n   rw [he,intervalIntegral.integral_const]\n   simp only [smul_eq_mul]; ring\n have h₂ : (∫ y in a.2..b.2, α*b.1+β*y+p) - (∫ y in a.2..b.2, α*a.1+β*y+p) = α*(b.1-a.1)*(b.2-a.2) := by\n   rw [← intervalIntegral.integral_sub (Continuous.intervalIntegrable (by fun_prop) _ _) (Continuous.intervalIntegrable (by fun_prop) _ _)]\n   have he : (fun y : ℝ => (α*b.1+β*y+p)-(α*a.1+β*y+p)) = fun _ => α*(b.1-a.1) := by funext y; ring\n   rw [he,intervalIntegral.integral_const]\n   simp only [smul_eq_mul]; ring\n calc\n  _ = ((∫ x in a.1..b.1, γ*x+δ*b.2+q) - (∫ x in a.1..b.1, γ*x+δ*a.2+q)) + ((∫ y in a.2..b.2, α*b.1+β*y+p) - (∫ y in a.2..b.2, α*a.1+β*y+p)) := by ring\n  _ = _ := by rw [h₁,h₂]; ring\n",
    [
        "Pair the top and bottom integrals, whose x-dependent and constant terms cancel.",
        "Their difference is δ times the height times the width.",
        "Pair the right and left integrals; their difference is α times the width times the height.",
        "Add the two contributions to obtain the trace coefficient α+δ times signed area.",
    ],
    "compute_construct",
    "introductory",
)

add(
    "c1_gauss_hypotheses",
    [d("f", "ScalarFunction"), d("g", "ScalarFunction")] + base,
    q.imp(
        a("cont_diff_one", f),
        a("cont_diff_one", g),
        q.both(
            a("continuous_on", f, closed),
            a("continuous_on", g, closed),
            q.bind(
                [d("z", "Point")],
                a("has_fderiv", f, z, a("field_apply", a("fderiv_field", f), z)),
            ),
            q.bind(
                [d("z", "Point")],
                a("has_fderiv", g, z, a("field_apply", a("fderiv_field", g), z)),
            ),
            a(
                "integrable_on",
                a("divergence", a("fderiv_field", f), a("fderiv_field", g)),
                closed,
            ),
        ),
    ),
    "If planar f and g are globally C¹, then on every closed bounded rectangle they are continuous, their totalized fderiv fields are actual derivatives at every point, and their divergence is Lebesgue integrable. Thus global C¹ regularity supplies the analytic Gauss hypotheses; endpoint ordering is a separate geometric condition.",
    "example (f g : ℝ × ℝ → ℝ) (a b : ℝ × ℝ) (hf : ContDiff ℝ 1 f) (hg : ContDiff ℝ 1 g) :\n ContinuousOn f (Set.Icc a b) ∧ ContinuousOn g (Set.Icc a b) ∧ (∀ z, HasFDerivAt f (fderiv ℝ f z) z) ∧ (∀ z, HasFDerivAt g (fderiv ℝ g z) z) ∧ MeasureTheory.IntegrableOn (fun z => fderiv ℝ f z (1,0) + fderiv ℝ g z (0,1)) (Set.Icc a b)",
    " refine ⟨hf.continuous.continuousOn,hg.continuous.continuousOn,?_,?_,?_⟩\n · intro z; exact (hf.differentiable (by norm_num) z).hasFDerivAt\n · intro z; exact (hg.differentiable (by norm_num) z).hasFDerivAt\n have hfc := hf.continuous_fderiv (by norm_num)\n have hgc := hg.continuous_fderiv (by norm_num)\n exact (hfc.clm_apply continuous_const |>.add (hgc.clm_apply continuous_const)).integrableOn_Icc\n",
    [
        "Global C¹ regularity implies continuity on the closed rectangle.",
        "It also provides actual derivatives everywhere, so fderiv is not being used without a differentiability certificate.",
        "The derivative fields are continuous; evaluating them on fixed coordinate directions and adding preserves continuity.",
        "A continuous divergence is integrable on the compact rectangle.",
    ],
    "recognize",
    "standard",
)

add(
    "missing_boundary_continuity",
    base + [d("c", "Real")],
    q.imp(
        q.lt(a("fst", lo), a("fst", hi)),
        q.lt(a("snd", lo), a("snd", hi)),
        q.ne(c, zero),
        q.bind(
            [d("f", "ScalarFunction")],
            q.both(
                q.bind(
                    [d("z", "Point")],
                    q.imp(
                        a("member", z, interior),
                        a("has_fderiv", f, z, q.s("zero_dual")),
                    ),
                ),
                q.ne(
                    a(
                        "real_sub",
                        a(
                            "interval_integral",
                            a("vertical_slice", f, a("fst", hi)),
                            a("snd", lo),
                            a("snd", hi),
                        ),
                        a(
                            "interval_integral",
                            a("vertical_slice", f, a("fst", lo)),
                            a("snd", lo),
                            a("snd", hi),
                        ),
                    ),
                    zero,
                ),
            ),
            "exists",
        ),
    ),
    "For any rectangle with positive width and height and any nonzero c, there exists a scalar component f whose actual derivative is zero at every interior point, yet its right-side flux minus left-side flux is nonzero. Taking the other vector-field component to be zero gives zero interior divergence but nonzero boundary flux: interior differentiability alone cannot replace boundary continuity in Gauss.",
    "example (a b : ℝ × ℝ) (ha : a.1 < b.1) (hb : a.2 < b.2) (c : ℝ) (hc : c ≠ 0) :\n ∃ f : ℝ × ℝ → ℝ, (∀ z ∈ Set.Ioo a.1 b.1 ×ˢ Set.Ioo a.2 b.2, HasFDerivAt f (0 : (ℝ × ℝ) →L[ℝ] ℝ) z) ∧ (((∫ y in a.2..b.2, f (b.1,y))) - (∫ y in a.2..b.2, f (a.1,y))) ≠ 0",
    " let f : ℝ × ℝ → ℝ := fun z => if z.1 = a.1 then c else 0\n refine ⟨f,?_,?_⟩\n · intro z hz\n   apply hasFDerivAt_zero_of_eventually_const (0 : ℝ)\n   have hn : z.1 ≠ a.1 := ne_of_gt hz.1.1\n   have he : ∀ᶠ w in nhds z, w.1 ≠ a.1 := continuousAt_fst.eventually_ne hn\n   filter_upwards [he] with w hw\n   simp [f,hw]\n · simp only [f,ne_of_gt ha,↓reduceIte,eq_self,intervalIntegral.integral_zero,intervalIntegral.integral_const,smul_eq_mul,zero_sub,neg_ne_zero]\n   exact mul_ne_zero (sub_ne_zero.mpr (ne_of_gt hb)) hc\n",
    [
        "Put f=c on the left boundary line and zero off that line.",
        "Every interior point has a neighborhood disjoint from the left line, so the actual derivative there is zero.",
        "The right-face integral is zero and the left-face integral is c times the positive height.",
        "Their difference is nonzero, giving a general counterexample to dropping boundary continuity.",
    ],
    "counterexample_audit",
    "standard",
)


def main():
    witness = ROOT / "docs/vector-calculus-v6-batch.lean"
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
    result = subprocess.run(
        ["lake", "env", "lean", str(witness)],
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
    evidence = {
        "witness_path": str(witness.relative_to(ROOT)),
        "witness_sha256": sha(witness),
        "validator_sha256": sha(
            ROOT / "pals-agent/pals_agent/typed_vector_calculus_v6.py"
        ),
        "registry_sha256": sha(
            ROOT
            / "pals-agent/pals_agent/content_dictionaries/typed-vector-calculus-v6-registry.json"
        ),
        "toolchain": (WORKSPACE / "lean-toolchain").read_text().strip(),
        "mathlib_revision": next(
            p["rev"]
            for p in json.loads((WORKSPACE / "lake-manifest.json").read_text())[
                "packages"
            ]
            if p["name"] == "mathlib"
        ),
    }
    (ROOT / "docs/vector-calculus-v6-batch.json").write_text(
        json.dumps(
            {
                "schema_version": "pals.typed-catalog-expansion-batch.v1",
                "profile_id": "typed-vector-calculus-v6",
                "cards": cards,
                "evidence": evidence,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )
    (ROOT / "docs/vector-calculus-v6-bindings.json").write_text(
        json.dumps(
            {
                "schema_version": "pals.proposed-explicit-curriculum-bindings.v1",
                "status": "proposed_for_parent_review",
                "bindings": bindings,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )
    print(f"Compiled and emitted {len(cards)} general Green/Gauss cards.")


if __name__ == "__main__":
    main()
