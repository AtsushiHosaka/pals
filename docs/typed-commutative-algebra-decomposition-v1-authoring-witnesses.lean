import Mathlib.RingTheory.Ideal.IsPrimary
import Mathlib.RingTheory.Ideal.MinimalPrime.Basic

-- This bundle is direct local Lean evidence for original CA-4 authoring cards.
-- `PrimaryIdeal(R)` and `PrimeIdeal(R)` in the OpenMath profile correspond to
-- an Ideal R paired with the explicit hypotheses below.

-- manifest card: commalg_decomp_ideal_le_radical
example {R : Type*} [CommRing R] (I : Ideal R) : I ≤ I.radical := by
  exact Ideal.le_radical

-- manifest card: commalg_decomp_radical_idempotent
example {R : Type*} [CommRing R] (I : Ideal R) : I.radical.radical = I.radical := by
  exact (Ideal.radical_isRadical I).radical

-- manifest card: commalg_decomp_radical_inf2
example {R : Type*} [CommRing R] (I J : Ideal R) :
    (I ⊓ J).radical = I.radical ⊓ J.radical := by
  exact Ideal.radical_inf I J

-- manifest card: commalg_decomp_radical_inf3
example {R : Type*} [CommRing R] (I J K : Ideal R) :
    (I ⊓ J ⊓ K).radical = I.radical ⊓ J.radical ⊓ K.radical := by
  rw [Ideal.radical_inf, Ideal.radical_inf]

-- manifest card: commalg_decomp_prime_is_primary
example {R : Type*} [CommRing R] (P : Ideal R) (hP : P.IsPrime) : P.IsPrimary := by
  exact hP.isPrimary

-- manifest card: commalg_decomp_primary_radical_prime
example {R : Type*} [CommRing R] (Q : Ideal R) (hQ : Q.IsPrimary) : Q.radical.IsPrime := by
  exact Ideal.isPrime_radical hQ

-- manifest card: commalg_decomp_primary_ne_top
example {R : Type*} [CommRing R] (Q : Ideal R) (hQ : Q.IsPrimary) : Q ≠ ⊤ := by
  exact hQ.ne_top

-- manifest card: commalg_decomp_primary_inf_common_radical
example {R : Type*} [CommRing R] (Q1 Q2 : Ideal R) (hQ1 : Q1.IsPrimary)
    (hQ2 : Q2.IsPrimary) (hrad : Q1.radical = Q2.radical) : (Q1 ⊓ Q2).IsPrimary := by
  exact hQ1.inf hQ2 hrad

-- manifest card: commalg_decomp_common_radical_inf_radical
example {R : Type*} [CommRing R] (Q1 Q2 : Ideal R) (hrad : Q1.radical = Q2.radical) :
    (Q1 ⊓ Q2).radical = Q1.radical := by
  rw [Ideal.radical_inf, hrad, inf_idem]

-- manifest card: commalg_decomp_primary_minimal_primes_singleton
example {R : Type*} [CommRing R] (Q : Ideal R) (hQ : Q.IsPrimary) :
    Q.radical ∈ Q.minimalPrimes := by
  rw [Ideal.minimalPrimes_eq_subsingleton hQ]
  simp

-- manifest card: commalg_decomp_prime_minimal_primes_singleton
example {R : Type*} [CommRing R] (P : Ideal R) (hP : P.IsPrime) :
    P ∈ P.minimalPrimes := by
  letI : P.IsPrime := hP
  rw [Ideal.minimalPrimes_eq_subsingleton_self]
  simp

-- manifest card: commalg_decomp_radical_is_radical
example {R : Type*} [CommRing R] (I : Ideal R) : I.radical.IsRadical := by
  exact Ideal.radical_isRadical I

-- manifest card: commalg_decomp_primary_underlying_is_primary
example {R : Type*} [CommRing R] (Q : Ideal R) (hQ : Q.IsPrimary) : Q.IsPrimary := by
  exact hQ

-- manifest card: commalg_decomp_two_component_reconstruct
example {R : Type*} [CommRing R] (I Q1 Q2 : Ideal R) (h : I = Q1 ⊓ Q2) :
    I = Q1 ⊓ Q2 := by
  exact h

-- manifest card: commalg_decomp_two_component_radical
example {R : Type*} [CommRing R] (I Q1 Q2 : Ideal R) (h : I = Q1 ⊓ Q2) :
    I.radical = Q1.radical ⊓ Q2.radical := by
  rw [h]
  exact Ideal.radical_inf Q1 Q2

-- manifest card: commalg_decomp_two_component_le_left
example {R : Type*} [CommRing R] (I Q1 Q2 : Ideal R) (h : I = Q1 ⊓ Q2) : I ≤ Q1 := by
  rw [h]
  exact inf_le_left

-- manifest card: commalg_decomp_two_component_le_right
example {R : Type*} [CommRing R] (I Q1 Q2 : Ideal R) (h : I = Q1 ⊓ Q2) : I ≤ Q2 := by
  rw [h]
  exact inf_le_right

-- manifest card: commalg_decomp_three_component_reconstruct
example {R : Type*} [CommRing R] (I Q1 Q2 Q3 : Ideal R) (h : I = Q1 ⊓ Q2 ⊓ Q3) :
    I = Q1 ⊓ Q2 ⊓ Q3 := by
  exact h

-- manifest card: commalg_decomp_three_component_radical
example {R : Type*} [CommRing R] (I Q1 Q2 Q3 : Ideal R) (h : I = Q1 ⊓ Q2 ⊓ Q3) :
    I.radical = Q1.radical ⊓ Q2.radical ⊓ Q3.radical := by
  rw [h, Ideal.radical_inf, Ideal.radical_inf]

-- manifest card: commalg_decomp_three_component_le_first
example {R : Type*} [CommRing R] (I Q1 Q2 Q3 : Ideal R) (h : I = Q1 ⊓ Q2 ⊓ Q3) : I ≤ Q1 := by
  rw [h]
  exact le_trans inf_le_left inf_le_left

-- manifest card: commalg_decomp_irredundant2_omit_first_changes
example {R : Type*} [CommRing R] (I Q1 Q2 : Ideal R) (h : I = Q1 ⊓ Q2)
    (hnot : ¬ Q2 ≤ Q1) : I ≠ Q2 := by
  intro hI
  apply hnot
  rw [← hI, h]
  exact inf_le_left

-- manifest card: commalg_decomp_irredundant2_omit_second_changes
example {R : Type*} [CommRing R] (I Q1 Q2 : Ideal R) (h : I = Q1 ⊓ Q2)
    (hnot : ¬ Q1 ≤ Q2) : I ≠ Q1 := by
  intro hI
  apply hnot
  rw [← hI, h]
  exact inf_le_right
