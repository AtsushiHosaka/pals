import Mathlib

-- manifest card: calculus_reuse_derivative_sum
example (f g : ℝ → ℝ) (a u v : ℝ) (hf : HasDerivAt f u a) (hg : HasDerivAt g v a) : HasDerivAt (fun x => f x + g x) (u + v) a := by
  exact hf.add hg

-- manifest card: calculus_reuse_derivative_difference
example (f g : ℝ → ℝ) (a u v : ℝ) (hf : HasDerivAt f u a) (hg : HasDerivAt g v a) : HasDerivAt (fun x => f x - g x) (u - v) a := by
  exact hf.sub hg

-- manifest card: calculus_reuse_derivative_product
example (f g : ℝ → ℝ) (a u v : ℝ) (hf : HasDerivAt f u a) (hg : HasDerivAt g v a) : HasDerivAt (fun x => f x * g x) (u * g a + f a * v) a := by
  exact hf.mul hg

-- manifest card: calculus_reuse_derivative_quotient
example (f g : ℝ → ℝ) (a u v : ℝ) (hf : HasDerivAt f u a) (hg : HasDerivAt g v a) (hne : g a ≠ 0) : HasDerivAt (fun x => f x / g x) ((u * g a - f a * v) / (g a)^2) a := by
  exact hf.div hg hne

-- manifest card: calculus_reuse_derivative_chain
example (f g : ℝ → ℝ) (a u v : ℝ) (hf : HasDerivAt f u (g a)) (hg : HasDerivAt g v a) : HasDerivAt (fun x => f (g x)) (u * v) a := by
  exact hf.comp a hg

-- manifest card: calculus_reuse_derivative_scalar_multiple
example (f : ℝ → ℝ) (a u c : ℝ) (hf : HasDerivAt f u a) : HasDerivAt (fun x => c * f x) (c * u) a := by
  exact hf.const_mul c

-- manifest card: calculus_reuse_derivative_unique
example (f : ℝ → ℝ) (a u v : ℝ) (hu : HasDerivAt f u a) (hv : HasDerivAt f v a) : u = v := by
  exact hu.unique hv

-- manifest card: calculus_reuse_derivative_implies_differentiable
example (f : ℝ → ℝ) (a u : ℝ) (hf : HasDerivAt f u a) : DifferentiableAt ℝ f a := by
  exact hf.differentiableAt

-- manifest card: calculus_reuse_differentiable_implies_continuous
example (f : ℝ → ℝ) (a : ℝ) (hf : DifferentiableAt ℝ f a) : ContinuousAt f a := by
  exact hf.continuousAt

-- manifest card: calculus_reuse_differentiable_sum
example (f g : ℝ → ℝ) (a : ℝ) (hf : DifferentiableAt ℝ f a) (hg : DifferentiableAt ℝ g a) : DifferentiableAt ℝ (fun x => f x + g x) a := by
  exact hf.add hg

-- manifest card: calculus_reuse_differentiable_product
example (f g : ℝ → ℝ) (a : ℝ) (hf : DifferentiableAt ℝ f a) (hg : DifferentiableAt ℝ g a) : DifferentiableAt ℝ (fun x => f x * g x) a := by
  exact hf.mul hg

-- manifest card: calculus_reuse_differentiable_quotient
example (f g : ℝ → ℝ) (a : ℝ) (hf : DifferentiableAt ℝ f a) (hg : DifferentiableAt ℝ g a) (hne : g a ≠ 0) : DifferentiableAt ℝ (fun x => f x / g x) a := by
  exact hf.div hg hne

-- manifest card: calculus_reuse_differentiable_composition
example (f g : ℝ → ℝ) (a : ℝ) (hf : DifferentiableAt ℝ f (g a)) (hg : DifferentiableAt ℝ g a) : DifferentiableAt ℝ (fun x => f (g x)) a := by
  exact hf.comp a hg

-- manifest card: calculus_reuse_differentiable_absolute_value
example (f : ℝ → ℝ) (a : ℝ) (hf : DifferentiableAt ℝ f a) (hne : f a ≠ 0) : DifferentiableAt ℝ (fun x => |f x|) a := by
  exact hf.abs hne

-- manifest card: calculus_reuse_continuous_sum
example (f g : ℝ → ℝ) (a : ℝ) (hf : ContinuousAt f a) (hg : ContinuousAt g a) : ContinuousAt (fun x => f x + g x) a := by
  exact hf.add hg

-- manifest card: calculus_reuse_continuous_product
example (f g : ℝ → ℝ) (a : ℝ) (hf : ContinuousAt f a) (hg : ContinuousAt g a) : ContinuousAt (fun x => f x * g x) a := by
  exact hf.mul hg

