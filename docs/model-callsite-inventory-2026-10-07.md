# モデル選択は回答・Lean生成に適用し、検索・判定・QAは固定する

2026-10-07 JST。ユーザーの指示に基づき、モデル選択を実装する前に利用箇所を調査した。選択肢はGPT-6 Luna、GPT-6.1 Sol、GPT-5.6 Terra。選ぶのは回答やLeanコードを作るモデルで、DBから取得したDraftの適合判定などは固定する。料金と換算式は[原価換算の仕様メモ](gpt-model-selection-and-usage-2026-10-07.md)を参照。

## 調査対象は親リポジトリの参照commit

親`7c45dbb`が参照するagent `7a6c343`、API `aa8b12c`、webfront `d436271`、infra `8aa5700`、observability `fa121a8`、datasets `dcc8185`のソースを調べた。以下の`agent/`、`api/`、`web/`は各submodule内のパスを示す。行番号はこのcommitのソースに対応する。

既存チェックアウトには別revisionと他作業の変更があったため、参照commitのソースだけを取得して照合した。別チェックアウトのsupplemental usageやexternal toolsの追加を、今回の基準に混ぜていない。API・webのprovider SDK呼出し、agentの推論・embedding・reranker呼出し、親の運用スクリプト、infra・observabilityのソースを検索し、factoryから実際の呼出しまで追った。依存ライブラリ内部、稼働環境の設定、モデルの実応答は調査対象外。モデル呼出し、テスト、アプリ・コンテナ起動は行っていない。

## 切替対象は証明内容と回答を作る工程

通常のrelease roleは現在すべて`gpt-6-luna`。assessmentの限定的な昇格だけが`gpt-5.6-terra`になっている（`agent/pals_agent/model_roles.py:33`）。次の生成工程に、受付時に保存した選択モデルを渡す。

| 用途 | 根拠 | 現在の接続 |
|---|---|---|
| DSPの新規Draftを作る | `agent/pals_agent/generator.py:256` | factoryのDRAFT設定。DBから取ったDraftの適合判定とは別 |
| Lean Sketchを作る | `agent/pals_agent/generator.py:303` | 同じgenerator設定 |
| 完成したLean証明を作る | `agent/pals_agent/generator.py:361` | prove専用overrideはrelease factoryでは未指定 |
| コンパイル失敗後にDraft/Sketch/Leanを再生成する | `agent/pals_agent/pipeline.py:825` | 通常生成と同じ段階別処理を再実行 |
| Recipe再利用時に公開する自然言語回答を作る | `agent/pals_agent/proof_reuse.py:517`、`:685` | 現在はDraftを根拠に適合判定と同じ呼出し内で作る。生成を分離し、採用RecipeのLeanソースを渡す |
| Leanで検証済みの証明を説明する | `agent/pals_agent/explanations.py:441`、`:582` | EXPLAIN設定 |
| 証明への追加質問に答える | `agent/pals_agent/explanations.py:492`、`worker.py:1285` | 同じexplainer。CLARIFY設定を独立には使っていない |

## 固定するのは根拠の選択と正しさの判定

選択モデルを判定用の設定へ一括で流さない。現行の役割ごとの固定方針を維持し、独立QAも別セッションのままにする。固定側の使用量も、各モデルの実績原価で合算する。

