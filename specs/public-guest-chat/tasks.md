# Public guest chat tasks

WORKING checklist. Evidence: [initial rollout](../../docs/public-guest-chat-implementation-2026-10-04.md), [three daily messages](../../docs/guest-daily-message-limit-2026-10-04.md).

- [x] GUEST-001/006: Public LP at unauthenticated `/` and `/about`, four-language copy, LP draft hand-off to `/try`.
- [x] GUEST-002/004/007: Guest session, durable admission, ordinary worker/independent review reuse, account separation, disabled-by-default configuration and release migration.
- [x] GUEST-003: Three daily messages per session and network including clarification replies, global cap, JST reset, replay without consumption; real PostgreSQL concurrency/upgrade tests.
- [x] GUEST-005: Origin, cookie, cache/index/referrer and trusted client-IP boundaries.
- [ ] GUEST-002: A successful real-provider guest answer after the three-message change (the 2026-10-04 run ended `proof_reuse_provider_unavailable`; the earlier one-message rollout answered successfully).
- [ ] GUEST-005/007: Production ingress with the admitted Cloudflare client-IP header and exact proxy addresses.
