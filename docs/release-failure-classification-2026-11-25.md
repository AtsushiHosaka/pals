# seq33〜seq41 の失敗を「どの手段なら事前に検出できたか」で分類する

作成日 2026-11-25。読み取りのみ。根拠は pals#475・#433・#379・#509・#496、pals-infra の PR、`~/pals-release-archive/seq33-20261123/` の cycle journal。

## (1) 結論

### 件数

失敗は、ledger と journal から独立した原因ごとに数えて43件です。派生した件（期限切れ、再取得の費用など）と未発生の近接事象は、件数に含めていません。

| 分類 | 件数 | 割合 | 内訳 |
|---|---|---|---|
| A rehearsal で検出できた | 17 | 39.5% | 無条件 9、条件付き 8 |
| B 本番の読み取り観測で検出できた | 9 | 20.9% | |
| C どちらも不可（外部要因・原因不明） | 8 | 18.6% | 外部要因を特定できたもの 4、原因不明 4 |
| D 検査が存在しない・手管理リストの漏れ | 7 | 16.3% | |
| 不確実（分類を保留） | 2 | 4.7% | A/B のどちらか決められない |

- 「無条件」は、既存の gate・plan に実入力を通すだけで落ちたものです。「条件付き」は、実 image、実 DB の連鎖、新しい scenario、全工程の通しが無いと見えなかったものです。
- **rehearsal だけで防げる割合は 9〜17件（20.9〜39.5%）です。** 上限の17件は、失敗を見たあとで scenario を足した場合の値で、事後の判断を含みます。
- rehearsal、本番の読み取り観測、静的な署名ゲート（A+B+D）を足すと33件（76.7%）です。
- 残る10件（C 8、不確実 2）は、事前の検査では 0 にできません。

### 防げない失敗（C）の性質

- 外部要因を特定できた4件は、capture の鮮度切れ（36-1）、モデルの出力のばらつき（39-2）、API の ReadTimeout（39-6）、CI の列と取消し（41-9）です。
- 原因不明の4件は、restore-check の exit 2（41-2）、post-request の失敗（39-5）、capture-7 の失敗（39-4）、dispatch 集合の変化（36-6）です。journal が stdout の hash と終了コードしか残さないため、原因を後から特定できません。診断すれば A か B に移る可能性があります。
- **C が新たに本番停止を起こした記録は、この範囲に無いようです。** C は切替前の観測や capture、または再起動後の観測で起きています。36-6 は、すでに停止中の復旧作業で起きており、停止への寄与を判定できません。

### 本番停止の原因はすべて A か D です

| 停止 | journal 上の時間 | 原因 |
|---|---|---|
| seq33 | 約15時間18分（deregister 11-23 10:38Z から、seq39 の register 11-24 01:56Z まで） | 33-4（D）。33-5・34-1・36-5・37-2 が復旧を長引かせた（A） |
| seq40 | 9分38秒（計画どおりの切替） | なし |
| seq41 | 2時間47分（03:31Z から 06:19Z まで） | 41-10（A）。実 API の `--check` を stand-in に置き換えていた |

なお #475 の本文は seq33 の停止を「約3時間」と書いていますが、journal の時刻とは合いません。書かれた時点（復旧中）の値と思われます。

### オーナーの問い「rehearsal で今後の失敗を 0 にできるのか」への答え

**できません。** 理由は次の4つです。

1. **A の半数以上は、失敗を見たあとに scenario を足せば見える、という事後の分類です。** 条件付き 8件のうち、41-10 は実 image の probe、41-12 は coupon 直後の forward-only の組み合わせ、41-13 は受入以降の工程を、それぞれ rehearsal が通していませんでした。rehearsal が検出できるのは、モデル化した状態だけです。候補の連鎖（通常、coupon、forward-only、software_after_coupon、…）の組み合わせは、リリースのたびに増えます。
2. **C が18.6%あります。** 分類をA〜Dで揃えたため、C の件数は、原因不明の4件を含みます。C を含むシーケンスは、対象の8シーケンス（seq33・34・36〜41）中で seq36・39・41 の3つです。小標本の参考値ですが、C だけで「2回連続で 0 件」になる確率は約4割です（(5/8)^2）。
3. **rehearsal 自体が、失敗と費用を生んでいます。**
   - 36-2: 私の rehearsal の Docker ビルドが、buildx の履歴を押し出して、本番手順の検証を壊しました。
   - 41-11: rehearsal の harness に、forward-only の plan 入力のキーが欠けていました。
   - seq41 の rehearsal は5回で、1回30〜39分でした（#509）。
   - rehearsal の記録は tooling の tree hash に束縛されるため、infra の commit が1つ変わるたびに、候補、署名、rehearsal をやり直します（署名から次の署名まで55〜114分）。
