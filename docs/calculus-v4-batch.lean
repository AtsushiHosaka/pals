import Mathlib

-- manifest card: calculus_v4_linear_map
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] {F : Type*} [NormedAddCommGroup F] [InnerProductSpace ℝ F] [FiniteDimensional ℝ F] (A : E →L[ℝ] F) (x : E) : HasFDerivAt (fun y => A y) A x := by
  exact A.hasFDerivAt

-- manifest card: calculus_v4_affine_map
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] {F : Type*} [NormedAddCommGroup F] [InnerProductSpace ℝ F] [FiniteDimensional ℝ F] (A : E →L[ℝ] F) (y : F) (x : E) : HasFDerivAt (fun z => A z+y) A x := by
  exact HasFDerivAt.add_const y A.hasFDerivAt

-- manifest card: calculus_v4_frechet_sum
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] {F : Type*} [NormedAddCommGroup F] [InnerProductSpace ℝ F] [FiniteDimensional ℝ F] (f : E → F) (A : E →L[ℝ] F) (x : E) (hf : HasFDerivAt f A x) (g : E → F) (B : E →L[ℝ] F) (hg : HasFDerivAt g B x) : HasFDerivAt (fun y => f y+g y) (A+B) x := by
  exact hf.add hg

-- manifest card: calculus_v4_frechet_difference
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] {F : Type*} [NormedAddCommGroup F] [InnerProductSpace ℝ F] [FiniteDimensional ℝ F] (f : E → F) (A : E →L[ℝ] F) (x : E) (hf : HasFDerivAt f A x) (g : E → F) (B : E →L[ℝ] F) (hg : HasFDerivAt g B x) : HasFDerivAt (fun y => f y-g y) (A-B) x := by
  exact hf.sub hg

-- manifest card: calculus_v4_constant_scalar
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] {F : Type*} [NormedAddCommGroup F] [InnerProductSpace ℝ F] [FiniteDimensional ℝ F] (f : E → F) (A : E →L[ℝ] F) (x : E) (hf : HasFDerivAt f A x) (c : ℝ) : HasFDerivAt (fun y => c • f y) (c • A) x := by
  exact hf.const_smul c

-- manifest card: calculus_v4_chain_rule
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] {F : Type*} [NormedAddCommGroup F] [InnerProductSpace ℝ F] [FiniteDimensional ℝ F] {G : Type*} [NormedAddCommGroup G] [InnerProductSpace ℝ G] [FiniteDimensional ℝ G] (f : E → F) (A : E →L[ℝ] F) (x : E) (hf : HasFDerivAt f A x) (g : F → G) (B : F →L[ℝ] G) (hg : HasFDerivAt g B (f x)) : HasFDerivAt (g ∘ f) (B.comp A) x := by
  exact hg.comp x hf

-- manifest card: calculus_v4_variable_scalar_product
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] {F : Type*} [NormedAddCommGroup F] [InnerProductSpace ℝ F] [FiniteDimensional ℝ F] (f : E → F) (A : E →L[ℝ] F) (x : E) (hf : HasFDerivAt f A x) (g : E → ℝ) (B : E →L[ℝ] ℝ) (hg : HasFDerivAt g B x) : HasFDerivAt (fun y => g y • f y) (g x • A + B.smulRight (f x)) x := by
  exact hg.smul hf

-- manifest card: calculus_v4_inner_product_rule
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] {F : Type*} [NormedAddCommGroup F] [InnerProductSpace ℝ F] [FiniteDimensional ℝ F] (f : E → F) (A : E →L[ℝ] F) (x : E) (hf : HasFDerivAt f A x) (g : E → F) (B : E →L[ℝ] F) (hg : HasFDerivAt g B x) : HasFDerivAt (fun y => inner ℝ (f y) (g y)) ((fderivInnerCLM ℝ (f x,g x)).comp (A.prod B)) x := by
  exact hf.inner ℝ hg

-- manifest card: calculus_v4_norm_square_chain
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] {F : Type*} [NormedAddCommGroup F] [InnerProductSpace ℝ F] [FiniteDimensional ℝ F] (f : E → F) (A : E →L[ℝ] F) (x : E) (hf : HasFDerivAt f A x) : HasFDerivAt (fun y => ‖f y‖^2) (2 • (innerSL ℝ (f x)).comp A) x := by
  exact hf.norm_sq

-- manifest card: calculus_v4_norm_away_zero
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] {F : Type*} [NormedAddCommGroup F] [InnerProductSpace ℝ F] [FiniteDimensional ℝ F] (f : E → F) (x : E) (hf : DifferentiableAt ℝ f x) (hx : f x ≠ 0) : DifferentiableAt ℝ (fun y => ‖f y‖) x := by
  exact hf.norm ℝ hx

