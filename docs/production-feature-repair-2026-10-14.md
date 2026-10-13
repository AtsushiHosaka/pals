# Production feature repair — 2026-10-14

This record distinguishes current production observations from source and isolated-test evidence. Existing features and deployment guards are preserved.

## Project session repair

[Frontend PR22](https://github.com/AtsushiHosaka/pals-webfront/pull/22) fixes an authentication classification error: an HTTP403 `project_plan_required` response previously signed the user out. The exact business denial now preserves the session while still rejecting project creation. HTTP401, other403 responses and malformed envelopes retain the existing authentication handling.

The new regression failed before the repair. Sixty-one focused frontend tests, TypeScript, changed-file ESLint and diff checks passed. Independent source review found no actionable defect. Production deployment of this repair remains pending.

## Current production observations

- A signed-in Pro session created private project `790b0119-43ba-4553-9da9-a743706bf200` and chat `e9c8f7eb-c319-46b6-a259-8fb30bfd6b1d`; the project overview lists the saved chat.
- The previously failed demo PNG in project `bc1c567c-3378-489f-9168-7d43bfb2885e` is ready after reload and its original preview loads. [Read-only inspection38425724517](https://github.com/AtsushiHosaka/pals/actions/runs/38425724517) independently confirms one ready material and one persisted extraction page, with no failed/queued/processing records or extraction error. The original-file UPDATE privilege remains absent. Its availability probe does not establish the serving connection role.
- A fresh coprime-divisibility proof in the new project still returns “Lean verification is not available right now, so no answer can be shown.” Project creation and chat persistence therefore do not establish usable formal proof delivery.
- [Fresh runtime inspection38425212526](https://github.com/AtsushiHosaka/pals/actions/runs/38425212526) has only `assessment_queue_not_ready`; memory capacity is sufficient. [Queue inspection38425448883](https://github.com/AtsushiHosaka/pals/actions/runs/38425448883) narrows this to `queue_aws_authentication_unavailable` at the fixed administrative launcher. It does not distinguish expired from missing or invalid authentication. The user was given the documented Mac mini sign-in renewal command. No Lean runtime switch occurred.

## Remaining verification

Release the frontend fix and verify its actual deployment receipt. Verify fresh PNG and scanned-PDF upload, OCR readiness, preview and persisted material use. After the Mac mini operator authentication is restored, obtain fresh queue/runtime plans, activate only a ready exact plan, and prove a newly generated Lean job, delivered answer and learner-opened source. Finalize predecessor containers only with the newly verified delivered job. Do not weaken admission, TLS, ownership, resource or exact-plan checks.
