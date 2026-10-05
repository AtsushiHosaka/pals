# 本番数学カタログ追加 — 2026-10-05

## 実行結果

本番DBの既存Lean Recipeは **0→923件**。923件すべてについて、登録直後に対象命題・証明本文・materialized source・toolchain・receipt・admission event を読み戻して既存の厳密一致検査に通した。コミット後の新しいread-only接続でも923件の全bundleを再照合した。既存自然文Draftは **433→433件**、sealed releaseとの厳密一致を登録前後に確認した。APIの `/health` は `status=ok`、`environment=prod`。

新しいtyped Draft **652件・21 profile** はローカル準備済み。本番typed行は現在0件、active profileも0件。embedding生成の外部送信が自動承認レビューに拒否され、明示許可の回答を待っている。承認リストに記載された既存の継続許可を再提示したが、審査はファイルの許可記録を直接のユーザー許可として認めなかった。未送信のDraftを「本番追加済み」や「公開済み」とは数えない。

| Recipeの主な範囲 | 本番追加件数 |
| --- | ---: |
| 学校数学・数論・論理・離散数学ほか | 324 |
| 線形代数 | 178 |
| 解析・微積分 | 194 |
| 多変数・ベクトル解析 | 51 |
| 可換環論・加群・整拡大・次元 | 176 |
| 合計 | 923 |

このうち新たに著作した学校算術は35件。大学後半の候補にはHilbert基底定理、Artinian/Noetherian環、整拡大のlying over/going up/going down、素スペクトル、Krull次元などを含む。既存の著作済み候補を実コンパイルして本番へ移したものも含み、923件を新規のカリキュラムセルや数学的に独立な問題パターンの数とはみなさない。

候補929件の一次検査から6件を除外した。内訳は、必要なnamespace/notationが欠けた極限1件・確率4件と、gcd補題の引数順が誤っていた学校算術1件。失敗したものを修正済み・検証済みとは記録せず、本番へ追加していない。対象が完全に閉じた単独のtactic exampleとして取り出せない等の168件も、コンパイル前に対象から除外した。

最終の923件だけを通常Lean CLIで再コンパイルし、終了コード0・拒否0件・公理監査923件を得た。誤命題拒否の制御検査も成功。証明hashの改変、誤命題の制御結果の成功偽装、`sorryAx`への公理改変、失敗証明の昇格を拒否する4種類の検査もすべて成功した。

## 検証と公開の区別

追加対象は既存の著作済み候補と、新たに独自に著作した学校算術の候補。各命題の全変数・仮定を保持して閉じた Lean 命題へ変換する。全候補を匿名 `example` として先にコンパイルし、その後に同一証明の名前付きコピーを置いて `#print axioms` を確認する。匿名例には、後続の監査用宣言を利用できる順序上の依存がない。

誤命題 `1 + 1 = 3` が通常の Lean コンパイラに拒否されることを制御検査とする。失敗した候補を除き、残りだけを別のファイルで再コンパイルし、終了コード0と全公理監査の一致を要求する。許可する基礎公理は `propext`、`Classical.choice`、`Quot.sound` のみ。`sorryAx`、追加公理、`native_decide` は受け入れない。個別ファイルごとのコンパイラ実行とは記録せず、実際のバッチ検証として証拠を保存する。

Lean Recipe は既存の admission bundle 形式で登録する。Draft は正規化した OpenMath・既存モデルの実embeddingとともに、署名なし・独立レビュー待ち・inactive の世代として保存する。自然文・OpenMath・Lean の意味対応の独立承認、検索品質評価、公開用署名はこの実行では捏造しない。世代の `review.authoring_witnesses` に Draft ID から検証済み Recipe への参照を保存するが、これは承認済みの runtime alignment を意味しない。

DB構成のDDL変更は行わない。既存433件の自然文カタログは immutable なリリース成果物であり、直接追記するとその整合性検査を破るため、別途存在する Lean Recipe / typed Draft テーブルを使う。登録前後に既存カタログの厳密一致を検査する。

## 調査資料

以下は命題の範囲・概念・形式化方法を調べた一次資料。一般の数学的事実を独自に記述し、教材の文章や演習解答を転載していない。今回の Lean の正しさの証拠は、固定された実コンパイラの結果である。資料を発見したことだけでは、当該分野を網羅したとは数えない。

