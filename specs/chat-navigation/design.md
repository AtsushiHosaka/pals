# Chat navigation design

## Search

`GET /v1/chat-search?q=&limit=&cursor=` (q ≤ 200 characters, limit 1–50, default 30; no other query or body). The query is NFKC-normalized and lower-cased. One owner-fenced PostgreSQL statement matches the Project name, chat ID or any proof statement in the chat and orders by `(created_at, id)` descending with keyset pagination. The opaque cursor binds the query digest, so a cursor cannot be reused for another query. Each entry returns the chat, its Project name and the latest statement truncated to 160 characters. `ChatSearchDialog` aborts superseded requests and appends further pages.

## Completion indicators

`GET /v1/chat-completions` returns exactly `{items: [{chat_id, completion_id, completed_at}]}` for the owner's latest successful result per chat across both conversation models; completion IDs are namespaced and contain no text. It requires Cognito, rejects extra query/body data and sends `no-store`, including for pre-route credential rejection.

`useChatCompletions` polls every 30 seconds while visible and on focus/visibility/navigation. `chatCompletionReadState` stores per-account acknowledgments in `localStorage` (memory fallback), merges other tabs monotonically and fences account/session changes. `useViewedChatCompletion` acknowledges displayed results. `ChatCompletionDot`, `ChatSidebar` and `SidebarProjectGroup` render the 8 px dot; unread project chats stay visible beyond the collapsed five rows.
