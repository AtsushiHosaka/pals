# typed-linear-algebra-v3 authoring profile

この版は有限次元**実**内積空間の一般定理36件を表現する。任意の次元・部分空間・ベクトル・有限族を量化し、特定の行列サイズや数値例で件数を増やさない。既存v1/v2の意味とファイルは変更しない。ローカルDraft authoring用であり、runtime structuring/publication対応を宣言しない。

## 数学的な範囲

- 内積とノルム: 自己内積、Cauchy–Schwarz、Pythagorasの同値、平行四辺形、偏極、直交族の独立性、Bessel。
- 直交補空間: 包含反転、二重直交補、和の直交補、次元公式、直交直和。
- 直交射影: 分解、唯一性、固定点、冪等性、核、縮小性、補射影、入れ子、対称性、Pythagoras、ノルム等号条件、最良近似。
- Gram–Schmidt: 直交性、span保存、独立性保存、正規化、正規化後のspan、直交入力の固定。
- 正規直交基底: 展開、Parseval、内積の座標表示、座標係数、基底変換の行列式。
- 実対称作用素のスペクトル定理: Fin n正規直交固有基底と固有値を存在量化する。各固有ベクトルの非零性を含む。

これは教科書全演習の網羅を意味しない。複素Hermitian空間、SVD、極分解、QRの行列分解としての表現、二次形式の慣性法則、Jordan標準形、双対空間のテンソル的扱い、無限次元Hilbert空間は未収録。Gram–Schmidtのアルゴリズムは収録するが数値安定性の主張は扱わない。

## 型と文法

`RealInnerProductSpace` は Leanの `V : Type*`, `NormedAddCommGroup V`, `InnerProductSpace ℝ V`, `FiniteDimensional ℝ V` を同時に要求する。空間は名前に依存する名目的carrierで、二つの宣言を次元だけで同一視しない。有限次元により部分空間は完備となり、starProjectionが利用できる。実数体は固定で、複素数の共役規約は混在させない。

型引数は先行する束縛変数のみ。`VectorFamily(V,n)` は `Fin n → V`、`ScalarFamily(n)` は `Fin n → ℝ`。n=0も許す。基底の存在は型から無条件に推論せず、基底を量化したカードと、次元一致の仮定の下で基底を構成するスペクトルカードを区別する。

以下の署名は引数を左から順に記す。`@0`は第0引数のcarrier、`@0,1`は第0引数の空間と第1引数の族サイズに依存する。`Space`と`IndexSize`はそれぞれ束縛済み空間・自然数変数を要求する。引数の順序を入れ替えると、同じXML構造でも型が異なる場合は拒否する。

| 記号 | 引数の順序 → 結果型 | Leanでの意味 |
|---|---|---|
| `End` | `Space → End@0` | V →ₗ[ℝ] V |
| `Nat` | ` → sort` | ℕ; family sizes may be zero |
| `OrthonormalBasis` | `Space, IndexSize → ONBasis@0,1` | OrthonormalBasis (Fin n) ℝ V |
| `Real` | ` → sort` | ℝ |
| `RealInnerProductSpace` | ` → sort` | V : Type with NormedAddCommGroup V, InnerProductSpace ℝ V, FiniteDimensional ℝ V; nominal carrier V |
| `ScalarFamily` | `IndexSize → ScalarFamily@0` | Fin n → ℝ |
| `Subspace` | `Space → Subspace@0` | Submodule ℝ V |
| `Vector` | `Space → Vector@0` | V |
| `VectorFamily` | `Space, IndexSize → Family@0,1` | Fin n → V |
| `apply` | `Space, End@0, Vector@0 → Vector@0` | f x |
| `coefficients` | `Space, IndexSize, Family@0,1, Vector@0 → ScalarFamily@1` | fun i : Fin n => inner ℝ (v i) x |
| `coordinates` | `Space, IndexSize, ONBasis@0,1, Vector@0 → ScalarFamily@1` | fun i : Fin n => b.repr x i |
| `dim` | `Space → Nat` | Module.finrank ℝ V |
| `dot` | `IndexSize, ScalarFamily@0, ScalarFamily@0 → Real` | ∑ i : Fin n, a i * b i |
| `eigenfamily` | `Space, IndexSize, End@0, ScalarFamily@1, Family@0,1 → Prop` | ∀ i : Fin n, Module.End.HasEigenvector f (a i) (v i); explicitly f(v i)=a i •v i and v i≠0 |
| `family_nonzero` | `Space, IndexSize, Family@0,1 → Prop` | ∀ i : Fin n, v i ≠ 0 |
| `family_span` | `Space, IndexSize, Family@0,1 → Subspace@0` | Submodule.span ℝ (Set.range v) |
| `gram_schmidt` | `Space, IndexSize, Family@0,1 → Family@0,1` | InnerProductSpace.gramSchmidt ℝ v, in the natural order on Fin n |
| `gram_schmidt_normed` | `Space, IndexSize, Family@0,1 → Family@0,1` | InnerProductSpace.gramSchmidtNormed ℝ v (normalization of zero is zero) |
| `independent` | `Space, IndexSize, Family@0,1 → Prop` | LinearIndependent ℝ v |
| `inner` | `Space, Vector@0, Vector@0 → Real` | inner ℝ x y |
| `member` | `Space, Vector@0, Subspace@0 → Prop` | x ∈ S |
| `norm` | `Space, Vector@0 → Real` | ‖x‖ |
| `onbasis_vectors` | `Space, IndexSize, ONBasis@0,1 → Family@0,1` | fun i : Fin n => b i |
| `orthogonal` | `Space, Subspace@0 → Subspace@0` | Sᗮ |
| `orthogonal_family` | `Space, IndexSize, Family@0,1 → Prop` | Pairwise (fun i j => inner ℝ (v i) (v j) = 0) |
| `orthonormal` | `Space, IndexSize, Family@0,1 → Prop` | Orthonormal ℝ v |
| `projection` | `Space, Subspace@0, Vector@0 → Vector@0` | S.starProjection x (ambient V-valued orthogonal projection) |
| `real_abs` | `Real → Real` | \|a\| |
| `real_mul` | `Real, Real → Real` | a * b |
| `real_nat` | `Nat → Real` | (n : ℝ) |
| `real_neg` | `Real → Real` | -a |
| `real_square` | `Real → Real` | a ^ 2 |
| `real_sub` | `Real, Real → Real` | a - b |
| `sub_bot` | `Space → Subspace@0` | (⊥ : Submodule ℝ V) |
| `sub_dim` | `Space, Subspace@0 → Nat` | Module.finrank ℝ S |
| `sub_inf` | `Space, Subspace@0, Subspace@0 → Subspace@0` | S ⊓ T |
| `sub_le` | `Space, Subspace@0, Subspace@0 → Prop` | S ≤ T |
| `sub_sup` | `Space, Subspace@0, Subspace@0 → Subspace@0` | S ⊔ T |
| `sub_top` | `Space → Subspace@0` | (⊤ : Submodule ℝ V) |
| `sum_scaled` | `Space, IndexSize, Family@0,1, ScalarFamily@1 → Vector@0` | ∑ i : Fin n, a i • v i |
| `sum_squares` | `IndexSize, ScalarFamily@0 → Real` | ∑ i : Fin n, (a i) ^ 2 |
| `symmetric` | `Space, End@0 → Prop` | f.IsSymmetric = ∀ x y, inner ℝ (f x) y = inner ℝ x (f y) |
| `transition_det` | `Space, IndexSize, ONBasis@0,1, ONBasis@0,1 → Real` | b.toBasis.det c; determinant of matrix with columns c in coordinates of b |
| `vector_add` | `Space, Vector@0, Vector@0 → Vector@0` | x + y |
| `vector_sub` | `Space, Vector@0, Vector@0 → Vector@0` | x - y |
| `vector_zero` | `Space → Vector@0` | (0 : V) |

