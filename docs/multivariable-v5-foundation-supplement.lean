import Mathlib

-- manifest card: mv_foundation_partial_value_criterion
example (n : ℕ) (f : (Fin n → ℝ) → ℝ) (A : (Fin n → ℝ) →L[ℝ] ℝ) (x : Fin n → ℝ) (i : Fin n) (c : ℝ) (hf : HasFDerivAt f A x) : HasDerivAt (fun t => f (Function.update x i t)) c (x i) ↔ c = A (Pi.single i 1) := by
  have hh : HasFDerivAt f A (Function.update x i (x i)) := by simpa using hf
  have hd := hh.comp_hasDerivAt (x i) (hasDerivAt_update x i (x i))
  constructor
  · intro hc
    exact hc.unique hd
  · intro he
    simpa [he] using! hd

-- manifest card: mv_foundation_zero_totalized_jacobian_counterexample
example (m n : ℕ) (i : Fin m) (j : Fin n) : ∃ f : (Fin m → ℝ) → (Fin n → ℝ), ¬DifferentiableAt ℝ f 0 ∧ ∀ r c, LinearMap.toMatrix' (fderiv ℝ f 0).toLinearMap r c = 0 := by
  let f : (Fin m → ℝ) → (Fin n → ℝ) := fun x _ => |x i|
  have hn : ¬DifferentiableAt ℝ f 0 := by
    intro h
    have hs : DifferentiableAt ℝ (fun t : ℝ => f (Pi.single i t) j) 0 := by
      have hp : DifferentiableAt ℝ (fun x => f x j) (Pi.single i (0 : ℝ)) := by
        simpa using (differentiableAt_pi.mp h) j
      simpa [Function.comp_def] using! hp.comp (0 : ℝ) (hasFDerivAt_single (𝕜 := ℝ) (E := fun _ : Fin m => ℝ) (i := i) (0 : ℝ)).differentiableAt
    apply not_differentiableAt_abs_zero
    simpa [f] using hs
  refine ⟨f,hn,?_⟩
  intro r c
  simp [fderiv_zero_of_not_differentiableAt hn]

