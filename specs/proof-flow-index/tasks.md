# Tasks: Proof Flow Index

`tasks.md` is non-normative. This focused bundle never authorizes the incomplete full Proof Flow
implementation; that scope requires a separately named successor Spec.

Explicit trace keys: PFI-001, PFI-002, PFI-003, PFI-004, PFI-005, PFI-006, PFI-007, PFI-008, PFI-009, PFI-010.

## Implementation Plan

- [x] 1. Audit and freeze the focused Draft/OpenMath slice without relying on a historical seed count.
  - Covers: PFI-001–PFI-004
  - Repositories: pals-agent, pals-draft-admin, cross-repo
  - Evidence: `current-implementation-audit.md`, SHA-256
    `80112efea6d42ca4f09025a861c43abc5b572ebcfdfdd2cc803d62ac474526f1`; it records deterministic
    commands, exact path/line evidence and file digests, the uninitialized datasets submodule, and
    every aligned/partial/gap disposition without claiming implementation conformance
  - Verification: six-field schema; exact standard/PALS cdbase URIs; closed XML
    node/child/attribute/namespace grammar; 65,536-byte, 4,096-node, depth-64,
    256-bound-variable, 20,000-code-point, 256-step, exact 4,096-row manifest and eight-row DB
    candidate bounds; exact
    alpha-renaming/shadowing/C14N bytes; exact four-sort function profile; complete structural
    feature-key grammar and 48/71-weight known-answer maps; DB-only `LIMIT 8`, structural evidence,
    and one real PAE draft-role rerank selecting zero through four ordered unique contexts;
    exact runtime-provenance JCS+LF digest; compact sorted seed-manifest SHA-256/count; migration,
    typed no_match, and read-only admin evidence map

- [x] 2. Split unresolved future Proof Flow graph behavior from this focused bundle and retire PFI-005–PFI-007 without reuse.
  - Covers: retired PFI-005–PFI-007
  - Repositories: cross-repo
  - Verification: `SPEC-CHG-2026-07-26-PARENT-GRILL`; no graph/private-trace requirement remains

- [x] 2a. Close the PFI-001–PFI-004 parser, canonicalizer, feature, bound, tie, and migration contracts.
  - Covers: PFI-001–PFI-004
  - Repositories: cross-repo
  - Verification: requirements precede design/tasks; safer limits and current-code differences are
    recorded; six-field/scoring/fingerprint/no-match behavior and retired history are preserved

- [x] 2b. Remediate canonicalization, typing, numeric, DTO, provenance, and promotion-order
  findings, Spec only.
  - Covers: PFI-001–PFI-004
  - Repositories: cross-repo
  - Verification: CPython 3.12.13/rewrite-prefix v3 known bytes and immutable provenance; exact
    term/proposition rules with OMV-head/lambda rejection; finite binary32 vectors and strict
    binary64 scoring/ties; exact match/no_match/error DTO and precedence; expected REP-005 key and
    checker predecessor; requirements -> design -> tasks only, retained `draft`, no code/test/
    inventory edit

- [x] 2c. Remediate focused typing, runtime-provenance, and REP-005 surface findings,
  Spec only.
  - Covers: PFI-001–PFI-004
  - Repositories: cross-repo
  - Verification: requirements remove `arith1:sum|product` and `set1:map|suchthat` rather than
    redefining their standard function/predicate arguments; define the exact
    `pals.draft-retrieval-runtime-provenance.v1` JCS-plus-LF digest subject; preserve the registered
    exclusive parent `schema:proof-flow-index` surface; design/tasks only realize those requirements

- [x] 2d. Remediate fifth-distance tie and seed-schema byte findings, Spec only.
  - Covers: PFI-002–PFI-004
  - Repositories: cross-repo
  - Verification: exact `(cosine_distance ASC,Draft ID ASC)` selection before limit five; unique
    Draft IDs; byte-identical packaged/model `matched_prompt` to storage/response/manifest
    `canonical_statement` mapping; exact no-LF RFC 8785 JCS manifest subject; requirements -> design
    -> tasks only

- [x] 2e. Supersede earlier retrieval and type details with coordinated parent authority.
  - Covers: PFI-001–PFI-004
  - Repositories: cross-repo
  - Verification: four-sort lambda/function profile; exactly one DB-only distance/ID `LIMIT 8`
    query; no runtime seed union or cutoff; structural evidence plus one exact PAE draft-role rerank
    selecting zero through four ordered unique contexts; coordinated PAE draft/import/converge/
    re-promote/post-review dependency; requirements -> design -> tasks only

- [x] 2f. Remediate fresh pre-promotion reproducibility, corpus, and dependency findings, Spec and
  evidence only.
  - Covers: PFI-001–PFI-004
  - Repositories: cross-repo
  - Verification: requirements-first exact 4,096-row manifest; closed retrieval gate with retained
    lower free-variable oracles; UTF8/`C` DB ordering and release minimum eight; exact
    `sysconfig` ElementTree-source and OCI manifest digest subjects; 16,384-byte natural/candidate
    plus 262,144-byte request bounds; fixed prompt/JCS/Responses API/timeout/response parser with
    temperature/seed omitted and no retry/fallback; profile-valid corpus rows and renewed hashes;
    deterministic PR/main versus one cost-bearing release-live gate; API read-only no-public-route
    assertion; Dataset N/A evidence disposition; obsolete threshold telemetry removal; immediate PFI
    post-promotion review before PAE import; retained `draft`; no production/test/status/registry or
    child-Spec edit

