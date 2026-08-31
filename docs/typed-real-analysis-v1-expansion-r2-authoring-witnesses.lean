import Mathlib

open Set Filter
open scoped Topology Interval

-- manifest card: real_analysis_eps_delta_affine_shift
example (a ε : ℝ) (hε : 0 < ε) :
    ∃ δ : ℝ, 0 < δ ∧ ∀ x : ℝ, |x - a| < δ → |(x + 3) - (a + 3)| < ε := by
  refine ⟨ε, hε, ?_⟩
  intro x hx
  simpa using hx

-- manifest card: real_analysis_epsilon_delta_continuous_square
example (a : ℝ) : ContinuousAt (fun x : ℝ => x ^ 2) a := by
  fun_prop

-- manifest card: real_analysis_continuous_cubic_minus_linear
example (a : ℝ) : ContinuousAt (fun x : ℝ => x ^ 3 - 2 * x) a := by
  fun_prop

-- manifest card: real_analysis_continuous_reciprocal_nonzero
example (a : ℝ) (h : a ≠ 0) : ContinuousAt (fun x : ℝ => 1 / x) a := by
  simpa only [one_div] using continuousAt_inv₀ h

-- manifest card: real_analysis_has_deriv_affine
example (a : ℝ) : HasDerivAt (fun x : ℝ => 3 * x + 5) 3 a := by
  simpa using ((hasDerivAt_id (x := a)).const_mul (3 : ℝ)).add_const (5 : ℝ)

-- manifest card: real_analysis_has_deriv_sum_square_linear
example (a : ℝ) : HasDerivAt (fun x : ℝ => x ^ 2 + 3 * x) (2 * a + 3) a := by
  convert! (hasDerivAt_pow 2 a).add (hasDerivAt_const_mul 3) using 1
  all_goals ring

-- manifest card: real_analysis_has_deriv_product_shifted_identity
example (a : ℝ) : HasDerivAt (fun x : ℝ => (x + 1) * (x - 1)) (2 * a) a := by
  convert! ((hasDerivAt_id (x := a)).add_const 1).mul ((hasDerivAt_id (x := a)).sub_const 1) using 1
  all_goals simp [id_eq]
  all_goals ring

-- manifest card: real_analysis_has_deriv_chain_polynomial
example (a : ℝ) : HasDerivAt (fun x : ℝ => (x ^ 2 + 1) ^ 3) (3 * (a ^ 2 + 1) ^ 2 * (2 * a)) a := by
  convert! ((hasDerivAt_pow 2 a).add_const 1).pow 3 using 1
  all_goals ring

-- manifest card: real_analysis_differentiable_affine
example (a : ℝ) : DifferentiableAt ℝ (fun x : ℝ => 3 * x + 5) a := by
  fun_prop

-- manifest card: real_analysis_differentiable_product_polynomial
example (a : ℝ) : DifferentiableAt ℝ (fun x : ℝ => (x ^ 2 + 1) * (x - 1)) a := by
  fun_prop

-- manifest card: real_analysis_differentiable_reciprocal_nonzero
example (a : ℝ) (h : a ≠ 0) : DifferentiableAt ℝ (fun x : ℝ => 1 / x) a := by
  simpa only [one_div] using differentiableAt_inv (𝕜 := ℝ) h

-- manifest card: real_analysis_interval_integrable_affine_all_endpoints
example (a b : ℝ) : IntervalIntegrable (fun x : ℝ => 3 * x + 5)
    (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b := by
  exact (by fun_prop : Continuous (fun x : ℝ => 3 * x + 5)).intervalIntegrable (μ := (MeasureTheory.volume : MeasureTheory.Measure ℝ)) a b

-- manifest card: real_analysis_interval_integrable_cubic_all_endpoints
example (a b : ℝ) : IntervalIntegrable (fun x : ℝ => x ^ 3 - 2 * x)
    (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b := by
  exact (by fun_prop : Continuous (fun x : ℝ => x ^ 3 - 2 * x)).intervalIntegrable (μ := (MeasureTheory.volume : MeasureTheory.Measure ℝ)) a b

-- manifest card: real_analysis_interval_integrable_product_all_endpoints
example (a b : ℝ) : IntervalIntegrable (fun x : ℝ => (x ^ 2 + 1) * (x - 1))
    (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b := by
  exact (by fun_prop : Continuous (fun x : ℝ => (x ^ 2 + 1) * (x - 1))).intervalIntegrable (μ := (MeasureTheory.volume : MeasureTheory.Measure ℝ)) a b

-- manifest card: real_analysis_interval_integrable_reciprocal_quadratic
example (a b : ℝ) : IntervalIntegrable (fun x : ℝ => 1 / (x ^ 2 + 1))
    (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b := by
  have hcont : Continuous (fun x : ℝ => 1 / (x ^ 2 + 1)) := by
    apply continuous_const.div (by fun_prop)
    intro x
    nlinarith [sq_nonneg x]
  exact hcont.intervalIntegrable (μ := (MeasureTheory.volume : MeasureTheory.Measure ℝ)) a b
