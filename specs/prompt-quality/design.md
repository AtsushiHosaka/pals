# Controlled natural-answer experiments

Authority: WORKING contract in [requirements.md](requirements.md). The parent repository
owns this cross-repository design. Implementations belong to private `pals-observability`
and `pals-infra`. Existing dirty files are outside this slice's write ownership.

## Execution and identity

The explicit private evaluator imports the installed `pals-agent` runtime and calls
the factory-composed runtime's `answer` without the SQS processor or settlement APIs.
Current upstream uses `ChatRuntime` around `ProofReuseRuntime`; direct execution
preserves the outer routing and covers concept explanations. The separate live
runner creates empty projectless benchmark chats, obtains ordinary billing quotes
when required, submits normal proof requests and polls their owner-scoped API.
Existing workers supply real claims and Lean services; the evaluator never
impersonates a worker or bypasses verification.
Dataset requests and reference evidence remain in operator-owned private files.
Reference evidence goes only to the independent evaluator, never generation.

The dataset digest covers the complete canonical input, references and audience.
The prompt-source bundle digest covers actual installed source files that own prompt
instructions and response schemas. Generation configuration binds actual role/model,
client and retrieval configuration; credentials are excluded. The retrieval manifest
names the expected catalog revision; observed catalog evidence must match when used.
This detects drift rather than claiming to freeze an external service. Missing
provenance blocks a trustworthy run instead of fabricating a version.

The independent judge has a versioned rubric, an explicit requested model and an
operator-attested revision. The provider response must match the requested model,
but mutable aliases can drift without changing these recorded controls. Use snapshot
model identifiers when available; no remote model immutability is claimed. It estimates
five dimensions on [0,1]. Mathematical correctness and clarity are never collapsed
into an accuracy score. For undergraduates, the rubric checks definitions, assumptions,
justified transitions and stable notation. Unattested token/cost totals remain null. Errors retain
their observation and missing score, so the denominator cannot silently shrink.

## Records and comparisons

`pals.prompt-quality.v1` remains the legacy format. The closed v2 format adds a
required per-case formal-verification record: required flag, status, evidence kind
and source/answer/compiler/toolchain hashes. Catalog source/entry bindings are
fetched from the owned source endpoint; generated proofs require the linked
verified job and matching source. Formal success may coexist with failed delivery.
The deployment manifest comes from actual deployed image/source read-back, rather
than local agent source. The operator checks deployment identity before/after the run.
Pending/not-submitted observations are distinct from actual terminal failures.

Records have run identity and up to 256
case/repetition observations, bounded to 256 KiB. Case identifiers are SHA-256
fingerprints. Scores, usage and every nested object's keys are validated before any
export. Local output is exclusive and private; existing artifacts are not overwritten.

Only the prompt-source bundle may differ in a controlled comparison. Environment,
dataset, generation configuration, retrieval revision, evaluator, rubric, models,
audience and case/repetition populations must agree. Paired measurements expose
regressions and missingness instead of comparing unrelated traffic averages.
Full-population delta bounds preserve unknown scores as ranges; outcome rates expose
selective generation failures alongside the paired averages.
Repeated trials are clustered by case when calculating uncertainty. Intervals
describe benchmark sampling uncertainty, not truth or causal guarantees. Holdout
cases must be separated from tuning cases to limit benchmark overfitting.

## Problem registry and repeated prompt experiments

The November 9 user request and issue #316 extend the WORKING contract with
PQ-011–PQ-013. A content-free registry pins each authored fixture and its dataset
revision. Append-only episodes retain source record digests, observation type and
diagnostic category. A later successful observation does not rewrite pending
history. Reviewed explanation weaknesses are distinguished from false mathematical
claims; application projection defects and operational delays are separate categories.

The first controlled iteration reuses verified Lean source bytes whose hashes match
the original benchmark evidence. It calls the production factory's real proof
explainer, strict output parser and grounded reviewer with the existing repair
loop. Both arms generate fresh text; cached catalog/template answers are not a
fresh baseline. A real-client adapter appends only the selected versioned explanation
policy. The baseline suffix is empty. References remain judge-only. The unchanged
production chat projection is applied to both arms before judging, including its
known omission of the structured conclusion. This measures that explanation stage,
not a newly compiled proof, an unchanged catalog answer or a deployed product gain.

