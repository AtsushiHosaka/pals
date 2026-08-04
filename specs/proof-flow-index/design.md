# Design: Proof Flow Index

## Detached Local pgvector Validation

PFI-009 is a parent-owned developer fixture under
`pals-scripts/continuity-pgvector-validation`; it is not Agent release tooling, API migration
code, or a PFI catalog implementation. Its only raw-card input is the hash-pinned child catalog.
Before `validate` performs Docker interaction, the runner reads the child frontmatter and catalog
as bytes, requires
the child to be approved, requires `parent_spec.path` to equal `specs/proof-flow-index`, compares
each child-pinned parent requirements/design/tasks SHA-256 to the current exact bytes at that path,
requires current parent `requirements.md` status `approved`, and recomputes the catalog SHA-256.
It rejects any mismatch or LF, then reserializes the string-only catalog schema with sorted UTF-8
keys and no whitespace to prove the bytes are its JCS form. It verifies the complete derived
source-ID set, root coverage profile, every per-card coverage object, and every required source
field. It uses no alternate card projection or generated
seed/manifest/evidence input.

The runner uses only Python standard-library parsing/hashing/subprocess facilities and a checked
locally cached `pgvector/pgvector:pg16` image. It first checks the image is present, then invokes
Docker Compose with the fixed project name `pals-continuity-pgvector-validation` and explicit
no-pull behaviour. The checked-in Compose file declares a single PostgreSQL service, no `ports`,
`network_mode: none`, no named volume, and `tmpfs: /var/lib/postgresql/data`. The runner uses only
`docker compose exec` to execute `psql` inside that networkless container; it refuses a
service/container whose resolved Compose configuration or Docker network mode differs. It also
refuses a service/container whose Compose project label, image, or configuration differs; it does
not accept a host DSN, database URL, provider option, or arbitrary Compose-file path.
The service environment has exactly `POSTGRES_DB=pals_continuity_validation` and
`POSTGRES_HOST_AUTH_METHOD=trust`, with no password/credential/secret key or value. `trust` is
confined to the container because `network_mode:none` and no port are both independently verified.

The only executable entrypoint is
`pals-scripts/continuity-pgvector-validation/run.py`. From the repository root it accepts exactly
one positional mode, `validate` or `teardown`, matching the two requirements-defined `python3`
commands. Any missing/extra/unknown argument fails before Docker interaction; no Make target,
shell wrapper, environment override, or alternate executable is a supported contract path.
`validate` alone performs the child/catalog/current-parent identity preflight and load. `teardown`
does not open any child/catalog/parent input: it loads the fixed Compose path, checks the fixed
project name and matching Compose-project labels, and can then remove only that project.

After the health check, the runner sends one generated, transaction-wrapped SQL program through
`psql` running inside that PostgreSQL container. The program creates `vector`, then creates only
`continuity_validation_cards` with every catalog card field: ID, canonical statement, coverage,
coverage objective, bilingual and hard-negative retrieval fields, Lean target, novelty key,
OpenMath, proof strategy, and Sketch. It adds a canonical complete-card source hash, a fixed
`vector_kind` check of `deterministic-test-v1`, and `validation_vector vector(3)`. It inserts every
card in the validated current source set exactly once. It does not name or create a `pfi_catalog_*`
relation, active pointer, manifest, release evidence, or application schema. SQL literals are
constructed by the runner's single-quote/byte-safe escaping routine; no untrusted shell expansion
or temporary seed file is used.

For a card, `source_sha256` is SHA-256 of the UTF-8 canonical JSON object whose keys are exactly
the complete validated catalog-card key set; its values are copied byte-for-byte from that card.
Let `h0..h5` be the first six bytes of that hash, and let
`u0,u1,u2` be their big-endian unsigned 16-bit pairs. The deterministic test vector is
the three IEEE-754 binary32 values obtained by round-to-nearest, ties-to-even from the exact
rationals `[(65536+u0)/65535,(65536+u1)/65535,(65536+u2)/65535]`. The runner derives that binary32
value with integer/rational arithmetic, serializes each component with Python's exact
`format(float32_value, ".9g")` rule, and uses those three decimal strings as the pgvector literal.
It rejects a non-finite, zero-norm, duplicate, or collinear validation vector, and labels every
stored row `deterministic-test-v1`. This construction intentionally has no language or mathematical
similarity semantics.

The runner queries each saved vector with cosine distance and requires the sole top-one ID to be
the input card's ID. It separately checks extension availability, relation name/column shape,
derived source-set cardinality, source hashes, IDs, vector kind, and the exact `network_mode:none`, absence
of a public port, and absence of a named volume in the resolved Compose configuration and
running-container inspection. Its terminal report contains only the expected
catalog-hash prefix, project name, sorted IDs, vector-kind, pass/fail counts, and teardown status.
It never prints a card field, SQL program, DSN, password, provider response, or copyrighted source
material.

