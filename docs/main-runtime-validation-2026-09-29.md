# main 実行検証 — 2026-09-29

**判定: mainに不具合を確認し修正。修正後のローカル環境では、対象の主要操作フローはPASS。** 自然言語・形式的命題の証明生成、Projectの初回送信、ログアウト・再ログイン、数式をまたぐ選択質問、補足回答からの再質問、長い回答の閲覧、検索とLean source表示を実環境で確認した。過去の全ジョブの復旧、本番環境、Google OAuthの実フローはこのPASSに含めない。修正はローカルの未コミット変更。

## 対象

リモート main とローカル HEAD の一致を確認して開始した。

| Repository | main revision |
| --- | --- |
| pals | `02801ca4b670c0d8aa7938c1d531fabf1dbf83e2` |
| pals-webfront | `7837f8f15be095d0c911a3d36241d110683475d2` |
| pals-api | `858dd167f5f2409900b8d33b88a667d8b0b3127e` |
| pals-agent | `ab423351d95af0efbd18544a7a21739a0f27e548` |

既存の `pals-local` Compose 環境を使用。PostgreSQL、Cognito Local、LocalStack/SQS/S3、OpenAI、Lean verifier/reconciler は実体を使用した。UI検証の応答はモックしていない。クラウド本番・Google Hosted UI の実ログインは未検証。

## 修正内容

| 問題 | 修正と根拠 |
| --- | --- |
| Cognito の同一ユーザーのセッション更新で未送信入力が消える | auth epoch を維持して更新。再現回帰テストを追加。 |
| StrictMode の再マウントで OAuth callback を消費してから交換処理を中断する | 現在の試行が有効なことを確認してから callback を消費。回帰テストを追加。 |
| 数式と文章をまたぐドラッグ選択で質問フォームが出ない | パーサー由来の位置情報で表示選択を元の Markdown/TeX に対応付け。実ドラッグで送信まで確認。モデルが生成したHTMLによる位置属性の偽造は許可しない。 |
| 長い証明履歴ラベルで Lean source ボタンが画面外に出る | 履歴欄の幅を制限。デスクトップ・狭い画面で確認。 |
| 再読み込みすると最古の証明が選ばれる | 初期選択を最新に統一。表示中の手動選択は維持。 |
| 移行済み旧チャットがあると検索全体がエラーになる | Chat ID を厳密に検証する取得経路を追加。証明に残る元 Project ID は状態照会・SSE・source照会でも保持。検索結果から旧チャットとsourceを開けることを確認。 |
| 中断後の証明再開が過去の状態への遷移として拒否される | 獲得したclaimの最新状態を基準に、再計算中の古い進捗通知を抑制。APIの状態遷移検証は維持。 |
| 2回目以降のrepair再開で証跡が欠落しAPIに拒否される | 保存済みrepair routeの証跡を引き継ぐ。実際の旧ジョブ2件から構成したpayloadがAPIスキーマに適合することを確認。 |
| 補題の根拠への質問に補題の言い換えだけで答える | 生成・レビューの両方で循環しない数学的導出を要求。修正後の実回答ではgcdとベズーの等式による導出を確認。追加説明を別途Lean検証済みと主張しない制約を維持。 |
| 中断再開時に試行履歴が部分的で、修復回数を過少に送信する | 配列長ではなく保存済みの絶対試行番号から回数を算出。試行2→3の再現テストと実APIスキーマで検証。 |
| 新しいProjectで入力できるのに最初の証明を送れない | 初回送信でProject所属chatを作成してproofを送信。失敗時は入力を保持しchatを再利用。重複送信・遅延応答も検証。 |
| 長い補足回答の下部が切れる | Project非所属チャットの本文を既存のスクロール領域で囲む。入力欄と見出しを残して末尾まで読めることを実画面で確認。 |

## 実行状況

| Journey | 現在の判定 | 証跡 |
| --- | --- | --- |
| ローカルのメール・パスワードによるログイン | PASS | 認証後のワークスペース取得と再読み込み後の保持を確認。 |
| 自然言語の新規証明要求 | PASS | UIから受理され永続化。job `6c8d2059-b4f4-44c1-813d-2af3af546cec` はverified・説明completed。画面で表示し再読み込み後も保持。 |
| 形式的命題の証明要求 | PASS | `∀ n : ℕ, n + 0 = n` を実UIから送信。job `aa82258d-a13e-444e-bc5f-4a9a9c9acc2b` はverified・説明completed。画面表示と原文source一致を確認。 |
| 実Lean検証済みの証明・説明を表示 | PASS（既存要求の実処理） | job `14d447ec-9007-4667-ba93-a14a57f0d2fc` が今回の稼働中にverifiedとなり説明生成も完了。 |
| 数式をまたぐドラッグ選択と追加質問 | 操作PASS、非循環な導出を確認 | 初回 `398a3c67-7f14-4d8a-8961-a20f3c6b910c` からさらに質問した `1cd33bb4-7fb2-4b54-bfce-3c13901cb7a8` がcompleted。元のTeXと親回答IDをAPIで確認。修正版は約8秒で回答を保存した。 |
| Lean source表示 | PASS | 素数の証明、および元Project IDを保持する旧証明で表示を確認。素数の証明はAPIの原文284文字と画面表示の完全一致も確認。 |
| チャット検索・履歴からの再表示 | PASS | 検索の一致・不一致、旧チャット遷移、最新履歴の初期選択を確認。 |
| 狭い画面でsource表示 | PASS | CSS幅416pxで横方向のはみ出しなし。閉じる操作も確認。 |
| 既存の説明失敗表示 | PASS（失敗を正しく表示） | 旧証明のverifiedを維持し、説明生成失敗を表示。 |
| Google OAuth実フロー・実TTL経過の更新 | 未検証 | 回帰テストでの検証と実認証検証を区別する。 |
| Project作成・ログアウト後の再ログイン | PASS | ユーザーの明示許可後に実施。再ログインで元チャットへ戻り、証明とsourceを取得。Private Project `ade718b1-e6fc-4ecb-af8c-d68983cfc7d9` を作成。 |
| 新規Projectで最初の証明送信 | PASS | chat `fa07a393-e6f8-4abc-941a-1c0f8909934d`、job `7bc7b377-844b-4ebe-b346-e7302ae4a215` がverified・説明completed。Project/chat紐付けと画面のsource完全一致もAPIで確認。 |
| 長い補足回答のスクロール | PASS | 本文スクロール領域の高さ754px、内容1274pxで末尾まで520pxスクロールし、入力欄・見出しを保持。 |
| 中断済み旧ジョブの修正後の実再開 | 部分確認 | 旧proving job `85637af9` は再開して証明・説明完了。旧sketching job `0b90bcc7` は証明完了、説明レビュー失敗を正しく表示。全履歴の復旧は未完了。 |

