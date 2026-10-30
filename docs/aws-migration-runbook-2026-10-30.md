# PALSのMac miniからAWSへの移行手順書

開始日 2026年10月30日。ユーザーの指示により、本番移行、必要なAWS構成変更、DNSの向き先変更、draw.io図の作成を実施対象とします。Web・APIはt4g.medium、計算ノードは通常r8a.large、大会時r8a.xlargeを使う方針です。作業を完了した段階だけを実施済みとし、コード・ローカル試験・AWS配備・DNS切り替えを区別します。

DNSを先にAWSへ向けると、未準備の移行先へ利用者を送ってしまいます。まず現在のレコードと切り戻し先を保存し、AWS側でデータ・認証・証明生成を確認した後に向き先を変更します。Cloudflareのネームサーバーは維持し、ドメイン移管は行いません。

## 現在の実行状況

| 段階 | 状態 | 実際に確認したこと |
| --- | --- | --- |
| 対象と接続 | 実施済み | pals-prod-memberのSSOをユーザーが更新し、本番アカウントとの一致をSTSで確認 |
| 現行の公開サービス | 実施済み | WebとAPI healthのGETが200、未認証projectsが401。DNSはCloudflare経由 |
| AWS資源の棚卸し | 実施済み | Cognito・S3・SQS・署名KMS・state bucketあり。EC2・Aurora・ECRはまだなく、state bucketは空 |
| 移行元への接続 | 一部実施済み | Parsec接続とDocker一覧を確認。リモート入力で修飾文字が欠落するため、バックアップ操作はまだ実行していない |
| ACM証明書 | 発行済み | 現在のWebとAPIを対象に申請。Web/APIの検証に成功し、AWS ACMのISSUEDを確認 |
| private network実装 | 配備中 | 保存planは新規74件、既存資源の更新・削除0件。独立照合後にapply開始。完了後の読み戻しが必要 |
| 既存資源の再利用 | 作業中 | 現在のCognito・S3・SQS・署名KMSを読み取り参照する経路を実装・試験済み。実planの独立照合中 |
| DB移送と署名付き受理 | 未完了 | 現行Macの署名を別ホストへそのまま流用できない。専用の移送証拠とAWS側の受理が必要 |
| AWS runtimeと容量モード | 未配備 | x86 runtime、別ホストmTLS、pool配送、drain、通常・大会モードの実配備は未実施 |
| DNS切り替え | 未実施 | 現行Cloudflare originとMac miniを維持 |
| 移行後の受け入れ | 未実施 | ログイン、履歴、資料、生成、共有、ゲスト、負荷試験が必要 |

移行先ALB用のACM証明書を発行し、AWS基盤の作成を開始しました。Cloudflareには証明書検証用CNAMEを1件追加しました。ACMの申請は配信先を変更しません。追加資源を作成した場合は、この表と秘密値を含まない実行記録を更新します。

## 移行する対象と保持する情報

Webの公開名は`palschat.site`、APIは`api.palschat.site`です。既存ログインのcallbackは`https://palschat.site/auth/callback`、logoutは`https://palschat.site`を維持します。使用中のCognito pool/client/issuerはそのまま使い、ユーザーやパスワードの移し替えは行いません。

アプリDBの全schema・行・sequence・所有者・ACL・署名付きadmission履歴を移送対象とします。資料の原本にはPostgreSQLのbyteaもあるため、S3だけを移せば完了するわけではありません。既存S3の成果物と参照、SQSのジョブ、ゲスト用hash key、provider接続、課金・利用枠・共有・継続質問の状態も維持します。

既存バックアップbucketには10月4日のphysical base backupが3件あります。10月30日の移行に使える最新の論理バックアップとは扱いません。新しい一貫したsnapshotに基づくpg_dumpと、復元試験を作ります。

raw dump、DB接続先、鍵、provider token、Terraform plan/state、SSO cacheはGitに含めません。ローカルの作業記録はignoredの`.local/aws-migration/`に置き、ディレクトリ0700・機密ファイル0600を使います。クラウド上は既存の非公開backup bucketの専用prefixへ暗号化して保存し、許可した移送roleだけが取得します。

## 移行先のネットワーク

