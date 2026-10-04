# Draft Catalog Expansion Design

## Overview

The expansion has three planes with deliberately different data:

1. **Coverage and authoring plane** in the parent repository: curriculum/reference
   families, problem modes, difficulty bands, candidate identities, evidence references,
   and admission state.
2. **Catalog publication plane**: immutable generic and profile-separated typed
   generations containing only searchable Draft content and compatible embeddings.
3. **Runtime retrieval plane**: explicit profile selection, profile-specific OpenMath
   validation and embedding, candidate retrieval, structural reranking, and proof
   planning.

The six-field Draft record remains unchanged. The coverage plane answers whether enough
material exists; the catalog plane answers what is published; the runtime plane answers
whether a request can retrieve it correctly.

## Requirements traceability

| Requirement | Design coverage |
|---|---|
| DCE-001 | Draft boundary and separate coverage/evidence manifests |
| DCE-002–DCE-005 | Coverage matrix, cell identity, diversity and collision rules |
| DCE-006–DCE-007 | Admission manifest, Draft/Recipe separation and state derivation |
| DCE-008 | Existing immutable generic PFI generation path |
| DCE-009–DCE-010 | Separate typed runtime index and explicit profile routing |
| DCE-011–DCE-012 | Versioned evaluation corpus, release gates, atomic activation and rollback |
| DCE-013 | Reference-only source metadata and independent authoring rule |
| DCE-014 | Deterministic inventory command and reconciled report |
| DCE-015 | Authenticated bounded private API and API-owned database access |
| DCE-016 | Profile population capacity calculation and fail-closed limits |

## Architecture

```text
official curriculum / reference maps
                 |
                 v
coverage-matrix.v1.json -----> coverage inventory/report
          |                              ^
          v                              |
authoring manifests -> validation/evidence/admission manifests
          |                              |
          +---------- release layout ----+
                            |
             +--------------+---------------+
             |                              |
             v                              v
      generic PFI generation       typed profile generation
             |                              |
             +----------- active pointers -+
                            |
                            v
 profile structuring -> profile-specific candidate API -> reranker -> proof planner
```

### Component ownership

| Component | Ownership | Responsibility |
|---|---|---|
| Canonical coverage matrix and cross-repository rollout | parent repository | Define completeness, references, manifests, inventory and orchestration |
| OpenMath profile validators, typed registries, Draft DTOs and structuring/reranking | `pals-agent` | Produce and validate profile-correct queries and consume candidate results |
| Immutable generation schemas, release admission, active pointers and candidate reads | `pals-api` | Own searchable local/production catalog state and internal runtime API |
| Local authoring manifests and preparation utilities | parent scripts plus `pals-agent` libraries | Revalidate candidate/evidence artifacts and produce sealed release layouts |
| Read-only catalog inspection | `pals-draft-admin` | Inspect active searchable content without becoming an authoring or release path |

## Coverage model

The canonical artifact is
`specs/draft-catalog-expansion/coverage-matrix.v1.json`. It is a closed,
versioned JSON object. Its stable identifiers are independent of Draft IDs.

```text
scope
  id, kind, reference, reference_revision
  defaults
    required_modes[], required_difficulties[]
  families[]
    id, title, prerequisites[], profile_requirement
    required_modes[] (or inherit scope defaults)
      mode, minimum_distinct_patterns
    required_difficulties[] (or inherit scope defaults)
      difficulty, minimum_distinct_patterns
    draft_bindings[]
      draft_id, primary_mode, difficulty, authoring_manifest, admission_manifest|null
```

Initial problem-mode vocabulary is deliberately small:

- `recognize`: identify a definition, condition, or applicable theorem;
- `compute_construct`: compute, transform, or construct an object;
- `justify_prove`: supply a reusable deductive argument;
- `model_apply`: translate and solve an application or representation problem;
- `counterexample_audit`: refute a nearby claim or identify a missing hypothesis;
- `synthesize`: combine prerequisites or techniques across families.

Each family declares only applicable modes. Difficulty is `introductory`, `standard`, or
`advanced`; a family is not forced to manufacture an inauthentic difficulty or mode. One
Draft has one primary mode and one difficulty, so it can satisfy both axes without being
counted twice. A family's minimum distinct-pattern target is the larger of the sum of its
mode minima and the sum of its difficulty minima. Targets are therefore derived from the
declared axes, not assigned as a top-down row quota.

