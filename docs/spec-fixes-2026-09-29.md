# 仕様監査14項目の修正状況 — 2026-09-29

**判定：全体は未完了。** 最新の利用枠回復後の結果は末尾の追記を優先する。 [元の監査](spec-audit-2026-09-29.md)への修正対応を、実装・実依存テスト・実アプリ結果に分けて記録する。対象は root `02801ca`、API `858dd16`、agent `ab42335`、web `7837f8f` を基点とする未コミット変更を含む作業ツリーであり、公開済み main 単体や本番稼働の合格を意味しない。実ジョブの状態は本書作成時点の親担当の確認結果で、後続の再実行結果は追記する。

## 元の指摘との対応

| # / 仕様 | 現在のproductionコード・契約 | 実行済みの検証と残件 |
|---|---|---|
| 1 / DPB-005 必須migration欠落 | `production_database_release.py` に explanation retry・billing・typed catalog等を統合。runtime readiness、最小権限、canonical FK trigger判定、非公開catalog metadata参照を修正。 | 正規SQLを適用した実PGで従来17 stepsとrestricted runtime readinessを確認。最終QA運用障害migrationを追加して計18 stepsとし、実PGreadiness回帰も合格。signed AWS bootstrap全体の実行は未確認。[DB証拠](core-rcp-rpcs-implementation-evidence-20260929.md#全-registry-gate-最終結果)。 |
| 2 / BILL-002/003 quota・冪等性 | `billing_admission.py` とproof作成を接続。Free累計3／Pro期間100、予約・job・idempotency・outboxを同一transaction化。失敗時の自動返金なし。必須 `Idempotency-Key` と同一要求replay／再利用拒否を実装。 | 実PGの並列予約・同一key競合・owner分離を確認。13か月後のdetail削除＋永久tombstoneは下記の承認済み契約。 |
| 3 / BILL-001/004/005/007/010 課金導線 | `BillingSettings`、billing routes、server管理Checkout/Portal、raw-body署名Webhook、権威あるsubscription再照合、durable operation、claim付きcontent-free usageを実装。実設定のmini／nano固定releaseを公式価格snapshot registryへ追加し、記録拒否を修正。 | 実PG・実HMAC・API/worker unitで検証。料金identity5通りの実PG保存に加え、新workerの二項平方でgeneration-call 4件の実usage保存を確認（Stripe請求ではない）。外向きStripe transportはテスト代替。**Stripe未設定のため実Checkout／Portal／Webhook往復は未確認**。未設定toastの実UI確認を成功決済と扱わない。 |
| 4 / DPB-009 idle scan | `explanation_retry.py` をstartup一回＋通知駆動へ変更。既知の未処理仕事だけbounded retryし、commit結果不明時は同owner/keyを再照合。永続outboxを維持。 | recovery/readiness unitと実PG権限負例を確認。空の15秒周期scanを除去。実Aurora自動休止・請求への効果は未測定。 |
| 5 / CORE-003/006 選択文章QA | API→worker→generator/reviewerへ `selected_text` を渡し、clarification completion receipt v3をcanonical質問contextに結合。 | serializer→実API validator、実PGの誤選択digest拒否・正しいv3完了を確認。単体model doubleは文章品質の証拠ではない。日本語drag質問と親回答への再質問が実モデルでcompleted。選択文・親本文を含むv3 receiptと全出力hashを独立再構築して一致。新しい証明でも同操作と保存済み独立QAの一致を確認し、動画収録済み。 |
| 6 / CORE-003/006 親回答context | APIが完了済み親のID・質問・回答全文・key pointsをowner／同proof境界で取得。生成・QA双方へ渡し、親本文を新しい公理として扱わない。完了時にcontextをDBから再構築して照合。 | 実PGで親本文差替え・異なるcontext・新規旧v2公開を拒否し、歴史的v2のread/replay互換を確認。修正後の親回答再質問は実モデルでcompleted、分配法則の逆利用による回答内容とv3結合を独立確認。 |
| 7 / CORE-004/006/008 i18n | 表記衝突／置換不可警告を4言語化。保存された証明・補足の本文と状態／失敗は保存言語、メニュー・操作・右パネルはUI言語。観測timeoutをserver生成失敗と区別し、同IDのGET再確認を提供。 | frontend全体 **88 files / 912 tests PASS**、最終guardの関連6件・TypeScript・対象ESLint PASS。混在言語・locale変更・deadline→同ID回復をテスト。既存Chromeで4 locale、未設定toast、再ログイン後の保存証明復帰を確認。pending／status再確認のweb修正は実適用済み。[旧i18n記録の冒頭訂正](i18n-completion-2026-09-29.md)を優先。全言語での新規生成完走を意味しない。 |
| 8 / LRC-006/007 aligned Draft | workerが自然言語要求の取得結果をprepare/reuseし、一意のimmutable五field Draftからv4 reference＋methodを作ってRecipe選択。選択時はexact sourceを使用。 | worker/pipeline/client契約unit、実PG alignment・selection、実Lean corpusを確認。実アプリで公開済みRecipeにhitする全経路とは区別。 |
| 9 / LRC-008/009 NoRecipe証跡 | canonical query、考慮候補・除外結果・署名結果を保存し、generation claimでfenceしたimmutable attemptへ結合。保存ack前にfallback生成しない。 | 実PGでcross-job／wrong・expired claim／未結合／並列replayを検証。[LRC更新記録](lean-recipe-catalog-spec-loop-ledger.md#implementation-evidence-update--2026-09-29)。 |
| 10 / LRC-007・RCP-003/006 認証500 | 非ASCII credentialを安全なUTF-8 byte比較で拒否。Recipe semantic reviewerは専用credential・principal・source bindingを持つ別actorへ分離。HTTP境界もclosed化。 | 不正header認証unitとdedicated actor/transport unit。一般workerによるv3送信拒否をtransport前に確認。実ネットワーク全構成の運用負荷検証は未実施。 |
| 11 / BILL-008 Google | production Terraformの条件付きGoogle provider・Hosted UI domain・非秘密設定、外部secret-safe IdP provisionerの配線を追加。 | code／契約検査とpasswordフローの証拠は存在。**Google credential未設定、Google実認証は未確認**。 |
| 12 / LRC-011/012・DCE 評価／拡充 | squareの実admission witness・versioned7case corpusを追加。typed API-owned immutable catalog、16 profile／222 card loader、独立署名review・inactive admission・評価／activation gateを実装。`PALS_TYPED_CATALOG_ENABLED`で通常workerへprofile routingを接続し、typed結果をgeneric Recipe参照へ変換しない。 | 実PG＋mTLS＋pinned Leanのsquare corpus合格。routingの独立コードレビュー・関連20 tests／型検査は合格。実workerでmatrix profile選択は確認したが取得は不適合no_match。grammar・provider usage解析・式ASTを修正。旧診断を保持して利用枠回復後に12queryを実行。期待方針6/6・誤答除外6/6だが構造化11/12で逆行列述語の同語反復が残り公開gate不合格。matrix6件は実embedding・inactive DB6rows、active0。activation未完。学校36/321・大学25/500 filled、admitted coverage0、**760 cells不足・advanced500未具体化**。generic PFI実DBは空のまま。[DCE契約と限界](typed-catalog-runtime.md)。 |
| 13 / RCP・RPCS 記録の過大判定 | v1/v2 model由来proposalを既存catalog/alignment/receipt/trace込みで検査。同proposal競合とhistoric evidence validationを修正。RPCSはcandidate→実Lean→専用reviewer v3→durable terminal gateを追加。 | RCP実PG・Lean＋unit22件、RPCS関連32件合格。semantic approvalは明示された独立review／fixtureでありライブLLM審査ではない。[詳細証拠](core-rcp-rpcs-implementation-evidence-20260929.md)。過去ledgerの一律Verifiedや古い未実装表を現状の全体判定に使わない。 |
| 14 / BILL-009・DPB-008/010 spec衝突 | 承認済みbilling specをSSM SecureString JSON、Terraformに秘密値なし、既存hostのTLS egress、no NATへ統一。Google secretも独立したSSM object。worker専用最小IAM roleと短期sessionの`credential_process`、host role／IMDS／DB接続の隔離を追加。userdataはgzip化し、tar buildのDockerfile指定をarchive相対pathへ修正。 | [BILL requirements](../specs/individual-billing/requirements.md)／design／tasksとproduction配線を整合。隔離sourceはfreeze済み。infra Python5件・Terraform validate／mock5件合格。実AWS IAM・session更新・firewall・secret配布・egress・releaseは未検証。ローカルworkerのnamespace隔離は実適用・接続検証済み。 |

## 現在の実アプリ結果

- **証明・説明・QA**：新しい二項平方 `a46643b0-cdea-48b1-b6ac-e604b026f427` はverified＋説明completed。導入で変数を置き、一度の展開から結論へ進む本文で、以前の証明全体の反復は再発しなかった。元の失敗例の保存本文を書き換えた結果ではない。
- **選択文からの質問**：新証明の部分質問 `e6517a2b-303a-47a4-99fa-40942b1ce9fc` と、その回答への再質問 `85cbf8ff-a6c6-4065-b00a-8094ad3d7ec9` は実モデルでcompleted。後者は分配法則と交換法則の役割を正しく区別。保存された3件の独立QAの全hash・session・選択文と親本文を含むcontextを再構築して一致した。[証拠](../output/spec-fixes-20260929/fresh-ui-completion-evidence.json)。
- **画面**：同じChromeタブで4言語設定、Stripe未設定のtoast、右側Lean panel、project配下のchat title、ログアウト・再ログイン後の保存証明復帰を確認。更新後も証明と補足2件を表示でき、console error/warningなし。
- **古い停止履歴**：本人限定の読取診断と、保存言語による理由表示を追加。保存情報が不足・不整合な場合を進行中の表示と区別し、断定できない場合は判定不能と明示。元の質問全文を入力欄へ戻せるが未送信文は上書きしない。実画面で照合不整合／修正上限／判定不能を確認。操作前後でjob114件、利用枠予約2件、最新作成時刻、対象履歴が不変だった。[UI/実PG証拠](../output/recovery-diagnosis-validation-20260930/validation.md)。旧37件は再開不可7件・判定不能30件であり、自動再生成や履歴の捏造はしていない。

[動作確認動画](../output/spec-fixes-20260929/pals-spec-fixes.mp4)は実Chromeの画面フレームから作成した約67秒のH.264動画。長い生成待ちは区間を分けた。成功した主フローと停止履歴の入力復元を収録し、全仕様や任意入力の成功を証明するものではない。

## 実行中に見つけた追加不具合

API→reconciler通知が、2つの共有networkのうちDB側へ名前解決され、固定peer検査で拒否されていた。e2e専用aliasへ修正し、許可peerは拡張していない。新rankの通常通知→Lean→QA→説明完了を実確認した。

候補の保存後に通知や応答が失敗した場合は、private APIから候補ID・生成claim・source hash・artifact・Recipe bindingを完全照合し、同じ候補の通知と確認を続ける。二重import／別生成claim／追加生成は行わない。確認済み候補に限り330秒wait＋360秒visibilityを使う。QA開始前も候補のimmutable bindingを照合し、旧claim不整合のままモデルを呼ばない。QAの最大3試行を覆うvisibility延長にも失敗した場合は呼び出さない。実HTTP応答喪失の注入試験は未実施で、unit・実PGの証拠と通常通知の実成功を分けて扱う。[境界検証](../output/candidate-import-recovery-20260930/review.md)。

workerのDB隔離は当初OrbStackのSNATで破られた。networkとHBAだけに依存せず、worker自身のnamespaceへDB／IMDS拒否を設置してからUID/GID65532・全capability0へ落とす形へ修正。workerのDNS／直接IP／host転送／gateway転送は拒否、APIとhost管理のSELECT1は成功。既存workerへの適用と同一コンテナ再起動を実施した。再起動前後でcontainer/image ID同一、起動時刻のみ変化しhealthy。nftは同じ3規則、全capability0・4DB経路拒否・API/host接続を再確認。container/network/volume一覧も不変だった。[隔離証拠](../output/worker-capability-validation-20260930/validation.md)。AWS実環境の強制は未検証。

## 行列と検索の結果

元の6件では加算・スカラー倍・転置がverified＋説明完了。修正後の積 `de59354d-d5df-4969-99ed-1f50add7bcb3` もverified＋説明完了。逆行列の旧失敗はLean 3形式のlet-inが原因だった。実失敗候補からinだけ除去した同一命題はpinned Leanで成功し、Lean 4生成指示とlet内の代入を証明開始と誤認しない抽出を修正した。旧切断targetの承認receiptで昇格することも拒否する。新inverse `39d78ec6-3a26-49fe-88e3-f0f37f4fd6a2` はLean成功後、通常の再配送でQAへ進んだが、16:11:12 UTCに独立レビュー未完了としてfailedになった。説明は作成されていない。[保存状態](../output/dce-matrix-six-run/39d78ec6-3a26-49fe-88e3-f0f37f4fd6a2-final-quota-observation.json)。生成leaseの期限切れだけではsemantic結果保存を妨げないことをソースで独立確認した。数学的な誤りと断定せず、成功にも数えない。

新rank `4e96b538-122b-4b29-befe-2eba61c5ace2` はverified＋説明completed。標準基底の一次独立性と張る空間の次元からrank=2へ進む。候補・source・出力・QAのhashと独立sessionを再計算して一致した。結論にLean型表記が残る表示上の改善余地はある。[実出力とレビュー](../output/dce-matrix-phase2/rank-terminal-review.json)。旧failedや説明却下のjobは保存した。

**検索はまだ合格していない。** profile grammarの不足、provider usage metadataの厳しすぎる解析、XML構文崩れを修正したが、実入力では式の構造と型の取り違えが残った。汎用XML treeの初回実診断はtransposeの引数内へ等式右辺を入れ、演算子別AST v2は行列の値をMatrix型へ置換した。両方とも全validatorが拒否し、成功として扱っていない。旧観測は保持し、新しい実装の評価へ付け替えない。

手動診断の初期clientは6,000 output tokens、実workerは12,000だった。現在のhelperは実worker設定・schema・codec・provider adapter等のhashに束縛し、90秒／最大2回の構造化制限を共有する。未公開generationの明示profile診断であり、通常profile routerを通した公開検索の成功証拠ではない。型専用の58記号を通常式から分離したAST v3は、全16profileの往復一致・迂回拒否など関連268testsと独立116testsに合格した。初回の実1件は約1.8秒でtyped_structuring_unavailableになり、その記録だけでは原因を特定できない。安全なHTTP分類を追加した16:12:18 UTCの再診断では **HTTP429 / insufficient_quota** を確認し、以降の外部モデル検証を止めた。[診断結果](../output/dce-matrix-phase2/transpose-sort-expression-ast-v3-transport-diagnostic-observations.json)。以前の失敗や別のinverseレビューに同じ原因を推定で付けない。providerがv3 schemaを受理したかは未確認。最終のQA運用障害修正とともにv3を含む最新コードをローカルworkerへ反映したが、行列catalogはinactiveのまま、実検索合格・公開とは扱わない。行列6行はinactive、active0。追加6誤答は2026-09-30に明示許可済み。01:08:42 UTCに最初の誤答1件を再実行したが、HTTP429 insufficient_quotaで構造化前に停止した。残り5誤答と今回の正答6件は送っておらず、12query gateと公開は未完。[再開結果](../output/dce-matrix-approved-resume-20260930/review.md)。

## 独立レビューの運用障害と数学的却下

最後の確認で、providerや応答解析の障害を架空の `rejected` QA receiptとして保存する追加不具合を検出した。新inverseの保存文はこのfallbackに一致するが、元の例外は記録されておらず、その原因は断定できない。既存履歴は変更しない。

CORE-002/004 の working deltaに基づき、明示された有効なモデル判定だけを承認・却下として保存し、運用障害は別の有限停止として記録する修正を実装・反映済み。候補・生成セッション・source/target/artifactの照合と専用reviewer認証を維持し、未検証内容の公開、自動再生成、利用枠の追加消費は行わない。サービス障害とschema不正を型で分離し、永続記録は運用障害の区分のみとする。生の例外や細分類は保存しない。[対象契約](../output/semantic-review-unavailable-20260930/working-contract.md)／[API・worker検証](../output/semantic-review-unavailable-20260930/backend-validation.md)。

実PG＋実Lean/mTLSを使う7ケースで、QA receiptを作らない停止、候補取り違え拒否、再送不変、未検証sourceの公開拒否を確認。外部モデル障害自体は試験条件として送ったものであり、更新後OpenAIの実応答試験ではない。HTTP応答喪失後のモデル再呼出し防止とDB障害時の503を回帰検証した。画面では保存言語4種で区別し、failed履歴の詳細がない場合だけ本人限定GETを一度行う。terminalのSSE/pollは再開しない。

既存サービスの書き込みを停止して正規local adapterを適用し、前後で証明・候補・QA・チャット・説明・利用枠・送信キー記録の件数と内容digest、および対象ACLが不変だった。[DB反映結果](../output/semantic-review-unavailable-20260930/local-release-result.json)。API/reconciler/worker/reviewer/webfrontを既存サービスへ反映し、9container/6network/10volumeは増加なし、全healthy、稼働source hash一致、worker DB隔離も再確認。[最終反映確認](../output/semantic-review-unavailable-20260930/final-deployment-check.json)。

## 承認済み保持方針

BILL-003は、作成から**13暦月後に詳細idempotency recordを削除**し、正確なowner subjectとkeyの各SHA-256 digestのみをimmutable tombstoneとして永久保持する。job・要求fingerprint・応答・生owner・timestampは残さない。同account/keyの再利用を永久拒否し、別accountの同keyは許可する。maintenanceとadmissionは同account lockを使い、tombstone挿入とdetail削除を原子的に実施する。ローカルv3 migration適用済み。実テーブルも2列のみ。未解決Stripe operationの保持方針は変更していない。

## 検証の範囲と残件

- 最新のQA運用障害修正後、agent unit全体 **1,626件PASS**、API unit全体 **913件PASS**。最後のAPI例外変換修正は別途7件で確認。frontend全体 **88 files / 912 tests PASS**、最終scope guard追加後の関連6件・型検査・lintも合格。[agent全体ログ](../output/semantic-review-unavailable-20260930/agent-unit-final.log)／[API全体ログ](../output/semantic-review-unavailable-20260930/api-unit-final.log)。APIの変更対象静的検査には、既存billing作成コードのE501が2行残る。新migrationは実PGを含む35件、旧履歴診断14件・実PG1件、候補binding実PG1件などの個別証拠と重複を足し合わせない。
- COREの実PG109件、production registry全17 steps、billing並列予約／tombstone／owner分離、Recipeの実PG・mTLS・pinned Lean等の詳細は表の各証跡を参照。重複suiteを足して総件数にしない。fixtureは学習者データと分離した。
- 実モデルusageは新二項平方のgeneration4callを保存できた。5,592microUSDはその範囲の記録であり、全モデル利用やStripe請求の総額ではない。
- **未完了**：実検索の構造化品質と12query公開gate、Draft本文760 cells不足・advanced500の未具体化、generic PFI実DBの充実、可換環論の難問完走。利用枠は回復し、inverseの独立QA・説明完了の新試験は成功した（下記）。最新の難問実測は[別報告](commutative-algebra-runtime-tests-2026-09-30.md)に記録し、単純な行列の成功で代替しない。
- **設定後の実検証が必要**：Stripe Checkout／Portal／Webhook往復、Google実認証、AWS IAM／release／運用。設定未提供のためローカル実装やテスト代替を実接続成功と扱わない。
- 未コミットの作業ツリーへの実装・ローカル反映であり、mainへのcommit／pushや本番公開は行っていない。

## 利用枠回復後の再検証 — 2026-09-30

02:05 UTCの実呼出しでOpenAI接続の回復とv3 schemaの受理を確認した。
ただし行列を零行列へ変える構造化の誤り、および正しく構造化された誤答に
関連するだけのDraftを選ぶ別の誤りが見つかった。取得を証明成功としては扱わない。
元の観測を保存し、literal専用AST、数値保持検査、型付き検索専用の証明支援方針選択を
修正して再検証中。過去の「quotaで停止」はその時点の記録で、現在のブロックではない。

交換行列は新job `7316fb0b-4d3c-4685-ac7b-f54907fb74c9` でverified＋説明completed。
自動修復3回を経て02:14:25 UTCに検証完了、02:14:31 UTCに説明完了した。
任意の体・両側自己逆という元の命題、成分計算、独立QA sessionと全結合hashを確認。
導出の反復や循環は見られなかった。旧failed履歴や旧corpusの参照は書き換えていない。
[独立確認結果](../output/dce-matrix-quota-restored-20260930/inverse-independent-review.json)。
ブラウザ描画の追加確認や検索公開gateの合格を意味しない。

最終の行列再試験は期待方針取得6/6・誤答除外6/6。ただし構造化の完全一致は11/12で、
逆行列の述語を同じ述語同士の等式へ置き換える誤りが残ったため、検索公開gateは未合格。
その別ジョブの正しいLean証明で検索結果を合格扱いにはしない。
最終agent unit1,805件・対象lint/型検査に合格し、既存worker/reviewerへ反映。
9サービスhealthy、6network/10volume不変、workerのDB隔離も維持した。
ユーザー指示により、次の実試験を根基・局所化・中山の補題の3題へ拡張した。

可換環論の初回3題はいずれも13候補・12回修復で失敗し、意味QA・説明生成に到達しなかった。簡単な問題の成功で難問対応まで合格とは扱わない。[問題・実測結果](commutative-algebra-runtime-tests-2026-09-30.md)と再利用可能な `tests/e2e/fixtures/commutative-algebra-v1.json` を追加した。

この実測で、実compiler診断名の取りこぼし、構文エラー位置を見ず命題を保持する修復指示、API再開ごとに消えていた連続失敗の履歴を修正。最後の修正後、agent全1,845件・API全934件と追加HTTP回帰・実PG3件・実PG→API→worker結合が通過した。3サービスへ反映し、全9サービスhealthy・6network/10volume不変、worker DB隔離も維持。これらは難問の数学的成功を意味しない。根基の元問題だけを新jobで再試験し、旧失敗履歴は保持する。

根基の再試験も04:01:37 UTCに13候補・12修復で `repair_budget_exhausted`。実モデル入力への停滞警告到達は確認できたが、未知のmathlib宣言・型不一致が残り、意味QA・説明生成は0件だった。難問3題と根基の再試験は未合格であり、成功動画もない。[最終結果](commutative-algebra-runtime-tests-2026-09-30.md#修正後の根基問題の最終結果)。
