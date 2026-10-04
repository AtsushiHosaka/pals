import Mathlib

-- manifest card: commalg_reuse_20260930_radical_product
example {R : Type*} [CommRing R] (I J : Ideal R) : (I * J).radical = I.radical ⊓ J.radical := by
  exact Ideal.radical_mul I J

-- manifest card: commalg_reuse_20260930_radical_sum
example {R : Type*} [CommRing R] (I J : Ideal R) : (I + J).radical = (I.radical + J.radical).radical := by
  exact Ideal.radical_sup I J

-- manifest card: commalg_reuse_20260930_radical_closure_containment
example {R : Type*} [CommRing R] (I J : Ideal R) : I.radical ≤ J.radical ↔ I ≤ J.radical := by
  exact Ideal.radical_le_radical_iff

-- manifest card: commalg_reuse_20260930_radical_top_criterion
example {R : Type*} [CommRing R] (I : Ideal R) : I.radical = ⊤ ↔ I = ⊤ := by
  exact Ideal.radical_eq_top

-- manifest card: commalg_reuse_20260930_comaximal_product_intersection
example {R : Type*} [CommRing R] (I J : Ideal R) (h : I + J = ⊤) : I * J = I ⊓ J := by
  exact Ideal.mul_eq_inf_of_coprime h

-- manifest card: commalg_reuse_20260930_comaximal_sum_product_reduction
example {R : Type*} [CommRing R] (I J K : Ideal R) (h : I + J = ⊤) : I + J * K = I + K := by
  exact Ideal.sup_mul_eq_of_coprime_left h

-- manifest card: commalg_reuse_20260930_prime_product_containment
example {R : Type*} [CommRing R] (I J P : Ideal R) (hP : P.IsPrime) : I * J ≤ P ↔ I ≤ P ∨ J ≤ P := by
  exact hP.mul_le

-- manifest card: commalg_reuse_20260930_prime_intersection_containment
example {R : Type*} [CommRing R] (I J P : Ideal R) (hP : P.IsPrime) : I ⊓ J ≤ P ↔ I ≤ P ∨ J ≤ P := by
  exact hP.inf_le

-- manifest card: commalg_reuse_20260930_distinct_maximal_comaximal
example {R : Type*} [CommRing R] (I J : Ideal R) (hI : I.IsMaximal) (hJ : J.IsMaximal) (hne : I ≠ J) : I + J = ⊤ := by
  exact hI.coprime_of_ne hJ hne

-- manifest card: commalg_reuse_20260930_maximal_above_proper
example {R : Type*} [CommRing R] (I : Ideal R) (hI : I ≠ ⊤) : ∃ P : Ideal R, P.IsMaximal ∧ I ≤ P := by
  exact Ideal.exists_le_maximal I hI

-- manifest card: commalg_reuse_20260930_radical_via_all_containing_primes
example {R : Type*} [CommRing R] (I J : Ideal R) : J ≤ I.radical ↔ ∀ P : Ideal R, I ≤ P ∧ P.IsPrime → J ≤ P := by
  rw [Ideal.radical_eq_sInf I]
  exact le_sInf_iff

-- manifest card: commalg_reuse_20260930_comaximal_radicals_criterion
example {R : Type*} [CommRing R] (I J : Ideal R) : I.radical + J.radical = ⊤ ↔ I + J = ⊤ := by
  change I.radical ⊔ J.radical = ⊤ ↔ I ⊔ J = ⊤
  rw [← Ideal.radical_eq_top (I := I ⊔ J), Ideal.radical_sup I J, Ideal.radical_eq_top]

-- manifest card: commalg_reuse_20260930_ideal_modular_law
example {R : Type*} [CommRing R] (I J K : Ideal R) (h : I ≤ K) : (I + J) ⊓ K = I + (J ⊓ K) := by
  exact sup_inf_assoc_of_le J h

-- manifest card: commalg_reuse_20260930_ideal_product_distributes_sum
example {R : Type*} [CommRing R] (I J K : Ideal R) : I * (J + K) = I * J + I * K := by
  exact mul_add I J K

-- manifest card: commalg_reuse_20260930_comaximal_no_common_prime
example {R : Type*} [CommRing R] (I J : Ideal R) : I + J = ⊤ ↔ ∀ P : Ideal R, I ≤ P ∧ J ≤ P → ¬ P.IsPrime := by
  constructor
  · intro h P hle hp
    apply hp.ne_top
    exact top_unique (h ▸ sup_le hle.1 hle.2)
  · intro h
    exact (Ideal.coprime_of_no_prime_ge (fun P hi hj => h P ⟨hi, hj⟩)).sup_eq

-- manifest card: commalg_reuse_20260930_ideal_product_top_criterion
example {R : Type*} [CommRing R] (I J : Ideal R) : I * J = ⊤ ↔ I = ⊤ ∧ J = ⊤ := by
  constructor
  · intro h
    exact ⟨top_unique (h ▸ Ideal.mul_le_right), top_unique (h ▸ Ideal.mul_le_left)⟩
  · rintro ⟨rfl, rfl⟩
    simp
