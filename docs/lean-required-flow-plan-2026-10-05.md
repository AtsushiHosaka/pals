# Lean検証をすべての回答の核に戻す

## 背景

2026-10-04 の同期コミット（webfront `0750588`）以降、送信は「AI回答」の経路（`/v1/chats/{id}/proof-requests`）しか使っていない。agent の `pals_agent/proof_reuse.py` は Lean を一切実行しない（`evidence_kind: llm_assessed`）。

本来の Lean パイプラインは API・agent・画面に残っているが、送信からは呼ばれていない。中身は Draft 検索 → Recipe 再利用 → DSP（draft/sketch/prove）→ コンパイル → 修復 → 独立レビュー → 自然言語の説明 → 追加質問。

仕様も同じようにずれた。CORE-012 は「回答の採用条件にしない・選ばせない」としか書いていないのに、PFR-002 と proof-request-reuse の設計に「Lean を呼ばない」と書かれていた。

ユーザー（2026-10-05）：Lean 検証はプロダクトの核で、絶対に残す。本来の流れは次の4段階。
1. Draft DB で似た証明を探し、候補を LLM で判定する。
2. 全く同じなら、見つかった Lean と回答を返す（**コンパイルしない**）。
3. 同じでなければ DSP で Lean を作ってコンパイルし、通ったら LLM で自然言語にして提示する。
4. 追加質問がなければ Draft DB に追加する。

この会話で決まったこと：
- 修復しても Lean が通らない → **回答は出さない**。「Leanで検証できませんでした」と再試行を表示する。
- Draft DB への追加 → **候補として登録**（会話文は含めない）し、**運用者が承認**してから追加する。
- 完全一致 → コンパイルなしで再利用。一般定理の**特殊化** → 代入版だけをコンパイルする。
- **ゲストチャット（/try）も最初から Lean 必須**。

## 目標の流れ（前提確認・課金・ゲスト・履歴は維持）

送信先は今と同じ proof request とし、これが自分で回答を作る代わりに Lean を指揮する。

1. **前提確認**：今の `needs_input` 質問をそのまま使う（PFR-004）。
2. **Draft 検索と LLM 判定**：既存の Draft 検索（上位8件）と `proof_reuse.py` の判定（`direct` / `instantiate` / `derive` / `none`）を使う。
3. **カタログ再利用**：`direct` で、その Draft に登録済みの Recipe が紐付き、toolchain が現行と一致する場合。
   - 状態は `answered`、証拠区分は `lean_catalog`（Recipe ID・source の SHA-256・登録時のコンパイル記録）。
   - 回答文はその Lean source に基づく自然言語の証明で、既存の独立 QA（CORE-006）を通す。
   - 要求と Recipe の命題の対応も、別セッションの LLM が独立レビューする（CORE-002）。コンパイルはしない。
4. **代入版の検証**：`instantiate` で Recipe が紐付く場合、Lean ジョブを起こす。一般定理に代入を適用するラッパー定理を作ってコンパイルし、失敗したら同じジョブで DSP に移る。
5. **新規証明**：それ以外（`derive` / `none` / `uncertain` / Recipe のない `direct`）は、既存の DSP パイプラインをそのまま使う Lean ジョブを起こす。
6. **成功**：ジョブが `verified` になり説明がレビューを通ったら、要求は `answered`（証拠区分 `lean_verified`、ジョブへのリンク付き）。追加質問は既存の説明への質問機能を使う。
7. **失敗**：ジョブが失敗したら要求は `failed`（`lean_verification_failed`）とし、回答は出さない。再試行は既存の上限内で新しいジョブを起こす。
8. **AI だけの最終回答（`llm_assessed`）は作らない**。保存済みの過去の回答はそのまま読める。

## フェーズ（各フェーズでテスト→コミット→push。本番は Phase 7 まで変えない）

