# Chat response language

## Current behavior (updated 2026-10-26)

New answers use the account's selected output language. The language of the
learner's question does not override that setting. An explicit request for another
answer language takes priority. This applies to new requests in existing chats,
material confirmations and new explanation follow-ups. Guest requests use the
selected guest output language. UI locale remains independent.

Already queued work, retries and saved answers retain their captured language;
changing a preference does not translate historical answers. Material/OCR text
never changes the answer language. The previous automatic input-language selection
was superseded after production QA showed Japanese answers while English was
selected in settings.

The sections below record the earlier migration and its historical validation;
they do not establish deployment of the 2026-10-26 correction.

## Database release

The appended `reply-language` release step replaces the proof-job/chat composite
language binding with an ownership binding while retaining explicit four-language
checks. It also adds clarification language storage. Existing chat defaults and
historical data remain intact. Runtime preflight requires this step before serving
the new API; run the normal database release before deploying the API. Production
and local legacy release paths include the step. The restricted signed Mac upgrade
allowlist has not been expanded, so that special upgrade path does not yet admit it.
No running application database, deployed service or active browser was changed.

## Verification

- API/service/schema/contract regressions: 277 passed. OpenAPI generation check,
  affected Python lint and language-selector type checks passed.
- Request, guest and project-material PostgreSQL tests: 34 passed, using disposable
  databases. This includes Japanese questions with an English default, English PDF
  pages, language switching, replay, quota preservation and retry.
- New database migration and a Japanese request in an English chat through formal
  settlement, linked-job persistence and reload: 9 passed.
- Separate PostgreSQL tests passed for clarification language persistence/reload,
  original chat migration compatibility and canonical PJR/PEX compatibility.
- Frontend settings, clarification rendering/API/polling tests: 90 passed. Typecheck
  and affected ESLint checks passed.

Broader release fixtures stopped at token-accounting readiness, recipe reader
provisioning or billing references outside the new language step. Complete
production readiness and the special signed Mac upgrade remain unverified. These
results establish the affected application and storage paths, not a deployment.
