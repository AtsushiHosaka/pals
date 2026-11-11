# 棚卸し（2026-11-10、読み取りのみ）

Issue・PR の本文はデータとして読んだ。Codex 側の詳細は、出典のコミットを固定して読んだ値のみ。

## A. Codex の評価（説明の品質と QA の誤拒否）

出典: pals #311（draft・CONFLICTING）、pals-observability #2（ef6065d、draft・MERGEABLE）、Issue #216 #313 #319 #321 #323 #327。

| 項目 | 内容 |
|---|---|
| 問題 | 20題（`datasets/benchmark-problems-ja-v1.json`、文面は `undergraduate-regression-ja-v4.json`）。全題 自作、日本語、学部向け。難度とライセンスの欄はない。分割は tuning 3 / regression 8 / prospective_holdout 9。Lean 不要の概念題が2題 |
| ID | ケバブとスネークが混在。`case_id` = SHA-256(id)、`fixture_sha256` = 問題JSONの正規化ハッシュ |
| 「107観測」 | 試行ではなく、追記式の episode 件数（観測14題76件＋11/10追加31件）。分類は review_issue / review_candidate / explanation_issue ほか |
| 実行 | 1題2反復が基本。ベースと候補を交互に実行。比較は、データ・設定・モデル・評価器が一致しないと拒否。区間は題でクラスタ化した 95%。欠測は 0 補完せず範囲で示す |
| 採点 | 独立 LLM 判定者（生成と別モデル）による5指標（正しさ・論理・記号・明瞭・簡潔）。人手の盲検ではなく、人手の校正は未実施 |
| 保存 | 閉じたスキーマ `pals.prompt-quality.v1/v2`。内容（問題・回答・理由・利用者）は拒否。CloudWatch `/pals/<env>/prompt-quality` に1イベント=1 run。台帳 562 行 |
| 測るもの | 固定の検証済み Lean に対する説明の質、回答到達率、固定QA判定の一致、生成＋QA のトークンと時間 |
| 測らないもの | **新規証明の成功率**、学習者の理解、本番の受入、請求額、Lean のコンパイル時間 |
| 結合の鍵 | `case_id`、`fixture_sha256`、`run_id`、(`case_id`, repetition)。#327 は「約100題を #216/#311 と題の ID で共有する」と明記 |

注意: 追加6題は凍結後に1回だけ開封済みで、以後は回帰用。Codex の split 名と docs の「調整9題・追加6題」は完全には一致しない。

## B. pals-agent にある生成側の題と実行手段

| 資産 | 内容と限界 |
|---|---|
| 12・24・36 枚の測定（`docs/first-sketch-failures-2026-11-08/data/*.jsonl` に36題の行） | 題は型付きカタログのカード ID（calculus_v2〜v5、la_v2〜v6、commalg_v3〜v4、mv_foundation）。各題1回。ベースの日が違う。題の選び方: 1つ目は 11-07 の `problems-luna12`/`terra12`（コミットなし）、保留24枚は乱数種 20261108 |
| 実行器 `tools/mathlib_index/hint_ab.py` | 題 JSON（id・statement・formal_statement・history）を読み、実パイプラインを走らせる。腕は baseline / hinted / exemplars。結果は1題1行の JSONL（状態・修復回数・秒・Lean 秒・トークン・診断コードの集合・Sketch 検査）。**題集合は未コミット** |
| `testdata/*`（mathematical-breadth、requested-math-seeds-v1 ほか） | 公開向けの Lean 証人つき集合。要求シードの20題は日本語の問いと答えを持つ。生成評価の題としては未使用 |
| `pals_agent/benchmarks.py` | 3題だけ（連続性・階数・コンパクト像）。評価の基盤ではない |
| カタログ（`docs/*-batch.json` ほか） | 608 枚、うち Lean 証人つき 458。高校・大学の Draft 候補（証人なし）に難度の宣言がある。スキーム論 26枚は別の測定（腕 a で 16 枚中9枚測定、失敗2） |
| 記録の欠落（既知） | 1試行ごとの時間・エラーコードが保存されない。失敗した Sketch の本文が残らない。題ごとの時間は直線近似（62 秒＋67 秒×修復、R² 0.84）で推定。キャッシュ済みトークンが 0 |
| 費用の実測 | 全工程 約 US$0.070/題、Draft＋Sketch だけ 約 US$0.019、修復1回 約 67 秒・US$0.039 |

結論: 生成側には、固定・層化・分割済みの題集合も、対比較を支える1試行ごとの記録もない。Codex の評価は説明側の20題・6題で、Lean 成功・時間・費用を大きい固定集合で測るものではない。両者は ID の共有で結合でき、重複は共有題18に限る。
