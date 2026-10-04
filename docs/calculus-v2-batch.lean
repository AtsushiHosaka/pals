import Mathlib

-- manifest card: calculus_v2_natural_power_derivative
example (n : ℕ) (a : ℝ) : HasDerivAt (fun x : ℝ => x ^ n) ((n : ℝ) * a ^ (n - 1)) a := by
  exact hasDerivAt_pow n a

-- manifest card: calculus_v2_natural_power_continuous
example (n : ℕ) : Continuous (fun x : ℝ => x ^ n) := by
  exact continuous_id.pow n

-- manifest card: calculus_v2_natural_power_integral
example (n : ℕ) (a b : ℝ) : IntervalIntegrable (fun x : ℝ => x ^ n) (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b ∧ (∫ x : ℝ in a..b, x ^ n) = (b ^ (n + 1) - a ^ (n + 1)) / ((n + 1 : ℕ) : ℝ) := by
  constructor
  · exact (continuous_id.pow n).intervalIntegrable a b
  · simpa only [Nat.cast_add, Nat.cast_one] using (integral_pow (a := a) (b := b) (n := n))

-- manifest card: calculus_v2_natural_power_chain
example (f : ℝ → ℝ) (n : ℕ) (a u : ℝ) (hf : HasDerivAt f u a) : HasDerivAt (fun x => (f x)^n) ((n : ℝ) * (f a)^(n-1) * u) a := by
  exact hf.pow n

-- manifest card: calculus_v2_exp_chain
example (f : ℝ → ℝ) (a u : ℝ) (hf : HasDerivAt f u a) : HasDerivAt (fun x => Real.exp (f x)) (Real.exp (f a) * u) a := by
  exact hf.exp

-- manifest card: calculus_v2_log_chain
example (f : ℝ → ℝ) (a u : ℝ) (hf : HasDerivAt f u a) (hne : f a ≠ 0) : HasDerivAt (fun x => Real.log (f x)) (u / f a) a := by
  exact hf.log hne

-- manifest card: calculus_v2_sin_chain
example (f : ℝ → ℝ) (a u : ℝ) (hf : HasDerivAt f u a) : HasDerivAt (fun x => Real.sin (f x)) (Real.cos (f a) * u) a := by
  exact hf.sin

-- manifest card: calculus_v2_cos_chain
example (f : ℝ → ℝ) (a u : ℝ) (hf : HasDerivAt f u a) : HasDerivAt (fun x => Real.cos (f x)) (-Real.sin (f a) * u) a := by
  exact hf.cos

-- manifest card: calculus_v2_sqrt_chain
example (f : ℝ → ℝ) (a u : ℝ) (hf : HasDerivAt f u a) (hpos : 0 < f a) : HasDerivAt (fun x => Real.sqrt (f x)) (u / (2 * Real.sqrt (f a))) a := by
  exact hf.sqrt (ne_of_gt hpos)

-- manifest card: calculus_v2_arctan_chain
example (f : ℝ → ℝ) (a u : ℝ) (hf : HasDerivAt f u a) : HasDerivAt (fun x => Real.arctan (f x)) ((1 / (1 + (f a)^2)) * u) a := by
  exact hf.arctan

-- manifest card: calculus_v2_exp_integral
example (a b : ℝ) : IntervalIntegrable Real.exp (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b ∧ (∫ x : ℝ in a..b, Real.exp x) = Real.exp b - Real.exp a := by
  exact ⟨Real.continuous_exp.intervalIntegrable a b, integral_exp⟩

-- manifest card: calculus_v2_sin_integral
example (a b : ℝ) : IntervalIntegrable Real.sin (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b ∧ (∫ x : ℝ in a..b, Real.sin x) = Real.cos a - Real.cos b := by
  exact ⟨Real.continuous_sin.intervalIntegrable a b, integral_sin⟩

-- manifest card: calculus_v2_cos_integral
example (a b : ℝ) : IntervalIntegrable Real.cos (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b ∧ (∫ x : ℝ in a..b, Real.cos x) = Real.sin b - Real.sin a := by
  exact ⟨Real.continuous_cos.intervalIntegrable a b, integral_cos⟩

-- manifest card: calculus_v2_reciprocal_integral_positive
example (a b : ℝ) (ha : 0 < a) (hb : 0 < b) : IntervalIntegrable (fun x : ℝ => 1 / x) (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b ∧ (∫ x : ℝ in a..b, 1 / x) = Real.log (b / a) := by
  constructor
  · apply ContinuousOn.intervalIntegrable
    apply continuousOn_const.div continuousOn_id
    intro x hx
    exact ne_of_gt (lt_of_lt_of_le (lt_min ha hb) hx.1)
  · exact integral_one_div_of_pos ha hb

-- manifest card: calculus_v2_mean_value
example (f g : ℝ → ℝ) (a b : ℝ) (hab : a < b) (hc : ContinuousOn f (Set.Icc a b)) (hd : ∀ x : ℝ, a < x ∧ x < b → HasDerivAt f (g x) x) : ∃ c : ℝ, (a < c ∧ c < b) ∧ g c = (f b - f a) / (b - a) := by
  exact exists_hasDerivAt_eq_slope f g hab hc (fun x hx => hd x hx)

-- manifest card: calculus_v2_rolle
example (f g : ℝ → ℝ) (a b : ℝ) (hab : a < b) (hc : ContinuousOn f (Set.Icc a b)) (heq : f a = f b) (hd : ∀ x : ℝ, a < x ∧ x < b → HasDerivAt f (g x) x) : ∃ c : ℝ, (a < c ∧ c < b) ∧ g c = 0 := by
  exact exists_hasDerivAt_eq_zero hab hc heq (fun x hx => hd x hx)

-- manifest card: calculus_v2_fundamental_theorem_antiderivative
example (f g : ℝ → ℝ) (a b : ℝ) (hd : ∀ x : ℝ, HasDerivAt f (g x) x) (hi : IntervalIntegrable g (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b) : (∫ x : ℝ in a..b, g x) = f b - f a := by
  exact intervalIntegral.integral_eq_sub_of_hasDerivAt (fun x _ => hd x) hi

-- manifest card: calculus_v2_fundamental_theorem_variable_upper
example (f : ℝ → ℝ) (a b : ℝ) (hc : Continuous f) : HasDerivAt (fun x : ℝ => ∫ t : ℝ in a..x, f t) (f b) b := by
  exact (hc.integral_hasStrictDerivAt a b).hasDerivAt

-- manifest card: calculus_v2_integration_by_parts
example (f g h k : ℝ → ℝ) (a b : ℝ) (hf : ∀ x : ℝ, HasDerivAt f (h x) x) (hg : ∀ x : ℝ, HasDerivAt g (k x) x) (hi : IntervalIntegrable h (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b) (hj : IntervalIntegrable k (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b) : (∫ x : ℝ in a..b, f x * k x) = f b * g b - f a * g a - (∫ x : ℝ in a..b, h x * g x) := by
  have cf : Continuous f := continuous_iff_continuousAt.mpr (fun x => (hf x).continuousAt)
  have cg : Continuous g := continuous_iff_continuousAt.mpr (fun x => (hg x).continuousAt)
  exact intervalIntegral.integral_mul_deriv_eq_deriv_mul_of_hasDerivAt cf.continuousOn cg.continuousOn (fun x _ => hf x) (fun x _ => hg x) hi hj

-- manifest card: calculus_v2_integration_substitution
example (f g h : ℝ → ℝ) (a b : ℝ) (hd : ∀ x : ℝ, HasDerivAt f (h x) x) (ch : Continuous h) (cg : Continuous g) : (∫ x : ℝ in a..b, g (f x) * h x) = (∫ y : ℝ in f a..f b, g y) := by
  exact intervalIntegral.integral_comp_mul_deriv (fun x _ => hd x) ch.continuousOn cg

-- manifest card: calculus_v2_integral_additivity
example (f g : ℝ → ℝ) (a b : ℝ) (hf : IntervalIntegrable f (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b) (hg : IntervalIntegrable g (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b) : (∫ x : ℝ in a..b, f x + g x) = (∫ x : ℝ in a..b, f x) + (∫ x : ℝ in a..b, g x) := by
  exact intervalIntegral.integral_add hf hg

-- manifest card: calculus_v2_integral_scalar_linearity
example (f : ℝ → ℝ) (a b c : ℝ) (hf : IntervalIntegrable f (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b) : IntervalIntegrable (fun x => c * f x) (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b ∧ (∫ x : ℝ in a..b, c * f x) = c * (∫ x : ℝ in a..b, f x) := by
  exact ⟨hf.const_mul c, intervalIntegral.integral_const_mul c f⟩

-- manifest card: calculus_v2_integral_join_intervals
example (f : ℝ → ℝ) (a b c : ℝ) (hab : IntervalIntegrable f (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b) (hbc : IntervalIntegrable f (MeasureTheory.volume : MeasureTheory.Measure ℝ) b c) : (∫ x : ℝ in a..b, f x) + (∫ x : ℝ in b..c, f x) = (∫ x : ℝ in a..c, f x) := by
  exact intervalIntegral.integral_add_adjacent_intervals hab hbc

-- manifest card: calculus_v2_integral_order
example (f g : ℝ → ℝ) (a b : ℝ) (hab : a ≤ b) (hf : IntervalIntegrable f (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b) (hg : IntervalIntegrable g (MeasureTheory.volume : MeasureTheory.Measure ℝ) a b) (hle : ∀ x : ℝ, a ≤ x ∧ x ≤ b → f x ≤ g x) : (∫ x : ℝ in a..b, f x) ≤ (∫ x : ℝ in a..b, g x) := by
  exact intervalIntegral.integral_mono_on hab hf hg (fun x hx => hle x hx)

-- manifest card: calculus_v2_nonnegative_derivative_monotone
example (f g : ℝ → ℝ) (hd : ∀ x : ℝ, HasDerivAt f (g x) x) (hn : ∀ x : ℝ, 0 ≤ g x) : ∀ a b : ℝ, a ≤ b → f a ≤ f b := by
  exact fun a b hab => monotone_of_hasDerivAt_nonneg hd hn hab

-- manifest card: calculus_v2_zero_derivative_constant
example (f : ℝ → ℝ) (hd : ∀ x : ℝ, HasDerivAt f 0 x) : ∀ a b : ℝ, f a = f b := by
  exact is_const_of_deriv_eq_zero (fun x => (hd x).differentiableAt) (fun x => (hd x).deriv)

-- manifest card: calculus_v2_intermediate_value
example (f : ℝ → ℝ) (a b u : ℝ) (hab : a ≤ b) (hc : ContinuousOn f (Set.Icc a b)) (ha : f a ≤ u) (hb : u ≤ f b) : ∃ c : ℝ, (a ≤ c ∧ c ≤ b) ∧ f c = u := by
  exact intermediate_value_Icc hab hc ⟨ha, hb⟩

-- manifest card: calculus_v2_extreme_value_minimum
example (f : ℝ → ℝ) (a b : ℝ) (hab : a ≤ b) (hc : ContinuousOn f (Set.Icc a b)) : ∃ c : ℝ, (a ≤ c ∧ c ≤ b) ∧ ∀ x : ℝ, a ≤ x ∧ x ≤ b → f c ≤ f x := by
  exact isCompact_Icc.exists_isMinOn ⟨a, le_rfl, hab⟩ hc
