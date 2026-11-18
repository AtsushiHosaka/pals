# Figure rendering and production readiness — 2026-11-18

Tracking: [#318](https://github.com/AtsushiHosaka/pals/issues/318).
Owner: [Codex chat](codex://threads/01a1ed09-2b3d-76c3-91c4-92efa30bdecc).
The owner explicitly requested resumption and production integration in coordination
chat `01a1ed35-9cde-7fe0-8c9d-b7d017703443`. The sole live release owner remains
`01a1ebe7-a4ee-78c0-ab22-a16cfcccc3d2`, through #433 recovery and #425 release.

## Why the old issue did not establish the current state

The last #318 update, on November 14, described shared release-controller failures
after figure source integration. It did not contain the subsequent live figure
acceptance or a current runtime readback. The figure source PRs were already merged:
API #95 at `430aa198`, Web #64 at `c4593de8`, and worker #89 followed by its regression
qualification. Treating all figure source as still absent would be incorrect.

The release owner identified the saved admitted manifest with SHA-256
`1be72c60b705328c30b61c198fa037f6b6ef14dfd0f9ed92aa118914bf543f15`.
Reading the exact saved bytes reproduced that hash and these source pins:

| Role | Saved manifest | New UI candidate inspected |
| --- | --- | --- |
| API | `4868a504fc6f20211742377b80e40ac27a88464c` | `a3191b4cd11a347724bbabff54e39c829faca31e` |
| Web | `86c946b34ebb14fa9b0f8742d6de2d17ab55aa70` | `aa1a6d48ceeb90f79c5360e5f699e72d11735f56` |
| Worker | `146ecf2b816ac6830940fac824bd9e8df90d80e4` | same |

The API figure validator, registry, registry lookup and final-answer propagation
are unchanged across those API pins. The Web figure component/parser/layouts are
unchanged across those Web pins. This is saved manifest and source evidence;
fresh deployment/schema/flag readback remains **NOT VERIFIED** here.

## Source findings

- Worker `explanations.py`, `chat_runtime.py` and `worker.py` generate, validate,
  independently review and publish the declarative figure and paragraph bindings.
  An invalid or unsupported figure is discarded without certifying it as a proof.
- API `proof_request_lean.py` propagates accepted explanation figures to the answer;
  its PostgreSQL serialization preserves the figure and bindings. Guest and history
  paths retain the answer payload. No separate figure-enablement flag was found.
- API `recipe_figures.py` alone attaches catalog figures by Recipe ID plus the
  exact answer-text digest. The shipped registry has 35 entries, all geometry.
  Polynomial graph templates are supported by generated explanations, not by any
  current registry row. A catalog answer without a matching row receives no figure.
- The API registry intentionally differs from the worker's older generated JSON
  in 27 answer digests: API commit `e27a1ca` rebound paragraph-separated answers.
  Copying the stale worker file would undo that fix. Actual matching against the
  currently admitted catalog text has been requested as a limited read-only check.
- Web renders `AnswerFigure` inline in both `ProofRequestThread` and `GuestChat`.
  There are 11 geometry template names and two polynomial graph template names
  (degree at most seven). Arbitrary university diagrams, transcendental graphs and
  a dedicated Simson-line layout are not implemented by this closed catalog.
  The existing specification excludes commutative diagrams from this component.
  The inspected answer contract carries one figure call. The four-renderer check
  below proves coexistence across answer blocks, not multiple calls in one answer.

## Added real-browser coverage

[Web #92](https://github.com/AtsushiHosaka/pals-webfront/pull/92), commit
`8d807a74e324862e8df8a9994dbba9da8a9e7a68`, adds a Chromium check to the existing
`web-regression` workflow. It renders the real `AnswerFigure`, its complete module
CSS and the complete application stylesheet. Its declarative inputs and explanatory
text are explicit local fixtures, not saved user answers or provider responses.

At 1024px and 375px it checks a cubic derivative illustration for Rolle's theorem,
equal inscribed angles and a cubic graph. A fourth tangent-length figure verifies
simultaneous display. An unsupported call must remove only its figure, retaining
the explanatory text and neighboring source action. Checks inspect actual SVG
primitives, accessible titles, label bounding boxes, answer-before-figure placement
and horizontal overflow. One browser/page is reused and closed in `finally`.

| Viewport | Three required categories | Figure width | Smallest graph label height | Geometry label height |
| --- | --- | --- | --- | --- |
| 1024px | 3/3 rendered within frame | 460px | 16px | 21px |
| 375px | 3/3 rendered within frame | 335px | 11px | 15px |

All four answer-block figures coexist at both widths; invalid-call fallback retains the text
and source action. Mobile screenshot inspection also found no clipped labels or
page overflow. The quality ledger records only the six category/viewport checks;
the fourth figure and invalid-call assertions are supplementary, not extra trials.

Executed checks:

- `vitest run --config tests/browser/answer-figure.config.ts`: one browser check
  passed, with eight rendered samples and invalid-call assertions at both widths.
- `vitest run tests/unit/answer-figure.test.tsx`: 73 passed.
- `npm run typecheck`, full ESLint and `git diff --check`: passed.
- API `test_figure_calls.py` and `test_recipe_figures.py`: 64 passed using the
  inspected API source and a temporary dependency environment. These are unit and
  serializer/registry checks, not a real-database acceptance journey.
- Worker figure/catalog/explanation-selected tests passed after installing PyYAML
  in a temporary environment; the earlier dependency-related catalog skip was
  resolved. Provider responses in existing unit tests remain test doubles.
- Independent review found one fixture label omission (center O); the text was
  corrected and the browser/lint checks rerun successfully.

Local untracked evidence is under Web `output/playwright/figures318/`:
`answers-1024px.png`, `answers-375px.png`, and `layout.json`. SSR checks the visible
initial frame, not hydration, playback or clipboard operations in a real browser.
Existing unit tests cover those component interactions at their declared boundary.

## Remaining acceptance and handoff

No model call, new proof submission, AWS/SSM mutation, DB write or service restart
was performed by this task. The existing budget ledger and release owner are
unchanged. UI #425 need not wait for every other feature's acceptance.

1. The sole live owner performs the required fresh readback under its approved
   access: exact running source/image bindings and current admitted catalog digest
   matches for the 35 registry rows. Keep raw text, credentials and user data private;
   report only counts and missing Recipe IDs. Missing access stays NOT VERIFIED.
2. If an existing approved test request already contains a non-null visualization,
   read that same request and history without submitting another proof. Compare the
   figure and bindings before and after reload in authenticated and guest contexts
   where the existing authorized records permit it.
3. For geometry, use a registered inscribed-angle or tangent-secant answer whose
   actual saved text digest matches. For university analysis and a graph, use a
   generated polynomial-derivative or polynomial answer with explicit function,
   domain and assumptions. An arbitrary abstract theorem is not evidence for these
   templates. Do not manufacture or inject a figure into a live stored answer.
4. Capture the three real production categories at desktop and 375px as available,
   preserving answer text, Lean/source controls and reload/history. If a new paid
   request is required, allocate it through the live owner's existing authorization;
   this report does not authorize three additional calls or expand the shared budget.
5. Real PostgreSQL completion-to-answer-to-HTTP retrieval with figure/bindings is
   not covered by an integration regression today. Static paths and serializer
   tests do not establish that durable boundary; record the actual live result or
   add a separately isolated real-DB regression before claiming it verified.

Until those observations are available, #318 remains open: source and local
rendering are verified at the stated boundaries; production figure acceptance is
**NOT VERIFIED**. The blocking release recovery is tracked separately in #433.

## Closed readback helper follow-up

At the sole live owner's request, `pals-scripts/figure-readback.py` and its eleven
pure policy/aggregation tests were added. The [readback runbook](figure-readback-runbook-2026-11-18.md)
defines its fixed registry hash, 35 IDs, current toolchain/Japanese scope, two
read-only transactions, closed output and external timeout/source-image bindings.
It has not queried a database or production. Independent review caught the
initial guard treating the API's permanent `module` counters as an existing pool;
the corrected guard and its regression passed. These source tests are not entered
as product measurements or used to claim the pending live acceptance.

Web #92 has passed its exact-source CI and reviews and was merged at `5e2fab4a`.
