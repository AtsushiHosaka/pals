# Draft Catalog Expansion Requirements

## Overview

PALS shall expand its reusable Draft catalog until it covers the required problem and
proof patterns of Japanese elementary, junior-high, and high-school mathematics, the
undergraduate mathematics core, and explicitly selected advanced domains. Expansion
shall increase usable retrieval coverage rather than merely add rows.

A Draft remains a six-field retrieval record: stable identity, canonical statement,
canonical OpenMath, proof strategy, Sketch steps, and embedding. Curriculum placement,
authoring evidence, Lean compiler evidence, review state, and publication state remain
outside the Draft record.

## Goals

- Define a measurable, machine-readable standard for sufficiently comprehensive
  coverage without counting coefficient or variable-name substitutions as new patterns.
- Fill the elementary and junior-high gap, complete high-school subject coverage, and
  broaden undergraduate and advanced mathematics.
- Make admitted generic and typed Drafts searchable in local and production runtime.
- Preserve profile-specific OpenMath meaning, immutable publication, rollback, and
  reproducible evaluation.

## Non-goals

- Add grade, topic, difficulty, provenance, lifecycle, or Lean fields to Draft rows.
- Store Lean source or compiler receipts in the Draft catalog.
- Mix typed OpenMath profiles into the generic profile or its generation.
- Claim that textbook exercises were copied or exhaustively reproduced.
- Count altered constants, renamed variables, or paraphrases as distinct coverage.
- Make Draft retrieval itself establish theorem equivalence or proof correctness.

## Users

- Learners: need a relevant reusable proof approach for problems across their curriculum.
- Draft authors: need an explicit backlog and deterministic admission gates.
- Operators: need immutable, measurable, reversible catalog publication.
- Proof runtime: needs profile-correct candidates with compatible embeddings and
  canonicalization.

## Functional requirements

| ID | Requirement | Priority | Source |
|---|---|---|---|
| DCE-001 | The system shall preserve the existing six-field Draft content contract and shall keep curriculum metadata and Lean evidence outside the Draft row. | Must | User decision |
| DCE-002 | The project shall maintain a versioned machine-readable coverage matrix that maps each required curriculum or university concept family to required problem modes, difficulty bands, profile feasibility, prerequisite families, and admitted Draft identities. | Must | User goal |
| DCE-003 | Coverage shall include Japanese elementary grades 1–6, junior-high grades 7–9, high-school Mathematics I/A/II/B/III/C, the undergraduate core through the usual second-year sequence, and the selected advanced domains declared by the coverage matrix. | Must | User goal |
| DCE-004 | A scope may be called sufficiently comprehensive only when every required coverage cell is filled by at least one admitted structurally distinct Draft, every required family contains the declared diversity of problem modes and difficulty bands, and the scope passes its retrieval evaluation corpus. | Must | User goal |
| DCE-005 | The coverage calculation shall reject row-count inflation: canonical OpenMath collisions, alpha-equivalent statements, variable renaming, constant-only variants, and paraphrases of the same proof pattern shall not satisfy separate required cells. | Must | Existing authoring rule |
| DCE-006 | Each admitted Draft shall pass profile validation, canonicalization, statement/OpenMath alignment review, nonempty strategy, appropriate Sketch validation, and collision checks. Nearby false or materially different statements shall be covered by hard-negative tests. Draft admission shall not require Lean source, a Lean Recipe, or Lean compiler metadata. | Must | User decision and existing Draft/Recipe separation |
| DCE-007 | The authoring pipeline shall expose a deterministic funnel from backlog to authored, validated, independently reviewed, admitted, embedded, published, and retrieval-evaluated states without placing those fields in the Draft row. Optional external proof evidence shall remain separately reportable and shall not change Draft admission eligibility. | Must | Operational need |
| DCE-008 | Generic Draft publication shall use an immutable generation and active-pointer transition with compatibility checks and rollback; the legacy mutable local-table loader shall not be the production publication path. | Must | Existing PFI design |
| DCE-009 | Typed Draft publication and retrieval shall remain profile-separated from generic publication. A query shall be validated and searched only under an explicitly selected compatible profile, and results from incompatible profiles shall not be merged. | Must | Existing typed design |
| DCE-010 | The runtime shall be able to retrieve every published generic or typed profile that the active coverage matrix marks searchable; authoring-only or unreviewed material shall not be returned. | Must | User outcome |
| DCE-011 | Every release candidate shall be evaluated against versioned positive queries and nearby hard negatives for each changed coverage family. Gates shall report at least structuring success, Recall@k, reciprocal rank, false-match rate, false-no-match rate, and verified proof completion rate. | Must | Retrieval quality |
| DCE-012 | A catalog release shall fail closed on validator, canonicalizer, registry, embedding provider/model/dimension/revision, evidence, manifest, row-count, or profile mismatch and shall leave the previously active catalog searchable. | Must | Compatibility and safety |
| DCE-013 | Coverage references may describe curriculum or textbook-equivalent concept reach, but every Draft statement, strategy, and Sketch shall be independently authored and shall not reproduce copyrighted exercise sets or solutions. | Must | Repository policy |
| DCE-014 | The project shall provide a reproducible inventory command that reconciles coverage declarations with generic generations, typed generations, authoring manifests, embedding rows, external evidence, and active runtime publication. | Must | Operability |
| DCE-015 | Internal generic and typed candidate APIs shall use closed and bounded versioned DTOs, dedicated worker authentication, constant-time secret comparison, and API-owned read roles. The agent shall not receive direct catalog database access. | Must | Existing private runtime boundary |
| DCE-016 | Before authoring or publication, the coverage inventory shall compare the required active population of each profile with its generation and API limits. A scope that exceeds a limit shall require a versioned capacity change and regression evidence rather than silently truncating coverage. | Must | Feasibility |