- [x] 2g. Close the second fresh pre-promotion response, provenance, resource, and catalog findings,
  Spec only.
  - Covers: PFI-001–PFI-004
  - Repositories: cross-repo
  - Verification: requirements-first exact completed/model-matched one-message Responses envelope;
    512-token/512-byte and 64-character eligible-ID feasibility; no-network content-addressed OCI
    Image Layout extraction of the PRX-signed-worker config and `PFI-BP-001` child property with no
    parent manifest extension; signed PRX database resource plus live PostgreSQL provenance with no
    database-OCI claim; storage-valid versus retrieval-eligible bounds; one immutable active
    generation and six-clause eligibility/count/query predicate;
    requirements -> design -> tasks only, retained `draft`, no implementation/test/status/registry
    or child-Spec edit

- [x] 2h. Close API-exclusive database authority and authenticated live-target binding, Spec only.
  - Covers: PFI-002–PFI-004
  - Repositories: cross-repo
  - Verification: requirements-first API-only schema/migration/active-snapshot/SQL ownership;
    Agent-only runtime canonicalization/embedding/structural/rerank with zero DB capability; exact
    worker-authenticated vector-only private route and bounded response/deadline/error contract;
    admitted PRX environment/endpoint/port/name/resource plus AWS IAM/TLS verify-full or local
    token-verifier login/role/live-session binding; Agent-built signed-worker seed
    file/fingerprint plus no-network safe OCI layer extraction by the API release controller; no
    public endpoint, retry, cache, provider call in API, parent-manifest extension, or fallback;
    requirements -> design -> tasks only, retained `draft`, no implementation/test/status/registry
    or child-Spec edit

- [x] 2i. Close sole-source catalog population, snapshot count, and OCI JSON parser findings,
  Spec only.
  - Covers: PFI-002–PFI-004
  - Repositories: cross-repo
  - Verification: signed-worker seed is the only readable v1 catalog source; exact
    `seed_count == row_count == eligible COUNT(*)`; non-seed prior rows become immutable quarantine
    history and never merge; exact same-ID six-field duplicates create no second row; snapshot and
    candidate DTO carry the seed count; index/manifest/config parsing is duplicate-aware, manifest
    and descriptors have closed schemas, every descriptor size/digest is exact; REP-005 wording is
    limited to participant-row ownership and does not narrow API implementation ownership;
    requirements -> design -> tasks only, retained `draft`, no implementation/test/status/registry
    or child-Spec edit

- [x] 2j. Restore strict provider-schema compatibility and reopen convergence, Spec only.
  - Covers: PFI-003–PFI-004
  - Repositories: cross-repo
  - Verification: `SPEC-CHG-2026-07-26-PFI-STRICT-SCHEMA-COMPATIBILITY`; requirements first remove
    unsupported provider keywords `maxLength` and `uniqueItems` while exact `pattern` and
    `maxItems` plus the duplicate-aware application parser preserve the complete 64-character,
    zero-through-four, unique, ordered, supplied-ID result contract; deterministic tests reject
    every unsupported schema-key mutation before network; release-live evidence proves exact schema
    admission and treats `invalid_json_schema` or equivalent rejection as release-blocking; design
    and tasks realize only that restoration; requirements/index return to draft; no product,
    product-test, child-Spec, registry, stage, or commit edit

- [ ] 3. Generate a separately named future Proof Flow graph Spec only when that scope is approved.
  - Covers: successor IDs replacing retired PFI-005–PFI-007
  - Repositories: cross-repo
  - Verification: new requirements/design/tasks, TDG dependency, ownership registration, and no raw
    prompt/model-output indexing

- [x] 4. Historical exact multilingual retrieval/evaluation corpus snapshot, superseded for source
  inventory by Task 17.
  - Covers: PFI-001, PFI-003, PFI-004
  - Repositories: cross-repo; pals-agent is read-only source evidence; pals-datasets is N/A and
    uninitialized
  - Verification: `evaluation-corpus.json`, SHA-256
    `896047cb7bac49603235f9f7428a4d88aa8063b7859d2b52cc71ffb6c172a5cf`, and
    `evaluation-corpus.md`, SHA-256
    `e3a6e6d2f3ff3a70e0a2bf6c4f3a96e53a78c0a58105d32ef9df7ba570a40c8b`;
    six English/Japanese query IDs record natural statements, canonical OpenMath, exact eight-row
    candidate order, expected zero-through-four ordered Draft IDs/no_match, exact reranker identity,
    metric formulas/oracles, hard negatives, false-positive adjudication, and reproducible commands.
    Every candidate is a profile-valid closed row under the pinned seed snapshot. The fixture
    explicitly records zero observed real reranker executions and is not production data

- [ ] 5a. Generate, independently converge, and approve the repository-owning PFI child Specs.
  - Covers: PFI-001–PFI-004
  - Repositories: pals-agent, pals-api, pals-draft-admin
  - Depends on: Task 20
  - Verification: `pals-agent/specs/proof-flow-index`, `pals-api/specs/proof-flow-index`, and
    `pals-draft-admin/specs/proof-flow-index` import this approved parent without changing it;
    API child closes route/auth/DTO, PJR typed-pool/session/ACL, schema/migration/active-snapshot/
    quarantine/SQL, OCI seed extraction, COMMIT/recovery, and route-inventory details; Agent child
    closes build/runtime canonicalization/embedding/client/evidence/rerank and zero-DB capability;
    Draft-admin child is read-only; each is independently `IMPLEMENTATION READY`, status-only
    promoted, and post-promotion reviewed before any test or implementation edit

