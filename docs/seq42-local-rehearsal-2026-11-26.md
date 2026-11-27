# seq42 実コンポーネント版リハーサルの再実行

2026-11-26 15:31 JSTに、Mac実機のOrbStackで [pals-infra#401の引き継ぎ手順](https://github.com/AtsushiHosaka/pals-infra/pull/401#issuecomment-7182497855) に従い、`real-cycle` を再実行した。実行したpals-infraコミットは `12a3afc3b22c2743316e945eb43ea2c49264d93a`、Gitツリーは `a59b1dbd64224da54c1579c6a8b2bb20c698d0e6`。リハーサル用候補テンプレートの生ファイルのSHA-256は `243220a7b88296626b0bd1cc5fcdeb4e6dcb3c861c0a7c628aaf31143783417c`。Dockerの隔離ネットワークを使い、ローカルの前任環境と候補で試した。

前回止まったPKI検査はAPIリポジトリを参照できる作業ツリーで通過した。実イメージの取得、実APIイメージによるDB初期化、実オーナープログラムによる両ホストの前任環境構成、復旧記録の検査を含む13項目が通過した。前任環境の構築は235.0秒だった。候補のホスト準備と配置、planの生成と検証、最終planの検証も通過した。

実切替ドライバーはソース検査・事前受入・オーナー取得まで進み、`preflight` が `native_preflight_refused` で停止した。退避処理の `admission-status` は `observer_command_failed` で終わり、オーナー解放も通らなかった。cleanupは通過した。ドライバー全体は27.5秒で、`preflight` は15.6秒だった。

同じツリーで診断を追加して再実行した。Auroraのクラスタとインスタンスの読み取りを通過し、DBの最新admission行を照合する `plan-latest-admission` で停止した。前任環境の構築は237.0秒、ドライバー全体とpreflightの所要時間は初回と同じだった。リハーサルのDB初期化は固定の署名鍵情報を保存する一方、実ドライバーはこの実行の署名鍵を検証して値を計算する。[pals-infra#409で初期化時に実行ごとの署名鍵を使うよう修正した](https://github.com/AtsushiHosaka/pals-infra/pull/409)。

修正後のツリー `d771016ad1fd7c297c8c613e940e5099b0b2a80d` で再実行した。前任環境の13項目、最終plan検証、実切替ドライバーのpreflightが通過した。前任環境の構築は231.2秒、ドライバー全体は33.9秒、preflightは16.5秒。次のcompute側の `lifecycle-plan` が `actual-previous-tuple-readiness` で `recovery_network_changed` を返し、実ドライバーはローカルの通信停止とadmissionに進む前に停止した。観測とオーナー解放は通らず、cleanupは通過した。

computeの隔離ホストで同じサブネットを指定してブリッジを作成した。Dockerデーモンの再起動前はIPAMがサブネットだけを返し、再起動後は同じサブネットに既定ゲートウェイを加えて返した。[pals-infra#410](https://github.com/AtsushiHosaka/pals-infra/pull/410) ではcomputeの復旧検査がこの表現を受け入れるようにした。既定値と異なるゲートウェイやサブネットは拒否する。回帰の再現後、回復スイート42件が通過した。現行のリハーサルは前任側にも検証ツリーのヘルパーを配置する。本番の固定済みヘルパーに対する確認は、本番の読み取り事前検査に残る。

両修正を合わせたツリー `21a6bc94df307f8288e83cb15a2f3cde0426fd44` では、実切替ドライバーがpreflight、plan、復旧事前検査、通知窓の開始と隔離環境内の通信切離しまで進んだ。computeの停止確認で `drain_readback_refused` が出たため、admissionには進まなかった。通知窓の取消とcleanupは通過し、オーナー解放は失敗した。前任環境の構築は229.0秒、ドライバー全体は110.8秒、停止処理は20.6秒だった。

修正の対象コミットでは重いCIがそれぞれ4件通過した。[署名鍵の修正](https://github.com/AtsushiHosaka/pals-infra/actions/runs/45771930188) · [computeの復旧検査](https://github.com/AtsushiHosaka/pals-infra/actions/runs/45772302312)。ローカルのplan一括テストは、テスト中に作業ツリーのブランチを切り替えたため対象リビジョンの証拠から外した。

検証器の同じAMD64イメージをOrbStackの読み取り専用コンテナで動かし、停止確認のプロセス計数を切り出した。読み取り専用ルートの /tmp ではRosettaが一時ファイルを作れず終了コード133になった。TMPDIRを既存の検証器用一時領域に変えても結果は同じだった。実行不可の8 MiB tmpfsを /tmp に置いた場合はプロセス計数が完了した。[pals-infra#412](https://github.com/AtsushiHosaka/pals-infra/pull/412) はこの一時領域をOrbStack上のリハーサルに限定し、ドレインの拒否時に閉じた処理段階と原因コードを返す。

Rosetta対応後の統合ツリー 98b02a3f04e1fda6122d89f0ff5db9f9358388a4 で再実行した。隔離環境の停止確認、DBの候補登録、確定、3段階の起動、簡易ヘルス、ターゲット登録、通知窓の終了が通過した。次の control 側の復旧ヘルス検査が拒否し、最終受入とオーナー解放は完了しなかった。cleanupは通過した。前任環境の構築は234.0秒、ドライバー全体は289.7秒だった。

復旧診断を含むツリー 1af8373c52c479d7def433ea89ba03ee16d16e27 で再実行し、同じ復旧ヘルスの拒否を再現した。[pals-infra#414](https://github.com/AtsushiHosaka/pals-infra/pull/414) の診断で、拒否した操作はcontrolの `install-recovery`、原因コードは `systemd_command_failed` と追跡できた。前任環境は241.4秒、切替ドライバーは290.4秒だった。

同型の隔離ホストで単独確認したところ、APIの資格情報サービスは `LoadState=not-found` だった。実オーナーが生成したcontrolとreconcilerの復旧unitを `systemd-analyze verify` に渡すと、要求先の `pals-private-api-credentials.service` が存在しないと報告して終了コード1を返した。

正規のレンダラーが出力した資格情報サービスを一時ディレクトリに置き、同じ隔離ホストで復旧unitと合わせて検証した。controlとcomputeの両方で systemd-analyze verify が終了コード0となった。[pals-infra#416](https://github.com/AtsushiHosaka/pals-infra/pull/416) は、隔離ホストの認証サービスを停止状態かつ無効で配置する。STS更新や実ホストの再起動は今回の検証範囲に含まれない。

資格情報unitを含むツリー d9fc194ff7650ca5426f749f87685c0ead7fe834 のOrbStack実走は `rehearsal_passed` で終了コード0だった。切替ドライバーは `accepted`、`owner_released=true` を返し、cleanupも通過した。前任環境の13検査は230.6秒、切替ドライバーは288.9秒。両ホストの復旧検査、最終ヘルス、ローカルの受入とオーナー解放を1回の実行で通過した。

今回の受入にはリハーサルの代替親ランナーを使った。OrbStackのAMD64エミュレーションには専用の一時領域があり、STSブローカーは停止状態。候補種別ごとの全必須シナリオ、復旧時間の計測、実配備候補の署名ゲートおよび本番の読み取り事前検査は未確認。[担当と経緯は #518](https://github.com/AtsushiHosaka/pals/issues/518#issuecomment-7184546859)。

## Isolated compensation and standby handover

On November 26 UTC, two isolated OrbStack runs on `a10c711` injected a PostgreSQL admission lock and exercised the full recovery of the serving predecessor. The restore steps took 143.836 s and 142.834 s. Both runs restored the original healthy host containers and registered ingress, verified the unchanged database admission, cancelled the notification window, released the owner, and cleaned up.

The first typed standby run on `0cea94b` completed the native handover from A to S and cleaned up after S began serving. The overall typed case failed at evidence export with `primitive_plan_lineage_differs`. The exporter rejected the standby declaration that the inherited-window plan required.

The retry on `9cf9fdb` bound the exact child plan and reached `standby_case_recorded`. It verified S admission and serving, released the owner, and completed cleanup. The interval from A ingress deregistration to S ingress registration was 291.515 s. The inherited notification window was deleted 315.444 s after it became active. These runs used isolated AWS and acceptance substitutes. Production timing and the live A/S model qualifications remain separate release gates. [Release tracking](https://github.com/AtsushiHosaka/pals/issues/509)

## SのDB承認後に障害を起こした隔離試験

統合コミット `c334c9a` では、SのDB承認後に確定処理を一度失敗させた。Sの復旧処理が `same_window_fault_reconcile_not_verified` で止まり、通し試験は失敗した。`49f5fa7` の追試では、試験が復旧直前に発行した確認用SSMコマンドを、安全検査が未確認の操作として検知した。Aの通知抑制は両試行で解除できた。

試験側のホスト確認を復旧後に移した `bcb830e` では、同じ障害から正規の `--reconcile` でSを復旧できた。復旧開始から通信先の再登録まで173.500秒、受入と後片付けの完了まで223.032秒だった。DB承認の重複はなく、通知抑制は期限の956.525秒前に解除した。オーナーの解放と試験用Dockerリソースが残っていないことを読み戻し、型付き証跡を再検証した。

修復ジャーナルのSHA-256は `4fe7c093c859628df55f7871589f63470ef239c83fb4e291c25adac071e8de54`。試験では隔離したAWS実装と受入用の代替ランナーを使った。実測値を本番の署名予算へ取り込む検証と、実モデルを使うA/Sの受入は継続中。 [修正コミットの回帰CI](https://github.com/AtsushiHosaka/pals-infra/actions/runs/45868756885)

## SのDB承認前に障害を起こした隔離試験

`bcb830e` でSのDB承認を拒否させた。DBはAを承認した状態を保ち、稼働中の通信先は空のまま、Sが復旧用のオーナー権限を保持した。Aで開いた通知抑制は期限の967.810秒前に解除した。隔離環境のDockerリソースを削除し、型付き証跡の再検証を通過した。

証跡のSHA-256は `d946833a6f68b77ba5ddd01babe7837d7e2cdb02723797f8fbeade5935fa2355`。この試験はSの承認を拒否した時点でのDB、オーナー権限、通信先、通知の状態を確認した。 [修正コミットの回帰CI](https://github.com/AtsushiHosaka/pals-infra/actions/runs/45868756885)

## 待機系の実測を署名側で再検証

`23957d6` でAの確定処理に障害を入れ、同じ通知窓でSへ切り替えた。Aの通信先を外してからSの通信先を登録するまで282.512秒だった。Sの隔離環境での受入とオーナー解放を確認し、試験用Dockerリソースを削除した。

署名ゲートの検証器は、P・A・Sの原本と実行ツール、署名、実行結果、片付けを再検証した。移管10.135秒、Sの事前検査20.668秒、通信先の登録解除15.836秒、書き込み停止の確認35.661秒、通知窓の読み戻し0.151秒を取り込んだ。これらは隔離環境での実測値で、1,800秒の予算判定には別途、復旧経路の測定と本番実績による補正が要る。 [回帰CI](https://github.com/AtsushiHosaka/pals-infra/actions/runs/45872349109)

## 同じツールで通常の復旧を再計測

`23957d6` と同じP・Aを使い、通常の切替でAのDB承認をPostgreSQLのロックで拒否させた。復旧は140.768秒、復旧後の前任のヘルス検査は9.469秒だった。通信先を外してから前任を再登録するまでは216.767秒。DBがPを承認したまま、両ホストでPの元のコンテナが稼働し、通知抑制とオーナー権限が解除されたことを確認した。

この試験は通常の切替用の計画で実行し、承認済み候補向けの復旧ブリッジは使っていない。ジャーナルのSHA-256は `1dac873a5c8001f5db9a5fa1411429288a4106fa2afb49279537fd7f7a59f49c`。

署名ゲートと同じ取り込み処理で、通常復旧とSへの切替について実測記録を再現できた。現行の換算は、代替ランナーを使う受入検査から計算した約798倍を未計測の本番工程にも掛ける。換算後は通常復旧と待機切替の両方が1,800秒の予算を超え、判定は `window_budget_cannot_fit` だった。

## 同じツールで待機系の稼働確認を再実行

`23957d6` で、Aの承認後に書き込みが止まった状態から同じ通知窓でSを起動した。Aの通信先を外してからSを登録するまでは289.499秒だった。AからSへのオーナー移管、Sの受入とオーナー解放、通知抑制と試験用Dockerリソースの片付けを確認し、型付き証跡の検証に通った。

同じP・A・Sの原本で、SのDB承認後に確定処理を一度失敗させた。通知抑制を解除し、同じSを正規の復旧経路で起動した。復旧開始からSの通信先の登録までは176.476秒、受入と片付けの完了までは225.055秒だった。SのDB承認は一度で、オーナー解放と試験用Dockerリソースが残っていないことを確認した。

SのDB承認前に拒否する試験も、同じ原本とツールで合格した。DBはAを承認した状態を保ち、Sが復旧用のオーナー権限を保持し、通信先は空のままだった。通知抑制は期限の965.784秒前に解除された。片付けまで通過した4試行の証跡を正規CLIで集約し、再検証した。集約した証跡のSHA-256は `85e4193571a25f10e448749f9a9e5a92b2a84cf35795613f3ce96bcea9752b79`。

## 実モデル検証用の専用依存サービス

MacのOrbStackで、PostgreSQL 16、LocalStack、CognitoのエミュレーターをAとSに1組ずつ起動した。6サービスの正常性、各DBの専用ユーザーと初期状態、各4キューにメッセージがないことを読み戻した。旧PostgreSQLの稼働、旧予算ガードの停止、元の予算台帳のSHA-256も確認した。各候補に対応するスキーマ準備と実モデルの受入は未実施。 [専用環境の起動と検証の実装](https://github.com/AtsushiHosaka/pals/pull/533)
