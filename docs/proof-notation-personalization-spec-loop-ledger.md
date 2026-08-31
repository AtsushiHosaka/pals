# Proof Notation Personalization — Specification Loop Ledger

## Iteration record

| Iteration | Spec revision | Code revision | Trigger | Expected verdict-changing delta | New evidence | Findings opened/closed | Routes invoked | Stage/overall budget | Elapsed | Stop/cancel action | Result |
|---|---|---|---|---|---|---|---|---|---:|---|---|
| 0 | Parent `8bd6dd7`; no current focused frontend spec | Webfront `c21a63c` | User request: let a learner replace proof notation with preferred symbols in the frontend | Establish canonical baseline | Rendered learner math is used in explanations and clarification answers; the verified Lean source is separately shown; math currently has a source-based accessible alternative | Opened D-01 and D-02 | `sdd-review-spec` baseline | 30 min / two iterations | — | Baseline completed | PASS |
| 1 | Parent `8bd6dd7` (dirty); Webfront `c21a63c` (dirty) | No code change | User selected display-only substitution | Make the selected presentation boundary traceable | New focused frontend spec with `PNP-001`–`PNP-003`; Lean source remains exact | Closed D-01; opened D-02 | `sdd-update-spec` → targeted `sdd-review-spec` | 30 min / two iterations | — | Awaiting D-02 | BLOCKED |
| 2 | Parent `8bd6dd7` (dirty); Webfront `c21a63c` (dirty) | No code change | User selected account-wide, cross-device persistence | Add account lifecycle and cross-repo product requirement | `CORE-010`, `PNP-004`–`PNP-007`; existing account-preferences endpoint is output-language-only and exact-shape clients require a new compatible API contract | Closed D-02; opened D-03 | `sdd-update-spec` → targeted `sdd-review-spec` | 30 min / two iterations | — | Iteration budget reached; awaiting D-03 | BLOCKED |
| 3 | Parent `8bd6dd7` (dirty); Webfront `c21a63c` (dirty); API `5bd33e2` (dirty) | No code change | User selected arbitrary replacement text | Start a new bounded continuation and define untrusted replacement-text handling plus the API-owned resource | `PNP-008`–`PNP-009`, `APNP-001`–`APNP-006`; new dedicated API resource avoids changing the exact output-language endpoint | Closed D-03; opened D-04 | `sdd-update-spec` → targeted `sdd-review-spec` | 30 min / two iterations | — | Awaiting D-04 | BLOCKED |
| 4 | Parent `8bd6dd7` (dirty); Webfront `c21a63c` (dirty); API `5bd33e2` (dirty) | No code change | User selected variable/function identifiers and continuous frontend collision monitoring | Complete the source scope, profile limits, collision behavior, and catalog versioning | `PNP-010`–`PNP-012`, `APNP-007`; exact collision fallback is standard whole-expression presentation | Closed D-04; targeted review found no P0/P1 specification gap | `sdd-update-spec` → targeted `sdd-review-spec` | 30 min / two iterations | — | Converged at specification boundary | PASS |
| 5 | Same dirty baselines | No code change | Implementation discovery: identifier names cannot be enumerated in a finite catalog | Reconcile source-ID validation with arbitrary variable/function identifiers | Static catalog IDs plus derived NFC-token ID grammar; no user-visible scope changed | Closed source-ID contradiction | `sdd-update-spec` → `sdd-implement-spec` | 15 min / implementation workflow | — | Resume implementation | PASS |
| 6 | Same dirty baselines | No code change | Implementation discovery: static catalog needs one runtime owner | Prevent API/webfront catalog drift | Dedicated API returns the versioned static catalog with the profile | Closed catalog-ownership gap | `sdd-update-spec` → `sdd-implement-spec` | 15 min / implementation workflow | — | Resume implementation | PASS |
| 8 | Same dirty working specifications | API `5bd33e2` + webfront `c21a63c` working trees | Implementation audit found PNP-004/PNP-007 live authentication evidence missing | Replace mocked HTTP-only confidence with real account/session evidence | Isolated PostgreSQL 16, real Cognito, local API and Chromium; primary save, fresh primary context restore, and distinct secondary-account isolation all passed | Closed the fresh-context persistence and account-isolation gap; opened I-08b for same-page account switch and real Learner-math application | `sdd-implement-spec` → `$sdd-generate-tests` → `$sdd-audit-implementation` | Verification continuation | — | Continue with I-08b before completion | PARTIAL |

