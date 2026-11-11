# 生成側の評価セット: 設計

要件は [requirements.md](requirements.md)。実装は pals-agent（PR は #327 に記載）。既存の本番コード（`generator.py`、`worker.py`、`pipeline.py`、`explanations.py`、`lean_verifier/http_server.py`）は**編集しない**。

## 構成

```
pals-agent/
  testdata/generation-eval-v1/
    manifest.json              100 題。文面・層・分割・履歴・共有 ID を持つ（コミット）
    SPLIT.sha256               (id, split, 文面ハッシュ) の SHA-256。変更不可
    codex_shared_problems.json Codex の20題の問い文だけ（参考解答は含めない）と fixture ハッシュ
  scripts/eval/
    build_manifest.py          記録（docs と testdata）から決定的に manifest を作る
    run_eval.py                schedule / witness-replay / tier0 / validate
    compare_runs.py            records.jsonl から腕 A・B を対比較
  pals_agent/evals/
    manifest.py                スキーマ、決定的な分割、チェックサム、検証
    records.py                 閉じたスキーマの追記専用 JSONL
    runner.py                  RecordingVerifier / RecordingGenerator、Tier 0・1・全工程
    analysis.py                題単位の並べ替え検定・対ブートストラップ、対の2値だけの McNemar（正確）、MDE
```

## 問題集合の作り方（`build_manifest.py`）

出典を5つに分け、同じ ID・同じ文面は1回だけ入れる。

| 出典 | 題数 | 難度の根拠 | 備考 |
|---|---:|---|---|
| 型付きカタログのカード（過去の12・24・36枚の測定に出たもの） | 36 | observed（失敗または修復3回以上=hard、1〜2回=medium、0回=easy） | 修復を使い切った7題、命題不一致の履歴9題を含む。文面はカードの `canonical_statement`（問いとしてだけ使う） |
| 要求シード `requested-math-seeds-v1` | 20 | assigned（手動。表は `build_manifest.py`） | 日本語。判定・計算の9題に期待する答えを付ける |
| Codex の題（`pq-` 付き） | 18 | assigned（構造から手動） | 日本語。Codex の登録に難度欄がないため |
| スキーム論の M カード（Mathlib のみ） | 6 | observed（腕 a の結果） | 固定の Lean 命題つき。Frontier を使う F カードは除く |
| 候補カード（高校・大学の問い） | 20 | declared 19（introductory/standard/advanced → easy/medium/hard）。宣言難度のない1題（`number_theory_gcd_dvd_left`）だけ assigned | Lean の証明なし。分野ごとの枠を、題の ID の SHA-256 順に medium → hard → easy の順で回して選ぶ |

難度の根拠の合計は observed 42（36+6）・assigned 39（20+18+1）・declared 19。件数は `manifest.json` の `tier_basis` を数えた値で、[requirements.md](requirements.md) と journal も同じ。

除外: `(x+y)^2` 系（正規表現と ID）、同じ文面の重複。分野・タグは文面と ID から決定的に付ける。

**分割:** (分野, 難度) の層ごとに保留数を 30% の切り捨てとし、合計が `round(0.3N)` になるよう端数の大きい層から1題ずつ足す。層内の並びは `sha256(salt:id)`。乱数を使わないので、再計算で同じ結果になり、`SPLIT.sha256` と照合できる。**manifest を作り直して分割が変わるなら、版（`generation-eval-v2`）を上げる。**

## 実行計画（対比較・時間の交互）

`interleaved_schedule(題, 腕, 反復)`: 反復ごとに題を並べ替え、題ごとに2腕を連続させる。腕の順は題の番号と反復で回転し、先に走る腕の偏りを避ける。API の混み具合や Mac の負荷が一方の腕にだけ当たる交絡（2026-11-09 の保留24枚で起きたもの）を防ぐのが目的。

## 記録のスキーマ（追記専用 JSONL、閉じている）

