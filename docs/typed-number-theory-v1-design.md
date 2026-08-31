# typed-number-theory-v1

高校数学から大学初年級までの初等整数論のうち、carrier を明示しないと
意味が変わる部分だけを扱う、generic Draft とは独立した authoring profile。

## v1の受理範囲

- `Nat` と `Int` は別sort。暗黙coercionはない。
- OMI は直接値ではなく、`nat_literal` / `int_literal` によって明示的に
  carrier 化する。負の `Nat` literal は拒否する。
- `gcd`, `lcm`, `divides_nat`, `nat_mod`, `congruent_nat`, `is_prime` は `Nat`。
- `divides_int`, Bezout の係数計算は `Int`。`int_of_nat` が唯一の
  `Nat → Int` 変換である。
- `nat_mod` と `congruent_nat` の法は、正の `nat_literal` に限る。
  従って法 0 と、0でないことを証明していない変数の法は v1 で拒否する。

## v1で扱わないもの

- 変数法の合同、Chinese remainder theorem、剰余環、p進評価、
  Dirichlet型の素数定理、負の自然数へのtotalized除算。
- 標準OpenMathの `arith1:divide` や未型付けの `relation1:divides`。
  これらは 0 除算・carrier・符号の解釈を十分に固定できない。

## 封印と入庫境界

候補manifestは、profile validator・registry・Lean witness・設計文書の
SHA-256を結び、各カードを C14N した OpenMath と Lean target/witness の
digestで固定する。これはローカルauthoring evidenceであって、generic DB、
seed、embedding index、PFI packageには入れない。いずれかのartifactが
変化すればmanifest validatorは stale として拒否する。