Before paid calls, the explicit command freezes fixture/source hashes, prompt
policies, generator/reviewer/judge settings, projection, repetitions and interleaved
order. A private durable journal prevents an uncertain provider call from being
blindly replayed. Content-free arm records use the existing closed schema; stage
and registry lineage stay in sidecars. An ordered iteration manifest selects runs
from a validated CloudWatch fetch. Every comparison uses the existing strict paired
comparator; unrelated observations and regrades never form a connected improvement
curve. Repeated measurements preserve failures and missing scores. The exposed
starter corpus is tuning/regression material, not an independently blind holdout.

## Answer analysis and corpus expansion

Issue #317 and the next November 9 user request extend the WORKING contract with
PQ-014/PQ-015. Inspect the actual rejected drafts, repaired drafts, delivered prose
and reviewer reasons before choosing the next generic policy. Keep source terminology
errors and misleading ordering separate from false mathematical conclusions. A
reviewer's refusal may itself be wrong. The API projection defect is a separate
application contract and stays fixed in prompt-only comparisons.

The original three-case manifest and frozen collector remain usable unchanged for
longitudinal measurements. New authored proof problems form a separate population.
Actual installed Lean and Mathlib compile the exact source files with a bounded
command and a standard-axiom audit. A separate local-compile authority adapter may
validate those real artifacts and call the same production explanation/review loop.
It binds its own implementation and authority provenance in the generation controls,
and explicitly labels local compilation versus the explanation replay stage. It
never fabricates a v2 live measurement as proof authority. Unavailable or invalid
compiler evidence blocks only the dependent new-case replay.

Before model calls, freeze each population, references, policy, order, repetition
count and source/authority digests. Each baseline/candidate pair has the same controls.
Report the stable core and additional problems separately; different corpus or
collector controls cannot be joined into a single controlled improvement curve.

## QA and conclusion implementation treatment

The next user request and issue #319 authorize PQ-016/PQ-017. Source inspection
confirms that the current production API still omits conclusion, while the existing
production-source branch already contains the ce5cd2f projection fix. Reuse that
narrow change. A task-owned worker candidate adds only reviewer evidence-grounding
instructions; generation, parsing, model roles, checklist and repair limits stay
unchanged. Fixed valid and invalid mathematical explanations test the actual review
model; approval alone is not sufficient acceptance evidence.

This is a joint QA-plus-projection treatment. Both arms use the exact same v4
generation suffix. Fresh Python workers load one pinned agent/API source per arm,
because global module names cannot safely hold both source trees in one process.
Separate private journals preserve arm identity and uncertain-call recovery. A
parent orchestrator alternates the same six case/repetition inputs, validates the
reviewed component differences before paid calls, and retains actual source and
configuration hashes in the closed records.

The original strict prompt comparator remains unchanged. A dedicated treatment
comparison validates raw identities, pinned configurations and allowed code
differences before computing paired statistics. It must not normalize fingerprints
or hide source drift. The fixed projection executes the actual ordered production
AST, including the append and text-size guard; selecting only assignment nodes
would silently discard the fix. Owning API tests compare it with the real helper
and verify persistence, fresh reads and history. Production rollout/acceptance is
a separate release contract and is not implied by a successful local experiment.

## Storage and operation

A dedicated CloudWatch Logs group stores one complete content-free run per event.
CloudWatch Logs is the authoritative export, avoiding non-idempotent custom metric
increments. A retry may duplicate an event; exporters deduplicate canonical content
and reject a reused run identity with conflicting data. The publisher confirms an
identical event is readable before reporting success. It never creates an unknown
log group or changes IAM. New Terraform policies belong to explicit operator roles,
not the application host by default. The independent Terraform root is
`pals-infra/terraform/prompt-quality`, with encrypted/locked S3 state at
`pals/prod/prompt-quality.tfstate`. The inspected saved plan contains only five
measurement resources and does not use the application's state key.

The live command accepts a mode-0600 access-token file. A local terminal helper
uses normal Cognito authentication, retains only the access token after the PALS
owner check, and never stores the password. Account challenges remain on the website.
A locked private append-only journal records mutation intent, returned identifiers,
terminal state and measurements. Ambiguous submissions recover with read-only calls;
the normal ten-request rolling-hour limit and product credits remain enforced.

