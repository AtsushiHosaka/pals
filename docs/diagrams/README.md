# PALSのAWS構成図

2026年11月1日13:46 JSTに公開を再開したseq7の構成を示します。AWS設定の読み戻し記録と、全7コンテナ・サービス間TLS・Auroraの34段階の状態確認・カタログ保持・復旧unitの確認結果に基づく配備図です。ログインなしの証明生成と応答時間は、公開後の別の検証で確認します。構成変更を行う際は、実設定を再確認して更新します。

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

seq7のmanifestは`c9aa33f03336cea5696491c124707d481711c8388e08bb07291ce72b81417860`です。新構成のcontrol確認はSSM `20d0b37c-b3e6-4e37-91ac-cca803253e41`、compute確認は`df56be45-2806-44ad-999a-61968a6d4852`で成功しました。13:46:23 JSTにALBのlistenerとruleを既存の状態へ戻し、公開を再開しました。

LeanのDraft・Sketch・Prove・RepairはGPT-6.1 Terraの推論量medium、説明・経路判定・審査はLunaのlowに固定しました。自動的なモデル切り替えは追加していません。Webとverifierのイメージ・toolchainはseq6から変更していません。配備用の一時KMS検証・RDS参照ポリシーは削除し、存在しないことを読み戻しました。

AuroraにはDraft 433件、検証済みの登録Recipe 102件があります。Recipeのうち検索公開済みは20件です。カタログ9項目の件数と内容のfingerprintは更新前後で一致しました。1,100件の本番利用可能という目標は未達成です。

ASG、自動増減、大会時のxlargeへの切り替えは未配備です。1秒回答、30件を10秒以内に処理する性能、ホスト再起動からの復旧は未検証です。Aurora writerは直近の設定確認で`pending-reboot`を示しており、再起動は行っていません。復旧unitは有効ですが、運用ツールによる現リリースの再起動・再構築期限は11月2日12:32:25 JSTです。稼働サービスはこの時刻だけで停止しません。

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
