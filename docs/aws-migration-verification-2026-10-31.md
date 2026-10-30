# AWS移行の復元・配備準備の検証記録

2026年10月30日から31日に実施した作業の記録です。移行元と同じ環境への復元は成功しました。Auroraは別の検証clusterを作成し、roleの自動membershipが想定と異なるため、復元前の能力検証を続けています。本番受理、アプリのAWS起動、DNS切り替えは未実施です。

## 練習用バックアップ

Mac miniのサービスを稼働させたまま、同じexported snapshotからdump、schema、metadataを取得しました。既存配備manifest、DER署名、履歴registryを含む6ファイルを非公開S3へ暗号化して転送し、VersionIdを固定して作業端末へ取得しました。サイズ、S3 checksum、metadataのSHA256とローカルSHA256を照合しています。

新しいmetadata v2では、25個のroleについて実際の11項目を取得しています。`rolconfig`は全roleでNULLでした。旧metadataに欠けていた値を推測で補ってはいません。

| 保持した証拠 | SHA256 |
| --- | --- |
| 今回の移送manifest | `32cbfe80ea5e6f0c2375bd08f89e4485a2b39fe347045c46136af597595e0fd0` |
| dump、4,353,802 bytes | `3f1fe8d9379b37f91dc8dfc04a93d3154bc81a5e27d00e91bf9b8da4ce251cd7` |
| 既存の配備manifest | `6718ad3f1d8fcc17cc463759bd7673f2438db3624a65c84bd7696ab2824921c3` |
| 基準環境の検証receipt | `053eaf5c1ed17eb7a13678354d51855f43b16a326a88fbd5fe75f5bfa923fc6d` |

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

## Auroraの分離と実測

本番用に確保した`pals-prod-aurora`は空のまま保持しています。roleはcluster全体に存在するため、検証には別の`pals-prod-compat-7650da7ee9c7`を作成しました。新しいTerraform rootとstate keyを使い、保存済みplanの新規5資源だけの作成を独立レビューして適用しました。

実AWSから、暗号化、非公開writer、指定した2つのDB subnet、0.5〜2 ACU、専用SGを読み戻しました。DB ingressはcontrol SGからのTCP5432だけで、DB subnetにdefault routeはありません。検証clusterの削除保護は無効、backupは1日で、後片付け時のfinal snapshotは作らない設定です。本番用clusterの保護設定は維持しています。

SSM転送、実RDS hostname、公式CAのverify-full、TLS1.3で空DBを確認しました。CloudTrailの実StartSessionイベントでも、同じsessionの転送先hostとportが一致しています。

今回の本番用・検証用Auroraでは、SQLのsystem identifierが同じ値でした。この値だけでclusterを識別しません。AWS resource ID、endpointのTLS検証、検証用の別master credentialとSSMの転送先を合わせて照合しています。

role能力試験では、operatorの属性は想定どおりでした。一方、NOLOGIN roleを1個作った直後の自動membershipは0件でした。現行の本番復元profileは自動membershipの存在を要求するため、そこで停止しています。診断用roleはrollbackされ、アプリroleが0件へ戻ったことを確認しました。元のvalidatorや署名資料を書き換えず、実際のGRANT、SET ROLE、所有者変更と解除の能力を別の試験で確認します。

sourceのpgvector 0.8.7に対し、このAuroraの提供版は0.8.2です。localeとlibcも異なります。さらに、[上流の0.8.7修正](https://github.com/pgvector/pgvector/issues/1036)が[対応するAWS管理版](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraPostgreSQLReleaseNotes/AuroraPostgreSQL.Extensions.html)へ取り込まれている根拠は未確認です。版番号だけで管理版の安全性を断定しません。機能比較が通っても、この確認の代わりにはなりません。

## runtimeイメージの準備

追跡済みの固定commitからbuildし、API・Web・workerを既存の非公開ECRへpushしました。sourceとCPU構成を照合し、実際のdigestを読み戻しています。verifierは前段のLinux実機試験で使ったimageを保持しています。

| 用途 | CPU構成 | 固定source | ECR digestの先頭 |
| --- | --- | --- | --- |
| API | arm64 | `187191753eca58ce425e0a9a8b8a3edc51c16abc` | `bbcf45449f8c` |
| Web | arm64 | `89daac472e89ac9800563b81f360d43e73cc7665` | `eb52fbaa64ce` |
| worker | amd64 | `0a45e4984538dc82294ad41994309081eddb9296` | `1b57f44cc2ef` |
| verifier | amd64 | `0a45e4984538dc82294ad41994309081eddb9296` | `6fe2a2e7e2b9` |

Webはnetworkなし・公開portなしの短命コンテナで起動し、トップ、サインイン、登録、password再設定、ゲスト入口の5画面でHTTP200を確認しました。既存Cognitoのpool/client、callbackとlogoutを使っています。実ログインとAWS公開経路の確認は残っています。

APIとworkerは、資格情報なし・非root・networkなしで正式モジュールのimportが通過しました。workerの試験はMac上のamd64実行で、AWS native実機の確認は未完了です。これらの準備は、アプリの本番起動やqueue処理の確認には含めません。

次はAuroraの権限・データ・検索の比較を行います。採用できる場合も、別の署名付き復元profile、最終snapshot、実runtime、全機能、容量制御、DNSと復旧の確認が必要です。[移行手順書](aws-migration-runbook-2026-10-30.md)で実施状況を更新します。
