import Mathlib

abbrev Mat2 := Matrix (Fin 2) (Fin 2) ℝ
abbrev Vec2 := Fin 2 → ℝ

def A : Mat2 := !![1, 2; 3, 4]
def B : Mat2 := !![2, 0; 1, 2]
def P : Mat2 := !![0, 1; 1, 0]
def x : Vec2 := ![2, -1]
def b : Vec2 := ![0, 2]

def IsMatrixInverse (M N : Mat2) : Prop := M * N = 1 ∧ N * M = 1

-- matrix1:add
example : A + B = !![3, 2; 4, 6] := by
  ext i j
  fin_cases i <;> fin_cases j <;> norm_num [A, B]

-- matrix1:mul
example : A * B = !![4, 4; 10, 8] := by
  ext i j
  fin_cases i <;> fin_cases j <;> norm_num [A, B, Matrix.mul_apply, Fin.sum_univ_succ]

-- matrix1:scale
example : (3 : ℝ) • A = !![3, 6; 9, 12] := by
  ext i j
  fin_cases i <;> fin_cases j <;> norm_num [A]

-- matrix1:transpose
example : Matrix.transpose A = !![1, 3; 2, 4] := by
  ext i j
  fin_cases i <;> fin_cases j <;> norm_num [A]

-- matrix1:determinant
example : A.det = -2 := by
  norm_num [A, Matrix.det_fin_two]

-- matrix1:is_inverse
example : IsMatrixInverse P P := by
  dsimp [IsMatrixInverse]
  constructor <;> ext i j <;> fin_cases i <;> fin_cases j <;>
    norm_num [P, Matrix.mul_apply, Fin.sum_univ_succ]

-- matrix1:rank
example : (1 : Mat2).rank = 2 := by
  simp

-- matrix1:mul_vec (the linear system A x = b)
example : Matrix.mulVec A x = b := by
  funext i
  fin_cases i <;> norm_num [A, x, b, Matrix.mulVec, dotProduct, Fin.sum_univ_succ]
