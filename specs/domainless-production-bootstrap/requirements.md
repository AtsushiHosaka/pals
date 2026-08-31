# Cost-Conscious Production Bootstrap Requirements

## Purpose

`palschat.site` の初期公開を、将来の PostgreSQL/pgvector 利用を維持しながら低い固定費で
開始する。初期トラフィックでは単一 EC2 ホストに frontend、API、worker、TLS proxy、
隔離 Lean verifier、verified reconciler を
同居させ、Aurora Serverless v2 はアイドル時に 0 ACU まで自動休止させる。

## Goals

- Terraform state、DNS、データ、認証、コンテナ配布を再現可能に管理する。
- NAT Gateway、ALB、ECS/Fargate、Interface VPC Endpoint の固定費を初期構成から除外する。
- secret 値を Terraform state、tfvars、Git、ログ、コマンド引数に残さない。
- 利用増加時に、Aurora とデータを維持したまま compute 層だけを分離できるようにする。

## Non-goals

- 初期リリースで multi-AZ compute、無停止デプロイ、水平 auto scaling を実現すること。
- ACM 証明書を EC2 に直接関連付けること。
- RDS Proxy を使用すること。RDS Proxy の常時接続は Aurora 自動休止を妨げる。
- Terraform `apply`、secret 投入、アプリケーション公開を暗黙に実行すること。

## Functional Requirements

