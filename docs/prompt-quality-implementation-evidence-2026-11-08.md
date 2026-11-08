# Prompt-quality implementation evidence — November 8, 2026

Authority: the user's design/implementation request and the WORKING
`specs/prompt-quality` contract. Initial audience: undergraduate learners.
This record distinguishes local implementation from live deployment and improvement.

## Scope and preservation

The shared checkout contained pre-existing tracked/untracked work. This task added
private observability modules/tests/datasets and a standalone Terraform file without
editing the dirty implementation paths. Publication uses isolated temporary Git
indexes based on current upstream; the shared index, branch and existing worktree
changes are preserved. No force push, stash, reset, container, observer or deployment
was used. Temporary source archives and transfer files were cleaned.

Pinned upstream compatibility references:

- Parent: `3c746c56a5595cd2468fd062fccd9d393300eb28`.
- Agent: `adec9626b385c0784e6bf36adaef038f4046b6fe`.
- Observability base: `c8c89250fdb8d76af400d949299e4bc6b7fdade4`.
- Infrastructure base: `d70b12555f71cf0e4403ef13d616b5f802326e5c`.

The evaluator supports the older direct natural runtime and current factory-composed
`ChatRuntime`. It calls the outer runtime, preserving routing. Current proof/solution
requests need live claim-bound Recipe/Lean callbacks, so direct evaluation retains
their failed/unavailable outcomes. No claim of complete proof-flow coverage is made.
The eight concept cases provide usable explanation-route inputs; the twelve proof/
counterexample/clarification cases remain useful for the explicit coverage boundary.

## Executed checks

| Check | Environment and actual result |
| --- | --- |
| Closed schema, runner, provenance, pairing/missingness, AWS adapter and CLI contracts | Existing observability Python 3.12 environment; focused suite: 82 passed. AWS/model isolation here proves boundary contracts only. |
| Complete observability regression suite | Task tree combined with current upstream in one temporary archive; existing venv reused; `python -m pytest -rs`: **1,071 passed, 1 skipped** in 16.24 seconds. |
| Skipped check | Credential-dependent Langfuse smoke explicitly requires opt-in and audit evidence; it was not activated. |
| Static checks | Existing venv: `ruff check src tests` passed; strict `mypy src` passed across 25 source files. |
| Current agent composition | Actual upstream agent source in a temporary archive using existing agent venv: factory constructs `ChatRuntime`, source/config fingerprints compute, real invalid-input path fails before provider access. No model call. |
| Infrastructure contract | Four tests passed using actual Terraform console evaluation of new IAM expressions; not mock deployment evidence. |
| Terraform | New file format check passed. New file combined with current upstream validated successfully with the existing provider cache; no AWS resource operation. |
| Benchmark references | Independent mathematical review found no defect in all 20 authored references. Japanese lint found no substantive issue; the concept dataset's retained negative contrast specifies the requested route rather than adding rhetoric. |
| Independent architecture review | References isolated from generation; task-write boundary preserved; AWS calls match scoped policy; atomic/private output and retry deduplication reviewed. Partial usage was repaired to null; judge revision limits are explicit. Missing-score coverage bounds and failure denominators verified. |

Initial host `python3` lacked pytest; infrastructure tests were rerun with the existing
observability environment. A sandboxed fetch could not write `FETCH_HEAD`; authorized
Git metadata operations were performed with the required sandbox permission. These
were environment issues, not failing product behavior.

## Result and remaining evidence

The local implementation and configuration checks pass within the declared direct
evaluation scope. Independent review found no remaining material defect after repairs.
Publication commits on `codex/prompt-quality-evaluation-20261108`:

- Observability: `fadea9bc3a2448e328a26f26421185aa7154ed8e`.
- Infrastructure: `0d7bde1c7fed3f9cfc3af4210df535dd8860c405`.

Both commits were pushed. Draft reviews:
[observability #2](https://github.com/AtsushiHosaka/pals-observability/pull/2) and
[infrastructure #109](https://github.com/AtsushiHosaka/pals-infra/pull/109).

Not executed: paid generation/judging, actual AWS ingestion/read-back, saved query
execution, infrastructure apply, full claim-bound proof collection, human calibration
or measured prompt improvement. Mutable model aliases, operator-attested judge
revision, non-Python assets and transitive dependencies limit provenance. Usage totals
remain null without completeness attestation. The next evidence delta is a real,
controlled baseline/candidate holdout run and CloudWatch publish/fetch after deployment,
plus proof-output integration for complete answer-path coverage.
