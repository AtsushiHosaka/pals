# Lean Recipe Catalog — Specification Update

Status: PASS
Baseline: Parent `8bd6dd7c829ed52687055ca433ec69f9f029b9d9` with user-owned dirty
working trees and initial untracked Lean Recipe Catalog specs created in this loop.
Resulting revision: Uncommitted specification-only changes in the parent repository; no code,
database, API, generated catalog, or test fixture was changed.

## Authorized change

Change ID: SPEC-CHG-LRC-001
Authority: User explicitly requested an SDD loop for a separate Lean Recipe DB that remains
independent from mathematical Drafts.
Reason: The recorded square-continuity run had a sound Draft but failed to turn it into robust Lean
source. Lean-specific compiler/API knowledge needs its own reusable, provenance-bound catalog.
Old behavior: Drafts can contain proof strategy and an informal sketch, while final Lean code is
generated/repaired without a separately versioned, compiler-checked Recipe input.
New behavior: A private service owns an append-only exact-target Recipe catalog and a separate
Draft-to-Recipe alignment catalog. The agent receives only a digest-bound selection DTO and sends
its immutable source unchanged to verification.
Affected IDs: Added `LRC-001`–`LRC-013` and `LRC-T001`–`LRC-T009`; the dependent API migration
uses `RPCS-001`–`RPCS-007`.
Compatibility/migration expectation: Existing generic Draft/PFI schemas and public contracts remain
unchanged. New local service schemas and a private agent port are required.
Assumptions: v1 supports exact targets only; it uses the existing target extractor's whitespace
normalization, but neither alpha-equivalence nor semantic rewriting.
Open decisions: None for v1. Templates, vectors, and production publication are deliberately
deferred rather than left ambiguous.

## Independent-review corrections

Two independent read-only reviews found no P0 issue, but identified seven P1 specification defects
in the draft revision. This update corrected all of them:

| Finding | Correction |
|---|---|
| Draft references were called revisions even though generic Drafts have no revision field. | `DraftRevisionReference` now binds catalog, Draft ID, immutable payload digest, and canonicalizer version. |
| Alignment was inconsistently optional/required and natural-language selection lacked an input path. | Two explicit selection modes now exist: formal-target or aligned-Draft; if both inputs exist, both must agree. |
| Admission `example` source could differ from request-harness/runtime/review source. | `RecipeMaterializerV1` now defines one exact source used for admission, verifier, display, and semantic review. |
| Append-only rows conflicted with mutable status columns. | Immutable payloads and append-only lifecycle events are separated, with a terminal-state selection view. |
| Multiple exact candidates and active toolchain behavior were unspecified. | Active `ToolchainFingerprintV1` and fail-closed `ambiguous_recipe` behavior are normative. |
| Agent-side Recipe DB access conflicted with the existing private-candidate boundary. | The private catalog service owns all database access; the agent has a private DTO port and no DB driver/configuration. |
| Recipe attempts could be recorded as LLM output or fall into repair. | `recipe` is a terminal source kind; verifier failure cannot invoke a model/repair in the same attempt. |
| Existing proof candidate and semantic-review persistence required model-session provenance. | API-owned v2 candidate/v3 review contracts preserve historic rows, bind Recipe receipts/principals, persist server-derived review evidence, and keep v1/public response bytes unchanged. |

## Files changed

- `specs/README.md`: Lists Lean Recipe Catalog as a current canonical specification.
- `specs/lean-recipe-catalog/requirements.md`: Requirements and acceptance criteria.
- `specs/lean-recipe-catalog/design.md`: Service boundary, immutable data/lifecycle model,
  materialization contract, selection modes, and evaluation rules.
- `specs/lean-recipe-catalog/tasks.md`: Ordered implementation and real-dependency verification work.
- `pals-api/specs/recipe-proof-candidate-source/requirements.md`: API/data-model migration requirements.
- `pals-api/specs/recipe-proof-candidate-source/design.md`: v2 source union, receipt authority,
  review evidence, response compatibility, and state design.
- `pals-api/specs/recipe-proof-candidate-source/tasks.md`: Ordered API migration and integration work.
- `docs/lean-recipe-catalog-spec-loop-ledger.md`: Loop evidence and routing ledger.

## Impact matrix

| Changed ID | Requirements section | Design decisions | Tasks | Code/tests/evidence invalidated | Migration/docs | Revalidate |
|---|---|---|---|---|---|---|
| LRC-001–LRC-002 | Independent ownership and alignment | private service, DraftRevisionReference, append-only schemas | T001, T002, T004, T005 | No existing Recipe implementation; generic Draft behavior must remain unchanged | New private schemas/docs only | real DB ownership, lifecycle, and non-mutation tests |
| LRC-003–LRC-004 | exact target and compiler evidence | extractor, materializer, fingerprint | T001, T003 | Existing raw harness logic is insufficient for Recipe source identity | new authoring docs | byte-equality and real Lean receipt tests |
| LRC-005–LRC-006 | alignment and eligibility | two selection modes, exact matching, ambiguity rejection | T004, T005 | Current learner path lacks both ports | private DTO/client docs | aligned/formal/negative selection tests |
| LRC-007–LRC-009, LRC-013 | terminal Recipe attempts and durable selection receipt | exact source propagation, no LLM repair, receipt authority, trace | T002, T005, T006, T007 | Existing GeneratedProof/API provenance cannot represent Recipe source | API migration and trace/operator docs | verifier/reviewer source identity, receipt lifecycle, and terminality |
| LRC-010 | direct lookup/toolchain behavior | runtime attestation, no vectors in v1 | T001, T003, T005 | No toolchain DTO or test service exists | future vector profile deferred | mismatched/missing toolchain tests |
| LRC-011–LRC-012 | square vertical slice/evaluation | explicit δ Recipe, metric manifest | T007, T008 | The existing x² report is failure evidence, not a Recipe witness | evaluation docs | real local DB + Lean corpus gate |

## Validation evidence

- `rg -n "LRC-[0-9]{3}|LRC-T[0-9]{3}" specs/lean-recipe-catalog docs/lean-recipe-catalog-spec-loop-ledger.md` — all current IDs appear in requirements/design/tasks.
- Trailing-whitespace scan over changed spec and ledger files — passed.
- Independent SDD review of the initial draft — identified P1 gaps; all were addressed.
- Independent feasibility review of the initial draft — identified P1 gaps; all were addressed.
- Final read-only review across the Recipe Catalog and dependent API specifications — PASS; no
  remaining P0/P1 contract contradiction.

## Revalidation route

Implement the API source-contract migration, then implement the Recipe Catalog selection port and
run their combined real PostgreSQL/isolated Lean integration gates. The following remain NOT
VERIFIED until implementation: PostgreSQL DDL/roles, private service/DTO, exact materializer,
active toolchain fingerprint, direct Recipe pipeline, square witness, and evaluation corpus.
