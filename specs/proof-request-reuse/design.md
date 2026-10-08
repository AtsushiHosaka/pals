# Proof request design

The proof-request aggregate is what the ordinary Send action creates in project, projectless and guest chats. It owns premise clarification, catalog retrieval and the decision of how the request is Lean-verified. The existing proof-job aggregate remains the Lean engine (DSP generation, isolated verifier, repair, semantic review, explanation, follow-up questions). There is no learner-facing Lean mode selector or consent step.

## States and outcomes

`queued → assessing → needs_input | verifying | answered | failed`. Answering a premise question advances the revision and requeues the same request. The existing SQS worker recognizes `proof_request:<UUID>`. The API owns persistence, ownership, quota, dispatch recovery, leases, linked-job creation and settlement; the agent owns prompts, catalog retrieval and mathematical decisions. No model client belongs in the API.

The worker settles a claimed revision with one of:

- `needs_input`: premise question, including a suspected counterexample or an unstated choice that changes the claim's truth (PFR-014). The assessment output carries `premise_check` (`counterexample`, `truth_depends_on`, `assumed_defaults`), stored only as private evidence. A counterexample comes from the model and is worded tentatively; Lean-checked refutation is a separate, later step.
- `catalog_reuse`: the decision was `direct` and the identical Draft has an aligned admitted Recipe. The settlement carries the Recipe id/revision and materialized-source SHA-256, the independent correspondence review, the natural-language proof generated from that source and its independent answer QA. The API re-reads the Recipe through the selector role and checks source SHA-256, admission compile receipt and the active toolchain fingerprint before storing `answered` with evidence `lean_catalog`; any mismatch is stored as `formal` instead.
- `formal` with plan `refute` (PFR-015): after a clarification turn, when the assessment still reports a counterexample. The plan carries the claim, the suspected counterexample and a negation statement in the output language; its linked job proves the negation with the ordinary DSP pipeline. A verified refutation is answered with `verdict: refuted`. A failed refutation is followed, in the same request, by a `dsp` job for the claim at the next revision.
- `formal`: everything else. The settlement carries the plan (`instantiate` with Recipe binding and substitutions, or `dsp`) and the confirmed premises. In the same transaction the API creates one linked proof job (statement plus confirmed context, `context.proof_request_id`, `context.lean_plan`), its event and dispatch outbox, without a second billing reservation, and sets the request to `verifying` with `formal_job_id`.
- `failed`: provider/catalog/integrity failures and unsupported requests (no answer text).

LLM-only `answer` settlements are rejected for new revisions.

## Linked Lean job

The formal worker runs a request-linked job like any proof job. For `instantiate` it first submits a wrapper theorem applying the selected Recipe to the substitution through the existing Recipe candidate path; on compile failure it continues with the existing DSP pipeline in the same job. When the job is verified and its explanation passes review, the API marks the request `answered` with evidence `lean_verified` (job id, verified Lean source SHA-256) and settles the request's hold once. A terminal job or explanation failure marks the request `failed` with `lean_verification_failed` and releases the hold once. Learner retry creates a new linked job (retry_count ≤ 2). Follow-up questions use the existing explanation clarification API of the linked job.

## Public API

`POST/GET /v1/chats/{chat_id}/proof-requests`, `GET /v1/proof-requests/{id}`, `POST /v1/proof-requests/{id}/answers` and `/retry`. Create supplies statement/idempotency_key; answer supplies question_id/expected_revision/answer/idempotency_key. The response adds `formal_job_id` (nullable). Answer `evidence_kind` is `lean_catalog`, `lean_verified` or (history only) `llm_assessed`. Internal claim, usage and settlement operations are fenced to the current lease and revision. Guest routes expose the same states; guest reads add the linked job's stage, verified Lean source and reviewed explanation, but no follow-up questions.

## Quota

One hold (count policy) or one token operation (token policy) per request revision covers assessment and the linked job. Needs_input releases it; continuation reacquires it. Consumption happens once on a `lean_catalog` or `lean_verified` answer; any terminal failure releases it. Linked-job provider calls obtain permits and receipts against the request's token operation. Bounds: at most five premise rounds, two learner retries and three delivery attempts per revision; admission also has an account rate limit. Public results omit prompts and provider internals. Context belongs to the exact owner/chat/request and is not shared with another learner.

## Frontend

All composers create proof requests. The thread shows premise questions, live Lean stages of the linked job (existing proof-job events), the Lean-verified answer with its Lean source, natural-language proof and follow-up questions (existing explanation and clarification components), and on failure a notice with retry and no answer text. Saved `llm_assessed` answers keep their existing display. Polling and event streams are scoped to the owner and chat, use abort on change and refuse mismatched response identities.

## Existing Draft catalog integration (runtime finding, 2026-09-30)

The existing local catalog contains real `public.dsp_drafts` rows, including universal power continuity, but has no active new PFI/typed publication. Natural-proof retrieval therefore has a distinct worker-authenticated read-only candidate port over these existing sketches. The API owns its dedicated reader credential, bounded top-eight vector query, embedding fingerprint checks, canonical payload validation and exact source content hash. The agent receives candidates without any publication/Lean approval claim and must assess them; only an aligned admitted Recipe (PFR-010) can supply reusable Lean. Do not manufacture a publication receipt, bypass a formal catalog admission gate, or alter formal PFI/typed selection. Only actually available typed profiles may be used by the new runtime. The preserved older embedding metadata is not repurposed as a false generation certification.

The natural retrieval query is an untrusted search hint, not an admitted theorem or a source of substitution types. Generate a bounded strict JSON tree and serialize canonical v2 OpenMath for the real legacy embedding contract. Keep exact source v4 validation/content hashes and numeric-only instantiation separate. Natural retrieval evidence records actual cosine distance and source identity; it does not manufacture formal PFI equivalence scores.


## Provider text and durable JSON storage

Parsed provider JSON must contain Unicode scalar text compatible with PostgreSQL JSONB. Reject U+0000 and unpaired surrogates in every string and key before retaining an assessment, computing the answer hash or requesting independent QA. The strict provider schemas exclude NUL, while the local parser remains authoritative. Never strip or rewrite proof text after QA. Invalid provider text produces the existing `proof_reuse_invalid_response` failure with only earlier valid evidence and no automatic paid retry.

The API's existing recursive closed-command Unicode validator also rejects NUL before repository entry. This is a 422 input/contract rejection, distinct from a transient persistence 503. A failed operation must still persist safe failure evidence and release its original hold without losing already-recorded provider receipts. Exact valid answer bytes and independent QA binding remain unchanged. October 2's repeated square request exposed NUL in the private-evidence JSONB write; its finer nested field is unavailable from retained logs and must not be invented.
