# Guest chat: three daily submissions

Working contract: the user's 2026-10-04 clarification permits three messages per JST calendar
day while logged out. Both an initial mathematics question and each reply to a clarification
consume one submission. The existing shared-network restriction and global cap remain; the
global cap now includes clarification submissions. Exact idempotent replay, status reads,
rejected input, and rejected state changes do not consume allowance. Accepted work that later
fails still counts. At midnight JST the allowance resets, including for a pending clarification.

## Implementation

The API uses one transactional admission path for initial questions and clarification replies.
It locks the same durable session/network/global budgets and returns the smallest remaining
allowance in the range 0–3. Clarification admission is recorded by request/revision. The frontend
accepts 0–3 and disables both question and clarification sending at zero. The public landing
page, FAQ, guest introduction, and failure/limit messages describe the same policy in all four
supported languages. Account billing limits were not changed.

`002_daily_messages.sql` upgrades the existing guest schema after validating its recorded SQL,
schema fingerprint, and original key. It removes the old session/day unique constraint and adds
clarification admissions. Existing sessions, questions, accepted counts, and the key are retained.
Previously free clarification replies are not charged retrospectively. Serving checks readiness;
it does not migrate. The same guest release command installs fresh databases and upgrades the
exact previous schema. Drift and key changes are rejected.

## Verification

- Frontend guest/public tests: **67 passed**; typecheck and targeted ESLint passed.
- API guest boundary tests: **16 passed**; guest PostgreSQL integration: **17 passed**.
- Legacy migration, preservation, concurrent release, rollback, and drift tests: **5 passed**.
- Normal proof-request/chat/health regressions: **97 passed**.
- Targeted Ruff and production-file mypy passed. Independent source review found no actionable
  issue in quota, replay, concurrency, daily reset, network authority, or upgrade paths.
- Real PostgreSQL tests used uniquely named disposable databases on the existing service and
  removed those databases. No additional database or application service was created.
- The earlier frontend full-suite baseline had two existing `auth-loss.test.tsx` failures in
  Cognito password-challenge test setup. This change did not modify that code.
- Japanese copy passed Yomiyasu lint/diff and manual review. Natural Japanese lint could not run
  because its dependency was absent and registry DNS was unavailable; its manual checklist was
  applied instead.

## Local runtime

Existing `pals-local-api-1` and `pals-local-webfront-1` were updated with versioned images
`pals-api:guest-three-messages-20261004` and `pals-webfront:guest-three-messages-20261004`.
The API image overlays only the guest files on the running materials image. Parallel materials
work later rebuilt the active API as `pals-api:materials-20261004`; its core, repository, route,
and guest migration file hashes match this change exactly. The active Compose
configuration was retained and extended with the git-ignored
`.local/e2e/guest-three/compose.json` image override. PostgreSQL and the worker were reused.
The schema release preserved the original guest key. Both services became healthy; `/health`
and `/try` returned 200. A real guest session returned one remaining message after the existing
one-message consumption and one additional browser submission; private chat history returned
401 for that cookie.

The browser displayed the new clarification-inclusive three-message copy and accepted a real
mathematics question. Request `98de32fe-5d02-43fe-ba5f-8a183ff41b45` recorded three model calls,
but finished `failed` with `proof_reuse_provider_unavailable`. A successful real-provider answer
is therefore **not verified** in this run. The browser also showed a connection recovery notice
while that request was pending. No repeated questions or quota resets were used to hide this
failure. The admission/state behavior is verified separately by the actual PostgreSQL tests.

Public production ingress/deployment was not changed or verified. Existing guest source files
were already untracked before this chat; their earlier changes have not been staged or committed.

Final inventory: the existing API and Web services are healthy; the unrelated reconciler is
restarting. No service was duplicated. The source delta remains available locally for commit
after resolving ownership of the previously untracked guest feature.
