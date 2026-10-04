# Planar Green/Gauss authoring profile v6

The `typed-vector-calculus-v6` profile introduces actual planar rectangular Green and Gauss identities. It does not reuse a potential-path integral as a substitute for these results. All functions, derivative fields, rectangle endpoints, and affine coefficients are general parameters. The fixed plane is the natural domain of Green's theorem; the fixed first derivative order is its analytic regularity requirement, not numerical-example enumeration.

The independent module, registry, generator, five-card manifest and exact Lean bundle preserve every older profile's bytes and semantics. Parent integration registers only authoring/loading support. This profile alone does not add runtime structuring, theorem selection, automatic instantiation, or publication.

## Closed mathematical types and conventions

`Point` means `ℝ × ℝ`, with its standard real structure and product Lebesgue volume. `ScalarFunction`, `Dual`, `DualField`, `Set`, and `RealFunction` mean respectively planar scalar functions, continuous linear functionals on the plane, fields of those functionals, sets of planar points, and real functions. They are distinct monomorphic sorts: a point cannot substitute for a real parameter, a derivative field cannot substitute for a derivative at a point, and planar functions cannot substitute for real slice functions. No arbitrary carrier, theorem-name predicate, or implicit regularity is admitted.

The registry lists every operator's ordered arguments, result type, and mathematical meaning. In particular:

* `has_fderiv(f,z,A)` means `HasFDerivAt f A z`: XML places the point before the derivative.
* `divergence(A,B)(z) = A(z)(1,0) + B(z)(0,1)` and `curl(A,B)(z) = B(z)(1,0) - A(z)(0,1)`. The operators themselves do not assert that A and B actually differentiate particular components; cards supply those hypotheses separately.
* `closed_rectangle(a,b)` is `Set.Icc a b` in componentwise order. `open_rectangle(a,b)` requires both coordinates to be strictly inside. Reversed endpoints are not silently sorted.
* `boundary_flux(f,g,a,b)` is top minus bottom plus right minus left. For ordered endpoints this is outward flux of `(f,g)`.
* `boundary_circulation(P,Q,a,b)` follows bottom, right, reversed top, reversed left: counterclockwise circulation of `P dx + Q dy` for ordered endpoints.
* `interval_integral` keeps oriented endpoints, while `set_integral` uses product Lebesgue volume. These integrals use Lean's totalized definitions; integrability must be asserted where needed.
* `cont_diff_one` is global `ContDiff ℝ 1`, a stronger explicit sufficient hypothesis, not merely continuity or unverified partial derivatives.

The grammar rejects extra namespaces/cdbases/attributes/symbols, forged sorts, unbound or shadowed variables, wrong arities, type mismatches, and registry identity/signature drift. XML is bounded to 65,536 bytes, 4,096 nodes, and depth 64. The registry has an exact schema/profile/symbol set. Standalone nullary value symbols are allowed only for the zero functional and zero planar function. OpenMath typing and canonicalization certify syntax and types, not theorem truth or a general XML-to-Lean translation.

## Cards and evidence

| Card ID | Main content | Proposed mode | Difficulty |
|---|---|---|---|
| `vector_v6_gauss_rectangle` | Area integral of divergence equals outward rectangle flux; closed-boundary continuity, interior derivatives, divergence integrability, and endpoint ordering explicit | justify/prove | standard |
| `vector_v6_green_countable_exceptions` | Green identity with an explicitly countable set excluded from interior derivative hypotheses; curl integrability and boundary continuity retained | justify/prove | advanced |
| `vector_v6_affine_flux` | Signed flux of a fully general affine field equals its linear-part trace times signed rectangle area | compute/construct | introductory |
| `vector_v6_c1_gauss_hypotheses` | Global C¹ implies closed-rectangle continuity, actual derivatives everywhere, and integrable divergence | recognize | standard |
| `vector_v6_missing_boundary_continuity` | General positive rectangle and nonzero amplitude with zero actual interior derivatives but nonzero boundary flux | counterexample/audit | standard |

The affine-field computation explicitly integrates opposite sides and cancels cross-coordinate and constant contributions. The Green proof rotates the field to `(Q,−P)` and applies the genuine Mathlib rectangular Gauss theorem with countable exceptions, then checks orientation signs. The counterexample sets one field component equal to a nonzero amplitude on the left boundary line and zero elsewhere; interior derivatives vanish because the function is locally constant there, while the right-minus-left flux is minus amplitude times positive height. The other component may be taken zero. This refutes omission of boundary continuity, not the correctly hypothesized theorem.

These cards are mathematically distinct from the earlier potential line-integral and path-independence cards: their fields need not be gradients and their identities explicitly involve area divergence/curl and the four oriented boundary sides. The C¹ recognition card supplies sufficient analytic hypotheses; it does not assert they are necessary or remove the separate endpoint-ordering check.

The pinned local Mathlib sources are `Mathlib/MeasureTheory/Integral/DivergenceTheorem.lean`, particularly `integral_divergence_prod_Icc_of_hasFDerivAt_of_le` and its `off_countable` variant. All five exact witnesses compile without admitted facts. The generator emits a manifest only after successful `lake env lean` and hashes the witness, validator, registry, toolchain and actual Mathlib revision. Five paired negative questions are authored audit candidates, not retrieval outcomes.

## Curriculum scope and limitations

Proposed bindings are in `docs/vector-calculus-v6-bindings.json`. Relative to `output/foundation-expansion-v6-20260930/after-all-bindings.json`, the integral-theorems chapter already has its synthesis/standard binding. If the parent accepts these five explicit recommendations, its four missing modes and introductory/standard/advanced difficulty deficits are filled, reaching that chapter's five-mode/four-difficulty-slot contract.

This finite contract is not full mathematical coverage of vector calculus. No arbitrary surface, surface orientation, curl of a three-dimensional field, general Stokes theorem, divergence theorem for arbitrary domains, or curved-domain Green theorem is included. Those require additional genuine geometry and typed operators. The existing synthesis binding remains parent-owned and was not reclassified here. No database insertion, runtime execution, or automatic theorem retrieval was performed by this task.

## Verification

Five exact Lean witnesses compile in the existing pinned workspace. Thirty-five dedicated unit tests cover every card, exact manifests/pins, strict loader, generator reproducibility, closed types, unbound/shadowed variables, arities, namespaces/cdbases, attributes, byte/depth limits, registry drift, actual derivative argument order, divergence/curl orientation, countable exclusions, boundary continuity, counterexample hypotheses, negative pairing, proposed bindings, and tampered witness rejection. Ruff and mypy pass for the new validator (Ruff also checks generator and tests). The parent handles independent semantic review and shared registration.
