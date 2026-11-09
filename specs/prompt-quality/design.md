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
