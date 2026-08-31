# Recipe Curation Proposals Tasks

| ID | Task | Requirements | Verification |
|---|---|---|---|
| RCP-T001 | Add API-owned immutable proposal/event schemas, exact Origin-binding validation, lifecycle lock/transition function, curation identities, role grants, release migration, and migration-state detection. | RCP-001–RCP-003, RCP-005 | Real PostgreSQL fresh/upgrade, role denial/grants, UPDATE/DELETE rejection, one-Origin uniqueness, stale-transition, and rollback tests. |
| RCP-T002 | Implement the dedicated-secret internal propose, decision, and curation-only list operations. Derive v1 and v2-model Origin bindings from the permitted durable columns; reject caller evidence, Recipe origins, incomplete/non-verified origins, free text, and all invalid credentials. | RCP-001–RCP-006 | Unit, HTTP/service, repository, idempotency, conflict, authorization, and no-conversation-data tests. |
| RCP-T003 | Run a real PostgreSQL + internal API integration using actual persisted v1 and v2-model proof evidence. Prove decision leaves Recipe/alignment rows, events, receipts, and traces unchanged and curation roles have no catalog grant. | RCP-001–RCP-006 | Fresh durable-state inspection and integration artifact. |
| RCP-T004 | Document curator operation, data-minimization boundary, closed reason/error registry, and the separate later Recipe authoring/alignment workflow. | RCP-003, RCP-004, RCP-006 | Documentation review, secret scan, and diff check. |

## Completion gate

The first slice is complete only when RCP-T001 through RCP-T004 have real PostgreSQL evidence.
Unit tests, manually constructed Origin bindings, or a successful proposal record alone do not
prove source derivation, role isolation, or the no-Recipe-promotion boundary.
