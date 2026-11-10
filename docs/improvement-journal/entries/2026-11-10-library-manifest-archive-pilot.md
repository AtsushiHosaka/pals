# ライブラリのmanifest化と Mathlib Archive の棚卸し（2026-11-10）

- 指標: 成功率の土台（外部形式化の再利用でカバーする分野を増やす）。時間・費用は対象外。
- 仮説: 外部ライブラリの対応をmanifestの宣言にすれば、次のライブラリは設定だけで足せる。プロジェクトが既に固定しているMathlibの `Archive/`・`Counterexamples/` は、追加の取得なしに、既定プロファイルで棚卸しできる。
- 変更: pals-agent [PR #102](https://github.com/AtsushiHosaka/pals-agent/pull/102)。manifestとローダー、プロファイルの導出（旧定数は削除、固定値とのテストで同一を確認）、汎用の信頼語、索引ツール、`mathlib-archive` のmanifestと索引、`lean.frontier_duplicate_definition` ほか3コードの分類。
- 測定の条件: モデル呼び出し0回、費用0。Lean `v4.32.0-rc1`、Mathlib `8b62164`。ビルド済みのメインcheckoutを読み取りのみで使い、出力はscratch（削除済み）。Leanは常に1プロセス。他セッションの負荷が高く（load average 14〜21）、時間は競合込み。
- 結果: 113／113ファイルがコンパイル成功（エラー0、`sorry` 0）。合計267.1秒、1ファイル最大7.3秒、最大常駐3.29 GB、成果物60.6 MB。theorem 1,378件（Lean環境の実体）の公理は標準の3つだけで、`sorryAx` は0。字句の宣言は1,440、theorem／lemma 1,121。ただし110ファイル中69ファイルが独自の定義を持ち、「Mathlib定数のみ」の文は少ない。100選のうち Archive にあるのは15項目、1000+は7項目。詳細は[試作の記録](../../external-library-pilot-2026-11-10.md)。
- 判断: manifest方式を採用（既定の挙動とdigestは不変）。Archive は取り込めるが、カタログへは追加しない（拡張の停止中）。
- 限界・未確認: 検証器の実経路での再検証、文の切り出しコンパイル、自然言語との忠実性、他ライブラリ。`tests/integration` は誤って全体実行に含め、短時間の Lean が数回起動した（失敗、環境起因）。
- 失敗の記録: 失敗分類コードに該当する失敗はなし（コンパイル失敗0）。
- 次にやること: 設計メモ（前提検索、ライブラリ選択、容量）のうち、費用0の recall@k から測る。次の候補は Compfiles、MIL＋formalising-mathematics-notes、cslib（所有者の承認が要る）。
- 出典: pals-agent PR #102、[試作の記録](../../external-library-pilot-2026-11-10.md)、台帳 `2026-11-10-mathlib-archive-compile`。
