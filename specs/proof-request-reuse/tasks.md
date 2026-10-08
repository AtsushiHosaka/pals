# Implementation tasks

Working baseline: requirements and design in this directory, user approval 2026-09-30 plus the 2026-10-05 Lean-required and Recipe-first correction. Earlier checked items describe executed historical slices; they do not certify the new flow. Existing uncommitted work is preserved. Budget 120 minutes for this implementation pass, commands normally ≤60 seconds, two transient retries maximum; root owns cancellation and final cleanup.

- [x] PFR-001: Luna/Terra bindings, Responses parameters, usage and price registration; targeted model and price tests.
- [x] PFR-002/003/008: real catalog/LLM reuse and instantiation, bounded escalation, application evidence, worker queue integration; mathematical rejection and no-Lean tests.
- [x] PFR-004/005/006: durable PostgreSQL request/answer/lease/outbox/usage/quota API and release migrations; actual DB integration checks.
- [x] PFR-007: project and projectless UI, premise answers, reload/polling/owner isolation and safe rendering; interaction tests and typecheck.
- [x] PFR-009: connect existing real Draft sketches through read-only natural-answer retrieval; independent trust-boundary review and actual n→2 probe.
- [x] Cross-repository transport and real-provider smoke, regression checks, architecture review and local release evidence. Direct answer, premise continuation/reload and source-backed n=2 instantiation verified. Production deployment and broad accuracy/p50/p95 evaluation remain separate, unexecuted work.

## 2026-10-02 ordinary-send acceptance slice

- [x] CORE-012/013, PFR-002/007: remove the unapproved Lean-mode UI while preserving both ordinary composers, independent answer review and existing formal history; run affected UI/static regressions.
- [x] CORE-003/006, PFR-002/008: verify real local-provider answers for plain Japanese square continuity and determinant multiplication through ordinary Send, including exact assumptions, a meaningful derivation and honest no-Lean evidence.
- [x] PFR-005/007: verify durable answers after a fresh application restart and record the reproducible local demo runbook.

October 2 execution stops feature expansion at 06:00 JST under the user’s explicit deadline. The earlier 120-minute implementation budget does not extend that deadline.

- [ ] PFR-005 / BILL-013 release follow-up: recover an exact ambiguously dispatched paid operation when its original hold leaves no available balance; retain the scoped quote and permit only the exact replay through UI allowance gates. Current backend fresh-quote idempotency repair is tested, but the frontend boundary remains open.


- [x] PFR-005/006: reject JSONB-incompatible provider Unicode before evidence retention and QA/hash binding; preserve safe durable failure and receipts. Agent parser regressions and actual PostgreSQL HTTP/settlement regressions pass. Real ordinary-send retesting remains governed by the unchecked October 2 acceptance items above.

October 2 local acceptance evidence: four consecutive ordinary Mac Chrome core answers with exact-answer independent QA; same-image restart of six application services preserving dependency data; saved answer/receipt/accounting equality; new postrestart Mac Chrome square answer. Additional determinant, rank-nullity, radical-product and inclusion-exclusion real HTTP integration cases also exact-QA bound. Subsequent UI checks unavailable after execution-context switch; production source/release/deployment remains separately unaccepted. Runbook: docs/2026年10月2日.md.

## 2026-10-05 Lean-required flow

The user directed that every new answer is Lean-verified (PFR-002, PFR-006, PFR-007, PFR-010–PFR-013). Plan: `docs/lean-required-flow-plan-2026-10-05.md`. Items are checked only with executed evidence.

