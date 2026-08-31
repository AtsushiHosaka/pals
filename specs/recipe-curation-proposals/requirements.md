# Recipe Curation Proposals Requirements

## Purpose

学習者との対話で到達した verified proof を、会話内容と混同せず再利用候補として審査する。
候補は Lean Recipe Catalog への自動公開ではない。明示的な curator の推薦、既存の Recipe
authoring/admission、独立 alignment review を経たものだけが selectable Recipe になれる。

## Definitions

- **Curation Proposal**: 一件の verified proof candidate を再利用候補として固定した、内部専用の
  immutable record。既存の「Recipe candidate」（選択済み Recipe を proof job に投入する値）とは別物。
- **Curator**: 候補を推薦または審査する、API が認証した内部運用 principal。
- **Origin binding**: `pals.recipe-curation-origin.v1` の RFC 8785 object。`proof_job_id`、
  `candidate_id`、`candidate_schema_version`、`candidate_source_kind`、Lean source SHA-256、
  semantic-review target declaration SHA-256、verifier-attestation SHA-256、semantic-review schema
  version、およびその schema の evidence SHA-256 を含む。v2 `model` candidate では
  source-binding SHA-256 も含む。v1 candidate の source kind は literal `legacy_provenance_unknown_v1` であり、
  その provenance を `model` や Recipe と推測で補完しない。

## Goals

- verified proof のうち再利用価値があるものだけを、対話と分離して後から審査可能にする。
- 候補化・審査・Recipe admission の責任と証跡を分離する。
- 学習者の質問、説明、clarification、アカウント識別子を Recipe Catalog に持ち込まない。

## Non-goals

- verified proof、LLM 出力、または chat の終了を契機に自動で Recipe を publish/admit すること。
- 学習者向けの候補投稿、候補一覧、Recipe authoring、または公開 Recipe API を提供すること。
- raw chat transcript、prompt、説明本文、clarification 本文、学習者アカウント識別子を proposal に
  複製すること。
- Lean Recipe Catalog の exact-target selection、authoring manifest、alignment admission の検証条件を
  緩めること。

## Functional requirements

| ID | Requirement |
|---|---|
| RCP-001 | An authenticated internal curator shall be able to nominate exactly one `verified` v1 proof verification candidate or v2 `model` candidate as a Curation Proposal. The service shall derive the closed Origin binding from durable candidate, verifier, and semantic-review records; it shall not accept caller-supplied Lean source, target, evidence digest, account identifier, or chat text. A candidate that is absent, not verified, not bound to one exact Lean source, is Recipe-originated, or lacks successful verifier and independent semantic-review evidence shall be rejected. A v1 candidate is eligible only when its historic evidence validates as-is and is labeled `legacy_provenance_unknown_v1`; the service shall not assert a model origin, invent v2 source binding, or invent Recipe provenance. |
| RCP-002 | A Curation Proposal shall be immutable and append-only. It shall bind a proposal ID, the Origin binding, server-derived proposing curator principal, an enum proposal reason code, and an immutable lifecycle event. Its initial state is `proposed`. Valid transitions are only `proposed` to `approved_for_authoring`, `rejected`, or `retired`, and `approved_for_authoring` to `retired`; `rejected` and `retired` are terminal. One Origin binding may create one proposal total, including after a terminal event. |
| RCP-003 | Proposal records and their internal read/list operations shall be available only to a dedicated curation credential and API-owned curation writer/reader identities. The API shall derive the fixed versioned curator principal from that credential; it shall reject worker, agent, selector, catalog-owner, learner-facing, generic-Draft, absent, or incorrect credentials. The agent, learner-facing API, generic-Draft identities, and Recipe runtime selector shall have no proposal read or write permission. Proposal data shall contain no raw chat transcript, prompt, explanation, clarification, learner account ID, or mutable reference whose later content is used as admission evidence. |
| RCP-004 | Approving a proposal shall only mark it `approved_for_authoring` with a curator decision record. It shall never insert, alter, select, or publish a Recipe or alignment. A later Recipe admission must use the existing sealed `RecipeAuthoringManifestV1`, independently supplied `source_author_principal`, compiler verification, and separately reviewed alignment required by LRC-004 and LRC-005. |
| RCP-005 | The service shall make proposal creation idempotent only for an exact replay of the same proposal ID, Origin binding, server-derived curator principal, and proposal reason code while the proposal is `proposed` or `approved_for_authoring`; a changed value, different proposal ID for the same Origin binding, or terminal proposal shall be rejected without mutation. Every lifecycle decision shall compare the request's expected event sequence with the locked current event and shall atomically append exactly one valid event or return a closed conflict reason. |
| RCP-006 | The curation contract shall use only closed versioned propose, decision, list, and response objects. Proposal reason codes are `reusable_proof`; decision reason codes are `independent_curation_approved`, `not_reusable`, and `superseded_or_invalid`. Free-text rationale, caller-supplied principals, and unknown, absent, or duplicate members are invalid. Successful propose and decision operations return the same closed proposal summary. List sorts proposal IDs in ascending UTF-8 byte order and accepts only an optional exclusive `after_proposal_id` cursor and `limit` from 1 through 100; its response contains closed proposal summaries and the next cursor or `null`. The service shall return only the closed error codes `unauthorized`, `invalid_request`, `origin_not_found`, `origin_not_verified`, `origin_recipe_source`, `origin_evidence_missing`, `proposal_conflict`, `proposal_terminal`, `proposal_transition_conflict`, and `persistence_failed`. |

## Acceptance criteria

- A curator can nominate a v1 verified proof or v2 model-origin verified proof without copying its user question, explanation, clarification, or account data into the proposal; a Recipe-origin proof is rejected.
- Nominating a proof that lacks a successful Lean verification or independent semantic review creates no proposal.
- The stored Origin binding identifies the exact verified Lean source and target used by the proof candidate; caller-supplied substitutions are rejected.
- An approved proposal does not make any Recipe selectable. A Recipe can become selectable only after the existing Recipe and alignment admission gates pass.
- A learner-facing request and an agent/selector request cannot create, list, or read a proposal.
- Exact replay is safe; a conflicting replay, second proposal for the same origin, or transition after rejection/retirement leaves the stored proposal unchanged.
- A worker, agent, selector, catalog owner, or learner-facing credential cannot create, decide, list, or read a proposal; free text cannot be persisted in a proposal or event.

## Constraints and assumptions

- Proposal storage is local, internal, and append-only in the first slice. The service derives
  `verifier_attestation_sha256` from RFC 8785 bytes of exactly `{schema_version, proof_job_id,
  lean_sha256, result_artifact_uri, verification_succeeded}`. It uses v2 semantic review's existing
  `evidence_sha256` and v3 semantic review's existing `review_evidence_sha256` without conversion.
  Public curation workflows,
  learner consent UX, and cross-device sharing are deferred; proposal content deliberately excludes
  user-authored conversation data in this scope.
- A curator may use the conversation in an authorized operational workspace to decide whether to
  nominate a proof, but the proposal's durable evidence is limited to the verified proof record and
  its cryptographic bindings.
- `source_author_principal` remains the identity supplied later by Recipe authoring; a curator is
  not thereby asserted to be the Recipe author.

## Open questions

None for the internal, no-conversation-data first slice.
