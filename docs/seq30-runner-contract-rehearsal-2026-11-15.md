# seq30の受け入れ契約修正後の予行

## ソースと必須検査

[infra #181](https://github.com/AtsushiHosaka/pals-infra/pull/181)を`claude/seq30-worker-trust`へ統合した。統合コミットは`ce084f345b3ebaa3fe15aee0a1519e6b0dceffaf`で、レビュー済みhead `4ba2009`とツリーが同一である。契約の生成側を実consumerと同じ4ファイルのfingerprintへ合わせ、欠落・変更の拒否と固定した実parentへの受け渡しを検査する。API・Web・worker・検証器は変更していない。

正確な統合コミットの[必須CI](https://github.com/AtsushiHosaka/pals-infra/actions/runs/43594794847)は、release-cycle-regression、release-host-harness、private-runtime-trust-tables、release-e2eの4件すべて成功した。実行先は自前ランナーである。関連212件のローカル検査と、正確なheadの独立レビューも完了した。検査件数は以下の予行の分母に加えない。

## 初回7シナリオと所要時間の未確認

統合後の同じcleanなソースから、正規の`sh tests/rehearsal/run.sh`を7通り順に実行した。機能上は全7件が`rehearsal_passed`となり、専用container・network・volume・imageを回収した。オーナー・製品・クラウドは代用品であり、本番や数学の受け入れではない。

ただし、外側の計測がmonotonic時計だけを使っており、Macのスリープ時間を含めていなかった。OSのSleep・Wake記録と壁時計の差を確認した。6件目の開始から7件目の開始までは809.270秒あり、7件目にも長い中断があった。終了時の壁時計を記録していなかったため、この2件を壁時計600秒以内の成功として採用しない。元の集計とログは書き換えていない。

| シナリオ | 初回のmonotonic秒 | 壁時計の確認 |
|---|---:|---|
| success | 319.724 | 次の開始まで319.853秒。終了処理と独立照合を含む上限 |
| fail-before-admit | 378.651 | 次の開始まで378.766秒。同上 |
| expired-predecessor-fail-before-admit | 358.422 | 次の開始まで358.546秒。同上 |
| fail-after-admit | 389.621 | 次の開始まで389.749秒。同上 |
| crash-after-admit | 374.444 | 次の開始まで374.557秒。同上 |
| expired-predecessor | 360.194 | 未確認。次の開始までの809.270秒を実行時間とは断定しない |
| recovery-units-active | 414.333 | 未確認。スリープを除外した値 |

初回集計の2596.222秒もmonotonic値であり、実際の全体所要時間とは扱わない。品質台帳では後半2件の成功数・成功率を空欄とし、`audit.coverage_gap`で時間の未検証を残した。機能シナリオ自体の成功と、時間を含めた採用判断を分ける。

## 影響した2件の再確認

永続的な電源設定を変えず、最大3時間の一時的なスリープ防止を起動し、有効状態を読み取った。計測ラッパーは壁時計とmonotonicの両方で600秒を上限とし、超過時には対象のprocess groupだけを終了して回収を確認する。最終ソースのcleanと全資源回収も合格条件に含めた。独立レビューの後、同じ統合ソースで影響した2件だけを新しく実行した。

| シナリオ | 壁時計秒 | monotonic秒 | 結果 |
|---|---:|---:|---|
| expired-predecessor | 317.882 | 317.909 | 期待する終端・独立回収確認とも成功 |
| recovery-units-active | 357.803 | 357.809 | 同上 |

2件全体の壁時計は675.922秒。最終ソースはclean、全専用資源の回収を確認した。初回5件とこの新しい2件で、正確な統合ソースの全7シナリオと各600秒以内を確認できた。ただし、これらを連続した1回の全体時間へ合成しない。[#379](https://github.com/AtsushiHosaka/pals/issues/379)の全体10分、自動検査、本物のオーナーを使う予行という課題は未達のまま残す。

本記録の検査ではモデルを呼び出していない。ローカル有料取得3回目と、新しい候補の署名・配置・本番切り替えは未実行である。未有効化候補bc742の配置は[前の記録](seq30-acceptance-provenance-2026-11-14.md)のとおり回収済み。本番受け入れは、この記録を流用せず別に確認する。

## 証跡

生ログは非公開で保持する。下表は対応する集計ファイルのSHA-256であり、本番PASSの受領書ではない。各ケースのログSHA・開始時負荷・回収結果は集計に含む。

| 記録 | SHA-256 |
|---|---|
| 初回7件の元集計 | `9adf51e0294eab05c2d16a23d2c302ac2e0af28f05a6241bfa9e910e7c20de78` |
| 壁時計の未検証を記録した監査 | `71729d308fd15893a52d8c340f7565ce690eb76fccf983a257050cf900a29f68` |
| 影響2件の再確認集計 | `cf1b200bd4bff07f39604c7915a0b62edf81a552651b83cc8b277d6d81a0c7bd` |

進行の正本は[#378](https://github.com/AtsushiHosaka/pals/issues/378)、リリースの親PRは[#394](https://github.com/AtsushiHosaka/pals/pull/394)。
