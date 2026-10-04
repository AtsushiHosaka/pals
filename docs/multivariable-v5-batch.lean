import Mathlib

-- manifest card: mv_v5_coordinate_projection
example (n : ℕ) (i : Fin n) (x : Fin n → ℝ) : HasFDerivAt (fun y : Fin n → ℝ => y i) (ContinuousLinearMap.proj i : (Fin n → ℝ) →L[ℝ] ℝ) x := by
  exact hasFDerivAt_apply (𝕜 := ℝ) i x

-- manifest card: mv_v5_coordinate_update
example (n : ℕ) (x : Fin n → ℝ) (i : Fin n) (t : ℝ) : HasDerivAt (Function.update x i) (Pi.single i 1) t := by
  exact hasDerivAt_update x i t

-- manifest card: mv_v5_coordinate_partial_from_total
example (n : ℕ) (f : (Fin n → ℝ) → ℝ) (A : (Fin n → ℝ) →L[ℝ] ℝ) (x : Fin n → ℝ) (i : Fin n) (hf : HasFDerivAt f A x) : HasDerivAt (fun t => f (Function.update x i t)) (A (Pi.single i 1)) (x i) := by
  have hh : HasFDerivAt f A (Function.update x i (x i)) := by simpa using hf
  exact hh.comp_hasDerivAt (x i) (hasDerivAt_update x i (x i))

-- manifest card: mv_v5_component_derivative_assembly
example (m n : ℕ) (f : (Fin m → ℝ) → (Fin n → ℝ)) (A : (Fin m → ℝ) →L[ℝ] (Fin n → ℝ)) (x : Fin m → ℝ) : HasFDerivAt f A x ↔ ∀ j : Fin n, HasFDerivAt (fun y => f y j) ((ContinuousLinearMap.proj j).comp A) x := by
  exact hasFDerivAt_pi'

-- manifest card: mv_v5_component_differentiability
example (m n : ℕ) (f : (Fin m → ℝ) → (Fin n → ℝ)) (x : Fin m → ℝ) : DifferentiableAt ℝ f x ↔ ∀ j : Fin n, DifferentiableAt ℝ (fun y => f y j) x := by
  exact differentiableAt_pi