The initial school contract contains 107 concept families: 33 elementary, 23
junior-high, and 51 high-school families. Every family requires one
`compute_construct`, one `justify_prove`, and one `model_apply` pattern, yielding 321
distinct primary mode cells. The initial undergraduate core contains 100 concept families
across logic/foundations, discrete mathematics, linear algebra, geometry, calculus, real
analysis, multivariable calculus, ODE, probability/statistics, abstract algebra, and
number theory. Every family requires one `recognize`, `compute_construct`,
`justify_prove`, `counterexample_audit`, and `synthesize` pattern, yielding 500 distinct
primary mode cells. The commutative-algebra advanced scope retains its separate 500-pattern
chapter target and must later refine every chapter target into the same mode/difficulty
axes before it can report comprehensive.

### Distinctness

A binding can satisfy a separate structural pattern only when its canonical OpenMath
operator/subtree signature or declared proof-method signature is materially different.
Canonical byte equality, alpha-equivalence, constant-only substitution, variable renaming,
and prose-only changes collapse to one pattern. A manual review is required when structural
signatures differ but the reusable proof method is unchanged.

## Authoring and admission artifacts

Curriculum/reference classification remains outside Draft records. A release layout binds:

- one coverage matrix revision;
- one or more closed authoring manifests;
- profile validator, registry, canonicalizer and embedding bindings;
- canonical Draft content;
- optional external proof-evidence references, which do not control Draft eligibility;
- statement/OpenMath alignment reviews;
- positive and hard-negative evaluation queries;
- a deterministic manifest digest.

The inventory derives states from artifacts rather than writing mutable status onto Drafts:

```text
backlog -> authored -> profile_valid -> reviewed
        -> admitted -> embedded -> published -> retrieval_passing
```

An absent `draft_bindings` member is equivalent to an empty list in the initial matrix;
future bindings must use the closed binding object above. A null `admission_manifest`
means authored-but-not-admitted and never counts as admission. Failure in a later state
does not mutate earlier immutable evidence. It simply prevents a release layout from
advancing or an active pointer from moving.

## Generic publication

The existing PFI generation model remains the generic runtime boundary. The release input
must be built from the complete admitted generic manifest, not the 31-row packaged seed or
the mutable 431-row local table. Publication creates immutable rows, records compatible
fingerprint and runtime provenance, verifies the actual row count, and moves the singleton
active pointer atomically. Rollback selects a previous compatible published generation.

The legacy `prepare-local-draft-batch.py` remains a legacy/local authoring tool and is not
used as evidence of production publication.

The coverage inventory computes the required generic population before release. The
current v1 PFI population bound is 4096 rows. If the required active generic population
exceeds the bound, the limit and every request/result/database constraint that encodes it
must move together under a versioned compatibility change; splitting or truncating a
complete generic scope without an explicit profile or scope boundary is forbidden.

## Typed publication

Typed OpenMath is not inserted into the generic PFI generation. `pals-api` owns a separate
typed runtime catalog with the same immutable-generation principles, keyed by explicit
`profile_id`:

```text
typed_catalog_profiles
typed_catalog_generations(profile_id, generation_id, bindings, row_count, state)
typed_catalog_rows(profile_id, generation_id, six-field Draft content, embedding)
typed_catalog_active(profile_id -> generation_id)
typed_catalog_quarantine
typed_catalog_publications
```

The current `pals_local_typed_catalog` remains authoring evidence. A release-only command
revalidates its sealed manifests and evidence, builds a profile-specific release layout,
and admits it into the API-owned runtime catalog. It never copies an unreviewed proposal
merely because it exists in the local authoring schema.

## Profile routing and retrieval

The structuring result becomes a discriminated internal value:

```text
profile_id, canonical_openmath_xml, canonicalizer_version
```

The selected profile determines the validator, registry, embedding namespace, active
generation, structural comparator, and reranker input. Generic v1 remains compatible and
continues to use its existing API contract. Typed profiles use a separate versioned internal
candidate contract containing `profile_id`; no implicit generic/typed union or cross-profile
fallback exists.

The typed contract reuses the existing private candidate security posture: one dedicated
worker secret, constant-time comparison, an exact JSON content type, duplicate-member
rejection, closed request/response models, bounded bodies, bounded candidate counts, and
stable incompatible/unavailable errors. `pals-api` owns the catalog connection and read
role. The agent receives neither a database URL nor catalog grants.

If structuring cannot select exactly one supported profile or the selected runtime catalog
is unavailable, retrieval returns a stable no-match/error classification. It does not search
another mathematical type system.

