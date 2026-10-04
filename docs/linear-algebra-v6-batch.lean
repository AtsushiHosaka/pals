import Mathlib

-- manifest card: la_v6_fredholm_solvability
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {W : Type*} [AddCommGroup W] [Module K W] [FiniteDimensional K W] (f : V →ₗ[K] W) (y : W) : (∃ x, f x = y) ↔ ∀ phi : W →ₗ[K] K, (∀ x, phi (f x) = 0) → phi y = 0 := by
  change y ∈ LinearMap.range f ↔ _
  rw [← Subspace.forall_mem_dualAnnihilator_apply_eq_zero_iff (LinearMap.range f) y]
  simp only [Submodule.mem_dualAnnihilator]
  constructor
  · intro h phi hp
    apply h phi
    rintro _ ⟨x,rfl⟩
    exact hp x
  · intro h phi hp
    apply h phi
    intro x
    exact hp (f x) ⟨x,rfl⟩

-- manifest card: la_v6_kernel_causes_nonunique_solutions
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {W : Type*} [AddCommGroup W] [Module K W] [FiniteDimensional K W] (f : V →ₗ[K] W) (u x : V) (hu : u ≠ 0) (hk : f u = 0) : x+u ≠ x ∧ f (x+u) = f x := by
  constructor
  · intro h; apply hu; exact add_left_cancel (show x+u=x+0 by simpa using h)
  · simp [map_add,hk]

-- manifest card: la_v6_left_inverse_detects_injective_action
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {n m : ℕ} (A : Matrix (Fin n) (Fin m) K) (B : Matrix (Fin m) (Fin n) K) (h : A*B=1) : Function.Injective B.mulVec := by
  intro x y hxy
  have he := congrArg A.mulVec hxy
  simpa only [Matrix.mulVec_mulVec, h, Matrix.one_mulVec] using he

-- manifest card: la_v6_matrix_units_noncommute
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {n : ℕ} (i j : Fin n) (t : K) (h : i ≠ j) (ht : t ≠ 0) : (Matrix.single i j t : Matrix (Fin n) (Fin n) K) * Matrix.single j i 1 ≠ Matrix.single j i 1 * Matrix.single i j t := by
  intro he
  have hh := congrArg (fun M : Matrix (Fin n) (Fin n) K => M i i) he
  apply ht
  simpa [Matrix.single_mul_single_same, h, h.symm] using hh

-- manifest card: la_v6_nilpotent_geometric_inverse
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {n k : ℕ} (N : Matrix (Fin n) (Fin n) K) (h : N^k=0) : (1-N)*(∑ j ∈ Finset.range k, N^j)=1 ∧ (∑ j ∈ Finset.range k, N^j)*(1-N)=1 := by
  constructor
  · simpa [h] using mul_neg_geom_sum N k
  · simpa [h] using geom_sum_mul_neg N k

-- manifest card: la_v6_subspace_sum_membership
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] (S T : Submodule K V) (x : V) : x ∈ S ⊔ T ↔ ∃ u ∈ S, ∃ y ∈ T, u+y=x := by
  exact Submodule.mem_sup

-- manifest card: la_v6_incomparable_union_not_closed
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] (S T : Submodule K V) (hST : ¬ S ≤ T) (hTS : ¬ T ≤ S) : ∃ u ∈ S, ∃ y ∈ T, u+y ∉ S ∧ u+y ∉ T := by
  obtain ⟨u,hu,huT⟩ := SetLike.not_le_iff_exists.mp hST
  obtain ⟨y,hy,hyS⟩ := SetLike.not_le_iff_exists.mp hTS
  refine ⟨u,hu,y,hy,?_,?_⟩
  · intro h; apply hyS; simpa using S.sub_mem h hu
  · intro h; apply huT; simpa using T.sub_mem h hy

-- manifest card: la_v6_injective_images_preserve_intersection
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {W : Type*} [AddCommGroup W] [Module K W] [FiniteDimensional K W] (f : V →ₗ[K] W) (hf : Function.Injective f) (S T : Submodule K V) : (S ⊓ T).map f = S.map f ⊓ T.map f := by
  exact Submodule.map_inf f hf

-- manifest card: la_v6_independence_zero_coefficients
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {n : ℕ} (v : Fin n → V) : LinearIndependent K v ↔ ∀ a : Fin n → K, (∑ i, a i • v i)=0 → a=0 := by
  rw [Fintype.linearIndependent_iff]
  simp only [funext_iff, Pi.zero_apply]

