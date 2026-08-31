# Lean Recipe Catalog — Specification Loop Ledger

## Iteration record

| Iteration | Spec revision | Code revision | Trigger | Expected verdict-changing delta | New evidence | Findings opened/closed | Routes invoked | Stage/overall budget | Result |
|---|---|---|---|---|---|---|---|---|---|
| 0 | Parent `8bd6dd7` (dirty); no focused canonical spec | `pals-agent` working tree (dirty) | User-approved direction: keep Drafts independent from Lean-specific reusable knowledge | Establish an implementation-ready boundary without changing Draft semantics or the verified-proof contract | `continuous_square` gives a correct ε–δ Draft, but real generation failed before Lean verification; current learner pipeline does not use proof-flow retrieval; existing `typed_local_catalog` is admission evidence, not runtime proof guidance | Opened LR-01 (independent storage/identity), LR-02 (safe runtime selection), LR-03 (recipe evidence and reproducibility), LR-04 (evaluation) | `sdd-review-spec` baseline | Two iterations / current turn | PASS baseline |
| 1 | Parent `8bd6dd7` (dirty); focused specs untracked | No code change | Two independent baseline reviews | Resolve source-identity, lifecycle, service-boundary, selection, and evaluation defects | Review found no P0 and 7 merged P1 gaps: immutable Draft reference, selection modes, single materialization, lifecycle events, active-toolchain/ambiguity rule, API-owned catalog port, Recipe attempt terminality, and metric oracle | Closed LR-01–LR-04 in the spec revision; opened only downstream implementation evidence | `sdd-update-spec` → targeted `sdd-review-spec` | Two iterations / current turn | Pending re-review |
| 2 | Parent `8bd6dd7` (dirty); focused specs untracked | No code change | Targeted review of the corrected revision | Verify the private port, exact Draft bytes, closed-target restriction, and Recipe provenance boundary | The corrected spec closed prior P1 findings. One new P1 came from the concrete API persistence contract: semantic review currently requires `generator_session_id`, so a Recipe attempt cannot be truthfully persisted without an explicit discriminated candidate-source migration. | LR-01–LR-04 remain closed; opened LR-05 (API review/persistence source union) | targeted `sdd-review-spec` | Two iterations / current turn | FAIL — iteration budget reached |
| 3 | Parent `8bd6dd7` (dirty); Recipe and API-focused specs untracked | No code change | User requested implementation-ready API/data-model specifications | Close LR-05 without altering Draft storage, historic model provenance, or public proof-job payloads | Added a v2 candidate-source/v3 review migration contract and hardened it through focused review: receipt preimage/key separation, authority revalidation, expiry/retirement serialization, source-author/reviewer principal binding, v2 worker response isolation, and immutable v3 review evidence | Closed LR-05; added LRC-013 selection-receipt requirement | `sdd-generate-spec` → `sdd-update-spec` → targeted `sdd-review-spec` | One focused iteration / current turn | PASS — specification-only |
| 4 | LRC `946bff0b`/`2ac4c2f7`/`2b21920f`; RPCS `aa20e507`/`189181cd`/`9c1e1686` | Parent `8bd6dd7`; API `d9c18af`; agent `9b696dd` (all dirty) | User invoked implementation-alignment SDD loop | Determine whether the approved Recipe path is implemented and make the smallest safe vertical slices | Read-only audit found all Recipe Catalog runtime work missing; added agent private selection client and API v2 source/persistence core. Spec review also corrected source-vs-DTO verifier wording and receipt nonce lifetime. | Opened implementation gaps LR-06 (catalog/runtime), LR-07 (API route/reconciliation), LR-08 (real DB/Lean evidence); closed one LRC task wording defect | `sdd-audit-implementation` → `sdd-update-spec` → `sdd-review-spec` → `sdd-implement-spec` | Two iterations / current turn | FAIL — full approved scope incomplete |
| 5 | Same inputs; LRC nonce window/current task wording changed in working tree | Same dirty working trees plus agent/API core changes | Targeted review of the newly implemented slices | Close concrete client and API-core defects without expanding to catalog/runtime scope | Closed target extraction, nonce retention/error handling, idempotent Recipe binding comparison, and migration mixed-state detection; reran focused unit/static checks and independent delta reviews. | Closed client P1/P2 and API-core P1/P2; LR-06–LR-08 remain | `sdd-implement-spec` → `sdd-review-code` | Two iterations / current turn | FAIL — iteration budget reached with major tasks still missing |
| 6 | LRC `a393c1be`/`66624aa1`/`fb2301b9`; RPCS design `0f7c7ff5` | Parent/API/agent working trees remain dirty | User restarted `$sdd-run-loop` to continue implementation readiness | Complete LRC-T002 and LRC-T003 without expanding the runtime selection scope | LRC-T002 passed fresh install, idempotence, and six integrity-drift cases on local PostgreSQL 16. T003 review exposed missing sealed-manifest/digest, release-writer, admission-verifier, replay, and initial-event contracts; `SPEC-CHG-LRC-007` closed them. Release-only admission then passed a combined API materializer → actual TLS 1.3 mTLS verifier → pinned Lean workspace → NOINHERIT owner transaction → PostgreSQL readback test, including every Recipe/profile/evidence/event binding. | Closed LR-09/LR-10 (T002) and LR-11 (T003 contract/implementation). LRC-T004+ and runtime/API integration remain. | `sdd-review-spec` → `sdd-update-spec` → targeted `sdd-review-spec` → `sdd-implement-spec` → `sdd-review-code` | Two iterations / current turn | PASS — scoped LRC-T002/T003 |

