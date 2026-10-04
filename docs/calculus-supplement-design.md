# Single-variable calculus curriculum supplements

## Scope and immutable profiles

This append-only supplement adds **24 different general propositions**: 15 under
`typed-calculus-v5` and 9 under `typed-calculus-v3`. It introduces no new profile,
registry, operator, carrier, or change to existing records. The closed dictionaries
and validator source hashes are exactly those of their original manifests.
The existing local authoring loader accepts each original and supplement
independently with the same profile binding. This is authoring evidence, not
production admission, runtime activation, or a measured retrieval-accuracy gain.

Both bundles were actually compiled with the repository-pinned Lean/mathlib
before manifest emission. Their source is the exact expansion-batch serialization:
`import Mathlib`, followed only by each card identifier comment and anonymous
example target/witness. No auxiliary axioms, sorry, admission substitutions,
extra imports, or hidden helper declarations are present. Each card has a genuine
4–6-step mathematical outline and a paired invalid candidate with an explanation.

## Semantic constraints and boundary cases

- XML `has_deriv_at(f, point, slope)` lowers to Lean `HasDerivAt f slope point`.
  The difference-quotient extension explicitly inserts its derivative value at
  zero. It is not merely the old arbitrary removable-singularity statement:
  its value is determined from differentiation and it constructs the quotient.
- Real interval integrals are total, oriented Lebesgue integrals. Their values
  alone do not imply integrability. The FTC synthesis has an explicit integrability
  premise; the exponential moment integrand is proved continuous and integrable.
  A nonzero singleton spike has every interval integral zero, while its value
  at the spike is nonzero: this is a Lean-proved failure of pointwise FTC when
  continuity is omitted, not just an auxiliary negative-question example.
- The MVT counterexample has zero derivative throughout the interior and a
  discontinuous right endpoint; the nonzero endpoint slope cannot be attained.
  The quadratic MVT construction works for arbitrary a<b and c,d, including c=0.
  The constant-slope corollary retains exactly closed-interval continuity and
  open-interior derivative hypotheses.
- The quantitative minimization result assumes f′=h, h(a)=0, c>0, and
  h(y)-h(x)≥2c(y-x) for x≤y. Subtracting c(x-a)² gives a function with monotone
  derivative; convexity and stationarity yield global quadratic growth. This
  strengthens the earlier local positive-second-derivative minimum criterion
  by an explicit global bound, rather than duplicating that criterion.
- Natural degrees include zero. Taylor polynomials and higher derivatives use
  the fixed domain uIcc(a,b). The bounded-error card assumes a≤b, C^(n+1)
  regularity, a derivative bound throughout [a,b], and an evaluation point in
  that interval. Its valid estimate has denominator **n!**, deliberately not a
  falsely sharp (n+1)! constant. The arbitrary-degree monomial counterexample
  has all degree≤n coefficients zero and positive value at b>0.
- `sequence_limit` means ordered Nat-index convergence. `has_sum` and `summable`
  mean Mathlib unconditional summation (equivalent to absolute convergence for
  real series). The power-series inward-convergence hypothesis is convergence
  of **ordered partial sums**, so a conditionally convergent boundary is allowed;
  its conclusion is unconditional convergence strictly inside. Equality of
  radii is explicitly excluded. Neither alternating convergence nor arbitrary
  ordered convergence is mislabeled as HasSum.
- The harmonic family is indexed from zero using total real division; changing
  that single term affects neither its zero term limit nor its nonsummability.
  The geometric error estimate proves summability and a quantitative tail bound,
  with denominator 1-q and 0≤q<1. It is more than an application of the term test.
- The derivative of the geometric sum is proved using equality to 1/(1-x) on
  an open neighborhood inside |x|<1. It makes no claim of a generic theorem
  allowing unrestricted interchange of derivatives and infinite sums.

## Overlap and difficulty audit

All earlier calculus v1–v5 canonical statements were inspected. No new card
repeats an old Lean target or same-profile canonical XML. Counterexamples are
parameterized mathematical families, not numerical or renamed duplicates.
The absolute-value factor reuses an old nondifferentiability fact only as a
component of a new failure of the converse product rule. The Taylor monomial
has arbitrary degree, and the integration example has arbitrary exponential
slope and endpoints. Existing L’Hôpital and geometric-series evaluation cards
are reused by the parent coverage matrix rather than reissued here.

A standard first-year argument is not relabeled advanced merely because its
Lean proof needs tactics. Four proposed advanced cards combine substantive
ideas: quantitative convex optimization, summability plus certified tail error,
conditional-boundary/absolute-interior power-series convergence, and local
identification plus differentiation of an infinite sum. Proposed bindings are
review suggestions; the parent owns actual inventory and chapter decisions.

