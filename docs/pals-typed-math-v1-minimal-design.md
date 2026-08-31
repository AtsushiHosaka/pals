# `pals.typed-math.v1` 最小設計

## 結論

`pals.typed-math.v1` は既存の generic retrieval profile を拡張しない、別の OpenMath profile とする。
generic-v1 の受理集合、canonical bytes、既存 Draft の seed/API 契約は変更しない。

最初の実装 slice は群・環の型付き構文と正負 fixture だけを対象とし、カードを publish しない。多項式・Frechet 微分・Fubini は、card ごとの完全な signature と文面/OpenMath/Lean の対応レビューがそろう次段階へ送る。ODE、勾配、Hessian、Lagrange 乗数、変数変換は含めない。

## 非目標

- generic-v1 の `arith1:times` を抽象群・環の演算として再解釈しない。
- generic-v1 の `pals1:forall_real_function`（`ℝ → ℝ`）を多変数写像として流用しない。
- 型チェックだけで英語の `canonical_statement` と OpenMath が同値だと主張しない。
- この設計では DB、既存 seed、既存 retrieval API を変更しない。

## Profile の分離

| 項目 | generic-v1（既存） | typed-math-v1（新規） |
| --- | --- | --- |
| エントリポイント | `validate_canonical_retrieval_openmath_xml` | `validate_canonical_typed_math_openmath_xml` |
| 許容要素 | `OMOBJ, OMS, OMV, OMI, OMB, OMF, OMA, OMBIND, OMBVAR` | 左記に加えて、型注釈用の `OMATTR, OMATP` |
| 型 | `term / proposition / term_function / predicate_function` | 依存する構造型、carrier 型、関数型、命題 |
| CD | 既存 `_SUPPORTED_SYMBOLS` の固定集合 | `typed1`, `algebra1`, `analysis1`, `measure1` の固定集合 |
| canonicalizer | 既存 C14N v4 | 同じ C14N 実装を、typed validator 成功後にだけ呼ぶ |
| seed/API | 既存 schema のまま | 新しい typed-math 専用 schema/endpoint |

profile は XML の内容から自動選択しない。呼び出し側が明示的に `generic-v1` または `typed-math-v1` を指定する。未知 profile、generic endpoint に届いた typed XML、typed endpoint に届いた generic XML はいずれも reject する。

## `OMATTR` と typed binder の選択

採用案は **typed binder + `OMATTR` による binder 変数の sort 注釈** である。

- 初回sliceの binder は `typed1:forall` と `typed1:exists` だけとする。`typed1:lambda` は関数型・codomain の signature を導入する次段階まで許可しない。
- 各 `OMBVAR` 宣言は必ず一つの `OMATTR(typed1:type, SortExpr)` で包む。
- `OMATTR` は `OMBVAR` 直下の `OMV` 宣言でのみ許す。式本体、OMS、OMA、既存 generic XML での属性付与は許さない。
- typed 文書は `typed1:forall` または `typed1:exists` と、少なくとも一つの `typed1:type` 宣言を必ず含む。`quant1:*` と `fns1:*` は typed profile で禁止する。
- 型注釈は外側 scope または同じ `OMBVAR` の先行宣言だけを参照できる。forward/self reference と binder shadowing は reject する。

この選択には次の理由がある。

1. OpenMath の `OMBIND` の三要素文法を守れる。型を binder の第4引数に置く独自構文は採用しない。
2. リポジトリの core XML validator はすでに attributed OMV 宣言を構文的に扱える。`_is_bound_variable_declaration` と `_normalize_bound_declaration` は `OMATTR` で包んだ OMV を受理・alpha 正規化できる。
3. pure `OMATTR + quant1:forall` だけでは、「この式が typed profile で解釈される」という境界が不明確になる。専用 binder により generic-v1 の profile confusion を防ぐ。
4. `forall_group_element`、`forall_polynomial` のような binder を増やす方式は、`Elem(G)` や `Polynomial(K)` の依存 parameter を持てず、CD が際限なく増えるため採用しない。

型付き量化の例は次の形とする。`G` は群構造、`a,b` は `G` の carrier 要素である。

