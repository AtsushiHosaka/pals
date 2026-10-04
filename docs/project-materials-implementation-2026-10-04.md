# Project attachments: implemented upload and viewing

Implemented on 2026-10-04 in `pals-api` and `pals-webfront`, and applied to the existing `pals-local` API/Web/PostgreSQL services. The public deployment destination has not been confirmed; this evidence does not establish a release to palschat.site.

Component commits: API `07390f1`, frontend `13230d7`. The committed source, with peer working changes excluded, independently passed 45 backend unit/regression tests and 50 frontend unit/story tests plus frontend type checking before push. The four real PostgreSQL attachment tests passed separately.

## Delivered behavior

Project home now lists private PDF, PNG and JPEG attachments, with file selection, upload status/cancellation, safe page previews in a right panel, original download, and confirmed deletion. Four UI languages follow the existing locale setting. Existing attachments remain readable after paid entitlement expires; new uploads require the API's current paid entitlement. A failed billing lookup displays a retry action rather than identifying the user as unpaid.

Each project has at most five stored files, including concurrent requests. Each file is limited to 50,000,000 bytes. PostgreSQL commits original bytes and metadata together; project row locks and a capacity trigger protect the limit. Every operation checks the owner and project. Deletion removes the stored original and blocks subsequent original/page requests. These checks do not claim immediate erasure from PostgreSQL backups.

The parser validates the actual format in a child process without application credentials. PDF pages are rendered to PNG rather than embedded as executable documents. Original downloads use attachment disposition; private responses disable caching. Encrypted and invalid documents are rejected. Parser limits include 5,000 PDF pages, 20 million image pixels, a 30-second parser deadline, and two concurrent upload/preview slots per service instance. The local API temporary filesystem was enlarged to 256 MiB for bounded file processing.

Additive, hash-checked migrations are registered in both local and production release paths. Serving performs a schema/grants preflight and does not create tables. Originals are stored as PostgreSQL bytea in this implementation, rather than the object-store staging architecture in the older proposal.

## Verification

- Backend: 20 attachment unit tests and four tests against disposable real PostgreSQL databases passed. They cover the exact 50 MB boundary, streamed input with misleading Content-Length, real PDF/image parsing, 1,000 PDF pages and final-page rendering, parser timeout, deletion during rendering, authentication, owner/project isolation, entitlement expiry, repository restart, migration drift, and 12 concurrent inserts accepting exactly five files.
- Frontend: 32 attachment/API tests passed. A combined run including existing project overview, session isolation and project creation race stories passed all 50 tests. TypeScript, full frontend ESLint and the final production image build passed. New backend files passed Ruff and strict mypy. The existing routes aggregate has a pre-existing import-order Ruff warning.
- Live HTTP with the existing Cognito test account: uploaded a synthetic three-page PDF; verified persistent listing, exact original bytes, PNG previews of pages one and three, missing-page rejection and unauthenticated rejection. After deleting the synthetic PNG, both original and page endpoints returned 404.
- Existing Chrome tab: opened the project, navigated to the PDF's third page, uploaded PNG through the file chooser, reloaded and observed both attachments, downloaded the PDF, and checked its SHA-256 against the uploaded original. The browser download-event adapter timed out although the actual saved file matched. Delete confirmation/cancellation, Escape and focus restoration were checked. At the browser's actual mobile viewport width of 433 px, the panel had no horizontal overflow. Console error/warning logs were empty.
- One existing local release integration test still fails at the independent Recipe login preflight. The same failure was reproduced with attachment migration disabled; two other local release integration tests passed. This report does not claim the complete local release integration suite passed.

Runtime evidence and synthetic files are task-local under `/private/tmp/pals-materials-runtime/` and are not committed. User-owned working changes were retained and excluded from this change's commits.

The synthetic three-page PDF is retained in the local test account's project `b61b5941-7406-45b4-a77b-916273489244` for manual inspection. The PNG used to verify deletion was removed; all four disposable database fixtures were cleaned up.

## Remaining proposal scope

OCR, semantic search, using material contents as actual AI input, answer citations, inline chat image input, and paid-only project creation remain outside this attachment upload/viewing implementation. PDF validation/page viewing does not establish all-page OCR completion or proof readiness. These items in the older project-materials proposal must not be marked complete by these results.
