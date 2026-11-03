# 大学数学(学部1〜4年+修士1年)の Draft/Recipe カタログ網羅性分析

対象は `snap/all_cards.json` の 1,881 枚のうち、大学範囲の 1,019 枚である。
`school_*` 全10ファイル、`entrance_exam`、平面・三角形・円・五心の幾何(`geometry_plane/triangle/circle/centers`)の計 862 枚は除いた。
Mathlib は pinned rev `8b62164d`(コミット日 2026-06-24、8,212 ファイル)。宣言名は `Mathlib/` の宣言索引と原文 grep で確認した名前だけを書いた。
記号は ◎=定理あり、△=定義のみまたは部分的、×=全 8,212 ファイルの原文 grep で見当たらず。優先度は S=直ちに追加、A=次点、B=語彙拡張か工数が要る、C=Mathlib 側が未整備。
可換環論・代数幾何の詳細は `gap_commalg_ag.md` にあるので、本書の §7 は要点と参照だけを置き、内容を重複させない。

## 1. 総評

**学部1〜3年の基礎(線形代数・微積分・実解析・位相・群環体・測度・複素解析入門)は看板定理が揃っている。4年〜修士の分野は、カード0枚または1〜6枚の分野が約25ある。**
README の「4年次までの標準命題」は、基礎科目については妥当である。上級科目については成り立たない。

1. **枚数は分野の重要度でなく、ファイルごとの枠で決まっている。** 大学範囲22ファイルは29〜61枚(中央値約50)に収まる。`advanced_undergrad` は Lie 環・表現論・代数的整数論・p進・論理・ホモロジー代数・楕円曲線・解析的整数論の8分野を 31 枚で兼ねる。
2. **大学範囲のカードは level 1〜3 が 857 枚(84%)で、level 4 は 162 枚(16%)である。** level 4 の 115 枚は `commutative_algebra` 36、`functional_analysis` 33、`advanced_undergrad` 29、`field_galois` 17 の4ファイルに集中する。
3. **証明の 75% は4行以下である(中央値2行)。** 大半は `intro` の後に Mathlib の既存定理を `exact` で渡すだけの形で、カタログは「Mathlib が持つ定理の索引」として働く。このため「Mathlib にあるのにカード化されていない領域」が最も安価な穴になる。Brown 運動、分布論、C*環、Lie 理論の根系、導来圏の Ext、特異ホモロジー、計算可能性がこれに当たる。
4. **逆に Mathlib に無い領域は構造的に0枚である。** リーマン曲率・測地線、Sard、素数定理、Hecke 作用素、留数定理・Rouché、Jordan 曲線、Brouwer、Cayley の公式、Cramér–Rao、Euler–Lagrange は、カード作成ではなく Lean 定理の新規開発になる(§8)。
5. 見かけの枚数が多いのに浅い領域は §6 に挙げた。特に `advanced_undergrad`(31 枚中 約15 枚が公理・インスタンスの言い換え)、確率のマルチンゲール3枚(期待値の保存のみ)、多様体6枚(接写像と定義の展開)が目立つ。

実利用の優先順位は §5 の Top25 にまとめた。上位は Fourier 解析の主定理、特殊関数、確率分布と特性関数、初等整数論の定番、マルチンゲール、組合せ論の主要定理群、Ext・群コホモロジー、計算可能性である。

## 2. 方法と注意

- **カウント方法。** 各カードを `_dom` と `topic` の接頭辞(「・」の前)で一次割当てした(重複なし、1,019 枚中 1,006 枚を割当て、残り4枚は有限分布カードで確率論に入れた)。表の枚数はこの値である。
- **キーワード検索は偽陽性が大きく、採用しなかった。** id・topic・target に regex を掛けた結果は、実際の枚数と大きくずれた。グラフ理論は 37(実12。「degree」が体の次数に、「Connected」が位相の連結に当たる)、群論は 166(実57)、位相は 168(実59)、表現論は 10→実5(「character」が標数 `characteristic` に当たる)だった。
- **0枚の主張は、全 1,881 枚の id・target・statement_en に対する次の語の検索で確かめた。** `singularHomology|cohomology|simplicial`、`Ext|Tor|Derived`、`Riemannian|curvature|geodesic`、`RootPairing|killingForm|Cartan`、`Computable|Partrec|Turing|DFA`、`SchwartzMap|Tempered|Sobolev`、`Laplacian|Harmonic`(ヒット6はいずれも調和級数・調和振動子)、`CStar|Gelfand|cfc|GNS`(ヒット1は `gelfand_spectral_radius_formula`)、`Ergodic|Conservative|Birkhoff`、`Brownian|Markov|stoppedValue|upcrossing`、`Hartogs|polydisc`、`Lattice|Heyting|lfp`。
- 「欠けている定理」は、一般形(定数でなく変数で書ける形)で、Mathlib の宣言名が確認できるものだけを挙げた。名前が確認できないものは「×」とした。
- 限界。語彙(OpenMath)側の対応は調べていない。`typed_*` の既存 profile 102 枚(`existing-recipes.tsv`)は別系統として数えていない。同ファイルは解析・線形代数・可換環論・確率の古い実装で、本書の分野表の穴を埋めるものは見当たらなかった。

## 3. level 分布(大学範囲 1,019 枚)

