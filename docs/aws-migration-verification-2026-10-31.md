# AWS移行の復元・配備準備の検証記録

2026年10月31日11:42 JST時点の記録です。ユーザーの承認により、移行先DBを現行と同じPostgreSQL・pgvectorイメージのprivate EC2へ変更しました。DBサーバーの起動と読み取り接続まで完了しています。DBの本番復元・受理、アプリのAWS起動、DNS切り替えは未実施です。公開先は引き続きMac miniです。

## 10月31日午前の実機確認

| 対象 | 実際の結果 |
| --- | --- |
| DB基盤 | 独立stateの保存済みplanを適用し、25資源を新規作成。既存資源の更新・削除なし |
| DBホスト | `i-041db5930304ef5d1`、m7g.large、`10.42.10.172`、public IPなし、IMDSv2、SSM Online |
| ディスク | 暗号化した80 GiB gp3を保持。`vol-007fcbf9fa67f80fd`を`/srv/pals-postgresql`へmountし、実UUID・device・PGDATAの対応を照合 |
| DBイメージ | sourceと同じ内容をECRへ保存し、実コンテナのconfigと全16 layerをECRのOCI連鎖と照合 |
| DBのTLS・SQL | 実SSM転送とCloudTrailの接続先一致、証明書・hostname検証付きTLS1.3接続、PostgreSQL16.15、libc2.36、`en_US.utf8`を確認。vector0.8.7が利用可能 |
| 空の移行先 | アプリroleとアプリobjectはともに0。データ復元・本番受理は未実施 |
| DB認証情報 | 新規master passwordとDB用TLS秘密鍵の指定先への配備をユーザーが許可。非公開S3の固定versionをSSE-KMSで転送し、指定DBホストへ配備済み |
| DBネットワーク | control SGから5432のみ。DB専用の6 interface endpointはprivate DNS無効で、DBホストだけの名前解決を使う。既存control/computeのVPC DNSを変更しない |
| 公開入口 | 専用WAFの新規3資源を適用。実ALB association、default BLOCK、Cloudflare公式15 IPv4 CIDRの実送信元だけの許可、request sampling無効をAWSから読み戻し |
| hostのSSM権限 | 承認済みのcontrol4件・compute3件について、完全一致名のGetParameterだけを追加。アプリactorとverifierには付与しない |
| native worker | AWS x86実機でimport試験を通過。ECR認証を`/run`のtmpfsに限り、終了後の削除を確認。queue処理と本番回答生成は未検証 |

DB起動コマンド`e2f186c0-3190-4a2b-ab41-a125aea1655a`と独立observer`a621da98-3315-4d66-9238-383c5083d458`は実SSMでSuccess/0でした。読み取りSQL観測のSHA256は`d8cc6857c695f59c1f53c58c71a1c1494836f2c3ace004f810d7a0d4fd145c08`です。これらを本番復元・アプリ起動の証拠には扱いません。

最終取得前に、Mac miniの既存watchdogをmaintenanceにし、実MacとLinuxコンテナのlock伝播を確認します。取得に失敗した場合も、watchdogが旧writerを勝手に再開しないことが必要です。最終取得・署名・受理と実アプリの確認が通るまでDNSは変更しません。

以下は練習用バックアップとAurora比較の記録です。Auroraを本番DBとして採用した記録ではありません。

## 練習用バックアップ

Mac miniのサービスを稼働させたまま、同じexported snapshotからdump、schema、metadataを取得しました。既存配備manifest、DER署名、履歴registryを含む6ファイルを非公開S3へ暗号化して転送し、VersionIdを固定して作業端末へ取得しました。サイズ、S3 checksum、metadataのSHA256とローカルSHA256を照合しています。

新しいmetadata v2では、25個のroleについて実際の11項目を取得しています。`rolconfig`は全roleでNULLでした。旧metadataに欠けていた値を推測で補ってはいません。

| 保持した証拠 | SHA256 |
| --- | --- |
| 今回の移送manifest | `32cbfe80ea5e6f0c2375bd08f89e4485a2b39fe347045c46136af597595e0fd0` |
| dump、4,353,802 bytes | `3f1fe8d9379b37f91dc8dfc04a93d3154bc81a5e27d00e91bf9b8da4ce251cd7` |
| 既存の配備manifest | `6718ad3f1d8fcc17cc463759bd7673f2438db3624a65c84bd7696ab2824921c3` |
| 基準環境の検証receipt | `053eaf5c1ed17eb7a13678354d51855f43b16a326a88fbd5fe75f5bfa923fc6d` |
| 分離Auroraの復元・比較receipt | `427ae344600bc6d63e5bc02f6be001d2e49eea384403785f3f9090e339e0fd8f` |
| 追加の検索・照合順序比較 | `d235f4b3ebfbddcd2e83e2c728796f6c7de930b78cd91b0774835abc637c158b` |
| 実アプリと文字変換・全文検索成分の比較 | `2d761f3412bf91dda29386749be86ff2ae391ca654a4c5ffe2ec89d64d6607f5` |

