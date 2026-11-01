# PALS

PALS is the private parent repository for the Proof Assistant Learning System.

This repository coordinates the implementation repositories, local development
workflow, documentation, and Codex helper scripts. Implementation repositories
are managed separately and will be linked from this repository after their
GitHub remotes are created.

## AWS構成図・配備状況

2026年11月2日00:25:23 JSTにseq11の公開を再開しました。全7コンテナ、サービス間TLS、Auroraの35段階の状態、カタログ保持、復旧unitを実機で確認済みです。配備用の一時KMS・RDS参照権限は削除し、不在を確認しました。

[![PALSのAWS構成図](docs/diagrams/pals-aws-private-target.png)](docs/diagrams/pals-aws-private-target.png)

[PNGを拡大](docs/diagrams/pals-aws-private-target.png) · [draw.ioで編集](docs/diagrams/pals-aws-private-target.drawio) · [配置・通信・確認範囲](docs/diagrams/README.md)

| 層 | 配備構成 |
| --- | --- |
| 公開入口 | Cloudflare → WAFを関連付けた公開ALB → private controlのCaddy。Web・APIともHTTPS |
| Web・API | t4g.medium ×1。Web、API、Caddy、reconcilerを実行。公開IPv4なし |
| Lean・生成 | r8a.large ×1。評価worker、証明worker、隔離Lean verifierを実行。公開IPv4なし |
| DB | isolated subnetのAurora PostgreSQL 16.15・pgvector。controlからTLSで接続。writerは1台 |
| 外向き通信・運用 | 許可された通信はNAT Gateway経由。S3はGateway Endpoint経由。AWS SSO・SSMで管理 |

以前137.447秒かかった自然数冪の連続性の問題は、検証済みRecipeを再利用するよう修正しました。ログインなしの同じ通常ゲストで、新しい3チャットへの回答とLeanソース表示を確認しました。

| 測定 | 送信クリックから回答表示 | 要求作成からDB保存 |
| --- | --- | --- |
| 1 | 4.775秒 | 2.664秒 |
| 2 | 4.664秒 | 2.507秒 |
| 3 | 4.830秒 | 2.683秒 |

3件とも`lean_catalog`で、保存済みの回答・Lean・コンパイル記録のハッシュが一致しています。別の本番読み取り確認で、モデル使用量・token呼び出し・新しい証明jobは0件でした。通常ゲスト枠を3から0まで消費し、リセットはしていません。

高速経路は、審査済みの完全な日本語入力2文と適合する規約・空の文脈を対象とします。公開で測定したのはそのうち1文です。それ以外の入力は通常の審査を通し、独立した2つの審査を並列化しました。すべての質問が10秒以内になるとは確認していません。[問題文・実行ID・測定方法](https://github.com/AtsushiHosaka/pals/blob/5e88f2eab52f422fe664b47aa17754729f48c72a/docs/aws-recipe-reuse-latency-2026-10-31.md#11月2日の実装と公開確認の状況)に対象範囲を記録しています。

seq11のmanifestは`a22a5f2f0a98d15b761f679cfa2e7f19f0307f9af5398d0c14d63a502c84e9c7`です。配備元は親`f6f02bc`、API`9b8b004`、worker`122f2f9`、infra`46f4010`、Web`a74b57b`です。モデルと推論量の選択機能は維持し、既定はTerra・mediumです。自動的なモデル切り替えは行いません。

図には実際の通信方向とsubnetを記載しています。大会時のxlarge切り替えと自動スケールは未配備です。1秒回答・30件を10秒以内に処理する性能、1,100件の本番利用も未達成または未検証です。全層の冗長化やセキュリティ監査の完了を示す図ではありません。[配備・復旧手順と実行記録](https://github.com/AtsushiHosaka/pals/blob/5e88f2eab52f422fe664b47aa17754729f48c72a/docs/aws-migration-runbook-2026-10-30.md)も参照してください。

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
