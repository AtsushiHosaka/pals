import Mathlib

-- manifest card: commalg_v3_noetherian_iff_fg
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] : IsNoetherian R M ↔ ∀ U : Submodule R M, U.FG := by
  exact isNoetherian_def

-- manifest card: commalg_v3_noetherian_submodule_quotient
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] (U : Submodule R M) : IsNoetherian R M ↔ IsNoetherian R U ∧ IsNoetherian R (M ⧸ U) := by
  exact isNoetherian_iff_submodule_quotient U

-- manifest card: commalg_v3_noetherian_exact_extension
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] {N : Type*} [AddCommGroup N] [Module R N] {P : Type*} [AddCommGroup P] [Module R P] [ IsNoetherian R M] [IsNoetherian R P] (f : M →ₗ[R] N) (g : N →ₗ[R] P) (h : Function.Exact f g) : IsNoetherian R N := by
  exact isNoetherian_of_range_eq_ker f g h.linearMap_ker_eq.symm

-- manifest card: commalg_v3_noetherian_product
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] {N : Type*} [AddCommGroup N] [Module R N] [IsNoetherian R M] [IsNoetherian R N] : IsNoetherian R (M × N) := by
  infer_instance

-- manifest card: commalg_v3_artinian_submodule_quotient
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] (U : Submodule R M) : IsArtinian R M ↔ IsArtinian R U ∧ IsArtinian R (M ⧸ U) := by
  exact isArtinian_iff_submodule_quotient U

-- manifest card: commalg_v3_artinian_exact_extension
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] {N : Type*} [AddCommGroup N] [Module R N] {P : Type*} [AddCommGroup P] [Module R P] [ IsArtinian R M] [IsArtinian R P] (f : M →ₗ[R] N) (g : N →ₗ[R] P) (h : Function.Exact f g) : IsArtinian R N := by
  exact isArtinian_of_range_eq_ker f g h.linearMap_ker_eq.symm

-- manifest card: commalg_v3_artinian_product
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] {N : Type*} [AddCommGroup N] [Module R N] [IsArtinian R M] [IsArtinian R N] : IsArtinian R (M × N) := by
  infer_instance

-- manifest card: commalg_v3_noetherian_surjective_endomorphism
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] [IsNoetherian R M] (f : M →ₗ[R] M) (hf : Function.Surjective f) : Function.Injective f := by
  exact IsNoetherian.injective_of_surjective_endomorphism f hf

-- manifest card: commalg_v3_artinian_injective_endomorphism
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] [IsArtinian R M] (f : M →ₗ[R] M) (hf : Function.Injective f) : Function.Surjective f := by
  exact IsArtinian.surjective_of_injective_endomorphism f hf

-- manifest card: commalg_v3_noetherian_hom
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] {N : Type*} [AddCommGroup N] [Module R N] [Module.Finite R M] [IsNoetherian R N] : IsNoetherian R (M →ₗ[R] N) := by
  infer_instance

-- manifest card: commalg_v3_noetherian_ring_finite_module
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] [IsNoetherianRing R] [Module.Finite R M] : IsNoetherian R M := by
  infer_instance

-- manifest card: commalg_v3_finite_length_iff_chain_conditions
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] : IsFiniteLength R M ↔ IsNoetherian R M ∧ IsArtinian R M := by
  exact isFiniteLength_iff_isNoetherian_isArtinian

-- manifest card: commalg_v3_localization_preserves_injective
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] {N : Type*} [AddCommGroup N] [Module R N] (S : Submonoid R) (f : M →ₗ[R] N) (hf : Function.Injective f) : Function.Injective (IsLocalizedModule.map S (LocalizedModule.mkLinearMap S M) (LocalizedModule.mkLinearMap S N) f) := by
  exact IsLocalizedModule.map_injective S (LocalizedModule.mkLinearMap S M) (LocalizedModule.mkLinearMap S N) f hf

-- manifest card: commalg_v3_localization_preserves_surjective
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] {N : Type*} [AddCommGroup N] [Module R N] (S : Submonoid R) (f : M →ₗ[R] N) (hf : Function.Surjective f) : Function.Surjective (IsLocalizedModule.map S (LocalizedModule.mkLinearMap S M) (LocalizedModule.mkLinearMap S N) f) := by
  exact IsLocalizedModule.map_surjective S (LocalizedModule.mkLinearMap S M) (LocalizedModule.mkLinearMap S N) f hf

