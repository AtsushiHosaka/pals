# Individual Billing Requirements

## 2026-10-07 approved GPT selection and tariff-based consumption

The learner may select the three GPT models for answer/Lean production in PFR-001; judgment and independent QA retain their fixed server policy. New-policy consumption shall be calculated from the actual usage of each selected or fixed call and that call's model tariff, then converted to the common utilization-token unit. Pre-call worst-case reservations remain separate from actual settlement. This supersedes using conservative input-price estimates as the settled processing value for newly admitted operations under the new tariff policy. Existing plans, success-only consumption, caps, unknown-usage handling and historical records remain unchanged.

## 2026-09-30 approved USD plan change (sandbox rollout)

The user approved monthly Plus USD10, Pro USD20 and Research USD100, followed by these provisional utilization-token limits: Plus 1,000,000 per period / 100,000 per request; Pro 3,000,000 / 300,000; Research 15,000,000 / 1,500,000. These are customer utilization tokens, not raw provider tokens or request counts. Apply them only in the local Stripe sandbox until whole-operation cost and correctness evidence supports release. Free's existing allowance and existing legacy/complimentary grants are unchanged by this delta. Preserve historic usage and JPY contracts.

- BILL-012: The API owns the versioned paid-plan catalogue, closed plan selection, exact USD/month/amount/quantity validation, and actual purchased product identity. UI shows all three prices and their distinct limits in all four languages. Unknown plans, client price IDs, duplicate paid subscriptions and cross-plan reuse of a pending checkout are rejected.
- BILL-013: New token-policy operations atomically reserve the displayed quote maximum from the current period. Display used/reserved/available separately; settle the actual weighted sum once after an independently reviewed answer, release all on failure, and never exceed the displayed cap. Unknown usage is not zero. All model and retrieval calls need a durable pre-call permit and bound receipts; existing count accounting is not re-labelled.
- BILL-014: New Project creation and material additions require an active paid entitlement, including any paid tier, legacy Pro or an unexpired, unrevoked complimentary Pro grant. The API shall enforce Project creation under the shared account entitlement lock before inserting any project data. Free accounts cannot create Projects; existing Projects remain readable after cancellation or expiry. The UI shall direct Free accounts to plan settings and public pages shall describe Project creation as a paid feature. Existing file limits remain five per project and 50MB per file. Research increases monthly and per-request budgets; it does not promise successful solutions to open problems. No tier receives a lower correctness standard.

The USD rollout supersedes the single-plan exclusion only for the new catalogue. Mid-period upgrades/proration and automatic contract migration are not part of this rollout; an active subscription is managed through Portal and cannot open a duplicate subscription. Unimplemented token-operation capabilities must fail closed and be reported as incomplete, never silently fall back to 100 requests.

## 2026-09-30 approved token-policy change

新制度は固定回数から、全依頼の処理負荷を換算した「利用トークン」へ移行する。生成・内部修復・検索・独立QA・説明までを対象とし、送信前に表示した最大量を予約する。独立QA済み説明の提供成功で実績だけを確定し、失敗では消費しない。画像の読取り量も反映し、設定・アカウントメニューで実残量を示す。有料資格はProject新規作成・資料追加にも必要で、解約後の既存閲覧は維持する。

下記のFree累計3/Pro100・1,500円・generation-only計測は**稼働中の旧制度**の契約であり、新制度の完成仕様ではない。旧数値を新tokenへ呼び換えない。成功会計だけを固定1回の新制度として先行公開する方針も、この変更で置き換える。既存データは遡及変更しない。

新API/会計設計は[利用トークン接続案](../../docs/proposals/project-materials/token-accounting.md)、付与量・価格候補は[料金案](../../docs/proposals/project-materials/pricing.md)、添付とUI要件は[資料仕様案](../../docs/proposals/project-materials/requirements.md)。金額・付与量・全工程meterの検証前は新制度を有効にせず、以下の旧wire/API互換性を保持する。

## Purpose

PALS の個人利用者に、累計無料枠と月額 Pro を安全に提供する。課金の結果は、証明生成を開始する
サーバー側の entitlement だけで判定し、ブラウザの return URL や自己申告には依存しない。

