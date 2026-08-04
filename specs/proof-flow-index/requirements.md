---
status: approved
repositories:
  - cross-repo
  - pals-agent
  - pals-api
  - pals-draft-admin
---

# Requirements: Proof Flow Index

## C14N v4 Release-Tooling Alignment Restoration

- Change ID: `SPEC-CHG-2026-08-05-PFI-C14N-V4-RELEASE-TOOLING-ALIGNMENT`.
- Classification: behavior-preserving `RESTORATION` of the existing PFI-001/PFI-008 valid-XML C14N
  v4 contract.
- Authority: the user-directed implementation of the 110-card continuity collection exposed that
  the seed builder, worker-image verifier, CLI seed constructor, and private candidate/runtime
  fingerprint checks still identify their canonicalization as C14N v3 after the parent contract
  moved to v4.
- Current: those release-tooling paths can emit or accept a v3 fingerprint/provenance value while
  their OpenMath inputs are validated and canonicalized by the v4 contract. The resulting seed or
  runtime compatibility metadata is internally inconsistent and cannot be used as release evidence.
- Expected: every PFI seed-build, OCI provenance/image verification, CLI seed construction, and
  private candidate/runtime compatibility path identifies the canonicalizer exactly as
  `openmath-cdbase-alpha-c14n-v4`; v3 fingerprints reject before embedding, image construction,
  candidate selection, or generation admission. The legacy non-PFI Draft catalog is outside this
  restoration.
- Unchanged: canonical OpenMath bytes, the closed typed grammar, content, Lean receipts, source
  review, signing, API-only atomic publication, pgvector ownership, active-generation state, and
  user-visible retrieval results are unchanged. This restoration creates no seed signature, API
  request, database write, active generation, or release claim.
- Compatibility, security, data, migration, rollout, rollback, recovery, observability, cost, and
  documentation: v3 PFI fingerprints are incompatible and require the existing scan/quarantine/
  re-embed migration before an otherwise eligible immutable generation can be admitted; no version
  alias or silent conversion is permitted. The release tooling records only the version value
  already bound into its fingerprint and provenance. Failure leaves the prior generation unchanged.

## Detached-Validation Full-Card Fidelity Restoration

- Change ID: `SPEC-CHG-2026-08-05-PFI009-FULL-CARD-FIDELITY`.
- Classification: behavior-preserving `RESTORATION` of PFI-009's existing exact-row local fixture
  contract.
- Current: the detached fixture's schema and source hash retain only a subset of a catalog card,
  despite PFI-009 requiring every current card to be loaded exactly once. Retrieval prompts, Lean
  target, coverage, and novelty key can therefore drift without fixture detection.
- Expected: the detached fixture stores and compares every catalog card field—typed OpenMath,
  bilingual/hard-negative queries and expected outcomes, Lean target, proof strategy, Sketch,
  coverage, novelty key, and canonical statement—plus its deterministic test-vector metadata. Its
  source hash binds that complete card object.
- Unchanged: PFI-009 remains an isolated, networkless, tmpfs-only deterministic-vector plumbing
  test; it neither verifies Lean nor provides source review, a signed seed, semantic retrieval,
  an API/database write, generation, or release evidence.
- Compatibility, security, data, migration, rollout, rollback, recovery, observability, cost, and
  documentation: the fixture has no durable catalog data or public interface. A stale partial-row
  fixture rejects before load; teardown remains project-scoped and independent of input drift.

## Continuous-On Typed-Profile Recognition Restoration

- Change ID: `SPEC-CHG-2026-08-05-PFI-CONTINUOUS-ON-PROFILE-RECOGNITION`.
- Classification: behavior-preserving `RESTORATION` of PFI-008's existing continuity-on contract.
- Current: `pals1:continuous_on` is already an admitted PFI-008 predicate and the catalog contains
  its required global-continuity rows, but the focused continuity-v1 construct-presence guard omits
  that predicate. Consequently the focused canonicalizer rejects an otherwise valid explicit
  `continuous_on(R, lambda(...))` proposition before its typed profile can be used to generate a
  card.
- Expected: the construct-presence guard recognizes `continuous_on` together with the existing
  limit, sequence, point-continuity, and closure vocabulary. It continues to require the unchanged
  closed typed profile, exact v4 canonical bytes, and all existing sort/arity/binder checks; it
  admits no new symbol, theorem form, data source, seed, receipt, database write, or release.
- Unchanged: PFI-001--PFI-010, the four-sort vocabulary, source-review boundary, Lean/seed/API
  gates, retrieval behavior, status, and every external interface.

## Continuity Volume-Floor Admission

- Change ID: `SPEC-CHG-2026-08-04-PFI-CONTINUITY-ONE-HUNDRED-FLOOR`.
- Classification: `ADDED` PFI-010 release-admission floor; PFI-008 coverage semantics are unchanged.
- Authority: the user's explicit instruction that continuity/epsilon-delta data, Drafts, and
  formally verified proofs must each exceed one hundred rather than leaving the current 37-card
  source candidate and local database counts as a stopping point.
- Current: the approved source candidate has 37 cards and no formal Lean-receipt collection, signed
  seed, active PFI generation, or PFI-owned database publication. Read-only local observation of
  `pals-local-postgres-1` found 40 Draft rows, 16 proof jobs (7 verified), and 4 verification
  candidates (2 verified); these are not a PFI-008 generation and do not satisfy release admission.
- Expected: a continuity-v1 release is admissible only when its catalog, successful Lean-receipt
  collection, signed seed delta, and API-published active Draft generation each contain at least
  100 unique IDs and have exactly the same derived ID set. Every additional row remains original,
  typed-profile-valid, reviewed, evaluated, and receipt-bound; 100 is a minimum admission floor,
  not a replacement for semantic coverage or the 4,096-row resource maximum.
- Unchanged: no direct pgvector write, partial seed, unverified proof, raw-model/Tao-derived
  content, public/admin curation path, or count-only release is permitted. PFI-009 remains an
  ephemeral local fixture and cannot establish a receipt, active generation, or floor satisfaction.
- Compatibility, security, data, rollout, rollback, recovery, observability, cost, and
  documentation: an existing active generation below 100 is incompatible with this new
  continuity-v1 admission floor and remains untouched; no migration or append occurs. Admission
  rejects 0--99 rows before embedding/database publication, records content-free aggregate counts
  only, and rolls back atomically to the preceding compatible generation.

## Valid-XML C14N Transport Restoration

- Change ID: `SPEC-CHG-2026-08-04-PFI-C14N-VALID-XML-TRANSPORT-RESTORATION`.
- Classification: behavior-preserving `RESTORATION` of PFI-001/PFI-008's canonical OpenMath
  validity and identity. PFI-002--PFI-004, PFI-009, the seven-sort/type contract, the fixed
  novelty-object members, original-content/source-review boundaries, Lean receipts, signed-seed
  gate, API-only database authority, and every release boundary are unchanged.
- Authority: independent revalidation established that CPython 3.12.13 ElementTree C14N with
  `rewrite_prefixes=true` emits the literal ` xmlns:n0=""` in this profile. That namespace
  undeclaration is rejected by the same runtime's XML parser, making an otherwise required
  canonical OpenMath field non-XML and preventing source-catalog, Lean, and seed admission.
- Current: the existing C14N v3 text treats that raw ElementTree result as the stored canonical
  byte sequence. The current companion's 37 source rows therefore contain one unparseable
  `xmlns:n0=""` declaration each. Existing validation removes it only as a read workaround,
  which leaves the stored source incompatible with the closed OpenMath contract.
- Expected: `openmath-cdbase-alpha-c14n-v4` has one exact, valid-XML transport-canonical output
  defined in the canonical serialization contract below. It derives the fixed raw C14N
  intermediate, removes exactly its one prescribed empty-prefix declaration, reparses the result,
  and requires exact regeneration.
  Every admitted canonical OpenMath field and every SHA-256 identity derived from it uses only
  this valid transport-canonical UTF-8 byte sequence. The stale 37-row companion, all golden
  fixtures/corpus values, and all derived novelty identities are regenerated mechanically from
  their typed semantics before any curriculum catalog/companion child approval, Lean compile,
  seed, fixture, or DB action.
  The Spec-owned `evaluation-corpus.json` is regenerated as valid v4 input at SHA-256
  `9f3cbf318ae5d6ba3accc635a65bb9df67ccf5f503f2fec6a6c22a6a93613e54`; its former raw-byte
  corpus is retired and has no compatibility or production-catalog status.
- Unchanged: no input other than original independently authored content may enter the curriculum;
  this restoration itself accepts only synthetic/golden XML until the separately reapproved child
  gate. It does not create a card, Lean target/wrapper/receipt, manifest, evidence, embedding,
  signed seed, image, network request, database write, active generation, or release claim.
- Compatibility, security, data, migration, rollout, rollback, recovery, observability, cost, and
  documentation: all `openmath-cdbase-alpha-c14n-v3` raw bytes and fingerprints are rejected as
  noncanonical; no version alias or silent conversion exists. No persisted generation exists to
  migrate. Regeneration is deterministic and source-only; failure retains no derived artifact and
  publication remains blocked. Tests prove parser round-trip, exact
  canonical regeneration, rejection of the raw artifact, novelty preimage identity, and no
  database/network side effect. Documentation labels the catalog candidate until the normal
  full-release gates succeed.
- Completion evidence: the parent v4 contract independently converged with C/H=0, underwent the
  exact two-surface status promotion whose draft inverses were requirements
  `921f9331b86ea06b2e0194c2b43d997af12e80d72c9db109553e2cfc1677f62c` and index
  `dbbe10659f7255c44c8d85c9e969bc0347145d74ef707882b28c65f5f3dac2eb`, and received a
  distinct promoted-byte review with C/H=0. This evidence authorizes only the next synthetic
  PFI-AG-009 bootstrap lane, never catalog/Lean/seed/database/publication work.

## Canonical OpenMath Identity and Bootstrap Restoration

- Change ID: `SPEC-CHG-2026-08-04-PFI-C14N-IDENTITY-BOOTSTRAP-RESTORATION`.
- Classification: behavior-preserving `RESTORATION` of PFI-001/PFI-008 canonical OpenMath identity
  and implementation sequencing. PFI-002--PFI-004, PFI-009, all seed/Lean/review gates, API-only
  database authority, and every release boundary are unchanged.
- Authority: the detected all-card C14N/novelty mismatch and the resulting child-approval versus
  canonicalizer implementation cycle.
- Current: PFI-008 describes a novelty JCS object without fixing its member names, so its SHA-256
  identity is not reproducible. The current task order also makes the child C14N restoration wait
  for the general implementation lane while that lane waits for the restored child to be approved.
- Expected: the novelty preimage and valid transport-canonical C14N v4 byte identity below are
  exact. A narrowly scoped,
  no-catalog-input Agent canonicalizer restoration may be specified, tested, and implemented after
  its own approved child import and this parent re-promotion, before curriculum-child reapproval.
  It accepts only synthetic/golden typed XML test inputs and has no seed, embedding, Lean wrapper,
  manifest, evidence, database, network, image, or runtime-retrieval effect.
- Unchanged: the source companion itself remains a candidate until its child is re-approved; every
  content-family card still needs its C0/theorem-shape, attestation, source-review, Lean receipt,
  complete source-set, signed-seed, API admission, and release checks. No bootstrap action can
  read the companion as an admitted source, create a database write, or claim publication.
- Compatibility, security, data, rollout, rollback, and recovery: stale/noncanonical source and
  novelty identities reject before projection. The bootstrap has no persistent output and is
  removable without changing an active generation; full rollout continues through the existing
  immutable-generation path only.

## PFI Implementation Dependency Decoupling

- Change ID: `SPEC-CHG-2026-08-04-PFI-IMPLEMENTATION-DEPENDENCY-SPLIT`.
- Classification: `MODIFIED` PFI-008 implementation sequencing only; no retrieval, catalog,
  OpenMath, Lean, seed, API, database, PAE, or explanation behavior changes.
- Authority: the user's direction to implement the approved continuity catalog flow without stopping
  on unrelated human approvals, and the absence of a PFI behavior dependency on EXP.
- Current: Task 24 joined the PFI implementation children to a later PAE import and also named
  `pals-product-core`, although CORE owns no PFI implementation surface and its independent
  promotion waits on unrelated product contracts. Either condition wrongly delays Lean compilation,
  signed seed construction, and immutable catalog publication.
- Expected: Task 24a owns only the Agent/API/Draft-admin repository-owned PFI child imports and
  gates Tasks 25--29. Task 24b owns the behavior-preserving PAE import, remains after the separately
  approved/post-reviewed EXP bundle, and cannot delay PFI implementation or publication. PAE still
  cannot import PFI until PFI is approved and post-reviewed. CORE remains an independent
  cross-repository product bundle and is not a PFI implementation predecessor.
- Unchanged: all implementation children independently converge, status-promote, and post-review
  before their code/tests; PAE retains retrieval-versus-verification separation and every stated
  dependency; no implementation starts from this draft amendment.
- Compatibility, security, data, rollout, rollback, and recovery: none; this removes only an
  unrelated precondition from the PFI lane.

## Continuity Content-Family Expansion

- Change ID: `SPEC-CHG-2026-08-04-PFI-CONTINUITY-CONTENT-FAMILIES`.
- Classification: `MODIFIED` PFI-008's fixed-cardinality curriculum admission, coverage-manifest
  schema, and evaluation oracle, and PFI-009's fixed-row local fixture oracle. PFI-001--PFI-004's
  resource limits, the closed `continuity-v1` grammar, independent authorship and external
  source-review, actual Lean verification, signed-worker provenance, API-exclusive atomic
  publication, rollback, and no-direct-write boundary are unchanged.
- Authority: the user's explicit direction to manage the continuity catalog by mathematical
  content and independently authored exercise families rather than by a fixed total, and to
  implement that flow through Lean compilation and immutable-generation publication.
- Current: PFI-008/PFI-009 prescribe exactly 22 rows while the same bundle treats seed count as
  inventory rather than curriculum behavior. The fixed list omits required sequence closure forms
  and forces every later original variant through a cardinality Spec amendment.
- Expected: the approved child catalog carries a canonical `coverage` object on every card and a
  canonical `coverage_profile` at its root. The profile names mandatory semantic signatures; it is
  the coverage authority, not its row count. A release's nonempty pilot ID set `P` is derived from
  that catalog and must equal the unique ID sets in the coverage manifest, evidence bundle, Lean
  receipts, and signed-seed delta. Every profile signature must be covered, every card's coverage
  object must be profile-valid and have a unique `novelty_key`, and every card must have its own
  verified Lean receipt and Japanese, English, and hard-negative evaluation. Additional original
  profile-valid variants are admitted without changing a fixed count. Existing 4,096-row and byte
  limits remain resource limits only.
- Unchanged: a card may not be source-derived, a raw model output, completed Lean source, a direct
  pgvector/database write, a partial seed, a public/admin curation action, or a release claim. One
  failed card, coverage signature, review, receipt, or evaluation blocks the complete candidate and
  leaves the previous immutable generation unchanged.
- Compatibility, security, data, rollout, rollback, and recovery: this replaces only the
  pre-release candidate's cardinality contract. Every changed profile or source catalog creates a
  new complete signed seed and immutable generation; it never appends to or rewrites an active
  generation. PFI-009 reads the same approved catalog only as a tmpfs/no-network plumbing fixture.

## Historical Fixed-Cardinality Expansion

This 22-card change record is historical. Its exact-count, exact-ID-list, and 21/23 mutation
wording is superseded for current behavior by
`SPEC-CHG-2026-08-04-PFI-CONTINUITY-CONTENT-FAMILIES`.

- Change ID: `SPEC-CHG-2026-08-04-PFI-CONTINUITY-CATALOG-EXPANSION`.
- Classification: `MODIFIED` PFI-008's concrete pilot cardinality and complete-delta admission
  oracle, plus PFI-009's detached-fixture cardinality and validation oracles. PFI-008's
  signed-release, independent-authorship, source-review, Lean-verifier, complete-generation, and
  API-owned atomic-publication gates are unchanged.
- Authority: the user's request to expand the actual continuity retrieval catalog rather than merely
  a local pgvector fixture. The PFI-008 curriculum remains within its existing nine objectives and
  closed OpenMath profile; the Agent-owned child defines the exact 22 independently authored cards.
- Current: PFI-009 loads the same child companion only when it contains exactly nine overloaded
  candidate cards. That fixed fixture cardinality prevents the child from replacing those broad
  closure examples with the finer-grained limit, continuity, sequence, and closure cards needed for
  meaningful retrieval coverage.
- Expected: the hash-pinned `continuity-v1` companion, PFI-008 coverage manifest, evidence bundle,
  and signed-seed delta have one identical set of exactly 22 child-defined IDs. The detached
  PFI-009 fixture loads and validates all 22 cards solely as non-semantic local pgvector plumbing.
  The 22-card catalog is still only a candidate until every PFI-008 release gate passes; fixture
  success does not publish, activate, or otherwise make it a retrieval catalog.
- Unchanged: the nine objective tokens, closed typed grammar, canonical OpenMath-to-Lean profile,
  no-Tao/no-close-paraphrase boundary, independent external source-review disposition, required
  Lean receipts, recorded bilingual and hard-negative evaluation, six governed-query preservation,
  signed-worker seed, API-exclusive immutable-generation publication, and rollback behavior remain
  exact. No direct database insert, partial publication, public/admin curation endpoint, provider
  call, or source-derived release input is authorized.
- Compatibility, security, data, rollout, rollback, and recovery: this is a pre-release source
  expansion. The existing nine-card companion is unverified and has no active-generation or public
  compatibility commitment. A changed catalog requires a new child hash pin, independent child
  review, complete 22-card evidence bundle, and all existing release gates; a failed card blocks
  the entire candidate and leaves any prior immutable generation unchanged. PFI-009 remains an
  ephemeral, networkless, tmpfs-only local fixture and cannot supply release evidence.

## Detached Local pgvector Validation

- Change ID: `SPEC-CHG-2026-08-01-PFI-CONTINUITY-LOCAL-PGVECTOR-VALIDATION`.
- Classification: `ADDED` PFI-009. PFI-001--PFI-008, including PFI-008's complete signed-release
  admission and prohibition on direct writes to a PFI catalog generation, are unchanged.
- Authority: the user's request to load the approved `continuity-v1` candidate cards for local
  pgvector validation only. This is not authorization to publish, merge, or repair any active
  catalog.
- Current: PFI-008 has no detached local validation fixture. Its only permitted catalog path is
  complete signed-release admission, which requires manifest-bound independent-authorship,
  prohibited-source-review, and Lean-verifier evidence and is currently gated by the dependent
  child/import work. Therefore a direct insertion into an existing local or deployed PFI database
  would violate PFI-002/PFI-008 and could change an active catalog.
- Expected: a developer-invoked, local-only, detached pgvector fixture loads every card from the
  approved current `continuity-v1` catalog into an isolated ephemeral Compose project. It
  validates only local pgvector DDL, exact-row loading, and nearest-neighbour plumbing with
  deterministic test vectors. It neither creates a PFI generation nor asserts semantic retrieval,
  Lean verification, source-review completion, release readiness, or any theorem proof result.
- Unchanged: PFI-008 publication still requires the complete signed seed/coverage manifest,
  independent-authorship and prohibited-source-review evidence, Lean receipts, complete-generation
  compatibility/evaluation, and API-owned atomic activation. The existing PFI database, active
  pointer, `pfi_catalog_*` relations, application tables, API routes, Agent database capability,
  embeddings, source boundary, and all public/runtime retrieval behaviour are not changed.
- Compatibility, security, data, rollout, rollback, and recovery: this is an additive local
  developer fixture with no production migration, network/provider/LLM call, credential, API,
  event, public surface, or durable catalog data. It may run only from an exact approved catalog
  hash and must fail closed before any load on a missing/changed catalog, non-JCS bytes, an
  unexpected card count, duplicate ID, unavailable local image, or an isolation violation. Its
  database data directory is `tmpfs`; explicit teardown removes the detached project and any
  transient state without touching another Compose project or database. PFI-009 has no separate
  approval path: the complete PFI-001--PFI-009 parent bundle must independently converge, be
  promoted, and receive its required distinct post-promotion review before any child resync,
  fixture implementation, Docker interaction, or local load.

## Sequence-Evaluation Completion

- Change ID: `SPEC-CHG-2026-08-01-PFI-SEQUENCE-EVALUATION`.
- Classification: `MODIFIED` PFI-008 typed OpenMath/Lean profile and its validation, curriculum,
  manifest, and evaluation oracles. PFI-001--PFI-004, the nine-objective curriculum boundary,
  catalog/API ownership, and all non-PFI-008 behavior are unchanged.
- Authority: the user's authorization to resolve routine typed-profile gaps without a separate
  approval, provided the resulting card is mathematically meaningful and remains fully
  canonicalized and Lean-verified.
