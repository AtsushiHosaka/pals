# 品質アラームと送信値の不一致の修正

親Issueは[pals#217](https://github.com/AtsushiHosaka/pals/issues/217)。infraの基点は`52a1ced3c33fc43310ec1b53f25ae570e3a434fb`、確認した送信コードはpals-agentのマージコミット`e77931405f02efe416e09b3723de44e81cc860e7`です。作業は本番へ適用していません。

送信側は失敗分類に`model`と`review`を使いますが、Terraformの率アラームと成功率パネルは`proof`と`review_rejected`を参照していました。実際の失敗数を拾えず、成功率の分母も欠けます。参照する値を送信側に合わせました。既存のアラーム名・Terraformのキー・しきい値・最小サンプル数は維持しています。

また、送信側の`verifier`分類には通常のLeanコンパイル失敗も含まれます。分類全体を基盤異常として扱わず、`verifier.trusted_audit_failed`と`verifier.runtime_unavailable`の固定コードだけを検証器の重大イベントとして数えます。Lean試行の失敗メトリクスにはコード別dimensionがないため、専用ログのJSONフィールドをmetric filterで選びます。対象は`lean_attempt`と`proof_request_terminal`で、Environmentを持つイベントだけです。

このメトリクスは重大イベントの有無を見るためのものです。試行と終端やログの再配信が同じ原因を複数回表すことがあるため、一意な失敗件数や失敗率の分母には使いません。[AWSの説明](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/MonitoringLogData.html)にも、metric filterの配信が重複する場合があると記載されています。

## 確認した範囲

Terraform 1.13.5の公式アーカイブをSHA-256一覧と照合し、一時領域で使いました。既存のAWS provider 5.100.0を使い回し、remote backendを初期化せずに実行しています。

| 確認 | 結果と範囲 |
|---|---|
| `terraform validate` | 通過。構文とprovider schemaの検証 |
| `terraform test -filter=tests/quality_monitoring.tftest.hcl` | 17件通過。既存のmock providerによるローカルplan検査で、実AWSのplanではない |
| CloudWatch `TestMetricFilter` | 8例のうち重大イベント3例だけ一致。通常のコンパイル失敗、命題不一致、モデル失敗、別イベント、Environment欠落は一致しない |
| Terraformの整形と静的契約 | 実行結果はPR本文に記録 |

フィルタ検査に使った本文を含まない8例は`tests/fixtures/quality-events/critical-verifier-cases.json`に保存しました。`critical`は検査の期待値で、実際のログフィールドではありません。TestMetricFilterへ送ったのは`message`だけです。実ログや利用者の質問は使っていません。

最初のTerraform起動はローカルproviderプロセスのsandbox制限で失敗し、同じコマンドを必要な権限で再実行しました。途中のassertionは変更前のmetric名とdimensionを期待していたため、新しい契約へ更新しました。しきい値、通知先、既存アラーム数を緩める変更はありません。

## 未確認

ロググループやmetric filterの作成、アプリからの送信、実メトリクスの抽出、アラーム遷移は未確認です。AWSへの変更やログ投入、通知、ホスト交換は行っていません。CloudWatchのAPIを呼んだのは、ログを保存せずパターンを検査するTestMetricFilterだけです。

アプリのAPI終端フック、ハートビート、ホスト受信経路は別の未了部分です。この修正だけで品質監視が稼働したとは扱いません。
