# Live Lean evaluator and rollout evidence — November 9, 2026

Authority: explicit follow-up to implement the missing proof evaluator, deploy, run
actual evaluation and chart results retrieved from CloudWatch. The user selected
their existing PALS account and completed local normal authentication after a
helper defect was repaired. No account was created or credential reset.

## Implementation and verification

- Ordinary owner-scoped chat/quote/request submission preserves the actual queue,
  claim, Recipe and Lean workflow. Catalog and generated-job source bindings are
  independently read and hashed; verification is separate from answer delivery.
- V2 retains pending/unknown submissions and unattempted cases separately from
  terminal failures. Missing/nonterminal evidence remains unavailable, and completion
  latency excludes censored/unsubmitted operations.
- A private fsynced locked journal precedes mutations and supports GET-only recovery.
  Passwords/tokens/raw responses are excluded from CloudWatch records.
- Auth helper debugging reproduced HTTP 403 for Python's default client identity
  and normal HTTP 401 for the explicit PALS client. The request header was corrected.
  Closed step/error diagnostics and private token retention avoid blind repeated
  password prompts. A subsequent real owner, token-capacity and Japanese-language
  preflight succeeded. Credentials remain outside tracked artifacts.
- Exact published observability tree: **1,129 passed, 1 credential-dependent Langfuse
  smoke skipped** in 21.97 seconds. Ruff and strict mypy passed. Actual deployed API
  source contracts accepted the request/quote/terminal/source forms in source checks.
  Boundary fixtures do not count as live proof evaluation.
- Observability commit: `1d08533533a4d6e6a0b88076a995e7594a7f4202`.
- Infrastructure commit including live query repair: `fcad5bbbd883bd42f7cbc9a197974ac815fcc4a7`.

## Actual infrastructure deployment

The standalone `pals-infra/terraform/prompt-quality` root uses the existing encrypted
S3 bucket with a distinct locked key, `pals/prod/prompt-quality.tfstate`.
Provider account guard: 828786775577, ap-northeast-1, existing member profile.
The inspected saved plan added exactly five resources: one 90-day log group,
two unattached scoped policies and two saved queries supporting v1/v2. Apply
completed with **5 added, 0 changed, 0 destroyed**. No application resource, policy
attachment, database schema or running service was changed by this deployment.

Actual AWS query compilation then exposed a saved-query issue that local Terraform
validation did not prove. The summary now flattens cases before aggregation and
uses distinct scalar intermediate aliases. Both candidate queries completed against
the real empty group, without synthetic events. An inspected follow-up plan changed
only the saved summary query: zero creates/deletes and one measurement-query update.
That repair was applied; both deployed queries subsequently completed successfully.
An actual post-deployment plan had already confirmed no infrastructure drift before
the explicit query repair.

Plan SHA-256: `bc91eb3e04e562b2816fb590c72a2a0e711667c8eef56f38dbefe5b9b59d7cc8`.
The log group is `/pals/prod/prompt-quality`. Operator artifacts, plan, source/runtime
attestations and any credentials/results remain in the ignored mode-0700 task output
directory, not this repository's committed evidence.

## Baseline preparation and availability prerequisite

The planned baseline has six proof cases and two concept cases, one repetition,
using the deployed generator and independent provider-available snapshot
`gpt-5.4-2026-03-05`. The account's normal token quota was sufficient at preflight;
the ten-request rolling-hour limit remains enforced. No candidate improvement is
claimed from a single baseline.

Before collection, actual SSM read-back matched the signed sequence-28 release:
API `14e9bf93c9eece11d8e6f2d316936a519ba00610`, worker
`b27f1d8292391567a2ca15f103eb08b18dc016c4`, with seven protected containers unchanged.
The actual eligible Japanese Recipe catalog had 13 entries and SHA-256
`af905dd6d624a1059289397641816ea326075da84375057e5bed1f66df568a03`, read through
the deployed reader in a repeatable-read, read-only transaction. These are runtime
observations, not local/simulator substitutes.

The first benchmark attempt stopped at owner preflight with public HTTP 503, before
creating any chat or proof request. Public web and API were both 503. Read-only
diagnosis found the HTTPS load-balancer target group empty. CloudTrail records
successful removal of its sole target at **00:06:25 JST on November 9**. The shared
SSO caller identifies an operator session, not which chat/person issued it.
The backend itself remained healthy: internal API health/readiness both 200,
unchanged protected containers, zero restarts/OOMs and ready unexpired credential
brokers. The measurement Terraform apply did not touch load balancing.

Ingress restoration must be coordinated with its drain owner. This task did not
blindly reregister the target or interfere with a release. At this evidence point,
there are no proof benchmark outcomes or CloudWatch quality observations to graph.
Resume actual collection after a serving window is confirmed, re-attest deployment
and catalog identities, then publish/fetch and chart only those real observations.
