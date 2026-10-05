# Projectless Chat Start Requirements

## Purpose

学習者が Project を作成する意思と、ただちに証明について会話する意思を分ける。Project に属さないチャットも通常のチャットとして作成、再選択、証明要求送信できるようにする。

## Requirements

| ID | Requirement |
|---|---|
| PCS-001 | `New chat` は Project を作成せず、認証済み学習者の Project 非所属チャットを新規作成して開く。Project 作成 dialog は `Create project` の明示操作時だけ開く。ホームの入力例には数学の問題だけを表示し、選択すると入力欄にその問題を入れる。 |
| PCS-002 | ホームで空でない証明要求を送信したとき、PALS は Project を作成せず Project 非所属チャットを作成してその要求を送信する。作成または送信に失敗した場合は入力を失わず、失敗を表示して再試行できる。 |
| PCS-003 | Project 非所属チャットは Project 配下のチャットと同じく、所有者だけが一覧、選択、証明要求、説明および追加質問に利用できる。証明 job の `project_id` はそのチャットの所属に従い、Project 非所属チャットでは `null` とする。 |
| PCS-004 | Project 非所属チャットにも開始時点のアカウント出力言語を保存する。過去の legacy Project 非所属 chat は引き続き読め、他アカウントの chat、証明 job、言語設定を表示または操作できない。 |

## Acceptance Criteria

- `New chat` を押すと Project 作成 dialog を表示せず、Project 非所属チャット画面を開く。
- ホームの送信は Project 作成 dialog を表示せず、作成した Project 非所属チャットで要求を送信する。
- ホームの入力例はプランに関係なく数学の問題だけを表示する。選択しても設定画面や Project 作成 dialog を開かず、入力欄に問題を入れる。
- `Create project` は従来どおり Project 作成 dialog を開き、Project 配下の chat の挙動を変えない。
- Project 非所属 chat の一覧と個別画面は再読み込み後も復元し、同一所有者だけが取得・送信できる。
- Project 非所属 chat から送信した proof job は `project_id=null` として作成され、説明・追加回答・失敗表示はその chat の保存済み言語を用いる。
- chat 作成、一覧取得または proof 送信に失敗したとき、未送信の入力を保持し、誤って Project 作成 dialog を開かない。
