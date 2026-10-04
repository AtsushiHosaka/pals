# typed-calculus-v4: finite-dimensional multivariable calculus

This isolated local-authoring profile contains 34 general results on arbitrary
finite-dimensional real inner product spaces. Its namespace is
`urn:pals:openmath:typed-calculus:v4`, with dictionaries `typed4` and `calculus4`.
It changes no v1/v2/v3 validator, registry or canonical proposition. Actual Lean
compilation proves each separate Lean target; semantic review is needed to match
that target with its typed XML and natural-language statement. Type acceptance is
not a truth checker or a certified translation. This work does not activate
runtime structuring, production publication or automatic trusted admission.

## Carriers and derivative conventions

`RealInnerProductSpace` means an arbitrary type E with `NormedAddCommGroup E`,
`InnerProductSpace ℝ E` and `FiniteDimensional ℝ E`. Each quantified space has a
nominal identity. E and F are not identified merely because their dimensions
happen to agree. The zero-dimensional space is permitted. Finite dimension
provides completeness for Riesz representation and adjoints.

| Type | Exact Lean carrier |
| --- | --- |
| `Vector(E)` | E |
| `Function(E,F)` | E → F |
| `CLM(E,F)` | E →L[ℝ] F |
| `ScalarFunction(E)` | E → ℝ |
| `ScalarCLM(E)` | E →L[ℝ] ℝ |
| `Curve(E)` | ℝ → E |
| `DerivativeField(E,F)` | E → E →L[ℝ] F |
| `Bilinear(E,F)` | E →L[ℝ] E →L[ℝ] F |
| `RealFunction` | ℝ → ℝ |
| `Real`, `Nat` | ℝ, ℕ including zero |

The derivative field and bilinear carriers are *not* silently assigned an inner
product compatible with their operator norm. They are dedicated types, and only
the explicit operators appropriate to them are permitted.

The complete closed registry specifies every operator's ordered argument sorts,
result sort and mathematical/Lean meaning. Notable conventions are:

- `has_fderiv(E,F,f,x,A)` means `HasFDerivAt f A x`. Point precedes derivative
  in XML; Lean places the derivative before the point.
- `has_gradient(E,f,x,u)` means `HasGradientAt f u x`. Gradient and point have
  the same vector sort, so independent semantic tests pin this order.
- `has_curve_deriv(E,c,t,v)` and `has_real_deriv(f,t,m)` likewise put the
  parameter point before velocity or slope.
- `has_line_deriv(E,F,f,x,v,w)` means `HasLineDerivAt ℝ f w x v`: the
  derivative at zero of t↦f(x+t•v) is w. A direction need not have unit norm.
- `scalar_line_deriv(E,f,x,v)` is the totalized `lineDeriv ℝ f x v`. The bound
  card has an actual gradient premise and identifies this value through a
  derivative witness; a zero returned by the operator alone proves no existence.
- `derivative_field(E,F,f,D)` asserts ∀x, HasFDerivAt f (D x) x.
  `has_second_deriv(E,F,D,x,H)` is HasFDerivAt D H x. Neither is an opaque
  theorem name: both are explicit derivative predicates on typed functions.
- `clm_compose(E,F,G,B,A)` applies A first and then B. The gradient chain rule
  uses `adjoint_apply(E,F,A,u)` with result in E, not F.
- `dual(E,u)` is the real Riesz map u↦(h↦⟨u,h⟩). Complex conjugation
  conventions are out of scope. `inner_derivative` is the concrete linear map
  h↦⟨A h,v⟩+⟨u,B h⟩, not a hidden theorem or proof.
- `fderiv` is totalized as zero on nondifferentiable inputs. Its equality to a
  given map is only concluded from an actual derivative witness.
- `local_min` and `local_extremum` mean unrestricted neighborhood extrema.
  Constrained boundary extrema are different and are not encoded by these symbols.
- `cont_diff` and `scalar_cont_diff` mean global C^n for a natural n. They
  include n=0; no n+1 regularity is inferred.

Functional constructors represent explicit pointwise functions (addition,
subtraction, scalar multiplication, norms, inner products, affine maps and
composition). They carry full domain/codomain types, and cannot be used as
untyped aliases for a theorem. Variables are bound by typed forall/exists only.

