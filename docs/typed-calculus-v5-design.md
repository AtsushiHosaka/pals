# typed-calculus-v5: real-function limits and local interval calculus

This independent authoring profile fills first-year single-variable calculus
coverage. It preserves all v1–v4 source, registry and canonical bytes. The namespace
is `urn:pals:openmath:typed-calculus:v5`, with `typed5`/`calculus5` dictionaries.
Acceptance establishes closed typing only. Actual Lean compilation proves each
separate Lean target; alignment of natural language, XML and that target remains
an independently reviewed semantic obligation. No runtime activation, production
publication, certified translator or retrieval-precision result is asserted.

## Types and exact mathematical meaning

The only value carriers are Real (ℝ), Nat (ℕ including zero), and RealFunction
(ℝ→ℝ). Prop is distinct. Real lambda expressions bind a typed real variable.
Forall/exists bind declared types, and all variables must be in scope. Numerals
are explicit real casts or natural literals. Powers require Nat exponents;
negative, fractional and real-typed exponents are rejected. The isolated registry
lists each symbol's signature and meaning. Operators are mathematical functions
and predicates, never theorem names that hide assumptions.

- `has_deriv_at(f,a,u)` means `HasDerivAt f u a`: point precedes slope in XML.
- `deriv(f)` is Mathlib's total derivative function, equal to zero where f is
  not differentiable. A value of this operator alone proves no differentiability.
- `interval_integral(f,a,b)` is the total oriented volume interval integral.
  Its occurrence or equality to zero does not imply `IntervalIntegrable`.
  `interval_integrable` is a separate predicate. Negation, endpoint reversal,
  reflection and periodic-translation identities retain their total meanings.
- `continuous_on_closed(f,a,b)` uses Icc(a,b), empty when a>b.
  `continuous_on_unordered(f,a,b)` uses uIcc(a,b)=Icc(min a b,max a b).
  Interior derivative assumptions use explicit strict inequalities between
  min/max endpoints. Ordered open intervals and unordered intervals are distinct.
- `continuous_on_image(g,f,a,b)` means ContinuousOn g (f '' uIcc(a,b)); the
  outer function comes first. It is the actual image, not automatically the
  interval between the endpoint images, and f need not be monotone.
- `limit_punctured(f,a,u)` means Tendsto f (nhdsWithin a {a}ᶜ) (nhds u).
  It ignores the value f(a). `limit_left` and `limit_right` respectively use
  Iio(a) and Ioi(a). `limit_at_top(f,u)` has a real variable tending to +∞,
  unlike the natural-index sequence limits of v3. All limit targets are finite
  real values; infinite limits have no encoding here.
- `update_value(f,a,u)` is Function.update f a u: it changes only the value
  at a, and asserts neither continuity nor a limit.
- `monotone(f)` and `convex(f)` mean global Monotone f and ConvexOn ℝ univ f.
  `strict_convex` means StrictConvexOn ℝ univ f. Restricted monotonicity uses
  explicit closed or unordered domains. `local_min(f,a)` is an unconstrained
  IsLocalMin f a; boundary minima are not silently treated as interior minima.
- `periodic(f,c)` is Function.Periodic f c for any real c, including zero
  and negative periods. It does not assert c is a fundamental positive period.

The strict derivative / strict convexity card intentionally follows Mathlib's
criterion under continuity and StrictMono (deriv f). It does not assume global
differentiability: because a nondifferentiable point has total derivative zero,
strict increase permits at most one such point. This is a valid stronger
criterion and is stated explicitly in the natural-language card.

## New mathematical coverage and overlap audit

The main cards cover integral triangle and uniform bounds; strict positivity
and zero-integral characterization; weighted integral mean value; odd/even and
periodic symmetry; affine change of variables for integrable functions; absolute
and continuous-multiplier integrability; orientation and integral differences;
lower and two moving endpoints; interval-local integration by parts and
image-local substitution; inverse differentiation; strict increase; derivative
signs and convexity; second-derivative minimum and convexity tests; Darboux;
Cauchy's mean-value theorem without division; derivative difference-quotient
limits; polynomial/exponential and logarithmic asymptotics; right-hand
L'Hôpital under exact zero-limit and nonzero-derivative assumptions; compact
uniform continuity; monotone integrability; and convex secant bounds.

Function-limit cards separately cover punctured sum/product and quotient,
continuous outer composition, removable-singularity extension, squeeze, and
matching left/right limits. Sum and product share one card to avoid inflating
counts with parallel closure rules. Finite limits do not constrain point values.
Outer continuity in the composition theorem is deliberately stronger than an
outer punctured limit: with the latter one must also prevent the inner function
from repeatedly taking the outer basepoint.

Parameterized counterexample cards are actual Lean propositions, separate from
the authored negative-query fixtures. They distinguish a punctured limit from
continuity, zero integral from pointwise vanishing without nonnegativity, and
continuity from differentiability. Their real parameters vary location or values;
they are mathematical families, not a list of numerical substitutions.

The v1 reuse batch has integrability closure but no integral-value difference
identity. V2 has globally assumed parts/substitution and monotonicity; here the
parts rule allows endpoint nondifferentiability and substitution requires outer
continuity only on the source interval's image. The affine substitution rule
needs only integrability and retains the sign of the slope. These are weaker
premises/new conclusions, not renamed duplicates. V3 has sequence limits and
Taylor remainders, not real punctured function limits. V4 has multivariable
Fréchet/gradient statements, not these local univariate criteria. Tests reject
verbatim target/prose duplication; semantic overlap was also manually audited.

These are reusable general solutions and counterexample families. They do not
by themselves provide every exercise form, multi-step composition, difficulty
level or all textbooks' exercises. The coverage matrix is maintained separately.

## Guardrails and evidence

The validator checks exact namespace, cdbase, allowlisted symbol, attribute set,
arity, argument sort and closure. It rejects shadowing, duplicate names, unbound
variables, unsupported operators, malformed integer literals and rational casts.
Input limits are 64 KiB UTF-8, 4096 nodes, depth 64, 256 declarations per binder,
32 application arguments and bounded attribute lengths. Registry header and
symbol identities are fixed in source. Canonicalization follows validation and
normalizes bound-variable names; canonical validation requires exact bytes.

Tests include natural-exponent rejection, scopes/types/arity, resource bounds,
independent point/slope and image-order formulas, lower-endpoint sign, both
endpoint velocities, left/right/punctured limit direction, and all L'Hôpital
limit targets. The exact Lean bundle is compared with manifest serialization,
and witness/validator/registry SHA-256 hashes are checked.

The generator writes `import Mathlib` and the exact example targets/witnesses,
then invokes the existing pinned lake workspace with a 180-second timeout. Only
a successful compilation emits the JSON manifest. Evidence records toolchain,
mathlib revision and actual source hashes. No sorry, admit or added axiom is used.
Negative fixtures are authored candidate queries with counterexamples or precise
missing-premise explanations; their status explicitly does not claim retrieval
or embedding testing.

## Still outside this batch

Infinite target limits, general filter carriers, epsilon-delta limit exercises,
one-sided extended L'Hôpital forms, improper-integral convergence tests,
parameter-dependent integrands/differentiation under the integral, general
inverse existence/local bijectivity, numerical quadrature and error bounds,
non-natural real powers and inverse trigonometric branches beyond the existing
arctangent derivative are not claimed. Elementary explicit limits such as
sin(x)/x, full trigonometric substitution exercises and integration recurrences
remain candidates for a subsequent precise grammar extension or batch.
