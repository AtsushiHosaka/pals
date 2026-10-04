import Mathlib

-- manifest card: la_v3_nonadditive_norm_family
example {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V] [FiniteDimensional ℝ V] (x : V) (hx : x ≠ 0) : ‖x+(0-x)‖ ≠ ‖x‖+‖(0-x)‖ := by
  simp only [zero_sub, add_neg_cancel, norm_zero, norm_neg]
  have hp : 0 < ‖x‖ := norm_pos_iff.mpr hx
  linarith
