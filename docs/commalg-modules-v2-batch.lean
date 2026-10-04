import Mathlib

-- manifest card: commalg_modules_v2_quotient_kernel
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] (U : Submodule R M) : LinearMap.ker U.mkQ = U := by
  exact U.ker_mkQ

-- manifest card: commalg_modules_v2_quotient_surjective
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] (U : Submodule R M) : Function.Surjective U.mkQ := by
  exact U.mkQ_surjective

-- manifest card: commalg_modules_v2_quotient_exact_sequence
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] (U : Submodule R M) : Function.Exact U.subtype U.mkQ := by
  exact LinearMap.exact_subtype_mkQ U

-- manifest card: commalg_modules_v2_quotient_factorization
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] {N : Type*} [AddCommGroup N] [Module R N] (U : Submodule R M) (f : M →ₗ[R] N) (hU : U ≤ LinearMap.ker f) : ∃ g : (M ⧸ U) →ₗ[R] N, g.comp U.mkQ = f := by
  exact ⟨U.liftQ f hU, U.liftQ_mkQ f hU⟩

-- manifest card: commalg_modules_v2_quotient_factorization_unique
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] {N : Type*} [AddCommGroup N] [Module R N] (U : Submodule R M) (f g : (M ⧸ U) →ₗ[R] N) (h : f.comp U.mkQ = g.comp U.mkQ) : f = g := by
  apply LinearMap.ext
  intro x
  obtain ⟨m, rfl⟩ := U.mkQ_surjective x
  exact LinearMap.congr_fun h m

-- manifest card: commalg_modules_v2_quotient_submodule_correspondence_pullback
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] (U V : Submodule R M) : (V.map U.mkQ).comap U.mkQ = U ⊔ V := by
  exact U.comap_map_mkQ V

-- manifest card: commalg_modules_v2_quotient_submodule_correspondence_pushforward
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] (U : Submodule R M) (W : Submodule R (M ⧸ U)) : (W.comap U.mkQ).map U.mkQ = W := by
  exact Submodule.map_comap_eq_self (by simp [U.range_mkQ])

-- manifest card: commalg_modules_v2_quotient_by_kernel_embedding
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] {N : Type*} [AddCommGroup N] [Module R N] (f : M →ₗ[R] N) : ∃ g : (M ⧸ LinearMap.ker f) →ₗ[R] N, g.comp (LinearMap.ker f).mkQ = f ∧ Function.Injective g ∧ LinearMap.range g = LinearMap.range f := by
  refine ⟨(LinearMap.ker f).liftQ f le_rfl, Submodule.liftQ_mkQ _ _ _, ?_, Submodule.range_liftQ _ _ _⟩
  exact LinearMap.ker_eq_bot.mp (Submodule.ker_liftQ_eq_bot _ _ _ le_rfl)

-- manifest card: commalg_modules_v2_finite_quotient
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] (U : Submodule R M) [Module.Finite R M] : Module.Finite R (M ⧸ U) := by
  infer_instance

-- manifest card: commalg_modules_v2_finite_surjective_image
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] {N : Type*} [AddCommGroup N] [Module R N] (f : M →ₗ[R] N) [Module.Finite R M] (hf : Function.Surjective f) : Module.Finite R N := by
  exact Module.Finite.of_surjective f hf

-- manifest card: commalg_modules_v2_finite_submodule_carrier_iff_fg
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] (U : Submodule R M) : Module.Finite R U ↔ U.FG := by
  exact Module.Finite.iff_fg

-- manifest card: commalg_modules_v2_finite_extension_quotient
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] (U : Submodule R M) (hU : U.FG) [Module.Finite R (M ⧸ U)] : Module.Finite R M := by
  letI : Module.Finite R U := Module.Finite.of_fg hU
  exact Module.Finite.of_submodule_quotient U

-- manifest card: commalg_modules_v2_nakayama_jacobson_submodule
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] (I : Ideal R) (U : Submodule R M) (hU : U.FG) (hI : I ≤ Ideal.jacobson ⊥) (h : U ≤ I • U) : U = ⊥ := by
  exact Submodule.eq_bot_of_le_smul_of_le_jacobson_bot I U hU h hI

