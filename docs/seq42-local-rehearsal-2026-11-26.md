# seq42 実コンポーネント版リハーサルの再実行

2026-11-26 15:31 JSTに、Mac実機のOrbStackで [pals-infra#401の引き継ぎ手順](https://github.com/AtsushiHosaka/pals-infra/pull/401#issuecomment-7182497855) に従い、`real-cycle` を再実行した。実行したpals-infraコミットは `12a3afc3b22c2743316e945eb43ea2c49264d93a`、Gitツリーは `a59b1dbd64224da54c1579c6a8b2bb20c698d0e6`。リハーサル用候補テンプレートの生ファイルのSHA-256は `243220a7b88296626b0bd1cc5fcdeb4e6dcb3c861c0a7c628aaf31143783417c`。Dockerの隔離ネットワークを使い、ローカルの前任環境と候補で試した。

前回止まったPKI検査はAPIリポジトリを参照できる作業ツリーで通過した。実イメージの取得、実APIイメージによるDB初期化、実オーナープログラムによる両ホストの前任環境構成、復旧記録の検査を含む13項目が通過した。前任環境の構築は235.0秒だった。候補のホスト準備と配置、planの生成と検証、最終planの検証も通過した。

実切替ドライバーはソース検査・事前受入・オーナー取得まで進み、`preflight` が `native_preflight_refused` で停止した。退避処理の `admission-status` は `observer_command_failed` で終わり、オーナー解放も通らなかった。cleanupは通過した。ドライバー全体は27.5秒で、`preflight` は15.6秒だった。

同じツリーで診断を追加して再実行した。Auroraのクラスタとインスタンスの読み取りを通過し、DBの最新admission行を照合する `plan-latest-admission` で停止した。前任環境の構築は237.0秒、ドライバー全体とpreflightの所要時間は初回と同じだった。リハーサルのDB初期化は固定の署名鍵情報を保存する一方、実ドライバーはこの実行の署名鍵を検証して値を計算する。[pals-infra#409で初期化時に実行ごとの署名鍵を使うよう修正した](https://github.com/AtsushiHosaka/pals-infra/pull/409)。

修正後のツリー `d771016ad1fd7c297c8c613e940e5099b0b2a80d` で再実行した。前任環境の13項目、最終plan検証、実切替ドライバーのpreflightが通過した。前任環境の構築は231.2秒、ドライバー全体は33.9秒、preflightは16.5秒。次のcompute側の `lifecycle-plan` が `actual-previous-tuple-readiness` で `recovery_network_changed` を返し、実ドライバーはローカルの通信停止とadmissionに進む前に停止した。観測とオーナー解放は通らず、cleanupは通過した。

computeの隔離ホストで同じサブネットを指定してブリッジを作成した。Dockerデーモンの再起動前はIPAMがサブネットだけを返し、再起動後は同じサブネットに既定ゲートウェイを加えて返した。[pals-infra#410](https://github.com/AtsushiHosaka/pals-infra/pull/410) ではcomputeの復旧検査がこの表現を受け入れるようにした。既定値と異なるゲートウェイやサブネットは拒否する。回帰の再現後、回復スイート42件が通過した。現行のリハーサルは前任側にも検証ツリーのヘルパーを配置する。本番の固定済みヘルパーに対する確認は、本番の読み取り事前検査に残る。

両修正を合わせたツリー `21a6bc94df307f8288e83cb15a2f3cde0426fd44` では、実切替ドライバーがpreflight、plan、復旧事前検査、通知窓の開始と隔離環境内の通信切離しまで進んだ。computeの停止確認で `drain_readback_refused` が出たため、admissionには進まなかった。通知窓の取消とcleanupは通過し、オーナー解放は失敗した。前任環境の構築は229.0秒、ドライバー全体は110.8秒、停止処理は20.6秒だった。

修正の対象コミットでは重いCIがそれぞれ4件通過した。[署名鍵の修正](https://github.com/AtsushiHosaka/pals-infra/actions/runs/45771930188) · [computeの復旧検査](https://github.com/AtsushiHosaka/pals-infra/actions/runs/45772302312)。ローカルのplan一括テストは、テスト中に作業ツリーのブランチを切り替えたため対象リビジョンの証拠から外した。

候補種別ごとの全必須シナリオ、復旧時間の計測、実配備候補の署名ゲートおよび本番の読み取り事前検査は未確認。[担当と経緯は #518](https://github.com/AtsushiHosaka/pals/issues/518#issuecomment-7184546859)。
