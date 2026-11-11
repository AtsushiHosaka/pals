# Recipe 具体化の限界の実測（2026-11-10、実 Lean、モデル呼び出し 0 回）

「一般形 Recipe を Lean の単一化に具体化させる」方式（`recipe_instantiation.py` の `exact G _ …`）が、どこまで通り、どの閉じ方と安全検査が要るかを測った。本番コードは変えていない。スクリプトと結果は pals-agent のブランチ `claude/recipe-instantiation-experiment` の `scripts/experiments/recipe_instantiation/`（`results/*.jsonl` が生データ、`summarize.py` が集計）。

## 条件

- Lean 4.32.0-rc1（`~/.elan/toolchains/leanprover--lean4---v4.32.0-rc1`）。Mathlib 8b62164d808cd0f23b7d8cc28190a6c1a1bb483a。メインのチェックアウトにビルド済みの `.lake/packages` を `LEAN_PATH` で参照した（再ビルドなし、`lake` 不使用）。
- Recipe 12 件のライブラリ `PalsRecipes`（`.olean` 化に 21 秒）。既存 10 件（`testdata/` の連続性 ε-δ 5、微分可能性 3、奇数冪の狭義単調 1、`x^2` の ε-δ 1）に、仮定つきの 2 件を ε-δ で書き足した（`recipe_add_continuous_epsilon_delta`: f, g が連続なら f+g が連続、`recipe_const_mul_continuous_epsilon_delta`: f が連続なら c·f が連続。`Continuous.add` 等は使っていない）。
- 文 48 件（正例 38、負例 10）を手で書いた（`statements.py`）。`(x+y)^2` は使っていない。1 文 × 1 closer が 1 回の独立した compile。`sorry`・`native_decide` なし。公理は `propext`・`Classical.choice`・`Quot.sound` だけを合格とした。
- 実行は Lean を 1 回に 1 プロセス。ただし**他のセッションが同時に Lean を動かしており**、開始時の 1 分間 load average は 35、集計時は約 9 だった。時間は参考値。
- closer（各々を別の compile）:
  - (i) 現行 `exact G _ …`（仮定は `(by norm_num)`）
  - (ii) `first | simpa using G _ … | (convert G _ … using 2 <;> norm_num)`（束縛なし）
  - (ii-b) (ii) と同じだが、手で書いた束縛（`2` や `1 (-1)`）を渡す。本番の「提案のヒント」付き経路に相当
  - (iii) 候補 5 件に対する `first | exact R1 … | exact R2 … | …` の 1 compile
  - (iv) `first | apply_rules [候補 5 件, Continuous.continuousAt] | aesop (add safe apply [候補 5 件])`。`Continuous.continuousAt` だけは Recipe ではなく「接着」として許した。
  - (v)（依頼にない追加）束縛つきで `first | exact G b | (convert G b using 1; funext x; ring)`
- 使用定数検査: 各成功で `#print axioms` と、証明項（`pals_recipe_instance._proof_*` などの補助項を辿る）の使用定数を出力した。(a) Recipe G を使うか、(b) `continuous_*`、`Continuous.*`、`differentiable*`、`strictMono*`、`_simp_` 補題などの近道があるかを見る。型名そのもの（`Continuous` など）と接着の `Continuous.continuousAt` は近道に数えない。G を使わないか近道がある成功は、下の表で `S`（近道のみ）と区別する。

## 結果（import 形式、全 262 compile）

記号: `G` = 成功し、Recipe を使い、近道なし。`S` = 成功したが Recipe を使わず近道の補題で閉じた。`×` = 失敗。`-` = 該当なし（仮定つき Recipe には手書きの束縛がない）。

