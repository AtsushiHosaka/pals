import Mathlib

-- manifest card: la_v5_basis_reconstruction
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {n : ℕ} (b : Module.Basis (Fin n) K V) (x : V) : ∑ i, b.repr x i • b i = x := by
  exact b.sum_repr x

-- manifest card: la_v5_coordinates_of_combination
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {n : ℕ} (b : Module.Basis (Fin n) K V) (a : Fin n → K) : (fun i => b.repr (∑ j, a j • b j) i) = a := by
  exact b.repr_sum_self a

-- manifest card: la_v5_prescribed_basis_map
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {W : Type*} [AddCommGroup W] [Module K W] [FiniteDimensional K W] {n : ℕ} (b : Module.Basis (Fin n) K V) (y : Fin n → W) : ∃ f : V →ₗ[K] W, (fun i => f (b i)) = y ∧ ∀ g : V →ₗ[K] W, (fun i => g (b i)) = y → g = f := by
  refine ⟨b.constr K y, ?_, ?_⟩
  · funext i; exact b.constr_basis K y i
  · intro g hg; apply b.ext; intro i; simpa using congrFun hg i

-- manifest card: la_v5_constructed_map_formula
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {W : Type*} [AddCommGroup W] [Module K W] [FiniteDimensional K W] {n : ℕ} (b : Module.Basis (Fin n) K V) (y : Fin n → W) (x : V) : b.constr K y x = ∑ i, b.equivFun x i • y i := by
  exact b.constr_apply_fintype K y x

-- manifest card: la_v5_constructed_map_range
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {W : Type*} [AddCommGroup W] [Module K W] [FiniteDimensional K W] {n : ℕ} (b : Module.Basis (Fin n) K V) (y : Fin n → W) : LinearMap.range (b.constr K y) = Submodule.span K (Set.range y) := by
  exact b.constr_range K

-- manifest card: la_v5_constructed_map_injective
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {W : Type*} [AddCommGroup W] [Module K W] [FiniteDimensional K W] {n : ℕ} (b : Module.Basis (Fin n) K V) (y : Fin n → W) (hy : LinearIndependent K y) : Function.Injective (b.constr K y) := by
  exact b.injective_constr_of_linearIndependent hy

-- manifest card: la_v5_constructed_map_surjective
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {W : Type*} [AddCommGroup W] [Module K W] [FiniteDimensional K W] {n : ℕ} (b : Module.Basis (Fin n) K V) (y : Fin n → W) (hy : Submodule.span K (Set.range y) = ⊤) : Function.Surjective (b.constr K y) := by
  apply LinearMap.range_eq_top.mp
  rw [b.constr_range K, hy]

-- manifest card: la_v5_basis_determines_map
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {W : Type*} [AddCommGroup W] [Module K W] [FiniteDimensional K W] {n : ℕ} (b : Module.Basis (Fin n) K V) (f g : V →ₗ[K] W) (h : (fun i => f (b i)) = (fun i => g (b i))) : f = g := by
  apply b.ext
  intro i
  exact congrFun h i

-- manifest card: la_v5_matrix_action_coordinates
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {W : Type*} [AddCommGroup W] [Module K W] [FiniteDimensional K W] {n m : ℕ} (b : Module.Basis (Fin n) K V) (c : Module.Basis (Fin m) K W) (f : V →ₗ[K] W) (x : V) : (LinearMap.toMatrix b c f).mulVec (b.repr x) = c.repr (f x) := by
  exact LinearMap.toMatrix_mulVec_repr b c f x

-- manifest card: la_v5_matrix_representation_unique
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {W : Type*} [AddCommGroup W] [Module K W] [FiniteDimensional K W] {n m : ℕ} (b : Module.Basis (Fin n) K V) (c : Module.Basis (Fin m) K W) (A : Matrix (Fin m) (Fin n) K) : ∃ f : V →ₗ[K] W, LinearMap.toMatrix b c f = A ∧ ∀ g, LinearMap.toMatrix b c g = A → g = f := by
  refine ⟨Matrix.toLin b c A, LinearMap.toMatrix_toLin b c A, ?_⟩
  intro g hg
  apply (LinearMap.toMatrix b c).injective
  simpa using hg

