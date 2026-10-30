# PALSのAWS移行先の構成図

この図は2026年10月30日の移行先の設計を表します。AWSへの配備結果ではありません。Terraform管理のVPCを用意し、既存データ・認証を維持しながらWeb・APIと計算ノードをprivate subnetへ置く案です。現状のAWS default VPCをPALS用として再利用する図ではありません。

![PALSのAWS移行先の構成図](pals-aws-private-target.png)

[編集可能なdraw.ioファイル](pals-aws-private-target.drawio)には、すべての図形・文字・接続線を保存しています。PNGにもdraw.ioのXMLを埋め込んでいるため、draw.ioで開いて編集できます。

## 図の範囲

公開ALBは2つのAZのpublic subnetに配置し、EC2にはpublic IPv4を付けません。外向き通信は初期1台のNAT Gatewayを経由し、S3宛の通信だけをGateway Endpointへ送ります。DB subnetにはインターネット向けdefault routeを設けません。

図中のAZ-AとAZ-Bは配置の役割を示します。図のCIDRはTerraformのdefault `vpc_cidr=10.42.0.0/16`に基づく設計値です。public、private control、private compute、isolated DBのsubnetをそれぞれ2つのAZに分けています。実際のAZ名・CIDR・resource IDはplanと配備後の読み戻しで確認します。DB subnetが2つあることは、Aurora writerやreaderが2台あるという意味ではありません。Web・API、NAT、Aurora writerは初期各1台であり、全層の高可用性を示す図ではありません。

接続線は通信の開始側から宛先へ向けています。制御ホストからverifierへはmTLSのTCP 18117、計算workerから制御ホストへはHTTPS 443を使う設計です。計算workerからAuroraへの直接接続は許可しません。描画の実装・実行・配備を示すinline diagram機能の記号は含めていません。

DNSの管理元は決め打ちしていません。現在のDNS管理元を確認し、AWS側の受け入れ確認後に`palschat.site`と`api.palschat.site`の向き先をALBへ変更します。Route 53へのNS移管を完了したという意味ではありません。

## 描画の再現

XMLは標準ライブラリだけを使う次のプログラムで生成できます。draw.ioで手動編集した場合、再生成すると手動変更を置き換えるため、先にプログラムへ反映します。

```sh
python3 docs/diagrams/generate_architecture.py
```

PNGは、公式のdraw.io Desktop 32.6.1を実行して書き出しました。macOSのコード署名とnotarizationを確認し、作業用の一時ディレクトリから実行しました。アプリのsystem-wideなインストールは行っていません。

```sh
/path/to/draw.io.app/Contents/MacOS/draw.io \
  --disable-update --export --format png --embed-diagram \
  --timeout 60 --scale 1.5 --border 20 \
  --output docs/diagrams/pals-aws-private-target.png \
  docs/diagrams/pals-aws-private-target.drawio
```

実際のPNGを目視し、XMLの埋め込みと画像寸法を確認しました。配備完了時にはAWSのsubnet、route、security group、各サービスの設定を読み戻し、設計図との相違を更新する必要があります。

参照元は[全体設計](../aws-low-latency-architecture-2026-10-30.md)、[draw.io Desktop公式リリース](https://github.com/jgraph/drawio-desktop/releases/tag/v32.6.1)、[draw.io Desktopの説明](https://github.com/jgraph/drawio/wiki/Desktop-App)です。
