# 一般 Recipe 具体化で届くための一般形の一覧（2026-11-14）

カタログ追加の再開を判断する材料として、評価セット 90 題（tuning 70、dev_unseen 20）について、どの一般形 G があれば一般 Recipe 具体化の経路（モデルなし）で届くかを調べた。カードは作っていない。held_out は読んでいない。

## 条件

- 入力: tuning と dev_unseen の 90 題の形式命題だけ（86 題に形式命題あり、4 題は null）。題文は参照していない。
- 経路: `elaborate(G のソース, 依頼の命題)` が作る `first | exact G _ … | (intros; apply G <;> first | assumption | fun_prop | positivity | (norm_num; done) | linarith | (simp; done)) | …` を、固定版 Lean 4.32.0-rc1（`LeanRunner.from_workspace`）で compile した。合格の判定は、終了コード 0、`error` なし、`#print axioms` に `sorryAx` なし。lane の「結論の種類が同じ Recipe だけ採用する検査」は通していない。
- 題付属（given）の `example (束縛) : P` は、経路に渡すために `∀ 束縛, P` へ機械的に書き換えた。本番の経路が同じ書き換えをするかは未確認。
- 「Luna 由来」は、Luna が作り独立審査を通っただけの命題で、題と同値かは確認していない。
- 一覧の G は、G 単体の compile と、G を使った具体化の compile の両方が通ったもの。Mathlib 名は、G の証明項に使って compile が通ったことで存在を確かめた。

## 結論

- **網羅性の成果に数えられる一般形（2 題以上に届くもの）は 1 個だけで、届くのは 2 題（どちらも tuning、Luna 由来）**。dev_unseen は 0 題。
- 1 題だけに届く G を個別追加として足していくと、実 Lean で確かめた範囲では 35 個の G で 36 題（tuning 28、dev_unseen 8）に届く。ただし、そのうち 28 題は G が題の命題そのもの（恒等の具体化）で、一般から具体への汎化は起きていない。
- 定数を変数にした G から実際に具体化が起きたのは 8 題（tuning 5、dev_unseen 3）。
- 90 題は分野と形がばらばらで、同じ一般形を共有する題がほとんどない。この評価セットでは、一般形のカードを足しても被覆はほぼ題数と同じ数のカードを要する。

## 一覧 1: 定数を変数にした一般形で具体化が起きたもの（8 題）

| # | 一般形 G（Lean 風） | 題数・ID | 学習段階 | Mathlib | 経路で閉じるか | 累積 |
|---|---|---|---|---|---|---|
| 1 | `∀ (n : ℕ) (c a d : ℝ), (n:ℝ) * a^(n-1) - c = d → HasDerivAt (fun x => x^n - c*x) d a` | 2: calc_derivative_cubic_minus_linear, seed-cubic_derivative（ともに命題が Luna 由来） | 初学者向け。べき関数と一次関数の微分だけで示せる | 直接の定理なし。`hasDerivAt_pow`・`HasDerivAt.const_mul`・`HasDerivAt.sub` の合成 | 実 Lean で確認（2 題とも。n=3 と c を単一化で決め、側条件は norm_num） | 2 |
| 2 | `∀ (a b c : ℝ) (n : ℕ), (b^(n+1) - a^(n+1)) / (n+1) = c → ∫ x in a..b, x^n = c` | 1: calc_integral_square_zero_one（Luna 由来）。個別追加 | 初学者向け。べき関数の原始関数と微積分の基本定理 | `integral_pow` を書き換えた形 | 実 Lean で確認 | 3 |
| 3 | (dev_unseen の題に当たる式のため、ここには書かない) | 1: fy1-integral-of-sine-over-half-period（Luna 由来）。個別追加 | 初学者向け。sin の原始関数 | `integral_sin` を書き換えた形 | 実 Lean で確認 | 4 |
| 4 | `∀ (m n : ℤ), Int.gcd m n = 1 → ∃ a b : ℤ, m*a + n*b = 1` | 1: nt_bezout_101_37（Luna 由来）。個別追加 | 初学者向け。ユークリッドの互除法 | `Int.gcd_eq_gcd_ab` から数行 | 実 Lean で確認（側条件の gcd 計算は norm_num） | 5 |
| 5 | (dev_unseen の題に当たる式のため、ここには書かない) | 1: fy1-abs-continuous-at-zero（Luna 由来）。個別追加 | 初学者向け | `Continuous.continuousAt` の直接の言い換え | 実 Lean で確認（側条件は fun_prop） | 6 |
| 6 | `∀ (a b : ℝ), a^2 + b^2 = 1 → (a - b)^2 ≤ 2` | 1: trig_expand_difference_square_le_two（Luna 由来）。個別追加 | 初学者向け。展開と平方の非負性 | 直接の定理なし（nlinarith で証明） | 実 Lean で確認（a, b を sin, cos に単一化し、側条件は simp） | 7 |
| 7 | (dev_unseen の題に当たる式のため、ここには書かない) | 1: fy1-exp-two-x-derivative（Luna 由来）。個別追加 | 初学者向け。合成関数の微分 | `HasDerivAt.exp` と `const_mul` の合成 | 実 Lean で確認 | 8 |

