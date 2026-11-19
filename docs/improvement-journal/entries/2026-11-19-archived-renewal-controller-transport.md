# 退役後の履歴接続とcontroller転送上限への対応（2026-11-19）

復旧更新の開始時に、退役後の正規操作18件を履歴へ接続できず、host変更前で拒否した。元の正規sourceからの再導出と実provider結果の照合を追加した。未知操作の拒否と元の記録は維持する。

最終controllerを含む保存済み実packetのローカル測定では、両role形式を完全復元し、各61,247 byteで62,000 byte上限に収まった。固定bootstrapの別圧縮を採用し、hash・展開量・memory・EOF・余剰dataの検査を残した。これは転送の成立確認であり、所要時間や費用の改善率は測っていない。最終変更後の関連回帰36件は成功したが、製品回答数には数えない。

0699の正規実機更新は記録時点で実行中である。新しい実機health、UI反映、機能受入の結果は未取得。記録のための追加テスト・実測・有料生成は行っていない。

根拠は[経過記録](../../admitted-recovery-source-progress-2026-11-18.md)、[infra PR #219](https://github.com/AtsushiHosaka/pals-infra/pull/219)、品質台帳の`2026-11-19-archived-renewal-history-refusal`と`2026-11-19-archived-renewal-controller-transfer`である。
