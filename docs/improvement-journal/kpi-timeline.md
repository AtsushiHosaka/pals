# 指標の推移（時間・成功率・費用）

1行が1つの測定です。条件が違う行どうしは、数字を並べても改善率になりません。「条件」の列を必ず読んでください。新しい測定は末尾に足します（追記のみ）。費用の列は、合計と1枚あたりが混ざっていたため、各セルに単位を書きました（2026-11-09 に訂正）。詳細は各エントリ、数字の正本は[品質台帳](../quality-ledger/README.md)です。

| 日付 | 何を測ったか | 条件 | 成功 | 1枚あたりの時間 | 費用（推計。合計か1枚あたりかを各セルに明記） | エントリ |
|---|---|---|---:|---:|---:|---|
| 2026-11-03 | Mathlib命題ヒントの有無（Luna low、各腕12枚） | Luna low、ヒントあり/なし | 12枚中4枚でヒントのみ成功 | 未集計 | Luna 36実行の合計 0.265ドル（約0.0074ドル/実行） | [mathlib-statement-hints](entries/2026-11-03-mathlib-statement-hints.md) |
| 2026-11-03 | 同ヒントの有無（Terra、新しい12枚） | Terra、ヒントあり/なし | 両群とも11/12（差なし） | 未集計 | Terra 30実行の合計 1.861ドル（ベース腕の12実行は0.596ドル、約0.0497ドル/実行） | 同上 |
| 2026-11-07 | モデル比較・24枚（事前登録） | 修復上限6、各カード1回 | Luna low 12/24、Terra low 16/24、**Terra medium 21/24** | Terra low 100秒、**Terra medium 212秒** | 約0.05ドル/枚（Terra medium、推計） | [model-call-latency](entries/2026-11-07-model-call-latency-preregistered.md) |
| 2026-11-08 | 近道3種（呼び出しと route 選択の削減）、同じ12枚 | Terra medium、修復上限6、各1回 | 10/12（ベースも10/12） | 176→173秒（−2%、偶然の範囲） | 12枚で約1.16ドル（ベース腕。約0.10ドル/枚） | [pipeline-shortcuts](entries/2026-11-08-pipeline-shortcuts.md) |
| 2026-11-08 | Recipe 証明の few-shot、同じ12枚 | 同上 | 10/12（変化なし） | 176→174秒、初回Sketch通過 6/12のまま | 未集計 | [recipe-fewshot](entries/2026-11-08-recipe-fewshot.md) |
| 2026-11-08 | 説明の先行生成フラグ（最大19ペア） | Luna、意味審査→説明書き込みの区間のみ | — | 差（off−on）+1.0秒、95%区間[−2.1, +3.7]秒 | 3ペアの合計 約0.019ドル | [speculative-explanation](entries/2026-11-08-speculative-explanation.md) |
| 2026-11-08 | 機械修復（Sketch失敗の決定的修復）、同じ12枚 | Terra medium、修復上限6 | 10/12（変化なし） | 176→186秒（偶然の範囲）、初回に使えたSketch 6→12枚、修復 26→19回 | 12枚で約1.19ドル（全工程、台帳 1.193。約0.10ドル/枚） | [sketch-failure-repair](entries/2026-11-08-sketch-failure-repair.md) |
| 2026-11-08 | 命題の固定（Sketch/修復で命題を書き換え不可に）、同じ12枚 | 同上 | 10/12（変化なし） | 186→172秒（偶然の範囲）、食い違いの試行 14→0、呼び出し 97→82（機械修復のみの腕→命題固定） | 12枚で約1.12ドル（台帳 1.123。約0.09ドル/枚） | 同上 |
| 2026-11-08 | 保留24枚（機械修復＋命題固定の1腕） | Terra medium、修復上限6、各1回 | 23/24 | 平均113.5秒、中央値87.6秒 | 24枚で約1.25ドル（台帳 1.253。約0.05ドル/枚） | 同上 |
| 2026-11-08 | 本番の x² 連続性、High（各 n=1、seq27 配備後） | リリース担当の4件（High 2件、Medium 2件）、各 n=1 | — | High 2件: 138秒・143秒（原因は語彙表の取りこぼし。テンプレートに外れ、Sketch が49.7秒・55.4秒）。Medium 2件は別の事例: 52秒（テンプレートに当たる）、126秒（判定の問いで、意図的に外した。Sketch 33.9秒）。2026-11-09 に訂正 | 未集計 | [x-squared-structure-recognition](entries/2026-11-08-x-squared-structure-recognition.md) |
| 2026-11-09 | x² の短絡と固定説明（seq28 の本番実測 英語48.4秒・日本語68.6秒、見込みは算術のみ・実モデルなし） | Terra High、各 n=1 | — | 英語 48→約19秒、日本語 69→約22秒（見込み） | 未集計 | [x-squared-chat-fastpath-fixed-explanation](entries/2026-11-09-x-squared-chat-fastpath-fixed-explanation.md) |
| 2026-11-09 | 同日のベース腕（保留24枚、機械修復・命題固定なし）との対比較 | Terra medium、修復上限6、各1回。ベースは11-09深夜、処理あり腕は11-08夜の実行 | 23/24（ベースも23/24、差なし） | 164→113秒（−50秒、95%区間[−79, −20]。ただし時間帯・実行中の他作業が交絡し、設計用12枚では差なしのため効果とは断定しない）。修復上限3の机上計算: 成功 21→23/24（区間が0に接する）、149→104秒 | ベース 24枚で約1.37ドル（台帳 1.374、約0.06ドル/枚。上限2.5ドル内）、処理あり 24枚で約1.25ドル | [sketch-failure-repair](entries/2026-11-08-sketch-failure-repair.md)（同日のベース腕の節） |
| 2026-11-09 | スキーム論の易しい命題・腕a（Mathlibのみ）、M01〜M09（中間、予算で停止） | Terra medium、修復上限6、各1回、命題固定＋意味審査、Lean 4.35 | 7/9（上限3では5/9） | 中央値174秒（全実行）、113秒（成功のみ） | 9枚の合計 2.87ドル（推計。gpt-5.6-terra の単価で、gpt-6.1-terra の単価は未確認）。1枚あたりの中央値 $0.18 | [scheme-theory-frontier-measurement](entries/2026-11-09-scheme-theory-frontier-measurement.md) |
| 2026-11-09 | スキーム論の易しい命題と Frontier の取り込み（最終、上限10ドル）。腕a M01〜M16、腕b M07・M09・M14、腕c F01〜F08（C01・C02は予算のため未実行） | Terra medium、修復上限6、各1回、命題固定＋意味審査、Lean 4.35。ロード中央値8〜12 | 腕a 12/16（上限3では10/16、Wilson [0.51, 0.90]）、腕b 1/3、腕c 3/8（[0.14, 0.69]） | 全実行の中央値 腕a 255秒・腕b 747秒・腕c 343秒（基準120秒を超過）。成功のみ 144秒・198秒・40秒 | 合計 9.95ドル（試運転0.12ドル含む。推計: gpt-5.6-terra の単価で、gpt-6.1-terra の単価は未確認。上限10ドルとの比較は概算）。失敗が費用の68% | [scheme-theory-frontier-measurement-final](entries/2026-11-09-scheme-theory-frontier-measurement-final.md) |
| 2026-11-09 | スキーム論の易しい命題と Frontier の取り込み（第2予算4ドル、手当て2つの後）。C01・C02（腕a）、腕d F01〜F08（早期打ち切り＋範囲拡張）、c2 F01〜F03（同条件の繰り返し）。改善率は作らない | Terra medium、修復上限6、各1回、命題固定＋意味審査、Lean 4.35。ロード中央値10〜13 | 腕a合算 12/18（上限3では10/18、Wilson [0.44, 0.84]）、腕d 5/8（[0.31, 0.86]）、c2 1/3。成功への効果は保留 | 全実行の中央値 腕a合算309秒、腕d 80秒（失敗は360〜430秒）、c2（完了3回）41秒 | 合計 4.02ドル（推計、同じ単価の前提。上限4.0を0.02ドル超過）。腕d 1.75ドル、c2 1.07ドル、C01・C02 1.20ドル（いずれも合計） | [scheme-theory-frontier-measurement-second-budget](entries/2026-11-09-scheme-theory-frontier-measurement-second-budget.md) |
| 2026-11-09 | 命題ごとの最小 import（腕 c カード、実機。Mathlib のみ16枚 + Frontier を使う6枚） | Lean 4.35、`import Mathlib` と最小 import、各3回・温かい、他の作業が動く機械（1分ロード 7〜20）。モデル呼び出しなし | 文が通る Mathlib のみ 15/16 と Frontier 4/6（`import Mathlib` は全て通る。失敗は変数への dot 記法で、全 import に戻す前提） | 5.09→2.37秒（中央値、n=45、カード対の比 0.48）、常駐メモリ 5.8→2.7 GB、読み込み 10,974→3,673〜4,323 モジュール。Frontier の通った4枚: CPU 時間の比 0.47〜0.65、メモリ 6.1→3.0〜3.9 GB（負荷の高い機械、温かい） | 0 | [stacks-import-index](entries/2026-11-09-stacks-import-index.md) |

