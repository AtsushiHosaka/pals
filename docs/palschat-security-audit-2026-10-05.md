# palschat.siteはHTTPS強制と公開設定の補強が必要

2026年10月5日14:36〜14:44 JSTに、公開Web/APIと既存ソースを調査した。
HTTPでログイン画面が表示され、TLS 1.0・1.1も受け付けていた。
ブラウザーの防御ヘッダーも不足している。まずCloudflareのHTTPS強制と最小TLS設定を直す。
確認した範囲では、認証突破や秘密情報の公開は実証していない。
ただし、本番ホスト内部とユーザー間の分離は実機で未検証のため、安全との総合判定は出さない。

## 公開環境で3件の設定不備を確認した

重大度は今回確認した条件での評価であり、侵害の発生を示すものではない。

| ID | 重大度 | 結果 | 対象と根拠 | 影響・修正方針 |
| --- | --- | --- | --- | --- |
| SEC-001 | 高 | FAIL | `http://palschat.site/`と`/signin`が200。HTTPSへのLocationなし。HTTPS応答にHSTSなし | 通信経路上の攻撃者がページを改変し、偽のログイン処理を実行する余地がある。CloudflareでHTTP→HTTPSを強制し、HTTPS確認後にHSTSを設定する |
| SEC-002 | 中 | FAIL | WebはTLS 1.0・1.1指定で接続成功。APIもTLS 1.0のハンドシェイク成功 | 古い暗号方式を受け付ける。Cloudflareの最小TLSを1.2以上にする |
| SEC-003 | 中 | FAIL | HTTPSの`/`・`/signin`にCSP、frame制限、nosniffなし | 他サイトのframeへの埋め込みを防ぐ指示がなく、XSS発生時の追加防御も不足。CSPの`frame-ancestors`とスクリプト制約、`X-Content-Type-Options: nosniff`を設定する |

SEC-001の問題はHTTPでページを受け取る利用者への改変リスクである。
API接続先をHTTPSに制限する実装があっても、ページ自体の改変は防げない。
HTTPSで接続している利用者の通信が、この観測だけで平文になるとは判断していない。

SEC-002はcurlの成功コードだけでなく、詳細ログの実ネゴシエーションも確認した。
WebのTLS 1.0は`TLSv1 / ECDHE-ECDSA-AES128-SHA`、TLS 1.1は`TLSv1.1`だった。
APIのTLS 1.0も同じ暗号方式で接続したが、`/health`の応答は404だった。
通常HTTPSの`/health`は200で、本番環境を示すJSONを返した。
APIについては古いTLSの受付を確認したのであり、全機能の動作は確認していない。

