# Typed Draft runtime release

DCE keeps authoring proposals (`pals_local_typed_catalog`) separate from the API-owned
immutable runtime (`pals_typed_catalog`). The generic PFI is unchanged. A Draft remains
five content fields plus its embedding; review/evaluation/provenance belong to generation
and publication records. Unreviewed authoring rows never become candidates automatically.

## Preparation and independent review

Run from `pals-agent` with the existing OpenAI credential supplied privately through the
environment. This command performs actual embedding calls and does not approve or publish:

```sh
.venv/bin/python -m pals_agent.typed_release \
  --manifest ../docs/typed-math-matrix-v1-authoring-manifest.proposal.json \
  --repository-root .. --author-id pals.principal.v1/author/matrix-six \
  --family university.linear-algebra.matrix --output /absolute/path/layout.json
```

The existing-manifest adapter revalidates its original evidence. New Draft authoring can
use `prepare_from_rows`: it requires the five retrieval content fields and actual pinned
embedding model, and does **not** require Lean source or a compiler receipt. These paths
produce unsigned bytes. The exact profile validator/registry hashes are separately pinned
in `pals-api/app/domain/typed_catalog_bindings.json`; changes require a reviewed contract
update, never an inferred fallback.

An independent reviewer reviews exact content and its versioned positive/hard-negative
corpus, then signs RFC 8785 bytes of a `pals.typed-catalog-independent-review.v1` receipt.
It includes `layout_sha256` (SHA256 of layout JCS), distinct `reviewer_id`, UTC `reviewed_at`,
`alignment: approved`, and `hard_negative_corpus_sha256` (SHA256 of corpus JCS). The detached
Ed25519 signature is base64 text. The trusted release configuration supplies the raw
32-byte public key; the untrusted layout cannot nominate a key. Private keys and generated
artifacts must not be committed. A digest or caller-provided approval boolean is insufficient.

## Admission and evaluation

From `pals-api`, the release-only connection is supplied as
`PALS_TYPED_CATALOG_RELEASE_DATABASE_URL`. It needs the controlled migration/owner role,
never the API's serving credential. Install is transactional and refuses schema drift.

```sh
.venv/bin/python -m app.release.typed_catalog install
.venv/bin/python -m app.release.typed_catalog admit \
  --layout /absolute/path/layout.json --review /absolute/path/review.json \
  --signature /absolute/path/review.sig --review-public-key /absolute/path/reviewer.pub
```

Admission creates an **inactive** generation. The ordinary worker endpoint is
`POST /v1/internal/typed-catalog/candidates`, and only reads active generations. The
release evaluator uses `POST /v1/internal/typed-catalog/evaluation-candidates`, exact
`generation_id` and a distinct `X-PALS-Release-Secret` configured via
`PALS_TYPED_CATALOG_RELEASE_SECRET`. Worker credentials cannot access it. Both endpoints
use the same read-only candidate engine, profile binding, population limit (4096), vector
distance and result limit (8). API role membership in `pals_typed_catalog_reader` is
required. The agent never receives a catalog DB credential.

The corpus has schema `pals.typed-catalog-evaluation-corpus.v1`, `profile_id`,
`layout_sha256`, and `queries`. Each query contains only `family_id`, `statement`, reviewed
`canonical_openmath_xml`, `expected_draft_ids`, and `proof_job_id` (nullable). Empty expected
IDs identify hard negatives. Every changed family requires both positive and negative
queries. Positive proof IDs must refer to real API-owned verified jobs with the exact
statement; missing/unverified/different-statement jobs contribute zero completion.

Run from `pals-agent`, supplying existing credentials privately via `PALS_API_BASE_URL`,
`PALS_TYPED_CATALOG_RELEASE_SECRET`, `PALS_WORKER_SHARED_SECRET` and the OpenAI key:

```sh
.venv/bin/python -m pals_agent.typed_evaluation \
  --corpus /absolute/path/corpus.json --generation-id GENERATION_UUID \
  --evaluator-id pals.principal.v1/evaluator/release --output /absolute/path/evaluation.json
```

This executes real structuring, embedding, authenticated API retrieval and semantic
reranking. It computes structuring success, Recall@8, reciprocal rank, false-match/no-match
rates and API-verified completion. It does not accept success booleans or create proof jobs.
A model/transport error fails the run and does not activate. The report remains unsigned
until a release authority inspects and signs its exact JCS bytes.

## Activation and rollback

```sh
.venv/bin/python -m app.release.typed_catalog activate \
  --profile typed-math-matrix-v1 --generation-id GENERATION_UUID \
  --layout-sha256 LAYOUT_SHA256 --evaluation /absolute/path/evaluation.json \
  --signature /absolute/path/evaluation.sig --review-public-key /absolute/path/reviewer.pub
```

