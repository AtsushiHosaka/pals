# typed-calculus-v2: general real calculus

This is a new, isolated authoring profile. It leaves every v1 validator, registry,
manifest and canonical proposition unchanged. The namespace is
`urn:pals:openmath:typed-calculus:v2`; its dictionaries are `typed2` and
`calculus2`. The registry records a signature and mathematical/Lean semantics
for every admitted symbol. Standard real arithmetic and logic retain their
standard OpenMath dictionaries.

The first batch contains 28 independently stated general results. Every target
is compiled against the existing pinned local Lean/mathlib workspace. Compilation
establishes the Lean proposition, while independent comparison of prose,
OpenMath and Lean remains necessary. Type validation is not a proof of truth,
an OpenMath-to-Lean translation certificate, or approval for serving/publication.

## Mathematical surface

| Construct | Exact meaning |
| --- | --- |
| `typed2:Real`, `typed2:Nat` | ℝ and ℕ; Nat includes zero. |
| `calculus2:RealFunction` | A function ℝ → ℝ. |
| `lambda`, `apply` | One explicitly typed real binder and ordinary function application. |
| `arith1:power(x,n)` | Real base and **Nat** exponent, including bound natural variables. Negative/fractional/Real exponents are rejected. |
| `nat_pred(n)`, `nat_succ(n)`, `of_nat(n)` | Truncated predecessor, successor and exact cast ℕ → ℝ. |
| `of_int`, `of_rat` | Exact integer-literal or reduced rational-literal real values. A bound Nat must use `of_nat`. |
| `has_deriv_at(f,a,m)` | **HasDerivAt f m a**. OpenMath uses function, point, slope; Lean uses function, slope, point. |
| `continuous_at`, `differentiable_at` | Pointwise `ContinuousAt` and `DifferentiableAt ℝ`. |
| `epsilon_delta_continuous_at(f,a)` | Positive ε/δ continuity at a, equivalent to `ContinuousAt f a`. |
| `continuous(f)`, `differentiable(f)` | Global continuity and global real differentiability. |
| `continuous_on_closed(f,a,b)` | `ContinuousOn f (Set.Icc a b)`. |
| `differentiable_on_open(f,a,b)` | `DifferentiableOn ℝ f (Set.Ioo a b)`. |
| `interval_integrable(f,a,b)` | `IntervalIntegrable f volume a b`. |
| `interval_integral(f,a,b)` | The oriented Bochner `intervalIntegral f a b volume`. |
| `exp`, `sin`, `cos`, `arctan` | The corresponding real mathlib functions. |
| `log` | `Real.log`, which equals the logarithm of absolute value away from zero and is totalized as zero at zero. |
| `sqrt` | `Real.sqrt`, the nonnegative square root on nonnegative inputs, zero on negative inputs. |

`interval_integral` is a total Lean operation. Merely typing an expression with
it does **not** assert integrability. The elementary integral cards state
integrability together with the value; other value identities carry explicit
integrability assumptions or continuity/derivative assumptions sufficient for
the particular theorem. No limit, improper integral, principal value or
nonabsolute Riemann integral is silently identified with this operator.

All derivative formulas specify the derivative value using `has_deriv_at`;
there is no total `deriv` operator in the OpenMath grammar. The logarithm chain
card states its nonzero-input premise and the square-root card its
positive-input premise. The natural-power derivative uses
`of_nat(n) * a^(nat_pred(n))`, so n=0 and a=0 are both covered correctly. The
power integral denominator is `of_nat(nat_succ(n))`, always nonzero.

## Initial coverage

- Arbitrary natural powers: derivative, global continuity, finite integral with
  integrability, and power chain rule.
- General function composition with exp, log, sin, cos, sqrt and arctan, retaining
  the inner derivative and all domain premises.
- Finite exp/sin/cos integrals for arbitrary endpoints; reciprocal integral on
  an interval with positive endpoints.
- Lagrange mean value and Rolle theorems with continuity on the closed interval,
  explicit two-sided derivative evidence on its interior and strict a<b.
- Both fundamental theorems: integrate an antiderivative with an integrable
  derivative, and differentiate the integral of a continuous integrand.
- Integration by parts and substitution with explicit derivative functions.
  Substitution preserves oriented endpoints and needs no monotonicity premise.
- Integral addition, scalar multiplication, adjacent interval addition and
  order preservation with the required endpoint orientation.
- Nonnegative derivative implies monotonicity; everywhere-zero derivative
  implies constancy; intermediate value and minimum-attainment theorems.

The 23 authored hard-negative cases cover all 28 cards with missing assumptions
or incorrect conclusions and concrete counterexamples. They are candidates for
retrieval evaluation, not a claim that retrieval precision has been tested.

## Validation and evidence boundaries

Validation permits only a closed, typed proposition with the listed dictionaries.
Every OMV must be bound exactly once in its scope. Function argument/result sorts
are checked; a real lambda binds exactly one Real and returns a Real. The root
must be Prop. Namespaces, symbol identities, cdbase declarations, allowed
attributes and binder forms are closed. Unknown theorem-name operators are
rejected.

Limits are 65,536 UTF-8 bytes, 4,096 nodes, depth 64, 256 binder variables and
32 application arguments. Canonicalization uses the existing structural OpenMath
canonicalizer only after this independent profile validator has accepted the tree.
Canonical bytes retain the v2 namespace and cannot masquerade as v1 bytes.

The generator writes the exact `import Mathlib` plus `example` bundle, invokes
`lake env lean` with a 180-second timeout, and only after a successful compilation
emits the expansion JSON. Its evidence pins the full source hash, validator hash,
registry hash, actual Lean toolchain and actual mathlib revision. No `sorry`,
`admit`, custom axiom, mock compilation or unbound auxiliary theorem is used.

Profile tests exercise closed typing, variable exponents, invalid exponents,
wrong carriers, arity, free/redeclared variables, casts, unsupported symbols,
canonicalization and resource limits. Independent semantic tests pin the exact
function/point/slope expressions in nine derivative theorem families; these
cannot be checked by sort validation alone because point and slope are both Real.

## Remaining gaps

This batch does not claim textbook completeness. Infinite sequences and series,
Taylor expansions/remainders, convergence and interchange theorems, improper
integrals, multivariate calculus, ODEs and arbitrary indexed sums remain outside
this profile. Extending those requires exact types, operators, hypotheses,
compiled witnesses and semantic review in an appropriate versioned dictionary.
