# Individual Billing Requirements

## Purpose

PALS の個人利用者に、累計無料枠と月額 Pro を安全に提供する。課金の結果は、証明生成を開始する
サーバー側の entitlement だけで判定し、ブラウザの return URL や自己申告には依存しない。

## Product decisions

- 初期商品は **PALS Pro: JPY 1,500 / month**。無料 trial、年額、買い切り、チーム・教育機関プランは対象外。
- Free はアカウントごとの **累計 3 proof-generation requests**。日次・月次に復活しない。
- Pro は Stripe が `active` と確認した各請求期間に **100 proof-generation requests**。
  Pro 期間の終了、未払い、取消し、または上限到達後は、未使用の Free 枠だけを使える。
- 一枠は、認証済み利用者の proof job が受理され、生成 queue へ送るために予約された時点で消費する。
  Lean verification や回答品質が失敗しても返却しない。これにより再試行や失敗を使った無制限の API
  消費を防ぐ。

## Definitions

- **Entitlement**: 特定 account subject が今この proof job を開始できるかを表す、API 所有の durable
  snapshot。
- **Reservation**: ひとつの accepted proof job と一対一に結びつく immutable quota 消費記録。
- **Stripe event ledger**: 署名検証済み Stripe event ID を一度だけ処理する append-only 記録。
- **Billing period**: Stripe subscription が返す開始・終了時刻で定義する期間。暦月やブラウザ時計ではない。

## Goals

- 個人利用者が Free 残数、Pro の価格・上限・更新日、契約の管理先を確認できる。
- 一つの account subject が同時に複数 job を作っても、Free 3 枠またはその billing period の Pro 100 枠を
  超えない。
- Checkout、Portal、Webhook は Stripe を唯一の課金状態ソースとし、API が署名済み Webhook から
  entitlement を更新する。
- 課金状態にかかわらず既存 proof、chat、説明、clarification は読める。制限するのは新規 proof job
  開始だけである。
- Google と email/password のログインはいずれも Cognito `sub` を billing account identity とし、email や
  Google subject を entitlement の照合キーにしない。

## Non-goals

- 従量課金、usage-based Stripe billing、クレジットの譲渡、返金、自動返金、税額の自動計算、法人請求、
  coupon、年額、または複数 Pro プラン。
- provider token usage を顧客への請求単位にすること。初期リリースでは job reservation を上限単位とする。
- Google/Stripe の secret、client secret、Webhook body、カード情報を frontend、Terraform state、ログ、
  chat、proof record に保存すること。

## Functional requirements

