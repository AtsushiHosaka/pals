# 検証済み回答の反映をキュー送信から分離する（2026-11-17）

- 指標: 時間。送信待ちが検証済み回答の反映を妨げる経路を減らす。
- 仮説: 要求の送信、linked jobの送信、完了結果の反映を独立したタスクにすると、キュー送信が遅延・失敗しても反映を続けられる。
- 変更: [API PR #118](https://github.com/AtsushiHosaka/pals-api/pull/118)。基点は承認済みAPIブランチの`08cf8acc6f6ea9059445bdd4e82e5c160e99cc5f`、候補は`c999de02ab3333d4c08cd7eccb2e64c68f238034`。3タスクの通知・待機を分離し、各recover呼び出しの送信を最大4並列にした。既存のDB claim・token・lease、曖昧な送信の再試行、終了時のcancel・awaitを維持する。新規フラグはなく、統合・配備後は対象経路に適用される。記録時点で本番への適用は確認していない。
- 測定の条件: 2026-11-17、macOS Apple Silicon、Python 3.12.13、uv.lockに一致する専用venv、FastAPI 0.140.2。モデル・推論量・修復上限・カード数は対象外で、モデル呼び出しはない。最終技術検証はunit77件と実PostgreSQL9件を同じ実行にまとめた1回。実DBは既存ローカル検証用クラスタ内の専用一時DBを使い、正規migration chainを適用した。

## 結果

| 確認対象 | 条件 | 観測した結果 | 時間・性能の扱い |
|---|---|---|---|
| 旧ソースのスケジューリング回帰 | 基点08cf8acへ新規回帰4件を適用 | 4件失敗。送信待ちによる反映停止、片側の失敗によるループ停止、直列送信を検出 | 回帰検出であり、p95の測定ではない |
| 初期の実DB検証 | 古いlean-flow fixtureを利用 | 2件失敗を3回観測。モデル未対応、generation settings未導入、修正途中のNone値validation errorを保持 | fixtureの失敗。正規migration chainへ修正後に再実行 |
| 修正後の最終技術検証 | locked環境、unit77件＋実PostgreSQL9件 | 86件成功、失敗0・error0・skip0。ruffと対象2sourceのmypyも成功 | suite所要20.738秒。利用者の回答時間ではない |
| 候補のself-hosted CI | 同一head c999de0、push・PRの2run | `api-regression`は両runで成功 | 性能改善の測定ではない |
| 20秒送信遅延時の反映p95 | Issue #111の性能条件 | 未測定。増加1秒未満という条件は未確認 | 性能改善は未立証 |

単体・統合テストの件数は、製品や数学の成功率へ換算しない。実PostgreSQLの新規3件は、送信待ち中の完了結果の反映、request claim、job tokenによる競合送信の拒否を確認した。残る6件は既存の結論保存回帰である。完了jobはfixtureで準備し、queueは制御したテスト境界を使った。実SQS・Lean・モデル・認証・本番画面を通した成功を示すものではない。

判断は追加測定とする。送信待ちと反映の分離、および実DBの反映・競合防止は対象検査で確認したが、比較可能なbefore/afterの反映p95がなく、速度向上やIssue完了を宣言する根拠には足りない。既存の失敗を後続の成功で消さず、本番の受け入れも別に確認する。

費用は、新しい有料モデル呼び出しなし。本試行による総費用や削減額は未測定。新規コンテナやAWS設定変更はなく、一時DBはfixtureが削除した。次は20秒遅延条件でbefore/afterを同条件測定し、反映p95の増分を確認する。この追記では測定を実行せず、品質台帳の製品評価分母も追加しない。

## 出典

- [API #111](https://github.com/AtsushiHosaka/pals-api/issues/111)、[親 #380](https://github.com/AtsushiHosaka/pals/issues/380)、[API PR #118](https://github.com/AtsushiHosaka/pals-api/pull/118)
- [親の作業記録](../../issue-progress-and-ingress-2026-11-17.md)、API候補内の`docs/engineering-notes/dispatch-apply-isolation-20261117.md`
- [push run 44040433240](https://github.com/AtsushiHosaka/pals-api/actions/runs/44040433240)、[PR run 44040444397](https://github.com/AtsushiHosaka/pals-api/actions/runs/44040444397)
- ローカル証跡は`/private/tmp/pals-api111-red.log`、`/private/tmp/pals-api111-locked.xml`。一時ファイルは永続保存を保証しないため、確認結果と条件は上記の版管理された記録にも残した。
