import Mathlib

open Set Filter
open scoped Topology Interval

-- manifest card: real_analysis_eps_delta_identity
example (a ε : ℝ) (hε : 0 < ε) :
    ∃ δ : ℝ, 0 < δ ∧ ∀ x : ℝ, |x - a| < δ → |x - a| < ε := by
  exact ⟨ε, hε, fun _ hx => hx⟩

-- manifest card: real_analysis_has_deriv_square
example (a : ℝ) : HasDerivAt (fun x : ℝ => x ^ 2) (2 * a) a := by
  simpa [pow_two] using hasDerivAt_pow 2 a

-- manifest card: real_analysis_differentiable_cubic_minus_linear
example (a : ℝ) : DifferentiableAt ℝ (fun x : ℝ => x ^ 3 - 2 * x) a := by
  fun_prop

-- manifest card: real_analysis_interval_integrable_square_zero_one
example : IntervalIntegrable (fun x : ℝ => x ^ 2)
    (MeasureTheory.volume : MeasureTheory.Measure ℝ) 0 1 := by
  have hcont : Continuous (fun x : ℝ => x ^ 2) := by fun_prop
  exact hcont.intervalIntegrable (μ := (MeasureTheory.volume : MeasureTheory.Measure ℝ)) 0 1