`validate` leaves the distinct tmpfs-backed project available for manual local inspection. The
fixed `teardown` mode runs only `docker compose --project-name
pals-continuity-pgvector-validation down --volumes --remove-orphans` against the checked-in fixture
file and verifies no project-labeled container remains. It refuses any project-name override and
remains callable when the catalog, child/parent hash/status, or image has subsequently drifted or
disappeared. Failure before or during load runs that same project-scoped teardown and returns
nonzero; it cannot roll back, connect to, mutate, or report a PFI/application database. PFI-009 is
deliberately outside PFI-008 release orchestration, so it does not create a seed, receipt,
manifest, generation, or release/semantic-evaluation evidence.

## C14N v4 Release-Tooling Alignment

All PFI-owned seed and retrieval compatibility metadata uses the single exact string
`openmath-cdbase-alpha-c14n-v4`. `ProofDraftSeedBuilder`, its fingerprint and build provenance,
the CLI constructor, worker-image artifact checks, and the private candidate/runtime fingerprint
validator share that value. A v3 value is rejected at the normal fingerprint/provenance boundary;
there is no compatibility alias. The older non-PFI Draft catalog keeps its own historical version
because this restoration does not migrate it. Updating metadata alone does not construct an
artifact, sign a seed, call an embedding provider, contact an API, or alter a database.

## Seed Function-Sort Conformance Restoration

`SPEC-CHG-2026-07-27-PFI-SEED-FUNCTION-SORT-CONFORMANCE` changes no normative grammar or retrieval
result. The existing iterative inference must validate the declared sort of every
function-consuming slot rather than closing only the first child of `OMA`. Build tooling rejects
all nine known incompatible source rows atomically. The checked-in source seed removes those rows;
the corpus keeps its six queries and exact candidate/selection rows while updating only source
inventory metadata. Seed JCS, manifest, fingerprint-bound build provenance, and OCI evidence are
regenerated from the remaining 31 rows. That restoration introduces no synthetic theorem/OpenMath
replacement; a later PFI-008 generation may add only its independently authored, typed-profile-valid
curriculum rows through the separate manifest and Lean-verification gate.

## Overview

Candidate implementation design for the focused v1 OpenMath Draft retrieval slice. Future Proof Flow
entities, trace retrieval, and general/runtime curation are outside this bundle. PFI-008 adds only
a first-party static continuity curriculum seed path.

## Typed Continuity and Curriculum-Seed Expansion

## Continuity Volume-Floor Gate

`ContinuityVolumeGate` runs after `CoverageProfileGate` and the complete source-set/Lean-receipt
gate, before seed embedding and API admission. It counts distinct IDs in catalog, successful
receipts, seed delta, and candidate active generation; each count must be at least 100 and every
set must be bytewise identical under the existing Draft-ID order. It rejects 99 or fewer rows,
duplicates, and set mismatch without a partial seed or database transaction. It neither generates
content nor weakens PFI-008's profile/originality/review constraints; PFI-009's detached fixture is
outside this gate.

PFI-008 extends the existing iterative sort inference with `real_function`, `real_sequence`, and
`natural_index`.
The PALS typed quantifier binders declare one of those sorts before use; ordinary quantifiers still
declare only terms. `sequence_lambda` binds only natural-index variables and explicitly constructs
a real sequence; `index_zero`, `index_succ`, and `index_to_real` are its only index primitives. A
`continuity-v1` `fns1:lambda` or `sequence_lambda` has exactly one declaration, respectively yielding
`ℝ → ℝ` or `ℕ → ℝ`; multi-variable generic binders remain outside the pilot. A term-body
`fns1:lambda` explicitly supplies a real function in a registered real-function position. The
validator checks each declaration and use, rejecting a free, undeclared, conflicting, or swapped
sort. `pals1:apply` is the sole real-function application constructor: it accepts a real function
and a term. Within a `continuity-v1` `sequence_lambda` term body,
`pals1:sequence_apply` is the sole real-sequence application constructor: it accepts a real
sequence and natural index and returns a term; it is invalid outside that body. This supplies the
value `u(n)` needed by the forward sequential-continuity law without allowing an `OMV` to become an
application head. The registered function/sequence constructors provide the closure forms.
Existing lexical binding, alpha-normalization, C14N, resource bounds, and closed retrieval
admission run unchanged after this additional inference.

The pre-child C14N bootstrap is strictly lower-level PFI-001 conformance work. Its Agent-owned
canonicalizer accepts only synthetic/golden typed XML strings in memory, validates the complete
typed/scope/valid-XML transport-canonical C14N v4 contract, and derives the fixed two-member
novelty JCS preimage. It rejects the raw empty-prefix transport artifact rather than repairing it
on read. It does not
discover or read a curriculum companion, construct a card/Lean target/wrapper, embed, write a
manifest/evidence/receipt/seed, use a network/image/database, or change runtime retrieval. The
separate `CoverageProfileGate` remains the first component permitted to read the re-approved child
catalog and is still behind every PFI-008 release gate.

