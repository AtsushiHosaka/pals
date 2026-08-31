# Draft Catalog Expansion specification loop ledger

## Baseline

- Objective: make the PALS Draft catalog sufficiently comprehensive for Japanese
  elementary, junior-high, and high-school mathematics plus the undergraduate core and
  selected advanced mathematics, and make the admitted catalog searchable in local and
  production runtime.
- User constraints: keep the six-field Draft record; do not store grade, topic, or
  difficulty in the Draft database; keep Draft content as OpenMath, proof strategy, and
  Sketch rather than persisted Lean source.
- Parent revision: `4c887ef385fbeedfe5c46ff753c0d7768bda31a3`.
- Submodule revisions: `pals-agent@9b696dd2492f6bb34cc6740e9112a7063a811e4d`,
  `pals-api@3560db1f2c07a692b4c199a4c8315b23f1b3ebe9`.
- Observed local runtime: legacy `public.dsp_drafts` table with 431 rows; packaged
  generic seed with 31 rows; isolated typed catalog with 163 embedded cards across 13
  profiles.
- Working tree: dirty before this loop. All pre-existing tracked and untracked changes
  are user-owned and must not be overwritten, staged, committed, reset, cleaned, or
  stashed.
- Loop budget: two complete iterations. First stage budget: specification and first
  evidence-producing implementation slice, at most two hours.

## Iteration record

| Iteration | Spec revision | Code revision | Trigger | Expected verdict-changing delta | New evidence | Findings opened/closed | Routes invoked | Stage/overall budget | Elapsed | Stop/cancel action | Result |
|---|---|---|---|---|---|---|---|---|---:|---|---|
| 1 | working draft | parent `4c887ef3`; agent `9b696dd2`; api `3560db1f` | User approved comprehensive expansion while preserving the Draft record | Pin measurable completeness, profile separation, publication, evaluation, and staged implementation | 107 school families/321 cells; 100 undergraduate families/500 cells; 12 advanced target groups/500 target patterns; repository inventory 31 packaged, 398 generic authored unique, 222 typed authored, 163 typed loader-supported | Closed: school taxonomy, undergraduate target matrix, Draft/Lean admission contradiction, missing binding/source contracts. Open: DB adapter, generic and typed runtime publication | `sdd-generate-spec`, `sdd-review-spec`, `sdd-update-spec`, `sdd-implement-spec`; delegated coverage and implementation reconnaissance | 2h stage / 6h ceiling | in progress | Parent cancels delegated work at stage boundary | working slice tests pass; runtime not verified |
| 2 | working draft | parent `4c887ef3`; uncommitted working tree | First evidence-producing authoring and reconciliation slices | Add 12 exact school families and five undergraduate foundation families without changing the Draft record or falsely claiming admission | 24 original generic-v1 Drafts; school coverage 36/321 filled and 0/321 admitted; undergraduate coverage 25/500 filled and 0/500 admitted; generic authored unique count 422; local DB remains legacy 431 and typed authoring 163; runtime catalogs absent | Closed: ambiguous anchor IDs, binding/source/profile reconciliation, stale text summary, generic hard-negative placeholders, six school precursor gaps. Open: embedding data-egress approval, DB insertion, admission, publication, retrieval evaluation, remaining 285 school and 475 undergraduate cells | `sdd-implement-spec`; actual OpenMath and typed-profile validators; SELECT-only local DB audit; delegated school/university slice mapping | 2h stage / 6h ceiling | in progress | Stop before external Draft data egress or DB write without explicit approval | 13 contract tests pass; two school generators/profile-valid; five university families meet all mode/difficulty cells; runtime NOT VERIFIED |

## Delegation record

| Delegation ID | Agent/skill | Owned slice | Mode/owned paths | Input revisions | Prompt summary | Stage/command budgets | Required verification | Result revision/status | Evidence and NOT VERIFIED | Elapsed/retries/stop action | Next route |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DCE-D001 | school coverage investigator | Japanese elementary, junior-high, and high-school coverage contract | read-only / none | parent `4c887ef3` | Derive concept-family, problem-mode, difficulty, target, and generic/typed feasibility matrices from official curriculum and repository evidence | 25m; commands/web 2m; two retries | Official curriculum source per family or explicit recommendation label; no coefficient variants | complete / no writes | 107 families, 321 cells, official MEXT sources; authoring and publication NOT VERIFIED | no retry; returned after bounded research | merged into matrix/design |
| DCE-D002 | university coverage investigator | Undergraduate core and advanced extension coverage contract | read-only / none | parent `4c887ef3`; typed DB baseline 163 | Reconcile supported typed evidence and derive prerequisite, family, mode, target, and profile-gap matrix | 25m; commands 2m; two retries | Reconcile manifest/test counts; proposal is not runtime admission | complete / no writes | 100 core families, 500 cells; advanced aggregate target 500; typed loader test passed; runtime NOT VERIFIED | no retry; returned after bounded research | merged into matrix/design |
| DCE-D003 | implementation reconnaissance | Parent-script and test conventions, reusable inventory boundaries | read-only / none | working spec iteration 1 | Find safe exact paths and identify contract gaps before DCE-T001/T002 implementation | 25m; commands 2m; two retries | Exact source/test references; no workspace or DB mutation | complete / no writes | Found missing Draft bindings, classification registries, capacity declarations, and closed inventory sources | no retry; returned after sufficient evidence | gaps corrected through `sdd-update-spec`; implementation resumed |
| DCE-D004 | school next-slice mapper | Six generic prerequisite families joining the first school anchors | read-only / none | working spec iteration 2 | Identify exact reusable Drafts and genuine authoring gaps for three modes per family | 20m; commands 2m; no retry | Semantic fit, source path, collision risk and hard negatives | complete / no writes | Recommended six families; 12 exact reusable patterns and six model/square-root gaps; admission NOT VERIFIED | stopped after bounded mapping | author second school generator and bindings |
| DCE-D005 | undergraduate first-slice mapper | Five high-impact foundation families | read-only / none | working spec iteration 2 | Select prerequisite roots and map five modes per family without relabeling weak candidates as comprehensive | 20m; commands 2m; no retry | Exact IDs/paths, profile fit, structural collision and hard negatives | complete / no writes | 25 bindings applied; functions remain scalar-instance coverage, not a general typed maps profile; admission NOT VERIFIED | stopped after bounded mapping | add family evaluation corpus and typed-discrete successor |