## 一覧 2: G が題の命題そのものになるもの（28 題、すべて個別追加）

形式命題がすでに変数で書かれた定理なので、G は命題と同じ形になる。一般から具体への汎化はなく、網羅性の成果には数えない。すべて G 単体と具体化の両方を実 Lean で確認した。累積は一覧 1 の 8 題からの続き。

| # | G（命題と同形） | 題 ID | 由来 | 学習段階 | Mathlib | 累積 |
|---|---|---|---|---|---|---|
| 8 | `0 < Real.exp x` | exlog_exp_strictly_positive | Luna | 初学者 | `Real.exp_pos` | 9 |
| 9 | `exp (x-y) * exp y = exp x` | exlog_expand_exp_sub_recover | Luna | 初学者 | `Real.exp_add` から 1 行 | 10 |
| 10 | `0 ≤ x^2` | poly_square_nonnegative | Luna | 初学者 | `sq_nonneg` | 11 |
| 11 | `HasDerivAt (fun y => 1/y) (-1/a^2) a`（`a ≠ 0`） | seed-reciprocal_derivative | Luna | 初学者 | `hasDerivAt_inv` から書き換え | 12 |
| 12 | `Continuous (fun x => x^n)` | seed-natural_power_continuous | Luna | 初学者 | `continuous_pow` | 13 |
| 13 | (dev_unseen の題に当たる式のため、ここには書かない) | fy1-reverse-triangle-inequality | Luna | 初学者 | `abs_abs_sub_abs_le_abs_sub` | 14 |
| 14 | (dev_unseen の題に当たる式のため、ここには書かない) | fy1-consecutive-product-even | Luna | 初学者 | `Int.even_mul_succ_self` | 15 |
| 15 | (dev_unseen の題に当たる式のため、ここには書かない) | fy1-geometric-sequence-tends-to-zero | Luna | 初学者 | `tendsto_pow_atTop_nhds_zero_of_abs_lt_one` | 16 |
| 16 | (dev_unseen の題に当たる式のため、ここには書かない) | fy1-limit-of-sum | Luna | 初学者 | `Filter.Tendsto.add` | 17 |
| 17 | (dev_unseen の題に当たる式のため、ここには書かない) | fy1-union-monotone | Luna | 初学者 | `Set.union_subset_union_left` | 18 |
| 18 | 合成が単射なら最初が単射 | seed-composite_injective_implies_first | Luna | 初学者 | `Function.Injective.of_comp` | 19 |
| 19 | 中間値の定理（符号変化） | seed-continuous_endpoint_sign_change_has_root | Luna | 初学者（定理の証明自体は進んだ内容） | `intermediate_value_Icc` | 20 |
| 20 | 導関数が正なら単射 | pq-positive-derivative-injectivity | Luna | 平均値の定理が必要 | `strictMono_of_deriv_pos` | 21 |
| 21 | 任意の N より大きい素数 | pq-prime-above-every-bound | Luna | 初学者 | `Nat.exists_infinite_primes` から 1 行 | 22 |
| 22 | 次元定理 | seed-rank_nullity | Luna | 線形代数 1 年 | `LinearMap.finrank_range_add_finrank_ker` | 23 |
| 23 | 積の行列式 ≠ 0 の同値 | seed-product_determinant_nonzero_iff | Luna | 線形代数 1 年 | `Matrix.det_mul` から 1 行 | 24 |
| 24 | 数列のずらしと極限 | calculus_v3_limit_fixed_shift | given | 初学者 | `Filter.tendsto_add_atTop_iff_nat` | 25 |
| 25 | 極限の順序保存 | calculus_v3_limit_order | given | 初学者 | `le_of_tendsto_of_tendsto'` | 26 |
| 26 | 定数倍の積分可能性と線形性 | calculus_v2_integral_scalar_linearity | given | 初学者 | `IntervalIntegrable.const_mul`, `intervalIntegral.integral_const_mul` | 27 |
| 27 | 曲線との合成の連鎖律 | calculus_v4_curve_chain_rule | given | 多変数 | `HasFDerivAt.comp_hasDerivAt` | 28 |
| 28 | ノルム 2 乗の微分 | calculus_v4_norm_square_chain | given | 多変数・内積空間 | `HasFDerivAt.norm_sq` | 29 |
| 29 | 閉点と極大イデアル | commalg_v4_closed_point_maximal | given | 進んだ（可換環論） | `PrimeSpectrum.isClosed_singleton_iff_isMaximal` | 30 |
| 30 | 完全列の合成は 0 | la_reuse_exact_sequence_zero_composite | given | 線形代数 | `LinearMap.range_le_ker_iff` | 31 |
| 31 | 核が全体 ↔ 零写像 | la_reuse_kernel_detects_zero | given | 線形代数 | `LinearMap.ker_eq_top` | 32 |
| 32 | 合成の表現行列 | la_v5_matrix_of_composition | given | 線形代数 | `LinearMap.toMatrix_comp` | 33 |
| 33 | `det(1+AB) = det(1+BA)` と可逆性 | la_v6_rectangular_determinant_transfer | given | 線形代数（進んだ） | `Matrix.det_one_add_mul_comm` | 34 |
| 34 | 部分空間の和の元 | la_v6_subspace_sum_membership | given | 線形代数 | `Submodule.mem_sup` | 35 |
| 35 | 直積上の可積分性の判定 | mv_v5_absolute_section_criterion | given | 進んだ（測度論） | `MeasureTheory.integrable_prod_iff` | 36 |

