# seq30のrestore-check停止（2026-11-17）

正規dry runの通過後にapplyしましたが、利用停止前の`restore-check`で終了しました。結果はfailed、owner解放・cleanup・alert cleanupはいずれもtrue、alert overrunはfalseです。quiesce、通信除外、admission、通知抑制の開始、有効化、切り替え後の質問送信は実行していません。直前の[第5回ローカル資格確認](seq30-validation-recovery-2026-11-17.md)のacceptedとは別の失敗です。

実行sourceは親`3b663576036a5c3a9fe2ca092e8ccbf84b5f96a8`、infra`3b31597edda4d474700af9b55178ae20193b6001`、候補SHA256は`f20df8a4970b5a3ea98af712ca1663164b2dcd9e7119c8eae840bdb43ea89f46`です。凍結した最終planのSHA256は`c6d935f9d5e6095f14a042323d58e93dd111506ae1a205537017353623c00400`です。

## 確認した失敗と診断の限界

restore-checkは00:37:06.990461 UTCに開始し、00:39:43.462210 UTCに失敗しました。正規controllerの固定コードは`native_operation_failed:restore-check`です。既存SSM commandの結果を読み取ると、controlのnative guard確認はSuccess、compute inventoryもSuccessでしたが、control inventoryはFailed・returncode2で、`exact_native_current_tuple_unresolved`を返していました。

| 既存commandの読取結果 | SSM状態 | returncode | 言える範囲 |
|---|---|---:|---|
| controlのnative guard確認 | Success | 0 | guard確認。返却statusはnot_recoveredで、実際の復旧完了ではない |
| compute inventory | Success | 0 | 該当する読取commandは完了 |
| control inventory | Failed | 2 | exact native current tupleを確定できず拒否 |

このコードだけでは、どの入力や観測が合わなかったか、現在版が実際に不一致なのかまでは確定できません。根因は未確定です。静的な確認では、下位の診断を上位へ十分に残せない箇所が確認されており、診断の修正を進める予定です。修正や実再試行が成功したとは扱いません。凍結済みsource、state、元の失敗結果は保持しています。

## 終了と時間

`release-timing.py`の出力では、restore-checkが156.472秒、前後のadmission-status読取が97.150秒と93.299秒でした。通信除外、quiesceからadmission、activeな通知抑制の時間はnullです。工程を開始していないことと、実際の停止時間を0秒と計測したことは区別します。15分以内の本番受け入れ成功にも換算しません。

最終結果の`predecessor_restored=false`を、実復旧を試みて失敗した証拠とは扱いません。候補有効化や利用停止に進む前に終了しており、今回のrestore-check自体も実復旧の完了ではありません。alert cleanup=trueも、開始していない通知抑制の実作成・期限切れを検証したという意味ではありません。

00:44:02 UTCの事後正規観測は、ownerなし、application・databaseの変更なしを記録しています。これは失敗後の時点観測であり、本番質問の回答・保存・描画・履歴の受け入れではありません。新しい有料本番質問の送信は0件でした。

品質台帳には正規applyの技術bundle1件として0/1を追加します。根因が確定していないため分類はunclassified、rawには固定拒否コードを残します。複数の読取commandや失敗工程を別の製品・数学の試行へ加算せず、以前のローカル資格確認の費用も再計上しません。AWSなどを含む今回の費用総額は未測定です。

## 根拠のSHA256

| 記録 | SHA256 |
|---|---|
| 正規applyログ | `7546ce4121e15f78a26abd17b0f0daf865a5cac0b36a3dea539fcefaf80f24d8` |
| 正規timing | `df6f86e7761d394b933fe7158f1d6334d8758e919f604d07402e85dd6f073525` |
| 事後正規観測 | `9fbd021e3bc767551577aa12ab0aeda625bcc63cc3b535fe3448b2ab62736528` |
| control guard既存SSM読取 | `fb0026ba9453e3de0d5df796a4063ed9c1ad2315ff0a3ac7d04dc8568981cd3b` |
| compute inventory既存SSM読取 | `db1c5c1c432deed3de4f64eea62379eb438f59396a48cbe1b7317c6eacf4484d` |
| control inventory既存SSM読取 | `a92c117ccef1160abd9bec24b6a2c9bb2606f0db1644a0325832c76de64344ca` |

生のSSM結果、ログ、内部host・識別子・配置場所と資格情報は非公開です。次は拒否理由を切り分ける診断と回帰検査を行います。今回の失敗を後の修正結果で上書きせず、新しい実行にはsource checks、予行、資格確認の鮮度と正規controllerのgateを適用します。

診断欠落の修正は[#400](https://github.com/AtsushiHosaka/pals/issues/400)で追跡します。安全判定を変えず、固定phase・例外class・許可された原因codeだけを残す範囲で進めます。本番の下位原因が解消したとは扱いません。