既存配備資料は、正式な`verify_predecessor`でAWS KMS Verify、固定した公開鍵SPKI、ローカルP-256署名を検証しました。履歴の署名が正しいことと、最終切り替えの受理は別の確認です。今回のsnapshotは書き込み停止を要求しておらず、本番切り替えにはdrain後の最終取得が必要です。

raw資料、DB内容、認証情報、実行ログとreceiptはignoredの保護領域へ保存しています。この文書には含めません。

## 移行元と同じ環境への復元

移行元と同じ`pgvector/pgvector`イメージdigestを取得しました。実際のbuild文字列もPostgreSQL 16.15、Debian 12、aarch64で一致し、pgvector 0.8.7、`en_US.utf8`、libc 2.36を確認しています。専用コンテナはnetworkなし、公開portなし、root filesystemはread-onlyです。既存の開発コンテナは変更していません。

全1,098個のarchive項目を保持し、所有者とACLを含めてsingle transactionで復元しました。sourceのpasswordはコピーせず、5個のLOGIN roleには検証用の新しい値を使っています。

| 比較対象 | 実際の結果 |
| --- | --- |
| 全tableのCOPY内容 | 108テーブル、6,390行。件数と行順に依存しないSHA256が一致 |
| アプリroleとmembership | 24 role、18 edgeの属性とgrantorが一致 |
| 取得済みの所有者・ACL情報 | effective ACLへ正規化して全項目一致 |
| schema | 全1,311 SQL文のPG16構文木が一致。文字列の正規化後hashは一致せず、この差も保存 |
| sequence | 3個すべての位置と`is_called`がarchiveと一致 |
| large object | sourceと復元先ともに0個。資料のbyteaはtable比較に含む |
| vector | 2列のbinary hashを取得。`dsp_drafts`の433行で自己距離はすべて0 |
| 制限付きreader | 実際のLOGINでNaturalDraftReaderとhybrid readerを実行し、それぞれ433件から8件を取得 |
| readerの権限制限 | UPDATE、public schemaへのCREATE、schema ownerへのmembershipがないことを確認 |

生成列`pals_recipe_search.entries.search_vector`の対象tableは0行でした。元DBのconnection limitは今回のmetadataに含まれず、元の値との一致は未確認です。基準環境でのreader実行だけでは、Auroraでの検索結果の一致を証明しません。

追加の読み取り専用試験で、全433件の既存vectorをそれぞれqueryに使い、上位8件、計3,464件のIDと距離を取得しました。既存の5種類の文字列項目、計3,723値についても、default collationで並べた値のhashを保存しました。基準資料のSHA256は`b3e45a2379ed8e65a5cedd9def1eaed009d88aba1c4d41f896245c5b6a6f00c4`です。アプリreaderの試験とは別のDB検索・照合順序の試験で、Auroraとの比較結果は後述します。

## Auroraの分離と実測

本番用に確保した`pals-prod-aurora`は空のまま保持しています。roleはcluster全体に存在するため、検証には別の`pals-prod-compat-7650da7ee9c7`を作成しました。新しいTerraform rootとstate keyを使い、保存済みplanの新規5資源だけの作成を独立レビューして適用しました。

実AWSから、暗号化、非公開writer、指定した2つのDB subnet、0.5〜2 ACU、専用SGを読み戻しました。DB ingressはcontrol SGからのTCP5432だけで、DB subnetにdefault routeはありません。検証clusterの削除保護は無効、backupは1日で、後片付け時のfinal snapshotは作らない設定です。本番用clusterの保護設定は維持しています。

SSM転送、実RDS hostname、公式CAのverify-full、TLS1.3で空DBを確認しました。CloudTrailの実StartSessionイベントでも、同じsessionの転送先hostとportが一致しています。

今回の本番用・検証用Auroraでは、SQLのsystem identifierが同じ値でした。この値だけでclusterを識別しません。AWS resource ID、endpointのTLS検証、検証用の別master credentialとSSMの転送先を合わせて照合しています。

