# AWS上で移行元と同じPostgreSQLを運用する代替案

2026年10月31日、ユーザーはこの方式と追加費用を承認しました。11:42 JST時点で、m7g.largeのprivate DBホスト、保持する80 GiBの暗号化data EBS、専用SG・endpointを配備し、同一内容のDBイメージを起動しました。実際のTLS1.3接続、PG16.15・libc2.36・locale・vector0.8.7を確認しました。空DBで、本番復元・受理とアプリ起動は未実施です。以下のbackup/PITR・standby・復旧試験は運用設計を含み、配備完了を意味しません。

この文書はEC2方式の設計と比較を記録します。実施済みの範囲は冒頭と検証記録に示し、backup/PITRや冗長化の未実施部分は設計として区別します。

## 検討する理由と確認範囲

分離Auroraへの復元では全行、権限、433件のvector queryが一致しました。一方、既存の3文字列項目ではdefault collationの並び順が異なりました。追加fixtureでは、基準環境の`lower(U+1C90)=U+10D0`と`upper(U+10D0)=U+1C90`に対し、Auroraはどちらも変換しませんでした。これはfixtureの実測であり、既存APIや利用者の操作に退行があるかは別のreplayで確認中です。Aurora管理版pgvectorの修正状況も未確認です。[現在の検証記録](aws-migration-verification-2026-10-31.md)と[未送信の問い合わせ案](aws-aurora-pgvector-security-inquiry-2026-10-31.md)を判断材料にします。

移行元と基準環境で観測した参照は、次のARM64イメージです。

```text
pgvector/pgvector@sha256:7b822b0aac60967beb1ea5e576b8602c94c300a157d187f385ae3e0da199b90a
```

PostgreSQL 16.15、pgvector 0.8.7、Debian 12、glibc 2.36、UTF8、`en_US.utf8`を固定します。DBコンテナ内でパッケージを更新しません。ECRへの複製時には、元のregistry参照、選択したARM64 manifest、configとlayerの対応を照合し、複製先の実digestを保存します。Dockerの`.Id`を一律にOCI config digestと見なしません。基準環境の復元成功は、Graviton上の動作、負荷、障害復旧の検証には代えられません。

| 比較点 | このEC2案 | 現在検証中のAurora案 |
| --- | --- | --- |
| DBの実装 | sourceと同じイメージ、拡張、glibcを保持する案。移植後の再確認は必要 | 管理版16.15.1、vector 0.8.2、glibc 2.26。実測差と修正根拠が未解決 |
| データと権限 | sourceのowner、role、ACLを保ちやすい。新hostのidentityと運用roleは別途審査 | 全行・権限の比較は通過。operatorのgrantorなど明示した対応が必要 |
| 更新と復旧 | OS、Docker、DB、バックアップ、復旧を運用者が担当 | DB基盤の保守をAWSが担当。アプリ互換性と復旧確認は利用者側にも残る |
| 障害時 | primary1台では停止。別AZへの復元と書き込み先の切り替えを自分で行う | 現構成もwriter1台で、別instanceへのfailover冗長性は未構成 |

## 最小構成と任意のstandby

最初の評価候補は`m7g.large`1台、2 vCPU・8 GiBです。基準DBは2 CPU・1 GiB制限の隔離コンテナで復元と機能比較に成功しましたが、少量のsnapshotを使った試験です。本番のpeak RSS、同時接続、autovacuum、checkpoint、バックアップ併走を測っていません。8 GiBはOSと監視、DB cache、保守処理に余裕を置く初期案であり、必要量や性能の実証値ではありません。

