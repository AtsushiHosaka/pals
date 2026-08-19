# Domainless Production Bootstrap Design

## Overview

The existing production Terraform root becomes a two-phase deployment: a private
foundation can be applied without a domain, while application services and an HTTPS
listener are enabled only after their immutable images, secrets, and domain inputs
exist. A checked-in operator script orchestrates the phases but never stores secret
values in Terraform inputs or receipts.

## Requirements Traceability

| Requirement | Design coverage |
|---|---|
| DPB-001 | Explicit script operations, account guard, state-backend bootstrap |
| DPB-002 | `foundation` deployment mode and absent public listener/service |
| DPB-003 | ECR-first immutable image build/push phase |
| DPB-004 | Secret shells and protected value injection outside Terraform |
| DPB-005 | One-shot private database release task and schema verification |
| DPB-006 | Explicit public HTTPS mode with supplied domain inputs |
| DPB-007 | Ignored, non-secret deployment receipt |

## Architecture

```text
operator
  | production-deploy bootstrap|plan|apply
  +-> AWS CLI: validate account; create/validate state bucket
  +-> Terraform foundation: VPC, Aurora, queues, ECR, Cognito, secret shells
  +-> Docker/Buildx: API + worker -> ECR immutable digests
  +-> AWS Secrets Manager: secret values (outside Terraform)
  +-> Terraform application: private task definitions and release task support
  +-> ECS run-task: database release + schema verification
  +-> Terraform public mode (only with real domain): HTTPS ALB + API service
  +-> local ignored receipt: non-secret deployment identity
```

### Terraform modes

The production root shall use a single remote state and an explicit closed deployment
mode:

| Mode | Created/enabled | Explicitly absent |
|---|---|---|
| `foundation` | VPC, Aurora, private endpoints, S3, SQS/DLQ, logs, Cognito user pool, ECR repositories, secret shells, ECS cluster, private security groups | Cognito browser client, ALB listener, API/worker task definitions or services, public ingress |
| `application` | Foundation plus a private one-shot database-release task definition | Cognito browser client, ALB listener, API/worker task definitions or services, public ingress |
| `public` | Application plus Cognito browser client, HTTPS ALB listener, one API service, and a SQS-driven worker service with minimum count zero | HTTP listener, synthesized DNS/certificate/callback values |

`foundation` is the default. All public-facing resources and all task definitions
that require the public API origin must be conditional on `public`, including the
ALB ingress rule, listener, API/worker task definitions and services, CORS
configuration, and worker's API base URL. The private database-release task is the
only application task definition permitted before public mode. The ALB DNS name is an
output for DNS configuration only, never a substitute for `api_domain_name`.

The existing application image inputs and secret ARNs are required only in
`application` and `public` modes. The Terraform configuration shall create named
Secrets Manager secret containers without secret versions; the script owns secret
values. Terraform must not read a secret value or define an `aws_secretsmanager_secret_version`.

### Deployment operations

`pals-infra/scripts/production-deploy.sh` is the sole operator entry point for this
slice.

| Operation | Mutates AWS | Sequence |
|---|---:|---|
| `bootstrap` | yes, explicit confirmation | validate caller/account/region; create or validate the dedicated S3 state bucket; configure encryption, versioning, ownership controls, and all public-access blocks; initialize the production backend |
| `plan` | no | validate binaries, account, protected input paths, local configuration, and run the requested Terraform plan; application validates clean infrastructure/API revisions and public additionally validates the worker revision |
| `apply foundation` | yes, explicit production confirmation | bootstrap if needed; apply foundation; record non-secret outputs |
| `apply application` | yes, explicit production confirmation | ensure foundation; build/push the API digest; write the required secret values; apply the private release task definition; run database release task; verify schema; record result |
| `apply public` | yes, explicit production confirmation | require exact domain/TLS/Cognito/CORS inputs; apply HTTPS listener/API service; wait for health; record result |

Each mutating operation requires both `--apply` and `--allow-production`. `plan` and
all rejected validation paths make no AWS write request. The script shall use a
non-interactive `--account-id` allowlist check and reject a caller whose AWS account
does not exactly match it.

### Inputs and local files

Non-secret inputs use a JSON configuration file supplied by `--config`; it is
validated as a closed object and intended to live under ignored
`.local/production-deploy/`. The required values are project, AWS account ID, region,
two AZs, environment `prod`, and deployment mode. Public mode additionally requires
the API domain, ACM certificate ARN, exact frontend origin, Cognito callback and
logout URLs, and ingress CIDRs.

The OpenAI key is supplied only as `--openai-key-file`, which must be a regular,
owner-readable-only local file. It is not accepted in JSON, a command argument value,
or environment variable. The script creates temporary secret files with `umask 077`
and deletes them via a trap. It reads the RDS master secret only into such a temporary
file, derives the application database URL, and uses `file://` AWS CLI input. The
script disables command echo before handling protected values and logs only ARNs.

The script creates four secret containers: `database-release-url`, `database-runtime-url`,
`worker-shared-secret`, and `openai-api-key`. It generates distinct random database-role
and worker-shared values. The private release task receives both database URLs; the public
API receives only `database-runtime-url`, and no normal service receives
`database-release-url`.

The script writes only non-secret, mode-appropriate Terraform variables to an ignored
generated tfvars file. It records a JSON receipt at
`.local/production-deploy/receipts/<timestamp>.json`; the receipt has a closed schema
with account ID, region, state bucket/key, operation, mode, source commits, image
digests, output ARNs/identifiers, result, and retry command. Receipt validation
rejects any key named like a secret, password, token, key value, or URL containing
userinfo.

