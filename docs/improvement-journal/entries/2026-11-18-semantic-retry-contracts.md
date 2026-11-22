# 意味審査後の作り直しで元の設定と期限を保持する

対象は[#382](https://github.com/AtsushiHosaka/pals/issues/382)。回答なしの終端を減らす既存の作り直し機能について、元の推論量を新jobに保持し、元のadmission期限を延長しないようにした。[API PR #124](https://github.com/AtsushiHosaka/pals-api/pull/124)を、正規本番用source `a3191b4`から準備した。

実PostgreSQLの新規8回帰では、旧版4件失敗から修正版8件成功へ変わった。正規workflowと同じ24ファイルのローカル実行は386件成功した。別の広い66件では旧版19件、修正版15件が失敗し、対象外の既存15件を保持した。これらはjob終端をfixtureで準備した実装境界の検査で、生成の成功率・数学的正しさ・本番性能には換算しない。

既存サービスを再利用し、専用DBは削除した。新規有料呼出・本番設定変更は0件。flagは既定offのままで、exact CIと独立レビューを終えてから本番用候補へ渡す。定量精度の受け入れは未完了である。

出典: [今回の実装候補](../../382-answer-quality-candidate-2026-11-18.md)、API PR #124内の検証note。

追記: exact CI初回は386件中385件成功、既存の別process終了5秒timeoutが1件失敗した。旧baselineでも同じ失敗を再現し、sourceとgateを変えずfailed-jobを一度だけ再確認中である。環境負荷という原因は未確定。

追記: failed-jobの再確認も同じ既存signal timeoutで失敗した。exact CIは未合格で、追加rerunを停止した。元sourceでも起きる失敗だが、実行区間を分ける原因診断が必要である。

追記: 診断追加後の最終head `96b58766739bff793f2ebf41c11f28c62237f5a1`は、正規PR CI `44255020572`で389件成功・失敗/error/skipなしとなった。appとworkflowは最初の実装headから不変で、旧timeoutの原因は未確定のまま保持する。本番担当へexact sourceを渡したが、flag有効化と本番受け入れは未確認である。
