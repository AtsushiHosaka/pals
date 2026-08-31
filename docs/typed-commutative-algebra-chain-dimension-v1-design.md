# typed-commutative-algebra-chain-dimension-v1

## Scope

`typed-commutative-algebra-chain-dimension-v1` is an isolated CA-6 authoring
profile for original exercises on Noetherian and Artinian commutative rings.
It models a declared `CommRing R`, dependent `Ideal(R)`, the predicates
`NoetherianRing(R)`, `ArtinianRing(R)`, `IdealFG(R,I)`,
`KrullDimLEZero(R)`, `PrimeIdeal(R,I)`, and `MaximalIdeal(R,I)`.
`HilbertNoetherian(R)` has the precise fixed meaning
`IsNoetherianRing (Polynomial R)`; `IteratedHilbertNoetherian(R)` means
`IsNoetherianRing (Polynomial (Polynomial R))`.

The profile is deliberately separate from the ideal, module, and localization
profiles.  It changes neither generic retrieval nor the generic Draft DB,
seed, embedding index, or PFI package.  Sealed cards are original statements,
not transcriptions of a textbook exercise.

## Acceptance contract

Every card must contain a closed profile-validated OpenMath proposition,
exact v4 C14N, four to eight Sketch steps, a direct witness compiling against
the pinned local Mathlib workspace, and source/canonical/Lean/profile artifact
digests in a sealed manifest.  The card claims only a reviewed manual
statement--OpenMath--Lean alignment; it does not claim automatic translation.

## Soundness rules

- `Ideal(R)` may name only a previously declared `CommRing R`.
- Every ideal predicate and operation repeats the exact ring carrier.  Cross
  carrier ideal use is rejected.
- `NoetherianRing`, `ArtinianRing`, and `KrullDimLEZero` accept exactly one
  declared commutative-ring carrier.  They are not untyped labels.
- `IdealFG`, `PrimeIdeal`, and `MaximalIdeal` accept exactly a ring and an
  ideal over that same ring.
- Typed cdbases must be direct on each typed `OMS`; inherited cdbases,
  untyped variables, free variables, shadowing, unknown symbols, and malformed
  type annotations are rejected.

## Explicit deferrals

This v1 does not encode arbitrary ascending/descending chains as functions,
finite-length modules, quotient/localization carriers, `Spec`, height, a
general natural-number-valued Krull dimension, or polynomial dimension
formulae.  In particular, a generic `dimension` token is rejected: the only
dimension statement here is the directly Lean-aligned `KrullDimLE 0` core.
Those features need their own dependent-chain or spectrum profile and hard
negative cases before authoring evidence can be admitted.