-- manifest card: commalg_v3_localization_exact
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] {N : Type*} [AddCommGroup N] [Module R N] {P : Type*} [AddCommGroup P] [Module R P] (S : Submonoid R) (f : M →ₗ[R] N) (g : N →ₗ[R] P) (h : Function.Exact f g) : Function.Exact (IsLocalizedModule.map S (LocalizedModule.mkLinearMap S M) (LocalizedModule.mkLinearMap S N) f) (IsLocalizedModule.map S (LocalizedModule.mkLinearMap S N) (LocalizedModule.mkLinearMap S P) g) := by
  exact LocalizedModule.map_exact S f g h

-- manifest card: commalg_v3_localization_kernel
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] {N : Type*} [AddCommGroup N] [Module R N] (S : Submonoid R) (f : M →ₗ[R] N) : LinearMap.ker (IsLocalizedModule.map S (LocalizedModule.mkLinearMap S M) (LocalizedModule.mkLinearMap S N) f) = (LinearMap.ker f).localized₀ S (LocalizedModule.mkLinearMap S M) := by
  exact LinearMap.ker_localizedMap_eq_localized₀_ker S (LocalizedModule.mkLinearMap S M) (LocalizedModule.mkLinearMap S N) f

-- manifest card: commalg_v3_localization_range
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] {N : Type*} [AddCommGroup N] [Module R N] (S : Submonoid R) (f : M →ₗ[R] N) : LinearMap.range (IsLocalizedModule.map S (LocalizedModule.mkLinearMap S M) (LocalizedModule.mkLinearMap S N) f) = (LinearMap.range f).localized₀ S (LocalizedModule.mkLinearMap S N) := by
  exact LinearMap.range_localizedMap_eq_localized₀_range S (LocalizedModule.mkLinearMap S M) (LocalizedModule.mkLinearMap S N) f

-- manifest card: commalg_v3_localization_composition
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] {N : Type*} [AddCommGroup N] [Module R N] {P : Type*} [AddCommGroup P] [Module R P] (S : Submonoid R) (f : M →ₗ[R] N) (g : N →ₗ[R] P) : (IsLocalizedModule.map S (LocalizedModule.mkLinearMap S M) (LocalizedModule.mkLinearMap S P) (g.comp f)) = (IsLocalizedModule.map S (LocalizedModule.mkLinearMap S N) (LocalizedModule.mkLinearMap S P) g).comp (IsLocalizedModule.map S (LocalizedModule.mkLinearMap S M) (LocalizedModule.mkLinearMap S N) f) := by
  exact IsLocalizedModule.map_comp' S (LocalizedModule.mkLinearMap S M) (LocalizedModule.mkLinearMap S N) (LocalizedModule.mkLinearMap S P) f g

-- manifest card: commalg_v3_localization_naturality
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] {N : Type*} [AddCommGroup N] [Module R N] (S : Submonoid R) (f : M →ₗ[R] N) : (IsLocalizedModule.map S (LocalizedModule.mkLinearMap S M) (LocalizedModule.mkLinearMap S N) f).comp (LocalizedModule.mkLinearMap S M) = (LocalizedModule.mkLinearMap S N).comp f := by
  exact IsLocalizedModule.map_comp S (LocalizedModule.mkLinearMap S M) (LocalizedModule.mkLinearMap S N) f

-- manifest card: commalg_v3_localization_intersection
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] (S : Submonoid R) (U V : Submodule R M) : (U ⊓ V).localized₀ S (LocalizedModule.mkLinearMap S M) = U.localized₀ S (LocalizedModule.mkLinearMap S M) ⊓ V.localized₀ S (LocalizedModule.mkLinearMap S M) := by
  exact Submodule.localized₀_inf S (LocalizedModule.mkLinearMap S M) U V

-- manifest card: commalg_v3_localization_ideal_action
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] (S : Submonoid R) (I : Ideal R) (U : Submodule R M) : (I • U).localized₀ S (LocalizedModule.mkLinearMap S M) = I • U.localized₀ S (LocalizedModule.mkLinearMap S M) := by
  exact Submodule.localized₀_smul S (LocalizedModule.mkLinearMap S M) U I

-- manifest card: commalg_v3_localization_extreme_submodules
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] (S : Submonoid R) : (⊥ : Submodule R M).localized₀ S (LocalizedModule.mkLinearMap S M) = ⊥ ∧ (⊤ : Submodule R M).localized₀ S (LocalizedModule.mkLinearMap S M) = ⊤ := by
  exact ⟨Submodule.localized₀_bot _ _, Submodule.localized₀_top _ _⟩

