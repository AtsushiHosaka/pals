# コードレビュー指摘への修正記録（2026-09-29）

**i18nの完了判断に誤りがあったため、[追加修正・検証記録](i18n-completion-2026-09-29.md)で訂正する。** 前回の証明画面は操作文言まで出力言語に従う箇所が残り、今回UI言語へ統一した。

対象は既存の `main` チェックアウト上の未コミット変更。既存のユーザー変更を保持し、コミット・本番デプロイは行っていない。本書は今回の修正を8領域に整理したもので、元レビューの指摘番号とは対応しない。

## 作業上の契約

- **UI言語と証明の出力言語を分離する。** UIは `en` / `ja` / `zh-Hans` / `zh-Hant` から選択し、端末の `pals.ui-language` に保存する。SSRの初期表示は一定に保ち、保存値またはブラウザー言語を起動後に適用する。既存チャットの保存済み出力言語、説明本文、LeanソースはUI言語の変更で書き換えない。
- **検索は所有者で限定したサーバー処理にする。** `GET /v1/chat-search?q=…&limit=…&cursor=…` を利用し、各チャットの証明履歴をブラウザーから個別取得しない。NFKC正規化、件数上限、作成日時とIDの降順によるページングを用いる。
- **QA拒否後は新しい候補を最大1回生成する。** 同じ候補への再投票で承認を取り直さない。修正候補も別セッションの独立QAに通す。元の処理期限を延長せず、拒否理由は非公開の運用記録として扱う。
- **利用者による説明の再生成は永続的な処理にする。** `POST /v1/proof-jobs/{id}/explanation/retry` は所有者・検証済み証明・失敗した説明の版を確認し、冪等キーと永続dispatchで重複を防ぐ。Lean証明そのものの生成は再開しない。完了済み説明をこの操作で上書きしない。

## 指摘・実装・回帰テストの対応

| 領域 | 問題と修正 | 主な実装・回帰テスト |
|---|---|---|
| 1. IMEとcomposerの重複 | 日本語変換の確定Enterで送信され得た。3画面の入力を共通化し、IME変換、Shift+Enter、キーのリピート、送信不可状態を共通処理した。 | `pals-webfront/components/ProofComposer.tsx`、`tests/unit/proof-composer.test.tsx`、`tests/stories/composer-safety.story.test.tsx` |
| 2. 入力と非同期処理の競合 | New chat失敗や遅れて完了する送信で、入力や表示中の証明が失われ得た。失敗時のdraft保持、送信開始後に編集したdraftの保護、画面破棄時のabortと遅延応答の無効化を追加した。 | `ProjectDashboard.tsx` / `ProjectDetailScreen.tsx` / `LegacyChatArchive.tsx`、`tests/stories/composer-safety.story.test.tsx`、`tests/stories/project-detail-create-race.story.test.tsx` |
| 3. UIのi18n | 固定英語・日本語と証明言語が混在していた。UI locale provider、4言語辞書、独立した言語選択、操作ラベル・エラー・日時の翻訳を追加した。説明本文とその `lang` は保存済み出力言語を維持する。 | `UiLocaleProvider.tsx` / `UiLanguageSelector.tsx` / `lib/uiMessages.ts`、`tests/unit/ui-locale-notifications.test.tsx`、`tests/unit/account-output-language-settings.test.tsx`、Activity/Timelineのunit tests |
| 4. エラーと通知 | 成否の通知が不統一で、内部エラー文字列や実装用メタデータが表示されていた。構造化されたエラー種別から安全な翻訳文を選び、InlineNoticeのlive regionとtoastを整備した。フォーム失敗はinline、成功・サイドバーでのチャット作成失敗・課金画面への遷移失敗はtoastとし、同じ失敗を二重に通知しない。Activityの内部UUID・S3 URI等と、何も表示できないコンパイラ欄も除去した。 | `primitives.tsx` / `ToastProvider.tsx` / `BillingCard.tsx` / `ActivitySidePanel.tsx`、`tests/unit/ui-locale-notifications.test.tsx`、`tests/unit/billing-notification.test.tsx` |
| 5. 検索の取得量と回復 | クライアント側のチャット別履歴取得を、所有者で限定した検索APIへ置換した。追加ページの失敗時も既読ページを残し、そのcursorで再試行する。アカウント切替はrender時に古い結果を隠し、abortした応答を反映しない。 | `pals-api/app/application/services/chats.py` / `PostgresChatRepository.search`、API `tests/test_chat_search.py` / `tests/integration/test_chat_search.py`、frontend `ChatSearchDialog.tsx` / `tests/unit/chat-search-dialog.test.tsx` |
| 6. Leanの修復材料 | コンパイラ失敗が汎用メッセージだけでは、重複宣言等の修復材料にならなかった。分類済みエラー、ソースに存在する識別子、行・列を上限付きで渡し、保存したattempt情報を修復へ引き継ぐ。生のstdout/stderrや任意のメッセージは渡さない。 | agent `lean_verifier/http_server.py` / `generator.py` / `worker.py`、API `tests/unit/test_compiler_feedback.py`、agent `tests/unit/test_isolated_verifier_http_server.py` / `test_repair_runtime_spec.py` |
| 7. QA拒否からの回復 | QA拒否、通信失敗、schema失敗を区別した。正当な拒否では新候補を最大1回作り、本文が同じ候補への再投票とreview session再利用を拒否する。拒否理由はterminal更新に非公開記録として引き継ぐ。 | `pals-agent/pals_agent/explanations.py` / `worker.py` / `api_client.py`、`tests/unit/test_explanations.py` / `test_worker_claim_spec.py`、APIのprivate failure schema/persistence tests |
| 8. 失敗済み説明の再生成 | 読み直しだけでは失敗済み説明を回復できなかった。所有者確認付きretry API、失敗版に結び付く冪等要求、永続dispatch・claim fencingを追加した。frontendは応答不明時も同じ冪等キーを使い、受理直後に残る古いfailed snapshotを新しい失敗と誤認しない。 | API `application/services/explanation_retry.py` / `db/migrations/explanation_retries/`、`tests/test_explanation_retry.py` / `tests/integration/test_explanation_retry.py`、frontend `hooks/useProofExplanation.ts` / `tests/unit/explanation-retry.test.tsx` |