## Legacy product decisions

- 初期商品は **PALS Pro: JPY 1,500 / month**。無料 trial、年額、買い切り、チーム・教育機関プランは対象外。
- Free はアカウントごとの **累計 3 proof-generation requests**。日次・月次に復活しない。
- Pro は Stripe が `active` と確認した各請求期間に **100 proof-generation requests**。
  Pro 期間の終了、未払い、取消し、または上限到達後は、未使用の Free 枠だけを使える。
- 新制度の一枠は、受付時に仮押さえし、Lean検証・独立証明QA・説明の独立QAが成功して説明を表示可能な状態で保存した時点で消費を確定する。途中の失敗では仮押さえを解放し、消費しない。説明再試行で同じ証明を二重消費しない。
- 制度切替前の予約・消費履歴は書換えず、新規受付から適用する。旧制度の失敗を推測で遡及補償しない。金額と総枠は添付機能の料金改定が確定するまで現行値を維持する。

## Definitions

- **Entitlement**: 特定 account subject が今この proof job を開始できるかを表す、API 所有の durable
  snapshot。
- **Reservation**: ひとつの accepted proof job と一対一に結びつく immutable quota 予約記録。新制度では消費確定・解放の履歴を別に保持する。
- **Stripe event ledger**: 署名検証済み Stripe event ID を一度だけ処理する append-only 記録。
- **Billing period**: Stripe subscription が返す開始・終了時刻で定義する期間。暦月やブラウザ時計ではない。

## Goals

- 個人利用者が Free 残数、Pro の価格・上限・更新日、契約の管理先を確認できる。
- 一つの account subject が同時に複数 job を作っても、確定消費と仮押さえの合計がFree 3枠または当該請求期間のPro 100枠を超えない。
- Checkout、Portal、Webhook は Stripe を唯一の課金状態ソースとし、API が署名済み Webhook から有料契約のentitlementを更新する。無償テスト資格はBILL-011の独立した管理者操作だけで付与し、Stripe契約には見せかけない。
- 課金状態にかかわらず既存 proof、chat、説明、clarification は読める。旧制度では新規proof開始を制限する。新制度では新規Project/資料追加と新規質問にも各承認済み枠を適用する。
- Google と email/password のログインはいずれも Cognito `sub` を billing account identity とし、email や
  Google subject を entitlement の照合キーにしない。

## Non-goals

- 従量課金、usage-based Stripe billing、クレジットの譲渡、金銭の返金・自動返金、税額の自動計算、法人請求、
  coupon、年額、または複数 Pro プラン。
- 旧制度ではprovider token usageは原価観測のみ。新制度では上記承認変更に従い、換算tokenを利用枠にする。Stripeの無断従量請求は追加しない。
- Google/Stripe の secret、client secret、Webhook body、カード情報を frontend、Terraform state、ログ、
  chat、proof record に保存すること。

## Functional requirements