- [ ] 5b. Generate the requirement-to-assertion matrix and execute it red before implementation.
  - Covers: PFI-001–PFI-004
  - Repositories: pals-agent, pals-api, pals-draft-admin
  - Depends on: Task 5a
  - Verification: every acceptance criterion has a stable assertion ID; tests fail for the expected
    missing behavior, including lower free-variable versus closed retrieval, every worker-child/
    seed-layer/admitted-endpoint/resource/transport/session/live-observation/manifest/resource
    boundary, private-route auth/request/response/deadline/error precedence,
    active-generation eligibility/count/query identity, UTF8/`C` API-only DB LIMIT 8 and release
    minimum, exact supported-keyword provider schema and `maxLength`/`uniqueItems`/arbitrary-key
    rejection before network, exact recorded reranker completion/model/message/output-text/
    0..4/foreign/duplicate IDs, exact usage allowlist/normalization, pinned pricing, rational
    cost/rounding, closed evidence/access/retention/deletion/privacy, zero Agent DB capability, one
    private/no-public-route assertion, closed DTO/errors, and no runtime seed union or deterministic
    cutoff. The matrix also proves all twelve direct `OMV` application heads plus every nested
    function-consuming position reject, the exact nine named source IDs are incompatible, removing
    only those IDs yields exactly 31 rows, none of the six governed query candidate/selection lists
    contains an excluded ID, and stale corpus source count/hash metadata fails.

- [x] 5. Superseded without execution by the concrete post-approval Tasks 6–9.
  - Covers: PFI-001–PFI-004
  - Repositories: cross-repo
  - Verification: completed history records only task decomposition; no implementation or test was
    generated or executed by this Spec update

- [ ] 6. Before rollout, scan, quarantine, and atomically migrate the Draft catalog.
  - Covers: PFI-001, PFI-002, PFI-004
  - Repositories: pals-api; pals-agent owns the pre-image build artifact only
  - Depends on: Task 8
  - Verification: Agent release tooling packages exact canonicalized/embedded sole-source seed rows
    and fingerprint inside the admitted signed worker image; API safely extracts and validates that
    exact artifact, scans every seed and preexisting row against exact grammar and limits, blocks
    invalid seed rows, retains every non-seed prior row only as immutable quarantine history, and
    atomically moves exact seed rows/
    quarantine ledger/runtime provenance/fingerprint/manifest/count/active-generation pointer;
    a seed candidate JCS above 16,384 bytes, an ineligible seed ID, row 4,097, or any other invalid
    seed condition rejects the complete artifact before a database transaction and creates no row
    or quarantine record; invalid worker child property/OCI layer/seed file,
    admitted endpoint/resource/transport/session/
    live-observation mismatch, non-UTF8/`C`, any seed/row/eligible-count inequality, count/query
    drift, or release eligible count below eight blocks; partial failure exposes no mixed readable
    catalog

- [ ] 7. After approval, implement the bounded focused validator/canonicalizer and candidate gate.
  - Covers: PFI-001–PFI-004
  - Repositories: pals-agent, pals-api
  - Depends on: Task 5b
  - Verification: exact namespace/node/attribute/cdbase/binder/C14N/feature grammar and every
    lower/free versus closed-retrieval, four-sort/function-position/prefix/provenance rule, exact
    API private-route/auth/DTO/deadline/error and admitted DB connection/session binding,
    UTF8/`C` distance/ID eighth-tie order,
    unique six-field mapping, no-LF JCS seed manifest, runtime-provenance JCS+LF digest, exact
    DTO/error precedence, finite vector/binary64 rule, and every max/max+1 bound are enforced before
    embedding/evidence scoring/provider call; implement the exact PAE draft-role prompt/JCS/
    Responses-API/90-second/supported-schema-admission/completed-model-message response-parser
    boundary returning zero through four ordered unique contexts; require exact content-free usage,
    normalize cached/uncached input and reasoning/non-reasoning output counts, and implement the
    pinned-pricing arbitrary-precision release-cost/evidence/access/retention/deletion path; API
    alone owns
    persistence/migration/one-query active-generation
    selection; Agent has zero DB capability; no runtime seed union, deterministic cutoff,
    truncation, retry, cache, or fallback. Enforce declared sorts in every function-consuming
    position, remove exactly the nine requirements-named ineligible source rows without replacement,
    and publish no seed artifact from any pre-remediation or otherwise invalid input.

- [ ] 8. Make the approved assertion matrix green and refactor without changing behavior.
  - Covers: PFI-001–PFI-004
  - Repositories: pals-agent, pals-api, pals-draft-admin
  - Depends on: Task 7
  - Verification: complete 48/71-weight feature maps, alpha/shadow/free-variable cases,
    OMV-head/sort/function-position rejection, prefix/global-namespace known bytes,
    runtime-provenance OCI-layout/index/manifest/config duplicate/root/size/digest,
    layer/seed/path/symlink/descriptor/child-label/source/
    PRX-environment/endpoint/resource/transport/session/live-DB/preimage/newline/digest mutations,
    private-route auth/body/response/deadline/error and zero-Agent-DB-capability mutations, finite/NaN/zero vector,
    active-generation eligibility/count/query drift, UTF8/`C`
    eighth-distance tie, DB-only query and recorded reranker request/body/schema-keyword/
    timeout/completion/model/message/content/text envelope/0..4/foreign/duplicate-ID rejection;
    usage missing/extra/duplicate/type/range/equality mutations; pricing identity/rate/effective-
    date/currency/unit mutations; rational arithmetic/half-up/string-rendering boundaries;
    evidence schema/corpus/access/encryption/expiry/deletion/privacy mutations;
    matched_prompt/canonical_statement and JCS escaping/newline mutations; all storage/eligible-ID/
    candidate/request/response aggregate boundaries, attribute rejection, 4,096/4,097 manifest, API
    one-private/no-public route inventory, closed DTO/error mutations, migration/rollback, and typed
    no_match. Regenerate the exact 31-row seed, no-LF manifest, fingerprint-bound provenance, and
    OCI evidence; update only corpus source count/hash metadata; prove the six query IDs, all 48
    ordered candidate slots, expected selections, and metrics remain byte-for-byte unchanged.

