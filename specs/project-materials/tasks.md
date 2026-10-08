# Project materials tasks

Evidence: [implementation and OCR](../../docs/project-materials-implementation-2026-10-04.md), [real PDF verification](../../docs/project-materials-real-pdf-verification-2026-10-04.md).

- [x] MAT-001/002/008/012: Upload, limits, deletion fencing and paid entitlement for additions (real PostgreSQL).
- [x] MAT-004: Page-by-page PDFium/Tesseract ingestion with durable jobs and recovery (1,000-page real run).
- [x] MAT-005/006/007: Bounded selection, snapshot binding, citation validation, page preview and extracted-proposition confirmation (real provider run).
- [ ] MAT-003: Restore the project-home PDF/PNG/JPEG upload, list, cancellation, retry, confirmed deletion, page preview and original download UI removed by webfront `fc3a0b5`. Preserve paid upload gating and existing-material access after entitlement expiry.
- [ ] MAT-003: Verify a real PDF upload from the browser through persistent listing, page/original viewing and deletion; check four locales, keyboard access and phone/tablet/desktop layouts. Confirm that the unwanted answer-side OCR/citation panel stays hidden and stored citations are unchanged.
- [x] MAT-016: Exclude unnamed failed extractions from admission; unit tests cover named/unnamed failed and processing cases.
- [ ] MAT-016: Re-run `tests/integration/test_proof_material_context.py` on real PostgreSQL.
- [ ] MAT-011: Inline chat images (not started).
- [ ] MAT-012: Paid gating for new project creation (blocked on the individual-billing open question).