| level | 枚数 | 主なファイル |
|---|---:|---|
| 1 | 220 | calculus_single, linear_basic, real_analysis(前半), logic_sets, combinatorics_graphs |
| 2 | 308 | topology_general, group_theory(前半), multivariable, probability, ring_theory |
| 3 | 329 | measure_integration, complex_analysis, ode, modules_categories, number_theory(後半) |
| 4 | 162 | commutative_algebra 36, functional_analysis 33, advanced_undergrad 29, field_galois 17, modules 10, geometry_homotopy 9 ほか |

## 4. 被覆表

「深さ」は、基礎補題 / 標準定理 / 上級のうち、カードが届いている最上位を書いた。「カード」は §2 の一次割当ての枚数。

### 4.1 代数・数論

| 分野 | カード | 深さ | 欠けている主な標準定理(一般形) | Mathlib | 優 |
|---|---:|---|---|---|---|
| 群論 | 57 | 標準(Sylow, Burnside 補題, A_n 単純, 有限アーベル群) | Jordan–Hölder、Schur–Zassenhaus、Nielsen–Schreier、Burnside 転送、二面体群・四元数群、Frattini | ◎ `CompositionSeries`(Order/JordanHolder)、`exists_right_complement'_of_coprime`(GroupTheory/SchurZassenhaus)、`subgroupIsFreeOfIsFree`、GroupTheory/Transfer、`DihedralGroup`、`QuaternionGroup` | A |
| 環論 | 54 | 標準(PID⇒UFD, Gauss, Eisenstein) | 有限族の CRT・prime avoidance など | §7 参照 | A |
| 体拡大・Galois | 39 | 標準〜上級(基本定理, 原始元, 有限体, 円分, 作図) | Kummer 理論、Hilbert 90、Dedekind の指標独立性、超越基底、素数次既約式の Galois 群、可解性の逆方向 | ◎ `isCyclic_of_isSplittingField_X_pow_sub_C`、`isCyclic_tfae`、`linearIndependent_monoidHom`、`IsTranscendenceBasis`、`Polynomial.Gal.card_of_separable`、`galActionHom_bijective_of_prime_degree`(Complex/Polynomial/Basic)、`solvableByRad`。Artin–Schreier の定理は × | A |
| 初等整数論 | 49 | 標準(Fermat, Euler, Wilson, CRT, 二次剰余, 二平方, Pell) | Lagrange 四平方、ピタゴラス数の分類、LTE、Jacobi 記号と相互法則、連分数、Dirichlet 近似、Lucas の定理、Bernoulli 数と Faulhaber、FLT n=3 | ◎ `Nat.sum_four_squares`、`PythagoreanTriple.coprime_classification`、`Int.emultiplicity_pow_sub_pow`、`jacobiSym.quadratic_reciprocity`、`exists_int_int_abs_mul_sub_le`、`Choose.choose_modEq_choose_mod_mul_choose_div`、`sum_range_pow`、`fermatLastTheoremThree`。完全数は定義のみ(Euclid–Euler は ×) | S |
| 解析的整数論 | 1(+ Bertrand 1) | 標準(Dirichlet の算術級数定理) | Euler 積、ζ(2k)、ζ の関数等式、L(1,χ)≠0、Chebyshev の θ・ψ 評価、素数逆数和の発散、Abel 総和、篩 | ◎ `riemannZeta_eulerProduct`、`hasSum_zeta_nat`、`riemannZeta_one_sub`、`LFunction_ne_zero_of_one_le_re`、`not_summable_one_div_on_primes`、`ArithmeticFunction.vonMangoldt`、NumberTheory/Chebyshev、SelbergSieve。素数定理は × | A |
| 楕円曲線・保型形式 | 1 | 標準(群法則。ただし群の公理4つの言い換え) | Eisenstein 級数の正則性、レベル1・重さ0の保型形式は定数、SL₂(ℤ) の基本領域と生成、Jacobi θ の変換、j 不変量 | △ `eisensteinSeriesSIF_mdifferentiable`、`levelOne_weight_zero_const`、`exists_smul_mem_fd`、`slash_action_generators_SL2Z`、`jacobiTheta`。Hecke 作用素、Hasse の定理、Mordell–Weil は × | B |
| p進・付値 | 5 | 基礎(超距離, 完備性) と Hensel | Ostrowski、ℤ_p のコンパクト性、Witt ベクトル、局所体、アデール | ◎ `equiv_real_or_padic`(NumberTheory/Ostrowski)、`PadicInt.compactSpace`、`WittVector`、`IsNonarchimedeanLocalField`、`AdeleRing` | B |
| 集合論(濃度・順序数・Zorn) | 16 | 標準(Zorn, 整列可能, Cantor, CSB, 可算性) | Cantor 標準形、正則基数、König の定理、#ℝ=𝔠、ZFSet、Hartogs | ◎ `Ordinal.CNF`、`Cardinal.isRegular_succ`、`Cardinal.sum_lt_prod`、`Cardinal.mk_real`、`ZFSet` | A |
| 数理論理・モデル理論 | 3 | 標準(compactness, Löwenheim–Skolem)+β関数 | Łoś の定理、Łoś–Vaught、DLO の完全性、Skolem 化、Fraïssé 極限、Presburger | ◎ `FirstOrder.Language.Ultraproduct.sentence_realize`、`Categorical.isComplete`、`aleph0_categorical_dlo`、`dlo_isComplete`。Presburger は定義のみ | A |
| 計算可能性・オートマトン | 0 | なし | 停止問題の決定不能、Rice、再帰定理、Ackermann は原始再帰でない、DFA のポンピング補題、Myhill–Nerode、正規表現・文脈自由文法 | ◎ `ComputablePred.halting_problem`、`ComputablePred.rice`、`Nat.Partrec.Code.fixed_point`、`not_primrec_ack_self`、`DFA.pumping_lemma`、`Language.leftQuotient`(Computability/MyhillNerode) | S |
| 順序・束・Boole 代数 | 6 | 基礎(最大/極大, 整礎) | Knaster–Tarski、Birkhoff 表現、Heyting 代数と Frame、Stone 双対、Jordan–Hölder の束版 | ◎ `OrderHom.lfp_le`、`supIrredLowerSet`。Stone 双対は △(Topology/Order/Category/FrameAdjunction)。Dilworth は × | B |
| 普遍代数・自由構造 | 0 | なし | 自由群の普遍性、表示群、合同関係と商、Birkhoff の HSP | △ `FreeGroup`、`PresentedGroup`、`Con`。HSP 定理は × | C |
| 線形代数 | 107(基礎56+応用51) | 標準(Cayley–Hamilton, スペクトル定理, Sylvester) | Jordan 標準形、Smith 標準形、有理標準形、Witt の定理、Pfaffian | ◎ `Submodule.smithNormalForm`、`Module.End.exists_isNilpotent_isSemisimple`(Jordan–Chevalley、カードあり)。Jordan 標準形・有理標準形は × | B |
| 多重線形代数・テンソル | 約7 | 基礎(普遍性, 外冪の次元) | Hom–⊗ 随伴、基底変換、対称冪、Clifford 代数、外積代数の普遍性、交代写像と行列式 | ◎ `TensorProduct`、`ExteriorAlgebra`、`CliffordAlgebra`、`SymmetricAlgebra`、`AlternatingMap`。Hodge 作用素は × | B |
| 行列解析 | 2 | 標準(正定値の特徴づけ, Sylvester の慣性) | Schur 補行列、Gershgorin、Hadamard 積の半正定値、特異値、Birkhoff–von Neumann、Perron–Frobenius | ◎ `Matrix.PosSemidef.hadamard`、`Matrix.eigenvalue_mem_ball`(Gershgorin)、`singularValues`、`Matrix.IsHermitian.spectral_theorem`。Perron–Frobenius は既約性の定義のみ。Cholesky・極分解は × | A |