- [x] Local Lean runtime: refresh the expired local verifier/reconciler TLS material, start the verifier and verify one existing proof job end to end. Evidence: `docs/lean-required-flow-evidence-2026-10-05.md`.
- [x] PFR-010/012 API: Lean-flow storage as the appended `proof-request-lean` step (`proof_request_lean/001_lean_flow.sql`, because the Mac update contract only allows appended steps), registered in the local release with upgrade/drift tests (`test_proof_request_lean_migration.py`) and applied to the local shared database.
- [ ] PFR-010/012 production: add `proof-request-lean` to the production registry, the Mac update and the strict production startup check (API `9fdcbf5`).
- [x] PFR-006/012 API: `catalog_reuse` and `formal` settlements, linked job creation without a second reservation, job/explanation terminal propagation with exactly-once consume/release; real PostgreSQL tests (`test_proof_request_lean_flow.py`).
- [x] PFR-010 API: worker Recipe lookup and settlement re-verification of source SHA-256, admission receipt and active toolchain fingerprint; tamper tests (`test_proof_request_catalog_settlement.py`, `test_proof_request_sources.py`).
- [x] PFR-002/010/013 agent: decision → `catalog_reuse` / `formal(instantiate|dsp)`; no LLM-only answers; reuse answer from Recipe source with independent review (`test_proof_reuse_lean_flow.py`).
- [ ] PFR-011 agent: request-linked jobs compile the specialization wrapper before DSP.
- [ ] PFR-006 agent/API: linked-job provider calls use the request's token operation permits.
- [x] PFR-007 webfront: Lean progress, verified answer with source/explanation/follow-ups, failure without answer text; project, projectless and guest; four languages (`proof-request-lean-flow.test.tsx`).
- [x] Real local journeys: DSP, failure (semantic review rejected a weakened statement; no answer, hold released), follow-up, guest, phone/tablet/PC. Evidence: `docs/lean-required-flow-evidence-2026-10-05.md`.
- [ ] Real local journeys: catalog reuse and specialization. Blocked locally: the local Draft table has no PFI catalog for alignment admission, and PFR-011 is not implemented.
- [ ] Production prerequisite: proof-request assessment must not wait behind Lean jobs. Run a `natural-only` worker for proof requests beside the `full` Lean worker (one worker processes one SQS message at a time).

## 2026-10-08 Recipe-first acceptance

The following items cover the current Recipe-first path. The preceding October 5 section retains its executed historical evidence. The user directed that every new answer is Lean-verified and that direct Recipe search precedes DSP/Draft reuse after the premise/refutation checks (PFR-002, PFR-006, PFR-007, PFR-009–PFR-017). Plan: `docs/lean-required-flow-plan-2026-10-05.md`. Items are checked only with executed evidence.

- [ ] PFR-006/012 API: `catalog_reuse` and `formal` settlements, linked job creation without a second reservation, job/explanation terminal propagation with exactly-once consume/release; real PostgreSQL tests.
- [ ] PFR-010/017/016 API: direct bounded Recipe retrieval independent of Draft/alignment; immutable source/description/answer review entries; admission/operator command and final transaction revalidation; source/answer/review/toolchain tamper, retirement and replay tests.
- [ ] PFR-002/009/010/013/017 agent: Recipe-first signature extraction, candidate assessment, independent request/source correspondence and exact stored-answer QA; `catalog_reuse` versus `formal(dsp)`; no explanation generation on reuse and no Draft call outside DSP Draft.
- [ ] PFR-011 agent: new request-linked jobs enter full DSP for specialization and compile their new source; preserve the separately traced legacy ordinary-job specialization behavior.
- [ ] PFR-006 agent/API: linked-job provider calls use the request's token operation permits.
- [x] PFR-007 webfront: Lean progress, verified answer with source/explanation/follow-ups, failure without answer text; project, projectless and guest; four languages (`proof-request-lean-flow.test.tsx`).
- [x] Real local journeys: DSP, failure (semantic review rejected a weakened statement; no answer, hold released), follow-up, guest, phone/tablet/PC. Evidence: `docs/lean-required-flow-evidence-2026-10-05.md`.
- [ ] Real local journeys: catalog reuse and specialization. Blocked locally: the local Draft table has no PFI catalog for alignment admission, and PFR-011 is not implemented.
- [ ] Production prerequisite: proof-request assessment must not wait behind Lean jobs. Run a `natural-only` worker for proof requests beside the `full` Lean worker (one worker processes one SQS message at a time).

