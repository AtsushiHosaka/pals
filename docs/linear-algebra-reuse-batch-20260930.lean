import Mathlib

-- manifest card: la_reuse_kernel_injectivity
example {R M N : Type*} [CommRing R] [AddCommGroup M] [Module R M] [AddCommGroup N] [Module R N] (f : M →ₗ[R] N) : (LinearMap.ker f = ⊥ → Function.Injective f) ∧ (Function.Injective f → LinearMap.ker f = ⊥) := by
  exact ⟨LinearMap.ker_eq_bot.mp, LinearMap.ker_eq_bot.mpr⟩

-- manifest card: la_reuse_range_surjectivity
example {R M N : Type*} [CommRing R] [AddCommGroup M] [Module R M] [AddCommGroup N] [Module R N] (f : M →ₗ[R] N) : (LinearMap.range f = ⊤ → Function.Surjective f) ∧ (Function.Surjective f → LinearMap.range f = ⊤) := by
  exact ⟨LinearMap.range_eq_top.mp, LinearMap.range_eq_top.mpr⟩

-- manifest card: la_reuse_kernel_detects_zero
example {R M N : Type*} [CommRing R] [AddCommGroup M] [Module R M] [AddCommGroup N] [Module R N] (f : M →ₗ[R] N) : (LinearMap.ker f = ⊤ → f = 0) ∧ (f = 0 → LinearMap.ker f = ⊤) := by
  exact ⟨LinearMap.ker_eq_top.mp, LinearMap.ker_eq_top.mpr⟩

-- manifest card: la_reuse_range_detects_zero
example {R M N : Type*} [CommRing R] [AddCommGroup M] [Module R M] [AddCommGroup N] [Module R N] (f : M →ₗ[R] N) : (LinearMap.range f = ⊥ → f = 0) ∧ (f = 0 → LinearMap.range f = ⊥) := by
  exact ⟨LinearMap.range_eq_bot.mp, LinearMap.range_eq_bot.mpr⟩

-- manifest card: la_reuse_kernel_composition_inclusion
example {R M N P : Type*} [CommRing R] [AddCommGroup M] [Module R M] [AddCommGroup N] [Module R N] [AddCommGroup P] [Module R P] (f : M →ₗ[R] N) (g : N →ₗ[R] P) : LinearMap.ker f ≤ LinearMap.ker (g.comp f) := by
  exact LinearMap.ker_le_ker_comp f g

-- manifest card: la_reuse_kernel_postcompose_injective
example {R M N P : Type*} [CommRing R] [AddCommGroup M] [Module R M] [AddCommGroup N] [Module R N] [AddCommGroup P] [Module R P] (f : M →ₗ[R] N) (g : N →ₗ[R] P) : Function.Injective g → LinearMap.ker (g.comp f) = LinearMap.ker f := by
  intro hg
  exact LinearMap.ker_comp_of_ker_eq_bot f (LinearMap.ker_eq_bot.mpr hg)

-- manifest card: la_reuse_range_precompose_surjective
example {R M N P : Type*} [CommRing R] [AddCommGroup M] [Module R M] [AddCommGroup N] [Module R N] [AddCommGroup P] [Module R P] (f : M →ₗ[R] N) (g : N →ₗ[R] P) : Function.Surjective f → LinearMap.range (g.comp f) = LinearMap.range g := by
  intro hf
  exact LinearMap.range_comp_of_range_eq_top g (LinearMap.range_eq_top.mpr hf)

-- manifest card: la_reuse_zero_composite_criterion
example {R M N P : Type*} [CommRing R] [AddCommGroup M] [Module R M] [AddCommGroup N] [Module R N] [AddCommGroup P] [Module R P] (f : M →ₗ[R] N) (g : N →ₗ[R] P) : (LinearMap.range f ≤ LinearMap.ker g → g.comp f = 0) ∧ (g.comp f = 0 → LinearMap.range f ≤ LinearMap.ker g) := by
  exact ⟨LinearMap.range_le_ker_iff.mp, LinearMap.range_le_ker_iff.mpr⟩

-- manifest card: la_reuse_injective_composition
example {R M N P : Type*} [CommRing R] [AddCommGroup M] [Module R M] [AddCommGroup N] [Module R N] [AddCommGroup P] [Module R P] (f : M →ₗ[R] N) (g : N →ₗ[R] P) : Function.Injective f ∧ Function.Injective g → Function.Injective (g.comp f) := by
  rintro ⟨hf, hg⟩ x y hxy
  exact hf (hg hxy)