- Current: `real_sequence` has constructors and a typed binder but no registered elimination form.
  Consequently the required sequential-continuity statement cannot express the indexed value
  `u(n)` and an explicit sequence `n ↦ f(u(n))` without either an invalid `apply(u,n)` sort or an
  unrelated conjunct.
- Expected: within the term body of a `continuity-v1` `sequence_lambda`,
  `pals1:sequence_apply(u,n)` is the sole typed elimination form for a real sequence and a
  natural index, returns a real term, and translates deterministically to Lean application. No
  sequence application is valid outside that scope. The sequential-continuity objective is the
  forward preservation law: if `f` is continuous at `a` and `u` converges to `a`, then both
  `sequence_compose(f,u)` and `sequence_lambda(n ↦ apply(f,sequence_apply(u,n)))` converge to
  `apply(f,a)`.
- Unchanged: `pals1:apply` remains restricted to a real function and real term; direct `OMV`
  application heads remain invalid; no biconditional/`logic1:equivalent`, epsilon-delta surface,
  API/DTO/schema/database behavior, source material, external model input, or new signing
  authority is added. The canonical nine objectives, independent-authorship gate, source-review
  procedure, required nonzero quotient hypotheses, exact Lean wrapper, and atomic publication
  remain unchanged.
- Compatibility, rollout, and recovery: this is an incompatible expansion of the closed
  `continuity-v1` grammar only. Existing pre-PFI-008 retrieval remains unchanged. A seed containing
  `sequence_apply` is rejected until the amended parent and dependent child Specs are independently
  converged, promoted, and post-reviewed; an incompatible build leaves the prior immutable
  generation active and rollback selects only a prior mutually compatible generation.

## Seed Function-Sort Conformance Restoration

- Change ID: `SPEC-CHG-2026-07-27-PFI-SEED-FUNCTION-SORT-CONFORMANCE`.
- Classification: behavior-preserving specification/implementation `RESTORATION`.
- Current: the packaged 40-row source seed contains eight rows with twelve direct `OMV`
  application heads and `compact_image`, whose term-sort `OMV f` occupies function positions in
  `continuous_on` and `set1:map`. All nine rows are already ineligible under the approved
  four-sort grammar, but the source inventory and current validator do not reject the complete
  function-position set consistently.
- Expected at the restoration generation: the validator enforces the approved sort of every function-consuming argument,
  including nested applications; the sole-source seed excludes exactly `continuous_add`,
  `continuous_mul`, `continuous_neg`, `continuous_sub`, `continuous_abs_of_function`,
  `continuous_square_of_function`, `continuous_power_of_function`, `continuous_composition`, and
  `compact_image` instead of inventing replacement semantics. The remaining 31 rows exceed the
  release minimum of eight. Corpus source metadata, generated seed/manifest/provenance, tests, and
  documentation are regenerated from those exact source bytes. A later PFI-008 release may add
  only independently authored, typed-profile-valid curriculum rows through its separate complete
  seed/manifest gate; it does not reinstate any excluded row.
- Unchanged: PFI-002–PFI-004, accepted retrieval semantics, six governed
  query IDs, their eight-row candidate orders and expected selections, reranker metrics, exact seed
  count being non-normative, API/Agent/Draft-admin ownership, and every public/private runtime
  contract. None of the nine excluded IDs is a governed query candidate.
- Historical gate: the restoration revision returned requirements and the root index to `draft` and
  used Tasks 17–20 for its own review/publication. Task 22a governs the pre-22-card PFI-008
  amendment; Task 35 is historical and Task 36 is the current parent
  review/promotion/post-review gate; thereafter all three repository-owned PFI child bundles must
  be requirements-first resynchronized, independently converged, and reapproved before seed,
  validator, corpus, or runtime edits. The PAE consumer import is the independent Task 24b lane and
  remains blocked on EXP; it is not a predecessor to those PFI edits.

## Overview

Define the implementable v1 retrieval contract over the current minimal OpenMath Draft catalog.
Complete Proof Flow graph indexing, private execution-trace retrieval, and general/runtime curation
are deferred to a separate future Spec and do not block this focused slice. The bounded,
first-party static curriculum-seed expansion in PFI-008 is the only exception.

## Typed Continuity and Curriculum-Seed Expansion

- Change ID: `SPEC-CHG-2026-08-01-PFI-TYPED-CONTINUITY-SEED`.
- Rationale and authority: the user authorized a meaningful, copyright-safe coverage expansion of
  the continuity material adjacent to Tao's *Analysis I*, while forbidding ingestion of the book's
  text. The catalog must therefore represent limits, sequence convergence, continuity at a point,
  and closure theorems over function variables, rather than only fixed lambda expressions.
- Classification: `MODIFIED` PFI-001 and PFI-002; `ADDED` PFI-008. PFI-003--PFI-007 remain
  unchanged.
- Current: the four-sort profile admits only global `continuous_on` statements for a concrete
  lambda. The checked-in restoration revision has 31 remaining source rows and expressly forbids a
  replacement row. No approved path admits independently authored curriculum rows, and the profile
  cannot express limits, convergent real sequences, continuity at a point, or closure over a bound
  function variable.
- Expected: the closed profile gains the explicit real-function and real-sequence constructs plus
  typed real-function/real-sequence quantifiers and a sequence abstraction below.
  The named first release is `continuity-v1`; its first-party, release-built static curriculum seed
  may add independently authored rows only after its coverage manifest, Lean-verification evidence,
  OpenMath validation, embedding, signed-worker packaging, migration, and evaluation gates pass.
  Another curriculum version requires a subsequent Spec update. The six stored Draft fields and
  private candidate route do not change.
- Unchanged: direct `OMV` application heads remain invalid; user/runtime/admin ingestion, public
  retrieval, graph/trace indexing, raw prompts/model outputs, completed Lean source, and explanatory
  prose remain outside the Draft catalog. Retrieval remains context rather than verification and
  PFI-003's one-query/one-rerank contract is unchanged.
- Compatibility, migration, rollout, rollback, and recovery: this is a profile-compatible
  *expansion*, not a reinterpretation. A release builds one new signed seed and immutable catalog
  generation; every existing and added row is revalidated under the extended sort profile, and an
  invalid row blocks publication rather than being rewritten. The active pointer switches
  atomically only after the whole generation and its evaluation pass. Rollback may select only a
  mutually compatible prior immutable generation. No direct pgvector insert, partial seed merge,
  or in-place repair is allowed.
- Affected repositories and surfaces: parent PFI owns this contract; `pals-agent` owns the
  validator, seed builder, coverage-manifest gate, Lean-verification gate, embedding, and tests;
  `pals-api` owns immutable-generation publication and catalog/evaluation checks; `pals-draft-admin`
  remains read-only; the PAE consumer Spec must resynchronize its parent import without changing
  retrieval-versus-verification behavior. No public API, event, schema column, user-facing
  explanation, or new cost-bearing provider operation is introduced. Locale, operational
  documentation, content-free metrics, recorded evaluations, rollback, and security tests are
  required by PFI-008.

## Historical Promotion-Surface Precision

- Change ID: `SPEC-CHG-2026-07-27-PFI-PROMOTION-SURFACES`.
- Lifecycle: the Tasks 12–14 cycle completed for its prior revision and was superseded by the
  historical Tasks 17–20 restoration path; Task 22a governs the pre-22-card PFI-008 amendment,
  while the current content-family amendment uses Task 36's convergence/promotion path.
- Current: the root-index description must follow the frontmatter lifecycle exactly, while the promotion
  task does not define the exact status tokens or inverse proof.
- Expected: the root-index description is status-neutral. Promotion changes only requirements
  frontmatter `status: draft` to `status: approved` and the `proof-flow-index` row Status cell
  `draft` to `approved`; the inverse must reproduce the reviewed candidate requirements and index
  hashes exactly. The row description, requirements body, design, tasks, and every other byte remain
  unchanged.
- Historical marker custody: Tasks 12–14 remain literal unchecked history. Their prior completion
  exists only in external reports/projection evidence and supplies no authority for current bytes.
- Unchanged: PFI-001–PFI-004, retired PFI-005–PFI-007, retrieval/provider/cost/evidence behavior,
  ownership, implementation, tests, and runtime evidence.

## Approved Change Record

- Change ID: `SPEC-CHG-2026-07-26-PARENT-GRILL`
- Authority: explicit user delegation to resolve the grilled retrieval decisions autonomously.
- Baseline revision: parent `fa29ad0a3c66499230de4c327936906aa5f19c3d`.
- Classification: scope split and conservative compatibility decision.
- Current: stable Draft retrieval PFI-001–PFI-004 is mixed with unresolved future graph
  PFI-005–PFI-007.
- Expected: this bundle governs only the current six-field internal Draft retrieval contract;
  PFI-005–PFI-007 are retired from this bundle without ID reuse and require a new future Spec.
- Unchanged: similarity is context, never verification; invalid semantics and incompatible
  fingerprints fail closed.
- Compatibility: current scoring defaults and catalog schema are frozen; no public/private trace
  graph API is introduced.

## Canonicalization and Resource-Contract Remediation

- Classification: `MODIFIED` validator/canonicalizer/resource contract and behavior-preserving
  `RESTORATION` of the current structural-feature algorithm.
- Current mismatch: the bundle names a supported symbol table and score weights but does not close
  the XML namespace/node/attribute grammar, `cdbase` resolution, binder/alpha/canonicalization
  algorithm, structural feature-key bytes, resource limits, or known-answer vectors.
- Expected: the exact contracts and limits below govern PFI-001 through PFI-004.
- Unchanged: the six-field Draft schema, seven-field embedding fingerprint,
  `openmath-cdbase-alpha-c14n-v2`, top-five-plus-seeds candidate source, `.40/.60/.35` scoring,
  typed `no_match`, read-only/private boundary, and retired PFI-005–PFI-007 remain unchanged.
- Compatibility and migration: current code accepts some XML above the new closed limits and does
  not reject every extra attribute, oversized candidate union, or oversized manifest. The safer
  limits below prevail. Before rollout, revalidate every packaged and retained row; quarantine any
  incompatible row, then atomically re-embed/rebuild the manifest. No incompatible row is silently
  truncated or reactivated. Rollback restores a mutually compatible validator, canonicalizer,
  embedding fingerprint, catalog, and manifest.

## Numeric, DTO, and Provenance Remediation

- Classification: `MODIFIED` PFI-001 through PFI-004 and their canonicalization, semantic typing,
  numeric, DTO/error, provenance, dependency, and task oracles. Retired PFI-005 through PFI-007 and
  all IDs remain unchanged.
- Authority: explicit user authorization to close the identified material findings with deterministic
  oracles, closed DTOs, immutable provenance, and REP-005 promotion ordering.
- Current mismatch: `rewrite_prefixes=false` permits process-global ElementTree namespace
  registration to change canonical bytes; free-variable function heads and `lambda` lack a decidable
  focused type system; embedding/numeric domains and response/error bytes are incomplete; promotion
  omits the parent behavior-key predecessor.
- Expected: exact CPython/C14N provenance and prefix rewriting, the closed two-sort profile, finite
  vector and binary64 score rules, exact result/error DTOs, and key
  `cross-repo:proof-flow-index` govern PFI-001 through PFI-004.
- Compatibility and migration: `OMV` application heads and `fns1:lambda` are now incompatible and
  quarantined; every retained row is re-canonicalized/re-embedded under the new immutable
  provenance. No row, score, or response is silently converted.
- Unchanged: six-field Draft data, seven-field embedding fingerprint, top-five-plus-seeds source,
  `.40/.60/.35` scoring intent, no-match semantics, privacy/read-only boundary, draft status, and
  retired future scope remain unchanged.

## Historical Focused Typing and Ownership-Surface Remediation

- Classification: `MODIFIED` PFI-001 through PFI-004 semantic-profile, provenance, ownership-gate,
  design, and task oracles; no requirement ID is added, removed, renamed, or reused.
- Current mismatch: four standard OpenMath symbols require function/predicate arguments that the
  focused two-sort profile deliberately cannot represent; the response names an undefined runtime
  provenance digest; promotion promises child overlap rows absent from the registered exclusive
  parent surface.
- Historical expected: before PFI-008, `arith1:sum|product` and `set1:map|suchthat` were excluded
  from the focused MVP; runtime provenance has one exact JCS-plus-LF preimage; REP-005 uses the
  already registered exclusive parent `schema:proof-flow-index` surface. PFI-008 supersedes only
  that symbol exclusion: those four symbols are accepted with their normative function/predicate
  signatures below for generic retrieval, but are not eligible in a `continuity-v1` Lean target.
- Unchanged: the remaining symbol registry, prefix-independent valid transport-canonical C14N v4
  bytes, finite vector/binary64
  score rules, exact DTO shape, sole behavior key, read-only/private boundary, and retired future
  scope remain unchanged.
- Compatibility and migration: any retained row containing a removed function-argument symbol is
  quarantined and re-curated under a future typed profile rather than reinterpreted. Existing
  responses whose runtime digest was not computed from the exact v1 provenance object are
  incompatible and cannot be silently converted.

## Candidate-Tie and Seed-Byte Remediation

- Change ID: `SPEC-CHG-2026-07-26-PFI-TIE-SEED-BYTES`.
- Authority: explicit user authorization to apply the validated candidate-order and seed-byte
  findings.
- Classification: `MODIFIED` PFI-002 through PFI-004 candidate-order, six-field mapping,
  seed-manifest, design, and task oracles; no requirement ID is added, removed, renamed, or reused.
- Current mismatch: equal cosine distances at the fifth-row boundary have no deterministic
  secondary order, and the same human-readable statement is named `matched_prompt` in the packaged
  model but `canonical_statement` in storage/response without a normative mapping or one canonical
  manifest byte form.
- Expected: the vector query orders by exact `(cosine_distance ASC, Draft ID ASC)` before taking
  five; Draft IDs are unique; packaged/model `matched_prompt` maps byte-for-byte to
  storage/response/manifest `canonical_statement`; and the seed manifest hashes exact RFC 8785 JCS
  UTF-8 bytes with no terminal LF.
- Unchanged: the focused symbol/type profile, valid transport-canonical C14N v4, top-five-plus-
  seeds source, scoring weights,
  threshold, runtime provenance, exact DTOs, exclusive parent surface, retired future scope, and
  `draft` status remain unchanged.
- Compatibility and migration: catalogs/manifests produced with distance-only fifth-row selection,
  duplicate IDs, the legacy manifest key `matched_prompt`, or any non-JCS seed bytes are
  incompatible and must be rebuilt atomically; no row or score is silently converted.

## Coordinated Parent-Authority Remediation

- Change ID: `SPEC-CHG-2026-07-26-PFI-PARENT-AUTHORITY`.
- Authority: explicit user delegation and the coordinated decision to preserve the formerly
  approved, now-draft PAE-034 observable/runtime retrieval semantics while relocating their
  cross-repository authority into this parent bundle.
- Classification: `MODIFIED` PFI-001 through PFI-004 OpenMath function profile, candidate source,
  rerank, result/error, dependency, and downstream-work contracts; no requirement ID is added,
  removed, renamed, or reused.
- Current mismatch: the focused PFI contract selects deterministic top-five-plus-seed candidates by
  a fixed final score and `0.35` cutoff, excludes function-valued lambda constructs required by the
  current catalog, and conflicts with the then-approved/current-draft PAE-034 database-only
  `LIMIT 8` plus separate real
  `draft`-role relevance rerank.
- Expected: one PostgreSQL/pgvector cosine query orders by exact distance then Draft ID and uses
  `LIMIT 8`; packaged files may seed the compatible catalog but never join runtime candidates; exact
  structural evidence is input to a separate real `draft`-role LLM that returns an ordered unique
  subset of zero through four IDs; zero selection is typed `no_match`; no deterministic final score,
  cutoff, seed union, or fallback participates.
- Unchanged: canonical OpenMath validation, finite embedding/fingerprint/catalog gates, unique
  six-field Draft records, exact manifest bytes, read-only/private boundary, similarity-is-not-proof,
  retired PFI-005 through PFI-007, REP-005 key, and `draft` status remain unchanged.
- Compatibility, rollout, and rollback: catalogs using the invalid historical v3 bytes remain
  subject to a full scan and
  atomic rebuild, but valid explicit lambda/function rows are not quarantined merely for using the
  restored profile. PAE is already `draft` and remains non-authoritative; after both PFI and the
  separate `proof-explanations-and-clarifications` (EXP) bundle are independently converged and promoted,
  PAE imports both parent contracts without changing preserved
  runtime behavior, independently converges, explicitly re-promotes, and passes post-promotion review
  before implementation. Rollback never mixes retrieval profiles or catalogs.

## Pre-Promotion Reproducibility and Dependency Remediation

- Change ID: `SPEC-CHG-2026-07-26-PFI-PRE-PROMOTION-CLOSURE`.
- Authority: explicit user delegation to apply all validated reproducibility and dependency findings without
  changing PFI-001 through PFI-004 scope or promoting this bundle.
- Classification: `MODIFIED` PFI-001 through PFI-004 resource, retrieval-admission, database-order,
  provenance, reranker, evaluation, repository, and promotion-order contracts; no requirement ID is
  added, removed, renamed, or reused.
- Current mismatch: the manifest has no normative row maximum; Unicode tie order depends on
  database collation; provenance digests lack exact subjects; the reranker prompt/transport and
  aggregate input are open; lower-level free-variable canonicalizer fixtures can be mistaken for
  admitted retrieval; the corpus contains rows that migration must quarantine; release admission
  does not enforce the preserved eight-row PAE minimum; quality tiers and affected repositories are
  inconsistent; and the PFI/PAE post-review order creates a cycle.
- Expected: exact 4,096-row manifest, UTF8/`C` byte order, verifiable source/OCI digest subjects,
  bounded JCS request and fixed Responses-API contract, closed retrieval propositions, only
  profile-valid corpus candidates, release-only eight-row admission, deterministic PR/main plus one
  cost-bearing release-live rerank, API no-public-surface assertion, Dataset N/A disposition, and
  immediate PFI post-promotion review before any PAE import.
- Compatibility, migration, rollout, and rollback: rows whose complete reranker projection exceeds
  16,384 UTF-8 bytes or violates the closed pre-PFI-008 sort profile are incompatible and quarantined
  without truncation. Existing catalog/provenance/request bytes are rebuilt atomically. PFI remains
  `draft`; no production, test, status, ownership-registry, or child-Spec byte is changed by this
  update.
- Unchanged: six-field Draft storage, valid transport-canonical v4 lower-level bytes, exact
  structural evidence,
  DB-only `LIMIT 8`, zero-through-four real rerank, typed `no_match`, no deterministic cutoff or
  seed union, read-only/private boundary, retired PFI-005 through PFI-007, and sole REP-005 key.

## Response, Provenance, Resource, and Population Closure

- Change ID: `SPEC-CHG-2026-07-26-PFI-PRE-PROMOTION-CLOSURE-2`.
- Authority: explicit user delegation to remediate the validated response/provenance findings
  without changing the focused PFI-001 through PFI-004 product scope.
- Classification: `MODIFIED` PFI-002 through PFI-004 response-envelope, provenance-carrier,
  resource-domain, and active-catalog contracts; behavior-preserving `RESTORATION` of PFI-001
  provenance traceability. No requirement ID is added, removed, renamed, or reused.
- Current: a 2xx incomplete/mismatched Responses envelope can be accepted; provenance is assigned
  to an undefined release manifest that conflicts with approved PRX; storage-valid 20,000-code-point
  fields are conflated with retrieval eligibility while selected IDs exceed the bounded response
  feasibility; and `eligible_row_count` is not tied to one active catalog population.
- Expected: accept only one exact completed assistant message from the pinned response model; carry
  canonicalizer expectations in a PFI child OCI-config label inside the already PRX-signed worker
  image and combine them with the signed PRX database resource plus live authenticated PostgreSQL
  observations, without extending the parent manifest; distinguish storage validity from bounded
  retrieval eligibility, constrain eligible IDs to 64 ASCII characters and use a 512-token/512-byte
  selection envelope; and count/query one immutable active catalog generation under one exact
  eligibility predicate.
- Unchanged: canonical XML and six-field Draft data, DB-only `LIMIT 8`, UTF8/`C` order, structural
  evidence, real draft-role rerank, zero-through-four contexts, typed `no_match`, no cutoff/seed
  union/fallback, PAE dependency order, `draft` status, and every retired future requirement.
- Compatibility, rollout, rollback, and recovery: storage-valid rows that fail the separate
  eligibility predicate remain quarantined and never enter the readable generation. Legacy
  provenance, response parsers, IDs outside the eligible grammar, or count/query population drift
  are incompatible. Publication and rollback switch only a fully validated immutable generation.

## API Database Authority and Authenticated Connection Closure

