# Draft OpenMath 符号化の監査

## 結論

判定は**修正**(modify)。OpenMath 2 XML、alpha 正規化、ベクトル検索と構造リランクの組み合わせは残す。置換は不要。
ただし現状のまま公開すると、定理と逆、同一事実の別表記という2種類の誤りが構造スコアに出る。原因は次の3点。

1. リランクの構造特徴が変数の配線と前提・結論の役割を見ない。
2. 向き(`>` と `<`)や可換引数の順序を正規化していない。
3. 同義語、引数順の食い違い、担体と構造の欠落、カード固有述語が語彙に残っている。

1と2は XML 形式を変えずに直せる(リランクのコードだけ)。3は語彙とカードの修正で、XML が変わるので再埋め込みが要る。
担体付きバインダ(OMATTR)は次の正規化バージョンの課題とし、今は載せない。

## 前提と測定方法

- 対象: `drafts.json` の 1,881 件(`generic_now` 442、`needs_vocabulary` 1,438、`duplicate_of_existing` 1)。語彙 `pals2` は 1,055 記号。
- 構造類似度は、デプロイ済み `openmath.py` の `_structural_features` をそのまま読み込んで使った(`rfc8785` だけスタブ化)。
- ペアの指標は特徴多重集合の重み付き Jaccard(最小の和/最大の和)。全 1,881 件の全ペア約177万を計算した。
  - 0.5以上が1,031、0.8以上が24、0.9以上が9、1.0が5。
  - デプロイ済みの非対称スコア(被覆率0.85+精度0.15)も併記した。両者の順位はほぼ一致する。
- 「Lean が異なる」は、正規化した `target`(束縛名を番号化)が一致しないこととした。同一 XML や同一正規化 Lean の重複カードはない。
- 未測定: 埋め込み側の40%、クエリ側 LLM の出力、実際のヒット率。標準 CD の記述は記憶による(各行に「要確認」を付けた)。
- 参考: README の「generic_now 87件、976記号」は古く、このスナップショットでは442件と1,055記号。

## 発見(検索リスク順)

### F1 構造特徴は変数の配線を見ず、逆定理と双対を弁別できない(誤再利用、高)

- `_shape_signature` は OMV をすべて `OMV` として扱う。どの変数がどの引数位置に現れるかは特徴に入らない。
- 前提と結論の入れ替えは、最上位の `implies` の部分木にしか差を作らない。
- 上位40ペアの判定は、危険12、軽度4、重複5、無害19(下表)。
- 同一特徴(Jaccard 1.00)で XML が異なるペアが5つある。
  - `geometry_circle_intersecting_chords_converse` と `geometry_circle_secants_converse`。弦の内点Hと割線の外点Qの違いが配線にしかない。
  - `geometry_plane_three_perpendiculars` と `..._converse_foot`。前提と結論が入れ替わっただけ。
- 逆のペアは 0.88〜0.94 で並ぶ。例: `geometry_triangle_angle_bisector_theorem_internal` と `..._converse`(0.94)、`geometry_plane_corresponding_angles_of_parallel` と `geometry_plane_parallel_of_corresponding_angles`(0.90)。
- 強法則と弱法則(`probability_statistics_strong_law_large_numbers` と `..._weak_law_...`)は、`ae_tends_to` と `prob_tends_to` の差だけで 0.84。
- 試作(コードのみ): 次の2種類の特徴を足した。
  - 変数ごとの出現スロット(記号:引数位置:前件/後件)の集合と、スロット対のリンク。変数名や束縛順に依存しない。
  - 原子式が `implies` の前件側か後件側かの印。
