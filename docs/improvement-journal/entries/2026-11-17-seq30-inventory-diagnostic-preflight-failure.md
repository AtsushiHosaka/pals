# seq30診断CLIの送信前失敗（2026-11-17）

狙いは、restore-checkの固定拒否コードでは不足していた情報を、読み取り専用診断で取得することだった。初回はdiagnostic_refused・closed_diagnostic_failureで停止し、主担当の確認ではhost送信・state作成とも0件だった。技術bundle1件の0/1として保持する。

guard一覧hashへの不要な改行を直したほか、旧凍結validatorの実source pathを使う必要をpure回帰検査で再現し、13be88fcで修正した。旧configやgateを緩和せず、実closureもprovider0で検査した。初回の閉じたコードだけでは最初に失敗した条件を一意に特定できず、分類はunclassifiedとする。

判断は、修正した診断を別の読取bundleで確認すること。元のrestore-check根因を修正したとまでは主張しない。新しいpaid処理は0件、実費総額と全体時間は未測定。後の正常probeでこの初回失敗を成功に変えず、製品・数学の分母にも含めない。

根拠は[診断記録](../../seq30-inventory-diagnostic-2026-11-17.md)、品質台帳IDは2026-11-17-seq30-inventory-diagnostic-preflight-failure。

仮説に当たる狙いは、旧configを変更せず、切り替えの再試行から独立した診断を実行できるか確かめることだった。これは実施後の説明であり、事前登録した比較実験ではない。モデル・修復上限・カード数は対象外である。
