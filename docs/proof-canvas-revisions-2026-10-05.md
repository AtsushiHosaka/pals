# One evolving proof — 2026-10-05

The user requested preserved drag selection, quoted follow-up question history, and removal of the persistent floating question field. Their clarification specified one proof whose selected passages are updated, as in a Canvas, rather than repeated full-proof messages.

## Delivered behavior

The composer retains a cloned selection highlight and a mathematical quotation. Sending immediately replaces the floating field with an inline quoted question and pending response. Accepted requests close the field; rejected requests restore the draft and quote without automatic redispatch. Busy-section rejections keep the draft inline without overlapping the proof. Saved questions appear as black bubbles below the proof.

The agent generates a replacement for the exact selected excerpt and derives the complete revised section. Both texts pass the independent review and enter its canonical output hash. API admission and settlement validate the current parent, exact splice and unchanged surrounding text. Competing or stale edits fail safely; the worker settles those failures instead of repeatedly generating paid output.

The frontend displays one proof and replays only valid completed revision chains. Subsequent selections use the saved current section, including selections spanning changed and unchanged prose. It preserves selection and parent provenance through POST, polling and hydration. Brief revision confirmations are not selectable proof text; legacy supplemental answers remain selectable. Original proof content, verified Lean source and review provenance remain immutable.

Fresh shared snapshots include the current proof and quoted follow-ups, including jobs linked to proof requests. Projection validates the revision chain and stored proof, parent and Lean review hashes. Existing published snapshots remain frozen. A new snapshot of later edits requires revoking and publishing again, following the existing sharing contract.

## Validation

Frontend: all 1,441 tests passed across 127 files. TypeScript, ESLint, production build and diff checks passed. The subsequent busy-draft placement adjustment passed 54 focused tests, TypeScript, ESLint and diff checks. New tests cover exact longer/shorter splices, rejected and stale output, quote visibility, dispatch/rejection behavior, source mapping, CSS highlight cleanup, real hook-to-component HTTP normalization, reload and provenance changes during polling.

API: 180 focused schema/service/route/story/OpenAPI checks passed. One real PostgreSQL integration test passed on the existing local container using an isolated temporary schema, removed afterward. It covers durable revision pairs, review-hash tampering, stale competing settlement, child selections across updated and untouched text, reload and immutable original proof. Focused Ruff and MyPy checks passed. Unrelated baseline Ruff line-length errors remain in existing repository/test code. Regenerating OpenAPI also reconciled pre-existing differences between the checked-in artifact and current source.

The subsequent sharing adjustment passed 11 unit tests and 11 real PostgreSQL tests (10 sharing tests and a repeat of revision settlement). Coverage includes cumulative projection, invalid revision evidence, current preview digest, publication/read equality, frozen snapshots, revoke/new publication, and linked-request owner/chat isolation. Ruff, MyPy and diff checks passed for the sharing changes.

Agent: 269 focused generator/reviewer/worker/claim tests passed, with Ruff, MyPy and diff checks. An offline cross-repository smoke used the actual agent generator/reviewer interfaces, worker evidence builder and API validators to verify initial and cumulative revision DTOs, short confirmations, matching content/context hashes and legacy omission semantics. No live paid generation was performed.

Real desktop (1440×900) and phone (390×844) browser checks used production components with a temporary display fixture. Drag selection crossed formulas, typing retained visible selection and quotation, sending removed the floating field, and the revised proof appeared once with saved question history. Screenshots were inspected for clipping, overlap and horizontal overflow. The fixture was removed before the successful production build. Evidence remains in ignored `pals-webfront/output/playwright/proof-canvas-*.png`.

## Implementation references

- API: `f4f735d`, sharing adjustment `45907b3`, branch `codex/proof-canvas-revisions`.
- Agent: `0a2d0a4`, branch `codex/proof-canvas-revisions`.
- Frontend: `bd404e7`, busy-draft adjustment `13c6519`, branch `codex/quoted-proof-followups`.

The existing local application containers have not been redeployed. The changes are published as implementation branches.

## Bounds

Selection is still limited to one section and 800 source code points. A repeated excerpt must include sufficient context to identify a unique occurrence; overlapping duplicates are also rejected. Revised sections are capped at 12,000 code points. The reviewer sees the initial other sections and the selected section's current revision. Editing theorem premises or the formal claim requires a new proof request.
