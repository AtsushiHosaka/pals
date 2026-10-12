# Pro QA issue batch: fixes and investigation evidence

Issues #36–#41 were created on 2026-10-09 at 00:44–00:45 JST. All six received the existing `in progress` label. Implementation PRs remain reviewable separately; this parent change pins their pushed sources. No merge, deployment, production migration, public sharing, or new production proof request was performed.

| Issue | Finding and change | Remaining verification |
| --- | --- | --- |
| #36, private sharing preview | Read-only inspection of the existing approved Pro session reproduced an OPTIONS 404 for `/v1/chats/{id}/share`; Chrome reported `PreflightMissingAllowOriginHeader`. The preview API was never reached. Infrastructure PR #16 adds exact UUID4 GET/OPTIONS routes for private share settings and preview. | Install through the protected host process, then verify the same Pro preview and retry. This does not establish a database permission defect. |
| #37, formal-proof request | The saved failed request returns `proof_reuse_unsupported`, revision 6, and `formal_job_id: null`. Frontend PR #11 explains that request assessment stopped before Lean verification. A local complete formal fixture of the requested theorem compiles successfully. | Privately inspect the corresponding claim evidence to distinguish premise rejection, unsupported assessment, or capability restrictions. No deployed generated proof or compiler receipt was obtained. |
| #38, rejected Home answer | The QA report records one rejected answer followed by successful Retry. Source inspection confirms that each claim retains its own private evidence, including the assessed candidate and independent review rationale where available. | Inspect both attempts privately before judging whether rejection was justified. No false-positive reviewer defect or repair is claimed. |
| #39, follow-up context | API worker claims previously supplied only the current request and its clarification turns. The API now freezes bounded preceding completed turns from the same owner and chat; the agent uses them in premise resolution, generation, and independent review. Receipt hashing includes the frozen history. Catalog fallback retains the resolved goal. | A deployed provider-backed follow-up without restatement remains unverified. |
| #40, clarification language | Project and standalone clarification composers selected labels from answer language. Frontend PR #11 uses interface locale while retaining saved answer languages. | Deployed Japanese/English switching remains unverified. |
| #41, materials and OCR access | The Project overview materials panel had been removed while the API/client remained. Frontend PR #11 restores PDF/PNG upload and management for active paid and complimentary Pro access. | Real deployed upload, extraction/OCR, project association, and reload persistence remain unverified. Control availability alone does not complete this issue. |

Implementation PRs:

- [Infrastructure #16](https://github.com/AtsushiHosaka/pals-infra/pull/16): private sharing routes, `7fffc7e9c8750011ef171a0e89727171dcec474b`.
- [Frontend #11](https://github.com/AtsushiHosaka/pals-webfront/pull/11): clarification labels, Project materials, and bounded failure copy, `24ae8b427d535b33cddbfb94a6c888b4359edd05`.
- [API #9](https://github.com/AtsushiHosaka/pals-api/pull/9): frozen conversation context and catalog fallback, `0f1d34a7fc5ec089cda3b5f1460cb0a575be1d43`.
- [Agent #6](https://github.com/AtsushiHosaka/pals-agent/pull/6): context-aware premise resolution, generation, review, and receipt identity, `b96aa1aa49263e5cc78b1a0d1d0dc67c982a7572`.

Merge the reviewed child PRs before the parent integration PR. The API and agent history changes require coordinated rollout; the sharing edge file requires protected host installation separately from merely advancing a source pin.

## Validation

- Frontend: 96 targeted tests across nine files, full lint, TypeScript checks, and production build passed at `24ae8b427d535b33cddbfb94a6c888b4359edd05`. Transport and extraction results in these tests are mocked.
- Sharing edge: 15 real Caddy 2.10.2 HTTP tests passed at infrastructure `7fffc7e9c8750011ef171a0e89727171dcec474b`, including bearer forwarding, upstream anonymous rejection, CORS behavior, retry after 503, and rejection of public/internal/invalid routes. Nine API share tests separately passed against disposable PostgreSQL 16 data.
- Context changes: 109 focused agent tests, 86 API unit regressions followed by seven focused history/convention tests, and 14 PostgreSQL 16 history/request-lifecycle tests passed. A separate reviewer ran 18 history/convention unit tests successfully. Lint and targeted type checks passed. Independent source review caught the catalog fallback losing its referent, which was corrected and regression-tested before publication. A broader ten-test catalog integration suite failed during fixture setup in `LeanRecipeCatalogMigrator.apply`; its catalog lifecycle database coverage remains unverified. The canonical release gate was not changed to make that fixture pass.
- Local Lean: `pals-scripts/fixtures/coprime-divisibility.lean` compiled with exit 0 using Lean `4.32.0-rc1` (`b4812ae53eea93439ad5dce5a5c26591c31cb697`) and mathlib `8b62164d808cd0f23b7d8cc28190a6c1a1bb483a`. The existing local workspace was reused. This proves only the checked fixture, not a model-generated artifact or deployed job.
- Parent: the three operator-workflow boundary tests and the parent-only checkout secret scan passed. The initialized multi-repository scan reports four pre-existing matches (index and worktree in each of the agent/infra synthetic credential test fixtures); those files are unchanged by this batch. The parent-only scan matches the workflow's pre-submodule scan order.

## Private attempt correlation for #37 and #38

Public request history omits rejected candidates and reviewer rationales. A successful Retry does not replace the per-claim evidence: `public.proof_request_claims` stores `request_id`, `revision`, `created_at`, `settlement_sha256`, and `private_evidence`. The current request projection alone cannot explain an earlier rejected attempt.

The next operator inspection should use the existing authorized database path and a read-only transaction, scoped to the request identifier from the approved browser. This query is a reviewable investigation recipe; it was **not run against production** in this task:

```sql
BEGIN READ ONLY;
SET LOCAL statement_timeout = '5s';
SELECT revision, created_at,
       settlement_sha256 IS NOT NULL AS settled,
       private_evidence->>'phase' AS phase,
       private_evidence#>>'{preflight,action}' AS premise_action,
       private_evidence#>>'{primary_assessment,action}' AS assessment_action,
       private_evidence#>>'{token_qa,approved}' AS token_review_approved,
       private_evidence#>>'{answer_qa,approved}' AS answer_review_approved,
       private_evidence ? 'token_qa_rationale' AS token_rationale_retained,
       private_evidence ? 'answer_qa_rationale' AS answer_rationale_retained
FROM public.proof_request_claims
WHERE request_id = $1::uuid
ORDER BY created_at, revision
LIMIT 20;
ROLLBACK;
```

If the diagnostic confirms review rejection, assess the privately retained candidate against the exact original request, hypotheses, requested compactness argument, formatting, and language. Keep the candidate and rationale out of GitHub comments and runner logs; publish only the justified finding and sanitized conclusion. Preserve independent review rather than turning an observed rejection into an approval bypass.

The existing browser session was reused for the read-only checks. Account information, credentials, private conversation URLs, request identifiers, and raw screenshots are omitted from this note. #36–#39 and #41 remain investigations until their outstanding runtime criteria are demonstrated; opening a PR does not establish deployed recovery.