| ID | Status | Requirement |
|---|---|---|
| DPB-001 | active | Deployment tooling shall provide separate guarded `bootstrap`, `plan`, and `apply` operations. `plan` shall make no AWS mutation; every mutating operation shall validate the exact AWS account and region and require fresh production confirmation. |
| DPB-002 | retired | Replaced by DPB-008 and DPB-009. The former ECS/private-endpoint domainless foundation is not part of the cost-conscious production architecture. |
| DPB-003 | active, changed | Application delivery shall build the checked-out API, web, worker, and isolated Lean verifier sources for `linux/arm64`, push them to the Terraform-created ECR repositories, resolve immutable OCI digest references, and deploy only those digests. Clean-source or explicit content-identity recording remains mandatory. |
| DPB-004 | retired | Replaced by DPB-010. Terraform-managed Secrets Manager containers are removed from the initial architecture. |
| DPB-005 | active, changed | A one-shot initial database release container shall run on the production host before normal services. It shall verify an exact KMS-signed, short-lived bootstrap manifest that binds the AWS account/region, Aurora resource, source revisions, immutable API/web/worker/verifier images, checked-in database artifacts, and the active Lean/Mathlib Recipe toolchain before any database mutation. It shall then create separate least-privilege release, API runtime, verified-reconciler, Recipe-selector, and PFI-reader logins, install `vector`, create the empty application base relations required by PJR/PEX, persist the signed release admission, install PJR/PEX, apply the checked-in migration manifest, install exact runtime grants, and verify every long-running login. Replays of the same manifest shall be idempotent; a changed, expired, incorrectly signed, or resource-mismatched manifest shall fail before mutation. Normal API startup shall remain DDL-free. |
| DPB-006 | retired | Replaced by DPB-011. Public ALB/ACM enablement is removed from the initial architecture. |
| DPB-007 | active | Every operation shall write an ignored, non-secret receipt with the account, region, state key, source identities, image digests, resource identifiers, operation result, and safe retry command. |
| DPB-008 | active | Terraform shall create one VPC, one public EC2 host subnet, two private Aurora subnets in distinct AZs, an Internet Gateway, and no NAT Gateway or VPC endpoint. The only public workload ingress shall be TCP 80/443 to the host; SSH shall be absent. Aurora TCP 5432 shall be reachable only from the host security group. |
| DPB-009 | active, changed | Terraform shall retain Aurora Serverless v2 PostgreSQL with pgvector compatibility, encrypted storage, RDS-managed master credentials, deletion protection and backups. It shall set minimum capacity to 0 ACU, use a bounded auto-pause interval, omit RDS Proxy, keep maximum capacity explicitly bounded, and admit no periodic application-originated database scan while there is no candidate work. |
| DPB-010 | active | Runtime secret values shall be written outside Terraform to named SSM Parameter Store `SecureString` parameters. During first boot only, the EC2 instance profile may read the exact RDS-managed master secret, verify with the exact PALS asymmetric KMS release key, and create/update only the named PALS release, API runtime, reconciler, Recipe-selector, and PFI-reader database URL parameters; application containers shall not receive the master credential. Host-local verifier mTLS keys shall be generated after signed-release admission, kept off Terraform state and SSM/Secrets Manager, separated into server/client read-only mounts, and bound to the release/image/toolchain identity. The profile shall otherwise read only the PALS parameter path, pull only the PALS ECR images, consume/send only the PALS SQS queue, access only the PALS artifact/backup bucket, and use SSM Session Manager. No SSH key or long-lived AWS credential shall be installed. |
| DPB-011 | active | Public mode shall allocate one stable EC2 public IPv4 address and create Route 53 A records for the exact frontend and API domain names. Caddy shall obtain and renew public certificates and route frontend and API hosts to loopback-only containers. Terraform shall not create an ALB, ACM attachment, or synthesized domain. |
| DPB-012 | active, changed | The host shall run frontend, API, worker, isolated Lean verifier, and API-owned verified reconciler containers with restart policies and bounded resources. After a candidate is durably imported, the API shall send its canonical candidate ID to the reconciler over the existing private Docker network; the reconciler shall process only notified candidate IDs and shall not poll PostgreSQL while idle. The notification is an in-memory trigger, not a second durable queue: notification refusal shall make the API request retryable, and an accepted trigger lost during process failure shall be recovered by the already-unacknowledged proof-job SQS delivery and idempotent candidate re-import. The verifier shall be rootless, read-only, capability-free, egress-blocked, and reachable only through TLS 1.3 mTLS using the admitted SPIFFE/SPKI identity; proof services shall not start unless verifier and reconciler readiness pass. A scheduled encrypted `pg_dump` shall upload to the private S3 backup prefix with lifecycle retention; failures shall be visible in the system journal and shall not delete the newest successful backup. |
| DPB-013 | active, changed | API startup and host deployment shall tolerate an Aurora auto-resume delay with bounded retries and fail closed after the deadline. Normal request code shall not maintain an idle connection pool that prevents auto-pause. Durable proof dispatch recovery may scan once during API startup, but no delivery-reconciliation loop shall query PostgreSQL after startup; ordinary proof creation shall continue to send its outbox item in the foreground and fail closed when delivery is not confirmed. |
| DPB-014 | active | Production configuration shall be verified as one cross-repository contract. The Cognito client shall allow the exact password authentication flow used by the frontend. The API shall receive the artifact bucket, active Recipe toolchain identity, and dedicated Recipe/PFI database login URLs required by enabled Recipe selection and candidate admission; the worker shall receive the matching Recipe worker identity and verifier/toolchain bindings. The SQS worker shall use the queue's 20-second long-poll boundary instead of one-second receives. Public release receipts shall record all source commits, four immutable image digests, the saved-plan digest and plan action counts without recording secret values. |
| DPB-015 | active | Terraform shall create one monthly USD 100 AWS cost budget with direct email actual-cost notifications when spend is greater than the absolute USD 20, 50, and 100 thresholds. Every threshold shall notify `hosaka2917+pals@gmail.com` without introducing an SNS topic or subscription. |

## Acceptance Criteria

### DPB-001 / DPB-007

- `plan` validates caller, backend and closed configuration and writes a redacted receipt without changing AWS.
- `apply` without both explicit mutation flags stops before any write.

### DPB-003 / DPB-005

