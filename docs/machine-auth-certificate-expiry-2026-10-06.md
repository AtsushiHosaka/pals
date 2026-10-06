# 11月4日の証明書失効前に、現行世代と更新結果を照合する

確認日: 2026年10月6日。対象はPALSの運用者。

AWS通知の6件と、Mac miniの現行4用途の証明書を照合する必要がある。更新処理は実装済みだが、今回の調査では実機の現行世代と更新状況を確認できていない。通知の件数だけで、稼働用途が6つあるとも、自動更新が失敗しているとも判断しない。

## 通知の6件は過去1日以内に認証で使われた証明書

10月6日09:10:59 JSTのAWS Healthメールを確認した。サービスはIAM Roles Anywhere、accountは`828786775577`、regionは`ap-northeast-1`。イベント種別は`AWS_IAMROLESANYWHERE_EE_CERT_EXPIRY_NOTIFICATION`。メールには、過去1日以内に認証で使われた以下の6件が2026年11月4日に期限を迎えると記載されている。

| 通知のcertificate serial | 現行用途との照合 |
| --- | --- |
| `12ea7e6203739b5404a139d640454b1023d52c` | 未確認 |
| `0ac93ef1f90cf5a64a9cf968888e1bf7967ce1` | 未確認 |
| `00a30f4c68a4e428d8fd53c25fef36801fcc5e7d` | 未確認 |
| `008ad08dec8f7dda9fcefdfb8ec5fb9c67763398` | 未確認 |
| `0fafd51ec01d8cc81fe0bf07f8a2c1a0396e3f` | 未確認 |
| `0b33d797c2ed0da095b10218f2e18d9730bd33` | 未確認 |

全件に`CN=pals-macmini-machine-ca`が記載されている。このCA名だけではleafの用途を区別できない。設置・再発行試験の旧世代が含まれる可能性はあるが、現行serialとの照合前には確定しない。serialは大文字小文字と先頭のゼロを正規化して比較する。