`CurriculumSeedGate` runs only in Agent release tooling after every pilot row passes typed
validation and canonicalization and before embedding. It reads
a deterministic no-LF JCS `continuity-v1` coverage manifest alongside a first-party static seed,
uses the signed 31-row base projection plus manifest rows as the exact disjoint full seed,
requires one manifest entry per pilot Draft ID, verifies the bound original-content and Lean-verifier evidence,
rejects prohibited source bytes, raw model content, incomplete/duplicate mappings, a missing
independent-authorship/prohibited-source-review attestation, or a failed verifier result. The
independent source review uses `manual_external_comparison_v1`: a non-author manually compares the
frozen hashed fields in an out-of-repository workspace, retains no derivative, and the PRX signing
operator confirms that procedure before signing. It therefore attests to no copying or close
paraphrase without introducing Tao material into release inputs. It resolves every manifest hash to
the requirements-defined no-LF JCS release-evidence object, deterministically translates the canonical OpenMath through
`pals.openmath-to-lean.continuity-v1`, and asks the existing PAE-017 verifier to compile a
no-network, exact-template wrapper from the no-LF canonical Lean target to the named declaration;
the receipt hashes that target itself as `lean_declaration_sha256`. It packages the validated
manifest and evidence-bundle identities with the existing signed-worker seed artifact. It never
adds a Draft field, direct database capability, or runtime ingestion path.
The original Lean theorem module exists only as a no-follow temporary Agent build input; the wrapper
imports its deterministic module name and the gate hashes it before verifier submission, then
removes it after receipt generation. API receives only the hash-bound receipt in the evidence bundle.
The API release controller treats the manifest as a release-admission input, not catalog content:
the existing PRX-signed worker config's PFI-BP-001 label binds its normalized path and raw-file
digest, and binds the separate evidence-bundle path and digest the same way. API extracts both with
the existing no-follow OCI overlay procedure, requires the exact requirements-defined JCS schemas,
its seed-manifest/hash projections, and every manifest-to-evidence object hash, then atomically
publishes the full new generation or leaves the prior one active. Lean source and user-facing
explanations are neither passed to the API nor stored in the Draft catalog.

`continuity-v1` coverage is a content-family profile with nine retained objective tokens, not a
fixed-card matrix. Before embedding, Agent release tooling derives `P` from the approved child
catalog and requires the catalog, coverage manifest, evidence bundle, Lean-receipt collection, and
signed-seed delta to have that same unique nonempty ID set. It validates the catalog/profile/card
coverage hashes, every required semantic signature, every unique novelty key and canonical OpenMath
byte string, and each card's Japanese/English positives and hard negative. It rejects any missing
objective, construction, applicable quotient hypothesis, profile signature, or source-set mismatch.
`CoverageProfileGate` first expands the requirements-defined `C0` table into seven-field signature
JCS, verifies that the child profile includes it, then checks every coverage object against the
canonical OpenMath tree. It requires and strips the exact closed typed theorem-binder prefix before
matching the Core Theorem-Shape Library residual; it rejects a free, extra, or vacuous binder,
except for the exact unused natural-index binder of the required constant-sequence shape and the
one-variable inner universal nonzero predicate required only by global-continuity division.
It then checks context predicates and direct consequent constructions, antecedent role-specific
prerequisites, proof root shape, representation, quotient nonzero form, distinct left/right,
numerator/denominator, and inner/outer binder connections, and derived novelty digest. It emits
only profile/card hashes and dispositions. The gate accepts original concrete or sequence variants
only when their signature belongs to the approved profile and their alpha-canonical OpenMath differs
from every other card.
Recorded reranker fixtures, not a live model call, assert the specified selected Draft IDs/no-match
outcome and every one of the six pre-PFI-008 governed-query candidate/selection outcomes
byte-for-byte. The source-review attestation is hash-bound to each statement, strategy, and Sketch
and accepted only as part of the PRX-signed worker artifact; its role is a review disposition, not a
new credential or API identity.

The release evaluator separately consumes the holdout corpus. It partitions cases by the card
coverage-signature hash and compares the candidate with the preceding compatible generation using
identical recorded inputs. It records content-free aggregate and partitioned retrieval/rerank,
negative, Lean, latency, and source-set metrics; shared-signature regression or a new-signature
miss rejects admission. The local PFI-009 source-hash vectors cannot enter this evaluator.

## Requirements Traceability

Explicit trace keys: PFI-001, PFI-002, PFI-003, PFI-004, PFI-005, PFI-006, PFI-007, PFI-008, PFI-009, PFI-010.

