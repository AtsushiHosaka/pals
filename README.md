# PALS

PALS is the private parent repository for the Proof Assistant Learning System.

This repository coordinates the implementation repositories, local development
workflow, documentation, and Codex helper scripts. Implementation repositories
are managed separately and will be linked from this repository after their
GitHub remotes are created.

## AWS構成図・配備状況

[![PALS AWS architecture and deployment status](docs/diagrams/pals-aws-private-target.png)](docs/diagrams/pals-aws-private-target.png)

[PNGを拡大](docs/diagrams/pals-aws-private-target.png) · [draw.ioで編集](docs/diagrams/pals-aws-private-target.drawio) · [配置・通信・確認範囲](docs/diagrams/README.md)

現在のソフトウェアは署名済みseq12です。2026年11月2日04:58:11 JSTの公開後読取で、右極限・非連続性とπの下界のRecipeがrevision 2へ置き換わったことを確認しました。新しいLeanソースの実コンパイル、独立審査、署名、2件の原子的な公開を実施し、公開後に有効20件の証拠、他18件の保持、旧revisionのソース・回答の履歴参照を読み取り専用で確認しました。図の物理構成は変えていません。

公開済みR2を含む20候補を使ったv8の実API評価では、同値・変数名変更13問中11問を受理し、陰性19問はすべて未受理でした。内訳は自然数冪4/4、tan 1°が1/3、右極限3/3、πの下界3/3です。64応答はすべてHTTP 200で、返されたtargetのSHA-256不一致による出力検査の拒否が1件、provider失敗は0件でした。受理した11件の分類時間は5.871〜7.120秒、中央値6.232秒です。キュー・保存・ブラウザー表示は含まず、言い換えた質問への公開画面での10秒以内は未検証です。[現行v8、旧v7、none比較の結果と制限](docs/aws-recipe-semantic-benchmark-2026-11-02.md)を記録しています。

2026年11月2日05:16:57 JSTの実機読取では、自然文Draftは433行、現在admittedのRecipeは102件、そのうち検索公開済みは20件でした。typedカタログは4世代35行、有効世代は0です。DraftとRecipeの重複や旧revisionを足し合わせず、重複を除いた検索・利用可能な1,100件という目標は未達としています。数学的な言い換えはGPT-6 Luna・lowの独立した2呼び出しで並列に確認し、型・仮定・量化・結論・方法と保存回答について両者が一致した場合だけ再利用します。旧20候補での静的none比較は同値7/13、出力検査の拒否2件で、採用していません。

health修正のseq13は、API `5ef6ebabaf8aa133ec067f8e8881153a0fb49880`とmanifest `b021df9144fb261235b13e63616b6d3d0eb6d1863978a8c3f8f3e438f6ae9dfe`の署名、両ホストの配備用ファイル準備までです。DB admissionとactivationは未実施です。AWS作業用SSOの失効により、停止コマンドの送信前に止まっており、公開経路の停止やdrainは行っていません。この作業で追加した一時参照権限は最終確認時点では残っています。有効期限は2026年11月2日06:01:53 JSTで、再認証後の削除確認は未完了です。公開測定用アカウントのログイン確認も待っています。

Web・APIはprivate controlのt4g.medium、Lean worker・verifierはprivate computeのr8a.large、DBはAuroraです。大会時のxlarge切り替え、ASG・自動スケールは未配備です。1秒回答と30人同時利用も未達成または未検証です。Lean生成の既定はTerra・mediumで、モデルの自動切り替えはありません。

現在配備中のseq12は、2026年11月2日03:02:32 JSTに元のALB listenerとruleで公開を再開しました。全7コンテナ、サービス間TLS、DBの35項目、復旧unitと当時のカタログ9項目の保持、公開Web・API healthのHTTP 200を確認しています。manifestは`6f84b0967c9ef4cd12fb6658764599c2d5ccd2c7582daa03b67376df358acf3f`です。

