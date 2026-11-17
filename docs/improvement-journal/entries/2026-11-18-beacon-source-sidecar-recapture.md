# 計測beaconのcounter修正と別sidecarによる機能再確認（2026-11-18）

受け入れ確認の成功率を正しく記録するため、通信を止めた計測beaconと、禁止されたアプリwriteのcounterを分けた。元のgateは既存回答の検証・保存・render・reloadを通過後、RUM POST3件による`observer_attempted_mutation`で失敗していた。この失敗は変更せず保持する。

[PR #415](https://github.com/AtsushiHosaka/pals/pull/415)では、正確なWeb originの`/cdn-cgi/rum`と末尾単独`?`の2種類だけをabortしたまま専用counterへ分け、他write拒否・回答・Lean・保存・描画・reloadの検査を維持した。旧sourceと途中のqueryなし限定案では回帰RED、修正後はGREENとなり、途中のsandbox bind失敗も[sourceの検証記録](../../release-acceptance-rum-suppression-2026-11-18.md)に残した。

最終実行source `52ccfc334e97cce5215918eb44d89c62415b241a`のexact CI 2件が成功し、4ファイルをimmutable archiveへ固定した。別sidecarは旧post contractから`runner_sha256`だけを変え、元のplan・seed・failed journal、runtime・model・scenario・source・image・固有の結論条件を維持した。

先に送信した1件だけを再観測し、正規acceptanceとstatus再検証でacceptedを確認した。terminalはanswered、evidenceはlean_verified、runtime 6 roles・実asset 26件・render/reload hashを照合し、attempted mutations 0、抑止RUM 3件、認証POST 1件、product telemetry 0だった。source順序だけの推測ではなく、実runtimeと画面観測を含む別証拠である。

本recaptureの新規有料送信は0件。観測区間を生成時間や#380性能へ換算せず、金額未取得のUSDは空とする。台帳はn=1・成功1、元gate失敗行への重複参照付きで、数学の独立試行へ加えない。元releaseのfailed・停止時間超過・accepted=false、owner解放とcleanupの未完了を維持する。固定policyの追加承認待ちでapply 0という境界も変えない。

[別証拠のhash・観測時刻・未完了事項](../../410-acceptance-recapture-2026-11-18.md)。台帳行IDは`2026-11-18-canonical-acceptance-sidecar-recapture`。
