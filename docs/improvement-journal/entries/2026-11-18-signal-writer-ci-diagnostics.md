# 子プロセスのCI失敗で停止工程を残す（2026-11-18）

[#382](https://github.com/AtsushiHosaka/pals/issues/382)の[API候補 #124](https://github.com/AtsushiHosaka/pals-api/pull/124)は、最初のheadで別プロセスの5秒timeoutが2回起き、正式CIを通らなかった。旧baselineでも同じ失敗を再現した。一方、区間別に調べたローカルの旧・新各20子プロセスは全て成功し、最大0.910秒・0.844秒だった。CIの遅延原因をローカルの数値から断定しない。

`96b58766739bff793f2ebf41c11f28c62237f5a1`ではtest helperへ固定工程名とmonotonic時刻を足し、時間切れでも安全な部分記録を回収する。raw stderr、DB URL、job ID、環境変数は診断へ出さない。5秒、実PG fixture、応答速度p95の1秒未満という条件、production appとCI gateは不変である。子と通信taskは時間切れ・取消し時も回収する。

元helperで部分記録の回帰が1件失敗し、新helperのparser単体1件と実子プロセス2件は成功した。最終signal suiteも実PGで8件成功した。独立レビューとrootレビューにP0〜P2指摘はなかった。これらは実装境界の検査で、製品の回答率や速度の評価へ足さない。

新headの正式PR CI `44255020572`は389件成功・失敗/error/skipなしで完了し、先行push CI `44255013475`も成功した。診断追加を原因修正や配備完了と扱わない。旧2失敗と原因未確定の記録を保持する。新規有料呼出・本番変更は0件。

出典: [実装候補と検証範囲](../../382-answer-quality-candidate-2026-11-18.md)、API PR #124内の検証note。
