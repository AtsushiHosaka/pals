# 大学基礎 100 章：次に埋める 70 章

2026-09-30 時点。今回の **30/30 は線形代数・一変数微積分・多変数微積分の各 10 章について、固定された最低演習枠を満たした**という意味である。100 章全体、全教科書の演習、検索・再利用の実行成功を意味しない。30 章にも、一般曲面の Stokes 定理など最低枠だけでは保証されない内容が残る。

分母は [coverage matrix](../specs/draft-catalog-expansion/coverage-matrix.v1.json) の `undergraduate-core-v1`。これは PALS の参考カリキュラムであり、特定の数学書の全演習一覧ではない。各章の要件は recognize / compute_construct / justify_prove / counterexample_audit / synthesize 各 1 枠、難度は introductory 1・standard 2・advanced 1 枠。mode と難度は同じカードを別軸で評価するので、両者の分母を合算して必要カード数にしない。

## 70 章の現在値

現行 matrix と `audit-draft-catalog-coverage.py --format json` を再照合した。下表は **旧監査が対応付けから数える authored 枠**であり、今回の 30 章と同じ独立内容審査・証拠固定を済ませた数ではない。0 は未対応付けであり、Draft が 0 件という意味ではない。

| 分野 | 章数 | mode 枠 | 難度枠 | 旧監査で両軸充足の章 |
|---|---:|---:|---:|---:|
| 論理・集合・証明の基礎 | 10 | 25/50 | 20/40 | 5/10 ※ |
| 離散数学 | 10 | 0/50 | 0/40 | 0/10 |
| 幾何 | 6 | 0/30 | 0/24 | 0/6 |
| 実解析 | 10 | 0/50 | 0/40 | 0/10 |
| 常微分方程式 | 6 | 0/30 | 0/24 | 0/6 |
| 確率・統計 | 10 | 0/50 | 0/40 | 0/10 |
| 抽象代数 | 10 | 0/50 | 0/40 | 0/10 |
| 数論 | 8 | 0/40 | 0/32 | 0/8 |
| **計** | **70** | **25/350** | **20/280** | **5/70 ※** |

※ 論理・量化・証明法・集合・写像に各 5 件の旧 binding がある。ただし `logic_not_lt_self_real` の「x<x ではない」を advanced / counterexample_audit、`logic_forall_natural_exists_larger` の「n より大きい自然数がある」を advanced / counterexample_audit とする等、内容とラベルの再審査が必要である。したがって **今回の 30 と足して「35/100 検証済み」と報告してはいけない**。残る 65 章は binding が空。旧監査の admission は 0、公開・retrieval は未測定であり、local Draft の存在・Lean authoring 証拠とは別である。

## 既存カードで先に埋められる範囲と、本当の不足

「不足」は今回読んだ catalog の収録命題に対象の一般形が見つからない、または特殊例しかないことを指す。Mathlib に定理がないという判断ではない。既存カードも、型 profile、自然文/XML/Lean、negative、難度を審査してから対応付ける。