- [ ] 9. Update repository documentation and content-free resource-overflow observability.
  - Covers: PFI-001–PFI-004
  - Repositories: pals-agent, pals-api, pals-draft-admin
  - Depends on: Tasks 7–8
  - Verification: docs expose the focused contract without promoting implementation evidence to
    authority; API docs expose only the private candidate port and no public PFI route; Agent docs
    expose no DB configuration/capability; metrics use only closed non-content error classes and
    bounded counts and contain no undefined relevance-threshold telemetry; release operations
    document access limited to `pals_release_operator|pals_release_auditor`, expiry exactly
    15,552,000 seconds after `observed_at`, scheduled deletion within 86,400 seconds after expiry,
    overdue-record blocking, and the price-snapshot update procedure without copying records into
    the repository or corpus. Documentation records that the nine removed rows were rejected rather
    than semantically rewritten and that exact packaged count remains non-normative.

- [ ] 10. Run the sole cost-bearing release-live retrieval evaluation.
  - Covers: PFI-003–PFI-004
  - Repositories: pals-agent, pals-api
  - Depends on: Tasks 6 and 9
  - Verification: admitted PostgreSQL/pgvector reports at least eight eligible rows; each governed
    corpus query performs exactly one fixed-contract real OpenAI reranker call with zero retries
    and proves the exact strict schema was admitted without `invalid_json_schema` or equivalent
    rejection; require the exact usage object and normalized counts; calculate cost from
    `openai-gpt-5.4-mini-2026-07-27` using the exact arbitrary-precision rational/half-up contract;
    write one closed content-free external evidence record per corpus query with encryption, exact
    `pals_release_operator|pals_release_auditor` access, expiry at `observed_at + 15,552,000`
    seconds, and scheduled deletion within 86,400 seconds after expiry. Missing/unknown/inconsistent
    usage, pricing drift, arithmetic/schema/privacy/retention failure, overdue retained evidence,
    incomplete corpus evidence, unavailable provider, request/identity drift, unexpected IDs, or
    metric failure blocks release and never rewrites the corpus

- [x] 11. Remove persisted specification-review invocation labels and results without changing the
  PFI contract.
  - Covers: PFI-001–PFI-004
  - Repositories: cross-repo
  - Verification: substantive remediations remain traceable; no review verdict, severity counter,
    reviewer identity, reviewed-file hash, fingerprint, or invocation ledger remains in the bundle

- [x] 15. Close content-free live usage and reproducible release-cost evidence before Task 12.
  - Covers: PFI-003–PFI-004
  - Repositories: cross-repo
  - Change ID: `SPEC-CHG-2026-07-27-PFI-USAGE-COST-EVIDENCE`
  - Verification: requirements first define the exact duplicate-aware extra-forbid Responses usage
    object, bounded integer/equality rules, cached/uncached and reasoning/non-reasoning normalization,
    pinned official-source USD-per-million snapshot/effective date, arbitrary-precision rational
    micro-USD calculation, half-up rounding, exact evidence schema, exact-role access/encryption,
    15,552,000-second retention, deletion within 86,400 seconds, and prohibited content; design
    realizes only that contract;
    tasks add Red/Green/docs/release evidence work; no review invocation result/count/hash/verdict,
    product code, product test, child Spec, status/index, registry, Notion, stage, commit, rollout,
    rollback, or recovery mutation

- [x] 16. Make the root authority description phase-neutral and close the exact promotion inverse,
  Spec only.
  - Covers: PFI-001–PFI-004; lifecycle metadata only
  - Repositories: cross-repo
  - Change ID: `SPEC-CHG-2026-07-27-PFI-PROMOTION-SURFACES`
  - Verification: the root row description is status-neutral; promotion changes only requirements
    frontmatter `status: draft` to `status: approved` and the `proof-flow-index` row Status cell
    `draft` to `approved`; applying the inverse reproduces the reviewed candidate requirements and
    index hashes exactly; every other byte and all behavior remain unchanged

- [x] 17. Restore seed function-sort conformance requirements-first, Spec only.
  - Covers: PFI-001–PFI-004
  - Repositories: cross-repo
  - Change ID: `SPEC-CHG-2026-07-27-PFI-SEED-FUNCTION-SORT-CONFORMANCE`
  - Verification: requirements and root index return to `draft`; requirements name the exact nine
    already-ineligible IDs, the 31-row remainder, unchanged six-query corpus outcomes, and the
    no-synthetic-replacement rule; design and tasks project only that restoration. No product,
    test, source-seed, corpus, child-Spec, registry, generated, stage, commit, or runtime byte is
    changed by this authoring task.

- [x] 18. Run fresh independent convergence on the exact current draft parent bundle and index.
  - Covers: PFI-001–PFI-004
  - Repositories: cross-repo
  - Depends on: Task 17
  - Verification: exact authority/ownership/traceability and the nine-ID restoration return
    `IMPLEMENTATION READY`, CRITICAL=0, HIGH=0, and no material open question; evidence is external.

- [x] 19. Publish only the exact two-surface status promotion.
  - Covers: PFI-001–PFI-004
  - Repositories: cross-repo
  - Depends on: Task 18
  - Verification: change only requirements frontmatter and the root index Status cell from `draft`
    to `approved`, prove the exact inverse, then publish only this completion marker.

- [x] 20. Run a distinct promoted-byte review.
  - Covers: PFI-001–PFI-004
  - Repositories: cross-repo
  - Depends on: Task 19
  - Verification: a reviewer distinct from Task 18 returns `IMPLEMENTATION READY`, CRITICAL=0,
    HIGH=0, and no material open question. Only its inverse-proved completion marker may then be
    published; every other edit restarts Task 18.

