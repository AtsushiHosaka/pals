# Cost-Conscious Production Bootstrap Design

## Approved change

Change ID: `SPEC-CHG-2026-08-19-COST-HYBRID`

- Authority: explicit user approval on 2026-08-19.
- Baseline: parent `4c887ef385fbeedfe5c46ff753c0d7768bda31a3`, infra
  `258812554ee237e3c4a0bd84e1795a775cbcc336` plus recorded working changes.
- Old behavior: ECS/Fargate behind an ALB, NAT and Interface PrivateLink endpoints, always-on
  Aurora minimum 0.5 ACU, Secrets Manager containers, and externally hosted frontend.
- New behavior: one public ARM64 EC2 host running Caddy/web/API/worker/verifier/reconciler, private Aurora with
  0-ACU auto-pause, SSM Parameter Store secrets, Route 53 records, and S3 database backups.
- Retired IDs: DPB-002 -> DPB-008/009, DPB-004 -> DPB-010, DPB-006 -> DPB-011.
- Changed IDs: DPB-003 and DPB-005 retain their delivery/release outcomes but use the host.

Change ID: `SPEC-CHG-2026-08-28-EVENT-RECONCILIATION`

- Authority: explicit user approval on 2026-08-28 to remove unnecessary polling and keep the
  minimum-cost architecture.
- Baseline: the cost-hybrid working tree before this change.
- Changed IDs: DPB-009, DPB-012, and DPB-013.
- Old behavior: the reconciler queried PostgreSQL every second even with no candidate, keeping
  Aurora active and defeating the intended 0-ACU idle state.
- New behavior: durable candidate import sends one private in-host notification; the reconciler
  queries PostgreSQL only for notified candidate IDs. Existing proof-job SQS redelivery is the
  recovery trigger, so no additional AWS queue or scheduler is introduced.

## Architecture

```text
Internet
  |  app.palschat.site / api.palschat.site
Route 53 A records
  |
Elastic IP
  |
public subnet: one t4g.medium EC2
  Caddy :80/:443 -> web :3000 / api :8000 (private Docker network)
  API -> SQS; worker <- SQS; worker -> S3
  worker -> API durable candidate import -> private reconciler notification
  reconciler -> exact candidate DB lease -> mTLS verifier -> Lean
  API/reconciler -> Aurora :5432
  SSM agent <- operator Session Manager / Run Command
  first boot -> exact RDS master secret + KMS-verified release bootstrap
  timer -> pg_dump -> encrypted S3 backup prefix
  |
private DB subnets in two AZs
  Aurora Serverless v2 PostgreSQL, 0..2 ACU, auto-pause
```

There is no ALB, ECS/Fargate service, NAT Gateway, Interface/Gateway VPC endpoint, RDS
Proxy, or SSH listener. Public outbound traffic from the host uses its Internet Gateway.
Aurora has no public address or route and accepts PostgreSQL only from the host security
group.

## Terraform phases

The state retains two closed phases because ECR must exist before immutable images can be
built.

| Mode | Creates | Must be absent |
|---|---|---|
| `foundation` | VPC/subnets/IGW, Aurora, S3, SQS/DLQ, Cognito pool and public web client, API/web/worker/verifier ECR, KMS release key, EC2 IAM/profile, log group | EC2/EIP and public DNS records |
| `public` | Foundation plus EC2/EIP, exact Route 53 records and host bootstrap using four image digests | ALB, ECS, NAT, endpoints, SSH |

The Cognito public client is created in foundation with the exact approved callback/logout URLs so
its ID is available when the immutable web image is built; it has no client secret and does not
publish a network endpoint. Public mode requires `route53_zone_id`, `frontend_domain_name`,
`api_domain_name`, exact HTTPS callback/logout/origin values, and API/web/worker/verifier ARM64 image digests. Terraform
creates names and policies only for the secret parameter path. The operator creates external
application `SecureString` values before host deployment; after signed-release admission the host
creates only the five named database-login URL parameters.

## Host runtime

Amazon Linux 2023 ARM64 is resolved from the AWS public SSM AMI parameter. Cloud-init
installs Docker, writes root-owned deployment and backup helpers, enables SSM, and starts
a systemd unit. The unit:

1. pulls the four exact digest images and the pinned Caddy image;
2. fetches required SecureString parameters with decryption to a mode-0600 runtime env;
3. runs the database release image once with separate release/runtime/reconciler/Recipe-selector/
   PFI-reader database values;
4. creates one release-bound host-local CA plus separated server/client mounts, starts the
   rootless read-only Lean verifier and API-owned event-driven reconciler, and requires both
   readiness gates;
5. starts API, worker and web only after release and verifier readiness success;
6. starts Caddy last, with web/API containers reachable only on the private Docker network;
7. removes temporary AWS response files and keeps the root-only runtime env for restart.

No secret is placed in user data, instance tags, Terraform inputs, SSM command arguments,
or Docker image metadata. The instance profile provides AWS SDK credentials through IMDSv2.
Containers receive only their required environment subset.

