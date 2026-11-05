# Shared-card footer clearance for X — 2026-11-05 JST

Tracking: [release #248](https://github.com/AtsushiHosaka/pals/issues/248),
[Open Graph #228](https://github.com/AtsushiHosaka/pals/issues/228),
[permission decision #256](https://github.com/AtsushiHosaka/pals/issues/256),
[Web PR #47](https://github.com/AtsushiHosaka/pals-webfront/pull/47).

Current status: **seq20 is deployed; both hosts, recovery configuration,
temporary-permission cleanup, production HTTP/card rendering and the actual X
footer clearance are verified.** X displayed the corrected card using the
versioned share link; the canonical link's cached preview was not confirmed
refreshed.

## Requested change and measured layout

The seq19 card appeared in the actual X draft, but X's black title overlay partly
covered the orange verification footer. The owner requested moving the marker
and `Verified with Lean` upward together, followed by review, merge, deployment
and another actual X check. The earlier result remains recorded in
[the seq19 report](proof-share-smoke-2026-11-05.md).

The revised 1200×630 layout moves both lower edges from y=570 to y=522: **48 px
upward**, preserving their alignment. Solid orange marker bounds are
`x=72–111, y=517–522`; text bounds are `x=131–481, y=491–522`.

| Actual layout fixture | Footer lower edge | Headline-to-footer ink gap | Result |
|---|---:|---:|---|
| Short | 522 px | 139 px | Pass |
| 80 glyphs | 522 px | 40 px | Pass |
| 130 glyphs | 522 px | 44 px | Pass |
| 160 glyphs | 522 px | 31 px | Pass |

These are four layout fixtures, not mathematical questions or a proof-quality
benchmark. They establish fit for the checked cases. The initial padding-only
attempt cleared only **1/3** fixtures; two still overlapped. Those failed renders
are retained privately rather than replaced by the final **4/4** measurements.

## Reviewed source and signed candidate

PR #47 merged as `92542958b4bfd2720b7f30053b40bead7fafb6d4`. The actual image was
built from reviewed source `41b3d1c1738bdf756e3a53c84b423ad554cd512d`, bound by
clean parent capture `91aed0f8f8b1828acac7ea7025cbcc2e3f2a4e77`.

| Artifact | Exact identity |
|---|---|
| Published Web image | `sha256:cf51def1325b89d1d753cde306b8ff0c0aa4a4f34c958f61e30e1e09ef1e968f` |
| Formal publication receipt | `49023dd3865daca11ec1ac2c135674fe37acf6bce5189b79741ab9b78f8bf48d` |
| Signed seq20 manifest | `2c7b96baa2d0b7577f52d5793fe5fb849639bdf688a5a86ef9814a17c2da6afa` |
| Actual built/native preview PNG | `0434a0bde9ba55edec40e374125ed25f5bc59fca21d568308f952a174391d38f` |
| Four-fixture measurement record | `0b31b1c81962a9be9d4c72af5e4a8e1fa5b03bd20a816594ca63ea14fb9afa4c` |

The signed window is **2026-11-05 06:03:04 UTC through 2026-11-06 06:03:04 UTC**
(15:03:04 JST to the next day). The candidate preserves the existing API, worker,
verifier, infrastructure, 35-step database contract and Lean/Lake identities.
Only the Web source/image and parent gitlink advance.

## Executed preparation gates and retained failures

| Actual gate | Evidence and boundary |
|---|---|
| Native preparation | Both hosts returned `prepared_not_admitted_not_activated` at 06:08:36–37 UTC. Preparation did not activate services or admit the DB. |
| Strict native image prewarm | Completed at 06:19:00 UTC; source, platform, independent image/configuration and nine filesystem layers passed the owning image guard. Temporary ECR authentication was removed. |
| First native preview dispatch | Failed with `SyntaxError` before preview code executed. This was a dispatch-source failure, not a font, API or rendering result. |
| Second native preview dispatch | Failed on a stale current-config reference before a test container started. It supplies no render result. |
| Corrected native preview v3 | Passed at 06:25:45 UTC using the existing Web network namespace and live shared-snapshot API/font dependencies. Its 1200×630 PNG matched the actual built image bytes. The test was removed and serving actors were unchanged. |
| Owning read-only preflight | Passed at 06:27:32 UTC: 35 release-schema and 35 runtime checks, zero DB mutations, with task container/RAM cleanup and unchanged serving actors. |

The first two preview failures remain separate observations. The successful
native preview used the existing owner-requested snapshot, introduced no new
share or model-generation request, and did not exercise the public X composer.

## Permission window and cleanup

The owner approved a new 45-minute verification window in decision #256. Exact
policy readback records attachment request start at **06:27:01 UTC (15:27:01 JST)**,
capped at **07:12:01 UTC (16:12:01 JST)**. The scope remains exact-target KMS
verification/public-key and RDS metadata reads in Tokyo, without Sign, schema,
coupon or other write permissions. This approval is separate from the already
removed seq19 grant.

The exact temporary policy was deleted and its absence confirmed with
`NoSuchEntity` at **06:57:55 UTC (15:57:55 JST)**, before the 07:12:01 UTC cap.
The cleanup did not treat an access denial as evidence of absence.

## Actual cutover and bounded reconciliation

The first control quiesce attempt failed at **06:34:31 UTC**, returning
`FileNotFoundError` in `actual-prepared-state`. The launched-child wrapper
conservatively recorded `child_may_have_mutated=true`; this failure is retained
separately. The closed error did not identify the missing path or establish a
root cause. Its recorded lifecycle phase preceded the control SIGTERM stage,
without overriding that conservative mutation boundary.

Two subsequent read-only diagnostics passed the preparation prerequisites,
launch-lock and ownership boundaries. They found the same four control actors
running. No missing prerequisite file was created and no guard was relaxed.
After this bounded reconciliation, **one explicit retry of the unchanged
quiesce operation** passed at **06:40:55 UTC**, with `forced_stop=false`.

| Actual completed phase | Evidence and boundary |
|---|---|
| Owning seq20 DB admission | Passed at 06:41:34 UTC with the actual five-step `released` receipt: identity, existing schema/roles, exclusive quiescence, signed admission and DB preservation. |
| Both finalized configurations | Control and compute both passed materialization plus owning load/plan checks. Finalization alone did not start them. |
| Control cleanup and core start | Exact old owned resources were removed, preserving old material. The new core reached `core_ready_reconciler_stopped`; final application readiness was checked separately below. |
| Compute cleanup and start | Idle-verifier cleanup and actual start passed the signed control-admission and Landlock image-source gates. The initial start result was `started_not_capacity_admitted`; final readiness was checked separately below. |

Traceability hashes for these actual results:

| Artifact | SHA-256 |
|---|---|
| Actual seq20 DB admission receipt | `7f77fae9a66eb1d2c844ac022b6bf6c559c61c0e7c732eac736e1115a2085a83` |
| Final control configuration | `9ae7fe087c1854e8a800f28ee64c3bd6442fc4733b706ad8314df510e962eacf` |
| Final compute configuration | `8edd697a559965b42e8bb25dfe5423b88d8e1d738814dd9a2c1fca3618074692` |

## Final native and public HTTP verification

The control and compute health checks passed at **06:54:47 UTC** and
**06:57:16 UTC** respectively. Both were ready on seq20 with all **seven actors
running across two hosts**, exact firewall checks and the three enabled recovery
units bound to the new recovery configurations. Control confirmed latest DB
admission sequence 20. These are two host checks, not seven independent trials.

Public ingress was restored with the existing target and attributes unchanged;
the target read back `healthy` at **06:59:33 UTC**. The canonical owner operation
completed and released ownership at **07:00:05 UTC**. The admitted
software/schema scope remains the signed Web-only change described above.

Actual production Twitterbot HTML and its PNG passed the HTTP check. The image
was **1200×630**, with SHA-256
`0434a0bde9ba55edec40e374125ed25f5bc59fca21d568308f952a174391d38f`:
the same bytes and decoded RGBA pixels as the approved/native image. Marker and
text lower edges were both **y=522**. HTML and image retained private/no-store,
noindex/nofollow/noarchive and no-referrer headers. This verifies the public PALS
response. The separate actual X result is recorded below.

| Final evidence artifact | SHA-256 |
|---|---|
| Control final health result | `a42d87abe1a58a9ad5c43a31e53cd97124c77073de2c4751c2b1698da2be99ec` |
| Compute final health result | `accfc2543ca8c43eff1612085a252315fbb6c4b1d008fb0c8106ab931189370d` |
| Exact temporary policy cleanup result | `bc7202694e4a21bf8dd1df1de1ad14f4b4377218192a933d1f3a1d9f0add7992` |
| Restored ingress readback | `115a6438a49265c42a2cd73eb1d6a7aff8383c41b940a3012dc747918cfde7b9` |
| Canonical owner release result | `89d20a84dcf18cd6a4b4340a1311395de758463806996f82707dedb601d56caa` |
| Production HTTP/card result | `24180e92214468a27a28d40c30ddb3d865d96b404083a308117f89f7b7609d9b` |

## Actual X footer-clearance verification

The first actual X preview of the canonical share link still displayed the
previous image. This is retained as **one failed preview observation**, separate
from the successful versioned-link trial. It does not establish why X retained
the old image or that its canonical-link cache was subsequently cleared.

The versioned share link, with `?v=footer-clearance-41b3d1c`, served the same
public PNG with SHA-256 `0434a0bde9ba55edec40e374125ed25f5bc59fca21d568308f952a174391d38f`.
After the validator loaded that link and the composer was cleared and the link
reinserted, the actual signed-in X draft displayed the corrected card at
**07:14:57.610 UTC (16:14:57.610 JST)**. The complete orange marker and
`Verified with Lean` were visible above X's black title overlay. This is **one
successful bounded visual trial**, not a guarantee about every X client or
cached URL. No post was sent.

| Private X evidence artifact | SHA-256 |
|---|---|
| Canonical-link stale-preview screenshot | `34283b637b339891dfe55cf97d613858722535622a649cb005dce38c8dde9e5f` |
| Actual footer-clearance screenshot | `dd72d65d6b4a483f72b2af83c33bf4d62bb4e973f112f639ce5aa08aa506fb67` |
| Matching accessibility snapshot | `715f2ce60d30b77d6d8b7f076d50486bcc9b8497869250fe163e644712735dcc` |
| Actual X visual-verification receipt | `ec2b4fbf09d8de1d80c1aaa51c80c0cc97fea10ff1b788e9eb08ea18c320c2aa` |

## Measurement batches

The quality ledger records these bounded observations separately. The
denominators count fixtures, dispatches, complete operations or hosts as stated;
the 35-step checks and five admission steps are not independent trials. These
are release/layout measurements, not a model benchmark.

| Measured batch | Passed / checked |
|---|---:|
| Initial padding-only layout fixtures | 1 / 3 |
| Final footer-clearance layout fixtures | 4 / 4 |
| Strict native source/image guard | 1 / 1 |
| Initial native preview dispatches, before a test container | 0 / 2 |
| Corrected native preview and pixel match | 1 / 1 |
| Owning read-only preflight | 1 / 1 |
| First control quiesce attempt | 0 / 1 |
| Explicit unchanged quiesce retry after reconciliation | 1 / 1 |
| Owning DB admission transaction | 1 / 1 |
| Final host health and recovery | 2 / 2 |
| Exact temporary verification policy cleanup | 1 / 1 |
| Actual production HTTP/card rendering | 1 / 1 |
| Canonical-link X preview with the previous image retained | 0 / 1 |
| Versioned-link actual X footer clearance | 1 / 1 |

The two X rows use `environment=other`; they are external UI observations. The
successful versioned-link row does not supersede the canonical-link observation.

No actual reboot or new model/Lean generation is claimed. No X post was sent.
Screenshots, share tokens, browser accessibility text, conversation/Lean bodies,
account details and internal runtime identifiers remain outside Git.
