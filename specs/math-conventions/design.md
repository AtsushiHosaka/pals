# Math conventions — design

## Catalog v1（MCV-001）

カタログの正本は `pals-api` の `app/domain/math_conventions.py`。4 言語の文言と既定の読みを持ち、設定画面と確認文の両方がここから作られる。agent は判定用に ID と英語の説明だけを持ち、両方の ID の並びはテストで固定する。

| ID | 「含める」の読み | 「含めない」の読み | 既定（ゲスト） |
|---|---|---|---|
| `zero_ring_domain` | 零環（1 = 0 の環）も整域に含める | 整域は 1 ≠ 0 を要求する | 含めない |
| `natural_zero` | 自然数 ℕ に 0 を含める | 自然数は 1 から始まる | 含める |
| `ring_without_unit` | 乗法の単位元を持たない環も環に含める | 環は乗法の単位元を持つ | 含めない |
| `ring_commutative` | 「環」を可換環に限る | 「環」は可換とは限らない | 含めない |
| `zero_pow_zero` | 0⁰ = 1 と定める | 0⁰ は定義しない | 含める |
| `division_by_zero` | x / 0 = 0 と定める（Lean の約束） | 0 での割り算は定義しない | 含めない |
| `compact_hausdorff` | 「コンパクト」にハウスドルフ性を含める | コンパクトはハウスドルフ性を含まない | 含めない |
| `subset_proper` | ⊂ を真部分集合（⊊）とする | ⊂ は ⊆ と同じ | 含めない |
| `positive_zero` | 「正」に 0 を含める | 「正」は 0 より大きい | 含めない |
| `log_base_ten` | 底のない log を常用対数（底 10）とする | 底のない log は自然対数 | 含めない |
| `monotone_nonstrict` | 「単調増加」を広義（x ≤ y ⇒ f(x) ≤ f(y)）とする | 「単調増加」は狭義 | 含める |

確認の選択肢は、要求の出力言語で「今回だけ: 〈含める読み〉」「常に: 〈含める読み〉」「〈含めない読み〉（以後確認しない）」の順で固定する。API はこの位置で答えを解釈する。

## Data（MCV-002・MCV-004・MCV-006・MCV-009）

新しい appended release step `math-conventions`（`app/db/migrations/math_conventions/001_math_conventions.sql`）で、次の 2 表を作る。既存の `proof_requests` は変更しない。

- `account_math_conventions(user_id, convention_id, choice, created_at, updated_at)`
  - 主キーは (user_id, convention_id)。`choice` は `include` か `exclude`。
  - 行がない状態が「確認する」。ゲストの所有者（`guest:` で始まる ID）は保存できない。
- `proof_request_conventions(request_id, convention_id, choice, source, revision, created_at)`
  - その要求で採った読み。`source` は `once`・`account`・`default` のいずれか。
  - 主キーは (request_id, convention_id)。`request_id` は `proof_requests(id)` を参照する。

step は自分の表の fingerprint を `math_conventions_schema_revision` に記録する。serving は read-only の確認で、その step が current のときだけ機能を有効にする。ローカルの legacy release に登録する。本番の署名付き registry への追加は本番反映の承認時に行う。

## API

- `GET /v1/auth/me/math-conventions`
  - カタログ全項目と現在の設定（`ask`・`include`・`exclude`）、既定、4 言語の文言を返す。
  - 未リリースなら 503 `math_conventions_unavailable` を返す。
- `PUT /v1/auth/me/math-conventions/{id}` に `{"choice": "ask"|"include"|"exclude"}`
  - 1 項目を更新し、一覧を返す。`ask` は行を削除する。
- worker の claim 応答
  - 機能が有効なときだけ `math_conventions` を付ける。
  - 中身は `policy`（ゲストは `default`、それ以外は `ask`）と、その要求に効く読み `choices` だけ。`choices` は、その要求の `once` が学習者の設定より優先する。
- settlement
  - `needs_input` の質問は `convention_id` を持てる。
    - API は、ID がカタログにあること、方針が `ask` であること、その要求でまだ決まっていないことを確かめる。
    - 確認文と 3 つの選択肢は、カタログの文言で置き換えてから保存する。
  - `answered`・`formal` の settlement は `conventions: [{id, choice}]` を持てる。
    - API は、各読みがその要求の `once`・学習者の設定・既定（`default` 方針のときだけ）のどれかと一致することを確かめる。
    - 一致したら、出どころとともに `proof_request_conventions` に記録する。一致しない読みは settlement ごと拒否する。
- 前提の答え（ログイン中の学習者）
  - 保存中の質問が `convention_id` を持ち、答えが選択肢のどれかと完全に一致するとき、次のように扱う。

    | 位置 | 選択肢 | 扱い |
    |---|---|---|
    | 0 | 今回だけ含める | その要求に `once`・`include` を記録する |
    | 1 | 常に含める | `include` を設定に保存し、要求に `account` で記録する |
    | 2 | 含めない | `exclude` を設定に保存し、要求に `account` で記録する |

  - どの選択肢とも一致しない答えは通常の前提の答えとして扱う。
  - 答えの記録、設定の保存、要求の再キューは 1 トランザクションで行う。
- 公開する要求の応答
  - 記録があれば `conventions: [{id, choice, source, label}]` を付ける。`label` は出力言語での読み。
  - 質問には `convention_id` を付ける。どちらもないときは従来の形のまま。

## Agent（pals-agent）

- preflight の `premise_check` に `conventions`（カタログ ID の配列）を加える。
  - 読みによって主張の真偽が変わる項目だけを入れる。
  - プロンプトには、カタログの説明と、分かっている読み（`choices`。`default` 方針なら全項目の既定）を渡す。
  - 分かっている読みは命題に明記させる。読みの分からない項目は、モデル自身には聞かせない。
- コード側の判定は次のとおり。
  - 関係する項目のうち読みの分からないものがあり、方針が `ask` なら、最初の 1 項目について `convention_id` 付きの `needs_input` を返す。これは反例の確認より先に行う。
  - 関係して読みの分かる項目は `conventions` として settlement に付ける。
- claim に `math_conventions` がないとき（未リリース）は従来どおりとする。

## Webfront

- 設定の画面に「数学の約束事」の区分を設ける。
  - 全項目の題名・説明と、「確認する／〈含める読み〉／〈含めない読み〉」の選択を表示する。
  - 変更はその場で保存する。未リリースならその旨を表示する。
- 証明要求の表示
  - `convention_id` 付きの質問では、選択肢の下に「『常に』と『含めない』は設定に保存され、設定から変更できます」と、設定を開く手段を出す。
  - 要求に `conventions` があれば、回答（検証中・失敗を含む）に「この回答の前提」として読みと出どころを並べる。ログイン中なら設定を開く手段を出す。
- ゲストのチャットは前提の表示だけを行う。
