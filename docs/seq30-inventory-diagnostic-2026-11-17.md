# seq30のnative inventory診断（2026-11-17）

[restore-checkの失敗](seq30-restore-check-failure-2026-11-17.md)で失われていた診断を残すため、[#400](https://github.com/AtsushiHosaka/pals/issues/400)と[infra PR #183](https://github.com/AtsushiHosaka/pals-infra/pull/183)で読み取り専用CLIを実装しています。初回の診断準備は送信前に失敗しました。その後の実ホスト診断3回はprobe_completedでしたが、元のtuple拒否は再現せず、根因は未確定のままです。本番の切り替えや受け入れが成功した記録ではありません。

## 初回の失敗と互換性の修正

最初のCLIの送信前検査はdiagnostic_refused・closed_diagnostic_failureで停止しました。主担当が確認したこの時点のホスト送信とstate作成は0件です。guard一覧のhash計算に不要な改行を含めていた点を直しました。閉じた初回結果から、どの条件が最初に失敗したかまでは断定しません。

さらに、旧凍結configを新しい診断CLIから読む際に、旧validator自身のsource pathを使う必要があることをpure検査で再現しました。正規の旧validatorを使う修正を13be88fcへ追加し、CLIの回帰検査は15件から16件になりました。実際の旧configと参照先closureも、providerへ接続しないpure検査を通過しています。旧configや受領書の書換え、許可条件の緩和で通したものではありません。

## 実ホストの読み取り3回

実行時に主担当が固定したsourceは`13be88fc10d31cf402af5a29f3e8245b89a46a33`でした。次の各stateにはintent・sent・resultが各1組あり、三つのSSM command IDも異なることを確認しました。内部ID自体は公開しません。

| 診断 | intent・送信 UTC | result UTC | 結果 |
|---|---|---|---|
| 初回の正常probe | 01:20:12 | 01:20:14 | probe_completed・code none |
| 追加probe 2 | 01:24:19 | 01:24:21 | probe_completed・code none |
| 追加probe 3 | 01:24:24 | 01:24:26 | probe_completed・code none |

三つともdiagnostic_only=true、application_mutated=false、database_mutated=falseで、phaseはprobe、error classはnoneです。結果JSONのSHA256は三つとも同じですが、journalと異なるcommand IDによって、各読取の実行を照合しています。同じ内容のJSONが同じhashになること自体を、三回の実行証拠とはしません。

診断には有限のphase・code・error classを使い、unknown flagsや生のruntime内容は出力しません。今回のprobeで例外が出なかったことから、過去の拒否が解消したとは判断しません。過去のcontainer StartedAtも保存されておらず、その間の再起動を否定できません。

既存のhost CloudWatchログも読み取りましたが、返却logStreamsは0件で次ページtokenもなく、対象に使える過去ログ源は見つかりませんでした。これを当時のruntimeが正常だった根拠にはしません。

## 最終offline検査とlive sourceの区別

PRの最終headは`e4adbff090e59ddb3b476045484f550a27332b14`です。主担当の最終offline検査では、H診断11、CLI16、既存native123、host57、workflow13の計220 unique testsが通過し、全体5.230秒でした。保存ログから各suiteの件数と成功を照合しています。

CLIの実bytesは、liveの13be88fcと最終e4adbffで一致し、SHA256は`7dbdb4fe819407a80aadcbb043349e8400bcff93425c4481f1e2c58fcc075bf5`です。ただし、Hの有限語彙やCI groupingの追加はlive実行後なので、実ホスト3観測を最終head全体のlive検証とは扱いません。H診断は10件からRefusal等を含む11件へ増えています。

自動集約を追加した同じheadでは、push run 43998354835がcancelledとなり、PR run 43998363240が存続したことを主担当が確認しています。4 jobs、自前runner labels、test scopeの変更はありません。これは今回の同branchのpush/PRを集約した記録で、所要時間の削減量は測っていません。本記録に向けた確認時点ではPRは未統合で、必須CIとレビューは別に必要です。offline成功や診断3回を、本番に取り込んだ結果へ読み替えません。

## 計数と根拠

品質台帳には、最初の診断準備失敗を技術bundle1件の0/1、回復後の実読取診断bundleを別の1/1として記録します。bundle内の3観測や220 testsを、製品・数学の3試行や220試行へ加算しません。新しいpaid処理とモデルprovider callsは0件です。文書作成時のローカル台帳も83 calls・actual/reserved292673μUSD・blocked=falseのままでした。実費総額と診断全体の精密な所要時間は未測定です。

| 記録 | SHA256 |
|---|---|
| 初回の拒否ログ | `061d52ce493565a0e069432955034eec47838f9f55f58659cfdd0f32b5326b48` |
| 各実probeの結果JSON・3件共通 | `5c73bd1d0101a848509f2be56fb00485042adf226892818949cf5cba9e55e146` |
| 正常probeの閉じたCLIログ・同一内容 | `0df40245ca6f63898121ed0222a454f839296ec84bd2ccec7f8c193da9cc70a0` |
| 最終e4adbffのoffline 5 suites | `f06807c04c3653d6093fd385e204e0d3881508f78ed068324d134129589f197b` |
| 既存CloudWatchログ源の読取 | `b56a85d0e3996a303cd3155f1a6a9e72ab7ebc8220d1008261b68b24df84dc02` |

rawログ、command ID、内部hostや配置場所、資格情報は非公開で保管します。次の判断は、元の拒否を再現できる証拠と、診断を保持する修正のレビュー・CIによって行います。元のapply失敗や未確定の根因を、この診断bundleの成功で上書きしません。
