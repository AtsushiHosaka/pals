import Mathlib

-- manifest card: calculus_v3_limit_sum
example (u v : ℕ → ℝ) (a b : ℝ) (hu : Filter.Tendsto u Filter.atTop (nhds a)) (hv : Filter.Tendsto v Filter.atTop (nhds b)) : Filter.Tendsto (fun n => u n + v n) Filter.atTop (nhds (a + b)) := by
  exact hu.add hv

-- manifest card: calculus_v3_limit_product
example (u v : ℕ → ℝ) (a b : ℝ) (hu : Filter.Tendsto u Filter.atTop (nhds a)) (hv : Filter.Tendsto v Filter.atTop (nhds b)) : Filter.Tendsto (fun n => u n * v n) Filter.atTop (nhds (a * b)) := by
  exact hu.mul hv

-- manifest card: calculus_v3_limit_quotient
example (u v : ℕ → ℝ) (a b : ℝ) (hu : Filter.Tendsto u Filter.atTop (nhds a)) (hv : Filter.Tendsto v Filter.atTop (nhds b)) (hb : b ≠ 0) : Filter.Tendsto (fun n => u n / v n) Filter.atTop (nhds (a / b)) := by
  exact hu.div hv hb

-- manifest card: calculus_v3_limit_absolute_value
example (u : ℕ → ℝ) (a : ℝ) (hu : Filter.Tendsto u Filter.atTop (nhds a)) : Filter.Tendsto (fun n => |u n|) Filter.atTop (nhds |a|) := by
  exact hu.abs

-- manifest card: calculus_v3_limit_unique
example (u : ℕ → ℝ) (a b : ℝ) (ha : Filter.Tendsto u Filter.atTop (nhds a)) (hb : Filter.Tendsto u Filter.atTop (nhds b)) : a = b := by
  exact tendsto_nhds_unique ha hb

-- manifest card: calculus_v3_limit_order
example (u v : ℕ → ℝ) (a b : ℝ) (hu : Filter.Tendsto u Filter.atTop (nhds a)) (hv : Filter.Tendsto v Filter.atTop (nhds b)) (hle : ∀ n, u n ≤ v n) : a ≤ b := by
  exact le_of_tendsto_of_tendsto hu hv (Filter.Eventually.of_forall hle)

-- manifest card: calculus_v3_squeeze
example (u v w : ℕ → ℝ) (a : ℝ) (hu : Filter.Tendsto u Filter.atTop (nhds a)) (hw : Filter.Tendsto w Filter.atTop (nhds a)) (hlo : ∀ n, u n ≤ v n) (hhi : ∀ n, v n ≤ w n) : Filter.Tendsto v Filter.atTop (nhds a) := by
  exact tendsto_of_tendsto_of_tendsto_of_le_of_le hu hw hlo hhi

-- manifest card: calculus_v3_limit_fixed_shift
example (u : ℕ → ℝ) (n : ℕ) (a : ℝ) : Filter.Tendsto (fun k => u (k+n)) Filter.atTop (nhds a) ↔ Filter.Tendsto u Filter.atTop (nhds a) := by
  exact Filter.tendsto_add_atTop_iff_nat n

-- manifest card: calculus_v3_monotone_bounded_limit
example (u : ℕ → ℝ) (b : ℝ) (hm : ∀ n m : ℕ, n ≤ m → u n ≤ u m) (hb : ∀ n, u n ≤ b) : ∃ a : ℝ, Filter.Tendsto u Filter.atTop (nhds a) := by
  exact ⟨⨆ n, u n, tendsto_atTop_ciSup (fun _ _ h => hm _ _ h) ⟨b, fun _ ⟨n, hn⟩ => hn ▸ hb n⟩⟩

-- manifest card: calculus_v3_geometric_limit
example (q : ℝ) (hq : |q| < 1) : Filter.Tendsto (fun n : ℕ => q^n) Filter.atTop (nhds 0) := by
  exact tendsto_pow_atTop_nhds_zero_of_abs_lt_one hq

-- manifest card: calculus_v3_reciprocal_natural_limit
example (a : ℝ) : Filter.Tendsto (fun n : ℕ => a / (n : ℝ)) Filter.atTop (nhds 0) := by
  exact tendsto_const_div_atTop_nhds_zero_nat a

-- manifest card: calculus_v3_has_sum_unique
example (u : ℕ → ℝ) (a b : ℝ) (ha : HasSum u a) (hb : HasSum u b) : a = b := by
  exact ha.unique hb

-- manifest card: calculus_v3_has_sum_add
example (u v : ℕ → ℝ) (a b : ℝ) (hu : HasSum u a) (hv : HasSum v b) : HasSum (fun n => u n + v n) (a+b) := by
  exact hu.add hv

-- manifest card: calculus_v3_has_sum_scalar
example (u : ℕ → ℝ) (a b : ℝ) (hu : HasSum u a) : HasSum (fun n => b * u n) (b*a) := by
  exact hu.mul_left b

-- manifest card: calculus_v3_absolute_comparison
example (u v : ℕ → ℝ) (hv : Summable v) (hb : ∀ n, |u n| ≤ v n) : Summable u := by
  exact hv.of_norm_bounded (by simpa only [Real.norm_eq_abs] using hb)

-- manifest card: calculus_v3_absolute_convergence
example (u : ℕ → ℝ) (hu : Summable (fun n => |u n|)) : Summable u := by
  exact Summable.of_norm (by simpa only [Real.norm_eq_abs] using hu)

-- manifest card: calculus_v3_summable_terms_zero
example (u : ℕ → ℝ) (hu : Summable u) : Filter.Tendsto u Filter.atTop (nhds 0) := by
  exact hu.tendsto_atTop_zero

