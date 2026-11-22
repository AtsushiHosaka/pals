# Local release qualification

This path is an explicitly local qualification basis. It uses the real PostgreSQL database,
real model provider, real Lean compiler and product guest UI. LocalStack queue/blob/secrets,
guest sessions, a temporary budget TLS proxy and the local database bootstrap role do not
prove production AWS, account authentication, billing, ingress or runtime isolation parity.

`pals-scripts/local-qualification.py` accepts a frozen
`pals.local-qualification-subject.v1` subject and a private mode-0700 state directory. It
verifies actual runtime image/source/platform/configuration, real build provenance and a fresh
compiler canary through the configured mTLS HTTP verifier before launching a browser. The
fixed True theorem is dependency readiness only; it cannot qualify the mathematical journey.
The runner also reads actual definer functions, owners, migration revisions and row-lock
permissions before any paid browser action. The subject pins the schema/ACL fingerprint and
the capture rechecks it after completion. This is local dependency readiness, not production
database admission.

The browser submits one approved guest request through `/try`. A durable exclusive marker is
written before clicking. A timeout or ambiguous result cannot trigger a second submission.
Acceptance requires a fresh terminal Lean-verified answer, persisted complete explanation
including conclusion, matching verified source, visible rendered content and browser reload,
an independent database read, unchanged runtime, and known actual all-lane provider usage.

```sh
python3 pals-scripts/local-qualification.py \
  --subject /private/path/subject.json \
  --state-dir /private/path/capture \
  --web-root /path/to/installed-web-dependencies \
  --database-env /private/path/local.env
```

