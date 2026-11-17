# seq30のrestore-check停止（2026-11-17）

狙いは、利用停止前に正規nativeの復旧前提を確認したうえで、候補f20を切り替えることだった。親3b663576・infra3b31597の凍結sourceで、正規dry run通過直後にapplyした。

restore-checkが156.472秒で失敗し、既存commandの読取ではcontrol inventoryがexact_native_current_tuple_unresolved・returncode2だった。control guardとcompute inventoryのcommandはSuccess。根因は未確定で、unclassifiedとする。quiesce・通信除外・admission・alerts-begin・有効化・post質問送信は未実行だった。

判断は、今回のapplyを技術bundle1件の0/1として停止し、診断の不足を修正して追加検証へ進むことである。owner解放・cleanup・alert cleanupは完了し、事後観測もownerなし・app/DB変更なしを示す。利用停止区間のtimingはnullで、停止時間0秒の実測や15分以内の受け入れ成功ではない。

新規有料本番質問は0件、費用総額は未測定。第5回ローカル取得のacceptedと費用は別記録のまま保持し、読取command数を製品・数学の試行へ加算しない。実復旧や本番受け入れは完了していない。実測とhashは[失敗記録](../../seq30-restore-check-failure-2026-11-17.md)、品質台帳IDは2026-11-17-seq30-restore-check-failure。

仮説に当たる見通しは、正規の復旧確認を利用停止前に行えば、復旧の前提を満たさない候補を安全に止められる、というものだった。これは実施後の説明であり、今回の下位原因を推定したものではない。
