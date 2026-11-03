# ledger.csv のスキーマ

1行が1回の測定(同じ構成と題材の実行のまとまり)です。UTF-8、カンマ区切り、LF 改行、1行目が見出しです。不明なセルは空にします。推測や換算で埋めません。

| 列 | 型 | 内容 |
|---|---|---|
| `id` | 文字列 | 行の識別子。一意。`<日付>-<実験の短い名前>` を基本にする |
| `date` | `YYYY-MM-DD` | 実行日。出典に実行日がないときは出典の日付(PR のマージ日、docs の日付)を使い、`notes` に書く |
| `family` | 列挙 | 実験の系統。`answer_latency` / `recipe_retrieval` / `exact_precheck` / `statement_index` / `lean_runtime` / `proof_generation` / `guest_quality` / `catalog_audit` / `load_test` / `feature_audit` / `availability` / `other` |
| `experiment` | 文字列 | 実験の短い名前 |
| `model_config` | 文字列 | モデルと推論量(例: `Luna low`、`Terra medium`)。モデルを使わない測定は空 |
| `dataset` | 文字列 | 題材(カード集合、質問集合、テスト集合)の名前と大きさ |
| `n` | 整数 | 試行または項目の数 |
| `successes` | 整数 | 成功の数。`success_rate` の定義と同じ数え方にする |
| `success_rate` | 0〜1 | 出典に書かれた率、または `successes / n`。再現率や Hit@k など別の指標の率は、定義を `notes` に書く |
| `failures_json` | JSON | `{"<失敗コード>": 件数}`。コードは [taxonomy.md](taxonomy.md) のものだけを使う。失敗がなければ空 |
| `failures_raw_json` | JSON | 出典の失敗の文字列と件数。分類の根拠を残す |
| `cost_usd` | 数値 | 測定した費用(米ドル)。版付き単価で出した推計は `notes` に「推計」と書く。請求額とは限らない |
| `latency_p50_s` | 数値(秒) | 中央値。出典に書かれているものだけ |
| `latency_p95_s` | 数値(秒) | p95。出典に書かれているものだけ。5 件の最大値などは入れない |
| `latency_other` | 文字列 | 平均、最大、区間ごとの内訳など、上の2列に入らない所要時間 |
| `environment` | 列挙 | `local macOS` / `AWS` / `CI` / `other`。出典に書かれているものだけ。`other` は公開サイトや旧ホストなど、前の3つに当てはまらない環境 |
| `source` | 文字列 | 根拠。`;` 区切りで複数可。docs は `docs/<ファイル>.md@<コミット>`、PR と Issue は URL |
| `source_type` | 列挙 | `doc` / `spec` / `pr_pals` / `pr_agent` / `issue` |
| `overlap_with` | 文字列 | この行が他の行の合計や一部を含むとき、その行の `id` を `;` 区切りで書く。通常は空 |
| `notes` | 文字列 | 200 字程度まで。日付の由来、比較できない理由、推計かどうか |

## 規則

- 同じ測定が docs と PR に書かれているときは1行にし、`source` に両方を書きます。
- 合計の行(例: 3つの実行の合算)は、内訳の行がある場合だけ `overlap_with` を付けて残します。成功率と失敗の集計では除外し、費用のグラフでは白抜きで示します。
- 合計の行どうし、または合計の行と内訳の行を足してはいけません。
- 単体テストや CI の通過件数は、評価ではないので入れません。
- 計画や予算の費用は入れません。測定した費用だけを入れます。
- `make_charts.py` は実行のたびに、列挙の値、失敗コード、`successes <= n`、`overlap_with` の参照先を検査します。問題があれば止まります。
