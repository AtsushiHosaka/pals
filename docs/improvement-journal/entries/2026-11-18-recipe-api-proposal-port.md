# 一般Recipeの候補をAPIで検査する接続（2026-11-18）

既存workerにはLean環境がなく、一般laneのローカル検査もmacOSのsandboxに依存していた。workerへ検証器の資格情報を渡さず、APIが所有する既存検証器へ候補検査を接続する。[判断446](https://github.com/AtsushiHosaka/pals/issues/446)の承認範囲で、[draft API132](https://github.com/AtsushiHosaka/pals-api/pull/132)、[draft Agent151](https://github.com/AtsushiHosaka/pals-agent/pull/151)を作成した。APIは9045f9a、Agentは653c4b0。既定無効を維持し、本番操作・有料評価・採用や署名の権限追加は行っていない。

APIは現在のclaim・revision・質問文脈・可視Recipeの記録と固定sourceを照合し、閉じた文法からwrapperを再導出する。結果は候補提示だけで、最終の意味審査・回答QA・APIによるcompileを省略しない。workerは応答の型とechoを検査し、source hashを自分でも再導出する。APIの待機予算は残claim期間と読み取りに使った時間で制限する。既存のremote Lean processをHTTP切断で直ちに停止できるという保証はない。

APIの対象31 unitが成功・スキップ0、0.80秒。Agentの対象195 unitが成功・スキップ0、0.569秒。独立レビューで阻害する欠陥は見つからなかった。これは単体の境界検査であり、実DBや配備の検証ではない。

最初のlocalhost実mTLS試行は、API既定budget30000で正例が29.486秒後に待機timeoutとなり、直後の不正例もbusyで503となった。2caseは失敗として保持する。fixtureはremote終了を待って閉じ、終了後Lean0・Lake0・対象portのlisten無しを確認した。

実依存のcanary compileは7215msで成功。その後、APIが明示的に許すbudget90000の別条件で、正例candidate・不正命題の実compile拒否・短い待機のfallbackと再試行無しの3caseが成功・スキップ0、88.21秒だった。claim/catalogは明示した固定fixtureで、API transport・mTLS・Leanは実物である。30秒での成功や速度改善を示す測定には数えない。

使用した検証器source146と本番に保持する189はv1 attestationの形は同じだが、内部sourceには差がある。本番sourceとの同等性、実PostgreSQL、Agent既定30秒の通し検証、remote CPUの即時停止、本番の保存・描画・再読み込みは未確認。これらが必要な配備判断へ進める証拠にはしない。sourceの対象CIは確認中。
