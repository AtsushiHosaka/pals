# USDプランと利用トークンのローカル検証

2026-09-30。ユーザー承認の価格・暫定枠を、既存ローカルPALSと `atsushi hosaka sandbox` に適用した。本番課金の公開・既存JPY契約の移行はしていない。変更は未コミット。

## 設定したプラン

| プラン | 毎月の料金 | 月間利用トークン | 1依頼の上限 | StripeテストPrice |
|---|---:|---:|---:|---|
| Plus | USD 10 | 1,000,000 | 100,000 | `price_1ULJ6bKGKycmoWoDcS3b4vN7` |
| Pro | USD 20 | 3,000,000 | 300,000 | `price_1ULJ6bKGKycmoWoDy1mgeDZi` |
| Research | USD 100 | 15,000,000 | 1,500,000 | `price_1ULJ6cKGKycmoWoDZXgKpsf6` |

それぞれ別の商品・Priceを作成し、通貨・月額・数量1・商品IDをサーバー側で照合する。旧JPY1,500 Priceは過去契約の照合用に保持し、新規USD Checkoutでは選べない。Free累計3回と既存の無償Pro資格は従来台帳のままであり、過去の消費量を利用トークンへ換算していない。

`.local/e2e/billing/config.json` をv2へ更新した。秘密鍵・Webhook署名鍵は既存のものを維持し、ファイルはmode0600、Git管理外。`PALS_ENV=local`・テスト鍵・`PALS_TOKEN_ACCOUNTING_ENABLED=true` が揃った環境だけで新プランを有効にする。公開環境へこの暫定枠を適用しない。

## アプリの変更

- 設定の「使用量とプラン」で3プランを比較・選択できる。日本語・英語・簡体字・繁体字対応。
- 現在のプラン、料金、消費済み・処理中の仮押さえ・利用可能量・期間終了日・換算ルールを表示。
- アカウントメニューにも最新残量を表示。回答完了・失敗・前提確認の状態変更後に再取得する。
- 送信前に上限を表示し、残量がプラン上限より少なければその残量まで縮小する。表示後に上限が変わった場合は自動送信しない。
- 未払いCheckoutから戻って別プランを選んだ場合、所有者と未払い状態を確認した元セッションを失効させてから新しいものを作る。支払い競合・不明状態なら停止する。
- 契約中の重複購入は停止。日割りのプラン変更や自動アップグレードは実装していない。

## 利用量の仕組み

新台帳を追加し、従来の回数台帳と分離した。送信内容に結びついた5分有効の見積、依頼上限の予約、各provider呼出し前の許可、使用量の耐久的な記録、回答と独立QAの成功時精算を接続した。外部呼出しが上限を超える見込みなら実行しない。

換算ポリシーは `utilization-v1-2026-09-30`。100万利用トークンをUSD0.75相当とする基準で、モデル・入力・出力の固定版の重みを使う。現在はキャッシュ割引を適用しない保守的な値であり、提供元の請求額そのものではない。全呼出しを合算して最後に1回だけ切り上げる。cached inputとreasoning outputを二重加算しない。

失敗・前提確認では消費0、予約を解放する。使用量欠測、記録応答不明、QA不承認を成功扱いしない。処理中のクラッシュ後に既に外部呼出しがあった場合も、未知の処理を勝手に重複実行しない。API原価の既存記録は別途保持する。

## 実環境で確認した結果

既存Chromeと既存Composeサービスを再利用。DBレコードを手で成功状態へ書き換えず、PALS API→Stripe Checkout→署名付きWebhook、PALS API→SQS→実worker→OpenAI→精算の経路を確認した。

1. Plus $10、Research $100、Pro $20それぞれで実Checkoutの金額・月額表示を確認。Plus→Research→Proと選び直し、前の未払い2件がStripe上でも `expired` になった。
2. Stripe公式テストカード4242でProを決済。`livemode=false`。`checkout.session.completed`、`invoice.paid`、`customer.subscription.created/updated` を受理し、月300万・依頼30万の権限をAPIと画面で確認した。
3. 可換環の問題「√(IJ)=√I∩√J、逆包含の指数選択」を実際に送信。30万を予約し、回答・独立QA後に4,316だけ消費、予約0・残量2,995,684をAPIと画面で確認した。回答は両包含を分け、逆包含では `x^m∈I, x^n∈J` から `x^(m+n)∈IJ` と説明している。自然言語回答であり、Lean検証済みとはしていない。
4. 上限1の専用APIテスト依頼を実workerへ送信。予算不足で生成を拒否し、消費0・予約解放・残量不変を確認。成功テストの記録を失敗テストへ流用していない。

成功依頼の記録：

| 呼出し | モデル | 入力 | 出力 |
|---|---|---:|---:|
| 初期判断 | gpt-6-luna | 489 | 149 |
| 構造化 | gpt-6-luna | 1,469 | 1,473 |
| 検索埋め込み | text-embedding-3-small | 1,766 | 0 |
| 回答 | gpt-6-luna | 12,311 | 924 |
| 独立QA | gpt-6-luna | 619 | 135 |

テスト用Pro契約 `sub_1ULJeYKGKycmoWoDzHWv97d5` は動作確認用として有効のまま。ローカルの既存QAアカウントで利用できる。実カード・実請求は使っていない。旧JPYテスト契約は終了済みのまま変更していない。

## テストと証跡

- APIの実PostgreSQL：token/proof-request回帰25件。tier・legacy・unsupported gate等は担当の記録で88件。重複する検証があるため合算しない。
- token換算・閉じた入力契約・起動配線40件。Stripe launcher25件、migration12件、focused API/HTTP98件。
- Agent関連229件と静的検査、実API schemaとのroundtrip。これらのHTTP doublesは上記の実OpenAI検証とは別。
- フロント全体1,041件、追加の状態更新75件・残量縮小47件、typecheck・lint・Next build成功。追加ケースとの重複あり。
- 独立レビューでmigrationのNULL許容を修正。Checkout選び直しの追加レビューで重大指摘なし。既知予算不足の汎用エラーを修正し、関連89テスト・型検査を実行。最終workerで新しい上限1の依頼を再実行し、`token_budget_exceeded` と「失敗した依頼は利用枠を消費しません」の実画面表示を確認した。

スクリーンショットと秘密値を含まないJSONは `output/usd-plans-20260930/`。主なファイル：`plan-comparison.png`、`stripe-products.png`、`checkout-{plus,research,pro}.png`、`settled-usage.png`、`commutative-algebra-answer.png`、`verified-stripe-checkouts.json`、`generation-progress.json`、`after-budget-failure.json`、`final-runtime.json`、`budget-failure.png`。API・worker・Webを既存サービスへ適用済み。

## 残る範囲

これは新料金のローカル検証であり、新しい課金方針全体の完成ではない。現在の新台帳は自然言語回答の判断・構造化・検索埋め込み・回答・独立QAに接続済み。正式なLean証明、部分質問、説明再試行は未計測なので新USDプランで新規実行を拒否する。既存結果の閲覧と旧契約の処理は維持する。

資料添付、inline画像、資料読取り枠、有料限定Project作成の全体整合、Free/無償Proのtoken移行、Research専用の実行時間、税・本番運用・アップグレードの適用日、全利用分布と失敗原価を含む採算検証は別途必要。本番販売可能・全機能完成とは判定しない。
