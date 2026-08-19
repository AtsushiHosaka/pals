# Recipe Curation Proposals Design

## Scope and traceability

This design implements RCP-001 through RCP-006. It introduces a curation boundary between a
learner's completed proof experience and the Lean Recipe Catalog. It does not change CORE-002
verification, explanation/clarification generation, or LRC runtime selection.

## Ownership and boundary

`pals-api` owns proposal persistence and exposes it only through a dedicated
`X-PALS-Recipe-Curation-Secret` internal curator contract. The server uses constant-time comparison
against its configured secret and derives the fixed principal
`pals.principal.v1/curator/internal`; no request supplies a curator identity. The credential and its
`pals_api_recipe_curation_writer` / `pals_api_recipe_curation_reader` database identities are
distinct from the API runtime, proof worker, agent, selector, catalog owner, generic-Draft, and
learner-facing identities.

The proposal service reads the durable proof verification candidate and its verifier/semantic-review
evidence in the same transaction used to insert a proposal. It derives the Origin binding itself.
Neither the agent nor a learner-facing route accepts or receives proposal records.

The curation boundary deliberately stores no chat or learner content. A curator's external review
may consider the learning conversation, but durable proposal data records only the verified proof
artifact and the curator's closed reason code. The proof job remains the historical owner of its own
chat, explanation, and clarification records.

## Data and lifecycle

`recipe_curation_proposals` has immutable proposal ID, canonical Origin binding bytes and
SHA-256, proposing curator principal, reason code, and immutable initial event evidence. The Origin
binding has exactly the following keys:

```text
schema_version, proof_job_id, candidate_id, candidate_schema_version,
candidate_source_kind, lean_sha256, target_declaration_sha256,
verifier_attestation_sha256, semantic_review_schema_version,
semantic_review_evidence_sha256, source_binding_sha256
```

`candidate_source_kind` is `legacy_provenance_unknown_v1` for a v1 candidate or `model` for a v2
candidate. `source_binding_sha256` is `null` for v1 and the persisted value for v2 model candidates.
The v1 label deliberately makes no claim about how its Lean source was produced. Recipe
candidates are rejected. The verifier-attestation digest is SHA-256 over RFC 8785 bytes of exactly
`{schema_version,proof_job_id,lean_sha256,result_artifact_uri,verification_succeeded}`. The target
digest comes from the persisted semantic-review target declaration. The review evidence digest is
v2 `evidence_sha256` or v3 `review_evidence_sha256`, selected by its persisted schema version; no
historic provenance is reinterpreted. A unique Origin-binding constraint permits one proposal total.

`recipe_curation_proposal_events` is append-only. Sequence one is `proposed`; valid later events
are `approved_for_authoring`, `rejected`, and `retired`. `proposed` may move to any one of those
three values; `approved_for_authoring` may only move to `retired`; `rejected` and `retired` are
terminal. Each decision holds a transaction-scoped proposal lock and supplies the current expected
event sequence, so a stale or competing decision produces `proposal_transition_conflict`. The
current state is derived from the highest valid sequence, never updated in place. UPDATE and DELETE
triggers reject mutation of proposal and event evidence.

## Internal contract

The initial serving operations are `POST /v1/internal/recipe-curation-proposals`,
`POST /v1/internal/recipe-curation-proposals/{proposal_id}/decisions`, and
`GET /v1/internal/recipe-curation-proposals`. Every request uses the curation credential. The
closed propose request is exactly
`{schema_version:"pals.recipe-curation-proposal-request.v1",proposal_id,candidate_id,
reason_code:"reusable_proof"}`. The closed decision request is exactly
`{schema_version:"pals.recipe-curation-proposal-decision-request.v1",expected_event_sequence,
decision,reason_code}`, where the enum pairs are `approved_for_authoring` /
`independent_curation_approved`, `rejected` / `not_reusable`, and `retired` /
`superseded_or_invalid`. It contains no Lean source, source/target digest, author identity, chat
identifier, explanation, clarification, learner data, or free text. The service locks the candidate
and evidence, verifies the RCP-001 conditions, derives the RFC 8785 Origin binding, and atomically
inserts the proposal and sequence-one event.

An exact replay returns the existing proposal only while its nonterminal active state and all bound
values equal the request. A conflicting proposal ID/origin or a terminal proposal returns its closed
conflict reason. Unknown, absent, duplicate, or noncanonical members are invalid. Failed validation,
authorization, lifecycle, or insert work rolls back the entire transaction.

Successful propose and decision responses are exactly
`{schema_version:"pals.recipe-curation-proposal-response.v1",proposal_id,origin_binding_sha256,
state,current_event_sequence,proposal_reason_code,proposing_curator_principal}`. This summary is a
projection of immutable proposal/event data only; it contains neither Origin-binding bytes nor proof,
chat, account, explanation, or clarification data.

The list request permits only the optional query members `after_proposal_id` and `limit`; duplicate,
empty, unknown, or out-of-range members are `invalid_request`. Results sort by proposal ID's UTF-8
bytes ascending. `after_proposal_id` is exclusive; `limit` defaults to 100 and is at most 100. Its
closed response is exactly `{schema_version:"pals.recipe-curation-proposal-list-response.v1",
items,next_after_proposal_id}`. Each item is exactly `{proposal_id,origin_binding_sha256,
state,current_event_sequence,proposal_reason_code,proposing_curator_principal}`. The next cursor is
the last returned proposal ID only if another row exists, otherwise `null`; it carries no state or
user data.

The initial `approve` operation is likewise internal and records an event only. It does not create a
Recipe manifest, invoke a compiler, or call the Recipe Catalog. Recipe authoring starts separately
with the existing release-only command, thus retaining LRC source-author and independent alignment
review boundaries.

## Verification

- Unit/contract tests cover closed input, authentication, server-derived principal, v1/v2-model
  origin derivation, Recipe-origin rejection, evidence absence, exact/conflicting replay, CAS
  lifecycle terminality, and no-conversation-data serialization.
- Proposal derivation reads only `proof_verification_candidates` (candidate ID, proof job ID,
  schema/source-kind, Lean SHA-256, source-binding SHA-256, state, verifier attestation),
  `proof_semantic_reviews` (candidate/proof IDs, Lean SHA-256, target digest, review schema,
  decision, the selected evidence digest), and the proof job's ID/state for the verified join. It
  must not select, persist, or log `theorem_statement`, `context`, owner/account/chat fields,
  explanation/clarification/output-review tables, or free text.
- PostgreSQL integration covers role grants including denied direct base-table reads, append-only
  triggers, transaction rollback, one-Origin uniqueness, and candidate/evidence locking.
- A real API + PostgreSQL test uses a verified proof with actual persisted verification/review
  evidence; it proves before/after equality of Recipe/alignment rows, events, receipts, and traces,
  and that curation identities have no catalog-service invocation or grant.
