# 未解決Issueの実行状況

2026-11-05 04:28 JSTにGitHubから取得した63件の一覧。priority:highは23件である。判断記録、総合管理、別チャットの進行、配備待ちも含む。件数を未修正バグ数やコードレビュー完了数とは扱わない。

今回の担当は[Codex](codex://threads/01a1a6ef-927b-7d72-b689-5c442ada7af7)。進行の正本は各IssueとProjectであり、この文書は時点記録である。実装、局所検証、独立レビュー、本番の確認を分けて更新する。

## 今回実装・レビューした範囲

| 対象 | 実装と独立レビュー | 次の受入 |
|---|---|---|
| #217 品質計測 | [API #49](https://github.com/AtsushiHosaka/pals-api/pull/49)はDB commit後の終端、[Agent #49](https://github.com/AtsushiHosaka/pals-agent/pull/49)はLean試行・heartbeat・説明最終失敗・版付きSchemaを実装。[infra #96](https://github.com/AtsushiHosaka/pals-infra/pull/96)は保護fileとcollector設定をoffline準備 | 隔離verifierの制限を保つ出力先・署名付き設定・rotation、CloudWatch実抽出・通知。監視は未稼働 |
| #232/#233 説明の根拠・結論 | [Agent #50](https://github.com/AtsushiHosaka/pals-agent/pull/50)で未証明の同一視を促す指示、複数行haveの引用、具体的結論を修正。新2題のLean監査と実モデル24呼出し、別の固定QA24反復を記録。[統合Agent #51](https://github.com/AtsushiHosaka/pals-agent/pull/51)は657件通過 | 本番と元の症状の確認。一般の精度向上とはしない。新しいQA根拠誤判定は#252 |
| #250 Plus有料転換 | [API #50](https://github.com/AtsushiHosaka/pals-api/pull/50)で支払receipt、13か月保持、未回収を示すreportを実装。実PGで独立再現したUTC窓・snapshot不一致を修正 | 実Stripe、定期回収・削除、操作eventの新データ契約・trackerと集計。本番未収集 |
| #250 後続schema37 | 専用署名契約[API #51](https://github.com/AtsushiHosaka/pals-api/pull/51)、候補と初回software更新[infra #97](https://github.com/AtsushiHosaka/pals-infra/pull/97)をoffline実装。[統合API #52](https://github.com/AtsushiHosaka/pals-api/pull/52)は実PG3群を含む724件通過 | 新image、全36形状/TLS/Aurora/native controller、署名候補と本番受入。旧36候補のimageだけを置換しない |
| #11 質問の数式表示 | 本番sourceに既存Web #9の修正があることを確認。[Web #41](https://github.com/AtsushiHosaka/pals-webfront/pull/41)は実routeから履歴復元までの回帰・記録だけを追加し候補branchへmerge | 本番ブラウザ受入。別session使用中の既存タブは操作していない |
| #251 新たに見つかったCI課題 | coupon状態の試験fixtureとRetry時のfocus検査を[Web #42](https://github.com/AtsushiHosaka/pals-webfront/pull/42)で修正・独立レビュー・merge。全1,721件、型・lint通過。Issue/ProjectはDone | 完了済みなので下の未解決一覧には含めない。製品のa11y変更ではない |
| #252 新たに見つかったQA課題 | 最終版の拒否理由2件に、正しい下界→等号条件の導出を重複とする誤指摘を独立確認。根拠と別の受入条件をIssueへ記録 | 未修正。元の採点を保持し、正例・負例と理由を検証する別の実装へ着手できる状態 |

説明生成の初回比較は旧版・中間版とも2/2で、精度向上は確認していない。固定QAの別測定では、結論欠落は旧4回誤承認・最終4回正しく拒否、正例は両版4回承認だった。一方、未証明の同一視への拒否自体は両4/4でも、正しい理由まで要求すると旧4/4・最終2/4だった。別群を足して改善率を作らない。

## 一覧の読み方

以下は取得時のラベルをそのまま分類した。readyは受入済みや自動マージ可能という意味ではない。他チャットがin-progressの領域は重複編集しない。#138にはreadyとblockedが共存しており、待ち先を確認してから整理する。

| Issue | 優先度 | 担当ラベル | 状態ラベル |
|---|---|---|---|
| [#252 回答QAが正しい証明段階に根拠のない欠陥を付け加える](https://github.com/AtsushiHosaka/pals/issues/252) | high | codex | ready |
| [#250 操作後の離脱とPlus有料転換を、CloudWatchと確定課金記録で計測する](https://github.com/AtsushiHosaka/pals/issues/250) | high | codex | in-progress |
| [#244 Plusクーポンを本番へ出す専用署名appendプロファイルと引換経路を実装する](https://github.com/AtsushiHosaka/pals/issues/244) | high | codex | needs-decision |
| [#242 Plus・Pro・Researchの料金と利用枠を、実測原価と利用分布で再検討する](https://github.com/AtsushiHosaka/pals/issues/242) | high | codex | in-progress |
| [#240 初期ユーザー向けにPlusを1か月使えるクーポンを準備する](https://github.com/AtsushiHosaka/pals/issues/240) | high | codex | needs-decision |
| [#239 AWS費用の増加理由を確認し、機能を保って削減する](https://github.com/AtsushiHosaka/pals/issues/239) | high | codex | in-progress |
| [#237 【引き継ぎ】Claude から Codex へ: 現状と、着手する順序(2026-11-04)](https://github.com/AtsushiHosaka/pals/issues/237) | high | codex | in-progress |
| [#236 日本語の依頼で出力言語が en になった経路を特定する](https://github.com/AtsushiHosaka/pals/issues/236) | high | codex | in-progress |
| [#235 イプシロン問題のベンチマーク結果を X に載せる(共有リンク・下書き・確認)](https://github.com/AtsushiHosaka/pals/issues/235) | high | user | needs-decision |
| [#234 機能修正を次の署名リリースへ配備する（seq18は同一構成更新済み）](https://github.com/AtsushiHosaka/pals/issues/234) | high | codex | blocked |
| [#233 計算問題で説明に最終的な答えが明記されない(双対数 ε²=0 の総和)](https://github.com/AtsushiHosaka/pals/issues/233) | high | codex | in-progress |
| [#232 Lean コードのパネル: 行ごとの説明が出ない、説明欄が上部を占める](https://github.com/AtsushiHosaka/pals/issues/232) | high | codex | in-progress |
| [#231 チャットのタイトルが LaTeX のソースのまま表示される](https://github.com/AtsushiHosaka/pals/issues/231) | high | codex | ready |
| [#229 UI の言語と回答の言語を統一し、初期の言語をブラウザの言語から決める](https://github.com/AtsushiHosaka/pals/issues/229) | high | codex | ready |
| [#228 共有チャットのURLを X に貼ったとき、カード画像(Open Graph)が出るようにする](https://github.com/AtsushiHosaka/pals/issues/228) | high | codex | blocked |
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

## 配備と判断待ち

同一構成のseq18更新だけが本番で完了している。新機能は未配備で、次の署名候補に必要なembedding版の限定読取は承認待ちである。自動承認レビューが旧承認の範囲・期限外として操作を拒否したため、別経路で読み取らない。

Plus1か月と、おおむね最大100人という意向は記録済み。実際の発行数・引換期限は未確定である。料金変更、AWS縮小、全操作の収集開始も実施していない。個別の進捗と質問・回答は[総合Issue #237](https://github.com/AtsushiHosaka/pals/issues/237)と関連Issueからたどる。