- [ ] 12. Historical prior-revision `$sdd-review-spec`; superseded by Tasks 17–20.
  - Covers: PFI-001–PFI-004
  - Repositories: cross-repo
  - Depends on: Tasks 1, 2, 2a–2j, 4, 11, 15, and 16; REP-005 inventory contains sole key
    `cross-repo:proof-flow-index` and exclusive parent surface `schema:proof-flow-index`, and the
    unmodified ownership checker returns exact `spec-ownership: PASS`
  - Verification: the invocation-local report returns `IMPLEMENTATION READY`, P0=0, P1=0, and no
    material open question; the result is not written into this bundle. This checkbox is a fixed
    unchecked candidate-byte marker and is not edited when the external report completes.

- [ ] 13. Historical prior-revision publication; superseded by Tasks 17–20. Publish the exact reviewed candidate by changing only requirements frontmatter and the
  parent index row Status cell from `draft` to `approved`.
  - Covers: PFI-001–PFI-004
  - Repositories: cross-repo
  - Depends on: the successful external Task 12 report; Task 12's fixed checkbox remains unchecked
  - Verification: change exactly requirements frontmatter `status: draft` to `status: approved`
    and the `proof-flow-index` index-row Status cell `draft` to `approved`; the inverse reproduces
    the reviewed candidate requirements and index hashes exactly; the row description,
    requirements body, design, tasks, and every other canonical byte remain unchanged. This
    checkbox is also a fixed unchecked marker; completion is the exact published projection and its
    external operation evidence.

- [ ] 14. Historical prior-revision post-review; superseded by Tasks 17–20. Run a distinct independent `$sdd-review-spec` against the exact published bundle.
  - Covers: PFI-001–PFI-004
  - Repositories: cross-repo
  - Depends on: the exact Task 13 published projection and external operation evidence; Tasks 12
    and 13 remain unchecked fixed markers
  - Verification: the invocation-local report returns `IMPLEMENTATION READY`, P0=0, P1=0, and no
    material open question; any material edit restarts Task 12. After EXP independently completes
    its own promotion/post-review, already-draft PAE may import both parent contracts and run its
    own convergence/promotion/post-review; PFI has no later dependency on PAE. This checkbox remains
    an unchecked fixed published-byte marker; the review result exists only in its external report.

## Traceability Check

- [x] Every candidate requirement has design coverage.
- [x] Current-slice audit and material decisions precede implementation.
- [x] No task treats retrieval as verification.
- [x] Review-invocation details are report-only.
- [x] Historical Tasks 18–20 revalidated and published the pre-PFI-008 seed-conformance
  restoration; Tasks 21–29 own all subsequent publication work.

## Typed Continuity and Curriculum-Seed Expansion

The exact-31 restoration assertions in Tasks 17--20 are completed historical evidence for the
pre-PFI-008 generation. They remain unchanged history; they do not authorize a new seed and are
superseded for subsequent publication by Tasks 21--29.

- [x] 21. Define the typed continuity profile and static curriculum-seed boundary, Spec only.
  - Covers: PFI-001, PFI-002, PFI-008
  - Repositories: cross-repo
  - Change ID: `SPEC-CHG-2026-08-01-PFI-TYPED-CONTINUITY-SEED`
  - Verification: requirements first define exact new symbols, pilot single-argument lambda arity,
    typed sort unification, complete-delta static-manifest fields, canonical Lean target/receipt,
    independent-authorship/manual-source-review/prohibited-source gates, and atomic-generation rule;
    design realizes only those requirements; this task adds no code, seed, manifest, child-Spec,
    test, database, Notion, stage, or commit edit.

- [x] 21a. Complete the typed real-sequence evaluation form, Spec only.
  - Covers: PFI-001, PFI-002, PFI-008
  - Repositories: cross-repo
  - Change ID: `SPEC-CHG-2026-08-01-PFI-SEQUENCE-EVALUATION`
  - Verification: requirements first record the missing `u(n)` representation and define exactly
    `pals1:sequence_apply(real_sequence,natural_index) -> term` inside only a `continuity-v1`
    `sequence_lambda` term body, its forward-only sequential-continuity interpretation, and
    canonical Lean target; design realizes only this typed form; this task adds no code, seed,
    manifest, child-Spec, test, database, Notion, stage, or commit edit.

- [x] 22. Independently converge and promote the pre-sequence-evaluation PFI-008 parent candidate.
  - Covers: PFI-001, PFI-002, PFI-008
  - Repositories: cross-repo
  - Depends on: Task 21
  - Verification: historical external evidence recorded `IMPLEMENTATION READY`, CRITICAL=0,
    HIGH=0, and no material open question, followed by status promotion and a distinct
    post-promotion review. That evidence applies only to the bytes preceding Task 21a and cannot
    authorize child, test, seed, or runtime work for the amended grammar.

- [ ] 22a. Historical pre-22-card convergence, promotion, and post-review of the amended PFI parent candidate.
  - Covers: PFI-001, PFI-002, PFI-008, PFI-009
  - Repositories: cross-repo
  - Depends on: Tasks 21, 21a, and 30
  - Verification: a fresh independent analysis reports `IMPLEMENTATION READY`, CRITICAL=0,
    HIGH=0, and no material open question for the exact PFI-001--PFI-009 bytes; only then may the
    one parent status surface change from `draft` to `approved`, followed by a post-promotion
    reviewer distinct from both the convergence reviewer and promotion approver. Historical
    PFI-008 review evidence does not authorize the PFI-009-amended bytes. Before that result, no
    child, test, seed, fixture, Docker interaction, or runtime work is authorized; it also does not
    authorize the later 22-card amendment.

