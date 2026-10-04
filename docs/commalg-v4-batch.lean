import Mathlib

-- manifest card: commalg_v4_vanishing_galois
example {R : Type*} [CommRing R] (I : Ideal R) (T : Set (PrimeSpectrum R)) : T ⊆ PrimeSpectrum.zeroLocus I ↔ I ≤ PrimeSpectrum.vanishingIdeal T := by
  exact PrimeSpectrum.subset_zeroLocus_iff_le_vanishingIdeal T I

-- manifest card: commalg_v4_zero_locus_vanishing_closure
example {R : Type*} [CommRing R] (T : Set (PrimeSpectrum R)) : PrimeSpectrum.zeroLocus (PrimeSpectrum.vanishingIdeal T) = closure T := by
  exact PrimeSpectrum.zeroLocus_vanishingIdeal_eq_closure T

-- manifest card: commalg_v4_vanishing_zero_locus_radical
example {R : Type*} [CommRing R] (I : Ideal R) : PrimeSpectrum.vanishingIdeal (PrimeSpectrum.zeroLocus I) = I.radical := by
  exact PrimeSpectrum.vanishingIdeal_zeroLocus_eq_radical I

-- manifest card: commalg_v4_zero_locus_sum
example {R : Type*} [CommRing R] (I J : Ideal R) : PrimeSpectrum.zeroLocus ((I ⊔ J : Ideal R) : Set R) = PrimeSpectrum.zeroLocus I ∩ PrimeSpectrum.zeroLocus J := by
  exact PrimeSpectrum.zeroLocus_sup I J

-- manifest card: commalg_v4_zero_locus_product
example {R : Type*} [CommRing R] (I J : Ideal R) : PrimeSpectrum.zeroLocus ((I * J : Ideal R) : Set R) = PrimeSpectrum.zeroLocus I ∪ PrimeSpectrum.zeroLocus J := by
  exact PrimeSpectrum.zeroLocus_mul I J

-- manifest card: commalg_v4_closed_sets_zero_loci
example {R : Type*} [CommRing R] (T : Set (PrimeSpectrum R)) : IsClosed T ↔ ∃ I : Ideal R, T = PrimeSpectrum.zeroLocus I := by
  exact PrimeSpectrum.isClosed_iff_zeroLocus_ideal T

-- manifest card: commalg_v4_closure_prime_point
example {R : Type*} [CommRing R] (p : PrimeSpectrum R) : closure ({p} : Set (PrimeSpectrum R)) = PrimeSpectrum.zeroLocus p.asIdeal := by
  exact PrimeSpectrum.closure_singleton p

-- manifest card: commalg_v4_closed_point_maximal
example {R : Type*} [CommRing R] (p : PrimeSpectrum R) : IsClosed ({p} : Set (PrimeSpectrum R)) ↔ p.asIdeal.IsMaximal := by
  exact PrimeSpectrum.isClosed_singleton_iff_isMaximal p

-- manifest card: commalg_v4_irreducible_zero_locus
example {R : Type*} [CommRing R] (I : Ideal R) : IsIrreducible (PrimeSpectrum.zeroLocus (I : Set R)) ↔ I.radical.IsPrime := by
  exact PrimeSpectrum.isIrreducible_zeroLocus_iff I

-- manifest card: commalg_v4_basic_open_quasicompact
example {R : Type*} [CommRing R] (x : R) : IsCompact (PrimeSpectrum.basicOpen x : Set (PrimeSpectrum R)) := by
  exact PrimeSpectrum.isCompact_basicOpen x

-- manifest card: commalg_v4_basic_open_empty_nilpotent
example {R : Type*} [CommRing R] (x : R) : (PrimeSpectrum.basicOpen x : Set (PrimeSpectrum R)) = ∅ ↔ IsNilpotent x := by
  simpa only [← TopologicalSpace.Opens.coe_bot, TopologicalSpace.Opens.coe_inj] using PrimeSpectrum.basicOpen_eq_bot_iff x

-- manifest card: commalg_v4_basic_open_inclusion_radical
example {R : Type*} [CommRing R] (x y : R) : (PrimeSpectrum.basicOpen x : Set (PrimeSpectrum R)) ⊆ PrimeSpectrum.basicOpen y ↔ x ∈ (Ideal.span ({y} : Set R)).radical := by
  exact PrimeSpectrum.basicOpen_le_basicOpen_iff x y

