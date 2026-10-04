import Mathlib

-- manifest card: calculus_v5_integral_absolute_bound
example (f : ℝ → ℝ) (a b : ℝ) (hab : a ≤ b) (hf : IntervalIntegrable f MeasureTheory.volume a b) : |∫ x in a..b, f x| ≤ ∫ x in a..b, |f x| := by
  exact intervalIntegral.abs_integral_le_integral_abs hab

-- manifest card: calculus_v5_integral_uniform_bound
example (f : ℝ → ℝ) (a b c : ℝ) (hf : IntervalIntegrable f MeasureTheory.volume a b) (hb : ∀ x ∈ Set.uIcc a b, |f x| ≤ c) : |∫ x in a..b, f x| ≤ c*|b-a| := by
  simpa only [Real.norm_eq_abs] using (intervalIntegral.norm_integral_le_of_norm_le_const (f := f) (a := a) (b := b) (C := c) (fun x hx => by simpa only [Real.norm_eq_abs] using hb x (Set.uIoc_subset_uIcc hx)))

-- manifest card: calculus_v5_integral_strict_positive
example (f : ℝ → ℝ) (a b : ℝ) (hab : a < b) (hc : ContinuousOn f (Set.Icc a b)) (hn : ∀ x ∈ Set.Icc a b, 0 ≤ f x) (hp : ∃ c ∈ Set.Icc a b, 0 < f c) : 0 < ∫ x in a..b, f x := by
  exact intervalIntegral.integral_pos hab hc (fun x hx => hn x ⟨le_of_lt hx.1,hx.2⟩) hp

-- manifest card: calculus_v5_zero_integral_continuous_nonnegative
example (f : ℝ → ℝ) (a b : ℝ) (hab : a < b) (hc : ContinuousOn f (Set.Icc a b)) (hn : ∀ x ∈ Set.Icc a b, 0 ≤ f x) : (∫ x in a..b, f x)=0 ↔ ∀ x ∈ Set.Icc a b, f x=0 := by
  constructor
  · intro hi x hx
    by_contra h
    have hp := intervalIntegral.integral_pos hab hc (fun y hy => hn y ⟨le_of_lt hy.1,hy.2⟩) ⟨x,hx,lt_of_le_of_ne (hn x hx) (Ne.symm h)⟩
    linarith
  · intro hz
    calc
      (∫ x in a..b, f x) = ∫ x in a..b, (0 : ℝ) := intervalIntegral.integral_congr (by intro x hx; exact hz x (by simpa only [Set.uIcc_of_le hab.le] using hx))
      _ = 0 := by simp

-- manifest card: calculus_v5_weighted_integral_mean_value
example (f g : ℝ → ℝ) (a b : ℝ) (hf : ContinuousOn f (Set.uIcc a b)) (hg : IntervalIntegrable g MeasureTheory.volume a b) (hn : ∀ x ∈ Set.uIcc a b, 0 ≤ g x) : ∃ c ∈ Set.uIcc a b, (∫ x in a..b, f x*g x)=f c*(∫ x in a..b, g x) := by
  exact exists_eq_const_mul_intervalIntegral_of_nonneg hf hg (fun x hx => hn x (Set.uIoc_subset_uIcc hx))

-- manifest card: calculus_v5_odd_symmetric_integral
example (f : ℝ → ℝ) (a : ℝ) (hf : ∀ x, f (-x) = -f x) : (∫ x in (-a)..a, f x)=0 := by
  have h := intervalIntegral.integral_comp_neg (a := -a) (b := a) f
  simp only [neg_neg, hf, intervalIntegral.integral_neg] at h
  linarith

-- manifest card: calculus_v5_even_symmetric_integral
example (f : ℝ → ℝ) (a : ℝ) (hc : Continuous f) (hf : ∀ x, f (-x)=f x) : (∫ x in (-a)..a, f x)=2*(∫ x in (0:ℝ)..a, f x) := by
  have h : (∫ x in (-a)..(0:ℝ), f x) = ∫ x in (0:ℝ)..a, f x := by simpa only [hf, neg_zero, neg_neg] using (intervalIntegral.integral_comp_neg (a := -a) (b := 0) f)
  have hj := intervalIntegral.integral_add_adjacent_intervals (μ := MeasureTheory.volume) (hc.intervalIntegrable (-a) 0) (hc.intervalIntegrable 0 a)
  linarith

