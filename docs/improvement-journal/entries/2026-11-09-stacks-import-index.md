# Stacks の import 索引と、命題ごとの最小 import （2026-11-09）

- 指標: 時間（検証1回の Lean の import と elaboration）、メモリ。成功率と費用には触れない（モデル呼び出しなし、費用 0）。
- 仮説: 依頼の命題が使う定数から、定義モジュールと import の辺だけで「必要最小の import」を求められれば、`import Mathlib` + Frontier のハブより少ないモジュールを読み込んで同じ文が通り、検証1回の import が短く、軽くなる。Frontier 全体（62,528 モジュール）を読み込まずに済む。
- 変更（PR・コミット・フラグ、既定のオン/オフ）: pals-agent PR #86（`tools/stacks_index/` に新規ファイルのみ。コミット f554132）。PR #72 の宣言索引（`decl.module` で宣言→モジュールは既にあった）に、import の辺、Mathlib・依存・Lean の層、同名の二重定義の記録、`ImportIndex.plan`、版の固定（`source_digest`、`--verify`、`--diff`）を足した。Frontier は `--include-frontier` のときだけ（既定オフ）。本番・検証器には未接続。
- 測定の条件:
  - 索引: Stacks `5ed82d1`、Mathlib `56a0058`、Lean 4.35.0。4 並列、`nice`。他のセッションが動く機械（1分ロード 7〜20）。
  - 実機（Mathlib のみの16枚）: 腕 c の事前登録カード M01〜M14、M16、C02（`docs/scheme-theory-measurement-cards-2026-11-09.json`）。`import Mathlib` と最小 import で、`sorry` で証明を省いた文を `lean` にかけ、各3回、温かい状態。`#check @t`（`pp.all`）で elaborate 結果を比べ、違う場合は完全 import の環境で defeq を検査。
  - 標本（Lean を動かさない）: Frontier の宣言の文を、代数幾何 562 件（300 ファイル）と Frontier 全体 749 件（400 ファイル）、無作為。
- 結果:

| 項目 | `import Mathlib` | 最小 import |
|---|---:|---:|
| 文が通る（Mathlib のみ16枚） | 16/16 | 15/16（M13 は instance `Zero ↥(Spec R)` が足りず失敗） |
| 通った15枚の elaborate 結果 | — | 10枚は完全一致、5枚は instance の経路だけ違い defeq |
| 実時間の中央値（n=45） | 5.09 秒（p90 6.59） | 2.37 秒（p90 4.18）、カード対の比の中央値 0.48 |
| 最大常駐メモリの中央値 | 5.8 GB | 2.7 GB |
| 読み込むモジュール | 10,974 | 3,673〜4,323 |

  読み込むモジュール数の標本（`import Mathlib` + Frontier 全体は 74,383）: 代数幾何の文の中央値 8,043（p90 17,038）、Frontier のうち中央値 806（p90 5,629）。宣言の所属モジュール自身の import は中央値 13,372 / Stacks 1,974。腕 c のカード26枚は 3,673〜8,119（Stacks 0〜913）で、26枚の文に要る Stacks モジュールの和は 969（カード自身の import の和は 982、腕 c の B は 3,748）。一方、代数幾何の文 562 件の和は 26,660（Frontier の43%）で、任意の依頼を受けるなら B では足りない。索引: 74,764 モジュール、508,882 辺、947,561 宣言、232 MB、構築 58 秒・0.87 GB。精度の自己検査: 文の定数のうち閉包内に解決 91.8%（Frontier、57,543 個）、閉包外 1.05%、未解決 7.2%。同名の二重定義は Frontier どうしで 113（112 は互いを import しない組）、Stacks と Mathlib の間は 0。

  実時間と常駐メモリは、Mathlib のみの12種類の import（1,011〜10,974 モジュール）で、実時間 ≈ 0.45 + 0.00045·N 秒、メモリ ≈ 0.52 MB·N だった（N は読み込むモジュール数）。
- 判断: PR #86 を出す（本番への接続は未決定）。最小 import は「提案」として扱い、通らなければ全 import に戻す前提にする。M13 のような instance の不足は、字句解析では見えない。
- 費用: 0（モデル呼び出しなし）。
- 限界・未確認:
  - **Frontier の import の時間とメモリは測れていない。** Frontier のコードは AI 生成で人手未レビューのため、このセッションの権限判定がビルドを止めた。Frontier の数字はモジュール数のみで、時間とメモリは上の式と pals-agent #74 の測定（3,748 モジュールで +1 秒、+1.6 GB）からの見込み。
  - 「冷たい」import は測れていない（ページキャッシュを捨てるには管理者権限が要る）。
  - 腕 c の B（3,748）は再現できなかった（私の再構成は cap=200 で ハブ 481〜495 / 2,277〜2,986 モジュール、事前登録は 487 / 2,393）。比較は事前登録の数字そのものとした。
  - 「`open N` の N を宣言する信頼の高いモジュールを足す」規則と「曖昧な dot 記法の末尾は閉包が最小のものを取る」規則は、カードで失敗や過大な結果を見たあとに足した。事前登録ではなく、16枚の通過 15/16 は過学習を含みうる。
  - 16枚は Mathlib のみで、Frontier の定義を使う F 群（8枚）は実機で未検査。
  - 実時間は同じ機械で他の作業が動いていた条件で、並列度と負荷が揃っていない。
- 次にやること: 権限の判断がつけば、Frontier の小さな閉包（F04、F05、F07、C01、F02 の約 90 モジュール）をビルドして、最小 import の実機の通過と時間・メモリを測る。pals-agent の検証器に `plan` を接続する（通らなければ全 import に戻す経路つき）かどうかの決定。腕 c のビルド集合 B をカード以外の依頼に広げたときの和（26,660 まで増える）の扱い。
- 出典: pals-agent PR #86（`tools/stacks_index/README.md`、`measure_imports.py`、`validate_imports.py`）。関連: pals-agent PR #72、#74、親リポジトリの `docs/scheme-theory-measurement-*-2026-11-09.*`（PR #307）、改善ジャーナルの `2026-11-09-scheme-theory-frontier-measurement.md`。生データはこの機械の作業用ディレクトリ（`exp/m_cards_result.json`、`exp/sweep_result.json`、`exp/measure_*.json`）。