| Requirement | Design Coverage |
|---|---|
| PFI-001–PFI-002 | Bounded exact OpenMath grammar/canonicalizer and minimal bounded Draft record |
| PFI-003 | Closed Agent admission, one worker-authenticated private API candidate call, API-owned UTF8/`C` DB-only `LIMIT 8` query, exact Agent structural evidence, one fixed-contract real PAE draft-role rerank selecting zero through four ordered contexts, and exact normalized content-free usage |
| PFI-004 | Aggregate resource validator, source/OCI provenance, fingerprint/catalog compatibility gate, migration, explicit errors, release-only eight-row admission, and pinned-price rational release evidence |
| PFI-005–PFI-007 | Retired; successor Spec required |
| PFI-008 | Typed continuity/limit/sequence profile plus mechanically expanded content-family coverage/AST-realization gate, complete per-card evaluation and independent holdout comparison, first-party static curriculum manifest, original-content, Lean-verification, and atomic-publication gates |
| PFI-009 | Parent-owned detached tmpfs Compose fixture, exact hash-pinned catalog reader, deterministic non-semantic test vectors, fixture-only pgvector DDL/load/self-nearest-neighbour assertion, and project-scoped teardown |
| PFI-010 | ContinuityVolumeGate exact 100-ID floor and complete catalog/receipt/seed/active-generation equality before embedding or API publication |

## Provider-Schema Compatibility Restoration

For PFI-003 and PFI-004, `DraftRerankerRequestBuilder` emits the exact strict provider schema from
requirements with only `pattern` on ID strings and `maxItems` on the selection array. The ID pattern
itself is the complete one-through-64-character domain; the provider schema does not use
`maxLength`, `uniqueItems`, or any other unsupported keyword. A closed recursive schema-keyword
validator and byte-exact request fixture reject every added, removed, or substituted keyword before
network I/O.

`DraftRerankerResponseParser` remains duplicate-aware and independently enforces zero-through-four
ordered unique supplied IDs, the same ID grammar, foreign-ID rejection, and all response limits.
Removing the unsupported provider keywords therefore changes no accepted application result.

Historical specification-review ledgers, verdicts, reviewer identities, counters, and reviewed-file
hashes are not design inputs and remain external to the canonical bundle.

The release-live oracle distinguishes provider schema admission from a generated invalid response.
An `invalid_json_schema` or equivalent rejection before generation is a release-blocking schema
compatibility failure and cannot satisfy the live rerank gate. Reapproval changes only requirements
frontmatter and the owning root index row after fresh review; a different reviewer checks the exact
inverse status-only transform.

## Usage and Cost Evidence Design

For PFI-003 and PFI-004, `DraftRerankerResponseParser` requires the exact duplicate-aware
extra-forbid `usage` object after response identity/completion validation. `UsageNormalizer` parses
the three required top-level counts and two required nested counts as bounded nonnegative integers, checks
cached input against total input, reasoning output against total output, and total equality, then
produces the seven exact normalized counts. Unknown, missing, duplicate, non-integer, inconsistent,
or over-bound values map to `reranker_invalid`; no partial usage object is salvaged.

`ReleasePricingSnapshotRegistry` contains exactly the requirements-defined
`openai-gpt-5.4-mini-2026-07-27` USD-per-million-token snapshot. It performs no network or dashboard
lookup. `ReleaseCostCalculator` uses arbitrary-precision integers to produce the exact
micro-USD numerator/denominator, round-half-up micro-USD value, and six-decimal USD rendering.
Reasoning tokens remain a reported subset of output tokens and are charged exactly once at the
output rate.

`DraftRerankerReleaseEvidenceWriter` accepts only a governed corpus ID, selected governed Draft IDs,
canonical UTC observation time, bounded latency, normalized usage, the exact pricing identity, and
the exact derived cost object. It duplicate-aware serializes the extra-forbid evidence schema to the
external release-evidence store with encryption, access limited to exact roles
`pals_release_operator` and `pals_release_auditor`, expiry exactly 15,552,000 seconds after
`observed_at`, and scheduled deletion no later than 86,400 seconds after expiry. Raw envelopes,
request/response text, prompts, headers, credentials, response/request IDs, user/project/proof
identifiers, and free-form fields never enter the record. The writer never writes the corpus,
repository, Notion, runtime DTO, logs, traces, metrics labels, database rows, or
training/evaluation datasets. Missing corpus coverage, schema, pricing, arithmetic, privacy,
encryption, exact role binding, expiry, or scheduled-deletion configuration blocks release; an
overdue retained record blocks the next release until audited deletion completes without extending
retention.

## Affected Repositories

- Parent: cross-repository semantic and retrieval contract.
- `pals-agent`: canonicalization, embedding, private-port caller, structural evidence, rerank, and
  final result boundary; no database capability.
- `pals-api`: sole Draft persistence/migration/active-generation/SQL authority and the one
  worker-authenticated private candidate port; no public PFI endpoint.
- `pals-draft-admin`: read-only operational inspection of the current Draft slice.
- `pals-datasets`: N/A in this slice because the submodule is uninitialized and owns no evidence;
  the parent owns the deterministic corpus and Agent seed bytes are read-only source evidence.

## Architecture and Components

```text
statement -> Agent OpenMath structurer/validator/canonicalizer -> Agent embedding
      -> one worker-authenticated vector-only API candidate request
      -> API admitted-PRX DB binding -> one active-snapshot UTF8/C DB-only LIMIT 8 query
      -> 0..8 ordered Draft rows -> Agent structural evidence
      -> bounded fixed Responses-API draft-role rerank
      -> 0..4 typed contexts | typed no_match

independently authored continuity cards + coverage manifest + Lean-verifier evidence
      -> Agent typed validator/canonicalizer -> CurriculumSeedGate -> embedding
      -> signed worker seed artifact
      -> API complete-generation admission -> atomic active-generation switch | no switch
```