-- manifest card: calculus_v5_period_integral_translation
example (f : ℝ → ℝ) (a b c : ℝ) (hf : Function.Periodic f c) : (∫ x in a..a+c, f x)=(∫ x in b..b+c, f x) := by
  exact hf.intervalIntegral_add_eq a b

-- manifest card: calculus_v5_affine_substitution_integrable
example (f : ℝ → ℝ) (a b c d : ℝ) (hc : c ≠ 0) (hi : IntervalIntegrable f MeasureTheory.volume (c*a+d) (c*b+d)) : (∫ x in a..b, f (c*x+d))=(1/c)*(∫ x in c*a+d..c*b+d, f x) := by
  simpa only [one_div, smul_eq_mul] using intervalIntegral.integral_comp_mul_add (a := a) (b := b) f hc d

-- manifest card: calculus_v5_absolute_integrability
example (f : ℝ → ℝ) (a b : ℝ) (hf : IntervalIntegrable f MeasureTheory.volume a b) : IntervalIntegrable (fun x => |f x|) MeasureTheory.volume a b := by
  exact hf.abs

-- manifest card: calculus_v5_continuous_multiplier_integrability
example (f g : ℝ → ℝ) (a b : ℝ) (hf : IntervalIntegrable f MeasureTheory.volume a b) (hg : ContinuousOn g (Set.uIcc a b)) : IntervalIntegrable (fun x => f x*g x) MeasureTheory.volume a b := by
  exact hf.mul_continuousOn hg

-- manifest card: calculus_v5_integral_orientation_reversal
example (f : ℝ → ℝ) (a b : ℝ) : (∫ x in b..a, f x)= -(∫ x in a..b, f x) := by
  exact intervalIntegral.integral_symm a b

-- manifest card: calculus_v5_integral_difference
example (f g : ℝ → ℝ) (a b : ℝ) (hf : IntervalIntegrable f MeasureTheory.volume a b) (hg : IntervalIntegrable g MeasureTheory.volume a b) : (∫ x in a..b, f x-g x)=(∫ x in a..b, f x)-(∫ x in a..b, g x) := by
  exact intervalIntegral.integral_sub hf hg

-- manifest card: calculus_v5_fundamental_theorem_lower_endpoint
example (f : ℝ → ℝ) (a b : ℝ) (hf : Continuous f) : HasDerivAt (fun x => ∫ t in x..b, f t) (-f a) a := by
  convert! (hf.integral_hasStrictDerivAt b a).hasDerivAt.neg using 1
  funext x
  exact intervalIntegral.integral_symm b x

-- manifest card: calculus_v5_moving_both_endpoints
example (f g h : ℝ → ℝ) (a u v : ℝ) (hf : Continuous f) (hg : HasDerivAt g u a) (hh : HasDerivAt h v a) : HasDerivAt (fun x => ∫ t in g x..h x, f t) (f (h a)*v-f (g a)*u) a := by
  have h1 := ((hf.integral_hasStrictDerivAt 0 (h a)).hasDerivAt.comp a hh).sub ((hf.integral_hasStrictDerivAt 0 (g a)).hasDerivAt.comp a hg)
  convert! h1 using 1
  funext x
  exact (intervalIntegral.integral_interval_sub_left (hf.intervalIntegrable 0 (h x)) (hf.intervalIntegrable 0 (g x))).symm

-- manifest card: calculus_v5_local_integration_by_parts
example (f g h k : ℝ → ℝ) (a b : ℝ) (hf : ContinuousOn f (Set.uIcc a b)) (hg : ContinuousOn g (Set.uIcc a b)) (hfh : ∀ x ∈ Set.Ioo (min a b) (max a b), HasDerivAt f (h x) x) (hgk : ∀ x ∈ Set.Ioo (min a b) (max a b), HasDerivAt g (k x) x) (hh : IntervalIntegrable h MeasureTheory.volume a b) (hk : IntervalIntegrable k MeasureTheory.volume a b) : (∫ x in a..b, h x*g x+f x*k x)=f b*g b-f a*g a := by
  exact intervalIntegral.integral_deriv_mul_eq_sub_of_hasDerivAt hf hg hfh hgk hh hk

-- manifest card: calculus_v5_local_image_substitution
example (f g h : ℝ → ℝ) (a b : ℝ) (hd : ∀ x ∈ Set.uIcc a b, HasDerivAt f (h x) x) (hc : ContinuousOn h (Set.uIcc a b)) (hg : ContinuousOn g (f '' Set.uIcc a b)) : (∫ x in a..b, g (f x)*h x)=∫ x in f a..f b, g x := by
  exact intervalIntegral.integral_comp_mul_deriv' hd hc hg