| ID | Requirement |
|---|---|
| BILL-001 | API shall expose the authenticated learner's closed billing summary: plan (`free` or `pro`), Free and current-period Pro `used`/`limit`/`reserved`/`available` when applicable, consumption policy, billing source, current entitlement state, and period end when applicable. `used` means settled consumption, `reserved` means active holds, and `available` is the nonnegative remainder after both. Legacy admitted reservations remain consumed. It shall not expose Stripe payment data or another account's state. |
| BILL-002 | Before creating or dispatching a proof job, the API shall lock the account's entitlement and atomically insert exactly one immutable reservation bound to that proof job. It shall keep settled consumption plus active holds at or below three lifetime Free units, or 100 units for a Stripe-confirmed `active` Pro billing period or one valid complimentary grant period. Historical reservations and their sequence numbers shall remain immutable; released holds do not permit reuse of their sequence numbers. A quota rejection shall create neither a proof job nor an SQS dispatch. |
| BILL-003 | The first accepted proof job for an account without a current Pro entitlement shall lazily establish its Free entitlement. For jobs admitted under the new policy, the API shall reserve without settling consumption. Only a persisted, independently reviewed completed explanation for the verified proof settles consumption, at most once per proof job. A terminal proof or explanation failure releases its active hold exactly once; intermediate candidate failures during repair do not. An explanation retry for an unconsumed job requires a new hold in the then-valid billing scope before any retry dispatch; insufficient allowance rejects it without side effects. Successful settlement stays bound to its hold's original scope even if the billing period changes. Legacy jobs remain under their recorded original policy without retroactive refunds or additional retry charges. `POST /v1/proof-jobs` shall require an `Idempotency-Key` header of 32–128 URL-safe ASCII characters. The service binds its SHA-256 request fingerprint and key to the owner for 24 hours: an exact replay returns the existing job/reservation; a different payload or expired/reused key returns `idempotency_conflict` without mutation. After 13 calendar months from creation, maintenance shall delete the detailed idempotency record and retain only the SHA-256 owner-subject digest and SHA-256 key digest as an immutable tombstone for permanent same-account reuse rejection; no request fingerprint, job ID, response, raw owner, or timestamp remains in that tombstone. A different account may independently use the same key. |
| BILL-004 | Only the API shall create a Stripe Checkout session for PALS Pro and a Stripe Customer Portal session. It shall derive the authenticated Cognito `sub` server-side, create or reuse exactly one Stripe Customer binding for it, bind that subject in Stripe metadata, and use fixed server configuration for price, success, and cancel URLs. Frontend return query parameters and a client-supplied customer or price ID shall never grant an entitlement. |
| BILL-005 | The API shall verify Stripe webhook signatures against a configured secret before parsing or persisting an event. It shall deduplicate by Stripe event ID, record only the minimum event metadata needed for audit, and derive subscription/entitlement snapshots only from accepted webhook events. A temporary Stripe lookup failure shall return HTTP 503 and roll back the event transaction, preserving the previous entitlement and leaving the event eligible for Stripe redelivery. `checkout.session.completed` alone shall not grant Pro; only an `active` subscription grants paid Pro. Complimentary Pro is separately governed by BILL-011. Invalid, expired, duplicate, unknown, or out-of-order events shall fail closed without raising an entitlement. |
| BILL-006 | Billing data shall be account-scoped by the verified Cognito `sub`; endpoints require normal learner authentication. A user may create Checkout/Portal sessions and view the summary only for self. Worker, agent, public anonymous, generic internal, and Stripe-return requests without a verified bearer token shall have no billing management access. |
| BILL-007 | The frontend shall distinguish complimentary grants under BILL-011 and otherwise present the Free lifetime limit and remaining requests; for an existing legacy Pro subscription its JPY 1,500 monthly price, 100-request period limit and management action; and for a USD token plan its product, price, used/reserved/available utilization tokens, per-request maximum, period end and management action. It shall present the API's paid-plan catalogue (BILL-012) with an upgrade action enabled only when the API reports `checkout_enabled`; no new legacy JPY upgrade action is offered. For the new policy it shall distinguish reserved, consumed, and available allowance, explain that consumption is finalized only after a reviewed explanation is available, and state that terminal failures release the hold. It shall not describe old-policy consumption as refundable or count held units as available. A quota rejection shall be understandable and link to the usage and plan settings. |
| BILL-008 | Production Cognito shall support the existing email/password flow and Google Hosted UI authorization-code + PKCE flow. Google federation is enabled only with an operator-supplied Google OAuth client ID/secret, a Cognito Hosted UI domain, and exact HTTPS callback/logout URLs. Both flows must issue access tokens the API validates. Different Cognito `sub` values are distinct billing accounts; initial release performs no automatic email-based identity merge or account linking. |
| BILL-009 | The release configuration shall fail closed unless a single SSM SecureString JSON object supplies Stripe secret key, webhook signing secret, Pro Price ID, billing success/cancel URLs, and launch-enable flag. Google client credentials are a separate SSM SecureString JSON object and are used only by a secret-safe external Cognito IdP provisioner. Terraform owns non-secret parameter names/IAM and Cognito resources only; production follows DPB-008/010 without NAT or application secret resources in Terraform, and it shall never receive either JSON value. |
| BILL-010 | A worker-authenticated, closed usage-ingest operation shall record bounded, content-free provider usage per generation call. It binds a unique call ID to the active proof-generation claim, proof job, provider/model, token counts, and a checked-in price-snapshot ID; it accepts an exact replay only. The aggregate is safe numeric cost telemetry for future pricing review and excludes prompt, theorem statement, Lean code, explanation, chat, email, and API credentials. Missing usage data must not reduce or refund a reservation. |
| BILL-011 | An operator may grant an existing Cognito account complimentary Pro without payment or a Stripe subscription. The grant requires an explicit future expiry, a bounded audit reason, an immutable operation/grant ID, and a trusted database operator identity. A distinct operator role may grant/revoke/show; application runtime, workers and learners cannot grant or revoke. Active Stripe Pro takes precedence; otherwise an unexpired, unrevoked grant permits the normal 100-request allowance for that grant period with existing unused Free fallback. Sources are never added to create a double Pro allowance. Expiry/revocation affects future admission only and preserves accepted jobs, history and read access. A duplicate grant operation does not reset consumption; overlapping grants for one account are rejected under the same admission lock. Summary/UI identify `billing_source` as `free`, `stripe`, or `complimentary`; complimentary Pro shows its expiry and does not imply monthly payment, automatic renewal, or require a Stripe Portal. This is an explicit working delta for the existing count policy, not the unimplemented token-policy migration. |
| BILL-015 | A member chat request's single hold (count policy) or token operation (token policy) covers intent classification, ordinary explanation or its linked Lean proof job, and the required independent review; the linked job shall not create a second reservation. The hold or operation is consumed exactly once when the selected route persists its independently reviewed answer: a Lean-verified (`lean_catalog` or `lean_verified`) proof, or the ordinary explanation approved under CHAT-008. It is released exactly once on terminal failure or needs-input under the member policy. Under token policy, provider calls, including image processing and linked-job calls, obtain permits and receipts against the request's token operation. Existing count accounting is not re-labelled as weighted tokens. Guest requests use only the guest daily budgets (GUEST-003), including accepted failures and clarification sends. |
| BILL-016 | For newly admitted tariff-policy operations, the API shall calculate processing value from actual provider usage and immutable, model-specific price snapshots, then convert the whole operation once to common utilization tokens. Ordinary input, cached input and cache writes shall use their applicable distinct rates; input subsets and reasoning-output subsets shall not be charged twice. Applicable context-length, service-tier and regional pricing shall be bound and accounted for. Unknown counts or pricing must not be invented or interpreted as zero; conservative pre-call bounds must not be presented as actual settled usage. Intent classification, assessment, image processing, retrieval, ordinary explanation, linked Lean generation, repair and independent reviews shall be metered against the same operation under BILL-013/015 before this policy is enabled. Actual provider cost telemetry shall remain available on failure while customer consumption remains zero. Prices and unit conversion shall be fixed at admission; future changes apply only to new operations. Legacy snapshots, receipts and settlements remain immutable. |

