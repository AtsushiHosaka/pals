# Local Lean runtime recovery — 2026-10-13

Local PALS now delivers a model-generated Lean-verified answer and explanation. The learner-opened source matches the accepted candidate, compiler attestation and answer source hash. The unchanged coprime-divisibility fixture also compiled natively and through the isolated mTLS verifier. Production activation remains a separate task.

## Recovery

The existing local stack was reused. PostgreSQL, LocalStack and Cognito were stopped. PostgreSQL's fixed database address was occupied by the dynamically attached reconciler. Stopping only API/reconciler, starting the existing PostgreSQL container, and restarting API/reconciler restored the database without changing its container or named volume. API and Web returned HTTP200.

The verifier/reconciler's exact LocalStack TLS secret versions no longer existed. `bootstrap-local-verifier-tls.py` generated replacement local material bound to the actual existing verifier image/toolchain. Only verifier/reconciler were recreated for that rotation. Complete Docker configuration, environment, host settings and network creation fields were checked against private snapshots; private keys were neither published nor committed. The former containers remain stopped rollback archives. No database migration, reset, queue purge or old-secret deletion was performed.

The initial TLS repair used release `c91c1a93-d78c-4432-a20e-0cac20d08528`. After applying the closed diagnostic repair, the current local release is `095967d8-07d2-4263-9813-db1a076f7f17`, binding `d1052ee798658ec0a92cf058b47b54d9d1d668707342b115ed4e8a8e4228cde3`, verifier image `sha256:305f0aee3ccd30e6d5c3a66015fd06404696152d9556003ae0f7617a3fb95fac`. API, Web, worker, PostgreSQL, LocalStack, Cognito, reviewer, verifier and reconciler are healthy. Existing unrelated application containers were preserved.

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

## Worker and diagnostic repair

A normal guest request at `http://localhost:3000/try` asked for coprime divisibility. It created request `e81fd032-ea85-48ba-a871-1cecdfb9547d`, formal job `ff673933-50ec-4dcf-92f6-834594459cf8`. Real Lean compilation rejected generated candidates; their source was never manually replaced with the successful fixture.

During repair, an embedding response disconnected with `BrokenPipeError` outside the existing embedding exception boundary. The worker restarted at15:24:29UTC, after acquiring the queued job's one-hour generation lease. Its claim expired normally at16:23:48UTC; the delivery then acquired a fresh guarded claim. No queue visibility, claim, source or quota was manually changed.

[Agent PR11](https://github.com/AtsushiHosaka/pals-agent/pull/11), merged as `1148de9e328945532f0b620870ab06178a47b13e`, normalizes socket and truncated HTTP failures to the existing closed `EmbeddingError`. Provider failure cannot supply a fallback vector; metered accounting remains unchanged. It also exports the exact Lean error “No goals to be solved” as additive `lean.no_goals`, with a fixed repair instruction to remove the redundant tactic while preserving the theorem. Raw compiler output remains private. [API PR14](https://github.com/AtsushiHosaka/pals-api/pull/14), merged as `bc698c7c30411debcc470fd920ca94c8771634ac`, preserves that closed vocabulary through settlement and readback. Seventy-four focused transport checks,114 agent verifier/repair checks and44 paired API checks passed. Ruff/diff checks passed; independent review found no blocking defect.

The local roles use derivative images built from their exact preceding images without dependency installation. API/reconciler changed only the compiler-feedback module; verifier changed only the HTTP diagnostic module; worker changed only the embedding module and the closed repair-message mapping in both installed copies. The worker's older installed package was preserved outside those reviewed changes. Complete image configuration and base layers, container environment, host settings, mounts and network creation fields were verified against private snapshots. The original containers remain stopped for rollback.

The compiler toolchain fingerprint remains `825c2426544d7305324669510907cfcd955d4312000407f7928e0eaf402e6d3f`: compiler, workspace and LeanVerifier implementation are unchanged. The local strict deployment binding distinguishes the new image digest from that compiler fingerprint and binds fresh mTLS material to the actual image. Existing catalog admission was retained. This local evidence does not change production release-envelope rules.

## Delivered generated proof

Normal redelivery resumed the original formal job. A failed candidate produced `lean.type_mismatch` and `lean.no_goals`; durable events38 and39 show the closed feedback was settled and consumed by normal repair. The next candidate compiled successfully in46.163 seconds at16:27:26.214743UTC, sequence44, repair7 of12. Explanation completed at16:28:07.846199UTC and the original request became `answered` at16:28:19.109384UTC.

The answer has `evidence_kind=lean_verified`, source type `proof_job`, and formal job `ff673933-50ec-4dcf-92f6-834594459cf8`. Accepted candidate, successful compiler attestation, answer and learner-opened source all match SHA256 `8b4d98f9a810f42a1d6ab43095d6d4d9c01c31f9a746232ce772439a616900b4`. The source panel was opened through its visible learner control and its rendered text was hashed unchanged. This is a generated Bézout-based proof, not the fixture substituted into the job. The sanitized private delivery-evidence file has SHA256 `32a3628e5f89ec34b5a04dffea3e28da995bac198a7c74876d5b0a0774f5f1a9`; raw source, runtime snapshots and provider output are not committed.

The [public rollout evidence](public-lean-runtime-repair-2026-10-12.md) retains the production AWS sign-in and memory-capacity prerequisites. Local compiler success does not resolve them.
