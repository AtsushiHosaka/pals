import Mathlib

-- manifest card: la_v2_rank_nullity
example {K V W : Type*} [Field K] [AddCommGroup V] [Module K V] [FiniteDimensional K V] [AddCommGroup W] [Module K W] [FiniteDimensional K W] (f : V →ₗ[K] W) : Module.finrank K (LinearMap.range f) + Module.finrank K (LinearMap.ker f) = Module.finrank K V := by
  exact f.finrank_range_add_finrank_ker

-- manifest card: la_v2_rank_domain_bound
example {K V W : Type*} [Field K] [AddCommGroup V] [Module K V] [FiniteDimensional K V] [AddCommGroup W] [Module K W] [FiniteDimensional K W] (f : V →ₗ[K] W) : Module.finrank K (LinearMap.range f) ≤ Module.finrank K V := by
  exact f.finrank_range_le

-- manifest card: la_v2_rank_codomain_bound
example {K V W : Type*} [Field K] [AddCommGroup V] [Module K V] [FiniteDimensional K V] [AddCommGroup W] [Module K W] [FiniteDimensional K W] (f : V →ₗ[K] W) : Module.finrank K (LinearMap.range f) ≤ Module.finrank K W := by
  exact (LinearMap.range f).finrank_le

-- manifest card: la_v2_nullity_injectivity
example {K V W : Type*} [Field K] [AddCommGroup V] [Module K V] [FiniteDimensional K V] [AddCommGroup W] [Module K W] [FiniteDimensional K W] (f : V →ₗ[K] W) : (Module.finrank K (LinearMap.ker f) = 0 → Function.Injective f) ∧ (Function.Injective f → Module.finrank K (LinearMap.ker f) = 0) := by
  have h : Module.finrank K (LinearMap.ker f) = 0 ↔ Function.Injective f := by
    rw [Submodule.finrank_eq_zero, LinearMap.ker_eq_bot]
  exact ⟨h.mp, h.mpr⟩

-- manifest card: la_v2_full_rank_surjectivity
example {K V W : Type*} [Field K] [AddCommGroup V] [Module K V] [FiniteDimensional K V] [AddCommGroup W] [Module K W] [FiniteDimensional K W] (f : V →ₗ[K] W) : (Module.finrank K (LinearMap.range f) = Module.finrank K W → Function.Surjective f) ∧ (Function.Surjective f → Module.finrank K (LinearMap.range f) = Module.finrank K W) := by
  constructor
  · intro h
    exact LinearMap.range_eq_top.mp (Submodule.eq_top_of_finrank_eq h)
  · intro h
    rw [LinearMap.range_eq_top.mpr h]
    exact finrank_top K W

-- manifest card: la_v2_injective_dimension_bound
example {K V W : Type*} [Field K] [AddCommGroup V] [Module K V] [FiniteDimensional K V] [AddCommGroup W] [Module K W] [FiniteDimensional K W] (f : V →ₗ[K] W) : Function.Injective f → Module.finrank K V ≤ Module.finrank K W := by
  exact LinearMap.finrank_le_finrank_of_injective

-- manifest card: la_v2_surjective_dimension_bound
example {K V W : Type*} [Field K] [AddCommGroup V] [Module K V] [FiniteDimensional K V] [AddCommGroup W] [Module K W] [FiniteDimensional K W] (f : V →ₗ[K] W) : Function.Surjective f → Module.finrank K W ≤ Module.finrank K V := by
  exact LinearMap.finrank_le_finrank_of_surjective

-- manifest card: la_v2_equal_dimension_injective_surjective
example {K V W : Type*} [Field K] [AddCommGroup V] [Module K V] [FiniteDimensional K V] [AddCommGroup W] [Module K W] [FiniteDimensional K W] (f : V →ₗ[K] W) : Module.finrank K V = Module.finrank K W → (Function.Injective f → Function.Surjective f) ∧ (Function.Surjective f → Function.Injective f) := by
  intro h
  exact ⟨(LinearMap.injective_iff_surjective_of_finrank_eq_finrank h).mp, (LinearMap.injective_iff_surjective_of_finrank_eq_finrank h).mpr⟩

-- manifest card: la_v2_subspace_dimension_bound
example {K V : Type*} [Field K] [AddCommGroup V] [Module K V] [FiniteDimensional K V] (S : Submodule K V) : Module.finrank K S ≤ Module.finrank K V := by
  exact S.finrank_le

