import Mathlib

open scoped Topology

def HasPartialXAt (f : ℝ × ℝ → ℝ) (slope : ℝ) (point : ℝ × ℝ) : Prop :=
  HasDerivAt (fun x : ℝ => f (x, point.2)) slope point.1

def HasPartialYAt (f : ℝ × ℝ → ℝ) (slope : ℝ) (point : ℝ × ℝ) : Prop :=
  HasDerivAt (fun y : ℝ => f (point.1, y)) slope point.2

-- manifest card: multivar_partial_x_quadratic
example (a b : ℝ) :
    HasPartialXAt (fun p : ℝ × ℝ => p.1 ^ 2 + p.2 ^ 2) (2 * a) (a, b) := by
  simpa [HasPartialXAt, pow_two] using (hasDerivAt_pow 2 a).add_const (b ^ 2)

-- manifest card: multivar_partial_y_quadratic
example (a b : ℝ) :
    HasPartialYAt (fun p : ℝ × ℝ => p.1 ^ 2 + p.2 ^ 2) (2 * b) (a, b) := by
  simpa [HasPartialYAt, pow_two] using (hasDerivAt_pow 2 b).const_add (a ^ 2)

-- manifest card: multivar_partial_x_product
example (a b : ℝ) :
    HasPartialXAt (fun p : ℝ × ℝ => p.1 * p.2) b (a, b) := by
  simpa [HasPartialXAt] using (hasDerivAt_id a).mul_const b

-- manifest card: multivar_partial_y_product
example (a b : ℝ) :
    HasPartialYAt (fun p : ℝ × ℝ => p.1 * p.2) a (a, b) := by
  simpa [HasPartialYAt] using (hasDerivAt_id b).const_mul a

-- manifest card: multivar_differentiable_quadratic
example (p : ℝ × ℝ) : DifferentiableAt ℝ (fun q : ℝ × ℝ => q.1 ^ 2 + q.2 ^ 2) p := by
  fun_prop

-- manifest card: multivar_differentiable_product
example (p : ℝ × ℝ) : DifferentiableAt ℝ (fun q : ℝ × ℝ => q.1 * q.2) p := by
  fun_prop
