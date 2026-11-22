# 大学1年レベルの未使用の題が足りない: 評価集合の棚卸しと、取れた 4 題の測定 (2026-11-13)

- 指標: 時間(10 秒目標)、回答率、忠実さ。大学1年レベルの易しい題で、解説レビュー込みの表示時間を測ること。
- 仮説: 評価集合と台帳に、これまでの調整・評価で使っていない大学1年レベル(`tier=easy`)の題が十分ある。
- 変更: [pals-agent#121](https://github.com/AtsushiHosaka/pals-agent/pull/121)の `run_fast_answer.py` に `--requests-json` を追加。
- 測定の条件: Luna(none、関所 `terse2`、3 並列)、既存の解説レビュー込み、Mac 常駐 Lean、負荷 10 前後、2026-11-13。
- 結果:
  - **足りない。** generation-eval-v1 の `easy` は tuning 17 題 + held_out 5 題(命題固定なし)。tuning の 17 題は、固定命題のある 4 題と、これまでの 2 回の評価(20 題、初見 24 題)ですべて使用済み(調整に使ったこと、初見の 24 題に `pq-real-square-continuity` を含めたこと)。残る未使用は held_out の `easy` 3 題(`pq-cancellation-zero-coefficient`、`pq-square-root-of-square-false-claim`、`seed-linear_system_unique_solution`)で、ほかの 2 題(`logic_no_negative_natural`、`seed-sum_derivative`)は探索の試走で触れている。held_out は最終確認用なので開いていない。台帳(`ledger.csv`)は測定の記録で、題の一覧ではない。`requested-math-seeds-v1` の 20 題は評価集合に全て入っている。題を作り足してはいない。
  - 取れた未使用の題は、`general-recipe-probes-v1` の自然文つきの 4 題(`xの3乗は実数全体で連続`、`x^10 is continuous`、`x^5 is differentiable`、`f(x)=2x+1 は連続`)で、**べき乗・1 次関数の連続・微分の雛形の題**であり、新入生レベルの代表ではなく、自動化が閉じやすい。
  - 4 題の結果: 答えた(解説レビュー込み)は 1/4(`x の 3 乗の連続`、表示まで 10.2 秒、検証済みまで 4.1 秒)。ほかは、解説レビューの却下 1(概要が証明を先取り)、解説の形式が崩れて出せなかった 1、関所の却下 1(2 つの形式化が Lean 上で一致しない、`ContinuousAt` の書き方の差)。解説レビューの前までの表示は 5.0〜7.5 秒。通った 1 件(`Continuous (fun x : ℝ => x ^ 3)`)は忠実。**4 題は回答率・10 秒以内の割合の根拠にはならない。**
- 判断: 大学1年レベルの初見の測定は、題が足りないため**成立しない**。次のいずれかが要る: (a) held_out の `easy` 3 題を最終確認として開く(理由をこの台帳に書く)、(b) 評価集合の担当が新入生レベルの題を追加する。
- 限界・未確認: n=4、雛形の題。
- 次にやること: 上の (a) か (b) の判断。
- 出典: [pals-agent#121](https://github.com/AtsushiHosaka/pals-agent/pull/121)、生データ `data/2026-11-12-fast-answer/probes-unused-nl-4.jsonl`。