-- manifest card: la_v5_matrix_of_composition
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {W : Type*} [AddCommGroup W] [Module K W] [FiniteDimensional K W] {U : Type*} [AddCommGroup U] [Module K U] [FiniteDimensional K U] {n m p : ℕ} (b : Module.Basis (Fin n) K V) (c : Module.Basis (Fin m) K W) (d : Module.Basis (Fin p) K U) (f : V →ₗ[K] W) (g : W →ₗ[K] U) : LinearMap.toMatrix b d (g.comp f) = LinearMap.toMatrix c d g * LinearMap.toMatrix b c f := by
  exact LinearMap.toMatrix_comp b c d g f

-- manifest card: la_v5_matrix_representation_linear
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {W : Type*} [AddCommGroup W] [Module K W] [FiniteDimensional K W] {n m : ℕ} (b : Module.Basis (Fin n) K V) (c : Module.Basis (Fin m) K W) (f g : V →ₗ[K] W) (z : K) : LinearMap.toMatrix b c (f+g) = LinearMap.toMatrix b c f + LinearMap.toMatrix b c g ∧ LinearMap.toMatrix b c (z • f) = z • LinearMap.toMatrix b c f := by
  exact ⟨(LinearMap.toMatrix b c).map_add f g, (LinearMap.toMatrix b c).map_smul z f⟩

-- manifest card: la_v5_basis_change_coordinates
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {n : ℕ} (b : Module.Basis (Fin n) K V) (c : Module.Basis (Fin n) K V) (x : V) : (c.toMatrix b).mulVec (b.repr x) = c.repr x := by
  exact Module.Basis.toMatrix_mulVec_repr b c x

-- manifest card: la_v5_basis_change_cocycle
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {n : ℕ} (b : Module.Basis (Fin n) K V) (c d : Module.Basis (Fin n) K V) : b.toMatrix c * c.toMatrix d = b.toMatrix d := by
  exact b.toMatrix_mul_toMatrix c d

-- manifest card: la_v5_basis_change_inverse
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {n : ℕ} (b : Module.Basis (Fin n) K V) (c : Module.Basis (Fin n) K V) : b.toMatrix c * c.toMatrix b = 1 ∧ c.toMatrix b * b.toMatrix c = 1 := by
  exact ⟨b.toMatrix_mul_toMatrix_flip c, c.toMatrix_mul_toMatrix_flip b⟩

-- manifest card: la_v5_two_sided_basis_change
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {W : Type*} [AddCommGroup W] [Module K W] [FiniteDimensional K W] {n m : ℕ} (b : Module.Basis (Fin n) K V) (c : Module.Basis (Fin m) K W) (b2 : Module.Basis (Fin n) K V) (c2 : Module.Basis (Fin m) K W) (f : V →ₗ[K] W) : c.toMatrix c2 * LinearMap.toMatrix b2 c2 f * b2.toMatrix b = LinearMap.toMatrix b c f := by
  exact basis_toMatrix_mul_linearMap_toMatrix_mul_basis_toMatrix b b2 c c2 f

-- manifest card: la_v5_eigenbasis_diagonal_matrix
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {n : ℕ} (b : Module.Basis (Fin n) K V) (f : V →ₗ[K] V) (a : Fin n → K) : (∀ i, f (b i) = a i • b i) ↔ LinearMap.toMatrix b b f = Matrix.diagonal a := by
  constructor
  · intro h; ext i j; by_cases hij : i = j <;> simp [LinearMap.toMatrix_apply, h, hij]
  · intro h i
    have hf : f = Matrix.toLin b b (Matrix.diagonal a) := by rw [← h, Matrix.toLin_toMatrix]
    rw [hf]
    exact (hasEigenvector_toLin_diagonal a i b).apply_eq_smul

-- manifest card: la_v5_dual_basis_expansion
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {n : ℕ} (b : Module.Basis (Fin n) K V) (phi : V →ₗ[K] K) : (∑ i, phi (b i) • b.coord i) = phi := by
  exact b.sum_dual_apply_smul_coord phi

-- manifest card: la_v5_dual_coordinates_independent
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {n : ℕ} (b : Module.Basis (Fin n) K V)  : LinearIndependent K b.coord := by
  exact b.linearIndependent_coord

