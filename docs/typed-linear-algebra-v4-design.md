# typed-linear-algebra-v4: arbitrary-size matrices

任意の体Kと自然数m,n,pを量化した行列の一般定理34件。固定2×2行列の数値演習ではない。既存v1の数値行列、v2の抽象線形写像のrank-nullity/行列式の合成・scalar-degree、v3の実内積空間の各validatorとregistryは変更しない。本profileはDraft authoring用で、runtime structuring、XML→Lean自動翻訳、公開配信を新たに対応したとは主張しない。

## 数学的な内容

15件の行列式・随伴行列・逆行列・一般線形方程式/Cramer、5件の行列階数、10件の特性多項式/Cayley–Hamilton/冪零、4件のtrace/相似不変量/行列の作用を収録する。直交性に限らない任意の体、任意の標数が対象である。

- `Matrix(K,m,n)` は `Matrix (Fin m) (Fin n) K`。mは行数、nは列数。行列積は内側の次元が一致したときのみ許す。
- 全サイズは束縛された自然数変数。0も許す。空行列のdet=1、χ=1、rank=trace=0という規約を保持する。
- `inv` はMathlibのtotal nonsingular inverse。特異行列では零になり、無条件でAA⁻¹=Iとは主張しない。逆行列の積則はこの規約でも成立するが、相似変換のカードは明示的にIsUnitを仮定する。
- 特性多項式の規約はχ_A(X)=det(XI-A)。評価はスカラー評価と行列評価を別演算にする。後者はPolynomial.aeval A q。
- traceの係数公式は `nextCoeff` を使う。n=0で自然数n-1を用いて定数係数を読む誤りを避ける。
- Cramerは各列を右辺で置換した行列式のベクトル。解はそのままCramerベクトルではなく、det(A)で割ったもの。

対角化の必要十分条件、最小多項式、Jordan標準形、有理標準形、行基本変形の列としての算法、SVD、一般ブロックSchur補はこの版の未収録範囲。固有基底の十分条件はv2、実対称作用素の正規直交固有基底はv3に既にある。34件だけで線形代数全演習を網羅したとはしない。

## 閉じた依存型の署名と意味

Field宣言は名目的scalar carrier KとLeanのField Kを同時に要求する。KとLは別の型であり、同型でも自動に混ぜない。行列・ベクトル・多項式はすべてその体に依存する。`@0`は第0引数の体、`@0,1,2`は第0引数の体と第1、第2引数の行数・列数を参照する。`Field`と`IndexSize`は先行する束縛変数のみを受理する。サイズが偶然等しいという未証明推論は行わない。