### 4.2 解析

| 分野 | カード | 深さ | 欠けている主な標準定理(一般形) | Mathlib | 優 |
|---|---:|---|---|---|---|
| 1変数微積分 | 51 | 標準(MVT, Taylor, FTC, 広義積分) | 有界変動・絶対連続、Lebesgue の微分定理(単調関数)、Abel の極限定理 | ◎ `Monotone.ae_differentiableAt`、`AbsolutelyContinuousOnInterval`、`Complex.stolzSet`(AbelLimit) | B |
| 実解析(数列・級数・一様収束) | 53 | 標準(Weierstrass 近似, Arzelà–Ascoli, Dini) | Γ 関数と Bohr–Mollerup、Beta 関数、Stirling、Basel と ζ(2k)、Euler の正弦積、Cantor 関数 | ◎ `Complex.Gamma_mul_Gamma_one_sub`、`Real.eq_Gamma_of_log_convex`、`betaIntegral`、`stirlingSeq`、`hasSum_zeta_two`、`Complex.tendsto_euler_sin_prod`。Euler–Maclaurin は × | S |
| 多変数微積分・ベクトル解析 | 38 | 標準(逆関数, 陰関数, Lagrange 乗数, 変数変換, 長方形上の Green) | 微分形式と外微分、一般の Stokes、曲面積分、Jacobian の体積公式、線積分、Morse 補題 | △ `extDeriv`(ℝⁿ 上のみ)、◎ `lintegral_abs_det_fderiv_eq_addHaar_image`、`CurveIntegral`。一般 Stokes・Poincaré の補題は × | B |
| 一般位相・距離空間 | 59 | 標準(Tychonoff, Urysohn, Tietze, Baire) | 一点コンパクト化、Polish 空間、Stone–Čech と profinite、局所コンパクト、パラコンパクト、Gromov–Hausdorff | ◎ `OnePoint`、`PolishSpace`、`GromovHausdorff`、`isDenseEmbedding_coe` | B |
| 測度・積分 | 51 | 標準〜上級(MCT, DCT, Fubini, Radon–Nikodym, Lebesgue 微分) | Hausdorff 測度と次元、Riesz–Markov–Kakutani、Haar 測度の一意性、Vitali・Besicovitch 被覆、弱収束の Portmanteau、Prokhorov | ◎ `dimH`、`hausdorffMeasure`、RieszMarkovKakutani/、`measure_isHaarMeasure_eq_smul_of_isEverywherePos`、MeasureTheory/Covering/(Besicovitch, Vitali)。Lusin は × | A |
| Banach・Hilbert 空間 | 36 | 上級(HB, 開写像, 閉グラフ, Alaoglu, Riesz) | 弱位相、反射性、Lax–Milgram、再生核、Krein–Šmulian、Schauder 基底 | ◎ `IsCoercive`(LaxMilgram)、`Analysis/InnerProductSpace/Reproducing`、`WeakBilin` | B |
| 作用素論・スペクトル論 | 14 | 上級(共役, コンパクト作用素, スペクトル半径) | コンパクト自己共役作用素のスペクトル分解、Fredholm の択一、非有界作用素、連続関数計算 | ◎ `eq_zero_of_forall_hasEigenvalue_eq_zero`・`finite_dimensional_eigenspace`(InnerProductSpace/Spectrum)、Fredholm 択一(Normed/Operator/Compact/FredholmAlternative)、`LinearPMap`、`IsSelfAdjoint.spectralRadius_eq_nnnorm` | A |
| C*環・作用素環 | 0(`adjoint_cstar_identity` のみ) | なし | Gelfand 双対、連続関数計算、正元の特徴づけ、GNS、Fuglede、近似単位元 | ◎ `gelfandTransform_map_star`・`spectrum.gelfandTransform_eq`(GelfandDuality)、`cfcHom`、`PreGNS`(GelfandNaimarkSegal)、Fuglede。von Neumann 環は定義のみ | A |
| 調和解析・Fourier | 12 | 標準(級数, Parseval, Riemann–Lebesgue, Poisson 和) | Fourier 反転、Plancherel、Gauss 関数の Fourier 変換、畳み込み定理、有限アーベル群の DFT と指標の直交性、Haar 測度 | ◎ `MeasureTheory.Integrable.fourierInv_fourier_eq`、`fourierTransformₗᵢ`・`norm_fourier_eq`(Fourier/LpSpace)、`fourierIntegral_gaussian`、`fourier_bilin_convolution_eq`、`expect_eq_ite`(AddChar)。Pontryagin 双対、Hardy–Littlewood 極大関数は × | S |
| 超関数・Sobolev | 0(`smooth_bump_exists` のみ) | なし | 緩増加超関数、Schwartz 空間上の Fourier、基本補題(du Bois-Reymond)、Fourier 乗法子、Bessel ポテンシャル | ◎ `TemperedDistribution`、`ae_eq_zero_of_integral_contMDiff_smul_eq_zero`、`fourierMultiplierCLM`、`besselPotential` | B |
| PDE | 0 | なし | 調和関数の平均値性質・最大値原理、Poisson 核、Lax–Milgram、熱・波動方程式の解 | △ `HarmonicOnNhd.circleAverage_eq`、`herglotzRieszKernel`、`IsCoercive`。熱核・波動方程式・Poincaré 不等式は × | B |
| 常微分方程式 | 29 | 中級(線形, Gronwall, Picard–Lindelöf, 行列指数, Wronskian) | 最大解と爆発、平衡点と Lyapunov 安定、Sturm の比較、Liouville の公式、フロー | ◎ `Dynamics/Flow`、`OmegaLimit`、ODE/ExistUnique。Lyapunov・Hartman–Grobman・Poincaré–Bendixson は × | B |
| 変分法 | 0 | なし | 基本補題、Euler–Lagrange、等周不等式、Dirichlet 原理 | △ 基本補題のみ(上の超関数行)。Euler–Lagrange は × | C |
| 複素解析 | 47 | 標準(Cauchy, Liouville, 最大値, 開写像, Schwarz) | 有理型関数と位数・因子、Schwarz–Pick、exp は被覆、Phragmén–Lindelöf、Hadamard 三線、Jensen の公式、Riemann の写像定理 | ◎ `meromorphicOrderAt`、`Complex.dist_le_div_mul_dist_of_mapsTo_ball`、`Complex.isCoveringMap_exp`、`PhragmenLindelof.horizontal_strip`、JensenFormula、`ValueDistribution`。Riemann の写像定理は △(`exists_injective_not_dense_image_deriv_ne_zero`)。留数定理・偏角の原理・Rouché・Mittag-Leffler は × | A |
| 多変数複素関数・Riemann 面 | 0 | なし | 多重円板の Cauchy 公式、Hartogs、Riemann 面、一意化 | △ `TorusIntegral`、Geometry/Manifold/Complex。Hartogs は × | C |

