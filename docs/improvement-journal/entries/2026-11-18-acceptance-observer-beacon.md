# 単一送信の受け入れgateが計測beaconで拒否された記録（2026-11-18）

認証情報を別保存してcanonical送信を再開した。旧plan・session・凍結hashは不変で、同じkey・state・scenario・cycle・modelを維持し、session引数だけを変更した。新規送信は1件だけで、追加質問は送っていない。送信はexit 0だったが、初回acceptanceは`observer_attempted_mutation`、exit 1でfailedとなった。

traceはverifying・revision 2からanswered・revision 3へ進み、最後のHTTPは200、runtime 6 rolesのmetadata照合も済んだ。sourceの順序上は回答・保存・render・reload比較を通過し、rootもChrome実画面で結論全文とreload復元を独立確認した。それでもwrite counterの拒否により正式acceptedは不可である。観測時刻差を正確な回答時間やp95へ換算しない。

局所診断で、拒否は`POST /cdn-cgi/rum`の3件だけと特定した。元policyで全abortし、質問再送・SSM・IAM更新・host操作は0件。[Cloudflare公式資料](https://developers.cloudflare.com/web-analytics/data-metrics/data-origin-and-collection/)では同一domain上のこのpathをWeb Analytics beaconの送信先として説明している。別sourceではabortを続けながら当該計測要求だけをsuppressed counterへ分ける修正を準備中だが、CI・独立レビュー前で、新sourceの正式acceptanceは未実施である。

元のfailed結果を保持し、品質台帳はgateの1件だけをn=1・成功0・`unclassified: 1`として追加する。先行認証確認と同じ再開に属する別時点・別指標のため、`overlap_with`を付け、利用者試行・数学の成功率へ合算しない。金額は未取得でUSDは空。source補修・live後続の成果や全体完了は主張しない。

[段階別の観測・hash・未確認範囲](../../410-resume-auth-diagnostic-2026-11-18.md)。台帳行IDは`2026-11-18-canonical-acceptance-observer-write-blocked`。

追加診断で実URLは3件とも`/cdn-cgi/rum?`、末尾単独`?`・query keys 0と判明した。queryなしだけの厳密一致案はこの実通信に合わず、新sourceでは区切りなしと末尾単独`?`の正確な2種類だけをabortしたまま分離する方針へ進んでいる。値付きquery等は対象外で、実装は進行中、機能gate合格は未取得である。
