# 外部ライブラリ取り込みの試作: Mathlib の Archive／Counterexamples（2026-11-10）

Issue: [#327](https://github.com/AtsushiHosaka/pals/issues/327)。pals-agent の変更は [PR #102](https://github.com/AtsushiHosaka/pals-agent/pull/102)（`claude/library-manifest`、commit `62c11d72`、base は main `8a75810`）。

範囲は、プロジェクトが既に固定している Mathlib の一部である `Archive/` と `Counterexamples/` だけです。他のリポジトリは clone・取得・ビルド・実行していません。**カタログにカードは追加していません**（拡張の停止中。2026-11-04〜）。モデル呼び出しは0回、費用は0 USDです。

## 1. 仕組み: ライブラリを manifest で宣言する

- 1ライブラリ1ファイル: `pals_agent/lean_libraries/<名前>.toml`（schema `pals.lean-library-manifest.v1`）と型付きローダー `lean_library_manifest.py`。項目は、出典リポジトリ・commit・SPDXライセンス・帰属、Lean toolchain、workspace、pins、依存root、root別の信頼層、生成するプロファイル（import可能root・文の検査方式・有効化フラグ）、監査の公理許可リスト、ビルド手順の参照、索引のSHA-256です。
- 既存4プロファイル（`mathlib-4.32`、`stacks-4.35`、`stacks-frontier-4.35`、`stacks-frontier-defs-4.35`）は manifest から導出します。旧定数（`_PROFILES`、`_LIBRARY_ROOTS`）は削除しました。削除前に、旧コードの全フィールドと監査プログラムのSHA-256を固定値にし（`tests/fixtures/lean_profiles_golden.json`、pals-agent `8a75810` から生成）、導出値と一致することをテストにしました（`tests/unit/test_lean_library_manifest.py`）。既存のプロファイル・監査・ルーティングのテストは変更なしで通ります。
- 信頼語は汎用語に変えました: `kernel-checked-reviewed`／`kernel-checked-unreviewed`／`statement-only`。旧語 `core`／`frontier` は別名として読めます（`canonical_trust`、Stacks索引の検索も両方を受け付けます）。監査結果の水準（`mathlib`／`core`／`frontier_proof`／`frontier_statement`）は保存済みデータなので変えていません。
- manifest は監査の公理許可リストを**狭められるが広げられない**（`sorryAx` などを許す manifest は読み込みで拒否）。statement-only の層は import できません。manifest 1枚で新ライブラリのプロファイルが作れることを、テスト（`test_one_manifest_is_enough_to_add_a_library`）で示しました。
- 索引は `tools/library_index/build.py` が manifest から作ります（宣言名・種類・文・module・path・行・信頼層）。Stacksのタグ解析は任意プラグイン（`--plugin stacks-tags`）です。既存の `tools/stacks_index` は変更せず、検索の信頼語の比較だけ別名に対応させました。
- `lean.frontier_duplicate_definition` ほか3件の未分類コードを `quality_events` で処理しました。`lean.library_trust` と `lean.frontier_duplicate_definition` は検証成功に付く助言診断なので、失敗分類を持たない `LEAN_ADVISORY_CODES` に入れ、`lean.statement_uses_untrusted_library` は他の `lean.disallowed_*` と同じ `verifier.lean_compile_error` にしました。`tests/unit/test_quality_events.py::test_every_lean_diagnostic_code_in_the_package_is_classified` は、`origin/main`（`8a75810`）で `AssertionError: lean.frontier_duplicate_definition` と失敗し、変更後に通ります。分類表（taxonomy.md）の新しい行は足していません。

## 2. 棚卸し（実Lean、費用0）

### 条件

| 項目 | 値 |
|---|---|
| 対象 | Mathlib `8b62164d808cd0f23b7d8cc28190a6c1a1bb483a` の `Archive/`（84ファイル）と `Counterexamples/`（29ファイル）。合計113ファイル |
| Lean | `leanprover/lean4:v4.32.0-rc1`（既定プロファイル）。ビルド済みのメインcheckoutの `lean-workspace/.lake/packages` を**読み取りだけ**に使用 |
| cache | 共有workspaceのビルドに `Archive`・`Counterexamples` の `.olean` は**無かった**（0件）。そのため113ファイルをすべてコンパイル |
| 出力 | workspace外のscratchだけ（共有cacheは未変更）。調査後に削除 |
| オプション | Mathlib の lakefile が両ライブラリに与えるもの: `autoImplicit=false`、`pp.unicode.fun=true`、`maxSynthPendingDepth=3` |
| 実行 | Leanプロセスは常に1つ、import順、`nice -n 10`。他セッションが同時に Lean を動かしていた（`uptime` の load average は 14〜21）ため、時間は競合込みの値です |
| コマンド | `python -m tools.library_index.compile_inventory ...`、`axiom_report`、`inventory_report`（pals-agent `62c11d72`） |

### 結果

- **コンパイル: 113／113成功**。エラー0、`sorry` 警告0。
- **ビルド時間**: 合計267.1秒（1ファイル中央値2秒、p90 3秒、最大7.3秒 `Archive.Imo.Imo2024Q5`）。1ファイルの最大常駐メモリは3.29 GB（Mathlib の .olean を読み込む分を含む）。成果物（`.olean`）は合計60.6 MB。
- **件数（原文の字句解析、索引）**: 宣言1,440（theorem／lemma 1,121、def 236、abbrev 33、instance 22、structure 14、inductive 12、class 2）。宣言を1つ以上持つのは110ファイル。除外（数えて記録）: 匿名instance 77、example 56、private 33。
- **件数（Lean環境の実体）**: 113モジュールを import した環境にある theorem 定数は3,526、内部補助（`isInternalDetail`）を除いた1,378。差は、構造体・帰納型から自動生成された補題、等式補題（`.eq_N`）、private などで、字句の1,121とは一致しません。**どちらを「定理数」と呼ぶかは用途で決める**必要があります（自分で書かれた命題は前者）。
- **公理**（`Lean.collectAxioms`、1,378件）: 標準の3つ（`propext`、`Classical.choice`、`Quot.sound`）の部分集合のみ。**3つ以外の公理は0件、`sorryAx` は0件**。内訳: 3つ全部1,097、`propext` のみ108、なし108、`Quot.sound`＋`propext` 55、`Classical.choice`＋`propext` 6、`Quot.sound` のみ4。axiom 実行は29.1秒、最大常駐3.46 GB。
- **証明の長さ**（theorem 1,121件の、宣言行から次の宣言行までの空でない行数。次の宣言の docstring・コメントを含む上界）: 中央値6、平均10.4、p90 24、p99 62、最大129。
- **索引**: 1,440行、構築0.09秒、SQLite 774 KB、行データ（`decls.jsonl.gz`）54.5 KB。SHA-256 `64b4e3ed…`。manifest `mathlib-archive.toml` の `[index]` に記録し、行データを `lean-indexes/mathlib-archive/` にコミットしました（テストで一致を固定）。

### 分野別（ファイル数／字句のtheorem数）

| 区分 | ファイル | theorem |
|---|---|---|
| `Archive/Imo`（IMO。53ファイル） | 53 | 515 |
| `Archive/Wiedijk100Theorems`（100選） | 14 | 153 |
| `Archive/` 直下（Arithcc、Hairer、Kuratowski、MinimalSheffer、Sensitivity、ZagierTwoSquares） | 6 | 93 |
| `Archive/Examples` | 5 | 26 |
| `Archive/MiuLanguage` | 3 | 22 |
| `Archive/OxfordInvariants` | 1 | 1 |
| `Counterexamples` | 28（索引に宣言があるもの） | 311 |

`docs/100.yaml` は100項目、うち `decl` を持つのは78。その中で宣言が Archive の索引にあるのは**15**でした（残りは Mathlib 本体にあり、Archive ではありません）。`docs/1000.yaml` は1,199項目、`decl` を持つのは202、Archive の索引にあるのは**7**です。IMO の問題は53ファイル（1959〜2024）で、ファイル名と見出しが `IMO 年 Q番号` です。

### 文の素材としての性質

- 110ファイル中**69ファイル（theorem 991／1,121）が、自分のファイルの中に `def`／`structure`／`abbrev`／`inductive`／`class` を持ち**、その文はそれらを使います（例: IMO 1962 Q1 の `ProblemPredicate`、ballot problem の `countedSequence`）。定義を持たない41ファイルの theorem は130件だけです。IMO 53ファイルでは27が独自定義を持ちます。「Mathlib 定数のみ」の文は、全体のごく一部です（字句の近似であり、`variable` や notation 経由の依存は数えていません）。
- 索引の `statement` は署名の原文です。`variable` で束縛された前提や `open` は含まれず（`context` 列に別に保存）、文だけを切り出して単独でコンパイルできるとは限りません。

### 文の標本10件（無作為。シード327。IMOは `imoYYYY_qN` 形式の名前、100選は yaml の `decl`、反例は各ファイル1件から）

| # | 自然言語の題 | 宣言（path:行） | 文（署名の原文、先頭240字まで） |
|---|---|---|---|
| 1 | IMO 1962 Q1 | `imo1962_q1`（Archive/Imo/Imo1962Q1.lean:127） | `IsLeast {n \| ProblemPredicate n} 153846` |
| 2 | IMO 2019 Q2 | `imo2019_q2`（Imo2019Q2.lean:581） | `[Fact (finrank ℝ V = 2)] (A B C A₁ B₁ P Q P₁ Q₁ : Pt) (affine_independent_ABC : AffineIndependent ℝ ![A, B, C]) …`（長いため省略） |
| 3 | IMO 2006 Q5 | `imo2006_q5`（Imo2006Q5.lean:190） | `{P : Polynomial ℤ} (hP : 1 < P.natDegree) {k : ℕ} (hk : 0 < k) : (P.comp^[k] X - X).roots.toFinset.card ≤ P.natDegree` |
| 4 | IMO 1975 Q1 | `imo1975_q1`（Imo1975Q1.lean:30） | `(hσ : {x \| σ x ≠ x} ⊆ Finset.Icc 1 n) (hx : AntitoneOn x …) (hy : AntitoneOn y …) : ∑ i ∈ Finset.Icc 1 n, (x i - y i) ^ 2 ≤ ∑ i ∈ Finset.Icc 1 n, (x i - y (σ i)) ^ 2` |
| 5 | Erdős–Szekeres の定理（100選） | `Theorems100.erdos_szekeres`（Wiedijk100Theorems/AscendingDescendingSequences.lean:139） | `{r s : ℕ} {f : α → β} (hn : r * s < Fintype.card α) (hf : Injective f) : (∃ t : Finset α, r < #t ∧ StrictMonoOn f t) ∨ ∃ t : Finset α, s < #t ∧ StrictAntiOn f t` |
| 6 | The Ballot Problem（100選） | `Ballot.ballot_problem`（BallotProblem.lean:345） | `: ∀ q p, q < p → uniformOn (countedSequence p q) staysPositive = (p - q) / (p + q)` |
| 7 | 三角数の逆数の和（100選） | `Theorems100.inverse_triangle_sum`（InverseTriangleSum.lean:29） | `(n : ℕ) : ∑ k ∈ range n, (2 : ℚ) / (k * (k + 1)) = if n = 0 then 0 else 2 - (2 : ℚ) / n` |
| 8 | 半ノルムの束は分配的でない | `Counterexample.SeminormNotDistrib.not_distrib`（Counterexamples/SeminormLatticeNotDistrib.lean:47） | `: ¬(p ⊔ q1) ⊓ (p ⊔ q2) ≤ p ⊔ q1 ⊓ q2` |
| 9 | 半環上の相補分解が直和にならない例 | `Counterexample.withSign.not_internal`（DirectSumIsInternal.lean:91） | `: ¬DirectSum.IsInternal withSign` |
| 10 | `algebraMap R (CliffordAlgebra Q)` が単射とは限らない | `LinearMap.BilinMap.not_forall_toQuadraticMap_surjective`（CliffordAlgebraNotInjective.lean:290） | `¬∀ (R : Type) (M : Type v) [CommRing R] [AddCommGroup M] [Module R M], Function.Surjective (BilinMap.toQuadraticMap : …)`（原文にコメント `TODO` が混入） |

標本でも、#1・#6・#8・#9 のようにファイル内の定義や `variable` に依存して、署名だけでは意味が決まらないものがあります。10件すべて、公理は標準の3つでした。

### この節で測っていないこと

- 標準プロファイルの**検証器の経路**（ソース方針・trusted audit・kernel replay）での再検証。今回は `lean` を直接使い、Mathlib 自身の lakefile のオプションでコンパイルしました。
- 自然言語の質問との対応の正しさ（文が元の問題を忠実に表すか）。IMO の題の対応は見出しからで、文の忠実性は未確認です。
- 文だけをファイルから切り出して既定プロファイルで単独コンパイルできる割合。
- 他ライブラリ（Compfiles ほか）。取得もビルドもしていません。

## 3. 設計メモ（未実装）

### (a) 質問に対するライブラリ／プロファイルの選択

選択は呼び出し側（worker）が行い、検証器は要求本文からプロファイルを受け取らない（既存の不変条件）。

- **要求時に使える信号**: ①型付きプロファイルの選択結果（`ProfileRoutedProofFlowRuntime` が既に返す `profile_id`。30の型付きプロファイル、`generic-v1`、`null`）。②OpenMath の構造化結果（使われる記号・CD）。③カタログ／評価集合の分野タグ（`generation-eval-v1` の `field` 15種）。④質問本文の出典語（「IMO 1988」「Putnam」「Stacks tag」など）。
- **安価で決定的な最初の規則**: manifest に `[[selectors]]`（分野タグ・記号・出典語の完全一致表）を持たせる。1つのライブラリだけに一致したときだけ、そのライブラリの非既定プロファイルを選ぶ。一致なし・複数一致・フラグが閉じている・対応する検証器が配備されていない、のいずれでも**既定プロファイル**にする。
- **安全な退避**: 退避先は常に `mathlib-4.32`。ただし、文がそのライブラリの定義に依存する場合（スキーム論など）は既定へ退避しても `unknown identifier` で失敗するだけなので、退避ではなく「該当ライブラリなし」と答える。選択理由は閉じた語彙の1コード（`library_selection.*`）で品質イベントに残す。質問本文は残さない。
- **測定**: 規則の適合率は、既存の分野タグ付き100題と、固定の「他分野」題で、モデルなしに先に測れる。

### (b) 前提（premise）の検索: 実在する補題名を Sketch／Prove に渡す

- **供給元**: 索引の行（名前・種類・文・module・信頼層）。既定は信頼層が reviewed の行だけ。unreviewed の行は層名を付けて明示する。
- **検索**: Sketch の `formal_statement` から定数を取り（既存の `tools/stacks_index/shape.query_shape`）、定数の重なり（`symbol_search`）と FTS の文面検索を、既存の `reciprocal_rank_fusion` で融合する。
- **上限**: 上位 k=8 件、各文は300字で切る、全体3 KB（約1,000 token）。プロンプトには「次の宣言は実在する。名前は一字も変えずに使え。ここにない名前を作るな」と書く。
- **索引は字句であること**: 名前は `open` を解決していない。検索結果の名前が実際に解決するかは、コンパイルで決まる。
- **測定（幻覚した識別子への効果）**: 
  1. **費用0の事前測定**: 過去の記録にある `unknown identifier`／`unknown constant` の失敗について、正しい名前が検索の上位 k に入るか（recall@k）を、索引だけで測る。
  2. **実モデル**: `generation-eval-v1` の tuning 70題、base と retrieval の2群、各2回。指標は、初回コンパイルの `lean.unknown_identifier`／`unknown constant` の件数（100試行あたり）、初回成功、最終成功、修復回数、入力token増、費用。held-out 30題は最後の1回だけ。費用の上限は都度確認（小さな回帰セット）。
  3. 幻覚の判定は、生成した証明の非局所の識別子が、索引とMathlibの索引のどちらにも無いことで機械的に行う。

### (c) 容量方針

- 1つの toolchain＝別の Mathlib のコピー（この checkout の Mathlib ビルドだけで約6.3 GB）。16 GiB の検証器ホストではページキャッシュが共有できず、2つ目の Mathlib は実質的に1つ目のキャッシュを追い出す。**同じ Lean と同じ Mathlib commit のライブラリは、既定の検証器に同居できるが、`lake-manifest` が変わると既定プロファイルの指紋（`lake_manifest_sha256`）が変わり、既存の Recipe がすべて不一致になる。** そのため、同居は「別プロファイルの別 workspace が、同じ読み取り専用の Mathlib ビルドを共有して参照する」形に限られ、共有されるかどうか（同じファイルを同じホストパスから読むか）は**実測するまで仮定しない**。
- 調査（`lean-formalization-sources-2026-11-08.md`）の分類:
  - **A: 同じ版（Lean `v4.32.0-rc1`＋同じ Mathlib）**。Mathlib Archive／Counterexamples（今回、同梱）。`v4.32.0-rc1` のタグを持つ teorth/pfr、leanprover/cslib、infinity-cosmos（Mathlib commit 360da6fa が一致するか、cslib のみ調査に記載。他は未確認）。追加の Mathlib のコピーは要らない。
  - **B: 文の素材だけを使う（ライブラリを import しない）**。文が Mathlib 定数のみで、既定プロファイルで再コンパイルできるもの: Compfiles、PutnamBench、formal-conjectures（約600ファイル）、ProofNet、miniF2F。取得・変換のみで追加の toolchain は不要。ただし Mathlib の版の差（Compfiles は HEAD が 4.35、タグ `lean-v4.32.0` あり）で、名前が変わった文は落ちる。
  - **C: 別 toolchain が必要**。Mathematics in Lean（v4.34.0）、formalising-mathematics-notes（v4.32.0 で rc1 と異なる Mathlib）、flt-regular（v4.36.0-rc2）、Stacks（v4.35.0、既に定義だけある）、brownian-motion／carleson（v4.32.0）。別 verifier の別ルーティング、およびホスト容量の明示的な決定が必要（容量の決定は所有者）。
  - **D: 使わない**。公理で穴があるもの（ImperialCollegeLondon/FLT、cam-combi）、ライセンスなし、ML利用を禁じる（atlas-lean）、独自の基礎を使う（equational_theories、teorth/analysis ほか）。

### (d) 次に取り込む3件（順序と理由）

Archive は今回の試作で済み。

1. **Compfiles**（`dwrensha/compfiles`、Apache-2.0）。理由: 競技問題521ファイル、sorry 6ファイルのみ、axiom 0、文はほぼ Mathlib のみ。B の経路で追加 toolchain が要らない。**所有者の承認が要るもの**: 第三者リポジトリの clone（読み取り用の浅い clone）。ビルドはしない前提で、文の抽出だけ。問題原文の権利の確認（調査では未確認）。ライセンス（Apache-2.0）の確認。
2. **Mathematics in Lean＋formalising-mathematics-notes**（Apache-2.0／MIT とヘッダ Apache-2.0）。理由: 学部標準の分野（論理〜測度、群・環・ガロア）、解答付きで、利用者の質問に近い。**承認が要るもの**: clone。LICENSE（MIT）とファイルヘッダ（Apache-2.0）の食い違いの扱い（作者に確認するか）。本文（`doc/`）のライセンス。MIL は v4.34.0 のため、ライブラリとして使うなら C（別 toolchain）、文の素材だけなら B。所有者がどちらにするか。
3. **leanprover/cslib**（Apache-2.0、タグ `v4.32.0-rc1` あり）。理由: 計算可能性・オートマトン・λ計算など、これまで分野に無い領域で、A と同じ版なので追加の Mathlib が要らず、sorry 0・axiom 0。**承認が要るもの**: 第三者コードの clone と `lake build`（lakefile は任意コードを実行しうるため、ビルドは隔離環境で行い、所有者が許可する）。独自定義（LTS、DA／NA など）が文に含まれるため、プロファイルとして import できる形での配備になる点。固定する commit。

承認されるまで、上の3件は clone・ビルド・実行していません。

## 4. 検証

- pals-agent: 追加・既存のプロファイル／索引／品質イベントのテストを実行（結果は PR 本文）。
- 失敗の比較: 統合テスト（`tests/integration`、実 Lean を使う）は、この環境では `lean.trusted_audit_failed` などで失敗しました（**私が誤って全体実行に含めてしまい、短時間の Lean が数回起動しました。以後は除外**）。ユニットテストの全体は PR 本文に記載します。

## 5. 未実施のもの

- 検証器の実経路での Archive 再検証、文の切り出しコンパイル、忠実性の評価。
- (b) の recall@k とモデルありの測定。(a) の規則の適合率。
- 他ライブラリの取り込み。同居時のページキャッシュ共有の実測。