## Interfaces and Contracts

- Internal Agent Draft search returns one through four ordered Draft contexts, canonical query
  OpenMath, per-row cosine/vector/structural evidence, exact-equivalence flags, and compatibility
  metadata, or a typed zero-selection `no_match`.
- Reject before XML parse or embedding when input exceeds 65,536 UTF-8 bytes. During one iterative
  validation walk, enforce at most 4,096 nodes, depth at most 64 with root depth 1, 1..256 variables
  per binder, and 20,000 code points per attribute/text/literal.
- Accept only exact OpenMath namespace `http://www.openmath.org/OpenMath`, the closed PFI-001
  element/child/attribute table, exact standard `cdbase` `http://www.openmath.org/cd`, and exact PALS
  `cdbase` `urn:pals:openmath:cd:v1`. Reject every unlisted constructor or attribute; the focused
  path does not reuse the broader general-purpose validator surface.
- Validator tables are generated from the normative requirements registry for the exact standard
  `relation1|logic1|arith1|set1|setname1|alg1|quant1` and PALS `pals1` symbols, roles, and
  arities, including the registered lambda/function-consuming forms. Implementation source is
  evidence, never authority.
- Run the closed `term|proposition|term_function|predicate_function` inference during the same
  iterative walk. Reject `OMV` application heads, wrong argument sorts, function values outside
  registered positions, and every non-proposition root before canonicalization or embedding.
- For PFI-008, extend that same walk with `real_function|real_sequence|natural_index`, the exact PALS typed
  binders, and the registered positions in requirements. A term-body lambda can satisfy a
  real-function position and `sequence_lambda` constructs a real sequence from natural-index
  variables; for a `continuity-v1` row each of those lambdas has exactly one declaration; a declared variable's
  uses must agree with its binder sort. `pals1:apply`, `pals1:sequence_apply`, and the named
  function/sequence constructors are the only new application/closure forms. Within the term body
  of a `continuity-v1` `sequence_lambda`, `sequence_apply` returns a term only from a real sequence
  and natural index; it is invalid outside that body. Direct `OMV` heads, unbound variables,
  ordinary term variables in typed positions, and conflicting function/sequence/index positions
  remain invalid before any provider or database work.
- Preserve free term `OMV` only in lower-level canonicalizer/feature fixtures. A distinct lexical
  admission walk requires every retrieval `OMV` to resolve to an enclosing binder and rejects a
  free variable before embedding, DB access, evidence, or rerank.
- Resolve `cdbase` from the nearest nonblank self/ancestor value or the exact standard default.
  Alpha-normalize with one document-global preorder counter, left-to-right declarations, same-binder
  duplicate rejection, lexical shadowing, and unchanged free-variable bytes. Remove only the
  requirement-defined ignorable whitespace, serialize through CPython 3.12.13 ElementTree C14N 2.0
  with mandatory prefix rewriting. Treat its raw ` xmlns:n0=""` result as the exact intermediate,
  remove exactly one such literal, require direct parser round-trip and exact regeneration, and
  compare only those valid transport-canonical UTF-8 bytes for equivalence. Admission binds
  the v4 canonicalizer and exact `sysconfig`-derived raw ElementTree source file through the
  `PFI-BP-001` OCI-config child property inside the already PRX-signed worker image. A no-network,
  content-addressed OCI Image Layout reader validates duplicate-aware closed
  index/manifest/descriptor JSON, exact config/layer blobs and descriptor size/digests,
  the two labels, safe overlay extraction, and the labeled seed file against the admitted
  platform-specific worker image/source without trusting the carrier or adding a parent manifest
  row. The API release controller alone extracts and imports the seed. Live database validation
  exact-matches the admitted PRX Infra
  environment/endpoint/port/name/resource to the approved IAM-verify-full or local-token
  connection plus PostgreSQL 16/pgvector/UTF8/`C` session observations; no database OCI identity is
  claimed. Global namespace registration is mutation-tested and cannot change bytes.
- API `ActiveCatalogSnapshotRepository` owns and reads one immutable readable generation containing
  exact signed-seed manifest/count, fingerprint, runtime provenance, equal active row count,
  eligible seed rows, and quarantine ledger.
  Publication validates the complete six-clause eligibility predicate and count, then atomically
  switches one pointer. Release count and retrieval use the same pointer/population in one
  repeatable-read transaction; every eligible signed-seed row and no other row participates.
