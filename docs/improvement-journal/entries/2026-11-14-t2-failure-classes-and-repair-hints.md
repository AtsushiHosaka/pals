# T2: 初回失敗の種類の再分類と、失敗の種類ごとの修復の指示（効果なし、採用しない）

日付: 2026-11-14 / 担当: T2 レーン / 状態: 測定済み。**この試み（`PALS_T2_REPAIR_HINTS_ENABLED`）は採用しない**。実装は pals-agent の `claude/t2-repair-classes`（PR なし）。前の試みは [t2-30s-late-items-and-cheap-patch](2026-11-14-t2-30s-late-items-and-cheap-patch.md)。

## 利用者にとって何が変わるか
変わりません。30秒以内は dev_unseen 20題で 12〜13/20 のままで、目標の 14/20 に届きませんでした。残りの失敗は、主に「同じ4題が、どの設定でも落ちる」ことだと分かりました。

## 初回失敗の分類（Lean の診断が根拠、cheap-first の6回・33件）
保存済みの第1候補を再コンパイルして、最初のエラーで分けました（dev_unseen 4回と tuning 2回）。

| 種類 | 件数 | 例 |
|---|---|---|
| E: tactic が閉じない・未解決（`exact?` が閉じない、`unsolved goals`、`simp` が進まない、`omega` が足りない） | 15（45%） | `arctan-lipschitz`、`dependent-consecutive-triples`、`consecutive-product-even`、`factorial-dominates-power-of-two` |
| A: 存在しない名前（補題・定数） | 7（21%） | `abs_add`、`intervalIntegral.integral_sin`、`Nat.dvd_sub'` |
| D: 型の不一致・引数・instance | 5（15%） | `HasDerivAt` の関数形が合わない |
| C: 構文 | 5（15%） | `expected no space before`、型の引数の形 |
| その他 | 1 | `rfl` が定義上の等式にならない |
形式化の誤り（命題の意味の誤り）と import の不足は 0 件でした（import は整形で直る分を除いた後の第1候補なので、結果として残らない）。

## 修復2回以上の題は、ほぼ同じ4題
cheap-first の4回（80題・回）で、修復が2回以上かかった 15 件（19%）の題は、`arctan-lipschitz`、`dependent-consecutive-triples`、`exp-two-x-derivative`、`reverse-triangle-inequality` の4題（20題の20%）に集中しています。最初の失敗は、E が2題（`exact?` を残す、未解決の goal）、D が1題、C（構文）が1題です。一方、存在しない名前（A）の題（`limit-of-sum`、`integral-of-sine-over-half-period`）は、1回の patch で通ります。つまり、**名前の存在を確かめる検索の一段は、1回の修復で通る題（17.5%）を速くするものであって、修復2回以上の題（19%）を減らすものではありません**。

## 試み: 失敗の種類ごとの修復の指示
patch の修復プロンプトに、失敗の種類（`failure_brief` の閉じた語彙: 未知の識別子、未解決の goal・tactic の失敗、型の不一致、書き換えの失敗、構文）ごとに、固定の1文（`pals_agent/t2_lane.py` の `REPAIR_HINTS`）を足しました。コンパイラの出力は、文字列として混ぜません（修復モデルは生のコンパイラ出力を読まない設計を保つ）。
- 測定: 保存済みの失敗した第1候補 30 件に、同じ入力で patch を、指示なしと指示ありで1回ずつ（実 Terra、役割の強度）。パッチ後の再コンパイルの成功は **15/30 対 14/30**（両方成功 13、指示なしのみ 2、指示ありのみ 1）。patch の所要は中央値 19.3 秒対 16.6 秒。費用 US$0.448。
- 成功は、題で決まっています（`limit-of-sum` 4/4、`factorial` 2/2、`integral` 3/4 に対して、`reverse-triangle-inequality` 0/4、`arctan-lipschitz` 0〜1/4、`dependent-consecutive-triples` 0〜1/4）。指示では動きません。
- 理由の推測（未検証）: 修復モデルは、残っている goal や未知の名前を見られない設計（サニタイズ済みの要約）なので、種類ごとの一般的な指示だけでは、必要な情報が足りません。この設計は、プロンプト注入を避けるためのもので、変えていません。

## 試み: 異種レース＋patch＋整形（`hetero_fix` の arm）
低 effort と medium の2候補を同時に走らせ、失敗したら保持候補を出し、その後 patch。整形と名前の案内も有効。
| | dev_unseen（2回） | tuning 14題 |
|---|---|---|
| 検証済み | 20/20、20/20 | 13/14 |
| 初回成功 | 12、14 | 12 |
| 30秒以内 | 13、13 | 12 |
| 20秒以内 | 10、11 | 7 |
| 回答完成 p50 / p90 | 21.9 / 89.0、17.8 / 115.7 秒 | 19.6 / 30.0 秒 |
| 修復2回以上（提出3回以上） | 5/20、5/20（25%） | 1/14 |
| 1問の費用 | US$0.0224、0.0217 | 0.0351 |
| 保持候補の成功 | 3/8、1/5 | 1/1 |
- 30秒以内は cheap-first（13、12 / tuning 13）と同じで、20秒以内は少し多く、費用は約1.5〜1.8倍です。採用しません。

## 結論
- 30秒以内は、この構成の範囲では 12〜13/20（約 60〜65%）で頭打ちです。目標の 14/20、修復2回以上の割合 10% 以下は、**未達**です。
- 修復2回以上の割合（19〜25%）は、4題のモデルの力の限界（tactic が閉じない、型の形、構文）で決まっていて、修復プロンプトや候補数では動きませんでした。
- 次の候補（未実施）: (1) 難しい題を事前に判別して初回から強い effort にする（判別の信号が要る。`routine` は未配線）。(2) 修復モデルに残りの goal や名前を見せる（サニタイズ設計の見直しが要り、注入の観点でレビューが要る）。(3) 修復2回目を high effort にする（時間は30秒に収まらない）。
- 実 API・SQS は通していません。held_out は読んでいません。

## 出典（生データ）
この entry の数値は、測定ごとの `records.jsonl`（`steps` に各呼び出しの所要・effort・試行番号、`submits_detail` に提出ごとの成否を持つ）と、保存した失敗候補の再コンパイル結果から集計しました。生データは Lean のソースと定理文を含むため git に入れず、共有ノートの `t2-lane/fix1`、`fix2`、`fix3`、`remeasure3` にあります。集計は `scripts/eval/recheck_first_candidates.py`、`scripts/eval/replay_patch_ab.py`（pals-agent）と、records の集計で行いました。

## 破棄・失敗した測定
- cheap-first の dev20 の取り直し前の1回が API の不通で停止（記録は前のエントリ）。
- 今回の費用: 対比測定 US$0.448、`hetero_fix` の3回 US$1.37（0.449＋0.433＋0.492 の合計、各実行は1回 US$1 以下）。
