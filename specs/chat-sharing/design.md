# Chat sharing design

## Boundaries and data

FastAPI owns authorization, snapshot projection, content digests, and publication. PostgreSQL stores the immutable JSON snapshot and a cryptographically random capability token, associated privately with its owner/chat. A partial uniqueness constraint or equivalent transactional serialization enforces one active link per chat. Revoked tokens never become active again. Serving performs no schema DDL; an explicit idempotent release migration installs the schema and grants.

The snapshot is an allowlisted projection of saved learner-visible proof requests and legacy proof/explanation/clarification records, ordered as a conversation. It contains `title`, `output_language`, `captured_at`, and `messages`. Each message contains `role`, `kind`, `content`, `status`, and nullable `lean_source`. States distinguish `pending`, `failed`, `answered`, `verified`, and `unverified`; null is permitted when no proof state applies. Internal IDs and operational failure details are excluded. Output already withheld by existing learner-output rules must remain withheld. Pending work is represented as the captured state, without polling or generation.

Clarification questions retain the selected excerpt as a quotation before the question text, including multiline excerpts, so references such as “why this?” keep their meaning. This does not expose internal section or clarification IDs.

Preview computes a digest of the material snapshot fields (excluding the volatile capture timestamp). Publish recomputes the projection in a consistent transaction and requires that digest to match. This binds publication to the reviewed content. A changed conversation returns 409 and creates no link. Timestamp metadata is assigned on publication. A 1 MiB canonical-material limit rejects excessive data rather than truncating it.

## API

| Method/path | Contract |
|---|---|
| `GET /v1/chats/{id}/share-preview` | Owner only. `{snapshot, snapshot_digest}`. |
| `GET /v1/chats/{id}/share` | Owner only. `{share: {token, created_at, snapshot} \| null}`. |
| `POST /v1/chats/{id}/share` | Owner only. `{snapshot_digest}` → `{token, created_at, snapshot}`. Reject stale preview or existing active link with 409. |
| `DELETE /v1/chats/{id}/share` | Owner only. Idempotent revocation; 204. |
| `GET /v1/shared-chats/{token}` | Anonymous. Snapshot only; missing/revoked token → identical 404. |

Authorization happens before owner-specific reads. Other owners cannot distinguish missing chats from inaccessible chats. Tokens use at least 256 bits of cryptographic randomness. Responses use `Cache-Control: no-store`, `X-Robots-Tag: noindex, nofollow`, and referrer protection. Persistence errors produce explicit non-success responses, without exposing database details.

## Frontend

The existing project and projectless chat headers open one reusable sharing dialog. If an active share exists, show its frozen content, public URL, copy, and revoke actions. Otherwise show a current preview and an explicit create-link action. Do not publish merely by opening the dialog. A 409 prompts refresh; a completed revoke returns to the unpublished state. Async responses must not cross account/chat changes or a closed/reopened dialog. Focus is trapped in the modal and restored on close.

`/share/[token]` is an anonymous read-only route, using an unauthenticated API fetch with no cookies or authorization attached. Its renderer is shared with the preview to keep math, content order, source, and state labels consistent. It has no owner-only data hooks. Disable indexing/caching and cross-origin referrers, and retain existing sanitization for learner content. Four-language UI copy follows the existing locale provider.

## Verification and operations

Use the existing PALS local services and test database fixture; do not create duplicate stacks. Real PostgreSQL integration proves durable publication and isolation. Real Cognito/API/browser testing proves anonymous route behavior, publication, reload, and revocation. Unit checks cover projection/parser and UI failure states but do not replace real integration. Production deployment is outside this local implementation request; document the release command and verify its restricted-runtime grants.

## Image and chat deletion delta

CHAT-005/011 adds ordered image manifests to the same preview digest and frozen publication. Binary payloads are stored separately from bounded snapshot JSON. Owner preview uses authorized private reads; public image reads require an active share and its exact manifest. Chat deletion atomically revokes the share and fences all source/image reads before payload cleanup. Revoked or deleted content cannot be reactivated. Normal-store image erasure and expired guest cleanup have a 24-hour ceiling; backup retention is at most 30 days. Restore must reapply deletion markers before serving data.
