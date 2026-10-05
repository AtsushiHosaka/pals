# Proof request design

The proof-request aggregate is what the ordinary Send action creates in project, projectless and guest chats. It owns premise clarification, direct Recipe retrieval and the decision of how the request is Lean-verified. Draft DB is searched only inside DSP when producing new Lean. The existing proof-job aggregate remains the Lean engine (DSP generation, isolated verifier, repair, semantic review, explanation, follow-up questions). There is no learner-facing Lean mode selector or consent step.

## States and outcomes

`queued → assessing → needs_input | verifying | answered | failed`. Answering a premise question advances the revision and requeues the same request. The existing SQS worker recognizes `proof_request:<UUID>`. The API owns persistence, ownership, quota, dispatch recovery, leases, linked-job creation and settlement; the agent owns prompts, catalog retrieval and mathematical decisions. No model client belongs in the API.

The worker settles a claimed revision with one of:

- `needs_input`: premise question, including a suspected counterexample or an unstated choice that changes the claim's truth (PFR-014). The assessment output carries `premise_check` (`counterexample`, `truth_depends_on`, `assumed_defaults`), stored only as private evidence. A counterexample comes from the model and is worded tentatively; Lean-checked refutation is a separate, later step.
- `catalog_reuse`: direct Recipe search produced one confirmed same-content result. Settlement supplies the admitted Recipe and immutable reuse-entry identities, source/target/toolchain/compiler-receipt digests, the exact stored answer and its language/digest, independent request/source correspondence review and request-specific answer QA. The API re-reads the entry and Recipe, recomputes source/description/answer digests, checks admission and active verifier fingerprint, and persists `answered` with `lean_catalog` while settling the original hold once. No Draft fetch/alignment, generator, explanation generator, proof job or verifier invocation occurs. If lifecycle or toolchain eligibility changed, settle as `formal(dsp)` instead; altered immutable data or forged review binding fails explicitly.
- `formal`: no safe match, specialization or any other need for new Lean source. Settlement carries a `dsp` plan and confirmed premises. In one transaction the API creates a linked proof job, event and outbox without another billing reservation, and sets `verifying`/`formal_job_id`. Draft lookup happens inside that job's DSP Draft stage, never in request assessment.
- `failed`: provider/catalog/integrity failures and unsupported requests (no answer text).

LLM-only `answer` settlements are rejected for new revisions.

## Linked Lean job

The formal worker runs a request-linked job like any proof job. New request-linked jobs use full DSP for all non-identical targets. The legacy ordinary-job Recipe specialization path remains separate and always compiles any new wrapper. When the job is verified and its explanation passes review, the API marks the request `answered` with evidence `lean_verified` (job id, verified Lean source SHA-256) and settles the request's hold once. A terminal job or explanation failure marks the request `failed` with `lean_verification_failed` and releases the hold once. Learner retry creates a new linked job (retry_count ≤ 2). Follow-up questions use the existing explanation clarification API of the linked job.

## Public API

`POST/GET /v1/chats/{chat_id}/proof-requests`, `GET /v1/proof-requests/{id}`, `POST /v1/proof-requests/{id}/answers` and `/retry`. Create supplies statement/idempotency_key; answer supplies question_id/expected_revision/answer/idempotency_key. The response adds `formal_job_id` (nullable). Answer `evidence_kind` is `lean_catalog`, `lean_verified` or (history only) `llm_assessed`. Internal claim, usage and settlement operations are fenced to the current lease and revision. Guest routes expose the same states; guest reads add the linked job's stage, verified Lean source and reviewed explanation, but no follow-up questions.

## Quota

One hold (count policy) or one token operation (token policy) per request revision covers assessment and the linked job. Needs_input releases it; continuation reacquires it. Consumption happens once on a `lean_catalog` or `lean_verified` answer; any terminal failure releases it. Linked-job provider calls obtain permits and receipts against the request's token operation. Bounds: at most five premise rounds, two learner retries and three delivery attempts per revision; admission also has an account rate limit. Public results omit prompts and provider internals. Context belongs to the exact owner/chat/request and is not shared with another learner.

## Frontend

All composers create proof requests. The thread shows premise questions, live Lean stages of the linked job (existing proof-job events), the Lean-verified answer with its Lean source, natural-language proof and follow-up questions (existing explanation and clarification components), and on failure a notice with retry and no answer text. Saved `llm_assessed` answers keep their existing display. Polling and event streams are scoped to the owner and chat, use abort on change and refuse mismatched response identities.

## Recipe-first assessment and matching

The preflight sees the original request, confirmed clarifications and authorized material context. Before candidate retrieval or Lean, it preserves PFR-014 literal-claim counterexample/truth-dependent-choice preflight and the learner’s saved choice; it asks only for a consequential missing premise (PFR-004); search or verification difficulty is not a missing premise. It extracts a bounded mathematical signature before reading candidates. That signature and the exact request-context digest are retained as private evidence; they do not modify the learner's statement.