### 4.3 確率・統計

| 分野 | カード | 深さ | 欠けている主な標準定理(一般形) | Mathlib | 優 |
|---|---:|---|---|---|---|
| 確率論(測度論的) | 44 | 標準(独立, 期待値, 分散, 条件付き期待値, LLN/CLT は名のみ) | 特性関数と一意性、Lévy の連続性、Hoeffding・sub-Gauss、標準分布(Poisson, 指数, 幾何, Gamma, Beta, 多変量 Gauss)、0-1 法則 | ◎ `charFun`、MeasureTheory/Measure/LevyConvergence、`HasSubgaussianMGF`、`poissonMeasure`、`exponentialPDF`、`geometricMeasure`、`IsGaussian`、Probability/Independence/ZeroOne | S |
| マルチンゲール・確率過程 | 3 | 基礎(期待値の保存のみ) | 収束定理、Doob の極大不等式、任意停止、upcrossing、Brown 運動、Kolmogorov の連続性、Markov 連鎖 | ◎ `Submartingale.ae_tendsto_limitProcess`、`MeasureTheory.maximal_ineq`、`Submartingale.expected_stoppedValue_mono`、`IsPreBrownianReal`、`HasIndepIncrements`、`IsKolmogorovProcess`。Markov 連鎖は Kernel の既約性定義のみ。Poisson 過程・Itô は × | S |
| 数理統計 | 3 | 基礎(不偏性) | Bayes 推定とリスク、最小二乗(正規方程式)、Gauss–Markov、十分統計量、Cramér–Rao、最尤推定、検定、χ²・t 分布 | △ Probability/Decision/BayesEstimator(`avgRisk_eq_lintegral_posterior_prod`、`lintegral_iInf_posterior_le_bayesRisk`)。十分統計量・Cramér–Rao・検定は × | B |

