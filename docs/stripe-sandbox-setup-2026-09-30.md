# Stripeサンドボックス設定記録

追記：この文書は最初のJPYテスト設定の履歴です。後続の承認済みUSD3プランと利用トークンの設定・検証は [USDプラン検証記録](usd-plans-sandbox-2026-09-30.md) を参照してください。

2026-09-30。ユーザーがChromeで開いていた `atsushi hosaka sandbox` を利用。接続先はユーザー指定のローカルPALS。既存Chromeを再利用し、実カード・実請求・本番アカウントの変更は行わない。

## Stripeに登録した内容

| 項目 | 内容 |
|---|---|
| 商品 | PALS Pro |
| 商品ID | `prod_VM0NMPXOhD0PC1` |
| 価格ID | `price_1ULIN7KGKycmoWoDHu7msxEz` |
| 料金 | JPY 1,500、毎月、固定料金、数量1 |
| 説明 | PALS Pro 月額プラン。各請求期間に証明生成リクエストを100回利用できます。 |
| 環境 | サンドボックス、`livemode=false` |
| 無料トライアル | 設定なし |

最初に開かれていた「Create a test subscription」は特定顧客への契約作成画面なので、そこで契約を手動作成せず商品カタログに登録した。PALS側のアカウント識別と紐付けるため、契約はPALSのアップグレードからCheckoutを経て作成する。

今回の価格は現行コードに合わせたテスト用。検討中の利用トークン制と新料金を確定したものではない。

## 顧客ポータル

デフォルト設定 `bpc_1ULIPmKGKycmoWoDOBaAo8Gf` を保存。

- 見出し：PALS Pro のお支払い・契約管理。
- 戻り先：`http://localhost:3000/`。
- 請求履歴、支払方法変更、顧客情報変更：有効（既定）。
- 解約：有効、請求期間の終了時（既定）。解約理由の収集も既定のまま。
- プラン変更・数量変更：無効（既定）。
- 公開用ログインリンクの発行は不要。PALS APIが認証済み顧客のPortal sessionを生成する。

保存後に再読込し、Stripe APIの読み取りでも価格・テストモード・ポータルの値を照合した。

## ローカル接続

- 既存サンドボックス秘密鍵を `.local/e2e/stripe/sandbox-key` にmode0600で保存。鍵の新規作成・ローテーションは行っていない。
- API向けJSONは `.local/e2e/billing/config.json` にmode0600で保存し、APIコンテナだけに読取り専用マウントする。これらはGit管理外。
- `.env.local` に秘密値ではなく `PALS_BILLING_CONFIG_FILE=/run/pals-billing/config.json` を追加。
- `PALS_ENV=local`・テスト鍵・localhost:3000の組合せだけを許可する設定読込を実装。本番のHTTPS origin制限は維持。
- 公式Stripe CLI v1.52.1を `.local/e2e/tools/stripe/stripe` に配置。公式公開SHA256とGitHubのasset digestを照合。
- Stripe CLIでイベントを `http://127.0.0.1:8000/v1/internal/stripe/webhook` に転送する。本番向けWebhook endpointは作成していない。
- 対象は `checkout.session.completed`、`customer.subscription.created/updated/deleted`、`invoice.paid`、`invoice.payment_failed` の6種類。

CLIの通知はサンドボックス既定の `2026-08-26.dahlia`。APIによる契約再照会は既存の `2024-06-20` 固定を維持する。新しいinvoice通知の `parent.subscription_details.subscription` にも対応し、旧形式との矛盾・不正な参照は無視する。通知の内容だけで権限付与せず、Stripeから契約を再取得して所有者・商品価格・状態を照合する。

