# typed-calculus-v3: real sequences, series and finite Taylor theorems

This isolated authoring profile uses `urn:pals:openmath:typed-calculus:v3`,
`typed3` and `calculus3`. It does not change the v1/v2 validators or canonical
bytes. The initial batch contains 31 general results with compiled Lean witnesses.
It is local authoring evidence, not serving activation or a textbook-completeness
claim. Type acceptance is not a mathematical proof or a certified translation
between the XML and the separate Lean target; semantic comparison is required.

## Exact mathematical operations

The registry records signatures and semantics for every symbol. Real calculus
operations inherited from v2 retain their meanings in the new namespace; in
particular `has_deriv_at(f,a,m)` means `HasDerivAt f m a`. Real `power` takes a
natural exponent; `rpow` is a separate real-exponent operation. There are no
implicit Nat-to-Real coercions, opaque theorem-name propositions or free variables.

| Operation | Meaning and order |
| --- | --- |
| `RealSequence` | ℕ → ℝ, indexed from zero. |
| `sequence_lambda`, `sequence_apply` | One typed Nat binder returning Real; application at a Nat. |
| `nat_add`, `nat_factorial` | Natural addition and factorial, including 0!=1. |
| `sequence_limit(u,L)` | `Filter.Tendsto u Filter.atTop (nhds L)`. |
| `has_sum(u,L)` | Mathlib `HasSum u L`, convergence of finite-subset sums, **unconditional**, not merely the natural-order partial-sum limit. |
| `summable(u)` | Mathlib `Summable u`; for real sequences this requires absolute summability. |
| `partial_sum(u,n)` | `∑ i ∈ Finset.range n, u i`, indices 0 through n−1, zero when n=0. |
| `tsum(u)` | Mathlib's total infinite sum, zero if nonsummable. Its presence implies no convergence premise. |
| `rpow(x,p)` | `Real.rpow x p`, the precise total Mathlib operation. |
| `cont_diff_on(n,f,a,b)` | `ContDiffOn ℝ n f (Set.uIcc a b)`, unordered closed interval. |
| `iterated_deriv(n,f)` | Global `iteratedDeriv n f`, a total real function. |
| `iterated_deriv_on(n,f,a,b)` | `iteratedDerivWithin n f (Set.uIcc a b)`, with its domain fixed by a,b. |
| `taylor_on(n,f,a,b,c,x)` | `taylorWithinEval f n (Set.uIcc a b) c x`; degree n, fixed derivative-domain endpoints a,b, center c, evaluation point x. |

Conditional natural-order convergence can be expressed as
`sequence_limit(sequence_lambda(n,partial_sum(u,n)),L)`. It must never be
substituted for `has_sum(u,L)`. The alternating harmonic series demonstrates the
difference: its ordered partial sums converge, but it is not `Summable` over ℝ.
The batch only proves the forward implication from HasSum to ordered convergence.
Likewise, `interval_integral` remains a total oriented Bochner integral; typing
an expression with it never asserts `IntervalIntegrable`.

## Coverage and endpoint conventions

Eleven sequence cards cover sum/product/quotient limits, absolute value,
uniqueness, non-strict order, squeezing, fixed index shifts, monotone bounded
convergence, geometric decay and a fixed numerator divided by the natural index.
The quotient requires a nonzero denominator limit. Monotone convergence includes
both monotonicity and a uniform upper bound. A shift is a fixed natural number.

Fifteen series cards cover uniqueness, addition, scalar multiplication, absolute
comparison/convergence, the zero-term test, ordered partial sums, finite shifts,
geometric and exponential series, the real p-series criterion, bounded
nonnegative partial sums, sum bounds, absolute sum estimates, and prefix/tail
splitting. The p-series uses `Real.rpow` and states the exact criterion 1<p;
the n=0 term is Mathlib's totalized expression and does not change convergence.
The exponential series has coefficients x^n/n! for arbitrary real x.

Five finite Taylor cards give the explicit degree-n coefficient sum, successor
recurrence, derivative of the finite Taylor polynomial, Lagrange remainder and
integral remainder. The first three are identities of finite polynomials with
totalized derivative coefficients: no assertion of smoothness or approximation
of f is hidden in their statements. In the derivative identity, the domain a,b
and center c stay fixed while the evaluation point varies.

The Lagrange remainder requires a<b and C^(n+1) on uIcc a b, and produces c
strictly between a and b. Its remainder uses the ordinary iterated derivative
at that interior c. The integral remainder allows arbitrary endpoint orientation
and uses the within-derivative on the fixed unordered interval. Its kernel is
(b−t)^n/n!, with derivative order n+1. The global and within derivatives are
separate typed operators and are not silently interchanged.

All degrees are arbitrary Nat, including zero. The degree-zero finite expansion
has its single zeroth-derivative coefficient, the successor degree is n+1,
factorials never vanish, and the remainder theorems at n=0 require C^1. Equal
endpoints are allowed by the integral identity (both sides vanish), but excluded
from the Lagrange card because its strict interior would be empty.

## Validation and evidence

The closed grammar checks sorts, arities, lexical scopes, allowed attributes,
OpenMath namespaces and exact cdbases. Natural/real comparisons require matching
sorts. All variable references must resolve; binders cannot shadow existing
variables. A sequence lambda binds one Nat and returns a Real; a real lambda
binds one Real and returns a Real. Registry header, complete symbol identities,
entry shapes and nonempty semantics are checked against the fixed implementation.

Bounds are 65,536 UTF-8 bytes, 4,096 nodes, depth 64, 1–256 binder variables and
at most 32 application arguments. Exact canonical bytes are checked after typed
validation. Tests reject negative/fractional natural arguments, wrong function
carriers, unknown operators, free/shadowed variables, wrong arities and malformed
namespaces. Independent semantic assertions pin partial-sum cutoffs, exponential
coefficients, Taylor domain/center/evaluation slots and derivative-order slots.

The generator serializes exactly `import Mathlib` and the per-card anonymous
examples, runs the existing pinned `lake env lean` with a 180-second timeout,
and emits the JSON only after success. The evidence pins witness, validator and
registry hashes plus the actual toolchain and mathlib revision. No sorry, admit,
custom axiom or mocked receipt is used. Authored hard negatives cover all cards
but have not been run through retrieval evaluation.

## Remaining gaps

There is no claim of general Taylor-series convergence for smooth functions.
General radii of convergence, analytic expansions of arbitrary functions,
alternating/conditionally convergent series, rearrangement theorems, ratio/root
criteria, uniform convergence, interchange of limits/derivatives/integrals,
complex power series and multivariate Taylor expansions remain future work.
Each needs its own exact hypotheses and compiled witnesses rather than aliases
for the already-covered theorem families.
