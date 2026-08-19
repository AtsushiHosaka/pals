# Individual Billing Design

## Scope and traceability

This design implements BILL-001 through BILL-010 in `pals-api`, `pals-webfront`, and the production
Terraform release surface. It is deliberately a job-reservation entitlement system, not a token-priced billing
system. Existing proof verification and chat ownership remain unchanged.

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
- `billing_stripe_operations`: immutable operation ID, owner, kind (`customer` or `checkout`), Stripe idempotency key,
  optional resulting Stripe object ID, `pending`/`completed`/`expired` status, and timestamps. A partial unique index
  permits one pending customer operation per owner and one unexpired checkout operation per owner; Stripe idempotency
  key and `(owner, kind, operation ID)` are unique. Allowed transitions are `pending -> completed` or `expired`; a
  later checkout call returns/reconciles an unexpired completed operation and creates one new operation only after
  expiry. No operation is deleted;
- `billing_stripe_events`: Stripe event ID (unique), event type, event creation time, received time, verified payload
  SHA-256, and processing outcome;
- `proof_job_usage_calls`: immutable call ID (unique), proof job ID, generation claim ID, provider/model, nonnegative
  input/output token counts, optional cached and reasoning tokens, price snapshot ID, integer micros-USD cost estimate,
  and recorded timestamp. Per-job and monthly aggregates are derived from these rows, never updated source facts.

No billing relation contains payment method detail, card detail, email, OAuth provider subject, prompt, theorem,
Lean source, chat, explanation, clarification, raw webhook body, or provider request/response payload. The raw Stripe
body exists only in memory for signature verification and is discarded after minimal projection.

Stripe event metadata, idempotency, and Stripe-operation records are retained for 13 months; numeric proof-job usage is
retained for 90 days and then irreversibly aggregated by calendar month without job/account linkage. Only an API-owned
support-auditor role may read event metadata; normal runtime and learner endpoints read summary projections only. A later
privacy policy may shorten but must not silently extend these windows.

`owner_user_id` is the validated Cognito access-token `sub`; it is never derived from email. Database policies and
repository queries bind every learner-facing read/write to that value. Two different Cognito subjects never merge based
on a matching email in this release. An explicit account-link feature would require a separately authenticated,
consented Cognito `AdminLinkProviderForUser` design and is out of scope.

## Entitlement and reservation transaction

The existing authenticated proof-job create service requires the exact `Idempotency-Key` header `[A-Za-z0-9_-]{32,128}`
and receives an API-owned `BillingAdmissionService` dependency. It RFC-8785-canonicalizes the closed create payload,
hashes it and the header independently, and keeps the digests—not the original request—in the 24-hour idempotency
record. In one
PostgreSQL transaction it obtains an advisory/account-row lock, reads the authoritative entitlement snapshot, counts
reservations in the selected scope, rejects an exhausted allowance, creates the proof job, and inserts the reservation.
The transaction commits before the existing outbox/SQS dispatch path; any failure rolls back both job and reservation.
An existing non-expired `(owner,key digest)` is resolved before a new reservation: equal request fingerprint returns the
original response, while a changed fingerprint or key reuse after expiry returns HTTP 409 `idempotency_conflict`.
Reservation insertion has a unique `proof_job_id` constraint and scope-limited unique sequence/index constraints; it
does not rely on a read-then-write count alone.

Selection is deterministic:

1. An entitlement derived from a Stripe subscription with status `active`, whose period includes the
   server time, selects `pro` and that subscription's exact period; allowance is 100.
2. Otherwise it selects `free` and the account lifetime scope; allowance is 3.
3. It returns closed `quota_exhausted_free` or `quota_exhausted_pro` before proof creation when no slot exists.

There is no refund path in this release. Internal operations may annotate a support case separately, but cannot mutate
the immutable reservation ledger.

## Stripe boundary

The API provides authenticated endpoints:

- `GET /v1/billing/summary`
- `POST /v1/billing/checkout-session`
- `POST /v1/billing/portal-session`
- `POST /v1/internal/stripe/webhook` (Stripe only; no learner bearer token)

Checkout and Portal endpoints have closed empty request objects with no `customer_id`, `price_id`, URL, or plan member.
The only billing runtime configuration is the injected `PALS_BILLING_CONFIG_JSON` Secret value with exact keys
`schema_version`, `stripe_secret_key`, `stripe_webhook_secret`, `pro_price_id`, `checkout_success_url`,
`checkout_cancel_url`, and `live_checkout_enabled`. URLs must be exact HTTPS `app.palschat.site` origins; the API
rejects unknown/duplicate/missing members and does not serve Checkout if `live_checkout_enabled` is false. The server
creates/reuses a local pending customer operation keyed by `(owner, "customer")`, calls Stripe with that operation ID
as its idempotency key, then atomically persists/reconciles the resulting customer ID. Checkout is likewise keyed by an
immutable local operation ID and uses it as Stripe's idempotency key, so an external success followed by a database
failure can be recovered by retrieving the same Stripe object rather than creating another customer/session. It creates
subscription-mode Checkout for the configured PALS Pro Price ID, and sets server-derived `owner_user_id` metadata on
Customer/Checkout/Subscription. Success and cancel URLs are configured server-side only.