| 配備中のソフトウェア | commit |
| --- | --- |
| 親リポジトリ | `e65906a01ff182e7e40e5aa7a98b8bdf7ae09751` |
| API | `7cde9674b0ff61d92116280f303638351362729e` |
| worker | `7c000dbb84288e01391e72bde796b53bfdd51608` |
| infra | `cf212c9134e4c4bf7a6747d8628f61bd98dd6027` |
| Web | `a74b57b130ac0de6c7bf793ca095e81b54c4344f` |

以前のseq11では、完全一致する自然数冪の日本語入力をモデル呼び出しなしで再利用し、通常ゲストの3チャットで4.775秒・4.664秒・4.830秒で回答とLeanソースを表示しました。これは今回の言い換え経路とは別の公開実測です。[対象の全文・測定方法・利用枠・記録](docs/aws-recipe-reuse-latency-2026-10-31.md)を参照してください。

The earlier observations below retain their original release and timing context.

At 2026-11-01 01:29 JST, the signed sequence-5 update was deployed to the
private AWS runtime, and the Cloudflare/TLS ALB listener and rules were restored.
A public Japanese tan-one-degree question reached `answered` with its proof and
Lean source displayed. Its verified Recipe was reused in 47.153515 seconds of
server time, with independent request/answer correspondence checks. Aurora holds
433 seeded Drafts and 102 compiler-verified Recipes. Of those Recipes, 20 have
independently approved searchable entries; the new 82 are not yet searchable.
A set of 744 typed Draft candidates passed local Lean and axiom replay; the new
82 Recipes come from that same set and are not additional unique propositions.
There are 35 inactive typed Drafts across four generations and none active in
production. Nine catalog counts and content/vector fingerprints were unchanged
across this update. The 1,100 usable-item target is not yet achieved.
Chat history was not imported, as requested.

The sequence-5 manifest is
`3c4f602e217e22685daa13eafca69fd4a6dc2cf48aa0c0bdae7f477e18442b18`.
All 33 preflight checks, all seven containers, private TLS connections and recovery
unit checks passed. The temporary KMS verification/RDS read policy was removed
and its absence confirmed. Typed catalog publication remains disabled pending
content review and real retrieval/proof evaluation.

The Web update moves project navigation to the sidebar heading and creation to
its + button, keeps plan/usage under Settings, and reuses an empty chat without
losing its draft or attachments. Fractions and exponents can be edited inline in
prose, with fonts served from PALS. Public checks passed project navigation and
creation/cancel, Settings-to-usage access, empty-chat reuse, and ordinary keyboard
fraction input with TeX copy. Sequence 5 had a reproducible double-paste defect.
The corrected Web image, commit `79f2df0722d241663851bab9fa66cc5b99fb09df`,
was deployed in sequence 6. Its signed manifest is
`b17899ab82efad2dc27bae99985fc78593012bb43bb4aa30984c281375f527d4`.
The owning Aurora update admitted it without changing the API, worker or
verifier image/toolchain; the temporary KMS/RDS policy was removed and its
absence verified. All seven containers, private TLS and recovery-unit checks
passed, and all nine catalog fingerprints were preserved. Public access was
restored around 2026-11-01 01:57:50 JST with the ALB target healthy. After a
transient connection error cleared on reload, the authenticated browser showed
history and the Japanese proof. Explicit paste followed by TeX copy returned
`\frac{n}{n+1}` without duplicated characters in the public Web UI. In a new
empty chat, pressing New Chat twice kept the same URL, one list item and the
unsent Japanese draft, and returned focus to the composer.

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
but an actual reboot test has not been performed. Controlled restart/rebuild
permission for the current sequence-11 release expires on 2026-11-03
at 00:08:30 JST; running services do not stop solely because that time passes. See the runbook for the
release window and the shared-network guest quota.

- [Migration runbook and execution status](docs/aws-migration-runbook-2026-10-30.md)
- [AWS security checks and catalog expansion evidence](docs/aws-security-and-catalog-check-2026-10-31.md)
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