role能力試験では、operatorの属性は想定どおりでした。一方、NOLOGIN roleを1個作った直後の自動membershipは0件でした。現行の本番復元profileは自動membershipの存在を要求するため、そこで停止しています。診断用roleはrollbackされ、アプリroleが0件へ戻ったことを確認しました。元のvalidatorや署名資料を書き換えず、実際のGRANT、SET ROLE、所有者変更と解除の能力を別の試験で確認します。

続く3 roleのrollback試験では、GRANT、SET ROLE、schema・tableの所有者変更とtable ACLの付与・解除が実行できました。operatorによるrole付与のgrantorは`rdsadmin`として記録され、アプリroleによる委譲とself-grantorの別edgeも保持されました。このため、source operatorの14 edgeとアプリgrantorの4 edgeを分けて比較する必要があります。

一時SET edgeの解除では、`GRANTED BY compatadmin`はSQLが成功してもedgeを残しました。`GRANTED BY rdsadmin`は権限エラーとなり、通常の`REVOKE ... RESTRICT`で実際のedge消失を確認しました。SQLの終了コードだけで解除成功と判定しません。いずれの診断も最後にrollbackし、role・schema・tableが残っていないことを確認しています。

この実測に基づく検証専用profileで、全24 role、18 edge、24個の一時SET edgeを付与しました。source operatorの14 edgeだけを実際のcatalog grantorへ対応させ、アプリgrantorの4 edgeと全role属性を保持しています。一時edgeを解除し、元の18 edgeだけへ戻ることを実Auroraで確認しました。試験全体をrollbackし、空DBへ戻ったことも照合しています。

続く復元はschema準備中に停止しました。処理を分けたrollback診断で、roleの導入と`pgcrypto 1.3`、`vector 0.8.2`の作成は通過し、所有者のschema CREATE権限を確認する既存guardで止まったことを確認しました。基準環境でも、`pals_draft_candidates`内の`raw_recipe_admissions`を所有するNOLOGIN roleにはCREATE権限がありません。guardや署名済みsourceを書き換えず、失敗したtransactionはrole・extension・schemaを含めてrollbackしました。

別のrollback試験では、そのNOLOGIN roleへの追加CREATE権限なしで、空の検証tableと付随するrow型・array型の所有者を変更できました。全schemaのeffective ACLをsourceと一致させ、同roleのCREATEがfalseのままであることも確認しました。診断用の操作はすべてrollbackしました。

この実測に基づく別の検証専用profileを独立レビューし、Auroraへ実データを復元しました。全108テーブル・6,390行のhash、所有者・effective ACL・sequence・vector binary・schema構文木を照合し、明示したDB owner、DB ACL grantor、extension、localeの差以外は一致しました。24 roleの全属性を確認し、一時operator edgeをすべて解除して、14個のgrantor対応を明示した18 edgeだけが残ることを確認しています。実テーブルと付随する型の所有者、元のschema ACL、CREATEがfalseの状態も保持しました。これは正式な本番受理ではありません。

5個のLOGIN roleすべてで、実際の認証とTLS1.3接続に成功しました。制限付きreaderのNaturalDraftReaderとhybrid readerは、基準環境と同じqueryで結果が完全一致しています。UPDATE・public CREATE・schema ownerへのmembershipがないことも確認しました。

追加した全433件のqueryでも、上位8件のIDと順序、JSONに保存した距離値は完全一致し、距離の最大差は0でした。MATERIALIZED CTEによる全件比較であり、ANN index、HTTP/API、回答生成速度の試験ではありません。元のsnapshotにANN indexはありません。

一方、default collationによる並び順は、`canonical_statement`、`proof_strategy`、`sketch_step`の3項目で不一致でした。`id`と`openmath_xml`は一致し、5項目とも件数は同じです。比較処理はこの不一致で失敗として終了しました。データ消失とは判定していませんが、アプリの検索・ページ境界・case変換への影響を調べる必要があります。この差を無視して互換性を通過扱いにはしません。

続く調査では、3項目を直接並べ替えるアプリ処理は見つかりませんでした。実際の`PostgresProjectRepository._list_page`と`PostgresChatRepository._search`を、同じAPI実装と制限付きLOGINで呼び出しました。全16所有者・11 projects・53 chatsについて、page size 1・2・10、8種類の検索入力の結果、型とcursorが一致しました。両方の接続でread-onlyを実確認しています。各repository呼び出しが別のstatement snapshotになる範囲も記録し、共通のexported snapshotを使ったとは扱っていません。

