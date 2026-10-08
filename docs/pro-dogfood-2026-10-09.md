# Public Pro dogfood — 2026-10-09

The approved account is active on permanent complimentary Pro. Project creation, chat submission, saved conversations, search, output-language preferences and notation preferences work in this run. Full runtime QA remains **partial**: Mathematics settings and sharing preview fail, the formal-proof retry fails, and upload/OCR/model-switch controls are unavailable on the tested surfaces.

## Run

- ID: `20261008-pro-resume-2353`; mode: authenticated exploratory runtime QA.
- Target: `https://palschat.site`, the public PALS deployment hosted on Mac mini. Browser client: existing local Chrome tab controlled through `cua_repl`; no remote Mini desktop session was used.
- Live revision: unknown; no implementation-source inspection, repair or deployment performed.
- Actor: approved permanent complimentary Pro test account. Credentials and account identifiers omitted from this note.
- Time: 2026-10-08 23:54–2026-10-09 00:18 JST (UTC journal timestamps).
- Budget: bounded desktop pass, one safe Retry for each failed selected flow; two initial/retry attempts where stated below. Normal viewport 1401 × 812; no fresh mobile or assistive-technology audit.
- Authorization: synthetic Projects, chats, proof requests, uploads and QA preferences. No payment, public publication, destructive deletion or credential changes.
- Evidence directory: local ignored `outputs/dogfood/20261008-pro-resume-2353/`; paths below are relative to that directory. Raw account screenshots remain local. Recording unsupported by the available driver; no videos claimed.
- Independent reviewer assessed the three delivered mathematical answers using saved DOM and screenshots, without sharing browser ownership.

## Coverage

All rows use the same Pro actor. “Completed” describes the exercised slice, not certification of the entire feature.

| Area / starting state | Coverage | Actual outcome | Evidence / limit |
|---|---|---|---|
| Existing authenticated session | completed | Session retained across repeated full reloads; UI says complimentary Pro, no expiry, no charges | `qa/01-pro-active.png`, `qa/41-pro-usage-final.png`; fresh login/signup not visited |
| Usage, initially 0 used / 0 reserved / 3M available | completed | First delivered Project answer: 2,643 used. Final: 10,526 used / 0 reserved / 2,989,474 available; total remains 3M | `qa/02-pro-budget-before.png`, `qa/21-pro-usage-after-project.png`, `qa/41-pro-usage-final.png`; aggregate consistency only |
| Project creation from two-step dialog | completed | Blank-name validation; exact synthetic name/description saved and retained after reload | `qa/12-project-name-validation.png`, `qa/13-project-created.png`, `qa/14-new-project-reloaded.png` |
| Project list/search | completed | Matching query narrows list; nonexistent query gives empty state; clear restores list | `qa/15-project-search-match.png`, `qa/16-project-search-empty.png` |
| Existing Project chat, empty before submission | completed | Strict-monotonicity proof accepted, correct English answer delivered, persisted after navigation/reload | `qa/17-project-proof-answer.png`, `qa/18-project-answer-reloaded.png`, `review/project-proof-review.md` |
| New chat buttons | completed | Standalone empty chat and chat inside the new Project created; Project membership retained after reload | `qa/24-new-standalone-chat.png`, `qa/37-new-project-chat.png`, `qa/38-new-project-chat-reloaded.png` |
| Home proof | partial | Accepted; first result review-rejected; one Retry delivered correct compactness proof, retained after reload | `qa/29-home-review-rejected.png`, `qa/32-home-proof-recovered.png`, `qa/33-home-answer-reloaded.png`, `review/home-proof-and-formal-review.md` |
| Project follow-up / clarification | partial | Asked to restate visible prior theorem. Restatement accepted; correct Japanese counterexample delivered and all turns persisted | `qa/project-followup-clarification-dom.txt`, `qa/45-japanese-followup-visible.png`, `qa/47-context-clarification-visible.png`, `qa/project-followup-reloaded-dom.txt`, `review/project-followup-review.md` |
| Chat search | completed | Finds both fresh Home/Project proof chats; no-match message; Escape dismisses and returns focus to trigger | `qa/35-chat-search-match.png`, `qa/36-chat-search-empty.png` |
| General output language | completed | Japanese default saved and survived reload; original English default restored and verified | `qa/07-output-language-persisted.png`, `qa/42-output-English-restored.png` |
| Interface language / static notation | completed | English UI and synthetic `+` replacement persisted; replacement rendered in saved math. Original Japanese UI and empty notation restored after reload | `qa/43-ui-English-notation-saved.png`, `qa/44-notation-preference-reloaded.png`, `qa/notation-render-dom.txt`, `qa/final-chat-dom.txt`; identifier additions not visited |
| Mathematics settings | blocked | Initial open and Retry fail; save/reload inaccessible | `qa/03-math-settings-error.png`, `qa/04-math-settings-retry.png` |
| Sharing preview for delivered Project answer | blocked | Initial open and Retry fail | `qa/19-share-preview-error.png`, `qa/20-share-preview-retry.png`; publication/view/revocation not exercised |
| Formal Lean request, historical failed coprime-divisibility chat | partial | One fresh Pro Retry accepted then generic terminal failure. Lean source disabled; no compiler receipt | `qa/23-formal-retry-preparing.png`, `qa/28-formal-retry-failed.png`, `qa/formal-after-retry-dom.txt` |
| PDF / PNG uploads, materials, OCR | blocked | No attachment/material/OCR control on settled Home, Project overview or Project chat; zero DOM file inputs on Home/chat | `qa/08-project-chat-no-upload.png`, `qa/14-new-project-reloaded.png`, `qa/25-pro-home-no-upload.png`, `qa/project-chat-dom.txt`, `qa/home-dom.txt`; no upload/OCR request made |
| Model switching | blocked | No selector on the tested Pro surfaces or settings | Same screen/DOM evidence; model choice, persistence and entitlement boundaries unverified |
| Progress panel | partial | Opens; explanatory message visible, no live stage details or verification receipt | `qa/11-progress-panel.png`; cannot infer failed pipeline stage |
| Purchase, reset/exhaustion, account management, multiuser permissions | not visited | Complimentary Pro checkout disabled; no payment or destructive operations | Budget reset/exhaustion, per-request cap enforcement, isolated failure refunds, role isolation and logout/relogin unverified |

