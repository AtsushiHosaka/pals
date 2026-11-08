# Lean形式化の公開リポジトリ調査（Stacks以外）2026-11-08

目的: 分野別にLean 4で形式化された公開リポジトリを、PALSへ取り込む候補として取り込みやすい順に並べる。調査のみで、実装・ビルドはしていない。

## 結論

- **推奨の上位3件**: ①Mathlib Archive／100 theorems／1000+（タグ `v4.32.0-rc1` がPALSと同一）、②Mathematics in Lean と formalising-mathematics-notes（学部教材、解答付き）、③Compfiles（文と証明が揃う）。
- **次点**: formal-conjectures（文の量は最大。ファイル単位の選別と出典別ライセンスの判定が要る）。
- 公理で穴が開くもの（FLT、cam-combi）、ライセンス無しのもの、ML利用を禁じるもの（atlas-lean）は取り込まない。
- **どのリポジトリもコンパイル済み成果物（olean等）を配布していない**。取り込むなら各自でビルドし直す。ビルド可否は今回すべて未検証。

## 調べ方と限界

- `gh api`、raw取得、`--depth 1` の浅いclone（スクラッチのみ、調査後に削除。`~/.cache/mathlib` は未接触）。LICENSE本文は各repoで実読した。
- 規模・sorry数は grep による概算。sorryは各repoのHEAD基準で、v4.32系タグ時点の数ではない。
- 「Mathlib定数のみ」は、数件の実ファイルを読んだ範囲の判断。全件は確認していない。
- Mathlibのタグ `v4.32.0-rc1`（360da6fa）は実在し、正式版 `v4.32.0` とは598コミット差。多くのrepoは `v4.32.0-rc1` タグを持たず、HEADは v4.33〜4.36。

## 1. 文の素材として使える（Mathlib定数のみ）

取り込みやすい順。

| 順 | 対象 | 分野・水準 | 規模 | ライセンス | 版（PALS=v4.32.0-rc1） | 注意 |
|---|---|---|---|---|---|---|
| 1 | Mathlib Archive／docs/100.yaml／1000.yaml | 競技（IMO 53問）、定理100選、1000+定理 | Archive 84ファイル。100選は78件、1000+は1199件中203件に宣言あり | Apache-2.0（Mathlibと同じ） | タグ `v4.32.0-rc1` が一致 | Archiveは独自補題を持つが証明済み。MathlibのcacheにArchiveのoleanが入るかは未確認 |
| 2 | leanprover-community/mathematics_in_lean | 学部標準（論理〜測度） | `MIL/` 87ファイル約1.1万行。解答43ファイル | Apache-2.0 | v4.34.0（+2） | C07/C08に教材用の独自structure。本文の別ライセンスは確認できず |
| 3 | b-mehta/formalising-mathematics-notes | 学部〜院（論理〜ガロア理論）22節 | 159ファイル約1.7万行。解答66ファイル | LICENSEはMIT、各ファイルのヘッダはApache-2.0（矛盾） | v4.32.0（rc1の次） | 矛盾の整理が要る。文章部分（`doc/`）のライセンスは未確認 |
| 4 | dwrensha/compfiles | 競技（IMO 274、USA 217ほか） | 521ファイル、theorem/lemma 5,876 | Apache-2.0 | HEAD v4.35.0。タグ `lean-v4.32.0` あり | sorryは6ファイルのみ、axiomは0。独自コマンド `problem`／`determine` は中身がMathlibの文。問題原文の権利は未確認 |
| 5 | trishullab/PutnamBench（`lean4/`） | Putnam 1962–2025、学部の解析・代数・線形代数 | Lean 672問、全て文のみ | `lean4/` はApache-2.0。ルートにLICENSE無し。非形式文はMAAの許可つき公開 | v4.33.1。README上、4.32ではソース変更なし（未検証） | 約350問は答え用の `abbrev …_solution := sorry` を含む。問題原文の再配布権はMAAに確認が必要 |
| 6 | google-deepmind/formal-conjectures | 未解決問題・予想（Erdős 1,011、OEIS 348、Wikipedia 184ほか）。`textbook` 249件 | `FormalConjectures/` 1,832ファイル、約18.5万行 | コードApache-2.0、素材CC-BY 4.0。Wikipedia／MathOverflow／OEIS由来はCC BY-SA 4.0。arXiv由来は論文ごと | v4.33.1。タグ `v4.32.0` あり | **1,832ファイル中1,235に独自のdef/abbrev/structureがある**。Mathlib定数のみの文は約600ファイルに絞る必要がある。sorryは約5,100行（意図的）、axiomは0。誤定式化の報告issueが254件（open 19） |
| 7 | ProofNet（Lean 4版） | 学部教科書（Rudin、Munkres、Herstein、Axlerなど）371問 | DeepSeek-Prover-V1.5 の `datasets/proofnet.jsonl` | MIT（データ）。教科書の問題文の権利は未確認 | 版固定なし | 偽になる誤定式化が2件報告済み（Artin 13_4_10、Ireland–Rosen 5_13）。zhangir版はLean 3なので不可 |
| 8 | math-inc/FormalQualBench | 博士資格試験レベル23問 | 25ファイル約470行 | Apache-2.0 | v4.28.0（−4） | 個別の文のMathlib度は未確認 |
| 9 | teorth/pfr の `PFRPalomar/Challenge.lean` | 加法的組合せ論（PFR） | 6定理 | Apache-2.0 | タグ `v4.32.0-rc1` あり | 「Mathlibのみ」と冒頭に明記。内容は研究寄りで利用者の質問には稀 |
| 10 | miniF2F（Lean 4版、yangky11） | 高校〜AIME | 488問 | MIT | v4.24.0（−8） | 公式の訂正版が複数あり、誤定式化の報告が多い。学部向けは少ない |

