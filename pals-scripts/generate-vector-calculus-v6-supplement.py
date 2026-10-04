"""Generate a constant-curl circulation supplement after compiling the exact Lean bundle."""

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
f, g, A, B, P, Q, x, y, z, s, lo, hi, c = map(
    v, ["f", "g", "A", "B", "P", "Q", "x", "y", "z", "s", "lo", "hi", "c"]
)
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
    "constant_curl_circulation",
    pd + [d("c", "Real")],
    q.imp(
        order,
        a("countable", s),
        a("continuous_on", P, closed),
        a("continuous_on", Q, closed),
        derivative_on(P, A, a("set_difference", interior, s)),
        derivative_on(Q, B, a("set_difference", interior, s)),
        a("integrable_on", a("curl", A, B), closed),
        q.bind(
            [d("z", "Point")],
            q.imp(a("member", z, closed), q.eq(a("apply", a("curl", A, B), z), c)),
        ),
        q.eq(
            a("boundary_circulation", P, Q, lo, hi),
            a(
                "real_mul",
                a("real_mul", c, a("real_sub", a("fst", hi), a("fst", lo))),
                a("real_sub", a("snd", hi), a("snd", lo)),
            ),
        ),
    ),
    "For P,Q continuous on an ordered planar rectangle, assume specified derivatives outside a countable interior exception set, integrable scalar curl, and constant curl c throughout the closed rectangle. Then the counterclockwise boundary line integral of P dx+Q dy equals c times the rectangle area. Individual side integrals need not be known and the field need not be a gradient.",
    "example (P Q : ℝ × ℝ → ℝ) (A B : ℝ × ℝ → (ℝ × ℝ) →L[ℝ] ℝ) (a b : ℝ × ℝ) (hab : a ≤ b) (s : Set (ℝ × ℝ)) (hs : s.Countable) (hP : ContinuousOn P (Set.Icc a b)) (hQ : ContinuousOn Q (Set.Icc a b)) (hA : ∀ z ∈ (Set.Ioo a.1 b.1 ×ˢ Set.Ioo a.2 b.2) \\ s, HasFDerivAt P (A z) z) (hB : ∀ z ∈ (Set.Ioo a.1 b.1 ×ˢ Set.Ioo a.2 b.2) \\ s, HasFDerivAt Q (B z) z) (hi : MeasureTheory.IntegrableOn (fun z => B z (1,0) - A z (0,1)) (Set.Icc a b)) (c : ℝ) (hcurl : ∀ z ∈ Set.Icc a b, B z (1,0) - A z (0,1) = c) :\n (((∫ x in a.1..b.1, P (x,a.2)) + (∫ y in a.2..b.2, Q (b.1,y))) - (∫ x in a.1..b.1, P (x,b.2))) - (∫ y in a.2..b.2, Q (a.1,y)) = c*(b.1-a.1)*(b.2-a.2)",
    " have hgreen :  (∫ z in Set.Icc a b, B z (1,0) - A z (0,1)) = (((∫ x in a.1..b.1, P (x,a.2)) + (∫ y in a.2..b.2, Q (b.1,y))) - (∫ x in a.1..b.1, P (x,b.2))) - (∫ y in a.2..b.2, Q (a.1,y)) := by\n   have h := MeasureTheory.integral_divergence_prod_Icc_of_hasFDerivAt_off_countable_of_le Q (fun z => -P z) B (fun z => -A z) a b hab s hs hQ hP.neg hB (fun z hz => (hA z hz).neg) (by simpa [sub_eq_add_neg] using hi)\n   simp only [neg_apply,intervalIntegral.integral_neg] at h\n   simpa only [sub_eq_add_neg] using h.trans (by ring)\n have he :  (∫ z in Set.Icc a b, B z (1,0) - A z (0,1)) = (∫ z in Set.Icc a b, c) := by\n  apply MeasureTheory.setIntegral_congr_fun measurableSet_Icc\n  intro z hz\n  exact hcurl z hz\n rw [he] at hgreen\n apply hgreen.symm.trans\n rw [MeasureTheory.setIntegral_const]\n simp only [MeasureTheory.measureReal_def, smul_eq_mul]\n have hv : MeasureTheory.volume (Set.Icc a b) = ENNReal.ofReal (b.1-a.1) * ENNReal.ofReal (b.2-a.2) := by\n  rw [show Set.Icc a b = Set.Icc a.1 b.1 ×ˢ Set.Icc a.2 b.2 by ext z; simp only [Set.mem_Icc,Prod.le_def,Set.mem_prod]; tauto]\n  change ((MeasureTheory.volume : MeasureTheory.Measure ℝ).prod MeasureTheory.volume) ((Set.Icc a.1 b.1) ×ˢ (Set.Icc a.2 b.2)) = _\n  rw [MeasureTheory.Measure.prod_prod,Real.volume_Icc,Real.volume_Icc]\n rw [hv,ENNReal.toReal_mul,ENNReal.toReal_ofReal (sub_nonneg.mpr hab.1),ENNReal.toReal_ofReal (sub_nonneg.mpr hab.2)]\n ring\n",
    [
        "Apply the weak Green theorem, retaining closed-boundary continuity, countable derivative exceptions, and curl integrability.",
        "Replace the area-integral integrand by c using the equality on the entire rectangle.",
        "Identify the rectangle as a product of its two closed coordinate intervals.",
        "Compute its Lebesgue measure as the product of the two nonnegative side lengths.",
        "Convert the constant area integral to c times this area, preserving counterclockwise boundary orientation.",
    ],
    "compute_construct",
    "advanced",
)
bindings[0]["family_id"] = "univ.multivar.line-surface-integrals"
bindings[0]["authoring_manifest"] = "docs/vector-calculus-v6-supplement.json"


def main():
    witness = ROOT / "docs/vector-calculus-v6-supplement.lean"
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
    (ROOT / "docs/vector-calculus-v6-supplement.json").write_text(
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
    (ROOT / "docs/vector-calculus-v6-supplement-bindings.json").write_text(
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
