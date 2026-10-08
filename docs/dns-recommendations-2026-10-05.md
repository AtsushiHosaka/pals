# palschat.siteのDNS推奨事項への対応記録

2026年10月5日11:56 JST時点。CloudflareのDNS画面で「設定完了」「推奨事項はありません」を確認した。
`www.palschat.site`から正式URLへの転送と、メール不使用の設定を追加した。
利用者は、このチャットでドメインのメールを「送信・受信とも使わない」と回答した。

## 通常のWeb・APIは公開済みだった

画像と既存ブラウザータブには公開前の情報が残っていた。
再読み込み後は、`palschat.site`と`api.palschat.site`のプロキシ済みTunnelレコードを確認できた。
この2件は[10月4日の公開記録](pals-publication-cutover-2026-10-04.md)と一致する。
既存のTunnel経路、ACM検証CNAME、SSL/TLS設定は変更していない。

## wwwはCloudflareで正式URLへ転送する

| 項目 | 保存した値 |
| --- | --- |
| DNS | A `www` → `192.0.2.0`、プロキシ済み、TTL自動 |
| ルール名 | `www.palschat.site → palschat.site` |
| ルールID | `5e8e1541391e4b29886bce5bd7842ae3` |
| 条件 | `http*://www.palschat.site/*` |
| 転送先 | `https://palschat.site/${2}` |
| 応答 | 301、クエリ文字列を保持 |

最初のワイルドカードはHTTP/HTTPSの違いを吸収し、2番目はパスを引き継ぐ。
`192.0.2.0`は転送専用の予約アドレスで、実サーバーのIPではない。
Cloudflareのプロキシがリダイレクトを返す構成は、[公式の転送用DNS設定](https://developers.cloudflare.com/workers/configuration/routing/custom-domains/#redirect-between-www-and-root-domain)に従った。
この構成では、www用のTunnel経路を追加する必要がない。

## メールの受信とドメインを使った送信を拒否する

| 種類 | 名前 | 内容 | TTL |
| --- | --- | --- | --- |
| MX | `palschat.site` | 優先順位0、宛先`.` | 自動 |
| TXT | `palschat.site` | `v=spf1 -all` | 自動 |
| TXT | `*._domainkey.palschat.site` | `v=DKIM1; p=` | 自動 |
| TXT | `_dmarc.palschat.site` | `v=DMARC1; p=reject; sp=reject; adkim=s; aspf=s;` | 自動 |

TXTの3件は[Cloudflareのメール不使用向け設定](https://developers.cloudflare.com/dns/manage-dns-records/how-to/email-records/#prevent-domain-spoofing)で追加した。
受信しないことを明示するNull MXは、[RFC 7505](https://www.rfc-editor.org/rfc/rfc7505.html)に従って別途追加した。
DMARCの拒否方針はサブドメインにも適用する。レポート送信先は登録していない。
これらは対応するメールサーバーへの拒否指示であり、すべての受信者の処理を保証するものではない。
Cognitoの既定メール送信は、このドメインを送信元にしない既存設定のままである。

## 公開DNSとHTTP応答で保存結果を確認した

Cloudflareの権威DNS `ignacio.ns.cloudflare.com`で、MX・SPF・DMARCと任意セレクターのDKIM拒否応答を確認した。
Cloudflare `1.1.1.1`とGoogle `8.8.8.8`でも、wwwがプロキシIPを返した。

| 確認 | 結果 |
| --- | --- |
| HTTPS www `/signin?dns-check=20261005` | 301 → `https://palschat.site/signin?dns-check=20261005` |
| HTTP www 同パス | 同じ転送先に301 |
| 正式Web `GET /signin` | 200 |
| API `GET /v1/projects`、認証情報なし | 401 |
| DNS画面、再読み込み後 | 推奨事項なし、レコード8件 |

HTTP/HTTPSの転送は、権威DNSが返したCloudflare IPを指定して確認した。
続けてCloudflareのDNS over HTTPSを使い、HTTPS転送を確認した。TLSの証明書検証は有効にした。
手元の通常リゾルバーには追加前の否定キャッシュが残り、確認時点ではwwwを解決できなかった。
公開DNSとCloudflare側の反映は確認済みだが、すべての端末でのキャッシュ更新時刻は確認していない。
今回の確認はDNSと転送、既存Web/APIの匿名到達に限る。認証後の機能検証は含まない。

完了画面はローカルの`/private/tmp/pals-dns-recommendations-complete-20261005.jpg`に保存した。
今後メールを使う場合は、Null MXと拒否用TXTを見直し、メール事業者が指定するレコードへ切り替える必要がある。
