# PALSのAWS構成図

2026年11月1日21:53 JSTに公開を再開したseq9の構成を示します。全7コンテナ、サービス間TLS、Auroraの35段階の状態確認、カタログ保持、復旧unitを確認した配備図です。ネットワーク構成とEC2の配置はseq7から変えていません。ログインなしの証明生成は公開後に確認しました。選択モデルの利用量精算は引き続き確認中です。構成変更時には実設定を再確認して更新します。

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

seq9のmanifestは`a3340a717db963f64e42de8ddea3e10483f32712d4e4b9d2702f0866c95b774c`です。controlの確認はSSM `f60624fd-72a8-41a2-99d0-1665ad329639`、computeの確認は`10f341f2-1f31-4108-b98e-6944b4197677`で成功しました。21:53:13 JSTに元のALB listenerとruleへ戻し、公開を再開しました。

チャットからGPT-6.1 Terra・GPT-6.1 Sol・GPT-6 Lunaと、推論量low・medium・highを選べます。既定はTerraのmediumです。選択した設定は各依頼のDraft・Sketch・Prove・Repairに固定されます。その他の役割は既存のモデル設定を維持し、自動的なモデル切り替えは行いません。API・worker・Webを更新し、verifierのイメージとtoolchainは保持しました。配備用の一時KMS検証・RDS参照ポリシーは削除し、不在を確認しました。

| 配備元 | commit |
| --- | --- |
| 親リポジトリ | `6dca76eb6de6f3de41c0a98883f135c1bb334c82` |
| API | `adda2098ff3c8ee73d07214e3256e6e27b11e987` |
| worker | `d58b60dee6ac246db26f62891a1939083b17236b` |
| infra | `92330d6cdf204379b5e4fd652c7737fafc90bca3` |
| Web | `a74b57b130ac0de6c7bf793ca095e81b54c4344f` |

controlのruntime configは`a327705753bfdd9b35ede9bfaf2b850d963535cf5e27f4ef3cb9f0785a370879`、computeは`300096ec3138b33caec127f0c0e8709a18fc600c655c2c2828a1d1ab9fd40699`です。両ホストとカタログの確認結果を集約した記録のSHA-256は`2b1c81fcd17bfbdfcf15fa977b91cfd5513defb676329ae5f5eaa9c47b65879b`です。

ログインなしでGPT-6.1 Sol・highを選んだ実リクエストは、0を含む自然数冪の連続性についてLean検証済みの回答を返しました。サーバーの完了までは135.622958秒、公開APIのポーリングで完了を確認するまでは137.447秒でした。Recipeの再利用ではなく、新規のproof job `af3b53ca-6e1e-420b-bfe7-ed173859d054`で処理しました。検証済みLeanソースのSHA-256は`1d6c321c9100aeece073cfaddb66055e399efee42b2146040240a562b85d7ceb`です。10秒以内という目標は未達成です。

AuroraにはDraft 433件、検証済みの登録Recipe 102件があります。Recipeのうち検索公開済みは20件です。カタログ9項目の件数と内容のfingerprintは更新前後で一致しました。1,100件の本番利用可能という目標は未達成です。

ASG、自動増減、大会時のxlargeへの切り替えは未配備です。1秒回答、30件を10秒以内に処理する性能、ホスト再起動からの復旧は未検証です。Aurora writerは直近の設定確認で`pending-reboot`を示しており、再起動は行っていません。復旧unitは有効ですが、運用ツールによる現リリースの再起動・再構築期限は11月2日21:39:18 JSTです。稼働サービスはこの時刻だけで停止しません。

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
