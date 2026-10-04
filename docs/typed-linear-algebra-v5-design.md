# Linear algebra v5: bases, construction, coordinates and elementary operations

This authoring-only profile adds 39 distinct general proofs. It does not claim that a textbook, exercise mode or chapter is complete. Existing profiles and serving/runtime behavior remain unchanged.

## Mathematical scope

- Basis expansion and uniqueness of coefficients; existence/uniqueness of a linear map with prescribed basis images; explicit construction formula, range, injectivity and surjectivity criteria.
- Matrix representation in arbitrary source/target bases, linearity, composition, uniqueness; coordinate-change direction, composition, inverse and two-sided basis changes.
- Dual basis expansion/independence; arbitrary subspace complements; injective/surjective maps splitting over a field.
- Eigenbasis iff diagonal matrix; polynomial action on an eigenvector; roots of characteristic/minimal polynomials; minimal polynomial divisibility; commuting endomorphisms preserving eigenspaces; a common eigenbasis implies commutation; diagonal spectrum and eigenspace span.
- Elementary row addition and scaling, determinant behavior, rectangular matrix realization, elementary inverse, preservation of a whole rectangular linear system when both sides are transformed.
- Three **normal Draft cards**, not only negative fixtures, prove general counterexample patterns: nonzero square-zero off-diagonal matrix units, determinant-one nonidentity transvections, and the obstruction to an eigenbasis for any nonzero square-zero map. Their indices and coefficients are parameters; no fixed numeric matrices inflate the positive count.

All dimensions n,m,p are arbitrary natural numbers. Zero dimensions are permitted. A supplied Fin n index or a nonzero vector hypothesis naturally excludes inappropriate empty cases. K is any field, with no order, closure or characteristic restriction. Every declared abstract space includes AddCommGroup, Module K and FiniteDimensional K instances. Finite dimensionality is a common profile assumption, sometimes stronger than an individual theorem needs. Matrix-only cards retain the harmless universally bound abstract-space context used by the exact Lean target and XML alike.

## Closed dependent grammar

The exact cdbase is `urn:pals:openmath:typed-linear-algebra:v5`; mathematical symbols use `la5`, typed binders use `typed1`. Standard symbols use exactly `http://www.openmath.org/cd`. OpenMath namespace is exactly `http://www.openmath.org/OpenMath` and OMOBJ version is 2.0.

`Field` and `Nat` are atomic declaration sorts. `FiniteDimensionalSpace(K)` declares a new nominal carrier with the above Lean instances. All other constructors below require previously bound field/space/size arguments. An `Index(n)` is Fin n, while `Coordinates(K,n)` is a whole function Fin n→K; neither is conflated with a vector in an unrelated abstract space. Nominal field, source/target space and index-size identities propagate through every operator.

Signatures below use zero-based argument positions. `Space@i` refers to a space over the field in position i; `Vec@i,j`, `Sub@i,j`, `Lin@i,j,k` denote a vector, subspace or linear map over that field and the stated carriers. `Mat@i,j,k` denotes row/column sizes in positions j,k. `Basis/Family/FuncFamily@i,j,k` denote a basis/vector family/functional family on carrier j with index size k. `Coords@i,j`, `Index@j`, `Scalar@i`, `Poly@i`, `Func@i,j` retain their respective dependent roles. These signature annotations are interpreted internally and are not accepted as XML text.

Binders are sequentially checked, closed, and cannot shadow outer variables. Propositions are explicit logic1 connectives over typed equality/inequality and mathematical predicates. `eigenbasis` means the explicit equation for every basis vector; it is not a theorem identifier. A basis already guarantees independence, spanning and nonzero basis vectors. `has_eigenvector` additionally requires a nonzero vector. `eigenspaces_sup` is a subspace supremum, not a set union. `transition(b,c)` converts c-coordinates to b-coordinates. These distinctions are preserved in the Lean targets, sketches and negative fixtures.

Limits: 65,536 UTF-8 bytes, 4,096 XML nodes, depth 64, 256 characters per attribute, at most 64 declarations per binder. Every tag has an exact attribute set. Unknown tags/symbols/cdbases, mixed carriers, malformed/missing/extra arguments, free/shadowed variables, arbitrary theorem-name predicates and mathematical values used as carrier declarations are rejected before canonicalization. OMI is a nonnegative canonical natural below one billion; arbitrary field scalar literals are not inferred. Ordered field comparisons are not in the grammar. Equality cannot compare carrier declarations or propositions.

The new module exports the exact canonicalize/validate names for v5. It uses the existing alpha-aware v4 OpenMath normalization after its own shape and type validation. No global monkeypatch, profile replacement or loader/runtime registration is performed here.

