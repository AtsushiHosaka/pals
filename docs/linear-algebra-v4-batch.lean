import Mathlib

-- manifest card: la_v4_det_transpose
example {K : Type*} [Field K] {n : ℕ} (A : Matrix (Fin n) (Fin n) K) : A.transpose.det = A.det := by
  exact Matrix.det_transpose A

-- manifest card: la_v4_det_diagonal
example {K : Type*} [Field K] {n : ℕ} (d : Fin n → K) : (Matrix.diagonal d).det = ∏ i, d i := by
  exact Matrix.det_diagonal

-- manifest card: la_v4_det_upper_triangular
example {K : Type*} [Field K] {n : ℕ} (A : Matrix (Fin n) (Fin n) K) (h : A.BlockTriangular id) : A.det = ∏ i, A i i := by
  exact Matrix.det_of_upperTriangular h

-- manifest card: la_v4_adjugate_identity
example {K : Type*} [Field K] {n : ℕ} (A : Matrix (Fin n) (Fin n) K) : A * A.adjugate = A.det • (1 : Matrix (Fin n) (Fin n) K) ∧ A.adjugate * A = A.det • (1 : Matrix (Fin n) (Fin n) K) := by
  exact ⟨Matrix.mul_adjugate A, Matrix.adjugate_mul A⟩

-- manifest card: la_v4_adjugate_product
example {K : Type*} [Field K] {n : ℕ} (A B : Matrix (Fin n) (Fin n) K) : (A * B).adjugate = B.adjugate * A.adjugate := by
  exact Matrix.adjugate_mul_distrib A B

-- manifest card: la_v4_inverse_adjugate
example {K : Type*} [Field K] {n : ℕ} (A : Matrix (Fin n) (Fin n) K) : A⁻¹ = A.det⁻¹ • A.adjugate := by
  simpa only [Ring.inverse_eq_inv] using Matrix.inv_def A

-- manifest card: la_v4_inverse_product
example {K : Type*} [Field K] {n : ℕ} (A B : Matrix (Fin n) (Fin n) K) : (A * B)⁻¹ = B⁻¹ * A⁻¹ := by
  exact Matrix.mul_inv_rev A B

-- manifest card: la_v4_inverse_transpose
example {K : Type*} [Field K] {n : ℕ} (A : Matrix (Fin n) (Fin n) K) : A⁻¹.transpose = A.transpose⁻¹ := by
  exact Matrix.transpose_nonsing_inv A

-- manifest card: la_v4_inverse_determinant
example {K : Type*} [Field K] {n : ℕ} (A : Matrix (Fin n) (Fin n) K) : A⁻¹.det = A.det⁻¹ := by
  simpa only [Ring.inverse_eq_inv] using Matrix.det_nonsing_inv A

-- manifest card: la_v4_unit_iff_det_nonzero
example {K : Type*} [Field K] {n : ℕ} (A : Matrix (Fin n) (Fin n) K) : IsUnit A ↔ A.det ≠ 0 := by
  rw [Matrix.isUnit_iff_isUnit_det, isUnit_iff_ne_zero]

-- manifest card: la_v4_one_sided_inverse
example {K : Type*} [Field K] {n : ℕ} (A B : Matrix (Fin n) (Fin n) K) : A * B = 1 ↔ B * A = 1 := by
  exact mul_eq_one_comm

-- manifest card: la_v4_inverse_uniqueness
example {K : Type*} [Field K] {n : ℕ} (A B C : Matrix (Fin n) (Fin n) K) (h : A * B = 1) (g : C * A = 1) : B = C := by
  exact Matrix.right_inv_eq_left_inv h g

