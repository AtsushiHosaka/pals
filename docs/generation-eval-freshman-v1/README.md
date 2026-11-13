# 大学1年レベルの評価題 freshman-v1（40題）

高速経路（10秒目標、[pals#137](https://github.com/AtsushiHosaka/pals/issues/137)）を測るための、未使用の題。generation-eval-v1（pals-agent の `testdata/generation-eval-v1`）の `easy` が調整と試走で使い尽くされたため、題だけを足す。モデル呼び出し・カタログのカード追加はしていない。

## 中身

- `manifest.json`: 40題。generation-eval-v1 と同じ項目（`id`・`field`・`tier`・`tier_basis`・`split`・`language`・`statement`・`statement_sha256`・`tags`・`history`）に、`expected_conclusion`（証明すべき主張を自然言語で。忠実さを人が判定するため）、`mathlib_outlook`（Mathlib で述べられる見込み。`direct` 直接 / `lemma-needed` 補題が要る / `awkward` 述べにくい / `unlikely`）、`expected_answer` を加えた。`fixed_lean_statement` は全題 null（Lean の固定文は付けない）。
- `SPLIT.sha256`: (id, split, 文面ハッシュ) の SHA-256。変更不可。
- `build_freshman_set.py`: 題の定義、決定的な分割、検査。`build` は manifest を作り直し、`validate`（既定）は検査だけ。標準ライブラリのみ。
- `test_freshman_set.py`: 検査のテスト（10件。v1 との重複確認はサブモジュールがあるときだけ）。`pals-agent/.venv/bin/python -m pytest docs/generation-eval-freshman-v1`。

## 水準

大学1年の標準的な教科書の演習で、**自明なものからやや難しいものまで幅がある**。generation-eval-v1 の `easy` と同水準とは言えない（medium が17題ある）。補題1つで閉じる一般的な主張の3題（`union-monotone`、`abs-continuous-at-zero`、`set-difference-of-union`）に `trivial: true` を付けた。固定の数値を計算するだけの題（2^10 mod 11、固定データの平均、さいころの目の確率）は、10秒の達成率を計算問題で水増しするため、変数・量化子を含む一般の証明問題（`difference-divides-power-difference`、`deviations-from-mean-sum-to-zero`、`uniform-complement-probability`）に差し替えた。10秒の判定では、`trivial` を除いた集計も併記して、易しい題で達成が水増しされないようにする。

## 忠実さの判定

manifest の `faithfulness_rule` に従う: 期待される結論の主張が定理文として述べられていれば忠実とみなし、題文の証明方法の指定（「定義から」「直接の計算で」「ε-N 論法で」等）は判定に使わない。定式化に自由度がある題（確率、`limit-of-sum`）は、期待される結論に認める形を書いた。

## 内訳

| 区分 | 題数 |
|---|---|
| 分割 | dev_unseen 20 / held_out 20 |
| 難度（すべて assigned） | easy 22 / medium 18 |
| 言語 | ja 20 / en 20 |
| 分野 | calculus-analysis 9、linear-algebra 7、discrete-logic 5、number-theory 5、probability-statistics 5、sequences-limits 5、inequalities 4 |
| Mathlib の見込み | direct 19 / lemma-needed 21 |

分割は (分野, 難度) の層ごとに 50% を held_out にする決定的な関数（塩 `pals-generation-eval-freshman-v1`、順は `sha256(塩:id)`）。generation-eval-v1 の 30% とは別の版・別の塩で、v1 の `SPLIT.sha256` には触れていない。

## 使い方の規則

- **held_out は最終確認専用。誰も調整・探索・試走に使わない。** 開くときは理由を改善ジャーナルに書き、開いた後の題は調整に使わない。
- dev_unseen は作成時点（2026-11-13）でどの調整・評価・試走にも未使用。一度使った題は、その旨を journal に書き、以後は「使用済み」として数える。
- 題は `history` が空（観測なし）。難度は題の構造からの手動割り当てで、実測ではない。

## 重複の確認

題は自分の言葉で書いた標準的な演習。次と照合した。
1. generation-eval-v1 の100題: ID・文面ハッシュ・空白除去した文面が重複しない（テストで固定）。
2. `docs/` と `pals-agent/testdata`・`docs` の JSON にある1834個の文（カタログのカード、候補、要求シード）に対する語の重なり（Jaccard）と、題材ごとのキーワード検索。一致が見つかった4題（1/(n+1)→0、|a+b|≤|a|+|b|、∫₀¹x²、(2n+3)/(n+1) 型の有理式の極限）は別の題に差し替えた。独立レビューで指摘された、同型の ε-N の有理式の題、√3 の無理性（調整に使われた √2 の兄弟）、曖昧な二項分布の期待値、同じ証明の不等式1題も差し替えた。
3. 禁止題材 `(x+y)^2` とその類題は入れていない（正規表現を文面・期待する結論・期待する答えに適用）。

限界: 重なりの確認は語の一致で、意味の一致を全て拾うわけではない。Lean の証明を試していないので、`mathlib_outlook` は見込みで、成立の保証ではない。
