# Live proof and explanation evaluation

The November 8 follow-up authorizes completing the proof evaluator, deploying the
measurement infrastructure and running actual evaluations. The selected account is
the user's existing PALS account. This workflow creates private benchmark chats and
normal proof requests; it does not impersonate a worker or bypass claims, billing,
Recipe admission, Lean verification or independent answer review.

## Authentication

Use the existing app's Cognito client and a private token file. With `PYTHONPATH`
pointing to `pals-observability/src`, invoke `python -m
pals_observability.prompt_quality_login --client-id <actual-public-client-id>
--output <private-token-path>`. Enter credentials only in the local terminal.
The password is never stored or passed as a shell argument. A Cognito access token
is stored in a mode-0600 owner-private file; the normal PALS `/v1/auth/me` check
then verifies owner access. If this later check fails, the token remains private
and a retry checks it without asking for the password again. Challenges and password
changes remain on the normal website. Neither passwords nor tokens belong in chat.

The API client identifies itself as PALS-PromptQuality. The original helper's default
Python client received an HTTP 403 at the API boundary. This was reproduced without
credentials, repaired, and followed by successful owner/quota preflight using the
user's local token. Diagnostics now expose only the failing step and closed error
code, not the Cognito message, email, password, token or raw response.

## Infrastructure

Use `pals-infra/terraform/prompt-quality`, independent of the application Terraform
root. Initialize S3 with the existing encrypted bucket and the separate key
`pals/prod/prompt-quality.tfstate`, `encrypt=true` and `use_lockfile=true`.
The provider guards account 828786775577 in ap-northeast-1 using the existing
`pals-prod-member` profile. Inspect the saved plan before apply: it must contain
only one log group, two unattached scoped policies and two saved query definitions.
No application resource or IAM attachment is needed.

The reviewed plan was applied successfully: five added, zero changed/destroyed.
The group is `/pals/prod/prompt-quality`, with 90-day retention. Both saved queries
recognize v1 and v2 records. Actual publication/read-back is a separate live check.

## Dataset and deployment identity

`pals-observability/datasets/undergraduate-live-ja-v1.json` contains six proof cases
and two concept cases. Its closed live-dataset schema includes the original request,
expected outcome, reviewed reference and explicit `requires_lean` flag. References
are sent only to the independent judge. Current live submission supports text-only
initial requests; supplied clarification turns/material attachments are rejected
before spending rather than silently omitted. One run uses at most ten cases and
does not bypass the normal rolling-hour request limit or account credits.

A private `pals.prompt-quality-deployment.v1` manifest records the actual API origin,
deployment/source/configuration/catalog digests, selected generator and every
generation/QA/intent model. Build it from deployment read-back, not local HEAD.
Hash the nonprompt implementation, real model/reasoning/quote configuration and
toolchain separately from prompt-owning sources. Do not include secrets or user IDs.
Check the deployed image/source and catalog identities before and after collection;
the collector cannot freeze a remote release or detect hidden provider alias drift.
All runtime model identities must be listed so the judge can be independent.

## Execute and resume

```bash
python -m pals_observability.prompt_quality_live \
  --dataset pals-observability/datasets/undergraduate-live-ja-v1.json \
  --deployment-manifest /private/evaluation/deployment.json \
  --access-token-file /private/evaluation/access-token \
  --run-id seq28-baseline-001 \
  --output /private/evaluation/baseline.json \
  --journal /private/evaluation/journal.jsonl \
  --judge-model gpt-5.4-2026-03-05 --judge-revision gpt-5.4-2026-03-05 \
  --generation-reasoning-effort medium --environment prod --max-cases 8
```

The selected judge snapshot was available in the configured provider account and
is distinct from deployed generation/online-review/intent models. The judge uses
4,000 output tokens and low reasoning, fingerprinted with its rubric and code.
The first run establishes a baseline; there is no improvement claim without a
separate candidate under matching controls and a defensible holdout.

The locked mode-0600 append-only journal records intent before POSTs and stores
returned IDs, terminal responses and measurements privately. Uncertain submission
is recovered through GET-only lookup. Authorization/rate failures stop further new
submissions. A timeout leaves a real pending task; it never claims cancellation or
terminal failure. An unattempted case is `not_submitted`. Use the same journal/run
identity for explicit resume; missing judging can be retried without generation.
Keep API errors and partial-run evidence private and inspect them before retrying.

## Formal evidence and interpretation

For `lean_catalog`, fetch the owned historical Lean-source endpoint and verify
request/chat/Recipe/revision/entry/compiler/toolchain bindings. Recompute Lean-source
and displayed-answer hashes. For `lean_verified`, inspect the matching linked job,
require its state/status/stage to be verified, fetch its owned source and recompute
the Lean hash. Answered or QA approval alone never establishes verification.

A generated proof can be verified while its explanation fails. V2 records retain
that distinction. Missing/nonterminal evidence is unavailable; observed terminal
failed/canceled proof jobs are not verified. Required-proof counts remain the fixed
denominator. Completion latency excludes pending/unsubmitted work; pending elapsed
time is a censored lower bound. Quality scores remain independent LLM estimates.

Use the ordinary `prompt_quality_cli publish`, `fetch` and `summarize` commands.
Publish only the intended final immutable collection: the same run ID with changed
data is a conflict, not an update. Confirm identical read-back, fetch JSONL from
CloudWatch, then build graphs from those fetched records. Show sample sizes, missing
scores, incomplete observations and the distinction between formal verification and
answer delivery. Do not replace missing results with synthetic examples.
