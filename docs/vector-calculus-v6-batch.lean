import Mathlib

-- manifest card: vector_v6_gauss_rectangle
example (f g : ℝ × ℝ → ℝ) (A B : ℝ × ℝ → (ℝ × ℝ) →L[ℝ] ℝ) (a b : ℝ × ℝ) (hab : a ≤ b) (hf : ContinuousOn f (Set.Icc a b)) (hg : ContinuousOn g (Set.Icc a b)) (hA : ∀ z ∈ Set.Ioo a.1 b.1 ×ˢ Set.Ioo a.2 b.2, HasFDerivAt f (A z) z) (hB : ∀ z ∈ Set.Ioo a.1 b.1 ×ˢ Set.Ioo a.2 b.2, HasFDerivAt g (B z) z) (hi : MeasureTheory.IntegrableOn (fun z => A z (1,0) + B z (0,1)) (Set.Icc a b)) :
 (∫ z in Set.Icc a b, A z (1,0) + B z (0,1)) = (((∫ x in a.1..b.1, g (x,b.2)) - (∫ x in a.1..b.1, g (x,a.2))) + (∫ y in a.2..b.2, f (b.1,y))) - (∫ y in a.2..b.2, f (a.1,y)) := by
 exact MeasureTheory.integral_divergence_prod_Icc_of_hasFDerivAt_of_le f g A B a b hab hf hg hA hB hi

-- manifest card: vector_v6_green_countable_exceptions
example (P Q : ℝ × ℝ → ℝ) (A B : ℝ × ℝ → (ℝ × ℝ) →L[ℝ] ℝ) (a b : ℝ × ℝ) (hab : a ≤ b) (s : Set (ℝ × ℝ)) (hs : s.Countable) (hP : ContinuousOn P (Set.Icc a b)) (hQ : ContinuousOn Q (Set.Icc a b)) (hA : ∀ z ∈ (Set.Ioo a.1 b.1 ×ˢ Set.Ioo a.2 b.2) \ s, HasFDerivAt P (A z) z) (hB : ∀ z ∈ (Set.Ioo a.1 b.1 ×ˢ Set.Ioo a.2 b.2) \ s, HasFDerivAt Q (B z) z) (hi : MeasureTheory.IntegrableOn (fun z => B z (1,0) - A z (0,1)) (Set.Icc a b)) :
 (∫ z in Set.Icc a b, B z (1,0) - A z (0,1)) = (((∫ x in a.1..b.1, P (x,a.2)) + (∫ y in a.2..b.2, Q (b.1,y))) - (∫ x in a.1..b.1, P (x,b.2))) - (∫ y in a.2..b.2, Q (a.1,y)) := by
 have h := MeasureTheory.integral_divergence_prod_Icc_of_hasFDerivAt_off_countable_of_le Q (fun z => -P z) B (fun z => -A z) a b hab s hs hQ hP.neg hB (fun z hz => (hA z hz).neg) (by simpa [sub_eq_add_neg] using hi)
 simp only [neg_apply,intervalIntegral.integral_neg] at h
 simpa only [sub_eq_add_neg] using h.trans (by ring)

