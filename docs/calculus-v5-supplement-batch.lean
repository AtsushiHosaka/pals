import Mathlib

-- manifest card: calculus_supp_v5_difference_quotient_extension
example (f : ℝ → ℝ) (a u : ℝ) (hf : HasDerivAt f u a) : ContinuousAt (Function.update (fun t => (f (a+t)-f a)/t) 0 u) 0 := by
  apply continuousAt_update_same.mpr
  simpa only [smul_eq_mul, div_eq_mul_inv, mul_comm] using hf.tendsto_slope_zero

-- manifest card: calculus_supp_v5_product_converse_counterexample
example (a : ℝ) : HasDerivAt (fun x : ℝ => |x-a| * |x-a|) 0 a ∧ ¬DifferentiableAt ℝ (fun x : ℝ => |x-a|) a := by
  constructor
  · have h := ((hasDerivAt_id a).sub_const a).pow 2
    convert! h using 1 <;> simp [sq_abs, ← sq, Pi.pow_apply, funext_iff]
  · intro hd
    have hh : DifferentiableAt ℝ (fun x : ℝ => |x-a|) (0+a) := by simpa using hd
    exact not_differentiableAt_abs_zero (by simpa only [Function.comp_def, add_sub_cancel_right, id_eq] using hh.comp 0 (differentiableAt_id.add_const a))

-- manifest card: calculus_supp_v5_exp_quotient_derivative
example (f g : ℝ → ℝ) (a u v : ℝ) (hf : HasDerivAt f u a) (hg : HasDerivAt g v a) (h : g a ≠ 0) : HasDerivAt (fun x => Real.exp (f x) / g x) ((Real.exp (f a)*u*g a-Real.exp (f a)*v)/(g a)^2) a := by
  exact hf.exp.div hg h

-- manifest card: calculus_supp_v5_primitives_constant_difference
example (f g h : ℝ → ℝ) (a b : ℝ) (hf : ∀ x, HasDerivAt f (h x) x) (hg : ∀ x, HasDerivAt g (h x) x) : f b-g b=f a-g a := by
  exact is_const_of_deriv_eq_zero (fun x => ((hf x).sub (hg x)).differentiableAt) (fun x => by simpa using ((hf x).sub (hg x)).deriv) b a

-- manifest card: calculus_supp_v5_quadratic_unique_minimum
example (a c d : ℝ) (hc : 0 < c) : ∀ x : ℝ, d ≤ c*(x-a)^2+d ∧ (c*(x-a)^2+d=d ↔ x=a) := by
  intro x
  constructor
  · nlinarith [sq_nonneg (x-a)]
  · constructor
    · intro h
      have : (x-a)^2=0 := by nlinarith [sq_nonneg (x-a)]
      nlinarith [sq_nonneg (x-a)]
    · intro h; simp [h]

-- manifest card: calculus_supp_v5_stationary_not_minimum
example (a c : ℝ) (hc : 0 < c) : HasDerivAt (fun x : ℝ => -c*(x-a)^2) 0 a ∧ ∀ e : ℝ, 0<e → ∃ x, |x-a|<e ∧ -c*(x-a)^2 < -c*(a-a)^2 := by
  constructor
  · convert! (((hasDerivAt_id a).sub_const a).pow 2).const_mul (-c) using 1 <;> simp
  · intro e he
    refine ⟨a+e/2,?_,?_⟩
    · simp only [add_sub_cancel_left, abs_of_pos (half_pos he)]; linarith
    · simp only [add_sub_cancel_left, sub_self, zero_pow (by decide : 2≠0), mul_zero]
      have : 0 < (e/2)^2 := sq_pos_of_pos (half_pos he)
      nlinarith

