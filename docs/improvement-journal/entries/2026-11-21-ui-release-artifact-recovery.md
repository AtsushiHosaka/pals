# UI配備の再開資料の回収（2026-11-21）

- 指標：配備再開までの時間と成功率。
- 仮説：新しい診断版を最初から転送し直す前に、最後に受理された命令と保存済み原本を照合すれば、重複操作を避けられる。
- 変更：本番変更は行っていない。消失した一時worktreeの代わりに、復旧sourceをworkspaceの永続ディレクトリへ復元した。
- 条件：引き継ぎIssue #451、既存proposalとdispatch台帳、source `8db2cc1267202bfbaa9ff3af3811e6c349f4994b`。有料生成は0件。
- 結果：sourceはcleanで、署名済みinventoryの現行infra alias26件すべてのraw SHAが一致した。不一致は0件。これはsource照合1組の成功であり、本番受入の成功率ではない。
- 再開上の不足：最新planの参照先には消失した一時ファイルがある。既存2337ファイルとのSHA照合で3参照を完全一致のまま回収した。残る参照の回収を続けており、推定したreceiptや結果は作成していない。
- 実機の未確認事項：最新proposalはcompute側cleanupの受理後、control側installの受理記録がない。古いinstall失敗を最新試行の結果とは扱わない。AWS認証が失効して自動更新にも失敗したため、通常ログインを開始した。
- 判断：sourceの一括再実装や診断用の全再転送を始めず、原本回収と同じCommandIdの結果確認を先に進める。
- 費用・時間：モデル追加費用0。配備完了までの時間短縮は未測定。
- 次にやること：AWS認証を復旧し、最後の受理済み命令を読み取り確認する。参照先を完全一致で回収した後、正規入口で再開する。
- 出典：[引き継ぎIssue #451](https://github.com/AtsushiHosaka/pals/issues/451)、ローカルのsource照合記録と原本回収manifest。私有artifactは公開しない。

追記：通常ログインが成功した。AWSの実readbackでは限定IAMが11月21日06:00 JST失効の承認済み内容と一致した。既存4命令の再観測では、最後のcompute cleanupと後続の両host healthは成功、古いcontrol installはclass_refusalで失敗していた。既知309命令の読み取り回収は最初にレート制限を受け、取得済み結果を保持して全呼び出しを600ms以上空ける設定へ変更した。新しい変更命令は送っていない。

最終結果：既知309件のSSM入力・結果をすべて読み取り回収した。完全JSON、定数byte、base64、圧縮payloadを期待SHAと照合したが、追加復元は0件、未解決は65参照だった。内訳は元退役closure1、config/bindings12、中止配備snapshot3、failed plan1、ローカルjournal14、prepare/stage/observe receipt14、元inert-stage receipt20。journalはローカルで付けた時刻を含むため、AWS時刻では元byteを再現できない。既存の別入口も原本を必須としており、通常の再開は停止した。バックアップの有無を確認中。新しい本番変更命令、署名、有料生成は0件。公開ホームGETはHTTP 200だったが、機能受入とはしない。
