# seq30のhealth-light失敗と受付未復旧（2026年11月17日）

## 07:14 UTC時点の状態

候補`1be72c60b705328c30b61c198fa037f6b6ef14dfd0f9ed92aa118914bf543f15`はadmissionとcontrol・compute・reconcilerの有効化まで進んだが、computeの`health-light`で停止した。同じattemptの正規reconcileも同じgateで失敗した。状態は`deployed_unverified`で、本番受け入れは未完了である。

受付先は0件、ownerは保持中、cleanupは未完了。通知抑制は解除済みである。利用停止15分以内の目標は未達となった。受付復旧が終わっていないため、停止時間の最終値は空欄とする。新しい本番質問・追加の有料モデル呼び出しは行っていない。

親sourceは`8b778b235ff44fca947d22f982769077ccba18de`、infraは`15c54e2645e52942aa759b09562ee29fa1db99c8`。署名、必要なsource CI、配置したファイルの照合は切り替え前に成功した。主担当は[#378](https://github.com/AtsushiHosaka/pals/issues/378)の継続セッションで、障害の正本は[#410](https://github.com/AtsushiHosaka/pals/issues/410)に置く。

## 正規attemptの経過

時刻はすべて2026年11月17日のUTCで、元journalの記録を使う。

| 工程 | 記録された時刻・結果 |
|---|---|
| deregister | 06:04:46.686108開始、06:06:55.164614成功 |
| quiesce | 06:06:55.177653開始、06:07:44.074833成功 |
| admit | 06:07:44.087384開始、06:08:00.618943成功 |
| activate-control | 06:10:51.532506成功 |
| activate-compute | 06:12:09.618799成功 |
| activate-reconciler | 06:13:06.265356成功 |
| 初回health-light | 06:13:06.278203開始、06:13:24.733251失敗 |
| 通知抑制の解除 | 06:15:13.773531成功 |
| 初回終端 | 06:17:05.959235、failed・owner保持・cleanup未完了 |
| reconcileのhealth-light | 06:23:37.079209開始、06:23:58.954030失敗 |
| reconcile終端 | 06:27:43.034669、failed・owner保持・cleanup未完了 |

終端の固定コードは`native_operation_failed:health-light`。controlは成功したが、compute側の下位Refusal理由が包まれて失われた。元applyとreconcileを別の製品試行に数えず、同じattemptの技術検証1件、0/1として台帳に記録する。受付停止の最終所要時間、回答latency、数学の成功率はこの表から算出しない。

## 読み取り診断で確認した範囲

既存SSM結果と既存ログを読んだ後、記録付きの通常Session Managerで個別の読み取り診断を行った。新しいSendCommandは送信していない。アプリ・DB・稼働設定・元journal・元driverを変更せず、診断の成功を正規gateのPASSに転用していない。

最初の診断では`control_ready`、proof、assessmentの検査を通過し、reviewerのinspectが`native_command_failed`となった。sourceではcompute applyが`reviewer_enabled=false`のreviewerを作らない一方、light readinessは4役割を無条件に列挙していた。

07:03 UTCのconfigured診断v2-bで、実設定の`reviewer_enabled=false`と、設定済みactorがproof・assessment・verifierの3つであることを確認した。認証済みAPI readiness、3actorの実inspectと全validate、firewall、verifier source、Lean child、前後closureがすべて成功した。未設定reviewerを除いた診断であり、凍結された正規health-light自体が成功した記録ではない。

controlについても、元の凍結phaseをそのまま呼ぶ読み取り診断が成功した。前後closureと通常Sessionの終了を確認した。transportはcompute専用schemaを期待していたため初回は結果をnullとして扱ったが、主担当が元の非公開JSONからcontrolの結果を抽出保存した。gateへPASSを取り込んだものではない。

診断過程の失敗も保持する。初回接続のEOF、システムPythonの依存不一致、closure例外が元の例外を隠した不備、transport終了時の`killpg`のPermissionError、configured旧版のFileNotFoundErrorを含む。後者の実missing filenameは未特定である。v2では主失敗とclosure失敗を分け、固定の分類だけを出力した。これらを新たな製品試行や数学問題の失敗数には加えない。通常Sessionはすべて終了を確認済みである。

## source修正と復旧の制約

[infra PR186](https://github.com/AtsushiHosaka/pals-infra/pull/186)は、最終設定で無効なreviewerだけをlight readinessから除外する。有効reviewerと他の設定済みactorの必須検査、running状態、identity、firewall、Lean childの検査は維持する。

exact base`04590c6`では新3件のうち無効reviewerのケースがerrorとなり、修正版`68ae4be751b5e59ee7001a1286321f10c3f2086f`は対象202件・skip0を1.892秒で通過した。これは新3件、正規render63件、native safety123件、workflow13件の技術検証で、providerや本番を使った検証ではない。台帳には別の技術bundle1/1を置き、unit件数を製品・数学の分母へ加えない。

07:14 UTCまでにexact headの既存run`44034444123`の必須4検査がすべて成功し、独立レビューと未解決thread 0を確認して通常mergeした。mergeは`5511ff48df540cc78f932ac1ea4c68f35592e1f6`。当該headを候補にした正規source gateは未実行で、host上の凍結driverは元のinfra15c54e2のままである。

元のIAM読み取りpolicyは06:34:06 UTCに失効した。正規grantは同じ凍結policyの再設置に限られ、期限を延長しない。既存attemptのplanとbindingを新late-freezeに差し替える機構はなく、元ledgerを手編集して継続した扱いにはできない。

07:05 UTCに主担当が既存target1件だけの再登録を緊急復旧案として提示した。07:14 UTC時点ではオーナーの例外承認待ちで、登録は未実行。元のgate・署名・認証を変更せず、診断成功だけでacceptedにしない。後続判断と実復旧は別の時点の記録として追記する。

## 根拠

非公開の原本はリリース保管領域に保持する。本文には内部path、host、IP、account、認証情報、元質問・Lean・回答を載せず、原本のSHA-256と論理名だけを示す。

| 原本の論理名 | SHA-256 |
|---|---|
| 元attempt journalの読取時点 | `bf91010331f2a317ed7b83dd1b1398a575a08afbb75b5e03d9434cdc7aaf774c` |
| 凍結IAM policy | `2939b63918f566f1d5d5f6f0a0befee13c07c0b42f3fbe57ef63e428ee35947c` |
| configured診断v2 source | `babcd7ceee5475ba785e013701af3e0015ca9662165f17977728bd877a8e8f63` |
| configured診断v2-bの出力ログ | `adf1e5305510cd063731b03f01307025219917aa25835ba96107d1b8f6e3d79f` |
| configured診断v2-bの保存結果 | `53ab35889af8eee5c18b3b8cc8483db2d14e297cfe1a0205ea713b607bd96e7e` |
| control元phase診断の保存結果 | `48c912478ff4ae5e4d7f819c5df13969297ba09dc6e3e25f2ced01fa6303b73e` |
| control元phase診断の出力ログ | `996eb630cf4635049f0814dd7f06a458bd7fc88c15f118d2180c337998ac7d25` |
| source修正の旧版REDログ | `9e263a908abe0e45bfea35c9aea51eeed22723201ef4b805709e8430ff00eca2` |
| source修正のGREENログ | `5b25b32fb2c1e51136eacd330b175ab7e45391035e442e63ec10805f4594c328` |

品質台帳IDは`2026-11-17-seq30-health-light-incident`と`2026-11-17-seq30-configured-reviewer-fix`。改善の成功率・時間短縮率や費用総額は未測定。過去697行と旧試行の成功・失敗は保持する。
