# seq30の第6回ローカル資格確認（2026-11-17）

[#398の包括承認](https://github.com/AtsushiHosaka/pals/issues/398)に従い、同じ問題・gpt-6.1-terra / medium・oracle・意味審査・合格条件で正規ローカル資格確認を1回実行しました。保存された同じrequestがstatus=failed、error_code=lean_verification_failedとなり、取得はfailedで終了しました。受け入れは0/1です。曖昧な送信を理由に再送した記録ではありません。

実行sourceは親`5e53d4a33f2cac3b77af9f1db42872c82a0d66fe`、infra`3f9ade65eccd49453fa303b1954e47f7fe37aabf`、準備対象の候補SHA256は`33447ab916651f741b4fa763f43e18528f051479cfb720dc43b0a10584005972`です。subjectは`1b5ba06b599841bae3d4a426fb99e6a07c51e165cf5aac4c3a0d1436fb0f3fac`で、旧候補の取得結果をPASSとして流用していません。

## 終端と重複送信の防止

新しい専用stateに単一送信markerがあり、stateはsubmittedでした。markerと保存済みrequest snapshotを比較し、request ID・chat IDが一致、markerと取得結果のsubject hashも一致することを確認しました。IDや質問内容は公開しません。

正規結果のコードは`browser_journey_failed:terminal_answer_required_failed_lean_verification_failed`です。snapshotも同じrequestのfailedを示し、answerはnullでした。取得前のcompiler canaryは2420msでverifiedでしたが、この準備用compileの成功から、生成した証明そのもののcompile結果を推定しません。保存された取得ログとsnapshotだけでは、compiler error、意味審査の拒否、他の実行上の原因を分離できないため、分類はunclassifiedとします。数学の誤りや意味審査の誤判定とは断定しません。

今回のstate・marker・失敗結果は保持します。次の取得が必要なら、同一条件・実台帳・残予算・依存先を確認し、別の専用stateと新しい単一送信markerで新しいproofを1回送信します。不明な既存送信を新しいIDで再送する扱いにはしません。今回の観測にDBの追加読取やraw SQLは必要ありませんでした。

## 時間と費用

取得全体の壁時計108.650秒は、主担当がwrapper終了時に観測した値です。正規receiptの開始・終了は02:57:04.074108 UTCと02:58:52.676291 UTCで、wrapper全体とは測る区間が異なります。回答時間の中央値や性能改善率には使いません。

取得前は83 calls・292673μUSD、終了後は91 calls・327573μUSDでした。差分は内部8 calls・34900μUSD、0.034900 USDです。実台帳の完了済み先頭91 recordsを、凍結sourceのversioned costで再計算し、全91 callsがcompleted、先頭83 recordsが292673μUSDであることを照合しました。後続の取得の使用量はこの計算へ含めていません。終了時のactualとreservedはともに327573μUSDでした。

過去closedの予約上限310668μUSDを含めた累積の保守的上界は638241μUSD、1 USDまでの残額は361759μUSDです。既知actualの累積は304459+327573=632032μUSDです。これらは版管理された料金表によるproxy台帳の値で、実請求額や過去unknown callの確定費用ではありません。reset、予算増額、健全な台帳のrolloverは行っていません。

品質台帳では今回の製品取得1件を0/1として追加します。内部8 callsを8試行とは数えず、以前の成功や技術診断とは分母を分けます。費用は今回の差分だけを計上し、以前の費用を重ねません。今回の記録は本番の切り替えや受け入れを示しません。

## 根拠のSHA256

| 記録 | SHA256 |
|---|---|
| 正規取得結果 | `f78b787a1e5de5feaac99a4adac4c863dab84fffdbb1ef4822fd7d0703e4c431` |
| 単一送信marker | `73fbc0579f1f80c70fc8307871347d7810c5ae15445cadfcb855ae46bd1a49b2` |
| 同じrequestの終端snapshot | `f99eb9c9866eb222651a1c184be3786a982ee541cd84cc991b478cb18da3b898` |
| 正規取得ログ | `6a28d6e534674f83584c1eedabc417aa7f1c8b808b832eaf5435de4baf099a1b` |

生の質問、回答、Lean、request ID、session、env、資格情報と内部配置場所は非公開で保管します。追加の実環境確認を行わず、保存結果と台帳の閉じたrecordsからこの記録を作成しました。