## Acceptance criteria

- A new authenticated account can have at most three Free units consumed or held. A fourth concurrent job is rejected before creation/dispatch; a terminal failure releases a hold, allowing a later request. Three successful completed explanations exhaust the Free allowance.
- A Pro account can have at most 100 units consumed or held in Stripe's current billing period. Duplicate completion or failure events never duplicate consumption or release. The next confirmed billing period starts a distinct allowance; old holds never become new-period credits.
- A failed explanation leaves the proof verified but releases the new-policy hold. A later explanation retry reserves available allowance before dispatch and settles at most once for the proof, regardless of repeated retry requests.
- The UI and API show consumed/reserved/available consistently. Prior-policy reservations and idempotency history remain unchanged.
- A browser that visits a Checkout success URL without a confirmed Stripe entitlement remains Free.
- A duplicate signed Stripe event and an invalid signature leave entitlement/reservations unchanged.
- A temporary Stripe lookup failure returns 503 without an event-ledger entry or entitlement mutation. Redelivery of the same event after recovery succeeds exactly once; permanent subscription validation failures remain non-granting.
- Free accounts cannot create a Project through either the UI or API. Active paid tiers and valid complimentary Pro grants can; expired or revoked entitlements cannot. Denial creates no project data and preserves existing read access.
- Public pages and account settings publish Plus USD 10/month, Pro USD 20/month and Research USD 100/month. Disabled Checkout is described as purchase preparation, never as an undecided price or unavailable product.
- Google and password sessions with the same Cognito `sub` share one entitlement; different subjects stay separate even if
  their emails match, and the UI does not claim automatic account merging.