- Change ID: `SPEC-CHG-2026-07-26-PFI-PRE-PROMOTION-CLOSURE-3`.
- Authority: explicit user delegation to resolve the identified authority conflict without weakening
  approved PRX database ownership.
- Classification: `MODIFIED` PFI-002 through PFI-004 repository ownership, catalog migration,
  private candidate-query transport, and database-provenance binding; no requirement ID is added,
  removed, renamed, or reused.
- Current: Agent-owned direct PostgreSQL access conflicts with approved PRX API-exclusive/sole
  database authority, and a copied signed database resource ID is not proof that the live
  connection reached the admitted endpoint.
- Expected: API alone owns catalog persistence, migration, active generation, database validation,
  and the exact one-query candidate port. Agent owns canonicalization, embedding, structural
  evidence, and reranking, and calls one worker-authenticated private API route with a bounded
  content-free vector/fingerprint request. API connection target and TLS/local transport identity
  are derived from and exact-match the admitted PRX Infra database endpoint/name/resource tuple;
  live PostgreSQL observations run only through that connection.
- Unchanged: six-field Draft semantics, signed-worker child provenance, storage/eligibility bounds,
  active-generation predicate, DB ordering/limit, scores, reranker, internal-only/no-public surface,
  errors, PAE sequencing, and `draft` status.
- Compatibility, rollout, rollback, and recovery: direct Agent database credentials, DSNs, clients,
  migrations, or queries are incompatible and removed rather than retained as fallback. API catalog
  publication consumes only seed bytes extracted and digest-validated from the already signed worker
  image. Route or connection ambiguity fails closed without a second query/provider/catalog.

## Catalog Population and OCI Parser Closure

- Change ID: `SPEC-CHG-2026-07-26-PFI-PRE-PROMOTION-CLOSURE-4`.
- Authority: explicit user delegation to choose the simplest safe resolution of the identified
  review without adding a curation surface.
- Classification: `MODIFIED` PFI-002 through PFI-004 catalog-source, snapshot metadata, migration,
  and OCI parser contracts; no requirement ID is added, removed, renamed, or reused.
- Current: the signed packaged seed manifest/count cannot equal an active population that also
  mandates copying additional retained rows; the exact snapshot omits the `seed_count` returned by
  the private port; and OCI manifest parsing is not explicitly duplicate-aware and closed.
- Expected: the signed worker seed is the sole v1 readable catalog source. Publication replaces the
  readable generation only with the exact eligible seed population, records every prior database
  row that is not byte-identical to a seed row as quarantined migration history, and requires exact
  `seed_count == row_count == eligible COUNT(*)`. OCI index, manifest, descriptors, and config are
  duplicate-aware, with a closed manifest/descriptor schema and exact descriptor size/digest checks.
- Unchanged: API alone owns persistence/migration/SQL; Agent has zero database capability;
  runtime/user/admin custom ingestion and curation remain non-goals; the private route,
  canonicalizer, structural evidence,
  reranker, result/error DTOs, release ordering, and `draft` status remain unchanged.
- Compatibility, rollout, rollback, and recovery: no legacy retained row is silently promoted,
  merged, or deleted. API writes an immutable quarantine record before switching the pointer.
  Rollback may select only a previously published immutable signed-seed generation that still passes
  the complete compatibility contract.

## Provider-Schema Compatibility Restoration

- Change ID: `SPEC-CHG-2026-07-26-PFI-STRICT-SCHEMA-COMPATIBILITY`.
- Authority: explicit user delegation to continue decision-free Spec remediation without
  pausing for nonmaterial approval; independently verified against the current official OpenAI
  Structured Outputs guide and pinned model page on 2026-07-26.
- Classification: behavior-preserving provider-compatibility **RESTORATION** of PFI-003 and
  PFI-004. No requirement ID is added, removed, renamed, reused, or repurposed.
- Current: the required `strict:true` provider schema uses string keyword `maxLength` and array
  keyword `uniqueItems`. They are outside the documented Structured Outputs subset for the pinned
  non-fine-tuned model, so the required provider call can fail at schema admission before reranking.
- Expected: the provider schema uses only supported `pattern` and `maxItems` constraints. Existing
  pattern `^[a-z][a-z0-9_]{0,63}$` continues to enforce the complete one-through-64-character ID
  domain. The duplicate-aware application response parser continues to enforce uniqueness,
  candidate membership, order, count, and every response bound after provider output. Deterministic
  tests reject any provider-schema keyword outside the exact allowlist, and the sole release-live
  call must prove schema admission: an `invalid_json_schema` or equivalent pre-generation rejection
  blocks release and cannot be classified as a valid reranker result.
- Unchanged: provider/model/snapshot/API identity; prompt and prompt hash; request subject and all
  non-schema request fields; zero-through-four ordered unique supplied-ID product behavior;
  duplicate/foreign-ID rejection; 512-token/text bounds; one call, deadline, no-retry/no-fallback
  rules; database, catalog, privacy, migration, rollout, rollback, recovery, observability, and
  cost contracts; retired PFI-005 through PFI-007.
- Status and delivery: the provider-compatibility defect invalidated the former approval, so this
  bundle and its owning index row return to `draft`. Reapproval requires a fresh all-zero review,
  requirements-frontmatter plus root-index status-only promotion, and a different all-zero
  post-promotion review. No product, product-test, child-Spec, registry, stage, or commit edit is
  authorized by this restoration.
- Primary evidence:
  `https://developers.openai.com/api/docs/guides/structured-outputs` and
  `https://developers.openai.com/api/docs/models/gpt-5.4-mini`.

## Review-Artifact Retention Restoration

- Current: historical convergence labels and a superseded review invocation's reviewed-file
  hashes, severity counters, verdict, and gate transcript are persisted in this bundle.
- Expected: retain the substantive findings and resulting PFI contract, but keep every
  specification-review invocation ledger and result report-only.
- Unchanged: PFI-001–PFI-004, retired PFI-005–PFI-007, API/Agent/Draft-admin ownership, catalog and
  reranker behavior, migration/rollback, downstream dependency order, implementation/test scope,
  and provider-compatibility restoration.

## Live Usage and Cost Evidence Remediation

- Change ID: `SPEC-CHG-2026-07-27-PFI-USAGE-COST-EVIDENCE`.
- Classification: `MODIFIED` PFI-003 and PFI-004 release-evidence, privacy, retention, and
  reproducibility contracts. No requirement ID is added, removed, renamed, reused, or repurposed.
- Current mismatch: the successful provider-envelope contract forbids using every non-selection
  provider metadata field for cost, while the manual release gate requires recorded token usage
  and cost without defining another token source, pricing authority, arithmetic, rounding,
  evidence schema, or retention policy.
- Expected: the response parser admits only the exact content-free Responses `usage` object below,
  normalizes cached/uncached input and reasoning/non-reasoning output counts, fails closed on every
  missing, unknown, inconsistent, negative, non-integer, or over-bound value, and computes release
  cost from one pinned USD-per-million-token snapshot using arbitrary-precision integer/rational
  arithmetic and exact half-up rounding. Only the closed content-free release-evidence schema is
  retained for the bounded period below.
- Unchanged: request/prompt/output-text bytes, selected Draft IDs and ordering, match/no-match
  semantics, provider/model/snapshot/API identity, database/catalog/migration behavior, no retry or
  fallback, runtime DTOs, product behavior, implementation, product tests, child Specs, lifecycle
  status, ownership registries, staging, commit, rollout, rollback, and recovery.
- Compatibility: a successful response lacking the exact usage object or containing an unknown or
  inconsistent usage member is `reranker_invalid`; a release-live run lacking the exact pricing
  snapshot or evidence record is release-blocking. No historical evidence is reinterpreted.
- Security, privacy, and data: token counts and derived price are content-free operational evidence.
  Raw provider envelopes, request/response text, prompts, headers, credentials, provider IDs other
  than the already pinned model, and user/project/proof identifiers remain prohibited from the
  release-evidence record.
- Open decisions: none.

## Goals

- Preserve language-independent theorem semantics for retrieval.
- Retrieve reusable strategy/Sketch context without treating similarity as proof or a trusted harness.
- Return a typed no-match result without inventing a Draft or verification claim.

## Non-Goals

- Treat retrieved Lean code as verified for a new user statement.
- Use natural-language aliases or completed proof templates as hidden deterministic fallbacks.
- Make the read-only Draft operations UI a write or curation surface.
- Index proof attempts, prompts, model output, Lean artifacts, explanations, or private traces.
- Define a complete Proof Flow graph or public retrieval API.

## Current, Expected, and Unchanged Behavior

### Current

- A six-column Draft catalog stores stable ID, human-readable statement, validated canonical OpenMath, strategy, ordered Sketch steps, and embedding.
- Retrieval combines vector similarity with OpenMath structural similarity and fails closed on embedding-fingerprint mismatch.
- Repository documentation conflicts on a historical seed count; exact count is therefore not a normative requirement.

### Expected

- The approved Spec will distinguish the existing Draft retrieval slice from the future full Proof Flow model and retrieval boundary.

### Unchanged

- Similarity never proves theorem equivalence or successful verification.
- A generated proof requires independent formal-statement binding and Lean verification.

## Functional Requirements

| ID | Candidate Requirement | Priority | Source |
|---|---|---|---|
| PFI-001 | PALS shall represent the retrieval proposition as validated alpha-canonical OpenMath using only the exact XML, resource, canonicalization, and v1 Content Dictionary profiles below. Unknown namespace/dictionary/symbol, extra node/attribute, invalid arity/role/binder, non-proposition root, semantic inconsistency, or exceeded bound fails before embedding. | Must | Current repository evidence; conservative bound closure |
| PFI-002 | A stored Draft record shall contain a unique stable ID, human-readable canonical statement, canonical OpenMath, proof strategy, ordered Sketch steps, and embedding under the exact storage, row, naming, and manifest limits below. A stored record is reusable by retrieval only when it also belongs to the one readable active generation and satisfies the separate exact eligibility predicate and aggregate request bounds below; storage validity alone never implies retrieval eligibility. Lean targets, aliases, completed proof fallbacks, and lifecycle counters shall not be trusted retrieval keys. | Must | Current repository decision; population/resource closure |
| PFI-003 | Internal Agent retrieval shall call the API-owned, worker-authenticated private candidate port below exactly once; API alone shall read one exact active catalog through one bounded database-only `LIMIT 8` cosine query and return the ordered candidate rows. Agent alone shall canonicalize and embed the query, compute deterministic structural evidence, and invoke one separate real PAE `draft`-role relevance rerank that returns an ordered unique subset of zero through four candidate IDs. The final Agent response exposes the selected Draft contexts, canonical query OpenMath, candidate vector/structural evidence, exact-equivalence flags, and compatibility/reranker provenance and is context only. | Must | Approved PAE-034 preserved behavior; approved PRX-004 database authority |
| PFI-004 | Retrieval shall fail closed under the exact fingerprint/manifest/resource/reranker contract below for invalid OpenMath, unsupported symbols, semantic inconsistency, stale/mixed fingerprint, incompatible metadata, seed mismatch, exceeded bounds, migration incompatibility, or reranker failure. A valid query whose strict reranker selects zero IDs returns typed `no_match`; it never selects an alias, exact-text fallback, packaged-seed runtime union, deterministic cutoff, completed Lean proof, or fabricated context. | Must | Approved PAE-034 preserved behavior |
| PFI-005 | **Retired from this focused bundle.** Complete Proof Flow entity/edge/provenance behavior requires a separately generated and approved future Spec. | — | Scope split; ID not reusable |
| PFI-006 | **Retired from this focused bundle.** Future verified/failed/partial/unsupported graph classification requires the successor Spec; v1 Draft retrieval makes no outcome-class claim. | — | Scope split; ID not reusable |
| PFI-007 | **Retired from this focused bundle.** Future role-scoped graph retrieval requires the successor Spec; v1 is an internal Agent Draft boundary only. | — | Scope split; ID not reusable |
| PFI-008 | PALS shall support a closed, typed OpenMath profile for real-function limits, real-sequence convergence, continuity at a point, and stated closure constructions, and shall admit only an approved, nonempty, content-profile-complete set of independently authored `continuity-v1` curriculum rows from one first-party static seed release. Each pilot row requires its canonical coverage object, coverage-manifest entry, independent-authorship attestation, external source-review disposition, and successful Lean-verifier evidence before seed publication. The complete child catalog, coverage manifest, evidence bundle, Lean-receipt collection, and seed delta shall have one identical unique derived ID set, and their coverage/profile hashes shall bind the exact source content. None becomes a seventh Draft field or a retrieval claim that its context proves a new theorem. | Must | User-authorized continuity curriculum expansion; PFI-001--PFI-004 boundaries |
| PFI-009 | PALS shall provide a developer-invoked, local-only pgvector validation fixture that loads every card in the approved current `continuity-v1` catalog into a separately named, ephemeral `pgvector/pgvector:pg16` Compose project and a fixture-only `continuity_validation_cards` relation. It shall use deterministic non-semantic `vector(3)` test vectors solely to validate DDL, exact source-set insertion, derived cardinality, and self nearest-neighbour behaviour, and shall neither contact a network/provider/LLM nor read/write a PFI catalog generation, active pointer, `pfi_catalog_*` relation, application table, or public/runtime interface. | Must | User-authorized local validation; PFI-002/PFI-008 release isolation |
| PFI-010 | A `continuity-v1` immutable generation shall be admitted only when the approved catalog, successful Lean-receipt collection, signed seed delta, and API-published active Draft generation each contain at least 100 unique IDs and have one identical derived ID set. The floor is checked after all PFI-008 typed/profile/originality/review/evaluation gates and before embedding or database publication; 0--99 rows, any duplicate, and any set mismatch reject atomically. | Must | User-authorized continuity volume floor; PFI-008 complete-source-set boundary |

### PFI-008 Content Coverage Contract

The `continuity-v1` child catalog root has `schema_version` exactly
`pals.continuity-draft-catalog.v2` and is exact no-LF JCS with only
`cards`, `coverage_profile`, and `schema_version`. `cards` is nonempty, has unique valid UTF-8
Draft IDs, and is sorted by each `draft_id`'s UTF-8 byte sequence in ascending order. Its
`coverage_profile` is exact no-LF JCS with
`schema_version` exactly `pals.continuity-coverage-profile.v1` and only
`required_signatures` and `schema_version`; signatures are sorted by their own JCS UTF-8 bytes,
unique, and nonempty. A signature is an object with exactly
`context`, `operators`, `prerequisites`, `proof_schema`, `representation`, `stratum`, and `topic`.
`operators` and `prerequisites` are sorted by valid UTF-8 byte sequence in ascending order and are
unique string arrays. A card has the existing exact raw
fields plus one exact `coverage` object with those seven signature fields and a nonempty
`novelty_key`; its signature is `coverage` without `novelty_key`.

`topic` is one of the nine existing `coverage_objective` tokens. `context` is exactly one of
`limit_at`, `sequence`, `continuity_at`, or `continuity_on`. `stratum` is exactly one of
`core_law`, `bridge`, or `instance`. `representation` is exactly one of
`variable_closure`, `concrete_lambda`, or `sequence_lambda`. `proof_schema` is exactly one of
`basic`, `transport`, `closure`, or `concrete_instance`. `operators` contains only the registered
`continuity-v1` function/sequence constructors or `constant_function` and `identity_function`.
`prerequisites` contains only `continuous_at_subject`, `continuous_on_real_subject`,
`has_limit_at_subject`, `converges_to_subject`, `continuous_at_left`, `continuous_at_right`,
`continuous_on_real_left`, `continuous_on_real_right`, `has_limit_at_left`, `has_limit_at_right`,
`converges_to_left`, `converges_to_right`, `inner_continuous_at`,
`outer_continuous_at_inner_value`, `inner_has_limit_at`, `inner_converges_to`,
`outer_continuous_at_inner_limit`, `continuous_at_numerator`,
`continuous_at_denominator`, `continuous_on_real_numerator`,
`continuous_on_real_denominator`, `has_limit_at_numerator`, `has_limit_at_denominator`,
`converges_to_numerator`, `converges_to_denominator`, `nonzero_denominator_at`,
`nonzero_denominator_limit`, `nonzero_denominator_everywhere`, or
`nonzero_denominator_sequence_limit`.
The source card's `coverage_objective` equals `coverage.topic`. Its `novelty_key` is exactly the
lowercase `sha256:` digest of the no-LF JCS object with exactly two members:
`{"coverage_signature":<the exact seven-field coverage object>,"openmath_xml_sha256":"sha256:" +
<the lowercase SHA-256 of the exact valid transport-canonical OpenMath C14N v4 UTF-8 bytes>}`. Therefore an
alpha-equivalent or identical OpenMath expression cannot masquerade as a distinct variant merely
by changing card text or tags.

A card realizes coverage only when its canonical OpenMath root has the exact closed theorem-binder
prefix and checked residual form specified by the Core Theorem-Shape Library below. After removing
only that prefix, `basic` has the exact context predicate/convergence proposition as its residual
root; `transport` and `closure` have one outer `logic1:implies`, with every listed role-specific
prerequisite in its antecedent and the context predicate/convergence proposition containing every
listed operator in its consequent; and `concrete_instance` has that same residual root shape with
at least one concrete function or sequence constructor/lambda in the consequent. `limit_at`,
`sequence`, `continuity_at`, and `continuity_on` mean respectively a consequent `has_limit_at`,
`converges_to`, `continuous_at`, or `continuous_on(setname1:R,...)` proposition. A listed
`continuity_at`, `continuity_on_real`, `has_limit_at`, or `converges_to` prerequisite is the
matching antecedent predicate on the role-named function or sequence; the four role-named nonzero
tags are the exact quotient hypotheses specified below. For every `left/right`,
`numerator/denominator`, and `inner/outer` pair, the two subjects are distinct enclosing typed
binders and occupy their stated direct operand positions in the consequent; a repeated subject,
swapped position, disconnected application, free variable, extra binder, or vacuous binder rejects,
except for the exact unused natural-index binder of the constant-sequence Core shape below.
An operator occurs only when it is the direct or nested real-function/real-sequence expression
governed by that consequent, never merely an unrelated antecedent occurrence. Any other
metadata-to-AST pairing rejects before compilation or embedding.

Let `C0` be the mechanically expanded required-signature set below. Every signature has
`stratum=core_law` and `representation=variable_closure` unless its row says otherwise. The only
function-to-sequence operator map used by this expansion is exactly
`{function_add:sequence_add,function_sub:sequence_sub,function_mul:sequence_mul}`; each binary
sequence signature substitutes the mapped sequence operator for its function operator. The checked
release tooling serializes the resulting unique sorted signature array as the exact no-LF JCS
`pals.continuity-coverage-profile.v1` golden fixture; a map change, duplicate, omission, or different
array order rejects.

| Family | `topic`, `context`, `operators`, `prerequisites`, `proof_schema`, `representation` |
|---|---|
| basic limits/sequences | `limit_at,limit_at,[constant_function],[],basic,concrete_lambda`; `limit_at,limit_at,[identity_function],[],basic,concrete_lambda`; `sequence_convergence,sequence,[],[],basic,sequence_lambda` |
| basic point/global continuity | `continuity_at,continuity_at,[constant_function],[],basic,concrete_lambda`; `continuity_at,continuity_at,[identity_function],[],basic,concrete_lambda`; `continuity_on,continuity_on,[constant_function],[],basic,concrete_lambda`; `continuity_on,continuity_on,[identity_function],[],basic,concrete_lambda` |
| bridges | `limit_at,limit_at,[],[continuous_at_subject],transport,variable_closure`; `continuity_at,continuity_at,[],[continuous_on_real_subject],transport,variable_closure`; `sequential_continuity,sequence,[sequence_compose],[continuous_at_subject,converges_to_subject],transport,sequence_lambda` |
| add/sub | for each `o` in `function_add,function_sub`: `closure_add_sub_neg,continuity_at,[o],[continuous_at_left,continuous_at_right],closure,variable_closure`; `closure_add_sub_neg,continuity_on,[o],[continuous_on_real_left,continuous_on_real_right],closure,variable_closure`; `closure_add_sub_neg,limit_at,[o],[has_limit_at_left,has_limit_at_right],closure,variable_closure`. For matching `sequence_add,sequence_sub`: `closure_add_sub_neg,sequence,[o],[converges_to_left,converges_to_right],closure,variable_closure`. |
| neg | `closure_add_sub_neg,continuity_at,[function_neg],[continuous_at_subject],closure,variable_closure`; `closure_add_sub_neg,continuity_on,[function_neg],[continuous_on_real_subject],closure,variable_closure`; `closure_add_sub_neg,limit_at,[function_neg],[has_limit_at_subject],closure,variable_closure`; `closure_add_sub_neg,sequence,[sequence_neg],[converges_to_subject],closure,variable_closure`. |
| mul | the add/sub matrix with `topic=closure_mul_scale`, `function_mul`, and `sequence_mul`. |
| scale | `closure_mul_scale,continuity_at,[function_scale],[continuous_at_subject],closure,variable_closure`; `closure_mul_scale,continuity_on,[function_scale],[continuous_on_real_subject],closure,variable_closure`; `closure_mul_scale,limit_at,[function_scale],[has_limit_at_subject],closure,variable_closure`; `closure_mul_scale,sequence,[sequence_scale],[converges_to_subject],closure,variable_closure`. |
| composition | `closure_compose,continuity_at,[function_compose],[inner_continuous_at,outer_continuous_at_inner_value],closure,variable_closure`; `closure_compose,limit_at,[function_compose],[inner_has_limit_at,outer_continuous_at_inner_limit],closure,variable_closure`; `closure_compose,sequence,[sequence_compose],[inner_converges_to,outer_continuous_at_inner_limit],closure,variable_closure`. |
| division | `closure_div_nonzero,continuity_at,[function_div],[continuous_at_denominator,continuous_at_numerator,nonzero_denominator_at],closure,variable_closure`; `closure_div_nonzero,continuity_on,[function_div],[continuous_on_real_denominator,continuous_on_real_numerator,nonzero_denominator_everywhere],closure,variable_closure`; `closure_div_nonzero,limit_at,[function_div],[has_limit_at_denominator,has_limit_at_numerator,nonzero_denominator_limit],closure,variable_closure`; `closure_div_nonzero,sequence,[sequence_div],[converges_to_denominator,converges_to_numerator,nonzero_denominator_sequence_limit],closure,variable_closure`. |

