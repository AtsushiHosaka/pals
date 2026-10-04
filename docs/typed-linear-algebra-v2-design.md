# Finite-dimensional linear algebra profile v2

`typed-linear-algebra-v2` is a new, closed authoring profile. It preserves all existing
profile bytes and does not declare production runtime structuring or publication support.
Its initial batch contains 27 general theorems, compiled against the repository's pinned
Mathlib. Natural dimensions and family lengths are variables, including zero.

## Declarations carry the mathematical assumptions

Every symbol below uses the explicit cdbase `urn:pals:openmath:typed-linear-algebra:v2`.
Types and value operators use CD `la2`; binders and type annotations use `typed1`.
There is no implicit conversion from a ring or an arbitrary module.

| Declaration | Lean interpretation |
| --- | --- |
| `K : Field` | `K : Type*`, `[Field K]` |
| `V : FiniteDimensionalSpace(K)` | `V : Type*`, `[AddCommGroup V] [Module K V] [FiniteDimensional K V]` |
| `f : LinearMap(K,V,W)` | `f : V →ₗ[K] W` |
| `S : Subspace(K,V)` | `S : Submodule K V` |
| `a : Scalar(K)` | `a : K` |
| `x : Vector(K,V)` | `x : V` |
| `n : Nat` | `n : ℕ` |
| `v : VectorFamily(K,V,n)` | `v : Fin n → V` |
| `a : ScalarFamily(K,n)` | `a : Fin n → K` |
| `b : Basis(K,V,n)` | `b : Module.Basis (Fin n) K V` |

All type parameters must be previously bound variables. Carrier identities are nominal:
a `K`-space cannot be used as an `L`-space; a family indexed by `n` cannot be supplied
where `m` is declared, even if an unrelated proposition claims `n=m`. There is no
scalar-to-vector, space-to-subspace, or ring-to-field coercion. Basis values encode
both independence and spanning, as Lean's `Basis` does. Finite dimensionality applies
to **every** declared space, including a codomain.

## Value operators, in argument order

In this table `S,T` are subspaces of `V`; `f:V→W`, `g:W→U`; an endomorphism has type
`V→V`. Every displayed `K,V,W,U,n` argument is explicit and carrier-checked.

| Operator | Result and exact mathematical/Lean meaning |
| --- | --- |
| `dim(K,V)` | Nat: `Module.finrank K V` |
| `sub_dim(K,V,S)` | Nat: `Module.finrank K S` |
| `sub_top(K,V)`, `sub_bot(K,V)` | Subspace(K,V): `⊤`, `⊥` |
| `sub_sup(K,V,S,T)`, `sub_inf(K,V,S,T)` | Subspace(K,V): `S ⊔ T`, `S ⊓ T` |
| `sub_le(K,V,S,T)`, `sub_lt(K,V,S,T)` | Prop: `S ≤ T`, `S < T` |
| `kernel(K,V,W,f)` | Subspace(K,V): `LinearMap.ker f` |
| `range(K,V,W,f)` | Subspace(K,W): `LinearMap.range f` |
| `injective(K,V,W,f)`, `surjective(K,V,W,f)` | Prop: `Function.Injective f`, `Function.Surjective f` |
| `linear_comp(K,V,W,U,f,g)` | LinearMap(K,V,U): **`g.comp f`**, applying `f` first |
| `linear_sub(K,V,W,f,h)` | LinearMap(K,V,W): `f-h`, where `h:V→W` |
| `linear_smul(K,V,W,a,f)` | LinearMap(K,V,W): `a • f`, where `a:Scalar(K)` |
| `linear_id(K,V)` | LinearMap(K,V,V): `LinearMap.id` |
| `det(K,V,f)` | Scalar(K): `LinearMap.det f`, only for an endomorphism |
| `eigenspace(K,V,f,a)` | Subspace(K,V): `Module.End.eigenspace f a`, i.e. all `x` with `f x=a • x`, including zero |
| `family_span(K,V,n,v)` | Subspace(K,V): `Submodule.span K (Set.range v)` |
| `independent(K,V,n,v)` | Prop: `LinearIndependent K v` |
| `basis_vectors(K,V,n,b)` | VectorFamily(K,V,n): the vector family underlying `b` |
| `scalar_family_injective(K,n,a)` | Prop: `Function.Injective a`; its values are pairwise distinct |
| `eigenfamily(K,V,n,f,a,v)` | Prop: `∀ i : Fin n, Module.End.HasEigenvector f (a i) (v i)`; **each `v i` is nonzero**, as well as satisfying its eigenvector equation |
| `has_eigenbasis(K,V,n,f,a)` | Prop: `∃ b : Module.Basis (Fin n) K V, ∀ i, Module.End.HasEigenvector f (a i) (b i)` |
| `scalar_zero(K)` | Scalar(K): `0` |
| `scalar_mul(K,a,b)` | Scalar(K): `a*b` |
| `scalar_pow(K,a,n)` | Scalar(K): `a^n`; here the exponent may be any well-typed Nat expression, such as `dim(K,V)` |

