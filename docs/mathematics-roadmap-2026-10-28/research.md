# Prior art and research direction

Primary sources reviewed on 2026-10-28. Compatibility, benchmark quality, and
third-party builds below have not been tested in this coordination chat.

## Geometry

- [Mathlib Euclidean geometry](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Geometry/Euclidean/Triangle.html)
  supplies formal geometry over inner-product/affine spaces. PALS still needs
  faithful input formalization, a readable synthetic trace, and matching diagrams.
- [LeanEuclid](https://github.com/loganrjmurphy/LeanEuclid) supplies System E
  vocabulary and geometric reasoning examples. Its
  [SMT solver source](https://raw.githubusercontent.com/loganrjmurphy/LeanEuclid/master/SystemE/Meta/Smt/Solver.lean)
  defines `axiom SMT_VERIF (P : Prop) : P` and uses it to close goals. Current
  solver success is unsuitable as PALS proof evidence without reconstruction.
- [LeanGeo](https://github.com/project-numina/LeanGeo) is relevant prior art,
  but its README lists proof reconstruction and remaining Mathlib-branch axioms
  as unfinished. Audit the exact chosen revision before reuse.
- [Euclean](https://arxiv.org/abs/2607.19374) and
  [MechGeo](https://arxiv.org/abs/2608.02295) are recent work to evaluate for
  Mathlib-native formalization and intermediate geometric representations.
  [MechGeoBench](https://github.com/MechMath/MechGeoBench) distinguishes problem
  templates containing `sorry` from solutions. Dataset membership is not proof.
- [GeoCoq](https://github.com/GeoCoq/GeoCoq) is established axiomatic synthetic
  geometry in Coq; it is not a drop-in Lean dependency.
- [AlphaGeometry](https://github.com/google-deepmind/alphageometry) offers
  construction search and deduction ideas. Solver output still needs checked
  Lean reconstruction before PALS can call it Lean-verified.
- [tikz-cd](https://ctan.org/pkg/tikz-cd) provides diagram rendering.
  [Mathlib CommSq](https://leanprover-community.github.io/mathlib4_docs/Mathlib/CategoryTheory/CommSq.html)
  provides formal commutative-square semantics. Rendering alone establishes no
  equality of composites.

## Name-invariant retrieval

- [Lean Expr](https://lean-lang.org/doc/api/Lean/Expr.html) represents bound
  variables with de Bruijn indices and distinguishes local free variables.
  Alpha-equivalence and arbitrary wildcard substitution are different operations.
- [Mathlib RefinedDiscrTree](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Lean/Meta/RefinedDiscrTree.html)
  provides typed-expression indexing with bound-variable structure and labeled
  wildcard identities. Repeated variables must remain consistent.
- [Lean LibrarySearch](https://lean-lang.org/doc/api/Lean/Meta/Tactic/LibrarySearch.html)
  retrieves and tries library lemmas; assess its integration point under the
  pinned toolchain rather than inventing an unchecked matcher.
- [MathWebSearch](https://kwarc.info/systems/mws/) provides substitution-tree
  and unification-based mathematical formula retrieval as earlier prior art.
- [LeanDojo/ReProver](https://arxiv.org/abs/2306.15626) and
  [LeanSearch v2](https://arxiv.org/abs/2605.13137) provide retrieval baselines.
  Embedding similarity cannot replace typed applicability checks.
- [Lake](https://lean-lang.org/doc/reference/latest/Build-Tools-and-Distribution/Lake/)
  documents artifact input tracking and caching. Verify support in the project
  toolchain before adopting features from latest documentation.
  [Lean compilation](https://lean-lang.org/doc/reference/latest/Elaboration-and-Compilation/)
  and [proof validation](https://lean-lang.org/doc/reference/latest/ValidatingProofs/)
  explain why compiled modules require trusted provenance and proof checks.

## Contribution to test

The prior art rules out a claim that Lean geometry or wildcard theorem search
does not exist. A valuable PALS contribution would integrate faithful problem
and image interpretation, explicit checked reasoning steps, synchronized chat
diagrams, typed reusable theorem search, and measured trusted artifact reuse.
Novelty and performance claims require comparative experiments.
