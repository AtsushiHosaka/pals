import Mathlib.Data.Nat.GCD.Basic

/- The formal theorem from PALS issue #37. This is a local regression fixture;
   compiling it does not verify a generated answer or the deployed worker. -/
theorem coprime_divisibility
    (a b c : ℕ) (hcoprime : Nat.gcd a b = 1) (hdiv : a ∣ b * c) : a ∣ c := by
  have h : Nat.Coprime a b := hcoprime
  exact h.dvd_of_dvd_mul_left hdiv
