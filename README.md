# PALS

PALS is the private parent repository for the Proof Assistant Learning System.

This repository coordinates the implementation repositories, local development
workflow, documentation, and Codex helper scripts. Implementation repositories
are managed separately and will be linked from this repository after their
GitHub remotes are created.

## AWS構成図

2026年11月1日01:57 JSTに公開を再開した本番構成です。Web・API・Leanの7コンテナをAWSのprivate subnetで稼働させ、本番DBにはAurora PostgreSQLを使用しています。

[![PALSのAWS構成図](docs/diagrams/pals-aws-private-target.png)](docs/diagrams/pals-aws-private-target.png)

[PNGを拡大](docs/diagrams/pals-aws-private-target.png) · [draw.ioで編集](docs/diagrams/pals-aws-private-target.drawio) · [配置・通信・確認範囲](docs/diagrams/README.md)

| 層 | 配備構成 |
| --- | --- |
| 公開入口 | Cloudflare → WAFを関連付けた公開ALB → private controlのCaddy。Web・APIともHTTPS |
| Web・API | t4g.medium ×1。Web、API、Caddy、reconcilerを実行。公開IPv4なし |
| Lean・生成 | r8a.large ×1。評価worker、証明worker、隔離Lean verifierを実行。公開IPv4なし |
| DB | isolated subnetのAurora PostgreSQL 16.15・pgvector。controlからTLSで接続。writerは1台 |
| 外向き通信・運用 | 許可された通信はNAT Gateway経由。S3はGateway Endpoint経由。AWS SSO・SSMで管理 |

図には実際の通信方向とsubnetを記載しています。xlargeへの大会時切り替えと自動スケールは未配備です。1秒回答・30件を10秒以内に処理する性能も未達成または未検証です。全層の冗長化やセキュリティ監査の完了を示す図ではありません。

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