## Coverage and comparison with prior profiles

The 34 cards comprise Fréchet linear/affine rules; sum, difference, fixed and
variable scalar rules; general chain and inner-product rules; norm-square
calculus; differentiability of norm and distance away from their singular locus;
derivative uniqueness, continuity and total-operator identification; Riesz
gradient representation and uniqueness; linear/squared-norm gradients; gradient
linearity and adjoint chain rule; directional/curve calculus and its norm bound;
Fermat conditions; zero-derivative constancy; a uniform derivative mean-value
estimate; symmetry of the second Fréchet derivative; and arbitrary-order smooth
composition, squared norms and inner products.

The v1 reuse batch and v2 dealt only with ℝ→ℝ functions. The analogous sum,
difference, scalar, chain, uniqueness, continuity, extremum and constancy rules
here quantify independent vector-space carriers and continuous linear derivative
maps. They strictly generalize those scalar statements: they cannot be obtained
by merely renaming a scalar variable or replacing a numeral. This overlap is
intentional reuse at a different mathematical type, not 34 wholly unrelated
ideas. The v3 sequence/series/finite univariate Taylor cards have no repeated
propositions here. Regression checks compare full Lean targets and prose against
all three prior batches; no exact proposition string is repeated.

New structural coverage that earlier scalar profiles could not express includes
rectangular derivative composition E→F→G, variable scalar-vector products,
inner-product differentiation, Riesz gradients, adjoint pullback of gradients,
vector curves, arbitrary directional derivatives, operator-norm bounds and the
continuous bilinear second derivative. Coordinate partial derivatives of these
maps are special directions, but this batch does not claim that merely having
coordinate partial derivatives establishes a Fréchet derivative. The mixed
partial counterexample in the negatives demonstrates why this distinction matters.

The second-derivative symmetry card assumes an actual first derivative field at
every point and differentiability of that field at x. It does not infer symmetry
from the existence of two isolated mixed partial derivatives. The bounded
first-derivative estimate requires its operator-norm bound at every point, not
merely the endpoints. Extrema must be unconstrained and differentiable. The
converse implication from a zero gradient to an extremum is not asserted.

## Validation and evidence

The validator is independent of older modules. It enforces exactly matching
OpenMath namespaces/cdbases, registered symbols, arities, attributes, nominal
source/target carriers, prior declarations, and closed variable scopes. Shadowing
and duplicate binders are rejected. Natural literals are canonical nonnegative
integers below one billion; a real numeral requires an explicit cast.
There is no implicit conversion among vectors, scalar values, functions, linear
maps and derivative fields. Equality requires the same value sort; carrier and
proposition equality are rejected. Numeric comparisons require matching Nat or
Real operands.

Bounds are 64 KiB UTF-8, 4096 nodes, depth 64, 256 characters per attribute and
64 declarations per binder. Every operator has a small fixed arity. Registry
header and symbol set are pinned to the implementation, and every registered
signature is checked against its implemented signature. Canonicalization occurs
only after typed validation. Tests include invalid carrier/slot substitutions,
negative/fractional regularity orders, malformed bindings and namespaces,
resource limits, and independent exact expressions for chain/gradient/second
and line derivative slots that ordinary type checks cannot distinguish.

The generator writes exactly the standard `import Mathlib` plus per-card examples,
compiles against the pinned existing lake workspace with a 180-second timeout,
and only then emits the manifest. Evidence includes SHA-256 of witness, validator
and registry, the actual toolchain and actual mathlib revision. The 34 paired
hard negatives are authored mathematical counterexamples, not a claim that
retrieval ranking or embedding precision has been tested.

## Uncovered material

Coordinate-indexed Jacobian matrices, general multivariable Taylor remainder
estimates, constrained Lagrange multiplier rules, inverse/implicit function
conclusions, line and surface integrals, Green/Stokes/divergence theorems,
change of variables in multiple integrals and numerical differentiation remain
outside this batch. The derivative and Hessian language is a foundation for
those topics, not a claim they have already been proved here. General Banach
spaces and complex differentiation are also intentionally outside this finite
real inner-product-space profile.
