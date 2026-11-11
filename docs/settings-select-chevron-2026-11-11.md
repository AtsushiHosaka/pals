# Settings dropdown chevron spacing — 2026-11-11

Owner: Codex. Tracking: [#339](https://github.com/AtsushiHosaka/pals/issues/339).
Session: [Codex chat](codex://threads/01a1c86d-afb9-7d32-97d1-fe951860b7fe).

## Scope and source

The owner's settings screenshot showed the interface-language and answer-language
dropdown chevrons almost touching the right border. Both controls are native HTML
selects with the shared `.field-control` style. The Web uses custom React primitives,
plain CSS and Lucide icons; it does not depend on a component-system package.

Starting Web source: `272b8af06999f59be146ae6e2b61050901f9ed7c`, freshly checked
against `codex/sidebar-inline-math-20261031`. The existing active checkout was old
and dirty, so this change used an isolated source worktree. Existing work was preserved.

Corrected Web commit: `29fc6d992dbdce189e9b1a925d80ff966fcf050e`, pushed before
updating the parent gitlink. Review:
[Web #68](https://github.com/AtsushiHosaka/pals-webfront/pull/68), targeting the
same approved production source branch. The independent final review found no
actionable issue; GitHub CI and production release remain separate gates.

The fix replaces only single-line selects' browser-drawn decoration with a 16px SVG
in a 12px inset background box, centered vertically. A 40px end padding reserves
space for selected text. RTL controls put the chevron on the left. Native selects,
options, labels, event handlers, disabled semantics and persistence behavior remain.
Listboxes and multiple selects retain their browser presentation. Forced colors
restores the system arrow and its original padding.

## Local visual measurement

Actual source CSS was rendered in Chromium on local macOS at a device scale factor
of 1. The browser regression samples dark pixels in the indicator area, excluding
the border and text region. It requires a visible chevron at least 10px from the
outer edge, with its vertical center within 3px of the control's center.

| Viewport | Starting source | Corrected source | Result |
| --- | --- | --- | --- |
| 1024 × 812 | 5px visible-pixel right inset | 17px visible-pixel right inset | FAIL → PASS |
| 375 × 812 | 5px visible-pixel right inset | 17px visible-pixel right inset | FAIL → PASS |

The corrected short and long selected labels both pass without horizontal page
overflow. The glyph center is 19.5px in a 40px control, a 0.5px center error.
Explicit `size=0` and `size=1`, in both LTR and RTL, give the same 17px edge inset.
The 17px pixel measurement includes the SVG's internal whitespace and control
border; it is distinct from the 12px background-box inset.

The original two visual assertions failed before the production stylesheet was
changed. A separate initial keyboard harness assumed a native popup-opening
sequence that did not work in headless macOS. It was replaced with native keyboard
typeahead and Tab; that harness failure is not classified as a product failure.

## Verification

- `npm run test:appearance`: five browser checks passed. Coverage includes desktop
  and phone-width appearance, long values, explicit dropdown sizes, RTL, native
  keyboard typeahead, disabled controls, listboxes, multiple selection and forced
  colors. This suite is now part of `web-regression` CI.
- Existing settings and billing checks: 41 passed.
- Full Web regression suite: 152 files, 2,056 tests passed.
- TypeScript, ESLint and `git diff --check` passed.
- Production build passed with the repository's declared CI configuration. The
  first build lacked the required API-base configuration and was not counted as
  successful; the configured rerun completed.
- Separate visual inspection of Japanese-language local previews at desktop and
  375px width confirmed aligned chevrons, readable labels and no clipped controls.

Local artifacts, excluded from Git: `output/playwright/select-before.png`,
`select-after.png`, `select-after-mobile.png`, `select-appearance-baseline.json`,
`select-appearance-results.json`, and the appearance runner's screenshots/traces.
The JSON report includes eight final pixel samples. These are internal samples
within the visual comparison, not eight independent product trials.

## Limits and follow-up

These are isolated browser/CSS measurements, not authenticated production settings
acceptance. No account setting was saved and no deployment occurred. Physical
phones and Safari were not tested. Production rendering remains unverified until
the reviewed fix is released through the normal process.

The older spacing repair [#265](https://github.com/AtsushiHosaka/pals/issues/265)
is closed. Mobile focus restoration
[#285](https://github.com/AtsushiHosaka/pals/issues/285) and the older mathematics
settings loading report [#12](https://github.com/AtsushiHosaka/pals/issues/12) are
separate open issues. No existing toggle/chevron redesign issue was found.

The quality ledger records only the two viewport measurements before and after
this change. Unit-test and CI pass counts are not entered as product measurements.