## Findings

Three observed failures (two reproduced on Retry), one intermittent rejection with recovery, and two UX observations. Causes are unverified; no common backend cause is asserted.

### ISSUE-001 — Mathematics settings cannot load

- Kind: bug; severity: high for Mathematics configuration QA; certainty: confirmed visible failure, reproduced 2/2 attempts.
- Location/precondition: authenticated Pro, account menu → Settings → Mathematics.
- Steps: open Mathematics; wait for terminal error; click Retry; wait again.
- Expected: settings become accessible for the requested configuration/save/reload test.
- Observed: “数学の設定を読み込めませんでした。” on both attempts. Configuration testing is blocked.
- Interpretation: load path fails; frontend/API/routing cause is unknown. Diagnose the failing response before choosing a repair.
- Evidence: `qa/03-math-settings-error.png`, `qa/04-math-settings-retry.png`; video unsupported.
- Resume condition: settings load with the same account, then save/reload can be exercised. No missing user information or new permission is needed.

### ISSUE-002 — Sharing preview fails for a completed proof

- Kind: bug; severity: high for sharing QA; certainty: confirmed visible failure, reproduced 2/2 attempts.
- Location/precondition: Project chat with freshly delivered, persisted strict-monotonicity answer.
- Steps: click Share; wait for result; click Retry.
- Expected: preview/settings load without publishing.
- Observed: “共有の操作を完了できませんでした。再試行してください。” both times; downstream share testing blocked.
- Interpretation: preview operation fails; cause unknown. Trace preview response and permission checks, then retest with the completed answer.
- Evidence: `qa/19-share-preview-error.png`, `qa/20-share-preview-retry.png`; video unsupported.
- Resume condition: working preview; public publication still requires scope appropriate to that action.

### ISSUE-003 — Accepted formal-proof Retry ends without a proof

