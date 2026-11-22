# seq30予行の権限修正と再確認（2026-11-14）

指標はリリース予行の完了と所要時間。数学の正答率や証明1件の性能を測ったものではない。

仮説は、実行ラッパーから引き継いだ権限制限が予行用イメージに入り、検査ユーザーによるソース読み取りを妨げている、というものだった。

測定はlocal macOSの隔離Docker環境で実施した。クラウド、製品、ownerは予行用の代用品で、有料モデルは呼んでいない。各行は技術試行1回で、モデル、推論量、カード、修復上限は対象外。

## 原因と変更

7efの最初のゲートと隔離再現はpreflightで失敗した。記録の`owning-module-bytes`と`ValueError`だけでは、コマンド失敗とハッシュ不一致を区別できなかった。8b19で読み取りコマンドと比較のphaseを分けたところ、前者の失敗と分かった。

同じDocker引数による調査で`PermissionError`を確認した。ラッパーでログを保護するために設定した`umask 077`が予行に引き継がれ、macOSの`cp -R`が0755のディレクトリと0644のファイルを0700・0600でコピーしていた。rootで読んだイメージ内モジュールは、元ソースと期待ハッシュに一致した。本番のソース不一致を示す結果ではない。

684の変更は、予行用productをコピーした後に`chmod -R a+rX`を適用するもの。通常のPythonファイルを実行可能にせず、読み取りとディレクトリ探索を可能にした。本番operatorのユーザー、ハッシュ検査、制限は維持した。変更はinfra PR #180でマージされ、マージ後の03ccで7筋書きを実行した。

## 測定結果

成功は各筋書きが期待する停止、復旧、照合を含む結果を満たすこと。意図したcontrollerの失敗も、安全条件と期待結果を確認できれば筋書きとして成功と数える。

| 技術試行 | 成功/試行 | 所要秒 | 品質台帳の行ID |
|---|---:|---|---|
| 7ef・マージ後success | 0/1 | case=221.158; wrapper=221.281 | `2026-11-14-seq30-7ef-rehearsal-preflight-failed` |
| 7ef・隔離再現 | 0/1 | run=160.476; total=162.268 | `2026-11-14-seq30-7ef-preflight-diagnostic-reproduction` |
| 8b19・診断変更後 | 0/1 | run=161.938; initial_capture=162.058 | `2026-11-14-seq30-8b19-preflight-permission-diagnosis` |
| 684・開発検証success | 1/1 | case=372.358; wrapper=372.487 | `2026-11-14-seq30-684-packaging-development-validation` |
| 03cc・success | 1/1 | case=328.837 | `2026-11-14-seq30-03cc-rehearsal-success` |
| 03cc・fail-before-admit | 1/1 | case=381.699 | `2026-11-14-seq30-03cc-rehearsal-fail-before-admit` |
| 03cc・expired-predecessor-fail-before-admit | 1/1 | case=363.945 | `2026-11-14-seq30-03cc-rehearsal-expired-predecessor-fail-before-admit` |
| 03cc・fail-after-admit | 1/1 | case=392.429 | `2026-11-14-seq30-03cc-rehearsal-fail-after-admit` |
| 03cc・crash-after-admit | 1/1 | case=370.167 | `2026-11-14-seq30-03cc-rehearsal-crash-after-admit` |
| 03cc・expired-predecessor | 1/1 | case=359.778 | `2026-11-14-seq30-03cc-rehearsal-expired-predecessor` |
| 03cc・recovery-units-active | 1/1 | case=355.234 | `2026-11-14-seq30-03cc-rehearsal-recovery-units-active` |

8b19の162.058秒は証拠の初回回収までで、後続調査とcleanupを含む総時間は未計測。03ccの各筋書きは600秒未満だったが、ケース合計は2552.089秒、ラッパー全体は2553.067秒で、7件全体の10分条件は満たしていない。

## 判断と限界

予行用の権限修正は採用した。開発検証とマージ後7筋書きは成功し、各試行の専用Docker資源の回収とソースのcleanを確認した。8b19の初回記録には調査のための資源保持が残り、その後のcleanup記録で回収を確認している。

以前の失敗3試行は残す。異なるコミットや実行条件の結果から改善率を算出せず、数学の精度、モデル性能、本番受け入れの成功とは扱わない。有料モデル呼び出しはなく、その他の実行費用は未集計。

本番の通知抑制、切り替え、質問の終端、保存、描画、再読み込みは別途確認が必要。全体10分条件の未達も残る。次の判断では、この予行結果と本番の証拠を分けて扱う。

## 出典

- [停止・原因調査・修正後予行の記録](../../seq30-preflight-diagnosis-2026-11-14.md)。各ログのSHA-256と開始時負荷を含む。
- [品質台帳](../../quality-ledger/ledger.csv)。上表の11行が数値の参照先で、このジャーナルのための台帳行は追加していない。
- [infra PR #180](https://github.com/AtsushiHosaka/pals-infra/pull/180)、[親PR #393](https://github.com/AtsushiHosaka/pals/pull/393)。
- ローカル原本は`/private/tmp/pals-seq30-mute-merged-7ef4034`、`/private/tmp/pals-seq30-mute-merged-debug-7ef4034`、`/private/tmp/pals-seq30-mute-merged-debug-8b19b22`、`/private/tmp/pals-seq30-packaging-dev-684dd17`、`/private/tmp/pals-seq30-packaging-merged-03cc80f`。
