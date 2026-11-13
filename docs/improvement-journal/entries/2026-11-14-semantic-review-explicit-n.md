# Lean 検証後の意味の審査: 「明示的な N」の要求（2026-11-14）

- 指標: 意味の審査の却下率、却下の理由が要件の欠落かどうか。
- 仮説（主担当から）: 「明示的な N を与えよ」のような、Lean の命題に表しにくい要求があると、審査役が不合格にしやすい。
- 測定: 数列 1/(n+1)→0 の題で、要求の文面 2 通り × Lean 3 通り（tendsto、`∃ N` の ε-N、N を `⌈1/ε⌉₊` で命題に含める）。各 6〜8 回。ほかに正しい 10 題（各 8 回）と、題と合わない Lean の負例 3 種（各 8 回）。Luna、US$0.1 未満。
- 結果:
  - 明示的な N を求める文面: tendsto の Lean 0/8 承認、`∃ N` の Lean 0/8 承認。理由は毎回「命題が明示的な N（式や値）を与えない」。
  - 同じ文面で N を命題に含む Lean は 5/6 承認。N の指定がない文面では tendsto、ε-N とも 8/8 承認。
  - 正しい 10 題は 9 題が 8/8、x²（ε-δ）が 6/8。負例は 24/24 却下。
- 判断: 審査役の過剰な厳しさではなく、**命題の形式化が要件を落としている**ためと読める（この題では）。却下の理由を命題の作り直しへ渡す経路がないことが、回答を返せない直接の原因。
- 限界・未確認: この 1 題。一般化しない。pals#290 や #223 と同じ原因かは未確認（本番の記録を読んでいない）。却下は API 側（`semantic_review_failed_status_context`）で終端し、依頼には `lean_verification_failed` と記録される（`proof_request_lean.py`）。
- 次にやること: (a) 理由コードを分ける、(b) 却下後に命題の作り直しを 1 回（既定 off）。どちらも pals-api の状態遷移とフロントの表示に関わるため、別の作業として切る。
- 出典: [pals-agent#127](https://github.com/AtsushiHosaka/pals-agent/pull/127)（マージコミット 6323633d90e8fa1e93b964b524b92180c6445a24）、意味の審査の追加分は [pals-agent#130](https://github.com/AtsushiHosaka/pals-agent/pull/130)。記録の場所: `pals-agent/testdata/answer-accuracy-regression-v1/results/semantic_review.json`。