通知原本は[AWS Notification Center](https://console.aws.amazon.com/notifications/home#/notifications/AWS-Health/Operations/a01m4786vzmngzgsqp1780wb4j3/details)で確認する。メールには正確な失効時刻がないため、実機の`notAfter`で確認する。

## 3用途は常駐更新、署名用は取得時に更新する

[10月5日の設置記録](mac-mini-machine-auth.md)では、4用途のleaf期限は11月4日、CA期限は2036年10月5日だった。参照中のinfra commit `bff2e777bd6c1003cfb4b2923e6c89c8c13dc94f`の実装をGit objectから確認した。

| 用途 | leafのCN | 更新処理を呼ぶタイミング |
| --- | --- | --- |
| API | `pals-macmini-api` | brokerの1800秒周期 |
| worker | `pals-macmini-worker` | brokerの1800秒周期 |
| backup-writer | `pals-macmini-backup-writer` | brokerの1800秒周期 |
| release-signer | `pals-macmini-release-signer` | native配備で署名用sessionを取得するとき |

leafの有効期間は30日。取得処理は期限まで7日以内になると再発行するため、設置時の期限が維持されていれば更新開始は10月28日前後になる。正確な開始時刻は現行leafの`notAfter`から7日を引いて求める。release-signerは常駐brokerの対象外なので、使われない期間に現行leafが失効する場合がある。実装は失効後も有効なCAから再発行するが、次の配備を成功と判断するには実認証の確認が必要になる。

新しい鍵とleafを作り、pair・chain・CN・期限・実AWS identityを検査してから`active.json`を原子的に切り替える。一時障害では有効な旧leafで新しいSTS sessionを取得し、更新を延期する。失効したleafへは戻らない。CAの交換は別保守で、新leafの発行にはCAの残存期限が30日より長いことを要求する。

根拠はinfraの[`machine_auth.py`](https://github.com/AtsushiHosaka/pals-infra/blob/bff2e777bd6c1003cfb4b2923e6c89c8c13dc94f/host/macmini-machine-auth/machine_auth.py)、[`broker.py`](https://github.com/AtsushiHosaka/pals-infra/blob/bff2e777bd6c1003cfb4b2923e6c89c8c13dc94f/host/macmini-machine-auth/broker.py)、[`pals_normal_update_authority.py`](https://github.com/AtsushiHosaka/pals-infra/blob/bff2e777bd6c1003cfb4b2923e6c89c8c13dc94f/host/macmini-deploy/pals_normal_update_authority.py)。コードの確認は、現在稼働中のMiniが同じ版を使っていることの証明にはならない。

## Miniでは現行pointer、証明書、brokerの記録を照合する

保管先は`/Users/hosakaatsushi/pals-mini-deploy/machine-auth`。各用途の`leaves/<purpose>/active.json`にある`generation`を読み、同じ用途directory内の`<generation>/cert.pem`を確認する。公開メタデータだけを読む例は次のとおり。`<purpose>`と`<generation>`は実機で確認した値に置き換える。

```sh
openssl x509 -in '/Users/hosakaatsushi/pals-mini-deploy/machine-auth/leaves/<purpose>/<generation>/cert.pem' -noout -serial -subject -issuer -dates -fingerprint -sha256
```

証明書ファイルのSHA256とpointerの`certificate_sha256`も照合する。これは上のOpenSSLが出すDER証明書のfingerprintとは別の値なので、直接比較しない。通知6件のうち現行serialに一致しないものは、保管済みの旧世代の`cert.pem`とも照合し、用途・世代・現行かどうかを記録する。

`broker-status.json`の`checked_at`、`next_renew_at`、3用途の`generation`・`certificate_sha256`・`certificate_expires_at`・STSの`expires_at`・`identity`を確認する。`leaf_renewed`と`renewal_deferred`で更新結果を確認し、pointerと一致すること、記録とSTS期限が古くないことを確かめる。この記録にserialやrelease-signerの定期更新結果は含まれない。

稼働中のLaunchAgent、用途別sessionの受け渡し、worker readyも確認する。証明書の期限だけで、サービスが認証情報を更新できているとは判断しない。秘密鍵、sessionの値、環境ファイル、ログはGitへ保存しない。

## 実認証の確認は、必要時の証明書更新も伴う

Miniの設置済みproviderで4用途を確認するコマンドは次のとおり。出力は認証結果の証跡だけだが、新しいSTS sessionの取得と、期限条件に応じたleafの生成・切り替えを伴う。今回の調査では実行していない。

```sh
/usr/bin/python3 -I -B /Users/hosakaatsushi/pals-mini-deploy/machine-auth/machine_auth.py check-all
```

`issue`の出力には認証情報が含まれるため、端末へ表示せず、既存の配備処理によるprivate pipeで扱う。`check-all`にもCLIの強制更新optionはない。期限に十分な余裕がある状態で実行しても、期限7日前の更新試験にはならない。

## 現行照合と期限前の更新確認が残っている

今回確認できたのは通知原本、設置記録、参照中infraの更新実装まで。手元の`pals-prod-member`と`pals-prod-admin`のSSOはいずれも期限切れだった。Miniの接続先も未確定で、現行4serial・brokerの稼働・AWS側の最終使用履歴は未確認のまま残る。この作業用SSOの失効だけでは、Miniの機械認証が停止したとは判断しない。

まずMiniの現行4用途と通知6件を照合する。10月28日前後の更新開始後には、新generation・新期限・実AWS identity・サービスの継続稼働を確認し、延期が続く場合は11月4日を待たず原因を解消する。署名用も取得時の更新を個別に確認する。これは確認手順の記録であり、将来の監視や確認作業を予約したものではない。

AWSの既定通知はleaf期限45日前からで、30日leafを使う構成では設置直後も通知対象になる。[AWS通知設定](https://docs.aws.amazon.com/rolesanywhere/latest/userguide/customize-notification-settings.html)。通知を受けたことと更新失敗を分け、現行証明書と実際の更新結果で判定する。
