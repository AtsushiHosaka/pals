# Opt-in local Plus coupon bootstrap

This is the first source-integration stage for #240. It extends the canonical
local qualification preparation path. It does not activate a production release
or complete authenticated coupon acceptance.

## Behavior

`pals-scripts/local-qualification-prepare.py` accepts `--enable-plus-coupons`.
Without it, the existing bootstrap arguments and API Compose environment remain
unchanged. A saved `PALS_PLUS_COUPONS_ENABLED=true` requires an explicit opt-in on
every preparation invocation; omission refuses before stopping the stack rather
than silently disabling an existing enabled profile.

Before the first stop, build or profile write, opt-in requires the dedicated
local environment and the API checkout's tracked HEAD bytes for the coupon
helper, SQL and manifest. The SQL and schema hashes must match the supported
profile, and the helper must expose the expected local installer and readback
signatures. Missing, changed, untracked or symlinked source is refused. This
inspection does not import the API or contact a database.

The real preparation callback passes the flag to `bootstrap_database.py`.
That child rechecks the source, keeps the existing local database URL boundary,
and calls the candidate's `apply_local_storage` inside an explicit caller
transaction. It verifies `current` in that transaction before returning an
installed/current receipt bound to the source hashes. Only `PALS_ENV=local` is
scoped to the installer call, and its prior process value is restored on both
success and failure. The existing token-accounting setting is preserved.

The generated API Compose environment contains a literal coupon flag only for
the validated opt-in profile. Ambient shell interpolation cannot enable it.
The driver requires the actual API environment to contain exactly one true flag
before and after the existing API configuration convergence loop. The receipt
is stored under `subject.preparation.plus_coupons`; the overall result remains
`prepared_dependency_ready_not_product_accepted`.

## Verification

The new `CouponBootstrapTests` exercise the actual source inspector, child argv
builder, preparation main/callback, receipt parser, installer call and runtime
flag check. Temporary Git source fixtures provide tracked/untracked/symlink and
signature/hash failures. Docker, TLS and database adapters are isolated in these
driver unit tests; no server or database is started.

```sh
python3 -m unittest discover -s pals-scripts/tests \
  -p test_local_qualification.py -k CouponBootstrapTests -v
```

The 14 new cases pass with zero skips. A separate resource-free inspection of
the reviewed API candidate passed using its actual tracked helper, SQL and
manifest. Rendering the default optional binding produced exactly the previous
Compose template bytes. Source/driver regression results are recorded in the
PR: the selected adjacent source/driver regression run had 49 passes and one
pre-existing skip because this isolated parent worktree has no initialized API
submodule. The new 14 tests have no skips. Existing unrelated Ruff diagnostics
are retained; the differential check found the same 29 diagnostics and no additions.

The API candidate already has 35 author-run and six independently reviewed real
PostgreSQL cases. Those support the unchanged API implementation only. This
preparation driver has not been run against PostgreSQL or the shared stack.

## Remaining gates

Coupon schema readback after API startup is not part of the existing frozen
Draft database contract. The bootstrap transaction receipt is not a fresh
coupon readiness or runtime-schema attestation. Extending that closed readiness
contract is a separate integration stage.

Actual local Cognito login, redemption, entitlement/allowance refresh, Plus use
without a paid model call, reload/history, and the later end-to-end scenario
remain unverified. The existing guest proof qualification and `local_pre` gate
are unchanged; this change does not mark either as passed.

The current shared application sources differ from the coupon candidate. The
stack owner must coordinate the source handoff before any preparation,
replacement or DDL. This work did not change existing applications, PostgreSQL,
Cognito, the network guard, the budget ledger or the native release hooks.
