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
existing LocalStack/Cognito services, private provider TLS files, and the cumulative known
budget ledger. It rotates local verifier mTLS, applies the actual local database migrations,
builds the versioned guard, starts one stable stack, freezes actual configuration into a new
subject, and executes the actual HTTP compiler canary. It never submits a mathematical proof.
It preserves prior captures, database rows and spending; missing/uncertain inputs fail closed.

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

The versioned local SQL bootstrap uses real sealed catalog data and migration modules. It
does not install production admission or insert a completed answer. The owned local profile
is task-scoped; cold provisioning and a different owner require an explicit setup contract.

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

Real captures, private sessions, certificates, environment files, generated receipts, images
and compiler diagnostics remain outside Git. Preserve failed runs and their budget ledger.
Clean up only task-owned resources after the approved verification work completes.