-- manifest card: calculus_v4_distance_off_diagonal
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] {F : Type*} [NormedAddCommGroup F] [InnerProductSpace ℝ F] [FiniteDimensional ℝ F] (f g : E → F) (x : E) (hf : DifferentiableAt ℝ f x) (hg : DifferentiableAt ℝ g x) (hx : f x ≠ g x) : DifferentiableAt ℝ (fun y => dist (f y) (g y)) x := by
  exact hf.dist ℝ hg hx

-- manifest card: calculus_v4_frechet_unique
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] {F : Type*} [NormedAddCommGroup F] [InnerProductSpace ℝ F] [FiniteDimensional ℝ F] (f : E → F) (A : E →L[ℝ] F) (x : E) (hf : HasFDerivAt f A x) (B : E →L[ℝ] F) (hb : HasFDerivAt f B x) : A=B := by
  exact hf.unique hb

-- manifest card: calculus_v4_frechet_continuity
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] {F : Type*} [NormedAddCommGroup F] [InnerProductSpace ℝ F] [FiniteDimensional ℝ F] (f : E → F) (A : E →L[ℝ] F) (x : E) (hf : HasFDerivAt f A x) : ContinuousAt f x := by
  exact hf.continuousAt

-- manifest card: calculus_v4_frechet_operator_value
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] {F : Type*} [NormedAddCommGroup F] [InnerProductSpace ℝ F] [FiniteDimensional ℝ F] (f : E → F) (A : E →L[ℝ] F) (x : E) (hf : HasFDerivAt f A x) : fderiv ℝ f x=A := by
  exact hf.fderiv

-- manifest card: calculus_v4_gradient_riesz_representation
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] (f : E → ℝ) (x u : E) : HasGradientAt f u x ↔ HasFDerivAt f (InnerProductSpace.toDual ℝ E u) x := by
  exact hasGradientAt_iff_hasFDerivAt

-- manifest card: calculus_v4_gradient_unique
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] (f : E → ℝ) (x u : E) (hf : HasGradientAt f u x) (w : E) (hw : HasGradientAt f w x) : u=w := by
  exact hf.unique hw

-- manifest card: calculus_v4_gradient_continuity
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] (f : E → ℝ) (x u : E) (hf : HasGradientAt f u x) : ContinuousAt f x := by
  exact hf.continuousAt

-- manifest card: calculus_v4_gradient_linear_functional
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] (u x : E) : HasGradientAt (fun y => inner ℝ u y) u x := by
  apply hasGradientAt_iff_hasFDerivAt.mpr
  exact (InnerProductSpace.toDual ℝ E u).hasFDerivAt

-- manifest card: calculus_v4_gradient_squared_norm
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] (x : E) : HasGradientAt (fun y : E => ‖y‖^2) (2 • x) x := by
  apply hasGradientAt_iff_hasFDerivAt.mpr
  convert! (hasStrictFDerivAt_norm_sq x).hasFDerivAt using 1
    <;> ext y <;> simp [inner_smul_left]

-- manifest card: calculus_v4_minimum_gradient_zero
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] (f : E → ℝ) (x u : E) (hf : HasGradientAt f u x) (hm : IsLocalMin f x) : u=0 := by
  have h := hm.hasFDerivAt_eq_zero hf.hasFDerivAt
  exact (InnerProductSpace.toDual ℝ E).injective (by simpa using h)

-- manifest card: calculus_v4_directional_from_frechet
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] {F : Type*} [NormedAddCommGroup F] [InnerProductSpace ℝ F] [FiniteDimensional ℝ F] (f : E → F) (A : E →L[ℝ] F) (x : E) (hf : HasFDerivAt f A x) (u : E) : HasLineDerivAt ℝ f (A u) x u := by
  exact hf.hasLineDerivAt u

-- manifest card: calculus_v4_curve_chain_rule
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] {F : Type*} [NormedAddCommGroup F] [InnerProductSpace ℝ F] [FiniteDimensional ℝ F] (f : E → F) (A : E →L[ℝ] F) (c : ℝ → E) (t : ℝ) (u : E) (hc : HasDerivAt c u t) (hf : HasFDerivAt f A (c t)) : HasDerivAt (f ∘ c) (A u) t := by
  exact hf.comp_hasDerivAt t hc

-- manifest card: calculus_v4_gradient_along_curve
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] (f : E → ℝ) (c : ℝ → E) (t : ℝ) (u w : E) (hc : HasDerivAt c u t) (hf : HasGradientAt f w (c t)) : HasDerivAt (f ∘ c) (inner ℝ w u) t := by
  exact hf.hasFDerivAt.comp_hasDerivAt t hc

-- manifest card: calculus_v4_gradient_direction_bound
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] (f : E → ℝ) (x u : E) (hf : HasGradientAt f u x) (w : E) : |lineDeriv ℝ f x w| ≤ ‖u‖*‖w‖ := by
  rw [(hf.hasFDerivAt.hasLineDerivAt w).lineDeriv]
  exact abs_real_inner_le_norm u w

