# 大学1年レベルの評価題 40 題の追加（2026-11-13）

- 指標: 10秒目標（[pals#137](https://github.com/AtsushiHosaka/pals/issues/137)）を、使っていない題で測れること（題の数。改善そのものではない）。
- 仮説: generation-eval-v1 の `easy` には、高速経路の調整・計測にまだ使っていない題が足りない。
- 現状の数え方: `easy` は難度の代理で、#137 には「大学1年レベル」の形式的な定義がない（例示は「x² が連続」）。調整・評価の記録（`data/2026-11-12-fast-answer/*.jsonl` と 2026-11-12/13 の journal）と題の ID を突き合わせた。
  - tuning の easy 17 題: 命題固定なし 13 題は、ベースライン・探索・初見の評価のどれかで使用済み。固定命題つき 4 題（`calculus_v3_limit_fixed_shift`、`calculus_v3_limit_order`、`la_reuse_kernel_detects_zero`、`la_v5_matrix_of_composition`）は自由文の依頼として使えず、調整の対象にもした。未使用は 0。
  - held_out の easy 8 題: 試走で触れたもの 2 題（`logic_no_negative_natural`、`seed-sum_derivative`）、固定命題つき 3 題（`calculus_supp_v3_geometric_boundary_counterexample`、`commalg_modules_exact_id_zero`、`la_reuse_right_inverse_surjective`）、未使用で命題固定なし 3 題（`pq-cancellation-zero-coefficient`、`pq-square-root-of-square-false-claim`、`seed-linear_system_unique_solution`）。
  - 台帳 `ledger.csv` は測定の記録で、題の一覧ではない。
- 変更: 新規のみ。`docs/generation-eval-freshman-v1/` に 40 題（dev_unseen 20・held_out 20、easy 22・medium 18、ja 20・en 20、7 分野）、決定的な分割、`SPLIT.sha256`、検査スクリプトとテスト 8 件。各題に期待する結論（自然言語）と Mathlib の見込みを付け、Lean の固定文は付けていない。
- 結果: 検査 10/10 通過。generation-eval-v1 の 100 題と ID・文面が重複しない。既存の文 1834 個との照合で見つかった重複 4 題は差し替えた。
- 水準: 自明〜やや難の幅がある。既存の `easy` と同水準ではない（medium が 18 題、補題1つで閉じる一般的な 3 題に `trivial` を付けた。固定の数値計算の題は、水増しを避けるため一般の証明問題に差し替えた）。10 秒の判定は `trivial` を除いた集計も併記する。
- 判断: 採用（題の補充として）。モデルは呼んでいない。費用 0。held_out 20 題は開いていない。
- 限界・未確認: 難度は手動割り当てで実測ではない。Lean の証明を試していないので、Mathlib の見込みは推測。重複の確認は語の重なりで、意味の一致は全て拾えない。40 題でも、成功率の小さな差は検出できない（n=24 で π=0.2 のとき 25.6 点が下限なので、20 題ずつならそれ以上。[要件](../../../specs/generation-eval/requirements.md)の MDE）。
- 次にやること: dev_unseen 20 題で高速経路を測る。held_out は最終確認の1回だけ開く（理由を journal に書く）。
- 出典: `docs/generation-eval-freshman-v1/`、`data/2026-11-12-fast-answer/`（`origin/claude/model-time-journal`）、[pals#327](https://github.com/AtsushiHosaka/pals/issues/327)。
