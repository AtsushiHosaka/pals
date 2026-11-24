# gate の条件表の一元化(pals#486、リアーキテクチャ段階2)(2026-11-24)

- 指標: 時間(release 当日の「実行して初めて分かる失敗」の再実行)。成功率ではなく、同じ判定が複数箇所にあることによる食い違いの数を減らす。
- 仮説: gate の条件と上限値が plan・cycle・step・host tools・preflight に別々に書かれているので、seq33〜seq40 で約6回、実環境で初めて食い違いが見つかった。1つの表に集めれば、条件の追加が表1行とテスト1本で済み、preflight の段階で拒否として出る。
- 変更: pals-infra PR #256(`scripts/release_gate_table.py`)。挙動は変えない。食い違いは厳しい側に合わせた。既定のオン/オフの切り替えはない。
- 測定の条件: pals-infra の `scripts/` と `host/private-runtime/` を AST で数えた(before=0b3c404、after=main 5e58b3b。#256 は統合 #269 で main に入った)。モデル呼び出しなし、費用なし。測定は [`pals-scripts/measure-gate-duplicates.py`](../../../pals-scripts/measure-gate-duplicates.py)(`python3 pals-scripts/measure-gate-duplicates.py <pals-infra のチェックアウト>`)。出力は [before](../../rearchitecture/gate-duplicates-before-2026-11-24.json) と [after](../../rearchitecture/gate-duplicates-after-2026-11-24.json)。

## 結果

| 指標(スクリプトの出力の項目) | before(0b3c404) | after(main 5e58b3b) |
|---|---:|---:|
| 判定に使う上限の数値リテラル定義(`numeric_literal_definitions_of_gate_limits`) | 36 | 4(host 側の import できない4つ。テストが表と一致を確認) |
| `OBSERVATION_MAX_AGE_S` の定義(`observation_max_age_definitions`) | 6(180秒4、900秒2。別物の同名) | 3(host 側のリテラルだけ。表に別名2つ) |
| `admitted_not_serving` との比較(`forward_only_state_comparisons`) | 17 | 7(検証器・host 側・観測値の確認。述語は表の1か所) |
| forward-only のモード組を手で比べる式(`forward_only_mode_tuple_agreements_by_hand`) | 2(plan・host_tools・cycle・step の4か所の判定のうち) | 0 |
| 記録検証の関数(`record_verifier_implementations`) | 2(gate と cycle、drift テスト付き) | 3(表の `verify_record`、cycle の記録を読むだけの関数、#242 が足した rehearsal 記録の検証。preflight 記録の検証ロジックは1つ) |
| gate に条件を足す変更ファイル | 3以上 | 2(表+テスト。テストで実証。スクリプトの項目ではない) |
| 実行して初めて分かった失敗/release | 5(seq33) | 未計測。次の release 後に数える |

## 判断

採用(PR #256 が merge された後)。release の前に plan を組み直し、rehearsal を再実行する必要がある(表が frozen set に入るため)。

- 食い違い: 通知窓の上限が preflight=600秒、cycle の形式=1800秒。cycle は下げていない(seq30 の rehearsal profile が1500秒)。要判断。
- 限界・未確認: 「実行して初めて分かる失敗が0件」は次の release の記録で確認する。rehearsal の Docker 通しはこのセッションでは実行していない。
- 次にやること: #242 が足した `verify_rehearsal_record`(コピー+drift テスト)を表の検証関数に寄せる。repair 系(`release-repair.py`、`release-supersede-owner.py`)が step を読むときに、表の pin を確認する。
- 出典: pals-infra#256(統合 #269 で main へ)、台帳の行 `2026-11-25-gate-table-duplicates`、pals#486、pals#493、`docs/release-gate-conditions.md`(pals-infra)
