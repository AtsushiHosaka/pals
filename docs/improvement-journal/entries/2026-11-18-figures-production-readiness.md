# Figure source and browser readiness (2026-11-18)

- Target: visible figure correctness and honest release readiness. No answer-time,
  mathematical-success or model-cost improvement was measured.
- Hypothesis: the old #318 issue conflates integrated figure code with unresolved
  shared release recovery; current source and real browser evidence can separate them.
- Change: Web #92 adds real Chromium checks for the existing figure renderer and
  includes them in canonical web-regression. No production component behavior changes.
- Conditions: exact source aa1a6d48 plus test commit 8d807a7; actual source CSS,
  explicit local declarative-call inputs, three categories at 1024px and 375px.
- Result: six category/viewport measurements passed. Figure widths are 460px and
  335px; graph-label heights are at least 16px and 11px respectively. Four simultaneous
  figures and invalid-call isolation also passed, without counting them as new trials.
- Decision: retain the browser regression and continue the sole live owner's current
  release. Saved manifest/source already include the figure paths, so do not replace
  approved source with old main or enable an invented feature flag.
- Cost: no paid model calls or additional production submissions.
- Limits: renderer SSR does not prove generated figures, hydration, real-DB/HTTP
  persistence or production. Live catalog-digest matches and three production
  categories remain unverified; shared release recovery is #433.
- Evidence: [readiness report](../../figures-production-readiness-2026-11-18.md),
  [#318](https://github.com/AtsushiHosaka/pals/issues/318),
  [Web #92](https://github.com/AtsushiHosaka/pals-webfront/pull/92),
  ledger ID `2026-11-18-figure-source-browser-layout`.

Follow-up: the live owner requested a closed aggregate readback helper. Eleven
pure policy tests passed after correcting the permanent module-counter pool guard.
It remains unexecuted against a database or API runtime; these are not new product
measurement rows. Web #92 passed exact CI and review and merged at `5e2fab4a`.