-- manifest card: mv_v5_jacobian_entries
example (m n : ℕ) (f : (Fin m → ℝ) → (Fin n → ℝ)) (x : Fin m → ℝ) (i : Fin m) (j : Fin n) (hf : DifferentiableAt ℝ f x) : HasDerivAt (fun t => f (Function.update x i t) j) (LinearMap.toMatrix' (fderiv ℝ f x).toLinearMap j i) (x i) := by
  have hc := (hasFDerivAt_pi'.mp hf.hasFDerivAt) j
  have hh : HasFDerivAt (fun y => f y j) ((ContinuousLinearMap.proj j).comp (fderiv ℝ f x)) (Function.update x i (x i)) := by simpa using hc
  simpa [Function.comp_def, LinearMap.toMatrix'_apply] using! hh.comp_hasDerivAt (x i) (hasDerivAt_update x i (x i))

-- manifest card: mv_v5_jacobian_chain
example (m n p : ℕ) (f : (Fin m → ℝ) → (Fin n → ℝ)) (g : (Fin n → ℝ) → (Fin p → ℝ)) (x : Fin m → ℝ) (hf : DifferentiableAt ℝ f x) (hg : DifferentiableAt ℝ g (f x)) : LinearMap.toMatrix' (fderiv ℝ (g ∘ f) x).toLinearMap = LinearMap.toMatrix' (fderiv ℝ g (f x)).toLinearMap * LinearMap.toMatrix' (fderiv ℝ f x).toLinearMap := by
  rw [fderiv_comp x hg hf, ContinuousLinearMap.toLinearMap_comp, LinearMap.toMatrix'_comp]

-- manifest card: mv_v5_jacobian_first_order_remainder
example (m n : ℕ) (f : (Fin m → ℝ) → (Fin n → ℝ)) (x : Fin m → ℝ) (hf : DifferentiableAt ℝ f x) : Asymptotics.IsLittleO (nhds x) (fun y => f y - f x - (LinearMap.toMatrix' (fderiv ℝ f x).toLinearMap).mulVec (y - x)) (fun y => y - x) := by
  simpa only [LinearMap.toMatrix'_mulVec, ContinuousLinearMap.coe_coe] using hf.hasFDerivAt.isLittleO

-- manifest card: mv_v5_continuous_block_partials
example (m n p : ℕ) (f : ((Fin m → ℝ) × (Fin n → ℝ)) → (Fin p → ℝ)) (A : ((Fin m → ℝ) × (Fin n → ℝ)) → ((Fin m → ℝ) →L[ℝ] (Fin p → ℝ))) (B : ((Fin m → ℝ) × (Fin n → ℝ)) → ((Fin n → ℝ) →L[ℝ] (Fin p → ℝ))) (x : Fin m → ℝ) (y : Fin n → ℝ) (hA : ∀ u v, HasFDerivAt (fun z => f (z,v)) (A (u,v)) u) (hB : ∀ u v, HasFDerivAt (fun z => f (u,z)) (B (u,v)) v) (cA : ContinuousAt A (x,y)) (cB : ContinuousAt B (x,y)) : HasStrictFDerivAt f ((A (x,y)).coprod (B (x,y))) (x,y) := by
  exact hasStrictFDerivAt_uncurry_coprod (𝕜 := ℝ) (u := (x,y)) (f := fun u v => f (u,v)) (f₁ := fun u v => A (u,v)) (f₂ := fun u v => B (u,v)) (Filter.Eventually.of_forall (fun z => hA z.1 z.2)) (Filter.Eventually.of_forall (fun z => hB z.1 z.2)) cA cB

-- manifest card: mv_v5_smooth_derivative_field
example (n k : ℕ) (f : (Fin n → ℝ) → ℝ) (hf : ContDiff ℝ (k+1) f) : ContDiff ℝ k (fderiv ℝ f) := by
  exact hf.fderiv_right (by simp)

-- manifest card: mv_v5_quadratic_derivative
example (n : ℕ) (B : (Fin n → ℝ) →L[ℝ] (Fin n → ℝ) →L[ℝ] ℝ) (x : Fin n → ℝ) : HasFDerivAt (fun y => B y y) (B x + B.flip x) x := by
  convert! B.hasFDerivAt_of_bilinear (hasFDerivAt_id x) (hasFDerivAt_id x) using 1

-- manifest card: mv_v5_quadratic_hessian
example (n : ℕ) (B : (Fin n → ℝ) →L[ℝ] (Fin n → ℝ) →L[ℝ] ℝ) (x : Fin n → ℝ) : HasFDerivAt (fun y => B y + B.flip y) (B + B.flip) x := by
  exact B.hasFDerivAt.add B.flip.hasFDerivAt

-- manifest card: mv_v5_quadratic_taylor_exact
example (n : ℕ) (B : (Fin n → ℝ) →L[ℝ] (Fin n → ℝ) →L[ℝ] ℝ) (x h : Fin n → ℝ) : B (x+h) (x+h) = B x x + (B x + B.flip x) h + B h h := by
  simp only [map_add, add_apply, ContinuousLinearMap.flip_apply]
  ring

-- manifest card: mv_v5_lagrange_abnormal_allowed
example (n : ℕ) (f g : (Fin n → ℝ) → ℝ) (A B : (Fin n → ℝ) →L[ℝ] ℝ) (x : Fin n → ℝ) (he : IsLocalExtrOn g {y | f y = f x} x) (hf : HasStrictFDerivAt f A x) (hg : HasStrictFDerivAt g B x) : ∃ a b : ℝ, (a ≠ 0 ∨ b ≠ 0) ∧ a • A + b • B = 0 := by
  obtain ⟨a,b,hne,heq⟩ := he.exists_multipliers_of_hasStrictFDerivAt_1d hf hg
  exact ⟨a,b,by simpa only [ne_eq, Prod.mk_eq_zero, not_and_or] using hne,heq⟩

-- manifest card: mv_v5_lagrange_regular_constraint
example (n : ℕ) (f g : (Fin n → ℝ) → ℝ) (A B : (Fin n → ℝ) →L[ℝ] ℝ) (x : Fin n → ℝ) (he : IsLocalExtrOn g {y | f y = f x} x) (hf : HasStrictFDerivAt f A x) (hg : HasStrictFDerivAt g B x) (hA : A ≠ 0) : ∃ c : ℝ, B = c • A := by
  obtain ⟨a,b,hne,heq⟩ := he.exists_multipliers_of_hasStrictFDerivAt_1d hf hg
  have hb : b ≠ 0 := by
    intro hb
    have haz : a • A = 0 := by simpa [hb] using heq
    have ha : a = 0 := (smul_eq_zero.mp haz).resolve_right hA
    exact hne (by simp [ha,hb])
  refine ⟨-a / b, ?_⟩
  ext v
  have hh := congrArg (fun C : (Fin n → ℝ) →L[ℝ] ℝ => C v) heq
  simp only [add_apply, smul_apply, smul_eq_mul, zero_apply] at hh ⊢
  field_simp
  nlinarith [hh]

-- manifest card: mv_v5_lagrange_finite_constraints
example (k n : ℕ) (F : Fin k → (Fin n → ℝ) → ℝ) (D : Fin k → (Fin n → ℝ) →L[ℝ] ℝ) (g : (Fin n → ℝ) → ℝ) (B : (Fin n → ℝ) →L[ℝ] ℝ) (x : Fin n → ℝ) (he : IsLocalExtrOn g {y | ∀ i, F i y = F i x} x) (hF : ∀ i, HasStrictFDerivAt (F i) (D i) x) (hg : HasStrictFDerivAt g B x) : ∃ (L : Fin k → ℝ) (b : ℝ), (L ≠ 0 ∨ b ≠ 0) ∧ (∑ i, L i • D i) + b • B = 0 := by
  obtain ⟨L,b,hne,heq⟩ := he.exists_multipliers_of_hasStrictFDerivAt hF hg
  exact ⟨L,b,by simpa only [ne_eq, Prod.mk_eq_zero, not_and_or] using hne,heq⟩

-- manifest card: mv_v5_fubini
example (m n : ℕ) (f : ((Fin m → ℝ) × (Fin n → ℝ)) → ℝ) (hf : MeasureTheory.Integrable f) : (∫ z, f z) = ∫ x, ∫ y, f (x,y) := by
  exact MeasureTheory.integral_prod f hf

-- manifest card: mv_v5_fubini_order_exchange
example (m n : ℕ) (f : ((Fin m → ℝ) × (Fin n → ℝ)) → ℝ) (hf : MeasureTheory.Integrable f) : (∫ x, ∫ y, f (x,y)) = ∫ y, ∫ x, f (x,y) := by
  exact MeasureTheory.integral_integral_swap hf

-- manifest card: mv_v5_separable_product_integral
example (m n : ℕ) (f : (Fin m → ℝ) → ℝ) (g : (Fin n → ℝ) → ℝ) (_hf : MeasureTheory.Integrable f) (_hg : MeasureTheory.Integrable g) : (∫ z : (Fin m → ℝ) × (Fin n → ℝ), f z.1 * g z.2) = (∫ x, f x) * (∫ y, g y) := by
  exact MeasureTheory.integral_prod_mul f g

-- manifest card: mv_v5_separable_product_integrable
example (m n : ℕ) (f : (Fin m → ℝ) → ℝ) (g : (Fin n → ℝ) → ℝ) (hf : MeasureTheory.Integrable f) (hg : MeasureTheory.Integrable g) : MeasureTheory.Integrable (fun z : (Fin m → ℝ) × (Fin n → ℝ) => f z.1 * g z.2) := by
  exact hf.mul_prod hg

-- manifest card: mv_v5_fubini_rectangular_domain
example (m n : ℕ) (f : ((Fin m → ℝ) × (Fin n → ℝ)) → ℝ) (s : Set (Fin m → ℝ)) (t : Set (Fin n → ℝ)) (hf : MeasureTheory.IntegrableOn f (s ×ˢ t)) : (∫ z in s ×ˢ t, f z) = ∫ x in s, ∫ y in t, f (x,y) := by
  exact MeasureTheory.setIntegral_prod f hf

-- manifest card: mv_v5_almost_every_section_integrable
example (m n : ℕ) (f : ((Fin m → ℝ) × (Fin n → ℝ)) → ℝ) (hf : MeasureTheory.Integrable f) : ∀ᵐ x, MeasureTheory.Integrable (fun y => f (x,y)) := by
  exact hf.prod_right_ae

-- manifest card: mv_v5_inner_integral_integrable
example (m n : ℕ) (f : ((Fin m → ℝ) × (Fin n → ℝ)) → ℝ) (hf : MeasureTheory.Integrable f) : MeasureTheory.Integrable (fun x => ∫ y, f (x,y)) := by
  exact hf.integral_prod_left

-- manifest card: mv_v5_absolute_section_criterion
example (m n : ℕ) (f : ((Fin m → ℝ) × (Fin n → ℝ)) → ℝ) (hf : MeasureTheory.AEStronglyMeasurable f) : MeasureTheory.Integrable f ↔ (∀ᵐ x, MeasureTheory.Integrable (fun y => f (x,y))) ∧ MeasureTheory.Integrable (fun x => ∫ y, ‖f (x,y)‖) := by
  exact MeasureTheory.integrable_prod_iff hf

-- manifest card: mv_v5_finite_separated_product_integral
example (n : ℕ) (F : Fin n → ℝ → ℝ) (_hF : ∀ i, MeasureTheory.Integrable (F i)) : (∫ x : Fin n → ℝ, ∏ i, F i (x i)) = ∏ i, ∫ t : ℝ, F i t := by
  exact MeasureTheory.integral_fin_nat_prod_volume_eq_prod F

-- manifest card: mv_v5_finite_separated_product_integrable
example (n : ℕ) (F : Fin n → ℝ → ℝ) (hF : ∀ i, MeasureTheory.Integrable (F i)) : MeasureTheory.Integrable (fun x : Fin n → ℝ => ∏ i, F i (x i)) := by
  exact MeasureTheory.Integrable.fintype_prod hF

-- manifest card: mv_v5_jacobian_change_variables
example (n : ℕ) (f : (Fin n → ℝ) → (Fin n → ℝ)) (D : (Fin n → ℝ) → ((Fin n → ℝ) →L[ℝ] (Fin n → ℝ))) (s : Set (Fin n → ℝ)) (hs : MeasurableSet s) (hD : ∀ x ∈ s, HasFDerivWithinAt f (D x) s x) (hi : Set.InjOn f s) (g : (Fin n → ℝ) → ℝ) (_hg : MeasureTheory.IntegrableOn g (f '' s)) : (∫ y in f '' s, g y) = ∫ x in s, |(D x).det| * g (f x) := by
  simpa only [smul_eq_mul] using MeasureTheory.integral_image_eq_integral_abs_det_fderiv_smul MeasureTheory.volume hs hD hi g

-- manifest card: mv_v5_jacobian_integrability_equivalence
example (n : ℕ) (f : (Fin n → ℝ) → (Fin n → ℝ)) (D : (Fin n → ℝ) → ((Fin n → ℝ) →L[ℝ] (Fin n → ℝ))) (s : Set (Fin n → ℝ)) (hs : MeasurableSet s) (hD : ∀ x ∈ s, HasFDerivWithinAt f (D x) s x) (hi : Set.InjOn f s) (g : (Fin n → ℝ) → ℝ) : MeasureTheory.IntegrableOn g (f '' s) ↔ MeasureTheory.IntegrableOn (fun x => |(D x).det| * g (f x)) s := by
  simpa only [smul_eq_mul] using MeasureTheory.integrableOn_image_iff_integrableOn_abs_det_fderiv_smul MeasureTheory.volume hs hD hi g

-- manifest card: mv_v5_differentiable_injective_image_measurable
example (n : ℕ) (f : (Fin n → ℝ) → (Fin n → ℝ)) (D : (Fin n → ℝ) → ((Fin n → ℝ) →L[ℝ] (Fin n → ℝ))) (s : Set (Fin n → ℝ)) (hs : MeasurableSet s) (hD : ∀ x ∈ s, HasFDerivWithinAt f (D x) s x) (hi : Set.InjOn f s) : MeasurableSet (f '' s) := by
  exact MeasureTheory.measurable_image_of_fderivWithin hs hD hi

-- manifest card: mv_v5_potential_line_integral
example (n : ℕ) (f : (Fin n → ℝ) → ℝ) (D : (Fin n → ℝ) → ((Fin n → ℝ) →L[ℝ] ℝ)) (c u : ℝ → (Fin n → ℝ)) (a b : ℝ) (hD : ∀ x, HasFDerivAt f (D x) x) (hc : ∀ t ∈ Set.uIcc a b, HasDerivAt c (u t) t) (hi : IntervalIntegrable (fun t => D (c t) (u t)) MeasureTheory.volume a b) : (∫ t in a..b, D (c t) (u t)) = f (c b) - f (c a) := by
  apply intervalIntegral.integral_eq_sub_of_hasDerivAt _ hi
  intro t ht
  exact (hD (c t)).comp_hasDerivAt t (hc t ht)

-- manifest card: mv_v5_potential_path_independence
example (n : ℕ) (f : (Fin n → ℝ) → ℝ) (D : (Fin n → ℝ) → ((Fin n → ℝ) →L[ℝ] ℝ)) (c u : ℝ → (Fin n → ℝ)) (a b : ℝ) (hD : ∀ x, HasFDerivAt f (D x) x) (hc : ∀ t ∈ Set.uIcc a b, HasDerivAt c (u t) t) (hi : IntervalIntegrable (fun t => D (c t) (u t)) MeasureTheory.volume a b) (d w : ℝ → (Fin n → ℝ)) (hd : ∀ t ∈ Set.uIcc a b, HasDerivAt d (w t) t) (hj : IntervalIntegrable (fun t => D (d t) (w t)) MeasureTheory.volume a b) (ha : c a = d a) (hb : c b = d b) : (∫ t in a..b, D (c t) (u t)) = ∫ t in a..b, D (d t) (w t) := by
  have h1 : (∫ t in a..b, D (c t) (u t)) = f (c b) - f (c a) := intervalIntegral.integral_eq_sub_of_hasDerivAt (fun t ht => (hD (c t)).comp_hasDerivAt t (hc t ht)) hi
  have h2 : (∫ t in a..b, D (d t) (w t)) = f (d b) - f (d a) := intervalIntegral.integral_eq_sub_of_hasDerivAt (fun t ht => (hD (d t)).comp_hasDerivAt t (hd t ht)) hj
  rw [h1,h2,ha,hb]

-- manifest card: mv_v5_partials_without_continuity
example (m n : ℕ) (i : Fin m) (j : Fin n) (a : ℝ) (ha : a ≠ 0) :
 let f : ((Fin m → ℝ) × (Fin n → ℝ)) → ℝ := fun z => if z.1 i = 0 ∨ z.2 j = 0 then 0 else a
 HasFDerivAt (fun x => f (x, 0)) (0 : (Fin m → ℝ) →L[ℝ] ℝ) 0 ∧ HasFDerivAt (fun y => f (0, y)) (0 : (Fin n → ℝ) →L[ℝ] ℝ) 0 ∧ ¬ ContinuousAt f (0, 0) := by
 dsimp only
 constructor
 · simpa using (hasFDerivAt_const (𝕜 := ℝ) (0 : ℝ) (0 : Fin m → ℝ))
 constructor
 · simpa using (hasFDerivAt_const (𝕜 := ℝ) (0 : ℝ) (0 : Fin n → ℝ))
 intro hc
 have ha' : 0 < |a| := abs_pos.mpr ha
 obtain ⟨δ, hδ, hh⟩ := Metric.continuousAt_iff.mp hc (|a| / 2) (by positivity)
 let x : Fin m → ℝ := fun _ => δ / 2
 let y : Fin n → ℝ := fun _ => δ / 2
 have hxy : dist (x,y) (0,0) < δ := by
   rw [Prod.dist_eq, max_lt_iff]
   constructor <;> apply (dist_pi_lt_iff hδ).mpr <;> intro k <;> simp [x,y,abs_of_pos hδ] <;> linarith
 have hz := hh hxy
 simp only [x, y, Pi.zero_apply] at hz
 have hn : δ / 2 ≠ 0 := ne_of_gt (by positivity)
 simp only [hn, false_or, ↓reduceIte, true_or, dist_zero_right, Real.norm_eq_abs] at hz
 linarith
