# Identifier kind select chevron spacing (2026-11-18)

- Target: interface visual correctness. Mathematical answer success, generation
  time and model cost were not measured.
- Hypothesis: the existing shared chevron spacing rules omit the bare select in
  the complete-identifier fieldset. Extending their selectors should correct its
  spacing while preserving native selection.
- Change: [#427](https://github.com/AtsushiHosaka/pals/issues/427),
  [Web #91](https://github.com/AtsushiHosaka/pals-webfront/pull/91), commit
  `db6acf0`, and [parent #428](https://github.com/AtsushiHosaka/pals/pull/428).
  The three existing chevron rules now include the identifier-kind select.
- Conditions: local macOS Chromium and actual source CSS in an isolated HTML
  fixture, with the same fieldset, bare select and Japanese options. Two viewport
  cases, 1024px and 375px, were measured. The two options are repeated samples
  within each case, not independent trials.
- Result: visible chevron edge inset increased from 5px to 17px in both viewport
  cases. Both baseline cases failed the 10px minimum; both corrected cases passed.
  Corrected vertical-center error is 0.5px. The full appearance suite passed all
  eight checks; the account settings suite passed 18 checks. An independent diff
  review found no actionable issues. After installing the exact locked dependencies,
  TypeScript, full ESLint and the production build passed. The first CI run failed
  an existing upload story during its default one-second asynchronous wait; its
  four targeted cases passed locally. One unchanged-source CI rerun was requested.
- Decision: submit the correction for review and normal release. No deployment
  or account-setting write was performed.
- Limits: isolated CSS/browser checks do not establish authenticated production
  rendering or physical Safari/iPhone behavior. Japanese popup keyboard selection
  was not verified; selection and Tab focus navigation were checked separately.
- Next: complete review and the normal authorized release, then verify production
  rendering.
- Evidence: [measurement report](../../identifier-select-chevron-2026-11-18.md),
  ledger IDs `2026-11-18-identifier-chevron-baseline` and
  `2026-11-18-identifier-chevron-corrected`.
