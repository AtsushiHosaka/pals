# 固定QA原本から台帳候補を再生成する

`import_fixed_qa.py` は、[Issue216](https://github.com/AtsushiHosaka/pals/issues/216) の評価と台帳をつなぐ限定CLIです。既存のgrounded-rationaleとsemantic-priorityの2schemaを扱い、固定4入力×2arm、各3回・24QAから20列・8行のCSVを作ります。生成精度や独立した24問の評価へ読み替えません。

担当チャットは `codex://threads/01a1a6ef-927b-7d72-b689-5c442ada7af7`、実装記録は `codex://threads/01a1a6f1-392e-7841-9b79-4b3874381adf` です。基準は親PR243の `799bc1b6e2d2cf12dd5a84fd1472c25ad3cdb337` とrootが承認したWORKING契約です。台帳本体・README・グラフは編集しません。

## 信頼するものと検査するもの

意味の正誤は人手で確定したadjudicationを入力とし、CLIは採点しません。承認と拒否の回数、厳格な意味成功、根拠形式の完備性を分けます。正例に批判がない場合の根拠形式はNAで、0%や100%にはしません。新schemaの全判定に対する結論証拠も別の指標です。既存のschema別notesはこの2つの歴史群の記録を再現するためのもので、新しい候補の採用を自動判断しません。

private directoryと各原本は実行者が所有し、directoryは0700、ファイルは0600相当以下、通常ファイルである必要があります。symlinkは拒否します。prereg/outcomes/adjudicationのSHA256と人手確定の明示確認が必須です。新adjudication内のprereg/outcomes hashも照合します。旧adjudicationにはその欄がないため、外部指定hashが対応を固定します。

preregと保存済み入力・baseline/candidate source・harnessのbytes、24上限・順序・各cell3回・固有call/provider ID・raw envelopeと解析結果・providerのmodel/reasoning/output設定・usage・cost reserve・保存済みverdict/rationaleを検査します。既存2群のraw responseは prompt_cache_retention=24h と service_tier=default に明示限定し、保持表記の欠損や別TTLを拒否します。usageはrawとの対応を確認し、cached/cache-write/reasoningも欠ければ拒否します。欠損を0へ埋めません。観測したreserveはpreregの全入力0.25・出力0.50 USD/百万tokenの予算用計算で、請求額やcache保持の料金対応とは区別します。

question/Lean/prompt/corpusのhashは、hash固定したprereg内のpinとして検査します。private Pythonを実行せず、promptの再描画・Leanの再compileはしません。公開sourceはcommit固定GitHub reportとPRのURL形式を検査します。URL先の内容を通信で取りに行く検査や、人手採点の正しさの証明ではありません。

CSVへ出す文字列は既定の集計文と検査済みの公開sourceだけです。質問・回答・rationale・response ID・秘密・ローカルpathを転記する自由記述欄は設けません。エラーにも原本の値を出しません。

## 明示dry-runと新規出力

追加パッケージ・モデル・AWS・DBは不要です。private directoryには `predeclaration.json`、`outcomes.json`、`adjudication.json`、入力4ファイル、baseline/candidate/benchmarkの3source、24件のraw/parsed provider receiptとreviewが必要です。引数の値は実原本と確認済みの公開sourceを指定します。

```bash
python3 docs/quality-ledger/import_fixed_qa.py \
  --private-dir "$FIXED_QA_PRIVATE_DIR" \
  --prereg-sha256 "$FIXED_QA_PREREG_SHA" \
  --outcomes-sha256 "$FIXED_QA_OUTCOMES_SHA" \
  --adjudication-sha256 "$FIXED_QA_ADJUDICATION_SHA" \
  --confirm-human-adjudication \
  --source-report "$FIXED_QA_PUBLIC_REPORT_URL" \
  --source-pr "$FIXED_QA_PUBLIC_PR_URL" \
  --environment 'local macOS' --dry-run
```

出力時は `--dry-run` の代わりに `--output /path/to/new-proposal.csv` を明示します。完全な候補を既存の台帳検査に通し、0600の新規ファイルだけを排他的に公開します。既存ファイルやsymlinkを上書きせず、appendの機能はありません。台帳への取り込みとグラフ再生成はrootが候補を確認してから行います。

`--compare-ledger /path/to/reference.csv` は8行のIDを探し、全20field値を照合する再生成モードです。CSVの改行・引用方法が違ってもfieldが同じなら一致します。`--dedupe-ledger /path/to/current.csv` は新規候補用で、既存IDと重なると拒否します。両方は同時指定できません。いずれも参照台帳は読み取り専用です。

## 実原本の再生成と回帰

Git外の実原本2群を変更せずに読み、rootの既存16行snapshotに対して各8行・全20field一致を確認しました。生成CSVのSHA256はgrounded群 `991b81791731511fefadd17d708cd804e0e737ab2cf2e0310e587cce755aa49d`、semantic群 `9ae5009f8e5b4318f25981c8de329cb0498c7c2c6bacd125f7dd5a175fa34bdb` です。原本や生成CSVはcommitしません。

専用testは明示的な合成原本で、実importerを通して両schema、改変、採点binding、usage欠損、重複、既存CSV全field比較、出力の排他と原文非流出を検証します。fixtureのprivate Pythonは実行したら例外になる内容で、読み取りだけで処理できることも確認します。これはモデルの評価ではないため、unit/CI件数を品質台帳へ足しません。

2026-11-05の最終検証では、専用14件と既存audit8件の22件、変更2sourceのRuff、diff検査が通過しました。raw responseだけでなくattempt予約receiptも24件と照合し、未報告の25件目や欠損を拒否します。実2群はdry-runと明示した0600の新規CSV出力でも全field一致を確認しています。独立レビューで見つかった保持表記の検査不足を修正し、両schemaでmissing/別TTLの負例も確認しました。独立follow-upはこの記録時点で未了です。

```bash
python3 -m unittest discover -s docs/quality-ledger -p 'test_*.py'
```

既存2群への接続と候補生成が対象です。本番評価の自動収集、provider usageの真正性、人手による数学判断、将来の異なるschema、台帳への自動appendはこのCLIだけでは完了しません。