- [ ] PFR-017 negative matrix: a nontrivial real admitted source accepts paraphrase/binder renaming; rejects domain, missing/extra premise, quantifier-order/scope, changed conclusion and requested method mismatches; specialization compiles. Independent disagreement/uncertainty falls through, provider/integrity failures fail explicitly.
- [ ] PFR-010/017 zero-call witness: reuse with legacy Draft reader unavailable and no alignment still returns admitted source and stored reviewed answer byte-for-byte; verifier, generators, Draft client and linked-job count remain zero. Admission uses real Lean; runtime witness uses real PostgreSQL and a bounded real provider check when credentials permit.
- [ ] PFR-016 race/compatibility: retirement/toolchain change between retrieval and settlement cannot produce stale reuse; retries settle once; old `llm_assessed` history and old exact-target selector remain readable/valid unchanged.


## 2026-10-05 Ask before proving (PFR-014)

The user approved asking back first when a request is likely false or its truth depends on an unstated choice.

- [x] PFR-014 agent: `premise_check` in the assessment schema and prompt; validation and private evidence; localized fallback question; unit tests (`test_premise_check.py`, agent `4bc1433`).
- [x] PFR-014 evaluation: a fixed 26-case real-provider set (`pals-scripts/premise-check-eval.py`): 19/26 before, 26/26 in two runs after. Evidence: `docs/premise-check-evaluation-2026-10-05.md`.
- [ ] PFR-014 real local journey: a false claim is asked about before any Lean job; choosing the corrected claim proves it with Lean; keeping the statement as written is not asked again.
- [ ] PFR-014 next: check a suspected counterexample with Lean before presenting it, and after a failed proof try the negation so a false claim is reported as Lean-refuted.

## 2026-10-05 Recipe-first implementation slice

Executed evidence and remaining gates: `docs/recipe-first-implementation-2026-10-05.md`. The broad acceptance items above remain unchecked when they include unexecuted provider or deployed journeys.

- [x] PFR-017/016 API: immutable direct-search entry admission, alignment-free retrieval, locked settlement, exact stored-answer persistence, owner/guest source readback, retirement/tamper/replay and release-gate PostgreSQL checks.
- [x] PFR-009/013/017 agent: Recipe-first assessment, independent correspondence and stored-answer QA, full-DSP fallback, DSP-only Draft retrieval and zero-generation/compile unit witnesses; affected transport and token-meter regressions.
- [x] PFR-007 source viewer: exact nine-field DTO/digest validation, cancellation/retry, four-language strings, and legacy history compatibility; unit tests, TypeScript and ESLint.
- [ ] PFR-010/017 actual-provider reuse witness and deployed project/projectless/guest acceptance: opt-in runtime test is implemented; external-send consent remains pending.

## 2026-10-05 Lean refutation (PFR-015)

- [x] PFR-015 API: `refute` plan, `verdict: refuted` answers, a failed refutation followed by a DSP job for the claim; shared snapshots say the claim is false; real PostgreSQL tests (api `03ecaa5`).
- [x] PFR-015 agent: refute plan after a clarification when a counterexample is still reported; localized negation statement; unit tests (agent `e8d3467`).
- [x] PFR-015 webfront: "Lean-refuted" label for project, projectless and guest answers in four languages (webfront `e19606c`).
- [x] PFR-015 real local journey: "n² + n is odd" kept as written was refuted by Lean (`¬ ∀ n, 0 < n → Odd (n² + n)`) and shown as "Leanで反証済み：この主張は偽です" with the counterexample n = 1. Evidence: `docs/math-conventions-evidence-2026-10-05.md`.
