# 可換環論: Atiyah--Macdonald 相当の Draft coverage map

## 目的と境界

目標は、Atiyah--Macdonald の章構成に相当する概念・典型的な証明技法・反例構成を、**独自に書いた**問題で一通り学べる Draft catalog にすることである。本文・演習の文面、番号、解答を複製しない。章の対応は版元が示す目次を参照したものであり、以下の問題粒度・分類は PALS 独自である。[Routledge の目次](https://www.routledge.com/Introduction-To-Commutative-Algebra/Atiyah-MacDonald/p/book/9780367091286)

「演習が全部入っている」は、問題文の複製数では判定しない。次の三つを全 concept family で満たす場合だけ、**Atiyah--Macdonald 相当の演習到達範囲**と表示できる。

1. 定義の識別、具体例・反例、計算／構成、証明、他章への接続を少なくとも一件ずつ持つ。
2. それぞれの主張が独立した OpenMath、4--10 の Sketch、Lean witness、statement--OpenMath--Lean alignment review を持つ。
3. 独立レビューで、各 chapter family の依存関係と難度帯に穴がないと判定される。

数値係数や変数名だけを変えたものは別 Draft と数えない。各 family では原則として「定義判定 → 例／反例 → 構成 → 基本証明 → 合成証明」を別の問題型として作る。

## 現状監査（2026-08-10）

`typed-math-v1` の `group-ring-typical-theorems` proposal は22件である。内訳は群9、可換環の加法・乗法恒等式11、整域の零積則2である。別の core proposal 3件は同じ初期 profile の fixture であり、この22件の可換環論達成度に上乗せしない。

`typed-commutative-algebra-localization-v1` は、既存 profile と分離して、局所化の
最小core **23件**を sealed local authoring evidence として実装した。各件は明示的な
`CommRing R`、`Submonoid(R)`、`Localization(R,M)`、拡大／縮約idealを持ち、pinned
Mathlib Lean witness、C14N、artifact digestに束縛される。これは generic DB や PFI へ
admit された件数ではなく、独立review前の候補である。

`typed-commutative-algebra-decomposition-v1` は CA-4 の安全な最初の **22件**を
sealed local authoring evidence として実装した。対象は explicit `Ideal(R)`、
`PrimaryIdeal(R)`、`PrimeIdeal(R)`、二項／三項の交わり、radical、与えられた二成分／
三成分 decomposition、primary component の radical 上の minimal-prime witness である。
associated primes、Noetherian 仮定を使う分解の存在、任意有限個の成分、商・局所化成分は
語彙に入れず hard reject する。従って22件は Chapter 4 の54件目標や、一般の primary
decomposition theorem を達成したという意味ではない。

`typed-commutative-algebra-chain-dimension-v1` は CA-6 の安全な最初の核として
**17件**を sealed local authoring evidence にした。対象は Noetherian/Artinian ring、
同一 carrier の有限生成 ideal、Hilbert 基底定理の一・二回反復、`KrullDimLE 0`、および
素 ideal が極大となる次元零結論である。一般のideal chain、有限長 module、`Spec`、
height、一般 Krull 次元、多項式次元公式は表現しておらず、DB/PFIへadmitされた件数でもない。

現状、次は **0件または profile 未実装** のままである。

- ideal、商環、素・極大、Spec
- module、準同型、exact sequence、tensor/Hom、Nakayama
- module localization、複数局所化間の map、local property、fraction field
- integral element、integral closure、valuation、DVR/Dedekind
- Noetherian/Artinian の module chain・有限長・商／extension安定性、一般 Krull 次元・
  height・prime chain・completion
- completion、Krull dimension、height、chains of primes

このため、22件を可換環論の進捗率に換算してはならない。これは前提代数の小さな核であり、下記500件目標に対する証明形式の検証済み seed にすぎない。

## 目標量と chapter map

初版目標は **500個の非重複な独自 Draft** である。各件数は「問題文」ではなく、異なる概念操作または証明戦略の数である。`Lean feasibility` は theorem が真であることではなく、PALS の profile・alignment・pinned Lean 環境まで無理なく届く見込みを表す。

| Chapter family | Concept families / required skills | 前提 | 目標 | Typed profile need | Lean feasibility |
| --- | --- | --- | ---: | --- | --- |
| 0. 基礎ゲート | 可換環・準同型、subobject、集合包含、全称／存在、直接証明・背理法・反例 | 学部初年の代数 | 24 | generic logic + frozen `typed-math-v1` | 高 |
| 1. Rings and ideals | units, zero divisors, nilpotents, idempotents; generated/sum/product/intersection ideals; quotient; radical/Jacobson radical; prime/maximal ideals; polynomial examples | 0 | 56 | `typed-commalg-v1`: ring, ideal, quotient, predicates | 高〜中 |
| 2. Modules | submodule/quotient/direct sum; generators, free/finitely generated; kernels/images; exact sequences; Hom/tensor and universal properties; Nakayama | 1 | 58 | module, linear map, exactness, tensor/Hom | 中 |
| 3. Fractions | multiplicative sets; equality/zero tests; universal property; localization of modules; extension/contraction; local rings; checking a property locally | 1--2 | 48 | localization maps and localized ideals/modules | 中 |
| 4. Primary decomposition | primary ideals; associated/minimal primes; irredundant/minimal decompositions; isolated/embedded components; calculate decompositions in small rings | 1--3, 6--7 | 54 | primary/radical/associated-prime predicates; finite intersections | 中〜低 |
| 5. Integral dependence and valuations | integral elements/extensions; finite module criterion; integral closure; lying-over/going-up/going-down; valuation rings; algebraic examples | 1--3 | 48 | field/domain extensions, integrality, valuations | 中〜低 |
| 6. Chain conditions | ACC/DCC; Noetherian/Artinian modules; submodule, quotient, extension stability; finite generation; finite length | 2 | 26 | module chains and well-foundedness/finite length | 中 |
| 7. Noetherian rings | Hilbert basis theorem; Noetherian modules/algebras; ideals in polynomial rings; localization/quotients; existence uses for primary decomposition | 1--3, 6 | 42 | Noetherian predicates plus polynomial/localization modules | 中 |
| 8. Artin rings | Artinian criterion; length/composition factors; nilpotent radical; decomposition into local factors; examples and nonexamples | 1--2, 6 | 30 | finite length, quotient/product, local Artin structure | 中〜低 |
| 9. DVR and Dedekind domains | valuation/DVR tests; fractional and invertible ideals; factorization of nonzero ideals; localization at primes; number-theoretic examples | 3, 5--8 | 38 | fraction field, fractional ideals, DVR/Dedekind predicates | 低 |
| 10. Completions | I-adic filtrations/topology; separatedness/completeness; inverse systems; completion of modules; exactness/boundary counterexamples | 2, 6--8 | 30 | powers of ideals, inverse limits, completion maps | 低 |
| 11. Dimension theory | prime chains, height, Krull dimension; localization/quotient/polynomial behavior; principal-ideal bounds; calculate dimensions of standard examples | 1, 3, 5, 7 | 46 | Spec, chains, height/dimension, polynomial extension | 中〜低 |
| **合計** |  |  | **500** |  |  |

## 各 chapter の問題型配分

件数を水増しせず、各章の target を次の problem mode で配分する。例として Chapter 1 の56件は、定義識別10、具体例／反例12、構成12、element/ideal chase12、定理の仮定検査・応用10という別型で構成する。

| Mode | 必須成果 | 目安 | 禁止する水増し |
| --- | --- | --- | --- |
| definition discrimination | 似た概念の必要十分条件を区別する | 各 family 1--3 | 定義語を言い換えるだけ |
| concrete construction | 小さい環・module・idealを具体的に作る／計算する | 各 family 1--4 | 同じ環で係数だけ変更 |
| proof by containment / diagram chase | 双方向包含、kernel/image、普遍性を使う | 各 family 1--4 | 一行の `simp` 相当を別問題化 |
| counterexample / hypothesis audit | 仮定を一つ外したときの失敗を示す | 各 family 1--2 | 真偽だけで理由がない問題 |
| bridge theorem | 次章で使う補題を前提と結論ともに運用する | 各 chapter 6--12 | 同一定理の数値例を量産 |

## profile と admission の設計

既存の `typed-math-v1` は immutable に保つ。そこへ ideal や module を足すと registry digest と既存 card の受理意味を変えてしまうためである。

| Milestone | 新 profile / module | 最初に表現するもの | 対応章 | admission 前の必須 gate |
| --- | --- | --- | --- | --- |
| CA-1 | `typed-commalg-v1.core` | CommRing/Domain/Field, hom, ideal, quotient, `isPrime`, `isMaximal`, radical | 1 | carrier mismatch・ideal containment・quotient map の hard negatives |
| CA-2 | `typed-commalg-v1.modules` | Module, submodule, linear map, kernel/image, direct sum, exactness | 2, 6 | scalar-ring mismatch、map domain/codomain mismatch、free variable rejection |
| CA-3 | `typed-commutative-algebra-localization-v1` | multiplicative set, one explicit localization carrier, map, extend/contract | 3, 7, 9, 11 | inverted element side condition、map compatibility、localization carrier mismatch |
| CA-4 | `typed-commutative-algebra-decomposition-v1` | primary/radical/prime carriers、二項／三項 intersection、与えられた finite decomposition、minimal-prime witness | 4, 7--8 | primary-vs-prime confusion、carrier mismatch、Noetherian/associated-prime claim の hard reject |
| CA-5 | `typed-commalg-v1.integral` | integral extension/closure, valuation, fraction field, DVR/Dedekind | 5, 9 | domain/field assumptions、extension direction、fractional-ideal carrier mismatch |
| CA-6 | `typed-commutative-algebra-chain-dimension-v1` | Noetherian/Artinian ring, typed `Ideal(R)` finite generation, Hilbert basis one/two iterations, `KrullDimLE 0`, prime-to-maximal consequence | 6--8, 11 | ring/ideal carrier mismatch、unbounded dimension symbol、general chain／Spec／height hard reject |

各 milestone は、profile validator・fixed CD registry・positive/negative fixture・独立 manifest・pinned Lean witness を揃えるまで、DB には投入しない。generic の6列 Draft DB に typed card を混ぜない。

## dependency order

```text
0 → 1 → 2 ─┬→ 3 ─┬→ 4
            │      ├→ 5 → 9
            └→ 6 → 7 → 8
                     └→ 10 → 11
```

- Chapter 4 は Noetherian existence 系を使うため、まず Chapter 1 の具体分解を、次に Chapter 6--7 を通して一般論を作る。
- Chapter 9 は Chapter 5 の integral/valuation と Chapter 3 の localization に依存する。
- Chapter 10--11 は notation だけ先に置かず、ideal/module/localization の検証済み semantics を再利用する。

## 実施順と release gate

1. **CA-1（56件）**: 22件の既存恒等式を「前提」として残し、ideal/quotient/prime/radical を最優先で増やす。ここが可換環論として最初に可視化できる最低ラインである。
2. **CA-2 + CA-3（106件）**: CA-3 はまず局所化core 23件をsealed実装した。module と局所化を一体で拡張・authoring し、48件の局所化目標と58件のmodule目標に到達する。どちらかだけでは Atiyah--Macdonald 型の問題解決力にならない。
3. **CA-4 + CA-5（102件）**: primary decomposition、integral dependence、valuation。一般 theorem は仮定の明示を最重要 gate にする。
4. **CA-6 と chain/Noetherian/Artin（144件）**: まず Noetherian/Artinian・有限生成・
   Hilbert基底・次元零の17件を sealed化した。次に module chain、有限長、DVR/Dedekind、
   completion、prime chain／height／一般次元を、依存carrierを持つ別profileで投入する。
5. **独立監査（500件）**: family×mode matrix の空白、canonical collision、Lean receipt、近傍の偽命題を検査し、初めて「相当の演習到達範囲」と表示する。

進捗表示は `draft count / 500` だけにしない。chapter ごとに、(a) family coverage、(b) five problem modes、(c) Lean-aligned cards、(d) hard-negative coverage を別々に示す。たとえば primary decomposition が20件あっても反例・Noetherian 前提・minimality がなければ未達とする。

## 全分野へ適用する共通基準

可換環論を例外的に厚くするのではなく、他分野にも「教科書／標準講義の演習一冊分相当」の coverage map を作る。各分野は、(1) canonical reference の章/family、(2) prerequisite graph、(3) family×mode matrix、(4) target count、(5) profile/Lean feasibility、(6) independent gap audit を持たなければならない。

ただし、reference の演習を逐語的に収録した、または全問を収録したとは表示しない。copyright を守りつつ到達範囲を比較可能にする表示は、常に「独自問題による概念・技法カバレッジ」である。
