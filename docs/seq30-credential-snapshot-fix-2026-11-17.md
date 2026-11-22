# seq30の資格snapshot読み取り修正（2026-11-17）

[#407](https://github.com/AtsushiHosaka/pals/issues/407)の資格state更新中の読み取り競合に対し、[infra PR #185](https://github.com/AtsushiHosaka/pals-infra/pull/185)のcommit`15c54e2645e52942aa759b09562ee29fa1db99c8`を親の参照へ追加します。childの通常mergeと必要なexact CIの通過、親の必要検査を確認してから統合する段階です。この記録時点では本番へ適用していません。

## 修正と維持する境界

既存brokerのlock inodeを使い、readerが共有lockの下でstateを読むようにしました。既存のowner検証条件を維持し、旧ownerの場合も、既知のstate/credentials欠損やapi_handoff_not_readyに限って一度だけguarded loadを行います。待ちは20秒と既存deadlineで制限し、lockのmode・所有者・inode・親directoryを検証します。署名・manifest・権限の照合を外したり、任意のエラーをretryしたりはしません。

source変更はcontrol_runtime、生成observerのtemplate、復旧時のreader接続の3か所です。専用testと既存native test、既存CIの検査行を更新し、正規render出力のgolden5ファイルを再生成しました。goldenの4ファイルはobserverに依存するhashの連鎖更新です。アプリsource・image・数学のoracle・modelを変えていません。

## 検証結果

bad revisionであるinfra847の純Git archiveへ同じ新規12件のsuiteを当てると、failures=3・errors=12で失敗しました。subtestを含む内訳なので、15件の独立製品試行とは扱いません。修正版では新規12件・native123件・render63件の合計198件が2.167秒で成功し、skipは0でした。

実broker・reader・real flockを使用し、STSとOS ownershipを模擬したローカル境界の検証です。以前の局所fixtureの初回setup failureと修正後の再現は[元失敗の追記](seq30-current-tuple-failure-2026-11-17.md#2026-11-17追記broker時刻の限定的な読み取り)に保持しています。本番で不足した実ファイル名と因果関係は未確定です。旧候補f20の失敗も同じ原因だとは断定しません。

| 根拠 | SHA256 |
|---|---|
| bad847への新規suite REDログ | `edd9ee4d079c78a4d6f5aa370d98be1c785af2bfa813e66efc3655d417ff2560` |
| 修正版の対象198件 GREENログ | `22d2eda098809d51adf331b706efb68c0c6d886454bc1e5f57760cd67d735371` |
| 未使用候補085dの正規cleanup受領書 | `4adf683d07c8718b51073627a7ef82c4b8f1ea201f6dd2839abb17eafd85b6ea` |

主担当の正規cleanup受領書は候補085dに結び付き、application_mutatedとdatabase_mutatedはfalseです。旧候補の失敗結果を保持したまま未使用配置を片付けました。本番はseq29のままで、候補085dで利用停止工程は開始していません。

## 計数と残る確認

対象を限定した技術検証bundle1件の1/1として台帳へ追加します。198件のunit testを198件の製品試行へ換算せず、元の本番apply失敗0/1も残します。実provider・AWS・本番hostを使った修正検証は行っていません。新しいpaid取得はなく、費用や検証運用の短縮秒は未測定です。

[変更境界別の検証運用](seq30-validation-boundaries-2026-11-17.md)に従い、今回変えたshared readerと復旧境界の証拠を確認します。alert限定修正の予行継承をそのまま流用しません。必要なexact CI、影響する復旧確認、新候補の正規gate、本番の終端回答・保存・描画・reloadが残ります。以前の全7予行2548.159秒と全体10分未達を保持し、#379の完了や本番acceptedを先取りしません。
