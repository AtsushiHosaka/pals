# Individual Billing Design

## USD sandbox rollout (2026-09-30)

Use an API-owned `usd-monthly-test-2026-09-30` catalogue for plus/pro/research. A closed runtime v2 maps these IDs to distinct Stripe Prices and optionally retains the legacy JPY Pro Price. Add product identity to Stripe operations/subscriptions; preserve the existing Free/Pro entitlement classification for legacy callers and expose the actual product separately in summary v2. Only local test keys may activate the provisional token policy.

Token accounting uses separate additive tables for quote, operation and provider-call permits/receipts. The conversion baseline is the existing proposal of one utilization token per USD0.75/1,000,000 of price-snapshot processing value; calculate integer numerators and round once per successful operation. Cached and reasoning token subsets are not counted twice. Price weights are fixed for each operation. Legacy records stay separate.

Quotes bind the authenticated owner, action, request fingerprint, maximum and a five-minute expiry. Start/retry atomically validate the quote and current product, reserve from one period, and write the request/outbox. Claim-bound provider permits reserve worst-case call cost before transmission. Missing/unknown receipts or failed QA cannot settle success. A crashed token claim with pending calls is terminally released on claim recovery rather than repeating an uncertain provider call. A failed cycle is never retroactively charged. Runtime capability gates remain closed for any unwired operation path.

## 2026-09-30 approved token-policy change

新制度は固定回数から、全依頼の処理負荷を換算した「利用トークン」へ移行する。生成・内部修復・検索・独立QA・説明までを対象とし、送信前に表示した最大量を予約する。独立QA済み説明の提供成功で実績だけを確定し、失敗では消費しない。画像の読取り量も反映し、設定・アカウントメニューで実残量を示す。有料資格はProject新規作成・資料追加にも必要で、解約後の既存閲覧は維持する。

下記のFree累計3/Pro100・1,500円・generation-only計測は**稼働中の旧制度**の契約であり、新制度の完成仕様ではない。旧数値を新tokenへ呼び換えない。成功会計だけを固定1回の新制度として先行公開する方針も、この変更で置き換える。既存データは遡及変更しない。

新API/会計設計は[利用トークン接続案](../../docs/proposals/project-materials/token-accounting.md)、付与量・価格候補は[料金案](../../docs/proposals/project-materials/pricing.md)、添付とUI要件は[資料仕様案](../../docs/proposals/project-materials/requirements.md)。金額・付与量・全工程meterの検証前は新制度を有効にせず、以下の旧wire/API互換性を保持する。

## Scope and traceability

This design implements BILL-001 through BILL-010 in `pals-api`, `pals-webfront`, and the production
Terraform release surface. The existing implementation is a job-reservation entitlement system. The approved token policy above supersedes its product unit for new operations once the replacement is verified. Existing proof verification and chat ownership remain unchanged.

## Ownership and data model

`pals-api` owns all billing writes. PostgreSQL records only the following account-scoped, content-free data:

- `billing_customers`: immutable Cognito `owner_user_id`, Stripe customer ID, timestamps;
- `billing_subscriptions`: Stripe subscription ID, customer binding, status, current period start/end, latest accepted
  Stripe event creation time, and metadata revision;
- `billing_entitlements`: owner, plan, Stripe subscription reference when Pro, current state, and observed period;
- `billing_quota_reservations`: owner, proof job ID (unique), plan, limit scope (`lifetime` or exact Stripe period),
  reservation sequence, and timestamp;
- `billing_proof_job_idempotency`: owner, SHA-256 idempotency-key digest, request fingerprint SHA-256, proof job ID,
  first response status, and expiry timestamp;
- `billing_proof_job_idempotency_tombstones`: only SHA-256 owner-subject and key digests, a composite primary key, and immutable rows; no raw owner, job, request fingerprint, response, or timestamp.
- `billing_stripe_operations`: immutable operation ID, owner, kind (`customer` or `checkout`), Stripe idempotency key,
  optional resulting Stripe object ID, `pending`/`completed`/`expired` status, and timestamps. A partial unique index
  permits one pending customer operation per owner and one unexpired checkout operation per owner; Stripe idempotency
  key and `(owner, kind, operation ID)` are unique. Allowed transitions are `pending -> completed` or `expired`; a
  later checkout call returns/reconciles the existing operation. A completed terminal session is retired only after
  retrieving its current associated subscription; only canceled/incomplete-expired subscriptions, or an expired
  session without a subscription, permit a new operation. No operation is deleted;
