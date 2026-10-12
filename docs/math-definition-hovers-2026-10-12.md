# Mathematical definition hovers

The 2026-10-12 user request adds hover meanings for mathematical terms, symbols,
and explicitly declared variables. The user chose explicit declarations only and
requested no underlines. The implementation and continuity follow-up are merged in
[frontend PR #20](https://github.com/AtsushiHosaka/pals-webfront/pull/20) and
[frontend PR #21](https://github.com/AtsushiHosaka/pals-webfront/pull/21).
The deployed frontend pin is `c21907b33cf5c6658de57dd6e666803aba4d1fb1`.

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

The follow-up adds continuity/continuous/連続性/連続 and exact typed fixed-point
declarations, including `任意の実数 $a$ を固定する。`. Subsequent arbitrary epsilon
does not erase that fixed point; repeated, conditional, nested, or introduced
rebindings still suppress ambiguous meanings.

Validation in the frontend worktree:

- Integrated frontend main `7aabcd4` and preserved its existing attachments,
  guest source panel, newline repair, and math keyboard.
- Full integrated unit suite: 125 files / 1,564 tests passed. Final scoped
  regression suite: 5 files / 154 tests passed.
- TypeScript, ESLint, production build with the documented local API URL,
  and independent scoped code review passed.
- The final follow-up passed all 138 files / 1,684 tests, ESLint, TypeScript,
  the production build, and independent review. Existing full-text UI assertions
  retain their expected strings across inline hover spans.
- Real Chromium checks at desktop and 390px mobile viewport passed for invisible
  styling, variable/symbol/Japanese meanings, pointer transitions, keyboard
  controls, and long tooltip placement/scrolling. Screenshots remain local under
  the frontend's ignored `output/playwright/hover/` directory.

The local renderer checks use actual frontend components and CSS. They do not
prove authentication, backend/provider execution, or formal proof generation.

## Production deployment evidence

The user's explicit deployment request authorized the coordinated signed release.
The Mac mini deployment owner restored the failed candidate before the final
release. The signing and original-row preservation gates were retained; the
independently reviewed recovery patch narrowly accounts for the existing startup
retention of two expired guest records.

[Signed deployment run 38221916596](https://github.com/AtsushiHosaka/pals/actions/runs/38221916596)
completed successfully for parent `e24047817f60e3d27e44b2f31090ee0641751a05`,
which pins frontend `c21907b33cf5c6658de57dd6e666803aba4d1fb1` and reviewed infra
`850b916906d3fe3fcdf70b3656d0b36f7567f0df`. The merged frontend tree exactly
matches the tested follow-up tree `529f4696ca2bcfdcbc17accf4063652f4c6a6e79`.

Public site and API health probes returned HTTP 200. The actual `/try` asset graph
contains the definition metadata, tooltip, continuity glossary, and typed fixed
declaration code, with no underline trigger marker. Final public JavaScript
hashes include `b8af8571dd871d2aee0ec8c6af702917bc25839c377c6f643f21b16378567976`
and `930e2be426d67ef9ae41904af8c85c2d7203f3c3854e20412d20d6e899e7b5e1`.
These are release/distribution checks; authenticated tooltip behavior and the
separate attachment/settings routing checks require their own runtime evidence.
