# seq30の検証環境回復と第5回取得（2026-11-17）

AWSの通常ログイン、TLSと実build履歴の回復後、同じ問題・モデル・oracleで第5回の正規ローカル資格確認を実行し、acceptedになりました。この記録の対象は、その取得と直後の正規再照合までです。取得を受け入れた時点では、新候補の本番切り替えとcore受け入れは未実施でした。その後の本番結果は別に記録します。

sourceは親`3b663576036a5c3a9fe2ca092e8ccbf84b5f96a8`、infra`3b31597edda4d474700af9b55178ae20193b6001`、候補SHA256は`f20df8a4970b5a3ea98af712ca1663164b2dcd9e7119c8eae840bdb43ea89f46`です。アプリ、問題、gpt-6.1-terra / medium、oracle、意味審査と合格条件は変更していません。取得回数は[#398の包括承認](https://github.com/AtsushiHosaka/pals/issues/398)に従い、累積1 USDの制限と単一送信markerを維持しています。

## 前提の失敗と回復

ユーザーの通常SSOログイン完了後、同じ正規観測のrecoverで結果を回収しました。受領書はownerなし、application・databaseの変更なしを示しています。新しい観測要求を重複送信したものではありません。期限切れだった専用TLSは正規bootstrapで更新し、validを確認しました。

その後の最初の正規reprepareは、既存build receiptのlive history確認で停止しました。診断は`local_dependency_command_failed`、子処理のreturncodeは1でした。主担当はWebとnativeの実Docker履歴を別に読み、参照先が削除済みであることを確認しています。保存した閉じた診断はhistory確認の失敗を記録しますが、生の削除エラー全文や削除した機構を特定する証拠ではありません。GCなどの原因は断定しません。

この失敗時のsubject、env、予算台帳は保持しました。過去の受領書をPASSとして流用せず、同じsource・archive・builderを正規CLIで再buildしました。Webは実image IDが以前と異なる一方、runtime base先頭6層、materials、build parameters、sourceとloopback引数の一致を検査しています。全image差分が乱数だけだとは主張しません。nativeは同じimage IDとなり、source・Dockerfile・Lean・Mathlib・contextと実probeの一致を通過しました。

新しい実provenanceを使った正規reprepareは`prepared_dependency_ready_not_product_accepted`になりました。compiler canaryは2588msでverifiedです。既存71 calls・255446μUSD・各期cap700000・rolloverを保ったまま、新TLS、subject、envと実guardを再固定しました。初回失敗の記録や出力は上書きしていません。

## 認証開始と有料取得

更新後の端末ネットワーク確認は対象入口でHTTP 200でした。新subjectと新候補を指す正規previewのmetadataから認証contextを開始・終了し、`authenticated_context_observed`を確認しました。API operation messageは0、paid submissionはfalse、元seedは不変でした。この確認自体は本番API認可や製品受け入れではありません。

第5回は新しい専用stateとmarkerで正規`make release-local-qualify`を1回だけ実行し、acceptedになりました。実PostgreSQL・Lean・provider/modelから、説明、保存、描画と再読み込みまでのローカル契約を通しています。取得全体の壁時計139.635秒は、主担当がwrapper終了時に観測した値です。回答時間の中央値や本番性能の測定には使いません。

初回受領書のhashは独立に読み取って記録しました。その後、正規`--verify-existing`が同じ取得を新規送信なしで再照合したため、現latestのhashは変わっています。再照合時の`proof_submissions=0`は追加送信がなかったことを示し、最初の取得で送信しなかったという意味ではありません。再照合を新しいpaid試行や追加成功として数えません。

## 費用と試行の数え方

取得前の71 calls・255446μUSDから、取得後は83 calls・292673μUSDになりました。差分は内部12 calls・37227μUSD、0.037227 USDです。actualとreservedはともに292673μUSD、blocked=falseです。内部12 callsは、一つの取得を構成する処理であって12試行ではありません。

過去closedの累積reserved310668μUSDを含む保守的な使用上界は603341μUSDで、累積1 USDまでの残額は396659μUSDです。既知actualの累積は304459+292673=597132μUSDです。未知callの確定費用や実請求額とは区別します。reset、rolloverや予算増額は行っていません。

品質台帳では、最初の履歴確認失敗を技術bundle1件の0/1、今回の有料資格確認を別の製品取得1件の1/1として記録します。新build・reprepare成功は前提回復の経過に含め、別のpaid成功へ加算しません。技術失敗を数学の失敗に含めず、二つの分母を合算した製品成功率も作りません。各試行は別のjournal entryへ結び付けます。回復全体の所要時間と費用総額は未測定です。

## 証拠のSHA256

| 記録 | SHA256 |
|---|---|
| SSO後の正規recover観測 | `1f6e07f3595766247baa713f3a5d0e999350b8c26f825bde5e74f7b6be039957` |
| 正規TLS更新ログ | `077dfea89ba392371bc78269c9941974eec326e8f4cc4872ea43078ee31fb97c` |
| 最初のreprepare失敗ログ | `f0f447f889fcc0d29c11c98daa3688db51cb30c9dd71b67db559c80aab589ac4` |
| 閉じた子処理失敗診断 | `dd92afef92dfae0eadc097883b3acd5f1128a3460882693854be4cf50d72c95f` |
| 新Web build provenance | `4918f152415798a2b629be00691371b5dce14c685db470e1df9985932794651a` |
| 新native build provenance | `76df337db11cfd3e149b472676a51ad5b87ddf6b37cbb7809c36a422443d6cff` |
| 新provenanceによるreprepareログ | `cb6a51e4cbf3f36b3c4b97c1621ce076dbc93980c3981f033cad8bafaa509d6b` |
| 回復後subject | `1b5ba06b599841bae3d4a426fb99e6a07c51e165cf5aac4c3a0d1436fb0f3fac` |
| 回復後env | `854cdae9befa49ea93b2e0606f8326d33552b4d44d3c498e4e5e987c8a411299` |
| 第5回取得前台帳 | `26331a37cea6722062a378b54b7b9b5fc10c2b70eda3926bcd9185e5e1d7c236` |
| 新認証preview metadata | `8dda1e4215eb004f4fb9a3997186aa772681115b5cb7b22ff1f4c5c49a0c07a3` |
| 認証開始・終了ログ | `d2204ffdeb71d0184569bb164adc6ab11029e075289ca1ebdfa20d6f46919220` |
| 第5回の初回受領書・当時観測 | `ef5f7531d3c899dfacded9cceaaf2d61928d4be17094a2dc768be901d70c570b` |
| 同じ取得の正規再照合後受領書・記録時点 | `e450a7ae5094a06cde3429ffa67084bfe7608cd62dea5f8ca9531488843ac8aa` |
| 第5回取得ログ | `2e0c4af4aaf220b316963f33b9541e7bb8ec16a1f42e4dcfe2cdd86b46be525f` |

生のログ、質問、回答、Lean、env、資格情報と内部配置場所は非公開です。ここで扱った実ローカルの資格確認は、production AMD64、実API認可、切り替え後の新規質問の保存・描画・履歴の受け入れを証明しません。全体10分条件と実ownerの検証を含む手順見直しは、[#379のレビュー案](https://github.com/AtsushiHosaka/pals/issues/379#issuecomment-6933712862)へ分けています。