-- manifest card: calculus_supp_v5_convex_stationary_global_minimum
example (f : ℝ → ℝ) (a : ℝ) (hc : ConvexOn ℝ Set.univ f) (ha : HasDerivAt f 0 a) : ∀ x, f a ≤ f x := by
  intro x
  rcases lt_trichotomy a x with h | h | h
  · have hs := hc.le_slope_of_hasDerivAt (Set.mem_univ a) (Set.mem_univ x) h ha
    rw [slope_def_field] at hs
    have := (le_div_iff₀ (sub_pos.mpr h)).mp hs
    linarith
  · simp [h]
  · have hs := hc.slope_le_of_hasDerivAt (Set.mem_univ x) (Set.mem_univ a) h ha
    rw [slope_def_field] at hs
    have := (div_le_iff₀ (sub_pos.mpr h)).mp hs
    linarith

-- manifest card: calculus_supp_v5_scale_integrability_equivalence
example (f : ℝ → ℝ) (a b c : ℝ) (hc : c ≠ 0) : IntervalIntegrable (fun x => f (c*x)) MeasureTheory.volume (a/c) (b/c) ↔ IntervalIntegrable f MeasureTheory.volume a b := by
  exact IntervalIntegrable.comp_mul_left_iff hc

-- manifest card: calculus_supp_v5_exp_product_ftc
example (f g h k : ℝ → ℝ) (a b : ℝ) (hf : ∀ x, HasDerivAt f (h x) x) (hg : ∀ x, HasDerivAt g (k x) x) (hi : IntervalIntegrable (fun x => Real.exp (f x)*(h x*g x+k x)) MeasureTheory.volume a b) : (∫ x in a..b, Real.exp (f x)*(h x*g x+k x))=Real.exp (f b)*g b-Real.exp (f a)*g a := by
  apply intervalIntegral.integral_eq_sub_of_hasDerivAt _ hi
  intro x hx
  convert! ((hf x).exp.mul (hg x)) using 1 <;> ring

-- manifest card: calculus_supp_v5_exponential_moment_integral
example (a b c : ℝ) (hc : c ≠ 0) : (∫ x in a..b, x*Real.exp (c*x)) = (b/c-1/c^2)*Real.exp (c*b)-(a/c-1/c^2)*Real.exp (c*a) := by
  apply intervalIntegral.integral_eq_sub_of_hasDerivAt _ ((by fun_prop : Continuous (fun x : ℝ => x*Real.exp (c*x))).intervalIntegrable a b)
  intro x hx
  have h1 := (((hasDerivAt_id x).div_const c).sub_const (1/c^2)).mul (((hasDerivAt_id x).const_mul c).exp)
  convert! h1 using 1 <;> simp only [id_eq] <;> field_simp <;> ring

-- manifest card: calculus_supp_v5_ftc_point_spike_counterexample
example (a b v : ℝ) (hv : v ≠ 0) : HasDerivAt (fun x => ∫ t in b..x, Function.update (fun _ : ℝ => 0) a v t) 0 a ∧ ¬HasDerivAt (fun x => ∫ t in b..x, Function.update (fun _ : ℝ => 0) a v t) v a := by
  have he : (fun x => ∫ t in b..x, Function.update (fun _ : ℝ => 0) a v t) = fun _ => (0:ℝ) := by
    funext x
    calc
      (∫ t in b..x, Function.update (fun _ : ℝ => 0) a v t) = ∫ t in b..x, (0:ℝ) := by
        apply intervalIntegral.integral_congr_ae
        filter_upwards [MeasureTheory.volume.ae_ne a] with t ht
        intro _
        simp [Function.update_of_ne ht]
      _=0 := by simp
  rw [he]
  exact ⟨hasDerivAt_const a 0, fun h => hv (h.unique (hasDerivAt_const a 0))⟩

