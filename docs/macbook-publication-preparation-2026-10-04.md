# MacBook側の公開準備と読み取り結果

2026年10月4日。確認端末は `AtsushiHosakas-MacBook-Pro.local`。
Mini側の起動・本番認証・質問送信・復元試験は別担当が行う。
この作業では承認を受けてNSだけを変更した。公開ルート、IAM、資格情報、AWS資源は変更していない。

## 05:40 UTC頃の更新: NS保存とレジストリ委任を確認

通常公開の親担当から、ユーザーの実行直前承認を受領した。
対象はお名前.comの `palschat.site` 1件だけで、指定NSは
`ignacio.ns.cloudflare.com` / `nelly.ns.cloudflare.com` の2件。
再ログイン後、対象1件とNS2件の確認画面を照合して保存し、
`/domain/setting/ns/done` の「お手続きが完了しました」を確認した。
その後、ドメイン詳細へ再遷移してネームサーバー情報を読み直し、2件だけであることを確認した。

公開DNSから取得した現行 `.site` 権威DNSは `ns01.trs-dns.com`、`ns01.trs-dns.net`、
`ns10.trs-dns.info`、`ns10.trs-dns.org`。前の `a.nic.site` は現行権威DNSとして使わない。
`ns01.trs-dns.com` と `.net` の両方が上記Cloudflare NS2件への委任を返した（TTL 900）。
同 `.com` のDS照会はAA付きNOERROR・回答0件で、DSはない。
Googleのrecursive DNSには旧NSがTTL 20,336、1.1.1.1には旧NSがTTL 172,800で残っていた。
この照合時点のCloudflareはPendingで、「ネームサーバを今すぐ確認」を1回要求し、確認中の表示を確認した。
レジストリの委任完了とrecursive cacheの更新・Cloudflareの有効化を区別する。

05:46 UTCのCloudflare概要再読込でPending案内が消え、
「ドメインはCloudflareによって保護されています」に変わった。zone有効化を確認した。
続くエッジ証明書画面で `*.palschat.site, palschat.site` のUniversal証明書が
「アクティブ」、有効期限 `2027-01-02` と確認できた。有料証明書や追加subscriptionは作成していない。
その後のDNSレコード再読込でもACM CNAME1件だけで、root/API公開レコードはない。
証明書の管理画面の状態はアプリへ外部HTTPS接続できる証拠ではなく、公開後の実接続確認は残る。

ACM CNAMEは旧Route 53とCloudflareの権威DNSから同じ値・TTL 300で返ることを切替前に確認した。
Cloudflare DNSSECは未有効で、DNSレコードは保持ACM CNAME1件だけ。
旧Route 53 zone、ACM CNAME、root/API公開用レコード、Tunnelルート、connectorは変更していない。
保存後のTunnel再読込でも停止・レプリカ0・公開ルート0を確認した。
APIのNXDOMAINは、まだ公開用レコードを追加していない現状と一致する。

保存後の確認画像は `/tmp/pals-macbook-public-prep-20261004/onamae-ns-readback-20261004.jpg` に保持する。
証明書の確認画像は同じディレクトリの `cloudflare-universal-ssl-active-20261004.jpg` に保持する。
通常公開のローカルedge実装はMini担当、外部DNS/Tunnelの変更はこの担当に一元化する。
MiniのAPIは `127.0.0.1:8000`、Webは `127.0.0.1:3000`。
公開用edgeの別portはMiniで実装・検証後の正確な値を受領する。後述の13000/18000を確定値として扱わない。
通常公開の合格条件と公開ルート変更の承認は、NS変更の承認とは別に残る。
別CIMD依頼の追加経路は[レビュー用の公開案](cimd-public-edge-plan-2026-10-04.md)に分け、通常公開の必須条件へ加えない。
同担当から、本人許可による既存poolのEssentials変更・専用public client追加・API roleの読み取りpolicy追加を報告された。
これはMacBook公開担当のAWS変更ではなく、以下の04:05〜04:13 UTCの照合後の別作業である。
通常Web clientが維持されたという報告を親へ共有し、Mini配備前の実Cognito検査は担当の証拠で照合する。

