# `typed-real-analysis-v1` design

## 結論

実解析・一変数微積分は generic-v1 を拡張せず、明示選択する兄弟
profile `typed-real-analysis-v1` として導入する。既存の
`typed-math-v1` の typed binder、`OMATTR` による変数型、exact sort
equality、canonicalization、Lean receipt をそのまま再利用する。

```text
profile id: typed-real-analysis-v1
PALS typed CD base: urn:pals:openmath:typed-math:v1
new proposed typed CD: realanalysis1
```

ここでの `realanalysis1` は PALS 提案 CD であり、標準 OpenMath CD では
ない。standard `calculus1` を generic-v1 の term-returning 演算子として
増やして解決してはならない。generic-v1、base `typed-math-v1`、未知
profile はこの XML をすべて reject する。DB、generic validator、既存 Draft
の canonical bytes は変更しない。

この分離は「表現できる」と「型安全な実解析の定理である」を混同しない
ためのものでもある。typed XML の型検査だけでは定理は証明しない。Draft の
admission には、profile 分離した canonical XML、CD bundle digest、対応を
レビューした pinned Lean witness と verified receipt を要求する。

### 現実装の admission 境界

この初回実装は、現在 exact Lean witness と三者対応がある四つの family
（raw ε–δ、`has_deriv_at`、`differentiable_at`、`interval_integrable`）に
限定する。MVT、Taylor、積分値、広義積分はこの profile の記号 registry に
入れず hard reject する。下記のより広い意味論は将来 extension の設計根拠で
あり、現 sealed manifest への admission を意味しない。

## 現行カードの棚卸し

`pals_agent/openmath.py` の generic symbol registry はすでに
`calculus1:diff`、`calculus1:defint`、`interval1:oriented_interval` を
許している。しかし、その追加検査は次だけである。

| 現行構文 | 現行 validator が保証すること | 保証しないため型安全な実解析カードにできないこと |
| --- | --- | --- |
| `pals1:continuous_at` / `continuous_on` / `has_limit_at`（`continuity-v1`） | 関数位置が `fns1:lambda` 又は real-function slot であること、theorem-level の連続性 contract | 点・値・算術項は generic `term`。ε、δ、絶対値、不等式、定義域を実数として結べない。ε–δ の定義そのものではない。 |
| `calculus1:diff(λx. t)` | 引数が proposition でない単変数 `fns1:lambda` | `x` と戻り値が ℝ、微分可能性、点、微係数の型、定義域、除外点。 |
| `calculus1:defint(oriented_interval(a,b), λx. t)` | 第 1 引数が `interval1:oriented_interval`、第 2 引数が単変数ラムダ | 端点・被積分関数・積分値が ℝ、有限区間での可積分性、Riemann/測度論の意味、向きの約束。 |
| 通常の `arith1` / `relation1` / `transc1` | arity と proposition/term の粗い区別 | 実数・自然数・関数・集合の区別、分母非零、極限や導関数の side condition。 |

従って generic の連続性カードは、**theorem-level retrieval contract として
だけ**既存のまま使える。ε–δ の証明方針を Sketch に記録することはできるが、
その式を generic XML の証明済み定義として保存してはならない。

既存の `highschool-sequences-limits-calculus-candidates.json` にある九つの
`calc_*` 候補も同様である。現在の parser がその構文を受理しても、それは
「登録済みの shape」であって「型安全な実数微積分への admission」ではない。
新規 verified Draft としての採用は本 profile の実装後に再 canonicalize /
re-receipt する。それまでは legacy candidate 扱いに留める。

base `typed-math-v1` の `analysis1:has_fderiv_at` はこの穴を埋めない。
同 profile は一般の normed real space 用に限定された別 slice で、`ℝ` を
その space sort へ暗黙 coercion せず、閉区間・実数関数・ε–δ・一変数積分の
意味を持たない。base profile を広げず、実解析用の局所的な型系にする。

## 対象範囲と分離

