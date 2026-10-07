# 通知の6件を実機で照合し、4用途のAWS認証を確認した

確認日: 2026年10月7日。対象はPALS account `828786775577`、region `ap-northeast-1`。

Mac miniで通知6件を用途と世代に照合し、現行4用途すべてで新しいAWS認証情報を取得できた。常駐broker、API、workerも正常で、修復が必要な障害は見つからなかった。証明書はまだ期限7日前の更新条件に入っておらず、今回のleaf再発行は行っていない。

10月7日の通知3件はAPI・worker・backup-writerの現行証明書だった。残り3件は旧世代2件と現行release-signerで、件数の減少を証明書の更新成功とは扱わない。

前回は更新コードと手順の確認までで、実機確認が残っていた。今回はユーザーの許可で「検証 PALS本番起動」チャットに実機確認を依頼した。以下は同チャットの実行結果に基づく。MacBookからのSSHは名前解決に失敗し、作業用SSOも失効していたため、MacBookから本番へ直接操作した記録ではない。

## 現行4用途の期限は11月4日

2026年10月7日17:25:52 JSTの実機メタデータを確認した。serialは先頭ゼロと大文字小文字を正規化して照合した。

| 用途 | certificate serial | 状態 | notAfter（JST） | 更新条件に入る日時（JST） |
| --- | --- | --- | --- | --- |
| API | `0fafd51ec01d8cc81fe0bf07f8a2c1a0396e3f` | 現行・今日の通知対象 | 11月4日11:01:07 | 10月28日11:01:07 |
| worker | `12ea7e6203739b5404a139d640454b1023d52c` | 現行・今日の通知対象 | 11月4日11:39:34 | 10月28日11:39:34 |
| backup-writer | `0b33d797c2ed0da095b10218f2e18d9730bd33` | 現行・今日の通知対象 | 11月4日11:01:07 | 10月28日11:01:07 |
| release-signer | `008ad08dec8f7dda9fcefdfb8ec5fb9c67763398` | 現行・昨日のみ通知 | 11月4日11:01:07 | 10月28日11:01:07以降の取得時 |

昨日のみ通知されたworkerの`00a30f4c68a4e428d8fd53c25fef36801fcc5e7d`と、backup-writerの`0ac93ef1f90cf5a64a9cf968888e1bf7967ce1`は保管された非現行世代に一致した。実機の10月5日の証跡で、前者は更新試験、後者は失効復旧試験に使用されたことを確認した。署名用が今日の通知にないことは、証明書が更新された証拠にはならない。通知は過去1日以内に認証で使われた証明書を対象にする。

## 常駐brokerはSSOを使わず認証を更新している

実機のLaunchAgentはrunningで、設置コードと起動引数のSHA256が一致した。KeepAliveとRunAtLoadは有効だった。brokerは17:15:55 JSTに3用途を確認し、次回周期を17:45:55 JSTと記録していた。各用途の現行世代と証明書hashはbroker記録と一致した。

3用途とも対象accountと予定role/sessionの実AWS identityを記録し、STS期限は18:15台だった。`ssoconfig_or_cache_used=false`、`renewal_deferred=false`を確認した。`leaf_renewed=false`は、まだ期限7日前の更新条件に入っていない状態と一致する。

## 4用途の新規認証とサービス継続を確認した

設置済みproviderの`check-all`を実行し、4用途すべての実AWS認証が成功した。SSO設定・cacheを使わず、現行世代で認証した。実行前後の現行pointer、コードhash、既存handoffの更新時刻を照合し、常駐brokerの受渡しを変更していないことを確認した。

17:35:41 JSTの最終検査ではAPIとworkerがrunningで、workerは同じcontainer ID・imageのままreadyだった。用途別認証情報のmountはread-onlyだった。公開signin・API healthは200、匿名projectsは401で、想定の応答と一致した。MacBookからの独立確認でも公開API healthは200だった。

## 将来の証明書更新成功は別に確認する

設置済みproviderは期限7日前から新しいleafを発行し、実AWS認証が成功してから現行世代を切り替える。3用途は30分周期、署名用は認証情報の取得時にこの処理を呼ぶ。上表は更新条件に入る日時であり、実際の切替がその秒に起こるという意味ではない。

30日有効のleafは、AWSの既定の45日前通知の対象になる。通知だけで更新失敗と判定しない。[AWS通知設定](https://docs.aws.amazon.com/rolesanywhere/latest/userguide/customize-notification-settings.html)。10月28日以降は現行世代の切替、新しい期限、実認証、サービス継続を確認する必要がある。本記録だけでは将来の監視を予約していない。

## 公開メタデータと認証証跡だけを記録する

Mini側の証跡は`/Users/hosakaatsushi/Documents/Codex/2026-10-04/task/evidence/`にある。`certificate-expiry-20261007-before.json`と`certificate-expiry-20261007-after.json`で現行pointer・serial・期限・hash・broker・LaunchAgentを照合した。`certificate-expiry-20261007-real-identities.json`は`check-all`の公開証跡、`certificate-expiry-20261007-notification-chain-proof.json`は6件のCA chain確認、`certificate-expiry-20261007-service-after.json`はサービス継続と公開応答の記録である。秘密鍵・session値・環境ファイル・ログ全量は親リポジトリへ保存していない。

今日の通知原本は[Gmail](https://mail.google.com/mail/u/?authuser=hosaka2917%40gmail.com#all/1a113b2fea5f33d1)。前回の手順記録は[前回作業ブランチ](https://github.com/AtsushiHosaka/pals/blob/codex/machine-auth-expiry-20261006/docs/machine-auth-certificate-expiry-2026-10-06.md)にある。
