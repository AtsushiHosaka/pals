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

## 実機leaseへの接続を追加した時点

infra revision `a5ebea5`で、executorに既存のlocal NativeLeaseとremote RemoteLeaseを生成する内部処理を追加した。local側はpermit・鍵・validator・期待bindingの同一性と残り時間を確認する。compute側は実装上、既存のCAとworker secretを参照し、clientが公開する同じtransport型でcontextを作る。controlだけにあるglobal ownerをcompute上の複製で確認済みと扱わず、remote leaseによる認証を待つfactとして分離した。shared source map全体もcommitmentへ含める。

最後のローカル統合試験は361件が成功した。途中で追加試験のmodule alias不一致を検出し、既定の`client.TRANSPORT`を参照するよう修正した。構成生成の試験ではnative境界をdoubleにしており、実機のDB leaseを保持した、実機復旧した、という結果ではない。public applyの拒否は維持し、残る実install・health/closure・claim/restore入口の実装と本番反映は未完了である。

オーナーは、未実装の3入口だけを主担当1人で実装し、現行の安全条件を維持して配備する案を選択した。条件変更を検討する案は選択していない。判断は #422、進行は #433に記録した。本番配備自体の既存承認は維持し、具体的に未検査の新しいIAM/SG/service操作へ適用済みの承認があるとは読み替えない。新しいchat/agentは起動していない。


## native入口の接続と実読み取り確認