`C0` also includes every signature in the table with `stratum=bridge` for its bridge row and
`stratum=core_law` otherwise. The profile's `required_signatures` must contain `C0`; additional
signatures are permitted only when they use these exact field domains and are content-distinct
concrete-lambda or sequence-lambda variants. A candidate is complete when
every required signature has at least one card, every card's signature belongs to the profile, and
every `novelty_key` and canonical OpenMath byte string is unique. These are semantic coverage rules,
not a total-card requirement. When the existing 4,096-row resource cap would be exceeded, the
complete candidate rejects before embedding or a database transaction; a later curriculum version
requires a new Spec rather than truncating or splitting one release silently.

### PFI-008 Core Theorem-Shape Library

For `C0` only, coverage acceptance is restricted to the following canonical OpenMath theorem
shapes; this library resolves every role-specific prerequisite to the exact consequent binder,
point, and limit. Write `CA(f,a)`, `CO(f)`, `HL(f,a,L)`, and `CS(u,L)` for respectively
`continuous_at(f,a)`, `continuous_on(R,f)`, `has_limit_at(f,a,L)`, and
`converges_to(u,L)`. All displayed variables are distinct bound variables of their stated
real-function, real-sequence, real-term, or natural-index sort. A card has exactly one outer
closed theorem prefix: first one `pals1:forall_real_function` binding the displayed real-function
variables in their first left-to-right appearance, then one `pals1:forall_real_sequence` binding
the displayed real-sequence variables in that order, then one `quant1:forall` binding every
displayed free real-term variable in that order. An empty sort group omits its binder; a
`pals1:sequence_lambda` alone binds its displayed natural-index variable at the expression site.
No other quantifier/binder appears in the theorem prefix or residual proposition, and every outer
theorem-prefix variable occurs in the displayed shape. The sole permitted unused binder is the
natural-index `n` in the exact constant-sequence shape `CS(sequence_lambda(n,c),c)`; every other
unused binder rejects. The sole residual quantifier exception is the inner `quant1:forall` that
binds exactly one real term `x` and is scoped only to `apply(g,x) ≠ 0` in the global-continuity
division shape below. The antecedent is exactly the displayed conjunction in canonical
left-associative `logic1:and` form: an unlisted proposition, duplicate proposition, changed
point/limit, or added hypothesis rejects.

- The basic shapes are `HL(constant(c),a,c)`, `HL(identity,a,a)`,
  `CS(sequence_lambda(n,c),c)`, `CA(constant(c),a)`, `CA(identity,a)`, `CO(constant(c))`, and
  `CO(identity)`.
- The bridge shapes are `CA(f,a) → HL(f,a,apply(f,a))`,
  `CO(f) → CA(f,a)`, and
  `CA(f,a) ∧ CS(u,a) → CS(sequence_compose(f,u),apply(f,a)) ∧
  CS(sequence_lambda(n,apply(f,sequence_apply(u,n))),apply(f,a))`. The two sequential conclusions
  are the sole allowed multi-proposition consequent in `C0`.
- For binary `op` in `function_add`, `function_sub`, or `function_mul`, the three function shapes
  are `CA(f,a) ∧ CA(g,a) → CA(op(f,g),a)`, `CO(f) ∧ CO(g) → CO(op(f,g))`, and
  `HL(f,a,F) ∧ HL(g,a,G) → HL(op(f,g),a,op_result(F,G))`; its matching sequence shape is
  `CS(u,U) ∧ CS(v,V) → CS(sequence_op(u,v),op_result(U,V))`. `op_result` is exactly the matching
  `arith1:plus`, `minus`, or `times` term, and `sequence_op` is exactly the matching sequence
  constructor.
- For unary negation the shapes are `CA(f,a) → CA(function_neg(f),a)`,
  `CO(f) → CO(function_neg(f))`, `HL(f,a,F) → HL(function_neg(f),a,unary_minus(F))`, and
  `CS(u,U) → CS(sequence_neg(u),unary_minus(U))`. For scalar `c`, scale uses the same four shapes
  with `function_scale(c,f)` or `sequence_scale(c,u)` and result `times(c,F)` or `times(c,U)`.
- Composition shapes bind the connection point exactly: `CA(g,a) ∧ CA(f,apply(g,a)) →
  CA(function_compose(f,g),a)`; `HL(g,a,L) ∧ CA(f,L) →
  HL(function_compose(f,g),a,apply(f,L))`; and `CS(u,L) ∧ CA(f,L) →
  CS(sequence_compose(f,u),apply(f,L))`.
- Division shapes bind the denominator role exactly: `CA(f,a) ∧ CA(g,a) ∧ apply(g,a) ≠ 0 →
  CA(function_div(f,g),a)`; `CO(f) ∧ CO(g) ∧ ∀x, apply(g,x) ≠ 0 → CO(function_div(f,g))`;
  `HL(f,a,F) ∧ HL(g,a,G) ∧ G ≠ 0 → HL(function_div(f,g),a,divide(F,G))`; and
  `CS(u,U) ∧ CS(v,V) ∧ V ≠ 0 → CS(sequence_div(u,v),divide(U,V))`.
  In the global shape, `∀x, apply(g,x) ≠ 0` is exactly the sole residual-quantifier exception
  above: its `x` is a one-variable `quant1:forall` term binder, has no other scope, and cannot be
  replaced by an outer-prefix variable or any other predicate.

The role tags in `C0` select exactly the corresponding antecedent atoms in this library:
`left/right`, `numerator/denominator`, and `inner/outer` are not labels alone. Their bound variables,
points, limit values, operator operand order, and result term must be byte-for-byte the canonical
OpenMath tree produced by these shapes after alpha canonicalization. `core_law` cards may not use a
concrete lambda to discharge a generic role or add an unrelated condition. `bridge` cards use only
the displayed bridge shapes. A `concrete_instance` or `sequence_lambda` variant must first validate
against one applicable core shape after substituting its declared concrete construction; it may not
erase a required role, hypothesis, or nonzero condition.

## Supported OpenMath Profile

The following registry is normative; implementation source is evidence, not authority. `n` means
the applicable XML/node/resource limit rather than infinity. A predicate returns a proposition. A
connective additionally requires proposition arguments. Every standard symbol resolves to exact
`cdbase` `http://www.openmath.org/cd`; every `pals1` symbol resolves to exact
`urn:pals:openmath:cd:v1`.

| cdbase / CD | Symbols | Role | Arity |
|---|---|---|---|
| `http://www.openmath.org/cd` / `relation1` | `approx|eq|geq|gt|leq|lt|neq` | predicate application | 2 |
| `http://www.openmath.org/cd` / `logic1` | `and|nand|nor|or|xnor|xor` | connective application | 2..n |
| `http://www.openmath.org/cd` / `logic1` | `equivalent|implies` | connective application | 2 |
| `http://www.openmath.org/cd` / `logic1` | `not` | connective application | 1 |
| `http://www.openmath.org/cd` / `logic1` | `false|true` | proposition constant | 0 |
| `http://www.openmath.org/cd` / `arith1` | `gcd|lcm|plus|times` | term application | 2..n |
| `http://www.openmath.org/cd` / `arith1` | `abs|unary_minus` | term application | 1 |
| `http://www.openmath.org/cd` / `arith1` | `divide|minus|power|root` | term application | 2 term arguments |
| `http://www.openmath.org/cd` / `arith1` | `sum|product` | function-consuming term application | term collection, then term function |
| `http://www.openmath.org/cd` / `set1` | `in|notin|notprsubset|notsubset|prsubset|subset` | predicate application | 2 |
| `http://www.openmath.org/cd` / `set1` | `cartesian_product|intersect|union` | term application | 2..n |
| `http://www.openmath.org/cd` / `set1` | `setdiff` | term application | 2 term arguments |
| `http://www.openmath.org/cd` / `set1` | `map` | function-consuming term application | term function, then term collection |
| `http://www.openmath.org/cd` / `set1` | `suchthat` | predicate-consuming term application | term collection, then predicate function |
| `http://www.openmath.org/cd` / `set1` | `set` | term application | 1..n |
| `http://www.openmath.org/cd` / `set1` | `size` | term application | 1 |
| `http://www.openmath.org/cd` / `set1` | `emptyset` | term constant | 0 |
| `http://www.openmath.org/cd` / `setname1` | `C|N|P|Q|R|Z` | term constant | 0 |
| `http://www.openmath.org/cd` / `alg1` | `one|zero` | term constant | 0 |
| `http://www.openmath.org/cd` / `quant1` | `exists|forall` | proposition binder | 1..256 bound variables + proposition body |
| `http://www.openmath.org/cd` / `fns1` | `lambda` | function binder | 1..256 bound variables + term or proposition body; exactly 1 with term body in a `continuity-v1` row |
| `urn:pals:openmath:cd:v1` / `pals1` | `compact|finite_dimensional|linear_map` | predicate application | 1 term argument |
| `urn:pals:openmath:cd:v1` / `pals1` | `continuous_on` | predicate application | term collection, then real function |
| `urn:pals:openmath:cd:v1` / `pals1` | `dimension|domain|nullity|rank` | term application | 1 |
| `urn:pals:openmath:cd:v1` / `pals1` | `continuous_at` | predicate application | real function, then term |
| `urn:pals:openmath:cd:v1` / `pals1` | `has_limit_at` | predicate application | real function, then term, then term |
| `urn:pals:openmath:cd:v1` / `pals1` | `converges_to` | predicate application | real sequence, then term |
| `urn:pals:openmath:cd:v1` / `pals1` | `apply` | term application | real function, then term |
| `urn:pals:openmath:cd:v1` / `pals1` | `sequence_apply` | term application | real sequence, then natural index |
| `urn:pals:openmath:cd:v1` / `pals1` | `constant_function` | real-function application | 1 term argument |
| `urn:pals:openmath:cd:v1` / `pals1` | `identity_function` | real-function constant | 0 |
| `urn:pals:openmath:cd:v1` / `pals1` | `function_add|function_sub|function_mul|function_div|function_compose` | real-function application | 2 real-function arguments |
| `urn:pals:openmath:cd:v1` / `pals1` | `function_neg` | real-function application | 1 real-function argument |
| `urn:pals:openmath:cd:v1` / `pals1` | `function_scale` | real-function application | term, then real function |
| `urn:pals:openmath:cd:v1` / `pals1` | `sequence_add|sequence_sub|sequence_mul|sequence_div` | real-sequence application | 2 real-sequence arguments |
| `urn:pals:openmath:cd:v1` / `pals1` | `sequence_neg` | real-sequence application | 1 real-sequence argument |
| `urn:pals:openmath:cd:v1` / `pals1` | `sequence_scale` | real-sequence application | term, then real sequence |
| `urn:pals:openmath:cd:v1` / `pals1` | `sequence_compose` | real-sequence application | real function, then real sequence |
| `urn:pals:openmath:cd:v1` / `pals1` | `forall_real_function|exists_real_function` | typed proposition binder | 1..256 real-function variables + proposition body |
| `urn:pals:openmath:cd:v1` / `pals1` | `forall_real_sequence|exists_real_sequence` | typed proposition binder | 1..256 real-sequence variables + proposition body |
| `urn:pals:openmath:cd:v1` / `pals1` | `sequence_lambda` | typed sequence binder | 1..256 natural-index variables + term body; exactly 1 in a `continuity-v1` row |
| `urn:pals:openmath:cd:v1` / `pals1` | `index_zero` | natural-index constant | 0 |
| `urn:pals:openmath:cd:v1` / `pals1` | `index_succ` | natural-index application | 1 natural-index argument |
| `urn:pals:openmath:cd:v1` / `pals1` | `index_to_real` | term application | 1 natural-index argument |

Adding a dictionary, symbol, role, arity, or proposition rule is compatibility-changing and requires
a Spec update plus canonicalization/retrieval revalidation.

### Typed continuity sort contract

The retrieval profile extends its existing `term|proposition|term_function|predicate_function`
inference with `real_function`, `real_sequence`, and `natural_index`. `quant1:forall|exists` binds only term
variables. `pals1:forall_real_function|exists_real_function` binds only real-function variables;
`pals1:forall_real_sequence|exists_real_sequence` binds only real-sequence variables.
`fns1:lambda` with a term body is a real function only in a registered real-function position;
`pals1:sequence_lambda` binds natural-index variables and with a term body is a real sequence. The
generic registry cardinalities remain available outside the pilot. In a `continuity-v1` row,
`fns1:lambda` and `sequence_lambda` each declare exactly one variable; a typed or generic
quantifier may still declare 1..256 same-sort variables and its Lean translation nests them in
their declared left-to-right order. Thus neither pilot function nor pilot sequence translation
depends on implicit currying or an unspecified multi-argument lambda.
only natural-index values are `index_zero`, nesting `index_succ`, and a sequence-lambda-bound
variable; `index_to_real` is its sole conversion to a term. A variable's declared binder sort and
every use must agree; an ordinary term variable cannot become a function, sequence, or natural
index merely from position. Unconstrained, conflicting, or free variables are invalid.
`real_sequence` is a sequence indexed by natural numbers with real values; `real_function` is a
real-to-real function.
`pals1:apply`, not an `OMV` application head, is the only registered application form for a
variable or constructed real function. Within the term body of a `continuity-v1`
`sequence_lambda`, `pals1:sequence_apply` is the only registered application form for a variable
or constructed real sequence and a natural index; it returns a real term. It is invalid outside
that scope. The function and sequence construction symbols have exactly the sorts and arities in
the table. A real function may not occupy a sequence position or vice versa. The existing term and
proposition rules, binder scope, alpha canonicalization, resource limits, and closed retrieval gate
remain in force.

## Exact XML and Resource Contract

- The input is valid UTF-8 and at most 65,536 UTF-8 bytes. DTD and entity declarations are
  prohibited before parsing.
- Every element is in exact namespace `http://www.openmath.org/OpenMath`; no foreign or empty
  element namespace is accepted. Namespace-prefix spelling is not semantic.
- The tree contains at most 4,096 element nodes, has root depth 1 and maximum element depth 64, and
  every `OMBVAR` contains 1..256 declarations.
- Every XML attribute value and every text/literal value is at most 20,000 Unicode code points before
  whitespace canonicalization. The canonical statement, proof strategy, and each Sketch step are
  nonblank and at most 20,000 code points; Sketch steps contain at most 256 entries. A storage-valid
  Draft ID is nonblank and at most 20,000 code points, but a retrieval-eligible Draft ID must
  additionally match exact ASCII regex `[a-z][a-z0-9_]{0,63}`.
- The packaged manifest contains at most 4,096 Draft rows. The natural-language retrieval statement
  is nonblank valid UTF-8 and at most 16,384 UTF-8 bytes. For each compatible row, the complete
  requirement-defined reranker candidate object serialized as RFC 8785 JCS is at most 16,384 UTF-8
  bytes. The complete provider request body defined below is at most 262,144 UTF-8 bytes. Every
  bound is measured before provider invocation; no string, row, step, candidate, or request is
  truncated. A primitive storage maximum passes its own validator only when all enclosing
  aggregates independently remain within their maxima. A storage-valid row that exceeds the
  candidate aggregate or eligible-ID grammar is quarantined as retrieval-incompatible. Each
  primitive and aggregate exact maximum has a separate composable fixture that passes, and its
  maximum plus one fails with the first applicable error below.
- The only accepted elements, child grammar, and non-namespace attributes are:

| Element | Children | Attributes |
|---|---|---|
| `OMOBJ` | exactly one OpenMath object | required `version="2.0"`; optional `cdbase` |
| `OMS` | none | required nonblank `cd`, `name`; optional `cdbase` |
| `OMV` | none | required nonblank `name` |
| `OMI` | none | none; text matches `-?(0|[1-9][0-9]*|x[0-9A-Fa-f]+)` after concatenating Python `str.split()` tokens |
| `OMB` | none | none; text is canonical padded base64 after removing only CR/LF/SP/FF/HTAB |
| `OMF` | none | exactly one of `dec` or `hex`; `hex` is 16 uppercase hexadecimal digits and `dec` matches `-?([0-9]+(\.[0-9]+)?|\.[0-9]+)([eE]-?[0-9]+)?|INF|-INF|NaN` |
| `OMA` | at least two: an `OMS` with application role, then arguments | none |
| `OMBIND` | exactly an `OMS` with binder role, `OMBVAR`, body | none |
| `OMBVAR` | 1..256 `OMV` declarations | none |

`OMSTR`, `OME`, `OMATTR`, `OMATP`, `OMR`, every other OpenMath constructor, `id`/`xml:id`, local
reference attributes, and every unlisted attribute are rejected in this focused retrieval profile.
Direct `OMV` application heads remain rejected. Explicit `fns1:lambda` is the sole generic
function-valued constructor; a bound function variable may occur only in a registered typed
function position. A lambda obtains its exact result sort from its validated body and may appear
only in a registry position that requires that function sort.
`arith1:sum|product` and `set1:map|suchthat` use only the function-consuming signatures above and
must never be reinterpreted as ordinary `term × term -> term`.
This is intentionally narrower than the general-purpose validator evidence. All non-literal
element text and all non-whitespace child tails are rejected.

`cdbase` resolves by taking the nearest nonblank `cdbase` on the `OMS` itself or an ancestor;
absence resolves to exact standard URI `http://www.openmath.org/cd`. A standard registry symbol
must resolve to that URI. A `pals1` symbol must resolve to exact
`urn:pals:openmath:cd:v1`; a missing, empty, inherited-wrong, or other URI fails.

Semantic validation uses exactly seven sorts: `term`, `proposition`, `term_function`,
`predicate_function`, `real_function`, `real_sequence`, and `natural_index`. `OMI`, `OMB`, `OMF`, and every term
constant have sort `term`; proposition constants have sort `proposition`. A bound `OMV` starts
with the exact sort declared by its binder (term for generic binders, the registered PFI-008 sort
for typed PALS binders, and `natural_index` for `sequence_lambda`) and every occurrence must match.
Arithmetic/set term applications require only term arguments and return term. Relations and
pre-PFI-008 `pals1` predicates require only term arguments and return proposition; PFI-008
predicates use the registered function, sequence, and term signatures below. Logical connectives
require only proposition arguments and return proposition. `quant1:exists|forall` binds one through
256 distinct `OMV` term variables and requires a proposition body, returning proposition. No
implicit coercion, unknown sort, polymorphism, free variable, or child-Spec type extension exists.
`fns1:lambda` binds one through 256 distinct term variables and returns `term_function` when its
body is term or `predicate_function` when its body is proposition; it satisfies `real_function`
only in a registered PFI-008 real-function position. `real_sequence` is constructed only by
`pals1:sequence_lambda` or the registered sequence constructors. `sequence_lambda` binds only
`natural_index`; `index_zero`, `index_succ`, and `index_to_real` use exactly their registered
sorts. Within a `continuity-v1` `sequence_lambda` term body, `sequence_apply` requires
`real_sequence,natural_index` and returns `term`; it is otherwise invalid.
`sum|product` require `term,term_function`;
`map` requires `term_function,term`; `suchthat` requires `term,predicate_function`; and
`continuous_on` requires `term,real_function`. The PFI-008 symbols use exactly the additional
positions and results stated in the registry. The sole `OMOBJ` child must infer exact
`proposition`; all other roots fail before embedding.

