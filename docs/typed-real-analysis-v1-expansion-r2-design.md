# `typed-real-analysis-v1` r2 expansion design

## Immutable boundary

This document governs a supplementary, sealed local authoring manifest.  It
does not amend, replace, or supersede
`typed-real-analysis-v1-authoring-manifest-proposal.json`: that original
four-card manifest remains an immutable snapshot whose digest is recorded in
the local typed catalog.

The r2 manifest contains exactly 15 new cards and explicitly excludes the
four snapshot IDs.  It uses the same isolated `typed-real-analysis-v1`
validator and registry, but has its own schema, manifest digest, Lean witness
bundle, and staleness test.  It is not a DB Draft, a generic Draft, a seed
input, an embedding-index entry, or a PFI package.

## Admitted r2 families

| Family | Cards | Type-safety boundary |
| --- | ---: | --- |
| raw ε–δ / continuity | 4 | All scalars are `Real`; reciprocal claims carry an explicit nonzero premise. |
| `has_deriv_at` | 4 | Uses predicate-valued derivative evidence, including sum/product/chain rules; no total `deriv`. |
| `differentiable_at` | 3 | Closure facts only; the reciprocal is conditional on a nonzero point. |
| `interval_integrable` | 4 | Proves only `IntervalIntegrable f volume a b`; no integral value or linearity equality. |

No registry symbols are added.  Every card stays within the existing signatures
for `epsilon_delta_continuous_at`, `continuous_at`, `has_deriv_at`,
`differentiable_at`, `interval_integrable`, Real arithmetic, logical premises,
and typed `Real` binders.

## Hard exclusions

The current registry and hard-negative suite continue to reject MVT, Taylor,
integral values or integral linearity, Riemann partitions, and improper
integrals.  The r2 cards do not introduce `interval_integral`, a total
derivative term, infinity, partitions, or untyped coercions.  A future profile
requires a new registry, exact Lean evidence, and a separate immutable
manifest; it must never mutate either this r2 manifest or the original
four-card snapshot.

## Evidence and staleness

Each r2 card has 4–8 nonempty sketch steps, a strategy, raw XML, profile C14N,
canonical XML digest, an exact Lean target/witness marker, and a manifest
payload digest.  The generator revalidates XML and exact C14N before sealing;
the tests regenerate both base and expansion outputs byte-for-byte and assert
that their IDs and canonical XML are disjoint.
