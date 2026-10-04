"""Compile targeted foundation supplements without modifying existing profiles or batches."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pals-agent"))
from pals_agent.typed_calculus_v4 import (
    canonicalize_typed_calculus_v4_openmath_xml as canon4,
)
from pals_agent.typed_multivariable_v5 import (
    canonicalize_typed_multivariable_v5_openmath_xml as canon5,
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


G5 = Grammar("urn:pals:openmath:typed-multivariable:v5", "multivar5", "typed5", canon5)
G4 = Grammar("urn:pals:openmath:typed-calculus:v4", "calculus4", "typed4", canon4)
BATCHES = {5: [], 4: []}
BINDINGS = []


def add(
    version, key, ds, body, statement, target, proof, steps, family, mode, difficulty
):
    grammar = {5: G5, 4: G4}[version]
    card = {
        "id": "mv_foundation_" + key,
        "canonical_statement": statement,
        "proof_strategy": steps[0],
        "sketch_steps": steps,
        "openmath_xml": grammar.canon(
            '<OMOBJ xmlns="http://www.openmath.org/OpenMath" version="2.0">'
            + grammar.bind(ds, body)
            + "</OMOBJ>"
        ),
        "lean_target": target,
        "lean_witness": "by\n" + proof.rstrip(),
    }
    BATCHES[version].append(card)
    stem = {5: "multivariable-v5", 4: "calculus-v4"}[version]
    BINDINGS.append(
        {
            "family_id": "univ.multivar." + family,
            "draft_id": card["id"],
            "primary_mode": mode,
            "difficulty": difficulty,
            "authoring_manifest": f"docs/{stem}-foundation-supplement.json",
            "admission_manifest": None,
        }
    )


q = G5
a = q.a
d = q.d
n, m, k, x, y, u, w, f, g, A, B, H, D, c, t, i, j = map(
    v, ["n", "m", "k", "x", "y", "u", "w", "f", "g", "A", "B", "H", "D", "c", "t", "i", "j"]
)
Z = q.real(0)
add(
    5,
    "partial_value_criterion",
    [
        d("n", "Nat"),
        d("f", "ScalarFunction", "n"),
        d("A", "ScalarCLM", "n"),
        d("x", "Vector", "n"),
        d("i", "Index", "n"),
        d("c", "Real"),
    ],
    q.imp(
        a("has_scalar_fderiv", n, f, x, A),
        q.iff(
            a(
                "has_deriv",
                a("coordinate_slice", n, f, x, i),
                a("coordinate", n, x, i),
                c,
            ),
            q.eq(c, a("dual_apply", n, A, a("basis_vector", n, i))),
        ),
    ),
    "Given an actual total derivative A of a scalar f on ℝⁿ at x, a proposed ith coordinate partial value c is valid exactly when c=A(eᵢ). The coordinate slice is evaluated at xᵢ.",
    "example (n : ℕ) (f : (Fin n → ℝ) → ℝ) (A : (Fin n → ℝ) →L[ℝ] ℝ) (x : Fin n → ℝ) (i : Fin n) (c : ℝ) (hf : HasFDerivAt f A x) : HasDerivAt (fun t => f (Function.update x i t)) c (x i) ↔ c = A (Pi.single i 1)",
    "  have hh : HasFDerivAt f A (Function.update x i (x i)) := by simpa using hf\n  have hd := hh.comp_hasDerivAt (x i) (hasDerivAt_update x i (x i))\n  constructor\n  · intro hc\n    exact hc.unique hd\n  · intro he\n    simpa [he] using! hd",
    [
        "Use the known total derivative to obtain an actual derivative of the coordinate slice.",
        "The update curve passes through x at parameter xᵢ with velocity eᵢ.",
        "Uniqueness forces any proposed coordinate partial c to equal A(eᵢ).",
        "Conversely, that equality identifies c with the already established derivative.",
    ],
    "partials",
    "recognize",
    "introductory",
)
add(
    5,
    "zero_totalized_jacobian_counterexample",
    [d("m", "Nat"), d("n", "Nat"), d("i", "Index", "m"), d("j", "Index", "n")],
    q.bind(
        [d("f", "Function", "m", "n")],
        q.both(
            q.neg(a("differentiable_at", m, n, f, a("zero", m))),
            q.bind(
                [d("r", "Index", "n"), d("s", "Index", "m")],
                q.eq(
                    a(
                        "matrix_entry",
                        n,
                        m,
                        a("jacobian", m, n, f, a("zero", m)),
                        v("r"),
                        v("s"),
                    ),
                    Z,
                ),
            ),
        ),
        "exists",
    ),
    "For arbitrary nonempty coordinate dimensions m,n, there exists f:ℝᵐ→ℝⁿ that is not differentiable at the origin while every entry of Lean’s totalized Jacobian there is zero. Therefore a zero Jacobian expression without a differentiability premise is not evidence of an actual zero derivative.",
    "example (m n : ℕ) (i : Fin m) (j : Fin n) : ∃ f : (Fin m → ℝ) → (Fin n → ℝ), ¬DifferentiableAt ℝ f 0 ∧ ∀ r c, LinearMap.toMatrix' (fderiv ℝ f 0).toLinearMap r c = 0",
    "  let f : (Fin m → ℝ) → (Fin n → ℝ) := fun x _ => |x i|\n  have hn : ¬DifferentiableAt ℝ f 0 := by\n    intro h\n    have hs : DifferentiableAt ℝ (fun t : ℝ => f (Pi.single i t) j) 0 := by\n      have hp : DifferentiableAt ℝ (fun x => f x j) (Pi.single i (0 : ℝ)) := by\n        simpa using (differentiableAt_pi.mp h) j\n      simpa [Function.comp_def] using! hp.comp (0 : ℝ) (hasFDerivAt_single (𝕜 := ℝ) (E := fun _ : Fin m => ℝ) (i := i) (0 : ℝ)).differentiableAt\n    apply not_differentiableAt_abs_zero\n    simpa [f] using hs\n  refine ⟨f,hn,?_⟩\n  intro r c\n  simp [fderiv_zero_of_not_differentiableAt hn]",
    [
        "Construct every output coordinate as the absolute value of one chosen input coordinate.",
        "If the map were differentiable, restricting to that coordinate line and projecting to an output would make absolute value differentiable at zero.",
        "This contradicts nondifferentiability of absolute value at zero.",
        "Lean totalizes fderiv to zero in this case, and its standard matrix has all entries zero.",
    ],
    "total-jacobian",
    "counterexample_audit",
    "standard",
)
add(
    5,
    "jacobian_curve_velocity",
    [
        d("m", "Nat"),
        d("n", "Nat"),
        d("f", "Function", "m", "n"),
        d("c", "Curve", "m"),
        d("u", "Vector", "m"),
        d("t", "Real"),
    ],
    q.imp(
        a("differentiable_at", m, n, f, a("curve_apply", m, c, t)),
        a("has_curve_deriv", m, c, t, u),
        q.bind(
            [d("g", "Curve", "n")],
            q.both(
                q.bind(
                    [d("s", "Real")],
                    q.eq(
                        a("curve_apply", n, g, v("s")),
                        a("apply", m, n, f, a("curve_apply", m, c, v("s"))),
                    ),
                ),
                a(
                    "has_curve_deriv",
                    n,
                    g,
                    t,
                    a(
                        "matrix_action",
                        n,
                        m,
                        a("jacobian", m, n, f, a("curve_apply", m, c, t)),
                        u,
                    ),
                ),
            ),
            "exists",
        ),
    ),
    "For differentiable f:ℝᵐ→ℝⁿ at c(t) and a curve c with velocity u at t, the composite curve s↦f(c(s)) has velocity Jf(c(t))u. The dimensions and matrix multiplication order are explicit.",
    "example (m n : ℕ) (f : (Fin m → ℝ) → (Fin n → ℝ)) (c : ℝ → (Fin m → ℝ)) (u : Fin m → ℝ) (t : ℝ) (hf : DifferentiableAt ℝ f (c t)) (hc : HasDerivAt c u t) : ∃ g : ℝ → (Fin n → ℝ), (∀ s, g s = f (c s)) ∧ HasDerivAt g ((LinearMap.toMatrix' (fderiv ℝ f (c t)).toLinearMap).mulVec u) t",
    "  refine ⟨fun s => f (c s),fun _ => rfl,?_⟩\n  simpa only [LinearMap.toMatrix'_mulVec, ContinuousLinearMap.coe_coe] using! hf.hasFDerivAt.comp_hasDerivAt t hc",
    [
        "Construct the composite curve explicitly.",
        "Apply the curve chain rule using the actual derivative at c(t).",
        "Convert the derivative map into its standard-coordinate Jacobian.",
        "Its application to u is exactly matrix-vector multiplication Jf(c(t))u.",
    ],
    "total-jacobian",
    "synthesize",
    "advanced",
)
add(
    5,
    "quadratic_hessian_criterion",
    [
        d("n", "Nat"),
        d("B", "Bilinear", "n"),
        d("H", "Bilinear", "n"),
        d("x", "Vector", "n"),
    ],
    q.iff(
        a("has_field_derivative", n, a("quadratic_field", n, B), x, H),
        q.eq(H, a("symmetrize", n, B)),
    ),
    "For the quadratic form x↦B(x,x), a proposed derivative H of its first-derivative field is correct at any x exactly when H=B+B.flip. This identifies the Hessian including nonsymmetric presentations of the same quadratic form.",
    "example (n : ℕ) (B H : (Fin n → ℝ) →L[ℝ] (Fin n → ℝ) →L[ℝ] ℝ) (x : Fin n → ℝ) : HasFDerivAt (fun y => B y + B.flip y) H x ↔ H = B + B.flip",
    "  have hd : HasFDerivAt (fun y => B y + B.flip y) (B+B.flip) x := B.hasFDerivAt.add B.flip.hasFDerivAt\n  constructor\n  · intro hh\n    exact hh.unique hd\n  · intro he\n    simpa [he] using! hd",
    [
        "Identify the quadratic first-derivative field as x↦B x+B.flip x.",
        "Its derivative is the constant bilinear form B+B.flip.",
        "Derivative uniqueness gives the necessary condition on a proposed H.",
        "Substitution of H=B+B.flip proves the converse.",
    ],
    "hessian-taylor",
    "recognize",
    "introductory",
)
add(
    5,
    "quadratic_hessian_missing_flip_counterexample",
    [
        d("n", "Nat"),
        d("B", "Bilinear", "n"),
        d("x", "Vector", "n"),
        d("u", "Vector", "n"),
        d("w", "Vector", "n"),
    ],
    q.imp(
        q.ne(a("bilinear_apply", n, B, u, w), Z),
        q.neg(a("has_field_derivative", n, a("quadratic_field", n, B), x, B)),
    ),
    "If a bilinear form B has a nonzero value B(u,w), then B itself is not the Hessian of x↦B(x,x) at any point. The missing transpose contribution cannot be discarded, even in the one-dimensional nonzero quadratic case.",
    "example (n : ℕ) (B : (Fin n → ℝ) →L[ℝ] (Fin n → ℝ) →L[ℝ] ℝ) (x u w : Fin n → ℝ) (hB : B u w ≠ 0) : ¬HasFDerivAt (fun y => B y + B.flip y) B x",
    "  intro hh\n  have hd : HasFDerivAt (fun y => B y + B.flip y) (B+B.flip) x := B.hasFDerivAt.add B.flip.hasFDerivAt\n  have he := hh.unique hd\n  have hv := congrArg (fun C : (Fin n → ℝ) →L[ℝ] (Fin n → ℝ) →L[ℝ] ℝ => C w u) he\n  simp only [add_apply, ContinuousLinearMap.flip_apply] at hv\n  apply hB\n  linarith",
    [
        "Use the actual Hessian B+B.flip.",
        "If B were another derivative, uniqueness would identify B with B+B.flip.",
        "Evaluate this identity on the reversed pair (w,u).",
        "The resulting equality forces B(u,w)=0, contradicting the supplied nonzero witness.",
    ],
    "hessian-taylor",
    "counterexample_audit",
    "standard",
)
lds = [
    d("n", "Nat"),
    d("f", "ScalarFunction", "n"),
    d("g", "ScalarFunction", "n"),
    d("A", "ScalarCLM", "n"),
    d("B", "ScalarCLM", "n"),
    d("x", "Vector", "n"),
    d("u", "Vector", "n"),
]
add(
    5,
    "lagrange_multiplier_from_direction",
    lds,
    q.imp(
        a("local_extr_fiber", n, g, f, x),
        a("has_scalar_strict_fderiv", n, f, x, A),
        a("has_scalar_strict_fderiv", n, g, x, B),
        q.ne(a("dual_apply", n, A, u), Z),
        q.bind(
            [d("c", "Real")],
            q.both(
                q.eq(B, a("dual_scale", n, c, A)),
                q.eq(
                    a("real_mul", c, a("dual_apply", n, A, u)), a("dual_apply", n, B, u)
                ),
                q.bind(
                    [d("t", "Real")],
                    q.imp(
                        q.eq(
                            a("real_mul", t, a("dual_apply", n, A, u)),
                            a("dual_apply", n, B, u),
                        ),
                        q.eq(t, c),
                    ),
                ),
            ),
            "exists",
        ),
    ),
    "At a constrained local extremum of g on f=f(x), assume strict derivatives A,B and choose a direction u with A(u)≠0. Then the unique normalized multiplier c is determined by c A(u)=B(u), and the full derivative identity is B=cA. Thus one scalar division computes the multiplier after the regularity check.",
    "example (n : ℕ) (f g : (Fin n → ℝ) → ℝ) (A B : (Fin n → ℝ) →L[ℝ] ℝ) (x u : Fin n → ℝ) (he : IsLocalExtrOn g {y | f y = f x} x) (hf : HasStrictFDerivAt f A x) (hg : HasStrictFDerivAt g B x) (hu : A u ≠ 0) : ∃ c : ℝ, B = c • A ∧ c * A u = B u ∧ ∀ t : ℝ, t * A u = B u → t = c",
    "  have hA : A ≠ 0 := by intro h; exact hu (by simp [h])\n  obtain ⟨a,b,hne,heq⟩ := he.exists_multipliers_of_hasStrictFDerivAt_1d hf hg\n  have hb : b ≠ 0 := by\n    intro hb\n    have haz : a • A = 0 := by simpa [hb] using heq\n    have ha : a = 0 := (smul_eq_zero.mp haz).resolve_right hA\n    exact hne (by simp [ha,hb])\n  have he : B = (-a / b) • A := by\n    ext v\n    have hh := congrArg (fun C : (Fin n → ℝ) →L[ℝ] ℝ => C v) heq\n    simp only [add_apply, smul_apply, smul_eq_mul, zero_apply] at hh ⊢\n    field_simp\n    nlinarith [hh]\n  have hv : B u = (-a/b) * A u := by simpa only [smul_apply,smul_eq_mul] using congrArg (fun C : (Fin n → ℝ) →L[ℝ] ℝ => C u) he\n  refine ⟨-a/b,he,hv.symm,?_⟩\n  intro t ht\n  exact mul_right_cancel₀ hu (ht.trans hv)",
    [
        "The nonzero directional constraint derivative proves regularity.",
        "Obtain and normalize the weak Lagrange multipliers.",
        "Evaluate the resulting functional identity on u to get cA(u)=B(u).",
        "Since A(u)≠0, cancellation makes this scalar equation determine c uniquely.",
    ],
    "lagrange",
    "compute_construct",
    "introductory",
)
add(
    5,
    "singular_constraint_counterexample",
    [d("n", "Nat"), d("A", "ScalarCLM", "n"), d("u", "Vector", "n")],
    q.imp(
        q.ne(a("dual_apply", n, A, u), Z),
        q.bind(
            [d("f", "ScalarFunction", "n"), d("g", "ScalarFunction", "n")],
            q.both(
                a("local_extr_fiber", n, g, f, a("zero", n)),
                a("has_scalar_strict_fderiv", n, f, a("zero", n), a("dual_zero", n)),
                a("has_scalar_strict_fderiv", n, g, a("zero", n), A),
                q.bind(
                    [d("c", "Real")], q.ne(A, a("dual_scale", n, c, a("dual_zero", n)))
                ),
            ),
            "exists",
        ),
    ),
    "For any nonzero linear functional A on ℝⁿ, witnessed by A(u)≠0, there are strictly differentiable constraint and objective functions with a constrained extremum at zero, zero constraint derivative, and objective derivative A. No normalized multiplier represents A as a multiple of the zero constraint derivative.",
    "example (n : ℕ) (A : (Fin n → ℝ) →L[ℝ] ℝ) (u : Fin n → ℝ) (hu : A u ≠ 0) : ∃ f g : (Fin n → ℝ) → ℝ, IsLocalExtrOn g {y | f y = f 0} 0 ∧ HasStrictFDerivAt f (0 : (Fin n → ℝ) →L[ℝ] ℝ) 0 ∧ HasStrictFDerivAt g A 0 ∧ ∀ c : ℝ, A ≠ c • (0 : (Fin n → ℝ) →L[ℝ] ℝ)",
    "  refine ⟨fun x => (A x)^2, fun x => A x, ?_, ?_, A.hasStrictFDerivAt, ?_⟩\n  · left\n    apply IsMinOn.localize\n    intro y hy\n    have hy0 : A y = 0 := by simpa using (sq_eq_zero_iff.mp (by simpa using hy))\n    simp [hy0]\n  · simpa using (A.hasStrictFDerivAt (x := (0 : Fin n → ℝ))).pow 2\n  · intro c he\n    apply hu\n    have hh := congrArg (fun C : (Fin n → ℝ) →L[ℝ] ℝ => C u) he\n    simpa using hh",
    [
        "Choose the constraint f(x)=A(x)² and objective g(x)=A(x).",
        "On the level set f=0, A vanishes, so the objective is constant and has a constrained local minimum.",
        "The strict derivative of f at zero is zero, while that of g is A.",
        "Any normalized multiplier would force A=0, contradicting A(u)≠0.",
    ],
    "lagrange",
    "counterexample_audit",
    "standard",
)
# A genuinely exceptional section of an integrable product-space function.
section = a("product_scalar_slice_right", m, n, f, a("zero", m))
proof_source = "import Mathlib\nexample (m n : ℕ) (i : Fin m) (j : Fin n) (a : ℝ) (ha : a ≠ 0) :\n ∃ f : ((Fin m → ℝ) × (Fin n → ℝ)) → ℝ,\n MeasureTheory.Integrable f ∧ (∀ y, f (0,y) = a) ∧ ¬ MeasureTheory.Integrable (fun y => f (0,y)) := by\n letI : Nonempty (Fin m) := ⟨i⟩\n letI : Nonempty (Fin n) := ⟨j⟩\n let f : ((Fin m → ℝ) × (Fin n → ℝ)) → ℝ := fun z => if z.1 = 0 then a else 0\n have hae : f =ᵐ[MeasureTheory.volume] (fun _ => 0) := by\n   apply MeasureTheory.ae_iff.mpr\n   have hz : MeasureTheory.volume (({0} : Set (Fin m → ℝ)) ×ˢ (Set.univ : Set (Fin n → ℝ))) = 0 := by\n     change ((MeasureTheory.volume : MeasureTheory.Measure (Fin m → ℝ)).prod (MeasureTheory.volume : MeasureTheory.Measure (Fin n → ℝ))) _ = 0\n     rw [MeasureTheory.Measure.prod_prod]\n     simp\n   have hset : {z | ¬ f z = 0} = ({0} : Set (Fin m → ℝ)) ×ˢ (Set.univ : Set (Fin n → ℝ)) := by\n     ext z\n     simp [f,ha]\n   rw [hset]\n   exact hz\n refine ⟨f, (MeasureTheory.integrable_zero _ ℝ MeasureTheory.volume).congr hae.symm, ?_, ?_⟩\n · intro y; simp [f]\n · intro hh\n   have hh' : MeasureTheory.Integrable (fun _ : Fin n → ℝ => a) := by simpa [f] using hh\n   letI : MeasureTheory.IsFiniteMeasure (MeasureTheory.volume : MeasureTheory.Measure (Fin n → ℝ)) := (MeasureTheory.integrable_const_iff_isFiniteMeasure ha).mp hh'\n   have hne := MeasureTheory.measure_ne_top (MeasureTheory.volume : MeasureTheory.Measure (Fin n → ℝ)) Set.univ\n   have hv : MeasureTheory.volume (Set.univ : Set (Fin n → ℝ)) = ⊤ := by\n     change (MeasureTheory.Measure.pi (fun _ : Fin n => (MeasureTheory.volume : MeasureTheory.Measure ℝ))) Set.univ = ⊤\n     rw [MeasureTheory.Measure.pi_univ]\n     simp [Nat.ne_of_gt (Nat.zero_lt_of_lt j.isLt)]\n   exact hne hv\n"
# Replaced below with a literal proof for reproducible generation.
add(
    5,
    "exceptional_section_counterexample",
    [
        d("m", "Nat"),
        d("n", "Nat"),
        d("i", "Index", "m"),
        d("j", "Index", "n"),
        d("c", "Real"),
    ],
    q.imp(
        q.ne(c, Z),
        q.bind(
            [d("f", "ProductScalarFunction", "m", "n")],
            q.both(
                a("product_integrable", m, n, f),
                q.bind(
                    [d("y", "Vector", "n")], q.eq(a("scalar_apply", n, section, y), c)
                ),
                q.neg(a("integrable", n, section)),
            ),
            "exists",
        ),
    ),
    "For all nonempty coordinate dimensions m,n and nonzero real c, there exists a Lebesgue-integrable f on ℝᵐ×ℝⁿ whose entire section at x=0 equals c and is not integrable. Fubini ensures integrable sections almost everywhere, not at every point.",
    proof_source[proof_source.index("example ") : proof_source.index(" := by")]
    .replace("(a : ℝ) (ha : a ≠ 0)", "(c : ℝ) (hc : c ≠ 0)")
    .replace("= a", "= c"),
    " letI : Nonempty (Fin m) := ⟨i⟩\n letI : Nonempty (Fin n) := ⟨j⟩\n let f : ((Fin m → ℝ) × (Fin n → ℝ)) → ℝ := fun z => if z.1 = 0 then c else 0\n have hae : f =ᵐ[MeasureTheory.volume] (fun _ => 0) := by\n   apply MeasureTheory.ae_iff.mpr\n   have hz : MeasureTheory.volume (({0} : Set (Fin m → ℝ)) ×ˢ (Set.univ : Set (Fin n → ℝ))) = 0 := by\n     change ((MeasureTheory.volume : MeasureTheory.Measure (Fin m → ℝ)).prod (MeasureTheory.volume : MeasureTheory.Measure (Fin n → ℝ))) _ = 0\n     rw [MeasureTheory.Measure.prod_prod]\n     simp\n   have hset : {z | ¬ f z = 0} = ({0} : Set (Fin m → ℝ)) ×ˢ (Set.univ : Set (Fin n → ℝ)) := by\n     ext z\n     simp [f,hc]\n   rw [hset]\n   exact hz\n refine ⟨f, (MeasureTheory.integrable_zero _ ℝ MeasureTheory.volume).congr hae.symm, ?_, ?_⟩\n · intro y; simp [f]\n · intro hh\n   have hh' : MeasureTheory.Integrable (fun _ : Fin n → ℝ => c) := by simpa [f] using hh\n   letI : MeasureTheory.IsFiniteMeasure (MeasureTheory.volume : MeasureTheory.Measure (Fin n → ℝ)) := (MeasureTheory.integrable_const_iff_isFiniteMeasure hc).mp hh'\n   have hne := MeasureTheory.measure_ne_top (MeasureTheory.volume : MeasureTheory.Measure (Fin n → ℝ)) Set.univ\n   have hv : MeasureTheory.volume (Set.univ : Set (Fin n → ℝ)) = ⊤ := by\n     change (MeasureTheory.Measure.pi (fun _ : Fin n => (MeasureTheory.volume : MeasureTheory.Measure ℝ))) Set.univ = ⊤\n     rw [MeasureTheory.Measure.pi_univ]\n     simp [Nat.ne_of_gt (Nat.zero_lt_of_lt j.isLt)]\n   exact hne hv\n",
    [
        "Set f(x,y)=c when x=0 and zero otherwise.",
        "The exceptional hyperplane has product measure zero, so f is almost everywhere zero and integrable.",
        "Its section at x=0 is the nonzero constant c.",
        "Lebesgue measure of positive-dimensional ℝⁿ is infinite, hence that constant section is not integrable.",
    ],
    "multiple-integrals",
    "counterexample_audit",
    "standard",
)

q = G4
a = q.a
d = q.d
E, F, x, y, u, c, A, b, f = map(v, ["E", "F", "x", "y", "u", "c", "A", "b", "f"])
Z = q.real(0)
zero = a("vector_zero", E)
base = [d("E", "RealInnerProductSpace")]
quad = a("scalar_scale", E, c, a("norm_square", E))
residual = a(
    "norm_square_composition",
    E,
    F,
    a("affine_function", E, F, A, a("vector_sub", F, a("vector_zero", F), b)),
)

add(
    4,
    "stationary_not_minimum",
    base + [d("u", "Vector", "E"), d("c", "Real")],
    q.imp(
        q.ne(u, zero),
        q.lt(c, Z),
        q.both(
            a("has_gradient", E, quad, zero, zero), q.neg(a("local_min", E, quad, zero))
        ),
    ),
    "On any nontrivial finite-dimensional real inner-product space, every negative multiple c‖x‖² has gradient zero at the origin but does not have a local minimum there. Stationarity alone is not a sufficient minimum criterion.",
    "example (E : Type*) [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] (u : E) (hu : u ≠ 0) (c : ℝ) (hc : c < 0) : HasGradientAt (fun x : E => c * ‖x‖^2) 0 0 ∧ ¬IsLocalMin (fun x : E => c * ‖x‖^2) 0",
    " constructor\n · apply hasGradientAt_iff_hasFDerivAt.mpr\n   convert! (hasStrictFDerivAt_norm_sq (0 : E)).hasFDerivAt.const_smul c using 1 <;> ext y <;> simp\n · intro h\n   obtain ⟨δ,hδ,hh⟩ := Metric.eventually_nhds_iff.mp h\n   have hn : 0 < ‖u‖ := norm_pos_iff.mpr hu\n   let t := δ / (2 * ‖u‖)\n   have ht : 0 < t := by dsimp [t]; positivity\n   have hnorm : ‖t • u‖ = δ / 2 := by rw [norm_smul,Real.norm_eq_abs,abs_of_pos ht]; dsimp [t]; field_simp\n   have hd : dist (t • u) 0 < δ := by simpa [dist_zero_right,hnorm] using (show δ / 2 < δ by linarith)\n   have hv := hh hd\n   simp only [norm_zero,zero_pow (by decide : 2 ≠ 0),mul_zero,hnorm] at hv\n   have hp : 0 < (δ / 2)^2 := sq_pos_of_pos (by positivity)\n   nlinarith [mul_neg_of_neg_of_pos hc hp]\n",
    [
        "Differentiate the scaled squared norm to obtain gradient zero at the origin.",
        "Choose a nonzero direction u.",
        "Every neighborhood of zero contains a small positive multiple of u.",
        "At that point c‖x‖² is strictly negative, contradicting the local minimum inequality.",
    ],
    "gradient",
    "counterexample_audit",
    "standard",
)

add(
    4,
    "nondifferentiable_minimum",
    base + [d("u", "Vector", "E")],
    q.imp(
        q.ne(u, zero),
        q.bind(
            [d("f", "ScalarFunction", "E")],
            q.both(
                a("local_min", E, f, zero),
                q.neg(a("scalar_differentiable_at", E, f, zero)),
            ),
            "exists",
        ),
    ),
    "On any finite-dimensional real inner-product space with a nonzero vector, there exists a function with a local minimum at the origin that is not differentiable there. A local minimum does not imply the differentiability premise of Fermat’s theorem.",
    "example (E : Type*) [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] (u : E) (hu : u ≠ 0) : ∃ f : E → ℝ, IsLocalMin f 0 ∧ ¬DifferentiableAt ℝ f 0",
    " letI : Nontrivial E := ⟨⟨u,0,hu⟩⟩\n refine ⟨fun x => ‖x‖, ?_, not_differentiableAt_norm_zero E⟩\n apply Filter.Eventually.of_forall\n intro x\n simpa using norm_nonneg x\n",
    [
        "Use the norm function as the witness.",
        "Nonnegativity makes the origin a global, hence local, minimum.",
        "The supplied nonzero vector makes the space nontrivial.",
        "The norm on a nontrivial real normed space is not differentiable at zero.",
    ],
    "extrema",
    "counterexample_audit",
    "standard",
)

add(
    4,
    "quadratic_minimum_criterion",
    base + [d("c", "Real"), d("x", "Vector", "E")],
    q.imp(q.lt(Z, c), q.iff(a("local_min", E, quad, x), q.eq(x, zero))),
    "For c>0 on any finite-dimensional real inner-product space, a point x is a local minimum of c‖·‖² exactly when x=0. This recognizes all local minimizers of the positive definite radial quadratic.",
    "example (E : Type*) [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] (c : ℝ) (hc : 0 < c) (x : E) : IsLocalMin (fun y : E => c * ‖y‖^2) x ↔ x = 0",
    " constructor\n · intro h\n   have he := h.hasFDerivAt_eq_zero ((hasStrictFDerivAt_norm_sq x).hasFDerivAt.const_smul c)\n   have hv := congrArg (fun A : E →L[ℝ] ℝ => A x) he\n   simp [inner_self_eq_norm_sq_to_K] at hv\n   exact hv.resolve_left (ne_of_gt hc)\n · intro hx\n   subst x\n   apply Filter.Eventually.of_forall\n   intro y\n   simpa using mul_nonneg hc.le (sq_nonneg ‖y‖)\n",
    [
        "Differentiate the scaled squared norm.",
        "At a local minimum its derivative must vanish.",
        "Evaluating that derivative on x and using c>0 forces x=0.",
        "Conversely, nonnegativity proves that zero is a global and local minimum.",
    ],
    "extrema",
    "recognize",
    "introductory",
)

add(
    4,
    "nonnegative_quadratic_minimum",
    base + [d("c", "Real")],
    q.imp(
        q.le(Z, c),
        q.both(
            a("local_min", E, quad, zero),
            q.bind(
                [d("x", "Vector", "E")],
                q.le(a("scalar_apply", E, quad, zero), a("scalar_apply", E, quad, x)),
            ),
        ),
    ),
    "For every nonnegative c and every finite-dimensional real inner-product space, the origin is a local and global minimizer of c‖x‖². The conclusion allows c=0 and does not claim uniqueness.",
    "example (E : Type*) [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] (c : ℝ) (hc : 0 ≤ c) : IsLocalMin (fun x : E => c * ‖x‖^2) 0 ∧ ∀ x : E, c * ‖(0 : E)‖^2 ≤ c * ‖x‖^2",
    " have h : ∀ x : E, c * ‖(0 : E)‖^2 ≤ c * ‖x‖^2 := by intro x; simpa using mul_nonneg hc (sq_nonneg ‖x‖)\n exact ⟨Filter.Eventually.of_forall h,h⟩\n",
    [
        "The squared norm is nonnegative everywhere.",
        "Multiplication by c≥0 preserves that inequality.",
        "The objective has value zero at the origin, so the global minimum inequality follows.",
        "A global minimum is in particular a local minimum.",
    ],
    "extrema",
    "compute_construct",
    "introductory",
)

add(
    4,
    "exact_residual_minimum",
    base
    + [
        d("F", "RealInnerProductSpace"),
        d("A", "CLM", "E", "F"),
        d("b", "Vector", "F"),
        d("x", "Vector", "E"),
    ],
    q.imp(
        q.eq(a("clm_apply", E, F, A, x), b),
        q.both(
            a("local_min", E, residual, x),
            q.bind(
                [d("y", "Vector", "E")],
                q.le(
                    a("scalar_apply", E, residual, x), a("scalar_apply", E, residual, y)
                ),
            ),
            a("has_gradient", E, residual, x, zero),
        ),
    ),
    "For a continuous linear map A between finite-dimensional real inner-product spaces, any exact solution Ax=b globally and locally minimizes the squared residual ‖Ay−b‖² and has zero objective gradient. Neither uniqueness nor existence of an exact solution is asserted without the supplied solution.",
    "example (E F : Type*) [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] [NormedAddCommGroup F] [InnerProductSpace ℝ F] [FiniteDimensional ℝ F] (A : E →L[ℝ] F) (b : F) (x : E) (hx : A x = b) : IsLocalMin (fun y => ‖A y - b‖^2) x ∧ (∀ y, ‖A x - b‖^2 ≤ ‖A y - b‖^2) ∧ HasGradientAt (fun y => ‖A y - b‖^2) 0 x",
    " have h : ∀ y, ‖A x - b‖^2 ≤ ‖A y - b‖^2 := by intro y; simpa [hx] using sq_nonneg ‖A y - b‖\n refine ⟨Filter.Eventually.of_forall h,h,?_⟩\n apply hasGradientAt_iff_hasFDerivAt.mpr\n have hd := (hasStrictFDerivAt_norm_sq (A x - b)).hasFDerivAt.comp x (A.hasFDerivAt.sub_const b)\n convert! hd using 1 <;> ext y <;> simp [hx]\n",
    [
        "The given exact solution has residual zero.",
        "Every squared residual is nonnegative, proving global and local optimality.",
        "Differentiate the affine residual using the linear map A.",
        "Compose with the squared-norm derivative; the zero residual makes the derivative and gradient vanish.",
    ],
    "extrema",
    "synthesize",
    "advanced",
)


def main():
    mathlib = next(
        p["rev"]
        for p in json.loads((WORKSPACE / "lake-manifest.json").read_text())["packages"]
        if p["name"] == "mathlib"
    )
    sha = lambda path: "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    for version, cards in BATCHES.items():
        stem = {5: "multivariable-v5", 4: "calculus-v4"}[version]
        witness_path = ROOT / f"docs/{stem}-foundation-supplement.lean"
        witness_path.write_text(
            "import Mathlib\n\n"
            + "\n\n".join(
                "-- manifest card: "
                + card["id"]
                + "\n"
                + card["lean_target"]
                + " := "
                + card["lean_witness"].rstrip()
                for card in cards
            )
            + "\n"
        )
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
        evidence = {
            "witness_path": str(witness_path.relative_to(ROOT)),
            "witness_sha256": sha(witness_path),
            "validator_sha256": sha(
                ROOT
                / "pals-agent/pals_agent"
                / ("typed_" + stem.replace("-", "_") + ".py")
            ),
            "registry_sha256": sha(
                ROOT
                / f"pals-agent/pals_agent/content_dictionaries/typed-{stem}-registry.json"
            ),
            "toolchain": (WORKSPACE / "lean-toolchain").read_text().strip(),
            "mathlib_revision": mathlib,
        }
        payload = {
            "schema_version": "pals.typed-catalog-expansion-batch.v1",
            "profile_id": "typed-" + stem,
            "cards": cards,
            "evidence": evidence,
        }
        (ROOT / f"docs/{stem}-foundation-supplement.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        )
        print(f"{stem}: compiled and emitted {len(cards)} cards")
    (ROOT / "docs/multivariable-foundation-supplement-bindings.json").write_text(
        json.dumps(
            {
                "schema_version": "pals.proposed-explicit-curriculum-bindings.v1",
                "status": "proposed_for_parent_review",
                "bindings": BINDINGS,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