## Human decision queue

| Batch ID | Decision ID | Actor + trigger/state + observable question | Known facts | Options and impact | Recommendation | Affected IDs | Answer/authority | Resulting spec revision | Status |
|---|---|---|---|---|---|---|---|---|---|
| DCE-H001 | DCE-DEC-001 | When operators expand the catalog, whether Draft rows gain curriculum fields | The six-field record is sufficient for runtime retrieval; curriculum data is authoring-only | Keep external metadata, or migrate the Draft schema | Keep external metadata | DCE-001, DCE-002 | User: no grade/topic/difficulty fields in DB | draft iteration 1 | resolved |
| DCE-H001 | DCE-DEC-002 | Whether a Draft row stores Lean source | A Draft is OpenMath plus strategy and Sketch; Lean evidence has a separate lifecycle | Keep evidence external, or store Lean in Draft | Keep evidence external | DCE-001, DCE-006 | User: current Draft content is correct | draft iteration 1 | resolved |

## Requirement evidence

| Requirement | Design | Task | Code revision/location | Test/runtime evidence | Freshness | Status | Owner/next action |
|---|---|---|---|---|---|---|---|
| DCE-001 | `design.md` Draft boundary | DCE-T004/T005 | existing six-field contracts, no DB migration | repository inspection | fresh 2026-08-28 | working contract | root |
| DCE-002–DCE-005 | `coverage-matrix.v1.json` and schema | DCE-T001/T002/T008–T011 | `pals-scripts/audit-draft-catalog-coverage.py`; two school-algebra candidate manifests | 13 contract tests; targets reproduced; school 36/321 and undergraduate 25/500 filled; 0 admitted | fresh 2026-08-29 | first slices authored/reconciled, not admitted | root; add admission evidence and next slices |
| DCE-006–DCE-007 | separate admission/evidence design | DCE-T002/T004/T005 | inventory state separation | repository-only states stop at authored/profile-valid declarations | fresh 2026-08-28 | partial | add admission manifests |
| DCE-008–DCE-010 | generic/typed immutable publication design | DCE-T004–T006 | existing generic PFI; typed runtime absent | DB/runtime `not_checked` | NOT VERIFIED | open | API/agent implementation |
| DCE-011–DCE-012 | evaluation and rollback design | DCE-T007 | existing generic release evaluator only | changed-family evaluation not run | NOT VERIFIED | open | runtime milestone |
| DCE-013–DCE-014 | source references and deterministic inventory | DCE-T001/T002/T012 | closed source registry and audit command | deterministic-output test, official school references, SELECT-only local Compose audit: legacy 431, typed authoring 163, generic/typed runtime absent | fresh 2026-08-28 | repository and local DB inventory implemented; DB role boundary not proven | add dedicated read-only role integration test |
| DCE-015–DCE-016 | private runtime/capacity design | DCE-T003/T005/T006 | generic limit 4096 declared; typed limits absent | capacity test passes; 24 profiles report not configured | fresh 2026-08-28 | partial | define typed runtime limits with API work |

## Invalidated or NOT VERIFIED evidence

- Historical `expected-existing-count` values in candidate generators do not prove the
  current catalog population.
- The 431-row legacy table does not prove production/PFI publication.
- Presence in `pals_local_typed_catalog` does not prove runtime admission or searchability.
- Proposal and sealed-authoring status do not prove statement/OpenMath/Lean alignment
  admission unless the corresponding review and receipt are revalidated.
- The repository inventory's `loader_supported` field is a closed source declaration;
  the existing typed loader profile test passed on 2026-08-28, but publication and
  runtime retrieval remain NOT VERIFIED.
- A 2026-08-29 SELECT-only check found zero of the 24 newly authored school IDs in the
  431-row legacy table. Loading them would require sending their canonical OpenMath,
  strategy, and Sketch embedding text to the pinned OpenAI embedding endpoint; explicit
  data-egress approval is pending.
- Python standard-library validation enforces the matrix and source semantic contract;
  general JSON Schema Draft 2020-12 conformance is NOT VERIFIED in the current environment.
