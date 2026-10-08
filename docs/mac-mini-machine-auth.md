# Miniの常時運転を人のSSOから切り離す

更新日: 2026年10月5日。対象はPALSの運用者。本人の設置許可に基づき、機械認証の設置・自然更新・実Actionsからの配備を検証した。

## SSOの期限延長では常時運転にならない

導入前のMiniは、人の `pals-prod-member` SSOから用途別のSTS sessionを取得していた。既存brokerは1時間のsessionを30分ごとに更新するが、元のSSOが失効すると更新できない。10月4日と5日に失効し、workerが停止した。5日の本人再ログイン後、同じworkerのCID・imageでRunningとreadyへ復帰した。復旧時にはDB更新や新しい権限の付与を行っていない。

人の再ログインを運転条件にしたまま、自動デプロイを完成と判定しない。[配備状況](mac-mini-actions-deployment.md)に実行結果を記録する。

## Mini専用の証明書から短期sessionを取得する

AWS IAM Roles Anywhereに専用のCAを登録し、Miniが証明書と秘密鍵で短期sessionを取得する。AWS公式helperの `credential-process` を利用する。[公式helper](https://docs.aws.amazon.com/rolesanywhere/latest/userguide/credential-helper.html)

対象はPALS account `828786775577`、region `ap-northeast-1`。新しいtrust anchorの名前を `pals-macmini-machine` とし、profileは次の2つに分ける。新しいIAM userやaccess key、AWS Private CAは作成しない。

| Profile | 認証できる既存role |
| --- | --- |
| `pals-macmini-runtime` | `pals-mini-prod-api`、`pals-mini-prod-worker`、`pals-mini-prod-backup-writer` |
| `pals-macmini-release-signer` | `pals-mini-prod-release-signer` |

4roleはすべて `/pals-mini-prod/` 配下。ARN・RoleId・既存permissions・boundaryを維持する。専用anchor ARN、account、CAのissuer CN、用途別leaf CNを各trust文で要求する。`AssumeRole` には既存の固定RoleSessionNameを要求し、`TagSession` と `SetSourceIdentity` は別の文に分ける。後者には `CN=pals-macmini-<用途>` の固定SourceIdentityも要求する。AWS公式例もセッション名の条件を `AssumeRole` に限定している。[AWS構成例](https://docs.aws.amazon.com/eks/latest/userguide/hybrid-nodes-creds.html)、[SourceIdentityの規則](https://docs.aws.amazon.com/rolesanywhere/latest/userguide/trust-model.html#source-identity-rules)

既存のSSO statementを保持し、同時変更を検出したら適用を止める。両profileで `acceptRoleSessionName=true` とし、毎回session名を明示する。

同accountの全roleを読み取り監査する。他roleにanchor未限定のRoles Anywhere trustがあれば、4用途限定とは判断せず、設置を止める。[accountの信頼境界](https://docs.aws.amazon.com/rolesanywhere/latest/userguide/introduction.html)

初回anchor作成時、AWSが `AWSServiceRoleForRolesAnywhere` を自動作成した。専用の予約path・実RoleId・trust・AWS管理policyを照合し、このサービス用roleだけを監査上の例外にする。全11roleを監査し、2profileの対象は既存4roleだけであることを確認した。[AWSサービス用role](https://docs.aws.amazon.com/rolesanywhere/latest/userguide/using-service-linked-roles.html)

設置前の読み取り監査では、既存anchorとprofileは各0件。account全10roleにRoles Anywhere trustやwildcardのAllow principalはなかった。既存4roleはすべて1時間上限で、attached policy・permissions boundaryはない。APIには、SQS用policyに加えて既存CIMDのCognito読み取り検査policyがある。この既存policyも保持する。

[読み取り専用の計画コード](https://github.com/AtsushiHosaka/pals-infra/commit/e5c9bcc77278879bc6e953305e8df1b378c8a284)はpush済み。既存RoleId、roleの1時間上限、runtime profileの3600秒・signerの900秒、用途分離、既存trustの保全、同時変更の拒否を検査する。21テストと独立レビューが成功した。AWS変更や鍵作成の機能は持たない。CA・profile設定のhashは変更検出のための値であり、実issuer・CN属性の対応や全account監査、実認証を証明するものではない。

## 秘密鍵はMiniの専用領域に保管する

保管先は `/Users/hosakaatsushi/pals-mini-deploy/machine-auth`。directoryは所有UID 501・mode `0700`、秘密鍵は `0600`。Git、Actions出力、ログ、コンテナへ秘密鍵を渡さない。既存の用途別短期sessionを渡す方式と、workerの独立role policyを維持する。signerはnative配備処理だけが900秒以内のsessionをメモリで扱う。

設置中の検証では、専用CAと4用途のleafをこの領域に生成した。CAの期限は2036年10月5日、leafは2026年11月4日。実OpenSSLによるpair・chain・権限の検査と、更新失敗時の旧世代保持を含む15テストが通過した。常駐プロセスによる自然更新と稼働サービスへの切り替えは、以下の実機検証で確認した。

CAとleafは、公式helperが扱える名前付きEC曲線で生成した。4roleの分割trustは適用と読み戻しを完了し、旧SSOと権限を保持した。全4用途で、SSO設定・cacheを利用しない実AWS認証を2回確認した。予定のRoleIdとsession名で、runtimeは1時間、signerは900秒のsessionを取得した。worker証明書で別roleを使う要求、session名違い、runtimeとsignerのprofile取り違えも、実AWSが拒否した。workerの新leafは実認証後に有効世代へ切り替わり、一時的な更新失敗では、有効な旧leafを再認証して保持した。

LaunchAgentからの全4用途の認証も成功した。ただし、Documents配下の旧session保存先への書き込みはmacOSのアクセス制御で拒否された。新しい保存先を `/Users/hosakaatsushi/pals-mini-deploy/runtime-sessions` に移し、用途別ディレクトリとコンテナのread-only mountを保つ。旧brokerは候補サービスとDBの独立照合まで旧保存先を更新し、照合後に正常終了した。稼働コンテナは旧保存先を参照していない。新brokerは固定の `~/Library/LaunchAgents/site.pals.machine-runtime-broker.plist` に設置し、永続pathからの起動と、SIGKILL後のKeepAliveによる自動復帰を実測した。再設置で既存の資格情報・state・lock inodeを保持する試験も通過した。2026年10月5日04:05 UTC、brokerを再起動せずに30分周期の自然更新が成功した。API・worker・backup-writerの実AWS identityとreadyを確認した。

CAのCNは `pals-macmini-machine-ca`。leafは `pals-macmini-api`、`pals-macmini-worker`、`pals-macmini-backup-writer`、`pals-macmini-release-signer` の4つに分ける。CA鍵を読めるホストユーザーは4用途すべてを認証できるため、同じUID内での権限分離は保証しない。Miniホストを信頼境界とし、AWS側では4roleの権限に限定する。

## 証明書の更新と一時障害からの復帰も自動化する

CAは10年、leafは30日の有効期間とし、leafの期限7日前から更新する。broker起動時とSTS更新前にも期限を検査し、長期停止後の失効したleafも、有効なCAから再発行する。新しいkey・certificateを同じ世代directoryに作り、pair・chain・CN・期限と実AWS identityを検査してから原子的に切り替える。

CA自体の交換は事前保守として扱う。leafの自動更新だけで、登録anchorとCAも無期限に更新できるとは説明しない。CA失効前の交換を保守作業に含める。CA鍵が漏洩した場合は、専用anchorを無効化する。

brokerは期限前にSTSを更新し、一時的な失敗では再試行する。実workerのアプリ終了後に、同じコンテナが `unless-stopped` で自動復帰した。明示的な `docker stop` 後は、brokerの再起動と実AWS更新が行われても停止を維持した。試験後は同じコンテナを起動し、readyを確認した。失効したbackup-writerのleafを使う試験では、新leafの発行と実AWS認証が成功した。

## SSOを使わない実機検証後にpush連動を有効にする

設置前に既存4roleのtrust・policy・RoleIdを保存し、設置後もpermissionsが変わっていないことを確認する。SSOのprofile・cacheを利用できない実行環境で、全4用途のidentity、用途違い・session名違いの拒否、STSの再更新、leaf再発行、broker再起動後の継続を確認する。

その後、既存DB・保存行・権限を維持した手動デプロイと、親mainのpushによるデプロイを通す。コードの成功、Actionsの成功、無人認証の成功を区別し、未検証の部分は完了と記録しない。

2026年10月5日04:10 UTCの稼働版照合では、機械認証によるv3更新後の署名・全18項目・source7・imageと、旧79テーブルの全行・権限1075項目・同じDB/volumeを確認した。初回のActionsは既存Cloudflare connector停止による公開確認失敗で終了したため、Actions成功とは記録しない。connectorの復旧と常駐化後、公開応答200・200・匿名401、worker ready、pendingなしを確認した。その後の手動Actionsによる成功は、以下に別記する。

runner・OrbStack・brokerはMiniのユーザーセッション内で動く。AWSへの定期的な人のログインは不要だが、FileVault解除前やユーザーのログイン前から動く構成は検証していない。

[手動Actions 37263966083](https://github.com/AtsushiHosaka/pals/actions/runs/37263966083) は親 `8f9bf5b` の通常v1更新で成功した。2026年10月5日04:34 UTCの独立照合では、実KMS署名・sequence4の全18項目・source7・image/OCI label、同じDB/volume、旧79テーブルの全行・権限1075項目・回答2件・利用量10行の保持が一致した。worker ready、用途別read-only mount、公開応答200・200・匿名401、current/receipt一致・pendingなしも確認した。これを受けて `MACMINI_AUTO_DEPLOY=true` とし、親mainのpushから機械認証で配備する。pushごとの成功は、該当Actionsと実機の反映結果で判定する。
