# PALS

PALS is the private parent repository for the Proof Assistant Learning System.

This repository coordinates the implementation repositories, local development
workflow, documentation, and Codex helper scripts. Implementation repositories
are managed separately and will be linked from this repository after their
GitHub remotes are created.

## Repository Layout

- `pals-api` - private FastAPI backend
- `pals-webfront` - private frontend application
- `pals-infra` - private Terraform infrastructure
- `pals-datasets` - private ingestion and dataset tooling
- `pals-observability` - private observability and tracing operations
- `pals-agent` - public OSS LangGraph agent with Lean verifier tooling

Lean verification lives in `pals-agent` because it is a first-class agent tool.
Production can still run the verifier as a separate sidecar process or
container.

## Secret Policy

Do not commit API keys, database URLs, AWS credentials, Langfuse secrets, or
production configuration. Use local `.env.dev` and `.env.prod` files only.