4. **同じ型の再発が7件あります（16%）。** 40-2（鎖の段数、33-3 の再発）、41-1（固定リスト、33-4）、41-3（operators dir、38-1）、40-1・41-5（必須 check、33-1）、41-4（通知窓、40-8）、39-3（予算、36-3）です。他に、seq32 の「受入 runner の hash を固定していない」（#235）と同型の 41-13 があります。1回目の対策が、その場の修正にとどまり、同種の網羅検査になっていませんでした。これは rehearsal ではなく、署名ゲートと回帰コーパスで潰す対象です。

目標を直すことを勧めます。「リリース中に初めて見つかる拒否を 0」は、C を含むので達成できません。次の3つに分けて、それぞれ別の手段で追うほうが論理に合います。

- (a) 決定的な拒否（A・B・D）の本番初出を 0 にする。
- (b) 不可逆区間（admit 以降）の失敗を 0 にする。
- (c) C による停止を 15分以内にする。

### この分析の限界

- 反事実（その手段があれば検出できたか）は、記録の文面からの私の判断です。実際に再現して確かめたものではありません。
- seq34・seq35・seq38 は cycle の journal が無く、ledger と Issue の記述だけに頼っています。
- 原因を記録が特定していないものは、「不確実」または「C（原因不明）」にしています。

#509 の本文は、seq41 の4件を「すべて、rehearsal では通り、本番で初めて拒否された」と書いています。archive と PR では次のようになります。

- 41-11（#283）は、rehearsal 自身が検出しました。rehearsal-s41d が EXIT=1 で、s41e で通っています。
- 41-12（#284）は、復旧候補の host 準備（本番 host での native_prepare）が、切替の前に検出しました。
- 本番の cycle で初めて拒否されたのは、41-10 と 41-13 の2件で、停止を起こしたのは 41-10 だけです。

---

## (2) 失敗ごとの表

凡例: 【停】本番停止に寄与、【前】切替前（本番は未変更）、【後】受入以降。「足す手段」の番号は(3)の項目です。

### seq33

| ID | Issue・PR | 何が起きたか | 分類 | 根拠 | 足す手段 |
|---|---|---|---|---|---|
| 33-1 | #475 本文1、#467、journal `cycle-attempt` | 重い CI が PR 実行で skip され、固定 commit の成功が無く source-checks が拒否【前】 | B | GitHub の check を exact commit で読む操作は読み取りだけで足りる。journal 09:58Z で source-checks が exit 2 | 3.1-a |
| 33-2 | #475 本文2、infra#234 | 新しい release ランナーに sudo が無く web-regression が失敗【前】 | D | ランナーの能力を測る検査が無かった。canary は #236 で追加 | 3.1-a |
| 33-3 | #475 本文3、infra#236 | worker の出所の鎖が3段で、上限2段に当たった【前】 | A（無条件） | 実 manifest 鎖を gate に通せば落ちる。環境に依存しない | 3.1-c |
| 33-4 | #475 本文4、journal `cycle-attempt2` | `TRUSTED_WORKER_COMMITS` に 8703aaf が無く、admit 後の compute の finalize が拒否された【停】約15時間 | D | 手管理の固定リスト。seq30 の 146ecf2 と同型。gate の `fixed_lists` が #236 で追加 | 3.1-b |
| 33-5 | #475 本文5、#433 コメント、infra#237 | admission 後に、owner 解放が両 host の health を要求し、解放できなかった（循環）【停】 | A（条件付き） | fail-after-admit の scenario が owner 解放まで通れば見える。当時は未実施 | 3.1-d |

### seq34

| ID | Issue・PR | 何が起きたか | 分類 | 根拠 | 足す手段 |
|---|---|---|---|---|---|
| 34-1 | #433 コメント（11-23 13:23Z） | 前進修復の plan が `observation_stage_operator_preconditions_not_met` で拒否された。`stage_operator` は、前任の control コンテナが全て起動中であることを要求するが、api は Exited【停】 | A（条件付き） | 「admit 済みで未稼働の前任」を rehearsal の世界に置けば再現する。forward-only の scenario は #237 で追加 | 3.1-d |

