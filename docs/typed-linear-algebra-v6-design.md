# Linear algebra v6: foundation gaps

18 件を独立 `typed-linear-algebra-v6` profile に、内積の一般反例 1 件を既存 v3 profile の独立 supplement に追加する。既存 v1–v5 manifest/validator/registry は変更しない。標準数学の章名だけを増やすのではなく、固定された foundation 契約の recognize / compute_construct / counterexample_audit / synthesize の不足に対応する。

全カードは任意の体・有限次元空間・自然数サイズを量化し、数値例の焼き直しではない。行列の自然数サイズは 0 も許す。`Fin n` の添字を要求する反例は、その型自体で空添字集合を排除する。冪零幾何級数は k=0 も許すが、その仮定 N^0=0 は非零行列環では成立しない。空サイズでは恒等式は正しく成立する。v3 supplement は x≠0 を明示して零空間の反例を誤って主張しない。

## Boundaries and semantics

v6 は v5 の閉じた依存型文法を新しい cdbase として保持し、所属・核・共通部分・座標射影・有限行列幾何級数などの演算を追加する。仮定は量化された型に含まれる Field / AddCommGroup / Module / FiniteDimensional の組であり、単なる自由テキストのヒントではない。固有ベクトル等の既存演算の意味も引き継ぐが、今回のカードは固有値章の件数を増やさない。

型の引数 `Space@i` は i 番目の引数が指定する体の空間である。Vec/Sub/Func の添字は体・空間、Lin は体・始域・終域、Mat は体・行数・列数、Family/Basis は体・空間・添字サイズを保持する。異なる束縛名の空間やサイズは nominal に区別される。IndexSize は束縛された Nat 型の変数であり、固定数値の行列サイズをこの profile へ持ち込めない。通常の Nat 引数（冪指数など）は非負整数と Nat 変数を許す。型宣言順、束縛、shadow、演算のarity、namespace、cdbase、属性を厳密に検査する。

上限は UTF-8 65,536 bytes、4,096 XML nodes、depth 64、各 binder 64 宣言、各属性値 256 文字。検証後、共通 canonicalizer で alpha 正規化する。固有名詞だけの theorem-predicate は追加していない。`complementary` / `disjoint` は部分空間の和・共通部分の標準性質で、registry が Lean の意味を明示する。

## Operator dictionary

以下は registry の全演算・型記号。署名の順番が引数の意味を定め、すべて型検査と一致する。

