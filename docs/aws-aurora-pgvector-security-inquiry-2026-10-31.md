# Aurora PostgreSQLのpgvector修正状況に関する問い合わせ案

2026年10月31日確認。PAM-010のための未送信の下書きです。AWSへの連絡、サポートケースの作成、サポート契約の変更・購入は行っていません。

## 確認した事実と未確認事項

対象は東京リージョン`ap-northeast-1`のAmazon Aurora PostgreSQL互換16.15、Serverless v2です。手元の読み取り確認記録には`server_version_num=160015`、提供されている`vector`拡張は0.8.2とあります。サービス固有の詳細ビルド識別子は未取得です。確認記録の`aurora_version`欄がnullであることから、関数や識別子が提供されていないとは判断しません。

| 一次資料 | 確認できた内容 | 確認できない内容 |
| --- | --- | --- |
| [pgvectorの保守者による告知](https://github.com/pgvector/pgvector/issues/1036) | 2026年10月1日公開。IVFFlatインデックス作成時のCVE-2026-103484について、上流0.8.6以下が対象、0.8.7で修正と記載 | AWS管理版への適用状況 |
| [PostgreSQL CNAのCVE記録](https://raw.githubusercontent.com/CVEProject/cvelistV5/main/cves/2026/103xxx/CVE-2026-103484.json) | 公開日時は2026-10-01T19:49:03.670Z。上流の対象範囲は0.8.7未満。[修正コミット](https://github.com/pgvector/pgvector/commit/ee00d39ab30c2a7cf9510abf9288c624d91db156)を参照 | 管理版バイナリの修正有無 |
| [pgvector 0.8.7の変更履歴](https://raw.githubusercontent.com/pgvector/pgvector/v0.8.7/CHANGELOG.md) | 2026年10月1日付でIVFFlatの修正を記載 | AWSのリリース日や適用単位 |
| [Auroraの対応拡張一覧](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraPostgreSQLReleaseNotes/AuroraPostgreSQL.Extensions.html) | PostgreSQL 16の表で16.15に対応するpgvectorは0.8.2 | このCVEへのバックポートの有無。ページの更新日は確認できず |
| [Auroraの更新履歴](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraPostgreSQLReleaseNotes/AuroraPostgreSQL.Updates.html) | Aurora PostgreSQL 16.15の掲載リリース日は2026年9月29日 | 閲覧したページにこのCVE番号やIVFFlat修正の明示は見つからず |
| [AWS Security Bulletins](https://aws.amazon.com/security/security-bulletins/) | 公開索引とAWS公式ドメイン内の該当CVE検索を確認 | 今回の検索では、この管理ビルドに修正が含まれると確認できる告知は見つからず |

公開情報が見つからないことは、管理版が未修正である証拠にはなりません。表示上の拡張バージョンだけでは、脆弱とも修正済みとも断定できません。復元や検索の機能試験も、セキュリティ修正の確認には代えられません。現時点では、該当管理ビルドの修正有無と、根拠となるAWSの文書・ビルド識別子が未確認です。

## 日本語の送信文案

件名案　Aurora PostgreSQL 16.15のpgvector 0.8.2におけるCVE-2026-103484の修正状況

AWSご担当者様

Amazon Aurora PostgreSQLへの移行に向けて、管理版pgvectorのセキュリティ修正状況を確認しています。対象は東京リージョン`ap-northeast-1`、Aurora PostgreSQL互換16.15、Serverless v2です。対象環境で提供されている`vector`拡張のバージョンは0.8.2です。

上流の[保守者告知](https://github.com/pgvector/pgvector/issues/1036)と[CVE記録](https://raw.githubusercontent.com/CVEProject/cvelistV5/main/cves/2026/103xxx/CVE-2026-103484.json)では、IVFFlatインデックス作成時のCVE-2026-103484は0.8.7で修正されたとされています。一方、AWSの対応拡張一覧には、Aurora PostgreSQL 16.15のpgvectorとして0.8.2が掲載されています。表示バージョンだけでAWS管理版の修正有無を判断しないための確認です。

対象の管理ビルドに、CVE-2026-103484の修正、または同等のバックポートは含まれていますか。含まれる場合は、該当するAWSのアドバイザリ、リリースノート、またはビルド単位の確認根拠をご提示いただけますか。上流の[修正コミット](https://github.com/pgvector/pgvector/commit/ee00d39ab30c2a7cf9510abf9288c624d91db156)と同等の対応であることも確認したいと考えています。

サービス固有の詳細ビルド識別子は未取得です。確認に必要な識別子と、安全な読み取り方法をご指定ください。未適用または未確認の場合は、東京リージョンで修正を確認できる提供版と、必要なエンジン・拡張の更新をご案内ください。

本問い合わせは修正状況の確認です。脆弱性の再現や攻撃検証は依頼していません。アカウント情報、接続先、認証情報、顧客データは添付していません。

## English inquiry draft

Subject proposal: CVE-2026-103484 remediation status for managed pgvector 0.8.2 on Aurora PostgreSQL 16.15

Hello AWS team,

We are evaluating a migration to Amazon Aurora PostgreSQL and need confirmation of the managed pgvector build's remediation status. The environment is Aurora PostgreSQL-compatible version 16.15, Serverless v2, in Asia Pacific (Tokyo), `ap-northeast-1`. The `vector` extension version offered in this environment is 0.8.2.

The [upstream maintainer advisory](https://github.com/pgvector/pgvector/issues/1036) and [CVE record](https://raw.githubusercontent.com/CVEProject/cvelistV5/main/cves/2026/103xxx/CVE-2026-103484.json) identify CVE-2026-103484 in IVFFlat index building as fixed in pgvector 0.8.7. AWS's supported-extension table lists pgvector 0.8.2 for Aurora PostgreSQL 16.15. We are seeking build-specific confirmation rather than inferring remediation status from the displayed version.

Does this managed build contain the fix, or an equivalent backport, for CVE-2026-103484? If so, please provide an AWS advisory, release note, or build-specific confirmation showing that it includes the equivalent of [upstream commit ee00d39ab30c2a7cf9510abf9288c624d91db156](https://github.com/pgvector/pgvector/commit/ee00d39ab30c2a7cf9510abf9288c624d91db156).

We have not yet obtained a detailed Aurora-specific build identifier. Please specify the identifier needed and a safe read-only way to obtain it. If the fix is absent or its status is unconfirmed, please identify a verifiably remediated release available in Tokyo and any required engine or extension upgrade.

This is a remediation-status inquiry, not a request for exploit testing. No account identifiers, endpoints, credentials, or customer data are attached.

## 送信窓口と必要な手続き

AWSの[脆弱性報告ページ](https://aws.amazon.com/security/vulnerability-reporting/)には、セキュリティ上の懸念や質問の窓口として`aws-security@amazon.com`が掲載されています。サポートプランへの加入条件はそのページに記載されていません。ただし、バックポートの証明や返信期限が保証されているとは確認できません。この下書きでは、当該窓口への質問として扱えますが、新たな脆弱性を確認したとは主張しません。

AWS公式の[ケース管理](https://docs.aws.amazon.com/awssupport/latest/user/case-management.html)と[サポートプラン説明](https://docs.aws.amazon.com/awssupport/latest/user/aws-support-plans.html)によると、Basic Supportでは技術サポートケースを作成できません。本件を請求・アカウントの問い合わせに置き換えて、技術確認への対応を受けられるとは扱いません。

現在の契約プラン、IAM権限、サインイン状態、技術サポート窓口の利用可否は、アカウント上で確認していません。したがって「現在の無料サポートでこの技術問い合わせを送れる」とは記載しません。公開されたセキュリティ窓口の存在と、このアカウントでのサポート利用資格は別の確認事項です。

送信する場合の手続きは次のとおりです。

1. 利用者が文面と送信先を確認し、送信を明示的に指示します。この下書きの作成は送信の許可を含みません。
2. Support Centerを利用する場合は、契約プランと技術ケースの利用資格を読み取りで確認します。利用できない場合も、契約変更や購入は行いません。
3. 承認された窓口へ、上記の最小限の環境情報と公開資料のリンクだけを送ります。詳細識別子を求められた場合は、必要性と共有範囲を確認してから追加します。
4. 回答の対象となるリージョン、エンジンと管理ビルド、対象CVE、修正内容の根拠を記録します。一般的な「最新版」や表示バージョンだけの回答では、PAM-010の確認済み根拠にしません。

関連する移行判断は[PAM-010](../specs/domainless-production-bootstrap/private-aws-migration.md)、現在の実行記録は[移行検証記録](aws-migration-verification-2026-10-31.md)を参照してください。本書の作成では、AWS API、DB操作、メール送信、サポートケース作成、購入を行っていません。
