# Authenticated feature dogfood — release blockers, October 8, 2026

Full requested runtime coverage remains blocked by product failures and missing interfaces. The approved account now has permanent complimentary Pro, verified in the public browser with 3,000,000 available monthly usage tokens and a 300,000 request limit. Project creation and metadata persistence pass. New proof submissions fail; PDF/PNG/OCR have no public entry point. No app-wide PASS is claimed.

The dogfood skill was used against public PALS in the existing Chrome tab. An independent agent prepared mathematically validated text/scanned/mixed PDF and PNG fixtures and reviewed saved evidence and answers. The coordinator alone operated the browser. Free checks ran around 20:38–20:49 JST; Pro checks around 22:59–23:13 JST. Original preferences and viewport were restored.

| Feature | Observed result |
|---|---|
| Session and Pro | Existing authenticated session survived reload. Authorized coordination with the existing Mac mini chat enabled complimentary Pro, then live Billing verified it. No purchase. |
| Project creation/save/reload | Required-name validation, creation with name/description, detail/sidebar, reload and later navigation passed. Save is automatic on creation; no separate Save control exposed. |
| Project search and chats | Match, no-match and Clear passed. Two empty Project chats persisted in overview/sidebar. Edit/rename/delete/move controls were not found in inspected screens; these operations remain unverified. |
| Pro proof submission | Two Sends in Project chat and one from overview failed with “The proof request could not be submitted.” Home Send and Retry failed too. Overview/Home left empty chats. Successful Project answer persistence remains blocked. |
| PDF, PNG and OCR | No attachment/material/OCR control or file input found in settled Pro Home, Project overview or Project chat. Fixtures were never uploaded. Processing, preview, OCR accuracy/correction and material-backed answers are blocked. Deployment owner separately reports attachment UI restoration is incomplete. |
| Natural-language answers | Earlier Free continuous-zero proof passed independent IVT/EVT review. Japanese follow-up gave a correct discontinuous counterexample. Formulas rendered. |
| Lean/formal output | Earlier coprime-divisibility job failed on submission and Retry. Two later retries produced send errors, not new completed jobs. Source disabled; compilation receipts and explanation mapping unverified. |
| Sharing | Preview failed in five recorded openings/retries across Free, current-release and Pro checks. Publication, shared view, copy and revocation blocked. |
| Settings | Representative language/notation persistence and identifier validation passed. Mathematics load failed on four recorded openings/retries across Free and Pro. Notation effect in new output unverified. |
| Usage and subscription | Two Free answers consumed two requests; formal failures preserved the remaining request. Pro failures left Used 0, Reserved 0, Available 3,000,000. Successful Pro settlement, exhaustion/reset and checkout unverified. Checkout visibly disabled and marked as being prepared. |
| Model selection | No selector found in inspected Pro surfaces; deployment owner reports it is unimplemented. Actual model identity/switching unverified. |
| Responsive/keyboard slice | 390×844 chat and Project overview/navigation inspected. Escape dismissed navigation and restored opener focus. Actual touch hardware and screen reader untested. |

The Mac mini operator separately diagnosed a missing public route for /v1/billing/token-quotes: OPTIONS returned 404 publicly and 200 at API loopback; the running gateway lacked that path. This is consistent with Pro UI failing before question creation. Original attempts' individual network traces were not captured; no claim assigns every historical failure to this route. No unrelated application repair was performed in this QA run.

Resume conditions: expose the required POST/OPTIONS quote route and recheck Pro submission; restore a user-facing attachment/material workflow for PDF/PNG/OCR; recover Mathematics, sharing and formal output for downstream checks. Fresh signup/login/reset, permanent deletion and payment were not exercised. Further passwords/authentication codes are unnecessary for the current session.

Detailed local report: outputs/dogfood/2026-10-08-pro-full/report.md; screenshots/journal/DOM: qa/; independent reviews: review/. Generated evidence and fixtures are ignored and excluded from Git. This tracked record contains no credentials, account identifiers or authentication state.
