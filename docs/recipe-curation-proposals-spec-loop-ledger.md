# Recipe Curation Proposals — Specification Loop Ledger

## Iteration record

| Iteration | Spec revision | Code revision | Trigger | Expected verdict-changing delta | New evidence | Findings opened/closed | Routes invoked | Result |
|---|---|---|---|---|---|---|---|---|
| 1 | Parent `8bd6dd7` (dirty) | API `d9c18af` (dirty) | User approved the dialogue → curation proposal → independent Recipe admission direction | Define an internal proposal queue without automatic promotion or stored conversation content | Read-only review identified origin derivation, curator contract, lifecycle, and privacy gaps | Opened RCP-001–006; corrected origin preimages, identity, lifecycle, and access scope | `sdd-update-spec` → `sdd-review-spec` | Re-review required |
| 2 | Same working baseline; RCP revised | Same | Targeted review found v1 provenance claim and list contract incomplete | Label v1 origin as provenance-unknown and close list pagination grammar | Existing v1 candidates lack source kind; current API needs bounded list semantics | Corrected both P1 findings; final terminology sweep corrected stale `legacy_model_v1` wording | `sdd-run-loop` → `sdd-update-spec` → `sdd-review-spec` | Ready for implementation review |
| 3 | RCP response contract revised | Same | HTTP implementation required a successful response grammar | Define the shared proposal response for propose and decision | Closed request/list objects already existed; successful mutation response was implicit | Added an exact summary response; no lifecycle or data-boundary change | `sdd-update-spec` | Ready for implementation |
| 4 | Parent `255bf16` | API `5dcbf1d`, `58a4923`, `a0e12b8` | Implement RCP-T001--T004 | Dedicated curation roles, closed internal API, RFC 8785 Origin derivation, and real-PG proof | PostgreSQL 16 fresh database: migration, verified v1 candidate proposal, approval, denied proof-job table read, append-only trigger, and no Recipe schema | Closed implementation gap; Recipe catalog remains outside the proposal path | `sdd-implement-spec` → unit + real PostgreSQL integration | PASS |

## Delegation record

| Delegation ID | Agent/skill | Owned slice | Mode | Input revision | Result |
|---|---|---|---|---|---|
| RCP-DL-001 | `spec_audit` / `sdd-review-spec` | RCP requirements, design, tasks; LRC/RPCS consistency | Read-only | Parent `8bd6dd7` dirty | First review found derivation, auth, lifecycle, privacy, and test-scope gaps; targeted re-review found two P1s; iteration 2 re-review pending. |

## Requirement evidence

| Requirement | Design | Task | Code/test evidence | Status | Next action |
|---|---|---|---|---|---|
| RCP-001–RCP-006 | `specs/recipe-curation-proposals/` | RCP-T001–T004 | API commits `5dcbf1d`, `58a4923`, `a0e12b8`; 28 unit and 2 PostgreSQL integration tests passed | Verified | Maintain the separate Recipe authoring/alignment gates |
