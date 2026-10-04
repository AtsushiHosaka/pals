import Mathlib

-- manifest card: mv_line_supp_v5_orientation_law
example (n : ℕ) (D : (Fin n → ℝ) → ((Fin n → ℝ) →L[ℝ] ℝ)) (c u : ℝ → (Fin n → ℝ)) (a b : ℝ) (hc : ∀ t ∈ Set.uIcc a b, HasDerivAt c (u t) t) : (IntervalIntegrable (fun t => D (c t) (u t)) MeasureTheory.volume a b ↔ IntervalIntegrable (fun t => D (c t) (u t)) MeasureTheory.volume b a) ∧ (∫ t in b..a, D (c t) (u t)) = -(∫ t in a..b, D (c t) (u t)) := by
  exact ⟨⟨fun h => h.symm, fun h => h.symm⟩, intervalIntegral.integral_symm a b⟩

-- manifest card: mv_line_supp_v5_split_parameter_interval
example (n : ℕ) (D : (Fin n → ℝ) → ((Fin n → ℝ) →L[ℝ] ℝ)) (c u : ℝ → (Fin n → ℝ)) (a b e : ℝ) (hc : ∀ t, HasDerivAt c (u t) t) (hi : IntervalIntegrable (fun t => D (c t) (u t)) MeasureTheory.volume a b) (hj : IntervalIntegrable (fun t => D (c t) (u t)) MeasureTheory.volume b e) : (∫ t in a..b, D (c t) (u t)) + (∫ t in b..e, D (c t) (u t)) = ∫ t in a..e, D (c t) (u t) := by
  exact intervalIntegral.integral_add_adjacent_intervals hi hj

-- manifest card: mv_line_supp_v5_orientation_counterexample
example (n : ℕ) (i : Fin n) (x : Fin n → ℝ) (u : ℝ → (Fin n → ℝ)) (a b : ℝ) (hu : ∀ t, u t = Pi.single i 1) (hab : a ≠ b) : (∀ t, HasDerivAt (fun s => Function.update x i s) (u t) t) ∧ (∫ t in a..b, fderiv ℝ (fun y : Fin n → ℝ => y i) (Function.update x i t) (u t)) ≠ (∫ t in b..a, fderiv ℝ (fun y : Fin n → ℝ => y i) (Function.update x i t) (u t)) := by
  constructor
  · intro t
    rw [hu t]
    simpa using hasDerivAt_update x i t
  · have hi : ∀ y : Fin n → ℝ, fderiv ℝ (fun y : Fin n → ℝ => y i) y = ContinuousLinearMap.proj i := fun y => (hasFDerivAt_apply (𝕜 := ℝ) i y).fderiv
    simp_rw [hi, hu]
    simp only [ContinuousLinearMap.proj_apply, Pi.single_eq_same, intervalIntegral.integral_const, smul_eq_mul, mul_one]
    intro he
    apply hab
    linarith

-- manifest card: mv_line_supp_v5_bilinear_curve_integration_by_parts
example (n : ℕ) (B : (Fin n → ℝ) →L[ℝ] (Fin n → ℝ) →L[ℝ] ℝ) (D : (Fin n → ℝ) → ((Fin n → ℝ) →L[ℝ] ℝ)) (c d u w : ℝ → (Fin n → ℝ)) (a b : ℝ) (hD : ∀ x y, D x y = B x y) (hc : ∀ t ∈ Set.uIcc a b, HasDerivAt c (u t) t) (hd : ∀ t ∈ Set.uIcc a b, HasDerivAt d (w t) t) (hi : IntervalIntegrable (fun t => D (c t) (w t)) MeasureTheory.volume a b) (hj : IntervalIntegrable (fun t => D (u t) (d t)) MeasureTheory.volume a b) : (∫ t in a..b, D (c t) (w t)) + (∫ t in a..b, D (u t) (d t)) = B (c b) (d b) - B (c a) (d a) := by
  simp_rw [hD] at *
  rw [← intervalIntegral.integral_add hi hj]
  apply intervalIntegral.integral_eq_sub_of_hasDerivAt _ (hi.add hj)
  intro t ht
  exact B.hasDerivAt_of_bilinear (fun _ => hc t ht) (fun _ => hd t ht)
