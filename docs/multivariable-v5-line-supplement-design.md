# Parameterized line-integral supplement to multivariable v5

This append-only supplement contains four general Lean propositions under the
unchanged `typed-multivariable-v5` profile. The previous 32-card manifest,
validator, registry, and existing DB rows are not modified. Both old and new
manifests load separately with the same profile binding. Authoring status remains
`local_authoring_evidence_bound_not_admitted`.

## Mathematical scope

1. **Orientation recognition.** For an actual differentiable parameterized curve
   and any scalar one-form field, interval integrability is invariant under
   reversal of the endpoints, while the oriented scalar pullback integral is
   negated. The value identity uses Mathlib's total integral and does not imply
   existence of an integrable pullback. The extra actual-velocity premise keeps
   the mathematical interpretation as a line integral; the integral identity
   itself holds for every scalar pullback.
2. **Parameter interval splitting.** A fixed curve and field give the same
   pullback on both subintervals. Separate integrability assumptions justify
   additivity across the splitting point, with no ordering assumption on the
   three endpoints. Again the curve derivative premise gives its geometric
   interpretation, while the analytic proof uses the scalar interval theorem.
3. **Parameterized orientation counterexample.** In arbitrary dimension n with
   chosen coordinate i, change just that coordinate of any base vector to t.
   Its actual derivative is e_i. The coordinate potential has derivative dx_i,
   whose application to this velocity is 1. Its integrals a..b and b..a are
   b-a and a-b and differ whenever a≠b. The chosen Fin n coordinate excludes
   n=0 by an empty binder, rather than assuming a nonexistent coordinate. This
   is a genuine Lean counterexample family, not only a hard-negative annotation.
4. **Bilinear integration by parts for two curves.** Given any continuous
   bilinear real form B, actual velocities c′=u and d′=w, and separate
   integrability of B(c,w) and B(u,d), their integral sum is the endpoint
   difference of B(c,d). No symmetry of B is assumed. The explicit one-form
   field D is constrained pointwise by D(x)(y)=B(x,y).

## OpenMath alignment

The existing `pullback_one_form(n,D,c,u)` denotes exactly the real function
`t ↦ D(c(t))(u(t))`; it does not independently certify u as c's velocity.
Thus the bilinear card deliberately uses contractions (D,c,w) and (D,u,d).
Their actual derivative relationships are c′=u and d′=w, stated separately.
It does not incorrectly call w the velocity of c or d the velocity of u.
The two slots of B are preserved throughout, even for nonsymmetric B.

The orientation identity encodes negation as `real_sub(0, integral)`; the
integrability equivalence retains both endpoints in their exact order. The
counterexample constructs its field using `scalar_fderiv_field(projection)`
and its path using `update_curve`, with no opaque theorem-name operation or
new dictionary symbol. Every dimension-dependent term uses the same n.

## Overlap and curriculum classification

The orientation and splitting cards are explicitly **geometric applications of
existing one-variable interval-integral laws**, not independent new analytic
principles. Their XML now includes arbitrary-dimensional curves, fields and
actual velocities, making the parameterized hypotheses visible to retrieval.
They are classified introductory. This limited curriculum specialization is
not represented as a novel theorem or a broad surface-integral result.

The orientation counterexample supplies a previously missing geometric
counterexample form at standard difficulty. Bilinear curve integration by
parts combines actual velocities, a bilinear derivative, integrability,
linearity, and endpoint evaluation; it is classified standard, not advanced.
No old Lean target or canonical XML is duplicated within the profile.

Proposed bindings in the companion JSON fill recognize, justify_prove,
counterexample_audit, and synthesize modes, plus introductory and an additional
standard slot. **The advanced slot is left unfilled by this supplement.**
Surface measures, normal vectors, surface area elements, Stokes/Green/divergence
theorems, and arbitrary reparameterization invariance are outside this unchanged
profile. Four line-integral propositions cannot establish that the whole
line-and-surface-integrals chapter is covered.

## Evidence

- All four exact final anonymous Lean examples compiled successfully under
  the repository-pinned toolchain and mathlib revision in the manifest.
- Final source is the strict expansion-manifest serialization, without
  hidden declarations, axioms, sorry, admit, extra namespaces or options.
- Four independently formulated negative questions have mathematical
  counterexamples, paired one-to-one with the cards.
- Nine focused source/profile/role/negative/binding tests pass; combined with
  the unchanged 68 closed-profile tests, **77 tests pass**.
- Ruff formatting/checks pass. Generator execution reproduces manifest cards.
- Original and supplement loader results share the exact profile binding;
  immutable validator and registry hashes match the previous manifest.
- No retrieval-precision, production admission, runtime activation or DB write
  claim is made by this authoring task.

## Final hashes

- `docs/multivariable-v5-line-supplement-batch.json`: `sha256:e0566f1ab065b592cce08d8e30418138b2740282dcf89a5befeb6eb34d8338cf`
- `docs/multivariable-v5-line-supplement-batch.lean`: `sha256:a6d994adac02cef700bd9f0aa06aafc66ffe87331aeb66f8164686dafadafa7b`
- `docs/multivariable-v5-line-supplement-negatives.json`: `sha256:cadf1923d3572fcc21b7ea510b723c9a96633a1e22b09bded742ed413e03639d`
- `docs/multivariable-v5-line-supplement-proposed-bindings.json`: `sha256:664ebb6bd60486e48be4c5c574c3c3016bafe3bc25037cba4498bfad30f4701a`
