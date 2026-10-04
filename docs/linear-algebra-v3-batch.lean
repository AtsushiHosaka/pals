import Mathlib

-- manifest card: la_v3_inner_self
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] (x : V) : inner ℝ x x = ‖x‖ ^ 2 := by
  exact real_inner_self_eq_norm_sq x

-- manifest card: la_v3_cauchy_schwarz
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] (x y : V) : |inner ℝ x y| ≤ ‖x‖ * ‖y‖ := by
  exact abs_real_inner_le_norm x y

-- manifest card: la_v3_pythagorean_iff
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] (x y : V) : ‖x + y‖ ^ 2 = ‖x‖ ^ 2 + ‖y‖ ^ 2 ↔ inner ℝ x y = 0 := by
  simpa only [pow_two] using norm_add_sq_eq_norm_sq_add_norm_sq_iff_real_inner_eq_zero x y

-- manifest card: la_v3_parallelogram
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] (x y : V) : ‖x + y‖ ^ 2 + ‖x - y‖ ^ 2 = 2 * (‖x‖ ^ 2 + ‖y‖ ^ 2) := by
  exact parallelogram_law_with_norm ℝ x y

-- manifest card: la_v3_polarization
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] (x y : V) : 4 * inner ℝ x y = ‖x + y‖ ^ 2 - ‖x - y‖ ^ 2 := by
  nlinarith [norm_add_sq_real x y, norm_sub_sq_real x y]

-- manifest card: la_v3_orthogonal_independent
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] {n : ℕ} (v : Fin n → V) (hz : ∀ i, v i ≠ 0) (ho : Pairwise (fun i j => inner ℝ (v i) (v j) = 0)) : LinearIndependent ℝ v := by
  exact linearIndependent_of_ne_zero_of_inner_eq_zero hz ho

-- manifest card: la_v3_bessel
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] {n : ℕ} (v : Fin n → V) (hv : Orthonormal ℝ v) (x : V) : ∑ i, (inner ℝ (v i) x) ^ 2 ≤ ‖x‖ ^ 2 := by
  simpa using hv.sum_inner_products_le (s := Finset.univ) x

-- manifest card: la_v3_complement_antitone
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] (S T : Submodule ℝ V) (h : S ≤ T) : Tᗮ ≤ Sᗮ := by
  exact Submodule.orthogonal_le h

-- manifest card: la_v3_double_complement
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] (S : Submodule ℝ V) : Sᗮᗮ = S := by
  exact S.orthogonal_orthogonal

-- manifest card: la_v3_complement_sum
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] (S T : Submodule ℝ V) : (S ⊔ T)ᗮ = Sᗮ ⊓ Tᗮ := by
  exact (Submodule.inf_orthogonal S T).symm

-- manifest card: la_v3_complement_dimension
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] (S : Submodule ℝ V) : Module.finrank ℝ S + Module.finrank ℝ Sᗮ = Module.finrank ℝ V := by
  exact S.finrank_add_finrank_orthogonal

-- manifest card: la_v3_orthogonal_direct_sum
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] (S : Submodule ℝ V) : S ⊔ Sᗮ = ⊤ ∧ S ⊓ Sᗮ = ⊥ := by
  exact ⟨S.sup_orthogonal_of_hasOrthogonalProjection, S.inf_orthogonal_eq_bot⟩

-- manifest card: la_v3_projection_decomposition
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] (S : Submodule ℝ V) (x : V) : S.starProjection x ∈ S ∧ x - S.starProjection x ∈ Sᗮ := by
  exact ⟨S.starProjection_apply_mem x, S.sub_starProjection_mem_orthogonal x⟩

-- manifest card: la_v3_projection_unique
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] (S : Submodule ℝ V) (x y : V) (hy : y ∈ S) (ho : x-y ∈ Sᗮ) : S.starProjection x = y := by
  exact S.eq_starProjection_of_mem_orthogonal hy ho

-- manifest card: la_v3_projection_fixed_iff
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] (S : Submodule ℝ V) (x : V) : S.starProjection x = x ↔ x ∈ S := by
  exact S.starProjection_eq_self_iff

-- manifest card: la_v3_projection_idempotent
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] (S : Submodule ℝ V) (x : V) : S.starProjection (S.starProjection x) = S.starProjection x := by
  exact S.starProjection_eq_self_iff.mpr (S.starProjection_apply_mem x)

-- manifest card: la_v3_projection_zero_iff
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] (S : Submodule ℝ V) (x : V) : S.starProjection x = 0 ↔ x ∈ Sᗮ := by
  change x ∈ S.starProjection.ker ↔ x ∈ Sᗮ
  rw [Submodule.ker_starProjection]

-- manifest card: la_v3_projection_contractive
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] (S : Submodule ℝ V) (x : V) : ‖S.starProjection x‖ ≤ ‖x‖ := by
  exact S.norm_starProjection_apply_le x

-- manifest card: la_v3_projection_complement
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] (S : Submodule ℝ V) (x : V) : Sᗮ.starProjection x = x - S.starProjection x := by
  exact S.starProjection_orthogonal_val x

-- manifest card: la_v3_projection_nested
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] (S T : Submodule ℝ V) (h : S ≤ T) (x : V) : S.starProjection (T.starProjection x) = S.starProjection x := by
  exact congrArg (fun q : V →L[ℝ] V => q x) (Submodule.starProjection_comp_starProjection_of_le h)