The runner and the preparation driver stop before touching any dependency when their
interpreter lacks the database driver (`release_python_missing_module:psycopg`); see
[Interpreter](#interpreter). A fresh capture also performs a real TLS handshake with the
running local budget proxy, trusting only the task CA, before the compiler canary and the
browser. `local_provider_tls_expired`, `local_provider_tls_expires_before_capture_window`
(less than 1200 s left), `local_provider_tls_unavailable_or_untrusted` and
`local_provider_tls_differs_from_subject` refuse before the single paid submission can be
spent on a dead provider transport. The handshake sends no HTTP request and closes the
TLS session cleanly, so the guard logs nothing for it.

Use `--verify-existing` with the same arguments to re-read an unexpired successful capture.
It reuses only the runner's own private Playwright guest session, observes the same real
request and reloads its UI, repeats the actual compiler canary and database checks, and
rejects proof mutations before network dispatch. It cannot turn a failed request into success.
Changing a source, image, runtime, configuration or frozen runner invalidates prior acceptance.

The latest record is `running`, `failed` or `accepted`. A failed or unfinished latest record
blocks promotion. Deterministic CI tests do not create live acceptance. The canonical release
controller must invoke the runner, freeze its code and inputs, and require exit zero; this
script alone does not enforce branch protection or every possible deployment entrypoint.

## Prepare the reused local stack

`local-qualification-prepare.py` upgrades the existing owned E2E stack in one command. Its
explicit prerequisites are the dedicated owned PostgreSQL service (empty or initialised), private `local.env`,
existing LocalStack/Cognito services, unexpired private provider TLS files (see
[Local provider TLS material](#local-provider-tls-material)), and the cumulative known
budget ledger. It builds the versioned guard, converges LocalStack and Cognito to the given
compose root, then rotates local verifier mTLS and applies the actual local database
migrations, starts one stable stack, freezes actual configuration into a new subject, and
executes the actual HTTP compiler canary. It never submits a mathematical proof.
It preserves prior captures, database rows and spending; missing/uncertain inputs fail closed.

The driver requires the dedicated PostgreSQL container but never creates it; see
[Dedicated PostgreSQL container](#dedicated-postgresql-container). An empty server is
initialised in one run. While the workers and the guard are stopped it also refuses
unfinished proof work of an earlier capture; see
[Leftover proof work](#leftover-proof-work-of-a-failed-capture). A blocked budget ledger is
refused as before; the only way past it is the separate
[owner-approved rollover](#budget-ledger-rollover-owner-approval-only).

The subject digest is part of the API environment, so writing the subject recreates the
API container. The first preparation of a rebuilt stack used to refuse
`frozen_runtime_configuration_changed_api` and an unchanged second run passed: the host
configuration of the recreated API differed from the one frozen before that recreate
(image and environment were equal). Which key differed was not recorded, so the cause is
not established. The driver now freezes the API that actually serves: after the recreate it
compares again and, if the API changed, repeats the freeze (at most three rounds, then
`frozen_runtime_configuration_did_not_converge_api`). Every extra round is recorded in the
subject under `preparation.api_freeze_rounds` with the names (never the values) of the
changed host-configuration keys, so the next occurrence names its cause. The capture-time
check against the subject is unchanged.

Order matters. LocalStack keeps secrets in memory, and a different `--compose-root` changes
its bind-mount sources, so `docker compose up` recreates it. The driver therefore brings
`localstack` and `cognito-local` up and healthy first and writes the verifier mTLS secret,
recipe configuration and schema only afterwards; the first preparation after a compose-root
change succeeds in one run. If a dependency is nevertheless replaced after that bootstrap,
the driver refuses with `local_dependency_recreated_after_verifier_tls_bootstrap` instead of
leaving a verifier that cannot load its TLS material. That identity check runs immediately
after the application `up`, before the 120 s readiness wait, and once more after it.

Two locations must outlive the stack:

- The runtime directory holds the cumulative budget ledger, the provider TLS material and
  the private environment files, and the guard binds from it. Keep it in a persistent
  mode-0700 location. Do not place it under a path that is cleared on reboot or by
  periodic cleanup (`/tmp`, `/private/tmp`, `$TMPDIR`): losing the ledger blocks every
  further run, because spending is never reset.
- The `--compose-root` directory is the bind-mount source of LocalStack and Cognito
  (`pals-infra/localstack/init/ready.d`, `pals-infra/cognito-local/*`). Keep that checkout
  in place and unchanged for as long as the stack runs; removing it breaks the next start
  of those containers, and preparing from another root recreates them.

Relocating the runtime directory, in this order:

1. Confirm that nothing can spend: no capture or other request is running, no request or
   proof job is in a non-terminal state, and all four queues are empty. The guard keeps
   recording into the OLD ledger until preparation stops it, so a provider call made after
   step 2 would exist only there.
2. Copy the whole directory with modes preserved (`cp -Rp`) to a persistent mode-0700
   place. Leave the old directory untouched.
3. Run preparation once with `--runtime-dir` at the new place.

Step 1 is not left to care alone. Preparation reads from the existing guard container
which host directory it has been recording in, stops the task containers and the guard,
and only then compares that serving ledger with the one in `--runtime-dir`: `calls`,
`actual_microusd`, `reserved_microusd` and `blocked` must be identical. A copy that misses
a later call is refused with `relocated_budget_ledger_differs_from_the_serving_ledger`
before it is adopted (no resume binding is written), so spending cannot be under-counted;
`relocated_budget_serving_ledger_required` means the old ledger is gone or unreadable and
the copy cannot be proven current. After such a refusal the producers are stopped: copy
`budget/ledger.json` again from the old directory (it can no longer change) and rerun.

`--runtime-dir` accepts any existing mode-0700 directory with a plain absolute path; every
bind mount, `override.yml`, the subject and the environment files are derived from it on
that run, and the ledger continues with the same calls and spending because resumption is
bound to its bytes, not its path. The subject path, the `local.env` path and both their
hashes change, so relocate before the release plan freezes them. Keep the old directory
until the new stack is prepared.

```sh
python3 pals-scripts/local-qualification-prepare.py \
  --runtime-dir /private/path/owned-runtime \
  --compose-root /path/to/pinned-initialized-parent \
  --api-source /path/to/exact-clean-api-source \
  --base-subject /private/path/base-subject.json \
  --web-build-receipt /private/path/web/provenance.json \
  --verifier-build-receipt /private/path/verifier/provenance.json \
  --api-python /path/to/api/.venv/bin/python \
  --agent-python /path/to/agent/.venv/bin/python
```

Before it stops any container the driver checks, in this order, its own interpreter, the
`--api-python` (`psycopg`) and `--agent-python` (`boto3`, `cryptography`) interpreters
(`api_python_missing_module:<name>`, `agent_python_missing_module:<name>`,
`<role>_unavailable`), stack ownership, and the provider TLS material. A refusal prints
`{"state":"refused","code":...}` on stdout and exits non-zero.

### Interpreter

`RELEASE_PYTHON` (Makefile, default `python3`) selects the interpreter of
`make release-local-qualify`; start `local-qualification-prepare.py` with the same one. It
must provide `psycopg`. The API interpreter must satisfy the candidate API source, whose
dependencies change between releases. Build one private virtual environment from the
candidate's own lock, outside every checkout, and use it for all three roles:

```sh
uv export --frozen --no-dev --no-emit-project --project /path/to/exact-clean-api-source \
  -o /private/path/api-requirements.txt
uv venv --python 3.12 /private/path/api-venv
uv pip install --python /private/path/api-venv/bin/python --require-hashes \
  -r /private/path/api-requirements.txt
make release-local-qualify RELEASE_PYTHON=/private/path/api-venv/bin/python ...
```

Set `PYTHONDONTWRITEBYTECODE=1` so that neither driver writes into the clean source checkout.

### Failed child commands

Every refused child command keeps the closed code `local_dependency_command_failed`. Its
cause is no longer discarded: the last 16 KiB of the child's stderr are written, redacted,
to a mode-0600 file under `diagnostics/` (mode 0700) in the runtime directory (preparation)
or the capture state directory (runner). The refusal and `latest.json` carry
`diagnostic.failed_command` (program and script or subcommand name only, never arguments or
environment) and `diagnostic.diagnostic_file`. The whole text is redacted first and only then cut to
its tail, and the tail always starts at a line start, so a value cut by the size limit
cannot leave a readable remainder. Replaced are: values read from the private environment
files (any value of eight or more characters, shorter ones under a secret-looking name,
and the credentials inside their URIs), secret-named process environment values, the whole
user-info part of any URI, bearer and basic tokens, key blocks and stray encoded lines,
account numbers, and the value of every `password`/`secret`/`token`/`key`-like pair in
`key=value`, `key: value`, JSON and Python-repr form. Redaction is deliberately
conservative and may hide harmless text. Treat the file as private anyway and keep it
outside Git.

The versioned local SQL bootstrap uses real sealed catalog data and migration modules. It
does not install production admission or insert a completed answer. The owned local profile
is task-scoped; a different owner requires an explicit setup contract.

### Dedicated PostgreSQL container

Preparation refuses without a container named `pals-reliability-test-postgres` that carries
the owner label (`dedicated_owned_postgres_required`). It is external to the compose
project, so `docker compose down` and a rebuilt stack do not remove its data. Create it once:

```sh
# The network normally exists (the stack creates it). On a machine without the stack:
docker network inspect pals-reliability-local-database >/dev/null 2>&1 || \
  docker network create \
    --label com.docker.compose.project=pals-reliability-local \
    --label com.docker.compose.network=database \
    pals-reliability-local-database

docker run -d --name pals-reliability-test-postgres \
  --label codex.owner=01a1bb4b-dec2-76f0-a6fe-32405e465d6e \
  --network pals-reliability-local-database --network-alias postgres \
  -p 127.0.0.1:55432:5432 \
  -v pals-reliability-test-postgres-data:/var/lib/postgresql/data \
  --restart unless-stopped \
  --env-file /private/path/postgres-container.env \
  pgvector/pgvector:pg16
```

| Property | Value | Read by |
| --- | --- | --- |
| image | `pgvector/pgvector:pg16` (PostgreSQL 16 with `vector`) | bootstrap (`CREATE EXTENSION vector`), runner (major 16) |
| network and alias | `pals-reliability-local-database`, alias `postgres` | API, reconciler and LocalStack reach `postgres:5432` |
| port | `127.0.0.1:55432` only | every host tool; the closed local DSN admits no other host or port |
| label | `codex.owner=<owner>` | preparation, before it stops anything |
| volume | named volume `pals-reliability-test-postgres-data` | keeps the data when the container is replaced |

`postgres-container.env` is a private mode-0600 file outside Git with `POSTGRES_USER` and
`POSTGRES_PASSWORD`; they must equal the user and password of `PALS_HOST_DATABASE_URL` (and
`POSTGRES_USER`/`POSTGRES_PASSWORD`) in the runtime directory's `local.env`. No
`POSTGRES_DB` is needed. Then run the preparation command above; nothing else is applied
by hand. On an empty server `bootstrap_database.py`:

1. connects to the maintenance database `postgres` (the earlier default
   `pals_reliability_test` is only a fallback), creates `pals` and the NOLOGIN roles;
2. installs the sealed catalog, the legacy local release and the model/settings/guest/typed
   catalog storage as before;
3. reads the candidate's serving start (`app/infrastructure/bootstrap.py`) for every
   module-level import of a `preflight` and runs each read-only. It can install exactly
   one kind of migration: a release module with a module-level `apply(database_url)`,
   found as the preflight's own module or as the single `app/release/*_migration.py` that
   imports from it. With the current candidate the start imports seven preflights and
   only one of them has such a migrator, `app.release.explanation_retry_migration`; that
   is the only migration this step applies. The other six (`proof_requests`,
   `chat_shares`, `chat_experience`, `project_materials`, `project_materials_ocr`,
   `reply_language`) are installed in step 2 by the legacy local release, not here. No
   SQL is copied into this repository. The bootstrap result lists under
   `not_applicable_migrators` every preflight module this step could not install whatever
   its state, and under `serving_migrators` the state of each (`current`,
   `installed_by:<module>`, `failing_no_discoverable_migrator`,
   `not_checked_other_signature`). A future serving migration without a module-level
   `apply(database_url)` is therefore reported by name, NOT applied; the API then refuses
   to start and the migration must be added to the bootstrap deliberately. A migration
   after which the preflight still fails is `local_serving_migration_failed:<module>`;
4. grants `pals_api_schema_owner` column-level `UPDATE` on
   `proof_verification_candidates.candidate_id` and `proof_explanations.proof_job_id`,
   exactly the row locks `database_readiness.py` requires, and nothing else. A table-level
   `UPDATE` is refused (`local_rowlock_table_update_too_broad:<table>`), never granted and
   never revoked. This applies to the dedicated local database only (closed local DSN,
   `PALS_ENV=local`) and implies no production permission change.

Every step is idempotent; a second run reports the preflights `current` and repeats the
two grants without effect. The repository tests cover these steps with a faked database
and a miniature source tree only; no test in this repository runs them against a real
PostgreSQL server or starts the API.

### Leftover proof work of a failed capture

A capture that fails can leave its request and proof job non-terminal. The worker receives
the queued message again (LocalStack redelivers up to three times before the dead-letter
queue) and would call the provider as soon as a budget is open. Preparation therefore
reads the dedicated local database while the workers and the guard are stopped, before
anything is started: requests in `queued`, `assessing` or `verifying` and proof jobs
outside the candidate's own `TERMINAL_PROOF_JOB_STATES` refuse with
`leftover_non_terminal_local_jobs:requests=<n>,jobs=<m>`. An empty server or a database
without those tables has nothing left over.

To continue, either let the work finish or end it explicitly:

```sh
python3 pals-scripts/local-qualification-prepare.py ... --fail-leftover-local-jobs
```

That flag ends each such job with the candidate API's own `fail_unfinished_job` and each
such request with its own request-failure call (the pair the API uses for an overdue
request; token and quota holds are released, the outbox is closed), in one transaction,
and proves that nothing is left. The job is `failed` with `pals.request_deadline_exceeded`,
the request `failed` with `proof_request_deadline_exceeded`; a worker that still receives
the message acknowledges a failed job or finished request without a provider call. Rows are
kept, not deleted. The subject records counts, previous states and SHA-256 digests of the
identifiers under `preparation.leftover_local_jobs`. Local database only.

Not ended, with or without the flag: a job that is already `verified` whose explanation
is still `queued` or `generating` (with or without a request), and requests waiting in
`needs_input`. A worker that receives such a verified job again may call the provider to
write the explanation. The check does not refuse on them but counts them: the number is
in the helper's output, in the subject (`preparation.leftover_local_jobs`) and in the
preparation result as `verified_jobs_with_unfinished_explanation`. Look at it before a
budget is used; when it is not zero, decide what to do with those jobs first. A verified
job that has no explanation row at all is not counted.
Private database URIs require the PostgreSQL scheme, exact local host/port/database and no
query or fragment. Existing project roles and named containers must have the expected owner
before preparation stops anything.

## Build provenance

The Web variant permits only the eight fixed local public settings in `local-web-build.py`.
The versioned builder extracts an exact Git archive, checks the actual production publication
and configuration, builds without starting a service, and records the real BuildKit build
record, output image and complete source context. Verification re-reads the actual daemon
record and image, exact archive/Dockerfile, closed settings and frozen input files. Caller
labels, arbitrary 64-hex strings and self-reported PASS values are insufficient.

`web_variant` contains `production_publication`, `source_archive` and
`local_build_provenance` references, each exactly `{path, sha256}`, plus
`production_image_digest`, `dockerfile_sha256`, `source_archive_sha256` and
`local_build_args`. These files must also be frozen by the controller.

`docker buildx history inspect` prints the build `Context` relative to the caller's working
directory. Both builders therefore store and compare it as the resolved absolute build
context, so a receipt verifies from any working directory (`make` runs in the parent
checkout, a build may have run elsewhere). A legacy receipt with a relative `Context` is
accepted only when that value is a trailing part of the receipt's frozen absolute build
context; every other field of the real build record is still compared exactly. No "same
working directory" rule is needed any more.

`local-verifier-build.py` creates the explicit native ARM64 verifier variant from the exact
production verifier source and unmodified Dockerfile. It preserves the pinned Lean/Mathlib
library and full compiler sandbox. Native architecture and observed resolver dependency
versions differ from the production image; this is not byte equivalence. The receipt records
actual versions.

`verifier_variant` has exactly the key set the release plan accepts
(`pals-infra/scripts/release-cycle.py`, `local_verifier_variant`): `production_image_digest`,
`source_archive`, `recipe_archive`, `local_build_provenance`, `dockerfile_sha256`,
`lean_version` and `lake_manifest_sha256`. The two archives are git's own, as
`pals-infra/scripts/release_plan.py` (`VERIFIER_VARIANT_ARCHIVES`) re-derives them:

| Reference | Bytes | Why |
| --- | --- | --- |
| `source_archive` | `git archive --format=tar <verifier commit> pals_agent` | its hash is the signed manifest's `verifier_source.source_archive_sha256` |
| `recipe_archive` | `git archive --format=tar <verifier commit> docker/lean-verifier.Dockerfile lean-workspace` | the compiler recipe: Dockerfile, toolchain pin, manifest and workspace |

Neither archive can build the image: the Dockerfile also copies `pyproject.toml` and
`README.md`. The image is therefore still built from the complete `git archive` of the same
commit (`--source-archive`), which the receipt records as `build_archive`. The builder
writes both plan archives into its output directory (`source-archive.tar`,
`recipe-archive.tar`) and proves them before building, and `--verify-receipt` and the runner
repeat the proof: each archive must equal the bytes git produces at the recorded commit, and
every member (name, type, mode, size, time, link target, content) must equal the member of
the complete archive the image was built from, with no member missing or added below the
archived paths. A recipe archive of another commit with the same Dockerfile, toolchain and
manifest is refused (`native_plan_archive_differs_from_the_built_commit`,
`native_verifier_plan_archive_differs_from_the_built_commit`). The runner reads the
Dockerfile, toolchain pin and manifest from `recipe_archive`. The receipt
(`pals.local-verifier-build.v2`) stays hash-bound in the subject through
`local_build_provenance`, and through it the complete build archive. Receipts of the former
schema are refused; rebuild them. Freeze `source_archive`, `recipe_archive` and
`local_build_provenance` in the release plan.

## Cost and isolation

The local helper runs the network firewall and real provider forwarder. Exact app worker and
reviewer images run as UID 65532 without capabilities in its guarded namespace. Database,
metadata and direct external TLS bypasses are denied. Only those containers receive a
temporary local CA bundle; host/global trust is unchanged. The helper validates genuine
upstream provider TLS/SNI at a frozen public address and never caches or fabricates responses.

### Local provider TLS material

The guard terminates the task containers' provider connections on `127.0.0.1:443` and
forwards them to the real provider, whose genuine certificate it validates itself. The
runtime directory holds exactly three files in `provider-tls/` (mode 0700):

| File | Mode | Content | Read by |
| --- | --- | --- | --- |
| `server-key.pem` | 0600 | EC P-256 private key of the proxy leaf | guard only |
| `server.pem` | 0600 | leaf for the proxied provider host (SAN), server-auth only | guard only |
| `ca-bundle.pem` | 0644 | the one-off local CA certificate and nothing else | `SSL_CERT_FILE` of worker, assessment worker and recipe reviewer |

The CA is self-signed, path length 0, key usage certificate signing only, and name
constrained to the proxied host. Its private key exists only in a temporary directory during
issuance and is destroyed, so no further certificate can be issued under the trusted root.
Trust stays inside the three guarded containers: no host, system or global trust store is
read or changed. This material is LOCAL ONLY and proves nothing about production transport.

It is deliberately short lived (12 hours by default, 24 at most). Reissue it right before
preparation; the files never enter Git and nothing but public certificate facts is printed:

```sh
python3 pals-scripts/bootstrap-local-provider-tls.py \
  --directory /private/path/owned-runtime/provider-tls --issue
python3 pals-scripts/bootstrap-local-provider-tls.py \
  --directory /private/path/owned-runtime/provider-tls --check \
  --minimum-remaining-seconds 6300
```

`--issue` needs the `openssl` command (OpenSSL or LibreSSL). It proves the new generation
with a real handshake before replacing the previous files; a failed issuance changes nothing.
`--check` needs only the Python standard library. Each file is written to a new
exclusively created temporary file (a stale or linked leftover is removed, never followed)
and renamed into place. The three files are replaced one at a time, not as one atomic set:
a reader that catches a mixed generation fails closed, because key, leaf and CA no longer
complete a handshake (`invalid`). Issue while no preparation or capture is running.

Supported platform: macOS with OrbStack (or Docker Desktop), where bind mounts are served
with the host user's access. On a native Linux Docker daemon the guard runs as root with
`cap_drop: ALL`, has no `CAP_DAC_OVERRIDE`, and therefore cannot traverse a 0700 directory
or read a 0600 key owned by the host user; it would not become healthy. The modes are not
loosened to accommodate that. A Linux profile needs its own reviewed read path for the
guard and is not supported by this tool.

Preparation only checks and never issues. Reissuing replaces the CA the task containers
trust, so it remains one explicit operator step instead of a side effect of every
preparation. Before stopping any container it refuses with
`local_provider_tls_expired`, `local_provider_tls_expires_before_capture_window` (less than
6300 s left: the 3600 s capture freshness window, a 900 s margin and an 1800 s bound for
preparation itself, so marginal material is refused before the stack is rebuilt) or
`local_provider_tls_missing_or_invalid` (missing file, readable key, key/leaf mismatch,
leaf not signed by the bundled CA, wrong host). It records the leaf and bundle digests in
the subject, restarts the guard and task containers, which load the files at start, and
confirms by handshake that the running proxy serves exactly that leaf with at least 4500 s
left.

The first trial after this material had expired (2026-11-12) spent its single submission:
all three provider calls of the request failed in the TLS handshake with the 12-hour
certificate issued on 2026-11-08, the request ended `chat_provider_unavailable`, and no
provider call was forwarded or charged.

The forwarder counts actual provider input, reserves full configured maximum output and
enforces a **$0.70 aggregate conservative bound** across all local lanes. This reserves a
separate production test allowance inside the thread's $1 total. Unknown model/price/usage,
uncertain forwarded calls and exceeded reservations fail closed without retry. A restart
cannot reset spending. Explicit hash-bound resumption requires every prior call to have a
known completed cost and preserves the complete ledger while lowering its limit.

A forward whose cost stays unknown is marked `unknown` and blocks the ledger. Its row now
also carries `unknown_reason`, a closed code naming the condition and never provider or
request text: `upstream_status_<n>`, `timeout`, `body_too_large`, `unparseable_body`,
`unparseable_usage`, `model_mismatch`, `service_tier`, `usage_above_reservation`,
`upstream_tls_error`, `upstream_transport_error`, `upstream_protocol_error`,
`upstream_ip_not_public` or `internal_error`. Rows written before this change have none
and count as `not_recorded`.

### Budget ledger rollover (owner approval only)

A blocked ledger, or one with an `unknown` call, can never be resumed: the proxy refuses it
(`uncertain_budget_cannot_resume`) and preparation refuses it
(`known_existing_budget_required_no_reset`). That stays true. The one way forward is an
explicit rollover that the repository owner approves for exactly that ledger.

The approval record is an audit record, not access control. It is not signed or otherwise
authenticated: anyone who can write the runtime directory can write such a record, or
edit the ledger, the archive and the marker described below. The hashes make a rollover
deliberate, exact and visible to a reviewer; they do not prove who approved it. The
reviewer of a qualification compares the recorded approval text and hashes with what the
owner actually approved.

1. Stop the stack's producers and the guard (the guard holds the ledger in memory):
   `docker stop pals-reliability-local-worker-1 pals-reliability-local-assessment-worker-1
   pals-reliability-local-recipe-reviewer-1 pals-reliability-local-worker-network-guard-1`.
2. Take the hash of the ledger to close and write the approval record, a private file
   outside Git with exactly these keys:

   ```sh
   shasum -a 256 /private/path/owned-runtime/budget/ledger.json
   ```

   ```json
   {
     "schema_version": "pals.local-qualification-budget-rollover-approval.v1",
     "approved_by": "<owner>",
     "approved_at": "2026-11-13",
     "approval_text": "<the owner's approval, in the owner's words>",
     "closed_ledger_sha256": "<sha256 of the ledger being closed>",
     "new_limit_microusd": 300000
   }
   ```

   `new_limit_microusd` is the bound of the new ledger and may not exceed the fixed
   700,000. The closed ledger's spending is not subtracted automatically: the owner
   chooses the bound knowing the closed totals.
3. Roll over, passing the record by path and by hash:

   ```sh
   shasum -a 256 /private/path/rollover-approval.json
   python3 pals-scripts/local-qualification-budget-rollover.py \
     --runtime-dir /private/path/owned-runtime \
     --approval /private/path/rollover-approval.json \
     --approval-sha256 <sha256 of the approval record>
   ```
4. Run preparation as usual (with `--fail-leftover-local-jobs` if the failed capture left
   work behind).

The tool archives the closed ledger and the approval record byte-identically under
`budget/closed-<sha256 of the closed ledger>/` (mode 0400, never edited or overwritten) and
only then replaces `ledger.json` with a new ledger that has no calls, the approved bound
and a `rollover` header: `rolled_over_from_sha256`, `approval_sha256`, `rolled_over_at` and
`closed_totals` (calls, actual and reserved microUSD, the number of `unknown` calls and
their reasons, the closed limit and blocked flag, and the cumulative totals of every ledger
closed so far).

| Refusal | Meaning |
| --- | --- |
| `rollover_healthy_ledger_refused` | the ledger is resumable (not blocked, every call completed, or no call at all); rolling it over would be a silent reset |
| `rollover_call_in_flight_refused` | a call is still `reserved`; its outcome was never recorded and is not guessed |
| `rollover_approval_sha256_mismatch` | the record is not the one whose hash was given |
| `rollover_ledger_sha256_mismatch` | the record approves another ledger than the one on disk |
| `rollover_new_limit_invalid`, `rollover_approval_record_invalid` | bound above 700,000 or not a positive integer; missing, empty or additional field |
| `rollover_requires_stopped_guard`, `rollover_guard_state_unknown` | the guard runs, or Docker could not be asked |
| `rollover_approval_record_required`, `rollover_ledger_required`, `rollover_archive_differs` | missing or linked file; an existing archive with other bytes |
| `rollover_already_used` | the ledger opened from this closed ledger has recorded a call; neither this approval nor another one for the same closed ledger opens a second one |

Preparation and the proxy accept a ledger without calls only as the product of this tool,
and both repeat the proof against the archive: the header's two hashes must match the
archived bytes, the approval must name that ledger and that bound, the archived ledger
must have been blocked or uncertain, and the recorded totals must equal the recomputed
ones (`budget_rollover_not_proven:<reason>` from preparation,
`existing_budget_no_automatic_retry` or a `rollover_*` error from the proxy). A removed
archive, an edited closed ledger, a raised bound, a removed header, a hand-made empty
ledger and a missing ledger (`existing_budget_ledger_required_no_reset`) are all still
refused. The proxy enforces the approved bound instead of the fixed one and keeps the
header across restarts.

An approval is single-use. Before the proxy writes or forwards the first call of a
rolled-over ledger it creates `closed-<sha256>/started.json` exclusively (mode 0400,
synced). From then on a ledger without calls is refused for that archive by the proxy and
by preparation (`rollover_already_started_no_reset`), whatever it is restored from:
the ledger as the rollover wrote it, the `budget-before-prepare-<sha256>.json` copy
preparation keeps, or the closed ledger followed by the same rollover command
(`rollover_already_used`). Before the first call nothing has been spent, so restarting the
proxy or repeating the same rollover yields the same empty ledger and is allowed. A
further rollover needs a newly blocked ledger and a new approval record naming it. If the
proxy stops between creating the marker and writing that first call, the ledger stays
refused; no call was forwarded in that case.

The rollover is visible to every reviewer of the qualification: the subject carries it as
`guard.budget_rollover` with `guard.budget_limit_microusd` set to the approved bound, the
runner refuses when the serving ledger and the subject disagree
(`budget_rollover_differs_from_subject`), and the capture record `latest.json` carries
`budget_rollover` (`owner_approved_rollover` with both hashes, time, closed totals and new
bound, or `none_continuous_ledger`) next to the full ledger in `provider_budget_before`.

Not provided: a rollover without an approval record, of a healthy ledger, with a call
still `reserved` (for example after a killed guard), or of a lost ledger. Those need a
separate decision by the owner.
Paid Responses require confirmed default service tier; inputs above 272,000 tokens and
embedding batches are rejected before forwarding rather than priced with an unsafe estimate.

The first real local epsilon–N trial on 2026-11-09 failed and remains failed: the retained
AMD64 verifier on the local ARM machine could not establish Landlock (`ENOSYS`). HTTP error
classification presented that infrastructure failure as a compilation failure and the product
spent six repair attempts. This does not establish that the model could not prove the theorem,
or that production has the same kernel limitation. Its 19 actual provider calls cost a
conservative $0.141154; separate request and formal-job usage records reconcile exactly.

The second trial used the native sandbox and its mathematical Lean verification returned
HTTP 200. Final settlement failed because the local definer role lacked a privilege required
for its row lock; the capture timed out and remains failed. Both trials together used 27
provider calls and a conservative $0.171628. PostgreSQL requires UPDATE permission on a
column for these locking reads, including `FOR SHARE`. [PostgreSQL 16 SELECT privileges](https://www.postgresql.org/docs/16/sql-select.html).
The two column grants were first applied by hand; the local bootstrap now grants exactly
them (see [Dedicated PostgreSQL container](#dedicated-postgresql-container)). These failed
captures imply neither a production permission change nor successful mathematical acceptance.

The capture of 2026-11-13 failed and remains failed. One provider forward ended with an
unknown cost after 18.6 s; the proxy blocked the ledger and answered every later call with
HTTP 402, so the request never reached a terminal answer and its job stayed non-terminal.
The proxy recorded no reason, so the cause could not be established. The dedicated database
had been lost before that run, and an empty server could not be initialised by the tools.
The reason code, the rollover, the empty-server bootstrap and the leftover-work check above
are the response to that run.

Real captures, private sessions, certificates, environment files, generated receipts, images
and compiler diagnostics remain outside Git. Preserve failed runs and their budget ledger.
Clean up only task-owned resources after the approved verification work completes.