- `pals.generation-eval.attempt.v1`: 1回の段。`stage`（draft / sketch / sketch_check / prove / lean_check / repair / replay_check）、`started_at`・`ended_at`・`elapsed_ms`、`success`、`error_codes`、`model`・`effort`、`input_tokens`・`cached_input_tokens`・`output_tokens`、`diagnostics`（コード・行・メッセージの SHA-256、5件まで。**コンパイラのメッセージ本文は JSONL に入れない**。Lean の診断は問題の項や識別子を含みうるため。本文は失敗した Lean と同じく `<artifacts>/` 側にだけ置く）、失敗時は `lean_sha256` と `lean_path`。**Lean 本文は JSONL に入れず、`<artifacts>/<run_id>/<題>/<n>.lean` に保存**する（既知の欠落: 失敗した Sketch の本文が残らない）。**実装との差（未修正）:** pals-agent の `runner.py` の `_diagnostic_summary` は、いまメッセージ本文を300字まで `diagnostics` に書いている。R10 と合わせるには、本文を落とすか SHA-256 に置き換える修正が要る。
- `pals.generation-eval.run.v1`: 1回の (題, 腕, 反復)。`tier`、`split`、`success`、`first_attempt_ok`、`repairs_used`、`wall_s`、`cost_usd`、`model_calls`、トークン合計、`termination_reason`、`config`（モデル・推論量・フラグ）、`error`。
- 未知のフィールドは書き込みで拒否する（問題文・秘密・利用者内容の混入を防ぐ）。`error` が立った行（検証器の異常、API 失敗）は比較から除き、除いた数を報告する（失敗として数えない）。
- 保存先: 既定でリポジトリの外（`PALS_EVAL_ARTIFACTS`、例 `~/.local/share/pals-eval/<run_id>/`）。コミットするのは集計（docs）だけ。

**取得方法（編集しない）:** `RecordingVerifier` が `ProofPipeline` に渡す検証器を包み、`verify`・`verify_sketch` ごとに時間・エラーコード・失敗した Lean を記録する（`hint_ab.py` の `SketchRecorder` と同じ手法）。`RecordingGenerator` は `generate`・`repair` の戻り値が既に持つ `elapsed_ms`、`model`、`reasoning_effort` から draft / sketch / prove の行を作る（段の開始時刻は段を並べた導出値）。トークンは `usage.usage_scope`。

## Tier の実装

- **Tier 0** `run_tier0`: `{problem_id, lean_code}` を検証器に通すだけ。モデル呼び出し0。検証器・決定的な変換・修復規則の変更を、同じ入力に対する前後で比べる。入力は保存した出力、または `witness-replay` が作る**カタログの証明（モデルの出力ではない）**。後者は「検証器が既知の正しい証明を通すか」の確認で、生成の成功率ではない。
- **Tier 1** `run_tier1`: 保存した Draft（`{problem_id: draft 文}`）から `generate_sketch` を呼び、`verify_sketch`（`sorry` 許容）でコンパイル。費用は見積もりで記録（定価、キャッシュ値引きなし=上限）。単価不明のモデルは `cost_usd=null`（0 にしない）。
- **Tier 2・3** `run_pipeline_once`: 呼び出し側が組んだ `ProofPipeline`（Recording 付き）を1回走らせ、`result.json` から初回の検査結果・修復回数・終了理由を読む。キー（`OPENAI_API_KEY`）がなければ動かさない。このセッションでは**未実行**。
- 必要な最小フック（**編集はしない**）: 段ごとの開始時刻とトークンを `pipeline.py` が `usage_scope` と一緒に出せば、導出値が実測になる。必要になったら別 PR で相談する。

## 分析（`analysis.compare`）

1. 題と反復番号で腕 A・B の行を対にする。`error` のある行は除く。反復番号が**両腕に揃っている**ものだけを使い、題ごとにその反復を平均する。片腕にしかない反復（例: A は反復1・2、B は反復2が `error` → 使うのは反復1だけ）は平均に入れず、除いた対の数を腕ごとに報告する。揃った反復が1つもない題は分析から外し、外した題の数を報告する。
   **実装との差（未修正）:** `analysis.compare` の `per_problem_means` は、腕ごとに `error` のない行を題ごとに別々に平均してから、両腕にある題の差を取る。反復番号は合わせないので、上の例では A=[1,0] の平均 0.5 と B=[1] の 1.0 の差 +0.5 が出る（対になる反復1は差0）。`error` 行の除外と McNemar の反復番号ごとの対（`_binary_cells`）は実装済みだが、主解析の平均は対になっていない。直すまで、反復に `error` が混じる比較では主解析を使わない。
