# Local Development

The component-development workflow starts only PostgreSQL with pgvector.
The full-stack QA workflow is explicit and separate.

## Complete PALS Stack

For browser QA or an end-to-end local session, start every required service with:

```bash
make pals-up
```

This is the canonical full-stack entry point. It rebuilds the checked-out API,
web, worker, and verifier sources and starts the layered E2E Compose project.
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