### seq36

| ID | Issue・PR | 何が起きたか | 分類 | 根拠 | 足す手段 |
|---|---|---|---|---|---|
| 36-1 | #475 コメント（16:19Z） | capture-3 が鮮度の3600秒を超過【前】 | C | 時間経過。人の待ちと失敗の連鎖による遅れ。回避は工程順（capture を直前に取る） | 3.2 |
| 36-2 | 同上 | 私の rehearsal の Docker ビルドが buildx の履歴を押し出し、`--verify-receipt` が失敗【前】 | B | 検証器の受領書の検査は読み取りで実行できる。**rehearsal 自身が原因** | 3.1-a |
| 36-3 | 同上 | ローカル予算の残りが 143,536 µUSD で、1回の capture の予約額に足りない恐れ【前】 | B | 予算台帳は読み取りで、残りと予約額を比べられる | 3.1-a |
| 36-4 | journal `cycle-attempt2-s36` | claim が `private_owned_ledger_directory_required` で拒否【前】 | 不確実（B 寄り） | 原因の記録が無い。推論: 未使用の ledger-s34/s35 は 0755、s36 以降は 0700。ledger の権限だった可能性 | 3.1-a |
| 36-5 | #475 コメント（17:00Z）、infra 60044f6 | forward-only で、TLS 再利用記録の前任（seq32）と admitted の前任が不一致、`reused_pki_lineage_invalid` で finalize が拒否【停】 | A（条件付き） | 3段の鎖と forward-only を rehearsal の世界に作れば再現する | 3.1-d |
| 36-6 | journal `cycle-attempt3-s36` | `mutating_dispatch_set_changed_during_safety_observation` で admission-status が失敗（既に停止中） | C（原因不明） | 記録なし。観測中に SSM の dispatch 集合が変わった、という拒否コードのみ | 3.2 |

### seq37・seq38

| ID | Issue・PR | 何が起きたか | 分類 | 根拠 | 足す手段 |
|---|---|---|---|---|---|
| 37-1 | #475 コメント（17:33Z） | `alerts-preflight` が `alarm_already_in_alarm` で停止（17:08Z の 503 を 5xx アラームが拾っていた）【前】 | B | アラーム状態は読み取りで見られる。直前の停止の副作用 | 3.1-a |
| 37-2 | 同上 | 未 admit の owner を解放する経路が無く、置き換えツールを拡張【前】 | A（条件付き） | fail-before-admit の scenario が owner 解放まで通れば見える | 3.1-d |
| 38-1 | 同上 | host 準備で operators ディレクトリが衝突し、seq38 を捨てた【前】 | D | 「再署名には新しい infra commit が要る」は #225（11-21）で既知。強制する検査が無かった | 3.1-b |

### seq39

| ID | Issue・PR | 何が起きたか | 分類 | 根拠 | 足す手段 |
|---|---|---|---|---|---|
| 39-1 | #433 コメント（11-24 02:25Z） | plan の `previous_*` の取り違え（seq36〜39 のどこで見つけたかは不確実）【前】 | A（無条件） | plan の生成と検証は決定的で、rehearsal の plan 段で落ちる | 3.1-c |
| 39-2 | #475 コメント（17:33Z） | capture-5 が Lean 検証で失敗（同じ問題・同じ image で、capture-3・4 は通っていた）【前】 | C | モデルの出力のばらつき。事前観測では分からない | 3.2 |
| 39-3 | #475 コメント（01:25Z） | capture-6 が約3秒で失敗。残予算 58,298 µUSD が terra の予約額（約62,000〜65,500）を下回る【前】 | B | 台帳を読めば、予約額との大小が分かる | 3.1-a |
| 39-4 | #433 コメント | capture-7 が失敗（原因の記載なし）【前】 | C（原因不明） | 記録なし | 3.2 |
| 39-5 | #433 コメント、journal 01:58Z | cycle の `post-request` が exit 2（実際の応答は約93秒で成功）【後】 | C（原因不明） | journal は stdout の hash のみ。応答が約93秒かかるため、step の待ち時間の上限の可能性があるが未確認 | 3.2 |
| 39-6 | journal 02:01Z | reconcile の admission-status が `ReadTimeoutError`【後】 | C | 外部 API の一時的な失敗 | 3.2 |

