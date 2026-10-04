# Real PDF verification — 2026-10-04

Scope: existing MacBook `pals-local` instance, existing Stripe Pro account and existing private test project/chat. No entitlement grants, purchases, production writes, or new model calls were made during this verification.

The user authorized one local upload of `20240301_Krystal_Geck.pdf` (Geckによる半単純リー代数の構成). The original is 94,839 bytes and 14 pages; SHA-256 is `503ad59296e9611a89d66b4818222266293eb4d68da47519e77ec72d0593ba31`. The Library copy has a different byte identity and was not used.

Authenticated HTTP verification confirmed:

- Existing billing summary: `plan=pro`, `entitlement_state=active`, `billing_source=stripe`.
- Upload returned a material with 14 pages; extraction progressed from `queued` to `ready`, with `extracted_pages=14` and no extraction error.
- A subsequent list retained the uploaded material; downloading its original reproduced the exact original SHA-256.
- Authenticated page previews for pages 1 and 14 returned valid PNG images.

Material ID: `79235b56-ce13-4ce6-b4c8-99592a66c22f`. Project ID: `b61b5941-7406-45b4-a77b-916273489244`. Existing chat ID: `f7765394-d5df-41fb-adb3-b1f950756983`. Task-local JSON and page images remain outside Git.

Focused non-mutating API tests: 24 passed, 1 skipped. Coverage includes Free upload rejection without storage effects, ownership, PDF page limits and extraction, and processing timeouts. The host Tesseract test was skipped; the running API Docker image supplies Tesseract. New real-account Free rejection was not performed because an existing authenticated Free test account was not confirmed.

The paid gate applies to new material uploads, not project creation. Free/expired users retain access to existing attachments. This is existing behavior, not a new change in this verification.

The browser required sign-in again; this session did not retrieve a password to complete that flow. AI answering/citations for this specific PDF remain unverified because new model calls were stopped pending credential replacement. Earlier synthetic OCR-to-answer verification is recorded separately. Production write testing remains subject to coordination with the Mac mini migration. Public anonymous probes from this session returned HTTP 403; deployment-job success alone does not establish the served OCR revision.
