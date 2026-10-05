# Public guest chat tasks

WORKING checklist. Evidence: [initial rollout](../../docs/public-guest-chat-implementation-2026-10-04.md), [three daily messages](../../docs/guest-daily-message-limit-2026-10-04.md).

- [x] GUEST-001/006: Public LP at unauthenticated `/` and `/about`, four-language copy, LP draft hand-off to `/try`.
- [x] GUEST-002/004/007: Guest session, durable admission, ordinary worker/independent review reuse, account separation, disabled-by-default configuration and release migration.
- [x] GUEST-003: Three daily messages per session and network including clarification replies, global cap, JST reset, replay without consumption; real PostgreSQL concurrency/upgrade tests.
- [x] GUEST-005: Origin, cookie, cache/index/referrer and trusted client-IP boundaries.
- [x] GUEST-002: A successful real-provider guest answer after the three-message change (the 2026-10-04 run ended `proof_reuse_provider_unavailable`; the earlier one-message rollout answered successfully). 2026-10-05: answered through the Lean-required flow with the real provider. Evidence: `docs/lean-required-flow-evidence-2026-10-05.md`.
- [x] GUEST-002 (2026-10-05): Lean-required guest flow — guest reads expose linked-job stage, verified Lean source and reviewed explanation; no answer on Lean failure; real local guest journey. Local guest request `4b85b435…` answered `lean_verified` with its Lean source; allowance 3 → 2. Evidence: `docs/lean-required-flow-evidence-2026-10-05.md`.
- [ ] GUEST-005/007: Production ingress with the admitted Cloudflare client-IP header and exact proxy addresses.
