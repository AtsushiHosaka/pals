# プロンプト4フラグの初回実測（2026-11-10）

- 指標: 時間・費用・成功率（4フラグは `PALS_PROMPT_STATIC_PREFIX_ENABLED`、`PALS_PROMPT_FULL_MATHLIB_IMPORT_ENABLED`、`PALS_PROMPT_CONDITIONAL_GUIDANCE_ENABLED`、`PALS_DRAFT_STRUCTURED_FIELDS_ENABLED`）
- 仮説: 静的な指示を先頭に置くとプロバイダーの prefix キャッシュが効いて入力費用と時間が下がる。import を `import Mathlib` に固定すると import 起因の失敗が消える。条件付きの指針は、無関係な題のプロンプトを短くする。Draft の構造化欄は機械的に読める。
- 変更: なし（pals-agent#96・#97 のフラグを測っただけ）。道具は pals-agent#98 の評価一式と、本測定で足した `scripts/eval/run_stages.py`・`analyze_stages.py` と `RecordingGenerator` の修正（pals-agent#104）。
- Issue: AtsushiHosaka/pals#327

## 計画（実行前に書いたもの）

| 実行 | 内容 | 見積り |
|---|---|---|
| A | 調整用の題で Draft+Sketch を、全フラグ off で連続2回、`static_prefix` on で連続2回。段階別の入力・キャッシュ済み入力・時間 | 約US$0.3 |
| B | Tier 1。調整用約24題、`base` と `combined`（import・条件付き指針・静的先頭）を同じ題で交互に。Draft は共有して Sketch だけ差。結果は、固定版 Lean で `sorry` 許可のコンパイルが初回で通るか | 1以下 |
| C | Tier 2。全パイプラインで約12題、`base` と `combined` を交互に | 1以下（腕ごと） |
| 構造化欄 | Draft だけ。欄が読めるかと FINAL_ANSWER の中身 | 小 |

予算は1回US$1以下、このセッション合計US$3以下。**実際の変更点**: A は5題（予算を節約）。B は28題（Draft が安く、予算に余裕があった）。C は12題。構造化欄は B・C に混ぜず（Draft を共有する設計を壊すため）、別の Draft だけの実行にした。C の2回目の反復は、残りの予算で半端な題数しか回せず、題の集合が揃わなくなるので行わなかった。Tier 3（100題）は承認が要るため行っていない。

## 測定の条件

- 版: 親リポジトリ `af03a7f`。pals-agent は `origin/main` `8a75810`（`#98` 後）に、未コミットの `scripts/eval/run_stages.py`・`analyze_stages.py` を足した作業ツリー。`pals_agent/evals/runner.py` の修正（#104）は B・C の**後**に入れたので、B・C は修正前のコードで走った（影響は、C の段階別 draft/sketch/prove の行が記録されなかったことだけ。トークンと費用は実行の行に正しく入っている）。
- モデル: `gpt-6.1-terra`、推論の量 `medium`（リリースの役割束縛 `use_release_role_bindings=True`。Draft・Sketch・Prove・Repair すべて）。OpenAI Responses API。`PALS_OPENAI_MODEL`（.env.local の値）は使わず、役割束縛のモデルを使った。
- Lean: 固定版 4.32.0-rc1、Mathlib `8b62164`（メインのチェックアウトの構築済みを読み取りのみで使用）。Lean は1プロセスずつ。キャッシュは温かい状態。
- 修復上限: Tier 2 は `DEFAULT_MAX_REPAIR_ATTEMPTS`（3）。`ProofPipeline` の他の設定は既定（オプトインの近道は全部 off）。
- 腕のフラグ: `base` は4つとも false。`combined` は static_prefix・full_mathlib_import・conditional_guidance が true で、structured_fields は false。**3フラグを束ねた腕なので、どのフラグの効果かは分けられない。**
- 題: `generation-eval-v1` の tuning 分割（70題）のみ。held-out は開いていない。分野・難度の層（field×tier）を巡回して選んだ B の28題。C の12題は同じ並びの先頭12題（B の部分集合）。候補カード由来の題は Lean で成立するか未確認（README の注意）なので、失敗が命題の問題の可能性も残る。
- 順序: 題ごとに2腕を連続で実行し、腕の順序は交互。1題1腕1回（反復なし）。
- 統計: 題を単位にした対比較。二値は厳密 McNemar と、題でのブートストラップ95%区間。連続量は平均差の95%ブートストラップ区間と符号反転検定（B=10000）。検出可能差は、一致しない題の割合ごとに、厳密 McNemar の検出力80%を模擬で求めた。
- 費用: 記録した使用量に、リスト単価（Terra 入力US$1.25/出力US$5.00 per Mtok）を掛けた推計。キャッシュ済み入力の割引は引かないので上限寄り。請求額ではない。

