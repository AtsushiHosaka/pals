# 公開版の新規登録禁止を解除し、パスワード案内を本番条件に合わせる

2026年10月8日、公開版の登録失敗を調査した。本番Cognitoは管理者招待だけを許可しており、登録画面からのSignUpを拒否していた。00:38 JSTに、この制限だけを解除した。既存ユーザー、確認メール、パスワード条件を含む他の設定は保持されている。

## 登録APIと実設定で原因を確認した

対象はAWS account `828786775577`、region `ap-northeast-1`、User Pool `pals-mini-prod`（`ap-northeast-1_CnwrhavzI`）。公開Web App Clientは `4u13065h7ai6d7f6j8km19k7uc`。

変更前のSignUpはHTTP400、`NotAuthorizedException`、`SignUp is not permitted for this user pool`を返した。認証後のDescribeUserPoolでも `AdminCreateUserConfig.AllowAdminCreateUserOnly=true` を確認した。

ユーザーの修正依頼に基づき、値をfalseに変更した。UpdateUserPoolは省略項目を既定値に戻すため、取得した設定を更新APIの入力形式へ変換し、既存の更新可能な設定を引き継いだ。対象account・Poolを照合し、変更直前の再取得で設定の同時変更がないことを確認した。変更後のDescribeUserPoolは、更新日時とユーザー数の集計値を除き、対象フラグだけが異なることを照合した。

本番Poolはproduction Terraformのstateに含まれていないと[10月4日の記録](cognito-email-format-2026-10-04.md)に記載されている。Terraform側の宣言はすでに新規登録を許可しているため、今回その値を変更したり、production root全体をapplyしたりしていない。Pool・Clientの再作成やユーザー削除も行っていない。

## 画面が本番の接続先をローカル認証と誤判定していた

実際のパスワード条件は、14文字以上で英大文字・英小文字・数字・記号が必要だった。ところが公開画面は「8文字以上、小文字と数字、記号は任意」と表示していた。登録禁止の解除後も、13文字のテスト入力に対し同じ誤った条件でパスワードエラーを案内することをブラウザーで確認した。

原因は、Webの `lib/auth/passwordPolicy.ts` が `NEXT_PUBLIC_COGNITO_ENDPOINT` の値があるだけでローカル認証と判定していたこと。本番AWSの明示的な接続先も、この条件に該当していた。

修正後はHTTP(S)の `localhost`、`127.0.0.1`、`[::1]`、`cognito-local` のみをローカル用として扱う。AWSやその他の接続先は本番の案内・入力最小長・パスワードエラー表示を使う。既存のサインイン画面の言語選択削除は保持した。

認証関連の3ファイルで39テストが成功した。追加した10ケースでは、AWS・中国リージョン・その他のホスト・不正なURL・ローカル接続先ごとの登録画面とエラー案内を確認した。変更ファイルのESLint、型検査、diff検査も成功している。

## 再発確認は実際のPoolを対象にする

読み取り確認には以下を使う。結果はfalseであることを確認する。

```sh
aws cognito-idp describe-user-pool \
  --profile pals-prod-member --region ap-northeast-1 \
  --user-pool-id ap-northeast-1_CnwrhavzI \
  --query 'UserPool.AdminCreateUserConfig.AllowAdminCreateUserOnly' \
  --output json
```

登録画面の案内が14文字以上・大文字・小文字・数字・記号を要求することも確認する。テストアカウントの登録・メール確認・ログイン成功は、指定されたパスワードが本番条件を満たしてから別途確認する。設定修正と認証関連テストの成功だけで、ログイン後のチャットやプロジェクト機能の合格とは判定しない。

APIエラー・変更前後の設定hash・ブラウザー画面はローカルの `outputs/dogfood/2026-10-07-math-model-projects/` に保存した。認証情報、確認コード、設定の全量、ログ、生成物はGitへ含めない。