The webhook route first passes the unmodified raw request bytes and signature header to Stripe verification. It then
stores/deduplicates the event ID in a transaction. A verified relevant event is a trigger, not an authoritative ordering
source. Event extraction is closed: `customer.subscription.created|updated|deleted` use `data.object.id` as the
subscription ID; `invoice.paid|payment_failed` use nonempty `data.object.subscription`; and
`checkout.session.completed` uses `data.object.customer` to complete only the customer/checkout binding and, if present,
nonempty `data.object.subscription` to trigger subscription retrieval. Missing, malformed, or mismatched fields are
recorded `ignored` and have no entitlement effect. For an extracted subscription ID, the API retrieves the current Stripe
subscription and projects that response only if its customer metadata maps exactly to one existing owner. Thus a late or
equal-second event cannot overwrite a later subscription state. A failed retrieval marks the event
`reconciliation_pending` and keeps the affected entitlement non-granting until a later verified
event/reconciliation retrieves an `active` subscription.
Accepted lifecycle types are `customer.subscription.created`, `customer.subscription.updated`,
`customer.subscription.deleted`, `invoice.paid`, `invoice.payment_failed`, and binding-only
`checkout.session.completed`. `active` is the sole granting state;
`trialing`, `past_due`, `unpaid`, `incomplete`, `incomplete_expired`, `canceled`, and `paused` are non-granting.
`cancel_at_period_end` remains granting until Stripe reports a non-active status or its current period ends. Any
unsupported type is recorded as ignored after signature verification and has no entitlement effect. The
`checkout.session.completed` event can bind the customer but never activates entitlement itself without a subsequent
retrieval of an `active` subscription.

## Frontend

The account/settings surface calls only the API summary/Checkout/Portal endpoints. It displays the exact plan limits,
remaining count, current period end, and Stripe-hosted management destination; the browser cannot set entitlement. A
proof creation `quota_exhausted_*` response retains draft input, displays the reason, and offers Pro upgrade only when
Checkout is configured. No billing secret or Stripe SDK is needed in the frontend first slice.

## Google/Cognito production configuration

`pals-infra/terraform/production` owns conditional Cognito Hosted UI-domain and user-pool-client configuration only.
It separates `google_hosted_ui_enabled` from `google_client_enabled`. The release sequence is (1) apply the Hosted UI
with the client restricted to `COGNITO`; (2) a separately audited command reads the exact
`PALS_GOOGLE_OAUTH_CONFIG_JSON` Secret, calls Cognito Create/UpdateIdentityProvider, and reads it back to verify fixed
Google scopes/mappings; (3) apply `google_client_enabled=true`, which adds `Google` to the user-pool client and only
then publishes `NEXT_PUBLIC_COGNITO_GOOGLE_ENABLED=true`. It receives no Google credential. The provisioner does not
print values, write a local file, or place them in Terraform input/state. If step two fails or rollback is needed, step
three is not run (or is first reversed) before deleting the IdP. The configured Hosted UI domain, callback URL, and logout URL populate only public frontend build configuration.
Google Cloud Console registers Cognito's `https://<hosted-ui-domain>/oauth2/idpresponse` as its redirect URI; Cognito
registers the exact `https://app.palschat.site/...` callback/logout URLs. Runtime access-token verification stays
unchanged.

## Secrets, roles, and release

Terraform creates only two secret containers: `billing-runtime-config` and `google-oauth-config`. API task definition
injects the former as `PALS_BILLING_CONFIG_JSON`; only the API task role can read it. The Google provisioner role, not
the API or frontend role, reads the latter. Neither JSON value enters tfvars, state, plan, logs, nor frontend. API tasks
need explicit TLS egress through one production NAT gateway (a costed single-AZ launch dependency) to Stripe; private
AWS endpoints remain used for AWS traffic. A release command verifies all billing migrations and runs a Stripe API
connectivity check only when explicitly requested; normal application startup fails closed for billing actions if values
are absent.

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
  external provisioner creates/read-verifies the IdP without exposing credentials. NAT/API outbound Stripe reachability
  and secret scans are verified; no credential is present in plan/state/example.
- Cognito+Google production smoke after operator inputs: Hosted UI PKCE login reaches a valid API access token and a
  subject-bound billing summary; a same-email native account is not silently merged.