経路の引数上限（明示引数 6 個）を超える G は、前提を `→` に移して上限内に収めた（#19、#25、#27）。前提を束縛に書いた形では `elaborate` が「binding count is outside the supported arity」で拒否した。

## 上位の累積と内訳

| 範囲 | 届く題数 | tuning | dev_unseen |
|---|---|---|---|
| 2 題以上に届く G のみ（網羅性の成果） | 2 / 90 | 2 | 0 |
| 一覧 1 の 7 個（具体化が起きるもの） | 8 / 90 | 5 | 3 |
| 一覧 1・2 の上位 10 個 | 11 / 90 | 8 | 3 |
| 上位 20 個 | 21 / 90 | 13 | 8 |
| 一覧 1・2 の全 35 個 | 36 / 90 | 28 | 8 |

一覧 2 の並びは題数に差がない（すべて 1 題）ため、上位 10・20 個の内訳は並べ方で変わる。上の数字は表の並び順で数えた。

## 届かない題の理由別内訳（54 題）

| 理由 | 題数 | tuning | dev_unseen | 題 ID |
|---|---|---|---|---|
| 形式命題がない | 4 | 3 | 1 | pq-absolute-value-nondifferentiability, pq-irrational-square-root-two, seed-right_limit_and_discontinuity, fy1-image-of-intersection |
| 形式命題が偽（Luna 由来。題が否定や判定を問うのに、否定される側を形式化している） | 5 | 5 | 0 | seed-absolute_value_not_differentiable, seed-determinant_nonzero_decision, seed-linear_system_inconsistent, seed-projection_not_injective, seed-tan_one_degree_irrational |
| 経路の構文制約で命題を渡せない | 5 | 4 | 1 | scheme-M03, scheme-M10, scheme-M13, scheme-M16（命題が `open`・`universe` の前置きに依存し、経路は G 側でも `open`・`universe` を拒否する。完全修飾にしても `⟶` 記法が `open CategoryTheory` なしでは構文解析できず失敗した）、fy1-inverse-by-exhibiting（行列リテラルの `;` を経路が拒否） |
| 個別の事実（自然なパラメータ化がない） | 4 | 2 | 2 | disc_size_difference_closed, seed-pi_gt_305, fy1-dependent-consecutive-triples, fy1-three-tosses-two-heads |
| 一般形が題の命題と単一化しない（実 Lean で確認） | 2 | 2 | 0 | poly_square_linear_bound（`two_mul_le_add_sq` の `2*a*b` が `2*x` と合わない）、logic_add_neq_contrapositive_real（`ne_of_apply_ne` の `?f ?x` が `x + z` と高階単一化しない） |
| 複雑・複合で、命題そのもの以外の一般形が決まらない（未試験） | 34 | 26 | 8 | 下記 |

