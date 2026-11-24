# Admitted recovery startup fence (2026-11-18)

- Target: fail-closed recovery/release exclusion. No model quality, generation
  latency or cost improvement was measured.
- Hypothesis: durable per-host fences under the existing launch locks can provide
  explicit facts for a controller that observes both ACKs before claiming.
- Change: infra #194, source `25732a7`, production base `76335a4`. New filesystem
  primitive, tests and one required CI step; no existing execution consumer changed.
- Result: 31 real-filesystem/flock cases and 146 existing controller regressions
  passed locally. Source review resolved the owner-token hash representation and
  documented the trusted borrowed-lock precondition. Linux exact CI remains pending.
- Decision: pass the primitive to the main #433 integration, preserving partial
  records and existing normal gates. Do not promote a local ACK into full authority.
- Cost: zero paid model calls, live actions or AWS changes.
- Limits: no real power loss, foreign-UID-file or production-host test; no consumer
  integration, fresh DB/remote authority or actual recovery verified here.
- Next: finish #433 integration/CI/review and its concrete live approval, then the
  normal release and actual figure display, persistence and reload acceptance.
- Evidence: [source report](../../admitted-recovery-fence-2026-11-18.md),
  [infra #194](https://github.com/AtsushiHosaka/pals-infra/pull/194),
  [#433](https://github.com/AtsushiHosaka/pals/issues/433).