- `billing_stripe_events`: Stripe event ID (unique), event type, event creation time, received time, verified payload
  SHA-256, and processing outcome;
- `proof_job_usage_calls`: immutable call ID (unique), proof job ID, generation claim ID, provider/model, nonnegative
  input/output token counts, optional cached and reasoning tokens, price snapshot ID, integer micros-USD cost estimate,
  and recorded timestamp. Per-job and monthly aggregates are derived from these rows, never updated source facts.

No billing relation contains payment method detail, card detail, email, OAuth provider subject, prompt, theorem,
Lean source, chat, explanation, clarification, raw webhook body, or provider request/response payload. The raw Stripe
body exists only in memory for signature verification and is discarded after minimal projection.

Stripe event metadata, detailed proof-job idempotency records, and resolved Stripe-operation records are retained for 13 months. Idempotency maintenance atomically inserts the two-digest tombstone before deleting each expired detail record; tombstones are retained indefinitely solely to reject same-account key reuse. Pending/unresolved Stripe operations are outside this retention change and remain preserved. Numeric proof-job usage is
retained for 90 days and then irreversibly aggregated by calendar month without job/account linkage. Only an API-owned
support-auditor role may read event metadata; normal runtime and learner endpoints read summary projections only. A later
privacy policy may shorten but must not silently extend the detail windows. The explicitly approved minimal idempotency tombstone exception does not retain request/job linkage.

`owner_user_id` is the validated Cognito access-token `sub`; it is never derived from email. Database policies and
repository queries bind every learner-facing read/write to that value. Two different Cognito subjects never merge based
on a matching email in this release. An explicit account-link feature would require a separately authenticated,
consented Cognito `AdminLinkProviderForUser` design and is out of scope.

## Entitlement and reservation transaction

The existing authenticated proof-job create service requires the exact `Idempotency-Key` header `[A-Za-z0-9_-]{32,128}`
and receives an API-owned `BillingAdmissionService` dependency. It RFC-8785-canonicalizes the closed create payload,
hashes it and the header independently, and keeps the digests—not the original request—in the 24-hour idempotency
record. In one
PostgreSQL transaction it obtains an advisory/account-row lock, reads the authoritative entitlement snapshot, counts settled consumption and active holds
in the selected scope, rejects an exhausted allowance, creates the proof job, and inserts the reservation.
The transaction commits before the existing outbox/SQS dispatch path; any failure rolls back both job and reservation.
An existing non-expired `(owner,key digest)` is resolved before a new reservation: equal request fingerprint returns the
original response, while a changed fingerprint or key reuse after expiry returns HTTP 409 `idempotency_conflict`.
Maintenance obtains the same account advisory lock as admission before moving details to tombstones. Admission checks both live details and the owner/key digest tombstone under that lock, so concurrent purge cannot make a used key reusable. The owner digest is SHA-256 of the exact UTF-8 authenticated subject, independently hashed from the key. Runtime can read tombstones but cannot mutate them; only the maintenance security-definer function may insert tombstones and delete eligible details in one transaction.
Reservation insertion has a unique `proof_job_id` constraint and scope-limited unique sequence/index constraints; it
does not rely on a read-then-write count alone.

Selection is deterministic:

1. An entitlement derived from a Stripe subscription with status `active`, whose period includes the
   server time, selects `pro` and that subscription's exact period; allowance is 100.
2. Otherwise it selects `free` and the account lifetime scope; allowance is 3.
3. It returns closed `quota_exhausted_free` or `quota_exhausted_pro` before proof creation when no slot exists.

## Success-based consumption — approved working delta

Newly admitted jobs carry an immutable policy receipt. Their reservation is a hold, not settled usage. A separate append-only lifecycle records hold creation and exactly one consumed/released terminal outcome. Legacy reservations keep their prior meaning; do not backfill failed jobs or modify old rows. Gross reservation sequence allocation is independent of net usage.

