import Mathlib

-- Direct Mathlib certificates for the local CA-2 proposal.  They are not an
-- OpenMath-to-Lean translation claim and are never loaded into the generic DB.

-- manifest card: commalg_modules_le_sup_left
example {R M : Type*} [CommRing R] [AddCommGroup M] [Module R M] (I J : Submodule R M) : I ≤ I ⊔ J := by
  exact le_sup_left

-- manifest card: commalg_modules_le_sup_right
example {R M : Type*} [CommRing R] [AddCommGroup M] [Module R M] (I J : Submodule R M) : J ≤ I ⊔ J := by
  exact le_sup_right

-- manifest card: commalg_modules_inf_le_left
example {R M : Type*} [CommRing R] [AddCommGroup M] [Module R M] (I J : Submodule R M) : I ⊓ J ≤ I := by
  exact inf_le_left

-- manifest card: commalg_modules_inf_le_right
example {R M : Type*} [CommRing R] [AddCommGroup M] [Module R M] (I J : Submodule R M) : I ⊓ J ≤ J := by
  exact inf_le_right

-- manifest card: commalg_modules_bot_le
example {R M : Type*} [CommRing R] [AddCommGroup M] [Module R M] (I : Submodule R M) : ⊥ ≤ I := by
  exact bot_le

-- manifest card: commalg_modules_le_top
example {R M : Type*} [CommRing R] [AddCommGroup M] [Module R M] (I : Submodule R M) : I ≤ ⊤ := by
  exact le_top

-- manifest card: commalg_modules_sup_comm
example {R M : Type*} [CommRing R] [AddCommGroup M] [Module R M] (I J : Submodule R M) : I ⊔ J = J ⊔ I := by
  exact sup_comm I J

-- manifest card: commalg_modules_inf_comm
example {R M : Type*} [CommRing R] [AddCommGroup M] [Module R M] (I J : Submodule R M) : I ⊓ J = J ⊓ I := by
  exact inf_comm I J

-- manifest card: commalg_modules_inf_sup_absorb
example {R M : Type*} [CommRing R] [AddCommGroup M] [Module R M] (I J : Submodule R M) : I ⊓ (I ⊔ J) = I := by
  exact inf_sup_self

-- manifest card: commalg_modules_sup_inf_absorb
example {R M : Type*} [CommRing R] [AddCommGroup M] [Module R M] (I J : Submodule R M) : I ⊔ (I ⊓ J) = I := by
  exact sup_inf_self

-- manifest card: commalg_modules_kernel_identity
example {R M : Type*} [CommRing R] [AddCommGroup M] [Module R M] : LinearMap.ker (LinearMap.id : M →ₗ[R] M) = ⊥ := by
  exact LinearMap.ker_id

-- manifest card: commalg_modules_range_identity
example {R M : Type*} [CommRing R] [AddCommGroup M] [Module R M] : LinearMap.range (LinearMap.id : M →ₗ[R] M) = ⊤ := by
  exact LinearMap.range_id

-- manifest card: commalg_modules_kernel_zero
example {R M N : Type*} [CommRing R] [AddCommGroup M] [Module R M] [AddCommGroup N] [Module R N] : LinearMap.ker (0 : M →ₗ[R] N) = ⊤ := by
  exact LinearMap.ker_zero

-- manifest card: commalg_modules_range_zero
example {R M N : Type*} [CommRing R] [AddCommGroup M] [Module R M] [AddCommGroup N] [Module R N] : LinearMap.range (0 : M →ₗ[R] N) = ⊥ := by
  exact LinearMap.range_zero

-- manifest card: commalg_modules_comp_left_identity
example {R M N : Type*} [CommRing R] [AddCommGroup M] [Module R M] [AddCommGroup N] [Module R N] (f : M →ₗ[R] N) : (LinearMap.id : N →ₗ[R] N).comp f = f := by
  ext x
  rfl

-- manifest card: commalg_modules_comp_right_identity
example {R M N : Type*} [CommRing R] [AddCommGroup M] [Module R M] [AddCommGroup N] [Module R N] (f : M →ₗ[R] N) : f.comp (LinearMap.id : M →ₗ[R] M) = f := by
  ext x
  rfl

-- manifest card: commalg_modules_comp_associative
example {R M N P Q : Type*} [CommRing R] [AddCommGroup M] [Module R M] [AddCommGroup N] [Module R N] [AddCommGroup P] [Module R P] [AddCommGroup Q] [Module R Q] (f : M →ₗ[R] N) (g : N →ₗ[R] P) (h : P →ₗ[R] Q) : (h.comp g).comp f = h.comp (g.comp f) := by
  rfl

-- manifest card: commalg_modules_range_comp_le
example {R M N P : Type*} [CommRing R] [AddCommGroup M] [Module R M] [AddCommGroup N] [Module R N] [AddCommGroup P] [Module R P] (f : M →ₗ[R] N) (g : N →ₗ[R] P) : LinearMap.range (g.comp f) ≤ LinearMap.range g := by
  rintro _ ⟨x, rfl⟩
  exact ⟨f x, rfl⟩

-- manifest card: commalg_modules_identity_injective
example {R M : Type*} [CommRing R] [AddCommGroup M] [Module R M] : Function.Injective (LinearMap.id : M →ₗ[R] M) := by
  intro x y h
  exact h

-- manifest card: commalg_modules_identity_surjective
example {R M : Type*} [CommRing R] [AddCommGroup M] [Module R M] : Function.Surjective (LinearMap.id : M →ₗ[R] M) := by
  intro x
  exact ⟨x, rfl⟩

-- manifest card: commalg_modules_exact_zero_id
example {R M : Type*} [CommRing R] [AddCommGroup M] [Module R M] : LinearMap.range (0 : M →ₗ[R] M) = LinearMap.ker (LinearMap.id : M →ₗ[R] M) := by
  simp

-- manifest card: commalg_modules_exact_id_zero
example {R M : Type*} [CommRing R] [AddCommGroup M] [Module R M] : LinearMap.range (LinearMap.id : M →ₗ[R] M) = LinearMap.ker (0 : M →ₗ[R] M) := by
  simp

-- manifest card: commalg_modules_comp_zero_left
example {R M N P : Type*} [CommRing R] [AddCommGroup M] [Module R M] [AddCommGroup N] [Module R N] [AddCommGroup P] [Module R P] (g : N →ₗ[R] P) : g.comp (0 : M →ₗ[R] N) = 0 := by
  ext x
  simp

-- manifest card: commalg_modules_comp_zero_right
example {R M N P : Type*} [CommRing R] [AddCommGroup M] [Module R M] [AddCommGroup N] [Module R N] [AddCommGroup P] [Module R P] (f : M →ₗ[R] N) : (0 : N →ₗ[R] P).comp f = 0 := by
  ext x
  simp