追加回答は実際に理由を導出するようになったが、今回の文章には「対偶」と直接証明の区別や式の「左右辺」の呼称に不正確さが残る。非循環な根拠が出ることと、生成文の全表現が無誤りであることは区別する。Lean sourceの検証結果を、生成された追加説明全体の形式検証とみなさない。

## 自動検証

- Frontend: 65 files / **643 tests PASS**、TypeScript、ESLint PASS。
- Worker/pipeline: **271関連tests PASS**、ruff、mypy PASS。
- 追加の説明品質改善: **157関連tests PASS**、ruff PASS。独立レビューでも関連87tests PASS。これらの件数には重複がある。
- 最後の再開回数修正: **184関連tests PASS**、ruff・mypy PASS、復元試行3の4通知が実APIスキーマに適合。
- 実API状態遷移表: 9ケース / 35遷移 PASS。
- 独立レビュー: workerと旧チャット検索の両差分に未解決指摘なし。
- 上記は実UI・実LLM・実Leanの完了証跡を置き換えない。

## 実行環境上の制約

開始時に過去の未完了ジョブが多数残っていた。古いclaimの1時間のleaseや単一workerの逐次処理が待ち時間に影響している。既存ジョブの取消・queue削除・claimの手動変更は実施していない。

今回の新規自然言語要求は10:23 JSTに受理され、11:01 JST時点でverified・説明completedを確認。これは過去のキューを含む待ち時間で、空の環境の性能測定ではない。形式的命題も11:03 JST時点で完了を確認した。

説明品質改善の実モデル評価は、当初自動承認審査で具体的な送信許可が必要とされたため保留した。その後ユーザーの明示許可を受け、再ログイン・Project作成・修正後のOpenAI生成とレビューを実環境で完了した。

過去のreceiptにはDLQへ移動したものがある。現行DPB-013はstartup後の周期DB scanを禁止しており、全履歴の自動復旧を追加する変更は行っていない。既存の単発delivery reconciliationを利用する復旧条件は `output/playwright/main-validation-20260929/delivery-recovery-notes.md` に記録。DB直書き・lease短縮・DLQ直接移送はしていない。

Chromeの追加起動を避ける指示以後、検証用に追加したChromeを終了し、元からあるChromeの同じPALSタブを使用している。サービスも既存のComposeサービスを再利用する。

## 証跡

ローカルの `output/playwright/main-validation-20260929/` に動画、画面、サニタイズしたAPI結果、チェック結果を保存する。生成物・ログ・認証情報はコミットしない。動画は実操作の記録であり、完了待ちの画面を成功証跡として扱わない。

- `search-source-fixed.mp4`: 修正後の検索、証明表示、Lean source開閉、狭い画面の確認。
- `selection-question.mp4`: 数式をまたぐ選択から追加質問送信まで。回答完了はこの動画には含まれない。
- `new-proof-result.mp4`: 今回の自然言語要求の検証完了、説明、Lean source表示、再読み込み。
- `formal-proof-result.mp4`: 形式的命題の検証済み説明、Lean source、再読み込み。
- `pals-main-validation.mp4`: 上記実操作を結合した約4分の動画。0:00検索・source、1:05自然言語証明、2:10形式的命題、2:45ドラッグ選択・質問送信、3:45回答表示。待ち時間を一部カット。最後の回答は品質改善前の内容であり、改善成功の証跡ではない。
- **最終版 `pals-main-validation-final.mp4`（5分52秒）**: 0:00再ログイン・Project作成、1:30検索・source、2:05自然言語証明、2:55形式的命題、3:25補足回答をドラッグして再質問、4:05修正後の長い回答スクロール、4:27Project初回送信、4:57Project証明・source・再読み込み。各実操作の抜粋を結合し、待ち時間を一部カット。生成文の表現精度に関する留保は上記のとおり。
- `approved-clarification-api.json`: 修正後の追加回答、親回答との関連、原文TeX、生成完了時刻。
- `project-api-evidence.json`: Project初回送信の証明、説明、source、Project/chatの保存先。
- `backend-recovery-evidence.json`: 中断ジョブの再開、残存未完了、復元試行回数のAPIスキーマ検証。
- `api-evidence.json`: 公開APIから読み取った証明、説明、追加質問、sourceの状態と過去の観測。

既存ユーザー変更は保持。stage・commit・push・本番deployは行っていない。