-- manifest card: vector_v6_affine_flux
example (a b : ℝ × ℝ) (α β γ δ p q : ℝ) :
 (((∫ x in a.1..b.1, (γ*x+δ*b.2+q)) - (∫ x in a.1..b.1, (γ*x+δ*a.2+q))) + (∫ y in a.2..b.2, (α*b.1+β*y+p))) - (∫ y in a.2..b.2, (α*a.1+β*y+p)) = (α+δ)*(b.1-a.1)*(b.2-a.2) := by
 have h₁ : (∫ x in a.1..b.1, γ*x+δ*b.2+q) - (∫ x in a.1..b.1, γ*x+δ*a.2+q) = δ*(b.2-a.2)*(b.1-a.1) := by
   rw [← intervalIntegral.integral_sub (Continuous.intervalIntegrable (by fun_prop) _ _) (Continuous.intervalIntegrable (by fun_prop) _ _)]
   have he : (fun x : ℝ => (γ*x+δ*b.2+q)-(γ*x+δ*a.2+q)) = fun _ => δ*(b.2-a.2) := by funext x; ring
   rw [he,intervalIntegral.integral_const]
   simp only [smul_eq_mul]; ring
 have h₂ : (∫ y in a.2..b.2, α*b.1+β*y+p) - (∫ y in a.2..b.2, α*a.1+β*y+p) = α*(b.1-a.1)*(b.2-a.2) := by
   rw [← intervalIntegral.integral_sub (Continuous.intervalIntegrable (by fun_prop) _ _) (Continuous.intervalIntegrable (by fun_prop) _ _)]
   have he : (fun y : ℝ => (α*b.1+β*y+p)-(α*a.1+β*y+p)) = fun _ => α*(b.1-a.1) := by funext y; ring
   rw [he,intervalIntegral.integral_const]
   simp only [smul_eq_mul]; ring
 calc
  _ = ((∫ x in a.1..b.1, γ*x+δ*b.2+q) - (∫ x in a.1..b.1, γ*x+δ*a.2+q)) + ((∫ y in a.2..b.2, α*b.1+β*y+p) - (∫ y in a.2..b.2, α*a.1+β*y+p)) := by ring
  _ = _ := by rw [h₁,h₂]; ring

-- manifest card: vector_v6_c1_gauss_hypotheses
example (f g : ℝ × ℝ → ℝ) (a b : ℝ × ℝ) (hf : ContDiff ℝ 1 f) (hg : ContDiff ℝ 1 g) :
 ContinuousOn f (Set.Icc a b) ∧ ContinuousOn g (Set.Icc a b) ∧ (∀ z, HasFDerivAt f (fderiv ℝ f z) z) ∧ (∀ z, HasFDerivAt g (fderiv ℝ g z) z) ∧ MeasureTheory.IntegrableOn (fun z => fderiv ℝ f z (1,0) + fderiv ℝ g z (0,1)) (Set.Icc a b) := by
 refine ⟨hf.continuous.continuousOn,hg.continuous.continuousOn,?_,?_,?_⟩
 · intro z; exact (hf.differentiable (by norm_num) z).hasFDerivAt
 · intro z; exact (hg.differentiable (by norm_num) z).hasFDerivAt
 have hfc := hf.continuous_fderiv (by norm_num)
 have hgc := hg.continuous_fderiv (by norm_num)
 exact (hfc.clm_apply continuous_const |>.add (hgc.clm_apply continuous_const)).integrableOn_Icc

-- manifest card: vector_v6_missing_boundary_continuity
example (a b : ℝ × ℝ) (ha : a.1 < b.1) (hb : a.2 < b.2) (c : ℝ) (hc : c ≠ 0) :
 ∃ f : ℝ × ℝ → ℝ, (∀ z ∈ Set.Ioo a.1 b.1 ×ˢ Set.Ioo a.2 b.2, HasFDerivAt f (0 : (ℝ × ℝ) →L[ℝ] ℝ) z) ∧ (((∫ y in a.2..b.2, f (b.1,y))) - (∫ y in a.2..b.2, f (a.1,y))) ≠ 0 := by
 let f : ℝ × ℝ → ℝ := fun z => if z.1 = a.1 then c else 0
 refine ⟨f,?_,?_⟩
 · intro z hz
   apply hasFDerivAt_zero_of_eventually_const (0 : ℝ)
   have hn : z.1 ≠ a.1 := ne_of_gt hz.1.1
   have he : ∀ᶠ w in nhds z, w.1 ≠ a.1 := continuousAt_fst.eventually_ne hn
   filter_upwards [he] with w hw
   simp [f,hw]
 · simp only [f,ne_of_gt ha,↓reduceIte,eq_self,intervalIntegral.integral_zero,intervalIntegral.integral_const,smul_eq_mul,zero_sub,neg_ne_zero]
   exact mul_ne_zero (sub_ne_zero.mpr (ne_of_gt hb)) hc
