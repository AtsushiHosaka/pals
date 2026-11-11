# Lean の並列 compile 数とメモリの実測（2026-11-11）

- 指標: 時間（主）。10同時利用で30秒以内、2候補競争を現実にする土台
- 仮説: verifier は1 compile ずつ（2 CPU / 4 GiB）で、2候補の競争は直列になる。スロットを増やせば待ちが減る。
- 変更: スロット数・CPU・メモリを検証つきの設定にした（既定は不変）。pals-infra PR #153（[リンク](https://github.com/AtsushiHosaka/pals-infra/pull/153)）、pals-agent PR #111（[リンク](https://github.com/AtsushiHosaka/pals-agent/pull/111)）。いずれも draft、未配備。
- Issue: #137

## 今の仕組み（読んで確認）

- 1 compile ずつの強制: `pals-agent` の `http_server.py:51`（`MAX_CONCURRENT_COMPILES = 2` が上限）、`:207`（`BoundedSemaphore(設定値)`）、`:283`・`:351`（非ブロッキングで取得できないと 503。**待たせずに断る**）。スロット数の環境変数は `http_runtime.py:190-197`（`PALS_LEAN_MAX_CONCURRENT_COMPILES`、既定1）。
- 上限は `http_server.py` にあるので、3〜4スロットに上げるには `MAX_CONCURRENT_COMPILES` の変更が必要（同ファイルは Codex が編集中のため、パッチを PR #111 の説明に書いた）。
- 待ち行列は verifier 側にない: スロットが埋まっていると `verifier_unavailable`（503、`retryable=True`）を即座に返す（`http_server.py:283-285`、recipe 登録は `:351-`）。呼び出し元は reconciler で、同時検証数は `PALS_RECONCILER_MAX_CONCURRENT_VERIFICATIONS`（infra `control_runtime.py`、既定1、許可値1〜2）。**reconciler 本体と再試行の挙動は pals-api にあり、この worktree では submodule がなく読めていない（未確認）。**
- コンテナの上限: `pals-infra/host/private-runtime/compute_runtime.py` の `--cpus 2`（従来 `:714`）、メモリは `RETAINED_VERIFIER_MEMORY = 4 GiB`（`:267`）、レビュー済み source は `REVIEWED_VERIFIER_MEMORY = 8 GiB`（`:268`、`:614-617`）。スロット数は `VERIFIER_COMPILE_VALUES`（従来 `{1,2}`、`:246`）。agent 側の起動時 attestation も CPU 2、メモリ 8 GiB を上限にしていた（`boundary.py:9-14`）。
- `private_compute_capacity_mode`（`terraform/production/private_compute_operator.tf:5,72`）: `normal`=r8a.large、`event`=r8a.xlarge のインスタンス種別を切り替えるだけ。コンテナ上限とスロット数は変わらない。

## 測定の条件

- 実 Lean（固定版 4.32.0-rc1、Mathlib、`pals-reliability-verifier:189b44378e6e` の同梱ワークスペース。lake-manifest は repo と一致）。モデル呼び出し0回、費用0。
- 題: `pals-agent/testdata/*/proofs` の検証済み30件から10件（`import Mathlib` が重い5件と軽い5件、2〜32 s 級まで）。同一の10件を全腕で使用。`lake env lean --threads=1`（本番と同じ引数）。
- 腕: コンテナを `--cpus`/`--memory`（swap 同値）で本番の形に絞る。A=2 CPU/4 GiB/1スロット（今）、A8=2/8 GiB/1、B=2/4 GiB/2、C=2/8 GiB/2、D2=4/16 GiB/2、D4=4/16 GiB/4。各腕3回（全腕を交互に3周）、毎回新しいコンテナ。
- 各回: 単独10件、K件同時の burst を3ラウンド、10件キュー（K スロットで消化）。
- 負荷: **Mac の1分負荷平均は 10〜20（他セッション）。基準の6以下を30分待ったが 11.8 までしか下がらず、そのまま測った。** 各回の前後の負荷は `results.jsonl` に残した。Docker VM は 18 CPU / 15.7 GiB。
- 追加: 腕ごとの cold 測定（VM の page cache を毎回捨ててから開始、2回、A/B/C/D4）。

## 結果1: warm（page cache が既に載っている状態、3回）

| 腕 | 単独 p50／p90 | 同時 burst: 1本の時間／最初の完了／全部完了 | 10件キュー: 完了まで／件数毎分／10件目の待ち | 匿名メモリのピーク | OOM |
|---|---|---|---|---|---|
| A 2CPU/4G/1 | 4.6／31.6 s（各回のp50 3.9〜18.0） | — | 34.9〜229 s／2.6〜17.2／31.9〜222 s | 0.47 GiB | 0 |
| A8 2CPU/8G/1 | 4.2／6.6 s | — | 35.6〜46.6 s／12.9〜16.8／32.8〜43.0 s | 0.47 GiB | 0 |
| B 2CPU/4G/2 | 4.7／5.8 s | 3.6〜4.1／2.3〜2.6／4.9〜5.6 s | 19.2〜22.2 s／27.0〜31.2／15.3〜17.2 s | 0.66〜0.70 GiB | 0 |
| C 2CPU/8G/2 | 3.8／5.8 s | 3.7〜4.0／2.3〜2.5／5.0〜5.6 s | 20.4〜24.9 s／24.1〜29.5／16.0〜19.8 s | 0.68〜0.69 GiB | 0 |
| D2 4CPU/16G/2 | 4.7／6.8 s | 3.7〜4.9／2.3〜3.0／5.1〜6.9 s | 19.5〜20.8 s／28.9〜30.7／15.9〜16.6 s | 0.68〜0.70 GiB | 0 |
| D4 4CPU/16G/4 | 4.2／5.2 s | 3.9〜4.2／2.1〜2.2／5.3〜5.8 s | 11.6〜12.6 s／47.7〜51.6／7.7〜8.4 s | 1.25〜1.28 GiB | 0 |