Settle only in the transaction persisting a completed, independently reviewed explanation for the verified proof. Release only when the proof or explanation reaches a terminal failure; candidate compilation failures that can still repair do not release. Enforce at-most-one successful consumption per proof in the database, including replay and competing terminal events.

After release, an explanation retry on an unconsumed job must acquire a new hold in the currently eligible scope before creating retry work/outbox. Insufficient allowance creates neither. Retry replay is idempotent. A consumed job never acquires another billable hold. Old-policy explanation retries do not add consumption. Each hold settles or releases within its original scope, even across period changes; do not move credits into a later period or Free.

Keep lock ordering consistent between admission, retry and completion. Return policy, consumed, reserved and available in the summary; available = max(0, limit - consumed - reserved). During a rolling frontend/API update, the old seven-field summary remains distinguishable as old policy. The UI must not infer that a missing hold field means the new policy.

This change is usage allowance accounting, not a Stripe monetary refund. Exact schema/migration/transaction integration is verified against the real PostgreSQL path before deployment.

## Stripe boundary

The API provides authenticated endpoints:

- `GET /v1/billing/summary`
- `POST /v1/billing/checkout-session`
- `POST /v1/billing/portal-session`
- `POST /v1/internal/stripe/webhook` (Stripe only; no learner bearer token)

Checkout and Portal endpoints have closed empty request objects with no `customer_id`, `price_id`, URL, or plan member.
The only billing runtime configuration is the injected `PALS_BILLING_CONFIG_JSON` Secret value with exact keys
`schema_version`, `stripe_secret_key`, `stripe_webhook_secret`, `pro_price_id`, `checkout_success_url`,
`checkout_cancel_url`, and `live_checkout_enabled`. URLs must be exact HTTPS `palschat.site` origins; the API
rejects unknown/duplicate/missing members and does not serve Checkout if `live_checkout_enabled` is false. The server
creates/reuses a local pending customer operation keyed by `(owner, "customer")`, calls Stripe with that operation ID
as its idempotency key, then atomically persists/reconciles the resulting customer ID. Checkout is likewise keyed by an
immutable local operation ID and uses it as Stripe's idempotency key, so an external success followed by a database
failure can be recovered by retrieving the same Stripe object rather than creating another customer/session. It creates
subscription-mode Checkout for the configured PALS Pro Price ID, and sets server-derived `owner_user_id` metadata on
Customer/Checkout/Subscription. Success and cancel URLs are configured server-side only.

Rejoining after cancellation validates the exact session ID, customer, owner metadata, mode and status, then rechecks
the terminal session under the owner's advisory lock. Subscription and customer ownership, configured price and
current subscription status are reconciled before retiring the old operation. An active contract cannot create a
second checkout; recoverable nonterminal contracts require reconciliation. Concurrent calls share the new operation
and idempotency key. Pending operations beyond the 23-hour replay window fail closed for manual reconciliation;
elapsed time alone does not authorize a new Stripe operation. An operator recovery workflow remains unimplemented.

The webhook route first passes the unmodified raw request bytes and signature header to Stripe verification. It then
stores/deduplicates the event ID in a transaction. A verified relevant event is a trigger, not an authoritative ordering
source. Event extraction is closed: `customer.subscription.created|updated|deleted` use `data.object.id` as the
subscription ID; `invoice.paid|payment_failed` use nonempty `data.object.subscription`; and
`checkout.session.completed` uses `data.object.customer` to complete only the customer/checkout binding and, if present,
nonempty `data.object.subscription` to trigger subscription retrieval. Missing, malformed, or mismatched fields are
recorded `ignored` and have no entitlement effect. For an extracted subscription ID, the API retrieves the current Stripe
subscription and projects that response only if its customer metadata maps exactly to one existing owner. Thus a late or
equal-second event cannot overwrite a later subscription state. A temporary retrieval failure (transport failure,
HTTP 408/429 or 5xx, or an unreadable JSON response) propagates as HTTP 503 and rolls back the whole event transaction, including any event-ledger
insertion or binding changes. The previous entitlement remains valid only until its existing period end; no extension
or new grant is inferred. Stripe can redeliver the same event and it is deduplicated only after a successful commit.
Permanent subscription/binding/price validation failures retain the existing non-granting reconciliation behavior.
Accepted lifecycle types are `customer.subscription.created`, `customer.subscription.updated`,
`customer.subscription.deleted`, `invoice.paid`, `invoice.payment_failed`, and binding-only
`checkout.session.completed`. `active` is the sole granting state;
`trialing`, `past_due`, `unpaid`, `incomplete`, `incomplete_expired`, `canceled`, and `paused` are non-granting.
`cancel_at_period_end` remains granting until Stripe reports a non-active status or its current period ends. Any
unsupported type is recorded as ignored after signature verification and has no entitlement effect. The
`checkout.session.completed` event can bind the customer but never activates entitlement itself without a subsequent
retrieval of an `active` subscription.