-- manifest card: la_v4_unique_linear_solution
example {K : Type*} [Field K] {n : ℕ} (A : Matrix (Fin n) (Fin n) K) (h : A.det ≠ 0) (y : Fin n → K) : ∃ x : Fin n → K, A.mulVec x = y ∧ ∀ z, A.mulVec z = y → z = x := by
  have hu : IsUnit A := (Matrix.isUnit_iff_isUnit_det A).2 (isUnit_iff_ne_zero.mpr h)
  have hs := Matrix.mulVec_surjective_iff_isUnit.mpr hu
  have hi := Matrix.mulVec_injective_iff_isUnit.mpr hu
  obtain ⟨x, hx⟩ := hs y
  exact ⟨x, hx, fun z hz => hi (hz.trans hx.symm)⟩

-- manifest card: la_v4_cramer
example {K : Type*} [Field K] {n : ℕ} (A : Matrix (Fin n) (Fin n) K) (y : Fin n → K) (h : A.det ≠ 0) : A.det • (A⁻¹.mulVec y) = A.cramer y := by
  exact Matrix.det_smul_inv_mulVec_eq_cramer A y (isUnit_iff_ne_zero.mpr h)

-- manifest card: la_v4_det_power
example {K : Type*} [Field K] {n : ℕ} (A : Matrix (Fin n) (Fin n) K) (k : ℕ) : (A ^ k).det = A.det ^ k := by
  exact Matrix.det_pow A k

-- manifest card: la_v4_rank_transpose
example {K : Type*} [Field K] {m n : ℕ} (A : Matrix (Fin m) (Fin n) K) : A.transpose.rank = A.rank := by
  exact Matrix.rank_transpose A

-- manifest card: la_v4_rank_product_bounds
example {K : Type*} [Field K] {m n p : ℕ} (A : Matrix (Fin m) (Fin n) K) (B : Matrix (Fin n) (Fin p) K) : (A * B).rank ≤ A.rank ∧ (A * B).rank ≤ B.rank := by
  exact ⟨Matrix.rank_mul_le_left A B, Matrix.rank_mul_le_right A B⟩

-- manifest card: la_v4_zero_product_rank_bound
example {K : Type*} [Field K] {m n p : ℕ} (A : Matrix (Fin m) (Fin n) K) (B : Matrix (Fin n) (Fin p) K) (h : A * B = 0) : A.rank + B.rank ≤ n := by
  simpa using Matrix.rank_add_rank_le_card_of_mul_eq_zero h

-- manifest card: la_v4_rank_invertible_multipliers
example {K : Type*} [Field K] {n : ℕ} (A B : Matrix (Fin n) (Fin n) K) (h : IsUnit B) : (A * B).rank = A.rank ∧ (B * A).rank = A.rank := by
  have hd := (Matrix.isUnit_iff_isUnit_det B).mp h
  exact ⟨Matrix.rank_mul_eq_left_of_isUnit_det B A hd, Matrix.rank_mul_eq_right_of_isUnit_det B A hd⟩