### 4.4 組合せ論・離散・幾何

| 分野 | カード | 深さ | 欠けている主な標準定理(一般形) | Mathlib | 優 |
|---|---:|---|---|---|---|
| 組合せ論 | 36 | 基礎〜標準(二項, 包除, 鳩, Catalan の閉形式) | 母関数、整数分割(Euler・Glaisher)、Stirling・Bell、Dyck 語、Kruskal–Katona、LYM、Sauer–Shelah、Cauchy–Davenport、Erdős–Ginzburg–Ziv、Hales–Jewett、Hindman、Szemerédi の正則性 | ◎ `catalanSeries_sq_mul_X_add_one`、`card_odds_eq_card_distincts`、Combinatorics/Enumerative/Pentagonal、`kruskal_katona`、`local_lubell_yamamoto_meshalkin_inequality_mul`、`ZMod.cauchy_davenport`、`ZMod.erdos_ginzburg_ziv_prime`、`exists_mono_in_high_dimension`、`FP_partition_regular`、`szemeredi_regularity`。有限 Ramsey は × | A |
| グラフ理論 | 12 | 基礎(握手, 木, Euler, 二部) と Turán・Hall | Tutte の完全マッチング、色数、Laplacian の核と連結成分、Hamilton 閉路 | ◎ `SimpleGraph.tutte`、`chromaticNumber`、`lapMatrix_toLinearMap₂'_apply'_eq_zero_iff_forall_reachable`、`IsHamiltonian`(定義と補題のみ)。Cayley の公式・Menger・平面性・Kuratowski は × | A |
| 符号・暗号・離散情報 | 0 | なし | Hamming 距離、Kraft–McMillan、KL ダイバージェンス、Lucas 素数判定、Lucas–Lehmer | ◎ InformationTheory/Coding、InformationTheory/KullbackLeibler、`lucas_primality`。Reed–Solomon・Singleton 限界は × | B |
| 幾何(Euclid・アフィン・射影・凸) | 約12 | 標準(余弦定理, Ptolemy, 等長, Mazur–Ulam) | Helly、Radon、Birkhoff–von Neumann、Minkowski の凸体定理、Farkas と分離、反転、九点円と Monge 点、射影空間、双曲幾何 | ◎ `helly_theorem'`、`radon_partition`、`doublyStochastic_eq_convexHull_permMatrix`、`exists_ne_zero_mem_lattice_of_measure_mul_two_pow_lt_measure`、`hyperplane_separation'`、Geometry/Euclidean/Inversion、`ninePointCircle`。射影空間は定義と独立性(`Projectivization`)のみで Desargues・Pappus は × | A |
| 凸解析・最適化 | 10 | 標準(Jensen, KM, Carathéodory, 分離) | 強凸、Farkas、共役関数、KKT、勾配降下の収束 | ◎ `StrongConvexOn`、`hyperplane_separation'`。共役関数・KKT・LP 双対は × | A |
| 数値解析 | 8 | 基礎(二分法, 台形則, 縮小写像) | Chebyshev 多項式と補間、Bernstein 多項式、Newton の二次収束、Simpson・Gauss 求積 | ◎ `Polynomial.Chebyshev`。求積・反復法の誤差解析は × | C |
| エルゴード理論・力学系 | 0 | なし | Poincaré の再帰、平均エルゴード、回転・倍写像のエルゴード性、位相エントロピー、回転数、極小系 | ◎ `MeasurePreserving.conservative`、`ContinuousLinearMap.tendsto_birkhoffAverage_orthogonalProjection`、`ergodic_zsmul`、`coverEntropy`、`CircleDeg1Lift`、`MulAction.IsMinimal`。Birkhoff の各点エルゴード定理・Sharkovsky は × | B |

## 5. Top25(重要度 × 現時点の実現性)

重要度と実現性は各1〜5点で、積の降順に並べた(同点は重要度が高い方を上にした)。実現性は Mathlib の宣言があり、一般形で書けるかで判断した。
Mathlib 宣言名と「最初に作るカード」は §4 の該当行を参照。

