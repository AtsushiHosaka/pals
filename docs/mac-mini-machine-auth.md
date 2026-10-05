# Miniの常時運転を人のSSOから切り離す

更新日: 2026年10月5日。対象はPALSの運用者。現状と変更案の確認用。本人からこの構成の設置許可を受領し、機械認証の導入と実機検証を進めている。

## SSOの期限延長では常時運転にならない

現在のMiniは、人の `pals-prod-member` SSOから用途別のSTS sessionを取得する。既存brokerは1時間のsessionを30分ごとに更新するが、元のSSOが失効すると更新できない。10月4日と5日に失効し、workerが停止した。5日の本人再ログイン後、同じworkerのCID・imageでRunningとreadyへ復帰した。復旧時にはDB更新や新しい権限の付与を行っていない。

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

設置中の検証では、専用CAと4用途のleafをこの領域に生成した。CAの期限は2036年10月5日、leafは2026年11月4日。実OpenSSLによるpair・chain・権限の検査と、更新失敗時の旧世代保持を含む15テストが通過した。常駐プロセスによる実AWS認証と自然更新は検証を残している。

CAとleafは、公式helperが扱える名前付きEC曲線で生成した。4roleの分割trustは適用と読み戻しを完了し、旧SSOと権限を保持した。APIはSSO設定・cacheを利用しない実AWS認証に成功し、予定のRoleIdとsession名で1時間のsessionを取得した。残り3用途と常駐brokerへの切り替えは検証中。

CAのCNは `pals-macmini-machine-ca`。leafは `pals-macmini-api`、`pals-macmini-worker`、`pals-macmini-backup-writer`、`pals-macmini-release-signer` の4つに分ける。CA鍵を読めるホストユーザーは4用途すべてを認証できるため、同じUID内での権限分離は保証しない。Miniホストを信頼境界とし、AWS側では4roleの権限に限定する。

## 証明書の更新と一時障害からの復帰も自動化する

CAは10年、leafは30日の有効期間とし、leafの期限7日前から更新する案。broker起動時とSTS更新前にも期限を検査し、長期停止後の失効したleafも、有効なCAから再発行する。新しいkey・certificateを同じ世代directoryに作り、pair・chain・CN・期限と実AWS identityを検査してから原子的に切り替える。

CA自体の交換は事前保守として扱う。leafの自動更新だけで、登録anchorとCAも無期限に更新できるとは説明しない。CAの失効前に交換する手順と監視を設置する。CA鍵が漏洩した場合は、専用anchorを無効化する。

brokerは期限前にSTSを更新し、一時的な失敗では再試行する。常駐処理とworkerの再起動方式を検証し、配備中に意図的に停止したworkerを勝手に起動しない。

## SSOを使わない実機検証後にpush連動を有効にする

設置前に既存4roleのtrust・policy・RoleIdを保存し、設置後もpermissionsが変わっていないことを確認する。SSOのprofile・cacheを利用できない実行環境で、全4用途のidentity、用途違い・session名違いの拒否、STSの再更新、leaf再発行、broker再起動後の継続を確認する。

その後、既存DB・保存行・権限を維持した手動デプロイと、親mainのpushによるデプロイを通す。コードの成功、Actionsの成功、無人認証の成功を区別し、未検証の部分は完了と記録しない。
