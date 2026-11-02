# PALS

PALS is the private parent repository for the Proof Assistant Learning System.

This repository coordinates the implementation repositories, local development
workflow, documentation, and Codex helper scripts. Implementation repositories
are managed separately and will be linked from this repository after their
GitHub remotes are created.

## AWS構成図・配備状況

[![PALS AWS architecture and deployment status](docs/diagrams/pals-aws-private-target.png)](docs/diagrams/pals-aws-private-target.png)

[PNGを拡大](docs/diagrams/pals-aws-private-target.png) · [draw.ioで編集](docs/diagrams/pals-aws-private-target.drawio) · [配置・通信・確認範囲](docs/diagrams/README.md)

署名済みseq13を配備し、2026年11月2日10:39:34 JSTに公開WebとAPI healthのHTTP 200を確認しました。全7コンテナ、サービス間TLS、DBの35項目、復旧unit、現在の検索公開済み20件の署名・ソース・compiler receiptを実機で確認しています。配備前後のカタログ9項目の件数・fingerprintも一致しました。更新した一時KMS検証・RDS参照権限は削除し、不在を確認済みです。図はseq12時点の記録で、物理構成は変えていません。

2026年11月2日、ログイン済みの公開画面から言い換えた3問を送信し、自然数冪の連続性、tan 1°の無理性、右極限・非連続性の回答とLeanソースを確認しました。送信クリックから回答表示までは順に18.1981秒、21.5066秒、18.4529秒で、10秒目標は3件とも未達です。サーバー側でも、実20候補の証拠と各回答・Leanの結び付け、質問ごとのLuna・low実2呼び出し、有料利用枠の精算を確認しました。新しいformal jobは作成していません。費用は版付き単価による推計で、provider請求書の実額ではありません。検証で変更した数学規約2件と言語設定は元に戻し、再読取で一致を確認しました。

本番の数学的な言い換え判定はGPT-6 Luna・lowのv6審査方針のままです。独立した2呼び出しを並列に行い、型・仮定・量化・結論・方法と保存回答について両者が一致した場合だけ再利用します。現在のR2を含む20候補で行ったv8実API評価は、同値入力11/13、陰性19/19未受理でした。内訳は自然数冪4/4、tan 1°が1/3、右極限3/3、πの下界3/3です。

未採用のv11実験では、同じ32問で同値13/13を受理し、陰性19問はすべて未受理でした。64応答の実ID・使用量を照合し、出力解析とproviderの失敗は0件でした。ただし、受理した13件は6.647〜16.984秒、中央値7.341秒、p95は12.656秒で、10秒以内は12件です。キュー・保存・ブラウザー表示を含まない分類だけの時間でも、全件10秒以内には達していません。[公開3例、本番方針のv8基準、未採用実験の結果](docs/aws-recipe-semantic-benchmark-2026-11-02.md)を記録しています。

候補をembeddingで検索してモデル入力を5件に絞るv12は、自然数冪1例で再利用に成功しましたが、毎回の検索と2審査を含め11.111秒かかり、10秒目標未達のため未採用です。別途行った候補20件の埋込cache生成は、この時間に含みません。ローカル文字列検索のrecall@5は13/13で、これ自体は検索だけの測定です。local K5と2審査を組み合わせたv13は自然数冪1例で8.426秒でしたが、公開画面の計測ではなく、未採用です。500ms間隔で処理中状態を確認するWeb `c0978aabf81b046f34ec22818ed407d1292be928`も、イメージ公開までで本番には配備していません。配備中のWebは下表の`a74b57b`です。

2026年11月2日10:31:27 JSTの実機読取では、自然文Draftは433行、現在admittedのRecipeは102件、そのうち検索公開済みは20件でした。typedカタログは4世代35行、有効世代は0です。DraftとRecipeの重複や旧revisionを足し合わせず、重複を除いた検索・利用可能な1,100件という目標は未達としています。右極限・非連続性とπの下界のR2は、実コンパイル・独立審査・署名を経て公開済みで、他18件と旧revisionのソース・回答の履歴参照も保持しました。

Web・APIはprivate controlのt4g.medium、Lean worker・verifierはprivate computeのr8a.large、DBはAuroraです。大会時のxlarge切り替え、ASG・自動スケールは未配備です。1秒回答と30人同時利用も未達成または未検証です。Lean生成の既定はTerra・mediumで、モデルの自動切り替えはありません。

配備中のseq13 manifestは`b021df9144fb261235b13e63616b6d3d0eb6d1863978a8c3f8f3e438f6ae9dfe`です。

| 配備中のソフトウェア | commit |
| --- | --- |
| 親リポジトリ | `d54089d00bf1cd46f74ffd0f34dcad3cb79da501` |
| API | `5ef6ebabaf8aa133ec067f8e8881153a0fb49880` |
| worker | `7c000dbb84288e01391e72bde796b53bfdd51608` |
| infra | `cf212c9134e4c4bf7a6747d8628f61bd98dd6027` |
| Web | `a74b57b130ac0de6c7bf793ca095e81b54c4344f` |
| verifier | `f851917c390fe7cf49d453a5ff3ec70deaf92b67` |

以前のseq11では、完全一致する自然数冪の日本語入力をモデル呼び出しなしで再利用し、通常ゲストの3チャットで4.775秒・4.664秒・4.830秒で回答とLeanソースを表示しました。これは今回の言い換え経路とは別の公開実測です。[対象の全文・測定方法・利用枠・記録](docs/aws-recipe-reuse-latency-2026-10-31.md)を参照してください。

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
