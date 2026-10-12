# 2026年10月12日 ゲスト保持期限処理と本番復旧

16:17 JST の [通常更新](https://github.com/AtsushiHosaka/pals/actions/runs/38216786761) で、署名付き V7 の sequence21 が既存 DB に適用された。API 起動後に、すでに期限切れだったゲスト会話2件の内容を保存期限処理が削除した。ホストの更新処理が起動後にも旧テーブルの完全一致を要求していたため、この正当な削除をデータ保持失敗と判定した。復旧の再試行も、削除前の snapshot と比較して停止した。

調査時は公開 Web/API が502、13000/18000は connection refused。DB、Cloudflare connector、機械認証 broker は稼働していた。Web/API/worker/edge は停止していた。

## 原因を確認した証拠

旧 snapshot の103テーブルのうち、admissionを除く102テーブルを読み取りで照合した。差分は `public.proof_requests` と `public.proof_request_claims` だけで、行数は15件と22件のままだった。V7追加列の値は全件 `gpt-6-luna` だった。

2件のゲスト期限は削除時刻より前で、session・chatの所有者は一致した。07:18:11 UTC の tombstone と対象request・claimの更新は同一トランザクション1187で、署名付きadmissionは1186。対象requestの内容消去と `failed/chat_deleted`、claimのprivate evidence消去は、APIの `ChatRetentionService` と `chat_deletion.scrub` の実装に一致した。他のrequest/claimはadmissionより前の行バージョンで、対象外の旧テーブルはすべて一致した。利用量や回答を新たに書き換える復旧は行っていない。

## 修正と復旧

Infraの通常更新authorityは、writer停止中の厳密なデータ保持検査を、writerの初回起動前に証明する。private checkpointを元snapshot、署名manifest、親SHA、DB identityへ結び付け、復旧再試行では一致する証明を再利用する。起動後の保存期限処理で、その証明を無効にしない。証明のない新規更新は従来の保持検査を必須とし、不一致の証明は拒否する。

今回の旧authorityにはcheckpointがなかったため、candidate21専用の復旧処理で、旧authorityのhash、独立した実KMS署名/admission観測、旧source、停止した起動済みcandidateのimage/config、公開edgeのfingerprint、上記の期限・所有者・行数・transaction・対象外テーブル一致を検証した。元authority/policyをprivate backupへ保持し、修正版のhashを設置した。元snapshotは保持し、private auditとcheckpointを追加して、既存の署名付きforward recoveryとreceipt検査を実行した。

復旧は同じDB/volumeとsequence21を保持した。DDL再実行、署名、admission追加、削除済みpayloadの復元、DNS/route変更は行っていない。current receiptは親 `a59f27c23e95ab38c88764563599a12411fba7e5`、status `healthy`。pendingは解消し、既存の自動復旧監視も `healthy` になった。ホスト変更は本チャットのサーバー復旧依頼に基づく。

## 検証結果

- 復旧/host単体: 170件実行、失敗なし、専用PostgreSQL fixture 1件skip。既存APIの認証モジュールを指定し、実socket境界を含めて実行した。
- 16:58 JST の公開確認: root、`/signin`、`/try`、API `/health` が200。匿名 `/v1/auth/me` は401、内部worker経路は404。
- API/Web/worker/edgeがRunning。worker ready markerを確認。
- 公開ブラウザ `/try` のゲスト接続が完了し、質問例、入力欄、添付・数式キーボード操作が有効になった。質問送信・LLM回答生成は今回の確認には含めない。

Infra修正は `775231d`。秘密値、DB内容、ログ、cookie、生成物はこの文書に含めない。
