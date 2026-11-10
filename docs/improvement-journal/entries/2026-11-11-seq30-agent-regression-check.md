# seq30 前の pals-agent 退行確認: 候補 main 000da00 対 本番 worker 427caf8（2026-11-11）

- 指標: 成功率・時間・費用（退行がないことの確認。改善の測定ではない）
- 仮説: 既定経路（フラグはすべてコード既定）で、候補の pals-agent main `000da00` は、本番 worker の版 `427caf8` より悪くない。seq30 を配備する前の確認。
- 変更: コード変更なし。比較だけ。関連: [#318](https://github.com/AtsushiHosaka/pals/issues/318)、[#327](https://github.com/AtsushiHosaka/pals/issues/327)、[#336](https://github.com/AtsushiHosaka/pals/issues/336)。
- 測定の条件:
  - 方式は Tier 2 相当。生成パイプライン全体を、実 `gpt-6.1-terra` medium、実ローカル Lean 4.32.0-rc1 + Mathlib `8b62164` で動かした。Lean は直接のローカル runner で、HTTP 検証器もコンテナも使っていない。
  - 評価セットは `generation-eval-v1` の tuning split から 14 項目。両腕とも同じ項目、各 1 回。2 腕は同じ 1 台で同時に走らせた。修復上限は 6（前回のフラグ測定は 3）。
  - ハーネスは main にしかない。prod 腕では、ハーネスを無変更で本番コードの横に置いた。さらに、ハーネスだけの腕 `default`（`PALS_*` を一切設定しない）を使った。
  - 項目: la_v2_distinct_eigenspaces_intersection、calculus_v5_derivative_difference_quotient_limit、seed-absolute_value_not_differentiable、la_reuse_kernel_detects_zero、pq-bounded-monotone-real-sequence-convergence、pq-prime-above-every-bound、mv_foundation_exceptional_section_counterexample、seed-quadratic_not_injective、disc_size_difference_closed、scheme-M13、scheme-M10、pq-compact-hausdorff-continuous-bijection-inverse、rat_adjacent_partial_fractions、seed-rank_nullity。
  - 実行日: 2026-11-11（JST）。

## 結果

| 指標 | prod `427caf8` | main `000da00` |
|---|---:|---:|
| 最終成功 | 13/14 | 13/14 |
| 初回コンパイル成功 | 5/14 | 8/14 |
| 修復の合計 | 14 | 14 |
| 1 項目の時間 p50 | 92.6 秒 | 66.4 秒 |
| 1 項目の時間 平均 | 136.2 秒 | 135.3 秒 |
| モデル費用（計測値） | $0.7267 | $0.7283 |
| 入力 token | 187,035 | 194,954 |
| 出力 token | 112,101 | 112,228 |

- 費用は定価で換算した値。キャッシュ入力は割り引いていない（両腕ともキャッシュ token は 0）ので、上側の見積もり。
- 対比較（main − prod、項目を単位にする）:

| 指標 | 差 | 区間・検定 |
|---|---:|---|
| 最終成功 | 0 | 食い違い 0/0 |
| 初回コンパイル成功 | +0.214 | ブートストラップ 95% 区間 +0.000〜+0.429。prod のみ 0、main のみ 3、正確な McNemar p=0.25 |
| 時間 平均 | −0.84 秒 | 区間 −26.3〜+20.5 秒、並べ替え検定 p=0.95 |
| 修復回数/項目 | 0.00 | 区間 −0.36〜+0.36 |
| 費用/項目 | ±0.00 ドル | 区間 −0.01〜+0.01 ドル |

- 検出力: ツールの最小検出差（MDD）は nan と出力した。正確な McNemar 検定を n=14 でシミュレーションすると、検出力は 30 ポイントの差で約 22%、40 ポイントの差で約 51%。つまり、およそ 40 ポイント以上の悪化でなければ検出できなかった。
- 失敗: main だけが失敗して prod が成功した項目はなかった。両腕とも失敗した項目が 1 つあり、mv_foundation_exceptional_section_counterexample が 6 回の修復後に `repair_budget_exhausted` で終わった。前回の実行でも、この項目は両腕とも失敗している。
- 失敗した Lean 検査の件数（診断コード別）。attempt ごとの正規化は未確認:

| コード | main | prod |
|---|---:|---:|
| unknownIdentifier | 4 | 2 |
| synthInstanceFailed | 5 | 2 |
| 一般の lean.error | 10 | 8 |

  main は、最終的には成功した 3 項目で、修復を 1 回多く使った。
- #327 に挙がった既定経路の差 9 件のうち、この測定が触れた範囲:

| 区分 | 項目 |
|---|---|
| 通った | #6 クライアントの再試行（全呼び出しで通る経路。再試行が実際に起きたかは未確認）、#9 観測のみ |
| 到達可能だが発火せず | #5 事前検査 `pals.target_declaration_invalid`（0 件） |
| 通っていない | #1 説明 writer のプロンプト、#2 説明 reviewer のプロンプト、#3 Recipe と chat 回答のプロンプト、#4 Recipe の意味審査、#7 候補のポーリング間隔、#8 検証サーバー TLS の受け渡し |

  生成とコンパイルの範囲だけの確認である。

## 判断

- この標本の大きさでは、退行は検出されなかった。
- ただし根拠は弱い。上の検出力のとおり、約 40 ポイント未満の悪化は見えない。リリース前のローカル適格性確認の代わりにはならず、通っていない 6 件の差は未測定のまま残る。
- 回答時間の目標（[#137](https://github.com/AtsushiHosaka/pals/issues/137)、学部レベルで 30 秒以内）に対して、1 項目の時間 p50 はここで 66〜93 秒。どちらの版も目標に近くない。

## 費用

- 合計は約 $1.455（$0.7267 + $0.7283）。各腕とも 1 回あたりの上限 $1 の内。定価換算の上側の見積もりで、請求額ではない。

## 限界・未確認

- n=14、各 1 回。検出できるのは大きな悪化だけ。
- 初回コンパイル成功の +3 項目は、区間の下端が 0 で、McNemar も p=0.25。改善とは言わない。
- 2 腕は同じ 1 台で同時に走らせた。負荷は共有したが、腕ごとの時間への影響は未確認。
- 修復上限は 6。前回のフラグ測定の 3 とは違うので、数字を並べない。
- 通っていない 6 件の差（説明・Recipe・意味審査・ポーリング・TLS）は未測定。
- 生データは作者のマシンにだけあり、リポジトリには共有していない（Lean 本文と Draft 本文は含まない）。

## 次にやること

- リリース前のローカル適格性確認で見る。この測定の代わりにはしない。

## 出典

- [#318](https://github.com/AtsushiHosaka/pals/issues/318)、[#327](https://github.com/AtsushiHosaka/pals/issues/327)、[#336](https://github.com/AtsushiHosaka/pals/issues/336)、[#137](https://github.com/AtsushiHosaka/pals/issues/137)。
- 台帳の行: `2026-11-11-seq30-agent-regression-prod-427caf8`、`2026-11-11-seq30-agent-regression-main-000da00`。
- 生データは作者のマシンにだけある（共有していない）。
