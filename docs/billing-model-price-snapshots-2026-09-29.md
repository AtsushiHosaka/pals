# BILL-010 model price registry correction — 2026-09-29

Working scope: the current API `858dd16` / agent `ab42335` baselines plus existing uncommitted changes. Normal production roles in `pals_agent/model_roles.py` all resolve to `gpt-5.4-mini-2026-03-17`; local configuration also names the mini and nano families. The old usage reporter and API registry accepted only the undated nano identity, so actual fixed-release calls were not recorded. **Previously unrecorded usage remains missing; no historical calls or token counts are fabricated.**

Official OpenAI model pages were checked on 2026-09-29. They list both the undated aliases and the exact `2026-03-17` snapshots, with these standard text-token USD prices per million tokens:

| Model | Input | Cached input | Output | Primary source |
|---|---:|---:|---:|---|
| GPT-5.4 mini | $0.75 | $0.075 | $4.50 | [OpenAI mini model and snapshots](https://developers.openai.com/api/docs/models/gpt-5.4-mini) |
| GPT-5.4 nano | $0.20 | $0.02 | $1.25 | [OpenAI nano model and snapshots](https://developers.openai.com/api/docs/models/gpt-5.4-nano) |

New price IDs are `openai-gpt-5.4-mini-2026-09-29` and `openai-gpt-5.4-nano-2026-09-29`. Each allows only the exact undated family name and its listed `2026-03-17` release. Unknown dates, model suffixes, providers, and model/snapshot mismatches are rejected. The old nano `2026-08-19` price identity and rates remain unchanged in the API for persisted-event replay. No schema migration is needed; deploy the API registry before the new worker reporter.

Existing conservative estimation is preserved: all input tokens, including cached tokens, use the ordinary input rate. Cached tokens are stored as a subset, not added again. Reasoning tokens are also a stored subset of total output, not a second charge. API-owned rates are integer microUSD per million tokens; cost is `ceil((input × input_rate + output × output_rate) / 1_000_000)`, with no floating-point rounding. This is a standard text-token estimate, not an invoice or a claim about regional processing, priority, batch, tool, or embedding fees. The configured embedding model has a separate transport and is not silently treated as text generation.

Checks executed without model calls:

- Agent: `pytest -q tests/unit/test_usage_reporting.py tests/unit/test_openai.py` — **18 passed**. Exact fixed releases and aliases emit content-free counters; unknown releases warn without sending fabricated usage or changing generation behavior.
- API: `pytest -q tests/unit/test_billing_runtime.py` — **14 passed**. Exact rates, microUSD rounding, subset semantics, safe-integer bound, unknown identities and historical nano behavior.
- Actual PostgreSQL: `pytest -q tests/integration/test_billing_runtime_postgres.py -k usage_current_claim` — **5 passed**. All four new identities plus historical nano persist the expected cost, exact replay stays idempotent, conflicting usage and invalid claims fail. Existing local PG was reused with a dedicated disposable DB, removed by fixture cleanup; learner rows were not used.
- Cross-repository check: actual agent serializer → API `UsageRequest` → API estimator for all four new identities; all nine release roles resolve to a registered identity. Scoped Ruff, mypy and diff checks passed.

Live provider-call persistence after redeployment remains to be checked by the parent runtime task. This correction does not retroactively establish completeness of usage from earlier jobs, or extend the existing generation-claim metering scope to other operations.
