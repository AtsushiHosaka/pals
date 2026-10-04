import Mathlib

-- manifest card: vector_v6_constant_curl_circulation
example (P Q : ℝ × ℝ → ℝ) (A B : ℝ × ℝ → (ℝ × ℝ) →L[ℝ] ℝ) (a b : ℝ × ℝ) (hab : a ≤ b) (s : Set (ℝ × ℝ)) (hs : s.Countable) (hP : ContinuousOn P (Set.Icc a b)) (hQ : ContinuousOn Q (Set.Icc a b)) (hA : ∀ z ∈ (Set.Ioo a.1 b.1 ×ˢ Set.Ioo a.2 b.2) \ s, HasFDerivAt P (A z) z) (hB : ∀ z ∈ (Set.Ioo a.1 b.1 ×ˢ Set.Ioo a.2 b.2) \ s, HasFDerivAt Q (B z) z) (hi : MeasureTheory.IntegrableOn (fun z => B z (1,0) - A z (0,1)) (Set.Icc a b)) (c : ℝ) (hcurl : ∀ z ∈ Set.Icc a b, B z (1,0) - A z (0,1) = c) :
 (((∫ x in a.1..b.1, P (x,a.2)) + (∫ y in a.2..b.2, Q (b.1,y))) - (∫ x in a.1..b.1, P (x,b.2))) - (∫ y in a.2..b.2, Q (a.1,y)) = c*(b.1-a.1)*(b.2-a.2) := by
 have hgreen :  (∫ z in Set.Icc a b, B z (1,0) - A z (0,1)) = (((∫ x in a.1..b.1, P (x,a.2)) + (∫ y in a.2..b.2, Q (b.1,y))) - (∫ x in a.1..b.1, P (x,b.2))) - (∫ y in a.2..b.2, Q (a.1,y)) := by
   have h := MeasureTheory.integral_divergence_prod_Icc_of_hasFDerivAt_off_countable_of_le Q (fun z => -P z) B (fun z => -A z) a b hab s hs hQ hP.neg hB (fun z hz => (hA z hz).neg) (by simpa [sub_eq_add_neg] using hi)
   simp only [neg_apply,intervalIntegral.integral_neg] at h
   simpa only [sub_eq_add_neg] using h.trans (by ring)
 have he :  (∫ z in Set.Icc a b, B z (1,0) - A z (0,1)) = (∫ z in Set.Icc a b, c) := by
  apply MeasureTheory.setIntegral_congr_fun measurableSet_Icc
  intro z hz
  exact hcurl z hz
 rw [he] at hgreen
 apply hgreen.symm.trans
 rw [MeasureTheory.setIntegral_const]
 simp only [MeasureTheory.measureReal_def, smul_eq_mul]
 have hv : MeasureTheory.volume (Set.Icc a b) = ENNReal.ofReal (b.1-a.1) * ENNReal.ofReal (b.2-a.2) := by
  rw [show Set.Icc a b = Set.Icc a.1 b.1 ×ˢ Set.Icc a.2 b.2 by ext z; simp only [Set.mem_Icc,Prod.le_def,Set.mem_prod]; tauto]
  change ((MeasureTheory.volume : MeasureTheory.Measure ℝ).prod MeasureTheory.volume) ((Set.Icc a.1 b.1) ×ˢ (Set.Icc a.2 b.2)) = _
  rw [MeasureTheory.Measure.prod_prod,Real.volume_Icc,Real.volume_Icc]
 rw [hv,ENNReal.toReal_mul,ENNReal.toReal_ofReal (sub_nonneg.mpr hab.1),ENNReal.toReal_ofReal (sub_nonneg.mpr hab.2)]
 ring
