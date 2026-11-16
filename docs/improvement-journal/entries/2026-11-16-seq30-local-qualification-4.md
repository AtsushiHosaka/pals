# seq30の4回目のローカル資格確認（2026-11-16）

オーナーの[追加1回の承認](https://github.com/AtsushiHosaka/pals/issues/396#issuecomment-6909758854)後、固定した親24d8f95・infra ce084f3・候補b976で正規ローカル資格確認を1回実行し、acceptedになった。モデル、oracle、意味審査、成功条件は変えていない。第3回の失敗は保持する。

実PostgreSQL・Lean・providerから回答、説明、保存、描画、再読み込みまでの契約を受け入れた。主担当が初回wrapper終了時に観測した取得全体の壁時計は138.567秒、内部provider呼び出しは11件、proxy台帳の差分は0.034660 USDだった。実請求額ではない。取得後は71 calls・255446/700000μUSD、blocked=false。resetやrolloverは行っていない。

その後の正規verify-existingでもacceptedを確認した。同じ取得の再照合であり、新しい有料送信や試行として数えない。初回受領書が更新されたことと、現受領書のhashは[資格確認4の実測](../../seq30-local-qualification-4-2026-11-16.md)に残した。

品質台帳にはavailabilityの1/1を1行追加する。以前の失敗と併せて数学全般の精度向上や改善率を主張しない。本番AMD64・認証・ネットワークと本番受け入れは別の条件であり、この成功で代替しない。
