# seq30通知期限修正後の7シナリオ予行（2026-11-16）

infraの統合commit`3b31597edda4d474700af9b55178ae20193b6001`で、正規`sh tests/rehearsal/run.sh`の7シナリオを順番に実行しました。7件とも機能上の筋書きが成功し、各件の壁時計・monotonic時間は600秒以内でした。各件の所有するcontainer・image・network・volumeの回収も確認しています。

一式の所要時間は壁時計2548.159秒、monotonic2548.146秒でした。`overall_600s=false`で、全体10分の条件は満たしていません。[#379](https://github.com/AtsushiHosaka/pals/issues/379)は未完了のままです。今回の成功を、実ownerや本番切り替えの確認、利用停止時間の測定へ読み替えません。

## 実行順と時間

次の順序は、正規予行の宣言、実行wrapper、eventsの開始順、summaryの記録順が一致しています。

| シナリオ | 壁時計・秒 | monotonic・秒 | 結果 |
|---|---:|---:|---|
| success | 318.394 | 318.393 | 成功・回収確認 |
| fail-before-admit | 379.096 | 379.095 | 成功・回収確認 |
| fail-after-admit | 394.111 | 394.110 | 成功・回収確認 |
| crash-after-admit | 376.921 | 376.916 | 成功・回収確認 |
| expired-predecessor | 351.395 | 351.394 | 成功・回収確認 |
| expired-predecessor-fail-before-admit | 382.672 | 382.671 | 成功・回収確認 |
| recovery-units-active | 342.840 | 342.839 | 成功・回収確認 |

各logの最終結果は`rehearsal_passed`でした。保存したlogのhash、最終結果JSONのhash、run identityの確認結果をsummaryと照合しました。機能筋書きの失敗を成功へ書き換えたり、失敗した場合に残りを再試行したりした記録ではありません。

## sourceと証拠の保存

summaryは実行前後のsource検査を記録し、`source_still_clean=true`です。統合commitのtreeはレビュー済みtree`1af324ca59293976e31dd569eb761d1d056eeb8b`に一致しています。実行wrapperは正規run.shを呼ぶ計時・回収確認用で、別のrelease controllerを実装したものではありません。

| 記録 | SHA256 |
|---|---|
| 計時・回収確認wrapper | `1e2eb834088bb4a12cdf05666fb1259c82eabd85f04c576a1786afc8ef524a03` |
| 最終summary | `db287165ba480087fa43ac18beded8a30a146333d5dbfb937241a8732b78ad8b` |
| 非公開evidence index | `28601b3bd436f04c0644f3cb93fdd1e3831660baa22a324d5ce2fe75995dbbc0` |

非公開証拠の照会番号は`SEQ30-MINUTE-REHEARSAL-20261116`です。7 logs、7 run IDファイル、events、summary、実行wrapperの計17ファイルをbytes一致で専用archiveへ保存しました。ディレクトリは0700、各ファイルとindexは0600です。rawログ・配置場所・識別子は公開リポジトリへ追加しません。このarchiveは記録の保管用で、release gateへPASSや受領書として取り込むものではありません。

## 確認できた範囲

この予行ではcloud、host、製品とownerの動作をローカルの代用品で検査しています。実サービスの通知抑制作成、実ownerの復旧、DB・Lean・providerを通す本番回答、認証、保存、描画、履歴や再読み込みの受け入れは証明していません。新しい有料取得は実行していません。

品質台帳には、機能上の7シナリオをまとめた技術検査bundle1件として1/1を追加します。7件を独立した数学の試行へ加算せず、全体10分条件の成功率にも使いません。過去の通知抑制作成失敗と、その未完了結果は保持します。実candidateの新規生成や第5回有料ローカル資格確認の承認は別の手順です。
