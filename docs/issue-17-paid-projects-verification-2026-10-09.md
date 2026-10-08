# Issue #17: paid Projects verification

Issue: https://github.com/AtsushiHosaka/pals/issues/17

The issue's paid-account completion criteria were exercised in the authorized Pro
QA run `20261008-pro-resume-2353`, on 2026-10-08 23:54–2026-10-09 00:18 JST.
The [sanitized report at its immutable source commit](https://github.com/AtsushiHosaka/pals/blob/29b843db26b3297f760875495bec1cb14bb75f45/docs/pro-dogfood-2026-10-09.md)
records an active permanent complimentary Pro entitlement and synthetic test-data
authorization. This note consolidates those recorded results; it is not a new
authenticated browser run.

| Required check | Recorded result | Original evidence |
| --- | --- | --- |
| Authorized paid entitlement | Active permanent complimentary Pro; no purchase or subscription change | `qa/01-pro-active.png`, `qa/41-pro-usage-final.png` |
| Create a synthetic Project | Blank-name validation checked; exact name and description saved and retained after reload | `qa/12-project-name-validation.png`, `qa/13-project-created.png`, `qa/14-new-project-reloaded.png` |
| Find the Project | Matching search narrowed the list; clearing restored it; nonexistent query showed an empty state | `qa/15-project-search-match.png`, `qa/16-project-search-empty.png` |
| Save and revisit a Project conversation | Strict-monotonicity proof accepted; correct English answer persisted after navigation and reload | `qa/17-project-proof-answer.png`, `qa/18-project-answer-reloaded.png` |
| Retain Project membership | A new chat in the new Project retained its association after reload | `qa/37-new-project-chat.png`, `qa/38-new-project-chat-reloaded.png` |
| Retain later conversation turns | Clarification submission and Japanese counterexample persisted after reload | `qa/project-followup-reloaded-dom.txt` |

These results satisfy #17's stated completion condition: creation, conversation
storage, and reload using an actual paid entitlement, with recorded evidence.
The evidence files remain local to the original run; they are not represented as
GitHub attachments. The PR screenshot summarizes this recorded evidence and does
not replace the original captures or establish a fresh deployment test.

The exact live revision was not recorded. This run did not repeat Free-account
creation restrictions or Free-account access to existing Projects. The original
issue's Free-role observations remain historical evidence, and that broader
entitlement matrix remains separate coverage. Projects success does not resolve
Mathematics settings (#12), private sharing (#36), formal-proof failures (#37),
review rejection (#38), follow-up context (#39), clarification labels (#40), or
materials/OCR (#41).

Current frontend source `e07f95ca63f4ab06fcaf68a907250dddaaca478a` was checked
independently in this chat: 32 tests passed across saved user math, source panels,
Projects directory, and existing Project proof stories. Those tests use isolated
fixtures; they are supporting source regression checks, not production proof.