`eigenfamily` and `has_eigenbasis` express mathematical properties of explicitly typed
objects, not names of accepted theorems. For example, the profile can express an
incorrect implication obtained by omitting eigenvalue distinctness; syntax validation
does not pronounce such a claim true. Lean verification and independent alignment
review remain separate gates.

Standard symbols use the explicit cdbase `http://www.openmath.org/cd`:

- `relation1:eq/neq` compare values of exactly the same sort; comparison of carrier
  declarations or propositions is rejected.
- `relation1:leq/lt` compare two Nat expressions only.
- `arith1:plus` adds two Nat expressions only.
- `logic1:and/or/implies` take exactly two propositions; `logic1:not` takes one.
- Equivalence is written as the conjunction of the two implications.

`typed1:forall/exists` bind one to 64 ordered typed declarations and have proposition
bodies. Quantification is closed, and shadowing/redeclaration is forbidden.

## Validation and evidence

The parser requires the exact OpenMath element namespace, explicit registered cdbases,
known tags, closed attributes, exact operator arities, and dependent carrier matches.
It rejects unbound names, mixed fields, reversed map arguments, wrong family lengths,
rectangular determinants, unexpected text, unknown symbols, and sort constructors used
as values. Input limits are 65,536 UTF-8 bytes, 4,096 nodes, and depth 64. Natural literals
are canonical decimal integers from zero through 999,999,999; no negative or real literal
is silently accepted as a dimension. Quantified dimensions have no numeric upper bound.

Canonicalization uses the existing alpha-aware OpenMath v4 canonicalizer **after** type
validation. The strict entry point accepts only exact canonical bytes. The JSON registry
must match the validator's full closed symbol set with no duplicate entries.

`generate-linear-algebra-v2-batch.py` writes the exact marked Lean bundle, compiles it
with `lake env lean` in the existing local workspace, and writes JSON only upon successful
compilation. Evidence binds the witness, validator, registry, Lean toolchain and Mathlib
revision. This is manually authored alignment evidence, not a general automatic
OpenMath-to-Lean translator.

The 27 cards cover rank-nullity; dimension bounds and rank criteria; equal-dimensional
injectivity/surjectivity; subspace dimensions, Grassmann's formula and complements;
basis cardinality and finite independence/spanning criteria; eigenspace kernels,
distinct eigenvectors and eigenbasis construction; and determinant laws. They include
zero-dimensional spaces and empty families where the theorem applies.

Independent negative queries supply concrete counterexamples or explain which assumption
is missing. Their existence is not evidence of successful retrieval evaluation. Neither
this document nor the batch asserts full textbook coverage. Orthogonality, Gram–Schmidt,
inner products, spectral theorems, Jordan form, quotient-space syntax, matrix entry
calculations and general coordinate changes remain outside this profile's initial scope.

Inventory review resolved one similarity heuristic flag between
`la_v2_rank_domain_bound` and `la_v2_rank_codomain_bound`. These are different bounds:
`rank(f) ≤ dim(V)` follows from the domain/quotient, while `rank(f) ≤ dim(W)` follows
from the image's inclusion in the codomain. The heuristic erases the source/codomain
role distinction. Their canonical OpenMath identities differ, and neither is a numeric
or variable-renaming variant of the other.