読み方: **同時に走らせても1本あたりの時間はほぼ変わらない**（単独 約4 s、2同時 3.6〜4.9 s、4同時 3.9〜4.2 s）。2本同時なら、最初の1本は約2.4 s、2本とも約5.5 s で終わる（直列なら約8 s）。スロット1つあたりの匿名メモリ増分は約0.27 GiB。A の幅が大きいのは、1周目が cold に近く（page cache 追い出しの最中）、2周目以降に温まったため。

## 結果2: cold（page cache を捨てて開始、10件キュー、2回、各行は個別の値）

| 腕 | 1本の中央値 | 10件キュー完了 | 件数毎分 | 10件目の待ち | cgroup `max` 到達回数 |
|---|---|---|---|---|---|
| A 2CPU/4G/1 | 41.3／34.8 s | 229／200 s | 2.6／3.0 | 225／196 s | 約150万 |
| B 2CPU/4G/2 | 48.2／41.1 s（最大73 s） | 175／152 s | 3.4／4.0 | 128／111 s | 約145〜187万 |
| C 2CPU/8G/2 | 3.8／5.3 s | 18.3／23.9 s | 32.7／25.1 | 15.9／20.7 s | 約1,800 |
| D4 4CPU/16G/4 | 4.5／4.6 s | 12.6／13.4 s | 47.7／44.7 | 8.1／8.9 s | 0 |

**メモリ4 GiB は compile を約10倍遅くする**（`import Mathlib` の page cache が cgroup に収まらず追い出し合う）。4 GiB のまま2スロットにしても改善しない（B）。8 GiB にすれば2スロットが効く（C）。agent の `boundary.py` のコメント（4 GiBで最大129 s、8 GiBで8 s）と同じ傾向。

## 判断・推奨

- 現行インスタンス（r8a.large）: **2 CPU / 8 GiB / 2スロット**（C）。8 GiB は infra が既にレビュー済みの値で、全 actor の上限合計（verifier 8＋proof 1＋assessment 1＋reviewer 1＝11 GiB、並列プロファイルでも 13.5 GiB）が 16 GiB から OS 用 2.5 GiB を引いた 13.5 GiB に収まる。それ以上のメモリは足せない。
- **今の 4 GiB（保持された source）は、page cache が cgroup に載らないとき compile が約40 s になる。** 本番の実際の cache 課金は未確認（親 cgroup に課金されている可能性がある）。2スロットの前に、8 GiB 化だけでも効く可能性がある。
- (a) 2候補を毎回競争させる: **xlarge は不要。** r8a.large で2スロット・8 GiB なら、2本とも約5.5 s、最初の1本は約2.4 s（この Mac での値）。
- (b) 10人同時で30秒以内: 各人が1 compile なら2スロットで10件目の待ちが約17 s（この Mac）。2候補競争なら20 compile で約36 s（推計: 2倍）、2スロットでは30秒の枠に収まらない。**4スロット（xlarge 形、4 CPU/16 GiB）なら20 compile で約24 s（推計）。** 本番の Lean は通常2〜5 s、負荷時11 s の記録がある（t2 の測定）。11 s なら、1 compile 10人でも2スロットは約55 s で足りない。xlarge は、(b) を競争ありで満たす場合に必要（モデル呼び出しの時間が別にあるので、Lean に使える枠は30秒より小さい）。
- 費用は計算していない（リード判断）。

## 限界・未確認

- **Mac/Docker の測定が言えないこと:** CPU は arm64 で、r8a は AMD（x86_64）。vCPU が SMT の片方なら、2本の同時 compile は同じコアを分け合って遅くなる。この測定は各 vCPU が独立のコアのように見えており、**r8a の SMT の有無は未確認**（AWS の仕様で確認が要る）。page cache と I/O は Mac の VM の SSD で、本番の EBS とは違う（cold が本番でどれだけ遅いか不明）。他の作業が負荷を10〜20かけている端末で、時間は上下している。
- cgroup の page cache は、最初に触れたコンテナに課金される。warm の A8/B/C は他の腕の cache を借りた可能性があり（匿名メモリのピークは共通）、memory の効果は cold の表で見るのが正しい。
- 10件は varied だが、warm では全件が約2〜6 s に収まった。1件のコンパイルが数十秒かかる題はこの集合にない。
- verifier の 503（待たせず断る）の扱い（再試行間隔と上限）は測っていない。10人同時の実測には、再試行を含めたエンドツーエンドの負荷試験が要る。

## 出典

pals-infra PR #153、pals-agent PR #111。生データ（Lean 本文なし。ファイル名と時間のみ）: `side-session-notes/.../lean-slots/{results.jsonl,cold.jsonl}`、ハーネス `harness.py`・`driver.py`・`cold.py`。台帳の行: `2026-11-11-lean-slots-*`。