| id | 種別 | i | ii | iib | iii | iv | v |
|---|---|---|---|---|---|---|---|
| P01_x2 | def | G | G | G | G | G | G |
| P02_x3 | def | G | G | G | G | G | G |
| P03_x5 | def | G | G | G | G | G | G |
| P04_3x | def | G | G | G | G | G | G |
| P05_2x1 | def | G | G | G | G | G | G |
| P06_0x5 | def | G | G | G | G | G | G |
| P07_x2_sq | def | G | G | G | G | G | G |
| P08_xx | nondef | × | × | × | × | × | G |
| P09_xm1 | nondef | × | × | × | × | × | G |
| P10_x | nondef | × | × | G | × | × | G |
| P11_negx | nondef | × | × | G | × | × | G |
| P12_xdiv2 | nondef | × | × | × | × | × | G |
| P13_xxx | nondef | × | × | × | × | × | G |
| P14_xp1 | nondef | × | × | G | × | × | G |
| P15_2x_p_x | nondef | × | × | × | × | × | G |
| P16_at_x2 | at | × | × | × | × | G | × |
| P17_at_3x | at | × | × | × | × | G | × |
| P18_x2_p_3x1 | comp | × | × | - | × | G | - |
| P19_x2_3x_1 | comp | × | × | - | × | × | - |
| P20_x3_x2 | comp | × | × | - | × | G | - |
| P21_3x2 | comp | × | × | - | × | G | - |
| P22_x2_plus_x | comp | × | × | - | × | × | - |
| P23_x2_1x | comp | × | × | - | × | G | - |
| P24_x2_x3_x4 | comp | × | × | - | × | G | - |
| P25_2x2_3x3 | comp | × | × | - | × | G | - |
| P26_add_abs | hyp | × | × | - | × | G | - |
| P27_cmul_abs | hyp | × | × | - | × | G | - |
| P28_ff | hyp | × | × | - | × | G | - |
| P29_x2_g | hyp | × | × | - | × | G | - |
| P31_mono_x3 | mono | × | × | G | × | × | G |
| P32_mono_x5 | mono | × | × | G | × | × | G |
| P33_mono_x7 | mono | × | × | G | × | × | G |
| P34_mono_gen | mono | × | × | G | × | G | G |
| P35_d_x3 | diff | G | S | G | G | G | G |
| P36_d_2x1 | diff | G | G | G | G | G | G |
| P37_d_3x | diff | G | G | G | G | G | G |
| P38_d_xx | diff | × | S | S | × | S | G |
| P39_d_xm1 | diff | × | S | S | × | S | G |
| N01_x2_p1 | neg | × | × | × | × | × | × |
| N02_inv | neg | × | × | × | × | × | × |
| N03_mono_x2 | neg | × | × | × | × | × | × |
| N04_abs_cont | neg | × | × | × | × | × | × |
| N05_abs_diff | neg | × | × | × | × | × | × |
| N06_ucont_x2 | neg | × | × | × | × | × | × |
| N07_x2x | neg | × | × | G | × | × | G |
| N08_mono_x4 | neg | × | × | × | × | × | × |
| N09_step | neg | × | × | × | × | × | × |
| N10_x2_p_inv | neg | × | × | - | × | × | - |

### 集計（正例 38 件）

- 現行 (i): 10 件成功、28 件失敗。成功は定義的に一致する例（x²、x³、x⁵、3x、2x+1、0x+5、`x²` を square Recipe で、微分可能性の x³、2x+1、3x）だけ。
- (i) の失敗 28 件に対して:
  - (ii) 束縛なしの simpa/convert: 2 件。2 件とも `S`（Recipe を使わず simp の微分可能性補題で閉じた）。Recipe を使った救済は 0。
  - (ii-b) 束縛つき: 9 件。7 件は Recipe を使い近道なし（`x`、`-x`、`x+1`、x³・x⁵・x⁷ の狭義単調、一般の n）。2 件は `S`（微分可能性の `x*x`、`x-1`）。
  - (iii) 候補 5 件の `first | exact`: 0 件。単一 Recipe の `exact` と同じ結果で、候補を増やしても定義的一致でない文は通らない。
  - (iv) `apply_rules`／`aesop`: 15 件。13 件は Recipe を使い近道なし（合成 6 件、仮定つきの抽象命題 4 件、`ContinuousAt` 2 件、一般の n の単調性 1 件）。2 件は `S`（微分可能性の `x*x`、`x-1`。aesop の simp が閉じた）。
  - (v) 束縛つき＋`funext; ring`: 14 件。**14 件すべて Recipe を使い近道なし**（`x*x`、`x-1`、`x/2`、`x*x*x`、`2x+x`、`x`、`-x`、`x+1`、単調 4 件、微分可能性 `x*x` と `x-1`）。
- Recipe を使い近道なしで救えた件数の和集合（ii-b、iv、v）: **28 件中 26 件**。残る 2 件は `x²+3x+1`（`(x²+3x)+1` と書くため、定数の Recipe がなく、結合順も違う）と `x²+x`（`x` 単独の連続性の Recipe がない）。どちらも、候補にない Recipe が要る正しい失敗。
- (iv) が救えないもの: 奇数冪の指数（`2*?n+1 = 3`、単調性 3 件）、`x*x`・`x-1` 等の定義的でない形（束縛も無いため）。(v) が救えないもの: 合成・仮定つき・`ContinuousAt`（束縛が手書きできない、または `ring` の対象が関数の等式でない）。つまり (iv) と (v) は補完的。

### 負例 10 件