### seq40

| ID | Issue・PR | 何が起きたか | 分類 | 根拠 | 足す手段 |
|---|---|---|---|---|---|
| 40-1 | #475 コメント（seq40 結果）、pals#499、journal 11:37Z | 親の候補 commit に必須 check が無く（PR が無いと repository-safety が付かない）source-checks が拒否【前】 | B | GitHub の check の有無は読み取りで分かる | 3.1-a |
| 40-2 | infra#238 | worker の鎖が4段で、上限2段に当たった【前】 | A（無条件） | 33-3 の再発。gate に実 manifest 鎖を通せば落ちる | 3.1-c |
| 40-3 | infra#239 | 通常配備なのに、復旧 permit 系を gate が要求。session は refresh の実測に合わせる必要【前】 | A（無条件） | plan の種別と gate の条件の食い違い。gate の通し実行で落ちる | 3.1-c |
| 40-4 | infra#240 | `fence_present` と `broker_reachable` の観測に値が無い【前】 | 不確実（A/B） | fence は observer の hash 対象の追加（host の観測が要る）。broker は plan の種別。docker の host 模擬が observer を通すかは未確認 | 3.1-a、3.1-d |
| 40-5 | infra#241（sudo） | sudo が不要な job しかないのに、gate が sudo を必須にしていた【前】 | A（無条件） | gate の条件が実際の workflow と合っていない。決定的 | 3.1-c |
| 40-6 | infra#241（SSO） | SSO の残り時間が窓に足りない【前】 | B | 実トークンの期限は、読み取りで分かる | 3.1-a |
| 40-7 | infra#244（#243 は取下げ） | gate が IAM の窓に95分を要求するが、IAM の承認は45分以内で、両立しない【前】 | A（無条件） | 定数同士の矛盾。環境に依存しない | 3.1-c |
| 40-8 | #475 コメント（通知枠）、journal `cycle-attempt2-s40` | 通知枠600秒に対し、実測793秒で `release_alert_window_overrun`。cycle は failed【前〜後】 | D（C 成分あり） | 過去の実測（seq29 の847秒、#379）があるのに、窓を実測から決める検査が無かった。SSM 待ちのぶれ（456〜793秒、1.7倍）は C | 3.1-b、3.2 |

### seq41