-- manifest card: commalg_v3_localization_contains_image
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] (S : Submonoid R) (U : Submodule R M) : U.map (LocalizedModule.mkLinearMap S M) ≤ U.localized₀ S (LocalizedModule.mkLinearMap S M) := by
  exact Submodule.map_le_localized₀ S (LocalizedModule.mkLinearMap S M) U

-- manifest card: commalg_v3_tensor_universal_property
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] {N : Type*} [AddCommGroup N] [Module R N] {P : Type*} [AddCommGroup P] [Module R P] (b : M →ₗ[R] N →ₗ[R] P) : ∃ f : TensorProduct R M N →ₗ[R] P, TensorProduct.curry f = b ∧ ∀ g : TensorProduct R M N →ₗ[R] P, TensorProduct.curry g = b → g = f := by
  refine ⟨TensorProduct.lift b, ?_, ?_⟩
  · rfl
  · intro g hg
    apply TensorProduct.curry_injective
    exact hg

-- manifest card: commalg_v3_tensor_lift_naturality
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] {N : Type*} [AddCommGroup N] [Module R N] {P : Type*} [AddCommGroup P] [Module R P] {Q : Type*} [AddCommGroup Q] [Module R Q] (b : M →ₗ[R] N →ₗ[R] P) (g : P →ₗ[R] Q) : TensorProduct.lift (b.compr₂ g) = g.comp (TensorProduct.lift b) := by
  exact TensorProduct.lift_compr₂ g

-- manifest card: commalg_v3_tensor_right_exact
example {R : Type*} [CommRing R] {X : Type*} [AddCommGroup X] [Module R X] {M : Type*} [AddCommGroup M] [Module R M] {N : Type*} [AddCommGroup N] [Module R N] {P : Type*} [AddCommGroup P] [Module R P] (f : M →ₗ[R] N) (g : N →ₗ[R] P) (h : Function.Exact f g) (hg : Function.Surjective g) : Function.Exact (f.lTensor X) (g.lTensor X) := by
  exact lTensor_exact X h hg

-- manifest card: commalg_v3_tensor_symmetry
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] {N : Type*} [AddCommGroup N] [Module R N] : Function.Injective (TensorProduct.comm R M N).toLinearMap ∧ Function.Surjective (TensorProduct.comm R M N).toLinearMap := by
  exact (TensorProduct.comm R M N).bijective

-- manifest card: commalg_v3_tensor_associativity
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] {N : Type*} [AddCommGroup N] [Module R N] {P : Type*} [AddCommGroup P] [Module R P] : Function.Injective (TensorProduct.assoc R M N P).toLinearMap ∧ Function.Surjective (TensorProduct.assoc R M N P).toLinearMap := by
  exact (TensorProduct.assoc R M N P).bijective

-- manifest card: commalg_v3_hom_contravariant_left_exact
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] {N : Type*} [AddCommGroup N] [Module R N] {P : Type*} [AddCommGroup P] [Module R P] {X : Type*} [AddCommGroup X] [Module R X] (f : M →ₗ[R] N) (g : N →ₗ[R] P) (h : Function.Exact f g) (hg : Function.Surjective g) : Function.Exact (LinearMap.lcomp R X g) (LinearMap.lcomp R X f) := by
  exact LinearMap.exact_lcomp_of_exact_of_surjective X h hg

-- manifest card: commalg_v3_hom_precomposition_injective
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] {N : Type*} [AddCommGroup N] [Module R N] {X : Type*} [AddCommGroup X] [Module R X] (f : M →ₗ[R] N) (hf : Function.Surjective f) : Function.Injective (LinearMap.lcomp R X f) := by
  exact LinearMap.lcomp_injective_of_surjective f hf

-- manifest card: commalg_v3_hom_postcomposition_injective
example {R : Type*} [CommRing R] {X : Type*} [AddCommGroup X] [Module R X] {M : Type*} [AddCommGroup M] [Module R M] {N : Type*} [AddCommGroup N] [Module R N] (f : M →ₗ[R] N) (hf : Function.Injective f) : Function.Injective ((LinearMap.llcomp R X M N f) : (X →ₗ[R] M) →ₗ[R] (X →ₗ[R] N)) := by
  intro u v huv
  ext x
  apply hf
  exact LinearMap.congr_fun huv x