- Public deployment accepts only four ECR digest references ending in lowercase `@sha256:<64 hex>`.
- Database release and mTLS verifier/reconciler readiness complete successfully before API/web/worker startup; failure leaves normal services stopped.
- A forged, expired, wrong-account, wrong-Aurora, wrong-image, or wrong-artifact bootstrap manifest is rejected before role, extension, schema, admission, or parameter mutation.
- A valid first release creates the empty application/PJR/PEX schema and a restricted runtime login; an exact replay is non-destructive and succeeds.
- API startup performs only the checked-in readiness check and retries a paused database for a bounded period.

### DPB-008 / DPB-011

- A Terraform test and plan show zero `aws_nat_gateway`, `aws_vpc_endpoint`, `aws_lb`, and ECS resources.
- Exactly one public EC2 instance and one stable public IPv4 address exist in public mode.
- No security-group ingress rule exposes port 22 or Aurora; Route 53 maps only configured names to the host address.

### DPB-009

- The Aurora plan has `min_capacity = 0`, a 5-to-15-minute auto-pause interval, encrypted private placement, backups, deletion protection in prod, and a bounded maximum ACU.
- PostgreSQL `vector` extension creation remains in the release-owned migration path.
- With no candidate notification, a runtime test proves the reconciler performs no repository call during an interval longer than the former one-second polling period.

### DPB-010 / DPB-012

- Terraform state contains parameter names and IAM ARNs but no parameter values or `aws_ssm_parameter` value resources.
- Terraform creates one asymmetric `ECC_NIST_P256` signing key. The host may only verify/get its public key; signing remains an operator deployment action.
- EC2 is administered through SSM Session Manager and has no key pair.
- Backup objects are encrypted, private, versioned or lifecycle-managed, and retained for the configured period.
- Candidate notification uses only the existing private Docker network and proof-job SQS queue; Terraform creates no additional queue, scheduler, Lambda, or database proxy for reconciliation.
- A durable candidate import triggers reconciliation, notification refusal returns a retryable API error, and redelivery of the existing proof-job message can re-trigger the same candidate without conflict.

### DPB-013

- A test proves startup retries a transient readiness failure and eventually starts Uvicorn.
- A test proves startup exits non-zero without starting Uvicorn when the retry deadline is exhausted.
- A static/runtime boundary proves the serving API starts no periodic proof-delivery database scan after its single startup recovery pass.

### DPB-014

- A cross-repository test proves the frontend password flow is included in the Terraform Cognito client's explicit auth flows.
- Host configuration tests prove the API and worker receive the complete enabled Recipe/S3/toolchain/database contract and no master or release credential.
- An idle worker receive uses `WaitTimeSeconds = 20`; candidate reconciliation remains event-driven and performs no idle database read.
- A public plan/apply receipt records the parent, infrastructure, API, web, worker/agent source commits, all four image digests, a SHA-256 of the saved plan, and create/update/delete/read action counts.

### DPB-015

- Terraform tests show exactly one monthly USD 100 cost budget with three `ACTUAL`, `ABSOLUTE_VALUE`, `GREATER_THAN` email notifications at USD 20, 50, and 100.
- The notification address is exactly `hosaka2917+pals@gmail.com`; no email confirmation token or account contact data enters Terraform state or Git.

## Constraints and Assumptions

- Target account is `828786775577`, region is `ap-northeast-1`, and production state remains
  `s3://pals-tfstate-828786775577-ap-northeast-1/pals/prod/terraform.tfstate`.
- Route 53 zone `Z03464212MY64JSAVQSNN` owns `palschat.site`; registrar delegation may still be propagating.
- Initial host default is ARM64 `t4g.medium` with encrypted gp3. This is a single-host availability tradeoff.
- Frontend is `app.palschat.site`; API is `api.palschat.site`.
- The already-requested regional ACM certificate may remain for later ALB migration but is unused here.
- AWS Budgets notifications use the direct email subscriber contract; SNS and its subscription-confirmation flow are outside this initial architecture.

## Open Questions

None for the approved initial architecture. Scaling compute away from the single host is a later migration.
