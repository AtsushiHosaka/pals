# seq30通知期限修正後の7シナリオ予行（2026-11-16）

infraの統合commit3b31597で、正規run.shの7シナリオを順番に実行した。全7件の機能筋書きが成功し、各件の壁時計とmonotonic時間が600秒以内、所有resourceの回収も確認できた。

一式の壁時計は2548.159秒、monotonicは2548.146秒で、overall_600s=falseだった。全体10分の条件は未達で[#379](https://github.com/AtsushiHosaka/pals/issues/379)は未完了のままにする。個別の成功を全体時間条件や本番利用停止時間の成功へ換算しない。

代用品を使う機能検査bundle1件として品質台帳へ1/1を追加する。実cloud・host・ownerの動作や製品の本番受け入れ、数学の精度を示す測定ではない。新しい有料取得も行っていない。

各logと最終結果のhashをsummaryへ照合し、17ファイルを専用の非公開archiveへbytes一致で保存した。実行順、各時間、source・wrapper・indexのhashと限界は[予行記録](../../seq30-minute-rehearsal-2026-11-16.md)を参照。以前の実サービスの失敗結果は保持する。
