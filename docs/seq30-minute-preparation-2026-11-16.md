# seq30新候補のモデル送信前の準備（2026-11-16）

新候補の署名、source checks、ローカル依存先、ホスト配置と認証contextの開始確認まで進みました。実行sourceは親`3b663576036a5c3a9fe2ca092e8ccbf84b5f96a8`、infra`3b31597edda4d474700af9b55178ae20193b6001`です。候補SHA256は`f20df8a4970b5a3ea98af712ca1663164b2dcd9e7119c8eae840bdb43ea89f46`で、アプリimageとverifier sourceは従来のseq30の組合せを保持しています。

候補は有効化しておらず、通信除外や新しい有料質問の送信は行っていません。新候補に対する第5回ローカル資格確認は未承認・未実行です。今回の準備を、`accepted`なローカル取得や本番受け入れへ読み替えません。過去候補の失敗や期限切れの取得も、そのまま保持します。

## sourceとローカル依存先

正規の画像確認・未署名検査を経て署名し、正規`release-source-checks`は対象5repoについて`source_checks_passed`になりました。検査件数やrepo数は独立した製品試行には数えません。実行用のcleanなsourceは上記の親revisionで固定し、本記録を作る文書branchとは分けています。

正規local prepareの結果は`prepared_dependency_ready_not_product_accepted`です。実compiler canaryは2152msでverifiedとなり、attestationを含む準備契約を通過しました。新しいsubjectとenvを生成し、実runtime内の累積予算guard sourceも修正版のhashに一致しています。

準備後も予算台帳は71 calls、actual・reservedがともに255446μUSD、各期上限700000μUSD、blocked=false、全calls completedです。既存callsとrollover証拠を保持しており、今回のprepareによる新しいモデル費用はありません。予算proxyの再開に伴うmetadataだけを正規に更新しました。

過去closedの累積reserved310668μUSDを含む保守的な使用上界は566114μUSD、累積1 USDまでの残額は433886μUSDです。既知actual合計559905μUSD、unknown callの確定費用、実請求額とは区別します。各期の700000μUSDを追加予算とは扱いません。[累積予算ガード](seq30-cumulative-local-budget-2026-11-16.md)は元の台帳・承認・schemaを保った送信前制限であり、resetやhealthy rolloverは行っていません。

## ホスト準備と配置

正規host-prepareとhost-stageの受領書は同じ新候補を示し、いずれもapplication・databaseの変更はfalseです。配置には28 blobsを用い、実行sourceとの照合を通した17のsource依存も保持しています。これらは候補の準備・配置の記録であり、有効化の成功ではありません。

正規の初回観測は09:57:14 UTC、準備後は10:05:39 UTC、配置後は10:18:13 UTCです。三つともownerなし、application・databaseの変更なしを記録し、既知14 attempt stateを確認しています。観測は時点の記録です。次の操作で必要になる鮮度や実状態の照合を、この古い観測で省略しません。

## 端末と認証context

10:15:02 UTCの端末ネットワーク確認では、対象の二つの公開入口がHTTP 200でした。これは端末から到達できた記録で、本番回答や認可の受け入れではありません。

同候補・署名・実ホスト観測・computed runtime pinsに結び付けた正規factoryのpreview contractから、正規transportの開始と終了だけを実行しました。結果は`authenticated_context_observed`、API operation messageは0、paid submissionはfalseでした。元session seedは変更していません。製品自身の承認済み通常更新経路を使用し、refreshはcontext当たり最大1回、資格情報の書き戻しや出力は行いません。個別のrefresh要求・応答は今回の記録では観測していません。

この結果は、本番API認可や新候補の製品受け入れを証明しません。終了JSONが以前の確認と同じ内容になるため、ログのhashだけでは新候補への結び付きを判定しません。今回は新候補を指すauth-attempt、preview-inputs、post-contractのhashと相互参照も照合しています。previewのsubject projectionは`projection_checked=true`・`frozen_or_qualified=false`です。

## 第5回の実行前に残る条件

現在のplan-input-2 draftには三つの`SUPPLY` placeholderが残っています。これは準備のためのDATAで、実行可能な最終release plan、合格した資格確認、凍結済みcontractではありません。

