# Spec ↔ implementation review — 2026-10-05

Scope: `specs/` against the pinned `pals-api`, `pals-webfront` and `pals-agent` sources, plus a security, billing and responsive-layout pass.

## Spec alignment

Implemented behavior without a canonical spec now has one: `specs/public-guest-chat`, `specs/project-materials`, `specs/chat-navigation`. `specs/README.md` indexes every canonical and repository-owned spec. `individual-billing` BILL-007/BILL-014 describe the current plan UI and gating, and two product decisions are recorded as open questions. The materials proposal points to the canonical spec.

## Changes made

| Repo | Commit | Change |
|---|---|---|
| pals-webfront | `fc3a0b5` | Remove the project-home materials panel; remove PDF/material claims from the landing copy in four languages. The original attribution to a user decision was incorrect; see the correction below. |
| pals-webfront | `299d1ea` | Phone layout: wide display equations no longer push chat messages past the viewport; the mobile navigation sheet no longer clips icons; the composer grows with its text; TeX in suggested follow-up placeholders is shown as plain Unicode or falls back. |
| pals-api | `bdd3e26` | An unnamed failed OCR material no longer rejects every question in its project. |

The answer citation panel was removed by a separate session in webfront `5267537`.

## PDF添付の削除判断を訂正（2026-10-05）

PDF添付を削除するユーザー指示は確認できなかった。Claudeのレビュー用チャットでは「OCRのやつとか、何でこの位置にあるの？」「このUIは必要ないから削除してもらって構わない」という指示を、エージェントが `remove the OCR/attachments UI` と解釈していた。最初の依頼には「実装済の機能を勝手にデグレさせることは絶対にしないでください」とも明記されていた。

webfront `5267537` は回答のOCR出典表示を削除した。これとは別に `fc3a0b5` がプロジェクトの添付管理UIまで削除し、親リポジトリ `cf823eb` がMAT-003を撤回済みとして仕様に記録した。指示の対象を広げたうえで、その解釈を「ユーザー判断」と記録したのが誤りである。

根拠はClaudeセッション `522df5c0-8c34-47c6-b81a-fb52a5f6a4e5` の元ログ（359行目のユーザー指示、367行目の解釈、1472行目の完了報告）と、Codexチャット「選択範囲への質問機能を復旧」（`01a1076d-fe60-7e92-a343-7f2beb4956c9`）のOCR表示削除の指示。Gitの著者名を、削除を指示した人の証拠として扱わない。

今回の「PDF添付は必要です。specもそのようにしておいてください」というユーザー指示に従い、`specs/project-materials` のrequirements・design・tasksを更新した。MAT-003は同じ資料管理機能の要件として維持し、PDF添付を画面から利用できることを必須とする。回答の不要なOCR表示は削除したままにする。既存のAPI、所有者制限、最大5件・各50MB、有料資格の条件は変更しない。UI復旧と実ブラウザ検証は未完了であり、過去の実装記録だけで復旧完了とは判定しない。今後、指示の対象が不明な場合は、機能を削除する前に対象を確認する。

## Verification

- pals-webfront: typecheck, full ESLint and 121 files / 1,348 tests passed after rebasing onto `5267537`; production build passed.
- pals-api: 1,758 unit tests passed. `test_initial_mac_recipe_authority.py::test_production_registry_retains_recipe_positions_and_adds_catalog_before_reader` fails identically on the unmodified base. The real-PostgreSQL material integration tests were not run.
- Responsive: a build of these changes against the running local API, signed in as a throwaway local Cognito test user (`pals-responsive-check@example.test`), checked at 375×812, 768×1024 and 1280×800: dashboard, projects, project home, project chat with a real answer, mobile navigation, settings/billing, chat search, `/about` and `/try`. No page-level horizontal overflow remained. That user, its "Responsive check" project and one answered request remain in the local stack.
- `pals-scripts/check-secrets.sh` reports 4 pre-existing matches in `pals-agent` and `pals-observability` test fixtures, unrelated to these changes.

## Findings left for decision

- Stripe webhook: a transient Stripe API failure during reconciliation records the event as `reconciliation_pending`, marks the entitlement inactive and still returns 200, so Stripe does not redeliver. A paying subscriber stays downgraded until another event or a manual fix (the design says this deliberately). Returning 503 without recording the event on transient failures would let Stripe's retries restore access.
- Paid gating of Project creation (approved token policy) conflicts with the public "free account can organize into projects" copy; Project creation is currently open.
- Production settings show the provisional USD plans as unavailable while public pages say prices are unpublished.
- The landing page advertises Lean compilation and Lean-line hover; per CORE-012 new questions are not Lean-verified, so those features apply only to older verified history.
- Stripe Portal plan switching must stay disabled: a Portal plan change keeps the old `billing_product_id` metadata and the reconciler would mark the subscription inactive.
