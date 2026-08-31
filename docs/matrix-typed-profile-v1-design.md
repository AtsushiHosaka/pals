# `typed-math-matrix-v1` design

## Decision

Matrices are a new explicit sibling profile, `typed-math-matrix-v1`. Nothing
is added to generic-v1, and the existing `typed-math-v1` 17-card profile is
not widened. The profile uses the same typed binder, `OMATTR` variable type,
dependent equality, resource limits, canonicalizer, and Lean-receipt rules as
[`pals-typed-math-v1-minimal-design.md`](pals-typed-math-v1-minimal-design.md).

```text
profile id: typed-math-matrix-v1
PALS CD base: urn:pals:openmath:typed-math:v1
new proposed CD: matrix1
```

`matrix1` is a PALS CD proposal, not an OpenMath standard CD. The caller must
select this profile explicitly: generic-v1, base typed-math-v1, and unknown
profiles all reject matrix XML. No database, generic seed, existing Draft,
or existing canonical bytes change.

The first subset uses only field-valued matrices with literal dimensions from
1 through 8. This covers usual 2×2/3×3 first- and second-year exercises while
keeping inference bounded and directly lowerable to `Fin m`/`Fin n` in Lean.
Symbolic dimensions, arbitrary-size matrices, row-reduction traces,
eigenvalues, and numerical approximation are deliberately excluded.

## Concrete alignment with `pals.typed-math.v1`

| Existing v1 rule | Matrix-profile consequence |
| --- | --- |
| `typed1:forall`/`exists` plus attributed OMBVAR declarations | Reuse unchanged. A matrix variable has `typed1:type(matrix1:Matrix(K,m,n))`; no matrix-only binder. |
| Exact syntactic sort equality; no subtype/coercion search | `Matrix(K,2,3)` ≠ `Matrix(K,3,2)` and `ColumnVector(K,2)` ≠ `ColumnVector(L,2)`. Every mismatch is a hard error. |
| `Field` and `Elem(K)` are dependent sorts | All coefficients name one explicitly bound `K : Field`; no implicit `Real` or cross-field conversion. |
| `typed1:nat_cast(R,n)` takes an explicit compatible ring | It is not broadened. Matrix v1 adds `matrix1:field_nat_cast(K,n)` because v1 intentionally does not silently regard `K : Field` as `CommRing`. |
| Base typed CD gate is fixed | `typed-math-v1` rejects `matrix1`; only this sibling profile enables it. |
| generic-v1 has only coarse term/proposition sorts | generic `_SUPPORTED_SYMBOLS` and `_infer_retrieval_sort` are untouched. |
| Typed XML does not prove the theorem | Admission still requires canonical XML/profile, type-CD digest, pinned Lean witness digest, and verified receipt. |

The geometry profile's `V2` is not reused. `matrix1:ColumnVector(K,n)` is a
field-indexed linear-algebra object; `V2` is a separate planar geometry sort.
A future bridge must be explicit, never a validator coercion.

## Sorts and shapes

Only in `typed-math-matrix-v1`, extend the base `SortExpr` grammar:

```text
Dimension ::= OMI(n), where 1 ≤ n ≤ 8
SortExpr ::= ...base typed-math-v1 sorts...
           | Matrix(FieldVar, Dimension, Dimension)
           | ColumnVector(FieldVar, Dimension)
```

`matrix1:Matrix(K,m,n)` and `matrix1:ColumnVector(K,n)` are valid only as
the value of `typed1:type`, not as terms. `K` must be a lexically bound
`Field`; each dimension must be an integer literal in range. No OMV,
arithmetic expression, zero, decimal, or unbounded natural number is a
dimension.

This makes each central operation exact without backtracking:

```text
Mat(K,m,n) × Mat(K,n,p) → Mat(K,m,p)
Mat(K,m,n) × Vec(K,n)   → Vec(K,m)
```

## Minimal `matrix1` signatures

`K` below is a bound `Field`, `a : Elem(K)`, and dimensions are permitted
literals. Every arity and argument type is exact.

