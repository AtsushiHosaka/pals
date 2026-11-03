# Proof Quality Observability Tasks

Status: WORKING; 全タスクは未着手。この文書は [requirements](requirements.md) と [design](design.md) を作業に対応づける。仕様の承認、`terraform apply`、本番配備は、いずれもこの文書のタスクとして自動では承認されない。

担当の提案: `claude`（Claude）、`codex`（Codex）、`owner`（オーナー）。着手前に、GitHub の Issue で重複を確認する（AGENTS.md）。`pals-infra`、`pals-agent`、`pals-api` の変更は、それぞれのリポジトリの別 PR とする。

## Implementation order

| ID | Task | Requirements | Acceptance | 担当 | 承認 |
|---|---|---|---|---|---|
| PQO-T001 | 仕様をオーナーが承認する。[design.md の Open questions](design.md#open-questions) のうち、1（dot の資格情報）、5（読む内容）、8（アラームの動作）、9（ホストの置き換え）、13（運び方）に答える。 | 全体 | 回答が `type:decision` の Issue か Discussion に、日付つきで残っている | owner | 承認 |
| PQO-T002 | #216 の `taxonomy.md` が main に入った時点で、design の暫定分類を合わせる。未マージなら、暫定分類のまま進め、差分を #216 に書く。 | PQO-001、PQO-004 | design の対応表が `taxonomy.md` の識別子と一致するか、差分が #216 に記録されている | claude | |
| PQO-T003 | pals-agent に `quality_events` モジュールを足す。EMF の組み立て、許可リスト、禁止項目の検査、運び方の抽象（エージェント、ファイル、無効）、分類の対応表、スキーマ（JSON Schema）を持つ。既定の運び方は無効とする。 | PQO-001、PQO-003–PQO-005、PQO-007–PQO-009 | 単体テスト: 語彙の全コードが対応し、未対応は `unclassified`、許可リスト外は `unrecognized`、質問・Lean ソース・利用者識別子のダミー文字列がイベントに出ない、発行失敗で例外を出さず `QualityEventsDropped` が増える | claude | |
| PQO-T004 | pals-agent のフックを足す: 要求の終端（`settle_proof_request` が受理された後）、Lean の試行（検証器側を含む）、ワーカーのハートビート。 | PQO-002、PQO-003、PQO-006、PQO-009、PQO-014 | 単体・統合テスト: 終端1回につきイベント1件、再配信（`terminal` の分岐）では0件、`verifying` では `ProofRequestsSettled` を出さない、`policy_refusal` が分母に入らない | claude | |
| PQO-T005 | pals-api のフックを足す: Lean ジョブの終端（`proof_request_lean.py` の遷移）、ゲストの拒否。同じイベントのスキーマを使う。 | PQO-002、PQO-003、PQO-006 | 実 PostgreSQL の統合テスト: 遷移したときだけ1件、`return False` の経路で0件、失敗コードを `failure_code` と最後の診断コードから分類する | claude | |
| PQO-T006 | 運び方の確認（使い捨て）。使い捨てのロググループと、`Environment=probe` のイベントで、T1（エージェントの EMF 受信口）、T2（ファイル）の EMF 抽出を確かめ、運び方を確定する。 | PQO-010、PQO-003 | 抽出されたメトリクスが `ListMetrics` に現れる実測を、docs に記録する。使い捨てのリソースは削除する | claude | **AWS への書き込み: オーナー承認** |
| PQO-T007 | 評価の実行のイベントを足す。#216 の台帳への追記関数から `eval_run` を出す。 | PQO-017、PQO-018 | 単体テスト: 追記と発行が同じ関数からであり、台帳の行 ID が入る。評価を2回行うとイベントが2件 | claude（#216 と調整） | |
| PQO-T008 | pals-infra に、ロググループ、ホストの `logs` 権限、変数を足す。ホストの user data は、PQO-T006 の結果に基づく変更を、別のコミットに分ける。 | PQO-010、PQO-022、PQO-025 | `terraform validate` と `terraform test` が通る。新しい `run` で、ワーカーのロールが不変、ホストの `logs:*` が専用ロググループに限られることを検査する。`plan` が新規作成だけを示す | claude | |
| PQO-T009 | pals-infra に、アラーム9本（`alarm_actions` は空）を足す。 | PQO-011–PQO-016 | `terraform test`: 比較・しきい値・評価期間・欠測の扱いが design の表と一致し、`alarm_actions` が空である | claude | |
| PQO-T010 | 読む経路を確かめる。(a) CloudWatch を読める既存の ChatGPT プラグインがあるか、あれば権限を行為単位で読み取りに絞れるか。dot の資格情報の保存、失効時の挙動、監査の可否も調べる。 | PQO-019、PQO-020 | 確認した事実と出典を docs に記録する。結論として (a)(b)(c) のどれを採るかを、オーナーに示す | claude（調査）/ owner（dot の画面での確認） | |
| PQO-T011 | pals-infra に、読み取りの権限を足す。選んだ経路が (b) なら、読み取りポリシーと、変数で与える主体のロール。`observability_reader_principal_arns` が空なら何も作らない。 | PQO-019 | `terraform test`: 許可が design の一覧と一致し、書き込み、S3、SSM、DB、KMS、IAM を含まない。空の変数ではロールが作られない | claude | 主体の指定: owner |
| PQO-T012 | pals-infra に、ダッシュボード `pals-<env>-proof-quality` を足す。 | PQO-021、PQO-018 | `terraform validate` とウィジェットの JSON の検証。メトリクスが50以下 | claude | |
| PQO-T013 | 運用手順を書く: メトリクスの取得、Logs Insights のクエリ、ダッシュボードの見方、縮小手順、dot の未確認事項。 | PQO-020、PQO-023 | 手順内の全クエリが、読み取りの権限で成功する（PQO-T016 で確認） | claude | |
| PQO-T014 | **`terraform apply`**（`pals-infra`）。`plan` をオーナーが確認する。 | PQO-022 | `plan` が新規作成だけを示し、既存の変更・破壊を含まない。適用後の `plan` が差分なし | owner が承認、claude が実行を支援 | **オーナー承認が必須** |
| PQO-T015 | **本番配備**: アプリの新しい版（発行は有効）と、ホストの置き換え（エージェント導入）。 | PQO-010、PQO-022 | ヘルスチェックが通る。ハートビートのメトリクスが現れる。配備の記録を docs に残す | owner が承認、claude が手順を用意 | **オーナー承認が必須。ホストの置き換えを伴う** |
| PQO-T016 | 擬似失敗の注入と受け入れ。分類ごとに `Environment=probe` で1件ずつ発行し、アラームは一時アラームで検証し、読み取りの権限でクエリを実行する。 | PQO-024、requirements の受け入れ条件の全項目 | 各条件の実測を docs に記録する。一時リソースは削除する。本番のアラームが誤って `ALARM` にならない | claude | owner の確認 |
| PQO-T017 | 14日分の実測で、率のアラームのしきい値と最小サンプル数を見直す。月の実測費用を、見積もりと比べる。 | PQO-013、PQO-023 | 見直したしきい値と根拠、実測費用を docs に記録する。費用が上限（約44 USD）を超えるなら、縮小手順を実行する | claude | しきい値の変更: owner |

## Completion gate

- 仕様がオーナーに承認されている（PQO-T001）。
- 失敗の種別ごとのメトリクスが、本番の CloudWatch に出ている実測の記録がある（PQO-T016）。
- アラームとダッシュボードが、Terraform で管理されている（PQO-T009、PQO-T012、PQO-T014）。
- 外部の読み取り機能が、CloudWatch を読める権限と手順が書かれており、dot 側の未確認事項が、確認済みか、残る理由つきで記録されている（PQO-T010、PQO-T011、PQO-T013）。
