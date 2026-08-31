import Mathlib

structure Point2 where
  x : ℝ
  y : ℝ

structure Vector2 where
  x : ℝ
  y : ℝ

def distanceSq (p q : Point2) : ℝ :=
  (p.x - q.x) ^ 2 + (p.y - q.y) ^ 2

def reflectDiagonal (p : Point2) : Point2 := ⟨p.y, p.x⟩

def vectorAdd (u v : Vector2) : Vector2 := ⟨u.x + v.x, u.y + v.y⟩

def vectorScale (a : ℝ) (u : Vector2) : Vector2 := ⟨a * u.x, a * u.y⟩

def dot (u v : Vector2) : ℝ := u.x * v.x + u.y * v.y

def determinant2 (u v : Vector2) : ℝ := u.x * v.y - u.y * v.x

-- geometry_line_through_two_points
example :
    let line : Set Point2 := {p | p.y = 2 * p.x + 1}
    Point2.mk 0 1 ∈ line ∧ Point2.mk 2 5 ∈ line := by
  norm_num

-- geometry_circle_through_three_points
example :
    let circle : Set Point2 := {p | p.x ^ 2 + p.y ^ 2 = 1}
    Point2.mk 1 0 ∈ circle ∧ Point2.mk 0 1 ∈ circle ∧ Point2.mk (-1) 0 ∈ circle := by
  norm_num

-- geometry_perpendicular_bisector_locus
example (x y : ℝ) :
    distanceSq (Point2.mk x y) (Point2.mk (-1) 0) =
      distanceSq (Point2.mk x y) (Point2.mk 1 0) ↔ x = 0 := by
  constructor
  · intro h
    dsimp [distanceSq] at h
    nlinarith
  · rintro rfl
    simp only [distanceSq]
    ring

-- geometry_reflection_in_line (the non-axis-aligned line y = x)
example (x y : ℝ) :
    distanceSq (reflectDiagonal (Point2.mk x y)) (Point2.mk 0 0) =
      distanceSq (Point2.mk x y) (Point2.mk 0 0) := by
  dsimp [distanceSq, reflectDiagonal]
  ring

-- vector_component_addition
example : vectorAdd (Vector2.mk 1 2) (Vector2.mk 3 (-1)) = Vector2.mk 4 1 := by
  norm_num [vectorAdd]

-- vector_scalar_multiple
example : vectorScale 3 (Vector2.mk 2 (-1)) = Vector2.mk 6 (-3) := by
  norm_num [vectorScale]

-- vector_dot_product_orthogonality
example : dot (Vector2.mk 1 2) (Vector2.mk 2 (-1)) = 0 := by
  norm_num [dot]

-- vector_triangle_area_determinant
example : |determinant2 (Vector2.mk 2 0) (Vector2.mk 0 3)| / 2 = 3 := by
  norm_num [determinant2]

-- complex_cartesian_multiplication
example : ((1 : ℂ) + 2 * Complex.I) * (3 - Complex.I) = 5 + 5 * Complex.I := by
  calc
    ((1 : ℂ) + 2 * Complex.I) * (3 - Complex.I) = 3 + 5 * Complex.I - 2 * Complex.I ^ 2 := by ring
    _ = 5 + 5 * Complex.I := by rw [Complex.I_sq]; ring

-- complex_conjugate_modulus_square
example (z : ℂ) : z * star z = (Complex.normSq z : ℂ) := by
  simpa only [Complex.star_def] using Complex.mul_conj z

-- complex_multiply_i_quarter_turn
example (x y : ℝ) : ((x : ℂ) + y * Complex.I) * Complex.I = (-y : ℂ) + x * Complex.I := by
  calc
    ((x : ℂ) + y * Complex.I) * Complex.I = (x : ℂ) * Complex.I + (y : ℂ) * Complex.I ^ 2 := by ring
    _ = (-y : ℂ) + x * Complex.I := by rw [Complex.I_sq]; ring

-- complex_argument_quadrant (quadrant II branch)
example :
    Complex.arg ((-1 : ℂ) + Complex.I) =
      Real.arcsin ((-((-1 : ℂ) + Complex.I)).im / ‖(-1 : ℂ) + Complex.I‖) + Real.pi := by
  apply Complex.arg_of_re_neg_of_im_nonneg
  · norm_num
  · norm_num
