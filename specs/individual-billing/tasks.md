# Individual Billing Tasks

| ID | Task | Requirements | Verification |
|---|---|---|---|
| BILL-T001 | Add the billing migration, immutable customer/subscription/entitlement/reservation/idempotency/event/per-call-usage schemas, Stripe-operation recovery schema (partial uniqueness, transition constraints, expiry), repository ports, runtime grants, migration-state detection, and the exact production database-release manifest/module step. | BILL-001–BILL-003, BILL-005, BILL-006, BILL-010 | Real PostgreSQL fresh/upgrade and production-release readiness tests; account isolation, immutable records, unique job/event/customer/key/operation bindings, checkout-operation recovery, allowed transition, and concurrent quota tests. |
| BILL-T002 | Integrate transactional billing admission into proof-job creation and dispatch with Free lifetime 3 and Pro period 100 limits, idempotency, closed quota errors, and content-free metering ingestion. | BILL-001–BILL-003, BILL-010 | Unit/service/API/PostgreSQL tests prove no fourth Free job, no 101st Pro-period job, and no job/outbox dispatch on denial. |
| BILL-T003 | Add closed summary/error schemas; server-configured Checkout and Portal operations with local/Stripe idempotency and reconciliation; signed Stripe webhook handling, event ledger, total ordering, subscription transition table, entitlement projection, and fail-closed configuration. | BILL-001, BILL-004–BILL-006, BILL-009 | Stripe fixture/contract tests for signature, replay, out-of-order/equal ordering, Checkout-return forgery, external-success/local-failure recovery, canceled/past-due state, and metadata mismatch. |
| BILL-T004 | Add the web billing/account surface and quota-exhausted proof-create experience without a frontend Stripe secret. | BILL-001, BILL-007 | Component/API tests for Free, Pro, exhausted, upgrade/manage, retained draft, and no secret bundle. |
| BILL-T005 | Extend production Terraform/deployment documentation for billing-runtime secret injection/task IAM, one-NAT API Stripe egress, and conditional Google Cognito Hosted UI federation; add a secret-safe external Google IdP provisioner with verify/rollback. | BILL-008, BILL-009 | Terraform test/validate, NAT/API Stripe egress inspection, secret scan, provisioner dry-run/contract test, and a reviewed operator runbook with exact Google redirect/callback values. |
| BILL-T006 | Run a real Stripe test-mode + PostgreSQL + Cognito/Google smoke in the configured production-like environment and record sanitized evidence. | BILL-001–BILL-010 | Checkout → signed webhook → Pro admission → Portal/cancel → fallback, plus Google PKCE login and account isolation. |

## Completion gate

The release is complete only after BILL-T001 through BILL-T006 pass. Unit tests, a Stripe success redirect, or a
frontend-only price screen do not prove entitlement enforcement. Public production Checkout additionally requires the
tax/legal launch inputs stated in the requirements.
