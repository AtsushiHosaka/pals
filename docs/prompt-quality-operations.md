# Measure prompt-source changes to ordinary mathematical answers

For the real claim-bound Lean evaluator and deployed standalone infrastructure,
use [the live workflow](prompt-quality-live-operations.md). The direct-runtime
instructions below retain their narrower explanation scope.

The private `pals-observability` workflow evaluates the ordinary natural-answer path.
It scores mathematical correctness, logical completeness, notation consistency,
undergraduate clarity and concision separately. Definitions, assumptions and justified
steps matter; brevity alone earns no credit. Judge scores are estimates, distinct from
online QA approval, task completion, Lean verification and actual learner comprehension.

## Prepare and evaluate

Run from the parent checkout, reusing the existing environments:

```bash
export PYTHONPATH="$PWD/pals-observability/src"
pals-agent/.venv/bin/python -m pals_observability.prompt_quality_runner --help
pals-observability/.venv/bin/python -m pals_observability.prompt_quality_cli --help
```

The runner uses the actual installed agent's `AgentSettings.from_env()` and natural
runtime factory. Configure generation/catalog credentials using normal private
environment handling. `PALS_QUALITY_JUDGE_API_KEY` optionally supplies a separate judge
key; otherwise the generation key is used. Choose an explicit judge model different
from all generator and online QA models. Use provider snapshot identifiers when
available. `--judge-revision` is operator-attested, not verified remote provenance;
matching recorded configuration cannot detect hidden drift behind mutable aliases.

Current upstream composes `ChatRuntime` around the natural proof runtime. The runner
preserves this outer routing. Concept/notation explanations can be evaluated directly.
Proof/solution/correctness requests require the existing live claim-bound Recipe/Lean
flow, which this direct runner does not create; they remain failed with unavailable
quality scores. This implementation does not claim complete proof-pipeline coverage.
Use the existing Lean evaluator for its separate artifact scope; full proof-answer
collection remains a rollout integration task, not a reason to bypass verification.

Start with `pals-observability/datasets/undergraduate-concepts-ja-v1.json`, containing
eight authored Japanese definition/notation/intermediate-step explanation cases.
`pals-observability/datasets/undergraduate-math-ja-v1.json` contains 12 authored Japanese
starter cases: 11 answers/proofs/counterexamples and one domain clarification. The
reference arguments were independently checked during implementation review. This
small set lacks unsupported gold cases, supplied clarification turns and project
materials. Expand coverage and reserve a separate holdout before production decisions.
Keep the complete dataset, references and audience identical across compared variants.
Do not tune on the holdout.

Create a private retrieval manifest using the accepted catalog response's actual
`compatibility.catalog_revision_sha256`, not a name hash or placeholder:

```json
{
  "schema_version": "pals.prompt-quality-retrieval-manifest.v1",
  "catalog_revision_sha256": "<actual lowercase 64-character catalog digest>"
}
```

Observed catalog responses must match this revision. This detects drift rather than
freezing the service. Paths with no catalog request have no response to verify. An
actual retrieval with missing/mismatched provenance rejects the run.

With real configuration, this command makes paid generation/retrieval/judge calls.
Replace example private paths and judge identifiers with real operator values.
It calls the runtime directly without creating/settling customer tasks:

```bash
pals-agent/.venv/bin/python -m pals_observability.prompt_quality_runner \
  --dataset pals-observability/datasets/undergraduate-concepts-ja-v1.json \
  --retrieval-manifest /private/evaluation/catalog-manifest.json \
  --run-id baseline-001 \
  --judge-model ACTUAL_JUDGE_SNAPSHOT --judge-revision ACTUAL_JUDGE_REVISION \
  --repetitions 3 --environment staging \
  --output /private/evaluation/baseline-001.json
```

Run the candidate with identical controls, changing the prompt-source bundle, run ID
and output path. The tool hashes prompt-owning source files, other installed agent
Python files, client/model configuration, dataset and evaluator. Whole prompt-owning
files also contain implementation code: a changed bundle identifies a system variant,
not proof that wording alone caused an improvement. Non-Python data and transitive
dependency versions are not fully attested; reuse the same installed environment and
dependency lock revisions. Source/config drift detected during a run rejects it.