## 同期したコミットを公開作業の正本として保持する

MacBookのHEAD、親のsubmodule参照、GitHub mainを読み取り照合した。
次のSHAは一致した。GitHub照合時刻は03:38 UTC頃。

| リポジトリ | 同期済みSHA |
| --- | --- |
| pals | `818795e87fecf74c72a945336061e8b44f25cada` |
| pals-api | `c0062c38eb6bef3b470cb827a2ded869700fd051` |
| pals-webfront | `07505884bb5388d3d92f51619ab3e9313cc10cde` |
| pals-agent | `e4814d0a052126efa218cc4ecd19adad80447d97` |
| pals-infra | `063dfece859b05895a33c1938579cc0bf20fb3b3` |
| pals-observability | `fa121a88d5cd04c39a097a9b3e8bc80e515fb1e8` |
| pals-datasets | `dcc8185be01d5c5eff0e200983cd4462dc9816c7` |

datasetsはMacBookで未初期化。親の参照とGitHub mainのみ照合した。
API、Web、Agent、親に既存のtracked/untracked変更があり、Infraには未追跡cacheがある。
reset、clean、stash、stage、commit、pushは行っていない。
旧v4アーカイブで現在のソースを上書きしない。
親の `AGENTS.md` を読み、`.agents/skills/` は空であることを確認した。

公開URLは `https://palschat.site` と `https://api.palschat.site`。
[10月4日の監査](mac-mini-deployment-audit-2026-10-04.md)と今回の依頼を優先する。
[9月30日のrunbook](mac-mini-public-hosting-runbook.md)の `app.palschat.site`、新規Tunnel作成、AWS未構築という記述は旧状態なので転記しない。

## 現在確認できたDNSとCloudflare

03:36〜03:46 UTC頃、Cloudflareの既存画面を再読込し、公開DNSを照合した。

| 対象 | 現在の読み取り結果 |
| --- | --- |
| Cloudflare account | `e792ca2e954ad6da854305c109d17d75` |
| zone | `e69adb50e443a9804c9428f11c11d2bb`、`palschat.site`、Free、full setup、Pending |
| 割当NS | `ignacio.ns.cloudflare.com`、`nelly.ns.cloudflare.com` |
| Cloudflare DNS | ACM検証CNAMEのみ、DNS only、TTL 300。root/APIルート用レコードなし |
| 既存Tunnel | `mac-mini-m1-2020`、`aa7c15fc-5b2c-429c-85cd-0500b0955f27` |
| Tunnel状態 | 停止、レプリカ0、公開ルート0。Dify/Boltは再公開されていない |
| SSL/TLS | Full、エッジ証明書一覧0件、Universal SSL有効 |
| HTTPS関連 | Always Use HTTPSオフ、最小TLS 1.0、TLS 1.3オン |
| Cache Rules | 0件。cache response rulesも0件 |
| recursive DNS | 8.8.8.8で旧Route 53 NS4件、root AはNOERROR/回答0、API AはNXDOMAIN、DSはNOERROR/回答0 |
| 旧権威DNS | `ns-679.awsdns-20.net`へ直接照会し、既存ACM CNAMEとNS4件を確認 |
| レジストリ直接照会 | `a.nic.site`へのUDP/TCP照会はタイムアウト。現在の登録元設定を証明するものとして使っていない |
| お名前.com | 当初は失効。本人ログイン後に `palschat.site` の契約中画面とネームサーバー情報を読み取り、旧Route 53 NS4件が現行値と確認できた |

保持するACM CNAME:

```text
_806fcef89c65385fd6d345b3d6b4ebef.api.palschat.site
  -> _5b40eaa6ffc354dd65e527cba88de6a5.jkddzztszm.acm-validations.aws
TTL 300 / DNS only
```