| Symbol | Signature | Notes |
| --- | --- | --- |
| `literal` | `(K,m,n,e₁,…,eₘₙ) → Matrix(K,m,n)` | Row-major; exactly `m*n` entries, each `Elem(K)`. |
| `column_literal` | `(K,n,e₁,…,eₙ) → ColumnVector(K,n)` | Exactly `n` entries. |
| `field_nat_cast` | `(K,OMI nonnegative) → Elem(K)` | Required for numeric matrix/vector entries. |
| `zero` | `(K,m,n) → Matrix(K,m,n)` | Matrix zero. |
| `identity` | `(K,n) → Matrix(K,n,n)` | Identity. |
| `add` | `Mat(K,m,n) × Mat(K,m,n) → Mat(K,m,n)` | Addition. |
| `neg` | `Mat(K,m,n) → Mat(K,m,n)` | Subtraction is `add(A,neg(B))`. |
| `scale` | `Elem(K) × Mat(K,m,n) → Mat(K,m,n)` | Scalar multiplication. |
| `mul` | `Mat(K,m,n) × Mat(K,n,p) → Mat(K,m,p)` | Matrix product. |
| `transpose` | `Mat(K,m,n) → Mat(K,n,m)` | Transpose. |
| `determinant` | `Mat(K,n,n) → Elem(K)` | Rectangular inputs cannot type-check. |
| `rank` | `Mat(K,m,n) → Nat` | Rank over K, never an `Elem(K)`. |
| `is_inverse` | `Mat(K,n,n) × Mat(K,n,n) → Prop` | Means both products are identity. |
| `mul_vec` | `Mat(K,m,n) × Vec(K,n) → Vec(K,m)` | The `Ax` in `Ax=b`. |

`is_inverse` is intentionally a predicate, not a total `matrix_inverse(A)`.
A total inverse leaves a singular/undefined case that a separate proposition
cannot make safe. A problem asking for an inverse is expressed as
`exists B : Matrix(K,n,n). is_inverse(A,B)`. Non-square inputs reject before
semantic validation. `arith1:plus` and `arith1:times` are not overloaded for
matrices; all matrix-valued operations use `matrix1:*`.

## Complete positive XML

This 2×3 right-identity fixture exercises the typed binder/annotation form
from the base design and verifies the multiplication inner dimension 3.

```xml
<OMOBJ xmlns="http://www.openmath.org/OpenMath" version="2.0">
  <OMBIND>
    <OMS cdbase="urn:pals:openmath:typed-math:v1" cd="typed1" name="forall"/>
    <OMBVAR>
      <OMATTR><OMATP>
        <OMS cdbase="urn:pals:openmath:typed-math:v1" cd="typed1" name="type"/>
        <OMS cdbase="urn:pals:openmath:typed-math:v1" cd="algebra1" name="Field"/>
      </OMATP><OMV name="K"/></OMATTR>
      <OMATTR><OMATP>
        <OMS cdbase="urn:pals:openmath:typed-math:v1" cd="typed1" name="type"/>
        <OMA>
          <OMS cdbase="urn:pals:openmath:typed-math:v1" cd="matrix1" name="Matrix"/>
          <OMV name="K"/><OMI>2</OMI><OMI>3</OMI>
        </OMA>
      </OMATP><OMV name="A"/></OMATTR>
    </OMBVAR>
    <OMA>
      <OMS cdbase="http://www.openmath.org/cd" cd="relation1" name="eq"/>
      <OMA>
        <OMS cdbase="urn:pals:openmath:typed-math:v1" cd="matrix1" name="mul"/>
        <OMV name="A"/>
        <OMA>
          <OMS cdbase="urn:pals:openmath:typed-math:v1" cd="matrix1" name="identity"/>
          <OMV name="K"/><OMI>3</OMI>
        </OMA>
      </OMA>
      <OMV name="A"/>
    </OMA>
  </OMBIND>
</OMOBJ>
```

Computation fixtures bind `K : Field`, build entries with
`field_nat_cast(K,n)`, and use `literal`/`column_literal`. The validator
checks entry count and shape before it checks the enclosing equality.

## Positive fixtures and Lean witnesses