-- manifest card: la_reuse_surjective_composition
example {R M N P : Type*} [CommRing R] [AddCommGroup M] [Module R M] [AddCommGroup N] [Module R N] [AddCommGroup P] [Module R P] (f : M →ₗ[R] N) (g : N →ₗ[R] P) : Function.Surjective f ∧ Function.Surjective g → Function.Surjective (g.comp f) := by
  rintro ⟨hf, hg⟩ z
  obtain ⟨y, rfl⟩ := hg z
  obtain ⟨x, rfl⟩ := hf y
  exact ⟨x, rfl⟩

-- manifest card: la_reuse_injective_composite_first_factor
example {R M N P : Type*} [CommRing R] [AddCommGroup M] [Module R M] [AddCommGroup N] [Module R N] [AddCommGroup P] [Module R P] (f : M →ₗ[R] N) (g : N →ₗ[R] P) : Function.Injective (g.comp f) → Function.Injective f := by
  intro hgf x y hxy
  exact hgf (congrArg g hxy)

-- manifest card: la_reuse_surjective_composite_last_factor
example {R M N P : Type*} [CommRing R] [AddCommGroup M] [Module R M] [AddCommGroup N] [Module R N] [AddCommGroup P] [Module R P] (f : M →ₗ[R] N) (g : N →ₗ[R] P) : Function.Surjective (g.comp f) → Function.Surjective g := by
  intro hgf z
  obtain ⟨x, hx⟩ := hgf z
  exact ⟨f x, hx⟩

-- manifest card: la_reuse_left_inverse_injective
example {R M N : Type*} [CommRing R] [AddCommGroup M] [Module R M] [AddCommGroup N] [Module R N] (f : M →ₗ[R] N) (g : N →ₗ[R] M) : g.comp f = LinearMap.id → Function.Injective f := by
  intro hgf x y hxy
  have hx := LinearMap.congr_fun hgf x
  have hy := LinearMap.congr_fun hgf y
  simpa only [LinearMap.comp_apply, LinearMap.id_apply] using hx.symm.trans ((congrArg g hxy).trans hy)

-- manifest card: la_reuse_right_inverse_surjective
example {R M N : Type*} [CommRing R] [AddCommGroup M] [Module R M] [AddCommGroup N] [Module R N] (f : M →ₗ[R] N) (g : N →ₗ[R] M) : f.comp g = LinearMap.id → Function.Surjective f := by
  intro hfg y
  exact ⟨g y, LinearMap.congr_fun hfg y⟩

-- manifest card: la_reuse_cancel_injective_postcomposition
example {R M N P : Type*} [CommRing R] [AddCommGroup M] [Module R M] [AddCommGroup N] [Module R N] [AddCommGroup P] [Module R P] (f : M →ₗ[R] N) (h : M →ₗ[R] N) (g : N →ₗ[R] P) : Function.Injective g ∧ g.comp f = g.comp h → f = h := by
  rintro ⟨hg, heq⟩
  ext x
  exact hg (LinearMap.congr_fun heq x)

-- manifest card: la_reuse_cancel_surjective_precomposition
example {R M N P : Type*} [CommRing R] [AddCommGroup M] [Module R M] [AddCommGroup N] [Module R N] [AddCommGroup P] [Module R P] (f : M →ₗ[R] N) (g : N →ₗ[R] P) (h : N →ₗ[R] P) : Function.Surjective f ∧ g.comp f = h.comp f → g = h := by
  rintro ⟨hf, heq⟩
  ext y
  obtain ⟨x, rfl⟩ := hf y
  exact LinearMap.congr_fun heq x

-- manifest card: la_reuse_inverse_uniqueness
example {R M N : Type*} [CommRing R] [AddCommGroup M] [Module R M] [AddCommGroup N] [Module R N] (f : M →ₗ[R] N) (g : N →ₗ[R] M) (h : N →ₗ[R] M) : g.comp f = LinearMap.id ∧ f.comp h = LinearMap.id → g = h := by
  rintro ⟨hgf, hfh⟩
  ext y
  have a := LinearMap.congr_fun hgf (h y)
  have b := LinearMap.congr_fun hfh y
  exact (congrArg g b).symm.trans a