## 2. 証明側の補題として使える（kernel検査）

証明済み（sorryとaxiomが0）で、依存がMathlibのみのもの。文が独自定義を含むため、文の素材には使えない。取り込むには、PALSの検証器が外部packageをimportできる必要がある（この点は本調査の範囲外で未確認）。取り込み前に、使う補題ごとに `#print axioms` を確認する。

| 順 | 対象 | 内容 | 規模 | ライセンス | 版 | 注意 |
|---|---|---|---|---|---|---|
| 1 | Mathlib Archive／Compfiles／MIL・formalising-mathematics-notes の解答 | §1と同じ | §1参照 | §1参照 | §1参照 | Compfilesのsorry6ファイルは除く。MILの解答側sorryは5行、formalising-mathematics-notesの解答側は7行 |
| 2 | formal-conjectures の `ForMathlib` | 汎用補題 | 約1,310宣言、sorry 0 | Apache-2.0 | v4.33.1 | 同じrepoの文側と同時に取り込む形になる |
| 3 | leanprover/cslib | 計算可能性、オートマトン、λ計算、CCS、回路 | 341ファイル約5.2万行、sorry 0、axiom 0 | Apache-2.0 | タグ `v4.32.0-rc1` あり（mathlib 360da6fa）。毎日更新 | 文は独自定義（LTS、DA/NA、URMなど）が中程度。計算可能性の質問には直接役立つ |
| 4 | leanprover-community/flt-regular | 正則素数でのFLT | 25ファイル約3.7k行、sorry 0 | Apache-2.0 | v4.36.0-rc2（+4） | Mathlibへの移行が進行中。移行済み分はMathlibに既にある |
| 5 | emilyriehl/infinity-cosmos | ∞-コスモス | 32ファイル約4.7k行、sorry 0 | Apache-2.0 | タグ `v4.32.0-rc1` あり | blueprint段階で網羅度は小さい。文は独自クラス中心 |
| 6 | vihdzp/combinatorial-games | 超現実数、ニム | 69ファイル約2.4万行、sorry 0 | Apache-2.0 | v4.36.0-rc2。4.32時点のタグ無し | Mathlibの `SetTheory.PGame` との関係は未確認 |
| 7 | math-inc/Sphere-Packing-Lean | 球充填（次元8、24） | 830ファイル約18万行、sorry 0、axiom 0 | Apache-2.0 | v4.28.0（−4） | AI（Gauss）による自動形式化。移植コストが大きく、利用者の質問からも遠い |
| 8 | teorth/pfr 本体 | PFR予想 | 76ファイル約2.2万行、本体は完成 | Apache-2.0 | タグ `v4.32.0-rc1` あり | 追加依存 AddCombi。エントロピー等の独自定義が中心 |
| 9 | RemyDegenne/brownian-motion、fpvandoorn/carleson、FormalizedFormalLogic/Foundation、sphere-eversion | 確率過程、調和解析、論理学（不完全性定理）、微分位相 | それぞれ sorry 21／24／6／10 | Apache-2.0 | タグ v4.32.0（brownian、carleson）。他はタグ無し | 完成部分だけを選別する必要がある。Foundationは独自の論理体系でMathlibの `FirstOrder` と接続しない |

## 3. 使えない（理由つき）

