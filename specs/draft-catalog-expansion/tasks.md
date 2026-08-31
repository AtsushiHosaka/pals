# Draft Catalog Expansion Tasks

## Implementation order

| ID | Task | Requirements | Verification |
|---|---|---|---|
| DCE-T001 | Define the closed coverage-matrix schema and author the initial school, undergraduate-core, and named advanced-scope family matrices with official/reference revisions, applicable problem modes, difficulty bands, prerequisites, profile feasibility, population-limit calculation, and empty Draft bindings. | DCE-002–DCE-005, DCE-013, DCE-016 | Schema validation, stable-ID, capacity and closed-object tests; review every school family against the cited official curriculum and every university family against its declared boundary. |
| DCE-T002 | Implement the deterministic repository inventory command. Reconcile coverage cells with generic candidate manifests, packaged seed, typed authoring manifests, canonical OpenMath identities, profile validators, optional external evidence references and embeddings; emit JSON plus a concise report. | DCE-002, DCE-004–DCE-007, DCE-014, DCE-016 | Unit tests for duplicates, alpha/constant-only review flags, unknown IDs, orphan cards, missing profile, state derivation, capacity overflow, deterministic output and the observed 31/431/163 distinctions. |
| DCE-T003 | Add optional read-only PostgreSQL inventory adapters for legacy generic, immutable generic PFI, local typed authoring, and API-owned typed runtime catalogs. Never infer publication from authoring presence. | DCE-007–DCE-010, DCE-012, DCE-014 | Real PostgreSQL integration proves relation/generation detection, role read boundaries, row/embedding reconciliation, active generation reporting and `runtime_not_verified` without DB evidence. |
| DCE-T004 | Replace the production generic release input's dependence on the packaged 31-row seed with a sealed complete admitted-generic release layout. Preserve generic Draft payload and existing PFI immutable publication and rollback semantics. | DCE-001, DCE-006–DCE-008, DCE-010–DCE-012, DCE-016 | Existing PFI tests plus real PostgreSQL publication of a complete layout; reject manifest, fingerprint, provenance, row-count, capacity and canonical collisions; active runtime returns all admitted rows within query limits. |
| DCE-T005 | Add API-owned profile-separated typed generation, row, active, quarantine and publication storage plus release-only admission from sealed typed layouts. Keep `pals_local_typed_catalog` authoring-only and leave generic PFI unchanged. | DCE-001, DCE-006–DCE-010, DCE-012, DCE-015–DCE-016 | Real PostgreSQL role, immutability, profile separation, population limit, incompatible binding, failed activation, rollback and authoring-only exclusion tests. |
| DCE-T006 | Add the authenticated, closed and bounded typed candidate internal API and agent port using an explicit `profile_id`, then add profile-aware structuring, embedding and reranking without cross-profile fallback or direct agent database access. Keep generic v1 byte/behavior compatibility. | DCE-009–DCE-012, DCE-015–DCE-016 | Contract/integration tests for worker-secret failures, duplicate/unknown/oversized input, supported profiles, ambiguous/unknown/mismatched profile, capacity/binding mismatch, no fallback, result digests/limits, no agent DB configuration and unchanged generic retrieval. |
| DCE-T007 | Build the versioned family evaluation corpus and release evaluator for positive and hard-negative queries, including per-family structuring, Recall@k, MRR, false-match/no-match and verified-completion metrics. | DCE-004, DCE-006, DCE-011–DCE-012 | Run the real runtime stack against representative generic and typed generations; every metric is reproducible and a failed threshold preserves the active generation. |
| DCE-T008 | Author and admit the first 18-pattern school algebra slice against exactly six anchor families: `school.e4.two-quantity-relationships`, `school.e6.fractions-symbolic-expressions`, `school.g7.linear-equations`, `school.g8.simultaneous-equations`, `school.g9.quadratic-equations`, and `school.h1.inequalities`. Supply one compute/construct, justify/prove, and model/apply pattern per anchor using existing generic semantics where exact. Adjacent precursor families such as symbolic-expression transformation and polynomials remain separate and are not filled by implication. Bind every Draft to coverage cells and add hard negatives. | DCE-003–DCE-007, DCE-013 | Generator/schema tests, profile and alignment validation, exactly 18 distinct primary cells across the six named anchors, collision audit, runtime retrieval and downstream verified proof completion for the batch. |
| DCE-T009 | Release the existing six-card `typed-math-matrix-v1` profile end to end, then retrieve it through the real typed runtime path without reporting linear-algebra completeness. | DCE-006–DCE-012, DCE-015–DCE-016 | Sealed manifest revalidation, independent alignment review, real embeddings, PostgreSQL publication, active authenticated API retrieval, matrix hard negatives and downstream pinned-verifier completion. |
| DCE-T010 | Expand school families in prerequisite order until elementary, junior-high, and Mathematics I/A/II/B/III/C each reach 100% of required cells and pass evaluation. Add or extend typed profiles only when the matrix marks generic representation inexact. | DCE-002–DCE-013 | Per-stage inventory reports `comprehensive`; no duplicate inflation; all profile, publication, retrieval and proof-completion gates pass. |
| DCE-T011 | Expand undergraduate core families in prerequisite order. Before authoring an advanced scope, refine each aggregate target group into concept-family mode/difficulty cells; then expand each refined advanced scope independently. Reuse admitted profiles when exact and expose remaining profile gaps rather than silently omitting them. | DCE-002–DCE-013 | Per-scope inventory and runtime evaluation report `comprehensive`; no aggregate advanced target can report comprehensive before cell refinement; advanced gaps remain visible and do not affect unrelated scope verdicts. |
| DCE-T012 | Document authoring, independent review, optional evidence repair, generic/typed publication, rollback, private runtime access, capacity diagnostics, inventory diagnostics and the exact meaning of a comprehensive scope. | DCE-001–DCE-016 | Documentation-to-requirement review, secret scan and `git diff --check`. |

## Milestone gates

### Milestone A: measurable baseline

Complete `DCE-T001`–`DCE-T003`. It is complete only when the current repository and real
local database produce a reproducible report that distinguishes authoring, admission,
embedding, publication and runtime retrieval.

### Milestone B: real publication paths

Complete `DCE-T004`–`DCE-T007`. It is complete only when one complete generic generation
and one profile-separated typed generation can be published, queried, rejected safely and
rolled back using real PostgreSQL and runtime contracts.

### Milestone C: first content slices

Complete `DCE-T008`–`DCE-T009`. It is complete only when all six school anchor families and
one existing typed university profile pass the same production-shaped admission and retrieval gates.

### Milestone D: comprehensive scopes

Complete `DCE-T010`–`DCE-T012`. A named scope is complete only when every required coverage
cell is admitted, published and retrieval-passing and the scope has no blocking collision,
profile, capacity, alignment or runtime finding. Raw Draft count is not a completion gate.