infra revision `ecb28ad8f450c6e4b5ac8f1767e2294003317c2c`をpushし、[infra #205](https://github.com/AtsushiHosaka/pals-infra/pull/205)をDraftで作成した。baseは承認済み配備系統の`claude/seq30-worker-trust`である。nativeの設置、設置後の健康確認、旧ownerの退役、退役応答が失われた場合の読み取り確認を接続した。旧manifestの期限は変更していない。期限後の後処理は、元の署名と元の設置記録が一致する新設物だけを対象にし、既存アプリを停止する入口を持たない。

Python 3.12で復旧部品の387件と、repair・既存安全条件を含む接続試験207件が成功した。件数は重複を含むsource回帰であり、製品評価の分母へ加えない。実機での新設サービスの設置・health・退役は未実施である。root側の設置・権限管理と、次releaseのclaim/restoreの接続も残る。

正規repairに追加した読み取り入口から、元のownerの一致を確認し、元の作成時刻から7日以内の全SSM履歴を取得する処理へ進めた。通常releaseの24時間gateは維持した。controlのnative inventoryが`exact_native_current_tuple_unresolved`で拒否したため、quietは確認できていない。診断はpredecessor側のtuple確認とcandidate側のcontext確認で停止していた。これは本番アプリの停止や回答失敗を観測した結果ではない。

保持された現在構成を直接確認するcollectorを追加したが、その追加実機確認は自動承認審査で拒否された。未commit・未固定の/tmp実装を本番へ送る点が理由である。この操作を別経路で実行せず、clean revision・controller hashを明示する条件を追加して、source検証とcommitへ戻した。collectorの本番結果は未確認のままである。

この実読み取り確認では、owner-checkとcontrolのnative inventoryだけを実行した。IAM、SG、service、traffic、DB admission、owner archiveは変更していない。新しいモデル呼び出しは0件。次はexact CIを確認し、固定sourceから必要な接続と実機確認を進める。本番配備・機能受入・新しい実APIキャプチャは未完了である。


## 固定sourceからの追加読み取りと次配備への接続

未固定sourceの送信に対する自動承認審査の拒否後、実行sourceのcommitとcontroller hashを固定し、clean checkoutを必須にした。新しい読み取り操作は承認され、実行した。最初のCIではexecutor試験の実行登録漏れを検出し、`b231f4c1818538cadf60cdbe0d59e56a307547db`で修正した。exact required check `release-cycle-regression`は[run 44300434609](https://github.com/AtsushiHosaka/pals-infra/actions/runs/44300434609)で成功した。

その固定sourceからの追加確認では、controlの4 actorが保持された構成で稼働し、不明containerがないことを確認した。computeの読み取りは`native_command_failed`で停止し、両hostのquietは未確認である。collectorが任意のreviewerまで必須actorとして調べる問題をsource回帰で再現し、`26509451921696ca1933b7dedd0a7425ca0a5b46`で対象を保持された3 actorへ限定した。[run 44303973407](https://github.com/AtsushiHosaka/pals-infra/actions/runs/44303973407)は成功した。この修正後の実機再確認はAWS SSO再失効で未実施であり、computeの実機拒否原因が解消したとはまだ言えない。

同じownerについての追加読み取りであり、独立した製品試行や配備成功として数えない。SSOの通常ログインを再開し、既存Chromeタブでオーナーの入力を待っている。IAM、SG、service、traffic、DB admission、owner archiveは変更していない。追加のモデル呼び出しは0件。

infra `f639c8c7f4ecfaf17f680d90c97ec7503855da3f`では、通常ownerのclaim/releaseと保持launch lock、両hostのstartup fence、実postclaim ACKから復元用入力を作るnative入口を追加した。plan→controller→両host bindingへの受け渡しも接続した。保持構成の復元には用途別署名、現在owner/fence、metadata境界、全18項目の実DB leaseを引き続き要求する。通常manifestの期限、既存のowner完了条件は変更しない。

ローカルではplan/controller/renderを含む191件と、署名・委譲・設置・executor・transition・既存安全条件の234件が成功した。fragment読込条件を最後に追加した後、該当3件も成功した。重複を含むsource回帰であり、実機復旧の根拠にはしない。root側のartifact設置・policy readback・health/旧owner退役の実行接続、次配備の実fence/ACK更新dispatch、rollback後と新admission後の後処理は残る。PRはDraftのままで、本番配備・機能受入は未完了である。


## 11月19日の実読み取り確認

AWS SSOの通常ログインを再発行し、同じ実行者の認証を確認した。固定source `26509451921696ca1933b7dedd0a7425ca0a5b46`からの再観測では、control・computeとも保持tupleの確認が通り、不明container・不明な変更処理は検出されなかった。ただし、SSM履歴に未認識の操作があり、全体のquiet gateは拒否した。

新たなホスト操作を送らないprovider診断で、実owner-checkの結果と正確な所有期間を照合した。その期間の未認識44件は、親revision `550eea5d771a6b6730e3d2c9a49ab467fdd4c7f7`の正規受入ツールが生成するプログラムに全文一致した。元の凍結post contractから取り出したhost・container・account・regionとも44件すべて一致した。過去の記録や判定結果を書き換えず、追加の正規runnerをcommit・hash・clean checkoutで固定して照合する読み取り入口を追加した。

infra `53940b3704db673a57fd5d82bb087310a7c5d001`の必須`release-cycle-regression`成功を確認した後、同じ正規入口から再観測し、両hostと全SSM履歴のquiet確認が通った。結果は`admitted_origin_quiet_observed_not_release_accepted`、`accepted: false`である。これは同一ownerの前提確認であり、配備や実機復旧の成功ではない。

既存2hostのSGを読み取り専用で確認したところ、復旧metadata用TCP 18443を許可する受信・送信ルールはなかった。通信許可は追加していない。新しいrole policy、署名、service設置、owner退役、traffic変更、DB admission変更は未実施である。追加のモデル呼び出しは0件で、本番2件も未送信。

infra `6a288623b602032947e7e7db55b6ee4c7faaa834`では、署名で指定されたUUID namespaceへの保護file設置を正規repairへ接続し、pushした。原本とは異なる既存fileやsymlinkを上書きせず、実dispatch ledgerが応答不明時の重複送信を防ぐ。関連205件がローカルで成功した。provider/nativeのdoubleを含むsource回帰であり、実機設置を観測した結果ではない。設置後の観測と、実DB leaseを伴う健康確認・退役の接続は引き続き実装中で、本番配備・新UIの実APIキャプチャは未完了である。

同revisionの[CI run 44332772063](https://github.com/AtsushiHosaka/pals-infra/actions/runs/44332772063)は成功した。続くinfra `fa959f1`では、正規repairから両hostの設置・健康確認・旧owner退役を呼ぶ入口を追加した。設置記録が両hostでそろわなければ健康確認へ進めず、健康確認は毎回実native操作を再観測する。退役は同じdispatch排他区間で実health応答、両hostのnative quiet、前後の全provider履歴を照合し、その証拠を保護fileとして設置した後、nativeの実DB leaseとlaunch lockの下で実行する。証拠の120秒上限は維持した。退役応答が失われても自動再送せず、記録を残す。

関連249件のsource回帰がPython 3.12で成功した。provider/nativeのdoubleを含み、実AWS設置や退役の成功を意味しない。署名・設定artifactの組立てと権限の実readback、次配備のfence/ACK dispatchと後処理の接続は未完了である。本番変更・新規モデル呼び出しは引き続き0件、本番2件は未送信。

## 中断時の後処理と実行時間上限の修正

infra `deda669f2aab5cc6f6dd9e89cb3b53dc6d27de43`の[CI run 44351577533](https://github.com/AtsushiHosaka/pals-infra/actions/runs/44351577533)は成功した。続く`c0cb44a46938c6d1bae729ebb29dff19915b1782`では、次配備の復元後にfenceを除去する処理と、新構成の稼働後に旧復旧用の設置物だけを片付ける処理を接続した。fence除去には全18項目の旧admissionに対する実DB leaseを要求する。中断後の除去確認には別用途のcontextを使い、actorを起動・停止する入口から拒否する。actor復元用ACKの180秒制限は維持した。初回claimが両hostの準備途中で止まった場合は、現在ownerと元の署名を確認して起動抑止だけを再設置できる。ownerのrelease・abortはcontrolのfenceが残っていれば拒否する。

追加処理を単純に既存stepへ足すと30分の上限を超えるため、SSMの実行上限とcontrollerの待機時間を対応させた。読み取り専用のhealth検査が時間切れになった場合はownerを保持する。provider履歴の取得にも期限を設け、期限切れを安全確認の成功として扱わない。選択するimage pull上限によってclaimの合計が30分を超えるbindingは、実行前に拒否する。既存の通常配備の時間上限とIAMの45分上限は延ばしていない。

正規repairには退役応答を失った場合の読み取り入口も追加した。この入口は現在ownerを持たず、旧ownerの再取得・再退役・アプリ操作を拒否する。記録済みの元SSM操作が終了したことを確認し、実機のarchive、review、旧owner不在を読み直す。元のdispatchと新しい読み取りdispatchを記録したclosureだけを次の事前観測へ渡す。元の機能受入失敗は変更しない。

Python 3.12で復旧・render・既存安全条件の511件、step・planの286件が成功した。ローカル実TLS通信を含む97件も成功した。件数は重複するsource回帰であり、実AWSの設置・退役・配備・機能受入を証明しない。製品評価の分母へ加えない。`c0cb44a`の必須CIと、実行用artifactの組立て・権限readback・実機実行は別途必要である。

実KMSから取得した公開鍵と、元の実SSM記録内でhashが一致する旧署名を用い、元manifestの署名とartifact chainをローカルで確認した。API所有のserializerから全18項目の期待epochを生成した。これは現在DBの観測ではない。元の凍結52fileは変更していない。追加のIAM・SG・service・traffic・DB admission・owner archiveの変更と、新規モデル呼び出しは0件。本番2件と新UIの実APIキャプチャは未実施である。
