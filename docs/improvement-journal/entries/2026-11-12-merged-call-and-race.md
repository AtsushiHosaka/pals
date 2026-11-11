# 形式化と証明を 1 回で、候補を並列で: 統合呼びと競争、修復の試走 (2026-11-12)

- 指標: 時間と、閉じる題の割合。
- 仮説: 命題と証明を 1 回の呼びで出し、複数を同時に出して常駐 Lean で競争させれば、閉じる割合が上がり、時間は 1 呼び分で済む。
- 変更: [pals-agent#121](https://github.com/AtsushiHosaka/pals-agent/pull/121)の `fast_answer.merged_call` と `run_merged_probe.py`、`run_repair_probe.py`。
- 測定の条件: 12 題(探索用。held_out 2 題を含む)、Luna、各 1 回、Mac、負荷 11〜15、2026-11-12。命題の忠実さの関所は含まない(閉じる/閉じないだけ)。
- 結果:
  - 統合呼び(命題 + 証明 3 + 否定の証明 3): effort none で 2.0〜4.3 秒(出力約 80 トークン)。そのまま閉じたのは prove/decide の 9 題中 5。low は 4〜18 秒で、閉じる数は同じ(5/10)。
  - 4 並列(none): 閉じた題は 5 → 6/12。命題が一致するのは題により 1〜4 本で、証明の持ち寄りは同じ命題のときだけ。
  - **失敗した 1 回目:** low の統合呼びが `Structured response did not complete`(推論でトークン上限 800 を使い切る)。上限を 3000 に上げて解消。
  - 修復(コンパイラのエラーを返して再生成、最大 2 回、none): 閉じなかった 17 題中 3 題が閉じた(7.5 s、10.4 s、10.8 s)。cubic の導関数、数列の和、微分方程式、行列式は 2 回で閉じない。10 秒を超えるので採らない。
- 判断: 統合呼び(none)+ 3 並列 + portfolio の競争を採用。修復は不採用。
- 限界・未確認: 題の選び方の影響が大きい(n=12)。none の分類で `explain` に落ちる題がある(射影の非単射は none で explain、low で decide)。
- 次にやること: 強い証明生成を 5 秒以内に出す手。`explain` 型から中心の命題を取り出す手。
- 出典: [pals-agent#121](https://github.com/AtsushiHosaka/pals-agent/pull/121)、生データ `data/2026-11-12-fast-answer/mp*`、`rp-repair.json`(命題・証明の本文は除去)。