-- manifest card: calculus_v3_partial_sums_limit
example (u : ℕ → ℝ) (a : ℝ) (hu : HasSum u a) : Filter.Tendsto (fun n : ℕ => ∑ i ∈ Finset.range n, u i) Filter.atTop (nhds a) := by
  exact hu.tendsto_sum_nat

-- manifest card: calculus_v3_summable_tail_iff
example (u : ℕ → ℝ) (n : ℕ) : Summable (fun k => u (k+n)) ↔ Summable u := by
  exact summable_nat_add_iff n

-- manifest card: calculus_v3_geometric_sum
example (q : ℝ) (hq : |q| < 1) : HasSum (fun n : ℕ => q^n) (1/(1-q)) := by
  simpa only [one_div] using hasSum_geometric_of_abs_lt_one hq

-- manifest card: calculus_v3_exponential_power_series
example (a : ℝ) : HasSum (fun n : ℕ => a^n / (n.factorial : ℝ)) (Real.exp a) := by
  simpa only [Real.exp_eq_exp_ℝ] using NormedSpace.expSeries_div_hasSum_exp a

-- manifest card: calculus_v3_p_series_criterion
example (p : ℝ) : Summable (fun n : ℕ => 1 / (n : ℝ)^p) ↔ 1 < p := by
  exact Real.summable_one_div_nat_rpow

-- manifest card: calculus_v3_nonnegative_bounded_partial_sums
example (u : ℕ → ℝ) (b : ℝ) (hn : ∀ n, 0 ≤ u n) (hb : ∀ n, ∑ i ∈ Finset.range n, u i ≤ b) : Summable u := by
  exact summable_of_sum_range_le hn hb

-- manifest card: calculus_v3_nonnegative_sum_upper_bound
example (u : ℕ → ℝ) (b : ℝ) (hn : ∀ n, 0 ≤ u n) (hb : ∀ n, ∑ i ∈ Finset.range n, u i ≤ b) : (∑' n, u n) ≤ b := by
  exact Real.tsum_le_of_sum_range_le hn hb

-- manifest card: calculus_v3_absolute_sum_bound
example (u : ℕ → ℝ) (hu : Summable (fun n => |u n|)) : |∑' n, u n| ≤ ∑' n, |u n| := by
  simpa only [Real.norm_eq_abs] using norm_tsum_le_tsum_norm (f := u) (by simpa only [Real.norm_eq_abs] using hu)

-- manifest card: calculus_v3_sum_split_prefix_tail
example (u : ℕ → ℝ) (n : ℕ) (hu : Summable u) : (∑ i ∈ Finset.range n, u i) + (∑' k, u (k+n)) = ∑' k, u k := by
  exact hu.sum_add_tsum_nat_add n

-- manifest card: calculus_v3_taylor_finite_expansion
example (f : ℝ → ℝ) (n : ℕ) (a b c x : ℝ) : taylorWithinEval f n (Set.uIcc a b) c x = ∑ k ∈ Finset.range (n+1), ((x-c)^k / (k.factorial : ℝ)) * iteratedDerivWithin k f (Set.uIcc a b) c := by
  simpa only [smul_eq_mul, div_eq_mul_inv, mul_comm] using taylor_within_apply f n (Set.uIcc a b) c x

-- manifest card: calculus_v3_taylor_successor
example (f : ℝ → ℝ) (n : ℕ) (a b c x : ℝ) : taylorWithinEval f (n+1) (Set.uIcc a b) c x = taylorWithinEval f n (Set.uIcc a b) c x + ((x-c)^(n+1) / ((n+1).factorial : ℝ)) * iteratedDerivWithin (n+1) f (Set.uIcc a b) c := by
  rw [taylorWithinEval_succ]
  simp only [smul_eq_mul, Nat.factorial_succ, Nat.cast_mul, Nat.cast_add, Nat.cast_one]
  ring

-- manifest card: calculus_v3_taylor_polynomial_derivative
example (f : ℝ → ℝ) (n : ℕ) (a b c x : ℝ) : HasDerivAt (fun y => taylorWithinEval f (n+1) (Set.uIcc a b) c y) (taylorWithinEval (iteratedDerivWithin 1 f (Set.uIcc a b)) n (Set.uIcc a b) c x) x := by
  simpa only [iteratedDerivWithin_one] using (hasDerivAt_taylorWithinEval_succ (x₀ := c) (x := x) (s := Set.uIcc a b) f n)

-- manifest card: calculus_v3_taylor_lagrange_remainder
example (f : ℝ → ℝ) (n : ℕ) (a b : ℝ) (hab : a < b) (hf : ContDiffOn ℝ (n+1 : ℕ) f (Set.uIcc a b)) : ∃ c : ℝ, (a<c ∧ c<b) ∧ f b - taylorWithinEval f n (Set.uIcc a b) a b = iteratedDeriv (n+1) f c * (b-a)^(n+1) / ((n+1).factorial : ℝ) := by
  simpa only [Set.uIoo_of_lt hab, Set.mem_Ioo] using taylor_mean_remainder_lagrange_iteratedDeriv (ne_of_lt hab) hf

-- manifest card: calculus_v3_taylor_integral_remainder
example (f : ℝ → ℝ) (n : ℕ) (a b : ℝ) (hf : ContDiffOn ℝ (n+1 : ℕ) f (Set.uIcc a b)) : f b - taylorWithinEval f n (Set.uIcc a b) a b = ∫ t : ℝ in a..b, ((b-t)^n / (n.factorial : ℝ)) * iteratedDerivWithin (n+1) f (Set.uIcc a b) t := by
  simpa only [smul_eq_mul] using taylor_integral_remainder hf