- Existing proof/chat reading works after quota exhaustion or cancellation.
- A payment-free grant uses a real registered account and no fabricated Stripe rows. Operator grant/revoke and application admission serialize on the same account lock. Grant replay preserves original expiry and used count; another active grant is rejected.
- App/worker DB roles cannot insert grants/revocations or execute the operator mutation functions. An ordinary learner cannot promote self through query params, JSON, Checkout return, or an added public admin endpoint.
- At the exact expiry or after revoke, new admission uses the existing Free fallback; old accepted jobs and source/usage records remain unchanged. Paid Stripe Pro takes precedence without merging its quota with the complimentary quota.
- All four UI languages distinguish complimentary Pro expiry from paid subscription renewal. Real PostgreSQL and public API tests verify the allowance path; Stripe smoke is a separate still-unconfigured dependency.

## Constraints and assumptions

- This price is an initial guardrail, not a usage-derived break-even price. Historical jobs without provider usage are
  not backfilled with invented costs. The original 2026-08-19 estimate used `gpt-5.4-nano` with a 12,000 output-token cap; its published
  standard API price was USD 0.20/M input and USD 1.25/M output tokens on 2026-08-19, recorded from
  <https://developers.openai.com/api/docs/models/gpt-5.4-nano>. The 2026-09-29 generation roles used
  `gpt-5.4-mini-2026-03-17`; retain that historical price snapshot as documented in
  [model price snapshots](../../docs/billing-model-price-snapshots-2026-09-29.md). The approved 2026-09-30 delta
  uses `gpt-6-luna` by default and `gpt-5.6-terra` only for bounded mathematical escalation. New model estimates
  conservatively include cache-write input pricing and the long-context multiplier; the snapshot names identify
  these as upper-bound estimates rather than exact invoices. See [current model notes](../../docs/proof-reuse-latency-decisions-research-2026-09-30.md).
  The 2026-10-07 PFR-001/BILL-016 delta additionally permits selected Sol and Terra and requires a distinct tariff policy for new operations; these earlier upper-bound snapshots remain historical estimates. BILL-010 covers recorded provider calls, not a complete provider invoice. Provider and infrastructure cost telemetry will be
  reviewed after the first 30 paid accounts or 90 days, whichever occurs first.
- Stripe account country, merchant-of-record, consumption-tax registration, invoice wording, refund policy, and
  customer-facing tax disclosure require an operator/legal decision before public Checkout is enabled. The implementation
  must keep Checkout disabled until those release inputs are complete.
- Stripe secrets and Google OAuth credentials are operational inputs, not repository artifacts.

## 2026-10-05 approved corrections

- The user reaffirmed that Project creation requires a paid account. Apply BILL-014 now and remove the public landing page's Free-project claim.
- Monthly Plus USD 10, Pro USD 20 and Research USD 100 are decided prices. Publish them in public pages and settings independently of `checkout_enabled`; preserve the existing catalogue wire version and launch gate.
- Temporary Stripe lookup failures must request redelivery with 503 instead of consuming the event and downgrading the account.

The success-based policy is an approved 2026-09-30 working delta. Weighted image usage and whole-document processing allowances are being designed in [the materials proposal](../../docs/proposals/project-materials/requirements.md). The price-publication and Project-access corrections do not enable public Checkout. Tax/legal release inputs remain an operational launch gate.

## Working delta: natural proof answers (2026-09-30)

The user-approved [proof-request reuse](../proof-request-reuse/requirements.md) path shares the same account entitlement and quota lock with formal jobs. A queued/assessing request holds a slot. Needs-input and failed outcomes release it; continuation reacquires a slot; an answered request consumes it once. This does not label the answer Lean-verified. Record provider usage on each call even when the outcome is a question or failure. Complimentary Pro applies through the existing entitlement resolver. Request ownership, revision, claim and idempotency fences apply to all usage and settlement operations.
