# Codex引き継ぎ後の全体状況（2026年11月5日）

担当はCodex、[担当チャット](codex://threads/01a1a6ef-927b-7d72-b689-5c442ada7af7)は各Issueにも記録した。進行管理は[pals#237](https://github.com/AtsushiHosaka/pals/issues/237)、オーナーへの質問と回答は[#241](https://github.com/AtsushiHosaka/pals/issues/241)を参照する。3つのサブエージェントを並列で動かし、実装後に別の視点から確認した。

## 本番で完了したこと

同一構成のseq18への署名更新は11月5日01:03:21 JSTに完了した。7サービスの稼働、両側の正規readiness、DB最新承認seq18、復旧設定を確認し、一時権限と排他を削除した。次の期限は **11月5日23:53:01 JST**。今回の更新には新機能もDB schema変更も含めていない。[実測結果](seq18-renewal-result-2026-11-05.md)に照合値を残した。

署名の自動更新、期限後の正規復旧、実際のOS再起動は未完了であり、[#142](https://github.com/AtsushiHosaka/pals/issues/142)を開いたままにする。復旧用unitの設定確認と、再起動後の復旧成功は区別する。

クーポン追加後の初回更新用には、[infra#95](https://github.com/AtsushiHosaka/pals-infra/pull/95)で構成不変のcoupon36→software36候補を準備するofflineツールを追加した。82テストと独立レビューを通過したが、本番での署名・更新・再起動は未確認である。

## 依頼ごとの進捗

| 依頼 | 確認・実装したこと | 本番での状態・残作業 |
|---|---|---|
| AWS費用の説明 #239 | Gmailの受信額、Cost Explorer、予算、資源と容量を照合。11月4日23時台の実額52.672 USD、月末予測409.743 USD。主因はEC2・Aurora等の固定費。さらに72時間の9系列と現在のメモリを読み取り計測 | 削減は未実施。低い平均CPUだけで縮小せず、定期DB接続と短い復帰期限を含めて改善する必要がある |
| 料金の再検討 #242 | 本番Plus/Pro/Researchは月10/20/100 USD、月枠1M/3M/15M。最新仕様2M/5M/25Mとの差を確認。保存済み原価は重複を除く523呼び出しで推計1.019662 USD | 料金未変更。欠損・失敗・外部評価を含む請求全体ではなく、利用分布も不足。価格維持を暫定案とする |
| Plus1か月クーポン #240/#244 | API#45/#47、infra#93、Web#40で実際のPlus資格・暦月期限・取消・競合制御・引換画面を実装。API統合#48は602件通過。API60f8cd2とWebe63bc50のimageを非公開ECRへ保存し実体を検証。Web認証設定はTF・seq18・実Cognitoで照合 | 未配備・未発行。新schema専用候補と実Cognito→引換→実利用の統合確認が必要。最大100人・1回・30日引換の具体条件は質問中 |
| プロンプトと最終結論 #233 | 本番系統へのagent#48に続き、[Agent #50](https://github.com/AtsushiHosaka/pals-agent/pull/50)で非標準定義への未証明の同一視を促す指示を修正。characterize/classifyの具体的結論と引用見出しを検査。新2題のLean・axiom監査と実モデル24呼出しを記録し、さらに保存した3入力のQAを両版4回ずつ、計24回反復した。品質計測との[統合#51](https://github.com/AtsushiHosaka/pals-agent/pull/51)は657件と独立レビューを通過 | 初回の生成比較は両版2/2。別の固定QA反復では、結論欠落の誤承認が旧4/4・最終0/4、正例は両4/4承認。一方、別の負例で最終版2/4に誤った拒否理由が残った。未配備・一般の精度向上は未確認 |
| 出力言語 #236 | API#46で明示指定の漏れを修正。否定依頼と教科書の文章を依頼と誤認する回帰も修正、関連315テスト通過 | 未配備。一般のen経路は追跡したが、個別の事例を提出時metadataで特定していない。言語優先順位の判断 #229/#230は未選択 |
| タイトル #231 | 本番系統向けAPI#44を独立検証。タイトル・チャット・共有関連28テスト通過。Web#35は本番系統にマージ済み。修正を含むcoupon36用API60f8cd2・Webe63のimageは公開済み | 正式receipt・署名候補・配備・実画面が必要。後続37用の新imageは未作成 |
| Leanパネル #232 | Web#36のマージを保持。Agent #50で複数行haveの主張全体を同じ節で引用する検査と、API/Webと一致する改行処理を実装。保存済みの履歴読込は維持 | 現本番Webは旧source。新Web・worker配備と実画面の行表示は未確認。全Lean構文の依存関係網羅を保証する検査ではない |
| OGカード #228 | 別チャットがWeb#37/#38/#39を本番系統へマージ。Web#40にも通常mergeで取り込み、214テスト・型・lint・通常build通過 | 現本番Webには未反映。配備後のクローラー/X確認が必要 |
| 品質記録 #216 | 既存270行を保持し、前回までの10行、説明回帰9行、固定QA反復6行を追加して295行。無効な負例も費用を残し、採点から除外した | 異なる題材・指標を1本の精度改善線として読まない。評価から台帳への自動接続は未実装 |
| CloudWatch #217 | infra#94の分類・アラーム修正、[API #49](https://github.com/AtsushiHosaka/pals-api/pull/49)のcommit後終端、[Agent #49](https://github.com/AtsushiHosaka/pals-agent/pull/49)のLean試行・heartbeat・説明最終失敗・Draft202012 Schemaを実装。[infra #96](https://github.com/AtsushiHosaka/pals-infra/pull/96)で保護されたfileの確認とcollector設定をoffline準備。各独立レビューを完了 | 未適用。隔離verifierのegress/rootfsを維持し、安全な出力先・署名付き設定・rotationは未提供。ホスト受信・実抽出・通知遷移とcommit後停止の欠測も残るため、監視稼働済みとはしない |
| 操作後の離脱・Plus転換 #250 | [API #50](https://github.com/AtsushiHosaka/pals-api/pull/50)で支払receiptと13か月の保持・削除、未回収を示すreport v2を実装。独立レビューで再現したproration、UTC日付境界、別snapshotの不一致を修正。37署名契約は[API #51](https://github.com/AtsushiHosaka/pals-api/pull/51)、候補・初回software更新は[infra #97](https://github.com/AtsushiHosaka/pals-infra/pull/97)へ実装。[統合API #52](https://github.com/AtsushiHosaka/pals-api/pull/52)は実PG3群を含む724件と独立レビューを通過 | 未収集・未配備。全36形状/TLS/Aurora/native controller、実Stripe、定期回収/削除、操作eventの新データ契約とtracker、CloudWatchの識別子を含まない集計が必要。first_observedを生涯初回、観測0件を実支払0件とは呼ばない |
| 既存の質問数式表示 #11 | Web #9で修正済み。本番source581fd231とe63のrenderer4blob・関連CSSが同一であることを確認。[Web #41](https://github.com/AtsushiHosaka/pals-webfront/pull/41)の実route・client・hook・KaTeX・履歴再mount回帰と記録を独立レビュー後に候補branchへmerge。production code変更なし | 新Web待ちとはしていない。本番ブラウザ受入は未実施。既存タブは別sessionが使用中で、操作していない |

## AWS費用と料金の判断材料

EC2の現在の2型だけで30日169.86 USD相当、Aurora最低容量とNAT時間料まで足すと268.50 USD相当になる。100 USDは通知予算であり、現在の構成がその額で止まることを示さない。すでに削除されたInterface Endpointや一時DBを、今後も発生する費用へ足していない。詳細は[費用調査](aws-cost-review-2026-11-04.md)。

[容量の追加調査](aws-cost-capacity-2026-11-05.md)では、計算側CPUの72時間平均1.44%と最大99.72%を確認した。待機中のメモリは低いが、現在のコンテナ上限は合計12.5 GiBで、8 GiB機へ単純に縮小できる根拠にはならない。AuroraへはALBの30秒確認、outboxの15秒、OCRの最大30秒で接続する経路がある。0 ACU設定だけでは休止条件を満たせるとは見込めず、復帰時の3秒・5秒の期限も検討が必要である。

モデル原価の保存推計とAWSは別の費用である。外部ベンチマークの予算用見積もりも別に記録した。Lunaの全入力に12時間キャッシュ書込相当の0.25 USD/百万tokenを掛けた保守値で、通常入力単価やアプリの版付き見積器、実請求額とは一致させない。[試行の単価と計算式](prompt-benchmark-2026-11-05.md)を明記し、過去の数値は保持した。保存済み523呼び出しの推計から、保存に到達しなかった処理や外部ベンチマークを含む請求全体は推定できない。Researchという高額プランはすでにあり、年齢だけで新しい価格を決める根拠はない。先に利用枠の仕様差、欠損・失敗原価、固定費を確認する。[料金確認](pricing-review-2026-11-04.md)に計算式と制約を残した。

## 判断・原本・次の工程

オーナーが承認したのは、匿名化した費用公開、実際のPlus1か月、同一構成候補179a438b…7685db2の署名と本番適用である。新クーポンschemaやTerraform applyの承認へは広げない。クーポンの具体的なコード数と引換期限は未回答で、コード本体や利用者情報は公開しない。

[次期配備の準備](release-candidate-preparation-2026-11-05.md)では、cleanなsource一式と公開済みの実imageを固定した。正式receiptに必要なembeddingの版だけが不明である。保護された本番設定の単一項目を読む操作は、自動承認レビューで既承認の範囲・期限外として拒否された。操作は未実行で、オーナーの明示承認を質問中。別経路で回避せず、候補生成と本番適用を分けている。

原本は元リポジトリのGit対象外`pals-scripts/outputs/codex-takeover-20261104-01a1a6ef/`へ保存した。ディレクトリ0700、ファイル0600で、SHA-256一覧を付けた。公開する費用・品質の集計、構成と判定の定義はdocsと[品質台帳](quality-ledger/README.md)に残す。実装PRは正しい本番系統をbaseにしてpushした。親のsubmodule参照を、開発中の各枝へ一括変更していない。

[過去のプロンプト回帰の監査](prompt-regression-audit-2026-11-05.md)では、最終成功15/16/16件は再現できたが、一部の定義説明の採点値は保存フラグと一致しなかった。Leanの直接定義が、説明中の指数関数・冪級数との同値まで証明するとも言えない。旧6題の54件を新規実行として台帳へ足さず、採点規則と形式化の対応を先に確認する。

[行動計測案](product-analytics-plan-2026-11-05.md)では、最後の操作を離脱原因と断定せず、観測窓内の次段階への未到達を集計する。有料PlusとクーポンPlusは別に数え、クーポン経験者の後日の支払も追える定義にする。現時点のDBだけでは初回実支払の人数を確定できず、過去のクリックも復元できない。

次は、期限更新を継続できる運用、クーポン専用の検証可能な候補、元の症状に対応するプロンプト評価、負荷に基づく費用削減の順に残作業を進める。機能配備は[#234](https://github.com/AtsushiHosaka/pals/issues/234)で追跡する。#222/#223の原因、#137の10秒目標、#235の共有リンク・画面確認、#162と#229/#230のプロダクト判断は未完了のまま区別して残す。

オーナーから全Issueの実装・レビューを継続する指示を受け、3つのサブエージェントとrootで作業を進めている。[63件の時点一覧](issue-execution-status-2026-11-05.md)に、23件の高優先度を含む担当・状態をまとめた。独立レビューで見つけた欠陥は通常の追加commitで修正する。本番での受入が残るIssueを、局所試験の通過だけで閉じない。

## 配備候補を取り違えないための対応表

| 段階 | APIのsource・DB契約 | imageと実行状態 |
|---|---|---|
| 稼働中seq18 | 9f45a39、registry35 | 現本番。署名更新だけを実施済み |
| #249のcoupon36候補 | 60f8cd2、registry36。Webはe63bc50 | 実image公開・inspect済み。正式receiptと未署名候補は未生成 |
| #250の後続37準備 | 統合API #52の32ceeb2、registry37 | 新image・正式receipt・実候補は未生成。新sourceの通常startupは37必須 |

この3つのregistry件数は、各commitのmanifestから読み取り確認した。新37 sourceのimageだけを、旧36候補へ差し替えない。品質・説明workerの統合Agent #51も、新しいimageや配備候補へはまだ組み込んでいない。全ての台帳・局所試験と、本番の通し確認を分ける。

## 追加で見つけて解消したCI課題

[#251](https://github.com/AtsushiHosaka/pals/issues/251)は、既存modal試験でcoupon statusの応答が未定義だったため、Retryのある画面を全action disabledとして検査していた課題である。元のassertionを保持して状態を明示し、Retryが見える場合も別に検証した。[Web #42](https://github.com/AtsushiHosaka/pals-webfront/pull/42)を独立レビュー後に候補branchへmergeし、全1,721件・typecheck・lintを確認してIssueとProjectをDoneへ更新した。本番のa11yを変更したとは報告しない。

Web #41と#42を取り込んだa835b471は、e63bc50からtest/docの4ファイルだけが変わっている。アプリsource・設定・lockfileの差分は0で、既存imageや#249のsource pinは変更していない。#11の本番ブラウザ受入は残る。

## 固定QA反復で確認したこと

[Agent #52の固定QA反復](https://github.com/AtsushiHosaka/pals-agent/blob/c6dfc001b24559f37027700fa5185bb6c3a4a4fc/testdata/explanation-qa-repeat-v1/README.md)では、同じ保存済み説明3種類を旧版・最終版へ各4回渡し、24回で停止した。結論欄に具体的な条件がない説明は、旧版が4回とも承認し、最終版が4回とも欠落を理由に拒否した。正しい説明は両版4回とも承認した。この1入力について過剰拒否はなかったが、他の説明への一般化はしない。

未証明の同一視を含む負例は両版4回とも拒否した。一方、最終版の2回には、下界の証明から等号条件へ進むことを「重複」とする誤った指摘が加わった。正しい判定と理由の両方を求める事前基準では、旧4/4・最終2/4である。拒否率だけで改善を報告せず、この残るQA課題は[#252](https://github.com/AtsushiHosaka/pals/issues/252)で追跡する。

24件すべてにusageがあり、入力82,104・出力4,985 token、予算用見積もり0.02301850 USDだった。推論3,127 tokenは出力の内数。responseには全件で保持表記24h・tier defaultがある。ただし、その表記と価格表の書込料金の対応、実請求額は未照合である。既存の生成＋QA測定とは別の6行として台帳と6図へ反映する。新しい数学問題の生成、本番E2E、全体精度の改善率を測った結果ではない。