## Delegation record

| Delegation ID | Agent/skill | Owned slice | Mode/owned paths | Input revisions | Prompt summary | Stage/command budgets | Required verification | Result revision/status | Evidence and NOT VERIFIED | Elapsed/retries/stop action | Next route |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DEL-APNP-001 | `/root/api_notation_preferences` | `APNP-001`–`APNP-007`, `APNP-T001`–`T004` | Implementation; `pals-api/**` only | Parent `8bd6dd7`, API `5bd33e2`, working specs | Dedicated owner-scoped profile resource, static catalog, derived IDs, migration, tests; preserve output-language endpoint | 90 min; commands <=60 s; two retries | Focused API, repository/migration, and contract tests | Complete (WORKING) | Focused selection: 34 passed, 1 default-environment PostgreSQL case skipped; temporary PostgreSQL 16 integration passed. ruff, mypy, generated OpenAPI check, and diff check passed. | One repair/re-review cycle; closed | FastAPI architecture review PASS |
| DEL-PNP-001 | `/root/webfront_notation_personalization` | `PNP-001`–`PNP-012`, `PNP-T001`–`PNP-T010` | Implementation; `pals-webfront/**` only | Parent `8bd6dd7`, webfront `c21a63c`, working specs | Scoped settings/client, safe learner-math renderer, continuous collision monitor, tests; no API/spec edits | 100 min; commands <=60 s; two retries | Focused component/unit tests, typecheck, relevant regression subset | Partial (WORKING) | 55 unit files / 560 tests, 6 story files / 24 tests, lint, typecheck, and diff check passed. Iteration 8 added and passed a separate no-global-setup real Cognito/API/Chromium suite: a primary account saves a rule, a fresh primary context restores it, and a temporary distinct Cognito account observes its own empty profile. It does not yet prove real Learner-math application after restoration or an in-place account switch. | Two renderer repair/re-review cycles plus live E2E audit repair; I-08b open | Add real learner-math and same-page switch evidence |

## Human decision queue

| Decision ID | Actor + trigger/state + observable question | Known facts | Options and impact | Recommendation | Affected IDs | Answer/authority | Resulting spec revision | Status |
|---|---|---|---|---|---|---|---|---|
| D-01 | Learner viewing proof-related math: which surfaces may substitute notation? | The frontend renders learner explanation/answer math and exposes a separately verified Lean source. | Learner rendering only; also source view; per-view temporary substitution. | Learner rendering only, so proof source and verification identity remain exact. | `PNP-001`–`PNP-003` | User selected option 1 | Uncommitted focused spec after parent `8bd6dd7` / webfront `c21a63c` | Closed |
| D-02 | Learner who has set notation preferences: where are they retained and when do they apply? | The frontend already has an account-preferences API for output language, but no notation-preference contract. | Browser only; account-wide; current proof only. | Browser only if this is strictly frontend scope; account-wide requires API and data-contract scope. | `CORE-010`, `PNP-004`–`PNP-007` | User selected option 2 | Uncommitted focused spec after parent `8bd6dd7` / webfront `c21a63c` | Closed |
| D-03 | Learner editing their notation setting: what values can they choose? | A persisted profile requires a validated, renderable, and unambiguous rule set. | Curated individual substitutions; arbitrary text; named presets. | Curated individual substitutions preserve personal choice while protecting mathematical and accessible rendering. | `PNP-008`–`PNP-009`, `APNP-001`–`APNP-006` | User selected option 2 | Uncommitted focused specs after parent `8bd6dd7`, webfront `c21a63c`, API `5bd33e2` | Closed |
| D-04 | Learner choosing a source for an arbitrary replacement: which pieces of a formula are configurable? | A rule needs a stable source identity; arbitrary text alone does not decide whether operators, variables, or any formula fragment can be targeted. | Operators/relations only; include identifiers; arbitrary formula fragments. | Operators/relations only preserves proof readability and permits unambiguous source IDs. | `PNP-010`–`PNP-012`, `APNP-003`, `APNP-007` | User selected identifiers and required continuous client-side collision monitoring | Uncommitted focused specs after parent `8bd6dd7`, webfront `c21a63c`, API `5bd33e2` | Closed |