Project creation uses the same account advisory lock and entitlement resolver as material admission inside the project
transaction. Resolve against the database clock before inserting the Project, accepting active paid tiers, legacy Pro
and valid complimentary grants. Reject Free, expired or revoked access with `project_plan_required` (403) and no writes.
Existing reads remain owner-scoped and do not require a paid entitlement. The frontend uses the billing summary to
direct Free accounts to plan settings and prevent creation while entitlement is unknown; the API remains authoritative.

Public pages publish the approved Plus USD 10, Pro USD 20 and Research USD 100 monthly prices. Account settings retain
the API-owned catalogue and distinguish published prices from `checkout_enabled`. When Checkout is disabled, describe
purchase preparation without implying that prices are undecided. Keep catalogue/version and token-policy launch gates.

Local sandbox verification uses an explicit `PALS_ENV=local` configuration file, separate from production's injected
JSON. The mode-0600 regular file must belong to the effective runtime user; symlinks, oversized inputs and simultaneous
JSON/file configuration are rejected. Only `sk_test_` credentials and exact `http://localhost:3000` return origins are
accepted in this path. Production/dev do not read this file and retain the HTTPS `palschat.site` restriction.

For current Stripe snapshot versions, invoice events may instead identify their subscription through
`parent.type=subscription_details` and `parent.subscription_details.subscription`. Only strict subscription IDs are
accepted; conflicting legacy/new references are ignored. This compatibility does not change the authoritative
subscription/customer retrieval or owner/price/status validation. Stripe-hosted destinations retain exact HTTPS
host validation and preserve provider-supplied URL fragments required by Checkout.

## Frontend

The account/settings surface calls only the API summary/Checkout/Portal endpoints. It displays the exact plan limits,
remaining count, current period end, and Stripe-hosted management destination; the browser cannot set entitlement. A
proof creation `quota_exhausted_*` response retains draft input, displays the reason, and offers Pro upgrade only when
Checkout is configured. No billing secret or Stripe SDK is needed in the frontend first slice.

## Google/Cognito production configuration

`pals-infra/terraform/production` owns conditional Cognito Hosted UI-domain and user-pool-client configuration only.
It separates the optional `cognito_hosted_ui_domain_prefix` from `google_sign_in_enabled`. The release sequence is (1) apply the Hosted UI
with the client restricted to `COGNITO`; (2) a separately audited command reads the exact
`google-oauth-config` SSM SecureString JSON, calls Cognito Create/UpdateIdentityProvider, and reads it back to verify fixed
Google scopes/mappings; (3) apply `google_sign_in_enabled=true`, which adds `Google` to the user-pool client and only
then publishes `NEXT_PUBLIC_COGNITO_GOOGLE_ENABLED=true`. It receives no Google credential. The provisioner does not
print values, write a local file, or place them in Terraform input/state. If step two fails or rollback is needed, step
three is not run (or is first reversed) before deleting the IdP. The configured Hosted UI domain, callback URL, and logout URL populate only public frontend build configuration.
Google Cloud Console registers Cognito's `https://<hosted-ui-domain>/oauth2/idpresponse` as its redirect URI; Cognito
registers `https://palschat.site/auth/callback` as callback and `https://palschat.site/` as logout URL. Runtime access-token verification stays
unchanged.

## Secrets, roles, and release