-- manifest card: la_v4_rank_diagonal
example {K : Type*} [Field K] {n : ℕ} (d : Fin n → K) : (Matrix.diagonal d).rank = Nat.card {i : Fin n // d i ≠ 0} := by
  classical
  simpa only [Nat.card_eq_fintype_card] using Matrix.rank_diagonal d

-- manifest card: la_v4_cayley_hamilton
example {K : Type*} [Field K] {n : ℕ} (A : Matrix (Fin n) (Fin n) K) : Polynomial.aeval A A.charpoly = 0 := by
  exact Matrix.aeval_self_charpoly A

-- manifest card: la_v4_charpoly_monic_degree
example {K : Type*} [Field K] {n : ℕ} (A : Matrix (Fin n) (Fin n) K) : A.charpoly.Monic ∧ A.charpoly.natDegree = n := by
  exact ⟨Matrix.charpoly_monic A, by simpa using Matrix.charpoly_natDegree_eq_dim A⟩

-- manifest card: la_v4_charpoly_scalar_evaluation
example {K : Type*} [Field K] {n : ℕ} (A : Matrix (Fin n) (Fin n) K) (t : K) : A.charpoly.eval t = (Matrix.scalar (Fin n) t - A).det := by
  exact Matrix.eval_charpoly A t

-- manifest card: la_v4_charpoly_transpose
example {K : Type*} [Field K] {n : ℕ} (A : Matrix (Fin n) (Fin n) K) : A.transpose.charpoly = A.charpoly := by
  exact Matrix.charpoly_transpose A

-- manifest card: la_v4_charpoly_product_swap
example {K : Type*} [Field K] {n : ℕ} (A B : Matrix (Fin n) (Fin n) K) : (A * B).charpoly = (B * A).charpoly := by
  exact Matrix.charpoly_mul_comm A B

-- manifest card: la_v4_charpoly_similarity
example {K : Type*} [Field K] {n : ℕ} (A B : Matrix (Fin n) (Fin n) K) (h : IsUnit B) : (B * A * B⁻¹).charpoly = A.charpoly := by
  obtain ⟨u, rfl⟩ := h
  simpa only [Matrix.coe_units_inv] using Matrix.charpoly_units_conj u A

-- manifest card: la_v4_charpoly_diagonal
example {K : Type*} [Field K] {n : ℕ} (d : Fin n → K) : (Matrix.diagonal d).charpoly = ∏ i, (Polynomial.X - Polynomial.C (d i)) := by
  exact Matrix.charpoly_diagonal d

-- manifest card: la_v4_charpoly_recovers_det_trace
example {K : Type*} [Field K] {n : ℕ} (A : Matrix (Fin n) (Fin n) K) : A.det = (-1 : K)^n * A.charpoly.coeff 0 ∧ A.trace = -A.charpoly.nextCoeff := by
  exact ⟨by simpa using Matrix.det_eq_sign_charpoly_coeff A, Matrix.trace_eq_neg_charpoly_nextCoeff A⟩

-- manifest card: la_v4_nilpotent_charpoly
example {K : Type*} [Field K] {n : ℕ} (A : Matrix (Fin n) (Fin n) K) (h : IsNilpotent A) : A.charpoly = Polynomial.X ^ n := by
  have hq := Matrix.isNilpotent_charpoly_sub_pow_of_isNilpotent h
  have he := isNilpotent_iff_eq_zero.mp hq
  simpa using sub_eq_zero.mp he

-- manifest card: la_v4_nilpotent_trace
example {K : Type*} [Field K] {n : ℕ} (A : Matrix (Fin n) (Fin n) K) (h : IsNilpotent A) : A.trace = 0 := by
  exact isNilpotent_iff_eq_zero.mp (Matrix.isNilpotent_trace_of_isNilpotent h)

-- manifest card: la_v4_trace_cyclic_rectangular
example {K : Type*} [Field K] {m n : ℕ} (A : Matrix (Fin m) (Fin n) K) (B : Matrix (Fin n) (Fin m) K) : (A * B).trace = (B * A).trace := by
  exact Matrix.trace_mul_comm A B

-- manifest card: la_v4_similarity_det_trace
example {K : Type*} [Field K] {n : ℕ} (A B : Matrix (Fin n) (Fin n) K) (h : IsUnit B) : (B * A * B⁻¹).det = A.det ∧ (B * A * B⁻¹).trace = A.trace := by
  exact ⟨Matrix.det_conj h A, Matrix.trace_conj h A⟩

-- manifest card: la_v4_transpose_product
example {K : Type*} [Field K] {m n p : ℕ} (A : Matrix (Fin m) (Fin n) K) (B : Matrix (Fin n) (Fin p) K) : (A * B).transpose = B.transpose * A.transpose := by
  exact Matrix.transpose_mul A B

-- manifest card: la_v4_matrix_action_composition
example {K : Type*} [Field K] {m n p : ℕ} (A : Matrix (Fin m) (Fin n) K) (B : Matrix (Fin n) (Fin p) K) (x : Fin p → K) : (A * B).mulVec x = A.mulVec (B.mulVec x) := by
  exact (Matrix.mulVec_mulVec x A B).symm