- Kind: bug (observed core-flow failure, not a diagnosed compiler defect); severity: high for requested formal verification; certainty: confirmed terminal failure in one fresh attempt, repeatability unknown.
- Location/precondition: existing standalone coprime-divisibility request asks for complete Lean 4/mathlib proof and verification; prior failure present.
- Steps: Retry once under Pro; observe Preparing; revisit terminal result.
- Expected: requested formal artifact and verification result, or actionable failure diagnostics.
- Observed: “The proof could not be completed.” Lean source disabled, no compiler receipt. Historical baseline is not counted as another fresh attempt.
- Interpretation: formal verification is not established. Do not infer that compilation ran or which stage failed. Collect job-stage evidence and rerun this request after a verified repair.
- Evidence: `qa/23-formal-retry-preparing.png`, `qa/28-formal-retry-failed.png`, `qa/formal-after-retry-dom.txt`; video unsupported.

### ISSUE-004 — Home proof rejected once, Retry recovered

- Kind: bug/quality observation; severity: medium; certainty: intermittent, one rejection in two attempts.
- Steps: submit continuous-function uniform-continuity proof via Home; observe review rejection; Retry once.
- Observed: first result “The answer did not pass the required review. Please retry.” Retry delivered a mathematically correct English proof and persisted after reload.
- Interpretation: a user-visible failed attempt with a working recovery; rejected candidate and review rationale are unavailable, so a false-positive review cannot be concluded. Inspect review diagnostics if recurrence matters.
- Evidence: `qa/29-home-review-rejected.png`, `qa/32-home-proof-recovered.png`, `qa/33-home-answer-reloaded.png`, `review/home-proof-and-formal-review.md`; video unsupported.

### ISSUE-005 — Follow-up asks for a theorem already visible

- Kind: ux-observation; severity: medium; certainty: confirmed once, repeatability and cause unknown.
- Steps: after the strict-monotonicity proof, ask whether dropping endpoint continuity preserves “the theorem above,” requesting a counterexample.
- Expected: inferred conversation expectation—use the immediately preceding theorem.
- Observed: asks for the theorem's conclusion despite preceding exact theorem and answer in the same visible chat. Restating it recovers a correct Japanese counterexample.
- Interpretation: unnecessary clarification adds a turn; this does not prove a particular context-storage or model-routing defect. Verify history supplied to clarification before fixing.
- Evidence: `qa/project-followup-clarification-dom.txt`, `qa/46-followup-context-visible.png`, `qa/47-context-clarification-visible.png`, `qa/45-japanese-followup-visible.png`; video unsupported.

### ISSUE-006 — Clarification form labels use English in Japanese UI

- Kind: ux-observation; severity: low; certainty: confirmed in one clarification state.
- Observed: “Answer the question” and “Send answer” while the interface and clarification are Japanese. Normal Japanese labels return after submission.
- Expected: inferred consistency with selected Japanese interface language. Check translation selection for the clarification state.
- Evidence: `qa/project-followup-clarification-dom.txt` (full DOM); screenshot 34 shows the English input label but clips the question. Video unsupported.

## Boundaries and handoff

PDF/PNG/OCR and model switching remain required **blocked** coverage, not successful tests or proven backend defects. Access recovery checked Home, Project overview/chat, account settings and settled DOM; no hidden routes or APIs were guessed. Resume when the controls are exposed to this account, or when a specific intended UI entry point is supplied. That entry point is the only missing product-navigation information; no credentials need to be resent.

Budget arithmetic is consistent and reservations are zero after terminal jobs. Concurrent/retried work prevents isolating each unsuccessful job's charge; displayed refund policy alone is not verification of failure-refund semantics. Delivered answers pass independent mathematical review, which is separate from Lean compilation.

All synthetic artifacts were retained as evidence: one new Project, its empty Project chat, one standalone empty chat, the Home proof chat, and additional turns in an existing QA Project chat. Original preferences restored; no deletion performed. No active requests remain. Existing unrelated Git changes were preserved.

Raw journal, prompts, DOM and 47 screenshots are local; screenshot filenames 30/34/39/40 do not guarantee that the lower final answer is visible. For Japanese recovery use screenshot 45 and full saved DOM; screenshot 30 is not used as Preparing evidence. Console 404 query returned no captured errors and supplies no per-request network diagnosis. No overall application PASS is claimed.
