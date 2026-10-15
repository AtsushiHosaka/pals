# Production feature recovery — 2026-10-15

Guest chat is restored in production. The signed deployment and the representative feature walkthrough below completed successfully.

## Reproduced outage

The public `/try` page cannot initialize its session and disables the composer.
An actual POST to `https://api.palschat.site/v1/guest/session` with the public web Origin returns HTTP503 and `guest_network_unavailable`.
The running API trusts only `172.25.0.5`, while the actual existing public edge is `172.25.0.6` on their shared application network. The assessment worker occupies the old address. Uvicorn proxy rewriting remains disabled. The ordinary health endpoint and running containers do not detect this functional failure.

## Deployed correction

The normal signed update authority snapshots the existing named edge before draining, binds its exact identity and shared network, replaces the stale API peer with only that edge's IPv4 address, and verifies the same identity/address after restart. Public guest session creation must succeed before the release can be declared healthy. Authentication, cookie/Origin validation, admission, signatures, lifecycle locks and ownership checks remain in place.

Five regression tests cover the stale-worker-IP bug, wrong identity/network, invalid address, proxy rewriting and restart/address substitution. The stale-IP regression fails against untouched source and passes after the correction. The combined authority/full-runtime/guest tests pass all108 checks.

The complete host suite passes: 680 tests run, 679 successful and one existing dedicated PostgreSQL fixture skipped. The user explicitly approved the exact authority hash registration and immediate production rollout after the original automatic-review rejection.

Frontend source at `ee35e1f92012c5a02b7bcf6e804da5d500194729` passes all1691 tests across138 files using a lock-identical dependency cache.

## Fresh production walkthrough

The existing user-approved Pro test account was recovered from the prior chat and successfully logged in. Credentials are omitted from this record.

| Flow | Current result |
| --- | --- |
| Guest chat | Reproduced503 before repair; after deployment, actual UI submission returned a Lean-verified Japanese answer and matching Lean source |
| Fresh login | Successful |
| New project | Created private project `e8a800af-6fd2-427f-953d-f58af9539797`; name/description retained when navigating back |
| Project chat and proof | New chat `b6292f4f-83c1-4e5d-963d-94a550bb60a9`; prime-divides-product theorem submitted and answered |
| Actual Lean evidence | Job `7414f8c4-996b-46a6-a6b4-fe232783c988`: verified compiler result, independent semantic approval, completed explanation and matching answer/job/source references |
| Source hash | `9ee4e5ca246e568a354cbd54509f1ce0d8d8a3945b3f72ab34b943fe88e9592a` |
| PDF upload/OCR | Two-page image-only QA PDF uploaded to the new project; ready with2 pages; page2 preview renders |
| General and mathematics settings | Loaded successfully; all mathematics convention controls present |
| Usage/plans | Permanent complimentary Pro and consistent used/reserved/available counters loaded |
| Private/public Lean source | Displayed code matches the actual compiled source hash |
| Sharing | Preview, create, copy, separate-page view, source expansion and revocation succeeded; reloaded revoked link is unavailable |
| Search | Finds the new prime-divisibility chat with its correct project |
| Mathematical keyboard | Opens and inserts ≤ into the composer; test draft cleared without submission |
| Logout/relogin | Returns to sign-in; fresh successful login returns to the same project chat and retained proof |

Stripe remains excluded under the user's prior instruction. No payment, password change or user-data deletion has been performed. Generated documents, screenshots, private diagnostics and credentials stay outside Git.

## Production rollout and post-deploy checks

The user explicitly authorized immediate production deployment. [Infra PR71](https://github.com/AtsushiHosaka/pals-infra/pull/71) and [parent PR109](https://github.com/AtsushiHosaka/pals/pull/109) are merged. Parent release `0d575bd300e591be541d50296c21de196bc21f3e` pins infra `7cb51d886e76470dd99006871c1cdce3b8d282a5`.

The authority digest `5130f05ed837709078903d9722c11c30af31672cc2e6d531a94ed19afd6b0285` was installed under existing lifecycle/admission locks, with predecessor signature validation and unchanged admission/service identity checks. The [signed deployment run](https://github.com/AtsushiHosaka/pals/actions/runs/38740474085) succeeded. Its forward-health evidence reports signin200, health200, anonymous401, guest_session200 and preserved previous table data.

A fresh browser guest submission asked for coprime divisibility over natural numbers, including zero: gcd(a,b)=1 and a divides b*c imply a divides c. Request `7139948e-fd9d-4890-92f5-5521ff796d99` completed with `lean_verified`; job `e6691287-77dc-445a-9dac-6dca7ada89fc` is verified with approved semantic review and completed explanation. Compiler attestation, answer and actual UI-displayed Lean code agree on SHA256 `657f4200c8012d2bd35d0aca689bd31b1bc9f5d374ac8ea0b823661a2b88b7a6`. The Japanese answer and source both render successfully.

After deployment, fresh logout/login returned to the existing private proof with its content intact. Project `900f48b4-6d56-49bd-9d59-98df6a5f3621` (本番復旧後QA 2026-10-15) was newly created with its description retained.

These checks cover the observed public outage and the listed application flows; they are not a claim that every possible input or third-party outage has been exhaustively tested. Previously excluded Stripe and credential-changing flows were not executed.
