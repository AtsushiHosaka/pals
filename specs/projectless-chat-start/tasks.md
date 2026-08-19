# Projectless Chat Start Tasks

- [x] PCS-T001 Add the v3 immutable chat migration and migration-state detection for user-created projectless chats.
- [x] PCS-T002 Add owner-scoped `POST /v1/chats` and update chat domain/repositories/OpenAPI/docs.
- [x] PCS-T003 Permit proof jobs for projectless chats while preserving owner, language, and chat-project checks.
- [x] PCS-T004 Run chat migration during container startup and cover fresh/upgrade migrations with PostgreSQL tests.
- [x] PCS-T005 Change dashboard/sidebar/new-chat flows to create and navigate projectless chats without opening project creation.
- [x] PCS-T006 Add the projectless chat screen, proof interaction, error recovery, and frontend behavior tests.
- [x] PCS-T007 Execute API, frontend, migration, and local browser smoke verification; update these tasks from evidence. (2026-08-14: local authenticated browser QA confirmed New chat creates a projectless chat, proof submission returns 201 with `project_id: null`, chat selection/reload preserves the queued proof, and the explicit project dialog remains separate.)