This seven-sort validation is the lower-level canonicalizer profile and may preserve free term
`OMV` bytes for canonicalizer-only comparison fixtures. The admitted retrieval gate is stricter:
after lower-level validation/canonicalization and before embedding, it performs one lexical-scope
walk and requires every `OMV` occurrence to resolve to an enclosing `OMBVAR` declaration. Any free
variable returns `openmath_semantic_invalid` and performs no embedding, database query, evidence
scoring, or reranker call. Therefore the free-`x,y` prefix and 48-weight fixtures below are
canonicalizer-only oracles and are never admitted retrieval propositions.

## Exact Binder and Canonical Serialization Contract

Canonicalization validates first, deep-copies the tree, and traverses deterministically. A single
document-global counter starts at 1. For each `OMBIND`, its binder is processed under the incoming
environment; declarations are processed left-to-right; duplicate original names in the same
`OMBVAR` fail; each declaration is renamed `v<counter>` and increments the counter; the body is
processed under a copied environment extended by those declarations. An inner declaration shadows
the same original name only in its body. Bound references receive the nearest mapped canonical
name; free variables remain byte-for-byte unchanged.

After alpha-renaming, element text whose Python `str.strip()` is empty and child tails whose Python
`str.strip()` is empty are removed. `OMI` text becomes `"".join(text.split())`; other literal text
is preserved. Serialize the mutated tree with CPython 3.12.13
`xml.etree.ElementTree.tostring(..., encoding="unicode")`, then run that exact runtime's
ElementTree C14N 2.0 `canonicalize` with `with_comments=false`, `strip_text=false`,
`rewrite_prefixes=true`, and empty QName-aware/excluded tag/attribute sets. Prefix rewriting is
mandatory and makes input prefix spelling and process-global `register_namespace` state
non-semantic. The raw C14N Unicode output is an intermediate only. In this fixed runtime/profile
it must contain exactly one occurrence of the literal ` xmlns:n0=""`; otherwise
canonicalization fails. Remove that exact one occurrence, without any other replacement or
whitespace/namespace normalization. The resulting Unicode string must parse as closed OpenMath
under the same parser and a fresh full canonicalization of it (including this same one-artifact
removal) must reproduce it byte-for-byte. That valid transport-canonical Unicode string encoded
as UTF-8 is the sole C14N v4 canonical byte sequence; a source field containing `xmlns:n0=""` is
invalid and must reject rather than receive a read-time repair. `openmath-cdbase-alpha-c14n-v3`
identifies only the invalid historical raw representation and is never compatible with v4.
`exact_equivalence` is exact
equality of those valid transport-canonical bytes.

The PFI build-provenance property is carried only inside the already PRX-signed worker image; it
does not add a PRX root member, artifact row, signer, key, or trust system. The OCI config contains
exactly one `io.pals.draft-retrieval-provenance.v1` label whose value is unpadded base64url of the
exact RFC 8785 JCS bytes, without LF, of:

```json
{"canonicalizer_version":"openmath-cdbase-alpha-c14n-v4","curriculum_evidence_path":"<absolute-posix-path>","curriculum_evidence_sha256":"<hex64>","curriculum_manifest_path":"<absolute-posix-path>","curriculum_manifest_sha256":"<hex64>","elementtree_source_path":"<absolute-posix-path>","elementtree_source_sha256":"<hex64>","property_id":"PFI-BP-001","python_version":"3.12.13","schema_version":"pals.draft-retrieval-build-provenance.v1","seed_count":42,"seed_file_sha256":"<hex64>","seed_manifest_sha256":"sha256:<hex64>","seed_path":"<absolute-posix-path>","source_commit":"<40-lowercase-hex>"}
```

The displayed `42` is only an in-range JSON example: in a concrete label `seed_count` is an integer
in `[1,4096]` equal to the exact complete-seed row count, never a fixed literal. The same config contains exactly one
`io.pals.draft-retrieval-provenance.sha256` label equal to the lowercase SHA-256 of those decoded
JCS bytes. The closed PFI property registry contains exactly
`PFI-BP-001 -> [PFI-001,PFI-004,PFI-008]`; unknown, missing, duplicate, cross-owner, or differently mapped
property IDs fail build and release validation. `source_commit` equals the approved PRX manifest
`source_commits["pals-agent"]`. `elementtree_source_path` is the absolute POSIX path obtained by
resolving `Path(sysconfig.get_path("stdlib")) / "xml/etree/ElementTree.py"` inside that image; it
is a readable regular non-symlink file.
`elementtree_source_sha256` hashes that file's exact raw bytes without decoding or newline
normalization. `seed_path`, `curriculum_manifest_path`, and `curriculum_evidence_path` are distinct
absolute normalized POSIX paths without `.` or `..`, each names one regular non-symlink file inside
the final worker-image filesystem, and none is under `/proc`, `/sys`, `/dev`, `/run`, or `/tmp`.
`seed_file_sha256`, `curriculum_manifest_sha256`, and `curriculum_evidence_sha256` hash their
respective exact raw files. The seed file is
duplicate-aware JSON whose root is exactly
`{schema_version:"pals.draft-catalog-seed.v1",fingerprint,rows}` with no extra key.
`fingerprint` is the exact seven-field PFI tuple. `rows` is ordered by Draft ID and has `0..4096`
objects containing exactly the five seed-manifest fields defined below plus `embedding`; every
row is retrieval-eligible including the 16,384-byte candidate-JCS bound, and every embedding
satisfies the exact fingerprint dimension/binary32/nonzero rules. The file itself is exact no-LF
RFC 8785 JCS and at most 536,870,912 bytes. Agent-owned release tooling creates these canonicalized, embedded bytes
before the worker image is built. `seed_manifest_sha256` hashes the exact no-LF RFC 8785 JCS
projection of `rows` with `embedding` removed; `seed_count` is the row count. API does not
canonicalize, embed, call a provider, or accept an alternate seed producer during publication.
These observed seed values and fingerprint must equal the catalog manifest/count/fingerprint
admitted for publication.

The file at `curriculum_manifest_path` is duplicate-aware JSON and exact no-LF RFC 8785 JCS no
larger than 16,777,216 bytes. Its root is exactly:

```json
{"base_seed_manifest_sha256":"sha256:<hex64>","catalog_sha256":"sha256:<hex64>","coverage_profile_sha256":"sha256:<hex64>","curriculum_version":"continuity-v1","rows":[{"authorship_attestation_sha256":"sha256:<hex64>","canonical_statement_sha256":"sha256:<hex64>","coverage_objective":"<token>","coverage_sha256":"sha256:<hex64>","draft_id":"<id>","lean_receipt_sha256":"sha256:<hex64>","openmath_xml_sha256":"sha256:<hex64>","proof_strategy_sha256":"sha256:<hex64>","sketch_steps_sha256":"sha256:<hex64>","source_review_attestation_sha256":"sha256:<hex64>"}],"schema_version":"pals.continuity-coverage-manifest.v2","seed_manifest_sha256":"sha256:<hex64>"}
```

Every hash uses exactly lowercase SHA-256 hexadecimal with the displayed `sha256:` prefix;
`coverage_objective` and `draft_id` each satisfy the PFI retrieval-ID grammar. Rows are ordered by
valid UTF-8 `draft_id`, unique, and nonempty. `base_seed_manifest_sha256` hashes the exact no-LF
JCS seed projection of the already signed, pre-PFI-008 31-row restoration generation. Let `B` be
the exact rows in that projection and `P` the manifest row IDs; `P` is the exact set of pilot IDs.
`P` is nonempty, no larger than the existing manifest row bound, and equals the unique ID set in
the approved child `continuity-v1` catalog, the evidence bundle, and the Lean-receipt collection.
`catalog_sha256` hashes the source catalog's exact no-LF JCS bytes. `coverage_profile_sha256`
hashes the exact no-LF JCS `coverage_profile` member of that catalog. For each row,
`coverage_sha256` hashes that card's exact no-LF JCS `coverage` object. API recomputes and binds
all three values before its database transaction.
The full `continuity-v1` seed has
IDs exactly `IDs(B) ∪ P`, those sets are disjoint, every `B` row is byte-identical in the five
non-embedding Draft fields `id,canonical_statement,openmath_xml,proof_strategy,sketch_steps` to its base
projection, and every ID outside `B` occurs exactly once in this manifest. `embedding` is not part
of `B`: Agent recomputes it from the unchanged canonical OpenMath through the new signed fingerprint
before the full seed is built, and API never copies or compares a base-generation embedding. API
obtains `B` only from the currently active immutable generation after requiring that generation's
signed `seed_manifest_sha256` equal `base_seed_manifest_sha256`; missing/mismatched base generation
or any five-field content drift blocks the release.
Thus `P` is precisely the pilot delta, not an optional subset of a seed that can carry unreviewed
new rows. Its `seed_manifest_sha256` equals the provenance label and the no-LF JCS projection of
the complete seed. For every manifest row, API hashes the seed row's exact
`canonical_statement`, `openmath_xml`, and `proof_strategy` UTF-8 bytes and its exact no-LF JCS
`sketch_steps` array and requires equality with the four displayed hashes. A manifest ID not present
in the seed, a seed row named by more than one manifest row, a new ID outside the manifest, a base
row drift, a hash mismatch, excess key, invalid JCS, or mismatch with the signed provenance label
fails before a database transaction. The complete manifest is an immutable part of the signed
worker release artifact, not a Draft field or query-time payload.

The file at `curriculum_evidence_path` is duplicate-aware JSON and exact no-LF RFC 8785 JCS no
larger than 16,777,216 bytes. Its root is exactly
`{"records":[{"authorship_attestation":{},"lean_receipt":{},"source_review_attestation":{}}],"schema_version":"pals.continuity-evidence-bundle.v1"}`.
Records are ordered by their shared valid UTF-8 Draft ID and unique; every nested object is exactly
the requirements-defined attestation or receipt object and has no extra key. API hashes each nested
object's no-LF JCS bytes and requires the exact three hashes named by its manifest row. It validates
the evidence-bundle raw-file hash from PFI-BP-001 before these checks. The existing PRX-signed
worker image is the sole authorization for the evidence bundle: its accepted signature attests that
the fixed `pals_curriculum_author` and `pals_curriculum_reviewer` review dispositions were supplied
for this exact content. Neither role string is a credential or a separately trusted identity.

After complete PRX admission and before PFI catalog admission, the parent release helper receives
only the exact admitted platform-specific `worker_image_digest` plus an untrusted local OCI Image
Layout directory. No provider observation, registry endpoint, credential, tag, or network result is
an authority. The helper opens no symlink and accepts only regular files beneath the resolved layout
root. `oci-layout` is exact UTF-8 `{"imageLayoutVersion":"1.0.0"}` plus one LF. `index.json` is
duplicate-aware valid JSON with exact root keys `schemaVersion,manifests`, exact
`schemaVersion=2`, and exactly one descriptor. Every descriptor is a duplicate-aware object with
exact keys `mediaType,digest,size`; the index descriptor has
`mediaType="application/vnd.oci.image.manifest.v1+json"`, `digest` equal to the admitted worker
digest, integer `size` in `[1,1048576]`, and no platform ambiguity. The helper reads exact
`blobs/sha256/<digest suffix>`, requires path containment, declared size and lowercase SHA-256
equality, and caps index, manifest, and config at 1,048,576 bytes each. The manifest is
duplicate-aware JSON with exact root keys `schemaVersion,mediaType,config,layers`, exact
`schemaVersion=2`, and exact
`mediaType="application/vnd.oci.image.manifest.v1+json"`. It has one config descriptor with
`mediaType="application/vnd.oci.image.config.v1+json"`, lowercase SHA-256 digest, and integer
`size` in `[1,1048576]`, and `1..128` ordered layer descriptors using only
`application/vnd.oci.image.layer.v1.tar` or
`application/vnd.oci.image.layer.v1.tar+gzip`. Every layer descriptor has lowercase SHA-256 digest
and declared size in `[1,1073741824]`; the sum of compressed layer sizes is at most 4,294,967,296
bytes. Every verified blob is read through no-follow regular-file descriptors and rechecked for
device/inode/size after reading. Config JSON and every nested object are duplicate-aware parsed;
its root must be an object, `config` must be an object, `config.Labels` must be an object, and the
two labels above are validated. Unknown config fields remain signed non-authoritative OCI metadata
and cannot alter PFI behavior.

The API release controller, and no Agent runtime, resolves the labeled `seed_path` by applying the
ordered layers as one OCI overlay into a fresh private temporary directory. It permits only POSIX
ustar headers and, for gzip layers, one gzip member with no trailing bytes; caps each expanded layer
at 2,147,483,648 bytes, the aggregate expansion at 8,589,934,592 bytes, entries at 1,000,000, and
each path at 4,096 UTF-8 bytes. Absolute paths, empty components, `.`/`..`, backslash, NUL,
non-UTF-8 names, pax/GNU extensions, devices, FIFOs, sockets, setuid/setgid/sticky bits, sparse
files, and hardlinks are rejected. A symlink is accepted only when both its normalized parent-
relative target and every eventual traversal remain beneath the extraction root; extraction uses
no-follow directory descriptors and never follows an existing symlink while creating or replacing
an entry. OCI whiteouts are accepted only as regular zero-byte `.wh.<name>` or
`.wh..wh..opq` entries, delete only an already-extracted descendant beneath the same root, and are
never exposed as files. Duplicate paths within one layer, type replacement without an explicit
whiteout, case-fold collisions, entry/descriptor count drift, decompression overflow, or any
time-of-check/time-of-use identity change fails closed. After the last layer, the controller opens
`seed_path`, `curriculum_manifest_path`, and `curriculum_evidence_path` through separate no-follow
descriptors, requires the seed to be one regular file of at most 536,870,912 bytes and each
curriculum file to be one regular file of at most 16,777,216 bytes, and validates their file
digests, duplicate-aware JSON, exact schemas, JCS bytes, manifest-to-seed and manifest-to-evidence
binding, and seed count before any database transaction.

Unknown/missing/duplicate descriptors or labels, extra index descriptors, symlink/nonregular/path
escape, invalid base64url, non-JCS child bytes, digest/source/path/property/seed/manifest/evidence mismatch, mutable
tag/index substitution, or any acquisition/extraction failure is
`canonicalizer_provenance_mismatch` before catalog access. Because every consumed blob chains to
the already signed worker manifest digest, the layout is only a content-addressed byte carrier and
needs no producer, signature, freshness, or replay authority. This PFI helper does not repeat or
replace PRX signature, trust, image, source, expiry, or replay checks.

Database provenance does not claim an unavailable OCI identity. API imports the exact admitted PRX
Infra deployment-bundle fields `environment`,
`database.{endpoint_host,endpoint_port,database_name,database_resource_id}` and requires
`endpoint_port=5432`; no PFI configuration, request, environment variable, DSN, or Agent value may
supply or override any member. Before opening either PFI connection, API exact-matches those fields
to the same admitted release currently held by its approved PRX/PJR deployment gate. AWS `dev|prod`
uses the existing approved API typed-pool callback to mint a fresh one-use IAM token for that exact
resource and host, passes it directly to the driver in memory, and uses TLS `verify-full` with
`server_hostname=endpoint_host`; local uses the approved token-verifier callback bound to the exact
local endpoint/name/resource tuple. Credential-bearing DSNs, passwords, tokens, and database
credentials are absent from Agent, request/response bytes, environment, argv, files, logs, traces,
metrics, and PFI rows.

Catalog publication/migration authenticates only as the existing
`pals_api_release_migrator`, asserts `session_user`, then uses only its approved
`pals_api_schema_owner` role. Runtime candidate lookup authenticates only as
`pals_api_runtime_executor`, asserts that `session_user`, then uses only
`pals_api_runtime`; the owning API child Spec must enumerate the minimum PFI tables, columns,
functions, and ACLs before implementation, and grants no Agent/database role or credential. In the
same repeatable-read transaction used for the active snapshot and candidate query, API requires
`current_database()` to equal the bundle name,
`current_setting('server_version_num')::integer` in `[160000,169999]`, `SHOW server_encoding` equal
`UTF8`, `pg_collation.collname='C'` with `collprovider='c'` and `collencoding IN (-1,6)`, and one
installed `vector` extension version matching the exact semantic-version grammar below. Missing or
mismatched admitted-release binding, endpoint, port, TLS hostname, IAM/local token target, login,
role, database name/resource, or live observation fails before the active catalog snapshot is read.

The required prefix oracle for
`<OMOBJ xmlns="http://www.openmath.org/OpenMath" version="2.0"><OMA><OMS cd="relation1"
name="eq"/><OMV name="x"/><OMV name="y"/></OMA></OMOBJ>` is exact UTF-8 without a terminal LF:

```text
<n1:OMOBJ xmlns:n1="http://www.openmath.org/OpenMath" version="2.0"><n1:OMA><n1:OMS cd="relation1" name="eq"></n1:OMS><n1:OMV name="x"></n1:OMV><n1:OMV name="y"></n1:OMV></n1:OMA></n1:OMOBJ>
```

Its SHA-256 is exact
`a888813eb8c530dda0513e75e6bb833767e326a1d475c08ccbfcf828d5689565`.

Default-namespace, arbitrary-prefix, and any prior `register_namespace` fixture must produce these
same v4 bytes. This free-variable fixture exercises only lower-level canonicalization; the
separate closed-proposition retrieval gate rejects it before embedding. The preceding raw form
with exactly one `xmlns:n0=""` declaration is a required rejection fixture, never a byte oracle.

## Exact Private Candidate Port

The only PFI API surface is worker-authenticated
`POST /v1/internal/proof-flow-index/candidates`. It is absent from the public OpenAPI document,
public router, browser/CORS surface, proxy allowlist, and user authorization path. It imports the
existing PEX-008 `X-PALS-Worker-Secret` comparison and precedence without defining another secret:
missing server configuration returns 503 `worker_secret_not_configured`; otherwise a missing,
duplicate, or invalid header returns 401 `worker_secret_invalid`; only a valid header permits media
type/body/schema validation. Authentication runs before any body byte is decoded, database
connection is opened, or domain state is observed.

The request requires exact `Content-Type: application/json`, is at most 262,144 UTF-8 bytes, is
duplicate-aware and extra-forbid, and is exactly:

```json
{"schema_version":"pals.draft-candidate-query.v1","embedding":[0.0],"fingerprint":{"provider":"<id>","model":"<id>","endpoint":"<id>","deployment":"<id>","revision":"<id>","dimension":1,"canonicalizer_version":"openmath-cdbase-alpha-c14n-v4"}}
```

Every fingerprint string is nonblank and satisfies its existing PFI-002 bound; the fingerprint is
the exact seven-field tuple already defined here. `embedding` contains exactly `dimension` JSON
numbers, dimension is in `[1,4096]`, every number converts by the defined binary32 rule to finite
binary32, and the resulting vector has nonzero norm. The body contains no natural statement,
OpenMath, user/account/project/proof identifier, Draft ID, secret, trace, prompt, provider output,
or caller-selected catalog/provenance value. Agent sends exactly one request per retrieval after
its input/canonicalizer/fingerprint/embedding checks, with a 10-second hard deadline, no redirect,
retry, cache, alternate route, direct database access, or fallback.

On success API returns HTTP 200, exact `Content-Type: application/json`, at most 262,144 UTF-8
bytes, and the extra-forbid object:

```json
{"schema_version":"pals.draft-candidate-result.v1","generation_id":"<uuidv4>","manifest_sha256":"sha256:<hex64>","seed_count":42,"runtime_provenance_sha256":"<hex64>","fingerprint":{"provider":"<id>","model":"<id>","endpoint":"<id>","deployment":"<id>","revision":"<id>","dimension":1,"canonicalizer_version":"openmath-cdbase-alpha-c14n-v4"},"candidates":[{"draft":{"id":"<id>","canonical_statement":"<text>","openmath_xml":"<canonical>","proof_strategy":"<text>","sketch_steps":["<ordered>"]},"cosine_distance":0.0}]}
```

The response echoes only server-validated active-snapshot values. `generation_id`, manifest,
`seed_count`, runtime provenance, fingerprint, Draft fields, eligible ID grammar, candidate JCS
bound, distance, and numeric serialization use the exact contracts below. `candidates` contains
`0..8` unique rows in the database order returned by the sole query; it is not re-sorted or
truncated by API or Agent.
API performs no canonicalization, embedding, structural scoring, rerank, provider call, or final
context selection. Agent rejects a response whose fingerprint, manifest, runtime provenance,
generation, ordering, count, IDs, rows, distance, media type, or aggregate bound is invalid; it does
not salvage a subset.

