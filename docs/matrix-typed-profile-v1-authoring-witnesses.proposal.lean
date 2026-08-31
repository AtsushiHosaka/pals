import Mathlib

abbrev Mat2 (K : Type*) := Matrix (Fin 2) (Fin 2) K
abbrev Vec2 (K : Type*) := Fin 2 → K

def A {K : Type*} [Field K] : Mat2 K := !![1, 2; 3, 4]
def B {K : Type*} [Field K] : Mat2 K := !![2, 0; 1, 2]
def P {K : Type*} [Field K] : Mat2 K := !![0, 1; 1, 0]
def x {K : Type*} [Field K] : Vec2 K := ![2, -1]
def b {K : Type*} [Field K] : Vec2 K := ![0, 2]

def IsMatrixInverse {K : Type*} [Field K] (M N : Mat2 K) : Prop := M * N = 1 ∧ N * M = 1

example : ∀ {K : Type*} [Field K], A (K := K) + B (K := K) = (!![3, 2; 4, 6] : Mat2 K) := by
  intro K _
  ext i j
  fin_cases i <;> fin_cases j <;> simp [A, B] <;> ring

example : ∀ {K : Type*} [Field K], A (K := K) * B (K := K) = (!![4, 4; 10, 8] : Mat2 K) := by
  intro K _
  ext i j
  fin_cases i <;> fin_cases j <;> simp [A, B, Matrix.mul_apply, Fin.sum_univ_succ] <;> ring

example : ∀ {K : Type*} [Field K], (3 : K) • A (K := K) = (!![3, 6; 9, 12] : Mat2 K) := by
  intro K _
  ext i j
  fin_cases i <;> fin_cases j <;> simp [A] <;> ring

example : ∀ {K : Type*} [Field K], Matrix.transpose (A (K := K)) = (!![1, 3; 2, 4] : Mat2 K) := by
  intro K _
  ext i j
  fin_cases i <;> fin_cases j <;> simp [A]

example : ∀ {K : Type*} [Field K], IsMatrixInverse (P (K := K)) (P (K := K)) := by
  intro K _
  dsimp [IsMatrixInverse]
  constructor <;> ext i j <;> fin_cases i <;> fin_cases j <;>
    simp [P, Matrix.mul_apply, Fin.sum_univ_succ]

example : ∀ {K : Type*} [Field K], (1 : Mat2 K).rank = 2 := by
  intro K _
  simp

example : ∀ {K : Type*} [Field K], (A (K := K)).det = (-2 : K) := by
  intro K _
  simp [A, Matrix.det_fin_two]
  ring

example : ∀ {K : Type*} [Field K], Matrix.mulVec (A (K := K)) (x (K := K)) = b (K := K) := by
  intro K _
  funext i
  fin_cases i <;> simp [A, x, b, Matrix.mulVec, dotProduct, Fin.sum_univ_succ]
  all_goals ring
