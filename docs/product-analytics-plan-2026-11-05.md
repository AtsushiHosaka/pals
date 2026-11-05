# 操作後の離脱とPlus転換の計測案

CloudWatchを集計・閲覧の基盤にする考え方は妥当です。ただし、ボタン操作、回答の完成・閲覧、契約資格、実際の支払は別の出来事として記録する必要があります。CloudWatchを導入しただけでは、利用経路や有料転換の正しい分母は得られません。

オーナーの追加依頼は、どのボタンが押され、その後どこで利用が止まったか、Plusへ転換したかを調べたいというものです。担当はCodex、[担当チャット](codex://threads/01a1a6ef-927b-7d72-b689-5c442ada7af7)、進行は[pals#250](https://github.com/AtsushiHosaka/pals/issues/250)。本書は計測案と現行コードの調査記録で、まだ収集・配備は始めていません。

## 推奨する構成

まず送信・回答閲覧・プラン表示・Plus選択・Checkout・支払・クーポンの重要導線を対象にします。提案する流れは「画面とサーバーの出来事 → 許可されたアプリ側で照合・重複排除 → CloudWatchへ集計」です。どの操作の後に止まったかは、最後の観測段階と次段階への未到達から集計します。最後のボタンを離脱の原因と断定しません。

[CloudWatch RUMは独自イベントを送信できます](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-RUM-custom-events.html)。ただし現行のPALSには、ユーザー識別子や外部へ出す項目を制限する契約があります。RUMの自動収集をそのまま有効にする案は採用せず、必要なイベントと送信範囲を先に定義します。[RUMが収集する情報](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-RUM-datacollected.html)にはページのタイトルやpath、任意に有効化するDOM操作などがあるため、利用者の本文や識別子を含めない検査が必要です。

CloudWatch側は個人IDを含まない集計を、品質監視とは別のProduct用の名前空間・ログで扱う案を優先します。user・session・attemptをmetric dimensionにすると、個々の組み合わせが系列を作って費用が増えます。[AWSのEMF説明](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format.html)もこの点と重複配信を明記しています。生のイベント数を、そのまま正確な購入人数として使いません。

## 計測する段階と指標

| 対象 | 分けて観測する段階 | 指標の初期案 |
|---|---|---|
| 回答の利用 | 送信試行、API受理、回答完成、ブラウザでの回答閲覧 | 成熟した開始経路のうち、どこまで到達したか。拒否・処理失敗・完成未閲覧・欠測を別表示 |
| ボタン操作後の未到達 | 固定したaction ID、期待する次段階、最終観測時刻 | 所定の窓内に次段階が観測されなかった割合。30分は初期案で、観測窓が終わっていない対象は分母から分ける |
| Plusの有料転換 | Plus案内表示、Plus選択、Checkout作成、契約資格、実支払 | 適格な無料会員のうち、案内表示から7日以内に最初の実支払を確認した人数。7日は初期案で、live/test・0円/試用・再加入・他商品を別にする |
| 初期ユーザー施策 | 無償Plus引換、実利用、後日の有料化 | クーポンの利用開始と有料転換を別集計。後に本当に支払えば有料転換へ数え、獲得cohortだけを保持 |

30分・7日は、オーナーが決めた値でも、測定済みの値でもありません。導線の所要時間と実装上の欠測を確認して仕様で固定します。分母0を0%と表示せず、不明・未成熟・計測停止を区別します。比率には分子・分母の件数も付けます。

回答を読んで終了した正常な利用と、回答前に止まった利用は別です。Stripeへ画面が移ったことやタブが非表示になったことも、確定した離脱ではありません。別タブ、外部決済、後日の復帰、計測の遮断があるため、pagehideだけで判断しません。翌日・7日後などの再利用率も、今回の「操作後の未到達」とは別のcohort指標として扱います。

## 現行コードで確認できた不足

調査したsourceはAPI `60f8cd216bb33be542b155f76b8a9c9bec8ccc0a`、Web `e63bc50ed4c7410260888ad87a202bec19565bd7`です。これらは未配備の候補で、現在の本番に行動計測があると推定していません。

- Webにはボタンクリックや課金画面の分析イベント送信がありません。
- `billing_stripe_operations.completed`はCheckout Sessionを作成・保存できた状態です。API応答もcheckout URLだけで、画面の操作とサーバー由来の確定処理を照合する専用attemptがありません。
- subscription・entitlementは現況を保持します。Webhook台帳のaccepted件数から、初回入金や売上は算出できません。invoice・実支払額・通貨・live/test・初回日時と、Sessionからsubscriptionへの確定した対応記録が不足しています。ownerと時刻だけで推測結合しません。
- summaryの価格は商品カタログ上の公称月額で、実際の入金額ではありません。既存の`plan=pro`もPlus・Pro・Research等を区別する指標には使えません。
- `billing_product_id=plus`でも、`billing_source=complimentary`は無償Plusです。Stripeの資格成立、最初の実支払、クーポンの引換をそれぞれ区別します。以前クーポンを使った人を、後日の有料転換から永久に除外しません。

根拠は[課金処理](https://github.com/AtsushiHosaka/pals-api/blob/60f8cd216bb33be542b155f76b8a9c9bec8ccc0a/app/infrastructure/repositories/billing_operations.py)、[課金DTO](https://github.com/AtsushiHosaka/pals-api/blob/60f8cd216bb33be542b155f76b8a9c9bec8ccc0a/app/schemas/billing.py)、[Webの課金画面](https://github.com/AtsushiHosaka/pals-webfront/blob/e63bc50ed4c7410260888ad87a202bec19565bd7/components/BillingSettings.tsx)です。[Stripeの公式説明](https://docs.stripe.com/checkout/fulfillment)でも、戻り画面へのアクセスだけに購入確定処理を依存させないよう説明しています。

## 現行のデータ契約を維持する

[品質監視のPQO005・008・010](../specs/proof-quality-observability/requirements.md)はdimensionと送信範囲を限定し、利用者・アカウント・セッション識別子をログにもメトリクスにも出さない契約です。HMAC化した識別子を品質ログへ加えてよいという意味ではありません。品質指標の分母や許可項目は維持します。

APIの[TDG移行](https://github.com/AtsushiHosaka/pals-api/blob/60f8cd216bb33be542b155f76b8a9c9bec8ccc0a/app/release/trace_data_governance_migration.py)は旧analytics・experiment・feedbackの3テーブルを禁止対象として削除し、正規readinessも不存在を要求します。元のTDG仕様・判断本文は、今回の限定検索では見つかりませんでした。別のローカル作業ツリーには古い未版管理のANA案がありますが、無期限保存や旧環境の手順も含むため、現行契約として移植しません。

新しい計測の目的・対象・保持と削除・通知や同意・仮名の照合・アクセス権を、独立した仕様に定めます。仮名化は匿名化ではなく、guestからログイン後の本人を推測結合することも既定にはしません。旧テーブルを復活したり、名前だけを変えて制限を回避したりせず、現行方針との整合を確認してから収集を実装・有効化します。

## 次の実装と受入

閉じたpage/action名と期待する次段階、サーバー由来のattempt、重複排除済みの確定課金履歴を用意します。ブラウザの申告だけで支払を成立させません。URL・query・DOM本文・質問や回答・メール・IP・認証情報・生のaccount IDは送信対象にしません。計測の停止や通信失敗で、既存の操作を止めない設計にします。

アプリ側で成熟したcohortを計算し、CloudWatchには版付きの集計snapshotを出す案です。再送されたsnapshotを単純に足し続けず、遅延Webhookや再集計の更新も識別できるようにします。CloudWatch用のdimension、送信上限、保持期間、queryの走査範囲と追加費用も仕様に含めます。

受入では正常な完了、回答前の終了、完成未閲覧、外部決済後の支払、キャンセル、0円・クーポン、後日のcouponからpaid、再送と順不同、欠測、未成熟を合成記録で確認します。その後、許可された本番収集の対象と期間で保存・集計・CloudWatch閲覧まで検証します。過去に存在しなかったボタンクリックを、既存ログから復元したようには報告しません。本書は設計段階の記録であり、品質台帳へ新しい測定結果としては追加しません。
