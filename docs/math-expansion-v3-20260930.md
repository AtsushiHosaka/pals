# 一般定理Draftの拡充 v3 — 2026-09-30

続く拡充は[v4](math-expansion-v4-20260930.md)を参照。

前回368件だった型付きローカルDraftに、新たな一般定理98件を追記した。全件のLean証明を実コンパイルし、OpenMath・自然文・Lean・Sketchの意味を別担当が照合してから、実embeddingとともに保存した。結果は**466件・embedding466件・22profile・26manifest**。

| 分野 | 件数 | 新しく扱える主題 | 証拠 |
| --- | ---: | --- | --- |
| 微積分・解析 | 31 | 一般の実数列の極限、級数の収束・和・比較・幾何級数、Taylor多項式とLagrange/積分剰余 | [manifest](calculus-v3-batch.json)、[Lean](calculus-v3-batch.lean)、[型と意味](typed-calculus-v3-design.md) |
| 線形代数 | 36 | 任意有限次元実内積空間の直交性・直交補・射影・最良近似、Gram–Schmidt、正規直交座標、対称作用素のスペクトル定理 | [manifest](linear-algebra-v3-batch.json)、[Lean](linear-algebra-v3-batch.lean)、[型と意味](typed-linear-algebra-v3-design.md) |
| 可換環論 | 31 | Noether/Artin鎖条件、有限長、加群の局所化と正確性、テンソル積の普遍性・右完全性、Homの完全性 | [manifest](commalg-v3-batch.json)、[Lean](commalg-v3-batch.lean)、[型と意味](typed-commalg-v3-design.md) |

単なる数値や変数名の置換で件数を増やしていない。新profileは従来の型付き辞書と独立し、環・加群・局所化集合、空間・内積・射影、数列・部分和・Taylorの次数と微分階数を明示する。Mathlibの`HasSum`と`Summable`は実数列の無条件収束を表すので、自然数順の部分和の極限とは辞書上で区別した。Taylorの剰余は正則性・区間・次数の仮定を保持する。

全98件のカードと証明には、toolchain `leanprover/lean4:v4.32.0-rc1`、Mathlib `8b62164d808cd0f23b7d8cc28190a6c1a1bb483a`、validator・registry・Lean本文のhashが結び付く。`sorry`・`admit`・追加公理はない。別担当による全件の意味レビューは問題なし。新旧profileを含む統合テスト332件、カバレッジ監査13件、対象Ruff・mypyに成功。誤適用を試す反例は微積分29、線形代数36、可換環論21、計86件で98カードすべてを対象とする。検索精度の評価結果ではない。

[継続承認](../承認リスト.md)に基づき、形式の版・profile ID・canonical OpenMathを指定のOpenAI embedding APIへ送信し、384次元の実embeddingを生成した。ローカルDBへの追記は単一トランザクション。98件を読み戻して、本文・OpenMath・Sketch・各hash・authoring状態・embedding設定をmanifestと照合し、全ベクトルの次元と非零性を確認した。登録SQLのSHA-256は`08ceb80f63833d9799023ba4e7b4b89b9e09c34da6af6b71a173f145b190a4db`。証跡は`output/math-expansion-v3-20260930/`に保存した。

従来の辞書・validator43ファイルは作業前後のSHA-256が一致する。通常Draft431件、型付き公開中0件は変わらない。新profileはローカルauthoring用であり、本番回答時の検索・適用、時間短縮、署名付き公開の効果はまだ評価していない。

教科書全演習を網羅していない。多変数微積分、一般nの行列計算・座標変換、素イデアル・整拡大・次元・完備化などが残る。章と演習形式ごとの対応・誤適用の実検索評価も引き続き必要。