| 範囲 | 一次資料 |
| --- | --- |
| 算術・小中の式変形 | [OpenStax Prealgebra](https://openstax.org/books/prealgebra-2e/pages/1-introduction)、[Elementary Algebra: special products](https://openstax.org/books/elementary-algebra-2e/pages/7-4-factor-special-products) — 概念・範囲の参照のみ、教材本文は取込対象から除外 |
| Lean と証明の基本 | [Lean community documentation](https://leanprover-community.github.io/documentation.html)、[mathlib overview](https://leanprover-community.github.io/mathlib-overview)、[Mathematics in Lean: Basics](https://leanprover-community.github.io/mathematics_in_lean/C02_Basics.html) |
| 整除・gcd・lcm | [Mathematics in Lean: Elementary Number Theory](https://leanprover-community.github.io/mathematics_in_lean/C05_Elementary_Number_Theory.html) |
| 離散数学・有限集合 | [Mathematics in Lean: Discrete Mathematics](https://leanprover-community.github.io/mathematics_in_lean/C06_Discrete_Mathematics.html) |
| 群・環・代数 | [Mathematics in Lean: Groups and Rings](https://leanprover-community.github.io/mathematics_in_lean/C09_Groups_and_Rings.html)、[Milne: Group Theory](https://www.jmilne.org/math/CourseNotes/gt.html)、[Milne: Fields and Galois Theory](https://www.jmilne.org/math/CourseNotes/ft.html) |
| 線形代数 | [Mathematics in Lean: Linear Algebra](https://leanprover-community.github.io/mathematics_in_lean/C10_Linear_Algebra.html) |
| 位相 | [Mathematics in Lean: Topology](https://leanprover-community.github.io/mathematics_in_lean/C11_Topology.html)、[MIT 18.901 lecture notes](https://ocw.mit.edu/courses/18-901-introduction-to-topology-fall-2004/pages/lecture-notes/) |
| 実解析 | [MIT 18.100A Real Analysis](https://ocw.mit.edu/courses/18-100a-real-analysis-fall-2020/)、[MIT 18.102 Functional Analysis](https://ocw.mit.edu/courses/18-102-introduction-to-functional-analysis-spring-2021/) |
| 微分・積分・測度 | [Mathematics in Lean: Differential Calculus](https://leanprover-community.github.io/mathematics_in_lean/C12_Differential_Calculus.html)、[Integration and Measure Theory](https://leanprover-community.github.io/mathematics_in_lean/C13_Integration_and_Measure_Theory.html) |
| 可換環論・整拡大・次元 | [Milne: A Primer of Commutative Algebra](https://www.jmilne.org/math/xnotes/ca.html)、[Stacks Project](https://stacks.math.columbia.edu/)、[Milne: Algebraic Number Theory](https://www.jmilne.org/math/CourseNotes/ant.html) |
| 代数の追加資料 | [MIT Algebra I student notes](https://ocw.mit.edu/courses/res-18-011-algebra-i-student-notes-fall-2021/) — サイト自身が教員による正確性確認をしていないと明記しており、証明の正しさの根拠にはしない |

## 実行成果物

`output/verified-math-20261005/` はGit管理対象外。候補、除外理由、正規化された対象、実コンパイラ入力・出力・receipt、公理、embedding、DB読戻しreceiptを保持する。秘密情報やDBダンプをコミットしない。

## 固定された検証環境とhash

- Lean: `leanprover/lean4:v4.32.0-rc1`
- Mathlib commit: `8b62164d808cd0f23b7d8cc28190a6c1a1bb483a`
- バッチCLI: `lake env lean --threads=1 /evidence/accepted-batch.lean`
- 最終バッチ時間: 307865 ms
- 最終Lean source SHA-256: `2c9bfcecff2a3610e69e1c509819820ff3f4dda258b1928d77bddbad328fa78f`
- compiled inventory SHA-256: `8a2fca10e1aaa9938c10b7b96f90be4459921a5c6bf532cdfa6ec1f6fc34ce80`
- 公理内訳: 基礎公理なし15件、`propext`のみ39件、`propext`と`Quot.sound`の87件、許可した3公理の782件。

実行したコンパイラhelperのbytesも証拠directoryに固定する。初回helperにはreceiptのファイル名を監査用定理名で上書きする変数名の不具合があったため、実際のreceipt内容を変えずに探索用・最終用の名前へコピーし、今後のhelperでは変数名を修正した。コンパイラ入力・出力・終了コード・各hash・実行されたhelperのfingerprintを再照合してからDBへ登録した。
