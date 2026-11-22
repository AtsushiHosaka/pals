# seq30診断修正の検査選別（2026-11-17）

## 判定と契約上の根拠

[infra PR #183](https://github.com/AtsushiHosaka/pals-infra/pull/183)の変更については、既存の7シナリオを一律に再実行せず、不変な操作・復旧手順の証拠を継承します。変更した診断境界は、新しいsourceの単体テスト、host harness、E2Eと必須CIで検証します。

[共有契約](release-reliability-policy.md)28行は、変更した動作と依存境界に応じて検査を選び、無関係な重い検査を機械的に繰り返さないよう定めています。40行も、実行コードの変更時に求めるのは影響範囲の再検証です。全変更で7シナリオを再実行するという条項はありません。25行の、実際の配備と同じレビュー済みdriver・操作順を検証する要件は維持します。

## 比較したsourceと変更境界

比較元は`3b31597edda4d474700af9b55178ae20193b6001`、比較先はmerge commit `3f9ade65eccd49453fa303b1954e47f7fe37aabf`です。比較先のtreeはレビュー済みhead `e4adbff`と同一です。

```text
tree: 597f8f64679347d3a8af1771a9bb5fb8c451cfbc
```

Gitの差分を比較し、次のファイル・ディレクトリの実bytesが不変であることを確認しました。

- `scripts/release-cycle.py`、`scripts/release-step.py`
- `host/private-runtime/release_alert_window.py`
- `host/private-runtime/native_safety_restore.py`
- `host/private-runtime/release_native/`（drain・activation・owner・復旧などの生成元）
- `tests/rehearsal/`（7シナリオの実行スクリプトとharness）

変更した既存native 3ファイルは、拒否理由を固定されたphase・code・例外分類として伝えるための修正です。元のguard、observerのfallback順、操作順、復旧判断は維持しています。追加した共有importと診断JSONの境界は、既存host safety 57件、新しい単体テスト、必須CIのhost harness・E2Eで確認します。旧probeを直接呼ぶ新CLIは読み取り専用で、診断結果をreleaseのPASSへ変換しません。workflowの変更はテスト登録と重複実行の集約です。

## 継承する証拠と残る条件

`3b31597`で実行した7シナリオは、機能上すべてPASSでした。この結果を`3f9ade65`で再実測したとは扱いません。全体所要時間は2,548.159秒で、10分以内という条件は未達です。[#379](https://github.com/AtsushiHosaka/pals/issues/379)の未達を残します。

レビュー済みheadの必須4検査は成功しています。merge commitのCI run `44001276427`は、この文書の作成時点では完了待ちです。新sourceの必須検査は、正確なmerge commitと最新の正規workflow結果で確認します。未完了やキャンセルを成功として継承しません。

過去の`exact_native_current_tuple_unresolved`の根因は未特定です。後の読み取り専用probeが完了しても、当時の失敗原因が解消された証明にはなりません。新sourceを凍結した正規のfreshなstrict restore-checkを通過しない限り、切り替えを進めません。

新しい資格確認capture、署名、最終固定、dry runと直後のapplyも省略しません。署名前には、永続的な正規source checkoutで親revisionと6 submoduleの正確な参照・初期化・clean状態を確認します。今回の未初期化の親作業場所はPR提案に限って使います。

この選別は今回の差分に限る判断です。実行コード、操作、source、設定や依存境界をさらに変える場合は、必要な検査を再評価します。新しい測定結果や本番受け入れを示す文書ではないため、評価件数は追加しません。