Production follows the approved DPB cost-hybrid boundary: the API reads one externally populated
`billing-runtime-config` SSM SecureString, injected as `PALS_BILLING_CONFIG_JSON`. A separate,
explicitly trusted Google IdP provisioner reads `google-oauth-config`; OAuth values never enter
Terraform input/state/plan, application containers, logs, or frontend. Terraform owns parameter
names and IAM, not secret values or application secret resources. The existing host TLS egress
reaches Stripe without adding NAT gateways or interface endpoints. Billing actions fail closed
when configuration is absent or invalid; public Checkout also requires the launch flag and the
operator's legal/tax release inputs. A release verifies all migrations and permissions; real Stripe
connectivity is checked only in an explicitly requested configured smoke test.

Database migrations introduce a distinct API migration owned by the existing release authority, with runtime grants only
for the billing tables it needs. Webhook writes use the same API principal and do not gain proof/chat content access.

## Metering

The existing worker-secret authenticated `/v1/internal/proof-jobs/{proof_job_id}/usage` operation accepts exactly
`{schema_version:"pals.proof-job-usage.v1",generation_claim_id,call_id,provider,model,input_tokens,cached_input_tokens,
output_tokens,reasoning_output_tokens,price_snapshot_id}`. `call_id` is a UUID generated before each provider request;
the API locks the currently active generation claim, accepts one matching immutable record, and returns the existing
record only for an exact replay. Values are nonnegative safe integers, token subtotals must reconcile, and the checked-in
API price registry computes the integer micros-USD estimate; the worker never supplies price. The normal OpenAI client
must parse the response `usage` object and return it with output text. The API aggregates by proof job from immutable
call rows. Metering failure produces an observable internal error record but cannot alter a quota reservation or an
entitlement.

## Verification

- API unit and PostgreSQL integration tests: Free 3, concurrent reservation boundary, Pro 100 per period, mandatory
  idempotency/replay/conflict/expiry behavior, no proof/SQS action on denial, cancellation/failure fallback, and
  immutable ledger constraints.
- Stripe contract tests: raw-body signature validation, event idempotency, out-of-order events, falsified Checkout
  return, metadata mismatch, and no activation from Checkout completion.
- Web tests: summary, exhausted state, upgrade/manage state, retained proof draft, and absence of client payment secret.
- Terraform/deploy test: disabled Google creates no Hosted UI; enabled Google adds it to the user-pool client and the
  external provisioner creates/read-verifies the IdP without exposing credentials. existing host TLS egress to Stripe
  and secret scans are verified; no credential is present in plan/state/example.
- Cognito+Google production smoke after operator inputs: Hosted UI PKCE login reaches a valid API access token and a
  subject-bound billing summary; a same-email native account is not silently merged.


## Complimentary Pro for test accounts — BILL-011

Normal Cognito account registration/login remains unchanged. An operator resolves a registered account's Cognito `sub` and uses a separate administrative CLI; no learner-facing self-promotion endpoint or shared test password is added. There is no card entry, Checkout session or fabricated Stripe customer/subscription. This capability may be used for controlled beta access as well as QA; actual grants require a named subject and explicit expiry and are not created by installing the feature.

An additive migration stores immutable grants and separate immutable revocations in the billing schema. Each grant fixes owner, start/expiry, grant/operation identity, DB `session_user` and a bounded audit reason. The API runtime can read the tables but cannot mutate them or execute administrative functions. A distinct NOLOGIN operator role controls mutation through fixed-search-path functions; it is not assigned to the API runtime. Operator credentials stay outside the web application and repository. Expiry uses database time at each admission/summary, with no renewal cron.

A shared resolver selects active Stripe Pro first, then a current complimentary grant, then Free. Grant identity defines a separate `complimentary:<grant UUID>` scope with 100 requests for that explicitly granted period. Existing Free fallback remains; no Stripe-plus-grant Pro pooling. Grant/revoke use the same owner advisory lock as admission, so revocation and creation have an ordered transaction boundary. Duplicate identical grant operations return the original result; conflicting reuse and overlapping active grants fail. Revocation never resets usage or modifies earlier reservations.

The closed summary adds `billing_source` (`free`, `stripe`, `complimentary`) while retaining `plan=pro` and `period_end=expiry` for complimentary grants. Frontend compatibility accepts the preceding seven-field response as the old Free/Stripe contract; it rejects other unknown shapes. Card/menu text identifies complimentary Pro, its normal quota and expiry, and does not show recurring price/renewal or a Portal action for that grant. Existing genuine Stripe subscription management remains distinct; no subscription is canceled by a test grant.