-- manifest card: calculus_supp_v5_mvt_endpoint_counterexample
example (a b : ℝ) (hab : a < b) : ¬ ∃ x ∈ Set.Ioo a b, HasDerivAt (Function.update (fun _ : ℝ => (0:ℝ)) b 1) (1/(b-a)) x := by
  rintro ⟨x, hx, hd⟩
  have hz : HasDerivAt (Function.update (fun _ : ℝ => (0:ℝ)) b 1) 0 x := by
    apply (hasDerivAt_const x 0).congr_of_eventuallyEq
    filter_upwards [eventually_ne_nhds hx.2.ne] with t ht
    simp [Function.update_of_ne ht]
  have hn : (1:ℝ)/(b-a) ≠ 0 := div_ne_zero one_ne_zero (sub_ne_zero.mpr hab.ne')
  exact hn (hd.unique hz)

-- manifest card: calculus_supp_v5_quadratic_mean_value_point
example (a b c d : ℝ) (hab : a < b) : (a+b)/2 ∈ Set.Ioo a b ∧ HasDerivAt (fun x : ℝ => c*x^2+d) (((c*b^2+d)-(c*a^2+d))/(b-a)) ((a+b)/2) := by
  constructor
  · constructor <;> linarith
  · have hd := (((hasDerivAt_id ((a+b)/2)).pow 2).const_mul c).add_const d
    convert! hd using 1 <;> simp only [id_eq, Nat.cast_ofNat, Nat.reduceSub, pow_one, mul_one]
    field_simp [sub_ne_zero.mpr hab.ne']
    <;> ring

-- manifest card: calculus_supp_v5_mvt_constant_slope_recognition
example (f : ℝ → ℝ) (a b c : ℝ) (hab : a < b) (hc : ContinuousOn f (Set.Icc a b)) (hd : ∀ x, x ∈ Set.Ioo a b → HasDerivAt f c x) : f b-f a=c*(b-a) := by
  obtain ⟨x, hx, he⟩ := exists_hasDerivAt_eq_slope f (fun _ => c) hab hc hd
  exact (eq_div_iff (sub_ne_zero.mpr hab.ne')).mp he |>.symm

-- manifest card: calculus_supp_v5_strong_derivative_growth_minimum
example (f h : ℝ → ℝ) (a c : ℝ) (hc : 0 < c) (hf : ∀ x, HasDerivAt f (h x) x) (ha : h a = 0) (hh : ∀ x y, x ≤ y → 2*c*(y-x) ≤ h y-h x) : ∀ x, f a+c*(x-a)^2 ≤ f x := by
  let g : ℝ → ℝ := fun x => f x-c*(x-a)^2
  have hd : ∀ x, HasDerivAt g (h x-2*c*(x-a)) x := by
    intro x
    convert! (hf x).sub ((((hasDerivAt_id x).sub_const a).pow 2).const_mul c) using 1 <;> simp only [id_eq, Nat.cast_ofNat, Nat.reduceSub, pow_one, mul_one]
    <;> ring
  have he : deriv g = fun x => h x-2*c*(x-a) := funext fun x => (hd x).deriv
  have hm : Monotone (deriv g) := by
    rw [he]
    intro x y hxy
    have := hh x y hxy
    dsimp
    linarith
  have hg := hm.convexOn_univ_of_deriv (fun x => (hd x).differentiableAt)
  have hz : HasDerivAt g 0 a := by simpa [ha] using hd a
  intro x
  have hmin : g a ≤ g x := by
    rcases lt_trichotomy a x with hi | hi | hi
    · have hs := hg.le_slope_of_hasDerivAt (Set.mem_univ a) (Set.mem_univ x) hi hz
      rw [slope_def_field] at hs
      have := (le_div_iff₀ (sub_pos.mpr hi)).mp hs
      linarith
    · simp [hi]
    · have hs := hg.slope_le_of_hasDerivAt (Set.mem_univ x) (Set.mem_univ a) hi hz
      rw [slope_def_field] at hs
      have := (div_le_iff₀ (sub_pos.mpr hi)).mp hs
      linarith
  dsimp [g] at hmin
  nlinarith