| ID | Requirement |
|---|---|
| BILL-001 | API shall expose the authenticated learner's closed billing summary: plan (`free` or `pro`), Free `used`/`limit`, current-period Pro `used`/`limit` when applicable, current entitlement state, and period end when applicable. It shall not expose Stripe payment data or another account's state. |
| BILL-002 | Before creating or dispatching a proof job, the API shall lock the account's entitlement and atomically insert exactly one immutable reservation bound to that proof job. It shall admit at most three lifetime Free reservations, or at most 100 reservations for a Stripe-confirmed `active` Pro billing period. A quota rejection shall create neither a proof job nor an SQS dispatch. |
| BILL-003 | The first accepted proof job for an account without a current Pro entitlement shall lazily establish its Free entitlement. A reservation is never automatically refunded because the worker, verifier, explanation, or client later fails. `POST /v1/proof-jobs` shall require an `Idempotency-Key` header of 32–128 URL-safe ASCII characters. The service binds its SHA-256 request fingerprint and key to the owner for 24 hours: an exact replay returns the existing job/reservation; a different payload or expired/reused key returns `idempotency_conflict` without mutation. |
| BILL-004 | Only the API shall create a Stripe Checkout session for PALS Pro and a Stripe Customer Portal session. It shall derive the authenticated Cognito `sub` server-side, create or reuse exactly one Stripe Customer binding for it, bind that subject in Stripe metadata, and use fixed server configuration for price, success, and cancel URLs. Frontend return query parameters and a client-supplied customer or price ID shall never grant an entitlement. |
| BILL-005 | The API shall verify Stripe webhook signatures against a configured secret before parsing or persisting an event. It shall deduplicate by Stripe event ID, record only the minimum event metadata needed for audit, and derive subscription/entitlement snapshots only from accepted webhook events. `checkout.session.completed` alone shall not grant Pro; only an `active` subscription grants it. Invalid, expired, duplicate, unknown, or out-of-order events shall fail closed without raising an entitlement. |
| BILL-006 | Billing data shall be account-scoped by the verified Cognito `sub`; endpoints require normal learner authentication. A user may create Checkout/Portal sessions and view the summary only for self. Worker, agent, public anonymous, generic internal, and Stripe-return requests without a verified bearer token shall have no billing management access. |
| BILL-007 | The frontend shall present the Free lifetime limit, remaining requests, PALS Pro's JPY 1,500 monthly price and 100-request period limit, an upgrade action, and a management action for an active Pro subscription. It shall explain that a request consumes a slot when started and failed proof attempts do not restore it. A quota rejection shall be understandable and link to upgrade when eligible. |
| BILL-008 | Production Cognito shall support the existing email/password flow and Google Hosted UI authorization-code + PKCE flow. Google federation is enabled only with an operator-supplied Google OAuth client ID/secret, a Cognito Hosted UI domain, and exact HTTPS callback/logout URLs. Both flows must issue access tokens the API validates. Different Cognito `sub` values are distinct billing accounts; initial release performs no automatic email-based identity merge or account linking. |
| BILL-009 | The release configuration shall fail closed unless a single Secrets Manager JSON object supplies Stripe secret key, webhook signing secret, Pro Price ID, billing success/cancel URLs, and launch-enable flag. Google client credentials are a separate Secrets Manager JSON object and are used only by a secret-safe external Cognito IdP provisioner. Terraform owns secret containers and non-secret Cognito/egress resources only; it shall never receive either JSON value. |
| BILL-010 | A worker-authenticated, closed usage-ingest operation shall record bounded, content-free provider usage per generation call. It binds a unique call ID to the active proof-generation claim, proof job, provider/model, token counts, and a checked-in price-snapshot ID; it accepts an exact replay only. The aggregate is safe numeric cost telemetry for future pricing review and excludes prompt, theorem statement, Lean code, explanation, chat, email, and API credentials. Missing usage data must not reduce or refund a reservation. |

## Acceptance criteria

- A new authenticated account can start exactly three proof jobs across any number of days, then receives a quota rejection before a fourth job or queue dispatch.
- A Pro account can start at most 100 jobs in Stripe's current billing period; concurrent requests cannot exceed 100, and the next confirmed billing period starts a distinct allowance.
- A browser that visits a Checkout success URL without a confirmed Stripe entitlement remains Free.
- A duplicate signed Stripe event and an invalid signature leave entitlement/reservations unchanged.
- Google and password sessions with the same Cognito `sub` share one entitlement; different subjects stay separate even if
  their emails match, and the UI does not claim automatic account merging.
- Existing proof/chat reading works after quota exhaustion or cancellation.

## Constraints and assumptions

- This price is an initial guardrail, not a usage-derived break-even price: current normal proof generation does not persist
  historical token usage. The current default model is `gpt-5.4-nano` with a 12,000 output-token cap; its published
  standard API price was USD 0.20/M input and USD 1.25/M output tokens on 2026-08-19, recorded from
  <https://developers.openai.com/api/docs/models/gpt-5.4-nano>. Provider and infrastructure cost telemetry will be
  reviewed after the first 30 paid accounts or 90 days, whichever occurs first.
- Stripe account country, merchant-of-record, consumption-tax registration, invoice wording, refund policy, and
  customer-facing tax disclosure require an operator/legal decision before public Checkout is enabled. The implementation
  must keep Checkout disabled until those release inputs are complete.
- Stripe secrets and Google OAuth credentials are operational inputs, not repository artifacts.

## Open questions

None for the product's initial plan and quota. Tax/legal release inputs remain an operational launch gate, not an
alternate product behavior.
