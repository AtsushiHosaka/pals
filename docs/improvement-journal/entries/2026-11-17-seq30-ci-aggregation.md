# seq30の自動CI集約（2026-11-17）

狙いは、同じrepo・branchのpushとPRによる重複workflowを集約し、自前runnerで不要な重複実行を避けること。infraのe4adbff090e59ddb3b476045484f550a27332b14でconcurrency groupとcancel-in-progressを追加した。別repoのfork branchはgroupを分け、4 jobs、自前runner labels、検査範囲は保持した。13be88fcとの差分でも、workflowの変更がこのgroup追加に限られることを確認した。

同じhead e4adbffの[push run 43998354835](https://github.com/AtsushiHosaka/pals-infra/actions/runs/43998354835)はcancelledとなり、[PR run 43998363240](https://github.com/AtsushiHosaka/pals-infra/actions/runs/43998363240)が存続してsuccessになった。GitHubのrunとjobs APIを読み直し、存続runの4 jobsがすべてsuccess、自前runnerのself-hosted/linux/arm64/pals labelsだったことを確認した。新しいworkflowの起動や取消操作は行っていない。

判断は、同branchの重複集約を採用し、検査結果は候補の正確なcommitに対応する存続runで確認すること。所要時間の削減秒数、runner負荷の削減量、費用は未測定であり、成功例一つから改善率を作らない。製品や数学の成功率にも換算しない。

これは[既存の診断記録](../../seq30-inventory-diagnostic-2026-11-17.md)で触れたCI集約の出典補足で、新しい測定ではない。台帳の試行数とグラフは追加・変更しない。本番動作や元のtuple拒否の根因を修正したという証拠でもない。
