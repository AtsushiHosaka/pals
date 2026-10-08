# 2026年10月8日 PALS停止と自動復旧

`palschat.site` と `api.palschat.site/health` は10:00 JSTの確認でCloudflareの502を返した。DNSとTLSは正常で、Tunnelは稼働していた。MiniのWeb・API・worker・公開edgeが停止し、Tunnelの接続先13000/18000はconnection refusedだった。DBと機械認証brokerは稼働していた。

## 停止原因

[Actions 37646859592](https://github.com/AtsushiHosaka/pals/actions/runs/37646859592) の親 `8d4f5af085c9ce05239f2c658e471da07ecd29b0` の通常更新は、00:49:34〜38 JSTにedgeと3サービスを停止した。DBへの署名付きadmissionはsequence12まで適用済みだったが、ホスト処理は `OSError` で失敗し、`apply_result_received` のpendingを残した。元のログは例外の種類までしか記録していない。

同じ実機で、同じDB接続処理だけを使った隔離名の一時プロキシを起動・削除すると、1回目は成功し、直後の2回目のbindが `OSError: errno 48, Address already in use` になった。本番サービスやDBの行は変更していない。旧処理は `SO_REUSEADDR` なしで15432へbindしており、削除直後に残るTCP状態を使用中のポートとして拒否していた。DB適用後の再観測と例外時の復旧が同じ処理を呼ぶため、両方が停止する。独立した再試行監視もなかった。

10:11 JSTに既存の署名付き復旧処理でsequence12を独立再観測し、candidateへの復帰を完了した。旧データ照合、同じDB/volume、3サービスのimageとsource、匿名401、公開200、pending解除とcurrentの更新を確認した。GitHubの失敗runを成功と書き換えてはいない。

## 修正と常駐監視

Infraにポート再利用修正と `host/macmini-recovery` を追加した。`SO_REUSEADDR` と最大10秒の待機を使い、稼働中の別listenerは引き続き拒否する。修正後の実プロキシ連続起動・削除は3回とも成功した。

固定LaunchAgent `site.pals.auto-recovery` をMiniに設置し、15秒間隔で自然実行する。既存のdeploy/lifecycle lockを取得できない場合は介入しない。pending更新、公開edge単独停止、通常サービス停止をそれぞれ検証して復旧する。署名とDB状態が不明な場合は公開を再開しない。失敗時には間隔を延ばして再試行し、正常時はログを繰り返し出さない。

最初の実機障害注入では、監視から起動する旧PythonがmacOSのDocumentsFolder許可待ちになった。TCCのPID照合で確認し、試験で停止したedgeを一度手動で戻した。この試験を自動復旧成功とは扱わない。

既存Python 3.12と既存依存、6用途のDB URLファイル、host markerをMiniの専用保護領域へ複製した。元ファイルは保持し、秘密値・host identityのbytes・署名とDB identityを維持した。DB資格情報の再発行やIAM変更、ネットワーク公開範囲の変更は行っていない。常駐復旧と通常更新のauthorityはDocuments外の同じruntimeを使う。

Documents依存解消後、公開edgeを停止する自然試験では45.69秒で自動復旧した。同じedge CID、DB identityとsequence12の同じadmissionを保持し、root 200を確認した。アプリが健全なedge単独停止をより早く戻す経路を追加した後の再試験は19.41秒で復旧し、同じ3条件と200を維持した。単体・境界テストはauthority/controller 66件、監視・設置13件が成功した。実deploy/lifecycle lock保持中の監視skip、6用途のDB URLとhost markerのbyte一致、自然巡回後の公開・内部200とworker readyも確認した。

現在の対象はMac miniで動くAPI・Web・worker・公開edgeと、途中で止まった署名付き更新。Miniの電源・回線、Docker engine、DB自体の停止、OS未ログインは自動修復の対象外。保守時は保護領域の `auto-recovery/disabled.json` で復旧を停止する。

コードと検証範囲、設置・保守・状態ファイルは [Infraの運用手順](../pals-infra/host/macmini-recovery/README.md) に記載した。秘密ファイル、runtime、private log、生成された検証結果は親・InfraのGitへ含めない。
