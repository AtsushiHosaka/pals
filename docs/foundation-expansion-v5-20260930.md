# 大学基礎Draftの拡充と網羅監査 v5 — 2026-09-30

大学初年級を優先し、線形代数39件、一変数微積分43件、多変数微積分32件の一般Lean証明を追加した。固定2×2や特定の指数を変えて件数を増やしていない。型付きローカルDraftは**567→681件**、実embeddingも**567→681件**、28 profile・32 manifestとなった。

| 分野 | 新規 | 主な一般命題 | 証拠 |
| --- | ---: | --- | --- |
| 一変数微積分 | 43 | 実変数の関数極限、区間上の積分評価・部分積分・置換、逆関数微分、単調性・凸性、Darboux、Cauchy平均値、一般反例族 | [manifest](calculus-v5-batch.json)、[Lean](calculus-v5-batch.lean)、[設計](typed-calculus-v5-design.md) |
| 線形代数 | 39 | 任意の体・有限次元空間の基底と座標、写像の基底による構成、行列表現・基底変換、行基本変形、固有値・最小多項式、一般反例族 | [manifest](linear-algebra-v5-batch.json)、[Lean](linear-algebra-v5-batch.lean)、[設計](typed-linear-algebra-v5-design.md) |
| 多変数微積分 | 32 | 任意有限次元座標空間の偏微分・Jacobian、二次形式のHessian/Taylor、Lagrange乗数、Fubini、Jacobian変数変換、potentialの経路積分 | [manifest](multivariable-v5-batch.json)、[Lean](multivariable-v5-batch.lean)、[設計](typed-multivariable-v5-design.md) |

各manifestのカードは閉じた依存型のOpenMath辞書で検査し、実Leanコンパイルで証明した。自然文・XML・Lean・Sketchと反例114件は担当者以外が照合した。3件の一変数、3件の線形代数、1件の多変数の正規Draftは反例族自体をLeanで証明する。新profileの単体テストは34+52+68件、統合テストを含む対象pytest、既存カバレッジ監査13件、新カリキュラム監査30件、Ruff・mypyが成功した。旧profile43ファイルのSHA-256は不変。

## 件数とは別の網羅指標

[基礎カリキュラム契約](foundation-curriculum-contract.v1.json)は線形代数・一変数微積分・多変数微積分の各10章、計30章を固定する。各章に認識・計算/構成・証明・反例検討・組合せの5問題形式、入門1・標準2・上級1の難易度枠を要求する。[監査器](../pals-scripts/audit-foundation-curriculum.py)は実カードIDとmanifest、許可profile、正規化OpenMath構造、証拠hashとLean bundleを確認してから加点する。分母を設定変更で縮めることは拒否し、同内容の数値・変数・XML整形だけの差は重複排除する。

| 分野 | 問題形式 | 難易度枠 | 全条件達成章 |
| --- | ---: | ---: | ---: |
| 線形代数 | 27/50 | 30/40 | 0/10 |
| 一変数微積分 | 25/50 | 30/40 | 0/10 |
| 多変数微積分 | 24/50 | 23/40 | 0/10 |
| **合計** | **76/150（50.67%）** | **83/120（69.17%）** | **0/30** |

30章すべてに少なくとも1件の明示対応があるが、どの章も要求された問題形式と難易度を同時に満たしていない。欠けているのは問題形式74枠、難易度37枠。形式別には認識14/30、計算20/30、証明24/30、反例6/30、組合せ12/30で、特に反例と複数結果を組み合わせる問題が薄い。旧カードの分類を保守的に修正したv5追加前の基準値は34/150形式・44/120難易度・0/30章だった。[実測JSON](foundation-curriculum-audit-20260930-v5.json)は全章の不足セルと根拠カードを含む。

この指標はPALSが定義した基礎30章への**明示的なauthoring対応率**であり、特定の教科書の全演習を収録した率でも、回答時の成功率でもない。教材としての意味・難易度の妥当性は人手でレビューし、実問題の検索・一般変数の具体化・証明完了は別に測る必要がある。型付きruntimeの公開中件数は0件で、短縮効果は未測定。

次の優先欠落は、線形代数のRREF・自由変数による全解構成・基底抽出、一変数の冪級数・広義積分、多変数の一般高階Taylor・逆/陰関数・曲面積分・Stokes、および各章の反例/組合せ形式である。難易度を上げたカードだけで入門問題の不足を埋めたことにはしない。

## 保存と再現

[継続承認](../承認リスト.md)に従い、版・profile ID・canonical OpenMathを指定OpenAI embedding APIへ送った。114件の384次元実embeddingを生成し、単一トランザクションでローカルDraft DBへ追記した。114件を読み戻し、本文・XML・Sketch・証拠hash・authoring状態・embedding設定および次元/非零性を元manifestと照合した。登録SQLのSHA-256は`d1b82437703c15af82072c6ed48e5d7e316824371526bae112df33f4fc944f85`。証跡は`output/foundation-expansion-v5-20260930/`にある。