| 用途 | 根拠 | 現在のモデル・処理 |
|---|---|---|
| 前提不足・反例の疑い・流儀・資料の命題を確認する | `agent/pals_agent/proof_reuse.py:265` | Luna。流儀カタログの保存や選択肢組立て自体は決定的処理 |
| Draft適合、source、代入、証明方法を判定する | `agent/pals_agent/proof_reuse.py:419`、`:517` | Luna。回答生成も含むため分離が必要 |
| 数学的不確実性を追加判定する | `agent/pals_agent/proof_reuse.py:524` | Terra。選択された生成モデルの代替には使わない |
| 検索用のOpenMath queryを作る | `agent/pals_agent/proof_reuse_catalog.py:118` | Luna、OPENMATH設定 |
| formal検索のprofileを選ぶ | `agent/pals_agent/profile_routing.py:73` | Luna |
| generic OpenMathへ構造化する | `agent/pals_agent/openmath.py:345`、`factory.py:208` | Luna、OPENMATH設定 |
| typed OpenMathへ構造化・schema修復する | `agent/pals_agent/typed_runtime.py:132` | Luna |
| natural検索のembedding | `agent/pals_agent/proof_reuse_catalog.py:199` | `text-embedding-3-small`、384次元 |
| generic/typed検索のembedding | `agent/pals_agent/factory.py:227`、`:284` | 設定で固定。typedはsmall・384次元。genericはcatalog fingerprintに従う |
| generic/typed Draftをrerankする | `agent/pals_agent/proof_flow_reranker.py:21`、`:93`、`typed_reranker.py:52` | Luna。ただし現在DRAFT設定を参照しており、生成との分離が必要 |
| 修復するDSP段階を選ぶ | `agent/pals_agent/generator.py:132`、`pipeline.py:737` | generatorのモデルと共有。判定用を分ける |
| natural/Recipe再利用の回答を独立QAする | `agent/pals_agent/proof_reuse.py:594` | Luna。QAの役割ラベルを変えても実モデルはreuse judge設定から選ぶ（`:742`） |
| Leanの命題と依頼の対応をsemantic QAする | `agent/pals_agent/explanations.py:383`、`factory.py:150` | Luna、PROOF_REVIEW設定 |
| 専用プロセスでRecipe/model candidateをsemantic QAする | `agent/pals_agent/recipe_semantic_reviewer.py:324` | Luna、PROOF_REVIEW設定 |
| 説明・追加回答を独立QAする | `agent/pals_agent/explanations.py:287`、`factory.py:139` | Luna。ただしEXPLAIN設定と共有しており、生成との分離が必要 |

DBの候補取得、Recipe選択・materialize、Leanのコンパイル自体には選択するLLMがない。根拠は`agent/pals_agent/proof_reuse_catalog.py:204`、`recipe_attempt.py:146`、`worker.py:1139`。Lean compilerは全選択肢に共通の検証器として使う。

## 役割名だけを書き換えると判定まで変わる

実際の接続は役割名と一対一ではない。factoryは`HybridLeanGenerator`にDRAFT設定を一つだけ渡し、Draft・Sketch・Prove・修復先判定がそれを共有する（`agent/pals_agent/factory.py:118`）。説明と追加回答も同じexplainerを使い、説明の独立QAまでEXPLAIN設定を参照する。rerankerもDRAFT設定を参照する。

naturalのprimary assessmentはDraft適合判定と回答文の生成を一度に行う。Lean flowでは、その後にdirect Recipe再利用かDSP/代入によるLean生成へ分かれる（`agent/pals_agent/proof_reuse.py:537`、`:1032`、`:1073`）。Recipeは回答生成後に取得される（`:1047`）。再利用ではassessmentが作った回答をQAに渡し、QAがRecipeのLeanソースも読む（`:631`）。生成はまだそのソースを読んでいない。DSPへ進む場合、その回答は最終回答に使われない。固定assessmentで根拠と方法を決め、必要な回答・Lean生成だけを選択モデルで実行する形に分ける。再利用回答はPFR-010の既存要件に従い、採用したLeanソースから生成する。

別の修復指示LLMは`agent/pals_agent/generator.py:104`にあるが、通常pipelineは段階別interfaceを検出して直接再生成するため、通常の修復では呼ばない（`pipeline.py:647`）。この休眠経路も、再利用する際には内部判定とLean生成を区別する。

## 使用量には未計測と精算未接続がある