After authentication, the imported API normalized validation contract handles unsupported media
type/malformed/duplicate/extra/type/bound failures and performs zero repository work. A
fingerprint, manifest, provenance, generation, eligibility, count, database-binding, or release
admission mismatch returns the standard API error envelope with HTTP 409 code
`draft_catalog_incompatible`. A connection, transaction, deadline, or unambiguously rolled-back
read failure returns HTTP 503 `draft_retrieval_unavailable`. API never retries the query. Agent maps
either a nonconforming API response or `draft_catalog_incompatible` to its first applicable closed
PFI compatibility error and maps `draft_retrieval_unavailable`, transport failure, or its own
10-second deadline to `retrieval_unavailable`; no API error body is exposed in the final PFI DTO.

## Exact Retrieval and Compatibility Formulas

One API-owned immutable `ActiveCatalogSnapshot` governs both admission count and retrieval. Its metadata is
exactly
`{generation_id,manifest_sha256,seed_count,fingerprint,runtime_provenance_sha256,row_count,state}`:
`generation_id` is lowercase hyphenated UUIDv4, `manifest_sha256` and
`runtime_provenance_sha256` are the exact values defined here, `fingerprint` is the exact
seven-field tuple, `seed_count` and `row_count` are integers in `[0,4096]` and exactly equal, and
`state` is exactly `readable`.
The atomic active pointer names one generation only. A row is eligible iff, in this order, it:

1. belongs to that exact active generation and exact manifest;
2. passes every PFI-002 storage-field and manifest-membership check;
3. has an ID matching `[a-z][a-z0-9_]{0,63}`;
4. has exact closed-profile canonical OpenMath and a complete candidate JCS of at most 16,384 bytes;
5. has the active fingerprint and runtime-provenance digest plus a valid finite nonzero embedding;
6. has no immutable quarantine record for that generation.

The exact signed seed rows are the sole source copied into the new immutable generation. Every
preexisting database row that is not byte-identical across all six fields to the same-ID seed row,
including an otherwise profile-compatible custom/retained row, receives one immutable reasoned
quarantine record and is not copied; an exact same-ID six-field duplicate is migration evidence
only and still produces no second row. No prior, future, mixed-fingerprint, mixed-provenance,
non-seed, or quarantined row is eligible. Publication validates
`seed_count == row_count == COUNT(*)` under this exact predicate and atomically switches the pointer
only after the complete seed rows, manifest, metadata, and quarantine ledger commit. Release count and each
retrieval read the same pointer, metadata, and eligible population in one repeatable-read
transaction; a pointer/generation/count mismatch is `catalog_migration_incompatible` at admission
and `retrieval_unavailable` at runtime. A cached or separately computed eligible count is invalid.
`eligible_row_count` below means exactly this transaction's validated `row_count`, never another
table, generation, cache, manifest count, or pre-migration source count.

1. Agent validates and canonicalizes under the exact contracts above.
2. Agent embeds that canonical query and calls the private candidate port exactly once. API executes
   exactly one PostgreSQL/pgvector query over eligible persisted Draft rows in that transaction's
   exact active generation. Admission requires PostgreSQL
   `server_encoding=UTF8` and the built-in bytewise
   collation named exactly `C`; the ordering clause is exactly
   `ORDER BY (embedding <=> $1::vector) ASC, id COLLATE "C" ASC LIMIT 8`. Valid UTF-8 byte order is
   Unicode code-point lexicographic order, so the second key is locale-independent. The query
   returns exactly `min(8, eligible_row_count)` unique Draft IDs. Unit/local fixtures explicitly
   support eligible counts `0..7`; release admission requires `eligible_row_count >= 8` and its
   real gate observes exactly eight rows before traffic is enabled. Packaged rows may seed the
   database during an explicit catalog migration, but runtime retrieval must not union, append,
   substitute, or fall back to packaged rows.
3. Agent validates the exact candidate response and computes
   `vector_score = clamp(1 - cosine_distance, 0, 1)`.
4. Agent builds the structural feature multiset using the exact grammar below.
5. `overlap` is the sum of multiset intersection counts. If either feature-weight sum is zero,
   structural score is `0`; otherwise
   `structural_score = clamp(0.85*(overlap/query_weight) +
   0.15*(overlap/candidate_weight),0,1)`.
6. Vector and structural scores are evidence only and never select, exclude, threshold, or reorder a
   candidate. The reranker request subject is the exact RFC 8785 JCS UTF-8 serialization, without a
   terminal LF, of an object whose keys and shapes are exactly
   `schema_version="pals.draft-relevance-request.v1"`, `natural_statement`,
   `query_openmath`, `candidates`, and `compatibility`. `candidates` preserves database order and
   contains every returned row as exactly the same `draft` and `evidence` objects used by the result
   DTO below. `compatibility` is the complete result compatibility object below. Missing, extra,
   reordered candidate, duplicate, non-JCS, or over-bound bytes fail before a provider call.
7. The reranker is exactly one real PAE `draft`-role invocation using provider `openai`, model
   `gpt-5.4-mini-2026-03-17`, provider API `openai.responses.v1`, and contract version
   `pals.draft-relevance-reranker.v1`. The exact 332-byte UTF-8 prompt prefix, without BOM or
   terminal LF, is:

   ```text
   You are the PALS Draft relevance reranker v1. Read REQUEST_JCS. Return only the strict JSON selection. Select zero through four unique supplied draft IDs in descending semantic usefulness for proving the exact query. Similarity, lexical overlap, exact equality, and candidate order are evidence only. Do not add facts, code, or IDs.
   ```

   Its SHA-256 is
   `ee3210814e58edab5fa2a5878100b310d7811df23e3c5f2d09d93d8f3cc03d00`.
   The Responses API `input` string is exactly that prefix plus LF, literal `REQUEST_JCS`, LF, and
   the request-subject JCS text. The request body is RFC 8785 JCS for exactly:

   ```json
   {"input":"<exact input string>","max_output_tokens":512,"model":"gpt-5.4-mini-2026-03-17","store":false,"stream":false,"text":{"format":{"name":"pals_draft_relevance_selection_v1","schema":{"additionalProperties":false,"properties":{"selected_draft_ids":{"items":{"pattern":"^[a-z][a-z0-9_]{0,63}$","type":"string"},"maxItems":4,"type":"array"}},"required":["selected_draft_ids"],"type":"object"},"strict":true,"type":"json_schema"}}}
   ```

   `temperature`, `top_p`, `seed`, `reasoning`, tools, metadata, and every other optional request
   field are absent, not inherited or defaulted by application configuration. Send one HTTPS
   `POST` to exact `https://api.openai.com/v1/responses` with only secret-bearing
   `Authorization: Bearer <key>`, `Content-Type: application/json`, and
   `Accept: application/json`; use certificate verification, no redirect, no proxy rewrite, one
   90.0-second monotonic hard deadline covering connect/write/read, response-body maximum 65,536
   bytes, and zero retries.

   The exact provider schema contains no string keyword except `pattern`, no array keyword except
   `maxItems`, and no unsupported JSON Schema keyword at any depth. Local contract tests compare
   the complete schema object and reject added `maxLength`, `uniqueItems`, or any other keyword.
   The sole release-live request must be admitted by the provider as this exact strict schema; an
   `invalid_json_schema` or semantically equivalent pre-generation rejection blocks release.

   A successful provider envelope is duplicate-aware valid UTF-8 JSON. The top level is an object
   and must contain `object="response"`, `status="completed"`, `error=null`,
   `incomplete_details=null`, and `model="gpt-5.4-mini-2026-03-17"`. Missing, duplicate, wrong-type,
   or different values are invalid. Other top-level provider metadata except the exact content-free
   `usage` object below is ignored only after these required fields pass; it is never persisted,
   logged, or used for identity, selection, cost, or retry. `usage` is parsed only for the closed
   normalization and release-cost evidence contract and never participates in selection or retry.
   `output` is exactly a one-item array. That item is exactly one assistant message with
   `type="message"`, `role="assistant"`, `status="completed"`, no refusal/reasoning/tool/function/
   computer/custom item, and `content` exactly a one-item array. The content item has
   `type="output_text"`, `annotations=[]`, no refusal member, and one `text` string. Provider-added
   message/content metadata may be ignored but no second item or other item type is permitted.
   The `text` UTF-8 encoding is at most 512 bytes and contains exactly one JSON object with no
   duplicate key or trailing non-whitespace. That object is extra-forbid
   `{"selected_draft_ids":["<id>"]}` with zero through four unique IDs matching the eligible-ID
   grammar and drawn from the supplied candidates. Four maximum-length IDs fit below the 512-byte
   text maximum; `max_output_tokens=512` therefore does not make a schema-valid selection
   structurally impossible, independent of tokenizer merges. Response array order is context
   order. Transport/TLS/DNS/timeout/non-2xx/oversized envelope is `reranker_unavailable`; a 2xx
   incomplete/canceled/failed/refused envelope, malformed JSON/text/schema/path, wrong model,
   duplicate/foreign ID, or identity/contract mismatch is `reranker_invalid`. Zero IDs yields
   `no_match`; one through four yields `match`. No retry, fallback, repair, alternate prompt,
   alternate endpoint, cached result, deterministic score, or seed union participates.
8. The embedding fingerprint is the exact seven-field tuple
   `(provider,model,endpoint,deployment,revision,dimension,canonicalizer_version)`, every string
   nonblank, dimension positive, and `canonicalizer_version` exactly
   `openmath-cdbase-alpha-c14n-v4`. Stored and configured tuples must be exactly equal.
9. Draft IDs are unique within the signed seed. The packaged/in-memory field
   `ProofDraft.matched_prompt` maps byte-for-byte, without trim or normalization, to persistent,
   response, and manifest field `canonical_statement`; the two names are never independent fields.
   The seed-manifest subject is an array ordered by Draft ID using the same valid-UTF-8 bytewise
   order where every object contains exactly
   `id,canonical_statement,openmath_xml,proof_strategy,sketch_steps`; `openmath_xml` is the canonical
   UTF-8 string and `sketch_steps` preserves order. Serialize that complete array as RFC 8785 JCS
   UTF-8 with no terminal LF. The seed manifest is exactly
   `"sha256:" + lowercase_hex(SHA-256(those_exact_JCS_bytes))`. Stored manifest/count must equal the
   signed seed manifest/count; duplicate IDs, any row in the readable generation outside that exact
   seed projection, legacy `matched_prompt` manifest keys, alternate escaping, insignificant
   whitespace, or a terminal LF fail before catalog access. Immutable quarantine-history rows are
   outside the readable generation and do not trigger this predicate.

Embedding dimension is an integer in `[1,4096]` and equals both the fingerprint dimension and the
PostgreSQL `vector(n)` dimension. Provider output is accepted only as exactly that many finite JSON
numbers; each converts by IEEE 754 round-to-nearest-ties-to-even to finite binary32, and the
binary32 vector must contain at least one component other than `+0.0|-0.0`. Stored vectors satisfy the
same checks. NaN, infinity, overflow, zero norm, null distance, dimension mismatch, or non-finite
database result is `embedding_invalid` before candidate selection.

The PFI admission gate combines the authenticated worker child property, exact admitted PRX worker
image/source and database resource tuple, and live database observations above. Runtime provenance
is exactly the RFC 8785 JCS UTF-8 serialization plus one terminal LF of:

```json
{"canonicalizer":{"build_provenance_sha256":"<hex64>","canonicalizer_version":"openmath-cdbase-alpha-c14n-v4","elementtree_source_path":"<absolute-posix-path>","elementtree_source_sha256":"<hex64>","python_version":"3.12.13","source_commit":"<40-lowercase-hex>","worker_image_manifest_sha256":"<hex64>"},"database":{"current_user":"pals_api_runtime","database_name":"<signed PRX value>","database_resource_id":"<signed PRX value>","draft_id_collation":"C","endpoint_host":"<signed PRX value>","endpoint_port":5432,"environment":"local|dev|prod","pgvector_version":"<MAJOR.MINOR.PATCH>","postgresql_server_version_num":160000,"server_encoding":"UTF8","session_user":"pals_api_runtime_executor","transport":"local-token-verifier|tls-verify-full-iam"},"schema_version":"pals.draft-retrieval-runtime-provenance.v1"}
```

All placeholders are substituted before serialization. The path and source commit are the exact
validated child-property values; `worker_image_manifest_sha256` is the suffix of the admitted PRX
worker digest; `build_provenance_sha256` is the child label digest; the database
environment/endpoint/name/resource values are exact admitted PRX Infra bundle values;
`transport` is `local-token-verifier` exactly for local and `tls-verify-full-iam` exactly for
`dev|prod`; session/current user are live assertions from the same candidate-query transaction;
`postgresql_server_version_num` is the live integer in
`[160000,169999]`; every digest is 64 lowercase hexadecimal; and `pgvector_version` matches
`(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)`. The lowercase SHA-256 of these complete
JCS-plus-LF bytes is the sole `runtime_provenance_sha256` value in match and `no_match` responses;
no subset, display JSON, manifest digest, database-image claim, or newline-free variant may
substitute. The pgvector cosine operator
returns one finite IEEE 754 binary64 distance per eligible row. Application evidence scoring uses strict
IEEE 754 binary64 round-to-nearest-ties-to-even after every displayed subtraction,
multiplication, addition, division, and clamp, with no decimal rounding, epsilon, fused
multiply-add, database-computed structural score, or alternate precision. Ordering compares only
the exact database distance and Draft ID; `-0.0` is canonicalized to `+0.0`.

### Exact internal result and error DTO

Every internal response is extra-forbid JSON with keys serialized in the displayed order.
A match is exactly:

```json
{"schema_version":"pals.draft-retrieval.v1","outcome":"match","query_openmath":"<canonical>","contexts":[{"draft":{"id":"<id>","canonical_statement":"<text>","openmath_xml":"<canonical>","proof_strategy":"<text>","sketch_steps":["<ordered>"]},"evidence":{"cosine_distance":0.0,"vector":0.0,"structural":0.0,"exact_equivalence":false}}],"compatibility":{"provider":"<id>","model":"<id>","endpoint":"<id>","deployment":"<id>","revision":"<id>","dimension":1,"canonicalizer_version":"openmath-cdbase-alpha-c14n-v4","seed_manifest_sha256":"<sha256:hex64>","seed_count":42,"runtime_provenance_sha256":"<hex64>","reranker_provider":"openai","reranker_model":"gpt-5.4-mini-2026-03-17","reranker_provider_api":"openai.responses.v1","reranker_contract_version":"pals.draft-relevance-reranker.v1","reranker_prompt_sha256":"ee3210814e58edab5fa2a5878100b310d7811df23e3c5f2d09d93d8f3cc03d00"}}
```

Evidence numbers are finite binary64 results rendered by RFC 8785 JCS number serialization.
`exact_equivalence` is true exactly when query and that Draft's canonical UTF-8 bytes are equal.
`contexts` contains one through four unique Drafts in reranker order. A valid zero-selection result
has the same root keys, with `outcome="no_match"` and `contexts=[]`; it retains the validated
canonical query and compatibility object.

An error is exactly
`{"schema_version":"pals.draft-retrieval.v1","outcome":"error","error":{"code":"<token>"}}`
and exposes no query, Draft, score, provider response, database value, path, or free-form message.
Error precedence and the complete token registry are:

1. `input_too_large`;
2. `xml_invalid`;
3. `resource_limit_exceeded`;
4. `openmath_profile_invalid`;
5. `openmath_semantic_invalid`;
6. `canonicalizer_provenance_mismatch`;
7. `fingerprint_mismatch`;
8. `catalog_manifest_mismatch`;
9. `embedding_invalid`;
10. `candidate_limit_exceeded`;
11. `score_invalid`;
12. `reranker_invalid`;
13. `reranker_unavailable`;
14. `catalog_migration_incompatible`;
15. `retrieval_unavailable`.

The first applicable token wins. `no_match` is never an error, and no error may return partial
context, retry through another provider/catalog, or fall back to text/alias/Lean.
The token domains are closed: OpenMath or natural-statement input-byte overflow is
`input_too_large`; UTF-8/XML parsing, DTD, or entity failure is `xml_invalid`; a
tree/string/binder/manifest-row/candidate-JCS/complete-request bound is
`resource_limit_exceeded`; element/attribute/namespace/cdbase/symbol/arity/sort/root-profile
failure is `openmath_profile_invalid`; binder-scope or closed-retrieval failure is
`openmath_semantic_invalid`; unresolved/mismatched ElementTree source, worker OCI-config child
property, PRX worker image/source binding, or runtime-provenance preimage is
`canonicalizer_provenance_mismatch`; seven-field embedding identity mismatch is
`fingerprint_mismatch`; seed manifest/count/row identity mismatch is
`catalog_manifest_mismatch`; embedding component/dimension/norm/distance failure is
`embedding_invalid`; a database result containing more than eight rows or duplicate Draft IDs is
`candidate_limit_exceeded`; non-finite or nonconforming vector/structural evidence arithmetic is
`score_invalid`; provider identity/request/parser failure is `reranker_invalid`; provider
transport/TLS/DNS/deadline/non-2xx/response-size failure is `reranker_unavailable`;
missing/mismatched admitted PRX database environment/endpoint/port/name/resource, transport,
session/current role, live PostgreSQL/pgvector/UTF8/`C` observation, active
generation/count/predicate, fewer than eight eligible release rows, an incompatible row, or an
incomplete atomic migration is `catalog_migration_incompatible`; and an otherwise compatible
private-candidate transport, database, transaction, or storage operational failure is
`retrieval_unavailable`. No later token may mask an earlier applicable validation failure.

### Exact structural feature-key grammar

Let `S` be the Python tuple representation of resolved
`(cdbase, cd, name)`, including parentheses, comma-space separators, and single-quoted strings.
Let `K(node)` be its local element name. Let `L(OMI)` be its whitespace-removed integer,
`L(OMF)` be `dec:<value>` or `hex:<value>`, and otherwise absent. Iterate every node in document
preorder and add:

- `kind:<K>` with weight 1 for every node;
- for every `OMS` resolving to `S`, `symbol:<S>` with weight 2;
- for every `OMI`, `integer:<L>` with weight 3;
- for an `OMA` whose head resolves to `S`: `operator:<S>` weight 5,
  `operator-shape:<S>:<K(arg0)>,...,<K(argN)>` weight 12, and for each zero-based argument index
  `i`, `argument-kind:<S>:<i>:<K(arg)>` weight 8 plus
  `argument-literal:<S>:<i>:<L(arg)>` weight 10 when `L` exists;
- for every `OMBIND` whose binder resolves to `S`, `binder:<S>` weight 5, plus
  `bound-count:<number of OMBVAR declarations>` weight 4;
- for every `OMA` and `OMBIND`, `subtree:<shape>` weight 8, where
  `shape(OMS)=OMS(<S>)`, `shape(OMV)=OMV`, `shape(OMI)=OMI(<L>)`,
  `shape(OMF)=OMF(<L>)`, and every other accepted node is
  `<K>(<shape(child0)>,...,<shape(childN)>)`.

Repeated identical keys add their weights to the multiset count. `overlap` is the sum of
`min(query[key],candidate[key])` over the key union; the two total weights are the sums of their
multiset counts.

### Known-answer vectors and ties

For canonical `relation1:eq(x,y)`, the exact nonzero feature multiset is:

```text
kind:OMOBJ=1
kind:OMA=1
kind:OMS=1
kind:OMV=2
symbol:('http://www.openmath.org/cd', 'relation1', 'eq')=2
operator:('http://www.openmath.org/cd', 'relation1', 'eq')=5
operator-shape:('http://www.openmath.org/cd', 'relation1', 'eq'):OMV,OMV=12
argument-kind:('http://www.openmath.org/cd', 'relation1', 'eq'):0:OMV=8
argument-kind:('http://www.openmath.org/cd', 'relation1', 'eq'):1:OMV=8
subtree:OMA(OMS(('http://www.openmath.org/cd', 'relation1', 'eq')),OMV,OMV)=8
total=48
```

This 48-weight free-variable vector is a lower-level structural/canonicalizer oracle only. It is
rejected by the admitted retrieval closed-scope gate. The quantified 71-weight vector below is the
corresponding admitted closed retrieval oracle.

For canonical `forall v1. relation1:eq(v1,v1)`, add the binder/document structure and the exact
nonzero multiset is:

```text
kind:OMOBJ=1; kind:OMBIND=1; kind:OMBVAR=1; kind:OMA=1; kind:OMS=2; kind:OMV=3
symbol:('http://www.openmath.org/cd', 'quant1', 'forall')=2
symbol:('http://www.openmath.org/cd', 'relation1', 'eq')=2
binder:('http://www.openmath.org/cd', 'quant1', 'forall')=5
bound-count:1=4
operator:('http://www.openmath.org/cd', 'relation1', 'eq')=5
operator-shape:('http://www.openmath.org/cd', 'relation1', 'eq'):OMV,OMV=12
argument-kind:('http://www.openmath.org/cd', 'relation1', 'eq'):0:OMV=8
argument-kind:('http://www.openmath.org/cd', 'relation1', 'eq'):1:OMV=8
subtree:OMA(OMS(('http://www.openmath.org/cd', 'relation1', 'eq')),OMV,OMV)=8
subtree:OMBIND(OMS(('http://www.openmath.org/cd', 'quant1', 'forall')),OMBVAR(OMV),OMA(OMS(('http://www.openmath.org/cd', 'relation1', 'eq')),OMV,OMV))=8
total=71
```