標準OpenMath記号は `logic1.and/or/implies/not`、`relation1.eq/neq/leq/lt`、`arith1.plus` に閉じる。等式は同一の値型のみで、carrier自体や命題の等式は許さない。大小比較・加算は両辺とも同じℕまたはℝに限定する。数値のOMIは自然数で、実数への埋め込みは `real_nat` を必須とする。`typed1.forall/exists` と `typed1.type` 以外の量化・型付けはない。量化の型は本文の命題型検査に先立って宣言順に構築する。

`projection` は部分空間に値を持つ射影ではなく ambient space に値を戻した `starProjection`。`coefficients` は任意の族に対して定義できるが、それを基底座標と同一視できるのは正規直交基底の場合。`orthogonal_family` は異なる添字間の内積が0であること、`orthonormal` はそれに単位ノルムを加えた条件。前者だけでは零ベクトルを排除しない。`eigenfamily` は固有値方程式だけの略記ではなく `HasEigenvector` を用い非零条件を含む。

## 検証の境界と証拠

validatorは64 KiB、4096 nodes、深さ64、属性値256文字を上限とする。OpenMathのnamespace、cdbase、cd、name、許可属性の完全一致を要求する。未知の記号、自由変数、名前の再宣言・shadowing、carrierや族サイズの混同、不正arity、型記号の値利用を拒否する。型検査の後に既存v4 canonicalizerを呼び、既存validatorをmonkeypatchしない。

registryには全記号の署名と意味を記録し、validatorの閉じた記号集合と一致を検証する。manifestはvalidator・registry・Lean witnessのSHA-256、実際のLean toolchain、固定mathlib revisionを保持する。generatorは単一の `import Mathlib` と各カードの自己完結exampleからなる正確なLean bundleを作り、既存local lakeで実コンパイルが成功した場合だけJSONを書き出す。証明補助のaxiom/sorry/admitはない。

型検査は命題の真理判定や自然文との自動意味同値証明ではない。カードごとに自然文・XML・Leanの仮定と結論を照合し、独立reviewを行う。36件の独立したhard-negative question/counterexampleは `linear-algebra-v3-negatives.json` に保存する。これは数学的な誤適用を防ぐためのauthoring資料であり、検索やembeddingランキングをテストしたとの主張ではない。

## 重複の考え方

基底座標の内積公式からParsevalは導け、射影分解から冪等性や最良近似も導けるが、それぞれ異なる問題の中間目標・仮定・結論を持つ。既存カードの変数名や数値を変えただけの追加ではない。正規化spanのカードは零vectorも許し、orthonormal生成のカードは独立性を要求する。仮定の有無を保持することで誤適用を防ぐ。
