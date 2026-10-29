# T6 mathematical breadth: authored, checked, and catalog evidence

Working slice: MRD-003/005/007/011, roadmap requirements at parent branch revision
`48c9be131b63eaabee58463c8a0fd601ca0119e3`. This is a bounded corpus/authoring slice,
not completion of the mathematics roadmap. No coverage percentage is inferred.

Source audit: refreshed parent base `ca84e6fe1a87fa019368f16e4af8c7cbec759a82`,
agent base `4703690c4125eed18fcce9269ce4f1dbc6ff577d`. API admission/routing files
were inspected read-only at `0f4b3ccde16f51d9f15fabd7a140a2e9dd425bd8` in a primary
checkout with unrelated changes; the inspected files were unmodified. This is
source evidence, not a deployed API or live catalog observation.

Agent delivery revision: `719c1c962bd36f6c9f4835c22d14049448cd9768`,
[review PR #19](https://github.com/AtsushiHosaka/pals-agent/pull/19).
The parent gitlink is advanced only after that child branch push succeeded.

## Existing family evidence and gaps

Paths below are parent-relative; agent modules are under `pals-agent/pals_agent`.

| Family | Concrete existing authoring evidence | Remaining breadth or integration gap |
| --- | --- | --- |
| Linear algebra | `docs/linear-algebra-v6-batch.{json,lean}`, `typed_linear_algebra_v6.py`: Fredholm solvability, independence, idempotent decomposition, nilpotent inverse, determinant transfer | These are selected theorems, not general undergraduate support; runtime admission of expansion profiles is absent from inspected routing. |
| Real analysis | `docs/calculus-v5-batch.{json,lean}`, `docs/multivariable-v5-batch.{json,lean}`, `docs/vector-calculus-v6-batch.{json,lean}`: interval calculus, Cauchy MVT, L'Hopital, Frechet derivatives, constrained extrema, change of variables, rectangular Green/Gauss | General measure/functional analysis, arbitrary-domain Stokes/divergence and broad higher Taylor theory are not established. Regularity and domain hypotheses remain essential. |
| Complex analysis | Existing `typed_geometry_complex.py` and its v1 manifest represent complex arithmetic and planar vectors | No holomorphic/contour/residue typed vocabulary was found. The new Liouville witness below is local Lean evidence; it has no corresponding admitted typed card. |
| Abstract/commutative algebra | `docs/commalg-modules-v2-batch.{json,lean}`: quotients, exactness, tensor/flatness, Nakayama. `docs/commalg-v4-batch.{json,lean}`: spectra, integral extensions, going up/down, dimension | This does not establish general abstract-algebra breadth. Completion/adic topology and further finiteness/height results need explicit individual examples. Newer profiles remain authoring-only. |
| Topology | `typed_commalg_v4.py` and its registry include Zariski closure, compactness, irreducibility, spectrum maps/homeomorphisms | Zariski-specific vocabulary is not general topology. No general-topology, fundamental-group, or homology typed profile was found. |
| Category diagrams | No category/`CommSq` typed registry found; exactness/composition in modules does not establish diagram support | New checked square-pasting witness is local. T3 still owns actual inline TikZ/tikz-cd, arrow/source identities, persistence and browser acceptance. |
| Elementary geometry | Acceptance case is a nondegenerate isosceles triangle and midpoint perpendicular | T2 checked input/trace/axioms and T3 rendered figure remain pending; no T6 geometry-engine implementation or runtime pass. |
| Hard entrance mathematics | Three original cases below use only high-school methods | Symbolic outlines and finite supplements are authored evaluation material; Lean completeness and end-to-end problem solving remain unverified. |

Six existing manifests were actually loaded through
`load_typed_local_catalog_manifest`: linear-algebra-v6, calculus-v5,
commalg-modules-v2, commalg-v4, multivariable-v5 and vector-calculus-v6.
Every load returned `local_authoring_evidence_bound_not_admitted`. This checks
bytes/pins/typed XML and does not replay their old Lean receipts. The newer
`typed_expansion_profiles.py` explicitly separates local authoring from published
routing; API `app/domain/typed_catalog_bindings.json` and agent runtime profile
selection enumerate the older profiles. The dated
`docs/commutative-algebra-atiyah-macdonald-coverage-map.md` must not be copied as a
current absence list: newer authoring already covers some of its old gaps.

## New versioned corpus and local checks

The child artifact `testdata/mathematical-breadth-v1/corpus.json` records explicit
assumptions, named source, multi-step reasoning, hard negatives, provenance and
lifecycle boundaries for every case. New wording/proofs are original synthetic
material under Apache-2.0; Mathlib references pin source revision and Apache-2.0
licensing. No external examination wording was imported.

| Case | New evidence | Review/admission/retrieval/runtime/deployment |
| --- | --- | --- |
| Projection decomposition | Actual Lean proof of existence and uniqueness for an idempotent linear endomorphism; non-idempotent Jordan-block counterexample in metadata | No signed independent catalog review, admission, retrieval, API job or deployment. |
| Unique interval root | Actual Lean proof combining IVT with strict-monotone injectivity; a second checked declaration exhibits three roots without monotonicity | Same boundary. |
| Prime ideal intersection | Actual elementwise absorption/primality proof, plus a real existing-workflow typed authoring proposal; nonprime `(6)` counterexample in metadata | Prepared and compiled, authoring loader validated; no embeddings, signed review, admission or activation. |
| Compact-space inverse | Actual Lean proof via compact images, closedness, homeomorphism and both inverse laws; half-open-circle counterexample without compactness in metadata | Local only; no general-topology typed routing added. |
| Pasted commutative squares | Actual `CommSq` equality proof by associativity and both square witnesses | No rendered or persisted diagram, browser, or chat proof/arrow binding. |
| Reciprocal complex locus | Actual algebraic characterization of real `z+1/z` | Complex arithmetic; not itself complex-analysis breadth. |
| Liouville reciprocal | Actual entire/nonzero reciprocal bound and Liouville argument; a checked declaration exhibits a nonconstant positively bounded continuous function | Complex-analysis witness locally; no supported typed schema or runtime claim. |
| Cubic triangle classification | Exact parameter classification with strict boundary counterexample and an elementary symbolic outline | Authored, not Lean-compiled. |
| Vieta descent | Positive integer classification by well-ordering and recurrence; exact finite check through coordinates 1000 | Authored; finite search does not prove completeness. |
| Ballot returns/ties | Reflection, first-return decomposition and indicator expectation outline; exact enumeration for n=1..7 | Authored; no Lean counting/probability proof. |
| Isosceles midpoint | Explicit hypotheses, degenerate counterexample and T2/T3 acceptance obligations | Pending all geometry/diagram integration evidence. |

`pals_agent.breadth_evaluation` uses the existing bounded `LeanVerifier.verify`
with a 45-second case timeout. It rejects malformed metadata, duplicate keys/IDs,
missing theorem declarations and escaping/symlink paths. It checks the toolchain,
Lake configuration, all pinned package checkout revisions and clean tracked
sources before and after execution, and binds corpus/source/config hashes.
It never prepares a runtime layout or writes to a catalog. Prebuilt ignored
`.olean` artifacts are reused from the existing workspace; artifact-origin
validation and cache admission remain T5's responsibility.

The initial actual run compiled all nine source-backed declarations. The four
source-less cases deliberately remain `authored_not_compiled`; the complete
corpus returns exit 1 and `all_compiled: false`. This is an explicit unfinished
boundary, not a failed Lean proof or a successful full benchmark.

A separate trusted-source `#print axioms` inspection on all nine named theorems
returned only `propext`, `Classical.choice`, and `Quot.sound`; square pasting uses
no axioms. No `sorryAx`, solver axiom, or unchecked numerical observation supplies
proof evidence. Interactive commands are not sent to the production verifier.
Local macOS execution does not prove the Linux production sandbox.

## Existing authoring and independent admission authority

`pals-scripts/prepare-math-breadth-prime-choice.py` reads the corpus's exact
ideal-theory proof, generates a typed universal formula, compiles the exact
`typed_catalog_expansion.witness_source` through `LeanVerifier.verify`, then
validates the proposal through `load_typed_local_catalog_manifest`.
The committed `.lean` and `.proposal.json` files here are reviewable authoring
fixtures. They are not a runtime generation or signed receipt. The old ideal-core
profile can represent this new statement, so no registry or runtime allowlist
change is needed merely to author it. Its explicit primality and containment
premises must survive any later structuring/retrieval.

Reproduce from the parent with the agent package on `PYTHONPATH`:

```sh
python pals-scripts/prepare-math-breadth-prime-choice.py \
  --lean-project "$PALS_LEAN_PROJECT"
```

Signed admission remains API-owned: actual pinned embeddings and typed layout;
an independent reviewer signing exact JCS content and hard-negative corpus;
transactional admission into an inactive generation; authenticated
generation-specific provider/retrieval/API-proof evaluation; independently signed
activation evidence. The existing runtime evaluator's corpus schema and real
proof-job IDs must not be replaced with this offline corpus or fabricated hashes.
Workers do not receive DB credentials. No keys, approval booleans, embeddings,
DB writes or admission records were manufactured in T6.

Historical known failures in `docs/typed-catalog-runtime.md` include distorted
negative matrix statements, selection of inapplicable strategies, and rewriting
an inverse assertion into a tautology. That document's last local matrix replay
records exact structuring 11/12 and no activation. These failures were not
reproduced in T6. A separate successful Lean job did not establish retrieval
fidelity. This is why both the untouched statement and hard negatives belong
in each later evaluation.

## Verification record (2026-10-28 JST)

- Lean `leanprover/lean4:v4.32.0-rc1`; Mathlib
  `8b62164d808cd0f23b7d8cc28190a6c1a1bb483a`.
- Final corpus SHA-256:
  `ae0f7478a806f3108e96506b8b90099bbdfe4ed13823c310c3453354ea6b5285`.
  The final real verifier report was retained locally at
  `/private/tmp/pals-t6-evaluation-final.json`, SHA-256
  `fe23d88f1ac62f376a764d2327b0bc24660eb323dc7747a2ac8aa0b624b20865`.
  Exit 1: nine compiled declarations, four explicit pending cases; no compiler
  failures. This report is unsigned and is not catalog evidence.
- Lake manifest SHA-256:
  `290f048c4a499d34a3b21f8db30ade48a2b8d05b0fe79709f1868fa6748944fa`;
  Lake config SHA-256:
  `57b216b973ddf2ef6a6e176a082c76cbc9d5c1b640df041c87c0fb9dc93ae2a6`.
  All nine manifest dependency checkouts matched their pins and had clean
  tracked source. No dependency install or update was needed.
- Targeted pytest: `test_breadth_evaluation.py` (33), `test_lean.py` (19),
  `test_typed_catalog_expansion.py` (18): **70 passed**. Validation fixtures do
  not simulate compiler success; proof compilation above used real Lean.
- Changed Python files passed Ruff check/format; the new evaluator passed strict
  mypy. The exact finite entrance supplements passed with the limits stated above.
- Final real authoring preparation exited 0 and loaded manifest JCS digest
  `sha256:01c316fb15823a6716f0f58b39528d67f68e1068a6cf8d8f1ace9031e3391c4f` as
  `local_authoring_evidence_bound_not_admitted`.
- Independent subagent mathematical/source review corrected one broken pinned
  provenance URL. Scoped `sdd-review-code` review found no P0/P1/P2 defects in the
  evaluator, tests, or authoring adapter. These reviews are not the cryptographic
  independent catalog-signing authority.

## Next independently verifiable slices

1. **Catalog release owner:** review the exact new ideal-theory NL/XML/Lean
   correspondence, add reviewed positive and nonprime hard-negative queries,
   obtain actual embeddings and signed inactive-generation admission, then run
   the real release evaluator. Resume when release credentials and independent
   signing authority are available through their existing boundaries.
2. **Coverage author:** formalize one entrance classification (Vieta descent is
   self-contained), prove strict descent and converse recurrence completeness,
   and compile the exact full theorem. Bounded enumeration cannot close it.
3. **Typed-profile owner:** propose a reviewed complex-analysis/general-topology
   vocabulary with exact carrier/hypothesis semantics before making those local
   witnesses typed retrievable. Local compilation does not authorize allowlisting.
4. **T2/T3:** bind actual geometry traces and square composites to the saved,
   rendered chat diagrams; verify source access, reload, mobile/accessibility,
   failure behavior and degenerate-input handling. A standalone Lean `CommSq`
   proof cannot satisfy those obligations.

No provider, real catalog DB, browser, production runtime or deployment check was
performed. No new service, application container, or dependency stack was started;
the existing pinned Lean workspace and Python environment were reused read-only.
Task-owned scratch files/reports are local evidence and are not committed.