-- manifest card: calculus_v4_zero_derivative_constant
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] {F : Type*} [NormedAddCommGroup F] [InnerProductSpace ℝ F] [FiniteDimensional ℝ F] (f : E → F) (hf : ∀ z, HasFDerivAt f (0 : E →L[ℝ] F) z) (x y : E) : f x=f y := by
  exact is_const_of_fderiv_eq_zero (𝕜 := ℝ) (fun z => (hf z).differentiableAt) (fun z => (hf z).fderiv) x y

-- manifest card: calculus_v4_bounded_derivative_lipschitz
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] {F : Type*} [NormedAddCommGroup F] [InnerProductSpace ℝ F] [FiniteDimensional ℝ F] (f : E → F) (D : E → E →L[ℝ] F) (c : ℝ) (hf : ∀ z, HasFDerivAt f (D z) z) (hb : ∀ z, ‖D z‖ ≤ c) (x y : E) : ‖f y-f x‖ ≤ c*‖y-x‖ := by
  exact (convex_univ : Convex ℝ (Set.univ : Set E)).norm_image_sub_le_of_norm_hasFDerivWithin_le (fun z _ => (hf z).hasFDerivWithinAt) (fun z _ => hb z) (Set.mem_univ x) (Set.mem_univ y)

-- manifest card: calculus_v4_second_derivative_symmetry
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] {F : Type*} [NormedAddCommGroup F] [InnerProductSpace ℝ F] [FiniteDimensional ℝ F] (f : E → F) (D : E → E →L[ℝ] F) (H : E →L[ℝ] E →L[ℝ] F) (x u w : E) (hf : ∀ y, HasFDerivAt f (D y) y) (hD : HasFDerivAt D H x) : H u w=H w u := by
  exact second_derivative_symmetric hf hD u w

-- manifest card: calculus_v4_smooth_composition
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] {F : Type*} [NormedAddCommGroup F] [InnerProductSpace ℝ F] [FiniteDimensional ℝ F] {G : Type*} [NormedAddCommGroup G] [InnerProductSpace ℝ G] [FiniteDimensional ℝ G] (n : ℕ) (f : E → F) (g : F → G) (hf : ContDiff ℝ n f) (hg : ContDiff ℝ n g) : ContDiff ℝ n (g ∘ f) := by
  exact hg.comp hf

-- manifest card: calculus_v4_smooth_squared_norm
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] {F : Type*} [NormedAddCommGroup F] [InnerProductSpace ℝ F] [FiniteDimensional ℝ F] (n : ℕ) (f : E → F) (hf : ContDiff ℝ n f) : ContDiff ℝ n (fun y => ‖f y‖^2) := by
  exact hf.norm_sq ℝ

-- manifest card: calculus_v4_smooth_inner_product
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] {F : Type*} [NormedAddCommGroup F] [InnerProductSpace ℝ F] [FiniteDimensional ℝ F] (n : ℕ) (f g : E → F) (hf : ContDiff ℝ n f) (hg : ContDiff ℝ n g) : ContDiff ℝ n (fun y => inner ℝ (f y) (g y)) := by
  exact hf.inner ℝ hg

-- manifest card: calculus_v4_local_extremum_derivative_zero
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] (f : E → ℝ) (A : E →L[ℝ] ℝ) (x : E) (hf : HasFDerivAt f A x) (he : IsLocalExtr f x) : A=0 := by
  exact he.hasFDerivAt_eq_zero hf

-- manifest card: calculus_v4_gradient_sum
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] (f : E → ℝ) (x u : E) (hf : HasGradientAt f u x) (g : E → ℝ) (w : E) (hg : HasGradientAt g w x) : HasGradientAt (fun y => f y+g y) (u+w) x := by
  apply hasGradientAt_iff_hasFDerivAt.mpr
  convert! hf.hasFDerivAt.add hg.hasFDerivAt using 1 <;> simp

-- manifest card: calculus_v4_gradient_scalar
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] (f : E → ℝ) (x u : E) (hf : HasGradientAt f u x) (c : ℝ) : HasGradientAt (fun y => c*f y) (c • u) x := by
  apply hasGradientAt_iff_hasFDerivAt.mpr
  convert! hf.hasFDerivAt.const_smul c using 1 <;> simp

-- manifest card: calculus_v4_gradient_adjoint_chain
example {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [FiniteDimensional ℝ E] {F : Type*} [NormedAddCommGroup F] [InnerProductSpace ℝ F] [FiniteDimensional ℝ F] (g : E → F) (f : F → ℝ) (A : E →L[ℝ] F) (x : E) (u : F) (hg : HasFDerivAt g A x) (hf : HasGradientAt f u (g x)) : HasGradientAt (f ∘ g) (A.adjoint u) x := by
  apply hasGradientAt_iff_hasFDerivAt.mpr
  convert! hf.hasFDerivAt.comp x hg using 1
  ext v
  exact A.adjoint_inner_left v u