## Operator/type dictionary

| Symbol | Ordered arguments | Result | Lean meaning |
|---|---|---|---|
| `Basis` | `Field`, `Space@0`, `IndexSize` | `Basis@0,1,2` | Module.Basis (Fin n) K V |
| `Coordinates` | `Field`, `IndexSize` | `Coords@0,1` | Fin n → K |
| `Family` | `Field`, `Space@0`, `IndexSize` | `Family@0,1,2` | Fin n → V |
| `Field` |  | `declaration sort` | K : Type with Field K |
| `FiniteDimensionalSpace` |  | `declaration sort` | V : Type with AddCommGroup V, Module K V and FiniteDimensional K V; requires one bound Field argument K |
| `Functional` | `Field`, `Space@0` | `Func@0,1` | V →ₗ[K] K |
| `Index` | `IndexSize` | `Index@0` | Fin n; bounded index into a declared natural size |
| `LinearMap` | `Field`, `Space@0`, `Space@0` | `Lin@0,1,2` | V →ₗ[K] W |
| `Matrix` | `Field`, `IndexSize`, `IndexSize` | `Mat@0,1,2` | Matrix (Fin m) (Fin n) K, row size then column size |
| `Nat` |  | `declaration sort` | ℕ, including zero |
| `Polynomial` | `Field` | `Poly@0` | Polynomial K |
| `Scalar` | `Field` | `Scalar@0` | K |
| `Subspace` | `Field`, `Space@0` | `Sub@0,1` | Submodule K V |
| `Vector` | `Field`, `Space@0` | `Vec@0,1` | V |
| `apply` | `Field`, `Space@0`, `Space@0`, `Lin@0,1,2`, `Vec@0,1` | `Vec@0,2` | f x |
| `basis_vectors` | `Field`, `Space@0`, `IndexSize`, `Basis@0,1,2` | `Family@0,1,2` | fun i : Fin n => b i |
| `charpoly` | `Field`, `Space@0`, `Lin@0,1,1` | `Poly@0` | LinearMap.charpoly f, convention det(XI-f) |
| `commute` | `Field`, `Space@0`, `Lin@0,1,1`, `Lin@0,1,1` | `Prop` | Commute f g: f*g=g*f where product is composition |
| `complementary` | `Field`, `Space@0`, `Sub@0,1`, `Sub@0,1` | `Prop` | IsCompl S T: S⊔T=⊤ and S⊓T=⊥ |
| `compose` | `Field`, `Space@0`, `Space@0`, `Space@0`, `Lin@0,1,2`, `Lin@0,2,3` | `Lin@0,1,3` | g.comp f; first map f:V→W then g:W→U |
| `construct` | `Field`, `Space@0`, `Space@0`, `IndexSize`, `Basis@0,1,3`, `Family@0,2,3` | `Lin@0,1,2` | b.constr K v : V →ₗ[K] W; prescribed images of basis b |
| `coordinate_add` | `Field`, `IndexSize`, `Coords@0,1`, `Coords@0,1` | `Coords@0,1` | x+y, pointwise addition of equally sized coefficient vectors |
| `coordinate_contains` | `Field`, `IndexSize`, `Coords@0,1`, `Scalar@0` | `Prop` | ∃ i : Fin n, a i = z |
| `coordinate_functionals` | `Field`, `Space@0`, `IndexSize`, `Basis@0,1,2` | `FuncFamily@0,1,2` | fun i : Fin n => b.coord i, a family of K-linear functionals |
| `coordinate_smul` | `Field`, `IndexSize`, `Scalar@0`, `Coords@0,1` | `Coords@0,1` | a • x, scalar multiplication of coefficient vector |
| `coordinates` | `Field`, `Space@0`, `IndexSize`, `Basis@0,1,2`, `Vec@0,1` | `Coords@0,2` | fun i : Fin n => b.repr x i; equivalently b.equivFun x |
| `diagonal` | `Field`, `IndexSize`, `Coords@0,1` | `Mat@0,1,1` | Matrix.diagonal a |
| `diagonal_map` | `Field`, `Space@0`, `IndexSize`, `Basis@0,1,2`, `Coords@0,2` | `Lin@0,1,1` | Matrix.toLin b b (Matrix.diagonal a) |
| `eigenbasis` | `Field`, `Space@0`, `IndexSize`, `Lin@0,1,1`, `Basis@0,1,2`, `Coords@0,2` | `Prop` | ∀ i : Fin n, f (b i) = a i • b i; b is a Basis so each b i is nonzero |
| `eigenspace` | `Field`, `Space@0`, `Lin@0,1,1`, `Scalar@0` | `Sub@0,1` | Module.End.eigenspace f a |
| `eigenspaces_sup` | `Field`, `Space@0`, `Lin@0,1,1` | `Sub@0,1` | ⨆ a : K, Module.End.eigenspace f a; supremum of subspaces, not a set union |
| `family_images` | `Field`, `Space@0`, `Space@0`, `IndexSize`, `Lin@0,1,2`, `Family@0,1,3` | `Family@0,2,3` | fun i => f (v i) |
| `functional_independent` | `Field`, `Space@0`, `IndexSize`, `FuncFamily@0,1,2` | `Prop` | LinearIndependent K phi where phi : Fin n → (V →ₗ[K] K) |
| `functional_sum` | `Field`, `Space@0`, `IndexSize`, `FuncFamily@0,1,2`, `Coords@0,2` | `Func@0,1` | ∑ i : Fin n, a i • phi i; functional family precedes coefficients |
| `functional_values` | `Field`, `Space@0`, `IndexSize`, `Func@0,1`, `Family@0,1,2` | `Coords@0,2` | fun i : Fin n => phi (v i) |
| `has_eigenvalue` | `Field`, `Space@0`, `Lin@0,1,1`, `Scalar@0` | `Prop` | Module.End.HasEigenvalue f a: eigenspace f a is nonzero |
| `has_eigenvector` | `Field`, `Space@0`, `Lin@0,1,1`, `Scalar@0`, `Vec@0,1` | `Prop` | Module.End.HasEigenvector f a x: f x=a • x and x≠0 |
| `identity` | `Field`, `Space@0` | `Lin@0,1,1` | LinearMap.id |
| `independent` | `Field`, `Space@0`, `IndexSize`, `Family@0,1,2` | `Prop` | LinearIndependent K v |
| `injective` | `Field`, `Space@0`, `Space@0`, `Lin@0,1,2` | `Prop` | Function.Injective f |
| `linear_factor_product` | `Field`, `IndexSize`, `Coords@0,1` | `Poly@0` | ∏ i, (Polynomial.X - Polynomial.C (a i)) |
| `map_add` | `Field`, `Space@0`, `Space@0`, `Lin@0,1,2`, `Lin@0,1,2` | `Lin@0,1,2` | f+g |
| `map_smul` | `Field`, `Space@0`, `Space@0`, `Scalar@0`, `Lin@0,1,2` | `Lin@0,1,2` | a • f |
| `matrix_add` | `Field`, `IndexSize`, `IndexSize`, `Mat@0,1,2`, `Mat@0,1,2` | `Mat@0,1,2` | A+B |
| `matrix_det` | `Field`, `IndexSize`, `Mat@0,1,1` | `Scalar@0` | Matrix.det A |
| `matrix_identity` | `Field`, `IndexSize` | `Mat@0,1,1` | identity matrix |
| `matrix_mul` | `Field`, `IndexSize`, `IndexSize`, `IndexSize`, `Mat@0,1,2`, `Mat@0,2,3` | `Mat@0,1,3` | A*B with row/inner/column sizes specified |
| `matrix_single` | `Field`, `IndexSize`, `IndexSize`, `Index@1`, `Index@2`, `Scalar@0` | `Mat@0,1,2` | Matrix.single i j a: a at row i, column j, zero elsewhere |
| `matrix_smul` | `Field`, `IndexSize`, `IndexSize`, `Scalar@0`, `Mat@0,1,2` | `Mat@0,1,2` | a • A |
| `matrix_vec` | `Field`, `IndexSize`, `IndexSize`, `Mat@0,1,2`, `Coords@0,2` | `Coords@0,1` | A.mulVec x |
| `matrix_zero` | `Field`, `IndexSize`, `IndexSize` | `Mat@0,1,2` | zero matrix of the specified row and column sizes |
| `minpoly` | `Field`, `Space@0`, `Lin@0,1,1` | `Poly@0` | minpoly K f |
| `poly_aeval` | `Field`, `Space@0`, `Lin@0,1,1`, `Poly@0` | `Lin@0,1,1` | Polynomial.aeval f P : V →ₗ[K] V |
| `poly_divides` | `Field`, `Poly@0`, `Poly@0` | `Prop` | P ∣ Q in Polynomial K, first polynomial divides the second |
| `poly_eval` | `Field`, `Poly@0`, `Scalar@0` | `Scalar@0` | P.eval a |
| `poly_root` | `Field`, `Poly@0`, `Scalar@0` | `Prop` | P.IsRoot a, equivalently P.eval a=0 |
| `range` | `Field`, `Space@0`, `Space@0`, `Lin@0,1,2` | `Sub@0,2` | LinearMap.range f |
| `row` | `Field`, `IndexSize`, `IndexSize`, `Mat@0,1,2`, `Index@1` | `Coords@0,2` | A i : Fin n → K, where A has m rows and n columns |
| `row_update` | `Field`, `IndexSize`, `IndexSize`, `Mat@0,1,2`, `Index@1`, `Coords@0,2` | `Mat@0,1,2` | Matrix.updateRow A i r; replace row i by r |
| `scalar_mul` | `Field`, `Scalar@0`, `Scalar@0` | `Scalar@0` | a*b in K |
| `scalar_neg` | `Field`, `Scalar@0` | `Scalar@0` | -a in K |
| `scalar_one` | `Field` | `Scalar@0` | (1 : K) |
| `scalar_zero` | `Field` | `Scalar@0` | (0 : K) |
| `span` | `Field`, `Space@0`, `IndexSize`, `Family@0,1,2` | `Sub@0,1` | Submodule.span K (Set.range v) |
| `sub_le` | `Field`, `Space@0`, `Sub@0,1`, `Sub@0,1` | `Prop` | S≤T |
| `sub_map` | `Field`, `Space@0`, `Space@0`, `Lin@0,1,2`, `Sub@0,1` | `Sub@0,2` | S.map f |
| `sub_top` | `Field`, `Space@0` | `Sub@0,1` | (⊤ : Submodule K V) |
| `sum_scaled` | `Field`, `Space@0`, `IndexSize`, `Family@0,1,2`, `Coords@0,2` | `Vec@0,1` | ∑ i, a i • v i; family before coefficient family |
| `surjective` | `Field`, `Space@0`, `Space@0`, `Lin@0,1,2` | `Prop` | Function.Surjective f |
| `to_matrix` | `Field`, `Space@0`, `Space@0`, `IndexSize`, `IndexSize`, `Basis@0,1,3`, `Basis@0,2,4`, `Lin@0,1,2` | `Mat@0,4,3` | LinearMap.toMatrix b c f; source basis b (n entries), target basis c (m entries), result m×n |
| `transition` | `Field`, `Space@0`, `IndexSize`, `IndexSize`, `Basis@0,1,2`, `Basis@0,1,3` | `Mat@0,2,3` | b.toMatrix c; columns are c-vectors in b-coordinates, converts coordinates in c into coordinates in b |
| `transvection` | `Field`, `IndexSize`, `Index@1`, `Index@1`, `Scalar@0` | `Mat@0,1,1` | Matrix.transvection i j a = 1 + Matrix.single i j a; i and j are row indices, valid without i≠j (theorems specify the hypothesis) |
| `vector_smul` | `Field`, `Space@0`, `Scalar@0`, `Vec@0,1` | `Vec@0,1` | a • x |
| `zero_map` | `Field`, `Space@0`, `Space@0` | `Lin@0,1,2` | (0 : V →ₗ[K] W) |

