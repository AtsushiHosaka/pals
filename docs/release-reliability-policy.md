# Release reliability contract

Shared operating rules for Claude, Codex, and human contributors. Rationale and known gaps: [November 8 audit](release-reliability-audit-2026-11-08.md), [#309](https://github.com/AtsushiHosaka/pals/issues/309). These rules specify required evidence; they do not imply that missing automation already exists.

The executable paths are `make release-source-checks` (actual changed-source GitHub CI), `make release-local-qualify` (the approved real local journey), `make release-qualify` (authenticated live capture where a dedicated session exists), and `make release-cycle` (versioned native sequencing). See [the runner contract](release-acceptance-runner.md) and `pals-infra/host/private-runtime/RELEASE_CYCLE.md`. Cutover blocks without real qualification of the declared profile, exact source/image bindings and executable native recovery adapters. Passing deterministic controller/parser tests does not fill those prerequisites.

On November 9 JST, the user selected local real DB/Lean/model before release and the currently logged-in Chrome account for one production request after deployment. No AWS staging environment is required. Each approved evaluation has a US$1 maximum. The local profile retains the exact API, worker and verifier images; its Web build uses the exact candidate source with declared loopback public bindings. Local auth/queue emulation, bootstrap DB privileges, the budget forwarding proxy and network guard are explicit boundaries. They are not evidence for production auth/network. The controller uses `local-qualification.py --verify-existing` for fresh dependency/browser/DB reads of the fixed one-submission capture; it may not import a prior PASS value or submit a replacement job automatically. Production acceptance must separately establish the actual deployed candidate and the new authorized Chrome journey through completion, persistence and reload.

## Start from observable behavior

Before implementation, record the issue, owning repository, exact starting revision, expected user outcome, affected cross-repository contracts, failure/recovery cases, and non-goals. Inspect the existing behavior rather than treating a bug report or prior completion claim as established fact. Use one release owner; give parallel agents disjoint write ownership or read-only scopes.

For a defect, write a behavioral regression that fails on the pinned bad revision and passes after repair. Review what tests assert. Mocks establish the declared boundary only; they do not establish a real provider, database, queue, compiler, browser, or deployed result.

## Evidence required for promotion

| Gate | Required evidence |
| --- | --- |
| Source and contracts | Clean task-owned source snapshot; exact parent/submodule commits; immutable image digests; schema, catalog, prompt/model/config versions; preserved existing features |
| Deterministic checks | Changed-repository unit/static/build checks, cross-repository contract tests, actual database integration where affected, host/controller/recovery suites where affected |
| Product journey | Realistic input through the production-equivalent API/queue/worker/Lean/explanation path to the expected terminal outcome; all learner-visible fields survive persistence, rendering, and reload |
| Failure and time | Required transient GET failure/reconnect, auth expiry, long-running job, timeout/cancel/redelivery, migration/recovery cases; prove no duplicate results or charges where applicable |
| Release rehearsal | Same reviewed driver and operation order as production; prerequisites before traffic removal; bounded outage; compensating action for every safe pre-admission failure; compatible post-admission forward repair |
| Production acceptance | Actual deployed digests/config; authorized bounded critical-path check; terminal result, rendered answer, and history after reload; telemetry fresh; no unresolved critical regression |

Select checks by the changed behavior and dependency boundaries; do not rerun unrelated expensive suites mechanically. Required skipped, unavailable, stale, wrong-revision, or mock-only evidence yields `BLOCKED` or `NOT VERIFIED`, never a green gate. Any approved deferral must identify the exact gap, impact, owner, expiry/resume condition, and user decision; it must not silently weaken a required check. Honor existing paid-evaluation limits and authorization for production data/lifecycle operations.

Bind evidence to the candidate actually promoted. Changing code, images, schema, prompts/model configuration, catalog, driver, or relevant runtime settings invalidates affected evidence. Keep prior failures. Accept the latest successful rerun only after addressing a failed prerequisite; never search backward past an unresolved latest failure.

## Deploy safely and distinguish outcomes

Use `prepared` → `verified` → `deployed_unverified` → `accepted`, with explicit `failed`/`blocked` states. `accepted` requires the production-acceptance evidence above. Merge, image publication, admission, startup, health, empty queues, or “preparing response” alone is insufficient. Do not close a functional issue or promote an unrelated next release while a required critical acceptance remains unresolved.

Cleanup, traffic restoration where safe, temporary-access removal, and canonical-owner release must remain possible after a failed check. Keep safety cleanup separate from functional acceptance; never retain expired privileges or deadlock the release owner to obtain an acceptance result.

Before removing traffic, verify all prerequisites and a workable recovery plan. Prefer serving capacity that remains available; if the architecture requires maintenance, declare and measure a bounded maintenance window with a useful user response. On pre-admission failure, restore and verify the exact baseline ingress/runtime where compatible. After irreversible admission, use the reviewed schema-compatible repair path. Never bypass admission, signatures, authorization, or identity checks to make health green.

Reusable release code belongs in the owning repository. Freeze the exact executing driver revision/hash and arguments, not only generated artifacts. Changing it during a cutover requires renewed affected verification; a comment claiming approval is not approval evidence.

## Treat recovery as a product requirement

Specify behavior after a transient network error, reconnect/focus, access-token expiry, provider/queue failure, worker exit, and host reboot. Recover observation of the same request rather than resubmitting work. Preserve account isolation, unsent drafts, idempotency, billing, and terminal-state integrity.

Deployment authorization and recovery of the exact currently admitted runtime need explicit, reviewed lifetime rules. A short-lived release signature must not leave unattended recovery dependent on an unplanned manual feature deployment. Do not broaden credential storage or enable unrestricted restart policies as a shortcut.

## Observe and close the loop

Record privacy-minimized lifecycle events correlated to release/config and request: accepted, stage transitions, terminal outcome, bounded error code, duration, and retry reason. Reconcile accepted/terminal/in-flight work and alarm on missing telemetry, old active work, stopped consumers/outboxes, and DLQ growth. Health and answer-quality metrics have separate meanings.

One attempt may have multiple observations. Preserve raw observations and count its final outcome once; retain failures and unknowns. Unit-test counts are not product success rates, and load-balancer requests are not unique users.

For an incident, restore safely, identify the failure mechanism, add a regression at the boundary that missed it, and update only the necessary code/runbook/rule. Record what was observed, what was inferred, what remains unverified, and the exact follow-up owner. Documentation changes alone do not close implementation or production-recovery work.
