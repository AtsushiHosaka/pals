# Projectless Chat Start Design

## Scope and boundaries

- Project は利用者が明示的に作る整理単位であり、通常の会話開始の前提条件ではない。
- `project_id` は chat の所属を表す唯一の正とする。クライアントが送る任意の project ID で chat の所属を上書きしない。
- 既存の Project 配下 routes と legacy Project 非所属 chat の読取り URL は互換性を維持する。

## API and persistence

- `POST /v1/chats` は body を受け取らず、認証済み所有者の Project 非所属 chat を `201` で返す。`GET /v1/chats` は所有者の Project 非所属 chat を返し、`GET /v1/chats/{chat_id}` はその個別 chat を返す。
- `/v1/projects/{project_id}/chats` の作成・一覧契約は変更しない。
- `ChatCreate.project_id` と create command は nullable にする。repository は Project 非所属作成時に Project 所有確認をせず、どちらの作成でもアカウント出力言語を snapshot する。
- 新しい immutable chat migration で `chats_scope_ck` を、Project 所属と legacy proof link が同時に非 null ではないことだけを制約する形に置換する。Project 非所属一覧用の owner-scoped partial index を追加し、migration state machine は既存 v2 DB を v3 に upgrade できる。
- proof 作成 service は Project 非所属 chat を legacy 専用として拒否しない。chat の `project_id` を job に保存し、mismatch と所有者・言語境界は既存と同じ検査を行う。
- container 起動時は chat migration を API serve より前に適用する。

## Frontend flow

- Dashboard の `New chat` と空でない prompt 送信は projectless create API を呼び、成功後 `/chats/{chat_id}` を開く。prompt は chat 作成成功後にのみ送信する。
- Dashboard の入力例はプランに関係なく数学の問題だけを表示する。問題を選択すると入力欄を更新し、送信や画面遷移は行わない。
- `/chats/{chat_id}` は Project 非所属 chat の proof timeline、入力、説明、clarification を通常 chat と同じ安全な表示・再試行境界で表示する。
- sidebar は Project 非所属 chat を `Chats` として表示し、リンクは `/chats/{chat_id}` を使う。Project 作成 action は独立して dialog を開く。
- create/list/send の失敗は入力と既知の表示を保持し、retry を提示する。認証 subject が変わると取得中・保持中の chat state を破棄する。

## Verification

- API/service/HTTP tests は projectless create/list/get、所有者境界、language snapshot、proof create と project mismatch を検証する。
- PostgreSQL migration tests は fresh install と v2-to-v3 upgrade、legacy rows の保存、owner index を検証する。
- frontend tests は `New chat`、dashboard prompt、無料・有料プランでの数学の入力例、project modal 境界、projectless navigation、失敗時入力保持を検証する。
- local browser smoke は Project 非所属 chat 作成から proof request submit までを実 API・PostgreSQL で確認する。