The initial conservative policy requires all success metrics to equal 1 and both failure
rates to equal 0 for every changed family. Threshold relaxation requires an explicit
versioned policy change. Activation checks the exact layout/corpus/family binding, keeps
the old active generation on every precondition failure, and atomically records the new
pointer plus signed evaluation. Rollback runs the same command for a prior compatible
immutable generation and its signed evaluation; historical rows are never edited.

## Current evidence and limits

The repository inventory currently reports school 36/321 and undergraduate 25/500 filled,
with 0 admitted declared coverage cells: at least 760 required cells still need independently
authored, distinct patterns. Advanced 500 is unrefined and not included in that figure.
222 typed cards exist across 16 profiles; the full manifest loader now covers all 222 cards
across those 16 profiles. Loading preserves each sealed authoring status and does not confer
independent review, publication, or admitted coverage.

Tests cover actual PostgreSQL, exact existing matrix validators, immutable admission,
rollback preconditions, API authentication, and the agent HTTP port. Fixed vectors used by
those transport tests do not establish embedding quality. Actual embedding, runtime quality
and verified completion must be run separately; no fixture evaluation is release evidence.

### Worker profile routing

`PALS_TYPED_CATALOG_ENABLED=true` connects `build_pipeline` to
`ProfileRoutedProofFlowRuntime`. The worker first chooses one of the installed typed
profiles, `generic-v1`, or no compatible profile using a closed model response. An
invalid or ambiguous choice does not query a catalog. Typed requests retain their
profile, immutable generation/layout compatibility, and typed XML validator. Only
the existing worker credential is used; the worker has neither release-evaluation
credentials nor database access.

A selected typed profile that is unavailable or incompatible yields a reasoned
`pals.profile-routing.v1` no-match and ordinary custom proof generation. It never
queries the generic catalog or another typed profile as fallback. Selecting
`generic-v1` invokes the existing PFI runtime only when its pinned provenance is
configured; otherwise it records `generic_profile_unconfigured`. Setting the flag
to false preserves the prior generic PFI/direct-generation composition.

Typed matched strategies can inform generation. They cannot become a generic
Recipe `DraftRevisionReference`: `exact_retrieved_draft_reference` rejects typed
retrieval schemas until a profile-specific Recipe alignment contract exists.
The routing flag does not admit or activate catalog content, or establish runtime
retrieval quality. Those gates still require the signed exact layout/corpus and
actual generation-specific evaluation.

### Structuring grammar and private failure evidence

The symbol registry identifies vocabulary; it does not specify how many arguments an
operator accepts. Worker structuring now also supplies the trusted serialization and
signature notes in `typed_profile_guidance.py` and `typed_algebra_guidance.py`, derived
from the same 16 validators. This includes dependent-carrier binding order, literal
casts and dimensions, implicit-sort geometry binders, and the narrower ODE certificate
and graph-family boundaries. The notes contain no catalog answers. Validators remain
authoritative, and their bytes/registry admission fingerprints are unchanged.

Failures distinguish structuring, embedding, candidate retrieval, and reranking.
A failed structuring response records its hash and at most 4,096 UTF-8 bytes of XML,
plus at most 512 bytes of a local XML-validator diagnostic, in owner-scoped private
artifact metadata. Provider/transport exception strings are excluded. Public status
projection discards this diagnostic payload. This supports diagnosis without claiming
that malformed XML or an unavailable generation produced a successful retrieval.

### Provider usage metadata compatibility (2026-09-30)

The approved positive-only transpose diagnostic against inactive generation
`c439e33e-8a66-4d1d-84c9-729049c27123` failed at the reranker's `usage` parse stage.
The response was `completed`, with exactly one `message`, 9,282 input tokens
(8,960 cached), 67 output tokens (0 reasoning), and 9,349 total tokens. These
known counts satisfy the arithmetic bounds. This evidence identifies the usage
shape boundary; it does not prove the names or content of additional metadata,
and is not evidence that the earlier five failures all had the same cause.
Private diagnostic evidence: `output/dce-matrix-phase2/transpose-reranker-diagnostic-observations.json`.

The provider adapter now requires all known usage fields while ignoring additive
metadata in the usage object and its input/output detail objects. It still rejects
duplicate members in these objects, missing required fields, booleans, noninteger
or negative counts, integer overflow, cached input exceeding input, reasoning
output exceeding output, and inconsistent input/output/total counts. Unknown
metadata is never returned, persisted, or used to select a Draft. The provider
model, response status, single-message shape, strict selection JSON, candidate-ID
membership/uniqueness, 512 output-token request bound and single-call behavior
are unchanged. This is provider metadata adaptation, not a successful retrieval
observation: real replay remains separate from unit verification, and no release
metric or activation is inferred from this change.