## Delegation record

| Delegation ID | Agent/skill | Owned slice | Mode | Result | Next route |
|---|---|---|---|---|---|
| DL-004 | `recipe_implementation_audit` / `sdd-audit-implementation` | LRC/RPCS implementation matrix | Read-only | FAIL: catalog/runtime absent; current API is model-only | Implement API source core and agent client first |
| DL-005 | `recipe_selection_agent_port` / `sdd-implement-spec` | Agent private selection client | Implementation, `pals-agent` client/tests only | PASS after two targeted corrections; 35 focused tests | Planner integration after real API selection service |
| DL-006 | `recipe_api_source_core` / `sdd-implement-spec` | RPCS-T001/T002 source model and migration | Implementation, `pals-api` core/migration/tests only | Partial: code/unit evidence passes; real PostgreSQL migration is unverified | RPCS-T003 and real PostgreSQL gate |
| DL-007 | `recipe_selection_code_review` / `sdd-review-code` | Agent then API-core implementation deltas | Read-only | Client and API-core correction deltas PASS | Re-review only future changed routes |
| DL-008 | `recipe_spec_header_review` / `sdd-review-spec` | LRC cross-reference/task semantics | Read-only | Found and closed DTO-versus-source verifier wording | Re-review affected specs after later semantic changes |
| DL-009 | `recipe_catalog_spec_review` / `sdd-review-spec` | LRC-T002 plus RPCS authority boundary | Read-only | Initial FAIL: five P1 contract/task defects and one P2 lifecycle-code weakness. Re-review PASS after `SPEC-CHG-LRC-006`. | LRC-T002 implementation |
| DL-010 | `recipe_catalog_persistence` / `sdd-implement-spec` | LRC-T002 catalog DDL, roles, lifecycle lock, release migration, focused tests | Implementation; new catalog migration/release/test paths plus unavoidable bootstrap wiring only | PASS after repairs: direct target-only `UNIQUE INDEX` drift is rejected via `pg_index`; fresh install, idempotence, and six drift cases passed on PostgreSQL 16. Parent rerun: 7 integration and 9 unit tests; static checks pass; temporary DBs/catalog roles were `0/0`. | LRC-T003 admission/materialization |
| DL-011 | `recipe_catalog_persistence_review` / `sdd-review-code` | LRC-T002 persistence diff | Read-only | PASS after progressive repair and final changed-input review; no actionable P1/P2. | LRC-T003 admission/materialization |
| DL-012 | `recipe_admission_spec_review` / `sdd-review-spec` | LRC-T003 manifest/admission/verifier boundary | Read-only | Initial FAIL: closed manifest/digests, writer identity, verifier contract, replay, and initial-event binding absent. Final delta review PASS after `SPEC-CHG-LRC-007`. | Resume LRC-T003 implementation |
| DL-013 | `recipe_admission_verifier_endpoint` / `sdd-implement-spec` | Agent-owned private RecipeAdmissionVerifierV1 endpoint | Implementation, verifier server/runtime and focused tests only | PASS after timeout mapping and non-skipped actual mTLS/pinned-Lean endpoint evidence; existing proof-job verifier route unchanged. | LRC-T004 alignment admission |
| DL-014 | `recipe_admission_verifier_review` / `sdd-review-code` | Agent verifier endpoint delta | Read-only | Initial FAIL: timeout mapping and direct/skipped Lean test. Re-review PASS after correction. | LRC-T004 alignment admission |

## Baseline evidence