Typed model output uses a versioned, profile-aware expression AST with strict provider
schema output. Fixed-arity operators have named argument slots (for example, equality
has left/right operands and transpose has one argument); their legal operator sets come
from the selected validator contract. A variable-arity application cannot accept a
fixed-arity operator. Binders explicitly carry declarations and a body. Carrier, casts,
symbol identity and attributes remain explicit model input, never inferred by the codec.
Sort constructors belong only to a separate declaration-sort schema derived from each
profile's sort parser; they cannot appear as ordinary expressions. Sort parameters use
the exact permitted variable and integer-dimension forms. Term and proposition expressions
retain the existing validator's language rather than introducing new logical restrictions.
The local decoder independently checks duplicate members, closed fields, legal operators,
XML characters and byte/node/depth limits, then serializes exactly that tree with standard
XML escaping. It does not infer any missing
mathematical node. The selected existing XML canonicalizer and validator remain authoritative;
registry and admission fingerprints do not change. Raw XML is not accepted as a fallback.
Schema opt-in leaves generic provider requests unchanged. Refused or incomplete provider
responses are not accepted as partial trees. Evaluation implementation identity includes the
codec and provider adapter, so old XML observations cannot certify the new transport.
The generic-tag v1 diagnostic remains failed evidence: it admitted the structurally legal
but mathematically invalid tree `eq(transpose(A,B))`. Its XML balance check and 16 example
roundtrips are not evidence of correct expression generation. The replacement transport
must cover every fixed-arity symbol in all 16 profiles and reject that malformed shape
before XML validation; versioned real-input observations must be collected again.
The v2 real transpose diagnostic also failed: it substituted the sort `Matrix(K,2,2)`
for the literal matrix value. That failed observation motivates the explicit sort/context
separation; it must not be counted as a successful structurally or semantically valid query.

The v3 real replay accepted schema-valid zero matrices in place of supplied literals.
Transport v4 therefore gives matrix and column literals dedicated carrier, dimension and
entry slots. Entry count must match the explicit dimensions; neither values nor casts are
filled in by the codec. A separate pre-embedding preservation check for fully explicit
integer matrix literals compares their dimensions and row-major values with the validated
XML. Missing, altered or extra numeric literals trigger the same bounded correction path.
This narrow check is not a theorem-equivalence checker: operation roles, assumptions,
symbolic entries and unsupported natural-language notation still need semantic review and
real corpus evaluation. Old v3 observations cannot certify this implementation.

Typed structuring has one bounded repair opportunity only after tree decoding, canonicalization or profile
validation rejects the first generated tree. The correction receives the unchanged original
statement, selected registry and grammar, plus bounded prior tree output and validator diagnostics
marked as untrusted data. It never inserts tags or infers missing mathematical content in
code. Canonicalization and the complete selected validator run again. Both model calls share
a monotonic 90-second deadline; expiry prevents an additional call. A provider failure ends
structuring immediately. Embedding, candidate lookup and reranking are not retried by this
path. Private evidence records the first validation failure and whether correction was used;
public projection continues to use the closed existing failure classification. Evaluation
must use this same runtime limit and implementation identity and must not discard failed
attempts or reuse observations from the previous implementation as new results.

## Inventory and reporting

`pals-scripts/audit-draft-catalog-coverage.py` reads the coverage matrix and repository
manifests. With an explicitly provided read-only database connection, it also reconciles
active generic and typed generations and embedding rows. It emits deterministic JSON and a
short human report with:

- required and filled cells by scope/family/mode/difficulty;
- authored, admitted, published, and retrieval-passing counts;
- duplicate/collision findings;
- profile and manifest gaps;
- unknown or orphaned Draft identities;
- stale binding or count mismatches;
- a `comprehensive` verdict per named scope only.

No aggregate total may hide an incomplete required scope or advanced extension.

## Evaluation and release gates

For typed retrieval, a match means a strategy that can advance a concrete proof step
for the unchanged query, preserving its assumptions, quantifiers, carriers, dimensions,
literal values and conclusion. Topic similarity or a strategy that only refutes a nearby
false equality is insufficient. Generalization, specialization and auxiliary lemmas remain
allowed; canonical equality is evidence, never a mandatory selection filter. An empty
selection means no supported proof strategy was identified, not a falsity certificate.
The typed selector uses its own versioned prompt and SHA-256 in request compatibility;
the generic relevance selector's pinned contract remains unchanged. Positive evaluation
requires the expected strategy to be selected, not exact equality of the selected ID set.