## Typed structuring validation status (2026-09-29 UTC)

The local v3 expression transport separates all 58 sort constructors across sixteen
profiles from normal expressions, retaining the full mathematical validators. Its
268-test targeted suite passed; the separate closed provider-diagnostics addition
passed 150 related tests. These tests do not establish provider acceptance or live
semantic fidelity.

The reviewed original positive transpose diagnostic at 16:12:18 UTC received HTTP
429 with `provider_type=insufficient_quota`, one attempt and no repair. This confirms
the latest call was blocked by provider quota; schema incompatibility is **not**
established. An earlier attempt lacked HTTP metadata, so its cause remains unknown.
The final local service update on September 29 included v3 together with the semantic-review operational-failure fix (see `output/semantic-review-unavailable-20260930/deployed-source-binding.json`). Actual v3 schema acceptance, successful typed retrieval and final release evaluation remain unverified.

On September 30 the user approved the six previously pending negative statements. A new first-negative diagnostic at 01:08:42 UTC again returned HTTP429 / insufficient_quota after one attempt. The other five negatives were not sent; authorization is resolved but quota remains blocked. No activation or quality pass is inferred. See `output/dce-matrix-approved-resume-20260930/review.md`.

Local evidence (not committed):
`output/dce-matrix-phase2/transpose-sort-expression-ast-v3-transport-diagnostic-observations.json`,
`output/typed-ast-v3/validation.md`, and
`output/typed-ast-v3/transport-diagnostics.md`. Historical failed artifacts are retained.

## Quota-restored replay (2026-09-30 UTC)

The user's quota-restoration report was verified by actual provider calls at 02:05 UTC.
The v3 schema was accepted, but the first negative addition query became a zero-matrix
identity. Further diagnostics included a correctly structured false multiplication that
still selected four related strategies. These are separate structuring-fidelity and
proof-support-selection failures; neither is evidence that a false proof was accepted.
The baseline stopped at an invalid scale query after six attempted queries in total.
Evidence: `output/dce-matrix-quota-restored-20260930/{first,remaining}-observations.json`.

Transport v4 introduced explicit matrix literal slots and a pre-embedding numeric-literal
preservation guard. The next first-negative run was rejected twice because scalar entries
were represented as 1x1 zero matrices instead of field elements. This failed run is retained
at `output/dce-matrix-v4-20260930/first-observations.json`; no release success is inferred.
The typed selector now has a separate version/hash and requires applicable proof support
without changing the original conclusion. Generic relevance selection remains unchanged.

The original exchange-matrix proof was separately rerun as job
`7316fb0b-4d3c-4685-ac7b-f54907fb74c9`: verified at 02:14:25 UTC and explanation completed
at 02:14:31 UTC, after three automatic repairs. Independent review checked the unchanged
arbitrary-field two-sided inverse statement, component calculation, independent QA session
and all source/review/explanation bindings. This completes a successful original inverse
proof observation, not the retrieval or catalog release gates. Old failed job history and
the old signed corpus remain unchanged. See
`output/dce-matrix-quota-restored-20260930/inverse-independent-review.json`.

### Final local matrix replay in this slice

Transport v5 restricts matrix entries to the existing validator's scalar forms. The
exact-rational counterexample filter rejects only supported closed universal-field
queries that fail over Q; it does not prove positive queries or natural-language fidelity.
The last twelve-query run selected the expected card for all six positives and rejected
all six negatives. Exact structuring passed **11/12**, not 12/12: the inverse query was
still turned into equality of two copies of the inverse predicate, a tautology rather
than the requested assertion. Therefore the retrieval release gate is still failed,
and no typed generation was activated. The separate successful Lean proof of the
original inverse statement does not repair this query observation.

Evidence: `output/dce-matrix-v5-guard-20260930/{summary,first-observations,remaining-observations}.json`.
The final agent unit suite passed 1,805 tests; relevant Ruff and five-module mypy checks
passed. The existing worker/reviewer were updated and source hashes matched; all nine
services were healthy, six networks and ten volumes unchanged, and DB isolation passed.
See `output/dce-matrix-v5-guard-20260930/deployed-source-binding.json`.

The user then requested materially harder commutative-algebra tests. The radical,
localization and Nakayama cases exercise the normal public proof/explanation flow.
Nakayama exceeds the current typed registry; custom generation after retrieval no-match
must retain the original statement and must not be reported as successful typed retrieval.
