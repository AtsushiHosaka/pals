# typed-commutative-algebra-v1

## Requirements

`typed-commutative-algebra-v1` は、可換環上のイデアル演算に限る隔離済み
OpenMath profile である。generic retrieval、既存の `typed-math-v1`、DB seed、
埋め込み索引、PFI package を変更してはならない。候補はオリジナル文のみとし、
Atiyah--Macdonald の演習文を複製しない。

各 sealed candidate は次を満たさなければならない。

- `CommRing R`、`Ideal R`、必要なら `Elem R` を明示的に型注釈する。
- イデアル演算の各引数は同一の、束縛済み `R` に属する `Ideal R` である。
- exact C14N、raw/canonical XML、文、Lean target/witness、設計・registry・validator・
  Lean toolchain の SHA-256 を manifest に結び付ける。
- Sketch は 4--8 ステップ、Lean witness は pinned local Mathlib workspace で直接
  compile し、OpenMath から Lean への自動翻訳を主張しない。

## Scope

v1 は、イデアルの包含・和・積・交わり・radical、prime/maximal ideal と、それらの
単調性・格子性を扱う。`Ideal R` は `commalg1:Ideal(R)`、包含は
`commalg1:ideal_le(R,I,J)` とし、暗黙の carrier coercion を認めない。

許可する論理は等式／不等式、`and`、`or`、`implies`、`not`、および明示型付き
`forall` / `exists` だけである。symbol registry 外の演算、free variable、carrier の
混在、binder shadowing、typed cdbase の継承は reject する。

## Explicit deferrals

商環には quotient ring の carrier と quotient map、局所化には部分モノイド・局所化
witness・普遍性・map が必要である。v1 の `CommRing` / `Ideal` / `Elem` だけでは
それらを同じ式に型安全に束縛できないため、商環・局所化・加群・Spec・局所環は
**hard reject / defer** する。これらを token 的な predicate として偽装して受理しない。

## Design

profile id は `typed-commutative-algebra-v1`、typed cdbase は
`urn:pals:openmath:typed-commutative-algebra:v1` とする。独立 validator は registry を
読み、OpenMath core validation 後に profile の構文、直接 cdbase、型、閉性を検査して
から v4 C14N を返す。generic validator と既存 typed validators は変更しない。

sealed manifest は local authoring evidence であり、admission は独立 review が終わる
まで不可とする。generator は現在の artifacts から毎回 digest を作り直す。manifest
validator は source XML の再 canonicalize、manifest hash、artifact hash、Lean marker
binding を fail-closed で検査する。

## Tasks

1. registry と型 validator を package data として追加する。
2. original ideal-lattice candidates と直接 Lean witnesses を seal する。
3. canonicalization、carrier mismatch、unknown symbol、stale evidence、隔離性を unit test
   で検証する。
4. quotient/localization を表現できる dependent profile と witness convention が別途
   review されるまで、対象 profile に追加しない。
