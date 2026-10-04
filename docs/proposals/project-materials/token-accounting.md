# 利用トークン会計の API 接続案

2026-09-30。実装前の設計案。料金枠・重み・外部サービスの現在価格を確定する資料ではない。
ユーザーの D11/D12 決定と現行コードの読み取りに基づく。DB 適用・外部 API 呼び出しは行っていない。

## 確定した扱い

- 原価に応じた重み付き利用トークンを使い、開始前に最大消費量を表示する。
- 成功した要求の生成・修復・QA・説明を含む全工程を対象にする。
- 説明と独立 QA が成立して初めて顧客の消費を確定する。失敗は消費ゼロ。
- 再配送や説明の再表示は二重消費しない。説明再試行は独立した operation/cycle とする。
- 既存の回数予約、過去の失敗、原価記録は書き換えない。新ポリシーは新規 operation のみ。

## 現行コードとの隔たり

| 境界 | 現在 | 新契約で必要な変更 |
|---|---|---|
| 受付 | `billing_admission.reserve` が Free 3 / Pro 100、1 job 1 reservation を即計数 | quote に結び付く可変 cap の hold。gross 採番を net 残量から分離 |
| 残量 | `billing_operations.summary` と `billing_postgres.get_summary` が予約件数を used とする | token の consumed / reserved / available。回数との混合加算禁止 |
| usage | `billing_operations.usage` は有効な generation claim だけを受理 | 工程別の durable permit。保存済 permit に対する exact receipt の遅延再送 |
| usage 冪等性 | 現行 `usage` は既存 call_id 比較より先に claim 期限を検査 | 既存 receipt の完全一致 replay を先に処理。新規・不一致の期限後挿入は拒否 |
| 他工程 | semantic QA / explanation / clarification / Recipe QA 等に欠測。embedding/reranker も完全な精算源ではない | 全対象 provider call を呼出し前 permit と後続 receipt に接続 |
| 説明再試行 | `explanation_retry.request_explanation_retry` が新 retry/outbox を作成。課金 hold なし | 新しい quote と現時点の枠を transaction 内で確保してから配送 |
| 終了 | proof と explanation が別々に終端化 | 独立 QA 済み説明と完全な usage の両方を用いた一度限りの精算 |

未接続だった `004_explanation_consumption.sql` と `billing_quota.py` は今回作成した初稿だけを削除した。
その案は固定 3/100、units=1、hold 全量消費、旧件数と新 units の加算を含み、この契約には使用できない。
元の migration、公開 API、稼働台帳には変更を加えていない。

## 単位の提案と計算

親タスクからの提案は「1 利用トークン = USD 0.75 / 1,000,000 相当」、mini 入力 1 / cached 入力 0.1 / 出力 6。
これは提案値であり、本資料では現在の公式価格として検証・採用していない。月額の付与量も未決。
他モデルは同じ基準へ換算し、operation に immutable weight/price snapshot を固定する。

計算は浮動小数点を使わず、各 call の整数 token 数 × 有理数重みを合計し、operation 全体で最後に一回だけ切り上げる。
入力総数に cached、出力総数に reasoning が含まれる場合は内数として扱い、二重加算しない。
画像等の provider usage の内訳が異なる場合は、対応済み capability と計算法を明示するまで有料 token operation を有効化しない。
provider 原価台帳と顧客利用トークン台帳は別に保持する。

## 最小 API 契約案

### Quote と開始

`POST /billing/quotes` は認証 owner、action (`proof` / `explanation_retry` / `clarification`)、要求内容、希望 cap を受け取る。
API が canonical request fingerprint、policy/weight/runtime-capability version、期限を保存し、
`quote_id`, `expires_at`, `max_utilization_tokens`, `policy_version`, `unit` を返す。
quote は残量を予約しない。表示時の残量は開始を保証せず、開始 transaction で再検査する。
入力、説明の失敗版、cap が変われば再 quote。quote 作成だけでモデルを呼ばない。

既存 proof POST / explanation retry POST / clarification POST に quote_id を渡す。owner account → operation/proof の lock 順を統一し、
owner、fingerprint、期限、policy、現 entitlement と available を検査する。
hold(cap)、operation、job/retry、outbox、idempotency receipt は同一 transaction で確定する。
不足時はこれらを一つも作らない。exact idempotency replay は quote 期限切れ後も元の受付結果を返し、新規受付をしない。

### Call permit と durable receipt

外部呼出し前に `operation_id + call_id` を登録し、stage、provider/model、設定 digest、入力/出力上限、
claim/candidate/source binding、worst-case weighted amount を不可変に保存する。
permit は顧客 cap 内の予算を取り置き、並列呼出しの合計も拘束する。
入力 token の上限は provider が実際に送信する全 payload と画像等を含む必要がある。
上限の確かな計算法がないモデル/入力形式は未対応とし、表示 cap だけで課金可能にしない。
追加 permit が取得できなければ外部呼出しをせず、その operation を上限到達失敗として扱う。

権限境界は既存 generation claim を拡張流用しない。
generation/retrieval は有効 generation claim、semantic QA は candidate/source/session、
explanation は explanation claim と親証明/内容 binding、Recipe QA は専用 reviewer identity に結び付ける。
clarification は今回の全工程計測対象であり、専用 operation と既存 clarification claim、参照する説明版と選択範囲hashへ結合する。

完了 receipt は call_id に一度だけ、closed usage / outcome / response identity を保存する。
保存済 permit と receipt が完全一致する遅延 replay は claim 期限後も許可できるが、別内容、別 owner、
未登録 call の期限後注入は拒否する。新 claim を偽装して再送しない。
DB 応答喪失を provider 再実行で解決しない。provider 呼出しの exactly-once は仮定しない。
permit 登録後のクラッシュや provider timeout で実行有無/usage が不明な call は unknown とする。