### Phase 0 — 仕様（sdd-update-spec）
- `pals-product-core`：
  - CORE-002：登録時に同じ toolchain でコンパイル済みの Recipe と完全一致し、独立レビューに通った場合も `verified` とする。
  - CORE-012/013：全回答を Lean 検証済みにする。Lean モードやボタンは出さない。AI だけの回答は出さない。
- `proof-request-reuse`：PFR-002 の「Lean を呼ばない」を上の流れに置き換え、再利用・代入版コンパイル・Lean ジョブ・失敗時の扱いに新しい ID を振る。
- `public-guest-chat`（GUEST-002）：Lean 必須にする。
- `individual-billing`：要求の利用枠で、紐付く Lean ジョブまで賄う。Lean 経路の利用トークン計測（BILL-013）を追加する。
- `lean-recipe-catalog`：toolchain が一致する場合の再コンパイルなし再利用を追加する。
- 新規 `draft-addition-candidates`：候補の登録、24時間追加質問がなければ承認対象、運用者の承認。

### Phase 1 — ローカルの Lean 実行環境
- 期限24時間のローカル証明書が切れて reconciler が起動に失敗している（`ReconcilerTlsMaterialError`）。verifier は一度も起動していない。
- `pals-scripts/bootstrap-local-verifier-tls.py` で証明書を作り直し（`tests/e2e/run-local.sh` と同じ手順）、verifier と reconciler を起動する。
- コードを変える前に、既存の Lean ジョブが1件、`verified` と説明まで到達することを確認する。

### Phase 2 — API（`pals-api`）
- **migration** `app/db/migrations/proof_requests/002_lean_flow.sql`：
  - 状態 `verifying`、`formal_job_id`、証拠区分 `lean_catalog` / `lean_verified`、新しいエラーコードを追加する。
  - manifest と各リリース登録（`proof_requests_migration.py` / `production_database_release.py` / `mac_production_database_migrations.py`）に入れ、fingerprint テストを更新する。
- **確定処理**（`proof_requests.py`、`proof_request_contract.py`）：
  - 新しい結果 `catalog_reuse` と `formal(plan)` を追加する。
  - `formal` は同じトランザクションで Lean ジョブを作る。`_create_with_outbox` の挿入処理を流用し、**利用枠の二重予約はしない**（要求の仮押さえやトークン操作で賄う）。
  - ジョブには `proof_request_id`、確定した前提、代入計画を持たせる。
- **ジョブから要求への反映**：
  - ジョブの終了と説明レビュー完了（`proof_jobs.py`、説明サービス）で、要求を `answered` / `failed` にする。
  - 既存の確定・解放処理（`billing_admission.py`、`token_accounting.py`）で、利用枠をちょうど1回だけ消費または解放する。
- **カタログ再利用の権限**：
  - Draft に紐付く登録済み Recipe を返す worker 用エンドポイントを作る。`proof_request_sources.py` の照会と、`lean_recipe_selection` の現行 toolchain fingerprint を流用する。
  - 確定時に source の SHA・登録時のコンパイル記録・fingerprint を再照合する。
- **ゲスト**（`guest_chat.py`）：同じ結果を扱う。ゲストの読取りに Lean の進捗・検証済み Lean・レビュー済み説明を含める。ゲストは説明への追加質問ができない。新しい質問は1日3回の枠に数える。

### Phase 3 — agent（`pals-agent`）
- `proof_reuse.py`：AI だけの最終回答をやめ、判定を `catalog_reuse` / `formal(instantiate|dsp)` に対応させる。再利用時の自然言語の回答は Recipe の source から作り、既存の QA を通す。
- `proof_request_worker.py`：新しい結果を確定させる。
- `worker.py`：要求に紐付くジョブでは、`pipeline.run_statement` の前に代入版の検証を行う（`_submit_selected_recipe_candidate` と recipe planner を流用）。確定した前提を文脈として渡す。
- トークン制プラン：紐付くジョブの各 LLM 呼び出しに、要求のトークン操作から許可を取り記録する（`token_meter.py` を流用）。有料ユーザーを止めない。

