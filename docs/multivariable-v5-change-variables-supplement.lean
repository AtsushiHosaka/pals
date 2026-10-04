import Mathlib

-- manifest card: mv_v5_constant_map_not_coordinate_change
example (n : ℕ) (s : Set (Fin n → ℝ)) (_hs : MeasurableSet s) (x y c : Fin n → ℝ) (hx : x ∈ s) (hy : y ∈ s) (hxy : x ≠ y) : ∃ f : (Fin n → ℝ) → (Fin n → ℝ), ∃ D : (Fin n → ℝ) → ((Fin n → ℝ) →L[ℝ] (Fin n → ℝ)), (∀ z, f z = c) ∧ (∀ z, HasFDerivAt f (D z) z) ∧ ¬ Set.InjOn f s := by
  refine ⟨fun _ => c, fun _ => 0, fun _ => rfl, ?_, ?_⟩
  · intro z; exact hasFDerivAt_const c z
  · intro hi; exact hxy (hi hx hy rfl)

-- manifest card: mv_v5_successive_coordinate_changes
example (n : ℕ) (s : Set (Fin n → ℝ)) (f g : (Fin n → ℝ) → (Fin n → ℝ)) (D E : (Fin n → ℝ) → ((Fin n → ℝ) →L[ℝ] (Fin n → ℝ))) (F : (Fin n → ℝ) → ℝ) (hs : MeasurableSet s) (hD : ∀ x ∈ s, HasFDerivWithinAt f (D x) s x) (hf : Set.InjOn f s) (hE : ∀ y ∈ f '' s, HasFDerivWithinAt g (E y) (f '' s) y) (hg : Set.InjOn g (f '' s)) (hF : MeasureTheory.IntegrableOn F (g '' (f '' s))) : MeasureTheory.IntegrableOn (fun x => |(D x).det| * (|(E (f x)).det| * F (g (f x)))) s ∧ (∫ z in g '' (f '' s), F z) = ∫ x in s, |(D x).det| * (|(E (f x)).det| * F (g (f x))) := by
  have hm : MeasurableSet (f '' s) := MeasureTheory.measurable_image_of_fderivWithin hs hD hf
  have h1 : MeasureTheory.IntegrableOn (fun y => |(E y).det| * F (g y)) (f '' s) := by
    simpa only [smul_eq_mul] using (MeasureTheory.integrableOn_image_iff_integrableOn_abs_det_fderiv_smul MeasureTheory.volume hm hE hg F).mp hF
  constructor
  · simpa only [smul_eq_mul] using (MeasureTheory.integrableOn_image_iff_integrableOn_abs_det_fderiv_smul MeasureTheory.volume hs hD hf (fun y => |(E y).det| * F (g y))).mp h1
  · calc
      (∫ z in g '' (f '' s), F z) = ∫ y in f '' s, |(E y).det| * F (g y) := by
        simpa only [smul_eq_mul] using MeasureTheory.integral_image_eq_integral_abs_det_fderiv_smul MeasureTheory.volume hm hE hg F
      _ = ∫ x in s, |(D x).det| * (|(E (f x)).det| * F (g (f x))) := by
        simpa only [smul_eq_mul] using MeasureTheory.integral_image_eq_integral_abs_det_fderiv_smul MeasureTheory.volume hs hD hf (fun y => |(E y).det| * F (g y))