- [ ] 23. Create and maintain the separate draft content-family
  `continuity-draft-seed-pilot` curriculum Spec.
  - Covers: PFI-008
  - Repositories: cross-repo, pals-agent
  - Depends on: Task 38's promoted/post-reviewed v4 parent contract.
  - Verification: the child-owning draft curriculum Spec defines the `continuity-v1` original content
    coverage profile spanning
    limits, real sequences, pointwise continuity, sequential continuity, and closure laws including
    required nonzero hypotheses for division; exact
    independently authored Draft IDs/statements/OpenMath/strategies/Sketches; Lean target and
    verifier evidence; the closed nine-objective and every-constructor matrix with paired
    Japanese/English expected-ID queries and hard negatives; source-prohibition review; rollback;
    and a PFI-008 manifest projection without duplicating PFI's catalog/API contract. The child
    catalog, manifest, evidence bundle, Lean receipts, and seed delta have the same derived ID set;
    profile-signature omission, duplicate novelty/OpenMath, and any set mismatch reject before embedding.
    It cannot status-promote or admit its companion until the later CDS Task 14 C14N reapproval;
    that task is the sole curriculum-catalog child approval gate.

- [ ] 24a. Reopen, synchronize, independently converge, promote, and post-review all affected
  repository-owned PFI child Specs.
  - Covers: PFI-001, PFI-002, PFI-003, PFI-004, PFI-008
  - Repositories: pals-agent, pals-api, pals-draft-admin, cross-repo
  - Depends on: Task 23 and the completed CDS Task 14 C14N companion reapproval.
  - Verification: Agent child owns typed validation, complete-delta
    manifest/evidence-bundle/canonical-Lean-target gates, seed packaging, and no-DB capability;
    API child owns complete-generation manifest/evidence admission with no new route; Draft-admin
    remains read-only. Each exact parent-hash import is independently `IMPLEMENTATION READY`,
    status-promoted, and post-reviewed before code or test changes, except the separate synthetic-
    input-only C14N bootstrap in Task 24c.

- [ ] 24b. Independently synchronize the behavior-preserving PAE imports.
  - Covers: PFI-001, PFI-002, PFI-003, PFI-004
  - Repositories: pals-agent, cross-repo
  - Depends on: Task 36 and the separately completed
    `proof-explanations-and-clarifications` (EXP) convergence/promotion/post-review gate
  - Verification: the PAE import pins the exact independently approved/post-reviewed PFI and EXP
    contracts, preserves retrieval-versus-verification separation, independently converges,
    status-promotes, and post-reviews. It is not a predecessor for Tasks 25--29.

- [ ] 24c. Implement and verify the synthetic-input-only C14N canonicalizer bootstrap.
  - Covers: PFI-001, PFI-008
  - Repositories: pals-agent
  - Depends on: Task 38 and the separately converged/promoted/post-reviewed Agent C14N-only child
    import.
  - Verification: Red/Green tests cover the exact seven typed sorts, binders, scope, C14N v4 bytes,
    and fixed two-member novelty JCS preimage using only in-memory synthetic/golden XML. The bootstrap
    neither opens the curriculum companion nor constructs a card projection/Lean input/seed/evidence,
    and has no embedding, network, image, database, API, or runtime-retrieval operation. Its only
    downstream consumer before Task 24a is the child C14N identity check needed for reapproval.

- [ ] 25. Generate the PFI-008/PFI-010 requirement-to-assertion matrix and execute it red.
  - Covers: PFI-001, PFI-002, PFI-008, PFI-010
  - Repositories: pals-agent, pals-api
  - Depends on: Task 24a, which is permitted only after Task 24c and CDS Task 14 complete.
  - Verification: stable assertions cover every added symbol/arity/sort, typed-binder and
    sequence-lambda alpha-equivalence, all direct-`OMV`/free/conflicting-sort/index rejections,
    JCS manifest/evidence-bundle bytes/completeness/provenance-label/path/hash/complete-delta seed
    binding, mechanical content-profile/`C0`/AST-realization and exact sorted-profile golden JCS,
    explicit function-to-sequence operator-map expansion, exact closed theorem-binder prefix and
    residual-shape matching, free/extra/vacuous binder rejection except the required constant-
    sequence index and exact global-division nonzero quantifier, role-specific premise/binder
    connection, degenerate binary/compose rejection, and per-card evaluation binding,
    content-profile/catalog/manifest/evidence/receipt/seed-delta ID equality with profile omission,
    duplicate novelty/OpenMath, and source-set mismatch rejection, five-field base preservation plus full-generation re-embedding under the signed
    fingerprint, canonical OpenMath-to-Lean target/wrapper/declaration/toolchain binding and
    source-prohibition/manual-external-review/Lean-verification failures, byte-exact six-governed-
    query regression, no direct database write, complete
    generation admission/rollback, exact 99-row rejection, 100-row acceptance, complete
    catalog/receipt/seed/active-generation ID-set equality, independent-holdout generation comparison, nine-objective/
    every-constructor bilingual semantic retrieval, and hard negatives.

- [ ] 26. Implement the typed profile, manifest/volume gates, and at least 100 original continuity rows.
  - Covers: PFI-001, PFI-002, PFI-008, PFI-010
  - Repositories: pals-agent, pals-api
  - Depends on: Task 25 and its completed CDS Task 14 predecessor.
  - Verification: work red-green-refactor against Task 25; Agent produces no Tao-derived input or
    raw model output, verifies every manifest-bound theorem in Lean before embedding, emits one
    signed static seed, and API admits only the complete compatible immutable generation with no
    schema column, public endpoint, admin write path, or Agent database capability.

- [ ] 27. Make PFI-008/PFI-010 assertions green and execute recorded integration evaluation.
  - Covers: PFI-001, PFI-002, PFI-003, PFI-004, PFI-008, PFI-010
  - Repositories: pals-agent, pals-api, pals-draft-admin
  - Depends on: Task 26
  - Verification: deterministic/recorded Lean and retrieval fixtures pass; PostgreSQL/pgvector
    integration proves one active compatible generation with at least 100 rows, no partial publication, and byte-exact
    preservation of each existing governed-query candidate/selection outcome; independent-holdout
    comparison records per-signature retrieval/rerank/negative/Lean/latency metrics; the paired
    Japanese and English original queries cover each content-profile card and required semantic
    signature, while their hard negatives reject semantic near misses;
    no new live model call is required.

