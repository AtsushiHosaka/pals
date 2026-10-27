# T2: checked synthetic geometry first slice

Date: 2026-10-28 JST. This is a bounded implementation record, not full T2,
geometry-catalog admission, chat integration, or deployment acceptance.

## Authority, revisions and ownership

User-directed WORKING MRD-002/003/004/011 contract and explicit implementation
request. Shared requirement bytes SHA256
`16c3fbdd8b925b168d534343fb85abb385a843fc6f2236fb667cad971bdacf9c`;
shared design bytes SHA256
`625091412f449802c39bc885910988fdb7682d969242865264eb1df0055ba99e`.

- Refreshed parent base: `ca84e6fe1a87fa019368f16e4af8c7cbec759a82`.
- Refreshed agent base: `4703690c4125eed18fcce9269ce4f1dbc6ff577d`.
- Agent implementation: `fd8b4caae17604d8a935953ed6476c1b0cde7740`,
  [draft review PR #18](https://github.com/AtsushiHosaka/pals-agent/pull/18).
- Branch in each repository: `codex/synthetic-geometry-20261028`.
- Lean: `leanprover/lean4:v4.32.0-rc1`; Mathlib:
  `8b62164d808cd0f23b7d8cc28190a6c1a1bb483a`.

Own new agent geometry input, mathematical-content diagram producer, fixed Lean
proof, proof/trace verification and opt-in CLI. T3 retains diagram transport,
schemas, TeX generation, renderer, persistence and frontend. No API or frontend
repository was initialized here. The managed task worktree preserved the shared
primary checkout's pre-existing changes; existing Python/Lean dependencies were
reused. No full stack, app instance, image or container was created.

## Explicit working slice contract

`pals-geometry` / `python -m pals_agent.synthetic_geometry` accepts the closed
`pals.synthetic-geometry-input.v1` format. Only
`isosceles-midpoint-perpendicular-v1` is supported. It requires four distinct
point identities bound to A/B/C/M, the explicit hypotheses
`non_collinear(A,B,C)`, `equal_distance(A,B,A,C)`, `midpoint(M,B,C)`, and
`perpendicular(A,M,B,C)` as conclusion. Lines are represented by their nonzero
endpoint directions; circles and arbitrary construction search are outside this
slice. Original text, exact proposition spans, labels and figure metadata remain
in the immutable input snapshot. Distinct object IDs do not assume distinct
geometric locations; the necessary distinctness is proved.

The caller declares the structured interpretation. Text-span identity establishes
provenance, not mathematical equivalence between natural language and a formula.
The existing immutable MaterialContext validates selected OCR snapshots/citations;
the existing exact confirmation-turn contract gates OCR propositions. Unresolved
interpretation ambiguities return `needs_input` before any compiler access.
Image identities and source/image digests use the existing chat attachment
metadata contract. This does not claim that original pixels were inspected or
that an automatic image transcription was performed.

The actual theorem is generic over a real inner-product affine space, so it
applies to planar instances without fixing drawing coordinates:

```lean
(h_triangle : ¬ Collinear ℝ ({A, B, C} : Set P))
(h_equal_sides : dist A B = dist A C)
(h_midpoint : M = midpoint ℝ B C) :
B ≠ C ∧ A ≠ M ∧ ⟪A -ᵥ M, C -ᵥ B⟫ = 0
```

This analytic foundational model supports a synthetic perpendicular-bisector
explanation. No arbitrary axiom, external solver axiom, `sorry` or `admit` is
introduced. The existing authoring-only typed-plane-geometry/OpenMath profile,
Draft/Recipe admission, semantic review and ordinary worker behavior are unchanged.

## Checked steps and source binding

Proof resource: `pals_agent/geometry_proofs/isosceles_midpoint.lean` in the agent.
Its exact SHA256 is
`59441abf6e6a92e7e6413b6435356c7c49430b1cfcda22cb7eb0f9686ee7fa80`.
The runtime rejects resource drift and checks the toolchain, complete Lake
configuration/manifest and all dependency source revisions/cleanliness before
and after compilation. The existing operator-provisioned Lean executable and
compiled dependency artifacts remain trusted; source checks do not attest their
binary provenance or replace T5's artifact trust work.

| Named declaration (`PalsGeometry.` prefix) | Lines | Premises and earlier steps |
| --- | --- | --- |
| `base_distinct` | 11–13 | non-collinear; Mathlib `ne₂₃_of_not_collinear` |
| `apex_distinct_midpoint` | 16–22 | non-collinear + midpoint; `wbtw_midpoint`, `Wbtw.collinear` |
| `apex_mem_perpBisector` | 25–27 | equal sides; `AffineSubspace.mem_perpBisector_iff_dist_eq` |
| `midpoint_orthogonality` | 30–34 | prior bisector + midpoint; `AffineSubspace.mem_perpBisector_iff_inner_eq_zero` |
| `isosceles_midpoint_perpendicular` | 37–46 | conjunction of all four checked results |

The ordered trace carries actual hypothesis IDs, role-to-object bindings,
upstream rule names, instantiated symbolic conclusions, dependencies and exact
source ranges/digest. The final declaration explicitly applies those helpers.
The trace itself has an RFC8785 SHA256 binding. This is a reviewed fixed-source
trace; arbitrary generated traces are not accepted.

Every request executes the existing LeanVerifier plus a separate fixed trusted
`#print axioms` audit of the same resource through the same bounded child-process
isolation. The public verifier still rejects generated interactive commands.
Only `propext`, `Classical.choice`, and `Quot.sound` are allowed. All five actual
reports contain exactly those three. An absent, duplicate, unexpected or
non-foundational report cannot produce checked status.

## Diagram producer integration

Consumed T3 WORKING `pals.diagram.v1` contract SHA256
`2501433eb28d694844209a89995ac3407bc0fa02bfcc9b5bb372075a5a47f27a`.
The payload retains the same point IDs and labels, marks M/AM derived, and
references the checked final declaration and proof digest. It emits a deliberately
smaller safe label subset. Coordinates are explicitly display-only. Drawing
consistency is checked at the renderer's six-decimal precision; collapsed,
non-isosceles or wrong-midpoint displays are unavailable rather than misleading.
These numerical display checks never establish premises or verification status.
The checked proof/source/trace remain available on diagram-content failure.

The actual T3 working validator and deterministic source generator accepted the
produced fixture. Read source bindings at that execution:

- `app/domain/diagrams.py` SHA256
  `16ca447a43cbc35ba39c5e38d822b8c239fc5684e9fd4266b0fa039766fa2ee3`.
- `app/infrastructure/diagram_renderer.py` SHA256
  `a2dbf12ab5023935f142ac1a6b138ced33cb7618e5f8587747600e6ca03317ae`.
- Generated complete TikZ source SHA256
  `3c4393040aca8825fba7cdc905c726c377fc6a9e4329a4e4186e3db18e75d056`.

`prepared_unrendered` is the honest payload state. The Docker daemon did not
respond to a read-only image inventory; the task-owned command was interrupted.
No container or alternative unisolated renderer was started. Rendering, actual
geometry-to-chat flow, persistence/reload/mobile/browser evidence are missing.

## Executed evidence

1. **144 tests passed** in 20.05 s: geometry input, diagram content, source/trace
   bindings, real Lean integration, existing typed-plane geometry, material
   context and Lean-verifier regressions. No configured real checks were skipped.
2. Ruff passed on all new Python source/tests. Strict mypy passed all three new
   source modules. `git diff --check` passed.
3. The substantive proof compiled. Lean also proved concrete counterexamples
   showing failure when equal sides or the midpoint premise is removed, plus
   collinear-apex/collapsed-base degeneracy cases. Counterexample coordinates are
   witnesses in tests, never premises in the positive theorem.
4. `uv build` built sdist/wheel. A wheel installed to a temporary target completed
   a real CLI proof and axiom audit using the reused workspace.
5. Independent source/unit/generic-architecture review found two input defects
   (malformed nested metadata and multibyte proposition length); both were fixed
   and regression-tested. Follow-up reported no remaining P0–P2 findings.

Real CLI fixture bindings: input SHA256
`7d3f60e544a389dc5aea40e5223b4acad8f55d0cdfa66fa5bc582c54a3d59af5`,
trace SHA256
`80513f0fc74671ebda884d2ef75617d00f7d1584ce13d1cb377692f09e0399c9`.
Observed compilation 1842 ms + separate axiom audit 2719 ms on Darwin; this is one
local observation, not a latency benchmark or production isolation verdict.

Reproduce from the agent repository, pointing at an existing provisioned workspace:

```sh
PALS_GEOMETRY_LEAN_WORKSPACE=/path/to/lean-workspace \
  python -m pytest tests/unit/test_geometry_input.py \
  tests/unit/test_geometry_diagram.py tests/unit/test_synthetic_geometry.py \
  tests/integration/test_synthetic_geometry_runtime.py \
  tests/unit/test_typed_plane_geometry.py tests/unit/test_material_context.py \
  tests/unit/test_lean.py
pals-geometry testdata/synthetic-geometry-v1/isosceles-request.json \
  --lean-workspace /path/to/lean-workspace
```

Use the documented Lean/Lake/Elan/path overrides when outside the verifier image.
Local raw results and generated source stayed in temporary storage; generated
outputs/logs were not committed. No service or container residue was created.

## Prior-art audit

Primary source inspection, with no third-party builds or imported dependency:

| Project | Inspected immutable revision | Toolchain / Mathlib | License and decision |
| --- | --- | --- | --- |
| [Mathlib](https://github.com/leanprover-community/mathlib4/blob/8b62164d808cd0f23b7d8cc28190a6c1a1bb483a/Mathlib/Geometry/Euclidean/PerpBisector.lean) | `8b62164d808cd0f23b7d8cc28190a6c1a1bb483a` | Lean 4.32.0-rc1 | Apache-2.0; reused pinned foundation |
| [LeanEuclid solver](https://github.com/loganrjmurphy/LeanEuclid/blob/33a72c0fa83914202532998a2e7b8771295c3cc7/SystemE/Meta/Smt/Solver.lean) | `33a72c0fa83914202532998a2e7b8771295c3cc7` | Lean 4.19.0 / `c44e0c8ee63ca166450922a373c7409c5d26b00b` | MIT; unrestricted `SMT_VERIF (P : Prop) : P` rejects solver success as verified evidence |
| [LeanGeo SMT tactic](https://github.com/project-numina/LeanGeo/blob/9212b89ef0cb08adb049b32f6332a1f2b9e551ab/SystemE/Tactic/ESmt.lean) | `9212b89ef0cb08adb049b32f6332a1f2b9e551ab` | Lean 4.15.0 / `9837ca9d65d9de6fad1ef4381750ca688774e608` | MIT; actual tactic closes through unrestricted `SMT_VERIF` over Sort, so not reused |
| [Euclean](https://github.com/tlb-22/Euclean/tree/d53fc93d87887ede717dcc455797083744a8f673) | `d53fc93d87887ede717dcc455797083744a8f673` | Lean 4.28.0 / `8f9d9cff6bd728b17a24e163c9402775d9e6a365` | Apache-2.0; useful constraint-explication/review prior art; not built here |
| [MechGeoBench](https://github.com/MechMath/MechGeoBench/tree/e2c289c442de97dc1402d4ae4658c52153c7ad93) | `e2c289c442de97dc1402d4ae4658c52153c7ad93` | Lean 4.27.0 / `a3a10db0e9d66acbebf76c5e6a135066525ac900` | Apache-2.0 plus upstream notices; problem templates contain sorry, so membership is not proof |

## Remaining acceptance and continuation

This slice passes its local opt-in domain criteria. MRD-002 is partial: faithful
automatic text/image-to-model interpretation and real chat intake remain to be
integrated and semantically reviewed. MRD-003 is checked for this exact fixed
family only. MRD-004 has compatible prepared content/TikZ-source evidence, not
rendered chat evidence. MRD-011 gains one substantive prepared family, not broad
undergraduate or entrance-exam support. No real catalog DB/provider, admitted
catalog entry, deployment or production feature activation was attempted.

Next bounded integration: T3 pins and reviews its final contract/source revisions;
the geometry owner validates this producer against them; the chat/API owners
wire trusted user-confirmed structured input and reviewed proof correspondence,
then exercise an actual figure request through stored input, Lean proof, ordered
explanation, isolated rendering, inline chat and reload. Preserve the independent
semantic review and ordinary new-Lean/admission requirements. This parent gitlink
is a review proposal and must not be treated as an accepted deployment release.