SEC-003は実際のXSSやクリックジャッキングを実証した結果ではない。
ソースの[`next.config.mjs:8`](https://github.com/AtsushiHosaka/pals-webfront/blob/bb36ac34bec6201ccc6657f61ab15b560e5010ed/next.config.mjs#L8)も、共有ページ用ヘッダーだけを設定しており、公開応答と一致する。
通常ページのReferrer-Policyも未設定だった。
認証・Cognito・API・SSE・Nextのスクリプト動作を確認しながらCSPを導入し、安易に全originや全inline scriptを許可しない。
HSTSのサブドメイン適用とpreloadは、対象すべてのHTTPS対応を確認してから判断する。

## 認証なしのアクセスと内部経路は拒否された

次は認証情報・実データIDを使わない外部確認である。
個別経路の拒否を確認した結果であり、全経路の遮断を保証するものではない。

| 確認 | 今回の結果 | 判定 |
| --- | --- | --- |
| API `/v1/projects`、`/v1/chats`、認証なし | 401、`auth_required` | PASS |
| API `/v1/projects`、明らかに無効なBearer | 401、`auth_token_invalid` | PASS |
| API `/docs`、`/openapi.json`、`/metrics` | 404 | PASS |
| API `/v1/internal/health`と`/v1/%69nternal/health` | 404 | PASS |
| API `/mcp`、`/oauth/mcp/authorize` | 404 | PASS |
| CORS preflight、Origin `https://palschat.site` | 200、Allow-Originが一致 | PASS |
| 同preflight、Origin `https://example.net` | 400、Allow-Originなし | PASS |
| 上記APIの認証拒否・遮断・CORS応答 | `Cache-Control: no-store`、`CF-Cache-Status: DYNAMIC` | PASS |
| Web `/.env`、`/.git/config` | 404、通常のHTMLエラーページ | PASS |

ゲスト要求の読取経路への匿名GETはedgeで404だった。
ゲストセッションの作成や質問の送信は実施しておらず、ゲスト機能の本番有効化・費用上限は未検証である。
ログイン画面の`Cache-Control: s-maxage=31536000`は静的な匿名ページに対する値で、今回の応答はDYNAMICだった。
これをユーザー情報のキャッシュ漏えいとは判断していない。

## ソースでは防御を確認したが、依存更新と実行隔離に課題が残る

### Next.jsは既知の修正より古い

Webの`package.json:24`とlockはNext.js 16.2.9、lockのsharpは0.34.5だった。
[公式AVIF画像処理の勧告](https://github.com/vercel/next.js/security/advisories/GHSA-2xp9-vwfh-vxw4)はNext.js 16.3.3未満を影響範囲とする。
画像最適化へのAVIF入力を条件として、認証なしのコード実行につながる問題である。
確認したソースにはremotePatternsや`next/image`の利用、攻撃者が画像を供給する経路を見つけていない。
本番イメージのバージョンも未照合のため、サイトで悪用可能とは断定しない。
判定は「ソースの更新遅れを確認、本番の影響はNOT VERIFIED」とする。

Next.jsは[16.3.8の公式リリース](https://github.com/vercel/next.js/releases/tag/v16.3.8)までのセキュリティ修正を確認し、依存全体を検査して更新候補を選ぶ。
修正後はproduction build、認証、公開・共有ページ、SSEの回帰確認が必要になる。
[Server ActionsによるDoS勧告](https://github.com/vercel/next.js/security/advisories/GHSA-m99w-x7hq-7vfj)も確認したが、今回のソース・既存buildにはServer Actionsがなく、この経路の適用は確認できなかった。

### Leanの実行制限に、静的検査を通る経路がある

Agentの[`lean.py:30`](https://github.com/AtsushiHosaka/pals-agent/blob/eb62c0862f0f62b282711a84274ff704158d258c/pals_agent/lean.py#L30)はメタプログラミングの一部を拒否するが、`run_tac`を拒否していない。
既存Lean 4.32.0で、ログに無害な固定文字列を出すだけの`run_tac`が実行され、`lean.verified`になった。
`#eval`が拒否されることとの比較も確認した。
[Lean公式リファレンス](https://lean-lang.org/doc/reference/latest/Tactic-Proofs/Tactic-Reference/)は`run_tac`がTacticMを実行することを説明している。

Linuxの[`lean_child.py:137`](https://github.com/AtsushiHosaka/pals-agent/blob/eb62c0862f0f62b282711a84274ff704158d258c/pals_agent/lean_child.py#L137)は書込先を制限する一方、`/`全体への読取・実行を許可する。
予定のAWS構成では、verifierサービスのTLS資格情報を同じコンテナへmountする。
その構成でコンパイル中のコードが資格情報を読める可能性があるため、読取allowlistと資格情報を持たないコンパイル環境への分離を優先する。
禁止語の追加だけで任意コードの実行を封じたとは判断しない。

静的制限の欠落はFAIL、本番への到達と影響はNOT VERIFIED。
本番launcherがnatural-onlyを要求するという[10月5日の記録](worker-lane-isolation-2026-10-05.md)があり、現行サイトでLeanがどこから実行されるかは未照合である。
秘密ファイルの読取、ネットワーク通信、他プロセスへの操作は試していない。

### 本文を全部読み込んでから制限する箇所がある

APIの`app/api/routes/proof_requests.py:49`は本文を全読込後に1 MiBを検査する。
`chat_shares.py:27`は公開GETの本文を全読込し、`internal.py:270`は機械認証の選択前に本文を読む。
本番edgeの本文サイズ・同時接続・時間制限を確認できていないため、可用性への影響はNOT VERIFIED。
上限付きのストリーム読込とedgeの上限を組み合わせ、内部経路では可能な限り先に認証する。
負荷をかける再現試験は実施していない。

## 認証・表示・ゲスト上限は既存テストで確認した

Webの既存テスト57件、APIの認証・ゲスト関連34件が成功した。
これはローカルの単体検証であり、本番の認証済みユーザー2人による試験ではない。

| 境界 | 確認した制御 | 証拠と限界 |
| --- | --- | --- |
| JWT→ユーザー認証 | RS256、issuer、access token用途、client IDを検査。設定不足は起動拒否 | API `app/core/auth.py:42`。単体検証と外部の匿名・無効token拒否。本番の正常tokenは未試験 |
| OAuth→ログイン完了 | PKCE S256、乱数state、callback state一致、外部return URL拒否 | Web `lib/auth/cognitoOAuth.ts:53`、`components/AuthProvider.tsx:901`、`lib/auth/returnPath.ts:5`。単体検証 |
| LLM・利用者の文章→DOM | raw HTMLを文字列化、links/images除去、tag/property allowlist、KaTeX trust:false | Web `lib/learnerRichText.ts:276`、`:427`。攻撃的HTML/URLを含む既存テスト成功 |
| JS→認証資格情報 | sessionStorageへ保存 | Web `AuthProvider.tsx:197`、`lib/auth/cognitoSessionStorage.ts:29`。XSSが成立すればtoken読取が可能。XSS自体は実証していない |
| ユーザーID→チャット・資料 | 所有者に絞る問合せ、共有の明示snapshot、取消、256-bit共有token | ソース確認。本番の他ユーザーIDを使う拒否試験は未実施 |
| 匿名入力→モデル利用・DB | ゲスト本文32 KiB、Origin検査、hashed token、HttpOnly/SameSite/本番Secure cookie、DBでglobal/network/session上限 | ソースと単体テスト。実DBの競合・本番proxy IP信頼境界は未検証 |
| Lean→OS | 資源上限、Linuxのsocket syscall拒否、書込先制限、出力量上限、process group終了 | ソース確認。読取範囲の問題と本番環境の未確認が残る |

## 本番ホスト内部の確認が残る

本番Mac miniへは今回接続していない。
次の証拠が揃うまでは、内部設定や運用をPASSにしない。

- 配備済みWeb/API/worker/verifierのimage digestとソースcommit。
- 実Caddy設定、本文・同時接続上限、内部経路の全allowlist。
- ユーザー2人によるチャット・資料・共有・SSEの権限分離。
- guestの本番有効化、trusted proxy、日次global cap、課金・レート制限。
- コンテナの秘密mount、UID、read-only、権限、ネットワーク、メモリ・PID上限。
- AWSの現行IAM/S3/SQS設定、資格情報更新、バックアップ復元。

[10月4日の準備記録](macbook-publication-preparation-2026-10-04.md)はS3非公開・暗号化・versioningと用途別IAMを記録するが、今回の現在値ではない。
[機械認証の記録](mac-mini-machine-auth.md)には資格情報失効でworkerが停止した履歴と移行中の項目がある。
これは可用性の確認事項であり、認証突破の証拠ではない。
バックアップ復元の完了証拠も今回見つけておらず、バックアップが存在しないとは断定しない。

## 再現条件と調査対象

公開確認はcurl 8.7.1、通常のCA・hostname検証を有効にしたGET/HEAD/OPTIONSだけで実施した。
各通信は5〜25秒の上限付きで、並行する負荷試験は行っていない。
実アカウント、秘密値、質問送信、データ更新、設定変更は使っていない。
Python urllib経由では通常画面も一律403となり、curlの結果と一致しなかったため、判定にはcurlの結果を採用した。

```sh
curl -sS --connect-timeout 5 --max-time 10 -D - -o /dev/null http://palschat.site/signin
curl -sS --connect-timeout 5 --max-time 10 -D - -o /dev/null https://palschat.site/signin
curl -v --tlsv1.0 --tls-max 1.0 --connect-timeout 5 --max-time 10 -I https://palschat.site/
curl -v --tlsv1.1 --tls-max 1.1 --connect-timeout 5 --max-time 10 -I https://palschat.site/
curl -sS --connect-timeout 5 --max-time 10 -D - https://api.palschat.site/v1/projects
```

監査開始時の親リポジトリは`bfe488ce5dc6b03f8cad4eb6e6cdc943b7c30630`、cleanだった。
実装submoduleはこのworktreeで未展開のため、既存のDesktopチェックアウトを再利用した。

| リポジトリ | 読み取り対象HEAD |
| --- | --- |
| pals-api | `0f4b3ccde16f51d9f15fabd7a140a2e9dd425bd8` |
| pals-webfront | `bb36ac34bec6201ccc6657f61ab15b560e5010ed` |
| pals-infra | `fc3b9653064aa1fabcdc28c015613671a9e02fb0` |
| pals-agent | `eb62c0862f0f62b282711a84274ff704158d258c` |

実装チェックアウトには他作業のtracked/untracked変更がある。
指摘した主なソース箇所はHEADとの差分がないことを照合した。
それらの変更は編集・stage・commitしていない。
一時的な応答・診断は`/private/tmp`だけに保存し、生成出力や秘密情報をGitへ追加しない。
この監査の変更は本報告書だけであり、サイトの設定修正・配備は実施していない。
