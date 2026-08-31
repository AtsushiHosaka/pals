# typed-commutative-algebra-decomposition-v1

## Purpose and admission boundary

`typed-commutative-algebra-decomposition-v1` is the CA-4 primary-decomposition
core.  It contains original exercises only; it neither reproduces source-text
exercise wording nor changes the generic Draft DB, seed, embedding index, PFI
package, or generic OpenMath retrieval semantics.

This is a sibling of the ideal-lattice, modules, and localization profiles.
Those registries are immutable sealed evidence.  Changing them would alter
their accepted language, so primary decomposition receives its own cdbase and
validator.

The sealed manifest is local authoring evidence only.  It is not a claim that
OpenMath is automatically translated to Lean, and it is not admission to any
production catalog.

## Represented language

Each closed proposition binds a `CommRing(R)` first.  Every dependent object
names exactly that ring:

- `Ideal(R)` is an arbitrary ideal;
- `PrimaryIdeal(R)` is a primary ideal witness; it is converted to an ordinary
  ideal only by `primary_as_ideal(R,Q)`;
- `PrimeIdeal(R)` is a prime ideal witness; it is converted only by
  `prime_as_ideal(R,P)`;
- `primary_radical_prime(R,Q)` is the distinguished prime witness whose
  underlying ideal is the radical of the primary component `Q`;
- `ideal_inf2`, `ideal_inf3`, and `ideal_radical` construct only ideals over
  the same explicit carrier;
- `primary_decomposition2` / `primary_decomposition3` assert a finite
  decomposition with primary components, and
  `irredundant_decomposition2` is the two-component non-omission condition;
- `minimal_prime_over(R,P,I)` accepts a *prime-typed* `P` and an `Ideal(R)`.

The profile does not treat `PrimaryIdeal` or `PrimeIdeal` as implicitly
coercible to `Ideal`.  This makes the primary/prime evidence, all carrier
changes, and every decomposition component visible in the canonical XML.

More precisely, `primary_decomposition2(R,I,Q1,Q2)` asserts
`I = underlying(Q1) ∩ underlying(Q2)` with the primary facts carried by the
two component sorts.  The three-component form uses the fixed left-associated
intersection.  `irredundant_decomposition2` additionally asserts both
`underlying(Q2) ⊈ underlying(Q1)` and `underlying(Q1) ⊈ underlying(Q2)`.
It therefore cannot silently mean merely a list of components or a claim of
minimality for an arbitrary finite family.

## Fail-closed rules

- XML must be OpenMath-core-valid, closed, exact-v4-C14N at receipt time, and
  use only the fixed registry.
- Typed symbols directly declare this profile's cdbase.  Standard CD symbols
  cannot inherit a cdbase from an ancestor.
- Bound `Ideal`, `PrimaryIdeal`, and `PrimeIdeal` types can refer only to a
  previously bound `CommRing`; free variables, forward references, and binder
  shadowing are rejected.
- All intersections, radicals, predicates, and decomposition operations check
  the exact same ring carrier.  A primary component is not accepted where an
  ordinary ideal is required unless the explicit conversion is present.
- A minimal-prime assertion requires `PrimeIdeal(R)`, not merely `Ideal(R)`.
  A two- or three-component primary decomposition requires primary-typed
  components.  This rejects the common primary-vs-prime and carrier-mismatch
  confusions before authoring evidence can be sealed.

## Lean convention and scope

The companion Lean bundle uses the pinned local Mathlib workspace.  A
`PrimaryIdeal(R)` declaration corresponds to an `Ideal R` accompanied by an
explicit `Ideal.IsPrimary` hypothesis, and `PrimeIdeal(R)` similarly carries
`Ideal.IsPrime`.  The manifest's alignment record documents that convention
for each card; no XML-to-Lean compiler is asserted.

The v1 witnesses cover elementary radical identities, intersections with a
common radical, primary radical primeness, minimal-prime characterizations of
a primary ideal, and consequences of a given two- or three-component
decomposition.  They deliberately do **not** claim the existence of primary
decompositions.

## Explicit hard deferrals

The following remain outside the language and must reject as unknown symbols
or malformed sorts, rather than being represented by an untyped predicate:

- associated primes, annihilators, colon ideals, and module quotients;
- Noetherian hypotheses, existence/uniqueness of primary decomposition, and
  embedded-component theorems;
- arbitrary finite families, minimal or irredundant decompositions beyond the
  explicit two- and three-component witness forms;
- quotient rings, polynomial computations, localization, and localized
  modules.

Those topics need additional dependent carriers and a separate direct Lean
alignment profile.  In particular, the absence of an associated-prime token is
intentional: a prime ideal alone is not sufficient to encode its witness
module and annihilator.