2. 指標: `first_attempt_ok`、`success`、`repairs_used`、`wall_s`、`cost_usd`。差は B − A。二値指標も、題ごとの反復平均（0.5 のような値）の差を主解析にする。
3. 全指標に、題をクラスタにした**符号反転の並べ替え検定**（非ゼロの題が16以下は全列挙、超えれば種固定のモンテカルロ）と、題を単位とする対ブートストラップの 95% 区間（1万回、固定の種）。
   McNemar は対になった2値にだけ使う: 反復が全題1回のときに全体で1回、複数反復のときは「A の r 回目と B の r 回目」を対にして反復番号ごとに別々に出す（プールしない。平均した値には使わない）。主な判定は並べ替え検定と区間で行い、McNemar は補助。
4. 区間が 0 をまたぐ指標は「効果は確認できない」。報告に MDE を添える（`mde_binary`、`mde_continuous`）。MDE は検出力 80%（両側5%）となる真の差で、それより小さい差も有意になりうるが、検出力は 80% を下回る。
5. 複数の指標・複数の分野を見るときは、見た数を書く（多重比較の補正はしない。見た指標を事前に1つ決める）。

## 台帳・失敗分類への対応

台帳の1行は (腕, 層, 分割) の集計。`family=proof_generation`、`dataset=generation-eval-v1 tuning(70)` のように分割まで書く。`n` は試行数、`failures_json` は次の対応で taxonomy のコードにする。

| 記録の `error_codes` / `termination_reason` | taxonomy |
|---|---|
| `lean.error` 他の Lean 診断 | `verifier.lean_compile_error` |
| `lean.formal_harness_mismatch` | `verifier.formal_harness_mismatch` |
| `lean.statement_mismatch` | `verifier.statement_mismatch` |
| 時間切れ | `infra.timeout` |
| 上記以外で原因が記録にない | `unclassified`（推測で選ばない） |

## Codex の評価との接続

- 共有題 18 は `pq-<id>` と `shared.{prompt_quality_id, case_id, fixture_sha256}` を持つ。Codex の `fixture_sha256` が変わったら（問題文の改訂）、`codex_shared_problems.json` との照合テストが落ちる。
- Codex の分割名（tuning / regression / prospective_holdout）は**別の意味**（説明の調整・開封済み）。この評価の `split`（tuning / held_out）とは独立に持つ。共有題 18 の割り当ては 調整14・保留4。
- 結合して見たいもの（生成が成功した題で、説明が届き QA を通る率）は、別ファイル `user_level` に置く。v1 のランナーは書かない（説明と QA の実行は Codex の側が持つ）。
- 結合の鍵は `(題の ID, 実行 ID, 証明の SHA-256)`。Codex の説明の再生は固定の検証済み証明を入力に使うため、題の ID と実行 ID だけでは、生成が出した証明と別の証明の説明が結びつきうる。`user_level` の行は説明に渡した Lean の SHA-256 を持ち、その実行の最終証明の SHA-256 と一致した行だけを利用者側の指標に使う。一致しない行と証明を持たない実行は指標から除き、その数を報告する。
- **実装との差（未修正）:** run 行は最終証明の SHA-256 を持たない（`lean_sha256` は失敗した試行の行だけ）。成功した実行の最終証明の SHA-256 を run 行に足すまで、結合は定義だけで使えない。

## 検証

`tests/unit/test_generation_eval_{manifest,analysis,runner}.py`（計34件）: 一意 ID、層の件数、保留の固定チェックサム（分割や文面の改ざんで落ちる）、禁止題材、共有題と Codex の記録の一致、並べ替え検定の既知値と全列挙・モンテカルロの一致、分数の結果で McNemar を使わないこと、反復2回の偽陽性率、MDE と検出力のシミュレーション、実行計画の交互性、記録の閉じたスキーマ、Tier 0・1 の記録。