| 順位 | 穴 | 重要 | 実現 | 積 | 最初に作るカード(一般形) |
|---:|---|---:|---:|---:|---|
| 1 | Fourier 解析の主定理 | 5 | 5 | 25 | Fourier 反転、L² の等長(Plancherel)、Gauss 関数の変換、畳み込み定理、有限アーベル群の指標の直交性 |
| 2 | 特殊関数(Γ, ζ(2k), Stirling) | 5 | 5 | 25 | Γ の反射公式、Bohr–Mollerup、Euler の正弦積、ζ(2k)、Stirling の級数 |
| 3 | 確率分布と特性関数 | 5 | 5 | 25 | Poisson・指数・幾何分布の平均と分散、Gauss の特性関数、Lévy の連続性、Hoeffding |
| 4 | 初等整数論の定番 | 4 | 5 | 20 | Lagrange 四平方、ピタゴラス数の分類、LTE、Jacobi 記号の相互法則、Dirichlet 近似、Lucas の定理 |
| 5 | マルチンゲール | 4 | 5 | 20 | 収束定理、Doob の極大不等式、任意停止、Brown 運動の性質 |
| 6 | 組合せ論の主要定理群 | 4 | 5 | 20 | Kruskal–Katona、LYM、Cauchy–Davenport、EGZ、Hales–Jewett、Szemerédi の正則性、Glaisher |
| 7 | グラフ理論 | 4 | 5 | 20 | Tutte の完全マッチング、色数と二部性、Laplacian の核 |
| 8 | Ext・Tor・群コホモロジー | 5 | 4 | 20 | Ext の長完全列、Hilbert 90 を H¹ で、蛇の補題の一般形(§7) |
| 9 | 計算可能性・オートマトン | 4 | 5 | 20 | 停止問題、Rice、再帰定理、ポンピング補題、Myhill–Nerode |
| 10 | 代数的整数論の中心定理 | 5 | 4 | 20 | Dirichlet の単数定理、Minkowski の評価、Σeᵢfᵢ=n、Kummer–Dedekind(§7) |
| 11 | Lie 理論 | 4 | 5 | 20 | Lie の定理、Killing 形式⇒半単純、sl₂ 三つ組、Cartan 行列(§7) |
| 12 | 解析的整数論 | 4 | 4 | 16 | Euler 積、L(1,χ)≠0、Chebyshev 評価、素数逆数和の発散 |
| 13 | C*環と連続関数計算 | 4 | 4 | 16 | Gelfand 双対、自己共役元のスペクトル半径=ノルム、GNS |
| 14 | コンパクト作用素のスペクトル論 | 4 | 4 | 16 | Fredholm の択一、コンパクト自己共役作用素の固有空間、Lax–Milgram |
| 15 | 群論の中級定理 | 4 | 4 | 16 | Jordan–Hölder、Schur–Zassenhaus、Nielsen–Schreier |
| 16 | 複素解析の拡張 | 4 | 4 | 16 | 有理型関数の位数、Schwarz–Pick、exp は被覆、Phragmén–Lindelöf |
| 17 | 特異ホモロジーと被覆のモノドロミー | 5 | 3 | 15 | H₀≅⊕_{π₀}R、ホモトピー不変性、モノドロミー作用(§7、語彙が先に要る) |
| 18 | 数理統計 | 5 | 3 | 15 | Bayes リスク、最小二乗の正規方程式、Gauss–Markov |
| 19 | モデル理論 | 3 | 5 | 15 | Łoś、Łoś–Vaught、DLO の完全性 |
| 20 | 集合論(順序数・基数) | 3 | 5 | 15 | Cantor 標準形、正則基数、König、#ℝ=𝔠 |
| 21 | 凸幾何 | 3 | 5 | 15 | Helly、Radon、Birkhoff–von Neumann、Minkowski の凸体定理 |
| 22 | エルゴード理論 | 3 | 4 | 12 | Poincaré の再帰、平均エルゴード、回転のエルゴード性 |
| 23 | 測度論的幾何 | 3 | 4 | 12 | Hausdorff 次元、Riesz–Markov、Haar の一意性 |
| 24 | 超関数・Schwartz・Sobolev | 3 | 4 | 12 | 緩増加超関数、基本補題、Fourier 乗法子 |
| 25 | 順序・束(Knaster–Tarski, Birkhoff 表現) | 3 | 4 | 12 | 完備束の最小不動点、有限分配束の表現 |

次点は、楕円曲線・保型形式の基礎(積12)、多様体上の基礎(積分曲線と Lie 括弧、積12)、微分幾何(重要5、実現1、積5。Mathlib に曲率が無いため §8 へ)である。

## 6. 見かけの枚数に対して浅い領域

