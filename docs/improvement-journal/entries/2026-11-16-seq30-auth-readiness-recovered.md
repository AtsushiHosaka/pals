# seq30の新seedによる認証開始確認（2026-11-16）

- 指標: 有料capture前の認証context準備。数学の精度や本番受け入れは測定していない。
- 仮説: 新seedと現候補・source・実runtime pinsを結び付けた契約なら、正規helperが認証済みBearerを観測できるか確かめられる。
- 変更: 親24d8f95・infra ce084f3、新候補b976、新seed9295を使用。正規factoryでpreviewを導出し、正規transportの開始処理だけを実行した。
- 測定の条件: local macOS、実headless認証開始n=1。対象GETのBearer観測を成功条件とし、質問・見積もり・証明生成を送信していない。
- 結果: 技術認証開始1/1、authenticated_context_observed。seed不変、transportのAPI操作メッセージ0、有料処理false、本番API認可検証false、本番受け入れfalse。
- 判断: 認証開始の確認として記録し、後続の資格確認と本番受け入れを別に行う。前回の失敗は保持する。
- 費用: この認証確認時点では52 calls・180904/700000 μUSDを維持。有料capture3は未開始で、実請求額は未確認。
- 限界・未確認: 認証更新要求の個別観測はないため、refresh成功とは主張しない。前回HTTP 400の根本理由や解決は未確定。成功率の改善や時間短縮は示さない。
- 次にやること: 固定した候補・sourceで正規資格確認を行い、その後に本番の回答・保存・描画・再読み込みを検証する。
- 出典: [認証contextの観測](../../seq30-auth-context-observed-2026-11-16.md)、品質台帳 `2026-11-16-seq30-auth-readiness-recovered`、[pals#378](https://github.com/AtsushiHosaka/pals/issues/378)。実行結果のhashは確認記録に掲載した。
