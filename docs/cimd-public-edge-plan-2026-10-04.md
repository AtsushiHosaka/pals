# CIMD接続確認用の追加公開経路案

2026-10-04。CIMD担当から受領した依頼を、既存の通常PALS公開と別にレビューするための案。
この文書を作成してもedge、DNS、Tunnel、Cognito、DBは変更しない。
通常公開の親担当は、CIMDを通常ログイン・Send・保存・利用量・復元の必須条件に追加しないよう指示している。
CIMD担当はユーザーの実接続要求に含まれる範囲と報告したが、外部edgeへの同時追加は公開担当間で正確な対象を確定し、実行直前に承認を照合する。

## 担当と配備の境界

- MacBook公開担当: 既存Cloudflare DNS/Tunnelと公開後の外部HTTPS確認。外部設定の変更を一元化する。
- Mini担当: ローカルedge、接続先port、署名付き追加release、DB migrationと権限、loopback検証。
- CIMD担当: exact-baseの非秘密patch・manifest、専用client/resource/role設定の証拠、保持中のホスト設定ダイアログ、実OAuth確認。

Miniの同期済みAPI baseは `c0062c38eb6bef3b470cb827a2ded869700fd051`。
共有MacBook checkoutは他担当の変更で進んでいるため、HEADやdirty全体をMiniへ同期しない。
base/after SHA・archive SHA、migration・role・client・公開経路一覧を渡し、stagingと別DBで確認した署名付きchild releaseを使う。
既存checkout、通常release、稼働DB、会計データを保持する。
API upstreamは `127.0.0.1:8000`。Tunnelの接続先は、Miniが検証したローカルedgeの別portとし、APIを直接指さない。

## API hostnameだけへexact pathとmethodを追加する

対象hostnameは `api.palschat.site` だけ。通常Web hostnameには追加しない。

| method | exact path | 確認する応答 |
| --- | --- | --- |
| GET | `/.well-known/oauth-authorization-server` | PALS issuer、正確なauthorize/token/revoke endpoint、S256、CIMD対応 |
| GET | `/.well-known/oauth-protected-resource/mcp` | resource `https://api.palschat.site/mcp`、PALS authorization server、Bearer header方式 |
| GET | `/oauth/mcp/authorize` | callback・CIMD・resource・scope・PKCE検査後に同意画面 |
| POST | `/oauth/mcp/consent` | 正確なOriginとnonce Cookieの検査。承認時303、取消・期限切れ・再送の拒否 |
| POST | `/oauth/mcp/token` | native code交換とrefresh検査。秘密値を記録しない |
| POST | `/oauth/mcp/revoke` | access/refresh family失効と再利用拒否 |
| POST | `/mcp` | 認証、initialize/ping/tools一覧、全tools/call拒否 |
| GET / DELETE | `/mcp` | APIまで通し、未認証のchallenge、認証後405・`Allow: POST`を保持 |

`/.well-known/*`、`/oauth/*` のprefix全体や、未要求の `/.well-known/oauth-protected-resource` aliasは追加しない。
OPTIONSが必要になった場合は上表のexact pathだけを対象にし、既存CORSとの実照合後に追加する。
他method、末尾slashやencoded/dot pathによる迂回、隣接pathが通らないことをedgeの負例で確認する。
`/v1/internal/*`、docs/openapi/redoc、release/DB/admin、Stripe関連は引き続き公開しない。

## 転送・キャッシュ・受信上限

OAuthとmetadataの成功・エラー・redirect全てで `Cache-Control: no-store` を保持する。
OAuthの `Pragma: no-cache`、`Referrer-Policy: no-referrer`、`X-Content-Type-Options: nosniff` も保持する。
API hostnameのcache bypassと組み合わせ、Cookie、Authorization、Origin、WWW-Authenticate、Location、Allowを改変しない。
HTTPSを終端する場合は実際のHostとHTTPS schemeを正しく渡し、ブラウザへ返すCookieはSecure/HttpOnly/SameSite=Laxと正確なpathを保持する。

OAuth POSTは `application/x-www-form-urlencoded`、body上限32,768 bytes、読み取り10秒をアプリ実装と合わせる。
MCP POSTの上限は262,144 bytes。edgeが大きいbodyを認証処理前に拒否し、境界値と超過時の応答を検証する。
OAuth query/form、Cookie、Authorization、code、token、nonceをaccess log・traceへ保存しない。
MCPはbuffer・cacheを避け、JSON応答と将来のstream応答の転送を妨げない。
connection checkで返る通常JSONや認証後405は、SSE成功の証拠として扱わない。

## 接続確認だけを有効にする

署名対象の構成で以下を明示する。

```text
PALS_CIMD_ENABLED=true
PALS_CIMD_CONNECTION_VERIFICATION=true
PALS_EXTERNAL_ENABLED=false
```

全 `tools/call` を `external_connection_check_only` で拒否し、provider、worker、外部ツールservice、課金処理を呼ばない。
実DBで認可用途 `connection_check` とtoken bindingを検査し、実行用途への再利用も拒否する。
試験前後で既存会計の行と利用量が一致することをMiniで確認する。
callbackはCIMD担当が保持する実ダイアログの値を使い、ダイアログを作り直さない。
実ブラウザのCreate、OAuth grant、本人のパスワード入力は担当と本人がその場で確認する。

## 公開前後の確認と戻し方

公開前にMiniで実Cognito Describe、署名・release admission、別DB migration、全tools拒否、通常PALS回帰、edgeの許可・拒否・body上限を確認する。
公開後は有効なHTTPS証明書、discovery2件、無tokenのMCP challenge、保持中のホストダイアログによるS256 code交換・refresh・失効を確認する。
外部互換性のフラグやfull toolsを、接続確認だけで有効にしない。

問題が起きたら今回のCIMD exact path追加だけをedgeから戻し、通常PALSのルートとDNSを保持する。
署名済み通常releaseへ戻す場合はDB/schema互換性を確認し、migration tables、稼働DB、会計、S3、queueを削除しない。
NSのみの承認や、Cognito専用client作成の承認を、このedge追加の承認として流用しない。

実装照合: `pals-api/app/api/routes/cimd_oauth.py`、`external_mcp.py`、`app/core/cimd_oauth_config.py`。
AWS追加設定の報告と未完了範囲はCIMD担当の `docs/cimd-connection-evidence-2026-10-04.md` にある。
この案の作成時には同記録が共有worktreeの未追跡ファイルだったため、この担当のcommitには含めない。
