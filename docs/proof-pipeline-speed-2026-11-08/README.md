# 証明パイプラインの直列モデル呼び出しを減らす(2026-11-08)

新しい1枚の証明を作るときの待ち時間は、直列のモデル呼び出しの数と、各呼び出しの出力量で決まります。pals-agent の Draft / Sketch / Prove / Repair を調べ、モデルを呼ばずに済む3つの近道を、既定オフのフラグとして追加しました。

## パイプラインと修復ループ

```
初回      Draft ─▶ Sketch ─▶ [Sketchの Lean 検査] ─▶ Prove ─▶ Lean 検証
                                  └ 失敗: 空の出力(pals.generation_empty)
失敗後    route(モデル1回) ─▶ draft なら D+S+P、sketch なら S+P、prove なら P の再実行
```

`HybridLeanGenerator.repair()` は段階実行の経路では使われていません。

## 記録からの集計(Terra low / medium、各12カード)

`stage_breakdown.py` で `result.json` を集計しました。1呼び出しの平均秒数です。

| 段 | low | medium |
|---|---|---|
| Draft | 6.8 | 12.1 |
| Sketch | 11.2 | 35.4 |
| Prove(初回) | 9.3 | 24.8 |
| Prove(修復後) | 9.8 | 33.8 |
| route 選択 | 3.6 | 7.5 |

- 時間は出力トークンにほぼ比例します。呼び出しごとの固定費は2〜3秒です。
- medium では Sketch が全モデル時間の約3割で最大です。
- 試行の約28%が、Sketch の Lean 検査失敗で空の出力になり、Prove に進めませんでした。
- route 選択は約1割です。59件の判断は、直前の失敗が `lean.formal_harness_mismatch` なら draft、それ以外なら prove という1つの規則に一致しました。
- harness 不一致のあとに Draft からやり直して成功したのは 2/27 でした。

## 追加した近道(すべて既定オフ)

| フラグ | 動作 | 期待する利点 | リスク |
|---|---|---|---|
| `harness_splice` | モデルが書いた命題が固定の形式命題と、空白・改行・`;`・コメントの違いだけで食い違うとき、命題の範囲を固定の命題に置き換える | 不一致 → route → D+S+P の再実行を省く | 置換後も同じ前処理と Lean 検証を通るので正しさは変わらない。モデルが命題自体を変えた場合は何もしない |
| `deterministic_repair_route` | 形式命題が固定で、失敗が `repair_stagnation` / `proof_method_mismatch` 以外のとき、再開段をモデルなしで決める | route 呼び出し1回(medium で約7秒)を省く | 数学的な判断が要る失敗は従来どおりモデルが決める。規則は59件の記録から作ったので、別の分布では最適でないことがある |
| `sketch_failure_proceeds_to_prove` | Sketch が穴を含み、Lean 検査に失敗したとき、Sketch の診断を付けて Prove へ進む(従来は空の出力で失敗) | 空の出力による試行の消費と、続く route・再実行を省く | 壊れた Sketch から Prove が始まるので、Prove が直せず修復を1回使うことがある |

どのフラグでも、最終の可否は Lean の検証だけで決まります。環境変数は `PALS_HARNESS_SPLICE_ENABLED`、`PALS_DETERMINISTIC_REPAIR_ROUTE_ENABLED`、`PALS_SKETCH_FAILURE_PROCEEDS_TO_PROVE_ENABLED` です。

実装しなかったもの: Draft と Sketch の統合(節約は呼び出し固定費の2〜3秒だけ)、Sketch 段の廃止(品質を落とすおそれ)、再試行・キャッシュ・モデルの既定値(PR #73 などの別作業の領域)。

## 測定: 同じ12カード、Terra medium、修復上限6

3つのフラグをすべて有効にした版と、すべて無効の版を比べました。費用は Terra の入力1.25・出力5.00 USD/百万tokenでの推計です。

| 指標 | 無効 | 有効 |
|---|---|---|
| 成功 | 10/12 | 10/12 |
| 1枚あたり平均秒数 | 176.1 | 172.8 |
| 成功した10枚の平均秒数 | 122.1 | 106.0 |
| 失敗した2枚の秒数合計 | 891 | 1,013 |
| モデル呼び出し(合計) | 98 | 81 |
| うち route 選択 | 26 | 8 |
| 初回で検証できたカード | 0 | 4 |
| 推計費用(USD) | 1.16 | 1.10 |

読み方:

- 成功数は同じで、モデル呼び出しは17%、route 選択は69%減りました。
- 1枚あたり秒数の差は2%で、n=12 のばらつきより小さい値です。時間が縮まったとは言えません。成功した10枚だけでは13%短くなりましたが、同じ程度のばらつきが各カードの個別の差にもあります(例: `la_v3_polarization` は48.8秒から77.0秒に延びた)。
- 失敗した2枚はどちらも、修復のたびに formal_harness_mismatch で止まります。モデルが命題自体を書き換えるため、splice は効きませんでした。この種類は別の手当てが必要です。
- フラグごとの切り分けは行っていません。どの近道がどれだけ効いたかは分かりません。
- 各カード1回ずつの実行です。モデル側の出力は毎回変わります。
- 2回目の実行の後半4カードは通信断(`openai.error`)で無効になったため、同じ設定で取り直した結果を使っています。無効側の11・12枚目も、予算上限で打ち切られたため取り直しました。

## 推奨(この変更の範囲外)

過去の記録では、Terra low は同じカードで 10/12、80秒/枚でした(medium は 10/12、224秒/枚)。推論量の既定値は `model_roles.py` の持ち分なので変更していませんが、時間への効果は今回の3フラグより大きいと見ています。

## 再現

`pals-agent の PR [#76](https://github.com/AtsushiHosaka/pals-agent/pull/76) で、`tools/mathlib_index/hint_ab.py` に `--harness-splice`、`--deterministic-route`、`--sketch-continue` を追加しました。`--arms baseline --model gpt-6.1-terra --effort medium --max-repairs 6` で各版を測れます。出力の JSONL に、フラグ、route をモデルに尋ねた回数、各修復の route、呼び出し回数とトークンが入ります。
