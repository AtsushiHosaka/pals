# seq30のhealth-light失敗と診断（2026-11-17）

狙いは、正規切り替え後に稼働候補のreadinessを確認して受付を戻すことだった。親8b778b2・infra15c54e2の同じattemptで、admissionと3つの有効化工程は成功したが、元applyとreconcileのcompute health-lightがともに失敗した。07:14 UTC時点で受付先0件・owner保持・cleanup未完了、15分以内の目標は未達。最終停止時間はまだ確定していない。

読み取り診断では、無効なreviewerを作らないapplyと、全役割を検査するlight readinessの不一致を確認した。実reviewer_enabled=falseの設定に沿う3actor、API、firewall、Lean child、前後closureは診断を通過し、controlの元phase診断も成功した。EOF、Python依存不一致、closureによる元例外の隠蔽、transport終了失敗、missing filename未特定も保持する。診断を正規gateの合格に置き換えない。

修正PR186は有効reviewerと他actorの必須検査を保つ。旧版RED、修正版202件・skip0・1.892秒のGREENを確認し、必須4CIとレビューを経て通常mergeした。hostは旧driverを保持し、新sourceの正規候補gateは未実行。仮説は設定済みactorだけを必須とすれば無効reviewerへの誤った拒否を避けられるというもので、局所技術検証の成功を採用した。本番復旧と受け入れは未確認である。

台帳は元attemptを技術0/1、修正検証を別の技術1/1とする。モデル・推論量・修復上限・カード数は今回の読み取りとsource検証には該当しない。新しい数学問題・追加有料呼び出しは0件、費用総額と改善率は未測定。07:14 UTC時点で既存target1件の緊急再登録案は例外承認待ち・未実行である。

出典は[障害記録](../../seq30-health-light-incident-2026-11-17.md)、[#410](https://github.com/AtsushiHosaka/pals/issues/410)、[PR186](https://github.com/AtsushiHosaka/pals-infra/pull/186)。台帳IDは2026-11-17-seq30-health-light-incidentと2026-11-17-seq30-configured-reviewer-fix。