### Phase 4 — 画面（`pals-webfront`）
- `lib/api/proofRequests.ts`：`verifying`、`lean_catalog`、`lean_verified` と失敗コードを読む。
- `ProofRequestThread.tsx`：
  - 要求ごとに Lean の進捗を出す。
  - 検証済みとカタログ再利用は「Lean検証済み」、Lean source、説明スレッドを出す。
  - 失敗は回答本文を出さず、「Leanで検証できませんでした」と再試行を出す。
- `ProjectDetailScreen.tsx` / `LegacyChatArchive.tsx`：紐付くジョブを、既存の `useProofJobEvents` / `useProofExplanation` / `useProofClarifications` と `ProofExplanationThread` で表示する。
- `GuestChat.tsx`、`lib/api/guestChat.ts`：ゲストにも Lean の進捗・Lean source・説明を出す。
- 4言語の文言（`uiMessages`、`learnerCopy`、`guestMessages`、`publicMessages`）：LP と FAQ を「回答は Lean で検証済み」と正しい内容に戻す。
- 別セッションの「選択して質問」（`SelectableProofAnswer`）を壊さないよう、push 前に rebase する。

### Phase 5 — Draft 追加候補
- API 側に新しいテーブルとリリース migration を追加する。DSP で検証された証明1件ごとに候補を1件作る（カタログ再利用は対象外）。
- 候補に入れるのは、形式命題・Lean source とコンパイル記録のハッシュ・レビュー済みの説明だけ。**会話文とアカウントIDは含めない**（RCP-003 と同じ最小化）。
- 24時間追加質問がなければ承認対象にする。
- 運用者用 CLI（`python -m app.release.draft_candidates list|approve|reject`、`recipe_curation_proposals` を手本にする）を作る。承認すると、既存の Draft 登録と `lean-recipe-catalog-admit` / `lean-recipe-alignment-admit` で DB に入れる。

### Phase 6 — ローカルでの通し確認
実際のローカル環境と実 provider で、Project 配下・Project なし・ゲストのそれぞれについて確認する。
- (a) カタログ再利用（`continuous_square`）
- (b) n=2 の特殊化の代入版コンパイル
- (c) DSP による新しい定理
- (d) 失敗時に回答が出ないこと
- (e) 追加質問
- (f) 候補の承認で Draft が増えること
- 利用枠（回数制・トークン制・ゲスト）の消費

あわせてスマホ・タブレット・PC で画面を撮影して確認する。

### Phase 7 — 本番反映（別途承認）
Mac mini の verifier と reconciler（相互TLS、runbook どおり）、署名付き migration のリリース、デプロイ、本番での実確認。

## 検証
- **API**：単体テストと実 PostgreSQL の結合テスト。
  - migration の新規適用と既存からのアップグレード
  - 確定処理の各結果
  - 二重予約がないこと
  - 利用枠の消費・解放がちょうど1回であること
  - ゲストの分離
  - カタログ記録の改ざんを拒否すること
- **agent**：判定の対応付け、代入ラッパー、AI だけの回答が出ないこと、トークン許可の単体テスト。
- **画面**：新しい各状態の4言語の単体・ストーリーテスト。型チェック、lint、ビルド。
- **通し確認**：Phase 6 の実環境での確認。証跡は `docs/` に記録する。

## リスクと注意
- **規模**：数セッションかかる。各フェーズは単独で取り込めるようにし、送信を新しい流れに切り替えるのは Phase 2〜4 がそろった時点とする。
- **待ち時間**：DSP とコンパイルは数分かかる。画面には実際のジョブ段階を表示する（既存の SSE）。
- **ゲストの費用と verifier 負荷**：ゲスト全体の1日上限は維持する。verifier の同時実行枠は全員で共有する。
- **他セッションとの調整**：別セッションが外部 Lean 連携（`specs/external-lean-integration`、CIMD・external tools）を作業中なので、そのファイルは触らない。
