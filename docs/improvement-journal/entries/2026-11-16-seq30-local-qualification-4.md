# seq30の4回目のローカル資格確認（2026-11-16）

オーナーの[追加1回の承認](https://github.com/AtsushiHosaka/pals/issues/396#issuecomment-6909758854)後、固定した親24d8f95・infra ce084f3・候補b976で正規ローカル資格確認を1回実行し、acceptedになった。モデル、oracle、意味審査、成功条件は変えていない。第3回の失敗は保持する。

実PostgreSQL・Lean・providerから回答、説明、保存、描画、再読み込みまでの契約を受け入れた。主担当が初回wrapper終了時に観測した取得全体の壁時計は138.567秒、内部provider呼び出しは11件、proxy台帳の差分は0.034660 USDだった。実請求額ではない。取得後は71 calls・255446/700000μUSD、blocked=false。resetやrolloverは行っていない。

その後の正規verify-existingでもacceptedを確認した。同じ取得の再照合であり、新しい有料送信や試行として数えない。初回受領書が更新されたことと、現受領書のhashは[資格確認4の実測](../../seq30-local-qualification-4-2026-11-16.md)に残した。

品質台帳にはavailabilityの1/1を1行追加する。以前の失敗と併せて数学全般の精度向上や改善率を主張しない。本番AMD64・認証・ネットワークと本番受け入れは別の条件であり、この成功で代替しない。

条件の補足: 固定subjectと実requestは証明生成`gpt-6.1-terra / medium`、出力`en`、単一証明問題n=1だった。カード数は該当しない。固定worker実装の意味審査・説明は`gpt-6-luna / low`で、個別callのeffort記録はない。修復上限は設定source上6・凍結env/composeで上書きなしだが、今回の実使用回数は未確認。実request hashと根拠の区別は上記詳細記録に追記した。新しい測定や試行数は追加しない。
