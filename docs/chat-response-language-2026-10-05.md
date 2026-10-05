# Chat response language

The approved response-language priority is an explicit language request, the
learner's own message language, then the previous response language or the chat's
initial account/guest default. UI locale and account preferences remain separate.
The API selects and stores language before generation, for authenticated and guest
requests, premise continuations, direct proof jobs and clarification questions.

The selector accepts only the learner's text. Project OCR and material context are
bound separately and never passed into it. It removes quoted text, fenced/inline
code and delimited mathematical notation. Formulas and short confirmations retain
the preceding language. The implementation uses conservative rules for the four
supported output languages and adds no provider call. Unsupported or ambiguous
prose falls back; Han-only labels cannot reliably distinguish Japanese from Chinese.
Directly pasted source prose without quotation delimiters has no reliable source
boundary, unlike attached project materials.

Each proof request and linked Lean job keeps its selected language. Clarification
language is stored in a nullable new column: existing NULL rows retain the original
proof language and are never reclassified. A child's ambiguous question inherits
its parent's saved language. Retry retains the request's saved selection. The
frontend uses clarification language for content, preparation/failure copy and
accessible completion announcements, including after reload. Language switches do
not rewrite prior answers or Lean source.

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
