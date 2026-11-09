# 本番の障害: seq27 cutover の停止（2026-11-08）

- 種類: 運用上の出来事（改善の指標ではないが、時間・成功率の記録を読むときの前提）
- 経過: 01:19 JST に ALB のターゲットを外し、旧 writer（api、reconciler、proof/assessment worker）を quiesce で停止した。その後、DB admission の前で停止し、約7時間止まった。DB admission は「20分以内の preflight」を要求するが、停止後は取り直せなかった。CloudWatch のアラーム3件（runtime-unhealthy 01:06 以降、no-healthy-target 01:26 以降、5xx 08:17）と ALB の503の断続は、この停止で説明できる。
- 復旧: 08:19 JST ごろ。停止していた4つのコンテナを `docker start` で戻し、ターゲットが healthy に戻った。08:24 の確認で3件とも OK。DB は無変更（最新 admission は seq26 のまま）。
- 影響: 約01:19〜08:19の間、API は断続的に不安定。この間の測定値（本番の時間・成功率）は参考にならない。
- 学び: 夜間に止まる設計だった。admission の前に preflight を必ず取り直す、または時間切れなら自動で元に戻す仕組みが要る。seq27 の出し直しは、停止を最大20分以内にする。
- 出典: CloudWatch（`pals-prod-incident-*`）、ALB アクセスログ、リリース担当セッションの報告

## 訂正（2026-11-09、pals#320 のレビュー指摘）

- 経過の「CloudWatch のアラーム3件と ALB の503の断続は、この停止で説明できる」は、`runtime-unhealthy` には成り立ちません。`runtime-unhealthy` は 01:06 に始まり、ターゲットを外した 01:19 より13分早いためです。
- 停止の時間帯と時刻が合うのは、`no-healthy-target`（01:26 以降）と 5xx（08:17）です。
- `runtime-unhealthy` の 01:06〜01:19 の原因は、この記録からは確認できていません。未確認として残します。
- 元の記述は書き換えていません。根拠は、元の記述にあるアラームの時刻です。
