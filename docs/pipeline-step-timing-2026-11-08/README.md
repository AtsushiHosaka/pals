# 証明1件の中のステップ別所要時間を記録する(2026-11-08)

証明1件の時間が長い原因を、段ごとに後から集計できるようにするための設計と実装の記録です。コードは pals-agent の PR [#77](https://github.com/AtsushiHosaka/pals-agent/pull/77) にあります。本番への配備と署名、AWS への書き込み(ダッシュボードとアラームの作成)は、この作業では行っていません。

## 結論

- 既存の `runtime_latency.py` は、SQS 1配信ごとの通信フェーズの集計です。どのモデル・どの推論量で、何トークン使い、何回目の試行で、どう終わったかは分かりません。この差分を埋めるため、ステップ単位の構造化イベントを追加しました。
- 既定は無効です。環境変数 `PALS_STEP_TIMING_JSONL`(ファイルへ出力)または `PALS_STEP_TIMING_EMF=1`(CloudWatch の EMF)で有効にします。
- x² の連続性を扱うカード1件を実モデル(Terra medium)で1回走らせ、段ごとの内訳が取れることを確認しました。推計費用は約0.010 USD です。
- この1回は修復なしで検証に成功し、本番の「遅い」報告は再現していません。修復が入る流れの内訳は、単体テストの合成実行で確認しています。

## 既存の仕組み(重複して作らなかったもの)

| 既存 | 内容 | 本設計との関係 |
|---|---|---|
| `pals_agent/runtime_latency.py` / `latency_report.py` | 1配信ごとの通信フェーズ(provider / api / local)の集計。`queue_wait_ms`、`unattributed_ms`。stderr に `proof_request_latency` を出す | 残す。ステップ別イベントは別の行として併存する |
| `pals_agent/usage.py` の `report_usage` / `capture_usage` | 呼び出しごとの入力・キャッシュ・出力・推論トークン | トークン取得にそのまま使う |
| `pals_agent/quality_events.py` | EMF(名前空間 `PALS/ProofQuality`)。`LeanVerifyDurationMs`、`WorkerHeartbeat`。UDP(CloudWatch エージェント)またはファイルの送信経路 | 送信経路だけ再利用する。`send_line()` を1つ足した |
| `PALS/IncidentHealth` | EMF ではなく、ホスト側の `PutMetricData`(infra PR #106)。値は 0/1 | 関係なし。名前空間も別 |
| `tools/mathlib_index/hint_ab.py` | 1カード1行の結果(経過秒、Lean 秒、呼び出し数、トークン、診断コード) | `step_timing_run` で結果行とイベントを結び付ける |
| Issue [#217](https://github.com/AtsushiHosaka/pals/issues/217) | Lean 失敗の種別と精度の監視(失敗コード、アラーム、ダッシュボード) | 失敗の種類は #217 側。本設計は所要時間の内訳を担当する |
| pals-api | EMF と所要時間・トークンのメトリクスは main に無い。API は `RequestUsage`(トークン)と `verification_elapsed_ms` を保存する | API 側は変更しない |

pals-api の `main` ではなく、品質イベントの PR(API #49 / #52)と infra PR(#94 / #96 / #106)に実装があります。調査は各ブランチの内容に基づき、未マージの部分は未確認として扱いました。

## 記録する項目

ステップ1回ごとに `pipeline_step` を1行出します。

| 項目 | 内容 |
|---|---|
| `step` | 閉じた語彙。モデルのロール(`draft` `sketch` `prove` `route` `repair` ほか)と、`lean_check` `lean_sketch_check` `lean_reconcile_wait` `lean_env_cache` `queue_wait`。範囲外は `other` |
| `model` / `effort` | モデル名(既知の名前のみ)と、実際に送った推論量。Lean 側のステップは空 |
| `duration_ms` | 所要時間 |
| `input_tokens` `cached_input_tokens` `output_tokens` `reasoning_tokens` | プロバイダ応答の使用量 |
| `outcome` | `ok` `empty` `timeout` `transport_error` `http_429` `http_4xx` `http_5xx` `malformed` `model_mismatch` `config_error` `error`(モデル)、`ok` `lean_error` `timeout` `interrupted`(Lean)、`hit` `miss` `fallback`(Lake 環境キャッシュ) |
| `attempt` | 試行番号(1が最初の生成。修復で生成する試行は +1) |
| `diag_codes` | Lean の error 診断のコードだけ(最大8件) |
| `http_status` | プロバイダの HTTP ステータス(失敗時) |
| `run` / `start_offset_ms` | 1件の実行を結ぶ値(後述)と、実行開始からのずれ |

実行の終わりに `pipeline_run` を1行出します。`total_ms` `model_calls` `model_ms` `lean_ms`、トークン合計、`step_ms`(ステップ別の合計)、`state`、`termination_reason`、`attempts`、`repairs_used` です。

待ち行列は `queue_wait`(SQS の `SentTimestamp` からの経過)、キャッシュ命中は 2 つを記録します。Lake 環境キャッシュは `lean_env_cache` の `hit` / `miss` / `fallback`、プロンプトキャッシュは `cached_input_tokens` です。証明の再利用の命中は、今回は `runtime_latency` の経路名(`assessment_no_model` など)に任せ、ステップとしては記録していません。

### 禁止項目と防ぎ方

質問本文、Lean 本文、プロンプト、モデルの回答、診断メッセージ、利用者 ID、認証情報は出力に入りません。注意書きではなく、構造で防ぎます。

- イベントは型付きの引数だけから組み立てます。文字列は閉じた語彙の要素だけを通し、それ以外は捨てるか `other` にします。ステップ名、モデル名(`PRICE_SNAPSHOTS` の既知の名前)、推論量、結果、実行の状態、終了理由は、すべて列挙された値です。
- Lean の診断コードはコンパイラの出力から読むため、候補が出力に好きな文字列を混ぜられます(`error(任意の文字列)` の形)。このため、コードは既知の一覧(`LEAN_CODES`)にあるものだけを通し、それ以外は `lean.other` として記録します。トークン形式の検査だけでは、質問由来の文字列が通ってしまいます。
- 例外の文面は読みません。OpenAI の失敗は、すでに無害化された `private_diagnostics` の語彙(`stage` `transport_kind` `http_status`)から `outcome` を決めます。
- 診断は `severity == "error"` の `code` だけを読み、`message` は読みません。
- 実行の識別は `proof_job_id` の SHA-256 の先頭16桁です。ローカルの計測ツールだけが、自分で決めた `label` を渡せます。
- テスト(`tests/unit/test_step_timing.py`)は、質問・Lean 本文・利用者 ID・診断メッセージ・モデル回答・API キーに見立てた目印の文字列を実パイプラインに通し、JSONL と EMF のどちらにも現れないことを確認します。キーの許可リストと、全文字列のトークン形式も検査します。

## 本番の回答経路(テンプレート経路)の段への対応

x² の連続性は、本番ではモデルを呼ばない決定論的テンプレートで 22〜24 秒かかります。この内訳を取るため、モデル以外の段も同じ形式で記録します。`claude/seq27-worker` の系統に載せた枝は `claude/step-timing-seq27` です(pals-agent にあり、PR は未作成)。

| 段 | 記録の出どころ | 備考 |
|---|---|---|
| テンプレ命中 | `template_hit`(`hit` / `miss`) | seq27 の枝のみ。テンプレ検索の判定時間 |
| Draft 検索・文脈取得 | `context_retrieval` | `latency_stage` を step として写したもの |
| 意味審査 | `semantic_review`(container)と、その中のモデル呼び出し(`recipe_semantic_assessment` ほか) | container は他の段を囲むので割合に足さない |
| 説明生成 | `explain`(モデル) | `explanation`(container)が囲む |
| 説明審査 | `explanation_review`(モデル) | |
| 投機的説明 | 同じ `explain`。意味審査と並行するため `pipeline_run.overlap_ms` に出る | `busy_ms` は同時刻を1回だけ数えた時間、`unattributed_ms` は壁時計から `busy_ms` を引いた時間 |
| worker の job 取得待ち | `queue_wait`(SQS の `SentTimestamp` から) | 時計のずれで近似 |
| API → 検証器の Lean 検査 | worker の `lean_reconcile_wait`、検証器の `lean_stage`(`environment_prepare` `compile` `audit` `total`、環境キャッシュ)、API の `candidate_verification`(`candidate_wait_ms` `verify_ms`) | 既存の `latency_report.py` が集計する。API 側のイベントは品質 PR の枝にあり、main にはない |
| 結果確定から画面反映 | API の `proof_request_terminal_read.terminal_age_ms`、`client_answer_timing` | step 形式ではなく既存イベントのまま |

Lean 検査の「キュー待ち・起動・import・検査」の分割は、検証器の `lean_stage` が `environment_prepare`(起動と import の準備)、`compile`(検査)、`audit` を分けています。キュー待ちは `candidate_wait_ms` が近い値ですが、いずれも本計測とは別のログで、1件ごとの結合キーがありません。結合できるのは時刻の近さだけです。この点は未解決です。

### 実測: 投機的説明の有効・無効(実モデル、各3回、約0.019 USD)

x2-root-cure の `tools/speculative_ab.py`(枝 `claude/seq27-timing-ab-steps`)を `--real --confirm-spend -n 3` で実行しました。意味審査の状態から始め、`PALS_SPECULATIVE_EXPLANATION_ENABLED` だけを切り替えて、off・on を交互に3回ずつ走らせています。命題と Lean は検証済みの x² テンプレート(ε-δ)に手元で差し替えました(言語はハーネス既定の zh-Hans。同じ枝に追加された `--lean x2 --language ja` は使っていません)。モデルは意味審査・説明・説明審査とも gpt-6-luna です。API は stub で、Lean の検証は行いません。生の出力は [raw/](raw/) にあります。

| 段 | off の p50 | on の p50 | 備考 |
|---|---|---|---|
| 意味審査(モデル1回) | 3.4 秒 | 4.7 秒 | |
| 説明生成 | 12.9 秒 | 13.6 秒 | on では意味審査と並行して始まる |
| 説明審査 | 8.2 秒 | 12.3 秒 | 1配信で2回呼ばれる(全体では12呼び出し) |
| 開始から説明の書き込みまで | 22.4 秒(平均 20.1) | 20.2 秒(平均 21.0) | |

- 対応のある差(off − on、正なら有効側が速い)は、合計で平均 −0.9 秒、95% 信頼区間 [−9.0, +4.0] 秒でした。3回ずつでは、フラグの効果は検出できません。
- 意味審査と説明審査は on の方が遅い傾向でしたが、これも3回の範囲で、原因は調べていません。並行実行による競合か、モデル応答の揺れかは区別できていません。
- 段別の内訳は、説明生成が約47%、説明審査が約38%、意味審査が約14%です(container の `explanation` `semantic_review` は除く)。説明の2段で約8割を占めます。
- 範囲外: この実測は意味審査から説明の書き込みまでです。API → 検証器の Lean 検査、独立2審査の1つ目、worker の job 取得待ち、画面反映は含みません。本番の22〜24秒との直接比較はできません。
- ハーネスは `run_scope` を使わないため、`pipeline_run`(`overlap_ms` など)は出ていません。並行の重なりは、段別の `start_offset_ms` を見る必要があります。

## 書き込みの仕組み

イベントは呼び出し側のスレッドで直列化し、有界のキュー(1,024件)と専用のデーモンスレッドで書きます。出力先が止まっても(stderr のパイプが満杯など)、計測された呼び出しは待ちません。キューが満杯なら、そのイベントを捨てて `sink_errors()` に数えます。JSONL と EMF は別々に失敗を握るので、片方が壊れても他方は書きます。プロセス終了時と `flush()` で残りを書き出します。

1回の配信(`traced_delivery`)は1つの実行として扱い、worker の段(意味審査、説明)とパイプラインが同じ `run` と `pipeline_run` を共有します。1つの実行に記録するステップは2,048件までで、超えた分は `truncated` と `dropped_steps` で示し、レポートが警告します。

## CloudWatch の形

名前空間は `PALS/Pipeline` です。EMF の行は、既存の `quality_events` の送信経路(CloudWatch エージェントへの UDP、またはファイル)が設定されていればそこへ、なければ stderr へ出します。コンテナのログドライバが拾う前提です。

| 指標 | ディメンション | 備考 |
|---|---|---|
| `step_duration_ms`(ミリ秒) | `step` `model` `outcome` | ステップ1回ごとに1値。p50/p95 は CloudWatch の統計で取る |
| `run_total_ms` `run_model_ms` `run_lean_ms`(ミリ秒)、`run_model_calls`(回数) | `outcome` | 実行1件ごとに1値 |

系列数を抑える工夫は 3 つです。

- メトリクスの `outcome` は粗い 7 値(`ok` `hit` `miss` `fallback` `timeout` `rejected` `error`)に畳みます。詳しい値は同じ行の `outcome_detail` に残り、Logs Insights で見られます。
- 実行単位の指標の `outcome` は `verified` / `failed` / `other` の3値です。
- トークン、`attempt`、`run`、診断コードは指標にせず、ログの項目に置きます。

### 集計

| 知りたいこと | 方法 |
|---|---|
| ステップ別の p50/p95 | CloudWatch の `step_duration_ms` を `p50` / `p95` 統計で。ローカルは `python -m pals_agent.step_timing_report` |
| 1件あたりの合計 | `run_total_ms`(p50/p95)。実行を結べるのでログ側では `pipeline_run.total_ms` |
| 段ごとの割合 | `pipeline_run.step_ms` ÷ `total_ms`。レポートの「share of run time」と「unattributed」 |
| 試行ごとの内訳 | `pipeline_step` を `run` と `attempt` で集計する(Logs Insights) |
| トークンと費用 | `pipeline_step` のトークン項目をモデル別に合計する |

Logs Insights の例です。

```
fields step, model, outcome_detail, duration_ms
| filter event = "pipeline_step"
| stats count() as n, pct(duration_ms, 50) as p50, pct(duration_ms, 95) as p95, sum(duration_ms) as total by step, model
| sort total desc
```

## ダッシュボードとアラームの案(作成していません)

ダッシュボード案(1枚、ウィジェット6つ):

1. `run_total_ms` の p50 と p95(`outcome=verified` と `failed`)
2. ステップ別の `step_duration_ms` p95(`draft` `sketch` `prove` `repair` `route`、Terra)
3. `lean_check` / `lean_sketch_check` の p95 と、`outcome=timeout` の件数
4. 実行時間の内訳(ログのクエリ。ステップ別の `total` を積み上げ)
5. `queue_wait` の p95(既存の SQS `ApproximateAgeOfOldestMessage` と並べる)
6. `lean_env_cache` の `hit` / `miss` / `fallback` の件数

アラーム案(初期値は1週間分の実測を見て決める。ここで決めた数値の根拠はまだありません):

| アラーム | 条件の案 |
|---|---|
| 実行時間の悪化 | `run_total_ms` p95 が 600 秒超、1時間周期で 2/3 |
| Lean 検査の時間切れ | `step_duration_ms`(`lean_check`、`outcome=timeout`)の `SampleCount` が 1時間で 3 以上 |
| 待ち行列の悪化 | `step_duration_ms`(`queue_wait`)p95 が 300 秒超。既存の backlog アラーム(最古メッセージ 900 秒)の前段 |

既存の品質アラーム(infra PR #94 / #96)は失敗の種類を見ます。本案は所要時間だけを見ます。重複させません。

## 費用の概算

単価は `specs/proof-quality-observability/requirements.md` が前提にした値(東京リージョン。要確認)を使います。カスタムメトリクス 0.30 USD/月、アラーム 0.10 USD/月、ログ取り込み 0.76 USD/GB、ダッシュボード 3 USD/月です。

| 項目 | 見積り |
|---|---|
| 系列数 | 期待 約65(ステップ約55 + 実行12)、最大 約100。内訳は、証明経路のモデルステップ約15、そのほかのロール約16、Lean 検査約6、環境キャッシュ3、待ち行列と照合待ち3、モデル違いによる増分 |
| メトリクス | 期待 約20 USD/月、最大 約30 USD/月 |
| ログ | 1日500件の実行、1件あたり 5〜20 ステップ、1行約1 KB として月 0.1〜0.3 GB。約0.2 USD/月 |
| アラーム 3 + ダッシュボード 1 | 約3.3 USD/月 |
| 合計 | 期待 約24 USD/月、最大 約34 USD/月 |

系列数が支配的です。既存の品質計画は `PALS/ProofQuality` の系列を最大140(上限150)と見積もっています。上限が名前空間ごとなら本案は収まりますが、アカウント全体の予算ならあふれます。この点はオーナーの判断が要ります。節約するなら、証明経路以外のロールをメトリクスから外す(約16系列、約5 USD/月)のが最も効きます。

## 使い方

```bash
# ファイルへ出力(ローカル)
PALS_STEP_TIMING_JSONL=/path/steps.jsonl python tools/mathlib_index/hint_ab.py ... --step-timing
python -m pals_agent.step_timing_report /path/steps.jsonl --hint-ab /path/results.jsonl

# CloudWatch(本番。送信経路は quality_events の設定を共用)
PALS_STEP_TIMING_EMF=1
```

## 実測の例: x² の連続性(Terra medium、1回)

条件: `hint_ab.py --arms baseline --model gpt-6.1-terra --effort medium --max-repairs 6`、固定版 Lean 4.32.0-rc1、形式命題 `Continuous (fun x : ℝ => x ^ 2)`、依頼文「x² が連続であることを示してください。」。結果は検証成功、修復 0 回、経過 30.1 秒、推計費用 約0.010 USD(入力 4,329、出力 1,001 トークン、Terra の価格 1.25 / 5.00 USD/百万トークン)です。生の出力は [raw/](raw/) にあります。

| 順 | ステップ | モデル | 推論量 | 所要 ms | 割合 | 入力 | 出力 | 推論 | 結果 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | draft | gpt-6.1-terra | medium | 2,864 | 9.5% | 714 | 118 | 0 | ok |
| 2 | sketch | gpt-6.1-terra | medium | 8,232 | 27.3% | 1,629 | 609 | 473 | ok |
| 3 | lean_sketch_check | - | - | 4,926 | 16.3% | - | - | - | ok |
| 4 | prove | gpt-6.1-terra | medium | 4,600 | 15.3% | 1,986 | 274 | 133 | ok |
| 5 | lean_check | - | - | 9,508 | 31.6% | - | - | - | ok |
| | 合計 | | | 30,134 | 100% | 4,329 | 1,001 | 606 | |

- モデル呼び出し 3 回が 15.7 秒(52%)、Lean 検査 2 回が 14.4 秒(48%)でした。帰属できない時間は 0.0% です。
- `hint_ab.py` の結果行との突き合わせでは、呼び出し数 3、入力 4,329、出力 1,001、経過 30.1 秒が一致しました。
- 一致しなかったのは `lean_seconds` です。`hint_ab.py` は 9.5 秒、本計測は 14.4 秒でした。`hint_ab.py` は最終検証の `elapsed_ms` だけを足し、Sketch の Lean 検査(4.9 秒)を含めていないためです。これまでの `lean_seconds` は、Lean 時間を最大で約3割(この例では 4.9 / 14.4)少なく見せていた可能性があります。
- プロンプトキャッシュの命中は 0 トークンでした(3 呼び出しとも入力が異なるため)。

### 修復が入る流れ

実モデルの1回では修復が起きなかったため、修復を含む流れは合成実行で確認しました(`test_one_repair_run_yields_the_per_step_breakdown`)。ステップは `prove(1) → lean_check(1, lean_error) → route(2) → repair(2) → lean_check(2, ok)` の順に並び、`attempt` は修復で生成する試行から +1 になります。`pipeline_run` は `attempts=2`、`repairs_used=1`、`model_calls=3` を持ちます。

## 検証

- 追加テスト 32 件(seq27 の枝では 33 件)(`tests/unit/test_step_timing.py`)が通ります。無効時に何も出さないこと、provider 失敗が有限の `outcome` になって例外が元のまま出ること、sink 失敗が呼び出しを変えないこと、EMF のディメンション、禁止項目の漏れなしを含みます。
- `tests/unit` 全体は 49 件失敗しますが、Mathlib が見つからない、docker-compose のファイルがない、ポート競合など環境が原因です。関連ファイル(`test_pipeline` `test_openai` `test_lean` `test_worker` `test_quality_events` ほか)は単独で全件通ります。ベースライン(origin/main)との件数比較は、別 worktree の収集エラーで取れていません。
- 変更した各ファイルの ruff と、新規 2 モジュールの mypy は通ります。

## 未検証

- CloudWatch での実取り込み、メトリクスの抽出、ダッシュボードとアラームの動作は未確認です(AWS には書き込んでいません)。EMF の行の形は、単体テストと仕様の範囲で確認しただけです。
- 実モデルは 1 回だけで、修復・時間切れ・HTTP 失敗を含む実測は取っていません。
- 並列スレッドで走るモデル呼び出し(Recipe の意味審査など)は、ContextVar が伝わらないため `run` と `attempt` が空になります。イベントは出ます。
- 計測が有効なとき、`OpenAIResponsesClient.generate` は `capture_usage` を挟みます。使用量の記録先は変わりませんが、本番で有効にする前に負荷とレイテンシの影響を見る価値があります。
- 配備と署名は行っていません。`pals-agent` の参照更新も行っていません。
