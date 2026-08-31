# Draft curriculum coverage

This is the operational coverage map for local Draft authoring.  It targets
Japanese high-school mathematics and the usual mathematics sequence through
the second year of a science or engineering degree.  A checkmark means that
the local catalog has verified examples; it does not mean the topic is
exhaustive.

| Level | Topic | Required problem patterns | Status |
| --- | --- | --- | --- |
| High school | Equations and inequalities | linear systems, quadratics, absolute values, rational equations, AM-GM/Cauchy-style bounds | active |
| High school | Trigonometry | identities, equations, range and extremum inequalities | active |
| High school | Exponentials and logarithms | identities, equations, positivity domains, monotonicity and inequalities | active |
| High school | Sequences and limits | explicit limits, comparison, algebra of limits, function limits | active |
| High school | Differential and integral calculus | polynomial/trigonometric derivatives, definite-integral evaluations and properties | active |
| High school | Coordinate geometry, vectors, complex plane | lines/circles/conics, dot products, loci, complex arithmetic and geometry | scalar coordinate geometry and conics active; native vectors/complex pending typed profiles |
| High school | Counting, probability and statistics | combinations, conditional probability, expectation, variance, binomial laws | finite-set counting instances active; probability typed-profile design complete, 10 cards have compatible Lean lowering evidence and 7 are explicitly excluded pending re-authoring |
| High school / early university | Ordinary differential equations | separable, first-order linear, constant-coefficient second-order equations | active |
| University | Linear algebra | rank-nullity, dimension bounds, kernels/images, basis and matrix problems | generic rank/dimension instances active; six typed matrix authoring proposals have aligned Lean evidence, while profile implementation and candidate admission remain pending |
| University | Real analysis | limits, continuity, epsilon-delta, differentiability and integration | generic limits/continuity instances active; four typed authoring proposals have aligned witnesses, while registry implementation and candidate admission remain pending |
| University | Discrete mathematics | logic, sets, functions, relations, induction, finite counting | logic/sets/finite relation-map-counting instances active; a typed finite-graph profile is designed, while general relation/function schemas, recurrence, and graph admission remain pending |
| University | Abstract algebra | groups, rings, polynomial division/factorization, modular arithmetic | typed group/ring authoring boundary is implemented with an immutable three-card proposal and aligned Lean witnesses; broader candidate admission remains pending |
| University | Multivariable calculus | partial derivatives, gradients, Jacobians, multiple integrals | typed extension proposed; candidate admission pending |

## Authoring rules

- A topic becomes **active** only after every card has valid OpenMath, a
  compiled Lean witness, no canonical OpenMath collision, and a 4--10 step
  Sketch when the proof genuinely has intermediate goals.
- A single theorem schema with altered numeric coefficients does not count as
  multiple problem patterns.
- New notation is admitted only when its OpenMath meaning and Lean type are
  both explicit.  Do not encode matrices, probabilities, or derivatives as
  untyped `OMV` placeholders.
- Each new batch must contain hard-negative checks for nearby but different
  statements before it is treated as a release candidate.