仕様変更の根拠：[Stripe公式のinvoice構造変更](https://docs.stripe.com/changelog/basil/2025-03-31/adds-new-parent-field-to-invoicing-objects)。

## 検証と残作業

ローカル設定と新旧通知形式の関連118テスト、実PostgreSQL3ケース、Ruff・mypy成功。独立レビュー81テスト成功。実APIコンテナでも所有者一致・mode0600・通常ファイル・設定パスを秘密値を読まず確認した。

最初の実CheckoutではStripeの作成APIは200だったが、PALSのURL検証が正当なfragmentを拒否して画面遷移に失敗した。HTTPSと正規ホスト制約を維持したままfragmentを原文保持する修正を行い、新規18ケースを含む99テストを確認。同じ冪等操作で再試行し、顧客・Checkoutとも作成記録が1件だけであることを確認した。

- PALSの既存ローカルQAアカウントから「Proにアップグレード」を実操作。
- Stripe公式テストカード `4242 4242 4242 4242`、有効期限12/34、架空のテスト氏名・メールを使用。実カードは使わない。
- テスト決済成功後 `http://localhost:3000/` に戻り、画面と実APIで `billing_source=stripe`、Pro100回、期限2026-10-30を確認。
- `invoice.paid`、`checkout.session.completed`、`customer.subscription.created/updated` の4件がHTTP200かつDB上 `accepted`。新しいinvoice形式も実イベントで受理。
- 「契約を管理」からポータルに移動し、PALS Pro・月1,500円・テストVisa末尾4242・支払済み請求書を確認。
- テスト契約ID：`sub_1ULIduKGKycmoWoDnsdaMt0f`。解約は一度自動レビューで止まったが、ユーザーが「解約予約と即時終了まで確認してよい」と明示承認後に実施。
- ポータルで期間終了時の解約を予約し、Stripeの `cancel_at_period_end=true` とPALSの期間内Pro維持を確認。その後、このテスト契約だけを公式APIで即時終了し、`customer.subscription.deleted` 受理→PALS Free残量1回への復帰を確認。テスト契約は終了済み、実請求・返金なし。
- 期間終了時の解約後に「更新日」と表示すると誤解を招くため、4言語の表示を「請求期間の終了日」に変更。関連32テストと型検査成功。解約状態の新しいUIを実装したものではない。
- 解約後に再加入しようとすると、完了済みCheckoutのURLがnullになって再利用できない問題も修正。session/customer/owner/modeの照合と、owner lock内での契約再取得を行い、終了済み契約だけ新しいCheckoutへ切り替える。曖昧なpendingは23時間経過後も勝手に再作成せず、手動照合を要するエラーで停止する。この手動回復用の運用コマンドは未実装。
- 再加入修正は実PostgreSQL13ケース、unit46ケース、独立レビューの関連unit47ケース、Ruff・mypyで確認。これらは重複を含むため合計件数とはしない。
- 最終APIとフロントを既存Composeへ反映後、PALSの「Proにアップグレード」から新しいStripe Checkoutへの到達を実確認。再決済は行わず、未払いセッションを期限切れにして後片付けした。同じ顧客を再利用し、Stripe上の契約は終了済み1件だけ、active契約0件。既存9サービスはhealthy、通知リスナーは1つ稼働。

最終時点のAPIはFree。解約直後の残量1回と、最終確認時の残量0回は異なる。旧予約2件はそのままで、最終ビルドの集計は別の証明リクエスト用holdも含めるため、最終証跡を解約直後の残量の証拠として流用しない。今回のCheckout経路では証明を送信していない。

証跡は `output/stripe-setup-20260930/` の `stripe-configuration.json`、`paid-runtime.json`、`product.png`、`checkout-test.png`、`pro-after-payment.png`、`customer-portal.png`。サンドボックスの取引であり、資金移動はない。[公式テスト資料](https://docs.stripe.com/testing)

解約の証跡は `cancel-scheduled.png`、`scheduled-runtime.json`、`terminated-runtime.json`。Webhook配信ログの共有用コピーは秘密値を伏せた `webhook-deliveries.log`。
再加入の証跡は `rejoin-checkout.png`、`rejoin-runtime.json`、`final-runtime.json`。支払い失敗通知 `invoice.payment_failed` の実Stripe発生は今回確認していない。

## 次回のローカル起動

```sh
python3 pals-scripts/run-local-stripe.py
```

このコマンドは前面で通知を転送し、Ctrl+Cで終了する。起動中の同じリスナーがある場合は二重起動を拒否する。現在はこの正式スクリプトで転送を再開済み。秘密値が前回と同じであることを実Stripeのreadinessで確認した。

Webhook署名secretが変わったと表示された場合だけ、既存APIを通常のCompose手順で再起動して新設定を読む。スクリプトはAPIやDBを自動再起動しない。秘密鍵、CLI用ログ、JSONはいずれもGit管理外に保管する。起動スクリプトは16テスト（テスト用CLIプロセス）に加え、実Stripeでの起動確認済み。

## 本番公開とは別に残る作業

本番商品・価格、本番秘密鍵、本番Webhook、公開アプリへの設定配布、本番の事業者情報や税・利用規約等は未設定。今回の成功はローカル＋Stripeサンドボックスの確認に限定される。利用トークン制や成功時だけ消費する新料金体系を、このStripe商品へ適用したものではない。