-- manifest card: calculus_reuse_continuous_quotient
example (f g : ℝ → ℝ) (a : ℝ) (hf : ContinuousAt f a) (hg : ContinuousAt g a) (hne : g a ≠ 0) : ContinuousAt (fun x => f x / g x) a := by
  exact hf.div hg hne

-- manifest card: calculus_reuse_continuous_composition
example (f g : ℝ → ℝ) (a : ℝ) (hf : ContinuousAt f (g a)) (hg : ContinuousAt g a) : ContinuousAt (fun x => f (g x)) a := by
  exact hf.comp hg

-- manifest card: calculus_reuse_continuous_absolute_value
example (f : ℝ → ℝ) (a : ℝ) (hf : ContinuousAt f a) : ContinuousAt (fun x => |f x|) a := by
  exact hf.abs

-- manifest card: calculus_reuse_interval_integrable_sum
example (f g : ℝ → ℝ) (a b : ℝ) (hf : IntervalIntegrable f (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b) (hg : IntervalIntegrable g (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b) : IntervalIntegrable (fun x => f x + g x) (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b := by
  exact hf.add hg

-- manifest card: calculus_reuse_interval_integrable_difference
example (f g : ℝ → ℝ) (a b : ℝ) (hf : IntervalIntegrable f (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b) (hg : IntervalIntegrable g (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b) : IntervalIntegrable (fun x => f x - g x) (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b := by
  exact hf.sub hg

-- manifest card: calculus_reuse_interval_integrable_scalar_multiple
example (f : ℝ → ℝ) (a b c : ℝ) (hf : IntervalIntegrable f (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b) : IntervalIntegrable (fun x => c * f x) (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b := by
  exact hf.const_mul c

-- manifest card: calculus_reuse_interval_integrable_reverse
example (f : ℝ → ℝ) (a b : ℝ) (hf : IntervalIntegrable f (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b) : IntervalIntegrable f (MeasureTheory.volume : MeasureTheory.Measure ℝ) b a := by
  exact hf.symm

-- manifest card: calculus_reuse_interval_integrable_join
example (f : ℝ → ℝ) (a b c : ℝ) (hab : IntervalIntegrable f (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b) (hbc : IntervalIntegrable f (MeasureTheory.volume : MeasureTheory.Measure ℝ) b c) : IntervalIntegrable f (MeasureTheory.volume : MeasureTheory.Measure ℝ) a c := by
  exact hab.trans hbc

-- manifest card: calculus_reuse_continuous_implies_interval_integrable
example (f : ℝ → ℝ) (a b : ℝ) (hf : ∀ x : ℝ, ContinuousAt f x) : IntervalIntegrable f (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b := by
  exact (continuous_iff_continuousAt.mpr hf).intervalIntegrable (μ := (MeasureTheory.volume : MeasureTheory.Measure ℝ)) a b

-- manifest card: calculus_reuse_derivative_affine_parameters
example (a b c : ℝ) : HasDerivAt (fun x : ℝ => b * x + c) b a := by
  simpa using ((hasDerivAt_id (x := a)).const_mul b).add_const c

-- manifest card: calculus_reuse_derivative_reciprocal_function
example (f : ℝ → ℝ) (a u : ℝ) (hf : HasDerivAt f u a) (hne : f a ≠ 0) : HasDerivAt (fun x => 1 / f x) (-u / (f a)^2) a := by
  have hfun : (fun x => 1 / f x) = f⁻¹ := by
    funext x
    exact one_div (f x)
  rw [hfun]
  exact hf.inv hne

-- manifest card: calculus_reuse_interval_integrable_constant
example (a b c : ℝ) : IntervalIntegrable (fun _ : ℝ => c) (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b := by
  exact continuous_const.intervalIntegrable (μ := (MeasureTheory.volume : MeasureTheory.Measure ℝ)) a b

-- manifest card: calculus_reuse_continuous_epsilon_delta
example (f : ℝ → ℝ) (a : ℝ) (hf : ContinuousAt f a) : ∀ ε : ℝ, 0 < ε → ∃ δ : ℝ, 0 < δ ∧ ∀ x : ℝ, |x - a| < δ → |f x - f a| < ε := by
  intro ε hε
  obtain ⟨δ, hδ, h⟩ := Metric.continuousAt_iff.mp hf ε hε
  refine ⟨δ, hδ, ?_⟩
  intro x hx
  simpa only [Real.dist_eq] using h (by simpa only [Real.dist_eq] using hx)