| 領域 | 枚数 | 中身 | 根拠 |
|---|---:|---|---|
| `advanced_undergrad` | 31 | 約15枚は公理・インスタンス・定義の言い換えである。`lie_bracket_anticommutative`(`lie_skew`)、`lie_jacobi_cyclic_sum`(`lie_jacobi`)、`ring_of_integers_is_dedekind`・`class_group_of_number_field_finite`・`padic_numbers_complete`(`infer_instance`)、`elliptic_curve_points_group_law`(`add_comm`・`add_assoc`・`add_zero`・`add_neg_cancel` の連言)、`homology_map_functorial`(関手性の2式)、`padic_norm_ultrametric`(`Padic.nonarchimedean`)、`character_is_class_function`(`char_conj`) | 証明がすべて1行で、述べる事実が構造の定義そのもの。例外は Maschke、Schur、指標の直交、Engel、Hensel、Dirichlet、compactness、長完全列 |
| Lie 理論 | 6 | 3枚が公理、他は `lie_le_inf`・導来列の単調性・可解性の像など定義の帰結。Lie 群は0枚 | Cartan 判定・Killing・根系・sl₂ が0枚(§7) |
| 多様体 | 6 | `chart_contains_point`(チャートの定義の展開)、`mfderiv_id_const`(2補題の連言)、`mfderiv_eq_fderiv_normed`(定義の比較)、`mfderiv_chain_rule`。実質的な内容は隆起関数と1の分割の2枚だけ | 接ベクトル場・積分曲線・はめ込みが0枚 |
| 代数的位相 | 16 | 6枚はホモトピーの同値関係・基点変更・関手性の確認。基本群の計算は0枚。特異ホモロジー0枚。名前は「ホモトピー・基本群・被覆」だが、π₁(S¹) の計算がなく、ホモロジーがない | §7 |
| 圏論 | 14 | `inverse_morphism_unique`、`mono_with_section_is_iso`、`fully_faithful_reflects_isomorphism` など基本補題が主。Kan 拡張、モナドと monadicity、随伴関手定理、層化が0枚 | ◎ `AdjointFunctorTheorems`、`MonadicRightAdjoint`、`sheafificationAdjunction` |
| マルチンゲール | 3 | `martingale_expectation_const`、`submartingale_expectation_mono`、`doob_martingale` はいずれも期待値の保存や定義の確認。収束・停止・極大不等式が0枚 | §4.3 |
| 複素解析 | 47 | 15枚(32%)は複素数と初等関数の算術(共役、極形式、exp・log、1の冪根、Euler・de Moivre)。関数論は32枚。留数・有理型は0枚 | id 一覧は `conj_mul_self_eq_norm_sq` から `principal_log_derivative` までの15枚 |
| 論理・集合・写像・同値関係 | 28(`logic_sets` の56%) | 命題論理、集合算、写像と同値関係の level 1〜2 で、高校数学との重なりが大きい。集合論そのもの(濃度・順序数・Zorn)は16枚 | `logic_sets` 50枚のうち |
| 確率論 | 44 | 11枚は有限確率・初等恒等式(余事象、包除、全確率、乗法公式)。LLN・CLT・Borel–Cantelli II は名前つきの Mathlib 呼び出し | 標準分布・特性関数・Lévy が0枚 |
| 微積分(1変数) | 51 | level 1 が大半で、`school_calculus` 51枚と内容が重なる(広義積分、Taylor、MVT の基本形) | 高校範囲との重複は別途の重複調査が要る |

## 7. Algebra/Geometry detail

可換環論・代数幾何は `gap_commalg_ag.md` を参照する。ここでは他の6分野と、その2分野の位置づけを1行ずつ示す。

