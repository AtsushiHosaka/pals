# 初等幾何とグラフの図コンポーネント 設計

要件は [specs/geometry-figures](../../specs/geometry-figures/requirements.md) にある。

## 経緯

グラフは、2026-10-26 の Codex チャット「PALS interactive explanation side panel」で試作された。その作業フォルダは削除済みで、どのリポジトリにも入っていなかった。チャット履歴から設計を復元し、次のユーザーの指示を引き継いだ。

- テンプレート名と数値のパラメータで呼び出す。
- テーマの色だけを使う。
- 図の中に説明文を置かない。文字の代わりにアイコンを使う。
- 本文にホバーすると図が変わる。

サイドパネルで開く部分は、2026-11-03 の指示で本文への直接埋め込みに変えた。

## 呼び出し形式

```json
{
  "version": 1,
  "template": "inscribed-angle",
  "parameters": {
    "labels": { "chord_start": "A", "chord_end": "B", "on_arc_1": "P", "on_arc_2": "Q" },
    "marks": [
      { "icon": "equal_angle", "at": [["A","P","B"], ["A","Q","B"]], "claim": "conclusion", "step": "angles" }
    ]
  }
}
```

回答は `answer.visualization` にこの呼び出しを持ち、段落との対応を `answer.visualization_bindings`（`{step_id, paragraph}` の配列）に持つ。座標はテンプレートが決めるので、円周角の4点は必ず同じ円の上に乗る。

## テンプレート

| 系統 | テンプレート | 枠とパラメータ |
| --- | --- | --- |
| 三角形 | `triangle` | `a b c`、`shape`、`extra_points` |
| | `congruent-triangles`、`similar-triangles` | `a b c d e f`（対応順）、`criterion` |
| | `triangle-center` | `a b c center`、`kind`（5種） |
| | `ceva` | `a b c d e f p` |
| | `menelaus` | `a b c d e f` |
| 円 | `inscribed-angle` | `chord_start chord_end on_arc_1`、任意で `on_arc_2 center` |
| | `tangent-chord` | `touch chord_end on_arc tangent_point` |
| | `power-of-point` | `p a b c`、`d`、`kind`（3種） |
| | `cyclic-quadrilateral` | `a b c d` |
| | `tangent-lengths` | `p touch_1 touch_2`、任意で `center` |
| グラフ | `polynomial` | `coefficients domain range` |
| | `polynomial-derivative` | 上に加えて `anchor offsets` |

幾何のテンプレートには共通で `marks` と `segments` を渡せる。

## 記号

`equal_length`（目盛り）、`equal_angle`（弧）、`right_angle`（小さな四角）、`parallel`（矢羽根）の4種類である。同じ種類の組が複数あるときは、目盛りや弧の数で区別する。`claim` が `conclusion` の記号はテーマのアクセント色で描く。

## 描画

1. `lib/figureCalls.ts` が呼び出しを検証する。
2. `lib/figureLayouts.ts` が線、円、点、文字の描画要素を作る。
3. `components/AnswerFigure.tsx` が同じ描画要素を SVG に描き、TikZ ソースも同じ描画要素から作る。

ブラウザの中で完結するので、描画ワーカーを呼ばない。

## 既存の問題との関係

| 問題 | 扱い |
| --- | --- |
| ラベルの `\|` による TikZ 注入 | ラベルを `[A-Za-z][0-9']?` に限る。描画の経路に TeX がない。 |
| 4図同時描画で3件が 503 | 描画ワーカーを呼ばないので起きない。 |
| 平行・逆平行な矢印の重なり | 可換図式を対象にしないので、この経路には現れない。可換図式の問題は `pals-api#26` に残る。 |
| 描画失敗で本文が隠れる | パースの失敗と描画の例外を図の中で閉じる。 |

## 検証の境界

図は説明であり、証拠ではない。

| 経路 | 確認すること | 失敗したとき |
| --- | --- | --- |
| 共通 | 閉じたカタログへの一致（agent、API、webfront で同じテストデータを使う） | agent は図を捨てる。API は受け付けない。webfront は図だけを出さない。 |
| `reviewed_explanation` | ラベルが本文に現れる。独立レビューの `figure_consistent` | 図を捨て、本文は残す。 |
| `lean_verified` | ラベルが Lean ソースに現れる。出力レビューが図も確認する | 図を捨てる。レビューで却下されたら、図なしで作り直す。 |

ラベルの確認は名前の対応だけを縛り、図の数学的な正しさを証明しない。

既存の出力ダイジェストを壊さないよう、図がない回答の保存形式と digest は変えない。

## カタログ再利用の回答

図の呼び出しは Recipe の封印の外に置く。図は証拠ではない（GF-006）ので、図の修正に Recipe の新しい revision と再審査を求めない。封印に入れると、閉じた検証を持つ古い API が図付きの entry を読めず、再利用全体が 503 になる。

| 場所 | 役割 |
| --- | --- |
| `pals-agent/testdata/catalog-figures-v1/figures.yaml` | Recipe ID ごとの呼び出し（元データ） |
| `pals-agent/testdata/catalog-figures-v1/build.py` | カードの本文と照合し、`recipe-figures-v1.json` を作る |
| `pals-api/app/domain/recipe_figures_v1.json` | 上の生成物のコピー。API の起動時に一度だけ読む |
| `pals-api/app/domain/recipe_figures.py` | `(recipe_id, 本文の SHA-256)` で図を引く |

図を付けるのは `resolve_catalog_admission` の中で、本文の照合が通った後の1か所である。再利用の3経路（完全一致入力、意味審査、LLM審査）はここを通る。

- `settlement_sha256` は図を付ける前に計算するので、再送の判定は変わらない。
- 図は回答の行に保存されるので、対応表が後で変わっても、再読み込みで同じ図が出る。
- キーに Lean ソースとツールチェーンを含めないので、Fingerprint v2 で再登録しても、本文が同じなら図は残る。
- カードの本文を変えたら `build.py` を実行し、生成物を API にコピーする。忘れても図が消えるだけで、回答は壊れない。

## 制限

- 本文を LLM が毎回書くカタログ回答には図が付かない。
- グラフは多項式だけを扱う。
- `proof-job` の旧説明画面（`ProofExplanation`）には図を出さず、チャットの回答にだけ出す。
- 共有スナップショットは本文だけを使うので、図は含まれない。