停止中のTunnelへ向けたDNSだけを作ってもアプリは稼働しない。
DNSとTunnelは独立しており、同一accountのTunnel UUIDにCNAMEを向ける。
[Cloudflare公式のTunnel DNS説明](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/routing-to-tunnel/dns/)

## AWSブラウザーの現行照合とCLIの制約

`pals-prod-member` のaccount設定は `828786775577`、regionはTokyo `ap-northeast-1`。
設定上のSSO権限名は `AdministratorAccess`。読み取り専用権限だとは扱わず、今回呼ぶ操作を読み取りだけに限定する。
実ネットワークで `sts get-caller-identity` を試した結果、SSOは失効していた。
既存AWSブラウザー表示には管理account `027624646572:root` のRoute 53権限エラーが残っており、PALS用として流用しない。

以下は10月2日の保存済みreceiptからの候補値。ブラウザーで再確認できた範囲は次の表の後に明記する。
CLIによる全属性・RoleId・公開鍵fingerprintの再照合は未完了。再作成せず既存資源を使う。

| 資源 | 保存済み識別情報と再確認内容 |
| --- | --- |
| Cognito | Pool `ap-northeast-1_CnwrhavzI` / client `4u13065h7ai6d7f6j8km19k7uc`。Lite、招待のみ、client secretなし |
| callback/logout | `https://palschat.site/auth/callback` / `https://palschat.site` |
| Cognito domain | `pals-mini-828786775577.auth.ap-northeast-1.amazoncognito.com` |
| SQS | `pals-mini-prod-proof-jobs` / `pals-mini-prod-proof-jobs-dlq`。暗号化・TLS deny・DLQ配送設定 |
| S3 | `pals-mini-prod-artifacts-828786775577` / `pals-mini-prod-backups-828786775577`。Tokyo、非公開、AES256、versioning、TLS deny、expiryなし |
| KMS | `ff0e59ed-e74c-4e8f-aef3-c815a07f2296` / `alias/pals-mini-prod-release`。Enabled、ECC_NIST_P256、SIGN_VERIFY、ECDSA_SHA_256 |
| KMS公開鍵SHA256 | `66c76baf2578fcadb89f7f1b25fdc3b56ac424d3a5dcad28f62f318f1c562018` |
| IAM | `/pals-mini-prod/`配下のapi、worker、backup-writer、release-signer。各roleのtrust、policy、RoleId、1時間上限を照合 |
| CFN | `pals-mini-prod-dependencies` は保存済みreceiptで `ROLLBACK_COMPLETE`。RETAINされた既存資源を再作成・削除しない |
| Route 53 | zone `Z03464212MY64JSAVQSNN`。全recordsとDNSSEC状態を取得し、Cloudflareへの不足がないか照合 |

SSO cache、MacBookのAWS資格情報、Tunnel tokenをMiniへコピーしない。
release-signerはホストでの別操作とし、API/workerに配らない。
1時間のSTSとSSO再ログイン依存は無人常時運用の解決にはならない。
バックアップroleは書き込み用で、restore-operatorは保存済み資料では未作成。
復元に必要な読取権限を既存権限で満たせない場合は、具体的な対象prefix/操作/有効期間を示して別途承認する。

本人入力用Chromeタブ:

- AWS公式SSO: <https://ssoins-72235ad8d20425ad.us-east-1.portal.amazonaws.com/>、tab `1144547575`。公式AWS Username画面へ遷移済み。
- お名前.com公式: <https://navi.onamae.com/login>、tab `1144546375`。

パスワード・MFA・初回パスワードは本人が入力する。入力後も公開変更は実行しない。
ブラウザーのSSOログインだけではCLI cacheの更新を保証しない。
CLIが失効のままなら、本人による `aws sso login --profile pals-prod-member` の公式フローが必要になる。
本人のログイン報告直後はAWSポータルがUsername画面だったが、後の再確認でログイン完了を確認した。
PALS `828786775577` の既存 `AdministratorAccess` からTokyoコンソールへ入れた。管理accountは使っていない。
ブラウザー成功後もCLI再照会は `Token has expired and refresh failed`。CLIとブラウザーの認証状態は別である。