| Symbol | Arguments → result | Lean interpretation |
|---|---|---|
| `la6.Basis` | `Field, Space@0, IndexSize → Basis@0,1,2` | Module.Basis (Fin n) K V |
| `la6.Coordinates` | `Field, IndexSize → Coords@0,1` | Fin n → K |
| `la6.Family` | `Field, Space@0, IndexSize → Family@0,1,2` | Fin n → V |
| `la6.Field` | ` → binder/type/standard operator` | K : Type with Field K |
| `la6.FiniteDimensionalSpace` | ` → binder/type/standard operator` | V : Type with AddCommGroup V, Module K V and FiniteDimensional K V; requires one bound Field argument K |
| `la6.Functional` | `Field, Space@0 → Func@0,1` | V →ₗ[K] K |
| `la6.Index` | `IndexSize → Index@0` | Fin n; bounded index into a declared natural size |
| `la6.LinearMap` | `Field, Space@0, Space@0 → Lin@0,1,2` | V →ₗ[K] W |
| `la6.Matrix` | `Field, IndexSize, IndexSize → Mat@0,1,2` | Matrix (Fin m) (Fin n) K, row size then column size |
| `la6.Nat` | ` → binder/type/standard operator` | ℕ, including zero |
| `la6.Polynomial` | `Field → Poly@0` | Polynomial K |
| `la6.Scalar` | `Field → Scalar@0` | K |
| `la6.Subspace` | `Field, Space@0 → Sub@0,1` | Submodule K V |
| `la6.Vector` | `Field, Space@0 → Vec@0,1` | V |
| `la6.apply` | `Field, Space@0, Space@0, Lin@0,1,2, Vec@0,1 → Vec@0,2` | f x |
| `la6.basis_vectors` | `Field, Space@0, IndexSize, Basis@0,1,2 → Family@0,1,2` | fun i : Fin n => b i |
| `la6.charpoly` | `Field, Space@0, Lin@0,1,1 → Poly@0` | LinearMap.charpoly f, convention det(XI-f) |
| `la6.commute` | `Field, Space@0, Lin@0,1,1, Lin@0,1,1 → Prop` | Commute f g: f*g=g*f where product is composition |
| `la6.complementary` | `Field, Space@0, Sub@0,1, Sub@0,1 → Prop` | IsCompl S T: S⊔T=⊤ and S⊓T=⊥ |
| `la6.compose` | `Field, Space@0, Space@0, Space@0, Lin@0,1,2, Lin@0,2,3 → Lin@0,1,3` | g.comp f; first map f:V→W then g:W→U |
| `la6.construct` | `Field, Space@0, Space@0, IndexSize, Basis@0,1,3, Family@0,2,3 → Lin@0,1,2` | b.constr K v : V →ₗ[K] W; prescribed images of basis b |
| `la6.coordinate_add` | `Field, IndexSize, Coords@0,1, Coords@0,1 → Coords@0,1` | x+y, pointwise addition of equally sized coefficient vectors |
| `la6.coordinate_contains` | `Field, IndexSize, Coords@0,1, Scalar@0 → Prop` | ∃ i : Fin n, a i = z |
| `la6.coordinate_functionals` | `Field, Space@0, IndexSize, Basis@0,1,2 → FuncFamily@0,1,2` | fun i : Fin n => b.coord i, a family of K-linear functionals |
| `la6.coordinate_smul` | `Field, IndexSize, Scalar@0, Coords@0,1 → Coords@0,1` | a • x, scalar multiplication of coefficient vector |
| `la6.coordinates` | `Field, Space@0, IndexSize, Basis@0,1,2, Vec@0,1 → Coords@0,2` | fun i : Fin n => b.repr x i; equivalently b.equivFun x |
| `la6.diagonal` | `Field, IndexSize, Coords@0,1 → Mat@0,1,1` | Matrix.diagonal a |
| `la6.diagonal_map` | `Field, Space@0, IndexSize, Basis@0,1,2, Coords@0,2 → Lin@0,1,1` | Matrix.toLin b b (Matrix.diagonal a) |
| `la6.eigenbasis` | `Field, Space@0, IndexSize, Lin@0,1,1, Basis@0,1,2, Coords@0,2 → Prop` | ∀ i : Fin n, f (b i) = a i • b i; b is a Basis so each b i is nonzero |
| `la6.eigenspace` | `Field, Space@0, Lin@0,1,1, Scalar@0 → Sub@0,1` | Module.End.eigenspace f a |
| `la6.eigenspaces_sup` | `Field, Space@0, Lin@0,1,1 → Sub@0,1` | ⨆ a : K, Module.End.eigenspace f a; supremum of subspaces, not a set union |
| `la6.family_images` | `Field, Space@0, Space@0, IndexSize, Lin@0,1,2, Family@0,1,3 → Family@0,2,3` | fun i => f (v i) |
| `la6.functional_independent` | `Field, Space@0, IndexSize, FuncFamily@0,1,2 → Prop` | LinearIndependent K phi where phi : Fin n → (V →ₗ[K] K) |
| `la6.functional_sum` | `Field, Space@0, IndexSize, FuncFamily@0,1,2, Coords@0,2 → Func@0,1` | ∑ i : Fin n, a i • phi i; functional family precedes coefficients |
| `la6.functional_values` | `Field, Space@0, IndexSize, Func@0,1, Family@0,1,2 → Coords@0,2` | fun i : Fin n => phi (v i) |
| `la6.has_eigenvalue` | `Field, Space@0, Lin@0,1,1, Scalar@0 → Prop` | Module.End.HasEigenvalue f a: eigenspace f a is nonzero |
| `la6.has_eigenvector` | `Field, Space@0, Lin@0,1,1, Scalar@0, Vec@0,1 → Prop` | Module.End.HasEigenvector f a x: f x=a • x and x≠0 |
| `la6.identity` | `Field, Space@0 → Lin@0,1,1` | LinearMap.id |
| `la6.independent` | `Field, Space@0, IndexSize, Family@0,1,2 → Prop` | LinearIndependent K v |
| `la6.injective` | `Field, Space@0, Space@0, Lin@0,1,2 → Prop` | Function.Injective f |
| `la6.linear_factor_product` | `Field, IndexSize, Coords@0,1 → Poly@0` | ∏ i, (Polynomial.X - Polynomial.C (a i)) |
| `la6.map_add` | `Field, Space@0, Space@0, Lin@0,1,2, Lin@0,1,2 → Lin@0,1,2` | f+g |
| `la6.map_smul` | `Field, Space@0, Space@0, Scalar@0, Lin@0,1,2 → Lin@0,1,2` | a • f |
| `la6.matrix_add` | `Field, IndexSize, IndexSize, Mat@0,1,2, Mat@0,1,2 → Mat@0,1,2` | A+B |
| `la6.matrix_det` | `Field, IndexSize, Mat@0,1,1 → Scalar@0` | Matrix.det A |
| `la6.matrix_identity` | `Field, IndexSize → Mat@0,1,1` | identity matrix |
| `la6.matrix_mul` | `Field, IndexSize, IndexSize, IndexSize, Mat@0,1,2, Mat@0,2,3 → Mat@0,1,3` | A*B with row/inner/column sizes specified |
| `la6.matrix_single` | `Field, IndexSize, IndexSize, Index@1, Index@2, Scalar@0 → Mat@0,1,2` | Matrix.single i j a: a at row i, column j, zero elsewhere |
| `la6.matrix_smul` | `Field, IndexSize, IndexSize, Scalar@0, Mat@0,1,2 → Mat@0,1,2` | a • A |
| `la6.matrix_vec` | `Field, IndexSize, IndexSize, Mat@0,1,2, Coords@0,2 → Coords@0,1` | A.mulVec x |
| `la6.matrix_zero` | `Field, IndexSize, IndexSize → Mat@0,1,2` | zero matrix of the specified row and column sizes |
| `la6.minpoly` | `Field, Space@0, Lin@0,1,1 → Poly@0` | minpoly K f |
| `la6.poly_aeval` | `Field, Space@0, Lin@0,1,1, Poly@0 → Lin@0,1,1` | Polynomial.aeval f P : V →ₗ[K] V |
| `la6.poly_divides` | `Field, Poly@0, Poly@0 → Prop` | P ∣ Q in Polynomial K, first polynomial divides the second |
| `la6.poly_eval` | `Field, Poly@0, Scalar@0 → Scalar@0` | P.eval a |
| `la6.poly_root` | `Field, Poly@0, Scalar@0 → Prop` | P.IsRoot a, equivalently P.eval a=0 |
| `la6.range` | `Field, Space@0, Space@0, Lin@0,1,2 → Sub@0,2` | LinearMap.range f |
| `la6.row` | `Field, IndexSize, IndexSize, Mat@0,1,2, Index@1 → Coords@0,2` | A i : Fin n → K, where A has m rows and n columns |
| `la6.row_update` | `Field, IndexSize, IndexSize, Mat@0,1,2, Index@1, Coords@0,2 → Mat@0,1,2` | Matrix.updateRow A i r; replace row i by r |
| `la6.scalar_mul` | `Field, Scalar@0, Scalar@0 → Scalar@0` | a*b in K |
| `la6.scalar_neg` | `Field, Scalar@0 → Scalar@0` | -a in K |
| `la6.scalar_one` | `Field → Scalar@0` | (1 : K) |
| `la6.scalar_zero` | `Field → Scalar@0` | (0 : K) |
| `la6.span` | `Field, Space@0, IndexSize, Family@0,1,2 → Sub@0,1` | Submodule.span K (Set.range v) |
| `la6.sub_le` | `Field, Space@0, Sub@0,1, Sub@0,1 → Prop` | S≤T |
| `la6.sub_map` | `Field, Space@0, Space@0, Lin@0,1,2, Sub@0,1 → Sub@0,2` | S.map f |
| `la6.sub_top` | `Field, Space@0 → Sub@0,1` | (⊤ : Submodule K V) |
| `la6.sum_scaled` | `Field, Space@0, IndexSize, Family@0,1,2, Coords@0,2 → Vec@0,1` | ∑ i, a i • v i; family before coefficient family |
| `la6.surjective` | `Field, Space@0, Space@0, Lin@0,1,2 → Prop` | Function.Surjective f |
| `la6.to_matrix` | `Field, Space@0, Space@0, IndexSize, IndexSize, Basis@0,1,3, Basis@0,2,4, Lin@0,1,2 → Mat@0,4,3` | LinearMap.toMatrix b c f; source basis b (n entries), target basis c (m entries), result m×n |
| `la6.transition` | `Field, Space@0, IndexSize, IndexSize, Basis@0,1,2, Basis@0,1,3 → Mat@0,2,3` | b.toMatrix c; columns are c-vectors in b-coordinates, converts coordinates in c into coordinates in b |
| `la6.transvection` | `Field, IndexSize, Index@1, Index@1, Scalar@0 → Mat@0,1,1` | Matrix.transvection i j a = 1 + Matrix.single i j a; i and j are row indices, valid without i≠j (theorems specify the hypothesis) |
| `la6.vector_smul` | `Field, Space@0, Scalar@0, Vec@0,1 → Vec@0,1` | a • x |
| `la6.zero_map` | `Field, Space@0, Space@0 → Lin@0,1,2` | (0 : V →ₗ[K] W) |
| `typed1.forall` | ` → binder/type/standard operator` | universal typed binder |
| `typed1.exists` | ` → binder/type/standard operator` | existential typed binder |
| `typed1.type` | ` → binder/type/standard operator` | bound declaration type only |
| `logic1.and` | ` → binder/type/standard operator` | P∧Q |
| `logic1.or` | ` → binder/type/standard operator` | P∨Q |
| `logic1.implies` | ` → binder/type/standard operator` | P→Q |
| `logic1.not` | ` → binder/type/standard operator` | ¬P |
| `relation1.eq` | ` → binder/type/standard operator` | equality of matching dependent value types |
| `relation1.neq` | ` → binder/type/standard operator` | inequality of matching dependent value types |
| `relation1.leq` | ` → binder/type/standard operator` | ≤ on ℕ only |
| `relation1.lt` | ` → binder/type/standard operator` | < on ℕ only |
| `arith1.plus` | ` → binder/type/standard operator` | addition of matching naturals or matching field scalars |
| `la6.vector_zero` | `Field, Space@0 → Vec@0,1` | (0 : V) |
| `la6.vector_add` | `Field, Space@0, Vec@0,1, Vec@0,1 → Vec@0,1` | x+y in V |
| `la6.vector_sub` | `Field, Space@0, Vec@0,1, Vec@0,1 → Vec@0,1` | x-y in V |
| `la6.member` | `Field, Space@0, Vec@0,1, Sub@0,1 → Prop` | x ∈ S, vector before subspace |
| `la6.kernel` | `Field, Space@0, Space@0, Lin@0,1,2 → Sub@0,1` | LinearMap.ker f, a subspace of the source |
| `la6.sub_inf` | `Field, Space@0, Sub@0,1, Sub@0,1 → Sub@0,1` | S ⊓ T |
| `la6.sub_sup` | `Field, Space@0, Sub@0,1, Sub@0,1 → Sub@0,1` | S ⊔ T, the subspace sum |
| `la6.sub_bot` | `Field, Space@0 → Sub@0,1` | (⊥ : Submodule K V) |
| `la6.disjoint` | `Field, Space@0, Sub@0,1, Sub@0,1 → Prop` | Disjoint S T, equivalently S ⊓ T = ⊥ |
| `la6.functional_apply` | `Field, Space@0, Func@0,1, Vec@0,1 → Scalar@0` | phi x |
| `la6.family_at` | `Field, Space@0, IndexSize, Family@0,1,2, Index@2 → Vec@0,1` | v i |
| `la6.family_update` | `Field, Space@0, IndexSize, Family@0,1,2, Index@2, Vec@0,1 → Family@0,1,2` | Function.update v i x |
| `la6.coordinate_at` | `Field, IndexSize, Coords@0,1, Index@1 → Scalar@0` | a i |
| `la6.coordinate_zero` | `Field, IndexSize → Coords@0,1` | (0 : Fin n → K) |
| `la6.basis_projection` | `Field, Space@0, IndexSize, Basis@0,1,2, Index@2 → Lin@0,1,1` | (b.coord i).smulRight (b i): the linear map x ↦ b.coord i x • b i |
| `la6.matrix_pow` | `Field, IndexSize, Mat@0,1,1, Nat → Mat@0,1,1` | A^k for arbitrary natural k, with A^0=1 |
| `la6.matrix_geom_sum` | `Field, IndexSize, Mat@0,1,1, Nat → Mat@0,1,1` | ∑ j ∈ Finset.range k, A^j; empty sum at k=0 is zero |
| `la6.matrix_sub` | `Field, IndexSize, IndexSize, Mat@0,1,2, Mat@0,1,2 → Mat@0,1,2` | A-B |
| `la6.matrix_isunit` | `Field, IndexSize, Mat@0,1,1 → Prop` | IsUnit A in the square matrix algebra, equivalently invertibility |

