# seq30の初回admission-status失敗（2026-11-17）

候補085d9d03の正規applyは、利用を止める前の初回admission-statusで停止しました。cleanup中のadmission-status再確認はpassedとなり、owner解放とcleanupは完了しました。後の確認の成功で、最初の失敗を成功へ書き換えません。quiesce、通信除外、通知windowの開始、admission、有効化、本番の新規質問には進んでいません。

実行元は親`f00e5fae0088f7cc2c4caaf66bbec51d9eeb2941`・infra`847d515f4fd699e106ec4fe41647d72b14e255d3`、候補は`085d9d03cca2d4ec50d71d4761d1fcdad07315d90bea5d1808c62f3a92876795`です。凍結planのSHA256は`5c2cf83a04443e8b30b9fdc0e3071a44ec41ac49ce3b414f3bbea2d3dacce478`です。

## 実結果と終了時の境界

初回admission-statusは04:26:42.477403から04:27:39.867801 UTCまでの57.390秒でfailedでした。cycleのfailureはnative_operation_failed:admission-status、保存されたcontrol応答のcodeはexact_native_current_tuple_unresolvedです。続くcleanup経路の再確認は04:27:39.877121から04:29:21.611303 UTCまでの101.734秒でpassedでした。これは新しいapplyや新規の製品試行ではありません。

owner解放は04:29:34.658929 UTC、cleanupは04:29:36.694115 UTCに完了しました。終端はfailed、owner_released・cleanup_completed・alert_window_cleanup_completedはtrue、alert_window_overrunはfalseです。通知windowを開始していないため、alert cleanup=trueを新しい通知ruleの作成・取消成功とは扱いません。利用停止工程は未開始であり、停止時間0秒を実測したという主張もしません。

## 保存診断で分かった範囲

主担当が既存SSM commandを読み取った3件の保存応答は、DBとcomputeがSuccess、controlがFailed・終了コード2でした。controlの閉じた診断はInventoryFailureで、predecessorのcontext読み取りにFileNotFoundErrorが記録されています。実際に不足していたファイル名と根因は、この記録時点では未確定です。raw応答や内部識別子は公開しません。

[#407](https://github.com/AtsushiHosaka/pals/issues/407)では、資格brokerが排他lock内でstateを削除してからSTS取得・復元を行う一方、readerがそのlockを使わない競合を候補として調べています。これはsourceを読んだ仮説で、今回の実失敗や以前の候補f20の根因が確定したという意味ではありません。ローカル再現と修正後の検証を待ち、稼働中のsourceや凍結planを変更して進めません。

## 計数と判断

今回の正規applyを技術bundle1件の0/1として記録し、根因未確定のため分類はunclassified、rawにはexact_native_current_tuple_unresolvedを残します。admission-statusの再確認や通過工程を別の分母へ加えません。数学・モデルの失敗率にも換算しません。

既存の第7回ローカル資格確認は、同じ単一送信を正規verify-existingで再観測しました。今回の新しい有料送信は0件で、過去の取得費用も重複計上しません。本番で新しい質問は送っておらず、AWSなどを含む総費用は未測定です。

判断はリリースを停止し、#407の再現・診断を進めることです。候補はacceptedではありません。本番の終端回答・保存・描画・reloadは未検証のままです。

| 保存根拠 | SHA256 |
|---|---|
| 正規applyログ | `db01d369432eadd46ef52fa85045191bb25b22d25047e4c5defd47a0c486c7b3` |
| 既存DB commandの読取応答 | `d6cf2ea5f72210afc6865b6a4fd7b281b261cb72614334552955bfe6c6b4a050` |
| 既存compute commandの読取応答 | `7ded4572801cce7f2e81b5fa24ece4b63ffdedd6827c00dca2b699aad022dd19` |
| 既存control commandの読取応答 | `c0ca220b8a0fa0ed585964eff55747897e053ee3a99211e78d33453f3eaf54fa` |

生の記録は主担当の非公開release archiveに保持します。資格情報、内部ホスト・command識別子、質問・回答・Lean本文は公開文書へ転載しません。