- `PrivateDraftCandidateController` authenticates with the imported worker-secret rule before
  duplicate-aware parsing, accepts only the bounded exact vector/fingerprint DTO, and calls
  `ActiveCatalogSnapshotRepository` once. The API repository opens only the admitted typed runtime
  pool/session and executes exactly one persisted PostgreSQL/pgvector query scoped to that active
  generation and ordered by exact
  `(finite cosine_distance ASC, Draft ID valid-UTF-8 byte ASC)` using `server_encoding=UTF8`,
  `id COLLATE "C"`, and SQL `LIMIT 8`. Unit/local supports `0..7`; release admission requires at
  least eight eligible rows and observes eight. Packaged rows may seed the database only during
  API-owned migration and never participate in a runtime union or fallback. The controller returns
  the exact bounded `0..8` ordered candidate DTO and performs no canonicalization, embedding,
  structural score, rerank, or provider call.
- Agent `PrivateDraftCandidateClient` sends exactly one vector-only request after local validation,
  enforces the 10-second/no-redirect/no-retry/no-cache contract, validates every echoed
  generation/manifest/provenance/fingerprint/row/distance/order/bound, and has no PostgreSQL library,
  DSN, credential, migration, SQL, or network path to the database.
- Vector score is `clamp(1-cosine_distance,0,1)`. Structural feature multisets use exactly the
  PFI-003 `kind|symbol|integer|operator|operator-shape|argument-kind|argument-literal|binder|
  bound-count|subtree` key grammar and weights. Tests compare the complete 48-weight equality and
  71-weight quantified-equality known-answer maps byte-for-byte. Structural score is
  `clamp(0.85*(overlap/query_weight)+0.15*(overlap/candidate_weight),0,1)`, or zero if either
  feature-weight sum is zero.
- Vector and structural scores are evidence only. `DraftRerankerRequestBuilder` produces the exact
  no-LF JCS subject and exact prompt/body from PFI-003. It enforces eligible IDs matching
  `[a-z][a-z0-9_]{0,63}`, 16,384-byte natural statement,
  16,384-byte complete candidate JCS, and 262,144-byte complete provider-body bounds without
  truncation. Its closed recursive provider-schema validator admits only the exact required
  object/property/type/required/additionalProperties structure, string `pattern`, and array
  `maxItems`; `maxLength`, `uniqueItems`, and every other unlisted keyword fail before network I/O.
  `OpenAIResponsesDraftReranker` makes one HTTPS call to the exact endpoint with the
  pinned prompt hash, 512-token strict JSON Schema, absent temperature/top-p/seed/optional fields,
  90-second hard
  deadline, 65,536-byte response limit, no redirect, and no retry. `DraftRerankerResponseParser`
  requires a completed/error-null/incomplete-null exact-model response, one completed assistant
  message, one output-text item, no other output kind, at most 512 text bytes, and the exact
  zero-through-four unique supplied-ID object plus the exact content-free usage object.
  `UsageNormalizer` enforces the count bounds and equalities before returning normalized usage only
  to the release evidence path. Other top-level provider metadata is ignored after required
  identity/completion fields pass and is never persisted. Invalid usage is `reranker_invalid`;
  invalid and unavailable paths remain distinct and no alternate prompt/provider/catalog
  participates.
- Validate exact dimension, finite binary32 components, positive norm, finite pgvector binary64
  distances, private-port DTO, and admitted endpoint/resource/transport/session/live-observation
  PostgreSQL/pgvector provenance before evidence scoring. Execute every
  displayed arithmetic operation as strict binary64 without FMA/epsilon/rounding.
- There is exactly one private API candidate route and no public PFI API. Serialize only the exact
  candidate result and final match/no_match/error DTOs, JCS-rendered finite
  contexts/evidence, closed compatibility/reranker provenance, and error precedence from PFI-003/004.
  `runtime_provenance_sha256` is computed only over the exact requirement-defined
  `pals.draft-retrieval-runtime-provenance.v1` JCS-plus-LF object containing the complete
  canonicalizer and database provenance.

## Data Model and Migration

- Current Draft slice: six required columns `id,canonical_statement,openmath_xml,proof_strategy,
  sketch_steps,embedding` plus separate compatibility metadata. IDs are unique. Packaged/in-memory
  `ProofDraft.matched_prompt` maps byte-for-byte to `canonical_statement` and never creates a seventh
  independent field.
- PFI-008's coverage manifest is an Agent release artifact, not a Draft row, database column,
  candidate DTO member, API route payload, reranker input, or explanation store. Its no-LF JCS rows
  map every and only pilot Draft ID to the requirements-defined coverage, statement/OpenMath hashes,
  and attestation/Lean-receipt hashes. Its base-projection hash binds the unchanged five
  non-embedding fields of the 31-row seed through the currently active signed generation, so no
  unmanifested delta row can enter the full seed; Agent recomputes every full-seed embedding under
  the new signed fingerprint. The PFI-BP-001 config label binds its separate manifest and
  evidence-bundle artifact paths and raw-file digests; its root binds the no-LF JCS seed-manifest
  hash. The release build verifies those links before it packages the signed seed; the API
  re-verifies the same links before it admits the complete generation.
- Bound storage Draft strings at 20,000 code points and Sketch steps at 256 entries. Retrieval
  eligibility additionally requires the 64-character ASCII ID grammar and the complete candidate
  JCS at 16,384 UTF-8 bytes. Bound manifest rows at 4,096, the natural query at 16,384 UTF-8 bytes,
  the provider body at 262,144 UTF-8 bytes, response text at 512 UTF-8 bytes, and the database
  candidate set at eight. Primitive maxima pass independently only while enclosing aggregates also
  pass; storage-valid oversized rows are quarantined, never truncated.
