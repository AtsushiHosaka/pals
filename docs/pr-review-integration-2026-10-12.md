# PALS PR review and integration — 2026-10-12

The user requested review, repair, and merge of all open PALS pull requests. The initial inventory contained 24 PRs across the parent and its implementation repositories. Three additional focused repair PRs address defects found during review. The final inventory then found frontend #19 and parent #51 for a collapsible math keyboard; they are included in the same review and merge scope, bringing the total to 29 PRs. Deployment is outside this request; the live `MACMINI_AUTO_DEPLOY` variable was verified as `false` and left unchanged.

| Repository | Initial PRs | Review repairs |
|---|---|---|
| pals | #42, #43, #44, #45, #47, #48, #49 | Reconcile every overlapping pin to the reviewed child mains; retain historical QA limits and the working context specification |
| pals-webfront | #11, #15, #16, #17, #18 | Preserve materials controls, remove duplicated controls, fix upload cancellation/navigation races and source routing, make SSE fixtures deterministic, retain centered placeholder |
| pals-api | #8, #9, #10, #11 | Refresh OpenAPI; preserve both theorem history and multimodal history; repair image-only catalog fallback in #12 |
| pals-agent | #5, #6, #7 | Bind catalog review to original text, full frozen history, and every image/PDF page; preserve the original correspondence digest; construct synthetic scanner-test keys at runtime |
| pals-infra | #15, #16, #17, #18, #19 | Preserve the existing canonical token-quote route and actual HTTP coverage; add real attachment-route HTTP checks; construct synthetic scanner fixtures at runtime |

The datasets and observability repositories had no open PRs. `pals-draft-admin` is not configured as a submodule here and its repository lookup was unavailable.

## Review and validation

Independent local reviewers examined the changes and rechecked the integrated revisions. Automatic approval review rejected CodeRabbit CLI uploads of private API/frontend source because external disclosure was not authorized. Those uploads were not retried or bypassed. Existing CodeRabbit SUCCESS statuses, including draft-review skips, were not treated as evidence of independent review.

- Frontend: 1,639 tests pass, with lint, TypeScript, and production build passing. Actual shared composer checks at 1280×900 and 390×844 cover wrapped Japanese placeholders, typed English, and mobile overflow. The late math-keyboard review also covers selection replacement, caret/focus restoration, Escape, blocked IME actions, strict KaTeX labels, and a bounded mobile palette. Temporary QA pages and task-owned browser/server resources were removed; an unrelated existing browser session was left intact.
- API: 2,094 unit tests pass and one is skipped. The final repair has 118 related PostgreSQL/contract checks passing, including image-only catalog fallback, immutable original input, idempotent settlement, and rejection of route/receipt/preflight tampering. OpenAPI freshness, scoped Ruff, and strict mypy pass. PostgreSQL used an isolated temporary test environment that was removed.
- Agent: 271 relevant proof/chat/image/PDF/history/client/meter/worker checks pass after the source-binding repair; scoped Ruff passes. The independent reviewer verified API-compatible receipt hashes and complete historical source input. The public wheel boundary gate passes.
- Infrastructure: 149 host checks pass with one dedicated signed-predecessor PostgreSQL fixture skipped; edge and attachment HTTP checks pass using real Caddy fixtures. The machine-auth monitor has 16 Node and 42 Python checks passing. Temporary Caddy resources were removed.
- Parent: 85 deployment-controller, checkout, main-revision, and operator-workflow checks pass with isolated local listeners. The strict initialized-repository secret gate and public wheel boundary are checked for final integration.

Counts overlap between targeted runs and are not summed. A broader agent unit run encountered unavailable Mathlib/compiler prerequisites and legacy parent-fixture expectations; this does not establish a complete agent/compiler regression pass. Model/provider calls and catalog/compiler receipts in contract tests use explicit doubles.

## Integration and release boundaries

Each child change was pushed and merged before its final parent pin. The parent PR merge trees retain all their documentation changes, the current feature-preservation policy, and the same final reviewed child mains. Conflicts were resolved only for submodule pins, without resetting or stashing existing work. Normal exact-head merges were used; no force pushes or required-check bypasses were used.

The signed v7 registry append, SQL bytes, manifest hashes, and explicit host capability checks remain unchanged. Existing user-facing controls, guest/member sources, review gates, and private evidence were preserved. The context specification remains a working proposal; merging it does not make unresolved product requirements complete.

No production migration, AWS provisioning, host installation, deployment, live provider interpretation, or real generated Lean proof is claimed. Earlier QA reports retain their original dates and unverified boundaries. This document records source integration and the stated local/CI evidence only.
