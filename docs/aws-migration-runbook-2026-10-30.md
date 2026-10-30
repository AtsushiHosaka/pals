# PALSのMac miniからAWSへの移行手順書

開始日 2026年10月30日。ユーザーの指示により、本番移行、必要なAWS構成変更、DNSの向き先変更、draw.io図の作成を実施対象とします。Web・APIはt4g.medium、計算ノードは通常r8a.large、大会時r8a.xlargeを使う方針です。作業を完了した段階だけを実施済みとし、コード・ローカル試験・AWS配備・DNS切り替えを区別します。

DNSを先にAWSへ向けると、未準備の移行先へ利用者を送ってしまいます。まず現在のレコードと切り戻し先を保存し、AWS側でデータ・認証・証明生成を確認した後に向き先を変更します。Cloudflareのネームサーバーは維持し、ドメイン移管は行いません。

## 現在の実行状況

| 段階 | 状態 | 実際に確認したこと |
| --- | --- | --- |
| 対象と接続 | 実施済み | pals-prod-memberのSSOをユーザーが更新し、本番アカウントとの一致をSTSで確認 |
| 現行の公開サービス | 実施済み | WebとAPI healthのGETが200、未認証projectsが401。DNSはCloudflare経由 |
| AWS資源の棚卸し | 実施済み | 開始時点のCognito・S3・SQS・署名KMS・state bucketを特定。移行先EC2・Aurora・ECRは後続の基盤作成で追加 |
| 移行元への接続 | 練習用バックアップ取得済み | 同一snapshotのdump・schema・metadataと既存の配備署名資料を非公開S3へ転送。作業端末で6ファイルのハッシュを照合し、既存配備記録のKMS署名と固定公開鍵の検証に成功 |
| ACM証明書 | 発行済み | 現在のWebとAPIを対象に申請。Web/APIの検証に成功し、AWS ACMのISSUEDを確認 |
| private network実装 | 基盤作成済み・検証中 | 8 subnet、NAT、S3 endpoint、ALB、Auroraを作成。ALBログ書込みと経路を読み戻し済み。未使用legacy SGからのDB許可を除去し、controlだけに限定 |
| 既存資源の再利用 | 基盤で確認済み | 現在のCognito・S3・SQS・署名KMSを読み取り参照する経路を実装・試験済み。実planの独立照合中 |
| private control接続 | 実施済み | t4g.mediumを公開IPなしで起動。SSM Online、cloud-init完了、PG16.15 client、アプリ未起動markerを確認 |
| private compute接続 | 実施済み | r8a.largeを公開IPなしで起動。SSM Online、cloud-init完了、native x86 DockerとAMD EPYC 9R45、起動時のアプリ未配備markerを確認 |
| 短期AWS資格情報 | 実機検証済み | API/workerと各host supervisorの4 roleを分離。実STS認証とtimerによる更新、API image内のread-only mountからの資格情報検査に成功。parameter・master・署名権限なし |
| AWS料金アラート | 設定済み | 本番アカウント全体の月額予算をUSD650へ更新。実費USD20・50・100・650、月末予測USD520超過の5通知とメール宛先をAWSから読み戻して照合。自動停止actionなし |
| Lean単体の測定 | 実施済み | largeで48件の実コンパイルに成功。必要なimportとLake環境再利用で中央値0.805秒。アプリ全体の遅延は未測定 |
| DB移送と署名付き受理 | 練習用snapshot取得済み・復元未実施 | 専用の署名付き復元CLIとruntime検査を実装・試験。実Auroraでtyped SSM接続と空DBの読み取り検査を確認。互換性の復元比較、最終snapshotと移行受理は未実施 |
| AWS runtimeと容量モード | アプリ未配備 | x86 runtime、別ホストmTLS、pool配送、drain、通常・大会モードの実配備は未実施 |
| DNS切り替え | 未実施 | 現行Cloudflare originとMac miniを維持 |
| 移行後の受け入れ | 未実施 | ログイン、履歴、資料、生成、共有、ゲスト、負荷試験が必要 |

