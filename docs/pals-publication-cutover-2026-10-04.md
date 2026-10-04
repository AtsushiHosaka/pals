# PALSのWeb・API公開切替の記録

2026年10月4日。MacBookでCloudflareの既存Tunnelへ通常Web/APIの2経路を保存し、
07:19 UTC（16:19 JST）から外部HTTPSで到達と認証境界を確認した。
公開先は <https://palschat.site/signin> と <https://api.palschat.site>。

## 実行の根拠とMiniの受け口

通常公開の親担当から、本人の16:16 JSTの実行直前確認
「外部からアクセスできるようにしよう！」を受領した。
確認の対象は既存Tunnelの起動、Web 13000/API 18000の2経路と対応DNS。
本人が通常ログインを確認した後、追加E2Eの完了待ちを公開の前提から外すという最新指示を優先した。
[公開準備時点の文書](macbook-publication-preparation-2026-10-04.md)の未公開状態・E2E待機条件は、
この切替より前の記録として保持する。

Mini担当から署名済みcanonical Web `sha256:29461f86048286e9c567389ef783d12fc26a71e43d3241929cc88306487c8735`
への復帰、`Caddyfile.production`、各Hostと13000/18000、正常6経路の匿名401・拒否77件の404を報告された。
既存connectorは16:17:21 JSTに起動し、ready HTTP 200、nrtへの4接続という報告である。
MacBook担当はMiniの署名配備・connector資格情報を扱わず、以下のCloudflare保存と外部接続を直接確認した。

## 保存した対象と読み取り確認

Cloudflare account `e792ca2e954ad6da854305c109d17d75`、zone `palschat.site`、
既存Tunnel `mac-mini-m1-2020` / `aa7c15fc-5b2c-429c-85cd-0500b0955f27`。

| 公開ホスト | サービス | HTTP Host Header | パス |
| --- | --- | --- | --- |
| `palschat.site` | `http://127.0.0.1:13000` | `palschat.site` | 全体 |
| `api.palschat.site` | `http://127.0.0.1:18000` | `api.palschat.site` | 全体 |

両経路ともchunk encodingを無効化する設定はオフ。catch-allは `http_status:404`。
Webの保存成功とDNS自動作成の通知を確認した後、最新Tunnel設定でAPIフォームを再読込して追加した。
保存後の公開ルート一覧には上表の2件が残った。

DNSはルート保存時に自動作成され、別レコードを重複追加していない。
DNS一覧を再読込し、root/APIの2件ともTunnel `mac-mini-m1-2020`、プロキシ済み、TTL自動を確認した。
既存ACM検証CNAMEはDNSのみ・TTL5分で残り、計3件である。
旧Route 53 zone、ACM、NS、AWS資源、他ドメイン、Cache Rules、SSL/TLS設定を変更する操作は今回の範囲に含めていない。
APIの公開はMiniの既存allowlistを通し、CIMD/OAuth/MCPの追加経路は公開していない。

## MacBookからの外部HTTPS検証

資格情報・Authorization・個人アカウントを使用しない読み取り検証である。
両ホストのDNSは `104.21.9.220` / `172.67.131.11` を返した。
通常のCA・hostname検証を有効にしたTLS 1.3接続が成功し、証明書SANは
`*.palschat.site` / `palschat.site`、期限は2027年1月2日04:44:37 UTC。

| 確認 | 結果 |
| --- | --- |
| Web `GET /signin` | 200。実ChromeでもPALSログイン画面を確認 |
| API `GET /v1/projects`, `/v1/chats` | 匿名401 |
| API `/docs`, `/openapi.json`, `/metrics`, `/v1/internal/health` | 404 |
| API `/mcp`, `/oauth/mcp/authorize`, `/.well-known/oauth-authorization-server`, `/.well-known/oauth-protected-resource/mcp` | 404 |
| `OPTIONS /v1/projects`、Origin `https://palschat.site` | 200、Allow-Origin一致 |
| 同OPTIONS、Origin `https://example.net` | 400 |
| API・拒否経路・CORSのキャッシュ | `Cache-Control: no-store`、`CF-Cache-Status: DYNAMIC` |

13件すべて期待statusと一致した。Web signinは `CF-Cache-Status: DYNAMIC`。
今回の外部合格はHTTPS到達と上表の匿名境界であり、認証後SSE・質問の回答・保存/利用量・回答後復元の合格を意味しない。
これらは親担当とMini担当が公開後に続ける。

秘密を含まない詳細結果と画像は、MacBookの `/tmp/pals-macbook-public-prep-20261004/` に保存した。

- `public-https-result.json`
- `pals-public-signin-https-20261004.jpg`
- `tunnel-two-routes-saved-20261004.jpg`
- `dns-two-proxied-records-saved-20261004.jpg`

## 復旧の対象

今回の公開を停止する場合は、上表の2公開ルートと自動作成されたroot/API DNSだけを対象にする。
保持ACM CNAME、旧Route 53、NS、既存Tunnelとtokenは削除しない。
ルート削除とDNS削除は別に照合し、必要ならMini担当が既存connectorを停止する。
アプリを戻す場合はMini担当の保存済み旧構成を使い、DB/volumeを削除せず、署名と配備対象を照合する。
この文書は復旧対象の記録であり、停止・削除操作を実行した記録ではない。