- Re-embedding is explicit and atomic with exact seven-field
  `(provider,model,endpoint,deployment,revision,dimension,canonicalizer_version)` equality;
  canonicalizer version is `openmath-cdbase-alpha-c14n-v4`. Catalog compatibility uses the exact
  no-LF RFC 8785 JCS SHA-256 manifest with `canonical_statement`, unique IDs, and the count oracle in
  PFI-004.
- Agent-owned release tooling canonicalizes and embeds the bounded sole-source seed before the worker-image
  build and packages the exact fingerprint plus rows in the PFI-labeled seed artifact. The API
  release controller reads only that artifact through the verified signed-worker OCI overlay and
  scans every seed and preexisting database row against the exact attribute/resource/fingerprint
  contract without invoking an embedding provider. Only exact eligible seed rows enter the new
  generation. Every prior non-seed row, even when profile-valid, is retained only as immutable
  quarantine history; an exact same-ID six-field duplicate creates no second row. Invalid seed rows
  reject the complete artifact before a database transaction, create no row or quarantine record,
  and block publication. API persists the validated seed rows and publishes them with the revalidated
  seven-field fingerprint, exact runtime-provenance digest, and new mutually consistent manifest in
  one atomic migration. A seed row whose complete candidate JCS exceeds 16,384 bytes or whose ID is
  outside the eligible grammar blocks publication. Seed row 4,097, invalid PRX-bound worker child
  property, signed database resource/endpoint/transport/session/live observation mismatch,
  non-UTF8/`C`, any inequality among `seed_count`, `row_count`, and eligible `COUNT(*)`,
  count/query population drift, or a
  release catalog below eight eligible rows blocks admission. A failed scan or partial write cannot
  switch the active pointer or expose a mixed generation.
- PFI-005–PFI-007 are retained only as retired history and have no table/index representation.

## Continuous-On Typed-Profile Recognition

The focused continuity-v1 presence guard treats the existing `pals1:continuous_on` predicate as a
continuity construct before it invokes the unchanged typed sort checker. This correction is limited
to reachability of the existing global-continuity branch: the guard does not parse a new operator,
relax closed-variable checks, or create a normalization fallback. An explicit function remains a
one-variable term-valued `fns1:lambda` and must still satisfy the same v4 retrieval-canonical
validation as every other catalog proposition.

## State, Failure, and Recovery

- Invalid semantics, resource overflow, fingerprint mismatch, catalog mismatch, or migration
  incompatibility fails closed.
- A PFI-008 coverage-manifest, independent-content, prohibited-source, or Lean-verification
  failure fails the entire seed release before embedding or a database
  transaction. It returns no partial pilot catalog and does not affect query-time match/no-match
  semantics.
- Invalid/unknown profile symbol, free retrieval variable, or semantic inconsistency fails before
  embedding. Natural/XML input overflow precedes profile validation; row/manifest/request overflow
  precedes provider invocation. A valid no-match is distinct from invalid input.
- Map the first failure in the normative precedence to its exact error-only DTO; never include
  partial query/context or invoke fallback. COMMIT/migration ambiguity keeps the catalog
  unavailable and returns only `catalog_migration_incompatible|retrieval_unavailable`.

## Security and Privacy

- Only the authenticated Agent internal caller receives candidate and final results. Private/user
  trace indexing and a public retrieval boundary are prohibited.
- API route inventory asserts exactly one worker-authenticated private PFI candidate route and no
  public route, alias, proxy, browser/CORS exposure, or fallback. The request is vector/fingerprint
  only and Agent has zero database capability.
- The release-tooling source boundary rejects Tao PDF bytes, extracted/OCR text, images, quotations,
  raw model prompts/outputs, completed Lean source, and explanatory prose from the seed and coverage
  manifest. An independent source-review attestation covers no copying or close paraphrase without
  retaining the source material. Only the required content-free verification metadata crosses into
  the signed release artifact.
- This Spec governs the Draft operations surface only for the shared catalog contract, read-only boundary, and prohibition on public exposure without approved access controls; detailed UI behavior belongs to a separate owning Spec.

## Observability and Cost

- Preserve governed eval query, canonical OpenMath, expected Draft ID or `no_match`, scores,
  model/fingerprint, and latency in approved evaluation evidence only.
- Track structuring, embedding, and storage cost independently. Reranker release cost uses only the
  exact normalized content-free usage, pinned USD snapshot, rational arithmetic, rounding, evidence
  schema, access, 180-day retention, and deletion contract above.

## Testing Strategy

