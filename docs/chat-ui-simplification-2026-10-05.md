# Chat UI simplification — 2026-10-05

The user requested a simpler chat interface based on ChatGPT, removal of completed Lean badges and the large proof/source/follow-up action, removal of the “New proof” control, and settings accessed through the bottom-left account menu. This supersedes the previous UI arrangement; the proof verification policy remains unchanged.

## Reference evidence

The live [ChatGPT interface](https://chatgpt.com/) was visually inspected, including its bottom-left profile menu and Settings entry. The [UI Pocket web gallery](https://www.ui-pocket.com/web) was visually inspected. ChatGPT-specific UI Pocket material required login, so its individual screenshots were not inspected.

## Delivered behavior

Frontend commit: `5d6fbef` in `pals-webfront`, branch `codex/simplify-chat-ui`. [Frontend draft PR](https://github.com/AtsushiHosaka/pals-webfront/pull/2).

Completed answers show their text without a Lean badge or large combined action. Applied assumptions use a collapsed disclosure with provenance. Clarification choices remain next to the question, with a short notice when a choice is saved. Settings open through the account menu on desktop and the account menu within mobile navigation. The composer is capped at 760px and aligns with the conversation. Legacy-only proof archives keep their existing history selection without a “New proof” entry. Current request conversations omit that selector.

The existing topbar code icon opens verified Lean sources in the existing source panel. Older answers can be selected inside that panel, including when the latest answer has no source. Long chat names ellipsize so controls remain available on mobile. Source retrieval preserves job/chat/project binding, stale response suppression, aborts, and retry behavior. Verification progress and failures retain their existing meaning; no proof generation feature was added.

## Validation

Dependencies installed from the unchanged `package-lock.json` with `npm ci --ignore-scripts`. Production build, TypeScript, ESLint, and diff checks passed. Full Vitest result: 1,415 passed, 2 failed across 124 files. The final source-panel suite also passed all 27 tests. Both failures are in `tests/unit/use-proof-job-events.test.tsx` and reproduce on the unmodified base `e19606c`:

- Buffered event frames do not retain both server sequences as the test expects.
- A divergent buffered progression exposes an intermediate drafting state.

Desktop 1440×960 and mobile 390×844 browser checks used real production components with temporary display fixtures. Composer width, question choices, horizontal overflow, account-to-settings navigation, and uncaught page errors were checked. The temporary route was removed before the successful production build. This is UI evidence, not a live backend integration result.

Local screenshots remain in ignored `pals-webfront/output/playwright/`: `chat-desktop.png`, `question-desktop.png`, `question-mobile.png`, `chat-mobile.png`, `account-menu-desktop.png`, and `settings-desktop.png`. Generated output and environment files are not committed.