-- manifest card: calculus_v5_inverse_derivative
example (f g : ℝ → ℝ) (a u : ℝ) (hg : ContinuousAt g a) (hf : HasDerivAt f u (g a)) (hu : u ≠ 0) (hi : ∀ x, f (g x)=x) : HasDerivAt g (1/u) a := by
  simpa only [one_div] using hf.of_local_left_inverse hg hu (Filter.Eventually.of_forall hi)

-- manifest card: calculus_v5_positive_derivative_strict_monotonicity
example (f g : ℝ → ℝ) (a b : ℝ) (hc : ContinuousOn f (Set.Icc a b)) (hd : ∀ x ∈ Set.Ioo a b, HasDerivAt f (g x) x) (hp : ∀ x ∈ Set.Ioo a b, 0 < g x) : StrictMonoOn f (Set.Icc a b) := by
  apply strictMonoOn_of_deriv_pos (convex_Icc a b) hc
  intro x hx
  have hx' : x ∈ Set.Ioo a b := by simpa only [interior_Icc] using hx
  rw [(hd x hx').deriv]
  exact hp x hx'

-- manifest card: calculus_v5_monotone_derivative_nonnegative
example (f : ℝ → ℝ) (a u : ℝ) (hm : Monotone f) (hf : HasDerivAt f u a) : 0 ≤ u := by
  simpa only [hf.deriv] using (hm.deriv_nonneg (x := a))

-- manifest card: calculus_v5_monotone_derivative_convex
example (f : ℝ → ℝ) (hf : Differentiable ℝ f) (hm : Monotone (deriv f)) : ConvexOn ℝ Set.univ f := by
  exact Monotone.convexOn_univ_of_deriv hf hm

-- manifest card: calculus_v5_strict_derivative_strict_convex
example (f : ℝ → ℝ) (hc : Continuous f) (hm : StrictMono (deriv f)) : StrictConvexOn ℝ Set.univ f := by
  apply StrictMonoOn.strictConvexOn_of_deriv convex_univ hc.continuousOn
  exact hm.strictMonoOn _

-- manifest card: calculus_v5_second_derivative_convex
example (f : ℝ → ℝ) (hf : Differentiable ℝ f) (h2 : Differentiable ℝ (deriv f)) (hn : ∀ x, 0 ≤ deriv (deriv f) x) : ConvexOn ℝ Set.univ f := by
  exact convexOn_univ_of_deriv2_nonneg hf h2 hn

-- manifest card: calculus_v5_second_derivative_minimum
example (f : ℝ → ℝ) (a u : ℝ) (hf : HasDerivAt f 0 a) (h2 : HasDerivAt (deriv f) u a) (hu : 0 < u) : IsLocalMin f a := by
  exact isLocalMin_of_deriv_deriv_pos (by simpa only [h2.deriv] using hu) hf.deriv hf.continuousAt

-- manifest card: calculus_v5_darboux_derivative_intermediate
example (f g : ℝ → ℝ) (a b u : ℝ) (hab : a ≤ b) (hf : ∀ x ∈ Set.Icc a b, HasDerivAt f (g x) x) (ha : g a ≤ u) (hb : u ≤ g b) : ∃ c ∈ Set.Icc a b, g c=u := by
  exact exists_hasDerivWithinAt_eq_of_ge_of_le hab (fun x hx => (hf x hx).hasDerivWithinAt) ha hb

-- manifest card: calculus_v5_cauchy_mean_value
example (f g h k : ℝ → ℝ) (a b : ℝ) (hab : a < b) (hf : ContinuousOn f (Set.Icc a b)) (hg : ContinuousOn g (Set.Icc a b)) (hd : ∀ x ∈ Set.Ioo a b, HasDerivAt f (h x) x) (he : ∀ x ∈ Set.Ioo a b, HasDerivAt g (k x) x) : ∃ c ∈ Set.Ioo a b, (g b-g a)*h c=(f b-f a)*k c := by
  exact exists_ratio_hasDerivAt_eq_ratio_slope f h hab hf hd g k hg he

-- manifest card: calculus_v5_derivative_difference_quotient_limit
example (f : ℝ → ℝ) (a u : ℝ) : HasDerivAt f u a ↔ Filter.Tendsto (fun t => (f (a+t)-f a)/t) (nhdsWithin 0 {0}ᶜ) (nhds u) := by
  simpa only [smul_eq_mul, div_eq_mul_inv, mul_comm] using (hasDerivAt_iff_tendsto_slope_zero (f := f) (x := a) (f' := u))

-- manifest card: calculus_v5_exponential_dominates_natural_power
example (n : ℕ) : Filter.Tendsto (fun x : ℝ => x^n*Real.exp (-x)) Filter.atTop (nhds 0) := by
  exact Real.tendsto_pow_mul_exp_neg_atTop_nhds_zero n

-- manifest card: calculus_v5_log_power_over_affine_limit
example (n : ℕ) (a b : ℝ) (ha : a ≠ 0) : Filter.Tendsto (fun x : ℝ => Real.log x^n/(a*x+b)) Filter.atTop (nhds 0) := by
  exact Real.tendsto_pow_log_div_mul_add_atTop a b n ha

-- manifest card: calculus_v5_lhopital_zero_right
example (f g h k : ℝ → ℝ) (a b u : ℝ) (hab : a < b) (hf : ∀ x ∈ Set.Ioo a b, HasDerivAt f (h x) x) (hg : ∀ x ∈ Set.Ioo a b, HasDerivAt g (k x) x) (hk : ∀ x ∈ Set.Ioo a b, k x ≠ 0) (hfa : Filter.Tendsto f (nhdsWithin a (Set.Ioi a)) (nhds 0)) (hga : Filter.Tendsto g (nhdsWithin a (Set.Ioi a)) (nhds 0)) (hq : Filter.Tendsto (fun x => h x/k x) (nhdsWithin a (Set.Ioi a)) (nhds u)) : Filter.Tendsto (fun x => f x/g x) (nhdsWithin a (Set.Ioi a)) (nhds u) := by
  exact HasDerivAt.lhopital_zero_right_on_Ioo hab hf hg hk hfa hga hq

-- manifest card: calculus_v5_compact_interval_uniform_continuity
example (f : ℝ → ℝ) (a b : ℝ) (hf : ContinuousOn f (Set.Icc a b)) : UniformContinuousOn f (Set.Icc a b) := by
  exact isCompact_Icc.uniformContinuousOn_of_continuous hf

-- manifest card: calculus_v5_monotone_interval_integrability
example (f : ℝ → ℝ) (a b : ℝ) (hf : MonotoneOn f (Set.uIcc a b)) : IntervalIntegrable f MeasureTheory.volume a b := by
  exact hf.intervalIntegrable

-- manifest card: calculus_v5_convex_secant_derivative_bounds
example (f : ℝ → ℝ) (a b u v : ℝ) (hc : ConvexOn ℝ Set.univ f) (hab : a < b) (ha : HasDerivAt f u a) (hb : HasDerivAt f v b) : u ≤ (f b-f a)/(b-a) ∧ (f b-f a)/(b-a) ≤ v := by
  simpa only [slope_def_field] using And.intro (hc.le_slope_of_hasDerivAt (Set.mem_univ a) (Set.mem_univ b) hab ha) (hc.slope_le_of_hasDerivAt (Set.mem_univ a) (Set.mem_univ b) hab hb)

-- manifest card: calculus_v5_convex_derivative_monotone
example (f : ℝ → ℝ) (hc : ConvexOn ℝ Set.univ f) (hf : Differentiable ℝ f) : Monotone (deriv f) := by
  exact monotoneOn_univ.mp (hc.monotoneOn_deriv (fun x _ => hf x))

-- manifest card: calculus_v5_punctured_limit_sum_product
example (f g : ℝ → ℝ) (a u v : ℝ) (hf : Filter.Tendsto f (nhdsWithin a {a}ᶜ) (nhds u)) (hg : Filter.Tendsto g (nhdsWithin a {a}ᶜ) (nhds v)) : Filter.Tendsto (fun x => f x+g x) (nhdsWithin a {a}ᶜ) (nhds (u+v)) ∧ Filter.Tendsto (fun x => f x*g x) (nhdsWithin a {a}ᶜ) (nhds (u*v)) := by
  exact ⟨hf.add hg,hf.mul hg⟩

-- manifest card: calculus_v5_punctured_limit_quotient
example (f g : ℝ → ℝ) (a u v : ℝ) (hf : Filter.Tendsto f (nhdsWithin a {a}ᶜ) (nhds u)) (hg : Filter.Tendsto g (nhdsWithin a {a}ᶜ) (nhds v)) (hv : v ≠ 0) : Filter.Tendsto (fun x => f x/g x) (nhdsWithin a {a}ᶜ) (nhds (u/v)) := by
  exact hf.div hg hv

-- manifest card: calculus_v5_punctured_limit_continuous_composition
example (f g : ℝ → ℝ) (a b : ℝ) (hf : Filter.Tendsto f (nhdsWithin a {a}ᶜ) (nhds b)) (hg : ContinuousAt g b) : Filter.Tendsto (fun x => g (f x)) (nhdsWithin a {a}ᶜ) (nhds (g b)) := by
  exact hg.tendsto.comp hf

-- manifest card: calculus_v5_removable_singularity_extension
example (f : ℝ → ℝ) (a u : ℝ) : Filter.Tendsto f (nhdsWithin a {a}ᶜ) (nhds u) ↔ ContinuousAt (Function.update f a u) a := by
  exact continuousAt_update_same.symm

-- manifest card: calculus_v5_punctured_squeeze_limit
example (f g h : ℝ → ℝ) (a u : ℝ) (hf : Filter.Tendsto f (nhdsWithin a {a}ᶜ) (nhds u)) (hh : Filter.Tendsto h (nhdsWithin a {a}ᶜ) (nhds u)) (hfg : ∀ x, f x ≤ g x) (hgh : ∀ x, g x ≤ h x) : Filter.Tendsto g (nhdsWithin a {a}ᶜ) (nhds u) := by
  exact tendsto_of_tendsto_of_tendsto_of_le_of_le hf hh hfg hgh

-- manifest card: calculus_v5_two_sided_limit_characterization
example (f : ℝ → ℝ) (a u : ℝ) : Filter.Tendsto f (nhdsWithin a {a}ᶜ) (nhds u) ↔ Filter.Tendsto f (nhdsWithin a (Set.Iio a)) (nhds u) ∧ Filter.Tendsto f (nhdsWithin a (Set.Ioi a)) (nhds u) := by
  simp [← Set.Iio_union_Ioi, nhdsWithin_union]

-- manifest card: calculus_v5_counterexample_limit_without_continuity
example (a u v : ℝ) (hne : u ≠ v) : Filter.Tendsto (Function.update (fun _ : ℝ => u) a v) (nhdsWithin a {a}ᶜ) (nhds u) ∧ ¬ContinuousAt (Function.update (fun _ : ℝ => u) a v) a := by
  have hl : Filter.Tendsto (Function.update (fun _ : ℝ => u) a v) (nhdsWithin a {a}ᶜ) (nhds u) := by
    apply Filter.Tendsto.congr' _ (tendsto_const_nhds (x := u))
    filter_upwards [self_mem_nhdsWithin] with x hx
    simp only [Set.mem_compl_iff, Set.mem_singleton_iff] at hx
    exact (Function.update_of_ne hx v (fun _ : ℝ => u)).symm
  refine ⟨hl, ?_⟩
  intro hc
  have hv : Filter.Tendsto (Function.update (fun _ : ℝ => u) a v) (nhdsWithin a {a}ᶜ) (nhds v) := by
    simpa only [Function.update_self] using hc.tendsto.mono_left nhdsWithin_le_nhds
  exact hne (tendsto_nhds_unique hl hv)

-- manifest card: calculus_v5_counterexample_zero_integral_cancellation
example (a b : ℝ) (hab : a < b) : Continuous (fun x : ℝ => x-(a+b)/2) ∧ (∫ x in a..b, (x-(a+b)/2))=0 ∧ (a-(a+b)/2) ≠ 0 := by
  refine ⟨continuous_id.sub continuous_const, ?_, ?_⟩
  · rw [intervalIntegral.integral_sub (f := fun x : ℝ => x) (g := fun _ : ℝ => (a+b)/2) (continuous_id.intervalIntegrable a b) (continuous_const.intervalIntegrable a b), integral_id, intervalIntegral.integral_const]
    simp only [smul_eq_mul]
    ring
  · linarith

-- manifest card: calculus_v5_counterexample_continuous_not_differentiable
example (a : ℝ) : Continuous (fun x : ℝ => |x-a|) ∧ ¬ DifferentiableAt ℝ (fun x : ℝ => |x-a|) a := by
  refine ⟨(continuous_id.sub continuous_const).abs, ?_⟩
  intro hd
  have hx : DifferentiableAt ℝ (fun x : ℝ => x+a) 0 := differentiableAt_id.add_const a
  have hh : DifferentiableAt ℝ (fun x : ℝ => |x-a|) (0+a) := by simpa using hd
  have hc := hh.comp 0 hx
  exact not_differentiableAt_abs_zero (by simpa only [Function.comp_def, add_sub_cancel_right] using hc)
