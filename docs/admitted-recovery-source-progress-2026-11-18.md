# 承認済み構成の復旧処理の実装記録

対象は[#433](https://github.com/AtsushiHosaka/pals/issues/433)、配備待ちのUIは[#425](https://github.com/AtsushiHosaka/pals/issues/425)。担当はcodex://threads/01a1ebe7-a4ee-78c0-ab22-a16cfcccc3d2。状態は実装中で、本番配備・復旧・機能受入は未完了である。

旧manifestの有効期限を延長せず、現在DBが承認する同じ構成だけを新しい用途別署名で復旧する。旧manifest、署名、失敗記録は保持する。14:40失効の旧IAM再許可案は撤回済みで、適用していない。新しい署名、権限、通信口の本番適用は、具体的な入力と検証を揃えてから承認を求める。

## sourceと検証の範囲

| source | 確認した範囲 | 残る範囲 |
|---|---|---|
| [API #123](https://github.com/AtsushiHosaka/pals-api/pull/123) | 全18項目とsequenceのcanonical hash、旧API実imageへのread-only注入で公開vector一致 | 最新DBと実行権限はserializerの責務外 |
| [infra #190](https://github.com/AtsushiHosaka/pals-infra/pull/190) | 用途別署名文書の純粋validator、実暗号の負例 | 本番署名・実行・復旧は未実施 |
| [infra #191](https://github.com/AtsushiHosaka/pals-infra/pull/191) | 別名のmetadata policy生成。4read操作・3resource、account/region一致、発行時刻から最大24時間、完全一致での削除対象確認。4単体テストと独立レビュー成功 | IAM適用・role/name照合・削除確認・本番bootは未実施。通常release grantの45分制限は不変 |
| [infra #192](https://github.com/AtsushiHosaka/pals-infra/pull/192) | 旧INPUT先頭jumpを保持する専用overlayの生成と完全一致確認。5単体テストと独立レビュー成功 | listener、SG、systemd、本番の既存firewall全体は未検証 |
| [infra #193](https://github.com/AtsushiHosaka/pals-infra/pull/193) | 専用signerと旧API image上のfull18 observer。返答は観測事実のみ | 長時間DB leaseと実行処理への接続は別工程 |
| [infra #194](https://github.com/AtsushiHosaka/pals-infra/pull/194) | 既存launch lock内の永続startup fence。実FSと別processのflock試験 | 全claim/boot/restore入口への接続、既dispatchの調停は別工程 |

単体テスト数を配備成功率や証明精度の分母には足さない。各PRのexact CIは配備前に別途確認する。source側の成功を本番復旧の合格へ読み替えない。

## 分離したLinux環境での実iptables確認

infra #192のboundary moduleを読み取り専用で注入し、実Linux kernelの専用network namespaceで1束の確認を行った。テスト用のRFC1918アドレスを使い、外部通信は`--network none`で遮断した。ホストnetworkやDocker socketは共有せず、公開portも作らなかった。権限は全capabilityを落としたうえで、専用namespaceの設定に必要な`NET_ADMIN`だけを付けた。

実ルールを適用した後、指定peerからTCP 18443へ接続でき、別peerとloopback sourceからはtimeoutした。対象外の18444への通信は維持された。kernelが出力するルールはsourceの完全一致検査を通り、foreign chainからの追加参照を作ると拒否した。テストが使った旧base chainは最小の分離fixtureであり、本番の全ルールを再現したものではない。

実行スクリプトとtool imageのDockerfileはinfra #192の`tests/kernel/`へ保存する。ベースは既存の検証image `sha256:e3ed6892011013fd889b6be8fafa3e87e29624bf4c054175a828e1828fffcb50`。iptablesとiproute2を追加した試験専用imageを使い、終了後に専用containerとimageを削除した。既存サービス・既存image・本番設定・providerは変更していない。

この結果が示すのはIPv4 kernelの限定した通信境界だけである。TLSは別のtransport試験、本番SGやIPv6 socket、service identity、署名、DB lease、全停止復旧、OS rebootは別に検証する。初回と保存用スクリプトの整理後確認は同じ境界の再確認であり、独立した2試行として数えない。有料モデル呼出しは0件で、費用とlatencyの測定値はない。

## 次の完了条件

専用DB接続上でのTLS・principal・full18 lease、両hostのfence、認証付きの観測結果伝達、保持されたIDだけを起動するexecutorを接続する。新種別のassembly/install/health/closure receiptと、次releaseのclaim/admit/restore consumerを通す。部分失敗、失応答、期限切れ、接続喪失、foreign ownerを検査し、exact CIと独立レビューを確認する。

その後に新しい本番操作の具体案を提示する。承認後も、#425の配備、正規の機能受入、実API画面の撮影、保存・reload・history、後処理をそれぞれ記録し、完了していない段階を残す。

## 18:01 JST時点の接続確認

既存のunits、client、preclaim evidence、metadata、delegation、executorを同じinfra作業ブランチへ通常mergeした。停止していたbroker/workerの未commit成果は元の作業場所に残し、統合作業側へ引き継いだ。接続修正のinfra revisionは`0c32318`。他チャットやagentは再開していない。executorの起動引数、reconcilerの許可stage名、metadataへのphaseとbroker job参照の受け渡しを修正した。metadataの実host・config・契約・旧manifestが期待値と異なる場合も拒否する。

ローカルPython 3.12.13で統合前の既存347件、その後の接続修正を含む352件が成功した。canonical transport moduleの読み込み順を追加修正した後は、影響するexecutorの27件と、統合353件が成功した。接続回帰5件は元のexecutor source `4efce44128f280219e96fbb8c984fa51df9fc04c`で失敗することも確認した。これはsource間の呼び出し、実TLSとpipeの境界、保護ファイルの試験であり、本番の復旧・配備・起動・機能受入の合格ではない。最初のsandbox内実行はローカルsocket作成と/tmp親directoryの保護条件で失敗した。ローカル通信を許可し、保護されたfixture親を指定して再確認した。単体試験の件数は製品評価の分母へ足さない。

凍結済みの正規`release-repair.py` SHA256 `94549f8ca3aec8c43fc0d85e62f898111526bf4b11f9c1fe4b8ff75504257ffe`の読み取り処理で、旧ownerの記録の一致確認後、provider/nativeのquiet検査が`current_bounded_canonical_ownership_window_required`で拒否された。SSO接続後の現在のowner確認は通ったが、取得から24時間以内という配備履歴を全件確認する条件を満たさない。2回目は同じ試行の拒否理由の観測であり、独立した評価には数えない。quiet、本番health、旧owner解放、今回の配備は未確認である。

この確認でIAM・SG・service・traffic・DB admission・owner archiveは変更していない。読み取り用のowner-check SSMは実行した。14:40失効の旧一時権限は再適用していない。新しいモデル呼び出しは0件で、過去の呼び出し費用を増やしていない。

旧構成の復旧処理を省いてownerだけを退役させる案は、次の配備が失敗した際の旧構成への復帰も失うため採用しない。public executorのapplyは引き続き拒否する。残る実装は、具体的なauthorityの接続、実install/health/closure receiptの生成と消費、次releaseのclaim/restore入口へのfence接続である。部品試験の成功だけでこの状態を解除しない。