| ID | Issue・PR | 何が起きたか | 分類 | 根拠 | 足す手段 |
|---|---|---|---|---|---|
| 41-1 | pals-infra#277、#475 台帳1 | `TRUSTED_WORKER_COMMITS` に f9c69f21 が無く、gate が拒否。署名後の候補を作り直し（約1時間）【前】 | D | 33-4 の再発。#475 の教訓が手順に入っていなかった。`precheck41.py` が事後に作られた | 3.1-b |
| 41-2 | #475 台帳2、pals-infra#279 | cycle 1回目の `restore-check` が exit 2【前】 | C（原因不明） | journal は stdout の hash のみ。SSM 3件は成功で、直後の `inventory()` の拒否と推定（rate limit の可能性） | 3.2 |
| 41-3 | pals-infra#278、#475 台帳3 | owner token は1回限りで、host-prepare は同じ infra commit で再実行できない。cycle が1回失敗すると、infra に新しい commit が要る【前】 | D | #225 で既知。強制する検査が無い（38-1 の再発） | 3.1-b、3.2 |
| 41-4 | #379（11-25）、#475 台帳4 | 通知枠の上限600秒（gate の表）に対し、plan の1200秒が拒否された【前】 | A（無条件） | gate の表の拒否。決定的。オーナー判断で600秒のまま、cycle は overrun で failed になりうる（40-8 と同じ原因） | 3.1-b |
| 41-5 | #475 台帳5、#496 | api の必須 check が候補 commit に付かない（PR の run は skipped）。workflow_dispatch の run を採用【前】 | B | 33-1・40-1 と同型。GitHub の読み取りで分かる | 3.1-a |
| 41-6 | #475 台帳6、#496 | api の差分の `reviewed_paths` を宣言する必要（19ファイル、のち23）【前】 | D | 手で宣言するリスト。差分から導出できる | 3.1-b |
| 41-7 | #475 台帳7、#506 | SSO が約8時間で失効（interactive 1 day の設定が CLI のトークンに効かなかった）【前】 | B | トークンの `expiresAt` は読み取りで分かる。設定が効くという仮定が誤り | 3.1-a |
| 41-8 | #475 台帳8、pals-infra#249 | stage コマンドが上限62000バイトに近く、余裕が1,024バイト。復旧系 PR #221〜224 を閉じた【前】 | A（無条件） | 実サイズの検査（#228）が検出した。決定的 | 3.1-c |
| 41-9 | #475 台帳8、pals-infra#247 | 重い CI の列（ランナー2台）と、dispatch の run が push で取り消される concurrency【前】 | C | CI の資源と GitHub の挙動。静的に見える concurrency の取消しを除く | 3.2 |
| 41-10 | #475（切替の障害）、pals-api#152 | **新 API の `cloud_restore_runtime --check` の許可リストに、coupon append の carrier が無く、admit 後の gate が exit 2。activate-control が失敗**【停】2時間47分 | A（条件付き） | 実 image の `--check` を、実 manifest・36段 DB で走らせれば再現する。rehearsal の probe が stand-in で、一度も走っていなかった。許可リスト（手管理）の漏れでもある（D 併記） | 3.1-d、3.1-e |
| 41-11 | pals-infra#283 | rehearsal の forward-only の harness が、plan 入力のキー（`runtime_predecessor_manifest`）を欠いていた【前】 | A（無条件） | **rehearsal 自身が検出した**（rehearsal-s41d が EXIT=1）。rehearsal の欠陥 | 3.1-d |
| 41-12 | pals-infra#284 | native_prepare が、forward-only の旧ランタイムを coupon の形式で検査していた【前】 | A（条件付き） | 「coupon の直後の forward-only」の scenario（PR で `coupon-forward-only-after` を追加）で再現する | 3.1-d |
| 41-13 | #475 追記、#509 | plan 入力に `native.acceptance_runner` が無く、受入後の観測が「未解決」と判定され、release-owner が例外で owner を保持【後】 | A（条件付き） | cycle の終端（release-owner の解放）まで rehearsal が通れば見える。seq32 の #235 と同型。mkplan が必須にしていなかった | 3.1-d |
| 41-14 | #510 | reconcile の試行行が追記された後、`record_owner_release` が owner の解放を追記できない【後】 | A（条件付き、不確実） | 失敗後の recovery を通す scenario で見える。journal の最終行の前提は、ツールを読めば分かる | 3.1-d |

### 件数に含めないもの

- **派生**: capture と freeze の期限切れ（seq40 で2回）、subject 変更のたびの capture の取り直し（seq40 で5回、予算の rollover）、署名前の人の待ち（6時間49分と22分。#509、推測）。
- **未発生の近接事象**: pals-infra#282 が塞いだ穴（`assemble` が coupon の predecessor を複製し、不正な候補が `verify-unsigned` を通りうる）。署名後の admit で初めて落ちる型で、実際には候補 B を署名する前に見つかっています。

---

## (3) 「0 件」を目標にする場合に必要な手段

効果の見積もりは、上の分類にもとづく私の推定です。未測定です。

### 3.1 rehearsal 以外で A・B・D を詰める手段

**a) 署名前の本番の読み取り観測を、1コマンドにまとめる（#513、B 9件と D の一部）**
次の項目を、署名の前に一括で観測します。いずれも読み取りだけです。

- 必須 check を exact commit で確認する。workflow_dispatch の run の head_sha を含む（33-1、40-1、41-5）。
- ランナーの能力を測る canary（33-2）。
- 検証器の受領書（buildx ref）の検証（36-2）。
- 予算台帳の残りと、1回の予約額の比較（36-3、39-3）。
- アラーム状態（37-1）。
- SSO トークンの `expiresAt` と、計画の所要の比較（40-6、41-7）。
- host の operators ディレクトリの衝突と、ledger の権限（38-1、36-4、41-3）。

署名の後ではなく前に検出することが要点です。署名後の検出は、1件につき候補の作り直し（約1時間）に直結します。

**b) 手管理リストを導出か網羅検査に置き換える（D 7件）**