| 典型問題 | `typed-real-analysis-v1` | 後続 profile | 理由 |
| --- | --- | --- | --- |
| ε–δ 連続、連続性の否定 | 対応 | — | 量化する ε/δ/x と実数算術を exact sort で結べる。 |
| 一点での微分可能性、導関数の値、連鎖・積・商の具体計算 | 対応 | — | `has_deriv_at` を predicate にして未定義な total derivative を避ける。 |
| Rolle / 平均値の定理 | 現 profile では hard reject | `typed-real-analysis-mvt-v1` | 閉区間連続・開区間微分可能・順序付き端点と、`HasDerivAt` に一致する witness を別 revision で固定する。 |
| 連続関数の通常の定積分、区間上の積分値計算 | 現 profile では hard reject | `typed-real-analysis-integral-value-v1` | `interval_integrable` と積分値を同一 statement・Lean witness に束縛してから oriented interval integral を導入する。 |
| Taylor の一般次数・Peano / Lagrange remainder | 非対応 | `typed-real-analysis-taylor-v1` | 階数、反復導関数、factorial、smoothness、remainder point が必要。 |
| Riemann 可積分性を分割・mesh・tagged sum から定義する問題 | 非対応 | `typed-riemann-integral-v1` | Partition / tagged partition の依存 sort と二重の量化が必要。 |
| 広義積分 | 非対応 | `typed-improper-integral-v1` | 無限遠又は特異点への極限を finite real value と別に扱う。 |

将来の積分値 extension は Mathlib の `IntervalIntegral`（端点を入れ替えると
符号が反転する oriented interval integral）に固定する。その extension では
`interval_integrable`、又は連続性からそれを導く premise を同じ statement に
置く。現 profile は `interval_integrable` のみを許可し、`interval_integral` と
積分値を hard reject する。従って total operator の存在だけから未可積分関数を
積分可能と扱わない。

## v1 の sort と最小 signature

`typed-math-v1` に次の profile-local sort を加える。`RealFunction` は
validator 内部の sort で、OpenMath の term や set ではない。

```text
SortExpr ::= ...base typed-math-v1 sorts...
           | RealFunction              -- ℝ → ℝ
           | Real                       -- existing primitive sort
```

`RealFunction` は `typed1:type` の annotation のみで宣言する。関数を
`OMI`、scalar term、集合、又は一般の `Fn(E,F)` に coercion しない。実数の
integer literal は、裸の `OMI` ではなく `realanalysis1:of_int(OMI)` を使う。
これにより自然数 index と実数定数を混同しない。

### 実数 core

標準 CD の記号を使う場合も、この profile 内でだけ以下の signature に固定する。
`relation1:eq` は既存 typed ルールどおり両辺の sort が完全一致したときだけ
許す。

| Symbol | Signature | 制約 |
| --- | --- | --- |
| `realanalysis1:RealFunction` | sort constructor | `typed1:type` 内だけ。 |
| `realanalysis1:of_int` | `OMI → Real` | 入力は有限の integer literal のみ。 |
| `realanalysis1:of_rat` | `OMI × OMI → Real` | 分母 literal は非零。canonical form は既約・正分母。 |
| `realanalysis1:apply` | `RealFunction × Real → Real` | 関数適用はこれだけ。 |
| `realanalysis1:lambda` | `(x : Real) . Real → RealFunction` | 一変数、実数 body のみ。捕捉・自由変数は base binder rule で reject。 |
| `arith1:plus`, `times` | `Real × Real [× …] → Real` | 空・mixed-sort application は reject。 |
| `arith1:minus`, `divide` | `Real × Real → Real` | `divide` は型だけを与える。分母非零は statement の premise。 |
| `arith1:abs`, `unary_minus` | `Real → Real` | |
| `arith1:power` | `Real × Nat-literal → Real` | 指数は 0..64 の `OMI`。実数指数は v1 外。 |
| `relation1:lt/leq/gt/geq` | `Real × Real → Prop` | |

### 現 profile の連続・微分・可積分性と将来 extension

`uIcc(a,b)` は両端点の順序を問わない closed interval、`Ioo(a,b)` は通常の
open interval とする。MVT など、空区間を避ける定理は必ず別に `a < b` を
premise とする。

| `realanalysis1` symbol | Signature | 意味 / safety decision |
| --- | --- | --- |
| `epsilon_delta_continuous_at` | `RealFunction × Real → Prop` | 直下の全量化式と同値。実装は raw ε–δ form とこの abbreviation を同一 semantics にする。 |
| `continuous_at` | `RealFunction × Real → Prop` | `ContinuousAt f a`。raw ε–δ と同値を receipt で確認。 |
| `continuous_on_uIcc` | 将来 extension | 現 registry に入れず hard reject。 |
| `differentiable_at` | `RealFunction × Real → Prop` | `DifferentiableAt ℝ f a`。 |
| `has_deriv_at` | `RealFunction × Real × Real → Prop` | `HasDerivAt f f' a`。第 2 実数は slope、total `deriv` ではない。 |
| `differentiable_on_Ioo` | 将来 extension | 現 registry に入れず hard reject。 |
| `interval_integrable` | `RealFunction × Real × Real → Prop` | `IntervalIntegrable f volume a b`。 |
| `interval_integral` | `typed-real-analysis-integral-value-v1` | 現 registry に入れず hard reject。可積分性 premise と積分値 witness を同時に要求する。 |