## Requirement evidence

| Requirement | Design | Task | Code revision/location | Test/runtime evidence | Freshness | Status | Owner/next action |
|---|---|---|---|---|---|---|---|
| CORE-010 | `pals-webfront/specs/proof-notation-personalization/design.md`: Account preference lifecycle; `pals-api/specs/account-notation-preferences/design.md` | `PNP-T003`–`PNP-T005`; `APNP-T001`–`APNP-T004` | Dedicated API resource, account hook, settings UI, owner-scoped repository/migration | API contract/service/repository tests, temporary PostgreSQL integration, webfront API/hook/settings tests, plus Iteration 8 real Cognito/API/Chromium cross-context persistence/isolation | Fresh on WORKING baseline | Partial: real restored Learner math and in-place account switch remain unproven | Implement I-08b and re-audit |
| PNP-001–PNP-003 | `design.md`: Scope and boundary and Accessibility | `PNP-T001`, `PNP-T002` | `pals-webfront/lib/learnerRichText.ts`; `components/LearnerRichText.tsx`; proof/clarification wiring | 560 frontend unit tests include visual/ARIA, source-boundary, structured-math regressions | Fresh on WORKING baseline | Implemented; live E2E NOT VERIFIED | Run browser flow against API |
| PNP-004–PNP-009 | `design.md`: Account preference lifecycle and Arbitrary replacement text | `PNP-T003`–`PNP-T007` | `pals-webfront/lib/api/accountPreferences.ts`; `hooks/useAccountNotationPreferences.ts`; account settings | Client, account-switch, arbitrary-text safety and failure-path tests; dedicated real-Cognito Playwright save/restore/isolation | Fresh on WORKING baseline | Partial: PNP-004 real learner-math application and PNP-007 in-place account switch remain unproven | Implement I-08b and re-audit |
| PNP-010–PNP-012 | `design.md`: Configurable symbols and collision monitor | `PNP-T008`–`PNP-T010` | Public KaTeX MathML tokenizer and formula-local collision monitor | Identifier, collision, TeX control word, duplicate visual leaf, fraction/root/sum tests | Fresh on WORKING baseline | Implemented; live E2E NOT VERIFIED | Run browser flow against API |
| APNP-001–APNP-007 | `pals-api/specs/account-notation-preferences/design.md` | `APNP-T001`–`APNP-T004` | `pals-api/app/api/routes/auth.py`; domain/service/repository/migration | 34 focused tests passed, temporary PostgreSQL migration/durability/owner-scope integration passed; ruff/mypy/OpenAPI check passed | Fresh on WORKING baseline | Implemented | Run live browser/API E2E for the cross-repo lifecycle |

## Final report

# Specification Loop Result

Status: PASS
Objective and approved scope: Define a learner-facing proof-notation personalization feature. User-authorized scope is learner math in proof explanations and clarification answers, persisted per authenticated account and available across devices. Lean source and proof data remain unchanged.
Final spec revision: Uncommitted changes after parent `8bd6dd7`, webfront `c21a63c`, and API `5bd33e2`; each worktree had unrelated user-owned changes before this loop.
Final code revision: No code change.

## Iterations and routing

- Baseline review established the learner-rendering/verified-source boundary and found no existing current focused frontend spec.
- Iteration 1 applied the user-selected display-only boundary as `PNP-001`–`PNP-003`; targeted review routed account lifetime to D-02.
- Iteration 2 applied the user-selected account-wide lifetime as `CORE-010` and `PNP-004`–`PNP-007`; targeted review routed the profile value domain to D-03.
- Continuation iteration 3 applied arbitrary replacement text as `PNP-008`–`PNP-009` and added `APNP-001`–`APNP-006`; targeted review routed the configurable source-symbol range to D-04.
- Continuation iteration 4 applied the user-selected variable/function scope, continuous collision monitor, versioned catalog, and validation limits as `PNP-010`–`PNP-012` and `APNP-007`; targeted review closed the final material decision.

