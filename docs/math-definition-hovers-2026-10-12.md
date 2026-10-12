# Mathematical definition hovers

The 2026-10-12 user request adds hover meanings for mathematical terms, symbols,
and explicitly declared variables. The user chose explicit declarations only and
requested no underlines. Frontend commit `546bdeb6fe7238f3fc7e3d06a38b6694bbf231ca`
is pushed in [frontend draft PR #20](https://github.com/AtsushiHosaka/pals-webfront/pull/20).

Definitions are client-owned metadata on rendered KaTeX spans. The initial
glossary includes perpendicular/orthogonal and line/closed contour integrals,
including `垂直`, `直交`, `⊥`, and `∮`. Variable tooltips quote explicit English or
Japanese declaration sentences. No underlines or badges are added; hover,
keyboard focus, and click/tap open the same tooltip. Stored proof/LaTeX/Lean
source, notation customization, source selection, and KaTeX's `trust:false`
boundary are preserved.

Full request context carries into authenticated and guest answers, structured
explanations, activity views, and verified archive detail. Clarification branches
carry their own questions, parent answers, and key points; rebindings suppress
stale meanings and siblings remain isolated. The declaration grammar is
conservative: single ASCII/Greek inline-math names in supported English/Japanese
patterns. Unknown, ambiguous, bound, or indexed variable meanings are omitted.
These are rendered annotations, not portable commands saved in LaTeX source.

Validation in the frontend worktree:

- Integrated frontend main `7aabcd4` and preserved its existing attachments,
  guest source panel, newline repair, and math keyboard.
- Full integrated unit suite: 125 files / 1,564 tests passed. Final scoped
  regression suite: 5 files / 154 tests passed.
- TypeScript, ESLint, production build with the documented local API URL,
  and independent scoped code review passed.
- Real Chromium checks at desktop and 390px mobile viewport passed for invisible
  styling, variable/symbol/Japanese meanings, pointer transitions, keyboard
  controls, and long tooltip placement/scrolling. Screenshots remain local under
  the frontend's ignored `output/playwright/hover/` directory.

The renderer checks use actual frontend components and CSS. They do not prove
authenticated/backend/provider execution or deployment. No release or production
deployment was performed. The parent pin is updated only after the child push;
other submodule references match current parent main `7e7a3bc`.
