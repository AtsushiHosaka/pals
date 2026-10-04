# 大学基礎Draft拡充 v6 — 2026-09-30

大学初年級の線形代数・一変数微積分・多変数微積分を章と問題形式で再監査し、一般形のLean証明 **68件** を10個の新しいauthoring manifestに追加した。既存の対応漏れも9件修正した。追加カードは固定の2×2計算や指数だけを変えた件数稼ぎではなく、任意の体・有限次元、任意次数、関数・領域・区間などのパラメータを持つ命題を中心にした。

| 分野 | 新規Draft | 主な追加範囲 |
|---|---:|---|
| 線形代数 | 19 | 可解性の双対判定、核と非一意性、冪零行列の逆、部分空間、独立性、基底、核像分解、矩形行列の行列式恒等式、ノルムの反例 |
| 一変数微積分 | 24 | 連続延長、微分法則と反例、平均値の定理、極値、Taylor、FTC、積分、級数・冪級数 |
| 多変数微積分 | 25 | 偏微分・Jacobian・Hessian・Lagrange乗数、重積分の例外、二段階変数変換、線積分、長方形上のGreen/Gauss |
| **計** | **68** | 既存profileの補充に加え、線形代数v6とベクトル解析v6の型付きOpenMath辞書を新設 |

## 固定30章の測定結果

[契約](foundation-curriculum-contract.v1.json)が線形代数・一変数微積分・多変数微積分の各10章に要求する5問題形式と入門1・標準2・上級1の難易度枠を、[監査器](../pals-scripts/audit-foundation-curriculum.py)で測定した。各bindingは実カードIDとmanifest、許可profile、canonical OpenMath、証拠pin、Lean bundleに照合した。同一章内の数値・変数名・XML整形だけの重複は加点しない。

| 測定点 | 問題形式 | 難易度枠 | 両条件達成章 |
|---|---:|---:|---:|
| v5終了時 | 76/150 | 83/120 | 0/30 |
| 既存対応漏れ9件の修正後 | 83/150 | 91/120 | 2/30 |
| **今回の最終値** | **150/150** | **120/120** | **30/30** |

分野別にも線形代数50/50形式・40/40難易度、一変数50/50・40/40、多変数50/50・40/40。invalid bindingは0。今回は `--replay-lean` で対応する**20 manifestの正規Lean bundleを実コンパイル**し、同水準の150/150・120/120・30/30を記録した。[Lean再実行つき監査JSON](foundation-curriculum-audit-20260930-v6-lean.json)と[内容監査の設計](foundation-curriculum-audit-design.md)を参照。

これはPALSの**最低演習形式契約**を満たしたという測定であり、教科書の全演習収録率ではない。章内の細類型は未測定で、曲面積分・一般曲面Stokes・任意領域Gauss、RREFと自由変数、広義積分などは別途必要である。より広い大学基礎100章スコープは **175/500形式**の旧監査bindingにとどまり、今回の30章以外の70章には内容審査が必要である。[次の70章の不足調査](undergraduate-core-next-gaps-20260930.md)で既存Draftの対応漏れと証明不足を区別した。検索・具体化・問題のLean完了率と処理時間短縮は未測定であり、この100%を実利用の成功率とは呼ばない。

## 証拠とローカル保存

全68件のcanonical OpenMath・証拠pin・Lean target/witness bundle一致をprofile loaderで検査し、正規Lean bundleを再コンパイルした。自然文と形式表現の意味対応は内容レビューで確認したが、監査器が意味同値を自動証明するわけではない。新profileの単体テスト、補充manifestの整合テスト、カバレッジ監査テスト、Ruff、mypyが成功した。v5終了時に記録した旧profile43ファイルのSHA-256はすべて不変。

[継続承認](../承認リスト.md)の範囲で、版・profile ID・canonical OpenMathのみを指定OpenAI embedding APIに送り、68件の384次元実embeddingを生成した。ローカルDBへ56件、11件、1件をそれぞれ単一トランザクションで追記し、全68件の本文・XML・Sketch・証拠hash・embedding設定と非零ベクトルをmanifestと読み戻し照合した。型付きlocal Draft/embeddingは **681→749件**、profile **28→30**、manifest **32→42**。登録SQLのSHA-256は順に `441ebdefd9706b33f71559aeb92b7261edac725bb6925ca78e97a29336a43008`、`2a78ca8b754fba4f9373bbd4d2ff6a2f71d5bc7aa79e5ea6be3e27fd4e6d4187`、`e63f102e706e26e627a7e21b0dd542ff4009e4fdfe55b0a335b1338b9cc70a65`。ローカル作業証跡は `output/foundation-expansion-v6-20260930/` に保存した。typed runtime公開は0件のままで、再利用時の実行性能は測定していない。
