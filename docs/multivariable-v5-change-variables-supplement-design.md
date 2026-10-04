# Change-of-variables foundation supplement

新規 2 件と既存 1 件の対応付けで、change-variables の justify_prove / counterexample_audit / synthesize、introductory 1 件・standard 2 件の残枠を満たす候補を作る。既存 v5 profile、registry、manifest は変更しない。全量化対象は任意自然数次元 n の実座標空間であり、個別の数値積分の焼き直しではない。

`mv_v5_constant_map_not_coordinate_change` は任意可測領域 s の二つの異なる点を仮定し、任意目標 c の定数写像と零導関数場を存在量化する。全点で実 Fréchet 導関数を持ちながら s 上で非単射となる。n=0 の場合、異なる二点の仮定が成立しないので零次元に偽の反例を主張しない。このカードは微分可能性から単射性を推論する誤りを反証する。非単射のすべての写像で積分公式が偽になるという主張ではない。

`mv_v5_successive_coordinate_changes` は f:s→f(s)、g:f(s)→g(f(s)) の順に変数変換する。実際の within-domain 導関数場 D,E と各領域上の単射性を仮定する。最終領域上の F の積分可能性から、二回の integrability equivalence により元領域上の |det D(x)| (|det E(f(x))| F(g(f(x)))) の積分可能性を得る。次いで二回の Jacobian 積分公式を結合する。E は必ず中間点 f(x) で評価する。n=0 も正しく含む。非零行列式・開集合・全域単射性を追加していない。実積分の値は存在仮定とともに述べ、totalized integral の等値から積分可能性を推論していない。

既存 `mv_v5_differentiable_injective_image_measurable` は中間像を積分領域にできる根拠であり、新規の同義カードを作らず justify_prove / standard として提案する。正確な対応表は同フォルダの `multivariable-v5-change-variables-binding-proposals.json` に置く。

OpenMath は既存の Function/DerivativeField/ScalarFunction/Set の n 依存キャリアだけを用いる。像は `image(n,f,s)`、重みは `jacobian_weighted(n,f,D,F)`、微分仮定は `has_fderiv` または `has_fderiv_within` として明示し、定理名だけの述語を追加しない。重みの入れ子は g の密度を f で引き戻す順序そのものを表す。旧 validator/registry hashes と完全に一致する証拠を記録する。

Generator は pinned local Lake の actual compile に成功してから七フィールドカードと証拠を manifest に保存する。独立テストは全 canonical XML、Lean exact bundle、三 hash、旧 profile bytes、生成再現、ID/XML 非重複、local loader、negative 1:1 対応を検査する。negative は authored evidence であり、retrieval 評価成功を意味しない。DB・共有 matrix への反映は親作業に属する。
