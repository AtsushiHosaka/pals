# Public guest chat design

API contract, release command and configuration are owned by
[`pals-api/docs/api/guest-chat.md`](../../pals-api/docs/api/guest-chat.md); this file records only the cross-repo boundaries.

## API and persistence

- `POST/GET /v1/guest/session`, `POST /v1/guest/proof-requests`, `GET /v1/guest/proof-requests/{id}`, `POST /v1/guest/proof-requests/{id}/answers`. Statement 1–2000 characters; output language `en|ja|zh-Hans|zh-Hant`; idempotency key `[A-Za-z0-9_-]{32,128}`. Queries, duplicate credential headers, duplicate JSON members and bodies over 32 KiB are rejected.
- The `pals_guest` cookie is an opaque 256-bit token (HttpOnly, SameSite=Lax, path `/v1/guest`, Secure in prod, 48 h). Only its SHA-256 digest is stored. Mutations require an exact allowed `Origin`.
- `pals_guest_chat` schema stores sessions, chat bindings, initial and continuation admissions and daily budgets. One globally serialized PostgreSQL transaction checks the session, network and global budgets, inserts the admission and enqueues the ordinary proof-request outbox. Network identity is an HMAC of the IPv4 /32 or IPv6 /64; production uses `cf-connecting-ip` only from exact trusted proxy addresses. Session creation is also rate-limited per network and globally.
- Guest requests reuse the ordinary proof-request worker, usage records and independent answer review; they create no account billing reservation or token operation. A guest read of an answered request re-verifies the saved review evidence against the exact answer hash.
- Serving validates the schema and grants read-only; `python -m app.release.guest_chat_migration --apply` installs or upgrades it. Disabled by default (`PALS_GUEST_CHAT_ENABLED`).

## Frontend

- `HomeEntry` renders `PublicLanding` for unauthenticated `/`; `/about` always renders `PublicLanding`. The LP stores the draft and locale in session storage and navigates to `/try`.
- `GuestChat` restores the session and current request read-only, polls only active work with bounded requests, keeps stable submission keys after ambiguous sends, and disables both question and clarification sending at zero remaining.
- Public and guest copy live in `lib/publicMessages.ts` and `lib/guestMessages.ts` for all four locales. `/share/*` and guest API responses send `no-store`, `noindex` and `no-referrer`.