- 9 件は全 closer で失敗した: `x²+1`（純粋な冪 Recipe と候補 5 件では定数が出せない）、`x⁻¹`（偽）、`StrictMono (x^2)`（偽）、`|x|` の連続性（候補になし）、`|x|` の微分可能性（偽）、`UniformContinuous (x^2)`（偽）、`StrictMono (x^4)`（偽）、ステップ関数（偽）、`x²+x⁻¹`（偽）。
- 1 件が通った: `N07 Continuous (fun x => x^2 * x)` を `pow_c 3` で（(ii-b) と (v)）。これは**ラベルの誤り**で、`x^3` は定義的に `x^2 * x` に展開され、真の命題を Recipe G を実際に使って証明している（近道定数なし）。安全上の問題ではない。ただし「負例は 0 件通る」とは言えないので、ここに書く。

## 時間（import 形式 と append 形式）

12 文（x²、x³、3x、2x+1、`x*x`、`x`、`ContinuousAt`、x³+x²、3x²、狭義単調 x³、微分可能性 x³、負例 x²+1）× closer (i)(iib)(iii)(iv)（iib は仮定つき Recipe に無い）の append 形式 46 compile と、同じ 12 文の import 形式再実行 36 compile を比べた。

| closer | import（本実験の最初の実行、中央値） | import（再実行、中央値） | append（中央値） |
|---|---:|---:|---:|
| (i) | 4.0 秒 | 4.5 秒 | 4.8 秒 |
| (iii)（候補 5 件を連結） | 4.3 秒 | 4.3 秒 | 5.2 秒 |
| (iv)（候補 5 件を連結） | 4.2 秒 | 4.6 秒 | 5.2 秒 |

- 判定は全 46 組で import と append が一致した（不一致 0）。
- append は import より中央値で約 0.8〜1.0 秒長い。5 件の Recipe を連結しても 1 秒程度。1 compile の大半は `import Mathlib` の読み込み（約 3〜4 秒）。PIR-014 の「Recipe 全体の再コンパイルで約 10 秒」は、この Mac のこの条件（Recipe が小さい、キャッシュが温かい）では再現せず、Mathlib の読み込みが支配的だった。
- 最大は append で 16〜17 秒（一時的な負荷によるばらつきと見られるが、原因は未調査）。

## 推奨

1. **PIR-006 の緩和は、「closer の追加」と「使用定数検査」を 1 組で行うなら可**。検査なしの緩和は不可。
2. 追加してよい closer: (a) `exact G b`（束縛つき、現行の延長）、(b) 束縛つきの `convert G b using 1; funext x; ring`（(v)。定義的でない 1 変数の関数の等式を閉じる。14 件を近道なしで救った）、(c) Recipe 集合に限定した `apply_rules`（合成と仮定の自動充足。13 件）。この 3 つで 26/28 まで届く。(iii) の候補列挙は効果がなく不要。
3. 入れてはいけない closer: 裸の `simp`／`simpa`／`aesop`。微分可能性の 3 文（P35 は (ii)、P38・P39 は (ii)(iib)(iv)）で、Recipe を使わず Mathlib の補題で閉じた。教育上の制約（未習の定理を使わない）に反する。この実験の連続性の文では近道は出なかったが、38 件では保証にならない。
4. 付ける検査（必須）: 成功した `pals_recipe_instance` の証明項（補助項を辿る）の使用定数に、(a) 選んだ Recipe（または採用した Recipe 集合のどれか）が**含まれる**こと、(b) 近道補題（`continuous_*`、`Continuous.*`、`differentiable*`、`strictMono*`、`_simp_` 等の名前の一覧。許可リストは Recipe 名と接着の `Continuous.continuousAt` だけにする）が**含まれない**こと、(c) 公理が標準の 3 つだけであること。理由: `S` の 3 文は Lean の判定では合格だが、検査なしでは Recipe を使ったと誤って記録される。
5. 検査の限界: 定数の有無は「使った」の必要条件に近いが十分ではない（`have _ := G …` のような使い方が検出できない）。型を合わせて G を実際に適用していること（証明項の根に近い適用）の検査は未実施。名前の一覧はこの実験のものだけで、網羅性は未確認。
6. 今回の実験の範囲外（未実施）: 本番の検証器（mTLS、lake、制限付きの権限）での compile、`PALS_RECIPE_INSTANTIATION` 経路への実装、PIR-011（説明の置換禁止）への影響、独立審査での負例、`ContinuousAt` を Recipe の側で表す方法、cold キャッシュの計時、Recipe を `.olean` として検証器に置く運用。

## 実施していないこと

- cold キャッシュの計時（今回は全て Mathlib のページがメモリに載った状態。唯一の参考値として、最初の動作確認の `import Mathlib` 1 回が 50 秒かかった）。
- import 形式と append 形式を全 48 文×全 closer で比べること（append は 12 文）。
- 負荷を固定した条件での計時（load average は 9〜35 でばらついた）。
- 微分可能性と単調性の合成・仮定つき Recipe（積の微分など）、`UniformContinuous` の文、(x+y)^2 型の文。
- 3 回以上の反復と、時間の区間推定。
