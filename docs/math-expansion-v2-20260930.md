# 一般定理Draftの拡充 v2 — 2026-09-30

初年級の線形代数・微積分と、アティヤ＝マクドナルド水準の可換環論を充実させる依頼に基づき、一般定理77件を追加した。全件をLeanでコンパイルし、自然文・OpenMath・Leanの意味を独立レビューしたうえで、実embeddingとともにローカルDraft保管庫へ登録した。

続く[拡充v3](math-expansion-v3-20260930.md)でさらに98件を追加した。以下の件数・不足領域はv2完了時点の記録である。

型付きDraftとembeddingは各291件から**368件**、profileは16から19、manifestは20から23になった。教科書全演習の網羅や、回答時の検索精度・処理時間の改善を確認したという意味ではない。

## 今回追加した内容

| 分野 | 件数 | 主な一般定理 | 成果物 |
| --- | ---: | --- | --- |
| 微積分 | 28 | 任意の自然数nについての冪の微分・連続性・積分、超越関数の合成微分、平均値・Rolle、微積分の基本定理の両方向、部分積分・置換積分、積分の線形性・順序、単調性・中間値・極値 | [manifest](calculus-v2-batch.json)、[Lean](calculus-v2-batch.lean)、[辞書の意味と設計](typed-calculus-v2-design.md) |
| 線形代数 | 27 | 階数・退化次数、次元比較、部分空間の次元公式、任意nの独立族・生成族・基底、固有空間・固有ベクトルの独立性・固有基底、行列式の合成則・次数則 | [manifest](linear-algebra-v2-batch.json)、[Lean](linear-algebra-v2-batch.lean)、[辞書の意味と設計](typed-linear-algebra-v2-design.md) |
| 可換環論・加群 | 22 | 商加群の普遍性・対応・核による埋込み、有限生成の商・像・拡張、中山の補題のJacobson版・局所環版・生成版、テンソル積の有限生成・全射保存、平坦性による単射・完全性保存 | [manifest](commalg-modules-v2-batch.json)、[Lean](commalg-modules-v2-batch.lean)、[辞書の意味と設計](typed-commalg-modules-v2-design.md) |

数値や変数名だけを変えた追加はない。線形代数の空間と有限族の長さ、微積分の指数・関数・端点、可換環論の環・加群・部分加群を変数として扱う。中山の補題には有限生成を残し、自由加群やNoether環という不要な仮定を加えていない。

## OpenMathと証明の対応

従来の表現で不足していた構造を、新しい3つのauthoring用profileに分離した。

- `typed-calculus-v2`：自然数型と可変指数、自然数の切り詰めた前者・後者・実数への埋込み、実関数、区間積分値と可積分性を区別する演算。
- `typed-linear-algebra-v2`：体、有限次元空間、写像の定義域・値域、部分空間、添字長を保つ有限族・基底。
- `typed-commalg-modules-v2`：商の元の加群と部分加群を保持する型、順序付きテンソル積、有限生成・局所性・平坦性。

各辞書は記号の引数順・型・数学的意味・Lean上の意味を固定する。標準OpenMath記号とPALS独自の版付き記号を区別し、既存のalpha正規化を型検査後に適用する。既存16profileのvalidator・registry計32ファイルは作業前後でSHA-256が一致した。

たとえば微分はOpenMathの `(f, point, slope)` をLeanの `HasDerivAt f slope point` に対応付ける。指数n=0も証明対象とし、積分の式だけから可積分性を推定しない。Leanの全域関数 `Real.log`・`Real.sqrt` の意味も辞書に明示した。型検査だけでは数学的真偽や同じ実数型の引数交換を判定できないため、意味レビューを別に実施した。

## 検証

- 全77件を既存workspaceの `leanprover/lean4:v4.32.0-rc1`、Mathlib `8b62164d808cd0f23b7d8cc28190a6c1a1bb483a` で実コンパイルした。`sorry`、`admit`、追加公理は使っていない。
- 各manifestはLean本文全体・validator・registryのhashとtoolchain・Mathlib revisionを保持する。最後の型注釈修正後もカード内容・Lean本文・辞書が不変であることを確認した。
- 微積分28件と加群22件は別の担当、線形代数27件は親担当が全件の自然文・OpenMath・Lean・Sketchを照合した。authoring登録とruntimeの境界も別担当がレビューした。未解決の指摘はない。
- profile、loader、routing、guidance、実manifest統合のテスト196件、カバレッジ監査テスト13件が成功。対象Ruffと新規・変更validator/loader計5モジュールのstrict mypyも成功した。
- 誤適用の反例付き質問を微積分23、線形代数27、加群12、計62件作成し、77カードすべてに対応させた。これは検索試験の合格結果ではない。
- 新規77件にcanonical OpenMathの衝突・ID重複はなかった。類似性検査の1候補は `rank(f)≤dim V` と `rank(f)≤dim W`。定義域と値域に関する別の不等式なので、両方を保持する判断を設計文書に記録した。

## 保存結果と境界

[継続承認](../承認リスト.md)に基づき、形式の版・profile ID・canonical OpenMathを `https://api.openai.com/v1/embeddings` に送信し、`text-embedding-3-small` の384次元embeddingを77件生成した。最終の型注釈変更はembedding入力を変えないため、入力の完全一致を検査して実ベクトルを再利用し、最新の証拠hashを持つSQLを作成した。

既存の `pals_local_typed_catalog` へ単一トランザクションで追記した。全77件を読み戻し、命題・OpenMath・証明方針・Sketch・manifest対応・authoring状態・辞書/validator/profileのhash・embedding固定設定を照合した。全ベクトルは384次元かつ非零。通常Draft431件と型付き公開中0件は変更していない。

登録SQLのSHA-256は `2c2546fe28e9b19ba6a96f7b2084b010c8f0165309f866319bb9f2f63bf4c773`。ローカル証跡は `output/math-expansion-v2-20260930/` の `before-insert.json`、`after-insert.json`、`insert-77.log`、`unit-tests.log`、`persisted-verification.json`、`embedding-inputs.json`。生成出力はcommit対象にしない。

新profileはローカルauthoringの検証・embedding・保存に接続した。runtimeの対応profileとして自動広告せず、状態は `local_authoring_evidence_bound_not_admitted` とした。署名付き公開、検索・適用精度の評価、回答処理の短縮、本番反映は未実施。

## なお不足する主要範囲

| 分野 | 次の拡充対象 |
| --- | --- |
| 線形代数 | 内積・直交化、座標変換、スペクトル定理、Jordan標準形、具体的な行列操作から一般構造への橋渡し |
| 微積分・解析 | 数列・級数の収束、Taylor展開と剰余、冪級数、一様収束、極限と微分・積分の交換、広義積分 |
| 可換環論 | 局所化と完全性の連携、Hom・テンソル積の普遍性、準素分解・整拡大・次元論の演習への展開、Artin–Rees、完備化 |

件数を教科書の演習網羅率へ換算していない。全演習という基準に近づけるには、章・問題型ごとの対応表、未対応の仮定や結論、実際の検索・適用評価を継続して埋める必要がある。
