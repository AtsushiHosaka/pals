# 常駐 Lean を fork で作る試行: 失敗した 3 回と、通った設計 (2026-11-12)

- 指標: 時間(10 秒目標。検証 1 回の固定費)。
- 仮説: Mathlib を 1 回だけ import した Lean プロセスを fork して使えば、依頼ごとの隔離を保ったまま、起動と import(1 回の検証で 8 秒前後)を消せる。
- 変更: [pals-agent#120](https://github.com/AtsushiHosaka/pals-agent/pull/120)(既定 off)。`pals_agent/lean_verifier/resident/`。
- 測定の条件: Lean 4.32.0-rc1 + Mathlib、Mac(共有機、負荷平均 11〜50)。モデル呼び出しなし、費用 0。2026-11-12。
- 結果(試行ごと。失敗を含む):
  1. **子がタスク待ちで固まる(失敗)。** fork した子は親のタスク管理スレッドを持たず、`IO.processCommands` が `lean_task_get` で永久に待った。`sample` でスタックを確認。
  2. **旧式の逐次フロントエンドは使えない(失敗)。** タスクを使わない `Frontend.processCommands` に替えると子は終わるが、4.32 ではメッセージを全部捨てる(誤った証明でも error が 0 件)。エラーのある命題を必ず混ぜて測らないと、誤受理に気づけない。
  3. **fork の戻り値が壊れる(失敗)。** `BaseIO UInt32` の extern は、インタプリタから pid ではない値が返った(親も子も同じ値で `pid == 0` が成り立たない)。pure な形の extern にしたら pid が返った。
  4. **採用した設計。** 子ごとに新しいタスク管理を差し替える(`lean_init_task_manager_using(1)`)と、通常の `IO.processCommands` がそのまま動く。メッセージ、公理、タイムアウトの kill、zygote の再起動を実 Lean のテストで固定。
  - Linux の検証器イメージでは、さらに 2 つ失敗してから動いた: 本番イメージに libc ヘッダがなく C 部分が compile できない(手で宣言して解決)、`--load-dynlib` は `RTLD_LOCAL` で、インタプリタが記号を見つけられない(`-fvisibility=default` と `RTLD_GLOBAL` への昇格で解決)。
- 判断: 採用(既定 off)。
- 限界・未確認: 本番の `lean_child.py`(Landlock・seccomp)で zygote を包んだ状態は未検証。子が別依頼の scratch を書き換える経路は塞いでいない。
- 次にやること: `launcher` を本番の `lean_child.py` で実装して Linux で検証。依頼ごとに Landlock を絞る。
- 出典: [pals-agent#120](https://github.com/AtsushiHosaka/pals-agent/pull/120)、`docs/verification/resident-lean-2026-11-12.md`。
