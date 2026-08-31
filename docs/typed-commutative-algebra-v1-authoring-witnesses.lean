import Mathlib

-- These are direct Mathlib certificates for the sealed local proposal only.
-- They are not an OpenMath-to-Lean translation claim and are never loaded into
-- the generic Draft database, a seed, an embedding index, or a PFI package.

-- manifest card: commalg_ideal_le_sum_left
example {R : Type*} [CommRing R] (I J : Ideal R) : I ≤ I + J := by
  exact le_sup_left

-- manifest card: commalg_ideal_le_sum_right
example {R : Type*} [CommRing R] (I J : Ideal R) : J ≤ I + J := by
  exact le_sup_right

-- manifest card: commalg_ideal_product_le_left
example {R : Type*} [CommRing R] (I J : Ideal R) : I * J ≤ I := by
  exact Ideal.mul_le_right (I := I) (J := J)

-- manifest card: commalg_ideal_product_le_right
example {R : Type*} [CommRing R] (I J : Ideal R) : I * J ≤ J := by
  exact Ideal.mul_le_left (I := I) (J := J)

-- manifest card: commalg_ideal_product_le_inf
example {R : Type*} [CommRing R] (I J : Ideal R) : I * J ≤ I ⊓ J := by
  exact le_inf (Ideal.mul_le_right (I := I) (J := J)) (Ideal.mul_le_left (I := I) (J := J))

-- manifest card: commalg_ideal_le_radical
example {R : Type*} [CommRing R] (I : Ideal R) : I ≤ I.radical := by
  exact Ideal.le_radical

-- manifest card: commalg_ideal_radical_idempotent
example {R : Type*} [CommRing R] (I : Ideal R) : I.radical.radical = I.radical := by
  exact Ideal.radical_idem I

-- manifest card: commalg_ideal_radical_mono
example {R : Type*} [CommRing R] (I J : Ideal R) (h : I ≤ J) : I.radical ≤ J.radical := by
  exact Ideal.radical_mono h

-- manifest card: commalg_prime_ideal_is_radical
example {R : Type*} [CommRing R] (P : Ideal R) (h : P.IsPrime) : P.radical = P := by
  exact h.radical

-- manifest card: commalg_maximal_ideal_is_prime
example {R : Type*} [CommRing R] (M : Ideal R) (h : M.IsMaximal) : M.IsPrime := by
  exact h.isPrime

-- manifest card: commalg_ideal_inclusion_transitive
example {R : Type*} [CommRing R] (I J K : Ideal R) (hIJ : I ≤ J) (hJK : J ≤ K) : I ≤ K := by
  exact hIJ.trans hJK

-- manifest card: commalg_ideal_sum_mono_left
example {R : Type*} [CommRing R] (I J K : Ideal R) (h : I ≤ J) : I + K ≤ J + K := by
  simpa [add_comm] using add_le_add_right h K

-- manifest card: commalg_ideal_product_mono_left
example {R : Type*} [CommRing R] (I J K : Ideal R) (h : I ≤ J) : I * K ≤ J * K := by
  exact mul_le_mul_left h K
