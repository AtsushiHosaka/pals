import Mathlib

-- The following witnesses are deliberately small and use Mathlib's native
-- Nat/Int semantics.  They are evidence for the sealed proposal only, not an
-- OpenMath-to-Lean translation certificate.

-- manifest card: number_theory_gcd_comm
example (m n : ℕ) : Nat.gcd m n = Nat.gcd n m := by
  exact Nat.gcd_comm m n

-- manifest card: number_theory_gcd_zero_right
example (n : ℕ) : Nat.gcd n 0 = n := by
  exact Nat.gcd_zero_right n

-- manifest card: number_theory_lcm_zero_right
example (n : ℕ) : Nat.lcm n 0 = 0 := by
  exact Nat.lcm_zero_right n

-- manifest card: number_theory_dvd_reflexive
example (n : ℕ) : n ∣ n := by
  exact dvd_refl n

-- manifest card: number_theory_dvd_transitive
example (a b c : ℕ) (hab : a ∣ b) (hbc : b ∣ c) : a ∣ c := by
  exact hab.trans hbc

-- manifest card: number_theory_gcd_dvd_left
example (m n : ℕ) : Nat.gcd m n ∣ m := by
  exact Nat.gcd_dvd_left m n

-- manifest card: number_theory_dvd_mul_right
example (a b c : ℕ) (hab : a ∣ b) : a ∣ b * c := by
  exact dvd_mul_of_dvd_left hab c

-- manifest card: number_theory_mod_reduce_17_5
example (n : ℕ) (h : n = 17) : n % 5 = 2 := by
  subst n
  norm_num

-- manifest card: number_theory_mod_add_fixed_five
example (a b c d : ℕ) (hab : a ≡ b [MOD 5]) (hcd : c ≡ d [MOD 5]) :
    a + c ≡ b + d [MOD 5] := by
  exact hab.add hcd

-- manifest card: number_theory_mod_mul_fixed_five
example (a b c d : ℕ) (hab : a ≡ b [MOD 5]) (hcd : c ≡ d [MOD 5]) :
    a * c ≡ b * d [MOD 5] := by
  exact hab.mul hcd

-- manifest card: number_theory_prime_two
example (n : ℕ) (h : n = 2) : Nat.Prime n := by
  subst n
  exact Nat.prime_two

-- manifest card: number_theory_bezout_coprime_nat
example (a b : ℕ) (h : Nat.gcd a b = 1) :
    ∃ x y : ℤ, (a : ℤ) * x + (b : ℤ) * y = 1 := by
  refine ⟨a.gcdA b, a.gcdB b, ?_⟩
  rw [← Nat.gcd_eq_gcd_ab, h]
  norm_num