An identical canonical query/candidate has structural score exactly 1. If Draft IDs `a` and `b`
have identical canonical XML and bit-equal cosine distance, the database presents `a` then `b` to
the reranker. Only the reranker selects either row and determines returned order; database arrival
order, evidence scores, and a deterministic cutoff may not participate.

## Acceptance Criteria

### PFI-001–PFI-004

- Invalid or unknown Content Dictionary symbols and non-propositions are rejected.
- Equivalent bound-variable names canonicalize identically; materially different proposition structure remains distinguishable.
- Every primitive XML/string/node/depth/binder boundary accepts its exact maximum when its enclosing
  aggregate remains valid and rejects maximum plus one before embedding or scoring. Independent
  composable fixtures prove the exact candidate/request/text maxima; a storage-valid primitive that
  exceeds an aggregate is explicitly retrieval-incompatible rather than falsely accepted.
- `OMV` function heads, wrong argument sorts, and non-proposition roots reject under the exact
  seven-sort oracle; admitted lambda/function values are accepted only in registered positions.
- Lower-level free-term-variable canonicalization remains deterministic, while the admitted
  retrieval gate rejects every free `OMV` before embedding. The closed 71-weight fixture enters
  retrieval; the free 48-weight fixture cannot.
- Default/arbitrary prefixes and changed process-global namespace registration produce the exact
  v4 transport-canonical bytes under matching immutable runtime provenance.
- Dimension, finite-binary32, nonzero-norm, finite-distance, strict binary64 evidence arithmetic,
  UTF8/`C` eighth-boundary ties, local eligible counts `0..7`, release count minimum eight, and
  reranker identity/request/prompt/body/timeout/response/cardinality mutations have one result or
  closed error.
- Manifest rows 4,096 and every separately composable request-component/aggregate byte maximum pass;
  maximum plus one fails before provider invocation without truncation. Eligible-ID 64/65-character
  and four-maximum-ID 512-byte selection fixtures pass/fail exactly. Exact ElementTree-source,
  worker OCI-config child-property/seed/layer extraction, PRX database
  environment/endpoint/name/resource/transport/login/role, and live database-observation mutations
  fail admission.
- Agent has no database credential, DSN, client, migration, SQL, or network path. One valid retrieval
  makes exactly one authenticated private candidate request; API makes exactly one active-generation
  SQL query and returns `0..8` rows in database order. Authentication precedence, duplicate-aware
  request/response validation, 10-second deadline, aggregate bounds, connection target, no retry,
  no cache, and every API error mapping are mutation-tested.
- Match, no-match, and every error serialize only the exact DTO and follow the closed precedence.
- Successful response usage accepts only the exact five-field/nested-two-field object; every
  missing, extra, duplicate, negative, non-integer, overflow, `C>I`, `R>O`, or `T!=I+O` mutation is
  `reranker_invalid`. Exact normalized counts, pinned pricing snapshot, arbitrary-precision rational
  cost, half-up micro-USD rounding, evidence schema, 180-day retention, deletion, access, and privacy
  controls pass their exact positive and negative oracles.
- The known-answer feature vectors and exact-tie fixture above match byte-for-byte.
- Fingerprint or catalog-content mismatch causes an explicit retrieval error rather than silent fallback.
- Retrieved context cannot satisfy the formal verification oracle by itself.

### Retired PFI-005–PFI-007

- No Proof Flow graph row, private trace, failed attempt, repair trajectory, or user content is
  indexed under this Spec.
- A successor may reuse the concepts but shall allocate new requirement IDs and record the
  PFI-005–PFI-007 replacement mapping.

### PFI-008

- The closed parser accepts exactly the added PFI-008 symbols, arities, and inferred
  `real_function|real_sequence` positions and typed binders; it rejects an unknown symbol, direct
  `OMV` application head, free/undeclared/conflicting typed variable, ordinary term variable in a
  typed position, function/sequence sort swap, an index primitive outside `sequence_lambda`, or a
  `sequence_apply` outside that lambda's term body before embedding, retrieval, or seed publication.
- Recorded golden OpenMath fixtures cover: an epsilon-delta-equivalent `continuous_at` proposition,
  a `has_limit_at` proposition, a `converges_to` proposition, the forward sequential-continuity
  preservation law using `sequence_compose`, `apply`, `sequence_apply`, `sequence_lambda`, and a
  typed sequence binder, and closure of continuity/limits/sequences under every registered function
  or sequence construction. Within that lambda, `sequence_apply` accepts only a
  `real_sequence,natural_index` pair and returns a term; a wrong sequence/function or term/index
  sort, or a use outside the lambda term body, fails. Alpha-equivalent typed bindings canonicalize
  identically; a same-shape fixture with a wrong binder sort does not.
- A `continuity-v1` `continuous_on` fixture or seed row is valid only when its collection is exactly
  `setname1:R`; another collection remains valid only for non-PFI-008 generic retrieval and is not
  eligible for this pilot's Lean receipt or evaluation corpus.
- Closure fixtures for `function_div` or `sequence_div` are valid only with the corresponding
  explicit nonzero hypothesis: `apply(g,a) ≠ 0` for pointwise quotient continuity,
  `has_limit_at(g,a,L) ∧ L ≠ 0` for quotient limits, and `converges_to(v,L) ∧ L ≠ 0` for quotient
  sequence convergence. A `continuous_on` quotient row further requires the explicit
  `quant1:forall` real-term hypothesis `∀ vN, apply(g,vN) ≠ 0`, which the pilot printer renders as
  `(∀ (vN : ℝ), ((g vN) ≠ (0 : ℝ)))`. No unconditional division closure card, golden fixture, or
  Lean receipt is eligible for `continuity-v1`.
- The `continuity-v1` release contains a deterministic coverage manifest whose rows are keyed by
  Draft ID and include only: curriculum version fixed to `continuity-v1`, catalog/profile/card
  coverage hashes, coverage objective, independently authored statement hash, OpenMath hash,
  proof-strategy hash, Sketch-steps hash,
  independent-authorship attestation hash, prohibited-source-review attestation hash, and Lean
  receipt hash. The receipt, rather than the catalog, carries the Lean-verifier
  identity/version, verified theorem-artifact hash, and verification time. The manifest must be
  complete and one-to-one for the derived nonempty pilot ID set, equal to the approved child
  catalog, evidence-bundle, and Lean-receipt ID sets, with the exact catalog/profile/card-coverage
  hashes described above, sorted by valid UTF-8 Draft ID,
  canonicalized as no-LF JCS, and signed together with the seed. It contains no Tao text, page
  image, quote, source excerpt, raw model prompt/output, completed Lean source, user data, or
  explanatory prose.
- `coverage_objective` is exactly one of `limit_at`, `sequence_convergence`, `continuity_at`,
  `continuity_on`, `sequential_continuity`, `closure_add_sub_neg`, `closure_mul_scale`,
  `closure_compose`, or `closure_div_nonzero`; the manifest contains every profile-required
  signature. Its immutable recorded evaluation corpus contains, for every manifest card, one
  independently authored Japanese positive query and one independently authored English positive
  query whose exact expected Draft ID is that card, plus one semantic hard-negative query whose
  exact expected result is `no_match`. It rejects a missing/extra/duplicate card evaluation or a
  query whose expected ID differs from its card. The recorded reranker response and its selected
  ordered IDs must match those expectations; a corpus row must never use Tao source material or a
  user query.
- The six pre-PFI-008 governed queries remain a separate immutable regression corpus. Against the
  complete `continuity-v1` generation, each must retain its exact canonical query bytes, ordered
  eight-candidate ID list, selected ordered Draft IDs or `no_match`, and metric inputs; any added
  row that changes one of those recorded outcomes blocks publication rather than silently revising
  the existing retrieval contract.
- Within the closure objectives, the manifest and corpus contain at least one verified row and its
  paired Japanese/English/hard-negative cases for every registered `function_add`, `function_sub`,
  `function_mul`, `function_neg`, `function_scale`, `function_compose`, `function_div`,
  `sequence_add`, `sequence_sub`, `sequence_mul`, `sequence_neg`, `sequence_scale`,
  `sequence_compose`, and `sequence_div` construction. The division rows must include the preceding
  nonzero hypothesis. A coverage row may satisfy more than one construction only when its canonical
  OpenMath contains each named constructor and its Lean wrapper verifies all of their stated
  hypotheses.
- Before manifest hashing, Agent release tooling resolves an authorship-attestation hash against a
  no-LF JCS object with exactly `schema_version,draft_id,canonical_statement_sha256,
  proof_strategy_sha256,sketch_steps_sha256,reviewer_role,reviewed_at,result`, and a source-review
  attestation hash against the same keys plus `review_protocol`. Their schemas are respectively
  `pals.continuity-authorship-attestation.v1` and `pals.continuity-source-review.v1`, their roles
  are respectively `pals_curriculum_author` and `pals_curriculum_reviewer`, their result is exactly
  `original`, and the sole source-review protocol is exactly
  `manual_external_comparison_v1`. It resolves each Lean receipt hash against a no-LF JCS object with exactly
  `schema_version,draft_id,canonical_statement_sha256,openmath_xml_sha256,
  openmath_to_lean_profile,lean_declaration_name,lean_declaration_sha256,
  theorem_artifact_sha256,wrapper_source_sha256,toolchain_manifest_sha256,verified_at,result`.
  `lean_declaration_name` is exactly `Pals.ContinuityV1.<draft_id>` and is the declaration invoked
  by the wrapper; `lean_declaration_sha256` is `sha256:` plus the SHA-256 of the exact UTF-8,
  no-LF canonical Lean target described below (not an unspecified compiler or pretty-printer
  output). The receipt schema is exactly
  `pals.continuity-lean-receipt.v1`, `openmath_to_lean_profile` is exactly
  `pals.openmath-to-lean.continuity-v1`, every displayed hash has the manifest's SHA-256 grammar,
  and result is exactly `verified`.
- The fixed `pals.openmath-to-lean.continuity-v1` profile translates a real function to
  `ℝ → ℝ`, a real sequence to `ℕ → ℝ`, `continuous_at` to `ContinuousAt`, `continuous_on` to
  `ContinuousOn f Set.univ`; in a pilot row its collection argument is exactly `setname1:R`.
  It translates `has_limit_at` to `Filter.Tendsto f (𝓝[≠] a) (𝓝 L)`, and `converges_to` to
  `Filter.Tendsto u Filter.atTop (𝓝 L)`. Its target is the UTF-8, no-LF result of one deterministic,
  fully-parenthesized printer. The templates below use recursively printed placeholders exactly as
  written; each shown ASCII space is emitted once, and no other whitespace is emitted.

  | OpenMath construct | Exact canonical Lean target template |
  |---|---|
  | term `OMV vN`, `OMI i`, `alg1:zero|one` | `vN`, `(i : ℝ)`, `(0 : ℝ)`, `(1 : ℝ)` |
  | `quant1:forall|exists` | `(∀ (vN : ℝ), <body>)`, `(∃ (vN : ℝ), <body>)`, nested left-to-right |
| `relation1:eq|neq` | `(<left> = <right>)`, `(<left> ≠ <right>)` |
| `logic1:true|false|and|or|not|implies` | `True`, `False`, `(<left> ∧ <right>)`, `(<left> ∨ <right>)`, `(¬ <body>)`, `(<left> → <right>)` |
| `arith1:plus|times|minus|unary_minus|divide` | `(<left> + <right>)`, `(<left> * <right>)`, `(<left> - <right>)`, `(- <body>)`, `(<left> / <right>)` |
| term-body `fns1:lambda` with its one pilot declaration | `(fun vN : ℝ => <term>)` |
| `apply(f,x)`, `sequence_apply(u,n)`, `constant_function(c)`, `identity_function` | `(<f> <x>)`, `(<u> <n>)`, `(fun _ : ℝ => <c>)`, `(fun x : ℝ => x)` |
  | `function_add|sub|mul|div(f,g)`, `function_neg(f)`, `function_scale(c,f)`, `function_compose(f,g)` | `(fun x : ℝ => ((<f> x) +|-|*|/ (<g> x)))`, `(fun x : ℝ => (- (<f> x)))`, `(fun x : ℝ => (<c> * (<f> x)))`, `(fun x : ℝ => (<f> (<g> x)))` |
  | `sequence_add|sub|mul|div(u,v)`, `sequence_neg(u)`, `sequence_scale(c,u)`, `sequence_compose(f,u)` | `(fun n : ℕ => ((<u> n) +|-|*|/ (<v> n)))`, `(fun n : ℕ => (- (<u> n)))`, `(fun n : ℕ => (<c> * (<u> n)))`, `(fun n : ℕ => (<f> (<u> n)))` |
| typed function/sequence quantifiers | `(∀ (vN : ℝ → ℝ), <body>)` or `(∃ (vN : ℝ → ℝ), <body>)`; `(∀ (vN : ℕ → ℝ), <body>)` or `(∃ (vN : ℕ → ℝ), <body>)`, nested left-to-right |
  | `sequence_lambda`, `index_zero`, `index_succ`, `index_to_real` | `(fun vN : ℕ => <term>)`, `(0 : ℕ)`, `(Nat.succ <n>)`, `(↑<n> : ℝ)` |
  | `continuous_at(f,a)`, `continuous_on(R,f)`, `has_limit_at(f,a,L)`, `converges_to(u,L)` | `(ContinuousAt <f> <a>)`, `(ContinuousOn <f> Set.univ)`, `(Filter.Tendsto <f> (𝓝[≠] <a>) (𝓝 <L>))`, `(Filter.Tendsto <u> Filter.atTop (𝓝 <L>))` |

  In the two `+|-|*|/` table alternatives, the selected literal operator is the constructor's
  displayed suffix. `OMF`, `set1`, every unlisted logic/relation/arithmetic symbol, every other
  standard or PFI symbol (including `sum|product|map|suchthat`), and every other sort reject in a
  pilot row. No implicit coercion, unparenthesized alternate, or compiler pretty-printing
  participates in the target hash.
- Agent builds a no-network wrapper whose theorem target is the exact profile translation of the
  row's canonical OpenMath and whose source is exactly `import Pals.ContinuityV1.<draft_id>\n`
  followed by `example : <lean_target> := Pals.ContinuityV1.<draft_id>\n`; the wrapper's exact
  UTF-8 source hashes to `wrapper_source_sha256`. Its `lean_target` must hash to
  `lean_declaration_sha256`, so a differently typed declaration cannot satisfy the wrapper.
  During this Agent build only, `theorem_artifact_sha256` identifies a no-follow regular temporary
  Lean module named `Pals.ContinuityV1.<draft_id>` that exports that declaration; the wrapper
  imports this exact module, and the builder hashes it before verifier submission and deletes it
  after receipt generation. The module is never packaged in the worker image, manifest, evidence
  bundle, catalog, or API input. It accepts the receipt only when the PAE-017 verifier compiles that
  wrapper under the toolchain whose `pals.verifier-toolchain-manifest.v1` SHA-256 is
  `toolchain_manifest_sha256`. Thus the successful declaration is bound to the same canonical
  statement/OpenMath hashes as the seed row. Any field not matching its manifest row, profile,
  wrapper target, verifier toolchain, or result; an unknown result; a duplicate Draft ID; or a
  missing receipt fails the release. These evidence objects are build inputs only and are neither
  Draft data nor API/catalog content.
- Each pilot statement, strategy, and Sketch is independently written rather than copied or
  closely paraphrased from Tao. Tao may be used only outside the release inputs as a high-level
  coverage map. A row without a successful PALS Lean-verifier result for its manifest-bound
  theorem-artifact hash, an invalid/duplicate manifest entry, a missing independent source-review
  attestation, or prohibited source bytes fails the complete release before embedding or database
  publication. The review attestation, rather than storing copyrighted source material, is the
  release evidence for the no-copy/no-close-paraphrase rule.
- The source-review attestation is accepted only when its stated result is bound to the exact Draft
  ID plus statement, strategy, and Sketch hashes, has role `pals_curriculum_reviewer`, and is
  included in the Agent-built evidence bundle accepted by the existing PRX signed-worker gate.
  `manual_external_comparison_v1` requires a reviewer other than the content author to freeze the
  three hashed fields, compare them manually with the authorized Tao material only in a local
  out-of-repository workspace, and discard every comparison note, quotation, and source derivative
  before emitting the attestation. `original` means that this review found the statement, strategy,
  and Sketch independently expressed and free of copied text or close paraphrase. The PRX signing
  operator must confirm that this review occurred before it signs the worker image; this existing
  signed-worker authorization is the sole release acceptance root, not a second credential system.
  Because the review is hash-bound, any later content change requires a new review. The artifact
  record contains neither source material nor a reviewer identity and has no expiry-based reuse
  outside that exact content hash tuple.
- The pilot adds rows only through the existing Agent-built signed-worker seed and API atomic
  immutable-generation publication path. It does not create a direct pgvector write, a public or
  admin curation endpoint, a runtime/user ingestion path, a Draft schema column, a Lean-proof
  retrieval field, or an explanation index. Evaluations include Japanese and English independent
  continuity queries plus semantic hard negatives for limits, sequences, pointwise continuity, and
  function-variable closure; they preserve PFI-003's private candidate and reranker contract.

### PFI-010

- A release fixture with 99 otherwise-valid unique continuity IDs fails before embedding, seed
  signing, API generation admission, or database transaction; a 100-ID fixture passes this floor
  only when every existing PFI-008 gate also passes.
- Catalog, successful Lean receipt, signed seed delta, and candidate active-generation ID arrays
  are duplicate-free, bytewise Draft-ID ordered, each have cardinality at least 100, and are exactly
  equal. Any missing/extra/duplicate ID or count disagreement rejects the complete generation.
- The API publishes no partial rows or active pointer on floor failure. A preceding compatible
  generation remains active; a local PFI-009 fixture result never satisfies this acceptance
  criterion.

### PFI-009

- The sole input is
  `pals-agent/specs/continuity-draft-seed-pilot/continuity-v1-catalog.json` at the exact no-LF JCS
  SHA-256 recorded by that approved child Spec. `validate` accepts every distinct card in that
  current catalog together with its coverage object and the catalog's own statement, OpenMath,
  strategy, and ordered Sketch fields. Before `validate` creates a container or relation, it
  validates the profile-complete nonempty derived source set and requires the child's `parent_spec.path` to be
  exactly `specs/proof-flow-index`, its three parent SHA-256 fields to equal the current exact
  `requirements.md`, `design.md`, and `tasks.md` bytes at that path, and that parent's
  `requirements.md` status to be `approved`. `validate` fails on any child/parent status or path/hash
  mismatch, catalog hash/JCS mismatch, duplicate ID, invalid coverage/profile, or any source-set
  mismatch.
- The fixture starts only a separately named local Compose project
  `pals-continuity-pgvector-validation`, using a locally available `pgvector/pgvector:pg16` image,
  one private ephemeral PostgreSQL instance whose data directory is `tmpfs` and whose Docker
  `network_mode` is exactly `none`, and no named volume, host database connection, existing Docker
  network, public network port, password, credential, or secret environment value. Its service
  environment contains exactly `POSTGRES_DB=pals_continuity_validation` and
  `POSTGRES_HOST_AUTH_METHOD=trust`; trust is acceptable only because the service is networkless
  and has no host port. Image absence is a closed local precondition; the fixture never pulls an
  image or contacts a network endpoint.
- From the repository root, the only supported fixture commands are exactly
  `python3 pals-scripts/continuity-pgvector-validation/run.py validate` and
  `python3 pals-scripts/continuity-pgvector-validation/run.py teardown`. The runner accepts
  exactly one of those two modes and no project, Compose-file, database, image, network, provider,
  catalog, or arbitrary-command override.
- The fixture database has exactly one fixture-owned application relation,
  `continuity_validation_cards`; it is not a `pfi_catalog_*` relation and has no active-generation,
  quarantine, manifest, or API-pointer row. It stores each accepted card exactly once with its
  source-field hash and a finite, nonzero, deterministic `vector(3)` test vector. The vector is
  derived reproducibly from the exact card source fields, is labelled
  `deterministic-test-v1`, and is explicitly not an embedding or a semantic representation.
- A successful local run proves only that extension creation, relation DDL, insertion of the exact
  current source set,
  exact source-field/hash preservation, and each stored vector's top-one cosine nearest-neighbour
  query returns its own card ID. It must report the project identity, card count, card IDs,
  vector-kind, and pass/fail counters without printing card text, OpenMath, Sketches, Lean source,
  external source material, credentials, database URL, or provider output.
