# Production Lean restoration — 2026-10-12

The user reported a failure at `https://palschat.site/try` for “x² が連続であることを示してください。” This record tracks the production repair. It does not certify restoration until a public proof request reaches real Lean verification and its reviewed result is displayed.

## Confirmed cause

[Live inspection 38233474449](https://github.com/AtsushiHosaka/pals/actions/runs/38233474449) confirmed release sequence 22 and a healthy production API, but `proof_capability=natural-only`, `lean_schema_present=true`, and `lean_flow_enabled=false`. The host manages only API, Web and worker. The fixed verifier and reconciler services are absent. The failure occurs before compilation: the displayed text maps to `lean_flow_unavailable` or `lean_verification_required`.

The API also lacks five full-runtime settings: the fixed reconciler URL, Recipe selector database URL, independent Recipe reviewer principal/secret, and Recipe worker secret. No credentials or private values are recorded here.

[Prerequisite inspection 38236953620](https://github.com/AtsushiHosaka/pals/actions/runs/38236953620) confirmed all six existing protected database-role files are available. The existing signed ARM64 verifier image contains the matching Lean toolchain and Mathlib manifest, and the compiler version matches its pinned toolchain. Its offline metadata task was removed. Production remains natural-only at this checkpoint.

## Repair contract

The working baseline is the user's request and `specs/proof-request-reuse/natural-only-production.md`, superseded for ordinary Send on October 5, plus PFR-010–013 and `docs/worker-lane-isolation-2026-10-05.md`.

Reuse one verifier with the existing signed immutable image. Run separate assessment and proof workers against distinct queues, using one signed worker image containing both credential launchers. Keep existing provider accounting, independent review, exact source display, signatures, database admission, private networking, writer drain, locks and existing features.

The guarded transition has two stages:

1. Install reviewed controller/authority/contract support and stage the shared full worker package through the ordinary signed source update. The current natural-only environment and three serving services remain the predecessor during this stage.
2. Validate queue authority, complete private settings and actual topology; provision the missing assessment worker, verifier and reconciler; switch API/proof capability; bind the six-service recovery context to the same independently verified admission. Fail closed before switching if any prerequisite is missing.

Every subsequent signed update must rotate verifier/reconciler TLS to its new release ID, preserve the immutable verifier image, drain all writers and check all four runtime readiness markers. Current-release recovery must verify the signed carrier and database identity before recording health.

## TLS evidence and boundary

A real offline local check found that Mac bind mounts returned server-key UID 0 after `chown(65532)`. The repair uses separate native Linux server/client volumes. The verifier receives only server keys; the reconciler receives only client keys. A capped offline generator uses the admitted API image, no network or credentials, and only the capabilities required for ownership/mode changes. Fresh task processes and staging volumes have owner labels and bounded cleanup.

Real local checks verified UID 65532 server-key access, refusal of client-key access, directory mode 500/file mode 400, distinct keys, certificate signatures, deployment binding and sealed reuse. Both processes and all three test volumes were removed. Synthetic public binding values were used, so these checks do not establish production admission or public proof success.

## Outstanding evidence

Initial host preparation and the six-service switch must be read back through the guarded operator. Then verify a meaningful proof over explicit assumptions through the public application, with the linked job, actual compiler attestation, independent semantic/output reviews and the exact accepted Lean source. The original guest session's daily allowance must be respected; no quota reset or alternate identity is authorized by this repair.

## Initial transition diagnostics

[Read-only initial plan 38241022191](https://github.com/AtsushiHosaka/pals/actions/runs/38241022191) verified the signed sequence-22 predecessor and produced a guarded code-staging plan. It also reported an unverified assessment-queue observation and an API peer-address mismatch against the fixed production reconciler contract.

[Code-stage attempt 38241410834](https://github.com/AtsushiHosaka/pals/actions/runs/38241410834) refused `stage_plan_changed_since_review` before installing files. The precise hash guard remains required. Separate component hashes and closed queue/network diagnostics were added to identify the differing input; this refusal is not restoration evidence.