| 分野 | 未対応付けだが再利用できる証拠 | 既存のままでは足りない内容／次の一般 Lean 命題 |
|---|---|---|
| 基礎 10 章 | [logic 34 件](logic-proof-methods-set-foundations-candidates.json) の集合演算・量化、[discrete 21 件](discrete-relations-maps-combinatorics-candidates.json) の整数順序。`induction_nat_power_two_bound` は全 n の帰納法例。 | 同値関係と商集合、抽象順序、再帰、有限・可算、反例構成が未充足。**任意写像の核関係が同値関係である／商から像への全単射、単射による有限濃度比較、可算集合の可算和、パラメータ付き量化順序交換の反例**を追加。自然数の個別恒等式だけで帰納原理・再帰を網羅しない。 |
| 離散 10 章 | [有限グラフ 5 件](typed-finite-graph-v1-authoring-manifest.proposal.json)：握手補題、木の辺数、連結性、二部性、Euler trail の奇数次数必要条件。確率 profile の `prob_choose_pascal`・`prob_choose_symmetry` 等は二項係数章へ再利用できる。 | 数え上げ・包除・鳩ノ巣・漸化式は固定集合や 3→2 等の例だけでは不足。**任意有限集合の包除、\|A\|>\|B\| なら A→B に衝突、一般 n の二項定理、任意初期値の線形漸化式解**を先行。経路・木は **連結無閉路と一意単純路の同値**、後に Hall 条件と完全マッチング、彩色の一般上界を追加。 |
| 幾何 6 章 | [複素・ベクトル 8 件](typed-geometry-complex-v1-authoring-manifest.proposal.json) のうち `typed_complex_conjugate_norm_square`、[平面幾何 5 件](typed-plane-geometry-v1-authoring-manifest.proposal.json) の平行・垂直の対称性は一般形。線形 v3 の内積・直交結果も候補。 | 8+5 件の多くは特定座標・特定係数の計算。**異なる任意二点を通る直線の一意性、非共線三点を通る円の一意性、アフィン写像による共線性保存、非零複素数積の偏角加法（mod 2π）、直交変換による距離保存**が必要。一般二次曲線分類・幾何構成の正当性は別に残る。 |
| 実解析 10 章 | [calculus v3](calculus-v3-batch.json) の極限一意性・単調有界収束・級数比較、[v5](calculus-v5-batch.json) の `calculus_v5_compact_interval_uniform_continuity`・平均値定理、連続だが微分不可能な一般反例。**ゼロ収録ではなく、10 章が未対応付け。** | **実 Cauchy 列と収束の同値、上限の特徴付け、閉区間の列コンパクト性、一様収束極限の連続性、M-test、コンパクト距離空間上の一様連続性、連結像の連結性**を追加する。既存 intervalIntegral は Lebesgue/Bochner：Riemann 章には **Darboux 上下和による可積分判定と連続関数の Riemann 可積分性**が別途必要。`Summable` を条件収束も含む通常級数と同一視しない。 |
| ODE 6 章 | [ODE 10 件](typed-ode-v1-authoring-manifest.proposal.json) に任意 C,k の指数解がある。一次・二次方程式の候補には固定係数・sin/cos 等の解の検算が多い。 | **一般係数の積分因子公式＋初期値による一意性、定数係数二階線形方程式の基本解からの全解、局所 Lipschitz 条件下の存在一意性、線形系の行列指数解**を追加。位相図・安定性・数値近似には **Gronwall 評価、Euler 法の大域誤差評価、Lipschitz 欠落による非一意性の一般反例**が必要。「候補解の微分検算」を「すべての解を求めた」に格上げしない。 |
| 確率・統計 10 章 | [probability 10 件](typed-probability-v1-authoring-manifest.proposal.json)：6 件は二項係数、残りは定数の期待値・二項 PMF/両端の式。確率 profile が存在しても確率論 10 章の実質充足ではない。 | **任意有限分割の全確率・正の分母を仮定する Bayes、可積分変数の期待値線形性、独立二乗可積分変数の分散加法、Markov/Chebyshev、不偏標本平均と分散**を優先。連続分布の変数変換、同時分布、LLN/CLT、推定・検定は主要な新規範囲。除外欄の conditional probability 案を採用済み証拠として数えない。 |
| 抽象代数 10 章 | [group/ring 22 件](../pals-agent/testdata/typed-math-v1/group-ring-typical-theorems-authoring-manifest.proposal.json) の一般群・環の計算法、[commalg reuse](commalg-reuse-batch-20260930.json) のイデアル、[modules v2](commalg-modules-v2-batch.json) の商・核・像・因子化、[commalg v3](commalg-v3-batch.json) の有限性・完全列・テンソル。多くは今回の 10 章に未対応付け。 | **群準同型の第一同型定理、Lagrange、軌道安定化群、共役作用の類等式、環商の普遍性、多項式の除法・既約性、体拡大の次数乗法**を基礎章に沿って追加。PID 上有限生成加群の構造定理や有限アーベル群分類は独立課題。Spec/going-up 等の高度な証明が多数あっても、群作用・体拡大の穴を埋めたことにはならない。 |
| 数論 8 章 | [number theory 12 件](typed-number-theory-v1-authoring-manifest.proposal.json) の gcd・整除と `number_theory_bezout_coprime_nat` は再利用可能。ただし 4 件は法 5、17 mod 5、素数 2 などの固定例。 | **任意正整数法の合同演算、gcd を与える一般 Bézout、互いに素な任意法の CRT（存在＋一意性 mod 積）、ax+by=c の可解条件、素因数分解一意性、Euler/Fermat、乗法的算術関数、二次剰余判定**を追加。現 v1 は symbolic modulus を明示的に除外するため、法 5 を一般法として再対応付けせず、新しい型辞書が必要。 |

## 次の作業順

1. **まず対応付けの審査**：実解析の収束・級数・一様連続性、抽象代数のイデアル・商加群、離散数学のグラフ・二項係数を再利用する。これは authoring 数の水増しをせずに未計上を解消できる。
2. **次に一般化の不足**：有限集合の包除・鳩ノ巣、一般法の合同/CRT、一般アフィン・幾何、ODE の係数・初期値を一般化する。具体値を変えたカードの追加はしない。
3. **証明族そのものが薄い章**：確率の期待値/分散/Bayes、ODE の一意性/安定性、解析の Cauchy/一様収束/距離空間、代数の群作用/体拡大へ進む。各章で正規の一般反例カードも作り、negative JSON だけで counterexample 枠を埋めない。
4. **70 章にも今回と同じ厳格監査を展開**：source/profile の固定、構造重複除外、難度の内容審査、Lean exact bundle、OpenMath carrier、証拠 hash を確認する。章名が広い場合は演習類型の細分化も別に必要であり、最低 5 mode の完了だけを「全演習」と呼ばない。

## 証拠の境界

- 30 章の結果は [今回の固定監査](foundation-curriculum-audit-20260930-v6.json) を参照する。authoring / artifact-bound / Lean replay / runtime は別の証拠水準である。
- 本メモは repository の現行 manifest と matrix を読む内容調査。DB の未登録行や実行時検索を新たに照合していない。未測定を 0 成功にも 100% 成功にも変換しない。
- 70 章の数値を計算した matrix SHA256：`d7dcce8c1f7a0f5824dc0fe1e12c01fecb150e6ac5da19fe9728604dcd262dd9`。再現コマンド：`pals-agent/.venv/bin/python pals-scripts/audit-draft-catalog-coverage.py --format json`。共有 matrix・DB・既存証拠ファイルは変更していない。
