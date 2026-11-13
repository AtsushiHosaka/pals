# T2 cheap-first を次のリリースで有効にする手順書（2026-11-14）

対象: pals-agent#129（マージ済み、全フラグ既定 off）。根拠: [t2-cheap-first](improvement-journal/entries/2026-11-14-t2-cheap-first.md)、[t2-30s-late-items-and-cheap-patch](improvement-journal/entries/2026-11-14-t2-30s-late-items-and-cheap-patch.md)、[t2-failure-classes-and-repair-hints](improvement-journal/entries/2026-11-14-t2-failure-classes-and-repair-hints.md)。この手順書は有効にする判断を代行しません。有効にするのは、リリース担当が前提（下の「事前に確かめること」）を確かめてからです。

## 1. 有効にするフラグと値（ワーカーの環境変数。置き場所は配備担当が決める）
`true` にする: `PALS_T2_CHEAP_FIRST_ENABLED`、`PALS_T2_SOURCE_HYGIENE_ENABLED`、`PALS_T2_NAME_SAFETY_ENABLED`、`PALS_T2_PATCH_REPAIR_ENABLED`、`PALS_T2_NO_DRAFT_ENABLED`、`PALS_T2_PARALLEL_EXPLANATION_ENABLED`、`PALS_T2_PARALLEL_REVIEW_ENABLED`。
`false`（または未設定）のままにする: `PALS_T2_HETERO_RACE_ENABLED`、`PALS_T2_PARALLEL_CANDIDATES_ENABLED`、`PALS_T2_NO_SKETCH_ENABLED`、`PALS_FAST_FIRST_ATTEMPT_ENABLED`（別の機能で、cheap-first との組合せは測っていない）。`PALS_T2_CHEAP_PATCH_ROUNDS` と `PALS_T2_REPAIR_HINTS_ENABLED` は main にない（不採用）。
- 値は `true` か `false` だけ。ほかの値はパイプラインの構築時に例外になり、起動で止まる（モデルの費用が出る前）。
- 前提の設定: 本番の検証は `verification_mode="api_reconcile"`（既定）。Terra の役割の強度の束縛が有効であること。Luna（release モデル）は常に low なので cheap-first は何も変えない。依頼が effort を選んだときは、その選択が優先される。

## 2. 期待される効果（実 Terra、worker の carry 経路、常駐 Lean、API 往復は固定 1.1 秒の代用、1回ずつ）
| 指標 | 前（異種レース等） | cheap-first＋整形 |
|---|---|---|
| dev_unseen 20題、回答完成が30秒以内 | 9/20 | 12〜13/20 |
| 同、初回成功 | 9〜10/20 | 13〜14/20 |
| 同、1問の費用 | US$0.032〜0.036 | US$0.012〜0.016 |
| tuning 14題、30秒以内 / p50 / p90 / 費用 | 8/14、24.4 / 79.1 秒、US$0.037 | 13/14、18.9 / 27.8 秒、US$0.020 |
ばらつきが大きい（同じ設定の繰り返しで 13 と 12、1〜2題）。30秒の目標（16/20、14/20）には届いていない。

## 3. 危険と監視する指標
- 整形は、提出する header を書き換える（`import Mathlib.*` を `import Mathlib` に、`𝓝` などの `open` を足す）。formal statement を持つ依頼では何もしない。本番の検証器との結合は、凍結した方針のテストでしか確認していない → 監視: `lean.formal_harness_mismatch`、`lean.statement_mismatch` の件数（有効化前後で増えないこと）。
- 名前の案内の文が変わる（既存フラグの背後）。cheap-first の初回は候補0のスタイル指示も足す。→ 監視: 初回の成功率（有効前の値と比べる）。
- 失敗した候補ごとに解説・審査が先行して走る（失敗1題で最大10回、Luna low）。→ 監視: 1ジョブあたりの費用の p50 / p90、解説・審査の呼び出し回数。
- 回答完成の p50 / p90、修復回数、却下率（解説の審査・意味の審査）。本物の API の往復と待ち行列の影響は未測定。
- 戻す基準（提案、リリース担当が決める）: 上の2種の件数が有効化前より明らかに増える、または1ジョブの費用が US$0.03 を超える。

## 4. 元に戻す方法
7つのフラグを `false`（または削除）にして、ワーカーを再起動する。状態の移行はない。戻した後は、従来の経路（異種レースなし、patch なし）に戻る。

## 5. 事前に確かめること / 有効にした後の測定
- 事前（未実施）: 本物の API での小さな回帰（カナリア）。本番の検証器に対する、整形後の提出の確認（`lean.statement_mismatch` が出ないこと）。
- 有効にした後: 同じ dev_unseen 20題と tuning 14題を、本番構成で1回ずつ（各 US$1 以下）。dev_unseen の取り出しは pals-agent の `scripts/eval/extract_dev_split.py`（`split == "dev_unseen"` だけ。held_out は読まない・実行しない）。本物の API・SQS を叩く駆動は未作成。既存の `scripts/eval/run_hetero_api_sim.py` は往復を固定値で代用するので、本番構成の測定には使えない。作る必要がある。

## 6. 30秒に届かない残りの題: いまの構成で届かない理由と、必要なもの（測定に基づく、10行）
1. dev_unseen の4回（80題・回）: 30秒以内 60%、1回の修復で通る 17.5%（31〜41秒）、修復2回以上 19%（中央値126秒）、初回で通るが遅い 4%。目標の 16/20（64/80）は、1回修復をすべて動かしても 62/80（77.5%）で届かない。
2. 初回成功の経路の時間: low の prove 中央値 8.5 秒（p90 16〜18 秒）、検証の compile 0.3〜2.6 秒、検証後の解説・審査の待ち 中央値 6.5 秒。モデルの応答時間が半分を占める。
3. 1回修復の題: 初回の失敗を知るまで約12秒、patch（medium で中央値 20.1 秒、low で 7.7 秒）、解説・審査 6.5 秒。low の patch でも 33.5 秒で30秒を超える。残りは解説・審査の待ち（修復後のコードが確定してからしか始められない）。
4. 修復2回以上の題は、ほぼ同じ4題（`arctan-lipschitz`、`dependent-consecutive-triples`、`exp-two-x-derivative`、`reverse-triangle-inequality`）。どの設定でも初回で落ち、patch の成功は題で決まる（0/4）。失敗の種類ごとの指示では動かない（15/30 対 14/30）。モデルの力の限界。
5. 修復モデルは、残りの goal や名前を見られない（サニタイズの設計。注入対策）。これが patch の力を抑えている可能性があるが、未検証。
6. 候補を2本並べる（異種レース）と20秒以内は増える（10〜11 対 7〜9）が、30秒以内は変わらず、費用は1.5〜1.8倍。
7. 届かせるのに要るもの（順に、未実施）: (a) 難しい題を事前に判別し、初回から強い effort にする（信号が要る。`routine` は未配線）。(b) 解説・審査の待ちを短くする（解説の生成が 6.2 秒、p90 11.6 秒。担当は解説・審査の側）。(c) 修復モデルに goal や名前を見せる設計の見直し（注入の観点のレビューが要る）。(d) 実 API の往復の実測（固定 1.1 秒の代用）。
8. 修復の構造: patch が2回続けて失敗すると、route → draft → sketch → prove の全修復に入り、1回に 50〜90 秒かかる。2回目の patch で止めて、直接の再生成に切り替える案は、未測定。
9. 以上は、dev_unseen 20題と tuning 14題の、n が小さい測定に基づく（1回ずつ、1〜2題の差は区別できない）。