## 指標の表に入らないエントリ

数字の比較ではないが、経緯の理解に必要な記録です。

| 日付 | 内容 | エントリ |
|---|---|---|
| 2026-11-07 | Lean の時間は elaboration ではなく起動と import が占める（`lake env` の起動だけで0.9〜1.4秒） | [lean-skip-verification-phase0](entries/2026-11-07-lean-skip-verification-phase0.md) |
| 2026-11-07 | `∀`/`∃` による Luna 失敗の予測は根拠が弱い（n=12、補正後 p≈0.06） | [difficulty-routing-offline-check](entries/2026-11-07-difficulty-routing-offline-check.md) |
| 2026-11-08 | 代数幾何の取り込み調査（Mathlib定数のみの11文のうち7文が通る。verified≠命題の忠実性） | [algebraic-geometry-intake](entries/2026-11-08-algebraic-geometry-intake.md) |
| 2026-11-08 | x² の検証結果キャッシュ（ローカルで約18秒→約1.3ms。x² 専用・未配備） | [x-squared-verifier-cache](entries/2026-11-08-x-squared-verifier-cache.md) |
| 2026-11-08 | 段別計測（#77）と注入対策（#78）の実装とレビュー対応 | [step-timing-and-injection-defense](entries/2026-11-08-step-timing-and-injection-defense.md) |
| 2026-11-08 | 本番の障害（seq27 cutover の停止、01:19〜08:19 JST） | [production-incident-seq27-halt](entries/2026-11-08-production-incident-seq27-halt.md) |
| 2026-11-09 | x² の検証結果キャッシュの有効化の段取り（検証器 image は必ず変わる。toolchain hash の導出は未確認） | [verifier-cache-enablement-plan](entries/2026-11-09-verifier-cache-enablement-plan.md) |
| 2026-11-10 | 訂正: 「本番の修復上限は3」は main の既定で、本番（seq29、配備物の読み取り）は6の見込み。コンテナ env は未確認 | [prod-repair-limit-correction](entries/2026-11-10-prod-repair-limit-correction.md) |
| 2026-11-10 | 机上試算: 時間・費用が失敗実行にどう偏るか、修復上限・早期停止の反事実（モデル呼び出し0回） | [offline-savings-analysis](entries/2026-11-10-offline-savings-analysis.md) |
| 2026-11-10 | 早期停止の専用終了理由（#91、既定 off）。既存の停止は API に拒否され、本番で働くのは harness 不一致だけ | [early-stop-terminal-reason](entries/2026-11-10-early-stop-terminal-reason.md) |
| 2026-11-10 | import plan を検証器へ接続（#92、既定 off、実モデル測定なし） | [import-plan-verifier](entries/2026-11-10-import-plan-verifier.md) |
| 2026-11-10 | プロンプト4フラグの初回実測（Terra medium、tuning 28題/12題、US$2.33）: prefix キャッシュは hit 0（共通 prefix の対照も0）、束ねた腕の初回コンパイルは 20/28 同数・Tier 2 の最終成功は 11/12 同数で、検出できる差なし。出力は約15%短く生成は約3秒速いが、full import で Lean 検査が約2秒遅く、合計時間は同等。構造化欄は28/28で読めた | [prompt-flag-first-measurement](entries/2026-11-10-prompt-flag-first-measurement.md) |
