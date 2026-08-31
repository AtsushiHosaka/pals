# `pals.typed-finite-graph.v1` 設計案

## 結論

有限単純無向グラフの Draft は、既存 `generic-v1` と `typed-math-v1` のいずれにも
足さず、`typed-finite-graph-v1` という **sibling profile** に分離する。対象は大学2年までで
頻出の有限グラフ、次数、握手補題、木、連結性、二部性、Euler 路である。

初期 admission は、有限・単純・無向という一つのモデルを明記した一方向の定理だけに限る。
特に Euler 路の「次数条件から路が存在する」逆向きは、対応する Lean witness が検証されるまで
候補扱いに留める。これにより、型が通るだけの未検証な Euler 定理を Draft として混入させない。

本書の v1 scope は local authoring boundary として実装済みである。実装は
`pals_agent.typed_finite_graph` と profile 専用 registry に隔離し、DB、generic catalog、
既存 validator の受理集合は変更しない。sealed manifest は local evidence に限り、Draft の
publish・embedding・PFI package への admission は含意しない。

## OpenMath CD の位置付け

OpenMath の CD は参照できるが、この profile の型体系そのものにはしない。

| CD と cdbase | status | 正確な用途 | この profile での扱い |
| --- | --- | --- | --- |
| `graph1` / `http://www.openmath.org/cd` | experimental | `graph`, `digraph`, `vertexset`, `edgeset`, `arrowset`, `source`, `target` | 任意の OpenMath object を頂点にできる構成表現。typed theorem の入力にはしない。 |
| `graph2` / `http://www.openmath.org/cd` | experimental | graph automorphism/homomorphism/isomorphism の述語群 | 本 slice の対象外。次数・木・連結・二部・Euler の型付き意味を提供するものとして扱わない。 |
| `graph3` / `http://www.openmath.org/cd` | experimental | `mixedgraph`, `labelledgraph` | 多重・混合・ラベル付きグラフであり、有限単純無向モデルには入れない。 |
| `logic1`, `relation1` / `http://www.openmath.org/cd` | official standard CD | 論理結合子、等号 | exact cdbase で最小 allow-list として使う。等号の同型判定は sibling validator が行う。 |
| `pals_typed_graph` / `urn:pals:openmath:typed-finite-graph:v1` | private | 下記の sort、binder、有限グラフ定理語彙 | 唯一の typed graph 語彙。継承 cdbase は不可。 |

