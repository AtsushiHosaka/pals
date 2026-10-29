# T4: bounded hybrid Draft retrieval evidence

Date: 2026-10-28 JST. Status: implemented opt-in review slice; full T4 acceptance
is incomplete. No merge, deployment, catalog admission or caller activation.

## Authority, revisions and ownership

- Working MRD-006/007/008/009 and T4 design/task baseline:
  `48c9be131b63eaabee58463c8a0fd601ca0119e3` on
  `codex/mathematics-roadmap-20261028`.
- Requirements SHA256:
  `16c3fbdd8b925b168d534343fb85abb385a843fc6f2236fb667cad971bdacf9c`.
  Design SHA256: `625091412f449802c39bc885910988fdb7682d969242865264eb1df0055ba99e`.
  Tasks SHA256: `00b493a2f0b79f01cdb65d950d8a7d8824480779f7767aba44a30b6c84cc20e5`.
- Refreshed backend base: `25a5faf81753b14a85a13ab0a254708790de9b94`.
  Implemented backend head: `9678606e4bbb8f273c78983088e9a7740ab376da`.
  [Draft API review PR #27](https://github.com/AtsushiHosaka/pals-api/pull/27).
- Agent base inspected: `4703690c4125eed18fcce9269ce4f1dbc6ff577d`; no agent,
  compiler, cache or agent database-credential change. No prior isolated search
  prototype was copied into an admission or runtime trust boundary.
- Task-owned managed worktree: `typed-theorem-retrieval/pals`, branch
  `codex/typed-theorem-retrieval`. Only the API child, its parent gitlink, and this
  parent evidence file are owned writes. Existing shared checkout changes were
  left untouched. The child was pushed before the parent gitlink was updated.

The slice took approximately 40 minutes from worktree branch creation through
API PR creation, plus initial inspection. Commands were bounded, with a 60-second
Lean subprocess timeout and no service/container creation. The managed worktree
is retained for review; generated evidence remains outside tracked repositories.

## Findings before implementation

These are separate paths:

1. Existing Draft OpenMath canonicalization already recognizes consistent bound
   variable renaming. Read-only checks on absolute-value, affine, reciprocal and
   rank-nullity packaged statements found equal canonical bytes after renaming.
2. The natural-request Recipe reader uses PostgreSQL English full-text search.
   No live miss was reproduced, so a variable-name root cause is not established.
3. Formal LRC-003/006 intentionally uses exact whitespace-normalized target bytes.
   Its selector was not changed.
4. LRC-018 natural correspondence separately allows independently reviewed binder
   renaming. Search similarity and copied target digests do not prove this review.

Primary-source rationale is documented in the API's
`docs/api/hybrid-draft-retrieval.md` and the shared research document: Lean Expr
and local-context abstraction, RefinedDiscrTree labeled wildcards, LibrarySearch,
MathWebSearch, LeanDojo/ReProver and LeanSearch. No novelty claim follows.

## Concrete implementation

An authenticated, separately versioned
`/v1/internal/proof-requests/hybrid-draft-candidates` endpoint consumes closed v4
OpenMath plus the existing embedding binding. It unions bounded canonical
identity, structural and vector candidates over the exact API-owned read-only
snapshot. Its transient index retains lexical scope, resolved symbol namespaces,
constants, repeated-variable identity, explicit domains, hypotheses and quantifier
dependencies. No wildcard erases these features.

Candidate metadata distinguishes identity, one-parameter guarded integer-literal
specialization, a syntactic implication with its antecedent obligation, and
unsupported/inapplicable structures. Typed literal metadata reports the required
domain and unresolved membership obligation. This is not arbitrary typed Lean
unification or a proof of applicability. An explicit method is inapplicable when
the Draft lacks source-bound method evidence.

Every result remains `unverified_sketches`, with `establishes_equivalence=false`
and `requires_new_lean=true`. Existing payload/catalog/embedding bindings and
selectable-addition lifecycle reads remain separate from matching metadata.
No schema migration or mutable index is introduced. The existing endpoint and
worker stay on v1; adoption requires explicit integration after review.

PFR-010/011/016/017, LRC exact selection, Recipe admission/correspondence/stored
answers, and T5 compiler/cache execution remain unchanged. A new source,
specialization, substitution or wrapper still needs the linked Lean path.

## Executed evidence

Focused command: API dependency environment, `PYTHONDONTWRITEBYTECODE=1`,
`PYTHONPATH=.`, pytest with `-p no:cacheprovider`, selecting the two new matcher/
ranking unit modules, legacy natural-Draft validation, legacy Recipe selection,
Recipe wire bounds, and both new integration modules.

- **74 passed, 1 skipped**, exit 0. The skipped check is the real PG16/pgvector
  catalog test, whose required isolated release/reader LOGIN URLs were unavailable.
- Ruff passed for all changed Python files. Strict mypy passed for the five
  changed production modules. `git diff --check` passed. Existing Starlette/httpx
  and event-loop deprecation warnings remain.
- Independent implementation/architecture/FastAPI review found and fixed inherited
  namespace and namespace-whitespace canonicalization errors. Their regressions
  pass; targeted re-review found no remaining actionable P0/P1/P2 in this slice.
- Independent reviewer reran the 73 unit/legacy checks and actual pinned Lean
  application test. Unit test data and standalone Lean fixtures are not substitutes
  for live provider/database or source-bound runtime application evidence.

Pinned Lean application used the existing dependency workspace without another
Mathlib build: Lean `4.32.0-rc1`, commit
`b4812ae53eea93439ad5dce5a5c26591c31cb697`, Mathlib
`8b62164d808cd0f23b7d8cc28190a6c1a1bb483a`. Lake manifest SHA256:
`290f048c4a499d34a3b21f8db30ade48a2b8d05b0fe79709f1868fa6748944fa`.
Lean fixture SHA256:
`665b08b42990bfd4b75eb963e3c9b536e3fc04bb7fb740862d60129046e9a2bc`.

Actual compilation accepted a substantive real triangle inequality under renamed
binders and a newly compiled exponential-positivity specialization with explicit
domain obligation discharge. Changed sign, strict conclusion, dropped premise and
changed dependent witness order fail typing. Printed positive theorem axioms are
`propext`, `Classical.choice`, `Quot.sound`, with no `sorryAx`. These are manually
paired standalone proof examples, not an automatic XML-to-Lean binding verifier
or a runtime verified-application-rate measurement.

## Stored-vector replay and performance limit

The reproducible API script `scripts/evaluate_hybrid_drafts.py` reads 433 actual
stored 384-dimensional vectors and source payloads. Data SHA256:
`906e9b3256aeea340dac1caaa93c3e33fda817213bac506b6f11141a54292fe6`.
395 signatures pass closed-v4 validation; 38 incompatible legacy entries remain
excluded by the existing evidence contract. Eight substantive sources with three
consistent renamings give 24 trials. Their original stored query vector is reused
deliberately: this is offline self-retrieval, not unseen-query quality evidence.

| Metric | Baseline | Hybrid |
| --- | ---: | ---: |
| Any-identical Recall@1 | 1.0 | 1.0 |
| Any-identical Recall@8 | 1.0 | 1.0 |
| MRR@8 | 1.0 | 1.0 |
| Warm local CPU total p50 | 58.70 ms | 654.06 ms |
| Warm local CPU total p95 | 111.84 ms | 1266.65 ms |

There is no measured retrieval-quality gain or speedup. Hybrid transient index
rebuilding is slower. Stage p50/p95 milliseconds: stored-vector cosine
53.72/104.73; baseline top-eight canonicalization 3.86/8.80; hybrid all-row payload
canonicalization 285.45/564.42; canonical index 278.42/547.80; matching 36.03/55.84;
ranking 0.41/0.67. Cold process, database and provider timings are unmeasured.
Structural identity false-label count was zero on these replay labels;
mathematical false acceptance and end-to-end verified application remain unmeasured.

Raw final replay: `/private/tmp/pals-t4-final-replay.json`, SHA256
`9f3c08d0a1ae5bfc16fa6582569b26dd39e83bd1f4845ed2dd3c07c9a77aca9f`.
Standalone Lean diagnostics: `/private/tmp/pals-t4-lean-application.txt`.
Generated outputs were not committed.

## Missing evidence and concrete continuation

Existing OrbStack PostgreSQL ports 54321/54322/54323/54324/54327 accepted TCP but
timed out on PostgreSQL protocol negotiation. Docker inventory also failed to
respond and was interrupted. No existing service was restarted or duplicated.
The PG test is prepared against the existing owned isolated fixture, requiring
`PALS_TEST_POSTGRES_URL`, `PALS_TEST_PRODUCTION_RELEASE_URL`,
`PALS_PFI_DRAFT_READER_DATABASE_URL`, and `PALS_MAC_ISOLATED_TEST=1`; restore that
dependency and execute `tests/integration/test_hybrid_draft_postgres.py`.

T4 still owns these follow-ups before full acceptance:

- Real restricted-LOGIN PostgreSQL/pgvector query and lifecycle-concurrency checks.
- Fresh provider and reviewed unseen renamed-positive/hard-negative corpus,
  baseline/new Recall@k/MRR, mathematical false acceptance and verified application
  rates, and cold/warm stage p50/p95. No credentials or approval were bypassed.
- Reviewed general Lean Expr/local-context export, preserving types, universes and
  ordered dependent context; source/toolchain/admission-bound index metadata and
  Recipe candidate integration, while retaining the old exact selector.
- A separately reviewed persistent-index strategy if runtime performance warrants
  it, rather than activating this slower transient rebuilding path by default.
- Source-bound matcher-to-Lean application evidence through the linked verifier,
  coordinated with T5 without treating matching identity as compiler-cache identity.

No browser chat flow, admitted Recipe, provider query, deployed endpoint or
production performance result was verified by this slice.
