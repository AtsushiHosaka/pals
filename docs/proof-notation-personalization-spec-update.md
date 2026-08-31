# Proof Notation Personalization — Specification Update

Status: PASS
Baseline: Parent `8bd6dd7` / Webfront `c21a63c` / API `5bd33e2`, all with unrelated user-owned working-tree changes.
Resulting revision: Uncommitted specification changes; no implementation, test, API, or migration changes.

## Authorized changes

### SPEC-CHG-PNP-001

- Authority: User selected display-only substitution.
- Reason: Preserve the identity of the Lean source that established verification.
- Old behavior: Learner math has no notation-personalization requirement.
- New behavior: Only learner-facing mathematics in explanations and clarification answers may use a notation setting; Lean source and proof data remain unchanged.
- Affected IDs: Added `PNP-001`–`PNP-003`.
- Compatibility: No API, persistence, or Lean-source contract change.

### SPEC-CHG-PNP-002

- Authority: User selected account-wide, cross-device persistence.
- Reason: The notation setting should follow the learner rather than one browser.
- Old behavior: No account-level notation-preference requirement.
- New behavior: An authenticated account persists the notation setting; every device retrieves it for later learner-math rendering.
- Affected IDs: Added `CORE-010`, `PNP-004`–`PNP-007`.
- Compatibility: The existing account-preferences API and client accept only an exact output-language shape. A compatible new API contract is required; no existing contract is changed by this specification update.

### SPEC-CHG-PNP-003

- Authority: User selected arbitrary replacement text per configurable source.
- Reason: The learner wants a freely chosen display string, not a fixed preset or curated alternative.
- Old behavior: The setting's value domain was unspecified.
- New behavior: A rule keeps user-authored replacement text as untrusted text; the frontend does not interpret it as markup or commands, and the API validates a complete profile before atomically saving it.
- Affected IDs: Added `PNP-008`–`PNP-009` and `APNP-001`–`APNP-006`.
- Compatibility: A new `/v1/auth/me/notation-preferences` resource is specified so the exact request/response shape of the output-language preference resource remains unchanged.

### SPEC-CHG-PNP-004

- Authority: User selected variable/function identifiers as configurable sources and required continuous frontend collision monitoring.
- Reason: Every visible source-to-display correspondence must remain distinguishable, including when a customized display collides with an uncustomized token in a particular formula.
- Old behavior: The configurable source range and formula-level collision behavior were unspecified.
- New behavior: The v1 range is atomic operators, relations, logical symbols, and complete variable/function identifier tokens. The frontend validates every profile and displayed formula; it leaves any colliding expression entirely in standard notation and names the collision instead of showing ambiguous partial substitutions.
- Affected IDs: Added `PNP-010`–`PNP-012`, `APNP-007`; changed `APNP-003` and API/frontend designs and tasks.
- Compatibility: The dedicated notation-preferences resource is versioned by catalog and preserves the existing output-language preferences contract.

### SPEC-CHG-PNP-005

- Authority: Implementation discovery while starting the user-authorized selected tasks.
- Reason: Variable and function identifiers are intentionally unbounded, so a finite catalog alone cannot validate their stable IDs.
- Old behavior: The design described all sources as catalog members, which conflicts with configurable arbitrary identifiers.
- New behavior: Static symbols use catalog IDs. Variable/function IDs are derived from NFC complete identifier tokens under a versioned grammar; the API validates that grammar and bounded token size.
- Affected IDs: Changed `APNP-003`, the API and webfront designs, and `APNP-T001`.
- Compatibility: The profile JSON still uses `source_id`; the new prefixes make static and derived IDs unambiguous without changing the existing output-language API.

### SPEC-CHG-PNP-006

- Authority: Implementation discovery while reconciling the cross-repository shared-catalog requirement.
- Reason: Duplicating a static symbol catalog in API and webfront would allow the two runtimes to drift.
- Old behavior: The profile named a catalog version but did not prescribe how webfront obtains the matching static catalog.
- New behavior: The dedicated API resource returns its static catalog with the versioned profile; webfront uses that response rather than maintaining a second static catalog.
- Affected IDs: Changed `APNP-007`, API/frontend designs, and `APNP-T002`.
- Compatibility: Only the new notation-preferences resource changes. The existing output-language preference endpoint remains byte-for-byte compatible.

## Files changed

- `specs/pals-product-core/requirements.md`: Cross-repository product requirement `CORE-010`.
- `pals-webfront/specs/proof-notation-personalization/requirements.md`: Frontend requirements and acceptance criteria.
- `pals-webfront/specs/proof-notation-personalization/design.md`: Presentation, accessibility, and account-lifecycle decisions.
- `pals-webfront/specs/proof-notation-personalization/tasks.md`: Frontend implementation and verification tasks.
- `pals-api/specs/account-notation-preferences/requirements.md`: Account-scoped notation-profile API requirements.
- `pals-api/specs/account-notation-preferences/design.md`: Dedicated resource, versioned catalog, validation, and persistence decisions.
- `pals-api/specs/account-notation-preferences/tasks.md`: API implementation, migration, and verification tasks.