-- manifest card: la_reuse_split_kernel_range_complement
example {R M N : Type*} [CommRing R] [AddCommGroup M] [Module R M] [AddCommGroup N] [Module R N] (f : M →ₗ[R] N) (g : N →ₗ[R] M) : f.comp g = LinearMap.id → LinearMap.range g ⊔ LinearMap.ker f = ⊤ ∧ LinearMap.range g ⊓ LinearMap.ker f = ⊥ := by
  intro hfg
  constructor
  · apply top_unique
    intro x _
    apply Submodule.mem_sup.mpr
    refine ⟨g (f x), ⟨f x, rfl⟩, x - g (f x), ?_, ?_⟩
    · change f (x - g (f x)) = 0
      rw [map_sub, show f (g (f x)) = f x from LinearMap.congr_fun hfg (f x), sub_self]
    · abel
  · apply bot_unique
    rintro x ⟨⟨y, rfl⟩, hy⟩
    change g y = 0
    have hy0 : y = 0 := (LinearMap.congr_fun hfg y).symm.trans hy
    simp [hy0]

-- manifest card: la_reuse_idempotent_kernel_range_complement
example {R M : Type*} [CommRing R] [AddCommGroup M] [Module R M] (f : M →ₗ[R] M) : f.comp f = f → LinearMap.range f ⊔ LinearMap.ker f = ⊤ ∧ LinearMap.range f ⊓ LinearMap.ker f = ⊥ := by
  intro hf
  have hi : IsIdempotentElem f := hf
  exact ⟨(LinearMap.IsIdempotentElem.isCompl hi).sup_eq_top, (LinearMap.IsIdempotentElem.isCompl hi).inf_eq_bot⟩

-- manifest card: la_reuse_submodule_modular_law
example {R M : Type*} [CommRing R] [AddCommGroup M] [Module R M] (I : Submodule R M) (J : Submodule R M) (K : Submodule R M) : I ≤ K → I ⊔ (J ⊓ K) = (I ⊔ J) ⊓ K := by
  intro hik
  exact (sup_inf_assoc_of_le J hik).symm

-- manifest card: la_reuse_exact_sequence_zero_composite
example {R M N P : Type*} [CommRing R] [AddCommGroup M] [Module R M] [AddCommGroup N] [Module R N] [AddCommGroup P] [Module R P] (f : M →ₗ[R] N) (g : N →ₗ[R] P) : LinearMap.range f = LinearMap.ker g → g.comp f = 0 := by
  intro he
  exact LinearMap.range_le_ker_iff.mp he.le

-- manifest card: la_reuse_exactness_precompose_surjection
example {R Q M N P : Type*} [CommRing R] [AddCommGroup Q] [Module R Q] [AddCommGroup M] [Module R M] [AddCommGroup N] [Module R N] [AddCommGroup P] [Module R P] (h : Q →ₗ[R] M) (f : M →ₗ[R] N) (g : N →ₗ[R] P) : Function.Surjective h ∧ LinearMap.range f = LinearMap.ker g → LinearMap.range (f.comp h) = LinearMap.ker g := by
  rintro ⟨hh, he⟩
  rw [LinearMap.range_comp_of_range_eq_top f (LinearMap.range_eq_top.mpr hh), he]

-- manifest card: la_reuse_exactness_postcompose_injection
example {R M N P Q : Type*} [CommRing R] [AddCommGroup M] [Module R M] [AddCommGroup N] [Module R N] [AddCommGroup P] [Module R P] [AddCommGroup Q] [Module R Q] (f : M →ₗ[R] N) (g : N →ₗ[R] P) (h : P →ₗ[R] Q) : Function.Injective h ∧ LinearMap.range f = LinearMap.ker g → LinearMap.range f = LinearMap.ker (h.comp g) := by
  rintro ⟨hh, he⟩
  rw [LinearMap.ker_comp_of_ker_eq_bot g (LinearMap.ker_eq_bot.mpr hh)]
  exact he

-- manifest card: la_reuse_commuting_maps_kernel_sum
example {R M : Type*} [CommRing R] [AddCommGroup M] [Module R M] (f : M →ₗ[R] M) (g : M →ₗ[R] M) : f.comp g = g.comp f → LinearMap.ker f ⊔ LinearMap.ker g ≤ LinearMap.ker (g.comp f) := by
  intro hfg
  apply sup_le
  · exact LinearMap.ker_le_ker_comp f g
  · rw [← hfg]
    exact LinearMap.ker_le_ker_comp g f
