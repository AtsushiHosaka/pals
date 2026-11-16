# seq30の3回目のローカル資格確認（2026-11-16）

- 指標: 正規ローカル資格確認の受け入れと費用。性能改善や数学全般の精度は測定していない。
- 仮説: 実依存先と認証を確認した固定候補・sourceで、実モデルからLean・説明・保存・表示までの受け入れ条件を満たせるか確かめる。
- 変更: 親24d8f95・infra ce084f3・候補b976を使用。モデル、oracle、審査flag、成功条件を変えず、正規captureを1回実行した。
- 測定の条件: local macOS、有料資格確認全体n=1。実PostgreSQL・Lean・providerを使用。provider8 callsは試行数へ加算しない。
- 結果: 0/1、review.rejected。実compile・attestation結合はtrueだが、同じLeanに対する意味審査がrejected。修復0回/上限6回。APIの汎用lean_verification_failedを受け、受け入れは停止した。
- 時間: 正規処理全体の壁時計118.602秒。課金前compiler canary2429ms、生成物の保存検証時間3823msは別の区間で、回答時間の指標にはしない。
- 費用: proxy台帳の差分は8 calls・0.039882 USD。実請求額ではない。合計60 calls・220786/700000 μUSD、全calls completed、blocked=false。resetや新rolloverはしていない。
- 判断: 候補は未有効化、本番seq29を維持。最終freeze・dry run・cycleを行わず、再送もしない。承認済み3回を使い切ったため、4回目の有料取得は別途判断が必要。
- 限界・未確認: 生の意味審査理由や証明の正しさは独立審査していない。審査の誤判定やruntime故障は断定しない。終端に投影された意味審査errorとcompiler errorを区別し、元compiler診断の独立保存数は未確認とする。
- 次にやること: 限定forensic証拠v2と今回の失敗を提示し、追加取得の条件を審査可能にする。期待値を変えて失敗を消さない。
- 出典: [資格確認3の実測](../../seq30-local-qualification-3-2026-11-16.md)、品質台帳 `2026-11-16-seq30-local-qualification-3`、[pals#378](https://github.com/AtsushiHosaka/pals/issues/378)。安全な証拠hashとsource上の境界は実測記録を参照。

条件補足: 実requestでは証明生成`gpt-6.1-terra / medium`、出力`en`、単一証明問題n=1で、カード数は該当しない。固定workerの意味審査・説明は`gpt-6-luna / low`。修復上限6と実使用0は第3回の保存記録の値である。個別callのrole/effort記録はない。実request hashと固定実装の出典を詳細記録へ追記し、既存の失敗・費用・試行数を維持した。
