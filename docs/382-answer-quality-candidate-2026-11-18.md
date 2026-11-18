# #382 回答精度の実装候補と検証範囲（2026-11-18）

状態はWORKING。オーナーの本番反映依頼、[#382](https://github.com/AtsushiHosaka/pals/issues/382)の要件、現行の公開APIと表示契約を基準とする。調整担当は`01a1ed35-9cde-7fe0-8c9d-b7d017703443`、本件の実装担当は`01a1e863-d84c-7e82-bedb-156dd25d871e`、唯一の本番実行担当は`01a1ebe7-a4ee-78c0-ab22-a16cfcccc3d2`である。

## 基準と編集境界

親の記録用worktreeは`9aafc6d83dcc82de2d801647d71207459d095b52`を起点とする。本番担当が準備する親候補は別branchの`550eea5`で、記録の起点と配備候補を混同しない。

| 領域 | 実装基準 | 今回の範囲 |
|---|---|---|
| API | `a3191b4cd11a347724bbabff54e39c829faca31e` | 意味審査後の再形式化で、保存済みの推論量と元admissionの期限を保持する |
| Web | `aa1a6d48ceeb90f79c5360e5f699e72d11735f56` | 公開された意味審査の理由を表示し、従来のLean失敗と区別する |
| Agent | `146ecf2b816ac6830940fac824bd9e8df90d80e4` | 新規生成する求値説明の結論検査と、v2の生成・審査基準を整合させる |

共有checkoutの既存変更は変更しない。APIのadmission epoch、リリース制御、図生成・図のbinding、Lean検証器、ターゲット生成・Recipe再利用は他の担当または対象外である。#318担当から説明ファイルの結論関連hunkを本件で扱う確認を得た。図が不正なとき本文を失わず、修正時に図を落とす既存方針、独立した図の審査を維持する。

## 今回確認する実装条件

| 条件 | 修正と確認 | 合格しても証明しないこと |
|---|---|---|
| C1 | 新jobへ元のgeneration modelと保存済みreasoning effortを引き継ぎ、最初のjobの証跡を変更しない | モデルの一般精度や再形式化の成功率 |
| C2 | 元のquota/token admissionから残り時間を判定し、600秒の最初のjob上限と1回だけの再形式化を維持する | 混雑時の本番所要時間や費用 |
| C3 | 失敗したrequestの公開理由と、保存jobの型付き診断だけで意味審査の拒否・利用不可を区別する。生のLLM応答や例外文は表示しない | 非公開の審査理由や、新しいエラー分類の推測 |
| C4 | 対象となる求値説明では、新規生成の結論に結果の数式を要求し、修正予算・QA・Leanの信頼条件を維持する。既存の保存説明は読めるままにする | 数式があるだけで数学的に正しいこと、全言語・全表現の求値依頼を検出できること |
| C5 | 結論全文の保存と表示、既存の手動再試行、認可・quote・冪等性、進行中の表示、図の既存契約を保つ | 実API・worker・検証器を通した本番受け入れ |

失敗理由の公開契約は`semantic_review_failed`と`semantic_review_unavailable`の2分類である。独立したinvalid-response理由は公開されていないため作らない。未知の追加metadataや別error_codeとの組合せでは、意味審査だと断定せず従来の表示を維持する。

## APIで確認した不具合と修正候補

意味審査後の再形式化は既にAPIにあり、Agent #137はその効果測定である。新しいworker再試行機構を重複実装しない。結論全文のprojectionと精密なfailure_reason返却も既存実装を再利用する。

元の再形式化経路は、proof_requestsの生rowだけを新jobへ渡し、別テーブルに保存されたreasoning effortを引き継いでいなかった。また残り時間の判定をjoblink作成時刻から計算し、quota/token admission後に長く待った依頼で、元の期限を超える再試行を許し得た。

[API PR #124](https://github.com/AtsushiHosaka/pals-api/pull/124)のheadは`1da88bf1bb79e6f7485bd1cdb730d298cc953ec9`。既存のgeneration settings読取とdeadline sweeperのadmission時計を再利用する。source、既存CI対象テスト、検証noteの3ファイルだけを変更し、workflowとmigrationは変更していない。

実PostgreSQLの新しい8回帰は、旧版4件失敗・4件成功から修正版8件成功となった。推論量low/highの保持、quota/token両方の期限、残時間がある場合の作り直し、600秒上限、再適用時に新jobを作らないこと、answeredとhold消費までを確認した。生成jobの終端はfixtureで準備しており、実モデル・Lean・本番回答の測定ではない。

関連66件の比較では旧版19件失敗・47件成功、修正版15件失敗・51件成功で、対象4件以外の新規失敗はなかった。15件の既存失敗は古いtoken fixtureとgeneration settings migrationの不一致として保持し、対象外の期待値を変えていない。正規workflowと同じ24ファイルのローカル実行は386件成功・失敗とskipは0だった。通常mypyの既存10エラーは残し、変更sourceを対象とする静的検査とruffは成功した。専用DBは削除済みで、既存サービスを再利用した。

## Webの理由表示

[Web PR #94](https://github.com/AtsushiHosaka/pals-webfront/pull/94)の最終候補は`d11e7a9171d9ba5f46bf1504e6cd8cccffdf32b4`。正規本番用branchの`5e2fab4a156a9731d785ae4ea6d1f3a52c2316c1`を通常mergeし、本件の差分はproductionの4ファイル、回帰テスト、検証noteの6ファイルである。

公開APIの既知のfailure_reasonだけをDTOから表示へ渡す。失敗したrequestと対応するerror_codeの組合せでのみ使い、未知値・型違い・不一致は既存表示へ戻す。保存jobの履歴では既存の型付き診断を使い、生のLLM出力や例外文から理由を推測しない。日本語・英語・中国語簡体字・繁体字を扱い、手動再試行や認可の経路を保つ。

追加32回帰、関連138件、全体2233件、型検査・lint・production buildはローカルで成功した。実コンポーネントとCSSを使ったChromium fixtureでは、375pxと1024pxで4言語×2分類を確認し、再試行ボタンを保持し、横にはみ出さなかった。全networkを遮断したfixture検査であり、ログイン済み本番・実API・回答履歴の確認には換算しない。rootも375pxの保存画像を目視した。

## Agentの結論検査

[Agent PR #149](https://github.com/AtsushiHosaka/pals-agent/pull/149)は、現在候補と同じ`146ecf2b816ac6830940fac824bd9e8df90d80e4`を起点とする専用review branchをbaseにした。差分が大きいmain全体を配備候補へ持ち込まず、説明の2ファイルと新規テスト、検証noteをレビューする。新規生成の求値結論だけに結果の数式を要求し、保存済み説明の読取では既定の緩いparserを保つ。v2の生成指示と審査基準は、概要と結論の両方に答えを要求する。

初期候補`136b42a4dad9c29bec70a4e2031386c109794b5b`では新20回帰が旧版10件失敗・10件成功から20件成功となり、関連221件もskipなしで成功した。初期テストの単純計算題材はプロジェクトの題材条件に合わなかったため、最終候補で実質的な推論を要する題材へ置換する。sourceの2ファイルは変えず、テストと説明記録を更新し、最終headに対するCIを別に要求する。

広いローカル実行の47失敗・9error・4skipを成功件数で隠さない。loopback制限46失敗・9error、親compose fixture不足1失敗、MacでのLandlock3skip、未宣言の任意httpx依存1skipがあった。影響する5モジュールを通常権限で確認すると109件成功、httpxの1skipが残った。正規Linux CIの初回`44250860879`は、candidateで既存worker_processesのcoreテストが1件失敗した。同じテスト・worker実装はbaseと一致していたが、タイミング不安定性という原因は未確定である。同headの自然なPR CI`44251800913`とbaseのCI`44251757619`は成功した。初回失敗を保持し、最終headのCIに置き換えて消去しない。

worker sourceの新headは、実際の配備前に正規infraの`TRUSTED_WORKER_COMMITS`へ固定する必要がある。`TRUSTED_AGENT_CHILDREN`は独立verifierの権限を表すため追加先にしない。独立verifierの`189b44378e6e63e5ab7c92d9c5b7d6507acd80f0`と対応するarchive・imageの条件を維持し、workerの変更でverifierの信頼対象を広げない。sourceのCIとimageの公開・署名・配備は別の確認である。

## exact CIと引き継ぎの状態

| 候補 | 正式CI | 状態 |
|---|---|---|
| API #124 `1da88bf` | `44250703622` | failure。原因調査中で、ローカル386件の成功を代替にしない |
| Web #94 `d11e7a9` | `44252212263` | in_progress |
| Agent #149 | 最終headを準備中 | 初期headの再確認は成功。最終headのCIは別に必要 |

APIとAgentは実装担当以外のレビューを含め、Webはrootがproductionの4ファイルを確認した。sourceレビューのP0〜P2指摘がないことと、CIや本番受け入れの成功は別に扱う。本番担当には候補・CI失敗・worker trustの区分を伝達済みである。

## QAと本番受け入れの未完了

過去のQA案には、固定入力の判定が良くても端から端まででは悪化した測定がある。未mergeのQA案を全面採用したり、審査を省略して回答率を上げたりしない。現時点でQAの一般的な誤拒否率を改善したとは主張しない。

#382の定量条件である10題×3回の回答率95%以上、誤った回答の承認0件、求値結論の明示100%、週次CloudWatch集計は、この実装テストだけでは確認できない。30題への拡張も別の評価作業である。単体・CIの通過件数は品質台帳の製品評価分母へ足さない。

本チャットの新規有料呼出は0件。既存US$1枠は他担当と共有するため、追加の実測は候補・問題・モデル・呼出上限・残予算を固定し、本番担当と具体案を調整してから行う。本番へのフラグ適用、画像公開、配備、回答の保存・表示・reload受け入れは、唯一の本番担当へ引き継ぐ。

API flag `PALS_SEMANTIC_REVIEW_REFORMALIZE_ENABLED`は既定offを維持する。候補のsource・環境と検証を固定した署名リリースで有効化し、同じ仕組みでfalseへ戻す。既存の`docs/semantic-review-reformalize-rollout.md`にある監視・戻し方を使い、ここで本番環境は変更しない。
