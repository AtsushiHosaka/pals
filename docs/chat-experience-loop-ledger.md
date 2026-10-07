# Chat experience SDD loop — 2026-10-07

Objective: image attachment, mathematical rendering and composer/conversation redesign. Authority: this chat's explicit request and answers. Initial parent `7c45dbb`; API `aa8b12c`; webfront `d436271`; agent `7a6c343`. All working trees were clean before this work. Reuse existing runtimes; no new application or container stack. Default two iterations, commands monitored below 60 seconds, six-hour parent ceiling; root owns cancellation.

| Iteration | Finding / decision | Route | Evidence / next action |
|---|---|---|---|
| 1 | Inline images already requested; canonical MAT-011 lacks detail. User explicitly includes guests, previewed public images and full composer/conversation redesign. Images need not contain problems. | grill → update-spec | `specs/chat-experience`; scope answers received, remaining behavior questions pending. |
| 1 | Member user statements and clarification answers are plain text; guest/shared render explicit TeX already. | implement-spec | Webfront isolated slice, actual renderer tests; root reviews resulting diff. |

Decisions confirmed by the user's follow-up: add ordinary explanations without Lean and high-performance model intent routing; allow image-only admission and proceed on a clear problem, otherwise ask; PNG/JPEG, maximum five images per message, each 50,000,000 bytes. Pending decisions: solving/correctness judgments versus the proof route, and source-chat deletion versus published copies. Remaining contract work: local/provider/backup retention and deletion, bounded model input, route model binding and complete image/route usage evidence. No unanswered recommendation is approval.

Delegation: read-only cross-repo spec audit returned existing obligations and gaps; parent inspected cited files. Webfront agent owns user-message rendering components and tests only at base `d436271`, with a 30-minute budget; no spec writes, commits, pushes or runtime stacks. Actual verification output remains to be reconciled by root.

| Criterion | Implementation / evidence | Disposition |
|---|---|---|
| CHAT-002 | Member renderer and bubble CSS at webfront `bb467e78ddcf5fc669503a5f196f9fe0e6477125`; executable rendering/regression checks below | Code verified; browser layout NOT VERIFIED |
| CHAT-001/003/004/005/006 | Confirmed scope; API image contract and image model input absent from request flow | NOT IMPLEMENTED; dependent decisions pending |

No repository-wide spec validator was found in the root scripts/tests inventory. Spec review and Markdown reference validation are required before commit. Japanese lint findings are reviewed together; completed prose keeps user decisions distinct from proposals.

Spec review: guest/shared math regression tasks were made explicit. A reported doubled-backslash defect was not reproduced: root inspected file text and Python representation and confirmed single literal backslashes, matching the existing policy. Japanese lint: natural-japanese requirements/tasks have no findings; design rhythm warning retained because the compact technical obligations are clear. yomiyasu list-ratio warnings retained for parallel acceptance cases and checklist tasks; design has no findings. Root checked subject/predicate, connections, source authority and document stance together.

Iteration 2: root reviewed raw production/test diff, requested the bubble CSS correction, and reviewed its final direct-child selectors. Rendering preserves source and user notation boundaries; nested paragraphs and display equations now share one bounded user bubble. No dependency, API, model or persistence changes. No prohibited production shortcut or new mock boundary was added.

Executed evidence, webfront directory:

- Agent targeted renderer/selection/Lean-flow tests: 42 passed; legacy/project/guest/share regressions: 93 passed. After CSS correction, affected suites: 38 passed; typecheck, scoped ESLint and whitespace checks passed. These summaries were reconciled with raw code and root reruns, not treated as integration proof.
- Root `npm test -- tests/unit/member-chat-math.test.tsx`: 10 passed, exit 0; actual React/KaTeX, four delimiters, literal code, no user notation rewriting, rejected/malformed input.
- Root `npm test -- tests/unit/legacy-chat-archive.test.tsx tests/unit/project-detail-screen.test.tsx tests/unit/guest-chat.test.tsx tests/unit/chat-sharing.test.tsx`: three existing files / 80 tests passed, exit 0. `project-detail-screen.test.tsx` does not exist and matched no file; no separate root project-screen suite is claimed.
- Root production build: first run compiled/typechecked but prerender failed because API base configuration was absent. Re-run `NEXT_PUBLIC_PALS_API_BASE_URL=http://localhost:8000 npm run build` passed, exit 0. This sets the existing local build configuration; it does not verify API availability or authentication.
- Relative Markdown links: eight affected files, zero missing targets. Root/submodule `git diff --check`: passed. Japanese lints executed as recorded above. No browser, provider, database, guest-image or shared-image integration check ran.

