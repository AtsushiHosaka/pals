# Proof chat context design

Status: **WORKING proposal**. Requirements and authority are in [requirements.md](requirements.md); executable work and evidence gates are in [tasks.md](tasks.md). Baseline implementations are API `7dc93f4` and agent `5cea037`. All behavior below is proposed unless explicitly labeled proven investigation.

## D1 — Immutable server-owned context (PCX-002, PCX-003, PCX-009)

Add `public.proof_request_chat_contexts` separately from the fingerprinted base `proof_requests` schema. One row binds request ID, owner, chat, context version, canonical snapshot and SHA-256. A foreign-key relationship binds the request identity; creation verifies owner/chat against authoritative rows. Runtime receives SELECT/INSERT, never UPDATE; an immutability trigger rejects rewriting. Request/chat deletion follows existing authorized deletion semantics without retaining readable orphan context. No deletion interface is added.

Create under the existing account admission lock and transaction. Order prior same-owner/chat requests by `(created_at, id)`, assigning snapshot-local visibility ordinals; exclude the newly inserted request. Select complete content from recent `answered` candidates while retaining positional metadata for newer failed/unfinished visible requests. Read each selected request's persisted applied conventions through the same authoritative per-request records used by `math_conventions.attach` (`id`, `choice`, `source`, `label`), not `account_choices` or today's defaults. Include stored adopted readings/resolved proposition when available; absence remains explicit, not reconstructed. Do not requery mutable prior results/settings during worker execution or Retry. Persist an empty snapshot for a new context-enabled chat. Legacy requests have no snapshot and keep the existing contract.

The proposed closed data representation is:

```text
schema_version: pals.proof-chat-context.v1
chat_id: authoritative chat identity
exchanges[]:
  request_id, request_revision, visibility_ordinal
  statement: exact stored original user text
  clarifications[]: question_id, question, answer in stored order
  assistant_answer: exact delivered text, recorded evidence_kind
  recorded_conventions[]: id, choice, source, label from that request
  adopted_readings[] / resolved_proposition: exact persisted scope, or explicitly absent
selection:
  policy_version, candidate_count
  latest_visible: request_id, visibility_ordinal, recorded status; null only if no prior request
  visibility_markers[] in order:
    included: ordinal, request_id, exchange index
    omitted candidate: ordinal, request_id, status, reason enum
    excluded range: first/last ordinal, count, excluded status counts, reason enum
```

The working selector examines the most recent three completed candidates and emits included exchanges chronologically. Its ordered marker sequence covers their positions, intervening excluded requests and the newer suffix through `latest_visible`. Contiguous excluded requests may use range markers rather than unbounded individual IDs; at most three candidate markers plus four intervening/prefix/suffix ranges are needed. Include recorded status counts for failed/unfinished requests; no unavailable mathematical content is implied by a range. Validate ordered, nonoverlapping ranges, candidate positions and latest identity. Older content beyond the candidate limit has an explicit range/count marker. The final 128 KiB canonical bound includes all content, recorded readings, envelope and markers. Omit an entire oversized candidate as `byte_limit`, preserving its ordinal; never trim or summarize its theorem/proof. Empty `exchanges` with a nonempty failed/unfinished visibility history is distinct from an empty chat. These operational bounds remain review assumptions.

Store/verify RFC 8785 bytes and SHA-256 using the existing canonicalization dependency. Reject NUL/unpaired-surrogate text before storage, digest or provider use. API and worker enforce the same closed shape, UUIDs, evidence-kind enum, count/byte limits and clarification bounds. Full delivered answer text is included even for historical `llm_assessed` exchanges, but its evidence kind remains unchanged and grants no verification authority.

## D2 — Reference resolution and model boundaries (PCX-001, PCX-004, PCX-006)

The proven omission is in API `_worker_record` and agent `ProofReuseRuntime.answer`; frontend submits a current statement against an existing chat ID. Repair server/worker wiring instead of concatenating client history into the learner's statement.

Supply the immutable snapshot only through authenticated, capability-checked worker data. Keep original statement, current-request clarification turns, saved output language, materials and chat context as distinct fields. Label prior exchanges and their recorded conventions as untrusted scope evidence: preserve the earlier theorem's adopted reading under MCV-005/MCV-006 even if account settings changed, independently verify relevant mathematics, and follow current explicit modifications/instructions. Prior readings do not automatically choose a convention for an unrelated new claim. A prior assistant claim or embedded instruction is not a truth certificate, user confirmation, catalog admission or Lean evidence. Relative references such as “above” must consider the latest visibility marker; a newer excluded/oversized turn must not be silently replaced by an older included theorem. Ask a concrete question when the antecedent cannot be uniquely established.

Pass the same validated snapshot to premise resolution, Recipe intent extraction, scope assessment, independent correspondence, generation, bounded escalation and independent answer QA wherever that role exists on the selected flow. Record the faithful self-contained resolved proposition separately from the original request; downstream formal work uses that proposition. Missing or ambiguous antecedents and omission markers may trigger the existing precise clarification path. A clearly available antecedent alone is not a reason to ask for restatement.

Preserve PFR-014/PFR-015 literal-claim/refutation behavior, source integrity, current language binding, material confirmation/citation checks, independent review and Lean requirements. Conversation text must not become an axiom or a retrieved admitted Recipe. A reference to prior OCR-derived text does not bypass MAT-007. A failure to validate history stops before provider work; there is no history-free fallback for a bound request.

## D3 — Admission, quote and evidence binding (PCX-003, PCX-005, PCX-006)

