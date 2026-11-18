# Identifier kind dropdown chevron — 2026-11-18

Owner: Codex. Tracking: [#427](https://github.com/AtsushiHosaka/pals/issues/427).
Session: [Codex chat](codex://threads/01a1ed09-2b3d-76c3-91c4-92efa30bdecc).

The supplied screenshot shows the native arrow beside the right border of the
identifier-kind dropdown under 「完全な識別子を追加」. The existing settings
arrow rules matched only `select.field-control`; this select has no such class.

Starting Web source: `c585c60c31e5b45c4615babaf7e7b7273ff8790b`, freshly fetched
from the approved `codex/sidebar-inline-math-20261031` branch. Corrected Web source:
`db6acf0`. Parent documentation starts from `922aca6`. The old parent checkout's
Web pin was unavailable remotely; no existing checkout changes were overwritten.

The three shared arrow selectors now also match `.notation-identifier-add select`.
The existing SVG, right inset, vertical center, RTL placement and forced-colors
native fallback are reused. The component, options, handlers and persistence code
are unchanged. Listboxes and multiple selects remain excluded. The parent gitlink
also includes preceding approved Web branch changes; this report validates only
the two-file chevron patch, not those preceding changes or a release candidate.

## Local browser measurement

The existing Playwright appearance suite renders the actual source stylesheet and
an isolated HTML fixture with the same fieldset, bare select and Japanese options.
Actual dark arrow pixels are sampled separately from text and borders. The minimum
outer-edge inset is 10px; allowed vertical-center error is 3px.

| Viewport | Before | After | Vertical-center error after |
| --- | --- | --- | --- |
| 1024 × 812 | 5px inset, FAIL | 17px inset, PASS | 0.5px |
| 375 × 812 | 5px inset, FAIL | 17px inset, PASS | 0.5px |

Both new viewport regressions failed on the starting CSS and passed after the fix.
Afterward both 「変数」 and 「関数」 have the same inset and center, in a 40px control.
Each viewport is one measured case; option samples are not independent trials.
The mobile screenshot was also inspected visually with no clipped arrow or overflow.

## Verification and limits

- `npm run test:appearance`: 8 passed. Includes existing language arrows, size/RTL,
  forced colors, disabled controls, native typeahead, listboxes, identifier selection
  and Tab focus navigation.
- `vitest run tests/unit/account-output-language-settings.test.tsx`: 18 passed.
- ESLint for the changed test and `git diff --check`: passed.
- Independent read-only diff review: no actionable findings.
- TypeScript was attempted but did not pass: reused local dependencies lack
  `mathlive`, causing missing-module and associated implicit-any diagnostics in
  unchanged `RichMathInput.tsx`. This is not recorded as a successful typecheck.

The first sandboxed browser attempt could not launch Chromium; the actual baseline
was subsequently measured outside that sandbox. Early test harness attempts used
an exact English label containing option text and macOS OS-owned popup key events;
those harness errors were corrected. Japanese option selection and Tab focus are
verified separately; Japanese popup keyboard selection is not claimed.

Local, untracked evidence: `/tmp/pals-427-baseline.json` and Web
`output/playwright/select-appearance-results.json`, plus appearance screenshots.
Dependencies were reused from an existing checkout. No API, model, account-setting
write or deployment was performed. Authenticated production rendering and physical
Safari/iPhone behavior remain unverified until the normal reviewed release.
