# #433 ローカル資格確認の累積予算を2 USDにする（2026-11-21）

seq31（#433）のローカル資格確認が、課金なしで失敗しました。provider proxyの累積上限（1 USD）に達していたためです。過去のclosed台帳のreserved 310668μUSDと現在の台帳631517μUSDで合計942185μUSD、残り57815μUSDでした。次のTerra予約（最大65360μUSD）が残りを超えるので、proxyは台帳を変えずに拒否しました。ワーカーには`openai.error`として見えました。

台帳は健全（blocked=false）で、rolloverは健全な台帳を拒否し、累積allowanceは補充しません。上限の変更には、guardのコード定数の変更が必要でした。

2026-11-21にオーナーが、#433に限り1 USDの上限を考えない方針を承認し、累積上限の引き上げを選びました。`CUMULATIVE_LIMIT`を1000000から2000000μUSDにしました。各期の上限`LIMIT`（700000μUSD）、rolloverの仕組み、台帳の追記のみの扱いは変えていません。既存のclosed台帳と現在の台帳は書き換えていません。

境界の回帰テストは、元の1 USDの算術を固定するため、そのクラスだけ定数を1000000にパッチします。本番値が2000000であることは別の1件で確認します。この承認は#433だけが対象です。次回以降のリリースで広げる場合は、別の承認が必要です。

## 追記: 各期の上限も2 USDにする

累計上限を上げた後の取得で、各期の上限700000μUSDが次の障害になりました。1回目の取得（Lean検証失敗）で643191μUSDを使った後、次のTerra予約62758μUSDが各期の上限を超え、proxyが台帳を変えずに拒否しました。台帳は健全で、rolloverは使えません。

2026-11-21にオーナーが、各期の上限も引き上げることを承認しました。`budget_proxy.py`の`LIMIT`と、状態チェック`local-qualification.py`の`FIXED_LIMIT_MICROUSD`を、どちらも2000000μUSDにしました。この2つは同じ値でなければならず、テストで確認します。台帳の追記のみの扱いと、rolloverの仕組みは変えていません。

## 追記2: 健全な台帳の上限を、承認付きで引き上げる

`LIMIT`と`FIXED_LIMIT_MICROUSD`を2000000にしても、rollover済みの台帳は承認ファイルの`new_limit_microusd`（700000）で上限が固定されるため、反映されませんでした。台帳は健全なので、rolloverも拒否されました（`rollover_healthy_ledger_refused`）。台帳と承認ファイルを手で書き換える案は、承認への束縛を壊すため採りませんでした。

2026-11-21にオーナーが、rolloverのソース改修を承認しました。`require_rollover_eligible`は、呼び出しを1件以上行った健全な台帳で、上限が現在の`LIMIT`より小さいものに限り、オーナー承認付きのrolloverを許します。閉じた台帳はバイト一致でarchiveし、累計は引き継ぎます。何も初期化しません。呼び出しのない台帳と、上限が`LIMIT`に達している健全な台帳は、これまでどおり拒否します。

## 追記3: 累計上限をUS$5にする（seq42、2026-11-27）

seq42のローカル認定の準備で、閉じた台帳の累計予約が1498403μUSD、`CUMULATIVE_LIMIT`が2000000μUSDで、生涯の残りは501597μUSD（約US$0.50）でした。現在の台帳の各期の上限をUS$1にしても、実際に使える額はUS$0.50のままで、候補AとSの認定2本には足りますが、取り直しには足りません。

2026-11-27にオーナーが、ローカル認定の累計上限をUS$5に上げることを決めました（pals#509で司令塔が連絡）。`budget_proxy.py`の`CUMULATIVE_LIMIT`だけを2000000から5000000μUSDにしました。各期の上限`LIMIT`と`local-qualification.py`の`FIXED_LIMIT_MICROUSD`は2000000のままです。rolloverの仕組み、台帳の追記のみの扱い、閉じた台帳の累計の引き継ぎは変えていません。既存の台帳は書き換えていません。

影響範囲:

- `CUMULATIVE_LIMIT`を読む場所は、`Budget.reserve`の1か所だけです。本番のリクエスト、他の台帳、各期の上限、rolloverツール、`budget_handoff.py`、`lane_application.py`、`local-qualification-prepare.py`は、この定数を使いません。各期の上限`LIMIT`との比較は、`LIMIT`だけを見ます。
- 台帳のファイルに累計上限は書かれません。台帳の検査（`validate_rollover`、状態チェック）に、累計上限との整合を見る箇所はありません。
- `budget_proxy.py`のsha256は、guardのimage（`Dockerfile`が`guard.py`と`budget_proxy.py`をコピーする）と、subjectの`guard.source_sha256`に入ります。この変更で`budget_proxy.py`のhashが変わるため、guard imageの再build、subject（`local-qualification-freeze-lane.py`／`local-qualification-prepare.py`が作る）の作り直し、起動中のguardの入れ替えが必要です。台帳そのものは変わらないので、台帳のhashは変わりません。
- この変更の前に作ったsubject、またはこの変更の前のimageで動いているguardは、`guard_source_changed`で拒否されます。

回帰テストは、実際の定数のまま実物の`Budget`を通します。閉じた累計が約US$1.5の台帳で、旧上限（US$2）では拒否された予約が通ること、閉じた累計US$4の台帳で累計がちょうどUS$5に達した次の1μUSDが、各期の枠に余裕があっても累計上限で拒否されること、さらにrolloverを重ねても累計が補充されないことを確認します。
