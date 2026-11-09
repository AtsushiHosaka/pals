# Production reliability audit — 2026-11-08

Owner: Codex. Tracking: [#309](https://github.com/AtsushiHosaka/pals/issues/309).
Scope: investigation and proposed development rules. No application repair or production deployment is part of this change.

## Decision

Keep issue-driven development and monotonically increasing release sequences. The main problem is that the current process can establish source identity, admission, and running services without establishing a usable final answer or recovery after a transient failure. Several tests actively preserve behavior that conflicts with the desired reliability contract.

The evidence supports a focused stabilization effort before further feature releases: fix the reproduced answer/polling defects; make release execution reproducible and recoverable; require terminal, persisted, rendered acceptance; and complete production telemetry. Rewriting agent instructions alone cannot enforce any of these controls.

This is a scoped audit, not a review of every line or a guarantee of zero bugs. Security, billing, full browser/device coverage, all mathematical domains, and actual crash/reboot recovery were not exhaustively tested.

## Evidence and revisions

Read-only production observations were made on November 8, approximately 22:16–22:24 JST, while a different session was executing seq28. Preserve that distinction when interpreting errors. This audit made no deployment, IAM, database, queue-message, service-lifecycle, or user-submission changes and did not start or resume a monitoring automation.

| Artifact | Pinned revision / observation |
| --- | --- |
| Parent GitHub main | `3c746c56a5595cd2468fd062fccd9d393300eb28` after fresh fetch |
| Candidate source capture | seq28 parent `f727cdbd457edfc4b284ff898025090e7b4dadac` |
| API source | `14e9bf93c9eece11d8e6f2d316936a519ba00610` |
| Web source | `120cb477911b89ad2b8487f968fc0187f7d85496` |
| Candidate worker | `b27f1d8292391567a2ca15f103eb08b18dc016c4` |
| Candidate infrastructure | `f140a8df9655268168b4ac13b3ba2a7858896bd5` |
| Running container labels at 22:22 JST | API/reconciler `14e9bf93`; Web `120cb477`; both workers `a6d36bccc41c9ad37426219e92ae6c7a6a044cdd`; verifier `189b44378e6e63e5ab7c92d9c5b7d6507acd80f0` |

The candidate worker was therefore **not observed running** in this snapshot. Docker revision labels identify claimed source; this audit did not independently reconstruct the running image contents or verify their registry digests. API/Web code findings below match the observed labels. The candidate prompt change is analyzed as a cross-repository compatibility defect, not falsely reported as already deployed.

The original October checkout contained substantial pre-existing changes and was preserved. The report and proposals use one isolated parent worktree. Existing implementation snapshots and installed test dependencies were reused; no duplicate application stack was started.

### Live production findings

- Public site and public API health both returned **HTTP 503** at approximately 22:18 JST. This is one composite availability check, not two independent user failures.
- At 22:13 JST, the existing ALB/target 5xx alarm entered ALARM, evaluating **19 errors in the 22:10 minute**. The seq28 dispatch log records sole-target deregistration at **22:10:31 JST**. Their timing and the procedure support cutover-related unavailability; they do not classify every error's cause.
- In the approximately 72-hour window ending **22:19:43 JST**, CloudWatch returned **946 ELB-generated 5xx**, including 884 on November 8, and **no Target_5XX datapoints**. One five-minute bucket timestamped **04:44 JST** contained 775 ELB 5xx. These are load-balancer request counts, including possible probes/bots/retries, not unique affected users. No-datapoint target metrics are not proof that application failures never occurred. RequestCount has different coverage/semantics; do not divide these values into a product failure rate.
- Both existing PALS log groups had zero stored bytes; `/pals/prod/host` had **no log streams**. `PALS/ProofQuality` returned **zero metrics**. There were 15 metric alarms: ten machine-auth and five incident-health alarms. An OK explanation-failure gauge does not establish successful mathematical answers.
- SQS metadata showed approximately **32 proof-job DLQ messages and one proof-request DLQ message**, plus one in-flight proof job. No messages were received, replayed, or deleted. A November 6 record had 21+1; the change is a lead, not a classification of eleven new user failures. Retention, deletions, and redelivery prevent that inference.
- At 22:21–22:22 JST, all seven owned containers were running; current state showed no OOM kill. This coexisted with public 503s. Bounded logs of the current containers contained one API traceback/ValidationError match. The sanitized extraction did not identify its underlying cause. Current-container logs do not recover deleted predecessor logs or establish full 72-hour coverage.

Raw provider responses, identifiers, and bounded host evidence remain outside Git in the audit's private local evidence directory. No question, answer, Lean source, user identifier, credential, internal address, or raw traceback is published here.

## Findings

### F1 — P1: deployment removes all public serving capacity

The inspected seq28 `ingress_driver.py:26–37` requires exactly one healthy target, then deregisters it. `cutover.py:263–274` waits until that target is unused; registration follows drain, shutdown, DB admission, activation, recovery setup, and health. The API updater also requires all application DB clients stopped ([API source](https://github.com/AtsushiHosaka/pals-api/blob/14e9bf93c9eece11d8e6f2d316936a519ba00610/app/release/aurora_runtime_update.py#L468)).

This design necessarily has a maintenance outage. Sequence numbers do not create that outage; removing the only serving target does. First provide bounded maintenance handling and automatic restoration on safe pre-admission failures. Genuine zero downtime needs compatible parallel serving and an expand/contract data-admission design; adding a second incompatible target is insufficient.

### F2 — P1: release checks are ordered after the resources they require become unavailable

In the inspected seq28 driver, fresh-preflight age, remaining signature window, and predecessor-admission checks run in `guard_before_quiesce:100–111`, called after traffic deregistration. A refusal can therefore leave healthy old containers inaccessible. The later `do_admission:313–322` normally calls a probe implemented through `docker exec` into the API (`host_steps.py:145–146`), although the preceding quiesce stops that API.

The observed driver includes an optional probe waiver; its comment claims owner approval. This audit did not verify that approval and does not infer authorization from the comment. The underlying operator retains its own admission checks, so the waiver is not a removal of all database validation.

Move prerequisites before traffic removal, use a DB observer that survives application shutdown, and test the actual operation order with failure at each boundary. Every failure before DB admission needs a verified restore-to-baseline path. After an incompatible admission, use a schema-compatible forward repair rather than an old-image-only rollback.

### F3 — P1: release completion does not require functional acceptance

The seq28 runbook completes receipts and releases the owner at step 21; the public proof trial is a later manual step 22. The health helper explicitly reports `no_model_calls:true`. These checks establish runtime deployment, not Lean → explanation → stored answer → rendered answer → history after reload.

Use separate `deployed_unverified`, `accepted`, and `failed` states. Keep cleanup and owner release possible after failed acceptance, but prevent issue closure or the next unrelated promotion until required acceptance is satisfied. The acceptance record must identify actual candidate digests, model/config/catalog revisions, expected outcome, terminal outcome, persistence, UI rendering, and untested branches.

### F4 — P1: application tests are not an enforced merge/release gate

The parent has one workflow, [PALS parent checks](https://github.com/AtsushiHosaka/pals/blob/3c746c56a5595cd2468fd062fccd9d393300eb28/.github/workflows/pals-scripts-pr.yml), covering secrets and the public-agent boundary. No workflows were found in the inspected implementation main or candidate trees. GitHub branch metadata reported `protected:false` for the parent and API/agent/Web/infra main branches. The inspected agent main commit had zero check runs. External unpublished checks or repository rules were not exhaustively enumerated; these observations do not prove that no human or external checks ever run.

Parent `Makefile:113–118` runs Terraform formatting/init/validation for `infra-test`, omitting Python host/controller/recovery tests; `make test` omits E2E. The current web smoke explicitly tests answers **without Lean** ([test](https://github.com/AtsushiHosaka/pals-webfront/blob/120cb477911b89ad2b8487f968fc0187f7d85496/tests/e2e/proof-submission-smoke.spec.ts#L6)). Default API test fixtures replace repositories/SQS, and real PostgreSQL integrations may skip without their environment.

Retain these useful unit/contract tests. Add required, exact-revision checks for changed application repositories, real database integration, host runtime/recovery, and the actual Lean-to-answer journey. Required missing/skipped infrastructure checks must report a blocked gate rather than a pass. Verify rejection using a deliberately failing temporary PR/check in an authorized test setting before claiming enforcement.

### F5 — P1: final conclusions are dropped at the API/chat boundary

[API `_answer:274–299`](https://github.com/AtsushiHosaka/pals-api/blob/14e9bf93c9eece11d8e6f2d316936a519ba00610/app/infrastructure/repositories/proof_request_lean.py#L274) joins only `overview` and section summaries. It omits `content.conclusion`. [Web:139](https://github.com/AtsushiHosaka/pals-webfront/blob/120cb477911b89ad2b8487f968fc0187f7d85496/components/ProofRequestThread.tsx#L139) renders `request.answer.text`.

An executable call to the real API function with synthetic content confirmed `conclusion_present:false`. The worker [prompt:1537–1542](https://github.com/AtsushiHosaka/pals-agent/blob/a6d36bccc41c9ad37426219e92ae6c7a6a044cdd/pals_agent/explanations.py#L1537) explicitly encourages putting the unique final result in `conclusion`. This instruction is present in both the source identified by running worker labels (`a6d36bcc`) and candidate `b27f1d82`. It is therefore an existing cross-repository compatibility defect, not solely a candidate-change risk; image contents were not independently reconstructed.

The API integration fixture ([test:93–118](https://github.com/AtsushiHosaka/pals-api/blob/14e9bf93c9eece11d8e6f2d316936a519ba00610/tests/integration/test_proof_request_lean_flow.py#L93)) omits a conclusion and checks only section text. Add a schema-valid fixture with a unique conclusion; verify projection, persisted result, and actual chat display. This confirms a code defect, not the cause of every historical missing-answer report.

### F6 — P1: a network failure can stop automatic polling until reload or another trigger

[Web `useProofRequests:56–69`](https://github.com/AtsushiHosaka/pals-webfront/blob/120cb477911b89ad2b8487f968fc0187f7d85496/hooks/useProofRequests.ts#L56) schedules another poll only after success. Catch records the error without retry. There is no online/focus recovery in the effect. Guest observation has a similar path. The user can remain on an active state even if the backend later finishes.

The existing [test:273–285](https://github.com/AtsushiHosaka/pals-webfront/blob/120cb477911b89ad2b8487f968fc0187f7d85496/tests/unit/use-proof-requests.test.tsx#L273) explicitly asserts this stop as correct. It passed against the exact source in an isolated execution. This is why increasing test counts alone is insufficient: the expected behavior is wrong for transient failure recovery.

Define bounded backoff for retryable GET errors, one in-flight observation, cancellation/ownership fencing, and online/focus reconciliation. Authentication denial and terminal business outcomes need distinct treatment. Recover observation of the same request; do not resubmit a paid job to fix a read failure.

### F7 — P1: later crashes can require a new manual release to recover

[Runtime documentation:1000–1020](https://github.com/AtsushiHosaka/pals-infra/blob/f140a8df9655268168b4ac13b3ba2a7858896bd5/host/private-runtime/README.md#L1000) says a worker lane stays stopped after prolonged SQS failure or a crash threshold, with `restart=no`. There is no single-lane helper; recovery requires stopping the healthy sibling, potentially waiting a 3900-second drain, and stopping the verifier.

[Recovery:102–104](https://github.com/AtsushiHosaka/pals-infra/blob/f140a8df9655268168b4ac13b3ba2a7858896bd5/host/private-runtime/recover_runtime.py#L102) uses the ordinary current-window manifest validator. The deployment window is at most 24 hours. [Documentation:1064–1072](https://github.com/AtsushiHosaka/pals-infra/blob/f140a8df9655268168b4ac13b3ba2a7858896bd5/host/private-runtime/README.md#L1064) explicitly requires a manually signed next sequence after expiry and states that automated renewal/process-crash monitoring is absent.

Serving uses durable DB admission and does **not** automatically stop when the manifest expires. The defect in unattended operation is that a later crash/reboot becomes operator-dependent. Separate short-lived deployment authority from narrowly scoped recovery of the exact currently admitted runtime, preserving signatures, revocation, identities, admission, and image checks. Verify controlled lane failure and post-window recovery in an isolated production-equivalent environment before production lifecycle testing.

### F8 — P2: OAuth sessions expire without a renewal path

[OAuth token exchange:148–155](https://github.com/AtsushiHosaka/pals-webfront/blob/120cb477911b89ad2b8487f968fc0187f7d85496/lib/auth/cognitoOAuth.ts#L148) discards refresh tokens. [AuthProvider:219–235](https://github.com/AtsushiHosaka/pals-webfront/blob/120cb477911b89ad2b8487f968fc0187f7d85496/components/AuthProvider.tsx#L219) clears expired OAuth credentials; forced refresh returns null at 395–399. Password sessions have a different refresh path.

The default token lifetime is 3600 seconds minus 30-second skew; actual production lifetime and the user's login method were not checked. This establishes a concrete idle-expiry path, not attribution of the user's idle errors. Define the intended session lifetime and secure renewal behavior. Do not solve it by placing refresh tokens in broader browser storage. Acceptance must preserve the workspace and unsent draft through expiry, network interruption, and explicit reauthentication where necessary.

### F9 — P1: monitoring cannot yet explain the product's terminal failures

Live CloudWatch lacks application streams and `PALS/ProofQuality` metrics. Incident-health alarms provide a useful minimum but do not measure accepted requests reaching terminal outcomes, failed phases, retry reasons, age of active requests, or correct rendered answers. The DLQ backlog is unresolved. This matches unfinished work in [#217](https://github.com/AtsushiHosaka/pals/issues/217) and [#291](https://github.com/AtsushiHosaka/pals/issues/291).

Emit versioned, privacy-minimized lifecycle events with request correlation, release/config revision, stage, bounded error code, duration, and terminal status. Reconcile accepted/terminal/in-flight accounting so missing events cannot silently look healthy. Monitor consumer/outbox liveness, oldest active work, DLQ changes, and telemetry heartbeat. Retain no question/answer/Lean text or user credentials. Verify both event-to-CloudWatch delivery and the resulting alarm/notification separately from answer correctness.

### F10 — P2: executing release drivers are outside the reviewed source freeze

The inspected seq28 `bootstrap_next_release.py:26–35,104–112` copies roughly forty reusable local pipeline files from a prior release directory. These drivers are absent from the inspected parent/infra Git trees. `make_freeze.py:14–38` pins generated artifacts but omits executing drivers including `cutover.py`, `flow.py`, `host_steps.py`, and `ingress_driver.py`. The read version of `cutover.py` had SHA-256 `04a7f8f0dcf62b469009c5fc437ede2f9123edf28136f0f154b2504d10ba19a0`; its modification time was later than freeze generation. The active release directory may subsequently change.

Also, `flow.py:53–66` searches backward for a successful preflight instead of treating the latest failed attempt as blocking. Native owner validation remains a separate barrier.

Move reusable non-secret drivers into the owning infrastructure repository. Freeze the exact executing revision/hash, arguments, migration plan, and environment contract. A changed driver invalidates the affected rehearsal evidence. A failed latest prerequisite must block until repaired and rerun; do not cherry-pick an older green result.

### F11 — P2: charts can omit a known terminal failure

The [November 6 guest record](production-guest-proof-smoke-2026-11-06.md) first records an unfinished request, then its terminal UI failure. The latter is an overlapping follow-up. [Chart filters:81,108](https://github.com/AtsushiHosaka/pals/blob/3c746c56a5595cd2468fd062fccd9d393300eb28/docs/quality-ledger/make_charts.py#L81) exclude overlaps rather than resolving the latest outcome. Thus the terminal failure disappears from aggregates even though the raw evidence is retained and the limitation is documented.

Coalesce observations into one attempt with its latest terminal result, preserving immutable raw rows and uncertainty. Do not count it twice, drop the failure, or turn an observation interval into exact backend execution latency.

## Why the cycle repeats

The causal chain is: an issue proves a local slice → mocks and narrow expected behavior pass → a candidate combines independently evolved contracts → runtime checks prove identity/health → the sole traffic target is removed → operational completion precedes product acceptance → transient read/session/worker failures lack recovery or end-to-end telemetry → the owner discovers the defect and opens another issue.

This is a contract-and-enforcement problem across repositories, plus specific application defects and an availability-limiting deployment design. It is not evidence that Claude Code alone causes the bugs, nor that all recent releases introduced new defects. Some failures predate the latest candidate; the audit cannot calculate a change-failure rate without a release/incident denominator.

Keep the substantial existing protections: exact source/image bindings, cryptographic verification, latest-admission checks, canonical ownership, receipt preservation, and graceful drain. Improve their execution order and add the missing product/recovery gates.

## Ordered stabilization backlog

These are proposed implementation slices, not work declared complete by this report. Existing owners retain their areas; each slice needs a linked implementation PR and measured acceptance. Unrelated feature promotions should remain held while a critical release or answer regression remains unresolved; this document does not itself stop another session or an automation.

| Order | Owning area / related issue | Completion evidence |
| --- | --- | --- |
| 1 | CI/release, #309 | Reviewed/versioned controller; all prerequisites before ingress removal; failure compensation tested; probe works after API shutdown; actual driver is frozen |
| 2 | API/Web/agent, #233/#298 | Unique conclusion survives schema-valid completion → API → stored history → actual chat display; transient read failure recovers the same request without duplicate work |
| 3 | CI/release, #309 | Required checks bound to candidate revisions, real DB integration, runtime/recovery suites, and critical E2E; missing required checks block |
| 4 | Observability, #217/#291/#299 | Lifecycle accounting, causes, request age, consumers, DLQ and missing telemetry visible in CloudWatch; delivery/notification evidence; backlog disposition without blind replay |
| 5 | Runtime, #142 | Exact-current-runtime recovery after lane crash/reboot and deployment-window expiry; measured drain/recovery time, no duplicate charges/results |
| 6 | Web auth | Approved idle-session contract verified for password and enabled OAuth login paths; workspace/draft preserved |
| 7 | Release architecture | Graceful bounded maintenance first; later parallel compatible serving with migration/admission compatibility and measured zero unavailable cutover requests |
| 8 | Quality reporting, #216 | Final outcomes coalesced once; failure and unknowns retained; reproducible charts |

For every code defect, first add a test for the expected user behavior that fails on the pinned bad revision, then repair the owning implementation and run the relevant boundary checks. Do not change expected results to match a regression. For model/prompt changes, use one small fixed set spanning ordinary cases and failure-prone boundaries, with a reserved holdout and the production configuration for final acceptance. Record cost and randomness; respect the existing evaluation budget rather than repeating one easy problem until it passes.

The shared rule proposal is [release-reliability-policy.md](release-reliability-policy.md). It is guidance until the required CI, release-controller, telemetry, and recovery changes are implemented and independently verified.

## Verification and limits

- Executed: read-only CloudWatch/queue metadata, public HTTP reads, bounded read-only SSM container inspection, GitHub branch/check/workflow metadata, exact-source projection probe, and targeted existing polling test. No fault injection, model request, data write, restart, or new application service.
- Projection probe: real API `_answer` with synthetic overview/section/conclusion; returned text lacked the conclusion. This is a projection check, not Lean/schema/DB/UI E2E.
- Polling probe: exact Web source with existing Vitest 4.1.9, React/jsdom dependencies; the selected `retains the existing error stop` test passed. Sixteen other tests were unselected. This verifies the undesirable existing behavior, not a repaired journey.
- Not verified: complete production request histories, per-user failure rate, per-error causes, current OAuth configuration, image-content provenance, seq28 eventual outcome, fault/reboot recovery, final accepted answers, secure renewal design, and exhaustive source/security coverage.
- Live availability is time-bound. A later successful health response would show recovery at that later time, not invalidate the observed 503 or establish answer correctness.
- Read-only follow-up at approximately **22:29 JST** again returned HTTP 503 from both public endpoints. This is a follow-up of the same availability observation, not an extra independent trial in the quality ledger.
- Documentation validation: 473 ledger rows with zero validation errors; all 22 existing ledger tests passed; six charts regenerated; the prior 472 CSV rows were preserved byte-for-byte; parent working/index secret scan and whitespace checks passed. These checks validate the report change, not application reliability.
