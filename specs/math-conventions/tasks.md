# Math conventions — tasks

Items are checked only with executed evidence.

- [x] MCV-001/009 API: catalog module (11 items, 4 languages); appended `math-conventions` release step with fresh-install, idempotence and drift tests on real PostgreSQL; local legacy release registration; serving readiness gate (api `eddc270`). Evidence: `docs/math-conventions-evidence-2026-10-05.md`.
- [x] MCV-002 API: `GET`/`PUT /v1/auth/me/math-conventions`; owner isolation; guest owners rejected; unavailable before release.
- [x] MCV-003/004/008 API: claim `math_conventions`; convention question validation and catalog copy; answer mapping (once / always / deny / free text) in one transaction; applied-convention settlement validation; public `conventions` and `question.convention_id`; real PostgreSQL tests (`test_math_conventions.py`, 9 passed).
- [x] MCV-003/005/007 agent: `premise_check.conventions`; known readings in the prompt; convention question before the counterexample check; applied conventions in the settlement; unchanged behavior without `math_conventions`; unit tests and real-provider cases (agent `d0840b5`; 29–30/31 with conventions, all five convention cases as expected). Evidence: `docs/math-conventions-evidence-2026-10-05.md`.
- [x] MCV-002/006 webfront: settings section with all items; question hint and settings link; "この回答の前提" in project, projectless and guest threads; four languages (webfront `c9a3961`, unit tests).
- [x] MCV-002/006 webfront: phone/tablet/PC check on the shared local stack; question layout fixed (webfront `7d8d690`). Evidence: `docs/math-conventions-evidence-2026-10-05.md`.
- [x] Real local journey: zero-ring question asked once; once / deny behavior and a repeated question after once; settings changes used by the next request; guests never asked and given the default reading (browser display covered by a component test because of the daily limit). Fixes found by the journey: agent `c175c5e`, `acbf707`, `9b4cff7`, `89d03d1`. Evidence: `docs/math-conventions-evidence-2026-10-05.md`.
- [ ] MCV-005 follow-up: when a reading makes the claim false, report the counterexample to the learner (today the request fails without an answer); part of the Lean-checked refutation step in PFR-014.
- [ ] Production: add `math-conventions` to the production registry and Mac update with the strict production checks (needs separate approval).
