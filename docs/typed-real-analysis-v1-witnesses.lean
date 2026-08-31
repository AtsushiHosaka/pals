import Mathlib

open Set Filter
open scoped Topology Interval

-- ε–δ continuity, for f(x) = x.  The witness is δ = ε.
example (a ε : ℝ) (hε : 0 < ε) :
    ∃ δ : ℝ, 0 < δ ∧ ∀ x : ℝ, |x - a| < δ → |x - a| < ε := by
  exact ⟨ε, hε, fun _ hx => hx⟩

-- realanalysis1:has_deriv_at for x ↦ x².
example (a : ℝ) : HasDerivAt (fun x : ℝ => x ^ 2) (2 * a) a := by
  simpa [pow_two] using hasDerivAt_pow 2 a

-- Differentiability is a proposition, separate from a total derivative value.
example (a : ℝ) : DifferentiableAt ℝ (fun x : ℝ => x ^ 3 - 2 * x) a := by
  fun_prop

-- Mean-value theorem receipt: the derivative equals a secant slope somewhere inside.
example {f : ℝ → ℝ} {a b : ℝ} (hab : a < b)
    (hcont : ContinuousOn f (Icc a b))
    (hdiff : DifferentiableOn ℝ f (Ioo a b)) :
    ∃ c ∈ Ioo a b, deriv f c = (f b - f a) / (b - a) := by
  exact exists_deriv_eq_slope f hab hcont hdiff

-- A Taylor polynomial is admitted only with an explicit smoothness/remainder profile.
-- This exact quadratic calculation is a receipt for the fixed order-two fragment.
noncomputable def taylor2 (f0 f1 f2 x : ℝ) : ℝ := f0 + f1 * x + (f2 / 2) * x ^ 2

example (x : ℝ) : x ^ 2 = taylor2 0 0 2 x := by
  simp [taylor2]

-- The initial definite-integral meaning is Lean's oriented interval integral.
example : (∫ x : ℝ in 0..1, x ^ 2) = 1 / 3 := by
  norm_num [integral_pow]

example : IntervalIntegrable (fun x : ℝ => x ^ 2) (MeasureTheory.volume : MeasureTheory.Measure ℝ) 0 1 := by
  have hcont : Continuous (fun x : ℝ => x ^ 2) := by fun_prop
  exact hcont.intervalIntegrable (μ := (MeasureTheory.volume : MeasureTheory.Measure ℝ)) 0 1

-- An improper integral is a separate limit-backed notion, never a total “∞” term.
example : ∫ x : ℝ in Ioi 0, Real.exp (-x) = 1 := by
  simpa using integral_exp_neg_Ioi_zero
