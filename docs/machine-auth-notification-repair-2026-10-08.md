# 更新が進まない証明書を期限3日前から警告する

2026年10月8日12:38 JST、PALSのIAM Roles Anywhereで、用途別証明書の期限警告を45日前から3日前へ変更した。警告は有効のまま保持した。30日有効・期限7日前に自動更新する運用に対し、正常な証明書も毎日警告される設定だったことが原因である。

対象はAWS account `828786775577`、region `ap-northeast-1`、trust anchor `pals-macmini-machine`（ID `19ba8073-2d7e-4907-815a-68f979ebb580`）。SSO再ログイン後に対象accountを確認し、AWSの実設定を読み取ってから適用した。

## 実設定の変更と読み戻しが一致した

| 通知対象 | 変更前 | 変更後 |
| --- | --- | --- |
| 用途別証明書 `END_ENTITY_CERTIFICATE_EXPIRY` | 有効・45日前・ALL | 有効・3日前・ALL |
| CA `CA_CERTIFICATE_EXPIRY` | 有効・45日前・ALL | 同じ設定を保持 |

変更前の両設定は `configuredBy=rolesanywhere.amazonaws.com` だった。変更後の用途別証明書の設定主体は対象accountとなった。別の `GetTrustAnchor` による読み戻しで、期限3日前・有効・ALLを確認した。AWS側の更新時刻は `2026-10-08T03:38:01.746883Z`。

変更前後のtrust anchor ID・ARN・名前・有効状態・CA証明書source・作成日時は一致した。CA通知設定と `ListProfiles` のJSON全体も一致した。独立レビューでも、差分が用途別証明書の警告閾値・設定主体・更新日時だけであることを確認した。

再適用する場合は対象accountを確認し、次の通知設定だけを指定する。

```sh
aws rolesanywhere put-notification-settings \
  --trust-anchor-id 19ba8073-2d7e-4907-815a-68f979ebb580 \
  --notification-settings '[{"enabled":true,"event":"END_ENTITY_CERTIFICATE_EXPIRY","threshold":3,"channel":"ALL"}]' \
  --profile pals-prod-member --region ap-northeast-1
```

## 現在も証明書によるAWS認証が続いている

対象anchorの `AWS/RolesAnywhere`、`Success`、`Operation=CreateSession` をCloudWatchから取得した。集計範囲は10月7日12:30 JSTから10月8日12:38 JST、統計は `Sum`、周期は1800秒。48区間で計168回成功し、最新の10月8日12:00 JST区間も7回成功した。用途別の状態を分けた値ではないため、この合計だけで4用途すべての健全性を証明したとは扱わない。

さらに `GetSubject` の用途別監査記録で、最新の証明書認証が4用途とも `failed=false` であることを確認した。AWSが監査記録として返した公開証明書をOpenSSLで解析し、通知serialと期限も照合した。

| 用途 | 最新認証成功（10月8日JST） | 証明書期限（JST） |
| --- | --- | --- |
| API | 12:26:52 | 11月4日11:01:07 |
| worker | 12:26:58 | 11月4日11:39:34 |
| backup-writer | 12:27:03 | 11月4日11:01:07 |
| release-signer | 12:27:49 | 11月4日11:01:07 |

今日09:10 JSTのメールは現行4枚すべてを対象とし、期限は11月4日だった。変更後の3日前という条件に、現在の証明書は入らない。将来も正常に期限7日前の更新が続けば、発行直後からの毎日の警告は生じない。

## 更新停止の監視は用途別の状態も確認する

用途別証明書のAWS Health警告は、直近1日で認証に使用した証明書だけを対象にする。認証処理自体が完全停止した場合は、この期限警告だけでは検知できない。CloudWatchの `DaysToExpiry` もCA用なので、用途別証明書の期限監視には流用しない。

追加作業前のTokyo regionのCloudWatch alarmとSNS topicは0件だった。その後、ユーザーの許可でMac miniの既存チャット「検証 PALS本番起動」に、実機の最終確認と更新停止監視の整備を依頼した。12:51 JSTの `check-all` は4用途すべての実AWS認証に成功し、証明書世代は不変、更新延期もなかった。12:57 JSTにもbrokerが通常の周期でSTSを更新した。

MiniにLaunchAgent `site.pals.machine-auth-monitor` を設置した。毎分、用途別の状態・35分の鮮度・STS期限・証明書hash・更新延期を検査する。API・worker・backup-writerの診断認証は追加せず、署名用途だけはruntime3用途が正常な時に1時間ごとに確認する。署名用途の15分STSが自然失効したことは障害と扱わない。初回の常駐実行は正常終了し、runtime3用途が正常、backgroundからの署名用途の認証も成功した。正常時の通知は0件だった。