第5回を実行するには、追加1回の明示的な承認を、新候補・subject・実台帳のhashに結び付けて得る必要があります。取得は正規`make release-local-qualify`の1回に限り、自動再送、成功条件の緩和、予算reset・rolloverは行いません。今回の準備でその承認を代用しません。その後も、新しい取得の受け入れ、最終固定、dry runと実行、本番の回答・保存・描画・履歴確認は別の工程です。

## 根拠のSHA256

| 記録 | SHA256 |
|---|---|
| 署名evidence | `b2fa586c68b6f509df53963861c09aa6ed1b3f5bca133ed64be89ff36626ad54` |
| source checksログ | `2e28cd09aabcaf366484fe08fa6a0a1ec87ca812d00dc32a2443cf7c7eca080b` |
| local prepareログ | `f63419b778148a4f2747e6c217b47755edd4a492ec211288f4c14efa06420429` |
| 新subject | `24b3a2e12cbf2af3ee50b1d579598f923c02885974a941ed287fd30473087b6d` |
| 新env | `6a2881028fc2dbc0371e49b9b292ef863c6093dfc1150234bf3e285861c00484` |
| 再開後予算台帳 | `f0e2191d784e604f6415d400206f050c766d486138b54d8cbd24132fe580cb85` |
| host-prepare受領書 | `652dc2c2a6f26e65ea2ed2b446514122b97f585ea299d695b72d0752bb8afd2c` |
| host-stage受領書 | `77cb6f701a4b61d2be903e55f647c25604b5e67e718e40e02c67d4cc393d295f` |
| stage config | `a601e30733c4f533b43024c7d5613e404fdea67211e2591d0e8c8d447ab9c3d8` |
| 初回観測 | `66f9dfca4525a1c1e6cb20bc86f8f13def436452e28febba56ee67c438511b51` |
| 準備後観測 | `d9f0b658f680d120d2a29a4a17387b7f23b7520041e1bdea8cfd9c880f9a860d` |
| 配置後観測 | `691664f5259f48d1ec3fe13568699712314e03d62918f1726afafb2e6267c4f5` |
| 端末ネットワーク確認 | `5e4b2033884443de8db442f0ba40c1b172232b3baa23af628d956e9100dd883d` |
| preview post contract | `b1c9e84cb7919984c81855cde66725cf0e9effd3a30cdc5bc5a0e6d55ccdc1e7` |
| 新preview入力metadata | `2ca401ec1f552f274a136f4723bf0e642416a2fcb5c9e0e58b60a17f047ebf41` |
| 新auth-attempt | `1805a949756ad160577ed6b809566752f2ad6e32c4352386aa35e5b38408ccc1` |
| auth開始・終了の結果ログ | `d2204ffdeb71d0184569bb164adc6ab11029e075289ca1ebdfa20d6f46919220` |
| placeholder付きplan-input-2 draft | `8d5a0fd4570cf2cc502a913823929eac256ba19aa775870cce84d7cc6157c923` |

生の証拠、env、session、資格情報、内部識別子と配置場所は非公開で保管します。品質台帳には、新候補のモデル送信前の準備bundle1件として1/1を追加します。各手順や内部件数は数学の試行に数えません。費用総額と全体所要時間は未測定です。

## 2026-11-17 JST追記・取得回数の判断

オーナーは「何回でも許可しますよ」と回答し、[最新の判断を#398](https://github.com/AtsushiHosaka/pals/issues/398)に記録しました。同じ問題、生成モデルgpt-6.1-terra / medium、oracle、意味審査と合格条件を維持したseq30のローカル資格確認について、回数上限を解除しています。本文の「第5回未承認」は、今回の回答より前の状態を記したものとして保持します。今後は回数だけを理由に承認を取り直しません。

累積1 USD、過去のunknown callを予約額で数える正規guard、既存台帳・各期上限・履歴は維持します。reset、予算増額、健全な台帳のrolloverは含みません。各取得は新しい専用stateと単一送信markerに固定し、不明な送信は同じIDの観測を回復して重複送信を防ぎます。次の取得が必要な場合も、同一条件、残予算、期限と実依存先を確認します。今回の判断だけで、取得や本番有効化が成功したとは扱いません。