| 対象 | 確認した状態 | 必要な変更 |
|---|---|---|
| natural assessment・検索・QA | `agent/pals_agent/proof_request_worker.py:152`のusage scope、token operationがあれば`:159`のmeterで記録 | 固定処理と選択生成を分けても同じoperationに含める |
| formal生成・OpenMath/profile | `agent/pals_agent/worker.py:829`、`:858`で原価観測。ただしtoken permitはない | linked requestのoperationへ接続し、段階別に記録 |
| generic/typed embedding | `agent/pals_agent/draft_embeddings.py:94`でusageを送らない | 実usageの記録とpermit/receiptを追加 |
| generic/typed reranker | `agent/pals_agent/proof_flow_reranker.py:245`でusageを読むが`:88`でIDだけを返す | 実usageを捨てずに記録・精算へ渡す |
| Lean semantic QA・説明・追加回答・それぞれのQA | `agent/pals_agent/worker.py:609`、`:1425`、`:1434`、`:1285`、`:1288`にusage scopeがない | provider応答がusageを持っていても、`usage.py:41`で記録されない。全工程を接続 |
| 専用Recipe QA | `agent/pals_agent/recipe_semantic_reviewer.py:142`にusage scopeがない | 運用審査の原価として計測。learner operationと無断で混合しない |
| linked Lean精算 | `api/app/infrastructure/repositories/token_accounting.py:422`の`settle_lean`は存在 | 既存receipt合計の精算だけ。必要な工程が揃ったことの検査を追加 |

linked-job成功時の精算処理が存在しても、全工程が計測済みとは限らない。現行permitはrequestが`assessing`で、有効なrequest claimを持つ場合に限る（`api/app/infrastructure/repositories/token_accounting.py:263`）。Lean jobを動かす`verifying`状態の呼出しはこの契約では接続できない。さらに`settle_lean`は空のcall集合でも0を精算できる。BILL-015/016では、linked jobの権限と各工程の完全なreceiptを追加し、欠測を消費ゼロの成功にしない。

Luna/Terraの価格記録はキャッシュ書込み単価を全入力へ適用する上限見積りで、Solの価格記録は未登録（`api/app/domain/billing_prices.py:17`、`agent/pals_agent/usage.py:18`）。キャッシュ割引と書込み内訳に対応する新ポリシーが必要。Solを指定するだけでは、現在のstrict meterが未知価格として拒否する。OpenAI clientの処理方式・推論設定もLuna/Terraだけに明示されている（`agent/pals_agent/openai.py:64`）。

## 運用・評価のモデルはチャットの選択から分離する

| 用途 | 根拠 | 扱い |
|---|---|---|
| optional artifact評価 | `agent/pals_agent/factory.py:159`、`semantic_evaluation.py:264` | configured OpenAI/Ollama。運用設定を固定 |
| typed catalog評価 | `agent/pals_agent/typed_evaluation.py:134` | structuring・embedding・rerankerを評価用に組み立てる。選択対象外 |
| 旧ローカル生成backend | `agent/pals_agent/ollama.py:35`、`mlx.py:18` | release factoryはOpenAIを使用。旧CLI/library経路は今回のGPT選択に含めない |
| Draft/typed ingestのembedding | `pals-scripts/prepare-local-draft-batch.py:140`、`prepare-local-typed-catalog-batch.py:65` | catalogと同じ固定embedding。運用原価 |
| premise-check評価 | `pals-scripts/premise-check-eval.py:79`、`:102` | 実ProofReuseRuntimeの判定を評価。固定assessment |
| 開発用model切替script | `pals-scripts/env/use-openai-nano.sh:25`、`use-oprover.sh:29` | global envの変更。依頼別selectorの実装には使わない |
| production embedding設定 | `infra/terraform/production/variables.tf:286`、`scripts/production-publish-images.sh:139` | 固定small、generic既定は1536次元。natural/typedの384次元契約と混同しない |
| observability | `observability/src/pals_observability/schema.py:239`、`plan.py:130` | model情報を受け取る記録・集計。推論呼出しは確認されない |
| datasets | pinned `dcc8185`は`.gitignore`のみ | モデル実装なし |