既存のproject名・説明、問題文、資料名・page本文、Draftの全項目とstepsを対象に、3,828行の入力、NFKC・大小文字変換、simple/englishの全文検索成分も一致しました。資料contextの実methodは`FOR UPDATE`を含むため呼び出しておらず、ここで確認したのは文字変換と全文検索の成分です。全HTTP機能や資料の選択・抜粋の結果まで通過したとは扱いません。

公開文字だけの追加試験330組では、不一致が残りました。チャット検索で使う`strpos(lower(normalize(value,NFKC)),term)>0`に、値`Ა`（U+1C90）とquery`ა`（U+10D0）を与えると、基準環境はtrue、Auroraはfalseでした。queryの大小文字を変えた重複ケースを含む2行で同じ差を確認しています。既存データの比較が通っても、将来の検索条件の差は解消していません。比較処理はこの差を保持して失敗として終了しました。

復元commit後の独立した読み取りでも、24 roleと18 edgeが計画どおりであることを再確認しました。receiptのSHA256は`e08c1aefe8da97d17ab14607a6553ee39e1789e8674d9954e0d6b1c195669e6c`です。

sourceのpgvector 0.8.7に対し、このAuroraの提供版は0.8.2です。公式SQLで実測したAuroraの版は`16.15.1`でした。localeとlibcも異なります。さらに、[上流の0.8.7修正](https://github.com/pgvector/pgvector/issues/1036)が[対応するAWS管理版](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraPostgreSQLReleaseNotes/AuroraPostgreSQL.Extensions.html)へ取り込まれている根拠は未確認です。版番号だけで管理版の安全性を断定しません。機能比較が通っても、この確認の代わりにはなりません。[問い合わせ文案](aws-aurora-pgvector-security-inquiry-2026-10-31.md)を用意し、送信の許可を待っています。

## runtimeイメージの準備

追跡済みの固定commitからbuildし、API・Web・workerを既存の非公開ECRへpushしました。sourceとCPU構成を照合し、実際のdigestを読み戻しています。verifierは前段のLinux実機試験で使ったimageを保持しています。

| 用途 | CPU構成 | 固定source | ECR digestの先頭 |
| --- | --- | --- | --- |
| API | arm64 | `7027478ef6664a0ab8f8a245e3da714e18dc0f37` | `e870dc5d2d4d` |
| Web | arm64 | `89daac472e89ac9800563b81f360d43e73cc7665` | `eb52fbaa64ce` |
| worker | amd64 | `0a45e4984538dc82294ad41994309081eddb9296` | `1b57f44cc2ef` |
| verifier | amd64 | `0a45e4984538dc82294ad41994309081eddb9296` | `6fe2a2e7e2b9` |

Webはnetworkなし・公開portなしの短命コンテナで起動し、トップ、サインイン、登録、password再設定、ゲスト入口の5画面でHTTP200を確認しました。既存Cognitoのpool/client、callbackとlogoutを使っています。実ログインとAWS公開経路の確認は残っています。

APIとworkerは、資格情報なし・非root・networkなしで正式モジュールのimportが通過しました。workerの試験はMac上のamd64実行で、AWS native実機の確認は未完了です。これらの準備は、アプリの本番起動やqueue処理の確認には含めません。

東京のStandard On-Demand上限は、実際のService Quotasで40 vCPUへ増えたことを確認しました。想定する大会用xlarge 4台とmediumの18 vCPU、切り替え中の最大8台とmediumの34 vCPUを収容できる枠です。ASGやready slotの実配備・負荷試験は未完了です。

## runtime秘密値の引き継ぎ準備

[専用helper](../pals-scripts/aws-migration-source-runtime-secrets.py)は、既存controllerのlockと稼働中コンテナのidentityを照合し、固定した5件だけを同AWSアカウント・東京のSSM SecureStringへ移す処理です。秘密値はstdinで渡し、ファイル、argv、標準出力やreceiptへ保存しません。既存値が異なる場合は上書きせず、一致する既存値だけを再利用します。書き込み結果が不明な場合は、読み取り専用の明示的なreconcileが必要です。

ユーザーは5項目のSSM転送、control/compute supervisorへの限定した読取権限、RAM内だけのECR短期token利用を許可しました。権限追加とnative worker試験は実施済みです。秘密値の転送はMac mini側のCLI入力方式で停止しており、完了していません。既存値と異なる値を上書きせず、不明な書込結果は構造化レスポンスで照合してから再開します。

EC2方式の選択と追加費用は承認済みです。DBサーバーは前述のとおり起動しました。最終snapshot、全データ・権限の復元照合、署名付き受理、実runtime、全機能、容量制御、DNSと復旧の確認が残っています。[移行手順書](aws-migration-runbook-2026-10-30.md)で実施状況を更新します。
