# 基礎カリキュラム網羅の監査 v1

この監査は、線形代数・一変数微積分・多変数微積分について、既存の `coverage-matrix.v1.json` に明示されたカード対応を測る。カードの総件数からカリキュラムの網羅を推定しない。対象は PALS が定めた大学基礎30章であり、あらゆる大学の初年次科目を代表する標準ではない。多変数積分など、大学によって履修年次が異なる範囲も含む。

## 分母と判定

`foundation-curriculum-contract.v1.json` は既存契約の3分野・各10 family を章として固定し、各章の5 mode に具体的な問題形式の説明を与える。契約には各stage10章、mode IDと必要数、difficulty IDと必要数を明記し、v1の固定値と照合する。matrix defaultsおよび各family overrideの実効要件もこの契約と完全一致しなければ拒否する。章や mode が欠ける契約も拒否する。既存 matrix の編集、カードの自動分類、既存 binding の意味変更はしない。

- 問題形式: 30章 × 5 mode = **150枠**。認識、計算・構成、証明、反例の検討、複数結果の組合せを各章で1枠ずつ要求する。
- 難易度: 各章で introductory 1、standard 2、advanced 1 = **120枠**。standard は1カードでは満たさない。
- 章の達成: 当該章の問題形式と難易度の両方を満たす場合に限る。1枚のカードがあるだけでその章を達成としない。
- mode × difficulty の **450セル**は対応を可視化する診断表。既存契約はこの直積の全セルを要求していないため、450を達成率の分母として追加しない。

各軸の充足数は `sum(min(必要数, 当該セルに対応する有効カード数))`。同一カードは自身の mode 枠と difficulty 枠の双方に寄与するため、150と120を合算して単一の網羅率にはしない。分野間の分母は同じであり、利用頻度による重み付けはしていない。

## 明示対応と重複排除

`draft_bindings` の `(draft_id, authoring_manifest)` を既存 inventory の実在カードに完全一致で照合する。IDが別のファイルに存在しても加点しない。family の許可profile、XMLの構造も確認する。未対応カードが大量に存在しても加点しない。各結果にはカードID、manifest、mode、difficulty、XMLハッシュを残す。

同一章内では新監査内の XML構造タプルfingerprint で重複排除する。旧監査のfingerprintは変更しない。新fingerprintは名前空間付きタグ・整列済み属性・意味のあるテキスト・子要素を構造タプルにし、空白だけの整形text/tail、属性の記載順、変数名、数値リテラルを正規化する。数値・変数名・インデント・属性順を変更しただけのカードを複数パターンとして加点しない。これは保守的な近似であり、異なる数学的命題をまとめることもある。逆に、異なる fingerprint が数学的に独立した解法を保証するわけでもない。全件数を「意味の異なるパターン数」とは呼ばない。

binding の分野・mode・difficulty は人が判断して付ける。監査器はその意味的正しさや教材としての難易度を自動証明しない。各問題形式は広い型であり、例えば「積分法」の1枠を満たしても、部分分数・三角置換・広義積分などすべての小類型を網羅したことにはならない。今回の指標は明示された契約への対応率であり、出題分布に対する正答率ではない。

## 証拠水準

| 水準 | 実際に確認するもの | 確認していないもの |
|---|---|---|
| `authored` | exact binding、実在カード、許可profile、構文解析可能なXML | 型validator、Lean、意味一致、DB、問題処理 |
| `artifact_bound` | expansion loaderによるcanonical XML、validator/registry pins、toolchain/mathlib pins、全カードから復元したLeanファイルの完全一致 | この実行でのコンパイル、自然文/XML/Leanの意味一致、DB、問題処理 |
| `lean_replayed` | `--replay-lean` 指定時、この実行で既存workspaceの `lake env lean` が終了コード0 | カードの意味対応の独立レビュー、検索、具体化、ユーザー問題の解決 |
| runtime問題処理 | この監査では未実装・未測定 | 未測定なので `null` とし、0%や成功と報告しない |

再コンパイルを指定しなければ、その集計は `measurement_status=not_run`、分子・割合は `null`。各カードの `lean_replayed=false` は今回の再実行成功記録がないことを示す。既存の生成時コンパイルの失敗を意味しない。

現在、artifact adapter は `pals.typed-catalog-expansion-batch.v1` のみに対応する。旧sealed proposal等は、authoring対応は数えられても `unsupported_evidence_schema_no_credit` とし、上位証拠に自動昇格しない。DB保存やrelease admissionも推定しない。別のschemaに対応するときは、その証拠形式を検証するadapterとテストを追加する。

## 再現と検証

```sh
pals-agent/.venv/bin/python pals-scripts/test-foundation-curriculum-audit.py
pals-agent/.venv/bin/python pals-scripts/audit-foundation-curriculum.py \
  --output docs/foundation-curriculum-audit-20260930.json
```