## Acceptance criteria

### DCE-001: stable Draft boundary

- When a generic or typed Draft is persisted, its retrieval payload shall contain only
  the established Draft content fields for that catalog contract.
- Curriculum classification and evidence state shall be reconstructable from versioned
  manifests without altering the Draft payload.

### DCE-002–DCE-005: measurable completeness

- The coverage matrix shall use stable identifiers for stage, course, domain, concept
  family, problem mode, and difficulty.
- Each required cell shall name its minimum structural pattern count and profile.
- The inventory command shall produce separate counts for required, filled, admitted,
  published, and retrieval-passing cells.
- If two candidates differ only by constants, alpha-renaming, or prose, they shall not
  fill two required cells.
- A scope shall not report `comprehensive` while any required cell is unfilled,
  unpublished, or fails its retrieval gate.

### DCE-003: scope

- The school matrix shall trace its mandatory families to the current official Japanese
  curriculum and shall keep curriculum revisions explicit.
- The university matrix shall declare its reference syllabus or chapter-family boundary,
  prerequisites, and included problem modes.
- Advanced domains shall be opt-in named scopes; their incompleteness shall not be hidden
  inside an aggregate undergraduate percentage.

### DCE-006–DCE-007: admission

- Invalid OpenMath, unsupported typed carriers, missing strategy, invalid Sketch shape,
  canonical collision, or failed alignment review shall stop admission.
- The absence of Lean source, a Lean Recipe, or compiler metadata shall not stop Draft
  admission. When present, formal proof evidence shall remain a separate referenced
  artifact and shall not become part of the Draft payload.
- Authoring-only proposals shall remain distinguishable from admitted and published
  material.

### DCE-008–DCE-010: publication and retrieval

- Publishing a generic release shall create a new immutable generation and atomically
  move the active pointer only after all generation checks pass.
- Publishing a typed release shall retain an explicit profile identity and shall never
  place typed OpenMath into a generic generation.
- A profile mismatch shall return no candidates and a stable diagnostic; it shall not
  fall back to an incompatible catalog.
- A successful publication shall make every admitted row in that generation reachable
  through the real runtime retrieval path.

### DCE-011–DCE-012: release quality and rollback

- Changed families shall carry positive queries and structurally close negative queries.
- Evaluation shall run against the actual candidate population, embedding binding,
  canonicalizer, structural reranker, and runtime limits used by the release.
- Any failed gate shall preserve the previously active generation unchanged.
- Rollback shall select a previously published compatible immutable generation rather
  than modifying historical rows.

### DCE-013: independent authoring

- Coverage manifests may cite an official curriculum or a reference table of contents.
- Draft content shall be original and shall not include copied exercise numbering,
  wording, or solutions.

### DCE-014: inventory

- The inventory shall fail on duplicate coverage-cell ownership, unknown Draft IDs,
  missing profile declarations, conflicting admission states, or database/manifests
  count divergence.
- The inventory output shall be deterministic for the same repository revision and
  database generation.

### DCE-015–DCE-016: private runtime and capacity

- Candidate endpoints shall reject missing, duplicate, or incorrect worker credentials,
  duplicate JSON members, unknown fields, oversized bodies, invalid embeddings, and
  incompatible fingerprints without exposing catalog data.
- The normal agent runtime shall reach catalogs only through the private candidate API
  and shall have no catalog database credential or driver configuration.
- The inventory shall report required, configured, and available population limits per
  profile. If required coverage exceeds a limit, release preparation shall fail before
  building or activating a partial generation.

## Constraints

- Existing user-owned working-tree changes shall be preserved.
- Generic and typed canonicalizer and registry versions are immutable compatibility
  boundaries.
- Production evidence must use real PostgreSQL and the real embedding/runtime contracts;
  downstream verified-completion evidence must additionally use the pinned proof verifier.
  Mocks or fixed responses do not prove completion.
- Publication must not expose authoring-only proposals.

## Assumptions

- Curriculum classification is needed for authoring and measurement, not runtime
  retrieval ranking.
- Formal proof receipts remain separate evidence and may evolve independently from a
  Draft record.
- The first implementation milestone can establish complete inventory and one end-to-end
  school and typed publication slice before the full matrix is authored.

## Open questions

No material product decision is currently open. Exact family lists and targets are
evidence-driven design inputs and do not alter the approved Draft boundary.
