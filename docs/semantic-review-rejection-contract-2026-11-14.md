# 意味の審査の不合格: 理由コードの分離と再試行の契約案（2026-11-14）

状態: 提案。コードは未実装。pals-api（非公開）とフロントの変更を含み、本番の API/Web ソース分岐は PR のみ・必須 CI・管理者にも適用のため、別の作業として切る。

## 事実（読み取りと測定）

- 意味の審査が却下すると、API が `proof_jobs.state='failed'` で終端させる（`postgres.py` の semantic review 決済、`semantic_review_failed_status_context`）。作り直しも修復もない。診断コードは `pals.proof_semantic_review_failed`、`status_context.termination_reason='semantic_review_failed'`。
- 依頼側は `proof_request_lean.py` の `apply()` が、job が `verified` 以外なら一律 `lean_verification_failed` と記録する。実際の理由（意味の審査）と食い違う。
- フロントは `components/ProofRequestThread.tsx` で `error_code === "lean_verification_failed"` を `leanFailed` の文言に対応づける。未知のコードは汎用文言になる。
- 測定（`pals-agent/testdata/answer-accuracy-regression-v1/`、README の E 節、Luna）: 依頼が「明示的な N を与えよ」「連続の ε-δ 定義を使え」で、Lean の命題・証明がそれを表さないとき、意味の審査は 0/16・0/3 承認（毎回、要件の欠落を理由に却下）。要件を命題に含めた Lean は 5/6・3/3 承認。題と合わない Lean は 24/24 却下。要件のない依頼は 8/8 承認。→ 却下は多くが正しい。回答が返らない原因は「却下後の作り直しがない」こと。

## (a) 理由コードの分離

- API: `apply()` で `state='failed'` のとき、job の `status_context.termination_reason` が `semantic_review_failed` なら `lean_semantic_review_failed`（`semantic_review_unavailable` なら `lean_semantic_review_unavailable`）を依頼の `error_code` に記録する。他は従来どおり `lean_verification_failed`。
- フロント: 新しい 2 コードを `leanFailed` と同じ文言に対応づける（表示は変えない）。`chat_shares._request_messages` など、`error_code` を見る API 側の他の箇所と、`tests/unit/test_proof_request_unverified_deadline.py` の対応表も同じに揃える。
- **出す順序**: 先にフロント（新コードを受理）、後で API。API が先だと新コードが汎用文言になる。
- 互換: 既存の履歴は変えない。コードの値は追記のみ。

## (b) 却下後の命題の作り直し（1 回、既定 off のフラグ）

- 必要な API の契約: 意味の審査の却下決済で、フラグが on かつ再試行の予算が残るとき、job を終端させず、却下理由を添えた「再形式化の種」を持つ状態へ戻す（コンパイル失敗の修復 `api_repair_seed` と同じ形）。worker はその種で命題の形式化と証明をやり直し、新しい候補を提出する。予算は 1 回、期限は既存の壁時計に従う。
- worker 側: 審査役の根拠（rationale）を形式化の入力に足す。審査プロンプトは変えない。
- 安全: 作り直した候補も同じ意味の審査と Lean 検証を通る。却下を覆す経路はない。
- 計測する量（実装後）: 回答が返る割合、誤った回答を通していないこと（題と合わない負例の通過 0）、追加の費用・時間。
- 未決: API の状態遷移の追加（候補の世代、イベント、冪等性）、フラグの置き場、既存の `no_progress` 終端との関係。

## 次にやること

1. (a) を別作業にする（フロント → API の順の 2 PR）。
2. (b) は API の設計レビューを先に行う。この文書を入力にする。