## 結果

### A: prefix キャッシュは効いたか → **効いていない（この経路では）**

5題 × 腕2 × 連続2回 = 20回の Draft+Sketch（40呼び出し）。`cached_input_tokens` は**全40呼び出しで0**。

| 腕・段階 | 呼び出し | 入力（平均） | キャッシュ済み | 出力（平均） | 時間（平均） |
|---|---|---|---|---|---|
| base Draft | 10 | 772 | 0 | 625 | 9.5 s |
| base Sketch | 10 | 2022 | 0 | 2075 | 25.0 s |
| static_prefix Draft | 10 | 772 | 0 | 570 | 8.6 s |
| static_prefix Sketch | 10 | 1964 | 0 | 2040 | 24.7 s |

- Draft の入力は約770トークンで、プロバイダーのキャッシュ下限（1024）に届かない。キャッシュ対象になりうるのは Sketch（約2000）だけ。
- 静的な先頭は、Sketch で6275文字（約1500トークンと見込む）が題によらず共通になることをプロンプトの組み立てで確かめた。それでも hit は0。
- 対照（同じ endpoint、`gpt-6.1-terra`、US$0.03）: 約4200トークンの同一プロンプトを連続で3回。**同一プロンプトの再送は 4174/4177 がキャッシュ済み**（3回目）。**先頭4000トークンを共有し末尾だけ違う**3回（15秒間隔）は**すべて0**。つまりこの経路では、完全一致の再送は効くが、共通 prefix だけの再利用は観測できなかった。
- 読み方: 限界が大きい。対照の「共通 prefix のみ」は1つのプロンプトを1回試しただけで、間隔も15秒だけ。`prompt_cache_key` などのパラメーターも使っていない。本番の経路（直結か、ゲートウェイ経由か）でも同じとは限らない。**「prefix キャッシュが効かない」と一般化はできないが、このフラグの効果の前提（共通 prefix の hit）は、この測定では再現しなかった。**
- 副次: `static_prefix` は2つの指示を落とすので、Sketch の入力は平均58トークン（約3%）減った。

### B: Tier 1（Draft 共有・Sketch のみ差）。n=28 題、`base` vs `combined`

| 指標 | base | combined | 差（combined − base） | 95%区間 | 検定 |
|---|---|---|---|---|---|
| Sketch が初回でコンパイル（`sorry` 可） | 20/28 | 20/28 | 0 | −0.18〜+0.18（割合） | McNemar p=1.0（base のみ成功3、combined のみ成功3） |
| 入力トークン（Sketch、平均） | 1930 | 1799 | −131 | −170〜−100 | 符号反転 p<0.001 |
| 出力トークン（Sketch、平均） | 1688 | 1431 | −257（−15%） | −380〜−138 | p<0.001 |
| Sketch 生成の時間（平均） | 20.9 s | 18.0 s | −2.9 s（−14%） | −4.3〜−1.6 | |
| Lean の Sketch 検査（平均） | 2.83 s | 4.85 s | **+2.0 s（+71%）** | +1.4〜+2.5 | |
| 題あたりの合計時間（生成＋検査、平均） | 23.7 s | 22.8 s | −0.9 s | −2.2〜+0.4 | p=0.20 |
| 費用（Sketchのみ、28題合計） | US$0.304 | US$0.263 | −US$0.041（−13%） | | |

エラーの内訳（Lean の診断メッセージを分類）:

| 指標 | base | combined |
|---|---|---|
| エラー総数（28題の合計） | 11 | 19 |
| `Unknown identifier/constant` の件数（失敗した題の数） | 1（1題） | 6（3題） |
| import 起因のエラー | **0** | **0** |
| 先頭の import が `import Mathlib` だった Sketch | 7/28 | 28/28 |