`graph1` は公式 OpenMath サイトで公開されているが、status は experimental であり、同 CD の
公開 symbol は構成子群に限られる。[`graph1`](https://openmath.org/cd/graph1.html)
の `graph(V,E)` は任意の OpenMath object を頂点に許すため、有限性、simple/loopless、頂点の
carrier identity、次数や path の型を保証しない。`graph3` も experimental で、mixed/labelled
graph 用である。[`graph3`](https://openmath.org/cd/graph3.html) OpenMath の CD 一覧も
`graph1`、`graph2`、`graph3` を experimental としている。[CD index](https://openmath.org/cdnames/)

従って、public `graph1:*` を `FinSimpleGraph` と同一視してはならない。外部 `graph1` XML を
取り込む場合も将来の `pals_typed_graph:import_graph1_simple` adapter に限り、別 manifest に
有限性・loopless・simple・undirected を機械検査した certificate とその digest を必須にする。
certificate のない `graph1:graph` は typed profile で reject する。初期 slice は adapter 自体を
実装しない。

## Profile 境界

| 項目 | generic-v1 | typed-math-v1 | typed-finite-graph-v1（提案） |
| --- | --- | --- | --- |
| profile ID | `generic-v1` | `typed-math-v1` | `typed-finite-graph-v1` |
| typed cdbase | なし | `urn:pals:openmath:typed-math:v1` | `urn:pals:openmath:typed-finite-graph:v1` |
| graph の carrier | なし | なし | `FinSimpleGraph` と `Vertex(G)` |
| entry point | 既存 generic | 既存 typed math | 新設 `validate_canonical_typed_finite_graph_openmath_xml` |
| index/manifest | generic schema | typed-math manifest | profile 固有 manifest。generic reader は reject |

呼出元は profile を明示指定する。XML 内容から profile を推測しない。次は entry point の前に
reject する。

- generic に `pals_typed_graph:*` 又は `OMATTR` 型宣言を送る。
- typed-math に graph profile の cdbase を送る、又はその逆。
- typed-finite-graph に generic `quant1:*`、`fns1:*`、base cdbase の継承、未知 symbol を送る。

この分離は generic の受理集合・canonical bytes・DB six-column contract を変えないための必須条件で
ある。既存 `typed-math-v1` と CD 名が衝突しないよう、private CD 名も `graph1` の派生名ではなく
`pals_typed_graph` とする。

## 数学モデルと sort

`FinSimpleGraph` は有限、無向、loopless、重複辺なしのグラフ値である。孤立頂点は許す。multi-graph、
directed graph、weighted graph、hypergraph、無限グラフは reject する。

```text
SortExpr ::= Prop | Nat | FinSimpleGraph
           | Vertex(GraphVar)
           | VertexClass(GraphVar)
           | Trail(GraphVar)
```

- `Vertex(G)` はグラフ値 `G` に依存する carrier である。`Vertex(G)` と `Vertex(H)` は、`G` と `H`
  が別の binder なら構文的に異なる。isomorphism や implicit transport は探索しない。
- `VertexClass(G)` は `G` の頂点集合の部分集合を表す opaque value であり、全域性を含む二部分割の
  witness として使う。`VertexClass(H)` を受け取る位置には渡せない。
- `Trail(G)` は有限 edge 列、連続性、edge 参照が `G` に属することを持つ opaque witness である。
  リストを generic `list1` で直に渡す方式は取らない。
- `Nat` は非負の `OMI` のみを受ける。負の `OMI` と、`Vertex(G)` 等への literal coercion は reject
  する。

`tree(G)` は「連結かつ acyclic」と定義する。`|E|=|V|-1` を定義にせず、後者を有限木の定理として
表す。空グラフが木かという教科書差異を、`Nat` の切詰め減算や暗黙 convention で隠さないためである。

Euler 条件の連結性は `nonisolated_connected(G)`、すなわち正次数頂点が一つの連結成分にあることを
意味する。孤立頂点を含む三角形には Euler circuit があるため、ここを単なる `connected(G)` と
してはならない。edge がないグラフではこの predicate を true（support が空なら vacuous）と定める。
これにより長さ 0 の Euler trail/circuit を持つという convention と、`odd_degree_count(G)=0` が整合する。

## exact typed signature

全ての private symbol は `cdbase="urn:pals:openmath:typed-finite-graph:v1"` を直接持つ。public
`logic1`/`relation1` も `http://www.openmath.org/cd` を直接持つ。祖先 `OMOBJ` 等からの cdbase
継承は両方とも reject する。

| Symbol | arity / signature | 定義上の制約 |
| --- | --- | --- |
| `pals_typed_graph:forall`, `exists` | typed binder | body は `Prop`。各 `OMBVAR` は一個だけの `type` OMATTR を持つ。 |
| `pals_typed_graph:type` | OMATTR key | `OMBVAR` 直下の宣言 `OMV` にのみ許可。 |
| `pals_typed_graph:FinSimpleGraph` | sort constant | finite, undirected, loopless, simple。 |
| `pals_typed_graph:Vertex(G)` | `(G : FinSimpleGraph) -> Sort` | graph-indexed vertex carrier。 |
| `pals_typed_graph:VertexClass(G)` | `(G : FinSimpleGraph) -> Sort` | graph-indexed vertex subset。 |
| `pals_typed_graph:Trail(G)` | `(G : FinSimpleGraph) -> Sort` | graph-indexed finite trail witness。 |
| `degree(G,v)` | `(G : FinSimpleGraph, Vertex(G)) -> Nat` | `G` 内の次数。 |
| `vertex_count(G)`, `edge_count(G)`, `degree_sum(G)`, `odd_degree_count(G)` | `(G : FinSimpleGraph) -> Nat` | `degree_sum` は全頂点次数和、`odd_degree_count` は奇数次数頂点数。 |
| `nat_add`, `nat_mul` | `(Nat,Nat) -> Nat` | integer/ring の暗黙 coercion なし。 |
| `adjacent(G,u,v)` | `(G, Vertex(G), Vertex(G)) -> Prop` | simple graph の隣接。 |
| `connected(G)`, `nonisolated_connected(G)`, `acyclic(G)`, `tree(G)`, `bipartite(G)` | `(G : FinSimpleGraph) -> Prop` | 上記モデルでの述語。 |
| `proper_bipartition(G,L,R)` | `(G, VertexClass(G), VertexClass(G)) -> Prop` | `L∩R=∅`, `L∪R=V(G)`, 全辺が class をまたぐ。 |
| `is_euler_trail(G,t)`, `is_euler_circuit(G,t)` | `(G, Trail(G)) -> Prop` | 各 edge をちょうど一回通る。circuit は始点=終点も要求。 |
| `has_euler_trail(G)`, `has_euler_circuit(G)` | `(G : FinSimpleGraph) -> Prop` | 上記 witness の存在を意味する。 |

`relation1:eq` と `relation1:neq` は両辺の inferred sort が完全一致するときだけ `Prop` となる。
`logic1:and/or/implies/not` は `Prop` のみ、root も `Prop` のみ受理する。sort equality は structural
equality だけで、graph isomorphism、subgraph inclusion、暗黙の `Vertex(G) -> Vertex(H)` は含めない。

## binder と XML 形

typed-math-v1 と同様、`OMBIND` の三要素文法を維持し、binder variable を
`OMATTR(typed-graph:type, SortExpr)` で注釈する。型 annotation は先行する同じ/外側 binder の変数
だけを参照できる。自由 OMV、shadowing、forward/self reference、複数 type annotation、`OMBVAR` 外の
OMATTR を reject する。

握手補題の canonical statement は次の AST であり、実 XML ではすべての private `OMS` に上記 exact
cdbase を付与する。

```text
forall G : FinSimpleGraph.
  relation1:eq(
    degree_sum(G),
    nat_mul(OMI(2), edge_count(G)))
```

`OMI(2)` は `nat_mul` の expected sort により `Nat` と判定する。`OMI(-2)`、`degree(G, OMI(2))`、
`degree_sum(G)` を `Vertex(G)` 位置へ入れることは reject する。

## 初期 Draft family と Lean alignment

以下だけを initial admission candidate とする。Lean column の `verified candidate` は、現行 pinned
mathlib source に定理があり、card を追加する時点で exact toolchain 上の witness と digest を固定すべき
ものを表す。`blocked` は statement を Draft に publish してはいけない。

| ID | canonical statement | Lean target / witness candidate | 状態 |
| --- | --- | --- | --- |
| GRAF-001 | `forall G. degree_sum(G) = 2 * edge_count(G)` | `SimpleGraph.sum_degrees_eq_twice_card_edges`、`[Fintype V] [DecidableRel G.Adj]` | verified candidate |
| GRAF-002 | `forall G. tree(G) -> nat_add(edge_count(G),1)=vertex_count(G)` | `SimpleGraph.IsTree.card_edgeFinset`、finite edge set の instance を明示 | verified candidate |
| GRAF-003 | `forall G. tree(G) -> connected(G)` | `SimpleGraph.IsTree.connected` | verified candidate |
| GRAF-004 | `forall G. tree(G) -> bipartite(G)` | `SimpleGraph.IsTree.isBipartite` | verified candidate |
| GRAF-005 | `forall G,t. is_euler_trail(G,t) -> (odd_degree_count(G)=0 or odd_degree_count(G)=2)` | `SimpleGraph.Walk.IsEulerian.card_odd_degree` | verified candidate |
| GRAF-006 | `has_euler_trail(G) <-> nonisolated_connected(G) and (odd_degree_count(G)=0 or ...=2)` | existence direction is not supplied by the pinned `Trails` module; it is marked TODO there | blocked |
| GRAF-007 | `bipartite(G) <-> exists L,R. proper_bipartition(G,L,R)` | `SimpleGraph.isBipartite_iff_exists_isBipartiteWith` is close but its `IsBipartiteWith` need not cover isolated vertices; add an exact bridge proof first | blocked |

The Lean bridge maps `FinSimpleGraph` to a `SimpleGraph V` together with finite vertex and edge instances;
`Vertex(G)` maps to `V`; `Trail(G)` maps to `SimpleGraph.Walk G u v`; and `is_euler_trail` maps to
`Walk.IsEulerian`. A manifest must record that mapping, the imports, exact theorem expression, witness SHA-256,
toolchain digest, and a human-reviewed statement/OpenMath/Lean alignment record. It must not claim that XML type
checking itself proves the Lean theorem.

For GRAF-005, the profile deliberately uses the **necessary** theorem first. The graph-side definition of
`has_euler_trail` is existential, but the witness card binds `t : Trail(G)` explicitly; this avoids asserting an
unproven constructive existence theorem through a bare boolean-like predicate.

## positive fixtures

Every positive fixture must include full typed XML, canonical XML, expected root `Prop`, registry digest, and the
matching manifest/Lean receipt. The validator-facing acceptance examples are:

| Fixture | required typed shape | acceptance |
| --- | --- | --- |
| `handshaking` | `G : FinSimpleGraph`; `eq(degree_sum(G), nat_mul(2,edge_count(G)))` | pass |
| `tree_edge_count` | `G : FinSimpleGraph`; `implies(tree(G), eq(nat_add(edge_count(G),1),vertex_count(G)))` | pass |
| `tree_connected` | `G : FinSimpleGraph`; `implies(tree(G),connected(G))` | pass |
| `tree_bipartite` | `G : FinSimpleGraph`; `implies(tree(G),bipartite(G))` | pass |
| `euler_odd_degree_necessity` | `G : FinSimpleGraph`, `t : Trail(G)`; `implies(is_euler_trail(G,t), or(eq(odd_degree_count(G),0),eq(...,2)))` | pass |
| `bipartition_well_typed` | `G : FinSimpleGraph`, `L,R : VertexClass(G)`; `proper_bipartition(G,L,R)` | pass as syntax only; no theorem card without bridge proof |

## hard-negative fixtures

| Case | expected rejection |
| --- | --- |
| `degree(H,v)` where `v : Vertex(G)` and `G`,`H` differ | dependent carrier mismatch at argument 2 |
| `adjacent(G,u,v)` where `v : Vertex(H)` | dependent carrier mismatch |
| `proper_bipartition(G,L,R)` with `L : VertexClass(H)` | graph-indexed class mismatch |
| `is_euler_trail(G,t)` with `t : Trail(H)` | graph-indexed trail mismatch |
| `degree(G,e)` for `e : Edge`/`Trail(G)` | expected `Vertex(G)` |
| `OMI -1` in any `Nat` context | negative natural literal |
| `graph1:graph` as a `FinSimpleGraph` value, or use with inherited cdbase | foreign untyped constructor / cdbase inheritance |
| plain `quant1:forall`, `fns1:lambda`, generic XML, or typed-math cdbase | profile confusion |
| no `pals_typed_graph:forall/exists`, missing/multiple/misplaced `type` OMATTR, free OMV | typed binder gate |
| Euler theorem using `connected(G)` in place of `nonisolated_connected(G)` | schema/card-family semantic lint reject; triangle plus isolated vertex is the regression counterexample |
| GRAF-006 or GRAF-007 with receipt `status=verified` but no bridge/existence witness digest | manifest admission reject |

Comparing `edge_count(G)` with `edge_count(H)` is **not** a type error: both are natural numbers and the comparison
is mathematically meaningful. The carrier check is instead enforced at operations whose inputs denote vertices,
vertex classes, or trails. A card requiring `G=H` semantically must state that condition explicitly; the validator
must not invent it.

## registry and manifest contract

The registry is at
`pals-agent/pals_agent/content_dictionaries/typed-finite-graph-v1-registry.json`; the sealed local manifest is
`docs/typed-finite-graph-v1-authoring-manifest.proposal.json`. This keeps implementation-specific validator material
in `pals-agent`, while the cross-repository evidence remains in `docs/`. No generic registry is mutated.

Each manifest requires at least:

```text
schema_version, openmath_profile, card_id, canonical_statement,
canonical_openmath_xml, expected_root_sort, registry_sha256,
cd_bundle_sha256, lean_target, lean_target_sha256, lean_witness,
lean_witness_sha256, lean_toolchain_digest, receipt_status,
alignment_review { statement_to_openmath, openmath_to_lean, reviewer, reviewed_at },
canonicalization { algorithm, version }, manifest_sha256
```

`manifest_sha256` is SHA-256 of RFC 8785 canonical JSON with only `manifest_sha256` omitted. All other digests are
over the exact UTF-8 bytes of their named canonical artifact. Admission requires `receipt_status=verified`, every
digest to match, and the GRAF family to be non-blocked. A proposal with `blocked` status may be stored as testdata but
cannot be placed in a DB, embedding index, candidate persistence, or release input.

## why generic is not enough

The generic profile can represent an untyped syntactic equality but cannot establish any of the following invariants:

1. `v` belongs to this graph's vertex carrier, rather than another graph's carrier.
2. A finite/simple/undirected graph model is being used, rather than a directed, labelled, mixed, or arbitrary-set
   `graph1` construction.
3. A supplied path/trail traverses edges of the same graph exactly once.
4. `degree_sum`, `edge_count`, and `odd_degree_count` have their stated finite-graph semantics.

Encoding all of this with generic `set1`, `list1`, `graph1`, `arith1`, and untyped `relation1:eq` would transfer
those obligations into English and Lean only, letting malformed OpenMath enter the Draft corpus. The sibling profile
keeps generic-v1 fully backward compatible while rejecting that malformed boundary data before it can be embedded or
persisted.

## implementation and admission gate

The local v1 implementation pins the exact registry JSON, strict direct-cdbase XML form, 64-depth/4,096-node limits,
typed binder/OMATTR rules, five positive fixtures, and hard negatives for dependent carrier mismatch, public
`graph1`, Euler existence converse, and full bipartition equivalence. Its generator revalidates every raw XML with
the isolated profile before sealing its canonical bytes; registry, design, strategy, sketch, signature trace, Lean
target/witness, and the RFC 8785 manifest digest are regression-bound.

Regression must run generic and existing typed-profile tests in addition to graph positive/hard-negative fixtures,
and compare pre-existing generic C14N bytes unchanged. This is still not authorization to add a DB table or publish
a graph Draft: admission additionally needs an independent project review and an explicit profile-aware catalog path.