- [ ] 28. Publish operational documentation and content-free observability for the pilot.
  - Covers: PFI-008
  - Repositories: pals-agent, pals-api, pals-draft-admin
  - Depends on: Task 27
  - Verification: documentation states the original-content boundary, static release path,
    verification-only manifest metadata, rollback, no-public-write rule, and the independent
    prior-generation comparison protocol. Metrics record only bounded non-content classes,
    coverage-signature hashes, verifier outcome, catalog generation, and cost-free evaluation
    outcomes.

- [ ] 29. Perform release admission and rollback rehearsal for the pilot.
  - Covers: PFI-002, PFI-004, PFI-008, PFI-010
  - Repositories: pals-agent, pals-api
  - Depends on: Task 28
  - Verification: a release candidate demonstrates exact derived child/manifest/evidence/receipt/seed
    compatibility, successful full scan, required holdout comparison disposition and metrics, atomic
    pointer switch, recorded bilingual evaluation, and rollback to a mutually
    compatible immutable generation. Any missing source/verification/manifest/evaluation evidence
    blocks release without modifying the active catalog.

- [x] 30. Specify the detached local continuity pgvector validation boundary, Spec only.
  - Covers: PFI-009
  - Repositories: cross-repo, pals-scripts
  - Change ID: `SPEC-CHG-2026-08-01-PFI-CONTINUITY-LOCAL-PGVECTOR-VALIDATION`
  - Verification: requirements first added a fixture-only nine-card, exact-catalog, tmpfs/no-network/
    no-active-catalog contract and measurable DDL/load/self-nearest-neighbour oracles; design
    realizes only the detached project and deterministic non-semantic vector mechanics; this task
    adds no implementation, Docker state, seed, manifest, database, child-Spec, stage, or commit.

- [ ] 30a. Confirm PFI-009 implementation readiness after content-family whole-parent promotion.
  - Covers: PFI-009
  - Repositories: cross-repo, pals-scripts
  - Depends on: Tasks 38 and 30
  - Verification: confirm that the exact parent bytes which Task 38 independently converged,
    promoted, and post-reviewed include PFI-009's detached-fixture contract. This task changes no
    status and cannot independently promote PFI-009 or satisfy, replace, or advance PFI-008
    Tasks 24--29.

- [ ] 31. Resynchronize and independently reapprove the continuity child catalog import for
  detached validation.
  - Covers: PFI-009
  - Repositories: pals-agent, cross-repo
  - Depends on: Tasks 23, 30a, and completed CDS Task 14 C14N companion reapproval.
  - Verification: the child imports the exact promoted parent triple and explicitly permits its
    hash-pinned catalog as read-only input to the parent-owned PFI-009 fixture only. It remains
    non-owning of database/API/runtime behaviour and does not claim release evidence. Its own
    requirements-first convergence, promotion, and distinct post-promotion review pass before any
    local load implementation reads the catalog.

- [ ] 32. Implement the fixture and deterministic local integration tests.
  - Covers: PFI-009
  - Repositories: pals-scripts
  - Depends on: Task 31
  - Verification: the documented fixed-project runner rejects every catalog/image/isolation
    precondition, including any noncanonical command/argument and every current-parent triple
    path/hash/status mutation, before Docker mutation; it creates only the configured
    tmpfs/networkless/no-port/no-secret fixture,
    loads every current source-hashed row with known-answer IEEE-754 binary32
    `deterministic-test-v1` `vector(3)` values, rejects non-finite/zero/duplicate/collinear
    vectors, checks every loaded row's self nearest-neighbour query, emits content-free output, and its
    teardown cannot target another Compose project or database. Mutated/missing child-parent-
    catalog/image inputs block `validate` but leave the exact project-label teardown usable; every
    partial-validation failure runs only that cleanup path.

- [ ] 33. Execute one developer-invoked local validation and teardown rehearsal.
  - Covers: PFI-009
  - Repositories: pals-scripts
  - Depends on: Task 32
  - Verification: from the repository root, run exactly
    `python3 pals-scripts/continuity-pgvector-validation/run.py validate`; with the locally cached
    image it reports the approved catalog hash, its derived sorted IDs, and one self-nearest-neighbour
    successes, and no provider/network/API/catalog generation interaction. Then run exactly
    `python3 pals-scripts/continuity-pgvector-validation/run.py teardown`, which removes only the
    named detached project. The evidence is content-free and is not a PFI-008 release, retrieval,
    semantic, Lean, or source-review claim.

- [x] 34. Historical: expand the continuity-v1 candidate catalog contract from nine overloaded cards to 22
  finer-grained cards, Spec only.
  - Covers: PFI-008, PFI-009
  - Repositories: cross-repo, pals-agent, pals-scripts
  - Change ID: `SPEC-CHG-2026-08-04-PFI-CONTINUITY-CATALOG-EXPANSION`
  - Verification: requirements first retain PFI-008's nine objectives, closed profile, proof,
    review, release, and rollback gates while adding exact 22-ID complete-delta admission and
    PFI-009's detached-fixture cardinality/22-row validation oracles; design/tasks realize no code, seed, catalog, manifest,
    evidence, database, Docker, status, stage, or commit change.

- [ ] 35. Historical: independently converge, promote, and post-review the 22-card PFI parent amendment.
  - Covers: PFI-008, PFI-009
  - Repositories: cross-repo
  - Depends on: Task 34
  - Verification: this historical predecessor required a fresh independent analysis reporting `IMPLEMENTATION READY`, Critical/High 0,
    and no material open question; only then may the parent requirements and root-index status be
    promoted, followed by a distinct post-promotion review. No child catalog, test, fixture,
    seed, evidence, Lean, or release implementation was authorized first.

