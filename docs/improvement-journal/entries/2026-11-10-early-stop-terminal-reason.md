# 早期停止の専用終了理由と、本番で有効化できない理由（2026-11-10）

- 指標: 時間・費用（失敗する実行が時間の大半と費用の約3分の2を占める）
- 仮説: 繰り返す `statement_mismatch` / `formal_harness_mismatch` で修復ループを止めると、行き詰まった実行の時間と費用を減らせる。ただし、本番で有効にするには、停止を専用の終了理由として区別でき、誤停止を後から数えられる必要がある。
- 変更: pals-agent PR #91（merge commit `3010c8cb`、既定はすべて off）。
  - 専用の終了理由 `repair_stopped_repeated_statement_mismatch`、診断コード `pals.repair_stopped_repeated_statement_mismatch`、source `repair_early_stop`。
  - 修復予算を使い切る回は、2回連続の不一致でも `repair_budget_exhausted` のままにする（停止は予算が残るときだけ）。
  - result.json に `early_stop`（規則・窓・停止時の試行・残り回数）。品質イベント `repair_early_stop`（メトリクス `RepairEarlyStops`、`RepairEarlyStopsObserved`）。診断コード・回数・窓・`request_hash` だけを持つ。質問・Lean 本文は含まない。
  - 観測のみのフラグ `PALS_OBSERVE_REPEATED_STATEMENT_MISMATCH_ENABLED`（止めずにイベントだけ出す）。連続回数 `PALS_REPEATED_MISMATCH_WINDOW`（2 または 3、既定 2）。
- 測定の条件: 実モデルの測定なし（費用ゼロ）。単体テストと、pals-api の `ProofStatusContext` を実際に実行した契約の確認だけ。
- 結果（発見。測定値ではない）:
  1. #87 と 5a48be1 の既存の停止は、`repair_budget_exhausted` を再利用し、`max_repair_attempts` は設定値のままです。pals-api は `attempt == max_repair_attempts + 1` を要求するため、**このままでは API に拒否され、本番で有効にできません**。
  2. 新しい理由をそのまま送っても拒否されます（`TerminationReason`、`TerminationSource` は閉じた列挙）。#91 は、worker の `_proof_status_context` が API 宛てだけ `repair_budget_exhausted`、source `repair_budget`、`max_repair_attempts = 使った回数` に写します。この形を API が受け付けることは、実行して確認しました。
  3. 本番（`api_reconcile`）では、隔離検証器が API へ返す診断が8個のコードに閉じています。`lean.statement_mismatch` はそこに入らず `lean.compile_error` に畳まれます。そのため、**本番で働く停止は `lean.formal_harness_mismatch` だけ**で、statement_mismatch の停止は働きません。
- 判断: 既定 off のまま採用。有効化は見送り。観測モードで先にデータを集めるのが妥当。
- 誤停止を減らす条件の机上試算（生の試行別コード列は残っておらず、記録済みの27回の結果からの推論。推定）:
  - 連続2回（現行）: 上限6で止まる9回のうち2回（M06、M12）が後で成功。偽の停止は2件とも harness の組で、statement_mismatch の組（M14の2件）は本当に行き詰まっていました。
  - 連続3回: M12 は止まらなくなります。費用の削減は 36% から 28〜30% 程度。既定の修復上限3（最大4試行）では、3回連続は最大でも試行4の1回分しか削れず、削減は 0〜約10%（2回連続は 19%）。
  - statement ハッシュの一致を条件にする案: harness 不一致のメッセージは定数なので判別力がなく、statement_mismatch は本番で見えないため、記録だけでは評価できません。
- 費用: モデル費用ゼロ。
- 限界・未確認: 実モデルでの誤停止率は未測定です。窓3で再開 worker が見る履歴は最大3件なので、4連続以上では同じ job のイベントが重複します。集計は `request_hash` ごとに最初のイベントだけを使います。CI は pals-agent に無く、Codex の指摘1件（観測モードが長い連続を1回ずつ数える）は修正済みです。main では `test_quality_events.py::test_every_lean_diagnostic_code_in_the_package_is_classified` が以前から失敗しています（`lean.frontier_duplicate_definition` が未分類。この変更とは無関係）。
- 次にやること:
  1. pals-api（別リポジトリ）で `TerminationReason` に `repair_stopped_repeated_statement_mismatch`、`TerminationSource` に `repair_early_stop` を足し、検証関係と `docs/api/openapi.json` を更新する。入ったら worker の写像 `_project_early_stop_for_api` を外す。
  2. 検証器・API・worker の3か所を同時に変えて、`statement_mismatch` を診断として通す（リリース系統の変更）。
  3. 観測モード（停止 off）で `RepairEarlyStopsObserved` を集め、`request_hash` で最終結果と突き合わせて、偽の停止率を実測してから、窓2か3を決める。
- 出典: pals-agent PR #91（`3010c8cb`）、#87、`5a48be1`、[offline-savings-analysis](2026-11-10-offline-savings-analysis.md)、[scheme-theory-frontier-measurement-second-budget](2026-11-09-scheme-theory-frontier-measurement-second-budget.md)。
