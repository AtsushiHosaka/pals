import Mathlib

-- The generator seals each target/proof pair below into the proposal manifest.
-- No theorem asserts ODE existence or uniqueness: each certificate names its
-- concrete function, initial value at zero, and all-real equation.

-- manifest card: ode_separable_exponential_growth
example (C k : ℝ) : ((fun t : ℝ => C * Real.exp (k * t)) 0 = C) ∧ ∀ x : ℝ, deriv (fun t : ℝ => C * Real.exp (k * t)) x = k * (C * Real.exp (k * x)) := by
  constructor
  · simp
  · intro x
    have hd := ((Real.hasDerivAt_exp (k * x)).comp x (hasDerivAt_const_mul k)).const_mul C
    calc
      deriv (fun t : ℝ => C * Real.exp (k * t)) x = C * (Real.exp (k * x) * k) := by
        simpa [Function.comp_apply] using hd.deriv
      _ = k * (C * Real.exp (k * x)) := by ring

-- manifest card: ode_separable_exponential_decay
example (C k : ℝ) : ((fun t : ℝ => C * Real.exp (-k * t)) 0 = C) ∧ ∀ x : ℝ, deriv (fun t : ℝ => C * Real.exp (-k * t)) x = -k * (C * Real.exp (-k * x)) := by
  constructor
  · simp
  · intro x
    have hd := ((Real.hasDerivAt_exp (-k * x)).comp x (hasDerivAt_const_mul (-k))).const_mul C
    calc
      deriv (fun t : ℝ => C * Real.exp (-k * t)) x = C * (Real.exp (-k * x) * (-k)) := by
        simpa [Function.comp_apply] using hd.deriv
      _ = -k * (C * Real.exp (-k * x)) := by ring

-- manifest card: ode_separable_zero_solution
example : ((fun _ : ℝ => (0 : ℝ)) 0 = 0) ∧ ∀ x : ℝ, deriv (fun _ : ℝ => (0 : ℝ)) x = (0 : ℝ) ^ 2 := by
  constructor
  · simp
  · intro x
    simp

-- manifest card: ode_first_linear_homogeneous_unit
example (C : ℝ) : ((fun t : ℝ => C * Real.exp (-t)) 0 = C) ∧ ∀ x : ℝ, deriv (fun t : ℝ => C * Real.exp (-t)) x + C * Real.exp (-x) = 0 := by
  constructor
  · simp
  · intro x
    have hd := ((Real.hasDerivAt_exp (-x)).comp x (hasDerivAt_neg x)).const_mul C
    rw [show deriv (fun t : ℝ => C * Real.exp (-t)) x = C * (Real.exp (-x) * (-1)) by simpa [Function.comp_apply] using hd.deriv]
    ring

-- manifest card: ode_first_linear_affine_particular
example : ((fun t : ℝ => t - 1) 0 = -1) ∧ ∀ x : ℝ, deriv (fun t : ℝ => t - 1) x + (x - 1) = x := by
  constructor
  · norm_num
  · intro x
    have hd : HasDerivAt (fun t : ℝ => t - 1) 1 x := (hasDerivAt_id x).sub_const 1
    rw [hd.deriv]
    ring

-- manifest card: ode_first_linear_polynomial_forcing
example : ((fun t : ℝ => 2 * t) 0 = 0) ∧ ∀ x : ℝ, deriv (fun t : ℝ => 2 * t) x + 2 * x = 2 * x + 2 := by
  constructor
  · norm_num
  · intro x
    have hd : HasDerivAt (fun t : ℝ => 2 * t) 2 x := by
      simpa using (hasDerivAt_id x).const_mul 2
    rw [hd.deriv]
    ring

-- manifest card: ode_second_harmonic_sine
example : ((fun t : ℝ => Real.sin t) 0 = 0) ∧ ∀ x : ℝ, deriv (fun t : ℝ => deriv (fun s : ℝ => Real.sin s) t) x + Real.sin x = 0 := by
  constructor
  · simp
  · intro x
    rw [show (fun t : ℝ => deriv (fun s : ℝ => Real.sin s) t) = Real.cos by
      ext t
      exact (Real.hasDerivAt_sin t).deriv]
    rw [(Real.hasDerivAt_cos x).deriv]
    ring

-- manifest card: ode_second_harmonic_cosine
example : ((fun t : ℝ => Real.cos t) 0 = 1) ∧ ∀ x : ℝ, deriv (fun t : ℝ => deriv (fun s : ℝ => Real.cos s) t) x + Real.cos x = 0 := by
  constructor
  · simp
  · intro x
    rw [show (fun t : ℝ => deriv (fun s : ℝ => Real.cos s) t) = fun t : ℝ => -Real.sin t by
      ext t
      exact (Real.hasDerivAt_cos t).deriv]
    rw [show deriv (fun t : ℝ => -Real.sin t) x = -Real.cos x by
      rw [show (fun t : ℝ => -Real.sin t) = fun t : ℝ => (-1 : ℝ) * Real.sin t by
        ext t
        ring]
      rw [deriv_const_mul]
      · rw [(Real.hasDerivAt_sin x).deriv]
        ring
      · fun_prop]
    ring

-- manifest card: ode_second_exponential_positive_root
example : ((fun t : ℝ => Real.exp t) 0 = 1) ∧ ∀ x : ℝ, deriv (fun t : ℝ => deriv (fun s : ℝ => Real.exp s) t) x - Real.exp x = 0 := by
  constructor
  · simp
  · intro x
    rw [show (fun t : ℝ => deriv (fun s : ℝ => Real.exp s) t) = Real.exp by
      ext t
      exact (Real.hasDerivAt_exp t).deriv]
    rw [(Real.hasDerivAt_exp x).deriv]
    ring

-- manifest card: ode_second_zero_characteristic_identity
example : ((fun t : ℝ => t) 0 = 0) ∧ ∀ x : ℝ, deriv (fun t : ℝ => deriv (fun s : ℝ => s) t) x = 0 := by
  constructor
  · simp
  · intro x
    rw [show (fun t : ℝ => deriv (fun s : ℝ => s) t) = fun _ : ℝ => 1 by
      ext t
      exact (hasDerivAt_id t).deriv]
    simp