### 終端と再試行

proof/説明retryの消費条件は `explanation completed + 独立 approved QA/hash binding + 全対象 call の確定`。
clarificationの消費条件は `回答completed + 独立回答QA承認/context hash binding + 全対象callの確定`。追加質問も自分の見積上限内で独立精算する。
actual weighted sum を消費し、cap との差額を元の scope/period に解放する。
成功を確定するまで cap を超える call は許可せず、未知の usage をゼロにして精算しない。
証明 failed/canceled、説明 failed、解決不能な usage unknown は顧客消費ゼロで hold を解放する。
その際も実原価と unknown 記録は残す。未知の provider 原価をゼロと表示しない。
解放後に receipt が到着しても失敗 cycle を消費へ変更しない。

usage 後着時の取りこぼしを防ぐため、terminal 更新と durable finalization wakeup を同じ transaction に入れる。
説明完成後に usage が未確定なら会計 pending として明示する。unknown の解決期限後は消費ゼロで閉じる。
学習用の正しい証明/説明を会計エラーで false に書き換えず、billing outcome を別に持つ。
遅延 receipt の回復期限と利用者への pending 表示は実装前に明記する必要がある。

一 proof の successful consumption は最大一つ。説明再試行は、新 quote/new hold をその時点の有効 scope で取得する。
旧失敗 cycle の原価は新 cycle に足さず、再試行した説明/QA 工程の成功時だけ精算する。
既に成功した内容の再表示・通知・同 receipt 再配送で追加消費しない。
元 hold を期間またぎで成功精算しても元 scope のまま。失敗で旧期間を解放しても次期間へ credit は作らない。

### Summary と設定

旧 flat 回数 fields は互換表示用に隔離し、新 token 情報と混ぜない。
新 summary は `accounting_policy`, `unit`, `policy_version`, `weight_snapshot_id` と、
scope ごとの `limit`, `consumed`, `reserved`, `available`, `period_end` を公開する案。
`available = max(0, limit - consumed - reserved)`。値の単位は全て customer utilization token。
必要なら最近の operation の cap/actual/status を別ページング API で表示し、private QA や provider payload は公開しない。

## 接続ファイルと実装順序

1. 新しい billing domain/schema/migration: policy/weights/capability、quote、operation、hold、call permit/receipt、settlement、finalization outbox。
   `app/domain/models/billing_runtime.py`, `app/schemas/billing.py`, `app/db/migrations/billing/`,
   `app/release/individual_billing_migration.py`。既知旧 schema からの additive upgrade と runtime 権限/readiness を実 PG で検証。
2. API の新会計 repository/service/routes と全 provider metering の耐久化を先に完成させる。
   `app/api/routes/billing.py`, `app/infrastructure/repositories/billing_operations.py` および分離した新モジュール。
   worker/agent は別担当 slice が必要。現在の usage v1 は旧契約のまま残す。
3. `billing_admission.py` と `postgres.py::_create_with_outbox` に quote/hold を接続。
   `explanation_retry.py::request_explanation_retry`、`postgres.py::_acquire_explanation` で retry hold と旧 receipt の無課金再生成を防ぐ。
4. `postgres.py::_finish_explanation` と `_insert_proof_job_event` に同一 transaction の終端通知を接続。
   candidate の中間 compile failure は proof terminal ではないため解放しない。
5. summary/quote/start UI と設定画面を接続し、全工程の real-dependency test 後に有効化。

local を含め `token_accounting_enabled=false` を初期値とする。未対応工程があるときは quote/start を unavailable で拒否し、
新ポリシーを広告・表示しない。既存 operation の処理と旧 usage は継続する。
有効化時は単なる flag だけでなく、schema readiness と全対象 stage の metering capability version を照合する。
付与枠と重みが未設定なら起動時または当該 capability の readiness を fail closed にする。

## 必須検証範囲

- unit: 最後に一回だけ ceil、cached/reasoning 内数、重み snapshot 固定、負数/bool/桁上限/unknown model 拒否。
- 実 PG: 同 owner 同時 start の超過拒否、別 owner 分離、quote 改変/期限切れ、同 key replay、同 call の重複/不一致、transaction rollback/commit unknown。
- 実 PG: 初期 hold → actual 消費/差額解放、proof/説明失敗ゼロ、旧履歴不変、期間またぎ、retry 新期間、retry 不足時副作用ゼロ。
- 結合: 呼出し前 permit がない全 provider call を禁止、cap 内の並列配分、未知 receipt のゼロ精算禁止、期限後 exact replay、クラッシュ後の二重 provider 呼出し防止。
- 結合: valid QA だけでは meter 未確定を成功精算しない、meter 完了だけでは未検証説明を消費しない、一 proof の重複消費なし。
- release: 既存実 DB は専用 disposable schema/database だけを使う。learner rows、Stripe、価格設定、本番 flag はテストから変更しない。

## 未確定・未実装

価格枠の数量は2026-09-30に暫定値を承認（Plus月100万／依頼10万、Pro月300万／依頼30万、Research月1,500万／依頼150万）。本番のweight最終値、資料処理枠、unknownの運用回復期限は未確定。
最小案は一 operation 一 scope とし、scope 合算は自動で行わない。資料前処理の読取り枠と失敗精算案はdesign.mdの取込operationを参照し、生成token台帳とは分ける。
2026-09-30に自然言語回答経路へquote→予約→provider permit→usage receipt→独立QA→成功時精算のAPI/DB/agent接続を追加した。local opt-in限定。正式証明・部分質問・説明再試行・資料取込・inline画像はこの計測へ未接続で、新USDプランの未計測生成経路は停止する。全提案の実装完了ではない。旧回数台帳は分離して維持する。
