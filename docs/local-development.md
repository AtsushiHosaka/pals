# Local Development

The component-development workflow starts only PostgreSQL with pgvector.
The full-stack QA workflow is explicit and separate.

## Complete PALS Stack

For browser QA or an end-to-end local session, start every required service with:

```bash
make agent-deps
make local-cognito-bootstrap
make pals-up
```

This is the canonical full-stack entry point. It rebuilds the checked-out API,
web, worker, and verifier sources and starts the layered E2E Compose project.
The Cognito bootstrap creates or reuses the loopback-only User Pool and App
Client, provisions the reviewer account configured in `.env.local`, and verifies
that password authentication succeeds before the web image is built.
Run `make pals-qa` to start the same stack and execute the public-API QA fixture.

## Database

```bash
cp .env.example .env.local
make dev-up
```

This starts one container:

- `postgres`: PostgreSQL 16 with pgvector on `127.0.0.1:55432`

Stop it when it is not needed:

```bash
make dev-down
```

The named `postgres-data` volume is preserved by both commands.

## Application Components

Run only the component currently being developed, using its repository-native
tooling:

```bash
make api-test
make web-test
make draft-admin-test
make agent-test
make agent-lean-deps
```

API, web, Draft Admin, Agent, Lean, and Ollama do not belong to the default
Compose project. A component-specific container may still be built manually for
deployment validation, but local development must not build it implicitly.

## Local LLM

Ollama runs on the host. Keep API keys and environment-specific values in
`.env.local`; never commit them.

### Explanation retry schema

`make pals-up` builds the API image, waits for the existing local database, and runs
`app.release.explanation_retry_migration` once before bringing up application services.
The command is idempotent, creates no listening application replica, and stops startup
if migration fails. It expects the existing base proof/explanation schema to be installed.

For a production release, run the following in the release process, where
`PALS_DATABASE_URL` is supplied from the existing schema-owner/migration credential
secret (not the restricted `pals_api_runtime` serving credential):

```sh
python -m app.release.explanation_retry_migration
```

The release login must own the migration objects or have the schema-owner privileges
needed to create tables, functions, triggers, and grant the listed serving privileges.
Expected output is `installed` or `already_current`. Then start the new API version
using its existing restricted serving credential. Startup only checks the catalog and
privileges; it never applies this migration. Do not print or copy database credentials
into commands, logs, or documentation. This addition does not change production
infrastructure deployment or the original proof-job dispatch recovery policy.

### Billing and OAuth release inputs

Billing admission requires `Idempotency-Key` on proof creation (32–128 URL-safe ASCII
characters). Preserve the key when retrying an uncertain send; use a new key after a
confirmed successful request. Existing proof/chat reads remain available when the
allowance is exhausted.

The production secret provisioner requires `--billing-config-file PATH`, a mode-0600
JSON file with the exact billing runtime schema. It no longer manufactures a disabled
placeholder. Supply real Stripe credentials outside the repository and keep
`live_checkout_enabled` false until the BILL-009 operator launch inputs are complete.
Production uses SSM SecureString and existing host TLS egress, without adding NAT.

For Google, first configure `cognito_hosted_ui_domain_prefix` and explicit
`google_idp_operator_principal_arns` with `google_sign_in_enabled=false`. Populate the
Google OAuth SSM SecureString outside Terraform, run and verify the dedicated IdP
provisioner, then enable `google_sign_in_enabled`. The web image build reads the public
Hosted UI domain and enabled flag from Terraform outputs. Google's redirect is the
Cognito domain's `/oauth2/idpresponse`; the app callback is
`https://app.palschat.site/auth/callback` and logout is `https://app.palschat.site`.

The existing daily production backup runs billing retention before the dump, using the
release connection and a dedicated maintenance function. The serving API receives no
delete/maintenance privileges and no idle polling is added. After 13 calendar months,
idempotency request/response details are removed atomically after retaining only the
account and submission-key hashes. These hashes reject reuse of expired keys without
retaining the original account identifier or proof details. Unresolved Stripe operations
remain outside this purge.

### Worker replacement and typed catalog evaluation

The worker drains its current queue receipt on SIGTERM before accepting more work.
Keep the API, reviewer, reconciler and verifier available during this drain. Local
Compose and the production host allow 65 minutes for draining. The one-hour claim
lease is renewed across repairs and is not a bound on the entire request. A forced
kill can still delay recovery until the current lease expires.
The local runner stops the worker before applying migrations or replacing dependencies.

The local configuration helper retains existing Recipe credentials and creates a distinct
`PALS_TYPED_CATALOG_RELEASE_SECRET` when upgrading an older configuration. The release
secret belongs only to the API and the release evaluator, never the ordinary worker.
The local schema-release step installs the same immutable typed catalog schema. See
[typed-catalog-runtime.md](typed-catalog-runtime.md) for independent review, inactive
admission, real evaluation, activation and rollback. Installation alone does not publish
Drafts or establish their mathematical quality.

### Local routing regression checks

Install the parent test dependencies from `tests/requirements.txt` into the test environment, then run `python -m pytest tests/test_local_reconciler_route.py tests/test_local_postgres_access.py tests/e2e/test_run_local.py`. These checks cover the dedicated API-to-reconciler network alias, the PostgreSQL access guard and startup ordering. The trigger URL must use `pals-reconciler`, whose alias is limited to the e2e network; the shared `reconciler` service name can resolve on the database network and fail the fixed API-peer check. This configuration check complements real notification/proof verification and does not replace it.
