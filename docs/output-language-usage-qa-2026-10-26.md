# Output-language and usage-display correction — 2026-10-26

Production walkthrough exposed an actual inconsistency: the loaded account output
preference was English, while newly generated PDF/PNG answers were Japanese. The
search result also labeled the PDF chat English. This was not accepted as a pass.
The prior language selector intentionally preferred detected question language;
that behavior has now been superseded by the user's output-setting requirement.

## Changes

- New authenticated questions, direct jobs, existing-chat messages, material
  confirmation revisions and explanation follow-ups use the current account output
  language. Explicit language requests can override it. Guests use their selected
  language. Queued work, ordinary retries and saved answers retain their snapshot.
- The shared usage panel omits reservation balances and provider-cost conversion
  details in all four interface languages. Used/remaining allowance, limits,
  renewal dates, plan information and billing actions remain available.
- Account sidebars no longer display an authentication-provider name when email
  is absent. The output-language hint describes the corrected behavior.

## Verification

- API: the initial combined suite passed 304 tests. After preserving explicit
  language instructions across premise confirmations, the final affected suite
  passed 147 tests, including 33 real disposable PostgreSQL request/guest tests,
  current-preference changes, Japanese input with English selected, existing chats,
  follow-ups, explicit/negated/quoted/ambiguous directives and retry snapshots.
  Ruff, targeted mypy and diff checks passed. The temporary database was removed.
- Frontend: 1,691 tests across 138 files passed; all four locales reject internal
  reservation/conversion copy. Typecheck, affected ESLint and diff checks passed.
- Real provider: the fixed selector resolved `en` for
  `上限と最大値の定義の違いを説明してください。`; actual ChatRuntime classification,
  generation and independent review returned an approved English explanation.
  Japanese appeared only as the glossary labels `(上限)` and `(最大値)`, with no
  Japanese sentences. This tested local selector/runtime/provider behavior,
  not HTTP, browser integration or deployment. No Lean/catalog source was sent.
- Production PDF result: domain-relative limit 0, distinct from f(0)=1, with
  epsilon-delta explanation and generated Lean source visible.
- Production PNG result: exactly -2 and 3, all three intervals covered and both
  values substituted back; the private share preview marked the answer Lean verified.
  These production answers predate the language fix and therefore remain evidence
  of the language defect rather than of its correction.

## Review and release status

- API: https://github.com/AtsushiHosaka/pals-api/pull/24
- Frontend: https://github.com/AtsushiHosaka/pals-webfront/pull/24
- Parent: https://github.com/AtsushiHosaka/pals/pull/114

No merge or deployment occurred. Corrected production/browser behavior is not yet
verified. Merge child repositories first, then update the parent pin and release.
The earlier production catalog publication remains pending under the constraints
recorded in `math-request-repair-2026-10-26.md`.

## Recording evidence

Local media and test response artifacts are deliberately untracked. The valid
production footage contains guest questions, a completed conceptual answer,
PDF/PNG attachments and previews, the new completed PDF/PNG solutions, Lean source,
share preview, settings and chat search. Login is excluded. The footage explicitly
labels the production language defect and predates these fixes.

Project creation and persistent PDF processing succeeded in the real UI, but their
native recordings were black while Chrome was not visible to macOS capture. Those
files were rejected. The recording must not be represented as complete coverage
of every feature or as a successful end-to-end recording of project creation.
