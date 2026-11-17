# seq30の第6回ローカル資格確認（2026-11-17）

狙いは、同じ問題・gpt-6.1-terra / medium・oracle・審査と成功条件を維持して、実DB・Lean・providerを使う資格確認の受け入れを確かめること。#398の包括承認と累積1 USD制限に従い、親5e53d4a3・infra3f9ade65・候補33447ab9の準備から新しい専用state・単一送信markerで1回実行した。

結果は0/1。保存markerと同じrequestがfailed・lean_verification_failedになり、取得結果もfailedだった。準備用canaryは2420msでverifiedだが、生成した証明のcompileと意味審査のどちらで失敗したかは保存証拠だけでは不明で、分類はunclassifiedとする。

取得全体wall108.650秒は主担当の終了時観測。内部8 calls・proxy差分0.034900 USDで、実請求額ではない。終了時91 completed calls・actual/reserved327573μUSD、過去closed reserved込み上界638241μUSD・残361759μUSDだった。内部callsを製品・数学の分母へ加算しない。

判断は失敗を保持し、同じmarkerで重複送信しないこと。終端failedと費用が確定した今回とは分けて、次に取得する場合は同条件・残予算を確認し、新しいstate・markerの別proofとして実行する。保存結果だけで数学の誤りを断定せず、期待値も緩和しない。本番受け入れは別の条件である。

[結果と証拠hash](../../seq30-local-qualification-6-2026-11-17.md)、品質台帳IDは2026-11-17-seq30-local-qualification-6。新しい実環境読取やモデル送信はこの記録作成では行っていない。
