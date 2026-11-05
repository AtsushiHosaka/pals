# Settings dialog layout repair — 2026-11-05

Owner: Codex. [Issue #265](https://github.com/AtsushiHosaka/pals/issues/265).
[Session](codex://threads/01a1aac0-d36c-7331-9a73-a79dc78d1a0a).

The owner reported touching controls and action buttons in General settings.
The working contract is to repair spacing and narrow-screen layout while preserving
all settings, navigation, validation, and persistence. This is a visual repair,
not a change to the unresolved language-policy decision in #229.

## Implementation

Baseline frontend: `41b3d1c` (the source line used for the current shared-card
release). Repair: [Web PR #49](https://github.com/AtsushiHosaka/pals-webfront/pull/49), `9332a04`. Only `app/globals.css` and
`components/AccountOutputLanguageSettings.tsx` change.

- General settings and forms now have explicit grid gaps. Heading/help pairs use
  a smaller, consistent gap; form controls and action buttons no longer touch.
- Notation fields and buttons share a 40px minimum height.
- At widths up to 760px, the identifier-add button moves to its own row. Action
  buttons and settings navigation can wrap. Fields retain a usable input column.
- Settings notices fill the content column and wrap long identifiers and retry
  actions. Help text uses the existing darker muted text color.

No control, handler, API resource, setting, or user-facing entry point is removed.
Independent source review found and corrected a notice selector that did not
match the actual component, then found no further actionable defect in this diff.

## Browser evidence and its boundary

The owner explicitly approved a **local preview with sample settings** in this
session. A temporary page rendered the real settings component and stylesheet
with six sample notation symbols, supplied notation state, and a temporary
output-language hook. No authenticated API calls or account writes were used.
The sample save/refresh callbacks prove only preview rendering and interaction,
not real persistence or backend recovery.

Chrome on local macOS was reused. Before measurements used the original component
and CSS at `41b3d1c`, with the same sample data as the repaired measurements.
An action gap is the distance from the last control group to the first action
button. A matched case passes when both forms have at least 16px separation and
the dialog/forms have no horizontal overflow.

| Japanese viewport | Before: language / notation gap | After: language / notation gap | Horizontal overflow after |
|---|---|---|---|
| 1280 × 900 | 0px / 0px | 20px / 20px | none |
| 375 × 812 | 0px / 0px | 20px / 20px | none |

The matched original cases pass 0/2; the repaired cases pass 2/2. Eight additional
ready-state cases pass: Japanese at 320, 640, and 760px, and English at 320, 375,
640, 760, and 1280px. Together the ten repaired cases have 20px action separation
in both forms and no dialog/form horizontal overflow. These are fixed local
layout cases, not a general product or mathematical success rate.

Four further Japanese cases at 320 × 812 pass their layout checks:

1. A 64-character identifier and collision notice wrap without overflow; invalid
   notation leaves Save disabled.
2. The sample error notice and retry action fit. The dialog-scoped error disappears
   after the sample retry callback. A page-wide empty framework announcement is
   separate and was not counted as a settings error.
3. The loading state fits, leaves Close available, and disables notation saving.
4. The saving state fits, disables notation editing/add/save, and leaves Close available.

Local evidence is retained under frontend `output/playwright/settings-layout-20261105/`:
`baseline.json`, `after.json`, `collision.json`, `states.json`, and before/after
desktop/phone screenshots. Generated preview captures are not committed.

Actual browser zoom is **not verified**: attempted shortcuts left the measured
viewport and device-pixel ratio unchanged. Narrow viewport coverage is not
reported as a successful zoom test. An additional keyboard attempt after stopping
the temporary server could not reach the preview; it is not runtime focus evidence.

## Source checks and cleanup

Node 24.15.0; locked frontend dependencies; Next.js 16.4.3.

- Six targeted Vitest files pass, 69 tests: account-output-language-settings,
  modal-accessibility, math-conventions, billing-settings, notation-preferences,
  and use-account-notation-preferences. From the frontend repository:

  ```sh
  node node_modules/vitest/vitest.mjs run --configLoader native \
    tests/unit/account-output-language-settings.test.tsx \
    tests/unit/modal-accessibility.test.tsx \
    tests/unit/math-conventions.test.tsx \
    tests/unit/billing-settings.test.tsx \
    tests/unit/notation-preferences.test.ts \
    tests/unit/use-account-notation-preferences.test.tsx
  ```

- `npm run typecheck`, ESLint on the changed TSX, and `git diff --check` pass.
- The normal Turbopack `npm run build` passes TypeScript and generates 15 static
  pages after the temporary preview is removed. The first build found stale
  generated development types referring to that removed preview; removing this
  task's `.next/dev` directory resolves it. No source check is weakened.

The first dependency-reuse attempt could not validate this source because its
shared installation lacked `mathlive`. The shared installation was left intact;
the lockfile was installed in this isolated worktree instead. The native Vitest
config loader also avoids writing configuration cache into shared dependencies.

The preview server is stopped. The temporary route is removed, and the original
language hook and Next configuration are restored byte-for-byte. The final source
diff contains only the two implementation files above. Browser viewport overrides
are reset. No container, account, model call, paid operation, or deployment is involved.

Local visual repair and targeted source checks are complete. Authenticated
backend persistence, real API failure/retry, production rendering, actual browser
zoom, and deployment remain unverified. The existing unit suite separately covers
account settings behavior and modal focus; it does not establish production E2E.
