# seq30の通知rule読戻し失敗（2026-11-17）

狙いは、正規restore-checkと通知windowを確認してから利用を止め、seq30を切り替えることだった。親5e53d4a3・infra3f9ade65・候補33447ab9の正規applyでrestore-checkは434.466秒、alerts-preflightは1.259秒でpassedになった。

alerts-beginは2.086秒で失敗し、直後のcancelも0.601秒で失敗した。保存GetはruleがACTIVE、種別recurring、オフセット付き日時で固定期限03:44 UTCを示していた。#404で応答表現の正規化不足を記録し、分類はinfra.app_defect、rawはrule_identity_changedとする。

判断は今回のcycleを0/1で停止し、同じcycleを再実行せず、通知の早期取消と読戻し境界の修正へ進むこと。owner解放と通常cleanupは完了したが、終端時のalert cleanupは未完了だった。利用停止前でquiesce・通信除外・admissionは未実行、timing nullを停止時間0秒の測定とはしない。後の解除成功もこの記録では未確認である。

新しいpaid本番質問は0、総費用は未測定。begin/cancelや通過工程を別の製品・数学の試行へ加算せず、第7回ローカルacceptedの費用も再計上しない。実結果、時刻、固定期限とhashは[失敗記録](../../seq30-alert-readback-failure-2026-11-17.md)、品質台帳IDは2026-11-17-seq30-alert-readback-failure。
