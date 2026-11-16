# seq30の通知抑制作成失敗（2026-11-16）

親24d8f95・infra ce084f3・候補b976で、正規dry run通過直後にapplyした。alerts-beginで失敗し、quiesce・通信除外・admission・有効化は実行されなかった。1試行0成功として記録する。ローカル資格確認の成功とは別の試行である。

AWS監査記録の完全一致する要求は、ExpireDateに秒が含まれるためValidationExceptionで拒否されていた。正規controllerのowner解放とcleanupは完了したが、alerts-cancelはincompleteだった。元の結果と未確定stateを保持し、監査記録から手動で成功扱いにはしていない。

正規timingはalerts-begin 90.061秒、restore-check 415.087秒。停止区間は未開始でnullである。新しい有料本番質問は送信していない。費用の総額は測定していない。新規作成・終了時短縮の期限を分単位へ切り捨て、上限を延長しない修正と回帰テストを進める。

根拠と限界は[失敗の記録](../../seq30-alert-minute-precision-failure-2026-11-16.md)に残した。配備、受け入れ、時間短縮の改善はまだ示していない。
