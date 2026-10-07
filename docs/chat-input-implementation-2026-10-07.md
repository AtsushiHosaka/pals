# 応答中の追加入力：実装と検証

対象は `specs/proof-request-reuse` の PFR-016〜020 と関連する回数枠・トークン枠・ゲスト制限。仕様の基準は親リポジトリ `7e11a18`。実装revisionはAPI `312b5eb`、Agent `66b1697`、Frontend `02d3be0`。追加入力の扱いは、2026-10-07 にユーザーが選択した7項目に従う。本番デプロイはこの作業に含めない。

## 実装

APIは追加入力を保存するトランザクションで回答の公開を保留する。受信しただけでは数学的な条件を失効させず、エージェントが訂正と判定した時点で入力の世代を進める。旧世代のassessment claimとLean jobの関連付けを失効させるため、遅れて届く旧結果を新条件の回答として採用しない。

曖昧な入力は意図確認待ちにし、明確な別質問は同じチャットの後続要求に保存する。別質問と判定した場合は原要求の保留を解除し、保存していた結果を条件付きで公開できる。混合入力は訂正と後続要求を同じトランザクションで保存する。順番は入力の受信番号で決め、先行要求の回答・失敗・保留状態を実行直前にも確認する。

表示済みの旧回答は、原文、確認済みの前提、適用した数学的な約定、出典、Lean jobとの関連を履歴に残す。訂正によって旧証明の検証記録を書き換えない。画面はAPIの受信確認を優先し、世代・revision・更新時刻が古い取得結果を取り込まない。日本語・英語・簡体字・繁体字の通知と意図確認を追加した。

回数枠は論理的な要求に対して最大1回を消費する。別質問は別要求として実行前に枠を確認する。トークン枠は旧世代を含む実利用を集計し、未確定の呼び出しには予約上限を残す。訂正後のquoteは現在の条件と世代に結び付ける。残量が足りない場合も訂正は保存し、旧回答を保留して明示的な再開を待つ。ゲストは訂正と意図確認の送信にも日次制限を適用し、混合入力の派生レコードや同じ送信の再試行には重複加算しない。

エージェントは実モデルで入力を解釈し、その後のモデル・検索・Lean呼び出しの前に現在のsnapshotを確認する。進行中の外部呼び出しの即時停止は前提にしない。独立したRecipe reviewerには専用のpermit/receipt経路を追加し、候補、source hash、作者との分離、現在の要求・世代を検証する。

DB変更は既存テーブルを変更しない追加migration。local、production、署名を検証するMac releaseの経路に配線した。起動時は新schemaを読み取り検査する。したがって、新コードの起動前にmigrationが必要であり、起動時にDDLを実行して補う処理は入れていない。

## 検証記録

| 対象 | 結果 | 証明する範囲 |
| --- | --- | --- |
| Frontend全unit | 1,352 passed | 既存画面への回帰。型検査、変更ファイルのESLint、webpack buildも通過 |
| Frontendの履歴条件修正 | 101 passed | reload後も旧前提・約定を表示し、現世代の条件を混ぜない |
| Agentの対象テスト | 391 passed | 解釈、snapshot fence、meter、Recipe actorのHTTP契約 |
| 実Lunaによる解釈 | 5/5 passed | 実数→整数、整数→正整数、曖昧な整数質問、別質問、混合入力 |
| 実Agent/Luna/API/PostgreSQL | 1 passed | production factoryとAPI routeを使う実解釈・永続化・usage保存 |
| 訂正・既存Lean連携・約定・完了通知・共有のDB回帰 | 59 passed、1 opt-in skipped | 受信と公開の競合、旧結果の不採用、旧回答履歴、既存共有の不変性。追加の再起動・count・idempotencyケースも通過 |
| トークン・release・認証 | 102 passed | PG16実DB28件とunit74件。累積上限、80+20、差分精算、期間変更、late receipt、旧operation分離、Recipe認証、起動時検査 |
| APIのHTTP契約・ゲスト入力・履歴・出典 | 118 passed | 送信枠、所有者分離、closed JSON、履歴経路 |

DB検証にはPostgreSQL 16の専用一時DBを使った。共有ローカルのPostgreSQLは停止中で、固定IPがreconcilerと競合していたため、そのネットワークは変更していない。既存の `pgvector/pgvector:pg16` イメージを検証専用の一時サーバーに使った。検証用コンテナは終了後に削除した。共有コンテナの設定は変更していない。Frontend/Agent/APIの依存は既存checkoutのランタイムを再利用した。

APIでは変更箇所のRuffとmypyを実行した。Agentの変更箇所にmypyの新規診断はなく、未変更の `openmath.py` に6件の既存診断が残る。全Agent unitの試行には既存の依存不足などがあるため、全リポジトリ成功とは扱わない。

再現対象はAPIの `tests/integration/test_proof_inputs.py`、`test_guest_inputs.py`、`test_input_allowance.py`、`test_token_corrections.py` と各既存回帰。実プロバイダテストは同ファイルのopt-inケース。Agentの実モデル検査は `scripts/proof-input-smoke.py`。秘密情報やテストDBの接続情報は記録・commitしていない。

最終のAPI関連検査は114 passed、実プロバイダ用1件はdefault runでskip。実プロバイダケースは別実行で通過した。文書はnatural-japaneseのlintで検出0件となり、読解負荷の列挙3件を確認して意味を優先した。yomiyasuの主述関係・接続・文末の観点も同じ原稿に適用した。

## レビューと残る検証

SDDとFastAPI/Next.jsの境界をレビューし、P1の4件を修正した。ゲストの意図確認にも送信枠を適用し、解釈claimを通常回答の再試行回数から恒久的に除外した。旧履歴には確認済みの前提を残し、解釈だけの再開でrevisionが変わっても、同じ世代の保留結果を正しいclaimから公開できるようにした。別タブの意図確認が英語になるP2は、画面の4言語表示を使う修正で解消した。

実装と上記の境界検証は完了した。実キュー、provider、Lean compiler、ブラウザを通す訂正・別質問・混合入力の一連の受け入れ検証は **NOT VERIFIED**。DBテストのfinished-job fixtureは要求側の公開制御を検証するものであり、実Leanの成功を証明しない。本番の署名・KMS admissionとデプロイも未実行のため、release全体の完了とは判定しない。

確定済みの `unknown` receiptを成功に上書きする運営経路は追加していない。unknownが残る場合は成功公開を止める。期限切れのDSP review claimも許可せず、再生成が必要という既存の制約を維持する。これらを解消済みとは扱わない。
