# Vector / complex-plane typed OpenMath extension

## Decision

Do not add `linalg1`, `linalg2`, or `complex1` to the current generic
allow-list as ordinary `term`-returning symbols.  The current retrieval
validator distinguishes only `term`, `proposition`, and function sorts; it
does not retain scalar, vector, matrix, point, or complex types.  A raw
allow-list change would therefore accept invalid expressions such as a scalar
product whose second argument is a real number, or the conjugate of a real
number.

Add a new, opt-in `typed-geometry-complex-v1` profile instead.  It uses the
standard OpenMath symbols below unchanged and assigns them PALS-enforced
sorts.  New PALS symbols live in the *proposed* CD
`urn:pals:openmath:cd:v2`, `pals2`; that CD does not exist yet and must not be
advertised as a standard OpenMath CD.

The four geometry cards must remain backlog until phase B.  The other eight
cards can be admitted once phase A is implemented.  This is a semantic split,
not merely a vocabulary split.

## What the standard CDs supply, and what they do not

`linalg2:vector` is an n-ary row-vector constructor, and `linalg1` supplies
one-based `vector_selector`, binary `scalarproduct`, and unary `determinant`
(on a square matrix).  It does **not** provide a typed planar-vector binder,
vector addition, scalar action, a two-vector determinant, or affine points.
In particular, `linalg1:determinant` consumes a matrix rather than two side
vectors.  [linalg2](https://openmath.org/cd/linalg2.html) and
[linalg1](https://openmath.org/cd/linalg1.html) document these distinctions.

`complex1` supplies Cartesian/polar constructors, `conjugate`, `real`,
`imaginary`, and `argument`; `nums1:i` is the imaginary-unit constant.
Complex addition and multiplication are represented by overloaded `arith1`
operators in the standard examples, but the current validator has no algebra
type parameter with which to resolve that overload.  It also has no modulus
symbol.  [complex1](https://openmath.org/cd/complex1.html) documents the
standard constructors and projections.

The existing `complex_argument_quadrant` backlog entry is right to name
`transc2:arctan` when it specifically needs an `atan2` derivation: it is the
two-argument, quadrant-preserving arctangent.  It is an **experimental** CD,
so it is optional and must be separately opted into; `complex1:argument` is
enough for statements that ask for an argument without requiring the atan2
calculation.  [transc2](https://openmath.org/cd/transc2.html).

## Exact type gaps for the 12 existing backlog entries

| Backlog ID | Standard symbols that help | Remaining missing type/semantics |
| --- | --- | --- |
| `geometry_line_through_two_points` | `linalg2:vector` can encode coordinates | No affine `Point2`, `Line2`, line binder, or point-line incidence.  Equating coordinate vectors does not define a line. |
| `geometry_circle_through_three_points` | `linalg2:vector` can encode coordinates | No `Circle2`, incidence, or non-collinearity predicate, so the three points and one circle cannot be linked. |
| `geometry_perpendicular_bisector_locus` | vector coordinates only | No point distance, midpoint, line, or perpendicularity sorts; scalar equalities lose the locus relation. |
| `geometry_reflection_in_line` | vector coordinates only | No affine line or reflection operation.  Treating a point as a vector would incorrectly make point addition/scaling legal. |
| `vector_component_addition` | `linalg2:vector`, `linalg1:vector_selector` | `vector` has arbitrary dimension; no type rule ties two component equations to one `V2` value, and no vector-add operation exists. |
| `vector_scalar_multiple` | `linalg2:vector` | No scalar action; generic `arith1:times` cannot distinguish `R × V2` from scalar multiplication or invalid products. |
| `vector_dot_product_orthogonality` | `linalg1:scalarproduct` | The CD describes two vector arguments, but the current validator cannot enforce them or bind `V2` variables.  Dimension equality is unchecked. |
| `vector_triangle_area_determinant` | `linalg1:determinant` | Standard determinant takes a square matrix; the card has two `V2` side vectors.  Matrix shape, real output, and area orientation are all otherwise unchecked. |
| `complex_cartesian_multiplication` | `complex1:complex_cartesian`, `nums1:i` | No `C` sort or complex multiplication resolution.  Untyped `arith1:times` would accept real/vector/complex mixtures. |
| `complex_conjugate_modulus_square` | `complex1:conjugate` | No complex input/output checking, real-valued squared-modulus operation, or explicit real-to-complex coercion. |
| `complex_multiply_i_quarter_turn` | `nums1:i`, `complex1:real`, `complex1:imaginary` | No complex product sort, so `i` can be multiplied by any generic term; no connection to its Cartesian components. |
| `complex_argument_quadrant` | `complex1:argument`, optional `transc2:arctan` | No `C → R` rule, no typed real-sign premises for quadrant selection, and no separate opt-in for experimental `atan2`. |

## Minimal proposed signatures

The sorts below are validator-internal sorts, not OpenMath XML tags:
`R`, `V2`, `C`, `P2`, `L2`, and `Circle2`.  An integer/decimal literal is
contextually usable as `R`; it is not silently usable as `V2`, `C`, or `P2`.

### Phase A — admissible vector and complex cards

Reuse standard symbols with these strict profile signatures:

| Symbol | Profile signature | Constraint |
| --- | --- | --- |
| `linalg2:vector` | `R × R → V2` | The profile accepts exactly two operands, although the standard CD permits arbitrary arity. |
| `linalg1:vector_selector` | `{1,2} × V2 → R` | Index is a positive integer literal; no symbolic/out-of-range selector. |
| `linalg1:scalarproduct` | `V2 × V2 → R` | Both operands must have the same fixed planar sort. |
| `complex1:complex_cartesian` | `R × R → C` | |
| `complex1:conjugate` | `C → C` | |
| `complex1:real`, `complex1:imaginary`, `complex1:argument` | `C → R` | `argument` is the principal argument specified by `complex1`. |
| `nums1:i` | `C` | |
| `transc2:arctan` (optional) | `R × R → R` | Only in an explicit experimental profile; arguments are `(x, y)` per the CD. |

Add only these PALS operations, because standard OpenMath has no way to make
the current scalar `arith1` rules type-safe for these cases:

| Proposed `pals2` symbol | Signature | Purpose |
| --- | --- | --- |
| `forall_real_vector2`, `exists_real_vector2` | binder over `V2` | Typed vector quantification. |
| `forall_complex`, `exists_complex` | binder over `C` | Typed complex quantification. |
| `vector_add` | `V2 × V2 → V2` | Component addition. |
| `vector_scale` | `R × V2 → V2` | Scalar action. |
| `determinant2` | `V2 × V2 → R` | Planar determinant; verifier lowers it to the determinant of the corresponding 2×2 matrix. |
| `complex_add`, `complex_mul` | `C × C → C` | Safe alternative to adding polymorphic algebraic overloading to the current validator. |
| `complex_norm_sq` | `C → R` | `re(z)^2 + im(z)^2`; deliberately not a complex-valued modulus. |

This phase covers `vector_component_addition`, `vector_scalar_multiple`,
`vector_dot_product_orthogonality`, `vector_triangle_area_determinant`, and
the four complex-plane entries.

### Phase B — affine geometry cards

Points must be distinct from vectors even if both lower to `ℝ × ℝ` in Lean.
Add the following only when the geometry verifier is ready:

| Proposed `pals2` symbol | Signature |
| --- | --- |
| `forall_point2`, `exists_point2` | binder over `P2` |
| `forall_line2`, `exists_line2` | binder over `L2` |
| `forall_circle2`, `exists_circle2` | binder over `Circle2` |
| `point2` | `R × R → P2` |
| `incident_point_line` | `P2 × L2 → Prop` |
| `incident_point_circle` | `P2 × Circle2 → Prop` |
| `distance_sq` | `P2 × P2 → R` |
| `midpoint` | `P2 × P2 → P2` |
| `perpendicular` | `L2 × L2 → Prop` |
| `reflect` | `P2 × L2 → P2` |
| `non_collinear` | `P2 × P2 × P2 → Prop` |

`line_through` and `circle_through` are intentionally absent: quantified
`L2`/`Circle2` values plus incidence express existence without inventing
partial constructors for coincident points.  `non_collinear` supplies the
necessary precondition for a unique circumcircle.  This phase covers the four
geometry entries only.

## Complete positive OpenMath examples (after phase A)

The first is entirely standard-CD vocabulary but receives `V2` typing from
the profile.  The second exercises a proposed PALS operation while retaining
the standard complex constructor and conjugation symbol.

```xml
<OMOBJ xmlns="http://www.openmath.org/OpenMath" version="2.0"
       cdbase="http://www.openmath.org/cd">
  <OMA>
    <OMS cd="relation1" name="eq"/>
    <OMA>
      <OMS cd="linalg1" name="scalarproduct"/>
      <OMA>
        <OMS cd="linalg2" name="vector"/>
        <OMI>1</OMI><OMI>2</OMI>
      </OMA>
      <OMA>
        <OMS cd="linalg2" name="vector"/>
        <OMI>2</OMI><OMI>-1</OMI>
      </OMA>
    </OMA>
    <OMI>0</OMI>
  </OMA>
</OMOBJ>
```

```xml
<OMOBJ xmlns="http://www.openmath.org/OpenMath" version="2.0"
       cdbase="urn:pals:openmath:cd:v2">
  <OMA>
    <OMS cdbase="http://www.openmath.org/cd" cd="relation1" name="eq"/>
    <OMA>
      <OMS cd="pals2" name="complex_norm_sq"/>
      <OMA>
        <OMS cdbase="http://www.openmath.org/cd" cd="complex1" name="complex_cartesian"/>
        <OMI>3</OMI><OMI>4</OMI>
      </OMA>
    </OMA>
    <OMI>25</OMI>
  </OMA>
</OMOBJ>
```

The different `cdbase` values are intentional: OpenMath standard symbols
retain their standard base, while only proposed PALS symbols use the new PALS
CD base.

## Validator implementation boundary and tests

Safe now:

1. Add an opt-in profile dispatcher; leave the current generic profile
   unchanged.
2. In that dispatcher, register the standard symbols above with arity and the
   exact sort rules in phase A.  Do not register generic `linalg2:vector` or
   `arith1:plus`/`times` as untyped vector/complex terms.
3. Add phase-A PALS symbols and reject an expression unless every subterm has
   one exact inferred sort.  A separate profile version is required because
   the current `urn:pals:openmath:cd:v1` contract cannot silently gain these
   semantics.

Positive tests:

1. The two XML fixtures above validate under `typed-geometry-complex-v1`.
2. `vector_selector(2, vector(1, 2)) = 2` infers `R`.
3. `complex1:conjugate(complex1:complex_cartesian(3,4))` infers `C`.
4. `complex1:argument(complex1:complex_cartesian(-1,1))` infers `R`, and the
   `re < 0`, `im > 0` premises are accepted as real propositions.

Negative tests:

1. `scalarproduct(vector(1,2), 3)` fails: argument 2 requires `V2`, got `R`.
2. `scalarproduct(vector(1,2), vector(3,4,5))` fails: the second constructor
   is not a `V2` in this profile.
3. `vector_selector(0, vector(1,2))` and selector index 3 fail the fixed
   one-based `{1,2}` index rule.
4. `complex1:conjugate(3)` fails: argument requires `C`, got `R`.
5. `complex_mul(complex_cartesian(1,2), vector(1,2))` fails: argument 2
   requires `C`, got `V2`.
6. `complex1:argument(complex_cartesian(1,2))` passed to `complex_mul` fails:
   the result is `R`, not `C`.
7. Before the new profile is selected, every one of these standard symbols
   remains rejected by the current profile.  This regression test prevents a
   permissive allow-list change from widening the existing Draft contract.

## Lean evidence

`vector-complex-typed-extension-witnesses.lean` contains one witness for
each of the 12 backlog entries.  It models points/vectors as planar pairs,
complex numbers as `ℂ`, and uses `Complex.arg_of_re_neg_of_im_nonneg` for the
quadrant-II argument branch.  It was compiled in the pinned workspace with:

```sh
lake env lean ../../docs/vector-complex-typed-extension-witnesses.lean
```

Result: exit status 0.

The Lean file is semantic evidence, not the parser's type checker: the PALS
profile still has to keep `P2` and `V2` distinct before lowering both to Lean
coordinates.
