# Chat sharing operation and verification

Chat headers expose Share. Review the preview, then create a public link. Anyone holding
the link can read the saved snapshot without an account. Later conversation changes do
not update it. Reopening Share shows the existing snapshot; revoke it before publishing
a fresh snapshot. A new publication always receives a different token. Mathematical
content remains readable, and Lean source is shared only when the existing learner
source boundary permits it (a verified proof).

Snapshots over 1 MiB of canonical material are rejected without truncation. Empty chats
cannot be shared. The response/page disables caching and indexing. Revocation blocks
future retrieval; it cannot recall text that a reader has already copied.

## Release

The API needs the additive `chat-shares` migration before startup. The migration is
registered in the existing production release manifest and local legacy release runner,
so the normal repository release processes install it. Serving startup checks the schema
and never creates tables.

For a standalone production child release, use the existing authorized release process
and schema-owner credential in `PALS_DATABASE_RELEASE_URL`:

```sh
python -m app.release.chat_shares_migration --apply
```

This command requires the existing closed production foundation. The historical local
database uses the existing local legacy release workflow instead. Do not copy release
credentials to serving processes or logs. The runtime role is granted SELECT, INSERT,
and UPDATE only on `revoked_at`; a database trigger also prevents snapshot changes,
deletion, and revival of revoked tokens.

No frontend environment variable is added. The anonymous client uses the existing
browser-facing API origin, with credentials omitted. `/share/[token]` is publicly
readable while owner operations retain the normal Cognito authorization boundary.

## Verification

Run the API PostgreSQL integration suite against an authorized local test database
using `PALS_TEST_POSTGRES_URL`. It creates and cleans up its own disposable database
within the existing PostgreSQL service:

```sh
cd pals-api
.venv/bin/python -m pytest tests/integration/test_chat_shares.py -q
```

With the real local stack running, a saved chat owned by the configured local reviewer
account can be checked from the parent repository:

```sh
pals-api/.venv/bin/python tests/e2e/check_chat_sharing.py --chat-id CHAT_UUID
```

The HTTP smoke uses real local Cognito and API services. It rejects a fixture with an
existing active link, verifies preview/publication/anonymous access/revocation, and
revokes only the links it creates. Credentials and capability tokens are not printed.
The browser journey additionally checks the dialog, link-copy feedback, math, Lean disclosure,
anonymous view, narrow screen layout, and revoked-link state. Current results and
source/build identities are recorded in `docs/chat-sharing-loop-ledger.md`.
