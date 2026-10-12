# Local Lean runtime recovery — 2026-10-13

Local Lean is operational: the unchanged coprime-divisibility fixture compiled natively and through the real isolated mTLS verifier. This establishes compiler and verifier success. The model-generated PALS chat answer remains unverified; production Lean remains a separate activation task.

## Recovery

The existing local stack was reused. PostgreSQL, LocalStack and Cognito were stopped. PostgreSQL's fixed database address was occupied by the dynamically attached reconciler. Stopping only API/reconciler, starting the existing PostgreSQL container, and restarting API/reconciler restored the database without changing its container or named volume. API and Web returned HTTP200.

The verifier/reconciler's exact LocalStack TLS secret versions no longer existed. `bootstrap-local-verifier-tls.py` generated replacement local material bound to the actual existing verifier image/toolchain. Only verifier/reconciler were recreated for that rotation. Complete Docker configuration, environment, host settings and network creation fields were checked against private snapshots; private keys were neither published nor committed. The former containers remain stopped rollback archives. No database migration, reset, queue purge or old-secret deletion was performed.

The repaired release is `c91c1a93-d78c-4432-a20e-0cac20d08528`, binding `9d57f742e7e2636331b7b72f124166472e49d19a428041779a20e88c045d39f4`, verifier image `sha256:825c2426544d7305324669510907cfcd955d4312000407f7928e0eaf402e6d3f`. API, Web, worker, PostgreSQL, LocalStack, Cognito, reviewer, verifier and reconciler are healthy. Existing unrelated application containers were preserved.

## Compiler evidence

The exact tracked source is [coprime-divisibility.lean](../pals-scripts/fixtures/coprime-divisibility.lean), SHA256 `2b22702ef3feadeb2669fad0979d7a17aae84a91633154e251cdbafc71f89dfd`.

- Native Lean4.32.0-rc1, commit `b4812ae53eea93439ad5dce5a5c26591c31cb697`, reused the existing Mathlib cache at commit `8b62164d808cd0f23b7d8cc28190a6c1a1bb483a`. The unchanged source exited0 in5.375 seconds, with no compiler output.
- The existing reconciler's strict client verified TLS1.3 mTLS readiness and submitted that same source with a fresh task-owned UUID. The actual verifier returned `pals.verifier-attestation.v1`, `verification_succeeded=true`, matching source hash, UUID `4c528830-b1a2-4d85-8e9e-585e5616f81f` and task-owned artifact URN. This direct fixture check constructed no database repository and wrote no business record or result artifact.
- The actual isolated container reports Lean4.32.0-rc1 with that same compiler commit. Its correct version command is `docker exec -w /app/lean-workspace pals-local-verifier-1 lake env lean --version`; `/app` alone does not select its Lean toolchain.

The straightforward native command also exited0 against the existing cache, without updating dependencies:

```sh
cd /Users/atsushi/Desktop/projects/personal/pals/pals-agent/lean-workspace
/Users/atsushi/.elan/bin/lake env lean /Users/atsushi/.codex/worktrees/ac7d/pals/pals-scripts/fixtures/coprime-divisibility.lean
```

## Worker repair and remaining chat boundary

A normal guest request at `http://localhost:3000/try` asked for coprime divisibility. It created request `e81fd032-ea85-48ba-a871-1cecdfb9547d`, formal job `ff673933-50ec-4dcf-92f6-834594459cf8`. Real Lean compilation rejected generated candidates; their source was never manually replaced with the successful fixture.

During repair, an embedding response disconnected with `BrokenPipeError` outside the existing embedding exception boundary. The worker restarted at15:24:29UTC, after acquiring the queued job's one-hour generation lease. Read-only inspection found zero visible and one hidden delivery; the persisted job remained at sequence33, repair5 of12, with a failed candidate. There was no active Lean compiler. Its claim expires at16:23:48UTC (01:23:48JST).

[Agent PR11](https://github.com/AtsushiHosaka/pals-agent/pull/11), commit `78b71032ccf0e5e08488db0aeb53bee6cdb6dc41`, normalizes socket and truncated HTTP failures to the existing closed `EmbeddingError`. Provider failure cannot supply a fallback vector; metered accounting remains unchanged. Seventy-four focused provider, retrieval, accounting and worker checks passed, Ruff/diff checks passed, and independent review found no blocking defect.

The local worker now uses derivative image `sha256:e33c46a83c628b9d011a7726e1a9659aaa0aedb3ed98a89828772b07bca6947e`, built from its exact preceding image without dependency installation. Only the two installed copies of `draft_embeddings.py` changed; both match tested SHA256 `068c6d55109164374e527a4cfd5448b0a1eba82039379eec85198f6159a6bb3e`. Full environment, configuration except image, host settings and network creation fields were verified unchanged. The original worker remains stopped for rollback.

The chat's active-request guard prevents starting a second question. Preserve that guard and the existing claim: normal queue redelivery must acquire a fresh guarded claim after expiry. The intentionally closed repair diagnostics provide a compiler-error category and location, rather than raw Lean output. No delivered `lean_verified` answer, explanation or learner-opened source has been observed for this generated request. That remaining boundary must be checked before claiming the PALS chat flow is repaired.

The [public rollout evidence](public-lean-runtime-repair-2026-10-12.md) retains the production AWS sign-in and memory-capacity prerequisites. Local compiler success does not resolve them.
