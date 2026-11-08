# 指標の推移（時間・成功率・費用）

1行が1つの測定です。条件が違う行どうしは、数字を並べても改善率になりません。「条件」の列を必ず読んでください。新しい測定は末尾に足します（追記のみ）。詳細は各エントリ、数字の正本は[品質台帳](../quality-ledger/README.md)です。

| 日付 | 何を測ったか | 条件 | 成功 | 1枚あたりの時間 | 1枚あたりの費用 | エントリ |
|---|---|---|---:|---:|---:|---|
| 2026-11-03 | Mathlib命題ヒントの有無（Luna low、各腕12枚） | Luna low、ヒントあり/なし | 12枚中4枚でヒントのみ成功 | 未集計 | Luna 36実行の合計 0.265ドル（約0.0074ドル/実行） | [mathlib-statement-hints](entries/2026-11-03-mathlib-statement-hints.md) |
| 2026-11-03 | 同ヒントの有無（Terra、新しい12枚） | Terra、ヒントあり/なし | 両群とも11/12（差なし） | 未集計 | Terra 30実行の合計 1.861ドル（ベース腕の12実行は0.596ドル、約0.0497ドル/実行） | 同上 |
| 2026-11-07 | モデル比較・24枚（事前登録） | 修復上限6、各カード1回 | Luna low 12/24、Terra low 16/24、**Terra medium 21/24** | Terra low 100秒、**Terra medium 212秒** | Terra medium 約0.05ドル | [model-call-latency](entries/2026-11-07-model-call-latency-preregistered.md) |
| 2026-11-08 | 近道3種（呼び出しと route 選択の削減）、同じ12枚 | Terra medium、修復上限6、各1回 | 10/12（ベースも10/12） | 176→173秒（−2%、偶然の範囲） | 約1.16ドル（ベース12枚） | [pipeline-shortcuts](entries/2026-11-08-pipeline-shortcuts.md) |
| 2026-11-08 | Recipe 証明の few-shot、同じ12枚 | 同上 | 10/12（変化なし） | 176→174秒、初回Sketch通過 6/12のまま | 未集計 | [recipe-fewshot](entries/2026-11-08-recipe-fewshot.md) |
| 2026-11-08 | 説明の先行生成フラグ（最大19ペア） | Luna、意味審査→説明書き込みの区間のみ | — | 差（off−on）+1.0秒、95%区間[−2.1, +3.7]秒 | 約0.019ドル（3ペア時） | [speculative-explanation](entries/2026-11-08-speculative-explanation.md) |
| 2026-11-08 | 機械修復（Sketch失敗の決定的修復）、同じ12枚 | Terra medium、修復上限6 | 10/12（変化なし） | 176→186秒（偶然の範囲）、初回に使えたSketch 6→12枚、修復 26→19回 | 約1.19ドル（全工程） | [sketch-failure-repair](entries/2026-11-08-sketch-failure-repair.md) |
| 2026-11-08 | 命題の固定（Sketch/修復で命題を書き換え不可に）、同じ12枚 | 同上 | 10/12（変化なし） | 186→172秒（偶然の範囲）、食い違いの試行 14→0、呼び出し 97→82 | 約1.2ドル | 同上 |
| 2026-11-08 | 保留24枚（機械修復＋命題固定の1腕） | Terra medium、修復上限6、各1回 | 23/24 | 平均113.5秒、中央値87.6秒 | 約1.25ドル（24枚） | 同上 |
| 2026-11-08 | 本番の x² 連続性、High（各 n=1、seq27 配備後） | Terra High、リリース担当の4件 | — | 138〜143秒（原因は語彙表の取りこぼし。テンプレートに外れ、Sketch が34〜55秒） | 未集計 | [x-squared-structure-recognition](entries/2026-11-08-x-squared-structure-recognition.md) |
| 2026-11-09 | x² の短絡と固定説明（seq28 の本番実測 英語48.4秒・日本語68.6秒、見込みは算術のみ・実モデルなし） | Terra High、各 n=1 | — | 英語 48→約19秒、日本語 69→約22秒（見込み） | 未集計 | [x-squared-chat-fastpath-fixed-explanation](entries/2026-11-09-x-squared-chat-fastpath-fixed-explanation.md) |
| 2026-11-09 | 同日のベース腕（保留24枚、機械修復・命題固定なし）との対比較 | Terra medium、修復上限6、各1回。ベースは11-09深夜、処理あり腕は11-08夜の実行 | 23/24（ベースも23/24、差なし） | 164→113秒（−50秒、95%区間[−79, −20]。ただし時間帯・実行中の他作業が交絡し、設計用12枚では差なしのため効果とは断定しない）。修復上限3の机上計算: 成功 21→23/24（区間が0に接する）、149→104秒 | ベース約1.37ドル（24枚。上限2.5ドル内）、処理あり約1.25ドル | 同上 |

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