- `TRUSTED_*` を、候補 manifest に含まれる全 commit と全 digest に対して照合する（`precheck41.py` を署名ゲートに入れる）（33-4、41-1）。
- 全 carrier を全 allowlist に対して検査する（pals-api#152 で導入済み）（41-10 の D 側）。
- `reviewed_paths` を、差分から導出する（41-6）。
- 通知枠は、過去 journal の実測の最大値から1.5倍で計算し、gate の上限表と矛盾する値を、署名前に拒否する（40-8、41-4）。793秒×1.5 は約1200秒（#475 コメント）。上限600秒は自前の定数です。
- infra の commit と host-prepare の対応を、新しい commit が要る場合に署名前に判定する（38-1、41-3）。

**c) gate と plan を実入力で通し、失敗の回帰コーパスにする（A 無条件 9件。seq42-B）**
この表の A・D を、変異テストにします。受け入れ基準は、許可リストから1件外すか、定数を1つ変えると落ちることです。同型の再発7件（上の(1)）が対象です。

**d) rehearsal を、実形と全工程に近づける（A 条件付き 8件。#511、#509 の #5）**

- 実 API image の probe、使い捨て PostgreSQL、実 migration、候補の carrier の admission 行。
- 受入と release-owner の解放まで通す（41-13、41-14）。
- 失敗後の recovery（fail-after-admit、fail-before-admit、forward-only）の scenario。
- 候補の連鎖の組み合わせ行列。ただし、組み合わせは増え続けるため、「全パターン」は約束できません。新しい種類の候補（例: coupon の次の候補）が出るたびに、scenario を足す運用が前提です。

**e) 不可逆な操作の前に、本番の状態を読むだけの shadow を足す（41-10 型への唯一の B 手段）**

- 提案: admit の前に、候補 image の `--check` 系 probe を、本番の現行 manifest と DB の admission 連鎖の読み取りだけを入力にして実行します。
- 実現可否は**未確認**です。probe が admit 済みの状態を前提にするなら使えません。その場合の代替は、Aurora の clone 上での実走ですが、費用と権限は未確認です。

**f) admit の後に失敗しても、停止を短くする（A・D の被害の上限）**
admit の後は前の版に戻せません（forward-only）。署名と rehearsal まで済ませた前進修復の候補を待機させます（#509 の #13、復旧165分から60分以内を目標）。

### 3.2 C の失敗を短い停止で済ませる手段

- **切替前の C（41-2、41-9、39-2、36-1）**
  - 読み取りの観測は、有界の再試行をする（Throttling 向けの再試行は #222 で導入済み）。
  - 失敗した step の stdout の先頭を journal に残す（pals-infra#279）。
  - 再試行のたびに候補を作り直さない。owner token の再発行と、docs だけの commit の記録再利用（seq42-E）を入れる。
  - capture は freeze の直前に取り、予約額の2倍の余裕を予算に持たせる。モデルのばらつき（39-2）に備えて、再試行の枠を事前に確保する。
- **切替後の C（39-5、39-6）**
  - 読み取りの観測は再試行する。変更を伴う操作は再送しない（既存の方針）。
  - 受入と post-request の失敗を、cycle の結果（failed）と分けるかどうかは、成功の定義を変えるため、オーナーの判断事項です。
- **停止そのものの短縮**
  - deregister から register までの停止は、seq40 が9分38秒でした。SSM の待ち（admission-status 1回あたり90〜130秒）が主因です。
  - 待ちの回数を減らし、停止前にできる準備を終えます。目標は15分以内（#509 の #9）です。
- **原因不明の C を減らす**
  - controller の例外に closed code を残し、journal に step の待ち時間と stdout の先頭を記録します（#514）。
  - これで、C の原因不明4件を A か B に移せる可能性があります。

### 優先順位（私の推定）

1. 署名ゲート（3.1-a・b）。B と D の16件を、署名前に検出します。コストが最も低く、署名後の作り直しを減らします。
2. 回帰コーパス（3.1-c）。同型の再発7件を潰します。
3. rehearsal の実形化（3.1-d）。ただし「0 件」の保証にはなりません。
4. 前進修復の待機（3.1-f）。A・D が漏れた場合の停止時間の上限になります。
5. 3.1-e は、実現可否の確認が先です。

---

機械可読の台帳（失敗の id、分類、拒否する段）は pals-infra の `tests/regression_corpus/ledger.json`。この文書の表と `ledger.json` の A・D の行は、回帰コーパスの網羅検査（pals-infra `test_corpus_index.py`）が突き合わせる。親: pals#509、seq42-B。