-- manifest card: la_v5_subspace_has_complement
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] (S : Submodule K V) : ∃ T : Submodule K V, IsCompl S T := by
  exact S.exists_isCompl

-- manifest card: la_v5_injective_map_splits
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {W : Type*} [AddCommGroup W] [Module K W] [FiniteDimensional K W] (f : V →ₗ[K] W) (hf : Function.Injective f) : ∃ g : W →ₗ[K] V, g.comp f = LinearMap.id := by
  exact f.exists_leftInverse_of_injective (LinearMap.ker_eq_bot.mpr hf)

-- manifest card: la_v5_surjective_map_splits
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {W : Type*} [AddCommGroup W] [Module K W] [FiniteDimensional K W] (f : V →ₗ[K] W) (hf : Function.Surjective f) : ∃ g : W →ₗ[K] V, f.comp g = LinearMap.id := by
  exact f.exists_rightInverse_of_surjective (LinearMap.range_eq_top.mpr hf)

-- manifest card: la_v5_polynomial_on_eigenvector
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] (f : V →ₗ[K] V) (z : K) (x : V) (P : Polynomial K) (hx : Module.End.HasEigenvector f z x) : (Polynomial.aeval f P) x = P.eval z • x := by
  exact Module.End.aeval_apply_of_hasEigenvector hx

-- manifest card: la_v5_eigenvalue_charpoly
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] (f : V →ₗ[K] V) (z : K) : Module.End.HasEigenvalue f z ↔ (f.charpoly).IsRoot z := by
  exact Module.End.hasEigenvalue_iff_isRoot_charpoly f z

-- manifest card: la_v5_eigenvalue_minpoly
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] (f : V →ₗ[K] V) (z : K) : Module.End.HasEigenvalue f z ↔ (minpoly K f).IsRoot z := by
  exact Module.End.hasEigenvalue_iff_isRoot

-- manifest card: la_v5_minpoly_divides_charpoly
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] (f : V →ₗ[K] V) : minpoly K f ∣ f.charpoly := by
  exact LinearMap.minpoly_dvd_charpoly f

-- manifest card: la_v5_annihilator_minpoly_divisibility
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] (f : V →ₗ[K] V) (P : Polynomial K) : Polynomial.aeval f P = 0 ↔ minpoly K f ∣ P := by
  exact minpoly.dvd_iff.symm

-- manifest card: la_v5_commuting_preserves_eigenspace
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] (f g : V →ₗ[K] V) (z : K) (h : Commute f g) : (Module.End.eigenspace f z).map g ≤ Module.End.eigenspace f z := by
  rintro _ ⟨x, hx, rfl⟩
  change x ∈ Module.End.eigenspace f z at hx
  rw [Module.End.mem_eigenspace_iff] at hx ⊢
  have hh := congrArg (fun q : V →ₗ[K] V => q x) h.eq
  change f (g x) = g (f x) at hh
  rw [hh, hx, map_smul]

-- manifest card: la_v5_common_eigenbasis_commutes
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {n : ℕ} (b : Module.Basis (Fin n) K V) (f g : V →ₗ[K] V) (a z : Fin n → K) (hf : ∀ i, f (b i) = a i • b i) (hg : ∀ i, g (b i) = z i • b i) : Commute f g := by
  show f * g = g * f
  apply b.ext
  intro i
  simp [Module.End.mul_apply, hf, hg, smul_smul, mul_comm]

-- manifest card: la_v5_diagonal_operator_spectrum
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {n : ℕ} (b : Module.Basis (Fin n) K V) (a : Fin n → K) (z : K) : Module.End.HasEigenvalue (Matrix.toLin b b (Matrix.diagonal a)) z ↔ ∃ i, a i = z := by
  exact hasEigenvalue_toLin_diagonal_iff a b

-- manifest card: la_v5_diagonal_operator_eigenspaces_span
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {n : ℕ} (b : Module.Basis (Fin n) K V) (a : Fin n → K) : (⨆ z : K, Module.End.eigenspace (Matrix.toLin b b (Matrix.diagonal a)) z) = ⊤ := by
  exact Matrix.iSup_eigenspace_toLin_diagonal_eq_top a b

