#!/usr/bin/env python3
"""Create locally compiled Lean witnesses for the typed-extension proposal.

This companion deliberately keeps only propositions with a direct, checked
Mathlib formulation.  It neither claims that the proposed OpenMath extension
exists nor modifies a Draft database.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROPOSAL = ROOT / "docs/algebra-calculus-typed-extension-draft-proposal.json"


def witness(target: str, proof: str, note: str) -> dict[str, str]:
    return {
        "lean_target": target,
        "lean_witness": f"example : {target} := {proof}",
        "lean_formalization_note": note,
    }


WITNESSES: dict[str, dict[str, str]] = {
    "ext_group_inverse_product": witness(
        "∀ {G : Type*} [Group G] (a b : G), (a * b)⁻¹ = b⁻¹ * a⁻¹",
        "by\n  intro G _ a b\n  exact mul_inv_rev a b",
        "The carrier-indexed abstract group is represented directly by Lean's `Group G`.",
    ),
    "ext_group_left_cancellation": witness(
        "∀ {G : Type*} [Group G] (a b c : G), a * b = a * c → b = c",
        "by\n  intro G _ a b c h\n  exact mul_left_cancel_iff.mp h",
        "Lean's equality is homogeneous in the group carrier.",
    ),
    "ext_group_left_equation_solution": witness(
        "∀ {G : Type*} [Group G] (a b : G), ∃! x : G, a * x = b",
        "by\n  intro G _ a b\n  refine ⟨a⁻¹ * b, ?_, ?_⟩\n  · simp\n  · intro y hy\n    calc\n      y = a⁻¹ * (a * y) := by group\n      _ = a⁻¹ * b := by rw [hy]",
        "`∃! x : G` gives the required carrier-restricted quantifier.",
    ),
    "ext_group_conjugation_automorphism": witness(
        "∀ {G : Type*} [Group G] (g : G), Function.Bijective (fun x : G => g * x * g⁻¹) ∧ ∀ x y : G, g * (x * y) * g⁻¹ = (g * x * g⁻¹) * (g * y * g⁻¹)",
        "by\n  intro G _ g\n  constructor\n  · constructor\n    · intro x y h\n      change g * x * g⁻¹ = g * y * g⁻¹ at h\n      calc\n        x = g⁻¹ * (g * x * g⁻¹) * g := by group\n        _ = g⁻¹ * (g * y * g⁻¹) * g := by rw [h]\n        _ = y := by group\n    · intro y\n      refine ⟨g⁻¹ * y * g, ?_⟩\n      group\n  · intro x y\n    group",
        "The conjunction expands the `GroupAut` claim into the two properties needed by the Draft.",
    ),
    "ext_group_hom_kernel_normal": witness(
        "∀ {G H : Type*} [Group G] [Group H] (f : G →* H), f.ker.Normal",
        "by\n  intro G H _ _ f\n  exact MonoidHom.normal_ker f",
        "`G →* H` carries the homomorphism's domain and codomain; `ker` is therefore typed.",
    ),
    "ext_commutative_ring_binomial_square": witness(
        "∀ {R : Type*} [CommRing R] (a b : R), (a + b)^2 = a^2 + 2 * a * b + b^2",
        "by\n  intro R _ a b\n  ring",
        "Numeral coercion and commutative-ring operations are resolved by `CommRing R`.",
    ),
    "ext_commutative_ring_difference_squares": witness(
        "∀ {R : Type*} [CommRing R] (a b : R), (a - b) * (a + b) = a^2 - b^2",
        "by\n  intro R _ a b\n  ring",
        "Subtraction is the additive-group operation supplied by `CommRing R`.",
    ),
    "ext_integral_domain_cancellation": witness(
        "∀ {R : Type*} [CommRing R] [IsDomain R] (a b c : R), a ≠ 0 → a * b = a * c → b = c",
        "by\n  intro R _ _ a b c ha h\n  have hzero : a * (b - c) = 0 := by rw [mul_sub, h, sub_self]\n  have hsub : b - c = 0 := (mul_eq_zero.mp hzero).resolve_left ha\n  exact sub_eq_zero.mp hsub",
        "`IsDomain R` is the no-zero-divisors assumption needed for cancellation.",
    ),
    "ext_polynomial_factor_theorem": witness(
        "∀ {K : Type*} [Field K] (p : Polynomial K) (a : K), p.eval a = 0 ↔ Polynomial.X - Polynomial.C a ∣ p",
        "by\n  intro K _ p a\n  simpa [Polynomial.IsRoot] using (Polynomial.dvd_iff_isRoot (p := p) (a := a)).symm",
        "The coefficient field and polynomial sort are `K` and `Polynomial K`; `eval` is type-indexed by K.",
    ),
    "ext_polynomial_division_algorithm": witness(
        "∀ {K : Type*} [Field K] (p q : Polynomial K), q ≠ 0 → ∃ s r : Polynomial K, p = q * s + r ∧ r.degree < q.degree",
        "by\n  intro K _ p q hq\n  refine ⟨p / q, p % q, ?_, Polynomial.degree_mod_lt p hq⟩\n  exact (EuclideanDomain.div_add_mod p q).symm",
        "This is the existence-and-degree-bound component of division; the full uniqueness formulation remains in the extension proposal but is not claimed by this witness.",
    ),
    "ext_polynomial_root_bound": witness(
        "∀ {K : Type*} [Field K] (p : Polynomial K), p.roots.card ≤ p.natDegree",
        "by\n  intro K _ p\n  exact Polynomial.card_roots' p",
        "Mathlib counts roots with multiplicity, which is stronger than the proposed distinct-root upper bound.",
    ),
    "ext_polynomial_degree_product": witness(
        "∀ {R : Type*} [CommRing R] [IsDomain R] (p q : Polynomial R), p ≠ 0 → q ≠ 0 → (p * q).natDegree = p.natDegree + q.natDegree",
        "by\n  intro R _ _ p q hp hq\n  exact Polynomial.natDegree_mul hp hq",
        "The nonzero premises avoid the designated natural degree of the zero polynomial.",
    ),
    "ext_polynomial_formal_derivative_product_rule": witness(
        "∀ {R : Type*} [CommRing R] (p q : Polynomial R), Polynomial.derivative (p * q) = Polynomial.derivative p * q + p * Polynomial.derivative q",
        "by\n  intro R _ p q\n  exact Polynomial.derivative_mul",
        "`Polynomial.derivative` is the formal derivative, not an analytic derivative.",
    ),
    "ext_multivar_chain_rule": witness(
        "∀ {E F G : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E] [NormedAddCommGroup F] [NormedSpace ℝ F] [NormedAddCommGroup G] [NormedSpace ℝ G] (f : E → F) (g : F → G) (x : E) (fprime : E →L[ℝ] F) (gprime : F →L[ℝ] G), HasFDerivAt f fprime x → HasFDerivAt g gprime (f x) → HasFDerivAt (g ∘ f) (gprime ∘SL fprime) x",
        "by\n  intro E F G _ _ _ _ _ _ f g x fprime gprime hf hg\n  exact hg.comp x hf",
        "This is a dimension-independent Frechet-derivative form of the proposed Euclidean chain rule.",
    ),
    "ext_multivar_scalar_product_rule": witness(
        "∀ {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E] (f g : E → ℝ) (x : E) (fprime gprime : E →L[ℝ] ℝ), HasFDerivAt f fprime x → HasFDerivAt g gprime x → HasFDerivAt (f * g) (f x • gprime + g x • fprime) x",
        "by\n  intro E _ _ f g x fprime gprime hf hg\n  exact hf.mul hg",
        "Pointwise multiplication of scalar-valued functions is the multivariable product rule in Frechet form.",
    ),
    "ext_multivar_interior_extremum_gradient_zero": witness(
        "∀ {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E] (f : E → ℝ) (x : E), IsLocalExtr f x → fderiv ℝ f x = 0",
        "by\n  intro E _ _ f x h\n  exact h.fderiv_eq_zero",
        "For Euclidean finite-dimensional E, `fderiv ℝ f x = 0` is the type-correct Lean representation of zero gradient. The original differentiability premise is stronger than needed by this theorem.",
    ),
    "ext_multivar_fubini_rectangle": witness(
        "∀ {α β E : Type*} [MeasurableSpace α] [MeasurableSpace β] {μ : MeasureTheory.Measure α} {ν : MeasureTheory.Measure β} [MeasureTheory.SFinite μ] [MeasureTheory.SFinite ν] [NormedAddCommGroup E] [NormedSpace ℝ E] (f : α × β → E), MeasureTheory.Integrable f (μ.prod ν) → (∫ z : α × β, f z ∂(μ.prod ν)) = ∫ x : α, ∫ y : β, f (x, y) ∂ν ∂μ",
        "by\n  intro α β E _ _ μ ν _ _ _ _ f hf\n  exact MeasureTheory.integral_prod f hf",
        "This is the measure-theoretic Fubini core. A typed extension must additionally establish integrability from continuity on a declared rectangle.",
    ),
}


EXCLUSIONS: dict[str, str] = {
    "ext_multivar_gradient_directional_derivative": "The pinned Mathlib workspace does not expose a canonical general `gradient` operator matching the proposed Euclidean typed signature; a witness using only `fderiv` would change the Draft target.",
    "ext_multivar_mixed_partials_schwarz": "A direct, checked C²-on-open-set mixed-partial theorem needs a dedicated multivariable smoothness formulation and was not found without weakening the statement.",
    "ext_multivar_positive_hessian_strict_minimum": "The exact positive-definite Hessian to strict-local-minimum theorem needs a compatible Hessian and second-order Taylor API; no direct witness was established in the pinned workspace.",
    "ext_multivar_lagrange_multiplier": "The proposed regular-level-set Lagrange multiplier statement requires a manifold/tangent-space formalization beyond a direct local Mathlib witness.",
    "ext_multivar_change_of_variables": "The exact C¹-diffeomorphism change-of-variables statement requires a measure/Jacobian theorem with the proposed typed-domain contract; it was not directly compiled.",
    "ext_ode_linear_first_order_ivp": "The integrating-factor formula requires an oriented-interval integral and ODE-solution API not present as one directly matching Mathlib statement.",
    "ext_ode_logistic_ivp": "A direct witness would require a separately formalized solution-domain invariant (0<y<K), logarithm branch conditions, and ODE solution predicate.",
    "ext_ode_picard_lindelof_local_existence_uniqueness": "The exact local-existence/uniqueness theorem requires a typed ODE RHS and locally-Lipschitz API; no direct pinned-workspace theorem was established.",
    "ext_ode_harmonic_oscillator_ivp": "The exact second-order IVP and uniqueness formulation requires a typed second-derivative/ODE solution interface; an explicit derivative calculation alone would not witness the stated uniqueness claim.",
}


def payload() -> dict[str, object]:
    proposal = json.loads(PROPOSAL.read_text(encoding="utf-8"))
    proposal_cards = {card["id"]: card for card in proposal["cards"]}
    if set(proposal_cards) != set(WITNESSES) | set(EXCLUSIONS):
        raise RuntimeError("companion partition does not cover the base proposal")
    verified = []
    for identifier in proposal_cards:
        if identifier not in WITNESSES:
            continue
        item = dict(proposal_cards[identifier])
        item.update(WITNESSES[identifier])
        item["lean_verification_status"] = "verified_local_pinned_workspace"
        verified.append(item)
    excluded = [
        {"id": identifier, "reason": EXCLUSIONS[identifier]}
        for identifier in proposal_cards
        if identifier in EXCLUSIONS
    ]
    if len(verified) != 17 or len(excluded) != 9:
        raise RuntimeError("unexpected companion counts")
    return {
        "schema_version": "pals.typed-extension-lean-companion.v1",
        "source_proposal": "docs/algebra-calculus-typed-extension-draft-proposal.json",
        "verification_scope": "local pinned Mathlib workspace only; no OpenMath profile or DB publication claim",
        "verified_cards": verified,
        "excluded_cards": excluded,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(payload(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
