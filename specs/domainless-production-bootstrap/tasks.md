# Domainless Production Bootstrap Tasks

## Implementation Plan

- [ ] DPB-T001 Split the production Terraform root into closed `foundation`, `application`, and `public` modes.
  - Covers: DPB-002, DPB-006
  - Verification: `terraform fmt -check`, `terraform validate`, and Terraform tests prove foundation/application create no listener, public ingress, API/worker task definition, API service, or worker service, except for the scoped private database-release task in application; public mode requires all HTTPS inputs.

- [ ] DPB-T002 Make ECR and four secret-container prerequisites deployable before application task definitions.
  - Covers: DPB-003, DPB-004
  - Verification: a foundation plan needs no image digest or secret ARN input; application requires only an API ECR `@sha256:` reference, public requires API and worker references, Terraform state contains no secret value or secret version, and release/runtime database secret references remain distinct.

- [ ] DPB-T003 Add a manifest-backed production database release entry point to the API image.
  - Covers: DPB-005
  - Verification: clean PostgreSQL integration test proves baseline roles/schemas/extensions plus every migration are applied in order and idempotently; only the release task receives the privileged release connection, the runtime connection cannot perform role/DDL operations, and API startup performs only manifest-status/readiness verification.

- [ ] DPB-T004 Add the private Fargate release task definition and outputs for running/verifying the database release.
  - Covers: DPB-005
  - Verification: Terraform tests assert the task has no listener/public IP, gets only the two distinct database secret ARNs, uses private subnets/release-only security group, and has the release entry point; a real AWS foundation/application smoke run succeeds before public enablement.

- [ ] DPB-T005 Implement `scripts/production-deploy.sh` with guarded state-backend bootstrap and non-mutating plan.
  - Covers: DPB-001, DPB-007
  - Verification: shell tests cover `bootstrap`, `plan`, account/region guard, absent confirmation, state bucket controls, and secret-safe receipt generation; `plan` test asserts no mutating AWS CLI command is invoked.

- [ ] DPB-T006 Implement image delivery, protected secret injection, and application release orchestration in the deploy script.
  - Covers: DPB-003, DPB-004, DPB-005, DPB-007
  - Verification: shell tests prove infrastructure/API/worker clean-source gate; the `pals.source-worktree.v1` manifest digest separately binds stage-0 index entries and working-tree bytes, including staged-then-modified, staged deletion plus recreated worktree file, unstaged, deleted, and non-ignored untracked source; receipt redacts its manifest; agent-supported worker builder invocation, digest resolution, secret-file permission/redaction rules, failed-task halt, and retry receipt all pass.

- [ ] DPB-T007 Implement guarded public enablement and write operator documentation/config examples.
  - Covers: DPB-006, DPB-007
  - Verification: shell/Terraform tests reject no-domain/invalid-cert/non-HTTPS callback inputs; documentation walkthrough ends at domainless application readiness and separately lists the exact domain inputs required for public mode.

- [ ] DPB-T008 Run static validation and the production readiness review before any real AWS apply.
  - Covers: DPB-001 through DPB-007
  - Verification: API tests, shell tests, Terraform validation/tests, secret scan, `sdd-review-spec`, and `sdd-review-code` pass. A real AWS apply requires a separate explicit operator request and credentials.
