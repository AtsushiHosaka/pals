# `typed-ode-v1` design

`typed-ode-v1` is an isolated authoring profile for concrete ordinary
differential-equation solution certificates.  It is not an extension of the
generic OpenMath profile, `typed-math-v1`, or `typed-real-analysis-v1`; it is
not a generic DB/seed/PFI input.

## Narrow v1 statement form

Every accepted statement has exactly this shape (with zero or more outer real
parameters):

```text
forall parameters : Real,
  initial_value(f : Real -> Real, 0, y0) and
  forall x : Real, ODE-equality(deriv_at(f, x) | second_deriv_at(f, x), ...)
```

`f` is a literal `ode1:lambda` that binds precisely one `Real` variable and
returns a `Real`.  The initial-value lambda and derivative lambda must be
alpha-equivalent and the derivative point is exactly the globally quantified
`x`.  This excludes a superficially plausible conjunction whose initial value
belongs to a different function.

`ode1:deriv_at(f,x)` lowers to Lean `deriv f x`; `ode1:second_deriv_at(f,x)`
lowers to `deriv (fun t => deriv f t) x`; and
`ode1:initial_value(f,0,y0)` lowers to `f 0 = y0`.  Thus the statements are
solution certificates for the displayed concrete functions, not claims of
existence or uniqueness.

## Signature and boundary

- Profile ID: `typed-ode-v1`
- Typed cdbase: `urn:pals:openmath:typed-ode:v1`
- Typed OMS nodes, including binders, must directly carry that cdbase; inherited
  cdbases are rejected.
- Only `OMOBJ`, `OMS`, `OMV`, `OMI`, `OMA`, `OMBIND`, `OMBVAR`, `OMATTR`, and
  `OMATP` occur.  Each permits an exact allowlist of attributes; unknown
  attributes are rejected.
- The profile allows only `Real` declarations.  It does not quantify arbitrary
  functions, sets, intervals, domains, or unknown initial points.
- Literal real functions use `ode1:lambda`; only `of_int`, `apply`,
  `deriv_at`, `second_deriv_at`, and `initial_value` are available ODE
  primitives.  The small arithmetic/transcendental whitelist is enough for
  the ten existing source examples.

The sealed manifest binds the source candidate catalog, this design, registry,
exact Lean witness file, canonical XML, per-card proof/statement evidence, and
its own canonical JSON digest.  Any mismatch is stale and rejected by tests.

## Explicit non-goals

The following are deliberately rejected rather than approximated:

- local/open/closed/half-open intervals or arbitrary domain predicates;
- IVPs at points other than `0`, omitted initial values, or initial values for
  a different function;
- arbitrary `Real -> Real` variables and unsupported function equality;
- existence, uniqueness, maximal interval, Picard--Lindelöf, or stability;
- higher order beyond the named second derivative, systems, weak solutions,
  distributions, numerical methods, and special functions.

These require a successor profile with its own CD, typed semantics, and Lean
evidence.  No v1 validator, generic profile, loader, DB row, seed, or PFI
package is widened here.
