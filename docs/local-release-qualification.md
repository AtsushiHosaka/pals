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
explicit prerequisites are the dedicated owned PostgreSQL service, private `local.env`,
existing LocalStack/Cognito services, unexpired private provider TLS files (see
[Local provider TLS material](#local-provider-tls-material)), and the cumulative known
budget ledger. It builds the versioned guard, converges LocalStack and Cognito to the given
compose root, then rotates local verifier mTLS and applies the actual local database
migrations, starts one stable stack, freezes actual configuration into a new subject, and
executes the actual HTTP compiler canary. It never submits a mathematical proof.
It preserves prior captures, database rows and spending; missing/uncertain inputs fail closed.

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
is task-scoped; cold provisioning and a different owner require an explicit setup contract.
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
production verifier source and unmodified Dockerfile. `verifier_variant` contains
`production_image_digest`, `source_archive`, `local_build_provenance`, `dockerfile_sha256`,
`lean_version` and `lake_manifest_sha256`. It preserves the pinned Lean/Mathlib library and
full compiler sandbox. Native architecture and observed resolver dependency versions differ
from the production image; this is not byte equivalence. The receipt records actual versions.

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
The complete local privilege repair plan needs separate approval. These failed captures
imply neither a production permission change nor successful mathematical acceptance.

Real captures, private sessions, certificates, environment files, generated receipts, images
and compiler diagnostics remain outside Git. Preserve failed runs and their budget ledger.
Clean up only task-owned resources after the approved verification work completes.
