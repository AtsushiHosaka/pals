import Mathlib
open MeasureTheory Set
open ProbabilityTheory
open scoped ProbabilityTheory unitInterval ENNReal

-- manifest card: prob_choose_zero
example (n : ℕ) : Nat.choose n 0 = 1 := by exact Nat.choose_zero_right n

-- manifest card: prob_choose_self
example (n : ℕ) : Nat.choose n n = 1 := by exact Nat.choose_self n

-- manifest card: prob_choose_one
example (n : ℕ) : Nat.choose n 1 = n := by simp

-- manifest card: prob_choose_pascal
example (n k : ℕ) : Nat.choose (n + 1) (k + 1) = Nat.choose n k + Nat.choose n (k + 1) := by exact Nat.choose_succ_succ' n k

-- manifest card: prob_choose_symmetry
example {n k : ℕ} (hk : k ≤ n) : Nat.choose n (n - k) = Nat.choose n k := by exact Nat.choose_symm hk

-- manifest card: prob_choose_two
example (n : ℕ) : Nat.choose n 2 = n * (n - 1) / 2 := by exact Nat.choose_two_right n

-- manifest card: prob_expectation_constant
example {Ω : Type*} [MeasurableSpace Ω] (μ : Measure Ω) [IsProbabilityMeasure μ] (c : ℝ) : ∫ _ : Ω, c ∂μ = c := by simp

-- manifest card: prob_binomial_pmf
example (n k : ℕ) (p : I) : (Bin(n, p)).real {k} = (n.choose k) * p^k * (1 - p)^(n - k) := by exact binomial_real_singleton n k p

-- manifest card: prob_binomial_zero_success
example (n : ℕ) (p : I) : (Bin(n, p)).real {0} = (1 - p)^n := by simp

-- manifest card: prob_binomial_all_success
example (n : ℕ) (p : I) : (Bin(n, p)).real {n} = p^n := by simp