必要なときだけ `--replay-lean` を加える。各対応manifestの証明ファイルを1回ずつコンパイルし、1ファイル180秒で打ち切る。既存の Lean workspace を使い、コンテナ・DB・ネットワーク操作を行わない。

出力には入力matrix・contract・inventory・監査器のハッシュ、対応manifestのハッシュ、検証した証拠pins、全セルのカード対応を保存する。matrixやmanifestが変われば過去の出力は当時のsnapshotであり、現状を知るには再実行する。invalid binding、現行expansion証拠の破損、要求した再コンパイルの失敗は終了コード1になる。

30件の回帰テストで、未対応総件数の非加点、別manifestの同ID、未知ID、profile不一致、mode/difficulty誤記、分母の縮小（matrix defaults・family overrides・契約axes・各stage章数）、重複章、整形差を含む構造重複、stale hash、証明ファイル不一致、standard 2枠、コンパイル成否とruntimeの分離、未測定null、決定的出力を確認した。compiler成否の分岐テストには模擬subprocessを用い、実コンパイルと表現しない。

## 2026-09-30 の実測（v5対応追加前）

44件の明示binding・7個のexpansion manifestを検証し、invalid bindingおよび構造重複は0件。44件すべてでartifact検証が通った。今回の監査では Lean を再コンパイルしていない。

| 分野 | 問題形式 | 難易度枠 | 全条件を満たす章 |
|---|---:|---:|---:|
| 線形代数 | 17/50 = 34% | 20/40 = 50% | 0/10 |
| 一変数微積分 | 12/50 = 24% | 17/40 = 42.5% | 0/10 |
| 多変数微積分 | 5/50 = 10% | 7/40 = 17.5% | 0/10 |
| 合計 | **34/150 = 22.67%** | **44/120 = 36.67%** | **0/30** |

これは authored / artifact_bound の両水準で同じ。23章には少なくとも1対応があるが、それを23/30章の網羅と表現しない。問題形式別では認識7/30、計算8/30、証明19/30、反例0/30、組合せ0/30。難易度別は introductory 22/30、standard 18/60、advanced 4/30。

`all_catalog_records_not_credited_to_target_scope` は他分野も含むリポジトリ全体の未加点records数である。基礎カリキュラムの不足数や分母として使わない。

## 不足に対する優先順

1. **基礎の対応を確かめる**: 現在明示対応がない関数極限・偏微分について、既存カードの仮定と結論を確認し、合致するものだけをbindする。存在しなければ一般カードを追加する。未対応をカード不存在と断定しない。
2. **計算・構成の不足を埋める**: 計算枠は8/30。特に連立方程式、座標・基底、核と像、固有空間、積分、偏微分・Jacobianについて、定理カードの存在に加えて、どの一般的な計算形式を直接支えるかを明示する。行基本変形や座標計算の多段問題は別途実行検証が必要。
3. **多変数の未対応章**: Lagrange乗数、重積分、変数変換、線積分・面積分、積分定理の5章。一般定理でも正則性・積分可能性・向きなどの条件を省かない。部分的な勾配定理をこれらの代用にしない。
4. **問題形式の偏りを直す**: 認識は7/30章に対応があり、残り23章が未対応。反例・組合せは各30章すべて未対応。negativesファイルがあるだけでは、その章の「反例を説明するカード」として加点しない。既存資料からレビューできるカードを作り、必要な条件を学習・選択できる形にする。
5. **難易度の不足を追う**: standardは42/60枠、advancedは26/30枠不足。出力の `missing_difficulty_slots` に章ごとの必要数・充足数・不足数・既存カードを記録する。高度なカードを増やすだけでは初級の不足や問題形式の不足は埋まらない。

実利用の処理省略量を評価する次の段階では、独立した問題集合ごとに検索・適用条件確認・一般変数の具体化・最終Lean検証の実行記録が必要。この監査の割合をその成功率として再利用しない。

## v5追加後

[v5の追加内容と結果](foundation-expansion-v5-20260930.md)を参照。監査の分母を契約で固定し、OpenMathの整形・変数・数値の差による重複を新監査内で除外した。現行snapshotは[監査結果v5](foundation-curriculum-audit-20260930-v5.json)。問題形式76/150、難易度83/120、全条件達成章0/30である。上の34/150・44/120はv5追加前の履歴値として残す。

## v6追加後

[v6の追加内容と結果](foundation-expansion-v6-20260930.md)を参照。現行snapshotは[Lean再実行つき監査結果v6](foundation-curriculum-audit-20260930-v6-lean.json)。問題形式150/150、難易度120/120、全条件達成章30/30を正規Lean bundleの再実行でも確認した。この30章は固定された最低演習形式の契約であり、全教科書の演習収録率でも実問題での再利用成功率でもない。[残る70章と章内の不足](undergraduate-core-next-gaps-20260930.md)は別に管理する。