The September 30 real twelve-query replay showed that prompt-only proof-support selection
still matched five of six false literal statements. A conservative retrieval-only filter
therefore checks the strictly closed fragment `forall K : Field, P`, with K as its sole
declaration and P a direct equality, inequality or two-sided-inverse predicate. Supported
literal matrix operations are evaluated exactly over rational numbers, with bounded
dimensions, tree size, arithmetic operations and integer bit lengths. A false result over
this particular field supplies a counterexample to the structured universal query and
suppresses Draft selection. A true result, unsupported expression or resource limit makes
no universal claim and proceeds through the normal selector. Hypotheses, existential
quantifiers, other variables and logical combinations are not evaluated by this filter.
The filter does not certify the translation from natural language, issue a semantic QA
receipt, change a proof's state or establish proof correctness. Its version and bounded
reason are recorded in private retrieval evidence; release evaluation still checks exact
structuring and downstream verified completion independently.

Each changed family supplies exact natural-language queries, reviewed canonical OpenMath,
expected family/profile, expected positives, and close hard negatives. The release evaluator
runs the real structurer, embedding binding, active candidate query, structural reranker and
runtime limits. It reports structuring success, Recall@k, MRR, false match/no-match, and the
downstream verified proof completion rate.

Release order is:

1. validate closed artifacts and evidence;
2. build embeddings under the pinned profile binding;
3. create an immutable inactive generation;
4. verify generation counts and evaluation gates;
5. atomically move the profile's active pointer;
6. record publication evidence;
7. rerun an active-runtime smoke query.

Any failure before step 5 leaves the old generation active. A failure after step 5 triggers
an explicit rollback publication to the prior compatible generation; historical rows are
never edited.

## Initial implementation slice

The first slice produces evidence without pretending to complete the full catalog:

1. canonical coverage-matrix schema plus school/university seed matrix;
2. deterministic repository inventory covering the current 431 generic and 163 typed
   local cards, with their actual publication distinction;
3. generic publication-input reconciliation that identifies the 31/431 gap;
4. an 18-pattern school algebra slice spanning exactly the six anchor families named in
   DCE-T008, with one compute/construct, justify/prove, and model/apply pattern per
   anchor; adjacent precursor families remain independently unfilled;
5. the six-card `typed-math-matrix-v1` profile released and retrieved through the new
   profile-specific runtime path, without claiming linear-algebra completeness;
6. positive and hard-negative runtime evaluation for both slices.

Later batches repeat the proven path by prerequisite order until each named scope reaches
its comprehensive gate.

## Validation and error handling

- Unknown fields in closed manifests fail validation.
- Unknown scope, family, mode, difficulty, profile, Draft, or evidence identity fails
  inventory and release preparation.
- Missing database access produces a repository-only report explicitly marked
  `runtime_not_verified`; it cannot produce a comprehensive verdict.
- Binding, digest, row-count, or evaluation mismatch blocks activation.
- Profile ambiguity or mismatch never falls back to another profile.

## Testing strategy

- Unit tests: schema closure, identifier rules, target derivation, duplicate collapse,
  state derivation, deterministic output and fail-closed errors.
- Integration tests: real PostgreSQL generic and typed generation admission, role grants,
  immutable history, failed activation, rollback and active reads.
- Agent/API contract tests: profile discriminator, validator/registry mismatch, response
  digests, no cross-profile fallback, existing generic v1 regression.
- Retrieval tests: real embeddings or the release-pinned provider test boundary,
  structural reranking, positive/hard-negative corpus and runtime result limits.
- End-to-end smoke: publish one generic and one typed generation, query both through the
  real internal API, and verify downstream proof completion through the pinned verifier.

## Risks

- **False completeness from loose metadata:** closed coverage cells and inventory
  reconciliation prevent manual percentages from becoming release evidence.
- **Typed proposal mistaken for admission:** authoring and API-owned runtime catalogs remain
  separate and require a release-only admission step.
- **Profile explosion:** new profiles require an explicit family gap, fixed registry and
  hard negatives; similar carriers should reuse an existing immutable profile when exact.
- **Evaluation overfitting:** every positive family includes nearby false or different
  statements and reports false-match/no-match separately.
- **Large release regression:** immutable inactive builds, active-pointer transition and
  rollback preserve the last compatible catalog.
