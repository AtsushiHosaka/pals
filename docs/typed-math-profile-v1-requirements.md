# typed-math-profile-v1 requirements

## Outcome

Enable type-safe authoring for carrier-sensitive university mathematics without
weakening the current generic OpenMath catalog.  `typed-math-v1` is an isolated
authoring profile; it is not a migration of the generic seed, API, or
six-column local `dsp_drafts` table.

## Must requirements

| ID | Requirement | Acceptance evidence |
| --- | --- | --- |
| TYPED-REQ-001 | Provide explicit typed validation and canonicalization entry points, entirely separate from generic-v1. | A valid typed fixture passes the typed entry point and fails the generic one; generic canonical-byte fixtures remain unchanged. |
| TYPED-REQ-002 | Allow only the versioned registry in `pals_agent/content_dictionaries/typed-math-v1-registry.json`, require at least one `typed1:forall` or `typed1:exists` and one `typed1:type` declaration, and forbid `quant1`/`fns1` in a typed document. | Unknown CD/symbol, generic-only XML, misplaced/multiple/missing annotation, and free typed variable fixtures reject. |
| TYPED-REQ-003 | Infer structural dependent sorts bottom-up and reject carrier, equality, and natural-literal cast mismatches in the initial group/ring slice. | Group/ring positive and hard-negative fixtures pass; later polynomial, Frechet, and Fubini modules each add their own requirement and evidence before admission. |
| TYPED-REQ-004 | Profile confusion shall fail before embedding, candidate persistence, or release preparation. | Typed XML at generic entry points and generic XML at typed entry points both reject. |
| TYPED-REQ-005 | Typed candidates shall use a profile-specific immutable authoring manifest rather than the existing generic DB loader. | The generic loader rejects the typed manifest; the typed reader requires `openmath_profile`, canonical XML, Lean target/witness/toolchain/CD-bundle digests, and a reviewed statement/OpenMath/Lean alignment record. |

## Initial scope and exclusions

The first admissible slice is group/ring core syntax and its positive and
negative fixtures; it does not yet publish a card.  Polynomial, limited
Frechet, and Fubini cards remain proposed until each card has a complete
signature and a reviewed three-way statement/OpenMath/Lean alignment record.
XML type checking is not a Lean proof nor an English/OpenMath
semantic-equivalence proof.

ODE, gradients, Hessians, Lagrange multipliers, change of variables,
probability, vectors, matrices, and public/production publication are excluded
from this slice.  Sort equality is structural: no implicit subtyping, coercion
search, or Lean execution occurs during validation.

## Authoring decision

Typed local authoring starts with a RFC 8785-canonical immutable manifest under
`pals-agent/testdata/typed-math-v1/`; each sha256 digest is over the exact UTF-8
bytes of the named canonical artifact.  A typed database table is deferred until
a profile-specific retrieval endpoint and release controller are designed
together.  This preserves the fixed generic database contract.

The detailed data model, exact sort grammar, registry, failure modes, and
rollout sequence are in [the typed-math design](pals-typed-math-v1-minimal-design.md).
