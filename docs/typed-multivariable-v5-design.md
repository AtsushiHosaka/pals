# typed-multivariable-v5: coordinate calculus and multivariable integration

This isolated authoring profile adds 32 general cards to address undergraduate foundation gaps. It registers no runtime structuring, retrieval, publication, or trusted admission behavior. No previous profile is modified. The namespace is `urn:pals:openmath:typed-multivariable:v5`, with dictionaries `typed5` and `multivar5`.

The batch is locally compiled against the existing pinned Lean workspace. Each Lean example proves its stated Lean proposition. The XML validator checks closed syntax, dependent types, and canonical bytes; it is not a proof-producing XML-to-Lean translator. Matching the natural statement, XML, and Lean proposition still requires semantic review.

## Domain and closed types

All coordinate dimensions are arbitrary natural numbers, including zero, bound before their dependent objects. `Vector(n)` is `Fin n → ℝ` with the standard finite-product topology and supremum norm. `Index(n)` is `Fin n`; a bound coordinate index implicitly requires that dimension to have an element. No numerical dimension is hardcoded in a positive card. Measures are the standard Lebesgue volume on these coordinate spaces and its product measures. Norms and measures are not independently user-selectable parameters in this profile.

| Type | Mathematical/Lean carrier |
|---|---|
| `Function(m,n)`, `CLM(m,n)` | ℝᵐ → ℝⁿ; ℝᵐ →L[ℝ] ℝⁿ |
| `Matrix(m,n)` | Matrix (Fin m) (Fin n) ℝ, rows first |
| `ScalarFunction(n)`, `ScalarCLM(n)` | ℝⁿ → ℝ; ℝⁿ →L[ℝ] ℝ |
| `Bilinear(n)` | ℝⁿ →L[ℝ] (ℝⁿ →L[ℝ] ℝ) |
| `ScalarDerivativeField(n)` | ℝⁿ → (ℝⁿ →L[ℝ] ℝ) |
| `DerivativeField(m,n)` | ℝᵐ → (ℝᵐ →L[ℝ] ℝⁿ) |
| `Curve(n)`, `Set(n)` | ℝ → ℝⁿ; Set ℝⁿ |
| `FunctionFamily(k,n)`, `DualFamily(k,n)` | k scalar functions on ℝⁿ; their k linear derivative functionals |
| `RealFunctionFamily(n)` | Fin n → (ℝ → ℝ) |
| `ProductScalarFunction(m,n)` | (ℝᵐ × ℝⁿ) → ℝ |
| `ProductFunction(m,n,p)`, `ProductCLM(m,n,p)` | (ℝᵐ × ℝⁿ) → ℝᵖ; the corresponding continuous linear maps |
| `LeftField(m,n,p)`, `RightField(m,n,p)` | jointly indexed derivative fields whose linear domains are the first and second block, respectively |

Dimensions with different bound identities remain different sorts, even if the proposition contains an equality between their values. There are no implicit dimension transports or casts between vectors, matrices, functions, and continuous linear maps. A dimension/index argument must refer to a previously bound natural variable; literal numbers cannot masquerade as dependent carrier declarations. Natural literals used as smoothness orders are canonical nonnegative integers below one billion. Real numerals require the explicit natural-to-real cast.

The registry exhaustively lists ordered argument types, result types, and mathematical/Lean meaning for every operator. Both registry headers and the exact symbol/signature set are checked against the implementation. Unsupported symbols, including arbitrary theorem-name predicates, are rejected. Quantifiers have ordered typed declarations, no free variables, no shadowing, and no implicit structure instances.

## Derivative and matrix conventions

