# Lean production recovery — 2026-10-14

Lean is restored in production and authenticated QA is complete for the flows below.
Work started on 2026-10-14 and final browser verification finished on 2026-10-15 JST.
The last signed production release is sequence 33, parent
`4e629e7a3d01a3d6eff935a8cb752189bea9588b`. Historical failures and intermediate
next steps below are retained as operating evidence, not current blockers.

| Flow | Final evidence |
| --- | --- |
| Authentication | Normal Chrome AWS login and current pinned-account STS succeed; PALS Pro login succeeds in both browsers. |
| Lean delivery | Newly generated standalone and material-backed jobs compile, receive independent semantic approval and deliver independently reviewed explanations. |
| Source display | Private source, public shared source and repaired Activity source match the actual compiled source hashes. |
| Materials | Raster PDF OCR/confirmation, both page previews, saved project context and original download hash pass. |
| Follow-up | Actual selected-excerpt question returns a correct reviewed explanation of nonnegative integer quotients. |
| Sharing | Preview, create, copy, unauthenticated read, source expansion and revocation pass. The QA link is revoked. |
| Navigation/settings | Project/chat persistence, search/readback, settings, mathematical keyboard and Pro usage display pass. |

Stripe checkout remains excluded at the user's request. Existing historical records are
preserved. Screenshots, generated files, private logs and credentials are not committed.

## Authentication and current prerequisites

