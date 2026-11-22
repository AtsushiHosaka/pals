# 意味の審査の不合格: 理由コードの分離（実装）と再形式化の測定（2026-11-14）

- 指標: 意味の審査で却下された依頼の記録の精度（依頼の理由コード）、却下後に作り直した場合の回答が返る割合・費用・時間。
- 変更（(a)、マージ済み）: [pals-api#106](https://github.com/AtsushiHosaka/pals-api/pull/106)。却下・利用不能で終端した Lean 依頼の `error_code` を `lean_semantic_review_failed` / `lean_semantic_review_unavailable` で保存し、公開応答の `error_code` は従来の `lean_verification_failed` のまま、追加の `failure_reason` を該当依頼にだけ付ける。DB 移行なし。独立レビューの指摘（OpenAPI 再生成、候補の failure_code の併用）を反映。実 PostgreSQL と CI（api-regression）で検証。本番へは未配備。
- 測定（(b) の効果、[pals-agent#137](https://github.com/AtsushiHosaka/pals-agent/pull/137)）: 却下の実例 4 種×2 回×2 腕。Draft から作り直すだけで 8/8 が再審査で承認（修復の平均 1.38、壁時計の中央値 98.9 s、推計 US$0.36）。却下理由を渡す指針を足した試作は 8/8（平均 1.62、101.0 s、US$0.42）で、改善しないため不採用。誤った命題は通っていない（再審査で承認されたのは新しく生成された Lean）。
- 判断: (a) 採用。(b) の agent 側（理由を渡す指針、既定 off のフラグ）は実装しない。作り直し自体は有効だが、API の状態遷移（`semantic_review` → `compiling`）が要る。現在の遷移表（`proof_job.py`）はこれを許さない。
- 限界・未確認: 却下された入力は人手で作った例で、本番の却下の分布ではない（n=8/腕）。画面が未知の `error_code` をどう表示するかは確かめていない（公開応答は従来コードのまま）。旧版 API へのロールバックや混在配備では、新しいコードが公開の `error_code` に出る。
- 次にやること: 状態遷移の設計の承認（再形式化 1 回、既定 off のフラグ、`semantic_reformalizations` の上限）。画面の文言の変更は提案にとどめる。
- 出典: pals-api#106、pals-agent#137（README の G 節、`results/reformalize_after_semantic_rejection.json`）、[契約案](../../semantic-review-rejection-contract-2026-11-14.md)。