復旧先は既存brokerのLaunchAgentに限定し、保守による明示停止と別publisherを尊重する。通常の再試行を妨げないよう、更新予定から2分の遅延では強制再起動せず、35分の鮮度基準で停滞を判定する。復旧要求は10分間隔・1時間3回まで。未解消の異常と復旧はMac通知へ送り、記録は保護されたローカル領域に残す。Mac通知の送信失敗は通知済みと記録せず、60秒間隔・10分で最大3回再試行する。Mac通知の要求成功は、画面への表示や本人の既読を証明するものではない。

監視コードの40試験とruffがPASSした。独立レビューで通常の再試行を中断する条件と通知失敗時の再試行不足を見つけ、両修正と回帰試験を再レビューした。実装と実機証跡は[pals-infraのcommit db1b546](https://github.com/AtsushiHosaka/pals-infra/commit/db1b546f25d7540e22b5995445e1ccf72db7ca7b)までpush済み。

13:21:49 JST、既存brokerの停止を検知し、設置監視の復旧関数から固定LaunchAgentへ要求した結果、PIDが58397から77205へ変わり、runtime3用途すべてが新しいSTSでreadyに戻った。試験中は監視lockを保持して復旧関数を直接呼んだため、毎分tickからの自然な復旧遷移や、launchdのKeepAliveと独立した因果関係を実測したものではない。判定遷移は回帰試験、復旧機構は実機試験として区別する。

13:30:45–46 JST、復旧後の新しい認証情報がAPI・worker・backup-writerのconsumer guardで受け入れられたことを確認した。API・workerのCID・image・RestartCountは不変で、worker ready、公開URLの200・200・匿名401も確認した。毎分監視は11回正常終了し、正常時の通知は0件だった。4証明書の世代と既存認証コードは不変で、再設置では監視lockのinodeが保持された。実機の復旧試験と、その後のconsumer受入・サービス継続を独立レビューでも確認した。

## Miniが停止してもAWS側で認証欠測を検知する

親チャットでCloudWatch alarm `pals-macmini-machine-auth-stalled` とSNS topic `pals-macmini-auth-alerts` を作成した。SNSの通知先は本人のPALS宛 `hosaka2917+pals@gmail.com` で、購読確認を完了した。通知はALARM・OKの状態遷移時だけであり、正常時の定期メールは送らない。初期のOK遷移時には確認用の通知が1通届いた。

アラームは対象anchorの既存 `Success` 指標を1800秒周期の `Sum` で読み、`FILL(sessions,0)` で欠測を0にする。3区間連続で認証成功が3回未満の場合にALARMとなり、式の結果も欠測なら `breaching` と扱う。直近24時間の48区間はすべて3回以上で、この基準と一致した。3区間連続という条件で、周期のずれや単発の計測遅延を許容する。これはホスト外での集約認証不足の検知であり、別用途の利用やbrokerの再試行が成功数を増やす場合には停止した用途を区別できない。用途別の停滞はMini側で補う。

SNSへのCloudWatchサービスのPublish許可は、対象accountとこのアラームのARNを条件に限定した。既存4用途のIAM権限へSNS権限を追加していない。アラームの設定・SNS policy・購読状態を読み戻し、設定値の一致を検査した。

12:57:03 JST、認証処理を止めずに `SetAlarmState` でALARM通知経路を試験した。理由には「監視通知経路の試験です。本番の証明書認証は正常です」と明記した。12:57:56 JSTには実指標の評価で自然にOKへ戻った。両遷移のSNS action成功履歴と、本人のGmailで[ALARM試験メール](https://mail.google.com/mail/u/?authuser=hosaka2917%40gmail.com#all/1a119a8517d8a0f9)・[OK復帰メール](https://mail.google.com/mail/u/?authuser=hosaka2917%40gmail.com#all/1a119a92045ee755)の受信を確認した。これは通知経路と自然復帰の実証であり、本番の認証を90分停止した試験ではない。

10月28日の将来の自然更新成功と、次のAWS日次評価後の期限メール不着は、現時点では未観測である。

根拠は[AWS通知設定](https://docs.aws.amazon.com/rolesanywhere/latest/userguide/customize-notification-settings.html)、[Health通知の対象条件](https://docs.aws.amazon.com/rolesanywhere/latest/userguide/monitoring-health.html)、[CloudWatchの指標定義](https://docs.aws.amazon.com/rolesanywhere/latest/userguide/monitoring-cloudwatch.html)、[通知原本](https://mail.google.com/mail/u/?authuser=hosaka2917%40gmail.com#all/1a118d95555a98e8)。AWS読み戻しの一時ファイル、証明書、認証情報はGitへ保存していない。
