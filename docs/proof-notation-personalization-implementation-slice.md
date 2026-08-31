# Proof Notation Personalization — Implementation Slice

## Baseline authority

- Authority: WORKING.
- Source files/revisions: parent `8bd6dd7`, webfront `c21a63c`, API `5bd33e2`; the new specification files are uncommitted and all worktrees contained unrelated user-owned changes before this slice.
- Selected IDs: `CORE-010`; `PNP-001`–`PNP-012` / `PNP-T001`–`PNP-T010`; `APNP-001`–`APNP-007` / `APNP-T001`–`APNP-T004`.
- Why sufficient: the user explicitly requested implementation after resolving every material product decision in the specification loop.
- Material assumptions: the dedicated API resource may be introduced without changing the existing output-language endpoint; a supported structured tokenizer can be implemented without using KaTeX's private parser API.
- Governance gaps: specifications are uncommitted working artifacts, not a promoted release baseline.
- Claims not made: canonical task completion, deployment readiness, or release readiness.

## Slice plan

| Requirement / criterion | Task | Production path | Failure/state/persistence behavior | Verification |
|---|---|---|---|---|
| Account-owned versioned profile | `APNP-T001`–`T004` | API domain, repository, migration, authenticated route | Atomic replacement; reject invalid, foreign, or unknown-version profiles without changing stored state | API, migration, repository, contract tests |
| Settings lifecycle | `PNP-T003`–`T007` | Webfront API client, scoped hook, account settings UI | Apply only confirmed current-account settings; retain confirmed/standard state on failure | Component and API-client tests |
| Safe learner-math presentation | `PNP-T001`–`T002`, `T008` | Structured learner-math rendering | Do not mutate source/Lean/API payload or interpret replacement text as markup/commands | Renderer, source-boundary, accessibility tests |
| Collision monitor | `PNP-T009`–`T010` | Settings validation and per-expression rendering | Show named conflict; whole expression uses standard notation, including accessible representation | Collision, identifier, account-transition tests |

## Execution budget

- Parent workflow ceiling: six wall-clock hours.
- API slice: 90 minutes. Webfront slice: 100 minutes. Integration/review: 45 minutes.
- Command timeouts: normally 60 seconds; no more than two transient retries.
- No-progress stop: two consecutive cycles without new evidence, change, or verification progress.
- Cancellation owner: root agent.

## Verification ladder

1. Targeted static/type checks and focused API/frontend unit tests.
2. API migration and contract tests.
3. Frontend component/accessibility tests against the real client contract.
4. Relevant broader regression subsets, if targeted checks pass.
5. Changed-path shortcut scan and implementation/review handoff.

## Execution result

Status: PASS — implementation slice on the WORKING baseline. This is not a release-readiness claim.

- API: added the account-scoped, versioned `GET`/`PUT /v1/auth/me/notation-preferences` resource, API-owned v1 catalog, profile validation, owner-scoped PostgreSQL upsert, migration runner, generated OpenAPI, and focused tests. The pre-existing `/v1/auth/me/preferences` output-language contract remains unchanged.
- Webfront: added the scoped profile client/hook and account-settings editor. Learner math in explanations and clarification views is personalized only after public KaTeX MathML establishes the semantic token boundary; source/Lean content is unchanged. Replacements remain text nodes, never TeX or HTML input.
- Collision and structural safety: a formula with an ambiguous visual match is left entirely in standard notation with a conflict explanation. Unique occurrences in structured layouts such as fractions, roots, and sums are updated together with their accessible math text.

### Fresh verification

- Webfront: `npm run test:unit` (55 files, 560 tests), `npm run test:story` (6 files, 24 tests), `npm run lint`, `npm run typecheck`, and `git diff --check` passed. This includes closed-settings failure/retry and numeric/delimiter/format-command boundary coverage.
- API: notation-preference test selection passed (34 passed, 1 default-environment PostgreSQL case skipped); a separate temporary PostgreSQL 16 run passed the real migration/durability/owner-scope integration test. `ruff`, targeted `mypy`, OpenAPI generation check, and `git diff --check` passed. The API tests include literal 128/129 rule boundaries, NFC-equivalent replacement rejection, and unauthenticated route access.
- Code review: frontend and FastAPI architecture re-reviews found no P0/P1/P2 issues in the final implementation deltas.

### Remaining NOT VERIFIED

- A live browser/API end-to-end run against the new authenticated endpoint, including two authenticated sessions.
