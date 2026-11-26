# seq42 実コンポーネント版リハーサルの再実行

2026-11-26 15:31 JSTに、Mac実機のOrbStackで [pals-infra#401の引き継ぎ手順](https://github.com/AtsushiHosaka/pals-infra/pull/401#issuecomment-7182497855) に従い、`real-cycle` を再実行した。実行したpals-infraコミットは `12a3afc3b22c2743316e945eb43ea2c49264d93a`、Gitツリーは `a59b1dbd64224da54c1579c6a8b2bb20c698d0e6`。リハーサル用候補テンプレートの生ファイルのSHA-256は `243220a7b88296626b0bd1cc5fcdeb4e6dcb3c861c0a7c628aaf31143783417c`。Dockerの隔離ネットワークを使い、ローカルの前任環境と候補で試した。

前回止まったPKI検査はAPIリポジトリを参照できる作業ツリーで通過した。実イメージの取得、実APIイメージによるDB初期化、実オーナープログラムによる両ホストの前任環境構成、復旧記録の検査を含む13項目が通過した。前任環境の構築は235.0秒だった。候補のホスト準備と配置、planの生成と検証、最終planの検証も通過した。

実切替ドライバーはソース検査・事前受入・オーナー取得まで進み、`preflight` が `native_preflight_refused` で停止した。退避処理の `admission-status` は `observer_command_failed` で終わり、オーナー解放も通らなかった。cleanupは通過した。ドライバー全体は27.5秒で、`preflight` は15.6秒だった。

同じツリーで診断を追加して再実行した。Auroraのクラスタとインスタンスの読み取りを通過し、DBの最新admission行を照合する `plan-latest-admission` で停止した。前任環境の構築は237.0秒、ドライバー全体とpreflightの所要時間は初回と同じだった。リハーサルのDB初期化は固定の署名鍵情報を保存する一方、実ドライバーはこの実行の署名鍵を検証して値を計算する。[pals-infra#409で初期化時に実行ごとの署名鍵を使うよう修正した](https://github.com/AtsushiHosaka/pals-infra/pull/409)。

候補種別ごとの全必須シナリオ、復旧時間の計測、実配備候補の署名ゲートおよび本番の読み取り事前検査は未確認。[担当と経緯は #518](https://github.com/AtsushiHosaka/pals/issues/518#issuecomment-7184546859)。