| 対象 | 理由 |
|---|---|
| ImperialCollegeLondon/FLT | axiom `knownin1980s {P : Prop} : P` を含み、任意の命題が通る。ほかにaxiomが2件、sorryが65行。未完成 |
| YaelDillies/cam-combi | `axiom proved_later {P : Prop} : P` を含み、6箇所で使用。sorryも29行 |
| facebookresearch/atlas-lean | ルートのLICENSEが「ML開発（訓練・評価ほか）に使わない」旨を述べる。v1はCC BY-NC 4.0にno-training条項つき |
| LICENSEの無いrepo: math-inc/strongpnt、math-inc/RiemannHypothesisCurves、math-inc/KakeyaFiniteFields、b-mehta/ExponentialRamsey、rkirov/linear-algebra-done-right-lean、derekblair/rudin-lean、hrmacbeth/math2001 | 再利用の許諾が不明。作者に確認すれば候補に戻る（Axler、Rudinは文がMathlibのみで有望。ただし後者は独自の `pma*` ラッパーあり） |
| teorth/equational_theories | 独自の `class Magma` で記述し、Mathlibの型ではない。v4.29.1。repoは447MB |
| teorth/analysis（Tao『Analysis I』） | 2〜8章は独自定義（`Chapter2.Nat`、`Chapter5.Real`など）でMathlibの定数ではない。9章以降はMathlibとの混在。演習は意図的にsorry。v4.29.0-rc8 |
| AlexKontorovich/PrimeNumberTheoremAnd、teorth/IEANTN | sorryが262行と233行。進行中でaxiomも4件（IEANTN）。補題を個別に選べば部分利用の余地はある |
| thefundamentaltheor3m/Sphere-Packing-Lean | 未完成（sorry 64行、axiom 2件）。完成版は math-inc 側 |
| lecopivo/SciLean | sorry 805行、axiom 37件、native_decide 44件 |
| leanprover-community/NNG4、leanprover/theorem_proving_in_lean4 | 独自の `MyNat` を使う、またはMathlibを使わない |
| optsuite/optlib（v4.13）、Ivan-Sergeyev/seymour（v4.18）、hrmacbeth/math2001（v4.3）、Lean Workbook（v4.8）、NuminaMath-LEAN（v4.15）、Herald（v4.11） | 版が古く、移植量が大きい。Heraldの実体はMathlib宣言への注釈 |
| CombiBench、FormalMATH | CombiBenchは独自定義が多く、誤定式化の報告も多い（issue 10件）。FormalMATHは688問に独自defがあり、Lean／Mathlibの版が未確認 |
| Mathlib本体にあるもの（Fermatの最終定理のn=3, 4） | 取り込み不要（`fermatLastTheoremThree`、`fermatLastTheoremFour`） |

## 4. Blueprint系

- 仕組み: `\lean{宣言名}` で自然言語の文とLean宣言を結び、`\leanok` で形式化済みを示し、`\uses{}` で依存を書く。新方式 LeanArchitect は、文をLean側の `@[blueprint (statement := …)]` に書く。
- 実測した3件はいずれもApache-2.0。PFR（約213組）、Carleson（179組）、PrimeNumberTheoremAnd（約960組、LeanArchitect形式で最も機械処理しやすい）。
- 評価: 文が章冒頭の前提と独自マクロに依存し、単独では成立しない。対象が研究レベルで、学部〜院の質問の分野・粒度と合わない。toolchainもPALSより+3〜+4新しい。「問い→文」の対応データとしては優先度が低い。

## 5. Stacks・Kerodon（別セッション担当、事実のみ）

- AxiomMath/Stacks: Apache-2.0、`.lean` 49,745ファイル、v4.35.0、StacksCore／StacksFrontierの2層。
- optpku/stacks: Apache-2.0、`.lean` 47,466ファイル、v4.32.0。
- Kerodon: Lean版は見つからなかった（`leanprover-community/external-tags` はタグ検査の道具）。

## 6. 未確認・ユーザー確認が必要な点

- **Infinite-Sums**: 検索でも該当repoが見つからない。何を指すか確認したい。
- **qinz1yang/differential-geometry**: `.lean` が28,771ファイル、約395MBと異常に大きい。未cloneで内容未確認。取得してよいかの確認が要る。
- **問題原文の権利**: PutnamBench（MAA）、miniF2F、ProofNet、Compfiles、FormalMATHの再配布条件は未確認。
- **formal-conjectures**: CC BY-SA 4.0由来のファイルを含めてよいかの方針が要る。
- **formalising-mathematics-notes**: LICENSE（MIT）とファイルヘッダ（Apache-2.0）の食い違いを、作者に確認するか。
- **Mathlibのcache**: Archiveのoleanが含まれるか未確認。
- 未確認の文の独自度: flt-regular、brownian-motion、PrimeNumberTheoremAnd、IEANTN、GlimpseOfLean、LeanCourse26、LFTCM2026。
- 集合論の強制法、Euclid公理系、Turing機械単体、大偏差のLean 4 repoは、検索では見つからなかった（検索は上位のみで網羅ではない。`gh search` は一度rate limitに当たった）。
- 全件で、v4.32.0-rc1でのコンパイル可否と、文の移植時の名前衝突は未検証。HEADがv4.33以降のrepoは、文が通るかを実機で確認する必要がある。

## 7. 次の一手（提案）

1. ①Archive、②MIL＋formalising-mathematics-notes、③Compfiles から、文のうち独自定数を含まないものだけを抽出する小さな試作を行う。抽出は `#print axioms` と、v4.32.0-rc1での実コンパイルを条件にする。
2. 上記の権利確認（MAA、formalising-mathematics-notesのライセンス）を並行して進める。
3. formal-conjecturesは、Mathlib定数のみの文（約600ファイル）の選別基準を決めてから着手する。