| Family | Typed assertion | Lean witness |
| --- | --- | --- |
| Addition | `add(A,B)` preserves the operand shape | `A + B = [[3,2],[4,6]]` |
| Product | `mul(A,B)` unifies its inner dimension | `A * B = [[4,4],[10,8]]` |
| Scalar multiplication | `scale(a,A) : Mat(K,m,n)` | `3 • A = [[3,6],[9,12]]` |
| Transpose | `Mat(K,m,n) → Mat(K,n,m)` | `Aᵀ = [[1,3],[2,4]]` |
| Determinant | square result has sort `Elem(K)` | `det A = -2` for arbitrary `K : Field` (excluded from XML: no scalar negation) |
| Inverse | `is_inverse(P,P)` | `P * P = I` in both orders |
| Rank | `rank` returns `Nat` | `rank I₂ = 2` |
| System | `mul_vec(A,x) : Vec(K,m)` | `A *ᵥ (2,-1) = (0,2)` for arbitrary `K : Field` (excluded from XML: no scalar negation) |

[`matrix-typed-profile-v1-authoring-witnesses.proposal.lean`](matrix-typed-profile-v1-authoring-witnesses.proposal.lean)
lowers the finite fixtures to `Matrix (Fin m) (Fin n) K` and column vectors to
`Fin n → K`, universally over `{K : Type*} [Field K]`. It contains all eight
Lean calculations: six have profile-faithful XML candidates, while determinant
and the displayed system remain explicit exclusions. `is_inverse` lowers to
the conjunction of the two identity products.

## Hard-negative suite

Each must fail before canonicalization or Lean receipt creation, returning the
operator, argument index, expected sort, actual sort, and binder path.

| Invalid intent | Required rejection |
| --- | --- |
| `matrix1:*` or typed `OMATTR` sent to generic-v1 | profile/CD gate; generic symbols unchanged. |
| `matrix1:*` sent to base typed-math-v1 | profile mismatch; its fixed CD subset excludes `matrix1`. |
| `add(A₂×₃,B₃×₂)` | argument 2 expected `Mat(K,2,3)`, got `Mat(K,3,2)`. |
| `mul(A₂×₃,B₂×₂)` | inner-dimension mismatch: expected 3, got 2. |
| `scale(a : Elem(L),A : Mat(K,2,2))` | coefficient-field mismatch `L ≠ K`. |
| `transpose(A₂×₃) = B₂×₃` | equality mismatch: left is `Mat(K,3,2)`. |
| `determinant(A₂×₃)` | square-matrix constraint fails. |
| `is_inverse(A₂×₃,B₃×₂)` | first argument must be square; no inverse fallback. |
| `rank(A) = field_nat_cast(K,2)` | equality mismatch `Nat` versus `Elem(K)`. |
| `mul_vec(A₂×₃,x₂)` | expected `Vec(K,3)`, got `Vec(K,2)`. |
| `mul_vec(A₂×₃,x₃) = b₃` | equality mismatch: product is `Vec(K,2)`. |
| `literal(K,2,2,e₁,e₂,e₃)` | exact entry count 4 fails. |
| `column_literal(K,3,e₁,e₂,e₃,e₄)` | exact entry count 3 fails. |
| Dimension 0, 9, decimal, or OMV | fixed-dimension parser rejects it. |
| Bare `OMI 2` as an `Elem(K)` entry | `field_nat_cast(K,2)` is required. |
| `Matrix(L,2,2)` with unbound/non-Field L | sort annotation closure/kind check fails. |

## Implementation boundary

Implement a new `typed_matrix_profile.py` (or equally isolated module):

1. Select `typed-math-matrix-v1` explicitly.
2. Reuse the base typed profile's core XML parser, `OMATTR` declaration gate,
   lexical environment, resource limits, and C14N helper.
3. Parse Matrix/ColumnVector only in `typed1:type`; enforce the 1..8 bound.
4. Infer the signatures above bottom-up and require exact equality sorts.
5. Canonicalize only after inference succeeds; then require a profile-separated
   canonical hash, type-CD bundle digest, and compiled Lean receipt.

Do not modify generic `_SUPPORTED_SYMBOLS`, `_infer_retrieval_sort`, generic
seed builders, generic retrieval indexing, or the local DB. Matrix fixtures
and embeddings are separately keyed by `typed-math-matrix-v1`.

## Lean verification

Compiled in the pinned workspace:

```sh
cd pals-agent/lean-workspace && \
  lake env lean ../../docs/matrix-typed-profile-v1-authoring-witnesses.proposal.lean
```

Result: exit status 0.
