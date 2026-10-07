# Chat sharing

Status: WORKING — implementation baseline authorized by the user's 2026-09-30 request to implement the proposed sharing feature through the SDD loop.

## Scope

Share a frozen copy of one owned chat through an unguessable public link. Both Project and projectless chats, including existing proof conversations, are in scope. Editing, collaboration, importing a shared chat, automatic publication of later messages, and search discovery are out of scope.

The 2026-10-07 image-sharing delta is defined by [chat-experience](../chat-experience/requirements.md), CHAT-005: owner preview and frozen publication include chat attachment images. CHAT-011 fixes deletion: deleting the source chat immediately revokes its public link and image access, then erases normal-store image payloads within 24 hours and backups within 30 days. Implementation of this delta is tracked separately; Project materials are not published.

| ID | Observable requirement |
|---|---|
| SHARE-001 | The owner can open Share from an existing chat and review the complete content that will be published before creating a link. An empty chat cannot be published. A chat that changes after preview requires a refreshed preview before publication. |
| SHARE-002 | Creating a link saves an immutable snapshot of the previewed conversation. Later messages, proof progress, answers, or account preference changes cannot change that snapshot. Each chat has at most one active link; reopening Share shows that link and its saved content. |
| SHARE-003 | Anyone with the link can read the snapshot without signing in. The page shows the saved questions, answers, clarification turns including their selected quotations, mathematical notation, available learner-visible Lean source, and truthful verification states. It offers no chat mutation or generation controls. |
| SHARE-004 | Only the chat owner can preview, inspect its active link, create a link, or revoke it. The public response contains only the explicitly selected learner-visible snapshot fields: no account identity, project metadata, credentials, worker/reviewer internals, or other chats. |
| SHARE-005 | The owner can copy and revoke the active link. Revocation immediately prevents subsequent public retrieval. Missing and revoked links have the same unavailable response. Deleting the source chat also revokes its link and image access atomically. A later publication creates a fresh unguessable link and cannot reactivate the old link. |
| SHARE-006 | The dialog explains that anyone with the link can read the content and that later conversation changes are excluded. It reports loading, publication conflicts, copy errors, unavailable links, and service failures without false success. Dialog operations are bound to the selected chat and signed-in account. Keyboard operation, narrow screens, and the four existing UI languages are supported. |
| SHARE-007 | Publication and revocation are durable and atomic. Oversized snapshots fail explicitly without silently omitting conversation content. Public responses and pages do not permit caching or indexing; shared-link navigation does not send the token as a referrer to third parties. Existing authenticated chat access remains unchanged. |

## Acceptance evidence

- PostgreSQL-backed checks: ownership, exact snapshot allowlist, both conversation models, preview race, immutable content, one active link under contention, revoke/recreate, and persistence failures.
- UI checks: both entry points, preview before publish, copy/revoke, anonymous rendering, truthful verification labels, session/chat isolation, and error handling.
- Real local API + browser journey with existing Cognito/PostgreSQL: owner publishes, anonymous reader sees saved content, owner revokes, reader cannot retrieve it again. No substituted sharing/auth/persistence boundary.