- [ ] 36. Converge, promote, and post-review the content-family PFI parent amendment.
  - Covers: PFI-008, PFI-009
  - Repositories: cross-repo
  - Depends on: the requirements-first content-family update in this bundle; Task 35 is a
    non-blocking historical marker for the superseded fixed-cardinality revision.
  - Change ID: `SPEC-CHG-2026-08-04-PFI-CONTINUITY-CONTENT-FAMILIES`
  - Verification: a fresh independent analysis reports `IMPLEMENTATION READY`, Critical/High 0,
    and no material open question for content-profile completeness, derived source-set equality,
    Lean receipt binding, and detached-fixture isolation. Only then may the parent requirements and
    root-index status be promoted, followed by a distinct post-promotion review. This task does not
    waive the subsequent child synchronization, red test, implementation, release, or rollback tasks.

- [ ] 37. Restore exact C14N novelty identity and the acyclic bootstrap lane, then re-promote PFI.
  - Covers: PFI-001, PFI-008
  - Repositories: cross-repo, pals-agent
  - Change ID: `SPEC-CHG-2026-08-04-PFI-C14N-IDENTITY-BOOTSTRAP-RESTORATION`
  - Depends on: Task 36's approved/post-reviewed content-family parent bytes.
  - Verification: PFI fixes the exact novelty JCS member names and canonical byte digest, makes the
    synthetic-only bootstrap the sole exception to the otherwise complete child gate, independently
    converges with C/H=0, status-promotes, and receives a distinct post-promotion review. The
    review proves the bootstrap cannot read a child catalog or produce any release/DB/runtime output;
    Tasks 23, 24a, and 25--29 remain required for every wider content-family action.

- [x] 38. Restore valid-XML C14N v4 transport bytes and re-promote the parent contract.
  - Covers: PFI-001, PFI-008
  - Repositories: cross-repo, pals-agent
  - Change ID: `SPEC-CHG-2026-08-04-PFI-C14N-VALID-XML-TRANSPORT-RESTORATION`
  - Depends on: Task 37's completed identity/bootstrap parent promotion and post-review.
  - Verification: requirements define the exact one-artifact raw-C14N intermediate and
    valid-XML transport-canonical v4 byte output; design permits no read-time repair. This task
    regenerates the PFI prefix golden/hash and the Spec-owned
    `evaluation-corpus.json`/`.md` as parseable v4 bytes at corpus SHA-256
    `9f3cbf318ae5d6ba3accc635a65bb9df67ccf5f503f2fec6a6c22a6a93613e54`, and retires the old raw
    corpus from every compatibility/production claim. Fresh independent convergence reports C/H=0
    and no material open question, then the parent and index undergo the exact two-surface status
    promotion and distinct promoted-byte review. The Agent C14N-only child is resynchronized and
    independently reapproved before its Red/Green parser-round-trip and raw-artifact-rejection
    tests. Only then may CDS Task 13 mechanically regenerate the companion and novelty keys. No
    catalog child approval, Lean compilation,
    manifest/evidence/receipt/seed production, local pgvector load, API publication, or database
    write occurs under this task.
  - Evidence: the v4 parent bundle independently converged C/H=0; its status-only inverse hashes
    were requirements `921f9331b86ea06b2e0194c2b43d997af12e80d72c9db109553e2cfc1677f62c` and
    index `dbbe10659f7255c44c8d85c9e969bc0347145d74ef707882b28c65f5f3dac2eb`; and a distinct
    promoted-byte review returned C/H=0. `evaluation-corpus.json` is SHA-256
    `9f3cbf318ae5d6ba3accc635a65bb9df67ccf5f503f2fec6a6c22a6a93613e54` with six direct-parseable
    v4 strings, and the parent prefix oracle is SHA-256
    `a888813eb8c530dda0513e75e6bb833767e326a1d475c08ccbfcf828d5689565`.

- [ ] 39. Restore existing global-continuity recognition in the focused typed profile.
  - Covers: PFI-001, PFI-008
  - Repositories: pals-agent
  - Change ID: `SPEC-CHG-2026-08-05-PFI-CONTINUOUS-ON-PROFILE-RECOGNITION`
  - Depends on: the approved PFI-010 parent contract
  - Verification: a direct `continuous_on(R, fns1:lambda(...))` proposition first fails before the
    correction and then succeeds only with the existing closed typed-v4 profile. Existing wrong
    sort, free variable, noncanonical byte, and unknown-symbol cases remain rejected. This task
    creates no catalog card, Lean receipt, seed, database write, or release claim.

- [ ] 40. Restore C14N v4 identity across PFI release-tooling and runtime compatibility checks.
  - Covers: PFI-001, PFI-008
  - Repositories: pals-agent
  - Change ID: `SPEC-CHG-2026-08-05-PFI-C14N-V4-RELEASE-TOOLING-ALIGNMENT`
  - Verification: seed-build, CLI, worker-image, private candidate, and runtime tests accept only
    C14N v4 fingerprint/provenance metadata and reject v3 before an embedding, image, candidate,
    or database side effect. The legacy non-PFI Draft catalog remains unchanged.

- [ ] 41. Restore full current-card fidelity in detached pgvector validation.
  - Covers: PFI-009
  - Repositories: pals-scripts
  - Change ID: `SPEC-CHG-2026-08-05-PFI009-FULL-CARD-FIDELITY`
  - Verification: unit/contract tests mutate a retained catalog field, row content, parent/catalog
    binding, vector, and fixture isolation independently; two clean local loads retain all 110
    complete card objects, pass 110 self-nearest-neighbour checks, and leave no fixture container.
    The evidence remains local validation only.
