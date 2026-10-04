# 一般定理Draftの拡充 v4 — 2026-09-30

[v3](math-expansion-v3-20260930.md)の466件に、新たな一般定理101件を追加した。型付きローカルDraftは**567件・embedding 567件・25 profile・29 manifest**になった。今回の101件も自然文、canonical OpenMath、Lean命題、証明手順を対応づけ、全Lean証明をコンパイルした。

| 分野 | 新規件数 | 主題 | 証拠 |
| --- | ---: | --- | --- |
| 多変数微積分 | 34 | 任意有限次元実内積空間のFréchet微分、勾配、方向・曲線微分、連鎖律、導関数の評価、2階微分の対称性、滑らかさ | [manifest](calculus-v4-batch.json)、[Lean](calculus-v4-batch.lean)、[型と意味](typed-calculus-v4-design.md) |
| 線形代数 | 34 | 任意の体・任意の自然数サイズの行列式、逆行列、Cramer、階数、特性多項式、Cayley–Hamilton、冪零・相似・trace | [manifest](linear-algebra-v4-batch.json)、[Lean](linear-algebra-v4-batch.lean)、[型と意味](typed-linear-algebra-v4-design.md) |
| 可換環論 | 33 | 素スペクトルとZariski位相、局所化・商環のスペクトル、整拡大のlying over/going up/going down、Krull次元 | [manifest](commalg-v4-batch.json)、[Lean](commalg-v4-batch.lean)、[型と意味](typed-commalg-v4-design.md) |

固定サイズ・固定次数への置換で増やしていない。OpenMathの閉じた辞書は、行列の体と縦横サイズ、微分の始域・終域と点、環とそのイデアル・素点・局所化先を区別する。Leanコンパイルに加え、別担当が101件すべての自然文・XML・Lean・証明手順と演算子の意味を照合し、修正事項はなかった。誤適用例は微積分34、線形代数34、可換環論29の計97件で、全101カードに対応する。これらは検索器の精度試験ではない。

全件は既存のLean toolchain `leanprover/lean4:v4.32.0-rc1` と Mathlib `8b62164d808cd0f23b7d8cc28190a6c1a1bb483a` で実コンパイル済み。証拠にはLean本文・validator・registryのSHA-256を固定した。新旧profileを含む単体・統合テスト472件、カバレッジ監査テスト13件、対象Ruff・mypyが成功した。旧profileの43ファイルは作業前後でSHA-256が一致する。

[継続承認](../承認リスト.md)の範囲で、版・profile ID・canonical OpenMathだけを指定のOpenAI embedding APIへ送り、101件の384次元ベクトルを生成した。SQLは単一トランザクションでローカルDBへ追記した（SHA-256 `1822133d1de6a7843e7f186ebbfa8352fdaee1d05a31cdbd024d94c9a3a093b9`）。101件を読み戻し、本文・XML・Sketch・証拠hash・状態・embedding設定と384次元／非零性をmanifestと照合した。登録前後のDB件数は466→567、embeddingも466→567。証跡は`output/math-expansion-v4-20260930/`に保存した。

これらはまだ**ローカルauthoring Draft**であり、型付きruntimeの公開中件数は0。現在の回答時に検索・適用されることや、処理時間・正答率の改善は主張できない。教科書の全演習も未網羅で、条件付き収束、多変数Taylor・積分、Jordan標準形・SVD、完備化・一般の次元論などが残る。章・演習形式ごとの網羅表と、誤適用を含む実検索評価も必要である。