## Curriculum binding recommendations

別ファイル `linear-algebra-v6-foundation-binding-proposals.json` が全 19 件の推薦と判断根拠を記録する。親の独立内容審査・対応付け後にのみ監査結果へ反映する。advanced は長い Lean 証明の意味ではなく、複数の数学概念を統合する教科書上の応用問題として推薦する。冪等核像分解などを標準問題と判定するカリキュラムでは難度を下げ、その場合の不足は隠さず残す。

| Card | Chapter | Mode | Difficulty |
|---|---|---|---|
| `la_v6_fredholm_solvability` | univ.linear.systems | recognize | advanced |
| `la_v6_kernel_causes_nonunique_solutions` | univ.linear.systems | counterexample_audit | standard |
| `la_v6_left_inverse_detects_injective_action` | univ.linear.matrices | recognize | standard |
| `la_v6_matrix_units_noncommute` | univ.linear.matrices | counterexample_audit | standard |
| `la_v6_nilpotent_geometric_inverse` | univ.linear.matrices | synthesize | advanced |
| `la_v6_subspace_sum_membership` | univ.linear.subspaces | recognize | standard |
| `la_v6_incomparable_union_not_closed` | univ.linear.subspaces | counterexample_audit | standard |
| `la_v6_injective_images_preserve_intersection` | univ.linear.subspaces | synthesize | standard |
| `la_v6_independence_zero_coefficients` | univ.linear.span-independence | recognize | standard |
| `la_v6_span_construct_coefficients` | univ.linear.span-independence | compute_construct | standard |
| `la_v6_repeated_vector_dependence` | univ.linear.span-independence | counterexample_audit | introductory |
| `la_v6_independence_under_restricted_injection` | univ.linear.span-independence | synthesize | advanced |
| `la_v6_basis_recognition` | univ.linear.basis-dimension | recognize | standard |
| `la_v6_zeroing_basis_vector_loses_span` | univ.linear.basis-dimension | counterexample_audit | standard |
| `la_v6_nonzero_translation_not_linear` | univ.linear.maps | counterexample_audit | introductory |
| `la_v6_nonzero_maps_zero_composite` | univ.linear.kernel-image-rank | counterexample_audit | standard |
| `la_v6_idempotent_kernel_range_decomposition` | univ.linear.kernel-image-rank | synthesize | advanced |
| `la_v6_rectangular_determinant_transfer` | univ.linear.determinant | synthesize | advanced |
| `la_v3_nonadditive_norm_family` | univ.linear.inner-product | counterexample_audit | introductory |

## Evidence and limitations

Generators compile the exact marked Lean bundle against the existing pinned workspace before emitting JSON. Evidence records full witness bytes, independent validator and registry hashes, toolchain, and Mathlib revision. No sorry/admit/axiom is permitted. Tests verify all XML, all evidence pins, type/carrier errors, bounded grammar and 1:1 negative pairing. The v3 supplement is independently loadable using the unchanged v3 profile; its IDs and canonical XML are disjoint from the original v3 batch.

全 19 件に独立 hard-negative query と具体的反例または欠落仮定の理由を対にする。これは authored evidence であり retrieval test 成功を意味しない。counterexample_audit の枠には negatives ファイルだけでなく、一般パラメータの実 Lean 反例カードを対応付ける。span 係数の存在定理は計算可能性・実行速度の主張ではない。今回の完了は契約枠の充足候補であり、全教科書演習やすべての学習者の難易度を網羅したという主張ではない。runtime retrieval / PFI / publication はこの authoring 作業に含めない。
