import Mathlib

/-!
Local, pinned-Mathlib witnesses for `typed-commutative-algebra-localization-v1`.

Each `example` is intentionally written independently.  The manifest binds
one OpenMath proposition to one of these exact declarations; it does not claim
an automatic OpenMath-to-Lean translation.
-/

section PalsCommutativeAlgebraLocalization

variable {R : Type*} [CommRing R] (M : Submonoid R)
variable (S : Type*) [CommRing S] [Algebra R S] [IsLocalization M S]

example (I J : Ideal R) (h : I ≤ J) :
    I.map (algebraMap R S) ≤ J.map (algebraMap R S) := by
  exact Ideal.map_mono h

example (I J : Ideal S) (h : I ≤ J) :
    I.comap (algebraMap R S) ≤ J.comap (algebraMap R S) := by
  exact Ideal.comap_mono h

example (I : Ideal R) : I ≤ (I.map (algebraMap R S)).comap (algebraMap R S) := by
  exact Ideal.le_comap_map

example (J : Ideal S) : (J.comap (algebraMap R S)).map (algebraMap R S) ≤ J := by
  exact Ideal.map_comap_le

example (J : Ideal S) :
    (J.comap (algebraMap R S)).map (algebraMap R S) = J := by
  exact IsLocalization.map_under M S J

example (I J : Ideal S) :
    I.comap (algebraMap R S) ≤ J.comap (algebraMap R S) ↔ I ≤ J := by
  exact IsLocalization.under_le_under_iff M S

example (I J : Ideal R) :
    (I ⊓ J).map (algebraMap R S) = I.map (algebraMap R S) ⊓ J.map (algebraMap R S) := by
  exact IsLocalization.map_inf M S I J

example (I J : Ideal R) :
    (I ⊔ J).map (algebraMap R S) = I.map (algebraMap R S) ⊔ J.map (algebraMap R S) := by
  exact Ideal.map_sup (f := algebraMap R S) I J

example (I J : Ideal S) :
    (I ⊓ J).comap (algebraMap R S) =
      I.comap (algebraMap R S) ⊓ J.comap (algebraMap R S) := by
  exact Ideal.comap_inf (algebraMap R S) I J

example : (⊤ : Ideal R).map (algebraMap R S) = ⊤ := by
  exact Ideal.map_top (algebraMap R S)

example : (⊤ : Ideal S).comap (algebraMap R S) = ⊤ := by
  exact Ideal.comap_top

example (I : Ideal R) :
    I.radical.map (algebraMap R S) = (I.map (algebraMap R S)).radical := by
  exact IsLocalization.map_radical M S I

example (I : Ideal R) :
    I.map (algebraMap R S) ≠ ⊤ ↔ Disjoint (M : Set R) (I : Set R) := by
  exact IsLocalization.map_algebraMap_ne_top_iff_disjoint M S I

example (J : Ideal S) :
    J.IsPrime ↔ (J.comap (algebraMap R S)).IsPrime ∧
      Disjoint (M : Set R) ((J.comap (algebraMap R S) : Ideal R) : Set R) := by
  exact IsLocalization.isPrime_iff_isPrime_disjoint M S J

example (I : Ideal R) (hprime : I.IsPrime) (hdisjoint : Disjoint (M : Set R) (I : Set R)) :
    (I.map (algebraMap R S)).IsPrime := by
  exact IsLocalization.isPrime_of_isPrime_disjoint M S I hprime hdisjoint

example (I : Ideal R) (x : R) :
    algebraMap R S x ∈ I.map (algebraMap R S) ↔ ∃ m ∈ M, m * x ∈ I := by
  exact IsLocalization.algebraMap_mem_map_algebraMap_iff M S I x

example {I : Ideal R} (x : R) (m : M) :
    IsLocalization.mk' S x m ∈ I.map (algebraMap R S) ↔ ∃ s ∈ M, s * x ∈ I := by
  exact IsLocalization.mk'_mem_map_algebraMap_iff M S I x m

example {I : Ideal S} (x : R) (m : M) :
    IsLocalization.mk' S x m ∈ I ↔ algebraMap R S x ∈ I := by
  exact IsLocalization.mk'_mem_iff

example (m : M) : IsUnit (algebraMap R S m) := by
  exact IsLocalization.map_units S m

example (x y : R) : algebraMap R S (x + y) = algebraMap R S x + algebraMap R S y := by
  exact map_add (algebraMap R S) x y

example (x y : R) : algebraMap R S (x * y) = algebraMap R S x * algebraMap R S y := by
  exact map_mul (algebraMap R S) x y

example : algebraMap R S (0 : R) = 0 := by
  exact map_zero (algebraMap R S)

example : algebraMap R S (1 : R) = 1 := by
  exact map_one (algebraMap R S)

end PalsCommutativeAlgebraLocalization