- 初回コンパイルは**同数（20/28）で、一致しない題は3対3**。差は検出できない。n=28 で、一致しない題が約3割のとき、80%の検出力で拾える差は**約29ポイント（net 8題）以上**に限られる。これより小さい差は、このサンプルでは見えない。
- **「import 起因の失敗が減る」は見えなかった。** base でも21/28 の Sketch は絞った import（例: `Mathlib.Data.Real.Basic`）を書いていたが、import 起因のエラーは0件で、combined も0件。減る余地がまず無かった。
- 方向がはっきり出たのは次の2点。(1) combined は Sketch の出力が約15%短く、生成が約3秒速い。(2) full import 固定で Lean の Sketch 検査が約2秒（+71%）遅い（[stacks-import-index](2026-11-09-stacks-import-index.md) の測定、`import Mathlib` 5.1 s と最小 import 2.4 s の差と整合する）。**生成の短縮と検査の遅延がほぼ打ち消し合い、題あたりの合計時間は変わらない。**
- `Unknown identifier` は base 1 → combined 6 件（3題）と悪い方向だが、件数が少なく、1題（`seed-rank_nullity` の `Basis`）で3件を占める。偶然を排除できない。
- 一致しない6題: base のみ成功は `disc_size_difference_closed`・`seed-absolute_value_not_differentiable`・`seed-rank_nullity`、combined のみ成功は `calc_derivative_cubic_minus_linear`・`pq-prime-above-every-bound`・`rat_adjacent_partial_fractions`。いずれも反復なし1回の試行なので、モデルの抽出のばらつきと区別できない。

### C: Tier 2（全パイプライン）。n=12 題、`base` vs `combined`

| 指標 | base | combined | 差 | 95%区間 |
|---|---|---|---|---|
| 最終成功 | 11/12 | 11/12 | 0 | 0〜0（差なし） |
| 初回コンパイル（最初の試行で検証済み） | 8/12 | 6/12 | −2題（−0.17） | −0.50〜+0.17、McNemar p=0.63 |
| 修復の合計（回） | 9 | 9 | 0 | |
| 題あたりの時間（平均／中央値） | 121.5 s／79.7 s | 114.1 s／64.6 s | −7.4 s（平均） | −39.5〜+18.8、p=0.71 |
| 入力トークン（平均） | 11513 | 11161 | −351 | −3269〜+2458 |
| 出力トークン（平均） | 8230 | 7043 | −1187（−14%） | −3535〜+722 |
| 費用（12題合計） | US$0.667 | US$0.590 | −US$0.077（−12%） | |

- 最終成功は両腕とも11/12。失敗した1題は同じ `mv_foundation_exceptional_section_counterexample`（修復上限3まで使い切り、両腕で同じ）。n=12、成功が両腕で11/12なので、成功率の差はこの標本では**検出できない**（差が出るには、ほぼ全題で結果が割れる必要がある）。
- 初回コンパイルは base 8 → combined 6 と悪い向きだが、割れた題は3対1。p=0.63 で、偶然と区別できない。費用・時間・出力トークンは combined のほうが小さい向きだが、区間はどれも0をまたぐ。
- 参考: 全パイプラインの1題あたり費用は、推計で約US$0.05（平均）。前提にしていたUS$0.070より低い。

### 構造化欄（`PALS_DRAFT_STRUCTURED_FIELDS_ENABLED`）: Draft だけ

- 調整用の28題（B の題）で Draft を生成し、`FINAL_ANSWER` と `HARD_STEPS` が**厳密な構文で読めたのは28/28**（Clopper–Pearson 95%の下限は0.88）。`HARD_STEPS` の行数は0〜3（0行7題、1行6題、2行9題、3行6題）。
- `expected_answer` を持つ調整用6題（判定・計算の題）では、**6/6 で読めて、FINAL_ANSWER の結論が `expected_answer` の結論と一致した**（絶対値は0で微分不可、行列式は −1 で非零、連立方程式は解なし、射影は単射でない、平方は単射でない、右極限0かつ不連続）。`expected_answer` は短い答えでなく理由の文なので、結論の一致は私が目で比べた。n=6 で、95%の下限は0.54。
- Draft の欄が読めるかと結論が合うかの確認であり、下流（Sketch の入力に使うなど）の効果は測っていない。

## 費用（記録した使用量の推計、キャッシュ割引なし）

