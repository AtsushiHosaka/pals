# Billing Specification Loop Ledger

## Iteration record

| Iteration | Spec revision | Code revision | Trigger | Expected verdict-changing delta | New evidence | Findings opened/closed | Routes invoked | Stage/overall budget | Elapsed | Stop/cancel action | Result |
|---|---|---|---|---|---|---|---|---|---:|---|---|
| 1 | Parent `8bd6dd7`; canonical scope: `specs/pals-product-core/requirements.md` | Parent `8bd6dd7`; API `5bd33e2`; web `c21a63c` | Define robust learner billing: free quota, monthly plans, and plan-specific access | Establish authorized product decisions and a traceable canonical billing specification | Review: canonical scope has only CORE-001–009; none defines billing, quotas, entitlement, subscription lifecycle, or plan-gated access. `specs/README.md` confirms that no canonical design/tasks exist. `BILL-INV-001` found no payment SDK/integration, catalog, subscription state, metering, enforcement, or billing UI/tests; current creation is owner-authenticated only. | Opened: missing billing requirements, design, tasks, payment lifecycle, metering, enforcement, and product decisions | `sdd-review-spec`; `BILL-INV-001` implementation inventory | 30 min exploration / two iterations maximum | 13 min | — | `FAIL` for billing-spec readiness pending an authorized product decision |
| 2 | Parent working tree; `specs/individual-billing/` | API/Web/Infra current working trees | User authorized individual monthly billing and no-reset free allowance | Define initial price, quota, Stripe safety boundary, Google production gap, and implementation gate | Individual Pro JPY 1,500/month, Free lifetime 3 requests, Pro 100 requests per Stripe billing period. Normal proof jobs lack historical cost telemetry; current `gpt-5.4-nano` default/cap and published unit pricing are a guardrail only. Google Hosted UI code exists but production Terraform omits its IdP/domain. | Closed: initial plan-family decision. Opened: Stripe/Google credentials and tax/legal launch inputs; implementation tasks BILL-T001–T006. | `sdd-generate-spec`; implementation inventory | One spec/review iteration before implementation | — | — | `DRAFT` pending independent spec review |

## Delegation record

| Delegation ID | Agent/skill | Owned slice | Mode/owned paths | Input revisions | Prompt summary | Stage/command budgets | Required verification | Result revision/status | Evidence and NOT VERIFIED | Elapsed/retries/stop action | Next route |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BILL-INV-001 | `/root/billing_inventory` | Existing billing, quota, entitlement, and payment behavior inventory | Read-only | Parent `8bd6dd7`; API `5bd33e2`; web `c21a63c` | Locate present/partial/absent behavior and exact evidence; make no product decisions or edits | 15 min; two retries | Repository-wide targeted search and context inspection | `PASS`; no files changed | API package `pyproject.toml:11-22` and web `package.json:18-31` have no payment SDK; `proof_jobs.py:189-205` and service `:337-405` show owner-only admission; external infrastructure and live provider configuration remain NOT VERIFIED | 13 min / 0 retries / completed | First human product decision |

## Human decision queue

| Decision ID | Actor + trigger/state + observable question | Known facts | Options and impact | Recommendation | Affected IDs | Answer/authority | Resulting spec revision | Status |
|---|---|---|---|---|---|---|---|---|
| BILL-DEC-001 | A learner creates a paid account: choose the initial commercial surface and plan family | Individual Pro is only a non-canonical price hypothesis; course/lab pilots are the current stated near-term priority | Individual-only, pilot-first, or both | Pending product decision | New billing requirements | User | — | Open |

## Requirement evidence

| Requirement | Design | Task | Code revision/location | Test/runtime evidence | Freshness | Status | Owner/next action |
|---|---|---|---|---|---|---|---|
| Proposed billing scope | No canonical design | No canonical tasks | `pals-api/app/api/routes/proof_jobs.py:189-205` admits an authenticated learner's proof-job creation directly; no entitlement check is present. `pals-webfront/lib/api/proofJobs.ts:67-81` calls it directly. | No billing tests identified; external WAF/API-Gateway limits and live-provider configuration are NOT VERIFIED | Current as of 2026-08-10 | Missing | Resolve the first plan/visibility decision, then create canonical requirements |
