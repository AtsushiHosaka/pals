# seq30の通知抑制作成の失敗（2026-11-16）

候補`b976afec`は、正規dry runの通過直後にapplyしたが、`alerts-begin`で停止した。quiesce、通信除外、admission、有効化、新しい本番質問の送信は実行していない。正規の終了結果は`failed`、`owner_released=true`、`cleanup_completed=true`、`alert_window_cleanup_completed=false`だった。本番受け入れは未達である。

親は`24d8f9574d732ce909c2c00198b9a6772d61d7e2`、infraは`ce084f345b3ebaa3fe15aee0a1519e6b0dceffaf`。最終planのSHA256は`33616a6aba4fcc13282eef07f9043775512a83864c293f1280ab4801faf51955`である。直前の[第4回ローカル資格確認](seq30-local-qualification-4-2026-11-16.md)はacceptedだったが、本番での成功とは区別する。

## AWSで確認した原因

CloudTrailを読み取りで取得し、非公開stateのルール名と完全一致するPutAlarmMuteRuleイベントを確認した。2026-11-16 07:25:39 UTCの要求はValidationExceptionで拒否され、理由は「ExpireDateは分単位の精度のみを受け付けるため、秒を含めない日時にすること」だった。生成値はStartDateが07:26:00Z、ExpireDateが07:50:38Zだった。AWSの拒否は、後者の秒精度に対応する。

保存した取得結果のSHA256は`8a005f9175503ed278d6ba05e7815152ab649c15a7e744036bdc774139ddd54c`である。監査の生データ、実行主体や内部識別子は公開しない。この拒否イベントはルール作成が成功しなかった根拠になるが、実サービスの他の入力条件まで適合したことは示さない。

正規helperのstateは`put_attempted`のままだった。なぜCLI側が明示的な拒否として分類できなかったかは、現時点では未確定である。controllerは子プロセスの出力hashを保存するが、今回のalerts CLIが出力する`reason`をjournalの拒否コードとして取り込んでいなかった。これも診断時の制約として残す。

## 後処理と時間

正規controllerによる所有権の解放とcleanupは完了した。同じ凍結済みcontract、hash、stateで正規cancelを追加実行したが、`incomplete / pending_put_absence_unconfirmed`だった。Getで不在でも、helper自身は未確定Putの不在を確定できない設計である。監査結果を使ってstateや正規結果を書き換えてはいない。

AWSに渡した固定期限は2026-11-16 16:50:38 JSTである。期限後の読戻しと実状態の確認は別に記録する。今回の正規結果を通知抑制のcleanup成功へ読み替えない。

正規`release-timing.py`では、alerts-beginが90.061秒、restore-checkが415.087秒だった。通信除外、quiesce、admission、activeな通知抑制の区間は存在せず、時間はnullである。nullを停止時間0秒の計測や15分以内の受け入れ成功として扱わない。失敗した工程はalerts-beginとalerts-cancelの2つだが、品質台帳では同じapplyの失敗1件として数える。新しい有料の本番質問は送信していない。

## 修正の範囲

新規作成と終了時の短縮で、ExpireDateを分単位に切り捨てる修正を進める。元のmax_secondsや凍結済みnot_afterを延長せず、残り時間が足りない場合は作成前に停止する。回帰テストと予行側の代用品にも、今回観測した分精度の制約を追加する。修正のレビュー、必須CI、予行、実サービスでの適用はそれぞれ別の根拠として扱う。