| 実行 | 費用 |
|---|---|
| A（キャッシュ確認、40呼び出し） | US$0.335 |
| キャッシュの対照（2回） | US$0.032 |
| B（Draft 28題＋Sketch 56） | US$0.661 |
| C（全パイプライン、24実行） | US$1.169 |
| 構造化欄（6題＋28題） | US$0.133 |
| ヘルスチェック | 約US$0 |
| **合計** | **US$2.329**（上限US$3）。実行ごとの上限はUS$1。C は2腕の合計がUS$1.17で、腕ごとにはUS$0.67・0.59（腕ごとのUS$1上限に収まる）。それ以外の実行はどれもUS$1以下。 |

## 限界

- `combined` は3フラグを束ねた腕で、どれが効いたか分けられない。個別の効果は未測定。
- 1題1腕1回。モデルの抽出のばらつき（同じ題でも成否が変わる）と、フラグの効果を区別できない。反復を入れていない。
- B は n=28、C は n=12。検出できるのは大きな差（B の初回コンパイルで約29ポイント以上）だけ。「差がない」は証明していない。
- 題は tuning 分割のみで、候補カード由来の題は命題の成立が未確認。held-out は開いていない。
- Lean の時間は共有マシン上の温かい状態の値。費用はリスト単価の推計。
- キャッシュの対照は1プロンプトで、間隔も15秒のみ。本番の経路を直接測ってはいない。
- 結論の一致の判定は人の目で、6題のみ。
- C は `RecordingGenerator` 修正前の道具で走ったため、段階別の draft/sketch/prove 行は記録されていない（pals-agent#104 で修正）。

## 判断（フラグごと）

| フラグ | 判断 | 理由 |
|---|---|---|
| `PROMPT_STATIC_PREFIX` | **off のまま** | 期待する効果（prefix キャッシュ）がこの経路で再現しなかった（40呼び出しで hit 0、共通 prefix だけの対照でも0）。入力は約3%減るだけ。本番の経路で hit するかを先に確かめる |
| `PROMPT_FULL_MATHLIB_IMPORT` | **off のまま** | 狙った import 起因の失敗は base でも0件で、減る余地がなかった。Lean の検査が約2秒（+71%）遅くなる。最小 import の計画（#92）の方向と逆 |
| `PROMPT_CONDITIONAL_GUIDANCE` | **Tier 3 が要る** | 単独の測定をしていない。束ねた腕では出力が約14〜15%短く、費用が約12%減る向きだが、初回コンパイルの変化（Tier 2 で 8→6/12）は検出できず、悪化の可能性も残る。個別腕と held-out を含む Tier 3 で決める |
| `DRAFT_STRUCTURED_FIELDS` | **off のまま。次は下流の効果を測る** | 欄は28/28で読め、判定の題の結論は6/6一致。壊れる心配は小さいが、欄を使う側（Sketch への入力など）の効果は未測定 |

どのフラグも「既定で on にする」根拠はこの測定では出ていない。「効かない」と決めたのでもない。大きな差だけが見えるサンプルで、見えなかっただけである。

## 次にやること

- 本番の経路（実際の base URL と呼び出し方）で、同一プロンプトと共通 prefix の対照を数回。hit するかを見てから `static_prefix` を再評価する。費用はUS$0.05程度。
- `combined` を3腕（import だけ、条件付き指針だけ、静的先頭だけ）に分け、各腕を Tier 1 で反復2回にする。費用の目安は1腕あたりUS$0.3程度。
- 構造化欄を Sketch に渡す変更を入れてから Tier 1 で測る。

## 出典・生データ

- pals-agent#104（道具）、pals-agent#96・#97・#98、AtsushiHosaka/pals#327。
- 生データ（JSONL。Lean 本文・Draft 本文は含まない）: `/Users/atsushi/Library/Application Support/Claude/side-session-notes/local_9cbdcd9c-4fc2-4716-a1cd-bc3f475ff312/flag-measurement-data/`（A: `runA/cache.jsonl`、B: `runB/records.jsonl`・`sketch_errors.jsonl`、C: `runC/records.jsonl`、構造化欄: `runF/`（6題）・`runF2/`（28題）、費用の台帳: `spend.jsonl`）。
- 台帳の行: `2026-11-10-flagmeas-*`。