-- manifest card: commalg_modules_v2_nakayama_local_finite_module
example {R : Type*} [CommRing R] [IsLocalRing R] {M : Type*} [AddCommGroup M] [Module R M] [Module.Finite R M] (h : IsLocalRing.maximalIdeal R • (⊤ : Submodule R M) = ⊤) : (⊤ : Submodule R M) = ⊥ := by
  exact Submodule.eq_bot_of_le_smul_of_le_jacobson_bot _ _ Module.Finite.fg_top h.ge (IsLocalRing.maximalIdeal_le_jacobson ⊥)

-- manifest card: commalg_modules_v2_nakayama_local_generators
example {R : Type*} [CommRing R] [IsLocalRing R] {M : Type*} [AddCommGroup M] [Module R M] (U : Submodule R M) [Module.Finite R M] (h : U ⊔ IsLocalRing.maximalIdeal R • (⊤ : Submodule R M) = ⊤) : U = ⊤ := by
  apply top_unique
  exact Submodule.le_of_le_smul_of_le_jacobson_bot Module.Finite.fg_top (IsLocalRing.maximalIdeal_le_jacobson ⊥) h.ge

-- manifest card: commalg_modules_v2_fg_submodule_sum
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] (U V : Submodule R M) (hU : U.FG) (hV : V.FG) : (U ⊔ V).FG := by
  exact hU.sup hV

-- manifest card: commalg_modules_v2_finite_tensor_product
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] {N : Type*} [AddCommGroup N] [Module R N] [Module.Finite R M] [Module.Finite R N] : Module.Finite R (TensorProduct R M N) := by
  infer_instance

-- manifest card: commalg_modules_v2_tensor_preserves_surjections
example {R : Type*} [CommRing R] {X : Type*} [AddCommGroup X] [Module R X] {M : Type*} [AddCommGroup M] [Module R M] {N : Type*} [AddCommGroup N] [Module R N] (f : M →ₗ[R] N) (hf : Function.Surjective f) : Function.Surjective (f.lTensor X) := by
  exact LinearMap.lTensor_surjective X hf

-- manifest card: commalg_modules_v2_flat_tensor_preserves_injections
example {R : Type*} [CommRing R] {X : Type*} [AddCommGroup X] [Module R X] {M : Type*} [AddCommGroup M] [Module R M] {N : Type*} [AddCommGroup N] [Module R N] [Module.Flat R X] (f : M →ₗ[R] N) (hf : Function.Injective f) : Function.Injective (f.lTensor X) := by
  exact Module.Flat.lTensor_preserves_injective_linearMap f hf

-- manifest card: commalg_modules_v2_flat_tensor_preserves_exactness
example {R : Type*} [CommRing R] {X : Type*} [AddCommGroup X] [Module R X] {M : Type*} [AddCommGroup M] [Module R M] {N : Type*} [AddCommGroup N] [Module R N] {L : Type*} [AddCommGroup L] [Module R L] [Module.Flat R X] (f : M →ₗ[R] N) (g : N →ₗ[R] L) (h : Function.Exact f g) : Function.Exact (f.lTensor X) (g.lTensor X) := by
  exact Module.Flat.lTensor_exact X h

-- manifest card: commalg_modules_v2_finite_exact_extension
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] {N : Type*} [AddCommGroup N] [Module R N] {L : Type*} [AddCommGroup L] [Module R L] [Module.Finite R M] [Module.Finite R L] (f : M →ₗ[R] N) (g : N →ₗ[R] L) (h : Function.Exact f g) (hg : Function.Surjective g) : Module.Finite R N := by
  exact Module.Finite.of_exact h hg

-- manifest card: commalg_modules_v2_fg_image
example {R : Type*} [CommRing R] {M : Type*} [AddCommGroup M] [Module R M] {N : Type*} [AddCommGroup N] [Module R N] (U : Submodule R M) (f : M →ₗ[R] N) (hU : U.FG) : (U.map f).FG := by
  exact hU.map f
