# 段階的 Draft-Sketch-Prove レーン（`PALS_DSP_STEPWISE_ENABLED`、既定 off）

実装: `pals_agent/dsp_stepwise.py`。`pipeline.py` のフックは `_generate_staged_attempt` の先頭の8行だけ。

## 動き

1. **Sketch**: 固定の定理文（`statement_template.assemble` がシステム側で挿入するので、モデルは書き換えられない）に、名前付きの `have h : <主張> := by sorry` と最後にまとめる tactic を並べる。骨格を Lean で先に検査する（`sorry` の警告だけなら通る）。通らなければ修復を1回（`SKELETON_MAX_REPAIRS`）、それでも通らなければレーンを諦めて通常経路へ。
2. **Stage 0**: 各ステップを固定の自動化ポートフォリオ（`simp`、`norm_num`、`linarith`、`positivity`、`gcongr`、`nlinarith`、`aesop`。各候補は `; done` で閉じ切るものだけ）で試す。モデル呼び出しなし。1ステップ1コンパイル、`maxHeartbeats 40000` で打ち切る（返す証明には `set_option` を残さない）。`main` に Mathlib 自動化ポートフォリオ相当のモジュールはなかったので、固定リストにした。`exact?` は遅く非決定的なので入れていない。
3. **モデルのステップ**: 閉じなかったステップごとに1回、並列に呼ぶ。各呼び出しは、その手前までの骨格（前のステップは主張だけで証明は見せない）だけを受け取る。結果は「他のステップは `sorry` のまま」の骨格で、ステップごとに独立にコンパイルする。通ったステップは凍結し、再生成しない。落ちたステップだけを `STEP_MAX_REPAIRS`（2）回まで修復する。修復プロンプトが見る失敗は `sanitised_failure_brief` の整形済み要約だけで、Lean の生メッセージは渡さない（テストあり）。
4. **再スケッチ**: ステップが残ったら1回だけ許す。主張が変わらない凍結ステップは証明を引き継ぎ、コンパイル1回で再確認する（モデル呼び出しなし）。主張が変わらないまま失敗したステップは再挑戦しない。
5. **組み立て**: 全ステップの証明を入れた1ファイルを返す。それを通常のパイプラインがゼロから1回のコンパイルで検査し、固定の定理文・`sorry`/`axiom` なしを確認する。数えるのはこの結果だけ。ステップが残ったときはレーンが `None` を返し、通常経路（Draft→Sketch→Prove）が動く。組み立てたファイルが落ちたときは、通常の修復ループがそのファイルから始まる。

Draft はこのレーンでは作らない（Draft を挟むと約10〜14 s 増える）。必要なら骨格のプロンプトに Draft を足せる。

## ステップが最上位の補助補題を必要とするとき

ステップの証明は tactic ブロックで、ブロック内の局所補題（`have key : ∀ x, … := by …`）は使える。トップレベルの `lemma`／`theorem`／`def`／`axiom`／`set_option` は拒否する（`step_proof_rejection`）。理由: ワーカーは最上位の対象宣言が1つであることを要求し（`require_single_target`）、補助宣言を許すと定理文の固定と信頼範囲の検査を弱めるため。長い補助補題が要るステップは、Sketch／再スケッチで一般形の主張を独立したステップとして書かせる。報告された問題のステップ2（約35行の補題）は、局所 `have key : ∀ (Y : Ω → ℝ), … := by …` としてそのまま入る（実 Lean で確認済み、PR 本文）。

## 会計

モデル呼び出しとコンパイルは、行った時点で数える（例外で落ちた呼び出しも、後で捨てたステップも）。`StepwiseResult.counts`（種別ごと）、`timings`（`sketch_s`、`skeleton_check_s`、`stage0_s`、`steps_s`、`resketch_s`、`total_s`）、ステップごとの `model_calls`／`compiles`／`seconds`。使用量（トークン）は通常どおり `usage_scope` に流れる（ワーカースレッドへは `copy_context` で渡す）。`run_stages.py` の `stepwise` 腕は、`stepwise.jsonl` に1回ごとの `detail()`（ステップの主張つき。忠実さを読んで判定するため。利用者向けではない）を書く。

## 利用者向けの途中経過（この PR では何も返さない）

`StepwiseResult.progress()` は `[{"name", "status", "verified"}]`（構造だけ。主張も証明も含まない）を返す。ワーカーの返り値は変えていない。
