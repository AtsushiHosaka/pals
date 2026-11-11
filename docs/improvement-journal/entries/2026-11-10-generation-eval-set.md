# 生成側の評価セット（約100題）と Tier 0 の動作確認（2026-11-10）

- 指標: 成功率・時間・費用を、偶然と区別して比べられるようにする（測定の道具。改善そのものではない）。
- 仮説: 12〜36 枚・各1回・日ごとに別のベースでは、10/12 と 11/12 を区別できない。固定の層化した題集合、対比較、1試行ごとの記録、MDE の併記があれば、判定できる差とできない差を分けられる。
- 変更: 新規のみ。parent の `specs/generation-eval/`（棚卸し・要件・設計）、pals-agent の `pals_agent/evals/`、`scripts/eval/`、`testdata/generation-eval-v1/`（100題、調整70・保留30）。既存の本番コードは編集していない。モデルは呼んでいない。
- 測定の条件（Tier 0 の動作確認だけ）: モデルなし。カタログの証明3件（`calculus_v3_limit_sum`、`calculus_v5_convex_derivative_monotone`、`la_v5_matrix_of_composition`、モデルの出力ではなくカタログの証人）を、固定した Lean 4.32.0-rc1 と Mathlib `8b62164` で `LeanVerifier` に通した。開発 Mac、1回ずつ、2026-11-10。
- 結果: 3/3 が検証を通過。実時間 40.1・19.9・47.5 秒（Mathlib を毎回 import する冷えた実行で、他のセッションの負荷を含む。秒数は相対比較に使わない）。記録は attempt 3行・run 3行の JSONL（閉じたスキーマ）。
- 判断: 採用（道具として）。この確認は、検証器が既知の正しい証明を通すことを示すだけで、生成の成功率の根拠ではない。
- 費用: 0。
- 限界・未確認: Tier 1 と全工程（Tier 2・3）は実行していない（キーなし・予算の規則）。段ごとの開始時刻は、段を並べた導出値。難度は observed 42・assigned 39・declared 19 で、assigned は手動。高校の分野は2題ずつで、保留に入らない分野がある。
- 次にやること: Tier 1 を12題で試す（約US$0.2〜0.9）。Tier 3 の予算と保留の開け方をオーナーが決める（要件の決定事項 D1〜D4）。
- 出典: `specs/generation-eval/*`、pals-agent の `claude/generation-eval-set`、台帳の行 `2026-11-10-generation-eval-tier0-witness-demo`、umbrella Issue #327。