表内の省略したcomponent・testパスは、記載した各実装リポジトリ内のもの。

## 独立レビューで追加した境界修正

- 検索cursor内の非文字列値がUUID処理で500になる問題を修正し、解析前の型検証を追加した。
- NFKCで展開される200文字の検索文から、API自身が受け付けない長さのcursorが生成される問題を修正した。検索文のSHA-256をcursorへ結び付け、サイズを一定にした。両件はAPI回帰テストに追加済み。
- explanation retryのreceiptと要求した失敗版の結び付き、同一jobで所有者sessionが変わる初回renderの表示隔離を追加した。
- 修正候補がAPIの参照整合性検査で拒否された場合にも、先行する非公開QA失敗履歴を引き継ぐよう修正した。

- 設定取得hookの依存を認証スコープの値に統一した。画面言語だけの変更では再取得や未保存設定の初期化を行わず、本当のアカウント変更時は中断・隔離する。19関連テストで確認。
- 実運用で完了済み証明の履歴がqueuedのまま残る問題も修正。選択中の最新snapshotを履歴に反映し、遅い一覧取得では終端状態を巻き戻さない。待機中の固定文言もqueued期間に限定した。
- AbortErrorの判定を共通化し、異なるrealmの例外でも取消を通信失敗として通知しない。サイドバーの実API失敗経路は重複しないtoastで知らせ、成功・アカウント変更・unmount時に消去する。

## 確認済みの証拠

