# 完走性メトリクスの状態契約の修正

担当はCodex、[担当チャット](codex://threads/01a1a6ef-927b-7d72-b689-5c442ada7af7)。進行は[#217](https://github.com/AtsushiHosaka/pals/issues/217)、元の指摘は[PR#292のP2](https://github.com/AtsushiHosaka/pals/pull/292#discussion_r4488747241)で追う。基準は親 `32a70d5d1ad524b8b800de98c86f63292c912d45`。今回の依頼は有限の状態、メトリクス、アラームの契約修正とAPI・infraへの反映であり、本番操作を含まない。

## 修正した矛盾

PQO-005の許可リストには状態がなく、PQO-027/029は状態別ゲージと期限を要求していた。D4にも名前・単位・系列の定義がなかったため、APIが発行する系列とinfraが選択する系列を一致させられなかった。

`State` を `accepted`、`queued`、`verifying`、`explaining`、`awaiting_application` に限定した。新5メトリクスの単位と正確なディメンションの組をD4と機械可読な `completion-metrics.v1.json` へ定義し、T018/T019の検証条件にも対応付けた。契約ファイルのSHA-256は `2c634ef5b821265065affbaf35f33dbb354ca868333bff492b076de6671b12d9`。

状態を持つ在中2系列と、Environmentだけを持つ受付・未適用の3系列を分ける。未知状態を第6の系列へ変換しない。5状態を全て観測できた正常な0件と、集計失敗・欠測を区別し、受付からの経過秒数を状態遷移でリセットしない。監視状態はDB列の値とは別であり、具体的なDB対応・集計はT018に残す。

D11で状態別5個・未適用ジョブ1個のアラーム選択を固定した。単位Seconds、Maximum、300秒、1-of-1、暫定900秒超、欠測breachingで、追加分は既定無効とする。既存9アラームと旧イベントv1は保持する。

約1,522秒のUI観測を非終端DB状態の証拠とする断定も訂正した。単一環境の追加13系列と6アラームにより、従来の費用表をそのまま新構成の見積もりとして使えない。新見積もりと運用受入まで有効化しない。

## 親の検証

Pythonの標準ライブラリだけで、次を実行した。

```text
python3 pals-scripts/validate-proof-quality-completion-contract.py
python3 -m unittest discover -s pals-scripts/tests -p test_proof_quality_completion_contract.py -v
git diff --check
```

契約と仕様の整合はエラー0、専用5件は成功した。元のState許可の欠落、Routeへの置換、単位の相違・メトリクスの欠落、子コピーのbyte差を拒否する回帰を含む。これは仕様の整合検査であり、CloudWatchの抽出・アラーム遷移やDB集計の試験ではない。独立した仕様レビューでも、この契約範囲に未解決P0〜P2はなかった。

日本語の静的検査と意味の差分を確認した。旧文書の表形式・既存表現に関するnoticeは残し、今回の契約と関係のない文章は一括修正しない。単体・仕様検査件数は数学の精度台帳へ追記しない。

## API・infraと残る受入

APIは旧schemaを緩めず、別の版付き完走性契約とbuilder・送信入口を追加する。infraは同じ契約から、既定無効の6アラームを用意する。対応PRと固定head、独立レビュー・統合結果は確認後に追記する。

実DB集計、受付commit後の接続、5状態への排他的な割当、定期実行、collectorと新イベントの実収集、CloudWatchの実ALARM遷移は未検証である。T018全体と#217は完了扱いにしない。モデル呼出し、本番計測、DB操作、AWS/IAM変更、署名、image build・配備は今回行わない。