APIには直接の推論・embedding呼出しを確認していない。固定embeddingで作ったvectorを受け取りDB検索する。webにもprovider呼出しはなく、送信・表示が役割。現行create payloadには選択モデルがない（`api/app/domain/models/proof_request_contract.py:50`、`web/lib/api/proofRequests.ts:130`）。linked Lean contextにも選択モデルがない（`api/app/infrastructure/repositories/proof_request_lean.py:64`）。

## 実装は依頼の選択を生成工程だけへ運ぶ

projectとprojectlessの送信は`web/components/ProjectDetailScreen.tsx:540`と`LegacyChatArchive.tsx:285`から同じproof-request transportへ入る。guestは`web/lib/api/guestChat.ts:59`の別transport。選択モデルを`generation_model`としてrequest、quote、再送のfingerprint、claim、linked Lean contextへ保存し、固定役割は別のserver policyから解決する。継続・再試行・再送は受付時の選択を維持する。背景処理にはチャット選択を渡さない。

pipelineはworker内で再利用され、explainerとQA clientも起動時に作る（`agent/pals_agent/worker.py:1088`、`cli.py:384`）。共有instanceのmodelを変更せず、requestごとの不変な生成設定を使う。環境変数での一括model overrideは現行settingsが拒否するため、この方法でも実装しない（`agent/pals_agent/settings.py:17`、`:223`）。

ユーザーが連携を指示した別チャット「チャット機能を拡張」と`generation_model`の名称と接続方針を共有した。そちらの新しい意図判定は固定、通常説明の生成は選択モデル、独立QAは固定とする。今回のソース調査は新しい意図判定の実装済みを意味しない。

調査結果はPFR-001とBILL-016のrequirements・design・未完了tasksへ反映した。今回完了したのは利用箇所の調査と仕様整理。selector、各工程の実績計測、新原価精算の実装・実動作検証は未実施。

## 追加調査：後段の検証にはlinked LeanのDB権限整合も必要

2026-10-07 JST、連携先からagent `1006f2c`、webfront `e62dd15`のpushと、API統合中の報告を受けた。モデルの保存・受け渡し、通常説明の選択生成、固定のintent判定・QAは連携先が実装したと報告している。以下はその後の追加調査であり、冒頭の参照commitを対象とした調査とは区別する。

API `aa8b12c`のproduction registryは26段階で、`proof_request_lean`を含まない。連携先の作業中のregistryには`proof-request-lean`と`chat-experience`の2段階が追加されていた。これは作業中の変更を確認した結果であり、本番適用済みを意味しない。

同じAPIのcanonical migrationでは、`pals_api_runtime`に対する`proof_jobs`のSELECT/UPDATE権限は`generation_claim_id`と`generation_claim_expires_at`に限定される（`api/app/db/migrations/canonical/001_proof_job_runtime.sql:1522`）。一方、linked Leanの受付は`_insert_proof_job`で行を追加し、後続処理はstateやLeanコードなどを直接SELECTする（連携先の作業ツリーの`api/app/infrastructure/repositories/proof_request_lean.py:76`、`:159`、`postgres.py:6638`）。許可された列と必要な操作が一致していない。上記2段階の登録だけでは、この権限不整合の解消を確認できない。

後段の生成モデル選択、usage permit/receipt、精算の検証では、実際の制限されたAPI権限でlinked jobを作成・実行・完了できることも確認する。強いDB権限で成功したテストだけでは、この前提を満たしたと判断しない。連携先はチャット削除用の限定的なscrub関数を追加中で、既存Leanの権限境界全体の修正範囲はユーザーに確認中と報告している。このチャットでは権限変更やDB実動作検証を行っていない。実環境の接続ロールと追加の権限設定も未確認であり、上記はソース上の不整合を示す。