Limits are 256 total case/repetition observations and 10 repetitions per case. Output
is atomic, exclusive and mode 0600. It excludes questions, references, answers and
judge rationales. Failed generation/judging remains visible with null scores, never
invented zeros. Latency is retained. Generation tokens/costs remain null because
existing callbacks cannot attest complete provider-call coverage. Store private
inputs/artifacts outside tracked paths. No background observer is started.

## Compare and visualize

```bash
pals-observability/.venv/bin/python -m pals_observability.prompt_quality_cli summarize \
  --run /private/evaluation/baseline-001.json

pals-observability/.venv/bin/python -m pals_observability.prompt_quality_cli compare \
  --baseline /private/evaluation/baseline-001.json \
  --candidate /private/evaluation/candidate-001.json \
  --output /private/evaluation/comparison.json

pals-observability/.venv/bin/python -m pals_observability.prompt_quality_cli compare \
  --baseline /private/evaluation/baseline-001.json \
  --candidate /private/evaluation/candidate-001.json \
  --format csv --output /private/evaluation/comparison.csv
```

Comparison requires equal environment, dataset, generation configuration, retrieval,
evaluator, models, rubric, audience and exact case/repetition populations. It exposes
paired deltas, improved/regressed/tied counts, missing denominators and failure rates.
Full-population bounds assign unknown scores the possible range [0,1], without
imputing a value. They prevent selective failure from silently appearing as improvement.
Confidence intervals cluster by distinct case; repetitions do not inflate sample size.
Their population interpretation assumes representative independent cases. Inspect
coverage alongside averages and calibrate blind samples with human reviewers. Improved
clarity must not compensate for worse correctness.

CSV is long-form per case/repetition/score, with baseline/candidate outcomes and values
plus delta. Attach it to this chat for paired distributions, correctness/clarity trends
and regression charts. JSON adds uncertainty and coverage. No dashboard app is needed.
The implementation itself has produced no real quality measurements.

## Publish and retrieve

`pals-infra/terraform/prompt-quality/main.tf` defines the dedicated log group with
90-day retention, scoped publisher/reader policies, saved diagnostic score/conflict
queries and `prompt_quality_*` outputs. Apply it through the normal infrastructure
process and attach the policy to the intended operator principal. It is not attached
to the host/worker automatically. No new customer-traffic collection is introduced.

These example commands require an already provisioned staging group:

```bash
pals-observability/.venv/bin/python -m pals_observability.prompt_quality_cli publish \
  --run /private/evaluation/baseline-001.json \
  --log-group /pals/staging/prompt-quality --region ap-northeast-1

pals-observability/.venv/bin/python -m pals_observability.prompt_quality_cli fetch \
  --log-group /pals/staging/prompt-quality \
  --start 2026-11-08T00:00:00+09:00 --end 2026-11-09T00:00:00+09:00 \
  --region ap-northeast-1 --output /private/evaluation/history.jsonl

pals-observability/.venv/bin/python -m pals_observability.prompt_quality_cli compare \
  --baseline /private/evaluation/history.jsonl --baseline-run-id baseline-001 \
  --candidate /private/evaluation/history.jsonl --candidate-run-id candidate-001 \
  --format csv --output /private/evaluation/retrieved-comparison.csv
```

Production Terraform normally uses `environment=prod`: to store an offline benchmark
there, run it with `--environment prod` and publish to `/pals/prod/prompt-quality`.
Environment names the recording/storage cohort, not evidence of a live customer request.
The group must match the record. Use the existing AWS credential chain; `--profile` is
supported. A complete content-free run becomes one JSON log event, with identical
read-back required for success. Uncertain writes are not automatically retried: fetch
before retrying. Retrieval paginates, validates, deduplicates identical retries and
rejects conflicting reuse of a run ID. Use unique non-identifying run labels per group.
Fetch limits are 1,000 runs, 64 MiB and 60 seconds; narrow time ranges when necessary.
Keep private exports for history beyond the log-retention period.

CloudWatch Logs is authoritative; no non-idempotent custom metric increments are used.
Saved queries are diagnostic; strict CLI comparisons support controlled decisions.
Queries use [AWS's supported list expansion](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax-Unnest.html).
The approach follows [fixed-dataset experimentation](https://langfuse.com/docs/evaluation/get-started/offline),
while existing audited Langfuse export contracts remain unchanged. Infrastructure
application, live CloudWatch delivery and actual improvement all need live verification.