Webfront commit pushed successfully to `origin/codex/chat-experience` before parent submodule reference update. Parent work contains only this workflow's specs/evidence and that reference. No application or container stack was started. No task-owned process remains.

Stop reason: scoped math code is checked and saved; full CHAT-002 browser acceptance and image/UI redesign remain open. Pending questions concern meaningful behavior, not internal approval. Resume with the user's answers, settle remaining image lifecycle/usage contracts, review the updated specs, then implement the complete guest/member/image-sharing path.

## Follow-up: ordinary explanation route

Changed input: the user approved CHAT-007–010 as recorded above. Root updated CORE-003/012/013, PFR-001/007 scope, GUEST-002, BILL-015 and related design/tasks. The explicit explanation approval supersedes universal Lean requirements only for that route; CORE-002 proof conditions and CORE-006 independent review remain intact. Broader math boundaries remain an interview, not an inferred policy.

Read-only agent/API audits established that current assessment and QA demand complete proofs, current API rejects new LLM-only results, and the OpenAI adapter sends text only. Restoring old non-Lean proof generation or disabling Lean-flow is not a valid explanation implementation. The smallest independent vertical slice is text-only purpose classification → dedicated explanation generation/review → route-bound API settlement and truthful member/guest/shared rendering. Implementation still needs the selected routing boundary and release/model/meter contracts.

Lifecycle audit: guest 48-hour expiry currently denies reads but does not purge; revoked shares retain immutable payloads and reject physical deletes; there is no chat-delete endpoint; published snapshot JSON has a 2MiB cap, so up to 250MB originals require separate image payloads. Existing bounded PNG/JPEG validation can be reused without its paid-Project gate. Local OCR alone fails on textless diagrams. No retention claim for provider or backups is made.

Runtime prerequisites: no API/agent virtualenv or configured integration-test PostgreSQL URL in this checkout; frontend dependencies remain from the earlier slice. Existing listener ports are not proof of app ownership, readiness or credentials. No application/container, database, provider call or model change was started. No new integration evidence replaces the previous NOT VERIFIED entries.

Follow-up verification: read-only spec review found scope/acceptance, guest implementation-label and member-versus-guest/token-policy ambiguities; root corrected them and added CHAT-010 boundary/format/corruption tests to the task trace. The targeted second review confirmed those findings resolved; full implementation readiness remains open. Fourteen changed Markdown files have zero missing relative links; `git diff --check` passed. natural-japanese lint passed on requirements/tasks/core/guest with no findings; design's rhythm-only warning was retained after reading. yomiyasu lint and one diff inspection passed; task/acceptance list ratios and unchanged legacy spacing were retained. Meaning additions are the explicit user-approved delta, not stylistic inference; the proof gate remains unchanged.

Additional user question: proposed member images follow chat history; unsent files stay browser-local; guest purge follows 48-hour session expiry; normal-store deletion within 24 hours and backup deletion within 30 days. This is a proposal awaiting answer, not a decided lifecycle or an existing deletion guarantee. It does not imply external-provider erasure.

Current outcome: approved CHAT-007–010 requirements and cross-repo design/task alignment are reviewed and saved; no explanation/router/image production code was changed in this follow-up. Next action is to use the user's pending routing/lifecycle answers, select and verify the released high-performance model role and its meter contract, then implement the text-only explanation vertical slice before extending it to real images and frozen image sharing. No temporary lint/diff files or task-owned processes remain.