## Evidence and verification

`generate-linear-algebra-v5-batch.py` validates every canonical XML, checks distinct canonical bytes and 4–10 sketch steps, writes the exact marked example bundle, and compiles it with the pinned existing local Lake toolchain before emitting any manifest. The manifest pins the Lean source, validator and registry SHA-256 bytes, Lean toolchain and mathlib revision. No sorry, admit, axiom or fabricated compiler result is used. The bundle is only `import Mathlib` followed by independently scoped marked examples; there are no extra global assumptions or helper axioms.

The unit suite checks representative carrier, basis, matrix orientation, functional, polynomial, scalar/index roles; malformed XML and namespace handling; bounds; canonical alpha-renaming and exact byte validation; all 39 manifest cards and evidence hashes; and one-to-one negative fixture pairing. The 39 independent negative queries are authored counterexamples/missing-premise explanations. They have **not** been measured through retrieval or promoted to a claim of retrieval robustness. Three general counterexample families have their own independently Lean-checked positive Draft entries, separately from this fixture set.

## Remaining first-year gaps

This slice improves construct/recognize/counterexample coverage but does not close the exercise inventory. Still absent are a full Gaussian-elimination/RREF algorithm and uniqueness proof, general echelon pivot and augmented-rank solvability classification, constructive free-variable parameterization of all solutions, row swaps and rank-preservation chains as explicit exercise steps, extensive spanning-set basis extraction/extension constructions, Jordan/minimal-polynomial diagonalizability criteria, and multi-step worked solution generation with independently tested retrieval. Dual basis formulas and split-existence results prove mathematics; they are not a user-facing solver implementation.
