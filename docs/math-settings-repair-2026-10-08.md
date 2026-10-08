# 数学設定の読み込み障害と修正候補

[pals #12](https://github.com/AtsushiHosaka/pals/issues/12) の修正候補を更新した。公開ルートの欠落を確認し、guest導入後に数学設定をリリースする手順と、画面のRetry処理を修正した。本番への適用と実ログイン後の確認は未実施。

## 公開ルートがAPIに届いていない

2026年10月8日12:11 JST、匿名の`GET https://palschat.site/v1/auth/me/math-conventions`はHTTP 404を返した。本文はNext.jsの「Page not found」で、`x-nextjs-*`ヘッダーも付いていた。数学設定のAPI応答ではないため、画面でRetryを押しても同じルートでは取得できない。本番DBの状態と、報告に使われたアカウントの応答は未照合。

## guest導入後の保存先と公開ルートを修正した

| リポジトリ | PR | 変更 |
|---|---|---|
| pals-api | [#4](https://github.com/AtsushiHosaka/pals-api/pull/4) | guestを含む26段階から、数学設定を含む27段階への署名付き更新を許可する。既存guestの鍵検証と通常起動時の読み取り専用確認を保つ。 |
| pals-infra | [#2](https://github.com/AtsushiHosaka/pals-infra/pull/2) | APIと同じ更新対象を署名する。既存のAPI Host制限内に数学設定のGET・PUT・OPTIONSだけを追加する。 |
| pals-webfront | [#8](https://github.com/AtsushiHosaka/pals-webfront/pull/8) | `503 math_conventions_unavailable`だけを未提供と判定する。一時的な503ではRetryを表示し、再取得後に設定一覧を表示する。 |

旧版の数学設定候補は25段階からの更新専用だった。今回の対象は、末尾に`guest-chat`を持つ26段階のregistryに限定する。他の保存先・署名済みartifactは変更しない。

前提registryのSHA-256は`fd52d186a91906d6194b3f4b3da8aaa90359d96759952f8c7d43b93ed144347e`、更新後は`476a3c53fca174031d705c2f323dc214cc94858ef544b3fe81368bf1267cd1dc`。APIとinfraのファイル実体・検証コードで一致を確認した。

## 検証と未確認事項

画面の数学設定テスト12件、TypeScript、ESLintは成功した。404・500・一時的な503からRetryで設定を表示する経路を検証した。全unitテストは1345件成功・2件失敗。失敗した`use-proof-job-events.test.tsx`の2件は、変更前のmainのコードでも再現した。

infraのcontroller・authorityテスト66件と、edge matcherテスト4件が成功した。公式Caddy 2.10.2でguestと数学設定を同じHost制限内に配置した候補を検証し、構文検査と実HTTP応答51件が成功した。数学設定の許可method、内部・不正pathの拒否、未知Hostの拒否、guestルートの保持を確認した。これは一時的なloopback上の候補であり、本番のCaddyfileを検証した結果ではない。

APIの関連テスト339件が成功し、41件は未実行となった。数学設定の追加テスト後にも15件が成功し、8件は未実行。Ruffと差分の空白検査も成功した。実PostgreSQLの検証には専用の空DBと隔離されたroleが必要で、既存の共有DBは使用していない。本番の署名、DB更新、実アカウントでの読み込み・保存・再読み込みは未検証。

## 本番適用後にissueの完了を確認する

適用手順は [infraの更新手順](../pals-infra/host/macmini-deploy/README.md) と [edgeの設置手順](../pals-infra/host/macmini-edge/README.md) に記載した。既存のguest設定を保ち、署名付きDB更新と数学設定のimportを適用する。匿名アクセスがAPIの401に到達し、実ログイン後に11項目を閲覧・保存・再取得できることを確認する。最後に読み込み失敗からRetryで回復する経路を確認して、#12の完了を判断する。
