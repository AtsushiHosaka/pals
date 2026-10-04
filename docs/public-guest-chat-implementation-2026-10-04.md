# Public landing page and daily guest trial

Working implementation baseline: the user's request on 2026-10-04 for a public LP and a
ChatGPT-inspired, logged-out chat, followed by the explicit limit of three messages per day, including clarification replies.
This record does not replace or amend canonical product specifications.

## Implemented behavior

| Requirement | Implementation |
|---|---|
| Public introduction | `/` displays the LP until authentication is established; `/about` always remains public. Authenticated `/` retains the existing workspace. |
| Guest entry | `/try` supports a real mathematics question without Cognito. The LP Send action carries its draft and language into this flow. |
| Three daily messages | Server-side PostgreSQL admission allows three accepted messages per session and network per JST calendar day, including initial questions and clarification replies, with a configurable global cap. Shared networks share the limit. Failures after acceptance still count. Exact retries do not count again. |
| Clarification | A finite missing-premise continuation belongs to the same question and spends one daily message. After three accepted messages, further clarification is blocked until the daily reset. |
| Real processing | Guest requests use the existing durable outbox, SQS worker, model calls, usage records and independent answer review. They do not create account billing operations or account free-quota holds. |
| Recovery | Stable submission keys, bounded HTTP calls, read-only restoration, finite polling, and safe rich-text fallbacks. Account history is not automatically merged. |
| Public copy | English, Japanese, Simplified Chinese and Traditional Chinese. Paid plans are marked as preparation; sandbox prices are not published. |

References inspected in the shared browser: [ChatGPT overview](https://chatgpt.com/overview/)
and its logged-out chat. The implementation uses PALS branding and content, a spacious
composer, account entry actions, a desktop sidebar and a mobile menu.

## Original rollout verification (one daily initial request)

- Frontend: typecheck, full ESLint, production Docker build, and **1,236 unit tests** passed.
- Backend guest boundaries/environment: **14 tests** passed; guest PostgreSQL integration:
  **11 tests** passed against uniquely named disposable databases on the existing PostgreSQL.
  Existing authentication/chat and normal-request regression checks also passed.
- Read-only architecture review cleared the introduced source findings. The additive guest
  migration validates its actual ordinary-request and projectless-chat dependencies, without
  importing or modifying the unrelated formal-proof release gate.
- Actual local browser flow: LP Send → `/try` → real answer to an odd-number addition question.
  Request `d9738008-b967-43a5-bb0a-3f2420da8d29` reached `answered`, with five recorded model calls,
  independent QA approval and an exact match between reviewed and returned answer digests.
- Browser reload restored that answer; the daily allowance was exhausted and the composer
  disabled. An actual API probe with a new cookie still returned zero remaining, rejected a
  second initial request with 429, and kept private Projects inaccessible with 401. Guest
  responses carried private no-store and no-referrer headers.
  Desktop CSS width 1280 and narrow CSS width 480 had no horizontal overflow.
  Mobile menu, Escape and focus restoration were checked. The in-app browser's viewport
  override minimum prevented claiming a 390px real-browser check.

## Operating configuration

The owning API contract, release command, grants and production ingress requirements are in
[`pals-api/docs/api/guest-chat.md`](../pals-api/docs/api/guest-chat.md).
Guest service enablement defaults to false. Production requires an admitted Cloudflare client-IP
header boundary with exact immediate proxy addresses, and disabled Uvicorn proxy rewriting.
That public topology has not been exercised by this local verification.

`PALS_PUBLIC_SUPPORT_EMAIL` is an optional web server runtime environment variable. Only a
validated supplied address produces contact links; public routes are dynamic so this does not
require putting contact configuration into a client bundle. No public contact was supplied.

Existing `pals-local` API and Web services were updated with versioned images after the user
authorized the update; the stopped existing worker was started. PostgreSQL, LocalStack,
Cognito and other containers were reused. No existing data or user changes were reset,
staged or committed. The guest schema was installed through its release command.

The stable local hash key and a minimal Compose override are in the git-ignored
`.local/e2e/guest-chat/` directory with private permissions. Do not commit its files or print
the key. The current task's temporary runtime override preserved the prior API environment;
the durable minimal override adds only this feature's settings and image versions.

To retain this local feature when updating the same services, append
`-f .local/e2e/guest-chat/compose.json` to the existing Compose configuration. If rebuilding,
assign fresh image tags and update the ignored override to those tags. Keep the existing hash
key: the database binds its fingerprint, so replacing it needs an explicit migration.

Session expiry removes access after 48 hours; it is not a promise of physical data deletion.
This task did not publish the site, submit Stripe onboarding, set live subscription prices,
or author terms, privacy policies or commercial disclosures.