![AWS移行先の設計図](diagrams/pals-aws-private-target.png)

[draw.io元ファイル](diagrams/pals-aws-private-target.drawio)は編集可能で、PNGは実際のdraw.ioで出力しています。図に記載したCIDRはTerraformの設計値であり、配備結果ではありません。

公開ALBは2つのpublic subnetに置き、ACMでTLSを終端してprivate controlのHTTPSだけへ接続します。Web・APIと計算ノードにはpublic IPを付けません。Auroraはインターネット向けdefault routeのないDB subnetへ置き、controlのsecurity groupからの5432だけを許可します。

外部LLMへの通信が必要なため、private workloadの外向きHTTPSにはNATを使います。S3はgateway endpointを使います。初期のNATは1台で、AZをまたぐ通信と単一障害点を含む費用・可用性の選択です。EC2にはSSHを開かずSSMで管理します。verifierはさらにコンテナ単位で外向き通信を遮断し、DB・AWS・provider資格情報を持たせません。

通常のEC2本体約2.6万円に、NAT・ALB・Aurora最低容量などが加わります。2026年10月30日のAWS Price List APIで、東京のZonal NATは$0.062/時、ALBは$0.0243/時、Aurora PostgreSQL Standard Serverless v2は$0.15/ACU時と確認しました。月730時間、Aurora平均0.5 ACU、public IPv4最低3個を$0.005/IP時、1ドル150円と置くと、本体とこれらの合計は約4.5万円です。EC2はまだ未配備で、これは通常構成の見積もりです。ストレージ、I/O、LCU、NAT処理量、通信、ログ、税、LLM利用料と移行中の重複稼働は別途かかります。[VPC料金](https://aws.amazon.com/vpc/pricing/)、[ALB料金](https://aws.amazon.com/elasticloadbalancing/pricing/)、[Aurora料金](https://aws.amazon.com/rds/aurora/pricing/)を参照します。

## 実施手順

### 1 接続と現状の固定

`aws sso login --profile pals-prod-member`で接続を更新し、`aws sts get-caller-identity --profile pals-prod-member`で対象を確認します。別アカウントのpals-prod-adminを本番の代わりに使いません。CLIで確認した実際のCognito・bucket・queue・KMS identityを、ignoredの移行設定に保存します。

CloudflareのWeb/API origin、proxy状態、TTL、TLS設定、証明書検証レコードを読み取り保存します。既存Miniの稼働revision、image、DB identity、volume、現在の署名付きadmissionを読み取り記録します。秘密値を画面・ログに出さず、fingerprintや一致/不一致だけを残します。

### 2 証明書とAWS基盤の準備

ACMのWebルートとAPI用証明書を申請し、Cloudflareに検証CNAMEだけを追加します。これはWeb/APIの配信originの変更とは分けます。ISSUEDをAWS側で確認するまでALBの公開HTTPSを完了扱いにしません。

Terraformは既存データ平面をdata sourceとして参照します。新しいCognitoや代替bucketを作成するplan、既存ユーザーの設定変更、既存資源のdelete/replaceを含むplanは適用せず、差分の原因を解消します。backend、account、region、provider lock、source revision、plan digestを固定してから保存済みplanを適用します。

VPC、public/control/compute/DB subnet、route、NAT、S3 endpoint、ALB、Aurora、ECRと必要なIAMを準備します。この段階ではDNS originを変えません。runtimeのbootstrapが未実装のASGを、稼働する計算poolの代わりに作成しません。

### 3 最新バックアップと移送証拠

初回のsnapshotは移行練習用として取得し、最終切り替え用とは区別します。実行中の旧DBに対して、read-only exported snapshotと同じsnapshotのpg_dumpを使い、table/catalog/sequence/role/ACLの比較記録を作ります。DB内容を標準出力へ流さず、保護されたファイルへ書きます。

最終snapshotは、旧API、worker、reviewer、reconciler、OCRなど全書き込み元の処理をdrainし、新規書き込みを止めてから取得します。既存の停止・起動制御と署名ロックを使い、別の更新と競合させません。既存サービスの停止を、データやvolumeの削除で代用しません。

sourceの実DB/host/volume identity、現在のKMS署名付きadmission、dump digest、catalogとroleの比較記録、保持するguest key fingerprintと外部resource identityを新しい移送証拠に結び付けます。旧署名のpayloadを編集せず、元のadmission履歴も残します。

### 4 Auroraへの復元と受理

移行先Auroraは本番と同じengine系統、非公開接続、TLSとCA検証で照合します。AWSのcluster/resource identityと実PostgreSQLの観測を結び付けます。RDSの管理roleはMacのtrue SUPERUSERと同じではないため、所有者・ACL・role mappingの差を明示して検証します。superuser向けglobalsを無条件にrestoreしません。

復元は検証対象の空の移行先へ行い、元のDBを上書きしません。行・sequence・catalog・資料原本・参照・権限を比較し、署名付きのsource→target移行admissionを専用経路で確定します。prepared_not_admittedの計画だけでは、復元・受理・本番readyの証拠になりません。旧Mac用bootstrapや更新validatorの同一host検査を外す変更では対応しません。

### 5 runtimeと容量モードの配備

arm64のWeb/APIとx86のworker/verifierを、固定したソースとtoolchainからbuildしてECR digestで配布します。reconcilerと別ホストverifierのmTLS、registry、claim、実行先のbinding、drainと再配送を実装・確認します。workerはDB資格情報を持たず、verifierはproviderやAWS資格情報も持ちません。

現行verifierは2 CPU・4GiBの上限検査があるため、提案の8GiBは契約と検査を改訂してから使います。Lean常駐化などの高速化も、Linuxの実メモリと隔離を測って有効化します。速さのためにLeanや独立レビューを省きません。

normalはlarge 1台、eventは指定したxlarge容量へ、新規ノードの準備→配送先変更→旧ノードdrainの順で切り替えます。待ち行列に基づく自動台数制御、上限、1時間超の処理、起動失敗、監視欠落、重複結果を確認します。単なるEC2の起動を、poolの準備完了とは扱いません。

### 6 DNS切り替え前の受け入れ

本番host名・TLS・Cognito callbackの条件を保った検証経路でAWS側を確認します。DNS切り替え前に少なくともログイン、既存履歴と資料、質問の前提確認、実際のモデル呼び出しとLean検証、回答保存、共有、ゲスト、課金・利用枠の表示を確認します。実課金・新たな購入は試験の範囲に含めません。

代表問題は、仮定を明示した実質的な推論が必要な題材を使います。禁止された単純な平方展開は使いません。再利用・初見・難問を分けて測り、単発と30件同時送信の全体時間、失敗、OOM、LLM制限を記録します。healthの200だけでは移行完了にしません。

### 7 最終同期とDNS originの切り替え

旧環境をdrainして書き込みを止め、最終snapshot・差分照合・受理をやり直します。AWS側の書き込みを開始する前に、一意の書き込み先を決めます。DNSの伝播だけでは旧側へ届く利用者を止められないため、旧APIの書き込み停止または新側への安全な転送を維持します。

Cloudflareの既存Web/APIレコードのoriginだけをALBへ向け、既存NSや不要なレコードを変更しません。対象レコードを変更前後で読み取り照合し、TLS、Cognito、SSE、既存データ、新規要求の確定を公開経路から再確認します。旧Tunnelは検証完了まで消しません。

### 8 監視と移行完了

公開経路の失敗率、各段階の待ち時間、API/worker/Leanの資源、DB、provider、費用を確認します。AWSへの新規書き込みがある場合、DNSを旧DBへ戻すだけの切り戻しは行いません。書き込み停止と逆同期または復旧手順を使い、二重書き込みとデータ欠落を防ぎます。

全機能と実データの照合、最新バックアップからの復旧、manual/auto容量制御、秘密情報と通信制限の確認を終えた後、不要な旧writerとTunnelを停止します。旧DB・volume・バックアップの削除はこの移行で自動実行しません。最後にAWS構成をread-backし、draw.io図を設計図から実配備図へ更新します。

## 完了判定

移行完了は、AWS上の実runtime、移送データと認証、公開DNS、実際のLean回答、既存機能、復旧と監視を確認した状態です。手順書、Terraform test、図、準備用CLIだけが完成しても移行完了とはしません。残った作業はこの表に残し、未実行・未配備を明記します。