`deriv : RealFunction × Real → Real` は v1 に入れない。Lean の `deriv` は
非微分可能点にも total な値を返すため、`deriv f a = m` 単独で「微係数 m」
と読ませることができない。値を要求する Draft は `has_deriv_at(f,a,m)` を
使う。これが商の定義域・尖点・piecewise function で false positive を防ぐ。

## 代表 statement と完全 positive XML

次は恒等関数の ε–δ 連続性を raw formula で書いた **正しい型付き statement**
である。数学的には、任意の `a, ε>0` に対して `δ=ε` を取れることを主張する。
profile 実装後に受理する fixture であり、現 generic validator に送ってはなら
ない。`of_int(0)` が、裸の `OMI 0` を Real と解釈させない点にも注意する。

```xml
<OMOBJ xmlns="http://www.openmath.org/OpenMath" version="2.0">
  <OMBIND>
    <OMS cdbase="urn:pals:openmath:typed-math:v1" cd="typed1" name="forall"/>
    <OMBVAR>
      <OMATTR><OMATP>
        <OMS cdbase="urn:pals:openmath:typed-math:v1" cd="typed1" name="type"/>
        <OMS cdbase="urn:pals:openmath:typed-math:v1" cd="typed1" name="Real"/>
      </OMATP><OMV name="a"/></OMATTR>
    </OMBVAR>
    <OMBIND>
      <OMS cdbase="urn:pals:openmath:typed-math:v1" cd="typed1" name="forall"/>
      <OMBVAR>
        <OMATTR><OMATP>
          <OMS cdbase="urn:pals:openmath:typed-math:v1" cd="typed1" name="type"/>
          <OMS cdbase="urn:pals:openmath:typed-math:v1" cd="typed1" name="Real"/>
        </OMATP><OMV name="eps"/></OMATTR>
      </OMBVAR>
      <OMA><OMS cd="logic1" name="implies"/>
        <OMA><OMS cd="relation1" name="lt"/>
          <OMA><OMS cdbase="urn:pals:openmath:typed-math:v1" cd="realanalysis1" name="of_int"/><OMI>0</OMI></OMA>
          <OMV name="eps"/>
        </OMA>
        <OMBIND>
          <OMS cdbase="urn:pals:openmath:typed-math:v1" cd="typed1" name="exists"/>
          <OMBVAR>
            <OMATTR><OMATP>
              <OMS cdbase="urn:pals:openmath:typed-math:v1" cd="typed1" name="type"/>
              <OMS cdbase="urn:pals:openmath:typed-math:v1" cd="typed1" name="Real"/>
            </OMATP><OMV name="delta"/></OMATTR>
          </OMBVAR>
          <OMA><OMS cd="logic1" name="and"/>
            <OMA><OMS cd="relation1" name="lt"/>
              <OMA><OMS cdbase="urn:pals:openmath:typed-math:v1" cd="realanalysis1" name="of_int"/><OMI>0</OMI></OMA>
              <OMV name="delta"/>
            </OMA>
            <OMBIND>
              <OMS cdbase="urn:pals:openmath:typed-math:v1" cd="typed1" name="forall"/>
              <OMBVAR>
                <OMATTR><OMATP>
                  <OMS cdbase="urn:pals:openmath:typed-math:v1" cd="typed1" name="type"/>
                  <OMS cdbase="urn:pals:openmath:typed-math:v1" cd="typed1" name="Real"/>
                </OMATP><OMV name="x"/></OMATTR>
              </OMBVAR>
              <OMA><OMS cd="logic1" name="implies"/>
                <OMA><OMS cd="relation1" name="lt"/>
                  <OMA><OMS cd="arith1" name="abs"/>
                    <OMA><OMS cd="arith1" name="minus"/><OMV name="x"/><OMV name="a"/></OMA>
                  </OMA>
                  <OMV name="delta"/>
                </OMA>
                <OMA><OMS cd="relation1" name="lt"/>
                  <OMA><OMS cd="arith1" name="abs"/>
                    <OMA><OMS cd="arith1" name="minus"/><OMV name="x"/><OMV name="a"/></OMA>
                  </OMA>
                  <OMV name="eps"/>
                </OMA>
              </OMA>
            </OMBIND>
          </OMA>
        </OMBIND>
      </OMA>
    </OMBIND>
  </OMBIND>
</OMOBJ>
```

