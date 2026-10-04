# Mac miniでPALSを一般公開する手順

更新日: 2026年9月30日

PALSのWeb・API・証明生成・PostgreSQLを自宅のMac miniで動かし、`palschat.site`をCloudflare Tunnelにつなぐ。AWSには認証のCognito、ジョブ配送のSQS、生成物とバックアップ保存のS3を残す方針で進める。

この文書は運用者向けの準備・公開手順書。初回は「公開までの順序」に沿って読み、公開後は「停止と復旧」を参照する。Mac向けの公開用起動構成はまだ実装されていないため、DNSの準備とアプリの公開準備を分けて記載する。Cloudflareへのドメイン追加は完了したが、DNSの委任先変更・AWS構築・外部公開は未実施。

## 現在のドメインはRoute 53を向いている

2026年9月30日に公開DNSと登録情報を確認した。

| 項目 | 確認結果 |
| --- | --- |
| ドメイン | `palschat.site` |
| 登録・管理先 | お名前.com Naviで`palschat.site`を確認済み |
| 現在のDNS委任先 | AWS Route 53のネームサーバー4件。お名前.comの設定画面でも確認済み |
| `palschat.site` のAレコード | 権威DNSへの問い合わせで該当回答なし |
| `app.palschat.site` / `api.palschat.site` | 権威DNSがNXDOMAINを返した。ホスト名は未登録 |
| 既存レコード | Route 53管理画面でNS・SOAとAWS証明書検証用CNAMEの計3件を確認。A・MX・TXTは登録なし |
| DNSSEC | Route 53のゾーン署名は無効。公開DSも観測されていない |
| Cloudflare | ドメイン追加とFreeプラン選択が完了。検証用CNAMEをDNSのみ・TTL 5分で移行済み。ネームサーバーの切り替え待ち |
| AWSアカウント | AWS Organizationsで管理アカウント`027624646572`と、`hosaka2917+pals@gmail.com`を登録した稼働中のPALSメンバーアカウント`828786775577`を確認済み。新規アカウント作成は不要 |
| 既存ゾーンの所在 | 設計書はPALSメンバーアカウントのゾーン`Z03464212MY64JSAVQSNN`を指定。Chromeでログイン中の管理アカウントにはHosted zonesが0件。PALSアカウント内の現状は未確認 |

Cloudflareが割り当てた移行先は次の2つ。DNSスキャンの検出数は0件だったが、Route 53管理画面と照合し、標準のNS・SOA以外の1件を移行した。

```text
ignacio.ns.cloudflare.com
nelly.ns.cloudflare.com
```

PALSアカウントのRoute 53ゾーンとレコードの確認は完了した。端末の`pals-prod-member`プロファイルはPALSアカウントを指すが、SSOトークンが失効しているため、今回はAWSアクセスポータルから確認した。CloudflareへのCNAME移行も完了した。お名前.comで変更を確定しようとした際にセッションが切れたため、変更完了は未確認。直後に`.site`レジストリの権威DNSへ問い合わせた結果も旧Route 53委任先だった。再ログイン後にお名前.comの設定値を確認する。Web/APIの公開URLはまだ用意されていない。Cloudflare画面の「伝播待ち」は、購入先で変更済みという証拠ではない。

現在のネームサーバーは次の4つ。切り戻し用に残す。

```text
ns-118.awsdns-14.com
ns-1346.awsdns-40.org
ns-1588.awsdns-06.co.uk
ns-679.awsdns-20.net
```

購入先は変えず、DNSの管理だけCloudflareに移せばよい。Route 53の画面でNSレコードを編集するだけでは移行にならない。ドメイン購入先の管理画面で、委任先のネームサーバーを変更する。

## 公開までの順序

1. Mac miniのチップ・メモリ・空き容量、常時稼働の可否を確認する。
2. 既存DNSを調べ、Cloudflareに必要なレコードを準備する。ドメイン追加は完了済み。
3. Mac公開用の起動構成と、必要なAWSリソースを用意する。
4. Mac内で動作とバックアップ復元を確認する。
5. Tunnelを接続して公開ルートを準備し、お名前.comでDNSの委任先を変更する。その後、公開URLで認証・証明生成・再起動復旧を確認する。