Migration verification covers a fresh schema and known prior v3 upgrade, exact catalog fingerprints, manifest/release readiness, runtime/operator ACLs, no public function execution, and unchanged previous ledger rows. Real PostgreSQL concurrency and API tests exercise grants, exhaustion, replay, expiry, revoke and paid precedence. The later token policy will need its own explicit allowance mapping; current test grants are not silently interpreted as token balances.


## Explicit production token storage and runtime admission — authorized release slice

The 2026-10-02 authorized production billing implementation slice adds production migration and serving readiness for the existing token ledger. It preserves the approved catalogue, utilization weights, quote caps, immutable permit receipts, settlement/QA rules and legacy/count rows. It does not itself approve public Checkout, real charges, a wider model/retrieval rollout, or a subject-specific administrative allowance. The BILL-012/013 whole-operation release evidence and public billing launch inputs remain separate acceptance gates.

Production does not reuse local readiness. The existing production release registry adds a `token-accounting` step after proof-request storage. Its closed child manifest binds the unchanged v1 SQL and additive production authority SQL, PostgreSQL 16, and a separately derived canonical fingerprint of all five token/revision tables. The signed production bootstrap already binds the production registry manifest; its child hash therefore binds this token manifest and both SQL artifacts. Any artifact change requires a newly verified release admission. The public Aurora and Mac bootstrap function signatures and migration order remain unchanged.

Only a non-administrative release principal with the existing schema-owner authority, outside the runtime role, may apply this migration under the token migration transaction lock and a current signature-verified production admission. Fresh install and an exact known-v1 upgrade are supported. Existing quotes, active operations, caps, calls, usage receipts and historic rows are preserved. An exact replay changes nothing; an existing production revision with drift fails closed without repairing or rewriting data. The original local manifest, fingerprint and migration behavior stay unchanged.

The additive production authority migration fixes all five table owners to the release schema owner. Runtime receives SELECT/INSERT on the three ledger tables, SELECT on revision metadata, and UPDATE only for the quote's used-operation binding, operation settlement state/consumed/closed-at, and call state/receipt/actual-cost fields. It receives no cap/quote-content UPDATE, DELETE, revision write, DDL, grant option or public access. Serving uses no release credential and performs no migration.

When `PALS_ENV=prod` and the existing explicit `PALS_TOKEN_ACCOUNTING_ENABLED=true` flag are selected, API readiness additionally requires the exact current signed artifact admission and trust fence, the independently pinned PostgreSQL-16 catalog fingerprint, exact constraints/indexes/table kinds/owners/column and table ACLs, and absence of extra triggers/rules/generated columns/RLS. The runtime principal must have ordinary runtime authority without schema-owner membership, database/schema CREATE or reachable administrative roles. Existing PJR/PEX admission foundations, billing storage and proof-request storage must also be current. A flag or self-written database fingerprint alone cannot make serving ready.

The ordinary worker selects the existing token processor for the same explicit flag in `local` or `prod`; all other environments retain the preceding mode. This selection supplies no authority to call a provider. The API's claim-bound billing-operation UUID, pre-call permit, durable receipt, cap and independently reviewed answer/settlement contracts remain authoritative. Normal-only route/container capability selection is a separately owned release slice and adds no duplicate token environment flag.

Verification uses the existing random disposable PostgreSQL fixture, without changing shared cluster roles: signed local EC verification at the existing KMS boundary, known-v1 upgrade and exact replay with unchanged active-operation/receipt rows, read-only drift denial, unsigned/wrong-artifact rejection, and actual runtime denial of DDL/cap/delete/revision writes. The local cryptographic test is not live AWS KMS or production deployment evidence. Full signed bootstrap/runtime readiness, backup/restore replay, live provider/whole-operation coverage and operator launch inputs retain their own release checks.

Production principal checks validate both authenticated `session_user` and effective `current_user`, including MEMBER-reachable administrative and privileged predefined-role authority. Runtime additionally excludes reachable schema-owner or database/schema CREATE authority; release intentionally permits its schema-owner authority while excluding runtime membership. An administrative connection cannot become admissible through SET ROLE or RESET ROLE. Dedicated-login integration evidence is separate from administrative SET LOCAL ROLE observations; the initial master bootstrap remains a separate authority boundary.
