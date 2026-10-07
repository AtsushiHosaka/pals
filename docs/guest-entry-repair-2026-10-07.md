# ゲスト試用開始エラーの調査と修復範囲

2026年10月7日。ユーザーから、公開版のゲスト試用を開始できない障害への対応依頼を受けた。この文書は修復のWORKING記録であり、既存の仕様や本番の署名・認証・利用上限を変更しない。

## 公開入口でゲスト開始の通信が404になる

公開APIの`GET /health`は200で、`environment=prod`を返した。一方、`https://api.palschat.site/v1/guest/session`のGETと、ブラウザの事前確認に相当するOPTIONSは、どちらも404と`Not found`を返した。OPTIONSには次のヘッダーを指定した。

```text
Origin: https://palschat.site
Access-Control-Request-Method: POST
Access-Control-Request-Headers: content-type
```

404応答に`Access-Control-Allow-Origin`はない。ブラウザでも`/try`の入力欄が無効になり、接続エラーが表示された。API実装のゲスト経路は、機能無効なら503、機能が有効でCookieがない読取GETなら401を返すため、観測した404はその契約と異なる。

公開切替記録ではAPIの入口にCaddyの許可リストと既定404を設置している。保存済みの旧Caddy提案にもゲスト経路はない。ただし、本番の現行Caddy設定はこのMacBookから取得できていないため、そのファイルの内容は未確定。

調査の親リポジトリは`b85018b`、Webは`5989752`、APIは`03ecaa5`、infraは`bff2e777`。公開版の配備workflow成功だけではゲスト利用可能とは判定しない。現行の通常更新はホストのAPI環境とedgeコンテナを保持し、ゲスト経路・設定・DB構造の追加を代行しない。

## UIの安全な再接続と本番入口の修復を進める

Web側には、開始時の接続失敗から再試行できる操作と案内を追加した。未送信の入力、保存済み会話、応答が不明な送信の操作キーを保持する。連打による接続の重複も防ぐ。再接続だけで新しい質問は送信せず、既存のLPで明示的に送信した下書きの扱いは維持した。この修正だけでは公開入口の404は解消しない。

Webの修正は`d436271`として`codex/guest-entry-recovery`にpushした。変更は`hooks/useGuestChat.ts`、`components/GuestChat.tsx`、`lib/guestMessages.ts`、`tests/unit/guest-chat.test.tsx`の4ファイル。

同Webディレクトリで次の検証がすべて成功した。

| コマンド | 結果 |
| --- | --- |
| `npm exec -- vitest run tests/unit/guest-chat.test.tsx --cache=false --configLoader=runner` | 43件成功。うち8件が接続復旧の追加ケース。所要2.86秒 |
| `npm run typecheck` | 終了コード0 |
| `npm exec -- eslint hooks/useGuestChat.ts components/GuestChat.tsx lib/guestMessages.ts tests/unit/guest-chat.test.tsx --max-warnings=0` | 終了コード0、警告なし |
| `git diff --check` | 終了コード0 |

API呼出しを単体試験の境界で置き換え、初期接続失敗、復帰、連打、入力・会話・操作キー・LP下書きの保持を検証した。公開経路や本番DBはこの試験の対象外。依存パッケージは既存のものを再利用し、一時的なsymlinkは削除済み。初回のVitest起動は共有依存ディレクトリへのキャッシュ書き込みで失敗したため、上記のキャッシュ無効設定で実行した。

本番側では、Miniの現行Caddy設定、API起動設定、ゲストschemaの状態を読み取りで照合してから、必要な差分を確定する。必要なゲスト経路は次の範囲に限定する。

| 経路 | メソッド |
| --- | --- |
| `/v1/guest/session` | GET、POST、OPTIONS |
| `/v1/guest/proof-requests` | POST、OPTIONS |
| `/v1/guest/proof-requests/{UUID}` | GET、OPTIONS |
| `/v1/guest/proof-requests/{UUID}/answers` | POST、OPTIONS |
| `/v1/guest/proof-requests/{UUID}/lean` | GET、OPTIONS |

既存のprivate経路の拒否と既定404を維持する。APIが要求するOrigin、Cookie、利用上限の検査を迂回するCORS応答や代理の成功応答は追加しない。

APIの有効化には、既存のschemaとhash keyの一致、guest service、実workerが必要になる。公開環境の`CF-Connecting-IP`がedgeで上書きされ、originへ接続できる経路が限定されていることを確認する。APIで実際に見える直前proxyのIPを個別に指定し、Uvicornのproxy書換えを無効にする。未確認のIPや一般的なforwarded headerへの代替は使わない。通常CORSとゲストOriginの両設定を照合する。

既存DBの移行が必要なら、本番の署名と移行契約に沿った差分を別途確認する。schemaを設置したことやhealthが成功したことだけで、公開ゲストの修復完了とは判定しない。

## 完了は公開ブラウザの開始状態で確認する

完了条件は、公開ゲスト経路のOPTIONSが正しいOriginを許可し、`/try`でセッション開始後に入力欄と質問例が利用できること。開始時の一時失敗後は、未送信入力と既存の操作キーを保った再接続で復帰することも確認する。許可しないOriginとprivate経路は引き続き拒否される必要がある。

質問の送信・回答生成は、開始状態の確認とは分けて結果を記録する。ローカルのUI単体試験を、公開経路や本番DBでの合格の代用にしない。
