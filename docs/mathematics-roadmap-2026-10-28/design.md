# PALS mathematics implementation design

Date: 2026-10-28 JST. Requirements: [MRD](../../specs/mathematical-reasoning-and-diagrams/requirements.md).
This document records implementation choices for review; it does not assert that
the runtime already implements them.

## Current evidence

- GitHub API readback: `pals` and `pals-agent` are PUBLIC. `pals-api`,
  `pals-webfront`, `pals-infra`, `pals-datasets`, and `pals-observability` are PRIVATE.
  Public parent `main` is `ca84e6fe1a87fa019368f16e4af8c7cbec759a82`.
- [The publication audit](../repository-publication-audit-2026-10-27.md) documents
  a complete isolated secret-history gate, including retired verifier history.
  It explicitly excludes application security and several GitHub non-Git surfaces.
  Its historical pass is not a fresh security verdict.
- This coordination worktree has six uninitialized submodules. Existing runtime
  code and services must be inspected by the owning implementation chat; absence
  here does not mean that an implementation is absent elsewhere.
- [Draft retrieval](../openmath-omdoc-draft-retrieval.md) already describes
  alpha-canonical OpenMath, vector retrieval, and structural reranking.
  [LRC-003/006/018](../../specs/lean-recipe-catalog/requirements.md) distinguish the
  formal exact selector from independently reviewed natural-request correspondence.
  Variable-name-induced misses must be measured separately on each path.
- [Typed plane geometry](../typed-plane-geometry-v1-design.md) is authoring-only.
  Its proposals are not runtime-admitted geometry support.

## Geometry and diagrams

Use a versioned, typed mathematical object model for points, lines, circles,
hypotheses, constructions, and conclusions. Maintain object IDs across the
original input, formal statement, proof steps, and diagram. Keep display
coordinates separate from formal premises. Input transcription that changes
mathematical truth requires clarification.

Prefer the pinned Mathlib geometry library for the first checked proof slice.
Use synthetic theorem applications and a readable dependency trace to explain
the steps. A pedagogical synthetic argument may use an analytic foundational
model, provided its actual dependencies and axioms are explicit. Do not import
an external geometry solver merely because its output is accepted by Lean;
audit the transitive axiom footprint and reconstruct checked proof terms.

The first proposed substantial acceptance problem is a nondegenerate isosceles
triangle ABC with AB = AC and midpoint M of BC: prove AM is perpendicular to BC.
Confirm the precise formal assumptions and trace before treating it as supported.

The diagram owner defines a bounded, versioned payload for geometry and
commutative diagrams, with explicit evidence references. It owns serialization,
API persistence/transport, safe TikZ/tikz-cd generation, and frontend rendering.
The geometry owner consumes that contract and owns mathematical content and
proof-trace production. Agree on the contract before overlapping API edits.

Reuse the existing renderer/verifier isolation and running services where
suitable. Generate TeX from a restricted declarative model; never allow arbitrary
model-produced TeX to run in the application server. Render diagrams in the chat
answer, with source access, accessible descriptions, reload persistence, and
desktop/mobile checks. Preserve existing side-panel features and entry points.

For commutative diagrams, carry object/morphism identities and relations between
composites. A verified square references a checked equality/CommSq witness.
Rendering and proving commutativity have independent success states.

## Retrieval and compiled reuse

Retain four distinct paths: Draft retrieval, formal Recipe selection,
natural-request Recipe reuse, and compiled-module caching.

The proposed retrieval architecture unions bounded candidates from existing
semantic/vector retrieval, a versioned alpha-normalized identity index, and a
typed structural/discrimination index. Rerank them, then check scope, types,
repeated variables, dependencies, premises, and proof method. Return the match
relation, substitution, and remaining obligations explicitly.

Bound variables can use de Bruijn-style representations. Local free variables
need abstraction over a dependency-ordered typed context; replacing every name
with `*` loses repeated-variable and binder information. Mathematical constants,
domains, dependent quantifier order, and hypotheses remain significant.

The search owner owns canonicalization, candidate matching, indexes, and
retrieval evaluation. It retains API-owned catalog access and separate admission
evidence. Existing natural-request source reuse still requires independent
correspondence review. Specialization or changed source follows PFR-011.

The acceleration owner owns import planning, compiler execution, trusted module
artifact caching, and stage timing. Cache keys bind active Lean and Mathlib
versions, source, dependencies, imports, configuration, platform/ABI where
relevant, and artifact digests. Cached .olean files are executable module
artifacts, not portable proof snippets or certificates for an arbitrary request.
Cache metadata shall not be mistaken for catalog admission or semantic review.

## Parallel ownership and release

Work streams: security; synthetic geometry and input formalization; chat diagrams;
theorem retrieval; Lean compilation acceleration; mathematical coverage.
Each uses the existing PALS project. Each implementation chat checks for a
suitable attached worktree and creates one only when needed, then initializes
only its owning submodules. Do not edit the shared primary checkout concurrently.
Reuse dependencies and services where isolation permits; do not duplicate stacks.

Each chat commits and pushes only its own validated changes and opens review
PRs. Child repositories are pushed before parent gitlinks are updated. Merge
and production activation remain separate release actions. Security findings
are reviewed with exact revisions; no speculative history rewrite or visibility
change is authorized by this roadmap.

Integration order: security results and interface contracts; parallel search,
cache, and diagram slices; geometry producer integration; real cross-repository
verification; family-by-family coverage expansion. A blocked stream does not
prevent disjoint work, but no stream can declare cross-stream completion alone.