| Requirement | Test Level | Oracle | Fixtures / Environment | Execution Tier |
|---|---|---|---|---|
| PFI-001–PFI-004 | Unit/property/integration | Exact XML/attribute/cdbase/binder/seven-sort/C14N grammar; free canonicalizer versus closed retrieval; PRX-bound worker OCI config/layer/seed plus admitted endpoint/resource/transport/session/live-DB provenance; composable primitive/aggregate max/max+1 bounds; private route/auth/request/response/deadline/error contract; active-generation eligibility/count/query identity; complete feature maps; UTF8/`C` distance/ID eighth-tie order; API-only DB query and zero Agent DB capability; exact completed-model/message/output-text recorded reranker envelope; closed DTO/errors | Golden XML + adversarial boundaries + real PostgreSQL/pgvector + recorded provider envelopes | PR deterministic / main DB |
| PFI-003–PFI-004 | Retrieval eval/security | Exact supported-keyword strict provider schema; `maxLength`, `uniqueItems`, and arbitrary-keyword rejection before network; profile-valid eight-row candidates; zero-through-four expected Drafts or no_match; foreign/duplicate ID rejection; exact usage allowlist/normalization and inconsistent/unknown-field rejection; pinned pricing identity; arbitrary-precision rational cost and half-up rounding; closed external evidence schema/access/retention/deletion/privacy; one private vector-only API route; no public API/user-trace path; no Agent DB path | Preserved multilingual query corpus + exact request/schema/usage/pricing/cost/evidence fixtures + API route/capability inventory | PR/main recorded / release live |
| PFI-003–PFI-004 | Cost-bearing live | One exact fixed-contract provider call per corpus query; provider schema admission without `invalid_json_schema` or equivalent rejection; exact observed IDs, latency, and cost; release catalog has at least eight eligible rows | Real OpenAI role + admitted PostgreSQL/pgvector | Manual release only |
| PFI-001, PFI-008 | Unit/property/Lean verifier/golden | Every added symbol, arity, index, typed binding, alpha-equivalence, and wrong-sort rejection; deterministic manifest/evidence-bundle JCS/provenance-label/path/hash/complete-delta seed binding; canonical no-LF OpenMath-to-Lean target and exact wrapper/declaration/toolchain binding; prohibited-source/raw-content rejection plus external-manual-review procedure; manifest-bound Lean success/failure; byte-exact six-governed-query regression; immutable-generation migration/rollback; bilingual continuity queries and semantic hard negatives | Independent original cards + recorded Lean-verifier result + PostgreSQL/pgvector | PR deterministic / main recorded verifier and DB |

## Toolchain and Delivery

- Validator, canonicalizer, schema, catalog manifest, and embedding fingerprint versions move
  together through an explicit scan/quarantine/re-embed migration with rollback to one mutually
  compatible set.
- PFI-008 delivery builds the curriculum manifest and typed seed in Agent tooling, verifies every
  row before embedding, and provides the API only the validated signed artifact. The API does not
  inspect source PDFs or obtain a new write route; it atomically admits or rejects the generation.
- Before two-surface status-only promotion, preserve the sole key
  `cross-repo:proof-flow-index` and exclusive parent `schema:proof-flow-index` surface, require
  exact `spec-ownership: PASS`, and change only requirements frontmatter `status: draft` to
  `status: approved` plus the owning `specs/README.md` row Status cell `draft` to `approved`.
  The exact inverse must reproduce the reviewed candidate requirements and index hashes; the
  status-neutral row description and every requirements-body/design/tasks byte remain unchanged.
  Tasks 12–20, Task 22a, Task 35, Task 36, and Task 37 remain historical markers for superseded
  revisions. Completed Task 38 recorded fresh review, exact two-surface promotion, and a
  promoted-byte review by a reviewer other than both the convergence reviewer and promotion
  approver; its result is the sole predecessor of the synthetic C14N bootstrap lane.
- PFI-008 implementation delivery order is Task 38 valid-XML C14N transport restoration
  convergence/promotion/post-review, the separate resynchronized Agent C14N-only child import,
  Task 24c's synthetic-only canonicalizer,
  and CDS Task 14 companion reapproval. Only then may Task 24a synchronize the repository-owned
  Agent/API/Draft-admin PFI children, followed by Tasks 25--29. Task 24b is the separate
  behavior-preserving PAE import and starts only after the independently converged/promoted/
  post-reviewed EXP bundle; it is not a PFI implementation or publication predecessor. PFI has no
  later dependency on PAE.

## Rejected Alternatives

| Alternative | Reason Rejected |
|---|---|
| Alias/exact-text or seed-only shortcut | Breaks semantic retrieval and multilingual correctness. |
| Retrieved completed Lean proof as trusted harness | Violates PFI-003 and independent verification. |
| One untyped vector blob for all evidence | Cannot enforce outcome class, provenance, or deletion. |

## Risks

- High vector similarity can hide semantic mismatch; structural validation and eval are mandatory.
- The current general-purpose validator is broader than this focused profile; sharing it without a
  PFI-specific closed gate could silently admit unlisted nodes, attributes, or oversized data.
- A future graph proposal can silently expand v1 scope; ownership/inventory review must reject any
  graph or private-trace surface until a successor Spec is approved.

## Open Questions

None for the focused v1 slice.