-- manifest card: la_v5_row_addition_preserves_determinant
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {n : ℕ} (A : Matrix (Fin n) (Fin n) K) (i j : Fin n) (t : K) (h : i ≠ j) : (A.updateRow i (A i + t • A j)).det = A.det := by
  exact Matrix.det_updateRow_add_smul_self A h t

-- manifest card: la_v5_row_scaling_determinant
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {n : ℕ} (A : Matrix (Fin n) (Fin n) K) (i : Fin n) (t : K) : (A.updateRow i (t • A i)).det = t * A.det := by
  simpa using Matrix.det_updateRow_smul A i t (A i)

-- manifest card: la_v5_row_addition_matrix_realization
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {n m : ℕ} (A : Matrix (Fin n) (Fin m) K) (i j : Fin n) (t : K) : Matrix.transvection i j t * A = A.updateRow i (A i + t • A j) := by
  ext r c
  by_cases hr : r = i
  · subst r; simp [Matrix.transvection_mul_apply_same]
  · simp [Matrix.transvection_mul_apply_of_ne i j r c hr, Matrix.updateRow_ne hr]

-- manifest card: la_v5_row_addition_inverse
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {n : ℕ} (i j : Fin n) (t : K) (h : i ≠ j) : Matrix.transvection i j t * Matrix.transvection i j (-t) = 1 ∧ Matrix.transvection i j (-t) * Matrix.transvection i j t = 1 := by
  constructor <;> simp [Matrix.transvection_mul_transvection_same i j h]

-- manifest card: la_v5_row_operation_preserves_system
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {n m : ℕ} (A : Matrix (Fin n) (Fin m) K) (i j : Fin n) (t : K) (h : i ≠ j) (x : Fin m → K) (y : Fin n → K) : (Matrix.transvection i j t * A).mulVec x = (Matrix.transvection i j t).mulVec y ↔ A.mulVec x = y := by
  have he : IsUnit (Matrix.transvection i j t) := (Matrix.isUnit_iff_isUnit_det _).mpr (by rw [Matrix.det_transvection_of_ne i j h]; exact isUnit_one)
  have hinj := Matrix.mulVec_injective_iff_isUnit.mpr he
  rw [← Matrix.mulVec_mulVec]
  exact hinj.eq_iff

-- manifest card: la_v5_nonzero_square_zero_family
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {n : ℕ} (i j : Fin n) (t : K) (h : i ≠ j) (ht : t ≠ 0) : (Matrix.single i j t : Matrix (Fin n) (Fin n) K) ≠ 0 ∧ Matrix.single i j t * Matrix.single i j t = 0 := by
  constructor
  · intro hz; apply ht; simpa using congrArg (fun M : Matrix (Fin n) (Fin n) K => M i j) hz
  · simp [Matrix.single_mul_single_of_ne, h.symm]

-- manifest card: la_v5_determinant_one_nonidentity_family
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] {n : ℕ} (i j : Fin n) (t : K) (h : i ≠ j) (ht : t ≠ 0) : (Matrix.transvection i j t).det = 1 ∧ Matrix.transvection i j t ≠ 1 := by
  constructor
  · exact Matrix.det_transvection_of_ne i j h t
  · intro hz; apply ht; simpa [Matrix.transvection, h] using congrArg (fun M : Matrix (Fin n) (Fin n) K => M i j) hz

-- manifest card: la_v5_square_zero_obstructs_eigenbasis
example {K : Type*} [Field K] {V : Type*} [AddCommGroup V] [Module K V] [FiniteDimensional K V] (f : V →ₗ[K] V) (hf : f ≠ 0) (hs : f.comp f = 0) {n : ℕ} (b : Module.Basis (Fin n) K V) (a : Fin n → K) : ¬ (∀ i, f (b i) = a i • b i) := by
  intro he
  apply hf
  apply b.ext
  intro i
  have hz := congrArg (fun q : V →ₗ[K] V => q (b i)) hs
  have heq : (a i * a i) • b i = 0 := by simpa [LinearMap.comp_apply, he, smul_smul] using hz
  have ha : a i = 0 := by
    have hp := (smul_eq_zero.mp heq).resolve_right (b.ne_zero i)
    exact mul_self_eq_zero.mp hp
  simp [he, ha]