- The product contract in `specs/pals-product-core/requirements.md` already requires that a visible `verified` proof compile and undergo independent review. This loop does not weaken or replace that contract.
- `pals-agent/pals_agent/factory.py` constructs the learner path with `proof_flow_retriever=None`; Draft retrieval is not currently a learner-proof fallback.
- `pals-agent/pals_agent/generator.py` gives the model only a generated Draft and Sketch for the final Lean pass. It has no separately versioned, compiler-checked Lean recipe input.
- `/private/tmp/pals-x2-generation-1786498617/x2-generation-report.json` records a real run for continuity of `x ↦ x²`: the selected Draft's epsilon–delta strategy was mathematically sound, but preflight rejected the generated source for missing a syntactic explicit `let δ`; subsequent source also had unresolved Mathlib/API issues. Generic vector retrieval itself was not demonstrated because the catalog canonicalizer versions differed.
- `pals-agent/pals_agent/typed_local_catalog.py` already demonstrates isolated schemas, sealed manifests, exact canonicalization, embedding bindings, and fail-closed SQL preparation. Its typed-Draft evidence is not a contract for generation-time Lean snippets.

## Human decisions

| Decision | Authority | Selected boundary | Status |
|---|---|---|---|
| Lean knowledge placement | User | Keep theorem Drafts and Lean recipes independent; connect them with a many-to-many semantic alignment layer. | Closed |
| Recipe admission | Safe default pending implementation | Only compiler-checked, toolchain-pinned and immutable recipe revisions are selectable. Automatically generated code is never promoted merely because it was retrieved. | Closed |
| Runtime miss behavior | Safe default pending implementation | A missing or incompatible recipe is reported as unavailable to the generation planner; it is not silently substituted with stale or mismatched Lean code. Existing proof generation/verification behavior remains otherwise unchanged. | Closed |

## Initial scope boundaries

- The private catalog service owns local Recipe/alignment storage; the agent uses a digest-bound
  private DTO and never connects to that database directly. Public API publication, authorization,
  and cross-device synchronization are outside the first slice.
- The first release covers exact theorem alignment only. Semantic rewriting, automatic Recipe
  authoring, templates, and vector search are deferred.

## Requirement evidence

| Requirement area | Design/task evidence | Review result | Implementation evidence |
|---|---|---|---|
| LRC-001–LRC-002 | Private `pals-api` owner, RFC 8785 DraftRevisionReference, append-only schemas and events | PASS in final review | LRC-T002 schema/grant/lifecycle evidence verified on PostgreSQL 16; Draft alignment admission remains unimplemented |
| LRC-003–LRC-004, LRC-010 | Closed Recipe manifest, deterministic materializer, pinned admission verifier, release-only owner transaction, exact toolchain/evidence/event bindings | PASS after targeted review | LRC-T003 verified with actual mTLS verifier, pinned Lean, and PostgreSQL; runtime selection remains unimplemented |
| LRC-003–LRC-006 | Closed-target extractor, one materializer, exact selection modes, toolchain/ambiguity rules | PASS in final review | NOT VERIFIED |
| LRC-007–LRC-009, LRC-013 | Authenticated DTO, selection receipt, terminal Recipe attempt, API v2 candidate/v3 review migration | PASS in final review | NOT VERIFIED |
| LRC-010–LRC-012 | Direct lookup, square slice, real PostgreSQL/Lean evaluation gate | PASS in final review as a specification boundary | NOT VERIFIED |

## Current implementation evidence

| Requirement area | Current code/evidence | Status | Next action |
|---|---|---|---|
| LRC-001, LRC-003–LRC-004, LRC-010 | Agent private selection client plus a release-only API Recipe admission command, deterministic materializer, separate verifier endpoint, exact replay/terminal behavior, and PostgreSQL atomic insert are implemented and reviewed. | PARTIAL | LRC-T004 alignment admission, then selection/planner path |
| LRC-002, LRC-005, LRC-011–LRC-013 | `pals-api` has isolated Recipe/alignment schema, least-privilege roles, append-only lifecycle enforcement and release migration; actual Recipe admission has mTLS/Lean/PostgreSQL evidence. Alignment admission, selection receipts, square Recipe, and evaluation corpus are absent. | PARTIAL | LRC-T004–T008 |
| RPCS-001–RPCS-003 | API core contains closed source union, receipt authority port/model, additive migration, and focused unit evidence; real migration integration skipped without `PALS_TEST_POSTGRES_URL` | PARTIAL | Run real PostgreSQL migration, then wire authority/worker routes |
| RPCS-004–RPCS-007 | No v2 worker route, v3 reviewer route/auth, terminal Recipe reconciliation, output regression, or end-to-end API/Lean flow | MISSING | RPCS-T003–T007 |

## Final report

# Specification Loop Result

Status: PASS (scoped LRC-T002/T003)

