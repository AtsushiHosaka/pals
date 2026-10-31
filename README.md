# PALS

PALS is the private parent repository for the Proof Assistant Learning System.

This repository coordinates the implementation repositories, local development
workflow, documentation, and Codex helper scripts. Implementation repositories
are managed separately and will be linked from this repository after their
GitHub remotes are created.

## AWS migration

As of 2026-10-31 20:32 JST, both `palschat.site` and `api.palschat.site` serve
the private AWS runtime through Cloudflare and the TLS ALB. Public browser
verification confirmed a mathematical answer and its Lean source. Aurora holds
433 seeded Drafts and 102 compiler-verified Recipes. Of those Recipes, 20 have
independently approved searchable entries; the new 82 are not yet searchable.
Another 744 typed Draft candidates passed local Lean and axiom replay, but none
is active in production. The 1,100 usable-item target is not yet achieved.
Chat history was not imported, as requested.

Aurora now rejects the tested non-TLS connection path and accepts TLS 1.3.
The writer still reports `pending-reboot`; no reboot was performed. Private
networking, encryption, access controls and budget notifications were inspected.
The application source-security scan could not start, so this is not an
application-wide security approval.

The natural-power continuity question reused a verified Recipe and reached
`answered` in 25.003 seconds of server time, versus 154.333 seconds in the earlier
generation trial. These are two individual observations, not a controlled
performance benchmark. One-second answers, the 30-person latency target, and
automatic scaling remain unachieved or unverified. Recovery units are enabled,
but an actual reboot test has not been performed. See the runbook for the
current release window and the shared-network guest quota.

![PALS AWS private network target](docs/diagrams/pals-aws-private-target.png)

- [Migration runbook and execution status](docs/aws-migration-runbook-2026-10-30.md)
- [AWS security checks and catalog expansion evidence](docs/aws-security-and-catalog-check-2026-10-31.md)
- [Editable draw.io diagram](docs/diagrams/pals-aws-private-target.drawio)
- [Capacity and performance design](docs/aws-low-latency-architecture-2026-10-30.md)
- [Native Lean measurements on the private large instance](docs/aws-native-lean-benchmark-2026-10-30.md)
- [Verified Recipe reuse latency and the next optimization design](docs/aws-recipe-reuse-latency-2026-10-31.md)
- [Restore, Aurora rehearsal, and image preparation evidence](docs/aws-migration-verification-2026-10-31.md)

## Repository Layout

- `pals-api` - private FastAPI backend
- `pals-webfront` - private frontend application
- `pals-infra` - private Terraform infrastructure
- `pals-datasets` - private ingestion and dataset tooling
- `pals-observability` - private observability and tracing operations
- `pals-agent` - public OSS LangGraph agent with Lean verifier tooling
- `pals-draft-admin` - private, read-only Draft catalog operations UI

Lean verification source and tooling live in `pals-agent`.

## Secret Policy

Do not commit API keys, database URLs, AWS credentials, Langfuse secrets, or
production configuration. Use local `.env.local`, `.env.dev`, and `.env.prod`
files only.

## Environment Policy

- `.local` is for laptop/offline development and cheap LLM experiments. Prefer
  Ollama with local Qwen models here.
- `.dev` is for shared AWS development resources.
- `.prod` is for production and must require explicit confirmation in scripts.

Local LLM fine tuning assumes Apple Silicon, not NVIDIA/CUDA. Use MLX/MLX-LM
for local LoRA experiments; see `docs/apple-silicon-local-llm.md`.

## Local Development

To start the complete browser-testable PALS stack (web, API, worker, verifier,
reconciler, Cognito Local, LocalStack, and PostgreSQL), use the canonical runner:

```bash
make agent-deps
make local-cognito-bootstrap
make pals-up
```

The first-time Cognito bootstrap creates or reuses the local User Pool and App
Client, provisions the reviewer account from `.env.local`, verifies its login,
and writes the generated local IDs back to that ignored file. If the reviewer
password is absent, the helper generates one without printing it.

Run the complete public-API university-math QA with `make pals-qa`. Both commands
rebuild the checked-out application sources and use the layered E2E Compose files.

For database-only component development, use the narrower target below.

Docker Compose starts only PostgreSQL with pgvector. API, web, agent, Lean, and
Ollama are run explicitly on the host, so `make dev-up` does not build the
application containers:

```bash
cp .env.example .env.local
make dev-up
```

Use the repository-specific native commands only for the component currently
being developed. Run `make dev-down` when the database is no longer needed.