-- manifest card: la_v6_span_construct_coefficients
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {n : ℕ} (v : Fin n → V) (x : V) : x ∈ Submodule.span K (Set.range v) ↔ ∃ a : Fin n → K, ∑ i, a i • v i = x := by
  exact Submodule.mem_span_range_iff_exists_fun K

-- manifest card: la_v6_repeated_vector_dependence
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {n : ℕ} (v : Fin n → V) (i j : Fin n) (hij : i ≠ j) (hv : v i = v j) : ¬ LinearIndependent K v := by
  intro h
  exact hij (h.injective hv)

-- manifest card: la_v6_independence_under_restricted_injection
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {W : Type*} [AddCommGroup W] [Module K W] [FiniteDimensional K W] {n : ℕ} (v : Fin n → V) (f : V →ₗ[K] W) (h : Disjoint (Submodule.span K (Set.range v)) (LinearMap.ker f)) : LinearIndependent K (fun i => f (v i)) ↔ LinearIndependent K v := by
  exact f.linearIndependent_iff_of_disjoint h

-- manifest card: la_v6_basis_recognition
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {n : ℕ} (v : Fin n → V) : (∃ b : Module.Basis (Fin n) K V, (fun i => b i)=v) ↔ LinearIndependent K v ∧ Submodule.span K (Set.range v)=⊤ := by
  constructor
  · rintro ⟨b,rfl⟩; exact ⟨b.linearIndependent,b.span_eq⟩
  · rintro ⟨hi,hs⟩
    exact ⟨Module.Basis.mk hi hs.ge, by simp⟩

-- manifest card: la_v6_zeroing_basis_vector_loses_span
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {n : ℕ} (b : Module.Basis (Fin n) K V) (i : Fin n) : b i ∉ Submodule.span K (Set.range (Function.update (fun j => b j) i 0)) := by
  intro hm
  have hs : Submodule.span K (Set.range (Function.update (fun j => b j) i 0)) ≤ LinearMap.ker (b.coord i) := by
    apply Submodule.span_le.mpr
    rintro _ ⟨j,rfl⟩
    by_cases hj : j=i
    · subst j; simp
    · simp [LinearMap.mem_ker, Function.update_of_ne hj, Ne.symm hj]
  have hh := hs hm
  simp [LinearMap.mem_ker] at hh

-- manifest card: la_v6_nonzero_translation_not_linear
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] (u : V) (hu : u ≠ 0) : ¬ ∃ f : V →ₗ[K] V, ∀ x, f x = x+u := by
  rintro ⟨f,hf⟩
  apply hu
  simpa using (hf 0).symm

-- manifest card: la_v6_nonzero_maps_zero_composite
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {n : ℕ} (b : Module.Basis (Fin n) K V) (i j : Fin n) (hij : i ≠ j) : let p := (b.coord i).smulRight (b i); let q := (b.coord j).smulRight (b j); p ≠ 0 ∧ q ≠ 0 ∧ p.comp q = 0 := by
  dsimp only
  constructor
  · intro hp; have h := congrArg (fun f : V →ₗ[K] V => f (b i)) hp; exact b.ne_zero i (by simpa using h)
  constructor
  · intro hq; have h := congrArg (fun f : V →ₗ[K] V => f (b j)) hq; exact b.ne_zero j (by simpa using h)
  ext x
  simp [hij]

-- manifest card: la_v6_idempotent_kernel_range_decomposition
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] (f : V →ₗ[K] V) (hf : f.comp f=f) : IsCompl (LinearMap.range f) (LinearMap.ker f) := by
  have h : IsIdempotentElem f := hf
  exact LinearMap.IsIdempotentElem.isCompl h

-- manifest card: la_v6_rectangular_determinant_transfer
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {n m : ℕ} (A : Matrix (Fin n) (Fin m) K) (B : Matrix (Fin m) (Fin n) K) : (1+A*B).det=(1+B*A).det ∧ (IsUnit (1+A*B) ↔ IsUnit (1+B*A)) := by
  constructor
  · exact Matrix.det_one_add_mul_comm A B
  · rw [Matrix.isUnit_iff_isUnit_det, Matrix.isUnit_iff_isUnit_det, Matrix.det_one_add_mul_comm]
