# Lean acceleration: measured environment-reuse slice

Date: 2026-10-28 JST. Status: bounded implementation for review; full T5 and
MRD-009 remain incomplete. No activation, merge or deployment is established.

## Authority and pinned inputs

- Working MRD-007/008/009 and T5 at parent roadmap commit
  `48c9be131b63eaabee58463c8a0fd601ca0119e3`.
- Requirements SHA-256:
  `16c3fbdd8b925b168d534343fb85abb385a843fc6f2236fb667cad971bdacf9c`.
- Parent implementation base: `ca84e6fe1a87fa019368f16e4af8c7cbec759a82`.
- Agent implementation base: `4703690c4125eed18fcce9269ce4f1dbc6ff577d`.
- Agent review head: `12054624cdbb510d53c5f055079c76a9882f759d`,
  [draft PR #20](https://github.com/AtsushiHosaka/pals-agent/pull/20).
- Lean: `4.32.0-rc1`, Darwin arm64, compiler commit
  `b4812ae53eea93439ad5dce5a5c26591c31cb697`.
- Mathlib: `8b62164d808cd0f23b7d8cc28190a6c1a1bb483a`.

The supplied earlier prototype directories were absent and the supplied local
implementation commit was unavailable in the accessible agent object databases.
No prototype code was copied. Current sources and the installed pinned runtime
were inspected instead. Existing Python dependencies and installed Mathlib
artifacts were reused in place; no app/container/dependency stack was duplicated.

## Changed behavior

The isolated verifier can opt into process-local Lake environment reuse with
`PALS_LEAN_REUSE_LAKE_ENVIRONMENT=true`; its default is false. The production
composition enables it only after the existing read-only workspace and resource
boundary attestation. It caches one reviewed environment delta, not a proof
verdict, generated module or catalog entry. Every source still executes a fresh
bounded Lean child. No compiler process is kept alive.

The environment key includes platform, resolved executable paths and bytes,
closed child configuration, manifest/config bytes, resolved dependency topology
and evaluated Lake config artifacts. Dependency Lake config changes invalidate
setup. Unknown or scratch-dependent keys and unsupported topology trigger the
original compiler command, with a visible `fallback` metric and the remaining
deadline. Only Lake's exact default HOME-based config path is rebound to the
fresh request HOME. A known Darwin child-runtime key is discarded on Darwin.
The process cache serializes preparation, returns independent dictionaries, has
one-entry capacity and supports explicit reset. Restart creates a new cache.

Fresh compilation checks the requested source, imports and instantiation against
the installed trusted environment; it does not rebuild or certify deployment
artifacts. An environment-key hit never certifies a source or module. The key is
not an artifact trust certificate and does not authorize importing arbitrary
`.olean` files. Installed modules retain their deployment provenance boundary. Mutable executable Lake
configuration is unsupported for production reuse, including its transitive
inputs beyond the enumerated key files.

Proof-job verification keeps its existing source binding and response format.
Recipe admission uses a separate uncached verifier because its receipt binds
the literal `lake env lean --threads=1 Main.lean` command. Independent review
identified this receipt issue in the initial implementation; it was repaired
before publication and tested through runtime composition and mTLS dispatch.

The verifier emits source-free stage durations: environment identity,
environment preparation with miss/hit/fallback, compile and total. Preparation
encloses identity; stages are not additive. Baseline compile includes Lake setup;
cached compile excludes it. Import loading and elaboration are not separately
instrumented in this slice.

## Verification

Agent repository commands, using the existing Python environment:

```sh
python -m ruff check pals_agent/lean.py pals_agent/lean_environment.py \
  pals_agent/lean_verifier/http_runtime.py pals_agent/lean_verifier/http_server.py \
  tests/unit/test_lean_environment.py tests/unit/test_http_verifier_runtime.py \
  tests/unit/test_isolated_verifier_http_server.py \
  tests/integration/test_lean_acceleration_real.py tools/lean_acceleration
python -m mypy --explicit-package-bases pals_agent/lean.py \
  pals_agent/lean_environment.py pals_agent/lean_verifier/http_runtime.py \
  pals_agent/lean_verifier/http_server.py tools/lean_acceleration/benchmark.py \
  tests/integration/test_lean_acceleration_real.py
python -m pytest tests/unit/test_lean_environment.py tests/unit/test_lean.py \
  tests/unit/test_lean_process_boundary_spec.py tests/unit/test_http_verifier_runtime.py \
  tests/unit/test_isolated_verifier_http_server.py \
  tests/unit/test_lean_boundary_attestation_spec.py \
  tests/unit/test_lean_container_contract_spec.py tests/unit/test_lean_target.py \
  tests/unit/test_pipeline.py tests/unit/test_proof_reuse_lean_flow.py \
  tests/unit/test_proof_reuse.py tests/unit/test_proof_reuse_catalog.py \
  tests/unit/test_verifier_tls_material.py
```

The regression selection passed **247 tests**. Lint, type checks and whitespace
checks passed. Independent SDD/architecture review found no remaining P0/P1/P2
defect in the reviewed bounded slice after the admission repair; the final
containment guard was reviewed at agent commit
`12054624cdbb510d53c5f055079c76a9882f759d`.
Hosted PR checks showed only a skipped CodeRabbit check; hosted compiler/test
CI success is not established. The checks above are local evidence.

Real integration used explicit installed Lean/Lake binaries and the existing
trusted workspace via `PALS_ACCELERATION_REAL_PROJECT`,
`PALS_ACCELERATION_REAL_LEAN`, `PALS_ACCELERATION_REAL_LAKE`:

```sh
python -m pytest tests/integration/test_lean_acceleration_real.py
python -m tools.lean_acceleration.benchmark \
  --project-dir /absolute/trusted/lean-workspace \
  --lean-binary /absolute/pinned-toolchain/bin/lean \
  --lake-binary /absolute/pinned-toolchain/bin/lake \
  --repeats 5 --output /tmp/pals-t5-lean-environment-benchmark.json
```

All **5 real integration tests passed** in 96.48 s. The four substantive proof
bodies cover group-homomorphism injectivity from a trivial kernel, an epsilon
proof of sequence-limit addition, coprime product divisibility and the kernel
of a sum of linear maps with disjoint ranges. Each compiles under broad and
explicit imports. Every cached-mode request compiles again; each family showed
an actual setup miss then hit. A concurrent valid source succeeded while a
false target failed; clearing the cache forced preparation again. The local
two-call concurrency probe does not change the production server's one-slot
compile policy or establish production throughput.

## Final local measurements

The final run at agent revision `12054624cdbb510d53c5f055079c76a9882f759d`
completed with 81 successful source samples and 81 fresh compiler events,
including one separately recorded warmup. All 20 cold samples missed the setup
cache; all 20 warm samples hit; none fell back. Narrow-source hashes were
identical across baseline, cold and warm modes for each family. Production and
harness source hashes were checked before and after measurement; no drift was
found. An earlier exploratory run is excluded from these results.

| Mode | Samples | Wall p50 (s) | Wall p95 (s) |
| --- | ---: | ---: | ---: |
| Baseline, broad Mathlib | 20 | 7.836 | 8.499 |
| Baseline, explicit imports | 20 | 3.676 | 4.783 |
| Explicit imports, cold setup cache | 20 | 3.747 | 4.610 |
| Explicit imports, warm setup cache | 20 | 1.354 | 2.147 |

Per-family p50/p95 seconds, five samples in each cell:

| Family | Broad | Explicit baseline | Cold setup | Warm setup |
| --- | --- | --- | --- | --- |
| Group kernel/injectivity | 7.740 / 8.274 | 3.229 / 4.172 | 3.738 / 4.231 | 0.751 / 1.285 |
| Sequence limit addition | 8.009 / 8.927 | 4.403 / 4.845 | 3.974 / 4.414 | 1.655 / 3.889 |
| Coprime product divisibility | 7.490 / 8.048 | 3.565 / 3.722 | 3.504 / 3.967 | 1.424 / 1.988 |
| Linear kernel sum | 7.861 / 8.078 | 3.670 / 4.181 | 4.452 / 9.718 | 1.748 / 2.147 |

Cold setup preparation p50/p95 was 2.512/3.167 s; warm preparation was
5.54/10.92 ms. Fresh compile p50/p95 was 1.292/1.911 s in cold mode and
1.346/2.137 s in warm mode. Setup was a substantial measured cost in this
local narrow-import workload; warm setup avoids it while still recompiling.
This does not identify the end-to-end application bottleneck.

Maximum individual child RSS across the combined run was **5,449,842,688 bytes
(about 5.08 GiB)**. The cumulative maximum cannot identify the responsible mode,
measure concurrent aggregate RSS, or establish fit within the production
verifier's 4 GiB container. Darwin does not apply the Linux address-space/outer
container limits. Production memory validation remains required before any
activation; no production resource limit was changed.

Local raw evidence is retained at
`/tmp/pals-t5-lean-environment-benchmark.json` (generated output is not committed).
SHA-256: `6f77f9d84eb027b03f30ca97e734b1ed075ed9501b3ee21577f03fa5ce70c9cd`.
The corpus digest is
`0bfc1d6daf9b6b3dfb1f81c8bbaa5c9e81d9a1f4ce046c53370f37787e68c853`;
the installed Lake manifest digest is
`290f048c4a499d34a3b21f8db30ade48a2b8d05b0fe79709f1868fa6748944fa`.

## Integration boundary and remaining evidence

At the pinned agent base, `proof_flow_runtime.py` performs structuring and
canonicalization at lines 174–180, embedding at 188–193, API candidate retrieval
at 195–204, evidence/reranker preparation at 208–222 and actual reranking at
250–258. These boundaries have no stage clocks in the inspected baseline. They
were inspected, not measured against real providers or a database in this
slice; no end-to-end latency bottleneck is inferred from compiler measurements.

T4 continues to own matching, retrieval indexes and catalog access. No retrieval
relation, substitution, proof method, admission eligibility or source is changed
by this cache. A changed source or instantiation still follows PFR-011; a setup
hit does not skip semantic review or new Lean verification. Workers receive no
database credentials and remain outside local compiler execution.

The broad/explicit import comparison is evidence for authored input planning,
not an automatically applied source transformation or theorem-equivalence proof.
Automatic narrowing requires binding the transformed statement/origins to the
original target and independent review. No such transformation is enabled.

Generated compiled-module caching remains unimplemented. Its next bounded slice
must define verifier-owned production/storage, source/dependency/toolchain/
configuration/platform identity, artifact digests, trusted admission/lifecycle
bindings, atomic publication and concurrent materialization. It must reject
tampered/stale artifacts and prove hits plus invalidations with real Lean.
Untrusted compiled modules must never be admitted merely by a matching hash.

The local checks do not establish DB/provider stage timing, Recall@k/MRR/false
acceptance/verified application rate, end-to-end bottlenecks, independent import
versus elaboration timing, per-mode peak memory, Linux runtime isolation, live
mTLS compiler execution, admitted catalog reuse, browser behavior or deployment.
Cold/warm performance here describes process-local environment cache state;
filesystem/page caches remain uncontrolled. These missing checks remain
unverified, and full T5 is not complete.

The benchmark runs broad, narrow, cold and warm modes serially in that order.
Mode order, filesystem caching and background machine load can confound a
causal speedup estimate; no stable production speedup is inferred. Per-family
five-sample p95 is the largest observation and is descriptive, not a reliable
tail-latency estimate. A future performance acceptance run should interleave
paired baseline/changed samples on the production-equivalent Linux boundary.

This bounded slice used about 51 minutes of a 120-minute local budget. Initial
runtime parser failures were diagnosed and corrected; the exploratory timing
run was retained separately and the final measurements were rerun after source
hardening. No app service or container was started. Task-owned benchmark/test
processes completed and verifier scratch directories were cleaned by the
existing request lifecycle. The managed review worktree and local raw evidence
are retained for continuation.