- `has_fderiv(m,n,f,x,A)` and `has_scalar_fderiv(n,f,x,A)` place the **point before the derivative**, and mean `HasFDerivAt f A x`. The strict variant means `HasStrictFDerivAt`, not ordinary differentiability at one point.
- `has_deriv(f,t,v)` and `has_curve_deriv(n,c,t,v)` place the **parameter point before the velocity/slope**, while Lean's `HasDerivAt` places the derivative first.
- `coordinate_slice(n,f,x,i)` is `t ↦ f(update(x,i,t))`. Its base parameter is `x i`, not zero. It replaces the coordinate by t; it does not add t to the coordinate.
- The Jacobian of f:ℝᵐ→ℝⁿ is `LinearMap.toMatrix' (fderiv ℝ f x).toLinearMap`, with **n output rows and m input columns**. Entry (j,i) is the derivative of output component j along input coordinate i. The chain rule is `Jg(f(x)) * Jf(x)` in that order.
- `fderiv` is totalized to zero on nondifferentiable inputs. Merely writing a Jacobian or derivative-field term does not assert differentiability. Cards that identify an actual derivative retain the relevant witness or differentiability premise.
- Output-component assembly concerns **full Fréchet derivatives of scalar output functions**. It cannot be used to assemble a total derivative from isolated input partial derivatives.
- The two-block strict differentiability criterion assumes actual block derivative witnesses at every point, and joint continuity of both fields at the target point. This global hypothesis is deliberately stronger than the underlying neighborhood theorem; no neighborhood condition is silently dropped.
- The first-order Jacobian remainder is little-o of the displacement. No quadratic remainder bound is claimed from mere differentiability.

For a continuous bilinear form B, the quadratic derivative is `B x + B.flip x`, its Hessian is `B+B.flip`, and the exact second-order term is `B h h`. No symmetry hypothesis is required; replacing the derivative by `2B x` would require symmetry. These three cards concern arbitrary quadratic forms only. They do not claim a general higher-order multivariate Taylor theorem.

## Constraints, integrals, and the counterexample

The Lagrange cards use strictly differentiable scalar constraints and objectives and a local extremum **on the level set**. The weak single- and finite-family versions permit an abnormal objective multiplier of zero; only the combined multiplier vector is nonzero. The normal single-constraint conclusion `B=λA` separately requires `A≠0`. Constraint independence, a nonzero objective gradient, or sufficiency for an extremum is not inferred.

The Fubini cards retain actual product integrability. For real functions, this is absolute integrability, not convergence of signed iterated integrals. Section integrability is asserted almost everywhere, not everywhere. The integrability criterion retains product a.e. strong measurability and outer integrability of **x ↦ ∫ y, |f(x,y)|**. Cartesian-domain Fubini uses a genuine set product s×t. Arbitrary n separated-product formulas include n=0, where both the empty product and the singleton product volume are one.

Lean's Bochner integral is totalized, returning zero for a nonintegrable function. The separated-product identity is available in Mathlib even for totalized integrals without an integrability premise; this batch intentionally states it for integrable factors so its natural-language use does not suggest existence from a formal identity. Integrability is proved separately in distinct cards.

The Jacobian change-of-variables cards require a measurable domain s, actual **within-s** derivative witnesses at all points of s, and injectivity on s. The weight is `abs(det(D x))`. No open-domain assumption, global injectivity, or nonzero Jacobian is silently imposed or inferred. The formula card also assumes the target integrand is integrable on f(s). The integrability-equivalence card states the existence criterion itself; the measurable-image card supplies a distinct domain property.

The line integral is the oriented scalar interval integral of the explicitly constructed pullback `t ↦ D(c(t))(u(t))`. The potential f is globally defined with actual derivative field D; the supplied u must be the actual curve derivative on `uIcc(a,b)`, and the pullback must be interval-integrable. The fundamental theorem and path-independence cards do not cover arbitrary one-forms, singular fields, or piecewise differentiable paths without the stated derivative witnesses.

`mv_v5_partials_without_continuity` is a **positive, compiled counterexample card**, not just a negative-test annotation. For arbitrary m,n, chosen coordinates i,j, and every a≠0, it explicitly defines

