import Mathlib

-- CA-6: each target is kept beside its direct pinned-Mathlib witness.

-- manifest card: chain_noetherian_ideal_fg
example {R : Type*} [CommRing R] [IsNoetherianRing R] (I : Ideal R) : I.FG := by
  exact Ideal.fg_of_isNoetherianRing I

-- manifest card: chain_noetherian_sum_fg
example {R : Type*} [CommRing R] [IsNoetherianRing R] (I J : Ideal R) : (I + J).FG := by
  exact Ideal.fg_of_isNoetherianRing (I + J)

-- manifest card: chain_noetherian_inf_fg
example {R : Type*} [CommRing R] [IsNoetherianRing R] (I J : Ideal R) : (I ⊓ J).FG := by
  exact Ideal.fg_of_isNoetherianRing (I ⊓ J)

-- manifest card: chain_noetherian_product_fg
example {R : Type*} [CommRing R] [IsNoetherianRing R] (I J : Ideal R) : (I * J).FG := by
  exact Ideal.fg_of_isNoetherianRing (I * J)

-- manifest card: chain_noetherian_radical_fg
example {R : Type*} [CommRing R] [IsNoetherianRing R] (I : Ideal R) : I.radical.FG := by
  exact Ideal.fg_of_isNoetherianRing I.radical

-- manifest card: chain_noetherian_all_ideals_fg
example {R : Type*} [CommRing R] [IsNoetherianRing R] : ∀ I : Ideal R, I.FG := by
  intro I
  exact Ideal.fg_of_isNoetherianRing I

-- manifest card: chain_hilbert_basis_one_variable
example {R : Type*} [CommRing R] [IsNoetherianRing R] : IsNoetherianRing (Polynomial R) := by
  infer_instance

-- manifest card: chain_hilbert_basis_two_iterations
example {R : Type*} [CommRing R] [IsNoetherianRing R] : IsNoetherianRing (Polynomial (Polynomial R)) := by
  infer_instance

-- manifest card: chain_artinian_implies_noetherian
example {R : Type*} [CommRing R] [IsArtinianRing R] : IsNoetherianRing R := by
  infer_instance

-- manifest card: chain_artinian_dimension_zero
example {R : Type*} [CommRing R] [IsArtinianRing R] : Ring.KrullDimLE 0 R := by
  infer_instance

-- manifest card: chain_noetherian_dimension_zero_artinian
example {R : Type*} [CommRing R] [IsNoetherianRing R] (h : Ring.KrullDimLE 0 R) : IsArtinianRing R := by
  exact @IsNoetherianRing.isArtinianRing_of_krullDimLE_zero R _ _ h

-- manifest card: chain_artinian_prime_maximal
example {R : Type*} [CommRing R] [IsArtinianRing R] (P : Ideal R) (h : P.IsPrime) : P.IsMaximal := by
  letI : P.IsPrime := h
  exact IsArtinianRing.isMaximal_of_isPrime P

-- manifest card: chain_dimension_zero_prime_maximal
example {R : Type*} [CommRing R] (h : Ring.KrullDimLE 0 R) (P : Ideal R) (hP : P.IsPrime) : P.IsMaximal := by
  exact Ring.krullDimLE_zero_iff.mp h P hP

-- manifest card: chain_field_noetherian
example {K : Type*} [Field K] : IsNoetherianRing K := by
  infer_instance

-- manifest card: chain_field_artinian
example {K : Type*} [Field K] : IsArtinianRing K := by
  infer_instance

-- manifest card: chain_field_dimension_zero
example {K : Type*} [Field K] : Ring.KrullDimLE 0 K := by
  infer_instance

-- manifest card: chain_artinian_ideal_fg
example {R : Type*} [CommRing R] [IsArtinianRing R] (I : Ideal R) : I.FG := by
  exact Ideal.fg_of_isNoetherianRing I
