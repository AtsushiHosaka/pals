# PALSのAWS構成図

2026年11月2日03:02:32 JSTに公開を再開したseq12の構成を示します。全7コンテナ、サービス間TLS、Auroraの35項目、カタログ9項目の保持、復旧unitを実機で確認した配備図です。ネットワークとEC2の配置はseq11から変えていません。公開WebとAPI healthのHTTP 200まで確認済みで、言い換えた質問への公開画面での証明生成は未検証です。

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

seq12のmanifestは`6f84b0967c9ef4cd12fb6658764599c2d5ccd2c7582daa03b67376df358acf3f`です。controlの確認はSSM `19dffd6b-5118-4271-87f6-dcf6c9a86e5e`、computeは`428d2735-6a65-40c4-ad25-947f2e402b37`で成功しました。03:02:32 JSTに元のALB listenerとruleへ戻しました。時刻はALB API応答のHTTP Dateに基づきます。配備用の一時KMS検証・RDS参照ポリシーは削除し、不在を確認しました。

チャットからGPT-6.1 Terra・GPT-6.1 Sol・GPT-6 Lunaと、推論量low・medium・highを選べます。既定はTerraのmediumです。自動的なモデル切り替えは行いません。seq12では、数学的な言い換えに対して現在の20候補を調べ、独立した2つのLuna・low呼び出しで質問の条件と保存回答の対応を並列に確認します。両方が同じ候補を認めた場合だけ再利用します。Web・verifierのイメージとtoolchainは保持しています。

| 配備元 | commit |
| --- | --- |
| 親リポジトリ | `e65906a01ff182e7e40e5aa7a98b8bdf7ae09751` |
| API | `7cde9674b0ff61d92116280f303638351362729e` |
| worker | `7c000dbb84288e01391e72bde796b53bfdd51608` |
| infra | `cf212c9134e4c4bf7a6747d8628f61bd98dd6027` |
| Web | `a74b57b130ac0de6c7bf793ca095e81b54c4344f` |

controlのruntime configは`efc821b71bcd3d822599a46132eacc47d1a4218c08cc37d33fd094d1b7813d32`、computeは`4b210b91c16011005faf6990a9f3a29ae2c8e6d93c62755c67f7749229eb88cc`です。両ホストとカタログを集約した確認記録のSHA-256は`6ced21734d5edbdda58b421668fb38b7a158689bc8199876965e2ea2758320da`です。

固定環境から実APIを呼び出した32問の測定では、同値・変数名変更13問中11問を受理し、条件などが異なる19問をすべて拒否しました。受理した分類時間は6.082〜9.883秒で、キュー待ち・保存・ブラウザー表示を含みません。cached入力tokenは0でした。右極限とπの2件は同値でも再利用できず、保存回答を直すrevision 2は未登録です。[言い換えの測定結果と限界](../aws-recipe-semantic-benchmark-2026-11-02.md)に記録しています。

以前のseq11では、0を含む自然数冪の同じ入力をログインなしで3回送信し、4.775秒・4.664秒・4.830秒で回答とLeanソースを表示しました。モデル呼び出し・新規証明jobは0件でした。これは独立審査済みの完全な日本語入力2文のうち1文を公開測定した記録です。今回の言い換え経路の公開応答時間とは区別します。[過去の測定方法と対象](../aws-recipe-reuse-latency-2026-10-31.md)を参照してください。

AuroraにはDraft 433件、検証済みの登録Recipe 102件があります。Recipeのうち検索公開済みは20件です。カタログ9項目の件数と内容のfingerprintは更新前後で一致しました。1,100件の本番利用可能という目標は未達成です。

ASG、自動増減、大会時のxlargeへの切り替えは未配備です。1秒回答、30件を10秒以内に処理する性能、ホスト再起動からの復旧は未検証です。Aurora writerは直近の設定確認で`pending-reboot`を示しており、再起動は行っていません。復旧unitは有効ですが、現リリースの署名済みmanifestの有効期限は11月3日02:29:04 JSTです。期限後の運用操作には有効なリリースの準備が必要です。稼働サービスはこの時刻だけで停止しません。

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