The public API health check returned HTTP 200 with `environment=prod`. Production
was still serving the three-service natural-only configuration. Fresh runtime
[inspection 38488082529](https://github.com/AtsushiHosaka/pals/actions/runs/38488082529)
bound signed sequence 27 and manifest
`6ec700a37a6daceda914934595be64fafe1dc5b6fb90999c3254dbfcfd886a50`.
Its only blocker was `assessment_queue_not_ready`; Docker reported
11,545,612,288 bytes available against 9,261,023,232 required.

On the current Mac mini, `/opt/homebrew/bin/aws` does not exist. The installed CLI
is `/usr/local/bin/aws`. The protected `pals-prod-member` configuration exists, but
STS initially failed with an expired SSO token and failed refresh. Login was
started with the available CLI and `--no-browser`, and the official authorization
URL was opened in Chrome. The user completed the existing password/MFA flow.
The CLI then reported successful login, and STS matched the pinned account and
existing operator identity. No password, token or credential was copied into Git.

Use the CLI resolved from PATH rather than assuming a Homebrew prefix:

```sh
AWS_CONFIG_FILE=/Users/hosakaatsushi/Documents/Codex/2026-10-02/task-2/mini-build-20261002/secure-handoff/aws-public-config \
  aws sso login --profile pals-prod-member
```

Fresh queue
[inspection 38488351470](https://github.com/AtsushiHosaka/pals/actions/runs/38488351470)
returned `ready`, `queues_present=true` and `permissions_present=true` with plan
`d5dd786616ea84787fb995cb440e8a6a4e5d57528b0dadf2c3a49a151b4f950e`.
Both managed encrypted assessment queues and their request-queue-only grants
already existed. This chat did not create queues or change IAM permissions.
The inspection reported `runtime_switched=false` and `database_updated=false`.

## Validation

The queue helper, queue operator, initial runtime transition and runtime template
suites passed all 85 tests. Tests requiring runtime dependencies used the
existing protected Python environment with both API and agent source roots.
Initial attempts under the minimal system environment could not import those
dependencies; the corrected complete environment passed without source changes.

## Activation and proof delivery

Fresh runtime
[plan 38488545423](https://github.com/AtsushiHosaka/pals/actions/runs/38488545423)
returned `ready`, no blockers, no queue/DB update required, and digest
`c2cba98561e3871e1574b77c1d5a2122831178fcf1a4bbba6d8e5ec38510f64d`.
The guarded
[activation 38488717364](https://github.com/AtsushiHosaka/pals/actions/runs/38488717364)
failed inside candidate cloning. Its existing rollback restored the original
three services and public API HTTP 200, with no remaining pending transition.

An isolated real Docker reproduction with the same admitted verifier image and
saved protection settings narrowed the failure to
`Candidate network aliases differ`: cloning skipped a requested DNS alias equal
to the container's own name. Docker's stopped endpoint did not publish that
implicit name, so strict pre-start validation correctly rejected the candidate.
The repair explicitly declares requested stable aliases for the full runtime on
both primary and additional networks, including resumed network attachment.
It retains strict DNS alias validation and the natural-only cloning contract.
Three new regressions fail before the repair and pass afterward. The corrected
actual Docker clone passes with the own-name alias and every compared resource,
health, port, tmpfs and IPAM field preserved; it is never started. All task-owned
fixture resources are removed after the check.

The two-network real Docker check also exposes an exact representation mismatch:
dynamic IPAM requests appear as `null` on create and `{}` on network connect.
The repaired comparison accepts only those two equivalent empty requests.
Nonempty static addresses and every other request field still compare exactly.
Two additional regressions reject different addresses, unknown fields, empty
strings and non-object empty values. The final real two-network stopped clone
passes with all protected fields and both requested name aliases.

The complete guarded host suite passes 656 checks with one existing dedicated
PostgreSQL fixture skipped. The separately run queue helper passes 15 tests.
The authority source SHA256 is
`e2225af3d645a495ee3f98ec3d1bbde9cb1b135ac62dcc615530885be4e7ed8b`.
The operator source pin and exact support-refresh predecessor tuples are updated
accordingly; the actual prior installed tuple remains explicitly accepted.

The repair is integrated in
[infra PR64](https://github.com/AtsushiHosaka/pals-infra/pull/64), commit
`4ba044e9bd7a17f685d24861ad500a126bcde365`. Parent
[PR96](https://github.com/AtsushiHosaka/pals/pull/96) merged as
`0cd833e191366f6522a45fe49eca8330ff6842d4`; repository checks passed.
The fresh support
[plan 38490420949](https://github.com/AtsushiHosaka/pals/actions/runs/38490420949)
returned ready digest
`76f1aab829352b5d5f8b0636dc4ce182cbb9376501f1a420bd5351ca637a72f3`
and the exact repaired authority SHA above.
The first refresh attempt
[38490643893](https://github.com/AtsushiHosaka/pals/actions/runs/38490643893)
stopped on the outer deployment lock before host mutation. Read-only lock
inspection found no observed openers and no pending update; lock files were not
removed or bypassed. The same guarded plan was retried normally.
The guarded retry
[38490752294](https://github.com/AtsushiHosaka/pals/actions/runs/38490752294)
installed the exact corrected authority and support pins at 09:32:55 JST. Its
receipt verifies `runtime_switched=false`, `database_changed=false` and
`queue_permissions_changed=false`.
Fresh runtime
[plan 38493377552](https://github.com/AtsushiHosaka/pals/actions/runs/38493377552)
returned `ready`, no blockers and digest
`002f51438d45c5085e39f661e6e61ec693bd5f2e860d43afe0df4ece8f05360d`.
The first post-install runtime plan stopped at shared lock acquisition before
observation. Normal retry
[38490980957](https://github.com/AtsushiHosaka/pals/actions/runs/38490980957)
returned `ready`, no blockers, and exact digest
`263ec63862f616ad10bb5424c9c9c731d16e96eb0145d169bcd57d49e510f3e8`.

Activation
[38491154409](https://github.com/AtsushiHosaka/pals/actions/runs/38491154409)
passed candidate cloning and started the verifier with healthy status, but failed
the overall service startup check. Existing guarded rollback restored the original
runtime and public API health. The API's read-only composition preflight was
reproduced in a separate Python process without starting ASGI lifespan or changing
the serving process. Its fixed error was `Guest proxy needs explicit peer IPs and
disabled ASGI rewriting`.

The serving API's PID1 has `UVICORN_PROXY_HEADERS=false`; its Docker Config.Env
does not. The protected operational capture selected only settings-model aliases,
discarding this additional required serving input. The repair captures only that
exact false flag for API, rejects other Uvicorn inputs and worker placement, and
requires it in CF guest-proxy templates and subsequent template validation. Live
capture confirms preservation without copying ambient AWS keys. With the flag
preserved, the real admitted API's read-only composition preflight passes. The
complete host suite passes 660 checks with the same one existing fixture skipped.

This second repair is integrated in
[infra PR65](https://github.com/AtsushiHosaka/pals-infra/pull/65), commit
`7337bce16c4365e2c589e8f36d462ce4433d42a3`.
Parent [PR97](https://github.com/AtsushiHosaka/pals/pull/97) merged as
`42745b1e63d37c6d119bb31c64c186d43d31725b`; repository-safety checks passed.
Fresh support
[plan 38493073327](https://github.com/AtsushiHosaka/pals/actions/runs/38493073327)
returned ready digest
`23d6c19c33068ff22450d6d0dbfb7dc37aff3a86c7d7d8bd7c451f0608acb134`.
Guarded
[refresh 38493231566](https://github.com/AtsushiHosaka/pals/actions/runs/38493231566)
installed the exact new capture/planning and template helpers at 09:59:56 JST,
with `runtime_switched=false`, `database_changed=false` and
`queue_permissions_changed=false`.

Activation [38493571665](https://github.com/AtsushiHosaka/pals/actions/runs/38493571665)
starts API successfully, but worker/reconciler startup still fails and guarded
rollback restores the original runtime. Saved worker templates inherit `Entrypoint
=["sh"]` while their new `Cmd` already begins with `sh`. The admitted worker image
reproduces exit2 (`cannot open sh`) in a network-disabled temporary container before
any application startup. The repair replaces only known shell entrypoints with the
explicit credential-launcher command; unknown wrappers fail closed.

The verifier validates its entire workspace before binding the mTLS listener.
Initial activation previously started the reconciler immediately afterward without
waiting. A bounded check of the fixed verifier-local ready marker now precedes the
reconciler start, both in initial activation and ordinary forward recovery. Later
mTLS binding and complete service health checks remain required. This addresses a
possible dependency race; the prior closed reconciler error did not establish its
exact cause. Dependency-order, bounded marker and failed-start rollback regressions
pass. The complete guarded host suite passes 668 checks with one existing fixture
skipped. The corrected authority SHA is
`65567221f79c160f83fddfb0ad1c2dbb49eebf5c65768738b0810af03d9eebd2`.
[Infra PR66](https://github.com/AtsushiHosaka/pals-infra/pull/66) is merged as
`73522a00faa1b620e59234acbafae3fb7f973e21`.
Parent [PR98](https://github.com/AtsushiHosaka/pals/pull/98) merged as
`e4be3a5cf06fa1686b77adcd629f4baa5c545243`; repository-safety checks passed.
Fresh support
[plan 38495871911](https://github.com/AtsushiHosaka/pals/actions/runs/38495871911)
returned ready digest
`5b1af3450f8d04c56e8c6c531572527ac41fe7338b4faad226a5004965faaab1`.

## Sealed finalization and restricted reconciler startup

[Infra PR67](https://github.com/AtsushiHosaka/pals-infra/pull/67), merged as
`42e50189ae1e21beda459918d53ddf55927db6e2`, makes finalization re-observe
the exact sealed initial PKI profile, including private API TLS, through the
hash-pinned adapter. The ordinary three-role profile cannot re-observe a sealed
four-role profile. All equality, health and newly verified/delivered job checks
remain required. The guarded host suite passes 672 tests with one existing
dedicated PostgreSQL fixture skipped. Parent
[PR99](https://github.com/AtsushiHosaka/pals/pull/99) pins this repair.

[Activation38498303941](https://github.com/AtsushiHosaka/pals/actions/runs/38498303941)
started the verifier and corrected workers, but the reconciler exited with a
closed `RuntimeError` startup diagnostic. Guarded rollback restored the base
runtime. A separate read-only process reproduced `pex_path_id_migration_required`
with PostgreSQL SQLSTATE42501 under the actual reconciler role: the general API
startup check reads learner explanations and clarification conversations, which
this dedicated role intentionally cannot read.

[API PR19](https://github.com/AtsushiHosaka/pals-api/pull/19), merged as
`7c07b05a44a1b1e40f48f666b75dbc3802e1a510`, adds a read-only role-specific
preflight for proof-job paths and required verification-candidate columns. The
ordinary API keeps its complete learner-output checks; controlled release still
owns schema/ACL certification. Invalid paths, missing columns and missing access
remain failures. No database grants or migrations change. Thirty-seven focused
startup/path/delivery tests and changed-file Ruff pass. The new method succeeds
under the same actual production role without application lifespan, reconciler
loop, jobs or database writes.

Parent [PR100](https://github.com/AtsushiHosaka/pals/pull/100) merged as
`2d5077295d11ea13a1ed71d8f760ec00e8283906`. Explicit
[deployment38512289919](https://github.com/AtsushiHosaka/pals/actions/runs/38512289919)
returned a healthy receipt with API image
`sha256:f3f31fa831046e82984c545eae741dbd6e3f67f098677dbc8ceb350a296f8496`
and signed manifest
`2e663f153f4dd568b76b10528f25dcdd25f079e826c3143ee022e9594a017387`.
The actual deployed API image's new method passes the read-only reconciler-role
probe. Support [plan38545470906](https://github.com/AtsushiHosaka/pals/actions/runs/38545470906)
returned ready digest `95083b3b2593043dcc5faf276fbb65ca5f043992fea16f900d6f7dc5f8e518bb`;
[refresh38545637406](https://github.com/AtsushiHosaka/pals/actions/runs/38545637406)
installed it without runtime, DB or queue-permission changes.

## Actual proof handoff failure and generation authority repair

Normal Chrome SSO succeeded; [activation 38553082277](https://github.com/AtsushiHosaka/pals/actions/runs/38553082277) returned a healthy six-service runtime. This was not treated as proof delivery. A fresh browser number-theory request reached assessment but its formal settlement returned `proof_request_persistence_unavailable` (503). All three metered calls had successful receipts; PostgreSQL identified missing INSERT privilege on `proof_jobs`. On claim expiry the request failed with `token_usage_unknown`.

[Infra PR68](https://github.com/AtsushiHosaka/pals-infra/pull/68), merged as `337a66e165bf1f6f12cd9635c6fc3f8529f008ea`, repairs recovery after healthy startup but before proof finalization. That interval retains original containers but has a current pointer instead of a pending pointer. The new entry point checks the exact immutable record, admission, profile and original IDs before recreating a bound recovery phase. All 673 guarded host tests passed (one dedicated PostgreSQL fixture skipped).

The reviewed, SHA-checked recovery function was invoked under the original deployment/lifecycle/admission locks with installed dependencies still hash pinned. It restored the preserved natural-only predecessor and reported `database_updated=false`. No host policy, signed admission, proof status or receipt was manufactured to bypass finalization.

[API PR20](https://github.com/AtsushiHosaka/pals-api/pull/20), merged as `43d60ddcac7be600306db9798db9d8aaa7ab860c`, installs only named generation column grants inside the signed, drained Mac update transaction. API INSERT and UPDATE on compiler attestations remain denied for both jobs and candidates. Generation SQL omits protected attestation fields, and full production startup performs a read-only authority check. Canonical SQL, verification constraints and stored rows are preserved.

An owned, temporary canonical PostgreSQL fixture proves job creation, claim acquisition and progress updates succeed while attestation INSERT/UPDATE and unverified promotion fail. Twenty existing PostgreSQL generation/linked-request tests, 52 startup/path/delivery/language checks and Ruff passed. A broader signed-update fixture failed during its initial-bootstrap setup before update cases; it is not claimed as passing. Both temporary PostgreSQL containers were removed by exact owned IDs.

Parent [PR102](https://github.com/AtsushiHosaka/pals/pull/102) merged as `f270c360f10ea38acedad1004446eea400bb725d`. Explicit [deployment 38557789664](https://github.com/AtsushiHosaka/pals/actions/runs/38557789664) returned healthy with API image `sha256:4c02e97f69a8e47c0e797ac99565c456523df730b14ff6fd0059e4e8312e9709` and signed manifest `0557cf9bd05fca82a3dee9d7cb2d5b19acc2befb06283246f07f1fc47f520d80`. Actual production read-only ACL observation confirms generation columns are writable and attestation columns remain non-writable.

Pending: reactivate the repaired full runtime, verify a fresh browser proof and its exact source, finalize preserved containers, then deploy and validate the independently tested material-confirmation correction. Stripe is deferred by the user.

## Compiler deadline and cancellation follow-up

Reactivation [38558719086](https://github.com/AtsushiHosaka/pals/actions/runs/38558719086) returned healthy at signed sequence 29. Browser retry created a new proof job, progressed through Draft generation and submitted actual Lean source. The full Mathlib source hit the isolated verifier's compiler deadline and identical retries. This was not reported as proof success.

A valid coprime-divisibility control under the admitted image also exceeded 45 seconds with the full import. Its focused-import counterpart compiled successfully in 13,598 ms with network disabled and no mounted credentials or database access. Native Lean/ARM64 version was verified from the admitted workspace; no toolchain was installed or altered.

Only the chat-owned stalled job was canceled through the existing application repository under the restricted runtime role after checking exact request ID, chat ID, source SHA, absent attestation and its already-failed candidate. A fresh ordinary claim and the normal cancellation transition preserved code and recorded an event. Normal request reconciliation reported `lean_verification_failed`; no verification state or receipt was manufactured. Guarded [recovery 38562014528](https://github.com/AtsushiHosaka/pals/actions/runs/38562014528) restored the preserved predecessor with no database update.

[API PR21](https://github.com/AtsushiHosaka/pals-api/pull/21) distinguishes a complete authenticated job-bound compiler 504 from uncertain network failure: the former enters bounded model repair; the latter retains transport retries. Cancellation also retires only unverified pending candidates while preserving their code/bindings. Thirty-one reconciliation tests, the canonical PostgreSQL authority/cancellation test and 20 existing PostgreSQL generation/linked-request tests passed.

[Agent PR13](https://github.com/AtsushiHosaka/pals-agent/pull/13) preserves exact confirmed OCR text, content-bound issued question IDs, immutable snapshots and unresolved premise questions. Ninety-five related tests passed. [Agent PR14](https://github.com/AtsushiHosaka/pals-agent/pull/14) prefers focused Mathlib imports without removing full-library support or weakening proof targets; all 45 generator tests passed. Parent [PR103](https://github.com/AtsushiHosaka/pals/pull/103) integrates these fixes for the next signed deployment.

Parent PR103 merged as `6f4af0c194edf00a2e0f2d42d1e876b2b7dd0f08`. Explicit [deployment 38562518431](https://github.com/AtsushiHosaka/pals/actions/runs/38562518431) returned healthy at signed manifest `cf5d401e521d7bf525c0ae7666040ed92b60dfdf09ea9c25d1ba00e0d79c105f`, API image `sha256:ae4106a5dda34acae7e5f6d9e8e9cef7621ba625fd7c4965eb42a7b856a4abba`, worker image `sha256:01dcc12954852a3506f1b5a7461d24d060481bc00788dfe04fd0875fa689b318`. Read-only historical observation of the original generated failure reconstructs a valid bounded repair seed; no incomplete seed is accepted or regenerated from scratch.

## Delivered proof and exact browser source

The first focused-import proof compiled, but its reconciler transaction failed with SQLSTATE42501 because the dedicated role lacked schema USAGE on `pals_draft_candidates`. [API PR22](https://github.com/AtsushiHosaka/pals-api/pull/22), merged as `0abc2f5cdc0ec57255c909c72d3aebf544150a28`, grants only USAGE and EXECUTE on the existing bound receipt RPC. It grants no private-table reads/writes, capture or publication authority. Actual PostgreSQL scope/validation/replay/drift tests and Ruff passed.

The two fixed grants were applied transactionally through the exact reviewed installer under deployment/lifecycle/admission locks, after verification of the unchanged sequence 30 KMS signature, source SHA and undrifted schema. Its changed ACL fingerprint was recorded; signed admission, trust fence and proof rows were not edited by the operator. The existing authenticated API candidate-reconciliation retry then scheduled the stalled candidate. The actual compiler's bound attestation was persisted. The normal configured worker's real semantic reviewer, explainer and output reviewer resumed only this owned job in a bounded one-shot recovery, without receiving or fabricating an SQS receipt. Normal API claims and settlement checks remained active.

[Browser chat](https://palschat.site/chats/bd42079f-5404-4cb6-9ad4-df9429e0ecc2) request `1e1f0e5d-5a1b-4313-a3a0-a9aed2d4cfbb` is `answered`; newly generated job `b03bc8e8-cd20-4076-ad0e-71206d920621` is `verified`. Compiler success, job/source attestation binding, independent semantic approval, completed explanation and answer job/source binding all match. Evidence kind is `lean_verified`.

The learner-facing proof explicitly covers natural zero and coprime divisibility. Opening its Lean panel succeeds. SHA256 of the actual displayed DOM code is `ba42d906ca8cc9ed05f008cf96ce973e77062327cb88a22e70ae8e86fcec813f`, identical to the stored source, compiler attestation and answer reference. A screenshot is retained in the task's local visualization artifacts, not Git.

Guarded [finalization 38567829746](https://github.com/AtsushiHosaka/pals/actions/runs/38567829746) succeeded for that exact fresh, verified and delivered job. Remaining work: normal signed deployment of parent PR104's durable receipt authority and remaining authenticated functional QA.

## Full-profile normal update transport

[Normal deployment 38568163752](https://github.com/AtsushiHosaka/pals/actions/runs/38568163752) failed before database apply. The ordinary bridge attached its loopback PostgreSQL proxy to `application_network`, now the internal Lean trigger bus. Both attached networks were internal. The proxy's own listener and database TCP connection worked, but native loopback forwarding did not. Its standard failure recovery also could not observe the database and retained stopped writers and ingress. A browser reload correctly exposed HTTP502; this was not counted as a successful release.

[Infra PR69](https://github.com/AtsushiHosaka/pals-infra/pull/69), merged as `e5bd820cd99144d495970fd1466b4c6e500aa865`, chooses the unique noninternal bridge already recorded in the protected API predecessor. It changes no network isolation, credential, signed admission or database permission. Missing/ambiguous publication networks remain failures, and the legacy three-service transport is retained. All 675 host tests passed (one dedicated PostgreSQL fixture skipped) with the API/agent dependencies available; an initial incomplete dependency environment and old pin fixture were corrected before the successful run.

The tested transport methods were used with the unchanged installed signed observer under deployment and inherited lifecycle locks. The observer acquired its own admission lock, verified the actual previous admission, and standard recovery restored all six services and ingress without a database update. An initial parent-held admission lock caused its fail-closed observer to return `unknown`; this was not overridden. Automatic approval initially rejected removing that extra parent lock; after the standard CLI's internal admission locking was demonstrated from source, the reviewer approved the standard locking procedure. No lock file was removed or validation skipped.

Parent [PR105](https://github.com/AtsushiHosaka/pals/pull/105) merged as `85b04af8ca001bc260ce7e06d83e007fb181e7b0`. The exact reviewed normal authority SHA `6cd527457603ffa662e7fec0b2ae8dece67f095419e521bc2eef59ca7aea77ba` and its policy pin were installed atomically with a recoverable backup under deployment/lifecycle/admission locks. The existing KMS-signed carrier, admission and all running service IDs were verified unchanged. No database update or service switch occurred during that installation. [Normal deployment 38571570273](https://github.com/AtsushiHosaka/pals/actions/runs/38571570273) was then explicitly requested.

After public recovery, both raster PDF page previews render. Normal Chrome login and original download succeed; the completed download SHA `35d048c743f799f87664a6fde5a66b1b810093e7ee70b7907ce4cdbb8323e6cd` exactly matches the uploaded two-page, zero-embedded-text PDF. The in-app download event timed out, so the normal Chrome completed download and filesystem hash are used as the actual evidence. Generated files and screenshots remain outside Git.

[Normal deployment 38571570273](https://github.com/AtsushiHosaka/pals/actions/runs/38571570273) succeeded at sequence 31 with healthy full runtime, parent `85b04af8ca001bc260ce7e06d83e007fb181e7b0`, manifest `88f803f5cc06a68dfd188c05054355016a162cfb6f56e765896d0dc398a9cc4b`, API image `sha256:604401654476a3db4871249d9d60dab4041b307eb8e509eefe11e9a24c0817d3` and worker `sha256:35454df4bb17cf88d63633e35d8acc70304f5a2473d288d307b9e88ddac7d478`. The retained browser answer and exact displayed Lean hash still match after reload.

## Authenticated QA follow-up

The saved project request `e6639e58-09b9-4977-a743-8cebf3a435ed` accepted its latest issued confirmation once and advanced through the ordinary queue, without another confirmation loop or manual worker recovery. Fresh job `65dc8459-c10d-4580-9f97-4425630839a1` reached actual compiler verification and independent semantic approval with source SHA `25c25a7b042aef7487b396f27fb03d100f3c757a9760ac731d925d4ceb69808b`. Bounded compile corrections occurred before success. Its explanation was correctly withheld when the independent output review rejected duplicated exposition; a normal browser retry also withheld a correction that omitted the natural/integer quotient justification. These are failures, not delivered-proof evidence.

[Agent PR15](https://github.com/AtsushiHosaka/pals-agent/pull/15), merged as `807b7beb0b52b5ef5ca15f6b8a7ab073e8caec5e`, makes generation explicitly justify number-domain conversion. It distinguishes a short closing statement of an established claim from duplicated substantive derivation or a repeated complete final equality. Existing parser, mathematical grounding, independent approval, content/source binding and bounded correction remain intact. All 170 tests in six explanation/worker suites and changed-file Ruff pass.

Sharing preview loaded, but publication failed in both browsers. Read-only inspection of actual adapted Caddy routes found missing private POST/DELETE sharing and public GET snapshot routes. [Infra PR70](https://github.com/AtsushiHosaka/pals-infra/pull/70), merged as `0406b03dc45ca42913ee7213fbc2b66847e646e5`, adds exact routes and upgrades only the exact prior materials prefix through the existing bound plan/backup/rollback installer. It preserves every unrelated route, authentication header, CORS policy, network and runtime identity. All 101 edge/installer tests pass, including actual isolated Caddy HTTP checks. The fixtures use an existing immutable API image and read-only copy of the existing Caddy binary; their owned temporary containers are removed. An unauthenticated production POST/DELETE diagnostic was rejected by automatic approval review; no such probe was executed. Read-only configuration inspection established the missing routes instead.

Settings open normally. The usage view reads permanent complimentary Pro, the 3,000,000 monthly quota, actual used/reserved/available units and its refresh date. Paid checkout remains deferred by the user. Search finds the owned positive-integer proof chat and opens it without losing its project membership. Stable post-release sidebar reloads load all projects/chats; initial in-flight release/read failures are not hidden or counted as successful checks.

[Parent PR106](https://github.com/AtsushiHosaka/pals/pull/106) merged as `1206974112b9c884069993838ab37c64c559dfa8`. [Deployment 38576550439](https://github.com/AtsushiHosaka/pals/actions/runs/38576550439) succeeded at sequence 32, healthy full runtime, manifest `8c5a783ed5b0aecff74b857a47084e2012fc9451aac220ce3c59bf21b110d6bf`. API image is `sha256:eba73e1745613eec0a1ce58fba7982ff9b31e4fa0ac20e84d1bafc1ec6aef1ee`; worker is `sha256:22fffab857419a784bddf6aa3e500b083399302c63c4f0c2509d0aa1fdb1a580`.

The exact [edge plan 38577026022](https://github.com/AtsushiHosaka/pals/actions/runs/38577026022), `3ee3a82856a8d5d4f0b13da2b53fb9e54038d5f9161a90cb9990528485735c1a`, bound that current runtime and old 13-route configuration. [Installation 38577469622](https://github.com/AtsushiHosaka/pals/actions/runs/38577469622) succeeded with configuration hash `c84aa14b931b45499f53a14768f7e8438dd0febd7a25b566f124d52f88ea3e27`, a recoverable backup and unchanged service identities. No application/DB switch occurred.

The project's normal browser explanation retry then completed: request `e6639e58-09b9-4977-a743-8cebf3a435ed` is answered with `lean_verified`, no error, completed independently reviewed explanation, and matching job/source references and compiler/semantic evidence. Actual private and public browser code both hash to `25c25a7b042aef7487b396f27fb03d100f3c757a9760ac731d925d4ceb69808b`. Public sharing creation, copy, fresh unauthenticated-page read and code expansion succeed. Revocation succeeds; reloading the same public link makes it unavailable as intended. The QA link is revoked and its temporary tab is closed.

Selecting the nonnegative-quotient passage on the narrow-screen natural-number proof opens its question form. Actual follow-up `af026b16-c8bb-4c04-856d-7e77a145f330` completes as `reviewed_explanation`, without falsely labeling that prose a new Lean proof. Its visible answer argues that an integer quotient `k<0` implies `k<=-1`, hence `c=ak<=-a<0`, contradicting `c>=0`. Normal Chrome reload also reads the saved proof and this additional answer without the old sharing error dialog.

The material context remains bound to the exact owned project and both PDF pages; both saved source content hashes match the original downloaded PDF. The current presentation intentionally preserves OCR provenance without mounting the OCR citation panel in proof prose (`proof-request-material-presentation.test.tsx`); the evidence is the saved context, actual proposition confirmation and project page preview, not a claimed visible citation.

Final Activity-panel QA found a separate deterministic failure: its inline reader defaulted to a projectless scope while the actual verified source belongs to this project. [Frontend PR23](https://github.com/AtsushiHosaka/pals-webfront/pull/23), merged as `ee35e1f92012c5a02b7bcf6e804da5d500194729`, forwards the existing project ID through the panel to the unchanged exact source validator. Both regressions failed before the repair; 58 focused source/activity/boundary tests, TypeScript and changed-file ESLint pass. The React skill check found no new state/effect, fetch waterfall, event listener or bundle dependency. Test dependencies use a lock-identical existing cache and managed ARM64 Node; the owned temporary cache link was removed. This last repair still requires its explicit production deployment and Activity-panel source readback.

The corrected native AWS CLI's final STS read succeeds for the pinned account using `pals-prod-member`; no additional browser authentication is needed at this point.

## Final signed release and browser readback

[Parent PR107](https://github.com/AtsushiHosaka/pals/pull/107) merged as `4e629e7a3d01a3d6eff935a8cb752189bea9588b`. The first deployment attempt [38584644601](https://github.com/AtsushiHosaka/pals/actions/runs/38584644601) stopped before changes because the host's existing automatic recovery held the deployment lock. No lock was removed or bypassed. Normal retry [38585152330](https://github.com/AtsushiHosaka/pals/actions/runs/38585152330) succeeded with healthy full runtime at sequence 33, manifest `40949e536c019e61bcec824e0a19f0dbe0e0cff6083a63f0bf27eede2b5039ce` and web image `sha256:09cb2ca51e7974d7bc9a2dca9653b069a4a33ab563065f91b93a746bc5044a3c`.

A fresh browser reload of the original project chat now opens its Activity panel, renders the completed explanation and loads the exact verified Lean code without an unavailable-source alert. SHA256 of that actual Activity DOM code is `25c25a7b042aef7487b396f27fb03d100f3c757a9760ac731d925d4ceb69808b`, matching private/public source, job/answer reference and compiler evidence. The final read-only proof observation still reports answered, verified, `lean_verified`, compiler binding/semantic approval/explanation completion all true and no error code. Current captured API diagnostics contain no recognized exception or source-error frame. A current screenshot is saved in the task's local visualization artifacts and displayed in the completion reply.

The final production implementation pins are API `0abc2f5cdc0ec57255c909c72d3aebf544150a28`, agent `807b7beb0b52b5ef5ca15f6b8a7ab073e8caec5e`, infra `0406b03dc45ca42913ee7213fbc2b66847e646e5` and frontend `ee35e1f92012c5a02b7bcf6e804da5d500194729`. Documentation-only follow-up commits do not require another implementation deployment.