| 分野 | カード | 深さ | 欠けている標準定理(一般形、≤8) | Mathlib 状態と宣言名 | 優 |
|---|---:|---|---|---|---|
| 可換環論 | 36(+環論54+加群42) | 看板定理が各1〜3枚で最弱形。A–M 後(Matsumura)は0枚 | `gap_commalg_ag.md` §3 と §5 の15枚(Krull の標高定理、dim R[X]、Artin–Rees、going down、prime avoidance、正則列、正則局所環) | ◎ 大半あり。本書では再掲しない | S |
| 代数幾何 | 3(Spec の位相のみ) | スキーム・層・射が0枚 | `gap_commalg_ag.md` §4(構造層、Proj、準連接層、Ω、層コホモロジー) | ◎ Spec・Proj・`Scheme.Modules`。△ 層コホモロジーは定義。× Riemann–Roch、Picard、種数 | A(アフィン)/B(スキーム語彙) |
| ホモロジー代数 | 3(鎖複体)+加群行 約12(完全列・射影・移入・平坦) | 鎖複体の関手性と長完全列まで。導来関手がない | (1)Ext の長完全列、(2)Yoneda 拡大と Ext¹、(3)平坦⇔Tor₁=0、(4)射影分解、(5)群コホモロジー H¹・H² と Hilbert 90、(6)蛇の補題の一般形(ker・coker 両端を含む)、(7)スペクトル系列、(8)鎖複体の Euler 標数 | ◎ `Ext.covariant_sequence_exact₂'`(DerivedCategory/Ext/ExactSequences)、`groupCohomology`、`ProjectiveResolution`、`ShortComplex.SnakeInput.snake_lemma`、Hilbert90.lean、`isCoboundary₁_of_mem_coboundaries₁`。△ `SpectralSequence` は構造の定義、Euler 標数は `EulerCharacteristic.lean`。Tor は CategoryTheory/Monoidal/Tor と GroupHomology にある | S |
| 表現論 | 5(+加群行の Schur・半単純 約4) | 標準(Maschke, Schur, 指標の直交) | (1)指標の積・双対(`char_tensor`・`char_dual`)、(2)指標内積=不変部分の次元、(3)正則表現の分解、(4)誘導・余誘導と Frobenius 相互律、(5)Artin–Wedderburn、(6)既約表現の個数=共役類の個数、(7)群環の半単純性、(8)群コホモロジーとの接続 | ◎ `FDRep.finrank_hom_simple_simple`、`char_tensor`、`char_dual`、`scalar_product_char_eq_finrank_equivariant`、`IsSemisimpleRing.exists_algEquiv_pi_matrix_of_isAlgClosed`、`Representation.leftRegular`、`Representation.ind`・`coind`。(4)の相互律と(6)は × | A |
| Lie 理論 | 6(Lie 環のみ、Lie 群0) | 基礎(公理, イデアル, 可解) と Engel | (1)Lie の定理、(2)Killing 形式が非退化なら半単純、(3)Cartan の判定法、(4)sl₂ 三つ組と根空間、(5)根系と Cartan 行列、(6)古典 Lie 環 sl・so・sp、(7)普遍包絡環、(8)Lie 群の Lie 環 | ◎ `LieModule.exists_forall_lie_eq_smul_of_isSolvable_of_finite`、`LieAlgebra.IsKilling.instSemisimple`(Algebra/Lie/Killing)、`killingForm`、`IsSl2Triple`、`sl2SubalgebraOfRoot`、`cartanMatrixIn`、`LieAlgebra.sl`、`UniversalEnvelopingAlgebra`、`GroupLieAlgebra`、`LieGroup`。Cartan の判定法は △(CartanCriterion.lean は補助補題のみ) | A |
| 代数的整数論 | 7(+Dedekind 3、可換環論行) | 標準(Dedekind, 類群の有限性, 円分体の整数環) | (1)Dirichlet の単数定理、(2)Minkowski の類群評価、(3)判別式の下界、(4)Σeᵢfᵢ=n、(5)Kummer–Dedekind、(6)Frobenius 元、(7)Dedekind ζ の留数の正値性、(8)Hermite–Minkowski の有限性 | ◎ `exist_unique_eq_mul_prod`・`finrank_eq`(Units/DirichletTheorem)、`exists_ideal_in_class_of_norm_le`、`abs_discr_ge'`、`sum_ramification_inertia`、KummerDedekind.lean、`dedekindZeta_residue_pos`。△ `IsArithFrobAt` は定義。× Hermite–Minkowski、Chebotarev、Kronecker–Weber、類体論 | A |
| 代数的位相 | 16(基本群・被覆・ホモトピー) | 基礎(同値関係, 関手性, 道の持ち上げ) | (1)特異ホモロジーの定義と H₀、(2)ホモトピー不変性、(3)被覆のモノドロミー作用、(4)単連結空間からの持ち上げ基準、(5)π₁(S¹)≅ℤ、(6)Euler 標数、(7)Mayer–Vietoris、(8)Brouwer の不動点定理 | ◎ `singularHomology₀Iso`、`congr_homologyMap_singularChainComplexFunctor`、`monodromy_theorem`、`monodromyPerm_injective`、`Complex.isCoveringMap_exp`・`Circle.isCoveringMap_exp`。△ Eilenberg–Steenrod 公理(`TopPair.HomologyPretheory`)と CW 複体は定義。× π₁(S¹) の計算、特異ホモロジーの Mayer–Vietoris(層のものだけある)、Brouwer、Jordan 曲線 | A(語彙拡張が先) |
| 微分幾何・多様体 | 2(曲線の弧長)+多様体6 | 定義の展開と1の分割まで | (1)接ベクトル場の Lie 括弧、(2)積分曲線の存在と一意、(3)Riemann 計量、(4)微分形式と外微分、(5)はめ込み・沈め込み、(6)Whitney 埋め込み、(7)曲率と測地線、(8)Gauss–Bonnet | ◎ `mlieBracket`、`IsMIntegralCurveAt`、`IsImmersion`。△ `IsRiemannianManifold`(定義と距離のみ)、`extDeriv`(ℝⁿ 上)、`embeddingPiTangent`(Whitney の部分)。× 曲率・測地線・Gauss–Bonnet・Sard(該当語が Mathlib 全体で0〜数ファイル) | B(基礎)/C(曲率以降) |

## 8. Mathlib に無く、カード化ではなく定理開発になる領域

grep で見当たらなかったもの(2026-06-24 の pinned rev)。これらは先に Lean 側の定理が要るため、カタログ拡張の優先順位からは外した。

| 領域 | 無いもの |
|---|---|
| 位相・幾何 | Brouwer の不動点定理、Jordan 曲線定理、Riemann 曲率・Levi-Civita・測地線、Sard の定理、Mayer–Vietoris(特異ホモロジー) |
| 数論 | 素数定理、Hecke 作用素、Hasse の定理・Mordell–Weil、Euclid–Euler(完全数)、Wolstenholme |
| 解析 | 留数定理・偏角の原理・Rouché、Mittag-Leffler(複素解析版)、Hartogs、Euler–Maclaurin、熱方程式・波動方程式の解、Poincaré・Rellich 不等式、Euler–Lagrange、Lusin の定理 |
| 離散 | Cayley の公式、Menger、平面グラフと Kuratowski、Dilworth、有限 Ramsey、Dirac の Hamilton 定理 |
| 線形代数 | Jordan 標準形、Cholesky、極分解(Perron–Frobenius は既約性の定義のみ) |
| 確率・統計 | Cramér–Rao、十分統計量、Itô 積分、Birkhoff の各点エルゴード定理、Sharkovsky、Hartman–Grobman、Lyapunov 安定、Poisson 過程 |
| 代数 | Artin–Schreier、Birkhoff の HSP、Frobenius 相互律(誘導表現) |

## 9. 追加で確認した点

- `all_cards.json` の 1,881 枚は README の「1,062 枚」より多い。README の数値は旧版とみられ、本書は 1,881 枚を母数にした。
- 重複 id が9件あることは `gap_commalg_ag.md` §6 にある。本書の枚数は id 重複を除いていない(大学範囲で影響する重複は `quotient_lift_unique` の1件)。
- 提案した追加カードは、いずれも Mathlib の `exact` で閉じる形が確認できるものを優先した。OpenMath 語彙の追加が要る領域(層、導来圏、特異ホモロジー、確率過程)は優先度を A 以下にしてある。
