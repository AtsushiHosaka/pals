# Private AWS migration profile

Approved working baseline: the user's 2026-10-30 instruction to execute the Mac
mini migration, use private subnets, preserve features/data, and support the
selected normal/event capacity modes. This profile supersedes the original
single-public-host and auto-pause choices for this migration only. The original
default path remains supported; its evidence does not prove private deployment.

| ID | Requirement and verification |
| --- | --- |
| PAM-001 | Preserve DPB-001/007 account, region, saved-plan, source identity and non-secret receipts. Explicit migration authorization covers deployment; CLI mutation flags remain mandatory. Reject deletes and managed changes to existing Cognito, artifact buckets, queues and signing keys. |
| PAM-002 | Replace DPB-008/011 networking with two public ALB subnets, two private control subnets, two private compute subnets, and two isolated DB subnets. Workloads have no public IP/SSH. Permit ALB→control HTTPS, control→verifier mTLS and control→DB only. Use one NAT, an S3 gateway endpoint, ACM and retained Cloudflare DNS. Validate actual routes/SGs after apply. |
| PAM-003 | Replace DPB-003 delivery with native arm64 API/Web and amd64 worker/verifier images. Bind exact OCI digest, sources, toolchain and platform into the signed release. Reject architecture or identity mismatch before readiness. |
| PAM-004 | Retain DPB-009 encryption, bounded capacity, backups and deletion protection, with Aurora minimum 0.5 ACU and initial maximum 2 ACU for latency. Verify the Tokyo engine is currently orderable. One initial writer provides no instance failover redundancy. |
| PAM-005 | Extend DPB-005 with a distinct source→Aurora migration carrier. Capture a consistent current dump and authority inventory under the existing source lock; retain predecessor signatures. Verify target identity, TLS, emptiness, locale, roles/owners/ACLs, rows, sequences and original documents. Do not reuse the Mac same-host carrier or admit a preparation plan as a restore. |
| PAM-006 | Extend DPB-010/012 with separate control/compute credentials and release-bound per-node mTLS. Worker has no DB credential; verifier has no AWS/provider/DB credentials and remains isolated. Preserve notification, durable claim, retry and independently verified acceptance. |
| PAM-007 | Start normal capacity with t4g.medium control and one r8a.large compute node. Event uses r8a.xlarge. Prepare new slots before routing, drain old work before termination, reject stale/duplicate results, and bound auto scaling by queues and ready slots. An empty ASG is not working capacity. |
| PAM-008 | Preserve Cognito identities/callbacks, external resources, guest-key fingerprint, histories, documents, sharing, continuation, quotas and all existing entry points. Fence source writers before the final snapshot and allow one writing environment at cutover. After target writes, DNS rollback alone is insufficient. |
| PAM-009 | Extend DPB-014/015 with private runtime readback, real model/Lean checks, recovery and cost reporting including NAT/ALB/IPv4/DB. Preserve ACTUAL USD20/50/100 notifications. The private profile uses a USD650 monthly budget with additional ACTUAL USD650 and FORECASTED USD520 email alerts, with no automatic stop action. The fixed JPY150/USD planning conversion is not an exact JPY spending cap. Treat 1-second answers and 30 submissions within 10 seconds as measured targets. |
| PAM-010 | The user's 2026-10-30 compatibility-first decision permits Aurora adoption only after a separately isolated rehearsal verifies every source row, sequence, large object, owner/ACL/role restriction and applicable search behavior. Record the actual extension and collation-provider differences; obtain authoritative security-fix evidence for the managed build. Keep the final target empty and source serving during rehearsal. An ordinary live snapshot or compatibility report cannot authorize final admission, alter signed source evidence, weaken the existing strict restore profile, or replace the final drained capture. |

Design and execution evidence live in the [architecture document](../../docs/aws-low-latency-architecture-2026-10-30.md),
[runbook](../../docs/aws-migration-runbook-2026-10-30.md), and
[editable diagram](../../docs/diagrams/pals-aws-private-target.drawio).
The runbook records implementation, local verification, deployment and acceptance
separately. This document does not mark these requirements complete.

The observed source uses vector0.8.7 and libc2.36; the reserved Aurora16.15
offers vector0.8.2 and reports libc2.26-59.amzn2. The
[owning API review](../../pals-api/docs/aurora-compatibility-review.md) defines
the proposed data, authority and search replay. None of that replay has run.
Use a distinct private rehearsal cluster because application roles are
cluster-wide. The current final-restore v1 rejects these version/locale
differences and remains unchanged; any future supported profile requires its
own reviewed implementation and evidence.
