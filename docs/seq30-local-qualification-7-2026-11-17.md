# seq30の第7回ローカル資格確認（2026-11-17）

同じ問題・gpt-6.1-terra / medium・oracle・意味審査・合格条件で、新しい専用stateと単一送信markerを使って正規ローカル資格確認を1回実行し、acceptedになりました。[第6回の終端failed](seq30-local-qualification-6-2026-11-17.md)は別の取得として保持し、この成功で書き換えません。

sourceは親`5e53d4a33f2cac3b77af9f1db42872c82a0d66fe`、infra`3f9ade65eccd49453fa303b1954e47f7fe37aabf`、準備対象の候補SHA256は`33447ab916651f741b4fa763f43e18528f051479cfb720dc43b0a10584005972`です。実行は[#398の包括承認](https://github.com/AtsushiHosaka/pals/issues/398)と累積1 USD上限に従い、条件や予算のreset・rolloverは行っていません。

## 受け入れと計数

実DB・Lean・provider/modelを使い、終端、説明、保存、描画と再読み込みまでのローカル契約を受け入れました。独立に読み取った初回受領書はaccepted、terminal_statusはanswered、proof_submissionsは1で、表示と再読み込みのsemantics hashが一致しています。準備用compiler canaryは2428msでverifiedでした。終了は03:04:58.412825 UTCです。

取得全体の壁時計137.443秒は、主担当がwrapper終了時に観測した値です。回答時間の中央値や性能改善率には使いません。製品取得1件の1/1として記録し、内部provider calls、後の正規verify-existing、切り替え前の技術確認を追加の成功として数えません。第6回との2件だけで数学全般の精度や改善率も主張しません。

## 費用と残予算

初回受領書内の取得前台帳は91 calls・327573μUSD、取得後は102 calls・367767μUSDでした。差分は11 calls・40194μUSD、0.040194 USDです。全102 callsがcompleted、actualとreservedはともに367767μUSD、blocked=falseであることを保存受領書から照合しました。過去の費用は重ねて計上しません。

過去closedの予約上限310668μUSDを含む保守的な使用上界は678435μUSDで、累積1 USDまでの残額は321565μUSDです。既知actualの累積は304459+367767=672226μUSDです。いずれも版管理された料金表によるproxy台帳の値で、実請求額や過去unknown callの確定費用ではありません。各期のcap700000μUSDと、累積1 USDの送信前guardは維持しています。

## 証拠と残る条件

| 初回受け入れ時の記録 | SHA256 |
|---|---|
| 正規受領書・独立読取時点 | `b648893638748da013f5c7df6adc9e730d8c89426d8d233db073a388be8ad2fc` |
| 取得ログ | `d178466a1ed865716f60a4151caefce84070e6152e4103f395f66796f2768a7f` |
| 単一送信marker | `afc54327d3cc1674b6c6dddefd45243af4df394d56bc8855e50316651160e77e` |
| browser結果 | `dc8c5ae63a5454fdb46856a2c878e02f73a65052de4a2f6791b2cd514748b05c` |
| 同じrequestのsnapshot | `bedd49c9d97420da5256a6054785a0533ef4f9cc8ae7c2c5abd6867d1caf6f41` |

初回の受領書は、その後の正規verify-existingで新しい観測結果へ更新されました。表は現在のlatestのhashではなく、初回capture出力を独立に読んだ時点のhashです。初回の費用を固定し、再照合を新規送信や追加試行として数えません。rawの質問、回答、Lean、ID、session、env、資格情報と配置場所は非公開です。

判断は、この取得を後続の最終固定と正規切り替えに使うことです。ローカルの受け入れは、本番AMD64・認証・ネットワーク、切り替え後の新しい質問の回答・保存・描画・履歴を証明しません。元のrestore-check失敗の根因をこの成功で解消したとも扱いません。本記録は第7回取得の完了時点までを対象とし、その後の本番結果は別に記録します。