- 結果は次のとおり。
  - 逆ペア(#7〜#10)は 0.88〜0.94 から 0.50〜0.53 に下がった。
  - chords と secants は 1.00 から 0.68 に下がった。
  - 0.8以上は24から13、0.9以上は9から4になった。残りは真の重複(#4、#5 など)。
  - #11 や #13 のような無害な近傍は 0.90 や 0.89 のまま変わらない。

### F2 表面形の正規化がなく、同一定理が離れる(見逃し、高)

- 正規化は alpha 変換だけ(v4)。向きと可換引数の順序は元のまま残る。
- 各カードを正規化して元との類似度を測った。
  - `>`/`>=` を `<`/`<=` に引数交換して直した場合: n=389、平均0.787、中央値0.795。90%が0.9未満。
  - 可換記号(plus、times、and、or、eq)の引数を整列した場合: n=1,801、平均0.863。55%が0.9未満。
- 同じ定理の別表記(0.79〜0.86)が、別の定理の逆(0.88〜0.94)より低くなる。順位が逆転する。
- クエリは LLM(gpt-5.4)が構造化するので、どちらの向きが出てもおかしくない。語彙の使用状況は `gt/geq` が389件、`lt/leq` が403件で、偏りはない。
- 埋め込みは XML 文字列を見るため、同じ非正規化の影響を受ける(未測定)。

### F3 同義語と引数順の食い違い(見逃しと誤接続、高)

- 同義の統合候補は75記号(7.1%)で、283カード(15.0%)に影響する。高信頼49行、中信頼26行。
- 同概念で引数順が逆の記号がある(黙って食い違う)。
  - `vector_space K V`(11件)と `vector_space_over V K`(23件)。
  - `is_module R M`(28件)と `module_over M R`(8件)。
  - `cat_compose g f` と `morphism_comp f g`。前者は「g after f」、後者は「first f then g」。
- 引数順が意味文に書かれていない記号は、arity 2以上の634記号のうち409。
- 宣言と使用が食い違う例がある。`bijection_between`(宣言は `e A B`)を `topology_general_compact_to_hausdorff_hom` が `(X Y f)` で使っている。
- 同じ名前が複数のファイルで定義され(210記号)、うち50記号は文言が違う。意味が実際にずれているもの:
  - `exact_pair`(12カード)は「gf=0 かつ中間で完全」と「im f = ker g」の2通り。
  - `measurable_set` は「可測」と「Lebesgue 可測」。
  - `norm` はベクトルのノルムと作用素ノルム。
  - `complete_space` は距離空間とノルム空間。
  - `max_of` は実数と全順序集合。
- 引数の sort(term/term_function)は全ファイルで矛盾がない。使用箇所の arity 違反と sort 違反は 0 件。
- 同じ概念が複数の名前を持つ代表例(使用カード数):
  - 内射/全射/全単射: `injective`(7)、`injective_function`(6)、`injective_map`(9)。全射と全単射も同様。
  - 二項係数: `binom`(32)、`binomial`(2)、`binomial_coefficient`(2)。
  - 可換環: `comm_ring`(60)、`commutative_ring`(4)、`is_comm_ring`(6)。
  - 円周率 `pi`(90)と `pi_constant`(11)、虚数単位 `complex_imaginary_unit`(23)と `complex_i`(7)。
  - 写像の合成は7つ(`map_compose`、`function_compose_map`、`fn_comp`、`op_comp`、`operator_comp`、`cat_compose`、`morphism_comp`)。`op_comp` は線形写像の合成と行列積を兼ねる。
- デプロイ済み語彙と重複する記号(`openmath.py` の `_SUPPORTED_SYMBOLS` で確認済み):
  - `finite_dim_space`(22件)は `pals1:finite_dimensional`、`dim_of` と `vector_finrank` は `pals1:dimension`(12カードが既に使用)と重複。
  - `compact_set` は `pals1:compact`、`matrix_rank` は `pals1:rank` と重複。
  - `product_set` は `set1:cartesian_product`、`singleton_set` は `set1:set`、`image_of` は `set1:map` と重複。
  - `range_sum`、`real_partial_sum`、`ico_product` は `arith1:sum`/`product` と重複。
  - `interval_integral`(46件)は `calculus1:defint` と重複する。理由は検証器が `defint` の lambda 引数を拒否するため(AUTHORING.md の記述どおり)。検証器の登録 sort を直せば私有記号を減らせる。
- 標準 CD との重複候補(記憶による、公開 CD で要確認): `nums1:pi`、`integer1:factorial`、`combinat1:binomial`、`interval1:interval_cc/oo/co`、`fns1:left_compose/identity`、`complex1:real/imaginary/conjugate/argument`、`linalg1:determinant/transpose/scalarproduct`、`veccalc1:grad/divergence` など28行。
- 定義済みだが生成語彙に出ない記号が19ある(YAML 側の孤児)。

### F4 担体・型クラス・次元の情報が落ちる(誤再利用、中〜高)

- Lean に `Type*` 変数があるカードは977。そのうち557(57%)が、XML の束縛変数に1つ以上の型変数を欠く(`matrix_mul_assoc` は K と各次元を落とす)。型変数 1,666 個のうち 873 個(52%)が落ちている。
- 数の担体は表記が不揃い。ℝのみのカード485件で `(in v R)` の守りがあるのは78件(16%)。ℕ は129件中108件、ℤ は44件中43件、ℂ は38件中32件が守りを書く。「守りなし=ℝ」という暗黙の規約になっていて、ℕ・ℤ のカードが守りを欠くと ℝ と区別できない。
- 型クラスの対応述語が XML にある割合:
  - InnerProductSpace は 248件中53件(21%)。NormedAddCommGroup は 310件中103件(33%)。
  - Field は 137件中94件。Group は 53件中47件。
  - `[NormedAddTorsor V P]` は 193カード(幾何)で、XML に対応する述語がない(点と `dist_of` のみ)。
- 平面前提(`[Fact (Module.finrank ℝ V = 2)]`)を持つのは26カードで、XML に `euclidean_plane_ambient` があるのは5件。`geometry_plane_alternate_angles_of_parallel`(次元不問)と `..._parallel_of_alternate_angles`(平面前提あり)の XML は、この差を表さない。
- 担体と汎化度の違いが近傍に残る例:
  - `complex_analysis_de_moivre_formula`(ℕ冪)と `school_vectors_complex_de_moivre_integer_exponent`(ℤ冪): 0.66。ℤ版はℕ版を含むが逆は成り立たない。
  - `number_theory_euclid_lemma`(ℕ)と `school_integers_dvd_add_iff_right`(ℤ): 0.63。
  - `modules_categories_five_lemma_modules`(Ring)と `..._snake_lemma_modules`(CommRing): 0.76。
- 暗黙の型変換: Lean 本体にキャストを持つカードが194。XML に強制変換の記号はない。`school_data_logic_finset_card_union_two`(ℤ へキャストして引き算)は、ℕ の切り捨て引き算と区別できない。
- `times`/`plus`/`power`(arith1)は数・環・加群・ベクトルで同じ記号を使い、群だけ `group_mul`(6/57カード)を使う。算術記号を使うカード1,003のうち302が非数値の担体を持つ。担体ごとの混同は XML だけでは測れない。
- 述語を引数に取る記号は、述語を項変数として渡している(`holds_at Q n`、`ae_holds mu p`)。語彙の引数 sort は term と term_function のみで、predicate_function はない。

### F5 カード固有の述語と、使い手のいない記号(中)

- `pals2` 1,055記号のうち、1カードだけが使うものは448(42.5%、すべて needs_vocabulary)。依頼文の360件はこのスナップショットと合わない。2カード以上が使うものは607。1つ以上の単独記号を含むカードは326。
- クエリ側 LLM はこれらの名前を当てられない。該当カードの検索は実質埋め込みだけに頼る。
- 手作業で挙げた複合・固有の述語は約58。うち46が単独使用。
  - 他の原子の合成にすぎない例: `order_invertible_in`、`nonzero_in_field`、`char_not_two`、`finite_ring_hom`、`row_addition_product`。
  - 定理の断片を述語にした例: `locally_graph_of`、`right_inverse_near`、`local_inverse_of`、`ae_ball_average_converges`、`ae_eventually_outside`、`big_o_power_decay`、`box_boundary_flux`。
  - 計算式を丸ごと記号にした例: `polygon_exterior_angle_sum`、`group_average_inner_product`、`prime_power_cyclic_sum`、`trapezoid_sum`。
- `finite_group`(19件)は「群 かつ 有限」の合成、`field` と `is_field` は同じ対象を指す。`group_algebra`(1件)は原子としては妥当だが単独使用。
- 記号名に定理名は入っていない(命名規則 "Name concepts, not theorems" は守られている)。
- 単独記号は特徴を薄める。結論に効かない固有名と、長い前提の定型文が特徴量を占める。`five_lemma_modules` は束縛25個で `is_module` が10個並ぶ。
- ほぼ同一のカードが5組ある(#4、#5、#20、#22、#38)。語彙ではなくカードの重複。

### F6 バインダ・関数引数・alpha 正規化(中)

- バインダは裸の OMV。型は使われ方からしか分からない。
- 検索プロファイルが許す要素は OMOBJ、OMS、OMV、OMI、OMB、OMF、OMA、OMBIND、OMBVAR のみ。OMATTR は不可で、OMBVAR は直接の OMV だけを持てる。
  - alpha 正規化器(`_normalize_bound_declaration`)は OMATTR 付き宣言を処理でき、特徴抽出も OMATTR を扱う。
  - ただし、担体付きバインダの導入にはプロファイルの変更と新しい正規化バージョンが要る(v4 のベクトルとダイジェストは固定されている)。
- 2 sort の引数と alpha 正規化は矛盾しない。sort は lambda の有無で構文的に決まり、正規化は束縛名を変えるだけ。引数の sort 違反は 0 件。
- term_function を取る記号は60。lambda は768、そのうち 281(37%)は `(lambda (x) (fn_value f x))` というη展開で、`f` を渡すだけの内容に束縛1つと部分木1つを足している。
  - 同概念の項版と関数版が並存する: `has_derivative_at`(T)と `has_deriv_at`(F)、`continuous_on_set`(T)と `fn_continuous_on`(F)、`injective`(T)と `fn_injective`(F)。
- 束縛番号は束縛宣言の先行順で付く。`∀ a b` と `∀ b a` で XML が変わる(特徴は変数に無関係なので検索側は不変、埋め込みは影響を受ける)。

### F7 クエリ側の語彙(高、データ外)

- 構造化プロンプトが知らせるのは標準 CD と pals1 のみ(`_openmath_prompt`)。`pals2` の1,055記号はプロンプトにも検証器にも入っていない。
- 同義語と引数順の食い違いを解消しないまま、LLM に1,055記号から選ばせると見逃しが増える。F3の統合表は、この選択の前に済ませる。

## 上位40ペア(Jaccard 順、Lean は異なる)

判定: 危険は取り違えると誤った証明になるもの(逆、強弱、位置の差)。軽度は兄弟関係で、向きや符号だけが違うもの。重複は同一事実。無害は同じ道具立ての別命題。
「配線後」は F1 の試作特徴を足した場合。

| # | Jacc | 配線後 | A | B | 判定 | 理由 |
|--:|--:|--:|---|---|---|---|
| 1 | 1.00 | 0.68 | geometry_circle_intersecting_chords_converse | geometry_circle_secants_converse | 危険 | Hが両弦の内側/Qが両割線の外側。XMLの差は変数の配線のみ |
| 2 | 1.00 | 0.91 | geometry_plane_three_perpendiculars | geometry_plane_three_perpendiculars_converse_foot | 危険 | 定理と逆(前提と結論が入れ替わり) |
| 3 | 1.00 | 0.89 | geometry_triangle_right_triangle_altitude_geometric_mean | geometry_triangle_right_triangle_leg_square_projection | 軽度 | 同じ図形配置の別系 |
| 4 | 1.00 | 0.97 | school_algebra_basics_two_variable_system_explicit_solution | school_analytic_geometry_lines_cross_unique_intersection | 重複 | 同一事実(2元連立の公式)、変数名違い |
| 5 | 1.00 | 1.00 | school_algebra_basics_squares_equal_iff_equal_or_negative | school_algebra_basics_square_eq_square_iff | 重複 | 同一事実、変数名違い |
| 6 | 0.95 | 0.79 | geometry_triangle_triangle_congruent_asa | geometry_triangle_triangle_congruent_aas | 軽度 | ASAとAAS。与える辺の違いが特徴量に出ない |
| 7 | 0.94 | 0.53 | geometry_triangle_angle_bisector_theorem_internal | geometry_triangle_angle_bisector_theorem_converse | 危険 | 定理と逆 |
| 8 | 0.90 | 0.51 | geometry_plane_corresponding_angles_of_parallel | geometry_plane_parallel_of_corresponding_angles | 危険 | 定理と逆 |
| 9 | 0.90 | 0.50 | geometry_plane_alternate_angles_of_parallel | geometry_plane_parallel_of_alternate_angles | 危険 | 定理と逆 |
| 10 | 0.88 | 0.52 | geometry_plane_rhombus_diagonals_perpendicular | geometry_plane_rhombus_of_perpendicular_diagonals | 危険 | 定理と逆 |
| 11 | 0.88 | 0.90 | school_counting_probability_cond_prob_uniform_ratio | school_counting_probability_cond_prob_uniform_mul | 無害 | 同一等式の変形 |
| 12 | 0.87 | 0.68 | geometry_centers_menelaus_theorem | geometry_centers_menelaus_converse | 危険 | 定理と逆 |
| 13 | 0.87 | 0.89 | school_exp_log_logb_change_of_base | school_exp_log_logb_chain_product | 無害 | 別の対数恒等式 |
| 14 | 0.86 | 0.69 | school_analytic_geometry_line_tangent_circle_iff_dist_eq_radius | school_analytic_geometry_line_secant_circle_iff_dist_lt_radius | 軽度 | 接線(=)と割線(<) |
| 15 | 0.85 | 0.83 | school_quadratic_quadratic_min_at_vertex_unique | school_quadratic_quadratic_max_at_vertex_unique | 無害 | 最小と最大の双対 |
| 16 | 0.85 | 0.84 | school_analytic_geometry_ellipse_focal_sum_iff_standard | school_analytic_geometry_hyperbola_focal_difference_iff_standard | 無害 | 楕円と双曲線 |
| 17 | 0.84 | 0.85 | school_data_logic_data_variance_affine_transform | school_data_logic_data_stddev_affine_transform | 無害 | 標準偏差は分散から従う |
| 18 | 0.84 | 0.81 | probability_statistics_strong_law_large_numbers | probability_statistics_weak_law_large_numbers | 危険 | 強法則(a.s.)と弱法則(確率収束)。ae_tends_toとprob_tends_toだけが違う |
| 19 | 0.84 | 0.64 | geometry_centers_ceva_theorem | geometry_centers_ceva_converse | 危険 | 定理と逆 |
| 20 | 0.83 | 0.80 | entrance_exam_tetrahedron_opposite_edges_perpendicular | geometry_centers_three_perpendiculars_identity | 重複 | 同一のベクトル恒等式(自由点pの有無のみ) |
| 21 | 0.82 | 0.82 | school_exp_log_logb_lt_iff_base_gt_one | school_exp_log_logb_lt_iff_base_lt_one | 軽度 | 底>1と底<1。不等号の向きが反転 |
| 22 | 0.82 | 0.84 | combinatorics_graphs_card_union_add_card_inter | school_data_logic_finset_card_union_two | 重複 | 同一の包除原理、並べ替え |
| 23 | 0.82 | 0.65 | geometry_triangle_parallel_line_third_side_ratio | geometry_triangle_three_parallel_lines_proportional | 無害 | 平行線と比の系 |
| 24 | 0.80 | 0.48 | geometry_circle_tangent_chord_angle | geometry_circle_tangent_chord_angle_converse | 危険 | 定理と逆 |
| 25 | 0.80 | 0.77 | school_data_logic_data_correlation_abs_le_one | school_data_logic_data_correlation_abs_one_iff_linear | 無害 | どちらもCauchy-Schwarz系。等号条件が違う |
| 26 | 0.79 | 0.53 | school_counting_probability_bayes_uniform_simple | school_counting_probability_indep_uniform_iff_cond | 無害 | ベイズと独立の判定 |
| 27 | 0.79 | 0.51 | school_quadratic_quadratic_formula | school_quadratic_quadratic_factorization_by_formula | 無害 | 公式と、そこから出る因数分解 |
| 28 | 0.79 | 0.78 | geometry_triangle_angle_bisector_length_square | geometry_triangle_angle_bisector_foot_position | 無害 | 二等分線の別公式 |
| 29 | 0.79 | 0.69 | geometry_plane_heron_sine_form | geometry_plane_heron_formula_area | 無害 | ヘロンの二表現 |
| 30 | 0.78 | 0.75 | school_exp_log_logb_mul_positive | school_exp_log_logb_div_positive | 無害 | 積と商の対数法則 |
| 31 | 0.78 | 0.45 | geometry_circle_intersecting_chords_converse | geometry_circle_intersecting_chords_similar_ratio | 危険 | 逆と、順方向の相似比 |
| 32 | 0.78 | 0.45 | geometry_circle_secants_converse | geometry_circle_intersecting_chords_similar_ratio | 危険 | 逆と、順方向の相似比 |
| 33 | 0.78 | 0.57 | school_exp_log_logb_lt_iff_base_gt_one | school_exp_log_logb_compare_different_bases | 無害 | 別の単調性の主張 |
| 34 | 0.78 | 0.69 | school_inequalities_min_sum_squares_on_plane | school_inequalities_max_linear_on_sphere | 無害 | どちらもCauchy-Schwarz系の極値 |
| 35 | 0.77 | 0.64 | school_analytic_geometry_circle_tangent_at_point | school_analytic_geometry_tangent_contact_exists_iff_outside | 無害 | 接線に関する別の主張 |
| 36 | 0.76 | 0.74 | school_counting_probability_prob_uniform_union_add_inter | school_counting_probability_prob_uniform_exactly_one_of_two | 無害 | 別の確率の等式 |
| 37 | 0.76 | 0.64 | modules_categories_five_lemma_modules | modules_categories_snake_lemma_modules | 無害 | 前提の定型文(is_module x10)が特徴量を占有。別の補題 |
| 38 | 0.76 | 0.76 | combinatorics_graphs_card_union_three_sets | school_data_logic_finset_card_union_three | 重複 | 同一の3集合包除、並べ替え |
| 39 | 0.76 | 0.45 | geometry_triangle_proportional_segments_imply_parallel | geometry_triangle_parallel_iff_internal_division_ratio | 無害 | Bの(iff)がAの方向を含む |
| 40 | 0.76 | 0.70 | school_integers_coprime_mul_dvd | school_integers_common_divisor_dvd_gcd | 無害 | どちらも割り算をexistsで表す。主張は別 |

集計は危険12、軽度4、重複5、無害19。危険のうち8件が定理と逆のペア。

## 逆方向: 同じ事実が大きく違う符号化になる

- 同一 id の9対(別ドメイン): `chain_rule`、`product_rule`、`differentiable_implies_continuous`、`extreme_value_theorem`、`open_mapping_theorem`、`markov_inequality`、`uniform_limit_continuous`、`quotient_lift_unique`、`fundamental_theorem_of_algebra`。
  - Jaccard は 0.09〜0.45。多くは汎化度の違い(ℝ版と多様体版)で正当だが、記号がまったく別になる。例: `has_deriv_at` + lambda + `fn_continuous_at` と `has_fderiv_at` + `function_compose_map` + `continuous_map_at`。
  - 連続性は9記号に分かれている(`fn_continuous`、`fn_continuous_at`、`fn_continuous_on`、`continuous_on_set`、`continuous_on_set_fn`、`continuous_map`、`continuous_map_at`、`continuous_between`、`fn_continuous_real`)。
- 同一命題でも記号が違う例:
  - `functional_analysis_cauchy_schwarz_inner_product_space` と `linear_advanced_cauchy_schwarz_inner`。Lean は束縛順を除いて一致するが、前者は `inner_product_space E` と `(in x E)`、後者は `inner_product_space_over K E`。Jaccard 0.54。
  - `complex_analysis_fundamental_theorem_of_algebra`(`complex_polynomial`、`polynomial_degree`)と `field_galois_fundamental_theorem_of_algebra`(`polynomial_over`、`poly_degree`): 0.45。
  - `linear_advanced_tensor_product_universal_property`(`vector_space`、`bilinear_map`)と `modules_categories_tensor_universal_property`(`is_comm_ring`、`is_module`): 0.59。
  - `linear_basic_first_isomorphism` と `modules_categories_first_isomorphism_modules`: 0.19。
- 同じ整数の割り算でも段階で符号化が違う。`dvd` 記号を使うカードが28(すべて needs_vocabulary)、`exists` パターン `(exists (s) (and (in s Z) (= c (* a s))))` が13(generic_now)。
- 無意味な守り `(in (size ..) N)` が81カード、`(in v R)` が119カードにある。前者は常に真で、特徴を水増しするだけ。
- 同一事実の算術上の並べ替えも別物になる: `school_data_logic_finset_card_union_two` と `combinatorics_graphs_card_union_add_card_inter`(0.82)。
- F2のとおり、向きと可換順序の違いだけでも類似度は平均 0.79〜0.86 に下がる。

## 推奨

### 方針

format 全体(OpenMath 2 XML、alpha 正規化、`cdbase`、アルゴリズム)は維持する。
次の3段階で修正する。左ほどコストが低く、効果の測定が先に済んでいる。

### 段階A: リランクのコードだけ(XML と埋め込みは不変、先に実施)

1. 変数の役割特徴とスロット対リンク(F1の試作)を `_structural_features` に追加する。
   - 各原子式に前件・後件・同値の印(`implies`/`equivalent` の引数位置から決める)を付ける。
   - 重みは役割 10、リンク 6、側 8 とした(試作値、調整は未実施)。
2. 特徴抽出の前にだけ正規化した写しを作る。
   - `gt/geq` は `lt/leq` に引数を交換する。
   - 可換記号(plus、times、and、or、eq、neq、gcd、lcm、union、intersect)は、変数番号を無視した部分木の文字列で引数を整列する。
   - 保存された XML は変えない。
3. 回帰試験に上位40ペアの危険12組を加え、逆ペアの合計類似度が 0.8 を超えないことを確認する。

### 段階B: 語彙とカード(XML が変わる。再埋め込みを要する)

1. 同義の統合を `openmath_symbol_merges.json` の通りに行う。
   - 高信頼49行、中信頼55行(再書き換えや標準 CD 候補を含む)。
   - 引数順の入れ替えを伴うのは `vector_space`、`module_over`、`morphism_comp`(と `dim_of` の引数削除)。
   - `kind` が `rewrite`、`add_arg`、`std_cd_candidate`、`validator_gap` の行は単純な名前変更ではない。
   - `generic_now` の XML は検証器に通ったままでなければならない。生成後に再検証する。
2. 命名と受け入れの規則を `AUTHORING.md` に加える。
   - 同じ概念に名前を2つ作らない。統合時は使用数が多い綴りを残し、新規記号には `is_` 接頭辞を付けない。
   - arity 2以上の記号は、引数順を意味文に必ず書く(現状 409/634 が未記載)。
   - 新規記号は、2カード以上が使うか、教科書の定義語であること。単独使用の記号は、原子の合成なら展開する。
   - 命題の合成(複数の述語の連言、量化を含む式、特定の図形配置)を記号にしない。担体ごとの派生(`group_kernel` と `ring_kernel`)は、担体を引数や構造述語で表せるなら作らない。
   - 同名記号は全ファイルで同一の意味と引数順にする。`exact_pair`、`measurable_set`、`norm` などは分割するか意味を揃える。
   - 述語を引数に取るときは、term として渡さず、lambda(predicate_function)を許す方向で検証器の側を直す。
3. 担体と構造の守りを規約にする(現行プロファイルで書ける形)。
   - 非ℝの束縛変数には、担体を示す原子式を1つ必ず付ける: `(in x N|Z|Q|C)`、または構造述語(`group`、`comm_ring`、`field`、`vector_space_over`、`module_over`、`metric_space`、`inner_product_space_over` など)。
   - ℝも明示する(「守りなし=ℝ」を廃止する)。ただし ℝ の守りは全カードに同じ形で入るため、特徴が増える。段階Aで守り原子を専用の特徴族に分けて扱う。
   - 無意味な `(in (size ..) N)` は削る(81カード)。
   - 語彙に足りない構造述語は少数(`topological_space`、`measurable_space`)で、`instance_of` のような新記号は要らない。既存の単項述語を「構造述語」として指定して使う。
   - 次元や型クラスの追加仮定(平面、`RCLike`)は、対応する述語を付けるか、カードの `hard_negative` に明記する。
4. 重複カード5組を整理する(#4、#5、#20、#22、#38)。
5. η展開を減らす。同概念の項版と関数版を一本化し、`f` をそのまま渡せる項の sort を残す(F6の対応表)。

### 段階C: 次の正規化バージョン(v5)で検討

- バインダに担体を OMATTR/OMATP で付ける。守り原子が特徴を水増しする問題を避けられる。
  - 必要な変更: 検索プロファイルが OMBVAR 内の OMATTR を許す。v4 のベクトルとダイジェストを v5 で更新する。標準の型付け記号(OpenMath の `sts` CD。記憶による、要確認)か `pals2:type` を使う。
  - alpha 正規化器と特徴抽出は OMATTR を既に扱える。
  - 段階Bの規約が測定で不足と分かった場合のみ着手する。
- `defint`/`diff` に lambda 引数の sort を登録し、`interval_integral`(46件)と `has_deriv_at`(72件)を標準側へ寄せる。
- 順序: 段階A、段階Bを先に行い、段階Cは測定後に決める。

### 効果の見込みと未検証

- 段階Aの効果は上表の通り測定済み(合成の試作、実クエリでは未検証)。
- 段階Bの統合は件数のみ集計した。統合後の検索品質は未測定。
- 埋め込み側の影響と、構造化 LLM が `pals2` 記号をどれだけ当てるかは、実クエリの再現試験が要る。依頼の方針(実モデル検証は最小回数)に合わせ、まず小さな回帰セットで見る。

## 成果物

`$SP` は /private/tmp/claude-501/-Users-atsushi-Desktop-projects-personal-pals--claude-worktrees-draft-recipe-db-validation-8266ed/18beff06-3d00-48be-ba91-9ec6efea5ea4/scratchpad。

- `$SP/out/openmath_format_audit.md`(本書)
- `$SP/out/openmath_symbol_merges.json`(104行。キーは `from`、`to`、`reason`、`confidence`。任意キー: `kind`、`arg_permutation`、`cards_affected`、`verified_in_repo`)
- スクリプト: `$SP/work/openmath/`
  - `common.py`: 読み込みと Lean 束縛の解析
  - `a1_symbols.py`、`merges_table.py`: 記号の整理と統合表
  - `a2_similarity.py`: 全ペア類似度
  - `a3_reverse.py`、`a3b_surface.py`: 逆方向と表面形
  - `a4_binders.py`、`a5_typing.py`、`a6_carrier_pairs.py`: 束縛と型
  - `a7c_wiring_side2.py`: 配線特徴の試作
  - `top40_table.md`: 上位40ペア
