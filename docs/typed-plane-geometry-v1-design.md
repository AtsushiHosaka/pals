# typed-plane-geometry-v1: native planar-geometry authoring profile

## Scope and boundary

This is an opt-in sibling profile for the four Phase-B affine-geometry
backlog families in `vector-complex-typed-extension.md`.  It does not extend
generic retrieval, `typed-math-v1`, or `typed-geometry-complex-v1`; all three
keep their existing symbol contracts.  Its private CD base is exactly
`urn:pals:openmath:typed-plane-geometry:v1`, and every `OMS` must carry that
base (or the standard OpenMath base) directly.  Inherited bases are rejected.

The implementation is authoring-only.  Its sealed evidence is not a generic
Draft, seed, embedding-index entry, local-typed-catalog entry, PFI package, or
database row.

## Exact sorts

The profile has no catch-all `term` sort.  Each inferred expression has one
of the following exact sorts:

| Sort | Values admitted by v1 |
| --- | --- |
| `R` | integer literals only; they are never points, vectors, lines, circles, or complex values |
| `V2` | `vector2(R, R)` and `vector_add(V2, V2)` |
| `P2` | `point2(R, R)` and `midpoint(P2, P2)`/`reflect(P2, L2)` |
| `L2` | explicitly typed bound variables only |
| `Circle2` | explicitly typed bound variables only |
| `Prop` | relations, logical connectives, and geometry predicates |

`P2` and `V2` remain distinct even though both can lower to real pairs in
Lean.  The profile has no point/vector coercion, no complex sort, and no
standard `linalg`/`complex` vocabulary.  Thus a scalar or complex expression
cannot be silently used as a point, and a vector cannot be used as a point.

## Private signatures

All private symbols are in CD `pals_plane_geometry` under the profile cdbase.

| Symbol | Signature |
| --- | --- |
| `forall`, `exists` | bind explicitly annotated variables |
| `type` | annotation key used only in `OMBVAR` declarations |
| `Real`, `Vector2`, `Point2`, `Line2`, `Circle2` | sort expressions only |
| `vector2` | `R × R → V2` |
| `vector_add` | `V2 × V2 → V2` |
| `point2` | `R × R → P2` |
| `incident_point_line` | `P2 × L2 → Prop` |
| `incident_point_circle` | `P2 × Circle2 → Prop` |
| `parallel`, `perpendicular` | `L2 × L2 → Prop` |
| `distance_sq` | `P2 × P2 → R` |
| `midpoint` | `P2 × P2 → P2` |
| `reflect` | `P2 × L2 → P2` |
| `non_collinear` | `P2 × P2 × P2 → Prop` |

The only standard symbols admitted are `relation1:eq`, `relation1:neq`, and
the exact `logic1` connectives required to form propositions.  There are no
partial `line_through` or `circle_through` constructors: existence and
membership are expressed by quantifying `L2`/`Circle2` and using incidence.

## Fail-closed rules

1. `OMOBJ`, `OMS`, `OMV`, and every other allowed element have exact allowed
   attribute sets; unknown attributes are errors.
2. `OMATTR` is permitted only as one `type` annotation in `OMBVAR`; annotation
   values must be one of the six exact sort expressions.
3. Binders, symbols, and type annotations use the profile cdbase directly;
   base inheritance and unknown symbols are errors.
4. Bound variables cannot shadow or be redeclared, and free variables are
   errors.
5. Equality requires identical inferred sorts.  Predicate arguments require
   their exact declared sort, so `P2`/`V2`, `L2`/`Circle2`, scalar, and complex
   confusion is rejected before Lean lowering.
6. A root must be a closed `Prop` containing this profile's typed binder,
   annotation, and a non-declaration geometry construct.

## Sealed candidate evidence

The initial sealed proposal deliberately contains only direct Lean matches:

1. squared distance from a point to itself is zero;
2. there exists a line incident with two specified points;
3. there exists a circle incident with three specified points;
4. perpendicularity is symmetric;
5. parallelism is symmetric.

These are a narrow parser/evidence slice, not a claim that the profile already
covers general line construction, circumcircle existence, locus solving, or
reflection theorems.  Those need separate semantic admission review.