04:05〜04:13 UTC頃、PALSアカウントの現行コンソールで次を再確認した。設定保存、role引受け、署名、招待、資格情報取得は行っていない。

| 現行確認対象 | ブラウザーで確認できた内容 |
| --- | --- |
| Cognito pool/client | 上表のpool/client IDと一致。Lite、client secretなし、SRP/username-password/refresh flow有効、自己登録Disabled |
| Cognito redirect | callback `https://palschat.site/auth/callback`、logout `https://palschat.site`、code grant、Cognito directoryのみ、email/openid/profile |
| Cognito users | 現行一覧 `Users (0)` / `No users found`。実ログイン/初回変更の前に承認済み招待ユーザーが必要 |
| KMS | 上表のキーIDとalias一致。Enabled、Asymmetric、ECC_NIST_P256、Sign and verify、ECDSA_SHA_256 |
| SQS | source/DLQ2件一致、両方SSE-SQS。source policyは非TLS deny、DLQ有効・対象ARN一致・Maximum receives 5 |
| S3 | artifacts/backupsともTokyo、versioning Enabled、SSE-S3、Block all public access On、Bucket owner enforced。両方の通常object一覧0件 |
| CFN | `pals-mini-prod-dependencies` は現在も `ROLLBACK_COMPLETE`。再作成・削除しない |
| Route 53 | zone ID一致、recordsはNS/SOA/保持ACM CNAMEの3件だけ。root/API公開recordなし。DNSSECはNot signing、KSK0件 |
| IAM | 用途別4roleが存在し `/pals-mini-prod/` ARN、各MaxSessionDuration1時間。下表のinline policy/trustを読み取り確認 |

| role | 現行inline policy | trustで要求するRoleSessionName |
| --- | --- | --- |
| `pals-mini-prod-api` | source queueに `sqs:SendMessage` のみ | `pals-mini-api` |
| `pals-mini-prod-worker` | source queueにReceiveMessage/DeleteMessage/ChangeMessageVisibility/GetQueueAttributes、artifactsの `proof-jobs/*` にPutObject | `pals-mini-worker` |
| `pals-mini-prod-backup-writer` | backupsの `db/*` にPutObjectのみ。GetObject/ListBucketなし | `pals-mini-backup-writer` |
| `pals-mini-prod-release-signer` | 指定KMS keyへSign（ECDSA_SHA_256条件）、GetPublicKey、Verify | `pals-mini-release-signer` |

4roleのtrustは同一PALS `AWSReservedSSO_AdministratorAccess_7fecda475e1d9cf8` principalと、
`aws:userid = AROA4B54KSYMXVKP3YTR7:atsushi-hosaka` に限定される。
Mini側も、この既存SSOユーザーと各RoleSessionNameが一致することを、秘密値を出さずに確認する。
roles一覧10件にrestore-operatorはない。復元用権限をbackup-writerが持つとは扱わない。

今回未再確認の範囲はKMS公開鍵fingerprint/実署名、IAM RoleId、S3の全policy JSON/TLS deny/lifecycle、DLQ policyの全属性。
通常object一覧0件は非現行versionの不存在を保証せず、バックアップ/復元成功の証拠でもない。

## 公開時に変更する正確な対象

以下のうちNSだけは上記の承認で先行実施済み。他は未実行。
Miniの本番loopbackで認証・Send・QA・保存・利用量・復元が通り、正確な接続先を再確認した後、実行直前に対象をまとめて承認する。