-- manifest card: mv_foundation_jacobian_curve_velocity
example (m n : ℕ) (f : (Fin m → ℝ) → (Fin n → ℝ)) (c : ℝ → (Fin m → ℝ)) (u : Fin m → ℝ) (t : ℝ) (hf : DifferentiableAt ℝ f (c t)) (hc : HasDerivAt c u t) : ∃ g : ℝ → (Fin n → ℝ), (∀ s, g s = f (c s)) ∧ HasDerivAt g ((LinearMap.toMatrix' (fderiv ℝ f (c t)).toLinearMap).mulVec u) t := by
  refine ⟨fun s => f (c s),fun _ => rfl,?_⟩
  simpa only [LinearMap.toMatrix'_mulVec, ContinuousLinearMap.coe_coe] using! hf.hasFDerivAt.comp_hasDerivAt t hc

-- manifest card: mv_foundation_quadratic_hessian_criterion
example (n : ℕ) (B H : (Fin n → ℝ) →L[ℝ] (Fin n → ℝ) →L[ℝ] ℝ) (x : Fin n → ℝ) : HasFDerivAt (fun y => B y + B.flip y) H x ↔ H = B + B.flip := by
  have hd : HasFDerivAt (fun y => B y + B.flip y) (B+B.flip) x := B.hasFDerivAt.add B.flip.hasFDerivAt
  constructor
  · intro hh
    exact hh.unique hd
  · intro he
    simpa [he] using! hd

-- manifest card: mv_foundation_quadratic_hessian_missing_flip_counterexample
example (n : ℕ) (B : (Fin n → ℝ) →L[ℝ] (Fin n → ℝ) →L[ℝ] ℝ) (x u w : Fin n → ℝ) (hB : B u w ≠ 0) : ¬HasFDerivAt (fun y => B y + B.flip y) B x := by
  intro hh
  have hd : HasFDerivAt (fun y => B y + B.flip y) (B+B.flip) x := B.hasFDerivAt.add B.flip.hasFDerivAt
  have he := hh.unique hd
  have hv := congrArg (fun C : (Fin n → ℝ) →L[ℝ] (Fin n → ℝ) →L[ℝ] ℝ => C w u) he
  simp only [add_apply, ContinuousLinearMap.flip_apply] at hv
  apply hB
  linarith

-- manifest card: mv_foundation_lagrange_multiplier_from_direction
example (n : ℕ) (f g : (Fin n → ℝ) → ℝ) (A B : (Fin n → ℝ) →L[ℝ] ℝ) (x u : Fin n → ℝ) (he : IsLocalExtrOn g {y | f y = f x} x) (hf : HasStrictFDerivAt f A x) (hg : HasStrictFDerivAt g B x) (hu : A u ≠ 0) : ∃ c : ℝ, B = c • A ∧ c * A u = B u ∧ ∀ t : ℝ, t * A u = B u → t = c := by
  have hA : A ≠ 0 := by intro h; exact hu (by simp [h])
  obtain ⟨a,b,hne,heq⟩ := he.exists_multipliers_of_hasStrictFDerivAt_1d hf hg
  have hb : b ≠ 0 := by
    intro hb
    have haz : a • A = 0 := by simpa [hb] using heq
    have ha : a = 0 := (smul_eq_zero.mp haz).resolve_right hA
    exact hne (by simp [ha,hb])
  have he : B = (-a / b) • A := by
    ext v
    have hh := congrArg (fun C : (Fin n → ℝ) →L[ℝ] ℝ => C v) heq
    simp only [add_apply, smul_apply, smul_eq_mul, zero_apply] at hh ⊢
    field_simp
    nlinarith [hh]
  have hv : B u = (-a/b) * A u := by simpa only [smul_apply,smul_eq_mul] using congrArg (fun C : (Fin n → ℝ) →L[ℝ] ℝ => C u) he
  refine ⟨-a/b,he,hv.symm,?_⟩
  intro t ht
  exact mul_right_cancel₀ hu (ht.trans hv)

-- manifest card: mv_foundation_singular_constraint_counterexample
example (n : ℕ) (A : (Fin n → ℝ) →L[ℝ] ℝ) (u : Fin n → ℝ) (hu : A u ≠ 0) : ∃ f g : (Fin n → ℝ) → ℝ, IsLocalExtrOn g {y | f y = f 0} 0 ∧ HasStrictFDerivAt f (0 : (Fin n → ℝ) →L[ℝ] ℝ) 0 ∧ HasStrictFDerivAt g A 0 ∧ ∀ c : ℝ, A ≠ c • (0 : (Fin n → ℝ) →L[ℝ] ℝ) := by
  refine ⟨fun x => (A x)^2, fun x => A x, ?_, ?_, A.hasStrictFDerivAt, ?_⟩
  · left
    apply IsMinOn.localize
    intro y hy
    have hy0 : A y = 0 := by simpa using (sq_eq_zero_iff.mp (by simpa using hy))
    simp [hy0]
  · simpa using (A.hasStrictFDerivAt (x := (0 : Fin n → ℝ))).pow 2
  · intro c he
    apply hu
    have hh := congrArg (fun C : (Fin n → ℝ) →L[ℝ] ℝ => C u) he
    simpa using hh

-- manifest card: mv_foundation_exceptional_section_counterexample
example (m n : ℕ) (i : Fin m) (j : Fin n) (c : ℝ) (hc : c ≠ 0) :
 ∃ f : ((Fin m → ℝ) × (Fin n → ℝ)) → ℝ,
 MeasureTheory.Integrable f ∧ (∀ y, f (0,y) = c) ∧ ¬ MeasureTheory.Integrable (fun y => f (0,y)) := by
 letI : Nonempty (Fin m) := ⟨i⟩
 letI : Nonempty (Fin n) := ⟨j⟩
 let f : ((Fin m → ℝ) × (Fin n → ℝ)) → ℝ := fun z => if z.1 = 0 then c else 0
 have hae : f =ᵐ[MeasureTheory.volume] (fun _ => 0) := by
   apply MeasureTheory.ae_iff.mpr
   have hz : MeasureTheory.volume (({0} : Set (Fin m → ℝ)) ×ˢ (Set.univ : Set (Fin n → ℝ))) = 0 := by
     change ((MeasureTheory.volume : MeasureTheory.Measure (Fin m → ℝ)).prod (MeasureTheory.volume : MeasureTheory.Measure (Fin n → ℝ))) _ = 0
     rw [MeasureTheory.Measure.prod_prod]
     simp
   have hset : {z | ¬ f z = 0} = ({0} : Set (Fin m → ℝ)) ×ˢ (Set.univ : Set (Fin n → ℝ)) := by
     ext z
     simp [f,hc]
   rw [hset]
   exact hz
 refine ⟨f, (MeasureTheory.integrable_zero _ ℝ MeasureTheory.volume).congr hae.symm, ?_, ?_⟩
 · intro y; simp [f]
 · intro hh
   have hh' : MeasureTheory.Integrable (fun _ : Fin n → ℝ => c) := by simpa [f] using hh
   letI : MeasureTheory.IsFiniteMeasure (MeasureTheory.volume : MeasureTheory.Measure (Fin n → ℝ)) := (MeasureTheory.integrable_const_iff_isFiniteMeasure hc).mp hh'
   have hne := MeasureTheory.measure_ne_top (MeasureTheory.volume : MeasureTheory.Measure (Fin n → ℝ)) Set.univ
   have hv : MeasureTheory.volume (Set.univ : Set (Fin n → ℝ)) = ⊤ := by
     change (MeasureTheory.Measure.pi (fun _ : Fin n => (MeasureTheory.volume : MeasureTheory.Measure ℝ))) Set.univ = ⊤
     rw [MeasureTheory.Measure.pi_univ]
     simp [Nat.ne_of_gt (Nat.zero_lt_of_lt j.isLt)]
   exact hne hv
