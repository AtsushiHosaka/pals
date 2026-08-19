# Domainless Production Bootstrap Requirements

## Purpose

独自ドメイン未取得の間にも、PALS の実 AWS 本番基盤を再現可能に作成し、アプリケーション
イメージと必要な secret を安全に投入できるようにする。ドメインと ACM 証明書を追加するまで、
学習者向けの公開 HTTPS/API 認証導線は有効にしない。

## Goals

- 一つの明示的な production deploy コマンド群で、state backend、ECR、AWS 基盤、secret、
  immutable image digest、API migration を順番に扱えるようにする。
- secret 値を Terraform state、tfvars、Git、標準出力、引数履歴に残さない。
- ドメイン取得後に同じ state を保ったまま HTTPS 公開へ移行できるようにする。

## Non-goals

- ECS/ALB の生成 URL を正式な独自ドメインや TLS 証明書として扱うこと。
- ドメイン未取得の状態で、HTTP 経由の学習者向け API、ブラウザ認証、または frontend を公開すること。
- AWS アカウント、Route 53 hosted zone、独自ドメイン、OpenAI API key を自動購入・自動取得すること。
- 実際の AWS resource 作成を、明示的な apply 操作なしに起こすこと。
- 初回 Aurora/ECS 作成のクラウド待機時間をゼロにすること。

## Users

- PALS operator: AWS 認証済みの端末から本番基盤を安全に初期化・更新したい。

## Functional Requirements

| ID | Requirement |
|---|---|
| DPB-001 | The deployment tooling shall provide separate `bootstrap`, `plan`, and `apply` operations. `bootstrap` shall create or validate the dedicated encrypted, versioned Terraform state bucket before Terraform initialization. `plan` shall perform no AWS mutation. `apply` shall require an explicit production confirmation and shall fail before any mutation when the selected AWS account, region, required tools, repository revisions, or configuration are invalid. |
| DPB-002 | When no domain and ACM certificate are supplied, the production Terraform configuration shall create the private data plane, ECR repositories, Cognito user pool, ECS cluster, queues, logs, and named secret containers, but shall not create a Cognito browser client, an internet-reachable listener, an API/worker task definition or service, or internet ingress. It shall output a clear `domainless_foundation_ready` state and the exact next domain-enable command. |
| DPB-003 | The deployment tooling shall use the checked-out PALS infrastructure, API, and worker source revisions to apply Terraform and build images. It shall require each checkout to be clean and record its commit ID; an explicit recorded override may name each dirty checkout and its `pals.source-worktree.v1` content identity. That identity shall SHA-256 the RFC 8785 source manifest of the complete Git index and the current worktree state for every tracked, staged, unstaged, deleted, and non-ignored untracked file admitted by the clean gate. It shall push the PALS API and worker images to the Terraform-created ECR repositories, resolve immutable OCI digest references, and pass only the digest references to Terraform. |
| DPB-004 | The deployment tooling shall create or update only named Secrets Manager secrets outside Terraform state: a privileged database release URL, a least-privilege API runtime database URL, API/worker shared secret, and OpenAI API key. It shall receive the OpenAI key only from a local protected input, generate the database-role and shared-secret values cryptographically, and construct database URLs only after Aurora exposes its endpoint and RDS-managed credential. It shall never echo, persist, or commit secret values. |
| DPB-005 | When the domainless foundation and required secrets exist, the tooling shall run a dedicated, one-shot private release task using the privileged database release URL. It shall establish the production database roles/extensions, assign the API runtime role only the privileges required for runtime operations, and apply every checked-in API migration in its declared order. It shall verify the completed schema and runtime-role access without starting an API service or worker. A failed release task or verification shall halt the operation and report non-secret diagnostics without declaring deployment success. |
| DPB-006 | When an operator supplies a verified `api_domain_name`, an issued regional ACM certificate ARN, exact HTTPS frontend origin, and Cognito callback/logout URLs, the tooling shall enable the public HTTPS listener, learner-serving API, and SQS-driven worker service with a minimum count of zero. It shall not synthesize a hostname, certificate, CORS origin, or OAuth callback URL. |
| DPB-007 | Every operation shall write a local, ignored deployment receipt containing no secret values: account ID, region, Terraform state key, source revision IDs, image digests, resource identifiers, operation timestamp, and domainless/public status. The tooling shall print the same non-secret summary and exact safe retry command. |

## Acceptance Criteria

### DPB-001

- When an operator runs `plan`, the tooling validates prerequisites and produces a Terraform plan without creating or changing AWS resources.
- When an operator runs `apply` without the production confirmation, the tooling performs no mutation.
- If the state bucket exists with encryption, versioning, public-access blocking, and ownership matching the selected account, bootstrap reuses it; otherwise it fails safely.

### DPB-002

- When no domain configuration is supplied, apply provisions the domainless foundation but no security group permits internet ingress to an ALB listener and no learner-serving ECS task starts.
- The receipt states that the foundation is not public and names the required domain-enable inputs.

### DPB-003

- When the infrastructure, API, and worker source revisions are clean, apply deploys only resolved `@sha256:` image references.
- If any source revision is dirty, the operation stops before build or AWS mutation unless the operator uses the documented explicit override that identifies the affected checkout and its content identity.

### DPB-004

- When required protected local inputs are available, the four named secrets are available to their exact ECS consumers by ARN without their values appearing in Terraform plans, state, receipt, logs, command arguments, or committed files.
- The public API task receives only the API runtime database URL; the privileged database release URL is available only to the private release task.
- If a secret cannot be read or written, the tooling halts before starting an application task.

### DPB-005

- When the domainless foundation, images, and secrets are ready, a private release task establishes all required database prerequisites, creates/assigns the API runtime role, applies all current checked-in migrations exactly once per migration contract, and verifies runtime-role access.
- If the release task or schema verification fails, the receipt records a failed status and no API service, worker, or public listener is enabled.

### DPB-006

- When all domain-enable inputs are valid, apply creates or enables only an HTTPS listener using the supplied ACM certificate and admits traffic only from configured CIDRs.
- If any domain-enable input is missing or invalid, the operation leaves public HTTPS disabled.

### DPB-007

- After each completed or failed operation, the operator can inspect an ignored receipt containing the non-secret deployment identity and rerun the emitted retry command.

## Constraints and Assumptions

- The target is the existing real-AWS `pals-infra/terraform/production` root in `ap-northeast-1`, with `environment = "prod"` and no staging environment.
- AWS account credentials, Docker/Buildx, Terraform, AWS CLI v2, Git, and an OpenAI API key remain operator-supplied local dependencies.
- The existing AWS account is permitted to create the resources named by the production root and has no pre-existing state bucket requirement.
- A domainless foundation is an operational bootstrap, not a user-facing production release. It may incur AWS charges.
- Release reconciler/verifier infrastructure remains disabled; it has separate runtime-attestation prerequisites.

## Open Questions

None for the safe domainless bootstrap slice. Frontend hosting and public learner traffic are deferred until a domain is supplied.