-- manifest card: la_v3_projection_symmetric
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] (S : Submodule ℝ V) (x y : V) : inner ℝ (S.starProjection x) y = inner ℝ x (S.starProjection y) := by
  exact S.inner_starProjection_left_eq_right x y

-- manifest card: la_v3_projection_pythagoras
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] (S : Submodule ℝ V) (x : V) : ‖x‖ ^ 2 = ‖S.starProjection x‖ ^ 2 + ‖Sᗮ.starProjection x‖ ^ 2 := by
  exact S.norm_sq_eq_add_norm_sq_starProjection x

-- manifest card: la_v3_projection_norm_equality
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] (S : Submodule ℝ V) (x : V) : x ∈ S ↔ ‖S.starProjection x‖ = ‖x‖ := by
  exact S.mem_iff_norm_starProjection x

-- manifest card: la_v3_projection_best_approximation
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] (S : Submodule ℝ V) (x y : V) (hy : y ∈ S) : ‖x - S.starProjection x‖ ≤ ‖x - y‖ := by
  have h := Sᗮ.norm_starProjection_apply_le (x-y)
  rw [map_sub, S.starProjection_orthogonal_apply_eq_zero hy, sub_zero, S.starProjection_orthogonal_val] at h
  exact h

-- manifest card: la_v3_gram_schmidt_orthogonal
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] {n : ℕ} (v : Fin n → V) : Pairwise (fun i j => inner ℝ (InnerProductSpace.gramSchmidt ℝ v i) (InnerProductSpace.gramSchmidt ℝ v j) = 0) := by
  exact InnerProductSpace.gramSchmidt_pairwise_orthogonal ℝ v

-- manifest card: la_v3_gram_schmidt_span
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] {n : ℕ} (v : Fin n → V) : Submodule.span ℝ (Set.range (InnerProductSpace.gramSchmidt ℝ v)) = Submodule.span ℝ (Set.range v) := by
  exact InnerProductSpace.span_gramSchmidt ℝ v

-- manifest card: la_v3_gram_schmidt_independent
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] {n : ℕ} (v : Fin n → V) (hv : LinearIndependent ℝ v) : LinearIndependent ℝ (InnerProductSpace.gramSchmidt ℝ v) := by
  exact InnerProductSpace.gramSchmidt_linearIndependent hv

-- manifest card: la_v3_gram_schmidt_normalization
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] {n : ℕ} (v : Fin n → V) (hv : LinearIndependent ℝ v) : Orthonormal ℝ (InnerProductSpace.gramSchmidtNormed ℝ v) := by
  exact InnerProductSpace.gramSchmidtNormed_orthonormal hv

-- manifest card: la_v3_normalized_span
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] {n : ℕ} (v : Fin n → V) : Submodule.span ℝ (Set.range (InnerProductSpace.gramSchmidtNormed ℝ v)) = Submodule.span ℝ (Set.range v) := by
  exact (InnerProductSpace.span_gramSchmidtNormed_range v).trans (InnerProductSpace.span_gramSchmidt ℝ v)

-- manifest card: la_v3_gram_schmidt_fixed
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] {n : ℕ} (v : Fin n → V) (hv : Pairwise (fun i j => inner ℝ (v i) (v j) = 0)) : InnerProductSpace.gramSchmidt ℝ v = v := by
  exact InnerProductSpace.gramSchmidt_of_orthogonal ℝ hv

-- manifest card: la_v3_onbasis_expansion
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] {n : ℕ} (b : OrthonormalBasis (Fin n) ℝ V) (x : V) : ∑ i, (inner ℝ (b i) x) • b i = x := by
  exact b.sum_repr' x

-- manifest card: la_v3_parseval
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] {n : ℕ} (b : OrthonormalBasis (Fin n) ℝ V) (x : V) : ∑ i, (inner ℝ (b i) x) ^ 2 = ‖x‖ ^ 2 := by
  exact b.sum_sq_inner_right x

-- manifest card: la_v3_onbasis_inner
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] {n : ℕ} (b : OrthonormalBasis (Fin n) ℝ V) (x y : V) : ∑ i, (inner ℝ (b i) x) * inner ℝ (b i) y = inner ℝ x y := by
  simpa only [real_inner_comm (b _) x] using b.sum_inner_mul_inner x y

-- manifest card: la_v3_onbasis_coordinates
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] {n : ℕ} (b : OrthonormalBasis (Fin n) ℝ V) (x : V) : (fun i => b.repr x i) = (fun i => inner ℝ (b i) x) := by
  funext i
  exact b.repr_apply_apply x i

-- manifest card: la_v3_orthonormal_transition_det
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] {n : ℕ} (b c : OrthonormalBasis (Fin n) ℝ V) : b.toBasis.det c = 1 ∨ b.toBasis.det c = -1 := by
  exact b.det_to_matrix_orthonormalBasis_real c

-- manifest card: la_v3_spectral_orthonormal_basis
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] (n : ℕ) (f : V →ₗ[ℝ] V) (hn : Module.finrank ℝ V = n) (hf : f.IsSymmetric) : ∃ b : OrthonormalBasis (Fin n) ℝ V, ∃ a : Fin n → ℝ, ∀ i, Module.End.HasEigenvector f (a i) (b i) := by
  refine ⟨hf.eigenvectorBasis hn, hf.eigenvalues hn, ?_⟩
  intro i
  exact hf.hasEigenvector_eigenvectorBasis hn i