The CLI emits summary JSON and paired JSON/CSV suitable for charts in this chat.
Recording environments `dev`, `staging` and `prod` match Terraform; `offline` is
also a local recording label and needs a separately provisioned matching group
if explicitly published. The default is not evidence of provisioned infrastructure.
No dashboard application or automatic production feedback loop is introduced.
Existing Langfuse schema-v2/DSP projections remain intact: their audit and privacy
constraints are independent. The new records are usable without activating Langfuse.

## Verification and rollout boundaries

Run closed-schema, paired-comparison, provenance, runner, publisher/read-back and
pagination tests, then existing observability regressions and relevant static checks.
Isolated provider tests prove boundary contracts, not provider execution. Terraform
format/schema validation proves configuration, not applied infrastructure. No live
model run, Terraform apply or CloudWatch ingestion is implied by these checks.
The source-controlled datasets contain eight concept/notation cases usable on the
current explanation route and 12 proof/counterexample/clarification cases. They are
authored, independently checked starter corpora, not human calibration or
broad production coverage. Non-Python assets and transitive dependency versions
remain outside the current source fingerprint; reuse the same environment and locks.
After deployment, establish a real baseline using the selected account, publish/read
back/fetch it, and render the fetched observations. A later distinct candidate can
be compared with matching controls and a holdout dataset. Human calibration remains
necessary before selecting a prompt from small benchmark changes.

## Further generator-policy experiments

Issue #321 authorizes another bounded policy improvement. Both arms use repaired
agent64f01b8 and the ce5cd2f conclusion projector; only the generator suffix differs.
The v4 baseline is byte-identical to the prior v4 policy. A new policy-pair schema
allows two identified nonempty suffixes without weakening the older empty-baseline
loader. A manifest selects an explicit population and verifies all controls and
content-free case/source inventories, including disjoint development/holdout cases.
The original strict comparator must accept the untouched records.

Candidate design uses only the exposed six-question evidence. Another agent authors
and actually compiles three substantive fixtures without reading the candidate.
The question/reference content remains sealed during development. At most two
development candidates are measured, retaining failed attempts. A final selected
policy is frozen before opening the additional population; an exclusive stable
marker binds that policy/source identity and private journal, allowing observation
recovery but preventing adaptation followed by a second opening. Fresh v4 and
candidate runs use two repetitions per case with fixed source/model/judge/rubric
and execution limits. Individual changes, delivery failures and unavailable scores
remain explicit; historical collector changes never become an uncontrolled gain.

The recorded selection preference is no delivered-answer or confirmed-content
regression, nonnegative clarity and concision case means, and at least one positive
mean; it is exploratory and never production promotion. Added authored cases and
LLM grades do not replace a representative sample or human calibration.

## Quality and efficiency continuation, issue323

The next iteration preserves all previous measurements and distinguishes fixed-output QA decisions from fresh policy-only explanation replay. The repaired reviewer is tested on fixed positive/negative contrasts before its runtime is frozen for a new generation-policy comparison. A valid source-level prompt or transport-boundary unit test does not establish real-model acceptance, correct rejection rationale, or production behavior.

Efficiency capture observes the already returned real provider response. It does not resubmit model calls or modify generation settings. Generation and publication-review usage form product-stage totals; independent judging is reported separately. Historical token fields without raw usage stay null. Actual counts and elapsed times can be derived from durable completed-call journals without inventing token estimates or billed USD. Counter capture failure is explicit and blocks further unobserved calls. Closed standard records retain only supported numeric usage fields; detailed private receipts bind the selected records and call-stage totals.

The nine exposed proof fixtures are development/regression inputs. Six further independently authored, actually compiled proof fixtures stay sealed during candidate design. The selected runtime and policy are frozen before one additional-population evaluation. Improvements, regressions, observed condition mismatches, false refusals, legitimate refusals, missing scores and resource observations remain in the same evidence package. A shorter instruction is a design hypothesis, not measured token or latency savings.

The additional-population measurement freezes old/new QA source × v6/v8 policy with two repetitions,48 unique trials. Source-only contrasts use `compare_review_runs`, which pins allowed review-source/AST changes and validates actual opening markers against their own freeze and private journal. Operational marker paths may differ; collisions or missing/incorrect bindings fail. Its explicit preflight path accepts only entirely unmeasured zero-latency/all-null placeholders and cannot validate measured results. Existing strict policy comparisons and earlier treatment contracts remain unchanged. The second-candidate measurement-selection and400-to500 call-limit amendments were recorded before opening; failed screening remains failed screening. Final measurements do not authorize production promotion or reuse of the opened population as unseen evidence.
