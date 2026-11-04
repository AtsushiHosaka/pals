# 品質台帳(Quality Ledger)

PALS の評価と測定の結果を1つの機械可読な台帳に集め、失敗の種類と精度の推移をグラフにします。チャットやセッションごとに結果が散らばらないようにするための場所です。依頼の元は [#216](https://github.com/AtsushiHosaka/pals/issues/216) です。

| ファイル | 内容 |
|---|---|
| [ledger.csv](ledger.csv) | 台帳の本体。1行が1回の測定 |
| [ledger.schema.md](ledger.schema.md) | 列の定義と記入の規則 |
| [taxonomy.md](taxonomy.md) | 失敗分類(提案)。コード、定義、タグ、通知の方針 |
| [audit_ledger.py](audit_ledger.py) | 標準ライブラリだけで台帳を検査し、記録項目の空欄数を集計する |
| [make_charts.py](make_charts.py) | 台帳を検査してグラフを生成する |
| [charts/](charts/) | 生成した PNG(ライト用とダーク用) |

## 現在の内容

2026-08-28から2026-11-05までの279行です。出典の内訳は、docsが199行、pals-agentのPRが49行、palsのIssueが21行、palsのPRが10行です。palsのPRとIssueの多くはdocsと重複していたため、台帳では1行にまとめて`source`に両方を書きました。

系統ごとの行数は、`recipe_retrieval` 68、`lean_runtime` 41、`proof_generation` 40、`catalog_audit` 24、`guest_quality` 22、`answer_latency` 19、`exact_precheck` 18、`statement_index` 17、`feature_audit` 15、`availability` 11、`other` 4です。

2026-11-04の[引き継ぎ確認](../quality-observability-audit-2026-11-04.md)に、CloudWatchの実装と未検証の範囲、プロンプトの変更前後を比較するために今後記録する項目をまとめています。既存の散布図には、題材や成功の定義が違う点が含まれます。図全体からモデルの精度向上を判断しません。

2026-11-05の[説明プロンプトの小規模比較](../prompt-benchmark-2026-11-05.md)を2行追加しました。同じ2題で旧版・変更案とも2/2であり、改善は確認できていません。費用は使用量からの保守的な推計、時間は生成と後追いレビューのHTTP累計です。本番E2Eや数学全般の精度とは分けます。

同日の[seq18署名更新](../seq18-renewal-result-2026-11-05.md)後の稼働確認も1行記録しました。7サービスのその時点のコンテナ状態であり、継続的な稼働率や回答成功率ではありません。

## 台帳だけを検査する

次のコマンドは追加パッケージ、モデル呼び出し、AWS接続なしで実行できます。JSONには件数と整合性の検査結果を出し、台帳の本文は出しません。空欄は0で埋めません。モデルを使わない測定もあるため、空欄の多さだけで記録漏れとは判断しません。

```bash
python3 docs/quality-ledger/audit_ledger.py --json
python3 -m unittest discover -s docs/quality-ledger -p 'test_*.py'
```

列、一意なID、日付、列挙値、有限かつ非負の数値、整数の件数、成功率と分母の対応、p50とp95の順序、失敗コードと件数、重複参照を検査します。出典の内容の正しさや、異なる測定を比較してよいかは自動判定しません。グラフを生成するときも同じ検査を先に実行します。

## グラフ

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="charts/success_rate_by_family_dark.png">
  <img alt="系統ごとの成功率の推移" src="charts/success_rate_by_family_light.png">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="charts/failure_breakdown_dark.png">
  <img alt="失敗コードごとの行数と件数" src="charts/failure_breakdown_light.png">
</picture>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="charts/cost_latency_over_time_dark.png">
  <img alt="費用と所要時間の推移" src="charts/cost_latency_over_time_light.png">
</picture>

## 評価のあとに行を足す手順

評価や測定を実行したら、同じ PR(または記録を残す PR)で次の順に台帳へ足します。

1. 結果を docs か PR 本文に先に書きます。台帳は要約であり、根拠は出典に置きます。
2. `ledger.csv` に1行を足します。列は [ledger.schema.md](ledger.schema.md) に従います。不明なセルは空にします。
3. 失敗があれば、[taxonomy.md](taxonomy.md) のコードで `failures_json` に件数を書きます。出典の文字列は `failures_raw_json` に残します。該当するコードがなく原因も不明なら `unclassified` にします。新しいコードが要るときは、同じ PR で taxonomy.md に定義、タグ、通知の方針を足します。
4. `source` に根拠(docs はパスとコミット、PR と Issue は URL)を書きます。根拠をたどれない値は書きません。
5. グラフを再生成し、`ledger.csv` と `charts/` を一緒にコミットします。

```bash
python -m venv .venv && .venv/bin/pip install pandas matplotlib   # 初回のみ
.venv/bin/python docs/quality-ledger/make_charts.py
```

`make_charts.py` は標準ライブラリ、pandas、matplotlib だけを使います。ネットワーク、モデル呼び出し、AWS 呼び出しはしません。台帳に不整合があると、グラフを作らずに止まります。

## 使うときの注意

- **別の題材の行は比べられません。** `dataset` と `experiment` が違えば、n、難しさ、成功の定義が違います。成功率のグラフは、同じ実験の系列の中だけで読みます。
- **比較してよい行の例。**
  - 同じ題材を、モデルや設定だけ変えて測った行(例: `2026-11-03-hint-ab-*` の Luna low と Terra medium、ヒントあり・なし)。
  - 同じ32問を、判定の構成だけ変えて測った行(例: `2026-11-02-sem-*` の r1・r2・v11)。
  - 同じ測定を、修正の前後で測った行(例: `pr24-flag-on-before-fix` と `pr24-flag-on-after-fix`)。
- **比較してはいけない行の例。** `catalog_audit`(カタログの網羅率)と `proof_generation` の成功率、n が1〜3の行と n が100以上の行、再現率(Hit@20 など)と合否の率。
- **成功率の意味は行ごとに違います。** 合否の率、再現率、「誤再利用がなかった割合」が混在します。意味は `notes` と `experiment` で確認します。
- **n が小さい行が多くあります。** n が1〜3の行は、1回の実行の記録として読み、率として読みません。
- **費用は推計です。** 多くは版付き単価に使用量を掛けた値で、請求額ではありません。メモリの記述にあった約27米ドルは、定価換算です。
- **合計の行は足さないでください。** `overlap_with` が空でない行は、他の行の合計や一部を含みます。
- **失敗の件数は繰り返しを含みます。** 同じ質問を50回繰り返した実行は、50件と数えます。失敗の内訳のグラフは、行数と件数の両方を示しています。
- **実行環境は`local macOS`が多く、`AWS`で測った行は24行です。** 所要時間は環境で大きく変わるので、環境の違う行の所要時間を比べません。環境が書かれていない行は空です。該当するのは34行です。
- **出典の日付が実行日とは限りません。** 実行日が書かれていない行は PR のマージ日や docs の日付を使っています。`notes` に書いています。

## 台帳に入れなかったもの

- 単体テスト、CI、型検査の通過件数(評価ではないため)。
- 設計、計画、予算、価格表にある数値(測定ではないため)。
- 配備や運用の記録の個別の成否(例: 配備の失敗とその再試行)。件数として整理できる形で書かれていないためです。
- pals-agent の PR で、数値が親リポジトリの docs にだけある PR(例: pals-agent#40)。docs の側の行に入れています。
- オーナーのメモリのファイルにある数値のうち、リポジトリの docs や PR から根拠をたどれないもの。27 米ドルの評価費用は、Issue の記録とあわせて1行にしました。ほかにメモリだけを根拠とする記述(seq16 のリリースメモ)は入れていません。
- 出典に数値のない Issue と PR。

## Langfuse

リポジトリで確認できたことと、台帳との関係です。

- `pals-observability` は、正本のローカル評価履歴(schema-v2、JSONL)を **明示的な操作で** Langfuse へ書き出す部品です。Langfuse は比較用の任意の画面で、証明生成やローカル評価の依存先ではないと、その README に書かれています。出典: pals-observability の README(非公開リポジトリ)。
- 設計資料でも `pals-observability` は「privacy-minimized evaluation・trace export」で、JSONL と Langfuse の書き出しを担います([u22-2026-submission-research-dossier.md](../u22-2026-submission-research-dossier.md))。
- 回答経路の所要時間の計測は、Langfuse を使っていません。[answer-path-latency-tracing-2026-11-02.md](../answer-path-latency-tracing-2026-11-02.md) は、固定のラベルと数値だけを記録する別の仕組みだと書いています。
- 本番の LLM 呼び出しが Langfuse に常時送られているかどうかは、リポジトリの docs と PR では確認できませんでした。AWS の事業計画の表に「CloudWatch + Langfuse-compatible tracing」とある([pals-startup-aws-activate-business-plan.md](../pals-startup-aws-activate-business-plan.md))のは計画の記述です。
- 台帳と Langfuse の関係(提案)。台帳は、評価のまとまりごとの**長く残す要約**です(成功率、失敗コード別の件数、費用、所要時間、出典)。Langfuse は**リクエスト単位のトレース**で、1回ごとの経路を調べる用途です。台帳の行から、必要なら同じ評価の Langfuse のトレースへたどれます。ただし台帳にトレースの ID は入れません(質問本文や利用者情報につながる値を残さないため)。
- 失敗コードは [taxonomy.md](taxonomy.md) と同じ語彙で、評価の書き出しと運用の監視([#217](https://github.com/AtsushiHosaka/pals/issues/217) の CloudWatch)に使えます。評価の実行時に自動で台帳へ追記する仕組みは、まだありません。既存の仕組み(JSONL の履歴から台帳の行を作る)に乗せるか、CloudWatch のメトリクスに出すかは、#216 と #217 で決めます。
