# Chat composer and four-file attachments

Authority: WORKING contract from the user request on 2026-10-12. Make the existing chat composer more like ChatGPT and support up to four PNG, JPEG or PDF files per message. Earlier PNG/JPEG work was on unmerged branches; it was restored onto current main rather than replacing newer fixes. This record does not mark canonical specifications or production release acceptance complete.

## Pinned integration

Parent base: `3f09f328dae3553d6ac057cdbfdc1b85e2f8435e`. Current geometric branding, restrained red theme and account-settings language placement are preserved. API and worker main merges changed ancestry without changing their inspected source trees.

| Repository | Pushed source |
|---|---|
| pals-webfront | `d205efbcf319fff5c30e42be1412d8128fc59441` |
| pals-api | `b0b5bdda3566d073bda1d24a7b3013322efd9b70` |
| pals-agent | `021758e4222544a1a1f3350eef2a7f6d2e4856ad` |
| pals-infra | `4299b56cae5f6ecfce9275da9d5693c7e3c3afa0` |

Draft PRs: [webfront #15](https://github.com/AtsushiHosaka/pals-webfront/pull/15), [API #10](https://github.com/AtsushiHosaka/pals-api/pull/10), [agent #7](https://github.com/AtsushiHosaka/pals-agent/pull/7), [infra #19](https://github.com/AtsushiHosaka/pals-infra/pull/19).

## Behavior and evidence

| Criterion | Implementation and current evidence |
|---|---|
| PNG/JPEG/PDF, four per message | Shared composer across public landing, guest, project and projectless chats; mixed four-file selection, fifth-file rejection, removal, file-only submission, drop and paste regressions. Server submission contracts enforce four separately from the historical context manifest. |
| Recoverable drafts | Upload only on send, retain upload identities on retry, retry to the same chat with the same selected files, discard unbound uploads on removal/navigation and retry failed cleanup before further uploads. Server separately bounds pending storage at 16 files / 800 MB and removes expired drafts before capacity checks. Real PostgreSQL tests exercise abandoned drafts, replacement capacity and discard recovery. |
| Complete PDFs | Every accepted PDF page is rendered and hash-bound to generation, independent review and linked Lean delivery. First-page previews are labelled; owner/guest original PDF downloads validate media type, size and original SHA-256. Shared PDFs expose fixed first-page previews, not original downloads. Real two-page PDF decoding and API/worker hash equality passed. |
| Bounded processing | Original files <=50,000,000 bytes. PDFs <=20 pages, <=16 MB derived per file, <=20 MB derived context and <=20,000 auxiliary text characters. Limits fail explicitly without omitting pages. Upload timeout covers the API's 90-second parser allowance. Worker HTTP context transport is separately bounded at 56 MB; ordinary control responses retain their smaller bound. |
| Conversation context | Four applies to one message; frozen worker manifests may include up to 330 unique historical/current IDs. Regressions cover initial four plus clarification, and multiple four-file messages. Legacy five-image history remains readable. |
| Responsive presentation | Rounded composer, plus button, removable thumbnails, PDF tiles and internal attachment scrolling. Real browser checks at 1280x900 and 390x844; phone document width remained 390px with four selected files. Final screenshots retain the current PALS brand/theme. |
| Release integrity | New signed Mac v7 preserves the exact 32-step registry and appends the chat schema. Existing QA v6 remains distinct. Host checks preserve old rows while admitting only the fixed new model default. Explicit edge routes use a 51 MB multipart upload bound. |

Frontend TypeScript, ESLint and production build passed after current-main integration. Full suite: 1,539 passed, two existing `use-proof-job-events` failures; both reproduced on untouched `7c2b8e3`, and the tested event hook/tests are unchanged by this branch. Final focused attachment/composer suite passed, including retry and navigation cleanup.

API: initial 24 real PostgreSQL attachment/runtime-authority/chat-migration checks, affected 128 proof/production unit checks, 39 chat unit checks and 44 release checks passed. After recovery/context fixes, nine attachment integration tests passed on the task-owned pgvector PostgreSQL 16 instance. Scoped Ruff and mypy passed.

Worker: 400 affected tests initially passed; 129 affected tests passed after the complete-context correction. Full unit run: 3,173 passed and 35 failures, all reproduced on untouched `4422d48`. Scoped Ruff/mypy and real API DTO checks passed. Test fixtures isolate provider boundaries; they do not establish provider interpretation or deployment success.

Infrastructure: 149 host tests passed with one real PostgreSQL test skipped, plus two edge-route checks. Root inspected the closed v7 capability and immutable byte pins. The cached Caddy 2.10.2 binary successfully adapted and validated the attachment snippet in a network-disabled command container; this verifies syntax, not installed public routing.

UI Pocket reference: [ChatGPT mobile gallery, October 2024](https://www.ui-pocket.com/mobile/apps/chatgpt/2024-10). The user signed in and the file-upload flow was located. Its screenshots require Pro, so screenshot-level comparison was unavailable.

## Composer disclosure follow-up

The user requested removal of the OpenAI data-policy disclosure beneath the composer. Removed the disclosure and its CSS. Attachment behavior is unchanged. The focused attachment/keyboard suites passed all 24 tests, and TypeScript passed. Earlier preview screenshots predate this text removal.

## Remaining release checks

Implementation is pushed and reviewable; it is not deployed. `MACMINI_AUTO_DEPLOY` was false at the live audit. Before production acceptance:

1. Complete the exact signed 32-to-33 registry replay against the required PostgreSQL dependencies. A single cached-pgvector attempt failed at the historical 25-step predecessor bootstrap before the candidate DDL; it did not prove the signed transition.
2. Review/install the protected host source-hash policy and explicit v7 capability, then validate/install the attachment edge snippet inside the existing Host-restricted API handle.
3. Merge/release exact reviewed child commits and parent pins through the signed deployment path.
4. Verify authenticated owner and guest four-file upload, persisted history and original downloads, actual provider interpretation of every PDF page, and deletion/share/retention recovery. Local tests do not establish these deployed outcomes.

No production database or running PALS container was changed. The task PostgreSQL container was removed; temporary Caddy validation containers self-removed. The local frontend verification server is task-owned and is stopped after screenshots are saved. Existing app servers and shared database containers are preserved. Generated previews and raw test outputs remain outside Git.
