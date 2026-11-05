# Cost-Conscious Production Bootstrap Tasks

Private AWS migration execution is tracked separately in the
[migration runbook](../../docs/aws-migration-runbook-2026-10-30.md), against the
[approved profile](private-aws-migration.md). Completed tasks below are historical
evidence for the original path and do not imply private deployment is complete.

- [ ] PAM-T010 Receive and verify the protected live rehearsal bundle, restore the
  same snapshot into an isolated source-equivalent baseline and private Aurora
  rehearsal cluster, compare all data/authority and applicable search behavior,
  and verify the managed build's security-fix status. Record failures without
  changing the source or final target; design any necessary final-restore profile
  separately. This is not final admission. Covers: PAM-005, PAM-008, PAM-010.

- [x] DPB-T001 Create the guarded backend bootstrap and non-mutating plan entry point.
  - Covers: DPB-001, DPB-007

- [x] DPB-T009 Replace the production Terraform network/compute graph with the two-phase
  single-EC2 architecture and remove ALB, ECS, NAT and VPC endpoints.
  - Covers: DPB-008, DPB-011

- [x] DPB-T010 Configure Aurora 0-ACU auto-pause, private access, managed credentials,
  bounded maximum capacity and retained backups.
  - Covers: DPB-009

- [x] DPB-T011 Add least-privilege EC2 instance profile, SSM-only administration, ECR
  digest pulling and external SecureString parameter contract.
  - Covers: DPB-003, DPB-010

- [x] DPB-T012 Add host bootstrap/runtime orchestration, database release gate, isolated
  mTLS verifier/reconciler, Caddy routing and scheduled pg_dump-to-S3 backup.
  - Covers: DPB-005, DPB-011, DPB-012
  - KMS-bound release, exact RDS-master capability, three runtime URLs, mounted mTLS boundary,
    and fail-closed startup have targeted automated evidence.

- [x] DPB-T013 Add production ARM64 web image and bounded Aurora-resume startup retry.
  - Covers: DPB-003, DPB-013

- [x] DPB-T014 Replace Terraform tests with cost, isolation, auto-pause, DNS, IAM and
  backup contracts; run formatter, validate, targeted API/agent tests and deploy mocks.
  - Covers: DPB-008 through DPB-013
  - Terraform/API/agent boundary checks and guarded deploy mocks pass; real image push remains NOT VERIFIED.

- [x] DPB-T016 Replace the one-second verification-candidate database poller with an
  event-driven, private in-host trigger backed by existing proof-job SQS redelivery, and remove
  the API's five-second proof-delivery database loop after its startup recovery pass.
  - Covers: DPB-009, DPB-012, DPB-013
  - Completion requires durable-import notification, bounded/fail-closed ingress, idempotent
    redelivery evidence, an idle-no-database-call test, and proof that Terraform adds no queue,
    scheduler, Lambda, or proxy.
  - Targeted API/unit tests, the complete API unit suite, Ruff/Mypy, the production cost boundary,
    Terraform formatting/validation, and all four Terraform native tests pass.

- [ ] DPB-T017 Complete and test the cross-repository production configuration contract: Cognito
  password auth, API/worker Recipe and artifact bindings, 20-second SQS long polling, and complete
  non-secret plan/apply receipts.
  - Covers: DPB-014

- [ ] DPB-T018 Add the monthly AWS budget and absolute USD 20/50/100 actual-cost email
  notifications for `hosaka2917+pals@gmail.com`.
  - Covers: DPB-015

- [ ] DPB-T015 Generate a fresh real-AWS plan after DPB-T017/018, invalidate every prior plan,
  review all cost-bearing resources, and obtain a separate apply confirmation.
  - Covers: DPB-001, DPB-007, DPB-014, DPB-015
  - The prior 33-add and 38-add foundation plans predate the completed production contract and
    budget resources, so neither is eligible for apply.