| 順序 | 対象 | 変更内容 | 戻し方 |
| --- | --- | --- | --- |
| 1 | Mini connector | 既存Tunnelへ公式ARM cloudflaredを接続。token入力・常駐化は具体的なpath/owner/起動方式を提示して承認 | 新規公開ルートを先に止め、connectorを停止。tokenやTunnelは削除しない |
| 2 | 既存Tunnel | `palschat.site` -> `http://127.0.0.1:13000`、`api.palschat.site` -> `http://127.0.0.1:18000`。pathは全体、hostnameはこの2件だけ | 今回追加した2ルートだけを削除またはメンテナンス経路に置換 |
| 3 | Cloudflare DNS | root (`@`) と `api` のproxied CNAMEを `aa7c15fc-5b2c-429c-85cd-0500b0955f27.cfargotunnel.com` へ。TTL Auto。ルート保存時の自動作成と重複させない | 今回追加したroot/apiだけを戻す。既存ACM CNAMEは維持 |
| 4 | Cache Rules | API hostname全体をBypass cacheにする。式 `(http.host eq "api.palschat.site")`。originの`Cache-Control: no-store`も確認 | 今回追加した規則だけを戻す。認証レスポンスをキャッシュする規則は採用しない |
| 先行実施済 | お名前.com | `palschat.site`だけの委任先をCloudflare指定NS2件へ保存・読戻し済み。レジストリ委任も確認。他ドメインは選択していない | 旧NS4件へ戻す。旧Route 53のzone/recordsは保持 |
| 6 | Edge HTTPS | NS反映後にUniversal SSLの証明書を確認し、Always Use HTTPSオン、最小TLS1.2を設定する案 | 今回変更した値を保存済み値へ戻す。HTTPS成立前の公開合格判定はしない |

13000/18000は、cloudflaredがMiniの**ホスト**で動くときの接続先。
コンテナ方式へ変える場合、localhostを転用せずMini担当が実際のnetworkを確認する。
18000は内部APIを直接公開せず、Miniで検証済みのedge allowlistを通す。
既存Caddy提案は `/v1/internal*`、docs、metricsを拒否するが、現在の全UI操作を通すかMiniで再検証する。
DB、verifier、reconciler、admin、SSHは公開ルートへ追加しない。

