# `typed-multivariable-calculus-v1` 最小設計

## 結論

二変数微積分は generic retrieval、`typed-math-v1`、
`typed-real-analysis-v1` を拡張せず、明示選択する兄弟 profile
`typed-multivariable-calculus-v1` に隔離する。対象は `ℝ² → ℝ` の
具体的な first partial derivative と differentiability のみである。

```text
profile id: typed-multivariable-calculus-v1
typed CD base: urn:pals:openmath:typed-multivariable-calculus:v1
```

本 profile は sealed local authoring evidence であり、generic DB、seed、
embedding index、PFI package には入れない。generic validator と既存 profile の
受理言語は変更しない。

## Evidence-first admission

現時点で pinned Lean workspace が直接コンパイルするのは次の六つだけである。
各 `partial_x_at` / `partial_y_at` は以下の **明示した** one-variable lowering
を持つ。

```text
partial_x_at(f, (a,b), m) := HasDerivAt (fun x => f (x,b)) m a
partial_y_at(f, (a,b), m) := HasDerivAt (fun y => f (a,y)) m b
differentiable_at(f, p)   := DifferentiableAt ℝ f p
```

| Sealed card | Lean evidence |
| --- | --- |
| `∂x(x²+y²)(a,b)=2a` | `hasDerivAt_pow` + constant addition |
| `∂y(x²+y²)(a,b)=2b` | `hasDerivAt_pow` + constant addition |
| `∂x(xy)(a,b)=b` | derivative of `x ↦ x*b` |
| `∂y(xy)(a,b)=a` | derivative of `y ↦ a*y` |
| `x²+y²` is differentiable on `ℝ²` | `fun_prop` |
| `xy` is differentiable on `ℝ²` | `fun_prop` |

The manifest binds exact source XML, profile C14N output and its digest, the
registry digest, witness-file digest, Lean toolchain digest, exact witness
text, and a payload digest. It is not a claim that XML is automatically
translated into Lean.

## Exact sorts and signature

The checker has no implicit coercions. `OMI` is only a literal and becomes a
real scalar only through `multicalc1:of_int`.

| Sort | Meaning |
| --- | --- |
| `Real` | scalar ℝ |
| `Real2` | ordered pair ℝ × ℝ, not a generic vector space |
| `Real2Function` | ℝ² → ℝ |
| `Prop` | proposition |

| Symbol | Signature |
| --- | --- |
| `multicalc1:pair` | `Real × Real → Real2` |
| `multicalc1:fst`, `snd` | `Real2 → Real` |
| `multicalc1:lambda2` | `(p : Real2) . Real → Real2Function` |
| `multicalc1:apply` | `Real2Function × Real2 → Real` |
| `multicalc1:partial_x_at`, `partial_y_at` | `Real2Function × Real2 × Real → Prop` |
| `multicalc1:differentiable_at` | `Real2Function × Real2 → Prop` |
| `arith1:plus`, `times`, `minus`, `unary_minus` | scalar `Real` operands only |
| `arith1:power` | `Real × Nat-literal(0..64) → Real` |

Every typed `OMS` states this profile's cdbase directly. Standard CD symbols
may omit cdbase only when they do not inherit one. Bound declarations use
`typed1:type`; free variables, shadowing, wrong lambda binder count, mixed
sort arithmetic, and non-proposition roots reject before C14N.

## Explicit hard rejects / defers

The following are intentionally absent from the registry and must fail before
receipt creation:

| Family | Status | Reason |
| --- | --- | --- |
| gradient / directional derivative | hard reject | The Lean evidence is Fréchet-derivative based; a Euclidean Riesz/gradient contract is not sealed here. |
| extrema / Fermat theorem | hard reject | `IsLocalExtr → fderiv=0` has a total-derivative representation, not this profile's partial/gradient contract. |
| Hessian / Schwarz / second-derivative tests | hard reject | No C²/Hessian type and exact compatible witness are sealed. |
| Lagrange multipliers | hard reject | Requires constraint-set, tangent-space, and regularity semantics. |
| double or iterated integrals / Fubini | hard reject | Existing Lean Fubini witness is measure-theoretic and does not establish a rectangle-continuity-to-integrability contract. |
| change of variables | hard reject | Jacobian/diffeomorphism and measure-domain semantics are not present. |

In particular, a first-partial card is not silently promoted to a claim about
the gradient, Hessian, local optimum, or double integral. Each needs a new
profile revision with direct Lean evidence and a separate sealed manifest.

## Negative checks

The unit suite rejects:

- a scalar where `Real2` is required by `partial_x_at`;
- a `Real2` body from `lambda2` instead of a scalar body;
- a scalar body supplied to `fst` or `snd`;
- `gradient`, `hessian`, `double_integral`, or `partial_xy_at` as unknown
  symbols;
- profile XML submitted to generic retrieval or `typed-real-analysis-v1`;
- inherited typed cdbase and non-canonical bytes.