The internal Recipe search returns at most eight admitted, source-bound reuse entries (LRC-015–LRC-018), without calling the Draft service. Retrieval can use the entry's statement and structured mathematical description; ranking is deterministic and scores do not imply equality. The first assessor compares the request with each candidate's description and actual Lean source. Only a complete signature match can reach the separate-session correspondence reviewer, which sees the original request, confirmed assumptions, selected Lean, stored description and answer. It judges domain, hypotheses, quantifier binding/order, conclusion, method, and whether the stored answer answers this request without adaptation. Candidate text is untrusted data, never prompt instructions.

The independent result is `same`, `different`, or `uncertain`, with a bounded rationale and checks for the named mathematical dimensions. `same` needs every check true. Reviewer failure/invalid response is an explicit provider failure; a valid `different`/`uncertain` result falls through to new Lean. If two distinct eligible candidates remain and their correspondence cannot be disambiguated, use DSP; never select by unspecified row order. Do not copy a candidate's formal target into a selector request and present that circular equality as request verification. The old formal selector normalizes only whitespace and remains a separate proof-job contract.

The stored answer must exist in the request's output language and independently bind to this Recipe source. Request-specific QA reviews these exact bytes against the present request; it does not rewrite them. A missing language variant or needed explanation change uses the new-Lean path. The answer's original review and the present request reviews are distinct evidence. Unicode validation occurs before review, digest and durable JSON storage.

### Decision table

| Situation | Result | Draft DB | Compile |
|---|---|---|---|
| Same mathematical target, method compatible, valid source/answer/toolchain and both independent reviews pass | `catalog_reuse` / `lean_catalog` | No call | No call |
| Similar statement, changed domain/hypothesis/quantifier/conclusion, uncertain match or no eligible entry | `formal(dsp)` | Only DSP Draft | Required |
| General theorem needs substitution, a wrapper or a different method | `formal(dsp)` | Only if DSP Draft runs | Required for all new source |
| Missing consequential premise | `needs_input` | No call | No call |
| Provider/catalog unavailable or immutable source/answer integrity fails | `failed` | No fabricated fallback | No answer |

## Draft retrieval inside DSP

The real legacy `public.dsp_drafts` catalog is a source of unverified proof strategies, including when PFI/typed publication is absent. The dedicated worker-authenticated read-only port owns credentials, top-eight vector query, embedding-fingerprint verification, canonical payload validation and exact source-content hash. Only the DSP Draft stage calls it for a request needing new Lean. No Draft alignment admission or generic-Draft migration is necessary for Recipe-first reuse.

The natural Draft query is an untrusted search hint. Generate a bounded strict JSON tree and canonical v2 OpenMath for the real legacy embedding contract. Retain actual source v4 validation/content hashes and numeric-only substitutions separately; actual cosine distance is evidence, never formal equivalence. An invalid local search hint can continue DSP without retrieved Drafts with explicit query-invalid evidence; source-integrity/provider/catalog failures remain explicit. New Lean still compiles and passes source/answer review.

## Final binding and race protection

A `catalog_reuse` settlement is claim/revision fenced like all request mutations. The authoritative API transaction revalidates admitted Recipe and reuse-entry lifecycle, exact source/target/compiler receipt/current toolchain, description digest, stored answer bytes/language/review digest, and independent review bindings to the request-context digest. Invalid source integrity cannot become a new proof job silently. Eligibility change can fall through to one formal job under the same hold; settlement replay cannot create a second job or consume/release twice. Historical answers retain original evidence if an entry is later retired.

## Provider text and durable JSON storage

Parsed provider JSON must contain Unicode scalar text compatible with PostgreSQL JSONB. Reject U+0000 and unpaired surrogates in every string and key before retaining an assessment, computing the answer hash or requesting independent QA. The strict provider schemas exclude NUL, while the local parser remains authoritative. Never strip or rewrite proof text after QA. Invalid provider text produces the existing `proof_reuse_invalid_response` failure with only earlier valid evidence and no automatic paid retry.

The API's existing recursive closed-command Unicode validator also rejects NUL before repository entry. This is a 422 input/contract rejection, distinct from a transient persistence 503. A failed operation must still persist safe failure evidence and release its original hold without losing already-recorded provider receipts. Exact valid answer bytes and independent QA binding remain unchanged. October 2's repeated square request exposed NUL in the private-evidence JSONB write; its finer nested field is unavailable from retained logs and must not be invented.

A valid request whose narrow Draft retrieval representation cannot be formed (for example unsupported OpenMath) still enters DSP with the original goal and without an unverified Draft hint. Real catalog/provider outages remain explicit failures and cannot be disguised as an empty result.
