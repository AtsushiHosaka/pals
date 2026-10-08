# Recipe-first implementation evidence — 2026-10-05

This records the implemented change, rather than certifying every acceptance task. The approved behavior is defined in `specs/proof-request-reuse`, `specs/lean-recipe-catalog`, and `specs/draft-addition-candidates`. The earlier source working trees and their unrelated changes were preserved; implementation used an isolated `codex/recipe-first` branch.

## Implemented behavior

After premise clarification, proof requests directly search independently reviewed Recipe entries. Exact mathematical correspondence requires the actual stored Lean, premises, quantifiers, conclusion, requested method, language, and unchanged answer to pass independent review. Settlement revalidates source, compiler receipt, current toolchain, entry lifecycle, request revision, and claim in the existing request transaction. Successful reuse creates no Lean job and calls no compiler, Draft lookup, or answer generator. Ranking is retrieval evidence only; uncertainty, specialization, and valid misses enter full DSP. Provider or integrity errors remain explicit failures.

Draft lookup belongs to DSP's Draft stage. New verified and independently reviewed answers can create candidates from the normal verifier's fenced success receipt. Shared candidates contain no account, project, chat, or conversation fields; private origins remain separate. Each origin must satisfy the 24-hour quiet period. Restricted operators publish Recipe, Draft, and searchable answer in stages, retaining immutable receipts for replay. Final visibility and approval are atomic. The sealed base Draft catalog is unchanged; approved additions are read through a separate projection. Raw Lean admission preserves exact bytes and excludes its policy from the historical formal selector.

The agent provides release-only real-provider Recipe and Draft review/sealing CLIs using existing signing keys. The frontend reads exact stored Lean on demand, verifies the closed response and digest bindings, supports cancellation/retry in four languages, and preserves historical answers that lack the new source entry.

## Reviewable changes

| Repository | Revision | Draft PR |
|---|---|---|
| API | `1cab926` | [pals-api #2](https://github.com/AtsushiHosaka/pals-api/pull/2) |
| Agent | `9d31e8c` | [pals-agent #2](https://github.com/AtsushiHosaka/pals-agent/pull/2) |
| Webfront | `a34dbfa` | [pals-webfront #1](https://github.com/AtsushiHosaka/pals-webfront/pull/1) |

Child branches are pushed before the parent records their submodule revisions. No merge, production migration, deployment, or shared catalog publication was performed.

## Executed verification

| Scope | Executed evidence | Limits |
|---|---|---|
| API persistence and local release | 43 real PostgreSQL tests passed in the final combined run. First install and replay, sealed 433-row base preservation, separate restricted logins, search/admission/settlement, owner and guest source reads, quota and lifecycle tests passed. | The combined run skipped the explicitly configured Lean test and the opt-in provider test; the Lean test was then run separately as below. |
| Normal receipt and raw source | One separate actual mTLS/Lean integration test passed using the existing pinned Mathlib workspace. It exercised normal reconciliation receipt, exact reviewed-output candidate capture, unchanged raw-source compile/admission and replay, and exclusion from the legacy selector. | Independent source/answer reviews in the fixture are contract fixtures, not live model reviews. |
| Candidate authority and projection | Actual restricted operator login combinations, immutable/private data boundaries, and approved-only Draft union were tested against PostgreSQL. Independent two-connection quiet-window/lease tests also passed. | Projection approval, vector and review fixtures are synthetic; this does not establish actual reviewed publication. |
| API units | Final 232 relevant unit tests passed; another 50-test reconciliation/candidate regression run passed (counts overlap). Production registry exactness and diff check passed. | Six Ruff findings in unchanged baseline lines remain; comparing each changed Python file to HEAD found zero new Ruff findings. A pre-existing imported mypy issue remains outside the selected clean files. |
| Agent | 505 relevant regression tests, 17 final search-contract tests, 65 HTTP/deadline/diagnostics/token-meter tests, and 46 Recipe/Draft sealing tests passed (some suites overlap). New Draft producer passed the frozen API consumer contract. Changed-source Ruff and targeted mypy passed. | Six pre-existing mypy errors in unchanged `openmath.py` remain. Provider responses and signing keys in unit tests are fixtures. |
| Webfront | 47 relevant tests, TypeScript and ESLint passed; independent re-review ran a 28-test subset. | No deployed browser or phone/tablet journey is claimed. |
| Specifications | Ten specification/plan files were synchronized. Natural Japanese and yomiyasu checks completed; requirement IDs and final diff checks passed. | Historical checked tasks describe their historical evidence. Grouped acceptance tasks remain unchecked where full provider/runtime evidence is missing. |

Existing PostgreSQL, dependency runtimes, and Mathlib resources were reused. Tests used disposable databases and bounded temporary loopback listeners; no existing application's serving identity, global login password, or shared runtime was replaced. Credentials, raw logs, dumps, generated artifacts, and signing keys are not included in this commit.

## Remaining acceptance and release gates

- **NOT VERIFIED:** actual-provider paraphrase reuse with the zero-call witness. An opt-in `tests/integration/test_recipe_first_runtime.py` is implemented and defaults to skip. Automatic approval review rejected the attempted live run because explicit consent to send the existing square-continuity Lean and explanation to OpenAI was absent. User consent is pending; fixture reviews are not a substitute.
- **NOT VERIFIED:** full provider-reviewed candidate approval, actual embedding publication, partial-publication resume, and subsequent real-provider reuse. The production producers and consumers are implemented; local contract and compiler tests establish only the boundaries listed above.
- **NOT VERIFIED:** complete deployed specialization/DSP/failure/follow-up/guest journeys and broad mathematical negative evaluation.
- **NOT VERIFIED:** production first bootstrap and update. New migrations are registered, and actual closed-gate rejection/locking was tested. The old Mac updater deliberately refuses the new tail. Production authority and deployment require a separate approved release.

## Operator review producer

In the agent environment, an independently authenticated reviewer can produce the Draft part of the canonical publication bundle:

```sh
python -m pals_agent.draft_entry_review \
  --draft draft.canonical.json --embedding-text statement.canonical.xml \
  --lean-source verified.lean --answer reviewed-answer.txt \
  --lean-sha256 SOURCE_SHA256 --answer-sha256 ANSWER_SHA256 --output-language ja \
  --source-author-principal pals.principal.v1/SOURCE_AUTHOR \
  --reviewer-principal pals.principal.v1/REVIEWER --review-key-id REVIEW_KEY_ID \
  --private-key existing-reviewer-ed25519.pem --output sealed-draft.json
```

Inputs must already exist, use exact canonical Draft/OpenMath and captured source/answer bytes, and satisfy the bounds. Output must not exist. This command calls the configured review provider and must follow the approved data-send scope. It creates no key, embedding, Lean, answer, or Draft. The separately sealed Recipe entry and this sealed Draft are submitted through `python -m app.release.draft_candidates approve` using the bundle and pinned public review keys defined in the DAC design. The operator login needs the explicit operator, schema-owner and Recipe-catalog-owner memberships; serving roles receive none of these authorities. A failed publication is inspected through `list` and immutable stage receipts rather than reported as complete.