-- manifest card: la_v2_zero_dimensional_subspace
example {K V : Type*} [Field K] [AddCommGroup V] [Module K V] [FiniteDimensional K V] (S : Submodule K V) : (Module.finrank K S = 0 → S = ⊥) ∧ (S = ⊥ → Module.finrank K S = 0) := by
  exact ⟨Submodule.finrank_eq_zero.mp, Submodule.finrank_eq_zero.mpr⟩

-- manifest card: la_v2_full_dimensional_subspace
example {K V : Type*} [Field K] [AddCommGroup V] [Module K V] [FiniteDimensional K V] (S : Submodule K V) : Module.finrank K S = Module.finrank K V → S = ⊤ := by
  exact Submodule.eq_top_of_finrank_eq

-- manifest card: la_v2_grassmann_dimension_formula
example {K V : Type*} [Field K] [AddCommGroup V] [Module K V] [FiniteDimensional K V] (S : Submodule K V) (T : Submodule K V) : Module.finrank K (S ⊔ T : Submodule K V) + Module.finrank K (S ⊓ T : Submodule K V) = Module.finrank K S + Module.finrank K T := by
  exact Submodule.finrank_sup_add_finrank_inf_eq S T

-- manifest card: la_v2_contained_equal_dimension
example {K V : Type*} [Field K] [AddCommGroup V] [Module K V] [FiniteDimensional K V] (S : Submodule K V) (T : Submodule K V) : S ≤ T ∧ Module.finrank K S = Module.finrank K T → S = T := by
  rintro ⟨hST, hd⟩
  exact Submodule.eq_of_le_of_finrank_eq hST hd

-- manifest card: la_v2_strict_subspace_dimension
example {K V : Type*} [Field K] [AddCommGroup V] [Module K V] [FiniteDimensional K V] (S : Submodule K V) (T : Submodule K V) : S < T → Module.finrank K S < Module.finrank K T := by
  exact Submodule.finrank_lt_finrank_of_lt

-- manifest card: la_v2_complementary_subspace_dimension
example {K V : Type*} [Field K] [AddCommGroup V] [Module K V] [FiniteDimensional K V] (S : Submodule K V) (T : Submodule K V) : (S ⊔ T = ⊤) ∧ (S ⊓ T = ⊥) → Module.finrank K S + Module.finrank K T = Module.finrank K V := by
  rintro ⟨hs, hi⟩
  have h := Submodule.finrank_sup_add_finrank_inf_eq S T
  rw [hs, hi, finrank_top, finrank_bot, add_zero] at h
  exact h.symm

-- manifest card: la_v2_basis_cardinality
example {K V : Type*} [Field K] [AddCommGroup V] [Module K V] [FiniteDimensional K V] (n : ℕ) (b : Module.Basis (Fin n) K V) : Module.finrank K V = n := by
  simpa using Module.finrank_eq_card_basis b

-- manifest card: la_v2_independent_family_cardinality
example {K V : Type*} [Field K] [AddCommGroup V] [Module K V] [FiniteDimensional K V] (n : ℕ) (v : Fin n → V) : LinearIndependent K v → n ≤ Module.finrank K V := by
  intro h
  simpa using h.fintype_card_le_finrank

-- manifest card: la_v2_spanning_family_cardinality
example {K V : Type*} [Field K] [AddCommGroup V] [Module K V] [FiniteDimensional K V] (n : ℕ) (v : Fin n → V) : Submodule.span K (Set.range v) = ⊤ → Module.finrank K V ≤ n := by
  intro h
  have bound := finrank_range_le_card v (R := K)
  change Module.finrank K (Submodule.span K (Set.range v)) ≤ Fintype.card (Fin n) at bound
  rw [h, finrank_top] at bound
  simpa using bound

-- manifest card: la_v2_full_size_independent_spans
example {K V : Type*} [Field K] [AddCommGroup V] [Module K V] [FiniteDimensional K V] (n : ℕ) (v : Fin n → V) : LinearIndependent K v ∧ n = Module.finrank K V → Submodule.span K (Set.range v) = ⊤ := by
  rintro ⟨h, hn⟩
  exact h.span_eq_top_of_card_eq_finrank' (by simpa using hn)