```
f(x,y) = if xᵢ=0 or yⱼ=0 then 0 else a.
```

Both block restrictions at the origin are identically zero and have derivative zero. A nearby point with both blocks equal to a small nonzero constant vector has value a, contradicting continuity at the origin. The nonzero amplitude assumption is essential. The theorem includes that discontinuity conclusion; no automatic retrieval or application success is claimed.

## Coverage and non-duplication audit

The 32 cards comprise 8 coordinate/Jacobian facts, 1 block-partial regularity criterion, 1 derivative-field smoothness result, 3 general quadratic-form derivative/Hessian/expansion facts, 3 Lagrange results, 10 Fubini and product-integrability results, 3 Jacobian change-of-variables results, 2 potential line-integral results, and 1 parameterized counterexample.

Compared with calculus v1–v3, this profile introduces coordinate-indexed finite-dimensional carriers, rectangular Jacobian matrices, block partial fields, multiple Lebesgue integrals, determinant-density substitution, constrained extrema, and path integrals. Compared with v4, none of the 32 natural statements or Lean targets is an exact duplicate. The independent unit check enforces that limited claim; it is not a theorem-equivalence decision procedure.

Some coordinate facts are useful, explicitly represented **corollaries** of v4's abstract linear/affine/chain rules: projection, coordinate update, restriction to a coordinate, and matrix chain multiplication. They are not advertised as new independent mathematical principles. They supply the missing coordinate constructors, dimensions, and computational normal forms. The component iff criteria, block-partial continuity criterion, Lagrange constraints, product integration, substitution, path integrals, and genuine discontinuity counterexample add mathematical statements absent from the earlier calculus batches. The quadratic-form Hessian and exact expansion generalize the special norm-square setting without claiming arbitrary smooth-function Taylor coverage.

No family is multiplied by changing numerical coefficients or variable names. All dimensions, finite-family sizes, regularity orders, domains, and amplitudes remain quantified where relevant. The authored hard-negative file has 32 paired mathematical cases, including wrong derivative slots, missing joint continuity, weak versus normal Lagrange multipliers, Fubini cancellation, exceptional sections, signed versus absolute Jacobians, multiplicity, and non-exact fields. These cases are not retrieval evaluations.

## Verification and evidence

Bounds: 65,536 UTF-8 bytes, 4,096 XML nodes, depth 64, 256 characters per attribute, and 64 declarations per binder. Exact namespaces, cdbases, element attributes, scopes, arities, dependent dimensions, and canonical bytes are enforced before acceptance.

Unit checks cover all 32 canonical cards; invalid dimensions, indices, row/column shapes, free variables, slot types, arities, fake theorem predicates, dimension declarations, namespace/attribute drift, resource bounds, registry drift, canonicalization, exact witness serialization, and evidence hashes. Independent expression expectations pin the coordinate-slice base point, Jacobian row/column and chain order, objective/constraint order, derivative-field substitution order, integration order, and the counterexample's nonzero-amplitude premise.

The generator writes exactly `import Mathlib` followed by the standard per-card examples, compiles once with the existing `lake env lean` and a 180-second timeout, and emits the manifest only after success. It records the actual toolchain/mathlib revision and SHA-256 pins of witness, validator, and registry. No `sorry`, `admit`, added axiom, global namespace, auxiliary unbound theorem, or compile option is inserted into the witness.

## Remaining gaps

General higher-order multivariate Taylor remainders, general critical-point classification by Hessian definiteness, inverse/implicit function theorems, explicit nonlinear Jacobian calculations such as polar coordinates, arbitrary curved integration domains, generic line-integral parameterization invariance, surface integrals, Green/Stokes/divergence theorems, and numerical algorithms remain outside this batch. The existence of these 32 cards does not imply that a whole curriculum chapter or every exercise subtype is covered. Parent-level explicit bindings and the curriculum audit determine the narrower measured coverage.
