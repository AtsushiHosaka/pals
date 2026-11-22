# 接続先ガード適用後の送信遅延比較（2026-11-17）

対象は時間。初回測定器のquery host/dbname override見落としを修正し、routing環境不在と固定されたlocal接続先を記録して同条件を再測定した。初回の数値と失敗・限界は前entryに保持する。

実PG、完了job fixture、制御queue、各arm20件×3独立burst。旧requestのp95増分+20.049274秒に対して統合+0.006812秒、旧formal+20.095772秒に対して統合+0.006957秒だった。この限定条件では両経路で増分1秒未満を確認した。起点はfixture関数return直後で、厳密なcommit点ではない。独立burst3回・pooled60sampleを区別し、数学・本番成功率へ換算しない。

測定器の失敗なし。guardはnetworkなし49件と実PG少数smokeで検査し、CREATE/schema/DROPの接続先一致を確認した。新規有料モデル・コンテナ・AWS変更なし。一時DBを削除した。総費用・削減額は未測定。初回との集約改善率や、本番・#380全体の達成は主張しない。

[全条件・raw hashと再計算](../../410-380-verification-2026-11-17.md)、[API PR #119](https://github.com/AtsushiHosaka/pals-api/pull/119)。raw hashは2fd3a93fc6b82d4b2c7508243cdbcfd2c6ab765ab4e83173f0ef2e33e8984d53。