Objective: Complete isolated Recipe catalog persistence and release-only exact-source admission,
without coupling it to the Draft database or exposing a runtime write path.

Pinned baseline: Parent `8bd6dd7c829ed52687055ca433ec69f9f029b9d9`; API
`d9c18af809c6cf89d1dd7d8e12853da96579ce84`; agent
`9b696dd2492f6bb34cc6740e9112a7063a811e4d`, with unrelated user-owned working-tree changes.
Final current specification hashes are LRC
`a393c1bee8dbe7c7f6ac90962105384170e68a5e8e5932a515d9d359f2594a31` /
`66624aa15ea3986476fa03175c77f7ae2e5015a591e98f58fb6c24fd030434ea` /
`fb2301b9a22251026f5dff1812cfd3731ed75a929c7cde5b276e58a3a913a2cc`, and RPCS design
`0f7c7ff53a8661b0cafb7e414ce48b6085dcd74deb51d733433d07e678a90e63`.

Completed work:

- Added canonical requirements, design, and task artifacts for an append-only exact-target Lean
  Recipe Catalog, a separate many-to-many Draft alignment catalog, and a compiler-bound square
  continuity vertical slice.
- Defined `pals-api` internal ownership, an authenticated RecipeSelection DTO, RFC 8785 generic
  Draft payload references, one byte-exact materializer, closed-target v1 scope, lifecycle events,
  exact selection modes, terminal Recipe verification, toolchain attestation, and a real
  PostgreSQL/Lean evaluation gate.
- Performed two independent baseline reviews, a targeted re-review, and a final read-only API
  contract review. The initial reviews opened seven P1 specification defects; the targeted
  correction closed them. The API provenance gap is now specified by
  `pals-api/specs/recipe-proof-candidate-source/` and LRC-013.
- Defined versioned internal v2 candidate and v3 semantic-review contracts, historical v1/v2
  compatibility, server-derived reviewer evidence, immutable selection receipts, exact author
  principal binding, terminal Recipe failure, and v1/public response isolation.
- Implemented and independently reviewed the agent-side private RecipeSelection client: closed
  declaration extraction, authenticated canonical DTO checks, byte-exact source/binding handling,
  and bounded nonce lifetime with fail-closed clock/storage behavior.
- Implemented and independently reviewed the API source-model/migration core: closed model/Recipe
  source union, RFC 8785 source binding, receipt authority port, legacy-v1/v2 preservation,
  immutable v2/v3 persistence constraints, and idempotent binding comparison.
- Implemented LRC-T002: isolated Recipe/Alignment schemas; NOLOGIN/NOINHERIT owner, selector,
  and reader roles; append-only event/lifecycle enforcement; a fixed-search-path advisory-lock
  lifecycle function; release migration idempotence and drift checks. A direct target-only
  `UNIQUE INDEX` is rejected while the composite Recipe binding index remains allowed.
- Validated LRC-T002 on a fresh local PostgreSQL 16 database: seven integration tests (fresh
  install, reapplication, and six drift cases), nine unit tests, Ruff, mypy, and `git diff --check`.
  The test harness left zero temporary catalog databases and zero catalog roles.
- Implemented LRC-T003 as an executable release-only command. It accepts a sealed canonical
  manifest, independently materializes exact Lean bytes, uses a separate private admission-verifier
  contract, and either returns an exact admitted replay before compilation or persists profile,
  toolchain, Recipe payload, compiler evidence, and sequence-one event atomically under a scoped
  catalog-owner identity.
- Validated the full LRC-T003 binding on local PostgreSQL 16: API materializer → TLS 1.3 mTLS agent
  verifier → actual pinned Lean compilation → NOINHERIT release-login transaction → PostgreSQL
  readback. The assertion recomputes and compares manifest/profile/payload/source/toolchain/compiler
  receipt/initial-event bindings. Eleven catalog integration tests and eighteen focused units passed;
  static checks passed and temporary databases/logins were `0/0`.

Invalidated or NOT VERIFIED evidence:

- Alignment admission, selection receipts, HTTP selection, planner forwarding, terminal Recipe
  reconciliation, square witness, and the evaluation corpus remain unimplemented. No runtime
  Recipe-selection-to-proof-review end-to-end run has occurred.

Smallest continuation:

1. Implement LRC-T004–T005: independent Draft-alignment admission and the receipt-backed selection
   service on top of the verified Recipe catalog.
2. Implement RPCS-T003–T005 and LRC-T006: v2 worker/v3 review routes, authority transaction,
   terminal reconciliation, and planner source forwarding.
3. Provision a local PostgreSQL 16 test service and run the migration/integration gates; then add
   the square Recipe and real evaluation corpus under LRC-T007–T008.