## Impact matrix

| Changed ID | Requirements section | Design decisions | Tasks | Code/tests/evidence invalidated | Migration/docs | Revalidate |
|---|---|---|---|---|---|---|
| CORE-010 | Product-core requirements and acceptance criteria | Account setting crosses webfront and API | `PNP-T003`–`PNP-T005`; `APNP-T001`–`APNP-T004` | Existing API/client preference contract cannot carry a notation profile | Dedicated API contract and durable migration required | API, cross-device, and account-isolation tests |
| PNP-001–PNP-003 | Frontend requirement/display boundary | Render-only and accessibility boundary | `PNP-T001`–`PNP-T002` | Learner rich-text rendering and source-boundary tests | None | Renderer, source-boundary, and accessibility tests |
| PNP-004–PNP-007 | Frontend account lifecycle | Auth-scoped fetch/update and truthful failure handling | `PNP-T003`–`PNP-T005` | Account-preference client and settings UI tests | Dedicated API contract and durable migration required | Cross-device and account-isolation tests |
| PNP-008–PNP-009 | Frontend arbitrary text | Text-only rendering and all-or-nothing saves | `PNP-T006`–`PNP-T007` | Renderer-security and profile-validation tests | Dedicated API contract and durable migration required | Text-only rendering and atomic-save tests |
| APNP-001–APNP-006 | API notation profile | Dedicated resource, validation, persistence, migration | `APNP-T001`–`APNP-T004` | New API/repository/migration contract tests | New API documentation and migration required | API, migration, and contract tests |
| PNP-010–PNP-012 | Frontend identifier scope and collision monitor | Structured tokens, continuous validation, all-or-nothing expression rendering | `PNP-T008`–`PNP-T010` | Tokenizer, collision, accessibility, and account-change tests | Shared versioned catalog required | Implement after API/frontend catalog artifact is introduced |
| APNP-007 | API catalog versioning | Shared catalog version in profile contract | `APNP-T001`–`APNP-T004` | Contract and validation tests | Shared versioned catalog required | Implement with the dedicated resource |

## Validation evidence

- `git diff --check` in the parent, webfront, and API worktrees: passed for tracked changes.
- `perl` trailing-whitespace scan over the new specification files and loop ledger: passed.
- `rg` traceability search for `PNP-*`: all active IDs map to design and tasks.

## Revalidation route

The final targeted spec review passed. Code, tests, migration, runtime behavior, and released API
compatibility remain NOT VERIFIED until the listed implementation tasks run.

## Targeted independent review

- Input: `CORE-010` and `PNP-001`–`PNP-007` at the uncommitted revisions above, plus the current
  API and webfront account-preferences contracts.
- Finding (P1): The permitted substitution domain and learner editing freedom are undefined. Without
  them, the persistent profile has no validatable API shape and the renderer cannot guarantee an
  unambiguous, accessible result. Route: product decision D-03, then API-focused specification.
- No P0 finding was observed in the approved display-only boundary. The existing exact-shape
  account-preferences contract makes a compatible API addition mandatory, not optional.

## Targeted independent review after SPEC-CHG-PNP-003

- Input: `CORE-010`, `PNP-001`–`PNP-009`, and `APNP-001`–`APNP-006` at the current uncommitted
  revisions, plus the same current API and webfront contracts.
- Finding (P1): The configurable source-symbol catalog and its numeric profile limits are undefined.
  A stable `source_id`, server validation, accessible renderer transformation, and test fixtures
  cannot be completed until that source scope is selected. Route: product decision D-04, then a
  targeted update of both focused specs.
- No P0 finding or contradiction was observed in the display-only, owner-scoped, text-only, and
  atomic-save boundaries. Formatting and ID traceability checks passed; all code/runtime evidence
  remains NOT VERIFIED.

## Targeted independent review after SPEC-CHG-PNP-004

- Input: `CORE-010`, `PNP-001`–`PNP-012`, and `APNP-001`–`APNP-007` at the current uncommitted
  revisions, together with the current API/webfront preference contracts and the installed KaTeX
  package.
- Findings: None at P0/P1 for specification readiness. The catalog's individual IDs remain an
  implementation artifact constrained by the fixed v1 categories, version, and validation rules;
  this does not change user-visible behavior or leave a decision open.
- Validation: ID/cross-reference search and trailing-whitespace scans passed. `git diff --check`
  passed for all three worktrees. A local KaTeX `__parse` probe returned a parse tree for `x + f(y)`;
  this is feasibility evidence only, and the design explicitly forbids relying on that private API.
- Checklist exceptions: Code, API, migration, renderer, accessibility, and runtime tests are
  NOT VERIFIED because no implementation was requested. They are explicit tasks, not evidence for
  this specification-only PASS.