### Image build and delivery

Foundation creates the ECR repositories first. The script then:

1. verifies the infrastructure, API, and agent source revisions are clean, unless
   `--allow-dirty-source <checkout>:<recorded-reason>` is supplied for each dirty
   checkout;
2. builds the API from the parent workspace context using `pals-api/Dockerfile`;
3. invokes the agent's supported proof-flow-index worker-image builder with the exact
   agent source commit and the ECR tag; and
4. resolves each pushed image to a lowercase SHA-256 digest and injects only
   `<repository>@sha256:<digest>` into generated tfvars.

The receipt records every checkout's `HEAD` commit and clean/dirty status. A dirty
override records the checkout and the following `pals.source-worktree.v1` digest, but
never the manifest content:

1. reject an unmerged index; obtain every index stage-0 entry with `git ls-files -s -z`
   and record its base64-encoded byte path, mode, object-format name, and blob object ID
   in ascending byte-path order;
2. obtain the byte-path union of those index paths, `git ls-files --others
   --exclude-standard -z`, and all paths deleted relative to `HEAD` in either index or
   worktree;
3. for each union path in ascending byte order, record the current worktree file type and
   executable mode from `lstat`, and SHA-256 of regular-file bytes or symlink-target
   bytes; record a literal `absent` type when it is missing;
4. canonicalize `{schema_version:"pals.source-worktree.v1",head_commit,index_entries,
   worktree_entries}` with RFC 8785 and SHA-256 those bytes.

This preserves staged content even when the working copy changed again, and it preserves
the separately deployed working-tree bytes. It includes staged, unstaged, deleted, and
non-ignored untracked files—the same source set checked by `git status --porcelain=v1
--untracked-files=all`. A read error, special file, invalid Git path, or source-set
mismatch rejects the override. The override does not cause Git changes, staging, or
commits. A tag alone is never supplied to Terraform.

### Database release task

The API repository shall provide a release-owned `production_database_release` entry
point. It receives `PALS_DATABASE_RELEASE_URL` only in the private release task and
`PALS_DATABASE_RUNTIME_URL` only to provision and verify the runtime principal. It
shall create the required baseline roles, schemas, extensions, and tables for an empty
Aurora database, grant the runtime principal only its runtime operations, then invoke
every current release migration through one checked-in ordered manifest. It must be
idempotent and finish with a closed schema/readiness probe using the runtime URL.

The normal API entrypoint receives only `PALS_DATABASE_URL` from the runtime secret.
It shall run a manifest-status/readiness check that performs no DDL or role change
before Uvicorn starts. A missing or unapplied migration makes startup fail; startup
must not use the release URL or attempt to repair the database.

In `application` mode, Terraform creates a private Fargate task definition for this
entry point with the API image, a release-only task role/security group, both database
secret ARNs, and no listener or load balancer attachment. The script runs the task once with `aws ecs
run-task`, waits for `STOPPED`, retrieves its non-secret exit reason and CloudWatch log
pointer, then calls its schema/readiness probe. It does not start an API service or
worker in this mode.

### Public enablement

Public mode is rejected unless the supplied `api_domain_name` is covered by the
issued, same-region ACM certificate and all browser URLs are HTTPS exact origins.
Terraform then creates the 443 TLS 1.3 ALB listener and its ingress rule from supplied
CIDRs, configures CORS/Cognito input values, and creates the API ECS service at one
task. The script waits for ALB target health and reports the supplied HTTPS origin.
It neither creates Route 53 records nor hosts a frontend in this slice; the operator
  must point DNS and deploy a production frontend separately.

## Validation and Error Handling

- Missing binaries, invalid AWS identity/region/AZ, dirty infrastructure/API/worker
  sources without per-checkout override,
  invalid config, unsafe secret file permissions, missing state protections, and
  missing prerequisites are preflight errors with no mutation.
- A failed AWS/Terraform/image/release action stops subsequent phases. The receipt
  marks `failed`, includes only non-secret identifiers and the safe retry command,
  and preserves the remote state for diagnosis.
- No automatic destroy, rollback, scale-up, public listener creation, or reuse of a
  generated ALB name is allowed after failure.
- Production-only mutations always require fresh `--apply --allow-production`; the
  script never infers confirmation from a configuration file.

## Testing Strategy

- Shell unit tests cover argument parsing, closed config validation, account guard,
  source-clean gate, secret redaction, receipt schema, and exact command construction
  with mocked executables only at the shell boundary.
- `terraform fmt -check`, `terraform validate`, and `terraform test` cover all three
  modes and assert the absence of public listener/ingress/API or worker task definition
  or service in foundation and application plans, except for the private release task.
- API tests cover an empty PostgreSQL database release, manifest ordering,
  idempotency, and failure before API startup when a migration is absent.
- A real AWS smoke run is required before public enablement: foundation followed by
  application must complete in the selected account and leave no listener/service;
  public mode must be separately verified only after a domain and ACM certificate exist.

## Risks

- Aurora and VPC endpoints incur cost even in foundation mode: document cost and make
  `apply foundation` explicit.
- The worker build needs generated proof-flow-index artifacts: use the existing
  supported builder rather than inventing a Docker invocation.
- The current API container lists migrations individually: replace it with the
  manifest-backed release entry point so deploys cannot silently omit a migration.
- The production database has no direct operator ingress: use the scoped private ECS
  release task, not a public database path or fixture-only bootstrap.
