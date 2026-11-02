# PALS

PALS is the private parent repository for the Proof Assistant Learning System.

This repository coordinates the implementation repositories, local development
workflow, documentation, and Codex helper scripts. Implementation repositories
are managed separately and will be linked from this repository after their
GitHub remotes are created.

## AWS構成図・配備状況

[![PALS AWS architecture and deployment status](docs/diagrams/pals-aws-private-target.png)](docs/diagrams/pals-aws-private-target.png)

[PNGを拡大](docs/diagrams/pals-aws-private-target.png) · [draw.ioで編集](docs/diagrams/pals-aws-private-target.drawio) · [配置・通信・確認範囲](docs/diagrams/README.md)

署名済みseq15を配備し、2026年11月2日15:12:29.352 JSTに公開WebとAPI healthのHTTP 200を確認しました。全7コンテナ、サービス間TLS、DBの35項目、復旧unit、検索公開済み20件の署名・ソース・compiler receiptを実機で確認しています。配備前後のカタログ9項目の件数・fingerprintも一致しました。一時KMS検証・RDS参照権限は削除し、不在を確認済みです。図はseq12時点の記録で、物理構成は変えていません。

seq15のログイン済み公開画面で、自然数冪の連続性、tan 1°の無理性、右極限・非連続性の言い換え3問に回答しました。クリックから表示までは順に14.0561秒、13.9031秒、12.9266秒でした。3件ともLean検証済みRecipeを再利用し、新しいformal jobは0件です。直前のseq14では同じ3問が18.7066秒、20.7712秒、18.2612秒でした。今回も10秒目標は未達です。検証用の数学規約2件と言語設定は元に戻し、再読取で一致を確認しました。seq15のサーバー側でも、実Recipe証跡、各問のLuna・low実2呼び出し、利用枠の精算を独立に照合しました。

Web以外の診断では、20分野の言い換え40問と、条件を変えた負例20問を実モデル120呼び出しで検証しました。正例40問のうち32問が30秒以内に回答とLean再検証結果を取得し、10秒以内は0問でした。負例20問で誤った再利用はありませんでした。実コンパイル成功34件のうち、初回診断側で失敗した2件も最初の失敗判定を保持しています。[全60入力の集計・問題ごとの時間・失敗理由](docs/aws-broad-benchmark-2026-11-02.md)を記録しています。

本番はローカル検索で20候補から5件を取り出し、GPT-6 Luna・lowの独立した2審査を並列実行します。検索順位を同値の証拠にはせず、型・定義域・仮定・量化・結論・方法と保存回答のQAを照合し、両者が同じ候補を承認した場合だけ再利用します。全20候補をモデルに渡したv8の基準測定は、同値入力11/13、陰性19/19未受理でした。内訳は自然数冪4/4、tan 1°が1/3、右極限3/3、πの下界3/3です。

未採用のv11実験では、同じ32問で同値13/13を受理し、陰性19問はすべて未受理でした。64応答の実ID・使用量を照合し、出力解析とproviderの失敗は0件でした。ただし、受理した13件は6.647〜16.984秒、中央値7.341秒、p95は12.656秒で、10秒以内は12件です。キュー・保存・ブラウザー表示を含まない分類だけの時間でも、全件10秒以内には達していません。[公開3例、全20候補のv8基準、未採用実験の結果](docs/aws-recipe-semantic-benchmark-2026-11-02.md)を記録しています。

候補をembeddingで検索するv12は、自然数冪1例で毎回の検索と2審査を含め11.111秒かかり、未採用です。別途の候補20件のcache生成は、この時間に含みません。固定したローカル文字列検索のrecall@5は13/13で、検索だけの測定です。local K5と2審査を組み合わせたprivate v13の1例は8.426秒でした。その後seq14でlocal K5と、処理中状態を500ms間隔で確認するWeb `c0978aabf81b046f34ec22818ed407d1292be928`を配備しましたが、前記の公開3問はすべて10秒を超えました。

LinuxのHTTP子プロセス起動を変更したworker `01aca0a942cc88e81b9526232acb3a52cc4f08a9`、イメージ`sha256:c89591b81aac9c7850dcfc6d68b09220006884cdd9f1c8206b9ab186e095631f`は、実Linuxイメージの10項目のsmokeに合格しました。seq15として本番へ配備済みで、前記の公開3問を測定しました。

seq15配備後の実機読取では、自然文Draftは433行、現在admittedのRecipeは102件、そのうち検索公開済みは20件でした。typedカタログは4世代35行、有効世代は0です。DraftとRecipeの重複や旧revisionを足し合わせず、重複を除いた検索・利用可能な1,100件という目標は未達としています。右極限・非連続性とπの下界のR2は、実コンパイル・独立審査・署名を経て公開済みで、他18件と旧revisionのソース・回答の履歴参照も保持しました。

Web・APIはprivate controlのt4g.medium、Lean worker・verifierはprivate computeのr8a.large、DBはAuroraです。大会時のxlarge切り替え、ASG・自動スケールは未配備です。1秒回答と30人同時利用も未達成または未検証です。Lean生成の既定はTerra・mediumで、モデルの自動切り替えはありません。

配備中のseq15 manifestは`913327b2c280bcfb000aac7c0992ddefeb1d4eb1bc2bd62e1fbc6ff49c028fe3`です。署名の有効期限は2026年11月3日14:33:33 JSTで、起動時に検査します。期限切れだけでは稼働中サービスは停止しませんが、無人での署名更新は未実装です。

| 配備中のソフトウェア | commit |
| --- | --- |
| 親リポジトリ | `264b693cf59a555fc5b718f5d3057b8d946571b9` |
| API | `5ef6ebabaf8aa133ec067f8e8881153a0fb49880` |
| worker | `01aca0a942cc88e81b9526232acb3a52cc4f08a9` |
| infra | `4d9478a1601642a72ad15dc5ba82f8285b473e6e` |
| Web | `c0978aabf81b046f34ec22818ed407d1292be928` |
| verifier | `f851917c390fe7cf49d453a5ff3ec70deaf92b67` |

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