`t4g.medium`の2 vCPU・4 GiBは低価格の比較候補です。ただしCPU creditを使うため、継続負荷を測らずに安定したDB容量と扱いません。`m8g.large`も2 vCPU・8 GiBの候補です。AWSの[リージョン一覧](https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-regions.html)と[仕様表](https://docs.aws.amazon.com/ec2/latest/instancetypes/gp.html)で、東京のM7g・M8g・T4gとARM構成を確認しました。採用したm7g.largeは実AZで起動し、固定AMIとDBイメージのnative実行を確認しました。ほかの候補の在庫と動作は未確認です。

primaryは既存のisolated DB subnetの一方に配置します。公開IP、SSH、internet/NATへのdefault routeを持たせず、TCP5432の接続元は既存control SGだけに限定する案です。control側にも新DB SG宛ての5432 egressを明示します。PGDATAは専用の暗号化gp3 80 GiB、OSは暗号化20 GiBを初期案とし、data volumeはinstance終了時に削除しません。容量、IOPS、throughputは測定後に見直します。DBのTLSは固有のprivate hostnameとCAでverify-fullを行い、秘密鍵をサーバーだけへread-only mountします。

任意の別AZ構成は、同容量のもう1台にbase backupとS3上のWALを適用するwarm standby案です。DB間の5432を開けず、control-onlyの境界を保ちます。S3への到達とWAL取得にも別AZのendpointを用意します。未転送WALと再生遅延がRPOに影響するため、同期replicationや自動failoverとしては扱いません。streaming replicationを選ぶ場合はstandby専用SGからprimaryへの5432が追加で必要となるため、別の設計審査対象です。

standbyのhost側serviceがS3から取得したWALを復旧用spoolへ保存し、DBコンテナはそのspoolだけを読み取る案です。S3用資格情報をDBコンテナへ渡しません。取得済みWALとbase backupの検証が済むまで接続先に登録しません。

昇格はoperatorが旧primaryの停止・書き込み遮断を実際に確認してから行います。単なるhealth失敗で二つのwriterを作りません。private DNSまたは保護された接続先設定の更新、既存connectionの切断と再接続、timelineの保存、旧primaryの再参加までを復旧手順に含めます。RTOとRPOの許容値、担当者、夜間対応は未決定です。

## internetなしで起動・運用する経路

現行の[private network Terraform](../pals-infra/terraform/production/private_network.tf)では、S3 gateway endpointのroute table指定は`private_application`だけです。isolated DBのroute tableへ関連付けを追加し、専用backup prefix、ECR layer、必要なSSM配布物をendpoint policyで許可する変更が必要です。既存policyの許可を置き換えて削除しません。S3 gatewayは追加のendpoint料金なしでNATを使わずに利用できます。[AWSのS3 endpoint仕様](https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints-s3.html)

| 経路 | 最小案で追加するもの | 用途と境界 |
| --- | --- | --- |
| SSM | `ssm`、`ssmmessages`のinterface endpoint | 固定した新しいAgentで管理とSession Manager。受信用SSHは不要 |
| ECR | `ecr.api`、`ecr.dkr`のinterface endpointと既存S3 gatewayのDB route | 事前に複製したprivate ECRイメージだけを取得 |
| 監視 | `monitoring`、`logs`のinterface endpoint | 固定namespaceのmetricsと専用log groupへの送信 |
| backup | S3 gateway、専用prefixとbucket/KMS policy | 暗号化base backupとWALの保存・復元 |
| DNS・時刻 | VPC resolver、Amazon Time Sync | public DNSや外部NTPへの出口を作らない |

interface endpointは計6サービスです。private DNSを有効にし、endpoint SGの443 ingressをDB host SGだけに限定します。DB hostの443 egressはそのSGとS3 prefix listに限定し、DBコンテナからIMDS、hostの管理口、任意外部への通信を拒否する方針です。IAMの権限もendpoint policyも別々に検査します。

SSM Agentは3.3.40.0以降を固定し、`ssmmessages`を使う前提です。旧Agentを許容するなら`ec2messages`も追加して費用を再計算します。ECRは初回pull-through cacheを使いません。外部registryの取得と複製は承認されたbuild環境で済ませます。[SSMのprivate接続要件](https://docs.aws.amazon.com/systems-manager/latest/userguide/setup-create-vpc.html)、[ECRのendpoint要件](https://docs.aws.amazon.com/AmazonECR/latest/userguide/vpc-endpoints.html)

初回bootで`dnf`、Docker Hub、GitHub、外部package repositoryへ接続する手順は置きません。承認されたbuild環境でARM64のAL2023 AMIへDocker、固定SSM Agent、AWS CLI、CloudWatch Agent、PG16 backup toolsと運用設定を組み込みます。secretを入れず、AMI ID、所有者、内容hash、architectureをplanで固定する案です。DB hostはそのAMIから起動し、endpoint readinessを検査してからECRを取得します。AMI更新も同じbuild・検証を通し、既存data volumeを別hostで二重mountしません。

metricsの送信は`monitoring`、通常のlog送信は`logs`を使います。Live Tail用endpointやEC2 tag自動探索は最小案に含めません。DB host上で`GetCallerIdentity`や`AssumeRole`を使う実装を選ぶ場合は`sts`、直接KMS APIを使うSession暗号化などを採用する場合は`kms` endpointを追加します。S3がSSE-KMSを実行するだけなら、DB hostからの直接KMS接続とは分けて考えます。実装するAWS APIの全呼び出し先を照合してから、endpoint数と費用を確定します。[CloudWatch metrics](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch-and-interface-VPC.html)、[CloudWatch Logs](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/cloudwatch-logs-and-interface-VPC.html)、[Amazon Time Sync](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configure-ec2-ntp.html)

## 権限、バックアップと運用責任

| 主体 | 必要な権限の案 | 持たせない権限 |
| --- | --- | --- |
| 配備operator | 保存済みplanに固定したEC2・EBS・SG・endpoint・IAMの作成とreadback、指定SSM documentと対象instanceへの操作 | 既存Cognito・queue・artifact・署名鍵の変更、既存DB削除をこの案に混ぜない |
| DB hostのinstance profile | SSMの管理・4 channel操作、ECR取得、backup prefixへのS3書込み・検証読取り、必要なKMS利用、専用metrics/log送信 | アプリ用SSM secret、KMS Sign、他prefix削除、IAM変更、instance停止・昇格 |
| backup専用SQL role | localのbase backup/WAL streamに必要なREPLICATIONとLOGIN。接続先・認証を限定 | アプリroleへのmembership、SUPERUSER、DDLや通常の業務更新 |
| restore operator/standby | 固定backup versionのS3読取りとKMS Decrypt、指定hostのSSM操作 | backup書換え・削除、現primaryの自動昇格 |
| DBサーバーのコンテナ | sourceと同じDB roleを復元し、必要なPGDATAとTLSだけをmount | AWS/provider資格情報、Docker socket、IMDSへの接続 |

ECR token取得などresource指定できないAPIは、AWSの仕様に従いregion/accountと呼出主体を限定します。S3は専用prefix、KMSはS3経由とencryption contextへ絞ります。CloudWatchの`PutMetricData`はnamespace条件、Logsは事前作成したgroup/streamへ限定する方針です。実配備ではDB専用role、ECR取得、固定bootstrap object、backup prefixとS3経由KMSの条件を実装し、bootstrap取得とECR pullを確認しました。継続backupとmetrics/log送信の実動作は未検証です。EBS暗号化のためのKMS利用と、DB hostへ直接付けるKMS権限は区別します。[EBS暗号化の仕組み](https://docs.aws.amazon.com/ebs/latest/userguide/how-ebs-encryption-works.html)

バックアップ案は、host側の固定PG16 toolsによる`pg_basebackup`と`pg_receivewal --synchronous`、暗号化EBS上の専用spool、SSE-KMSのS3への転送です。DBイメージを改造せず、local接続だけをbackup roleへ許可します。base backup、WAL、timeline、manifestと設定のversionを対応付け、S3保存とchecksumの検証が済むまでspoolを消しません。backup roleの追加は明示的な運用差分として審査し、sourceのアプリ24 roleの照合を省略する理由にしません。[pg_basebackup](https://www.postgresql.org/docs/16/app-pgbasebackup.html)、[pg_receivewal](https://www.postgresql.org/docs/16/app-pgreceivewal.html)

`wal_level=replica`、`full_page_writes=on`を確認し、base backupとWAL受信が併走できる`max_wal_senders`、専用slotと上限を設定する案です。slotによる無制限のdisk消費を許容せず、上限到達後はbackup鎖を再構築する手順も用意します。設定値は既存接続と測定結果を踏まえて決めます。

localへのfsyncはS3への保存完了ではありません。低更新時のWAL segment完了待ち、転送遅延、slotによるWAL滞留、spoolとPGDATAの空き容量を監視します。segment切替間隔とretentionはRPOと保存費を測って決めます。dumpだけではPITRにならず、EBS snapshotだけでWAL鎖とDB整合性を確認済みとも扱いません。設定、証明書の再発行手順、秘密値の安全な復旧方法も別に保持します。[PostgreSQLのPITR手順](https://www.postgresql.org/docs/16/continuous-archiving.html)

採用前に、別の空volumeへbase backupとWALを実際に戻し、指定時刻までの復旧、全行・sequence・role/ACL、readerと既存APIを確認します。定期的な復元試験、復旧時間、最後にS3へ保存できたLSN、失敗通知を運用記録に残す案です。OSとcontainerの更新、セキュリティ情報、証明書更新、disk拡張、backup失敗、AZ障害への対応は運用者が引き受けます。同じimageを保持する利点と、古いimageを無期限に固定するリスクは別です。

## 東京の計画費用

2026年10月31日にAWSの公開Price Listを読み取りました。EC2はLinux、Shared、On-Demand、software NA、CapacityStatus Usedを選択しています。EC2一覧の公開日時は2026-10-29、VPC一覧は2026-10-16、対象料金の適用日はともに2026-10-01です。730時間/月、JPY150/USDは固定した計画換算で、現在の為替や円建て上限ではありません。[EC2東京Price List CSV](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/ap-northeast-1/index.csv)、[VPC東京Price List CSV](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonVPC/current/ap-northeast-1/index.csv)

| DB用EC2候補 | vCPU / RAM | USD/時 | 730時間のUSD | 計画円換算 |
| --- | --- | --- | --- | --- |
| t4g.medium | 2 / 4 GiB | 0.0432 | 31.54 | 約4,730円 |
| m7g.large | 2 / 8 GiB | 0.1054 | 76.94 | 約11,541円 |
| m8g.large | 2 / 8 GiB | 0.11594 | 84.64 | 約12,695円 |

T4g Unlimitedには余剰CPU creditのUSD0.04/vCPU時が別に発生します。料金比較に無料枠、Spot、Savings Plansは入れていません。[EC2 On-Demand料金](https://aws.amazon.com/ec2/pricing/on-demand/)

| m7g.large案の固定部分 | primary1台・endpoint1 AZ | 同容量2台・endpoint2 AZ |
| --- | --- | --- |
| EC2 | USD76.94 | USD153.88 |
| gp3合計100 GiB/host（設計時） | USD9.60 | USD19.20 |
| interface 6サービス×AZ数 | USD61.32 | USD122.64 |
| 小計 | USD147.86、約22,179円 | USD295.72、約44,359円 |

東京のgp3はUSD0.096/GB月で、標準の3,000 IOPS・125 MiB/sを使う仮定です。追加IOPS、throughputは含みません。interface endpointは東京のUSD0.014/サービス/AZ時を使い、最初の1 PBの処理量はUSD0.01/GBが別です。追加サービス1個につき1 AZで月USD10.22、2 AZでUSD20.44増えます。1 AZだけのendpointを別AZから使う案ではcross-AZ通信と障害依存が残るため、2 AZ構成の小計はendpointも複製しました。[EBS料金](https://aws.amazon.com/ebs/pricing/)、[PrivateLink料金](https://aws.amazon.com/privatelink/pricing/)

実配備では公式AMIの最小容量に合わせてrootを30 GiBとし、data80 GiBとの合計は110 GiBです。上表の100 GiBとの差は、同じ単価なら1台あたり月USD0.96です。

小計はDB案の固定部分です。税、backup/S3容量・request、KMS、ECR保存、metrics/log、endpoint処理量、AZ間転送、AMI作成と復元試験、LLM料金、運用工数は別です。既存control medium、Lean large、大会xlarge、ALB/NATなどの費用もこの表に含みません。既存Auroraを保持して比較する間はAurora料金も併存し、削除前提の差額を節約実績とは扱いません。

## 既存foundationからの差分と採用条件

既存VPC、2つのDB subnet、control/compute、ALB、Cognito、S3、SQS、署名KMSを維持します。Leanの通常large・大会xlarge、control mediumを変更しません。追加候補はDB EC2とdata EBS、DB/endpoint SG、6 endpoint、DB route tableへのS3関連付け、限定policy、ECR内のDB image、監視・backup設定、private接続先です。standbyは任意の追加です。Terraformで資源と所有者を追跡し、保存済みplanのaccount・Tokyo・state・source・config・digestを照合する実装が別途必要です。

Auroraを置き換えると決めた場合も、現時点で空の本番Auroraや検証clusterは削除しません。採用承認後にcluster/instance、parameter/subnet group、専用secret/SGなどの依存と保持要件を列挙し、対象を閉じた別cleanup planとして審査します。共用DB subnet、control SG、VPC、bucket、既存roleをまとめて消しません。sourceのDB・volume・サービスも保持します。

EC2方式の採用と追加費用は承認済みで、初期data EBSは80 GiBに確定しました。実DBの起動とTLS接続は確認しました。最終データの復元、既存API・検索のreplay、同時負荷、継続backupとPITR、AZ障害からの復旧、retentionとRPO/RTOの実測は残っています。

どちらを採用しても、新hostへの移送を結び付ける署名付きprofile、source drain後の最終capture、受理、全機能確認が必要です。履歴署名や今回の練習用snapshotを最終受理に流用しません。既存の厳密なvalidatorやsource資料を緩めず、公開DNSとwriterは承認された最終切り替えまで変更しません。
