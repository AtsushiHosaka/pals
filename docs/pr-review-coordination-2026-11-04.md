# Issue-driven implementation and PR coordination

Owner instruction, 2026-11-04: continue issue-driven implementation, proactively review PRs,
coordinate with other agents through GitHub, correct unsupported issue assumptions and create
focused issues when needed. API evaluations expected below $1 in total are authorized; stop
before an evaluation expected to reach $1. No new merge, deployment, publication, feature-removal
or admission authority is inferred from this instruction.

Session: `codex://threads/01a1a258-3e8e-7aa0-b2f0-6a2c91477ba8`.
Coordination comments are on [#178](https://github.com/AtsushiHosaka/pals/issues/178),
[#181](https://github.com/AtsushiHosaka/pals/issues/181),
[#186](https://github.com/AtsushiHosaka/pals/issues/186),
[#195](https://github.com/AtsushiHosaka/pals/issues/195) and the reviewed PRs.

## Reviews

| PR and pinned head | Result and limit |
| --- | --- |
| [agent#34](https://github.com/AtsushiHosaka/pals-agent/pull/34), `bb3788f214955eb38a60ea7aba5cbccbdabb022d`, base `088e3ce` | P2: new counterexample review omits the complete question/options, then approval returns the unreviewed question unchanged. A correct S3 counterexample can accompany an assertion that it is not a counterexample. The rewrite path retains old alternatives. Posted an inline review at `proof_reuse.py:1255`; request assembled-output review. The isolated boundary witness supports routing only, not model frequency. |
| [agent#39](https://github.com/AtsushiHosaka/pals-agent/pull/39), `e1eb5a148da103ba5975c60eafe94bf8963c93c8` | No demonstrated logic defect in the paragraph transformation; seven targeted tests pass. Actual generated effect is 747/1,899 answers, other fields unchanged. The body reflects older counts. Not a mathematical, DB, browser or deployment review. |
| [agent#37](https://github.com/AtsushiHosaka/pals-agent/pull/37), `dec2a27ca469d9870c7b34f1c6cb0e9fc39e7b32` | Actual figure build from exact committed #27 card sources reproduces all 35 figures, including answer-label checks. Fifty targeted tests pass; one integration-prerequisite test skips. The digest test compares only present IDs and can pass with zero comparisons if a present candidate file lacks the figure cards. Request a mandatory complete-ID integration gate. |

The #34 counterexample review/rewrite prompts also need the shared #45 learner policy when
those branches integrate; their output is learner-visible. This is a cross-branch requirement,
not a regression against #34's older base. No peer-owned branch was edited.

## Figure integration evidence

All 35 required geometry IDs already exist in committed [agent#27](https://github.com/AtsushiHosaka/pals-agent/pull/27)
head `b9db8d5245097b6b7cf29292a70e93f50e9b7d29`. The assumption that those sources remain
uncommitted is stale in #165 and the figure PR descriptions. This does not make concurrent
untracked university cards safe to overwrite.

- The actual #37 builder, run on `git show` copies of those committed cards in temporary
  storage, produces 35/35 matching figure calls and validates labels against answer text.
- Worker #37 and [API#41](https://github.com/AtsushiHosaka/pals-api/pull/41) head
  `c38d82af5484f232cc8505e95d562f81e433a328` figure JSONs are byte-identical, SHA-256
  `16e8d4b6d104489b9373ccbbedae6b09950068f8b1ae836195bfb93a9fffcdc7`.
- #39's 1,899-candidate generated data matches all 35 figure digests.
- Current #27's 2,480-candidate generated data matches only 8/35, with 27 digest differences.
  Applying the exact #39 paragraph transformation makes 35/35 match. It would change
  890/2,480 answers; do not overwrite the larger catalog with #39's older generated file.
- Keep uniqueness on `(recipe_id, answer_sha256)`, matching the API's versioned lookup.
  Recipe-ID-only uniqueness would reject legitimate answer versions.

These standalone artifact comparisons are recorded in the quality ledger. They prove local
binding consistency, not successful production settlement or visible rendered figures. API#41
and the web figure/lowercase-label PRs remain separate runtime prerequisites. Coordination is
posted on [#165](https://github.com/AtsushiHosaka/pals/issues/165), #37 and #39.

## Follow-on implementation

Claimed [#193](https://github.com/AtsushiHosaka/pals/issues/193) on GitHub before starting:
read-only offline catalog counting tool, its tests, and its definition document. It must keep
unauthenticated authoring candidates separate from published and proven reusable problems.
The full issue remains open until authenticated publication, Draft/typed generations, duplicate
semantics and actual retrieval evidence are implemented and verified.

[#189](https://github.com/AtsushiHosaka/pals/issues/189) requires coordinating the definitive
catalog source before regeneration; its untracked-source prerequisite has not been waived.
No shared expansion worktree, release flag, DB row or service lifecycle was changed here.