-- manifest card: commalg_v4_clopen_unique_idempotent
example {R : Type*} [CommRing R] (T : Set (PrimeSpectrum R)) (hT : IsClopen T) : ∃ x : R, IsIdempotentElem x ∧ T = PrimeSpectrum.basicOpen x ∧ ∀ y : R, IsIdempotentElem y ∧ T = PrimeSpectrum.basicOpen y → y = x := by
  obtain ⟨x, hx, huniq⟩ := PrimeSpectrum.existsUnique_idempotent_basicOpen_eq_of_isClopen hT
  exact ⟨x, hx.1, hx.2, huniq⟩

-- manifest card: commalg_v4_spectrum_t0
example {R : Type*} [CommRing R] : T0Space (PrimeSpectrum R) := by
  infer_instance

-- manifest card: commalg_v4_spectrum_nonempty_nontrivial
example {R : Type*} [CommRing R] : Nonempty (PrimeSpectrum R) ↔ Nontrivial R := by
  exact PrimeSpectrum.nonempty_iff_nontrivial

-- manifest card: commalg_v4_spectrum_comap_continuous
example {R : Type*} [CommRing R] {S : Type*} [CommRing S] (f : R →+* S) : Continuous (PrimeSpectrum.comap f) := by
  exact PrimeSpectrum.continuous_comap f

-- manifest card: commalg_v4_spectrum_preimage_zero_locus
example {R : Type*} [CommRing R] {S : Type*} [CommRing S] (f : R →+* S) (I : Ideal R) : (PrimeSpectrum.comap f) ⁻¹' PrimeSpectrum.zeroLocus I = PrimeSpectrum.zeroLocus (I.map f) := by
  ext p
  change I ≤ p.asIdeal.comap f ↔ I.map f ≤ p.asIdeal
  exact Ideal.map_le_iff_le_comap.symm

-- manifest card: commalg_v4_surjective_map_closed_embedding
example {R : Type*} [CommRing R] {S : Type*} [CommRing S] (f : R →+* S) (hf : Function.Surjective f) : Topology.IsClosedEmbedding (PrimeSpectrum.comap f) := by
  exact PrimeSpectrum.isClosedEmbedding_comap_of_surjective S f hf

-- manifest card: commalg_v4_spectrum_range_closure
example {R : Type*} [CommRing R] {S : Type*} [CommRing S] (f : R →+* S) : closure (Set.range (PrimeSpectrum.comap f)) = PrimeSpectrum.zeroLocus (RingHom.ker f) := by
  exact PrimeSpectrum.closure_range_comap f

-- manifest card: commalg_v4_localization_spectrum_embedding
example {R : Type*} [CommRing R] (M : Submonoid R) : Topology.IsEmbedding (PrimeSpectrum.comap (algebraMap R (Localization M))) := by
  exact PrimeSpectrum.localization_comap_isEmbedding (Localization M) M

-- manifest card: commalg_v4_localization_away_basic_open
example {R : Type*} [CommRing R] (x : R) : Topology.IsOpenEmbedding (PrimeSpectrum.comap (algebraMap R (Localization.Away x))) ∧ Set.range (PrimeSpectrum.comap (algebraMap R (Localization.Away x))) = PrimeSpectrum.basicOpen x := by
  exact ⟨PrimeSpectrum.localization_away_isOpenEmbedding (Localization.Away x) x, PrimeSpectrum.localization_away_comap_range (Localization.Away x) x⟩

-- manifest card: commalg_v4_nil_quotient_spectrum_homeomorphism
example {R : Type*} [CommRing R] (I : Ideal R) (hI : I ≤ nilradical R) : IsHomeomorph (PrimeSpectrum.comap (Ideal.Quotient.mk I)) := by
  exact isHomeomorph_iff_isEmbedding_surjective.mpr ⟨(PrimeSpectrum.isClosedEmbedding_comap_of_surjective (R ⧸ I) (Ideal.Quotient.mk I) Ideal.Quotient.mk_surjective).isEmbedding, (PrimeSpectrum.comap_quotientMk_bijective_of_le_nilradical hI).2⟩

-- manifest card: commalg_v4_integral_spectrum_closed_map
example {R : Type*} [CommRing R] {S : Type*} [CommRing S] (f : R →+* S) (hf : f.IsIntegral) : IsClosedMap (PrimeSpectrum.comap f) := by
  exact PrimeSpectrum.isClosedMap_comap_of_isIntegral f hf

-- manifest card: commalg_v4_integral_lying_over
example {R : Type*} [CommRing R] {S : Type*} [CommRing S] (f : R →+* S) (hf : f.IsIntegral) (hinj : Function.Injective f) : Function.Surjective (PrimeSpectrum.comap f) := by
  exact hf.comap_surjective hinj

