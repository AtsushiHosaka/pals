# seq30再準備時のbuild履歴確認失敗（2026-11-17）

狙いは、期限切れTLSを更新した同候補f20・親3b663576・infra3b31597で、有料送信前の実依存先を再確認することだった。事前登録した比較実験ではなく、release前提の技術確認である。

最初の正規reprepareは、build receiptのlive history確認でlocal_dependency_command_failed、returncode1となった。主担当はWeb/native両参照が削除済みであることを実読で確認した。削除原因は未確定で、過去のPASSやコピーしたreceiptを代用しなかった。技術bundle1件の0/1として失敗を保持する。

同じsource・archive・builderの正規rebuildで新しい実provenanceを得た後、正規reprepareが成功し、canary2588msでverifiedとなった。これは前提回復の経過で、当初失敗を成功へ変更せず、paid試行数にも加算しない。判断は新provenanceを採用して次の実取得へ進むことで、製品受け入れは別測定とした。

失敗時のsubject・env・71 calls/255446μUSDは保持した。回復全体の費用総額と所要時間は未測定で、数学の精度や改善率は示さない。根拠hashは[検証環境回復の記録](../../seq30-validation-recovery-2026-11-17.md)を参照。品質台帳IDは2026-11-17-seq30-provenance-history-refusal。

仮説に当たる見通しは、実ビルドの証拠が読み取れれば同じ構成の準備を再開できる、というものだった。これは実施後の説明であり、履歴削除の原因や復旧所要時間についての仮説検証ではない。
