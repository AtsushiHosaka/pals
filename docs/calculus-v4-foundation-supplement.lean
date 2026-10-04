import Mathlib

-- manifest card: mv_foundation_stationary_not_minimum
example (E : Type*) [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] (u : E) (hu : u ≠ 0) (c : ℝ) (hc : c < 0) : HasGradientAt (fun x : E => c * ‖x‖^2) 0 0 ∧ ¬IsLocalMin (fun x : E => c * ‖x‖^2) 0 := by
 constructor
 · apply hasGradientAt_iff_hasFDerivAt.mpr
   convert! (hasStrictFDerivAt_norm_sq (0 : E)).hasFDerivAt.const_smul c using 1 <;> ext y <;> simp
 · intro h
   obtain ⟨δ,hδ,hh⟩ := Metric.eventually_nhds_iff.mp h
   have hn : 0 < ‖u‖ := norm_pos_iff.mpr hu
   let t := δ / (2 * ‖u‖)
   have ht : 0 < t := by dsimp [t]; positivity
   have hnorm : ‖t • u‖ = δ / 2 := by rw [norm_smul,Real.norm_eq_abs,abs_of_pos ht]; dsimp [t]; field_simp
   have hd : dist (t • u) 0 < δ := by simpa [dist_zero_right,hnorm] using (show δ / 2 < δ by linarith)
   have hv := hh hd
   simp only [norm_zero,zero_pow (by decide : 2 ≠ 0),mul_zero,hnorm] at hv
   have hp : 0 < (δ / 2)^2 := sq_pos_of_pos (by positivity)
   nlinarith [mul_neg_of_neg_of_pos hc hp]

-- manifest card: mv_foundation_nondifferentiable_minimum
example (E : Type*) [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] (u : E) (hu : u ≠ 0) : ∃ f : E → ℝ, IsLocalMin f 0 ∧ ¬DifferentiableAt ℝ f 0 := by
 letI : Nontrivial E := ⟨⟨u,0,hu⟩⟩
 refine ⟨fun x => ‖x‖, ?_, not_differentiableAt_norm_zero E⟩
 apply Filter.Eventually.of_forall
 intro x
 simpa using norm_nonneg x

-- manifest card: mv_foundation_quadratic_minimum_criterion
example (E : Type*) [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] (c : ℝ) (hc : 0 < c) (x : E) : IsLocalMin (fun y : E => c * ‖y‖^2) x ↔ x = 0 := by
 constructor
 · intro h
   have he := h.hasFDerivAt_eq_zero ((hasStrictFDerivAt_norm_sq x).hasFDerivAt.const_smul c)
   have hv := congrArg (fun A : E →L[ℝ] ℝ => A x) he
   simp [inner_self_eq_norm_sq_to_K] at hv
   exact hv.resolve_left (ne_of_gt hc)
 · intro hx
   subst x
   apply Filter.Eventually.of_forall
   intro y
   simpa using mul_nonneg hc.le (sq_nonneg ‖y‖)

-- manifest card: mv_foundation_nonnegative_quadratic_minimum
example (E : Type*) [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] (c : ℝ) (hc : 0 ≤ c) : IsLocalMin (fun x : E => c * ‖x‖^2) 0 ∧ ∀ x : E, c * ‖(0 : E)‖^2 ≤ c * ‖x‖^2 := by
 have h : ∀ x : E, c * ‖(0 : E)‖^2 ≤ c * ‖x‖^2 := by intro x; simpa using mul_nonneg hc (sq_nonneg ‖x‖)
 exact ⟨Filter.Eventually.of_forall h,h⟩

-- manifest card: mv_foundation_exact_residual_minimum
example (E F : Type*) [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] [NormedAddCommGroup F] [InnerProductSpace ℝ F] [FiniteDimensional ℝ F] (A : E →L[ℝ] F) (b : F) (x : E) (hx : A x = b) : IsLocalMin (fun y => ‖A y - b‖^2) x ∧ (∀ y, ‖A x - b‖^2 ≤ ‖A y - b‖^2) ∧ HasGradientAt (fun y => ‖A y - b‖^2) 0 x := by
 have h : ∀ y, ‖A x - b‖^2 ≤ ‖A y - b‖^2 := by intro y; simpa [hx] using sq_nonneg ‖A y - b‖
 refine ⟨Filter.Eventually.of_forall h,h,?_⟩
 apply hasGradientAt_iff_hasFDerivAt.mpr
 have hd := (hasStrictFDerivAt_norm_sq (A x - b)).hasFDerivAt.comp x (A.hasFDerivAt.sub_const b)
 convert! hd using 1 <;> ext y <;> simp [hx]