移行元はpgvector 0.8.7、作成したAuroraの提供版は0.8.2です。locale名と並べ替えライブラリの版も異なります。ユーザーはAuroraで先に互換性を検証し、データ・権限・検索結果を確認できた場合だけ採用する方針を選択しました。元のDBは変更せず、この差を解消するまで本番復元・受理を進めません。[AWSの対応拡張一覧](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraPostgreSQLReleaseNotes/AuroraPostgreSQL.Extensions.html)も確認しています。

上流のpgvector 0.8.7にはIVFFlat index作成時の脆弱性修正が含まれます。Auroraの管理版に同じ修正が取り込まれているかは未確認です。版番号だけで安全性を判断せず、AWSの該当buildについて根拠を確認します。[上流の修正情報](https://github.com/pgvector/pgvector/issues/1036)を、採用前の確認対象に加えています。

移行先ALB用のACM証明書、VPC・subnet・NAT・ALB・Aurora・ECR・必要なIAMと専用ALBログbucketを作成しました。Web/APIや計算runtimeはまだ起動していません。Cloudflareには証明書検証用CNAMEを1件追加しました。ACMの申請は配信先を変更しません。追加資源を作成した場合は、この表と秘密値を含まない実行記録を更新します。

## 移行する対象と保持する情報

Webの公開名は`palschat.site`、APIは`api.palschat.site`です。既存ログインのcallbackは`https://palschat.site/auth/callback`、logoutは`https://palschat.site`を維持します。使用中のCognito pool/client/issuerはそのまま使い、ユーザーやパスワードの移し替えは行いません。

アプリDBの全schema・行・sequence・所有者・ACL・署名付きadmission履歴を移送対象とします。資料の原本にはPostgreSQLのbyteaもあるため、S3だけを移せば完了するわけではありません。既存S3の成果物と参照、SQSのジョブ、ゲスト用hash key、provider接続、課金・利用枠・共有・継続質問の状態も維持します。

既存バックアップbucketには10月4日のphysical base backupが3件あります。10月30日には、新しい一貫したsnapshotに基づく練習用pg_dumpを取得しました。次に復元試験を行い、本番切り替え用には書き込み停止後のsnapshotを改めて取得します。

raw dump、DB接続先、鍵、provider token、Terraform plan/state、SSO cacheはGitに含めません。ローカルの作業記録はignoredの`.local/aws-migration/`に置き、ディレクトリ0700・機密ファイル0600を使います。クラウド上は既存の非公開backup bucketの専用prefixへ暗号化して保存し、許可した移送roleだけが取得します。

## 移行先のネットワーク

![AWS移行先の設計図](diagrams/pals-aws-private-target.png)

[draw.io元ファイル](diagrams/pals-aws-private-target.drawio)は編集可能で、PNGは実際のdraw.ioで出力しています。図の8 subnetとCIDRは基盤作成後に読み戻して照合しました。アプリ、計算poolと容量制御を含む図全体は、引き続き移行先の設計図です。

公開ALBは2つのpublic subnetに置き、ACMでTLSを終端してprivate controlのHTTPSだけへ接続します。Web・APIと計算ノードにはpublic IPを付けません。Auroraはインターネット向けdefault routeのないDB subnetへ置き、controlのsecurity groupからの5432だけを許可します。

外部LLMへの通信が必要なため、private workloadの外向きHTTPSにはNATを使います。S3はgateway endpointを使います。初期のNATは1台で、AZをまたぐ通信と単一障害点を含む費用・可用性の選択です。EC2にはSSHを開かずSSMで管理します。verifierはさらにコンテナ単位で外向き通信を遮断し、DB・AWS・provider資格情報を持たせません。

通常のEC2本体約2.6万円に、NAT・ALB・Aurora最低容量などが加わります。2026年10月30日のAWS Price List APIで、東京のZonal NATは$0.062/時、ALBは$0.0243/時、Aurora PostgreSQL Standard Serverless v2は$0.15/ACU時と確認しました。月730時間、Aurora平均0.5 ACU、public IPv4最低3個を$0.005/IP時、1ドル150円と置くと、本体とこれらの合計は約4.5万円です。mediumとlargeは準備用として起動済みで、金額は通常構成の月額見積もりです。ストレージ、I/O、LCU、NAT処理量、通信、ログ、税、LLM利用料と移行中の重複稼働は別途かかります。[VPC料金](https://aws.amazon.com/vpc/pricing/)、[ALB料金](https://aws.amazon.com/elasticloadbalancing/pricing/)、[Aurora料金](https://aws.amazon.com/rds/aurora/pricing/)を参照します。

料金アラートは、既存の`pals-prod-monthly-cost`を再利用しています。private構成の月額予算はUSD650で、実費がUSD650を超えた場合と、月末の予測費用がUSD520を超えた場合に`hosaka2917+pals@gmail.com`へ通知します。設計時の固定換算1ドル150円では、それぞれ約9.75万円・7.8万円です。為替への自動追従や円建ての支出制限は行いません。既存の実費USD20・50・100の通知と、別管理の旧予算は保持しました。

対象は本番AWSアカウント全体で、外部LLM providerからの直接請求は含みません。AWSの請求集計には遅れがあり、予測通知は利用履歴にも依存します。料金による自動停止actionは設定していません。5件すべての閾値とメール宛先を実際のAWSから読み戻して確認しましたが、メールの実配信試験は行っていません。[AWS Budgetsの更新と通知の説明](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-best-practices.html)を参照します。

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

現在は本番受理の前に、互換性の検証を行います。roleはcluster全体に存在するため、本番用に確保した空DBとは別のprivate検証clusterを使います。同じsnapshotを移行元と同等のPG16環境とAuroraへ復元し、全table・sequence・large object・所有者・ACL・制限付きroleを照合します。vectorの値と距離、検索順位、文字列検索、ページ境界と資料の抽出結果も比較します。[API側の検証計画](../pals-api/docs/aurora-compatibility-review.md)に対象を記録しています。この復元・比較はまだ実施していません。

現在の本番復元v1はextensionとlocaleの一致を要求しており、観測した組み合わせを拒否します。互換性の検証で通過しても、この検査や元の署名情報を書き換えません。採用する場合は、証拠に基づく別の復元profileを実装・審査し、最後に書き込みを停止したsnapshotで本番復元を行います。

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

## 基盤適用の記録

2026年10月30日23時24分ごろ、Mac miniから練習用バックアップの転送が完了しました。private S3の7 objectを確認し、移送manifestに指定した6ファイルをVersionIdで固定して取得しました。S3のAES256暗号化、サイズ、SHA256 checksumとmetadata、ローカルのSHA256を照合しました。dumpは4,353,802 bytesで、SHA256は`8ce5ae7517b1c843117d99a67be118eb055dd7e200d8aca69145c69859a38539`です。DBや旧サービスの停止・変更は行っていません。

23時36分、既存の配備manifest・DER署名・履歴registryを、APIの正式な`verify_predecessor`で検証しました。AWS KMS Verify、独立して固定した公開鍵SPKIとローカルP-256署名検証が通過しました。配備manifestのSHA256は`6718ad3f1d8fcc17cc463759bd7673f2438db3624a65c84bd7696ab2824921c3`です。この結果は履歴資料の署名検証であり、最終移送の受理や稼働中DBの書き込み停止を証明するものではありません。取得・検証receiptとraw資料はignoredの保護領域に保存しています。

2026年10月30日、初回planは新規74件、既存資源の更新・削除0件でした。Auroraなどの作成後、ALBのログ保存先の権限チェックで一部適用が失敗しました。ALB自体はactiveで同じARNと確認できたため、Terraformの交換マークだけを解除して保持しました。

ログ配送のSourceArn条件をAWS公式の同一リージョン・アカウント範囲へ修正しました。修復planはlistener新規2件、作成済みALBと専用ログbucketポリシーの更新2件、削除・交換0件です。適用後、access_logs=trueと、ELBAccessLogTestFileの実保存・AES256を確認しました。初回planや失敗したplanを再利用していません。

Aurora 16.15はavailable、暗号化・削除保護・7日バックアップ・0.5〜2 ACUと読み戻しました。VPCの8 subnetはいずれもpublic IP自動付与なしで、DBのroute tableにdefault routeはありません。private computeからDBへの許可もありません。続くoperator用planで未使用legacy host SGからのDB許可を除去し、実際の5432 ingressをcontrol SGだけに限定しました。

東京のStandard On-Demand上限は16 vCPUでした。大会用xlarge 4台とmediumには18 vCPU、最大8台の切り替え中併存には34 vCPUが必要なため、40 vCPUへの増枠を申請しました。申請はCASE_OPENEDであり、上限の承認や大会容量の準備完了とは扱いません。

private controlのoperator用planは新規5件、DB SG更新1件、削除・交換0件で適用しました。mediumは公開IPなし、暗号化40GiB gp3、IMDSv2必須・hop1、SSM通信5操作だけのinstance profileです。SSM実行でcloud-init完了、アプリ未起動・ALB未登録marker、PG16.15 clientを確認しました。

compute用planは新規5件、既存資源の更新・削除・交換0件で適用しました。largeはprivate compute subnetに置き、暗号化80GiB gp3、IMDSv2必須・hop1、SSM通信5操作だけのinstance profileです。実機のcloud-init完了、Docker linux/x86_64と2 CPU、AMD EPYC 9R45、アプリとbenchmarkが未実施であるmarkerをSSMで確認しました。

実Auroraへの読み取り試験は、SSM転送とAWS公式CA、元のRDS hostnameを使うverify-fullで成功しました。続いて正式なAPIのtyped transportとAurora・空DB検査でも成功しました。TLS1.3、palsadminは非SUPERUSERでCREATEROLE/CREATEDBあり、UTF8/en_US.UTF-8/provider c、collationの記録値と実値は2.26-59.amzn2でした。移行元のlocaleとの互換性、role mappingの実能力試験、実復元、署名付き受理と全機能の試験は残っています。

Lean childのファイル隔離は、verifierのTLS秘密鍵へ到達する可能性がある規則を修正しました。実鍵を使わないLinux canary、実Lean・Mathlib、Elan/nativeとsymlink拒否の試験が通過し、独立したLinux再実行13件も通過しました。[agent PR #22](https://github.com/AtsushiHosaka/pals-agent/pull/22)はdraftで、本番verifierサービスの起動はまだです。

その後、同じ修正を含むx86 imageをbuildして非公開ECRへpushし、large自身のECR権限で取得しました。アプリと資格情報を渡さない隔離コンテナで48件の実Lean測定に成功しました。実cgroupと隔離検査、標本・cache状態・メモリの限界は[測定記録](aws-native-lean-benchmark-2026-10-30.md)に残しています。HTTP/mTLSの本番runtime起動は別途確認します。

IAM分離のplanは新規11件、既存2 hostのinstance profile更新だけで適用しました。4 roleのtrustと全inline policyを読み戻し、host ID、非公開IP、parameter読み取り0件を照合しました。controlからAPI、computeからworkerの専用STS sessionを実際に発行し、各5分の更新timer起動を確認しました。これは資格情報更新の確認であり、アプリやpoolの稼働確認ではありません。

続いて両hostのtimerが実際に短期資格情報を更新したことを確認しました。API imageは固定digestで取得し、networkなし・read-only root・権限削除の一時コンテナで、別々にread-only mountしたpolicyと資格情報を既存readerが受理しました。アプリは起動しておらず、DB接続や生成処理の成功を示す試験ではありません。

private computeの初回起動helperは、AL2023のDocker25に合わせたimage検査、actorからhostへのINPUT通信制限、起動期限後にもSIGTERMを送る処理を修正しました。独立レビューで追加の指摘はなく、rootによる再実行も171件通過しました。これらはコードと隔離した試験の結果で、実機のfirewall・mTLS・queue drainは未検証です。起動helperの本番実行も行っていません。

料金通知のplanは予算1件の更新、新規・削除0件でした。既存3通知が保持され、予算額と2通知の追加以外に差分がないことを保存済みplanから独立に照合して適用しました。適用後も予算額・全通知・全宛先・自動停止actionなしをAWSから確認しました。Terraform validateと既存production試験13件は通過しています。
