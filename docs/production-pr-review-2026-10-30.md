# PALS PR review and production walkthrough handoff

Status snapshot: 2026-10-30 JST. GitHub metadata was checked for all 19 PRs below.
All 15 approved PRs are confirmed merged, and four remain held. The signed
production deployment completed with status **healthy** for the reviewed parent.
The complete production screen recording is **PENDING**.

This report records source review, executed local checks and the signed production
deployment result. It does not establish authenticated UI completeness or mark
the mathematics roadmap done.

## PR dispositions

| Repository / PR | Confirmed disposition | Reviewed outcome or remaining prerequisite |
| --- | --- | --- |
| [pals #114](https://github.com/AtsushiHosaka/pals/pull/114) | Merged | Integrates the reviewed child revisions below; preserves existing account and usage features. |
| [pals #116](https://github.com/AtsushiHosaka/pals/pull/116) | Merged | Working mathematics roadmap and exact commit-identifier scanner findings; requirements are not runtime completion. |
| [pals #117](https://github.com/AtsushiHosaka/pals/pull/117) | Merged | Geometry evidence reconciled with merged agent main without downgrading child pins. |
| [pals #118](https://github.com/AtsushiHosaka/pals/pull/118) | Merged | Mathematics corpus and checked authoring evidence; no catalog admission claimed. |
| [pals #119](https://github.com/AtsushiHosaka/pals/pull/119) | Held, draft | Diagram integration depends on real renderer, persistence and browser acceptance. |
| [pals #120](https://github.com/AtsushiHosaka/pals/pull/120) | Merged | Hybrid retrieval evidence reconciled with merged API; slower opt-in path remains opt-in. |
| [pals #121](https://github.com/AtsushiHosaka/pals/pull/121) | Merged | Reviewed acceleration evidence reconciled with merged agent main; default-off behavior and incomplete production limits retained. |
| [pals-agent #16](https://github.com/AtsushiHosaka/pals-agent/pull/16) | Merged | Preserves computational/decision tasks and exact Lean harness, semantic review and answer review. |
| [pals-agent #18](https://github.com/AtsushiHosaka/pals-agent/pull/18) | Merged | Checked caller-structured isosceles/midpoint family, trace and axiom audit; opt-in CLI only. |
| [pals-agent #19](https://github.com/AtsushiHosaka/pals-agent/pull/19) | Merged | Offline breadth corpus/evaluator explicitly retains four unfinished entries. |
| [pals-agent #20](https://github.com/AtsushiHosaka/pals-agent/pull/20) | Merged | Fresh bounded compiler per proof; separate uncached admission compiler; Lake setup reuse defaults false. |
| [pals-api #23](https://github.com/AtsushiHosaka/pals-api/pull/23) | Merged | Overlapping-trigger regression tests; original concurrent-user production incident remains unreproduced. |
| [pals-api #24](https://github.com/AtsushiHosaka/pals-api/pull/24) | Merged | New work captures selected output language while queued work, retries and historical answers retain their captured language. |
| [pals-api #26](https://github.com/AtsushiHosaka/pals-api/pull/26) | Held, draft | Actual TeX worker isolation, deployment transport, producer and PostgreSQL reload are unverified. |
| [pals-api #27](https://github.com/AtsushiHosaka/pals-api/pull/27) | Merged | Authenticated versioned hybrid retrieval; stale generated OpenAPI artifact repaired during review. |
| [pals-webfront #24](https://github.com/AtsushiHosaka/pals-webfront/pull/24) | Merged | Output-language help and saved-message copy; unapproved usage/account removals restored before merge. |
| [pals-webfront #26](https://github.com/AtsushiHosaka/pals-webfront/pull/26) | Held, draft | Inline transport slice lacks producer/browser/worker acceptance and current-request rendering integration. |
| [pals-infra #28](https://github.com/AtsushiHosaka/pals-infra/pull/28) | Merged | Bounded qualified-site/final-route grammar preserves existing guards and routing behavior. |
| [pals-infra #57](https://github.com/AtsushiHosaka/pals-infra/pull/57) | Held, draft | Incident-specific sealed recovery helper; current-main overlay checks returned seven passes and one failure. No current production incident plan/apply authority or acceptance established. |

## Deployed d0ef source revisions

The deployment's six source commits match the exact parent gitlinks below.
Datasets and observability retain their existing pins; they were not changed by
the approved PRs. Source commits remain distinct from running image identities.

| Child repository | Pinned revision |
| --- | --- |
| pals-agent | `6581588b1d292549e3e7a5c07a4a4896b8ff3cdd` |
| pals-api | `8bb38aa27e4670b4195c334210e414029c2fcebe` |
| pals-webfront | `df325124172fe64c48c68bf4c697c2132ccb8243` |
| pals-infra | `d70b12555f71cf0e4403ef13d616b5f802326e5c` |
| pals-datasets | `9fac256800a78301ba3797e83e4278fa6afcfe97` |
| pals-observability | `c8c89250fdb8d76af400d949299e4bc6b7fdade4` |

Agent merge review covered #16 `fa901770`, #18 `80ea019b`, #19 `719c1c96`
and #20 `12054624`. Each merged subsystem's production bytes match its reviewed
head. The API #27 OpenAPI repair was reviewed at `6e8340f3`; final frontend #24
was reviewed and merged from `6e3075f5`. Parent #121 merged as the current
reviewed parent `d0ef6efd33e90c7aa0d899763d1c8e9e2df58702`.

## Executed evidence and repairs

The following results are from this review run and the root's recorded integration
checks. Counts overlap; they must not be added into a purported unique total.

| Scope | Actual evidence | Practical limit |
| --- | --- | --- |
| Combined agent main | 478 affected-subsystem tests passed; production subsystem bytes matched all four reviewed heads; whitespace checks passed. | No production/provider/UI acceptance implied. |
| Agent #16 | 196 targeted tests, Ruff and scoped mypy passed. | Live provider behavior was not rerun. Six transitive mypy errors were in byte-identical, pre-existing `openmath.py`; changed-module checking passed. |
| Agent geometry | 84 unit tests plus two actual pinned Lean proof/axiom/negative integration tests passed; Ruff and strict mypy passed. | Structured caller input only; no natural-language equivalence, chat persistence or rendered figure acceptance. |
| Agent breadth | 33 tests passed; all nine source-backed declarations actually compiled; Ruff and strict mypy passed. | Three entrance cases and one geometry entry remain `authored_not_compiled`; complete evaluation deliberately returns exit 1 and `all_compiled=false`. |
| Agent acceleration | 247 verifier/pipeline/reuse regression tests and five real Lean integration tests passed; Ruff and strict mypy passed. Thirteen mTLS tests passed after allowing the local test server's loopback bind. | Local compiler evidence does not establish production Linux containment or 4-GiB compatibility. |
| Combined API | 231 tests plus a separate actual pinned Lean application passed; OpenAPI consistency, Ruff and whitespace checks passed. | 34 PostgreSQL-dependent tests explicitly skipped because isolated database URLs were unavailable. |
| Final frontend #24 | TypeScript, affected ESLint and all 1,583 unit tests across 125 files passed. Billing and account/preference regressions also passed in targeted selections. | Source/local verification only; production browser behavior pending deployment. |
| Held frontend #26 | TypeScript and 47 inline-diagram/explanation tests passed. | Does not prove real renderer, persistence, producer or browser integration. |
| Infrastructure/parent | 63 integrated edge-grammar tests, 17 preparation tests and 105 controller/checkout/main/workflow tests passed; parent secret-history gate passed. | No production host mutation or serving-configuration activation established by these checks. |
| Parent authoring/evidence | Prime-ideal formula, generated witness and digest matched; loader retained `local_authoring_evidence_bound_not_admitted`. Geometry input/trace/source digests and documented line ranges matched combined agent main. Root reran the parent preparation command successfully. | Preparation is not embedding, signed catalog review, admission or publication. |

Review repaired the stale API OpenAPI artifact and restored reservation balances,
conversion disclosure, sidebar account fallback labels and existing billing
actions removed by the original frontend proposal. Final frontend #24 changes
only the output-language hint and saved confirmation in the four interface
languages. Parent evidence PRs were reconciled without reverting newer child
pins. These repairs preserve existing user-facing entry points.

## Release limits and pending operations

- **Production deployment: HEALTHY.** The exact clean Mini checkout passed
  preflight, and the existing signed deployment wrapper completed through approved
  Parsec input. Its `pals.macmini-deploy-result.v3` result reported `healthy` for
  parent `d0ef6efd33e90c7aa0d899763d1c8e9e2df58702` and the six source commits
  above. The safe manifest fingerprint is
  `e2c1ecedccd2d6577956f5023b9fa3628a4b58e91fc98632dc08d8c5ad59f69d`.
  Completion checks cover receipt and database identity, all running image
  identities/provenance, readiness, external HTTP and a second container check
  before atomic replacement of `current.json`. No account or database identifiers
  are recorded here. This result does not establish authenticated UI behavior.
  The public-repository self-hosted Actions gate remains intact; a workflow with
  a skipped deployment job was not used as deployment evidence.
- **Production recording: PENDING.** Source inventory and local tests do not
  establish that every required screen has been visited or recorded.
- **Diagram release: HELD.** No actual worker image/TeX render or filesystem,
  network, cgroup and cleanup containment was verified. Docker build provenance,
  split-container transport, real PostgreSQL reload, shared-snapshot behavior,
  producer wiring and desktop/mobile browser acceptance remain open. Current
  submissions render through a different thread from the existing inline-diagram
  component; deploying that component alone will not complete the integration.
- **Hybrid retrieval: opt-in.** Stored-vector self-replay showed no retrieval
  quality gain and higher transient-index CPU latency. Live DB/provider metrics,
  verified application rate, false acceptance, general Lean-context indexing and
  admission remain incomplete. Keep existing worker/formal selection contracts.
- **Lake environment reuse: default false.** Local peak child RSS previously
  exceeded 4 GiB in an aggregate measurement that cannot identify a safe mode.
  Do not infer production memory fit or enable reuse from local speed figures.
  No compiled-proof verdict or generated-module cache was introduced.
- **Catalog/coverage:** local authored proofs do not publish or admit a theorem
  and do not establish whole-family undergraduate/entrance-exam support.

## Production UI recording checklist

Executable coverage rows are **PENDING**. The source-absent model selector is
listed separately as unavailable. This is the source-derived coverage matrix
supplied by the frontend review, not a record of executed navigation. Reuse the authenticated
session and readable existing proof/material/share fixtures. Open and cancel
destructive confirmations; opening billing/share controls does not imply a
purchase, publication or revocation. Any unavailable role, fixture or screen must
remain an explicit coverage gap.

| Required UI group | Screens and interactions to record | Status |
| --- | --- | --- |
| Public and guest | `/`, `/about`, `/try`; About FAQ, plans and conditionally displayed product video; guest composer, math keyboard, image/PDF drafts, clarification and limit states. | PENDING |
| Authentication | Sign in, sign up, confirmation, forgot/reset password and normal callback transition; use existing account access. | PENDING |
| Navigation/projects | Dashboard, new-project dialog, `/projects` list/search/clear, project overview, desktop/mobile sidebar and expand-more. | PENDING |
| Chats/search | Project chat, current and legacy saved chats, chat-list redirect, search modal/results/pagination. | PENDING |
| Account/settings | Account menu; General UI/output language and notation rules/identifier; Usage balances, progress, plans, conversion disclosure and action entry points. Conventions selections autosave, so inspect without changing pending authorization. | PENDING |
| Composer | Math-keyboard categories, attachment controls and image/PDF previews. | PENDING |
| Generation-model selector | `ProofComposer` defines an optional model-selector prop, but no caller supplies it. There is no reachable menu in the reviewed source; do not count it as visited or as recording coverage. | UNAVAILABLE (source absent) |
| Materials | Project material list/detail, preview, PDF previous/next and numeric page/Go controls, original download and existing extraction states. | PENDING |
| Mathematical answer | Premise/clarification options, existing follow-up answer and text-selection question form, definition hover, Lean source and Activity panels. | PENDING |
| Sharing | Preview, existing snapshot `/share/:token`, existing-link/copy controls; publication/revocation not counted merely by opening controls. | PENDING |
| Confirmation/error/responsive | Open/cancel delete confirmations, readable existing empty/error states, mobile navigation and layout. `/qa/proof-explanation` intentionally returns 404. | PENDING |

Production completion requires the actual recording artifact, observed coverage
against this matrix, and an explicit list of any remaining inaccessible screens.

## Production keyboard follow-up

The authenticated production walkthrough exposed a focus-trap defect in the
Usage dialog for permanent complimentary Pro: with every purchase button
disabled, Tab from Mathematics wrapped to Close before reaching the native
usage-conversion disclosure. Frontend [#27](https://github.com/AtsushiHosaka/pals-webfront/pull/27)
adds native `summary` controls to the shared modal focusable selector. The
regression failed against the old implementation; 73 affected tests, typecheck
and lint passed. Independently reviewed head `304ba6df2fbcad369c550e74ff140493afa625e3`
merged as `89daac472e89ac9800563b81f360d43e73cc7665`. This follow-up parent pins
that merged frontend; the healthy deployment evidence above applies to the
preceding release until the follow-up is deployed and read back.

Production account sign-in succeeded through the normal saved-credential form.
Existing saved mathematical proof/follow-up data loaded. General settings,
interface-language options, temporary Japanese UI and restoration to English,
output-language options/save, Usage balances and the Mathematics catalog were
visited during native recording. Both language controls were restored to their
original English selection. Complete coverage and final video verification
remain pending. No purchase, deletion, public sharing, password change or
mathematics-convention change was executed.
