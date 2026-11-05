# Settings production release — 2026-11-05

Tracking: [#265](https://github.com/AtsushiHosaka/pals/issues/265).
[Session](codex://threads/01a1aac0-d36c-7331-9a73-a79dc78d1a0a).

Status: **guarded cutover paused before admission; previous runtime restored and
healthy**. Seq21 has not been admitted or activated. The real production
settings checks after deployment remain pending.

## Authorization and review

The owner requested review of Web #49 and parent #268, merge if sound, production
deployment, and checks on the actual settings screen at desktop, phone width,
and enlarged display. Independent code/evidence reviews passed. Web review reran
69 targeted tests; parent review reproduced all six charts, passed 22 ledger
tests, and confirmed preservation of prior rows. Those test counts are not
product-quality measurements.

Both PRs merged with their reviewed heads unchanged:

| PR | Reviewed head | Merge |
|---|---|---|
| [Web #49](https://github.com/AtsushiHosaka/pals-webfront/pull/49) | `9332a04109625da192891466e91c14a5140e4609` | `6d221f73ed2b5aceca4330ef978a712999d00f46` |
| [Parent #268](https://github.com/AtsushiHosaka/pals/pull/268) | `d8f882b64d5f4a7e139572321b78803108d0020f` | `f3e80d2b5d5edfc71bd6e6ce204d7de344f357f5` |

A minor automated review comment about the abbreviated test command was
verified and addressed in the follow-up documentation; it does not affect the
frontend repair or release image.

## Exact Web-only candidate

Fresh native checks confirmed the actual seq20 predecessor, seven running
services, exact firewall/readiness/recovery state, and no canonical release
owner. After AWS SSO expired, the owner completed normal sign-in. Identity was
rechecked, and read-only reconciliation established that the failed preparation
dispatch had not been accepted. Both native health checks then passed again.

The source capture starts from the deployed parent and changes only its Web
gitlink. The planning repository's historical non-Web pointers are not used as
release source. The canonical five-source capture guard passes, with API,
infrastructure, worker/verifier source and all existing capabilities retained.

| Artifact | Exact identity |
|---|---|
| Release parent source | `7e986cbc7658b57c3d7bdecbe9ebf7ce27034f3f` |
| Web source | `9332a04109625da192891466e91c14a5140e4609` |
| Source capture SHA-256 | `354e7c5a4032d0d0bf7e5ae5d2c3f96b737357e616f942c810a616740a26fad6` |
| Exact Web archive SHA-256 | `885ccdcc727d53dd3fb410c0d5f500d24df757e95b02198c8097a92527218e6e` |
| Verified build-arguments SHA-256 | `7b485ce536b0ffd17a8a49b1234ca7b617ba83c936d535a3fdb5d91e66003876` |
| Published immutable Web index digest | `sha256:93d88779e914485ae41df9137cb6525ee130e261e3794ad4b947a5c3f77cea72` |
| Selected arm64 manifest digest | `sha256:fc86042549826894fd9e5bd39cd94055b5be390f6f7acb953275224f8fcd5730` |
| OCI configuration digest | `sha256:a662bafd4b572be9d42c92a1eb6b65b0c93fb8c3ed45cf9a36e96b38d635749d` |
| Formal v2 publication receipt SHA-256 | `bc1e1a8301933c76304f2997d4f6777e9722e14a3c04411aad356bbbd765df78` |
| Signed seq21 manifest SHA-256 | `a00fd5b9a39ce1918e2ebd93e347b6cc22af51d9c73d60e94a8a3d78b5aeb773` |
| Actual signature SHA-256 | `919dd76075269b8db525d29157c5f892d698d1d5f69cf7b2f87265f8b295b7da` |

The signed window is 2026-11-05 08:56:30 UTC to 2026-11-06 08:56:30 UTC
(17:56:30 JST to the next day). It is a separate Web-only seq20→21 transition,
not the unsigned coupon/schema candidate. Schema35, runtime bindings,
non-Web images, platforms, Lean/Lake identities and infrastructure are unchanged.
The pinned API's pure transition check and independent canonical/signature/
receipt/source reviews pass. Signing is not admission or activation.

## Native preparation and retained failures

Both actual native preparations returned `prepared_not_admitted_not_activated`.
Their exact protected metadata was exported without environment or credential
values. The public-only operator bundle staged successfully. Post-preparation
observations confirmed the old runtime was exact and running before cutover began.

The first owning read-only preflight failed with `ClientError` at
`plan-predecessor-signature`. Both bounded operator containers and RAM files
were removed, and the serving actors were unchanged. No DB admission, traffic
drain, or activation occurred in that preflight. Temporary verification access
is limited to the exact KMS Verify/GetPublicKey and Aurora Describe scope, with
no Sign/DB-write/wildcard permission. The grant has now been removed, and its
absence was confirmed. Any replacement requires fresh explicit approval.

A later authorized owning read-only preflight passed all 35 existing steps
with zero database mutations. That successful preflight is distinct from
admission, activation and the earlier retained failure.

An initial helper-staging attempt failed on both hosts **before any write**.
The new stager had compared pretty-printed material-job file hashes with the
native preparer's canonical serialization hashes. The two constants were
corrected using the actual prepared metadata and independently recomputed
`encoded(packet.job)` values; all checks and payload files were retained.
The independently reviewed v2 then staged all nine exact helpers on both hosts,
preserving the original preparer. Failed responses and source are retained.

Native Web prewarm passed the exact OCI index/manifest/configuration, all nine
RootFS layers, source/platform and owning image checks. Temporary ECR
authentication was removed. No new application container or service started.

## Guarded cutover pause

The cutover paused after one host was quiesced: the next drain guard found one
active generation claim and refused to proceed. Read-only diagnostics showed
that the remaining lease left insufficient time for the bounded cutover and
cleanup. No database admission
occurred, and the signed candidate was not activated.

The exact retained previous workers were resumed without recreating actors or
changing configuration, images, networking, firewall or recovery units. Both
independent native health checks passed: all seven previous services are running,
readiness and firewall checks pass, and the latest database admission remains
seq20. The identical public target is healthy again and all 14 target-group
attributes match the saved baseline. Temporary verification access was removed,
and actual provider absence was confirmed while awaiting a new approval.

Before any renewed ingress restriction or quiesce, run a fresh pre-cutover check:
confirm the previous runtime is healthy, no active generation claim or in-flight
work remains, ownership is exclusive, and approved verification access has enough
validity for the bounded attempt and cleanup. A lease estimate or elapsed wait
does not prove that the claim has cleared. Continue only from reconciled actual
state; do not automatically retry partial phases.

## Actual browser baseline and remaining acceptance

The owner signed into the existing production app through its normal UI. The
actual account settings loaded from the real backend. Before deployment,
Japanese desktop 1280×900 and phone-width 375×812 both reproduce **0px** between
the last control group and first action button in both forms.

The enlarged-display method is now verified using Chrome's native View → Zoom
In and native shortcuts: device-pixel ratio changed from 2 to 4 and CSS viewport
width from 1272 to 636, establishing actual 200% page zoom. Zoom was restored.
This establishes the test method on the old release, not acceptance of the new
release. Screenshots are restricted to the settings dialog; account and chat
details are not published.

Remaining gates: actual claim clearance, fresh approved verification access and
positive pre-cutover checks;
exclusive ownership and guarded cutover/admission; final recovery, health,
ingress and permission-cleanup evidence; and post-reload production
desktop/phone-width/200% settings checks. Partial or unknown phases require
reconciliation rather than automatic retry or rollback.

Private artifacts and exact operation responses remain outside Git under the
task-owned release directory. No credentials, role/host identifiers, internal
addresses, raw account/chat content, authentication codes or tokens are included
in this record. This record will be updated from actual remaining results.
