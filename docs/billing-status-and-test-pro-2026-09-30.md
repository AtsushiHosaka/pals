# 料金・Stripe・無償Proの実装状況

2026-09-30。稼働中の回数制、新しい料金案、管理者向け無償Proを分けて記録する。

## 現在のStripe接続

実装は `pals-api/app/infrastructure/billing/stripe.py` と `billing_operations.py`、`app/api/routes/billing.py` にある。APIがCheckout/Portalを作成し、Webhook署名・重複・順序・所有者bindingを検証して有料契約の状態を反映する。課金設定がない場合は503で拒否する。

ローカル環境はStripe未設定。以前のUI検証は未設定時のエラー通知までであり、実Stripeのテスト決済→Webhook→Pro→解約を通した証拠ではない。公開Checkoutは実設定・運用条件と実接続確認が必要。

## 現行と料金案

| 状態 | Free | Pro |
|---|---|---|
| 現在のコード | 累計3回 | 月1,500円、請求期間100回 |
| 改定候補A（未適用） | 累計10万利用token | 月1,500円、月100万利用token、原本1GB、月1,000ページ読取り |
| 改定候補B（未適用） | 同上 | 月2,980円、月300万利用token、原本3GB、月2,000ページ読取り |

現在の回数制は受付時消費で失敗も戻らない。ユーザーが承認した次期方針は、全工程の換算利用token・事前上限・説明とQAの成功時実績精算・失敗消費0。これを現在実装済みとは扱わない。料金候補の原価・上限評価も未完了。詳細は[料金案](proposals/project-materials/pricing.md)。

## 無償Proの契約

通常のCognitoアカウントへ、管理者が支払い不要のPro資格を付与する。新たな公開登録用の特権や、共有パスワード、自己昇格APIは作らない。

- 対象はCognitoで存在・有効状態を確認したアカウントのsubject。メールだけを料金のidentityにしない。
- 期限と理由を明示して付与し、管理者のDBログインidentityと変更履歴を残す。無期限・自動更新なし。
- 現制度の通常100回枠を付与期間に適用。消費や失敗の扱いも現制度と同じで、無制限にはしない。
- 同じ付与の再実行は枠をリセットせず、重複する有効資格は拒否する。
- 有効な有料Stripe Proがあればそちらを使い、両方の100回枠を合算しない。
- 取消・期限切れ後の新規処理は既存Free残量へ戻る。過去のチャット・証明・受付済jobは維持する。
- 画面には「無償Pro」と期限を表示し、その資格に月額請求・自動更新・Stripe管理を表示しない。
- Stripe契約を作ったことにはしない。Stripeの接続確認にも代用しない。

実利用者への付与は対象アカウントと期限が未指定のため行っていない。利用者は通常の登録・ログインを行い、運営がその既存アカウントへ資格を付与する。

## 管理操作

実行場所は `pals-api/`。`PALS_BILLING_OPERATOR_DATABASE_URL` には専用LOGINの接続先を秘密管理から設定する。そのLOGINには `pals_billing_test_admin` を付与し、APIのruntime権限を併用しない。利用者画面から自己付与する機能はない。

DBリリース前の管理者bootstrapがNOLOGINの管理ロールを用意し、通常の権限制限されたmigrationはその属性を検証する。既存v3環境でも、この事前設定が必要。ローカルの明示的release adapterも同じ前提を準備する。API起動時にDDLは実行しない。

APIと同じ `PALS_COGNITO_USER_POOL_ID` と `PALS_COGNITO_ISSUER` を設定する（`COGNITO_*` aliasにも対応）。AWS上では対象poolの `ListUsers` 権限が必要。ローカルの場合のみ `PALS_COGNITO_ENDPOINT_URL` を指定でき、issuerと同じloopback originに限定する。

```sh
python -m app.release.billing_test_entitlement grant \
  --subject '<登録済みアカウントのsub UUID>' \
  --grant-id '<この付与に固定するUUID>' \
  --expires-at '<期限のISO8601。タイムゾーン必須>' \
  --reason '<付与理由>'

python -m app.release.billing_test_entitlement list \
  --subject '<登録済みアカウントのsub UUID>'

python -m app.release.billing_test_entitlement revoke \
  --grant-id '<取り消す付与のUUID>' \
  --reason '<取消理由>'
```

同じgrant IDと同じ内容の再実行は消費枠を初期化しない。新しいgrant IDでも有効期間が重なる付与は拒否する。実行者はDB接続の `session_user` として記録され、CLI引数で偽装しない。

## 検証記録

- API unit 962件、HTTP/story 429件成功。関連PostgreSQL試験27件成功に加え、通常の `NOCREATEROLE` 接続によるv3→v4更新と旧消費履歴保持を確認。
- フロントエンドは独立レビューの全unit 908件成功。対象48件、型検査、lint、production buildも成功。
- 課金migration manifest SHA256: `cc4aefd8810e78061d4192a92df87377e13b8c273ac841cf2f03ee151f479b4b`。
- 既存 `pals-local` へ明示的schema releaseを適用し、9サービスのhealthyを確認。Chromeも既存タブを再利用。
- 既存のローカルQAアカウントに20分の資格を実CLIで付与。Cognito emulatorの登録確認→実PostgreSQL→実API→実画面で `complimentary`、100回、期限、支払・自動更新なしを確認。同一コマンドの再実行でも同じ結果。
- 実CLIで取消後、元のFree残量1回へ復帰。一時operator LOGINと秘密状態ファイルも削除済み。取消後の最初のAPI確認は別のローカル更新処理による接続切断で失敗したが、更新後に読み取り再検証し、取消・role削除・Free復帰の全てを確認した。
- 実画面は `output/complimentary-pro-20260930/complimentary-pro-desktop.png` と `revoked-free-desktop.png`、実API記録は同ディレクトリの `grant-runtime.json` / `cleanup-runtime.json`。付与画面のconsole warning/errorなし。証明生成や利用枠の消費は行っていない。
- Stripe実接続、有料プランの実決済、AWS Cognito本番接続はこの検証に含まない。
