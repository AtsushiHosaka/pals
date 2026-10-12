# Issue #14: intermittent guest answer failure

Issue: https://github.com/AtsushiHosaka/pals/issues/14

The original report observed one failed accepted integral question followed by one successful
resubmission on 2026-10-08, 11:44–11:55 JST (02:44–02:55 UTC). It did not record the request IDs,
exact deployed revision, private generation evidence, or allowance changes. This observation
does not establish a cause or failure rate. No causal implementation fix or PR is justified yet.

## Verified source and tests

- Agent source inspected: `5cea0376c05e3dca528b0ae570dab2bb3eb628e6` (`origin/main`).
- Existing `test_proof_reuse.py`, `test_proof_request_worker.py`, and `test_openai.py`:
  **72 passed** using isolated provider fixtures; no production request was submitted.
- The agent retains assessment phase, sanitized provider diagnostics, and independent review
  evidence in settlement data. The API stores it in `public.proof_request_claims.private_evidence`.
- Provider failures do not trigger another paid attempt or model escalation. Review rejection
  prevents publication. These are required safeguards, not demonstrated defects.
- `GUEST-003` and `docs/guest-daily-message-limit-2026-10-04.md` explicitly count accepted
  failures toward three daily messages. Exact idempotent replay, reads, and rejected input/state
  do not consume allowance. A new accepted resubmission consumes another message. The existing
  guest failure copy describes this policy. Production allowance changes remain unverified.

## Missing original records

Run the following only through an authorized production reader, inside a read-only transaction.
It outputs request/claim IDs and bounded diagnostic fields, without question/answer text,
owner IDs, cookies, credentials, or network/session hashes. The mathematical substring is a
candidate filter, not proof that a row belongs to the original browser run. Correlate returned
IDs with original browser/network artifacts before attributing a failure.

```sql
BEGIN READ ONLY;
SET LOCAL statement_timeout = '5s';
SELECT r.id AS request_id, r.status, r.error_code, r.created_at,
       r.updated_at, a.day AS admitted_jst_day,
       c.claim_id, c.revision AS claim_revision, c.created_at AS claim_created_at,
       c.private_evidence->>'phase' AS phase,
       c.private_evidence->'provider_failure'->>'stage' AS provider_stage,
       c.private_evidence->'provider_failure'->>'http_status' AS provider_http_status,
       c.private_evidence->'provider_failure'->>'provider_code' AS provider_code,
       c.private_evidence->'provider_failure'->>'transport_kind' AS transport_kind,
       c.private_evidence->'provider_failure'->>'incomplete_reason' AS incomplete_reason,
       c.private_evidence->'answer_qa'->>'approved' AS answer_review_approved,
       c.private_evidence->'token_qa'->>'approved' AS token_review_approved,
       c.private_evidence->>'worker_elapsed_ms' AS worker_elapsed_ms
FROM public.proof_requests r
JOIN pals_guest_chat.admissions a ON a.request_id = r.id
LEFT JOIN public.proof_request_claims c ON c.request_id = r.id
WHERE r.created_at >= TIMESTAMPTZ '2026-10-08 02:44:00+00'
  AND r.created_at < TIMESTAMPTZ '2026-10-08 02:56:00+00'
  AND r.owner_user_id LIKE 'guest:%'
  AND r.statement LIKE '%int_0^1%'
ORDER BY r.created_at, c.created_at;
ROLLBACK;
```

Inspect all claims for each confirmed request, including settlement failure logs keyed by its
request/claim IDs. Compare the failed and successful request's phases, provider diagnostics,
review approval, and usage/admission ledgers. A present-day budget count alone cannot recover
the remaining allowance displayed at the original send time. Do not reset quota or create new
production questions to replace the missing original evidence. Leave #14 open until the cause
and original quota behavior are established; screenshots alone cannot establish either.