- frontend全体：**80 files / 796 tests PASS**。`npm run lint`、`npm run typecheck`もPASS。最後の見出し・アイコン調整後にも関連22テスト、lint、production buildを再確認した。
- 説明retry・claim・migration関連：実PostgreSQL上の5ファイル **77/77 tests PASS**。失効したretry claimを古い元ジョブdeliveryが奪えない回帰ケースも確認。[検証記録](../output/backend-recovery-validation-20260929/explanation-retry-validation.md)。
- 起動手順：DB readiness後・API起動前にretry migrationを実行し、migration失敗時は起動を止める。実行可能なshellテスト2件PASS。
- 検索：既存PostgreSQLを用いる所有者境界・Unicode検索の統合テストPASS。[実行ログ](../output/review-fixes-20260929/real-search-postgres.log)。
- backend/agent：[検証記録](../output/backend-recovery-validation-20260929/validation.md)。worker/explanation/API claim 185件、deadline/shape/generator/repair 110件、verifier TLS契約11件、API compiler関連39件、API service/schema等58件のPASSが記録されている。これらは個別テスト群の件数であり、重複を除いた全体件数とはしていない。
- 同記録には、実PostgreSQLでの最終修復結果の保存確認2件、既存Lean/Mathlibによる `add_sq` 重複宣言の再現、実agent serializerと実API schema間の検証を含む。ローカル生成物は証拠参照用で、コミット対象ではない。

## 実画面・実モデルの確認

同じChromeタブと既存の `pals-local` Composeスタックを使用した。API・worker・verifierとfrontendを今回の変更で再buildし、必要なretry migrationを既存ローカルDBへ適用した。API・worker・reconcilerのhealthyを確認した。本番への反映は行っていない。

- 検索：30件から60件への追加表示、実際の「分配法則」検索による絞り込みを確認。
- 設定：4言語のUI切替、保存済みチャットの日本語保持、出力言語保存の成功toastを確認。さらに記法を未保存で編集し、出力言語も未保存で選択したままUI言語を変更して、両方の編集内容が消えないことを確認した。検証用の未保存変更は保存せず閉じた。
- Project：実UIで「証明とUIの動作確認」を作成し、サイドバーの作成ボタンから所属チャットを追加。最初の入力からチャットタイトルが生成された。
- 新規証明：以前に送信が許可された二項平方の問題を実UIで再送信。Shift+Enterでは改行、Enterで送信。job `581d1a53-11b7-4aaf-a668-b59a6c3f033b` はLean検証・意味確認を経てverified、説明はcompletedになった。
- 生成本文：任意の実数を取る→分配法則による展開→積の可換性で中項をまとめる→結論、の一度の導出となり、以前の証明全文の繰り返しはなかった。別セッションの独立QAの承認と、公開本文・Leanソースのhash一致も実DBの読み取りで確認。[証拠](../output/explanation-approved-rerun-20260929/581d1a53-11b7-4aaf-a668-b59a6c3f033b-review-fixes.json)。これはこの1例の結果であり、全ての生成文が常に無誤りであるという保証ではない。
- Lean：右側パネルで当該ジョブの検証済みソースを表示した。再読み込み後も説明と検証済みの履歴表示を確認し、古い「準備しています」の表示が残らないことを確認した。

## 説明の再生成と残る実モデル検証

失敗済み等比級数の説明は、実UIで再生成を受理し、workerで2候補を生成・独立QAして、両方の拒否後に失敗と再試行ボタンを表示した。拒否を成功表示に変える処理や、同じ候補にQAだけ繰り返して通す処理はない。非公開の拒否理由が保存され、公開APIには出ないことも確認した。

その後、境界条件を結論より前に扱う生成指示と、正当な帰納法を循環論法と混同しないQA指示を改善した。関連91テストは通過。等比級数の問題文・LeanコードをOpenAIに送る追加検証は、自動承認審査が「以前の明示許可は二項平方に限られる」として拒否したため、個別の送信確認が返るまで実行しない。この修正後に等比級数の実モデル再生成が成功したとは扱わない。

## 動画

[今回の実操作動画](../output/review-fixes-20260929/pals-review-fixes.mp4) は、同一Chromeタブの実画面を約3〜4fpsで取得して結合した操作抜粋。検索、保存通知、Project/chat作成、二項平方の送信と最終結果、Leanパネル、再読み込み、設定編集保持を含む。生成待ちとビルド待ちは省略し、各操作の末尾フレームを読み取りのため1.5秒保持した。合成した成功画面やfixtureの画面ではない。[フレーム構成](../output/review-fixes-20260929/video-manifest.json)。

本書とコードは未コミット。ローカル動画・ログ・生成結果はコミット対象に含めない。
