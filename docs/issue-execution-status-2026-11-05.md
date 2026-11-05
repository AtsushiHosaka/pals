# 未解決Issueの実行状況

2026年11月5日15:18 JSTにGitHubから取得した64件の一覧。priority:highは23件である。#255は取得時点ではクーポン候補の署名・読取検証の判断待ちだった。15時台に承認を受領したが、別チャットの本番seq19更新で旧predecessorが無効になったため未実行で判断記録として閉じた。共有カードの#253はこの取得時点では閉じられている。件数には判断記録、総合管理、配備待ちが含まれ、未修正バグ数とは一致しない。

担当は[このCodexチャット](codex://threads/01a1a6ef-927b-7d72-b689-5c442ada7af7)。3つのサブエージェントと実装・独立レビュー・統合を分担する。進行は各IssueとProjectに残し、本書は取得時点の一覧と、その後15時台までの作業記録を分ける。

## 実装・レビューと残る受入

| 対象 | 今回の実装・確認 | 残る受入 |
|---|---|---|
| #231 タイトル | API#65/Web#46まででitalic内の積とMarkdownの境界を修正。API対象66件・Web対象91件、API統合122件・Web全145ファイル1,891件。元のAPI#44/Web#40とAPI#48へ統合 | 新image・本番と共有画面での確認 |
| #252 QAの誤指摘 | 最初の候補は結論欠落を3/3誤承認し不採用。唯一の追加修正は同じ4入力で各3/3の厳格成功。全24理由を独立照合、Agent#53を#51へ統合し関連590件通過 | 固定群に限る受入。一般精度・生成全体・追加質問の実モデル精度・本番の改善は未確認 |
| #232/#233 説明・結論 | Agent#50の引用と具体的結論の修正を保持。保存済み親の改行と不変hashの不整合をAgent#55/API#60で修正し、実worker→API→PGで独立10件確認 | 新worker・本番の元の症状、Lean行表示 |
| #236 出力言語 | API#46を保持。Agent#55で現APIのnullableな言語項目を厳格に受ける互換性を追加 | 個別の日本語→en事例、言語優先順位#229/#230の判断、本番受入 |
| #250 支払・転換 | API#53/#57/#59で失敗receipt後の公平回収・排他を実装し、親担当も実PG5件を確認。元#50/#51へ反映 | 実Stripe・定期runner/削除・操作event契約とtracker。本番未収集 |
| #250 後続37 | API#52へ品質・支払・37契約・親参照を通常merge。536単体、差分71、PG119件通過。広めのPG群39件は失敗し、代表3件は旧32ceでも同じfixture不備を再現 | 39件全部の旧版同一性は未確認。新image・完全schema・Aurora/PKI/native controllerと本番受入 |
| #217 CloudWatch | API#64/Agent#56でruntime診断のHTTP→API→DB終端を修正。独立実PG/mTLS16件も通過し、API#52/Agent#51へ統合 | 実モデル・生成全体・本番の受入とcollectorの収集/抽出/通知は未完了 |
| #216 評価記録 | 既存295行を保持し314行へ追記。失敗案8、追加修正8、タイトル測定3。6グラフ再生成・監査エラー0 | PR#254を独立レビュー後に親#243へ統合。既存2群の人手採点と原本から8行ずつ再生成して台帳と一致。汎用の自動収集・採点・appendは未実装 |
| #234/#244 配備 | 単一項目の承認済み読取は11:13完了。13:51のfresh metadata照合も一致。API5c1a2fd7/Web11b62967の実imageと正式receiptを固定。未署名候補fa94cf78を親担当も照合 | 旧fa94への承認を受領したが、別チャットの本番seq19で前提変更となり未実行。新候補の具体化と本番受入。37用imageを36へ混ぜない |
| #240 初期Plus | 実Plus1か月の資格・期限・取消・引換を実装済み。最大100人程度という意向を記録 | 発行数・引換期限の具体条件、実Cognito→引換→利用。本番発行0件 |
| #239/#242 費用・料金 | Gmail/Cost Explorerの費用、72時間の容量、保存原価523呼出しを調査済み | AWS縮小・料金変更は未実施。欠損/失敗原価・利用分布を含む採算と実負荷検証が必要 |
| #228/#11 共有カード・質問数式 | #228は別チャットが本番・実X下書きを確認して完了。質問数式は既存sourceとWeb#41の回帰を保持 | #248の追加カード修正、#11の本番ブラウザ受入は継続。別セッションのタブを重複操作しない |
| #251 進捗スクリプト | 前回の監査・修正・独立検証でdone/closed | 製品のa11y修正とは区別し、下の未解決一覧へは含めない |

15時台には#255を新設した。API#66の試験DB分離は独立25件を通過してAPI#52の6985402へ統合した。新Agent向けimage補助infra#98は、中断時回収とcanonical archive再照合のP2指摘2件を修正中。一覧のラベルは取得時点の値として保持し、後から完了扱いへ読み替えない。

追加レビューのsource・測定・限界は[記録](review-followups-2026-11-05.md)、費用は[AWS調査](aws-cost-review-2026-11-04.md)と[容量調査](aws-cost-capacity-2026-11-05.md)、料金は[再確認](pricing-review-2026-11-04.md)を参照する。別群を合算して改善率を作らない。

## 取得時点の未解決一覧

以下のラベルは15:18 JSTの取得値。readyは受入済みや自動merge可という意味ではない。他チャットがin-progressの領域は重複編集しない。#138のready/blocked共存も取得値のまま残す。

| Issue | 優先度 | 担当ラベル | 状態ラベル |
|---|---|---|---|
| [#255 判断: クーポン36候補の署名と期限付き読み取り検証](https://github.com/AtsushiHosaka/pals/issues/255) | high | user | needs-decision |
| [#252 回答QAが正しい証明段階に根拠のない欠陥を付け加える](https://github.com/AtsushiHosaka/pals/issues/252) | high | codex | in-progress |
| [#250 操作後の離脱とPlus有料転換を、CloudWatchと確定課金記録で計測する](https://github.com/AtsushiHosaka/pals/issues/250) | high | codex | in-progress |
| [#248 Lighten shared-card Lean backdrop and add truthful English verification footer](https://github.com/AtsushiHosaka/pals/issues/248) | 通常 | codex | in-progress |
| [#244 Plusクーポンを本番へ出す専用署名appendプロファイルと引換経路を実装する](https://github.com/AtsushiHosaka/pals/issues/244) | high | codex | in-progress |
| [#242 Plus・Pro・Researchの料金と利用枠を、実測原価と利用分布で再検討する](https://github.com/AtsushiHosaka/pals/issues/242) | high | codex | in-progress |
| [#240 初期ユーザー向けにPlusを1か月使えるクーポンを準備する](https://github.com/AtsushiHosaka/pals/issues/240) | high | codex | needs-decision |
| [#239 AWS費用の増加理由を確認し、機能を保って削減する](https://github.com/AtsushiHosaka/pals/issues/239) | high | codex | in-progress |
| [#237 【引き継ぎ】Claude から Codex へ: 現状と、着手する順序(2026-11-04)](https://github.com/AtsushiHosaka/pals/issues/237) | high | codex | in-progress |
| [#236 日本語の依頼で出力言語が en になった経路を特定する](https://github.com/AtsushiHosaka/pals/issues/236) | high | codex | in-progress |
| [#235 イプシロン問題のベンチマーク結果を X に載せる(共有リンク・下書き・確認)](https://github.com/AtsushiHosaka/pals/issues/235) | high | user | needs-decision |
| [#234 機能修正を次の署名リリースへ配備する（seq18は同一構成更新済み）](https://github.com/AtsushiHosaka/pals/issues/234) | high | codex | in-progress |
| [#233 計算問題で説明に最終的な答えが明記されない(双対数 ε²=0 の総和)](https://github.com/AtsushiHosaka/pals/issues/233) | high | codex | in-progress |
| [#232 Lean コードのパネル: 行ごとの説明が出ない、説明欄が上部を占める](https://github.com/AtsushiHosaka/pals/issues/232) | high | codex | in-progress |
| [#231 チャットのタイトルが LaTeX のソースのまま表示される](https://github.com/AtsushiHosaka/pals/issues/231) | high | codex | in-progress |
| [#229 UI の言語と回答の言語を統一し、初期の言語をブラウザの言語から決める](https://github.com/AtsushiHosaka/pals/issues/229) | high | codex | ready |
| [#226 Verify learning-context constraints through full proof and stored-answer paths](https://github.com/AtsushiHosaka/pals/issues/226) | 通常 | codex | ready |
| [#224 Decision: context-aware angle units and curriculum-aware explanations (#183)](https://github.com/AtsushiHosaka/pals/issues/224) | 通常 | user | 未設定 |
| [#223 本番で lean_explanation_failed が簡単な質問でも出続けている](https://github.com/AtsushiHosaka/pals/issues/223) | high | codex | ready |
| [#222 Lean検証後の説明生成が lean_explanation_failed で失敗する](https://github.com/AtsushiHosaka/pals/issues/222) | high | codex | ready |
| [#218 Mac mini 関連のファイル・ランナー・設定を撤去する](https://github.com/AtsushiHosaka/pals/issues/218) | 通常 | claude | ready |
| [#217 CloudWatch で Lean 失敗の種別と精度を監視する(本番は AWS)](https://github.com/AtsushiHosaka/pals/issues/217) | high | codex | in-progress |
| [#216 評価結果を一か所にまとめ、失敗の種類と精度の推移をグラフにする](https://github.com/AtsushiHosaka/pals/issues/216) | high | codex | in-progress |
| [#215 Lean 証明の失敗を、すぐに通知する仕組みを作る](https://github.com/AtsushiHosaka/pals/issues/215) | 通常 | user | needs-decision |
| [#213 判断ログ(索引)](https://github.com/AtsushiHosaka/pals/issues/213) | 通常 | 未設定 | 未設定 |
| [#195 公開・配備の承認事項を決める（停止指示の解除、LRC-T017・T020ほか）](https://github.com/AtsushiHosaka/pals/issues/195) | 通常 | codex | needs-decision |
| [#193 利用可能問題の定義と集計ツールを作る（#139の子）](https://github.com/AtsushiHosaka/pals/issues/193) | 通常 | codex | in-progress |
| [#192 pals-agent#33 を最新カードで再封緘し、pals2語彙と整合させる](https://github.com/AtsushiHosaka/pals/issues/192) | 通常 | codex | blocked |
| [#190 pals-agent#37 の図呼び出しを再実行して検証する](https://github.com/AtsushiHosaka/pals/issues/190) | 通常 | codex | blocked |
| [#189 pals-agent#39 の段落分割を取り込み、カタログを再生成して検証する](https://github.com/AtsushiHosaka/pals/issues/189) | 通常 | codex | blocked |
| [#187 pals-agent#27 の教科書・入試カードを独立に数学審査する](https://github.com/AtsushiHosaka/pals/issues/187) | 通常 | codex | blocked |
| [#186 欠落分野のカード追加の担当と優先分野を決める](https://github.com/AtsushiHosaka/pals/issues/186) | 通常 | codex | needs-decision |
| [#184 同義シンボルの統合と重複カードの整理を独立審査つきで行う](https://github.com/AtsushiHosaka/pals/issues/184) | 通常 | codex | ready |
| [#183 学習順序の方針を決める（弧度法・面積・凸多角形ほか）](https://github.com/AtsushiHosaka/pals/issues/183) | 通常 | codex | needs-decision |
| [#181 学習順序の書き替え案を適用し、残り63件を検査する](https://github.com/AtsushiHosaka/pals/issues/181) | 通常 | codex | ready |
| [#180 監査修正のうち意味が未確認のOpenMath約140件を独立に検査する](https://github.com/AtsushiHosaka/pals/issues/180) | 通常 | codex | ready |
| [#178 [Codex] Draft・Recipe DB の拡充と検証](https://github.com/AtsushiHosaka/pals/issues/178) | 通常 | codex | ready |
| [#170 リポジトリの外部からの書き込み制限](https://github.com/AtsushiHosaka/pals/issues/170) | 通常 | user | needs-decision |
| [#169 進行管理の運用(この Issue 体系・Project・Discussions)](https://github.com/AtsushiHosaka/pals/issues/169) | 通常 | claude | in-progress |
| [#168 PR監視と競合解消の自動運用](https://github.com/AtsushiHosaka/pals/issues/168) | 通常 | claude | in-progress |
| [#167 pals#119 (チャット内図の契約) の保留](https://github.com/AtsushiHosaka/pals/issues/167) | 通常 | user | blocked |
| [#165 pals-agent#37 と #39 の前提(カタログ再ビルド・ジオメトリカード)](https://github.com/AtsushiHosaka/pals/issues/165) | 通常 | claude | blocked |
| [#164 pals-agent#26 と #32 のマージと配備](https://github.com/AtsushiHosaka/pals/issues/164) | 通常 | claude | blocked |
| [#163 Mac mini の撤去と AWS への CI/CD 切り替え](https://github.com/AtsushiHosaka/pals/issues/163) | 通常 | user | needs-decision |
| [#162 pals#134 を本番に出す範囲を決める](https://github.com/AtsushiHosaka/pals/issues/162) | high | user | needs-decision |
| [#144 AWS料金通知が実際に配信されることを検証する](https://github.com/AtsushiHosaka/pals/issues/144) | high | codex | in-progress |
| [#143 実ホスト再起動とAurora設定反映後の正規復旧を保守枠で検証する](https://github.com/AtsushiHosaka/pals/issues/143) | 通常 | claude | blocked |
| [#142 署名の期限更新と期限後の正規復旧を運用可能にする](https://github.com/AtsushiHosaka/pals/issues/142) | high | codex | in-progress |
| [#141 ASGと実行枠の増減を実装し30人同時利用を実測する](https://github.com/AtsushiHosaka/pals/issues/141) | 通常 | claude | blocked |
| [#140 通常largeと大会xlargeを正規の停止・drain・復旧手順で切り替える](https://github.com/AtsushiHosaka/pals/issues/140) | 通常 | claude | ready |
| [#139 重複・旧revision・非アクティブ行を除いて利用可能な問題1,100件を確立する](https://github.com/AtsushiHosaka/pals/issues/139) | 通常 | codex | ready |
| [#138 実コンパイル・admission済みの行列式R2とπ下界R3を独立審査後に検索公開する](https://github.com/AtsushiHosaka/pals/issues/138) | 通常 | codex | ready, blocked |
| [#137 公開回答10秒目標の未達を、正しさを保った実測で解消する](https://github.com/AtsushiHosaka/pals/issues/137) | 通常 | claude | blocked |
| [#136 未配備の原子的な使用量・課金証跡保存を正規リリースして検証する](https://github.com/AtsushiHosaka/pals/issues/136) | high | codex | in-progress |
| [#41 [QA][Pro] PDF/PNG materials and OCR entry points are unavailable on tested screens](https://github.com/AtsushiHosaka/pals/issues/41) | 通常 | user | needs-decision |
| [#39 [QA] Project follow-up asks for the theorem already visible in the same conversation](https://github.com/AtsushiHosaka/pals/issues/39) | 通常 | user | needs-decision |
| [#38 [QA][Pro] Investigate one Home proof review rejection that recovered on Retry](https://github.com/AtsushiHosaka/pals/issues/38) | 通常 | claude | ready |
| [#37 [QA][Pro] Accepted formal-proof Retry ends in generic failure without Lean evidence](https://github.com/AtsushiHosaka/pals/issues/37) | 通常 | user | needs-decision |
| [#36 [QA][Pro] Sharing preview fails for a completed Project proof](https://github.com/AtsushiHosaka/pals/issues/36) | 通常 | user | needs-decision |
| [#16 【検証課題】モデル切り替えUIの提供条件と操作経路を確認する](https://github.com/AtsushiHosaka/pals/issues/16) | 通常 | claude | ready |
| [#14 【一時的事象】ゲストの積分質問が初回に回答失敗し、再送では成功した](https://github.com/AtsushiHosaka/pals/issues/14) | 通常 | claude | blocked |
| [#13 回答表示後のLeanソースが読み込めず、Check statusでも回復しない](https://github.com/AtsushiHosaka/pals/issues/13) | 通常 | user | needs-decision |
| [#12 Mathematics設定が読み込みエラーになり、Retryでも回復しない](https://github.com/AtsushiHosaka/pals/issues/12) | 通常 | user | needs-decision |
| [#11 認証済みチャットの質問本文でLaTeXが数式として表示されない](https://github.com/AtsushiHosaka/pals/issues/11) | 通常 | codex | blocked |

## 配備と判断の扱い

#228/#253の最新記録で、14時台にshared-cardのseq19が本番適用済みと確認した。Web3bc3f708、manifest1630bc12、schema35を維持した更新であり、保存原本のECDSA署名を親担当も独立検証し、期限11月6日11:10:57 JSTを確認した。新しいlive検査は行っていない。旧seq18の期限を現行期限として使わない。#248は別チャットが追加修正を進めている。同じ本番へ別候補を同時適用しない。

オーナーは#255のfa94候補への署名・全読取検証を承認したが、候補のpredecessorが旧seq18のため実行を停止した。署名/IAM/追加SSM/native/DB/サービス操作は0回。異なるdigestへの承認流用はせず、新しい候補を#234/#244で具体化する。質問・回答・理由と影響は#241/#255へ記録した。