DNS移行だけでは、Mac内のサービスは外部公開されない。公開ルートを追加する段階で、一般利用者からアクセスできるようになる。

## 1 Mac miniの公開用環境を用意する

搭載メモリは未確認。16GB以上なら検討しやすいが、必要量は実際の証明生成と同時アクセスで測る。macOSに加えてDockerのLinux仮想環境もメモリを使うため、EC2の容量をそのまま当てはめない。

- AC電源と安定した回線を使い、スリープを無効にする。有線LANを推奨する。
- 公開用のCompose project、DB volume、設定ファイルを開発用から分ける。既存の`pals-local`のDBや実行中ジョブは転用しない。
- Docker Desktopなど、利用条件に合うコンテナ実行環境を選ぶ。Apple Siliconでは対応するARM64イメージを使う。
- macOS更新・再起動後に、コンテナ実行環境、DB、アプリ、Tunnelが戻る手順を確認する。FileVaultやユーザーログイン待ちがある場合は、有人での復旧手順を残す。
- 公開用プロセスには必要なディレクトリだけを渡す。個人のホーム全体やDockerソケットをアプリにマウントしない。

Web/APIのホスト側ポートは`127.0.0.1`に限定し、Mac上の`cloudflared`から接続する。DB、Lean verifier、reconciler、管理画面はTunnelの公開ルートに登録しない。

## 2 palschat.siteのDNS管理をCloudflareへ移す

### 既存レコードを確認してCloudflareに追加する

