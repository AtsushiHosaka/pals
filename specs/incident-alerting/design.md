# 障害通知の設計

computeの独立したsystemd timerから1分ごとにobserverを起動し、既存Dockerの名前が固定された3actorの状態と、proofとassessment workerの直近5分のログを読む。窓はサンプル時刻の300秒前から5秒前までとし、clarificationの別イベントは対象外とする。Docker時刻付きの完全な最終失敗行だけを認め、理由とIDをメトリクスへ含めない。対象containerの切替、読取上限、未知形式、タイムアウトでは発行を拒否する。

| 名前空間 | メトリクス | 値 |
|---|---|---|
| PALS/IncidentHealth | ExplanationFailureObserved | 説明生成の最終失敗ログを窓内に観測したとき1、読取完了後に未観測なら0 |
| PALS/IncidentHealth | RuntimeHealthy | 3actorがすべてrunningかつhealthyのとき1、それ以外の既知状態は0 |
| PALS/IncidentHealth | MonitorHeartbeat | 必要な読取が全て完了したときだけ1 |

3メトリクスはディメンションなし、Unit=Countで一括発行する。窓内観測を繰り返しても累計件数へ足さない。タイマーは重複起動せず、各処理の総時間を制限し、AWS認証はhostの既存instance profileだけを使う。インストールは保護された新pathに限定し、既存unitやcontainerを停止しない。

説明のアラームはMaximumが1以上、60秒1期間で発火し、OK時の通知は付けない。runtimeはMinimumが1未満の60秒2期間で発火する。説明とruntimeの欠測は非異常として扱い、別のheartbeatで検知する。heartbeatは60秒3期間の欠測または1未満を異常とする。runtimeとheartbeatのOKは、その基盤観測の再開だけを意味する。

既存ALBの`HealthyHostCount`は、実LoadBalancerとTargetGroupのdimensionを固定し、1未満または欠測の60秒2期間で通知する。ALB本体とtargetのHTTP 5xxは、それぞれのSumを欠測0で足し、直近3つの60秒期間のうち1期間でも1以上なら通知する。遅れて届くALBメトリクスを0補完が隠し続けないよう、1/1評価にしない。5xxのOK通知は付けない。ALB設定やtarget登録は変更しない。

アラームは既存SNS topicを参照する。通常の通知は状態遷移単位で、継続ALARM中の個別追加メールや電話への段階通知は今回の範囲に含めない。既存の5分AWS読取も維持するが、オペレーターのローカル環境に依存せずAWS側で通知する。heartbeatはメトリクス到達までの監視であり、SNSから受信箱までの継続的な配送障害を監視するものではない。

配送テストでは、本番の要求やactorを壊さず、専用probeメトリクスと一時アラームを使う。名称と説明にテストと明記し、ALARMからメール受信までを照合してから、一時アラームを回収する。過去の実失敗ログの読取は別に検証し、テストイベントを本番障害の証拠へ置き換えない。


## 配備と変更範囲

独立したTerraform rootは新規stateで5アラームとnamespace限定のinline policy 1件を管理する。既存SNS、既存アラーム、他state、コンテナ用ロールは参照・維持し、所有権を移さない。ALBとターゲットグループのdimensionは実読み取りした値を必須入力し、形式を検証する。形式の合格だけを実在や対応関係の証明にはしない。

通知アクションは既定で無効にし、実planの確認後に明示的に有効化する。本番では最初のapplyで追加6・既存変更0・削除0、その後に新設5アラームの通知有効化と日本語の説明だけを更新した。observerの初回送信と毎分timerのactive/enabled、3actorのID不変を確認した。実ソース、設定、メール到達、probe回収の記録は[通知検証記録](../../docs/incident-notifications-2026-11-06.md)を正本とする。

probeは専用メトリクスと一時アラームで実ALARM、SNSアクション成功、Gmail受信箱到達を確認して削除し、不在を読み戻す。ALARMは配送中にOKへ戻り得るため、回収時に現在もALARMであることは必須にしない。保存済みの実ALARM・配送結果と、現在の設定の完全一致・所有タグを照合する。試験メトリクス履歴は削除せず、追加送信もしない。本番5アラームの有効化状態は回収後も確認する。

## 費用の見積もり

2026年11月4日公開の[公式東京料金表](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonCloudWatch/current/ap-northeast-1/index.json)の保存済み取得結果では、custom metricは月0.30 USD、標準解像度のalarm metricは月0.10 USD、APIは1,000要求あたり0.01 USDである。新設分はcustom metric 3系列、5アラームが評価するmetric 6系列、毎分1回のPutMetricDataを固定する。30日間なら発行43,200回で、無料枠適用前のCloudWatch概算は0.90 + 0.60 + 0.432 = 1.932 USD/月となる。

これは予算用の概算であり請求額の測定ではない。SNS、税、単発の検証・読み取り、31日月の差、既存の無料枠使用状況は別に扱う。月額の計画値を品質台帳の実測費用へ加算しない。利用者や要求ごとのdimensionを作らず、定期的なモデル実行を追加しない。