```xml
<OMOBJ xmlns="http://www.openmath.org/OpenMath" version="2.0">
  <OMBIND>
    <OMS cdbase="urn:pals:openmath:typed-math:v1" cd="typed1" name="forall"/>
    <OMBVAR>
      <OMATTR><OMATP>
        <OMS cdbase="urn:pals:openmath:typed-math:v1" cd="typed1" name="type"/>
        <OMS cdbase="urn:pals:openmath:typed-math:v1" cd="algebra1" name="Group"/>
      </OMATP><OMV name="G"/></OMATTR>
      <OMATTR><OMATP>
        <OMS cdbase="urn:pals:openmath:typed-math:v1" cd="typed1" name="type"/>
        <OMA><OMS cdbase="urn:pals:openmath:typed-math:v1" cd="typed1" name="Elem"/><OMV name="G"/></OMA>
      </OMATP><OMV name="a"/></OMATTR>
      <OMATTR><OMATP>
        <OMS cdbase="urn:pals:openmath:typed-math:v1" cd="typed1" name="type"/>
        <OMA><OMS cdbase="urn:pals:openmath:typed-math:v1" cd="typed1" name="Elem"/><OMV name="G"/></OMA>
      </OMATP><OMV name="b"/></OMATTR>
    </OMBVAR>
    <OMA><OMS cd="relation1" name="eq"/>
      <OMA><OMS cdbase="urn:pals:openmath:typed-math:v1" cd="algebra1" name="inv"/>
        <OMV name="G"/>
        <OMA><OMS cdbase="urn:pals:openmath:typed-math:v1" cd="algebra1" name="mul"/>
          <OMV name="G"/><OMV name="a"/><OMV name="b"/>
        </OMA>
      </OMA>
      <OMA><OMS cdbase="urn:pals:openmath:typed-math:v1" cd="algebra1" name="mul"/>
        <OMV name="G"/>
        <OMA><OMS cdbase="urn:pals:openmath:typed-math:v1" cd="algebra1" name="inv"/><OMV name="G"/><OMV name="b"/></OMA>
        <OMA><OMS cdbase="urn:pals:openmath:typed-math:v1" cd="algebra1" name="inv"/><OMV name="G"/><OMV name="a"/></OMA>
      </OMA>
    </OMA>
  </OMBIND>
</OMOBJ>
```

## Sort 表現

typed validator は型式を通常の term として推論しない。`typed1:type` の値だけを専用 parser で `SortExpr` に変換する。

```text
SortExpr ::= Prop | Nat | Real
           | Group | CommRing | IntegralDomain | Field
           | Elem(StructureVar)
           | Polynomial(CoefficientStructureVar)
           | GroupHom(GroupVar, GroupVar)
           | NormedRealSpace
           | Elem(SpaceVar)
           | Fn(SpaceVar, SpaceVar)
           | CLM(SpaceVar, SpaceVar)
           | Measure(SpaceVar)
           | Product(SpaceVar, SpaceVar)
           | RootMultiset(FieldVar)
```

`Group`、`Field`、`NormedRealSpace` は構造を値として束縛する sort であり、`Elem(G)` や `Polynomial(K)` はその束縛変数に依存する sort である。

型等価性は構文的等価性に限定する。`CommRing` と `Field` の暗黙部分型、`ℝ` の `NormedRealSpace`、多項式係数の暗黙 coercion は導入しない。必要な関係は CD の signature に現れる明示的な predicate または coercion operator で表す。

自然数 literal を環に入れるときは `OMI 2` を直接使わず、`typed1:nat_cast(R, 2)` を使う。これにより characteristic と係数環を明示できる。

## 依存 signature

各 symbol は `role`、arity、引数 pattern、結果型、追加制約を持つ。不特定な `term` 引数は認めない。初回sliceでは `pals-agent/pals_agent/content_dictionaries/typed-math-v1-registry.json` を exact symbol allow-list とし、signature は `typed_math.py` の group/ring inference に固定する。多項式以降を受理する前に、signature/arity/result sort も registryへ移す。標準 CD は `http://www.openmath.org/cd`、PALS typed CD は `urn:pals:openmath:typed-math:v1` を exact match し、typed CD の継承は許可しない。

| Symbol | Signature |
| --- | --- |
| `algebra1:mul` | `(G : Group, Elem(G), Elem(G)) → Elem(G)` |
| `algebra1:inv` | `(G : Group, Elem(G)) → Elem(G)` |
| `algebra1:ring_mul` | `(R : CommRing, Elem(R), Elem(R)) → Elem(R)` |
| `algebra1:poly_eval` | `(K : Field, Polynomial(K), Elem(K)) → Elem(K)` |
| `algebra1:poly_div` / `poly_mod` | `(K : Field, Polynomial(K), Polynomial(K)) → Polynomial(K)` |
| `algebra1:formal_derivative` | `(R : CommRing, Polynomial(R)) → Polynomial(R)` |
| `analysis1:has_fderiv_at` | `(f : Fn(E,F), f' : CLM(E,F), x : Elem(E)) → Prop` |
| `analysis1:fn_compose` | `(f : Fn(E,F), g : Fn(F,H)) → Fn(E,H)` |
| `analysis1:clm_compose` | `(L : CLM(F,H), M : CLM(E,F)) → CLM(E,H)` |
| `analysis1:fderiv` | `(f : Fn(E,Real), x : Elem(E)) → CLM(E,Real)` |
| `measure1:integrable` | `(f : Fn(Product(A,B),E), μ : Measure(A), ν : Measure(B)) → Prop` |
| `measure1:integral_prod` | `(f : Fn(Product(A,B),E), μ : Measure(A), ν : Measure(B)) → Elem(E)` |

