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

公開切替記録ではAPIの入口にCaddyの許可リストと既定404を設置している。Mini側の現行調査で、ゲスト経路の欠落に加え、ゲスト機能が無効、hash key・許可Origin・proxy設定が未設定、ゲストschemaも存在しないことを確認した。Uvicornにはproxy書換え無効の指定もない。現行の署名済み配備はseq9。

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

実ブラウザでは、一時的なローカルWebを起動し、接続できないloopback URLをAPIに指定した。日本語で接続失敗の案内と「接続を再試行」が表示され、再試行後も操作が残ることを確認した。API成功応答の代替は置いていない。これは失敗時UIの確認であり、本番開始の合格ではない。証跡は追跡対象外の`outputs/guest-entry-repair/20261007/local-connection-retry.png`。一時サーバーと依存symlinkは停止・削除し、開発サーバーが変更した型宣言は元に戻した。

ユーザーの明示的な許可を受け、本番Miniの既存チャット「検証 PALS本番起動」に、現行設定の確認と必要な修復を依頼した。現行v1〜v3の署名付き更新はゲストDDLを対象に含めないため、専用のv5契約を実装した。本番での適用結果と公開ブラウザの再確認は継続中。

Miniでゲスト5経路を追加した後、公開OPTIONSは200、ゲストGETはAPIの503 `guest_chat_unavailable`になった。こちらの独立した通信確認でも同じ応答だった。Miniでは、非許可OriginのOPTIONSが400、不許可methodとprivate経路が404であることを確認した。API直前の実TCP peerは`172.25.0.5`。Cloudflareへの偽装ヘッダー送信は公開側で403になったが、上書き後の値との直接比較は未実測。

ゲスト単独の署名付きv5候補は、既存25段階のregistry `612a7ef8…`からguestを追加した26段階の`fd52d186…`への遷移だけを許可する。2つの既存guest SQLの固定bytesと、32-byte keyのSHA-256 fingerprintを署名planに含める。raw keyは保護されたホストファイルから読み、Git・plan・引数・installer環境変数に置かない。既存のKMS、drain、署名admission、単一transactionを維持し、DBと親tableへの一時権限は元のACLへ復元する。

この候補は既存DBの25→26更新が対象。26段階の新sourceから空DBを初期化するguest契約は未実装であり、guest構造がない場合は起動・汎用migrationを拒否する。無署名のguest導入や鍵なしのDDL実行は追加しない。数学設定の既存v4候補は25→math26専用なので、guestを先に導入した後は、その前提と署名契約の更新が必要になる。

APIは`aa8b12c`、infraは`504f3d8`としてpushした。APIの共通単体・署名回帰287件、専用単体29件、実PostgreSQLのモジュール試験17件、共通署名更新の実DB試験5件、既存ゲスト試験16件が成功した。共通署名更新試験はPostgreSQL 16とpgvector 0.8.2で旧25段階から初期化し、v5適用、適用後検査失敗時の巻き戻し、鍵・署名・carrier改変の拒否、完全再実行、後続v1更新を確認した。KMS署名とDocker観測には試験用の境界を使っており、本番KMSやホスト由来の検証ではない。

infraのhost単体試験51件、Caddy 2.10.2の構文検証、実HTTPの経路試験141件も成功した。独立したソースレビューでは重大な問題を認めなかった。変更対象のRuffとdiff検査は成功。mypyは変更ソースにエラーを認めず、未変更の依存コードに既存の型エラーが残った。試験専用のコンテナ、認証情報、旧sourceの一時コピーは削除済み。

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
