# 初等幾何の図コンポーネント 設計案

状態: 提案中。要件は [specs/geometry-figures](../../specs/geometry-figures/requirements.md) にある。

## 現状（2026-11-02 に確認）

| 確認したこと | 結果 |
| --- | --- |
| 図の表示 | `pals-api#26` と `pals-webfront#26` は draft で、本番のブランチに入っていない。 |
| チャットからの幾何 | `pals-geometry` は CLI だけで、チャットの経路から呼ばれない。`isosceles_midpoint` の図もチャットには届かない。 |
| 回答の型 | 本番の `ProofExplanationContentSchema` に図の欄がない。agent の `explain` も図を出さない。 |
| カタログ | `pals-agent#27` のカードで文字列検索すると、方べき、外心・垂心（ベクトル）は当たり、円周角、メネラウス、チェバ、内心、重心は当たらない。網羅的な確認ではない。 |
| グラフ機能 | push 済みのブランチ、PR、手元のワークツリーのファイル名、Codex の履歴では見つからない。`typed-finite-graph` はグラフ理論の Lean 記述用で、描画ではない。 |

## 方針: 座標を持たない宣言と、ブラウザでの SVG 描画

回答は部品名と頂点の対応だけを宣言する。座標は部品が決めるので、円周角の図の4点は必ず同じ円の上に乗る。

```json
{
  "component": "inscribed_angle",
  "vertices": { "chord_start": "A", "chord_end": "B", "on_arc_1": "P", "on_arc_2": "Q", "center": "O" },
  "marks": [
    { "icon": "equal_angle", "at": [["A","P","B"], ["A","Q","B"]], "claim": "conclusion" }
  ],
  "evidence": { "declaration": "…", "source_sha256": "…" }
}
```

既存のレビューで見つかった問題との関係は次のとおり。

| 問題 | この案での扱い |
| --- | --- |
| ラベルの `\|` による TikZ 注入 | ラベルを `[A-Z][0-9']?` に限る。描画の経路に TeX がない。 |
| 4図同時描画で3件が 503 | 描画ワーカーを呼ばない。 |
| 平行・逆平行な矢印の重なり | 部品の配置で、重なる線をずらす。可換図式は対象外なので #26 側に残る。 |
| 描画失敗で本文が隠れる | 図ごとに境界を置き、失敗は図の中で閉じる。 |

TikZ ソースは同じ宣言から決定的に生成し、コピー用に提供する（MRD-004）。実行はしない。

### 描画方式の代替案

| 案 | 長所 | 短所 |
| --- | --- | --- |
| A. ブラウザの SVG（推奨） | ワーカーと Docker が不要で、同時表示の制限がない。色と記号をテーマに合わせられる。 | TikZ と SVG の2つの生成器を揃える必要がある。 |
| B. #26 の TikZ ワーカー | 生成器が1つで済む。 | 本番に Docker の supervisor が要る。直列のロックの改修が必要で、スマホ幅で文字が縮む PNG になる。 |

## 部品（v1）

| 系統 | 部品 | 頂点の枠 |
| --- | --- | --- |
| 三角形 | `triangle` | `a b c` |
| | `congruent_triangles`、`similar_triangles` | `a b c` と `d e f`（対応順） |
| | `triangle_center`（`circumcenter` `incenter` `centroid` `orthocenter` `excenter`） | `a b c center` |
| | `ceva`、`menelaus` | `a b c` と分点 |
| 円 | `inscribed_angle` | `chord_start chord_end on_arc_1 on_arc_2 center` |
| | `tangent_chord` | `touch chord_end on_arc tangent_point` |
| | `power_of_point`（`chords` `secants` `tangent_secant`） | `p a b c d` |
| | `cyclic_quadrilateral` | `a b c d` |
| | `tangent_lengths` | `p touch_1 touch_2 center` |

各部品は共通の部品（点、線分、円、弧、記号）の組み合わせで作る。

## 記号（閉じた一覧）

| 記号 | 意味 |
| --- | --- |
| `equal_length` | 同じ長さ（目盛り） |
| `equal_angle` | 同じ角（弧） |
| `right_angle` | 直角（小さな四角） |
| `parallel` | 平行（矢羽根） |
| `congruent`、`similar` | 合同、相似の関係 |
| `sss` `sas` `asa` `aa` | 合同・相似の条件 |

記号の `claim` は `given` か `conclusion` で、線の種類と色を変える。記号をタップまたはフォーカスすると意味を示し、図の中には文字を増やさない。

複数の段階で説明するときは `steps` で強調する要素を切り替え、説明文の代わりに小さな図を並べる。

## 型での縛り

1. API（Pydantic）と webfront（TS）で、部品ごとに閉じた型を持つ。
2. agent は、頂点ラベルが Lean の宣言の束縛変数に存在することを機械的に確かめる。部品の枠と Lean の変数の対応表を持つ定理は `evidence` を付け、それ以外は説明図として扱う。
3. 図の宣言は既存の出力レビューと digest の対象に含める。

この確認はラベルの対応を縛るだけで、図の数学的な正しさを証明しない。

## 変更範囲

| リポジトリ | ベース | 内容 |
| --- | --- | --- |
| `pals-agent` | `codex/aws-private-verifier` | `explain` の図の宣言、検証、対応表 |
| `pals-api` | `codex/initial-aurora-bootstrap` | 図の欄、永続化、digest、TikZ 生成 |
| `pals-webfront` | `codex/sidebar-inline-math-20261031` | 部品、記号、表示 |

`codex/sidebar-inline-math-20261031` をベースにするのは、webfront の最近の PR の向き先に合わせるためで、本番のブランチかは未確認。
