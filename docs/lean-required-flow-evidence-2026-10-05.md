# Lean必須フロー — ローカル通し確認の証跡（2026-10-05）

計画：[lean-required-flow-plan-2026-10-05.md](lean-required-flow-plan-2026-10-05.md)。対象はローカル共有環境（Docker Compose project `pals-local`）。本番は変更していない（Phase 7 は別途承認）。

## 実行したイメージとコミット

| 対象 | イメージ | コミット |
|---|---|---|
| API | `pals-api:leanflow-20261005` | `5a741bd`（以後の追加はテストのみ：`03aadaf`） |
| worker | `pals-agent-worker:leanflow-20261005` | `07ff6b3` |
| 画面 | `pals-webfront:leanflow-20261005` | `622d88c` |
| verifier / reconciler | `pals-lean-verifier:local` / `pals-api:local` | 期限切れのローカル TLS を作り直して再起動 |

共有 DB には appended step `proof-request-lean`（`proof_request_lean/001_lean_flow.sql`）を適用済み。古いコードの API は起動時の確認でこの schema を拒否するため、他セッションは最新 main で作り直す必要がある。

## 結果

| 確認 | 結果 | 証跡 |
|---|---|---|
| DSP で新しい定理を証明（ログイン・Project なし） | 成功 | 要求 `f966489d…` → ジョブ `ae77931b…`：修復を経て `verified`、説明のレビュー後に要求が `answered`（`lean_verified`）。画面に「Lean-verified」と検証済みの証明・Lean source を開くボタン。 |
| 検証済みの証明と Lean source を開く | 成功 | ボタンでジョブの説明が開き、`</>` で Lean source を表示。 |
| 追加質問 | 成功 | 説明の一部を選んで質問 → 回答が説明内に表示。回答本文に `\n` が文字のまま残る既存の問題を見つけ、別タスクにした。 |
| 失敗時に回答を出さない | 成功 | 偽の命題「n²+n は奇数」：修復後に Lean は弱めた別の命題をコンパイルしたが、意味レビューが不一致で失敗させた（`pals.proof_semantic_review_failed`）。要求は `failed`（`lean_verification_failed`）、回答なし。画面は「Lean could not verify this proof, so no answer is shown.」と再試行のみ。 |
| 利用枠 | 成功 | 成功した要求の仮押さえは `consumed`、失敗した要求は `released`（無料枠を消費しない）。 |
| ゲスト（/try） | 成功 | 要求 `4b85b435…` → ジョブ `c351badc…` が `verified`、要求は `answered`（`lean_verified`）。画面に「Lean-verified proof」と Lean source（折りたたみ）。1日の残り回数は 3 → 2。375px でも横スクロールなし（Lean source の枠内だけスクロール）。 |
| スマホ・タブレット・PC | 成功（修正後） | 375px で「検証済みの証明…を開く」ボタンが折り返さず画面外にはみ出していたのを修正（webfront `622d88c`）。375 / 768 / デスクトップで横スクロールなし。 |
| カタログ再利用（コンパイルなし） | ローカルでは未確認 | 下の「確認できなかったこと」を参照。経路は実 PostgreSQL の結合テストと、追加した単体テスト（API `03aadaf`：完全一致のときだけ再利用し、それ以外は DSP に回す）で確認。 |
| 特殊化の代入版コンパイル | 未実装 | PFR-011 の代入ステージは未実装。`instantiate` の計画も DSP で検証される（Lean 検証は必ず行われる）。 |

## 確認できなかったこと・見つかった問題

1. **カタログ再利用をローカルで通せない。** ローカルで登録済みの Recipe（x² の連続性）は、現行と異なる toolchain（verifier ハッシュが仮の値）で登録されていて、設計どおり再利用の対象外。現行 toolchain で登録し直す過程で次の 2 点が分かった。
   - **同じ Lean source の Recipe は toolchain 更新後に登録し直せない。** `recipe_evidence.materialized_source_sha256` が全体で一意のため。本番で Lean/Mathlib を更新すると、既存の Recipe はすべて再利用不可になり、source を変えない限り戻せない。Recipe Catalog の仕様課題（LRC）として記録する。
   - ローカルでは確認のため、証明本文にコメント 1 行を足した revision 2 を、実 verifier（mTLS・現行 toolchain）でコンパイルして登録した。ただし Draft との対応付け（alignment）の登録は、ローカルの Draft DB が旧形式のテーブルで PFI カタログの schema を持たないため通らない。PFI を入れると `public.dsp_drafts` がビューに置き換わるので、共有環境では行わなかった。revision 2 は対応付けがないため、選択や再利用には使われない。
2. **worker が 1 プロセスで、Lean ジョブが他の質問を待たせる。** worker は SQS から 1 件ずつ処理する。DSP の Lean ジョブ（数分）を処理している間、他のユーザーやゲストの新しい質問は評価も始まらない（今回のゲストの質問は、先行する Lean ジョブが終わるまで約 3 分 `queued`）。本番では、質問の評価を受け持つ worker（`PALS_PROOF_CAPABILITY=natural-only`）と Lean ジョブ用の worker を分けることを Phase 7 の前提にする。ただし今の `natural-only` worker は、受け取った Lean ジョブのメッセージを可視性タイムアウトまで隠したままにするので、キューを分けるか、すぐ戻すようにする必要がある。
3. **本番の起動確認が厳格になった**（別セッション、API `9fdcbf5`）。本番は proof request の schema が v1 と完全一致でないと起動しない。本番に Lean フローを入れるときは、この確認と本番のリリース登録に `proof-request-lean` を加える必要がある（Phase 7）。

## 残り（spec の tasks と対応）

- PFR-011：要求に紐付くジョブで、DSP の前に代入版をコンパイルする。
- PFR-006 / BILL-015：紐付くジョブの LLM 呼び出しに、要求のトークン操作から許可を取って記録する（現在は評価段階の利用だけを精算）。
- Phase 5：Draft 追加候補（DAC-001〜006）。
- Phase 7：本番反映（worker の分離、本番リリース登録、Mac 更新手順、LP/FAQ の文言の最終確認）。
