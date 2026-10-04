# Targeted multivariable foundation supplements

These two append-only manifests add 13 general theorem cards using the frozen `typed-multivariable-v5` and `typed-calculus-v4` profiles. Existing validators, registries, batches, database rows, and the shared coverage matrix are unchanged by this work. The generator compiles each exact Lean bundle before emitting its manifest and pins the existing validator, registry, witness, Lean toolchain, and Mathlib revision. Both original manifests and both supplements independently pass the strict expansion loader under their respective shared profile IDs.

The immediate purpose is to fill explicitly identified problem-form and difficulty gaps, not increase an undifferentiated theorem count. The proposed bindings in `multivariable-foundation-supplement-bindings.json` are recommendations for parent review. They are not database admissions or runtime routing claims.

## Mathematical distinctions and overlap audit

* The partial-value and quadratic-Hessian recognition cards establish **if and only if** certificates for a proposed derivative using uniqueness. Earlier cards establish the actual derivative; they do not characterize arbitrary proposed candidates. These are recognition adaptations of existing mathematics, not claims of wholly new subject areas.
* The totalized-Jacobian counterexample is a general nondifferentiable absolute-coordinate map in arbitrary nonempty dimensions. A zero Lean `fderiv` matrix is not an actual derivative witness. The curve-velocity card combines a genuine derivative premise, curve differentiation, and correctly ordered Jacobian action.
* The missing-flip Hessian counterexample needs an explicit nonzero value of the bilinear form. It does not incorrectly reject the zero form. Its paired recognition theorem includes the transpose term even when the original presentation is nonsymmetric.
* The directional Lagrange card refines the earlier existence result into a unique scalar equation `c A(u) = B(u)` with `A(u) ≠ 0`. The singular-constraint counterexample proves why normalization fails for `(A x)² = 0`; it does not contradict the unnormalized multiplier theorem.
* The exceptional-section theorem is a genuinely product-integrable function with a nonintegrable section through zero, for arbitrary positive coordinate dimensions and nonzero amplitude. A measure-zero exceptional hyperplane accounts for the difference between almost every section and every section.
* The stationary-point and nondifferentiable-minimum counterexamples separate two different failed converses of Fermat. Negative scaled squared norms refute sufficiency of a zero gradient; the norm refutes automatic differentiability at a minimum.
* Positive scaled squared norms have a unique local-minimizer location. Nonnegative scaled squared norms have a constructed global minimum, permitting coefficient zero and consequently nonuniqueness. The two conclusions answer recognition and construction tasks with different hypotheses.
* The exact-residual theorem combines an affine residual, nonnegative squared norm, and its derivative to obtain global/local optimality and zero gradient at any supplied exact solution. It does not solve inconsistent least-squares systems or claim uniqueness. Its synthesis/advanced label is relative to the initial multivariable curriculum: it combines linear maps between arbitrary finite-dimensional spaces, optimization, and a derivative chain, rather than asserting a difficult Lean proof.

No literal canonical-XML duplicates occur within either supplement or against its original same-profile manifest. Mathematical overlap with original derivative, Hessian, and Lagrange primitives is intentional and documented above; there is no variable-renaming or numerical-exponent enumeration. Scalars, dimensions, bilinear forms, functions, and linear maps remain parameterized. The six counterexample cards are regular Lean-verified theorem cards; the separate 13 negative examples only test admission/retrieval reasoning and do not count toward a curriculum counterexample slot by themselves.

## Semantics retained from the frozen dictionaries

`has_curve_deriv(n,c,t,u)` means `HasDerivAt c u t`; `has_gradient(E,f,x,g)` means `HasGradientAt f g x`. Standard Jacobian rows are output coordinates and columns are input coordinates. `local_extr_fiber(n,g,f,x)` is the local extremum of objective `g` on the constraint level `f=f(x)`. `quadratic_field(B)` is `x ↦ B x + B.flip x`, and its derivative candidate has bilinear type. The right product section fixes the first block. RealInnerProductSpace includes real inner-product and finite-dimensional assumptions; counterexamples additionally supply a nonzero vector or coordinate index where nontriviality is needed.

The residual is encoded as the squared norm composed with the affine map `y ↦ A y + (0-b)`, definitionally the displayed `‖A y-b‖²`. Its exact-solution hypothesis is mandatory. No new symbol or untyped theorem-name predicate has been introduced.

## Proposed coverage impact

Against `output/foundation-expansion-v6-20260930/baseline-after-curation.json`, and **only if** all proposed bindings pass the parent's classification review, multivariable mode slots rise from 26/50 to 39/50 and difficulty slots from 26/40 to 31/40. Seven of ten chapter contracts become satisfied: partials, total-Jacobian, gradient, Hessian/Taylor, extrema, Lagrange, multiple integrals. This is a projection from explicit bindings, not a new authoritative matrix audit or evidence that arbitrary exercises are solved.

Remaining gaps are deliberately not populated:

| Chapter | Missing modes | Missing difficulty slots |
|---|---|---|
| Change of variables | justify/prove, counterexample/audit, synthesize | introductory 1, standard 2 |
| Line and surface integrals | recognize, justify/prove, counterexample/audit, synthesize | introductory 1, standard 1, advanced 1 |
| Vector-calculus integral theorems | recognize, compute/construct, justify/prove, counterexample/audit | introductory 1, standard 1, advanced 1 |

The existing potential line-integral cards do not establish integration over general surfaces, Green, Stokes, or divergence theorems. This supplement makes no claims about those topics. Negative reasoning cases are authored candidates, not results of retrieval tests. Runtime problem execution, automatic instantiation, and catalog publication were not tested here.

## Validation

Both generated Lean bundles compiled successfully using the pinned existing workspace. Nineteen targeted Python tests pass, covering both same-profile original/supplement loader paths, exact bundle hashes, reproducibility from the generator, explicit bindings, negative pairing, no literal XML duplicates, semantic argument slots, dependent dimension rejection, unbound variables, arity errors, and mismatched Lean witness evidence. Ruff passes for both new Python files. Existing manifests and profile bytes remain unchanged.