| 記号 | 引数順 → 結果型 | Leanでの解釈 |
|---|---|---|
| `Field` | ` → sort` | K : Type with Field K, arbitrary characteristic |
| `Matrix` | `Field, IndexSize, IndexSize → Mat@0,1,2` | Matrix (Fin m) (Fin n) K; row dimension precedes column dimension |
| `Nat` | ` → sort` | ℕ including zero |
| `Polynomial` | `Field → Poly@0` | Polynomial K |
| `Scalar` | `Field → Scalar@0` | K |
| `Vector` | `Field, IndexSize → Vec@0,1` | Fin n → K (column coordinates) |
| `add` | `Field, IndexSize, IndexSize, Mat@0,1,2, Mat@0,1,2 → Mat@0,1,2` | A+B |
| `adjugate` | `Field, IndexSize, Mat@0,1,1 → Mat@0,1,1` | A.adjugate |
| `charpoly` | `Field, IndexSize, Mat@0,1,1 → Poly@0` | A.charpoly = det(XI-A) over Polynomial K |
| `count_nonzero` | `Field, IndexSize, Vec@0,1 → Nat` | Nat.card {i : Fin n // d i ≠ 0} |
| `cramer` | `Field, IndexSize, Mat@0,1,1, Vec@0,1 → Vec@0,1` | A.cramer y; ith coordinate det(Matrix.updateCol A i y) |
| `det` | `Field, IndexSize, Mat@0,1,1 → Scalar@0` | A.det |
| `diag_entries` | `Field, IndexSize, Mat@0,1,1 → Vec@0,1` | fun i : Fin n => A i i |
| `diagonal` | `Field, IndexSize, Vec@0,1 → Mat@0,1,1` | Matrix.diagonal d |
| `identity` | `Field, IndexSize → Mat@0,1,1` | (1 : Matrix (Fin n) (Fin n) K) |
| `inv` | `Field, IndexSize, Mat@0,1,1 → Mat@0,1,1` | Matrix nonsingular inverse A⁻¹; zero for a singular matrix |
| `is_unit` | `Field, IndexSize, Mat@0,1,1 → Prop` | IsUnit A, equivalent to a two-sided inverse |
| `linear_factor_product` | `Field, IndexSize, Vec@0,1 → Poly@0` | ∏ i : Fin n, (Polynomial.X - Polynomial.C (d i)) |
| `matrix_eval` | `Field, IndexSize, Mat@0,1,1, Poly@0 → Mat@0,1,1` | Polynomial.aeval A q; matrix argument before scalar polynomial |
| `mul` | `Field, IndexSize, IndexSize, IndexSize, Mat@0,1,2, Mat@0,2,3 → Mat@0,1,3` | A*B, left matrix m×n and right matrix n×p |
| `mul_vec` | `Field, IndexSize, IndexSize, Mat@0,1,2, Vec@0,2 → Vec@0,1` | A.mulVec x |
| `nilpotent` | `Field, IndexSize, Mat@0,1,1 → Prop` | IsNilpotent A = ∃ k : ℕ, A^k=0 |
| `poly_X` | `Field → Poly@0` | Polynomial.X : Polynomial K |
| `poly_coeff` | `Field, Poly@0, Nat → Scalar@0` | q.coeff k |
| `poly_degree` | `Field, Poly@0 → Nat` | q.natDegree; zero polynomial convention is 0 |
| `poly_eval` | `Field, Poly@0, Scalar@0 → Scalar@0` | q.eval t |
| `poly_monic` | `Field, Poly@0 → Prop` | q.Monic |
| `poly_next_coeff` | `Field, Poly@0 → Scalar@0` | q.nextCoeff; zero for constants, otherwise coefficient below leading degree |
| `poly_pow` | `Field, Poly@0, Nat → Poly@0` | q^k |
| `pow` | `Field, IndexSize, Mat@0,1,1, Nat → Mat@0,1,1` | A^k |
| `rank` | `Field, IndexSize, IndexSize, Mat@0,1,2 → Nat` | A.rank : ℕ, dimension of column span |
| `scalar_inv` | `Field, Scalar@0 → Scalar@0` | a⁻¹, with 0⁻¹=0 |
| `scalar_mul` | `Field, Scalar@0, Scalar@0 → Scalar@0` | a*b |
| `scalar_nat` | `Field, Nat → Scalar@0` | (i : K) |
| `scalar_neg` | `Field, Scalar@0 → Scalar@0` | -a |
| `scalar_pow` | `Field, Scalar@0, Nat → Scalar@0` | a^k |
| `smul` | `Field, IndexSize, IndexSize, Scalar@0, Mat@0,1,2 → Mat@0,1,2` | a • A |
| `trace` | `Field, IndexSize, Mat@0,1,1 → Scalar@0` | A.trace |
| `transpose` | `Field, IndexSize, IndexSize, Mat@0,1,2 → Mat@0,2,1` | A.transpose |
| `upper_triangular` | `Field, IndexSize, Mat@0,1,1 → Prop` | A.BlockTriangular id = ∀ i j, j<i → A i j=0 on Fin n |
| `vec_product` | `Field, IndexSize, Vec@0,1 → Scalar@0` | ∏ i : Fin n, d i |
| `vec_smul` | `Field, IndexSize, Scalar@0, Vec@0,1 → Vec@0,1` | a • x |
| `zero` | `Field, IndexSize, IndexSize → Mat@0,1,2` | (0 : Matrix (Fin m) (Fin n) K) |

標準OpenMathの論理演算はand/or/implies/not。eq/neqは同じ依存値型のみで、carrierや命題そのものの等式は禁止する。leq/ltは自然数だけで、任意の体に順序構造を捏造しない。plusは同じ自然数型または同じ体のscalar型のみ。OMIは非負整数で、体への埋め込みはscalar_natを明示する。forall/existsは型付き束縛だけを許し、前方参照・shadowingは拒否する。

三角行列性、冪零性、unit、monicは標準数学的述語として定義する。特定定理の名前だけを命題記号とする方式ではない。例えばCayley–Hamiltonはmatrix_eval(A,charpoly(A))=zeroという演算と等式を組み立てて表す。線形方程式の唯一存在はexists xとforall zによる明示的な解方程式・一意性で表す。

## 検査・証拠

validatorはv3を参考にした独立実装で、既存profileを登録し直したりmonkeypatchしたりしない。上限は65,536 bytes、4,096 nodes、深さ64、属性値256文字、1 binder当たり64宣言。namespace/cdbase/cd/name/属性集合の完全一致、既知記号、arity、依存carrier、サイズ、scalar/多項式/行列の役割を型検査した後に既存v4 canonicalizerへ渡す。registryは固定記号集合に対して検査され、metadataもmanifestハッシュで固定する。

Lean bundleは `import Mathlib` と34個の独立exampleのみ。generatorは既存local lakeと固定mathlibを使い、実コンパイル成功後にのみmanifest JSONを出す。witness/validator/registryのSHA-256、toolchain、mathlib revisionを記録する。禁止されたsorry/admit/axiomを使わない。単体テスト42件はcarrier/field/shape混同、矩形detの拒否、polynomial評価の引数順、数値型の誤用、XML境界、canonical bytes、全証拠ハッシュとnegative pairingを検査する。

34件すべてに対応する独立の数学的誤適用例を `linear-algebra-v4-negatives.json` に記録した。具体的な小行列は反例として使い、正例件数の水増しには用いない。negativeは検索やモデル選択のruntime評価済みという意味ではない。自然文/XML/Leanの意味一致は型検査だけで自動に保証できないため、別途全件のreviewを要する。

## 検証記録

34件の実Leanコンパイル成功。pytest 42件成功。Ruffとmypy成功。コンパイルにはcharpolyのdegreeに関する無害な `unnecessarySimpa` 警告が1件あるがエラーはない。hash対象を固定した後のmanifestと正確なbundle一致をテストで確認した。
