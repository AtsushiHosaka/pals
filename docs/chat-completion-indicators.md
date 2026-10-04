# Chat completion indicators

WORKING contract for the 2026-09-30 request: add a small blue dot to a chat with a newly
completed result that has not been opened. The dot is a notification, not a Lean
verification badge. Modern answered requests and legacy verified jobs qualify;
pending, failed, canceled, and premise-question states do not.

- Show the dot beside the title on desktop/mobile, in projects and projectless chats.
  Unread project chats remain visible beyond the usual collapsed five rows.
- Opening a visible chat marks its latest known completion read. Results already shown
  on screen are acknowledged immediately, even when navigation precedes the next poll.
- Establish the first successful feed as a baseline so historical results do not all
  become unread. Later completions, including repeated completions in the same chat,
  receive a dot. A transient API failure never clears existing dots.
- Store read state per account in this browser, including reloads and sign-in sessions.
  Other tabs merge acknowledgments monotonically; account/session changes fence pending
  responses. Cross-device read synchronization is not part of this implementation.
  When localStorage is disabled/full, read state remains available in the current tab.
- Poll one owner-scoped metadata endpoint every 30 seconds while visible, and refresh
  on focus/visibility/navigation. Background tabs neither poll nor acknowledge results.

## Implementation

`GET /v1/chat-completions` returns an exact `items` envelope of
`{chat_id, completion_id, completed_at}`. One PostgreSQL statement finds each owned
chat's latest successful result across both conversation models. Completion identity
is namespaced; timestamps and IDs determine ordering. No conversation text is returned.
The route requires the normal Cognito owner identity, rejects extra query/body data,
and sends `no-store` even for pre-route query-credential rejection. No migration is needed.

Frontend ownership: `useChatCompletions` reads the feed; `chatCompletionReadState`
persists and merges read acknowledgments; `useViewedChatCompletion` records displayed
results; `ChatCompletionDot`, `ChatSidebar`, and `SidebarProjectGroup` render the dot.
The accessible label is localized in four languages as “New result available”.

Baseline API HEAD `858dd167f5f2409900b8d33b88a667d8b0b3127e` and frontend HEAD
`7837f8f15be095d0c911a3d36241d110683475d2`, plus preserved existing uncommitted work.
No staging, commits, production deployment, billing/schema changes, or extra app stacks.

## Verification

- Frontend complete unit/story suite: 100 files / 1,078 tests passed. The final clarified
  two-answer immediate-navigation regression also passed (9 hook/state tests).
- TypeScript and scoped ESLint passed. Production Docker/Next build is checked separately.
- Backend: 6 real PostgreSQL/HTTP cases; existing regression 57 cases. After the outer
  header fix, middleware/wiring 39 cases and the 6 PostgreSQL cases passed again.
  Ruff, targeted mypy and OpenAPI consistency passed. Disposable test DBs were removed.
- Independent review found and verified fixes for concurrent-tab acknowledgments,
  completion ordering after retry, and outer authentication-error cache headers.
  Final review: no remaining material findings.
- Isolated frontend tests mock only the API boundary. Backend completion tests use real
  PostgreSQL; their external Cognito verifier boundary is covered separately by the
  read-only local smoke `tests/e2e/check_chat_completions.py`.

## Local runtime — 2026-09-30 JST

- Updated the existing API and web services after the concurrent billing QA released
  the stack. Both became healthy; no worker, schema, plan or payment was changed.
- `pals-api/.venv/bin/python tests/e2e/check_chat_completions.py`: PASS using real
  local Cognito, deployed API and saved PostgreSQL data (40 completed chats before
  the new browser fixture). Anonymous/query-credential rejection, owner feed,
  exact metadata shape, uniqueness and no-store all passed.
- Browser used the existing Chrome tab. Initial history had zero dots. Created one
  normal projectless proof through the real UI and immediately navigated to another
  chat. The real worker answered request `e0a3f25e-fd9c-4014-aaf3-e6fd2e77d7a2`
  in chat `be246868-28aa-4034-bf76-35ad209b89f5`; PostgreSQL state was `answered`
  without error. No seeded completion, intercepted response, or quota override was used.
- The blue marker appeared after polling. Measured 8×8 CSS pixels, RGB(59,130,246),
  visually inspected beside the truncated title on desktop and mobile. Reload retained
  the unread dot. Opening that chat removed it; navigating away and reloading kept it
  read. The generated answer remains as a normal local QA chat.
- Restored the temporary viewport override and left the existing user tab open on its
  prior conversation. No additional browser tabs or app stacks were created.
- Final API image manifest: `sha256:dce8b4733236a4d46d1495218386fc584d5fe357d7f18f32109059156d76c095`.
- Final web image manifest: `sha256:dc47918609c37bb76f535582511ef8b5338a53fb73e14eda6ffaeddb95cb55d6`.
- Final TypeScript, scoped lint and root/API/web whitespace checks passed.
- Outcome: requested local implementation and real generation→unread→read journey PASS.
  Production deployment and cross-device read synchronization were not performed.

Final core source SHA-256:


- `pals-api/app/infrastructure/repositories/chat_completions.py`: `810462333079f71cd4481077ffeebd57740ea63b1f96f15f06ea3b9f40921181`.
- `pals-webfront/hooks/useChatCompletions.ts`: `eaaed897e91ab1c6bef37465ca881e1c7e84e34fc67bd49ebd9b67783535a0fc`.
- `pals-webfront/hooks/useViewedChatCompletion.ts`: `e2e43972854a73e1a7a7eb72bd6d2c64f1fcfd568003eb686d8a8f9d6322dda3`.
- `pals-webfront/lib/chatCompletionReadState.ts`: `b8811473c58c4d7e12634df661626b35f9d6b5fafaf26cacedbfe1afff26d89c`.