`relation1:eq` は typed profile で特別扱いする。両辺の inferred `SortExpr` が完全に一致しなければ reject する。`logic1:*` の引数は `Prop` のみ、`typed1:forall/exists` の body は `Prop`、`typed1:lambda` の body は宣言した codomain と一致しなければならない。

## 検査アルゴリズム

1. **Core parse**: 現在の `validate_openmath_xml` で XML namespace、DTD 禁止、OMBIND の形、XML ID を検査する。
2. **typed element gate**: `typed-math-v1` だけが `OMATTR`/`OMATP` を許す。許容位置は `OMBVAR` 内の declared OMV のみ。属性 key は一つの `typed1:type` のみ。
3. **CD gate**: `typed1`, `algebra1`, `analysis1`, `measure1` と、型なし論理用の `logic1`, `relation1` だけを exact cdbase で許す。未知 CD、未知 symbol、CD base の継承は reject する。
4. **Environment construction**: OMBIND を preorder で歩き、各 attributed OMV から `name → SortExpr` を構築する。束縛名の重複、自由 OMV、型式内の未束縛構造変数を reject する。
5. **Bottom-up inference**: literal、OMV、OMS、OMA、OMBIND ごとに `SortExpr | Prop` を返す。operator signature の pattern variable を unification し、結果型を代入する。
6. **Dependent consistency**: `Elem(G)` の G、`Polynomial(K)` の K、`Fn(E,F)` の E/F、`CLM(E,F)` の E/F を全引数で一致させる。構造変数が違う場合は coercion を探索しない。
7. **Proposition closure**: root は `Prop`、全 OMV は lexical に束縛済み、すべての型 annotation は closed とする。
8. **Resource and canonicalization**: generic-v1 と同じ byte/node/depth/attribute 上限を適用してから `_canonicalize_openmath_v4_root` を呼ぶ。alpha 正規化後も type annotation 内の構造変数を同じ environment で rename する。

型エラーは最初の不一致に、`symbol`、argument index、expected sort、actual sort、関連する binder path を添えて失敗させる。型推論に backtracking、subtyping 探索、任意の Lean 実行は含めない。

## 17件を通す最小 CD subset

| Module | 必要カード | 最小機能 |
| --- | --- | --- |
| `typed1` | 全17件 | typed binder、`type` attribute、`Elem`、`Fn`、`CLM`、`nat_cast`、型付き equality |
| `algebra1.group` | group 5件 | `Group`, `Elem`, `mul`, `inv`, `one`, `GroupHom`, `kernel`, `normal_subgroup`, `exists_unique` |
| `algebra1.ring` | ring 3件 | `CommRing`, `IntegralDomain`, `ring_add/mul/neg/zero/one`, `neq`, `nat_cast` |
| `algebra1.polynomial` | polynomial 5件 | `Field`, `Polynomial`, `poly_eval`, `poly_X`, `poly_C`, `poly_dvd`, `poly_div`, `poly_mod`, `poly_degree`, `poly_nat_degree`, `poly_roots_card`, `formal_derivative` |
| `analysis1.frechet` | chain/product/Fermat 3件 | `NormedRealSpace`, `Fn`, `CLM`, `has_fderiv_at`, `fderiv`, function/CLM composition, pointwise scalar multiplication, zero CLM |
| `measure1.fubini` | Fubini 1件 | `Measure`, `Product`, `Fn`, `integrable`, `product_measure`, product/iterated Bochner integral、`SFinite` predicate |

`interval1` は最初の実装 slice に必要ない。Fubini を「閉区間上の連続関数」へ戻すと、後続 module として closed interval、Lebesgue restriction、compactness、continuityからの integrability を追加する必要がある。

次は初期 subset に含めない。

- `gradient`、`partial_derivative`、`hessian`、positive definite matrix
- manifold/tangent space と Lagrange multiplier
- C¹ diffeomorphism と Jacobian change of variables
- `ODE_RHS`、oriented interval、solution predicate、Lipschitz condition、second derivative

## 現行コードへの最小変更点

