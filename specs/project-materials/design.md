# Project materials design

## API

`/v1/projects/{project_id}/materials`: `GET` list, `POST` raw-body upload (`X-File-Name` percent-encoded UTF-8, ownership and paid entitlement checked before the body is read), `DELETE /{id}`, `GET /{id}/content` (attachment disposition), `GET /{id}/pages/{page}` (server-rendered PNG), `POST /{id}/retry`. Private responses use `no-store`, `nosniff` and a sandboxed CSP. Originals are PostgreSQL `bytea` committed with their metadata; a project row lock and a capacity trigger enforce MAT-001.

Parsing runs in a credential-free child process: at most 5,000 PDF pages, 20 million image pixels, a 30-second parse deadline and two concurrent upload/preview slots per instance. Encrypted or invalid documents are rejected.

## OCR ingestion

The long-running API process runs a durable queued/processing/ready/failed job per material, one at a time per instance. Text PDFs use PDFium; scanned pages and images use Tesseract (en, ja, zh-Hans, zh-Hant), and mixed pages keep both. Each page is committed separately; expired leases recover after restart; a material is `ready` only after every page is committed. Per-page subprocess bounds are 55 s, 45 CPU s and 1.5 GB.

## Answer binding

At proof-request admission the project lock is taken and the materials are selected (MAT-005). Explicitly named files restrict the selection. Without a named file, failed extractions are excluded (MAT-016); any queued/processing material rejects admission with `material_context_processing`; a named failed file rejects with `material_context_unavailable`. The selected excerpts form an immutable RFC 8785/SHA-256 snapshot bound to the token quote, request, clarification and retry. The worker reads it only under a live claim. Settlement validates every citation's page, filename, hash and exact excerpt and holds the project lock; a deleted source turns the result into a failure and releases its reservation.

## Frontend

There is no learner-facing materials UI: neither a project-home panel nor answer citations are rendered. `MaterialCitations` and its read-only `MaterialPreview` page dialog remain in the codebase unused; reintroducing them requires a new placement decision. Submission errors for unready materials are still shown in the chat language.