-- manifest card: la_v2_full_size_spanning_independent
example {K V : Type*} [Field K] [AddCommGroup V] [Module K V] [FiniteDimensional K V] (n : ℕ) (v : Fin n → V) : Submodule.span K (Set.range v) = ⊤ ∧ n = Module.finrank K V → LinearIndependent K v := by
  rintro ⟨h, hn⟩
  exact linearIndependent_of_top_le_span_of_card_eq_finrank h.ge (by simpa using hn)

-- manifest card: la_v2_eigenspace_as_kernel
example {K V : Type*} [Field K] [AddCommGroup V] [Module K V] [FiniteDimensional K V] (f : V →ₗ[K] V) (a : K) : Module.End.eigenspace f a = LinearMap.ker (f - a • LinearMap.id) := by
  ext x
  simp [LinearMap.mem_ker, sub_eq_zero]

-- manifest card: la_v2_distinct_eigenspaces_intersection
example {K V : Type*} [Field K] [AddCommGroup V] [Module K V] [FiniteDimensional K V] (f : V →ₗ[K] V) (a : K) (b : K) : a ≠ b → Module.End.eigenspace f a ⊓ Module.End.eigenspace f b = ⊥ := by
  intro hab
  apply bot_unique
  intro x hx
  have ha := Module.End.mem_eigenspace_iff.mp hx.1
  have hb := Module.End.mem_eigenspace_iff.mp hx.2
  change x = 0
  have hh : (a - b) • x = 0 := by rw [sub_smul, ← ha, ← hb, sub_self]
  exact (smul_eq_zero.mp hh).resolve_left (sub_ne_zero.mpr hab)

-- manifest card: la_v2_distinct_eigenvectors_independent
example {K V : Type*} [Field K] [AddCommGroup V] [Module K V] [FiniteDimensional K V] (n : ℕ) (f : V →ₗ[K] V) (a : Fin n → K) (v : Fin n → V) : Function.Injective a ∧ (∀ i, Module.End.HasEigenvector f (a i) (v i)) → LinearIndependent K v := by
  rintro ⟨ha, hv⟩
  exact Module.End.eigenvectors_linearIndependent' f a ha v hv

-- manifest card: la_v2_distinct_full_spectrum_eigenbasis
example {K V : Type*} [Field K] [AddCommGroup V] [Module K V] [FiniteDimensional K V] (n : ℕ) (f : V →ₗ[K] V) (a : Fin n → K) (v : Fin n → V) : (Function.Injective a ∧ (∀ i, Module.End.HasEigenvector f (a i) (v i))) ∧ n = Module.finrank K V → ∃ b : Module.Basis (Fin n) K V, ∀ i, Module.End.HasEigenvector f (a i) (b i) := by
  rintro ⟨⟨ha, hv⟩, hn⟩
  have hi := Module.End.eigenvectors_linearIndependent' f a ha v hv
  have hs := hi.span_eq_top_of_card_eq_finrank' (by simpa using hn)
  refine ⟨Module.Basis.mk hi hs.ge, ?_⟩
  simpa using hv

-- manifest card: la_v2_determinant_zero_kernel
example {K V : Type*} [Field K] [AddCommGroup V] [Module K V] [FiniteDimensional K V] (f : V →ₗ[K] V) : (LinearMap.det f = 0 → LinearMap.ker f ≠ ⊥) ∧ (LinearMap.ker f ≠ ⊥ → LinearMap.det f = 0) := by
  exact ⟨LinearMap.det_eq_zero_iff_ker_ne_bot.mp, LinearMap.det_eq_zero_iff_ker_ne_bot.mpr⟩

-- manifest card: la_v2_determinant_composition
example {K V : Type*} [Field K] [AddCommGroup V] [Module K V] [FiniteDimensional K V] (f : V →ₗ[K] V) (g : V →ₗ[K] V) : LinearMap.det (g.comp f) = LinearMap.det g * LinearMap.det f := by
  exact LinearMap.det_comp g f

-- manifest card: la_v2_determinant_scalar_degree
example {K V : Type*} [Field K] [AddCommGroup V] [Module K V] [FiniteDimensional K V] (f : V →ₗ[K] V) (a : K) : LinearMap.det (a • f) = a ^ Module.finrank K V * LinearMap.det f := by
  exact LinearMap.det_smul a f
