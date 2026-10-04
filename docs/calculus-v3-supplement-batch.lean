import Mathlib

-- manifest card: calculus_supp_v3_taylor_at_center
example (f : ℝ → ℝ) (n : ℕ) (a b c : ℝ) : taylorWithinEval f n (Set.uIcc a b) c c = f c := by
  exact taylorWithinEval_self f n (Set.uIcc a b) c

-- manifest card: calculus_supp_v3_taylor_uniform_remainder_bound
example (f : ℝ → ℝ) (n : ℕ) (a b c x : ℝ) (hab : a ≤ b) (hf : ContDiffOn ℝ (n+1) f (Set.uIcc a b)) (hx : a ≤ x ∧ x ≤ b) (hc : ∀ y, a ≤ y ∧ y ≤ b → |iteratedDerivWithin (n+1) f (Set.uIcc a b) y| ≤ c) : |f x - taylorWithinEval f n (Set.uIcc a b) a x| ≤ c*(x-a)^(n+1)/(n.factorial : ℝ) := by
  rw [Set.uIcc_of_le hab] at *
  change ‖f x - taylorWithinEval f n (Set.Icc a b) a x‖ ≤ _
  exact taylor_mean_remainder_bound hab hf hx (fun y hy => hc y hy)

-- manifest card: calculus_supp_v3_finite_taylor_not_exact
example (n : ℕ) (b : ℝ) (hb : 0 < b) : taylorWithinEval (fun x : ℝ => x^(n+1)) n (Set.uIcc 0 b) 0 b = 0 ∧ (0:ℝ) < b^(n+1) := by
  constructor
  · rw [taylor_within_apply]
    apply Finset.sum_eq_zero
    intro k hk
    have hk' : k ≤ n := Nat.le_of_lt_succ (Finset.mem_range.mp hk)
    rw [Set.uIcc_of_le hb.le, iteratedDerivWithin_pow (show (0:ℝ) ∈ Set.Icc 0 b from ⟨le_rfl, hb.le⟩) (uniqueDiffOn_Icc hb) (n+1) k]
    have hn : n+1-k ≠ 0 := by omega
    simp [zero_pow hn]
  · exact pow_pos hb _

-- manifest card: calculus_supp_v3_harmonic_term_test_counterexample
example (c : ℝ) (hc : c ≠ 0) : Filter.Tendsto (fun n : ℕ => c / (n:ℝ)) Filter.atTop (nhds 0) ∧ ¬Summable (fun n : ℕ => c / (n:ℝ)) := by
  refine ⟨tendsto_const_div_atTop_nhds_zero_nat c, ?_⟩
  simpa only [div_eq_mul_inv] using fun h => Real.not_summable_natCast_inv ((summable_mul_left_iff hc).mp h)

-- manifest card: calculus_supp_v3_geometric_majorant_error
example (u : ℕ → ℝ) (c q : ℝ) (hq0 : 0 ≤ q) (hq : q < 1) (hu : ∀ n, |u n| ≤ c*q^n) : Summable u ∧ ∀ n, |(∑ i ∈ Finset.range n, u i)-(∑' i, u i)| ≤ c*q^n/(1-q) := by
  have hs : Summable u := ((summable_geometric_of_lt_one hq0 hq).mul_left c).of_norm_bounded hu
  refine ⟨hs, ?_⟩
  intro n
  exact norm_sub_le_of_geometric_bound_of_hasSum hq hu hs.hasSum n

-- manifest card: calculus_supp_v3_power_series_interior_convergence
example (u : ℕ → ℝ) (a b c : ℝ) (ha : Filter.Tendsto (fun n => ∑ i ∈ Finset.range n, u i*a^i) Filter.atTop (nhds c)) (hb : |b| < |a|) : Summable (fun n => u n*b^n) := by
  exact summable_powerSeries_of_norm_lt ha.cauchySeq hb

-- manifest card: calculus_supp_v3_weighted_geometric_sum
example (q : ℝ) (hq : |q| < 1) : HasSum (fun n : ℕ => (n:ℝ)*q^n) (q/(1-q)^2) := by
  exact hasSum_coe_mul_geometric_of_norm_lt_one hq

-- manifest card: calculus_supp_v3_geometric_boundary_counterexample
example (q : ℝ) (hq : 1 ≤ |q|) : ¬Summable (fun n : ℕ => q^n) := by
  exact fun h => (not_lt.mpr hq) (summable_geometric_iff_norm_lt_one.mp h)

-- manifest card: calculus_supp_v3_geometric_sum_derivative
example (q : ℝ) (hq : |q| < 1) : HasDerivAt (fun x : ℝ => ∑' n : ℕ, x^n) (1/(1-q)^2) q := by
  have hn : (1:ℝ)-q ≠ 0 := by have := (abs_lt.mp hq).2; linarith
  have hd := (hasDerivAt_const q (1:ℝ)).div ((hasDerivAt_const q (1:ℝ)).sub (hasDerivAt_id q)) hn
  have hd' : HasDerivAt (fun x : ℝ => 1/(1-x)) (1/(1-q)^2) q := by convert! hd using 1 <;> simp
  apply hd'.congr_of_eventuallyEq
  filter_upwards [(isOpen_lt continuous_abs continuous_const).mem_nhds hq] with x hx
  simpa only [one_div] using tsum_geometric_of_norm_lt_one (show ‖x‖ < 1 from hx)
