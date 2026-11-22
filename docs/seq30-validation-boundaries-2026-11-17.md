# seq30の検証を実行する条件（2026-11-17）

同じsource SHAの全件検証を重複して実行せず、変更した境界と失効した依存を確認する。[#379の判断](https://github.com/AtsushiHosaka/pals/issues/379#issuecomment-6939162577)と[既存の変更境界選択規則](release-reliability-policy.md#evidence-required-for-promotion)に従う運用整理であり、新しいcodeやCIの実装ではない。

| 変化 | 実行する確認 | 継承できる証拠と条件 |
|---|---|---|
| 文書だけ | 親のexact required 2checksと文書・台帳の該当検査 | アプリ・infra・予行。製品取得やpaid送信は追加しない |
| 同じSHA・入力でCI待ち | 既存runを観測 | 完了した同SHAの結果。latestの失敗を飛ばさず、同じ全件local実行や新runを追加しない |
| alert readbackだけ | 境界の旧版RED・新版GREEN、保存実Getの正規validator、exact required CI、実運用時のfresh activation/readback/cancel | alertをfake化するE2Eやalertを呼ばないhost harness、変更しない予行境界。[847の判断](seq30-cloudwatch-readback-verification-2026-11-17.md)に対象と限界を記録済み |
| native snapshot・owner・recovery | 対象RED/GREEN、native・golden・該当復旧test、exact required CI。変更したreaderを通る正常・失敗・期限切れ等をcoverageで選ぶ | 未変更アプリの数学・paid取得。shared readerを通る予行の根拠が不足する場合、影響するscenarioは省略できない。alert限定の継承判断を流用しない |
| candidate UUID・期間・tooling pin | 新候補の正規source checks、署名・registry、観測・配置closure、derive再現・材料一致、late-freeze・verify-final・dry直後apply | 未変更のimage・source・schema・model・oracleと対象外test。新candidateという理由だけで全7予行やpaid取得を追加しない |
| session・TLS・観測のTTL | 失効した依存を正規renewし、readiness・observe等を確認 | 未変更sourceのCIと予行。captureは元stateのlatestがaccepted・未失効で、subject・env・runner等が一致する場合だけ正規verify-existingを使う。新送信0で再観測し、expired/failed結果の編集やPASSのコピーはしない |
| 本番activate後 | 新requestのcandidate一致、Lean終端、保存、実描画、reload/historyと必要な図QA。owner・復旧・cleanupを確認 | local acceptedやhealthだけで本番acceptedへ進めない |

必須検査は候補のexact sourceに結び付ける。欠落・skipped・queued・古いgreenは成功の代用にならない。変更が既存証拠を無効にする範囲を先に記録し、影響する復旧・失敗工程を省かない。実行中の所有権と安全境界も維持する。

既存workflowは同じPRとpushを同じconcurrency laneへ集約する。手動予行はrun.shでstand-in環境を構築するため、無関係な境界や同一SHAの全件を機械的に再実行しない。CIの検査を新たに選別する実装を追加したという意味ではない。

この整理による削減秒・費用・成功率は未測定で、品質台帳へ測定行は追加しない。以前の7予行の2548.159秒と全体10分未達は保持し、#379を閉じない。本番受け入れや復旧の成功も、この文書だけでは主張しない。
