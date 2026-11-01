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

## 2026-11-01 Recipe latency and exact-input profiles

Authority: the user explicitly requested reuse of the existing natural-power
continuity Recipe, a public answer within ten seconds and independent work in
parallel. Baseline is the actual sequence-9 release, API `adda209` and worker
`d58b60d`. This additive change affects PFR-010/016–018 and LRC-018/020; it does
not authorize weaker proof evidence or an unverified fixed answer.

- [x] Diagnose the actual slow request: the power Recipe was retrieved and passed all scope checks; independent answer correspondence rejected it before new DSP generation. Record the missing rejection-rationale evidence as a diagnostic gap.
- [x] Define the separate exact-input contract and independently review the two complete Japanese question forms against the admitted universal natural-power theorem, including zero and the recorded power convention.
- [x] PFR-018 API: authoritative finite registry, distinct closed evidence kind, exact current request/claim/context/convention validation and unchanged locked catalog/answer/lifecycle revalidation. No schema migration or worker-created provider approval.
- [x] PFR-006/018 API: permit zero-provider token settlement only from server-established exact-profile validation and absence of provider call records; retain normal holds, guest limits, replay fences and non-profile settlement behavior. Real PostgreSQL positive/negative/replay tests.
- [x] PFR-018 agent: real authenticated catalog retrieval and exact immutable entry validation before zero-call reuse; unknown input or context retains the ordinary route. Prove generator, compiler, Draft, explanation and model call counts remain zero for eligible inputs.
- [x] PFR-010/017 general path: independently assess and review the same bounded candidates concurrently, require exact agreement, preserve separate request context and token-call attribution, and retain bounded private rejection reasons.
- [x] Hard negatives: changed exponent type, conclusion, quantifiers, method, output language, conventions, added text, history/material/image context, source/answer/toolchain tampering, retired entry, stale claim and forged profile must not be accepted as matching reuse.
- [x] Signed software-only deployment followed by real public guest submissions: exact stored answer/Lean hashes, `lean_catalog`, no linked proof job, zero model/generator/verifier/Draft calls and each measured end-to-end time at most ten seconds. Report actual measurements and any remaining limits. Sequence 11 measured the registered plain-text form in three fresh guest chats: 4.7752/4.6638/4.8301 seconds, with a separate read-only zero-call/source/profile check.
- [ ] Measure the other registered form containing TeX delimiters through the public UI. Do not infer its public timing from the plain-text result.

Evidence: [production measurements and limits](../../docs/aws-recipe-reuse-latency-2026-10-31.md#11月2日の実装と公開確認の状況). API `9b8b004`, worker `122f2f9`: independent review, focused negative/concurrency tests and real PostgreSQL settlement plus guest GET/source/Lean tests. These tests do not establish general-input or concurrent-user latency.


## 2026-11-02 Mathematical paraphrases within ten seconds

Authority: the user rejected literal-only matching and explicitly requested
mathematically equivalent changed questions for natural powers, tan 1 degree and
other Recipes, with real public measurements under ten seconds. Baseline is
sequence 11, API `9b8b004`, worker `122f2f9`, parent `5e88f2e`.

- [x] PFR-019 API: complete authenticated bounded catalog snapshot, server-owned claim/input/batch receipt, explicit empty overflow result, unchanged source/compiler/lifecycle authority and no new DB grants.
- [x] PFR-014/017/019 worker: two genuine independent concurrent original-request/source/answer reviews, full scope/polarity/premise checks, exact same-entry agreement and ordinary-route compatibility; no question-string allowlist for this semantic path.
- [x] Actual-provider experiment: measure all 20 current candidates against 32 fixed questions and select static GPT-6 Luna / low with a 1,536-token output cap per call. Retain all 64 calls and actual usage; no automatic model cascade. Result: 11/13 equivalent inputs accepted, 19/19 negative inputs refused, no parser/provider failures. Classification time excludes the public request lifecycle.
- [x] PFR-006/016/019 API: actual reviewer identity/usage admission, normal charging of all recorded provider usage, replay/stale/forged receipt rejection, and real PostgreSQL guest/token-policy settlement, read/source/Lean and retirement tests. PostgreSQL accounting tests use explicitly synthetic provider receipts; the separate real-provider experiment does not establish live paid settlement.
- [x] Adversarial scope tests: changed exponent domain, degree/radian, dependent quantifiers, missing premises, different limit sidedness, method restrictions, false-proof versus truth-question polarity, answer/source mutation, incomplete catalog and incompatible conventions. Unit/contract, real PostgreSQL and actual-provider evidence retain their separate scopes.
- [x] Signed software deployment: sequence 12, API `7cde967` and worker `7c000db`; actual seven-container/private-TLS readiness, unchanged 35-step DB contract/catalogs, public routing restoration and HTTP health, with temporary verification authority absent.
- [ ] Semantic-path concurrent-request and retirement-during-settlement runtime witness beyond the existing lock/revalidation tests; do not infer 30-user behavior from single-request tests.
- [ ] Canonical-answer revision 2 for right-limit/discontinuity and the pi bound: complete fresh compilation/admission reconciliation, independent review, signature, atomic publication and read-only historical/source validation. Candidate preparation and attempted compilation are not publication evidence.
- [ ] Re-evaluate the unchanged 32-question corpus after any published answer revisions; equivalent-input acceptance of 13/13 has not been achieved by the recorded 11/13 run.
- [ ] Signed deployment and changed-question public witnesses across at least three substantive Recipes: multiple new paraphrases, exact stored source/answer, both real reviewer calls, zero new Lean jobs and each accepted measured answer within ten seconds. Record failures and remaining limits without extrapolating general completeness or 30-user latency.

Evidence: [actual-provider results, sequence-12 deployment and remaining gates](../../docs/aws-recipe-semantic-benchmark-2026-11-02.md). Independent API/worker review, cross-repository producer/consumer validation and real PostgreSQL tests establish the implementation boundaries above; they do not establish public changed-question latency, complete mathematical coverage or successful revision-2 publication.