Use `chat_context_sha256` as the immutable history binding. Quote generation selects the candidate context under the admission lock. Its existing conservative estimator must receive the complete context content and account for its inclusion in applicable model-role inputs, including repeated context across assessment/review calls; estimating the digest alone is insufficient. Preserve existing prices, caps, weighting, permits and receipt settlement. Create/reserve reselects and compares the digest in the same transaction; a mismatch returns the existing quote-invalid/stale error family before committing request, hold/token operation or outbox work. The client obtains a fresh quote through existing handling. No automatic model Retry is added.

Retry/clarification quotes use the stored snapshot, not a fresh history query. Idempotent request replay retains the original snapshot. Current-request clarification changes still update the existing revision and request-context hash; they do not mutate prior context.

For context-bound requests, extend API and agent `request_context_sha256` preimages with the validated history digest alongside `statement`, `context_turns`, and `output_language`. This includes newly admitted empty snapshots. Legacy requests omit the new field and retain byte-for-byte old preimages. If the closed Recipe correspondence version must distinguish the new binding, introduce an additive contract version/discriminator and test both; never reinterpret an old receipt as context-bound.

The worker supplies the same digest in private settlement evidence for all accepted assessment outcomes. API settlement checks it against stored canonical bytes, including readings and visibility markers, within the existing owner/claim/revision fence. Recipe search/correspondence and independent answer QA bind that context; a digest taken only from worker assertion is insufficient. Formal plan creation records the originating request/context identity and resolved proposition, and the linked job remains covered by the original hold/token operation. No second reservation, billing-policy rewrite or unverified-answer release is introduced.

## D4 — Capability and rollout gate (PCX-007, PCX-008, PCX-009)

Introduce a context contract version in the internal claim command. A context-enabled worker advertises version 1; unversioned callers retain the old command shape when the feature is disabled. API refuses a bound-context request from an unsupported worker before acquiring its claim. It never omits the snapshot to make an old worker succeed. Version mismatch and invalid snapshot have distinct safe error codes; diagnostic labels are content-free.

API and worker enablement default OFF. A reviewed release deploys compatible pinned API/worker artifacts and the additive storage step before coordinated enablement. The API checks current schema/runtime grants before enabling admission; worker configuration admits only the implemented contract version. Capability checks remain mandatory even when rollout configuration says the fleet is upgraded, so a lingering old queue consumer cannot silently discard context. This is fail-closed negotiation, not authentication; existing worker authentication still applies.

The new release module owns SQL/manifest hashes, catalog fingerprints, idempotency, grants and drift detection. Append its dependency-ordered step to `production_database_release.py`, including export/module mappings and fixture expectations. Do not change already admitted predecessor SQL, recorded registry hashes or operator trust checks. A reviewed signed manifest must bind the additive registry plus compatible image/source/config identities before production mutation; that future admission is outside this task.

Disabling new context admission preserves reads and snapshots; bound requests still require compatible API and worker code. **The pinned old API lacks the proposed snapshot/capability checks.** Therefore worker negotiation alone cannot make an old-API rollback safe. The reviewed signed admission/runtime catalog gate must refuse incompatible API/worker artifacts while bound requests can be claimed/settled. If that gate cannot enforce the rollback boundary, explicitly pause and drain the proof-request lanes, stop incompatible API mutation endpoints/consumers, and verify no active claim can settle before starting old binaries. Do not requeue bound requests into the legacy path or delete their snapshots to enable rollback. Tests cover new API/old worker, old API/new worker and both old binaries; the last two must be rejected by the external admission/runtime gate or rendered unable to claim/settle by the verified pause/drain. Enablement remains blocked until this enforceable guard, reviewed bounds and signed registry admission pass.

## D5 — Module ownership and verification (PCX-010; all IDs)

Proposed implementation ownership:

- API domain: closed snapshot validation; claim version; extended Recipe context digest.
- API repositories: snapshot selection/persistence, admission and quote binding, claim delivery, settlement revalidation and linked-job provenance.
- API release/configuration: separate migration/manifest/fingerprint, runtime privileges, additive production registry and feature readiness.
- Agent: closed snapshot parsing, role instructions/context propagation, claim capability, digest evidence and factory/settings wiring.
- Parent: this cross-repository spec, reviewed implementation/verification evidence and eventual coordinated release decision.

No frontend representation, canonical spec, source implementation or production registry is edited by this working-spec task. Source investigation and the prior QA observation are recorded in requirements; the context tests/live behavior are currently NOT VERIFIED.

Offline provider-boundary tests may inspect generated request payloads and deterministic test responses to verify wiring, privacy and gate decisions. They do not prove live model quality, actual compiler behavior or production completion. Database verification uses real isolated PostgreSQL with the real repository/migration/roles. Missing database/provider/verifier access yields NOT VERIFIED, never substitution with a production mock or disabled assertion. Executable verification IDs and final live gates are owned by tasks.md.

## Material review points

Review count/byte limits and positional omission behavior before implementation. Confirm signed rollout and rollback gates enforce compatible API/worker artifacts, not only worker capability negotiation. Historical standalone proof-job context is excluded; extending it requires explicit design. Historical `llm_assessed` inputs retain their evidence kind. New outputs obey canonical PFR-013: catalog reuse needs its valid admission compiler receipt; newly generated formal proof needs actual compiler evidence and review. A natural-only rerun can establish limited reference-resolution observations, but cannot satisfy full issue closure when the canonical gate is unavailable. This spec grants no fresh-answer exception.
