# Controlled natural-answer experiments

Authority: WORKING contract in [requirements.md](requirements.md). The parent repository
owns this cross-repository design. Implementations belong to private `pals-observability`
and `pals-infra`. Existing dirty files are outside this slice's write ownership.

## Execution and identity

The explicit private evaluator imports the installed `pals-agent` runtime and calls
the factory-composed runtime's `answer` without the SQS processor or settlement APIs.
Current upstream uses `ChatRuntime` around `ProofReuseRuntime`; execution preserves
the outer routing. Direct concept explanations are covered. Claim-bound Recipe/Lean
proof tasks cannot complete without their live worker callbacks and remain failed
with unavailable scores, never an unverified natural-language fallback. Full
proof-answer collection is a separate rollout integration task.
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

`pals.prompt-quality.v1` is a closed JSON object with run identity and up to 256
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

## Storage and operation

A dedicated CloudWatch Logs group stores one complete content-free run per event.
CloudWatch Logs is the authoritative export, avoiding non-idempotent custom metric
increments. A retry may duplicate an event; exporters deduplicate canonical content
and reject a reused run identity with conflicting data. The publisher confirms an
identical event is readable before reporting success. It never creates an unknown
log group or changes IAM. New Terraform policies belong to explicit operator roles,
not the application host by default.

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
After deployment, use an operator-owned holdout dataset, run both variants with
equal controls, publish and fetch them, then inspect paired results and human
calibration before selecting a prompt.
