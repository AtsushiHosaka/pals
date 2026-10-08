# Pro token quote edge repair — 2026-10-08

At 23:29:20 JST, the existing Mini public Caddy received only exact POST/OPTIONS `/v1/billing/token-quotes`, using its unchanged private API upstream. The missing public route previously returned OPTIONS 404 while the loopback API returned 200. Token-based Pro obtains this quote before creating, answering or retrying a question, explaining the generic submission error and an empty chat created earlier by the overview.

Infra ae450d62999b516ddc09531de1b31ba5baa865cb contains the route fragment, repeatable real-Caddy HTTP tests and operational procedure. The existing pinned Caddy binary was used in an isolated, bounded, credential-free test container; four tests covered bearer/Origin propagation, anonymous upstream 401, CORS rejection, unsupported methods, exact path/Host and private-path denial. The complete production candidate also passed adapt/validate with the running edge's Caddy.

Apply held the canonical deployment and lifecycle locks, preserved an exact backup, checked current bytes before atomic replacement and restarted only the same edge CID/image. The first attempt encountered the existing monitoring lock before changes; the bounded retry waited without stopping monitoring or replacing lock inodes.

Public checks after apply: allowed-Origin OPTIONS 200, foreign-Origin OPTIONS 400 without allow-origin, anonymous POST 401 auth_required. Quote GET and malformed/private/financial/docs/OAuth/MCP routes remain 404. Existing API health is 200 and auth/billing/projects are anonymous 401. API/Web/worker/DB CIDs, images and restart counts are unchanged; signed admission, policy and current.json remain unchanged at release 17. No quote, question, provider call, usage reset, credential or database migration was created by these probes. AUTO_DEPLOY remains false.

These route and local HTTP results do not establish a real authenticated Pro question submission. The existing QA browser owns that verification; its result must be recorded separately. Missing attachment/model UI is outside this repair. Sanitized host evidence is task-local in evidence/token-quotes-edge-applied.json.