最後の行の題は、命題が正しければ「命題そのもの」を G にすれば届く見込みがあるが、いずれも 1 題専用の個別追加になる。実 Lean では試していない。

- 存在命題・反例構成: calculus_supp_v5_ftc_point_spike_counterexample, mv_foundation_exceptional_section_counterexample, mv_foundation_nondifferentiable_minimum, mv_line_supp_v5_orientation_counterexample
- 連言で複数の主張をまとめたもの: ode_second_exponential_positive_root, ode_separable_zero_solution（後者は自明な命題で、題との同値性も疑わしい）
- Mathlib に直接の定理があるが形が違う、または名前を確認できなかったもの: calculus_v5_derivative_difference_quotient_limit（`hasDerivAt_iff_tendsto_slope_zero` は `t⁻¹ •` と `𝓝[≠] 0` の形）、la_v3_polarization（`inner_eq_sum_norm_sq_div_four` は形が違う）、la_v2_distinct_eigenspaces_intersection（`Module.End.disjoint_eigenspace` は存在しない。代わりの名前は未確認）、pq-distinct-eigenvalues-linear-independence（`Module.End.eigenvectors_linearIndependent` は存在するが形が違う）、pq-compact-hausdorff-continuous-bijection-inverse（`Continuous.homeoOfEquivCompactToT2`）、pq-coprime-moduli-unique-residue-solution（`Nat.chineseRemainder`）、pq-bounded-monotone-real-sequence-convergence（`tendsto_atTop_ciSup`）、pq-prime-order-group-nonidentity-generator（`zpowers_eq_top_of_prime_card`）、trig_expand_tan_square_plus_one（`Real.inv_one_add_tan_sq` は形が違う）
- 定理として個別に示すもの（Mathlib の直接の名前は未確認）: calculus_v4_gradient_direction_bound, la_v6_basis_recognition, la_v6_fredholm_solvability, pq-continuous-interval-self-map-fixed-point, pq-idempotent-linear-map-unique-decomposition, pq-real-sequence-limit-uniqueness, pq-real-square-continuity, pq-sum-of-first-n-integers, rat_adjacent_partial_fractions, coord_quarter_turn_orthogonal_components, seed-quadratic_not_injective
- dev_unseen: fy1-alternating-over-n-tends-to-zero, fy1-arctan-lipschitz（`Real.lipschitzWith_arctan` は存在しない）, fy1-coprime-sum-and-product, fy1-cube-minus-self-divisible-by-six, fy1-deviations-from-mean-sum-to-zero, fy1-factorial-dominates-power-of-two（`Nat.two_pow_pred_le_factorial` は存在しない）, fy1-idempotent-eigenvalues, fy1-independent-union-probability（`μ(A∪B) = a + b - ab` 型のパラメータ化は候補だが、ENNReal の減算があり未試験）

## 試して失敗した一般形

- `∀ f d a, DifferentiableAt ℝ f a → deriv f a = d → HasDerivAt f d a`（微分の 4 題をまとめる狙い）: 側条件の `deriv (fun x => x^3 - 2*x) a = …` を閉じ道具（simp・norm_num）が計算できず、4 題すべて不合格。微分の題は、関数の形ごとに別の G（一覧 1 の #1・#7、一覧 2 の #11）が必要だった。
- 結論の頭が `∧` の題と `↔` の題は、G がその題の命題そのものになる。

## 限界・未確認

- 一覧 1 の 8 題と一覧 2 の Luna 由来 16 題は、形式命題が題と同値かを確認していない。届いても、題に答えたことにはならない可能性がある。
- 実行時間は 6 並列・負荷平均 約 5 で 1 回あたり 5〜16 秒だった。単独の値ではない。
- lane の結論種別の検査と、本番の given 命題の書き換え（`example` から `∀`）は通していない。
- 1 題だけに届く G も、評価セットの外の題には届く可能性がある（例: `integral_pow` 型は他の区間・次数に届く）。この一覧は 90 題の中での被覆だけを数えている。