- The fixture must neither call an embedding provider, an LLM, a network endpoint, nor an
  application API; it must not write an existing local/deployed database, a PFI catalog relation,
  an active pointer, a signed seed/manifest/evidence artifact, source-review/Lean receipt, or any
  repository content other than its explicitly requested local validation implementation/test
  files. It must not be presented as PFI retrieval, a catalog publication, a semantic evaluation,
  or evidence satisfying any PFI-008 release gate.
- The normal completion state leaves only the named, running ephemeral fixture project for
  developer inspection. Its documented teardown removes that project and no other project;
  because data is `tmpfs`, restart/teardown cannot recover or alter fixture rows, and a subsequent
  run must revalidate and reload the complete current source set from the exact catalog.
- `teardown` must remain available after any changed/missing/unapproved child or parent Spec,
  catalog, or input image state. It reads no catalog or parent hash/status and never performs a
  load; it validates only the fixed checked-in Compose path, fixed project name, and the target
  containers' matching Compose-project labels before project-scoped removal. An internal cleanup
  after any partial `validate` failure follows that same restricted teardown path.

## Contracts and Data

- The v1 Draft table has exactly unique stable `id`, `canonical_statement`, `openmath_xml`,
  `proof_strategy`, ordered `sketch_steps`, and `embedding`, with separate compatibility metadata.
  Packaged/model `matched_prompt` is the byte-identical source projection of
  `canonical_statement`, not a seventh field.
- API alone owns the Draft schema, migration, seed import, immutable generation, quarantine ledger,
  active pointer, release admission, and SQL. Agent owns query canonicalization/embedding,
  structural evidence, reranking, and the final internal result. Draft admin remains read-only.
- The internal result and candidate port are read-only. Other than PFI-008's named first-party,
  release-built static curriculum seed, ingestion/curation of custom rows, public retrieval, graph
  indexing, and user-trace retrieval are not approved.
- PFI-009's fixture-only `continuity_validation_cards` relation is outside the PFI Draft catalog
  contract and is reachable only inside its detached Compose project. Its deterministic
  `vector(3)` column is not an `embedding` field and creates no compatibility/fingerprint,
  manifest, active-generation, retrieval-eligibility, or API contract.

## Security and Privacy

- Private questions, artifacts, failed attempts, and traces are prohibited from indexing in this
  slice. Any future handling may inherit `trace-data-governance` only after TDG approval.
- Tao PDF bytes, extracted text, OCR, screenshots, quotations, and close paraphrases are prohibited
  from the repository, coverage manifest, seed, embedding input, external-model prompt, database,
  logs, and traces. The PFI-008 manifest carries verification metadata only; completed
  Lean proof source and user-facing explanations belong to separately approved stores.
- PFI-009 retains only independently authored catalog fields in an ephemeral local database and
  emits content-free run output. It has no credentials, provider authentication, network egress,
  public listener, or durable volume; an attempted non-local target, image pull, or provider call
  fails before the load.
- The worker-secret candidate route accepts only vector/fingerprint bytes, is excluded from every
  public surface, and never exposes database credentials, provider errors, or catalog internals
  beyond the exact bounded candidate response.
- The Draft admin remains read-only and must not be publicly exposed without approved authentication/network controls.

## Internationalization and Accessibility

- OpenMath/OMDoc semantics are language-independent; Japanese or English parser/display defects cannot be hidden by switching to English-only storage.
- Human-readable statements and operations UI require locale and accessibility coverage in focused Specs.

## Observability and Cost

- Measure content-free structuring success, validation failure, `no_match`, Hit@1, Recall@k, MRR,
  false positives, latency, and embedding/provider cost using a governed preserved query corpus.
- PFI-009 emits only local content-free fixture counters (catalog hash prefix, distinct-card count,
  vector-kind, project identity, self-nearest-neighbour pass/fail count, and teardown result).
  These are not product metrics, traces, evaluation data, or cost records.

### Content-Family Release Comparison

Every PFI-008 release candidate shall run a separately stored, independently authored,
content-free `pals.continuity-holdout.v1` JCS corpus. Its queries are not the catalog's Japanese,
English, or hard-negative evaluation queries; it contains no Tao material or user query. Each case
has a unique ID, a profile-signature hash, a locale, a kind of `positive` or `hard_negative`, and
the exact expected Draft ID or `no_match`. Each required profile signature has at least one
Japanese and one English positive holdout plus one hard negative. The evaluator compares the
candidate generation with the immediately preceding compatible immutable generation when one
exists, using the same corpus and recorded embeddings/reranker outputs. It records aggregate and
signature-family `Recall@8`, reranked exact-ID rate, `MRR@4`, hard-negative false-positive rate,
Lean-receipt success rate, candidate and rerank latency, and source-set cardinality.

The candidate must meet every expected outcome for profile signatures newly introduced by that
generation, retain every expected outcome for signatures shared with the prior generation, and
retain the six governed-query results byte-for-byte. A missing prior compatible generation records
`no_prior_generation` rather than fabricating an improvement claim. PFI-009's deterministic test
vectors are never an input to this comparison. The signed release evidence stores only metric
values, generation/profile/catalog hashes, signature hashes, and content-free dispositions.

### Exact content-free provider usage and release-cost evidence

Every successful reranker response requires top-level `usage` to be a duplicate-aware, extra-forbid
object with exactly:

```json
{"input_tokens":1,"input_tokens_details":{"cached_tokens":0},"output_tokens":1,"output_tokens_details":{"reasoning_tokens":0},"total_tokens":2}
```

Each leaf is a JSON integer in `[0,9223372036854775807]`. Missing or extra objects/members, duplicate
keys, booleans, floats, exponent forms, strings, negative values, or larger integers are
`reranker_invalid`. Let `I=input_tokens`, `C=input_tokens_details.cached_tokens`,
`O=output_tokens`, `R=output_tokens_details.reasoning_tokens`, and `T=total_tokens`. Require
`C <= I`, `R <= O`, and `T == I + O`. Normalize exactly:

```text
input_tokens = I
cached_input_tokens = C
uncached_input_tokens = I - C
output_tokens = O
reasoning_output_tokens = R
nonreasoning_output_tokens = O - R
total_tokens = T
```

All subtraction and equality checks use arbitrary-precision integers. Usage is content-free and may
be consumed only by the manual release evidence path; it is absent from the PFI runtime result DTO,
logs, traces, metrics labels, corpus, database rows, and public/private API payloads.

The sole pricing authority for evidence created from `2026-07-27` until a later Spec update is this
embedded immutable snapshot:

```json
{"schema_version":"pals.provider-pricing.v1","snapshot_id":"openai-gpt-5.4-mini-2026-07-27","source_url":"https://developers.openai.com/api/docs/models/gpt-5.4-mini","effective_date":"2026-07-27","currency":"USD","unit":"USD per 1000000 tokens","rates":{"uncached_input":"0.75","cached_input":"0.075","output_including_reasoning":"4.50"}}
```

The official source URL is primary evidence; the exact embedded values, not a mutable live page or
dashboard, are the reproducibility authority for this gate. A price change requires a Spec update
and new snapshot ID before another release evaluation. Reasoning tokens are already included in
`O` and receive no second charge. Let `U=I-C`. Compute with arbitrary-precision integers:

```text
exact_cost_microusd = (30*U + 3*C + 180*O) / 40
cost_microusd_numerator = 30*U + 3*C + 180*O
cost_microusd_denominator = 40
rounded_cost_microusd = floor((cost_microusd_numerator + 20) / 40)
rounded_cost_usd = rounded_cost_microusd / 1000000 rendered as exactly six decimal digits
```

The last two lines implement round-half-up to the nearest micro-USD; no binary floating point,
provider-displayed rounded total, alternate currency, tax, discount, batch, regional, or dashboard
adjustment participates.

For each governed corpus query, Task 10 writes one duplicate-aware extra-forbid external record:

```json
{"schema_version":"pals.draft-reranker-release-evidence.v1","corpus_query_id":"<governed-id>","observed_at":"<RFC3339-UTC>","model":"gpt-5.4-mini-2026-03-17","schema_admitted":true,"outcome":"match|no_match","selected_draft_ids":["<ordered-id>"],"latency_ms":1,"usage":{"input_tokens":1,"cached_input_tokens":0,"uncached_input_tokens":1,"output_tokens":1,"reasoning_output_tokens":0,"nonreasoning_output_tokens":1,"total_tokens":2},"pricing":{"snapshot_id":"openai-gpt-5.4-mini-2026-07-27","effective_date":"2026-07-27","currency":"USD","unit":"USD per 1000000 tokens"},"cost":{"microusd_numerator":"210","microusd_denominator":40,"rounded_microusd":"5","rounded_usd":"0.000005"}}
```

`corpus_query_id` and selected IDs must exist in the immutable governed corpus; `model` and every
pricing member equal the displayed constants; `schema_admitted` is exactly `true`; `match` has one
through four selected IDs and `no_match` has none. No natural statement, OpenMath, prompt, output
text, raw response, response/request ID, header, account, project, user, proof, credential, or
free-form field is permitted. Decimal-string cost integers use exact `0|[1-9][0-9]*`;
`rounded_usd` matches `(0|[1-9][0-9]*)\.[0-9]{6}` and equals the rounded micro-USD value;
`latency_ms` is an integer in `[0,86400000]`; `observed_at` is canonical UTC
`YYYY-MM-DDTHH:MM:SSZ`. The record is encrypted in transit and at rest, readable only by exact roles
`pals_release_operator` and `pals_release_auditor`, retained outside the repository and immutable
corpus until exact expiry `observed_at + 15552000 seconds`, then deleted no later than
`expiry + 86400 seconds`. Release requires the active access, encryption, expiry, and scheduled-
deletion controls; their absence or mismatch blocks release. After expiry, a missed deletion blocks
the next release and requires audited deletion without extending retention. The record is never
copied to training/evaluation datasets, Notion, runtime logs/traces, or a canonical Spec. A
missing/invalid record, pricing mismatch, arithmetic mismatch, retention-control failure, or partial
corpus set blocks release.

## Test Requirements

| Requirement | Test Level | Required Scenarios | Execution Tier |
|---|---|---|---|
| PFI-001–PFI-004 | Unit / property / Postgres integration / golden | Exact namespace/node/attribute/cdbase/binder/seven-sort/C14N grammar; lower free-variable oracle versus closed retrieval gate; prefix/global-namespace invariance and exact source/OCI duplicate/root/descriptor/config/layer/seed provenance; every max/max+1 bound; unique six-field mapping; sole-source 4,096-row no-LF seed manifest and equal seed/active/query counts; complete 48/71-weight feature maps; finite embedding/evidence arithmetic; private candidate route/auth/body/response/deadline/error contract; admitted endpoint/resource/transport/login/role binding; deterministic UTF8/`C` distance/ID eighth-row order; exact recorded reranker request/response parser; closed match/no_match/error DTO and precedence; zero Agent DB capability | PR deterministic / main real PostgreSQL |
| PFI-003–PFI-004 | Retrieval eval | Exact, approximate, wrong strategy, duplicate-ID rejection, profile-valid eight-row corpus, equal-distance eighth-row tie, exact supported-keyword strict provider schema with `maxLength`/`uniqueItems` mutations rejected locally, release-live schema admission, zero-through-four unique reranker selections, invalid/foreign IDs, Japanese adversarial inputs, exact usage allowlist/normalization, pinned USD snapshot, rational cost/rounding, evidence schema, retention/deletion/privacy controls | PR/main recorded contract / release live |
| PFI-001–PFI-004 | Contract / security | Exact internal result; sole private API route and zero public route/alias/proxy/OpenAPI exposure; vector-only request; no Agent DB capability; no indexed user/trace content | Main / release |
| PFI-001, PFI-008 | Unit / property / Lean verifier / golden | All added symbol/arity/sort/index accept/reject fixtures; typed alpha-equivalence; direct-`OMV` and free/conflicting-sort rejection; deterministic no-LF catalog/profile/card-coverage/manifest/evidence-bundle/provenance-label/path/hash/complete-delta seed binding; mechanical `C0` signature expansion, metadata-to-AST realization, derived child-catalog/manifest/evidence/receipt/seed-delta ID equality, profile-signature omission, duplicate novelty/OpenMath, and source-set mismatch rejection; exact one-Japanese/one-English/one-hard-negative evaluation binding for every card; fixed OpenMath-to-Lean target and wrapper/declaration/toolchain binding; original-content prohibited-input scan and external-manual-review acceptance record; manifest-bound Lean verifier success/failure; byte-exact six-governed-query regression; expansion/migration/rollback; Japanese/English continuity retrieval and semantic hard negatives | PR deterministic / main recorded verifier and PostgreSQL |
| PFI-003, PFI-008, PFI-010 | Generation comparison and volume-floor admission | Independent holdout schema and source prohibition; per-signature Japanese/English positive and hard-negative completeness; no-prior-generation disposition; shared-signature non-regression; newly introduced-signature expected outcomes; aggregate and signature-family Recall@8, reranked exact-ID rate, MRR@4, false-positive, Lean-success, latency, and source-set metrics; exact 99-ID rejection, 100-ID acceptance only with equal catalog/receipt/seed/active-generation ID sets, and duplicate/missing/partial-seed/partial-transaction rejection; PFI-009-vector exclusion | Main recorded PostgreSQL/verifier / release admission |
| PFI-009 | Local Compose integration / adversarial | Exact canonical `validate`/`teardown` command and no-override parser; `validate` exact approved child/catalog/profile hash/JCS and complete derived-source-set acceptance; child parent path/current-parent requirements/design/tasks SHA-256/status mutations and changed hash/non-JCS/duplicate/coverage/profile mismatch refusal before startup; local-image/no-pull and detached-project-only checks; resolved-config and running-container exact `network_mode:none`, `tmpfs`, no-volume, no-public-port, and exact no-secret `POSTGRES_DB`/trust environment checks; extension/fixture-only DDL; exact current source hashes; fixed known-answer source-hash and IEEE-754 binary32 deterministic `vector(3)` values; finite/nonzero/unique/noncollinear rejection; one self top-one nearest-neighbour check for every loaded source card; no PFI/application-table/API/provider/network access; content-free output; stale/missing child-parent/catalog state still permits only fixed-label project teardown and partial-validate cleanup; named-project-only teardown and reload from source | Developer-invoked local only; never a PR/main/release gate |

## Quality Gates

- Required PR checks: exact OpenMath grammar/bound/canonicalizer properties, complete feature-key
  known-answer vectors and tie fixtures, recorded reranker contract/golden set, schema/fingerprint
  tests; no network or cost-bearing model call.
- Required main checks: real PostgreSQL/pgvector integration through the exact API candidate port,
  admitted endpoint/resource/transport/session binding, recorded deterministic reranker,
  read-only admin contract, zero Agent DB capability, and API route inventory proving exactly one
  private PFI endpoint and no public PFI endpoint; no cost-bearing model call.
- Nightly checks: deterministic preserved-query structuring/embedding/database evaluation with a
  recorded reranker response; no claim of real-model execution.
- Manual release check: exactly one cost-bearing real reranker execution per governed corpus query,
  exact strict-schema admission without `invalid_json_schema` or equivalent rejection, exact
  selected-ID comparison, compatibility metadata, `no_match`, privacy, migration, release
  eligible-row minimum, latency, exact normalized usage, pinned pricing identity, rational
  micro-USD arithmetic/rounding, closed evidence schema, and retention/deletion evidence. A
  skipped/unavailable real call, schema rejection, missing/unknown/inconsistent usage, price drift,
  arithmetic/schema/privacy/retention failure, or incomplete corpus evidence blocks release.
- PFI-009 local validation is opt-in and may run only through its documented detached-project
  command. It is not a PR, main, nightly, or release quality gate and cannot waive a failed or
  missing PFI-008 gate.

## Rollout, Rollback, and Recovery

- Schema, validator, canonicalizer, or fingerprint changes require a new Agent-built signed seed
  plus an explicit full-row scan, quarantine decision, and compatibility checks. Before opening a
  database transaction, seed validation rejects the complete artifact if it has row 4,097 or any
  row that is non-closed/out-of-profile, whose complete candidate JCS exceeds 16,384 UTF-8 bytes,
  or whose ID is not retrieval-eligible; an invalid seed creates no row or quarantine record.
  After seed validation, migration quarantines every preexisting database row outside the exact new
  seed population and verifies the PRX-bound worker
  child property/seed/layer extraction, admitted database endpoint/resource/transport/session and
  live observations, exact UTF8/`C`, one active-generation eligibility predicate, and release
  minimum-eight admission without truncation.
- PFI-008 publication additionally validates a single complete signed coverage manifest after typed
  validation and canonicalization but before embedding or a database transaction. It verifies every pilot ID exactly once,
  its independent-authorship and prohibited-content checks, and a successful manifest-bound Lean
  verifier result. Failure leaves the previous immutable generation active. The API never receives
  Tao source material, Lean source, or explanatory prose.
- PFI-009 has no migration, publication, pointer switch, or rollback into another database. A
  failed validation tears down only the named detached project; a successful validation may be
  explicitly torn down by the developer and is otherwise discarded on its next container restart
  because the database directory is `tmpfs`.
- Migration fails closed rather than truncating or reactivating quarantined or incompatible records;
  rows, quarantine ledger, fingerprint, manifest, runtime provenance, metadata/count, and readable
  active-generation pointer switch atomically.
- Rollback switches only to a prior immutable generation whose schema, catalog manifest,
  canonicalizer, runtime provenance, and embedding fingerprint all remain mutually compatible.
- Promotion requires the existing REP-005 sole behavior key `cross-repo:proof-flow-index`, the
  existing exclusive parent surface `schema:proof-flow-index`, and exact `spec-ownership: PASS`.
  Agent/API/Draft-admin are affected implementation repositories, not independent normative owners
  or required participant rows for this exclusive parent schema surface. For this REP-005
  ownership-check statement only, API participation adds no separate parent participant row; this
  does not limit the API-owned migration, persistence, SQL, or private route required above.
  `pals-datasets` is uninitialized and is not an
  affected repository or evidence owner in this slice; the parent owns the deterministic corpus
  while the pinned Agent seed is read-only source evidence.
- Immediately after this parent bundle is independently converged and promoted, a different
  independent reviewer must complete PFI post-promotion review on the exact promoted bytes. That
  reviewer may not be the Task 36 convergence reviewer or promotion approver; the independent
  review report records those three non-overlapping review roles without entering PFI release
  artifacts. Here `EXP` means the separate cross-repo
  `proof-explanations-and-clarifications` bundle. Only after both PFI and that exact EXP bundle
  have independently converged, promoted, and passed their own post-promotion reviews may the
  already-draft `pals-agent/specs/proof-explanation-evaluation` bundle import both
  parent-owned contracts without changing preserved observable/runtime semantics, independently
  converge, be explicitly re-promoted, and pass its separate post-promotion review. No later PFI
  review depends on PAE. PAE import or implementation does not start before that acyclic sequence
  completes; PFI Tasks 25--29 start after Task 24a alone.

## Constraints

- This focused bundle never authorizes the incomplete full Proof Flow implementation; that scope
  requires a separately named successor Spec regardless of this bundle's frontmatter status.
- Exact packaged seed count is content inventory, not a stable normative requirement.
- PFI-009 validates pgvector plumbing only; deterministic test-vector proximity must never be
  interpreted as mathematical, lexical, multilingual, structural, or semantic similarity.

## Assumptions

- PostgreSQL/pgvector remains adequate for evaluating the initial retrieval contract; platform selection is not fixed here.

## Deferred Future Scope

A separately named future Spec may define immutable Proof Flow versions, typed entities/edges,
outcome classes, provenance, general curation, deletion lineage, and role-scoped internal retrieval only
after TDG approval. It shall not index raw prompts/model output or treat similarity as verification.

## Open Questions

None for PFI-001–PFI-004, PFI-008, and PFI-009. Deferred future behavior is outside this bundle.

## Definition of Done

- [x] Existing Draft retrieval and future Proof Flow scope are separated with no contradictory schema.
- [x] Every v1 Draft data, evidence, reranker, compatibility, DTO, and no-match decision is resolved.
- [ ] Deterministic, Postgres, live, adversarial, lineage, privacy, migration, and cost tests have exact oracles.
- [ ] PFI-008 typed-profile, original-content, Lean-verification, curriculum-manifest, migration,
  and bilingual continuity-evaluation gates are implemented and pass.
- [ ] PFI-009 detached local pgvector validation loads and self-checks the complete approved
  content-profile catalog
  without accessing any active/application catalog or asserting semantic/release evidence.

## Evidence

- [Proof Flow Vector Index task](https://app.notion.com/p/38972123fc4381ef8f67ff4826ce3ce6) — in progress, not authority.
- [Undergraduate Draft dataset task](https://app.notion.com/p/38772123fc4381009f6ed8066698f322) — in progress, not authority.
- `docs/openmath-omdoc-draft-retrieval.md`
- `pals-agent/README.md`