| Card suffix | Chapter | Primary mode | Difficulty |
| --- | --- | --- | --- |
| calculus_supp_v5_difference_quotient_extension | univ.calculus.continuity | compute_construct | standard |
| calculus_supp_v5_product_converse_counterexample | univ.calculus.derivative-rules | counterexample_audit | standard |
| calculus_supp_v5_exp_quotient_derivative | univ.calculus.derivative-rules | synthesize | standard |
| calculus_supp_v5_primitives_constant_difference | univ.calculus.ftc | recognize | standard |
| calculus_supp_v5_quadratic_unique_minimum | univ.calculus.extrema | compute_construct | standard |
| calculus_supp_v5_stationary_not_minimum | univ.calculus.extrema | counterexample_audit | standard |
| calculus_supp_v5_convex_stationary_global_minimum | univ.calculus.extrema | synthesize | standard |
| calculus_supp_v5_scale_integrability_equivalence | univ.calculus.integration-methods | recognize | standard |
| calculus_supp_v5_exp_product_ftc | univ.calculus.ftc | synthesize | standard |
| calculus_supp_v5_exponential_moment_integral | univ.calculus.integration-methods | synthesize | standard |
| calculus_supp_v5_ftc_point_spike_counterexample | univ.calculus.ftc | counterexample_audit | standard |
| calculus_supp_v5_mvt_endpoint_counterexample | univ.calculus.mean-value | counterexample_audit | standard |
| calculus_supp_v5_quadratic_mean_value_point | univ.calculus.mean-value | compute_construct | standard |
| calculus_supp_v5_mvt_constant_slope_recognition | univ.calculus.mean-value | recognize | standard |
| calculus_supp_v5_strong_derivative_growth_minimum | univ.calculus.extrema | synthesize | advanced |
| calculus_supp_v3_taylor_at_center | univ.calculus.taylor | recognize | introductory |
| calculus_supp_v3_taylor_uniform_remainder_bound | univ.calculus.taylor | synthesize | standard |
| calculus_supp_v3_finite_taylor_not_exact | univ.calculus.taylor | counterexample_audit | standard |
| calculus_supp_v3_harmonic_term_test_counterexample | univ.calculus.series | counterexample_audit | standard |
| calculus_supp_v3_geometric_majorant_error | univ.calculus.series | synthesize | advanced |
| calculus_supp_v3_power_series_interior_convergence | univ.calculus.power-series | recognize | advanced |
| calculus_supp_v3_weighted_geometric_sum | univ.calculus.power-series | compute_construct | standard |
| calculus_supp_v3_geometric_boundary_counterexample | univ.calculus.power-series | counterexample_audit | standard |
| calculus_supp_v3_geometric_sum_derivative | univ.calculus.power-series | synthesize | advanced |

The supplement directly supplies every currently missing mode in continuity,
mean-value, extrema, Taylor, FTC, integration methods, series, and power series.
Derivative rules receive counterexample and synthesis cards; its proof-mode gap
can use the existing general derivative-uniqueness card. Limits are already
covered by the parent's existing L’Hôpital binding. The newly proposed advanced
extrema and series cards fill the corresponding advanced gaps; Taylor obtains
two new standard cards and power series obtains two standard and two advanced.
These are proposed contract cells, not a claim that every textbook exercise has
been covered. General analytic continuation, arbitrary-series termwise
integration/differentiation, and a general convergence-radius operator remain
outside these two unchanged dictionaries.

## Verification

- Both new bundles compiled successfully with `lake env lean`.
- 11 focused supplement tests pass, covering exact source/hash binding,
  same-profile original+supplement loading, negative pairing, reproducible card
  generation, nonduplication, closed failure on altered evidence/source,
  derivative argument roles, n! remainder, strict inward convergence with ordered
  partial sums, and the complete certified geometric remainder expression.
- Combined existing v3/v5 closed-grammar tests plus supplement tests: **75 pass**.
- Ruff formatting and checks pass for both generators and the new test file.
- The shared loader reports `local_authoring_evidence_bound_not_admitted`.
  No inference of review, runtime verification, or production publication is made.

### Final artifact hashes

- `docs/calculus-v5-supplement-batch.json`: `sha256:6295b44563b88c2ab6ec9e3b400fc9fb00aeffb1565ebe569224d72aa5d52081`
- `docs/calculus-v5-supplement-batch.lean`: `sha256:e4df3a4730b85758b6d2bc6083cfbf7288ce85fc756a3b79a09c8dccd76cec1a`
- `docs/calculus-v5-supplement-negatives.json`: `sha256:630e3de675c4f6c650af8e1bccd4ad04adc81e4bf7b38717858a1d2ee5460e0b`
- `docs/calculus-v3-supplement-batch.json`: `sha256:4f801c81e10b3ba9f576336c748c9e62758c3584d979b6d60a6c2f44579caa90`
- `docs/calculus-v3-supplement-batch.lean`: `sha256:3640e94e1b55142219f7cf6b5bb0d88cdf53438cea0fcda45409e95dfd5b105f`
- `docs/calculus-v3-supplement-negatives.json`: `sha256:4a0cafc0b0f503346154634c93a8734be029d97b8c605097f6789d48e44f79f2`
