import Mathlib

/-!
Pinned-Mathlib witnesses for the local CA-5 integral-dependence and valuation
proposal.  These declarations are direct evidence for the named cards only;
they do not assert an automatic OpenMath-to-Lean translation.
-/

section PalsCommutativeAlgebraIntegral

-- manifest card: commalg_integral_base_map
example {R S : Type*} [CommRing R] [CommRing S] [Algebra R S] (r : R) :
    IsIntegral R (algebraMap R S r) := by
  exact isIntegral_algebraMap

-- manifest card: commalg_integral_zero
example {R S : Type*} [CommRing R] [CommRing S] [Algebra R S] : IsIntegral R (0 : S) := by
  exact isIntegral_zero

-- manifest card: commalg_integral_one
example {R S : Type*} [CommRing R] [CommRing S] [Algebra R S] : IsIntegral R (1 : S) := by
  exact isIntegral_one

-- manifest card: commalg_integral_neg
example {R S : Type*} [CommRing R] [CommRing S] [Algebra R S] (x : S) (hx : IsIntegral R x) :
    IsIntegral R (-x) := by
  exact hx.neg

-- manifest card: commalg_integral_add
example {R S : Type*} [CommRing R] [CommRing S] [Algebra R S] (x y : S)
    (hx : IsIntegral R x) (hy : IsIntegral R y) : IsIntegral R (x + y) := by
  exact hx.add hy

-- manifest card: commalg_integral_sub
example {R S : Type*} [CommRing R] [CommRing S] [Algebra R S] (x y : S)
    (hx : IsIntegral R x) (hy : IsIntegral R y) : IsIntegral R (x - y) := by
  exact hx.sub hy

-- manifest card: commalg_integral_mul
example {R S : Type*} [CommRing R] [CommRing S] [Algebra R S] (x y : S)
    (hx : IsIntegral R x) (hy : IsIntegral R y) : IsIntegral R (x * y) := by
  exact hx.mul hy

-- manifest card: commalg_integral_square
example {R S : Type*} [CommRing R] [CommRing S] [Algebra R S] (x : S) (hx : IsIntegral R x) :
    IsIntegral R (x * x) := by
  exact hx.mul hx

-- manifest card: commalg_integral_extension_member
example {R S : Type*} [CommRing R] [CommRing S] [Algebra R S] [Algebra.IsIntegral R S] (x : S) :
    IsIntegral R x := by
  exact Algebra.IsIntegral.isIntegral x

-- manifest card: commalg_valuation_mem_or_inv_mem
example {K : Type*} [Field K] (V : ValuationSubring K) (x : K) : x ∈ V ∨ x⁻¹ ∈ V := by
  exact V.mem_or_inv_mem x

-- manifest card: commalg_valuation_zero_mem
example {K : Type*} [Field K] (V : ValuationSubring K) : (0 : K) ∈ V := by
  exact V.zero_mem

-- manifest card: commalg_valuation_one_mem
example {K : Type*} [Field K] (V : ValuationSubring K) : (1 : K) ∈ V := by
  exact V.one_mem

-- manifest card: commalg_valuation_neg_closed
example {K : Type*} [Field K] (V : ValuationSubring K) (x : K) (hx : x ∈ V) : -x ∈ V := by
  exact V.neg_mem x hx

-- manifest card: commalg_valuation_add_closed
example {K : Type*} [Field K] (V : ValuationSubring K) (x y : K) (hx : x ∈ V) (hy : y ∈ V) :
    x + y ∈ V := by
  exact V.add_mem x y hx hy

-- manifest card: commalg_valuation_sub_closed
example {K : Type*} [Field K] (V : ValuationSubring K) (x y : K) (hx : x ∈ V) (hy : y ∈ V) :
    x - y ∈ V := by
  exact V.sub_mem hx hy

-- manifest card: commalg_valuation_mul_closed
example {K : Type*} [Field K] (V : ValuationSubring K) (x y : K) (hx : x ∈ V) (hy : y ∈ V) :
    x * y ∈ V := by
  exact V.mul_mem x y hx hy

-- manifest card: commalg_valuation_square_closed
example {K : Type*} [Field K] (V : ValuationSubring K) (x : K) (hx : x ∈ V) : x * x ∈ V := by
  exact V.mul_mem x x hx hx

-- manifest card: commalg_valuation_not_mem_implies_inv_mem
example {K : Type*} [Field K] (V : ValuationSubring K) (x : K) (hx : x ∉ V) : x⁻¹ ∈ V := by
  exact (V.mem_or_inv_mem x).resolve_left hx

-- manifest card: commalg_valuation_not_inv_mem_implies_mem
example {K : Type*} [Field K] (V : ValuationSubring K) (x : K) (hx : x⁻¹ ∉ V) : x ∈ V := by
  exact (V.mem_or_inv_mem x).resolve_right hx

-- manifest card: commalg_valuation_integrally_closed
example {K : Type*} [Field K] (V : ValuationSubring K) : IsIntegrallyClosed V := by
  infer_instance

end PalsCommutativeAlgebraIntegral
