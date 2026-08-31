# typed-commutative-algebra-modules-v1

## Purpose and boundary

`typed-commutative-algebra-modules-v1` is an isolated CA-2 profile for
original exercises about modules over a commutative ring.  It is not an
extension of `typed-commutative-algebra-v1`: changing that profile would alter
the meaning and registry digest of its sealed ideal cards.

The profile represents a commutative ring `R`, an `R`-module `M`, an
`R`-submodule of `M`, and an `R`-linear map `M -> N`.  The map domain and
codomain, and the scalar ring of every dependent object, are explicit in
OpenMath.  It admits finite expressions for bottom/top, supremum/infimum,
kernel/range, identity/zero/composite maps, injectivity/surjectivity, and
exactness at one named middle module.

## CA-2 acceptance contract

Every sealed card has all of the following, computed from current bytes:

- a closed actual profile OpenMath proposition and exact v4 C14N;
- four to eight non-empty Sketch steps;
- a direct witness in the pinned local Mathlib workspace;
- raw/canonical XML, statement, Lean target, witness, design, registry,
  validator, toolchain, witness-bundle, and manifest digests;
- an explicit statement--OpenMath--Lean alignment record.

No claim is made that OpenMath is automatically translated to Lean.  The
manifest is local authoring evidence and is not a generic Draft, database
seed, embedding-index item, or PFI package.

## Soundness rules

- A `Module(R)` declaration requires a previously bound `CommRing R`.
- `Submodule(R,M)` and `LinearMap(R,M,N)` require modules whose scalar carrier
  is exactly the previously bound `R`.
- Every operation repeats its scalar ring and module carriers; no coercion or
  inferred ambient module is accepted.
- `exact_at(R,M,N,P,f,g)` accepts only `f : M -> N` and `g : N -> P`; it means
  `range(f) = kernel(g)` at the explicitly named module `N`.
- Free variables, shadowed binders, unknown symbols, inherited typed cdbase,
  scalar-ring mismatch, and linear-map domain/codomain mismatch are hard
  errors.

## Deliberate deferrals

Tensor products, `Hom` as a first-class module, quotient modules, direct-sum
universal properties, arbitrary diagrams, and arbitrary-length exact
sequences are outside v1.  In particular, a token named `exact` is not used
to pretend that arbitrary sequences are typed or Lean-aligned.  A later
profile must add the required dependent carriers and test negative cases
before those topics are admitted.