次は将来の `typed-real-analysis-mvt-v1` に予約する MVT statement shape である。
現 profile はこの family を hard reject する。`m` を function 値にせず、
`has_deriv_at(f,c,m)` が slope と微分可能性を同時に担保する。

```text
forall f : RealFunction, a b : Real.
  a < b ∧ continuous_on_uIcc(f,a,b) ∧ differentiable_on_Ioo(f,a,b)
  -> exists c m : Real.
       a < c ∧ c < b ∧ has_deriv_at(f,c,m)
       ∧ f(b) - f(a) = m * (b - a)
```

将来の `typed-real-analysis-integral-value-v1` の計算カードは、例えば次の形にする。
現 profile はこの `interval_integral` を hard reject する。

```text
interval_integrable(f, 0, 1)
∧ interval_integral(f, 0, 1) = 1/3
```

ここで `f` は typed `realanalysis1:lambda(x : Real). x^2`、`0`,`1`,`1/3`
は `of_int` / `of_rat` で作る。この構造により、被積分関数の代わりに scalar
を置く、端点に function を置く、といった XML を type checker が受理しない。

## positive fixture と Lean witness の対応

[`typed-real-analysis-v1-witnesses.lean`](typed-real-analysis-v1-witnesses.lean)
は pinned workspace で次の八つを検証する。OpenMath-to-Lean translator は未実装
なので、これは profile semantics と手書き witness の対応レビュー用 evidence で
あり、XML から自動証明したという主張ではない。

| Fixture family | Typed assertion | Lean lowering |
| --- | --- | --- |
| ε–δ | identity の raw ε–δ formula | `δ = ε` |
| 一点微分 | `has_deriv_at(x↦x²,a,2a)` | `HasDerivAt` |
| 微分可能性 | cubic polynomial の `differentiable_at` | `DifferentiableAt ℝ` |
| MVT | 除外：現 profile は hard reject | 将来の HasDerivAt-based exact witness が必要 |
| Taylor fixed order 2 | `x² = 0 + 0x + (2/2)x²` | exact ring calculation |
| 定積分値 | 除外：現 profile は hard reject | 可積分性 premise と結合した exact witness が必要 |
| 可積分性 | polynomial on `[0,1]` | `Continuous.intervalIntegrable` |
| 広義積分 semantic evidence | `∫_{(0,∞)} exp(-x)=1` | Mathlib improper integral theorem |

Compile command and result:

```sh
cd pals-agent/lean-workspace
lake env lean ../../docs/typed-real-analysis-v1-witnesses.lean
```

Result: exit status 0.

## Hard-negative suite

These must fail *before* canonicalization and before a Lean receipt is
created.  The diagnostic includes `symbol`, argument index, expected sort,
actual sort, and lexical binder path.

| Invalid XML intent | Required rejection |
| --- | --- |
| Send this profile's `OMATTR`, `realanalysis1:*`, or typed binder to generic-v1 | profile/CD gate; generic code remains unchanged. |
| Send `realanalysis1:*` to base `typed-math-v1` | fixed base-CD subset rejects it. |
| `apply(f : RealFunction, a : Nat)` | argument 2 expected `Real`, got `Nat`. |
| `apply(a : Real, x : Real)` | argument 1 expected `RealFunction`, got `Real`. |
| `has_deriv_at(f,a,g)` with `g : RealFunction` | slope position expected `Real`, got `RealFunction`. |
| `has_deriv_at(f,a,m)` used as a numeric equality operand | proposition/term mismatch. |
| `interval_integral(f,a,b)` | 現 registry 外なので hard reject。 |
| `interval_integrable(f,a,b) = of_int(0)` | equality mismatch `Prop` versus `Real`. |
| `arith1:plus(real, realFunction)` or `abs(realFunction)` | exact Real-argument mismatch; no pointwise coercion. |
| bare `OMI 2` in a Real slot | require `realanalysis1:of_int(2)`; a Nat literal never silently becomes a real. |
| `of_rat(p,0)` or non-canonical denominator sign | literal constructor rejects before type inference completes. |
| `power(x, y : Real)` or exponent 65 | exponent must be a 0..64 `OMI`, not a Real term or unbounded expression. |
| MVT statement | 現 registry 外なので hard reject。将来 extension では `a < b` と exact HasDerivAt witness を必須にする。 |
| Integral value card | 現 registry 外なので hard reject。将来 extension では `interval_integrable` 等の premise と exact witness を必須にする。 |
| A purported Riemann partition or infinity term is encoded via `interval1` / `nums1` | profile/CD gate rejects; these belong to later profiles. |

