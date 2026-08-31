# `typed-commutative-algebra-integral-v1`

## 要求と目的

CA-5 の初期sliceとして、整依存と付値環の**基礎命題だけ**を、既存の
`typed-commutative-algebra-v1`、局所化profile、generic Draft DBから分離して表現する。
問題はすべて独自に書き、既存の書籍の本文・演習文・番号を複製しない。

各sealed cardは、閉じた型付きOpenMath、C14N-v4、4--8のSketch、pinned Mathlibの直接
Lean witness、statement--OpenMath--Leanのalignment、すべてのartifact digestを持つ。
OpenMathからLeanへの自動翻訳は主張しない。manifestはlocal authoring evidenceだけであり、
generic DB、seed、embedding index、PFI packageへは投入しない。

## 型と意味

- `R : CommRing`、`D : Domain`、`K : Field` は互いに異なるcarrier sortである。
- `S : Extension(R)` は、明示された `R` 上の可換環拡大carrierである。`extension_map(R,S,x)`
  は `x : Elem(R)` にしか適用できない。
- `is_integral(R,S,x)` は `S : Extension(R)` と `x : Elem(S)` を同時に要求する。
  `is_integral_extension(R,S)` はこの指定された拡大がintegralであるという命題である。
- `V : ValuationRing(K)` は、明示されたfield `K` のvaluation subring carrierである。
  `valuation_mem(K,V,x)` と `field_inv(K,x)` は `x : Elem(K)` だけを受け取る。

carrier名、拡大の向き、field ambientが少しでも一致しない場合はrejectする。free variable、
shadowing、typed cdbaseの継承、裸の整数リテラル、registry外symbolもrejectする。

## v1で受理する範囲

整依存では、base-map、0/1、和・差・積・負元・平方の閉性、および明示されたintegral
extensionから各元のintegralityを扱う。付値環では、元または逆元のmembership、0/1、加法・
減法・乗法・負元・平方に関する閉性、およびvaluation subringがintegrally closedであることを
扱う。Lean witnessは `IsIntegral`、`Algebra.IsIntegral`、`ValuationSubring` の同じ主張を使う。

## hard reject / defer

次はこのprofileの意味域外であり、tokenだけのpredicateとして受理しない。

- zero divisorを許すfraction fieldや、`CommRing` をdomain/fieldへ暗黙coerceする主張;
- 複数拡大のscalar tower、integrality transitivity、finite-module criterion、integral closureの
  universal property;
- lying-over、going-up、going-down、Spec、prime chains;
- fractional ideal、DVR、Dedekind domain、value group、uniformizer、completion;
- base ring・target・ambient fieldが明示されない整依存／付値の主張。

これらには別profile、追加の依存carrier、対応するLean証拠とhard-negative testsが必要である。

## 実装タスク

1. 固定registryとfail-closed validatorをpackage dataとして追加する。
2. 20件の独自cardと直接Lean witnessをsealed manifestへ生成する。
3. C14N、carrier mismatch、extension direction、valuation-field mismatch、未知symbol、
   stale digest、generic/base typed math隔離を専用testで検証する。
