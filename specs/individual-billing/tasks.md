# Individual Billing Tasks

## USD catalogue and utilization-token sandbox rollout

Evidence: [USD sandbox verification](../../docs/usd-plans-sandbox-2026-09-30.md). Checked items are limited to the supported natural-answer route; this is not full-policy or production completion.

- [x] BILL-012: USD 10/20/100 Stripe sandbox Products/Prices, API catalogue/config v2, exact selected-plan Checkout and product projection, legacy compatibility.
- [x] BILL-012: Four-language plan selection, actual product display and lifecycle/error tests; real existing-browser Checkout verification for each tier.
- [x] BILL-013: Additive token ledger, quote/hold/permit/receipt/actual settlement and concurrency/idempotency/failure tests on real PostgreSQL.
- [x] BILL-013: Connect every supported answer/retrieval/QA call and pre-submit maximum display; verify real provider success and failure without fabricated usage.
- [ ] BILL-013/014: Audit remaining formal proof, clarification, materials and project capability paths before declaring the full new policy complete; keep unsupported paths explicitly unavailable.

| ID | Task | Requirements | Verification |
|---|---|---|---|
| BILL-T001 | Add the billing migration, immutable customer/subscription/entitlement/reservation/idempotency/event/per-call-usage schemas, Stripe-operation recovery schema (partial uniqueness, transition constraints, expiry), repository ports, runtime grants, migration-state detection, 13-month detail-to-two-digest tombstone retention with permanent same-account reuse rejection, and the exact production database-release manifest/module step. | BILL-001–BILL-003, BILL-005, BILL-006, BILL-010 | Real PostgreSQL fresh/upgrade and production-release readiness tests; account isolation, immutable records, unique job/event/customer/key/operation bindings, checkout-operation recovery, allowed transition, concurrent quota tests, detail deletion/minimal tombstone schema, replay/expired-key/account isolation, and purge/admission races. |
| BILL-T002 | Integrate transactional billing admission into proof-job creation and dispatch with Free lifetime 3 and Pro period 100 limits, idempotency, closed quota errors, and content-free metering ingestion. | BILL-001–BILL-003, BILL-010 | Unit/service/API/PostgreSQL tests prove no fourth Free job, no 101st Pro-period job, and no job/outbox dispatch on denial. |
| BILL-T003 | Add closed summary/error schemas; server-configured Checkout and Portal operations with local/Stripe idempotency and reconciliation; signed Stripe webhook handling, event ledger, total ordering, subscription transition table, entitlement projection, and fail-closed configuration. | BILL-001, BILL-004–BILL-006, BILL-009 | Stripe fixture/contract tests for signature, replay, out-of-order/equal ordering, Checkout-return forgery, external-success/local-failure recovery, canceled/past-due state, and metadata mismatch. |
| BILL-T004 | Add the web billing/account surface and quota-exhausted proof-create experience without a frontend Stripe secret. | BILL-001, BILL-007 | Component/API tests for Free, Pro, exhausted, upgrade/manage, retained draft, and no secret bundle. |
| BILL-T005 | Extend production Terraform/deployment documentation for external SSM SecureString injection/least-privilege IAM, existing host TLS Stripe egress without NAT, and conditional Google Cognito Hosted UI federation; add a secret-safe external Google IdP provisioner with verify/rollback. | BILL-008, BILL-009 | Terraform test/validate, DPB no-NAT/host TLS Stripe egress inspection, secret scan, provisioner dry-run/contract test, and a reviewed operator runbook with exact Google redirect/callback values. |
| BILL-T006 | Run a real Stripe test-mode + PostgreSQL + Cognito/Google smoke in the configured production-like environment and record sanitized evidence. | BILL-001–BILL-010 | Checkout → signed webhook → Pro admission → Portal/cancel → fallback, plus Google PKCE login and account isolation. |
| BILL-T007 | Introduce variable-token holds, successful explanation settlement of actual usage, terminal failure release, scoped retry reservation, consumed/reserved/available summary and UI while preserving separate old count/idempotency records. | BILL-001–003, BILL-007 | Real PostgreSQL concurrency, duplicate settlement/release, intermediate compile failure, explanation failure/retry, insufficient retry quota with zero dispatch, cross-period settlement, one consumption per proof, gross sequence uniqueness, legacy non-retroactivity; parser and four-language UI regression. |

| BILL-T008 | Implement quote binding, versioned weighted conversion, durable per-stage call permits and usage receipts for generation/retrieval/repair/QA/explanation/clarification, and enforce the displayed cap before each call. | Approved token-policy change, BILL-010, MAT-014 | Real DB atomic budgets/concurrency, all-call coverage, cap denial without provider calls, unknown usage recovery, replay/source binding, rounding and cached/reasoning non-duplication. |

| BILL-T009 | Add operator-managed complimentary Pro grants/revocations, shared entitlement resolution, a content-safe operator CLI, summary source, and four-language test-plan UI. | BILL-011 | Fresh/upgrade real PostgreSQL, trusted operator/runtime ACL separation, grant replay/conflict, concurrency, expiry/revoke, 100-request boundary/Free fallback, paid precedence, unchanged old history; closed API/parser and UI price/renewal/Portal distinction. |

## Completion gate

The release is complete only after BILL-T001 through BILL-T009 pass. Unit tests, a Stripe success redirect, or a
frontend-only price screen do not prove entitlement enforcement. Public production Checkout additionally requires the
tax/legal launch inputs stated in the requirements.