## Requirement evidence

The matrix above records the current `CORE-010`, `PNP-001`–`PNP-012`, and `APNP-001`–`APNP-007` mappings. Every in-scope requirement is traceable through design and task artifacts. Implementation, API, migration, test, and runtime evidence remains NOT VERIFIED because this task was specification-only.

## Invalidated or NOT VERIFIED evidence

- The existing API account-preferences endpoint and webfront client accept only an exact output-language payload. Implementation must add the specified dedicated resource without changing that contract.
- No renderer, accessibility, multi-device, account-isolation, or failure-path test exists for this feature.

## Human decisions

- Resolved: substitutions apply only to learner math, never to Lean source or verification data.
- Resolved: settings persist per authenticated account and are retrieved across devices.
- Resolved: each configurable source can have an arbitrary user-authored replacement string, treated as text rather than executable or markup input.
- Resolved: configurable sources include complete variable/function identifiers and operator, relation, and logical symbols; the frontend continuously rejects ambiguous presentation.

## Stop reason

Converged: all material user-visible decisions in the approved scope are testable and traced. The initial loop ended after two iterations; the next user decision began and completed one bounded continuation.

## Further iteration requires

Implementation only. Start with API task `APNP-T001` and frontend token/collision task `PNP-T008`; preserve the explicit source, security, accessibility, and no-partial-rendering constraints.

## Implementation continuation (Iteration 7)

Status: implementation-only PASS on the WORKING baseline. This was not a completion or release-readiness verdict.

- API now provides an account-scoped, catalog-versioned profile through the dedicated notation-preferences resource, with atomic validation and persistence. The existing output-language preference endpoint was not changed.
- Webfront now loads/saves that profile in account settings and applies it only to learner-facing explanation and clarification math. Lean source and API proof payloads are not transformed.
- The renderer uses public KaTeX MathML to identify configurable semantics, then applies literal text replacements only after verifying a complete, unambiguous visual mapping. Ambiguous formulas retain standard visual and accessible notation; structured formulas with a unique target remain personalizable.
- Final API and Next.js architecture re-reviews found no P0/P1/P2 issues in their respective deltas.

Fresh execution evidence is recorded in the delegation and requirement matrices. At this point, a live authenticated browser/API E2E run with two sessions was still NOT VERIFIED; it is closed by Iteration 8 below. No files were staged or committed.

## Audit correction and Iteration 8 result

The earlier implementation-only PASS was too easy to read as task completion while the audit still classified `PNP-004`, `PNP-007`, `PNP-T003`, `PNP-T004`, and `PNP-T005` as partial. That wording is corrected here: the implementation was not considered complete until the missing real authentication evidence was obtained and audited.

Iteration 8 used an isolated PostgreSQL 16 Compose project, the local Cognito emulator, a locally started API, and Chromium. A dedicated Playwright configuration deliberately has no proof-fixture global setup because this account-settings lifecycle does not require a proof fixture. It verifies all of the following without route interception, copied browser storage, test-only identity substitution, or mocked fetch:

- Primary account: read the API-owned profile, edit and save a notation rule through the visible settings UI, and receive a bearer-authenticated `PUT` success response.
- Fresh primary browser context: sign in again, receive the persisted profile through a real `GET`, and see the saved field value in the visible settings UI.
- Fresh distinct Cognito account: receive an empty profile and an empty corresponding settings field, proving that the primary account’s rule did not cross the authenticated-account boundary.

The exact execution passed on 2026-08-10: `npm exec -- playwright test --config=playwright.notation-preferences.config.ts` (1 passed). The test restores the primary rule in `finally`; the temporary secondary Cognito user is deleted by the isolated test-run harness. It was followed by `npm run test:unit` (55 files, 560 tests), `npm run test:story` (6 files, 24 tests), `npm run lint`, `npm run typecheck`, and `git diff --check`, all passing. The next `$sdd-audit-implementation` verdict is **FAIL/PARTIAL** for the selected implementation scope: the fresh-context lifecycle is proven, but real restored Learner math and an in-place account switch are not. It is still not a deployment or production-release claim.
