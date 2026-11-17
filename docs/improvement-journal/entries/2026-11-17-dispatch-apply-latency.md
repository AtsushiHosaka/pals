# 送信と反映の分離の性能実測（2026-11-17）

- 指標: 時間。仮説は、送信が20秒遅れても、反映を別taskへ分ければp95増分を1秒未満に抑えられること。
- 条件: 基点08cf8acと統合194e6aeaの実scheduler、locked Python3.12.13、実PostgreSQL、完了job fixture、制御したqueue待ち。各arm20件×3独立burst、60sample。モデル呼び出しなし。
- 結果: 旧requestのp95増分+20.147403秒、統合+0.023407秒。旧formal+20.113804秒、統合-0.024022秒。負の増分はばらつきであり、追加の改善効果にしない。旧版各3burstの未達も保持した。
- 失敗: 本測定の測定器失敗なし。request送信6回の20秒timeout/cancelを成功送信へ書き換えていない。初期smokeを本測定へ混ぜない。過去の実装fixture失敗は前のentryに保持する。
- 判断: この限定条件では増分1秒未満を確認。独立burstは3回だけで、実SQS/Lean/モデル/認証/画面/本番の結果や10秒目標全体へ外挿しない。
- 費用: 新規有料モデル呼び出しなし。総費用と削減額は未測定。既存PGを再利用し一時DBをfinally削除、新規コンテナなし。

条件、全arm、個別sampleへのリンク、負荷と限界は[確認記録](../../410-380-verification-2026-11-17.md)と[API PR #119](https://github.com/AtsushiHosaka/pals-api/pull/119)にある。主担当はrawからp95を独立再計算した。品質台帳nは独立burst3、p95はpooled60sampleで、製品成功率と区別する。