## Aurora pause behavior

Aurora uses one `db.serverless` writer, encrypted storage, RDS-managed master password,
  `min_capacity = 0`, `max_capacity = 2`, and a default 600-second auto-pause. Because an
open connection blocks pause, application repositories continue to open bounded per-
operation psycopg connections and close them at operation completion. The reconciler waits on an
in-process candidate-ID queue and makes no repository call while that queue is empty. No RDS Proxy,
resident connection pool, periodic candidate scan, additional SQS queue, Lambda, or scheduler is
introduced.

The proof-dispatch outbox is also recovered once at API startup, not by the former five-second
database loop. New proof creation still performs its SQS send and confirmation in the foreground;
an unconfirmed send fails closed and remains durable for the next startup recovery. This preserves
the minimum infrastructure graph and allows a truly idle deployment to reach Aurora auto-pause.

Candidate import and notification are deliberately ordered. The API first commits the idempotent
candidate record, then posts the canonical UUID to the reconciler on the fixed private Docker
network. A refused/full/unreachable notification produces HTTP 503, leaving the worker's existing
proof-job SQS receipt unacknowledged. A notification accepted before a reconciler crash may be lost
from memory, but the same unacknowledged SQS delivery later replays the idempotent import and sends
the trigger again. The database remains the state authority; the notification carries no proof
bytes or verifier verdict.

An initial connection after pause can take tens of seconds. API startup retries only the
DDL-free release readiness command for at most 90 seconds and fails closed afterward.

## TLS and DNS

Caddy terminates TLS and automatically obtains certificates for the two exact Route 53
names after registrar delegation reaches Route 53. HTTP is open only for ACME and redirect;
HTTPS is the application entry point. The pending ACM certificate is deliberately not
referenced because ACM certificates cannot be attached directly to EC2.

## Backups and recovery

Aurora automated backups remain enabled. In addition, a systemd timer runs `pg_dump` using
the release database URL, gzip-compresses it in a mode-0700 temporary directory, uploads it
with S3 server-side encryption to `database-backups/YYYY/MM/DD/`, and deletes local bytes
only after upload succeeds. S3 lifecycle expires backup objects after the configured
retention. Failed uploads remain local for diagnosis and never remove the newest successful
remote object.

## Testing and rollout

1. Terraform native tests assert resource absence, network boundaries, Aurora pause,
   instance profile scope, DNS and backup lifecycle.
2. `terraform fmt`, `validate`, and `test` run locally.
3. API startup retry tests exercise transient and terminal readiness outcomes.
4. Web/API/worker/verifier production images build for ARM64.
5. A real backend plan is reviewed for add/change/destroy counts and cost-bearing resources.
6. Only a separately confirmed apply may provision the foundation/public host.

## Cross-repository production contract

Terraform, the immutable web image, the API environment and the worker environment are one release
contract. The Cognito client explicitly enables the frontend's `USER_PASSWORD_AUTH` flow. Host
bootstrap passes the artifact bucket plus the release-admitted Recipe toolchain identity and
dedicated Recipe/PFI login URLs to the API, and passes the matching Recipe worker secret and
verifier/toolchain identity to the worker. The worker uses 20-second SQS long polling; this is the
only required idle polling path and does not touch Aurora.

The guarded deploy receipt is derived from the signed public tfvars and saved plan. It records all
five source commits, four OCI digests, the saved-plan SHA-256 and action counts. It rejects secret
fields and never copies database URLs, API keys, signatures, or manifest payloads into the receipt.

## Cost notifications

The foundation creates one monthly USD 100 AWS cost budget with absolute actual-cost email
notifications when spend is greater than USD 20, 50 and 100. All three directly notify
`hosaka2917+pals@gmail.com`. No SNS topic or
subscription is introduced.

The existing unapplied 78-resource ECS plan is invalidated and shall never be applied.

## First-database release

Foundation mode creates an asymmetric P-256 KMS release key and exposes only its ARN. After the
four ARM64 images have immutable ECR digests, the guarded deployment command builds a canonical,
short-lived bootstrap manifest binding those digests, source revisions, the Aurora resource ID,
the production account/region, and the checked-in database artifact digests. The operator identity
signs only that digest with KMS. The public host receives the non-secret manifest and signature,
but its role has only `kms:GetPublicKey` and `kms:Verify`, never `kms:Sign`.

On first boot the host reads the exact RDS-managed master secret, generates independent URL-safe
release/runtime/reconciler passwords, and runs the API image's initial-database release command. The command
validates the closed manifest and KMS signature before connecting to PostgreSQL, creates exact
roles and `vector`, creates only the empty legacy base relations required by the canonical PJR/PEX
migrations, persists the release trust/admission tuple, runs PJR then PEX then ordinary migrations,
and installs checked runtime grants. It writes the three role URLs to the exact SSM
SecureString names only after readiness succeeds and never gives the master URL to a serving
container. Exact replay is idempotent; any partial/mixed catalog or changed signed identity fails
closed.
