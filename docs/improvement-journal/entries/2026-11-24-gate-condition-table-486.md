# gate の条件表の一元化(pals#486、リアーキテクチャ段階2)(2026-11-24)

- 指標: 時間(release 当日の「実行して初めて分かる失敗」の再実行)。成功率ではなく、同じ判定が複数箇所にあることによる食い違いの数を減らす。
- 仮説: gate の条件と上限値が plan・cycle・step・host tools・preflight に別々に書かれているので、seq33〜seq40 で約6回、実環境で初めて食い違いが見つかった。1つの表に集めれば、条件の追加が表1行とテスト1本で済み、preflight の段階で拒否として出る。
- 変更: pals-infra PR #256(`scripts/release_gate_table.py`)。挙動は変えない。食い違いは厳しい側に合わせた。既定のオン/オフの切り替えはない。
- 測定の条件: pals-infra の `scripts/` と `host/private-runtime/` を AST で数えた(before=origin/main 0b3c404、after=PR #256)。モデル呼び出しなし、費用なし。計測スクリプトは共有ノートの `measure_gate_dups.py`。

## 結果

| 指標 | before | after |
|---|---:|---:|
| 判定に使う上限の数値リテラル定義 | 36 | 4(host 側の import できない4つ。テストが表と一致を確認) |
| `OBSERVATION_MAX_AGE_S` の定義 | 6(180秒4、900秒2。別物の同名) | 表に別名2つ。リテラルは host 側3つ |
| forward-only の一致を手で書いた比較 | 4 | 0 |
| 記録の検証ロジック | 2(drift テスト付き) | 1 |
| gate に条件を足す変更ファイル | 3以上 | 2(表+テスト。テストで実証) |
| 実行して初めて分かった失敗/release | 5(seq33) | 未計測。次の release 後に数える |

## 判断

採用(PR #256 が merge された後)。release の前に plan を組み直し、rehearsal を再実行する必要がある(表が frozen set に入るため)。

- 食い違い: 通知窓の上限が preflight=600秒、cycle の形式=1800秒。cycle は下げていない(seq30 の rehearsal profile が1500秒)。要判断。
- 限界・未確認: 「実行して初めて分かる失敗が0件」は次の release の記録で確認する。rehearsal の Docker 通しはこのセッションでは実行していない。
- 次にやること: マージ順に従い、#242 との競合を解く。release-modes(段階5)が表の `modes` 欄を使う。
- 出典: pals-infra#256、pals#486、pals#493、`docs/release-gate-conditions.md`(pals-infra)