Quick TunnelはSSEをサポートしないため使わない。
[Cloudflare公式の制約](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/)
Cache bypassとno-storeの動作を外部応答で確認する。
[Cloudflareのcache設定](https://developers.cloudflare.com/cache/how-to/cache-rules/settings/)

## 切替直前の合格条件と復旧

Mini担当から、同期SHA・新規build digest・本番設定SHA・実KMS署名・DB/volume identityの証拠を受け取る。
実Cognitoの初回変更、ログイン、質問1件、回答/独立QA、利用量、保存/再読込、別ユーザーへの拒否、別DBへのバックアップ復元までloopbackで通す。
ソース修正が追加される場合は、同期版との違いと検証済み差分を明示する。
credential更新とexpiry後の停止、FileVault解除/ログインを含む復旧条件を残す。

切替後は外部回線でroot/APIのHTTPS、HTTPからの転送、証明書hostname、CORS、SSEの逐次受信/再接続、再読込後の保存、利用量を確認する。
SSEは応答末尾までbufferされず、`text/event-stream`、cache非使用であることを確認する。
MacBookは再起動しない。Mini再起動は親と担当の承認範囲で行う。

障害時は新規要求をedgeで止め、処理中ジョブをdrainする。
NSの切り戻しは即時ではない。旧zoneにはroot/API公開recordがないため、旧NSに戻す目的は元のDNS状態への復帰であり、アプリ公開の維持ではない。
volume、S3 object、queue、旧データは削除しない。DB migration後のimage rollbackはschema互換性を確認する。

旧NS:

```text
ns-679.awsdns-20.net
ns-1588.awsdns-06.co.uk
ns-118.awsdns-14.com
ns-1346.awsdns-40.org
```

NS変更は登録元で行う。Route 53 zone内のNS編集で代替しない。
DSは今回のrecursive照会で未観測だが、切替直前に登録元とpublic DNSを再確認する。
[Cloudflare full setupの手順](https://developers.cloudflare.com/dns/zone-setups/full-setup/setup/)

## Webの初回パスワード変更修正

同期済みWebの `components/AuthProvider.tsx:757` は `newPasswordRequired` をエラーで拒否していた。
今回追加依頼により、Web authだけを修正・検証した。旧Miniの未レビューauthコピーは採用しない。
既存Web tracked差分と認証/copy元ファイルを `/tmp/pals-macbook-public-prep-20261004/` へ退避済み。
インフラ文書はこの担当、Web authの限定実装は `cognito_first_password` 担当。
同じSDK CognitoUser/Sessionを保持して `completeNewPasswordChallenge` を呼び、必要属性、新パスワード確認、取消、再試行を扱う。
取消後の遅い完了が新しいsign-in状態を変更しないようにし、sign-in/challenge中のsnapshot取得はnullを返してepochを維持する。
実際の新パスワード入力・送信は本人が行う。実Cognito確認はMini側で残る。

同期base `07505884bb5388d3d92f51619ab3e9313cc10cde` の新規source exportで、認証関連18ファイル113テスト、typecheck、対象ESLintが成功。
読み取りレビューは追加修正を含めて残る具体的な指摘なし。`git apply --check` と適用後5ファイルのSHA256照合も成功した。
既存dirtyのanalytics追加3行とbilling文言は作業ツリーに保持し、受渡しpatchから除いた。commit/pushは行っていない。

Mini向けLibraryファイル:

- `pals-web-cognito-first-password-07505884-20261004-final.tar.gz`、40,214 bytes、version 0。
- Library ID `libfile_a6d5fc7fb7788191885dcfd21ca8a7a6`、file ID `file_00000000e7e881f58a6570aa529ff2e2`。
- archive SHA256 `4cec78a69423bc481d6d0dde827014b0147aff6f7b5977399dad83154d651fe2`。
- patch SHA256 `074e6d0b4e81c945b2e776303165b4d9da2679eecde7734f2f402b1be57cb78b`。
- base/after SHA256は同梱の `cognito-new-password-exact-base-manifest.json`。patch、after-source5件、適用手順を同梱した。

Miniでは新規の正確な同期base workspaceでcommitとbase-file hashを照合し、dirtyがないことを確認してから適用する。
旧checkoutや既存変更へコピーしない。修正後に再ビルドし、実Cognito・保存・利用量の確認を行う。

## 既存コミットのソース受渡し

親/Agent/Observabilityの不足commit用source exportは、直接GitHub取得再確認の連絡より前にLibrary保存が完了した。
追加uploadは止めて保持している。MiniがGitHubから正確なcommitを取得できれば直接取得を使う。
その後、親からMiniのgh認証と親・5submoduleの指定SHA完全一致・cleanの直接取得成功を受領した。
source exportは不要になり、保持のみ。Web auth差分だけを適用対象として引き継ぐ。

- `pals-sync-sources-818795e8-20261004.tar.gz`、2,436,541 bytes、version 0。
- Library ID `libfile_b42f58dad6e4819192583e8b12457930`、file ID `file_0000000087e881f798755f1b7ce17d46`。
- archive SHA256 `0cfbb3b88c261952530a0783838d9140d744d6c5fdb7dd99276f10472d1484fb`。

765 source filesを各固定commitのGit blobと照合した。Git履歴、dirty作業、Web auth差分、環境ファイル、資格情報、生成物は含まない。
既知のcredential形式を持つtest fixture2件も除外した。除外一覧と各ファイルSHA256は同梱manifestに記録した。
これは履歴・除外ファイルを持たないsource exportであり、完全なcloneの代替だとは扱わない。

## PALSプロジェクトのチャット

Codexのproject一覧にはローカル `pals` があり、pathはこのrepository、project idは `local-da76878add3e9ce6a27a5a03bcb4330b`。
同一覧のChatGPT ProjectsにはPALSがなく、このチャットのChatGPT PALS所属は確認できない。
ローカルCodexの新規タスクを作る際は、この保存済み `pals` projectを選べる。
ChatGPT Projects所属は別の設定であり、作業ディレクトリがPALSであるだけでは所属を主張しない。