MVT と積分値の template は現 registry には置かない。将来 extension で exact
Lean witness と同時に導入し、prose から side condition を推測しない。

## Taylor、Riemann、広義積分をここへ入れない理由

### `typed-real-analysis-taylor-v1`

General Taylor needs a degree sort, repeated derivatives, a factorial cast,
smoothness on a closed interval, and the location of a Lagrange remainder.
Adding `calculus1:nthdiff` as a generic total term would silently assign a
derivative at points where it is not defined.  The smallest safe later module
therefore adds these signatures, all profile-local:

| Symbol | Signature |
| --- | --- |
| `smooth_on_uIcc` | `RealFunction × Nat-literal(0..8) × Real × Real → Prop` |
| `has_iterated_deriv_at` | `RealFunction × Nat-literal(0..9) × Real × Real → Prop` |
| `factorial_cast` | `Nat-literal(0..9) → Real` |
| `has_taylor_lagrange_remainder` | `RealFunction × Nat-literal(0..8) × Real × Real × Real → Prop` |

The final argument of `has_taylor_lagrange_remainder` is `c`; its semantics
includes `a<c<b` and the exact degree-`n` Taylor equality with the
`(n+1)`-st derivative at `c`.  A Taylor theorem card additionally requires
`a<b` and `smooth_on_uIcc(f,n+1,a,b)`.  The fixed quadratic Lean receipt in
this document is evidence for a future order-two fixture only; it is **not**
an admission of arbitrary Taylor statements.

### `typed-riemann-integral-v1`

`calculus1:defint` and `interval_integral` do not define Riemann
integrability by partitions.  A faithful Riemann module needs at least
dependent `Partition(a,b)`, `TaggedPartition(a,b)`, `mesh`, `riemann_sum`,
refinement/order constraints, and the ε–δ quantification over all sufficiently
fine tagged partitions.  It must also state the relationship, when intended,
between that predicate and the interval-integral value.  Without those sorts,
representing a partition as an untyped list would allow unordered points,
tags outside subintervals, and wrong endpoints.  Defer it.

### `typed-improper-integral-v1`

Do not introduce a total `improper_integral(f,a,+∞) : Real`.  The minimal
future predicate is instead:

```text
has_improper_integral_to_pos_inf(f : RealFunction, a L : Real) : Prop
```

Its semantics requires every finite `a..B` segment to be interval-integrable
and `Tendsto (fun B => interval_integral(f,a,B)) atTop (nhds L)`.  Left
infinity and finite singularities are separate symbols.  In particular, `∞`
is not a Real value and divergence is not coerced into any ordinary integral
answer.

## Implementation boundary and rollout

Implement this as a new isolated module such as
`typed_real_analysis_profile.py`:

1. Caller selects `typed-real-analysis-v1` explicitly; reject profile/CD
   mismatches before inference.
2. Reuse base typed parser, OMBVAR-only `OMATTR` gate, lexical scope,
   canonicalizer, resource limits, and alpha renaming.
3. Add only `RealFunction` plus the exact signatures above. Infer bottom-up;
   no subtyping, coercion search, or generic `term` fallback.
4. 現 registry は四つの sealed family だけを許可する。MVT と積分値は、別
   extension が profile-separated canonical/XML/Lean receipt を持つまで reject
   する。
5. Keep generated embeddings and retrieval indexes separated by
   `profile_id || canonical_xml`; do not co-index generic-v1 and typed
   real-analysis fixtures.

Do not mutate generic `_SUPPORTED_SYMBOLS`, generic `_infer_retrieval_sort`,
generic continuity logic, generic Draft builders, or the local DB.  The
profile starts with positive/hard-negative fixtures and the pinned Lean file
above; Taylor, Riemann, and improper modules each need their own CD digest,
fixture suite, and Lean correspondence review before becoming admissible.
