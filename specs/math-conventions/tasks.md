# Math conventions — tasks

Items are checked only with executed evidence.

- [ ] MCV-001/009 API: catalog module (11 items, 4 languages); appended `math-conventions` release step with fresh-install, idempotence and drift tests on real PostgreSQL; local legacy release registration; serving readiness gate.
- [ ] MCV-002 API: `GET`/`PUT /v1/auth/me/math-conventions`; owner isolation; guest owners rejected; unavailable before release.
- [ ] MCV-003/004/008 API: claim `math_conventions`; convention question validation and catalog copy; answer mapping (once / always / deny / free text) in one transaction; applied-convention settlement validation; public `conventions` and `question.convention_id`; real PostgreSQL tests.
- [ ] MCV-003/005/007 agent: `premise_check.conventions`; known readings in the prompt; convention question before the counterexample check; applied conventions in the settlement; unchanged behavior without `math_conventions`; unit tests and real-provider cases.
- [ ] MCV-002/006 webfront: settings section with all items; question hint and settings link; "この回答の前提" in project, projectless and guest threads; four languages; phone/tablet/PC.
- [ ] Real local journey: zero-ring question asked once; once / always / deny behavior; settings change used by the next request; guest shows the default reading.
- [ ] Production: add `math-conventions` to the production registry and Mac update with the strict production checks (needs separate approval).
