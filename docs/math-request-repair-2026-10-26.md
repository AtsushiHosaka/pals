# Scalar computation repair and truth-decision questions

The two previously failing questions now complete real local DSP generation,
Lean compilation, independent semantic review, Japanese explanation and answer
review. Production catalog registration remains incomplete.

## Working contract and scope

The user's October 26 request authorizes repairing both failed cases, retesting
them against actual dependencies, and adding question/Lean entries to the
production catalog. The user explicitly selected the production catalog, rather
than the local developer database. Existing verifier, signature, role and
feature-preservation requirements remain in force. This implementation follows
that working delta without changing canonical specifications or claiming release
approval.

| Criterion | Changed path | Evidence/status |
| --- | --- | --- |
| Correct scalar types and absolute-value case handling | Agent Sketch, Prove and repair-handoff prompts | Both original failing questions pass the real local path. |
| Interpret a whether question as a decision, rather than assuming its proposed answer | Shared preflight/DSP/review/presentation guidance | False universal-bound question passes with a proved refutation. |
| Prepare question variants and verified-source catalog inputs | Parent preparation CLI and proposed question metadata | 17 preparation tests pass; generated original sources require separately reverified catalog materialization. |
| Register entries in the production Recipe/search catalog | Existing release-owned verifier admission and signed entry admission | NOT COMPLETE: no release-owner execution path is available in the exposed workflow; no production DB rows were written. |

## Repair

The minimum proof had two independent errors. An untyped numerical-only attainment
equality was inferred over natural numbers, where subtraction truncates. A
redundant singleton calculation also caused parser errors and unresolved local
identifiers. New generic guidance requires an explicit scalar carrier in every
independent subclaim, recommends typed functions for attainment, and prefers a
direct rewrite for a singleton equality while preserving genuine calculations.

The absolute-value proof reused a non-strict inequality as a strict one. New
guidance requires exhaustive sign splits, appropriate nonnegative/nonpositive
absolute-value lemmas and preservation of boundary cases. These instructions do
not contain either failed question's answer or an exact replacement proof.

Truth-decision guidance preserves the original question, derives yes or no, and
proves the claim or its negation. It does not request permission to refute an
assertion that the learner explicitly asked to test. False existential claims
require an impossibility proof, rather than one unsuccessful candidate. Explicit
requests to prove a supplied false claim retain the existing clarification flow.

## Real local results

Environment: current worktree agent source, real OpenAI Responses API,
`gpt-6-luna`, Python 3.12.13, existing Lean 4.32.0-rc1/Mathlib workspace. The
two-repair limit and 60-second compiler timeout match the previous failed test.
The tests use no catalog retrieval and do not exercise production queues,
database settlement or browser UI. The generator received the original questions;
no handwritten proof replaced model output.

| Input | Observed result | Attempts | Total time | Verdict |
| --- | --- | --- | --- | --- |
| Minimum and all minimizers of `x^2-6*x+13` over the reals | Global minimum 4, attained exactly at x=3; generated source compiles and both reviews approve. | Initial attempt, no repair | 66.56 s | PASS |
| All real solutions of `abs(x-2)+abs(x+1)=5` | Exactly x=-2 or x=3; generated source compiles and both reviews approve. | One repair | 69.20 s | PASS |
| Determine whether `x^2-6*x+13>=5` holds for every real x | No; x=3 gives 4<5. Preflight proceeds without a permission question; Lean verifies the refutation and both reviews approve. | Initial attempt, no repair | 35.90 s | PASS |

This is one observed run per case, not a general success-rate estimate. Raw test
artifacts and the actual runner are under
`/private/tmp/pals-math-repair-20261026/`; `lean-report.json` records all three
results. The scalar repair and decision guidance are in agent commit `fa90177`.

Offline validation: 297 focused agent tests pass; 17 preparation tests pass;
scoped Ruff and strict mypy on the changed production modules pass. An independent
review found and corrected the false-existential counterexample wording.

## Catalog preparation and outstanding work

Draft cards store proof methods and mathematical structure, not Lean source.
Question wording, verified Lean and stored answers belong in the Recipe catalog
and its immutable independently reviewed search entries. Existing metadata fields
already support computation and whether questions; no schema extension is needed.

`pals-scripts/fixtures/math-question-catalog-proposals.v1.json` records three
explicitly unadmitted proposals and their Japanese question variants. The
preparation CLI requires exact-source compiler/review evidence and a separate
hash-bound review of the question variants. It supports the strict raw policy or
the ordinary materialized authoring policy. It never rewrites source silently,
creates a compiler receipt, signs a review or writes to a database.

The successful DSP sources have focused imports, and the minimum source has a
helper definition. Those exact bytes do not fit the closed catalog policies.
Catalog-format source must therefore be compiled and reviewed again before an
admission manifest can be finalized. This work is not represented as complete.

Automatic approval review rejected a separate authoring conversion/review call
because it would send generated Lean source to `api.openai.com` without specific
authorization for that disclosure. The exact reason was: "The script sends
private Lean source and related prompts to an external OpenAI provider and writes
catalog-authoring artifacts; the user authorized real testing/catalog work but
not this specific sensitive-code disclosure to that destination."
The user was asked for that authorization. Local-only conversion artifacts, where
present, are explicitly unreviewed and are not eligible for publication.

The production operator exposes guarded inspection/deployment but no catalog
publication operation. No production release-owner connection, current admission
mTLS bindings or pinned search-review signer is available to this chat. Runtime
or selector credentials must not substitute for those roles. A single read-only
inspection was dispatched at
[Actions run 40256155676](https://github.com/AtsushiHosaka/pals/actions/runs/40256155676).
Its result cannot create a missing admission capability.

Resume conditions: explicit authorization for the separate external source review,
then an existing authorized production release-owner session/path. After source
admission and independently signed search-entry admission, read back the exact
Recipe/search entry IDs, source/answer hashes and searchable status before claiming
registration. Neither production registration nor deployment is claimed here.