-- manifest card: commalg_v4_integral_going_up
example {R : Type*} [CommRing R] {S : Type*} [CommRing S] [Algebra R S] [Algebra.IsIntegral R S] (I : Ideal R) (J : Ideal S) [I.IsPrime] [J.IsPrime] (h : J.comap (algebraMap R S) ≤ I) : ∃ U : Ideal S, J ≤ U ∧ U.IsPrime ∧ U.comap (algebraMap R S) = I := by
  exact Ideal.exists_ideal_over_prime_of_isIntegral_of_isPrime I J h

-- manifest card: commalg_v4_integral_incomparability
example {R : Type*} [CommRing R] {S : Type*} [CommRing S] [Algebra R S] [Algebra.IsIntegral R S] (I J : Ideal S) [I.IsPrime] (h : I < J) : I.comap (algebraMap R S) < J.comap (algebraMap R S) := by
  exact Ideal.IsIntegral.comap_lt_comap h

-- manifest card: commalg_v4_integral_maximal_equivalence
example {R : Type*} [CommRing R] {S : Type*} [CommRing S] (f : R →+* S) (hf : f.IsIntegral) (I : Ideal S) [I.IsPrime] : I.IsMaximal ↔ (I.comap f).IsMaximal := by
  constructor
  · intro hI
    letI := hI
    exact Ideal.isMaximal_comap_of_isIntegral_of_isMaximal' f hf I
  · exact Ideal.isMaximal_of_isIntegral_of_isMaximal_comap' f hf I

-- manifest card: commalg_v4_integral_extension_proper
example {R : Type*} [CommRing R] {S : Type*} [CommRing S] (f : R →+* S) (hf : f.IsIntegral) (I : Ideal R) (hI : RingHom.ker f ≤ I) : I.map f = ⊤ ↔ I = ⊤ := by
  exact Ideal.map_eq_top_iff_of_ker_le f hI hf

-- manifest card: commalg_v4_going_down_normal_domain
example {R : Type*} [CommRing R] {S : Type*} [CommRing S] [Algebra R S] [IsDomain R] [IsDomain S] [IsIntegrallyClosed R] [Algebra.IsIntegral R S] (hinj : Function.Injective (algebraMap R S)) (I J : Ideal R) (U : Ideal S) [I.IsPrime] [J.IsPrime] [U.IsPrime] (hU : U.comap (algebraMap R S) = J) (hIJ : I ≤ J) : ∃ T : Ideal S, T ≤ U ∧ T.IsPrime ∧ T.comap (algebraMap R S) = I := by
  letI : FaithfulSMul R S := (faithfulSMul_iff_algebraMap_injective R S).mpr hinj
  letI : U.LiesOver J := (Ideal.liesOver_iff U J).mpr hU.symm
  obtain ⟨T, hTU, hT, hTI⟩ := Ideal.exists_ideal_le_liesOver_of_le U hIJ
  exact ⟨T, hTU, hT, (Ideal.liesOver_iff T I).mp hTI |>.symm⟩

-- manifest card: commalg_v4_going_down_flat
example {R : Type*} [CommRing R] {S : Type*} [CommRing S] [Algebra R S] [Module.Flat R S] (I J : Ideal R) (U : Ideal S) [I.IsPrime] [J.IsPrime] [U.IsPrime] (hU : U.comap (algebraMap R S) = J) (hIJ : I ≤ J) : ∃ T : Ideal S, T ≤ U ∧ T.IsPrime ∧ T.comap (algebraMap R S) = I := by
  letI : U.LiesOver J := (Ideal.liesOver_iff U J).mpr hU.symm
  obtain ⟨T, hTU, hT, hTI⟩ := Ideal.exists_ideal_le_liesOver_of_le U hIJ
  exact ⟨T, hTU, hT, (Ideal.liesOver_iff T I).mp hTI |>.symm⟩

-- manifest card: commalg_v4_dimension_surjective_map
example {R : Type*} [CommRing R] {S : Type*} [CommRing S] (f : R →+* S) (hf : Function.Surjective f) : ringKrullDim S ≤ ringKrullDim R := by
  exact ringKrullDim_le_of_surjective f hf

-- manifest card: commalg_v4_dimension_polynomial_noetherian
example {R : Type*} [CommRing R] [IsNoetherianRing R] : ringKrullDim (Polynomial R) = ringKrullDim R + 1 := by
  exact Polynomial.ringKrullDim_of_isNoetherianRing

-- manifest card: commalg_v4_dimension_localization_height
example {R : Type*} [CommRing R] (p : PrimeSpectrum R) : ringKrullDim (Localization.AtPrime p.asIdeal) = p.asIdeal.height := by
  exact IsLocalization.AtPrime.ringKrullDim_eq_height p.asIdeal (Localization.AtPrime p.asIdeal)