| 箇所 | 変更 | generic-v1 への影響 |
| --- | --- | --- |
| `pals_agent/openmath.py:140-161` | profile 非依存の `TypedSymbolSpec`/`SortExpr` は新 module へ置き、既存 `_SymbolSpec` は変更しない | なし |
| `pals_agent/openmath.py:369-431` | `validate_canonical_typed_math_openmath_xml` と `canonicalize_typed_math_openmath_xml` を追加。既存 generic 関数は変更しない | なし |
| `pals_agent/openmath.py:2918-2964` | `_validate_retrieval_openmath_profile` は変更しない。typed 専用 `_validate_typed_math_profile` を新設する | なし |
| `pals_agent/openmath.py:3332-3404` | `_infer_retrieval_sort` は generic のまま。typed 用 `infer_typed_sort` を新設する | なし |
| `pals_agent/openmath.py:3444-3452` | core XML validator の既存 OMATTR 構文検査を再利用する。typed profile 側で許容位置を追加制限する | なし |
| `pals_agent/content_dictionaries/` | `typed1.ocd`, `algebra1.ocd`, `analysis1.ocd`, `measure1.ocd` を追加 | なし |
| `pals_agent/draft_catalog.py:104-114` | `ProofDraft` と generic `validate_draft_xml` は変更しない。`typed_draft_catalog.py` に `TypedProofDraft` を新設する | なし |
| `pals_agent/proof_flow_seed.py:795-824` | `ProofDraftSeedBuilder` は変更しない。`TypedMathSeedBuilder` を別 schema/manifest/canonicalizer version で追加する | なし |
| `pals_agent/private_draft_candidates.py:288-305` | generic v1 の exact object contract は維持する。typed candidate reader/endpoint を別 module/v2 contract にする | なし |

実装上、`typed_math_profile.py` は `validate_openmath_xml` と `_canonicalize_openmath_v4_root` を利用できるよう、必要最小の core helper を public に昇格する。typed module が generic `_SUPPORTED_SYMBOLS` を mutate してはならない。

## admission と Lean receipt

typed XML の型検査は Lean の定理検査ではない。最初の17件の admission では次を必須にする。

- typed OpenMath canonical bytes と `openmath_profile = typed-math-v1`
- `lean_target_sha256`、`lean_witness_sha256`、pinned toolchain digest
- receipt の `status = verified`
- type-CD bundle digest

XML と Lean target の意味的対応は、v1 では人手レビュー＋fixture で扱う。機械的な OpenMath-to-Lean translation を実装するまでは「型が通る」ことを「証明済み」や「英語文と同値」と言い換えない。

embedding/fingerprint と retrieval index は profile を分ける。embedding canonical text は少なくとも `profile_id || canonical_xml` を hash preimage に含め、generic-v1 と typed-math-v1 の候補を同一 generation に混在させない。

## hard-negative テスト

以下は typed profile の unit test として固定する。

| ケース | 期待結果 |
| --- | --- |
| generic validator に `typed1:forall` または OMBVAR 内 OMATTR を送る | generic profile reject |
| typed endpoint に profile field のない generic candidate を送る | profile mismatch reject |
| `a : Elem(G)` に `algebra1:mul(H,a,b)` を適用する | expected `Elem(H)` mismatch |
| `inv(G,a)` に `a : Elem(H)` を渡す | carrier mismatch |
| `eq(a,b)` で `a : Elem(G)`, `b : Elem(H)` | equality type mismatch |
| `poly_eval(K,p,x)` で `p : Polynomial(K)`, `x : Elem(L)` | coefficient carrier mismatch |
| `poly_div(K,p,q)` の q を `Elem(K)` にする | expected polynomial mismatch |
| `has_fderiv_at(f,L,x)` で `L : CLM(F,E)` | derivative map orientation mismatch |
| `fn_compose(f:E→F,g:H→K)` | f codomain / g domain mismatch |
| Fubini の f を `A×B→E` 以外にし product measureを `C×B` にする | product measure domain mismatch |
| `OMI 2` を `Elem(R)` 位置へ直接渡す | explicit `nat_cast` required |
| OMBVAR 外の OMATTR、複数 `typed1:type` attribute、unknown attribute key | typed element gate reject |
| type annotation に未束縛 `K` を含める | free sort variable reject |
| alpha 正規化で `G` を rename しても `Elem(G)` annotation だけ古い名前に残る fixture | canonicalization/closure reject |
| 既存 generic fixture の canonical byte/hash | 変更なし |

さらに17枚の各 card family（group/ring/polynomial/Frechet/measure）に一件ずつ positive fixture を置く。fixture は typed XML、canonical bytes、expected inferred root sort、Lean receipt digest を固定する。

## 段階導入

1. Core parser と profile isolation、typed1/algebra1 の group/ring fixtures。
2. Polynomial module と、card ごとの対応レビュー済み Lean receipt admission。
3. `analysis1.frechet` と chain/product/Fermat の、対応レビュー済み card。
4. `measure1.fubini` を完全な signature と対応レビュー後に、既定offの別 feature flag で導入する。
5. Typed seed builder、typed retrieval endpoint、profile-separated embedding/index を別 milestone として追加する。

各段階で generic-v1 の既存 test suite、canonical bytes、seed manifest digest を regression gate とする。typed profile は shared/prod DB に投入せず、独立した local fixture catalog でのみ開始する。