1. [Cloudflare管理画面](https://dash.cloudflare.com/)にログインする。
2. Domainsからドメイン追加を選び、`palschat.site`を入力してFreeプランを選ぶ。すでに登録済みなら既存の設定を開く。
3. AWSアクセスポータルから既存のPALSメンバーアカウント`828786775577`へ入り、Route 53のゾーン`Z03464212MY64JSAVQSNN`と全レコードを確認する。Chromeで現在ログイン中の管理アカウントとは異なる。TXT、メール用MX、証明書検証用CNAME、サブドメインも確認する。ゾーンが見つからなければ、旧設定が存在しないと決めつけず、移行前に管理元を確認する。
4. 必要なレコードをCloudflareへ引き継ぐ。自動スキャンは全レコードの取得を保証しない。Route 53固有のALIASは、そのままコピーせず対応する設定に置き換える。
5. Cloudflareがこのドメインに割り当てたネームサーバー2つを控える。値はアカウント画面から取得し、推測で入力しない。

旧Route 53のゾーン頂点NS・SOAを、Cloudflareの委任先としてコピーしない。サブドメインを別サービスに委任しているNSは個別に維持する。

今回移行した検証用CNAMEは次のとおり。これは`api.palschat.site`のAWS Certificate Manager向けで、Cloudflareではプロキシをオフにする。

```text
名前: _806fcef89c65385fd6d345b3d6b4ebef.api.palschat.site
値:   _5b40eaa6ffc354dd65e527cba88de6a5.jkddzztszm.acm-validations.aws
TTL:  300秒
```

### 購入先でネームサーバーを変更する

1. お名前.com Naviの「ネームサーバー設定」で`palschat.site`だけを選ぶ。管理画面で登録を確認済み。
2. DNSSECが有効なら、Cloudflareの移行手順に従って旧DSの扱いを確認する。今回DSは観測されていないが、管理画面でも確認する。
3. 既存レコードの移行とTunnelの公開ルート準備が終わってから、現在のRoute 53の4つをCloudflareが指定した2つへ置き換える。他のドメインは選択しない。
4. Cloudflare側がActiveになるまで待つ。反映にはキャッシュによる時間差がある。
5. 移行完了後、DNSSECを利用する場合はCloudflareが示すDSを購入先に登録する。

確認用コマンド:

```bash
dig +short NS palschat.site
dig +short DS palschat.site
```

NSがCloudflare指定値になり、引き継いだレコードが解決できればDNS移行は完了。Route 53の旧ゾーンは、動作と切り戻しを確認するまで保持する。ドメインの自動更新契約は購入先に残る。

根拠: [CloudflareのDNS移行手順](https://developers.cloudflare.com/dns/zone-setups/full-setup/setup/)

## 3 Mac公開用の起動構成を実装する

ここは公開前に必要な実装作業。既存の`make pals-up`はLocalStackとCognito Localを含む開発・検証用であり、公開用の起動コマンドではない。

実装は各所有リポジトリで行い、横断する設計は親の`specs/`に反映する。現行の[EC2向け設計](../specs/domainless-production-bootstrap/design.md)がこの文書だけで置き換わったと扱わない。

### AWSは必要なリソースだけを用意する

| サービス | 用意するもの |
| --- | --- |
| Cognito | 公開用User Pool、シークレットなしのWeb App Client、必要なログイン方式 |
| SQS | 証明生成用キュー、失敗メッセージを保管するDLQ、再配送・保持期間の設定 |
| S3 | 非公開の生成物保存先、外部バックアップ保存先、暗号化と保持期間 |
| IAM | API、worker、バックアップの用途に絞った権限と、Macへの資格情報供給方法 |

既存リソースがあれば、設定とデータの用途を確認して再利用する。APIには送信、workerには受信・削除など、役割ごとに必要な操作を割り当てる。MacにはEC2のinstance profileがないため、認証情報の保管・更新方法を決める。管理者キーやLocalStackの`test`資格情報を使わない。

現行の`pals-infra/terraform/production`をそのままapplyすると、foundationでもAuroraやVPCなどが作られる。今回の構成には専用の小さいTerraform構成が必要。既存の稼働リソースやstateを削除して節約したことにはしない。

前の説明にあった「Cognito・SQS・S3」は残す主要サービスを指す。現行のデプロイ処理にはSSM・KMS等の依存もあるため、Mac向けに資格情報、署名検証、秘密情報の供給方法を決め、残すサービスの費用も計上する。

### 公開URLと認証設定を一致させる

正式なアプリURLは既存の設計に合わせて`https://app.palschat.site`、APIは`https://api.palschat.site`とする。

| 設定名 | 公開用の値・扱い |
| --- | --- |
| `NEXT_PUBLIC_PALS_API_BASE_URL` | `https://api.palschat.site` |
| `NEXT_PUBLIC_COGNITO_USER_POOL_ID` / `NEXT_PUBLIC_COGNITO_CLIENT_ID` | 実Cognitoの公開用ID |
| `NEXT_PUBLIC_COGNITO_REDIRECT_URI` | `https://app.palschat.site/auth/callback` |
| `NEXT_PUBLIC_COGNITO_LOGOUT_URI` | `https://app.palschat.site` |
| `NEXT_PUBLIC_COGNITO_ENDPOINT` | ローカル上書きを除去 |
| `NEXT_PUBLIC_COGNITO_HOSTED_UI_DOMAIN` | Hosted UIを使う場合の実Cognitoドメイン |
| `NEXT_PUBLIC_COGNITO_GOOGLE_ENABLED` | Google IdPの設定・実ログイン検証後に有効化 |
| `PALS_ENV` / `PALS_LOCAL_RUNTIME_ENABLED` | `prod` / `false` |
| `PALS_CORS_ALLOWED_ORIGINS` | `https://app.palschat.site` |
| `PALS_AWS_REGION` | `ap-northeast-1` |
| `PALS_COGNITO_USER_POOL_ID` / `PALS_COGNITO_APP_CLIENT_ID` | Webと同じ公開用Pool・Client |
| `PALS_SQS_PROOF_JOBS_QUEUE_URL` / `PALS_S3_ARTIFACT_BUCKET` | 実AWSの公開用リソース |

`NEXT_PUBLIC_*`はWebのビルド時に組み込まれるため、変更後に再ビルドする。Cognitoの許可callback/logout URLも同じ値にする。Google OAuthの戻り先はCognitoの`/oauth2/idpresponse`であり、アプリのcallbackとは異なる。

`/auth/callback`は既存の本番設計の値だが、公開ビルドでの動作は未検証。このURLで認証応答を処理し、404画面を残さずアプリへ戻れることを確認する。必要ならcallback用の画面・ルーティングを実装する。

`PALS_LOCALSTACK_ENDPOINT_URL`、`PALS_AWS_ENDPOINT_URL`、`AWS_ENDPOINT_URL`と、Cognito issuer/JWKSのローカル上書きを除去する。workerの`PALS_API_BASE_URL`はDocker内部のAPIを指し、公開URLと区別する。

### DBとLeanの本番用の制約を維持する

PostgreSQL＋pgvectorを公開用volumeで動かす。初回構築・migrationの権限と、API・reconciler・検索処理の実行権限を分ける。開発用初期パスワードを流用しない。

本番APIにはRecipe関連の秘密情報、toolchain digest、役割別のDB接続情報も必要。`PALS_CANDIDATE_RECONCILER_URL=http://pals-reconciler:18118`などの内部経路、verifierとreconcilerの相互TLS認証、隔離した実行権限も維持する。URLだけ変えて、起動エラーを回避するためにlocalモードへ戻さない。

既存のEC2用`host-user-data.sh.tftpl`はAmazon Linuxとsystemdを前提とする。Macに直接実行せず、起動順・秘密情報注入・DB初期化・証明書管理をMac公開用構成に移す。公開用Composeと起動コマンドが完成したら、この節に実際のパスとコマンドを追記する。

## 4 Mac内で動作と復元を確認する

公開用のWeb/APIを、例として`127.0.0.1:13000`と`127.0.0.1:18000`に割り当てる。これは開発用3000/8000と分けるための提案値で、現在は未設定。

```bash
# 公開用構成を実装して起動した後に実行する
curl --fail http://127.0.0.1:18000/health
curl --fail --head http://127.0.0.1:13000/
```

起動後は実Cognito・SQS・S3に接続していることを確認する。開発用アカウント、テスト用課金設定、既存の個人データを公開用DBへ一括コピーしない。

DBは日次で`pg_dump`し、Mac外の非公開S3へ暗号化して保存する。復元に必要なDBロール・拡張機能・migrationの版も管理する。保存できたことだけで完了にせず、別DBへ復元して履歴を読めることを確認する。最初は日次7世代を保持する案とし、最大約24時間のデータ損失を許容できるか決める。

再起動試験は公開用の構成で行う。OS・Docker VM・DB・コンテナ・Tunnelの全てが戻ることを確かめる。`cloudflared`だけ自動起動しても、アプリが停止していれば公開できない。

## 5 TunnelをMacに接続して公開する

1. Cloudflare管理画面のNetworking → Tunnelsから、固定の名前を持つTunnelを作る。名前の案は`pals-mac-mini`。
2. Mac miniで公式の`cloudflared`を導入し、管理画面のmacOS向け手順で接続する。トークンは秘密情報として扱い、Git・手順書・共有ログに貼らない。
3. 管理画面でTunnelの状態がHealthyになったことを確認する。この時点では公開ルートを追加せず、内部サービスの準備を終える。
4. 公開用APIの認証・利用枠、Web設定、バックアップを確認した後、次のPublished application routeを追加する。

| 公開ホスト名 | Mac上の接続先案 |
| --- | --- |
| `app.palschat.site` | `http://127.0.0.1:13000` |
| `api.palschat.site` | `http://127.0.0.1:18000` |

この表は`cloudflared`をMacのホスト上で動かす場合の値。コンテナ内で動かす場合、`127.0.0.1`はそのコンテナ自身を指すので、専用Dockerネットワーク上の接続先へ変更する。

公開するAPI経路は、利用者が必要とするものに絞る。内部管理・release用経路を公開入口から到達可能にしない。課金を有効にする場合のみ、署名検証するStripe Webhookの経路を別途確認する。現在のローカルStripe sandbox設定は一般利用者向けの実課金設定ではない。

Cloudflareの管理画面からルートを追加すると、Tunnel向けのDNSレコードも作られる。家庭のグローバルIPをAレコードに登録したり、ルーターで80/443を開けたりする必要はない。

`palschat.site`と`www.palschat.site`は、最初は案内ページか`https://app.palschat.site`への転送用とする。転送する場合はCloudflareのRedirect Ruleと対応するproxied DNSレコードを設定する。CNAMEだけではURL転送にならない。

PALSは進捗通知にSSEを使うため、SSE非対応のQuick Tunnelは使わない。macOSでのサービス化はログイン後起動とシステム起動を区別し、利用する導入方式で再起動試験を行う。

根拠: [Tunnel設定](https://developers.cloudflare.com/tunnel/get-started/)、[ルーティング](https://developers.cloudflare.com/tunnel/concepts/routing/)、[macOS常駐化](https://developers.cloudflare.com/tunnel/features/locally-managed-tunnels/as-a-service/macos/)、[Quick Tunnelの制約](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/)

## 6 外部回線から公開状態を確かめる

- スマートフォンのモバイル回線でWebを開き、HTTPSとログインを確認する。
- 未ログインでは他人の履歴を読めず、ログイン後も自分のデータだけが表示されることを確認する。
- 証明要求を1件送信し、SQS配送、Lean検証、進捗通知、結果表示、再読み込み後の保持まで確認する。
- 利用枠と連続要求への制限を確認する。Cloudflareの保護だけでLLM料金の上限管理を代替しない。
- API応答・履歴・SSEをCloudflareで不用意にキャッシュしない。長い証明処理はジョブ受理後の状態照会と進捗通知で扱う。
- 公開用の再起動、回線再接続、バックアップ復元の結果を記録する。証明処理中のworkerを更新するときは、既存のdrain手順に従う。

Mac miniの本番運用では、外部からの死活監視、DBバックアップ失敗、ディスク残量、メモリ不足、キュー滞留を確認できるようにする。

## 停止と復旧

公開を止めたい場合は、まずCloudflareの公開ルートを無効化するかメンテナンス画面へ切り替え、新しい要求を止める。処理中ジョブをdrainしてからアプリを停止する。DB volumeやS3データは削除しない。

| 症状 | 確認する場所 |
| --- | --- |
| 名前が解決しない | 購入先のNS、CloudflareのActive状態、app/apiのDNSレコード |
| TunnelはHealthyだが502になる | Web/APIの起動、接続先ポート、ホストとコンテナのlocalhostの違い |
| ログイン後に戻れない | Cognitoのcallback/logout許可URL、Webのビルド時設定 |
| 結果は出るが進捗が届かない | 固定Tunnelを使っているか、SSEの接続・再接続・キャッシュ設定 |
| Mac再起動後に復旧しない | ログイン・ディスク解除、コンテナ実行環境、自動起動の順序 |

DNS移行を戻す場合は、保持しているRoute 53のレコードとDNSSEC状態を確認してから、購入先で元の4つのNSへ戻す。反映には時間差がある。移行前のRoute 53にはapp/apiがなかったため、NSを戻すだけでPALSが公開されるわけではない。

## 費用と残る確認事項

主な費用は、電気、ドメイン更新、Cognito/SQS/S3等の従量課金、LLM・埋め込みAPI。仮に平均20W、電気単価31円/kWhなら、Mac本体の電気代は30日で約446円。これは実測値でも合計額でもない。

既存AWSリソースの料金は、Macへ移すだけでは止まらない。公開が安定した後に請求とリソース一覧を確認し、不要なものの停止・削除を別作業として判断する。

未確認なのはMacの仕様と、再利用できるAWSリソース。公開用構成の実装後には、実際の起動コマンドと動作確認結果を本書へ追記する。不明点はこのCodexタスクに、該当する手順番号と秘密情報を除いたエラーを共有する。

用語: DNSはドメインの接続先を管理する仕組み。NSはDNSの委任先。TunnelはMacからCloudflareへ張る接続。SQSはジョブの待ち行列。SSEは進捗をブラウザーへ継続送信する仕組み。pgvectorはPostgreSQL内でベクトル検索を扱う拡張機能。

### リポジトリ内の参照先

- [ローカル開発の起動方法](local-development.md)
- [実操作の検証記録](main-runtime-validation-2026-09-29.md)
- [現在のローカルCompose](../docker-compose.e2e.yml)
- [APIの設定制約](../pals-api/app/core/config.py)
- [Webの環境変数](../pals-webfront/.env.example)
- [現在のEC2向け起動処理](../pals-infra/terraform/production/templates/host-user-data.sh.tftpl)
- [Stripe sandboxの現在地](stripe-sandbox-setup-2026-09-30.md)

登録先とネームサーバーはお名前.com Navi、Cloudflareの保留状態と0件のDNSレコードはCloudflare管理画面、Hosted zonesが0件であることはログイン中のAWS管理画面で確認した。
