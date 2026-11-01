# PALSのAWS構成図

2026年11月2日00:25 JSTに公開を再開したseq11の構成を示します。全7コンテナ、サービス間TLS、Auroraの35段階の状態確認、カタログ保持、復旧unitを確認した配備図です。ネットワーク構成とEC2の配置はseq7から変えていません。ログインなしでのRecipe再利用とLeanソース表示は公開後に確認しました。選択モデルの利用量精算は引き続き確認中です。構成変更時には実設定を再確認して更新します。

![PALSのAWS構成図](pals-aws-private-target.png)

[PNGを拡大](pals-aws-private-target.png) · [編集可能なdraw.ioファイル](pals-aws-private-target.drawio)

## 配置と通信

| 層 | 配備構成 |
| --- | --- |
| 公開入口 | Cloudflare DNS・Proxy → WAFを関連付けた公開ALB → private controlのCaddy。WebとAPIの両ドメインでHTTPSを使用 |
| Web・API | ap-northeast-1aのprivate control subnetにt4g.mediumを1台。Web、API、Caddy、reconcilerの4コンテナ |
| Lean・生成 | ap-northeast-1aのprivate compute subnetにr8a.largeを1台。評価worker、証明worker、Lean verifierの3コンテナ |
| DB | isolated DB subnetのAurora PostgreSQL 16.15・pgvector。writerは1台。controlからTLSで接続 |
| 非同期処理 | APIとworkerがSQSを利用。workerはprivate APIへHTTPSで接続し、reconcilerはverifierへmTLSのTCP 18117で接続 |
| 外向き通信 | control・computeの許可された通信はNAT Gateway 1台を経由。S3はGateway Endpointを経由 |
| 運用 | AWS SSOとSSMを使用。EC2に公開IPv4を付けず、SSHポート・踏み台を設けない |

Public、control、compute、DBのsubnetはap-northeast-1aと1cにあります。subnetが2AZにあっても、Web・API、compute、NAT、Aurora writerは各1台です。全層が冗長化されている構成ではありません。computeからAuroraへの直接接続は許可していません。verifierにはDB・AWS・LLMの資格情報を渡しません。

WAFはCloudflareの公式IPv4範囲を許可し、既定では拒否します。この範囲はCloudflare全体で共有されるため、特定zoneの認証を意味しません。Cognitoによる利用者認証とアプリの認可も必要です。

## 確認済みの状態と残る作業

seq11のmanifestは`a22a5f2f0a98d15b761f679cfa2e7f19f0307f9af5398d0c14d63a502c84e9c7`です。controlの確認はSSM `6bd9fedd-4332-4fab-b3e4-3e43ca9b8602`、computeの確認は`2270fca6-704e-461e-9296-1b8a898a8944`で成功しました。00:25:23 JSTに元のALB listenerとruleへ戻しました。配備用の一時KMS検証・RDS参照ポリシーは削除し、不在を確認しました。

チャットからGPT-6.1 Terra・GPT-6.1 Sol・GPT-6 Lunaと、推論量low・medium・highを選べます。既定はTerraのmediumです。自動的なモデル切り替えは行いません。seq10でRecipe再利用と独立審査の並列化を配備し、seq11で新しい検証記録をゲストの回答取得にも適用しました。Web・verifierのイメージとtoolchainは保持しています。

| 配備元 | commit |
| --- | --- |
| 親リポジトリ | `f6f02bc4f876aef13e688fec8d21b01af1a522bc` |
| API | `9b8b004463f2be2579eb80d71149a4378eeb4675` |
| worker | `122f2f92e75220c3f34e224b20a63bb28addde2c` |
| infra | `46f4010177a1ea5a79a785d312acc122ad8581be` |
| Web | `a74b57b130ac0de6c7bf793ca095e81b54c4344f` |

controlのruntime configは`471a10a3d221782f84e73aeaf6e51879d5cb3114fb6b40233649ed7c5398f939`、computeは`cdc9ecc975ec80f2c70d56db2ba657d04a6bec5c9e94fc2571f5c98a243baff6`です。両ホストとカタログを集約した確認記録のSHA-256は`c3e2d53c0dde86131eeebc1fcd331ecbb6e26f7ae88a581f6d7d0a3419fd5269`です。

ログインなしで、0を含む自然数冪の連続性を同じ問題文で3回送信しました。送信クリックから回答表示までは4.775秒・4.664秒・4.830秒で、保存済みRecipeの回答とLeanソースを取得できました。DBでの回答保存までは2.664秒・2.507秒・2.683秒でした。別の読み取り確認SSM `1135bd28-7d27-4f16-865f-2fc2f6ea5972`で、3件ともモデル呼び出し・新規証明jobが0件であることを確認しました。

高速経路は、独立審査済みの完全な日本語入力2文を対象とし、文脈・資料がなく規約が一致する場合に限ります。公開実測したのはそのうち1文です。通常経路の独立した審査も並列化しましたが、すべての質問が10秒以内になるとは確認していません。[測定方法と対象](https://github.com/AtsushiHosaka/pals/blob/5e88f2eab52f422fe664b47aa17754729f48c72a/docs/aws-recipe-reuse-latency-2026-10-31.md)を参照してください。

AuroraにはDraft 433件、検証済みの登録Recipe 102件があります。Recipeのうち検索公開済みは20件です。カタログ9項目の件数と内容のfingerprintは更新前後で一致しました。1,100件の本番利用可能という目標は未達成です。

ASG、自動増減、大会時のxlargeへの切り替えは未配備です。1秒回答、30件を10秒以内に処理する性能、ホスト再起動からの復旧は未検証です。Aurora writerは直近の設定確認で`pending-reboot`を示しており、再起動は行っていません。復旧unitは有効ですが、運用ツールによる現リリースの再起動・再構築期限は11月3日00:08:30 JSTです。稼働サービスはこの時刻だけで停止しません。

## 図の編集とPNGの書き出し

図形・文字・接続線はdraw.ioで編集できます。PNGにも同じ図のXMLを埋め込みます。ファイル名の`private-target`は既存リンクの互換性のために維持しています。

```sh
python3 docs/diagrams/generate_architecture.py
/path/to/draw.io.app/Contents/MacOS/draw.io \
  --disable-update --export --format png --embed-diagram \
  --timeout 60 --scale 1.5 --border 20 \
  --output docs/diagrams/pals-aws-private-target.png \
  docs/diagrams/pals-aws-private-target.drawio
```

生成後はPNGの文字・接続線と、埋め込まれたXMLの一致を確認します。以前の未配備設計とASG案を出力していた生成スクリプトも、上記の配備図に合わせて更新しました。
