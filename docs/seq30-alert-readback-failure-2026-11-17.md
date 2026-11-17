# seq30の通知rule読戻し失敗（2026-11-17）

候補33447ab9の正規applyは、全体restore-checkを通過した後、通知抑制のalerts-beginで停止しました。直後のalerts-cancelも失敗しました。今回のcycle終端ではowner解放と通常cleanupは完了しましたが、alert cleanupは未完了で、固定期限を保持しています。quiesce、通信除外、admission、有効化、本番の新規質問には進んでいません。

sourceは親`5e53d4a33f2cac3b77af9f1db42872c82a0d66fe`、infra`3f9ade65eccd49453fa303b1954e47f7fe37aabf`、候補SHA256は`33447ab916651f741b4fa763f43e18528f051479cfb720dc43b0a10584005972`です。凍結planのhashは`09ffa4a149d2fb1f39f7b56dedca89f1858c19423da8a2dd8452c4dfa16af7fb`です。[第7回ローカル資格確認](seq30-local-qualification-7-2026-11-17.md)のacceptedや、その正規verify-existingを本番受け入れの成功へ換算しません。

## 通過した確認と失敗箇所

正規timingではrestore-checkが434.466秒でpassed、alerts-preflightも1.259秒でpassedでした。alerts-beginは2.086秒、cancelは0.601秒で失敗しています。最終結果はfailed、failureはnative_operation_failed:alerts-beginです。

主担当が既存ruleを実Getした保存応答はStatus=ACTIVE、MuteType=recurringでした。日時はStartDateが12:20:00+09:00、ExpireDateが12:44:00+09:00で、UTCでは03:20と03:44です。保存応答のhashを照合し、この表現と状態を確認しました。

[#404](https://github.com/AtsushiHosaka/pals/issues/404)では、正規読戻しが種別をRECURRINGに限定し、日時にもUTC表記を要求していたため、同一時刻を表すAWS CLIの応答をrule_identity_changedとして拒否したことを記録しています。固定したARN、対象、説明、Ruleと実時刻の照合は緩めません。入力契約のUTC条件を保ったまま、応答の有限enumとタイムゾーン付き日時の同一instantを正規化する修正を進めています。修正や解除の成功は、この失敗記録ではまだ主張しません。

## 終了時の境界

owner解放は03:25:03.673126 UTC、通常cleanupは03:25:05.904419 UTCに完了しました。cycle終端のowner_releasedとcleanup_completedはtrue、alert_window_cleanup_completedはfalse、overrunはfalseでした。元の結果とstateを保持し、同じcycleの再実行や成功への書換えは行っていません。

通知ruleの作成後の読戻しで止まったため、controllerのtimingでalert_windowがnullでも、AWS上にruleがなかったという意味ではありません。保存GetはACTIVEを示し、早期取消が未完了だった終端時点では03:44 UTCの固定ExpireDateを保持しています。後の早期取消や期限後確認は、別の実観測として記録する必要があります。固定期限を延長せず、他のalarmやforeign ruleを操作しません。ACTIVEという読戻しだけで、通知の配送や抑制の全経路を検証したとも扱いません。

通信除外とquiesce→admissionの時間もnullで、工程を開始していません。実際の利用停止時間を0秒と測定したとは書かず、15分以内の本番受け入れ成功にも数えません。通常cleanupの成功と、未完了の通知cleanupは別々に保持します。

## 計数と残る作業

正規applyの技術bundle1件を0/1として品質台帳へ追加します。beginとcancelの二つの失敗を別の製品試行にせず、通過したrestore-checkを今回のcycle成功とも扱いません。新しい有料本番質問は0件、ローカル資格確認の費用を再計上せず、AWSなどを含む総費用は未測定です。分類は通知応答を読む実装境界のinfra.app_defect、rawにはrule_identity_changedを残します。

修正後は新しいsource・署名・候補・namespaceで正規gateへ進みます。同じ実アプリ・subject・runnerで資格確認の有効期間内なら、#404に記録したとおり、正規verify-existingで既存の単一送信を再観測します。不要なpaid再送、期待値の緩和、照合の削除で進めません。

| 記録 | SHA256 |
|---|---|
| 正規applyログ | `efa743daf18c16b9f0bf78e12bd9ad769387539b2cdaccafa2f24675bf96609f` |
| 正規timing | `30d3b93b42b8e1dffee3b298c7f985dfcd6af2f988ab3fa79052ff3c8b508efa` |
| 既存ruleの実Get保存応答 | `9b64d306413f52e6b5f4ad89bc6e23329d72dadd5fe7f2af93942f08f357e4f2` |

生のprovider応答、ARN、rule名、内部識別子・配置場所と資格情報は非公開です。この記録は失敗したcycleの終端と上記保存応答までを対象とし、その後の通知解除や本番状態を先取りしません。
